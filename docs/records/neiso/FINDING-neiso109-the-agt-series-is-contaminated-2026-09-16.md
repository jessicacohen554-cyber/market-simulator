# FINDING — neiso-109: the Algonquin series carries OTHER HUBS' PRICES, and the defects are not NYISO's

**Session** neiso-109 · **Date** 2026-09-16 · **ZERO LP.** No solve, no keeper change, no
`ScenarioConfig` field touched. Input repair under rule 14 `[R-ACCURATE]` and rule 23
`[R-FROZEN-DERIVE]` (cited to a source-alignment and source-coverage defect, never to a residual).

> ## THE HEADLINE
> `data/raw/gas-prices/algonquin_citygate_daily.csv` was **contaminated with other trading hubs'
> prices in two separate channels**, and the larger one had no Algonquin anchor at all:
>
> * **69 of the 89 `weekly_high`/`weekly_low` rows are a foreign hub's extreme** — Henry Hub,
>   Chicago Citygate, Transco Z6 NY, SoCal, PG&E, Waha, Dominion South, Tennessee Zone, Eastern
>   Gas and Katy (§4). **This includes the $28.36 "2023-02-02 arctic print" that
>   `hubs.iso_hub_daily_gas_prices`'s own docstring cites as the example of the mechanism
>   working. It is a New York price.**
> * **13 more are a foreign hub's main-sentence price** (§3), among them Sumas standing in the
>   Boston series through Winter Storm Elliott week.
>
> Plus **4 rows dated a week late** by stale EIA republishes (§5), **4 taken from a neighbouring
> week** (§6), and **47 prints never scraped at all** — among the missing, the whole of the
> **January 2025 polar vortex**.
>
> **NONE of the four NYISO defect classes is the cause.** They were audited against all 389
> archive pages and three of the four are provably inert here; the fourth is structurally
> impossible. The real defects were found by writing the guard first, exactly as the handoff
> instructed, and letting it fail.

---

## 1. THE FOUR NYISO DEFECTS, AUDITED — three inert, one impossible

Measured by running the committed parser against **all 389 EIA NG Weekly Update archive pages
2018–2026**, fetched from `https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/`.

| NYISO defect | NEISO verdict | evidence |
|---|---|---|
| **(a)** `re.search` takes only the FIRST table, discarding a catch-up page's additional live tables | **STRUCTURALLY IMPOSSIBLE** | 25 catch-up pages exist, but **the compact "Spot Prices" table has no Algonquin row at all** — verified on 2023-01-12 / 2024-01-11 / 2025-01-10, whose rows are `Henry Hub`, `New York`, `Chicago`. AGT is recovered from the NARRATIVE, and a catch-up page's narrative covers only its own week. |
| **(b)** hyphen-only date header drops the spaced form, shifting every price one day | **INERT** | Affects exactly **1 page of 389** (2023-01-12, `5 Jan`). AGT uses the column dates only to locate the report *Wednesday*, not to align N values against N+1 dates, so a lost column is harmless unless it is the Wednesday. **Pages where the Wednesday is missing: 0. Pages where `column_dates` returns empty: 0.** |
| **(c)** a tag splitting the month (`17-Fe<br/>b`) | **INERT** | Same measurement as (b): no page loses its Wednesday, none loses all its dates. |
| **(d)** a stray `</td>` so one region absorbs another's value | **N/A** | AGT reads no table value rows whatsoever. |

**This is why the handoff's instruction mattered.** Guessing from NYISO's list would have produced a
patch that changed nothing. The guard found the real defects.

## 2. WHAT THE GUARD IS, AND WHY IT IS A DIFFERENT SHAPE

Transco Z6 NY is a *table row*, so alignment there means column *i* of the values is column *i* of
the header — checkable inside one table. Algonquin has no table row. What the narrative carries
instead is a **redundant overlap**: every weekly page states the **prior** report Wednesday's price
as well as its own, so consecutive pages quote the same date twice. That is the invariant:

```
page(w).last_wednesday_price  ==  page(w-1).wednesday_price
```

`chain_guard()` checks it across pages the way the Transco guard checks across columns. Run against
the committed parser it reported **32 breaks**; against the repaired parser, **1** (§7).

## 3. DEFECT 1 — CROSS-HUB CONTAMINATION IN THE MAIN SENTENCE. 13 rows.

EIA opens a regional paragraph with a summary clause naming Algonquin and then prices a **different**
hub in the next sentence:

> "…to a decline of $5.01/MMBtu at **Algonquin Citygate**. Prices in the West, already at elevated
> levels… The price at **Sumas** on the Canada-Washington state border rose $4.73 from
> **$16.46/MMBtu last Wednesday** to $21.19/MMBtu yesterday." — page 2022-12-08

The committed `.{0,220}?` window reached across that sentence boundary and wrote **Sumas's** price
into the Boston series. The same page's *real* Algonquin sentence, 200 characters later, reads
"the price fell $5.01 from **$9.91/MMBtu** last Wednesday to $4.90/MMBtu yesterday".

**48 of 389 pages had the committed pattern spanning a sentence boundary.** Each of the 21 wrong
values was traced to the page that wrote it, and the causes separate cleanly:

