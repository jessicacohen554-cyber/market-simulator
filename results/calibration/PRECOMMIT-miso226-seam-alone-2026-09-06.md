# PRECOMMIT miso-226 — THE SEAM ARM **ALONE**: the neighbour-anchored PJM ladder with MISO's price carrying no exogenous shock, so the direction reading is unconfounded. Screen year 2023, ONE LP. S-1 is RE-SCOPED to reachability, declared here BEFORE the solve.

**Keeper `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the single
ledgered caveat. This document is committed and pushed BEFORE the solve, with the blind scorer
`scripts/probes/_miso226_screen_gates.py` in the same push. Rule 22 `[R-HOLDOUT]`: 2023–2025
only; **ONE LP (2023)**. Rule 29 `[R-SCREEN]`: the screen bundle
`results/calibration/miso226_seamalone_S` is a throwaway diagnostic probe — never registered,
never a keeper, and **deleted before this PR merges** (clause (c), owner ruling R-AV). Every
number this session will ever cite from it lives in this document or in the FINDING.

**No promotion is proposed, and none can follow from this screen.** Rule 29(2) is narrowed here
ex ante exactly as miso-224/225 narrowed it: screen → (owner, if it clears) → full span.

---

## 0. WHY THIS ARM, AND WHY IT IS THE CHEAPEST OPEN QUESTION ON THE BOARD

miso-225 screened the owner-ruled gas offer and the neighbour-anchored PJM seam ladder
**jointly**, and the seam leg failed its own direction gate in a way its FINDING §4 diagnosed
rather than accepted: every PJM import band came out **$2.3–4.6 cheaper** and imports still
**fell** (−75 MW in the cheap hours, −0.693 TWh annual), because the joint arm's *other* half
pulled MISO's body price down **$1.917** at the same time, and a fixed price ladder's bands
leave merit when the model's own price falls. Attributed against that price move, the anchor
had done **≈ +4.8 TWh** of real work and simply could not reverse the sign.

That is a confounded reading, and the FINDING named the clean successor in one sentence: run
the seam arm **ALONE**. With no fuel mechanism moving MISO's price, cheaper bands **must** raise
imports, so the mechanism's own arithmetic makes an unambiguous prediction and the LP either
honours it or falsifies it. This document is that test. It is also the first MISO screen in this
lane whose gate has **no confound available to explain a miss**.

The queue head (matrix §5.4 miso-225 stamp, item 1) names this arm first and instructs the
frozen G-2 bar be re-used verbatim. It is, below, to the digit.

## 1. PHASE 0 — the arm's own pre-solve arithmetic (zero-LP, committed)

`scripts/probes/_miso226_seam_static_remerit_phase0.py` → `_miso226_seam_static_remerit.json`.

The static re-merit, computed at the **keeper's own committed hourly `MISO_external` bus price**
(the bus the reference-price seam bands sit in) — i.e. the arm's premise made arithmetic: how
much import MW crosses from out-of-merit to in-merit purely because the ladder is re-anchored,
with nothing else moving. Exact to the keeper's own composition: per-band width =
`interface_limit_mw / SEAM_FLOW_TRANCHES`, and the keeper runs
`miso_seam_envelope_merit_cap = False`, so band *k*'s hourly availability is
`width × clip(cap(h)/interface_limit, 0, 1)` against the measured (month × hour-of-day) import
envelope.

| hour set | n | keeper bus price | keeper imports | static in-merit, incumbent | static in-merit, **neighbour** | **static Δ** | bands re-merited / hr |
|---|---:|---:|---:|---:|---:|---:|---:|
| all 8760 | 8,760 | $34.535 | 5,223.1 MW | 4,392.9 | 4,927.8 | **+534.9 MW** | 0.687 |
| **the frozen G-2 set** (real Indiana hub < $20) | **1,230** | $27.994 | **3,042.8 MW** | 3,629.2 | 4,329.9 | **+700.7 MW** | 0.856 |

Three things this establishes before any LP:

1. **The keeper's cheap-hour import mean reproduces at 3,042.8 MW**, i.e. the 3,043 MW the
   miso-225 scorer measured. The frozen bar's baseline is the same object.
2. **The static prediction is +700.7 MW over the frozen hour set.** The frozen +150 MW bar is
   therefore **0.214×** the static — *below* the 0.27× / 0.39× conversion ratios miso-224 and
   miso-225 each measured on their dispatch legs. The bar is reachable on this arm's own
   arithmetic, which is what makes it a discriminating test rather than a formality. **The bar
   is not moved**: it is re-used at 150 MW exactly.
3. **The overlay's EXPORT leg is structurally inert, measured not assumed.** An export band
   clears only when the bus price is *below* it; the 2023 PJM export rungs are $11.72–12.34
   (incumbent) and $7.02–7.73 (neighbour) against a bus mean of $34.5, and the probe counts
   **0 hours** in which any export band is in merit under **either** ladder. So this arm is a
   pure import-side test and G-2's gross-import measurement is the whole mechanism, not a net
   of two offsetting effects.

Reported against the arm: the annual static (+534.9 MW ≈ **+4.69 TWh**) lands within 2 % of the
**≈ +4.8 TWh** miso-225 §4 attributed to the anchor by an entirely independent route (scaling
the bare-hub arm's import loss to the ruled arm's price move). Two instruments that share no
input agreeing to 2 % is evidence the anchor's magnitude is understood. It is **not** evidence
the LP will realize it — miso-225's whole lesson is that phase 0 measures levels and *infers*
response, and the LP is what adjudicates the inference.

## 2. THE ARM

```
python3 scripts/replay_keeper.py results/calibration/miso220_nonsteamlift_B \
  --out-dir results/calibration/miso226_seamalone_S \
  --years 2023 \
  --set miso_seam_neighbour_anchored_ladder=true \
  --note "miso-226 rule-29 screen: seam-alone neighbour-anchored PJM ladder, 2023"
