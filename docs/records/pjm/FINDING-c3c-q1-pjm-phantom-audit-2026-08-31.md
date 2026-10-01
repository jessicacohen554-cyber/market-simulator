# FINDING — c3c-Q1, INDEPENDENT REPLICATION: PJM's reserve dual is **REAL**, not the ercot-214 phantom — reached by a different construction from pjm-164's and agreeing with it. Four new legs: the requirement is an **exact published identity** in 26,229 family-hours, the channel **never touches a penalty step** and is structurally bounded below the published $300 one, the positive-dual hours coincide with PJM's own posted shortage intervals at **75–91× base rate (p ≤ 9.7e-11)**, and the model **under**-prices reality by 2.7–7×. Plus one alignment caveat pjm-164 did not carry

**Session c3c-Q1/Q2, 2026-08-31, branch `claude/c3c-scarcity-charter-audit-uxmjon`.**
Executes Q1 of `docs/CHARTER-c3c-scarcity-program-2026-08-31.md` §5 under owner
ruling R-E. **ZERO SOLVE as dispatched: no LP built, no solver called, no year
scored, no run registered, no bundle modified, no holdout year touched (2023–2025
committed records only; `--holdout-authorized` never passed).**

**Keeper resolved fresh at session start AND end: `2026-08-15-pjm-162-inputclock`
— UNCHANGED, determination CALIBRATED.** Nothing here touches a keeper, shard,
marker, determination or matrix cell.

> ## PRIOR-ART NOTICE — this is a REPLICATION, not a first execution
>
> **Charter Q1 was already executed, at HEAD, by session pjm-164**
> (`docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md`; log entry
> `docs/calibration-log/pjm.md` "pjm-164"; artifact
> `results/calibration/_pjm164_c3c_overlap.json`), which returned **REAL**. This
> session ran in parallel and did not see that record until after its own
> measurement was complete. **The verdict below is theirs first.** What this
> finding contributes is an *independent replication by a different
> construction* — pjm-164 overlapped the model's C3c **tail hours** against the
> actual RT LMP tail; this overlaps the model's **positive-reserve-dual hours**
> against PJM's **published reserve-market record** — plus the four legs in §2–§5
> that their record does not carry, and one caveat (§6) that qualifies both.
> Where the two disagree on a number, both constructions are stated; there is no
> disagreement on the verdict.

Committed instrument: `scripts/probes/c3c_q1_pjm_phantom_audit.py` (no LP, no
solver) → `results/calibration/_c3c_q1_pjm_phantom_audit.json`.

---

## 0. VERDICT — **REAL**, independently

The ercot-214 phantom was an AS-product **shortfall-ramp penalty** (VOLL/12 =
$416.67) leaking through the all-tier cap dual into a written price, in hours
whose published settled RTORPA p50 was $14.2. Four legs, each independently
sufficient to have returned PHANTOM, all return REAL:

1. **Provenance is an exact identity, not a fit** (§2) — the model's reserve
   requirement equals the published PJM requirement plus the published ORDC
   breakpoint in **8,735 / 8,735 / 8,759 covered hours per family**, both
   families, zero exceptions.
2. **The channel is not the ercot-214 channel** (§3) — shortfall is identically
   zero in all **52,560** family-hours; the dual is opportunity cost, structurally
   bounded below the **cheapest published penalty factor ($300)** and observed at
   most $187.90.
3. **The timing is the inverse of caiso-144 §D** (§4) — 2025 returns **18/20**,
   **6/20** and **6/20** against three published severity tiers, at **3.7× / 75×
   / 91×** base rate, p = 1.1e-9 / 9.7e-11 / 2.8e-11.
4. **The direction of error is conservative** (§5) — the model prices **2.7–7×
   LESS** reserve scarcity than PJM posted in the same hours. A phantom
   over-prices; this under-prices.

**Two corrections to the charter's own premise, reported against this session's
convenience** (§6): PJM's C3c is scored on the **energy-only** LP dual (no
settlement overlay in any year), and the reserve channel is load-bearing in
**2025 only** — 2023's 4 tail hours coincide with **zero** positive-dual hours,
2024's 10 with 2 (max dual $8.49). pjm-164 reached the same conclusion
independently and recorded it as "cite **2025**, not 2023, as the existence
proof". The charter's "PJM's C3c PASS rides reserve duals to $187.90" is true of
one year in three.

