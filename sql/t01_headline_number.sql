-- t01 — The headline number: one KPI, stated with its comparison
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: an executive summary opens with ONE number. A number
-- with no comparison is trivia ("revenue was PKR 5,164,520" —
-- good? bad? nobody knows). The headline earns its place by
-- carrying its comparison in the same sentence: the value, the
-- period it is compared with, and the change in percent.
--
-- QUERY: the mart CTE builds one enriched line per order line
-- (net revenue = quantity x price x (1 - discount)). The quarter
-- CTE totals net revenue per quarter; the final SELECT states Q2
-- against Q1 — the only honest comparison in a six-month dataset
-- with no prior year (there is no 2025 to compare with, and the
-- file does not invent one).
--
-- RETURNS: 1 row — the headline KPI, its comparison, and the
-- headline sentence a manager would hear first.
-- EXPECTED: Q2 net revenue PKR 5,164,520, up 52.18% on Q1
-- (PKR 3,393,790). The sentence is the checkable claim: every
-- number in it is a column in the same row.

WITH mart AS (
    SELECT
        o.order_id,
        o.order_date,
        CASE WHEN CAST(strftime('%m', o.order_date) AS INTEGER) <= 3
             THEN 'Q1' ELSE 'Q2' END AS quarter,
        CAST(ROUND(i.quantity * i.unit_price_pkr
                   * (1.0 - o.discount_pct)) AS INTEGER) AS net_pkr
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
),
q AS (
    SELECT quarter, SUM(net_pkr) AS net
    FROM mart
    GROUP BY quarter
)
SELECT
    'Net revenue' AS metric,
    'Q2 2026 (Apr-Jun)' AS period,
    q2.net AS value_pkr,
    'Q1 2026 (Jan-Mar)' AS comparison_period,
    q1.net AS comparison_value_pkr,
    ROUND((q2.net - q1.net) * 100.0 / q1.net, 2) AS change_pct,
    'Net revenue was PKR ' || q2.net || ' in Q2 2026, up '
        || ROUND((q2.net - q1.net) * 100.0 / q1.net, 2)
        || '% on Q1 2026 (PKR ' || q1.net || ').'
        AS headline_sentence
FROM q AS q1, q AS q2
WHERE q1.quarter = 'Q1' AND q2.quarter = 'Q2';
