# PRECOMMIT — R-CAISO-3: Pastoria and the winter over-import (2026-09-25)

Lane R-CAISO-3. The keeper is `2026-09-25-caiso-r2-cc-gross` (bundle `rcaiso2_ccid_span`, 2022–2025, pin
`640c9fe3`), DETERMINATION CALIBRATED on thin margins (C1 2023 CC_REGULAR −5.14 vs ±5.27; C4 2023 gas NRMSE
0.298 vs ≤0.30). The parent solves nothing (rule 32(a)). Every number below is zero LP and was written
before any shard launched.

## 0. Housekeeping owed by the R-CAISO-2 promotion — DONE

`prune_iso_runs.py --iso CAISO --force-uncite` removed `2026-09-24-caiso-r-inputs-vintage` (its sidecar, payload
and bundle `rcaiso_inputs_span`). `audit_keepers.py --iso CAISO` passes (E13). The commit is on this lane's branch.

## 1. Object 1 — Pastoria 55656: the cause is a CEMS heat-input bias

**What the model sees.** Pastoria and High Desert 55518 are both in SP15_rest. Both are IPP non-CHP plants,
and both are fed directly by **Kern River Gas Transmission** with no LDC (EIA-860 plant file, *Natural Gas
Pipeline Name 1*). In the rebuilt 2023 keeper fleet they carry the same gas price every month (Jan 18.8 /
18.7 $/MMBtu implied), so **the gas delivery point is not the difference.** The difference is the heat rate:
Pastoria is applied at 7.691 (its eGRID rate, after R-CAISO-2 refused its gross < net rows), High Desert at
7.239. The model therefore always ranks High Desert ahead, which dispatches 3.58 of 4.08 TWh in 2023, while
Pastoria gets 1.81 of 4.34. In the real market Pastoria runs **harder** than High Desert: capacity factor
0.64 against 0.49 in 2023.

**The independent measurement (new this session).** EIA-923 Schedules 2–5, *Total Fuel Consumption MMBtu*,
is the owner's fuel filing and is independent of CEMS. Its CT+CA rows, divided by EIA-923 net generation:

| year | Pastoria EIA-923 fuel / net | Pastoria CEMS HI / net (= eGRID) | CEMS HI ÷ EIA-923 fuel | High Desert CEMS ÷ EIA-923 |
|---|--:|--:|--:|--:|
| 2019 | **7.047** | 7.337 | 1.041 | 0.998 |
| 2020 | **7.079** | 7.718 | 1.090 | 1.028 |
| 2023 | **7.036** | 7.691 | 1.093 | 0.998 |

The step is in CEMS, not in the plant. From 2020, all three Pastoria units' CEMS heat-input ÷ gross jumps
together: CT004 goes 7.14 → 7.50, and it never lost its steam turbine. EIA-923 fuel ÷ net holds at
7.04–7.08. eGRID 7.69 is CEMS HI ÷ EIA-923 net (`HTIANSRC = EPA/CAMD`), so it inherits the bias.

Measured on the owner's own fuel, **Pastoria is the most efficient CC in SP15_rest**: 7.04 against High Desert's
7.22. That is what its real dispatch says too.

Census of every CAISO CC (CEMS ÷ EIA-923 fuel, 2019 / 2020 / 2023): most plants sit in 0.95–1.05. Pastoria
(1.041 / 1.090 / 1.093) is the only plant above 1.05 in 2020 and 2023. Mountainview 0.94–0.96 and Carson
0.94–0.96 sit on the other side.

**Lever C (wave 2, not launched here).** Add a heat-input identity guard to `derive_campd_cc_heat_rates.py`.
CEMS heat input and EIA-923 fuel consumption measure the same fuel, so a plant where they disagree is priced
on the EIA-923 fuel ÷ EIA-923 net rate. The guard needs an intake first: EIA-923 Schedule 3 fuel consumption
for 2019–2025, which is not in the repo; the zips are fetched and staged in the session scratchpad. Its
tolerance must be fixed from measurement physics before any solve, and it will be stated in its own
PRECOMMIT addendum. Rule 23: the re-derivation is justified by the data defect, never by the residual.
Rule 25: CAISO's artifact only.

