"""
Metrics computation module.
Provides robust calculation of analytics KPIs, conversion rates, ROAS, CPC, CPA,
and user funnel progression with strict division-by-zero guards.
"""

import pandas as pd
import numpy as np


def safe_divide(numerator, denominator, default=0.0):
    """Safely divide two numbers or arrays, returning default when denominator is 0."""
    is_num_series = isinstance(numerator, pd.Series)
    is_denom_series = isinstance(denominator, pd.Series)
    is_num_array = isinstance(numerator, np.ndarray)
    is_denom_array = isinstance(denominator, np.ndarray)
    
    if is_num_series or is_denom_series or is_num_array or is_denom_array:
        num_arr = np.asarray(numerator, dtype=float)
        denom_arr = np.asarray(denominator, dtype=float)
        out_shape = np.broadcast(num_arr, denom_arr).shape
        out = np.full(out_shape, fill_value=default, dtype=float)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            valid_mask = (denom_arr != 0) & (~np.isnan(denom_arr))
            np.divide(num_arr, denom_arr, out=out, where=valid_mask)
            
        if is_num_series:
            return pd.Series(out, index=numerator.index)
        elif is_denom_series:
            return pd.Series(out, index=denominator.index)
        return out
        
    if denominator is None or denominator == 0 or pd.isna(denominator):
        return default
    try:
        return float(numerator / denominator)
    except (ZeroDivisionError, ValueError, TypeError):
        return default


def calc_impression_weighted_position(df, position_col="position", impressions_col="impressions"):
    """
    Calculate impression-weighted average position:
    Formula: sum(position * impressions) / sum(impressions)
    Safely handles zero impressions, empty DataFrames, and missing values.
    """
    if df is None or len(df) == 0:
        return 0.0
    valid = df.dropna(subset=[position_col, impressions_col])
    if len(valid) == 0:
        return 0.0
    imp = valid[impressions_col].values.astype(float)
    pos = valid[position_col].values.astype(float)
    total_imp = np.sum(imp)
    if total_imp <= 0:
        return 0.0
    return float(np.sum(pos * imp) / total_imp)


def compute_executive_kpis(filtered_data):
    """
    Calculate high-level executive KPIs across GA4 sessions and Google Ads.
    Strictly separates:
    1. Blended ROAS (All-channel GA4 revenue / Ad spend)
    2. GA4 Paid-Channel Revenue / Ad Spend (GA4 Google Ads attributed revenue / Ad spend)
    3. Google Ads Reported ROAS (Google Ads self-reported conversion value / Ad spend)
    """
    df_sess = filtered_data.get("sessions", pd.DataFrame())
    df_ads = filtered_data.get("google_ads", pd.DataFrame())
    
    if df_sess.empty:
        return {
            "total_sessions": 0,
            "total_users": 0,
            "engaged_sessions": 0,
            "engagement_rate": 0.0,
            "total_conversions": 0,
            "conversion_rate": 0.0,
            "total_revenue": 0.0,
            "avg_order_value": 0.0,
            "total_ad_spend": 0.0,
            "ga4_paid_revenue": 0.0,
            "ga4_paid_conversions": 0,
            "ads_reported_conversion_value": 0.0,
            "ads_reported_conversions": 0,
            "blended_roas": 0.0,
            "ga4_paid_roas": 0.0,
            "ads_reported_roas": 0.0,
        }
        
    total_sessions = int(len(df_sess))
    total_users = int(df_sess["user_id"].nunique())
    engaged_sessions = int(df_sess["is_engaged_session"].sum())
    engagement_rate = safe_divide(engaged_sessions, total_sessions)
    
    total_conversions = int(df_sess["has_conversion"].sum())
    conversion_rate = safe_divide(total_conversions, total_sessions)
    total_revenue = float(df_sess["revenue"].sum())
    avg_order_value = safe_divide(total_revenue, total_conversions)
    
    # Ad Spend from Ads table
    total_ad_spend = float(df_ads["cost"].sum()) if not df_ads.empty else 0.0
    
    # GA4 Paid Channel Revenue (Google Ads acquisition source only)
    ga4_paid_sess = df_sess[df_sess["acquisition_source"] == "Google Ads"]
    ga4_paid_revenue = float(ga4_paid_sess["revenue"].sum()) if not ga4_paid_sess.empty else 0.0
    ga4_paid_conversions = int(ga4_paid_sess["has_conversion"].sum()) if not ga4_paid_sess.empty else 0
    
    # Google Ads Reported Conversion Value & Conversions from Ads table
    ads_reported_conversion_value = float(df_ads["conversion_value"].sum()) if not df_ads.empty else 0.0
    ads_reported_conversions = int(df_ads["conversions"].sum()) if not df_ads.empty else 0
    
    # Separated ROAS Metrics
    blended_roas = safe_divide(total_revenue, total_ad_spend)
    ga4_paid_roas = safe_divide(ga4_paid_revenue, total_ad_spend)
    ads_reported_roas = safe_divide(ads_reported_conversion_value, total_ad_spend)
    
    return {
        "total_sessions": total_sessions,
        "total_users": total_users,
        "engaged_sessions": engaged_sessions,
        "engagement_rate": engagement_rate,
        "total_conversions": total_conversions,
        "conversion_rate": conversion_rate,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "total_ad_spend": total_ad_spend,
        "ga4_paid_revenue": ga4_paid_revenue,
        "ga4_paid_conversions": ga4_paid_conversions,
        "ads_reported_conversion_value": ads_reported_conversion_value,
        "ads_reported_conversions": ads_reported_conversions,
        "blended_roas": blended_roas,
        "ga4_paid_roas": ga4_paid_roas,
        "ads_reported_roas": ads_reported_roas,
    }


