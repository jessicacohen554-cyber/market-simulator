# PRECOMMIT — SCN-WS5B-NEISO, Stage-B full-horizon scenario campaign (2026–2050)

**Lane:** SCN-WS5B-NEISO (coordinator, ruling S16) · **ISO:** NEISO · **Data profile:** neiso
**Campaign id:** `scn-campaign-stageb-2026-09-07` (NEW — never `scn-campaign-policy-2026-09-06`)
**Branch:** `claude/scn-ws5b-neiso-p2mv` · **HEAD at phase 0:** `a667073f`
**Authorization:** owner ruling **S18** (2026-09-07, card D-5) — *"Narrow: 6 legs × NEISO+NYISO."*

This document is written and pushed **BEFORE THE FIRST SOLVE** (CLAUDE.md rule 29 `[R-SCREEN]`).
Every prediction scored later appears here first; the G-DRIFT audit is recorded here so it cannot
be written to fit a result.

---

## 0. Rule 29's one-year SCREEN does not apply — stated explicitly

Rule 29 `[R-SCREEN]` screens **a new config or mechanism** before spending a full span. These six
legs are **not new configs**: they are the *same* case configs Stage A already solved at the pin,
extended in horizon (`end_year` 2030 → 2050) by swapping the base YAML. No mechanism is being
introduced, no default is moved, and nothing here is tuned. There is therefore no screen year to
name and no screen gate to pass. What rule 29 *does* still bind here is clause (b) — **G-CTRL form
4, no control solves** — discharged in §3 by the `G-DRIFT` code-level audit, and clause (c) /
rule 31 `[R-RETAIN]`, discharged in §8.

Phase 0 is nonetheless run in full (§4–§6), and it **killed one leg at zero LP**.

---

## 1. The §2.1b gate — all four legs verified at HEAD `a667073f`, independently

Read directly from the committed artifacts, not from the board's prose.

| Leg | Requirement | Reading | Verdict |
|---|---|---|---|
| **(a)** | Full-span keeper + entry in the `complete` block of `calibration-complete.json` | NEISO present; keeper **`2026-09-06-neiso-106-fossil-offer`**, determination **CALIBRATED** (rubric v3.6, 0 FAILs, 1 ledgered C3c caveat); `complete=True`, `final=False` | **PASS** |
| **(b)** | FF-2D T1 battery verdict at the T1→T2 bar | **bare** `neiso-t1f` = **`PROMOTE`**, `reasons: []`, run `neiso-2026-2030-d50-ccscapex`, scored at `9e48ff6820b0` / 2026-09-04 | **PASS** |
| **(c)** | T1-X crossover gap (FC-4) measured **and reported** + FF-3E readiness green + cost table | board `c_crossover_gap` = pass (lane capx-D14, FC-4 FAIL reported at full magnitude — the leg asks for a MEASUREMENT, not a pass); `c_readiness` = green; `c_cost` measured at both grains (25-yr golden: 33.0 min / 3.7 GB) | **PASS** |
| **(d)** | Explicit, session-logged owner authorization naming ISO, window, budget | **Ruling S18**, 2026-09-07, card D-5 | **GRANTED** |

### 1.1 Why leg (b) — not the calibration marker — is what confines Stage B to two ISOs

The `complete` block now holds **five** ISOs (ERCOT, NEISO, PJM, CAISO, NYISO), so leg (a) passes
for five. The **bare `*-t1f` verdicts** read:

| ISO | bare `t1f` determination |
|---|---|
| **NEISO** | **PROMOTE** |
| **NYISO** | **PROMOTE** |
| ERCOT | HOLD |
| CAISO | HOLD |
| PJM | HOLD |
| MISO | HOLD |
| SPP | *(key absent)* |

**Leg (b) passes for NEISO and NYISO alone.** That, not the calibration marker, is the binding
constraint on Stage B, and it is exactly the pairing S18 grants. A preserved `-ff2d` / `-ffr3a2` /
`-pre-d60` suffixed key is a historical snapshot and was **not** read as current state.

### 1.2 One correction to the count carried into this lane

