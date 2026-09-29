"""
User Acquisition & Behavior Analytics Dashboard
A complete, professional, interactive Python analytics platform built with Streamlit, Pandas, Plotly, and NumPy.
Explicitly uses SAMPLE / SYNTHETIC DATA across 90 days with cross-channel relational consistency.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils.data_loader import (
    load_all_datasets,
    filter_datasets,
    get_available_filter_options,
    DATA_DICTIONARIES
)
from utils.generate_data import generate_all_datasets
from utils.metrics import (
    compute_executive_kpis,
    compute_acquisition_breakdown,
    compute_funnel_metrics,
    compute_events_kpis,
    compute_search_console_kpis,
    compute_google_ads_kpis,
    safe_divide
)
from utils.blender import (
    build_daily_blended_data,
    build_landing_page_blended_data,
    build_campaign_blended_data,
    ATTRIBUTION_DOCUMENTATION
)
from utils.charts import (
    create_dual_line_chart,
    create_donut_chart,
    create_horizontal_bar_chart,
    create_funnel_chart,
    create_scatter_plot,
    create_grouped_bar_chart,
    CHART_THEME
)
from utils.ui import (
    inject_custom_css,
    render_synthetic_notice,
    render_kpi,
    render_real_data_instructions
)

# ---------------- Streamlit App Configuration ----------------
st.set_page_config(
    page_title="User Acquisition & Behavior Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS styling
inject_custom_css()

# Load raw datasets with cache
raw_data = load_all_datasets()
filter_opts = get_available_filter_options(raw_data)

# ---------------- Sidebar Filter State Management ----------------
st.sidebar.markdown("### 🎛️ Global Filters")

# Initialize session state for filters if not set
if "filter_start_date" not in st.session_state:
    st.session_state["filter_start_date"] = filter_opts["min_date"]
if "filter_end_date" not in st.session_state:
    st.session_state["filter_end_date"] = filter_opts["max_date"]
if "filter_sources" not in st.session_state:
    st.session_state["filter_sources"] = filter_opts["sources"]
if "filter_devices" not in st.session_state:
    st.session_state["filter_devices"] = filter_opts["devices"]
if "filter_campaigns" not in st.session_state:
    st.session_state["filter_campaigns"] = filter_opts["campaigns"]

# Preset Buttons for quick date filtering
col_btn1, col_btn2, col_btn3 = st.sidebar.columns(3)
if col_btn1.button("Last 30D", use_container_width=True):
    st.session_state["filter_start_date"] = filter_opts["max_date"] - timedelta(days=29)
    st.session_state["filter_end_date"] = filter_opts["max_date"]
    st.rerun()

if col_btn2.button("Last 60D", use_container_width=True):
    st.session_state["filter_start_date"] = filter_opts["max_date"] - timedelta(days=59)
    st.session_state["filter_end_date"] = filter_opts["max_date"]
    st.rerun()

if col_btn3.button("Full 90D", use_container_width=True):
    st.session_state["filter_start_date"] = filter_opts["min_date"]
    st.session_state["filter_end_date"] = filter_opts["max_date"]
    st.rerun()

# Date Range Picker
selected_date_range = st.sidebar.date_input(
    "Date Range",
    value=(st.session_state["filter_start_date"], st.session_state["filter_end_date"]),
    min_value=filter_opts["min_date"],
    max_value=filter_opts["max_date"],
    key="date_picker"
)

if isinstance(selected_date_range, (tuple, list)) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
    st.session_state["filter_start_date"] = start_date
    st.session_state["filter_end_date"] = end_date
else:
    start_date = st.session_state["filter_start_date"]
    end_date = st.session_state["filter_end_date"]

# Acquisition Source Multi-select
selected_sources = st.sidebar.multiselect(
    "Acquisition Channel",
    options=filter_opts["sources"],
    default=st.session_state["filter_sources"],
    help="Filter GA4 sessions and cascades down to events and channel tables"
)
st.session_state["filter_sources"] = selected_sources

# Campaign Multi-select
selected_campaigns = st.sidebar.multiselect(
    "Campaign",
    options=filter_opts["campaigns"],
    default=st.session_state["filter_campaigns"],
    help="Filter campaigns across GA4 and Google Ads"
)
st.session_state["filter_campaigns"] = selected_campaigns

# Device Category Multi-select
selected_devices = st.sidebar.multiselect(
    "Device Category",
    options=filter_opts["devices"],
    default=st.session_state["filter_devices"],
    help="Filter traffic by Desktop, Mobile, and Tablet"
)
st.session_state["filter_devices"] = selected_devices

# Reset Filters Button
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.session_state["filter_start_date"] = filter_opts["min_date"]
    st.session_state["filter_end_date"] = filter_opts["max_date"]
    st.session_state["filter_sources"] = filter_opts["sources"]
    st.session_state["filter_campaigns"] = filter_opts["campaigns"]
    st.session_state["filter_devices"] = filter_opts["devices"]
    st.rerun()

st.sidebar.markdown("---")

# Navigation Selector
page = st.sidebar.radio(
    "Dashboard Navigation",
    options=[
        "📊 Executive Overview",
        "🚀 Acquisition Analysis",
        "🔄 User Journey & Funnel",
        "⚡ Events & Engagement",
        "🔍 Google Search Console",
        "💰 Google Ads Performance",
        "🔀 Cross-Channel Analysis",
        "🗄️ Dataset Explorer"
    ]
)

st.sidebar.markdown("---")
# Dataset Health Badge in sidebar
st.sidebar.caption(
    f"🟢 **4 Datasets Loaded (Offline)**\n"
    f"- GA4 Sessions: {len(raw_data['sessions']):,} rows\n"
    f"- GA4 Events: {len(raw_data['events']):,} rows\n"
    f"- Search Console: {len(raw_data['search_console']):,} rows\n"
    f"- Google Ads: {len(raw_data['google_ads']):,} rows\n"
    f"*(Synthetic 90-day window: {filter_opts['min_date']} to {filter_opts['max_date']})*"
)

# Apply global defensive filtering
filtered_data = filter_datasets(
    raw_data,
    start_date=start_date,
    end_date=end_date,
    sources=selected_sources,
    campaigns=selected_campaigns,
    devices=selected_devices
)

# Main Application Banner
render_synthetic_notice()

# Graceful Empty Filter State Handling
if filtered_data["sessions"].empty:
    st.warning(
        "⚠️ **No records match your selected filters.**\n\n"
        "Please adjust your date range, select at least one Acquisition Channel, or click 'Reset All Filters' in the sidebar."
    )
    st.stop()


# ==============================================================================
# 1. EXECUTIVE OVERVIEW
# ==============================================================================
if page == "📊 Executive Overview":
    st.title("📊 Executive Overview")
    st.markdown("High-level performance metrics, cross-channel revenue, and growth trajectories over the selected timeframe.")
    
    kpis = compute_executive_kpis(filtered_data)
    
    # Row 1: Traffic & Engagement KPIs
    c1, c2, c3, c4 = st.columns(4)
    render_kpi(c1, "Total Sessions", f"{kpis['total_sessions']:,}", "Active visitor sessions")
    render_kpi(c2, "Total Users", f"{kpis['total_users']:,}", "Distinct user IDs tracked")
    render_kpi(c3, "Engaged Sessions", f"{kpis['engaged_sessions']:,}", "Sessions >=10s or 2+ views")
    render_kpi(c4, "Engagement Rate", f"{kpis['engagement_rate']*100:.1f}%", "Engaged / Total Sessions")
    
    # Row 2: Conversion & Financial KPIs
    c5, c6, c7, c8 = st.columns(4)
    render_kpi(c5, "Total Conversions", f"{kpis['total_conversions']:,}", "Completed purchases")
    render_kpi(c6, "Conversion Rate", f"{kpis['conversion_rate']*100:.2f}%", "Purchases / Sessions")
    render_kpi(c7, "Total Revenue (All Channels)", f"${kpis['total_revenue']:,.2f}", f"Avg Order: ${kpis['avg_order_value']:.2f}")
    roas_label = f"{kpis['blended_roas']:.2f}x" if kpis['blended_roas'] > 0 else "N/A"
    render_kpi(c8, "Blended ROAS (All Rev / Spend)", roas_label, f"Ad Spend: ${kpis['total_ad_spend']:,.2f}")
    
    st.markdown("<div class='section-header'><span class='section-title'>📈 Trends & Channel Mix</span></div>", unsafe_allow_html=True)
    
    # Charts Row 1: Daily Sessions & Conversions + Acquisition Channel Contribution
    chart_col1, chart_col2 = st.columns([1.6, 1.0])
    
    with chart_col1:
        daily_sess = filtered_data["sessions"].groupby("date").agg(
            sessions=("session_id", "count"),
            conversions=("has_conversion", "sum")
        ).reset_index()
        fig_trend = create_dual_line_chart(
            daily_sess,
            date_col="date",
            col_left="sessions",
            col_right="conversions",
            title="Daily Sessions & Conversions Over Time",
            name_left="Sessions",
            name_right="Conversions"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with chart_col2:
        source_mix = filtered_data["sessions"]["acquisition_source"].value_counts().reset_index()
        source_mix.columns = ["source", "count"]
        fig_donut = create_donut_chart(
            source_mix,
            labels_col="source",
            values_col="count",
            title="Acquisition Channel Distribution"
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
    # Charts Row 2: Device Mix & Conversion Rate by Channel
    chart_col3, chart_col4 = st.columns([1.0, 1.6])
    
    with chart_col3:
        dev_mix = filtered_data["sessions"]["device_category"].value_counts().reset_index()
        dev_mix.columns = ["device", "count"]
        fig_dev = create_donut_chart(
            dev_mix,
            labels_col="device",
            values_col="count",
            title="Device Category Share",
            hole=0.60
        )
        st.plotly_chart(fig_dev, use_container_width=True)
        
    with chart_col4:
        acq_df = compute_acquisition_breakdown(filtered_data)
        src_cr = acq_df.groupby("acquisition_source").agg(
            sessions=("sessions", "sum"),
            conversions=("conversions", "sum")
        ).reset_index()
        src_cr["conversion_rate"] = safe_divide(src_cr["conversions"], src_cr["sessions"])
        fig_cr_bar = create_horizontal_bar_chart(
            src_cr,
            y_col="acquisition_source",
            x_col="conversion_rate",
            title="Conversion Rate (%) by Acquisition Source",
            x_title="Conversion Rate",
            is_percent=True
        )
        st.plotly_chart(fig_cr_bar, use_container_width=True)
        
    # Executive Insights Callout
    with st.expander("💡 Executive Summary & Strategic Takeaways", expanded=True):
        st.markdown(
            f"""
            * **Traffic Stability**: Over the selected period, the business generated **{kpis['total_sessions']:,} sessions** across **{kpis['total_users']:,} unique users**, maintaining an engagement rate of **{kpis['engagement_rate']*100:.1f}%**.
            * **Commercial Velocity**: **{kpis['total_conversions']:,} customer conversions** were recorded, producing **${kpis['total_revenue']:,.2f} in revenue** at an average order value of **${kpis['avg_order_value']:.2f}**.
            * **ROAS Breakdown & Attribution**:
              * **Blended ROAS (All-Channel Revenue / Ad Spend)**: **{roas_label}** (${kpis['total_revenue']:,.2f} total revenue / ${kpis['total_ad_spend']:,.2f} ad spend). *Note: Measures top-line business efficiency across all sources, not Ads-attributed return.*
              * **GA4 Paid-Channel Revenue / Ad Spend**: **{kpis['ga4_paid_roas']:.2f}x** (${kpis['ga4_paid_revenue']:,.2f} GA4 Google Ads revenue / ${kpis['total_ad_spend']:,.2f} ad spend).
              * **Google Ads Reported ROAS**: **{kpis['ads_reported_roas']:.2f}x** (${kpis['ads_reported_conversion_value']:,.2f} self-reported Ads conversion value / ${kpis['total_ad_spend']:,.2f} ad spend).
            * **Channel Highlights**: Direct and Email traffic exhibit the highest intent conversion rates, while Google Organic and Google Ads form the primary top-of-funnel acquisition pipeline.
            """
        )


# ==============================================================================
# 2. ACQUISITION ANALYSIS
# ==============================================================================
elif page == "🚀 Acquisition Analysis":
    st.title("🚀 Acquisition Channel Performance")
    st.markdown("Detailed breakdown of user acquisition channels, campaigns, conversion rates, and unit economics.")
    
    acq_df = compute_acquisition_breakdown(filtered_data)
    
    # Top Level Channel Summary
    st.markdown("<div class='section-header'><span class='section-title'>📊 Channel Performance Table</span></div>", unsafe_allow_html=True)
    
    # Format table for display
    display_df = acq_df.copy()
    display_df["Engagement Rate"] = display_df["engagement_rate"].apply(lambda v: f"{v*100:.1f}%")
    display_df["Conversion Rate"] = display_df["conversion_rate"].apply(lambda v: f"{v*100:.2f}%")
    display_df["Revenue ($)"] = display_df["revenue"].apply(lambda v: f"${v:,.2f}")
    display_df["Ad Spend ($)"] = display_df["cost"].apply(lambda v: f"${v:,.2f}" if v > 0 else "-")
    display_df["Ads CPC ($)"] = display_df["ads_cpc"].apply(lambda v: f"${v:.2f}" if v > 0 else "-")
    display_df["Cost / GA4 Session ($)"] = display_df["cost_per_ga4_session"].apply(lambda v: f"${v:.2f}" if v > 0 else "-")
    display_df["GA4 Paid ROAS"] = display_df["roas"].apply(lambda v: f"{v:.2f}x" if v > 0 else "-")
    
    st.dataframe(
        display_df[[
            "acquisition_source", "source_medium", "campaign", "users", "sessions",
            "engaged_sessions", "Engagement Rate", "conversions", "Conversion Rate",
            "Revenue ($)", "Ad Spend ($)", "Ads CPC ($)", "Cost / GA4 Session ($)", "GA4 Paid ROAS"
        ]].rename(columns={
            "acquisition_source": "Channel",
            "source_medium": "Source / Medium",
            "campaign": "Campaign",
            "users": "Users",
            "sessions": "Sessions",
            "engaged_sessions": "Engaged",
            "conversions": "Conversions"
        }),
        use_container_width=True,
        hide_index=True
    )
    st.caption("ℹ️ **Metric Distinctions:** **Ads CPC** is calculated as Google Ads Spend / Google Ads Clicks. **Cost / GA4 Session** is Google Ads Spend / GA4 Sessions. **GA4 Paid ROAS** is GA4 Attributed Revenue / Ad Spend for paid campaigns.")
    
    # Charts: Revenue vs Cost & Efficiency comparison
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        rev_by_channel = acq_df.groupby("acquisition_source").agg(
            revenue=("revenue", "sum"),
            cost=("cost", "sum")
        ).reset_index()
        fig_rev_cost = create_grouped_bar_chart(
            rev_by_channel,
            x_col="acquisition_source",
            y1_col="revenue",
            y2_col="cost",
            title="Revenue vs Ad Cost by Acquisition Channel ($)",
            name1="Revenue ($)",
            name2="Ad Cost ($)",
            y_title="USD ($)"
        )
        st.plotly_chart(fig_rev_cost, use_container_width=True)
        
    with c_chart2:
        fig_scatter = create_scatter_plot(
            acq_df,
            x_col="engagement_rate",
            y_col="conversion_rate",
            size_col="sessions",
            text_col="campaign",
            title="Engagement Rate vs Conversion Rate by Campaign",
            x_title="Engagement Rate",
            y_title="Conversion Rate"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    # Download Channel Performance Report
    csv_bytes = acq_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Channel Performance CSV",
        data=csv_bytes,
        file_name=f"acquisition_performance_{start_date}_{end_date}.csv",
        mime="text/csv"
    )


# ==============================================================================
# 3. USER JOURNEY & FUNNEL
# ==============================================================================
elif page == "🔄 User Journey & Funnel":
    st.title("🔄 User Journey & E-Commerce Funnel")
    st.markdown("Step-by-step user conversion progression from entry to final transaction.")
    
    funnel = compute_funnel_metrics(filtered_data)
    
    # Funnel Definition Documentation
    with st.expander("ℹ️ Chronological Funnel Methodology & Denominator Definitions", expanded=False):
        st.markdown(
            """
            * **Chronological Sequential Progression**:
              * **Stage 1 (Session / Landing Page)**: All unique entry sessions initiating on the site.
              * **Stage 2 (View Item / Plan)**: Sessions recording `view_item` event at or after session start.
              * **Stage 3 (Add to Cart)**: Sessions recording `add_to_cart` event **strictly chronologically at or after** qualifying Stage 2.
              * **Stage 4 (Begin Checkout)**: Sessions recording `begin_checkout` event **strictly chronologically at or after** qualifying Stage 3.
              * **Stage 5 (Purchase)**: Completed payment confirmation (`purchase`) **strictly chronologically at or after** qualifying Stage 4.
            * **Strict Sequencing Safeguards**:
              * Out-of-order events (e.g., purchase recorded before add-to-cart or checkout) do **not** qualify as a completed sequential journey.
              * Skipped stages disqualify later events from progressing.
            * **Dual Conversion Rate Metrics & Explicit Denominators**:
              * **Entry-Session Conversion Rate (%)**: Measures overall retention from the top of the funnel:
                $$\\text{Entry-Session Conversion Rate} = \\frac{\\text{Current Stage Sessions}}{\\text{Total Entry Sessions (Stage 1)}} \\times 100$$
                The denominator is strictly **Stage 1 (Total Entry Sessions)** for all stages.
              * **Step Conversion Rate (%)**: Measures step-to-step conversion efficiency between consecutive stages:
                $$\\text{Step Conversion Rate} = \\frac{\\text{Current Stage Sessions}}{\\text{Previous Stage Sessions}} \\times 100$$
                The denominator is strictly the **immediately preceding qualifying stage**.
              * **Drop-off Rate (%)**: Percentage of users who abandoned at each step:
                $$\\text{Drop-off Rate} = \\frac{\\text{Previous Stage Sessions} - \\text{Current Stage Sessions}}{\\text{Previous Stage Sessions}} \\times 100$$
            """
        )
        
    # Top KPI cards for Funnel
    f1, f2, f3, f4 = st.columns(4)
    render_kpi(f1, "Top of Funnel (Visits)", f"{funnel['counts'][0]:,}", "Total entry sessions (Stage 1)")
    render_kpi(f2, "Cart Additions", f"{funnel['counts'][2]:,}", f"{safe_divide(funnel['counts'][2], funnel['counts'][0])*100:.1f}% of Stage 1 entry")
    render_kpi(f3, "Checkout Initiated", f"{funnel['counts'][3]:,}", f"{safe_divide(funnel['counts'][3], funnel['counts'][2])*100:.1f}% step CR from cart")
    render_kpi(f4, "End-to-End Conversion", f"{funnel['overall_conversion_rate']*100:.2f}%", f"{funnel['counts'][4]:,} Purchases (vs Stage 1)")
    
    # Funnel Chart and Stage Table
    fn_col1, fn_col2 = st.columns([1.5, 1.0])
    
    with fn_col1:
        fig_funnel = create_funnel_chart(funnel["stages"], funnel["counts"], funnel["drop_offs"])
        st.plotly_chart(fig_funnel, use_container_width=True)
        
    with fn_col2:
        st.markdown("#### 📋 Funnel Progression Summary")
        summary_cols = [
            "Stage",
            "Sessions",
            "Entry-Session Conversion Rate (%)",
            "Step Conversion Rate (%)",
            "Drop-off Rate (%)"
        ]
        st.dataframe(funnel["funnel_df"][summary_cols], use_container_width=True, hide_index=True)
        st.caption("ℹ️ **Entry-Session Conversion Rate (%)** uses Stage 1 (Total Entry Sessions) as the denominator. **Step Conversion Rate (%)** uses the immediately preceding stage as the denominator.")
        
        # Largest Drop-off Warning
        if len(funnel["drop_offs"]) > 1 and funnel["counts"][0] > 0:
            max_drop_idx = int(np.argmax(funnel["drop_offs"][1:])) + 1
            max_drop_val = funnel["drop_offs"][max_drop_idx] * 100
            if max_drop_val > 0:
                st.warning(
                    f"⚠️ **Key Friction Point:** Highest drop-off occurs between **{funnel['stages'][max_drop_idx-1]}** "
                    f"and **{funnel['stages'][max_drop_idx]}** ({max_drop_val:.1f}% drop-off). "
                    f"Optimizing this transition represents the largest immediate revenue opportunity."
                )
            
    # Funnel by Device Category Comparison
    st.markdown("<div class='section-header'><span class='section-title'>📱 Funnel Conversion by Device</span></div>", unsafe_allow_html=True)
    dev_funnel_rows = []
    for dev in filtered_data["sessions"]["device_category"].unique():
        dev_sub = {
            "sessions": filtered_data["sessions"][filtered_data["sessions"]["device_category"] == dev],
            "events": filtered_data["events"]
        }
        res = compute_funnel_metrics(dev_sub)
        dev_funnel_rows.append({
            "Device": dev.capitalize(),
            "Total Sessions": res["counts"][0],
            "View Item": res["counts"][1],
            "Add to Cart": res["counts"][2],
            "Checkout": res["counts"][3],
            "Purchases": res["counts"][4],
            "End-to-End CR (vs Stage 1)": f"{res['overall_conversion_rate']*100:.2f}%"
        })
    st.dataframe(pd.DataFrame(dev_funnel_rows), use_container_width=True, hide_index=True)


# ==============================================================================
# 4. EVENTS & ENGAGEMENT
# ==============================================================================
elif page == "⚡ Events & Engagement":
    st.title("⚡ Events & User Engagement")
    st.markdown("Micro-interaction analysis, custom event distribution, and active user engagement duration.")
    
    evt_kpis = compute_events_kpis(filtered_data)
    
    e1, e2, e3, e4 = st.columns(4)
    render_kpi(e1, "Total Events", f"{evt_kpis['total_events']:,}", "All interaction records")
    render_kpi(e2, "Unique Event Users", f"{evt_kpis['unique_event_users']:,}", "Active participants")
    render_kpi(e3, "Avg Events / Session", f"{evt_kpis['avg_events_per_session']:.1f}", "Micro-interactions")
    render_kpi(e4, "Avg Engagement Time", f"{evt_kpis['avg_engagement_time']:.1f}s", "Seconds on site")
    
    # Event Visualizations
    ev_c1, ev_c2 = st.columns([1.3, 1.0])
    
    with ev_c1:
        if not evt_kpis["event_counts"].empty:
            fig_top_events = create_horizontal_bar_chart(
                evt_kpis["event_counts"],
                y_col="event_name",
                x_col="count",
                title="Event Frequency Breakdown",
                x_title="Event Occurrences"
            )
            st.plotly_chart(fig_top_events, use_container_width=True)
            
    with ev_c2:
        if not evt_kpis["category_counts"].empty:
            fig_cat = create_donut_chart(
                evt_kpis["category_counts"],
                labels_col="event_category",
                values_col="count",
                title="Event Volume by Category"
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
    # Event Stream Table
    st.markdown("<div class='section-header'><span class='section-title'>📋 Raw Event Stream (Filtered View)</span></div>", unsafe_allow_html=True)
    df_ev = filtered_data["events"]
    
    flt_col1, flt_col2 = st.columns([1, 2])
    with flt_col1:
        selected_evt_names = st.multiselect(
            "Filter by Event Name",
            options=sorted(df_ev["event_name"].unique()) if not df_ev.empty else [],
            default=[]
        )
    with flt_col2:
        search_kw = st.text_input("Search Event Records (Session, User, Path, Plan)", "")
        
    display_events = df_ev.copy()
    if selected_evt_names:
        display_events = display_events[display_events["event_name"].isin(selected_evt_names)]
    if search_kw:
        mask = (
            display_events["session_id"].str.contains(search_kw, case=False, na=False) |
            display_events["user_id"].str.contains(search_kw, case=False, na=False) |
            display_events["page_path"].str.contains(search_kw, case=False, na=False) |
            display_events["item_name"].str.contains(search_kw, case=False, na=False)
        )
        display_events = display_events[mask]
        
    st.caption(f"Showing **{len(display_events):,}** of **{len(df_ev):,}** matching events")
    st.dataframe(
        display_events[["timestamp", "session_id", "user_id", "event_name", "event_category", "page_path", "item_name", "event_value"]].head(500),
        use_container_width=True,
        hide_index=True
    )


# ==============================================================================
# 5. GOOGLE SEARCH CONSOLE
# ==============================================================================
elif page == "🔍 Google Search Console":
    st.title("🔍 Google Search Console Performance")
    st.markdown("Organic search visibility, query intent analysis, click-through rates, and average SERP rankings.")
    
    gsc_kpis = compute_search_console_kpis(filtered_data)
    
    g1, g2, g3, g4 = st.columns(4)
    render_kpi(g1, "Organic Clicks", f"{gsc_kpis['total_clicks']:,}", "Visits from Google Search")
    render_kpi(g2, "Organic Impressions", f"{gsc_kpis['total_impressions']:,}", "SERP appearances")
    render_kpi(g3, "Average CTR", f"{gsc_kpis['avg_ctr']*100:.2f}%", "Total Clicks / Impressions")
    render_kpi(g4, "Avg Position (Weighted)", f"{gsc_kpis['avg_position']:.1f}", "sum(pos*imp) / sum(imp)")
    
    # Trends
    if not gsc_kpis["daily_trend"].empty:
        fig_gsc_trend = create_dual_line_chart(
            gsc_kpis["daily_trend"],
            date_col="date",
            col_left="impressions",
            col_right="clicks",
            title="Daily Organic Impressions & Clicks",
            name_left="Impressions",
            name_right="Clicks"
        )
        st.plotly_chart(fig_gsc_trend, use_container_width=True)
        
    # Query & Page Performance Tables
    g_tab1, g_tab2, g_tab3 = st.tabs(["🔑 Top Queries", "📄 Top Landing Pages", "📊 CTR vs Position Curve"])
    
    with g_tab1:
        q_df = gsc_kpis["query_performance"].copy()
        q_df["CTR (%)"] = q_df["ctr"].apply(lambda v: f"{v*100:.2f}%")
        st.dataframe(
            q_df[["query", "clicks", "impressions", "CTR (%)", "avg_position"]].rename(columns={
                "query": "Organic Query",
                "clicks": "Clicks",
                "impressions": "Impressions",
                "avg_position": "Avg Position (Weighted)"
            }),
            use_container_width=True,
            hide_index=True
        )
        
    with g_tab2:
        p_df = gsc_kpis["page_performance"].copy()
        p_df["CTR (%)"] = p_df["ctr"].apply(lambda v: f"{v*100:.2f}%")
        st.dataframe(
            p_df[["landing_page", "clicks", "impressions", "CTR (%)", "avg_position"]].rename(columns={
                "landing_page": "Landing Page URL",
                "clicks": "Clicks",
                "impressions": "Impressions",
                "avg_position": "Avg Position (Weighted)"
            }),
            use_container_width=True,
            hide_index=True
        )
        
    with g_tab3:
        if not q_df.empty:
            fig_pos_ctr = create_scatter_plot(
                q_df,
                x_col="avg_position",
                y_col="ctr",
                size_col="clicks",
                text_col="query",
                title="Organic CTR vs Impression-Weighted Position (SERP Curve)",
                x_title="Impression-Weighted Position (Rank)",
                y_title="Click-Through Rate (CTR)"
            )
            st.plotly_chart(fig_pos_ctr, use_container_width=True)


# ==============================================================================
# 6. GOOGLE ADS PERFORMANCE
# ==============================================================================
elif page == "💰 Google Ads Performance":
    st.title("💰 Google Ads Campaign Performance")
    st.markdown("Paid advertising expenditure, keyword cluster returns, acquisition costs, and ROAS.")
    
    ads_kpis = compute_google_ads_kpis(filtered_data)
    
    a1, a2, a3, a4 = st.columns(4)
    render_kpi(a1, "Total Ad Spend", f"${ads_kpis['total_spend']:,.2f}", f"{ads_kpis['total_clicks']:,} Clicks")
    render_kpi(a2, "Reported Conversions", f"{ads_kpis['total_conversions']:,}", f"${ads_kpis['total_conversion_value']:,.2f} Value")
    render_kpi(a3, "Average CPC", f"${ads_kpis['avg_cpc']:.2f}", f"CPA: ${ads_kpis['cpa']:.2f}")
    render_kpi(a4, "Ads Reported ROAS", f"{ads_kpis['ads_reported_roas']:.2f}x", f"GA4 Paid ROAS: {ads_kpis['ga4_paid_roas']:.2f}x")
    
    st.caption(
        f"ℹ️ **Attribution Clarification:** **Google Ads Reported ROAS** (`{ads_kpis['ads_reported_roas']:.2f}x`) "
        f"is based on self-reported conversion value (${ads_kpis['total_conversion_value']:,.2f} / ${ads_kpis['total_spend']:,.2f}). "
        f"By contrast, **GA4 Paid ROAS** (`{ads_kpis['ga4_paid_roas']:.2f}x`) evaluates revenue attributed to Google Ads "
        f"under GA4 cross-channel data-driven attribution (${ads_kpis['ga4_paid_revenue']:,.2f} / ${ads_kpis['total_spend']:,.2f})."
    )
    
    # Ads Trend Chart
    if not ads_kpis["daily_trend"].empty:
        fig_ads_trend = create_dual_line_chart(
            ads_kpis["daily_trend"],
            date_col="date",
            col_left="cost",
            col_right="conversion_value",
            title="Daily Ad Spend vs Conversion Value ($)",
            name_left="Ad Cost ($)",
            name_right="Conversion Value ($)",
            is_currency_left=True,
            is_currency_right=True
        )
        st.plotly_chart(fig_ads_trend, use_container_width=True)
        
    # Campaign Table
    st.markdown("<div class='section-header'><span class='section-title'>📋 Paid Campaigns Table</span></div>", unsafe_allow_html=True)
    c_df = ads_kpis["campaign_performance"].copy()
    if not c_df.empty:
        c_df["CTR (%)"] = c_df["ctr"].apply(lambda v: f"{v*100:.2f}%")
        c_df["Cost ($)"] = c_df["cost"].apply(lambda v: f"${v:,.2f}")
        c_df["Conv Value ($)"] = c_df["conversion_value"].apply(lambda v: f"${v:,.2f}")
        c_df["Avg CPC ($)"] = c_df["avg_cpc"].apply(lambda v: f"${v:.2f}")
        c_df["CPA ($)"] = c_df["cpa"].apply(lambda v: f"${v:.2f}")
        c_df["Ads Reported ROAS"] = c_df["ads_reported_roas"].apply(lambda v: f"{v:.2f}x")
        
        st.dataframe(
            c_df[[
                "campaign", "impressions", "clicks", "CTR (%)", "Cost ($)",
                "conversions", "Conv Value ($)", "Avg CPC ($)", "CPA ($)", "Ads Reported ROAS"
            ]].rename(columns={
                "campaign": "Campaign",
                "impressions": "Impressions",
                "clicks": "Clicks",
                "conversions": "Conversions"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No Google Ads records match the active filter criteria.")


# ==============================================================================
# 7. CROSS-CHANNEL ANALYSIS
# ==============================================================================
elif page == "🔀 Cross-Channel Analysis":
    st.title("🔀 Cross-Channel Analysis & Data Blending")
    st.markdown("Unified reconciliation of Google Analytics 4, Search Console, and Google Ads using shared dimensional joins.")
    
    # Architectural Framework Documentation Accordion
    with st.expander("📘 Attribution Principles, Shared Dimensions & Join Rules", expanded=True):
        st.markdown(ATTRIBUTION_DOCUMENTATION)
        
    blended_daily = build_daily_blended_data(filtered_data)
    blended_page = build_landing_page_blended_data(filtered_data)
    blended_camp = build_campaign_blended_data(filtered_data)
    
    # Section 1: Organic & Paid Click-to-Session Comparison Charts
    st.markdown("<div class='section-header'><span class='section-title'>📊 Cross-Source Traffic & Click Reconciliation</span></div>", unsafe_allow_html=True)
    
    cross_c1, cross_c2 = st.columns(2)
    
    with cross_c1:
        st.markdown("##### 🟢 Organic Search: GSC Clicks vs GA4 Organic Sessions")
        fig_org_cross = create_dual_line_chart(
            blended_daily,
            date_col="date",
            col_left="gsc_clicks",
            col_right="ga4_organic_sessions",
            title="GSC Organic Clicks vs GA4 Organic Sessions",
            name_left="GSC Clicks",
            name_right="GA4 Organic Sessions"
        )
        st.plotly_chart(fig_org_cross, use_container_width=True)
        avg_org_ratio = blended_daily["organic_click_to_session_ratio"].mean()
        st.caption(f"ℹ️ Average Organic Click-to-Session Ratio: **{avg_org_ratio:.2f}** (Variance driven by consent banners, bounce drops, and cookie policies).")
        
    with cross_c2:
        st.markdown("##### 🔵 Paid Advertising: Google Ads Clicks vs GA4 Paid Sessions")
        fig_paid_cross = create_dual_line_chart(
            blended_daily,
            date_col="date",
            col_left="ads_clicks",
            col_right="ga4_paid_sessions",
            title="Google Ads Clicks vs GA4 Paid Sessions",
            name_left="Google Ads Clicks",
            name_right="GA4 Paid Sessions"
        )
        st.plotly_chart(fig_paid_cross, use_container_width=True)
        avg_paid_ratio = blended_daily["paid_click_to_session_ratio"].mean()
        st.caption(f"ℹ️ Average Paid Click-to-Session Ratio: **{avg_paid_ratio:.2f}** (Ad clicks vs site-loaded sessions).")

    # Section 2: Combined Daily Blended Table
    st.markdown("<div class='section-header'><span class='section-title'>📅 Daily Blended Performance Table (Date Dimension)</span></div>", unsafe_allow_html=True)
    
    disp_blended = blended_daily.copy()
    disp_blended["Ads Cost ($)"] = disp_blended["ads_cost"].apply(lambda v: f"${v:,.2f}")
    disp_blended["Ads Value ($)"] = disp_blended["ads_conversion_value"].apply(lambda v: f"${v:,.2f}")
    disp_blended["Ads ROAS"] = disp_blended["ads_reported_roas"].apply(lambda v: f"{v:.2f}x" if v > 0 else "-")
    disp_blended["GA4 Paid Rev ($)"] = disp_blended["ga4_paid_revenue"].apply(lambda v: f"${v:,.2f}")
    disp_blended["GA4 Paid ROAS"] = disp_blended["ga4_paid_roas"].apply(lambda v: f"{v:.2f}x" if v > 0 else "-")
    disp_blended["GA4 Total Rev ($)"] = disp_blended["ga4_total_revenue"].apply(lambda v: f"${v:,.2f}")
    disp_blended["Blended ROAS"] = disp_blended["blended_roas"].apply(lambda v: f"{v:.2f}x" if v > 0 else "-")
    
    st.dataframe(
        disp_blended[[
            "date", "ga4_total_sessions", "ga4_organic_sessions", "gsc_clicks",
            "ga4_paid_sessions", "ads_clicks", "Ads Cost ($)", "Ads Value ($)", "Ads ROAS",
            "GA4 Paid Rev ($)", "GA4 Paid ROAS", "GA4 Total Rev ($)", "Blended ROAS"
        ]].rename(columns={
            "date": "Date",
            "ga4_total_sessions": "GA4 Total Sessions",
            "ga4_organic_sessions": "GA4 Org Sessions",
            "gsc_clicks": "GSC Clicks",
            "ga4_paid_sessions": "GA4 Paid Sessions",
            "ads_clicks": "Ads Clicks"
        }).tail(30),
        use_container_width=True,
        hide_index=True
    )
    st.caption("ℹ️ **ROAS Definitions:** **Ads ROAS** = Ads Value / Spend. **GA4 Paid ROAS** = GA4 Paid Rev / Spend. **Blended ROAS** = GA4 Total Rev (All Sources) / Spend.")
    
    # Section 3: Landing Page Alignment Table
    st.markdown("<div class='section-header'><span class='section-title'>📄 Landing Page Cross-Analysis (GSC vs GA4 Organic)</span></div>", unsafe_allow_html=True)
    st.dataframe(
        blended_page.rename(columns={
            "landing_page": "Landing Page URL",
            "gsc_clicks": "GSC Clicks",
            "gsc_impressions": "GSC Impressions",
            "avg_position": "Avg SERP Rank (Weighted)",
            "organic_sessions": "GA4 Org Sessions",
            "organic_users": "GA4 Org Users",
            "conversions": "Organic Conversions",
            "revenue": "Attributed Rev ($)",
            "click_to_session_ratio": "Click:Session Ratio"
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Section 4: Campaign Alignment & Conversion Attribution Gap
    st.markdown("<div class='section-header'><span class='section-title'>🎯 Campaign Reconciliation: Google Ads vs GA4 DDA</span></div>", unsafe_allow_html=True)
    st.dataframe(
        blended_camp.rename(columns={
            "campaign": "Campaign",
            "ads_impressions": "Ads Impressions",
            "ads_clicks": "Ads Clicks",
            "ads_cost": "Ads Spend ($)",
            "ads_conversions": "Ads Reported Convs",
            "ga4_conversions": "GA4 Attributed Convs",
            "conversion_gap": "Attribution Gap",
            "ads_conv_value": "Ads Conv Value ($)",
            "ads_reported_roas": "Ads Reported ROAS",
            "ga4_revenue": "GA4 Attributed Rev ($)",
            "ga4_roas": "GA4 Paid ROAS"
        }),
        use_container_width=True,
        hide_index=True
    )


# ==============================================================================
# 8. DATASET EXPLORER (MANDATORY)
# ==============================================================================
elif page == "🗄️ Dataset Explorer":
    st.title("🗄️ Dataset Explorer & Raw CSV Inspector")
    st.markdown(
        "Supervisor verification portal: inspect the raw rows of each underlying dataset, search records, "
        "review data dictionaries, and export filtered datasets."
    )
    
    # Real data instructions
    render_real_data_instructions()
    
    tab_s, tab_e, tab_g, tab_a, tab_b = st.tabs([
        "1. GA4 Sessions CSV",
        "2. GA4 Events CSV",
        "3. Search Console CSV",
        "4. Google Ads CSV",
        "5. Blended Cross-Channel"
    ])
    
    # ---------------- Tab 1: GA4 Sessions ----------------
    with tab_s:
        st.markdown("### 📊 Google Analytics 4 Sessions (`ga4_sessions.csv`)")
        with st.expander("📖 View Schema & Column Data Dictionary", expanded=False):
            st.json(DATA_DICTIONARIES["ga4_sessions"])
            
        df_curr = filtered_data["sessions"]
        srch_s = st.text_input("🔍 Search Sessions (User, Session, Source, Campaign, Page)", key="srch_sess")
        
        filtered_view = df_curr.copy()
        if srch_s:
            m = (
                filtered_view["session_id"].str.contains(srch_s, case=False, na=False) |
                filtered_view["user_id"].str.contains(srch_s, case=False, na=False) |
                filtered_view["acquisition_source"].str.contains(srch_s, case=False, na=False) |
                filtered_view["campaign"].str.contains(srch_s, case=False, na=False) |
                filtered_view["landing_page"].str.contains(srch_s, case=False, na=False)
            )
            filtered_view = filtered_view[m]
            
        st.caption(f"Showing **{len(filtered_view):,}** of **{len(df_curr):,}** records in active filter window")
        st.dataframe(filtered_view, use_container_width=True, height=450)
        
        st.download_button(
            "📥 Download Filtered Sessions CSV",
            data=filtered_view.to_csv(index=False).encode("utf-8"),
            file_name="ga4_sessions_filtered.csv",
            mime="text/csv",
            key="dl_sess"
        )
        
    # ---------------- Tab 2: GA4 Events ----------------
    with tab_e:
        st.markdown("### ⚡ Google Analytics 4 Events (`ga4_events.csv`)")
        with st.expander("📖 View Schema & Column Data Dictionary", expanded=False):
            st.json(DATA_DICTIONARIES["ga4_events"])
            
        df_curr_e = filtered_data["events"]
        srch_e = st.text_input("🔍 Search Events (Event Name, User, Session, Item)", key="srch_evt")
        
        filtered_view_e = df_curr_e.copy()
        if srch_e:
            m = (
                filtered_view_e["event_name"].str.contains(srch_e, case=False, na=False) |
                filtered_view_e["session_id"].str.contains(srch_e, case=False, na=False) |
                filtered_view_e["user_id"].str.contains(srch_e, case=False, na=False) |
                filtered_view_e["item_name"].str.contains(srch_e, case=False, na=False)
            )
            filtered_view_e = filtered_view_e[m]
            
        st.caption(f"Showing **{len(filtered_view_e):,}** of **{len(df_curr_e):,}** events in active filter window")
        st.dataframe(filtered_view_e, use_container_width=True, height=450)
        
        st.download_button(
            "📥 Download Filtered Events CSV",
            data=filtered_view_e.to_csv(index=False).encode("utf-8"),
            file_name="ga4_events_filtered.csv",
            mime="text/csv",
            key="dl_evt"
        )

    # ---------------- Tab 3: Search Console ----------------
    with tab_g:
        st.markdown("### 🔍 Google Search Console Performance (`search_console.csv`)")
        with st.expander("📖 View Schema & Column Data Dictionary", expanded=False):
            st.json(DATA_DICTIONARIES["search_console"])
            
        df_curr_g = filtered_data["search_console"]
        srch_g = st.text_input("🔍 Search GSC Records (Query, Page, Country)", key="srch_gsc")
        
        filtered_view_g = df_curr_g.copy()
        if srch_g:
            m = (
                filtered_view_g["query"].str.contains(srch_g, case=False, na=False) |
                filtered_view_g["landing_page"].str.contains(srch_g, case=False, na=False) |
                filtered_view_g["country"].str.contains(srch_g, case=False, na=False)
            )
            filtered_view_g = filtered_view_g[m]
            
        st.caption(f"Showing **{len(filtered_view_g):,}** of **{len(df_curr_g):,}** records in active filter window")
        st.dataframe(filtered_view_g, use_container_width=True, height=450)
        
        st.download_button(
            "📥 Download Filtered Search Console CSV",
            data=filtered_view_g.to_csv(index=False).encode("utf-8"),
            file_name="search_console_filtered.csv",
            mime="text/csv",
            key="dl_gsc"
        )

    # ---------------- Tab 4: Google Ads ----------------
    with tab_a:
        st.markdown("### 💰 Google Ads Performance (`google_ads.csv`)")
        with st.expander("📖 View Schema & Column Data Dictionary", expanded=False):
            st.json(DATA_DICTIONARIES["google_ads"])
            
        df_curr_a = filtered_data["google_ads"]
        srch_a = st.text_input("🔍 Search Google Ads Records (Campaign, Ad Group, Device)", key="srch_ads")
        
        filtered_view_a = df_curr_a.copy()
        if srch_a:
            m = (
                filtered_view_a["campaign"].str.contains(srch_a, case=False, na=False) |
                filtered_view_a["ad_group"].str.contains(srch_a, case=False, na=False)
            )
            filtered_view_a = filtered_view_a[m]
            
        st.caption(f"Showing **{len(filtered_view_a):,}** of **{len(df_curr_a):,}** records in active filter window")
        st.dataframe(filtered_view_a, use_container_width=True, height=450)
        
        st.download_button(
            "📥 Download Filtered Google Ads CSV",
            data=filtered_view_a.to_csv(index=False).encode("utf-8"),
            file_name="google_ads_filtered.csv",
            mime="text/csv",
            key="dl_ads"
        )

    # ---------------- Tab 5: Blended Cross-Channel ----------------
    with tab_b:
        st.markdown("### 🔀 Blended Daily Cross-Channel Dataset")
        st.caption("Reconciled daily records combining GA4, Search Console, and Google Ads metrics.")
        
        blended_daily_df = build_daily_blended_data(filtered_data)
        st.dataframe(blended_daily_df, use_container_width=True, height=450)
        
        st.download_button(
            "📥 Download Blended Cross-Channel CSV",
            data=blended_daily_df.to_csv(index=False).encode("utf-8"),
            file_name="blended_daily_analytics.csv",
            mime="text/csv",
            key="dl_blended"
        )
        
    st.markdown("---")
    # Regenerate Data Utility Button
    col_reg1, col_reg2 = st.columns([1, 3])
    with col_reg1:
        if st.button("🎲 Re-generate Synthetic Data", use_container_width=True):
            with st.spinner("Generating fresh reproducible datasets..."):
                generate_all_datasets()
                st.cache_data.clear()
            st.success("✅ Datasets re-generated and cache refreshed successfully!")
            st.rerun()
    with col_reg2:
        st.caption("Resets and re-generates all 4 synthetic CSV files using random seed while preserving relational consistency.")
