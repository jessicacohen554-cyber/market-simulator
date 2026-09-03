# PRE-DECLARATION — capx D45: the PJM + NYISO first diagnostics-on T1-H solves at the live stack posture, plus the two pre-stated probe legs the curve-ON adjudication needs

**Lane:** capx D45 — the once-only cross-ISO clearing-half + curve-ON charter
(`docs/handoffs/capx-director-prompt-pack-2026-08.md` §D45, issued r#31). Branch
`claude/capx-d45-pjm-nyiso-curves-f3dn56`, FRESH off `origin/main` `c73f78f5`.
**Pushed BEFORE any solve started.** Predictions are graded at full magnitude in the
finding, misses included, and nothing below may be re-narrated after a result is read.

**Governing discipline (rule 14, inherited from D28/D31/D37/D40):** faithful positions
and curves move capacity revenue UP and retirements HARDER; nothing is sized by any
residual; a worse-looking FC-3 after accurate inputs is the expected signature.
**NOTHING ARMS in this lane.** No `ScenarioConfig` field is added or moved
(rule 28 not triggered); no keeper / shard / marker; the backcast namespace is untouched.

---

## 1. The posture, resolved and verified before the solve

Four legs, all `run_capacity_hindcast.py --start-year 2021 --end-year 2025 --vintage 2020
--fuel-variant realized`, years sequential inside every invocation, **one leg at a time on
this 15 GB / 4-core host** (a PJM year solve holds ~8.8 GB peak RSS per S-6; rule 12's
~2-concurrent cap is a memory ceiling here, exactly as D42 recorded for MISO).

| # | leg | run id | posture | cache key (HEAD, `build_config` + `apply_iso_scenario_defaults`) |
|---|---|---|---|---|
| L1 | **PJM live-posture baseline** | `pjm-2021-2025-realized-t1h-d45` | HEAD default + `--entry-screen-diagnostics` (PJM ships curve-ON: `capacity_market_clearing_by_iso[PJM]=True`) | `ea767a6254b8e4af` |
| L2 | **NYISO live-posture baseline** | `nyiso-2021-2025-realized-t1h-d45` | HEAD default + `--entry-screen-diagnostics` (NYISO ships curve-OFF: absent from the mapping → the flat $110/kW-yr anchor) | `212eb1c57251fdc6` |
| L3 | NYISO curve-ON probe (suffixed) | `nyiso-2021-2025-realized-t1h-d45-curveon` | L2 + `--capacity-market-clearing` (force-ON for NYISO only) | `88f39cbe48b958c3` |
| L4 | PJM fixed-anchor control (suffixed) | `pjm-2021-2025-realized-t1h-d45-fixed` | L1 + `--fixed-net-cone` (the FFR-2E comparison arm: flat $77.43/kW-yr) | `8d4e574cb496bd01` |

Bare-HEAD keys for reference (no diagnostics): PJM `effea5304621a7e4`, NYISO
`f655e800b177b01c`. **None of the four keys collides with any committed PJM or NYISO
bundle** (the 37 committed keys were enumerated). Each leg gets a fresh, verified-empty
out-dir and `CACHE_ROOT` is redirected there by the harness, so no pre-existing bundle can
be served. **Solve order: L1 → L2 → L3 → L4** (PJM first, then NYISO, per the charter;
the two probes after both baselines). If wall-clock runs short, **L4 is the leg dropped**
(the PJM adjudication has the FFR-2E fixed/shipped pair and the D28 census as fallback
evidence; the NYISO curve-ON probe has no current-stack equivalent and is the charter's
loudest latent object).

**Posture vintage, stated per leg (the D44 collision, a fact not a conflict):** at the
launch HEAD `c73f78f5`, D44 has NOT landed — `fossil_announced_exits_enabled` ships
`False` (verified in `scenarios.py:3042`) and `hindcast_verified_announced_exits` ships
`True`. Every leg therefore records the **pre-D44 fossil-dates posture**; if D44 merges
mid-session the later legs still solve at the checkout they launched from, and the finding
states the vintage per leg from each `run_config.json`.

**The `entry_screen_diagnostics` precondition (D43 §7's routing for PJM/NYISO).** D37
verified it is output-only (byte-identical fleet outcome) but NOT cache-key-free (it is
hashed at every value). So L1/L2 are the first PJM/NYISO solves that commit the
expected-side entry-screen dumps — a by-product, not an object — at the cost of a full
re-solve rather than a cache hit.

### 1.1 The published record the positions are graded against (computed BEFORE the solve)

Instrument: `docs/handoffs/d45/published-positions-2026-09-03.py` (+ `.json`), zero model
quantities. Every number is a committed CSV row or a transcription from a fetched primary
document whose sha256 the finding records.

**PJM — where the RPM really sat, on the auction's own UCAP denominator** (BRA report
Table 6 offered UCAP; committed cleared UCAP + price; committed FRR-adjusted requirement +
EE addback; HEAD's vintage curve evaluated at each published position):

| DY | requirement | offered | cleared | **pos offered** | **pos cleared** | pos (1+RM)/(1+IRM) | real $/kW-yr | HEAD curve @cleared | zero-cross |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021/22 | 157,073.7 | 186,504.8 | 163,627.3 | **1.187** | **1.042** | 1.049 | 51.10 | 57.37 | 1.074 |
| 2022/23 | 137,461.6 | 167,698.4 | 144,477.3 | **1.220** | **1.051** | 1.047 | 18.25 | 20.86 | 1.066 |
| 2023/24 | 137,291.5 | 156,614.5 | 144,870.6 | **1.141** | **1.055** | 1.048 | 12.46 | 15.30 | 1.065 |
| 2024/25 | 139,722.9 | 157,362.7 | 147,478.9 | **1.126** | **1.056** | 1.050 | 10.56 | 14.46 | 1.064 |
| 2025/26 | 135,023.4 | 135,692.3 | 135,684.0 | **1.005** | **1.005** | 1.006 | 98.52 | 104.48 | 1.067 |
| 2026/27 | — | 135,191.8 | 134,205.3 | — | — | 0.998 | 120.15 | — | 1.045 |

Two published facts that frame the whole PJM half, stated now so they cannot be
back-fitted: (i) **the OFFERED position in 2021–2024 was 1.13–1.22, the CLEARED position
1.04–1.06** — one auction, two quantities, and the price forms at the second; (ii) HEAD's
vintage curves reproduce the real clearing price at the CLEARED position to +6 % … +37 %
(the shape is published-faithful; D28's finding stands) and pay **$0 at the OFFERED
position in every pre-CIFP year**.

**NYISO — where the NYCA really sat** (NYSRC 2026-27 IRM Study Appendices Table D.2:
ICAP-market peak, ADOPTED IRM, derate factor, ICAP and UCAP requirements; Potomac SOM
"UCAP Margin (Summer), % of Requirement"; committed spot prices):

| CY | IRM study / adopted | derate | ICAP req | UCAP req | UCAP supplied | **pos** | spot $/kW-yr | HEAD curve @pos |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2021/22 | 20.7 / 20.7 | 0.0877 | 39,026 | 35,604 | 37,349 | **1.049** | 50.16 | (flat vintage) |
| 2022/23 | 19.6 / 19.6 | 0.0978 | 37,993 | 34,277 | 37,122 | **1.083** | 36.60 | (flat vintage) |
| 2023/24 | 19.9 / **20.0** | 0.1014 | 38,459 | 34,559 | 36,045 | **1.043** | 49.32 | 47.57 |
| 2024/25 | 23.1 / **22.0** | 0.1321 | 38,481 | 33,397 | 35,334 | **1.058** | 41.64 | 37.38 |
| 2025/26 | 24.4 / 24.4 | **0.1300** | 39,148 | 34,059 | 36,034 | **1.058** | 51.36 | 26.12 |

Three published facts, stated now: (i) NYSRC **adopted** 22.0 % for 2024/25 (study 23.1 %)
and 20.0 % for 2023/24 (study 19.9 %) — the committed `nyiso.csv` carries the STUDY values;
(ii) the 2025/26 derate factor is 0.1300 (the committed series stops at 2024/25's 0.1321,
which HEAD applies to every year); (iii) HEAD's single-vintage requirement factor is
1.244 × 0.8679 = 1.0797 × the MODEL's weather-year peak, where the market's is
`ICAP req × (1 − derate)` on the NYSRC ICAP-market forecast peak — the same
absolute-vs-ratio class D33/D40 measured for NEISO.

### 1.2 Confounds and scope limits, declared before the run

- **No committed live-stack PJM or NYISO T1-H ledgers exist at HEAD.** The last PJM
  live-posture leg with a committed score is `pjm-2021-2025-realized-verified-exits`
  (2026-08-22, key `4c2c7907805e679b`; retire 18.147 GW / coal 18.137 / recall 0.80 /
  false 7.839; adds wind 3.0 / solar 9.762 / gas_cc 8.118 / gas_ct 1.013 / storage 0.0).
  The last NYISO live-posture leg with committed ledgers is `nyiso-2021-2025-realized`
  (2026-07-14; retire 1.036 GW, all announced nuclear, zero economic exits; adds wind 4.0
  / solar 8.0 / gas_cc 3.0 / gas_ct 4.0 / storage 0.0). HEAD has moved past both (D30,
  D36, D39/D43 gated, D41, D42 gated, perf-b, the entry-rate ladders …), so every
  "vs committed" comparison below is CONFOUNDED by epoch drift and is labelled as such;
  attribution within this lane is **L1 vs L4** (PJM curve vs fixed, one field apart) and
  **L2 vs L3** (NYISO fixed vs curve, one field apart) only.
- **Position projections are a bound, not a forecast** (D40's reading). The PJM positions
  below are D28's instrument rows on the 2026-07-05 ledgers restated on the adopted
  basis (1.142 / 1.196 / 1.183 / 1.100); the NYISO ones are the 2026-07-14 ledgers'
  `firm = peak × (1 + reserve_margin)` identity against HEAD's 1.0797 factor
  (0.957 / 1.149 / 1.241 / 1.141, post-evolution). A fleet the live screens produce will
  differ.
- **The scorer's 2025 window mechanic** (D31 P6): entry decisions in the 2025 screen land
  at COD 2027, outside the scored additions bands.

## 2. PREDICTIONS (graded at full magnitude afterwards)

### P1 — L1 (PJM live posture): every screen year prices capacity at exactly $0

Entering positions (HEAD requirement: 0.8710 × gross peak for 2021–2024 via the composite,
0.9008 × peak in 2025 via the published FPR) land **1.08–1.24 in every screen year**, above
each vintage's published zero-cross (1.064–1.074). Consequently the per-event
`capacity_revenue_usd` is **0.0 for every retirement candidate in every year**, and the
diagnostics dumps' capacity term is 0 for every entry candidate. Falsifier: any screen year
with a strictly positive capacity leg.

### P2 — L1 retirements: the over-fire persists and is coal-monopolised

`retire.total_gw` **14–22 GW, central 18** against 15.062 actual (band FAIL); coal
**13–21 GW** against 10.299 (the whole excess is coal); gas_cc / gas_ct / gas_st / oil
**exactly 0.000 GW** each (against 0.434 / 0.808 / 2.702 / 0.613 actual — the missing
non-coal channel D32/D42 named, untouched by anything this lane runs);
`unit_recall_gt300` ≥ 0.70 PASS; `false_retire` FAIL (≥ 5 GW). Falsifier: coal below
10.3 GW (under-retirement) or any non-coal fossil class above 0.3 GW.

### P3 — L1 vs L4 (the one-field PJM A/B): the curve REMOVES revenue, so the fixed leg retires LESS

At $0 (L1) vs $77.43/kW-yr flat (L4), L4's coal retirements are **lower by 4–15 GW** and
its total lands **3–12 GW** (the FFR-2E fixed leg read 4.106); L4's `unit_recall_gt300`
FALLS (below 0.70 → FAIL). This is the D6 signal reproduced on the live stack: **the
curve-ON leg over-fires relative to the fixed leg**. Falsifier: L4 total ≥ L1 total.

### P4 — the PJM clearing-half reading (stated before the solve)

L1's entering positions sit **within ±5 points of the published OFFERED position**
(1.13–1.22) in 2021–2024 and **≥ 8 points above the published CLEARED position**
(1.04–1.06) in every one of those years. I.e. the model's census is NOT wrong relative to
what PJM's suppliers actually offered; what the model lacks is the intersection of that
offered stack with the VRR curve — the supply half. Falsifier: any 2021–2024 entering
position within 3 points of the cleared position, or more than 8 points from the offered one.

### P5 — L2 (NYISO live posture): the flat $110 pays every candidate through, zero economic exits

`retire.total_gw` **0.9–1.2 GW, central 1.04** (the announced nuclear exit only), band FAIL
at about −30 %; economic retirement events **exactly zero in every year**; per-event
`capacity_revenue_usd` = pmax × UCAP fraction × $110,000 for every candidate that appears
(none should, since none fails). Additions: wind/solar/gas_ct bands FAIL (over-build,
as the 2026-07-14 leg and the FFR-3A-3 band list both read); storage **exactly 0.000 GW**
(the D37-class shut channel, predicted to recur in NYISO). Falsifier: any economic
retirement event, or storage entry > 0.

### P6 — L3 (NYISO curve-ON at HEAD): the +123 % latent arms again, gas_st-led

With the curve consulted at the model's own census position (**1.10–1.30** in
2023–2025, past the 1.12 zero-cross in at least two of the three scored screen years),
the capacity leg collapses to ≤ $10/kW-yr in those years and downstate steam fails its
bar: `retire.total_gw` **2.0–4.5 GW, central 3.0** (the 2026-07-18 probe read 3.318),
**gas_st ≥ 1.5 GW** of it, `false_retire` FAIL (≥ 0.5 frac). Falsifier: L3 total within
0.3 GW of L2 (the curve inert), or the excess led by any class other than gas_st/oil.

### P7 — the NYISO position reading (stated before the solve)

L2's entering positions exceed the published NYCA positions (1.043–1.083) by **+5 to +20
points** in 2023–2025, and the excess decomposes into a REQUIREMENT half (HEAD's
1.0797 × weather-year peak vs the published UCAP requirement 33.4–34.6 GW: the model's
requirement is **1.5–4 GW LOW**) and a SUPPLY half whose sign I do NOT pre-commit
(the base-year fleet's firm ~32 GW sits BELOW the published 2021 UCAP supply of 37.3 GW,
i.e. under-accredited hydro and uncounted SCRs, while the 2023–2025 entry over-build pushes
the later years long). Falsifier: any 2023–2025 entering position below the published one.

### P8 — verdict rows and cross-lane safety

Both bare keys read **HOLD** before and after (FC-3 FAIL both ISOs); FC-7 moves
FAIL → CAVEAT on both bare keys as an INSTRUMENT change (the FFR-3A-3 legs predate
`run_config.json`), never a model improvement; FC-1/FC-8 SKIPPED; FC-2/4/5/6 n/a.
Nothing outside `pjm-t1h` / `nyiso-t1h` and their `-pre-d45` preserves and the two probe
keys moves in `ff-verdicts.json`; the board edit touches the PJM and NYISO blocks only.

### P9 — the two arming questions the owner actually asked (answered on conditions fixed NOW)

- **NYISO — consult the published curve at default?** Recommend ARM only if ALL of:
  (a) L3's `retire.total_gw` lands within the ±10 % band; (b) L3's `false_retire` is in
  band; (c) L3's entering positions are within ±3 points of the published NYCA positions
  in every scored year (i.e. the position is not the artifact P7 predicts). **Any two of
  three is not enough.** I predict none of the three is met, and that the honest reading
  is "position artifact first, curve second" — the FF-3D flip stays withheld and the
  identified repairs (§1.1's three published facts + the supply half) are routed.
- **PJM — does the curve-ON over-fire survive the corrected position?** Adjudicated
  zero-solve on L1's own ledgers: re-evaluate every failing candidate's screen at the
  published CLEARED position's curve price ($57 / $21 / $15 / $14 / $104 per kW-yr by DY).
  Pre-stated reading: it **survives in 2022–2024** (a $14–21/kW-yr leg cannot lift coal
  over a ~$58/kW-yr bar) and **does not survive in 2025** (a $104 leg does). The D6 object
  is therefore the clearing half + the 2025 vintage, not a curve shape. No PJM default
  moves either way.

## 3. Registration plan (frozen here)

Preserve-then-overwrite, the D27/D37 pattern: `pjm-t1h` → preserved verbatim at
`pjm-t1h-pre-d45`, then L1 takes the bare `pjm-t1h`; `nyiso-t1h` → `nyiso-t1h-pre-d45`,
then L2 takes the bare `nyiso-t1h`. L3 registers under its own key
`nyiso-t1h-d45-curveon` and L4 under `pjm-t1h-d45-fixed` — probes are never pointed at a
bare per-tier key (a run must never render a verdict its own score contradicts). Both
bundles' evolution ledgers get the one-bundle `.gitignore` carve-out (the D37 precedent),
the four hindcast sidecars + `VERDICT_MAP` entries + the board blocks land in one chain.

**STOP condition (charter, binding):** if anything beyond the two ISOs' `t1h` keys and
board blocks would move, the session stops and routes it.

## 4. Kills

- **K-a — solve budget.** Priced: PJM ~21 min / 8.8 GB per leg (S-6), NYISO ~7 min.
  Any leg that OOMs or exceeds 2× its price is reported and NOT registered; years are
  never trimmed (rule 16's spirit). L4 is dropped first if the budget binds.
- **K-b — no parameter moves, no field added.** A miss that "wants" a tuned constant is an
  open root-cause item routed onward (rule 21). `capacity_market_clearing_by_iso` ships
  unchanged; NYISO stays absent from it.
- **K-c — rule 22.** Solve years {2021, 2023, 2024, 2025}, 2022 bridged and never scored;
  scoring bounded to 2023–2025; the holdout freeze is untouched; nothing is scored against
  measured H1-2026.
- **K-d — rule 13/14.** The published offered/cleared quantities and the SOM margins are
  VALIDATION observables here; nothing in any leg targets them.
- **K-e — rule 27.** Local edits, exact on-disk bytes pushed; any pushed file ≥ 300 lines
  is blob-verified against the remote before the next commit.
- **K-f — rule 25.** Two ISOs, two separate adjudications, two separate identification
  sources; no parameter or verdict transfers between them or from MISO/NEISO.
