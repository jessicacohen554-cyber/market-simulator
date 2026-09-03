# PRECOMMIT ADDENDUM — caiso-240: the §6 decision, FIRED, and the arm's ADVERSE BOUND

**Registered 2026-09-03, session caiso-240. Branch
`claude/caiso-239-hr-mult-census-ycpdgu`. PUSHED BEFORE THE SOLVE. No LP has
been built and no solver has been called in this session; every number below
comes from committed artifacts and from `run_year(fleet_only=True)` fleet
rebuilds.**

Parent: `PRECOMMIT-caiso240-default-hr-mult-census-2026-09-03.md` (`bfa6999a`,
pushed before any footprint measurement). This addendum records what the census
measured for CAISO, applies the parent's §5 grading and §6 decision rule to it,
and pre-registers the arm's adverse bound and gates **before** the arm solves.
Nothing in the parent is re-specified.

---

## §A1 — THE METHOD FALSIFIERS BOTH PASS

* **M-1 (null pass).** A baseline→baseline rebuild of the CAISO keeper (2023) is
  **byte-identical** in `unit_ids`, `heat_rate` and `mc_base` across all 1,801
  fleet rows. The cache-clearing hazard declared in parent §3.3 does not bite.
* **M-2 (two-point validation).** The `ST_GAS.mc` cell is responsive on
  **exactly 3** tranches — plants **315 / 335 / 350** — in **every** year on the
  **caiso-231 predecessor recipe**, reproducing caiso-239 F-1 exactly; and on
  **ZERO** tranches in every year on the **caiso-239 keeper**. The instrument is
  validated, and caiso-239's repair is independently confirmed to have retired
  the literal it claimed to retire.

## §A2 — THE CAISO FOOTPRINT: 2 OF 28 CELLS LIVE

Measured on `2026-09-02-caiso-239-b1-stgas`; 2023 figures, stable across years.

| cell | tranches | mc-live | plants | pmax | available |
|---|--:|--:|---|--:|--:|
| `ST_GAS:econ` = 1.00 | 3 | 3 | 315 / 335 / 350 | 2,240.8 MW | 15,958.8 GWh |
| `ST_GAS:peak` = 1.10 | 3 | 3 | 315 / 335 / 350 | 428.8 MW | 3,054.0 GWh |
| every other cell | **0** | — | — | — | — |

## §A3 — THE §5 GRADES, AND THE §6 DECISION

* **`ST_GAS:peak` → F1, GROUNDABLE NOW.** Footprint non-zero; the counterpart is
  **1.166**, read from the committed
  `data/raw/_validation-source/caiso_offer_curve_measured.json`
  (`CT_PEAKER.bands.peak`), a single number against a single flat model
  multiplier — **at the model's own grain**. Population match: the derive's own
  disclosure, *"the three OTC/RMR steamers (ST_GAS …) and priced CT_CHP curves
  land in the CT bucket"*, which is the exact basis caiso-231 re-grounded the
  ST_GAS class band on. Zero free parameters — 1.166 is already the value the
  keeper's own ST_GAS class band carries.
  **DISCLOSED AGAINST INTEREST: the population match is CONTAINMENT, not
  coincidence**, and so is weaker than caiso-239's exact ten-unit coincidence —
  the CT bucket is pooled CT_PEAKER + CT_CHP + ST_GAS conduct and the OASIS ids
  are masked, so the steamers cannot be isolated inside it.
* **`ST_GAS:econ` → F3, NOT GROUNDABLE AT THIS GRAIN.** Footprint non-zero and
  **larger** (2,240.8 MW vs 428.8), but the model's band for a bypassed plant is
  **one flat multiplier** while every measured counterpart is a **two-endpoint
  ramp** — the class's measured `econ_low` 1.145 / `econ_high` 1.166, or the
  physical `marg_econ_low` 0.725 / `marg_econ_high` 0.755. No measured value
  exists at the model's own grain, and choosing an endpoint would be a free
  parameter, which parent §6(3) forbids. **Not armed.** Its F1 route (render the
  measured ramp with the keeper's own registered `offer_curve_smoothing_n = 6` /
  `exp = 1.0`) is a mechanism change, not a substitution, and is put to the owner
  in the assessment.
* **§6 FIRES on `ST_GAS:peak`** — the only F1 CAISO cell, hence trivially the
  largest. **Exactly one cell is executed**, as the parent caps.

## §A4 — WHAT IS BUILT (committed at `80318b90`, before this addendum)

