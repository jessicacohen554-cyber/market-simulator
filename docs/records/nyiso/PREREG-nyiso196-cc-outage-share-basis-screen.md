# PREREG nyiso-196 — the C1-2024 `CC_REGULAR` over-run decomposed to ONE measured object: the unit-outage removed SHARE at combined cycles is taken across two capacity bases, and at Cricket Valley 57185 an EIA-860 id collision halves it — screened on 2024 with `unit_outage_extract_basis_share`

**Session:** nyiso-196 (`claude/nyiso-cc-regular-overrun-2024-apt3d6`), 2026-09-05.
**Owner instructions in force** (nyiso-194/195 sittings, verbatim): *"Only run 2024 to see
if it fixes the c1 gas cc miss. C3c is an acceptable caveat and known limitation of this model
type."* / *"No control arm just use the last keeper."* / *"stop doing control solves … just use
the last keeper as the control"* / *"only run in calibrated years thru new configs first"*.
**Keeper / control:** `2026-09-05-nyiso-192-astoria-panel` (bundle
`results/calibration/nyiso192_astoria_panel`, `git_sha d5bba63b`), NOT-YET on exactly one
load-bearing cell — C1-2024 `CC_REGULAR` model 37.74 vs actual 34.06 TWh, +3.68 TWh /
+3.03 pp against ±3.98 TWh / ±3.0 pp (fails on SHARE by 0.03 pp). Control = the keeper's
COMMITTED bundle (rule 29(b) form 4; G-DRIFT §5). **No control solve. Screen = 2024 only.**
**This file is pushed BEFORE the screen is launched**; the phase-0 numbers below were
measured with zero LP and the prediction in §7 is written before any solve.

---

## 0. What this session was asked and what it found (steps 1–3, zero LP)

Steps 1–3 of the brief were executed as one measurement
(`scripts/probes/nyiso196_cc_overrun_decomp.py` → `_nyiso196_cc_overrun_decomp.json`;
`scripts/probes/nyiso196_rebuild_checks.py` → `_nyiso196_rebuild_checks_2024.json`,
Addendum A; the loader on/off census `_nyiso196_extract_basis_census.json`). The keeper's
per-plant hourly MW is decoded from its committed dashboard payload exactly as
`legitimacy_diagnostics` and the nyiso-194/195 probes decode it; the meter is the bench
part's CAMPD series on the same plant/group split (1 % byte quantisation), so the class
totals here are CAMPD-gross (36.44 TWh in 2024), not the scorer's EIA-923 net (34.06).

### 0.1 Step 1 — the buckets (TWh; `a + b+ − b− − c ≡ model − meter`)

| year | model | meter | net | (a) model on / meter off | (b+) loading excess | (b−) loading deficit | (c) meter on / model off | online plant-h model / meter |
|---|---|---|---|---|---|---|---|---|
| 2023 | 34.074 | 33.455 | +0.62 | **+1.18** | +4.05 | −3.77 | −0.84 | 91,873 / 89,406 |
| 2024 | 37.614 | 36.440 | +1.17 | **+1.47** | +3.62 | −3.33 | −0.58 | 101,929 / 90,664 |
| 2025 | 35.434 | 33.880 | +1.55 | **+2.27** | +3.99 | −3.56 | −1.15 | 119,192 / 95,550 |

The loading buckets net out (+0.29 / +0.29 / +0.43 TWh); the year-to-year growth of the net
is the ONLINE-HOURS bucket (a) — the object the brief named. Per plant, 2024 (GWh):

