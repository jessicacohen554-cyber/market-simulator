# PREREG miso-215 — THE `phys_*` COVERAGE GAP ON THE INTERMEDIATE-DUTY COHORTS: phase 0 (zero-solve) sizes the three uncovered cohorts, tests whether the frozen class p50s are theirs to borrow, tests whether the ISO anchor is itself the object, and charters AT MOST ONE single-delta A/B (2026-09-05)

**Pushed BLIND** — before any adjudicating statistic of this session, and before any arm is
designed. Keeper at open `2026-09-05-miso-213-layering` (bundle
`results/calibration/miso213_layering_B`), **NOT-YET on C3a-2025 alone (−11.747 %)**, C3c
ledgered 3/3, C6 attested 41/2. Branch `claude/miso-215-intermediate-phys-waosaw` (the
session's DESIGNATED branch; the charter text names
`claude/miso-215-intermediate-phys-coverage` — same lane, the designated name governs) from
`origin/main` **`182aa74a`**, which contains the miso-214 work
(`FINDING-miso214-ct-peaker-conduct-2026-09-05.md`, its PREREG, probe and JSON record).
Rule 22 `[R-HOLDOUT]`: **2023–2025 only** — MISO holds no marker; the probe hard-asserts it.
Rule 25 `[R-ISO-SCOPE]`: MISO's shard only, plus one cell line per shard IF a new
`ScenarioConfig` field is added (rule 28c).

---

## 1. The object, read from the code and from the miso-214 record (not measured here)

`gas_offer_net_revenue_margin` is **armed** on the MISO keeper (matrix cell `K`,
`gas_offer_margin_anchor = 3.0492 $/MMBtu`). Its mc-side half is

```
mc'[g,t] = mc[g,t] + markup_hr[g] × (anchor − F[g,t])
         ≡ phys × HR_base × F[g,t]  +  markup_hr[g] × anchor
```

— the physical burn keeps full delivered-fuel tracking, the residual markup becomes a
fuel-invariant $/MWh margin identified at the anchor. `markup_hr` comes from
`offer_curves.gas_offer_margin_markup_mult`, which reads the `phys_*` keys carried on the
tranche's **resolved offer-curve band dict**, and whose documented rule-24 neutral fallback
is: *a band whose `phys_*` key is absent returns markup 0.0* — byte-identical at every gas
price, i.e. the mechanism SKIPS it.

`pipeline/backcast_config._neutralize_generic_gas_bands` lists exactly five classes
(`CC_REGULAR`, `CC_CHP`, `CT_CHP`, `CT_PEAKER`, `ST_GAS`) and its docstring states that
"every other class (coal, `*_INTERMEDIATE`) are kept"; `_MISO_OFFER_CURVE` then deep-merges
`phys_*` onto **those same five**. So on this keeper — which arms all three duty splits
(`ct_intermediate_split`, `cc_intermediate_split`, `st_gas_intermediate_split`, each at
`cf_threshold = 50.0`) — the three intermediate-duty curves carry **no `phys_*` keys at
all**:

| class | committed | econ_low | econ_high | peak | `phys_*` present |
|---|---:|---:|---:|---:|---|
| `CT_PEAKER` | 1.025 | 1.000 | 1.000 | 4.00 | **all four** (1.025 / 0.687 / 0.691 / 1.0) |
| `CT_INTERMEDIATE` | 1.000 | 1.000 | 1.200 | 3.00 | **none** |
| `CC_REGULAR` | 1.005 | 0.950 | 1.080 | 2.25 | **all four** (1.005 / 0.887 / 1.008 / 2.25) |
| `CC_INTERMEDIATE` | 1.005 | 0.950 | 1.080 | 2.25 | **none** |
| `ST_GAS` | 1.000 | 1.000 | 1.000 | 1.00 | **all four** (1.079 / 0.812 / 0.849 / 1.0) |
| `ST_GAS_INTERMEDIATE` | 1.000 | 1.000 | 1.150 | 2.20 | **none** |

(read verbatim from `results/calibration/miso213_layering_B/run_config.json`.)

