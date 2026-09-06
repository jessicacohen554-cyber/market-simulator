# PRE-DECLARATION — capx D58: the retirement-screen SECTOR GATE on PJM, the DISCRIMINATING leg of D53

**Lane:** capx D58 — the PJM leg of the sector gate D53 built and measured on MISO, named by
D53 §7 item 1 / design §7 as **the discriminating test of the partition**. D53 partitioned the
screen's candidate set on the published EIA-860 `Sector` attribute (sector 1 = electric utility
exits only through step 0's instrument channel and step 1/1b's filed-date channel; every other
sector faces the merchant screen). On MISO the failing pool fell **76.75 → 17.46 GW (−77 %)**
with zero sector-1 rows and every exit byte-identical. PJM's sector mix is the inverse, so the
pool should shrink by a **MINORITY**. This document fixes that claim in numbers before any LP.

**Branch:** `claude/capx-d58-pjm-sectorgate-v0b9fa`, fresh off `origin/main` `6887484f`.
**Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.
**Pushed BEFORE any solve.** Graded at full magnitude in `FINDING-capx-d58-2026-09-06.md`,
misses included.

**NOTHING ARMS.** No mechanism code is written (D53 built it; if PJM needs a seam D53 did not
build, this lane STOPS and routes). No keeper, no shard verdict beyond PJM's own
`retirement_sector_gate` cell, no marker, no default flip, no parameter value. The arm registers
**suffixed** (`pjm-t1h-d58-sectorgate`); the bare `pjm-t1h` verdict key is untouched. Rules 1,
12, 13, 14, 19, 21, 22, 24, 25, 27, 28d, 29 hold (§8).

---

## 0. Preconditions, checked