def compute_acquisition_breakdown(filtered_data):
    """
    Aggregate acquisition metrics by Acquisition Source, Source/Medium, and Campaign.
    Correctly calculates:
    - Advertising CPC = Ads Spend / Ads Clicks (for paid channels with ad click data).
    - Cost per GA4 Session = Ads Spend / GA4 Sessions (clearly distinguished from CPC).
    - GA4 Paid ROAS = GA4 Attributed Revenue / Ads Spend (for paid channels).
    Prevents double-counting across different granularities and handles missing clicks safely.
    """
    df_sess = filtered_data.get("sessions", pd.DataFrame())
    df_ads = filtered_data.get("google_ads", pd.DataFrame())
    
    if df_sess.empty:
        return pd.DataFrame(columns=[
            "acquisition_source", "source_medium", "campaign", "users", "sessions",
            "engaged_sessions", "engagement_rate", "conversions", "conversion_rate",
            "revenue", "cost", "ads_clicks", "ads_cpc", "cpc", "cost_per_ga4_session", "roas"
        ])
        
    # Aggregate GA4 by source, source_medium, campaign
    agg = df_sess.groupby(["acquisition_source", "source_medium", "campaign"]).agg(
        users=("user_id", "nunique"),
        sessions=("session_id", "count"),
        engaged_sessions=("is_engaged_session", "sum"),
        conversions=("has_conversion", "sum"),
        revenue=("revenue", "sum")
    ).reset_index()
    
    # Calculate rates
    agg["engagement_rate"] = safe_divide(agg["engaged_sessions"], agg["sessions"])
    agg["conversion_rate"] = safe_divide(agg["conversions"], agg["sessions"])
    
    # Prepare Ads cost and clicks aggregation strictly by campaign
    if not df_ads.empty:
        ads_camp = df_ads.groupby("campaign").agg(
            cost=("cost", "sum"),
            ads_clicks=("clicks", "sum"),
            ads_impressions=("impressions", "sum")
        ).reset_index()
        
        # Split Google Ads rows to join ad metrics strictly to Google Ads channels
        is_google_ads = agg["acquisition_source"] == "Google Ads"
        agg_ads = agg[is_google_ads].copy()
        agg_non_ads = agg[~is_google_ads].copy()
        
        if not agg_ads.empty:
            merged_ads = pd.merge(agg_ads, ads_camp, on="campaign", how="left")
            merged_ads["cost"] = merged_ads["cost"].fillna(0.0)
            merged_ads["ads_clicks"] = merged_ads["ads_clicks"].fillna(0).astype(int)
            merged_ads["ads_impressions"] = merged_ads["ads_impressions"].fillna(0).astype(int)
        else:
            merged_ads = agg_ads.copy()
            merged_ads["cost"] = 0.0
            merged_ads["ads_clicks"] = 0
            merged_ads["ads_impressions"] = 0
            
        agg_non_ads["cost"] = 0.0
        agg_non_ads["ads_clicks"] = 0
        agg_non_ads["ads_impressions"] = 0
        
        merged = pd.concat([merged_ads, agg_non_ads], ignore_index=True)
    else:
        merged = agg.copy()
        merged["cost"] = 0.0
        merged["ads_clicks"] = 0
        merged["ads_impressions"] = 0
        
    # True Advertising CPC: Google Ads Spend / Google Ads Clicks
    merged["ads_cpc"] = np.where(
        merged["acquisition_source"] == "Google Ads",
        safe_divide(merged["cost"], merged["ads_clicks"]),
        0.0
    )
    # Maintain 'cpc' alias mapped to real advertising CPC
    merged["cpc"] = merged["ads_cpc"]
    
    # Separate metric: Cost per GA4 Session
    merged["cost_per_ga4_session"] = np.where(
        merged["acquisition_source"] == "Google Ads",
        safe_divide(merged["cost"], merged["sessions"]),
        0.0
    )
    
    # GA4 Paid ROAS: GA4 Attributed Revenue / Ad Spend
    merged["roas"] = np.where(
        merged["cost"] > 0,
        safe_divide(merged["revenue"], merged["cost"]),
        0.0
    )
    
    return merged.sort_values(by="sessions", ascending=False)