miso-214 §6 measured the CT half of the consequence: 44 plants / 9,333.2 MW = **41.9 % of
MISO's CT class capacity**, carrying **55–57 %** of the class's CAMPD energy
(9.23 / 10.15 / 10.83 TWh), at a cap-weighted econ **offer** heat rate of **12.465** with a
markup of **exactly 0.000**, against the true-peaker cohort's physical leg 8.649 + markup
3.906 — i.e. the cohort offers its energy at 12.465 MMBtu/MWh against its own measured
average burn of 11.07. The CC and ST cohorts have **never been sized**.

**This lane's question is NOT "does closing the gap improve the fit."** It is: *is the
intermediate cohort's offer form structurally wrong, and if so is there a single
zero-DOF field that fixes it — or is the mechanism's own identification point the object
instead?* Rule 1 `[R-STRUCT]`: a structurally-faithful arm stays in even if it makes the
residual worse, and a favourable residual reached through a mis-identified anchor is not a
keeper.

## 2. Instrument, and what it can and cannot see

* **Zero solve.** Every number comes from committed artifacts and the HEAD fleet chain.
* **Plant- and zone-grain model merit is the miso-214 PRICE-TAKING STATIC SCREEN**, not the
  LP: the keeper ships `class_band_hourly / class_hourly / network / reserve_family /
  storage / system`, and NOT `unit_hourly/` or `dispatch/`. The screen prices the HEAD fleet
  chain (`build_year` under the keeper's own recorded config, `mc_base`, no P1 startup
  adder) against the keeper's own committed P1 zone prices, and is **loose in both
  directions by a measured factor** — miso-214 §1: 1.430 / 1.410 / 1.416 × the LP's own
  CT_PEAKER class energy, and it runs plants CAMPD shows OFF in 9.7 / 16.2 / 12.3 TWh of
  plant-hours. Every reach number below is a BOUND on the LP, reported as such.
