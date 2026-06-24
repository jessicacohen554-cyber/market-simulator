# ERCOT West/Permian CT over-run: net-load-indexed Waha delivered gas + Laredo zone fix (2026-06)

**Status: run154 — net-load Waha delivered-gas step + Laredo zone correction.
Registered (`2026-06-23-run154-netload-gas-laredo`, determination NOT-YET).**
Branch `claude/ercot-run154-waha-netload-*`. Supersedes the run152/153 per-plant
Waha contract haircut.

## What changed vs the run153 framing

The run152/153 work priced West/Permian gas off the Waha *trading hub* and tried
a per-plant **contract haircut**. Two corrections:

1. **Delivered ≠ hub.** The model priced West/Panhandle gas off the Waha *trading
   hub* (wellhead pooling point, ~$0/MMBtu in 2024, negative 42% of trading days
   per EIA id=64445) while every other ERCOT zone uses EIA-923 *delivered*
   receipts. A power plant pays delivered (burner-tip) gas, not the wellhead pool.
2. **The per-plant contract haircut (run153) was backwards.** It scaled each
   unit's hub basis by its EIA-923 spot share, so 100%-**spot** units (Permian,
   Laredo) kept the *full* Waha collapse (→ ran baseload) while a 100%-**contract**
   unit in the same zone (Ector) lost the discount entirely (→ idled). "100% spot"
   is a contract *type*, not a *price* — spot gas is still delivered. Dropping the
   haircut and pricing all West units on one delivered basis fixes both.

## The mechanism: a two-regime net-load step

`fuel.apply_ercot_west_netload_gas_shape` makes the West/Panhandle Waha basis a
**two-regime function of system net-load** (`load − wind − solar`). The Waha hub
is bimodal — deeply negative on low-demand over-supply days (constrained Permian
takeaway), firm at high demand — and anti-correlated with net-load, the same
weather/demand driver the ST_GAS reliability drag keys off. A single annual
scalar prices a West **peaker** (burns only in high-net-load scarcity hours, when
Waha is firm) on the same ~$0 annual-mean gas as a West baseload **CC** (burns
all hours), collapsing the heat-rate spread and floating the peakers.

- **Split** by the **measured** Waha negative-price-day frequency
  (`data/raw/ercot_zonal_gas_hub.csv` `neg_day_freq`; 2024 EIA-authoritative
  **0.42** = 42% of trading days, id=64445; 2023 **0.03**, 2025 **0.11** from
  NGI/Reuters negative-day counts). The lowest `collapse_freq` of net-load hours
  → collapsed regime; the top `1 − collapse_freq` → firm.
- **Firm level** = `Henry Hub + ercot_west_gas_firm_basis` (the cited firm Waha
  delivered basis, default −0.50). The **deep** value is forced by the measured
  annual-mean constraint `cf·deep + (1−cf)·firm = annual_basis`, then floored.
- **Burner-tip delivered floor** (`ercot_west_gas_delivered_floor`, $0.40). The
  hub goes to ~$0 (and negative), but a plant's *delivered* gas never does —
  intrastate transport + handling set a positive floor. **This is the fix for the
  cheap-hour magnet** (below): flooring the collapse regime at the generic ~$0.10
  gas floor (a hub-like number) made the lowest-demand hours an artificially cheap
  block that pulled low-HR West CTs in.

