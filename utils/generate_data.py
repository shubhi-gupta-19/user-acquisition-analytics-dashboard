"""
Data Generator for User Acquisition & Behavior Analytics Dashboard.
Generates reproducible synthetic datasets representing 90 days of:
1. GA4 Sessions (>= 1000 records)
2. GA4 Events (>= 2000 records)
3. Google Search Console (>= 500 records)
4. Google Ads (>= 300 records)

All datasets are explicitly tagged with 'SAMPLE / SYNTHETIC DATA'.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set fixed seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DATA_ORIGIN_TAG = "SAMPLE / SYNTHETIC DATA"

# Constants & Shared Dimensions
START_DATE = datetime(2024, 7, 1)
DAYS_COUNT = 90
END_DATE = START_DATE + timedelta(days=DAYS_COUNT - 1)

LANDING_PAGES = [
    "/",
    "/pricing",
    "/features/analytics",
    "/features/integrations",
    "/blog/saas-growth-metrics",
    "/blog/cro-best-practices",
    "/demo",
    "/signup"
]

PAGE_WEIGHTS = [0.35, 0.15, 0.15, 0.08, 0.12, 0.07, 0.05, 0.03]

SOURCES_CONFIG = [
    {"source_medium": "google / organic", "source": "Google Organic", "campaign": "(not set)", "weight": 0.32},
    {"source_medium": "google / cpc", "source": "Google Ads", "campaign": "brand_search", "weight": 0.12},
    {"source_medium": "google / cpc", "source": "Google Ads", "campaign": "generic_b2b_tools", "weight": 0.08},
    {"source_medium": "google / cpc", "source": "Google Ads", "campaign": "summer_sale_2024", "weight": 0.05},
    {"source_medium": "google / cpc", "source": "Google Ads", "campaign": "retargeting_q3", "weight": 0.03},
    {"source_medium": "direct / (none)", "source": "Direct", "campaign": "(not set)", "weight": 0.20},
    {"source_medium": "social / linkedin", "source": "Social", "campaign": "b2b_thought_leadership", "weight": 0.06},
    {"source_medium": "social / twitter", "source": "Social", "campaign": "summer_announcement", "weight": 0.04},
    {"source_medium": "referral / partner_blog", "source": "Referral", "campaign": "(referral)", "weight": 0.05},
    {"source_medium": "email / newsletter", "source": "Email", "campaign": "weekly_digest_q3", "weight": 0.05},
]

DEVICES = ["desktop", "mobile", "tablet"]
DEVICE_WEIGHTS = [0.58, 0.36, 0.06]

ADS_CAMPAIGNS = [
    {"campaign": "brand_search", "ad_group": "Brand_Exact", "avg_cpc": 1.45, "ctr_base": 0.085},
    {"campaign": "generic_b2b_tools", "ad_group": "Analytics_Core", "avg_cpc": 3.80, "ctr_base": 0.035},
    {"campaign": "summer_sale_2024", "ad_group": "Promo_Discount", "avg_cpc": 2.20, "ctr_base": 0.052},
    {"campaign": "retargeting_q3", "ad_group": "Cart_Abandoners", "avg_cpc": 2.90, "ctr_base": 0.068},
]

GSC_QUERIES = [
    {"query": "business analytics dashboard", "page": "/", "base_pos": 3.2, "base_imp": 850},
    {"query": "user behavior analytics tool", "page": "/features/analytics", "base_pos": 4.1, "base_imp": 620},
    {"query": "saas funnel tracking software", "page": "/features/analytics", "base_pos": 5.4, "base_imp": 480},
    {"query": "b2b customer journey analytics", "page": "/features/analytics", "base_pos": 6.8, "base_imp": 390},
    {"query": "analytics software pricing", "page": "/pricing", "base_pos": 2.8, "base_imp": 540},
    {"query": "enterprise analytics pricing tiers", "page": "/pricing", "base_pos": 3.5, "base_imp": 310},
    {"query": "saas growth metrics guide", "page": "/blog/saas-growth-metrics", "base_pos": 2.1, "base_imp": 920},
    {"query": "conversion rate optimization tips 2024", "page": "/blog/cro-best-practices", "base_pos": 4.5, "base_imp": 710},
    {"query": "ga4 third party integration connector", "page": "/features/integrations", "base_pos": 7.2, "base_imp": 290},
    {"query": "interactive business intelligence demo", "page": "/demo", "base_pos": 3.9, "base_imp": 360},
    {"query": "free analytics trial signup", "page": "/signup", "base_pos": 2.4, "base_imp": 420},
    {"query": "brand name analytics platform", "page": "/", "base_pos": 1.2, "base_imp": 1250},
]


def generate_ga4_sessions_and_events(num_sessions=1600):
    """
    Generate realistic GA4 Sessions and corresponding Events.
    Maintains relational consistency between session_id, user_id, date, and e-commerce funnel events.
    """
    sessions = []
    events = []
    
    # Pool of users for repeat visits (approx 1000 unique users for 1600 sessions)
    num_users = int(num_sessions * 0.65)
    user_ids = [f"USR_{1000 + i:04d}" for i in range(num_users)]
    
    event_counter = 1
    
    # Pre-select source config indices
    source_indices = np.random.choice(
        len(SOURCES_CONFIG),
        size=num_sessions,
        p=[c["weight"] for c in SOURCES_CONFIG]
    )
    
    for sess_idx in range(1, num_sessions + 1):
        session_id = f"SESS_{20000 + sess_idx:05d}"
        user_id = random.choice(user_ids)
        
        # Day distribution with slight weekend dip and upward growth trend
        day_offset = random.randint(0, DAYS_COUNT - 1)
        sess_date = START_DATE + timedelta(days=day_offset)
        is_weekend = sess_date.weekday() >= 5
        
        src_cfg = SOURCES_CONFIG[source_indices[sess_idx - 1]]
        source_medium = src_cfg["source_medium"]
        acq_source = src_cfg["source"]
        campaign = src_cfg["campaign"]
        
        landing_page = np.random.choice(LANDING_PAGES, p=PAGE_WEIGHTS)
        device = np.random.choice(DEVICES, p=DEVICE_WEIGHTS)
        
        # Channel-specific engagement & conversion propensity
        base_eng_prob = {
            "Google Organic": 0.68,
            "Google Ads": 0.62,
            "Direct": 0.72,
            "Social": 0.52,
            "Referral": 0.65,
            "Email": 0.75,
        }.get(acq_source, 0.60)
        
        if is_weekend:
            base_eng_prob -= 0.08
            
        is_engaged = 1 if random.random() < base_eng_prob else 0
        
        if is_engaged:
            engagement_time = int(np.random.gamma(shape=3.5, scale=40)) + 15
            pageviews = int(np.random.geometric(p=0.35)) + 1
        else:
            engagement_time = random.randint(1, 10)
            pageviews = 1
            
        # Conversion probability (higher on Pricing, Demo, Signup, and Paid/Email)
        conv_multiplier = 1.0
        if landing_page in ["/pricing", "/demo", "/signup"]:
            conv_multiplier *= 2.2
        if acq_source in ["Email", "Google Ads", "Direct"]:
            conv_multiplier *= 1.4
            
        base_conv_prob = 0.045 * conv_multiplier
        if not is_engaged:
            base_conv_prob = 0.0
            
        has_conversion = 1 if random.random() < min(base_conv_prob, 0.40) else 0
        
        if has_conversion:
            # Pricing plans: Starter ($49), Pro ($149), Enterprise ($499)
            plan_revenue = random.choice([49.0, 149.0, 149.0, 499.0])
            revenue = plan_revenue
        else:
            revenue = 0.0
            
        sessions.append({
            "session_id": session_id,
            "user_id": user_id,
            "date": sess_date.strftime("%Y-%m-%d"),
            "acquisition_source": acq_source,
            "source_medium": source_medium,
            "campaign": campaign,
            "device_category": device,
            "landing_page": landing_page,
            "is_engaged_session": is_engaged,
            "engagement_time_seconds": engagement_time,
            "pageviews": pageviews,
            "has_conversion": has_conversion,
            "revenue": round(revenue, 2),
            "data_flag": DATA_ORIGIN_TAG
        })
        
        # ---------------- Generate Realistic Funnel Events ----------------
        # 1. Base Event: page_view / session_start
        base_hour = random.randint(8, 22)
        base_minute = random.randint(0, 50)
        t0 = sess_date + timedelta(hours=base_hour, minutes=base_minute)
        
        events.append({
            "event_id": f"EVT_{event_counter:07d}",
            "session_id": session_id,
            "user_id": user_id,
            "date": sess_date.strftime("%Y-%m-%d"),
            "timestamp": t0.strftime("%Y-%m-%d %H:%M:%S"),
            "event_name": "page_view",
            "event_category": "navigation",
            "page_path": landing_page,
            "item_name": "(not set)",
            "event_value": 0.0,
            "data_flag": DATA_ORIGIN_TAG
        })
        event_counter += 1
        
        if is_engaged:
            # 2. Scroll or engagement
            events.append({
                "event_id": f"EVT_{event_counter:07d}",
                "session_id": session_id,
                "user_id": user_id,
                "date": sess_date.strftime("%Y-%m-%d"),
                "timestamp": (t0 + timedelta(seconds=random.randint(10, 30))).strftime("%Y-%m-%d %H:%M:%S"),
                "event_name": "user_engagement",
                "event_category": "engagement",
                "page_path": landing_page,
                "item_name": "(not set)",
                "event_value": 0.0,
                "data_flag": DATA_ORIGIN_TAG
            })
            event_counter += 1
            
            # E-commerce Funnel Progression:
            # Stage 1: view_item (product / plan view)
            # 65% of engaged users view a plan
            reaches_view_item = random.random() < 0.65 or has_conversion
            if reaches_view_item:
                plan_viewed = random.choice(["Starter Pack", "Pro Tier", "Enterprise Tier"])
                events.append({
                    "event_id": f"EVT_{event_counter:07d}",
                    "session_id": session_id,
                    "user_id": user_id,
                    "date": sess_date.strftime("%Y-%m-%d"),
                    "timestamp": (t0 + timedelta(seconds=random.randint(35, 60))).strftime("%Y-%m-%d %H:%M:%S"),
                    "event_name": "view_item",
                    "event_category": "ecommerce",
                    "page_path": "/pricing",
                    "item_name": plan_viewed,
                    "event_value": 0.0,
                    "data_flag": DATA_ORIGIN_TAG
                })
                event_counter += 1
                
                # Stage 2: add_to_cart
                # 45% of view_item proceed to add_to_cart
                reaches_add_to_cart = (random.random() < 0.45) or has_conversion
                if reaches_add_to_cart:
                    events.append({
                        "event_id": f"EVT_{event_counter:07d}",
                        "session_id": session_id,
                        "user_id": user_id,
                        "date": sess_date.strftime("%Y-%m-%d"),
                        "timestamp": (t0 + timedelta(seconds=random.randint(65, 110))).strftime("%Y-%m-%d %H:%M:%S"),
                        "event_name": "add_to_cart",
                        "event_category": "ecommerce",
                        "page_path": "/pricing",
                        "item_name": plan_viewed,
                        "event_value": 0.0,
                        "data_flag": DATA_ORIGIN_TAG
                    })
                    event_counter += 1
                    
                    # Stage 3: begin_checkout
                    # 60% of cart proceed to checkout
                    reaches_checkout = (random.random() < 0.60) or has_conversion
                    if reaches_checkout:
                        events.append({
                            "event_id": f"EVT_{event_counter:07d}",
                            "session_id": session_id,
                            "user_id": user_id,
                            "date": sess_date.strftime("%Y-%m-%d"),
                            "timestamp": (t0 + timedelta(seconds=random.randint(120, 180))).strftime("%Y-%m-%d %H:%M:%S"),
                            "event_name": "begin_checkout",
                            "event_category": "ecommerce",
                            "page_path": "/checkout",
                            "item_name": plan_viewed,
                            "event_value": 0.0,
                            "data_flag": DATA_ORIGIN_TAG
                        })
                        event_counter += 1
                        
                        # Stage 4: purchase
                        if has_conversion:
                            events.append({
                                "event_id": f"EVT_{event_counter:07d}",
                                "session_id": session_id,
                                "user_id": user_id,
                                "date": sess_date.strftime("%Y-%m-%d"),
                                "timestamp": (t0 + timedelta(seconds=random.randint(190, 260))).strftime("%Y-%m-%d %H:%M:%S"),
                                "event_name": "purchase",
                                "event_category": "ecommerce",
                                "page_path": "/thank-you",
                                "item_name": plan_viewed,
                                "event_value": round(revenue, 2),
                                "data_flag": DATA_ORIGIN_TAG
                            })
                            event_counter += 1

    df_sessions = pd.DataFrame(sessions)
    df_events = pd.DataFrame(events)
    return df_sessions, df_events


def generate_search_console_data():
    """
    Generate Google Search Console query & page performance data across 90 days.
    Contains at least 500 records.
    """
    records = []
    countries = ["United States", "United Kingdom", "Germany", "Canada", "India"]
    country_weights = [0.45, 0.20, 0.15, 0.10, 0.10]
    
    for day in range(DAYS_COUNT):
        cur_date = (START_DATE + timedelta(days=day)).strftime("%Y-%m-%d")
        
        # Select 7-10 queries each day
        daily_queries = random.sample(GSC_QUERIES, k=random.randint(7, 10))
        
        for q_item in daily_queries:
            device = np.random.choice(DEVICES, p=DEVICE_WEIGHTS)
            country = np.random.choice(countries, p=country_weights)
            
            # Position fluctuation around base
            position = max(1.0, round(q_item["base_pos"] + np.random.normal(0, 0.6), 1))
            
            # Impressions based on query popularity & day
            imp_noise = np.random.uniform(0.7, 1.3)
            impressions = int(q_item["base_imp"] * 0.1 * imp_noise)
            if device == "mobile":
                impressions = int(impressions * 0.7)
            impressions = max(impressions, 12)
            
            # CTR is negatively correlated with position (typical SEO curve)
            # Position 1: ~25%, Position 2: ~15%, Position 3: ~10%, Position 5: ~4%, Position 10: ~1%
            expected_ctr = max(0.012, 0.35 / (position ** 0.85))
            ctr = round(float(np.clip(np.random.normal(expected_ctr, 0.015), 0.008, 0.42)), 4)
            clicks = max(1, int(round(impressions * ctr)))
            
            records.append({
                "date": cur_date,
                "query": q_item["query"],
                "landing_page": q_item["page"],
                "country": country,
                "device_category": device,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": round(clicks / impressions, 4),
                "position": position,
                "data_flag": DATA_ORIGIN_TAG
            })
            
    df_gsc = pd.DataFrame(records)
    return df_gsc


def generate_google_ads_data():
    """
    Generate Google Ads campaign-date records across 90 days.
    Contains at least 300 records.
    """
    records = []
    
    for day in range(DAYS_COUNT):
        cur_date = (START_DATE + timedelta(days=day)).strftime("%Y-%m-%d")
        
        for camp in ADS_CAMPAIGNS:
            # 1 to 2 device segments per campaign per day
            dev_sample = random.sample(DEVICES, k=random.randint(1, 2))
            
            for dev in dev_sample:
                # Impressions
                base_imp = random.randint(180, 850) if dev == "desktop" else random.randint(80, 420)
                
                # CTR
                ctr = float(np.clip(np.random.normal(camp["ctr_base"], 0.008), 0.015, 0.16))
                clicks = max(1, int(round(base_imp * ctr)))
                
                # CPC
                avg_cpc = round(float(np.clip(np.random.normal(camp["avg_cpc"], 0.25), 0.80, 8.50)), 2)
                cost = round(clicks * avg_cpc, 2)
                
                # Conversions (3% - 12% conversion rate on paid clicks)
                conv_rate = float(np.clip(np.random.normal(0.065, 0.02), 0.01, 0.18))
                conversions = int(np.random.binomial(clicks, conv_rate))
                
                # Conversion value
                if conversions > 0:
                    val_per_conv = random.choice([49.0, 149.0, 249.0, 499.0])
                    conversion_value = round(conversions * val_per_conv, 2)
                else:
                    conversion_value = 0.0
                    
                records.append({
                    "date": cur_date,
                    "campaign": camp["campaign"],
                    "ad_group": camp["ad_group"],
                    "device_category": dev,
                    "impressions": base_imp,
                    "clicks": clicks,
                    "cost": cost,
                    "conversions": conversions,
                    "conversion_value": conversion_value,
                    "ctr": round(clicks / base_imp, 4),
                    "avg_cpc": avg_cpc,
                    "cpa": round(cost / conversions, 2) if conversions > 0 else 0.0,
                    "roas": round(conversion_value / cost, 2) if cost > 0 else 0.0,
                    "data_flag": DATA_ORIGIN_TAG
                })
                
    df_ads = pd.DataFrame(records)
    return df_ads


def generate_all_datasets(output_dir="data"):
    """Generate all 4 synthetic datasets and save them to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating GA4 Sessions and Events...")
    df_sessions, df_events = generate_ga4_sessions_and_events(num_sessions=1650)
    
    print("Generating Search Console Data...")
    df_gsc = generate_search_console_data()
    
    print("Generating Google Ads Data...")
    df_ads = generate_google_ads_data()
    
    # Save CSVs
    p_sessions = os.path.join(output_dir, "ga4_sessions.csv")
    p_events = os.path.join(output_dir, "ga4_events.csv")
    p_gsc = os.path.join(output_dir, "search_console.csv")
    p_ads = os.path.join(output_dir, "google_ads.csv")
    
    df_sessions.to_csv(p_sessions, index=False)
    df_events.to_csv(p_events, index=False)
    df_gsc.to_csv(p_gsc, index=False)
    df_ads.to_csv(p_ads, index=False)
    
    print(f"Generated {len(df_sessions)} GA4 Sessions -> {p_sessions}")
    print(f"Generated {len(df_events)} GA4 Events -> {p_events}")
    print(f"Generated {len(df_gsc)} Search Console rows -> {p_gsc}")
    print(f"Generated {len(df_ads)} Google Ads rows -> {p_ads}")
    
    return {
        "sessions": df_sessions,
        "events": df_events,
        "search_console": df_gsc,
        "google_ads": df_ads
    }


if __name__ == "__main__":
    generate_all_datasets()
