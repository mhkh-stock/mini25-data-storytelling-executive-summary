-- t08 — The one-page executive summary: headline, findings, action, risk
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: an executive summary is not a shorter report — it is a
-- fixed shape: HEADLINE (one number + comparison), FINDINGS
-- (three, no more), RECOMMENDATION (one), RISK (one). Anything
-- that does not fit the shape is cut, not squeezed. Every line
-- here is built from the same aggregates as techniques 1–7, so
-- the page cannot disagree with the pack.
--
-- QUERY: one scalar CTE holds every number the page needs; the
-- final SELECT emits the six lines of the page in reading order.
-- src/build.py renders these rows into
-- outputs/executive_summary_one_pager.md (and the PDF) — the
-- page a manager could actually read.
--
-- RETURNS: 6 rows — 1 headline, 3 findings, 1 recommendation,
-- 1 risk.
-- EXPECTED: headline PKR 8,558,310 total, Q2 PKR 5,164,520
-- (+52.18%) · promo discounts Apr-May PKR 645,700 · margin
-- 38.14% to 30.53% · Online 41.13%, Stationery 2.82% · June
-- -13.71%.

WITH mart AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS month,
        CASE WHEN CAST(strftime('%m', o.order_date) AS INTEGER) <= 3
             THEN 'Q1' ELSE 'Q2' END AS quarter,
        o.channel,
        p.category,
        o.order_id,
        i.quantity * i.unit_price_pkr AS gross_pkr,
        CAST(ROUND(i.quantity * i.unit_price_pkr
                   * (1.0 - o.discount_pct)) AS INTEGER) AS net_pkr,
        i.quantity * p.unit_cost_pkr AS cogs_pkr
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products AS p ON p.product_code = i.product_code
),
q AS (
    SELECT quarter, SUM(net_pkr) AS net,
           ROUND(SUM(net_pkr - cogs_pkr) * 100.0 / SUM(net_pkr), 2)
               AS margin_pct,
           SUM(net_pkr - cogs_pkr) AS profit
    FROM mart
    GROUP BY quarter
),
m AS (
    SELECT month, SUM(net_pkr) AS net,
           ROUND(SUM(net_pkr - cogs_pkr) * 100.0 / SUM(net_pkr), 2)
               AS margin_pct
    FROM mart
    GROUP BY month
),
s AS (
    SELECT
        (SELECT SUM(net_pkr) FROM mart) AS total_net,
        (SELECT net FROM q WHERE quarter = 'Q1') AS q1_net,
        (SELECT net FROM q WHERE quarter = 'Q2') AS q2_net,
        (SELECT margin_pct FROM q WHERE quarter = 'Q1') AS q1_margin,
        (SELECT margin_pct FROM q WHERE quarter = 'Q2') AS q2_margin,
        (SELECT profit FROM q WHERE quarter = 'Q1') AS q1_profit,
        (SELECT profit FROM q WHERE quarter = 'Q2') AS q2_profit,
        (SELECT SUM(gross_pkr - net_pkr) FROM mart
         WHERE month IN ('2026-04', '2026-05')) AS promo_discount,
        (SELECT net FROM m WHERE month = '2026-05') AS may_net,
        (SELECT margin_pct FROM m WHERE month = '2026-05') AS may_margin,
        (SELECT ROUND(SUM(net_pkr) * 100.0
                      / (SELECT SUM(net_pkr) FROM mart), 2)
         FROM mart WHERE channel = 'Online') AS on_share,
        (SELECT ROUND(SUM(net_pkr) * 100.0
                      / (SELECT SUM(net_pkr) FROM mart), 2)
         FROM mart WHERE category = 'Stationery') AS st_share,
        (SELECT ROUND(((SELECT net FROM m WHERE month = '2026-06')
                       - (SELECT net FROM m WHERE month = '2026-05'))
                      * 100.0
                      / (SELECT net FROM m WHERE month = '2026-05'), 2)
        ) AS jun_mom
    FROM (SELECT 1)
)
SELECT 'Headline' AS section, 1 AS item_no,
    'Noor Electronics made PKR ' || total_net
        || ' net revenue in Jan-Jun 2026; Q2 was PKR ' || q2_net
        || ', up ' || ROUND((q2_net - q1_net) * 100.0 / q1_net, 2)
        || '% on Q1 (PKR ' || q1_net || ').' AS line_text
FROM s
UNION ALL
SELECT 'Finding', 1,
    'Growth was promo-bought: April-May discounts of PKR '
        || promo_discount || ' drove the May peak of PKR ' || may_net
        || ', the biggest month of the half.'
FROM s
UNION ALL
SELECT 'Finding', 2,
    'Margin fell from ' || q1_margin || '% in Q1 to ' || q2_margin
        || '% in Q2 — profit grew only '
        || ROUND((q2_profit - q1_profit) * 100.0 / q1_profit, 2)
        || '% while revenue grew '
        || ROUND((q2_net - q1_net) * 100.0 / q1_net, 2) || '%.'
FROM s
UNION ALL
SELECT 'Finding', 3,
    'Online leads with ' || on_share
        || '% of net revenue; Stationery is just ' || st_share
        || '% and needs a decision.'
FROM s
UNION ALL
SELECT 'Recommendation', 1,
    'Repeat the promo only with a 35% margin floor and a 20% '
        || 'discount cap, and put the next ad spend behind Online.'
FROM s
UNION ALL
SELECT 'Risk', 1,
    'If the promo repeats without a cap, margin stays near 30% — '
        || 'and June already fell ' || ABS(jun_mom)
        || '% when the promo ended, so a quiet month costs profit, '
        || 'not just revenue.'
FROM s;
