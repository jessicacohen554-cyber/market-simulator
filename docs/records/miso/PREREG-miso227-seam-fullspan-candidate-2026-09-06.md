# PREREG miso-227 — THE FULL-SPAN KEEPER CANDIDATE: the neighbour-anchored PJM seam ladder armed on the miso-220 recipe across 2023/2024/2025, under the owner's explicit rule-1 steer. The PROMOTION DECISION RULE is declared here, BEFORE the solve.

**Incumbent keeper `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the single
ledgered caveat. This document is committed and pushed **before** the solve. Rule 22
`[R-HOLDOUT]`: 2023–2025 only. Rule 16 `[R-ALLYEARS]`: **all three years, ONE `--year`
invocation, ONE bundle** — which is precisely why the miso-226 screen bundle could never have
been promoted and was deleted under rule 29(c).

## 0. THE OWNER STEER THAT OPENED THIS, recorded verbatim

miso-226 cleared its screen and I recommended **against** spending the full span, weighting the
gate regressions over the structural gain. The owner overruled that weighting:

> *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves
> but gates regress that may still be a keeper."*

That is rule 1 `[R-STRUCT]` restated by its author, and my recommendation had it backwards. Rule
1 says a structurally-correct mechanism is **never** judged by whether it improves the fit and
is **never** reverted because the residual moved the wrong way; rule 14 `[R-ACCURATE]` says a
worse fit on a more faithful input is a **discovered bug elsewhere**, not grounds to revert.
This run is that correction, and the owner's sentence is the rule-29(2) owner step my miso-226
PRECOMMIT §0 pre-registered as the gate between a cleared screen and a full span.

## 1. THE STRUCTURAL CASE — why this is a candidate at all

| | incumbent `miso_seam_measured_ladder` | armed `miso_seam_neighbour_anchored_ladder` |
|---|---|---|
| PJM import band *k* priced at | a quantile of **MISO's OWN** DA hub | a quantile of the **PJM western-border** DA |
| an import's merit position depends on | the **buyer's** own price | the **exporting market's** supply cost |
| owner ruling (2026-09-06) | — | **the ONE admissible form** of the D-2 5(i) object |
| fitted parameters | 0 | **0** (measured table, frozen derive) |
| forward analogue | EIA-930 + MISO DA | EIA-930 + border LMP, pooled 2023–25 ladder |

The incumbent anchor is **structurally wrong in kind**: a seller does not price its offer off the
buyer's clearing price. That it is *measured* does not make it *right* — it measures the wrong
quantity. The neighbour anchor measures the right one. miso-226 then showed the mechanism does
what its arithmetic claims (0.829× its static, 277× footprint concentration, all five gates), so
the structural improvement is not hypothetical.

**Stated plainly and against the arm**: the neighbour anchor is *more faithful, not fully
faithful*. It fixes the ladder's **anchor** and leaves its **frozen-annual-quantile** form, which
is why miso-226 measured only 3 % of the responsiveness repair. Arming a strictly-more-faithful
form while its successor (the hourly anchor) is unbuilt is exactly what rule 1 prescribes; it is
not a claim that the seam is solved.

## 2. THE CANDIDATE

```
python3 scripts/replay_keeper.py results/calibration/miso220_nonsteamlift_B \
  --out-dir results/calibration/miso227_seamneighbour_K \
  --years 2023 2024 2025 \
  --set miso_seam_neighbour_anchored_ladder=true \
  --note "miso-227 full-span keeper candidate: neighbour-anchored PJM seam ladder on the miso-220 recipe"
