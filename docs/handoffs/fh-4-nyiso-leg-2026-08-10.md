# FH-4-NYISO — the NYISO leg of the forward-skill battery (shipped defaults)

**Session.** FH-4-NYISO `[FABLE]`, Wave FH Phase A sibling leg (manager
dispatch, prompt pack `docs/forecast-readiness-prompt-pack-2026-07.md`
§FH-4-NYISO; released by Addendum AI.1). Branch `claude/fh-4-nyiso-leg-iu4l9v`,
off `origin/main` `aa61791e`. **The FH-4 lift is UNCONDITIONAL** (Addendum
AI.1: the AG.2 condition was discharged by the ERCOT leg's step-0 gate PASS at
0.0 %), so this leg carries **no step-0 gate** — the I6 invariant remains as a
**stop-the-line RIDER** on both arms (§1.1). Protocol of record:
`docs/handoffs/fh-4-ercot-leg-2026-08-09.md`, executed for NYISO at **SHIPPED
DEFAULTS** per the dispatch: **no keeper contact, no arming, no tuning.**

**Baseline epoch.** Solved at HEAD `aa61791e` (cold container; `uv sync` +
full `regenerate_clean.py` before any solve). The FFR-9A storage vintage-seed
fix and the FFR-3V renewable vintage-seed fix ride automatically. Two UNGATED
NYISO input repairs also ride in both arms by construction (they are
constants/taxonomy, not flags): the nyiso-132 measured solar CF level
(`RENEWABLE_AVG_CF["NYISO"]["solar"]` = 0.1955, the 2026 Gold Book Table
III-2a identity) and the D-25 gas_st fuel-taxonomy correction. Both are also
embedded in the keeper comparator, so the three-way read is not confounded by
them.

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any solve was launched.
Nothing in §1 changes after. Sections §2+ are filled in order, as produced.
This leg lands NO code change — the Arm K `demand_growth_vintage` wiring
landed at FH-4-ERCOT and is engaged here by the harness arm selection alone.
The one new artifact committed with this prereg is the solve-independent
γ-rider probe `scripts/probes/fh4_nyiso_instrument_date_split.py` (§1.5).*

### 1.1 The I6 rider, as written

**Criterion (the FH-1 §3.3 invariant, applied AS WRITTEN as a rider).** The
I6 over-retirement invariant of `scripts/check_forecast_invariants.py`:
single-year economically-retired capacity as a fraction of prior thermal MW,
cap **0.20** (`Thresholds.econ_retire_frac_cap`), measured per evolution year
from each run's own ledgers, **on BOTH arms**. This is not a gate on the lift
(the lift is unconditional); it is the dispatch's stop-the-line rider:
**FAIL on either arm → the lane STOPS** — that arm's run is registered, the
verdict + numbers are committed, the record goes to the manager, and nothing
further runs. I7 and I12 are reported alongside at full magnitude — they are
the FH-1 signature's other two legs, not the criterion.

**Expectation (to test, never a target).** PASS is expected on both arms: the
committed NYISO capacity-hindcast record (base-2020 plain hindcasts,
`nyiso-2021-2025-realized*` sidecars) shows the model's NYISO exits carried by
the announced/confirmed nuclear channel (Indian Point 3, 1,036 MW model vs
1,012 MW actual) with essentially zero economic-wave content, and the ERCOT
leg's determined-posture probe read I6 PASS at base 2023. Whether that holds
for NYISO at shipped defaults (which, unlike the ERCOT leg, do NOT arm the
unified-lookahead/scarcity-restoration screens) is exactly what the rider
measures, and the criterion is applied as written whatever comes out.

### 1.2 Arm R invocation (declared before solving)

**Shipped-defaults posture, stated.** Unlike the ERCOT leg (which armed
`capacity_screen_unified_lookahead` + `capacity_screen_scarcity_restoration`
BY INVOCATION under the manager's AG.2 arming determination — a determination
scoped to that leg), this leg passes **no arming flags at all**: both screen
fields inherit the shipped default (**OFF**), `retirement_rule` `"pipeline"`
rides the shipped default (D-1), and the capacity-price posture is the
FFR-2E harness default `shipped` — which resolves **NYISO curve-OFF**
(`capacity_market_clearing_by_iso = {PJM, MISO, CAISO, NEISO: True}`, NYISO
deliberately absent, matching production; `scripts/lib/forecast_posture.py`).
NYISO carries **no `ISOConfig.default_scenario_overrides`**, and every
`nyiso_*` keeper-recipe mechanism flag ships `False`
(`nyiso_ordc_measured_step_span`, `nyiso_nyc_rcpf_step_curve`,
`nyiso_seny_rcpf_increment_step`, `nyiso_gas_commitment_bridge`, the zonal
gas-offer anchor and seam-envelope lineage, …), so the arms run **none of the
keeper recipe** — the keeper is the skill COMPARATOR only.

