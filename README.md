# User Acquisition & Behavior Analytics Dashboard

A production-grade, interactive Python business intelligence and digital marketing analytics dashboard built with **Streamlit**, **Pandas**, **Plotly**, and **NumPy**.

> ⚠️ **NOTICE — SAMPLE / SYNTHETIC DATASET**:  
> All records contained within this project (GA4 Sessions, GA4 Events, Google Search Console, and Google Ads) are **100% synthetically generated** for demonstration, cross-channel data modeling, and business framework analysis over a reproducible 90-day window. This project does not contain, claim, or require real client or Google proprietary data.

---

## 📌 Executive Summary & Key Capabilities

The **User Acquisition & Behavior Analytics Dashboard** reconciles multi-channel user acquisition funnels, digital advertising spend, search console visibility, and on-site e-commerce conversion pathways into a single cohesive interface:

1. **Global Multi-Dimensional Filters**:
   - **Date Range Picker** with quick preset filters (`Last 30D`, `Last 60D`, `Full 90D`).
   - **Acquisition Channel Multi-select** (`Google Organic`, `Google Ads`, `Direct`, `Social`, `Referral`, `Email`).
   - **Campaign Filter** (dynamically aligned across paid and organic).
   - **Device Category Filter** (`desktop`, `mobile`, `tablet`).
   - **One-click "Reset All Filters"** restoring default full selection.
   - Robust defensive filtering: zero-division safeguards, non-mutating caches, and graceful warning banners for empty states.
2. **Interactive Dataset Explorer (Supervisor Requirement)**:
   - Live inspection of raw CSV rows for all 4 underlying datasets plus the blended cross-channel table.
   - Column-level data dictionaries, row count monitors, real-time table keyword search, and CSV download buttons for filtered views.
3. **Cross-Channel Data Blending**:
   - Defensible relational alignment across Google Search Console, Google Ads, and GA4 using shared dimensions (`Date`, `Landing Page`, `Campaign`).
   - Deep architectural documentation detailing attribution discrepancies (e.g., GSC clicks vs. GA4 sessions; Google Ads last-click vs. GA4 cross-channel data-driven attribution).
4. **Offline & Self-Contained**:
   - No Google API credentials, tokens, or paid third-party connectors required. Runs immediately offline out of the box.

---

## 🏗️ Repository Architecture

```text
Business Analysis Dashboard/
├── .gitignore                      # Git ignore file for Python, venv, and Streamlit caches
├── requirements.txt                # Production Python dependencies
├── README.md                       # Comprehensive setup guide, schemas, and methodology
├── app.py                          # Main Streamlit web application & page routers
├── data/                           # 4 Realistic reproducible synthetic CSV datasets
│   ├── ga4_sessions.csv            # >= 1,000 records (1,650 rows over 90 days)
│   ├── ga4_events.csv              # >= 2,000 records (4,073 rows, chronological funnels)
│   ├── search_console.csv          # >= 500 records (772 rows, query/page rankings)
│   └── google_ads.csv              # >= 300 records (526 rows, campaign-date spend & ROAS)
├── utils/                          # Modular business logic and analytics engines
│   ├── __init__.py
│   ├── generate_data.py            # Reproducible synthetic data generation script
│   ├── data_loader.py              # Streamlit cached loader, schemas & data dictionaries
│   ├── metrics.py                  # KPI calculations, conversion rates, ROAS, zero-division guards
│   ├── blender.py                  # Cross-channel blending, join keys & attribution documentation
│   ├── charts.py                   # Plotly charts with curated visual themes and custom tooltips
│   └── ui.py                       # Glassmorphic CSS styling, custom KPI cards & notice banners
└── tests/                          # Automated unit test suite
    ├── __init__.py
    └── test_dashboard.py           # Pytest tests for data generation, filters, metrics, and joins
```

---

## 🚀 Quickstart Guide (Windows PowerShell)

Run the following commands in **Windows PowerShell** to set up the environment and launch the dashboard:

