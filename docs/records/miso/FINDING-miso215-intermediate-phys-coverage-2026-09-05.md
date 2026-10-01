# FINDING miso-215 — THE `phys_*` COVERAGE GAP ON THE INTERMEDIATE-DUTY COHORTS: the gap is real and **58.4 % of MISO's assembled gas capacity** wide, the frozen class p50s ARE the cohorts' own physics (borrowing VALID in 9 of 9 cohort-years), and the arm is ONE zero-DOF field — but the two cohorts where it has any magnitude are exactly the two whose fixed margin the ISO anchor sizes worst, correcting the anchor makes the arm MORE adverse rather than less, and the SAME identification question already governs the margin installed on the ARMED classes; **NO A/B CHARTERED (decision-rule (b) / M-3), NOTHING MINTED**, the anchor's BASIS grain routed to the owner and one measured documentation defect repaired (2026-09-05)

**Keeper UNCHANGED at `2026-09-05-miso-213-layering`** (bundle
`results/calibration/miso213_layering_B`), NOT-YET on C3a-2025 alone (−11.747 %), C3c
ledgered 3/3, C6 attested 41/2. **Zero solve. Nothing minted. No `ScenarioConfig` field
created, no matrix row added, no cell verdict changed.** PREREG
`PREREG-miso215-intermediate-phys-2026-09-05.md` pushed **BLIND** at `cae766ec`, before any
adjudicating statistic of this session and before any arm was designed. Probe
`scripts/probes/_miso215_intermediate_phys_phase0.py` → record
`results/calibration/_miso215_intermediate_phys.json`. Rule 22 `[R-HOLDOUT]`: 2023–2025
only (the probe hard-asserts it).

---

## 0. Verdict in one paragraph

The coverage gap miso-214 §6 named is real, it is far larger than that session could see,
and every cheap objection to closing it fails. `_neutralize_generic_gas_bands` carries
`phys_*` on exactly five gas classes, so `CT_INTERMEDIATE`, `CC_INTERMEDIATE` and
`ST_GAS_INTERMEDIATE` return the documented rule-24 neutral markup 0.0 and
`apply_gas_offer_margin` skips them — **38,501 MW, 58.4 % of MISO's assembled gas capacity
and 90.7 % of its CC fleet**, sitting in the fully fuel-scaled multiplier form the armed
mechanism exists to replace. The arm is exactly **one** `ScenarioConfig` boolean with **zero
free parameters** (K-a passes), and the borrowing it depends on is **valid**: each cohort's
OWN measured marginal heat-rate multiplier — fitted here from CEMS steady-state
input-output slopes, never re-derived — lands within **0.001–0.039** of the parent class
p50 it would borrow, in **9 of 9 cohort-years**, against a pre-registered ±0.06 (K-b silent,
P-3b RIGHT). K-c does **not** fire as written, K-e does not fire. What stops the charter is
**decision-rule (b)**, and the measurement behind it is sharper and different from the prior
I registered. The candidate's whole magnitude is the fixed margin `markup_hr × anchor`, and
**the anchor's placement is unsettled at exactly the grain that sets it**: `3.0492` is
Henry Hub plus a flat `$0.30` basis constant — reproduced here at **+0.2992 / +0.2993 /
+0.2990** in the three years — while the fleet is priced by the per-plant EIA-923 print,
which applies after that series and is invisible to its derive. Against the cohorts' own
delivered fuel the anchor is **within ±0.82 $/MMBtu of every cohort-year MEDIAN** but sits
**0.45–3.29 below the capacity-hour MEAN** of the two cohorts where the arm has any
magnitude. The two readings disagree because the delivered-price distribution is fat-tailed,
and **which of them is the identification point is not this lane's call** — it already
governs the margin installed on the ARMED `CT_PEAKER` and `ST_GAS` classes, whose fixed
margin is $11.91 and $6.24 at the ISO anchor against **$18.25–24.76** and **$8.29–11.02** at
their own mean fuel. **And the easy rescue is refuted before it is proposed**: M-3c shows
that re-anchoring on the cohort's own delivered mean does not reverse the arm's direction,
it deepens it (CT 2023 −1.47 → −4.22 TWh, 2024 −5.28 → −7.04). Under rule 1 `[R-STRUCT]`
the adverse reach is **not** the reason and is not treated as one — closing the gap is
structurally right in FORM and this finding says so. The reason is the order of work:
arming a mis-sized margin across three more classes and 58 % of the gas fleet is not "right
structure first". One measured documentation defect is repaired in passing (the anchor's own
citation comment described the MISO series as a per-plant 923 level; it is not). miso-216's
head is the anchor's basis grain, as an owner question.

## 1. Instrument, and what it can and cannot see (PREREG §2, restated with the checks)

