# PRE-REGISTRATION — caiso-154: is the caiso-153 OLS-attenuation failure mode LIVE in the PJM and NEISO measured offer surfaces?

Committed and pushed **before any estimator value on this session's corpus
exists**. House rule; caiso-139/146/147/148/151/152/153 precedent.

Lane: the NEW cross-ISO lead from `FINDING-caiso153` §H — "the *failure mode* —
a per-resource daily fuel regression whose slope is levered on one gas spike —
is generic to any ISO whose offer surface is identified the same way, and the
PJM/NEISO derives use the same family. **Not tested here and not claimed**;
flagged for their lanes." This session adjudicates that flag.

**This is NOT a re-test of any adjudicated mechanism cell** (rule 28a duty,
stated explicitly). `measured_offer_surface` PJM is `R` (the dispersion lever
family, pjm-126/127/132; the D-BIN resolution bound, pjm-141) and NEISO is `I`
(Limb B dormant, neiso-58). Those verdicts adjudicated the mechanism *as a
lever*; this session audits an **estimator defect in each ISO's own derive
script** — an input-standing question, the caiso-152/153 class. No cell verdict
letter is proposed to change; evidence/notes are appended per the caiso-152
precedent ("the INPUT's standing changed, the mechanism did not"). Rule 25
`[R-ISO-SCOPE]`: no verdict, parameter, or threshold transfers across ISOs;
each ISO is measured on its own corpus and its own fuel series. Both target
ISOs' §5 lever queues were read (matrix §5.3, §5.6); this session is
**off-queue by design** — it is the chartered cross-ISO audit from
FINDING-caiso153 §H, not a price lever from either queue.

Keepers at entry: CAISO `2026-07-31-caiso153-reid-b` (CALIBRATED-WITH-CAVEATS,
0 FAILs); PJM `2026-07-31-pjm-143b-hy-level` (CALIBRATED); NEISO
`2026-07-31-neiso-72-hy-window`.

**Rule-22 marker state, re-verified this session** (correcting the handoff
prompt, which said no ISO in scope holds a marker): PJM holds `complete`
(validation tier, declared 2026-07-31) and NEISO holds `complete` (declared
2026-07-07); CAISO holds none; **no ISO holds `final`**; and the **holdout
spend freeze (`holdout-freeze.json`) is ACTIVE**, which outranks both blocks —
no out-of-training year may be solved for any ISO. This session plans **no LP
solve at all**; if one becomes licensed by §5's rules it is 2023–2025 only.
**No marker is written for any ISO.**

---

## §1 — the question, made precise

The caiso-153 defect, exactly: `derive_caiso_offer_surface.py::_classify`
regresses each masked resource's **daily body bid** on the **daily CA-composite
citygate** series, reads the pooled-OLS **slope as the resource's marginal heat
rate**, gates admission on `r ≥ 0.6` / `slope ∈ [4, 18]` / `≥ 120 days`, and
splits classes at `hr_cut = 8.5`. When the regressor's variance is dominated by
a short extreme tail (Jan-2023 citygate $24.29/MMBtu vs a 2023–25 median near
$3–4), the pooled-OLS slope is levered on those few days and **attenuates
toward zero for any resource that did not track the spike proportionally, with
correlation intact** — so the r gate cannot catch it. In CAISO this put
16,329 MW at a marginal heat rate below 4 MMBtu/MWh and collapsed the CT bucket
to G1 0.235.

"LIVE in ISO X" therefore requires ALL of:

* **L1 (structural)** — ISO X's shipped derive consumes a per-resource
  fuel-regression slope (or any estimator in that family) into a consumed
  artifact value;
* **L2 (precondition)** — ISO X's fuel regressor exhibits the extreme-tail
  variance domination;
* **L3 (materiality)** — neutralizing the tail leverage (robust estimator or
  tail exclusion) moves a consumed artifact value beyond that artifact's own
  tolerance.

## §2 — L0 disclosure: the code-inspection facts, found BEFORE this document and disclosed here

Read before any corpus existed on disk this session (the corpora are gitignored
and the container is fresh; both refetches were started before this document
was finished, and no derived value from either has been computed):

