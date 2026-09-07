# PRECOMMIT — pjm-169 F4: the gas-offer margin anchor is identified on 2023–2025 and applied to 2021–2022

**Session:** pjm-169 · **Date:** 2026-09-06
**Branch:** `claude/pjm-calibration-f2-f4-n6wzrr`
**Keeper (control):** `2026-08-15-pjm-162-inputclock` / `pjm_debugb_inputclock_A`
**Predecessor evidence:** `results/calibration/FINDING-pjm168-f1-f2-screens-2026-09-06.md` §1
(F1 killed by G3: given the CORRECT 2021 registry the model still runs coal to 95.0 % of its
ceiling and overshoots the metered coal peak by +3,619 MW — so the binding object is **offer
ordering**, not the registry).

Written **before any LP is solved and before the mechanism is built**, per rule 29 `[R-SCREEN]`.
Every threshold and gate below is fixed here and is **not revisable after a result is seen**.

---

## 1. The defect

`apply_gas_offer_margin` (`data/offer_curves.py`) reprices each gas band's above-physical markup
from a fuel-scaled multiplier to a **fixed $/MWh margin**:

```
mc[g,t] += markup_hr[g] × (anchor − fuel_price[g,t])
```

`anchor = constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"] = 3.3483 $/MMBtu`. It is armed in the
PJM keeper (`run_config.json`: `gas_offer_net_revenue_margin: true`,
`gas_offer_margin_anchor: 3.3483`), carried through the recipe's generic overrides channel.

**The anchor is not a tunable — it is an IDENTIFICATION POINT**, and
`scripts/data/derive_gas_offer_margin_anchor.py` says so in its own docstring:

> the mean of the model's own merit-order delivered-gas series (`_gas_series` …) over the
> **training window 2023–2025**. **At `fuel == anchor` the reformed offer reduces EXACTLY to the
> registered band multiplier**, so the anchor is the point where the multiplicative and
> fixed-margin forms are observationally equivalent — the identification point, not a tunable.

That identity is the whole basis on which the registered `offer_curve_by_group` band multipliers
remain meaningful under the reform. **It holds only near the window mean.** The term is a *linear*
extrapolation with no saturation, so as `fuel` departs from `anchor` the offer departs from the
band multiplier the ISO was calibrated with — proportionally, and without bound.

Across 2023–2025 that is a small correction, because the window's own delivered gas is what the
anchor is the mean of. **2021 and 2022 are outside it**, and 2022 is far outside: the keeper's
recorded Henry Hub scalars are 2.54 / 2.19 / 3.52 in-window against **6.45 in 2022** and 3.72 in
2021, and PJM's delivered basis adds ≈ +$0.67 on top. The sign is the operative part: when
`fuel > anchor` the term is **negative**, so the mechanism marks gas offers **DOWN** — by the most
in the year gas is dearest, which is exactly when the identification says nothing.

**This is a vintage/extrapolation defect of the same family as pjm-162's input clock**, one level
up: not a mis-dated *input*, but a *constant whose identification window does not contain the
solve year*.

## 2. The change to be built (ONE mechanism, rule 19 `[R-ONE-MECH]`)

`ScenarioConfig.gas_offer_margin_anchor_vintage: bool = False`. When armed, the anchor resolves to
the **mean of `_gas_series` for the SOLVE YEAR**, computed by the identical construction
`derive_gas_offer_margin_anchor.py` uses for the window — instead of the frozen window mean. The
resolved value is written into the recorded config exactly as the ISO anchor is today, so
`run_config.json` carries the number the LP solved with (rule 24 `[R-REGISTRY]`).

- **Zero free parameters** (rule 21 `[R-DOF]`). Nothing is fitted, chosen or swept. The formula is
  unchanged; only the year it is evaluated on moves, from a frozen 2023–2025 to the solve year.
- **Rule 13 `[R-MEASURED]` admissible.** The admissibility test is *"could this same quantity be
  produced for a forward year from forward drivers, and would it respond to changed conditions?"*
  Yes on both counts: a forecast year's anchor is the mean of that year's own forecast gas
  trajectory, and it moves when the trajectory moves. It is not a measured **outcome**: no price,
  no residual and no actual dispatch is read.
- **It is NOT the rule 1 `[R-STRUCT]` offer-curve carve-out and does not touch it.** The band
  multipliers (`committed` / `econ_low` / `econ_high` / `peak`) are untouched, in every year. This
  restores the condition under which those registered multipliers mean what they were calibrated
  to mean; it does not retune them.
