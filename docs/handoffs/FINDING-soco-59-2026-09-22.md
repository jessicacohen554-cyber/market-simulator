# FINDING — SOCO-59 (2026-09-22): the last failing row has no lever in reach; the 2025 hydro hole is repaired on rule 14 alone, and SOCO's EIA-930 hydro folds pumped-storage discharge

**Lane** SOCO-59 · **DATA PROFILE** soco · **Model** Opus (rule 27 — scope writes `src/` and `scripts/`).
**Control of record** `2026-09-22-soco58-warm-committed` (`results/calibration/soco58_warm_committed`),
rule 29 (b) **form 4**, no control solve.
**Arm** `hydro_backfill_year=2024` + `hydro_eia930_monthly=True`, with
`EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025` registered (`constants.py`). Zero new fields, zero free
parameters.
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-59-2026-09-22.md`, pushed at
`3c5a8967b7f060852c9e541d50f0bb1fa65ef011` before any LP; Addendum A (wrong) and Addendum B (post-hoc
correction) appended to it.
**Run** `2026-09-22-soco59-hydro-split` — owner ruled *promote* 2026-09-23, but a concurrent SOCO hydro-4 promotion landed first; it stays a **registered candidate** (§10).

---

## 1. HEADLINE

1. **The object — 2024 `CC_REGULAR`, +10.42 TWh / +3.84 pp (was +3.97 pp) — is NOT reached, and no
   admissible lever for it exists in this repo.** Stated ex ante, confirmed: the arm's dispatch moves
   **no** scored C1 row.
2. **Candidate (1) was a name swap.** FINDING-soco-58 labels plant 703 "Scherer" and 6257 "Bowen". EIA-923
   Schedule 5, CAMPD and the model's own tranche table all say **703 = Bowen** (100 % bituminous from
   IL/IN/PA/KY, **$5.08/MMBtu** in 2024) and **6257 = Scherer** (100 % Wyoming PRB, **$3.12**). Class and
   delivered price are correct at all six coal plants to ≤ $0.02/MMBtu. There is no coal-price repair.
3. **Candidate (2) is real, and it hid a data-admissibility defect.** SOCO's EIA-930 hydro before the
   2024-07-15 taxonomy cut-over is the combined "Hydropower and Pumped Storage" column and it folds
   pumped-storage **discharge** (soco-data-audit §3.3 excluded folded *pumping* only). Registering SOCO
   in the existing time-split registry repairs the LP's 2025 hydro input **and** SOCO's 2023/2024
   benchmark hydro, through one row.
4. **The keeper was shedding load in 2025.** 8 hours, up to 2,450 MW, 7.9 GWh of unserved energy —
   because 37 of 42 hydro plants were missing from the input. The arm sheds none. (SOCO has no price
   benchmark, so this is reported, not scored: load-weighted 2025 model price $136.18 → $40.15/MWh.)

## 2. CANDIDATE (1) — CLOSED

| id | EIA-923 name | CAMPD name | model name | rank received 2019–24 | 2024 delivered | model |
|---|---|---|---|---|---|---|
| 703 | **Bowen** | Bowen | Bowen | 100 % BIT | **$5.084** | $5.099 |
| 6257 | **Scherer** | Scherer | Scherer | 100 % SUB (WY) | **$3.119** | $3.117 |
| 26 | E C Gaston | E C Gaston | — | 100 % BIT | $6.529 | $6.547 |

The SOCO-58 statement "Scherer's delivered coal is $5.10/MMBtu against Miller's $2.10" describes
**Bowen**. The attestation's disclosure 9 records the correction; SOCO-58's own records are not rewritten.

## 3. CANDIDATE (2) — THE FOLD, MEASURED ON SOCO'S OWN DATA

| test | pre-split column 2021 / 2022 / 2023 | 2025 clean hydro | 2025 hydro + PS discharge |
|---|---|---|---|
| hours above SOCO's 3,317.6 MW conventional nameplate | **6 / 29 / 6** (max 3,873 MW) | **0** | 3 |
| diurnal swing (hourly-mean max/min) | **2.84 / 3.12 / 3.82×** | 2.13× | **3.77×** |
| level | 2023: 8.446 vs 6.815 EIA-923 HY = **+1.63 TWh** | — | PS gross discharge **1.963 TWh** |

SOCO's pumped storage is endogenous (1,306.6 MW), so a pinned pre-split year double-counts it.
`EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025` refuses the pin in 2023/2024 and keeps it in 2025.

## 4. WHAT THE RUN DELIVERED

### 4.1 Gates — every status unchanged

| gate | keeper | **arm** |
|---|---|---|
| determination | `NOT-YET` | **`NOT-YET`** |
| C1 | FAIL · 13/14 · free 9/10 | **FAIL · 13/14 · free 9/10** |
| C2 / C4 / C6 / C8 | PASS | **PASS** |
| C3a / b / c | UNSCORABLE | **UNSCORABLE** |
| `grade_summary` | 5 / 4 / 1 | **5 / 4 / 1** |
| DOF | 7 / 1 residual | **7 / 1** |

### 4.2 Dispatch vs benchmark, decomposed (scoring each run on each bench part)

| row | keeper, old bench | arm, old bench (**dispatch**) | arm, new bench (**+ benchmark**) |
|---|---|---|---|
| 2024 `CC_REGULAR` | +10.42 TWh / +3.97 pp | +10.42 / +3.97 | +10.42 / **+3.84** (vol. margin −2.95 → −2.98) |
| 2023 `ST_GAS` | −6.86 / −2.87 pp | −6.86 / −2.87 | −6.86 / **−2.90** (margin 0.13 → **0.10 pp**; vol. 0.32 → 0.27 TWh) |
| 2023 `CC_REGULAR` | +5.83 / +2.28 | +5.83 / +2.28 | +5.83 / +1.97 |

**All 14 scored C1 rows are identical to 0.01 pp on a common bench.** The benchmark move is SOCO's
2023/2024 hydro actual going 8.4465 / 7.0798 → **6.815 / 6.3014 TWh** (PS-folded EIA-930 swap refused;
EIA-923 HY census kept). The bench part is shared per ISO-year, so this applies to the keeper's
display too once this lands. **2023 `ST_GAS` is now the run's thinnest row at 0.10 pp.**

### 4.3 2025 — every C1 row SKIPPED (preliminary vintage); reported at full magnitude

| class | keeper | **arm** | actual (prelim) | |
|---|---|---|---|---|
| hydro | 0.327 | **5.920** | 6.012 (EIA-930) | the repair |
| CT_PEAKER | 7.711 | **4.717** | 4.998 | +2.71 → −0.28 |
| CC_REGULAR | 111.207 | **110.541** | 110.605 | +0.60 → −0.06 |
| COAL_PRB | 32.098 | **31.593** | 27.445 | +4.65 → +4.15 |
| COAL_BIT | 17.007 | **16.749** | 14.535 | +2.47 → +2.21 |
| **ST_GAS** | 3.178 | **1.957** | 8.656 | **−5.48 → −6.70 (worse)** |

C4 2025: coal r 0.883 → 0.879, NRMSE 0.206 → **0.201**; gas r 0.949 → 0.941, NRMSE 0.083 → **0.097**
(gas family +1.6 % over → −2.4 % under). C8 2025: `ST_GAS` forced share 0.182 → **0.186**; hydro 0.000
(now material); `CT_PEAKER` drops below the 2 % materiality floor and becomes SKIPPED-immaterial (0.0 %
forced either way). C2 2025 (skipped): coal +20.9 % → +19.1 %, gas −1.2 % → −5.1 %.

**Against the lane:** the water also displaces `ST_GAS`, already the model's most under-dispatched class.
**The 2025 coal overshoot is mostly NOT a hydro artifact** — coal falls only 0.76 TWh; SOCO-58's "up
to ~5.7 TWh" was an arithmetic ceiling.

### 4.4 Check E — 2025 per-plant coal (EIA-923 basis)

Σ|model − actual| **8.157 → 7.896 TWh** (−3.2 %). Scherer (6257) −0.471 (2.205 over → 1.733 over);
Bowen (703) −0.252 (**0.670 under → 0.922 under — worse**); Daniel −0.034; Barry −0.007; Miller and
Gaston 0.000.

## 5. PREDICTIONS — 12 CONFIRMED, 1 PARTIAL, 1 FALSIFIED

| # | prediction | outcome |
|---|---|---|
| P1 | 2023/2024 legs byte-identical | **CONFIRMED** — all four sidecars, both years |
| P2 | 2025 hydro 5.90–5.93 | **CONFIRMED** — 5.920 |
| P3 | non-hydro supply −5.2…−5.9 | **CONFIRMED** — −5.59 |
| P4 | class bands (CT, CC, coal, ST) | **CONFIRMED** — −2.99 / −0.67 / −0.76 / −1.22 |
| P5 | Scherer largest coal cut; Miller \|Δ\| < 0.5 | **CONFIRMED** — −0.471; 0.000 |
| P6 | C4 2025 coal 0.185–0.215 | **CONFIRMED** — 0.201 / r 0.879 |
| P7 | C4 2025 gas 0.07–0.13, r ≥ 0.90 | **CONFIRMED** — 0.097 / 0.941 |
| P8 | C8 2025 ST_GAS 0.18–0.26 | **CONFIRMED** — 0.186 |
| P9 | C8 2025 hydro 0.000 | **CONFIRMED** |
| P10 | every status unchanged; 2024 CC_REGULAR unchanged | **PARTIAL** — statuses hold; its share leg moves +3.97 → +3.84 pp on the benchmark side |
| P11 | 2025 coal allocation 7.2–8.1 | **CONFIRMED** — 7.896 |
| P12 | DOF 7 / 1 | **CONFIRMED** |
| P13 | only SOCO's surface row moves | **CONFIRMED** |
| P14 | benchmark `eia923` frame unchanged | **FALSIFIED** |

**P14 is this lane's error, not the mechanism's.** Addendum A's A/B popped the registry row between
two calls in one process; `_hydro_benchmark_is_923_only` is `@lru_cache`d
(`run_calibration_full.py:2908`), so the second call returned the first's answer. Found at
registration by diffing bench parts (one leaf per year: `classFull/hydro`); corrected in Addendum B
with a fresh-process A/B. **Lesson for a successor: any A/B over a registry read through
`run_calibration_full` must run each side in its own process.**

The greedy bracket was right for CT_PEAKER and CC (the LP placed water like the `peak` allocation) but
understated `ST_GAS` (−1.22 vs −0.89) and overstated coal (−0.76 vs −0.85…−0.98) — noisy again, as
SOCO-58 §5 said; the symmetric ±2× bands held.

## 6. RULE 1 / RULE 14

The input was missing 94.5 % of the year's water because a preliminary survey had not collected 37
plants; the repair is the year's own measured series from a column shown clean by three independent
tests, and the guard that makes it admissible also removes PS discharge from SOCO's 2023/2024
benchmark. **If the only argument for this arm were that a 2025 row improves, it would not be taken** —
none is scored, and one (`ST_GAS`) gets worse.

## 7. ROUTED

1. **2024 `CC_REGULAR`** — still the sole failing row, still no admissible input (over-dispatched CC tail:
   Tenaska Lindsay Hill, Central Alabama, Ratcliffe, E B Harris).
2. **`ST_GAS`** — SOCO-54 §4's $1.0–1.7/MMBtu gas-steam vs CT fuel separation, unmodelled; 2023 margin
   now 0.10 pp; 2025 −6.70 TWh.
3. **2025 coal overshoot** (+4.15 PRB / +2.21 BIT) — not hydro; Barry (3) at 6.1× its 2025 actual is the
   largest per-plant piece (stale EIA-860 fleet row, SOCO-56 §3).
4. **D79 fingerprint gap** — a first-time per-ISO row in a by-ISO registry table enters no cache key,
   so SOCO's forecast hydro climatology (7.089 → 7.571 TWh/yr) moved with no key move. No SOCO forecast
   result exists today; flagged for whoever owns `solve_surface`.
5. **SOCO hydro-4's two registered probes** (`2026-09-22-soco-h4-hydro-min`, `-hydro-ror`) solved 2025 on backfill-only
   (6.33 TWh) as a stand-in for this repair; their own RESULT §4.1 says their 2025 legs should re-solve on it before any
   promotion. This lane's repair is the one they name.
6. Inherited, untouched: boundary-refused CC plants 533 / 7946; the tranche half of
   `campd_per_unit_attribution`; `derive_parasitic_load.py` for SOCO coal/steam; the
   `tranche_startup_amortization` governance boundary (SOCO-58 §6) — no owner ruling seen, not re-litigated.

## 8. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: zero.** Three shards, one year each, pinned to `3c5a8967…`, ~8–9 min wall each
  including setup; all archived after fetch + checkout + verification.
- **The control's per-plant layer was recovered at zero LP for the fifth consecutive lane**; all twelve
  committed hourly sidecars byte-identical to the keeper.
- Leg SHAs (provenance only, not a durability claim): 2023 `0ba91f581a2c3655a74a6686f371407098fe9595`,
  2024 `ca09c2772717ab5436e456077c414f3f5cd81db1`, 2025 `52c8f3ce6fcc696fe544dcbc41473e463e609c55`.
- **Retrievability (rule 34 (e)):** the composed bundle `results/calibration/soco59_hydro_split`
  (17 files, rule-15 shape), its sidecar and its run payload are committed on
  `claude/soco-59-cc-regular-5y7z69`. **A promotion from that state costs zero re-solves** once that
  branch reaches `main`. The per-plant layer (`dispatch/`, `floors/`, `unit_hourly_*`) exists only in the
  gitignored legs and on the shard branches; cost any need for it as a ~3 × 90 s re-solve.
- Gate noise, machine-verified: `check_registry_payload_parity` RED **locally only** on six unmapped dirs,
  all this lane's (three recovered control legs, three arm legs), all gitignored with 0 tracked files;
  `audit_keepers` E11 (expected) and E13 × 2 (`soco53g`, now the **twelfth** lane; and this candidate,
  until the owner rules — plus hydro-4's two probes once `main` is merged); 30 unit-test failures in `tests/unit/{data,config}`, identical set on `main`.

## 9. THE PROMOTION QUESTION (rule 31)

**Recommendation: promote**, on rule 14 — it removes a 5.6 TWh input hole and 8 hours of spurious load
shedding, and repairs SOCO's benchmark hydro, with zero free parameters and no scored status moving.
**Against it:** it buys no gate, it worsens 2025 `ST_GAS` (ungated) and Bowen's allocation, and the
benchmark repair thins 2023 `ST_GAS` to 0.10 pp — though that last effect lands whether or not the run is
promoted, because the registry row and the shared bench part are in this PR.

**And the standing E13, twelfth lane:** `2026-09-20-soco53g-prb-own-iso` still awaits a ruling. The
standing recommendation is to **decline** it so the next promoting session can prune it.

---

## 10. THE PROMOTION — RULED, THEN SUPERSEDED BY A CONCURRENT PROMOTION

The owner ruled, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."* This lane recommended it on rule 14 and executed the promotion on its branch. On rebasing onto `main` (2026-09-23), SOCO's keeper had meanwhile been re-designated by the SOCO hydro-4 lane to **`2026-09-22-soco-h4-hydro-ror`** (`hydro_ror_split`), which also pruned `soco58`. Two single-delta promotions off the same control cannot both be the keeper, and this lane does NOT overwrite another lane's designation: the rebase keeps `main`'s keeper, and `2026-09-22-soco59-hydro-split` remains registered as a candidate (audit_keepers E13 by design, rule 31).

**The two deltas compose; neither is complete alone.** h4-ror's 2025 legs ran on backfill-only hydro (6.33 TWh, 2024's shape) as a stand-in for this lane's repair — its own RESULT §4.1 says they must re-solve on it — and it carries no `EIA930_PS_SPLIT_COMPLETE_FROM['SOCO']` guard in its recorded surface. The registry row is now on `main` via this branch regardless. **Next step: one combined span = h4-ror recipe + `hydro_backfill_year=2024` + `hydro_eia930_monthly=true`, three shards (~10 min each), promoted over h4-ror; then prune this candidate.** 2023/2024 of that span are predicted byte-identical to h4-ror's (the pin is refused there).

## Log entry

```
## soco-59 — 2026-09-22

