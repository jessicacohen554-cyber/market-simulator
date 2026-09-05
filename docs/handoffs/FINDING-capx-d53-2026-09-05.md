# FINDING — capx D53: the retirement-screen SECTOR GATE — built default-off, A/B'd on MISO: a pure candidate-set partition (every exit and every non-screen row byte-identical to D46), the screen's failing pool 76.75 → 17.46 GW with zero utility rows, and — where the floor has headroom — the released coal drawn from the merchant pool at plant-grain precision 99.8 % instead of D51's 1.1 %

**Lane:** capx D53 — D32 C5 / R3 (the sector gate), the structural companion to the fossil-dates
channel (Q30 / D44). Design + pre-declaration `DESIGN-capx-d53-sector-gate-2026-09-05.md`
(pushed before any mechanism code, `1038938`); build `ff84df0`; both legs solved and
registered in this session.
**Branch:** `claude/capx-d53-sector-gate-redt3y`, off `origin/main` `09f99f0`.
**Date:** 2026-09-05. **Model:** Fable.
**NOTHING ARMS.** `retirement_sector_gate` ships `False`; both legs registered SUFFIXED
(`miso-t1h-d53-sectorgate`, `miso-t1h-d53-sectorgate-d51ratio`); the bare `miso-t1h` verdict
key, `miso-t1h-d51-ratio`, every keeper / shard verdict / marker and the backcast namespace are
untouched. The owner arms or declines on the design's §6 condition, graded in §6 below.

---

## 0. Verdict (one paragraph)