- **It is not per-year fitting.** Rule 1(b)'s "ONE config across EVERY scored year" binds the
  *config*, and the config here is one boolean and one formula, identical in every year. The
  quantity that varies by year is a **measured fuel level** — the same class of object as
  `gas_prices` itself, which every keeper already carries per year.
- **In-sample it is NOT expected to be inert**, and that is declared here rather than discovered:
  the window mean is not equal to any single in-window year's mean. Whatever it does to
  2023–2025 is a cost this hypothesis must carry openly, and gate S5 below is what measures it.

## 3. Phase 0 — the zero-LP footprint census (rule 29 clause 0), and the screen year

`scripts/probes/_pjm169_f4_window_footprint.py` measures, per year, on the keeper's own resolved
config and with no LP: the delivered gas series `_gas_series` the offer path prices against, the
anchor gap `anchor − fuel` (mean and abs-max), and — as a **confound check only** — the resolved
gas-keyed coal passthrough sigmoid and how much of each year sits on its `ceil` asymptote.

**The screen year is chosen on FOOTPRINT — the largest measured `|anchor − fuel|` — and never on
any residual** (rule 29). On the constants alone the answer is already 2022 and not close: the
in-window abs-max gap is `|3.3483 − 2.19| = 1.158 $/MMBtu`, against `|3.3483 − 6.45| = 3.102` on
the 2022 Henry Hub scalar before basis, i.e. **≈ 2.7× the largest gap the identification window
ever saw**, and larger still on the delivered series. 2021's `|3.3483 − 3.72| = 0.372` is *inside*
the in-window range — the mechanism is near-identified there.

> **SCREEN YEAR: 2022.** Declared here, before any solve, on footprint.

The census table is appended to this document as §7 when it runs, **before** the screen is
launched. If the census contradicts the constant-level arithmetic above and names a different year
as the largest footprint, **the census wins and the screen year moves to it** — that rule is fixed
now, so the choice cannot be made after seeing a dispatch result.

### 3.1 A confound this PRECOMMIT declares in advance

The coal side carries its own window-extrapolation, and it pushes the **opposite** way. PJM
bituminous resolves `COAL_SIGMOID_DEFAULTS[("PJM","bituminous")]` = `{floor 0.65 (keeper
override), ceil 1.32, gas_mid 3.4, gas_slope 2.5}`, and that table's own docstring records the
weakness: *"each asymptote is pinned by a single gas regime — floor by the cheapest observed year,
**ceil by the dearest**"*. At in-window gas the logistic never approaches `ceil`; at 2022 delivered
gas it is **saturated on it**, so 2022 coal is priced by an asymptote no in-window observation
constrains — and `ceil > 1` marks coal **UP**.

**F4 does not touch the coal sigmoid.** It is named here so that (a) the screen's footprint gate
cannot silently attribute a coal-side move to F4, and (b) the finding is on record as its own
card rather than absorbed into this one (rule 19 `[R-ONE-MECH]`: one mechanism per phenomenon; a
second window-extrapolation gets its own PRECOMMIT, its own evidence and its own decision).

## 4. Control — G-CTRL form 4, and the G-DRIFT audit that licenses it

Per rule 29 clause (b) **no control solve is spent**: the control is the committed
`pjm_tp2022_2021_k162` touchpoint bundle's 2022, differenced against the arm. Its validity rests
on a code-level **G-DRIFT** audit — `git diff <keeper/touchpoint sha> HEAD` over the backcast solve
path, every changed hunk classified INERT-for-PJM-backcast with its reason, or LIVE. **The audit is
recorded in §8 of this document before the arm is solved.** A LIVE hunk earns a control solve for
the screen year only; all-INERT means the committed bundle is the control.

**One LIVE hunk is already known and is declared here:** this session's own F2 arm
(`pjm_interface_feed_admissibility_gate`, armed in `pipeline/backcast_config.py`) changes the 2022
solve path. The F4 screen is therefore differenced against the **re-run, F2-armed 2022 touchpoint
this session produces**, not against the pre-arm bundle — so F2 and F4 are never confounded and
the F4 screen isolates a single delta.

## 5. STOP gates — structural only, pre-registered, and a KILL rule

Every gate below asks whether the mechanism **does what its own arithmetic says it does**. Per
rule 29 the screen **may kill an arm and may never promote one**. **No gate reads C3a, C3b, or any
price residual** — a screen gated on the target residual is exactly the fitted-mechanism selection
rule 1 `[R-STRUCT]` forbids, done one year at a time.

