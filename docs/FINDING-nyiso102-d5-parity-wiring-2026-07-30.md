# FINDING — nyiso-102: the D-5 parity FAIL was a forecast-orchestrator wiring gap, not a declaration gap

**Session:** nyiso-102 · **Date:** 2026-07-30 · **ISO:** NYISO
**Keeper:** `2026-07-30-nyiso-100-silretire` — **UNCHANGED** by this session.
**Scope:** `src/market_sim/runner.py` (forecast orchestrator) + tests + matrix. **No LP delta on the backcast.**

---

## 0. Headline

The standing D-5 FAIL on `nyiso_local_selfsupply` — carried unchanged by
nyiso-98 / 99 / 100 and reproduced in nyiso-100's own zero-delta control — is a
**genuine forecast-mode wiring gap**, not the declaration-list gap the charter
proposed as the likely cause. Three NYISO downstate mechanisms were called only
from the backcast orchestrator (`scripts/run_calibration.py`); the forecast
orchestrator (`src/market_sim/runner.py`) never referenced them. Wiring all
three into `runner.py` clears the gate.

**D-5 now PASSES on the keeper's own config, with every remaining row a
`declared` overlay.** The backcast dispatch is byte-identical — proved three
ways (§5), not asserted.

The charter offered two candidate fixes ("does it belong on the declared list,
or is its backcast-only gating the bug?"). **Neither is quite right**, and the
distinction matters:

* Declaring it would be **wrong** (§2). It is market design, not an overlay.
* The backcast-only gating *is* a real bug — but it is **not** what makes this
  keeper fail, because in this config the mechanism is **inert on both sides**
  (§3). The gate fires on a config flag, not on realized activity.

So the FAIL was simultaneously **a true defect** (a real forecast gap, latent
today) and **a false positive for this keeper** (the named mechanism forces zero
energy here). Both are recorded; only the defect is fixed.

---

## 1. The failure, exactly as committed

From `results/calibration/nyiso100_silretire/legitimacy_diagnostics.json`:

```
nyiso_local_selfsupply: active backcast-only for this config but NOT on the
declared backcast-overlay list (docs/backcast-measured-data-audit-2026-06.md)
```

| field | value |
|---|---|
| `difference` | `backcast-only` |
| `declared_overlay` | `false` |
| `note` | "LMIC market-design rule — mode-independent by intent" |
| `verdict` | **FAIL** |

D-5 (`scripts/legitimacy_diagnostics.py::run_d5`) measures wiring by **source
text**: for each registry row whose config toggle is on, it checks whether the
row's builder symbols appear in the backcast entry source and the forecast entry
source, and fails any undeclared difference. The registry row is:

```python
MechanismSpec("nyiso_local_selfsupply", "nyiso_local_selfsupply", "both", False,
              backcast_symbols=("inject_nyiso_local_selfsupply",),
              forecast_symbols=("inject_nyiso_local_selfsupply",),
              note="LMIC market-design rule — mode-independent by intent")
```

Measured on the real sources before the fix:

| symbol | `scripts/run_calibration.py` | `src/market_sim/runner.py` |
|---|---|---|
| `inject_nyiso_local_selfsupply` | 3 occurrences | **0** |
| `apply_nyiso_li_tsl_import_cap` | present | **0** |
| `apply_nyiso_nyc_tsl_import_cap` | present | **0** |

`mode="both"` + wired in one entry only ⇒ undeclared `backcast-only` ⇒ FAIL.

---

## 2. Why declaring it would have been wrong

`nyiso_local_selfsupply` is not a measured overlay. Its own definition
(`config/scenarios.py`) states the test rule 13 `[R-MEASURED]` asks for:

> **FORWARD-REPRODUCIBLE** (scales with load, responds to conditions) and
> grounded in NYISO market design — **NOT a pin to measured LI generation**.

It floors in-zone thermal at `frac × zonal load` in the HB14-21 design-cooling
window. It consumes no measured outcome, would regenerate for any forward year
from forward load, and responds to changed conditions — so it passes rule 13's
admissibility test as a *market-design mechanism*, and its registry row records
that intent as `mode="both", declared=False`.

Adding it to the declared backcast-overlay list would have asserted the
opposite: that an LMIC self-supply rule is a historical overlay with no forward
analogue. That is false, it would have silently sanctioned the real forecast gap
forever, and it is precisely the move rule 1 `[R-STRUCT]` forbids — reaching a
green indicator through a change that isn't the real fix.

---

## 3. The nuance the charter did not anticipate: the mechanism is INERT in this keeper

`NYISO_LOCAL_SELFSUPPLY_FRAC` contains **exactly one** pocket:

```python
NYISO_LOCAL_SELFSUPPLY_FRAC: dict[str, float] = {"Long_Island": 0.45}
```

The keeper runs `nyiso_li_lcr_tsl=True`, and the backcast call site passes:

```python
_selfsupply_exclude = frozenset({"Long_Island"}) if config.nyiso_li_lcr_tsl else frozenset()
```

`inject_nyiso_local_selfsupply` iterates the single pocket, hits `continue` on
the exclusion, and returns `False` — **no floor, byte-identical**. This is
correct and deliberate: the Zone-K LCR/TSL import cap *replaces* the 0.45 energy
floor for Long Island (rule 19 `[R-ONE-MECH]`, never stacked).

Confirmed in the keeper's own committed diagnostics: **D-2 attributes zero rows
and zero forced energy to `nyiso_local_selfsupply`** (0 of 20 D-2 rows; 0 of 15
D-4 rows).

So D-5's `_toggle_on` reads the raw config flag and concludes the mechanism is
active, while the rule-19 exclusion has already reduced it to nothing. **In this
config the gate reports a parity difference for a mechanism that is not active
on either side.**

This is a real coarseness in D-5 — but it is **deliberately left alone**. The
honest fix is to make the mechanism genuinely mode-independent (which the gate
then measures correctly); teaching the gate to excuse an inert mechanism would
weaken a legitimacy gate to silence a symptom, and would still leave the
forecast gap open for any config with `nyiso_li_lcr_tsl=False` — where the floor
*is* live in backcast and *was* absent in forecast. Recorded here as a known
property, not patched.

---

## 4. The fix, and why the LCR/TSL caps had to travel with the floor

`src/market_sim/runner.py` now calls all three, each behind its existing gate
(all default-off, NYISO-only):

1. **`inject_nyiso_local_selfsupply`** — placed after the availability derates
   (`apply_neiso_coldsnap_derate`, `apply_correlated_outage_derate`) so the
   floor's "never demand more than the in-zone fleet can supply" clamp sees
   final availability. Same ordering as the backcast orchestrator. Carries the
   identical rule-19 `exclude_zones` logic.
2. **`apply_nyiso_li_tsl_import_cap`** and
3. **`apply_nyiso_nyc_tsl_import_cap`** — applied to `year_ttc` inside the year
   loop, after the CAISO per-year and transmission-expansion TTC swaps, before
   `DispatchSpec` reads it. Both accept a 1-D TTC and broadcast to `(hours,
   n_links)`, the same expansion the backcast path performs.

**Why not the floor alone.** Wiring only `inject_nyiso_local_selfsupply` would
have turned D-5 green while leaving the substantive gap open, because
`nyiso_li_lcr_tsl` is *exactly what excludes the only pocket the floor has*. A
forecast run carrying the keeper's config would then have found the floor
excluded (the flag is on) and the cap unwired (never called) — **neither
mechanism on the downstate pocket**, with the gate reporting parity. That is
gate-gaming in the precise sense rule 1 names, so the caps ship with the floor.
`tests/scoring/test_legitimacy_diagnostics.py::TestD5NyisoDownstateParity::
test_lcr_tsl_caps_travel_with_the_floor` pins this invariant.

**Precedent.** This is not a new pattern. `runner.py` already carries
`apply_neiso_coldsnap_derate` annotated *"orchestrator-unification Stage 6:
previously wired only in the backcast orchestrator, the plan's §2.2
accidental-drift row"* — the same defect class, same remedy. The NYISO downstate
family is another §2.2 row.

**Why a direct call rather than a shared wrapper.** The Stage-6 wrappers
(`apply_netload_drag_floors`) are called by both orchestrators under a *new*
name. Routing these through such a wrapper would remove the literal symbol
`inject_nyiso_local_selfsupply` from `run_calibration.py`, making D-5 see it
unwired on *both* sides — which also "passes", for a bogus reason. Direct calls
keep both entry sources honestly measurable by the gate that checks them.

---

## 5. Byte-identity of the backcast — proved three ways

The change touches only the forecast orchestrator, so no backcast solve can move.
Asserting that is not enough (charter instruction), so:

**(a) Static.** No file in the backcast entry chain —
`scripts/run_calibration_full.py`, `scripts/run_calibration.py`,
`src/market_sim/pipeline/solve.py`, `src/market_sim/pipeline/commitment.py` —
contains any reference to `market_sim.runner`. The only module that names it is
`pipeline/api.py`, the forecast facade, and it imports lazily inside functions.

**(b) Runtime import graph.** Importing the backcast entry module never loads
the forecast orchestrator:

```
>>> import scripts.run_calibration; 'market_sim.runner' in sys.modules
False
```

Pinned as a regression test
(`TestD5NyisoDownstateParity::test_backcast_chain_never_loads_the_forecast_orchestrator`).

**(c) Empirical — a same-HEAD zero-delta control.** `scripts/replay_keeper.py`
replays the keeper's own `meta.json` (so the fix is the only delta) across
**2023 2024 2025 in one sequential invocation** (rule 16) into
`results/calibration/nyiso102_ctrl_zerodelta`, compared against the committed
keeper hourlies. Result in §6.

---

## 6. Result

D-5 on the keeper's config, re-run against the fixed sources:

```
## D-5 forecast/backcast parity — PASS
```

12 rows → 11, all `declared`. The `nyiso_local_selfsupply` row is **gone
entirely** — not downgraded to a sanctioned difference, but absent, because
`active_backcast == active_forecast` is now true and D-5 emits no row at all.
This is the correct shape of the fix: the gate stops reporting a difference
because there is no longer a difference.

Zero-delta control vs the committed keeper: see §7 and the calibration log entry.

---

## 7. Blast radius on the forecast lane

**None today.** All three flags default `False`, and no forecast driver or
recipe sets any of them (`scripts/run_capacity_hindcast.py`, the T1-F/T1-X/T1-H
lanes, the ensemble/matrix modules — none reference them; forecast configs do
not inherit backcast keeper configs). Every existing forecast run is therefore
byte-identical too; what changed is that the mechanisms are now **reachable**
in forecast mode rather than silently dropped.

Matrix consequence: `lcr_tsl_published` has always declared `mode: "BF"`, but
its forecast half was unreachable in code. nyiso-102 makes the declared mode
true and records `fc: "..UUU."` — NYISO forecast lane **U**, reachable but
untested, not **K**.

---

## 8. What this does NOT touch

* **The keeper is unchanged.** No re-solve, no promotion, no gate re-scoring
  beyond D-5's own scorer-only regeneration (rule 20).
* **C3c** remains the sole determination blocker; determination stays NOT-YET.
  This fix is not aimed at it and does not move it.
* **The ISO's tightest cell** (2023 CC_REGULAR, −2.80 of ±2.94) spends
  **0.00 TWh** of its ~0.14 TWh budget: the backcast dispatch does not move.
* **Item B of the charter** (`nyiso_gas_commitment_bridge`) was **already armed
  in the keeper** before this session — see §9.

---

## 9. Correction to the charter: Item B was already done

The charter offered Item B as "the only remaining armable NYISO lever
(default off)". That describes the **`ScenarioConfig` default**, not the
keeper's state. `2026-07-30-nyiso-100-silretire` already runs the bridge, at the
measured parameters, with the peak-window floors off exactly as the owner
directive requires:

| field | keeper value | source |
|---|---|---|
| `nyiso_gas_commitment_bridge` | `true` | `meta.json`, `run_config.json` |
| `nyiso_gas_bridge_cc_min_load_frac` | `0.523` | ScenarioConfig default (measured, WP-3) |
| `nyiso_gas_bridge_st_min_load_frac` | `0.239` | ScenarioConfig default (measured, WP-3) |
| `nyiso_gas_bridge_min_run` | `true` | `meta.json` |
| `nyiso_gas_bridge_cc_min_run_hours` | `21` | `meta.json` |
| `nyiso_gas_bridge_st_min_run_hours` | `13` | `meta.json` |
| `nyiso_gas_bridge_startup` | `true` | `meta.json` |
| `reliability_floor_overrides` | the 5 `NYISO_PEAK_WINDOW_FLOORS_OFF` limbs | `meta.json` |

Armed since `2026-07-29-nyiso-99-demandfix` (the matrix's
`caiso_p1_export_sink_seam` row already cites NYISO as exposed *because*
`nyiso_gas_commitment_bridge` is armed there). Confirmed live in this session's
control solve log:

```
NYISO gas commitment bridge: 34998 unit-hours floored (2.32 TWh floor volume),
3875 floored segments {'<4h': 813, '4-8h': 1121, '8-16h': 1098, '16-24h': 838,
'>24h': 5} (min_run extension ON)
NYISO gas bridge leg gas_st (min_load_frac 0.239, min_run 13h): 5161 unit-hours
floored, 0.1363 TWh floor volume
```

Re-arming it would have been a no-op A/B against itself. **Item B needs no
session**; the charter's next NYISO lever queue should drop it.

---

## 10. Files

| file | change |
|---|---|
| `src/market_sim/runner.py` | wire the three NYISO downstate mechanisms into the forecast orchestrator |
| `tests/scoring/test_legitimacy_diagnostics.py` | `TestD5NyisoDownstateParity` — 4 regression tests on the REAL entry sources |
| `docs/codebase-site/data/mechanism-matrix.js` | `lcr_tsl_published` → `fc: "..UUU."` + nyiso-102 note/evidence |
| `results/calibration/nyiso100_silretire/legitimacy_diagnostics.json` | D-5 block regenerated in place (scorer-only, rule 20) |
| `docs/calibration-log/nyiso.md` | session entry |