THE LAST FAILING ROW HAS NO LEVER IN REACH, AND THIS LANE SAID SO BEFORE IT
SOLVED ANYTHING. 2024 CC_REGULAR (+10.42 TWh; share +3.97 pp on the old bench,
+3.84 on the new) is capacity-bound (SOCO-56) on measured heat rates (SOCO-57),
and neither named candidate reaches it.

CANDIDATE (1) WAS A NAME SWAP. FINDING-soco-58 labels plant 703 "Scherer" and
6257 "Bowen". EIA-923 Schedule 5, CAMPD and the model's own tranche table all
give 703 = BOWEN (100 % bituminous from IL/IN/PA/KY, $5.08/MMBtu in 2024) and
6257 = SCHERER (100 % Wyoming PRB, $3.12). Class and delivered price are right
at all six coal plants to <= $0.02/MMBtu. No coal-price repair exists.

CANDIDATE (2) IS REAL AND HID A DATA-ADMISSIBILITY DEFECT. The keeper's 2025
hydro was 0.327 TWh (5 of 42 plants in the preliminary EIA-923 vintage) against
5.926 measured. The fix is the NEISO/MISO construction, hydro_backfill_year=2024
+ hydro_eia930_monthly=true -- but that pins EVERY year, and SOCO's pre-split
EIA-930 hydro (the combined "Hydropower and Pumped Storage" column, to the
2024-07-15 cut-over) FOLDS PUMPED-STORAGE DISCHARGE. soco-data-audit §3.3's
"never negative" excluded folded PUMPING only. Measured on SOCO's own data: the
pre-split column exceeds SOCO's 3,317.6 MW conventional nameplate in 6/29/6 h of
2021/2022/2023 and 0 h after the split; its diurnal swing is 2.84-3.82x against
2.13x for clean hydro and 3.77x for clean hydro + PS discharge; the 2023 gap to
the EIA-923 HY census, 1.63 TWh, matches 2025's 1.963 TWh of PS discharge.
EIA930_PS_SPLIT_COMPLETE_FROM gains SOCO: 2025 (the neiso-72 design).

