# PRECOMMIT — ercot-233: the `NE_LOB` binding-hour TIMING Phase-0 — is there ANY admissible zonal-grain driver?

**Session ercot-233, 2026-08-24. Pushed and blob-verified BEFORE any
driver-vs-target statistic is computed** (the card-Y §2 bound). Authorized by
the owner's card-Y signature **(Y-C — hold the lane open)**, executed under
the card RESOLUTIONS: read-only, zero fitted scalars, borderline escalated,
never self-adopted.
**Keeper (untouched):** `2026-08-24-231-tie-zone-measured`
(`results/calibration/ercot231_tiegtc_full`).
**Probe:** `scripts/probes/ercot233_nelob_timing_phase0.py` →
`results/calibration/ercot233_nelob_timing_phase0.json`.

## 0. The question, and what it is not

ercot-232 re-attributed the keeper's G-SPUR residual to **`NE_LOB`
binding-hour TIMING**: the model's NE congestion aggregate is now 79.8 % of
measured with 1,974 congested hours (measured 2,408), but its timing is
~uncorrelated with reality in both keepers (corr −0.059 → −0.042; 1,531
model-only vs 1,965 measured-only hours; under-deep $8.71 vs $25.91 p50 on
the 443 agreeing hours). This Phase-0 asks EXACTLY ONE question: **does any
admissible driver at ZONAL grain predict measured `NE_LOB` binding-hour
incidence materially better than chance?**

- It is NOT a topology change and does not touch the ERCOT-117 / §10 `G`
  adjudication (`internal_congestion_split`): §10 refused sub-zonal *splits*;
  it never measured whether zonal-grain *drivers* time this one
  already-modeled constraint. Stated prior, carried from §10: the real
  binding is sub-zonal (nodal-only 36–47 % of SCED intervals, 138 kV single
  elements 66–83 %), so **the expected outcome is that this closes**.
- It is NOT a 2023-price lever (Q-B/R-A stand; any price relevance would be
  side-effect territory for some future owner-chartered build, which this
  Phase-0 cannot and does not propose).
- A positive result NAMES a driver and **escalates to the owner** — it never
  arms, builds, or proposes a mechanism by itself.

## 1. Target (fixed; copied constructions, no choices left open)

Year **2023 only** (the adjudicated object year; rule 22 satisfied,
2023 ∈ train). Hourly grain, the fixed non-leap calendar.

- **`y(t)`** = 1{measured `NE_LOB` binding in hour `t`} and **`dual(t)`** =
  the hourly-equivalent measured dual — both copied EXACTLY from
  `scripts/probes/ercot232_gspur_phase0.py::_measured_nelob` (NP6-86 archive
  `data/raw/iso-specific-transmission/SCEDBTCNP686_SCEDBTCNP686_2023.parquet`;
  shadow price averaged over ALL SCED intervals in the hour, non-binding
  at 0; binding = binding-interval share > 0). Expected: 2,408 binding hours,
  annual dual ≈ $69,932 — a mismatch against the ercot-232 record STOPS the
  probe.
- **Active-hour mask** `A(t)` = hours with an `NE_LOB` row in the curated
  clean partition `data/clean/gtc-limits/ERCOT/gtc-limits_2023.parquet`
  (`scripts/data/curate_gtc_limits.py`, run this session: 13,452 rows /
  17 GTCs — the recorded values). Expected ≈ 3,640 hours. **Binding ⊂ active
  by construction**, so activeness itself is a trivial in-sample separator
  and is NEVER scored as a driver; it only scopes d1.

## 2. Drivers (fixed list; every constant cited; ZERO fitted scalars)

All series are model inputs or their direct measured sources — each is
forward-reproducible in class (rule 13) and already lives in the model's
input vocabulary. Directions are pre-signed from the physics (binding =
export-limit congestion of a generation-long lobe).

