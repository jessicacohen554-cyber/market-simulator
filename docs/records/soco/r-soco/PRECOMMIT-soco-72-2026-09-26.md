# PRECOMMIT — soco-72: the SOCO per-year gas basis, extended over the window the keeper solves

Lane soco-72, 2026-09-26. Written and pushed **before any shard was launched**. The parent solves nothing
(rule 32(a)). Each year is solved in its own shard (rule 36) and each shard pushes its full bundle (rule 34).

Control: the keeper `2026-09-26-soco71-coal-hr-window` (bundle `results/calibration/soco71_span`, legs solved at
`ae5fb43a4fb9df8d4cd5b5b32df655e5cd1d78f2`). Its committed numbers are the control (rule 29(b) form 4). No control
solve is spent.

**Read this first: the lever moves the one failing row the WRONG way.** It is taken because it is a measured input
the keeper does not have (rules 1 / 14), not because it helps the gate. §6 pre-registers that 2019 COAL_BIT gets
worse.

## 0. G-DRIFT (rule 29(b)), keeper sha `ae5fb43a` → HEAD `c8de72bb`

- **Measured.** `scripts/probes/_soco72_gdrift_identity.py` rebuilds the keeper recipe's `fleet_only` arrays at both
  shas on one shared `data/` tree: **ALL LP INPUTS BIT-IDENTICAL**, all seven years. Record:
  `results/calibration/_soco72/gdrift_input_identity.json` (gitignored).
- **Read by hand (code).** Four files changed on the backcast path (`scenarios.py`, `data/fleet/arrays.py`,
  `data/fleet/floors.py`, `data/outages.py`, plus a `run_calibration.py` pass-through). Every hunk belongs to one of two
  new default-off fields absent from the recipe: `unit_outage_coal_extract_basis_share` (SPP-86) and
  `ercot_dam_availability_event_cap_per_unit` (R-ERCOT-7, ERCOT-only). `_extract_basis_groups(False, False)` returns
  `()`, and `extract_basis` is `None` whenever both flags are off, so the refactored branch is unreachable. **INERT.**
- **Read by hand (data).** `git diff ae5fb43a origin/main -- data/` is **empty**. **INERT.**

**Form 4 is valid. The keeper is the control.**

## 1. The 2019 price side, decomposed (zero LP)

`_soco72_phase0.py price`, on the soco-71 legs. "H" = hours in which Barry 3, Crist 641 or Wansley 6052 is
CEMS-synced but model-off. Marginal = partly loaded and priced within $0.50 of its zone price.

**Who is marginal in H:**

| year | H hours | price p50 in H | CC_REGULAR | COAL_PRB | ST_GAS | COAL_BIT | CT_PEAKER |
|---|---|---|---|---|---|---|---|
| 2019 | 8,349 | $32.90 | 18 % (mc $26.2) | 16 % ($32.8) | 13 % ($35.3) | 12 % ($33.1) | 12 % ($34.7) |
| 2020 | 7,905 | $28.54 | 16 % ($21.1) | 11 % | 20 % ($30.6) | 6 % | 19 % ($29.9) |
| 2021 | 4,478 | $34.19 | **44 %** ($33.9) | 12 % | 0 % | 16 % | 0 % |
| 2022 | 1,645 | $57.51 | **51 %** ($53.7) | 0 % | 6 % | 4 % | 9 % |
| 2023 | 3,950 | $32.23 | 15 % | 11 % | 29 % | — | 27 % |

