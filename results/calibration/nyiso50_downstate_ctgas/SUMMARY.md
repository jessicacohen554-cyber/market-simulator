# nyiso 50 downstate ctgas — PROBE (real partial fix; keeper stays nyiso-41 STALE-VS-HEAD)

The NYISO peaker-pricing structural fix the a4c219e HEAD re-gate required before
NYISO can be re-gated (`docs/handoffs/co2-keeper-regate-2026-07-05.md`, issue
#1344). Both named candidates evaluated; candidate (a) implemented.

> Registered as a PROBE (rule #15). The full findings also live in this run's
> registry sidecar (`frontend/data/backcast/registry/2026-07-05-nyiso-50-downstate-ctgas.json`)
> and the co2-keeper-regate handoff. Kept out of the shared append-only
> `docs/calibration-log.md` to stay parallel-session-safe (calibration-report
> skill guidance) and within the push size limit.

## Candidate (a) — LI/NYC downstate delivered-fuel (city-gate) basis — IMPLEMENTED (default off)

New rule-13 measured input `nyiso_downstate_ct_gas_basis`
(`market_sim.data.fuel.apply_nyiso_downstate_ct_gas_basis`): each NYC (zone J) /
Long Island (zone K) `CT_PEAKER` (LM6000) unit's delivered gas is lifted from
the Transco Z6 NY pipeline hub the model prices it at to its LDC **city-gate**
delivered index by the MEASURED monthly premium — EIA NG `N3050NY3` (NY
city-gate) minus the measured Transco Z6 NY hub, floored 0
(`scripts/fetch_nyiso_downstate_gas_basis.py` →
`data/raw/gas-prices/nyiso_downstate_ct_gas_basis_monthly.csv`; positive
year-round, mean ~$2.7/MMBtu, summer-peaked to ~$5). Physical driver: non-firm
downstate peakers (few hundred hrs/yr, no firm interstate capacity) buy
interruptible gas off the Con Ed / National Grid / KeySpan city gate, so an
HR~9-10 LM6000 should not undercut the HR~11-12 downstate steam fleet on flat hub
gas — the de-leaked (1.0×) offer's CT over-run (B-NYI-1). Forward-reproducible
(both series publish monthly and respond to a tight winter/summer).

## Gate (one-delta vs `nyiso 48 head regate`, all years 2023-2025)

- **CT_PEAKER** 4.46/4.51/4.73 (nyiso-48) → **3.26/4.20/4.03 TWh** (actual
  2.26/2.13/2.84). **C1 CT_PEAKER FAIL → PASS** 2023 (+1.00) / 2024 (+2.06 TWh,
  inside the ±2.94 band). C1 free-class stays **9/10** (remaining free fail =
  2024 ST_GAS −3.39, the pre-existing steam / gas-total under-run, unchanged by
  the premium). C2 / C4 / C5a PASS.
- **NOT a keeper (rule #3):** C7 (D-1) 2024 CT_PEAKER stays **FAIL** (off-peak
  cv_ratio 0.454 → 0.418 < 0.5); C3a stays **−17/−18/−15%**.

## Root cause of the residual (the two structures the de-leaked wall proxied)

1. **Fuel-delivery physics** — CLOSED by candidate (a).
2. The Long Island CT over-run's residual is **floor-forced**: the LI local
   self-supply floor + CT temperature reliability floor force flat in-pocket
   LM6000 baseload (LI CT ~2.3-3.1 TWh, nearly flat Jan-Dec), which a fuel-cost
   premium cannot reduce — so C7 (diurnal flatness) and the LI volume barely
   move. The C3a under-price is the **missing peaker competitive-scarcity /
   #1344 reserve-RCPF price structure**: in most hours the marginal unit is
   still cheap CC, so dearer downstate peaker gas lifts LI zonal price but not
   the system mean.

## Candidate (b) — reserve/RCPF scarcity price formation — EVALUATED

The published-tariff NYISO RCPF locational families (NYCA ⊃ East ⊃ SENY ⊃ NYC,
`config.reserve_config.NYISO_RCPF_*`, cited FERC ER21-502 / RS4) are already in
the LP under `energy_reserve_coopt` (on in the keeper) and form prices in the LP
duals when they bind. They remain **non-binding with grounded static
requirements** (reserve_price >0 in only ~1000-2500 zone-hrs vs measured
~3000-4000; consistent with the exhaustive nyiso-29/30/31 refutation), and the
dearer downstate gas does not make them bind. Manufacturing the tail by
inflating the static requirement / steepening the curve is forbidden (rule #12).
The one remaining grounded lever is a measured, condition-varying downstate
reserve requirement from the NYISO AS postings (`process_nyiso_as.py`) — a new
data intake, out of scope here.

## Disposition

Keeper stays `nyiso-41` **STALE-VS-HEAD**. The delivered-fuel basis is a
validated, grounded, forward-reproducible structural input kept **default-off** —
the correct fix for the fuel-delivery half of what the de-leaked wall proxied.
NYISO **calibration-complete item 1 stays BLOCKED**; the remaining work is the
CT/ST reliability-floor **re-derivation** (rule #23, now that the basis has
landed — the floors over-force LI in-pocket volume and flatten the diurnal
shape) and the #1344 peaker-scarcity / measured condition-varying reserve
requirement. Did NOT re-arm the de-leaked scalars (rule #26).

## Reproduce

```
python scripts/replay_keeper.py results/calibration/nyiso41_hubprices \
    --out-dir results/calibration/nyiso50_downstate_ctgas \
    --set nyiso_downstate_ct_gas_basis=true --note "downstate CT city-gate gas premium"
```
(or `scripts/solve_nyiso_downstate_ctgas.py`, which passes the flag as a
first-class `solve_and_persist` kwarg). Requires
`data/raw/gas-prices/nyiso_downstate_ct_gas_basis_monthly.csv`
(`scripts/fetch_nyiso_downstate_gas_basis.py`).