| plant | zone | model | meter | net | a | b+ | b− | c | online h model / meter | bridge binding h (D-4) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Cricket Valley 57185** | Capital_Hudson | 5,038 | 4,241 | **+797** | **466** | 705 | 371 | 3 | 8,748 / 7,704 | 40 |
| CPV Valley 56940 | Capital_Hudson | 4,296 | 4,982 | −686 | 0 | 74 | 711 | 49 | 8,204 / 8,301 | 5 |
| Athens 55405 | Capital_Hudson | 3,572 | 4,046 | −474 | 72 | 185 | 706 | 26 | 6,276 / 6,086 | 34 |
| Bethlehem 2539 | Capital_Hudson | 5,965 | 5,539 | +426 | 43 | 754 | 320 | 51 | 8,016 / 8,037 | 211 |
| Carr Street 50978 | Upstate_West | 491 | 134 | +356 | 314 | 55 | 8 | 6 | 7,958 / 2,752 | 0 |
| Astoria Energy 55375 | NYC | 4,596 | 4,282 | +314 | 7 | 517 | 150 | 60 | 8,208 / 8,342 | 0 |
| Zeltmann 56196 | NYC | 4,044 | 3,782 | +262 | 0 | 430 | 124 | 45 | 7,800 / 7,930 | 0 |
| Astoria II 57664 | NYC | 4,263 | 4,137 | +126 | 29 | 489 | 339 | 52 | 8,160 / 8,250 | 0 |

Cricket Valley carries 466 of the class's 1,471 GWh bucket (a) and is the only large plant
whose online hours exceed the meter's by ~1,000 h. Its bucket (a) is **flat across the 24
hours of day** (18.6–21.0 GWh per hour-of-day) and sits in **January (173 GWh), March (78),
October (58) and December (156)** — the calendar of its 2024 unit outages, not a diurnal or
price pattern (by keeper-zone LMP quartile 44 / 79 / 92 / 252 GWh: it is largest in the
dearest quartile, i.e. the model runs the plant when the zone price is high and the meter
says it could not).

### 0.2 Step 2 — mechanism attribution of bucket (a)

* **Commitment bridge:** the keeper's D-4 unit-conduct rows put
  `nyiso_gas_commitment_bridge × CC_REGULAR` binding at 57185 for **40 h** in 2024 (92 / 152 in
  2023 / 2025; 2539 211 h, 50292 2,173 h, 54574 259 h). The floor cannot own a 1,044-hour
  online excess; its window declaration (`D4_WINDOWS`, all-hours by measurement, the
  per-plant unit-conduct check PASS at every plant) is not in question.