def compute_funnel_metrics(filtered_data):
    """
    Calculate the chronological e-commerce progression funnel:
    Stage 1: Session / Landing Page (all entry sessions)
    Stage 2: View Item (Plan) (view_item)
    Stage 3: Add To Cart (add_to_cart)
    Stage 4: Begin Checkout (begin_checkout)
    Stage 5: Purchase (purchase)
    
    A stage only counts if it occurs chronologically at or after the preceding qualifying stage
    within the exact same session. Out-of-order stages (e.g. purchase before cart) or skipped
    stages are strictly excluded from qualifying for subsequent stages.
    
    Denominator Definition:
    - Standardized to Total Entry Sessions (Stage 1) across all stage percentages and overall conversion rate.
    - Step conversion rate is: Sessions in Stage i / Sessions in Stage i-1.
    """
    df_sess = filtered_data.get("sessions", pd.DataFrame())
    df_events = filtered_data.get("events", pd.DataFrame())
    
    stages = [
        "1. Session / Landing Page",
        "2. View Item (Plan)",
        "3. Add To Cart",
        "4. Begin Checkout",
        "5. Purchase"
    ]
    
    if df_sess.empty:
        return {
            "stages": stages,
            "counts": [0, 0, 0, 0, 0],
            "drop_offs": [0.0, 0.0, 0.0, 0.0, 0.0],
            "step_conversion_rates": [0.0, 0.0, 0.0, 0.0, 0.0],
            "entry_conversion_rates": [0.0, 0.0, 0.0, 0.0, 0.0],
            "overall_conversion_rate": 0.0,
            "stage_sessions": {1: set(), 2: set(), 3: set(), 4: set(), 5: set()},
            "funnel_df": pd.DataFrame({
                "Stage": stages,
                "Sessions": [0, 0, 0, 0, 0],
                "Entry-Session Conversion Rate (%)": [0.0, 0.0, 0.0, 0.0, 0.0],
                "Step Conversion Rate (%)": [0.0, 0.0, 0.0, 0.0, 0.0],
                "Drop-off Rate (%)": [0.0, 0.0, 0.0, 0.0, 0.0],
                "% of Total Sessions": [0.0, 0.0, 0.0, 0.0, 0.0]
            })
        }
        
    sessions_all = set(df_sess["session_id"].dropna().unique())
    
    # Stage 1: All entry sessions
    stage_sessions = {
        1: set(sessions_all),
        2: set(),
        3: set(),
        4: set(),
        5: set()
    }
    
    if not df_events.empty:
        # Filter for relevant funnel events and valid sessions
        target_events = ["view_item", "add_to_cart", "begin_checkout", "purchase"]
        evt_subset = df_events[
            (df_events["session_id"].isin(sessions_all)) &
            (df_events["event_name"].isin(target_events))
        ].copy()
        
        if not evt_subset.empty:
            evt_subset["ts"] = pd.to_datetime(evt_subset["timestamp"])
            # Lifecycle priority tie-breaker for identical timestamps
            lifecycle_order = {
                "view_item": 1,
                "add_to_cart": 2,
                "begin_checkout": 3,
                "purchase": 4
            }
            evt_subset["order_rank"] = evt_subset["event_name"].map(lifecycle_order)
            
            # Sort chronologically by session, timestamp, and lifecycle rank
            evt_sorted = evt_subset.sort_values(by=["session_id", "ts", "order_rank"])
            
            # Process each session's event stream sequentially
            grouped = evt_sorted.groupby("session_id")
            for sess_id, grp in grouped:
                target_idx = 1  # Looking for view_item (rank 1)
                last_ts = None
                
                for _, row in grp.iterrows():
                    evt_rank = row["order_rank"]
                    evt_time = row["ts"]
                    
                    if evt_rank == target_idx:
                        if last_ts is None or evt_time >= last_ts:
                            target_idx += 1
                            last_ts = evt_time
                            stage_sessions[target_idx].add(sess_id)
                            if target_idx > 4:
                                break
                                
    counts = [
        len(stage_sessions[1]),
        len(stage_sessions[2]),
        len(stage_sessions[3]),
        len(stage_sessions[4]),
        len(stage_sessions[5])
    ]
    
    step_conversion_rates = []
    drop_offs = []
    entry_conversion_rates = []
    base_sessions = counts[0]
    
    for i in range(len(counts)):
        curr = counts[i]
        entry_cr = safe_divide(curr, base_sessions)
        entry_conversion_rates.append(entry_cr)
        
        if i == 0:
            step_conversion_rates.append(1.0 if base_sessions > 0 else 0.0)
            drop_offs.append(0.0)
        else:
            prev = counts[i - 1]
            step_cr = safe_divide(curr, prev)
            drop_rate = safe_divide(prev - curr, prev)
            step_conversion_rates.append(step_cr)
            drop_offs.append(drop_rate)
            
    overall_cr = safe_divide(counts[-1], base_sessions)
    
    funnel_df = pd.DataFrame({
        "Stage": stages,
        "Sessions": counts,
        "Entry-Session Conversion Rate (%)": [round(c * 100, 2) for c in entry_conversion_rates],
        "Step Conversion Rate (%)": [round(c * 100, 2) for c in step_conversion_rates],
        "Drop-off Rate (%)": [round(d * 100, 2) for d in drop_offs],
        "% of Total Sessions": [round(c * 100, 2) for c in entry_conversion_rates]
    })
    
    return {
        "stages": stages,
        "counts": counts,
        "drop_offs": drop_offs,
        "step_conversion_rates": step_conversion_rates,
        "entry_conversion_rates": entry_conversion_rates,
        "overall_conversion_rate": overall_cr,
        "stage_sessions": stage_sessions,
        "funnel_df": funnel_df
    }


