# NYISO — import hour-assignment, the overnight marginal setter, and a nuclear benchmark defect

**Date:** 2026-07-24 · **Keeper under study:** `2026-07-23-nyiso-72-netrev-margin`
(`results/calibration/nyiso72_netrev_margin`, determination NOT-YET, load-bearing
FAILs C3a/C3b/C3c 2023) · **Solves run:** none. Every number below is measured
from the keeper's committed `hourly/` sidecars and from raw source data.

All hourly work is on the repo's non-leap 8760 model clock (Feb 29 dropped —
`scripts/probes/_ercot_lmp_shape_score.py:66` and the `campd.py` convention).
Confirmed lag-0 dominance on model-vs-actual demand before trusting any shape:
demand r = 0.9849 / 0.9830 / 0.9871 and wind r = 0.9935 / 0.9926 / 0.9937 for
2023 / 2024 / 2025 on that clock. (Aligning 2024 naively to the first 8,760
calendar hours instead collapses those to 0.904 / 0.443 — an analysis artifact,
not a model defect. The scorer aligns correctly: `actuals.py:195`.)

---

## 1. Rule-13 adjudication of `interchange_shaping` — **FORBIDDEN as a keeper mechanism**

**Code path.** `scripts/run_calibration.py:2402-2431` gates on
`priced_interchange and config.interchange_shaping`, then calls
`model/interchange/import_nodes.py:746 inject_interchange_shape`, which calls
`data/eia930/envelopes.py:223 measured_interchange_envelope(iso, year, hours,
pct)`. That function reads `_eia_hourly_frame_filled(ba, year)` — the
**same-year** EIA-930 `Total interchange` series **for the ISO itself** — buckets
it by (month × hour-of-day), takes the percentile, and returns
`import_cap[t] / export_cap[t]`. The caller scales every import tranche's
`availability` row by `import_cap / static_tranche_total`
(`import_nodes.py:832-837`).

**Verdict: it pins the model to a measured OUTCOME and has no forward analogue.**

- The series it reads is the ISO's *realized net interchange* — the outcome of
  neighbour dispatch versus NYISO dispatch — not a capability envelope. The
  capability envelope already exists in the model and is a different object: the
  published Simultaneous Import Limit (`EXTERNAL_SIMULTANEOUS_LIMITS["NYISO"]`,
  4,350 MW) and the per-seam interface limits.
- It fails the rule-13 test in the strongest possible way: the function
  **returns `None` for a forecast year, by construction**, and the docstring says
  so — "or the year is not covered (a forecast year), in which case the caller
  leaves the static node unshaped" (`envelopes.py:248-250`). There is no forward
  analogue because the code cannot produce one.
- It does not respond to changed conditions. The cap is a frozen (month, hod)
  table lifted from that year's actuals; change load, gas price or the fleet and
  the cap does not move.
- It caps the very series that is scored. Interchange TWh and interchange hourly
  r are reported metrics; shaping the import node hour-by-hour at the p90 of the
  measured interchange is shaping the scored output.

The docstring's defence — "adds the measured temporal shape without pinning the
flow or introducing any fitted constant" — is true about *fitted constants* and
irrelevant to rule 13. Rule 13 does not forbid fitted constants only; it forbids
a **measured outcome fed back** to force the match. A same-year realized-flow
envelope is exactly that.

Admissible use is diagnostic-only, default-off, never quoted as skill and never
registered as a keeper.

**It is also moot.** §2-3 below show the model already imports *more* overnight
than the real system does, so the flag could not close C3a even as a ceiling
estimate. No probe was spent on it.

---

## 2. What sets the model's overnight price — **domestic thermal, not an import rung**

Measured from `hourly/system_2023.parquet` + `class_hourly_2023.parquet`,
hod 0-6, n = 2,555 h. NYISO ladder rungs and cumulative depths:
HQ_hydro 900 @ $20.78 · IESO_Ontario 1,590 @ $26.36 · PJM_shoulder 2,280 @
$32.24 · PJM_west 2,970 @ $40.13 · eastern_mid 3,660 @ $51.03 · ISONE_tie 4,350
@ $71.46 · import_scarcity 6,385 @ $152.97.

