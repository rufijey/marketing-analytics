-- ====================================================================
-- 01_ddl_raw_marketing_campaigns.sql
-- Raw Marketing Campaigns Table DDL in Google BigQuery
-- Project: stone-booking-511312-g0
-- Dataset: martech_dwh
-- ====================================================================

CREATE TABLE IF NOT EXISTS `stone-booking-511312-g0.martech_dwh.raw_marketing_campaigns`
(
  date DATE OPTIONS(description="Advertising activity date (YYYY-MM-DD)"),
  platform STRING OPTIONS(description="Ad platform: Google Ads, Meta Ads, TikTok Ads, LinkedIn Ads"),
  campaign_id STRING OPTIONS(description="Unique campaign identifier"),
  campaign_name STRING OPTIONS(description="Marketing campaign name"),
  campaign_type STRING OPTIONS(description="Campaign category (Search, Social, Video, PMax, Sponsored)"),
  campaign_status STRING OPTIONS(description="Operational status (Active, Paused)"),
  audience_segment STRING OPTIONS(description="Target audience segment (Cold, Retargeting, Lookalike, Intent)"),
  creative_name STRING OPTIONS(description="Creative concept or format (UGC, Static, Video, Carousel)"),
  country STRING OPTIONS(description="2-letter ISO country code (US, GB, DE, FR, CA, AU, PL)"),
  device_category STRING OPTIONS(description="User device category (Mobile, Desktop, Tablet)"),
  impressions INT64 OPTIONS(description="Total ad impressions delivered"),
  clicks INT64 OPTIONS(description="Total ad clicks generated"),
  spend FLOAT64 OPTIONS(description="Total advertising spend in USD"),
  leads INT64 OPTIONS(description="Micro-conversions / Leads generated (Stage 1)"),
  purchases INT64 OPTIONS(description="Macro-conversions / Completed purchases (Stage 2)"),
  revenue FLOAT64 OPTIONS(description="Gross sales revenue generated in USD"),
  cogs FLOAT64 OPTIONS(description="Cost of Goods Sold in USD")
)
CLUSTER BY platform, country, campaign_id;