```powershell
# 1. Create a Python virtual environment (.venv)
python -m venv .venv

# 2. Activate the virtual environment
.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install required dependencies
pip install -r requirements.txt

# 4. (Optional) Run the automated unit test suite
python -m pytest tests/test_dashboard.py -v

# 5. Launch the Streamlit dashboard
streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`.

---

## 📊 Dashboard Pages & Functional Modules

| Page / Section | Key Metrics & Visualizations | Purpose |
| :--- | :--- | :--- |
| **📊 Executive Overview** | Sessions, Users, Engaged Sessions, Engagement Rate, Conversions, Conversion Rate, Total Revenue, Total Ad Spend, Blended ROAS. Dual-axis line trend, Channel contribution donut, Device mix, Conversion rate by source. | C-suite high-level performance snapshot and commercial growth trajectories. |
| **🚀 Acquisition Analysis** | Channel performance table with Users, Sessions, Engagement, Conversions, Revenue, Ad Cost, CPC, ROAS. Revenue vs. Cost comparison and Engagement vs. Conversion Rate scatter plot. | Evaluates acquisition channels and identifies high-ROI campaigns. |
| **🔄 User Journey & Funnel** | 5-Stage Funnel: `Landing Page` → `View Item (Plan)` → `Add to Cart` → `Begin Checkout` → `Purchase`. Stage counts, drop-off percentages, Plotly Funnel visualization, and Device-level funnel breakdown. | Diagnoses user drop-off bottlenecks and friction points across the checkout flow. |
| **⚡ Events & Engagement** | Total Events, Unique Event Users, Avg Events/Session, Avg Engagement Time. Top event frequency, Category distribution (Ecommerce, Engagement, Navigation), and searchable Event Stream table. | Evaluates granular user interactions and on-site feature engagement. |
| **🔍 Search Console** | Organic Clicks, Impressions, Average CTR, Average Position. Daily impressions & clicks trend, Top Queries table, Top Landing Pages table, and CTR vs. Average Rank position decay curve. | Measures organic search visibility, SEO keyword rankings, and landing page reach. |
| **💰 Google Ads** | Ad Spend, Impressions, Clicks, Conversions, Avg CPC, CPA, ROAS. Campaign-level performance table, Daily Spend vs. Conversion Value trend, and ROAS vs. Cost analysis. | Tracks paid search efficiency, keyword acquisition costs, and ad campaign returns. |
| **🔀 Cross-Channel Analysis** | Reconciliation of GSC clicks vs. GA4 organic sessions, Google Ads clicks vs. GA4 paid sessions, Combined Daily Blended Table, Landing Page Cross-Analysis, and Campaign Attribution Reconciliation. | Eliminates siloed reporting and reconciles data across platforms. |
| **🗄️ Dataset Explorer** | Full interactive dataframes for `ga4_sessions`, `ga4_events`, `search_console`, `google_ads`, and `blended_daily`. Search bar, row counter, schema data dictionary accordion, CSV download button, and Re-generate Data utility. | Supervisor verification portal to inspect raw records and validate metrics. |

---

## 📐 Analytical Methodology & Corrected Formulations

This dashboard implements defensible, mathematically rigorous marketing analytics standards across all platforms:

### 1. Advertising CPC vs. Cost per GA4 Session
* **Advertising CPC**:
  $$\text{Ads CPC} = \frac{\text{Google Ads Spend}}{\text{Google Ads Clicks}}$$
  Calculated exclusively using Google Ads aggregate campaign and date data. Handles zero-click edge cases safely (returning `$0.00`) and non-paid acquisition channels without error.
* **Cost per GA4 Session**:
  $$\text{Cost per GA4 Session} = \frac{\text{Google Ads Spend}}{\text{GA4 Sessions (Google Ads)}}$$
  Maintained as a separate efficiency metric. Explains click-to-session drop-offs caused by ad blockers, cookie consent rejections, tracking latency, or redirects.
* **Join Safeguards**: Spend and clicks are aggregated to campaign level before joining to GA4 sessions to prevent Cartesian product inflation.

