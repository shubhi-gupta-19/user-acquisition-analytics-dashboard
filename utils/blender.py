"""
Cross-channel data blending module.
Performs defensible aggregation and alignment across GA4, Search Console, and Google Ads
using shared dimensions (Date, Landing Page, Campaign) while explaining attribution limitations
and preventing double-counting or false row-level joins.
"""

import pandas as pd
import numpy as np
from utils.metrics import safe_divide


ATTRIBUTION_DOCUMENTATION = """
### 📐 Cross-Channel Data Blending Architecture & Attribution Framework

#### 1. Shared Dimensions & Join Keys
* **Calendar Date (`YYYY-MM-DD`)**: Available across GA4, Google Search Console, and Google Ads. Enables unified time-series trend analysis.
* **Landing Page / URL Path**: Shared between GA4 and Google Search Console. Connects organic search ranking/clicks with on-site engagement and revenue.
* **Campaign Name**: Shared between Google Ads and GA4 (`source_medium == 'google / cpc'`). Enables cost, ROAS, and conversion reconciliation.

#### 2. Granularity Mismatch & Relational Integrity
* **Search Console**: Highly aggregated at `Date × Query × Landing Page × Country × Device`. Does **not** track session IDs or cookies.
* **Google Ads**: Aggregated at `Date × Campaign × Ad Group × Device`. Does **not** expose individual user IDs in standard exports.
* **GA4 Sessions & Events**: Event/Session grain with `session_id`, `user_id`, and exact timestamps.
* **Safeguard**: We **never** perform synthetic 1-to-1 row merges between Search Console clicks and individual GA4 sessions, or attribute Ads spend to arbitrary user IDs. Merging is strictly executed at aggregated dimensional intersections (`Date`, `Landing Page`, `Campaign`).

#### 3. Attribution Differences & ROAS Metric Definitions
* **Blended ROAS (All-Channel Revenue / Ad Spend)**:
  * Formula: `Total GA4 Revenue (All channels: Organic, Direct, Social, Email, Paid) / Total Google Ads Spend`.
  * *Important*: This measures overall top-line marketing efficiency per ad dollar spent. It is **not** an ad-attributed ROAS because it includes revenue from unpaid sources.
* **GA4 Paid-Channel Revenue / Ad Spend (GA4 Paid ROAS)**:
  * Formula: `GA4 Google Ads Attributed Revenue / Total Google Ads Spend`.
  * Uses GA4's cross-channel data-driven attribution (DDA), crediting multiple touchpoints.
* **Google Ads Reported ROAS (Conversion Value / Ad Spend)**:
  * Formula: `Google Ads Conversion Value / Google Ads Spend`.
  * Sourced directly from Google Ads campaign reporting. Ads defaults to attributing conversions to the last paid Google touchpoint.

#### 4. Traffic & Metric Nuances
* **Advertising CPC vs. Cost per GA4 Session**:
  * Advertising CPC is strictly `Google Ads Spend / Google Ads Clicks`.
  * Cost per GA4 Session is `Google Ads Spend / GA4 Google Ads Sessions`. These differ due to click-to-session drop-offs (e.g., ad blockers, cookie rejection, page bounce before GA4 script load).
* **Search Console Impression-Weighted Average Position**:
  * Organic position across multiple rows or queries is computed as `sum(position * impressions) / sum(impressions)`. An unweighted arithmetic mean is misleading because low-traffic long-tail keywords skew the metric.
"""