* **The `_miso212` import trap (miso-214's own disclosed instrument defect) is carried
  forward as a hard requirement**: `_miso212_south_gas_cost_basis` transitively imports
  `_miso211_rdt_binding_state`, which re-points `_miso134.BUNDLE` to `miso210_clock_B` **at
  module scope**. The T-1 re-pointing block MUST sit AFTER the last import and MUST carry a
  hard assert on a keeper-only field (`miso_zonal_gas_basis_skip_923_priced`).
* **CAMPD** is read exactly as miso-214 read it — `data/raw/campd-unit-level/` directly (not
  `load_campd_hourly`, which drops `opTime`), on the model's fixed non-leap 8760 clock with
  **no timezone shift** (the established MISO-probe convention, disclosed not corrected),
  CAMPD **gross** against the model's **net** tranches unadjusted.
* **The EIA-923 print is an ALL-IN delivered cost** (commodity + fixed firm-transport demand
  charges, which do not enter an hourly offer). The average-vs-marginal delivered-cost
  convention (miso-212 §8) is **OWNER-COURT and untouched**; §5's M-3 reports the size of
  the anchor's basis gap and **adjudicates nothing about the convention**.
* **What this instrument CANNOT do**: identify a cohort-specific physical basis. The frozen
  rule-23 artifact `data/raw/reference/miso_campd_marginal_hr_summary.csv` carries rows for
  MODEL PLANT GROUPS only (`CT_PEAKER` n=249, `CC_REGULAR` n=103, `ST_GAS` n=40) — the
  intermediate split is a config-time ROUTING that happens downstream of it, so **no
  `*_INTERMEDIATE` p50 exists and none may be minted here** (rule 23 `[R-FROZEN-DERIVE]`: a
  derive re-runs only on a source-data change). Any arm must therefore BORROW the parent
  class's pooled p50 — and M-3b below is the test of whether that borrowing is legitimate.

## 3. What will be measured (M-1 … M-4)

Probe `scripts/probes/_miso215_intermediate_phys_phase0.py` → record
`results/calibration/_miso215_intermediate_phys.json`. Reuses the miso-214 readers
(`build_year`, `keeper_config`, the static screen, `campd_ct`, `actual_lmp_by_zone`,
`_capw_hr`, `io_fit`).

* **M-1 SCOPE.** For each of `CT_INTERMEDIATE`, `CC_INTERMEDIATE`, `ST_GAS_INTERMEDIATE`:
  cohort membership, plant count, capacity and share of the parent class's capacity, econ
  tranche count, cap-weighted econ offer / physical-leg / markup heat rates, cap-weighted
  resolved delivered fuel, and CAMPD energy per year. Same table for the three parent
  cohorts, so the blast radius of a CC-side arm is sized BEFORE scope is chosen.
* **M-2 BAND SCOPE.** The static reach measured **econ-only** and **econ+peak**, per cohort
  and per year, with the peak leg's own C3c exposure (the change in the cohort's peak-band
  offer at its own delivered fuel, and the model's top-1 %/top-0.1 % price hours). miso-214's
  reach was econ-only, matching the miso-134 band-scoping precedent (the peak band is a
  deliberate scarcity wall). `CT_PEAKER` itself carries `phys_peak = 1.0`, so an econ-only
  arm is **not** a mirror of `CT_PEAKER` — the asymmetry is stated and measured, not assumed.
* **M-3 ANCHOR GRAIN.** `GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"] = 3.0492` is derived
  (`scripts/data/derive_gas_offer_margin_anchor.py`, `GAS_SERIES_FLAGS["MISO"] =
  {gas_seasonality, gas_daily_shape, miso_zonal_gas_basis}`) from
  `data.fuel.trajectories._gas_series` — an **ISO-level Henry-Hub × seasonality × daily-shape
  series**, means 2.8392 / 2.4893 / 3.8190. The fleet is priced by the **per-plant EIA-923
  PRINT path** (`gas_plant_monthly_fuel_pricing = True`, `gas_monthly_actuals = False`,
  `gas_hub_basis_overlay = False`), which the anchor derive cannot see because it applies on
  the `(n_gen, T)` array. Measured: the anchor against each cohort-year's own cap-weighted
  resolved delivered fuel; the ISO series against measured annual Henry Hub; the share of
  each cohort's econ capacity-hours above the anchor; and the **anchor-artefact
  decomposition** defined in M-3c below. This is the BASIS grain and is a DIFFERENT question
  from the ZONAL grain already adjudicated `I` on MISO (`gas_offer_margin_zonal_anchor`,
  miso-119/120) — that cell is **not re-tested** and is not re-opened.
* **M-3b BORROWING VALIDITY.** The `CT_INTERMEDIATE` cohort's **own** measured marginal-HR
  multiplier, computed in the probe by the same construction the frozen derive uses
  (per-unit steady-state input-output slope, `opTime ≥ 0.98`, inside the unit's own p3–p97
  load envelope, cap-weighted, expressed as a multiple of the class base HR), against the
  pooled `CT_PEAKER` p50s 0.687 / 0.691 the arm would borrow. **Diagnostic only — nothing is
  re-derived and no artifact is rewritten.** Same for the CC and ST cohorts.
* **M-3c ANCHOR-ARTEFACT DECOMPOSITION.** Re-run the static reach with the anchor replaced,
  per cohort-year, by that cohort-year's **own cap-weighted resolved delivered fuel** (a
  counterfactual diagnostic, never an arm, never a field). Report the fraction of the
  |screen delta| that survives. If most of the reach vanishes, the reach is a statement
  about where 3.0492 sits in the fuel distribution, not about the offer FORM.
* **M-4 RULE-19 CENSUS.** Everything that already prices these cohorts' econ tranches: the
  P1 startup amortization (`tranche_startup_amortization` + `tranche_startup_measured_runs`
  / `_conditional_runs`, all True on the keeper) and its cap-weighted $/MWh, the committed
  band, the armed `RELIABILITY_FLOOR_REGISTRY` limbs and the bundle's own D-2/D-4 rows, and
  the C8 forced share by class. Rule 19 `[R-ONE-MECH]`: enumerate before proposing.

