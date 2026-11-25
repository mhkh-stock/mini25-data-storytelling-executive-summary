"""Regenerate the SAMPLE data for Mini #25 — Data Storytelling &
Executive Summary Pack.

Writes the CLEAN, typed dataset for the fictional "Noor Electronics"
shop — the same shop, products and prices as Mini #1 / #3 / #15 /
#22 / #23 / #24, but at a storytelling scale: ~550 orders and
~1,000 order lines, Jan–Jun 2026 (the earlier minis' 32 orders /
52 lines are too small for rankings, splits and caveats to mean
anything). Same 9 products, same catalogue prices, same per-line
economics — the total is ~20x Mini #23's PKR 346,800 only because
the dataset is ~20x larger, and the README says so plainly.

Planted story material (all discoverable from the data by query,
never asserted without one):

- A discount-driven volume spike: Apr–May 2026 runs an "Eid sale"
  promo (most orders 20–30% off). Order volume jumps, gross
  revenue jumps — but the discount bill eats the margin, so Q2
  net revenue is up while gross margin is DOWN on Q1.
- One weak category: Stationery has a single product (Notebook
  Set, PKR 1,200), so its revenue share is a small single digit.
- One strong channel: Online is the largest channel by net
  revenue and by orders.

Everything is deterministic: random.Random(20261125). Re-running
produces byte-identical files. No network.

Run: python3 src/generate_data.py [--out-dir DIR]
"""

import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

SEED = 20261125

# ------------------------------------------------------------------
# products: (product_code, name, category, unit_price_pkr,
#            unit_cost_pkr). Same catalogue as Minis #1/#23/#24,
#            plus a unit cost so margin can be computed honestly.
# ------------------------------------------------------------------
PRODUCTS = [
    ("PRD-01", "Wireless Mouse", "Electronics", 2500, 1400),
    ("PRD-02", "Mechanical Keyboard", "Electronics", 8500, 5200),
    ("PRD-03", "Laptop Stand", "Electronics", 4500, 2700),
    ("PRD-04", "Office Chair", "Furniture", 18000, 11500),
    ("PRD-05", "Desk Lamp", "Furniture", 4200, 2400),
    ("PRD-06", "Notebook Set", "Stationery", 1200, 650),
    ("PRD-07", "Ceramic Mug Set", "Kitchen", 3200, 1800),
    ("PRD-08", "Dinner Set 24pc", "Kitchen", 14500, 9200),
    ("PRD-09", "Bluetooth Speaker", "Electronics", 6500, 3900),
]

# Sales weights per product (must sum to 1.0). Stationery's only
# product sells often but cheaply, so it stays the weak category.
PRODUCT_WEIGHTS = [0.16, 0.12, 0.11, 0.08, 0.12, 0.14, 0.11, 0.07, 0.09]

# ------------------------------------------------------------------
# customers: 60 fictional customers across 12 Pakistani cities.
# ------------------------------------------------------------------
CUSTOMER_NAMES = [
    ("Ayesha Khan", "Lahore"), ("Bilal Ahmed", "Karachi"),
    ("Fatima Noor", "Islamabad"), ("Hassan Raza", "Rawalpindi"),
    ("Zainab Ali", "Lahore"), ("Usman Tariq", "Peshawar"),
    ("Maryam Siddiqui", "Lahore"), ("Ali Nawaz", "Multan"),
    ("Sara Malik", "Faisalabad"), ("Omar Farooq", "Karachi"),
    ("Hina Shah", "Quetta"), ("Danish Iqbal", "Hyderabad"),
    ("Sana Mirza", "Lahore"), ("Ahmed Raza", "Sialkot"),
    ("Nadia Hussain", "Karachi"), ("Fahad Iqbal", "Gujranwala"),
    ("Rabia Anwar", "Islamabad"), ("Kashif Mehmood", "Rawalpindi"),
    ("Amna Saleem", "Faisalabad"), ("Tariq Aziz", "Multan"),
    ("Mahnoor Asif", "Lahore"), ("Zeeshan Haider", "Karachi"),
    ("Iqra Batool", "Bahawalpur"), ("Shahid Khan", "Peshawar"),
    ("Sadia Parveen", "Hyderabad"), ("Noman Akhtar", "Sialkot"),
    ("Amina Yousuf", "Islamabad"), ("Waqas Ahmad", "Gujranwala"),
    ("Hira Fatima", "Lahore"), ("Salman Butt", "Rawalpindi"),
    ("Kiran Shahid", "Karachi"), ("Adnan Javed", "Multan"),
    ("Farah Naz", "Quetta"), ("Imran Sheikh", "Faisalabad"),
    ("Bushra Bibi", "Bahawalpur"), ("Arslan Ghani", "Lahore"),
    ("Mehwish Rani", "Hyderabad"), ("Junaid Alam", "Karachi"),
    ("Shazia Kousar", "Sialkot"), ("Rashid Minhas", "Islamabad"),
    ("Saima Khalid", "Gujranwala"), ("Asadullah Khan", "Peshawar"),
    ("Noreen Akhtar", "Rawalpindi"), ("Mudassir Ali", "Multan"),
    ("Areeba Siddiqui", "Lahore"), ("Hamza Yousaf", "Karachi"),
    ("Laiba Anwar", "Faisalabad"), ("Saqlain Abbas", "Sialkot"),
    ("Sumbal Riaz", "Islamabad"), ("Faisal Mehmood", "Gujranwala"),
    ("Tehreem Zahra", "Lahore"), ("Umair Siddique", "Hyderabad"),
    ("Anam Rafiq", "Karachi"), ("Sheraz Ahmed", "Bahawalpur"),
    ("Gulnaz Begum", "Quetta"), ("Waleed Hassan", "Rawalpindi"),
    ("Sidra Amin", "Multan"), ("Bilawal Bhutto", "Larkana"),
    ("Tooba Aslam", "Lahore"), ("Huzaifa Tariq", "Karachi"),
]