## 2. Object 2 — the Dec 2022–Mar 2023 over-import: two structural defects in the import offer

A fleet-only rebuild of the keeper puts the desert-SW import offers **below zero in January 2023**:

| 2023, $/MWh (month mean) | Jan | Feb | Mar | Jun | Dec |
|---|--:|--:|--:|--:|--:|
| DSW_CCGT | **−21.5** | 42.5 | 33.9 | 38.9 | 61.7 |
| DSW_CT | **−53.1** | 43.4 | 29.4 | 42.7 | 68.1 |
| DSW_solar_PV (firm, static ladder) | **−29.5** | 37.7 | 26.4 | 43.8 | 48.9 |
| WECC_DSW node price (P1) | **−0.1** (median −15.3) | 49.9 | 44.1 | 27.4 | 44.7 |

In Dec 2022 the measured Palo Verde hub averages 249.9 $/MWh, but DSW_CCGT is offered at 183.0 and DSW_CT at 148.5.

**Defect A — the gas coupling stacks on a measured hub price.** `inject_caiso_import_gas_coupling` adds
`(iso_hub_monthly_gas_prices − iso_monthly_gas_prices) × HR` to each DSW gas tranche. Its premise, in its own
docstring, is a tranche level "fitted against the F923 delivered world". Under `caiso_per_hub_intertie`,
however, `inject_caiso_per_hub_intertie_prices` has already set DSW_CCGT and DSW_CT to the **measured Palo Verde
intertie LMP**, which carries the region's gas cost. `inject_caiso_import_hub_prices` says those rows "are then
overwritten off measured gas by `inject_caiso_import_gas_coupling`", but the code adds instead. The operand
is the N3050CA3 citygate (the LDC purchase price, which lags) minus F923 delivered:

| $/MMBtu | 2022-12 | 2023-01 | 2023-02 | 2023-03 | typical other month |
|---|--:|--:|--:|--:|--:|
| spot (HH + N3050 basis) | 11.42 | 27.62 | 10.71 | 4.41 | — |
| F923 delivered | 23.10 | 38.68 | 12.19 | 7.49 | — |
| delta | **−11.68** | **−11.06** | −1.47 | −3.08 | −0.1 to −2.6 |

That is −81 / −121 $/MWh on DSW_CCGT / DSW_CT in Dec 2022, and −77 / −115 in Jan 2023. The coupling makes
the desert-SW gas imports cheaper during the western gas spike.

**This is new evidence against caiso-279.** caiso-279 ablated the whole coupling on 2022 and was refuted on
its own G-DIR gate. Its §3 operand was computed by hand from weekly SoCal spot prints (33.77 $/MMBtu in
December, giving a **+74** $/MWh shift) and not from the model's own operand. The model's operand is **−81**.
caiso-279 pre-registered the wrong sign for December, and its measured December response (ablation raised
the price) is exactly what a −81 coupling predicts. Its other finding still stands and is not reopened here:
the per-corridor measured import envelope binds on Dec 23–31 2022.

**Repair A — `caiso_import_gas_coupling_ladder_only`** (new, CAISO-only, default off). The coupling skips
any tranche a measured hub series has repriced (`_caiso_measured_hub_priced_tranches`, which mirrors the
backcast overlay's own gates). Static-ladder rows, i.e. the `caiso_perhub_firm_base` DSW_solar_PV block, keep
the coupling exactly as before. Rule 19: the measured hub becomes the one gas channel for a hub-priced row.
The repair adds zero parameters. In forecast years it is inert, because no measured series exists and the
set is empty.

**Defect B — the Jan 1–Mar 26 2023 OASIS gap is filled with a FORECAST.** Both hubs have 2,040 hours missing
(744 / 672 / 624 by month). `measured_import_hub_prices` fills them with
`caiso_hub_reference_price = (HENRY_HUB_TRAJECTORIES[mid][2023] + static basis) × HR × shape`, which gives
Palo Verde about 39 $/MWh and Malin about 35 $/MWh through the western gas crisis. Measured Dec 2022 was
250 / 262.

**Repair B — `caiso_intertie_gap_fill_measured_gas`** (new, CAISO-only, default off). The same formula takes the
**measured monthly delivered-to-electric-power gas of the hub's host state** (EIA N3045: AZ for Palo Verde, OR
for Malin; a location crosswalk, `spec.CAISO_INTERTIE_HUB_GAS_STATE`) in place of the forward HH plus static
basis. HR and shape are unchanged, so the repair adds zero parameters. **It was identified out of sample on
fully measured months, never on a model output:**

