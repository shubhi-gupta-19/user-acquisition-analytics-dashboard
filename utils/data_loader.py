"""
Data loading, schema validation, and defensive filtering module.
Provides cached loading and comprehensive data dictionaries.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

DATA_DICTIONARIES = {
    "ga4_sessions": {
        "title": "Google Analytics 4 (GA4) Sessions",
        "description": "Session-level interaction data capturing acquisition source, landing page, device, user ID, engagement, and conversion metrics over 90 days.",
        "grain": "1 row per Session ID",
        "columns": {
            "session_id": "Unique session identifier (e.g., SESS_20001). Join key to ga4_events.",
            "user_id": "Unique pseudonymous user identifier (e.g., USR_1042). Allows tracking of returning users.",
            "date": "Calendar date of session start (YYYY-MM-DD).",
            "acquisition_source": "Normalized acquisition channel group (Google Organic, Google Ads, Direct, Social, Referral, Email).",
            "source_medium": "Raw UTM source and medium (e.g., google / organic, google / cpc, direct / (none)).",
            "campaign": "Marketing campaign name (e.g., brand_search, summer_sale_2024, or (not set)).",
            "device_category": "Client device class (desktop, mobile, tablet).",
            "landing_page": "First URL path viewed in the session (e.g., /, /pricing, /demo).",
            "is_engaged_session": "Binary flag (1 = session lasted >= 10s or had >= 2 pageviews or 1 conversion; 0 otherwise).",
            "engagement_time_seconds": "Total active user time recorded during the session.",
            "pageviews": "Count of page views during this session.",
            "has_conversion": "Binary flag (1 if purchase occurred during session; 0 otherwise).",
            "revenue": "Attributed transaction revenue in USD ($).",
            "data_flag": "Explicit tag indicating synthetic sample nature."
        }
    },
    "ga4_events": {
        "title": "Google Analytics 4 (GA4) Events",
        "description": "Granular user interaction events within sessions, capturing the e-commerce funnel (page_view -> view_item -> add_to_cart -> begin_checkout -> purchase).",
        "grain": "1 row per Event instance",
        "columns": {
            "event_id": "Unique event identifier (e.g., EVT_0000001).",
            "session_id": "Session identifier linking event to ga4_sessions.",
            "user_id": "User identifier linking event to ga4_sessions.",
            "date": "Event date (YYYY-MM-DD).",
            "timestamp": "Precise event timestamp (YYYY-MM-DD HH:MM:SS).",
            "event_name": "Standard GA4 event name (page_view, user_engagement, view_item, add_to_cart, begin_checkout, purchase).",
            "event_category": "Grouping category (navigation, engagement, ecommerce).",
            "page_path": "Page path where event occurred.",
            "item_name": "Product tier or plan interacted with (e.g., Starter Pack, Pro Tier, Enterprise Tier).",
            "event_value": "Monetary value associated with event (revenue for purchases).",
            "data_flag": "Explicit tag indicating synthetic sample nature."
        }
    },
    "search_console": {
        "title": "Google Search Console (GSC) Performance",
        "description": "Organic search visibility metrics aggregated by query, landing page, country, and device.",
        "grain": "Date x Query x Landing Page x Country x Device",
        "columns": {
            "date": "Date of search impression/click (YYYY-MM-DD).",
            "query": "Organic search query typed by searcher on Google.",
            "landing_page": "Destination landing page URL path.",
            "country": "Country where search originated.",
            "device_category": "Searcher device (desktop, mobile, tablet).",
            "clicks": "Number of organic clicks that sent searchers to the website.",
            "impressions": "Number of times a website URL appeared in organic search results.",
            "ctr": "Click-Through Rate (clicks / impressions).",
            "position": "Average rank position in Google organic search results (1.0 = top rank).",
            "data_flag": "Explicit tag indicating synthetic sample nature."
        }
    },
    "google_ads": {
        "title": "Google Ads Performance",
        "description": "Paid advertising performance metrics aggregated by campaign, ad group, date, and device.",
        "grain": "Date x Campaign x Ad Group x Device",
        "columns": {
            "date": "Advertising date (YYYY-MM-DD).",
            "campaign": "Ad campaign name matching UTM campaign in GA4.",
            "ad_group": "Targeting ad group or keyword cluster.",
            "device_category": "Target device (desktop, mobile, tablet).",
            "impressions": "Count of paid ad impressions served.",
            "clicks": "Count of user clicks on paid ads.",
            "cost": "Total advertising spend in USD ($).",
            "conversions": "Google Ads attributed conversions.",
            "conversion_value": "Total conversion monetary value in USD ($).",
            "ctr": "Ad Click-Through Rate (clicks / impressions).",
            "avg_cpc": "Average Cost Per Click (cost / clicks) in USD ($).",
            "cpa": "Cost Per Acquisition / Conversion (cost / conversions) in USD ($).",
            "roas": "Return on Ad Spend (conversion_value / cost).",
            "data_flag": "Explicit tag indicating synthetic sample nature."
        }
    }
}


def ensure_datasets_exist():
    """Ensure data files exist; if not, invoke generator automatically."""
    required = ["ga4_sessions.csv", "ga4_events.csv", "search_console.csv", "google_ads.csv"]
    all_exist = all(os.path.exists(os.path.join(DATA_DIR, f)) for f in required)
    if not all_exist:
        from utils.generate_data import generate_all_datasets
        generate_all_datasets(DATA_DIR)


@st.cache_data(show_spinner=False)
def load_all_datasets():
    """
    Load all 4 CSV datasets with caching, parsing dates and handling missing values safely.
    Returns a dictionary of raw DataFrames.
    """
    ensure_datasets_exist()
    
    # 1. Load GA4 Sessions
    path_sessions = os.path.join(DATA_DIR, "ga4_sessions.csv")
    df_sessions = pd.read_csv(path_sessions)
    df_sessions["date"] = pd.to_datetime(df_sessions["date"])
    df_sessions["session_id"] = df_sessions["session_id"].astype(str)
    df_sessions["user_id"] = df_sessions["user_id"].astype(str)
    df_sessions["revenue"] = df_sessions["revenue"].fillna(0.0).astype(float)
    df_sessions["is_engaged_session"] = df_sessions["is_engaged_session"].fillna(0).astype(int)
    df_sessions["has_conversion"] = df_sessions["has_conversion"].fillna(0).astype(int)
    
    # 2. Load GA4 Events
    path_events = os.path.join(DATA_DIR, "ga4_events.csv")
    df_events = pd.read_csv(path_events)
    df_events["date"] = pd.to_datetime(df_events["date"])
    df_events["timestamp"] = pd.to_datetime(df_events["timestamp"])
    df_events["session_id"] = df_events["session_id"].astype(str)
    df_events["user_id"] = df_events["user_id"].astype(str)
    df_events["event_value"] = df_events["event_value"].fillna(0.0).astype(float)
    
    # 3. Load Search Console
    path_gsc = os.path.join(DATA_DIR, "search_console.csv")
    df_gsc = pd.read_csv(path_gsc)
    df_gsc["date"] = pd.to_datetime(df_gsc["date"])
    df_gsc["clicks"] = df_gsc["clicks"].fillna(0).astype(int)
    df_gsc["impressions"] = df_gsc["impressions"].fillna(0).astype(int)
    df_gsc["position"] = df_gsc["position"].fillna(0.0).astype(float)
    df_gsc["ctr"] = np.where(df_gsc["impressions"] > 0, df_gsc["clicks"] / df_gsc["impressions"], 0.0)
    
    # 4. Load Google Ads
    path_ads = os.path.join(DATA_DIR, "google_ads.csv")
    df_ads = pd.read_csv(path_ads)
    df_ads["date"] = pd.to_datetime(df_ads["date"])
    df_ads["clicks"] = df_ads["clicks"].fillna(0).astype(int)
    df_ads["impressions"] = df_ads["impressions"].fillna(0).astype(int)
    df_ads["cost"] = df_ads["cost"].fillna(0.0).astype(float)
    df_ads["conversions"] = df_ads["conversions"].fillna(0).astype(int)
    df_ads["conversion_value"] = df_ads["conversion_value"].fillna(0.0).astype(float)
    df_ads["ctr"] = np.where(df_ads["impressions"] > 0, df_ads["clicks"] / df_ads["impressions"], 0.0)
    df_ads["avg_cpc"] = np.where(df_ads["clicks"] > 0, df_ads["cost"] / df_ads["clicks"], 0.0)
    df_ads["cpa"] = np.where(df_ads["conversions"] > 0, df_ads["cost"] / df_ads["conversions"], 0.0)
    df_ads["roas"] = np.where(df_ads["cost"] > 0, df_ads["conversion_value"] / df_ads["cost"], 0.0)
    
    return {
        "sessions": df_sessions,
        "events": df_events,
        "search_console": df_gsc,
        "google_ads": df_ads
    }


def filter_datasets(raw_data, start_date, end_date, sources=None, campaigns=None, devices=None):
    """
    Apply global filter state across all datasets defensively without mutating cached originals.
    Handles date range, acquisition sources, campaigns, and devices.
    """
    ts_start = pd.to_datetime(start_date)
    ts_end = pd.to_datetime(end_date)
    
    # Copy dataframes to avoid mutation
    sessions = raw_data["sessions"].copy()
    events = raw_data["events"].copy()
    gsc = raw_data["search_console"].copy()
    ads = raw_data["google_ads"].copy()
    
    # 1. Date Range Filtering
    sessions = sessions[(sessions["date"] >= ts_start) & (sessions["date"] <= ts_end)]
    gsc = gsc[(gsc["date"] >= ts_start) & (gsc["date"] <= ts_end)]
    ads = ads[(ads["date"] >= ts_start) & (ads["date"] <= ts_end)]
    
    # 2. Acquisition Source Filtering (Primary dimension on GA4)
    if sources is not None and len(sources) > 0:
        sessions = sessions[sessions["acquisition_source"].isin(sources)]
        
        # If Google Ads is excluded from sources, filter Ads table
        if "Google Ads" not in sources:
            ads = ads.iloc[0:0].copy()
            
        # If Google Organic is excluded from sources, filter Search Console table
        if "Google Organic" not in sources:
            gsc = gsc.iloc[0:0].copy()
            
    # 3. Campaign Filtering
    if campaigns is not None and len(campaigns) > 0:
        sessions = sessions[sessions["campaign"].isin(campaigns)]
        ads = ads[ads["campaign"].isin(campaigns)]
        
    # 4. Device Filtering
    if devices is not None and len(devices) > 0:
        sessions = sessions[sessions["device_category"].isin(devices)]
        gsc = gsc[gsc["device_category"].isin(devices)]
        ads = ads[ads["device_category"].isin(devices)]
        
    # 5. Cascading Filter on Events based on remaining valid session_ids
    valid_sessions = set(sessions["session_id"].unique())
    events = events[events["session_id"].isin(valid_sessions)]
    
    return {
        "sessions": sessions,
        "events": events,
        "search_console": gsc,
        "google_ads": ads
    }


def get_available_filter_options(raw_data):
    """Extract distinct values for dropdowns and date limits."""
    df_sess = raw_data["sessions"]
    min_date = df_sess["date"].min().date()
    max_date = df_sess["date"].max().date()
    
    all_sources = sorted(list(df_sess["acquisition_source"].dropna().unique()))
    all_campaigns = sorted(list(df_sess["campaign"].dropna().unique()))
    all_devices = sorted(list(df_sess["device_category"].dropna().unique()))
    
    return {
        "min_date": min_date,
        "max_date": max_date,
        "sources": all_sources,
        "campaigns": all_campaigns,
        "devices": all_devices
    }
