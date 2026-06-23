# ERCOT CT_PEAKER over-run: the Waha delivered-gas floor & contract haircut (2026-06)

**Problem.** With `ERCOT_ZONAL_GAS=1` (the run151 coal keeper recipe) the
West/Permian gas units see the raw Waha **hub** basis (2024 −2.19 vs Henry Hub),
which floors near $0/MMBtu. At HR ~10–13 they offer ~$0–5/MWh and run **baseload**,
the CT_PEAKER over-run: 2024 model 15.01 TWh vs EIA-923 8.21 (**+82.8% / +6.80
TWh**). The Far_West zone split was already built and **rejected** — the Permian
CTs serve large *local* load, so the over-run is not transmission-closable
(`docs/ercot-far-west-zone-split-2026-06.md`). The cause is the cheap-Waha-gas CT
**economics**, attacked here at the offer/fuel level.

## Per-unit anatomy of the over-run (2024)

| unit | type (EIA-860) | yr | real CF | model CF | model−EIA GWh |
|---|---|---|---|---|---|
| Morgan Creek 3492 | GT, **Petroleum Liquids/DFO** | 1988 | 1.6% | ~92% | +3584 |
| Laredo 3439 | GT, NG | 2008 | 1.8% | ~94% | +1899 |
| Permian Basin 3494 | GT, NG | 1988 | 8.8% | ~86% | +2534 |
| Ector County 58471 | GT, NG | 2015 | 13.5% | ~88% | +1985 |
| Odessa-Ector 55215 | CC, NG | 2001 | 69% | ~75% | +317 (fine) |
| Quail Run 56349 | CC, NG | 2007 | 48% | ~85% | +863 |

The over-run is the **four GT peakers** (real CF 1.6–13.5%) the model runs
baseload on ~$0 gas. The two CCs are genuine baseload and roughly match.
**Morgan Creek (3492)** is an EIA-860 *Petroleum-Liquids / DFO* peaker the model
prices on Waha gas — a per-unit fuel issue tracked as "direction 3".

## The fix, in two layers

### Layer 1 — delivered-gas floor (`ercot_gas_delivered_floor_basis`, merged PR #786)

The `−2.19` in `data/raw/ercot_zonal_gas_hub.csv` is a Waha **hub** (pooling-point)
basis — the takeaway-constrained wellhead price producers offload associated gas
at, negative ~42% of days in 2024. A power plant buys **delivered** gas at the
burner tip (intrastate transport + fuel retention + minimum commodity on top), so
its delivered discount has a structural floor regardless of how negative the hub
goes. The measured TX delivered-to-electric-power series (EIA N3045TX3, $2.11/MMBtu
in 2024) confirms no TX plant paid near $0 delivered.

`ercot_gas_delivered_floor_basis` floors each zone's per-zone delivered discount
at the cited measured Waha **delivered** basis (`GAS_BASIS_DIFFERENTIAL["ERCOT"]`
= −0.50). West 2024 delivered: $0.35 → **$1.60** (HR10 offer $3.5 → $16/MWh).
Env: `ERCOT_GAS_FLOOR=1` (`ERCOT_GAS_FLOOR_BASIS=<f>` overrides).

**Result (2024 probe, matched recipe), model − EIA-923 TWh:**

| class | baseline (floor off) | floor −0.50 | EIA | Δ |
|---|---|---|---|---|
| CT_PEAKER | 15.01 (+82.8%) | **5.94 (−27.6%)** | 8.21 | −9.07 |
| CC_REGULAR | 143.58 (−1.3%) | **148.74 (+2.3%)** | 145.41 | +5.16 |
| ST_GAS | 15.74 (−13.1%) | 16.55 (−8.6%) | 18.10 | +0.81 |
| COAL_PRB | 43.09 (−1.3%) | 45.02 (+3.1%) | 43.68 | +1.93 |
| TOTAL thermal | 301.02 | 300.04 (+0.6%) | 298.24 | −0.98 |

