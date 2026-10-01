# PRECOMMIT — nyiso-236: the rule-29 screen of `hydro_budget_period_by_instrument`

**Session** nyiso-236 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a), this session runs ZERO LP).
**Date** 2026-09-16. **Branch** `claude/nyiso-236-calibration-nvup6u`.
**Keeper, to be left untouched** `2026-09-14-nyiso-235-gas-repair`, bundle
`results/calibration/nyiso235_gasrepair_span`.
**Committed and pushed BEFORE the shard is launched and before any screen number exists.**

This document **adopts `results/calibration/PRECOMMIT-nyiso220-screen.md` in full** — that screen was
written, committed and pushed on 2026-09-08 and **never run**; the cell
`hydro_budget_period_by_instrument` is still `U`. Nothing here loosens a threshold nyiso-220 wrote.
What this addendum does is exactly three things: **re-base its reference values onto the current
keeper**, **record that G-DRIFT now makes rule 29(b) form 4 valid**, and **flag one gate-construction
defect before the solve rather than after**.

---

## 1. WHY THIS LEVER, AND WHY IT IS NOT A REDO (rule 28 `[R-MECH-MATRIX]` (a))

The owner asked for the hydro gap. It is real, and it is a **shape** gap, not a level gap — measured
this session, zero LP, against EIA-930 `NG: WAT`:

| year | EIA-930 hydro | model | annual error | **hourly r** | model σ ÷ actual σ |
|---|---:|---:|---:|---:|---:|
| 2022 | 26.183 | 25.612 | −2.2 % | **0.688** | 1.182 |
| 2023 | 26.837 | 26.616 | −0.8 % | **0.673** | 1.176 |
| 2024 | 26.834 | 26.739 | −0.4 % | **0.737** | 1.169 |
| 2025 | 24.063 | 24.059 | −0.0 % | **0.722** | 1.220 |

Annual energy is essentially exact and monthly energy is pinned (monthly r 0.915–0.998); the hour-of-day
mean profile tracks within ~100–150 MW at every hour. **All the error is elsewhere**, and hydro is the
worst-shaped resource in the model — against `fuelRows` r of 0.971 nuclear, 0.989 wind, 0.861 gas — on
~26 TWh/yr, more than wind and solar combined. It is also **unscored**: hydro appears in neither
`fuelRows` nor `nonfossil`, so C1 never sees it.

**Independent confirmation that this is the already-localized residual.** nyiso-218 §8 measured the
same thing from the other side (month energy r ≈ 1.000, hour-of-day r ≈ 0.98, **within-month
day-to-day r 0.207–0.392**), and nyiso-219 recorded that "the keeper tracks load at r 0.647/0.686/0.616
with 1.86–2.25× the actual". This session measured the **price** analogue without reading that note
first and got the same object:

| year | actual r(hydro, RT price) | model r(hydro, own price) | ratio |
|---|---:|---:|---:|
| 2022 | +0.242 | +0.521 | **2.15×** |
| 2023 | +0.321 | +0.573 | 1.79× |
| 2024 | +0.211 | +0.384 | 1.82× |
| 2025 | +0.270 | +0.397 | 1.47× |

The LP dispatches hydro as a price-optimizing arbitrageur; the real fleet is roughly half as
price-responsive. **Reported and NOT a gate** (see §4): it is the motive for looking, never the
instrument, and no threshold below is written against it.