| # | gate | pass condition (fixed here) |
|---|---|---|
| **S1** | *identity* | the 2022 resolved anchor equals the mean of that year's own `_gas_series` to within 1e-6 $/MMBtu, and the 2023/2024/2025 resolved anchors each equal their own year's mean — i.e. the mechanism computes what §2 says it computes |
| **S2** | *the identity it asserts* | in the arm, for every gas tranche, `mc` at the hour whose `fuel_price` equals the resolved anchor reduces to the registered band multiplier to within 1e-6 $/MWh — the reform's own stated identity, now holding in the solved year |
| **S3** | *direction & order of magnitude* | the arm's mean gas-tranche `mc` delta vs the control has the SIGN and lies within [0.5×, 2.0×] the MAGNITUDE that the pre-solve arithmetic `markup_hr × (anchor_arm − anchor_control)` predicts from the committed offer arrays (a pure algebraic prediction made in §7 before the solve) |
| **S4** | *footprint confined* | the mechanism claims gas tranches only. Non-gas classes (nuclear, wind, solar, hydro, biomass, coal, OTHER) each move < 1.0 % in annual energy — a larger coal move means the coal-sigmoid confound of §3.1 is in play and the screen is not isolating F4 |
| **S5** | *no non-target load-bearing flip* | C1 (`fuelmix`), C2 (`sysvol`) and C4 (`dispatch_corr`) do not go PASS → FAIL on the screen year |

**KILL RULE.** Any of S1–S5 failing kills the arm. The remaining years are then **never spent**,
the result is reported as the session's finding, and nothing is promoted. S1 or S2 failing is a
construction defect, not a market finding.

**Passing every gate promotes nothing.** It earns the full-span step (rule 16 `[R-ALLYEARS]`: one
`--year 2023 2024 2025` invocation, one bundle) and, separately, a re-run of the 2021/2022
touchpoints — which remain iterable model-SELECTION evidence and never a skill claim (rule 22).

## 6. What is out of scope

F1 (`eia860_vintage_tracks_solve_year`, adjudicated `R` — DO NOT REDO), F1b and F3 (both withdrawn
by pjm-167), and pjm-166 §7.4's "retire the coal-CC framing" recommendation (superseded by
pjm-167 §6). The coal-sigmoid `ceil` extrapolation of §3.1 is **recorded, not built** here.

## 7. Phase-0 census and the pre-solve algebraic prediction

Run before the screen, per §3. Artifact: `results/calibration/_pjm169_f4_census.json`; probe
`scripts/probes/_pjm169_f4_window_footprint.py`. Measured on the keeper's own resolved config, on
`_gas_series` — the **hourly** delivered series the offer path actually prices against.

| year | gas mean | min | max | gap mean | **gap abs-max** | ×in-window | hours gas > anchor |
|---|---|---|---|---|---|---|---|
| 2021 | 4.109 | 2.943 | 5.649 | −0.761 | 2.3006 | **0.67×** | 5,832 |
| **2022** | **7.121** | 5.089 | 9.535 | **−3.772** | **6.1870** | **1.80×** | **8,760** |
| 2023 | 3.255 | 2.314 | 4.975 | +0.093 | 1.6270 | 0.47× | 3,624 |
| 2024 | 2.856 | 2.224 | 5.066 | +0.493 | 1.7178 | 0.50× | 1,488 |
| 2025 | 3.934 | 2.655 | 6.791 | −0.586 | **3.4429** | 1.00× | 5,088 |

### 7.1 THE CENSUS CORRECTS §1 AND §3 OF THIS DOCUMENT — recorded, not quietly amended

**§3's magnitude claim was WRONG and is withdrawn.** It reasoned from the recipe's *annual Henry
Hub scalars* and asserted an in-window abs-max gap of $1.158/MMBtu and a 2022 footprint of "≈2.7×".
The identification point is defined on `_gas_series`, which is hourly and carries the monthly
EIA-923 actuals and the hub overlay, so its in-window spread is far wider: the true in-window
abs-max is **$3.4429/MMBtu (2025)**, and 2022's is **$6.1870 = 1.80×**, not 2.7×.

**What survives, and what does not:**