* **Zero solve.** Every number is from committed artifacts and the HEAD fleet chain.
* **Footing check, and it is exact.** The probe reproduces miso-214's independently-derived
  CT numbers **to the last published digit**: cohort 44 plants / **9,333.2 MW**, econ offer
  HR **12.465**, markup **0.000**, true-peaker physical leg **8.649** + markup **3.906**,
  delivered fuel **4.424 / 3.494 / 4.156**, econ capacity-hour share above the anchor
  **0.6055 / 0.435 / 0.840**, static reach **−1.4746 / −5.2847 / +1.4566 TWh**, cap-weighted
  fixed margin **$14.20/MWh**. That agreement is what establishes the T-1 re-point actually
  landed on the miso-213 keeper (below) rather than the control.
* **The `_miso212` import trap is carried forward and closed.**
  `_miso212_south_gas_cost_basis` transitively imports `_miso211_rdt_binding_state`, which
  re-points `_miso134.BUNDLE` to `miso210_clock_B` **at module scope** — the defect
  miso-214 §9 disclosed. The T-1 block sits AFTER the last import and carries a hard assert
  on `miso_zonal_gas_basis_skip_923_priced`, a keeper-only field.
* **Plant-grain model merit is the miso-214 PRICE-TAKING STATIC SCREEN**, not the LP: the
  keeper ships `class_band_hourly / class_hourly / network / reserve_family / storage /
  system` and **no** `unit_hourly/` or `dispatch/`. miso-214 §1 measured the screen at
  **1.41–1.43×** the LP's own CT class energy. Every reach number below is a BOUND.
* **The screen is BLIND to cross-class backfill**, because it holds the price fixed. The
  K-1 exposure (CT displaced → CC picks it up) is therefore an **un-instrumented risk**
  reported as such, never a measurement.
* **CAMPD** read from `data/raw/campd-unit-level/` directly (not `load_campd_hourly`, which
  drops `opTime`), restricted per cohort by the three-way `_unit_family` map the frozen
  derive uses, on the model's fixed non-leap 8760 clock with **no timezone shift** (the
  established MISO-probe convention, disclosed not corrected), CAMPD **gross** against the
  model's **net** tranches unadjusted.
* **Nothing re-derived.** `data/raw/reference/miso_campd_marginal_hr_summary.csv` carries
  rows for MODEL PLANT GROUPS only (`CT_PEAKER` n=249, `CC_REGULAR` n=103, `ST_GAS` n=40) —
  the duty split is a config-time ROUTING downstream of it, so no `*_INTERMEDIATE` p50
  exists and **none was minted** (rule 23 `[R-FROZEN-DERIVE]`). M-3b fits the cohorts' own
  slopes as a DIAGNOSTIC and writes nothing back.
* **Two instrument defects found in the 2023 smoke test and fixed BEFORE the scoring run,
  disclosed**: (i) the M-3b fit weighted each CEMS unit by its whole plant's model capacity,
  so covered MW ran 3× the cohort's own (27,559 against 9,333) — now averaged within a plant
  first, then weighted by plant capacity, giving covered MW **8,779.6 / 24,826.0 / 4,290.8**
  against cohort capacities 9,333.2 / 24,877.0 / 4,290.8; (ii) the resolved delivered price
  could not be separated from the dual-fuel oil-parity step — the exact confound miso-214
  §8(3) disclosed and could not resolve. The probe now builds every year a **second** time
  with `dual_fuel_switching=False`. **Result, and it settles the confound: the oil-parity
  step binds in 0.000 of the econ capacity-hours of all six cohorts in all three years**, and
  the two fuel series agree to ≤ $0.024/MMBtu on the three intermediate cohorts. The
  CT and ST premium over the anchor is a **gas print**, not oil.
* **One asymmetry in §4's own statistics, disclosed**: the cohort MEAN delivered fuel is
  capacity-hour weighted; the p25/p50/p75 are unweighted over the cohort's econ
  tranche × hour matrix. The mean/median divergence §4 turns on is far larger than that
  inconsistency, but it is not zero.

## 2. M-1 — the gap is 58.4 % of MISO's assembled gas capacity

`phys_*` presence, read verbatim from `miso213_layering_B/run_config.json`:

| class | committed | econ_low | econ_high | peak | `phys_*` |
|---|---:|---:|---:|---:|---|
| `CT_PEAKER` | 1.025 | 1.000 | 1.000 | 4.00 | **all four** — 1.025 / 0.687 / 0.691 / 1.00 |
| `CT_INTERMEDIATE` | 1.000 | 1.000 | 1.200 | 3.00 | **NONE** |
| `CC_REGULAR` | 1.005 | 0.950 | 1.080 | 2.25 | **all four** — 1.005 / 0.887 / 1.008 / 2.25 |
| `CC_INTERMEDIATE` | 1.005 | 0.950 | 1.080 | 2.25 | **NONE** |
| `ST_GAS` | 1.000 | 1.000 | 1.000 | 1.00 | **all four** — 1.079 / 0.812 / 0.849 / 1.00 |
| `ST_GAS_INTERMEDIATE` | 1.000 | 1.000 | 1.150 | 2.20 | **NONE** |
| `CC_CHP`, `CT_CHP` | | | | | all four |

