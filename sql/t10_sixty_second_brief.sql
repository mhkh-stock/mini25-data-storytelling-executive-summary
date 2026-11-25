-- t10 — The 60-second verbal brief: say it out loud, from verified numbers
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: a manager's time is sixty seconds, not six pages. The
-- verbal brief is the executive summary spoken: opening (the
-- headline), numbers (three, no more), recommendation (one),
-- close (the one line to remember). Every line is built from the
-- same aggregates as techniques 1–8, so nothing in the brief is
-- said that the pack cannot prove. Percentages are spelled out
-- ("52.18 percent") because a brief is meant to be read aloud.
-- Total: about 130 words — a minute at normal speaking pace.
--
-- QUERY: one scalar CTE holds every number the script needs; the
-- final SELECT emits the eight spoken lines in order, with an
-- approximate speaking time per line (words / 2.5 per second).
--
-- RETURNS: 8 rows — the spoken script, in order.
-- EXPECTED: headline PKR 8,558,310 · Q2 PKR 5,164,520, up 52.18%
-- · promo discounts PKR 645,700 · margin 38.14% to 30.53% · May
-- peak PKR 2,020,840, June -13.71% · Online 41.13%, Stationery
-- 2.82% · 35% margin floor, 20% discount cap.

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
               AS margin_pct
    FROM mart
    GROUP BY quarter
),
m AS (
    SELECT month, SUM(net_pkr) AS net
    FROM mart
    GROUP BY month
),
s AS (
    SELECT
        (SELECT SUM(net_pkr) FROM mart) AS total_net,
        (SELECT net FROM q WHERE quarter = 'Q2') AS q2_net,
        (SELECT net FROM q WHERE quarter = 'Q1') AS q1_net,
        (SELECT margin_pct FROM q WHERE quarter = 'Q1') AS q1_margin,
        (SELECT margin_pct FROM q WHERE quarter = 'Q2') AS q2_margin,
        (SELECT SUM(gross_pkr - net_pkr) FROM mart
         WHERE month IN ('2026-04', '2026-05')) AS promo_discount,
        (SELECT net FROM m WHERE month = '2026-05') AS may_net,
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
SELECT 1 AS seq, 'Opening' AS section,
    'Good morning. Six months, one shop, one story: Noor '
        || 'Electronics made PKR ' || total_net
        || ' in net revenue.' AS script_line,
    7 AS approx_seconds
FROM s
UNION ALL
SELECT 2, 'Numbers',
    'Q2 was PKR ' || q2_net || ', up '
        || ROUND((q2_net - q1_net) * 100.0 / q1_net, 2)
        || ' percent on Q1 — but that growth was bought, not earned.',
    8
FROM s
UNION ALL
SELECT 3, 'Numbers',
    'April and May discounts cost PKR ' || promo_discount
        || ', and margin fell from ' || q1_margin || ' percent to '
        || q2_margin || ' percent.',
    8
FROM s
UNION ALL
SELECT 4, 'Numbers',
    'May was the peak at PKR ' || may_net
        || ', then June fell ' || ABS(jun_mom)
        || ' percent when the promo ended.',
    7
FROM s
UNION ALL
SELECT 5, 'Numbers',
    'Online leads with ' || on_share
        || ' percent of revenue; Stationery is just ' || st_share
        || ' percent.',
    6
FROM s
UNION ALL
SELECT 6, 'Recommendation',
    'So: repeat the promo only with a 35 percent margin floor and '
        || 'a 20 percent discount cap.',
    7
FROM s
UNION ALL
SELECT 7, 'Recommendation',
    'Put the next ad spend behind Online, and bundle the Notebook '
        || 'Set or review the range.',
    7
FROM s
UNION ALL
SELECT 8, 'Close',
    'That is the half in sixty seconds: growth bought on discount, '
        || 'margin down, Online leading.',
    7
FROM s;
