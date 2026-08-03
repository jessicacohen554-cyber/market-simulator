# FINDING miso-118 — all four `CC_CHP` plant outliers are the SAME basis artifact, proven by an exact decomposition: the comparator's denominator reports LESS gross electricity than the plants generate net. No charter, no solve. And one genuinely new single-plant defect found in the sweep — pointing the OTHER way

Session miso-118, 2026-08-03, branch `claude/miso-118-backcast-calibration-f0ngwe`,
off `origin/main` at `10c23ab`. **NO LP SOLVED.** Every number is read from
committed artifacts: the CURRENT keeper bundle
`results/calibration/miso117_ctheatrate_B` (its `run_config.json` only),
`chp_power_only_heat_rates_MISO.csv`, `parasitic_load_factors.parquet`,
`data/raw/campd-unit-level/`, EIA-923 via the model's own loader, and the
repo's own fleet build. Probe
`scripts/probes/_miso118_cchp_plant_outlier_basis.py` (re-runnable, ~6 min,
zero LP); transcript
`results/calibration/PROBE-miso118-cchp-plant-outliers-2026-08-03.txt`;
pre-registration
`results/calibration/PREREG-miso118-cchp-plant-outliers-2026-08-03.md`, written,
committed **and pushed** (`d94905f`) before the probe ran.

**Keeper UNCHANGED** (`2026-08-03-miso-117b-ct-heat`). Rule 15: no run
produced, nothing to register.

## 0. Verdict

**BASIS-ARTIFACT on all four plants. No charter, no solve.** The
pre-registered decision rule returns the same verdict for 10745, 55089, 55259
and 55088, and the mechanism behind it is one thing, measured exactly.

| plant | name | model cap | miso-116 ratio (2023) | **`R_basis`** 2023 / 2024 / 2025 | verdict |
|---|---|---:|---:|---|---|
| 10745 | Midland Cogeneration Venture | 1,479 MW | 0.810 | 1.000 / **1.006** / **0.995** | BASIS |
| 55089 | Taft Cogeneration | 739 MW | 0.653 | 1.000 / **0.998** / **1.013** | BASIS |
| 55259 | Whiting Clean Energy | 513 MW | 0.802 | 1.000 / **1.071** / **1.026** | BASIS |
| 55088 | Dearborn Industrial Generation | 350 MW | 0.817 | 1.000 / **1.006** / **0.942** | BASIS |

`R_basis` is the model's loaded rate over a comparator built from two
independent meters — CAMPD fuel over EIA-923 net MWh — **neither of which is
the eGRID number the model loads**. All four land inside the pre-registered
`[0.90, 1.10]` band in 3 of 3 years. The pre-registered band for a REAL error
was "outside `[0.85, 1.15]` in ≥ 2 of 3 years"; no plant comes near it.