| derive | consumed artifact | armed in current keeper? | estimator |
|---|---|---|---|
| `derive_caiso_offer_surface.py` | `caiso_offer_curve_measured.json` + `caiso_offer_surface_condbinned.json` | CAISO: YES | per-resource daily **OLS regression** slope → classifier + hr_cut buckets (the caiso-153 family; Theil–Sen since caiso-153) |
| `derive_pjm_offer_surface.py` | `pjm_offer_surface_condbinned.json` | PJM: **NO** (`pjm_offer_surface_conditional = False` in `pjm143_hy_level_B/run_config.json`) | per-unit **median of daily ratio** `(top_of_curve / fuel_day) / base_HR`; segments by unit PHYSICS (`min_runtime`, ecomin/ecomax), no regression, no slope, no r gate |
| `derive_pjm_offer_midcurve.py` | `pjm_offer_midcurve_condbinned.json` | PJM: **YES** (`pjm_offer_midcurve_conditional = True`, segments `['LONG_RUN','CC_LIKE']`) | capacity-weighted **median of daily ratio** `price/gas_day` at fixed within-unit shares; physics segments imported from the top-of-curve derive; no regression |
| `derive_neiso_offer_surface.py` | `neiso_offer_surface_condbinned.json` | NEISO: **NO** (`neiso_offer_surface_conditional = False` in `neiso72_hy_window_B/run_config.json`) | per-asset **median of daily ratio** `(top_of_curve / fuel_day) / base_HR`; fast-start segment by physics (`Claim30 ≥ 0.9 × EcoMax`); no regression |

A precise-pattern grep (`polyfit|linregress|lstsq|theilslopes|siegelslopes`)
over `scripts/data/` confirms `derive_caiso_offer_surface.py` is the **only**
offer-surface derive containing a regression estimator.

**Consequence, registered ex ante:** **L1 is FALSE for both PJM and NEISO** —
no shipped PJM/NEISO offer-surface artifact consumes any regression slope, so
the caiso-153 estimator defect **cannot be live** in them in the strict sense,
and FINDING-caiso153 §H's premise ("the PJM/NEISO derives use the same family")
is **imprecise**: the shared family element is the *daily-fuel normalization*,
not the estimator. The primary structural verdict is therefore **NOT LIVE, for
both ISOs**, decidable from code alone. The corpus measurements below remain
the substance of the session: they adjudicate (i) the §H transfer question as a
*data* question — had the CAISO identification been used here, would it have
failed the same way; (ii) the genuine analogue exposure of the estimator these
derives DO use — a median-of-ratio has its own conceivable tail-leverage mode
(a fuel spike divides down that day's ratio; if spike days concentrate inside
one net-load bin, that bin's median attenuates); and (iii) the caiso-152-class
reproducibility of both ISOs' committed artifacts, which has never been checked
for PJM/NEISO.

## §3 — corpus (frozen)

* **PJM**: the full 36-month 2023–2025 DataMiner2 `energy_market_offers`
  corpus, exactly what `scripts/data/fetch_pjm_energy_offers.py` produces with
  no arguments (per-month coverage reported; the committed artifact records
  36/36 months).
* **NEISO**: every published `hbdayaheadenergyoffer` day in 2023–2025, exactly
  what `scripts/data/fetch_neiso_da_energy_offers.py --years 2023 2024 2025`
  produces (the endpoint's documented unpublished-day gaps mean coverage lands
  near the committed artifact's 1,058/1,096 days; achieved coverage is
  reported, and the derive's own 9 critical tail-event days must be present or
  the measurement halts there).
* **NO seasonally balanced subsample anywhere** (DO-NOT-REDO: caiso-152 §D
  measured that it starves a per-resource daily estimator; caiso-150 §B
  governs only the intertie climatology — different estimator, different
  corpus requirement).
* Fuel regressors are the **exact series the shipped derives divide by**:
  PJM — Henry Hub daily spot (`data.fuel.HENRY_HUB_DAILY_PATH`),
  forward-filled, + `GAS_BASIS_DIFFERENTIAL['PJM']`; NEISO — Algonquin
  Citygate daily (`data.fuel.ALGONQUIN_DAILY_PATH`), forward-filled. Both are
  committed inputs, byte-fixed before this session.

## §4 — measurements (frozen)

Instrument: `scripts/probes/_caiso154_ols_attenuation_xiso.py`, which
**imports and reuses** the caiso-153 harness core —
`scripts.probes._caiso153_offer_classifier_reid._fit` (OLS/TS/TRIM) and
`_score_resources` (slope / r / level-adder / alternating-gas-rank split-half),
plus the family constants from `derive_caiso_offer_surface`
(`MIN_CAP_MW = 20`, `GAS_MIN_DAYS = 120`, `GAS_MIN_R = 0.6`,
`GAS_SLOPE_RANGE = [4, 18]`, `TRIM_Q = 0.95`, `LEVEL_ADDER_MAX = $20`,
`hr_cut = 8.5`) — parameterized by ISO (per-ISO corpus adapters producing the
same `(resource, day, p_body)` frame), **not forked**.

**M1 — regressor tail leverage** (the L2 precondition), per ISO fuel series
over 2023–2025 flow days: max/median ratio; the top-1%-of-days share of the
regressor's variance about its mean. CAISO reference (recorded, not
recomputed): $24.29 max vs ~$3–4 median.