* **Reliability floors:** `CC_REGULAR` carries no `reliability_floor` limb (the D-2 rows
  list the bridge as the class's only mechanism).
* **The P0 run pattern / plain economics — on the availability the LP was GIVEN.** The
  committed tranche is offered at 0.90 × HR under `gas_offer_net_revenue_margin` and
  clears the Capital_Hudson LMP in the great majority of bucket-(a) hours (Addendum A,
  A-1). So the LP is behaving exactly as its inputs say — and the input it contradicts the
  meter on is **availability**: **all 466 GWh of Cricket Valley's bucket (a) fall in hours
  where the LP was handed more available capacity than the committed unit-outage extract
  states**, 257 GWh of it (671 h) inside windows where the extract has all three blocks out
  and the meter reads zero.

### 0.3 Step 3 — the same-zone neighbours, for the record (2024, Capital_Hudson excess hours)

In the 3,987 h where the zone's `CC_REGULAR` runs above its meter (1,460 GWh): same-zone
`ST_GAS` −567 GWh (model below meter), `CC_CHP` +194, imports (ISO total, model class vs the
measured `SCH-*` scheduled interchange) −885 GWh; annual imports 20.71 model vs 20.67 TWh
measured. None of these is a contradicted MEASURED INPUT in those hours: the import
capability never binds below the measured flow (Addendum A, I-1), the delivered-gas series
sits on its measured hub monthlies (Addendum A, G-1), and the `ST_GAS` deficit is the
cell-G / owner-court steam object (nyiso-187 / 192 / 193), not an input the model
contradicts hour by hour. The one measured input the model contradicts hour by hour is the
extract's own availability at the class's own plants.

---

## 1. The measured object (rule 14 `[R-ACCURATE]`, zero DOF)

**The defect.** `outages._unit_outage_factors_from_events` derates a bin by
`unit_capacity_mw / cap[bin]` — the numerator from the committed extract
(`data/raw/campd-unit-outages-perunitmerit-NYISO.csv`, written by
`derive_campd_unit_outages.build_capacity_index`), the denominator from
`outages._iso_plant_capacity`, the fleet's net-summer pmax sum. The two are meant to be one
basis (the deriver's docstring: *"the same basis as the model bin denominator the derate
divides into"*) and at Cricket Valley they are not, for a reason visible in the two data
files alone:

| | EIA-860 `eia860_generator_operable` | CAMPD `NY_2024` |
|---|---|---|
| ids `U001`, `U002`, `U003` | prime mover **CA** (steam turbines), 174.2 MW each, unit codes CCG1–3 | the three CEMS **stacks**, gross reaching 374 / 380 / 373 MW each |
| ids `U004`, `U005`, `U006` | prime mover **CT**, 263.3 MW each, unit codes CCG1–3 | — |

The deriver's exact-id route matches CAMPD `U001` to EIA `U001` — a **steam** generator — so
the CT steam-coupling augmentation (`derate_mw = CT × (1 + ΣCA/ΣCT)`, applied only to prime
mover CT) never fires, and the extract writes each 1×1 block at **174.2 MW**
(`capacity_source eia_exact`, `plant_capacity_mw 522.6`, `unit_pct_of_plant 33.3`). The LP
accumulator then divides 174.2 by the 1,016.8 MW net-summer bin: **one block out removes
17.1 % of the plant against the physical 33.3 %; all three blocks out (Jan 13–24, Feb 29–
Mar 8, Dec 20–27 2024) leave 48.6 % of the plant available at a plant whose meter reads
zero.** The extract's own columns say 33.3 % and 0.0.

**Why the SHARE and not another side of it.** The consistency-repair family already holds
five legs: `unit_outage_lp_capacity_basis` raises the CC DENOMINATOR to nameplate (at
Cricket Valley: 174.2 / 1,312.5 = 13.3 %, worse), `unit_outage_st_capacity_basis` puts the
STEAM numerator on the fleet's per-unit pmax (CC bins out of scope by construction),
`unit_outage_fleet_status_scope` (event set), `unit_outage_mixed_gas_routing` (address),
`unit_outage_per_unit_clip` (arithmetic). None makes the CC share basis-independent. The
sixth leg does: **numerator and denominator from ONE construction — the extract's own
`unit_capacity_mw / plant_capacity_mw` at a single-group facility (exactly the published
`unit_pct_of_plant`), the group's distinct-unit sum at a multi-group facility.** It needs
no per-unit fleet-roster match and no knowledge of which EIA generator a CAMPD stack is.

**Scope, decided by physics.** COMBINED-CYCLE bins only (`_CC_NAMEPLATE_BASIS_GROUPS` =
`CC_REGULAR`, `CC_CHP`): a CEMS unit at a combined cycle is a 1×1 block or a steam-coupled CT
whose share of the plant the deriver's `fac_cap` states. Steam bins keep their own
numerator alignment (`st_capacity_basis`, disjoint bins — rule 19 `[R-ONE-MECH]`); the
unscoped construction was measured first and REJECTED for this arm because it also moved
Astoria 8906 `ST_GAS` (+1.8 TWh available) and Ravenswood 2500 `ST_GAS` (+0.55) — steam bins
the nyiso-192 panel repair just adjudicated and whose object is a different one. Non-ERCOT
only. Mutually exclusive with `unit_outage_lp_capacity_basis` (the loader raises).

**Forward story (rule 13):** a property of the accumulator; a forecast year's extract carries
the same two columns and regenerates identically. **DOF ledger: zero** — no scalar, no
table, no per-plant entry; the field is a bool.

**The census (zero LP, `unit_outage_derate_factors` on vs off on the committed extract; GWh
of available energy, arm − keeper; only CC bins move):**

| bin | 2023 | 2024 | 2025 | what moves it |
|---|---|---|---|---|
| **57185 Cricket Valley** `CC_REGULAR` | **−801** | **−1,832** | **−1,599** | the id collision (17.1 % → 33.3 % per block) |
| 10725 Selkirk `CC_CHP` | −1,360 | −1,576 | −1,129 | observed-peak basis 406–447 MW vs a larger fleet bin; three blocks dark ~340 days/yr each (meter 0.16 / 0.11 / 0.38 TWh; keeper 0.15 / 0.26 / 0.34) |
| 50006 Linden `CC_CHP` | +303 | +326 | +314 | observed peak 1,242 > bin |
| 55405 Athens `CC_REGULAR` | +236 | +272 | +410 | observed peak 378 × 3 vs 1,064.7 bin |
| 50292 Bethpage `CC_REGULAR` | +202 | +154 | +102 | steam-augmented nameplate 176 vs 129 net-summer bin |
| 54574 Saranac `CC_REGULAR` | +94 | +128 | +152 | observed peak 304 vs 237.8 |
| 54547 Sithe `CC_CHP` | +182 | +89 | +98 | nameplate-augmented 1,157.6 vs bin |
| others (2539, 56940, 57664, 2500, 56196, 55375, 56259, 50450, 50451, 54114, 50368) | ±0–75 each | | | |
| **`CC_REGULAR` net / Σ\|Δ\|** | −248 / 1,534 | **−1,183 / 2,481** | −667 / 2,531 | |
| **`CC_CHP` net** | −898 | −1,259 | −793 | |

Every CC bin moves toward the availability its own extract rows state; no non-CC unit moves
(17 bins in 2024, 0 steam).

---

## 2. The arm

**Single delta**, `ScenarioConfig.unit_outage_extract_basis_share: False → True`, applied on
the keeper's committed recipe through the replay driver's generic override channel:

```
uv run python scripts/replay_keeper.py results/calibration/nyiso192_astoria_panel \
  --years 2024 --set unit_outage_extract_basis_share=true \
  --out-dir results/calibration/nyiso196_screen_2024 \
  --note "nyiso-196 SCREEN 2024: unit-outage removed share on the extract's own basis (CC bins)"
```

G-DELTA = exactly `{unit_outage_extract_basis_share: false → true}`; every other recorded
flag is the keeper's. The field is registered in `_CACHE_KEY_OPTIONAL_FIELDS` /
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit (the nyiso-119 / caiso-186
discipline), so the default cache key does not move; its matrix row and a cell in every
ISO shard land in the same commit (rule 28(c)); unit tests
`tests/unit/data/test_unit_outage_extract_basis_share.py` pin the Cricket Valley arithmetic,
the full-stop-is-zero invariant, the multi-group fallback, the scope, the mutual exclusion,
the per-unit-clip interaction and the registration (502 tests pass with the sibling suites).

---

## 3. Screen year: **2024** — named here, before the solve

Rule 29 names the year the mechanism's OWN measured footprint is largest. The object is the
Cricket Valley under-derate; its footprint (LP-applied minus extract-own-basis available
energy) is **0.86 / 1.96 / 1.71 TWh** in 2023 / 2024 / 2025 on 190 / 450 / 398 unit-outage
days, and the class-net footprint −0.25 / **−1.18** / −0.67 TWh. Stated for honesty: the
class-wide ABSOLUTE footprint (Σ|Δ| over `CC_REGULAR` bins) is 2 % larger in 2025 (2.53 vs
2.48 TWh) because Athens' and Astoria II's over-derates are larger there; the object named
in §1 is largest in 2024, which is also the year the owner instructed. 2024 is not the year
chosen for its residual (2023 PASSES the cell; 2025 PASSES it).

---

## 4. Control = the keeper's committed 2024 (form 4)

Control rows: the keeper's per-plant 2024 rows (`_nyiso194_screen_gates_S.json` keeper
side, `_nyiso196_cc_overrun_decomp.json`), `hourly/system_2024.parquet`,
`class_band_hourly_2024.parquet`, the committed payload + bench part, the on-recipe
`fleet_only` rebuild (Addendum A). **No control solve.**

## 5. G-DRIFT `d5bba63b..5b5af5ab` — every solve-path hunk INERT for a NYISO 2024 backcast

The nyiso-195 PREREG (§4, pushed at `9a0b80fe`) audited `d5bba63b..9a0b80fe` (153 commits)
hunk by hunk and classified every one INERT; that audit is adopted by reference and was
re-checked this session on the full range (`git diff d5bba63b HEAD --stat` over
`src/market_sim scripts/run_calibration*.py scripts/lib data/raw/_validation-source
data/raw/reference`, 32 files): `data/offer_curves.py` (`_with_intermediate_phys`, gated
`iso == "MISO"` and default off); `config/scenarios.py` (two new default-off/`None`
fields; the `ccs_retrofit_capex_co2_scaling` default flip — `ccs.py` returns at
`year < 2028` and the backcast orchestrator never enters capacity evolution);
`config/iso_configs.py` (PJM `default_scenario_overrides`, other ISO; NYISO
`nyiso_requirement_forecast_peak` / `nyiso_requirement_vintage_factors` consumed only in
`capacity_evolution/retirements.py`, forecast-only, and the replay runs the bundle's
recorded values, which carry them `false`); `config/constants.py` (capacity-market imports,
a removed CCS reference dict, an **ERCOT** `NUCLEAR_MONTHLY_CF_BY_YEAR` **2022** row, two
removed ERCOT constants); `data/raw/reference/nyiso-market-solar-capacity.csv` (**2022 rows
added only** — 0 changed rows for 2023–2026, verified by grep); `capacity_market.py`,
`capacity_evolution/*`, `runner.py` (forecast-only); `results/cache.py` (key-epoch
comments; the replay writes a fresh bundle); dead-code removals with no importer
(`floor_mechanisms.tag_raised`, `eia923.plant_state_map`, `eia860._committed_vintage_years`,
`plant_taxonomy.is_fossil`, `benchmark_corridor.load_benchmark_corridor`, `som_conduct.py`,
`results/metrics.py`, `pipeline/result.py`, `outages.read_clean_outages` and
`CT_DEPLOYMENT_CSV`, `paths.TX_UNIT_OUTAGES_CSV`, `miso_outages.FORECAST_PARQUET`);
`interchange/spec.py`, `pipeline/reference.py` (comments). **Increment since the nyiso-195
audit, `9a0b80fe..5b5af5ab`:** `scripts/lib/bench_stamp.py` (post-solve dashboard
stamping, not the solve) and `scripts/run_calibration_full.py` (a replay-only
`caiso_dsw_daytime_evening_trim` override whose default `None` keeps the recipe). **All
INERT ⇒ form 4 valid; the keeper is the control.**

## 6. STOP gates — structural only, may kill, never promote, never a residual

Evaluated by `scripts/probes/nyiso196_screen_gates.py` → `_nyiso196_screen_gates.json` on the
screen bundle against the control rows of §4.

* **F-1 footprint (zero LP, both rebuilds).** The arm's fleet differs from the keeper's ONLY
  in `availability`, ONLY on CC bins of the plants the §1 census names; `pmax`, heat rate,
  `offer_markup_hr`, `mc_base` and `fuel_prices` byte-identical on every unit. **STOP** if
  any non-CC unit's availability moves or any offer/capacity moves.
* **F-2 identity (zero LP).** On every moved plant, arm ÷ keeper availability equals the
  loader's on ÷ off ratio hour for hour (max error < 1e-4) — the flag reaches the LP through
  `unit_outage_derate_factors` and nothing else. At 57185 the arm's availability is exactly
  0.0 in the three all-blocks-out windows. **STOP** otherwise.
* **S-3 direction (the frozen structural gate).** (i) Cricket Valley's 2024 energy in the
  extract's dark windows (keeper 257 GWh over 671 h) is **0** in the arm, by construction;
  (ii) its energy above the arm's availability envelope is 0; (iii) its annual energy FALLS
  by at least half of the 512 GWh the keeper dispatched from capacity the extract says was
  out (the LP cannot re-place all of it at a plant already at its wall in the remaining
  hours) — **STOP** if the fall is < 256 GWh or if (i)/(ii) are violated (a plumbing defect,
  whatever the residual does); (iv) Selkirk 10725's energy falls (its availability falls
  in 8,448 h); (v) the footprint of the DISPATCH delta is confined in sign to the census:
  no CC bin whose availability the arm did not touch changes its own availability-bound
  hours. Reported, not gated: the direction at Athens / Bethpage / Saranac / Linden (whose
  availability rises — they may or may not take energy, that is displacement).
