# Mini #25 — findings: what each storytelling technique proves

**SAMPLE / DEMO data only.** Fictional store "Noor Electronics",
fictional sales, Jan–Jun 2026. The storytelling techniques are
real; the business is not. Every number below is recomputed from
the raw CSVs by `src/checks.py` and matches `outputs/summary.json`
and the README exactly. Numbers in the technique CSVs are plain
integers (PKR 5164520, not PKR 5,164,520) so the SQL output can be
byte-compared by the checks; the formatted versions live here,
in the one-pager, and in the README.

## Headline numbers

- 550 orders, 1,023 lines, 1,523 units, Jan–Jun 2026.
- Gross revenue PKR 9,331,200; discounts PKR 772,890 (8.28% of
  gross); **net revenue PKR 8,558,310**; gross profit
  PKR 2,870,810; overall margin 33.54%.
- Q1: 205 orders, net PKR 3,393,790, margin 38.14%.
  Q2: 345 orders, net PKR 5,164,520 — **up 52.18%** — margin
  30.53%, down 7.61 points. Profit rose only 21.80%
  (PKR 1,294,340 → PKR 1,576,470): the growth was bought.
- Monthly net revenue: Jan 991,350 · Feb 1,209,670 ·
  Mar 1,192,770 · Apr 1,399,860 · **May 2,020,840** ·
  Jun 1,743,820. May is 23.61% of the whole half.
- Categories: Electronics PKR 3,474,800 (40.60%) · Furniture
  PKR 3,164,160 (36.97%) · Kitchen PKR 1,678,390 (19.61%) ·
  Stationery PKR 240,960 (2.82%) — the weak category.
- Channels: Online PKR 3,520,350 (41.13%, 224 orders) · Phone
  PKR 2,627,200 (30.70%, 164) · In-Store PKR 2,410,760 (28.17%,
  162) — the strong channel is Online.
- Top product: Office Chair PKR 2,430,000 (28.39%). The top 5
  products are 77.68% of net revenue; the other 4 are 22.32%.
- Average order value: PKR 15,561 overall — PKR 16,753 at full
  price, PKR 13,772 on discounted orders.

## Technique by technique

### 1 — The headline number: one KPI, with its comparison

"Net revenue was PKR 5,164,520 in Q2 2026, up 52.18% on Q1 2026
(PKR 3,393,790)." The sentence works because it answers the
two questions every headline must answer — how much, and
compared with what — in one breath. The comparison is Q1, not
last year: there is no 2025 in this dataset, and the file does
not invent one. A headline that says "revenue was
PKR 5,164,520" and stops is trivia; a headline that says "up
52.18%" with no base is a claim. The number to remember is the
pair: PKR 5,164,520 against PKR 3,393,790.

### 2 — The 3-number story: context, change, consequence

Context: Q1 net revenue PKR 3,393,790, before any promo.
Change: Q2 net revenue PKR 5,164,520, up 52.18%. Consequence:
gross profit PKR 1,576,470, up only 21.80% on Q1 profit
(PKR 1,294,340). The consequence is the technique: the story
does not stop at the change, it names what the change meant —
and here the consequence undercuts the change, which is exactly
why the pattern matters. A three-number story where the third
number just repeats the second ("and orders rose too") is
decoration. The third number should be the one that decides
whether the change was good news, and profit is that number
here: revenue +52.18%, profit +21.80%.

### 3 — Before/after framing: same metric, two periods, honest baseline

Q1 is the baseline (205 orders, PKR 3,393,790 net, 38.14%
margin, average order PKR 16,555.07); Q2 is the promo period
(345 orders, PKR 5,164,520 net, 30.53% margin, average order
PKR 14,969.62). The file states the baseline in the
`baseline_note` column instead of hiding it: Q2 is NOT
like-for-like with Q1, because the promo changed the mix —
discounts rose from PKR 52,710 (1.53% of gross) to PKR 720,180
(12.24% of gross), and the average order fell by PKR 1,585.45
even as order count rose 68.29%. A before/after that pretends
the two periods differ only in time is a lie with true numbers.
The honest version shows the whole P&L shape per period, so
the reader can see WHICH lines moved.

### 4 — Ranking with a cut-off: top 5 plus "the rest"