```
uv run python scripts/run_capacity_hindcast.py --iso NYISO \
  --forward-from-base --arm realized --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/nyiso-2023-2025-t1ff-armr-fh4
```

Config cache key **`90c7a76c8e25ee61`**, measured at prereg (gas
`hindcast_realized`, per-solve-year weather, `demand_growth_vintage=null` —
the registered cache-neutral default). Registered ONCE, id
**`nyiso-2023-2025-t1ff-armr-fh4`** (hindcast namespace,
`meta.kind="full_forward"`), regardless of verdict or reads.

### 1.3 Arm K invocation (per protocol §1.3, at this head)

**Arm K posture, resolved at this head** (base 2023): gas
`hindcast_asknown_aeo2023` (nominal 5.48 / 4.34 / 3.80 $/MMBtu vs realized
2.54 / 2.19 / 3.53 — **+116 % / +98 % / +7.6 %**, the ex-ante AEO2023 error
Arm K exists to measure); weather pinned to 2023 for every solve year; demand
growth on the rates **published as of 2023** — the NYISO 2023 Gold Book
(April 2023, Table I-1a Baseline Energy), mid near **0.54 %/yr**, selected by
the arm via the FH-2 §7 / FH-4 `demand_growth_vintage` wiring (vs the live
table's 1.22 %/yr the pre-wiring harness would have leaked). This is the
wiring's **first NYISO-armed solve**; Arm R and every other posture pass the
cache-neutral `None`. Config cache key **`30eedfd2d38e5b92`** at prereg.

```
uv run python scripts/run_capacity_hindcast.py --iso NYISO \
  --forward-from-base --arm asknown --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/nyiso-2023-2025-t1ff-armk-fh4
```

Registered id **`nyiso-2023-2025-t1ff-armk-fh4`**, hindcast namespace,
`meta.kind="full_forward"`, regardless of what the reads show. Runs
sequentially AFTER Arm R (rule 12; one container, years sequential within
each invocation).

### 1.4 The skill reads (the §2.1b metric set), pre-registered

From `scripts/score_crossover.py` run verbatim per arm — no new metric, no
re-derivation: `dispatch_skill.metrics` = **fuelmix, price_mean, price_shape**
(+ `co2` reported) per scored year 2023–2025, each carrying `forecast_err`,
`keeper_backcast_err`, `input_gap = |forecast_err| / |keeper_backcast_err|`.
Keeper comparator: the CURRENT NYISO keeper at this head,
**`2026-08-08-nyiso-132-cf-arm`** (**RE-VERIFIED** in
`frontend/data/backcast/keepers/NYISO.json` at branch time — the dispatch's
"at dispatch" id holds; determination CALIBRATED-WITH-CAVEATS, C3c the lone
ledgered caveat). The scorer reads the keeper's committed `determine()`
records — no solve. The three-way read per metric-year (plan §2.1): keeper
err → Arm R err → Arm K err; the R-vs-keeper spread is the **overlay value**,
the K-vs-R spread the **driver-forecast error**. Both are the program's
deliverable, reported at full magnitude, never targets, never tuned toward.

**Pre-registered directions (to test, never targets):**

* **Arm R price level (`price_mean`)**: UNDERSHOOT (signed negative) expected
  in all three years, with input_gap > 1. The keeper's C3a record is
  +8.8 / +0.8 / −3.4 % and its price level rests on armed conduct/scarcity
  content (zonal gas-offer margin anchor, NYC RCPF, ORDC measured step span,
  SENY increment) plus the backcast's measured delivered-fuel input; the
  shipped forward stack carries none of that, so the bare co-optimized LP
  dual is expected to sit low.
* **Arm R price shape (`price_shape`, monthly NRMSE)**: materially worse than
  the keeper, winter months especially — forward gas is annual Henry Hub plus
  a FLAT NYISO basis adder (`GAS_BASIS_DIFFERENTIAL`), which cannot carry the
  measured winter basis blowouts the backcast's delivered-fuel input carries.
* **Arm K vs Arm R**: price level HIGHER in 2023–2024 (the +116 % / +98 %
  as-known gas vintage), near-converged by 2025 (+7.6 %). **Named in
  advance:** if Arm K's 2023/2024 price errors print SMALLER in magnitude
  than Arm R's, that is the ERCOT leg's error-compensation artifact (a wrong
  driver masking missing conduct content), NOT skill — the reading discipline
  carries over verbatim. Fuel-mix: the expensive as-known gas depresses
  gas-fired energy in 2023–2024 relative to Arm R; NYISO's scoreable classes
  are gas + nuclear + hydro + VRE — there is **no coal** in the window fleet
  (the NY coal fleet exited pre-window), so the ERCOT leg's coal-zero
  headline cannot transfer. Whether an analogous structural zero appears in
  some other class is a read, not a prediction.
* **`co2`** is reported at full magnitude; where the keeper record carries no
  comparable, `input_gap` is null and the forecast error stands alone.
* **Quoting rule.** The lift is unconditional and both arms run the shipped
  posture, so the reads are quotable as T1-FF skill — UNLESS an arm's I6
  rider FAILs, in which case that arm's dispatch numbers are context to the
  stop-the-line report only, and no skill is quoted from it.

### 1.5 The γ rider: instrument-date split of the window's actual exits

**Purpose (AG.2 γ rider, carried by the protocol).** The exit-side skill
number must never be mis-attributed: the T1-FF confirmed-exit channel is
information-gated at `confirmed_registry_as_of = date(vintage, 12-31)` =
**2023-12-31**, so a window exit whose enforceable instrument post-dates the
cutoff is invisible to that channel BY DESIGN.

**Method (solve-independent; committed artifacts only).** The NYISO sibling
probe `scripts/probes/fh4_nyiso_instrument_date_split.py`, committed with
this prereg: the scorer's own target rows
(`data/raw/_validation-source/capacity_actuals_nyiso.csv`,
`kind="retirement"`) matched against the confirmed-exit registry
(`data/raw/confirmed-retirements/nyiso.csv`) on `(plant_id, generator_id)`,
split at the cutoff; reported for the leg's window 2023–2025 AND for
2021–2025 (the scorer's window-unfiltered referent), so the two windows'
numbers are never conflated.

**Registry fact visible at prereg, and the split it forces.** The NYISO
confirmed-exit registry is an **AUDITED ZERO** — zero qualifying rows, with
the audit trail in the file itself (researched 2026-07-05, re-queried
2026-07-31 and 2026-08-03): every NYISO completed deactivation notice in the
candidate set was reversed, withdrawn, or retained on a NYISO reliability
determination (Far Rockaway, Gowanus/Narrows, Pinelawn), and Danskammer is
HELD OUT for want of an unconditional instrument date. The split is therefore
**degenerate by registry content**, and the probe's committed output records
it: instrumented ≤ 2023-12-31 = **0.0 MW**; instrumented after = **0.0 MW**
(unlike ERCOT, where 477 MW acquired a post-cutoff instrument); no-instrument
= **100 %** of the window's actual exits — **578.9 MW** all-fuel / **474.2
MW** thermal in 2023–2025 (oil 328.9, gas_ct 142.9, biomass 60.3, hydro 35.9,
gas_cc 2.4, wind 7.5, storage 1.0), and **1,757.2 MW** all-fuel / **1,647.7
MW** thermal in the scorer's 2021–2025 referent (dominated by Indian Point
3's 1,012 MW April-2021 nuclear exit, which the vintage-2023 fleet basis
predates anyway).

**Attribution, pre-stated.** ZERO MW of the window's actual exits were
knowable-as-confirmed at the vintage cutoff — the confirmed-exit channel can
carry nothing for NYISO by the information gate's own design and the
registry's honest zero. The exit-side rows on these arms therefore measure
the **economic/announced channel only**, and must not be read as the
confirmed-exit mechanism failing; equally they must not be excused — whether
the economic screen should anticipate unconfirmed exits of this kind is the
FFR retirement lane's question, untouched here.

### 1.6 Governance

* Holdout freeze ACTIVE (steady state) — read at launch by the harness and
  recorded in `meta.json`; this leg stays legal under it: solve years
  {2023, 2024, 2025} — training-tier only (2022 auto-bridged, evolved but
  never solved, its data never read); no out-of-training backcast year
  solved/scored/registered; no measured H1-2026 contact anywhere; scoring
  never leaves 2023–2025 (the scorer refuses both bounds).
* Hindcast namespace ONLY — never the backcast registry, never
  `frontend/data/forecast/` committed inputs. No keeper contact, no
  promotion, no shipped-default flip, no matrix cell verdict beyond
  measurement citations. Bar re-levels, signal scaling, tuning toward any
  residual: refused by name.
* ≤5 solve-years per invocation; years sequential within an invocation;
  invocations sequential in this container (rule 12).
* Registration commitment: every solved run registers REGARDLESS of verdict
  or reads. Commit order: prereg → I6 rider verdicts → results → handoff, as
  they exist.
* The other sibling ISO legs and FH-5 are NOT this session's (FH-5 dispatches
  only after the full battery); re-litigating the lift is refused (the
  determination is the manager's record).
* Rule 27: Fable; edits are local on-disk bytes; any push touching a
  ≥300-line file is blob-verified; no new workflows.

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*
