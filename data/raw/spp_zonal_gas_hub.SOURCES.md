# `spp_zonal_gas_hub.csv` — SOURCES

Landed **2026-09-07** by lane **SPP-32**
(`docs/multi-iso/spp-addition-plan-2026-09.md` §5 row SPP-32). Schema is exactly
the MISO/PJM/CAISO one (`zone,year,basis_vs_hh_usd_mmbtu,hub,source`), so
`market_sim.data.fuel.basis.meanzero._zonal_gas_basis_by_zone` reads it with no
new parsing code.

## What each zone sits on, and why that state

SPP's two model zones straddle the Mid-Continent gas complex. Each zone's basis
is the EIA *natural gas delivered to electric power consumers* price for **one
proxy state**, minus the Henry Hub monthly mean, averaged over the 12 months of
the year.

| Zone | Proxy state | EIA series | Hub | Why this state |
|---|---|---|---|---|
| SPP-North | KS | `N3045KS3` | NGPL Mid-Continent / Panhandle Eastern | Plurality of the zone's gas fleet (30.1 %) and the only North state EIA publishes |
| SPP-South | OK | `N3045OK3` | ANR Oklahoma / Panhandle Eastern | Outright majority of the zone's gas fleet (59.0 %) |

The weights are measured, not asserted — EIA-860 operable nameplate (`Energy
Source 1 = NG`) assigned to model zones by
`market_sim.data.zone_assignment.build_zone_lookup("SPP")`:

| Zone | Gas MW | State split |
|---|---|---|
| SPP-North | 13,097 | KS 30.1 %, MO 30.0 %, NE 21.7 %, ND 9.6 %, SD 5.3 %, IA 2.4 % |
| SPP-South | 23,627 | **OK 59.0 %**, TX 29.2 %, NM 5.9 %, LA 4.1 %, AR 1.7 % |

**Stated limitation, not buried:** KS is only 30 % of SPP-North's gas fleet, so
the North row is a genuine *proxy* for a zone whose gas also sits in MO / NE /
the Dakotas — states EIA does not publish this series for. This is the same
construction and the same limitation MISO-West carries on its IA proxy
(`miso_zonal_gas_hub.csv`). SPP-South's OK row is on firmer ground at 59 %.

## The committed span is 2022–2024, and why it stops there

`N3045OK3` is an **intermittent** series: EIA publishes it for 2022, 2023 and
2024 and prints **nothing for 2019–2021 or for 2025**. `N3045KS3` is complete
2019–2025. The committed table is therefore the **intersection** — the years in
which *both* zones have a published series:

| Zone | Published years | |
|---|---|---|
| SPP-North (KS) | 2019 – 2025 | |
| SPP-South (OK) | 2022 – 2024 | |
| **Committed** | **2022, 2023, 2024** | 2 zones × 3 years = 6 rows, from **36 monthly source observations per zone** |

This is deliberate and it is the *safe* choice rather than the maximal one.
`_zonal_gas_basis_by_zone` filters on `year` and returns `{zone: basis}` for
whatever rows it finds; a consumer then reads each zone with `.get(name, 0.0)`.
Committing a 2025 North row without its South partner would hand an armed
applier `{"SPP-North": +1.129}` and let SPP-South silently default to `0.0` — a
fabricated ~$0.7/MMBtu cross-zonal spread produced entirely by a publication
gap. With no 2025 row at all the lookup returns `None` and the applier no-ops,
which is a *visible* absence instead of an invisible error.

## Why the 2025 gap is NOT filled by blending in TX/NM

The obvious repair — weight SPP-South over the states EIA does publish — was
measured and **rejected**. The candidate constructions, gas-capacity weighted:

| Year | OK only | OK+TX+NM | TX+NM only | \|TX+NM − OK\| |
|---|---|---|---|---|
| 2023 | +0.418 | +0.258 | −0.012 | 0.429 |
| 2024 | +0.861 | +0.451 | −0.239 | **1.100** |
| 2025 | — | −0.483 | −0.483 | — |

