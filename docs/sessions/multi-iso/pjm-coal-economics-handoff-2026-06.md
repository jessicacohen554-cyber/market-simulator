# PJM coal economics & plant-operations modeling — deep-dive handoff (2026-06)

## Mission

The PJM coal numbers are still wrong, and every coal lever we've tried trades
one error for another. **Stop tuning passthrough knobs and go back to first
principles:** characterize how PJM coal plants *actually* operate and what
*actually* drives their dispatch economics, compare that to how the model
represents them, and rebuild the representation to match real-plant operation
using standard production-cost / unit-commitment best practices. Bituminous is
the focus (it's ~90% of PJM coal energy); a parallel CC_REGULAR thread runs
alongside (same "modeled too baseload" symptom). **Do not fit to the EIA-923
total** (CLAUDE.md #1/#11) — get the operating *mechanism* right and let the
level follow.

## Where we are (this session's results, all on the dashboard)

- **Keeper:** `pjm_42_campdfix` ("pjm 42 campd-nan-fix"). coal-tot resid
  **+9.4 / +1.6 / +9.4%** (2023/24/25), but **over-exports** (net-export
  +27/+15/+82%) and **under-prices** (LMP +3.0/−7.8/−14.5%). Coal is held at
  volume by a **forced must-run floor** + a sub-cost gas-keyed passthrough
  discount; that floods cheap coal into a 3×-too-large export and suppresses LMP.
- **`pjm_43` (coalbit-marginal):** made bituminous fully dispatchable
  (`coal_bit_dispatchable=True`, must-run floor zeroed) **and** bid full
  delivered cost (`coal_bit_passthrough_floor=1.0`). Coal **collapses**
  −36/−46/−20%, gas balloons +12/+14/+9%, per-plant hourly shape worsens
  (fleet r 0.77→0.61, cf_emd 0.088→0.229). LMP lands near-perfect in 2024
  (+0.7%) but only because cheap coal leaves and pricey peakers set the margin.
- **`pjm_44` (coalbit-sigmoid-dispatch):** dispatchable **but keeps the
  gas-keyed sigmoid** (floor 0.76→ceil 1.32). Best of the three on volume +
  export: coal −21/−28/−13%, **net-export near-actual** (2025 17.9 vs 18.0),
  band_overlap back to keeper level (0.642). Still coal-under / gas-over (the
  relabel), LMP 28.7 vs 29.5 in 2024.

**The crux (confirmed empirically):** there is an **irreducible volume↔price
tension** in the current structure. Hold coal at its observed volume → bit must
bid low (deep discount / forced must-run) → suppresses LMP and over-exports.
Get LMP right → bit bids full cost → coal collapses ~50% and relabels to gas.
You cannot resolve this *with the coal offer alone* — it is downstream of PJM's
**price formation** (gas-marginal / missing afternoon scarcity; see
`pjm-coal-overrun-decomp-2026-06.md`, `pjm-reserve-ordc.md`). The coal
representation and the price-formation lever must be designed **together**.

Probe docs: `docs/multi-iso/pjm-coalbit-marginal-probe-2026-06.md`,
`pjm-coalbit-marginal-handoff-2026-06.md`, `pjm-coal-overrun-decomp-2026-06.md`.

## Thread A — How PJM coal plants ACTUALLY operate (from data, first)

Build a per-plant operational fingerprint from **EPA CAMPD/CEMS hourly** (the
ground truth; benchmark is now correct after the plant_hourly_net NaN fix) for
each PJM bituminous plant — Cardinal (2828), Kyger Creek (2876), Gavin (8102),
Amos (3935), Mountaineer, Conemaugh (6264), Keystone (3954), Homer City
(retiring), etc. For each unit/plant and year (2023-25), quantify:

1. **Minimum sustained load** — the real Pmin as a % of capacity (P5 of online
   hours), and whether the plant ever two-shifts to zero vs holds a floor.
2. **Cycling behaviour** — # of starts/stops, run-length distribution, how often
   it drops below 50% / 40% of capacity, diurnal swing (overnight backdown),
   weekend vs weekday. Is it *baseload* (flat), *load-following* (ramps with net
   load), or *two-shifting* (off overnight)?
3. **Capacity-factor shape** — annual CF, the CF duration curve, seasonal
   pattern (winter/summer peaks vs shoulder backdown), and the price-conditional
   CF (CF in low- vs high-LMP hours, using PJM nodal/zonal LMP — does the plant
   *actually* back down when prices are low?).
4. **Ramp rates** — observed MW/hr ramp envelope.
5. **Heat rate vs load** — part-load heat-rate degradation (CEMS heat-input ÷
   gross MW across the load range): the incremental HR at Pmin is materially
   higher than full-load HR; this shapes the offer curve and is currently
   approximated by tranche HR multipliers.

The key empirical question: **does PJM bituminous behave as baseload, or as a
gas-price-following swing fuel, in the data?** This session's evidence says the
big units (Gavin/Cardinal/Kyger) ran *near-baseload* (P5-all-hours floor
37-60%), i.e. they did NOT back down to the degree a pure full-cost merit-order
would predict — which is why forcing full-cost dispatchability collapses them.
Confirm/refute per plant, and identify which plants cycle (smaller/older units)
vs hold baseload (large supercritical units).

## Thread B — What actually drives the economics (the offer, for real)

A PJM coal plant's day-ahead offer is **cost-based or price-based** under
PJM Manual 15 (Cost Development Guidelines) and the Fuel Cost Policy. Map our
representation to the real offer components:

1. **Delivered fuel cost** — EIA-923 fuel-receipt delivered $/MMBtu per plant
   (`derive_coal_supply.py`; ~$3.0/MMBtu bituminous 2024). Spot vs contract:
   how much is **take-or-pay tonnage** (sunk, must-burn) vs **spot** (avoidable)?
   This is the heart of the marginal-vs-baseload question. Investigate whether
   Appalachian/ILB bituminous into PJM is genuinely spot (thesis) or substantially
   contracted (data suggests the latter — plants ran through cheap gas).
2. **Incremental (part-load) heat rate** → the energy offer curve.
3. **VOM, consumables, reagents** (SCR/SNCR urea/ammonia, FGD limestone), **CO2
   (none in PJM RGGI? — VA left RGGI; check per-state)**, **NOx/SO2** (CSAPR
   allowance prices), **start-up cost** (cold/warm/hot, fuel + auxiliary +
   wear), **min-run / min-down**.
4. **Capacity-market must-offer** — Capacity Performance resources have a
   **must-offer obligation** into the energy market; a committed coal unit can be
   *obligated to run / offer* even when out-of-merit, and faces non-performance
   penalties. This is a real reason coal stays online through cheap gas that a
   pure energy-merit model misses entirely.
5. **Opportunity / commitment hysteresis** — large coal units avoid expensive
   cold starts, so they self-commit and run min-load through low-price nights
   rather than two-shift (start-up cost > overnight losses). This is *unit
   commitment*, and is the mechanism the must-run floor is crudely proxying.

The honest reframe: the keeper's "must-run floor + discount" is a **reduced-form
unit-commitment + take-or-pay + must-offer proxy**, not an ERCOT-PRB mis-port.
The question is whether to keep it as a calibrated reduced form or replace it
with explicit UC economics (Thread D).

## Thread C — How the model represents coal today (audit)

- **Per-plant CAMPD binning** → `bins_to_fleet` (`data/fleet.py:~5051`). Each
  coal plant = must-run / committed / econ / peak tranches forming a rising
  offer curve. `docs/binning-methodology.md`.
- **Must-run floor** = `thermal_tranches_PJM.csv` `mustrun_pct` (P5 of all-hours
  CF, capped 0.60), from `scripts/data/derive_thermal_tranches.py`. Cardinal 60 /
  Kyger 48 / Gavin 48 / Amos 37. The `_mustrun` tranche is **forced on** and
  bids **VOM+carbon+NOx only** (fuel sunk = take-or-pay assumption).
- **Gas-keyed passthrough sigmoid** (above-must-run fuel cost) —
  `COAL_SIGMOID_DEFAULTS[("PJM","bituminous")]` floor 0.76 / ceil 1.32 /
  gas_mid 3.40 / gas_slope 2.5 (`config/scenarios.py:1577`); applied
  `fuel.coal_passthrough_by_supply` → `fleet.apply_coal_tranches`. Discounts the
  bid when gas is cheap (hold merit), marks up when gas is dear (back down).
- **New lever (default OFF, diagnostic):** `coal_bit_dispatchable` zeros the bit
  must-run floor so it's fully marginal (`fleet.py` coal pct_mr block +
  `plant_tranche_bands`). Run scripts: `_pjm_coalbit_marginal_run.py` (flat
  full-cost), `_pjm_coalbit_sigmoid_run.py` (keeps sigmoid). Compare:
  `_pjm_coalbit_shape_cmp.py`.
- **Commitment:** P0 base-cost → P1 bid-cost (+amortized startup) → P2 optional
  decommit screen (`commitment_enabled`, default **off** for PJM). So coal min-
  run/min-down/startup is only partially modeled (P1 markup, no true UC).

Document precisely which real-offer component (Thread B) each knob stands in
for, and where the representation is physically ungrounded (e.g. floor 0.76 is a
calibrated discount, not a measured contract share).

## Thread D — Best-practice target & what to build

Standard production-cost models (PLEXOS, GE-MAPS/MAPS, PROMOD, Dayzer, SERVM)
represent a coal unit with: **Pmin/Pmax, incremental (piecewise) heat-rate
curve, min-up/min-down times, start-up cost & time (temperature-dependent), ramp
rate, no-load cost, must-run/must-offer flags, and fuel contract structure.**
Evaluate, against our LP-only (no MIP) constraint:

1. **Explicit-ish unit commitment for coal** — can the P2 decommit screen +
   min-run/min-down be turned on for PJM coal so large units self-commit and run
   min-load through cheap-gas nights (matching CAMPD) *endogenously*, replacing
   the hardcoded must-run floor? Tests whether UC economics reproduce the
   observed baseload behaviour without a forced floor.
2. **Take-or-pay as a real, forward-reproducible input** — if a share of
   bituminous fuel is contracted, model that share as sunk (bids low, holds
   merit) and the rest as avoidable spot (bids full cost, backs down). Source the
   contract share from data, not the residual (CLAUDE.md #11). This is the
   physically-honest version of the 0.76 discount.
3. **Capacity-market must-offer floor** — represent the CP must-offer / penalty
   as the reason committed coal stays offered through low prices (a structural
   input from the PJM capacity construct, forward-reproducible).
4. **Part-load heat-rate curve** — replace flat tranche HR multipliers with the
   CEMS-derived incremental HR(load) so the offer curve slope is physical.
5. **Pair with price formation** — only after PJM's afternoon clearing price is
   lifted toward actual (reserve/ORDC scarcity, `derive_dam_offer_hrmults`) can
   coal be made marginal without collapsing. Co-design.

## Thread E (parallel) — CC_REGULAR is modeled too baseload

Same symptom on gas CC: model runs CC_REGULAR at >80% of its own max in **74%**
of hours vs **68%** in CAMPD (2024 keeper, top-12 plants); committed_pct median
**56.5%** of capacity bidding cheap pins them flat (plants 55502/60356/59906/
60589 pinned >85% vs CAMPD ~75-82%). Investigate: is the CC committed-tranche
share / offer-curve too cheap-and-flat? Are start-up costs and min-run too low
so CC never two-shifts? Real CC cycles daily (especially 1×1 and older units).
Levers: `CC_REGULAR` offer-curve overrides (committed/econ/peak/peak shares in
`offer_curve_overrides`), `thermal_tranche_overrides` committed_pct, P2
commitment for CC. Characterize CC cycling from CAMPD the same way as Thread A.

## Data sources

- **EPA CAMPD/CEMS hourly** (`data/raw/campd-unit-level/`, `campd-facility-level/`)
  — operations ground truth; net-MWh via `run_calibration_full._campd_hourly_frame`.
- **EIA-923** fuel receipts (delivered $/MMBtu, rank) + monthly generation
  (`data/raw/...`, `derive_coal_supply.py`, `data/fuel.py`).
- **EIA-860** unit characteristics (Pmin, ramp, Technology, retirements).
- **PJM**: Manual 15 (Cost Development), Fuel Cost Policy, Capacity Performance
  rules, public DA LMP & fuel-mix (for price-conditional CF). EPA CSAPR
  allowance prices for NOx/SO2; check per-state CO2 (VA out of RGGI).

## Commands (PJM per-plant LP is GB-heavy → ONE year at a time, ~12 min/yr,
## ~11 GB peak; no pandas probes during a live solve)

```bash
.venv/bin/python scripts/probes/_pjm_score.py pjm_42_campdfix      # keeper score
.venv/bin/python scripts/probes/_pjm_score.py pjm_44               # this session's best probe
.venv/bin/python scripts/probes/_pjm_coal_decomp.py pjm_42_campdfix
# per-plant shape compare (bituminous): keeper vs a probe
.venv/bin/python scripts/probes/_pjm_coalbit_shape_cmp.py \
    results/calibration/pjm_42_repro_y2024 results/calibration/pjm_44_y2024 2024
# re-solve a year (clone a probe runner), then merge + register:
.venv/bin/python scripts/probes/_pjm_aswh_merge.py results/calibration/<b> \
    results/calibration/<b>_y202{3,4,5}
.venv/bin/python scripts/dashboard_add_run.py --label "pjm 45 <kw>" --bundle results/calibration/<b>
# (PJM next number is pjm 45; top-15-per-ISO retention)
```

## Key files

- `data/fleet.py`: `bins_to_fleet` (~5051), coal pct_mr / `coal_bit_dispatchable`
  block (~5071), `apply_coal_tranches` (~2077), `campd_tranche_fuel_frac`
  (~2048), `plant_tranche_bands` (~5614), `coal_supply_class` (~3450).
- `scripts/data/derive_thermal_tranches.py` (must-run/committed P5 derivation),
  `derive_coal_supply.py` (EIA-923 rank/cost).
- `config/scenarios.py`: `COAL_SIGMOID_DEFAULTS` (1529), `coal_bit_*` /
  `coal_bit_dispatchable` (~879).
- `scripts/run_calibration.py` `run_year` / `_calibration_config`;
  `run_calibration_full.py` `solve_and_persist` (flag threading via
  `bit_overrides` → `with_overrides`), `report_run`, `_plant_hourly_fit`.
- `model/commitment.py` (P0/P1/P2 UC screen), `model-methodology-spec.md`.

## Guardrails (CLAUDE.md)

- **#1/#11**: right structure first; ground every input (contract share, Pmin,
  HR curve) in physics/data that a forward year would reproduce — never a
  discount/floor tuned to the coal-MWh or LMP residual. A change that worsens the
  fit but tracks real operation stays in; fix the real root cause.
- **#12**: EIA-923 is the class-total gate; CAMPD is the hourly-shape diagnostic.
  Every completed run → dashboard (keeper or rejected probe).
- **#13**: solve & register ALL years (2023-2025) in one bundle; single-year =
  throwaway diagnostic only. Top-15-per-ISO, PJM labelled `pjm N <keyword>`.
- Memory: one PJM per-plant solve at a time.
```
