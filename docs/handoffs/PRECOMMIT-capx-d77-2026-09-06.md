# PRECOMMIT — capx D77: the CCS retrofit emission-rate seam

**Lane:** capx D77 · **Branch:** `claude/capx-d77-ccs-emission-rate-seam-pvfezi` (fresh off
`origin/main` `2fa2f23a`) · **Date:** 2026-09-06 · **Model:** `claude-opus-5` (rule 27 `[R-PUSH]`)
**Data profile:** `neiso` · **Charter:** pack §D77 + `FINDING-scn-ws2b-2026-09-06.md` §5.3 / §8 item 1
**Pushed BEFORE the screen solve.** Every number below was produced with ZERO LP.

---

## 1. Phase 0 — the premise, reproduced (zero LP)

WS2b's leading candidate is **CONFIRMED**, not merely plausible. The overwrite is
`data/fleet/campd_bins.py::apply_plant_emission_rates_v2`, reached from
`data/fleet/assembly.py::build_dispatch_fleet`, which `runner.py` calls at **line 2479 —
after `evolve_fleet` at line 2237** — in every forecast year.

The quoted overwrite, pre-fix:

```python
# src/market_sim/data/fleet/campd_bins.py, apply_plant_emission_rates_v2
for gen in generators:
    triple = rates.get((int(gen.plant_code), fuel_class(gen.fuel_type)))
    if triple is None:
        continue
    co2, nox, so2 = triple
    touched = False
    if co2 > 0.0:
        gen.emission_rate_co2 = co2        # <-- restores the UNCAPTURED host rate
```

Three facts make it bite, each measured:

1. **`fuel_class("gas_cc_ccs") == "gas"`** — conversion does not escape the match key, so a
   retrofitted unit still finds its own host plant's measured **gas** row.
2. **The map's value is exactly WS2b's number.** The NEISO 2028 forecast-mode v2 map has 69
   `(plant, class)` rows, 45 of them gas; the plant whose measured rate is closest to WS2b's
   0.3745 is **plant_code 55041 at 0.3745 t/MWh** — the observed "0.3745 → 0.3745" is the
   measured host rate being re-booked, to four decimals.
3. **Driving a post-retrofit unit through the function reproduces the defect exactly.** A
   generator carrying `fuel_type="gas_cc_ccs"`, `heat_rate=8.4113`, `emission_rate_co2=0.0375`
   (i.e. `0.3745 × 0.10`) comes out at **0.3745 — 10.0× its intended rate.** An unabated sibling
   at the same plant is unchanged, so the function is correct for everything except a converted
   unit.

**Why two of ccs.py's three writes survived and one did not:** this function writes CO2, NOx and
SO2 only. `heat_rate` and `fuel_type` are never touched by it, so they persist; `emission_rate_co2`
is assigned unconditionally. That also answers WS2b's "why did the rate not follow the 12 %
heat-rate rise" — the forward-year rate is a **plant-keyed CAMPD measurement**, not a
recomputation from the model's heat rate, so no heat-rate linkage exists on this path for an
abated or an unabated unit alike.

**It is NOT a stale FleetContext and NOT a cache-invalidation seam.** Two independent reasons:
`FleetContext.from_arrays` (`runner.py:3568`) is built from that same year's `fleet_arrays`, so it
reports what actually dispatched; and on the CAMPD path — NEISO's, `use_campd_bins=True` —
`build_dispatch_fleet` opens with `dispatch_fleet = fleet + inline_imports`
(`assembly.py:1881`), a list concatenation, **not a copy**. The override therefore mutates the
**persistent** generator objects, which is why WS2b saw 0.3745 again in 2029 and 2030 and why the
next year's retirement and CCS screens (`retirements.py:2382`, `:3300`) also read the uncaptured
rate.

**Semantics the repair must preserve (rule 13 `[R-MEASURED]`).** The forward-year rate for an
existing unit is the multi-year CAMPD-derived measured rate — an admissible measured input, not
an overlay. The measured quantity is the **host stack's** intensity. A unit with a capture island
therefore emits `measured_host_rate × (1 − capture)`: the measured input still enters, every year,
and the capture applies on top. A converted unit is never silently returned to its uncaptured rate.

## 2. Phase 1 — the fix

**Route chosen: apply the capture at the point the measured rate is restored.** The alternative —
exempt converted units from restoration, leaving `ccs.py`'s write standing — was enumerated and
**rejected on structure, not on any residual**, for three reasons:

- the same override also books **NOx and SO2**, and a CCS retrofit does not zero a unit's NOx/SO2
  measurement; exempting the unit would silently freeze both (and, under
  `control_retrofit_forward`, drop its announced SCR/FGD stepping);
- it freezes the CO2 basis at the retrofit year, so a lane whose estimator basis moves per year
  (the hindcast `as_of_year` bound) would drift away from the measured input — the opposite of
  rule 13;
- it puts the capture in one file and the exemption in another, which must then agree
  (rule 19 `[R-ONE-MECH]`).

**Mechanism:** one new **Generator** attribute, `ccs_capture_fraction: float = 0.0` — a physical
property of the unit, not a `ScenarioConfig` field and not a tunable (rule 24 `[R-REGISTRY]`). It
is stamped at the two places a capture island comes into existence
(`ccs.py::apply_ccs_retrofit` ← `config.ccs_retrofit_capture_rate`; `new_entry.py`'s CCS build ←
`config.ccs_capture_rate`) and read at the one place a measured host rate is booked, in both
override functions:

```python
gen.emission_rate_co2 = co2 * (1.0 - float(gen.ccs_capture_fraction))
```

**Zero DOF (rule 21 `[R-DOF]`):** the value is always one of two already-registered
`ScenarioConfig` fields; nothing is chosen, nothing is swept, no residual can be closed by it. No
new `ScenarioConfig` field ⇒ **no gate, no default, no matrix row** (rule 28 duty (c) is not
engaged). NOx/SO2 are deliberately **not** scaled — the model carries no capture co-benefit
parameter and inventing one would be a new free parameter.

**Deliberately NOT changed, and routed instead.** `ccs.py` computes the residual as
`old_er × (1 − capture)` and the captured tonnage as `old_er × capture`, both off the
*unpenalized* rate, while the retrofit raises the heat rate 12 %. Physically the parasitic load
raises gross stack CO2 per **net** MWh, so the residual would be
`old_er × (1 + pen) × (1 − capture)`. That is a **different, second-order defect** in the screen's
own capture arithmetic; correcting it would move the §45Q and transport economics and therefore
the retrofit set. **Out of scope here** — this fix makes the dispatch fleet agree with `ccs.py`'s
stated semantics and nothing more. Routed to the director in the FINDING §8.

**Tests:** `tests/unit/model/test_ccs_retrofit_rate_seam.py`, 10 cases — the WS2b table as a seam
test (a unit's rate across its own retrofit year, through the restoration), the three untouched
writes, the explicit "the rate does NOT follow the heat-rate rise, and here is why" pin, a
non-cohort control, idempotence across 2029/2030, NOx/SO2 unscaled, the v1 branch, and the
unabated-fleet no-op.

## 3. Cache: BEHAVIOUR MOVES, NO KEY MOVES — the pre-declared re-resolution

**Measured, pre- and post-fix, on the same tree** (`git stash` of `src/market_sim` only):

| config | pre-fix | post-fix |
|---|---|---|
| `ScenarioConfig()` default | `e5ecd4105ada3e58` | `e5ecd4105ada3e58` |
| bare backcast | `6a2845e50951394e` | `6a2845e50951394e` |
| bare ERCOT / CAISO / PJM / MISO / NYISO / NEISO 2026–2030 | `78b01278f2eb64eb` / `41367ccc55859d4c` / `577a950add853227` / `a6b9ed663987311b` / `81af4882eeda50f5` / `f1b2dc5e9f2a47e3` | **identical** |

**Every key is unmoved.** This is the same-key invalidation class the ledger exists for and the
2026-08-31 entry's predicted recurrence: a pre-fix bundle whose horizon reaches 2028 sits at
**exactly** the key a post-fix run computes, so the post-fix run will silently serve the pre-fix
bundle unless the bundle is purged or re-solved.

**INVALIDATED — pre-declared, before any solve.** Every `results/<ISO>/<key>/` **forecast-lane**
bundle whose horizon reaches **2028** (`ccs_retrofit_available_year`) *and* whose fleet contains a
retrofitted unit. Census of the committed evidence in FINDING §8; the concrete bare keys a
re-solve at HEAD would re-resolve are the six above plus the per-bundle keys named there —
`5e2c52ea81694c10` (NEISO bare t1f / WS2b BAU), `18515067bf4d2fbe`, `8ebed20ae90ec0e7`,
`6690e4d6d66bc819`, `9a7f68fc7dcac931` (NEISO), `19a9690bb12c8459`, `aed447f88457dff7`,
`cc7d1050a8090c76`, `470338150a2f85a0` (NYISO), `772b1e5abc7fc80c`, `29f8eb372810195f` (CAISO),
`873d8c0e6cab52ae`, `075e6aa30813f061`, `383509581661faba` (ERCOT), `8d8bc63a0d4378a9`,
`587dc5b32ba71ceb` (MISO), `321f04e9060787f0`, `167e65187f32056b`, `09996eca71ee80fd`,
`31a19d815fa319a7` (PJM), and the `ff-t3-neiso-golden` 2026–2050 family.
**D77 re-solves none of them** — that batch is D65-B's, at one HEAD, carrying this fix.

**NOT invalidated:** every **backcast** bundle in every ISO, and every hindcast/crossover horizon
ending before 2028. `apply_ccs_retrofit` returns at its first statement,
`if year < config.ccs_retrofit_available_year`, so no such fleet ever contains a converted unit;
`ccs_capture_fraction` is 0.0 on every generator, and `co2 * (1.0 - 0.0)` is the pre-fix
expression. Asserted with the persisted-identity tests, not by argument (§5). No keeper, sidecar,
determination or dashboard row moves.

## 4. Phase 2 — the screen (rule 29 `[R-SCREEN]`)

**Screen year / leg, named here before it runs:** ONE leg, **NEISO `t1f` 2026–2030**, the year
span in which the mechanism's own measured footprint is largest (8.8 GW of retrofits by 2030 in
the bare arm — the 3 GW/yr ISO cap binding in 2028, 2029 and 2030). Chosen on **footprint**, never
on residual.

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2030 \
  --golden-posture --out-dir results/ff-t1f-d77/neiso
