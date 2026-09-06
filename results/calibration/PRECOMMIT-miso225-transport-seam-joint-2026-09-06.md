# PRECOMMIT miso-225 — THE OWNER RULED, AND PHASE 0 SOURCED WHAT THE RULING REQUIRED: gas at marginal commodity **plus measured variable transport**, screened JOINTLY with the neighbour-anchored PJM seam ladder on 2023. The coal self-commitment floor is REFUSED at phase 0.

**Keeper `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the single
ledgered caveat. This document is committed and pushed BEFORE the solve. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; ONE LP (2023). Rule 29 `[R-SCREEN]`: the screen bundle is a
throwaway diagnostic probe — never registered, never a keeper, and **deleted before this PR
merges** (clause (c), owner ruling R-AV). Every number this session will ever cite from it
lives in this document or in the FINDING.

## 0. THE TWO RULINGS THIS SESSION OPENED WITH

The miso-224 queue head made an owner ruling the precondition for any LP. Both were put and
both were answered at the top of this session.

1. **The fuel convention** (miso-212 §8, miso-224 §5) — *does MISO price gas at marginal
   commodity or at the EIA-923 average print?* **RULED: marginal commodity, but the offer is
   hub commodity PLUS VARIABLE TRANSPORT — not the bare hub miso-224 screened.** Owner's
   words, recorded verbatim as the option they selected: *"the only form that drops the demand
   charges / contracted-transport amortization (the actual defect) without also dropping the
   real variable delivery cost."* **Conditioned**: *"Needs a measured variable-transport
   component sourced before it is armed (zero fitted scalars, or the arm does not run)."*
2. **The seam object** (D-2 5(i), admissibility outstanding since miso-178) — **RULED
   ADMISSIBLE in one form only: reprice on the NEIGHBOUR.** *"Imports offered at the exporting
   market's own measured price … so that an import's merit position depends on the neighbour's
   supply cost, which is the real driver."* Explicitly *not* the miso-181 coincident-peak
   envelope (adjudicated `R`) and not flow-pinning.

Everything below is phase 0 under those two rulings. **No LP has been solved.**

## 1. THE RULING'S CONDITION IS MET — the variable transport is SOURCED, and it is measured

### 1.1 The identification

A plant's EIA-923 monthly print is its AVERAGE delivered cost: the commodity plus every charge
it paid, over that month's takes. Split it the way the tariff is split:

> `print[p,m] − hub[p,m] = v[p] + F[p] / burn[p,m]`

`v[p]` is the VOLUME-INVARIANT wedge over the traded hub — the usage (commodity) charge, fuel
retention and delivery-point basis paid on the **next** MMBtu. That is the ruling's variable
transport. `F[p]` is the month's FIXED charge in dollars — the reservation/demand charges a
dispatch offer must not carry. Estimator: WLS of the wedge on `1/burn` over the plant's own
2023–2025 months, weight = `burn`. The weight is not a convenience — a month's print is itself
the volume-weighted mean price of that month's deliveries, so its variance scales as `1/burn`
and `burn` is the efficient weight; it also makes the pooled fallback rungs mean the cost of a
pooled MMBtu rather than of an average plant-month. **One value per plant across every scored
year** (rule 1 `[R-STRUCT]` condition (b)); the unweighted OLS value ships alongside every row
so the choice is auditable. Frozen derive, rule 23 `[R-FROZEN-DERIVE]`:
`scripts/data/derive_miso_gas_variable_transport.py` → `data/raw/reference/
miso_gas_variable_transport.csv` (+ `.pool.csv`). **Zero fitted scalars; nothing swept.**

### 1.2 Why it IS identified, stated before the arm runs

| check | measurement |
|---|---|
| burn spread within a plant (max/min, p25/p50/p75) | **8.5 / 38.7 / 293.3×** — the intercept and slope are separately identified; the low per-plant R² (0.03–0.24 by class) is noise in a self-reported print, not a lack of spread |
| an independent, REGRESSION-FREE estimator | the plant's own top-burn-quartile burn-weighted wedge, which amortizes **79 %** of the fitted fixed leg away (cap-wtd $1.114 → $0.231/MMBtu) |
| do the two agree? | **r = 0.975** fleet-wide; CC_REGULAR top-quartile $0.386 = `v` $0.213 + its OWN measured residual fixed leg $0.173 |
| is the print really an AVERAGE and not a marginal cost? | month-over-month, the slope of d(wedge) on d(hub) is **−0.69 fleet-wide, −0.76 for CC_REGULAR** (a perfectly lagged average implies −1; a hub-tracking marginal cost implies 0), and the wedge LEVEL is uncorrelated with the hub level (r = −0.02) |

The regression is primary because it removes the fixed leg by construction; the top-quartile is
the cross-check. Records: `_miso225_transport_id.json`, `_miso225_wedge_anatomy.json`.

### 1.3 What it measures — and how much SMALLER the ruled arm is than miso-224's

Capacity-weighted, from the committed table:

| class | MW | wedge over hub | **v (WLS)** | v (OLS) | v (top-q) | share of the wedge the ruled arm DROPS |
|---|---:|---:|---:|---:|---:|---:|
| **CC_REGULAR** (the margin-setting class) | 24,695 | 0.452 | **0.209** | 0.236 | 0.385 | **54 %** |
| CT_PEAKER | 14,022 | 2.118 | 1.441 | 1.738 | 1.725 | 32 % |
| ST_GAS | 6,695 | 1.860 | 1.288 | 1.517 | 1.360 | 31 % |
| ST_CHP | 894 | 1.713 | 0.754 | 0.935 | 1.526 | 56 % |
| CT_CHP | 254 | 0.123 | −0.137 | −0.152 | 0.072 | — |
| **fleet** | 46,560 | 1.179 | **0.744** | 0.884 | 0.949 | **37 %** |

**The bare-hub arm dropped 100 % of that wedge. The ruled arm drops 54 % of it on the class
that sets the price.** 19 plants / 14.5 GW carry a NEGATIVE `v` and are **not clipped**: the
MidCon zones are priced off the Chicago series by the documented rule-14 reconciliation in the
applier, and a MidCon plant really does buy under the Chicago index. Coverage: 102 of 366 MISO
gas plants (70.0 % of gas nameplate) hold any EIA-923 gas receipt, so the declared ladder
**own → (zone,class) → class → MISO-wide** is load-bearing and mirrors the print path's own
pooling.

### 1.4 Reported against the ruling, from its own evidence base

MISO's own market monitor computes its marginal-cost benchmark on the **bare traded hub with no
transport adder**: *"a daily implied heat rate based on the daily average SMP divided by the
daily maximum gas price between Chicago Citygate and the Henry Hub"* (2024 MISO SOM Appendix
p.14; Figure A4 "MISO Fuel Prices" plots Henry Hub and Chicago Citygate and nothing else). That
is evidence FOR the miso-224 form and it is recorded here rather than omitted. It does not
override the ruling — the IMM's implied heat rate is a system diagnostic, not a per-unit
reference level — and the ruling is the stricter, more conservative reading of the same
convention. The owner ruled; this session builds what was ruled.

## 2. THE COAL SELF-COMMITMENT FLOOR IS REFUSED AT PHASE 0 (rule 19 `[R-ONE-MECH]`)

The queue head asked for a coal self-commitment floor with a window, a driver and a forward
story, screened jointly. Phase 0 refuses it, on the keeper's own committed evidence, at zero
LP cost — which is what rule 29 clause 0 exists for.

1. **The phenomenon is already represented, and in a BETTER form.** miso-53 adjudicated exactly
   this question in 2026-07 (`docs/handoffs/miso-coal-offer-som-redesign-2026-07.md` §3): the
   per-plant CAMPD `_mustrun` fuel-free price-taker band **is** the realized self-commitment
   floor at plant granularity, and replacing 44 measured per-plant floors with one fleet-level
   SOM start-share *"would lose measured granularity (rule 14) and manufacture a floor level no
   real unit operates at"*. Measured now: the MISO COAL band is **29.3 % cap-weighted**, sourced
   from CAMPD conduct at **44 of 57** plants, with **17 plants at exactly 0 %** — the
   economically-offered cyclers the SOM's own merchant column describes. A self-committed unit
   really does bid as a price taker; it is not pinned by a `min_gen` floor. The offer-side
   representation is the structurally faithful one.
2. **There is almost nothing to reconcile against, and a new floor would create the problem it
   is meant to fix.** The keeper's committed `legitimacy_diagnostics.json` D-2 attribution puts
   MISO COAL forced energy at **0.5475 / 0.5749 / 0.3575 TWh = 0.30 % / 0.34 % / 0.17 %** of a
   182.5 / 170.0 / 204.6 TWh class, one mechanism (`reliability_floor`), verdict `pass` in all
   three years. Coal is held in merit by ECONOMICS. A self-commitment `min_gen` floor sized to
   the IMM's must-run share would take a material class from 0.3 % forced toward the C8 30 %
   budget and owe a D-4 window it does not have.
3. **The exposure that motivated re-opening it is halved by §1 anyway** (§4.2 below).

**The driver is real and is now in the repo as data, not as a floor.** The 2025 MISO SOM
published since miso-53 — which named its publication as the rule-23 re-derive trigger — is
intaken this session into the `som-competitive-conduct` datatype (12 new MISO-2025 rows;
source PDF verified byte-exact against the committed `SHA256SUMS.txt`,
`a179e31a…398aec06`). Regulated-utility coal starts, must-run share (profitable + not):
**56 % (2023) / 53 % (2024) / 61 % (2025)**; merchant **7 % / 25 % / 24 %**; regulated net
revenue $5.75 / $8.01 / $17.43 per MWh; system price-cost mark-up +3.0 % / −2.5 % / **−1.07 %**;
output gap 0.10 % / 0.06 % / **0.08 %** of load. Intaking the evidence is not the same as
building a second mechanism on it, and this session does the first only.

## 3. THE SEAM LEG PASSED ITS OWN PRE-SOLVE GATE

`_miso225_seam_neighbour_phase0.py`, zero-LP. The incumbent `miso_seam_measured_ladder` prices
every band at a quantile of **MISO's OWN** DA hub, so an import's merit position moves with the
model's price and imports CONTRACT when MISO clears cheaply. The measured market does the
opposite, and the number is unambiguous:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| PJM-seam import band 1–4, neighbour anchor − incumbent | **−$3.81** | **−$3.03** | **−$2.32** |
| in MISO's sub-$20 hours: MISO DA vs PJM border | $17.51 / $15.22 | $17.23 / $15.11 | $18.83 / $18.13 |
| … PJM the cheaper of the two, share of those hours | **85.4 %** | 80.0 % | 74.0 % |
| **measured seam import in those hours** | **6,021 MW** | 4,683 | 4,485 |
| measured seam import, all hours | 4,674 MW | 3,678 | 3,199 |
| corr(PJM border, MISO DA) | 0.809 | 0.869 | 0.883 |

**MISO imports MOST when it is cheapest** — 6,021 MW against a 4,674 MW all-hours mean in 2023 —
because the neighbour is cheaper still. A ladder anchored on MISO's own falling price cannot
represent that; the neighbour anchor lowers every band in every year, in the required
direction. The 0.81–0.88 correlation says the repricing is neither cosmetic nor a second copy
of MISO's own signal. **PJM only**: no measured SPP or SOCO/TVA price series exists under
`data/raw`, so those seams keep the incumbent anchor — a DATA boundary stated at the gate
(rule 14's misalignment clause), not a choice.

## 4. THE ARM, and the screen year

Two new `ScenarioConfig` fields, both default off, both byte-identical off, both **REFUSED at
construction** when armed without the mechanism they overlay (fail-closed, never a silent
no-op):

* **`miso_gas_variable_transport`** — requires `miso_gas_marginal_commodity_pricing` (rule 19:
  a transport adder on top of the average print double-counts the transport that print already
  amortizes). Adds each gas row's `v[p]` to its zone's daily hub. MISO-scoped through that
  flag's own rule-25 guard.
* **`miso_seam_neighbour_anchored_ladder`** — requires `miso_seam_measured_ladder` (there is
  nothing to overlay otherwise). Overlays `MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR["PJM"]`, derived
  by `derive_miso_seam_ladders.py::derive_pjm_neighbour` — the identical Q-Q construction read
  off the PJM western-border DA. Per seam and per year: an absent seam falls through untouched.

Matrix rows minted with the fields (rule 28c). Ledger: **zero new fitted scalars**; `v[p]` is a
measured table, the ladder a measured table. Applied by
`replay_keeper --set miso_gas_variable_transport=true --set
miso_gas_marginal_commodity_pricing=true --set miso_seam_neighbour_anchored_ladder=true`.

**SCREEN YEAR = 2023**, unchanged from miso-224 and named here before the screen runs. It is
the year the fuel mechanism's own measured footprint is largest — the fuel-convention layer at
the marginal tranche in body hours, **$4.68 (2023) > $3.44 (2024) > $3.25 (2025)** — and it is
also the seam mechanism's largest band displacement (−$3.81 > −$3.03 > −$2.32) and its largest
cheap-hour import deficit. Disclosed: 2023 also carries the largest body residual; the choice
is by the footprint columns, and it is 2023 on every one of them. It is **not** 2025, the
largest-|C3a| and largest-tail year.

**JOINT, per the queue head, and separable by construction.** The two mechanisms aim at
different observables — the fuel arm at the body PRICE, the seam arm at import MW in the cheap
hours — so G-3's legs below are pre-registered per mechanism and attribution survives the join.

### 4.2 The pre-solve arithmetic (`_miso225_static_remerit.json`, 2023, zero-LP)

miso-224's own static-clearing instrument, re-run on the ruled offer basis. Transport applied
to 1,448 gas rows, mean **+$0.704/MMBtu** (cap-wtd +0.708, range −0.718…+12.926).

| hour set | dP bare hub (miso-224) | **dP RULED** | ruled share | coal ΔMW bare | **coal ΔMW ruled** | gas ΔMW ruled |
|---|---:|---:|---:|---:|---:|---:|
| body (bottom 90 %) | −6.724 | **−2.976** | 0.443 | −3,391 | **−1,346** | +1,379 |
| tail (top 10 %) | −13.61 | −7.295 | 0.536 | −2,515 | −922 | +990 |
| real hub < $20 (n=1,230) | −4.913 | **−1.941** | 0.395 | −2,919 | **−1,470** | +1,483 |
| MEC d1 / d5 / d9 | −4.84 / −6.80 / −10.18 | −1.93 / −3.21 / −4.87 | 0.40 / 0.47 / 0.48 | −2,188 / −4,020 / −2,596 | −1,257 / −1,534 / −842 | +1,262 / +1,574 / +892 |

## 5. SCREEN GATES — structural, STOP-only, never gated on the target residual

Scorer `scripts/probes/_miso225_screen_gates.py`, committed in the same push as this document
and run once when the solve exits, never edited after (the miso-223 §2 / miso-224 §2
discipline: a scorer artifact is disclosed, not repaired after the fact).

- **S-1 single delta.** The arm's `run_config.scenario_config` differs from the keeper's ONLY
  in the three armed fields, scoped as miso-224 §2's successor prescribed — **each arm field is
  `True` in the arm and absent-or-`False` in the keeper** — over the non-year-scoped fields
  (`weather_year`, `gas_price_override`, `start_year`/`end_year`/`year(s)` excluded ex ante).
  Fields absent from the keeper's older config are listed, not counted. Else STOP.
- **S-2 liveness, on the SOLVE log** (miso-224 Addendum A's lesson, which this session inherits
  rather than relearns): the 2023 SOLVE log carries the marginal-commodity line **with the
  `PLUS the derived per-plant variable transport` clause**, the winter-shape line is ABSENT,
  and the seam line names `PJM WESTERN-BORDER DA quantiles`. Else STOP.
- **G-1 fuel-arm direction & magnitude.** MISO-Indiana mean price over the keeper's OWN 2023
  body hours falls by **$1.49–$4.46** — 0.5×–1.5× the static prediction of **−$2.976**. Outside
  the band ⇒ the mechanism does not do what its arithmetic says ⇒ STOP.
- **G-2 seam-arm direction & footprint.** Annual gross imports RISE against the keeper, and in
  the 1,230 real sub-$20 hours mean imports rise by **≥ +150 MW** against the keeper's 3.23 GW.
  (Every PJM import band is $2.3–4.6 cheaper, so an economically-clearing ladder must import
  more; a fall is the mechanism doing the opposite of its arithmetic.) Wrong direction ⇒ STOP.
- **G-3 dispatch response, fuel leg.** In the 1,230 hours INDIANA.HUB cleared below $20, the arm
  moves coal DOWN and gas UP against the keeper by at least **0.3×** the ruled static
  prediction: coal Δ ≤ **−441 MW** and gas Δ ≥ **+445 MW**. Wrong direction or below the
  fraction ⇒ STOP.
- **G-4 no non-target load-bearing flip.** No 2023 C1 class flips PASS → FAIL, scored by DELTA
  TRANSFER from the sidecars against the committed `classFull` actuals and the verdict's own
  band (8.0 TWh, share ±3 pp), exactly as miso-224 §5 defined it. A miss within **±1.5 TWh** of
  the band edge is INCONCLUSIVE, not a kill (the per-class transfer is approximate). **C2 is
  UNSCORED ex ante.** C3a/C3b/C3c are the target family: reported, never gated.

**NAMED EX ANTE AS THE LIKELIEST KILL — G-4 on COAL_PRB.** The ruled static displaces about
**−1.3 GW** of coal on the body mean against the bare arm's −3.4 GW. miso-224's LP converted
its static at 0.27×, and realized COAL_PRB **−1.56 → −11.88 TWh** (a flip) and CC_REGULAR
**−4.17 → +12.60** (a flip). At 44 % of the fuel move the same conversion lands COAL_PRB near
**−6 to −7 TWh** and CC_REGULAR near **+1 to +4** — both inside ±8.0, COAL_PRB with perhaps
1–2 TWh of headroom. **That is a prediction, not a target**: if COAL_PRB flips, the arm is
killed on the screen and the finding is that the transport measurement does not shrink the
displacement enough, which is a structural result about the fuel convention and not a reason to
re-tune anything. Second exposure: **CT_PEAKER-2023**, the miso-220 keeper's fragile edge at
**−7.985 against ±8.00, 0.015 TWh of headroom** — the arm makes CTs dearer relative to the bare
form (their `v` is $1.44/MMBtu, the largest of any material class), so this cell can flip on a
small move in EITHER direction and is named here before it is scored.

## 6. REPORTED AGAINST THE ARM, BEFORE IT RUNS — and what this screen cannot license

- **C3a will get worse in 2023 and that is not a reason to reject it** (rule 1 `[R-STRUCT]`).
  Static: the body falls $2.98 and the tail $7.30, so C3a-2023 moves from **+7.15 %** toward
  about **−1 %**, and the cancellation that makes C3a pass today (positive body against a
  negative tail) is reduced. The tail deficit the reserve/ORDC family owns (miso-219/221/222)
  is exposed further. **This document does not propose the arm as a keeper**, and no promotion
  is contemplated in this session.
- **The seam repair is PARTIAL by construction.** SPP and South keep the incumbent MISO-hub
  anchor. If the cheap-hour import deficit only half closes, that is the expected result, not a
  refutation.
- **The transport measurement's own weakest point, stated first.** Per-plant R² is 0.03–0.24.
  The intercept is nonetheless identified (§1.2 burn spread) and confirmed by a regression-free
  estimator at r = 0.975, but a reader should know the fit is loose and that 30 % of gas
  nameplate takes a pooled rung rather than its own value.
- **Rule 29(2) is narrowed here ex ante, exactly as miso-224 narrowed it**: screen → (owner, if
  the screen clears) → full span. A cleared screen is NOT a licence to spend 2024/2025 or to
  promote.
- The screen bundle `results/calibration/miso225_ruled_S` is never registered and is **deleted
  before the PR merges** (rule 29(c)).

## 7. G-DRIFT — the audit that makes G-CTRL form 4 valid (rule 29(b)); NO CONTROL SOLVE

miso-224 audited `b3fb0edc..cd2f1ed8`: ALL INERT. Extended here from its tip `cbcd3d33` to HEAD
`d1aa877f` over `src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` — seven files, **511 insertions,
22 deletions**, this session's own diff excluded:

| changed file(s) | classification | reason |
|---|---|---|
| `config/capacity_market.py` (+62), `data/avoidable_cost_rate.py` (+33), `model/capacity_evolution/{evolve,retirements}.py` (+68), `config/constants.py` (+2 imports) | **INERT** | capacity-market accreditation / capacity-evolution, entered only by `mode="forecast"`; a backcast solve never reaches step 0–7 |
| `config/scenarios.py` (+310) | **INERT** | capx D65-B: `ccs_retrofit_vom_adder` 8.0 → 2.95 and `ccs_retrofit_fixed_cost_co2_scaling` default flip (CCS retrofit is inert below `ccs_retrofit_available_year` = 2028, and is a forecast-mode capacity-evolution step), plus `capacity_no_default_cap_convention_by_iso` (capacity market) |
| `results/cache.py` (+58) | **INERT** | the D65-B cache-key epoch note; documentation of the flip, not a solve path |
| **this session's own diff** | **INERT for the control** | both fields default off and REFUSED without their host mechanism; the off path is byte-identical, verified by `tests/unit/data/test_fuel.py::test_miso_gas_variable_transport_off_is_byte_identical` and `tests/iso/miso/test_miso_seam_ladder.py::TestNeighbourAnchoredOverlay::test_off_is_byte_identical` (277 passed) |

**VERDICT: no LIVE hunk. The committed keeper is the control; no control solve is spent.**
Residual caveat carried forward from miso-223 Addendum D: the keeper was solved with cross-year
warm-start ON and `replay_keeper` pins it OFF; prices are bit-identical under that switch and
marginal-tie dispatch reshuffles ~0.003 %, inside G-4's ±1.5 TWh inconclusive width.

**Disclosed, and NOT this lane's to fix:** `main` at `d1aa877f` carries **18 pre-existing
failures** in the pinned-default-cache-key tests (`test_smr_available_year`,
`test_vre_procurement_ffr5e`, and 16 siblings), reproduced identically at HEAD with this
session's changes stashed. This session's own additions do **not** move the default key: both
fields are registered in `_CACHE_KEY_OPTIONAL_FIELDS` and `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`
in the same commit as the fields (the nyiso-119 discipline), and the hashed payload of
`ScenarioConfig()` is **byte-identical to HEAD's** (diffed directly, empty). The pins look to
have been left stale by the capx D65-B flip; that is the capx lane's call, not a MISO edit.

## 8. Governance

Rule 1 `[R-STRUCT]`: structure first — no offer-curve multiplier is touched, no scalar is
minted, and neither mechanism was selected against a residual. Rule 13 `[R-MEASURED]`: both
inputs are reproducible market quantities with exact forward analogues (the transport
re-identifies from the then-current EIA-923 vintage and rides the forward hub; the neighbour
ladder re-derives from the extending EIA-930 + border-LMP record, with the pooled 2023–2025
ladder as the forward story). Rule 14 `[R-ACCURATE]`: the misalignment clause, documented in
the derive and the applier docstrings; the SPP/South gap is stated rather than proxied. Rule 19
`[R-ONE-MECH]`: supersede, never stack — the transport is refused on top of the print, the
neighbour ladder is an overlay on one ladder, and the coal floor is refused outright (§2).
Rule 22 `[R-HOLDOUT]`: 2023 only, one LP. Rule 23: two frozen derives, both citing their source
data. Rule 25 `[R-ISO-SCOPE]`: MISO-scoped; no other ISO's file is touched. Rule 26
`[R-DELETE]`: nothing deprecated is left parseable. Rule 27 `[R-PUSH]`: every source file was
edited locally and pushed as on-disk bytes, with each ≥300-line blob verified on the remote
after its push. Rule 28: rows minted with the fields, cells stamped in this session. Rule 29:
zero-LP phase 0 first (it killed one of the three legs before any solve), one screen year named
from the footprint, structural STOP-only gates, scorer committed blind, keeper as control via
G-DRIFT, bundle deleted before merge. DOF ledger unchanged at **41/2**.

Memory recipe (`FINDING-miso169` §3): 8 GB swapfile created and confirmed live from a separate
call (`/proc/swaps`, 8,388,604 kB); `MARKET_SIM_HIGHS_THREADS=4`; pins numpy 2.4.6 / scipy
1.17.1 / pandas 3.0.3 / pyarrow 24.0.0 / highspy 1.14.0 / openpyxl.

---

## ADDENDUM A (written before ANY gate was scored and before any arm output was read) — the first screen solved BOTH passes and then died in post-solve bookkeeping, on a guard of MY OWN that was at the wrong layer

**No band, kill condition, gate or pre-registered value in §5 changes.** The scorer
`_miso225_screen_gates.py` is untouched. What follows is a code repair and its disclosure.

### What happened

The first 2023 launch ran to completion — **P0 cold 304.2 s / 383,621 simplex iterations, P1
warm 189.1 s / 235,082 iterations, results written (sidecars 19.1 s), peak RSS 13.27 GB with
the swapfile untouched** — and then raised in `run_calibration_full.solve_and_persist` →
`_recorded_config`, before `run_config.json` existed:

> `ValueError: ScenarioConfig.miso_seam_neighbour_anchored_ladder requires
> miso_seam_measured_ladder`

**Both liveness lines had already fired correctly in the SOLVE log**, which is what makes the
diagnosis unambiguous: `MISO gas marginal-commodity pricing (2023): 1487 gas units repriced …
PLUS the derived per-plant variable transport (−0.718..+12.926, mean +0.716 $/MMBtu)` and
`seam bands repriced … PJM WESTERN-BORDER DA quantiles on the PJM seam (miso-225
neighbour-anchored), MISO DA hub quantiles on SPP/South`. The LP solved the intended arm. The
failure was downstream of it.

### The cause — my own defect, and it is a LAYER error, not a typo

`miso_seam_measured_ladder` is a **`solve_and_persist` kwarg**, applied to the recorded config
at `run_calibration_full.py:4888`; the `--set` fields land in the base `backcast_config` far
earlier. `_recorded_config` rebuilds the as-solved config through a long chain of
`with_overrides`, and `dataclasses.replace` re-runs `__post_init__` on **every intermediate
config in that chain** — so the pair is legitimately SPLIT part-way through even though the
final config is well formed. My §4 cross-field validators were in `__post_init__`, so they
rejected a correct run after its LP had already finished.

`__post_init__` is the wrong layer for a cross-field invariant in this codebase, and the repo's
own idiom already says so: the rule-25 ISO guard and the fuel-pair guard both live in the
APPLIER, at the point of use, where the config is complete.

### The repair, all before any result was read

1. **Both `__post_init__` validators are DELETED**, not disabled (rule 26 `[R-DELETE]`), with
   the reason recorded in place so they are not "restored" as a regression fix.
2. **The fuel pair keeps its point-of-use guard**, which was always the real one:
   `apply_miso_gas_marginal_commodity` raises when transport is armed without the hub
   repricing, and that applier runs on every backcast path, so an armed-alone transport flag
   can never reach a price.
3. **The seam pair gains the equivalent guard at its point of use** — `run_calibration.py`'s
   seam block, checked on the complete as-solved config, immediately before the injection
   `if` whose condition would otherwise skip the overlay silently. Arming the overlay without
   its ladder is still a hard error; it is now raised where the config is whole.
4. Tests updated to the layer that actually holds: the fuel guard is exercised through the
   applier, and a new `TestNeighbourOverlayRequiresItsHost` asserts BOTH halves — that a split
   intermediate config constructs fine (and can still take its host via `with_overrides`,
   which is exactly what `_recorded_config` does), and that the solve path carries the
   refusal. 279 tests pass.

### What this cost and what it did not

It cost one 582-second LP. It did not cost any gate integrity: **no gate was scored, no
`_miso225_screen_gates.json` was written, and no price, dispatch or C1 number from the arm was
read** before this repair was made and committed. The partial bundle is deleted and the screen
re-run from scratch on the repaired code, so the scored bundle is one code state throughout.

**The disclosed lesson for the record**, the sibling of miso-224's Addendum A: that one found
that a fuel mechanism's LIVENESS must be asserted on the chain the solve runs. This one finds
that a mechanism's cross-field INVARIANTS must be asserted where the config is COMPLETE — a
builder chain will hand `__post_init__` states that no solve ever uses.
