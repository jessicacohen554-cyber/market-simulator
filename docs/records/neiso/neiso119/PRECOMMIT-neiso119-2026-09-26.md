# PRECOMMIT neiso-119 — solve-year gas-margin anchor + winter fuel-security conduct roster (2026-09-26)

Keeper (precondition verified): `2026-09-26-neiso-118-canal-ct`, bundle `results/calibration/neiso118_span`, 2019–2025.
Train tier 2023–2025 CALIBRATED (C3c ledgered); full span NOT-YET on ONE line: C3a price_mean 2019 $35.86 vs RT
$32.59 (+10.03 %, band ±10 %).

## 1. Phase 0 (zero LP) — `docs/handoffs/neiso119/phase0_*`

**(d) The 2019 price residual is not a 2019 defect.** `phase0_price_2019.py` (keeper hourly `system_<Y>.parquet` vs
committed hourly RT, load-weighted on model demand). In EVERY year the model lifts the cheap hours and under-prices the
peaks; 2019 is simply the year with too few peaks to offset:

| year | model / RT $/MWh | contrib. of hours with RT ≤ $25 | contrib. of hours with RT > $60 | p5 model / RT |
|---|---|---|---|---|
| 2019 | 35.86 / 32.59 | **+4.93** | −1.98 | 20.6 / 13.3 |
| 2020 | 26.78 / 25.14 | +4.52 | −1.47 | 18.9 / 10.8 |
| 2021 | 49.17 / 47.77 | +2.06 | −4.60 | 27.4 / 17.9 |
| 2022 | 89.54 / 91.16 | +1.11 | −8.74 | 38.9 / 32.5 |
| 2023 | 38.37 / 38.10 | +4.00 | −4.90 | 22.5 / 15.2 |
| 2024 | 43.02 / 41.68 | +3.39 | −4.45 | 26.2 / 17.3 |
| 2025 | 72.70 / 70.23 | +1.72 | −3.76 | 34.6 / 22.0 |

2019 by month: Jan–Oct all +$2.3–7.3, Nov +1.0, Dec −3.1. `phase0_marginal.py`: in the cheap hours a **CC_REGULAR**
tranche sits within $0.50 of the zonal price in ~100 % of hours.

**The structural defect found in that offer: the gas net-revenue margin is identified at a frozen 2023–2025 anchor.**
`gas_offer_net_revenue_margin` (armed in the keeper) prices every gas markup as `offer_markup_hr × anchor` with
`anchor = 4.0763` $/MMBtu, the mean of 2023–2025 delivered gas, applied to every solved year. The derive's own
identity — at `fuel == anchor` the offer reduces to the calibrated band multiplier — holds only inside that window.
2019 CC_REGULAR (`phase0_cc_offer.py`): markup 0.842 MMBtu/MWh × 4.0763 = **$3.43/MWh** fixed, vs $1.4–2.2 if it
scaled with the year's gas (Apr–Oct $1.66–2.56). `gas_offer_margin_anchor_vintage` (pjm-169 F4; built, zero DOF,
default off; MISO **K**, PJM **R**, NEISO **U**) evaluates the SAME formula on the solved year.

**(b) The winter fuel-security floor binds units that are metered offline.** `phase0_fuelsec.py` / the derive below:
across the floor's own cold-day window, CEMS boiler units were online 2019: Middletown 562 **0 %**, Newington 8002
**1 %**, West Springfield 1642 **0 %**, Merrimack 2364 45 %, Bridgeport 568 22 %; the floor forces **1.06 TWh** of
2019 energy (ST_GAS 0.56 vs 0.23 TWh actual ST_GAS class energy). Rule 17: a floor binding in hours its driver
evidence says the unit is offline is a defect by definition; the mechanism has no `D4_WINDOWS` entry, so D-4's
conduct rider never tested it.

