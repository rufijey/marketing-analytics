-- ====================================================================
-- 04_mart_executive_kpis.sql
-- Daily Aggregate KPIs with 7-Day Moving Averages for Executive Summary
-- Project: stone-booking-511312-g0
-- Dataset: martech_dwh
-- ====================================================================

CREATE OR REPLACE VIEW `stone-booking-511312-g0.martech_dwh.mart_executive_kpis` AS
WITH daily_totals AS (
    SELECT
        date,
        SUM(impressions) AS daily_impressions,
        SUM(clicks) AS daily_clicks,
        ROUND(SUM(spend), 2) AS daily_spend,
        SUM(leads) AS daily_leads,
        SUM(purchases) AS daily_purchases,
        ROUND(SUM(revenue), 2) AS daily_revenue,
        ROUND(SUM(cogs), 2) AS daily_cogs,
        ROUND(SUM(revenue) - SUM(cogs), 2) AS daily_gross_profit,
        ROUND((SUM(revenue) - SUM(cogs)) - SUM(spend), 2) AS daily_contribution_margin
    FROM `stone-booking-511312-g0.martech_dwh.raw_marketing_campaigns`
    GROUP BY date
)
SELECT
    date,
    daily_impressions,
    daily_clicks,
    daily_spend,
    daily_leads,
    daily_purchases,
    daily_revenue,
    daily_cogs,
    daily_gross_profit,
    daily_contribution_margin,
    ROUND(SAFE_DIVIDE(daily_clicks, daily_impressions) * 100, 2) AS daily_ctr_pct,
    ROUND(SAFE_DIVIDE(daily_spend, daily_clicks), 2) AS daily_cpc,
    ROUND(SAFE_DIVIDE(daily_spend, daily_leads), 2) AS daily_cpl,
    ROUND(SAFE_DIVIDE(daily_spend, daily_purchases), 2) AS daily_cpa,
    ROUND(SAFE_DIVIDE(daily_revenue, daily_spend), 2) AS daily_roas,
    ROUND(SAFE_DIVIDE(daily_revenue, daily_purchases), 2) AS daily_aov,
    
    -- 7-Day Moving Averages to smooth weekly seasonality
    ROUND(AVG(daily_spend) OVER (
        ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS spend_7d_ma,
    ROUND(AVG(daily_revenue) OVER (
        ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS revenue_7d_ma,
    ROUND(AVG(daily_contribution_margin) OVER (
        ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS cm_7d_ma

FROM daily_totals
ORDER BY date;