| precondition | reading |
|---|---|
| `retirement_sector_gate` in `ScenarioConfig` on `origin/main` (D53 merged) | **PASS** — `scenarios.py:15737`, default-off, registered in the optional-cache-key fields at `"False"` (`:2001`) |
| `capacity_market_supply_clearing_by_iso` on `origin/main` (D57 landed) | **PASS** — `scenarios.py:15854`; **armed for PJM** through `iso_configs._pjm_config` `default_scenario_overrides` |
| D60-R3 merged (#5038) | **PASS** — `83f77bea`, and the director's r#46 am.1 note `0d688e85` records it |

**The posture this lane runs on, stated (D57 / Q42 / Q44).** PJM's `default_scenario_overrides`
at HEAD carry three fields — `pjm_accreditation_design_vintage: True`,
`pjm_demand_response_supply: True`, `capacity_market_supply_clearing_by_iso: {"PJM": True}` —
so the bare `pjm-t1h` recipe **already clears the fleet's net-ACR sell-offer stack against the
delivery year's published VRR curve**, and the screen's failing set IS the auction's uncleared
set. `ccs_retrofit_capex_co2_scaling` is at its D60/Q42 default `True` and is inert below
`ccs_retrofit_available_year` (2028), so it cannot touch a 2021–2025 hindcast. This is a
materially different screen from the one D45 L1 measured, and §2 says so where it matters.

---

## 1. Disclosure — what was computed before this text, and from what (ZERO solves)

Everything in §2 was read from **committed artifacts only**: the D57 arm A hindcast ledgers
(`results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a/evolution_*.json`
and its `score.json`), the EIA-860 `vintage_2020` plant + generator tables, and the committed
scoring target `data/raw/_validation-source/capacity_actuals_pjm.csv`. No LP, no screen, no
evolution was run; the fleet loader was not called. Instrument:
`docs/handoffs/d58/census_probe.py` → `census_probe.json` (committed with this text).

The join reconstructs the gate's own key, `Generator.plant_code`, from both fleet grains PJM
carries: CAMPD-binned tranches (`..._p<code>_<tranche>`) and the legacy per-unit rows PJM's oil
and gas_ct fleet uses (`<code>_<generator>`) — D53 design §10's two shapes.

**§0.1 equivalence re-checked at this vintage** (D53 §0.1, on the whole plant table):
**3,587 / 3,587 sector-1 plants are `RE`; 0 are `NR`**; the only `RE` plants outside sector 1
are 16 commercial / industrial self-generators (sectors 4/5/7). The gate keys on `Sector` alone
(rule 19), and the equivalence holds unchanged.

---

## 2. The PJM census — the discriminating numbers

### 2.1 The PJM fleet by sector (EIA-860 2020 vintage, BA = PJM, operable, nameplate MW)

| fuel | sector 1 | 2 | 3 | 4 | 5 | 6 | 7 | sector-1 share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| coal | 18,824 | 29,813 | 991 | 0 | 0 | 0 | 267 | 0.377 |
| gas_cc | 9,168 | 44,949 | 1,770 | 0 | 80 | 0 | 80 | 0.164 |
| gas_ct | 7,935 | 21,148 | 234 | 140 | 259 | 13 | 511 | 0.262 |
| gas_st | 1,691 | 9,016 | 178 | 130 | 27 | 18 | 350 | 0.148 |
| nuclear | 5,940 | 28,527 | 0 | 0 | 0 | 0 | 0 | 0.172 |
| oil | 978 | 3,901 | 166 | 4 | 18 | 4 | 24 | 0.192 |
| **total** | **44,536** | **137,354** | 3,339 | 274 | 384 | 36 | 1,232 | **0.238** |

**PJM is 23.8 % sector-1; MISO is 80.2 %.** The merchant IPP fleet (sector 2) is **73.4 %** of
PJM's operable thermal nameplate where it is 11 % of MISO's. This is the inverse mix D53 §7
predicted from the ex-Exelon / Vistra / Talen / LS Power ownership record, measured rather than
asserted.

### 2.2 What the bare recipe's screen fails, by sector (D57 arm A, key `f0e050e820c1159a`)

The failing set of a screen year is its `decided` rows (admitted by the reliability floor's
admission cap) **plus** its `entry_capped` rows (failed the bar, retained by the floor).
`executed` / `re_confirmed` / `reversed` are pipeline follow-ups on earlier decisions.

| screen year | failing rows / MW | sector 1 | 2 | 3 | 4 | 5 | 6 | 7 | sector-1 share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **2022** (bridge) | 429 / **20,788.5** | **2,676.8** | 17,252.2 | 373.1 | 82.7 | 41.5 | 21.1 | 341.2 | **12.88 %** |
| **2023** | 151 / **4,384.3** | **622.7** | 3,230.4 | 164.5 | 0 | 29.9 | 11.8 | 325.1 | **14.20 %** |
| 2024 / 2025 | 0 / 0 | — | | | | | | | — |

By fuel at the 2022 screen (MW, sector-1 / other): coal 1,225.8 / 4,608.8 · gas_cc 221.9 /
1,938.1 · gas_st 771.2 / 8,559.7 · oil 457.9 / 2,871.5. **Zero unknown-sector rows** in either
year — every failing unit's plant resolves in the 2020 table, so PJM has no fail-open residual
to report (MISO carried 0.37 GW in 2022 and 5.88 GW from 2023).

**The screen fails PJM's sectors close to the fleet's own proportions** (12.9 % of the failing
pool vs 23.8 % of nameplate), the same ownership-blindness D32 named — but at a quarter of
MISO's level, because PJM's fleet is a quarter as utility-owned.

### 2.3 THE FLOOR HAS HEADROOM — and PJM is the first ISO where it does

This is the structural fact that separates this leg from D53's primary, and it was the
charter's stated reason to expect an observable composition effect on the PRIMARY leg (D48 §3.3:
the PJM admission cap admitted +1.4 GW between arms).

| screen year | failing MW | **admitted (`decided`)** | capped | admitted share |
|---|---:|---:|---:|---:|
| 2022 | 20,788.5 | **13,168.3** | 7,620.2 | **63.3 %** |
| 2023 | 4,384.3 | **4,384.3** | 0.0 | **100 %** |

MISO's floor admitted **zero** at every screen, which is why D53's primary could not adjudicate
composition and needed the D51 rider. **PJM's floor admits 13.2 GW in 2022 and its entire
failing pool in 2023.** The gate's composition effect is therefore observable on the primary
leg here, with no rider — and this leg carries no rider for that reason.

The two years are structurally different regimes and must be predicted separately:

- **2022 — a BINDING cap with 7.6 GW of capped pool behind it.** Removing 2,676.8 MW of
  sector-1 candidates (of which **1,694.2 MW was admitted**) frees admission budget that the
  cap **re-fills cheapest-firm-first from the remaining merchant pool**. This is exactly the
  D53 rider's mechanic (MISO: 477.4 → 367.3 MW — the same headroom, a different pool). The
  admitted MW should therefore stay near 13 GW and become **all non-sector-1**, not fall by
  1.69 GW.
