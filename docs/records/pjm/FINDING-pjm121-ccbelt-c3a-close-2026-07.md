# FINDING — PJM's C3a gate closes on the measured CC_LIKE offer belt; the dispersion compression it was supposed to fix does NOT (pjm-121, 2026-07-25)

> **STATUS — COMPLETE.** Candidate keeper `2026-07-25-pjm-121-cc-belt`
> (bundle `results/calibration/pjm121_ccbelt`) scores **CALIBRATED, 10/10
> criteria PASS** — PJM's first all-pass determination, closing the sole open
> gate carried by `2026-07-24-pjm-119-overlay-restore`. `keepers.json` is
> owner-only and untouched; the promotion is **flagged, not made**.
>
> **Read the scope section (§4) before quoting this result.** The gate closes
> on a legitimate *measured* mechanism, but **~73 % of the gain is a price
> LEVEL lift on hours the model already ran too high**, and the pjm-120
> dispersion compression is essentially untouched. This is a real structural
> improvement that also happens to clear the band — it is **not** the
> dispersion repair the residual calls for, and must not be reported as one.

**Charter:** close PJM's last open gate — C3a mean LMP 2025 at `−10.7 %`
against a `±10 %` band, the single NOT-YET criterion (9/10 PASS).

---

## 1. Result

One config delta vs the pjm-119 keeper, applied through `replay_keeper --set`:

```
pjm_offer_midcurve_segments:  ("LONG_RUN",)  ->  ("LONG_RUN", "CC_LIKE")
```

That hands the `CC_REGULAR` **econ** tranches to the already-frozen measured
mid-curve offer surface (`data/raw/_validation-source/pjm_offer_midcurve_condbinned.json`
— 36 months of PJM DataMiner2 `energy_market_offers`, 25.95 M unit-hours /
3,595 units, within-unit capacity-share ladders keyed by within-year net-load
percentile), at the **same** P1-only `mc_bid_adjust` seam, **same** floor-only
(raise-only) semantics and **same** VOLL cap as the `LONG_RUN` scope that has
been live in the keeper line since pjm-104. The mechanism engaged in every
year: **264 → 461 priced tranche rows** (197 CC_LIKE rows added).

**Zero new free parameters.** No offer-curve band, sigmoid, floor, ORDC
parameter, derive value or surface JSON was touched (rules 13/20/21/23). The
delta is a rule-19 *scope* flag.

| criterion | pjm-119 keeper | **pjm-121** |
|---|---|---|
| **C3a mean LMP** | **FAIL** (2023 +4.7 · 2024 −3.8 · **2025 −10.7**) | **PASS** (2023 +5.6 · 2024 −2.5 · **2025 −9.3**) |
| C1 fuel-mix | PASS 16/16 (free 12/12) | PASS 16/16 (free 12/12) |
| C2 / C3b / C3c / C4 / C5a / C7 / C8 | PASS | PASS |
| C6 governance | attested | attested |
| **determination** | **NOT-YET** | **CALIBRATED** |

C3a is scored on the RT load-weighted basis (`rt_lw`): 2025 model **$41.53**
vs actual **$45.80**.

## 2. Why it was worth re-testing a previously-rejected lever

This is the **pjm-108 lever**, which was **REJECTED on C1** — the measured CC
floor displaced **8.52 TWh of CC_REGULAR** out of merit in 2023, out of band.

That rejection was measured on the **pjm-107 base**, which predates three
structural changes now in the keeper line:

* the **symmetric-net DA-virtual form** (pjm-105), which specifically removed
  the clamped form's one-sided +10–17 TWh/yr phantom demand — the thing that
  was landing on whichever class was cheapest and breaking C1;
* the **restored east-interface cut** and **measured interface limits**
  (pjm-119, after the silent-overlay-degradation defect);
* the net-revenue offer margin (pjm-118).