| cause | rows | what the committed file held |
|---|---:|---|
| **cross-hub latch** (this section) | **13** | another hub's price, in the Boston series |
| **stale republish** (§5) | 4 | the right price on the wrong week |
| **missed phrasing** (§6) | 4 | a neighbouring week's price, where the scraper skipped the real sentence |

The largest errors, all thirteen cross-hub rows included:

| date | committed | true AGT | error | page that wrote it |
|---|---:|---:|---:|---|
| **2025-01-29** | 4.06 | **16.54** | **+12.48** | 2025-02-06 |
| **2025-02-05** | 2.98 | **13.22** | **+10.24** | 2025-02-13 |
| **2024-01-17** | 2.27 | **13.35** | **+11.08** | 2024-01-25 |
| **2022-11-30** | 16.46 | **9.91** | **−6.55** | 2022-12-08 — **Sumas**, Canada-WA border |
| 2023-07-05 | 1.87 | 7.93 | +6.06 | 2023-07-13 |
| 2025-07-16 | 4.48 | 9.74 | +5.26 | 2025-07-24 — **FGT Citygate**, Florida |
| 2023-06-28 | 1.66 | 5.94 | +4.28 | 2023-07-06 |
| 2023-08-30 | 4.51 | 1.43 | −3.08 | 2023-09-07 — **PG&E Citygate**, N. California |

2022-11-30 is the one the NYISO handoff quoted as a *surrounding print* for Winter Storm Elliott.
**It is a Pacific Northwest quote.**

**The fix is not a wider character bound** — at 400 characters the pattern latches onto Northwest
Sumas, Transco Z6 NY and PG&E prose on four further pages. The span is scoped by *what it must not
cross*: a tempered dot over `_OTHER_HUBS`, the hub vocabulary harvested from the archive's own
"the price at &lt;hub&gt;" constructions. A **sentence**-scoped span is also wrong — EIA writes the
price anaphorically across one ("Algonquin Citygate … had a significant price increase. **It rose
from** $8.08/MMBtu last Wednesday to $25.00/MMBtu yesterday", 2025-12-04) and sentence scoping drops
that real print.

## 4. DEFECT 2 — THE BIGGER ONE. The extremum harvest had NO ALGONQUIN ANCHOR AT ALL. 69 rows.

The `weekly_high` / `weekly_low` rows — **89 of the committed file's 436, one row in five** — came
from a pattern applied to **the whole page**:

```python
_HILO_TAIL = re.compile(r"weekly (high|low) of\s+\$([0-9]+\.?[0-9]*)/MMBtu\s+on\s+(\w+day)")
```

There is no `Algonquin` in it. It captured **whichever hub EIA happened to quote an extreme for**
and filed it as a Boston citygate print. Measured over the archive: of **120** matches, **95** had
a different hub as the nearest preceding hub name, and **69 of the 89 committed extremum rows are a
foreign hub's price**:

| foreign hub | rows | | foreign hub | rows |
|---|---:|---|---|---:|
| Henry Hub | 15 | | PG&E Citygate | 6 |
| Chicago Citygate | 15 | | Waha | 3 |
| Transco Z6 NY | 14 | | Dominion South / Tennessee Zone / Eastern Gas | 2 each |
| SoCal Citygate | 9 | | Katy | 1 |

**Two land where the model leans hardest, and one of them is quoted in the model's own source:**

* **2023-02-02 $28.36.** `hubs.iso_hub_daily_gas_prices`'s docstring names this as the worked
  example of the mechanism succeeding — *"the real cold-day spike (e.g. the $28/MMBtu 2023-02-02
  arctic print) lands on its true calendar day"*. It is **Transco Z6 NY**. Algonquin's own
  published extremes that week were a low of $3.22 on Friday and a high of $13.49 on Tuesday, and
  the committed parser captured **neither**.
* **2024-01-16 $23.90** — likewise Transco, in the January-2024 arctic outbreak.

The concentration is worst in **2021**, which is why that year carried 94 rows, more than any
other: most of its extremum rows are Chicago, Henry Hub, SoCal and PG&E.

