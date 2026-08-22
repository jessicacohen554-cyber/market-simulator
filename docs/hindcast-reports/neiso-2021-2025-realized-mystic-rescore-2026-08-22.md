# Capacity hindcast — NEISO 2021→2025 (realized fuel)

_Generated 2026-08-22 · W2-P5 · plan §1.4 · bundle `results/hindcast/neiso-2021-2025-realized-mystic-rescore/NEISO/e118e887b306da37`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Provenance — what this run hindcasts, and what moved

**This is a RE-SCORE leg, not a new model result.** It reproduces the
`neiso-2021-2025-realized-k99` hindcast (2026-08-19) and scores it against the
**corrected, Mystic-inclusive** capacity actuals. The prior leg committed no
evolution ledgers, so it could not be re-scored in place; this bundle is
ledger-complete (`evolution_2021..2025.json`) and supersedes it as the scoring
basis. **Solve/registration lane only:** no mechanism was proposed, no
`ScenarioConfig` default was changed, and nothing was tuned (rules 1
`[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 21 `[R-DOF]`, 23
`[R-FROZEN-DERIVE]`, 24 `[R-REGISTRY]`). The actuals correction is a **data
repair**, not a lever.

**The model side is BIT-IDENTICAL to k99** — total 7.332 GW and every per-fuel
figure (`biomass` 0.002 · `coal` 0.791 · `gas_cc` 5.100 · `gas_ct` 0.000 ·
`gas_st` 1.438 · `oil` 0.000) reproduce exactly. **Every metric movement below is
attributable to the actuals repair alone.**

**`hindcast_verified_announced_exits` is CONFIRMED INERT for NEISO — measured, not
assumed.** The harness arms it by default and this run carries it `true`
(`run_config.json`); k99 predates the field and ran without it. Two independent
confirmations: (a) `load_announced_reversal_plants("NEISO")` returns the **empty
set under both arms** (`as_of=None`, the un-gated verified arm, and
`as_of=2020-12-31`, the ex-ante arm) — NEISO's registry carries no reversal row
to un-gate; (b) the bit-identical model output above. The registry's only two
NEISO rows are Merrimack 1/2 (consent decree), which are **double-blocked**
in-window: `exit_year` 2028 is outside 2021→2025, and `instrument_date`
2024-03-29 post-dates the run's 2020-12-31 vintage cutoff.

**Retirement channel mix — all-economic, as expected.** From the committed
ledgers' own `reason` tags, cumulative 2021→2025: **economic 7,330.1 MW**
(`gas_cc` 5,100.4 / `gas_st` 1,438.2 / `coal` 791.5) and **announced 1.8 MW**
(biomass only, 2 units). **No fossil retires through the announced channel** —
`forecast_fossil_retirement_economic` is `True`, making step 1 a default no-op for
fossil — and **no unit retires through the confirmed channel** (step 0 contributes
0.0 MW for the reasons above). The entire fossil exit path is the step-3 economic
screen.

**Solve HEAD, recorded for reproducibility.** The LP was solved at `2c54910`; this
bundle is committed onto `8bf6e03`, which merged NYISO-lane work in between. That
merge cannot move a NEISO result: its only `src/market_sim/` deltas sit behind the
NYISO CHP lay-up duty flags, and **both are default-off** (`chp_layup_duty_split`
and the newly-added `chp_layup_duty_curve: bool = False`), so no NEISO code path
changes. Stated rather than left implicit, since the two commits differ.

**Governance (printed at launch, not inferred):** `mode="forecast"` throughout, no
backcast overlay fires. The window **solves [2021, 2023, 2024, 2025] and bridges
[2022]** (evolved across, LP never solved, measured data never read — rule 22
`[R-HOLDOUT]`); 2021 seeds the price/margin signal and is never scored; scoring
stays inside 2023-2025 on both bounds. `leakage_violations: []`. The holdout spend
freeze was ACTIVE at launch and this run is legal under it — **no out-of-training
year is solved, scored or registered, and no marker is spent.**

### What the actuals repair moved (scoring basis only)

RD-5 third coverage gap: Mystic 8/9 (plant 1588 — six CC parts
`GT81`/`GT82`/`ST85`/`GT93`/`GT94`/`ST96`, 1,744.4 MW, retired 2024-06) was absent from
`capacity_actuals_neiso.csv` because EIA dropped plant 1588 from the 2025 Early
Release retired sheet and the 2023/2024 vintages carry no retired sheet at all.

| metric | k99 basis | this run | Δ |
|---|--:|--:|--:|
| actual thermal GW retired | 3.253 | **4.997** | +1.744 |
| actual `gas_cc` GW | 0.139 | **1.884** | +1.745 |
| model thermal GW (unchanged) | 7.332 | 7.332 | 0.000 |
| thermal-retire err | +125% | **+47%** | −78 pp |
| `gas_cc` err | +3562% | **+171%** | −3391 pp |
| false-retire GW | 5.920 | **4.175** | **−1.745** |
| false-retire, % of model | 81% | **57%** | −24 pp |
| recall denominator (≥300 MW) | 4 | **6** | +2 |
| recall | 2/4 = 50% | **4/6 = 67%** | +17 pp |
| plant-exact recall | 2/4 = 50% | **4/6 = 67%** | +17 pp |

**`ST85` and `ST96` (315 MW each) join the recall set and are BOTH matched — at
both grains.** They enter the denominator because the D-24 member rule is
fail-closed and NEISO has no committed exit decode (that instrument is
ERCOT-only), so no exclusion can be taken: `members` = 6, `excluded` = 0. They are
matched on the fuel-MW-coverage grain trivially (the model's 5,100 MW `gas_cc`
derate pool covers 2 × 315 MW), **and on the stricter plant-exact grain as well** —
the model retires `CC_REGULAR_Boston_p1588_econ`, **664.4 MW at plant 1588,
executed 2024**, the same plant, fuel and year as the real Mystic 8/9 exit. The
model's largest single `gas_cc` exit was therefore a **true positive that the old
actuals basis was scoring as a false-retire**; that is precisely what the repair
corrects, and it is why the recall movement is real rather than denominator
inflation.

**The remaining `gas_cc` gap is genuine over-retirement: 5.100 GW model vs 1.884 GW
actual = 3.216 GW.** All three retirement bands still FAIL and are reported at full
magnitude. Root cause below.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 4.997 | 7.332 | +47% | ❌ FAIL |
| unit recall >300MW | 6 units | 4 matched | 67% | ❌ FAIL |
| false-retire (GW) | — | 4.175 | 57% of model | ❌ FAIL |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **67%** (4/6). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **6 of 6** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.262 | 0.002 | -99% |
| coal | 0.846 | 0.791 | -6% |
| gas_cc | 1.884 | 5.1 | +171% |
| gas_ct | 0.319 | 0.0 | -100% |
| gas_st | 0.48 | 1.438 | +200% |
| oil | 1.208 | 0.0 | -100% |

### Root-cause note on the residual 3.216 GW `gas_cc` over-retirement (rules 1 / 14 — diagnosis only, nothing implemented)

**Rule 28(a) DO-NOT-REDO check, run BEFORE any lever was considered.** NEISO's lever
queue (`docs/mechanism-testing-matrix.md` §5.6) is **CLEARED** — its last live item
was spent at neiso-81 — and the ISO's declared frontier target is C3c, a backcast
criterion this forecast-family run does not touch. The NEISO shard already carries
`economic_retirement_screen` at **`R`/`fc: R`** (FFR-3A-2/3A-3, twice measured,
never attributed). **Nothing here re-opens that cell, no parameter was touched, and
no arm was solved.** What follows is measurement off this run's own committed
ledgers plus two standing instruments; every number is reproducible from committed
artifacts.

**The `gas_cc` exit is a single screen firing, not a five-year drift.** All 46
`gas_cc` exit decisions (5,100.4 MW) were **decided in 2023 and executed in 2024**.
Measured from this run's own ledgers, 2024 deactivates **5,891.9 MW of a 26,888.9 MW
entering thermal fleet — 21.9 % in one year** (denominator = `fleet_by_fuel_before`
summed over coal/gas_cc/gas_ct/gas_st/oil/nuclear/biomass; the k99 report's 23.1 %
is the harness's own I6 statistic on a different denominator, and no per-run
invariant file was emitted for this bundle, so the figure quoted here is the
directly-computed one). The screen for year Y consumes year Y−1's dispatch, so the
decisive price object is the **2023 solve**.

**Which leg is understated — measured, from the ledger's own per-unit bar
decomposition** (`pipeline_events[].{energy_margin,reserve_uplift,capacity_revenue,as_annual_credit,attribute_revenue}_usd`,
capacity-weighted over the 46 exiting units):

| leg | $/kW-yr |
|---|--:|
| energy margin | 6.42 |
| reserve uplift (ORDC adder) | 0.32 |
| AS annual credit | 0.00 |
| attribute revenue (EAC/RPS/45U) | 0.00 |
| **capacity revenue** | **0.00** |
| **net revenue** | **6.73** |
| going-forward bar (`fixed_om_gas_cc` × 1.0) | 30.00 |
| **shortfall** | **23.27** |

**The understated leg is capacity revenue, and it is decisive on its own.** The
model pays these units **exactly $0.00/MW-yr** of RA revenue in every year of the
window. ISO-NE's own published FCA clearing prices over the same window
(`data/raw/capacity-market/auction-price/neiso/neiso.csv`, committed) are:

| delivery year | $/kW-mo | $/kW-yr | cleared MW |
|---|--:|--:|--:|
| 2021/2022 | 4.631 | 55.6 | 34,828 |
| 2022/2023 | 3.800 | 45.6 | 34,839 |
| 2023/2024 | 2.001 | **24.0** | 33,956 |
| 2024/2025 (Rest of Pool) | 2.611 | 31.3 | 34,621 |
| 2025/2026 (Rest of Pool) | 2.591 | 31.1 | 32,810 |

The FCA price for the decisive delivery year is **$24.01/kW-yr against a
$23.27/kW-yr shortfall** — the measured capacity payment alone covers **103 %** of
the gap, and every other window year covers it outright. Crediting the observed
RA revenue would have kept the entire 5.1 GW solvent. The AS leg (0.32 $/kW-yr,
the ORDC adder under `screen_reserve_value_enabled`; `as_revenue_enabled` is off)
is second-order, and the energy margin (6.42 $/kW-yr, screen price mean $40.66
against mc mean $44.07) is directionally plausible for a low-gas 2023.

**It is NOT the demand curve.** `scripts/validate_capacity_prices.py` Pass 1 places
the *implemented* NEISO curve at each auction's **published, fleet-independent**
reserve position: shape reproduction is exact (cap fraction 1.600 vs 1.600, +0.0 %
in 2020/21→2024/25) and price reproduction lands **within +11 % to +13 %** of the
cleared price for 2021/22, 2022/23 and 2023/24 (−22 % in 2020/21). At the real
positions the curve pays real money — $26.7/kW-yr for 2023/24 against $24.0
cleared.

**It is the model's own accredited reserve position.** Pass 2, run on this
bundle's ledgers (`--pass2-run NEISO=neiso-2021-2025-realized-mystic-rescore`):

| cal yr | peak MW | firm MW | req MW | reserve pos | model curve | cleared |
|---|--:|--:|--:|--:|--:|--:|
| 2021 | 25,101 | 33,803 | 25,163 | **1.343** | **$0.0** | $55.6 |
| 2023 | 23,475 | 32,262 | 23,533 | **1.371** | **$0.0** | $24.0 |
| 2024 | 24,255 | 26,259 | 24,315 | 1.080 | $4.0 | — |
| 2025 | 25,898 | 27,447 | 25,962 | 1.057 | $33.9 | — |

**The bundle's own forecast invariants corroborate this independently.** The
registered sidecar (`frontend/data/hindcast/neiso-2021-2025-realized-mystic-rescore.json`)
carries **I12 as a WARN** for exactly this: reserve margin **27.8 % (2021)** and
**30.5 % (2023)** against a requirement-implied band of **[0.2 %, 15.2 %]** — the
same over-long position, flagged by a check that knows nothing about the capacity
screen. **I6 FAILs** alongside it (23.1 % of thermal retired in one year, 2024 —
the harness's own statistic on its own denominator; the 21.9 % quoted above is the
directly-computed figure and the two differ only in denominator).

`_NEISO_FCA_CURVE`'s zero-cross is **reserve position 1.083**. The published
positions sit at **1.035–1.063**, just inside it; the model's own sit at
**1.343 / 1.371**, well past it — so the curve returns **exactly zero** in both
screen-relevant years. The numerator is not the problem: 32,262 MW of accredited
firm capacity against 33,956 MW actually cleared in FCA 2023/24 is ~5 % low, and
NEISO's thermal accreditation basis (`claimed_capability` → 1.0, ISO-NE's
Qualified Capacity, no EFORd derate) is the ISO's own published basis.

**The dominant identified term inside the position is a peak-basis mismatch — and
it does not fully close the gap.** `resolve_adequacy_requirement_mw` falls back to
`peak × (1 − f) × (1 + PRM)` for NEISO (no published FPR is wired —
`resolve_forecast_pool_requirement("NEISO", y)` returns `None` for every year in
the window), giving a multiplier of **1.0025**. Both factors are pinned to ISO-NE
**planning** quantities from FCA 17 (Net ICR 30,305 MW, cleared demand resources
2,940 MW, CELT 50/50 summer peak 27,298 MW), and the registry's own comment states
the identity it reproduces — `requirement = (peak / CELT_peak) × (Net_ICR − DR)` —
holds **"when peak = CELT_peak"**. The model applies it to its *simulated
coincident* peak, which runs at **0.86–0.95 × the CELT 50/50 peak** (2023: 23,475
vs 27,298). The requirement scales with that peak; the accredited fleet does not.
Re-anchoring the 2023 denominator on the planning peak the ratio was built from
(`Net_ICR − DR` = 27,365 MW) moves the position **1.371 → 1.179** — roughly
**two-thirds** of the distance to the published 1.063, **but still above the 1.083
zero-cross**. So a second, smaller term remains and is **NOT identified here**; and
the vintage caveat is stated rather than buried — the registry ratio is FCA-17
(CCP 2026/27) vintage while the Pass-1 comparators are each year's own published
parameters, so the two are not a like-for-like pairing.

**This is cross-cutting, not a NEISO lever.** The same instrument shows PJM's
committed capacity hindcast (`pjm-2021-2025-realized`, the validator's default
Pass-2 run for PJM) failing **identically**: a model curve of **$0.0** against
cleared $51.1 / $12.5 / $10.6 / $98.5 — **−100 % in every year**. The −100 %
signature holds on **both** readings of PJM's positions: the committed
`results/capacity-price-validation/validation.json` records 1.0969 / 1.1489 /… and
a HEAD re-run of the validator returns 1.1422 / 1.1963 / 1.183 / 1.100. (That PJM
requirement drift between the committed artifact and HEAD is **another lane's
finding, observed and left alone here** — the artifact was reverted rather than
refreshed, since adopting a PJM-side change unexamined would breach rule 25
`[R-ISO-SCOPE]`. It does not touch this conclusion: the model price is $0.0 either
way.) Two ISOs, one signature. The lane that owns this
is therefore the **FR-4 retirement-screen row**
(`docs/forecast-readiness-audit-2026-07.md`) together with the **CR-3 curve-refinement**
item `_NEISO_FCA_CURVE`'s own comment already names ("a first-order linear reduction
of the MRI slope (skips FCA 11's interior kink); refined in CR-3") — **not** NEISO's
cleared backcast queue, and not this session. **No lever was pulled and no cell
verdict moved on this finding.**

**One prior-record note, filed rather than acted on.** The NEISO
`economic_retirement_screen` cell's `R` verdict rests on FFR-3A-2/3A-3 evidence
quoted against an actual retirement total of **0.951 GW**, and k99 was scored
against **3.253 GW**; both bases are superseded by this run's **4.997 GW**. The
verdict itself is unaffected — a 3.216 GW `gas_cc` over-retirement is real on the
corrected basis, and the cell stays `R` — but any future re-adjudication should
restate its magnitudes on the repaired actuals.

**The `oil` / `gas_ct` −100 % misses are the SAME defect, not a second one.** With the
capacity leg at zero, the 2024 screen fails **19,185.8 MW** — **86 % of the
22,238 MW of non-nuclear thermal it looked at** — in a single firing:

| fuel | failed the screen | admitted to exit | entry-capped | median depth below bar |
|---|--:|--:|--:|--:|
| `gas_cc` | 12,223.0 MW | **5,100.4** | 7,122.6 | **27.77** $/kW-yr |
| `oil` | 5,115.3 MW | 0.0 | 5,115.3 | 24.60 $/kW-yr |
| `gas_ct` | 1,847.4 MW | 0.0 | 1,847.4 | 20.62 $/kW-yr |

What holds the realized exit down to 5,891.9 MW is **not** the screen's
discrimination — it is the R-NEW pipeline's **adequacy admission cap**, which
un-admits candidates until scheduled post-pipeline firm capacity clears the PRM
requirement. Admission is ordered **deepest-loss-first**
(`candidates.sort(key=lambda item: (-item[1], item[0].unit_id))`), and `gas_cc`
carries the deepest per-kW shortfall precisely **because it has the highest
going-forward bar** ($30.00/kW-yr vs `oil` $25.00 and `gas_ct` $21.00) while every
class is being paid the same $0.00 of RA revenue. `gas_cc` therefore consumes the
entire admission budget and `oil`/`gas_ct` — the fuels that actually *did* retire
in New England — never enter the pipeline at all.

**So "too much" and "the wrong fuel" are one defect seen from two sides**: a single
collapsed capacity leg, refracted through a depth-ordered admission cap. That is
also why the 2025 screen rebounds to `gas_cc` net_rev **$208.6/kW-yr** on a
9,385 MW class — the classic cobweb overshoot of the same 2024 over-fire, with the
model's reserve position falling to 1.080 / 1.057 (back inside the zero-cross,
paying $4.0 and $33.9/kW-yr) only *after* it has retired the fleet that made it
long.

## Additions (cumulative 2021→2025) — **decision basis**

_Attribution basis: **decision** (owner decision D-9(ii), signed 2026-08-04 (sitting Addendum K.2)). Scored on the DECISION basis (D-9(ii)). Additions verdicts on this basis are NOT comparable to any additions verdict committed before 2026-08-04, which were scored on the COD basis — the metric means something different. Retirements-side comparability is unaffected. See docs/handoffs/ffr-3s-cod-shifted-scoring-2026-08-04.md._

Basis effect — decided in-window with COD **after** the window (invisible under the COD basis): `{'wind': 1.0, 'solar': 1.028, 'gas_ct': 0.5, 'gas_cc': 1.0}`; commissioned in-window from a **pre-window** decision (dropped under the decision basis): `none` (GW).

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 0.225 | 2.0 | +790% | ❌ FAIL | +23.0 |
| solar | 1.947 | 2.056 | +6% | ✅ PASS | -34.0 |
| gas_cc | 0.0 | 2.0 |  | — | +30.5 |
| gas_ct | 0.162 | 0.5 | +209% | ❌ FAIL | +2.2 |
| storage | 0.642 | 0.0 | -100% | ❌ FAIL | -21.5 |

COD-basis comparison (**not** the graded instrument; model total 3.028 GW vs decision-basis 6.556 GW):

| tech | model GW (COD) | model GW (decision) | band (COD) |
|---|--:|--:|:--|
| wind | 1.0 | 2.0 | ❌ FAIL |
| solar | 1.028 | 2.056 | ❌ FAIL |
| gas_cc | 1.0 | 2.0 | — |
| gas_ct | 0.0 | 0.5 | ❌ FAIL |
| storage | 0.0 | 0.0 | ❌ FAIL |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 22.0 | (n/a) | — | — |
| 2024 | 22.0 | (n/a) | — | — |
| 2025 | 16.5 | (n/a) | — | — |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |
