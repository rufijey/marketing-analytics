-- ====================================================================
-- 03_mart_unit_economics_geo_creative.sql
-- Aggregated Unit Economics by Country and Creative Mart View
-- Project: stone-booking-511312-g0
-- Dataset: martech_dwh
-- ====================================================================

CREATE OR REPLACE VIEW `stone-booking-511312-g0.martech_dwh.mart_unit_economics_geo_creative` AS
WITH aggregated AS (
    SELECT
        country,
        CASE 
            WHEN country IN ('US', 'GB', 'DE', 'CA', 'AU') THEN 'Tier 1'
            ELSE 'Tier 2'
        END AS country_tier,
        platform,
        campaign_name,
        creative_name,
        SUM(impressions) AS total_impressions,
        SUM(clicks) AS total_clicks,
        ROUND(SUM(spend), 2) AS total_spend,
        SUM(leads) AS total_leads,
        SUM(purchases) AS total_purchases,
        ROUND(SUM(revenue), 2) AS total_revenue,
        ROUND(SUM(cogs), 2) AS total_cogs
    FROM `stone-booking-511312-g0.martech_dwh.raw_marketing_campaigns`
    GROUP BY 1, 2, 3, 4, 5
)
SELECT
    country,
    country_tier,
    platform,
    campaign_name,
    creative_name,
    total_impressions,
    total_clicks,
    total_spend,
    total_leads,
    total_purchases,
    total_revenue,
    total_cogs,
    
    -- Unit profitability
    ROUND(total_revenue - total_cogs, 2) AS gross_profit,
    ROUND((total_revenue - total_cogs) - total_spend, 2) AS contribution_margin,
    
    -- Performance metrics
    ROUND(SAFE_DIVIDE(total_clicks, total_impressions) * 100, 2) AS blended_ctr_pct,
    ROUND(SAFE_DIVIDE(total_spend, total_clicks), 2) AS blended_cpc,
    ROUND(SAFE_DIVIDE(total_spend, total_leads), 2) AS blended_cpl,
    ROUND(SAFE_DIVIDE(total_spend, total_purchases), 2) AS blended_cpa,
    ROUND(SAFE_DIVIDE(total_revenue, total_purchases), 2) AS blended_aov,
    ROUND(SAFE_DIVIDE(total_revenue, total_spend), 2) AS blended_roas,
    
    -- Unit economics per single order
    ROUND(SAFE_DIVIDE((total_revenue - total_cogs) - total_spend, total_purchases), 2) AS cm_per_order,
    ROUND(SAFE_DIVIDE((total_revenue - total_cogs) - total_spend, total_revenue) * 100, 2) AS contribution_margin_pct,
    
    -- Automated profitability classification
    CASE
        WHEN ((total_revenue - total_cogs) - total_spend) > 0 AND SAFE_DIVIDE(total_revenue, total_spend) >= 2.5 
            THEN 'High Profit (Scale Up)'
        WHEN ((total_revenue - total_cogs) - total_spend) > 0 
            THEN 'Profitable (Optimize)'
        WHEN ((total_revenue - total_cogs) - total_spend) >= -500 
            THEN 'Near Break-Even (Tune)'
        ELSE 'Loss-Making (Stop / Cut)'
    END AS unit_profitability_status

FROM aggregated;