---

## 1. WHAT WAS AUDITED, AND AGAINST WHAT

| | |
|---|---|
| Model side | `results/calibration/pjm_debugb_inputclock_A/hourly/reserve_family_<y>.parquet` (P1 per-family dual, requirement, held MW, ORDC shortfall — the only artifact in which a family's binding is observable, rule 15) + `system_<y>.parquet` (P1 zonal energy dual, the C3c basis) |
| Reality side | `data/raw/PJM-AS/reserve_market_results_<y>.parquet` — PJM DataMiner2 "Ancillary Services Market Results — Reserve Market Results" (RT), 5-minute, `locale` ∈ {PJM_RTO, MAD} × `service` = PR: published `mcp`, published `as_req_mw`, published `total_mw` |
| Published curve | `data/raw/_validation-source/pjm_ordc_curve.csv` — Manual 11 §4.3.3 two-step ORDC: $850 to the requirement, $300 for the next 190 MW, $0 beyond (FERC EL19-58 / ER19-1486, in force 2022-10-01) |

`pjm_primary` is the RTO Reserve Zone; `pjm_primary_mad` the nested
Mid-Atlantic/Dominion Reserve Subzone (Manual 11 §4.2). **Nesting convention:**
the model's MAD family is the *incremental* nested row while the published MAD
`mcp` is the *total* subzone price (visible directly — 2025-06-24 18:00: RTO
$1,212.15, MAD $1,384.76), so every MAD ratio in §5 uses a **larger** published
denominator than like-for-like, which strengthens rather than weakens the
conservative-direction conclusion.

## 2. PROVENANCE IS AN EXACT IDENTITY

| year | family | covered h | h where `requirement_mw` = published `as_req_mw` + 190 MW | median diff |
|---|---|---|---|---|
| 2023 | pjm_primary / _mad | 8,735 | **8,735 / 8,735** (both) | 190.0000 |
| 2024 | pjm_primary / _mad | 8,735 | **8,735 / 8,735** (both) | 190.0000 |
| 2025 | pjm_primary / _mad | 8,759 | **8,759 / 8,759** (both) | 190.0001 |

**26,229 family-hours, zero exceptions.** A lag scan over −3…+3 h returns
r = 1.00000 at lag 0 and strictly less elsewhere. 190 MW is the published
outermost ORDC breakpoint read from the cited CSV; `req` is
`load_pjm_measured_reserve_requirement` — PJM's own posted `as_req_mw`. The
builder is literally `requirement = req + outer_offset`
(`model/reserves/spec.py::_pjm_design`). No free parameter anywhere in the chain:
rules 5 `[R-NO-MAGIC]`, 13 `[R-MEASURED]`, 24 `[R-REGISTRY]` all clean. *(The
25 / 25 / 1 uncovered hours are gaps in the published feed, excluded from every
denominator rather than imputed.)*

## 3. THE CHANNEL — the published ORDC, never on a penalty step

`pjm_ordc_shortfall_steps` converts the published descending demand curve into
ascending LP shortfall bands, cheapest first: **penalties [$300, $850], widths
[190 MW, REQ]**. The dual is therefore bounded above by $300 unless the LP takes
>190 MW of shortfall.

| year | ORDC shortfall hours | dual max | cheapest published penalty | below it? |
|---|---|---|---|---|
| 2023 | **0** | $0.00 (never binds) | $300 | — |
| 2024 | **0** | $8.49 | $300 | yes |
| 2025 | **0** | **$187.90** | $300 | **yes — 63 % of the step** |

`shortfall_mw` is identically zero in **all 52,560 family-hours** and
`held_mw ≥ requirement_mw` in every one. The dual is opportunity cost and nothing
else — the exact structural point at which PJM and ercot-214 part company.

**The stronger reading of the same number.** PJM's published curve says the
(REQ + 190)th MW is worth **$300** to PJM. In every hour of three years the
model's cost of holding it was **at most $187.90** — the model never buys reserve
above what PJM's own published curve says PJM would pay at that quantity. A dual
above $300 would have been over-procurement against its own cited curve, i.e. a
manufactured channel. It has 37 % headroom and never approaches it.

## 4. THE OVERLAP — caiso-144 §D construction, on the published reserve record

`base rate` = the tier's share of the year's covered hours; `lift` = model hit
share ÷ base rate; `p` = one-sided hypergeometric P(X ≥ observed).

### 2025 — `pjm_primary` (PJM_RTO), 20 positive-dual hours

| reality tier | reality h | base rate | overlap | share | lift | p |
|---|---|---|---|---|---|---|
| reserve priced at all (`mcp` > 0) | 2,151 | 0.2456 | **18 / 20** | 0.900 | 3.66× | 1.1e-09 |
| on a published ORDC penalty step (5-min `mcp` ≥ $300) | 35 | 0.0040 | **6 / 20** | 0.300 | **75.08×** | 9.7e-11 |
| actually short (`total_mw` < `as_req_mw`) | 29 | 0.0033 | **6 / 20** | 0.300 | **90.61×** | 2.8e-11 |

### 2025 — `pjm_primary_mad` (MAD), 29 positive-dual hours

| reality tier | reality h | base rate | overlap | share | lift | p |
|---|---|---|---|---|---|---|
| reserve priced at all | 2,253 | 0.2572 | **22 / 29** | 0.759 | 2.95× | 2.2e-08 |
| on a published ORDC penalty step | 41 | 0.0047 | **7 / 29** | 0.241 | **51.57×** | 4.2e-11 |
| actually short | 8 | 0.0009 | **2 / 29** | 0.069 | **75.51×** | 2.9e-04 |

### 2024 — non-discriminating, and said so

Both families carry **2** positive-dual hours (2024-08-28 15:00/16:00). Both
coincide with `mcp` > 0 (2/2); neither with a penalty step or shortage (0/2). At
n = 2 against a 0.62 base rate, **p = 0.379** — evidence for nothing in either
direction, with duals of $8.49 / $8.00. Reported because a lane that reports only
its discriminating year is not reporting.

### 2023 — the family never binds

Zero positive-dual hours in either family, all 8,760 hours; nothing to overlap.
Reality priced RTO primary reserve in 2,822 hours and was short in 14 — so 2023 is
a **miss**, not a false positive. Same conservative direction as §5.

### Where the hours are

The 2025 positive-dual hours fall on **June 23–25** and **July 28–30, 2025** —
the two PJM heat events — the same days reality's own >$200 RT tail sits on, and
the same days pjm-164's independent construction identified. RTO 2025 hour table:

| hour (EPT) | model dual | published MCP (h-mean) | published MCP (5-min max) | reality short intervals |
|---|---|---|---|---|
| Jun 23 15:00 | $42.09 | $0.00 | $0.0 | 0 |
| Jun 23 16:00 | $66.50 | $0.43 | $5.2 | 0 |
| Jun 23 17:00 | $51.04 | $87.48 | $198.7 | 0 |
| Jun 23 18:00 | $19.88 | $614.47 | $849.2 | **9** |
| Jun 24 13:00 | $12.88 | $128.35 | $236.5 | 0 |
| Jun 24 14:00 | $64.66 | $9.07 | $68.9 | 0 |
| Jun 24 15:00 | $106.89 | $11.61 | $77.2 | 0 |
| Jun 24 16:00 | $138.79 | $234.30 | $784.2 | **1** |
| Jun 24 17:00 | **$187.90** | $265.69 | $677.7 | **4** |
| Jun 24 18:00 | $81.30 | **$1,212.15** | **$1,700.0** | **12** |
| Jun 25 15:00 | $5.28 | $0.00 | $0.0 | 0 |
| Jun 25 16:00 | $5.37 | $12.15 | $82.2 | 0 |
| Jun 25 17:00 | $15.13 | $239.55 | $850.0 | **2** |
| Jul 28 16:00 | $39.20 | $66.28 | $142.3 | 0 |
| Jul 28 17:00 | $97.50 | $26.87 | $129.3 | 0 |
| Jul 28 18:00 | $22.04 | $142.90 | $378.9 | **1** |
| Jul 29 15:00 | $57.15 | $72.05 | $235.1 | 0 |
| Jul 29 16:00 | $148.92 | $69.25 | $211.0 | 0 |
| Jul 29 17:00 | $161.99 | $93.03 | $248.7 | 0 |
| Jul 29 18:00 | $36.07 | $215.29 | $290.2 | 0 |

## 5. MAGNITUDE AND DIRECTION — the model under-prices real reserve scarcity

Restricted to coincident hours (model dual > 0 **and** reality priced reserve):

| year | family | n | model mean | model max | published MCP h-mean | published h-max | published 5-min max | ratio | h model exceeds |
|---|---|---|---|---|---|---|---|---|---|
| 2024 | pjm_primary | 2 | $4.42 | $8.49 | $17.08 | $33.93 | $113.05 | 0.259 | 1 / 2 |
| 2024 | pjm_primary_mad | 2 | $5.16 | $8.00 | $17.08 | $33.93 | $113.05 | 0.302 | 1 / 2 |
| 2025 | pjm_primary | 18 | $72.96 | $187.90 | $194.50 | $1,212.15 | $1,700.00 | **0.375** | 6 / 18 |
| 2025 | pjm_primary_mad | 22 | $31.95 | $70.49 | $225.23 | $1,384.76 | $2,550.00 | **0.142** | 6 / 22 |

**This is the leg that settles it.** The model carries **2.7–7× less** reserve
scarcity price than PJM posted in the same hours, with a ceiling 14× below
reality's realized 5-minute maximum. It is not inventing a tail. (pjm-164 states
the same fact from its own construction: "the channel under-fires reality's
reserve pricing ~10×".)

## 6. TWO PREMISE CORRECTIONS, AND ONE ALIGNMENT CAVEAT

### (a) C3c is scored on the energy-only dual, and the channel is load-bearing in 2025 only

| year | payload `ordc.hoursGt200` | scored basis | model tail h (> $200) | of those, h with a positive reserve dual |
|---|---|---|---|---|
| 2023 | `{model: 4, actual: 6}` | energy-only LP dual | 4 | **0** |
| 2024 | `{model: 10, actual: 18}` | energy-only LP dual | 10 | **2** (max $8.49) |
| 2025 | `{model: 32, actual: 59}` | energy-only LP dual | 32 | **27** |

Corroborated by config: `scarcity_price_overlay = False`,
`scarcity_pricing_enabled = False`. No reserve adder is written into PJM's scored
price; the dual reaches C3c only through co-optimization displacement. This makes
the existence proof **narrower** than the charter claimed and **cleaner**: the one
year in which the channel is load-bearing is the one year independently
corroborated against PJM's own posted scarcity intervals at p < 1e-10. pjm-164
additionally bracketed the counterfactual (2025 tail 5–30 h without the channel
against band [29.5, 118]) and concluded the channel **is** load-bearing for the
2025 PASS; this session ran no counterfactual and neither confirms nor disputes
that bracket.

### (b) ALIGNMENT CAVEAT — the overlap counts are lag-sensitive, and lag 0 is the conservative choice

PJM's `_dt_ept` is **prevailing** time (measured: UTC − `_dt_ept` is 4 h in
409,464 rows and 5 h in 219,528), while the model's PJM standard clock is
`Etc/GMT+5` (`derive_actual_lmp._STD_TZ["PJM"]`). The §2 identity proves the
model's *reserve requirement* is placed on the **prevailing positional index**,
so the dual-vs-published-price comparison above is self-consistent — it compares
the dual against the price of the very requirement row the LP enforced.