* **S-4 load-bearing companions (approximate, same-weights construction as nyiso-194/195).**
  No 2024 load-bearing criterion flips PASS → FAIL: C2 (load-weighted mean price vs actual,
  keeper −0.72 %), C3a-like, C3b-like (monthly NRMSE 0.183), C1 cells other than
  `CC_REGULAR` (`CC_CHP` +2.10, `ST_GAS` −1.43, `CT_*`, non-gas). **STOP** on any flip.
* **C8 / D-4:** the arm's `legitimacy_diagnostics.json` regenerates (the replay's post-step);
  forced shares reported; the keeper's own D-4 rider rows are expected unchanged.
* **C1-2024 `CC_REGULAR` — REPORTED at full magnitude, NEVER gated:**
  `calibration_verdict.score_fuelmix` on the keeper's committed payload `gmModel` with the
  screen's P1 class-energy deltas applied (the nyiso-195 construction), for every class.
* **C3c:** the owner's accepted caveat, reported, never a gate.

## 7. Prediction (written before the solve; not a gate)

Cricket Valley 2024: −0.3 to −0.6 TWh (the 512 GWh dispatched above the arm's envelope,
partly re-placed in other hours); Selkirk −0.1 to −0.15 TWh; Athens / Bethpage / Saranac
+0 to +0.3 TWh combined (they gain headroom in hours their committed offers already clear).
Class `CC_REGULAR` −0.2 to −0.5 TWh; `CC_CHP` −0.1 to −0.3; the released energy lands on
same-zone `ST_GAS` / the other CC plants / imports. C1-2024 `CC_REGULAR` moves from +3.68 TWh
/ +3.03 pp toward the band; whether it crosses 3.0 pp is not a gate and not predicted. C2
moves < 0.5 pt; NRMSE < 0.01.

