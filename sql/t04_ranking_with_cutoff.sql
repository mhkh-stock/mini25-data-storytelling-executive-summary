-- t04 — Ranking with a cut-off: top N plus "the rest"
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: "our top 5 products" without the rest is
-- cherry-picking with a ranking. The honest ranking shows the
-- cut-off AND the tail: top 5 products, then one "All other
-- products" row, then a TOTAL row — so the shares sum to 100%
-- and nobody can quote the top 5 as if they were the business.
-- The cut-off (top 5 of 9) is stated in the row itself.
--
-- QUERY: rank all 9 products by net revenue, keep the top 5,
-- aggregate the remaining 4 into "the rest", and add a TOTAL row.
-- The rank column holds '1'–'5', 'Rest' and 'TOTAL' so the file
-- reads in order.
--
-- RETURNS: 7 rows — 5 ranked products, the rest, the total.
-- EXPECTED: 1 Office Chair PKR 2,430,000 · 2 Mechanical Keyboard
-- PKR 1,556,350 · 3 Dinner Set 24pc PKR 1,228,150 · 4 Desk Lamp
-- PKR 734,160 · 5 Bluetooth Speaker PKR 699,400 · Rest (4
-- products) PKR 1,910,250 · TOTAL PKR 8,558,310 (100.00%).

WITH mart AS (
    SELECT
        p.name AS product_name,
        p.category,
        CAST(ROUND(i.quantity * i.unit_price_pkr
                   * (1.0 - o.discount_pct)) AS INTEGER) AS net_pkr
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products AS p ON p.product_code = i.product_code
),
ranked AS (
    SELECT
        product_name,
        category,
        COUNT(*) AS lines,
        SUM(net_pkr) AS net_pkr,
        ROUND(SUM(net_pkr) * 100.0
              / (SELECT SUM(net_pkr) FROM mart), 2) AS share_pct,
        ROW_NUMBER() OVER (ORDER BY SUM(net_pkr) DESC) AS rn
    FROM mart
    GROUP BY product_name, category
)
SELECT rank, product_name, category, lines, net_pkr, share_pct
FROM (
    SELECT CAST(rn AS TEXT) AS rank, product_name, category, lines,
           net_pkr, share_pct
    FROM ranked
    WHERE rn <= 5
    UNION ALL
    SELECT 'Rest', 'All other products (4)', 'Mixed',
           SUM(lines), SUM(net_pkr),
           ROUND(SUM(net_pkr) * 100.0
                 / (SELECT SUM(net_pkr) FROM mart), 2)
    FROM ranked
    WHERE rn > 5
    UNION ALL
    SELECT 'TOTAL', 'All products (9)', 'Mixed',
           SUM(lines), SUM(net_pkr), 100.0
    FROM ranked
)
ORDER BY
    CASE WHEN rank = 'TOTAL' THEN 3
         WHEN rank = 'Rest' THEN 2
         ELSE 1 END,
    CAST(rank AS INTEGER);
