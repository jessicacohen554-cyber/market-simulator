# FINDING — nyiso-170: the within-gas merit-order split is NOT an hourly displacement — the CC over-run and the CT/ST under-run are at-or-below their own null in every year and ANTI-coincident in 2025 — but the composition→price association survives four controls and is handed forward as a named object

**Session:** nyiso-170 · **Date:** 2026-09-01 · **Keeper:** `2026-08-30-nyiso-159-loss-surface`
(determination **NOT-YET** on {C3a-2025 −11.5 %, C3c}) · **Solves run: ZERO.**
**No parameter was touched, no offer band was swept, no run was registered.**

---

## 0. The result in one paragraph

The brief opened the within-gas merit-order split as the last live, NYISO-grounded,
in-lane lead on C3a-2025, on the hypothesis that the model clears cheap combined
cycles in the high-load hours where the market cleared CTs and gas steam — which
would be a direct structural source of the missing supply-curve steepness
nyiso-167/168 measured as the 0.7032 gain. It set a phase-0 stop condition: if the
over-run and the under-run are not the same hours, this is two objects rather than
a displacement, and the lane stops. **The stop condition is met, decisively and in
every year.** On the four classes CAMPD can identify, the matched-share statistic
is **0.164 / 0.313 / 0.474**, which sits **at or below its own 999-fold
circular-shift null p95** (0.167 / 0.314 / 0.525) in all three years; Pearson r is
**+0.022 / +0.016 / −0.212**; and with the load channel removed the 2025 series is
**anti-coincident** at a mean within-decile r of **−0.153 with 1 of 10 deciles
positive**. The *aggregate* composition claim does hold — the model's share of a
rising-load gas increment is more CC-heavy than the market's by **+0.086 (2024)**
and **+0.130 (2025)**, and 2025's class errors are **95 % / 90 % within-gas MIX**
rather than total-gas LEVEL — but it is not realised as an hour-local swap, so a
merit-order re-level is **not identified** as its mechanism and no lever follows.
Two things are nevertheless delivered rather than a bare null: a **citable
instrument limit** (CAMPD cannot identify NYISO's ST_CHP or CT_CHP hourly conduct
*at all*), and **one positive finding that survives four adversarial controls** —
within narrow load slices, the hours the model runs a higher CC share of its gas
are the hours it under-prices.

## 1. What was measured, and off what

Zero solve throughout. Every series is either a committed artifact or a raw
measured record:

| instrument | source |
|---|---|
| model hourly MW by class | the keeper's committed `hourly/class_hourly_<year>.parquet`, pass **P1** |
| model hourly zonal price + demand | the keeper's committed `hourly/system_<year>.parquet`, pass **P1** |
| measured hourly MW by class | `data/raw/campd-unit-level/NY_<year>.parquet`, `unitType` × the EIA-860 CHP flag via `market_sim.data.chp._chp_by_plant` — the model's own CHP determination |
| class volume reference | the committed `frontend/data/backcast/bench/NYISO/<year>.json.gz` `classFull` |
| actual price | the committed `actual_lmp_hourly_NYISO.parquet` (DA basis, the like-for-like comparable per nyiso-167 §2.1) |
| gas | `data/raw/gas-prices/transco_z6_ny_daily.csv` (Transco Z6 NY) |

**Rule 13 `[R-MEASURED]` compliance.** CAMPD enters only as *conduct
identification*. Nothing here pins a class to its observed generation, and no
offset, haircut or rescaling was tuned to any residual. Each measured class is put
on the grid-delivered basis by **one** factor, `benchmark_TWh / CAMPD_TWh` — which
**preserves the annual level error exactly**, since the anchored series sums to the
benchmark by construction and `model − anchored` therefore sums to the committed
`delta_twh` that nyiso-169b reported.

**Rule 22 `[R-HOLDOUT]`.** Every year read is 2023, 2024 or 2025. NYISO holds no
`complete` marker and is absent from `final`; nothing out-of-training was read,
solved, scored or registered, and no marker was requested.

**Reproduction of the inherited probes.** All five briefed probes were re-run
first. `nyiso167`, `nyiso168_gap_anatomy`, `nyiso169_congestion_gradient_anatomy`
and `nyiso169b` reproduce **bit-identically**; `nyiso168_reserve_supply_slack`
reproduces to 1e-15 as the brief documents and was **not** "repaired". One
operational note for successors, not a defect: `nyiso169`'s component
decomposition needs NYISO's DA zonal-LBMP container and most RT months, which are
**gitignored/regenerable** per `data/raw/lmp-data/README.md`. A fresh container has
only the 21 committed months, so the probe degrades silently to
`C_components_da: available=false` and 1,464 covered RT hours. Re-staging with
`scripts/data/fetch_nyiso_zonal_lmp.py --start 202301 --end 202512 --kind both`
(plus `regenerate_clean.py nyiso-interface-flows`) restores **bit-identical**
reproduction. The degraded output was never committed.