The lane brief records S18 as *"the second time in program history leg (d) has been granted (the
first was Q13)."* The board's own `d_owner_auth` cell records **two** prior NEISO grants, **both
spent**: **Q13** (r#17, 2026-08-30 — the T3 BAU golden) and **Q25** (r#26 am.1, 2026-09-01 — the
NEISO BAU 2026-2050 re-run at the R-A-armed storage posture). **S18 is therefore the third
leg-(d) grant for NEISO, not the second.** This changes nothing about the authorization or its
scope; it is recorded so the count stays honest.

---

## 2. Scope — exactly six cases, and no seventh

S18 grants **REF · CAP-STATE-TIGHT · CES-P60 · CES-T80 · CARB-MID · ALL-CLEAN**, and nothing else.
The CES ladder {10, 20, 30} is deliberately excluded (Stage A measured it entry-masked in both
ISOs). §2.1b(3) forbids riders by name. No seventh leg is added by this lane; §5 records one case
(**CARB-HI**) that phase 0 shows *would* be live, and routes it to SCN-DESK rather than running it.

### 2.1 CES-P60 is not a matrix case — the reproduction route is declared

`configs/scenario_campaign_matrix.yaml` at HEAD carries CES-P10 / P20 / P30 / T80; there is **no
`CES-P60` case**. Stage A produced its CES-P60 leg through a `--set` override, and the committed
`run_config.json` proves it: `set_overrides = {"federal_ces_premium_usd_per_mwh": 60.0}`.

Reproduced at HEAD, zero LP: `--case CES-P10`, `--case CES-P20` and `--case CES-P30`, each with
`--set federal_ces_premium_usd_per_mwh=60.0`, **all three resolve to cache key
`a37868175d5ae724`** — byte-identical to the committed Stage-A CES-P60 key. The three premium
cases differ only in the field the override replaces, so the choice of base case is immaterial.
**This lane uses `--case CES-P20 --set federal_ces_premium_usd_per_mwh=60.0`.**

---

## 3. G-DRIFT — the code-level drift audit (rule 29 clause (b)), run BEFORE the first solve

**THE PIN:** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` — the sha Stage A solved every leg at.
**HEAD:** `a667073f`. The pin **is** an ancestor of HEAD; **929 commits** separate them, touching
**73 files / +43,313 / −26,442** inside the audited scope
(`src/market_sim`, `scripts/lib`, `scripts/run_calibration*.py`, `scripts/run_full_horizon.py`,
`scripts/run_ces_leg.py`, `data/raw/reference`).

**VERDICT: every changed hunk is INERT for a NEISO forecast leg. Form 4 is valid; the committed
Stage-A artifacts are the control; no control solve is spent.**

### 3.1 Machine check A — resolved config + cache key (the decisive one)

For each case the resolution `runner.run_scenario_iso` performs was reproduced exactly
(`resolve_policy_bundle` → `apply_iso_scenario_defaults` → `cache_key()`) at HEAD on the
**2026-2030** base, and differenced against the committed Stage-A `run_config.json`:

| Case | Stage-A key (2026-2030) | HEAD-resolved key (2026-2030) | Match |
|---|---|---|---|
| REF | `8878d29743555b45` | `8878d29743555b45` | **YES** |
| CAP-STATE-TIGHT | `89264f98832068de` | `89264f98832068de` | **YES** |
| CES-P60 | `a37868175d5ae724` | `a37868175d5ae724` | **YES** |
| CES-T80 | `ce37aefe169bb82b` | `ce37aefe169bb82b` | **YES** |
| ALL-CLEAN | `cbb53bd42bba88a6` | `cbb53bd42bba88a6` | **YES** |

The field-level diff is the same **11 fields in every case**, and all eleven are *new*
`ScenarioConfig` fields that did not exist at the pin, each resolving **`False`** for NEISO:
`cc_summer_derate_reconciled_basis`, `eia860_vintage_tracks_solve_year`, `ercot_ep_gas_basis_monthly`,
`ercot_zonal_spread_ep_referenced`, `gas_offer_margin_anchor_vintage`, `miso_seam_neighbour_hourly_ladder`,
`miso_seam_neighbour_hourly_spp`, `netload_drag_layup_window_mask`, `pjm_interface_feed_admissibility_gate`,
`pjm_thermal_accreditation_vintage`, `spp_gas_commitment_bridge`. None re-keys at its default.

### 3.2 Machine check B — the D79 solve-surface fingerprint

`solve_surface.surface_stamp("NEISO", cfg)` at HEAD:

```
{"schema": 1, "iso": "NEISO", "fingerprint": "531e4805c9085734",
 "rows": 195, "moved": {}, "epochs": [], "git_sha": "a667073f"}
