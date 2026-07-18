# ERCOT CT_PEAKER over-run: the Waha delivered-gas floor & contract haircut (2026-06)

> **SUPERSEDED (run154, 2026-06-24).** This doc's conclusion — "the gas-side
> lever is largely exhausted; the residual must close at the unit level
> (direction 3)" — was **wrong**. The gas side was *not* exhausted: the run153
> per-plant contract haircut was **backwards** (it kept 100%-spot Permian/Laredo
> at the full Waha hub collapse and over-priced 100%-contract Ector), and pricing
> on the **hub** rather than the **delivered** burner tip was the root cause.
> run154 replaces the haircut with a structural **net-load-indexed West delivered
> gas step** (firm at high net-load, collapsed at low, floored at a physical
> burner-tip minimum) and corrects **Laredo's zone misassignment** (it is South
> TX / Rio Grande, not West/Permian — the bin sheet put it on Waha). CT_PEAKER is
> now in band all three years without a per-unit fit. See
> `docs/ercot-west-netload-gas-shape-2026-06.md`. Two claims below are now known
> false: (a) "Layer 2 haircut is the honest correction — keep it" (dropped); (b)
> "Laredo 3439 is a West GT peaker" (it is a South-zone unit, idles correctly once
> rezoned). Kept for history.

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

- `scripts/data/derive_gas_takeorpay.py` — per-plant gas contract/spot share from
  EIA-923 Schedule-5 **Purchase Type** (C/NC/T = firm, S = spot), mirroring the
  coal take-or-pay deriver → `data/raw/_processed-legacy/gas_takeorpay_ERCOT.csv`.
- `fuel.ercot_gas_spot_share_by_plant` — each gas plant's own EIA-923 spot share,
  keyed on `plant_code` (the implementation lever). `ercot_gas_spot_share_by_zone`
  is kept as the MMBtu-weighted zonal aggregate, now only a diagnostic log.
- `fuel.apply_ercot_zonal_gas_basis` — scale **each gas unit's** hub basis by **its
  own plant's** spot share (`gen_basis *= unit_haircut`) before the mean-zero
  spread; non-reporting units default to 1.0 (full spot exposure). Composes with
  the floor (haircut shrinks the discount, floor caps the residual tail). Env:
  `ERCOT_GAS_HAIRCUT=1`.

This makes the depth a measured haircut, not a chosen constant — answering the
"isn't a floor magic-numbering?" objection.

**Per-PLANT, not zone-average (run153).** Applying each unit's *own* share is both
more physically faithful and a strictly better fit (#11/#12): a 100%-spot unit
(Permian Basin, Laredo) keeps the full Waha discount while a 100%-contract unit in
the *same* zone (Ector County, share 0.0) loses it entirely — the zone mean (0.78)
smeared one number across both and mis-priced each. Result vs the zone-average
run152: CT_PEAKER 2023 −17.6% (was −25.9%), **2024 +48.7% (was +68.6%)**, 2025
+62.7% (was +66.8%) — Ector County correctly backing down outweighs the 100%-spot
Permian peakers staying cheap. LMP MAE 27.8/15.2/11.3 (no regression).

**Measured result (EIA-923 2023–24 Schedule-5, `gas_takeorpay_ERCOT.csv`):** the
West/Permian gas spot share is **0.78** (MMBtu-weighted), and the biggest CT
over-runners are **100% spot** — Permian Basin 3494 and Laredo 3439 buy *all*
their gas spot at Waha (Ector County 58471 is 100% contract; Quail Run 43% spot;
Odessa-Ector 100% spot and dominates the weighting at 100M MMBtu). So the haircut
scales the West hub discount by only ~0.78 (−2.19 → −1.71): a **small** correction.

This is the decisive finding, and it cuts against the floor: **the measured data
shows these merchant peakers genuinely pay cheap spot Waha gas** (they are 100%
spot, by receipt). The gas price the model gives them is therefore *not* the
error — the `−0.50` floor (layer 1) overstates their true delivered fuel cost and
is closer to a fit than a physical correction (CLAUDE.md #11: prefer the measured
input, find the real root cause). The reason Permian Basin / Laredo run ~2–9% CF
in reality despite cheap fuel is **peaker economics, not fuel price** — old/low-CF
GTs with high startup + non-fuel going-forward costs, plus (for Morgan Creek) the
wrong fuel entirely. That is **direction 3**, and the measured contract data shows
the gas-side lever is largely exhausted: the haircut is the honest, measured gas
correction (keep it), the floor is the non-physical level patch (drop it once
direction 3 carries the residual), and the bulk of the CT over-run must close at
the unit level.

**Data constraint (RESOLVED).** The gas share is on disk:
`data/raw/_processed-legacy/gas_takeorpay_ERCOT.csv` (EIA-923 2023–24, committed).
The f923 zips download from the EIA-923 **archive** path
(`.../eia923/archive/xls/f923_<year>.zip` — the live `/xls/` path 301-redirects to
the homepage, which is what blocked the first attempt); they stay gitignored and
are re-downloadable from the URL recorded in `scripts/data/derive_gas_takeorpay.py`.
Morgan Creek / Permian Basin are merchant and file no Schedule-5 gas receipts, so
they default to spot share 1.0 (full discount) — consistent with the deriver's
"no classifiable Purchase Type → treated as fully spot".

## Disposition / next steps

- **Layer 2 (haircut) is the honest, measured gas correction — keep it.** Live and
  **per-plant** (`ERCOT_GAS_HAIRCUT=1`, run153 on the dashboard): each gas unit is
  haircut by its own EIA-923 spot share. It trims the over-run (2024 +82.8% →
  +48.7%) — chiefly by correctly pricing the 100%-contract Ector County off its
  discount — but cannot close it, because the dominant over-runners are 100% spot
  and genuinely buy cheap Waha gas.
- **Layer 1 (floor −0.50) is now suspect.** The contract data shows the 100%-spot
  over-runners genuinely pay ~$0 spot Waha gas, so the floor overstates their fuel
  and is closer to a fit than a physical correction. Recommend dropping it (or
  keeping only the haircut) once direction 3 carries the residual. The merged
  `ercot_gas_delivered_floor_basis` stays in the code as a default-off lever.
- **Direction 3 (peaker cost / classification) is now the PRIMARY lever**, not the
  complement: the measured contract data shows the gas-side is largely exhausted.
  Price Morgan Creek (DFO distillate peaker) on oil not Waha gas; treat the
  old/low-CF GT peakers (Permian Basin, Laredo) via startup / non-fuel
  going-forward economics or the P2 commitment screen — the reason they idle in
  reality is peaker economics, not fuel price. See the direction-3 handoff prompt.

Reproduce the per-plant haircut keeper (run153; gas share already on disk):
```bash
ERCOT_ZONAL_GAS=1 ERCOT_GAS_HAIRCUT=1 KEEPER_RTORDPA=1 \
  KEEPER_PERSIST_P2=1 KEEPER_STGAS_DRAG=1 \
  KEEPER_PRB_PARAMS='{"coal_prb_passthrough_floor":0.78,"coal_prb_follower_floor":0.78}' \
  python scripts/probes/_keeper_2023as_run.py ctharcut_pp_3yr 2025 2023 \
  '{"ST_GAS":{"committed":0.0}}'
```

Do **not** dial the floor depth or any per-unit adder to land CT_PEAKER on 8.21
(CLAUDE.md #11) — the gas-side depth comes from the measured spot share (now
shown to be small), and the residual must close at the unit level (direction 3).
