"""
Unit tests for User Acquisition & Behavior Analytics Dashboard.
Tests data generation, loading, defensive filtering, metric calculations, and cross-channel blending.
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from utils.generate_data import generate_all_datasets
from utils.data_loader import load_all_datasets, filter_datasets, DATA_DICTIONARIES
from utils.metrics import (
    safe_divide,
    compute_executive_kpis,
    compute_acquisition_breakdown,
    compute_funnel_metrics,
    compute_events_kpis,
    compute_search_console_kpis,
    compute_google_ads_kpis
)
from utils.blender import (
    build_daily_blended_data,
    build_landing_page_blended_data,
    build_campaign_blended_data
)


@pytest.fixture(scope="session")
def raw_data():
    """Load raw data fixture."""
    return load_all_datasets()


def test_data_generation_counts(raw_data):
    """Verify all datasets satisfy the minimum record count requirements."""
    sessions = raw_data["sessions"]
    events = raw_data["events"]
    gsc = raw_data["search_console"]
    ads = raw_data["google_ads"]
    
    assert len(sessions) >= 1000, f"Expected >= 1000 sessions, got {len(sessions)}"
    assert len(events) >= 2000, f"Expected >= 2000 events, got {len(events)}"
    assert len(gsc) >= 500, f"Expected >= 500 GSC rows, got {len(gsc)}"
    assert len(ads) >= 300, f"Expected >= 300 Ads rows, got {len(ads)}"


def test_data_consistency_and_foreign_keys(raw_data):
    """Verify that event session IDs belong to valid sessions and dates align."""
    sessions = raw_data["sessions"]
    events = raw_data["events"]
    
    session_ids = set(sessions["session_id"].unique())
    event_session_ids = set(events["session_id"].unique())
    
    # All event sessions must exist in sessions table
    assert event_session_ids.issubset(session_ids), "Event contains session IDs not present in GA4 sessions!"
    
    # Check synthetic tag
    assert (sessions["data_flag"] == "SAMPLE / SYNTHETIC DATA").all()
    assert (events["data_flag"] == "SAMPLE / SYNTHETIC DATA").all()
    assert (raw_data["search_console"]["data_flag"] == "SAMPLE / SYNTHETIC DATA").all()
    assert (raw_data["google_ads"]["data_flag"] == "SAMPLE / SYNTHETIC DATA").all()


def test_safe_divide():
    """Test zero-division safeguards."""
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) == 0.0
    assert safe_divide(10, None) == 0.0
    
    # Array test
    nums = np.array([10, 20, 30])
    denoms = np.array([2, 0, 5])
    res = safe_divide(nums, denoms)
    np.testing.assert_array_equal(res, [5.0, 0.0, 6.0])


def test_filtering_logic(raw_data):
    """Test date, source, and cascade filtering."""
    sessions = raw_data["sessions"]
    min_date = sessions["date"].min().date()
    max_date = sessions["date"].max().date()
    
    # Filter by source: Google Organic only
    filtered = filter_datasets(raw_data, min_date, max_date, sources=["Google Organic"])
    
    assert (filtered["sessions"]["acquisition_source"] == "Google Organic").all()
    # Google Ads table should be empty when Google Ads is not in sources
    assert len(filtered["google_ads"]) == 0
    # Search console should retain data
    assert len(filtered["search_console"]) > 0
    
    # Cascading event filter: all remaining events must belong to filtered sessions
    remaining_sessions = set(filtered["sessions"]["session_id"].unique())
    assert set(filtered["events"]["session_id"].unique()).issubset(remaining_sessions)


def test_empty_filter_handling(raw_data):
    """Ensure filtering to empty result does not crash metric computations."""
    # Filter with impossible date range
    future_date = datetime(2099, 1, 1).date()
    empty_filtered = filter_datasets(raw_data, future_date, future_date)
    
    assert len(empty_filtered["sessions"]) == 0
    assert len(empty_filtered["events"]) == 0
    assert len(empty_filtered["search_console"]) == 0
    assert len(empty_filtered["google_ads"]) == 0
    
    # Metric functions must handle empty data gracefully
    kpis = compute_executive_kpis(empty_filtered)
    assert kpis["total_sessions"] == 0
    assert kpis["engagement_rate"] == 0.0
    assert kpis["blended_roas"] == 0.0
    
    funnel = compute_funnel_metrics(empty_filtered)
    assert sum(funnel["counts"]) == 0
    assert funnel["overall_conversion_rate"] == 0.0
    
    gsc_kpis = compute_search_console_kpis(empty_filtered)
    assert gsc_kpis["total_clicks"] == 0
    
    ads_kpis = compute_google_ads_kpis(empty_filtered)
    assert ads_kpis["total_spend"] == 0.0


def test_funnel_calculation_monotonicity(raw_data):
    """Funnel counts should be monotonically decreasing or equal across stages."""
    sessions = raw_data["sessions"]
    min_date = sessions["date"].min().date()
    max_date = sessions["date"].max().date()
    filtered = filter_datasets(raw_data, min_date, max_date)
    
    funnel = compute_funnel_metrics(filtered)
    counts = funnel["counts"]
    
    assert len(counts) == 5
    for i in range(len(counts) - 1):
        assert counts[i] >= counts[i + 1], f"Funnel stage {i} ({counts[i]}) has fewer sessions than stage {i+1} ({counts[i+1]})"


def test_cross_channel_blending(raw_data):
    """Test daily, landing page, and campaign blending."""
    sessions = raw_data["sessions"]
    min_date = sessions["date"].min().date()
    max_date = sessions["date"].max().date()
    filtered = filter_datasets(raw_data, min_date, max_date)
    
    # 1. Daily Blended
    blended_daily = build_daily_blended_data(filtered)
    assert not blended_daily.empty
    assert "ga4_total_sessions" in blended_daily.columns
    assert "gsc_clicks" in blended_daily.columns
    assert "ads_cost" in blended_daily.columns
    assert "blended_roas" in blended_daily.columns
    # Check that date count matches 90 days
    assert len(blended_daily) == 90
    
    # 2. Landing Page Blended
    blended_page = build_landing_page_blended_data(filtered)
    assert not blended_page.empty
    assert "landing_page" in blended_page.columns
    assert "gsc_clicks" in blended_page.columns
    assert "organic_sessions" in blended_page.columns
    
    # 3. Campaign Blended
    blended_camp = build_campaign_blended_data(filtered)
    assert not blended_camp.empty
    assert "campaign" in blended_camp.columns
    assert "ads_cost" in blended_camp.columns
    assert "ga4_sessions" in blended_camp.columns


def test_data_dictionaries_coverage():
    """Verify all 4 datasets have complete data dictionaries defined."""
    assert "ga4_sessions" in DATA_DICTIONARIES
    assert "ga4_events" in DATA_DICTIONARIES
    assert "search_console" in DATA_DICTIONARIES
    assert "google_ads" in DATA_DICTIONARIES
    
    for key, dic in DATA_DICTIONARIES.items():
        assert "title" in dic
        assert "description" in dic
        assert "columns" in dic
        assert len(dic["columns"]) > 0


def test_chart_generation(raw_data):
    """Verify all Plotly chart generation functions execute without property or syntax errors."""
    from utils.charts import (
        create_dual_line_chart,
        create_donut_chart,
        create_horizontal_bar_chart,
        create_funnel_chart,
        create_scatter_plot,
        create_grouped_bar_chart
    )
    
    sessions = raw_data["sessions"]
    daily_sess = sessions.groupby("date").agg(
        sessions=("session_id", "count"),
        conversions=("has_conversion", "sum")
    ).reset_index()
    
    # 1. Dual line chart (the one that previously had titlefont issue)
    fig_dual = create_dual_line_chart(
        daily_sess,
        date_col="date",
        col_left="sessions",
        col_right="conversions",
        title="Daily Sessions & Conversions",
        name_left="Sessions",
        name_right="Conversions"
    )
    assert fig_dual is not None
    assert fig_dual.layout.yaxis.title.text == "Sessions"
    assert fig_dual.layout.yaxis2.title.text == "Conversions"
    
    # 2. Donut chart
    source_counts = sessions["acquisition_source"].value_counts().reset_index()
    source_counts.columns = ["source", "count"]
    fig_donut = create_donut_chart(source_counts, "source", "count", "Channel Share")
    assert fig_donut is not None
    
    # 3. Horizontal bar chart
    fig_bar = create_horizontal_bar_chart(source_counts, "source", "count", "Sources", "Total", is_percent=False)
    assert fig_bar is not None
    
    # 4. Funnel chart
    fig_funnel = create_funnel_chart(["Stage 1", "Stage 2"], [100, 40], [0.0, 0.6])
    assert fig_funnel is not None
    
    # 5. Scatter plot
    fig_scatter = create_scatter_plot(source_counts, "count", "count", "count", "source", "Scatter", "X", "Y")
    assert fig_scatter is not None
    
    # 6. Grouped bar chart
    fig_grouped = create_grouped_bar_chart(daily_sess.head(10), "date", "sessions", "conversions", "Grouped", "Sess", "Conv")
    assert fig_grouped is not None
    
    # Test on empty dataframes (must handle gracefully)
    empty_df = pd.DataFrame()
    fig_empty = create_dual_line_chart(empty_df, "date", "s", "c", "Empty", "S", "C")
    assert fig_empty is not None


def test_advertising_cpc_calculation(raw_data):
    """
    Verify Advertising CPC is calculated as Google Ads Spend / Google Ads Clicks,
    and Cost per GA4 Session is calculated separately as Google Ads Spend / GA4 Sessions.
    """
    acq_df = compute_acquisition_breakdown(raw_data)
    
    # Check Google Ads rows
    ads_rows = acq_df[acq_df["acquisition_source"] == "Google Ads"]
    assert not ads_rows.empty, "Google Ads rows missing in acquisition breakdown"
    
    for _, row in ads_rows.iterrows():
        cost = row["cost"]
        ads_clicks = row["ads_clicks"]
        sessions = row["sessions"]
        
        # Verify CPC is Spend / Clicks (not Spend / Sessions)
        if ads_clicks > 0:
            expected_cpc = cost / ads_clicks
            assert abs(row["ads_cpc"] - expected_cpc) < 1e-4, f"Expected ads_cpc {expected_cpc}, got {row['ads_cpc']}"
            assert abs(row["cpc"] - expected_cpc) < 1e-4
            
        # Verify Cost per GA4 Session
        if sessions > 0:
            expected_cost_per_sess = cost / sessions
            assert abs(row["cost_per_ga4_session"] - expected_cost_per_sess) < 1e-4
            
    # Non-paid channels must have zero ad cost and zero CPC
    non_ads = acq_df[acq_df["acquisition_source"] != "Google Ads"]
    assert (non_ads["cost"] == 0.0).all()
    assert (non_ads["ads_cpc"] == 0.0).all()
    assert (non_ads["cost_per_ga4_session"] == 0.0).all()
    
    # Unit test on custom dummy data with zero clicks
    dummy_filtered = {
        "sessions": pd.DataFrame([{
            "session_id": "S1", "user_id": "U1", "acquisition_source": "Google Ads",
            "source_medium": "google / cpc", "campaign": "zero_click_camp",
            "is_engaged_session": 1, "has_conversion": 0, "revenue": 0.0
        }]),
        "google_ads": pd.DataFrame([{
            "campaign": "zero_click_camp", "cost": 50.0, "clicks": 0, "impressions": 500
        }])
    }
    dummy_acq = compute_acquisition_breakdown(dummy_filtered)
    assert dummy_acq.iloc[0]["ads_cpc"] == 0.0
    assert dummy_acq.iloc[0]["cost_per_ga4_session"] == 50.0


def test_gsc_impression_weighted_position():
    """
    Verify GSC average position uses impression-weighting: sum(position * impressions) / sum(impressions).
    """
    from utils.metrics import calc_impression_weighted_position
    
    # Controlled synthetic sample:
    # Row 1: Position 2.0, Impressions 1000
    # Row 2: Position 10.0, Impressions 100
    # Simple unweighted mean: (2.0 + 10.0) / 2 = 6.0
    # Impression-weighted: (2.0*1000 + 10.0*100) / 1100 = 3000 / 1100 = 2.7272...
    dummy_gsc = pd.DataFrame([
        {"query": "q1", "landing_page": "/p1", "clicks": 50, "impressions": 1000, "position": 2.0},
        {"query": "q2", "landing_page": "/p2", "clicks": 2, "impressions": 100, "position": 10.0}
    ])
    
    weighted_pos = calc_impression_weighted_position(dummy_gsc)
    assert abs(weighted_pos - (3000.0 / 1100.0)) < 1e-4
    assert weighted_pos < 3.0, "Unweighted mean was incorrectly computed!"
    
    # Test compute_search_console_kpis on dummy
    kpis = compute_search_console_kpis({"search_console": dummy_gsc})
    assert abs(kpis["avg_position"] - (3000.0 / 1100.0)) < 1e-4
    assert kpis["total_clicks"] == 52
    assert kpis["total_impressions"] == 1100
    assert abs(kpis["avg_ctr"] - (52.0 / 1100.0)) < 1e-4
    
    # Zero impressions edge case
    zero_imp_df = pd.DataFrame([{"position": 5.0, "impressions": 0, "clicks": 0}])
    assert calc_impression_weighted_position(zero_imp_df) == 0.0


def test_chronological_funnel_progression():
    """
    Verify the funnel strictly enforces chronological order:
    session -> view_item -> add_to_cart -> begin_checkout -> purchase.
    Out-of-order, skipped, repeated, equal-timestamp, and eventless sessions must be handled correctly.
    """
    dummy_sessions = pd.DataFrame([
        {"session_id": f"SESS_{i}"} for i in range(1, 7)
    ])
    
    dummy_events = pd.DataFrame([
        # SESS_1: Perfect chronological order
        {"session_id": "SESS_1", "event_name": "view_item", "timestamp": "2024-07-01 10:00:00"},
        {"session_id": "SESS_1", "event_name": "add_to_cart", "timestamp": "2024-07-01 10:05:00"},
        {"session_id": "SESS_1", "event_name": "begin_checkout", "timestamp": "2024-07-01 10:10:00"},
        {"session_id": "SESS_1", "event_name": "purchase", "timestamp": "2024-07-01 10:15:00"},
        
        # SESS_2: Out-of-order purchase before checkout (must NOT count as purchase)
        {"session_id": "SESS_2", "event_name": "view_item", "timestamp": "2024-07-01 10:00:00"},
        {"session_id": "SESS_2", "event_name": "add_to_cart", "timestamp": "2024-07-01 10:05:00"},
        {"session_id": "SESS_2", "event_name": "purchase", "timestamp": "2024-07-01 10:07:00"},
        {"session_id": "SESS_2", "event_name": "begin_checkout", "timestamp": "2024-07-01 10:10:00"},
        
        # SESS_3: Missing intermediate stage (view_item -> purchase, skipped cart and checkout)
        {"session_id": "SESS_3", "event_name": "view_item", "timestamp": "2024-07-01 10:00:00"},
        {"session_id": "SESS_3", "event_name": "purchase", "timestamp": "2024-07-01 10:10:00"},
        
        # SESS_4: Repeated events with valid sequential progression
        {"session_id": "SESS_4", "event_name": "view_item", "timestamp": "2024-07-01 10:00:00"},
        {"session_id": "SESS_4", "event_name": "view_item", "timestamp": "2024-07-01 10:02:00"},
        {"session_id": "SESS_4", "event_name": "add_to_cart", "timestamp": "2024-07-01 10:05:00"},
        {"session_id": "SESS_4", "event_name": "add_to_cart", "timestamp": "2024-07-01 10:06:00"},
        {"session_id": "SESS_4", "event_name": "begin_checkout", "timestamp": "2024-07-01 10:10:00"},
        {"session_id": "SESS_4", "event_name": "purchase", "timestamp": "2024-07-01 10:15:00"},
        
        # SESS_5: Equal timestamps (batch events in same second)
        {"session_id": "SESS_5", "event_name": "view_item", "timestamp": "2024-07-01 10:00:00"},
        {"session_id": "SESS_5", "event_name": "add_to_cart", "timestamp": "2024-07-01 10:00:00"},
        {"session_id": "SESS_5", "event_name": "begin_checkout", "timestamp": "2024-07-01 10:00:00"},
        {"session_id": "SESS_5", "event_name": "purchase", "timestamp": "2024-07-01 10:00:00"},
        
        # SESS_6: No events (stays at Stage 1)
    ])
    
    res = compute_funnel_metrics({"sessions": dummy_sessions, "events": dummy_events})
    counts = res["counts"]
    
    # Expected qualification:
    # Stage 1 (Session): S1, S2, S3, S4, S5, S6 = 6 sessions
    # Stage 2 (view_item): S1, S2, S3, S4, S5 = 5 sessions
    # Stage 3 (add_to_cart): S1, S2, S4, S5 = 4 sessions (S3 skipped cart)
    # Stage 4 (begin_checkout): S1, S2, S4, S5 = 4 sessions (S2 reached checkout at 10:10 after cart at 10:05)
    # Stage 5 (purchase): S1, S4, S5 = 3 sessions (S2 had purchase at 10:07 BEFORE checkout at 10:10, so S2 does NOT qualify for purchase!)
    
    assert counts[0] == 6, f"Expected 6 entry sessions, got {counts[0]}"
    assert counts[1] == 5, f"Expected 5 view_item sessions, got {counts[1]}"
    assert counts[2] == 4, f"Expected 4 add_to_cart sessions, got {counts[2]}"
    assert counts[3] == 4, f"Expected 4 checkout sessions, got {counts[3]}"
    assert counts[4] == 3, f"Expected 3 purchase sessions, got {counts[4]}"
    
    # Ensure SESS_2 was NOT counted as purchase
    assert "SESS_2" not in res["stage_sessions"][5], "SESS_2 purchase occurred before checkout and should not qualify!"
    # Ensure SESS_3 was NOT counted as purchase
    assert "SESS_3" not in res["stage_sessions"][5], "SESS_3 skipped cart and checkout and should not qualify!"
    
    # Denominator consistency across stages
    assert res["funnel_df"].iloc[0]["% of Total Sessions"] == 100.0
    assert res["funnel_df"].iloc[-1]["% of Total Sessions"] == 50.0  # 3/6 = 50%
    assert abs(res["overall_conversion_rate"] - 0.50) < 1e-4
    
    # Explicit dual conversion rate validation
    f_df = res["funnel_df"]
    # Stage 1: 6 / 6 = 100% Entry, 100% Step, 0% drop
    assert f_df.iloc[0]["Entry-Session Conversion Rate (%)"] == 100.0
    assert f_df.iloc[0]["Step Conversion Rate (%)"] == 100.0
    assert f_df.iloc[0]["Drop-off Rate (%)"] == 0.0
    
    # Stage 2: 5 / 6 = 83.33% Entry, 5 / 6 = 83.33% Step, 16.67% drop
    assert f_df.iloc[1]["Entry-Session Conversion Rate (%)"] == 83.33
    assert f_df.iloc[1]["Step Conversion Rate (%)"] == 83.33
    assert f_df.iloc[1]["Drop-off Rate (%)"] == 16.67
    
    # Stage 3: 4 / 6 = 66.67% Entry, 4 / 5 = 80.0% Step, 20.0% drop
    assert f_df.iloc[2]["Entry-Session Conversion Rate (%)"] == 66.67
    assert f_df.iloc[2]["Step Conversion Rate (%)"] == 80.0
    assert f_df.iloc[2]["Drop-off Rate (%)"] == 20.0
    
    # Stage 4: 4 / 6 = 66.67% Entry, 4 / 4 = 100.0% Step, 0.0% drop
    assert f_df.iloc[3]["Entry-Session Conversion Rate (%)"] == 66.67
    assert f_df.iloc[3]["Step Conversion Rate (%)"] == 100.0
    assert f_df.iloc[3]["Drop-off Rate (%)"] == 0.0
    
    # Stage 5: 3 / 6 = 50.0% Entry, 3 / 4 = 75.0% Step, 25.0% drop
    assert f_df.iloc[4]["Entry-Session Conversion Rate (%)"] == 50.0
    assert f_df.iloc[4]["Step Conversion Rate (%)"] == 75.0
    assert f_df.iloc[4]["Drop-off Rate (%)"] == 25.0


def test_funnel_conversion_percentages_and_edge_cases():
    """
    Test dual conversion rates on edge cases:
    1. Completely empty dataset (0 sessions, 0 events)
    2. Sessions with zero events (zero denominators for subsequent steps)
    3. Partial dropout with zero downstream conversions
    """
    # 1. Completely empty dataset
    empty_res = compute_funnel_metrics({"sessions": pd.DataFrame(), "events": pd.DataFrame()})
    assert empty_res["counts"] == [0, 0, 0, 0, 0]
    assert empty_res["step_conversion_rates"] == [0.0, 0.0, 0.0, 0.0, 0.0]
    assert empty_res["entry_conversion_rates"] == [0.0, 0.0, 0.0, 0.0, 0.0]
    assert empty_res["drop_offs"] == [0.0, 0.0, 0.0, 0.0, 0.0]
    assert empty_res["overall_conversion_rate"] == 0.0
    
    empty_df = empty_res["funnel_df"]
    assert (empty_df["Entry-Session Conversion Rate (%)"] == 0.0).all()
    assert (empty_df["Step Conversion Rate (%)"] == 0.0).all()
    assert (empty_df["Drop-off Rate (%)"] == 0.0).all()
    assert not empty_df.isna().any().any()
    
    # 2. 20 sessions but 0 events (all stages 2-5 have count = 0)
    sess_only = pd.DataFrame([{"session_id": f"S_{i}"} for i in range(20)])
    zero_evt_res = compute_funnel_metrics({"sessions": sess_only, "events": pd.DataFrame()})
    assert zero_evt_res["counts"] == [20, 0, 0, 0, 0]
    
    z_df = zero_evt_res["funnel_df"]
    # Stage 1: 20 sessions, 100% Entry, 100% Step
    assert z_df.iloc[0]["Sessions"] == 20
    assert z_df.iloc[0]["Entry-Session Conversion Rate (%)"] == 100.0
    assert z_df.iloc[0]["Step Conversion Rate (%)"] == 100.0
    assert z_df.iloc[0]["Drop-off Rate (%)"] == 0.0
    
    # Stage 2: 0 sessions, 0% Entry, 0% Step, 100% Drop-off
    assert z_df.iloc[1]["Sessions"] == 0
    assert z_df.iloc[1]["Entry-Session Conversion Rate (%)"] == 0.0
    assert z_df.iloc[1]["Step Conversion Rate (%)"] == 0.0
    assert z_df.iloc[1]["Drop-off Rate (%)"] == 100.0
    
    # Stages 3-5: 0 sessions, zero denominator (0/0) must yield 0.0 without errors or NaNs
    for stage_idx in [2, 3, 4]:
        assert z_df.iloc[stage_idx]["Sessions"] == 0
        assert z_df.iloc[stage_idx]["Entry-Session Conversion Rate (%)"] == 0.0
        assert z_df.iloc[stage_idx]["Step Conversion Rate (%)"] == 0.0
        assert z_df.iloc[stage_idx]["Drop-off Rate (%)"] == 0.0
        
    assert not z_df.isna().any().any()
    
    # 3. Partial dropout: 10 sessions, 5 view_item, 0 subsequent events
    part_sess = pd.DataFrame([{"session_id": f"P_{i}"} for i in range(10)])
    part_events = pd.DataFrame([
        {"session_id": f"P_{i}", "event_name": "view_item", "timestamp": "2024-07-01 12:00:00"}
        for i in range(5)
    ])
    part_res = compute_funnel_metrics({"sessions": part_sess, "events": part_events})
    assert part_res["counts"] == [10, 5, 0, 0, 0]
    
    p_df = part_res["funnel_df"]
    # Stage 1: 10 / 10 = 100% Entry, 100% Step
    assert p_df.iloc[0]["Entry-Session Conversion Rate (%)"] == 100.0
    assert p_df.iloc[0]["Step Conversion Rate (%)"] == 100.0
    assert p_df.iloc[0]["Drop-off Rate (%)"] == 0.0
    
    # Stage 2: 5 / 10 = 50% Entry, 5 / 10 = 50% Step, 50% Drop-off
    assert p_df.iloc[1]["Entry-Session Conversion Rate (%)"] == 50.0
    assert p_df.iloc[1]["Step Conversion Rate (%)"] == 50.0
    assert p_df.iloc[1]["Drop-off Rate (%)"] == 50.0
    
    # Stage 3: 0 / 10 = 0% Entry, 0 / 5 = 0% Step, 100% Drop-off
    assert p_df.iloc[2]["Entry-Session Conversion Rate (%)"] == 0.0
    assert p_df.iloc[2]["Step Conversion Rate (%)"] == 0.0
    assert p_df.iloc[2]["Drop-off Rate (%)"] == 100.0
    
    # Stage 4 & 5: 0/0 division safely returns 0.0
    assert p_df.iloc[3]["Step Conversion Rate (%)"] == 0.0
    assert p_df.iloc[4]["Step Conversion Rate (%)"] == 0.0


def test_roas_and_attribution_separation():
    """
    Verify strict separation and calculation of:
    1. Blended ROAS (All-channel GA4 revenue / Ad spend)
    2. GA4 Paid-Channel Revenue / Ad Spend (GA4 Google Ads attributed revenue / Ad spend)
    3. Google Ads Reported ROAS (Ads self-reported conversion value / Ad spend)
    Ensures non-paid revenue is NEVER added to Google Ads ROAS.
    """
    dummy_data = {
        "sessions": pd.DataFrame([
            {"session_id": "S1", "user_id": "U1", "acquisition_source": "Google Organic", "revenue": 6000.0, "is_engaged_session": 1, "has_conversion": 1},
            {"session_id": "S2", "user_id": "U2", "acquisition_source": "Direct", "revenue": 4000.0, "is_engaged_session": 1, "has_conversion": 1},
            {"session_id": "S3", "user_id": "U3", "acquisition_source": "Google Ads", "revenue": 3000.0, "is_engaged_session": 1, "has_conversion": 1},
        ]),
        "google_ads": pd.DataFrame([
            {"campaign": "c1", "cost": 1500.0, "clicks": 500, "impressions": 10000, "conversions": 15, "conversion_value": 4500.0}
        ])
    }
    
    kpis = compute_executive_kpis(dummy_data)
    
    total_rev = 13000.0  # 6000 + 4000 + 3000
    ad_spend = 1500.0
    ga4_paid_rev = 3000.0
    ads_reported_val = 4500.0
    
    expected_blended = total_rev / ad_spend           # 13000 / 1500 = 8.666...
    expected_ga4_paid = ga4_paid_rev / ad_spend       # 3000 / 1500 = 2.0
    expected_ads_reported = ads_reported_val / ad_spend # 4500 / 1500 = 3.0
    
    assert abs(kpis["blended_roas"] - expected_blended) < 1e-4
    assert abs(kpis["ga4_paid_roas"] - expected_ga4_paid) < 1e-4
    assert abs(kpis["ads_reported_roas"] - expected_ads_reported) < 1e-4
    
    # Crucial distinction: Blended ROAS != GA4 Paid ROAS != Ads Reported ROAS
    assert kpis["blended_roas"] != kpis["ga4_paid_roas"]
    assert kpis["ga4_paid_roas"] != kpis["ads_reported_roas"]
    
    # Zero spend edge case
    zero_spend_data = {
        "sessions": dummy_data["sessions"],
        "google_ads": pd.DataFrame([{"campaign": "c1", "cost": 0.0, "clicks": 0, "impressions": 0, "conversions": 0, "conversion_value": 0.0}])
    }
    zero_kpis = compute_executive_kpis(zero_spend_data)
    assert zero_kpis["blended_roas"] == 0.0
    assert zero_kpis["ga4_paid_roas"] == 0.0
    assert zero_kpis["ads_reported_roas"] == 0.0