## 4. My prior, stated before the measurement (scored in the finding, against interest)

**Explicitly NOT blind, and flagged as such:** the `CT_INTERMEDIATE` legs of P-2/P-3 are
already published in miso-214 §6 (cohort 44 plants / 9,333.2 MW / 41.9 %; econ offer HR
12.465, markup 0.000; delivered fuel 4.424 / 3.494 / 4.156 against the anchor; econ
capacity-hour share above anchor 0.606 / 0.435 / 0.840; static reach −1.475 / −5.285 /
+1.457 TWh and 1.1 / 0.8 / 8.0 % of missed MWh flipped in). Those are **restated, not
predicted**. The blind content of each prediction is named.

* **P-1 (M-1 scope).** `CC_INTERMEDIATE` is the LARGEST of the three cohorts by capacity —
  **≥ 60 %** of MISO's `CC_REGULAR`-class capacity and **≥ 15 GW** — and
  `ST_GAS_INTERMEDIATE` is the smallest, **< 4 GW**. The three uncovered cohorts together
  carry **≥ 35 %** of the assembled MISO gas capacity. *(Blind: all three legs.)*
  Rationale: MISO's whole CC fleet runs intermediate/baseload (the generic
  `CC_INTERMEDIATE` comment states median CF 50–150 %, mean ~90 %) at a 50.0 threshold.
* **P-2 (M-2 band scope).** Cap-weighted fixed margin at the anchor
  (`markup_mult × base_HR × 3.0492`), econ bands: `CT_INTERMEDIATE` **$10–16/MWh**,
  `ST_GAS_INTERMEDIATE` **$6–13/MWh**, `CC_INTERMEDIATE` **$1.0–2.0/MWh** — i.e. the CC arm
  is nearly inert per-MWh because its registered bands (0.95 / 1.08) sit within 0.07 of
  `CC_REGULAR`'s measured phys (0.887 / 1.008), while its ENERGY blast radius is the
  largest. *(Blind: all three ranges.)*
  **And the peak leg is C3c-ADVERSE**: `CT_INTERMEDIATE` peak 3.00 against a borrowed
  `phys_peak` 1.0 is a markup of 2.00, so arming the peak band replaces a fuel-scaled
  scarcity wall with a fixed **$70–80/MWh** margin and **LOWERS** the cohort's peak offer by
  **≥ $20/MWh** in 2023 and 2025 (where delivered fuel exceeds the anchor). **I therefore
  pre-commit to scoping ECON-ONLY** if anything is chartered.
* **P-3 (M-3 anchor grain).** The anchor sits **BELOW** each cohort-year's own cap-weighted
  delivered fuel by **≥ +0.30 $/MMBtu in ≥ 8 of the 9 cohort-years**, AND the ISO
  `_gas_series` annual means sit **within ±0.35 of measured annual Henry Hub**
  (2.54 / 2.19 / 3.52). *(Blind: the CC and ST cohort-years, the 8-of-9 aggregate, and the
  `_gas_series`-vs-HH leg. The three CT numbers are restated from miso-214.)*
* **P-3b (borrowing validity).** The `CT_INTERMEDIATE` cohort's own measured marginal-HR
  multiplier lands **within ±0.06** of the pooled `CT_PEAKER` p50s (0.687 / 0.691) — i.e.
  the borrowing is legitimate and the pooled statistic is the cohort's physics too.
  *(Blind.)* miso-214 measured the cohort's I-O slope in ABSOLUTE terms (8.76 / 9.03 / 8.83
  MMBtu/MWh cap-weighted over BOTH CT cohorts); it never expressed the intermediate cohort's
  own slope as a multiple of the class base HR, which is the quantity the arm would need.
* **P-4 (M-4 census).** **≥ 3** mechanisms already price the `CT_INTERMEDIATE` econ
  tranches, the P1 startup amortization is present on them and is worth **≥ $2/MWh**
  cap-weighted, and **no** existing mechanism converts this cohort's markup to a fixed
  margin — the gap is real and unfilled. *(Blind: the count and the $/MWh.)*