- **2023 — a NON-BINDING cap: zero capped pool, nothing to backfill with.** Gating can only
  REMOVE. The admitted MW should fall by close to the full **622.7 MW** of sector-1 candidates.

### 2.4 The real PJM exit cohort by sector (committed target, 2021–2025)

| fuel | exited MW | sector-1 share | MISO's (D53 §0.4) |
|---|---:|---:|---:|
| coal | 10,298.7 | **0.102** | 0.88 |
| gas_st | 2,701.7 | 0.330 | 0.90 |
| gas_ct | 808.2 | 0.005 | 0.87 |
| oil | 612.5 | 0.063 | 0.92 |
| gas_cc | 433.9 | 0.000 | 0.07 |
| biomass | 207.4 | 0.097 | 0.02 |

**PJM's real coal exits are 10 % utility-owned where MISO's are 88 %.** The partition's premise —
that a filed date, not a merchant margin, is the utility exit channel — costs PJM almost nothing
in reachability: where the MISO gate put 1.18 GW of D49's reachable cohort beyond the screen's
reach, PJM's utility cohort is 1.05 GW of coal across the whole window and the merchant channel
keeps 90 % of the coal it needs to find. (Two coal rows totalling 728.0 MW carry a plant code
absent from the 2020 table and are counted `unknown`, neither sector-1 nor merchant.)

### 2.5 What the control's release looks like today (the composition baseline)

From the committed `score.json` (`plant_release_precision`, plant-code+fuel grain, reported-only
per D32 R4) and the admitted rows joined to the real-exit plant set:

| quantity | control (D57 arm A) |
|---|---:|
| `retire.total_gw` model / actual / err | 18.702 / 15.062 / **+24.2 %, FAIL** |
| per-fuel: coal / gas_st / gas_cc | 6.016 (−41.6 %) / 10.297 (**+281 %**) / 2.328 (+437 %) |
| `false_retire` | **9.490 GW**, 50.7 % of model, FAIL |
| `unit_recall_gt300` | 12/20 = 0.60 FAIL (plant grain 14/20 = 0.70) |
| window **economic** released MW / precision | 12,159.2 / **11.6 %** |
| window **all** released MW / precision | 18,702.1 / 40.7 % |
| LOYO recall −2023 / −2024 / −2025 | 0.583 / 0.579 / 0.579, `holds_2of3` **False** |
| 2022 admitted: sector-1 MW / its plant-grain precision | 1,694.2 / **0.5 %** |
| 2022 admitted: non-sector-1 MW / its precision | 11,474.1 / **29.0 %** |
| 2023 admitted: sector-1 MW / its precision | 622.7 / **18.9 %** |
| 2023 admitted: non-sector-1 MW / its precision | 3,761.6 / **0.9 %** |

**Two honest readings, both stated before the solve.** In 2022 the sector-1 block the gate
removes is very nearly pure false-positive (0.5 % — Mt Storm 465.9 MW and Clinch River 460.0 MW,
neither of which exited), so gating should *raise* release precision there. In **2023 the sector-1
block is the BETTER block** (18.9 % vs the merchant pool's 0.9 %, carried by Chesterfield 98.0 MW
against a real 1,052.9 MW exit): gating **removes the more precise cohort in that year** and
2023 precision should FALL. The lane pre-declares both directions rather than only the flattering
one; the MW-weighted net across the two screens is the graded quantity (§3 P6).

---

## 3. The pre-declaration

**Primary A/B:** bare `pjm-t1h` at HEAD **+ `--retirement-sector-gate`** vs a **same-HEAD
control**, full span `--start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized
--entry-screen-diagnostics`. PJM solo, years sequential (rule 12).

### P1 — THE MINORITY CLAIM (the discriminating prediction, in numbers)

The screen's failing pool falls by the **sector-1 share and no more**:

| screen year | control failing MW | **arm, predicted** | fall | MISO's fall |
|---|---:|---:|---:|---:|
| 2022 | 20,788.5 | **17,600 – 18,600** | **−11 % to −15 %** | −77 % |
| 2023 | 4,384.3 | **3,650 – 3,900** | **−11 % to −17 %** | −77 % |

