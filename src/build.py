"""Build Mini #25 — Data Storytelling & Executive Summary Pack.

1. Rebuilds data/demo.db from scratch: runs data/schema.sql, then
   loads the 4 SAMPLE CSVs verbatim.
2. Runs sql/t01..t10 in order against the fresh DB.
3. Writes one CSV per technique to outputs/technique_NN_<slug>.csv
   (the expected output of each .sql file), outputs/summary.json
   (every headline number, machine-readable), the technique-6
   chart (outputs/technique_06_monthly_trend.png, matplotlib),
   and the one-page executive summary rendered from the
   technique-8 rows (outputs/executive_summary_one_pager.md and
   .pdf via reportlab).

Run: python3 src/build.py
The .db is rebuildable from the pushed scripts and is NOT uploaded
to GitHub (see .gitignore).
"""

import csv
import json
import re
import sqlite3
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SQL = ROOT / "sql"
OUT = ROOT / "outputs"

TECHNIQUES = [
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

LOAD = [
    ("products", "products_SAMPLE.csv"),
    ("customers", "customers_SAMPLE.csv"),
    ("orders", "orders_SAMPLE.csv"),
    ("order_items", "order_items_SAMPLE.csv"),
]


def fmt(n):
    """PKR 8,558,310 — thousands separators for prose."""
    return f"{int(round(n)):,}"


def fmt_ints(text):
    """Format the plain integers SQL writes (PKR 5164520) with
    thousands separators for the manager-facing one-pager, leaving
    years (2026), percents (52.18) and small numbers alone."""
    def repl(m):
        n = int(m.group(0))
        return m.group(0) if 2000 <= n <= 2099 else f"{n:,}"
    return re.sub(r"\b\d{4,}\b", repl, text)


def build_db():
    db = DATA / "demo.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript((DATA / "schema.sql").read_text())
    for table, fname in LOAD:
        with open(DATA / "raw" / fname, newline="") as f:
            rows = list(csv.reader(f))
        header, data = rows[0], rows[1:]
        con.executemany(
            f"INSERT INTO {table} VALUES ({','.join('?' * len(header))})",
            data)
    con.commit()
    return con


def build_chart(t06_rows, takeaway):
    """Monthly net revenue bars + margin line; the takeaway sentence
    is the chart title — one chart, one message (technique 6)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    months = [r[0] for r in t06_rows]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    net = [r[4] for r in t06_rows]
    margin = [r[5] for r in t06_rows]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    bars = ax.bar(labels, net, color="#1f6f4a", edgecolor="white")
    for b, v in zip(bars, net):
        ax.text(b.get_x() + b.get_width() / 2, v + 40000,
                fmt(v), ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Net revenue (PKR)")
    ax.set_ylim(0, max(net) * 1.18)
    ax.set_title("\n".join(textwrap.wrap(takeaway, 72)),
                 fontsize=11, pad=14)
    ax2 = ax.twinx()
    ax2.plot(labels, margin, color="#c0392b", marker="o",
             linewidth=2, label="Gross margin %")
    ax2.set_ylabel("Gross margin (%)", color="#c0392b")
    ax2.set_ylim(20, 45)
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax2.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    path = OUT / "technique_06_monthly_trend.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"wrote {path.name}")
    return path


def build_one_pager(t08_rows, summary):
    """Render the technique-8 rows into the one-page summary
    (Markdown + PDF). The prose is the SQL output; this only
    formats it, so the page cannot disagree with the pack."""
    by_section = {}
    for section, _, line in t08_rows:
        by_section.setdefault(section, []).append(line)
    # The SQL writes plain integers (checkable); the one-pager is
    # manager-facing, so format them here — same lines, commas added.
    headline = fmt_ints(by_section["Headline"][0])
    findings = [fmt_ints(f) for f in by_section["Finding"]]
    recommendation = fmt_ints(by_section["Recommendation"][0])
    risk = fmt_ints(by_section["Risk"][0])

    md = f"""# Executive Summary — Noor Electronics, Jan–Jun 2026

**SAMPLE / DEMO data only.** Fictional shop, fictional sales.
Never claimed as real client or real business data.

## Headline

{headline}

## Findings

"""
    for i, f in enumerate(findings, start=1):
        md += f"{i}. {f}\n"
    md += f"""
## Recommendation

{recommendation}

## Risk

{risk}

---

*Basis: {fmt(summary["orders"])} orders, {fmt(summary["lines"])} order lines, """
    md += (f"""{fmt(summary["units"])} units, Jan–Jun 2026. Gross revenue PKR """
           f"""{fmt(summary["gross_revenue_pkr"])}; discounts PKR """
           f"""{fmt(summary["total_discount_pkr"])}; net revenue PKR """
           f"""{fmt(summary["net_revenue_pkr"])}; gross profit PKR """
           f"""{fmt(summary["gross_profit_pkr"])}. Every number recomputed """
           f"""from data/raw/*_SAMPLE.csv by src/checks.py. """
           f"""Full pack: Mini #25 — Data Storytelling & Executive Summary Pack.*
""")
    (OUT / "executive_summary_one_pager.md").write_text(md)
    print("wrote outputs/executive_summary_one_pager.md")

    # ---- PDF (reportlab) ----
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                    Spacer)

    styles = {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold",
                                fontSize=17, leading=21, spaceAfter=4),
        "sub": ParagraphStyle("sub", fontName="Helvetica-Oblique",
                              fontSize=9, leading=12, spaceAfter=10),
        "h": ParagraphStyle("h", fontName="Helvetica-Bold",
                            fontSize=12, leading=15, spaceBefore=10,
                            spaceAfter=4),
        "body": ParagraphStyle("body", fontName="Helvetica",
                               fontSize=10.5, leading=15, spaceAfter=4),
        "foot": ParagraphStyle("foot", fontName="Helvetica-Oblique",
                               fontSize=8, leading=11, spaceBefore=10),
    }
    doc = SimpleDocTemplate(
        str(OUT / "executive_summary_one_pager.pdf"), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Executive Summary — Noor Electronics, Jan–Jun 2026",
        author="Mini #25 — Data Storytelling & Executive Summary Pack")
    story = [
        Paragraph("Executive Summary — Noor Electronics",
                  styles["title"]),
        Paragraph("Jan–Jun 2026 &nbsp;·&nbsp; SAMPLE / DEMO data only — "
                  "fictional shop, fictional sales, never claimed as "
                  "real client or real business data.", styles["sub"]),
        Paragraph("Headline", styles["h"]),
        Paragraph(headline, styles["body"]),
        Paragraph("Findings", styles["h"]),
    ]
    for i, f in enumerate(findings, start=1):
        story.append(Paragraph(f"{i}. {f}", styles["body"]))
    story += [
        Paragraph("Recommendation", styles["h"]),
        Paragraph(recommendation, styles["body"]),
        Paragraph("Risk", styles["h"]),
        Paragraph(risk, styles["body"]),
        Paragraph(
            f"Basis: {fmt(summary['orders'])} orders, "
            f"{fmt(summary['lines'])} "
            f"order lines, {fmt(summary['units'])} units, Jan–Jun 2026. "
            f"Gross revenue PKR {fmt(summary['gross_revenue_pkr'])}; "
            f"discounts PKR {fmt(summary['total_discount_pkr'])}; net "
            f"revenue PKR {fmt(summary['net_revenue_pkr'])}; gross "
            f"profit PKR {fmt(summary['gross_profit_pkr'])}. Every "
            f"number recomputed from data/raw/*_SAMPLE.csv by "
            f"src/checks.py. Full pack: Mini #25 — Data Storytelling "
            f"&amp; Executive Summary Pack.", styles["foot"]),
    ]
    doc.build(story)
    print("wrote outputs/executive_summary_one_pager.pdf")


def main():
    OUT.mkdir(exist_ok=True)
    con = build_db()

    raw_counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t, _ in LOAD}
    print("raw rows:", raw_counts)

    results = {}
    for num, slug in TECHNIQUES:
        path = SQL / f"{num}_{slug}.sql"
        cur = con.execute(path.read_text())
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        results[num] = (cols, rows)
        out_path = OUT / f"technique_{num[1:]}_{slug}.csv"
        with open(out_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        print(f"ran {path.name}: {len(rows)} rows -> {out_path.name}")

    # ---- headline numbers, all derived from the query results ----
    t01 = results["t01"][1][0]
    t02 = {r[0]: r for r in results["t02"][1]}
    t03 = {r[0]: r for r in results["t03"][1]}
    t04 = results["t04"][1]
    t05 = {r[0]: r for r in results["t05"][1]}
    t06 = results["t06"][1]
    t07 = results["t07"][1]
    t08 = results["t08"][1]

    monthly_net = {r[0]: r[4] for r in t06}
    monthly_margin = {r[0]: r[5] for r in t06}
    peak_month = max(monthly_net, key=monthly_net.get)
    month_names = {"2026-01": "January", "2026-02": "February",
                   "2026-03": "March", "2026-04": "April",
                   "2026-05": "May", "2026-06": "June"}
    # Apr–May discount bill, from the monthly table via a direct query
    promo_discount = con.execute(
        """SELECT SUM(gross_pkr - net_pkr) FROM (
               SELECT o.order_id,
                      i.quantity * i.unit_price_pkr AS gross_pkr,
                      CAST(ROUND(i.quantity * i.unit_price_pkr
                                 * (1.0 - o.discount_pct)) AS INTEGER)
                          AS net_pkr
               FROM orders o
               JOIN order_items i ON i.order_id = o.order_id
               WHERE strftime('%Y-%m', o.order_date) IN
                     ('2026-04', '2026-05'))"""
    ).fetchone()[0]

    takeaway = (
        f"Net revenue peaked in {month_names[peak_month]} at PKR "
        f"{fmt(monthly_net[peak_month])} — but the Apr–May promo bought "
        f"that growth with PKR {fmt(promo_discount)} of discounts, so "
        f"margin fell from {t03['Q1'][8]}% in Q1 to {t03['Q2'][8]}% in Q2."
    )

    # Category / channel shares, from direct queries (independent of
    # the technique files, same mart definition).
    cat = dict(con.execute(
        """SELECT category, SUM(net_pkr) FROM (
               SELECT CAST(ROUND(i.quantity * i.unit_price_pkr
                                 * (1.0 - o.discount_pct)) AS INTEGER)
                          AS net_pkr, p.category
               FROM orders o JOIN order_items i
                 ON i.order_id = o.order_id
               JOIN products p ON p.product_code = i.product_code)
           GROUP BY category"""
    ).fetchall())
    chan = dict(con.execute(
        """SELECT channel, SUM(net_pkr) FROM (
               SELECT o.channel,
                      CAST(ROUND(i.quantity * i.unit_price_pkr
                                 * (1.0 - o.discount_pct)) AS INTEGER)
                          AS net_pkr
               FROM orders o
               JOIN order_items i ON i.order_id = o.order_id)
           GROUP BY channel"""
    ).fetchall())

    summary = {
        "orders": raw_counts["orders"],
        "lines": raw_counts["order_items"],
        "customers": raw_counts["customers"],
        "products": raw_counts["products"],
        "units": t03["Q1"][3] + t03["Q2"][3],
        "gross_revenue_pkr": t03["Q1"][4] + t03["Q2"][4],
        "total_discount_pkr": t03["Q1"][5] + t03["Q2"][5],
        "net_revenue_pkr": t01[2] + t01[4],
        "gross_profit_pkr": t03["Q1"][7] + t03["Q2"][7],
        "overall_margin_pct": round(
            (t03["Q1"][7] + t03["Q2"][7]) * 100.0
            / (t01[2] + t01[4]), 2),
        "q1_net_revenue_pkr": t01[4],
        "q2_net_revenue_pkr": t01[2],
        "headline_change_pct": t01[5],
        "headline_sentence": t01[6],
        "q1_margin_pct": t03["Q1"][8],
        "q2_margin_pct": t03["Q2"][8],
        "margin_change_points": round(
            t03["Q2"][8] - t03["Q1"][8], 2),
        "q1_gross_profit_pkr": t03["Q1"][7],
        "q2_gross_profit_pkr": t03["Q2"][7],
        "profit_change_pct": t02["Consequence"][3],
        "promo_discount_apr_may_pkr": promo_discount,
        "monthly_net_revenue_pkr": monthly_net,
        "monthly_margin_pct": monthly_margin,
        "peak_month": peak_month,
        "peak_month_net_pkr": monthly_net[peak_month],
        "net_revenue_by_category_pkr": cat,
        "net_revenue_by_channel_pkr": chan,
        "top_product": t04[0][1],
        "top_product_net_pkr": t04[0][4],
        "rest_products_net_pkr": t04[5][4],
        "takeaway_sentence": takeaway,
        "technique_rows": {num: len(results[num][1])
                           for num, _ in TECHNIQUES},
        "months": sorted(monthly_net),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("wrote outputs/summary.json")

    build_chart(t06, takeaway)
    build_one_pager(t08, summary)
    print(f"total net revenue PKR {fmt(summary['net_revenue_pkr'])}, "
          f"{summary['orders']} orders, {summary['lines']} lines")
    con.close()


if __name__ == "__main__":
    main()