**Two of the three candidate routes are already CLOSED on measurement and are not re-spent**
(nyiso-219): the USGS daily-inflow driver (71.38 % of fleet MW sits on regulated Great-Lakes outflow
with daily flow CV 3–4 %; Niagara's own r is 0.079 on 51.9 % of the MW) and the multi-year
climatological daily shape (mean r 0.031). `hydro_ror_split` is `G` and is not re-opened.
`hydro_dispatch_envelope` and `hydro_min_flow_floor` are `K` and bound a **different** dimension —
the diurnal ceiling, not day-to-day energy conservation — which is the rule 19 `[R-ONE-MECH]`
**RECONCILE** posture the owner's Q2 arithmetic decided at phase 0 and which this session's re-base
reconfirms.

## 2. THE ARM — ONE FIELD, ZERO DOF

`hydro_budget_period_by_instrument`, built by nyiso-220, `bool = False` GATED default off, CLI
`--hydro-budget-period-by-instrument`. Registry:

* **2693 Robert Moses Niagara → 24 h.** Derived: its instruments state no conservation period
  (verified mechanically against the full 1950 Treaty text) and its **measured pondage is 0.244 h** —
  use it or lose it. 51.89 % of NYISO hydro MW.
* **2694 Robert Moses St. Lawrence → 168 h.** **Stated in words** by the IJC peaking-and-ponding
  directive. 19.48 % of MW.
* The other **161 plants are deliberately absent** — unretrieved FERC licence articles, rule 14
  `[R-ACCURATE]`: do not invent an instrument we have not read.

Rule 21 `[R-DOF]`: **the period lengths are not free parameters and will not be swept.** If the screen
fails, the arm dies — it is not re-run at another period length.

## 3. RE-BASED REFERENCE VALUES (this is the only thing that moves)

nyiso-220's gates are stated against "the keeper's 2025 value", and the keeper it meant
(`nyiso213_summer_seam`) has since been pruned under rule 15's keeper-only retention. Re-measured on
the CURRENT keeper with `scripts/probes/nyiso220_phase0_period_overlap.py --keeper
results/calibration/nyiso235_gasrepair_span` (zero LP; the probe's hardcoded bundle is now a CLI
argument):

| year | cross-day footprint, current keeper | nyiso-220's value on nyiso-213 |
|---|---:|---:|
| 2022 | 6.36 % | *(not measured)* |
| 2023 | 5.31 % | 5.15 % |
| 2024 | 4.71 % | 4.58 % |
| **2025** | **7.46 %** | 7.47 % |

**SCREEN YEAR = 2025, unchanged**, and still the **largest-footprint** year on the current keeper —
rule 29's basis, explicitly **not** the largest-residual year. Q2 posture recomputes **RECONCILE**.

Gate reference values, keeper 2025, from committed sidecars:

* **G2** annual hydro **24.0589 TWh** (±0.1 % = ±0.0241); monthly TWh
  `2.1321 1.7441 2.2287 2.0966 2.3116 2.0655 2.0435 1.8796 1.6913 1.7046 2.0241 2.1371` (±0.5 % each).
* **G3** cross-day footprint **7.46 %** → must FALL, into the pre-registered band **1.0–6.0 %**, and
  must **not** reach 0.00 %.
* **G4** non-hydro class annual TWh: CC_REGULAR 35.5034 · nuclear 28.3416 · CC_CHP 20.5034 ·
  import 19.3209 · ST_GAS 9.7828 · wind 7.0487 · OTHER 1.9483 · CT_CHP 1.6590 · ST_CHP 1.4505 ·
  oil 1.2008 · solar 0.9813 · CT_PEAKER 0.7375 · biomass 0.6724 · COAL_BIT 0 · COAL_PRB 0.

## 4. G-DRIFT — form 4 is VALID, which nyiso-220 could not claim

nyiso-220 deliberately made its gates self-contained because 45 solve-path files had changed since its
keeper's sha and it had no audit. **This session has one**
(`docs/FINDING-nyiso236-the-anchor-grain-and-the-gas-slope-2026-09-16.md` §1): `moved_rows("NYISO")`
is `{}`, the surface fingerprint `bd2b4657f9b5df7e` reproduces, and all 35 changed files classify
INERT. **The keeper's committed bundle is therefore a valid control (rule 29(b) form 4) and no control
solve is spent.** The gates stay self-contained anyway — a stronger test, not a weaker one — and the
control differencing is reported beside them.

## 5. ONE GATE-CONSTRUCTION DEFECT, DECLARED BEFORE THE SOLVE

**G4 as written is 2 % of each non-hydro class, as a KILL gate.** On the current keeper that is
**±0.0148 TWh on CT_PEAKER** and ±0.0134 on biomass. Re-timing 7.46 % of a 24 TWh hydro fleet *must*
re-dispatch the marginal classes, and nyiso-220's own text says so ("some thermal re-dispatch is
expected and correct"). A 2 % band on a 0.74 TWh class is therefore not a bound on the mechanism's
**reach**; it is a near-certain kill for the mechanism doing its job — the same defect class nyiso-200
recorded as "a gate construction handed forward for correction".

**I am not loosening it.** Both forms are pre-registered here and **both will be reported**:

* **G4-as-written** — every non-hydro class within 2 % of the keeper's 2025 value.
* **G4-material** — the same 2 % bound applied to classes whose annual energy is **≥ 2 % of ISO load**
  (rule 20 `[R-FORCED-BUDGET]`'s own materiality floor, not a number invented here), plus the
  requirement that the total non-hydro move **conserves against** the hydro move to within 2 % of the
  hydro move itself. Sub-material classes are **reported at full magnitude**, never gated.

**If the two forms disagree, that is the session's reported result and the owner decides.** I will not
advance to the full span on `G4-material` alone without saying, in those words, that `G4-as-written`
failed. The other four gates are adopted verbatim and no threshold in them is restated after any
number is seen.

## 6. RULE 14 `[R-ACCURATE]`, RESTATED BEFORE THE NUMBER EXISTS

Hydro is ~20 % of NYISO generation, so re-timing it **will** move C3a/C3b/C3c. **If the faithful
representation makes the price fit worse, it STAYS**, and the worse fit is a discovered root-cause
question, not grounds to revert. This session has a specific reason to expect a worse price fit and
records it now: its own §3.3 measurement shows the model carries a **+$5.24/MWh excess fixed
intercept** that partially masks a tail deficit, so any structurally-correct change that removes
price-suppressing over-optimization may move C3a either way. **C3a is not a gate here** and will not
be used to promote or to kill.

## 7. WHAT MUST NOT HAPPEN

* No sweep of the period lengths (§2). One arm, one configuration.
* No re-opening of `hydro_ror_split` (`G`), the inflow driver, or the climatology (nyiso-219 closed
  both on measurement).
* No registration of the screen bundle, ever (rule 29 (2)); it is **gitignored, not deleted**
  (rule 31 `[R-RETAIN]`), and the promotion question is surfaced before this session ends.
* The full span 2022–2025 is spent only if this screen clears, as ONE `--years 2022 2023 2024 2025`
  invocation and ONE bundle (rules 16 / 32(b) / 34(c) — the registry year union is {2022, 2023, 2024,
  2025}).
