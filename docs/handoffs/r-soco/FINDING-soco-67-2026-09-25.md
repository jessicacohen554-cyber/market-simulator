# FINDING — soco-67: the 2023 CT_PEAKER excess sits on a CC fleet pinned at its availability ceiling, and one ceiling is a double count

Lane soco-67, 2026-09-25. Zero LP. The object is SOCO's only failing criterion: 2023 C1 CT_PEAKER, model +7.22 TWh
and +3.0 pp against the keeper `2026-09-25-r-soco-b2-boundary`.

Every number here is reproduced by one of these:

- `scripts/probes/_soco67_gdrift_identity.py`
- `scripts/probes/_soco67_phase0.py`
- `scripts/probes/_soco67_cod_census.py`

They read three things: the keeper's committed hourlies and registered run payload, fleet rebuilds made with
`run_year(fleet_only=True)` on the keeper's own recipe, and CAMPD unit-level CEMS. EIA-923 per-plant net comes from
`_soco62_phase0.bench_plant_twh`.

## 0. G-DRIFT (rule 29(b)): all INERT, and the keeper is the control

The keeper legs were solved at `422915ca`. That sha is not an ancestor of `main` because the lane was rebased.
`main` @ `9241a212` adds four non-lane commits on the solve path:

- COAL-SUB `8eaf34b5` and `05437cc0`
- NWPP-NEXT `9e3b40d1`
- PJM-NEXT `18ab44d2`

**Measured, not argued.** The probe `_soco67_gdrift_identity.py` rebuilds every keeper year at both shas on one
shared data tree. **Every LP input is bit-identical in all seven years 2019–2025.** The checked inputs are
`unit_ids`, `mc_base`, `pmax`, `pmin`, `min_gen`, `availability`, `heat_rate`, `emission_rate`, `vom` and demand.

**The hunks the rebuild cannot see** are the ones after the `fleet_only` exit, in `model/`, `pipeline/`,
`results/scarcity.py` and `runner.py`:

- **ERCOT-only or PJM-only branches:** the held classes, the RUC groups, the PJM commitment physics and the ERCOT
  envelopes.
- **The reliability-floor coal limb** (`artifact_class_array`). SOCO has no `reliability_floor_coeffs_SOCO.csv`,
  and the keeper's `reliability_floor` is `None`.
- **`fleet_zone_vintage_coords`**, which is set per solve. Its dataclass default is `False` and the keeper recipe
  does not carry it.

The moved constants are the coal-family rows, `RGGI_MEMBER_STATES_BY_YEAR` and `CAMPD_BINNING_ISOS`. The rebuild
shows all of them land identically for SOCO. The `ScenarioConfig` path defaults that "changed" are the worktree's
absolute paths.

**Verdict: every hunk is INERT. The committed bundle is the control, and no control solve is spent.**

## 1. Where the excess is

The 2023 class moves against actual (EIA-923), in TWh:

| class | model − actual |
|---|---|
| CT_PEAKER | **+7.23** |
| ST_GAS | −4.50 |
| COAL_BIT | −2.12 |
| COAL_PRB | −1.24 |
| CC_REGULAR | −0.74 |

- **By zone,** CT is +6.14 in GA and +1.29 in AL.
- **By month,** CT runs from +0.4 to +1.4 TWh every month from March to December. The peak is July–August.
- **2024 has the same signature at a smaller size:** CT +4.53, ST −4.26, coal −5.34, CC +0.38. That is why 2024
  passes.

**Plants.** Five GA/AL IPP turbines carry +6.6 TWh of the excess. These are the cheapest CT offers, at an mc of
$33.0–35.1/MWh.

| plant | model TWh | CEMS TWh | model hours on | CEMS hours on | model runs | CEMS runs |
|---|---|---|---|---|---|---|
| Tenaska Georgia 55061 | 2.81 | 0.25 | 4,070 | 505 | 355 | 55 |
| Calhoun 55409 | 1.57 | 0.04 | 3,088 | 278 | 341 | 31 |
| Walton County 55128 | 1.42 | 0.26 | 4,393 | 684 | 347 | 66 |
| Washington County 55332 | 0.77 | 0.15 | 1,738 | 704 | 216 | 55 |
| Baconton 55304 | 0.73 | 0.04 | 4,595 | 898 | 358 | 88 |

**Run length is right; run count is not.** Median runs are 9–13 h in the model and 7–14 h in CEMS. But the model
cycles these units almost every day, 4–10× more runs than they really made. A per-run start amortization at NREL
$20/MW over a 12 h run is about $1.7/MWh, so the SOCO-64 start-cost lever (`tranche_startup_amortization`, G) is
weak against this signature.

**The merit order explains the choice.** On the keeper's own fleet, those five CTs undercut the gas boilers
(ST_GAS $34.7–36.4) and every coal econ tranche. COAL_BIT's committed and econ tranches sit at $61–85 (2023
delivered bituminous), and in the keeper COAL_BIT dispatches **only its must-run tranche**.

