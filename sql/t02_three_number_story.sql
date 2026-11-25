-- t02 — The 3-number story: context, change, consequence
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: one number is a headline; three numbers are a story.
-- The pattern is fixed: CONTEXT (where we stood), CHANGE (what
-- moved, by how much), CONSEQUENCE (what it meant — the number
-- that decides whether the change was good news). A story that
-- stops at "change" leaves the manager to guess the consequence,
-- and managers guess wrong.
--
-- QUERY: same mart and quarter totals as t01, plus gross profit
-- (net revenue minus cost of goods). The consequence is
-- deliberate: profit, not revenue — because revenue rose 52.18%
-- while profit rose only 21.80%, and that gap IS the story.
--
-- RETURNS: 3 rows — Context, Change, Consequence — each with its
-- value, its change in percent, and the sentence a manager hears.
-- EXPECTED: Context PKR 3,393,790 (Q1 net revenue) · Change
-- PKR 5,164,520, +52.18% · Consequence PKR 1,576,470 profit,
-- +21.80% on Q1 profit (PKR 1,294,340).

WITH mart AS (
    SELECT
        o.order_id,
        CASE WHEN CAST(strftime('%m', o.order_date) AS INTEGER) <= 3
             THEN 'Q1' ELSE 'Q2' END AS quarter,
        CAST(ROUND(i.quantity * i.unit_price_pkr
                   * (1.0 - o.discount_pct)) AS INTEGER) AS net_pkr,
        i.quantity * p.unit_cost_pkr AS cogs_pkr
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products AS p ON p.product_code = i.product_code
),
q AS (
    SELECT quarter, SUM(net_pkr) AS net,
           SUM(net_pkr - cogs_pkr) AS profit
    FROM mart
    GROUP BY quarter
)
SELECT
    'Context' AS part,
    'Net revenue in Q1 2026 (Jan-Mar, before the promo)' AS label,
    q1.net AS value_pkr,
    NULL AS change_pct,
    'In Q1, before any promo, net revenue was PKR ' || q1.net || '.'
        AS sentence
FROM q AS q1
WHERE q1.quarter = 'Q1'
UNION ALL
SELECT
    'Change',
    'Net revenue in Q2 2026 (Apr-Jun, Eid-sale promo)',
    q2.net,
    ROUND((q2.net - q1.net) * 100.0 / q1.net, 2),
    'In Q2 net revenue rose to PKR ' || q2.net || ', up '
        || ROUND((q2.net - q1.net) * 100.0 / q1.net, 2)
        || '% on Q1.'
FROM q AS q1, q AS q2
WHERE q1.quarter = 'Q1' AND q2.quarter = 'Q2'
UNION ALL
SELECT
    'Consequence',
    'Gross profit in Q2 2026 vs Q1 2026',
    q2.profit,
    ROUND((q2.profit - q1.profit) * 100.0 / q1.profit, 2),
    'Gross profit rose only '
        || ROUND((q2.profit - q1.profit) * 100.0 / q1.profit, 2)
        || '% to PKR ' || q2.profit
        || ' (Q1: PKR ' || q1.profit
        || ') — the promo bought revenue, not profit.'
FROM q AS q1, q AS q2
WHERE q1.quarter = 'Q1' AND q2.quarter = 'Q2';