def build_daily_blended_data(filtered_data):
    """
    Builds a unified daily time-series combining GA4, Search Console, and Google Ads metrics.
    Guarantees no Cartesian explosion by aggregating each source to Date grain before merging.
    """
    df_sess = filtered_data.get("sessions", pd.DataFrame())
    df_gsc = filtered_data.get("search_console", pd.DataFrame())
    df_ads = filtered_data.get("google_ads", pd.DataFrame())
    
    # 1. Aggregate GA4 by Date
    if not df_sess.empty:
        # Total GA4
        ga4_total = df_sess.groupby("date").agg(
            ga4_total_sessions=("session_id", "count"),
            ga4_total_users=("user_id", "nunique"),
            ga4_total_conversions=("has_conversion", "sum"),
            ga4_total_revenue=("revenue", "sum")
        ).reset_index()
        
        # Organic GA4
        ga4_org = df_sess[df_sess["acquisition_source"] == "Google Organic"].groupby("date").agg(
            ga4_organic_sessions=("session_id", "count"),
            ga4_organic_conversions=("has_conversion", "sum"),
            ga4_organic_revenue=("revenue", "sum")
        ).reset_index()
        
        # Paid Google Ads GA4
        ga4_paid = df_sess[df_sess["acquisition_source"] == "Google Ads"].groupby("date").agg(
            ga4_paid_sessions=("session_id", "count"),
            ga4_paid_conversions=("has_conversion", "sum"),
            ga4_paid_revenue=("revenue", "sum")
        ).reset_index()
        
        ga4_daily = pd.merge(ga4_total, ga4_org, on="date", how="left").fillna(0)
        ga4_daily = pd.merge(ga4_daily, ga4_paid, on="date", how="left").fillna(0)
    else:
        ga4_daily = pd.DataFrame(columns=[
            "date", "ga4_total_sessions", "ga4_total_users", "ga4_total_conversions", "ga4_total_revenue",
            "ga4_organic_sessions", "ga4_organic_conversions", "ga4_organic_revenue",
            "ga4_paid_sessions", "ga4_paid_conversions", "ga4_paid_revenue"
        ])

    # 2. Aggregate Search Console by Date
    if not df_gsc.empty:
        df_gsc_calc = df_gsc.copy()
        df_gsc_calc["pos_x_imp"] = df_gsc_calc["position"] * df_gsc_calc["impressions"]
        gsc_daily = df_gsc_calc.groupby("date").agg(
            gsc_clicks=("clicks", "sum"),
            gsc_impressions=("impressions", "sum"),
            pos_x_imp=("pos_x_imp", "sum")
        ).reset_index()
        gsc_daily["gsc_ctr"] = safe_divide(gsc_daily["gsc_clicks"], gsc_daily["gsc_impressions"])
        gsc_daily["gsc_avg_position"] = safe_divide(gsc_daily["pos_x_imp"], gsc_daily["gsc_impressions"]).round(1)
        gsc_daily = gsc_daily.drop(columns=["pos_x_imp"])
    else:
        gsc_daily = pd.DataFrame(columns=["date", "gsc_clicks", "gsc_impressions", "gsc_ctr", "gsc_avg_position"])

    # 3. Aggregate Google Ads by Date
    if not df_ads.empty:
        ads_daily = df_ads.groupby("date").agg(
            ads_cost=("cost", "sum"),
            ads_clicks=("clicks", "sum"),
            ads_impressions=("impressions", "sum"),
            ads_conversions=("conversions", "sum"),
            ads_conversion_value=("conversion_value", "sum")
        ).reset_index()
    else:
        ads_daily = pd.DataFrame(columns=[
            "date", "ads_cost", "ads_clicks", "ads_impressions", "ads_conversions", "ads_conversion_value"
        ])

    # 4. Determine full union of dates
    date_series = []
    if not ga4_daily.empty:
        date_series.append(ga4_daily["date"])
    if not gsc_daily.empty:
        date_series.append(gsc_daily["date"])
    if not ads_daily.empty:
        date_series.append(ads_daily["date"])
        
    if not date_series:
        return pd.DataFrame()
        
    all_dates = pd.DataFrame({"date": sorted(pd.concat(date_series).unique())})
    
    # 5. Safe outer merges
    blended = pd.merge(all_dates, ga4_daily, on="date", how="left").fillna(0)
    blended = pd.merge(blended, gsc_daily, on="date", how="left").fillna(0)
    blended = pd.merge(blended, ads_daily, on="date", how="left").fillna(0)
    
    # 6. Compute Cross-Source Comparison Ratios
    blended["organic_click_to_session_ratio"] = safe_divide(blended["ga4_organic_sessions"], blended["gsc_clicks"])
    blended["paid_click_to_session_ratio"] = safe_divide(blended["ga4_paid_sessions"], blended["ads_clicks"])
    blended["blended_roas"] = safe_divide(blended["ga4_total_revenue"], blended["ads_cost"])
    blended["ga4_paid_roas"] = safe_divide(blended["ga4_paid_revenue"], blended["ads_cost"])
    blended["paid_roas"] = blended["ga4_paid_roas"]  # backwards compatibility alias
    blended["ads_reported_roas"] = safe_divide(blended["ads_conversion_value"], blended["ads_cost"])
    
    return blended.sort_values(by="date")