RESULT (run 2026-09-22-soco59-hydro-split, CANDIDATE, three per-year shards
composed at zero LP). 2023 and 2024 BYTE-IDENTICAL to the keeper. 2025 hydro
0.327 -> 5.920 TWh, displacing CT_PEAKER -2.99, ST_GAS -1.22, coal -0.76,
CC_REGULAR -0.67 TWh, and ending 8 HOURS OF LOAD SHEDDING (up to 2,450 MW,
7.9 GWh) the hole was causing in the keeper. Every status unchanged: NOT-YET,
C1 13/14 / free 9/10, C2/C4/C6/C8 PASS, grade 5/4/1, DOF 7/1. The arm's DISPATCH
moves no scored C1 row (all 14 identical to 0.01 pp on a common bench). The
same registry row moves SOCO's 2023/2024 BENCHMARK hydro 8.4465/7.0798 ->
6.815/6.3014 TWh (the PS-folded swap refused), shifting share legs by <= 0.31 pp:
2023 ST_GAS -2.87 -> -2.90 pp, now the thinnest row at 0.10 pp. 2025 (ungated):
C4 coal NRMSE 0.206 -> 0.201, gas 0.083 -> 0.097; ST_GAS -5.48 -> -6.70 TWh
(WORSE); the 2025 coal overshoot falls only 0.76 TWh -- SOCO-58's "up to ~5.7
TWh" was an arithmetic ceiling, and the overshoot is mostly NOT hydro.