**M2 — the counterfactual classifier grid** (the §H transfer question).
4 body probes × 3 estimators per ISO: `P035` / `BAND` (cap-weighted mean over
[0.35, 0.85]×cap) / `P060` — the caiso-153 axis — **plus `TOP`** (highest-priced
step: the statistic these ISOs' shipped derives actually consume), × `OLS` /
`TS` / `TRIM`. Population: every corpus resource with cap ≥ 20 MW (cap = the
shipped derives' own convention: PJM per-unit median `avg_ecomax`, NEISO
per-asset median `EcoMax`). Basis for the implied non-fuel adder `L`: **gas
only** (declared: PJM/NEISO carbon (RGGI) is a partial-footprint $0–6/MWh that
a masked/unit-code corpus cannot assign per-unit; it lands inside `L`
identically for every estimator, so the OLS-vs-robust CONTRAST — the object of
interest — is unaffected; each cell's absolute `|L|` vs the $20 bar is reported
with this caveat attached). Per-cell outputs, all descriptive: cap-weighted
median `|L|`; admissibility vs $20; slope p25/p50/p75; split-half instability;
the `r ≥ 0.6 & slope < 4` count/MW; bucket MW at the 8.5 cut; and the
cap-weighted confusion of slope-bucket vs the shipped physics segmentation.
**No winner is selected, no selection rule exists here, and NOTHING is derived
from this grid** — the caiso-153 grid fed a re-derivation; this one cannot,
because no shipped PJM/NEISO code consumes a slope.

**M3 — shipped-estimator tail sensitivity** (the analogue liveness test, and
the only measurement that can override the structural NOT-LIVE). Re-run the
shipped ladder construction (the derive modules' own functions, outputs
redirected — consumed artifacts under `data/raw/_validation-source/` are
NEVER rewritten) on the corpus with the top-1%-of-2023–25-fuel-price flow days
excluded, for all three artifacts (PJM top-of-curve; PJM midcurve within-year
vintage — the ARMED one; NEISO top-of-curve). **Verdict rule, fixed ex ante:
any consumed rung/band/`peak_p50` value moving by more than 10 % of its
committed value ⇒ TAIL-SENSITIVE** — a NEW named defect (not "caiso-153 live"),
FILE AND STOP: no estimator change, no derive edit, no re-derivation this
session (these derives have no frozen re-identification gates; inventing one
mid-session is what caiso-153 existed to avoid). ≤ 10 % everywhere ⇒ ROBUST,
quantified.

**M4 — reproducibility** (the caiso-152-class protective check, never run for
PJM/NEISO). Run each shipped deriver's own `main()` on the refetched corpus
with outputs redirected and the fleet basis **INJECTED from the committed
artifact's own provenance block** (PJM: `base_hr` 6.372/11.697, resolved peaks
5.0/4.0, class MW — the recorded `pjm98_cc_mustrun` bundle is NOT on disk in
this container, so the fleet-replay leg is BLOCKED and reported as such, and
what is tested is corpus + parser + estimator + ladder; NEISO: `base_hr` 9.791
— `neiso_fleet_binned.parquet` is likewise absent; PJM midcurve: needs no
fleet basis at all). Comparison against the committed JSONs, thresholds fixed
ex ante: identical after the derive's own rounding ⇒ REPRODUCED; any consumed
value |Δ| ≤ 2 % ⇒ reproduced-within-noise; **any consumed value |Δ| > 10 %
with day/month coverage matching the committed provenance ⇒ caiso-152-class
NOT REPRODUCIBLE** — file and stop, same handling as M3. NEISO deltas with
materially different day coverage (the endpoint republishes/withdraws days)
are attributed and reported, not verdict-flipped, unless they exceed 10 % with
coverage within ±5 files of the recorded 1,058.