```

**Zero moved rows, zero epochs.** Across the seven `SURFACE_MODULES` — which include
`config/constants.py`, `config/capacity_market.py`, `config/fuel_trajectories.py` and
`pipeline/offer_curve_base.generic`, four of the changed files — not one NEISO-projected registry
value moved off its frozen declaration. (`SOLVE_EPOCHS` is `()`; it is empty for every ISO, so it
is reported as "did not fire", not claimed as positive evidence.)

### 3.3 The named capx risks, resolved on a NEISO **forecast** leg at HEAD

| Field | HEAD | Stage-A | Same |
|---|---|---|---|
| `capacity_screen_peak_measured_hindcast` (D76, default `True` since 2026-09-07) | `False` | `False` | YES |
| `retirement_sector_gate` (D78 / Q56) | `False` | `False` | YES |
| `pjm_vre_accreditation_vintage` (D75-R / Q55) | `False` | `False` | YES |
| `pjm_accreditation_design_vintage` (D48) | `False` | `False` | YES |
| `capacity_adequacy_requirement_published_by_iso` (D67 / Q52) | `None` | `None` | YES |
| `capacity_market_supply_clearing_by_iso` (D57) | `None` | `None` | YES |
| `ccs_retrofit_capex_co2_scaling` (D50 / Q42) | `True` | `True` | YES |
| `fossil_announced_exits_enabled` (Q30) | `True` | `True` | YES |

D76 resolves `False` here **by its own `__post_init__` coercion**: the (b′-1) flip is declared with
the frozen drop value `"False"` plus a coercion back to it whenever `not config.hindcast`. A
forecast leg is `hindcast=False`, so the flip is inert by construction — as its arming record
states, and as measured. D78/D67/D75-R are armed for **PJM alone** through PJM's own
`iso_configs` `default_scenario_overrides`; the shared defaults are untouched.

### 3.4 Per-hunk classification — every changed file, with its reason

**Byte-identity spot checks (the NEISO-named surfaces):**
- `iso_configs.py::_neiso_config()` — **byte-identical**, 150 lines, PIN vs HEAD. The two large
  additions in that file are `_pjm_config` internals and a brand-new `_spp_config()`.
- `eia930/envelopes.py::neiso_net_interchange()` — **byte-identical**, 14 lines. The 27 added
  lines under that hunk context are the new `spp_net_interchange()`.
- `_SCALAR_INTERCHANGE_ISOS` — NEISO's entry unchanged; only a new `"SPP"` key added, which
  cannot affect a NEISO lookup.
- `data/raw/reference` — **no NEISO file touched**. Changes are CAISO supply-consistent demand
  CSVs (CAISO backcast) and new SPP seam tables.

**INERT by ISO scope (new-ISO or other-ISO code paths):** `data/renewables.py`
(`_spp_wind_reference_curtailment_rate`), `model/reserves/spec.py` (`iso == "SPP"`),
`pipeline/kwargs.py` (`elif iso == "SPP"`), `pipeline/year.py` + `runner.py` + `pipeline/commitment.py`
(`build_spp_gas_bridge_p1_prep`, which returns `None` unless `spp_gas_commitment_bridge and iso == "SPP"`),
`eia930/demand.py` (`_load_spp_hourly_demand`), `data/campd.py` (SPP state list), `data/fleet/models.py`
(`"SWPP": "SPP"`), `data/transmission_expansion.py` (SPP row), `data/fuel/*` + `fuel/basis/meanzero.py`
(SPP/ERCOT tables), `data/floor_mechanisms.py` (appended SPP mech id 24),
`model/interchange/registry.py` (adds `"SPP"` only), `model/interchange/{spec,miso,import_nodes}.py`
(MISO seam ladders, both `miso_seam_neighbour_hourly*` flags resolving `False`),
`data/zone_assignment.py` (`_spp_zone`), `data/neighbor_price.py` (a uniqueness *assertion* that
raises or does nothing), `results/scarcity.py` (`ercot_as_measured_requirement_mw`),
`data/fuel/basis/ercot.py`, `eia930/actuals.py` (ERCOT bench loaders; no actuals exist for 2026-2050),
`model/capacity_evolution/retirements.py` + `__init__.py` (the D84 thermal-vintage family, gated on
`pjm_thermal_accreditation_vintage` **and** membership of `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO`
— PJM alone).

**INERT by mode predicate (backcast-only, and this leg is `mode="forecast"`):**
`data/fleet/floors.py` — the lay-up window mask is *"BACKCAST ONLY … a forecast run and an unarmed
run both get an empty dict and the drag floors are byte-identical"*, and the flag resolves `False`
besides; `runner.py`'s eia860 vintage hunk, gated `config.mode == "backcast"`;
`config/paths.py::resolve_backcast_eia860_vintage`; `pipeline/backcast_config.py` (the whole module
is the backcast config builder, and its `_ordc_order` addition is `iso.upper() == "ERCOT" else {}`).

**INERT by flag default (resolved `False` for NEISO, per §3.1):** `data/fleet/arrays.py`
(`cc_summer_derate_reconciled_basis` **and** `cc_capacity_reconcile`),
`data/transfer_interface_limits.py` (`pjm_interface_feed_admissibility_gate`).

**INERT — recording only, no solve path:** `results/cache.py` (171 added lines, of which **two**
are code: `import json` and `from …solve_surface import surface_stamp`; the rest is the D76 key
record docstring), `pipeline/persist.py`, `results/export.py`, and **`scripts/run_full_horizon.py`
— this lane's own driver**, whose entire diff is one import plus `"solve_surface": surface_stamp(iso, config)`
written into the summary.

**INERT — no behaviour change:** `model/capacity_evolution/evolve.py` deletes
`exempt_unit_ids=frozenset()`; the parameter was passed the **empty set at the pin** and had no
producer, so its removal is a no-op for every ISO. `config/scenarios.py`'s 879 changed lines land
entirely in the dataclass body and the three cache-key registration tables
(`_CACHE_KEY_OPTIONAL_FIELDS`, `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`,
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, `TIER_TAGS`, `_BACKCAST_ONLY_OVERLAY_FIELDS`) — **no hunk
lands inside `__post_init__`, `cache_key`, `resolve_policy_bundle`, `with_overrides` or `from_yaml`.**

**OUT OF SCOPE for this lane's path:** `scripts/run_calibration.py`, `scripts/run_calibration_full.py`
(backcast lane entry points, never invoked by `run_ces_leg.py`), `scripts/lib/*` (`key_provenance`,
`wind_shape`, `load_forecast/spp`, `nuclear_license_status/spp`, `transmission_expansion/spp`,
`mech_matrix`, `forecast_provenance`).

**No hunk was classified LIVE. Nothing is routed to SCN-DESK on drift.**

---

## 4. The cache keys this campaign will solve on

Derived at HEAD from the pinned default (`tests/regression/test_persisted_identity.py::PINNED_DEFAULT_CACHE_KEY`
lineage) through the same resolution the runner applies — never copied from an older prompt.

| Case | Stage-B key (2026–2050) | Stage-A key (2026–2030) |
|---|---|---|
| REF | `09b7e61d88f83579` | `8878d29743555b45` |
| CAP-STATE-TIGHT | `31e7090a388d7da7` | `89264f98832068de` |
| CES-P60 | `859b3ca99d187974` | `a37868175d5ae724` |
| CES-T80 | `5d22c3d99d9e8d2e` | `ce37aefe169bb82b` |
| CARB-MID | `5a9e78535e28bbbf` *(leg killed — §5)* | *(no Stage-A leg)* |
| ALL-CLEAN | `aaecf1bb07355400` | `cbb53bd42bba88a6` |

The Stage-B and Stage-A keys differ **only** because `end_year` is a keyed field; the mechanism is
the horizon, not a posture change.

---

## 5. PHASE-0 KILL — **CARB-MID is INERT for NEISO across all 25 years** (zero LP)

Rule 29 clause (0): *an arm with a computable pre-solve gate does not reach a solve until that gate
passes.* CARB-MID's gate **fails**, and the proof costs no LP.

**The mechanism.** NEISO's REF posture resolves `carbon_price_path="zero"` with
`state_carbon_pricing=True` — REF already carries the **RGGI** state adder. Owner ruling **S2**
composes a named federal RFF path as a **FLOOR**, not a replacement:
`policy/carbon.py:187` → `resolved_base_trajectory_price = max(program, rff_path_price(path, year))`.

**The measurement.** The composed $/t the LP charges, NEISO 2026–2050:

| year | REF (RGGI) | RFF `mid` | CARB-MID | Δ |
|---|---|---|---|---|
| 2026 | 26.05 | 0.00 | 26.05 | **+0.00** |
| 2030 | 34.15 | 15.00 | 34.15 | **+0.00** |
| 2035 | 47.90 | 25.00 | 47.90 | **+0.00** |
| 2040 | 67.18 | 35.00 | 67.18 | **+0.00** |
| 2045 | 94.23 | 44.00 | 94.23 | **+0.00** |
| 2050 | 132.16 | 50.00 | 132.16 | **+0.00** |

**RGGI strictly dominates the RFF mid path in all 25 of 25 years**, so the floor never lifts.

**The identification is exhaustive, not a sample.** `carbon_price_path`'s only solve-affecting
consumer is `resolved_base_trajectory_price`. Every other reference is inert: `scenarios.py:17498`
is a warning-only `__post_init__` tripwire; `cap_and_trade.py` mentions it **only in prose**
describing the pre-S2 replacement branch that S2 *removed*; `scenario_resolvers.py` is the policy
bundle resolver, already applied before the comparison; `results/cache.py` is a docstring.
The resolved-config diff REF vs CARB-MID is **exactly one field**: `carbon_price_path`
`'zero'` → `'mid'`.

**Therefore CARB-MID's solve is byte-identical to REF's, under a different cache key.** Solving it
would spend ~30 min of LP to reproduce REF's trajectory. **This lane does not solve it.**

**What is reported instead** — this is a campaign result, not an omission: *the RFF mid carbon
path is entirely masked by RGGI in NEISO over 2026–2050; NEISO's reference carbon signal is
already above the federal mid path in every year of the horizon.*

**Routed to SCN-DESK, not acted on.** The same arithmetic shows **CARB-HI is LIVE** — it clears the
RGGI floor in **10 of 25 years** (2033–2043; peak Δ +3.32 $/t at 2038), which is precisely what the
matrix's own comment anticipated when it wrote *"a full-horizon **CARB-HI** is a LIVE arm on NYISO
and NEISO and must not be killed by an inertness argument taken from the T1-F window"* — it names
CARB-HI, not CARB-MID. If the campaign wants a live carbon-price arm on NEISO, CARB-HI is the case
that delivers one. **Substituting it is off-grant and this lane will not do it** (§2). The owner
grants it or it does not run.

---

## 6. Pre-registered predictions — every number this lane will later be scored on

### 6.1 GATE I — the 2026–2030 sub-trajectory identity gate

**Claim:** each Stage-B leg's 2026–2030 sub-trajectory reproduces the Stage-A leg it extends.

**Premise established at phase 0, zero LP.** `end_year` has no solve-path consumer that can reach
years 2026–2030:
- `policy/carbon.py:303, 390` — the only policy reads — are **warning/invariant functions** that
  return a message string and modify nothing. Verified directly: `resolve_carbon_program(cfg, y)`
  for y ∈ 2026…2030 is **identical** under `end_year=2030` and `end_year=2050` for REF,
  CAP-STATE-TIGHT and CARB-MID alike.
- The CCS retrofit remaining-life test is `max(0, _THERMAL_PLANT_LIFE_YEARS - age)`
  (`ccs.py:405`) — plant age against a constant, **not** the config horizon. A 2030-horizon and a
  2050-horizon run screen retrofits identically.
- The remaining `end_year` references are `config/schedulable.py` (the §2.1b window cap),
  `solve_surface.py` (epoch applicability), and `ensemble.py` (not on this path).

**Tolerance (pre-registered):** identity holds iff, for every year 2026–2030 and every leg,
`|HEAD − StageA| / max(1, |StageA|) ≤ 1e-6` on `co2_mt`, `lw_price`, `total_cap_mw`,
`builds_renew_mw`, `retire_mw`, `total_gen_mwh`.

**Prediction: PASS for all five solved legs.** A failure is **a finding about the horizon, not a
licence to re-pin** — it would mean something reads the horizon that this audit did not find, and
it is reported as such.

The Stage-A comparator values (from the committed summaries) are frozen here:

| Case | 2026 CO₂ | 2027 | 2028 | 2029 | 2030 (Mt) |
|---|---|---|---|---|---|
| REF | 15.8319 | 17.0960 | 9.8722 | 4.7566 | 6.1058 |
| CAP-STATE-TIGHT | 20.6700 | 20.0025 | 19.3350 | 18.6675 | 18.0000 |
| CES-P60 | 15.8314 | 17.0942 | 9.8018 | 3.5733 | 3.0664 |
| CES-T80 | 15.8323 | 17.0990 | 9.8418 | 4.7587 | 4.1093 |
| ALL-CLEAN | 16.2812 | 17.7414 | 10.6514 | 5.2369 | 4.4475 |

### 6.2 GATE II — CAP-STATE-TIGHT: the crossing year (the point of this grant)

Ruling **S17** routed CAP-STATE-TIGHT to Stage B for one reason: Stage A measured it a policy
**loosening** — binding in all five years with emissions equal to the budget to 3.2e-13 relative,
a dual of 12.23 → 8.26 $/t against the RGGI adder it **replaces** at 26.05 → 34.15, permitting up
to 293 % more emissions and building **less** clean capacity than REF (2030: 287.4 vs 1,198.0 MW).
The question is whether the glide bites once it has room.

**The resolved NEISO budget** (`mass_cap_tons_by_year`, linear between knots), read at HEAD:

| 2026 | 2027 | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|---|
| 20.670 | 20.003 | 18.000 | 14.700 | 11.400 | 7.750 | 4.100 Mt |

**Definition of the crossing (fixed before the solve):** the **first year `y` in which
`cap(y) < REF_CO2(y)`** — i.e. the first year the mass cap forces emissions *below* what the
RGGI-priced reference produces, which is the year it stops being a loosening and becomes a
tightening.

**PREDICTION: the crossing lands in 2048–2050, and "no crossing within the horizon" is the
explicitly admitted alternative.** Point estimate **2049**. Reasoning, stated so it can be judged:
Stage A's REF CO₂ is already 4.76–6.11 Mt by 2029–2030 against a cap of 18.0 Mt — the cap is loose
by ~12 Mt and the **gap is widening**, because REF CO₂ falls faster than the 80 %-decline glide
while REF's carbon price climbs 34 → 132 $/t. The budget only re-approaches a decarbonising
reference at its 2050 knot of 4.1 Mt. This is a *prediction about the cap's design*, not a target:
**the crossing year is reported whatever it is**, including "never within 2026–2050".

Also reported whatever it is, at full magnitude: the per-year dual, whether emissions still pin to
the budget to numerical tolerance in the late years, and the clean-build comparison against REF.
Ruling **S12**'s 80 % slope and `mass_cap_tons_by_year` **stand as built and are not re-levelled
by this lane.**

### 6.3 GATE III — invariants and registration

Every leg's I1–I14 record is committed as-solved. Any **FAIL** is declared in
`frontend/data/hindcast/invariant-failures.json` **in the same commit as the leg**, and
`scripts/check_forecast_invariants.py --sidecar-dir` is run with its **exit code quoted verbatim**
in the FINDING. No prediction is made that the invariants pass — Stage A's own NEISO legs are the
comparator and their records are committed.

---

## 7. Shard plan and LP budget

Sizes are computed from **each case's own measured Stage-A rate** (its committed
`total_wall_s` over 5 solve-years), not from a single campaign-wide average — the arms differ by
an order of magnitude. Cross-check: the T3 BAU golden ran 25/25 years in 33.0 min = 1.32 min/yr,
against REF's Stage-A-implied 1.08 min/yr, so the REF-class estimate is sound.

| Leg | Stage-A wall (5 yr) | min / solve-year | **Stage-B estimate (25 yr)** | Shard |
|---|---|---|---|---|
| REF | 5.4 min | 1.08 | **≈ 27 min** | S1 |
| CES-P60 | 8.4 min | 1.68 | **≈ 42 min** | S2 |
| CES-T80 | 13.5 min | 2.70 | **≈ 68 min** | S3 |
| ALL-CLEAN | 15.4 min | 3.08 | **≈ 77 min** | S4 |
| **CAP-STATE-TIGHT** | **72.9 min** | **14.58** | **≈ 364 min ≈ 6.1 h** | **S5 (long)** |
| CARB-MID | — | — | **0 — killed at phase 0 (§5)** | — |
| | | | **Total ≈ 9.6 h** | |

**CAP-STATE-TIGHT is the declared exception and gets its own long-running shard.** A full-horizon
leg **cannot be split across shards** — one-pass capacity evolution (rule 10) chains the years and
rule 12 makes years sequential within an invocation — so it is **not** sharded by year. It is
budgeted separately and started first, because it is the long pole and the point of the grant.

**Concurrency:** at most **2** SCN-track solves at once (ruling S14), and never while the capx
track is mid-solve — the owner sequences that half. Shard containers do not compose under rule
12's cap (S16), but the within-invocation half binds inside every shard: one solve at a time,
years always sequential. Peak RSS observed in Stage A is 2.97–3.68 GB per arm.

**Invocation form** (identical for every leg; `--case CES-P20 --set …` for CES-P60 per §2.1):

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
uv run python scripts/run_ces_leg.py \
  --config configs/scenarios/neiso_scenario_base_2026_2050.yaml \
  --matrix configs/scenario_campaign_matrix.yaml \
  --case <CASE> \
  --out-dir results/scn-campaign-stageb-2026-09-07/NEISO/<CASE> \
  --campaign scn-campaign-stageb-2026-09-07 \
  --full-solve-authorized
```

`--full-solve-authorized` lifts the §2.1b five-solve-year cap and is legitimate **only under
S18**, which is cited here and in every shard prompt. The horizon comes from the base config; no
year range is hand-edited.

---

## 8. Retention (rule 31 `[R-RETAIN]`) and registration

**Nothing is deleted because a session judged it unpromotable.** `results/scn-campaign-stageb-2026-09-07/`
is added to `.gitignore` at the outset — that is what discharges rule 29 clause (c) and keeps the
parity sweep green, since `check_registry_payload_parity.py` only ever sees committed dirs. `rm`
happens only on an owner ruling or a genuinely exhausted disk allowance, stated before it is done.
This container is ephemeral, so the promotion question is asked **explicitly** in the final report
while the bundles are still alive.

**Registration is the deliverable, not the solve.** Each leg is registered via the single path
`scripts/register_forecast_run.py --summary <…>/full_horizon_summary.json` into the
`frontend/data/forecast/` namespace (never the backcast registry), **with** its invariant FAILs
declared in `frontend/data/hindcast/invariant-failures.json`, **in the same commit as the leg**.
Then `scripts/check_forecast_invariants.py --sidecar-dir` is run and its exit code quoted. A leg
that solved and did not register did not happen — the PJM Stage-A precedent (ten legs solved,
none registered across three refreshes) is the failure mode this clause exists to prevent.

---

## 9. Files this lane owns / must not touch

**Owns:** `results/scn-campaign-stageb-2026-09-07/NEISO/**`; the NEISO Stage-B sidecars and their
`invariant-failures.json` rows; this PRECOMMIT; `docs/handoffs/FINDING-scn-ws5b-neiso-2026-09-07.md`;
`docs/codebase-site/data/mechanism-matrix/NEISO.js` (LAST commit, after rebase, one appended cell
line — rule 28(b)).

**Must not touch:** `src/market_sim/**`, `scripts/**`, `configs/**`, `tests/**`, any other ISO's
matrix shard or results tree, the backcast namespace, `frontend/data/forecast/program-status.json`,
`ff-verdicts.json`, the desk ledger, and the plan's §5.1 — §5.1 rows are **routed to SCN-DESK in
the FINDING**, never written here, because SCN-WS5A-POLICY-SYNTH is writing that table in the same
window.

**Known seam, reported and NOT fixed** (ruled D-15/S19, routed to the capx director):
`ccs.py:475-476` prices the CCS retrofit uplift with
`effective_eac_price_for_unit = max(legacy eac_price_*, CES premium × credit)` and never reads
`clean_attribute_price_by_fuel`, so a CES **TARGET**-row dual is invisible to the retrofit screen
while a **premium** is not (NYISO measured CES-T80's $50 ACP buying 0.0 MW where CES-P20's $20
buys 1,475.8 MW at 2030). **CES-T80 and CES-P60 sit on opposite sides of that seam**, so this lane
will not compare them as "one instrument at two levels" without saying so first, and will not edit
`ccs.py`.