def build_landing_page_blended_data(filtered_data):
    """
    Blends organic search metrics (GSC) with on-site engagement and conversion metrics (GA4)
    at the Landing Page level, using impression-weighted position for GSC rankings.
    """
    df_sess = filtered_data.get("sessions", pd.DataFrame())
    df_gsc = filtered_data.get("search_console", pd.DataFrame())
    
    if df_sess.empty and df_gsc.empty:
        return pd.DataFrame()
        
    # Organic GA4 by Landing Page
    if not df_sess.empty:
        ga4_org_page = df_sess[df_sess["acquisition_source"] == "Google Organic"].groupby("landing_page").agg(
            organic_sessions=("session_id", "count"),
            organic_users=("user_id", "nunique"),
            engaged_sessions=("is_engaged_session", "sum"),
            conversions=("has_conversion", "sum"),
            revenue=("revenue", "sum")
        ).reset_index()
        ga4_org_page["engagement_rate"] = safe_divide(ga4_org_page["engaged_sessions"], ga4_org_page["organic_sessions"])
        ga4_org_page["conversion_rate"] = safe_divide(ga4_org_page["conversions"], ga4_org_page["organic_sessions"])
    else:
        ga4_org_page = pd.DataFrame(columns=[
            "landing_page", "organic_sessions", "organic_users", "engaged_sessions", "conversions", "revenue", "engagement_rate", "conversion_rate"
        ])
        
    # GSC by Landing Page with impression-weighted average position
    if not df_gsc.empty:
        df_gsc_calc = df_gsc.copy()
        df_gsc_calc["pos_x_imp"] = df_gsc_calc["position"] * df_gsc_calc["impressions"]
        gsc_page = df_gsc_calc.groupby("landing_page").agg(
            gsc_clicks=("clicks", "sum"),
            gsc_impressions=("impressions", "sum"),
            pos_x_imp=("pos_x_imp", "sum")
        ).reset_index()
        gsc_page["gsc_ctr"] = safe_divide(gsc_page["gsc_clicks"], gsc_page["gsc_impressions"])
        gsc_page["avg_position"] = safe_divide(gsc_page["pos_x_imp"], gsc_page["gsc_impressions"]).round(1)
        gsc_page = gsc_page.drop(columns=["pos_x_imp"])
    else:
        gsc_page = pd.DataFrame(columns=["landing_page", "gsc_clicks", "gsc_impressions", "avg_position", "gsc_ctr"])
        
    merged = pd.merge(gsc_page, ga4_org_page, on="landing_page", how="outer").fillna(0)
    merged["click_to_session_ratio"] = safe_divide(merged["organic_sessions"], merged["gsc_clicks"])
    
    return merged.sort_values(by="gsc_clicks", ascending=False)


def build_campaign_blended_data(filtered_data):
    """
    Blends Google Ads campaign costs and reported conversions with GA4 recorded sessions
    and DDA attributed conversions/revenue for the same campaigns.
    """
    df_sess = filtered_data.get("sessions", pd.DataFrame())
    df_ads = filtered_data.get("google_ads", pd.DataFrame())
    
    if df_sess.empty and df_ads.empty:
        return pd.DataFrame()
        
    # GA4 Google Ads campaigns
    if not df_sess.empty:
        ga4_camp = df_sess[df_sess["acquisition_source"] == "Google Ads"].groupby("campaign").agg(
            ga4_sessions=("session_id", "count"),
            ga4_conversions=("has_conversion", "sum"),
            ga4_revenue=("revenue", "sum")
        ).reset_index()
    else:
        ga4_camp = pd.DataFrame(columns=["campaign", "ga4_sessions", "ga4_conversions", "ga4_revenue"])
        
    # Google Ads performance
    if not df_ads.empty:
        ads_camp = df_ads.groupby("campaign").agg(
            ads_impressions=("impressions", "sum"),
            ads_clicks=("clicks", "sum"),
            ads_cost=("cost", "sum"),
            ads_conversions=("conversions", "sum"),
            ads_conv_value=("conversion_value", "sum")
        ).reset_index()
    else:
        ads_camp = pd.DataFrame(columns=["campaign", "ads_impressions", "ads_clicks", "ads_cost", "ads_conversions", "ads_conv_value"])
        
    merged = pd.merge(ads_camp, ga4_camp, on="campaign", how="outer").fillna(0)
    
    merged["ads_cpc"] = safe_divide(merged["ads_cost"], merged["ads_clicks"])
    merged["ads_cpa"] = safe_divide(merged["ads_cost"], merged["ads_conversions"])
    merged["ga4_roas"] = safe_divide(merged["ga4_revenue"], merged["ads_cost"])
    merged["ads_reported_roas"] = safe_divide(merged["ads_conv_value"], merged["ads_cost"])
    merged["conversion_gap"] = merged["ads_conversions"] - merged["ga4_conversions"]
    
    return merged.sort_values(by="ads_cost", ascending=False)