```

**ONE armed field.** `miso_gas_marginal_commodity_pricing` and `miso_gas_variable_transport`
are **OFF** — that is the arm, not an omission. `miso_seam_measured_ladder` is already `true` in
the keeper's recipe, so the overlay has its host (the point-of-use guard added by miso-225
Addendum A raises if it ever did not). Zero new fitted scalars: the neighbour ladder is a
measured table from a frozen derive.

## 3. G-DRIFT — the audit that makes G-CTRL form 4 valid (rule 29(b)); NO CONTROL SOLVE

miso-225 audited `cbcd3d33..d1aa877f`: ALL INERT. Extended here from **its own tip `07099620`**
to HEAD **`47e306d3`** over `src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` —
**eight files, 204 insertions, 47 deletions**:

| changed file(s) | classification | reason |
|---|---|---|
| `scripts/run_calibration.py` (±2), `data/fuel/basis/miso.py` (±2) | **INERT** | pure formatter reflow of one expression each (`print_cells` ternary; `_miso_zone_hub_kind`'s `henry`/`chicago` ternary) — token-for-token identical semantics, no value or branch changed |
| `model/capacity_evolution/evolve.py` (+29/−11), `retirements.py` (+106/−29) | **INERT** | capx D78 / owner ruling Q53: the retirement screen's sector gate moves from `exempt_unit_ids` to `exit_exempt_unit_ids`. Capacity evolution is entered only by `mode="forecast"` (`runner.py::evolve_fleet`); a `mode="backcast"` 2023 run never reaches steps 0–7. The gate is additionally coerced to its default in a backcast, and the two constructions are byte-identical wherever the D57 clearing is off — which is every ISO but PJM |
| `config/scenarios.py` (±23) | **INERT** | **comment only** — the D78 narrative on the sector-gate seam. No field added, no default changed, no code line touched |
| `results/cache.py` (+20) | **INERT** | the D78 cache-epoch ledger note; documentation, not a solve path |
| `model/commitment.py` (+29/−5), `pipeline/commitment.py` (+31) | **INERT** | nyiso-201 per-unit / per-plant census inside `caiso_ra_mustoffer_min_gen`'s `screen_stats` block and the NYISO bridge's roll-up. `screen_stats` is `None` by default and is read by no floor arithmetic (`runs = kept_runs` unchanged); the roll-up is NYISO-only and log-only. MISO arms neither the CAISO RA must-offer nor the NYISO bridge |

**VERDICT: no LIVE hunk. The committed keeper is the control; no control solve is spent.**
Residual caveat carried forward unchanged from miso-223 Addendum D / miso-225 §7: the keeper was
solved with cross-year warm-start ON and `replay_keeper` pins it OFF; prices are bit-identical
under that switch and marginal-tie dispatch reshuffles ~0.003 %, inside G-4's ±1.5 TWh
inconclusive width.

**Disclosed and NOT this lane's to fix**, carried forward from miso-225 §7: `main` carries 18
pre-existing failures in the pinned-default-cache-key tests, left stale by the capx D65-B flip.
This session adds **no `ScenarioConfig` field at all**, so it cannot move the default key.

## 4. SCREEN GATES — structural, STOP-only, never gated on the target residual

Scorer `scripts/probes/_miso226_screen_gates.py`, committed in the **same push as this
document** and run once when the solve exits, never edited after (the miso-223 §2 / miso-224 §2
/ miso-225 §2 discipline: a scorer artifact is disclosed, not repaired after the fact).

Gate NAMES are **inherited from miso-225 wherever the construction is identical**, so nothing is
renamed to dodge a comparison. miso-225's **G-1** (fuel body price) and **G-3** (fuel dispatch
response) have no leg in this arm — there is no fuel mechanism — and are therefore **not
scored**; that is stated here rather than left as a silent gap.

- **S-1 config scoping — TWO LEGS, and the STOP leg is the RE-SCOPED one.** miso-225 FAILED S-1
  on a *real* fourth difference (`ccs_retrofit_vom_adder` 8.0 → 2.95, capx D65-B on `main`) that
  its own G-DRIFT had already classified inert-for-this-solve, and its FINDING §2 recorded the
  successor's obligation verbatim: *"A successor that wants S-1 to mean 'differs only in fields
  that can reach this solve' must say so in its own PRECOMMIT, before its solve."* **This is that
  declaration, made before the solve.**
  - **S-1a, IDENTITY** — miso-225's frozen form: the arm's `run_config.scenario_config` differs
    from the keeper's ONLY in `miso_seam_neighbour_anchored_ladder` (True in the arm,
    absent-or-False in the keeper), over the non-year-scoped fields. **REPORTED, not the STOP.**
  - **S-1b, REACHABILITY** — the STOP gate: as S-1a, except that a differing field is not
    substantive if it is on the **CLOSED, explicitly enumerated** exempt list below. Any other
    non-arm, non-year-scoped diff STOPS the arm. The list is an enumeration of *names*, never a
    rule that could swallow a reachable field, and it is written here before the solve:
    - **`ccs_retrofit_vom_adder`** — capx D65-B; the CCS retrofit screen is capacity-evolution
      step 2, entered only by `mode="forecast"`, inert below `ccs_retrofit_available_year` =
      2028 by construction, and unreachable by a `mode="backcast"` 2023 solve. G-DRIFT §3 above
      classifies it INERT independently.
  - Fields **absent** from the keeper's older config are listed, never counted (unchanged).
- **S-2 liveness AND isolation, on the SOLVE log** (miso-224 Addendum A's lesson, inherited): the
  2023 SOLVE log must carry the seam line naming `PJM WESTERN-BORDER DA quantiles`, **and must
  NOT carry** the `MISO gas marginal-commodity pricing (2023)` line or its transport clause — a
  seam-alone arm whose log shows the fuel repricing is not the arm this document pre-registered.
  The winter-shape line is **REPORTED, not gated**: with the fuel arm off it is the keeper's own
  behaviour, and this session holds no keeper solve log to compare against. Else STOP.
- **G-2 seam direction & footprint — THE PRIMARY GATE, FROZEN VERBATIM FROM miso-225 §5.** Annual
  gross imports RISE against the keeper, **and** in the 1,230 real sub-$20 hours mean gross
  imports rise by **≥ +150 MW** against the keeper's 3,043 MW. Threshold, hour set and
  measurement (the `import` class of the committed `class_hourly` sidecar) are unchanged to the
  digit. Wrong direction, or short of the bar ⇒ **STOP**.
  *Why this is not a residual gate:* it asks whether the mechanism moves imports in the direction
  its own arithmetic requires (every band cheaper ⇒ more imports clear), not whether imports land
  closer to the measured 4,890 MW. `import` is not a C1 cell. The static prediction (+700.7 MW)
  and the realized fraction are **reported**, never used as a threshold.
- **G-4 no non-target load-bearing flip — construction and bands UNCHANGED from miso-225 §5.** No
  2023 C1 class flips PASS → FAIL, scored by DELTA TRANSFER from the sidecars against the
  committed `classFull` actuals and the verdict's own band (8.0 TWh, share ±3 pp). A miss within
  **±1.5 TWh** of the band edge is INCONCLUSIVE, not a kill. **C2 is UNSCORED ex ante** (a
  single-year replay writes no `metrics.json`). C3a/C3b/C3c are the target family: reported,
  never gated.
- **G-5 footprint confinement — NEW, and it belongs to this arm.** Two legs, both STOP:
  - **(a) concentration.** Phase 0 partitions the year at the keeper's own bus price into hours
    where at least one PJM import band crosses merit status and hours where none does; in the
    latter the mechanism's arithmetic predicts **no import change at all**. The bar is
    directional and untunable: **mean import Δ in the re-merit hours must strictly exceed the
    mean in the zero-re-merit hours.**
  - **(b) slack/dump.** |Δ slack| and |Δ dump| ≤ **0.01 TWh** each — the change is real dispatch,
    not an infeasibility being repriced.
- **PRICE — computed and REPORTED, never gated.** Body / tail / annual load-weighted deltas, in
  miso-225's G-1 construction. In *this* arm a price move is the **consequence** of the import
  response being measured, not an exogenous driver, so gating on it would gate the screen on its
  own target residual — which rule 29 forbids and which would also make a *successful* arm
  killable for succeeding.

**NAMED EX ANTE AS THE LIKELIEST KILL — G-2 itself, on the conversion fraction.** The static says
+700.7 MW and the bar is +150 MW, so the arm dies iff the LP converts under **0.214×**. Both
predecessors converted their dispatch legs at 0.27× and 0.275× (coal) / 0.394× (gas) — above the
line — but neither of those was an *import* response, and imports face something the thermal
legs do not: the seam's measured deliverability envelope already derates every band by
cap/limit (0.90 in the G-2 hours), the other two seams and the internal fleet re-clear against a
price that will itself fall as imports rise, and that self-limiting feedback is exactly the
"responsiveness" defect miso-225 §4 identified. **A second, structurally different kill is
therefore live and named here: the arm raises imports but the induced price fall claws part of
it back, landing between 0 and +150 MW.** If that happens the finding is that the neighbour
anchor's level change is *real but self-limiting* — a statement about the ladder's fixed-price
form, not about the owner's ruling — and the successor object is a ladder whose bands respond to
the neighbour's price *hourly* rather than through a frozen annual quantile. That is a
prediction, not a target, and no band below moves on it.

## 5. REPORTED AGAINST THE ARM, BEFORE IT RUNS

- **A cheap-import rise makes C3a-2023 WORSE, and that is not a reason to reject it** (rule 1
  `[R-STRUCT]`). +150–700 MW of sub-ladder imports displaces marginal gas and pulls the body
  price down, reducing the positive-body / negative-tail cancellation that makes C3a-2023 pass
  today — the same direction miso-225 §6 disclosed for its fuel arm. **This document does not
  propose the arm as a keeper and no promotion is contemplated in this session.**
- **The seam repair is PARTIAL by construction**, unchanged from miso-225 §6: SPP and South keep
  the incumbent MISO-hub anchor because no measured SPP or SOCO/TVA price series exists under
  `data/raw` (rule 14's misalignment clause, stated at the gate). If the cheap-hour deficit only
  half closes, that is the expected result, not a refutation.
- **The measured deficit this is aimed at is 4,890 MW** (EIA-930, the real sub-$20 hours) against
  the keeper's 3,043. Even the full static +700.7 MW closes under 40 % of it. **Clearing G-2 is
  not "solving the seam"**, and this document will not be read as claiming otherwise.
- **ST_GAS is on watch.** miso-225 §3.2 measured it moving 3.35 TWh AWAY from actual under the
  fuel arm. It carries no fuel change here, but it is a marginal class that cheap imports
  displace first, so its C1 cell is the one to read in G-4 whatever the verdict.
- **The static instrument's own weakest point, stated first.** It clears bands against the
  keeper's `MISO_external` bus price with demand and every other row FIXED. It therefore ignores
  the price feedback named in §4, the SPP/South/Manitoba seams' own re-clearing, and storage. It
  is an upper bound on the LP's response and is used as one.

## 6. Governance

Rule 1 `[R-STRUCT]`: structure first — no offer-curve multiplier is touched, no scalar is
minted, and the mechanism was not selected against a residual (it was selected by the queue
head, and its gate is its own arithmetic). Rule 13 `[R-MEASURED]`: the neighbour ladder is a
reproducible market quantity with an exact forward analogue (it re-derives from the extending
EIA-930 + border-LMP record, with the pooled 2023–2025 ladder as the forward story). Rule 14
`[R-ACCURATE]`: the SPP/South gap is stated, never proxied. Rule 19 `[R-ONE-MECH]`: the overlay
supersedes the incumbent PJM ladder per seam, never stacks on it. Rule 22 `[R-HOLDOUT]`: 2023
only, one LP. Rule 23: the ladder's derive is frozen and cites its source data. Rule 25
`[R-ISO-SCOPE]`: MISO-scoped; no other ISO's file is touched. Rule 27 `[R-PUSH]`: every source
file is edited locally and pushed as on-disk bytes, with each ≥300-line blob verified on the
remote after its push. Rule 28: the mechanism's matrix row already exists (minted by miso-225);
this session updates the MISO cell only. Rule 29: zero-LP phase 0 first, one screen year, gates
structural and STOP-only, scorer committed blind, keeper as control via G-DRIFT, bundle deleted
before merge. **DOF ledger unchanged at 41/2: zero fitted scalars minted, and no `ScenarioConfig`
field is added.**

**The screen year is 2023**, unchanged from miso-224/225 and named here before the screen runs.
For this mechanism it is the year of the largest measured footprint on every column phase 0
carries: the largest band displacement (bands 1–4 mean **−$3.81** vs −$3.03 / −$2.32), the
largest share of MISO sub-$20 hours in which the PJM border is the cheaper of the two
(**85.4 %** vs 80.0 / 74.0), and the largest measured cheap-hour seam flow (**6,021 MW** vs
4,683 / 4,485). Disclosed: 2023 also carries the largest body residual; the choice is by the
footprint columns, and it is 2023 on every one of them.

Memory recipe (`FINDING-miso169` §3): 8 GB swapfile created and confirmed live from a separate
call (`/proc/swaps`); `MARKET_SIM_HIGHS_THREADS=4`; pins numpy 2.4.6 / scipy 1.17.1 /
pandas 3.0.3 / pyarrow 24.0.0 / highspy 1.14.0 / openpyxl.
