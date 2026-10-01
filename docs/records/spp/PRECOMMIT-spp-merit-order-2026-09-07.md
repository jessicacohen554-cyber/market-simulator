# PRECOMMIT — SPP MERIT ORDER / MHR ROTATION: the rotation gate, declared, and the two candidate arms it is declared against

**Lane:** SPP MERIT-ORDER. **Branch:** `claude/spp-merit-order-mhr-rotation-cbx1pu`. **DATA PROFILE: spp.**
**Model:** Opus. **Pushed BEFORE any LP — and no LP is spent by this lane** (see §0 and the companion
FINDING). **Control** = the committed keeper `2026-09-07-spp-3-screened-input` /
`results/calibration/spp43_screened_B` (`git_sha 623184f3`), rule 29(b) **form 4**, validated by the
G-DRIFT audit in §1.2.

---

## 0. ORDER OF WORK, DISCLOSED FIRST

Rule 29 clause 0 orders a **zero-LP phase 0 before any solve**, and *"an arm that has a computable
pre-solve gate does not reach a solve until that gate passes."* This lane's phase 0 is computable
end-to-end — the arms are offer-side, the keeper's own supply curve is reconstructable from an
on-recipe `fleet_only` rebuild, and the keeper's committed hourlies supply the clearing points — so
phase 0 ran **first** and its output is reported in `FINDING-spp-merit-order-2026-09-07.md`.

Three things follow, stated here rather than left to be inferred:

1. **No LP was solved by this lane, at all.** Nothing was screened, nothing was registered, the
   keeper is unchanged, and no bundle was created (so rule 29(c) has nothing to delete).