- **The screen year still stands at 2022, by the rule declared in §3 before any measurement** —
  largest measured footprint, 1.80× the in-window maximum, and the only year in which gas exceeds
  the anchor in **every one of 8,760 hours**. The pre-registered tie-break ("if the census names a
  different year, the census wins") did not need to fire.
- **2021 is INSIDE the identification support** (0.67×). The mechanism is *not* meaningfully
  extrapolating there, so F4 cannot be the 2021 story — which is a real narrowing of the
  hypothesis, and the handoff's framing of F4 as the 2021/2022 object is wrong for 2021.
- **The defect is smaller than §1 implied but is still real and one-directional in 2022**: the
  gap mean is −3.772 $/MMBtu across the whole year, so the mechanism marks gas offers DOWN in
  every hour of 2022, and the year sits entirely outside the sign regime the window identified
  (2023 and 2024 have positive gap means).

### 7.2 The confound of §3.1 is now QUANTIFIED, and in 2022 it is the LARGER effect

| year | PJM bit passthrough mean | max | `ceil` | **hours ON the ceiling** |
|---|---|---|---|---|
| 2021 | 1.1205 | 1.3176 | 1.320 | 16.7 % |
| **2022** | **1.3188** | 1.3200 | 1.320 | **91.5 %** |
| 2023 | 0.9166 | 1.3072 | 1.320 | **0.0 %** |
| 2024 | 0.8140 | 1.3098 | 1.320 | **0.0 %** |
| 2025 | 1.0565 | 1.3199 | 1.320 | 8.5 % |

(Sub-bituminous is identical in shape on `ceil` 2.100.) **In 2022 the PJM bituminous coal bid is
priced by its `ceil` asymptote in 91.5 % of hours — an asymptote the training window touches in
0.0 % of hours in two of its three years.** That is a *larger* and *better-evidenced* window
extrapolation than the gas anchor's 1.80×, and `ceil > 1` marks coal **UP** while the gas anchor
marks gas **DOWN**. The two corrections oppose each other, and the coal one is the bigger.

**This does not change what F4 is or what this screen does** — F4 touches only the gas anchor, and
gate **S4** exists precisely to detect the coal side moving. It does change the priority order the
session reports: **the coal-sigmoid `ceil` is now the stronger candidate for PJM's 2022 offer-order
defect**, and it is a separate card with its own PRECOMMIT, never folded into this one
(rule 19 `[R-ONE-MECH]`).

### 7.3 The S3 pre-solve algebraic prediction, fixed here before the solve

From the 2022 control solve's own log: **981 gas tranches** compressed, **median fixed margin
$9.39/MWh** at the 3.3483 anchor ⇒ median `markup_hr` = 9.39 / 3.3483 = **2.804 MMBtu/MWh**.

Arming moves the anchor to the 2022 mean of `_gas_series`, **7.121 $/MMBtu**, so:

> **Predicted median gas-tranche `mc` shift = markup_hr × (anchor_arm − anchor_control)
> = 2.804 × (7.121 − 3.3483) = +$10.58/MWh**, i.e. gas offers move **UP** — the arm REMOVES a
> downward extrapolation rather than adding a markup.

**S3 passes iff the measured mean gas-tranche `mc` delta is positive and within
[0.5×, 2.0×] of $10.58/MWh, i.e. in [$5.29, $21.16]/MWh.** Fixed here, before the solve.

*(Direction note, reported not gated: a rise in gas offers would be expected to REDUCE gas
dispatch, and 2022's live C1 failure is a CC_REGULAR OVER-run of +22.02 TWh. That the arm points
the helpful way is **not** a pass condition and no gate reads it — saying so here, in advance, is
what stops it becoming one.)*

## 8. G-DRIFT audit

**Discharged trivially, and that is the point of §4's control choice.** The control is
`results/calibration/pjm169_tp2022_2021_f2arm`'s 2022 — solved **in this session, at this HEAD,
on this branch**, with the F2 arm already live. The arm and the control therefore share their
entire solve path by construction: there is no interval between them for code to drift across,
so G-CTRL **form 4** is valid with **zero LP spent on a control** and no hunk classification is
required.

This is the LIVE-hunk case §4 anticipated, resolved by ordering rather than by a solve: the one
live hunk known in advance was this session's own F2 arm, and re-running the touchpoint first put
it on **both** sides of the comparison. The F4 screen therefore isolates a single delta — the
anchor's vintage — and F2 and F4 are never confounded.

*(The `46e08e5b` sha the superseded touchpoint bundle recorded is not resolvable on `main` — that
branch was squash-merged — which is a further reason the re-run control is the right instrument
here rather than the pruned bundle.)*