# Orders per month: the Apr–May promo doubles volume.
ORDERS_PER_MONTH = {
    "2026-01": 65, "2026-02": 72, "2026-03": 68,
    "2026-04": 118, "2026-05": 122, "2026-06": 105,
}
DAYS_IN_MONTH = {"2026-01": 31, "2026-02": 28, "2026-03": 31,
                 "2026-04": 30, "2026-05": 31, "2026-06": 30}

CHANNELS = ["Online", "Phone", "In-Store"]
CHANNEL_WEIGHTS = [0.40, 0.32, 0.28]  # Online is the strong channel.

# Discount menu per period: (discount, weight). Apr–May is the promo.
DISCOUNT_MENU = {
    "Q1": [(0.00, 0.85), (0.10, 0.15)],
    "PROMO": [(0.00, 0.35), (0.20, 0.40), (0.30, 0.25)],
    "JUN": [(0.00, 0.70), (0.10, 0.20), (0.20, 0.10)],
}

LINES_PER_ORDER = [1, 2, 3]
LINES_WEIGHTS = [0.35, 0.45, 0.20]
QUANTITIES = [1, 2, 3]
QUANTITY_WEIGHTS = [0.60, 0.30, 0.10]


def pick(rng, values, weights):
    return rng.choices(values, weights=weights, k=1)[0]


def discount_for(rng, month):
    if month in ("2026-01", "2026-02", "2026-03"):
        menu = DISCOUNT_MENU["Q1"]
    elif month in ("2026-04", "2026-05"):
        menu = DISCOUNT_MENU["PROMO"]
    else:
        menu = DISCOUNT_MENU["JUN"]
    return pick(rng, [d for d, _ in menu], [w for _, w in menu])


def main(out_dir=None):
    out = Path(out_dir) if out_dir else RAW
    rng = random.Random(SEED)

    customers = [
        (f"CUST-{i + 1:03d}", name, city)
        for i, (name, city) in enumerate(CUSTOMER_NAMES)
    ]
    products = PRODUCTS

    # --- orders: random day in month, then sorted by date so the
    # order ids run in date order (readable, like a real extract).
    raw_orders = []
    for month, count in ORDERS_PER_MONTH.items():
        for _ in range(count):
            day = rng.randint(1, DAYS_IN_MONTH[month])
            raw_orders.append({
                "customer_code": f"CUST-{rng.randint(1, 60):03d}",
                "order_date": f"{month}-{day:02d}",
                "channel": pick(rng, CHANNELS, CHANNEL_WEIGHTS),
                "discount_pct": discount_for(rng, month),
            })
    raw_orders.sort(key=lambda o: o["order_date"])
    orders = []
    for i, o in enumerate(raw_orders, start=1):
        orders.append((i, o["customer_code"], o["order_date"],
                       o["channel"], o["discount_pct"]))

    # --- order lines: 1–3 lines per order, weighted products.
    items = []
    line_id = 0
    for order_id, _, _, _, _ in orders:
        for _ in range(pick(rng, LINES_PER_ORDER, LINES_WEIGHTS)):
            line_id += 1
            prod = pick(rng, products, PRODUCT_WEIGHTS)
            qty = pick(rng, QUANTITIES, QUANTITY_WEIGHTS)
            items.append((line_id, order_id, prod[0], qty, prod[3]))

    def write_csv(path, header, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    write_csv(out / "products_SAMPLE.csv",
              ["product_code", "name", "category", "unit_price_pkr",
               "unit_cost_pkr"], products)
    write_csv(out / "customers_SAMPLE.csv",
              ["customer_code", "name", "city"], customers)
    write_csv(out / "orders_SAMPLE.csv",
              ["order_id", "customer_code", "order_date", "channel",
               "discount_pct"], orders)
    write_csv(out / "order_items_SAMPLE.csv",
              ["line_id", "order_id", "product_code", "quantity",
               "unit_price_pkr"], items)

    gross = sum(q * p for _, _, _, q, p in items)
    print(f"wrote 4 files to {out}")
    print(f"customers={len(customers)} products={len(products)} "
          f"orders={len(orders)} lines={len(items)} "
          f"gross_revenue=PKR {gross:,}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=None)
    main(ap.parse_args().out_dir)
