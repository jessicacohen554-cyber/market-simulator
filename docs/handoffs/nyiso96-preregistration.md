# nyiso-96 pre-registration — CT fast-start tranche startup amortization

**Written BEFORE the A/B was launched.** Recorded so the verdict is scored
against a prediction rather than rationalised after the numbers land, following
the `nyiso90-preregistration.md` precedent.

## 1. Lane and lever

Lane: NYISO C3c, queue item 2 — the CT start-frequency lane
(`docs/mechanism-testing-matrix.md` §5.5). Lever under test: matrix row
`tranche_startup_amortization` (NYISO cell `U`), armed together with its v3
measured-run basis `tranche_startup_measured_runs`. The two are ONE
mechanism family and one matrix row; v2 alone is the self-disabling circular
form (the nyiso-44 finding), so the family is tested in the configuration its
own docstring designates as correct.

**Rule 25 [R-ISO-SCOPE] compliance.** No parameter is ported. The v3 basis reads
`data/raw/_processed-legacy/campd_ct_run_lengths_NYISO.csv` — NYISO's own CAMPD
measured start-to-stop run lengths (22 plants + a pooled class fallback of
4.0 h, 34,057 runs). Start costs are the already-cited NREL table
(`fleet.BIN_STARTUP_COST_PER_MW`). Zero new fitted scalars.

## 2. Why this lever, and why not the alternative

The STEP-1 characterisation (`scripts/probes/nyiso96_ct_start_characterization.py`,
`nyiso96_ct_offer_reveal.py`) independently reproduces nyiso-90/91 on the
keeper's own committed sidecars:

* the model's CT_PEAKER **run lengths already match measured** — plant-grain
  median 6 h model vs 5 h measured in every year, mean 6.29/6.26/8.62 vs
  6.62/6.40/7.83. Block SHAPE is right;
* what is missing is **starts** — 987/894/2,048 model vs 3,737/3,796/3,528
  measured (3.79x/4.25x/1.72x);
* **82–88 % of the missing online-hours are hours the model prices BELOW the
  plant's own measured SRMC** — a commitment signature, not an economics one;
* the measured below-SRMC energy is **spread flat, not concentrated**: the
  deepest 10 % of below-SRMC hours carry only 3.3–6.6 % of that energy, barely
  above the same fleet's total-energy reference (2.5–4.4 %). A start-recovery
  story would concentrate it;
* **53–66 % of measured CT energy clears below its own SRMC at the fleet's own
  zonal price** (hub + measured NYC/LI premium), which is model-independent;
* availability is not binding (class capacity ~fully available, ≤3 % derate).

The characterisation therefore selects the **commitment/obligation** family, not
the start-economics family. Every commitment-side candidate in reach is already
adjudicated or governance-blocked (J/K obligation refuted at +0.11 TWh by
nyiso-83; reserve tiers closed by nyiso-84; `nyiso_gas_bridge_ct` block
commitment eliminated by nyiso-90 at +0.01–0.03 % of the gap; windowed floors
forbidden by owner directive 2026-07-27 and rule 17). The one surviving
candidate — NYISO SCUC load-pocket security commitment with BPCG make-whole —
is a sub-zonal data-intake and topology question needing owner scoping
(nyiso-91), not a mechanism this session can build.

`tranche_startup_amortization` is the last **buildable, un-adjudicated,
non-governance-blocked** cell in the queue. It is tested to close the matrix
cell with a measured verdict rather than an assumed one.

## 3. Pre-registered prediction

Markup added to each fast-start tranche is `startup_$/MW ÷ run_hours`. With the
NREL CT start cost (~$20/MW) and NYISO's measured median run basis of 3–6 h
(class fallback 4.0 h), the expected offer increment is **≈ $3–7/MWh** on the
CT_PEAKER econ + peak tranches.

Predictions, in order of confidence:

1. **CT_PEAKER energy and start count MOVE THE WRONG WAY** (down), because the
   lever raises the offer of a class the model already under-dispatches by
   1.5–1.9 TWh/yr. Expected magnitude: small — a few hundredths of a TWh —
   because the class is thin and its offer already sits near the margin.
2. **Run lengths barely move.** The model's runs already match measured, so the
   v3 ceiling `min(P0_run, measured_median)` binds rarely and v2/v3 nearly
   coincide for NYISO — unlike the ISOs where v3 was built to break a
   long-block circularity.
3. **C3c may improve marginally.** A higher CT offer raises the price the
   marginal peaker sets, which is the one channel by which this lever could
   help the lane's sole determination blocker. This is the only outcome that
   would argue for keeping it, and it is the reason the solve is spent rather
   than the cell being closed on direction alone.
4. **The knife-edge cell C1 2023 CC_REGULAR** (−3.045 TWh against ±2.94,
   currently FAILING) moves little; any CT displacement lands on CC/ST.

## 4. Decision rule, fixed in advance

* The lever is **NOT** promoted on a C3c gain alone if predictions 1 holds and
  the class level regresses — rule 1 [R-STRUCT] cuts both ways, and a mechanism
  that moves a class further from its measured level while buying tail hours is
  buying the right number by the wrong mechanism.
* The lever is **rejected `R`** if it degrades the CT level/start count without
  a structural argument that the higher offer is the more faithful
  representation.
* Whatever the outcome, the matrix cell is stamped and the run registered
  (rules 15/28b), rejection included.

## 5. A/B design

Single mechanism-family delta, `--replay-bundle` off the keeper's own
`meta.json` so every other kwarg is byte-identical:

* control `nyiso96_ctrl_zerodelta` — keeper recipe verbatim (a same-HEAD
  zero-delta baseline is required: this environment's solver/pandas differ from
  the keeper's recorded ones, so the registered keeper metrics are not a valid
  baseline — the nyiso-83 precedent);
* arm `nyiso96_ctamort` — the same recipe with
  `tranche_startup_amortization=true` and `tranche_startup_measured_runs=true`.

All three years 2023/2024/2025 in ONE invocation each, sequential within it
(rule 16 + rule 12); the two invocations run concurrently (rule 12, cap ~2 for
per-plant multi-zone LPs).