**Are the marginal gas units offered below their own measured cost? No — in 2019 they sit ABOVE it.** Offer fuel
((median `mc_base` − VOM) / HR from the keeper recipe's `fleet_only` build) against each plant's own 2019 EIA-923
receipts, weighted by marginal hours in H:

| year | offer fuel | gap vs own receipts |
|---|---|---|
| 2019 | $3.049 | **+$0.273 / MMBtu** (14 plants) |
| 2020 | $2.536 | +$0.045 (18) |
| 2021 | $4.142 | −$0.089 (13) |
| 2022 | $6.735 | −$1.100 (15) |
| 2023 | $2.879 | −$0.567 (18) |

**What is 2019-specific.** In 2021 and 2022 gas is dear ($3.9 / $6.4 Henry Hub), so a CC sets the price in H at
$34–54 and the cyclers clear. In 2019 Henry Hub is $2.57, the CC fleet offers at ~$26, and the cyclers' measured
offers ($35.8–37.3, soco-71) lie above even the ST_GAS and CT marginal offers. **The gas side is not too cheap in
2019. If anything it is $0.27/MMBtu too dear**, which already *helps* coal.

**Interchange (R1) is closed.** SOCO has no import node. The model's demand is EIA-930 net generation
(245.10 TWh in 2019, identical to the EIA-930 `net_gen` series), so no modelled import can displace coal.

## 2. The defect: the per-year gas basis never measured 2019–2022

- `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR["SOCO"]` (K mechanism `gas_basis_measured_by_year`, armed in the keeper)
  has rows for 2023 / 2024 / 2025 only. These are the years SOCO-55 served.
- The keeper's span became 2019–2025 at R-SOCO. Every 2019–2022 SOCO gas unit therefore falls through to the 2024
  scalar **0.64**. The table's own comment reserves that fall-through for "a forecast year, a year whose receipts are
  not yet filed". **The 2019–2022 receipts are filed and committed.** This is the same defect class as soco-71: an
  artifact that does not measure the window it declares.
- **Re-derived, same construction, unchanged:** q-weighted EIA-923 delivered gas to BA=SOCO plants
  (`data/raw/eia-860/eia860_plant.parquet`) minus the Henry Hub annual mean. It reproduces the committed 2023/2024/2025
  rows **byte-for-byte** (26 / 27 / 27 plants; 646,487,128 / 650,711,973 / 641,283,196 MMBtu; +0.4931 / +0.6395 /
  +0.6540).

| year | plants | MMBtu | q-wt delivered | Henry Hub | **measured** | applied | error |
|---|---|---|---|---|---|---|---|
| 2019 | 23 | 588,591,336 | 2.8337 | 2.5651 | **+0.27** | 0.64 | +0.37 too dear |
| 2020 | 24 | 571,328,321 | 2.3546 | 2.0337 | **+0.32** | 0.64 | +0.32 too dear |
| 2021 | 25 | 592,859,329 | 4.2121 | 3.9097 | **+0.30** | 0.64 | +0.34 too dear |
| 2022 | 26 | 626,610,774 | 7.6213 | 6.4191 | **+1.20** | 0.64 | −0.56 too cheap |

- **Precision:** 2dp, the family convention SOCO-55 fixed. Not selectable by a result.
- **Declared misalignment (rule 14), measured and not selected.** The current plant file excludes the former Gulf
  Power plants that the 2019–2022 runs still carry.
  - The run's own gas fleet gives 0.28 / 0.32 / 0.30 / 1.26.
  - The per-year EIA-860 vintage BA gives 0.28 / 0.32 / 0.32 / 1.27. It is not the committed construction: it would
    move 2023 to 0.59.
  - The committed construction is kept because it is the only one of the three that reproduces the committed rows.
    Every variant agrees in sign and to ≤ $0.07.
- **Zero free parameters.** Four measured rows on one existing K mechanism. No new field. **Rule 13:** the same
  quantity is producible for any forward year from that year's receipts.
- **Code:** four rows added to `src/market_sim/config/fuel_trajectories.py`. The solve-surface declaration stays frozen
  at `f8cc22e122024b9c`, so SOCO's key moves (lane-added-moved `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR`). No other ISO
  has a row.

## 3. Census (zero LP): the lever in the fleet

`_soco72_phase0.py fleet-gas`: a `fleet_only` rebuild on the keeper recipe, live table against the table with the four
rows.

| year | Δ basis | units | `mc` moved | pmax / min_gen / avail | moved-unit median Δmc | Δmc / (Δbasis × HR) |
|---|---|---|---|---|---|---|
| 2019 | −0.37 | 339 | 225 (CC / CT / ST tranches) | identical | −$3.58 | 0.9500 every unit |
| 2020 | −0.32 | 340 | 225 | identical | −$3.10 | 0.9500 |
| 2021 | −0.34 | 347 | 236 | identical | −$3.30 | 0.9500 |
| 2022 | +0.56 | 348 | 232 | identical | +$5.40 | 0.9500 |
| 2023–25 | 0 | — | **0** | identical | — | — |

- 0.95 is the median of the monthly `GAS_MONTHLY_SEASONALITY` factors. The basis rides inside the seasonally shaped
  delivered price, which averages 1.0 over the year.
- Coal, nuclear, hydro and the per-unit F923-priced gas units do not move.
- **2023–2025 LP inputs are bit-identical to the keeper's.**

## 4. Greedy estimate, NET of the instrument's own bias

`_soco72_phase0.py greedy-gas`.

- **Construction.** In every zone-hour whose marginal set holds a gas unit, the price moves by Δbasis × the median
  marginal gas HR. All eight coal plants are re-dispatched against that price as price-takers, with soco-71's refill
  rule. The result is net of the same greedy on the unshifted price.
- **Stated limits.** Coal- or hydro-marginal hours are held fixed. The 0.95 seasonal median is not applied, which
  overstates the shift by ~5 %.
- C1 is `calibration_verdict.score_fuelmix` on the keeper's committed payload. C4 is the scorer's construction.

| year | COAL_BIT pp | COAL_PRB pp | ST_GAS pp | CC_REGULAR pp | CT_PEAKER pp | C4 coal r / NRMSE |
|---|---|---|---|---|---|---|
| 2019 | −3.09 → **−3.46 FAIL** (−9.34 TWh) | +2.66 → +2.09 | −2.74 → −2.51 | +2.37 → +2.55 | +0.79 → +1.31 | 0.902 / 0.158 → 0.871 / 0.194 |
| 2020 | −1.65 → −1.74 | +0.35 → +0.27 | −2.19 → −2.18 | +1.91 → +1.95 | +1.40 → +1.51 | 0.891 / 0.276 → 0.894 / 0.279 |
| 2021 | +1.43 → +1.25 | +1.60 → +1.53 | **−2.77 → −2.76** | +1.35 → +1.51 | −0.69 → −0.62 | 0.874 / 0.227 → 0.875 / 0.223 |
| 2022 | +0.93 → +0.98 | **+2.67 → +2.68** | −2.28 → −2.30 | −0.45 → −0.47 | −0.81 → −0.83 | 0.814 / 0.236 → 0.815 / 0.237 |
| 2023–25 | = | = | = | = | = (+2.40) | = |

2019 plant deltas (TWh): Scherer −0.88, Miller −0.51, Bowen −0.47, Wansley −0.31, Crist −0.11, Barry −0.02.
Class: COAL_PRB −1.39, COAL_BIT −0.91, CT_PEAKER +1.28, ST_GAS +0.57, CC_REGULAR +0.44.

## 5. Recipe and hard stops

Each shard runs one year `<Y>` ∈ {2019, …, 2025}, pinned to the SHA that carries this document, which it pins
itself as step 0:

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install --no-deps -e .
.venv/bin/python scripts/hydrate_data.py --profile soco
PYTHONPATH=. .venv/bin/python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. .venv/bin/python scripts/data/curate_demand_profile.py
.venv/bin/python scripts/replay_keeper.py results/calibration/soco71_span --years <Y> \
  --out-dir results/calibration/soco72_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --note "soco-72 <Y>: soco-71 keeper recipe + GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'] extended to 2019-2022 (rule 14/23 source coverage)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- `git rev-parse HEAD` equals the pinned SHA.
- `run_config.json` `environment.packages` equals {highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3,
  pyarrow 24.0.0, pydantic 2.13.4}.
- `.venv/bin/python -c "from market_sim.config.fuel_trajectories import GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR as g; print(g['SOCO'])"`
  prints `{2019: 0.27, 2020: 0.32, 2021: 0.3, 2022: 1.2, 2023: 0.49, 2024: 0.64, 2025: 0.65}`.
- `sha256sum data/raw/_processed-legacy/campd_coal_heat_rates_SOCO.csv` equals `a55796…9d47`, and
  `thermal_tranches_SOCO.csv` equals `ab5ec265…22ad7`.
- `scenario_config` shows all eight `--set` fields true, plus `gas_basis_differential_measured_by_year` true and
  `gas_plant_monthly_fuel_pricing` false.
- Every band is 1.0.
- `dispatch/<Y>_P1.parquet` is present.
- `gas_prices[<Y>]` equals the keeper's value (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- The solve log carries `container preflight:` and `memory peak:`.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (identity).** In 2023, 2024 and 2025 the leg's `class_hourly` and `unit_hourly` `mw` and the system price are
  byte-identical to soco-71's legs, because the inputs are bit-identical (§3) and the year is isolated. **A difference
  there is a stop-the-line finding.**
- **E2 (direction).**
  - 2019–2021: the system price falls; COAL_BIT and COAL_PRB fall; CT_PEAKER, ST_GAS and CC_REGULAR rise.
  - 2022: the reverse, and small.
  - Nuclear, hydro and solar: |Δ| ≤ 0.1 TWh.
- **E3 (the failing row gets WORSE).** 2019 COAL_BIT −3.09 pp → **≈ −3.4 to −3.5 pp**, −8.43 → ≈ −9.3 TWh. Still
  FAIL. The LP may move it further than the greedy, because it also re-commits the ST_GAS campaign units and lets
  gas displace coal in coal-marginal hours, which the greedy holds fixed.
- **E4 (side-effect risks, declared now).**
  - **2019 C4 coal NRMSE** ≈ 0.19, r ≈ 0.87. Both still PASS (0.30 / 0.70).
  - **2022 COAL_PRB** +2.67 → ≈ +2.7. The thinnest row and the most likely new FAIL.
  - 2019 COAL_PRB +2.66 moves away from its band (≈ +2.1). 2019 ST_GAS −2.74 moves in (≈ −2.5).
  - 2021 ST_GAS −2.77 ≈ unchanged.
  - 2019 CT_PEAKER rises ≈ +0.5 pp, from +0.79.
  - **Expected determination: NOT-YET.** One failing row (2019 COAL_BIT, deeper), possibly two (2022 COAL_PRB).
- **E5 (unserved).** 0 MWh in every year. No capacity changes.
- **E6.** C2, C6 and C8 PASS. C3 is UNSCORABLE. D-2 and D-4 are unchanged in kind, because no floor is added.

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff** all four of these hold:

1. All seven legs solve cleanly with the §5 hard stops met.
2. **The mechanism fires exactly as censused.**
   - In every leg, every unit's hourly `cap_mw` is byte-identical to soco-71's leg.
   - In 2019–2022, every gas tranche's median solved-minus-keeper `mc` on its `_econlo` / `_econhi` / `_peak`
     tranches equals §3's Δmc to ±$0.01.
   - E1's 2023–2025 identity holds.
3. No year's unserved energy increases.
4. C6 and C8 PASS, and `legitimacy_diagnostics` records no new D-4 FAIL.

**This holds whatever C1 and C4 do**, and it is written knowing §4's greedy says the failing row deepens. The stale
0.64 was pricing 2019–2021 gas $3–4/MWh above the plants' own filed cost, and that error was propping up 2019 coal
(rule 14: "the estimate was silently compensating"). **If a new row FAILs, it is reported at full magnitude as the
next root-cause lead, never as a reason to keep the fall-through.**

The owner's standing ruling covers promotion ("If structural integrity improves but gates regress that may still be a
keeper"). If it lands:

- Rule 35 enumerates the year union from every SOCO sidecar, then runs `audit_keepers` E1.
- Then `prune_iso_runs --iso SOCO --force-uncite` removes `2026-09-26-soco71-coal-hr-window`.

## 8. What this lane establishes about the failing row, and the named next object

**2019 COAL_BIT is not a gas-input error.** With fuel, heat rate and gas basis all measured, the three cyclers' own
cost sits $3–5/MWh above a correctly priced 2019 gas fleet in most of the hours they actually ran. What remains is on
the coal side's **commitment**, not its offer:

1. **The coal start markup on no-must-run cyclers** — `coal_warm_committed`'s predicate against a measured CEMS run
   horizon (median start-to-stop 283 / 88.5 / 143.5 h for Barry / Crist / Wansley 2019). Ceiling ≈ +0.4 TWh. It rides
   with the open SOCO-64/65 owner question on cost-based starts.
2. **A measured coal commitment/must-run basis** for the cyclers' 2019 campaign conduct (they ran through hours
   priced below their own cost). This is the same object class as `soco_gas_st_campaign_commitment` (K) on the gas
   boilers. It needs its own driver, window and forward story (rule 17) before it is a lever.

Neither is armed here.

## 9. Retrievability (rule 34(e))

- Each shard pushes its full bundle, `dispatch/<Y>_P1.parquet` included, to `claude/soco72-<Y>` through a
  `.gitignore` negation and a plain `git add`.
- The parent fetches each leg, verifies it, and composes `soco72_span`. It lands the composite (slim set + `hourly/`),
  the sidecar and the payload on `main` with this lane's PR.
- A leg not landed on `main` is costed as a re-solve, ~2 min of LP.
