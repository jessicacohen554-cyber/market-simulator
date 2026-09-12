# FINDING — nyiso-230 phase 0: **NYISO has no price-LEVEL defect. It has a single-parameter GAS-SLOPE defect, r² = 0.996 over four years — and the mechanism that causes it is already registered, already default-off, and blocked from arming by the keeper's own zonal anchor.**

**Session:** nyiso-230 · **ISO:** NYISO · **Date:** 2026-09-12 · **DATA PROFILE: nyiso**
**ZERO LP.** Every number is read or recomputed from committed artifacts (the keeper bundle's
`run_config.json` / `hourly/` sidecars, the committed registry sidecars and run payloads, the
committed `data/raw/reference/nyiso_campd_marginal_hr_summary.csv`, and `_gas_series` evaluated on
the keeper's own recorded config). Rule 32 `[R-SHARD]` (a): the parent ran no LP.
**Keeper `2026-09-12-nyiso229-hourgrain-span` UNCHANGED. Nothing armed, nothing solved, nothing
registered.**

---

## 0. Headline

Four results, in ascending order of how much they should change what this lane does next.

1. **C1-2024 misses by 0.0458 pp — 60.3 GWh, 0.162 % of `CC_REGULAR`.** The volume leg PASSES with
   0.92 TWh of room; only the share leg fails, and by almost nothing. §1
2. **The offer bands WERE shifted down — as a rule-25 `[R-ISO-SCOPE]` DE-LEAKING of ERCOT-borrowed
   values, not a price cut — and `backcast_config.py` carries an explicit standing prohibition on
   reversing it to close C3a.** A lift is therefore NEW TUNING, not a reversal. §2
3. **The C3a residual is a linear function of (anchor − delivered gas): r² = 0.9955 in $/MWh across
   2022–2025, slope 2.691 $/MWh per $/MMBtu, intercept −1.28 $/MWh.** The in-sample geometric-mean
   bias is **−1.19 %** against an in-sample MAE of 4.90 % and a 12.2 pp spread — **the level is
   already right and the dispersion is 4× larger than the level.** §3
4. **The owner's requested experiment has already been run.** `2026-09-09-nyiso-222-offer-plus5` is
   a registered full-span solve of a uniform **+5 %** on all four bands of all five gas classes,
   against `2026-09-09-nyiso-221-fuelvintage-span` as its control. It yields NYISO's own measured
   full-span pass-through — **0.66685** — with no screen and no LP. §4

---

## 1. C1-2024 — the margin is 0.0458 pp, and the volume leg passes

Scorer: `python3 scripts/calibration_verdict.py results/calibration/nyiso229_hourgrain_span`.

| | model | actual | band | verdict |
|---|---:|---:|---|---|
| `CC_REGULAR` 2024 volume | 37.193 TWh | 34.060 | ±4.05 TWh | **PASS** (0.92 TWh of room) |
| `CC_REGULAR` 2024 share | 24.4395 % | 21.3937 % | ±3.0 pp | **FAIL, share_pp 3.0458** |

`m_gen` 131.5067, `a_gen` 134.9671 TWh (the scorer's own `_gen_totals` over `classFull`).
**Excess over band 0.0458 pp ⇒ 60.3 GWh** displaced within the scored fleet (84.0 GWh if the energy
leaves it entirely for import/hydro). That is **0.162 %** of `CC_REGULAR`'s energy.

**Where the energy belongs, by the scorer's own 2024 table (TWh, model − actual):**
`CT_PEAKER` **−1.623** · `ST_GAS` **−1.378** · `CT_CHP` **−1.198** · `ST_CHP` −0.141 · `CC_CHP`
+0.783 · `OTHER` +0.410 · `oil` +0.126. This is exactly the disposition **nyiso-187** attributed
and did not close: the CT/steam energy the market ran is out of the money at the actual price on the
LP's installed offer.

**Band decomposition of `CC_REGULAR` 2024** (`hourly/class_band_hourly_2024.parquet`, P1):
`committed` 20.106 TWh / 8760 h · six `econcNN` slices 2.815–2.830 TWh each, **all 8760 h at up to
430.5 MW** · `peak` 0.393 TWh / 2401 h. The econ ladder is **flat** — the top slice carries *more*
energy than the bottom one in 2024 — because the registered ramp spans only `econ_low` 0.95 →
`econ_high` 1.00.

## 2. Provenance: it was shifted down, and the shift was a legitimacy repair

The bands are **not** in the recipe, not in the shared `ScenarioConfig` default and not in NYISO's
`ISOConfig.default_scenario_overrides`. They are `_NYISO_OFFER_CURVE` in
`src/market_sim/pipeline/backcast_config.py:429`, which is why the keeper's
`authorized_price_tuning` is NULL and the provenance read as untraced.

| band | was | is | why |
|---|---|---|---|
| `CC_REGULAR.econ_high` | **1.21** | **1.00** | audit C-13 / B-NYI-1 rule-25 de-leak — an ERCOT CC marginal-HR reach value cross-borrowed to NYISO |
| `CT_PEAKER.econ_low/high` | 1.27 / 1.98 | 1.00 / 1.00 | same de-leak; "NYISO carries no independent CT part-load heat-rate spread yet" |
| `CT_PEAKER.peak` | 13.15 | 4.00 | ERCOT $5,000-ORDC wall → NYISO's $1,000/$2,000 cap |
| `CT_CHP` (all four) | 1.10/1.20/1.20/1.40 | 1.00 | same de-leak |
| `ST_GAS` | 0.97/1.10/1.45 | 1.05/1.08/1.13 | re-levelled (run 32) onto NYISO's own CAMPD steam marginal HR |

**The code carries a standing prohibition, verbatim** (`backcast_config.py:439-442`):

> *"The C3a hole this exposes is an OPEN ROOT CAUSE (rule #1): the real missing mechanism is NYISO
> scarcity/reserve (RCPF/AS) price formation, NOT a CC energy markup — see GitHub issue #1344.
> **Do NOT re-arm this markup to close C3a** (rule #26, rule #1)."*

It also records the cost of the de-leak — *"removing it craters C3a ≈ −24 %"* — and refuses it
anyway, because a residual justification is not a NYISO-identified value. **NYISO's own measurement
agrees with the de-leak**: `nyiso_campd_marginal_hr_summary.csv` gives `CC_REGULAR`
`marg_econ_high_p50` = **0.925**, nowhere near 1.21.

**A STALE CROSS-REFERENCE, provable from the file at HEAD with no history.** `ST_GAS`'s stated
identification basis is *"the CC class's own defensible reach ratio (CC econ_high **1.21** / native
CC marginal 0.925 = 1.31×)"* — it cites a CC band value the **same file** records as removed. On the
current CC reach (1.00 / 0.925 = 1.081×) the same construction returns `0.830 × 1.081 = 0.897`, not
1.08. **`ST_GAS` is ~20 % above its own stated construction, and it under-runs by 1.378 TWh in 2024.**
Reported here as an open object; not proposed as this session's lever (rule 19 `[R-ONE-MECH]` — see
§5 for why it must not be co-armed with §3's object).

**Answer to the question as put: it was shifted down, but a lift is not a reversal.** The cut removed
a cross-ISO leak that NYISO's own data does not support. Any lift is new tuning and must carry its
own ex-ante identification, the rule-1 `[R-STRUCT]` (a)–(e) conditions, an
`authorized_price_tuning` block and a rule-21 `[R-DOF]` ledger entry.

## 3. THE ROOT CAUSE: the residual is (anchor − fuel), not a level

`gas_offer_net_revenue_margin` is **armed** in the keeper with
`gas_offer_margin_anchor = 3.9046 $/MMBtu` — the frozen 2023–2025 mean of the model's own delivered
gas series. Its identity is *at `fuel == anchor` the reformed offer reduces EXACTLY to the registered
band multiplier*; away from the anchor the offer moves by `markup_hr × (anchor − fuel)`, a **linear
extrapolation with no saturation**.

`_gas_series` on the keeper's own recorded config (the registered anchor reproduces to 2×10⁻⁵):

| year | delivered gas $/MMBtu | anchor − fuel | C3a bias % | C3a bias $/MWh |
|---|---:|---:|---:|---:|
| 2024 | 2.7969 | **+1.1077** | **+3.3** | +1.240 |
| 2023 | 3.3566 | +0.5480 | +2.5 | +0.820 |
| 2025 | 5.5602 | −1.6556 | **−8.9** | −5.920 |
| 2022 | 8.4431 | **−4.5385** | **−16.6** | −13.460 |

> **Regression of bias$ on (anchor − fuel): slope 2.6911 $/MWh per $/MMBtu, intercept −1.2766 $/MWh,
> Pearson r = 0.99777, r² = 0.9955.** Residuals +0.030 / +0.622 / −0.464 / −0.188 $/MWh.

**The magnitude is an independent corroboration, not a curve fit.** The mechanism predicts the slope
*equals* the marginal-weighted `markup_hr = base_HR × max(0, mult − phys)`, which is computable from
the registered curve with no reference to any price:

| class | base HR | committed | econ_low | econ_high | peak |
|---|---:|---:|---:|---:|---:|
| `CC_REGULAR` | 7.763 | 0 (clipped) | 1.289 | 0.582 | 0 |
| `CC_CHP` | 6.989 | 0 (clipped) | 0 (clipped) | 0.957 | 0 |
| `ST_GAS` | 10.614 | 0 (clipped) | 2.654 | 3.205 | 33.965 |
| `CT_PEAKER` | 11.946 | 6.057 | 4.050 | 4.086 | 35.838 |

**The measured 2.691 lands between `CC_REGULAR`'s econ ladder (0.58–1.29) and `ST_GAS`'s
(2.65–3.21), with `CT_PEAKER` above** — exactly the load-weighted marginal mix NYISO has. And the
**intercept is −1.28 $/MWh: at the anchor the model is within ~3 % of actual in every year.**

**Honest limit.** Delivered gas and the price level are collinear, so correlation alone cannot
separate "the anchor mechanism does this" from "the model compresses price variation for any
reason". What distinguishes them is that (a) the slope's magnitude lands on an independently
computed property of the registered curve and (b) the zero-crossing sits at the anchor
(3.7044 $/MMBtu against the registered 3.9046). A generic-compression story predicts neither. The
decisive test is the A/B in §5.

**Corroborating, unprompted:** D-A diurnal amplitude is 63.1 → 53.8 → 42.9 % of measured as gas
rises (and 53.3 % in 2022) — the same compression, on a different statistic.

## 4. THE OWNER'S EXPERIMENT HAS ALREADY BEEN RUN — full span, registered, zero LP to read

`results/calibration/nyiso222_offer_curve_plus5.json` is a **uniform ×1.05 on all four bands of
`CC_REGULAR` / `CC_CHP` / `CT_PEAKER` / `CT_CHP` / `ST_GAS`** — exactly the lift under discussion.
Control: `2026-09-09-nyiso-221-fuelvintage-span` (its immediate predecessor recipe).

| year | actual | control $ | +5 % arm $ | Δ$ | control % | arm % | pass-through |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 32.25 | 33.65 | 34.94 | +1.29 | +4.34 | +8.34 | 0.7667 |
| 2024 | 38.12 | 40.15 | 41.52 | +1.37 | +5.33 | +8.92 | 0.6824 |
| 2025 | 66.43 | 61.60 | 63.30 | +1.70 | −7.27 | −4.71 | 0.5519 |

> **NYISO FULL-SPAN PASS-THROUGH = 0.66685** (geometric, the NEISO-106 estimator; arithmetic
> 0.66704). **It declines with delivered gas**, the neiso-104/105/106 signature, which is why a
> one-year screen coefficient would have been wrong here too — and why no screen was needed: the
> denominator was already on the dashboard.

**Two things this measurement settles.**

* **The lift is gas-INVARIANT in dollars** (+1.29 / +1.37 / +1.70 $/MWh) because the markup is
  priced at the fixed anchor. **A uniform lift slides all four years by the same dollars; it cannot
  compress the 12.2 pp spread.** Applied to the current keeper it gives **+6.5 / +6.8 / −6.4 %** —
  all in band, none of the dispersion touched.
* **It moves C1-2024 the right way, and by almost exactly the margin.** `CC_REGULAR` share_pp
  2.89 → **2.79** (−0.10 pp) on the nyiso-221 base. On the current keeper's 3.0458 that lands at
  **≈2.95 pp — a flip with 0.05 pp to spare.** (My own merit-order reasoning had predicted the
  opposite sign; the measurement overrules it. A uniform gas lift recedes gas as a whole against
  imports/hydro, and the largest gas class sheds the most.)

**The arm's registered determination reads NOT-YET for a RETENTION artifact, not a substantive
miss:** its bundle is pruned, so C6 is `UNATTESTED` and C8 `SKIPPED`. On what it does score it is
**C1 14/14 · free 10/10, C2 / C3a / C3b / C4 PASS**, with C3c its only substantive miss. C3b-2024
0.193 against ≤0.20 and C3a-2024 +8.92 % against ±10 % are the thin margins it buys that with.

## 5. THE SUCCESSOR IS ALREADY BUILT — and the keeper's own config blocks it

`ScenarioConfig.gas_offer_margin_anchor_vintage` (pjm-169 F4, `scenarios.py:14888`) resolves the
**same measurement on the solve year** instead of the frozen window. Its own field comment describes
§3's defect verbatim, before this session measured it:

> *"…the further a year's delivered gas sits from the window mean the further the offer departs from
> the band multiplier the ISO was calibrated with. In-window that is small by construction. Out of
> window it is not… when `fuel > anchor` the mechanism marks gas offers DOWN, by the most in the
> year gas is dearest, which is exactly where the identification says nothing."*

**Why it is the right class of object.** Zero free parameters, zero DOF entries, no
`authorized_price_tuning` block, and it is **not** the rule-1 `[R-STRUCT]` carve-out at all — the
band multipliers are untouched in every year and it restores the condition under which they mean
what they were calibrated to mean. Rule 13 `[R-MEASURED]` admissible on its own test (a forecast
year's anchor is the mean of that year's own forecast gas). Not rule-1(b) per-year fitting: the
config is one boolean and one formula identical in every year; what varies is a measured fuel level,
the same class of object as `gas_prices`.

**Rule 28(a) DO-NOT-REDO — clear.** NYISO's cell is **`U`**, and the row explicitly reserves it:
*"it is this lane's to adjudicate on its own market's data (rule 25 `[R-ISO-SCOPE]`): no PJM verdict
fills this cell."* PJM's cell is `R`, killed by its **S4 coal-displacement** gate (`COAL_BIT`
+3.28 %). **NYISO's coal is 0.000 TWh model and actual in every scored year, so PJM's kill reason
cannot fire here** — a per-ISO argument, not a transfer. PJM's S3 verified the arithmetic to a
ratio of **0.999** against a prediction fixed before its solve.

**Predicted NYISO effect (pre-solve, zero LP — fixed here before any solve).** Per-tranche offer
shift `= base_HR × max(0, mult − phys) × (gas_year − 3.9046)` $/MWh:

| year | `CC_REG` econ_lo | `ST_GAS` econ_lo | `CT_PEAK` committed | `CT_PEAK` peak |
|---|---:|---:|---:|---:|
| 2023 | −0.71 | −1.45 | −3.32 | −19.64 |
| 2024 | −1.43 | −2.94 | −6.71 | −39.70 |
| 2025 | +2.13 | +4.39 | +10.03 | **+59.33** |
| 2022 | +5.85 | +12.04 | +27.49 | **+162.65** |

If §3's regression is the mechanism, the bias collapses to the intercept in every year:
**≈ −4.0 / −3.4 / −1.9 % (2023/24/25) and −1.6 % (2022)** — the **12.2 pp in-sample spread → ~2 pp**,
2022's −16.6 % C3a FAIL closed, and `ST_GAS` / `CT_PEAKER` made *relatively* cheaper in 2024 (they
carry 2–6× `CC_REGULAR`'s `markup_hr`), which is the direction C1-2024 needs. The 2025 `CT_PEAKER`
peak tranche rising **+59.33 $/MWh** is also the first mechanism this lane has found that pushes on
**C3c** rather than around it.

### 5.1 THE BLOCKER, and it would have killed a shard on contact

`scripts/run_calibration.py:2534` — arming the vintage anchor while `gas_offer_margin_zonal_anchor`
is on is a **hard `SystemExit`**:

> *"…both re-resolve the SAME identification point; they are alternatives, never stacked
> (rule 19 `[R-ONE-MECH]`)."*

**The NYISO keeper has `gas_offer_margin_zonal_anchor = True`** with
`{Upstate_West 2.0346, Capital_Hudson 3.9046, Lower_Hudson 3.9046, NYC 2.7612, Long_Island 3.9046}`.
So **option B cannot be armed on the keeper recipe as it stands.**

That is not merely a plumbing accident — it is a real gap. NYISO needs **both** dimensions: the zone
spread is 2.03–3.90 $/MMBtu (validated at nyiso-109) and the year spread is 2.80–8.44. The mechanism
offers them as alternatives. The construction that serves both is the **same measurement resolved on
zone AND year** — `derive_gas_offer_margin_anchor.py` already supports `--by-zone`; evaluating it on
the solve year is the identical formula on a second index, still **zero free parameters**. It is a
new registered field (rule 24), a matrix row in the same PR (rule 28(c)) and an Opus-only edit to
`scripts/run_calibration*.py` + `constants.py` (rule 27).

## 6. WHAT THIS SESSION DID NOT DO

* **No LP, no screen, no arm, no promotion, nothing registered.** The keeper is unchanged.
* **No band lift is proposed here.** §4 measures what one does; sizing one is §7's decision.
* **The `ST_GAS` stale-reference object (§2) is NOT co-armed** with §5's object — they act on the
  same phenomenon (the gas offer level) and rule 19 `[R-ONE-MECH]` forbids stacking them. §5 first;
  §2 is re-measured against whatever §5 leaves.
* **C3c is not addressed directly.** §5's 2025/2022 `CT_PEAKER` peak shift is the first thing this
  lane has found that pushes on it, but that is a prediction, not a result.

## 7. THE DECISION, put rather than taken

| | option A — uniform band lift | option B — solve-year anchor |
|---|---|---|
| channel | rule-1 `[R-STRUCT]` authorized carve-out | registered field, not the carve-out |
| free parameters | **1** (ledgered, DOF entry, `authorized_price_tuning`) | **0** |
| evidence in hand | full-span A/B already solved (§4) | root cause r²=0.996 (§3); PJM arithmetic 0.999 |
| C1-2024 | flips, **0.05 pp of margin** | predicted improve, unmeasured |
| C3a | +6.5 / +6.8 / −6.4 %; spread **unchanged** | predicted ≈ −4 / −3 / −2 %; spread 12.2 → ~2 pp |
| 2022 (−16.6 %) | −13.5 %, still FAIL | predicted ≈ −1.6 % |
| rule-1(c) exposure | **the trap** — any size that flips C1 is a size chosen to make a criterion pass | none |
| blocked? | no | **yes, §5.1** — needs the zone×year build first |

**Recommendation: B, with A held in reserve and sized off B's own residual.** B attacks the measured
root cause with zero DOF and no carve-out; and once B lands, a level lift — if one is still wanted —
becomes cleanly sizable by the neiso-106 route, because **both halves of the division now exist**:
the target is B's own post-solve geometric-mean bias and the coefficient is the **0.66685** measured
in §4, on the full span, before the fact.

**Against my own recommendation, stated plainly:** A is measured and B is predicted; A needs no
build and B needs one; and B's prediction rests on a regression whose collinearity §3 discloses.
A reader who weights "already measured" over "structurally cleaner" should prefer A, and would be
reading the evidence correctly.

## 8. RULES

1 `[R-STRUCT]` — the recommendation rests on a construction defect measured from the model's own
inputs; the carve-out's condition (c) is named as the reason A is the riskier route, not reasoned
around. 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` — B is the same measured quantity at its own vintage.
19 `[R-ONE-MECH]` — §2's `ST_GAS` object and §5's anchor object act on one phenomenon and are not
co-armed; §5.1 is the codebase enforcing the same rule against A stacking on the zonal anchor.
21 `[R-DOF]` / 24 `[R-REGISTRY]` — B is zero-DOF; A is one ledgered free parameter identified by the
2026-09-05 ruling. 25 `[R-ISO-SCOPE]` — PJM's `R` verdict does not fill NYISO's cell; PJM's kill
reason is shown not to apply on NYISO's own zero-coal fleet. 28 `[R-MECH-MATRIX]` — the target cell
was checked before proposing (NYISO `U`, reserved for this lane); no cell is stamped because nothing
was tested. 29 `[R-SCREEN]` — phase 0 complete at zero LP; no screen year is named because no arm is
launched. 30(c) — 2022 cannot certify or decertify NYISO. 31 `[R-RETAIN]` — nothing deleted.
32 `[R-SHARD]` — the parent ran no LP.
