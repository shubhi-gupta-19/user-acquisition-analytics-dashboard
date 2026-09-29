"""
UI components, custom CSS styling, KPI card rendering, and synthetic notice banners.
Ensures a modern, polished executive analytics appearance.
"""

import streamlit as st


def inject_custom_css():
    """Inject modern custom CSS for styling cards, typography, and badges."""
    custom_css = """
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Top synthetic data banner */
    .synthetic-banner {
        background: linear-gradient(90deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
        border: 1px solid #4338ca;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: #e0e7ff;
        font-size: 0.85rem;
    }
    .synthetic-badge {
        background: #f59e0b;
        color: #1e1b4b;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-right: 10px;
        letter-spacing: 0.05em;
    }
    
    /* KPI Metric Cards */
    .kpi-container {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
        border-color: rgba(99, 102, 241, 0.35);
    }
    .kpi-title {
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .kpi-value {
        color: #0f172a;
        font-size: 1.65rem;
        font-weight: 700;
        line-height: 1.2;
    }
    @media (prefers-color-scheme: dark) {
        .kpi-value {
            color: #f8fafc;
        }
    }
    .kpi-subtitle {
        color: #64748b;
        font-size: 0.75rem;
        margin-top: 4px;
    }
    
    /* Section Headers */
    .section-header {
        margin-top: 15px;
        margin-bottom: 10px;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #334155;
    }
    @media (prefers-color-scheme: dark) {
        .section-title {
            color: #e2e8f0;
        }
    }
    
    /* Clean badges */
    .channel-pill {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_synthetic_notice():
    """Render a prominent banner notifying users of sample data and demonstration status."""
    st.markdown(
        """
        <div class="synthetic-banner">
            <div>
                <span class="synthetic-badge">SAMPLE / SYNTHETIC DATA</span>
                <strong>Demonstration & Framework Analysis Environment:</strong> 
                The 4 underlying CSV datasets (GA4 Sessions, Events, Search Console, Google Ads) 
                were synthetically generated across 90 days with relational consistency to showcase cross-channel analysis. 
                <em>This is not real client or Google proprietary data.</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpi(col, title, value_str, subtitle=None):
    """Render a styled KPI card in the given Streamlit column."""
    with col:
        subtitle_html = f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ""
        html = f"""
        <div class="kpi-container">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value_str}</div>
            {subtitle_html}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


def render_real_data_instructions():
    """Renders detailed instructions for replacing synthetic CSVs with real Google exports."""
    with st.expander("📖 Instructions: How to Replace Synthetic Data with Real Google Analytics & Ads Exports"):
        st.markdown(
            """
            This dashboard is fully decoupled from the synthetic data generator. You can plug in your own real exports 
            by replacing the files inside the `data/` directory.

            ### Step-by-Step Replacement Guide

            #### 1. Google Analytics 4 (GA4) Sessions & Events
            * **Export Source**: BigQuery Export for GA4 (Recommended) or GA4 Exploration report export to CSV.
            * **Required File 1**: `data/ga4_sessions.csv`
              * **Required Columns**: `session_id`, `user_id`, `date` (YYYY-MM-DD), `acquisition_source`, `source_medium`, `campaign`, `device_category`, `landing_page`, `is_engaged_session` (0/1), `engagement_time_seconds`, `pageviews`, `has_conversion` (0/1), `revenue` (float).
            * **Required File 2**: `data/ga4_events.csv`
              * **Required Columns**: `event_id`, `session_id`, `user_id`, `date`, `timestamp`, `event_name` (e.g. `page_view`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase`), `event_category`, `page_path`, `item_name`, `event_value`.

            #### 2. Google Search Console (GSC) Performance
            * **Export Source**: Google Search Console -> Performance -> Export -> Download CSV (Select `Queries.csv` and `Pages.csv`).
            * **Required File**: `data/search_console.csv`
              * **Required Columns**: `date` (YYYY-MM-DD), `query`, `landing_page`, `country`, `device_category`, `clicks`, `impressions`, `ctr`, `position`.

            #### 3. Google Ads Campaign Data
            * **Export Source**: Google Ads Reports -> Campaigns / Ad Groups -> Segment by Date & Device -> Download .csv.
            * **Required File**: `data/google_ads.csv`
              * **Required Columns**: `date` (YYYY-MM-DD), `campaign`, `ad_group`, `device_category`, `impressions`, `clicks`, `cost`, `conversions`, `conversion_value`.

            #### 4. Refreshing the Cache
            * Once you copy your CSV files into the `data/` folder with matching headers, click **'Clear Cache'** in the Streamlit hamburger menu or restart the application (`streamlit run app.py`).
            """
        )