| id | driver | construction | hours scored | pre-signed direction |
|---|---|---|---|---|
| **d1** | the measured limit's own level | `limit_mean_mw` of the `NE_LOB` rows in the clean partition | active hours `A` only (the activeness confound is excluded, not exploited) | LOWER limit → binding likelier (−) |
| **d2** | NE-lobe CAMPD-available thermal capacity | Σ over the model's OWN Northeast-zone thermal plants (`build_zone_lookup("ERCOT")` over `master-plant-registry.csv`, `plant_group` ∈ {COAL, CC_REGULAR, CT_PEAKER, CC_CHP, CT_CHP, ST_GAS}) of registry nameplate × (1 − outaged unit fraction from `data/raw/campd-unit-outages.csv` windows via `outages.unit_outage_event_window`) | all 8,760 | MORE available → more export pressure → binding likelier (+) |
| **d3** | zonal export-pressure margin | d2 + d4 − NE zone demand (the keeper's own committed P1 `system_2023.parquet` Northeast `demand`) | all 8,760 | HIGHER → binding likelier (+) |
| **d4** | placed DC-tie import into the lobe | −(SWPP net interchange, `data/raw/eia-930-interchange/ERCO interchange hourly.parquet`, hour-ending window slice per `eia930.demand.ercot_tie_zone_interchange`) × 600/820 (`constants.ERCOT_DC_TIE_ZONE_MAP`, registered) | all 8,760 | MORE import into the lobe → binding likelier (+) |

**Pre-registered limitation of d2/d3, stated before measurement:** the
NE-zone renewable output (~0.3–1.5 GW of 2023-operating solar) is NOT
reconstructable at zonal grain from committed artifacts without replaying
the data pipeline, so d3 omits it. The omission biases d3 *against* daytime
export pressure. Consequence rule: if d3 lands within the at-bar tolerance
(§3) of ANY bar from below, the omission is escalated with it rather than
letting the truncated driver adjudicate closure.

**Context block (reported, never scored as a driver):** the model's own
binding indicator (link dual `price(North) − price(Northeast) > $1`, the
ercot-232 construction) vs `y` — sensitivity, specificity, and its implied
AUC = (sens+spec)/2 — restating the ercot-232 agreement record as the
baseline the drivers are compared against narratively.

## 3. Metrics and verdict bars (fixed BEFORE measurement)

Per driver, over its scored hours:

1. **AUC** (Mann-Whitney rank statistic) of the pre-signed driver for `y`.
   Ties mid-ranked. Reported raw AND pre-signed; the bars read the
   pre-signed value.
2. **Spearman rank correlation** with `dual` (magnitude channel).
3. **Top-decile lift**: binding rate in the pre-signed driver's top decile ÷
   the scored-hours base rate.

Bars (family = the four drivers; the object needs ONE driver to survive):

- **NAMED** (escalate to the owner as a live identification): AUC ≥ **0.70**
  AND top-decile lift ≥ **1.5**.
- **BORDERLINE** (escalate as borderline, never self-adopt): **0.65** ≤ AUC
  < 0.70.
- **CLOSES** (that driver): AUC < 0.65.
- **At-bar tolerance:** an AUC within **±0.02** of a bar is treated as AT
  the bar and escalated rather than self-classified.
- **Object verdict:** the timing object **CLOSES AT ZONAL GRAIN** iff every
  driver CLOSES clear of tolerance; otherwise the surviving drivers are
  escalated to the owner with the numbers, and NOTHING is armed or built in
  this session either way.

## 4. Fences

No LP, no solve, no `ScenarioConfig` field (rule 28(c) not engaged), no
mechanism built or armed, no run registered, keeper untouched. Years {2023}
only. ERCOT-only artifacts (rule 25). Zero fitted scalars: every constant in
§2–§3 is either a registered model constant (600/820), a fixed convention
(deciles, $1 dual threshold from ercot-232, the ±0.02 tolerance), or a bar
fixed in this document before any measurement. The probe JSON is committed
whatever it shows; a verdict contradicting the stated prior is recorded, not
smoothed. The DO-NOT-REDO list is untouched: no `R`/`I`/`G` cell is
re-tested — this measures a named-unmeasured object (card Y §2), and its
closure re-affirms rather than re-opens ERCOT-117/§10.
