"""Independent checks for Mini #25 — Data Storytelling & Executive
Summary Pack.

Recomputes EVERY headline number from data/raw/*_SAMPLE.csv with
the standard library only (no pandas), re-implementing the SQL
mart in Python (net = qty x price x (1 - discount), cost from the
catalogue). Then it rebuilds the database from scratch, re-runs
all 10 .sql files, and compares their output row-for-row against
the shipped technique CSVs — including every sentence the SQL
builds, recomputed word-for-word in Python. It also compares
every number in outputs/summary.json, outputs/findings.md,
outputs/executive_summary_one_pager.md, the PDF and README.md,
and verifies the generator is deterministic and the build is
reproducible.

Run: python3 src/checks.py
Exit code 0 = all checks pass. Any failure is a build bug — fix the
build, never weaken the check.
"""

import csv
import hashlib
import json
import re
import sqlite3
import struct
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
SQL = ROOT / "sql"

PASSED = 0
FAILED = []


def check(name, ok, detail=""):
    global PASSED
    if ok:
        PASSED += 1
    else:
        FAILED.append(f"{name} :: {detail}")


def rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def sql_real(v):
    """Render a number the way SQLite prints a REAL in a CSV:
    shortest round-trip, no trailing '.0' artefacts beyond what
    SQLite itself writes (e.g. 52.18, 21.8, 100.0, -1.4)."""
    if isinstance(v, int):
        return str(v)
    if v == int(v):
        return f"{v:.1f}"
    return repr(round(v, 2))


def pct(part, whole):
    return round(part * 100.0 / whole, 2)


def fmt_ints(text):
    """Mirror of build.py's one-pager formatter: plain integers of
    4+ digits get thousands separators, except years 2000-2099."""
    def repl(m):
        n = int(m.group(0))
        return m.group(0) if 2000 <= n <= 2099 else f"{n:,}"
    return re.sub(r"\b\d{4,}\b", repl, text)