But an offset scan shows the model's series running **ahead** of the published
ones:

* model max-zonal energy dual vs `actual_lmp_hourly_PJM` (which is on
  `Etc/GMT+5`): r peaks at **lag −1** in 2023 (0.4096 vs 0.3997) and 2025 (0.6529
  vs 0.5906); 2024 is a tie at 0 (0.4868 vs 0.4848).
* mean published reserve MCP in the model's positive-dual hours, by lag:
  2025 → **−2: $368, −1: $303, 0: $175**, +1: $62, +2: $47.

**Consequence for this finding:** every overlap in §4 is reported at **lag 0**,
and the scan says lag 0 is the *weakest* alignment — shifting to the best lag
makes the coincidence stronger, never weaker. The verdict is therefore robust and
the counts are a **lower bound**. What the scan does *not* settle is the cause:
whether the model's reserve requirement is misplaced by an hour through the DST
season against its own EST energy clock (an input-clock question of exactly the
family `2026-08-15-pjm-162-inputclock` was built to repair), or the model genuinely
leads. **This is flagged, not diagnosed and not fixed** — it is outside Q1's
charter, it does not change the verdict, and it is named here so a future PJM lane
picks it up deliberately. The 1–3 h "lead" visible in the §4 hour table is the
same phenomenon and must **not** be read as an established model behaviour.