```

**HEAD GUARD:** `H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`.

### 4a. G-DRIFT — the control, audited hunk by hunk (rule 29(b))

**Control: the committed bare NEISO t1f `results/scn-campaign-load-2026-09-06/NEISO/REF/`**, run id
`neiso-2026-2030-scn-campaign-load-2026-09-06-ref`, key `5e2c52ea81694c10`, **solved at
`29b1c757`**. It is the most recent bare-posture NEISO forecast run on `main`. **No control solve
is spent.**

*(WS2b's own BAU shares that key and that base posture but was solved at `0c349d2f`; the two
disagree by 0.48–1.52 Mt CO2/yr — see §4c. The `0c349d2f → 29b1c757` window is NOT audited here
and is NOT the control window; the newer bundle is used precisely because it is on the near side
of it.)*

`git diff 29b1c757 HEAD` over the rule-29 window **plus the forecast lane's own entry chain**
(`scripts/run_full_horizon.py`, `check_forecast_invariants.py`, `golden_forecast_bands.py`,
`configs/`) yields ten changed files. Every hunk classified:

| file | hunk | verdict | reason |
|---|---|---|---|
| `pipeline/solve.py` | same-year P1 basis seed (+151/−38) | **INERT** | gated `_p1_seed = _xwarm and xyear_warmstart is None and env`; the forecast passes an **explicit bool** (`runner.py:3551`, `config.forecast_xyear_warmstart`), so `xyear_warmstart is not None` and `_p1_seed` is **always False** on this path. With it False the changed block reduces statement-for-statement to the original, save one added `model is not None` guard that only converts a would-be `AttributeError` into a skip. |
| `pipeline/solve.py` | `malloc_trim()` call removed | **INERT** | RSS-only: it freed heap the allocator already considered free and could not touch a live object. The single behavioural delta on this path, and it cannot move a number. |
| `utils/heap.py` | file deleted | **INERT** | its only remaining consumer is the line above |
| `model/lp/model.py` | simplex-iteration log line | **INERT** | read **after** `h.run()`; pure timing/diagnostics accounting |
| `config/scenarios.py` | new field `nyiso_ct_peaker_bands_measured` | **INERT** | another ISO's branch (hard-errors outside NYISO, rule 25), default-off, absent from the bare NEISO recipe; registered with frozen default `"False"` so the key is unmoved |
| `pipeline/backcast_config.py` | the NYISO band limb | **INERT** | the **backcast** front end — a `mode="forecast"` run never enters it; and NYISO-only, default-off |
| `config/constants.py` | +1 import name | **INERT** | pure re-export, no value change |
| `scripts/run_calibration.py`, `run_calibration_full.py` | +111 / +55 | **INERT** | backcast CLIs; `run_full_horizon.py` imports neither |
| `scripts/lib/invariant_ledger.py` | new, stdlib-only | **INERT** | registration/audit policy; never on the solve path |
| `scripts/check_forecast_invariants.py` | ledger refactor | **INERT** | post-solve audit; no threshold moved |

**All hunks INERT ⇒ G-CTRL form 4 is VALID and the committed bundle is the control.** Rule 29(b)
earns a control solve only on a LIVE hunk; there is none.

**Corroborated empirically at zero LP cost (§4b gate 5):** the fix can only move a unit carrying
`ccs_capture_fraction > 0`. Every zero-carbon row — nuclear, hydro, wind, solar generation — must
therefore reproduce the control **exactly**. If HEAD drift were live those rows would move too, so
the gate tests the G-DRIFT verdict and the fix's confinement with one comparison.

### 4b. STOP gates — structural, pre-registered, and STOP-only

A gate may **kill** the arm; none may promote it. None is gated on a residual.

| # | gate | pass condition |
|---|---|---|
| 1 | **the identity** | every unit with `fuel_type == "gas_cc_ccs"` has `emission_rate_co2 == measured_host_rate × (1 − 0.90)` **to the digit** (rel. tol 1e-9) against the v2 map for its `(plant_code, "gas")` |
| 2 | **the other three writes** | converted units' `heat_rate == host × 1.12` and `fuel_type == "gas_cc_ccs"` for every unit in the ledger; VOM equals the host's plus the ledger's own `vom_adder_per_mwh` |
| 3 | **confinement** | **no** unit outside the retrofit cohort moves its rate: every non-converted unit with a `(plant_code, class)` row equals the measured map **exactly** |
| 4 | **retrofit MW in band** | 2028/2029/2030 retrofit MW within the D50/D65 band (control: 2975 / 5897 / 8803 MW cumulative, the 3 GW/yr cap binding). **A moved retrofit SET is NOT a STOP** — the carbon adder now differs for converted units, which can legitimately re-order merit; it is reported with its magnitude and cause |
| 5 | **no collateral** | nuclear / hydro / wind / solar generation identical to the control in every year (also the G-DRIFT corroboration, §4a) |
| 6 | **no invariant regression** | no non-target load-bearing forecast invariant flips PASS → FAIL (control carries none) |

**Reported at full magnitude, and gating nothing:** NEISO 2030 CO2 and `gas_cc_ccs` generation
deltas against the control.

### 4c. Declared in advance, so it cannot be written to fit the result

Two bare NEISO bundles at the **same key** `5e2c52ea81694c10`, solved at `0c349d2f` (WS2b BAU) and
`29b1c757` (campaign REF), disagree: CO2 2026–2030 `16.3081/17.7888/16.9614/15.3855/14.8871` vs
`15.83/17.10/15.86/14.02/13.37` Mt (Δ up to **1.52 Mt**), with prices and reserve margins moving
too. The cache key does not identify a solve across code changes. This is **evidence for the §3
hazard, not part of this fix**, and it means WS2b's §5.4 arithmetic must be re-based on the newer
control before it is quoted. Routed, not acted on.

## 5. Byte-identity, asserted not argued

Run and passing **before** the screen: `tests/regression/test_persisted_identity.py`,
`test_fleet_arrays_golden.py`, `test_45u_backcast_inertness.py`, `test_fleet_unification.py`,
`test_fleet_facade.py` (34 passed), plus `tests/unit/model/test_ccs_retrofit.py`,
`tests/unit/data/test_campd_bins.py`, `tests/unit/pipeline/test_runner.py`,
`tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py` (150 passed) and the new seam file
(10 passed).

## 6. Out of scope, explicitly

No re-solve of any other bare key (D65-B's batch); no board byte (`ff-verdicts.json`,
`program-status.json` — D60-R4 / D63); no GOLDEN-3 re-solve; no keeper, marker, shard or freeze;
no dashboard registration. The screen bundle is a rule-29 throwaway and is **deleted before merge**
(rule 29(c)); the FINDING carries every number this session will ever cite.