1 Office Chair PKR 2,430,000 (28.39%) · 2 Mechanical Keyboard
PKR 1,556,350 (18.19%) · 3 Dinner Set 24pc PKR 1,228,150
(14.35%) · 4 Desk Lamp PKR 734,160 (8.58%) · 5 Bluetooth
Speaker PKR 699,400 (8.17%) · Rest (4 products)
PKR 1,910,250 (22.32%) · TOTAL PKR 8,558,310 (100.00%). The
"Rest" row is the technique: without it, "our top 5 products"
is cherry-picking with a ranking — the reader cannot tell
whether the top 5 are 90% of the business or 40%. Here they are
PKR 6,648,060, 77.68%, and the tail is big enough to matter: the rest contains
the Laptop Stand (PKR 656,550), the Wireless Mouse
(PKR 562,500), the Mug Set (PKR 450,240) and the Notebook Set
(PKR 240,960). The cut-off is stated in the row itself ("All
other products (4)"), and the shares sum to 100.00% — the
checks assert both.

### 5 — The honest caveat: a number that looks good but isn't

Q1: margin 38.14% on PKR 3,393,790 of net revenue, with only
PKR 52,710 given away in discounts. Q2: net revenue rose
52.18% to PKR 5,164,520, but margin fell to 30.53% — PKR
720,180 of discounts bought that growth. The caveat is not a
footnote; it is the same quarters with the discount bill and
the margin beside the revenue, so the good number and the bad
number share one table. Discounts went from 1.53% of gross in
Q1 to 12.24% in Q2. A summary that reports the revenue without
the margin is not optimistic, it is incomplete — and the
manager who acts on the revenue alone re-runs the promo and
wonders why the bank balance did not follow.

### 6 — One chart, one message

Monthly net revenue: Jan 991,350 · Feb 1,209,670 (+22.02%) ·
Mar 1,192,770 (−1.40%) · Apr 1,399,860 (+17.36%) ·
May 2,020,840 (+44.36%) · Jun 1,743,820 (−13.71%). The chart
(`outputs/technique_06_monthly_trend.png`) is bars for net
revenue with the margin as a line: the bars climb into May
while the line falls to its low of 26.86% in May, then the bars
fall in June while the line recovers to 36.71%. One chart, one
message — the title is the takeaway, and it is stored as text
in `summary.json` so it can be checked, not just seen: "Net
revenue peaked in May at PKR 2,020,840 — but the Apr–May promo
bought that growth with PKR 645,700 of discounts, so margin
fell from 38.14% in Q1 to 30.53% in Q2." A second message on
the same chart (say, the channel split) would be a second
chart. January has no month-on-month change — there is no
December 2025 in the dataset, and the file leaves it blank
rather than inventing one.

### 7 — The recommendation sentence: finding, so what, do this

Three worked recommendations, each with the number that
justifies it:

1. "Q2 net revenue rose 52.18% but margin fell 7.61 points to
   30.53%, so repeat the promo only with a 35% margin floor and
   a 20% discount cap." The supporting number is the 7.61
   points lost — the action (a floor and a cap) answers that
   number directly.
2. "Stationery is only 2.82% of net revenue, so bundle the
   Notebook Set with the Wireless Mouse, or review the range."
   Stationery is PKR 240,960 on 138 lines (13.49% of all lines,
   2.82% of the money): it sells often and earns little. The
   action is a bundle or a review, not "sell more Stationery"
   — the number says the category cannot carry itself.
3. "Online is 41.13% of net revenue, so put the next ad spend
   behind Online first." Online is PKR 3,520,350 across 224
   orders (40.73% of orders). The action follows the lead the
   data already shows, rather than spreading spend evenly.

A recommendation whose action cannot be traced back to a number
is an opinion, not analysis — each row here carries its
`supporting_value` and `supporting_label` beside the sentence.

### 8 — The one-page executive summary

The fixed shape: headline, three findings, one recommendation,
one risk — six lines, all built from the same aggregates as
techniques 1–7, so the page cannot disagree with the pack. The
headline is PKR 8,558,310 total, Q2 PKR 5,164,520 (+52.18%).
Finding 1: growth was promo-bought (Apr–May discounts
PKR 645,700 drove the May peak of PKR 2,020,840). Finding 2:
margin fell 38.14% → 30.53% while profit grew only 21.80%
against revenue +52.18%. Finding 3: Online leads at 41.13%;
Stationery is just 2.82% and needs a decision. The
recommendation is the promo with a 35% margin floor and a 20%
discount cap, ad spend behind Online. The risk: if the promo
repeats without a cap, margin stays near 30% — and June already
fell 13.71% when the promo ended, so a quiet month costs
profit, not just revenue. The rendered page is
`outputs/executive_summary_one_pager.md` and the matching PDF;
`src/build.py` renders both from the technique-8 rows, so the
page is regenerated, never hand-edited.

### 9 — What NOT to say: three misleading framings, each corrected

1. **Cherry-picked month.** "Revenue jumped 44.36% in May — our
   best month ever." True, and misleading: May is the promo
   peak, picked because it is the biggest; April rose only
   17.36% and June fell 13.71%. Corrected: "Net revenue rose
   44.36% in May to PKR 2,020,840, but that month carried
   PKR 384,160 of discounts and the lowest margin of the half
   — the jump was bought, not earned." The correction keeps the
   big number and adds the price of it.
2. **Percent without a base.** "Stationery revenue grew 83.09%
   in April!" True, and misleading: the base was PKR 24,840
   (March), so the rise is PKR 20,640 — about 0.24% of total
   net revenue. Corrected: "Stationery rose from PKR 24,840 in
   March to PKR 45,480 in April (+83.09%) — a PKR 20,640 move
   in a category worth 2.82% of revenue." A big percent on a
   tiny base is a small number in a loud voice; the correction
   states the base first.
3. **Average hiding a split.** "The average order is worth
   PKR 15,561." True, and misleading: discounted orders average
   PKR 13,772 (220 orders) and full-price orders PKR 16,753
   (330 orders) — the single average blends two different
   shops. Corrected: "Average order value is PKR 15,561
   overall, but PKR 16,753 at full price and PKR 13,772 on
   discounted orders; judge the promo on the discounted
   figure." Whenever an average is quoted, ask what it is
   averaging over — if the split is wider than the story, quote
   the split.

### 10 — The 60-second verbal brief

Eight spoken lines, 125 words, about 57 seconds at normal
pace: opening (the headline — PKR 8,558,310), numbers (Q2
PKR 5,164,520, up 52.18 percent; discounts PKR 645,700;
margin 38.14 to 30.53 percent; May peak PKR 2,020,840, June
down 13.71 percent; Online 41.13 percent, Stationery 2.82
percent), recommendation (35 percent margin floor, 20 percent
discount cap; ad spend behind Online; bundle the Notebook Set),
close ("growth bought on discount, margin down, Online
leading"). Percentages are spelled out because the brief is
meant to be read aloud, and every number in it is a number the
pack already proves — nothing in the brief is said that the
queries cannot show. The discipline is the count: 125 words
forces the choice of which three numbers matter, and the ones
left out (channel AOVs, the Rest row, February) are left out on
purpose.

## Two traps this pack teaches

- **A good number without its caveat is a half-truth.**
  Revenue +52.18% is true. Margin −7.61 points is also true,
  and it is the same story. The summary that reports one
  without the other has not summarised — it has selected. Put
  the caveat in the same table as the headline (technique 5),
  not in a footnote nobody reads.
- **A percent is not a number until it names its base.** 83.09%
  on PKR 24,840 is PKR 20,640; 44.36% in May is PKR 620,980
  on April's PKR 1,399,860 — and that May rise cost
  PKR 384,160 in discounts. Quote the base with the percent,
  every time, or the percent will do the misleading for you.

## Limits

- **SAMPLE data only.** The store, the sales and the "findings"
  are invented to teach the techniques.
- **The story is planted, not found.** Real business stories are
  messier — the promo effect, the weak category and the strong
  channel would overlap and need untangling. This pack plants
  each thread cleanly so the technique, not the untangling, is
  what gets practised.
- **One shop, six months, no prior year.** Every comparison is
  Q2 vs Q1 or month vs month; the pack never invents a
  prior-year baseline.
- **The discount lives on the order, not the line.** A real shop
  discounts some lines and not others; here the whole order
  shares one discount, which is what makes the margin
  arithmetic clean enough to check by hand.
- **The recommendation is illustrative, not advice.** A 35%
  margin floor and a 20% discount cap are the pack's worked
  example of a recommendation with a number behind it — a real
  shop would set its floor from its own costs, not from this
  file.
