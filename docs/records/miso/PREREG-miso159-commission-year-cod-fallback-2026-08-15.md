# PREREG — miso-159: repair the `_commission_year` hardcoded-2010 fall-through with the fleet's own measured EIA-860 COD (`commission_year_cod_fallback`)

**Session** miso-159 · **ISO** MISO · **Date** 2026-08-15 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`) ·
**Model** `claude-fable-5`.

Registered BEFORE the construction is built, before any adjudicating statistic
is computed, and before any LP is solved. Pushed to the session branch and
byte-verified against the fetched remote ref per rule 27 `[R-PUSH]` before
Phase 1 begins.

---

## 1. Provenance — why this lever, and why now (rule 28(a))

The MISO lever queue is **EMPTY of named, un-adjudicated candidates**
(miso-156 §8, re-affirmed miso-157 §10). This session is not going off-queue:
it executes **the construction miso-157 §11 item 1 prepared for the owner** —
the `_commission_year` vintage defect — whose rule-25 `[R-ISO-SCOPE]`
prerequisite (the cross-ISO exposure census) was discharged by miso-158
(`results/calibration/_miso158_vintage_census.json`, PR #3966, merged
2026-08-15). The owner's standing instruction to this session is to pick the
workstream up from the current keeper and drive toward a calibrated backcast;
the prepared, censused repair is the sanctioned next step.

**The defect** (miso-157 §7, measured at 100.0 % EIA-860 capacity coverage):
`data/fleet/assembly.py::_commission_year` looks each plant up in
`master-plant-registry.csv` and falls through to a **hardcoded `return 2010`**
on a miss. The registry is 833 rows, `ba_code='ERCO'` for all 833, so MISO's
plant codes intersect it at **zero** and the fall-through is total: **every
plant-group-tagged thermal row in MISO's fleet — 108.70 GW across 7 classes —
carries `online_year = 2010`**, and the age-escalation limb of
`THERMAL_AVAILABILITY` (WEFOR `+w_rate`/yr past `w_onset`; DERATE
`+d_rate`/yr past `d_onset`) is **identically inert** (0.000 GW past onset in
every class, every training year). True cap-weighted vintages (census):
COAL 1982.0, ST_GAS 1976.8, ST_CHP 1980.6, CT_CHP 1995.2, CT_PEAKER 1998.7,
CC_CHP 1999.6, CC_REGULAR 2006.5 — against a uniform model 2010.

This is a rule-14 `[R-ACCURATE]` / rule-5 `[R-NO-MAGIC]` input error with a
measured, in-repo replacement, and repairing it **removes** a magic literal's
reach rather than adding a knob.

## 2. The construction — one boolean, zero continuous DOF

**New `ScenarioConfig` field: `commission_year_cod_fallback: bool = False`.**

When `True`, `_commission_year`'s fall-through consults
`market_sim.data.cod_ramp.load_cod_map()` — the repo's **single COD source**
(module docstring), the capacity-weighted per-plant EIA-860
`(Operating Year, Operating Month)` reduction that ALREADY drives every
backcast's monthly online mask, resolved through `paths.active_eia860_dir()`
so the keeper's EIA-860 vintage pinning is honored — **before** the 2010
literal. Precedence, in order, is otherwise unchanged:

1. `COAL_PLANT_COMMISSION_YEAR` (curated per-plant coal years) — untouched;
2. `master-plant-registry.csv` `year_built` — untouched (ERCOT's curated
   registry stays authoritative where it hits; its keepers were solved on it);
3. **NEW, gated:** `load_cod_map()[plant_code].online_year`;
4. the 2010 fall-through — now reachable only for plants absent from both the
   registry and the EIA-860 COD map (census: 0.0–0.6 % of capacity per ISO),
   disclosed rather than silently clamped.

**Zero continuous degrees of freedom:** a boolean over a measured registry.
No tunable year, no per-class scale, no sweepable tolerance, and no
parameterised variant is built or solved. The COD reduction itself is not
edited — the mechanism *reuses* the existing, tested reduction (rule 19
`[R-ONE-MECH]`: one COD source for both the online mask and the age model,
where today the mask uses measured CODs and the age model uses a fiction).

**Cache-key discipline** (nyiso-119 / caiso-186 / miso-148): the field is
registered in `_CACHE_KEY_OPTIONAL_FIELDS` and the pinned-defaults ledger IN
THE SAME COMMIT as the field, so every pre-existing default-config cache key
is byte-stable and an armed run gets a distinct key.

**Scope when armed at MISO** (this session arms MISO only; every other ISO's
cell enters `U` per rule 25 and no verdict transfers): plants reached through
`bins_to_fleet` with a `plant_group` in `THERMAL_AVAILABILITY`. The monthly
COD online mask is unchanged for plants in the COD map (it already reads the
map directly); `Generator.online_year` changes only where the registry
misses, i.e. for MISO everywhere except the curated-coal dict's hits.

**What this is NOT** (rule 19): not an outage-source change
(`miso_native_outage_source` untouched), not a `SUMMER_WEFOR_SHARE`
adjudication (that stays an open rule-20 DOF-ledger item pending the owner's
data-provenance decision, miso-157 §11 item 2), not a POF/derate-table edit
(`THERMAL_AVAILABILITY` values untouched), and not a capacity rescale.

## 3. Validity gates — all run BEFORE any adjudicating statistic

* **V1 (instrument ↔ census):** with the flag ON, the built MISO fleet's
  per-class capacity-weighted `online_year` must reproduce the miso-158
  census's `true_capwt_online_year` to **±1.0 yr** per class. (The census used
  `vintage_2024/eia860_generators.parquet` cap-weighted `operating_year`;
  `load_cod_map()` uses the operable schedule + within-window retiree union,
  capacity-weighted continuous (year, month). These are two reductions of the
  same filing; a bounded difference is expected and reported, a breach stops
  the session.)
* **V2 (off-path byte-inertness):** with the flag OFF (default), the built
  fleet's `online_year` vector is **byte-identical** to HEAD's, and the pinned
  default cache key does not move
  (`tests/unit/config/test_cache_key_default_flip_guard.py` passes).
* **V3 (the keeper's own fleet):** both arms carry the keeper's `n_gen`
  (2929 / 2923 / 2923) and 6 carry zones.
* **V4 (`weather_year` pinned per solve year)** — inherited from the replay
  driver; the control's reproduction of the keeper at the gated grain is its
  control.

## 4. Phase plan

* **Phase 0 (no LP):** build the construction; run the instrument probe
  (`scripts/probes/_miso159_cod_vintage_instrument.py`): V1/V2 gates, the
  per-class `online_year` and availability deltas (flag on vs off) at annual
  and Jun–Sep grains, reproducing the census's overstatement table from the
  production fleet path.
* **Phase 1 (two solves, rule 12):** same-HEAD A/B via the sanctioned replay
  channel, sequentially (MISO peaks ≈10.8 GB RSS; this box has 15 GB —
  the rule-12 concurrency cap binds at 1 here):
  - **Control A:** `replay_keeper.py miso148_basis_B --out-dir
    results/calibration/miso159_cod_A` (zero-delta).
  - **Arm B:** same `--set commission_year_cod_fallback=true --out-dir
    results/calibration/miso159_cod_B`.
  Years 2023 2024 2025, one invocation each, sequential within each (rule 12).
* **Phase 2:** score both bundles (`calibration_verdict.py`), register BOTH
  runs on the dashboard (rule 15), update the MISO matrix shard cell + the new
  mechanism's base row + a cell line in every ISO shard (rule 28(b)/(c)),
  calibration-log entry, keeper decision per §7.

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only. MISO holds **neither**
`complete` nor `final`; the holdout spend freeze is ACTIVE. No out-of-training
year is read, solved, scored or registered by this session.

## 5. Priors — registered before measurement

All deltas are **arm B − control A**, never arm − committed-predecessor
(the miso-124 DO-NOT-MISREAD; miso-148's K0 showed the committed keeper need
not be bit-reproducible at a later HEAD).

* **P-1 (mechanism reach, from the census, restated as the fleet-path
  expectation):** summer capability removed (non-CHP classes)
  **1.8–2.8 GW** in each year (census: 2.060 / 2.272 / 2.488 GW); annual
  capability removed **3.0–5.0 GW** (census: 3.550 / 3.952 / 4.367 GW).
  Largest single class COAL, then ST_GAS, then CT_PEAKER
  (2025: +1.339 / +0.580 / +0.494 GW summer).
* **P-2 (price direction):** system demand-weighted LMP moves **UP in all
  three years** — capability only shrinks. Registered against interest for
  disclosure symmetry with miso-148 (whose repair moved prices down into an
  already-low 2025): this repair moves prices *toward* the failing gates, so
  any improvement it produces must NOT be quoted as calibration skill — it is
  adopted, if at all, on rule-14 structural fidelity, exactly as miso-148 was
  adopted against the same gates' direction.
* **P-3 (magnitude band, annual demand-weighted):** **+0.3 to +3.0 $/MWh** in
  2025, smaller in 2023/2024. Arithmetic anchor, not a fit: the removed
  capability (~2.5 GW summer / ~4.4 GW annual) against miso-142's measured
  model stack slope ($0.64/GW summer afternoon) and miso-153's 6.31 GW
  within-$20 cushion. The C3a-2025 gap is +7.08 $/MWh:
  **this lever is NOT expected to close C3a on its own**, and a residual move
  smaller than the gap is the expected result, not a failure (miso-157 §6
  precedent).
* **P-4 (2023 against-interest bound, computed at miso-156 §8):** a uniform
  lift of 2023's annual mean by more than **+3 %** (≈ +$0.97/MWh on the
  control's ~$32.2 mean) makes 2023's |C3a| WORSE than the control's 1.98 %.
  Prior: the 2023 lift lands **below** +3 % (P-3's band scaled by 2023's
  smaller overstatement). If it breaches, S-2023 fires (§6).
* **P-5 (composition):** aged COAL/ST_GAS run less; CC_REGULAR/CT_PEAKER pick
  up part of the displaced energy; net thermal down, imports/storage up
  marginally. C1 class errors move ≤ 2 TWh per class (band: no class's |C1
  error| grows by > 2 TWh).
* **P-6 (fail-set):** the control reproduces the keeper's determination
  (NOT-YET, fails exactly {C3a-2025, C3b-2025}); the arm's fail set is a
  **subset of {C3a, C3b}** (per-year: no criterion-year that PASSES in the
  control flips to FAIL in the arm).

## 6. Triggers

* **S-2023** — the arm's 2023 C3a |error| exceeds the control's (i.e. the
  lift breached P-4): report at full magnitude; promotion is then **blocked
  pending owner escalation** (the miso-148 route), never silently taken.
* **S-FLIP** — any criterion-year that PASSES in the control FAILS in the arm
  (P-6 breach): same escalation route. The C8 budgets and D-4 windows are
  re-read from the arm's own `legitimacy_diagnostics.json`, not assumed.
* **S-ZERO** — any adjudicating delta comes back exactly 0.0: per T-3
  (three consecutive MISO sessions' precedent), a clean zero gets a second
  derivation before it is believed (mis-wiring, stale cache key, and the
  flag-not-reaching-the-solve are the named suspects, in that order).
* **S-CACHE** — the arm's bundle records the same `scenario_config_sha256` as
  the control's: stop — the field did not enter the cache key and the arm may
  have read the control's cached fleet.
* **S-V1** — the V1 gate breaches ±1.0 yr in any class: stop, debug, disclose
  (miso-157 §3 protocol); no adjudicating statistic is quoted first.

## 7. Decision rule — fixed now

* **V1/V2/V3 pass + P-6 holds (fail set ⊆ {C3a, C3b}, no new criterion-year
  FAIL):** the arm is **PROMOTED to keeper** on rules 1 `[R-STRUCT]` / 14
  `[R-ACCURATE]` — a measured input replaces a magic literal on the
  price-setting fleet; the residual's direction of travel is disclosed and is
  not the ground of adoption. Both runs registered; matrix MISO cell → `K`.
* **Any S-trigger fires on the gates (S-2023 / S-FLIP):** both runs are still
  registered (rule 15), the matrix cell records the measured verdict, and the
  promotion question **escalates to the owner** with the full-magnitude
  scorecard — the miso-148 protocol, which this PREREG adopts by name.
* **The mechanism is dispatch- and price-inert (S-ZERO resolved as genuinely
  inert):** cell → `I` with the measured bound; the code stays (default-off);
  no promotion.
* In no case is the flag tuned, scoped, or re-parameterised in response to
  the residual within this session (rule 20 `[R-DOF]`).

## 8. Traps carried forward

T-1 bundle assertion (the probe asserts the control/arm bundle paths it
reads); T-2 zero 3-arg `getattr` in new probe/mechanism code — the new config
read is a direct attribute access that fails loudly on a rename; T-3
disbelieve clean zeros (§6 S-ZERO); T-4 production types only
(`generators_to_fleet_arrays`, no `SimpleNamespace`); T-5 `MISO_external*`
are import nodes (6 carry zones asserted); T-6 `weather_year` pinned per
solve year (replay driver); T-7 every delta reported in physical units (GW,
$/MWh) as well as shares; T-8 production functions, never re-implementations
(`load_cod_map.__module__` asserted in the probe); T-27 **does not apply and
its absence is the point**: unlike miso-157's chartered share this mechanism
is *deliberately* a level change (the DERATE leg is flat year-round), so the
annual-mean-invariance check is replaced by its opposite — the annual
capability delta must be **negative** and within P-1's band.

---

*Artifacts this session will produce:* `scripts/probes/_miso159_cod_vintage_instrument.py`,
`results/calibration/_miso159_cod_vintage_instrument.json`, bundles
`results/calibration/miso159_cod_A` / `miso159_cod_B`, runs
`2026-08-15-miso-159-control` / `2026-08-15-miso-159-cod-vintage`, a FINDING,
matrix row + cells, and the calibration-log entry.