TX+NM does not track OK: it is $0.43/MMBtu away in 2023 and **$1.10/MMBtu** away
in 2024. Renormalising onto TX+NM for 2025 would swing SPP-South's basis from
+0.861 (2024) to −0.483 (2025) — a $1.34/MMBtu year-on-year move manufactured by
*which states EIA happened to publish*, not by the gas market. That is precisely
the "bury the error back inside an inaccurate input" that rule 14
`[R-ACCURATE]` forbids, so the honest table has a hole where the source has one.

**What a consumer must do about 2025** is therefore an explicit decision, not a
default: either re-fetch `N3045OK3` once EIA prints it, or declare a hold-last
rule in the run that needs it. No applier is armed today (this lane adds no
`ScenarioConfig` field — plan §7 gate G8), so nothing depends on the answer yet.

## Units convention (inherited, stated)

The EIA delivered series is `$/Mcf` and Henry Hub is `$/MMBtu`; they are
subtracted directly, as in every sibling table (`pjm_`, `miso_`, `caiso_`). The
~3.7 % Mcf→MMBtu difference is common to both zones and the mean-zero applier
subtracts a capacity-weighted mean, so it very largely cancels out of the only
thing this table is used for — the cross-zonal *spread*. Diverging from the
sibling convention for SPP alone would be an unmotivated per-ISO degree of
freedom (rule 21 `[R-DOF]`).

## The measured spread, for the record

| Year | SPP-North | SPP-South | N − S |
|---|---|---|---|
| 2022 | +0.850 | +0.612 | +0.238 |
| 2023 | +0.784 | +0.418 | +0.366 |
| 2024 | +0.729 | +0.861 | **−0.132** |

The spread **changes sign** between 2023 and 2024. That is real and it is why
this enters as data rather than as a fitted "north premium" knob — exactly the
posture `caiso_zonal_gas_hub.csv` records for its own sign-flipping N–S spread.

## Inputs

* `data/raw/gas-prices/eia_delivered_gas_{KS,OK,TX,NM}_monthly_{2019-2022,2023-2025}.csv`
  — landed by lane SPP-11 (`docs/handoffs/FINDING-spp-11-2026-09-06.md` §5,
  which is where the `N3045OK3` 2025 gap was first recorded), fetched from the
  EIA dnav workbooks `hist_xls/N3045<ST>3m.xls`.
* `data/raw/gas-prices/henry_hub_monthly.csv` — EIA `RNGWHHDm`.
* `market_sim.config.paths.active_eia860_dir()` — the capacity weights above.

## Regeneration

The table is six numbers, each the mean of twelve published monthly prints minus
the matching Henry Hub prints. Re-derive only when the **source data** updates
(rule 23 `[R-FROZEN-DERIVE]`) — in practice, when EIA publishes `N3045OK3` for
2025 — never because a residual moved.

---

## STATUS UPDATE 2026-09-07 — lane SPP-54: a re-key for the SPS-pocket topology exists in the design commit

`docs/handoffs/PRECOMMIT-spp-54-2026-09-07.md` §5. On the SPP-54 three-zone map (`SPP-North` / `SPP-South`
residual / `SPP-SPS`; design commit `8d427adc`, not landed on main — no solve has run) the table is re-keyed
with **no measured value moved**: North and the residual South keep their KS and OK rows (Oklahoma is ~60 %
of the residual's gas fleet once the pocket is carved out), and `SPP-SPS` takes the **TX proxy** rows
(`N3045TX3`: 2022 −0.081 / 2023 +0.096 / 2024 −0.010, the values lane SPP-57 derived by this instrument
for its residual-South row) — the pocket's gas fleet is TX ≈ 4,680 of ≈ 6,100 MW (NM ≈ 1,410), and EIA
prints no New Mexico delivered-to-electric-power series usable here. The 2022–2024 span rule and the
no-applier posture are unchanged.