### 2. Google Search Console Impression-Weighted Position & Accurate CTR
* **Impression-Weighted Average Position**:
  $$\text{Weighted Position} = \frac{\sum (\text{Position} \times \text{Impressions})}{\sum \text{Impressions}}$$
  Applied consistently across overall KPIs, query-level performance, landing-page-level aggregations, and daily trend lines. Arithmetic means skew organic performance by giving equal weight to queries with 1 impression and queries with 10,000 impressions.
* **CTR Calculation**:
  $$\text{CTR} = \frac{\sum \text{Clicks}}{\sum \text{Impressions}}$$
  Calculated directly from aggregated volume rather than an unweighted average of individual row CTR percentages.
* **Zero Handling**: Safe division safeguards return `0.0` if total impressions are zero. Raw records in Dataset Explorer remain completely untouched.

### 3. Chronological Sequential E-Commerce Funnel
* **Stage Progression**:
  `1. Session / Landing Page` $\rightarrow$ `2. View Item (Plan)` $\rightarrow$ `3. Add To Cart` $\rightarrow$ `4. Begin Checkout` $\rightarrow$ `5. Purchase`
* **Strict Chronological Qualification**:
  Events within each session are sorted chronologically by `timestamp`. A session qualifies for Stage $i$ if and only if it previously qualified for Stage $i-1$ and an event for Stage $i$ occurred at or after the timestamp of Stage $i-1$.
  - An event occurring out-of-order (e.g. `purchase` occurring before `begin_checkout`) does **not** qualify for the subsequent stage.
  - Skipped stages break the progression chain.
  - Sessions with repeated events within a stage use the earliest qualifying event to allow subsequent downstream stages to qualify.
  - Equal timestamps between stages are resolved in logical lifecycle sequence.
* **Dual Conversion Rate Formulations & Explicit Denominators**:
  - **Entry-Session Conversion Rate (%)**:
    $$\text{Entry-Session Conversion Rate} = \frac{\text{Current Stage Sessions}}{\text{Total Entry Sessions (Stage 1)}} \times 100$$
    Standardized to **Total Entry Sessions (Stage 1)** as the denominator across all 5 stages.
  - **Step Conversion Rate (%)**:
    $$\text{Step Conversion Rate} = \frac{\text{Current Stage Sessions}}{\text{Previous Stage Sessions}} \times 100$$
    Measures step-to-step efficiency using the **immediately preceding qualifying stage** as the denominator.
  - **Drop-off Rate (%)**:
    $$\text{Drop-off Rate} = \frac{\text{Previous Stage Sessions} - \text{Current Stage Sessions}}{\text{Previous Stage Sessions}} \times 100$$

### 4. ROAS Metric Disambiguation & Attribution Hierarchy
* **a. Blended ROAS (All-Channel Revenue / Ad Spend)**:
  $$\text{Blended ROAS} = \frac{\text{Total GA4 Revenue (All Channels)}}{\text{Total Google Ads Spend}}$$
  Measures macro marketing leverage. Clearly documented as a top-line commercial ratio, not an ads-attributed return, since it includes revenue from Organic, Direct, Email, and Referral channels.
* **b. GA4 Paid-Channel Revenue / Ad Spend (GA4 Paid ROAS)**:
  $$\text{GA4 Paid ROAS} = \frac{\text{GA4 Attributed Revenue (Google Ads)}}{\text{Total Google Ads Spend}}$$
  Leverages GA4 cross-channel data-driven attribution (DDA), recognizing multi-touch customer conversion paths.
* **c. Google Ads Reported ROAS**:
  $$\text{Google Ads Reported ROAS} = \frac{\text{Google Ads Conversion Value}}{\text{Total Google Ads Spend}}$$
  Sourced from Google Ads self-reported conversions (last paid Google click model). Compatible at campaign and date aggregation levels.

---

## 🔀 Cross-Channel Data Blending Architecture

A primary requirement of multi-source digital marketing analysis is establishing defensible join keys without generating false row-level links or double-counting:

