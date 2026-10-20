"""
generate_marketing_data.py
Realistic full-funnel marketing dataset generator based on industry performance benchmarks
(Meta Ads, Google Ads, TikTok Ads, LinkedIn Ads) with automated loading into Google BigQuery.
"""

import os
import random
import datetime
import numpy as np
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# 1. Set seed for reproducibility
np.random.seed(42)
random.seed(42)

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
DATASET_ID = "martech_dwh"
TABLE_ID = "raw_marketing_campaigns"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)
CSV_BACKUP_PATH = os.path.join(OUTPUT_DIR, "raw_marketing_campaigns.csv")
EXCEL_BACKUP_PATH = os.path.join(OUTPUT_DIR, "raw_marketing_campaigns.xlsx")

# 2. Marketing platform configurations and benchmark definitions
PLATFORMS_CONFIG = {
    "Google Ads": {
        "campaigns": [
            {"id": "G_SRC_001", "name": "Search_Brand_Core", "type": "Search", "status": "Active", "intent": "high"},
            {"id": "G_SRC_002", "name": "Search_Generic_Solutions", "type": "Search", "status": "Active", "intent": "high"},
            {"id": "G_PMX_003", "name": "PMax_Smart_Ecom_Scale", "type": "PMax", "status": "Active", "intent": "medium"},
            {"id": "G_YT_004", "name": "YouTube_Video_Action", "type": "Video", "status": "Active", "intent": "low"}
        ],
        "creatives": [
            "Text_Ad_USP_FastShipping", "Text_Ad_Discount_Promo",
            "Responsive_Search_BestQuality", "PMax_AssetGroup_Lifestyle",
            "YT_Video_ProblemSolver_15s"
        ],
        "audiences": ["Brand_Keywords", "High_Intent_Search", "InMarket_Shoppers", "Similar_Audience"],
        "base_cpm": 18.5,       # USD
        "base_ctr": 0.042,      # 4.2% average (Search is higher, YouTube lower)
        "base_cr1": 0.095,      # Clicks -> Leads (9.5%)
        "base_cr2": 0.220,      # Leads -> Purchases (22.0%)
        "base_aov": 88.0        # Average Order Value (USD)
    },
    "Meta Ads": {
        "campaigns": [
            {"id": "FB_PROSP_001", "name": "Prospecting_AdvantagePlus_Catalog", "type": "Social", "status": "Active", "intent": "medium"},
            {"id": "FB_PROSP_002", "name": "Prospecting_Broad_Lifestyle", "type": "Social", "status": "Active", "intent": "low"},
            {"id": "FB_RET_003", "name": "Retargeting_Catalog_Viewers_30d", "type": "Social", "status": "Active", "intent": "high"},
            {"id": "FB_LAL_004", "name": "Lookalike_1pct_Purchasers", "type": "Social", "status": "Active", "intent": "medium"}
        ],
        "creatives": [
            "UGC_Unboxing_Video_01", "Static_Banner_Discount20",
            "Carousel_TopSellers_V1", "Founder_Story_Reel_30s",
            "Review_Quotes_Carousel"
        ],
        "audiences": ["Cold_Broad", "Cold_Interests_Lifestyle", "LAL_1pct_Purchasers", "Retargeting_Visitors_30d"],
        "base_cpm": 11.0,       # USD
        "base_ctr": 0.016,      # 1.6%
        "base_cr1": 0.068,      # Clicks -> Leads (6.8%)
        "base_cr2": 0.165,      # Leads -> Purchases (16.5%)
        "base_aov": 68.0        # USD
    },
    "TikTok Ads": {
        "campaigns": [
            {"id": "TT_SPARK_001", "name": "TikTok_SparkAds_ViralTrend", "type": "Video", "status": "Active", "intent": "low"},
            {"id": "TT_CONV_002", "name": "TikTok_GenZ_Lifestyle_Promo", "type": "Video", "status": "Active", "intent": "low"},
            {"id": "TT_RET_003", "name": "TikTok_Retargeting_EngagedViewers", "type": "Video", "status": "Active", "intent": "medium"}
        ],
        "creatives": [
            "TikTok_Hook_WaitUntilEnd", "Creator_Reaction_Video_Short",
            "Before_After_Transform", "Trend_Audio_LipSync"
        ],
        "audiences": ["GenZ_Viral_Interests", "Creators_Fans", "Engaged_TikTok_Viewers"],
        "base_cpm": 6.8,        # USD
        "base_ctr": 0.024,      # 2.4% (high CTR)
        "base_cr1": 0.075,      # Clicks -> Leads (7.5%)
        "base_cr2": 0.095,      # Leads -> Purchases (9.5% - lower checkout conversion)
        "base_aov": 48.0        # USD
    },
    "LinkedIn Ads": {
        "campaigns": [
            {"id": "LI_B2B_001", "name": "LinkedIn_LeadGen_Enterprise_Execs", "type": "Sponsored", "status": "Active", "intent": "high"},
            {"id": "LI_WHITEPAPER_002", "name": "LinkedIn_ContentDownload_Report", "type": "Sponsored", "status": "Paused", "intent": "medium"}
        ],
        "creatives": [
            "B2B_Single_Image_ROI_Infographic", "B2B_Document_LeadGen_Report",
            "B2B_Carousel_CaseStudy"
        ],
        "audiences": ["C_Level_Executives", "Marketing_Directors", "Operations_Leads"],
        "base_cpm": 38.0,       # High B2B CPM
        "base_ctr": 0.0075,     # 0.75%
        "base_cr1": 0.140,      # Clicks -> Leads (14% via native Lead Gen forms)
        "base_cr2": 0.065,      # Leads -> Deals (6.5%)
        "base_aov": 340.0       # High B2B deal value
    }
}

