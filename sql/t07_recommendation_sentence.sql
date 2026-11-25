-- t07 — The recommendation sentence: finding, so what, do this
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: "revenue is up" is not a recommendation, and neither
-- is "we should do something about margin". The recommendation
-- sentence has three fixed parts — FINDING (the number), SO WHAT
-- (why it matters), DO THIS (the action, with the number that
-- justifies it) — and a recommendation whose action cannot be
-- traced back to a number is an opinion, not analysis.
--
-- QUERY: three worked recommendations, each built from the same
-- quarter/category/channel aggregates as the earlier techniques.
-- The supporting_value column is the number that justifies the
-- action; the recommendation_sentence is the three parts joined
-- into the sentence a manager acts on.
--
-- RETURNS: 3 rows — promo margin floor, Stationery decision,
-- Online ad spend.
-- EXPECTED: R1 margin fell 7.61 points to 30.53% · R2 Stationery
-- 2.82% of net revenue · R3 Online 41.13% of net revenue
-- (PKR 3,520,350, 224 orders).

WITH mart AS (
    SELECT
        CASE WHEN CAST(strftime('%m', o.order_date) AS INTEGER) <= 3
             THEN 'Q1' ELSE 'Q2' END AS quarter,
        o.channel,
        p.category,
        o.order_id,
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
s AS (
    SELECT
        (SELECT margin_pct FROM q WHERE quarter = 'Q1') AS q1_margin,
        (SELECT margin_pct FROM q WHERE quarter = 'Q2') AS q2_margin,
        (SELECT net FROM q WHERE quarter = 'Q1') AS q1_net,
        (SELECT net FROM q WHERE quarter = 'Q2') AS q2_net,
        (SELECT ROUND(SUM(net_pkr) * 100.0
                      / (SELECT SUM(net_pkr) FROM mart), 2)
         FROM mart WHERE category = 'Stationery') AS st_share,
        (SELECT SUM(net_pkr) FROM mart
         WHERE category = 'Stationery') AS st_net,
        (SELECT ROUND(SUM(net_pkr) * 100.0
                      / (SELECT SUM(net_pkr) FROM mart), 2)
         FROM mart WHERE channel = 'Online') AS on_share,
        (SELECT SUM(net_pkr) FROM mart
         WHERE channel = 'Online') AS on_net,
        (SELECT COUNT(DISTINCT order_id) FROM mart
         WHERE channel = 'Online') AS on_orders
    FROM (SELECT 1)
)
SELECT
    1 AS rec_no,
    'Q2 net revenue rose '
        || ROUND((q2_net - q1_net) * 100.0 / q1_net, 2)
        || '% but margin fell from ' || q1_margin || '% to '
        || q2_margin || '%.' AS finding,
    'The promo bought volume at the cost of margin.' AS so_what,
    'Repeat the promo only with a 35% margin floor and a 20% '
        || 'discount cap.' AS recommendation,
    ROUND(q1_margin - q2_margin, 2) AS supporting_value,
    'margin points lost in Q2 vs Q1' AS supporting_label,
    'Q2 net revenue rose '
        || ROUND((q2_net - q1_net) * 100.0 / q1_net, 2)
        || '% but margin fell ' || ROUND(q1_margin - q2_margin, 2)
        || ' points to ' || q2_margin
        || '%, so repeat the promo only with a 35% margin floor '
        || 'and a 20% discount cap.' AS recommendation_sentence
FROM s
UNION ALL
SELECT
    2,
    'Stationery is ' || st_share || '% of net revenue (PKR '
        || st_net || ').',
    'One cheap product cannot carry a category.',
    'Bundle the Notebook Set with the Wireless Mouse, or review '
        || 'the range.',
    st_share,
    'Stationery share of net revenue (%)',
    'Stationery is only ' || st_share
        || '% of net revenue, so bundle the Notebook Set with the '
        || 'Wireless Mouse, or review the range.'
FROM s
UNION ALL
SELECT
    3,
    'Online is ' || on_share || '% of net revenue (PKR ' || on_net
        || ') and ' || on_orders || ' of 550 orders.',
    'The shop''s growth channel is already Online.',
    'Put the next ad spend behind Online first.',
    on_share,
    'Online share of net revenue (%)',
    'Online is ' || on_share
        || '% of net revenue, so put the next ad spend behind '
        || 'Online first.'
FROM s;