## 7. DISPOSITION

* **Q1 = REAL**, agreeing with pjm-164, by an independent construction.
* **Q2 opened** per the charter's chaining condition →
  `docs/FINDING-c3c-q2-nyiso-nyca-shortage-2026-08-31.md`. (It too was executed in
  parallel, by nyiso-164, which reached **CONFIRM**; that finding records this
  session's own initial contrary reading, its refutation, and the two data defects
  that produced it.)
* **Nothing armed, promoted, ledgered or re-determined.** No `ScenarioConfig`
  field added or changed; no bundle modified.
* **Matrix: NO cell moves, no shard edited.** Rule 26 duty (b) is not triggered —
  this is a measurement on committed artifacts and published raw, and it mints no
  verdict: `energy_reserve_coopt` PJM stays **K** on its existing evidence, as
  pjm-164 also recorded. Duty (c) not triggered (no new field). Rule 25
  `[R-ISO-SCOPE]`: this PJM finding enters no other ISO's shard.

## 8. DO-NOT-REDO (new, binding)

* **Re-auditing PJM's reserve dual for the ercot-214 phantom signature.** Now
  answered by two independent constructions (pjm-164 and this §2–§5). Re-open only
  on a PJM keeper whose committed `reserve_family_<y>.parquet` shows nonzero
  `shortfall_mw`, or whose payload acquires a settlement `overlay`.