* **P-5 (charter).** **P(an A/B is chartered) = 0.25.** I expect **K-c** to fire: the
  cohorts' delivered fuel sits well above the anchor, so I expect M-3c to show that most of
  the static reach is the anchor's position in the fuel distribution rather than the offer
  form — which makes the anchor, not the coverage gap, the object. I also note against
  myself that this prediction is partly informed by miso-214's published CT numbers.

## 5. Kill criteria — the decision rule, pre-committed

An A/B is chartered **only if ALL of K-a … K-e pass**. Any single fire ⇒ write the finding,
mint nothing, update the matrix cells, stop.

* **K-a — SINGLE FIELD, ZERO FREE PARAMETERS.** The arm must be exactly one
  `ScenarioConfig` boolean whose values are the **frozen measured p50s already registered in
  `_MISO_OFFER_CURVE`** for the parent class. If it needs a new number, a per-cohort value,
  a threshold, or more than one field ⇒ **FIRE**.
* **K-b — BORROWING VALIDITY (P-3b).** If a cohort's own measured marginal-HR multiplier
  falls **outside ±0.06** of the pooled parent p50 it would borrow, the pooled statistic is
  not that cohort's physics; the arm then carries a hidden identification choice and is not
  zero-DOF in substance ⇒ **FIRE** for that cohort. (If it fires for every candidate cohort,
  the whole charter dies and the question routes to a rule-23 source-data item.)
* **K-c — THE ANCHOR IS THE OBJECT (M-3 / M-3c).** If the anchor sits ≥ 0.30 $/MMBtu below
  the candidate cohort's own delivered fuel in **≥ 2 of 3 years** AND M-3c shows that
  **≥ 70 %** of the |static screen delta| vanishes when the anchor is set to the cohort's own
  delivered mean ⇒ the arm's direction is an anchor artefact, not an offer-form correction
  ⇒ **FIRE**, and the anchor question is routed to the OWNER (it is a property of the
  mechanism on all five ALREADY-ARMED classes, not of the coverage gap, and re-identifying
  it is a mechanism change, not a rule-23 re-derivation).
* **K-d — PROTECTIVE-GATE EXPOSURE.** If the static reach, taken as the bound it is, cannot
  move the object favourably in ≥ 2 of 3 years AND puts either pre-registered protective
  face at risk ⇒ **FIRE**. The two faces, pre-registered here with their bands:
  * **K-1 / C1 `CC_REGULAR`-2024** — currently **+7.419 %** against a ±8.00 band, i.e.
    **0.58 TWh** of headroom, and CT displacement backfills to CC. A projected move that
    would take it past ±8.00 is a kill.
  * **C8 `CT_PEAKER`-2023** — already **20.4 %** forced share (2.195 of 10.740 TWh,
    `reliability_floor` the only D-2 row) against the 15 % peaker budget, PASSing only on
    rule 20's conditional provenance+shape route. Less CT econ energy RAISES the forced
    share. A projected rise is a kill unless the D-4 window and D-1 shape legs still clear.
* **K-e — MATERIALITY.** If the three uncovered cohorts together carry **< 5 %** of the
  assembled MISO gas capacity, the gap is immaterial ⇒ **FIRE** (report only).

## 6. IF chartered — the arm, designed HERE and not after the measurement

* **Field:** one boolean on `ScenarioConfig`, MISO-gated, default **False**.
* **Seam (pre-registered, because `--set` would silently miss it):** `--set` on
  `replay_keeper` rides the generic `prb_overrides` channel, applied **AFTER**
  `backcast_config` has merged the per-ISO curves — so a config-BUILD-time merge gated on
  the new field would **NOT fire under a replay**. The arm is therefore implemented at
  **`data/offer_curves._offer_curve_for_group`** (read at fleet-assembly time, so the CLI and
  the replay path both see it), **returns a COPY** (the function today returns the config's
  own dict by reference), and gates on `iso == "MISO"` **as well as** the flag (rule 25).
