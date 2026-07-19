# CAISO floor fix — three parallel session prompts

Hand-off from the CAISO structural audit (`AUDIT-caiso-structural.md`). The audit
re-established a clean baseline, applied the 2025-hydro repin, built a (default-off)
interchange-shaping tool, and **corrected the floor diagnosis**: CAISO's over-priced
midday floor is a *longness / marginal-offer* phenomenon (RA must-offer commitment +
negative renewable bids), **not** an interchange, capacity, or solar-shape artifact.
The model is never *long* midday, so its marginal is always a priced import/gas
(≥ ~$28–40); real CAISO is long and prices its surplus at ~$0/negative.

These three workstreams can run **in parallel on separate branches**. A and B are
coupled (B only bites once A makes the model long) but can be developed independently
and combined; C is fully independent.

## Shared context (paste into each session)

- **Repo:** `jessicacohen554-cyber/market-simulator`. ENV:
  `uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"`.
- **Baseline (re-run first; scratch bundles are gitignored and don't survive a fresh
  container, ~27 min / single year ~9 min):**
  `python scripts/run_calibration_full.py --iso CAISO --year 2023 2024 2025
  --commitment --priced-interchange --out-dir results/calibration/caiso_tune0_base`.
  Iterate on **2024** (it has the actual LMP reference).
- **References:** EIA-930 `data/eia_hourly/CISO hourly.parquet` (cols incl. `Demand`,
  `Total interchange` [+=export], `NG: NG`/`NG: SUN`/`NG: WND`/`NG: WAT`/`NG: NUC`);
  actual LMP `inputs/calibration/actual_lmp.json["CAISO"]` (2024/25 only; `rt_mon`,
  `da_pct`); EIA-923 mix reference `inputs/calibration/calibration_reference.json`
  (`isos.CAISO.<year>.generation_twh`); per-class model output in each bundle's
  `dispatch/<year>_P2.parquet` (cols `klass,fuel,zone,plant_code,hour,mw,lmp`).
- **Benchmark caveat (do not re-derive):** EIA-930 CISO reports no geothermal/biomass,
  so its `NG: NG` (85.4 in 2024) absorbs ~11 TWh of geo+bio. **Score CAISO gas against
  EIA-923 (67.7 in 2024), not EIA-930.** Model 2024 gas already matches EIA-923 to
  <0.5 %; do not raise gas to chase the EIA-930 number.
- **2025 hydro:** run CAISO 2025 with `--hydro-backfill-year 2024 --hydro-eia930-monthly`
  (the early-release 923 vintage under-counts hydro 12.3 vs 21.3 TWh; the loader fix
  that enables the repin is already on main).
- **Interchange shaping (already built, default-off):** `--interchange-shaping`
  (`transmission.inject_interchange_shape`) shapes the priced node by the measured
  EIA-930 diurnal interchange envelope so it can export midday. On its own it raises
  the floor (it caps cheap imports → substitutes gas); it only helps **once the model
  is long** (Session A). Use it on the *export* side together with A.
- **Hard constraint:** do **NOT** touch `offer_curve_by_group` / band multipliers —
  that is a separate phase. These three workstreams are commitment / renewable-offer /
  reserve **market-design** mechanisms, not offer-curve tuning.
- **Commit discipline:** new code/constants/flag + a test + a 2024 (or 3-yr) before/after
  on mix (vs EIA-923) + monthly LMP (vs `rt_mon`); commit each fix separately; scratch
  bundles gitignored; commit messages end with the session-URL line; develop on the
  named branch; no PR unless asked.

---

## Session A — RA must-offer minimum-commitment floor (THE floor fix)

**Branch:** `claude/caiso-ra-mustoffer-commitment`