Cohort scope off the assembled fleet (capacity is year-invariant on this recipe; CAMPD TWh
by year):

| cohort | plants | capacity MW | share of parent class | econ tranches | cap-w econ offer HR | cap-w markup HR | CAMPD TWh 23/24/25 |
|---|---:|---:|---:|---:|---:|---:|---|
| **`CT_INTERMEDIATE`** | 44 | **9,333.2** | 41.9 % | 264 | 12.465 | **0.000** | 9.23 / 10.15 / 10.83 |
| `CT_PEAKER` remainder (ARMED) | 122 | 12,948.6 | 58.1 % | 243 | 12.555 | 3.906 | 6.84 / 8.23 / 8.02 |
| **`CC_INTERMEDIATE`** | 39 | **24,877.0** | **90.7 %** | 234 | 7.425 | **0.000** | 144.1 / 147.2 / 134.2 |
| `CC_REGULAR` remainder (ARMED) | 5 | 2,543.1 | 9.3 % | 30 | 7.311 | 0.486 | 7.48 / 6.26 / 7.40 |
| **`ST_GAS_INTERMEDIATE`** | 6 | **4,290.8** | 39.0 % | 36 | 10.780 | **0.000** | 12.86 / 15.89 / 13.94 |
| `ST_GAS` remainder (ARMED) | 18/17 | 6,700.2 | 61.0 % | 36/34 | 12.080 | 2.047 | 10.36 / 9.36 / 10.29 |

**The three uncovered cohorts are 38,501.0 MW = 0.5842 of the 65,907 MW of assembled MISO
gas capacity, identically in all three years.** K-e (< 5 % ⇒ immaterial) is silent by a
factor of twelve. The dominant cohort is not the CT one miso-214 found — it is
`CC_INTERMEDIATE`, **90.7 % of MISO's CC class** and 64.6 % of the uncovered capacity, and it
alone carries 134–147 TWh of measured energy, roughly ten times the whole CT class.

## 3. M-3b — the frozen class p50s ARE the cohorts' own physics. Borrowing VALID, 9 of 9

The arm's only numeric content is the parent class's already-registered `phys_econ_low` /
`phys_econ_high`. Whether those are the cohort's physics or a borrowed statistic is what
decides whether the arm is zero-DOF in substance. Measured per cohort from CEMS unit
input-output slopes (`heat = a + b·MW`, `opTime ≥ 0.98`, inside each unit's own p3–p97 load
envelope — the same construction the frozen derive uses), expressed as a multiple of the
class cap-weighted base HR, averaged within a plant then capacity-weighted:

| cohort | own marginal mult 2023 / 2024 / 2025 | borrowed `phys` econ midpoint | max &#124;dev&#124; | K-b bar | verdict |
|---|---|---:|---:|---:|---|
| `CT_INTERMEDIATE` | 0.7117 / 0.7234 / 0.6995 | 0.6890 | **0.0344** | 0.06 | **PASS** |
| `CC_INTERMEDIATE` | 0.9087 / 0.9465 / 0.9271 | 0.9475 | **0.0388** | 0.06 | **PASS** |
| `ST_GAS_INTERMEDIATE` | 0.8216 / 0.8168 / 0.8156 | 0.8305 | **0.0149** | 0.06 | **PASS** |

Covered capacity 8,779.6 / 24,826.0 / 4,290.8 MW — **94 %, 99.8 % and 100 %** of each
cohort's own capacity, on 102 / 98 / 15 fitted CEMS units. **P-3b RIGHT**, and this is the
strongest positive result of the session: the pooled parent p50 is not a convenient
substitute, it is the cohort's own measured incremental burn to within 4 % of the class base
heat rate. **K-a passes too** — the arm is one boolean, MISO-gated, reading numbers that are
already registered and frozen. If the anchor question below is settled, nothing else stands
between this gap and a single-delta A/B.

## 4. M-3 — THE ANCHOR. Its basis is not what its own citation says, and its grain decides the arm

**(a) What the anchor is.** `GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"] = 3.0492` is derived by
`scripts/data/derive_gas_offer_margin_anchor.py` from `data.fuel.trajectories._gas_series`
under `GAS_SERIES_FLAGS["MISO"] = {gas_seasonality, gas_daily_shape, miso_zonal_gas_basis}`.
Reproduced here exactly — annual means **2.8392 / 2.4893 / 3.8190**, mean **3.0492** — and
against the measured annual Henry Hub the derive itself carries (2.54 / 2.19 / 3.52) the
series is:

| year | `_gas_series` mean | measured annual HH | difference |
|---|---:|---:|---:|
| 2023 | 2.8392 | 2.54 | **+0.2992** |
| 2024 | 2.4893 | 2.19 | **+0.2993** |
| 2025 | 3.8190 | 3.52 | **+0.2990** |