* **Values:** the parent class's already-registered `phys_econ_low` / `phys_econ_high` only
  (econ-only per P-2); no `phys_committed`, no `phys_peak` — the peak band stays the
  deliberate fuel-scaled scarcity wall.
* **Tests:** unit tests pinning **flag-off byte identity** of the resolved curve and of the
  assembled `offer_markup_hr`, and the algebraic identity at `fuel == anchor`.
* **Matrix:** base row in `docs/codebase-site/data/mechanism-matrix.js` + one cell line in
  **every** shard (rule 28c, the one deliberately non-parallel edit);
  `scripts/check_mechanism_matrix.py` must pass.
* **Solve:** `scripts/replay_keeper.py results/calibration/miso213_layering_B --set
  <field>=true --out-dir results/calibration/miso215_<name>_B`, years **2023 2024 2025
  sequential in ONE invocation** (rule 16, rule 12). **CONTROL is the keeper bundle itself**
  (S-0 inherited; not re-solved).
* **Scorer** on the `_miso213_ab_gates.py` pattern, **committed BEFORE the solve**: S-0
  inherited; S-1 restated over the RECORDED configs (six fields are new on `main` since the
  keeper solved and must sit at default); S-2 liveness (`markup_hr > 0` on the cohort's econ
  tranches, and byte identity at `fuel == anchor`); K-1…K-6; and the §5 object gates —
  `CT_PEAKER` and `CC_REGULAR` C1 faces by year, C8 `CT_PEAKER` forced share, C3c tail hours.
* **Promotion** only if structurally faithful AND no protective gate regresses. **C3a is
  reported, never argued.**

## 7. Standing constraints this lane must not violate

* **The miso-214 standing result stands and must not be undone.** 62–70 % of the CT energy
  the model misses was produced by the real market **below the plant's own delivered cost**,
  at the market's own price (41–49 % on the strictest single substitution; 44–60 % paying the
  better of DA and RT). That energy is **not reachable by any offer or price mechanism**.
  Whatever this lane's arm does, it addresses **at most bucket C** (0.167 / 0.257 / 0.167 of
  the missed MWh) and part of **bucket A** (0.131 / 0.130 / 0.215) — the finding will say so,
  and **will not present a CT C1 improvement as closing the class's gap**.
* **DO-NOT-REDO honoured:** `gas_hub_basis_overlay` (R), `miso_offer_level_dispersion` (R),
  `miso_offer_spread_anchored` (I), `miso_rdt_measured_limit` (R),
  `miso_south_gas_delivered_cost_basis` (R), `gas_offer_margin_zonal_anchor` (I — the ZONAL
  grain; M-3's BASIS grain is a different question), `zonal_gas_basis` (K, scoped by
  miso-213).
* **CLOSED BY MEASUREMENT at miso-214, not re-opened:** a CT commitment bridge or min-load
  AS floor keyed on CAMPD (the B hours sit at a 0.70–0.78 load factor, not min load, and at
  the unconditional 10 % of their region's reserve top decile).
* **OWNER-COURT, not armed:** the average-vs-marginal delivered-cost convention (miso-212
  §8) and the D-2 5(i) seam-response object. **STILL OPEN, not this lane's lever:** the South
  PRICE separation (miso-213 O-4, the miso-211 D-3 object).
* **Rule 25:** PJM and CAISO carry the same `*_INTERMEDIATE` `phys_*` coverage gap in kind
  (they share `_neutralize_generic_gas_bands` and the per-ISO merge pattern). That is their
  lanes' `U`, **never MISO's business**, and no MISO verdict fills their cells.

## 8. What ends the session

Either (i) K-a…K-e all pass ⇒ ONE single-delta A/B, solved, scored, registered on the
dashboard (rule 15) in this session; or (ii) any kill fires ⇒ `FINDING-miso215-…md`, the
probe + JSON record, the `docs/calibration-log/miso.md` entry, the §5.4 queue stamp, the
MISO matrix-shard cell updates, and the miso-216 handoff prompt — **nothing minted**.

Next shorthand: **miso-215**.