## 8. Disposition rules (fixed now)

* A **killed** screen is the session's result: the arm is R in NYISO's own lane, nothing
  registered, the full span never spent, the screen bundle deleted after the gate record is
  written.
* A **cleared** screen earns the full span — ONE `--years 2023 2024 2025` bundle on the same
  single delta — then registration (`dashboard_add_run.py`), attestation (the
  `gen_nyiso192_attestation.py` pattern, G_CONTROL vs the keeper), `calibration_verdict.py
  --run-id`, matrix cell + §5.5 + calibration-log in the same session. **Promotion is the
  owner's call** under the standing structure-over-gates formula; the determination is
  stated at full magnitude; a `CALIBRATED` reading re-enters `complete` only through a NEW
  owner declaration (the `withdrawn.NYISO` re-entry clause), gate (a) re-keyed in the same
  PR. Nothing here is fitted to the 0.03 pp share miss.

## 9. Rules ledger

Rule 1: structural gates, residual reported never gated. Rule 13: the extract's own columns,
regenerable forward. Rule 14: a measured input the model contradicts hour by hour, kept over
the estimate it was silently compensating for. Rule 15/16: nothing registered from a
one-year screen. Rule 19: scoped so no bin carries two share constructions. Rule 21: zero
DOF. Rule 22: 2024 only, inside 2023–2025. Rule 23: no derive re-run, no artifact touched.
Rule 24: a registered `ScenarioConfig` field, in `run_config.json`. Rule 25: NYISO's own
extract; every other ISO's cell enters U. Rule 27: on-disk bytes pushed, ≥300-line blobs
verified. Rule 28: base row + six shard cells in this commit. Rule 29: phase 0 first, one
year, keeper as control, G-DRIFT audited, STOP gates only.

