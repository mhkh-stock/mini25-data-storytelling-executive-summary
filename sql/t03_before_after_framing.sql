-- t03 — Before/after framing: same metric, two periods, honest baseline
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: "before vs after" only works if the "before" is a fair
-- baseline. Q1 (Jan–Mar, no promo) is the baseline here; Q2
-- (Apr–Jun) is the promo period. The file states that in the
-- baseline_note column instead of hiding it — Q2 is NOT
-- like-for-like with Q1, because the promo changed the mix
-- (discounts, volume, channel behaviour). A before/after that
-- pretends the two periods differ only in time is a lie with
-- true numbers.
--
-- QUERY: one row per quarter with the full P&L shape — orders,
-- lines, units, gross, discount, net, profit, margin, average
-- order value — so the reader can see WHICH lines moved, not
-- just that the total moved.
--
-- RETURNS: 2 rows, Q1 then Q2.
-- EXPECTED: Q1 205 orders, PKR 3,393,790 net, 38.14% margin ·
-- Q2 345 orders, PKR 5,164,520 net, 30.53% margin. Discounts:
-- Q1 PKR 52,710, Q2 PKR 720,180.

WITH mart AS (
    SELECT
        o.order_id,
        CASE WHEN CAST(strftime('%m', o.order_date) AS INTEGER) <= 3
             THEN 'Q1' ELSE 'Q2' END AS quarter,
        i.quantity,
        i.quantity * i.unit_price_pkr AS gross_pkr,
        CAST(ROUND(i.quantity * i.unit_price_pkr
                   * (1.0 - o.discount_pct)) AS INTEGER) AS net_pkr,
        i.quantity * p.unit_cost_pkr AS cogs_pkr
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products AS p ON p.product_code = i.product_code
)
SELECT
    quarter,
    COUNT(DISTINCT order_id) AS orders,
    COUNT(*) AS lines,
    SUM(quantity) AS units,
    SUM(gross_pkr) AS gross_pkr,
    SUM(gross_pkr) - SUM(net_pkr) AS discount_pkr,
    SUM(net_pkr) AS net_pkr,
    SUM(net_pkr - cogs_pkr) AS gross_profit_pkr,
    ROUND(SUM(net_pkr - cogs_pkr) * 100.0 / SUM(net_pkr), 2)
        AS margin_pct,
    ROUND(SUM(net_pkr) * 1.0 / COUNT(DISTINCT order_id), 2)
        AS avg_order_value_pkr,
    CASE WHEN quarter = 'Q1'
         THEN 'Baseline: Jan-Mar, no promo — same shop, full prices.'
         ELSE 'Promo period: the Apr-May Eid sale drove Q2 (20-30% '
              || 'off most orders); NOT like-for-like with Q1 — the '
              || 'mix changed.'
    END AS baseline_note
FROM mart
GROUP BY quarter
ORDER BY quarter;
