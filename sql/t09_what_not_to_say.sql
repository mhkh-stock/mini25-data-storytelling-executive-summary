-- t09 — What NOT to say: three misleading framings, each corrected
-- (Data Storytelling Pack, Mini #25 — SAMPLE data only)
--
-- PROBLEM: the same data can be framed three dishonest ways
-- without inventing a single number. This technique names the
-- three framings every analyst meets — the cherry-picked month,
-- the percent without a base, the average that hides a split —
-- states each misleading claim exactly as a manager might hear
-- it, explains WHY it misleads, and gives the corrected
-- statement with the numbers that fix it. Every number in the
-- claims and the corrections is computed here, not typed in.
--
-- QUERY: monthly aggregates (net revenue, month-on-month change,
-- Stationery by month, average order value overall / discounted /
-- full-price) feed three rows, one per trap. The cherry-picked
-- month is the month with the largest month-on-month rise (May);
-- the small-base percent is Stationery's largest rise (April,
-- on a PKR 24,840 base); the split average contrasts discounted
-- and full-price orders.
--
-- RETURNS: 3 rows — one per trap.
-- EXPECTED: Trap 1 May +44.36% (PKR 2,020,840; PKR 384,160 of
-- discounts; margin 26.86%) · Trap 2 Stationery April +83.09%
-- on a PKR 24,840 base (a PKR 20,640 move) · Trap 3 overall AOV
-- PKR 15,561 vs PKR 16,753 full-price and PKR 13,772 discounted.

WITH mart AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS month,
        o.order_id,
        o.discount_pct,
        p.category,
        CAST(ROUND(i.quantity * i.unit_price_pkr
                   * (1.0 - o.discount_pct)) AS INTEGER) AS net_pkr,
        i.quantity * i.unit_price_pkr AS gross_pkr
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products AS p ON p.product_code = i.product_code
),
monthly AS (
    SELECT month, SUM(net_pkr) AS net,
           SUM(gross_pkr - net_pkr) AS discount
    FROM mart
    GROUP BY month
),
mom AS (
    SELECT
        m.month, m.net, m.discount,
        ROUND((m.net - prev.net) * 100.0 / prev.net, 2) AS mom_pct,
        prev.net AS prev_net
    FROM monthly AS m
    JOIN monthly AS prev
        ON prev.month = strftime('%Y-%m',
                                 date(m.month || '-01', '-1 month'))
),
stationery AS (
    SELECT month, SUM(net_pkr) AS net
    FROM mart
    WHERE category = 'Stationery'
    GROUP BY month
),
st_mom AS (
    SELECT
        s.month, s.net,
        ROUND((s.net - prev.net) * 100.0 / prev.net, 2) AS mom_pct,
        prev.net AS prev_net
    FROM stationery AS s
    JOIN stationery AS prev
        ON prev.month = strftime('%Y-%m',
                                 date(s.month || '-01', '-1 month'))
),
aov AS (
    SELECT
        CAST(ROUND(SUM(net_pkr) * 1.0 / COUNT(DISTINCT order_id), 0)
             AS INTEGER) AS overall,
        CAST(ROUND(SUM(CASE WHEN discount_pct > 0 THEN net_pkr END)
                   * 1.0
                   / COUNT(DISTINCT CASE WHEN discount_pct > 0
                                         THEN order_id END), 0)
             AS INTEGER) AS discounted,
        CAST(ROUND(SUM(CASE WHEN discount_pct = 0 THEN net_pkr END)
                   * 1.0
                   / COUNT(DISTINCT CASE WHEN discount_pct = 0
                                         THEN order_id END), 0)
             AS INTEGER) AS full_price
    FROM mart
),
s AS (
    SELECT
        (SELECT month FROM mom ORDER BY mom_pct DESC LIMIT 1)
            AS best_month,
        (SELECT mom_pct FROM mom ORDER BY mom_pct DESC LIMIT 1)
            AS best_mom,
        (SELECT net FROM mom ORDER BY mom_pct DESC LIMIT 1)
            AS best_net,
        (SELECT discount FROM mom ORDER BY mom_pct DESC LIMIT 1)
            AS best_discount,
        (SELECT mom_pct FROM mom WHERE month = '2026-04') AS apr_mom,
        (SELECT mom_pct FROM mom WHERE month = '2026-06') AS jun_mom,
        (SELECT month FROM st_mom ORDER BY mom_pct DESC LIMIT 1)
            AS st_month,
        (SELECT mom_pct FROM st_mom ORDER BY mom_pct DESC LIMIT 1)
            AS st_mom_pct,
        (SELECT prev_net FROM st_mom ORDER BY mom_pct DESC LIMIT 1)
            AS st_base,
        (SELECT net FROM st_mom ORDER BY mom_pct DESC LIMIT 1)
            AS st_net,
        (SELECT overall FROM aov) AS aov_overall,
        (SELECT discounted FROM aov) AS aov_discounted,
        (SELECT full_price FROM aov) AS aov_full,
        (SELECT ROUND(SUM(net_pkr) * 100.0
                      / (SELECT SUM(net_pkr) FROM mart), 2)
         FROM mart WHERE category = 'Stationery') AS st_share,
        (SELECT SUM(net_pkr) FROM mart) AS total_net
    FROM (SELECT 1)
)
SELECT
    1 AS trap_no,
    'Cherry-picked month' AS trap,
    'Revenue jumped ' || best_mom || '% in '
        || CASE best_month WHEN '2026-05' THEN 'May' END
        || ' — our best month ever.' AS misleading_claim,
    'May is the promo peak, picked because it is the biggest; '
        || 'April rose only ' || apr_mom || '% and June fell '
        || ABS(jun_mom) || '%. One month is not a trend.'
        AS why_misleading,
    'Net revenue rose ' || best_mom || '% in May to PKR ' || best_net
        || ', but that month carried PKR ' || best_discount
        || ' of discounts and the lowest margin of the half — '
        || 'the jump was bought, not earned.' AS corrected_statement
FROM s
UNION ALL
SELECT
    2,
    'Percent without a base',
    'Stationery revenue grew ' || st_mom_pct || '% in '
        || CASE st_month WHEN '2026-04' THEN 'April' END || '!',
    'The base was PKR ' || st_base || ' — the rise is PKR '
        || (st_net - st_base) || ', about '
        || ROUND((st_net - st_base) * 100.0 / total_net, 2)
        || '% of total net revenue. A big percent on a tiny base '
        || 'is a small number in a loud voice.',
    'Stationery rose from PKR ' || st_base || ' in March to PKR '
        || st_net || ' in April (+' || st_mom_pct
        || '%) — a PKR ' || (st_net - st_base)
        || ' move in a category worth ' || st_share
        || '% of revenue.'
FROM s
UNION ALL
SELECT
    3,
    'Average hiding a split',
    'The average order is worth PKR ' || aov_overall || '.',
    'Discounted orders average PKR ' || aov_discounted
        || ' and full-price orders PKR ' || aov_full
        || ' — the single average blends two different shops, '
        || 'and the promo is judged on the wrong one.',
    'Average order value is PKR ' || aov_overall
        || ' overall, but PKR ' || aov_full
        || ' at full price and PKR ' || aov_discounted
        || ' on discounted orders; judge the promo on the '
        || 'discounted figure.'
FROM s;