| overnight import-node position | hours | share |
|---|---|---|
| pinned **exactly at** a rung cumulative boundary → import **not** marginal | 1,780 | **69.7 %** |
| strictly interior to a rung → import *could* be marginal | 775 | 30.3 % |

And in the interior hours the price is **not** the rung's cost: the zonal price
equals the partially-loaded rung's MC in only 6.3 % of them, and the median price
sits **$2.23 below** that rung's MC (mean −$7.01) — i.e. the rung is running on
the firm-import floor (`NYISO_FIRM_IMPORT_FLOOR_FRAC`), not on economics.
Per-zone, the overnight price equals *any* rung price in **0.4-0.8 %** of hours.

> **An import rung sets the model's overnight price in roughly 2 % of overnight
> hours. Rung PRICES are not the C3a lever.**

The pinned hours corroborate the merit order rather than contradicting it — at
each boundary the clearing price sits just below the next rung's cost (pinned at
PJM_shoulder → $31.01 vs next rung $40.13; at ISONE_tie, the full economic ladder
loaded → $31.47 vs next rung $152.97).

---

## 3. Is the ladder's duration coupling the C3a mechanism? **No — and the hypothesised direction is refuted**

The premise under test was that the model cannot clear a cheap import overnight
and must run domestic mid-CC instead. The measurement says the opposite.

Measured net external import = the four "SCH -" external seams (HQ / IESO / PJM /
NE) of `data/raw/NYISO/interface-flows/`, the same aggregate
`scripts/data/derive_nyiso_import_tranches.py` derives against.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **measured** import, overnight (0-6) | 2,458 MW | 1,986 MW | 1,895 MW |
| **measured** import, evening peak (16-19) | 3,049 MW | 2,436 MW | 1,613 MW |
| measured overnight/peak ratio | **0.806** | **0.815** | 1.175 |
| **model** overnight / **model** peak ratio | **1.278** | **1.334** | 1.363 |
| model overnight **excess** | **+523 MW** | **+531 MW** | +368 MW |
| model evening-peak **deficit** | **−717 MW** | **−548 MW** | +47 MW |

The real system imports *less* overnight than at evening peak in 2023 and 2024;
the model does the reverse, every year. Adding cheap overnight depth — hypothesis
2 of the charter (HQ depth beyond the 900 MW firm base) — would move the model
*further* from the measurement. **That sub-lane is closed on measured evidence,
not on residual grounds.**

### The coupling is nevertheless defective, on method-correctness grounds

The derivation (`derive_nyiso_import_tranches.py`, docstring) is
`pi_k = Quantile_DA(1 − P[net_import > L_k])` — a Q-Q pairing of the price
duration curve against the import-depth duration curve. That construction
imposes a **rank correlation of ~1.0** between import depth and internal price.
The measured joint correlation is:

    r(net import, DA LBMP)  =  +0.158 (2023) · +0.383 (2024) · +0.432 (2025)

A coupling that assumes rank-1 monotonicity where the measurement shows +0.16 is
wrong about the object it models, independent of any residual — and a
distribution-matching construction carries no hour assignment at all, which is
precisely the signature the keeper shows: interchange annual volume within ~2 %
every year (model 23.92 / 20.73 / 19.44 vs bench 23.45 / 20.35 / 19.09 TWh)
while hourly r sits at 0.474 / 0.488 / 0.395. The ladder's own header comment
already records this failure mode once; the 2026-07-21 re-derivation fixed the
**level** and left the **hour assignment** untouched.

Note the model's overnight/peak ratio is 1.28 / 1.33 / 1.36 — nearly constant —
while the measurement swings 0.81 → 0.81 → 1.18. The model's import shape is
insensitive to the year's actual conditions. That is the hour-blindness, visible
directly.

**Admissible replacement (spec, not yet built).** An hour-conditioned
derivation: couple within diurnal (and seasonal) blocks — e.g. Q-Q *within*
{overnight, morning, midday, evening peak} × season cells — or, better, price the
seam on the neighbour's own hourly conditions so the rung responds to the
neighbour's state rather than to NYISO's price rank. Either regenerates for a
forward year and responds to changed conditions. Under rule 21 the re-derivation
commit cites **method incorrectness** (rank-1 coupling against a measured +0.16
joint; no hour assignment in a distribution-matching construction) — never the
residual.