def compute_events_kpis(filtered_data):
    """Compute event summary statistics, top events, and category breakdown."""
    df_events = filtered_data.get("events", pd.DataFrame())
    df_sess = filtered_data.get("sessions", pd.DataFrame())
    
    if df_events.empty:
        return {
            "total_events": 0,
            "unique_event_users": 0,
            "avg_events_per_session": 0.0,
            "avg_engagement_time": 0.0,
            "event_counts": pd.DataFrame(),
            "category_counts": pd.DataFrame(),
            "events_trend": pd.DataFrame()
        }
        
    total_events = len(df_events)
    unique_users = df_events["user_id"].nunique()
    total_sess_count = max(1, len(df_sess))
    avg_events_per_session = safe_divide(total_events, total_sess_count)
    avg_engagement_time = float(df_sess["engagement_time_seconds"].mean()) if not df_sess.empty else 0.0
    
    # Event counts
    event_counts = df_events["event_name"].value_counts().reset_index()
    event_counts.columns = ["event_name", "count"]
    event_counts["pct_of_total"] = safe_divide(event_counts["count"], total_events) * 100
    
    # Category counts
    cat_counts = df_events["event_category"].value_counts().reset_index()
    cat_counts.columns = ["event_category", "count"]
    
    # Events over time
    events_trend = df_events.groupby(["date", "event_name"]).size().reset_index(name="event_count")
    
    return {
        "total_events": total_events,
        "unique_event_users": unique_users,
        "avg_events_per_session": avg_events_per_session,
        "avg_engagement_time": avg_engagement_time,
        "event_counts": event_counts,
        "category_counts": cat_counts,
        "events_trend": events_trend
    }