| monthly-mean fit to the MEASURED hub | forward fill (current) | measured-regional-gas fill |
|---|---|---|
| 2022 PALOVRDE: corr / MAE $/MWh | 0.47 / 45.7 | **0.94 / 27.3** |
| 2022 MALIN | 0.16 / 50.2 | **0.96 / 12.9** |
| 2023 PV / Malin (measured months) MAE | 15.2 / 19.5 | **9.3 / 10.0** |
| 2024 PV / Malin MAE | 7.1 / 12.5 | **6.2 / 11.4** |
| 2025 PV MAE | 17.2 | **11.1** |

On Dec 2022 the measured-gas fill gives PV 253 against 250 measured, and Malin 218 against 262. Only 2023
has a gap in 2022–2025 (2022, 2024 and 2025 each carry a single DST hour, which `interpolate(limit=2)`
fills), so B is inert outside 2023 **by construction**.

**Why B is armed only together with A.** In gap hours, B's fill already carries measured gas, so the coupling
on top of it would be the defect-A double count again. B alone is therefore not a coherent arm.

**Zero-LP offer-array delta** (fleet-only rebuild, AB armed, month mean $/MWh):

| row | 2022-12 keeper → AB | 2023-01 | 2023-02 | 2023-03 |
|---|---|---|---|---|
| DSW_CCGT | 183.0 → 264.4 | −21.5 → 232.9 | 42.5 → 106.4 | 33.9 → 64.4 |
| DSW_CT | 148.5 → 269.5 | −53.1 → 238.8 | 43.4 → 112.4 | 29.4 → 70.3 |
| PNW_midC | 266.8 → 266.8 | 39.5 → 242.4 | 38.5 → 85.4 | 44.0 → 69.8 |
| DSW_solar_PV (static) | −33.8 → −33.8 | −29.5 → −29.5 | unchanged | unchanged |

In 2022, 2024 and 2025, A moves DSW_CCGT / DSW_CT up by `−delta × HR` in every month (typically +3 to +18
$/MWh). Every in-state row is byte-identical.

**Residual stated, not repaired:** the static DSW_solar_PV block keeps its coupling, and it stays negative in
Dec 2022 and Jan 2023. That block is the self-scheduled firm floor (`caiso_firm_import_selfschedule`), so its
price bites only above the floor. The coupling on a static contract block is its designed use, so no second
change is taken on it here.

## 3. G-DRIFT (rule 29(b)) — keeper pin `640c9fe3` → this lane's base

* **Code audit**, read-only, every hunk in `src/market_sim`, `scripts/run_calibration*.py` and `scripts/lib`
  (plus `data/fleet`, `replay_keeper`, the verdict scripts): **ALL INERT for the LP.** Each hunk is gated to
  another ISO, sits behind a flag that is off and absent from the recipe, is a doc change, or copies the
  former `COAL` values onto the coal subclasses unchanged. COAL-SUB relabels Argus Cogen 10684 (15 MW)
  `COAL` → `COAL_BIT`. Its offer curve is unchanged (`COAL_BIT` bands equal the old `COAL` bands), and
  `replay_keeper` has nothing to translate, because overrides and deltas are `{}` and
  `ScenarioConfig._retire_bare_coal_class` folds the recorded `COAL` key. **Scoring only:** about 0.1 TWh
  moves from the `COAL` to the `COAL_BIT` row. That is closer to the benchmark's `COAL_BIT` and far inside
  every band.