*(nyiso-196, 2026-09-05. Addendum A — the zero-LP rebuild checks F-1 / F-2 / A-1 / G-1 /
I-1 — is appended below before the screen is launched.)*

---

## Addendum A — the zero-LP rebuild checks, recorded BEFORE the screen is launched

`scripts/probes/nyiso196_rebuild_checks.py --year 2024` → `_nyiso196_rebuild_checks_2024.json`
(two on-recipe `run_year(fleet_only=True)` rebuilds of the keeper's `meta.json`, flag off =
the keeper, flag on = the arm through the replay driver's own `prb_overrides` channel).

* **F-1 footprint — PASS.** 128 LP units' `availability` differ, at exactly the 17 plants the
  §1 census names (2500, 2539, 10725, 50006, 50292, 50368, 50450, 50451, 54114, 54547, 54574,
  55405, 56196, 56259, 56940, 57185, 57664), groups `CC_REGULAR` / `CC_CHP` only; **0 non-CC
  units move**; `pmax`, heat rate, `offer_markup_hr`, `mc_base` and `fuel_prices` max |Δ| =
  **0.0** on every unit.
* **F-2 identity — PASS.** On every moved plant arm ÷ keeper availability equals the loader's
  on ÷ off ratio hour for hour, max error **3.6e-6**. Cricket Valley's LP availability
  (which also carries the statistical layer) 0.6955 → 0.5097 (loader 0.7821 → 0.5763), and
  reads 0.0 in the three all-blocks-out windows.
* **A-1 bucket-(a) economics at Cricket Valley — the LP behaves as its inputs say.** 1,052 h /
  466 GWh; in **97.1 %** of those hours the keeper's Capital_Hudson LMP (mean $56.45/MWh)
  clears the committed tranche's assembled offer (mean $27.25/MWh); **99.9 %** of the hours
  (466.1 of 466.4 GWh) sit in windows where the LP was handed more availability than the
  extract states, **58.1 %** (234.6 GWh) inside windows where the extract has all three
  blocks out. The bridge binds 40 h. So bucket (a) is plain economics on a contradicted
  availability input — not a floor, not a bridge, not an offer level.
* **G-1 delivered gas — the basis hypothesis is REFUTED for the over-running zone.** The
  keeper's cap-weighted `CC_REGULAR` delivered gas equals the committed measured hub monthly
  in 11 of 12 months exactly (ratio 1.000) at Capital_Hudson / Long_Island (Iroquois Z2,
  annual 2.778 / 2.771 vs 2.789) and NYC (Transco Z6 NY, 2.06 vs 2.08); January reads
  0.96–0.98 (the oil-parity cap). Upstate_West rides the SOM annual Tenn Z4 200L offset:
  1.715 vs the SOM 1.83 (the −1.07 offset is taken from the SOM 2.90 east level and applied
  to the 2.789 monthly construction) — a −$0.11/MMBtu upstate level effect present in every
  year, not a 2024 signature and not at the over-running plants. No basis error makes
  upstate CC cheaper than downstate steam in 2024 only.
* **I-1 import capability — not a contradicted input.** 13 import pseudo-units, capability
  66.8 TWh (p50 7,764 MW) against measured scheduled imports 20.67 TWh (p50 2,303, p99
  4,832 MW): **0 hours** in which the measured flow exceeds what the LP could import. The
  −885 GWh import shortfall in the class's excess hours (§0.3) is a priced-dispatch shape,
  not a cap below the measured flow.

**Conclusion of steps 1–3:** the one measured input the keeper contradicts hour by hour, with
the largest 2024 footprint, is the unit-outage availability at the class's own plants — the
object of §1. The screen is launched on §2's command; gates §6; prediction §7.

*(Addendum A written 2026-09-05 before the solve; pushed with the PREREG.)*