PREDICTIONS 12 CONFIRMED / 1 PARTIAL / 1 FALSIFIED. P14 (benchmark unchanged)
was falsified by this lane's own error: its A/B popped the registry row between
two calls in one process, and _hydro_benchmark_is_923_only is @lru_cache'd, so
the second call returned the first's answer. Caught at registration by diffing
bench parts; corrected post-hoc in PRECOMMIT Addendum B. Any A/B over a registry
read through run_calibration_full must run each side in its own process.

ROUTED: 2024 CC_REGULAR (no admissible input); ST_GAS fuel separation; the 2025
coal overshoot (Barry 6.1x); a D79 fingerprint gap -- a first-time per-ISO row
enters no cache key, so SOCO's forecast hydro climatology moved 7.089 -> 7.571
TWh/yr with no key move (no SOCO forecast result exists). OWNER RULED PROMOTE 2026-09-23, but the
concurrent hydro-4 promotion (keeper 2026-09-22-soco-h4-hydro-ror) landed first; this run stays a
candidate and the next step is a combined h4-ror + hydro-repair span.
E13 for 2026-09-20-soco53g-prb-own-iso re-raised for the TWELFTH lane
(recommendation: decline). Control per-plant layer recovered at zero LP for the
fifth consecutive lane. Records: docs/handoffs/PRECOMMIT-soco-59-2026-09-22.md,
docs/handoffs/FINDING-soco-59-2026-09-22.md, scripts/gen_soco59_attestation.py,
scripts/probes/soco59_compose_span.py, scripts/probes/_soco59_phase0.py,
scripts/probes/_soco59_rule19.py.
```