* **Mechanical proof.** The fleet was rebuilt at `640c9fe3`, with that commit's own code and its data files
  restored from git, and again at HEAD, for 2022, 2023, 2024 and 2025. `pmax`, `pmin`, `availability`,
  `min_gen`, `heat_rate`, `vom`, `emission_rate`, `zone_idx`, `mc_base`, `demand`, the wind/solar
  cap/cf/mc arrays and the storage power cap are **byte-identical in all four years**. The only difference
  is the 8 `plant_group` labels of 10684.

**Form 4 is valid.** The keeper's committed bundle is the control, and no control solve is spent.

## 4. Shard plan (rules 32, 34, 36)

Recipe: `scripts/replay_keeper.py results/calibration/rcaiso2_ccid_span --years <Y>` plus `--set` for each
flag below. One year per shard, and each shard pushes its full bundle.

| shard | year | flags | out-dir |
|---|--:|---|---|
| r-caiso-3-A-2022 | 2022 | A | `results/calibration/rcaiso3_A_2022` |
| r-caiso-3-A-2023 | 2023 | A | `results/calibration/rcaiso3_A_2023` |
| r-caiso-3-A-2024 | 2024 | A | `results/calibration/rcaiso3_A_2024` |
| r-caiso-3-A-2025 | 2025 | A | `results/calibration/rcaiso3_A_2025` |
| r-caiso-3-AB-2023 | 2023 | A + B | `results/calibration/rcaiso3_AB_2023` |

**Candidate AB span** = A-2022 + AB-2023 + A-2024 + A-2025. That composition is exact, because B is inert
outside 2023 by construction (§2). **A span** = the four A legs, which serves for attribution.

## 5. Stated before the solve

**Direction, not a gate.** A raises DSW gas-import offers in every year, so imports should fall and
CC_REGULAR rise. caiso-279's full 2022 ablation measured imports −1.52 TWh, CC_REGULAR +1.29 TWh and price
+1.41 $/MWh. AB adds a much larger 2023 January–February move. Expect Jan–Feb 2023 imports sharply down,
CC_REGULAR up in the object-2 window, and the 2023 C1 CC_REGULAR row moving toward zero. **Size is not a
criterion**, and neither flag is resized against any result (rule 1 (c)).