```

**ONE armed field** against the designated keeper's recipe. Both fuel fields
(`miso_gas_marginal_commodity_pricing`, `miso_gas_variable_transport`) stay **OFF** — they are
`O`, unpromoted, and this run does not touch them. Years run **sequentially inside one
invocation** (rule 12 `[R-PARALLEL]`). **DOF ledger unchanged at 41/2**: zero fitted scalars, no
new `ScenarioConfig` field.

## 3. G-DRIFT — `47e306d3..13ee0c89` (45 commits of `main` since the miso-226 screen)

| changed file(s) | classification | reason |
|---|---|---|
| `data/fuel/basis/miso.py` (±12), `scripts/run_calibration.py` (±6) | **INERT** | pure formatter reflow (the transport cache annotation, the ladder vector lookup, the miso-225 seam guard). No branch, value or condition changed |
| `config/constants.py` (±55) | **INERT** | **comment-only** — an "ILLUSTRATIVE" label replaced by "committed (owner ruling S9)". Both values unchanged (`mid` 0.5 / 4.5) |
| `config/scenarios.py` (+101), `policy/cap_and_trade.py` (+56), `results/evolution_ledger.py` (+11) | **INERT** | SCN-CAP `mass_cap_tons_by_year` (owner ruling S12): a NEW field defaulting `None`, and `__post_init__` **coerces it to `None` when `mode == "backcast"`**; `scheduled_power_sector_budget` returns `None` for a falsy schedule or an unnamed ISO. The MISO keeper is `mode="backcast"` with `carbon_price 0.0` / `carbon_price_path "zero"`, so the cap-and-trade path is doubly unreachable |
| `model/capacity_evolution/{evolve,retirements}.py` (+180/−.) | **INERT** | capacity evolution, entered only by `mode="forecast"` (`runner.py::evolve_fleet`); a backcast never reaches steps 0–7 |
| `results/cache.py` (+24) | **INERT** | cache-epoch ledger note; documentation, not a solve path |
| `data/raw/reference/caiso_offer_*` (3 files) | **INERT** | CAISO artifacts — rule 25 `[R-ISO-SCOPE]`, another ISO's lane |

**VERDICT: no LIVE hunk**, so attribution against the committed keeper stays valid (rule 29(b)
form 4) and no control solve is spent. The determination itself does not depend on this — a
keeper candidate is scored on its own merits against the actuals — but the arm-vs-keeper deltas
this document will report do.

Carried forward unchanged: the keeper was solved with cross-year warm-start ON and
`replay_keeper` pins it OFF (prices bit-identical, marginal-tie dispatch ~0.003 %); pydantic is
pinned to the keeper's recorded **2.13.4** so no environment caveat is carried.

## 4. THE PROMOTION DECISION RULE — declared BEFORE the solve, so it cannot be chosen to fit the number

The candidate is scored by `scripts/calibration_verdict.py` on the committed bundle. Then:

- **Determination `CALIBRATED`** → **PROMOTE.** Register (rule 15 `[R-DASHBOARD]`), edit
  `frontend/data/backcast/keepers/MISO.json`, rebuild `status/MISO.js`, run the
  `calibration-keeper-auditor`, re-stamp the matrix and the log.
- **Determination `CALIBRATED-WITH-CAVEATS`** → **PROMOTE**, with every caveat named on the
  determination basis. This is the case the owner's steer squarely covers: structural integrity
  up, a gate down, the ISO still calibrated.
- **Determination `NOT-YET` on a load-bearing criterion (C1 / C2 / C3a / C3b)** → **DO NOT
  PROMOTE unilaterally. Report and escalate.** The owner authorized *accepting a gate
  regression*; **decertifying the ISO is a different act** — it changes MISO's published
  headline from CALIBRATED to NOT-YET — and it is not implied by the sentence in §0. The
  candidate bundle, its verdict and the full criterion table go to the owner with a
  recommendation, and the incumbent keeper stays designated until they rule.
- **In every branch**: every criterion is reported at full magnitude, the incumbent's numbers
  beside the candidate's, and nothing is re-scored, re-banded or re-run to improve a verdict.

## 5. REPORTED AGAINST THE CANDIDATE, BEFORE IT RUNS — what miso-226 says to expect

From the scored 2023 screen (the same arm, the same recipe), all of which a full span will
reproduce and extend:

- **Every thermal C1 class moves AWAY from actual except ST_GAS.** 2023 deltas: CC_REGULAR
  −1.261, COAL_PRB −0.716, ST_GAS **−0.365 (toward)**, CT_PEAKER −0.304, CC_CHP −0.286,
  COAL_BIT −0.125, ST_CHP −0.034, COAL_LIGNITE −0.031 TWh; class sum **−3.12 TWh** against
  imports **+3.18**. The model is short in every one of those classes already.
- **CT_PEAKER-2023 is the named exposure and it may well FAIL.** The keeper sits at −7.985
  against a ±8.00 band (0.015 TWh of headroom); the delta transfer put the arm at **−8.289**,
  0.289 past the edge. On a real scored bundle that is a live C1 failure, and C1 is
  load-bearing — i.e. **the §4 escalation branch is a genuine possibility, named here before the
  solve, not a surprise to be explained afterwards.**
- **The annual import total moves further from every measured comparator** (2023: 45.754 →
  48.934 TWh). The seam's *duration shape* is the defect; this arm raises the *level*.
- **C3a should barely move**: the 2023 body price fell only **$0.308** (16 % of the joint arm's
  −$1.917), so the C3a-2023 cancellation is only slightly reduced. 2024/2025 are unmeasured —
  the band displacement is smaller there (−$3.03 / −$2.32 vs −$3.81), so a smaller effect is the
  expectation, and it is an expectation, not a target.
- **C3c is expected to remain the ledgered caveat** and nothing in this arm addresses the price
  tail.

**No band, threshold or verdict rule anywhere in the scorer is touched by this session.**

## 6. Governance

Rule 1 `[R-STRUCT]`: the mechanism is armed for its structural fidelity under the owner's
explicit steer, and no offer-curve multiplier is touched. Rule 13 `[R-MEASURED]`: a measured
table with an exact forward analogue; no outcome is pinned. Rule 14 `[R-ACCURATE]`: the more
faithful anchor is kept even though it degrades the fit; the SPP/South gap stays stated, never
proxied. Rule 16 `[R-ALLYEARS]`: all three years, one invocation, one bundle. Rule 19
`[R-ONE-MECH]`: the overlay supersedes the incumbent PJM ladder per seam, never stacks. Rule 22
`[R-HOLDOUT]`: 2023–2025 only. Rule 25 `[R-ISO-SCOPE]`: MISO only. Rule 28: the row exists
(minted by miso-225); the MISO cell is re-stamped by this session. **DOF ledger unchanged at
41/2.**

**Disclosed**: a cross-sha comparison of the DEFAULT `ScenarioConfig().cache_key()` (HEAD reads
`547053bdfccd4264`) was attempted against `47e306d3` and abandoned — the detached worktree would
not import the package. It does not bear on this run: the candidate solves into a fresh
`--out-dir` that does not exist, carrying a field value no prior bundle in it has, so the solve
is COLD by construction and the log line is checked for `cold` after the fact. The SCN-CAP field
is registered in the optional-field/drop-default registries in the same commit that added it.

Memory recipe: 8 GB swapfile re-armed and confirmed live from a separate call (`/proc/swaps`);
`MARKET_SIM_HIGHS_THREADS=4`; pins numpy 2.4.6 / scipy 1.17.1 / pandas 3.0.3 / pyarrow 24.0.0 /
highspy 1.14.0 / pydantic 2.13.4 / openpyxl.
