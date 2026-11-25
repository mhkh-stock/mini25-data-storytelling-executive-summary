-- t06 — One chart, one message: the monthly trend and its takeaway
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: a chart with five messages has no message. This
-- technique allows exactly one: the monthly net-revenue trend,
-- and the single sentence it supports. The CSV is the chart's
-- data (one row per month, with the month-on-month change so the
-- takeaway can be checked); the PNG drawn from it by
-- src/build.py carries the takeaway as its title, and the title
-- is stored in outputs/summary.json so the sentence is checkable
-- text, not pixels.
--
-- QUERY: monthly net revenue, gross, margin and month-on-month
-- net change (NULL for January — there is no December 2025 in
-- this dataset, and the file does not invent one).
--
-- RETURNS: 6 rows, one per month Jan–Jun 2026.
-- EXPECTED: peak May PKR 2,020,840 (+44.36% on April) · June
-- PKR 1,743,820 (-13.71% on May) · lowest month January
-- PKR 991,350 · margin lowest in May, 26.86%.
-- TAKEAWAY (chart title): "Net revenue peaked in May at
-- PKR 2,020,840 — but the April-May promo bought that growth
-- with PKR 645,700 of discounts, so margin fell from 38.14%
-- in Q1 to 30.53% in Q2."

WITH mart AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS month,
        o.order_id,
        i.quantity * i.unit_price_pkr AS gross_pkr,
        CAST(ROUND(i.quantity * i.unit_price_pkr
                   * (1.0 - o.discount_pct)) AS INTEGER) AS net_pkr,
        i.quantity * p.unit_cost_pkr AS cogs_pkr
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products AS p ON p.product_code = i.product_code
),
monthly AS (
    SELECT
        month,
        COUNT(DISTINCT order_id) AS orders,
        COUNT(*) AS lines,
        SUM(gross_pkr) AS gross_pkr,
        SUM(net_pkr) AS net_pkr,
        ROUND(SUM(net_pkr - cogs_pkr) * 100.0 / SUM(net_pkr), 2)
            AS margin_pct
    FROM mart
    GROUP BY month
)
SELECT
    m.month,
    m.orders,
    m.lines,
    m.gross_pkr,
    m.net_pkr,
    m.margin_pct,
    ROUND((m.net_pkr - prev.net_pkr) * 100.0 / prev.net_pkr, 2)
        AS mom_net_change_pct
FROM monthly AS m
LEFT JOIN monthly AS prev
    ON prev.month = strftime('%Y-%m', date(m.month || '-01', '-1 month'))
ORDER BY m.month;