A constant, in every year, and it is `GAS_BASIS_DIFFERENTIAL["MISO"] = 0.30` (the
Chicago-Citygate footprint blend). **So the anchor is Henry Hub + a flat $0.30 basis
constant.** The `constants.py` citation comment described it as "per-plant EIA-923 monthly
level + mean-preserving daily shape"; a per-plant 923 level cannot produce a constant offset
from Henry Hub in three different years, and `_gas_series` is ISO-level and cannot carry one
at all. **That comment is corrected in this session** (measured, value untouched, no solve
affected). The keeper prices the fleet by `gas_plant_monthly_fuel_pricing=True` with
`gas_monthly_actuals=False` and `gas_hub_basis_overlay=False`, i.e. the per-plant EIA-923
print — which applies on the `(n_gen, T)` array AFTER the series and is invisible to the
derive. **The anchor and the fleet's delivered price are identified on different bases.**
This is the **BASIS** grain and is a different question from the **ZONAL** grain
(`gas_offer_margin_zonal_anchor`, adjudicated `I` on MISO at miso-119/120), which is not
re-tested and not re-opened.

**(b) How far off it is — and the answer depends on which statistic you ask, which is the
whole point.** Cohort econ capacity-hour delivered fuel against the anchor:

| cohort | MEAN 23/24/25 | mean − anchor | MEDIAN 23/24/25 | median − anchor |
|---|---|---|---|---|
| `CT_INTERMEDIATE` | 4.424 / 3.494 / 4.156 | **+1.375 / +0.445 / +1.107** | 3.305 / 2.698 / 3.658 | +0.256 / −0.352 / +0.608 |
| `CT_PEAKER` rem. **(ARMED)** | 6.340 / 4.671 / 5.619 | **+3.291 / +1.622 / +2.570** | 3.521 / 2.913 / 3.727 | +0.471 / −0.136 / +0.678 |
| `CC_INTERMEDIATE` | 3.167 / 2.844 / 4.536 | +0.118 / −0.205 / +1.487 | 2.827 / 2.408 / 3.519 | −0.222 / −0.641 / +0.469 |
| `CC_REGULAR` rem. **(ARMED)** | 2.897 / 2.726 / 3.958 | −0.152 / −0.323 / +0.909 | 2.797 / 2.405 / 3.638 | −0.252 / −0.644 / +0.588 |
| `ST_GAS_INTERMEDIATE` | 6.342 / 2.692 / 3.910 | **+3.293** / −0.357 / +0.861 | 2.929 / 2.470 / 3.628 | −0.120 / −0.579 / +0.578 |
| `ST_GAS` rem. **(ARMED)** | 4.047 / 4.817 / 5.381 | +0.998 / +1.768 / +2.332 | 2.802 / 2.695 / 3.866 | −0.248 / −0.354 / +0.817 |

**The anchor is within ±0.82 $/MMBtu of EVERY cohort-year median and up to 3.29 below the
capacity-hour mean.** The two readings diverge because the delivered-price distribution is
fat-tailed to the upside, and the divergence is largest on exactly the peaking and steam
classes — the CT true-peaker cohort's mean is $6.34 against a median of $3.52.
**P-3 is half RIGHT and half WRONG, and the wrong half is the informative one**: the
`_gas_series`-vs-Henry-Hub leg is RIGHT (all three within ±0.35, at +0.299), but the
"≥ +0.30 in ≥ 8 of 9 cohort-years" leg is **WRONG** — on the mean it is 6 of 9 (CT 3/3,
ST 2/3, CC 1/3) and on the median 0 of 9. The CC cohort, which is 64.6 % of the uncovered
capacity, is **well anchored**.

**(c) What the anchor SIZES — the owner-facing number.** The mechanism's economic content is
a fixed margin `markup_hr × anchor` ($/MWh). `markup_hr` is measured physics; the anchor is
the identification point, so the margin is proportional to it:

| cohort | markup HR | source | fixed margin **@ anchor** | @ own MEAN fuel 23/24/25 | ratio |
|---|---:|---|---:|---|---|
| `CT_INTERMEDIATE` | 4.6574 | candidate | **$14.20** | 20.61 / 16.27 / 19.36 | 1.45 / 1.15 / 1.36 |
| `CT_PEAKER` rem. | 3.9059 | **ARMED (keeper)** | **$11.91** | **24.76 / 18.25 / 21.95** | **2.08 / 1.53 / 1.84** |
| `CC_INTERMEDIATE` | 0.4938 | candidate | **$1.51** | 1.56 / 1.40 / 2.24 | 1.04 / 0.93 / 1.49 |
| `CC_REGULAR` rem. | 0.4862 | **ARMED (keeper)** | **$1.48** | 1.41 / 1.33 / 1.92 | 0.95 / 0.89 / 1.30 |
| `ST_GAS_INTERMEDIATE` | 2.4517 | candidate | **$7.48** | 15.55 / 6.60 / 9.59 | 2.08 / 0.88 / 1.28 |
| `ST_GAS` rem. | 2.0475 | **ARMED (keeper)** | **$6.24** | 8.29 / 9.86 / 11.02 | 1.33 / 1.58 / 1.77 |

