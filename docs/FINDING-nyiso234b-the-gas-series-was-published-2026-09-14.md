# FINDING — nyiso-234b: the Elliott gas prints were never missing. EIA published them; the scraper dropped them — and shifted other weeks by a day

**Session** nyiso-234 · **Date** 2026-09-14 · **ZERO LP.** Keeper **UNCHANGED**
(`2026-09-13-nyiso-232-st-gas`). Executed under the owner ruling of 2026-09-14
(*"Yes to 1 and 2"*) on `docs/DECISION-CARD-nyiso234-tail-gas-coverage-2026-09-14.md`.

Companion to `docs/FINDING-nyiso234-tail-gas-is-unobserved-2026-09-14.md`, which measured the
defect from the model side. This one finds its cause, and it is **cheaper and larger** than that
finding assumed: cheaper because no new data source is needed, larger because the committed series
is not only incomplete — in some weeks it is **wrong**.

---

## 0. HEADLINE

1. **The prints were published.** EIA issues no Natural Gas Weekly Update during the
   Christmas/New Year weeks, and when it resumes it carries the skipped weeks as **additional live
   tables in the catch-up page**. `scripts/data/fetch_transco_daily_spot.py` took `re.search` —
   the **first** table only — and silently discarded them. **Transco Z6 NY on Elliott was
   $32.12 (Dec 22 2022) and $35.61 (Dec 23 2022)**, against the **$8.05** the model burned.
2. **A second defect, not anticipated by the card: some weeks are MISALIGNED BY ONE TRADING DAY.**
   The header date pattern required a hyphen and dropped the spaced form, leaving four dates
   against five values — so every price in such a week landed on the **following** trading day.
3. **Both are fixed in the fetcher, and the fix is guarded** so a misaligned table can never be
   emitted again — it is skipped with a warning instead. A silent one-day shift in delivered gas
   is worse than a gap, because a gap is visible and a shift is not.

**This is a rule 23 `[R-FROZEN-DERIVE]` re-derivation cited to a SOURCE-COVERAGE AND
SOURCE-ALIGNMENT defect — never to a residual.** No residual was consulted in finding it, and the
repair is not sized against any gate.

---

## 1. DEFECT 1 — the catch-up tables

### 1.1 EIA's publication calendar, measured from its own archive index

`https://www.eia.gov/naturalgas/weekly/includes/archive.php` (1,463 entries). Around every
year-end, three publication Thursdays in a row are absent:

| year | last page of December | next page | weeks skipped |
|---|---|---|---:|
| 2022 | **Dec 22** | **Jan 12** | 2 |
| 2023 | **Dec 21** | **Jan 11** | 2 |
| 2024 | **Dec 19** | **Jan 10** | 2 |

Requesting the missing Thursdays directly confirms it — `archivenew_ngwu/2022/12_29/` and
`archivenew_ngwu/2023/01_05/` both return **HTTP 404**.

### 1.2 But the data is in the catch-up page — as extra LIVE tables

The `2023-01-12` page carries **three** live "Spot Prices ($/MMBtu)" tables, not one:

| table | week | New York ($/MMBtu) |
|---|---|---|
| 1st (the current week) | Jan 5 – Jan 11 | 3.17 / 3.50 / 3.98 / 3.37 / 2.79 |
| 2nd | Dec 29 – Jan 4 | 3.29 / 2.77 / *Holiday* / 2.56 / 3.35 |
| **3rd** | **Dec 22 – Dec 28** | **32.12 / 35.61 / *Holiday* / 6.29 / 5.15** |

**The third table is the only published record of Winter Storm Elliott in this source, and it was
there the whole time.** The same three-table shape repeats in the `2024-01-11` and `2025-01-10`
catch-up pages (the latter carrying Dec 20 2024 at **$10.00**, another spike the committed series
never saw).

### 1.3 The line that lost it

```python
m = re.search(r"<table.*?</table>", seg, flags=re.S)   # the FIRST table only
```

`re.search`, not `re.finditer`. The commented-out template tables were correctly stripped
beforehand; what the function never considered is that a page may carry **more than one LIVE
table**, and that those extra tables are precisely the weeks with no page of their own.

---

## 2. DEFECT 2 — a one-day shift, and it is worse than the gap

Some headers separate day and month with a **space** rather than a hyphen — `"Thu, 5 Jan"` beside
`"Fri, 6-Jan"`, sometimes in the same table. The pattern was hyphen-only:

```python
date_tokens = re.findall(r"(\d{1,2})-([A-Z][a-z]{2})", head)   # misses "5 Jan"
```

so that week parsed **four** dates against **five** values, and `zip`-by-index then paired value *i*
with date *i+1*. Measured on the 2023-01-12 page's current-week table:

| date | committed series | EIA published | |
|---|---:|---:|---|
| 2023-01-05 | *(absent)* | 3.17 | dropped |
| 2023-01-06 | **3.17** | 3.50 | **shifted** |
| 2023-01-09 | **3.50** | 3.98 | **shifted** |
| 2023-01-10 | **3.98** | 3.37 | **shifted** |
| 2023-01-11 | **3.37** | 2.79 | **shifted** |

This is not a tail-only defect. It is a wrong delivered gas price on ordinary days, in the series
that prices **every gas unit in the NYISO fleet** — so unlike defect 1 it bears on C1/C3a generally,
not just on the extreme hours. It is also the more insidious of the two: the coverage gap is
visible to anyone who counts rows, whereas a one-day shift looks like perfectly good data.

---

## 3. THE FIX

`scripts/data/fetch_transco_daily_spot.py`, three changes, all in the parser:

1. **`re.finditer` over every live table**, each parsed independently by a new `_parse_one_table`
   helper, so one malformed table cannot discard the others.
2. **Both separators accepted** — `(\d{1,2})[-\s]([A-Z][a-z]{2})\b`.
3. **An ALIGNMENT GUARD.** A table is emitted only when its header dates and value cells line up
   exactly; otherwise it is **skipped with a warning on stderr** rather than emitted misaligned.
   This is the durable half of the repair: it converts the silent failure mode that produced
   defect 2 into a loud one, so the class cannot recur unnoticed.

`"Holiday"` / `"Closed"` cells still yield no row, which is correct — no trade occurred.

Verified on the 2023-01-12 page: **13 correctly-dated rows** where the old parser returned 4
misaligned ones.

---

## 4. WHAT THIS CHANGES, AND WHAT IT DOES NOT

**It does not change any model result yet.** Nothing has been re-solved; the keeper is untouched.
The repaired series changes an **input**, and under rule 29 `[R-SCREEN]` the arm is screened on one
year before any span is spent.

**It is not a tail-only repair, so it must not be screened as one.** Defect 1 concentrates on the
extreme days; defect 2 is spread across ordinary trading weeks. The screen must therefore look at
what the mechanism *does* — the delivered gas series and the dispatch response — and not at whether
C3a moved (rule 1 `[R-STRUCT]`, and the screen gate is a STOP gate only).

**Expect the tail to rise and expect that not to close C3a by itself.** nyiso-232 established that
NYISO's C3a is a difference of two large errors of opposite sign, and nyiso-234 §3 established that
a tail repair here carries no compensating re-level onto ordinary hours. So C3a may well get
*worse* as the tail is corrected — which is the predicted behaviour, not a failure, and is exactly
why rule 1 forbids judging this on the residual.

**The response is bounded by machinery already armed.** `dual_fuel_switching` caps downstate units
at oil parity, measured at **$24.85/MMBtu** on Dec 23-24 2022. With the real gas at **$35.61**, the
dual-fuel fleet re-prices to **oil parity**, not to $35.61 — which is what those units actually did
in Elliott. The non-dual-fuel fleet has no such cap.

**Rule 25 `[R-ISO-SCOPE]`: this is a shared fetcher, and NEISO is exposed.** The Algonquin Citygate
series has the same holiday holes. The fix here is to the Transco fetcher only; whether NEISO's
series carries the same two defects is **NEISO's lane to measure**, and is flagged, not acted on.

---

## 5. RULES

1 `[R-STRUCT]` — the defect was found from the source's publication calendar and the scraper's own
code, never from a residual; the repair is not sized against any gate.
5 `[R-NO-MAGIC]` — every value is EIA's published print; nothing is interpolated or invented.
13 `[R-MEASURED]` / 14 `[R-ACCURATE]` — a measured input replacing a wrong and incomplete one, with
the same forward construction for any year.
23 `[R-FROZEN-DERIVE]` — a re-derivation cited to a source-coverage and source-alignment defect.
25 `[R-ISO-SCOPE]` — NEISO's identical exposure is flagged for NEISO's lane, not fixed from here.
29 `[R-SCREEN]` — the repaired input is screened on ONE year before any span is spent, on what the
mechanism does, never on the target residual.
32 `[R-SHARD]` — **the parent runs zero LP**; the screen goes to a shard.