**Goal.** Make the model *long* midday so its surplus exports/curtails at a low price,
reproducing CAISO's collapsed spring-midday LMP (real Apr–May RT ~$11–14, p5 −$10,
min −$40; model today min $28, never ≤ $0). The lever is the CAISO **Resource Adequacy
must-offer obligation**: RA-obligated gas stays online at min-load through midday (it
can't economically cycle off for the evening ramp), so it over-generates midday and the
ISO exports/curtails the surplus at ~$0. The model instead *economically decommits* gas
to ~2 GW midday and imports the rest, staying balanced — so its marginal is always a
≥$28 import/gas.

**Diagnosis to confirm first.** Real CAISO runs ~6–7.6 GW gas at spring midday (EIA-930
`NG: NG`) while *exporting* ~+2 GW — gas is committed for non-energy (RA/ramp) reasons
and is infra-marginal; the marginal is the export/curtailment. The model runs ~2 GW gas
midday and imports 2.3 GW. Quantify the model-vs-EIA-930 midday `NG: NG` gap on the
baseline bundle.

**Mechanism (defensible, measured — no magic numbers).** Impose a midday minimum-
commitment floor on the gas fleet equal to the **measured EIA-930 `NG: NG` hourly
profile** (or a defensible fraction of it / of committed RA capacity), via the
hour-varying `FleetArrays.min_gen` lower bound (the same mechanism the CHP steam floor
and the export-sink shaping use). Keeping the RA gas online forces midday surplus; pair
with `--interchange-shaping` (export side) + the $0 export/curtailment sink so the
surplus prices at ~$0. Investigate `model/commitment.py` (the P2 screen that currently
lets gas decommit) and `data/fleet.py` min_gen assembly; the cleanest hook is a
CAISO midday gas `min_gen` floor injected in `scripts/run_calibration.py` after
`generators_to_fleet_arrays` (mirror `inject_offshore_wind_availability` /
`inject_interchange_shape`).

**Watch.** Forcing commitment can inflate gas TWh — the surplus must *export/curtail*,
not pad the mix. Validate gas vs **EIA-923** (not EIA-930). Expected: gas roughly flat
or modestly up, export hours rise from 0 %, spring-midday LMP drops toward actual.
Gate behind a flag (default off, byte-identical when off).

**Deliverable.** Flag + min_gen floor + test; 2024 before/after on monthly LMP (esp.
spring p5/min and `rt_mon`) and mix vs EIA-923; confirm on 3 years.

---

## Session B — Negative / curtailable renewable offers (the negative tail)

**Branch:** `claude/caiso-negative-renewable-offers`

**Goal.** Let solar/wind set a **≤ $0** marginal price in oversupply, reproducing real
CAISO negative midday prices (2024 `da_pct`: p5 −$10, p1 −$24, min −$41). California
renewables bid below $0 to keep producing for RPS/REC/PTC value; the model's solar/wind
are must-take at $0 and are never marginal (always absorbed), so the model floors at $0
at best and in practice never even reaches it.

**Mechanism (defensible single constant).** Add a *curtailable* renewable tier with a
**negative offer** equal to the renewable's effective keep-running value — the CA REC /
PTC value (~$15–30/MWh; cite RPS REC prices / the federal PTC). So in oversupply the
marginal unit is curtailed solar/wind at, e.g., −$20, and the LMP goes negative. Only
one defensible constant (the REC value), not a per-hour shape.

**Investigate first.** How solar/wind enter the LP today — are they netted from demand
or must-take availability-capped units at $0? (See `data/renewables.py`,
`scripts/run_calibration.py` solar/wind handling, and the `_must_run`/demand-netting
path.) The negative tier needs a curtailable slice that *is* in the LP with a negative
VOM. The existing $0 export/curtailment sink already floors surplus at $0; this pushes
below it.

**Dependency.** Negative offers only bite when the model is *long* (Session A). Develop
independently but **test in a forced-long harness** (e.g., a high-solar low-load hour or
with Session A's floor enabled) to prove the price goes negative; the full 3-yr payoff
needs A merged.

**Deliverable.** Flag + negative curtailable tier + REC-value constant + test; 2024
before/after showing negative-price hours appear and spring p5/min move toward actual.

---

## Session C — AS reserve-requirement formula (evening tail; independent)

**Branch:** `claude/caiso-as-reserve-formula`

**Goal.** A defensible, formula-based CAISO operating-reserve requirement withheld from
thermal energy headroom, lifting tight-hour / **evening-tail** prices (the model's 2024
max LMP is only $83.7). This is a ready, **default-off** scaffold until OASIS cleared-AS
data can be pulled (outbound network is blocked in the remote env, so OASIS is currently
unreachable; when available, fetch `AS_RESULTS`/`AS_REQ` and replace the formula with
measured MW).

**Formula (published standard, no fitted constants).** Upward reserve to withhold:
`R(t) = max(MSSC, 0.067 × load(t)) + 0.01 × load(t)` where
- contingency = WECC MORC: greater of the most-severe single contingency
  (`MSSC` ≈ largest single unit nameplate in the fleet, ~1,150 MW for a Diablo unit)
  or 5 % of hydro-served + 7 % of thermal-served load (≈ 6.7 % of load for CA's mix);
- regulation up ≈ 1 % of load (sub-hourly net-load variability; CAISO Reg ≈ 300–500 MW
  on 25–40 GW load). Reg-Down is downward — excluded (withholds no upward offer).

**Mechanism.** Add a CAISO branch to the existing withholding block in
`data/fleet.py` (~the `as_reserve_withholding` / `_withdraw_top_of_merit` block,
currently ERCOT-only): compute `R(t)` from `load_shape` (already passed to
`generators_to_fleet_arrays`) + the fleet's max unit nameplate, and withdraw it from the
gas top-of-merit headroom. New flag (e.g. `as_reserve_formula`, default off).

**Caveat (state it in the doc).** This lifts the **tail**, not the midday floor — it must
**not** be used to paper over the floor (Sessions A/B). Enable it only *after* the floor
is fixed.

**Deliverable.** `caiso_operating_reserve_mw(...)` + flag + test (formula correctness +
that it withholds and lifts tight-hour prices); 2024 before/after on monthly LMP showing
the evening/tight-hour lift with the midday floor unchanged.