Point estimates 18,111.7 and 3,761.6 MW (the measured post-gate residuals), banded for the
fleet-re-aggregation and pipeline-state differences a re-solve introduces.
**Falsifier: either year's failing pool falling by more than 30 % or less than 5 %.** A fall
near MISO's 77 % would mean the gate is not reading PJM's own ownership record and the
partition is not the attribute this design says it is.

**Zero sector-1 rows** in any `pipeline_events` row of any year, and **zero unknown-sector
rows** (PJM's failing pool resolves completely at the 2020 vintage). Falsifier: any of either.

**The gated set** (`sector_gated` ledger block) is **36 – 46 GW** of PJM utility thermal
capacity in 2022 (the 44.5 GW EIA spine at the model's fleet coverage), of which the
**2.5 – 2.9 GW that used to fail** is now simply not a candidate.

### P2 — the two headroom regimes behave differently, as §2.3 argues

- **2022 (binding cap):** admitted MW **11.5 – 14.5 GW** — i.e. the cap **re-fills** rather
  than losing the 1,694.2 MW of gated-out admission; **every admitted row non-sector-1**.
  Falsifier: admitted falling below 10.5 GW (the cap did not re-fill — a second seam moved), or
  any sector-1 admitted row.
- **2023 (non-binding cap):** admitted MW **3,650 – 3,900**, i.e. down by ≈ 622.7 MW with no
  backfill; **every admitted row non-sector-1**; `entry_capped` stays 0.
  Falsifier: admitted ≥ 4,300 MW (a backfill that has nothing to draw on), or any capped row.

### P3 — composition: the MW-weighted release precision RISES, and 2023's falls

Newly-measured on the arm against the control, `plant_release_precision`:

- **window `economic` precision RISES** from the control's **11.6 %** to **13 – 20 %**;
- **per-year 2022 `economic` precision RISES** from 18.5 % to **20 – 30 %**;
- **per-year 2023 `economic` precision FALLS** from 1.2 % to **0.0 – 1.2 %** — the honest
  countersignal of §2.5, pre-declared;
- **window `all` precision** 40.7 % → **40 – 50 %**.

Falsifier: window `economic` precision falling below the control's 11.6 %. That would mean the
partition makes the floor's pick **worse** than ownership-blind selection, which §6 reads as
DECLINE.

### P4 — everything outside the screen's candidate set is unchanged

Every `add.*` FC-3 row, `renewable_additions`, `storage_additions`, `announced_derates`,
`confirmed_derates`, `ccs_retrofits` (zero in-window; the D60 flip is inert below 2028), the
reserve-margin backstop, and both `screen_signal_diag_*.npz` — **identical to the control**,
because the gate is a candidate-set partition and the LP is the same LP. Falsifier: any of these
moving — that is a SECOND seam and §6 reads HOLD-and-route.

*(Unlike MISO, the `retirements` rows and the positions CANNOT be predicted identical here: the
floor has headroom, so the gate changes which units exit and therefore the fleet the next year
enters with. That is the point of this leg.)*

### P5 — the rule-14 sign line, STATED BEFORE THE SOLVE

**A gate can only REDUCE the set of units the economic screen may retire.** It removes
candidates; it never adds one. So economic exits can only fall or stay, and
`retire.total_gw` can only move **DOWN** — predicted **17.9 – 18.7 GW** (from 18.702), driven
mostly by 2023's un-backfilled 622.7 MW.

**PJM's control OVER-retires** (+24.2 %, `false_retire` 9.490 GW, 50.7 % of model). So here,
unlike MISO, a reduction moves the band **toward** the actual and `false_retire` **down**
(predicted **8.5 – 9.5 GW**). **This is NOT a criterion and is NOT why the mechanism is being
tested** (rules 1, 14): the gate is adjudicated on the partition's fidelity and on composition,
per §6, and a band that improved would be a *consequence* reported at full magnitude, never
evidence for the partition. Symmetrically, **if `retire.total_gw` or `false_retire` got WORSE
that would not be evidence against it** — that is the pre-declared signature D53 §3 P5 named of
a screen that had been retiring utility units for a reason their owners never faced.
`retire.total_gw`'s band reading is **not a condition in either direction**.

`unit_recall_gt300` is predicted **11–13 / 20** (from 12/20): the gate removes candidates, so
recall can fall if a gated sector-1 plant was a matched large exit. **A recall fall is not a
falsifier** for the same rule-14 reason; it is reported.

### P6 — cost, and the rule-29 screen

See §4. Screen ≈ 7–9 min per arm; full span ≈ 13–16 min per arm (D57/D67 measured PJM at
12–15 min for the 2021–2025 span on this box: 4 cores / 15 GB).

---

## 4. Rule 29 `[R-SCREEN]` — the screen, named before it runs

**Phase 0 (zero LP) is DONE and is §2** — the census, the cache keys (§5) and the drift audit
(§6) are the pre-solve gate, and they cost ~3 minutes rather than an LP.

**The screen year is 2023** — **the year the sector-1 share of the failing pool is largest**
(14.20 %, vs 2022's 12.88 %), from the census of §2.2 and **never from the residual**. Because
the 2023 screen prices on the 2022 bridge which prices on the 2021 seed, the screen span is
**`--start-year 2021 --end-year 2023`**: solve years {2021, 2023} with 2022 bridged — the
charter's two-year minimum, and it carries **both** screens (2022's largest-MW footprint and
2023's largest sector-1 share).

**The screen gate is STRUCTURAL and a STOP gate only.** It asks whether the mechanism does what
its own arithmetic says, and it may kill an arm but never promote one. It is **not** gated on
`retire.total_gw`, `false_retire`, recall, or any residual:

| # | screen gate (all must hold to proceed to the full span) |
|---|---|
| S1 | **Zero sector-1 rows** in any `pipeline_events` row of 2021–2023, and zero unknown-sector rows |
| S2 | 2022 failing pool falls **5–30 %** (the minority claim's direction and order of magnitude) |
| S3 | 2023 failing pool falls **5–30 %**, admitted falls by **400–850 MW**, `entry_capped` stays **0** |
| S4 | 2022 admitted stays **≥ 10.5 GW** (the cap re-fills; the identity "the gate frees budget the cap re-spends" holds) |
| S5 | No **non-target** load-bearing row flips: every `add.*` row, both `.npz`, the derates and the backstop identical to the same-span control (P4's footprint claim) |

**A screen that kills the arm is reported as the session's result and the remaining years are
never spent.** The screen bundle is a **throwaway diagnostic probe** — never registered, never
a keeper, never quoted as a keeper number, its years re-solved inside the full bundle — and it
is **DELETED from `results/calibration/` and `results/hindcast/` before the PR merges**
(rule 29(c)). Every number this lane will ever cite from it is in this document and the FINDING.

---

## 5. Cache keys, resolved through the harness path at HEAD

`run_capacity_hindcast.build_config(iso="PJM", start_year=2021, end_year=…, variant="realized",
vintage=2020, entry_screen_diagnostics=True)` → `iso_configs.apply_iso_scenario_defaults(·,
"PJM")` → `cache_key()`. Instrument `docs/handoffs/d58/keys_probe.py` → `keys_probe.json`.

| config | key | check |
|---|---|---|
| **control**, bare `pjm-t1h` at HEAD, full span | **`aef81c84c4609c76`** | **known-answer HIT** — the D67 lane independently measured this same value at its own base (`FINDING-capx-d67` §1(b)) |
| **arm**, + `retirement_sector_gate=True`, full span | **`f546407cf3489761`** | no collision under `results/`, `frontend/`, `docs/`, `src/`, `scripts/`, `tests/` |
| screen-span control (2021–2023) | **`e47fee08f5f37d6f`** | no collision |
| screen-span arm (2021–2023) | **`0265ce2b262ad37f`** | no collision |
| *anchor:* D57 arm A committed bundle | `f0e050e820c1159a` | **does NOT match the HEAD control** — moved by D60/Q42's declared `ccs_retrofit_capex_co2_scaling` flip, the attribution D67 §1(b) proves by reverting it |

**K-a:** any collision, or a realized key ≠ its value here unexplained from the resolved config
→ STOP for that leg.

---

## 6. G-DRIFT (rule 29(b)) — and why form 4 is VOID here

**G-CTRL form 4 (difference the arm against the incumbent keeper's committed numbers) is VOID
for this lane, and the charter says so with measured evidence rather than a heuristic.** The
committed control (D57 arm A, `f0e050e820c1159a`) is **PRE-hunk** on SCN-LOAD `d14a7ed0`, which
moved `DEMAND_GROWTH_RATES["PJM"]["mid"]["near"]` **0.036 → 0.064645** — verified in the diff
`5bb70047..HEAD` on `constants.py`. Because the capacity screen's seam peak is built from
`_scale_demand` on the **growth** path, the D67 lane measured that one line moving the PJM T1-H
screen peak by **−10,819 / −7,574 / −3,977 / 0 / +4,386 MW** across 2021–2025. A screen peak that
moves is a screen requirement that moves, which is the admission cap's own budget — the exact
quantity this lane differences. That hunk is **LIVE**, and the key arithmetic agrees
independently: the HEAD control key `aef81c84c4609c76` ≠ the committed `f0e050e820c1159a` (§5).

**Consequence, per rule 29(b): a same-HEAD control is EARNED and will be solved** for the screen
span and for the full span, and the arm-vs-control differencing is then exact and drift-immune by
construction. A matched cache key would not have been a G-DRIFT verdict, and no key matched
anyway.

**The one hunk the charter names classified: #5033 (`37f994fd`, the same-year P1 basis seed on
`pipeline/solve.py`) is INERT for this lane**, on three independent grounds, verified in code at
`solve.py:474-477` rather than from the docstring:

1. **Forecast path.** The seed requires `xyear_warmstart is None`. `run_capacity_hindcast` builds
   `mode="forecast"` (confirmed in the committed D57 `run_config.json`), and the forecast passes
   an explicit `ScenarioConfig.forecast_xyear_warmstart` bool — so the gate is False and nothing
   is exported or applied.
2. **The env var is never set on this path.** `MARKET_SIM_P1_BASIS_SEED` defaults `"0"` globally
   and only `scripts/run_calibration_full.py` flips it (`resolve_p1_basis_seed_default`);
   `run_capacity_hindcast.py` never references it.
3. **Basis-independence.** Even where armed it changes the solve path only — the LP optimum, and
   therefore the cleared prices and generation, are basis-independent.

The audit is recorded here, before the arm is solved, so it cannot be written to fit the result.
It is **not** used to revive form 4 — form 4 is void on the SCN-LOAD hunk and the control solve
settles the question directly.

---

## 7. The P9-style flip condition — the arming recommendation, PRE-STATED

Recommend **ARM for PJM** (`retirement_sector_gate: True` in `iso_configs._pjm_config`
`default_scenario_overrides` — rule 25, PJM's own evidence for PJM's own posture; a
ScenarioConfig default flip is a broader act and is **not** recommended from this leg) **iff ALL
of**:

- **(a) purity of footprint** — P4 holds: every non-screen row (`add.*`, derates, backstop,
  both `.npz`) identical to the same-HEAD control. The gate is a candidate-set partition and
  touches no second seam.
- **(b) fidelity of the partition** — P1 holds: **zero** sector-1 rows in any pipeline event,
  and both years' failing pools fall inside **5–30 %** — the MINORITY the ownership record
  predicts, not MISO's 77 %.
- **(c) composition** — P3 holds: the **window `economic` release precision does not fall below
  the control's 11.6 %**, and every admitted/decided/executed row is at a non-sector-1 plant.
  This is the leg's substantive test, and PJM can run it on the PRIMARY because its floor has
  headroom (§2.3) — the thing MISO needed a rider for.
- **(d) LOYO** — `retire.unit_recall_gt300` LOYO does not lose a fold it currently holds. *(The
  control already reads `holds_2of3 = False` — 0.583 / 0.579 / 0.579, all FAIL. So this limb is
  "does not get worse", stated at the control's actual level rather than against a 2/3 bar PJM
  does not currently clear.)*

Recommend **HOLD-and-route** if (a) fails — a second seam moved and the gate is not what D53
says it is. Recommend **DECLINE** if (b) fails (the code's partition is not the vintage's) or
(c) fails (the partition worsens composition).

**`retire.total_gw`'s and `false_retire`'s band readings are explicitly NOT conditions in either
direction** (rule 14, §3 P5) — including the improvement §3 P5 predicts. Selecting a mechanism
because the residual moved is exactly what rule 1 forbids, and it stays forbidden when the
residual moves the flattering way.

---

## 8. Governance attestation (as pre-declared; re-attested in the FINDING)

- **Rule 1 `[R-STRUCT]`:** the partition is a market-structure fact (who faces a merchant exit
  decision), argued from the owner's decision process (D53 §1.1) and measured on PJM's own
  cohort (§2.4). The residual's predicted direction is disclosed in §3 P5 and is **not** a
  criterion in §7.
- **Rule 12 `[R-PARALLEL]`:** PJM solo; years sequential within each invocation; the arm and the
  control run one after the other, never concurrently (a plant-level PJM year on 15 GB).
- **Rule 13 `[R-MEASURED]`:** `Sector` enters from the EIA-860 plant table at the run's active
  vintage — an owner attribute, forward-regenerating, never an outcome. The real cohort (§2.4)
  MEASURES the partition's consequence and identifies nothing.
- **Rule 14 `[R-ACCURATE]`:** the sign line is stated in §3 P5 before the solve, in both
  directions.
- **Rule 19 `[R-ONE-MECH]`:** one exit decision per unit — the gate and the dates channel union
  at the same `exempt_unit_ids` seam and neither produces an exit (D53 §1.8). No floor, no
  stacked mechanism, no new code.
- **Rule 21 `[R-DOF]`:** a partition on one published boolean. No weight, no threshold, no
  value that could be identified against a residual. Zero DOF added.
- **Rule 22 `[R-HOLDOUT]`:** solve years {2021, 2023, 2024, 2025} on the full span and
  {2021, 2023} on the screen, 2022 bridged and never scored; scoring and LOYO bounded to
  2023–2025; the holdout freeze untouched; nothing against 2019, 2020, 2022 or H1-2026.
- **Rule 24 `[R-REGISTRY]`:** the field is already in `ScenarioConfig` and `run_config.json`
  with the harness flag `--retirement-sector-gate`. No env knob, no literal, no per-plant dict.
- **Rule 25 `[R-ISO-SCOPE]`:** **PJM's cell gets PJM's own measured letter.** MISO's `K`/`O`
  never fills it; the recommendation in §7 is scoped to PJM's overrides, not the shared default.
- **Rule 27 `[R-PUSH]`:** no ≥300-line source file is rewritten from response content; any such
  edit is local and blob-verified after push.
- **Rule 28d `[R-MECH-MATRIX]`:** the PJM shard's `retirement_sector_gate` cell (`.` / `U`
  today) is stamped with PJM's measured verdict in this session, alongside the registration —
  **only PJM's shard is edited.**
- **Rule 29 `[R-SCREEN]`:** phase 0 is §2 (zero LP); the screen year is named in §4 from the
  mechanism's own footprint before the screen runs; the screen gate is structural and STOP-only;
  the screen and control bundles are deleted before merge.
- **No mechanism code.** D53 built the gate. If PJM needs a seam D53 did not build, this lane
  STOPS and routes rather than extending the gate.

**Collision:** the D67 lane (requirement seam), D74 (bar/offer seam) and D75 (ELCC registry) may
be live on PJM hindcast surfaces on different seams. This lane writes no `src/` code at all, so
the only shared surfaces are the PJM matrix shard and the forecast registry — rebase before
every push, never drop another lane's hunk.

## 9. Kills

- **K-a:** cache-key collision, or a realized key ≠ §5 unexplained → STOP for that leg.
- **K-b:** any sector-1 unit in a pipeline row on either leg → DECLINE by §7(b); the loader's
  join is the first suspect and is reported.
- **K-c:** P4 fails (a second seam moved) → the A/B is still registered and graded, but the
  recommendation is HOLD-and-route by §7(a) whatever the band reads.
- **K-d:** the screen gate (§4 S1–S5) fails → the arm is killed, the full span is never spent,
  and the kill is the session's reported result.
- **K-e:** the preserved baselines (`pjm-2021-2025-realized-t1h-d45r-fixed`, `-d45r`,
  `-d57-clearing`, `-d62-pubbar`) are never written; every leg takes a fresh out-dir.
- **K-f:** no operand of the gate is a model outcome or a residual (rules 13/14/21); the cohort
  of §2.4 measures, never identifies.

## 10. Reproduction of §2 and §5 (committed instruments)

```
uv run python docs/handoffs/d58/census_probe.py   # -> census_probe.json
uv run python docs/handoffs/d58/keys_probe.py     # -> keys_probe.json
```