**The fix is `agt_regions()`** — the stretch of prose from an Algonquin mention to the next OTHER
hub's name — with the extremum patterns run **inside a region** instead of over the page. A region
rather than one anchored regex, because EIA states two extremes in a single sentence ("reached a
weekly low of $3.22/MMBtu on Friday, **before rising to** a weekly high of $13.49/MMBtu on
Tuesday") and an anchored pattern finds only the first. The anchor also had to learn EIA's
three-word spelling, **"Algonquin City Gate"**, which carries a real $22.48 cold-week high on
2022-02-17. After the repair: **34 extremes harvested, and 0 regions contain a foreign hub name** —
the invariant holds by construction, not by inspection.

*(Two correctly-anchored patterns, `_AGT_HIGH` and `_AGT_LOW`, sat beside `_HILO_TAIL` and were
**never called**. The right intent was in the file the whole time; the wrong one was wired up.
They are DELETED rather than left parsing — rule 26 `[R-DELETE]`, a dead path is a re-armable
answer key.)*

## 5. DEFECT 3 — STALE REPUBLISH. 4 pages date every print a week late.

EIA sometimes publishes a new Weekly Update whose *Spot Prices* table carries the new report week
while **the prose is last week's, verbatim**: 2018-01-18, 2019-04-18, 2023-09-14, 2024-03-07. The
column dates advance and the sentence does not, so every print lands **exactly seven days late** —
the same class of harm as NYISO's one-day shift (wrong data on ordinary days), arriving by a
completely different route. A duplicate sentence carries no new information, so the page is now
skipped rather than dated.

**The republish signature had to be measured, not assumed, and the first version of it was wrong.**
A signature that stopped at the first period truncated at the first decimal
(`"…went down $1."`), and three *normal consecutive weeks* — 2018-03-15, 2022-05-12, 2022-06-23 —
collided on that prefix and were wrongly skipped. The signature now spans the sentence's own
decimals. Caught by `tests/test_fetch_algonquin_daily_spot.py`, before the data was regenerated.

## 6. DEFECT 4 — FOUR UNMATCHED EIA PHRASINGS. 47 prints were never scraped.

The committed pattern required, literally, `$X/MMBtu last Wednesday to $Y/MMBtu yesterday`. EIA
writes that sentence four other ways, each measured on the archive rather than speculated:

| variant | pages | example |
|---|---:|---|
| intervening extremum clause on either price | 39 | "to their weekly low of $3.85/MMBtu yesterday" |
| unit spelled out on first use | 2 | "$1.90 per million British thermal units (MMBtu) last Wednesday" |
| "this Wednesday" for the report Wednesday | 1 | **2025-01-10**, the January-2025 cold-snap print $4.86 → **$16.55** |
| "last week" for the prior report Wednesday | 2 | chain-guard-verified against the previous page |

Not matched, per rule 14 (prefer the real datum, never guess one): **"last Thursday"** (2024-06-27)
anchors the first price to a day the report week cannot resolve, so that page yields only its
Wednesday print.

**Still genuinely absent, and stated rather than filled:** 23 pages carry no Algonquin price at all
(EIA rotates which hubs the narrative prices) — notably five consecutive weeks in May 2025 and three
in October 2023. **And the Winter Storm Elliott hole is REAL and UNFILLABLE from this source**: the
gap 2022-12-21 → 2023-01-04 stands, because AGT has no table row and the catch-up narrative covers
only its own week. This is the sharpest NEISO/NYISO difference — NYISO's Elliott days were
recoverable because Transco Z6 NY *is* a table row.

## 7. THE RESULT, AND THE GUARD AFTER THE REPAIR

```
                     main-sentence pages   CHAIN BREAKS   IMPLAUSIBLE EXTREMES
committed parser             313               32              10 of 91
repaired parser              347                1               0 of 27     (+ 4 stale pages skipped)
```

**`436 → 417 rows: +47 added, −66 removed, 26 corrected.`** The file gets *smaller* because the
foreign extremes outnumber the recovered Wednesdays: **65 of the 66 removed rows are extremum rows**,
and the source mix moves from `weekly_high` 48 / `weekly_low` 41 to **17 / 7**. The 26 corrections
include `2024-01-16 $23.90 → $17.27` and `2025-08-11 $3.00 → $4.62`, both Transco rows replaced by
Algonquin's own.

**The two guards agree without sharing an assumption.** `chain_guard` tests date anchoring across
pages; `extremum_guard` tests, with no hub vocabulary at all, that a weekly high is not below its
own week's Wednesday prints and a weekly low not above them. On the pre-repair file the second one
independently flags **10 of 91** extremum rows, every one of them a row the region analysis had
already identified as a foreign hub's. On the repaired file it flags **0 of 27**.

**2021 loses 38 rows**, the most of any year — which is why it had carried 94, more than any other
year in the file.

**The single residual break is EIA's own contradiction, not a parser defect** — page 2019-12-05
restates 2019-11-20 as $4.63 where the 2019-11-21 page reported $3.58 for its own Wednesday, across
the archive's Thanksgiving-week gap. The later page wins (standard revision handling), it is outside
every registered year, and it is reported rather than silently absorbed.

## 8. WHAT THIS DOES NOT DO

* **It does not change any model result.** Nothing is re-solved here; the keeper
  `2026-09-09-neiso-108-fuelvintage` is untouched. The repaired input is screened under rule 29
  `[R-SCREEN]` on ONE year chosen by FOOTPRINT
  (`scripts/probes/_neiso109_gas_repair_footprint.py`), never by residual —
  `docs/PRECOMMIT-neiso109-gas-repair-screen-2026-09-16.md`.
* **It moves no mechanism cell** (rule 28 `[R-MECH-MATRIX]` (b)): no `ScenarioConfig` field was
  added or changed, so there is no cell to update.
* **Rule 25 `[R-ISO-SCOPE]`:** every changed byte is in NEISO's own AGT file. The shared
  `gas_basis_by_iso_month.csv` is **not touched** — NEISO's monthly anchor is an independent
  measured source and this repair is one-step (PRECOMMIT §2).