### 1. Shared Dimensions & Join Rules
- **Calendar Date (`YYYY-MM-DD`)**: Present in all four datasets. Enables daily time-series aggregation and cross-platform trend alignment.
- **Landing Page URL Path**: Shared between GA4 (`landing_page`) and Google Search Console (`landing_page`). Enables comparing organic search impressions and clicks with on-site bounce, engagement, and conversion revenue.
- **Campaign Name**: Shared between Google Ads (`campaign`) and GA4 (`campaign` where `acquisition_source == 'Google Ads'`). Enables calculating blended ROAS (`GA4 Attributed Revenue / Ads Spend`).

### 2. Preventing Granularity Mismatch & Double Counting
- **Search Console** data is aggregated at `Date × Query × Landing Page × Country × Device`. It contains no session IDs or cookie IDs. We **never** artificially force a 1-to-1 join between a GSC click and a GA4 session.
- **Google Ads** data is aggregated at `Date × Campaign × Ad Group × Device`.
- Merges are strictly performed at **aggregated dimensional boundaries** (`Date`, `Landing Page`, `Campaign`).

### 3. Understanding Common Discrepancies
- **GSC Organic Clicks vs. GA4 Organic Sessions**:
  - GSC logs clicks on Google SERP pages before site load. Users who navigate away before scripts load, reject cookie banners, or use ad-blockers will generate a GSC click but no GA4 session.
  - Conversely, users returning via bookmarks generate GA4 sessions without a GSC click.
- **Google Ads Clicks vs. GA4 Paid Sessions**:
  - 1 ad click can result in 0 sessions (accidental click bounced instantly) or multiple sessions (returning user within 30 minutes). Standard industry variance is typically 5%–15%.
- **Google Ads Conversions vs. GA4 Conversions**:
  - Google Ads defaults to attributing conversions to the last Google Ads touchpoint.
  - GA4 uses cross-channel data-driven attribution (DDA), sharing conversion credit with Organic, Email, and Social touchpoints.

---

## 🗃️ Dataset Schemas & Real Data Replacement Guide

To replace the synthetic CSVs with your organization's actual Google exports, simply place new CSV files in the `data/` folder matching the schemas below:

### 1. `data/ga4_sessions.csv`
* **Grain**: 1 row per Session ID
* **Required Columns**:
  * `session_id` (str): Unique session identifier (e.g. `SESS_20001`).
  * `user_id` (str): User identifier (e.g. `USR_1042`).
  * `date` (YYYY-MM-DD): Date of session.
  * `acquisition_source` (str): Channel name (`Google Organic`, `Google Ads`, `Direct`, `Social`, `Referral`, `Email`).
  * `source_medium` (str): Raw UTM (e.g. `google / organic`, `google / cpc`).
  * `campaign` (str): Marketing campaign name or `(not set)`.
  * `device_category` (str): `desktop`, `mobile`, `tablet`.
  * `landing_page` (str): First page visited (e.g. `/`, `/pricing`).
  * `is_engaged_session` (int: 0 or 1): GA4 engagement flag.
  * `engagement_time_seconds` (int): Duration in seconds.
  * `pageviews` (int): Count of page views.
  * `has_conversion` (int: 0 or 1): Binary conversion flag.
  * `revenue` (float): Transaction revenue in USD.