**The question is live on the KEEPER, not only on the candidate.** If the identification
point is the class's own capacity-hour mean delivered fuel, the armed `CT_PEAKER` margin is
installed 35–52 % below what the mechanism's own identity requires, and the armed `ST_GAS`
margin 25–43 % below. If it is the class median, all six are within a few dollars and there
is nothing to fix. **This lane does not adjudicate that** — re-identifying the anchor is a
mechanism change touching five already-armed MISO classes (and, in kind, every ISO), which
rule 23 `[R-FROZEN-DERIVE]` does not reach and rule 25 `[R-ISO-SCOPE]` forbids doing
ISO-locally. It goes to the owner as §8's question.

**(d) M-3c — the easy rescue, refuted before it was proposed.** The PREREG's own
counterfactual: re-run the static reach with the anchor replaced, per cohort-year, by that
cohort-year's own cap-weighted delivered mean. If the arm's direction were an artefact of a
too-low anchor, correcting it would reverse or null the reach. **It does the opposite:**

| cohort | reach @ ISO anchor 23/24/25 | reach @ own delivered mean | pre-registered "vanish share" |
|---|---|---|---|
| `CT_INTERMEDIATE` | −1.475 / −5.285 / +1.457 | **−4.218 / −7.043 / −2.805** | −1.860 / −0.333 / −0.926 |
| `CC_INTERMEDIATE` | +0.458 / +0.029 / +0.900 | +0.375 / +0.212 / −0.236 | +0.181 / −6.267 / +0.738 |
| `ST_GAS_INTERMEDIATE` | −0.702 / −1.350 / +0.506 | **−4.494 / −0.694 / −0.593** | −5.402 / +0.486 / −0.170 |

**The pre-registered M-3c estimator is MIS-SPECIFIED and its verdict is reported exactly as
frozen, not renegotiated.** "The share of the |screen delta| that vanishes at the cohort's
own anchor" presumes the reach is roughly linear in the anchor; it is not — merit is a
threshold, so a mean-preserving anchor shift does not preserve energy, and the share comes
out negative (the reach grows). **K-c therefore does NOT fire on its own wording** (the
vanish leg clears the 0.70 bar in 0, 1 and 0 of 3 years for the three cohorts) even though
its fuel-gap leg fires 3 / 1 / 2 of 3. The substantive content survives the mis-specification
and points the other way from my prior: **a higher, better-placed anchor makes the arm more
adverse, not less.** The mechanism is why — §5.

**(e) Why the direction is what it is.** The reprice shifts each offer by
`markup_hr × (anchor − F(t))`, so it LOWERS the offer wherever delivered fuel is above the
anchor and RAISES it below. On `CT_INTERMEDIATE` the cap-weighted MEAN shift is
**−$6.35 / −$2.03 / −$5.02 /MWh** — the offer is on average CHEAPER — and the screen still
loses energy in 2023 and 2024. The raised share of econ capacity-hours is 0.395 / 0.565 /
0.160. The reading is that **the cohort is marginal in the low-fuel hours**, which are
exactly the hours the margin form prices UP; in the high-fuel hours where it prices down the
cohort is already in or far out of merit. A fixed $/MWh margin is *supposed* to behave this
way — that is what a net-revenue margin means — so this is a property of the mechanism, not a
defect, and it is why a higher anchor deepens the loss.

## 5. M-2 — band scope, and the peak leg

The reach, measured ECON-ONLY and ECON+PEAK (TWh on the price-taking screen, a bound):

| cohort | econ-only 23/24/25 | econ+peak 23/24/25 | econ tranches repriced | fixed margin |
|---|---|---|---:|---:|
| `CT_INTERMEDIATE` | −1.475 / −5.285 / +1.457 | −1.474 / −5.285 / +1.457 | 264 | $14.20 |
| `CC_INTERMEDIATE` | +0.458 / +0.029 / +0.900 | +0.458 / +0.029 / +0.900 | 234 | $1.51 |
| `ST_GAS_INTERMEDIATE` | −0.702 / −1.350 / +0.506 | −0.703 / −1.352 / +0.507 | 36 | $7.48 |

