-- Mini #25 — Data Storytelling & Executive Summary Pack
-- SAMPLE / DEMO data only. Fictional shop Noor Electronics, fictional
-- people, fictional sales. Never claimed as real client or real
-- business data.
-- Clean, typed schema (unlike Mini #24's messy bronze): the story
-- is in the numbers, not in the formatting. Four tables, real
-- primary/foreign keys. SQLite 3.8.3+. Run: python3 src/build.py
-- (or: sqlite3 data/demo.db < data/schema.sql, then load the CSVs)

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;

-- 9 rows. Same catalogue as Mini #1 / #23 / #24, plus unit_cost_pkr
-- so gross margin can be computed honestly (technique 5).
CREATE TABLE products (
    product_code   TEXT    PRIMARY KEY,  -- PRD-01 .. PRD-09
    name           TEXT    NOT NULL,
    category       TEXT    NOT NULL,     -- Electronics / Furniture /
                                          -- Kitchen / Stationery
    unit_price_pkr INTEGER NOT NULL,     -- catalogue price
    unit_cost_pkr  INTEGER NOT NULL      -- what the shop paid
);

-- 60 rows. Fictional customers across 12 Pakistani cities.
CREATE TABLE customers (
    customer_code TEXT PRIMARY KEY,  -- CUST-001 .. CUST-060
    name          TEXT NOT NULL,
    city          TEXT NOT NULL
);

-- 550 rows, Jan–Jun 2026. discount_pct is the order-level promo
-- discount: 0.00, 0.10, 0.20 or 0.30. Apr–May 2026 is the "Eid
-- sale" promo: most orders 20–30% off (the planted story).
CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,  -- 1 .. 550, in date order
    customer_code TEXT    NOT NULL REFERENCES customers (customer_code),
    order_date    TEXT    NOT NULL,     -- ISO date, 2026-01-01 .. 2026-06-30
    channel       TEXT    NOT NULL,     -- Online / Phone / In-Store
    discount_pct  REAL    NOT NULL      -- 0.00 – 0.30
);

-- ~1,023 rows. unit_price_pkr is the price charged (the catalogue
-- price for that product); the discount lives on the order, so a
-- line's net revenue is quantity * unit_price * (1 - discount_pct).
CREATE TABLE order_items (
    line_id       INTEGER PRIMARY KEY,  -- 1 .. ~1,023
    order_id      INTEGER NOT NULL REFERENCES orders (order_id),
    product_code  TEXT    NOT NULL REFERENCES products (product_code),
    quantity      INTEGER NOT NULL,     -- 1 – 3
    unit_price_pkr INTEGER NOT NULL
);