The freed ~9 TWh lands predominantly on **CC_REGULAR (+5.16)** plus ST_GAS/imports
— gas-family conserved, nothing into slack. LMP MAE 2024 15.3 → 15.5 (≈flat). The
mechanism is structurally sound, but the cited −0.50 **overshoots** (CT to −27.6%).
A single cited scalar is still a chosen number, so it is not the final depth.

### Layer 2 — measured contract haircut (`ercot_gas_contract_haircut`, this branch)

The depth re-grounded on *measured* data instead of a chosen scalar: only the
**spot-purchased** fraction of a zone's gas sees the Waha hub collapse; the
**firm-contracted** fraction is priced off a term index and is insulated. So the
West delivered discount should be `spot_share × hub_basis` — a measured fraction.

- `scripts/derive_gas_takeorpay.py` — per-plant gas contract/spot share from
  EIA-923 Schedule-5 **Purchase Type** (C/NC/T = firm, S = spot), mirroring the
  coal take-or-pay deriver → `data/raw/_processed-legacy/gas_takeorpay_ERCOT.csv`.
- `fuel.ercot_gas_spot_share_by_zone` — aggregate per-plant share to model zones
  (MMBtu-weighted; zone map from the CAMPD bin sheet's `ERCOT_Zone` column).
- `fuel.apply_ercot_zonal_gas_basis` — scale each zone's hub basis by its spot
  share before the mean-zero spread; composes with the floor (haircut shrinks the
  discount, floor caps the residual tail). Env: `ERCOT_GAS_HAIRCUT=1`.

This makes the depth a measured haircut, not a chosen constant — answering the
"isn't a floor magic-numbering?" objection. With (e.g.) a 50% West spot share the
West hub discount halves, lifting CT off the over-suppressed −27.6%.

**Data constraint.** The gas share is forward-reproducible but needs the raw
`f923_*.zip` releases (gitignored, **not present in this environment**; outbound
EIA fetch is blocked by the network policy — returns the HTML homepage, not the
zip). The contract-type extraction on `main` is **coal-only**
(`coal_takeorpay_*.csv`). Morgan Creek / Permian Basin are merchant and file no
Schedule-5 receipts, so there is no per-plant fallback either. Until
`gas_takeorpay_ERCOT.csv` is produced (run the deriver where f923 lives), the
haircut is inert and the cited −0.50 scalar floor applies.

## Disposition / next steps

- **Layer 1 (floor) is merged and works**, validated 2024 (matched baseline) and
  3-yr (`results/calibration/ctfloor_3yr`). It over-corrects with the cited −0.50.
- **Layer 2 (haircut) is wired and tested**, inert until the gas share lands.
  Reproduce the share + re-grounded keeper:
  ```bash
  # where the f923_2023/24/25 zips are under inputs/raw-data/:
  python scripts/derive_gas_takeorpay.py --iso ERCOT --year 2023 2024 2025
  ERCOT_ZONAL_GAS=1 ERCOT_GAS_FLOOR=1 ERCOT_GAS_HAIRCUT=1 KEEPER_RTORDPA=1 \
    KEEPER_PERSIST_P2=1 KEEPER_STGAS_DRAG=1 \
    KEEPER_PRB_PARAMS='{"coal_prb_passthrough_floor":0.78,"coal_prb_follower_floor":0.78}' \
    python scripts/probes/_keeper_2023as_run.py ctfloor_haircut_3yr 2025 2023 \
    '{"ST_GAS":{"committed":0.0}}'
  ```
- **Direction 3 (peaker cost / classification)** is the complementary lever for
  the residual: price Morgan Creek (DFO distillate peaker) on oil not Waha gas,
  and check the GT-peaker low-CF / startup economics. See the handoff prompt in
  the session.

Do **not** dial the floor depth or any per-unit adder to land CT_PEAKER on 8.21
(CLAUDE.md #11) — the depth must come from the measured spot share, the residual
from the per-unit fuel/cost fixes.