* **Asserting that PJM's C3c PASS rides its reserve duals.** §6(a): 2025 only.
* **Re-deriving PJM's 2025 model reserve-binding hours as mis-timed.** §4.
* **Reading the §4 hour-table "lead" as a model behaviour.** §6(b): it is
  confounded with an unresolved prevailing-vs-standard placement question.
* Carried forward unchanged: caiso-144 §G, the ercot-214/215 phantom record, and
  pjm-164's own caveat list.

*Evidence:* `scripts/probes/c3c_q1_pjm_phantom_audit.py` →
`results/calibration/_c3c_q1_pjm_phantom_audit.json` (this session) ·
**`docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md` +
`results/calibration/_pjm164_c3c_overlap.json` (the prior execution this
replicates)** · `results/calibration/pjm_debugb_inputclock_A/` ·
`frontend/data/backcast/runs/2026-08-15-pjm-162-inputclock.js` ·
`data/raw/PJM-AS/reserve_market_results_<y>.parquet` + `README.md` ·
`data/raw/_validation-source/pjm_ordc_curve.csv` + `docs/multi-iso/pjm-reserve-curve-source.md` ·
`src/market_sim/model/reserves/spec.py::_pjm_design`,
`results/scarcity.py::pjm_ordc_shortfall_steps`,
`scripts/data/derive_actual_lmp.py::_STD_TZ` ·
`docs/FINDING-ercot214-gspur-phase0-2026-08-17.md` §0/§2,
`docs/FINDING-ercot215-counterpart-decontamination-2026-08-17.md` §3 ·
`results/calibration/FINDING-caiso144-coopt-dormancy-c3c-frontier-2026-07-30.md` §C/§D ·
`docs/CHARTER-c3c-scarcity-program-2026-08-31.md`.