def compute_search_console_kpis(filtered_data):
    """
    Compute GSC KPIs with impression-weighted average position and accurate CTR.
    - Overall average position: sum(position * impressions) / sum(impressions)
    - Query & Page average position: impression-weighted within each group
    - Overall CTR: sum(clicks) / sum(impressions)
    """
    df_gsc = filtered_data.get("search_console", pd.DataFrame())
    
    if df_gsc.empty:
        return {
            "total_clicks": 0,
            "total_impressions": 0,
            "avg_ctr": 0.0,
            "avg_position": 0.0,
            "query_performance": pd.DataFrame(),
            "page_performance": pd.DataFrame(),
            "daily_trend": pd.DataFrame()
        }
        
    total_clicks = int(df_gsc["clicks"].sum())
    total_impressions = int(df_gsc["impressions"].sum())
    avg_ctr = safe_divide(total_clicks, total_impressions)
    
    # Impression-weighted average position overall
    avg_pos = calc_impression_weighted_position(df_gsc)
    
    # Query performance with impression-weighted position
    df_gsc_calc = df_gsc.copy()
    df_gsc_calc["pos_x_imp"] = df_gsc_calc["position"] * df_gsc_calc["impressions"]
    
    if "query" in df_gsc_calc.columns:
        q_perf = df_gsc_calc.groupby("query").agg(
            clicks=("clicks", "sum"),
            impressions=("impressions", "sum"),
            pos_x_imp=("pos_x_imp", "sum")
        ).reset_index()
        q_perf["ctr"] = safe_divide(q_perf["clicks"], q_perf["impressions"])
        q_perf["avg_position"] = safe_divide(q_perf["pos_x_imp"], q_perf["impressions"]).round(1)
        q_perf = q_perf.drop(columns=["pos_x_imp"]).sort_values(by="clicks", ascending=False)
    else:
        q_perf = pd.DataFrame()
    
    # Page performance with impression-weighted position
    if "landing_page" in df_gsc_calc.columns:
        p_perf = df_gsc_calc.groupby("landing_page").agg(
            clicks=("clicks", "sum"),
            impressions=("impressions", "sum"),
            pos_x_imp=("pos_x_imp", "sum")
        ).reset_index()
        p_perf["ctr"] = safe_divide(p_perf["clicks"], p_perf["impressions"])
        p_perf["avg_position"] = safe_divide(p_perf["pos_x_imp"], p_perf["impressions"]).round(1)
        p_perf = p_perf.drop(columns=["pos_x_imp"]).sort_values(by="clicks", ascending=False)
    else:
        p_perf = pd.DataFrame()
    
    # Daily trend with impression-weighted position
    if "date" in df_gsc_calc.columns:
        daily = df_gsc_calc.groupby("date").agg(
            clicks=("clicks", "sum"),
            impressions=("impressions", "sum"),
            pos_x_imp=("pos_x_imp", "sum")
        ).reset_index()
        daily["ctr"] = safe_divide(daily["clicks"], daily["impressions"])
        daily["avg_position"] = safe_divide(daily["pos_x_imp"], daily["impressions"]).round(1)
        daily = daily.drop(columns=["pos_x_imp"]).sort_values(by="date")
    else:
        daily = pd.DataFrame()
    
    return {
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "avg_ctr": avg_ctr,
        "avg_position": avg_pos,
        "query_performance": q_perf,
        "page_performance": p_perf,
        "daily_trend": daily
    }