Every input is measured or cited; net-load = a load forecast + a VRE build, so the
shape regenerates forward and responds to changed conditions (admissibility
#10/#12). Env: `ERCOT_WEST_NETLOAD_GAS=1`, `ERCOT_WEST_GAS_DELIVERED_FLOOR=0.40`.

## The cheap-hour magnet, and why it's not transmission

The first cut (deep floored at the generic ~$0.10) made CT_PEAKER **aggregate**
land (2024 8.43 vs 8.21) but via a perverse mechanism: Permian/Ector/Laredo ran
**anti-correlated with load** (dispatch r vs net-load −0.45/−0.39/−0.32), serving
the $0.10 collapse hours baseload — the right *number* through a wrong *mechanism*
(CLAUDE.md #1). Raising the delivered floor to $1.40 flipped the correlations
positive but pushed CT below the band — the floor trades aggregate for shape.

**Transmission is not the lever.** West export uses only ~2 of its 10 GW WESTEX
TTC and is near-saturated in 0.4% of hours (0.6% during Permian's run hours), so
tightening the West→ERCOT limit does nothing — confirming the previously-built,
previously-rejected Far_West split (`docs/ercot-ct-waha-offer-floor-2026-06.md`:
"not transmission-closable"; the West CTs serve large local load). The residual
Permian/Ector over-run is cheap West gas + relatively-efficient peakers, which a
within-West gas shape cannot fully close at the physical delivered floor.

## Laredo (3439) zone misassignment — a clean fix

The CAMPD bin sheet assigned **Laredo to the West zone**, so the model priced its
gas on cheap Waha and ran it baseload (model >1.3 TWh vs real ~50 GWh). Laredo is
**Webb County / Rio Grande border — ERCOT South**, not West/Permian. Corrected
West→South in `custom-bin-assignments.csv`: it now pays measured South TX
delivered gas (basis +0.6) and idles correctly (**2024 model 56 vs real 52 GWh,
r +0.28**). A fleet zone-assignment correction (measured geography), not a fit.

## run154 3-yr keeper results (delivered floor $0.40, Laredo→South)

EIA-923 by class, model − actual:

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CT_PEAKER | 5.29 / 7.56 (−2.27) | 7.20 / 8.21 (−1.01) | 5.63 / 7.11 (−1.48) |
| CC_REGULAR | 142.1 / 143.7 (−1.1%) | 148.2 / 145.4 (+1.9%) | **148.3 / 142.1 (+4.3%)** |
| COAL_PRB | 46.4 / 45.1 (+3.0%) | 44.0 / 43.7 (+0.7%) | 48.4 / 47.6 (+1.5%) |

- **CT_PEAKER is in band all three years** (−2.27 / −1.01 / −1.48 TWh; 2023 at the
  ±2.3 band edge) — fixing the run151 keeper's accepted CT over-run
  (+6.80 / +7.05 TWh in 2024/25, which run151 wrongly attributed to intra-Permian
  transmission). [7c] operating-shape gate **passes** for CT_PEAKER 2023/2024.
- LMP MAE **27.8 / 15.3 / 11.7** (run153 27.8 / 15.2 / 11.3 — flat). Slack
  negligible (0.003–0.007 TWh): freed energy conserves in the gas family, not
  unserved.
- Per-unit in 2025 (expensive West gas $2.74), Permian/Ector land near real CF
  (398/450 vs 456/642 GWh); the residual magnet is the 2024 cheap-gas year only
  (r −0.44/−0.38).

## Residuals (documented, not fit)

1. **CC_REGULAR 2025 +6.15 TWh (out of band).** The freed CT_PEAKER energy lands
   in CC_REGULAR; this over-absorption (chiefly Hidalgo, Colorado Bend) was
   *masked* in run153/run151 by the CT over-run and is now exposed. A MODEL MISS —
   the next root-cause — **not** closed by reverting the structural CT fix
   (CLAUDE.md #1/#11). This is why run154's determination is NOT-YET while run151
   (with its accepted CT caveat) is CALIBRATED-WITH-CAVEATS; promoting run154 to
   keeper waits on closing this.
2. **Permian (3494) / Ector (58471) 2024 magnet.** Still over-run with a residual
   cheap-hour magnet in the deep-gas year (r −0.44/−0.38); near-correct in 2025.
   The remainder a within-West gas shape cannot close — West CTs serve large local
   load, not transmission-closable.
3. **Laredo HR (9.16).** Low for a GT peaker (EIA-860 per-unit data item); now
   immaterial since the zone fix idles it correctly.

## Reproduce

```bash
ERCOT_ZONAL_GAS=1 ERCOT_WEST_NETLOAD_GAS=1 ERCOT_WEST_GAS_DELIVERED_FLOOR=0.40 \
  ERCOT_OIL_PRIMARY=1 KEEPER_RTORDPA=1 KEEPER_PERSIST_P2=1 KEEPER_STGAS_DRAG=1 \
  KEEPER_PRB_PARAMS='{"coal_prb_passthrough_floor":0.78,"coal_prb_follower_floor":0.78}' \
  python scripts/probes/_keeper_2023as_run.py ercot_run154_netload_gas 2025 2023 \
  '{"ST_GAS":{"committed":0.0}}'
```

Do **not** dial the firm basis, collapse frequency, or delivered floor to land
CT_PEAKER on target (CLAUDE.md #11/#12) — all three are measured/cited, and the
residuals close at the unit level (CC over-absorption, per-unit HR), not by a
gas-side fit.
