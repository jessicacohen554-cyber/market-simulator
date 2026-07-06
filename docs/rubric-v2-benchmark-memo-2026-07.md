# Rubric v2 Benchmark Memo — commercial-grade anchors for the calibration determination

**Date:** 2026-07-06. **Session:** `claude/rubric-recalibration-fitness-vu7i24` (owner-authorized rubric recalibration).
**Deliverable of:** the RUBRIC RECALIBRATION directive — re-anchor the backcast
test to fitness-for-purpose and commercial-model benchmarks.
**Companions:** `docs/calibration-determination-rubric.md` (v2, canonical),
`scripts/calibration_verdict.py` (the scorer), the Calibration Status dashboard
page (renders §4's comparison table next to live keeper scores).

**Hard constraints honored (unchanged by this memo):** the anti-self-deception
protections — no measured-outcome feedback (rule 13), keep-accurate-data
(rule 14), holdout quarantine (rule 22) — plus rule 20 (forced-energy budget),
the D-9/D-6/E9 gates, and the keeper = most-structurally-faithful principle
(rule 1). No solves were run, no keeper swapped, no holdout year touched.

---

## 1. Why re-anchor

Rubric v1's tolerances were internally reasoned but externally unanchored: the
2026-07-02 re-balance tightened C3a to ±5%, C3b to 0.15, C3c to [0.7×, 1.5×]
and cut the soft-caveat budget 3→2 with no published reference point, and the
gap register (§4) records the consequence — all six keepers `NOT-YET`, with
NYISO/NEISO blocked *purely by caveat arithmetic* while carrying zero FAILs.
A test that no demonstrated commercial model could pass is not evidence of
rigor; a test that hides real misses is not evidence of skill. v2 sets every
band against the best published external comparable, in both directions.

## 2. What commercial and public models actually publish

Two independent web surveys (2026-07-06, this session). Headline **negative
finding first**: commercial vendors (Energy Exemplar PLEXOS/AURORA, Hitachi
PROMOD, GE MAPS, Anchor EnCompass, ICF IPM, Aurora Energy Research) publish
**no systematic backcast accuracy statistics** — Energy Exemplar sells
"pre-configured backcast year" datasets with the numbers behind the license
wall; EnCompass's public validation claim is regulatory adoption in 17 states.
The quantitative record lives in regulator-commissioned backcasts, ISO planning
benchmarks, market-monitor re-simulations, EIA's AEO Retrospective, and
academic hindcasts:

| # | Source | Model / market | Metric | Published value | Grade |
|---|---|---|---|---|---|
| 1 | SEM Committee (Ireland), NERA, [SEM-25-010](https://www.semcommittee.com/files/semcommittee/2025-03/SEM-25-010%20SEM%20PLEXOS%20Model%20Validation%202024-2032%20Backcast%20Report.pdf) (2025) | PLEXOS, I-SEM DAM | 4-yr mean price error, backcast 2020–23 (actual inputs) | **+0.1%** (+€0.09/MWh); winter peak +2.5%, off-peak −2.0%; regime sub-periods ±1–3% | strong |
| 2 | SEM Committee, ECA, [SEM-20-004](https://www.semcommittee.com/files/semcommittee/media-files/SEM-20-004%20SEM%20PLEXOS%20Validation%20(2019-2025)%20and%20Backcast%20Report.pdf) (2020) | PLEXOS, I-SEM | 1-yr mean price error; **the stated regulator criterion** | −5.8% raw / −2.1% excl. ~50–100 h/mo of scarcity events; criterion: **"±5% is an appropriate fit… against 3–5 years of real market data"**, monthly within ±10% | strong |
| 3 | SEM Committee, NERA, [SEM-21-086](https://www.semcommittee.com/files/semcommittee/media-files/SEM-21-086%20SEM%20PLEXOS%20Model%20(2021-2029)%20Input%20Validation%20and%20Backcast%20Report.pdf) (2021) | PLEXOS, I-SEM | Oct 2018–Apr 2021 backcast | +0.6% (metered-demand) / −3.1% (DAM-demand); **winter peak −9.0%, off-peak +11.3%** — regulator-accepted shape bias; recommends *against* tuning offers beyond cost | strong |
| 4 | NYISO 2023-2042 Outlook, [Appendix A PCM Benchmark](https://www.nyiso.com/documents/20142/46037616/Appendix-A%20-Production-Cost-Model-Benchmark.pdf/75c63a06-86e1-a160-7895-361cc5d7a00e) | GE MAPS, NYISO (2021) | Zonal annual LBMP, energy, congestion | LBMP **−2% to −17.4%** by zone (NYC −10.5%), systematic under-prediction, **accepted as the Outlook basis**; NYCA energy −0.03%; zonal energy ~0–4% (LI −14%); congestion $ −13.5%; residual closed with **tuned hurdle rates** | strong |
| 5 | CAISO DMM annual reports ([2024](https://www.caiso.com/documents/2024-annual-report-on-market-issues-and-performance-aug-07-2025.pdf), [2022](https://www.caiso.com/documents/2022-annual-report-on-market-issues-and-performance-jul-11-2023.pdf)) | actual market engine, competitive-offer counterfactual | annual DA price-cost markup | 2021 **2.5%**, 2022 **3.1%**, 2023 **3.6%**, 2024 9.6% (methodology change) — actual price sits 0–4% off a cost-based simulation in competitive years | strong (noise-floor, not skill bar) |
| 6 | [MISO SOM 2023](https://www.potomaceconomics.com/wp-content/uploads/2024/06/2023-MISO-SOM_Report_Body-Final.pdf) (Potomac); [PJM SOM 2024](https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/2024/2024-som-pjm-sec3.pdf) | markup analyses | annual price-cost markup | MISO **3.0%** (2023); PJM RT ~−0.1% annual but **July peak-hour markup 10.0%** monthly | strong (noise floor) |
| 7 | [EIA AEO Retrospective](https://www.eia.gov/outlooks/aeo/retrospective/) ([Table 1](https://www.eia.gov/outlooks/aeo/retrospective/pdf/table_1.pdf), [Table 2](https://www.eia.gov/outlooks/aeo/retrospective/pdf/table_2.pdf), AEO2022 vintage) | NEMS, US | forecast-error SD by horizon H (yrs) | electricity price H=1/2/3: **3.6/6.4/8.3%**; gas gen: 5.7/8.6/9.6%; coal gen: 6.1/10.8/13.2%; **CO2: 3.2/4.1/4.9%**; pooled avg abs: price 9.8%, CO2 14.6% | medium (forecasts — upper bound for a backcast) |
| 8 | [PyPSA-Eur 2020–24 hindcast](https://arxiv.org/abs/2606.16486) (TU Berlin/DTU, 2026) | open PCM, Europe | price SMAPE | daily load-weighted **20.8–21.3%** (dynamic fuel prices); static annual fuel prices degrade to 53–100%; **spikes systematically missed**; 2022 coal/gas split materially wrong | strong |
| 9 | [em.power dispatch](https://arxiv.org/abs/2304.09336) (Germany 2016–20) | LP fundamental model | hourly price errors | RMSE 9.50 €/MWh, MAE 6.00 €/MWh, mean bias ~−2.2 €/MWh (**~5–7% of mean price**) | strong |
| 10 | [NREL TP-581-42305](https://docs.nrel.gov/docs/fy08osti/42305.pdf) | PCM validation practice | norm-setting | hour-by-hour / unit-level comparison to actuals is **not a valid test**; validate seasonal-to-annual generation by type vs EIA-923 | medium |
| 11 | ERCOT LTSA (UPLAN), MISO/PJM PROMOD benchmarking, [WECC ADS](https://www.wecc.org/system/files/documents/anchor_data_set/2024/ADS_Data_Development_and_Validation_Manual_6-30-2020_V3.0.pdf), [EPA IPM](https://www.epa.gov/power-sector-modeling/integrated-planning-model-ipm-results-viewer) | practice statements | — | benchmarking practiced, **no error statistics published**; EPA IPM has no historical-validation publication | weak/indirect |

**What "commercial grade" means, per metric (synthesis):**

- **(a) Annual mean price:** ±1–5% is best-in-class (SEM); **±5% is the only
  stated regulator criterion in the record**; ISO planning practice accepted
  −2…−17%; ~5–10% is the normal planning-grade range. The 0–4% market-conduct
  markup (DMM/SOM) is an identification **noise floor**: a cost-based model
  chasing residuals below ~3% is fitting the conduct wedge, not gaining skill
  (rule 1, now with citations).
- **(b) Monthly/seasonal shape:** regulator-accepted period biases of −9%/+11%;
  published monthly norms ~5–15% with correct seasonality; weekly SMAPE 20–26%
  is the academic state of the art for the model class.
- **(c) Generation by fuel:** family/zonal level only — NYISO ~0–4% zonal
  energy; AEO 1–3-yr SDs: gas ~6–10%, coal ~6–13%. **Nobody publishes
  per-class validation.** Coal/gas switching is the documented weak point of
  every published study (PyPSA-Eur 2022).
- **(d) CO2:** **no PCM publishes a backcast CO2 error.** AEO 1–3-yr SD
  3.2–4.9% (full forecast). Thinnest evidence base; stated as such.
- **(e) Scarcity tail / duration curve:** the universal documented weakness —
  ECA *excluded* ~50–100 h/month of spike hours from scoring; NYISO absorbed
  the residual into tuned hurdle rates; PyPSA-Eur reports spikes "not captured
  well" in every configuration. **No source publishes a tail-hour or
  duration-curve statistic as a fitness criterion.**

## 3. Rubric v2 decisions (the directive's items a–e)

**(a) Caveat budget — restored to 3, on a different axis, with the external
rationale the 3→2 cut lacked.** v2 splits caveats into *auto commercial-band*
caveats (inside a cited external band; listed with magnitude, unbudgeted — they
ARE the certification claim) and *ledgered measured-input* caveats
(beyond-commercial, excused only by a named data limitation; budgeted).
Protective (C7/C8) budget stays 1 (v1's hard budget, rule-20 enforcement
unchanged). Non-protective ledgered budget is 3: the recurring documented
data-limitation classes are three by construction (preliminary-923 vintage,
EIA-930 storage coverage, data-blocked scarcity-requirement series), so a
budget of 2 forced `NOT-YET` on data availability, not model quality — the
nyiso-34 demotion had exactly that shape. The 07-02 cut's stated concern
(price caveated wholesale) is now structurally impossible: a price miss beyond
±10%/0.20 requires a *named measured-input reason*, not a free slot. Note
honestly: at the v2 re-score the budget is not what flips anyone — NYISO uses
2–3 slots, NEISO 2 — the two-band structure does the work.

**(b) Criterion-set unification.** All six ISOs score the identical C1–C8 set.
The v1 asymmetries retired: ERCOT's C3c no longer gates on its own ORDC-adder
proxy (kept as a report-only diagnostic, with the >$500 companion); the tail
basis is the same DA-expressible count for every ISO, per-ISO only in
*threshold* ($300 NYISO/NEISO winter city-gate — a market-design fact). The
reported D-7 statmode gaps must be re-measured on one criterion denominator
(flagged stale; re-measurement is solve work, out of this session's scope).

**(c) Scope-consistent C3c.** Gates the **DA-expressible tail** — the hourly,
commitment-aware DA market's own count of hours above the threshold, derived
from measured hub series into the committed `tail/actual_tail.json`
(2023–2025 only; rule-22 guard in the deriver). The RT count is a report-only
companion. This follows the MISO tail diagnosis §1 decomposition (2023 RT tail
= 30 isolated 5-minute-market transients; DA tail = 1 h) and is **not lenient
in either direction**: ERCOT's DA tail is *larger* than RT (311 vs 181 h in
2023 — DA prices scarcity expectations), so ERCOT's gate got harder; PJM/MISO
2025 collapsed tails (0 h vs DA 51/38 h) still FAIL. Band [0.5×, 2×] with a
<10 h absolute guard; supporting tier (no intended use consumes exact tail-hour
counts; the scarcity *level* stays load-bearing in C3a/C3b — and we keep
scoring the tail at all, which is stricter than published practice, per §2(e)).

**(d) Unchanged protections.** Rule-20/C8, C7, C6, D-9, D-6, E9, the exceptions
ledger, rules 13/14/22. Verified: no edit to `legitimacy_diagnostics.py`,
`audit_keepers.py`, holdout gates, or any threshold in C6/C7/C8.

**(e) Keeper principle.** Unchanged: keepers are the most structurally
faithful run; the rubric certifies fitness of the *designated* keeper, it
never selects by MAE. The rubric doc restates this (§preamble) and the
determination still fails a keeper whose structure is dishonest regardless of
its scores (C6–C8 precede every accuracy criterion in the decision logic).

## 4. The comparison table (current thresholds vs published vs our keepers)

v2 bands vs best published comparable vs the six keepers' actual v2 scores
(worst scored year shown; ✓ = target band, ○ = commercial band, ✗ = FAIL,
L = ledgered measured-input caveat):

| Criterion | v1 threshold | v2 target / commercial | Best published comparable | ERCOT | CAISO | PJM | NYISO | NEISO | MISO |
|---|---|---|---|---|---|---|---|---|---|
| C3a mean LMP | ±5% hard-edge | ±5% / ±10% | SEM criterion ±5%; NERA +0.1%; NYISO −2…−17% accepted | ○ +8.2% ('25) | ✗ +41.6% | ✗ −13.3% | L −10.9% | ○ −8.3% | ✗ −19.5% |
| C3b monthly NRMSE | ≤0.15 | ≤0.15 / ≤0.20 | SEM −9%/+11% period bias accepted; monthly norm 5–15% | ✗ 0.324 ('23) | ✗ 0.459 | ○ 0.196 | L 0.221 | ○ 0.169 | ✗ 0.225 |
| C3c tail hours | [0.7×,1.5×] vs RT | [0.5×,2×] vs **DA** (<10 h: \|Δ\|≤10) | none published; practice excludes spikes or tunes to them | ✗ 0.30× | ✗ 0.00× | ✗ 0.00× ('25) | ✓ 0.58× | L 0.00× ('25) | ✗ 0.00× |
| C1 per-class mix | min(2% load, 8 TWh) & 3 pp | unchanged (single-band) | **none published** (family grain only) — stricter than commercial | ✓ | ✗ +10.1 TWh | ✗ −19.8 TWh | ✓ | ✓ | ✗ +44.4 TWh |
| C2 family vol (prelim fallback) | ±2.5% | ±2.5% / ±5% | NYISO zonal ~0–4%; AEO gas SD 5.7–9.6% | ○ −5.0% | ✗ +8.1% | ○ +3.9% | ✓ −2.0% | ○ +3.0% | ✗ +8.8% coal |
| C5a CO2 | ±7% | ±7% / ±10% | no published PCM backcast; AEO SD 3.2–4.9% | ✓ +1.0% | ○ +8.6% | ✓ +4.6% | ○ −8.2% | ✓ +4.1% | ✓ +4.1% |
| C4 hourly fleet r | r≥0.70, NRMSE≤0.30 | unchanged | **none published**; NREL: hourly test invalid — stricter than practice | ✓ | ✗ r 0.55 | ✓ | ✓ | ✓ | ✓ |
| C5b storage | ±30% | unchanged | none published | skip | skip | skip | skip | L −56% | ✗ +1330% |
| C6/C7/C8 | pass/fail | unchanged | beyond practice (NYISO tunes hurdle rates; our C6 forbids it) | ✗ C8 12.4% | ✗ C7+C8 | ✗ C8 12.1% | L C8 | L C7 | C6 unattested |

**Stricter than anything commercial demonstrates (kept deliberately, flagged
per the directive):** C1 per-class mix; C4 hourly correlation; scoring C3c at
all; C6's prohibition on residual-tuned parameters (published practice openly
tunes hurdle rates and offer markups); the C7/C8 shape/forcing gates (no
external analogue). These stay because the intended uses (§0 of the rubric)
consume the class mix and because the protective gates are what make the rest
believable — but the table says out loud that no vendor is held to them.

**Below commercial grade (stays NOT-YET, no grading down):** CAISO price level
(+20–42% — no published backcast is remotely this far off), CAISO/MISO/PJM
collapsed DA tails against material actuals, MISO CC_REGULAR +44 TWh and
storage +1330%, PJM 2025 price −13.3%, ERCOT 2023 shape 0.324. The commercial
band is an anchor, not a curve.

## 5. Re-score result (all six keepers, one sweep, no solves)

| ISO | Keeper | v1 | v2 | What changed |
|---|---|---|---|---|
| **NYISO** | `2026-07-06-nyiso-53-li-tsl` | NOT-YET (4 soft caveats > 2) | **CALIBRATED-WITH-CAVEATS** | C3c now PASSes on the DA-expressible basis (7 h vs 12 h, 0.58× — the Zone-K LCR/TSL mechanism vs the same-resolution benchmark); C5a −8.2% is commercial-band; C3a/C3b stay ledgered (2/3 budget); C8 ledgered protective (1/1) |
| **NEISO** | `2026-07-06-neiso-49-stgas-netload` | NOT-YET (hard 2>1, soft 4>2) | **CALIBRATED-WITH-CAVEATS** | C2 vintage +3.0% and C3a/C3b move to commercial-band (unbudgeted, listed); C3c 2025 + C5b stay ledgered (2/3); C7 ledgered protective (1/1) |
| ERCOT | `2026-07-06-ercot34-stage4-overlay-off` | NOT-YET | NOT-YET | honest fails stand: C3b 2023 (0.324), C3c 0.30–0.32× vs DA (harder than v1's RT basis: DA 311 h in 2023), C8 CT 12.4% (rule 20) |
| PJM | `2026-07-05-pjm-77-ct-relfloor` | NOT-YET | NOT-YET | C1 2023 (CC −19.8 / ST_GAS +11.8 TWh), C3a 2025 −13.3%, C3c 2025 0 h vs DA 51 h, C8 12.1% |
| CAISO | `2026-07-03-caiso-51-firm-base` | NOT-YET | NOT-YET | 8 criterion fails incl. price +20–42%, C7/C8 |
| MISO | `2026-07-05-miso-41-ct-evening` | NOT-YET | NOT-YET | C6 unattested (G-02), C1 +44 TWh, price level/shape/tail, storage +1330% |

Everything the v2 flip "forgives" is either (i) inside a cited commercial band
and printed on the dashboard with its magnitude, or (ii) a pre-existing
ledgered measured-input limitation the v1 scorer had already accepted as a
caveat — no new excuse was minted for any keeper, and no keeper's underlying
numbers changed (no solves).

## 6. Calibration-complete recommendation (owner-gated; markers NOT set)

Rule 22: the `calibration-complete.json` marker and the one-shot 2022 /
H1-2026 holdout validation are **owner decisions**. This memo recommends;
it does not act.

> **Adjudicated 2026-07-06 (marker-adjudication session): owner HELD both
> markers.** NYISO held until #1344 lands (the C8 CT forced-share caveat
> dominates); NEISO held until the winter-fuel Component-B / C7 ST_GAS
> residual is re-examined. Preconditions were verified first (both keepers
> re-scored CALIBRATED-WITH-CAVEATS at HEAD; U-01 resolved — the Component-A
> probes were registered all along; G-13 moot for nyiso-53). No marker was
> written, no holdout data intaken, no solve run. Record: the 2026-07-06
> calibration-log adjudication entry.

**NYISO — recommend declaring calibration complete**, with eyes open:
- v2 determination CALIBRATED-WITH-CAVEATS; zero FAILs; 6/10 scored criteria
  at target grade; the intended-use price level sits at −9…−11% with the
  residual attributed to the ledgered #1344 reserve-scarcity/uplift frontier
  (data-blocked, not tuning-blocked) and the Iroquois Z2 winter data ask.
- Known risks the owner should weigh: the C8 ledgered caveat is large (CT
  forced share 92.7% of a small 1.6 TWh class — the ledger argues the floor is
  the windowed temperature-reliability ramp and the *economic* CT energy
  collapses without #1344 price formation; rule 20's letter would read this
  as a fail, and the ≤1 protective budget is the only thing admitting it);
  and the keeper is flagged stale-vs-HEAD (G-13). If either concern
  dominates, hold the marker until #1344's data ask lands.
- On declaration: intake NYISO 2022/H1-2026 actuals under the rule-22
  session-logged authorization, freeze this keeper config, score ONCE with
  `--holdout-authorized`, record whatever results.

**NEISO — recommend declaring calibration complete after one lookup**:
- v2 determination CALIBRATED-WITH-CAVEATS; zero FAILs; every load-bearing
  criterion at or above commercial grade; the four price/storage caveats all
  trace to the single documented winter fuel-inventory gap (G-24) with a
  built (default-off) Component A and a designed Component B — a *named
  structural* limitation, not scattered unknowns.
- Precondition: resolve U-01 (the unregistered winter-fuel probes — rule-15
  compliance) before the marker; the C7 2024 ST_GAS ledgered caveat (flat
  committed-floor year at $2.19 gas) should be re-examined when Component B
  lands but does not block a with-caveats certification.
- Same one-shot holdout protocol as above on declaration.

**Do not declare** ERCOT/PJM/CAISO/MISO: each carries undocumented
beyond-commercial fails on load-bearing or protective criteria (§5), all with
open root-cause workstreams (G-20…G-25).

## 7. Re-measurement obligations created by v2

- The D-7 statmode gaps quoted next to keepers were measured on the v1 rubric
  and mixed criterion denominators — flagged stale on the dashboard; re-measure
  with `run_statmode_probe.py` against current keepers on the v2 scorer
  (solve work).
- `tail/actual_tail.json` re-derives only when its source hub series update
  (rule 23; the deriver hard-guards years to 2023–2025).
- Keeper `metrics.json` sidecars regenerated this session record
  `rubric_version: 2` (now 2.1 after the addendum below).

## 8. Addendum — v2.1 owner amendments (2026-07-06, same day)

Two owner-directed amendments landed after the v2 re-score (§5), recorded here
so §4/§5 above stay the v2.0 record:

1. **C7/C8 materiality floor.** The protective shape and forced-share gates
   score only classes with annual energy — **max(model, actual)**, so a floor
   cannot hide a class below the line by its own forcing — **≥ 2 % of total
   ISO load**. Smaller classes are SKIPPED-immaterial with the D-1/D-2
   readings annotated (reported, never gated). Owner rationale: structural
   work making a trivial class hit a diurnal-r or unforced target is effort
   spent where no intended use consumes the answer. 2 % is the clean cut in
   the keeper data: NEISO ST_GAS/CT (0.1–0.7 % of load) and NYISO CT
   (1.4–1.9 %) fall below; CAISO CT 2023/24 (2.1–2.3 % — the caiso-42
   flat-floor case the gates exist to catch), PJM/MISO CT (3.5–4.2 %) and
   every material ST_GAS (2.1–10.6 %) stay gated. Mirrors the C2 (10 TWh) and
   C4 (5 TWh) immateriality precedents.
2. **C8 peaker cap 10 % → 15 %** (CLAUDE.md rule 20 amended in place;
   `legitimacy_diagnostics.py` D2 gate mirrored). Stated honestly: **no
   external anchor exists for either value** — no published model reports a
   forced-energy share at all — so this is an owner risk-tolerance setting on
   an internal protective gate, not a benchmark move. The scorer now gates
   D-2's *measured* shares against the rubric's caps rather than the
   artifact's embedded verdicts, so committed artifacts re-score correctly
   across gate versions.

**v2.1 re-score effect:** ERCOT C8 clears (CT 12.4 % forced but 1.5–1.7 % of
load → immaterial) — ERCOT's NOT-YET is now purely the price-structure fails
(C3b 2023, C3c), i.e. G-22; PJM C8 clears (CT 12.1 % < 15 % cap, class
material at 3.5 %) — PJM's NOT-YET is now C1 + C3a + C3c; NYISO's CT row
(92.7 % on a 1.4–1.9 %-of-load class) and NEISO C7 (ST_GAS 0.1–0.3 %) become
immaterial-skips; CAISO's C7/C8 CT fails stand (2.1–2.3 % of load,
27.5–32.6 % forced). The amendment also supersedes the same-day C7-only
2.5 % materiality cut landed in parallel by the L-15 lane (owner-confirmed
X = 2 %, scope C7+C8, max(model, actual) basis).

**Post-rebase status correction (2026-07-06 PM): the §6 NYISO recommendation
is WITHDRAWN pending root-cause work.** The same-day D-2 forced-energy
legitimacy regeneration (PR #1512) rebuilt NYISO's committed
`legitimacy_diagnostics.json` with full class coverage, surfacing **ST_GAS
forced at 59.7–69.8 %** of a fully material class (5.7–8.4 TWh, 3.9–5.5 % of
load — G-05's known number, previously absent from the bundle artifact). The
materiality floor correctly does not exempt it; there is no ledger entry; the
undocumented FAIL governs and **NYISO scores NOT-YET at HEAD** — under v1,
v2, and v2.1 alike. This is the protective gate working as designed on a
material class. The NEISO recommendation (§6) stands unchanged. NYISO
re-enters consideration when the ST_GAS floor is re-derived or ledgered with
a driver+window+forward story (the #1344 scarcity-formation family).
