# Mini #25 — data dictionary (SAMPLE / DEMO only)

Fictional store "Noor Electronics" — the same made-up Pakistani
electronics store as Mini #1 / #3 / #15 / #22 / #23 / #24,
Jan–Jun 2026. The store, the sales and every number are invented
for teaching — the storytelling techniques are real, the business
is not. Regenerate exactly with `python3 src/generate_data.py`
(deterministic seed 20261125, no randomness at run time). Build
the database and run all 10 techniques with `python3 src/build.py`.

## Why this dataset is bigger

The earlier minis run on 32 orders / 52 lines / PKR 346,800.
That is enough to learn a SQL function, but not enough to learn
storytelling: a ranking of 9 products on 52 lines, a margin
caveat on 2 discounted orders, a "misleading average" on 32
orders — none of them would mean anything. This pack scales the
same shop up to 550 orders / 1,023 lines, with the same 9
products at the same catalogue prices and the same per-line
economics (average order value PKR 15,561 vs PKR 10,838 in the
small base — same ballpark, same shop). The totals are ~20x
Mini #23's only because the dataset is ~20x larger, and this
file says so plainly instead of letting the totals look
incomparable.

## The planted story (discoverable by query, never asserted)

| Story thread | Planted how | Where to see it |
|---|---|---|
| Discount-driven volume spike | Apr–May 2026 "Eid sale": most orders 20–30% off; order volume roughly doubles | t03, t05, t06 — Q2 orders 345 vs Q1 205 |
| Revenue up, margin down | The promo discount bill (PKR 720,180 in Q2 vs PKR 52,710 in Q1) eats the margin | t05 — margin 38.14% → 30.53% |
| One weak category | Stationery has a single product (Notebook Set, PKR 1,200) | t04, t07 — 2.82% of net revenue |
| One strong channel | Online weighted 40% of orders | t07, t08 — 41.13% of net revenue |

## data/raw/products_SAMPLE.csv (9 rows)

| Column | Meaning |
|---|---|
| `product_code` | Product key, PRD-01 – PRD-09 |
| `name` | Product name |
| `category` | Electronics (4 products) / Furniture (2) / Kitchen (2) / Stationery (1) |
| `unit_price_pkr` | Catalogue price charged (PKR 1,200 – 18,000) |
| `unit_cost_pkr` | What the shop paid — the margin input (PKR 650 – 11,500) |

## data/raw/customers_SAMPLE.csv (60 rows)

| Column | Meaning |
|---|---|
| `customer_code` | Customer key, CUST-001 – CUST-060 |
| `name` | Fictional customer name |
| `city` | One of 12 Pakistani cities |

## data/raw/orders_SAMPLE.csv (550 rows)

| Column | Meaning |
|---|---|
| `order_id` | Order number, 1–550, in date order |
| `customer_code` | Buyer — CUST-001 – CUST-060 |
| `order_date` | ISO date, 2026-01-01 – 2026-06-30 |
| `channel` | Online / Phone / In-Store (Online weighted 40%) |
| `discount_pct` | Order-level promo discount: 0.00, 0.10, 0.20 or 0.30 |

Orders per month: Jan 65 · Feb 72 · Mar 68 · Apr 118 · May 122 ·
Jun 105. Discount menu: Jan–Mar mostly full price (15% of
orders 10% off); Apr–May promo (35% full price, 40% at 20% off,
25% at 30% off); Jun mostly full price again (20% at 10% off,
10% at 20% off).

## data/raw/order_items_SAMPLE.csv (1,023 rows)

| Column | Meaning |
|---|---|
| `line_id` | Order-line number, 1–1,023 |
| `order_id` | Order the line belongs to (1–3 lines per order) |
| `product_code` | Product — PRD-01 – PRD-09 |
| `quantity` | Units on the line, 1–3 |
| `unit_price_pkr` | Price charged — always the catalogue price |

Line revenue: gross = `quantity × unit_price_pkr`; net =
`gross × (1 − discount_pct)` where the discount comes from the
line's order; cost = `quantity × unit_cost_pkr`; profit =
`net − cost`. Net revenue is always a whole rupee: every price
is a multiple of PKR 100 and every discount is 0/10/20/30%.

## data/schema.sql

Clean, typed schema with real primary/foreign keys — products,
customers, orders, order_items. `data/demo.db` is built from it
by `src/build.py` and is rebuildable at any time; it is not
uploaded to GitHub.

## Totals (verified)

- 550 orders, 1,023 lines, 1,523 units, 60 customers, 9 products.
- Gross revenue PKR 9,331,200; discounts PKR 772,890 (8.28% of
  gross); net revenue PKR 8,558,310; cost of goods
  PKR 5,687,500; gross profit PKR 2,870,810; margin 33.54%.
- Q1: 205 orders, net PKR 3,393,790, margin 38.14%.
  Q2: 345 orders, net PKR 5,164,520 (+52.18%), margin 30.53%.
- Monthly net: Jan 991,350 · Feb 1,209,670 · Mar 1,192,770 ·
  Apr 1,399,860 · May 2,020,840 · Jun 1,743,820.
- Net by category: Electronics PKR 3,474,800 (40.60%) ·
  Furniture PKR 3,164,160 (36.97%) · Kitchen PKR 1,678,390
  (19.61%) · Stationery PKR 240,960 (2.82%).
- Net by channel: Online PKR 3,520,350 (41.13%, 224 orders) ·
  Phone PKR 2,627,200 (30.70%, 164) · In-Store PKR 2,410,760
  (28.17%, 162).

## Known quirks

- **SAMPLE data only.** The store, the sales and the "findings"
  are invented to teach the techniques.
- **The story is planted, not found.** Real business stories are
  messier — the promo effect, the weak category and the strong
  channel would overlap and need untangling. This pack plants
  each thread cleanly so the technique, not the untangling, is
  what gets practised.
- **One shop, six months, no prior year.** There is no 2025 to
  compare with, so every comparison in the pack is Q2 vs Q1 or
  month vs month — the pack never invents a prior-year baseline.
- **The discount lives on the order, not the line.** A real shop
  discounts some lines and not others; here the whole order
  shares one discount, which is what makes the margin arithmetic
  clean enough to check by hand.