## 2. The pre-registered gates and their outcomes

Four probe files, each **committed before it was run** (the nyiso-169
pre-registration discipline): `nyiso170_merit_order_coincidence.py` (`ac4c1520`),
`nyiso170b_displacement_controls.py` (`245a44ae`),
`nyiso170c_anchor_repair.py` (`a175a5b6`), `nyiso170d_price_linkage_controls.py`.

| gate | question | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|---|
| **G1a / J1** | are the over- and under-runs the SAME HOURS? matched-share vs a 999-shift null | 0.164 (null p95 0.167) | 0.313 (0.314) | 0.474 (0.525) | **FAIL ×3** |
| **J4** | …with the load channel removed (mean within-decile r) | +0.010, 6/10 | −0.010, 5/10 | **−0.153, 1/10** | **FAIL ×2, anti-signed in 2025** |
| **J2** | is the model's marginal increment more CC-heavy? | 0.549 vs 0.549 | 0.582 vs 0.496 | 0.546 vs 0.416 | **2 of 3** |
| **J3** | is the error within-gas MIX rather than total-gas LEVEL? | 0.48 / 0.92 | 0.53 / 0.92 | **0.95 / 0.90** | **2025 only** |
| **H1** | are the measured class anchors valid? | — | — | — | **FAIL — instrument, §3** |
| **G3 / H2 / K1–K3** | does composition track the price deficit? | −0.184 | −0.235 | −0.160 | **SURVIVES ×3, §4** |

**The stop condition is met.** The brief's phase (1) asked whether the
displacement is hourly-coincident. It is not — on the raw statistic it does not
beat its own null in any year, and on the load-controlled statistic 2025 is
*oppositely* signed. Phase (2) was therefore **not entered**: no cost separation
was identified, no parameter was touched, no offer band was swept, and no solve was
manufactured. Per rule 15 `[R-DASHBOARD]`, a session with no solve registers
nothing, and the dashboard is untouched **by design, not by omission**.

### 2.1 Why "aggregate yes, hourly no" is not a contradiction

Both readings are true and they are about different objects. Under the exact
identity

```
delta_class(h) = s_meas,class(h)·dG(h)   +   ds_class(h)·G_model(h)
                 \___ total-gas LEVEL __/     \____ within-gas MIX ___/
```

(verified to a floating-point residual of 0.0 TWh in every class-year), 2025's
class errors are almost entirely **MIX**: CC_CHP +2.765 TWh of which +2.753 is mix;
ST_GAS −3.925 of which −3.715 is mix. So the model really does run a different gas
*composition* than the market did. What the coincidence gates add is that this
composition error is **not built out of hour-local substitutions** — in the hours
the model runs extra CC it is not, in general, the hours it is short of CT/ST.

The honest consequence: the merit-order *object* is real, but the *displacement
mechanism* — the thing that would have made "re-level the CC offer so a CT clears
instead" a legitimate structural fix under rule 1 `[R-STRUCT]` — is not the
mechanism producing it. Arming an offer re-level here would have been a steepener
adopted because the residual wants one, which rule 1 forbids, and this session's
measurement is what establishes that rather than assuming it.

## 3. An instrument limit, established and citable

Gate H1 failed, and the failure is a fact about CEMS coverage, not about the model.
Measured on the CAMPD NY 2025 extract:

| model class | CEMS units | CEMS gross TWh | benchmark TWh | anchor | identifiable? |
|---|---|---|---|---|---|
| CC_CHP | 17 | 15.858 | 16.962 | 1.070 | **yes** |
| CC_REGULAR | 22 | 33.992 | 33.544 | 0.987 | **yes** |
| CT_PEAKER | 31 | 1.904 | 2.851 | 1.498 | **yes** |
| ST_GAS | 15 | 15.138 | 13.712 | 0.906 | **yes** |
| **ST_CHP** | 5 | **0.000** | 0.800 | — | **NO** |
| **CT_CHP** | 1 | 0.483 | 2.383 | 4.933 | **NO** |

NYISO's five CEMS-registered steam units at EIA-860 CHP plants reported **0.000 TWh
for the whole of 2025**, and CT_CHP is represented by a **single** unit carrying a
fifth of its class's benchmark volume. Neither class's hourly conduct can be
identified from CAMPD at any grain. This matters beyond this session in three ways:

1. **It silently contaminated this probe's own first pass.** With measured ST_CHP
   identically zero, the over-run group carried the model's *entire* ST_CHP output
   as error (+1.492 TWh, a nominal +186.6 %). Gate H1 caught it, gate J1–J4 re-ran
   on the admissible four, and the repair **strengthened** the kill rather than
   rescuing it. That ordering — validity gate first, verdict second — is the reason
   the conclusion stands.
2. **It confirms nyiso-169b's ST_GAS number rather than impeaching it.** That
   probe's measured ST_GAS pooled CHP and non-CHP boilers under `fired|boiler`.
   Because NY's CHP boilers report exactly zero, the pooled series **equals** the
   non-CHP series identically. nyiso-169b's ST_GAS figures stand unrepaired; a
   successor should not "fix" a non-bug.
3. **Any future NYISO lane proposing to identify ST_CHP or CT_CHP conduct from
   CAMPD should stop here.** The data does not exist. This is filed as an
   identification blocker, not a task.

## 4. The one finding that survives — and everything thrown at it

nyiso-170's gate G3 passed: model-minus-actual DA price gap, ordered by the hourly
CC-share excess `ds_CC`, spreads **−10.65 / −14.26 / −13.27 $/MWh** top-to-bottom
decile. **That result is worthless until the load channel is removed**, because
`ds_CC` and the price gap are both functions of load, and a pure load artifact
would produce exactly the same ladder. Four independent attacks were pre-registered
and run against it:

| control | construction | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **H2a** within-load-decile spread | ds_CC quartile spread *inside* each load decile | 6/10 deciles ≤ −$2 | 8/10 | 9/10 |
| **H2b** partial r given load | residualise both on load, load², load³ | **−0.243** | **−0.316** | **−0.257** |
| **K1** full partial r | further residualise on gas, gas², load·gas, net imports, renewables | −0.184 (0.76×) | −0.235 (0.74×) | −0.160 (0.62×) |
| **K2** rank robustness | Spearman on the K1 residuals | −0.159 | −0.248 | −0.206 |
| **K3** permutation null | 199 within-decile permutations of ds_CC | 8/10 beat p5 | 9/10 | 9/10 |

**It survives all of them.** Three details make the survival more than a
technicality. First, the **partial correlation is stronger than the raw**
(−0.257 vs −0.214 in 2025): load *suppresses* the association rather than creating
it, which is the opposite of the confound's signature. Second, the ds-decile ladder
is already nearly load-orthogonal — mean load runs 16,650 → 17,913 → 16,845 MW
across deciles 0→9 while the gap runs +4.22 → −11.68 → −9.05 $/MWh. Third, the
within-load-decile spreads are **monotone in load** (2025: −2.66 at decile 0 rising
to −22.08 at decile 8), which places the association squarely in the ordinary
50–90 band that nyiso-168 showed carries 73 % of the 2025 deficit.

**What this is, stated at its true strength.** A measured **association** between
the model's gas-composition error and its price deficit, robust to load, gas price,
imports, renewables, rank transformation and permutation. **It is NOT a
demonstrated causal mechanism**, and it does not name a lever: the same measurement
that upholds it (§2) shows the composition error is not built from hour-local
substitutions, so "make CC dearer so CT clears" does not follow from it. A
successor who opens it needs a *third* thing — an identification of why the model's
gas composition is wrong in a way that is not a swap — and that is not in hand.

## 5. Lines this session closes

* **CLOSED — the within-gas merit-order split as an HOURLY DISPLACEMENT.** Failed
  on its own pre-registered gate in all three years, at or below a circular-shift
  null, and anti-signed in 2025 once load is controlled. Do not re-open the
  displacement framing without a new instrument; the aggregate composition claim
  (§2.1) is *not* the same claim and is preserved.
* **CLOSED — CAMPD as an identification route for NYISO ST_CHP and CT_CHP hourly
  conduct.** 5 units at 0.000 TWh and 1 unit at a 4.93 anchor respectively. The
  data does not exist.
* **NOT OPENED — an offer-band re-level against C3a.** `offer_curve_by_group`
  stays **`K`**; no band value was changed and none was swept. Under rule 1
  `[R-STRUCT]` the mechanism must be right before the level is tuned, and this
  session's measurement says the displacement mechanism is not what is producing
  the composition error.
* **NOT OPENED — the un-grounded `peak` 2.25.** The brief's guardrail was
  honoured: it was neither swept against C3a nor otherwise touched, and it remains
  un-grounded (no NYISO measurement behind it; the CAMPD marginal-HR summary has no
  `peak` column) exactly as nyiso-169b recorded.
* **NOT RE-TESTED — the twelve closed lines (a)–(l)** of the brief, and no C3c
  lever was opened.

## 6. Honest expected value