COUNTRY_FACTORS = {
    "US": {"cpm_mult": 1.40, "cr_mult": 1.15, "aov_mult": 1.25, "weight": 0.35},
    "GB": {"cpm_mult": 1.15, "cr_mult": 1.05, "aov_mult": 1.10, "weight": 0.20},
    "DE": {"cpm_mult": 1.20, "cr_mult": 1.10, "aov_mult": 1.15, "weight": 0.18},
    "CA": {"cpm_mult": 1.10, "cr_mult": 1.00, "aov_mult": 1.05, "weight": 0.12},
    "AU": {"cpm_mult": 1.15, "cr_mult": 1.05, "aov_mult": 1.10, "weight": 0.08},
    "FR": {"cpm_mult": 0.95, "cr_mult": 0.90, "aov_mult": 0.95, "weight": 0.04},
    "PL": {"cpm_mult": 0.65, "cr_mult": 0.85, "aov_mult": 0.75, "weight": 0.03}
}

DEVICE_DISTRIBUTION = [
    ("Mobile", 0.68),
    ("Desktop", 0.26),
    ("Tablet", 0.06)
]


def generate_dataset(num_days=180):
    print(f"[*] Generating synthetic marketing dataset for past {num_days} days...")
    end_date = datetime.date.today() - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=num_days - 1)

    records = []
    
    # Iterate over each day
    for day_idx in range(num_days):
        current_date = start_date + datetime.timedelta(days=day_idx)
        day_of_week = current_date.weekday() # 0=Monday, 6=Sunday
        
        # Weekend seasonality: consumer social ads lift on weekends, B2B/Search softens
        weekend_factor_b2c = 1.18 if day_of_week in [5, 6] else 0.96
        weekend_factor_b2b = 0.55 if day_of_week in [5, 6] else 1.15

        # Long-term growth scaling trend (+25% over 6 months)
        growth_factor = 1.0 + (day_idx / num_days) * 0.25

        for platform, p_config in PLATFORMS_CONFIG.items():
            is_b2b = (platform == "LinkedIn Ads")
            w_factor = weekend_factor_b2b if is_b2b else weekend_factor_b2c

            for camp in p_config["campaigns"]:
                # Paused campaign simulation
                if camp["status"] == "Paused" and day_idx > (num_days * 0.4):
                    continue

                for country, c_factors in COUNTRY_FACTORS.items():
                    # Filter rare low-volume geo pairings for realistic distribution
                    if country in ["FR", "PL"] and random.random() > 0.45:
                        continue

                    # Select device category
                    device = np.random.choice(
                        [d[0] for d in DEVICE_DISTRIBUTION],
                        p=[d[1] for d in DEVICE_DISTRIBUTION]
                    )

                    # Select audience and creative
                    audience = random.choice(p_config["audiences"])
                    creative = random.choice(p_config["creatives"])

                    # Creative variance factor: top performers vs fatigued variants
                    creative_hash = hash(creative) % 100
                    creative_perf_mult = 0.75 + (creative_hash / 100.0) * 0.55
                    
                    # Creative fatigue over lifecycle
                    fatigue_mult = max(0.65, 1.05 - (day_idx / (num_days * 1.3)) * (creative_hash % 2))

                    # 1. Impressions
                    base_volume = 1200 if platform in ["Meta Ads", "Google Ads"] else 800
                    if platform == "LinkedIn Ads":
                        base_volume = 250
                    
                    rand_noise = np.random.normal(1.0, 0.12)
                    impressions = int(base_volume * c_factors["weight"] * 5 * growth_factor * w_factor * rand_noise)
                    impressions = max(50, impressions)

                    # 2. CPM & Spend
                    cpm = p_config["base_cpm"] * c_factors["cpm_mult"] * np.random.normal(1.0, 0.08)
                    spend = round((impressions / 1000.0) * cpm, 2)
                    spend = max(1.5, spend)

                    # 3. CTR & Clicks
                    ctr = p_config["base_ctr"] * creative_perf_mult * fatigue_mult * np.random.normal(1.0, 0.1)
                    if device == "Mobile" and platform in ["TikTok Ads", "Meta Ads"]:
                        ctr *= 1.15
                    elif device == "Desktop" and platform == "Google Ads":
                        ctr *= 1.10
                    ctr = max(0.002, min(0.15, ctr))
                    clicks = int(round(impressions * ctr))
                    clicks = max(1, clicks)

                    # 4. CR1 (Micro-conversions / Leads / Add-to-cart)
                    cr1 = p_config["base_cr1"] * c_factors["cr_mult"] * np.random.normal(1.0, 0.12)
                    if "Retargeting" in camp["name"] or "Brand" in camp["name"]:
                        cr1 *= 1.45  # Warm retargeting converts significantly higher
                    cr1 = max(0.01, min(0.35, cr1))
                    leads = int(np.random.binomial(clicks, min(cr1, 0.99)))

                    # 5. CR2 (Macro-conversions / Completed Purchases)
                    cr2 = p_config["base_cr2"] * c_factors["cr_mult"] * np.random.normal(1.0, 0.1)
                    if "Retargeting" in camp["name"]:
                        cr2 *= 1.35
                    cr2 = max(0.02, min(0.50, cr2))
                    purchases = int(np.random.binomial(leads, min(cr2, 0.99))) if leads > 0 else 0

                    # 6. Revenue & COGS (Cost of Goods Sold)
                    if purchases > 0:
                        aov = p_config["base_aov"] * c_factors["aov_mult"] * np.random.normal(1.0, 0.15)
                        revenue = round(purchases * max(15.0, aov), 2)
                        # COGS: 32% - 42% of revenue
                        cogs_ratio = random.uniform(0.32, 0.42)
                        cogs = round(revenue * cogs_ratio, 2)
                    else:
                        revenue = 0.0
                        cogs = 0.0

                    records.append({
                        "date": current_date,
                        "platform": platform,
                        "campaign_id": camp["id"],
                        "campaign_name": camp["name"],
                        "campaign_type": camp["type"],
                        "campaign_status": camp["status"],
                        "audience_segment": audience,
                        "creative_name": creative,
                        "country": country,
                        "device_category": device,
                        "impressions": int(impressions),
                        "clicks": int(clicks),
                        "spend": float(spend),
                        "leads": int(leads),
                        "purchases": int(purchases),
                        "revenue": float(revenue),
                        "cogs": float(cogs)
                    })

    df = pd.DataFrame(records)
    print(f"[+] Total generated records: {len(df):,}")
    print(f"    Total Ad Spend: ${df['spend'].sum():,.2f}")
    print(f"    Total Revenue: ${df['revenue'].sum():,.2f}")
    print(f"    Blended ROAS: {df['revenue'].sum() / df['spend'].sum():.2f}x")
    print(f"    Total Clicks: {df['clicks'].sum():,}")
    print(f"    Total Leads: {df['leads'].sum():,}")
    print(f"    Total Purchases: {df['purchases'].sum():,}")
    
    # Save local CSV and Excel backups
    df.to_csv(CSV_BACKUP_PATH, index=False)
    try:
        df.to_excel(EXCEL_BACKUP_PATH, index=False)
        print(f"[+] Local Excel saved: {EXCEL_BACKUP_PATH}")
    except Exception:
        pass
    print(f"[+] Local CSV saved: {CSV_BACKUP_PATH}")
    return df