**The peak leg is inert on the screen** (adding it moves nothing past the fourth decimal) —
those tranches essentially never clear — but it is **not** inert on price, which is what C3c
scores. `CT_INTERMEDIATE`'s peak band 3.00 against a borrowed `phys_peak` 1.00 is a markup of
2.00 × base HR 12.0393 = 24.08 MMBtu/MWh, a **$73.4/MWh** fixed margin replacing a fuel-scaled
wall; at the cohort's own delivered fuel that **LOWERS the peak offer by $29.03 / $8.69 /
$23.81 /MWh**, and `ST_GAS_INTERMEDIATE`'s by $38.96 / −$4.25 / $10.23. `CC_INTERMEDIATE`'s
peak 2.25 equals `CC_REGULAR`'s `phys_peak` 2.25, so its markup clips to 0 and its peak leg
is exactly inert. **P-2 RIGHT on all four legs** (CT $10–16 → $14.20; ST $6–13 → $7.48; CC
$1.0–2.0 → $1.51; CT peak margin $70–80 → $73.4 and a ≥ $20/MWh lowering in 2023 and 2025 →
$29.03 and $23.81). **The pre-commitment to ECON-ONLY stands**: an arm that lowers a
deliberate scarcity wall by $24–29/MWh in the two years C3c is already ledgered is not
something to slip in beside a form repair.

## 6. M-4 — the rule-19 census

Five mechanisms already price or force the `CT_INTERMEDIATE` econ tranches, and none of them
is the one that is missing:

1. **the band multiplier itself** — `econ_low` 1.00 → `econ_high` 1.20 on the plant's own
   base HR × its delivered fuel;
2. **the P1 startup amortization** — `tranche_startup_amortization` +
   `tranche_startup_measured_runs` + `tranche_startup_conditional_runs`, all True. Its
   actual value needs the P0 dispatch the keeper does not ship, so what is measured is its
   v3 measured-horizon value with no P0 shortening — a strict LOWER BOUND, since the
   endogenous P0 run may only shorten the horizon: **$1.942/MWh** cap-weighted on
   `CT_INTERMEDIATE` econ, **$2.579** on the true-peaker cohort, **$0.000** on both CC and
   ST cohorts (no fast-start horizon);
3. **the per-plant EIA-923 delivered-fuel path** (`gas_plant_monthly_fuel_pricing`), which
   since miso-213 is the sole regional signal on every MISO gas cell in a backcast;
4. **`ct_intermediate_split`** itself — the routing that put them on the flatter curve;
5. **`reliability_floor`** — six armed `CT_PEAKER` `netload` limbs, h15–21, one per zone;
   the ONLY `CT_PEAKER` D-2 row.

`gas_offer_net_revenue_margin` reaches **none** of them. **P-4 is mixed**: the count leg is
RIGHT (five, ≥ 3) and the "no existing mechanism converts this cohort's markup to a fixed
margin" leg is RIGHT; the magnitude leg is **WRONG** — I predicted the startup amortization
at ≥ $2/MWh and its lower bound is $1.942.

## 7. The decision, kill by kill, exactly as pre-registered

| kill | bar | measured | verdict |
|---|---|---|---|
| **K-a** single field, zero free parameters | one boolean, values = frozen parent p50s | one MISO-gated boolean at `_offer_curve_for_group`; no new number | **PASS** |
| **K-b** borrowing validity | cohort own marginal within ±0.06 of borrowed p50 | max &#124;dev&#124; 0.0388, 9 of 9 cohort-years | **PASS** |
| **K-c** the anchor is the object | gap ≥ 0.30 in ≥ 2 yr **AND** vanish ≥ 0.70 in ≥ 2 yr | gap 3/1/2 of 3; vanish 0/1/0 of 3 | **DOES NOT FIRE** (estimator mis-specified, §4d) |
| **K-d** protective-gate exposure | cannot move the object favourably in ≥ 2 yr **AND** a protective face at risk | CT adverse 2 of 3 and ST adverse 2 of 3, on classes 5–35 % under actual; C8 `CT_PEAKER`-2023 already 0.2044 vs the 0.15 budget and every material CT arm cuts merchant CT energy; CC adds energy in the two years CC is over actual, with `CC_REGULAR`-2024 at +7.419 of ±8.00 | **FIRES** |
| **K-e** materiality | uncovered < 5 % of gas capacity | **0.5842** | **DOES NOT FIRE** |

**NO A/B IS CHARTERED**, and the reason is **decision-rule (b)**, not K-d.

**Rule 1 `[R-STRUCT]` is applied, not evaded.** Closing the coverage gap is structurally
right in FORM and this finding says so plainly: there is no market reason for an
intermediate-duty gas unit's offer to be fully fuel-scaled while the same technology's
peaking curve is decomposed into measured physics plus a margin, and `_MISO_OFFER_CURVE`'s
own comment already accepts that reading for `CT_PEAKER`'s neutral 1.0 econ bands. **The
adverse reach is therefore NOT the reason and is not treated as one.** K-d is reported
because it was pre-registered and because its protective half — C8, a rule-20 gate already
over its peaker budget and surviving only on the conditional provenance+shape route — is a
genuine structural signal rather than a fit one; it corroborates, it does not decide.

