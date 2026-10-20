-- =====================================================================
-- VIEW: Daily Executive KPIs Mart
-- Dataset: martech_dwh
-- View: mart_executive_kpis_daily
-- =====================================================================

CREATE OR REPLACE VIEW stone-booking-511312-g0.martech_dwh.mart_executive_kpis_daily AS
SELECT
    date,
    COUNT(DISTINCT campaign_id) AS active_campaigns_count,
    SUM(impressions) AS total_impressions,
    SUM(clicks) AS total_clicks,
    ROUND(SUM(spend), 2) AS total_spend,
    SUM(leads) AS total_leads,
    SUM(purchases) AS total_purchases,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(cogs), 2) AS total_cogs,
    ROUND(SUM(revenue) - SUM(cogs), 2) AS gross_profit,
    ROUND(SUM(revenue) - SUM(cogs) - SUM(spend), 2) AS contribution_margin,
    ROUND(SAFE_DIVIDE(SUM(revenue), SUM(spend)), 2) AS roas,
    ROUND(SAFE_DIVIDE(SUM(spend), SUM(purchases)), 2) AS blended_cpa,
    ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS blended_ctr_pct
FROM stone-booking-511312-g0.martech_dwh.raw_marketing_campaigns
GROUP BY 1
ORDER BY date DESC;