**Rule 1 warning, stated up front.** Correcting this will *reduce* model
overnight imports, which raises the overnight price, which makes **C3a 2023
worse**. That is not a reason to skip it, and if it is built the result must not
be reverted on the residual.

---

## 4. Is NYISO nuclear missing refuel-outage windows? **No. The benchmark is wrong, not the model**

**Availability series checked:** the keeper's own `class_hourly_<year>.parquet`
nuclear dispatch. It is **not** flat — it carries 6-8 discrete MW levels, a
minimum of 2,461 MW against a 3,326 MW maximum (74 %), and 24.9 % of 2023 hours
below 90 % of maximum. Outage structure is present.

The apparent over-run is an artifact of the benchmark. Scored against **NYISO's
own hourly fuel-mix posting** (`data/raw/NYISO/fuel-mix/`), the model is within
**0.3 % in all three years**:

| 2023 | NYISO posting | EIA-930 `NG: NUC` | model | gap vs posting | gap vs 930 |
|---|---|---|---|---|---|
| nuclear TWh | 27.57 | 24.00 | 27.49 | **−0.08** | +3.49 |
| 2024 | 27.05 | 25.83 | 26.96 | **−0.10** | +1.12 |
| 2025 | 28.48 | 27.90 | 28.38 | **−0.10** | +0.43 |

**Cause.** The NYIS EIA-930 extract codes its `NG: NUC` filing gaps as an exact
`0.0` rather than a blank: **1,275 h in 2023** (56 distinct days, including one
1,179-hour block), 390 h in 2024, 118 h in 2025. A four-unit, ~3.4 GW baseload
fleet cannot be at exactly 0 MW; NYISO's own posting never reads 0 and never
drops below **1,989 MW** in 2023. Those hours are worth 3.46 / 1.12 / 0.37 TWh —
matching the apparent "over-run" to within 0.03 TWh.

The reported hourly-r collapse is the same artifact. Against the authoritative
posting, nuclear r is **0.801 / 0.832 / 0.617**, not 0.831 / 0.498 / 0.505.

**Also checked, same method:**
- **Gas under-run is REAL** — both benchmarks agree: model − NYISO posting
  (Natural Gas + Dual Fuel) = **−5.35 / −4.19 / −1.44 TWh**; model − EIA-930
  = −3.19 / −4.48 / −1.48 TWh. This half of the owner's observation stands.
- **Hydro is a real defect** — +1.20 / +0.96 / **−3.20** TWh vs the posting, with
  hourly r 0.622 / 0.580 / 0.413. Both benchmarks agree. Open.
- **Wind is excellent** — r 0.993 / 0.993 / 0.994, TWh within 0.08.

### Fix applied

`src/market_sim/data/eia930/actuals.py` — new `_ZERO_CODED_GAP_SERIES` registry
(BA code → columns whose exact zeros are filing gaps), applied in
`load_eia_hourly_benchmark` by masking those zeros to NaN so the loader's
existing interpolation bridges them. Repaired totals land within
**−0.4 % / −0.4 % / −0.7 %** of the NYISO posting, from −13.0 % / −4.5 % / −2.0 %
raw. Rule 14: prefer the accurate measurement; the repair is validated against an
independent posting, never against model output.

Registry contains **`NYIS: NG: NUC` only**. Audited every BA/class for the same
pathology; the two other >24 h zero-run cases are **physically real** and are
deliberately *not* registered — ERCO `NG: WAT` (a 0.05-0.24 TWh/yr hydro fleet
that genuinely sits at 0) and ISNE `NG: COL` (ISO-NE coal is all but retired).
Verified after the change: every other ISO's nuclear/hydro/coal benchmark is
byte-identical.

**Blast radius: scoring/reporting only — the LP is untouched.**
`load_eia_hourly_benchmark` feeds `run_calibration_full._eia930_frame_generic`
(the payload benchmark), probes, and derive scripts. It is not on the solve path;
the LP-feeding envelope functions (`measured_interchange_envelope`,
`measured_hydro_hourly_envelope`, `measured_gas_floor_profile`) are separate and
were not modified. No re-solve is required — **a re-score is** (see §6).