**(a)** Class-preserving re-derives (not armed): ST_GAS adds 8002 (pooled 13.00) and 6156 (11.46); CHP adds Masspower
10726 (~8.5, 2019–22). Both baselines reproduce the committed artifacts byte-for-byte. **(c)** Canal 3: EIA-860 files it
**OA** in the 2023/2024 vintages and DFO-primary / NG-secondary from 2023; EIA-923 shows mostly gas. No 2019 effect.

## 2. Owner rulings (2026-09-26, before any solve)

1. **"Anchor vintage"** — arm `gas_offer_margin_anchor_vintage` for NEISO.
2. **"Fuel-security conduct fix"**, form **"Conduct roster"**: a plant stays in the floor only if CEMS shows it online
   in ≥ 50 % of the floor's cold-day window hours pooled over the OTHER years (leave-one-year-out; D-4's threshold).
3. Not armed: (a) ST/CHP re-derive, (c) Canal 3 fuel class.

## 3. Change (this commit)

- `ScenarioConfig.neiso_winter_fuelsec_conduct_roster` (gated, default off, byte-identical off; cache-key optional
  field at `"False"`); `constants.WINTER_FUELSEC_CONDUCT_MIN_ONLINE_SHARE = 0.5` (D-4's median-output test).
- `winter_fuel_inventory.winter_fuelsec_cold_window` — the ONE window definition, now shared by the floor and the
  derive (refactor; the floor's window is byte-identical); `winter_fuelsec_conduct_roster` (leave-one-year-out
  loader); `apply_winter_fuelsec_mustrun(eligible_plants=None)`.
- `scripts/data/derive_neiso_winter_fuelsec_conduct.py` → `data/raw/_processed-legacy/winter_fuelsec_conduct_NEISO.csv`
  (32 plant-year rows; sha256 `1952101d29f51222bba9f5b8579a4dccc2e762a76f705238cc525b0a84fb5a58`). CEMS boiler units
  only (CTs / CC blocks excluded — this is what moved Bridgeport 568 from phase 0's 45–100 % to 2–22 %: phase 0 summed
  its CC block).
- Tests: `tests/unit/data/test_winter_fuel_inventory.py` (+3). Matrix row `winter_fuelsec_conduct_roster` + a cell in
  every ISO shard (rule 28(c)); NEISO cell **O** until the RESULT.
- Pre-existing, not this lane's: 8 unit tests fail identically on `main` without this change (d53 / d60 pinned keys,
  caiso ST peak, zonal-anchor vintage, NWPP demand, SOCO outage companion).

**Resolved roster (leave-one-year-out):** 2019 **none**; 2020–2025 **{2367 Schiller}** (pooled 0.70). This is narrower
than the phase-0 estimate put to the owner ("only Bridgeport would keep a floor"): with boiler-only metering Bridgeport
falls to 0.15 pooled and Schiller rises to 0.70. Declared here, before any solve.

## 4. LP-input diff (zero LP; `lp_input_diff.py`, fleet_only, keeper recipe vs armed, every year)

Unit ids identical in every year. Winter-fuelsec floor energy (TWh), mean `mc_base` shift ($/MWh) by class:

| year | anchor | floor control → arm | CC_REGULAR | CC_CHP | CT_PEAKER | ST_GAS |
|---|---|---|---|---|---|---|
| 2019 | 4.0763 → 3.1751 | 1.063 → **0** | −0.86 | −0.80 | −7.28 | −4.07 |
| 2020 | → 2.0025 | 0.561 → 0.033 (2367) | −1.93 | −1.86 | −17.09 | −9.91 |
| 2021 | → 4.5344 | 0.676 → 0 | +0.42 | +0.44 | +3.42 | +1.60 |
| 2022 | → 9.1574 | 0.400 → 0 | +4.69 | +4.95 | **+37.60** | +17.63 |
| 2023 | → 2.9365 | 0.173 → 0 | −1.05 | −1.02 | −7.90 | −2.84 |
| 2024 | → 3.0304 | 0.430 → 0 | −0.96 | −0.95 | −7.45 | −3.81 |
| 2025 | → 6.2264 | 0.121 → 0.037 (2367) | +2.03 | +1.95 | +15.13 | +5.91 |