On the current base the C1 blocker is simply gone: **16/16 gated rows, free
12/12.** The class the lever displaces is no longer the class absorbing a
phantom.

It also completes a chartered retirement. Per
`docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §A.1 the CC_LIKE econ rows
were *"the one remaining unmeasured mid-merit top"* and arming them was
explicitly designated a pure flag change. With this run all three mid-merit
segments are measured-owned — **CT_FAST** since pjm-103 (NREL/SR-5500-55433
start cost over CAMPD run horizons), **LONG_RUN** since pjm-104 (this same
surface), **CC_LIKE** now. Rule 19 is satisfied by *replacement*: the floor is
a `max()` against the fitted band on the CC econ rows, and the CC **peak**
rungs stay fitted-curve-owned (the pjm-99 top-of-curve surface remains off).

## 3. What sets the price — the measurement that reframes the lane

New this session (`scripts/probes/pjm121_marginal_decomp.py`): for each
pjm-120 actual-price stratum, which class is the LP's own price setter
(interior units at the clearing dual), the idle-supply shelf just above the
dual, and the binding-floor attribution. On the 2025 keeper baseline:

| actual stratum | h | model $ | actual $ | price-setting class share |
|---|---|---|---|---|
| 0–25 | 1,922 | 30.8 | 20.4 | **COAL 80 %**, ST_GAS 7, ST_CHP 5, CC_REGULAR 1 |
| 25–50 | 4,849 | 39.1 | 35.4 | **COAL 76 %**, CT_PEAKER 10, ST_GAS 7 |
| 50–100 | 1,655 | 48.5 | 66.0 | **COAL 56 %**, CT_PEAKER 33, ST_GAS 9 |
| 100–200 | 274 | 64.6 | 129.4 | COAL 48, **CT_PEAKER 39**, ST_GAS 11 |
| 200–376 | 45 | 86.0 | 252.5 | **CT_PEAKER 50**, COAL 44 |
| > 376 | 14 | 181.2 | 815.7 | **CT_PEAKER 59**, COAL 38 |

Two facts govern the lane:

1. **COAL sets 38–80 % of the price in EVERY stratum.** In a real market the
   marginal fuel rotates; in the model coal's tranche ladder straddles the
   whole price range and is marginal everywhere. The measured LONG_RUN corpus
   says coal tops out at `s0.995 ≈ 8.6 × gas ≈ $36` — **there is no coal wall**
   (confirmed at pjm-104) — yet coal is marginal in strata whose actual price
   is $66–252.
2. **CC_REGULAR is essentially never marginal (0–1 %)** despite carrying
   33–50 GW of dispatch, because it is inframarginal with only ~5 GW idle.
   This is precisely why the CC belt moves the *level* rather than the tight
   hours (§4): repricing a class that rarely sets the dual shifts the stack it
   sits in, not the margin.

The shelf table shows the same thing from the supply side: in the 50–100
stratum the model carries **15.6 GW of idle CT_PEAKER**, of which only 1.8 GW
is offered within $10 of the dual and 6.8 GW within $25 — a thick, too-cheap
mid-merit shelf pinning the price at $48.5 where the market cleared $66.

## 4. HONEST SCOPE — the dispersion guard is not satisfied

The pjm-120 finding measured the C3a-2025 residual as a **monotone dispersion
compression** and pre-registered a guard: *only a mechanism that increases
dispersion can close C3a-2025*; anything that lifts the level worsens the
6,771 cheap hours already $4–10/MWh too high. Stratified on the same bins:

| actual stratum | keeper contribution | **pjm-121** | Δ |
|---|---|---|---|
| 0–25 | +1.965 | +2.015 | **+0.050** |
| 25–50 | +2.045 | +2.249 | **+0.204** |
| 50–100 | −3.736 | −3.662 | +0.074 |
| 100–200 | −2.499 | −2.487 | +0.012 |
| 200–376 | −1.127 | −1.126 | +0.001 |
| > 376 | −1.534 | −1.534 | 0.000 |
| **total gap** | **−4.89** | **−4.54** | **+0.35** |

**+$0.254 of the +$0.35 (73 %) comes from the two CHEAP strata — hours the
model was already over-pricing.** The four tight strata contribute +$0.087
combined, and the three most expensive move by less than $0.02 each. The
dispersion compression is intact.

So: the gate closes on a structurally legitimate, measured, forward-native
mechanism with zero fitted parameters — **not** a fitted adder, haircut or
residual-tuned scalar (rules 1/11/13). But it is a level effect, and reporting
it as "the dispersion fix" would be false. The open root cause remains where
pjm-120 put it: the **reserve/LP supply-side tightness class (G-20b / ERCOT
G-22)** — 38.1 GW of deliverable 10-min ramp against a ~3.7 GW requirement, a
reserve dual that reaches $300 in **zero** hours all year, and §3's
coal-sets-everything margin.

## 5. Refuted this session — the LEVEL-form measured ladder

`docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §A.1 charters a *level-form*
step beyond the floor: *"A floor can only raise bids, so floor-form ownership
alone never retires a band that sits above the measured level — that is what
the level-form step (#3, the measured ladder replacing the synthetic smoothing
+ band construction) is for."* On paper it is the ideal dispersion mechanism:
the measured CC ladder is **cheaper** than the fitted band across the body
(shares 0.05–0.55: 4.9–5.5 × gas vs the fitted `econ_low` 0.96 × base-HR 6.372
= 6.12 ×) and **far dearer** at the top (shares 0.95–0.99: 11.1–18.8 × vs
`econ_high` 1.5 × = 9.56 ×).