## §5 — decision rule (frozen)

Per ISO: **LIVE requires L1 ∧ L2 ∧ L3.** L1 is FALSE for both ISOs (§2), so
the registered primary verdict is **NOT LIVE — structurally absent** for BOTH,
with M1/M2 quantifying the counterfactual ("would the family have failed here")
and M3/M4 the analogue and reproducibility exposures. If M3 or M4 trips, the
outcome is a NEW named finding for that ISO's lane (its own charter, its own
future prereg if it leads to a re-derivation) and this session **stops at the
filing** — the caiso-152 §"lane STOPS at the derive" pattern. No branch of this
prereg re-derives, rewrites, or re-arms anything.

**No LP solve is planned on any branch.** The handoff's step-2 A/B clause
("IF live … A/B that ISO's keeper") cannot fire: L1 is false, so no corrected
input exists to arm; and neither the PJM top-of-curve nor the NEISO surface is
armed in its keeper in any case, so no artifact this session could correct is
in any keeper's consumption set except the PJM midcurve, whose M3/M4 failure
modes are file-and-stop by the rules above. Consequently **nothing is
registered on any dashboard** (the caiso-136/143/144/149/150/152 no-solve
pattern).

## §6 — expected directions (signs only; no quantitative bands registered)

* M1: NEISO's Algonquin series has a **large** winter tail (expected
  max/median ≥ ~8×) — the L2 precondition likely PRESENT; PJM's HH+basis tail
  is **moderate** (expected ~3–6×).
* M2: where M1 finds leverage, OLS `|L|` exceeds TS/TRIM `|L|`, and the
  `r ≥ 0.6 & slope < 4` population is nonzero under OLS and shrinks under TS
  (the caiso-153 signature, transplanted). NEISO's fast-start fleet is heavily
  oil/dual-fuel, so a LARGE non-gas-classified population is expected under
  every estimator — that is the r/slope gates working, not the defect.
* M3: the shipped medians are expected ROBUST (a per-unit within-bin median is
  levered by the bin's median-fuel day, not its extreme day) — rung moves
  ≪ 10 %.
* M4: PJM expected REPRODUCED (stable monthly API, 36/36 months); NEISO
  expected reproduced up to day-coverage drift.

**REJECT conditions, binding on every branch:**

1. No derive script under `scripts/data/` is modified; no artifact under
   `data/raw/_validation-source/` is rewritten; no `ScenarioConfig` field, no
   gate, no threshold moves anywhere.
2. The M3/M4 tolerances above are fixed HERE and may not be re-chosen after
   values exist. Any mid-session change to a registered input (corpus, grid
   member, probe definition, tolerance) is registered in a **dated addendum
   before any value under it exists**.
3. No M2 cell is quoted as measured PJM/NEISO conduct in absolute terms —
   only contrasts (OLS vs robust; slope-bucket vs physics) and gate
   populations are results (the caiso-153 §G "no OLS absolute levels"
   discipline, extended).
4. Nothing here re-tests the adjudicated PJM `R` (pjm-126/127/132/141) or
   NEISO `I` (neiso-58) mechanism verdicts; no re-binning of PJM's net-load
   edges (pjm-141 D-BIN, rule-23-barred); no CAISO value is recomputed and no
   CAISO artifact is touched (caiso-153 §G stands in full).
5. The probe writes only under `results/calibration/caiso154_*` and the
   session scratchpad.

## §7 — deliverables

* `FINDING-caiso154-*.md` on every branch, with its own DO-NOT-REDO section.
* Rule 28b: `measured_offer_surface` **evidence/note updates for the P and Q
  columns in this session** (cells stay `R` / `I` — input-standing evidence,
  the caiso-152 precedent), and the CAISO column's §H flag recorded as
  adjudicated.
* `docs/calibration-log/caiso.md` gains the caiso-154 entry (primary lane);
  `docs/calibration-log/pjm.md` and `docs/calibration-log/neiso.md` gain
  cross-reference entries (their input standings are what was measured).
* No dashboard registration (no solve). No rule-22 marker for any ISO.
* `ruff format --check` clean on all new files.
