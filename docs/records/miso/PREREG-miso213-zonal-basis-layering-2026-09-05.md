# PREREG miso-213 — THE RULE-19 ZONAL-BASIS LAYERING ON 923-PRICED PLANTS: phase 0 (zero-solve) sizes the population and the reach, then ONE single-delta A/B skipping the mean-zero increment on print-derived gas cells (2026-09-05)

**Pushed BLIND** before any adjudicating statistic and before the arm is built. Keeper at
open `2026-09-04-miso-210-clock` (bundle `miso210_clock_B`), NOT-YET on {C3a-2025
−12.385} alone, C3c ledgered 3/3, C6 attested. Branch `claude/miso-213-zonal-basis-layering`
from `origin/main` `920f6bb6` (contains miso-212). Rule 22: 2023–2025 only. Rule 25: MISO's
shard only, plus one cell line per shard IF the new field is added (rule 28c).

---

## 1. The object, read from the code (not measured)

`resolve_fuel_prices` (`data/fuel/resolve.py`) builds every MISO gas tranche's delivered
price in this order:

1. trajectory: annual HH × seasonality × daily HH shape;
2. `apply_plant_monthly_fuel_prices` (`gas_plant_monthly_fuel_pricing=True` in the
   keeper): each gas row's months are overwritten by **the plant's own EIA-923 print**
   where reported; still-unreported months are filled by the **nearby pool** — the
   quantity-weighted mean of the OTHER reporting plants' 923 prints, same class → same
   state → same zone (`nearby_fuel_price_fallback=True`, `class_aware_fuel_price_fallback=
   True`, `min_state_plants=2`). Only a cell that neither its own print nor any pool fills
   keeps the trajectory. **The function leaves no marker of which cells it set.**
3. `apply_miso_zonal_gas_basis` → `_apply_meanzero_zonal_gas_basis`: adds to **every gas
   row** its zone's `basis_vs_hh` from `data/raw/miso_zonal_gas_hub.csv` minus the
   gas-capacity-weighted mean. The table's rows are **EIA N3045<ST>3 "natural gas delivered
   to electric power consumers" by state, minus Henry Hub** (IA → West/Plains, IL →
   Illinois/Indiana/East, LA → South): 2025 −0.585 / +0.018 / +0.343; 2024 +0.357 / +0.120
   / +0.388; 2023 +0.459 / −0.108 / +0.295.
4. dual-fuel oil parity cap.

The N3045 series is the state aggregate of the very receipts the 923 prints report. So on a
print-derived cell the regional delivered premium enters **twice**: once inside the print
(or the pool of prints), once as the zonal increment. On a trajectory cell it enters once
and legitimately — there the basis is the only regional signal. **Rule 19 `[R-ONE-MECH]`:
two mechanisms price one phenomenon on the print-derived cells.** In FORECAST mode the print
path is off by construction (backcast-only overlay), every cell is a trajectory cell, and
the basis is the sole regional signal — the mechanism's forward story is intact and the
repair below is inert there by construction.

Genealogy (L-4 checks it): `--miso-zonal-gas-basis` was armed at MISO zonal onboarding
(gate 2, `docs/multi-iso/miso-zonal-gate2.md` reproduction recipe, miso-38 era); the South
2025 row was rebuilt at MISO-60 (+0.095 → +0.343, a like-for-like construction fix). The
`zonal_gas_basis` MISO cell reads K with no session citation. miso-212 sized the layering on
the South idle-within-$20 block in the real S→N RDT-binding hours: +$0.29/MMBtu = $3.1/MWh,
**0.78 GW** of 3.27 made economic when removed (2024 0.37; 2023 0.46); Midwest sign −0.20.

**Correction to the record, made here:** miso-212's MISO.js evidence line on
`zonal_gas_basis` opens "miso-119 (keeper lineage …)". miso-119 adjudicated
`gas_offer_margin_zonal_anchor` (I), not the basis; the basis predates it (gate 2). Fixed in
this session's shard edit.

## 2. Instrument

