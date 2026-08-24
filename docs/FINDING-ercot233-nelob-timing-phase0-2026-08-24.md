# FINDING — ercot-233: the `NE_LOB` binding-hour TIMING object **CLOSES AT ZONAL GRAIN** — no admissible zonal-grain driver reaches the precommit bars, and the two capability-side drivers run BACKWARDS

**Date:** 2026-08-24 · **ISO:** ERCOT · **Keeper (untouched):**
`2026-08-24-231-tie-zone-measured` (`results/calibration/ercot231_tiegtc_full`)
· **Authorization:** card Y signed **(Y-C — hold the lane open)**, RESOLUTIONS
item (`docs/DECISION-CARD-ercot233-2023-object-closure-2026-08-24.md`)
· **Charter:** `docs/PRECOMMIT-ercot233-nelob-timing-phase0-2026-08-24.md`,
pushed + blob-verified (blob `b09116f`) BEFORE any measurement
· **Probe:** `scripts/probes/ercot233_nelob_timing_phase0.py` →
`results/calibration/ercot233_nelob_timing_phase0.json`

**NO SOLVE, NO LP, NO MECHANISM BUILT, NO `ScenarioConfig` FIELD (28(c) not
engaged), NO RUN REGISTERED, KEEPER UNCHANGED, ZERO FITTED SCALARS.** Every
bar, driver, direction and tolerance was fixed in the pushed precommit; the
target constructions are imported verbatim from the ercot-232 probe and the
probe STOPs on any mismatch against the adjudicated record (it reproduced
exactly: 2,408 measured binding hours, annual dual $69,932, 3,640 active
hours).

---

## 1. The question

ercot-232 re-attributed the keeper's G-SPUR residual to `NE_LOB` binding-hour
TIMING (corr −0.042 model-vs-measured dual; 1,531 model-only vs 1,965
measured-only binding hours; under-deep $8.71 vs $25.91 p50 on the 443
agreeing hours) and named it WITHOUT adjudicating it. Card Y §2 posed the
narrow Phase-0 question §10/ERCOT-117 never measured: **does any admissible
driver at ZONAL grain predict measured `NE_LOB` binding-hour incidence
materially better than chance?** Stated prior: it closes (the §10 record has
the real binding sub-zonal — nodal-only in 36–47 % of SCED intervals, 138 kV
single elements binding 66–83 %).

## 2. The measurement

Four precommitted drivers, each a model input or its direct measured source
(rule 13-admissible in class), scored for hourly binding incidence
(base rate 27.5 %; within active hours 66.2 %) against bars NAMED ≥ 0.70 AUC
(with ≥ 1.5 top-decile lift), BORDERLINE ≥ 0.65, at-bar tolerance ±0.02:

| driver | hours | AUC (pre-signed) | top-decile lift | Spearman vs dual | verdict |
|---|---|---|---|---|---|
| d1 measured limit level (active hours) | 3,640 | **0.551** | 1.14 | 0.222 | **CLOSES** |
| d2 lobe CAMPD-available thermal MW | 8,760 | **0.436** | 0.85 | −0.105 | **CLOSES** |
| d3 export-pressure margin (d2 + d4 − NE demand) | 8,754 | **0.415** | 0.42 | −0.128 | **CLOSES** |
| d4 placed SWPP tie import into the lobe | 8,754 | **0.496** | 0.95 | −0.001 | **CLOSES** |

Context (reported, never scored): the model's own binding indicator carries
sensitivity 0.184 / specificity 0.759 — implied AUC **0.4715**, below chance,
restating the ercot-232 mistiming on this probe's own constructions.

Three observations the numbers force, all recorded at full magnitude:

1. **Every driver closes CLEAR of tolerance** — the best (d1, 0.551) sits
   0.079 below even the tolerance-widened borderline edge (0.63). The at-bar
   escape never fires, and the pre-registered d3 renewables-omission
   consequence rule never fires (d3 is 0.215 below the borderline bar; no
   ≤1.5 GW daytime solar term could plausibly move an AUC +0.24).
2. **The capability-side story is not merely weak — it is BACKWARDS.** d2 and
   d3 land BELOW 0.5: hours with MORE lobe capability available (and more
   zonal export headroom) see LESS measured binding. That is what the §10
   record predicts if binding is set by sub-zonal element conditions
   (138 kV line outages/ratings) that co-move with the same maintenance
   seasons that take lobe plants offline — the zonal export-pressure physics
   simply does not operate at this grain.
3. **The tie placement carries zero timing information.** d4's Spearman with
   the measured dual is **−0.0006** and its AUC 0.496 — a coin flip. This
   sharpens ercot-232's verdict: the placement moved the congestion object
   toward measured on every AGGREGATE while contributing nothing to TIMING,
   because timing is not carried by any input the placement touches.

## 3. Verdict

**The `NE_LOB` binding-hour TIMING object CLOSES AT ZONAL GRAIN, on
measurement** — the card-Y §2 stated prior is confirmed rather than assumed.
The object joins the §10/ERCOT-117 adjudication as its measured completion:
sub-zonal topology splits were already refused (`internal_congestion_split`
= `G`, whose link TTC would have to be invented against the residual), and
now the zonal-grain driver route is measured empty as well. **DO-NOT-REDO**
without genuinely sub-zonal admissible data (e.g. published element-level
outage/rating schedules crosswalked to the lobe boundary — none is in the
committed corpus).

**Consequence for the lane.** The owner's Y-C holds the lane OPEN, and this
Phase-0 was its one named-unmeasured object. With it measured closed, the
ERCOT 2023 admissible queue is EMPTY again — the lane now works only new
evidence or waits on Door D (2026 SOM RTC+B-era anchors, ~mid-2027, card W).
Per the card RESOLUTIONS, Y-C manufactures no admissibility: nothing here
re-opens Q-B/R-A or any `R`/`I`/`G` cell.

**Keeper: UNCHANGED.** Nothing armed, nothing built, nothing registered.

## 4. Hygiene

Read-only measurement off committed artifacts + `data/raw`; the gtc-limits
clean partition regenerated with `scripts/data/curate_gtc_limits.py` (2023:
13,452 rows / 17 GTCs — the recorded values). Years {2023} only (rule 22);
ERCOT-only artifacts (rule 25); no matrix cell edit (rule 28(b) — no
mechanism tested; the closure re-affirms the existing `G`); no CI job, no
workflow; probe JSON committed whatever it showed, alongside the ercot-231/232
records. Precommit blob-verified before measurement per rule 27.