**What decides is that decision-rule (b) is not satisfied.** The arm's entire magnitude is
`markup_hr × anchor`. §4 shows the anchor is Henry Hub + a flat $0.30, that its own citation
described it as something it is not, and that whether it belongs at the fleet's median or
its capacity-hour mean changes the installed margin by 25–52 % on precisely the two classes
where this arm has magnitude — **a question that already governs the ARMED `CT_PEAKER` and
`ST_GAS` margins**. Arming a mis-sized margin across three more classes and 58 % of MISO's
gas capacity before that is settled is the opposite of "right market structure first". And
§4d removes the alternative reading: correcting the anchor does not rescue the arm's
direction, it deepens it — so this is not a case where the object is one adjustment away.

**The gap is NOT rejected.** No cell verdict moves, no field is minted, and the object stays
on the queue with its two prerequisites now measured and named: the anchor's basis grain
(owner), then the arm, which K-a and K-b say is ready the moment the anchor is.

## 8. The owner question this session routes

**At what grain should `GAS_OFFER_MARGIN_ANCHOR_BY_ISO` be identified?** Today it is the
mean of an ISO-level Henry-Hub-plus-flat-basis series. The fleet pays the per-plant EIA-923
print, whose class capacity-hour means sit +0.9 to +3.3 $/MMBtu above it for `CT_PEAKER` and
`ST_GAS` and within ±0.9 for `CC_REGULAR`, while every class's MEDIAN sits within ±0.82.
The consequence is the size of the fixed margin the armed mechanism installs (table §4c).
Three properties make this owner-court rather than a lane lever: it is a change to a
mechanism's identification, not a re-derivation on new source data (rule 23 does not reach
it); it moves five already-armed MISO classes at once; and PJM, CAISO, NYISO and NEISO carry
the same construction, so an ISO-local answer would be a rule-25 boundary crossing. **This
is the BASIS/CLASS grain and is distinct from the ZONAL grain** already adjudicated `I` on
MISO (`gas_offer_margin_zonal_anchor`, miso-119/120), which is untouched and not re-opened —
and which miso-213 made doubly moot in a MISO backcast by removing the zonal increment from
every 923-priced cell.

## 9. My prior, scored against interest

* **P-1 mostly RIGHT, one leg WRONG.** `CC_INTERMEDIATE` largest, ≥ 60 % of the CC class and
  ≥ 15 GW → **90.7 % / 24.9 GW, RIGHT**. Three cohorts ≥ 35 % of assembled gas capacity →
  **58.4 %, RIGHT**. `ST_GAS_INTERMEDIATE` < 4 GW → **4.29 GW, WRONG**.
* **P-2 RIGHT on all four legs** (§5).
* **P-3 half RIGHT, half WRONG** (§4b), and the wrong half is the one that matters: the CC
  cohort — 64.6 % of the uncovered capacity — is well anchored, which I did not predict.
* **P-3b RIGHT** (§3), the session's strongest positive result.
* **P-4 mixed**: count and no-existing-mechanism legs RIGHT, the ≥ $2/MWh startup leg
  **WRONG** at $1.942 (§6).
* **P-5 right outcome, WRONG reasoning.** I put P(charter) at 0.25 and expected K-c to fire
  because "most of the static reach is the anchor's position in the fuel distribution".
  **K-c did not fire, my own M-3c estimator was mis-specified for a threshold statistic, and
  the substantive result is the opposite of the mechanism I predicted**: re-anchoring on the
  cohort's own fuel makes the arm MORE adverse. The charter fails for a reason I named in the
  right place (decision-rule (b)) by an argument I did not have when I wrote it.

## 10. Reported against interest

1. **The static screen is a loose bound in both directions** (1.41–1.43× the LP's own class
   energy, miso-214 §1) and it is **blind to cross-class backfill**, so the K-1 exposure that
   K-d leans on is an un-instrumented risk, not a measurement. The `CC_INTERMEDIATE` arm's
   2024 reach is **+0.029 TWh** against a stated 0.58 TWh of `CC_REGULAR`-2024 headroom —
   5 % of it, on a bound that runs 1.4× the LP. **K-d's K-1 half is weak for the CC cohort
   and I say so**; it fires on the 2025 direction (+0.900 TWh into a class already over
   actual) and on the CT/ST cohorts, not on that cell.
2. **The C1 direction context in K-d is my own summation of the run payload's `volErr`
   zone-months, NOT the C1 scorer's own normalization.** My sums give `CT_PEAKER` −31.2 /
   −4.9 / −12.6 % and `CC_REGULAR` −2.0 / +4.1 / +2.9 %, while the pre-registered face for
   `CC_REGULAR`-2024 is +7.419 of ±8.00. The SIGNS agree and only signs are used; the
   magnitudes are not comparable and are not quoted as C1 results.