**Named risks.** C3a rises in every year. 2025 sits at +9.0% against a 10% band and is the first criterion
at risk. C4-2023 is at 0.298 against a 0.30 ceiling. The Jan–Feb 2023 gap hours are also absent from the
measured-LMP benchmark (the loader's own note), so B cannot move C3a directly in those hours.

**Stop gates (they can kill an arm; none promotes it):**

- **G-IDENT.** Each leg's `run_config.json` differs from the keeper leg only in the declared flag(s).
- **G-FOOT.** In the leg's rebuilt fleet only `WECC_*` import rows move, and they reproduce §2's table
  within ±0.5 $/MWh.
- **G-LIVE.** 2023 January net imports fall under AB.

**Not a keeper if** any of these happen:

- a load-bearing criterion (C1/C2/C3a/C3b) flips PASS → FAIL in any year;
- C6 or C8 fails;
- a second ledgered caveat appears;
- any leg's signature differs.

The owner may still promote on structure (rules 1, 31), so this is a recommendation, not a veto.

Offer-curve multipliers are unchanged, the DOF ledger stays 9/6, and there is no `authorized_price_tuning` block.

## 6. Routed, report only (rule 25)

- **CC gross < net rows in other ISOs:** ERCOT 14, MISO 10, NEISO 6, NWPP 5, NYISO 6, PJM 23, SPP 1. Each
  ISO's lane re-derives its own artifact.
- **CEMS-vs-EIA-923 heat-input census:** it is CAISO-only here. Other ISOs' CC artifacts inherit the same
  CEMS basis and are routed the same way.
- **Dec 2022 in-state gas operand:** N3050CA3 citygate + HH gives 11.42 $/MMBtu, while N3045CA gives 27.7
  and F923 delivered gives 23.10. The in-state gas level in December 2022 is a separate question, and this
  lane does not open it.

## 7. ADDENDUM (written before any wave-2 solve) — lever C, Pastoria: the EIA-923 identity fallback

**The design needs no threshold.** R-CAISO-2's gross-net identity already *refuses* Pastoria's 2020–2025
rows: their CEMS record is inconsistent with the owner's filing. The refused rows then fell back to eGRID.
But eGRID is **CEMS heat input** ÷ EIA-923 net (`HTIANSRC = EPA/CAMD`), so the same refused CEMS record
came back in through the numerator. Pastoria's CEMS heat input reads ×1.090–1.093 of EIA-923 fuel in
every year 2020–2025 (§1).

**Repair C** is an input correction on the path the keeper already arms (`measured_cc_heat_rates`), the
same route R-CAISO-2 took. It adds no ScenarioConfig field.

* **Intake:** `data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv`. This is EIA-923
  Page 1, every US plant, with total fuel MMBtu and net MWh per plant × prime mover × fuel. It is fetched
  by `scripts/data/fetch_eia923_generation_fuel.py`, with a README and SHA256SUMS (CSV `24f6f341…`).
* **Derive:** `derive_campd_cc_heat_rates.py::apply_eia923_identity`. A row flagged `gross_below_net`
  gets `heat_rate = Σ fuel ÷ Σ net` over the plant's CT/CA/CS prime movers for that year (the pooled row
  uses 2019–2025), provided the rate is inside the existing net physical band. Its flag becomes
  `eia923_identity`. Every row also carries `heat_rate_eia923_identity` as provenance.
* **Model:** `campd_bins._APPLIED_MEASURED_FLAGS = {"ok", "eia923_identity"}`. Every other ISO's artifact
  carries no such row, so it reads byte-identically (rule 25: only CAISO's artifact is re-derived).
* **Rule 23:** the re-derivation cites a data change, the new EIA-923 intake. It does not cite a
  residual.

**Artifact delta** (re-derived with the keeper's provenance posture
`--egrid-family-heat-rates --measured-ct-heat-rates`; new sha256 `ab976786…`). **Exactly the 12
previously refused rows flip, and nothing else moves**, not even the eGRID provenance column:

| plant | rows | applied before (fallback) | applied now |
|---|---|---|---|
| Pastoria 55656 | 2020–2025 + pooled | eGRID 7.67–7.72 | **7.079 / 7.079 / 7.036 / 7.036 / 7.039 / 7.077**, pooled 7.056 |
| Carson 10169 (56 MW) | pooled | eGRID 8.54–8.69 | 9.724 |
| Sanger 57564 | 2024 | eGRID 9.197 | 8.970 |
| Desert Star 55077 | 2024 | pooled 7.587 | 7.646 |
| Alamitos 62115 / Huntington Beach 62116 | 2020 only | pooled | 7.100 / 7.192 (outside the solved span) |

**Zero-LP offer check** (2023 fleet rebuild): Pastoria's committed tranche goes 7.691 → **7.036**. Its
in-the-money share against the keeper's SP15_rest price goes 0.39 → **0.68**, against High Desert's 0.76.

**Wave-2 shards: ABC.** These are pinned to the commit carrying the new artifact, with A and B set by
`--set`. There is one per year, 2022–2025, in `results/calibration/rcaiso3_ABC_<Y>`. ABC − AB (2023) and
ABC − A (2022, 2024, 2025) attribute C. The stop gates and not-a-keeper rules are §5's.

**Direction, not a gate:** Pastoria rises toward its 3.3–4.3 TWh/yr actual, SP15_rest CC rises, and
imports and CT fall. C1 CC_REGULAR 2022 is already +0.64, so expect it to move further positive; that
is reported at full magnitude either way.