`ScenarioConfig.caiso_st_gas_peak_measured` — gated, **default off**, per-ISO
registry `constants.ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO` (CAISO 1.166, cited to
the OASIS artifact). One gated limb in `fleet/assembly.py`'s `offer is None`
branch, **band-disjoint** from its caiso-239 sibling (rule 19 `[R-ONE-MECH]`);
an ISO with no registry entry is a **hard error** at both the config gate and the
consumer (rule 25). Threaded onto `--replay-bundle`. Eight unit tests including
the two-mechanism disjointness pin. Matrix base row plus a cell line in every ISO
shard, same commit (rule 28(c)); ERCOT's cell is **`U`, not n/a**.
**Registered in `_BACKCAST_ONLY_OVERLAY_FIELDS`, unlike caiso-239's** — this
arms measured **BID** conduct keyed to a year's OASIS record, not a physical
heat-rate ratio (rule 13 `[R-MEASURED]`). The pinned default cache key
`cedadc285f8603b9` is **unmoved**; the flag is registered in the cache-key
optional list in the same commit as the field (nyiso-119 discipline).

## §A5 — THE ADVERSE DIRECTION AND BOUND, BEFORE THE ARM SOLVES

**Direction is ADVERSE.** 1.10 → 1.166 is **+6.0 %** on the peak band, i.e.
**UP** on a C3a already over in 2024 and 2025. Per rule 1 `[R-STRUCT]` that is
not an argument against the repair; it goes on the record first.

First-order bound, caiso-230 §H form re-run on the **caiso-239 keeper**
(`scripts/probes/_caiso240_cell_bound.py` →
`results/calibration/_caiso240_cell_bound.json`, zero solves):

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| matched-marginal zone-hours | 12 | 14 | **0** |
| **THE ARM** — `ST_GAS:peak` 1.10 → 1.166 | **+0.0014** | **+0.0011** | **zero to within the estimator's attribution tolerance** |
| *(not armed)* `ST_GAS:econ` 1.00 → 1.145 | +0.0108 | +0.0084 | +0.0044 |
| C3a required move (scorer basis, caiso-230 §E) | 0.00 | −0.848 | −1.893 |
| model annual load-weighted price | 56.3744 | 39.0060 | 39.7867 |

The arm's bound is **+0.0014 $/MWh at its largest**, 0.17 % of 2024's required
move. **The 2025 leg is degenerate exactly as parent §0.7(2) anticipated** — no
responsive tranche is ever the matched marginal rung there — so it is stated on
the estimator's tolerance and **not** as an exact zero, and a small measured
move in 2025 is a bound-form limitation, not a falsification.

**Registered prediction:** measured C3a moves ≤ the bound in 2023 and 2024, and
lands inside the estimator's attribution tolerance in 2025; **no year flips
verdict; 2023 stays PASS.**

## §A6 — THE OWNER FLAG THE PARENT §0.8 RESERVED, ANSWERED

Parent §0.8 asked whether the funded cell would be live in all three years, in
which case the caiso-231 "no control arms" directive would leave the arm with
**no** independent check. **It is not.** The measured 2025 bound is zero
matched-marginal zone-hours, so 2025 is the year in which G-CTRL's
dispatch-identity leg can bind. The gap the parent flagged is therefore **not
realised on this arm** — but the flag stands for the next arm that is live
everywhere, and the FINDING will report what the 2025 leg actually showed.

## §A7 — GATES, UNCHANGED FROM PARENT §6, WITH THE BOUND NOW NUMERIC

G-CTRL (dispatch identity), G-STRUCT (exactly the three `_peak` tranches of
plants 315/335/350 move, at the exact ratio 1.166/1.10 = 1.06; 0 other bands,
groups or ISOs), G-INERT, G-C3a (≤ §A5's bound, no verdict flip, 2023 stays
PASS), G-C1 (12/12, free 8/8), G-C3b (with the 2025 composition-watch tripwire
re-read), G-C8, G-CAVEAT (budget 1 of 1). **Promotion rule unchanged:** proposed
as keeper only if every gate but G-C3a passes and G-C3a shows no verdict flip; a
regression **within** the bound does not block promotion, a verdict flip does.

**THE ARM:** `--replay-bundle results/calibration/caiso239_b1_stgas_committed_measured
--caiso-st-gas-peak-measured --year 2023 2024 2025`, sequential, one invocation,
one bundle (rules 12 / 16), registered on the backcast dashboard in **this**
session whether keeper or rejected probe (rule 15).