3. **The anchor reading turns on mean-vs-median and I did not anticipate that.** On the
   median the anchor is fine everywhere (max |gap| 0.82) and there is arguably nothing to
   route. I report both, state that the mean is capacity-hour weighted while the percentiles
   are not, and leave the choice to the owner rather than picking the statistic that makes my
   §7 argument strongest.
4. **A material class whose arm is nearly inert is a weak place to stop.** `CC_INTERMEDIATE`
   is 64.6 % of the uncovered capacity, is well anchored, and its markup is only 0.0630 /
   0.0720 (a $1.51/MWh margin) because its registered bands sit within 0.07 of
   `CC_REGULAR`'s measured phys. A CC-only arm would be defensible on §4's own logic and is
   **not** chartered here — because it would spend a solve on a change the screen puts at
   +0.03 to +0.90 TWh with no structural claim beyond consistency, and because splitting the
   gap by cohort would leave the CT/ST half arguing the anchor question from a worse
   position. That is a judgement, and a reader may reasonably disagree with it.
5. **The M-3b fit covers 94–100 % of each cohort's capacity but is an unweighted mean of
   unit slopes within a plant**, because CAMPD carries no per-unit model MW. A plant whose
   units differ in size is mis-weighted internally; the cohort-level weighting is correct.
6. **The dual-fuel separation is a counterfactual, not a decomposition.** `fp_gas` is the
   same resolution with `dual_fuel_switching=False`; for the three intermediate cohorts it
   agrees with the resolved price to ≤ $0.024 and the oil step never binds, which is the
   result quoted. For `ST_GAS` remainder 2023 the no-switch price is HIGHER (6.377 vs 4.047)
   — disarming the switch leaves some dual-fuel units on their oil default — so that column
   is not "the gas print" for every cohort and is not read as one.

## 11. Governance

Rule 15 `[R-DASHBOARD]`: **zero-solve session — no run produced, none registered**; the
deliverables are this finding, the PREREG, the probe, its JSON record, the log entry, the
§5.4 queue stamp and the MISO shard cells. Rule 22 `[R-HOLDOUT]`: 2023–2025 only (the probe
hard-asserts it). Rule 16 `[R-ALLYEARS]`: all three training years measured in one pass.
Rule 25 `[R-ISO-SCOPE]`: only `docs/codebase-site/data/mechanism-matrix/MISO.js` is edited;
no field added, so no base row and no other shard is touched (rule 28c not engaged). **PJM
and CAISO carry the same `*_INTERMEDIATE` coverage gap in kind — they share
`_neutralize_generic_gas_bands` and the per-ISO merge pattern — and that is their lanes' `U`,
never MISO's business; no verdict here fills their cells.** Rule 28(b): the two cells this
session produced evidence about — `gas_offer_net_revenue_margin` (cell UNCHANGED at `K`;
evidence about the mechanism's REACH and its IDENTIFICATION, not a re-verdict) and
`offer_curve_by_group` (cell UNCHANGED at `K`; the container holding the three uncovered
curves) — are updated in this session. Rule 13 `[R-MEASURED]`: CAMPD conduct and the
EIA-923 print path are read as DIAGNOSTICS only; no measured outcome is fed back as an input.
Rule 23 `[R-FROZEN-DERIVE]`: no derive script run and no artifact rewritten — the frozen
marginal-HR table is read, and M-3b's cohort fits are diagnostics that go nowhere near it.
Rule 24 `[R-REGISTRY]`: no new tunable. Rule 27 `[R-PUSH]`: every file edited locally and
blob-verified after push; the one core-file edit (`config/constants.py`, 4,742 → 4,756
lines) is a **comment-only correction with the constant's value asserted unchanged**.
DO-NOT-REDO honoured: `gas_hub_basis_overlay` (R), `miso_offer_level_dispersion` (R),
`miso_offer_spread_anchored` (I), `miso_rdt_measured_limit` (R),
`miso_south_gas_delivered_cost_basis` (R), `gas_offer_margin_zonal_anchor` (I — the ZONAL
grain) are neither re-tested nor re-opened; the average-vs-marginal delivered-cost convention
and the D-2 5(i) seam-response object stay OWNER-COURT; the South price separation
(miso-211 D-3) is untouched; the CT commitment-bridge / min-load AS family closed by
measurement at miso-214 is not re-opened.

**The miso-214 standing result is not undone.** 62–70 % of the CT energy the model misses was
produced by the real market **below the plant's own delivered cost, at the market's own
price** (41–49 % on the strictest single substitution; 44–60 % paying the better of DA and
RT), and that energy is **not reachable by any offer or price mechanism**. Had this arm been
chartered it would have addressed at most **bucket C** (0.167 / 0.257 / 0.167 of the missed
MWh) and part of **bucket A** (0.131 / 0.130 / 0.215). **No CT C1 movement from this family
should ever be presented as closing the class's gap.**

Next shorthand: **miso-216**.