def compute_google_ads_kpis(filtered_data):
    """
    Compute Google Ads KPIs, campaign table, date trends, and ROAS.
    Explicitly distinguishes:
    1. Google Ads Reported ROAS = Ads Conversion Value / Ads Spend
    2. GA4 Paid ROAS = GA4 Attributed Revenue from Google Ads / Ads Spend
    """
    df_ads = filtered_data.get("google_ads", pd.DataFrame())
    df_sess = filtered_data.get("sessions", pd.DataFrame())
    
    if df_ads.empty:
        return {
            "total_spend": 0.0,
            "total_impressions": 0,
            "total_clicks": 0,
            "total_conversions": 0,
            "total_conversion_value": 0.0,
            "avg_cpc": 0.0,
            "cpa": 0.0,
            "ads_reported_roas": 0.0,
            "ga4_paid_revenue": 0.0,
            "ga4_paid_roas": 0.0,
            "roas": 0.0,
            "campaign_performance": pd.DataFrame(),
            "daily_trend": pd.DataFrame()
        }
        
    total_spend = float(df_ads["cost"].sum())
    total_imp = int(df_ads["impressions"].sum())
    total_clicks = int(df_ads["clicks"].sum())
    total_conv = int(df_ads["conversions"].sum())
    total_val = float(df_ads["conversion_value"].sum())
    
    avg_cpc = safe_divide(total_spend, total_clicks)
    cpa = safe_divide(total_spend, total_conv)
    
    # 1. Google Ads self-reported ROAS
    ads_reported_roas = safe_divide(total_val, total_spend)
    
    # 2. GA4 Paid Revenue and ROAS for Google Ads channel
    ga4_paid_sess = df_sess[df_sess["acquisition_source"] == "Google Ads"] if not df_sess.empty else pd.DataFrame()
    ga4_paid_revenue = float(ga4_paid_sess["revenue"].sum()) if not ga4_paid_sess.empty else 0.0
    ga4_paid_roas = safe_divide(ga4_paid_revenue, total_spend)
    
    # Campaign performance
    camp_perf = df_ads.groupby("campaign").agg(
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        cost=("cost", "sum"),
        conversions=("conversions", "sum"),
        conversion_value=("conversion_value", "sum")
    ).reset_index()
    camp_perf["ctr"] = safe_divide(camp_perf["clicks"], camp_perf["impressions"])
    camp_perf["avg_cpc"] = safe_divide(camp_perf["cost"], camp_perf["clicks"])
    camp_perf["cpa"] = safe_divide(camp_perf["cost"], camp_perf["conversions"])
    camp_perf["ads_reported_roas"] = safe_divide(camp_perf["conversion_value"], camp_perf["cost"])
    camp_perf["roas"] = camp_perf["ads_reported_roas"]
    camp_perf = camp_perf.sort_values(by="cost", ascending=False)
    
    # Daily trend
    daily = df_ads.groupby("date").agg(
        cost=("cost", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
        conversion_value=("conversion_value", "sum")
    ).reset_index()
    daily["roas"] = safe_divide(daily["conversion_value"], daily["cost"])
    daily["ads_reported_roas"] = daily["roas"]
    
    return {
        "total_spend": total_spend,
        "total_impressions": total_imp,
        "total_clicks": total_clicks,
        "total_conversions": total_conv,
        "total_conversion_value": total_val,
        "avg_cpc": avg_cpc,
        "cpa": cpa,
        "ads_reported_roas": ads_reported_roas,
        "ga4_paid_revenue": ga4_paid_revenue,
        "ga4_paid_roas": ga4_paid_roas,
        "roas": ads_reported_roas,
        "campaign_performance": camp_perf,
        "daily_trend": daily
    }