**The 2023 column is circular and is not evidence.** eGRID total heat equals
CEMS total heat for these plants (`cems_vs_egrid_total` = 1.00000, the
artifact's own validation column) and `net923(2023)` equals `PLNGENAN`, so
`R_basis(2023) = 1.000` **by construction**. The informative years are 2024 and
2025, where the model holds a frozen eGRID-2023 vintage while both meters move
on their own. All four plants are in band **2 of 2** informative years, which
is the number that carries the verdict.

## 1. The decomposition — the ratio is fully accounted for, to 2×10⁻⁶

The pre-registered completeness identity closes exactly:

```
ratio(miso-116)  =  A_cems  ×  F_family  ×  G_gross
    A_cems   = eGRID total heat / CEMS total heat     (meter agreement)
    F_family = CEMS total heat / CEMS heat in family CC   (comparator truncation)
    G_gross  = CEMS gross load in family CC / PLNGENAN    (gross-load coverage)
```

2023, and `max |A·F·G − ratio| = 0.000002` across all 12 plant-years:

| plant | ratio | `A_cems` | `F_family` | **`G_gross`** |
|---|---:|---:|---:|---:|
| 10745 | 0.810 | 1.0000 | 1.0009 | **0.8088** |
| 55089 | 0.653 | 1.0000 | 1.0000 | **0.6526** |
| 55259 | 0.802 | 1.0000 | 1.0000 | **0.8024** |
| 55088 | 0.817 | 1.0000 | 1.6465 | **0.4960** |

**There is no unexplained residual for a model defect to occupy.** For three of
the four plants the entire gap is one term: `G_gross`.

## 2. Why `G_gross < 1` is a proof, not an estimate

`G_gross` is CEMS **gross** generation over eGRID **net** generation.
**Gross generation is never below net generation** — station service is
subtracted from gross to get net, so the ratio cannot be less than 1 for a
matched population. Measured, it is **0.65 to 0.81**. The comparator's
denominator is therefore reporting *less electricity than the plants
demonstrably produced*, and the only possible reading is that the CEMS
gross-load channel does not cover the plants' full electric output.

The unit anatomy says where it goes (2023):

| plant | CEMS units | CEMS gross MWh | EIA-923 net MWh | gross/net |
|---|---|---:|---:|---:|
| 10745 | 12 × `Combined cycle` (+ 6 boilers, no output) | 7,890,512 | 9,755,682 | **0.809** |
| 55089 | 3 × `Combined cycle` | 3,861,558 | 5,917,200 | **0.653** |
| 55259 | 2 × `Combined cycle` | 2,267,488 | 2,825,923 | **0.802** |
| 55088 | 2 × `Combined cycle`, 1 × `Combustion turbine` (+3 boilers, no output) | 3,648,140 | 5,259,825 | **0.694** |

Every CEMS unit at these plants is a *fuel-burning* one. The steam turbines
that convert their exhaust heat into electricity burn no fuel of their own, are
not Part-75 monitored, and so contribute **no `grossLoad` at all** — while
EIA-923 counts every MWh they make. The residual 0.65–0.81 is close to the
customary two-thirds combustion-turbine share of a combined cycle's output,
which is what a missing steam-turbine leg looks like.

**This is exactly the defect `FINDING-miso98-chp-sector-ab-2026-07.md` §6.1
already named** as the reason the CEMS route was abandoned for CHP heat rates:
"a cogen's CEMS gross-load channel misses the units EIA-923 counts, so the
reconciliation falls out of band on every cogen." miso-116 §3 then compared
against that channel anyway, one layer down at plant grain.

## 3. Independent corroboration — the repo had already recorded it

`data/raw/_processed-legacy/parasitic_load_factors.parquet`, produced by a
**different derive for a different purpose** (`derive_parasitic_factors`,
EIA-923 net over CAMPD gross), carries these plants:

| plant | year | CAMPD gross | EIA-923 net | net/gross | status |
|---|---|---:|---:|---:|---|
| 10745 | 2022 | 6,145,519 | 7,411,985 | **1.206** | `class_default` / `out_of_band` |
| 55088 | 2022 | 3,256,234 | 4,447,879 | **1.366** | `class_default` / `out_of_band` |
| 55259 | 2023 | 2,267,488 | 2,825,923 | **1.246** | `class_default` / `out_of_band` |
| 55259 | 2024 | 2,351,750 | 3,059,814 | **1.301** | `class_default` / `out_of_band` |
| 55259 | 2025 | 2,147,482 | 2,728,052 | **1.270** | `class_default` / `out_of_band` |

Every row present is the same impossible ordering, every row is flagged
`out_of_band`, and the derive **refused** the measurement and fell back to its
class default. 55089 carries no row at all. The comparator miso-116 §3 used was
already, independently, known to be broken at these plants.

## 4. The REAL-branch hypotheses, all tested, all negative

* **H-C, vintage staleness — DOES NOT FIRE.** The plants' own measured rates
  move **1.1 / 1.4 / 6.6 / 6.7 %** year-on-year against the pre-registered 10 %
  threshold, so one frozen eGRID-2023 vintage is a fair 2024–2025 rate at all
  four. (Prediction 5 confirmed.)
* **H-D, mis-key — DOES NOT FIRE.** **0** mismatches over all 3 years: every
  loaded generator carries the artifact's published rate to 1e-6, with a
  within-plant spread of exactly 0.0000. 55088's `CT_CHP` row correctly takes
  the same plant-level rate the artifact publishes for it.
* **H-B, comparator truncation — fires on 55088 only** (`F_family` = 1.65),
  and is a property of the comparator, not the model.

## 5. The one genuinely new item — and it points the OPPOSITE way

Plant **55088 Dearborn Industrial Generation** burns **13–17 % of its CEMS
fuel in three `Other boiler` units that report ZERO gross load** — direct-fired
host process fuel that makes no electricity at all. That fuel sits inside the
topping-cycle rate the model charges Dearborn's `CC_CHP` (350 MW) **and**
`CT_CHP` (165 MW) tranches:

| year | total CEMS fuel | zero-output boiler fuel | loaded rate | power-train-only rate | over-charge |
|---|---:|---:|---:|---:|---:|
| 2023 | 43,901,179 MMBtu | 7,306,886 (16.6 %) | 8.3465 | 6.9573 | **+20.0 %** |
| 2024 | 47,007,101 MMBtu | 6,967,354 (14.8 %) | 8.3465 | 7.0704 | **+18.0 %** |
| 2025 | 33,518,925 MMBtu | 5,637,389 (16.8 %) | 8.3465 | 7.3702 | **+13.2 %** |

The derive's own scope section is explicit that adding the credit back is
correct for a **topping cycle**, where "the steam is a free co-product, so no
fuel is avoided by making it" — and is *not* the right rate where fuel is fired
directly to steam. Its guard is eGRID's `thermal_share` against a 0.50 unfired
ceiling; Dearborn's `thermal_share` is **0.2396**, comfortably under, so the
gate passes it. eGRID's plant-level allocation cannot see that the plant is a
**hybrid** — a topping CC+CT train plus a package boiler — and CEMS can, at
unit grain.

**It does not generalise.** Swept across all **14** `ok`-flagged MISO CHP
plants CEMS covers in 2023, exactly **one** carries more than 1 % of its fuel in
zero-output units: 55088, at **515 of 6,357 MW**. MCV is the only other plant
with any such fuel at all, and at 80,561 MMBtu it is **0.09 %** — immaterial.

**This is NOT chartered here.** Three reasons, stated so a successor does not
mistake a named item for an authorised one: (a) it is a *different question*
from the pre-registered one and this session has no decision rule for it;
(b) fixing it means changing the derive's **scope gate**, which needs its own
pre-registration and its own admissibility argument (rule 23
`[R-FROZEN-DERIVE]` permits a logic change on measured grounds, but never a
re-derive aimed at a residual); (c) it is one plant of 515 MW — direction is
established, materiality is not. Admissible on rule 14 `[R-ACCURATE]` grounds
**only**; it must never be justified by what it does to a residual.

## 6. A pre-registered kill that was mis-specified, reported both ways

**K3 as written fired on all four plants, and it should not have.** It required
`|net923(year)/PLNGENAN − 1| ≤ 0.02` in *every* year. `PLNGENAN` is the frozen
eGRID-2023 vintage, so in 2024 and 2025 the test compares two **different
years'** net generation and fires mechanically (0.831–1.104). The identity the
derive actually claims — and the one K3 was written to check — is the
**same-year** one, `net923(2023) / PLNGENAN(eGRID2023) = 1.000000`, which
**passes exactly** at all four plants.

The probe prints the verdict under **both** readings and the transcript carries
both, because a kill that fires must not be quietly re-specified into one that
does not:

* **K3 as written** → INDETERMINATE ×4.
* **K3 corrected (same-year)** → BASIS-ARTIFACT ×4.

The correction is a specification repair with an independent justification (it
is the derive's own published claim, and `HR_match` never touches `PLNGENAN` in
any case), not a band moved to reach a verdict. The verdict at §0 is stated on
the corrected reading and this paragraph is the reason it is allowed to be.

## 7. Kills — all pre-registered, all resolved

* **K1 reproduction — PASSED EXACTLY.** 14 matched plants, 5,852 MW, the same
  four plant codes, 52.7 % of matched capacity, and the four 2023 ratios
  **0.810 / 0.653 / 0.802 / 0.817** — miso-116 part E reproduced before any
  correction was applied. It reproduces on the *new* keeper
  (`miso117_ctheatrate_B`) as well as the one miso-116 read
  (`miso109_hy_level_B`), which independently confirms miso-117's Phase-0 scope
  check that `measured_ct_heat_rates` touches `CT_PEAKER` only.
* **K2 flag fidelity — PASSED.** Both heat-rate flags READ from the keeper's
  `run_config.json` (`measured_chp_heat_rates=True`,
  `measured_ct_heat_rates=True`), asserted at runtime, never hardcoded.
* **K3 — FIRED as written**, resolved at §6.
* **K4 CEMS completeness — PASSED.** `cems_vs_egrid_total` = 1.00000 on all
  four.
* **K5 materiality — recorded.** `CC_CHP` is **3.03 / 3.02 / 2.46 %** of MISO
  load in the keeper's own P1, above the rule 20 2 % floor.

## 8. Predictions — 4 of 5 confirmed, 1 refuted

1. **H-A fires on ≥ 3 of 4 plants** — CONFIRMED, and stronger: **4 of 4**,
   `G_gross` 0.496–0.809.
2. **Decomposition closes to ≤ 0.005** — CONFIRMED at **0.000002**.
3. **`R_basis` in `[0.90, 1.10]` on all four** — CONFIRMED, 3/3 years each.
4. **55088's `CT_CHP` row is the open sub-item, surviving as a note** —
   **REFUTED IN SUBSTANCE.** 55088 *is* the one plant with a real defect, but
   not the one predicted: the prime-mover sharing is fine (H-D found the rate
   correctly applied), and the actual defect is a direct-fired boiler's process
   fuel inside a topping rate (§5) — which the prediction did not anticipate
   and which affects the `CC_CHP` row just as much as the `CT_CHP` one.
5. **H-C does not fire** — CONFIRMED, max 6.7 % against a 10 % threshold.

## 9. What this closes, and what must NOT be done with it

**CLOSED.** miso-116 §7's item 2 — "the 4 plant-level `CC_CHP` heat-rate
outliers (52.7 % of matched capacity below 0.85× CAMPD)" — is **adjudicated a
basis artifact and struck from the MISO queue**. Do not re-open it on this
comparator, and do not quote the 0.810 / 0.653 / 0.802 / 0.817 ratios as a model
result: they measure the CEMS gross-load channel, not the model.

**Standing bars, carried forward unchanged:**

* **Do NOT** relax the h14-21 `CT_PEAKER` reliability-floor limb to buy back C1
  volume (rules 1 / 14; miso-106 keeper note), and do **not** re-derive
  `min_stable_pct` against a residual (rules 23 / 25).
* **Do NOT** re-open the `CC_CHP` volume question or the
  `CT_PEAKER`/`ST_GAS`/`CC_REGULAR` trough-quantity question (miso-115/116), or
  quote the `CT_CHP`/`ST_CHP` ratios (VOID on coverage).
* **Do NOT** arm `miso_cc_coal_rebalance`, re-license `miso_firm_import_floor`
  or `miso_pjm_lmp_import_pricing`, charter the seam hod mis-shape, or re-open
  the top-decile convexity deficit (miso-89, ledgered).
* The regulated-PRB self-commitment family stays **SPENT** (miso-111 `R`,
  miso-112 `R`, miso-113 `I`).
* **C7 `COAL_PRB` is untouched by this session and no successor should expect a
  CHP-side lever to reach it.** It still needs the overnight dispatch
  *distribution* WIDENED (miso-113) — the data-blocked miso-78/79 congestion +
  sub-hourly-RT lane.
* **Do NOT re-run any derive script** on the strength of §5 (rule 23). The
  finding is documented; the fix is a chartered successor's job.

## 10. The named successors, in order

1. **`dual_fuel_switching`** (queue item 5, MISO cell `U`) — winter-event
   pricing candidate, Elliott-class, untested at MISO and needing its own
   measured identification. Unaffected by this session.
2. **`gas_offer_margin_zonal_anchor`** (cell `U`) — the matrix notes MISO's lane
   may adjudicate `I` **ex ante on the no-LP bar with zero solves** (spread
   0.332, coupled topology). That screen comes before any solve is considered.
3. **The Dearborn hybrid-cogen scope gate** (§5) — a rule 14 `[R-ACCURATE]`
   derive-logic item worth one plant / 515 MW / +13–20 % on its own rate.
   Needs its own pre-registration; sized here so a successor can judge whether
   it is worth the session.

## 11. Rule duties

* **Rule 15** — no run produced; nothing to register on the dashboard, stated
  rather than assumed.
* **Rule 16 `[R-ALLYEARS]`** — the 2023–2025 span was measured in one pass; no
  single-year claim anywhere.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 ONLY. MISO holds no
  `calibration-complete` marker; no holdout year was solved, scored **or read**.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive script re-run, no artifact
  regenerated. §5's defect is documented, not patched.
* **Rule 24 / 26 `[R-REGISTRY]`** — every crosswalk is the repo's own
  (`states_for_iso`, `_hour_index_8760`, `unit_family`,
  `measured_chp_heat_rates`, `load_monthly_generation`,
  `_CACHE_KEY_RETIRED_FIELDS`). No hand map. The three retired `CT_CHP` override
  keys in the keeper's `run_config.json` (deleted 2026-08-03 by nyiso-114 under
  rule 26 `[R-DELETE]`) are dropped **only** because they appear in the repo's
  own retired-field registry; any other unknown key hard-fails the probe.
* **Rule 19 / 25** — nothing armed, nothing stacked, no cross-ISO transfer.
* **Rule 28 duty (b)** — the `measured_chp_heat_rates` MISO cell is annotated in
  this session with this finding. **Status stays `K`**: no mechanism was armed,
  rejected or promoted — the correction is to the *evidence about* the
  mechanism, not to the mechanism.
* **Contamination declared** — the session was **not** blind. It read miso-115,
  miso-116, miso-117, the MISO log and the matrix first, the handoff named the
  basis-artifact hypothesis, and — declared at PREREG §8 — an arithmetic check
  on plant 10745 was run *before* the pre-registration was written and already
  pointed at H-A. What the pre-registration fixed in advance, and what the
  result therefore means, is the decision **bands**, the completeness
  **identity**, the **kills** and the per-plant verdicts for the other three
  plants. One prediction (4) was refuted in substance.
* Next number: **miso-119.**