It was **built and refuted without spending a solve.** The mechanism is
implemented behind `ScenarioConfig.pjm_offer_midcurve_level_segments`
(**default-off**, six regression tests), and
`scripts/probes/pjm121_level_form_precheck.py` runs the **real builder on the
real fleet and offer arrays** under three scopes and diffs them. 2025:

| arm | MW-wtd bid Δ vs keeper | row-hours dearer / cheaper |
|---|---|---|
| floor +CC_LIKE (this run) | **+0.61 $/MWh** | 12.4 % / 0.0 % |
| **level CC_LIKE** | **−8.76 $/MWh** | 12.4 % / **87.5 %** |

| CC econ offer spread (p90−p10, $/MWh) | bin0 | bin1 | bin2 | bin3 |
|---|---|---|---|---|
| keeper | 23.21 | 33.70 | 33.45 | 20.84 |
| floor +CC_LIKE | **24.76** | **34.85** | **34.65** | **22.63** |
| level CC_LIKE | **19.65** | **24.27** | **24.57** | **18.23** |

The level form **lowers** bids on 87.5 % of row-hours and **narrows** the
offer spread in every net-load bin — it is a level-*lowering* lever, the exact
opposite of what C3a-2025 needs, and it cannot close a dispersion gap. The
floor form is the only arm that widens the spread. The mechanism stays in the
codebase default-off (it is the correct construction for a fleet whose fitted
bands sit *below* measured); the reason it fails **here** is that the model's
CC econ rows sit predominantly at within-plant shares where the measured
ladder is flat and cheap — the measured steep belt (s0.95–0.99) lands on the
model's CC **peak** rows, which the mid-curve mechanism excludes by design.

**Also not re-opened** (closed by prior measurement, re-confirmed here): a
CT_FAST reprice. The measured CT_FAST corpus level is $96–164/MWh across every
stratum against a model marginal bid of $47–80 — a large, real gap — but
pjm-101/102 already armed exactly that as an HR-multiplier surface and it
**over-expressed**: CT −12 TWh crush, C3a +12 %. CT_FAST is owned by the
pjm-103 start-cost amortization (rule 19) and a floor computed against
`mc_base` alone would *stack* with it, since `mc_bid = mc_base + startup_markup
+ mc_bid_adjust` and the mid-curve builder never sees the startup term.