def main():
    products = rows(RAW / "products_SAMPLE.csv")
    customers = rows(RAW / "customers_SAMPLE.csv")
    orders = rows(RAW / "orders_SAMPLE.csv")
    items = rows(RAW / "order_items_SAMPLE.csv")

    # ================= raw files =================
    check("products_raw: 9 rows", len(products) == 9)
    check("products_raw: 4 categories",
          {r["category"] for r in products}
          == {"Electronics", "Furniture", "Kitchen", "Stationery"})
    check("products_raw: Stationery has exactly 1 product",
          sum(1 for r in products if r["category"] == "Stationery") == 1)
    check("products_raw: prices 1200-18000",
          min(int(r["unit_price_pkr"]) for r in products) == 1200
          and max(int(r["unit_price_pkr"]) for r in products) == 18000)
    check("products_raw: every cost below its price",
          all(int(r["unit_cost_pkr"]) < int(r["unit_price_pkr"])
              for r in products))
    check("customers_raw: 60 rows, 60 unique codes",
          len(customers) == 60
          and len({r["customer_code"] for r in customers}) == 60)
    check("orders_raw: 550 rows", len(orders) == 550, str(len(orders)))
    check("orders_raw: 550 unique ids",
          len({r["order_id"] for r in orders}) == 550)
    check("orders_raw: Jan-Jun 2026 only",
          min(r["order_date"] for r in orders) >= "2026-01-01"
          and max(r["order_date"] for r in orders) <= "2026-06-30")
    check("orders_raw: channels are Online/Phone/In-Store only",
          {r["channel"] for r in orders}
          == {"Online", "Phone", "In-Store"})
    check("orders_raw: discounts are 0/0.1/0.2/0.3 only",
          {float(r["discount_pct"]) for r in orders}
          == {0.0, 0.1, 0.2, 0.3})
    check("orders_raw: monthly counts 65/72/68/118/122/105",
          {m: sum(1 for r in orders if r["order_date"][:7] == m)
           for m in ("2026-01", "2026-02", "2026-03", "2026-04",
                     "2026-05", "2026-06")}
          == {"2026-01": 65, "2026-02": 72, "2026-03": 68,
              "2026-04": 118, "2026-05": 122, "2026-06": 105})
    check("items_raw: 1023 rows", len(items) == 1023, str(len(items)))
    check("items_raw: 1023 unique line ids",
          len({r["line_id"] for r in items}) == 1023)
    check("items_raw: every line belongs to a real order",
          {r["order_id"] for r in items}
          <= {r["order_id"] for r in orders})
    check("items_raw: quantities are 1-3",
          {int(r["quantity"]) for r in items} <= {1, 2, 3})
    check("items_raw: unit price always equals the catalogue price",
          all(int(r["unit_price_pkr"])
              == int({p["product_code"]: p for p in products}
                     [r["product_code"]]["unit_price_pkr"])
              for r in items))

    # ================= Python-side mart =================
    prod = {r["product_code"]: r for r in products}
    ords = {int(r["order_id"]): r for r in orders}
    lines = []
    for r in items:
        o = ords[int(r["order_id"])]
        p = prod[r["product_code"]]
        qty = int(r["quantity"])
        price = int(r["unit_price_pkr"])
        gross = qty * price
        net = int(round(gross * (1 - float(o["discount_pct"]))))
        cogs = qty * int(p["unit_cost_pkr"])
        lines.append({
            "line_id": int(r["line_id"]),
            "order_id": int(r["order_id"]),
            "product_code": r["product_code"],
            "product": p["name"], "category": p["category"],
            "channel": o["channel"],
            "month": o["order_date"][:7],
            "quarter": "Q1" if o["order_date"][:7] <= "2026-03"
                       else "Q2",
            "discount_pct": float(o["discount_pct"]),
            "quantity": qty, "gross": gross, "net": net, "cogs": cogs,
            "profit": net - cogs})
    check("mart: 1023 lines", len(lines) == 1023)
    check("mart: gross PKR 9,331,200",
          sum(l["gross"] for l in lines) == 9331200,
          str(sum(l["gross"] for l in lines)))
    check("mart: net PKR 8,558,310",
          sum(l["net"] for l in lines) == 8558310,
          str(sum(l["net"] for l in lines)))
    check("mart: discounts PKR 772,890",
          sum(l["gross"] - l["net"] for l in lines) == 772890)
    check("mart: profit PKR 2,870,810",
          sum(l["profit"] for l in lines) == 2870810)
    check("mart: 1523 units",
          sum(l["quantity"] for l in lines) == 1523)
    check("mart: every net is a whole rupee",
          all(l["net"] == round(l["gross"]
                                * (1 - l["discount_pct"]), 2)
              for l in lines))

    def agg(rows_):
        return {
            "orders": len({l["order_id"] for l in rows_}),
            "lines": len(rows_),
            "units": sum(l["quantity"] for l in rows_),
            "gross": sum(l["gross"] for l in rows_),
            "net": sum(l["net"] for l in rows_),
            "discount": sum(l["gross"] - l["net"] for l in rows_),
            "cogs": sum(l["cogs"] for l in rows_),
            "profit": sum(l["profit"] for l in rows_),
        }

    q1 = agg([l for l in lines if l["quarter"] == "Q1"])
    q2 = agg([l for l in lines if l["quarter"] == "Q2"])
    q1["margin"] = pct(q1["profit"], q1["net"])
    q2["margin"] = pct(q2["profit"], q2["net"])
    q1["aov"] = round(q1["net"] / q1["orders"], 2)
    q2["aov"] = round(q2["net"] / q2["orders"], 2)
    check("Q1: 205 orders, net 3393790, margin 38.14",
          (q1["orders"], q1["net"], q1["margin"])
          == (205, 3393790, 38.14), str(q1))
    check("Q2: 345 orders, net 5164520, margin 30.53",
          (q2["orders"], q2["net"], q2["margin"])
          == (345, 5164520, 30.53), str(q2))
    check("headline change +52.18%",
          pct(q2["net"] - q1["net"], q1["net"]) == 52.18)
    check("profit change +21.8%",
          pct(q2["profit"] - q1["profit"], q1["profit"]) == 21.8)
    check("margin fell 7.61 points",
          round(q2["margin"] - q1["margin"], 2) == -7.61)
    check("Q1 discount PKR 52,710 (1.53% of gross)",
          q1["discount"] == 52710
          and pct(q1["discount"], q1["gross"]) == 1.53)
    check("Q2 discount PKR 720,180 (12.24% of gross)",
          q2["discount"] == 720180
          and pct(q2["discount"], q2["gross"]) == 12.24)
    check("AOV Q1 16555.07 / Q2 14969.62",
          (q1["aov"], q2["aov"]) == (16555.07, 14969.62))

    monthly = {m: agg([l for l in lines if l["month"] == m])
               for m in sorted({l["month"] for l in lines})}
    for m in monthly:
        monthly[m]["margin"] = pct(monthly[m]["profit"],
                                    monthly[m]["net"])
    check("monthly net revenue",
          {m: v["net"] for m, v in monthly.items()}
          == {"2026-01": 991350, "2026-02": 1209670,
              "2026-03": 1192770, "2026-04": 1399860,
              "2026-05": 2020840, "2026-06": 1743820},
          str({m: v["net"] for m, v in monthly.items()}))
    check("monthly margins",
          {m: v["margin"] for m, v in monthly.items()}
          == {"2026-01": 38.59, "2026-02": 38.13,
              "2026-03": 37.77, "2026-04": 28.11,
              "2026-05": 26.86, "2026-06": 36.71})
    mom = {}
    prev = None
    for m in sorted(monthly):
        mom[m] = None if prev is None else pct(
            monthly[m]["net"] - monthly[prev]["net"],
            monthly[prev]["net"])
        prev = m
    check("month-on-month net change",
          mom == {"2026-01": None, "2026-02": 22.02,
                  "2026-03": -1.4, "2026-04": 17.36,
                  "2026-05": 44.36, "2026-06": -13.71}, str(mom))
    check("peak month is May (2020840)",
          max(monthly, key=lambda m: monthly[m]["net"]) == "2026-05")
    check("May is 23.61% of total net",
          pct(monthly["2026-05"]["net"],
              sum(l["net"] for l in lines)) == 23.61)
    check("Apr-May discount bill PKR 645,700",
          monthly["2026-04"]["discount"]
          + monthly["2026-05"]["discount"] == 645700)
    check("May discount PKR 384,160",
          monthly["2026-05"]["discount"] == 384160)

    cat_net = defaultdict(int)
    cat_lines = defaultdict(int)
    for l in lines:
        cat_net[l["category"]] += l["net"]
        cat_lines[l["category"]] += 1
    check("category net revenue",
          dict(cat_net) == {"Electronics": 3474800,
                            "Furniture": 3164160,
                            "Kitchen": 1678390,
                            "Stationery": 240960}, str(dict(cat_net)))
    check("category shares",
          {k: pct(v, 8558310) for k, v in cat_net.items()}
          == {"Electronics": 40.6, "Furniture": 36.97,
              "Kitchen": 19.61, "Stationery": 2.82})
    check("Stationery: 138 lines but 2.82% of revenue",
          cat_lines["Stationery"] == 138)
    chan_net = defaultdict(int)
    chan_orders = defaultdict(set)
    for l in lines:
        chan_net[l["channel"]] += l["net"]
        chan_orders[l["channel"]].add(l["order_id"])
    check("channel net revenue",
          dict(chan_net) == {"Online": 3520350, "Phone": 2627200,
                             "In-Store": 2410760}, str(dict(chan_net)))
    check("channel shares",
          {k: pct(v, 8558310) for k, v in chan_net.items()}
          == {"Online": 41.13, "Phone": 30.7, "In-Store": 28.17})
    check("channel orders Online 224 / Phone 164 / In-Store 162",
          {k: len(v) for k, v in chan_orders.items()}
          == {"Online": 224, "Phone": 164, "In-Store": 162})
    check("channel AOV: Phone 16019.51 / Online 15715.85 / "
          "In-Store 14881.23",
          {k: round(chan_net[k] / len(v), 2)
           for k, v in chan_orders.items()}
          == {"Online": 15715.85, "Phone": 16019.51,
              "In-Store": 14881.23})

    prod_net = defaultdict(int)
    prod_lines = defaultdict(int)
    for l in lines:
        prod_net[l["product"]] += l["net"]
        prod_lines[l["product"]] += 1
    top5 = sorted(prod_net.items(), key=lambda kv: -kv[1])[:5]
    check("top 5 products by net revenue",
          top5 == [("Office Chair", 2430000),
                   ("Mechanical Keyboard", 1556350),
                   ("Dinner Set 24pc", 1228150),
                   ("Desk Lamp", 734160),
                   ("Bluetooth Speaker", 699400)], str(top5))
    check("rest (4 products) PKR 1,910,250",
          sum(v for _, v in sorted(prod_net.items(),
                                   key=lambda kv: -kv[1])[5:])
          == 1910250)
    check("top 5 are 77.68% of net revenue",
          pct(sum(v for _, v in top5), 8558310) == 77.68)

    # AOV splits (technique 9, trap 3)
    disc_orders = {l["order_id"] for l in lines
                   if l["discount_pct"] > 0}
    full_orders = {l["order_id"] for l in lines
                   if l["discount_pct"] == 0}
    disc_net = sum(l["net"] for l in lines if l["discount_pct"] > 0)
    full_net = sum(l["net"] for l in lines if l["discount_pct"] == 0)
    check("discounted orders 220, full-price 330",
          (len(disc_orders), len(full_orders)) == (220, 330))
    check("AOV overall 15561 / discounted 13772 / full-price 16753",
          (round(8558310 / 550), round(disc_net / 220),
           round(full_net / 330)) == (15561, 13772, 16753))

    # Stationery by month (technique 9, trap 2)
    st_m = defaultdict(int)
    for l in lines:
        if l["category"] == "Stationery":
            st_m[l["month"]] += l["net"]
    check("Stationery monthly net",
          dict(st_m) == {"2026-01": 24480, "2026-02": 35880,
                         "2026-03": 24840, "2026-04": 45480,
                         "2026-05": 40800, "2026-06": 69480},
          str(dict(st_m)))
    check("Stationery biggest MoM rise is April +83.09% on PKR 24,840",
          pct(st_m["2026-04"] - st_m["2026-03"], st_m["2026-03"])
          == 83.09
          and st_m["2026-03"] == 24840)
    check("Stationery April rise is PKR 20,640 = 0.24% of total net",
          st_m["2026-04"] - st_m["2026-03"] == 20640
          and pct(20640, 8558310) == 0.24)

    # ================= fresh DB + re-run every query ==============
    db = ROOT / "data" / "demo.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript((ROOT / "data" / "schema.sql").read_text())
    for table, fname in [("products", "products_SAMPLE.csv"),
                         ("customers", "customers_SAMPLE.csv"),
                         ("orders", "orders_SAMPLE.csv"),
                         ("order_items", "order_items_SAMPLE.csv")]:
        with open(RAW / fname, newline="") as f:
            data = list(csv.reader(f))
        header, body = data[0], data[1:]
        con.executemany(
            f"INSERT INTO {table} VALUES "
            f"({','.join('?' * len(header))})", body)
    con.commit()
    check("DB: raw counts match CSVs",
          {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
           for t in ("products", "customers", "orders", "order_items")}
          == {"products": 9, "customers": 60, "orders": 550,
              "order_items": 1023})
    check("DB: foreign keys hold (no orphan lines)",
          con.execute(
              "SELECT COUNT(*) FROM order_items i LEFT JOIN orders o "
              "ON o.order_id = i.order_id WHERE o.order_id IS NULL"
          ).fetchone()[0] == 0)
    check("DB: every order belongs to a real customer",
          con.execute(
              "SELECT COUNT(*) FROM orders o LEFT JOIN customers c "
              "ON c.customer_code = o.customer_code "
              "WHERE c.customer_code IS NULL"
          ).fetchone()[0] == 0)

    slugs = [
        ("t01", "headline_number"),
        ("t02", "three_number_story"),
        ("t03", "before_after_framing"),
        ("t04", "ranking_with_cutoff"),
        ("t05", "honest_caveat"),
        ("t06", "one_chart_one_message"),
        ("t07", "recommendation_sentence"),
        ("t08", "executive_summary"),
        ("t09", "what_not_to_say"),
        ("t10", "sixty_second_brief"),
    ]
    results = {}
    for num, slug in slugs:
        path = SQL / f"{num}_{slug}.sql"
        check(f"sql file exists: {path.name}", path.exists())
        cur = con.execute(path.read_text())
        cols = [d[0] for d in cur.description]
        qrows = cur.fetchall()
        results[num] = (cols, qrows)
        shipped = rows(OUT / f"technique_{num[1:]}_{slug}.csv")
        shipped_t = [tuple(r[c] for c in cols) for r in shipped]
        fresh_t = [tuple("" if v is None else str(v) for v in r)
                   for r in qrows]
        check(f"{num}: shipped CSV matches a fresh query run",
              shipped_t == fresh_t,
              f"shipped {len(shipped_t)} rows, fresh {len(fresh_t)}")

    # ================= technique spot checks =================
    chg = sql_real(pct(q2["net"] - q1["net"], q1["net"]))
    pchg = sql_real(pct(q2["profit"] - q1["profit"], q1["profit"]))
    mdrop = sql_real(round(q1["margin"] - q2["margin"], 2))

    # t01 — headline number
    t01 = results["t01"][1][0]
    check("t01: 1 row", len(results["t01"][1]) == 1)
    check("t01: Q2 PKR 5164520 vs Q1 PKR 3393790, +52.18%",
          (t01[2], t01[4], t01[5]) == (5164520, 3393790, 52.18),
          str(t01))
    check("t01: headline sentence, word for word",
          t01[6] == f"Net revenue was PKR 5164520 in Q2 2026, up "
                     f"{chg}% on Q1 2026 (PKR 3393790).", t01[6])

    # t02 — 3-number story
    t02 = {r[0]: r for r in results["t02"][1]}
    check("t02: 3 rows in Context/Change/Consequence order",
          [r[0] for r in results["t02"][1]]
          == ["Context", "Change", "Consequence"])
    check("t02: Context sentence",
          t02["Context"][4] == "In Q1, before any promo, net revenue "
                               "was PKR 3393790.")
    check("t02: Change sentence",
          t02["Change"][4] == f"In Q2 net revenue rose to PKR 5164520, "
                              f"up {chg}% on Q1.")
    check("t02: Consequence sentence",
          t02["Consequence"][4]
          == f"Gross profit rose only {pchg}% to PKR 1576470 "
             f"(Q1: PKR 1294340) — the promo bought revenue, not "
             f"profit.")
    check("t02: consequence change (21.8%) is smaller than the "
          "headline change (52.18%)",
          t02["Consequence"][3] < t02["Change"][3])

    # t03 — before/after
    t03 = {r[0]: r for r in results["t03"][1]}
    check("t03: 2 rows Q1/Q2", len(results["t03"][1]) == 2)
    check("t03: Q1 row is the full P&L shape",
          t03["Q1"][1:] == (205, 375, 558, 3446500, 52710, 3393790,
                            1294340, 38.14, 16555.07,
                            "Baseline: Jan-Mar, no promo — same shop, "
                            "full prices."), str(t03["Q1"]))
    check("t03: Q2 row",
          t03["Q2"][1:10] == (345, 648, 965, 5884700, 720180, 5164520,
                              1576470, 30.53, 14969.62), str(t03["Q2"]))
    check("t03: baseline note says NOT like-for-like",
          "NOT like-for-like" in t03["Q2"][10])
    check("t03: AOV fell even as orders rose",
          t03["Q2"][9] < t03["Q1"][9]
          and t03["Q2"][1] > t03["Q1"][1])

    # t04 — ranking with cut-off
    t04 = results["t04"][1]
    check("t04: 7 rows in 1-5/Rest/TOTAL order",
          [r[0] for r in t04]
          == ["1", "2", "3", "4", "5", "Rest", "TOTAL"])
    check("t04: top 5 rows",
          [(r[1], r[4]) for r in t04[:5]]
          == [("Office Chair", 2430000),
              ("Mechanical Keyboard", 1556350),
              ("Dinner Set 24pc", 1228150),
              ("Desk Lamp", 734160),
              ("Bluetooth Speaker", 699400)])
    check("t04: Rest row is the other 4 products, PKR 1,910,250",
          t04[5][1:] == ("All other products (4)", "Mixed", 519,
                         1910250, 22.32), str(t04[5]))
    check("t04: TOTAL row reconciles (1023 lines, PKR 8,558,310)",
          t04[6][1:] == ("All products (9)", "Mixed", 1023, 8558310,
                         100.0), str(t04[6]))
    check("t04: shares sum to 100.00",
          round(sum(r[5] for r in t04[:6]), 2) == 100.0)
    check("t04: top 5 + rest = total",
          sum(r[4] for r in t04[:6]) == t04[6][4] == 8558310)

    # t05 — honest caveat
    t05 = {r[0]: r for r in results["t05"][1]}
    check("t05: discount share of gross 1.53% -> 12.24%",
          (t05["Q1"][3], t05["Q2"][3]) == (1.53, 12.24))
    check("t05: Q1 caveat sentence",
          t05["Q1"][8] == "Q1: margin was 38.14% on PKR 3393790 of "
                          "net revenue, with only PKR 52710 given "
                          "away in discounts.", t05["Q1"][8])
    check("t05: Q2 caveat sentence",
          t05["Q2"][8] == f"Q2: net revenue rose {chg}% to PKR "
                          f"5164520, but margin fell to 30.53% (from "
                          f"38.14%) — PKR 720180 of discounts bought "
                          f"that growth.", t05["Q2"][8])
    check("t05: the caveat is real (margin down, revenue up)",
          t05["Q2"][7] < t05["Q1"][7]
          and t05["Q2"][4] > t05["Q1"][4])

    # t06 — one chart, one message
    t06 = {r[0]: r for r in results["t06"][1]}
    check("t06: 6 rows, one per month", len(results["t06"][1]) == 6)
    check("t06: January has no MoM change (no Dec 2025 invented)",
          t06["2026-01"][6] is None)
    check("t06: May row (peak, +44.36%, margin 26.86)",
          t06["2026-05"][1:] == (122, 223, 2405000, 2020840, 26.86,
                                 44.36), str(t06["2026-05"]))
    check("t06: June fell 13.71% on May",
          t06["2026-06"][6] == -13.71)
    check("t06: monthly nets sum to PKR 8,558,310",
          sum(r[4] for r in results["t06"][1]) == 8558310)
    check("t06: monthly orders sum to 550",
          sum(r[1] for r in results["t06"][1]) == 550)

    # t07 — recommendation sentence
    t07 = {r[0]: r for r in results["t07"][1]}
    check("t07: 3 rows", len(results["t07"][1]) == 3)
    check("t07: R1 sentence",
          t07[1][6] == f"Q2 net revenue rose {chg}% but margin fell "
                       f"{mdrop} points to 30.53%, so repeat the promo "
                       f"only with a 35% margin floor and a 20% "
                       f"discount cap.", t07[1][6])
    check("t07: R1 supporting value is the 7.61 margin points lost",
          t07[1][4] == 7.61
          and t07[1][5] == "margin points lost in Q2 vs Q1")
    check("t07: R2 sentence",
          t07[2][6] == "Stationery is only 2.82% of net revenue, so "
                       "bundle the Notebook Set with the Wireless "
                       "Mouse, or review the range.", t07[2][6])
    check("t07: R3 sentence",
          t07[3][6] == "Online is 41.13% of net revenue, so put the "
                       "next ad spend behind Online first.",
          t07[3][6])
    check("t07: every recommendation names its action",
          all(("margin floor" in t07[1][3], "Bundle" in t07[2][3],
               "ad spend" in t07[3][3])))

    # t08 — executive summary
    t08 = results["t08"][1]
    check("t08: 6 rows — 1 headline, 3 findings, 1 rec, 1 risk",
          [(r[0], r[1]) for r in t08]
          == [("Headline", 1), ("Finding", 1), ("Finding", 2),
              ("Finding", 3), ("Recommendation", 1), ("Risk", 1)])
    check("t08: headline line",
          t08[0][2] == f"Noor Electronics made PKR 8558310 net "
                       f"revenue in Jan-Jun 2026; Q2 was PKR 5164520, "
                       f"up {chg}% on Q1 (PKR 3393790).", t08[0][2])
    check("t08: finding 1 (promo-bought growth)",
          t08[1][2] == "Growth was promo-bought: April-May discounts "
                       "of PKR 645700 drove the May peak of PKR "
                       "2020840, the biggest month of the half.")
    check("t08: finding 2 (margin vs profit)",
          t08[2][2] == f"Margin fell from 38.14% in Q1 to 30.53% in "
                       f"Q2 — profit grew only {pchg}% while revenue "
                       f"grew {chg}%.")
    check("t08: finding 3 (Online / Stationery)",
          t08[3][2] == "Online leads with 41.13% of net revenue; "
                       "Stationery is just 2.82% and needs a decision.")
    check("t08: recommendation line",
          t08[4][2] == "Repeat the promo only with a 35% margin floor "
                       "and a 20% discount cap, and put the next ad "
                       "spend behind Online.")
    check("t08: risk line",
          t08[5][2] == "If the promo repeats without a cap, margin "
                       "stays near 30% — and June already fell 13.71% "
                       "when the promo ended, so a quiet month costs "
                       "profit, not just revenue.")

    # t09 — what NOT to say
    t09 = {r[0]: r for r in results["t09"][1]}
    check("t09: 3 rows, one per trap",
          [r[1] for r in results["t09"][1]]
          == ["Cherry-picked month", "Percent without a base",
              "Average hiding a split"])
    check("t09: trap 1 claims May +44.36%",
          t09[1][2] == "Revenue jumped 44.36% in May — our best "
                       "month ever.")
    check("t09: trap 1 correction states the discount + margin cost",
          t09[1][4] == "Net revenue rose 44.36% in May to PKR "
                       "2020840, but that month carried PKR 384160 "
                       "of discounts and the lowest margin of the "
                       "half — the jump was bought, not earned.")
    check("t09: trap 1 why names April +17.36% and June -13.71%",
          "17.36%" in t09[1][3] and "13.71%" in t09[1][3]
          and "June fell 13.71%" in t09[1][3])
    check("t09: trap 2 claims April +83.09%",
          t09[2][2] == "Stationery revenue grew 83.09% in April!")
    check("t09: trap 2 why states the PKR 24,840 base and the "
          "PKR 20,640 move",
          t09[2][3] == "The base was PKR 24840 — the rise is PKR "
                       "20640, about 0.24% of total net revenue. A "
                       "big percent on a tiny base is a small number "
                       "in a loud voice.")
    check("t09: trap 2 correction",
          t09[2][4] == "Stationery rose from PKR 24840 in March to "
                       "PKR 45480 in April (+83.09%) — a PKR 20640 "
                       "move in a category worth 2.82% of revenue.")
    check("t09: trap 3 AOVs are whole rupees (15561/16753/13772)",
          t09[3][2] == "The average order is worth PKR 15561."
          and "PKR 13772" in t09[3][3]
          and "PKR 16753" in t09[3][3])
    check("t09: trap 3 correction",
          t09[3][4] == "Average order value is PKR 15561 overall, "
                       "but PKR 16753 at full price and PKR 13772 on "
                       "discounted orders; judge the promo on the "
                       "discounted figure.")
    check("t09: every corrected statement contains its numbers",
          all(any(ch.isdigit() for ch in t09[i][4]) for i in (1, 2, 3)))

    # t10 — 60-second brief
    t10 = results["t10"][1]
    check("t10: 8 lines in order",
          [r[0] for r in t10] == [1, 2, 3, 4, 5, 6, 7, 8])
    check("t10: sections are Opening/Numbers/Recommendation/Close",
          [r[1] for r in t10]
          == ["Opening", "Numbers", "Numbers", "Numbers", "Numbers",
              "Recommendation", "Recommendation", "Close"])
    script = " ".join(r[2] for r in t10)
    words = script.split()
    check("t10: 125 words (a minute at normal pace)",
          len(words) == 125, str(len(words)))
    check("t10: approx seconds sum to 57 (about a minute)",
          sum(r[3] for r in t10) == 57)
    check("t10: line 1 is the headline (PKR 8558310)",
          t10[0][2] == "Good morning. Six months, one shop, one "
                       "story: Noor Electronics made PKR 8558310 in "
                       "net revenue.")
    check("t10: line 4 states the June fall without a double negative",
          t10[3][2] == "May was the peak at PKR 2020840, then June "
                       "fell 13.71 percent when the promo ended."
          and "-13.71" not in t10[3][2])
    check("t10: line 6 is the recommendation (35% floor, 20% cap)",
          t10[5][2] == "So: repeat the promo only with a 35 percent "
                       "margin floor and a 20 percent discount cap.")
    check("t10: every line's numbers appear in the pack's aggregates",
          all(n in script for n in
              ("8558310", "5164520", "52.18", "645700", "38.14",
               "30.53", "2020840", "13.71", "41.13", "2.82")))
    check("t10: no line says a number the pack cannot prove",
          "2025" not in script and "last year" not in script.lower())

    # ================= reconciliation =================
    check("reconciliation: monthly sums = category sums = channel "
          "sums = total net",
          sum(v["net"] for v in monthly.values())
          == sum(cat_net.values()) == sum(chan_net.values())
          == 8558310)
    check("reconciliation: t03 + t05 + t06 agree on quarterly net",
          t03["Q1"][6] + t03["Q2"][6]
          == sum(r[4] for r in results["t06"][1]) == 8558310)
    check("reconciliation: t04 total = t06 total = t01 total",
          t04[6][4] == sum(r[4] for r in results["t06"][1])
          == t01[2] + t01[4] == 8558310)
    check("reconciliation: gross - discount = net, per quarter",
          q1["gross"] - q1["discount"] == q1["net"]
          and q2["gross"] - q2["discount"] == q2["net"])
    check("reconciliation: net - cogs = profit, per quarter",
          q1["net"] - q1["cogs"] == q1["profit"]
          and q2["net"] - q2["cogs"] == q2["profit"])

    # ================= summary.json =================
    summary = json.loads((OUT / "summary.json").read_text())
    exp = {
        "orders": 550, "lines": 1023, "customers": 60, "products": 9,
        "units": 1523, "gross_revenue_pkr": 9331200,
        "total_discount_pkr": 772890, "net_revenue_pkr": 8558310,
        "gross_profit_pkr": 2870810, "overall_margin_pct": 33.54,
        "q1_net_revenue_pkr": 3393790, "q2_net_revenue_pkr": 5164520,
        "headline_change_pct": 52.18, "q1_margin_pct": 38.14,
        "q2_margin_pct": 30.53, "margin_change_points": -7.61,
        "q1_gross_profit_pkr": 1294340,
        "q2_gross_profit_pkr": 1576470, "profit_change_pct": 21.8,
        "promo_discount_apr_may_pkr": 645700,
        "peak_month": "2026-05", "peak_month_net_pkr": 2020840,
        "top_product": "Office Chair",
        "top_product_net_pkr": 2430000,
        "rest_products_net_pkr": 1910250,
    }
    for k, v in exp.items():
        check(f"summary.json {k} == {v}", summary.get(k) == v,
              f"got {summary.get(k)}")
    check("summary.json monthly net revenue",
          summary.get("monthly_net_revenue_pkr")
          == {m: v["net"] for m, v in monthly.items()})
    check("summary.json monthly margins",
          summary.get("monthly_margin_pct")
          == {m: v["margin"] for m, v in monthly.items()})
    check("summary.json category revenue",
          summary.get("net_revenue_by_category_pkr") == dict(cat_net))
    check("summary.json channel revenue",
          summary.get("net_revenue_by_channel_pkr") == dict(chan_net))
    check("summary.json technique row counts",
          summary.get("technique_rows")
          == {"t01": 1, "t02": 3, "t03": 2, "t04": 7, "t05": 2,
              "t06": 6, "t07": 3, "t08": 6, "t09": 3, "t10": 8})
    check("summary.json headline sentence",
          summary.get("headline_sentence")
          == "Net revenue was PKR 5164520 in Q2 2026, up 52.18% on "
             "Q1 2026 (PKR 3393790).")
    check("summary.json takeaway sentence",
          summary.get("takeaway_sentence")
          == "Net revenue peaked in May at PKR 2,020,840 — but the "
             "Apr–May promo bought that growth with PKR 645,700 of "
             "discounts, so margin fell from 38.14% in Q1 to 30.53% "
             "in Q2.")
    check("summary.json takeaway uses formatted numbers (commas)",
          "2,020,840" in summary.get("takeaway_sentence", "")
          and "645,700" in summary.get("takeaway_sentence", ""))

    # ================= technique CSV headers =================
    exp_headers = {
        "t01": ["metric", "period", "value_pkr", "comparison_period",
                "comparison_value_pkr", "change_pct",
                "headline_sentence"],
        "t02": ["part", "label", "value_pkr", "change_pct", "sentence"],
        "t03": ["quarter", "orders", "lines", "units", "gross_pkr",
                "discount_pkr", "net_pkr", "gross_profit_pkr",
                "margin_pct", "avg_order_value_pkr", "baseline_note"],
        "t04": ["rank", "product_name", "category", "lines", "net_pkr",
                "share_pct"],
        "t05": ["quarter", "gross_pkr", "discount_pkr",
                "discount_share_pct", "net_pkr", "cogs_pkr",
                "gross_profit_pkr", "margin_pct", "caveat_sentence"],
        "t06": ["month", "orders", "lines", "gross_pkr", "net_pkr",
                "margin_pct", "mom_net_change_pct"],
        "t07": ["rec_no", "finding", "so_what", "recommendation",
                "supporting_value", "supporting_label",
                "recommendation_sentence"],
        "t08": ["section", "item_no", "line_text"],
        "t09": ["trap_no", "trap", "misleading_claim",
                "why_misleading", "corrected_statement"],
        "t10": ["seq", "section", "script_line", "approx_seconds"],
    }
    for num, slug in slugs:
        got = list(rows(OUT / f"technique_{num[1:]}_{slug}.csv")[0].keys())
        check(f"technique {num} CSV header", got == exp_headers[num],
              f"got {got}")

    # ================= findings.md / README.md / one-pager =====
    findings = (OUT / "findings.md").read_text()
    readme = (ROOT / "README.md").read_text()
    onepager = (OUT / "executive_summary_one_pager.md").read_text()
    needles = ["8,558,310", "5,164,520", "3,393,790", "52.18%",
               "38.14%", "30.53%", "7.61", "2,020,840", "645,700",
               "384,160", "41.13%", "2.82%", "240,960", "3,520,350",
               "15,561", "16,753", "13,772", "9,331,200", "772,890",
               "2,870,810", "33.54%", "1,023", "1,910,250", "6,648,060",
               "77.68%", "23.61%", "83.09%", "24,840", "20,640",
               "44.36%", "13.71%", "26.86%", "22.02%", "17.36%",
               "1.53%", "12.24%", "8.28%", "550", "125 words",
               "57 seconds"]
    for label, text in [("findings.md", findings),
                        ("README.md", readme)]:
        for needle in needles:
            check(f"{label} contains {needle!r}", needle in text)
        check(f"{label} never claims real client work",
              "real client" not in text.lower()
              or "never claimed as real client work" in text.lower())
        check(f"{label} carries the SAMPLE disclaimer",
              "SAMPLE" in text)
    for needle in ["8,558,310", "5,164,520", "52.18%", "645,700",
                   "2,020,840", "38.14%", "30.53%", "41.13%", "2.82%",
                   "13.71%", "9,331,200", "772,890", "2,870,810",
                   "550 orders", "1,023 order lines"]:
        check(f"one-pager.md contains {needle!r}", needle in onepager)
    check("one-pager.md has the fixed shape (Headline/Findings/"
          "Recommendation/Risk)",
          all(h in onepager for h in
              ("## Headline", "## Findings", "## Recommendation",
               "## Risk")))
    check("one-pager.md matches the technique-8 rows (formatted)",
          all(fmt_ints(line) in onepager
              for _, _, line in results["t08"][1]))
    check("README contains the demand signal (29–40% / 26%)",
          "29" in readme and "26%" in readme)
    check("README contains the '#1 final-round differentiator' line",
          "final-round differentiator" in readme)
    check("README states the dataset is ~20x the earlier minis",
          "20x" in readme)
    check("findings.md states the brief is 125 words",
          "125 words" in findings)
    check("findings.md names all three traps",
          all(t in findings for t in
              ("Cherry-picked month", "Percent without a base",
               "Average hiding a split")))

    # ================= chart PNG + PDF =================
    png = OUT / "technique_06_monthly_trend.png"
    check("chart PNG exists and is over 10 KB",
          png.exists() and png.stat().st_size > 10_000,
          str(png.stat().st_size if png.exists() else 0))
    if png.exists():
        data = png.read_bytes()
        check("chart PNG has a valid PNG signature",
              data[:8] == b"\x89PNG\r\n\x1a\n")
        w, h = struct.unpack(">II", data[16:24])
        check("chart PNG is at least 800x500 px",
              w >= 800 and h >= 500, f"{w}x{h}")
    pdf = OUT / "executive_summary_one_pager.pdf"
    check("one-pager PDF exists and is over 2 KB",
          pdf.exists() and pdf.stat().st_size > 2_000,
          str(pdf.stat().st_size if pdf.exists() else 0))
    if pdf.exists():
        data = pdf.read_bytes()
        check("one-pager PDF starts with %PDF",
              data[:5] == b"%PDF-")
        check("one-pager PDF ends with %%EOF",
              b"%%EOF" in data[-64:])
        check("one-pager PDF is exactly 1 page",
              len(re.findall(rb"/Type\s*/Page[^s]", data)) == 1,
              f"found {len(re.findall(rb'/Type\s*/Page[^s]', data))}")

    # ================= generator determinism =================
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "src" / "generate_data.py"),
             "--out-dir", str(td)],
            capture_output=True, text=True)
        check("generator re-runs cleanly", proc.returncode == 0,
              proc.stderr[-300:])
        if proc.returncode == 0:
            for src in sorted(RAW.glob("*.csv")):
                regen = td / src.name
                check(f"generator deterministic: {src.name}",
                      regen.exists()
                      and hashlib.sha256(src.read_bytes()).hexdigest()
                      == hashlib.sha256(regen.read_bytes()).hexdigest())

    # ================= build reproducibility =================
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.glob("technique_*.csv"))}
    before_sum = hashlib.sha256(
        (OUT / "summary.json").read_bytes()).hexdigest()
    before_one = hashlib.sha256(
        (OUT / "executive_summary_one_pager.md").read_bytes()
        ).hexdigest()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "src" / "build.py")],
        capture_output=True, text=True, cwd=str(ROOT))
    check("build.py re-runs cleanly", proc.returncode == 0,
          proc.stderr[-300:])
    if proc.returncode == 0:
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(OUT.glob("technique_*.csv"))}
        check("build is reproducible (technique CSVs stable)",
              after == before)
        check("build is reproducible (summary.json stable)",
              hashlib.sha256(
                  (OUT / "summary.json").read_bytes()).hexdigest()
              == before_sum)
        check("build is reproducible (one-pager md stable)",
              hashlib.sha256(
                  (OUT / "executive_summary_one_pager.md")
                  .read_bytes()).hexdigest() == before_one)
        check("build re-run still writes the chart + PDF",
              (OUT / "technique_06_monthly_trend.png").exists()
              and (OUT / "executive_summary_one_pager.pdf").exists())

    # ================= repo furniture =================
    check("requirements.txt names matplotlib + reportlab",
          "matplotlib" in (ROOT / "requirements.txt").read_text()
          and "reportlab" in (ROOT / "requirements.txt").read_text())
    check(".gitignore excludes *.db",
          "*.db" in (ROOT / ".gitignore").read_text())
    check("data/README.md exists", (ROOT / "data" / "README.md").exists())
    check("data/schema.sql exists", (ROOT / "data" / "schema.sql").exists())
    check("run_tests.py exists", (ROOT / "src" / "run_tests.py").exists())
    check("all 10 sql files exist",
          len(list(SQL.glob("t*.sql"))) == 10)
    check("all 10 technique CSVs exist",
          len(list(OUT.glob("technique_*.csv"))) == 10)
    check("no technique CSV is empty",
          all(p.stat().st_size > 0
              for p in OUT.glob("technique_*.csv")))
    check("findings.md exists and is substantial",
          (OUT / "findings.md").stat().st_size > 5_000)
    check("README.md exists and is substantial",
          (ROOT / "README.md").stat().st_size > 5_000)

    print(f"{PASSED} checks passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILURES:")
        for f in FAILED:
            print(" -", f)

    (OUT / "test_results.json").write_text(json.dumps({
        "checks_passed": PASSED,
        "checks_failed": len(FAILED),
        "failed": FAILED,
        "total": PASSED + len(FAILED),
    }, indent=2) + "\n")
    print(f"wrote outputs/test_results.json "
          f"({PASSED} passed, {len(FAILED)} failed)")
    con.close()
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