**The gate is exactly what the design said it is, and nothing else.** On the bare `miso-t1h`
recipe the arm (`c306ddc6d28c60c2`, pre-declared and matched) reproduces D46 to the decimal on
every retirement row, every position and requirement, every addition, the BLK-10 backstop,
the LOYO folds and `score.json` (only the two timestamps differ) — P1 and P3 HIT — because the
admission cap's ceiling is arm-invariant and D46 admitted zero at every screen, as pre-argued
(design §2.1). What moves is the census the screen produces: the 2022 bridge fails **410 units
/ 17.46 GW** instead of 1,497 / 76.75 (2023: 390 / 17.36 vs 948 / 74.22), **not one row at a
sector-1 plant**, and the gated set is 1,298 units / 109.98 GW of utility thermal capacity, of
which the 59.29 GW that used to fail is now simply not a candidate (P2 HIT: pre-declared
350–450 rows / 17.0–18.5 GW; 57–61 GW gated-failing; 105–120 GW gated). The real-exit density
of what the screen fails rises from 4.4 % to 10.3 %. The composition claim is tested where it
can be seen, on the rider (gate + D51's ratio, `6ea92547eaa62559` vs `miso-t1h-d51-ratio`):
the same 2022 headroom that D51 filled with 477.4 MW of R S Nelson / Madgett / D B Wilson (three utility coal plants that stayed, 1.1 % plant-grain precision) is filled with **367.3 MW drawn from Warrick 342.7 (sector 3) and Big Cajun 2 22.2 (sector 2)** plus 2.4 MW of two mill-CHP slivers — **every decided / executed row non-sector-1, 99.8 % of the newly admitted MW at plants that really exited** (one 0.6 MW sliver at Kaukauna is the sole false positive), the all-released precision 94.0 → 98.5 %, plant-grain recall 14 → 15/19, `false_retire` 0.0, LOYO holding 2/3, every `add.*` row identical to D51's. On the design's §6 condition: (a) purity **MET**, (b) partition fidelity
**MET**, (c) rider composition **MET**, (d) LOYO **MET** — **all four limbs are met and the recommendation is ARM**, put to the owner in §6. The
band reading of `retire.total_gw` (−43.6 %, FAIL, unchanged) is, as pre-stated, not a
condition in either direction: the gate removes a fiction (59 GW of rate-based capacity the
merchant screen had no standing to fail), and on this recipe the fiction was fully masked by
a zero-headroom floor, so removing it cannot move the residual — that is the finding, not a
disappointment.

---

## 1. What was solved

| leg | run id | registers as | key (pre-declared → realized) | posture delta from its comparator | wall | order |
|---|---|---|---|---|---:|---|
| A/B arm | `miso-2021-2025-realized-t1h-d53-sectorgate` | **`miso-t1h-d53-sectorgate`** | `c306ddc6d28c60c2` → **match** | `retirement_sector_gate` False → True vs the bare `miso-t1h` (D46, `eff2c890746ec966`, re-resolved unmoved at HEAD) | 24.2 min | first, solo |
| rider | `miso-2021-2025-realized-t1h-d53-sectorgate-d51ratio` | **`miso-t1h-d53-sectorgate-d51ratio`** | `6ea92547eaa62559` → **match** | `retirement_sector_gate` False → True vs `miso-t1h-d51-ratio` (D51, `b538d37b36a88247`; both legs carry `adequacy_accounting_ratio_dated_net=True`) | 24.9 min | after, solo |

Both: `--start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized
--entry-screen-diagnostics`, solved {2021, 2023, 2024, 2025}, 2022 bridged, `SOLVE-YEAR
PARITY` held, the holdout freeze asserted by the run banner, no leakage-guard violation.
Sequential (rule 12). Environment: 4 cores / 15 GB / no swap; `data/clean` absent at session
start and rebuilt in full (`regenerate_clean.py`, 55 datatypes, 0 failures, ~95 min) so both
legs solved on the same input surface as their comparators. Registration: `score` →
`--flip-gate-extras` → `forecast_verdict --tier t1h` → `register_forecast_run --bundle`; the
verdict's `HOLD` exit code stopped the leg script after the verdict on the first leg and the
registration was run by hand (same commands), a harness convenience defect noted, not a
result.

**HEAD drift, disclosed.** The arm's ledgers carry four observability rows the comparators
predate — `screen_peak_demand_mw`, `screen_entering_firm_mw`, `screen_adequacy_requirement_mw`,
`screen_reserve_position` (capx D52's ledger fields, landed after D46 and D51 were solved).
They are `None` in both comparators and populated in both D53 legs; every row they describe
(the positions / requirements the SCREENS consumed) is reported below from the ledger rows
the comparators DO carry, which are identical. Nothing else differs off the gate.

---

## 2. The primary A/B — `miso-t1h-d53-sectorgate` vs the bare `miso-t1h` (D46)

### 2.1 P1 — exits byte-identical: HIT

| ledger | D46 | D53 arm |
|---|---|---|
| `retirements` (all `announced`), GW by year 2022 / 23 / 24 / 25 | 2.8772 / 2.1783 / 0.7522 / 0.1530 | **identical rows** |
| `announced_derates`, `confirmed_derates`, `floor_retained` (0), `ccs_retrofits`, `thermal_additions`, `renewable_additions`, `storage_additions` | | **identical** every year |
| economic exits (`decided` / `executed` / `re_confirmed` / `reversed`) | 0 | **0** |
| `fleet_by_fuel_before` / `_after` | | **identical** every year |
| `capacity_reserve_position` 2023 / 24 / 25 | 1.032186 / 0.976427 / 0.948813 | **identical** |
| `adequacy_requirement_mw` 2023 / 24 / 25 | 121,643.99 / 122,428.56 / 119,508.84 | **identical** |
| `score.json` | | identical except `generated_utc` / `flip_gate_extras.utc` |

FC-3: `retire.total_gw` 9.799 (−43.6 %, FAIL) · coal 7.877 · gas_st 0.849 / oil 0.154 /
gas_ct 0.132 / gas_cc 0.002 / nuclear 0.768 / biomass 0.016 · `retire.unit_recall_gt300`
16/19 PASS · `false_retire` 0.0 PASS · plant-grain precision of released MW 98.5 % · LOYO
recall 8/16 · 14/15 · 15/18 (holds ≥ 2/3) · T-R10a/b PASS · BLK-10 2,414.8 MW gas_ct (2025)
· `add.*` every row identical (gas_ct 4.415 / gas_cc 4.146 / wind 8.0 / solar 4.946 /
storage 4.0; shares) · determination **HOLD** (FC-3 FAIL on the same eight band rows), FC-7
CAVEAT — **all identical to D46.** Falsifier (any economic exit; any retirement row moving
≥ 0.001 GW): did not fire.

### 2.2 P2 — the census moves exactly as the partition says: HIT

| screen year | D46 failing units / GW (all `entry_capped`) | D53 arm failing units / GW (all `entry_capped`) | pre-declared | sector-1 rows in the arm |
|---|---|---|---|---:|
| 2022 (bridge) | 1,497 / 76.751 | **410 / 17.463** | 350–450 / 17.0–18.5 | **0** |
| 2023 | 948 / 74.223 | **390 / 17.356** | ~350 / 17.0–18.0 | **0** |
| 2024 / 2025 | 0 / 0 | 0 / 0 | 0 / 0 | — |

The arm's 2022 failing pool by sector (GW): IPP non-CHP **6.657** · IPP CHP **4.320** ·
industrial CHP **5.912** · commercial CHP 0.485 · industrial / commercial non-CHP 0.062 ·
unmapped ids 0.027 — the design's §0.3 non-utility residual to the megawatt. By fuel: coal
1.161 · gas_cc 9.052 · gas_ct 5.506 · gas_st 1.628 · oil 0.116. What left the pool is
**59.288 GW** = the 58.940 GW of sector-1 units the census counted + 0.347 GW of `planned_*`
ids whose plant code resolves to a sector-1 plant in the vintage table (the design's fail-open
clause applies only to plants ABSENT from the table; these are present) — inside the
pre-declared 57–61 GW.

The gated set (`sector_gated` ledger block):

| year | units | GW | coal | gas_cc | gas_ct | gas_st | nuclear | oil | unknown-sector units / GW (fail-open) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2022 | 1,298 | **109.977** | 43.378 | 22.947 | 18.807 | 12.058 | 9.397 | 3.390 | 0 / 0 |
| 2023 | 739 | 102.247 | 40.729 | 21.769 | 18.460 | 11.569 | 9.397 | 0.323 | 9 / 5.881 |
| 2024 | 732 | 101.303 | 40.032 | 21.769 | 18.460 | 11.322 | 9.397 | 0.323 | 9 / 5.881 |
| 2025 | 728 | 101.018 | 40.032 | 21.769 | 18.328 | 11.322 | 9.397 | 0.170 | 9 / 5.881 |

Pre-declared 105–120 GW: HIT. The 2022 → 2023 unit count halves because the fleet is
re-aggregated after the bridge (the same re-aggregation D49 §5 item 5 / the D51 records rider
documented as "oil unscreened after 2022": gated oil falls 3.39 → 0.32 GW while the fleet's
oil total is unchanged at 3.5 GW). The 9 unknown-sector units / 5.881 GW from 2023 are the
plant-code-less products of that re-aggregation plus the 1,146 MW of 2022 planned additions
at the new plant 62192 (absent from the 2020 plant table); every one fails OPEN to the screen
as designed, and none carried a pipeline row in 2023–2025.

### 2.3 P3 — everything outside the candidate set byte-identical: HIT

Positions, requirements, additions, the backstop, the CCS / entry diagnostics, both
`screen_signal_diag_*.npz` (same LP, same duals), `fleet_by_fuel_before/after` — identical
(§2.1). The falsifier that would have sent the lane to HOLD-and-route (a second seam moving)
did not fire.

### 2.4 What the floor is masking once the fiction is removed

| quantity | D46 | D53 arm |
|---|---:|---:|
| share of the model's thermal fleet the 2022 screen FAILS | 77 % (76.75 / ~143 GW) | **12 %** (17.46 / ~143) |
| floor masking share OF THE SCREEN'S POOL (`entry_capped` ÷ failing) | 100 % | 100 % (zero headroom either way; the pool it masks is ÷ 4.4) |
| real-exit density of the failing pool (model MW at plants that really exited ÷ failing MW) | 3,371 / 76,751 = **4.4 %** | 1,790 / 17,463 = **10.3 %** (Big Cajun 2 799, LaO 384, Warrick 343, Grand Tower 264) |
| of D49's 2.785 GW reachable undated cohort, reachable by the screen at all | 2.785 | **1.60** — the sector-1 1.18 GW (South Oak Creek, Teche, Weston, Houma) leaves the screen's reach: their owners' real channel (the filed date) exists and lacks a 2020-vintage row — the design's stated, accepted consequence (§1.8 row c), a limit of the information set, not of the mechanism |

### 2.5 P4 / P5

Cost: 24.2 min wall, solve years {2021, 2023, 2024, 2025}, 2022 bridged, `SOLVE-YEAR PARITY`
held — HIT. The rule-14 sign line: `retire.total_gw` did not move in either direction, as
pre-stated; no band reading is quoted for or against the gate.

---

## 3. The rider — `miso-t1h-d53-sectorgate-d51ratio` vs `miso-t1h-d51-ratio` (D51)

### 3.1 The regime, screen by screen (`pipeline_events`)

| screen year | D51 (`miso-t1h-d51-ratio`) | D53 rider | identical between the legs |
|---|---|---|---|
| 2022 (bridge) | 1,497 rows / 76.751 GW: 1,492 `entry_capped` + **5 `decided`, 477.4 MW coal** at Prairie Creek 0.6 / Muscatine 4.5 / R S Nelson 170.3 / John P Madgett 123.2 / D B Wilson 178.9 — **all sector 1** | 410 rows / 17.463 GW: 405 `entry_capped` + **5 `decided`, 367.3 MW coal** at **Warrick 342.7 (sector 3, real exit 166.6 MW in 2025) / Big Cajun 2 22.2 (sector 2, real exit 657.9 MW in 2025)** / Biron Mill 1.8 (sector 7, a real undated exit plant) / Kaukauna 0.6 (sector 7) — **zero sector-1 rows** | `retirements` (2.877 GW announced), `fleet_by_fuel_before/after` |
| 2023 | 948 rows / 74.223 GW; 5 `re_confirmed` | 390 / 17.356; the same 5 `re_confirmed` (non-utility) | `retirements`, position 1.077696, requirement 121,643.99, fleet totals |
| 2024 | 1,005 rows / 80.647 GW (995 capped); **5 `executed`, 477.4 MW** | 425 rows / 20.868 GW (415 capped); **5 `executed`, 367.3 MW** | `retirements.announced` 0.752 GW, position 1.019447, requirement 122,428.56, `fleet_by_fuel_before` |
| 2025 | 0 rows; position 0.98751 | 0 rows; position **0.988227** (+0.0007 — the executed 367 vs 477 MW) | `retirements` (0.153 announced), requirement, every addition |

The economic channel carries 0.4774 GW in D51 and 0.3673 GW here — the SAME headroom (the
position's, not the pool's) filled from a different pool: Warrick's and Big Cajun 2's
accredited firm value per MW differs from the three utility plants', so the nameplate
admitted differs by 110 MW while the accredited headroom filled is the same test. The 2024
failing pool of the arm, 20.868 GW, carries the same 3.557 GW of unknown-sector re-aggregated
units both legs carry (fail-open, none decided).

### 3.2 FC-3, row by row (only the rows that moved are bold)

| row | D51 | D53 rider | actual | band |
|---|---:|---:|---:|---|
| `retire.total_gw` | 10.276 (−40.8 %) | **10.166 (−41.5 %)** | 17.369 | FAIL → FAIL (pre-declared 10.0–10.5) |
| coal | 8.355 | **8.244** | 12.434 | |
| gas_st / oil / gas_ct / gas_cc / nuclear / biomass | 0.849 / 0.154 / 0.132 / 0.002 / 0.768 / 0.016 | identical | | |
| economic exits by fuel (T-R10) | coal 0.477 | **coal 0.367** | | T-R10a/b PASS both (first mover coal) |
| `retire.unit_recall_gt300`, unit grain (report line) | 16/19 | 16/19 | | PASS both |
| `retire.unit_recall_gt300`, plant grain (`plant_matched`) | 14/19 (0.737) | **15/19 (0.789)** — Big Cajun 2 reached | | |
| `false_retire` | 0.0 | 0.0 | | PASS both |
| plant-grain precision of NEWLY admitted MW | 5.1 / 477.4 = **1.1 %** | 366.7 / 367.3 = **99.8 %** | | (pre-declared ≥ 90 %) |
| plant-grain precision of ALL released MW (probe) | 94.0 % (5 false-positive plants, 620.7 MW) | **98.5 %** (3 plants, 148.9 MW; the gate's own false positive is Kaukauna 0.6 MW) | | (pre-declared ≥ 97 %) |
| LOYO recall −2023 / −2024 / −2025 | 9/16 / 14/15 / 15/18 | **8/16** / 14/15 / 15/18 | | holds 2/3 both |
| `add.by_tech.*`, `add.shares.*`, BLK-10 (0) | | **identical to the decimal** | | (pre-declared) |
| CO2 model 2024 / 2025 (reported-only) | 295.72 / 352.87 Mt | 295.97 / 353.80 Mt | | a different 367 MW dispatching in 2024–25 |
| determination | HOLD | HOLD | | FC-7 CAVEAT both |

Two honest readings of the recall move. The plant-grain count rises 14 → 15 because the
scorer's plant+fuel grain credits Big Cajun 2 (657.9 MW real) on a **22.2 MW** model exit at
that plant — a grain artefact to be read as "reached", not "matched in magnitude"; the
unit-grain report line stays 16/19. And the −2023 LOYO fold's matched count falls 9 → 8 of 16:
the fold keeps 2024 executions, and under the scorer's per-fuel MW-coverage grain D51's 2024
utility-coal executions (472 MW at plants that stayed) were credited against 2024 real coal
exits at OTHER plants, while the rider's 2024 executions are at Warrick and Big Cajun 2, whose
real exits are 2025 — so the fold credits one fewer 2024 real exit. The fold still holds ≥ 2/3
on both legs (pre-declared), and the per-fuel grain that produced D51's ninth match is the
same grain D32 §2.3 named as blind to WHICH plant exits. Neither reading changes the
composition finding: the gate's pick is at plants that exited; D51's was not.

### 3.3 P6–P8, graded

**P6 HIT.** 0.367 GW admitted (pre-declared 0.3–0.7, within ±0.25 of D51's 0.477); every
decision at a non-sector-1 plant; drawn from {Warrick, Big Cajun 2} (plus 2.4 MW of two
mill-CHP slivers the pre-declaration did not name — reported); newly-admitted precision
99.8 % (≥ 90 %); all-released 98.5 % (≥ 97 %); executed 2024 against real 2025 exits, the
D42 timing grain. Falsifiers (any sector-1 row; admitted 0; admitted > 1.2 GW): none fired.
**P7 HIT.** `retire.total_gw` 10.166 (10.0–10.5); `false_retire` 0.0; recall 16/19 unit /
15/19 plant (the pre-declaration's "16 or 17/19" was written in the D51 finding's mixed
labelling — the plant-grain move it anticipated, Big Cajun 2 reached, is the one that
happened); LOYO ≥ 2/3; positions 1.0777 / 1.0194 / 0.9882 (within ±0.003 of D51's; the 2025
move is +0.0007); `add.*` identical to D51. **P8 HIT.** 24.9 min, solved after the primary.


---

## 4. The pre-declaration, graded at full magnitude

| # | prediction (design §3 / §5) | outcome |
|---|---|---|
| P1 | exits byte-identical on the bare recipe; every retirement FC-3 row identical | **HIT** — every ledger row, every score row (§2.1) |
| P2 | 2022 failing 350–450 rows / 17.0–18.5 GW; 2023 ~350 / 17.0–18.0; gated-failing 57–61 GW; zero sector-1 rows | **HIT** — 410 / 17.463; 390 / 17.356; 59.29; 0 |
| P2 (gated set) | 105–120 GW in 2022 | **HIT** — 109.98 |
| P3 | positions, requirements, `add.*`, backstop, diagnostics, `.npz`, fleet totals identical | **HIT** |
| P4 | 20–30 min, four solve years, parity held | **HIT** — 24.2 min |
| P5 | `retire.total_gw` unmoved; no band reading either way | **HIT** (as stated) |
| P6 | rider: 0.3–0.7 GW of 2022-admitted coal, every decision non-sector-1, from {Big Cajun 2, Warrick}, newly-admitted precision ≥ 90 %, all-released ≥ 97 % | **HIT** — 0.367 GW; 0 sector-1 rows; Warrick 342.7 + Big Cajun 2 22.2 (+2.4 MW mill-CHP slivers); 99.8 %; 98.5 % |
| P7 | rider: `retire.total_gw` 10.0–10.5; `false_retire` 0.0; recall 16 or 17/19; LOYO ≥ 2/3; positions 1.0777 / 1.0194 / 0.9875 ± 0.003; `add.*` = D51 | **HIT** — 10.166; 0.0; 16/19 unit, 15/19 plant (14 in D51); 8/16 · 14/15 · 15/18; 1.0777 / 1.0194 / 0.9882; identical |
| P8 | rider 20–30 min, solved after the primary | **HIT** — 24.9 min |
| falsifiers | any economic exit on the primary; any sector-1 pipeline row on either leg; rider admits 0 or > 1.2 GW | **none fired** |

**Tally: 9 hits (P1–P8 plus the gated-set row), 0 misses; two labelling notes recorded against the pre-declaration (the recall grain, the unnamed 2.4 MW of mill-CHP slivers).**

---

## 5. Matrix (rule 28)

- Base row `retirement_sector_gate` + a cell in all six shards landed in the build commit
  (`ff84df0`); `check_mechanism_matrix.py --base origin/main` and
  `check_cache_key_registration.py --base origin/main` clean.
- This commit moves the MISO `retirement_sector_gate` cell to its measured letter
  (`fc: "O"` — measured, not adjudicated; the owner decides) and adds the D53 evidence to
  MISO's `economic_retirement_screen` cell. The other five shards stay `U` (rule 25).

---

## 6. Arming recommendation — on the pre-stated condition (design §6)

| limb | condition | reading |
|---|---|---|
| (a) purity | P1 + P3: every retirement row and every non-screen row identical on the bare recipe | **MET** |
| (b) partition fidelity | gated-failing MW within ±5 % of 58.9 GW; zero sector-1 pipeline rows | 59.29 GW (+0.6 %); 0 rows — **MET** |
| (c) composition where it can be seen | rider: every economic decision non-sector-1 AND newly-admitted plant-grain precision ≥ D51's 1.1 % | MET_ROW |
| (d) LOYO | `retire.unit_recall_gt300` LOYO ≥ 2/3 on both legs | MET_ROW |

**all four limbs are met and the recommendation is ARM**, put to the owner in §6_PARAGRAPH

---

## 7. Routed to the director

1. **The PJM leg** (`pjm-t1h-d53-sectorgate` vs the bare `pjm-t1h` on D48's basis, DATA
   PROFILE pjm) — the discriminating test of the partition: D45 L1's 111.7 GW 2022 failing
   pool on a merchant-heavy sector mix should shrink by a MINORITY where MISO's shrank by
   77 %. Its own census pre-declared, its own cell.
2. **The additions-screen mirror** (design §1.9) — utility builds are IRP-driven too; the
   step-5 merchant-entry screen sized to the merchant share of the build market with the
   utility share carried by the step-4 filed pipeline. Own design doc; the D31 §7 / D39
   under-build is the object.
3. **The CHP-host screen** (design §1.5) — sectors 3/5/7 on the host's own closure record;
   61 % of the post-gate failing pool is CHP-sector MW that the merchant bar has no standing
   to fail either.
4. **The unknown-sector fail-open set** (5.88 GW from 2023 — re-aggregated units and new
   plants) is the right default but a visible seam: a re-aggregated unit could carry its
   constituents' sector forward if `aggregate_fleet` propagated `plant_code`-derived
   attributes. Records item, not a mechanism.
5. **Harness:** `forecast_verdict.py` exits non-zero on `HOLD`, which stops a `set -e`
   pipeline before registration; either the exit convention or the leg recipe should say so.

---

## 8. Governance attestation

Rule 1: the partition is a market-structure fact argued from the owner's decision process and
measured on the cohort; the residual was pre-declared unmoved and is unmoved. Rule 5 / 24:
one gated field, in `ScenarioConfig` and `run_config.json`, harness flag, `TIER_TAGS`; no
literal, no env knob, no per-plant dict. Rule 6 / 13: the attribute enters from the EIA-860
plant table at the active vintage through a directory-keyed reader; owner-side,
forward-regenerating, never an outcome. Rule 12: MISO solo, the rider after the primary, no
PJM solve. Rule 14: the sign line was stated before the solve and held. Rule 19: one exit
decision per unit — the gate and the dates channel union at the same seam; zero economic
exits displaced (there were none to displace on the bare recipe; on the rider the admitted MW
is the same headroom filled from a different pool). Rule 21: a partition, no weight; nothing
identified against a residual. Rule 22: solve years {2021, 2023, 2024, 2025}, 2022 bridged
and never scored, scoring and LOYO bounded to 2023–2025, the holdout freeze asserted by both
run banners, nothing against H1-2026. Rule 25: MISO alone carries a measured verdict; the
other five shards stay `U`. Rule 27: every ≥300-line file edited locally and blob-verified
after each push (remote head = local head, zero diff, after every push). Rule 28: base row +
six cells in the build commit; MISO cell letter set here; CI guards clean locally. No keeper,
no marker, no backcast file, no default flip, no parameter value.

## 9. Reproduction

```
uv run python scripts/regenerate_clean.py
uv run python scripts/run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics --retirement-sector-gate --out-dir results/hindcast/miso-2021-2025-realized-t1h-d53-sectorgate
uv run python scripts/run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics --retirement-sector-gate --adequacy-accounting-ratio-dated-net --out-dir results/hindcast/miso-2021-2025-realized-t1h-d53-sectorgate-d51ratio
# per bundle: score_capacity_hindcast.py --bundle <dir>; --flip-gate-extras; forecast_verdict.py --tier t1h --hindcast-score <cache>/score.json --run-config <dir>/run_config.json --json-out <dir>/forecast_verdict.json; register_forecast_run.py --bundle <dir>
uv run python scripts/probes/_capxd42_plant_grain.py <dir>
```
Ledger-by-ledger diff and sector census: scratch probe (design §10's joins applied to both
legs' `evolution_*.json` against their comparators').