## 6. Guardrail review

* **Rule 1** — the mechanism is measured market structure, not a fit to the
  residual; §4 states plainly that the criterion it closes is not the
  criterion it repairs, and the level/dispersion distinction is reported
  rather than buried. The refuted level-form arm (§5) is recorded in place.
* **Rule 11** — replaces a fitted band with measured submitted offers.
* **Rule 13** — submitted OFFERS only, conditioned on within-year net-load
  percentile (forward-native, regenerates for a forecast year and responds to
  changed conditions). Clearing prices stay validation-only. Nothing pinned.
* **Rule 16** — one bundle, all three scorable years (2023/24/25), solved as
  the rule-12 per-year chain.
* **Rule 18** — zero new free parameters; the DOF ledger gains no entry and
  records the partial retirement of `offer_curve_by_group`. The per-band
  dominance ablation that would retire a fully-dominated band to neutral 1.0
  is the remaining step and is **not** claimed here.
* **Rule 19** — replacement, not stacking: floor is a `max()` on the CC econ
  rows; CC peak rungs stay fitted-owned; CT_FAST untouched.
* **Rules 20/23** — the surface JSON is the frozen artifact, unmodified.
* **Rule 22** — 2023–2025 only; no holdout year touched.
* **Falsifiability** — §5's pre-check was written with an explicit kill
  criterion in its docstring *before* it was run, and it killed the author's
  preferred candidate.

## 7. For the next session

1. **The keeper decision is the owner's.** pjm-121 strictly dominates pjm-119
   on the gated criteria (C3a FAIL→PASS, everything else unchanged) and moves
   a segment from fitted to measured. Recommended for promotion — with §4
   attached, not detached.
2. **The dispersion lane is open and unchanged.** §3's decomposition is the
   new entry point: *why is coal marginal 38–80 % of the time in every
   stratum, and what should be marginal instead?* The measured corpus says
   the $40–150 segment belongs to CC top-of-curve and fast-start CT; the model
   has CC econ topping at ~9.6 × gas and CC peak starting at ~31.9 ×, with a
   hole between.
3. **Do NOT re-open**: the level-form CC ladder (§5), a CT_FAST HR-multiplier
   reprice (§5, pjm-101/102), `gas_offer_margin_anchor` (pjm-120 §2),
   reserve-product coverage (pjm-120 §6).

## Reproduction

```
uv sync
python scripts/regenerate_clean.py transfer-interface-limits ramp-capability lmp
python scripts/data/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds hrl_da_incs_decs
for Y in 2023 2024 2025; do
  python scripts/replay_keeper.py results/calibration/pjm119_overlay_restore --years $Y \
    --out-dir results/calibration/pjm121_ccbelt \
    --set pjm_offer_midcurve_segments='["LONG_RUN","CC_LIKE"]'
done
python scripts/probes/pjm119_merge_year_chain.py results/calibration/pjm121_ccbelt
python scripts/run_calibration_full.py --rebuild-benchmark results/calibration/pjm121_ccbelt
python scripts/legitimacy_diagnostics.py --bundle results/calibration/pjm121_ccbelt --iso PJM \
  --years 2023 2024 2025 --json-out results/calibration/pjm121_ccbelt/legitimacy_diagnostics.json
python scripts/dashboard_add_run.py --label "pjm 121 cc belt" --bundle results/calibration/pjm121_ccbelt
python scripts/calibration_verdict.py 2026-07-25-pjm-121-cc-belt --write-metrics
```

Diagnostics: `scripts/probes/pjm121_marginal_decomp.py <bundle> --year 2025`
(§3), `scripts/probes/pjm121_level_form_precheck.py <bundle> --year 2025`
(§5), `scripts/probes/pjm120_c3a_stratum_readout.py <bundle> --year 2025`
(§4). Note the container suspends between turns — a solve advances only while
a command is actively running.