### 2. `data/ga4_events.csv`
* **Grain**: 1 row per Event
* **Required Columns**:
  * `event_id` (str): Unique event ID.
  * `session_id` (str): Foreign key to `ga4_sessions.session_id`.
  * `user_id` (str): Foreign key to `ga4_sessions.user_id`.
  * `date` (YYYY-MM-DD): Event date.
  * `timestamp` (YYYY-MM-DD HH:MM:SS): Event timestamp.
  * `event_name` (str): `page_view`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase`, `user_engagement`.
  * `event_category` (str): `navigation`, `ecommerce`, `engagement`.
  * `page_path` (str): URL path of the event.
  * `item_name` (str): Product or plan name.
  * `event_value` (float): Monetary value.

### 3. `data/search_console.csv`
* **Grain**: Date × Query × Landing Page × Country × Device
* **Required Columns**:
  * `date` (YYYY-MM-DD): Search date.
  * `query` (str): Search term.
  * `landing_page` (str): Target landing page.
  * `country` (str): Country name.
  * `device_category` (str): `desktop`, `mobile`, `tablet`.
  * `clicks` (int): Organic clicks.
  * `impressions` (int): Organic impressions.
  * `ctr` (float): Clicks / Impressions.
  * `position` (float): Average rank position.

### 4. `data/google_ads.csv`
* **Grain**: Date × Campaign × Ad Group × Device
* **Required Columns**:
  * `date` (YYYY-MM-DD): Ad serving date.
  * `campaign` (str): Campaign name matching GA4 UTM campaign.
  * `ad_group` (str): Ad group cluster.
  * `device_category` (str): `desktop`, `mobile`, `tablet`.
  * `impressions` (int): Ad impressions.
  * `clicks` (int): Ad clicks.
  * `cost` (float): Spend in USD.
  * `conversions` (int): Google Ads reported conversions.
  * `conversion_value` (float): Reported conversion value in USD.

---

## 🧪 Automated Unit Test Results

The project includes an automated test suite in `tests/test_dashboard.py`.

Run tests with:
```powershell
python -m pytest tests/test_dashboard.py -v
```

### Verified Test Suite (14 / 14 Passed):
1. `test_data_generation_counts`: Verifies record count requirements (GA4 Sessions >= 1000, Events >= 2000, Search Console >= 500, Google Ads >= 300). **PASSED**
2. `test_data_consistency_and_foreign_keys`: Validates that all event `session_id` records map to valid sessions in `ga4_sessions.csv` and checks synthetic flags. **PASSED**
3. `test_safe_divide`: Ensures division by zero, empty arrays, Series broadcasting, and null inputs return default values safely. **PASSED**
4. `test_filtering_logic`: Verifies multi-select filtering for source, campaign, device, and cascading event filters. **PASSED**
5. `test_empty_filter_handling`: Guarantees that empty filter states do not crash metric calculations or raise exceptions. **PASSED**
6. `test_funnel_calculation_monotonicity`: Verifies that stage progression counts are strictly monotonically non-increasing. **PASSED**
7. `test_cross_channel_blending`: Validates date-level, landing page-level, and campaign-level joins without Cartesian explosions. **PASSED**
8. `test_data_dictionaries_coverage`: Confirms complete column schemas and data dictionaries are present for all datasets. **PASSED**
9. `test_chart_generation`: Verifies all Plotly chart generation functions (dual-axis line, donut, horizontal bar, funnel, scatter bubble, grouped bar) render cleanly without property or syntax errors. **PASSED**
10. `test_advertising_cpc_calculation`: Validates advertising CPC (`Spend / Clicks`), Cost per GA4 Session (`Spend / Sessions`), and non-paid channel zeroing without double-counting. **PASSED**
11. `test_gsc_impression_weighted_position`: Verifies that GSC average position uses impression-weighting (`sum(pos*imp)/sum(imp)`) and CTR uses `sum(clicks)/sum(imp)`. **PASSED**
12. `test_chronological_funnel_progression`: Validates strict timestamp order: rejects out-of-order stages (e.g., purchase before checkout), handles skipped stages, repeated events, and equal timestamps. **PASSED**
13. `test_funnel_conversion_percentages_and_edge_cases`: Validates dual conversion rate calculations (Entry-Session CR vs. Step CR), empty dataset handling, and zero denominators. **PASSED**
14. `test_roas_and_attribution_separation`: Validates separation of Blended ROAS (all-channel), GA4 Paid ROAS (DDA cross-channel), and Google Ads Reported ROAS (direct platform value). **PASSED**

---

## ⚖️ Limitations & Production Enhancements

- **Synthetic Modeling**: The current datasets use reproducible pseudorandom distributions tuned to realistic B2B SaaS benchmarks. Real-world client data may exhibit higher variance, seasonality, and long-tail query volumes.
- **Direct API Integration**: In an enterprise production deployment, the CSV pipeline can be augmented with direct API connectors to the **Google Analytics Data API (v1beta)**, **Google Search Console API**, and **Google Ads API** (or automated BigQuery transfer queries) for real-time streaming ingestion.