2. **The gate in §4 is therefore a STOP gate that was applied, not a promotion gate that was
   passed.** It can only kill. Its threshold is **inherited unchanged from this lane's own
   predecessor** (the SPP PRICE-FAMILY lane's pre-registered G-2, §4.1) precisely so that it cannot
   be a number chosen after seeing a result.
3. **The uncomfortable ordering is that the arms' predictions were computed as part of phase 0,
   before this document existed.** That is what phase 0 *is*. It is safe here only because the
   outcome is a refusal: a phase-0 measurement in this lane may kill an arm and may never promote
   one, and no arm survives. Had one survived, its screen gate would have had to be declared before
   its prediction was computed; that discipline is stated as binding on the successor lane (§5).

---

## 1. The target, and the control

### 1.1 The target — SPP's market heat rate must ROTATE with load, not merely scale

The steepening ratio **MHR(>95th load pct) / MHR(25–75th load pct)**, on SPP's own hourly RT LMP
(`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`) over SPP's own KS/OK delivered gas
(EIA `N3045KS3` / `N3045OK3`, $/Mcf ÷ 1.037), against the keeper's committed
`hourly/system_<year>.parquet` on the identical axis:

| year | measured | keeper | MHR mid (meas / model) | MHR hi (meas / model) |
|---|---|---|---|---|
| 2023 | **2.3375** | 1.5620 | 6.7093 / 8.6485 (**+29.0 %**) | 15.6829 / 13.5089 (**−13.9 %**) |
| 2024 | **2.0993** | 1.5163 | 7.1084 / 8.9198 (**+25.5 %**) | 14.9224 / 13.5250 (**−9.4 %**) |
| 2025 | **2.1069** | 1.6187 | 5.8103 / 6.6102 (**+13.8 %**) | 12.2416 / 10.7001 (**−12.6 %**) |

(The handoff's 2.1088 / 1.6214 for 2025 are the price-family lane's values on the *previous* keeper
`spp42_crosswalk_B`; the 0.17 % difference is the degenerate-vertex noise the SPP-43 keeper shard
already records. Reproduced here to 0.1 % on the current keeper.)

**The deficit has TWO legs with opposite signs — it is a rotation, not a level.** The model is too
dear in the middle *and* too cheap at the top, in every year.

### 1.2 G-DRIFT (rule 29(b)) — re-run from the CURRENT keeper's sha, and it is now clean

`git diff 623184f3 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` at `origin/main` `e042a9f5` → **13
files, two mechanisms, every hunk INERT for an SPP backcast:**

| change | classification | reason |
|---|---|---|
| `spp_gas_commitment_bridge` (SPP-44): `scenarios.py`, `constants.py`, `solve_surface_declared.py`, `floor_mechanisms.py`, `pipeline/commitment.py`, `pipeline/__init__.py`, `pipeline/year.py`, `runner.py`, both CLIs | **INERT** | `build_spp_gas_bridge_p1_prep` returns `None` unless `getattr(config, "spp_gas_commitment_bridge", False) and iso == "SPP"`; the field's dataclass default is `False` and it is **absent from the keeper's recipe**. The `year.py` / `runner.py` hunks add that `None` into an existing `or` chain; `floor_mechanisms.py` adds an unused mechanism id 24 + its name + ablation row. |
| `ercot_zonal_spread_ep_referenced` (ercot-255): `scenarios.py`, `data/fuel/basis/ercot.py`, `data/fuel/__init__.py`, `data/fuel/basis/__init__.py` | **INERT** | a new `ScenarioConfig` bool, dataclass default `False`, absent from SPP's recipe, and an ERCOT-only basis implementation plus two re-export lines. |

**ALL HUNKS INERT ⇒ form 4 is valid and the keeper's committed bundle is the control, for ALL THREE
YEARS.** This is a change from the price-family lane, which found one LIVE hunk (`data/eia930/
actuals.py`, SPP-41's `NG:` unit-slip screen) and could not difference 2023. **That hunk is now
inside the control**: keeper-3 IS keeper-2's recipe re-solved through the screened seam. No control
solve is earned and none is spent.

---

## 2. Phase 0 — what SPP's model stack actually is (zero LP)

Every number below comes from an on-recipe `run_year(fleet_only=True)` rebuild of the keeper (its
own `meta.json` through `replay_keeper.build_kwargs`, one delta at a time) plus the keeper's own
committed hourlies. Full tables: FINDING §1–§4.

### 2.1 SPP's offer curve is the IDENTITY, on every band of every class it dispatches

The keeper's resolved `offer_curve_by_group` reads `committed = econ_low = econ_high = peak = 1.0`
for `CC_REGULAR`, `CC_CHP`, `CT_PEAKER`, `CT_CHP`, `ST_GAS` (the rule-24 generic gas neutralization)
and for all five `COAL*` keys (the SPP-40/SPP-42 rule-25 identity correction). So **a plant's four
tranches are price-identical**, and the tranche structure carries no price information at all.

Two consequences that bound this lane before it starts:

- **`pct_peaking` — the handoff's arm 2 — is INERT on price for SPP, by measurement.** Two
  `fleet_only` rebuilds differing only in `CT_PEAKER pct_peaking 7.0 → 40.0` and
  `CC_REGULAR 8.0 → 30.0` move the LP's own cumulative-available-MW-by-offer-level curve by at most
  **3.83 MW** (91 sampled hours × 2 zones, against ~30 GW available) and total fleet pmax by
  **5.16 MW of 59,613 MW (0.0087 %)** — pure tranche-granularity rounding. Moving capacity between
  bands that are priced identically cannot move a price. **Arm 2 is dead at zero LP** and its own
  premise ("92.6 % of a CT's capacity sits outside its peak band") is a statement about a partition
  that the model does not price.
- The marginal-*band* attribution is degenerate (ties broken by row order) and is **not** used as
  evidence anywhere in this lane. The marginal-*class* attribution is not degenerate and is.

### 2.2 Who is marginal, by system-load percentile — two independent identifications, agreeing

Method A: per zone-hour, the available thermal row whose `mc_base` is closest to the keeper's own P1
zonal price (identification quality: median |mc − price| = **$0.0000**, **99.3–99.5 %** of hours
within $0.50). Method B: capacity-weighted over **every** available row within **$0.25** of the
price (4–14 rows, $395–490 MW at the median), so the answer does not depend on a tie-break.

Method B, capacity-weighted share of the margin:

| | COAL_PRB | CC_REGULAR | **CT_PEAKER** | ST_GAS |
|---|---|---|---|---|
| **MID (25–75 pct)** 2023 / 2024 / 2025 | .293 / .255 / .324 | .256 / .275 / .245 | **.264 / .270 / .244** | .092 / .095 / .098 |
| **HI (>95 pct)** 2023 / 2024 / 2025 | .068 / .132 / .079 | .006 / .091 / .061 | **.537 / .487 / .601** | .384 / .270 / .241 |

**A simple-cycle peaker is the marginal class in a quarter of SPP's MEDIAN-load hours.** That is the
merit-order defect this lane is named for — and it is *not* a capacity shortage: at mid load the
model leaves **3,084 / 3,725 / 2,829 MW** of available COAL_PRB and **3,271 / 2,898 / 3,261 MW** of
available CC_REGULAR unused (utilisation of availability 0.61–0.75 coal, 0.51–0.57 CC) while
dispatching 1,898 / 2,678 / 2,399 MW of CT_PEAKER.

### 2.3 The consequence for any offer-side lever, stated before the arms

Because the marginal class at mid load is a near-even three-way mix (coal ≈ CC ≈ CT, each ~25 %)
and at the top a two-way mix (CT ~50 %, ST_GAS ~25 %), **a per-class multiplier moves the middle
almost as much as it moves the top**. This is the structural reason a class-differentiated curve is
expected to behave like a level lever, and it is what §4's gate tests.

---

## 3. THE TWO CANDIDATE ARMS, declared

### 3.1 ARM A — the MEASURED start-recovery mechanism (`tranche_startup_amortization` + v3)

**Rule 19 `[R-ONE-MECH]` comes first, and it is what selects this arm over a fitted one.** What
prices start recovery on SPP's CT/CC tranche rows today, enumerated on the keeper's own resolved
config:

| rows | current owner of start recovery |
|---|---|
| every CAMPD bin `_committed` tranche | the NREL start cost amortized over P0 monthly run lengths (`compute_monthly_markup`, the P0→P1 seam) — active, and self-disabling (long P0 blocks ⇒ ≈ 0 $/MWh) |
| `ST_GAS` | **nothing** — `gas_st_startup_cost` is `False` |
| **`CT_PEAKER`/`CT_CHP` econ+peak, `CC_*` peak** (this arm's target rows) | **NOTHING. Every band multiplier is exactly 1.0; the above-SRMC margin on these rows is $0.00.** |

This is the **exact test that REFUSED the same mechanism on ERCOT** (`DIAGNOSIS-ercot145-tranche-
startup-2026-07-31.md` §1: ERCOT's CT rows already carried +$13 / +$35 / +$292–451 of *fitted*
multiplier margin against a $2.9–4.0 measured amortization, so arming was stacking). ERCOT-145's own
closing sentence names the other regime: *"Contrast with the four keeper ISOs: there the tranche rows
sit at or below their physical basis … so the amortization added a genuinely missing component."*
**SPP is that regime, not ERCOT's** — the rows are empty. Verdicts never transfer (rule 25); the
*test* does, and on SPP it points the other way. The mechanism is `K` on PJM/MISO/NYISO/NEISO, `G` on
ERCOT/CAISO, and `U` on SPP.

**Rule 25 `[R-ISO-SCOPE]` — SPP's own artifact, derived by this lane.**
`scripts/data/derive_campd_ct_run_lengths.py --iso SPP` →
`data/raw/_processed-legacy/campd_ct_run_lengths_SPP.csv`: **51 SPP CT facilities / 138 units, 50,460 measured
start-to-stop runs**, 2023–2025 pooled, **class-fallback median 9.0 h** (per-plant medians p25 7.0 /
p50 9.0 / p75 11.0 h; one outlier, Blackhawk Station 55064, 44 runs at a 713 h median, is a
non-peaker duty that the capacity weighting leaves immaterial).
No other ISO's run length, start cost or multiplier is carried in. Zero free parameters: the start
costs are the published NREL table already on the bins, the horizon is measured.

**The arm:** `tranche_startup_amortization=True` + `tranche_startup_measured_runs=True`, nothing
else. v4 (`tranche_startup_conditional_runs`) is **not** included and stays untested.

**Its own arithmetic, measured on the arm's `fleet_only` rebuild:** 384 rows / **11,600–11,631 MW**
gain a start-recovery term — `CT_PEAKER` econlo+econhi+peak (10,519–10,566 MW, $20/MW-start, 9 h
horizon, **max $2.12–2.14/MWh cap-weighted**), `CT_CHP` econ+peak (116–132 MW, **$0.66–0.87/MWh**), and `CC_REGULAR`/
`CC_CHP` peak (949 MW, $50/MW-start, which keep the v2 P0 basis so their markup is not computable at
zero LP and is bounded instead). `mc_base` is **byte-identical** between the arm and control fleets
(max |Δ| = 0).

### 3.2 ARM B — the PER-CLASS DIFFERENTIATED offer curve (the question the price-family lane left open)

The authorized price-tuning channel of rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`, resolved **per
class** instead of the uniform per-band quadruple that lane adjudicated `R`. Every carve-out
condition is met and stated: **(a)** band multipliers only — no `phys_*`, no `econ_low_share`, no
`pct_peaking`, no adder; **(b)** ONE config across every scored year, derived on the **pooled**
2023+2024+2025 panel; **(c)** set ex ante by the single rule below and **never swept**; **(d)**
cross-class merit-order adjustment is the intended effect; **(e)** would be declared in
`authorized_price_tuning` and carried as a DOF-ledger free parameter identified as *"price residual,
authorized channel (rules 1/13 amendment 2026-09-05)"*.

**The derivation rule — one rule, SPP's own data, stated as a rule before its values:**

> For each class *c*, `m_c` = (load-weighted mean **measured** SPP RT LMP, capped at $200, over the
> hours the MODEL's own marginal class is *c*) ÷ (load-weighted mean **model** price over the same
> hours), pooled 2023–2025.

Capped at $200 because the >$200 surface is a different mechanism (SPP-55) that no band multiplier
can generate; load-weighted because C3a is a load-weighted mean. Marginal class from §2.2 Method A.

**The declared values** (`{class: multiplier}`, applied to all four bands of that class):

```json
{"COAL_PRB": 0.7838, "COAL_LIGNITE": 0.8152, "CC_REGULAR": 0.8028, "CT_PEAKER": 0.8880,
 "CT_CHP": 0.8019, "ST_GAS": 0.8949, "ST_CHP": 0.8271}
```

The differentiation the arm is declared on: `CT_PEAKER / COAL_PRB = 1.133` — the peaker stack rises
**13.3 %** relative to the coal stack. `CC_*_INTERMEDIATE`, `CT_INTERMEDIATE` and
`ST_GAS_INTERMEDIATE` are untouched (all three splits are `False` in SPP's recipe, so they are
provably unreachable). `CC_CHP` and `COAL_BIT`/`COAL_WC`/`COAL` carry too few marginal hours to
identify and stay at 1.0.

---

## 4. THE GATE — pre-registered, STRUCTURAL, ROTATION-ONLY, and STOP-ONLY

### 4.1 The threshold is INHERITED, not chosen

`PRECOMMIT-spp-price-family-2026-09-07.md` §6.1 leg **G-2** required the steepening ratio to **RISE
by ≥ 10 % of the control's own value**. That number is adopted here **unchanged**, so this lane
cannot be accused of cutting its gate to fit its result. Expressed as a share of the measured gap it
is ≈ 33 % (the price-family lane's 1.6214 → 1.783 against a measured 2.1088).

> **G-ROT (STOP).** An arm reaches an LP only if the predicted steepening ratio
> `MHR(>95 pct)/MHR(25–75 pct)` **rises by ≥ 10 % of the control's value in the majority of the
> three years and never falls in any year.** Below that, the arm is refused at phase 0 and **no LP
> is spent**.

**G-ROT may kill an arm; it may never promote one.** It is not read against C3a, C3b or C3c, and no
determination follows from it. The level is *reported* alongside, never gated on.

### 4.2 The instrument, and its VALIDATION against a real LP

Zero-LP **re-clearing predictor**: for each zone-hour, the control clears `Q` MW = the available
thermal capacity offering at or below the keeper's own P1 zonal price; the arm re-prices the same
rows (`offer' = (mc − VOM) × m + VOM + adder`, band multipliers scaling the heat-rate term only) and
the predicted arm price is the offer at which the **same Q** clears. The two SPP zones are pooled
into ONE stack in the 77.8–80.0 % of hours the keeper's own zonal prices are equal (the link is
unconstrained, so one row sets both), and cleared separately when they differ.

**SELF-CHECK, and it is strict:** with every multiplier set to 1.0 the reconstruction must return
the keeper's own price **exactly**; hours where it does not are **excluded from every statistic**.
That leaves **25.9–28.6 %** of hours (the remainder are hours whose price is set by something other
than an available thermal row — hydro's monthly budget shadow price, storage, the link, a min-gen
row). The retained subsample is steeper on both sides than the full year and this is reported at
every use.

**VALIDATION against the one LP result that exists for this question.** The price-family lane
*solved* its uniform quadruple `{0.845, 0.794, 1.018, 1.118}` on 2025 and measured: arm/control
price ratio **0.9070–0.9151 across the load range**, LW mean **−9.05 %**, steepening
**1.6214 → 1.6298 (+0.52 %)**. This predictor, fed the identical quadruple:

| | LP-MEASURED (price-family) | THIS PREDICTOR | verdict |
|---|---|---|---|
| arm/control by load bin | 0.9070 – 0.9151 | 0.9147 – 0.9430 | same level, same near-flat shape |
| LW mean change | **−9.05 %** | **−8.11 %** (retained hours) / −9.12 % (all hours) | **matched to 0.1–0.9 pp** |
| steepening rise | **+0.52 %** | **+2.09 %** | **the predictor OVER-STATES rotation ≈ 4×** |

The 4× optimism is stated *against this lane's own interest* and is load-bearing: a predicted
rotation must be **divided by about four** to estimate what an LP would deliver. G-ROT is applied to
the raw (optimistic) prediction anyway, so the instrument's bias can only make the gate **easier**
to pass.

---

## 5. If an arm had passed — the screen that would have run

**SCREEN YEAR = 2023**, named here and chosen on the mechanism's own footprint, never on a residual:
Arm A's footprint is flat across years (11,600 / 11,631 / 11,631 MW) so the tiebreak is Arm B, whose
per-class re-pricing moves the most energy in 2023 (the widest measured-vs-model MHR mid gap,
+29.0 %, over the largest reconstructed subsample, 28.6 %). One year, one arm, one control
(form 4, §1.2) — then the full span `--year 2023 2024 2025` in ONE bundle (rule 16) only if the
screen cleared, and the screen bundle deleted before merge (rule 29(c)).

**Binding on the successor lane:** any arm not already predicted in this lane's phase 0 must have
its gate declared **before** its prediction is computed. This lane's ordering (§0.3) is admissible
only because it refuses.

---

## 6. What this lane does NOT claim

- **C1's gas split is not attempted.** It is reported at full magnitude and routed with a *new*
  measured lead (FINDING §5): SPP's `ST_GAS` fleet is priced at a **+29.3 % / +0.1 % / +7.9 %**
  delivered-gas premium over the `CT_PEAKER` fleet in 2023 / 2024 / 2025, and the ST_GAS energy
  under-run tracks it (**−7.49 / −5.12 / −10.27 TWh**). That is a rule-14 `[R-ACCURATE]`
  measured-input question about `gas_plant_monthly_fuel_pricing`, not an offer-curve or share
  question, and this lane does not touch it.
- **C3c is not this lane's object** and remains SPP-55's.
- **`energy_reserve_coopt` is not attempted and cannot be**: `model/reserves/spec.py::
  get_reserve_design` raises `ValueError` for SPP — there is no SPP reserve design in the repo. That
  the entire AS-opportunity-cost layer is missing from SPP's stack is reported as the largest
  *unbuilt* candidate for the top-of-stack leg, and routed.
- **Wind is +11.00 / +11.67 / +11.80 TWh over actual in every year** — the single largest class error
  in the keeper. Reported, not attempted; it is not an offer-curve object.