Phase 0: `scripts/probes/_miso213_basis_layering_phase0.py` →
`results/calibration/_miso213_basis_layering.json`. Readers from `_miso212_south_gas_cost_
basis.py` (`build_year`, `resolve_fuel_prices` with overlays toggled, `hh_daily_on_clock`,
`_band`) and `_miso211_rdt_binding_state.py` (real S→N binding hour sets, zone prices,
regional series). Print-derived cells are identified WITHOUT touching production code:
`F_nobasis` (basis off) ≠ `F_noplant` (basis off, print path off) at a cell ⇒ the print path
set it; own-print vs pool from `eia923.plant_month_price_grid` (own reported months).
Counterfactual reach uses the implied heat rate `(mc − VOM − markup_hr × anchor)/F`
(miso-212 §6). L-4 reads the gate-2 recipe and the argparse defaults of that era.

The arm (only if §4 licenses it): `apply_plant_monthly_fuel_prices` RETURNS an
`(n_gen, T)` boolean mask of the cells it wrote (own print or pool); `resolve_fuel_prices`
hands it to the MISO applier when `ScenarioConfig.miso_zonal_gas_basis_skip_923_priced`
(NEW, default False) is set; `_apply_meanzero_zonal_gas_basis` gains `skip_cells=None` and
**does not add the spread on masked cells**. The capacity-weighted mean is still computed
over ALL gas rows, so the zonal spread values are byte-identical to today's and only the set
of recipient cells changes — one delta. Flag off ⇒ byte-identical to HEAD (unit-tested).
A/B: `scripts/replay_keeper.py results/calibration/miso210_clock_B --set
miso_zonal_gas_basis_skip_923_priced=true --out-dir results/calibration/miso213_layering_B
--note …`, years 2023 2024 2025 sequential; CONTROL is the keeper bundle itself (S-0
bit-identity of the replay channel established at miso-210). Scorer
`scripts/probes/_miso213_ab_gates.py` on the miso-210 pattern, written before the arm's
numbers.

## 3. Predictions — each with its mechanism

* **P-1 population (L-1), Jun–Jul 2025, capacity-weighted.** ≥ 90 % of MISO gas capacity in
  EVERY zone sits on print-derived cells (own or pool) (0.7) — mechanism: the class-aware
  state/zone pools fill almost every unreported month once ≥ 2 plants in the state report.
  Own-print share of South gas capacity ≥ 60 % (0.6). Trajectory cells ≤ 10 % of gas
  capacity ISO-wide (0.7). Consequence stated in advance: the arm removes the basis from
  nearly the whole fleet, i.e. **`miso_zonal_gas_basis` is close to redundant under the
  print path in BACKCAST mode** — that is the finding if P-1 holds, not a surprise.
* **P-2 per-plant print − HH (L-2), same hours.** South p50 +0.3 to +0.6 $/MMBtu, p90
  ≥ +1.0 (small CHP/peaker takes amortize demand charges) (0.6); Midwest p50 +0.5 to +0.9
  (0.6) — the Midwest prints sit further over spot than the South's (miso-212 §3).
* **P-3 static reach (L-3).** South: 0.6–0.9 GW of the 3.27 GW idle-within-$20 block made
  economic at the fixed South price in the 2025 real S→N binding shoulder hours (0.65) —
  the miso-212 (b) number 0.78 less whatever trajectory cells keep the increment. Midwest
  mirror: 0.3–1.0 GW of Midwest gas made UNeconomic at the Indiana price (0.5) — the
  Illinois/Indiana/East increment is −0.20 (2025), West/Plains −0.8 after the mean; removing
  them RAISES Midwest/West gas by $2–8/MWh at 10–12 HR.
* **P-4 genealogy (L-4).** The gate-2 recipe carried `gas_plant_monthly_fuel_pricing` ON
  (a default-on calibration flag of that era, not listed among its explicit flags) — so the
  layering has been in every MISO keeper since the basis was armed (0.75). The basis was
  identified from the N3045 state series, never NET of the prints (0.8).