**What is delivered.** A reproducible, zero-solve, four-times-pre-registered
adjudication that (a) answers the brief's phase-0 question **NO** with the
strongest available construction — a matched-share statistic that fails against its
own null in every year *and* an anti-signed load-controlled version in the failing
year; (b) separates the *aggregate* composition claim, which survives, from the
*displacement* claim, which does not, through an exact algebraic identity rather
than an assertion; (c) establishes and documents a CEMS coverage limit that
contaminated this probe's own first pass and would contaminate any successor's;
(d) confirms nyiso-169b's ST_GAS construction is sound in NY; and (e) subjects its
own single positive finding to four controls designed to kill it, and reports that
it survived at its true, deliberately modest strength.

**What is NOT delivered. No gate moves.** C3a-2025 is still −11.5 %, C3c still
fails, the determination is still **NOT-YET on {C3a-2025, C3c}**, and NYISO still
does not read CALIBRATED. **No solve ran**, so rule 15 registers nothing. No matrix
cell verdict moves; `offer_curve_by_group` takes added evidence for the `K` it
already holds. **The lane did not produce a lever**, and the session does not claim
one.

**What could still be wrong.** The coincidence test is a demanding one: the LP is a
single simultaneous 8760-hour optimisation with storage and inter-temporal
coupling, so a real merit-order error need not appear as an hour-local MW swap if
imports, hydro or storage re-time the difference — the honest bound on the kill is
that it refutes *hour-local substitution*, which is what the brief specified, not
every conceivable merit-order story. The measured series carries CAMPD's own hourly
noise and a single annual anchor per class, so hour-to-hour matching is imperfect
even where coverage is good; CT_PEAKER's 1.50 anchor is at the edge of the
admissible band and is the weakest of the four. The price linkage is an
association: no control can rule out an unobserved third factor, and the direction
of causation is not established. And the `ds_CC`-vs-gap relationship is measured on
the model's own load ordering against a hub DA series, so the two are not the same
spatial object — the same caveat nyiso-168 §9 recorded for its band decomposition.

**The honest read on the object.** After nyiso-167, 168, 169, 169b and this
session, C3a-2025 is fully partitioned and every named partition is adjudicated.
The **gradient** half is a representation limit (nyiso-169 §8). The **level** half
is the price-response gain, whose remaining explanations are markup and reserve
offer structure, both blocked on data this lane cannot obtain (nyiso-168 §6.3).
This session removes the last in-lane candidate that was *not* blocked — the
merit-order displacement — by measurement rather than by exhaustion. What it leaves
behind is one named, controlled, honestly-bounded association and no lever. **A
successor should not expect to close C3a-2025 from the current data set at the
current grain**, and the standing $27.79–$56.03/MWh pass window nyiso-167 derived
should be planned around rather than solved away.

## 7. Evidence

* `scripts/probes/nyiso170_merit_order_coincidence.py` + `results/calibration/_nyiso170_merit_order_coincidence.json` — gates G1a/G1b/G2/G3; committed at `ac4c1520` **before** it was run.
* `scripts/probes/nyiso170b_displacement_controls.py` + `_nyiso170b_displacement_controls.json` — H1 anchor validity, H2 the load-confound attack, H3, H4; committed at `245a44ae` before running.
* `scripts/probes/nyiso170c_anchor_repair.py` + `_nyiso170c_anchor_repair.json` — J1–J5, the repair onto the four admissible classes; committed at `a175a5b6` before running.
* `scripts/probes/nyiso170d_price_linkage_controls.py` + `_nyiso170d_price_linkage_controls.json` — K1–K3 third-factor controls.
* `docs/FINDING-nyiso169-congestion-gradient-anatomy-2026-09-01.md` §7–§8; `docs/FINDING-nyiso168-supply-curve-slope-anatomy-2026-09-01.md` §4, §8–§9; `docs/FINDING-nyiso167-c3a-price-response-gain-2026-09-01.md` §2, §5 — the closed lines, none re-opened.
* `docs/calibration-log/nyiso.md` — the nyiso-169 / nyiso-169b entries this session continues.
* `src/market_sim/pipeline/backcast_config.py::_NYISO_OFFER_CURVE` + `data/raw/reference/nyiso_campd_marginal_hr_summary.csv` — the offer-band ladder of §0, read but **not modified**.
* `docs/codebase-site/data/mechanism-matrix/NYISO.js` — `offer_curve_by_group` (`K`, evidence added; **no verdict moves**), re-read before anything was proposed; `node --check` and `scripts/check_mechanism_matrix.py` both pass.
* CLAUDE.md rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 15 `[R-DASHBOARD]`, 22 `[R-HOLDOUT]`, 23 `[R-FROZEN-DERIVE]`, 25 `[R-ISO-SCOPE]`, 28 `[R-MECH-MATRIX]`.

Next shorthand: nyiso-171.