Tests: `tests/test_eia930_zero_gap.py` (registered gap bridged; unregistered real
zeros preserved; registry scope pinned). `tests/test_eia_loader.py` 61/61 pass
unchanged.

**Known limit, stated rather than buried:** the 2023 gap includes one contiguous
1,179-hour block. Interpolation recovers its *energy* correctly (−0.4 % vs the
posting) but cannot recover its *shape* — model-vs-repaired hourly r is 0.715 for
2023, against 0.801 vs the posting. Curating the NYISO fuel-mix posting into the
clean seam and filling registered gaps from it (rather than by interpolation)
would fix the shape too; that is a data-intake task and needs owner
authorization.

---

## 5. Where C3a 2023 actually lives — the overnight marginal unit is too inefficient

The 2023 price residual is **not a level miss, it is a trough miss.** Model
load-weighted price minus measured DA LBMP:

| hod | 0-6 | 12 | 16-19 | all |
|---|---|---|---|---|
| model − DA ($/MWh) | **+7.62** | +6.42 | **+1.62** | +5.66 |

The evening peak is calibrated. Worst hours are hod 2-3 at +$9.66 / +$9.58.

At the model's own 2023 NYISO gas price (**$3.09/MMBtu**, `resolve_annual_gas_price`),
the implied marginal heat rate (VOM $2) is:

| | model | actual DA |
|---|---|---|
| evening peak 16-19 | 13.38 | 12.86 — **4 % miss, calibrated** |
| overnight 0-6 | **9.97** | **7.51** — **33 % miss** |

Reality's overnight marginal unit is a ~7.5 HR machine — an efficient CCGT. The
model's is a ~10.0 HR machine. At $3.09 gas the model's $32.82 overnight price
sits in the **steam / high-HR band** ($33.90 at HR 10 + $3 VOM), while the actual
$25.20 sits in the **CCGT band** ($23-25). The model reproduces the *inefficient*
end of the merit order and not the efficient end.

This is consistent with every refuted A/B in the charter: markups, per-plant gas,
zonal basis and the net-revenue margin offer form all shift the *whole* curve,
and the peak is already right — so they could not have worked. It is also
consistent with the nyiso-73 gas-bridge result (fires on 6,492 unit-hours, moves
the trough −$0.20, compresses the spread): flooring a unit online does not help
if the offer *at* that floor is still a high-average-heat-rate tranche price.

**Named next lane (untested, not among the refuted set): the heat-rate basis of
the marginal offer in the low-load regime** — whether a committed CC's
*incremental* heat rate, rather than its tranche *average*, sets the price
overnight. Note this couples to C8: ST_GAS is 31.0 % (2023) / 41.2 % (2024)
forced, grounded-above-budget, and ~658 MW of it runs overnight. A forced unit
that is also price-setting is the thing to check first, via D-2 attribution
(rule 19: reconcile, never stack).

---

## 6. Status and what is NOT done

- **Keeper unchanged.** `frontend/data/backcast/keepers/NYISO.json` still points
  at `nyiso-72`. No solve was run; nothing was registered on the dashboard.
- **A re-score is owed.** The nuclear benchmark for NYISO changed
  (24.00 → 27.46, 25.83 → 26.96, 27.90 → 28.27 TWh). The keeper's committed
  `metrics.json` predates the fix. C1 and C4 should be re-scored from the
  existing bundle — no re-solve needed. This session did not re-score.
- **Lane 1 is not closed** — the cheap-overnight-depth sub-hypothesis is refuted,
  but the hour-conditioned re-derivation (§3) is specified and unbuilt.
- **Lane 2 nuclear is closed** with evidence: no missing refuel outages, the
  benchmark was wrong. **Lane 2 hydro is open** (−3.20 TWh 2025, r 0.41).
- **Lane 3 ST_GAS** was not worked as an intake task this session; §5 gives it a
  new and more specific target than a reliability floor. The pinned floor was not
  touched.
- `reference_price_interface` remains `False` for NYISO. It was not armed. If it
  ever is, NYISO inherits the neighbour's modelled overnight price and the
  overnight trough is an open cross-ISO defect — noted, not armed.