* **P-5 the A/B, if run.** S-1 exactly one config diff. Aggregate gas TWh moves < 0.3
  TWh/yr (mean-zero spread removed from a near-complete population: the fleet level is
  unchanged by construction) (0.7). Class: ST_GAS +0.1 to +0.5 TWh/yr (South-heavy, cheaper)
  and CC_REGULAR −0.1 to −0.5 (Midwest-heavy, dearer) (0.55). **C3a sign VARIES BY YEAR and
  is stated by mechanism**: 2025 the West/Plains increment is −0.8 and Illinois/Indiana/East
  −0.2 — removing them raises Midwest gas cost where the model already prices too low, so
  **C3a-2025 moves toward zero, +0.2 to +1.5 pp** (0.55); 2023/2024 the West/Plains
  increment is POSITIVE (+0.46/+0.36 raw, ≈ +0.2/+0.1 after the mean) so removing it lowers
  West gas — **C3a-2023/2024 move −0.05 to −0.5 pp** (0.5). Reported at full magnitude;
  never a gate.
  Object gates in the 177 real S→N binding 2025 shoulder hours (control values from
  miso-211/212): South boundary net +0.05 → −0.1 to −0.6 GW (0.5); S→N flow 357 → 450–1,000
  MW mean (0.5); free-tier share 2.8 → 4–12 % (0.5); Indiana−South spread −0.16 → +0.3 to
  +3 $/MWh (0.5); South gas dispatch 15.56 → 15.9–16.4 GW (0.6); Midwest gas dispatch in
  those hours −0.2 to −0.8 GW (0.5).
* **P-6 K-gates.** No K-1 band exit (largest class-year move ≤ 0.5 TWh, ST_GAS|2024
  headroom 0.514 is the tightest and the arm moves ST_GAS TOWARD zero) (0.7); K-2 C3b no
  PASS→FAIL; K-3 no new D-4 failure; K-4 no D-1 flip; K-5 no PASS→non-PASS; K-6 ledger 41 → 41
  (no new free parameter: a boolean scope on an existing measured input).

## 4. Decision rules

* **Phase-0 kill (no arm, no solve):** (a) L-1 shows the print path already excludes the
  basis-carrying cells (impossible from the code read — stated for completeness); or (b)
  L-4 shows the basis was identified NET of the prints (then the layering is intentional;
  finding says so, owner-court). Otherwise **the arm is built and solved regardless of
  L-3's size** — a rule-19 repair is structural (rule 1); size is reported, not gated.
* **A/B verdict order (miso-210 scorer):** S-1 fail ⇒ VOID. Any K-1..K-5 kill ⇒ reported at
  full magnitude, NOT promoted by the scorer, owner decision. Kills silent and values moved
  ⇒ **keeper candidate, PROMOTED as a structural repair** under the owner's standing bar
  ("if structural integrity improves but gates regress that may still be a keeper"),
  whichever way C3a moves. Kills silent and inert ⇒ still promoted (a double-counted
  premium is wrong at any magnitude), disclosed as inert.
* **Cells:** new row `miso_zonal_gas_basis_skip_923_priced` (field-added, rule 28c) — MISO
  K if promoted / R if a kill is upheld / O if owner-court; `.` elsewhere (rule 25 — other
  ISOs' print-path × basis interaction is theirs to test: PJM/CAISO share the mean-zero
  core and `gas_plant_monthly_fuel_pricing`, so they enter as U in their own lanes, never
  filled from MISO). `zonal_gas_basis` stays K with the layering evidence appended and the
  miso-119 misattribution corrected.

## 5. Reported against interest, in advance

* If P-1 holds, the honest headline is that the mean-zero basis is near-redundant in MISO
  backcasts; the repair then mostly REMOVES a mechanism's backcast effect rather than
  adding structure — said so, with the forward story (forecast cells are all trajectory)
  stated beside it.
* The static reach is a ceiling at fixed prices; the LP's response is the A/B's.
* The C3a-2025 direction predicted FAVOURABLE (toward zero) is a risk for motivated
  reasoning: the promotion rule above does not read C3a, and the finding reports it with
  the prereg sign beside it either way.
* The 2025 West/Plains row (−0.585) is flagged in the CSV as "MN withheld 2025" — a
  thinner series; the arm removes it from most rows, which is also disclosed as a data
  quality consequence, not a motive.

## 6. Governance

Rule 15: the arm bundle is registered (probe or keeper). Rule 28(b)/(c): new field ⇒ base
row + six cell lines; `zonal_gas_basis` evidence; §5.4 stamp. Rule 27: blob-verify;
`src/` edited locally with the Edit tool. Rule 24: the flag is a `ScenarioConfig` field
recorded in `run_config.json`. Rule 13: 923 prints, HH spot read as diagnostics in phase 0;
the arm changes no input, only which cells receive an existing one. Rule 12: years
sequential in one invocation. DO-NOT-REDO: `gas_hub_basis_overlay` R, offer level/spread
R/I, `miso_rdt_measured_limit` R, `miso_south_gas_delivered_cost_basis` R; the
average-vs-marginal convention is owner-court and is NOT touched.

Next shorthand: **miso-214**.
