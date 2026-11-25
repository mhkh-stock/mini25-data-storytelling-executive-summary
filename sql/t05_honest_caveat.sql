-- t05 — The honest caveat: a number that looks good but isn't
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: the headline (t01) is true — net revenue rose 52.18%
-- — and it is also misleading on its own, because the growth was
-- bought with discounts. The caveat is not a footnote; it is a
-- technique: the same quarters, shown with the discount bill and
-- the margin beside the revenue, so the good number and the bad
-- number share one table. A summary that reports the revenue
-- without the margin is not optimistic, it is incomplete.
--
-- QUERY: per quarter — gross, discount given away, discount as a
-- share of gross, net, cost, profit, margin — plus a
-- caveat_sentence that states the trade-off in one line. The Q2
-- sentence is built from both quarters' values, so it cannot
-- drift from the table.
--
-- RETURNS: 2 rows, Q1 then Q2.
-- EXPECTED: Q1 margin 38.14% on PKR 52,710 of discounts · Q2
-- margin 30.53% on PKR 720,180 of discounts; net revenue up
-- 52.18% while margin fell 7.61 points.

WITH mart AS (
    SELECT
        CASE WHEN CAST(strftime('%m', o.order_date) AS INTEGER) <= 3
             THEN 'Q1' ELSE 'Q2' END AS quarter,
        i.quantity * i.unit_price_pkr AS gross_pkr,
        CAST(ROUND(i.quantity * i.unit_price_pkr
                   * (1.0 - o.discount_pct)) AS INTEGER) AS net_pkr,
        i.quantity * p.unit_cost_pkr AS cogs_pkr
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products AS p ON p.product_code = i.product_code
),
agg AS (
    SELECT
        quarter,
        SUM(gross_pkr) AS gross_pkr,
        SUM(gross_pkr) - SUM(net_pkr) AS discount_pkr,
        SUM(net_pkr) AS net_pkr,
        SUM(cogs_pkr) AS cogs_pkr,
        SUM(net_pkr - cogs_pkr) AS gross_profit_pkr,
        ROUND(SUM(net_pkr - cogs_pkr) * 100.0 / SUM(net_pkr), 2)
            AS margin_pct
    FROM mart
    GROUP BY quarter
),
s AS (
    SELECT
        (SELECT net_pkr FROM agg WHERE quarter = 'Q1') AS q1_net,
        (SELECT net_pkr FROM agg WHERE quarter = 'Q2') AS q2_net,
        (SELECT margin_pct FROM agg WHERE quarter = 'Q1') AS q1_margin
)
SELECT
    a.quarter,
    a.gross_pkr,
    a.discount_pkr,
    ROUND(a.discount_pkr * 100.0 / a.gross_pkr, 2)
        AS discount_share_pct,
    a.net_pkr,
    a.cogs_pkr,
    a.gross_profit_pkr,
    a.margin_pct,
    CASE WHEN a.quarter = 'Q1'
         THEN 'Q1: margin was ' || a.margin_pct || '% on PKR '
              || a.net_pkr || ' of net revenue, with only PKR '
              || a.discount_pkr || ' given away in discounts.'
         ELSE 'Q2: net revenue rose '
              || ROUND((s.q2_net - s.q1_net) * 100.0 / s.q1_net, 2)
              || '% to PKR ' || a.net_pkr || ', but margin fell to '
              || a.margin_pct || '% (from ' || s.q1_margin
              || '%) — PKR ' || a.discount_pkr
              || ' of discounts bought that growth.'
    END AS caveat_sentence
FROM agg AS a
CROSS JOIN s
ORDER BY a.quarter;
