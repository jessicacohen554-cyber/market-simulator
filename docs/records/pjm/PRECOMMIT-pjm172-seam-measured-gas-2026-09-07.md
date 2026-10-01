# PRECOMMIT — pjm-172: give the priced-interchange seam a MEASURED backcast gas level (F-A, seam-local)

**Session** pjm-172 · **ISO** PJM · **Date** 2026-09-07
**Status: WRITTEN BEFORE ANY BUILD OR SOLVE** (rule 29 `[R-SCREEN]`). Nothing is implemented yet.
**Predecessor** `results/calibration/ADDENDUM-pjm171-seam-fuel-basis-freeze-2026-09-07.md`
**Owner decision (2026-09-07):** repair shape = **seam-local measured gas path**, *not* an edit to
the shared `HENRY_HUB_TRAJECTORIES` table.
**Keeper** `2026-08-15-pjm-162-inputclock` — unchanged by this card in every training year (§3).

---

## 1. THE DEFECT THIS REPAIRS (measured, predecessor §1)

`neighbor_gas_price`'s docstring promises *"a neighbor and its bordering ISO see the same Henry Hub
level"*. Measured error: **0 % in 2023/2024/2025**, **−32 % in 2021**, **−61 % in 2022**, because
`HENRY_HUB_TRAJECTORIES` has its first knot at 2023 and `_hold_flat_extrapolate` hands every
earlier year the 2023 knot ($2.54) while the ISO's own units burn the measured year price.
`reference_price_interface = True` on both the keeper and the registered touchpoint, so it binds.

---

## 2. THE ARM — ONE declared delta

**F-A only.** In `market_sim/data/neighbor_price.py::neighbor_gas_price`, when the requested year
falls **before the trajectory's first knot**, resolve the Henry Hub level from the **measured**
annual series (`data/raw/gas-prices/henry_hub_monthly.csv`, annual mean of the monthly spot) instead
of holding the first knot flat. The neighbour's own `gas_basis` is applied unchanged, so the seam
keeps its existing basis structure.

**Explicitly NOT in this arm** (each is its own card, rule 19 `[R-ONE-MECH]`):

- **F-B**, the missing `hr_by_year` entries for 2021/2022 (`derive_neighbor_hr_by_year.py`). The
  screen must measure the gas level alone; bundling two deltas makes S3 unfalsifiable.
- Any change to `HENRY_HUB_TRAJECTORIES` (owner decision: seam-local).
- Anything in the parent finding's trough object or the EMAAC availability census.

**Zero free parameters** (rules 21 `[R-DOF]`, 24 `[R-REGISTRY]`): the values are the measured EIA
Henry Hub annual means already on disk and already consulted by the ISO's own resolver —
2019 **2.565** · 2020 **2.034** · 2021 **3.910** · 2022 **6.419**. Nothing is fitted, nothing is
selectable by a result.

### 2.1 The look-ahead guard — load-bearing, and fixed here before any code exists

`neighbor_gas_price` is also called by `scripts/run_capacity_hindcast.py` under the
`hindcast_asknown_*` trajectories, whose entire purpose is to price a hindcast year with **only the
information available at the time**. Injecting a realized price there would be look-ahead
contamination. **The measured path must therefore be refused for any `hindcast_asknown_*` scenario
key**, which keeps `hindcast_asknown_aeo2023` (no pre-2023 knot) on its held-flat behaviour.
`hindcast_realized` already carries a 2021 knot and is untouched by construction. A test asserting
this refusal is part of the change, not a follow-up.

---

## 3. PHASE 0 — already complete, zero LP (rule 29 step 0)

1. **The freeze is measured** (predecessor §1) and the mechanism is armed on both bundles.
2. **The consequence is measured**: model net export vs EIA-930 — 2021 23.43 vs 37.94 (−14.51 TWh),
   2022 21.65 vs 31.64 (−9.99), 2023 −12.40, 2024 −12.12, 2025 +5.26.
