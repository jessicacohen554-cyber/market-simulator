# ERCOT CC_REGULAR North over-run: the zonal gas-basis probe (2026-06)

**Question (handoff).** The CC_REGULAR over-run (+2.7% / +10.3% / +8.8% in
2023/24/25, model vs CAMPD GWh) is not spread across the fleet: it concentrates
in North/Northeast (DFW-area) CC plants — Midlothian, Ennis, Wise, Wolf Hollow I,
Forney — while West/Permian (Odessa-Ector, Quail Run) and South_Central
(Guadalupe, Rio Nogales) CCs under-run. Is the North over-run a fixable
zonal/transfer/availability miss, or the documented sub-zonal (nodal) zonal-LP
limitation?

**Answer.** It is the documented sub-zonal/nodal limitation, and this probe
*proves the mechanism*. The first-order spatial driver is a **measured gas-basis
miss**: the model prices every ERCOT gas unit on one scalar basis (Henry Hub
− 0.50, the Waha discount applied fleet-wide), so DFW/North CCs burn the same
cheap gas as Permian CCs. Correcting it to the measured per-zone basis confirms
the cause but does **not** yield a keeper, because the zonal LP cannot model the
intra-Permian transmission the correction needs. The CC_REGULAR over-run stays an
ACCEPTED MEASURED-INPUT LIMITATION, now with a spatial decomposition as evidence.

## Diagnosis (no solve)

* **Hypothesis 1 (zonal demand share) — ruled out, measured.** The North model
  zone load share (~0.31) is the measured ERCOT NORTH+NCENT weather-zone load
  (`eia_loader.ercot_zonal_load_shares`), not an estimate. North genuinely
  carries ~31% of ERCOT load; the over-run is in CC *generation*, not demand.

* **Hypothesis 3 (per-zone gas basis) — the root cause.** EIA-923 Schedule-5
  quantity-weighted delivered gas (the same methodology cited for the
  PJM/NYISO/NEISO basis scalars) measures, vs Henry Hub:

  | model zone | 2023 | 2024 | 2025 | coverage |
  |---|---|---|---|---|
  | North | +0.13 | +0.21 | +0.43 | 5 plants / 60M MMBtu |
  | South_Central | +0.56 | +0.45 | −0.12 | 12 plants / 172M MMBtu |
  | South | +1.23 | +0.63 | +0.59 | 3–5 plants / 9–33M MMBtu |
  | West (Waha) | −0.72 | −2.19 | −2.38 | published annual avg (NGI/EIA) − HH |

  North/SC/South gas is *above* Henry Hub; only West/Permian sits at the Waha
  discount (annual avg ~$0/MMBtu in 2024, negative 42% of trading days). The
  single −0.50 scalar over-cheapens North/DFW gas by ~$0.7/MMBtu and applies the
  Waha discount fleet-wide — over-running North CCs and under-running West CCs,
  exactly the observed spatial reallocation.

* Merchant North/DFW CCs (Midlothian 55091, Ennis 55223, Wise 55320, Wolf Hollow
  I 55139) report **no** Schedule-5 delivered cost, so per-plant F923 pricing
  (off by default) cannot reach them; the reconciled measured input is a
  *per-zone* hub basis, not a per-plant one.

## The probe: `ercot_zonal_gas_basis` (run146_zonalgas)

A new overlay `apply_ercot_zonal_gas_basis` (mirroring the blessed
`apply_nyiso_zonal_gas_basis`) shifts each ERCOT gas unit to its zone's measured
basis vs Henry Hub (`data/raw/ercot_zonal_gas_hub.csv`), **re-centred to a
gas-capacity-weighted mean of zero** so the calibrated fleet-aggregate gas level
is preserved and only the cross-zonal split moves. Solved on the run145 keeper
recipe (RTORDPA overlay), 3-year, vs a flag-off baseline reproduction.

### Result — the mechanism is real, but it relocates the residual

CC_REGULAR over/under-run by zone (model − CAMPD GWh), baseline → treatment:

| zone | 2024 base | 2024 treat |
|---|---|---|
| North | +10074 | **+6587** |
| West | −1525 | **+1180** |
| South_Central | −6 | −6373 |
| South | +2471 | −1529 |
| Houston | +742 | +3161 |

Class over/under-run (model − CAMPD TWh), 2024 base → treat:

| class | base | treat |
|---|---|---|
| CC_REGULAR | +13.24 | **+3.65** |
| CT_PEAKER | −1.94 | **+8.87** |
| COAL | −3.71 | −0.86 |

* The North CC over-run shrinks and the West CC under-run is fixed — the gas
  basis is the correct first-order lever for the spatial split.
* But the **CT_PEAKER over-run is entirely West/Permian** (2024 West CT
  −667 → +9861 GWh): on ~$0 Waha gas, West CT peakers out-compete out-of-zone
  CCs and run baseload. The 7-zone LP cannot represent the intra-Permian
  (<200 kV) transmission that, in reality, traps that cheap West generation and
  keeps the peakers as peakers.
* **LMP is unchanged** (MAE 2023 27.3→27.2, 2024 14.9→14.9, 2025 11.3→11.5;
  duration curve and tail unchanged) — the mean-zero anchor preserved the level.

So the measured zonal gas basis trades the CC_REGULAR over-run for a *larger,
less defensible* West CT-peaker over-run, with no LMP gain — it relocates the
same unmodelable nodal-congestion residual from one gas class to another. This
fails the within-gas-ledger gate (CC/CT shape must hold).

## Disposition

* **run146_zonalgas — REJECTED PROBE.** Confirms the diagnosis; not a keeper.
* **`ercot_zonal_gas_basis` stays in the code, default-off, as a labelled
  diagnostic** (rule #11: a measured input misaligned to our zonal representation
  — using the literal Waha basis is *less* reflective of reality because the
  zonal LP lacks the sub-zonal transmission that traps its consequence). Never
  enabled in a keeper.
* **The CC_REGULAR North over-run remains an ACCEPTED MEASURED-INPUT LIMITATION**
  — now the zonal-LP shadow of trapped cheap-Permian gas. A measured zonal gas
  basis confirms the mechanism but cannot resolve it without nodal transmission;
  it only moves the residual to the same <200 kV West pocket (94% of SCED binding
  rent is on such local pockets, per the keeper attestation). No per-plant
  haircut was added (that would be a fit to the residual, barred).

## Reproduce

```bash
# baseline (flag off) and treatment (flag on), 3-year, sequential (OOM if parallel)
KEEPER_RTORDPA=1 python scripts/probes/_keeper_2023as_run.py run145_repro_baseline 2025 2023 '{"ST_GAS":{"committed":0.0}}'
ERCOT_ZONAL_GAS=1 KEEPER_RTORDPA=1 python scripts/probes/_keeper_2023as_run.py run146_zonalgas 2025 2023 '{"ST_GAS":{"committed":0.0}}'
```