The CT_PEAKER shift is large because its peak band carries a 4.0× multiplier (large `offer_markup_hr`): the anchor
moves the CT scarcity offers most, so 2022 and 2025 peak prices will rise. That is the formula's own consequence,
declared here, not selected.

## 5. G-DRIFT (rule 29(b)) — neiso-118 pin `faa5bd59` → HEAD `9149be2c`: ALL INERT

10 files: `apply_miso_winter_gas_daily_delivered` / `data/fuel/basis/miso.py` / `resolve.py` (MISO-only branch,
default off); `admit_standby_units` (`paths.py`, `eia860.py`, `outages.py`, `runner.py`, `run_calibration.py`) —
default off, absent from the keeper recipe, byte-identical off by construction. **Rebase window `9149be2c` → `76eaeeea`**
(main moved during phase 0): 5 files — `ercot_dam_availability_event_cap_per_unit` (R-ERCOT-7; `arrays.py`, gated on the
ERCOT field, default off) and `unit_outage_coal_extract_basis_share` (`outages.py`, `floors.py`, `run_calibration.py`;
default off) — both absent from the keeper recipe (recorded `None`), INERT. Form 4: the keeper is the control.

## 6. Recipe — declared before any solve

Every leg: `uv run python scripts/replay_keeper.py results/calibration/neiso118_span --years <Y>
--out-dir results/calibration/neiso119_<Y> --set gas_offer_margin_anchor_vintage=true
--set neiso_winter_fuelsec_conduct_roster=true`. Offer curve byte-identical. DOF: zero new (the anchor is re-evaluated
by the frozen formula; the 0.5 share is D-4's).

## 7. Gates — declared before any solve (rule 1: structural; a pass does not promote, a fail does not kill)

- **G1 recipe:** `docs/handoffs/neiso119/shard_check.py` ALL PASS on every leg (delta = the two flags + the pinned
  anchor, conduct and CT artifact sha256, std extract, classifier); log lines `coal per-yard budget (NEISO <Y>)` and
  `winter fuel-security conduct roster` present.
- **G2 mechanism:** D-2 `winter_fuelsec_mustrun` forced energy = 0 in 2019, 2021–2024 and ≤ 0.05 TWh (plant 2367 only)
  in 2020/2025; the recorded `gas_offer_margin_anchor` equals §4's anchor to 4 dp in every year.
- **G3 no silent breakage:** full span and train tier re-scored with `calibration_verdict.py --run-id`.
- **Predictions (price-taker, not LP):** 2019 C3a between +6 % and +9.5 % (**PASS**); 2020 roughly −2 % to +3 %;
  2022 and 2025 mean price UP (2025 is the risk: +3.5 % → +5–9 %); 2023/2024 down ≈ $1; ST_GAS 2019 energy down
  ≈ 0.5 TWh toward the 0.23 actual; coal 2019 down ≈ 0.4 TWh.
- **Promotion standard (owner):** promote if structurally faithful and nothing regresses, or if structure improves even
  with a gate regression, stated at full magnitude.

## 8. Shard plan (rule 36 — one shard per year; rule 34 — full bundle pushed)

Seven shards `neiso119_<Y>`, 2019–2025 (the keeper's whole year set), pinned to this doc's commit SHA via an explicit
`git fetch origin <sha> && git checkout --detach <sha>` step 0 (neiso-118 lesson). Branch `claude/neiso119-<Y>`. Each
curates `coal_stocks`, `coal_receipts`, `hydro_plant_modes --iso NEISO` before solving. Full bundle incl.
`dispatch/<Y>_P1.parquet` pushed via `.gitignore` negation + plain `git add`. Parent composes
(`docs/handoffs/neiso119/compose_span.py`), attests, registers `--no-prune`, scores; it never solves (rule 32(a)).