def upload_to_bigquery(df):
    print(f"[*] Connecting to BigQuery using service account: {CREDENTIALS_FILE}")
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"File {CREDENTIALS_FILE} not found!")

    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    # Cast data types for safe BigQuery serialization
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["impressions"] = df["impressions"].astype(int)
    df["clicks"] = df["clicks"].astype(int)
    df["leads"] = df["leads"].astype(int)
    df["purchases"] = df["purchases"].astype(int)
    df["spend"] = df["spend"].astype(float)
    df["revenue"] = df["revenue"].astype(float)
    df["cogs"] = df["cogs"].astype(float)

    full_table_id = f"{client.project}.{DATASET_ID}.{TABLE_ID}"
    print(f"[*] Preparing BigQuery table: {full_table_id}")

    schema = [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED", description="Advertising activity date"),
        bigquery.SchemaField("platform", "STRING", mode="REQUIRED", description="Advertising platform"),
        bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED", description="Campaign identifier"),
        bigquery.SchemaField("campaign_name", "STRING", mode="REQUIRED", description="Campaign name"),
        bigquery.SchemaField("campaign_type", "STRING", mode="NULLABLE", description="Campaign type"),
        bigquery.SchemaField("campaign_status", "STRING", mode="NULLABLE", description="Campaign status"),
        bigquery.SchemaField("audience_segment", "STRING", mode="NULLABLE", description="Audience targeting segment"),
        bigquery.SchemaField("creative_name", "STRING", mode="NULLABLE", description="Creative format or name"),
        bigquery.SchemaField("country", "STRING", mode="REQUIRED", description="Target country ISO code"),
        bigquery.SchemaField("device_category", "STRING", mode="NULLABLE", description="Device category"),
        bigquery.SchemaField("impressions", "INTEGER", mode="REQUIRED", description="Number of ad impressions"),
        bigquery.SchemaField("clicks", "INTEGER", mode="REQUIRED", description="Number of ad clicks"),
        bigquery.SchemaField("spend", "FLOAT64", mode="REQUIRED", description="Advertising spend in USD"),
        bigquery.SchemaField("leads", "INTEGER", mode="REQUIRED", description="Number of micro-conversions / leads"),
        bigquery.SchemaField("purchases", "INTEGER", mode="REQUIRED", description="Number of completed orders"),
        bigquery.SchemaField("revenue", "FLOAT64", mode="REQUIRED", description="Gross revenue generated in USD"),
        bigquery.SchemaField("cogs", "FLOAT64", mode="REQUIRED", description="Cost of Goods Sold in USD"),
    ]

    table = bigquery.Table(full_table_id, schema=schema)
    table.clustering_fields = ["platform", "country", "campaign_id"]

    client.delete_table(full_table_id, not_found_ok=True)
    table = client.create_table(table)
    print(f"[+] Table {full_table_id} successfully created with clustering!")

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    print(f"[*] Uploading data ({len(df):,} rows) to BigQuery...")
    job = client.load_table_from_dataframe(df, full_table_id, job_config=job_config)
    job.result()

    destination_table = client.get_table(full_table_id)
    print(f"[+] SUCCESS! BigQuery table loaded with {destination_table.num_rows:,} rows.")


if __name__ == "__main__":
    df = generate_dataset(num_days=180)
    upload_to_bigquery(df)