## 2. The CC fleet is pinned at its ceiling, and part of the ceiling is below measured output

**The ceiling binds.** In 2023, CC_REGULAR availability is 111.87 TWh and its dispatch is 110.15. It sits within
1 % of its hourly ceiling in **6,922 h**. It has **zero headroom in every one of the 4,727 hours** in which
CT_PEAKER runs above 50 MW.

**Measured output exceeds the ceiling.** Measured CC output (CEMS gross × 0.97) exceeds the model's CC availability
in 4,071 h. Summed by the hour, that is **4.01 TWh** at class grain and **9.10 TWh** at plant grain. The 2024
figures are 3.40 and 7.67 TWh. The excess is concentrated in June–September, the same months as the CT excess.

The largest plant-grain gaps in 2023 (TWh of availability below measured output):

| plant | model availability | CEMS net | EIA-923 net | excess | mechanism |
|---|---|---|---|---|---|
| **Barry (3)** | **4.38** | 7.08 | **7.34** | 2.79 | **double count, §3** |
| Jack McDonough (710) | 16.86 | 17.53 | 17.83 | 1.21 | pmax 2,335 MW < measured p95 2,511 |
| Thomas A. Smith (55382) | 8.77 | 8.80 | 8.74 | 0.80 | pmax 1,126 MW < p95 1,318 (reconciled down to a 1,192 MW nameplate bound) |
| E B Harris (7897) | 7.06 | 6.40 | 6.46 | 0.66 | |
| H A Franklin (7710) | 14.26 | 13.60 | 13.68 | 0.55 | |
| Daniel CC (6073) | 8.35 | 8.77 | 7.99 | 0.48 | |

`unit_partial_outage_windows` is **not** the cause: CC availability is identical with it off.

## 3. Barry unit 8: one not-yet-built unit, removed twice (rule 19)

**The unit.** EIA-860 lists Barry's third CC block, A3C1 + A3ST, at 685 MW summer / 774 MW nameplate, with
commercial operation in **2023-11**. It is in the 2023 LP `pmax` (1,821.2 MW = A1 + A2 + A3).

**First removal: the COD ramp.** The ramp in `arrays.py` is applied last. It holds the Barry CC bin at its online
nameplate share, **0.580**, from January to October.

**Second removal: the CAMPD window.** The per-unit extract carries unit `8` (747 MW) out
**2023-01-01 → 2023-12-12**. CAMPD has **no record of unit 8 in 2019–2022**. It first files a row on
**2023-10-01** and first produces on **2023-12-12**. The deriver fills a unit's absent hours as dark. So the
unit's absence from the record became a 345.6-day outage, and the overlay removes 747 MW **again**, from the A1/A2
blocks that existed.

**Result.** The model's Barry CC availability is 4.38 TWh against its own EIA-923 net of 7.34. The model is
physically forbidden from its measured output.

**The census** (`_soco67_cod_census.py`, every keeper-armed SOCO extract, 2019–2025) finds that this is the only
double count that moves a solved fleet:

- **Lowman (56) CC1** is also clipped by the mechanism below, but it is inert. Its COD ramp is 0 through August,
  so 0 × 0.
- **The `NET0-923` rows for 2021/22** are also touched and also inert. The plant is absent from those vintages.

## 4. What this does and does not explain

**The repair** clips unit 8's window to the COD month. Barry CC availability then goes 4.38 → **7.20 TWh**,
against the measured 7.34 (§ PRECOMMIT).

**A greedy restack** on the keeper's hourlies moves 2023 as follows. It counts only hours where CC is at its
ceiling, and displaces the highest-mc running CT/ST first:

- CC_REGULAR **+1.71 TWh**
- CT_PEAKER **−1.02 TWh**
- ST_GAS −0.70 TWh

That is a partial closure. **Routed, not stacked (rule 19):**

1. **CC capability basis.** Several CC plants have LP `pmax` below their measured p95 output. After the clip, the
   plant-grain excess is still 6.76 TWh in 2023 and 7.67 in 2024. The load log also shows a "trusted bound" that
   reconciles T.A. Smith's 1,353 MW down to its 1,192 MW nameplate while it measures 1,318 MW net at p95. This is
   SOCO's `cc_winter_capability_basis`, `cc_nameplate_summer_derate` and `cc_capacity_reconcile_path` cells, all
   `U`.
2. **The `<5-day` gas companion** (`campd-unit-outages-shortgas-SOCO.csv`) still routes Barry boiler units 1, 2 and
   4 to CC_REGULAR. This is the SOCO-56 defect, which was repaired only in the ≥5-day per-unit file. It is small
   (≤0.06 TWh/yr).
3. **CT daily cycling** (§1). This is the owner question from SOCO-65 §4, still open, and it is unchanged by this
   lane.