3. **Demand is ruled out**: model LP demand vs EIA-930 is +0.0 / +0.3 / +0.2 / −0.1 / −0.0 %.
4. **INERTNESS IN THE TRAINING WINDOW, by construction**: `_hold_flat_extrapolate` returns the exact
   knot whenever the year is present, so a pre-first-knot branch cannot execute for 2023/2024/2025
   or for any forecast year. **The keeper is byte-identical, no training re-solve is required, and
   no determination is re-verified.** This must be *asserted by test*, not argued.

---

## 4. THE SCREEN — ONE year, named here, chosen on FOOTPRINT

**Screen year: 2022.** Chosen by the mechanism's own pre-solve arithmetic, **not** by any residual:
the seam baseload delta (gas × HR, before the load shape) is

| year | control baseload | arm baseload | **delta** |
|---|---|---|---|
| 2021 | 30.035 | 45.614 | **+15.579 $/MWh** |
| **2022** | 30.035 | 74.156 | **+44.122 $/MWh** |

2022's footprint is **2.83×** 2021's, so 2022 is where the mechanism is largest — rule 29's stated
selection rule. Per-neighbour control → arm for 2022, fixed here before the solve: MISO
32.766 → 82.806 · NYISO 32.136 → 72.478 · Carolinas / TVA / LGEE 28.424 → 71.833.

