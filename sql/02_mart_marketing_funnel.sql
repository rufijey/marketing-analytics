-- ====================================================================
-- 02_mart_marketing_funnel.sql
-- Full-Funnel Performance and Unit Economics Mart View
-- Project: stone-booking-511312-g0
-- Dataset: martech_dwh
-- ====================================================================

CREATE OR REPLACE VIEW `stone-booking-511312-g0.martech_dwh.mart_marketing_funnel` AS
SELECT
    date,
    platform,
    CASE 
        WHEN platform = 'Google Ads' THEN 'Paid Search / Intent'
        WHEN platform = 'Meta Ads' THEN 'Paid Social'
        WHEN platform = 'TikTok Ads' THEN 'Short-Form Video'
        WHEN platform = 'LinkedIn Ads' THEN 'B2B Sponsored'
        ELSE 'Other'
    END AS channel_group,
    campaign_id,
    campaign_name,
    campaign_type,
    campaign_status,
    audience_segment,
    creative_name,
    country,
    CASE 
        WHEN country IN ('US', 'GB', 'DE', 'CA', 'AU') THEN 'Tier 1'
        ELSE 'Tier 2'
    END AS country_tier,
    device_category,
    
    -- Volume funnel metrics
    impressions,
    clicks,
    spend,
    leads,
    purchases,
    revenue,
    cogs,
    
    -- Cost and efficiency metrics
    ROUND(SAFE_DIVIDE(clicks, impressions) * 100, 2) AS ctr_pct,
    ROUND(SAFE_DIVIDE(spend, clicks), 2) AS cpc,
    ROUND(SAFE_DIVIDE(spend, leads), 2) AS cpl,
    ROUND(SAFE_DIVIDE(spend, purchases), 2) AS cpa,
    
    -- Funnel conversion rates
    ROUND(SAFE_DIVIDE(leads, clicks) * 100, 2) AS cr1_click_to_lead_pct,
    ROUND(SAFE_DIVIDE(purchases, leads) * 100, 2) AS cr2_lead_to_purchase_pct,
    ROUND(SAFE_DIVIDE(purchases, clicks) * 100, 2) AS overall_cr_pct,
    
    -- Financial and unit economics metrics
    ROUND(SAFE_DIVIDE(revenue, purchases), 2) AS aov,
    ROUND(SAFE_DIVIDE(revenue, spend), 2) AS roas,
    ROUND(revenue - cogs, 2) AS gross_profit,
    ROUND(SAFE_DIVIDE(revenue - cogs, revenue) * 100, 2) AS gross_margin_pct,
    ROUND((revenue - cogs) - spend, 2) AS contribution_margin,
    ROUND(SAFE_DIVIDE((revenue - cogs) - spend, revenue) * 100, 2) AS contribution_margin_pct,
    ROUND(SAFE_DIVIDE(revenue - spend, spend) * 100, 2) AS gross_roi_pct,
    ROUND(SAFE_DIVIDE((revenue - cogs) - spend, spend) * 100, 2) AS net_roi_pct

FROM `stone-booking-511312-g0.martech_dwh.raw_marketing_campaigns`;