**Disclosed against interest:** 2022 is also the year where this repair is expected to *help* the
target (2022's C3a is −9.9 %, and dearer imports raise price). That is a coincidence of the
footprint rule, not a reason for the choice, and **C3a is not a pass condition below.** The
residual movement is reported at full magnitude and gates nothing — pjm-170's discipline exactly.

**Holdout authorisation.** 2022 is validation tier; PJM holds the `complete` marker; the holdout
spend freeze's scope is the locked test alone. The screen therefore needs `--holdout-authorized`
and is a legitimate validation-tier spend. **The screen bundle is never registered** (rule 29
clause 2) and is **deleted before the PR merges** (rule 29(c)); this document will carry every
number the session ever cites from it.

---

## 5. PRE-REGISTERED STOP GATES — fixed now, never re-read after a number exists

The screen may **kill** the arm; it may never promote it.

| # | gate | pass condition |
|---|---|---|
| **S1** | resolution | Only the seam gas level differs. `neighbor_gas_price` for PJM's 5 neighbours moves to the §4 arm values to ≤1e-9; `neighbor_heat_rate` is **unchanged** in both years (F-B not bundled). |
| **S2** | identity | For every year ≥ 2023 and every forecast year, `neighbor_gas_price` is **bit-identical** to control across all 5 neighbours and all three of `low`/`mid`/`high`. |
| **S3** | magnitude | Measured 2022 seam baseload = the §4 predicted **74.156 $/MWh** mean (per-neighbour values as tabled), |err| ≤ 1e-6. |
| **S4** | footprint | The only `mc` rows that move are the 80 reference-price seam rows (5 neighbours × 8 tranches × 2 directions). Zero non-seam rows move; zero seam rows fail to move. |
| **S5** | direction | 2022 model **net export RISES** (control 21.65 TWh; measured actual 31.64). A fall, or a rise beyond the measured 31.64 by more than 25 %, fails. |
| **S6** | collateral | No load-bearing criterion **other than C3a** that PASSES on the control 2022 may FAIL on the arm (C1 `fuelmix`, C2 `sysvol`, C4, C8, C6). |

**Kill rule:** any gate fails ⇒ the arm is dead, 2021 is never spent, nothing is promoted, and the
result is the session's finding.

**C3a is deliberately absent from S5/S6.** Gating on it would be the fitted-mechanism selection
rules 1 `[R-STRUCT]` and 29 forbid. Its movement is reported.

---

## 6. G-CTRL / G-DRIFT — zero control LP to be spent

**Form 4**: the control is the committed `pjm169_tp2022_2021_f2arm` 2022 column. Before the arm
solves, a **G-DRIFT** hunk audit (`git diff <that bundle's git_sha> HEAD` over `src/market_sim`,
`scripts/run_calibration*.py`, `scripts/lib`, `data/raw/_validation-source`, `data/raw/reference`)
must classify every changed hunk on the PJM backcast path as INERT, with the PJM solve-surface
fingerprint compared at both revisions. **A LIVE hunk is the only thing that earns a control
solve.** The audit result is appended to this document *before* the arm is solved.

---

## 7. EXPECTED RESIDUAL MOVEMENT — recorded now so it cannot be written to fit

- **2022 C3a improves.** Control −9.9 %; dearer imports ⇒ less import, more export ⇒ PJM climbs
  its own stack ⇒ price rises toward the actual. Reported, not gated.
- **2021 C3a worsens.** Same mechanism, opposite side: 2021 is already +10.8 %. This card is
  expected to push it **further outside** the band. Under rule 14 `[R-ACCURATE]` that is a
  discovered bug elsewhere — the parent finding's trough object — never a reason to keep the
  estimate.
- **C1 `CC_REGULAR` direction is genuinely uncertain.** More export needs more generation (worse),
  but the marginal supply displaced is import rather than CC (unclear). No prediction is claimed;
  the measurement is reported.

---

## 8. CROSS-ISO — stated, not acted on

The freeze is in shared code, so any ISO arming `reference_price_interface` on a pre-2023 year hits
it. Today that is PJM (keeper + touchpoints) and MISO (`miso233_sppseam_K`, 2023–2025, currently
unaffected). The seam-local shape means **no other ISO's behaviour changes in any year it currently
solves**. Rule 25 `[R-ISO-SCOPE]`: no verdict here transfers; each lane must verify its own exposure
before spending a pre-2023 touchpoint.

---

## 9. DELIVERABLES

Code + tests (the inertness assertion of §3.4, the look-ahead refusal of §2.1, the S1/S2 identities),
this document plus its G-DRIFT appendix, a FINDING carrying the full gate table, the PJM matrix
shard cell, and a calibration-log entry. **No registration, no promotion, screen bundle deleted
before merge.**

---

## APPENDIX A — G-DRIFT hunk audit (appended 2026-09-07 by pjm-172, BEFORE any implementation or solve)

**Question (rule 29 `[R-SCREEN]` (b)):** is G-CTRL **form 4** valid — i.e. is the committed
`pjm169_tp2022_2021_f2arm` 2022 column still the arm's control at this HEAD, or does a changed
solve-path hunk earn a control solve?

**Revisions.** Control bundle `git_sha` **`f36cee6e`** (recorded in its `meta.json` / `run_config.json`;
`basis_sha a269fb77`, clean tree) → **HEAD `172af213`** (this branch, rebased onto `origin/main`
`6212108f`).

**Diff scope, verbatim as §6 specifies:**
`git diff f36cee6e HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
→ **69 files, +15,065 / −76**. Every one is classified below; nothing is sampled.

### A.1 The two instrument-level checks

1. **PJM solve-surface fingerprint (capx D79, the designed instrument for exactly this question).**
   The control bundle records `solve_surface = {fingerprint: 0f749d17202c32d9, rows: 211, moved: {},
   epochs: []}`. Recomputed at HEAD: **`0f749d17202c32d9`, 211 rows, `moved_rows("PJM") == {}`** —
   **identical**. Independently, the seven `SURFACE_MODULES` were extracted at `f36cee6e` into a
   stdlib-only tree and their PJM projection compared row-by-row against HEAD's:
   **0 rows added, 0 removed, 0 value-changed, 211 identical.** So every `constants.py` /
   `capacity_market.py` / `fuel_trajectories.py` table edit in this diff is provably outside PJM's
   projection.
2. **The control's own config, rebuilt at HEAD.** `ScenarioConfig(**run_config["scenario_config"])`
   at HEAD: no field was removed or renamed (`bundle − HEAD = ∅`); the five added fields all resolve
   **False**; `hindcast` resolves **False**, so `__post_init__` coerces
   `capacity_screen_peak_measured_hindcast` back to its frozen declaration **False**, matching the
   record; and **all six drop out of `cache_key()`** (each equals its registered drop value), so the
   control recipe's key is unmoved. Every other recorded field round-trips exactly — the only
   differences are JSON `list` → dataclass `tuple` on seven sequence fields.

### A.2 Hunk classification — all 69 files INERT for the PJM backcast path

| file(s) | verdict | reason |
|---|---|---|
| `data/neighbor_price.py` | INERT | comment rewrite + a new **import-time** uniqueness assertion `_assert_hr_gas_elastic_keys_unique`. `_HR_GAS_ELASTIC` is unchanged; the guard raises or does nothing and moves no returned value. |
| `model/interchange/spec.py` | INERT | **zero deletions in the whole file.** Purely additive: CAISO 2022 depth/tranche rows, the SPP `INTERFACE_NEIGHBORS` block, a MISO-SPP ladder table. PJM's `INTERFACE_NEIGHBORS` entry is byte-identical. |
| `model/interchange/registry.py` | INERT | comment + an added `"SPP"` entry; PJM's `(apply_reference_price_seam_injections,)` unchanged. |
| `model/interchange/miso.py` | INERT | MISO-only; guarded `if iso != "MISO": return False`. |
| `model/reserves/spec.py` | INERT | SPP constants + `if iso == "SPP"` design branch; the AS-requirement swap is inside `_ercot_multiproduct_design`. |
| `results/scarcity.py` | INERT | adds a module logger and `ercot_as_measured_requirement_mw`, called **only** from the ERCOT multiproduct design. |
| `results/cache.py` | INERT | module **docstring** only (cache-epoch ledger prose); no `def` / `class` / assignment added. |
| `pipeline/persist.py` | INERT | additive `environment_block()` provenance keys; not an input to `cache_key`, ignored by `--reuse-solved`. |
| `runner.py`, `pipeline/__init__.py`, `pipeline/year.py` | INERT | the SPP gas-bridge hook. `build_spp_gas_bridge_p1_prep` returns `None` unless `config.spp_gas_commitment_bridge` **and** `iso == "SPP"`. |
| `pipeline/kwargs.py` | INERT | an `elif iso == "SPP"` logging branch. |
| `pipeline/commitment.py` | INERT | new SPP-only helpers reached only through that hook. |
| `pipeline/backcast_config.py` | INERT | SPP offer curve behind `iso.upper() == "SPP"`; ERCOT ORDC order params behind `iso.upper() == "ERCOT"`. |
| `config/scenarios.py` | INERT | five new fields (`spp_gas_commitment_bridge`, `miso_seam_neighbour_hourly_spp`, `ercot_ep_gas_basis_monthly`, `ercot_zonal_spread_ep_referenced`, `cc_summer_derate_reconciled_basis`), all **default-off and absent from the keeper's recipe**, all registered at drop value `"False"`. The `capacity_screen_peak_measured_hindcast` **default flip** `False → True` is neutralized here by half 2 of its own arm: `if not self.hindcast: … = _CAPACITY_SCREEN_PEAK_FROZEN_DECLARATION`. Measured in A.1(2). |
| `config/iso_configs.py` | INERT | PJM's `default_scenario_overrides` gains `"retirement_sector_gate": True` (capx D78 / Q56). **The one hunk that names PJM.** `__post_init__` carries `if self.mode == "backcast": self.retirement_sector_gate = <dataclass default>`. Verified empirically at HEAD through the real ISO path: backcast → **False**, forecast → True. A backcast runs no capacity evolution, so the gate has no seam to reach either way. |
| `config/constants.py`, `config/capacity_market.py`, `config/fuel_trajectories.py` | INERT | value tables (three new names: `ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR`, `SPP_GAS_BRIDGE_MIN_LOAD_FRAC`, `SPP_GAS_BRIDGE_MIN_RUN_HOURS`; no `def`/`class`). PJM's projected rows identical per A.1(1). |
| `config/solve_surface.py`, `config/solve_surface_declared.py` | INERT | `SURFACE_ISOS` gains `"SPP"` (appended last, no surface name carries an SPP token); three `DECLARED` appends at their frozen registration hashes, which move no key by construction. |
| `config/paths.py` | INERT | new `SPP_HSL_DIR` / `SPP_WIND_SHAPE_DIR` and an `"SPP"` entry in `WIND_SHAPE_DIRS`; PJM is in neither map before or after. |
| `data/eia930/actuals.py` | **INERT — by measurement, not by argument** | `_screen_fuel_spike_columns` is a **new general screen on every BA's frame**, not SPP-gated, so it was measured rather than reasoned about. Applying its exact test (`> 2.5 × median` **and** `> 2.5 × p99.9`, `NG:` columns) to PJM's frames: **0 hours flagged in 2021, 2022, 2023, 2024 and 2025** — on the raw frame and on the filled frame alike. PJM's benchmark and delivered profiles are byte-identical. |
| `data/eia930/demand.py`, `envelopes.py`, `frames.py`, `__init__.py` | INERT | SPP demand loader, the MISO↔SPP hub reader, an `"SPP": "SWPP"` map entry, re-exports. |
| `data/fleet/arrays.py`, `data/fleet/models.py` | INERT | `_reconciled_summer_ratios` supports `cc_summer_derate_reconciled_basis` (new, default-off, absent from the recipe); `BA_CODE_TO_ISO` gains `"SWPP": "SPP"`. |
| `data/renewables.py`, `data/campd.py`, `data/zone_assignment.py`, `data/transmission_expansion.py`, `data/floor_mechanisms.py` | INERT | SPP entries added to per-ISO maps/frozensets and a new mechanism id 24; PJM's membership is unchanged in every one. |
| `data/fuel/**` (`__init__`, `basis/__init__`, `basis/ercot.py`, `basis/meanzero.py`) | INERT | ERCOT-only module; the changed logic sits behind the two new default-off flags, and `apply_ercot_zonal_gas_basis` is on the ERCOT fuel path alone. |
| `scripts/run_calibration.py` | INERT | an SPP bridge parameter (default `None`); `_renewable_bound_is_delivered_pinned` replaces an HSL-existence test at **two** call sites, both inside `… and iso == "ERCOT"` blocks. |
| `scripts/run_calibration_full.py` | INERT | additive override parameters, every one defaulting to `None` (keeps the recipe's own value). |
| `scripts/lib/{confirmed_retirements,load_forecast,nuclear_license_status,transmission_expansion}/` | INERT | `"spp"` appended to each `_ISO_MODULES` + four new SPP modules; all four registries are forecast-lane. |
| `scripts/lib/key_provenance.py` | INERT | new standalone tooling (capx D85); imported nowhere under `src/market_sim`, `run_calibration*.py` or `scripts/lib`. |
| `data/raw/reference/*` | INERT | new SPP seam CSVs + a CAISO 2022 demand file. **`calibration_reference.json` gains an `"SPP"` block and nothing else** — its only "deletion" is a closing brace, and no PJM line appears on either side of the diff, so PJM's C1/C4 scoring reference is untouched. |

### A.3 Verdict

**ZERO LIVE hunks. All 69 files INERT for the PJM backcast path.**

⇒ **G-CTRL form 4 is VALID.** The committed `pjm169_tp2022_2021_f2arm` **2022 column is the control**,
and **no control LP is spent**. The arm solves 2022 alone.

Two hunks were adjudicated on evidence rather than on a category, and are recorded that way because
each could have gone the other way: the `iso_configs.py` PJM `retirement_sector_gate` override
(neutralized by a backcast coercion, verified by running it) and the `eia930/actuals.py` fuel-spike
screen (ungated by ISO, and INERT for PJM only because its test flags nothing there — measured
across all five years).
