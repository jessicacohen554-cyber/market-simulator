"""Fuel-price trajectories, availability shapes, and carbon price paths.

Split out of ``config/constants.py`` (refactor-consolidation plan §5, D-1:
constants split, 2026-07). Pure transplant — every value and citation comment
is byte-identical to its pre-split form; ``config.constants`` re-exports the
entire surface, so both import paths resolve to the same objects.

Contents: Henry Hub / basis / seasonality gas prices, coal price trajectories
(incl. lignite/PRB and the coal-vs-gas passthrough sigmoid inputs), oil,
biomass and nuclear fuel prices, thermal availability / maintenance shapes,
and the carbon price paths (CARBON_PRICE_PATHS, state carbon adders, CARB
unspecified-import EF).
"""

# --- Henry Hub Natural Gas Price Trajectories ($/MMBtu, real 2024$) ---
# Source: EIA Annual Energy Outlook 2025 (AEO2025), released April 15, 2025
# Table 13: Natural Gas Supply, Disposition, and Prices
# Reference case, High Oil and Gas Supply case, Low Oil and Gas Supply case
# URL: https://www.eia.gov/outlooks/aeo/
# Note: AEO2025 assumptions frozen as of December 2024.
# All prices in real 2024 dollars per MMBtu.
# The model runs 2026-2050. The 2025 entry is included for interpolation
# context (it is the shared near-term anchor across all three cases).
#
# These trajectories replace the prior GAS_PRICE_BASE + GAS_PRICE_ESCALATION
# approach, which used a flat 2%/yr exponential that diverged from EIA's
# modeled supply/demand/LNG-export dynamics.
#
# AEO2026 Counterfactual Baseline case (the "mid" path): Henry Hub is $3.88
# (2026), eases to ~$3.6-3.7 through 2028, then rises to a ~$5.4 plateau
# (2040-41) on LNG-export growth and rising marginal production cost before
# declining to $4.64 (2050). Source: EIA AEO2026 Table 13 (real 2025$/MMBtu),
# https://www.eia.gov/outlooks/aeo/
#
# The model's gas_price_path lever ("low"/"mid"/"high") maps to AEO cases:
#   "low"  -> AEO High Oil and Gas Supply case (more supply -> lower prices)
#   "mid"  -> AEO Counterfactual Baseline case (formerly the Reference case)
#   "high" -> AEO Low Oil and Gas Supply case (less supply -> higher prices)
#
# VINTAGE: RE-DERIVED 2026-07-20 (FF-G2, CLAUDE.md rule 23) from AEO2026 Table
# 13 (data/raw/eia-aeo/eia_aeo2026_fuel_prices.csv, API-fetched by
# scripts/data/fetch_eia_aeo.py --aeo-year 2026), bumping the prior AEO2025
# vintage (P-1D). Two edition changes: (a) AEO2026 is in real 2025$ (AEO2025
# was 2024$) — the ~$1/MMBtu near-term lift over the old mid ($2.74 in 2026)
# is a real modeled change, not a dollar-year artifact (the 2024$->2025$ shift
# is only ~2.2%); (b) EIA renamed the central case "Reference" ->
# "Counterfactual Baseline" (cb2026), still the central projection. Re-derive
# with scripts/data/derive_fuel_trajectories.py::derive_gas_trajectory (default
# --aeo-year 2026) and paste the FORECAST years (2026-2050) only; see
# docs/fuel-forward-methodology-2026-07.md (FF-G2) for the full grounding,
# near-term AEO-vs-STEO-vs-strip triangulation, and the AEO-vs-AEO delta ledger.
#
# The 2023/2024/2025 entries are historical actuals, NOT AEO projections:
# the EIA Henry Hub spot annual averages ($2.54 in 2023, $2.19 in 2024, $3.52
# in 2025), identical across all three paths because a realized price has no
# scenario branching. They are DELIBERATELY kept unchanged across the vintage
# bump (AEO2026's own 2025 base-year value $3.47 is discarded in favour of the
# measured $3.52): the backcast neighbor-price seam (data.neighbor_price) reads
# these <=2025 values, so keeping them fixed preserves backcast byte-identity —
# the AEO2026 refresh touches only forecast years 2026+.
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
# URL: https://www.eia.gov/dnav/ng/hist/rngwhhdA.htm

HENRY_HUB_TRAJECTORIES: dict[str, dict[int, float]] = {
    # AEO High Oil and Gas Supply case -> model "low" gas price path.
    # Higher resource recovery + faster tech improvement = lower prices.
    "low": {
        2023: 2.54,
        2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 3.52,  # EIA Henry Hub spot annual average (2025 historical actual,
        # matches calibration_reference.henry_hub_actual; was a stale 2.88
        # forecast value). Consumed only by the backcast neighbor-price seam for
        # 2025 (forecasts start at START_YEAR 2026), so this keeps each
        # neighbor's gas consistent with the ISO's own 2025 delivered gas.
        2026: 3.2,
        2027: 2.82,
        2028: 2.74,
        2029: 2.8,
        2030: 2.96,
        2031: 3.1,
        2032: 3.43,
        2033: 3.43,
        2034: 3.36,
        2035: 3.42,
        2036: 3.52,
        2037: 3.54,
        2038: 3.45,
        2039: 3.37,
        2040: 3.3,
        2041: 3.21,
        2042: 3.11,
        2043: 3.03,
        2044: 2.97,
        2045: 2.92,
        2046: 2.88,
        2047: 2.86,
        2048: 2.83,
        2049: 2.78,
        2050: 2.75,
    },
    # AEO Reference case -> model "mid" gas price path.
    "mid": {
        2023: 2.54,
        2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 3.52,  # EIA Henry Hub spot annual average (2025 historical actual,
        # matches calibration_reference.henry_hub_actual; was a stale 2.88
        # forecast value). Consumed only by the backcast neighbor-price seam for
        # 2025 (forecasts start at START_YEAR 2026), so this keeps each
        # neighbor's gas consistent with the ISO's own 2025 delivered gas.
        2026: 3.88,
        2027: 3.62,
        2028: 3.67,
        2029: 3.84,
        2030: 4.48,
        2031: 4.85,
        2032: 5.27,
        2033: 5.23,
        2034: 5.04,
        2035: 5.05,
        2036: 5.17,
        2037: 5.28,
        2038: 5.3,
        2039: 5.31,
        2040: 5.36,
        2041: 5.38,
        2042: 5.29,
        2043: 5.14,
        2044: 5.05,
        2045: 5.0,
        2046: 5.01,
        2047: 4.9,
        2048: 4.79,
        2049: 4.7,
        2050: 4.64,
    },
    # AEO Low Oil and Gas Supply case -> model "high" gas price path.
    # Lower resource recovery + slower tech = higher prices.
    "high": {
        2023: 2.54,
        2024: 2.19,  # EIA Henry Hub spot annual average (historical)
        2025: 3.52,  # EIA Henry Hub spot annual average (2025 historical actual,
        # matches calibration_reference.henry_hub_actual; was a stale 2.88
        # forecast value). Consumed only by the backcast neighbor-price seam for
        # 2025 (forecasts start at START_YEAR 2026), so this keeps each
        # neighbor's gas consistent with the ISO's own 2025 delivered gas.
        2026: 4.31,
        2027: 5.0,
        2028: 6.0,
        2029: 6.61,
        2030: 6.91,
        2031: 7.29,
        2032: 7.83,
        2033: 8.07,
        2034: 8.3,
        2035: 8.62,
        2036: 9.16,
        2037: 9.67,
        2038: 9.9,
        2039: 10.22,
        2040: 10.38,
        2041: 11.07,
        2042: 11.48,
        2043: 11.74,
        2044: 12.0,
        2045: 12.45,
        2046: 12.79,
        2047: 13.05,
        2048: 13.27,
        2049: 13.48,
        2050: 13.67,
    },
    # --- Capacity-hindcast gas paths (W2-P5, plan §1.2) --------------------
    # "hindcast_realized": the year's ACTUAL Henry Hub spot annual average
    # ($/MMBtu), the realized-fuel variant of the capacity hindcast. Values are
    # the annual mean of data/raw/gas-prices/henry_hub_monthly.csv (EIA Henry
    # Hub spot), matching the historical entries already carried in the low/mid/
    # high paths above (2023: 2.54, 2024: 2.19, 2025: 3.53). 2022 is DELIBERATELY
    # omitted (rule 22 quarantine bridge — the hindcast never solves or reads
    # 2022, and its 2022 evolution step draws the 2021 value via driver_year).
    "hindcast_realized": {
        2021: 3.91,  # EIA Henry Hub spot annual mean (henry_hub_monthly.csv)
        2023: 2.54,
        2024: 2.19,
        2025: 3.53,
    },
    # --- As-known-then gas paths (T1-FF Arm K; hindcast plan §2.1) ----------
    # One entry per AEO edition that a hindcast BASE YEAR can be run from:
    # ``hindcast_asknown_aeo<edition>``, read by
    # ``run_capacity_hindcast.full_forward_gas_path(arm="asknown", base_year)``,
    # which HARD-ERRORS rather than substituting another vintage. The
    # realized−asknown gap isolates fuel-input (gas-forecast) error from
    # capacity-path error (plan §1.4 baseline (c); §2.1's three-way read).
    #
    # DOLLAR BASIS (FH-3, 2026-08-02) — every value below is NOMINAL $/MMBtu of
    # its own projection year, converted from the AEO's published real-dollar
    # value by that SAME edition's own projected GDP chain-type price index
    # (Table 20 Macroeconomic Indicators, series
    # ``eci_indx_NA_NA_gdp_NA_NA_y09eq1d3z``, 2012=1.000), rebased on the
    # edition's own history year:
    #     nominal(y) = real(y) x deflator(y) / deflator(edition history year)
    # Two reasons this, and not the published real value:
    #   (a) COMMENSURABILITY. ``hindcast_realized`` above is nominal spot
    #       ($3.91 in 2021, $2.54 in 2023, ...) and the model's whole cost stack
    #       (VOM, offer curves, the 2023-2025 price benches) is nominal. Pricing
    #       Arm K in a stale real-dollar base would put a dollar-year shift
    #       inside the Arm R -> Arm K spread, which is supposed to measure
    #       gas-FORECAST error alone. The drift is not second order: AEO2020$
    #       applied to 2025 understates nominal by 7.6 %, AEO2022$ by 9.0 %.
    #   (b) AS-OF HONESTY. The deflator used is the edition's own PROJECTION,
    #       which is all a forecaster had at the time — never a realized
    #       deflator published later, which would leak post-base-year
    #       information into an ex-ante path (plan §4's as-of test).
    # The low/mid/high forecast paths above keep the AEO's published real values
    # because their edition's dollar year sits alongside the years they price;
    # an as-known vintage is by construction 2-5 years stale, so it cannot.
    #
    # Both entries omit 2022 per the rule-22 bridge (the hindcast never solves
    # or reads 2022; its 2022 evolution step draws the prior year via
    # driver_year), matching ``hindcast_realized``.
    #
    # Source for both: EIA Annual Energy Outlook, Table 13 (Natural Gas Supply,
    # Disposition, and Prices), "Henry Hub spot price", Reference case, via the
    # EIA Open Data API v2 ``aeo`` route. Raw, immutable, re-fetchable:
    # data/raw/eia-aeo/eia_aeo2021_fuel_prices.csv and
    # data/raw/eia-aeo/eia_aeo2023_fuel_prices.csv
    # (scripts/data/fetch_eia_aeo.py --aeo-year 2021|2023). Arithmetic and the
    # full ledger: docs/handoffs/fh-3-asknown-driver-vintages-2026-08.md §2.
    #
    # "hindcast_asknown_aeo2021": AEO2021 Reference (``ref2021``), published
    # 2021-02-03, real 2020$; deflator base 2020 = 1.133393. The
    # as-known-then forecast for a 2021-base hindcast.
    #   year  real(2020$)  deflator  ratio     nominal
    #   2021   3.100730    1.145347  1.010547   3.13
    #   2023   2.992324    1.174500  1.036269   3.10
    #   2024   2.801792    1.194232  1.053679   2.95
    #   2025   2.880324    1.219112  1.075630   3.10
    # CORRECTED 2026-08-02 (FH-3, rule 23 — the change cites the DATA, not a
    # residual). The prior values (2021: 3.07, 2023: 2.86, 2024: 2.88, 2025:
    # 2.93) carried the flag "NEEDS CITATION" in docs/parameter-citations.md and
    # match NO basis of the AEO2021 Reference series — not the published real
    # 2020$ figures, not their nominal conversion, and not a uniform offset or
    # year-shift of either. They are unreconstructible, so they are replaced by
    # the API-fetched series rather than re-cited. Consequence, stated because
    # it is not free: the two registered T1-H runs that used this path
    # (``ercot-2021-2025-asknown``, ``pjm-2021-2025-asknown``) were produced on
    # the old values and no longer reproduce at HEAD; they stand as historical
    # artifacts and any re-read of the realized-vs-asknown spread re-solves.
    "hindcast_asknown_aeo2021": {
        2021: 3.13,
        2023: 3.10,
        2024: 2.95,
        2025: 3.10,
    },
    # "hindcast_asknown_aeo2023": AEO2023 Reference (``ref2023``), published
    # 2023-03-16, real 2022$; deflator base 2022 = 1.269200. The as-known-then
    # forecast for a 2023-base hindcast — Phase A / Arm K (plan §3.1), which
    # hard-errored before this intake.
    #   year  real(2022$)  deflator  ratio     nominal
    #   2023   5.266376    1.321666  1.041338   5.48
    #   2024   4.072381    1.353926  1.066755   4.34
    #   2025   3.489514    1.383368  1.089953   3.80
    # Sanity anchor (not an input): AEO2023's own 2022 history value, 6.524
    # (2022$, ratio 1.0), sits 1.6 % above the realized 2022 Henry Hub annual
    # average of $6.42 — confirming the deflator base is the edition's history
    # year and the rebasing is right. The as-known path is 2.2x the realized
    # 2023 price ($5.48 vs $2.54): AEO2023 was frozen in late 2022 at the top of
    # the post-invasion gas spike and did not see the 2023 collapse. That is the
    # ex-ante driver error Arm K exists to MEASURE, not a value to reconcile.
    "hindcast_asknown_aeo2023": {
        2023: 5.48,
        2024: 4.34,
        2025: 3.80,
    },
}

# --- Regional Basis Differentials ($/MMBtu, relative to Henry Hub) ---
# Source: EIA Natural Gas Weekly Update, 2024-2025 average basis
# URL: https://www.eia.gov/naturalgas/weekly/
# Waha (West Texas/ERCOT): historically trades at a discount to Henry Hub
#   due to Permian associated gas oversupply and pipeline constraints.
# SoCal Citygate (CAISO): historically trades at a premium to Henry Hub
#   due to pipeline constraints into California and limited local production.
#   Measured check (EIA-923 Schedule 5, quantity-weighted delivered gas to
#   CAISO plants minus Henry Hub annual average): +$7.06 in 2023 (the
#   Dec-22/Jan-23 western gas crisis — Jan-2023 delivered $38.7/MMBtu vs
#   HH $3.27), +$2.26 in 2024, +$1.12 in 2025. The +1.20 seed is only
#   right in a normal year; CAISO backcasts therefore default to
#   gas_monthly_actuals (measured ISO-month delivered gas), which makes
#   this scalar a forward-year/fallback value only.
# PJM: no single hub. PJM gas burn spans the Appalachian supply basin
#   (Dominion South / TETCO M2, a structural Marcellus *discount* to Henry
#   Hub from takeaway-constrained oversupply) and the Mid-Atlantic load
#   pocket (TETCO M3 and Transco Zone 6 non-NY, a modest annual *premium*
#   with large winter spikes). Rather than blend hub quotes by hand, the
#   +0.67 scalar is the empirical generation-weighted basis measured from
#   EIA-923 itself: the quantity-weighted delivered gas cost to PJM gas
#   plants (Schedule 5 fuel receipts) minus the Henry Hub annual average was
#   +$0.67/MMBtu in BOTH 2023 ($3.21 vs $2.54) and 2024 ($2.86 vs $2.19).
#   Source: scripts/data/derive_coal_supply.py-style EIA-923 receipt aggregation;
#   same EIA family as the ERCOT/CAISO figures. Caveat: Schedule-5 gas
#   reporting is sparse (~26 PJM plants), likely skewed toward the eastern
#   premium hubs, so this may run slightly high for the western price-taking
#   CCs — but it replaces the prior unvalidated +0.30 placeholder and lands
#   PJM CC dispatch on EIA-923 actuals without distorting the offer curve.
# NYISO: gas burn spans Transco Zone 6 NY / Iroquois (a steep winter premium
#   when downstate pipeline capacity is scarce) and the upstate path-priced
#   CCs. As with PJM, the +0.55 scalar is the generation-weighted basis
#   measured directly from EIA-923: the quantity-weighted delivered gas cost
#   to New York gas plants (Schedule 5 fuel receipts) minus the Henry Hub
#   annual average was +$0.53 (2023: 3.07 vs 2.54), +$0.44 (2024: 2.63 vs
#   2.19) and +$0.55 (2025: 4.08 vs 3.53) — a stable +0.54 quantity-weighted
#   over 2023-2025. Source: EIA-923 Schedule 5 receipt aggregation, same EIA
#   family as the ERCOT/CAISO/PJM figures. Caveat: a single annual scalar
#   flattens NY's pronounced winter blowout (the same Schedule-5 receipts show
#   monthly basis reaching +$3-7 in Jan/Dec) — enable
#   gas_plant_monthly_fuel_pricing for the monthly shape when winter price
#   fidelity matters.
# NEISO: New England gas burn prices off Algonquin Citygate (AGT), the
#   pipeline-constrained hub whose winter basis blows out to many multiples
#   of Henry Hub (doc-08 design decision 1). The +1.10 scalar is the
#   EIA-923 delivered-basis seed for *normal* (non-arctic-event) years:
#   quantity-weighted delivered gas cost to New England plants (Schedule 5
#   fuel receipts) minus the Henry Hub annual average was +$1.17 in 2024
#   (3.37 vs 2.19) and +$1.07 in Apr-Sep 2025 (4.60 vs 3.53); 2023 measured
#   +$3.17 (5.70 vs 2.54), inflated by the Jan/Feb-2023 arctic events
#   (Jan-23 delivered $15.17/MMBtu). Source: EIA-923 Schedule 5 receipt
#   aggregation, same EIA family as the other ISOs. STRONG caveat: only TWO
#   New England plants report Schedule-5 gas receipts (EIA plant codes 1660,
#   6081 — partly LNG-supplied), so the sample is far sparser than
#   PJM/NYISO. NEISO backcasts therefore default to gas_monthly_actuals +
#   the measured Algonquin hub-month basis overlay
#   (gas_hub_basis_overlay; data/raw/gas_basis_by_iso_month.csv),
#   which makes this scalar a forward-year/fallback value only — like the
#   CAISO +1.20 seed.
# MISO: a footprint-wide blend with no single hub. Northern MISO gas plants
#   (IL/WI/MI/MN) price off Chicago Citygate / MichCon (a modest premium driven
#   by interstate transport), while southern MISO (LA/MS/AR) prices essentially
#   at Henry Hub (near-zero basis). The public proxy is the EIA Illinois
#   natural-gas *citygate* series (n3050il3m): 2024 monthly avg = $3.495/Mcf
#   = $3.37/MMBtu (1 Mcf ~ 1.037 MMBtu) vs Henry Hub $2.22/MMBtu -> a raw
#   +$1.15/MMBtu. BUT that EIA "citygate" is the LDC-delivered price (it bakes
#   in full distribution transport), an UPPER BOUND that overstates power-plant
#   burn cost: the Chicago Citygate *trading hub* spot traded ~Henry Hub parity
#   in 2024 (Midwest hubs were weak vs HH), and most MISO gas plants buy nearer
#   the trading hub plus a small transport adder, not the LDC citygate. To keep
#   MISO on the same plant-delivered footing as the PJM/NYISO EIA-923 basis
#   (and not overstate the large southern-MISO Henry-Hub-priced fleet), we
#   reconcile the LDC-citygate proxy down to a footprint blend of +0.30/MMBtu
#   (≈ trading-hub parity + modest northern transport, net of ~$0 southern
#   basis). Refine with EIA-923 MISO Schedule-5 plant receipts in M8.
#   Source: EIA Illinois citygate (n3050il3m) + Henry Hub spot, 2024 avg.
# These are annual average differentials, held constant across the
# projection period for simplicity.
#
# Delivered price = Henry Hub + basis differential
GAS_BASIS_DIFFERENTIAL: dict[str, float] = {
    "ERCOT": -0.50,  # Waha discount; EIA NG Weekly, 2024 avg
    "CAISO": 1.20,  # SoCal Citygate premium; EIA NG Weekly, 2024 avg
    "PJM": 0.67,  # EIA-923 delivered-gas basis (see below)
    "NYISO": 0.55,  # EIA-923 delivered-gas basis (see below)
    "NEISO": 1.10,  # EIA-923 delivered-gas basis, normal-year (see below)
    "MISO": 0.30,  # Chicago Citygate footprint blend, reconciled (see above)
    # SPP (registered 2026-09-06, lane SPP-20): Panhandle Eastern is SPP's
    # own reference hub (the MMU's gas benchmark), and it trades at a DISCOUNT
    # to Henry Hub: HH - Panhandle = $0.38 (2023) / $0.26 (2024) / $0.55
    # (2025) per MMBtu. -0.26 is the 2024 annual average, the same "2024 avg"
    # basis the ERCOT/CAISO rows carry. Source: SPP MMU State of the Market
    # 2025 §4, report p. 119 (PDF p. 131), Fig. 4-4 discussion; 2023 from SOM
    # 2024 §4 (PDF p. 127) — docs/multi-iso/spp-data-audit.md §5 row 8. Rule
    # 14 restatement recorded, not buried: SOM 2024 printed Panhandle 2024 at
    # $1.81 (a $0.38 discount); SOM 2025 restates it $1.98 ($0.26) and the
    # later vintage is used. Forward-year / fallback value only — the SPP
    # backcast prices gas per plant off EIA-923 monthly delivered cost (765 /
    # 753 / 662 SWPP plant-rows, row 8b) like PJM/NYISO, and the zonal hub
    # wiring (Panhandle vs NGPL-MidCon; EIA delivered-to-EP OK/KS/TX/NM state
    # series landed by SPP-11) is SPP-32's.
    "SPP": -0.26,
    # NWPP (registered 2026-09-14, lane NWPP-20): Sumas — EIA's "main pricing
    # point for natural gas in the Pacific Northwest", the Northwest Pipeline
    # receipt point at the BC border that prices NWPP-NW (2,036.8 MW of the
    # zone's gas names Northwest Pipeline, audit §7.2) — trades at a DISCOUNT
    # to Henry Hub in 2024: Sumas 2024 mean $2.002 (data/raw/gas-prices/
    # sumas_weekly.csv, 50 weekly prints, scraped from the EIA Natural Gas
    # Weekly Update narrative by scripts/data/fetch_sumas_weekly.py) minus
    # Henry Hub 2024 mean $2.192 (henry_hub_monthly.csv) = -0.19, the same
    # "2024 avg" basis the ERCOT/CAISO/SPP rows carry. FORWARD-YEAR /
    # FALLBACK VALUE ONLY, and a KNOWN misalignment stated rather than
    # buried (rule 14): the footprint has a 2.51x internal delivered-gas
    # spread (NWMT 1.815 -> PACE 4.564 $/MMBtu, quantity-weighted EIA-923
    # 2023-25; FINDING-nwpp-12 §2.5) across five zones on four hubs (Sumas /
    # Stanfield / Opal / Kern River), so ONE basis misprices most of it; the
    # backcast reads per-plant EIA-923 delivered gas (30-32 plants/yr,
    # committed) and never this scalar, and the zonal hub wiring is lane
    # NWPP-33's. Stanfield, Opal and Kern River have no free public series
    # reachable from the session (SOURCES_nwpp_gas.md §3).
    "NWPP": -0.19,
    # SOCO (registered 2026-09-14, lane SOCO-20): the EIA-923 delivered-gas
    # basis, the PJM/NYISO construction — quantity-weighted Schedule-5
    # delivered gas cost to the SOCO balancing authority's gas plants
    # (data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet, plants by
    # EIA-860 BA code SOCO; 26 / 27 / 27 reporting plants) minus the Henry Hub
    # annual mean (data/raw/gas-prices/henry_hub_monthly.csv): +$0.49 (2023:
    # 3.029 vs 2.536), +$0.64 (2024: 2.832 vs 2.192), +$0.65 (2025: 4.183 vs
    # 3.529). 0.64 is the 2024 value, the same "2024 avg" basis the peer rows
    # carry. The footprint's pipeline basis is Southern Natural Gas (SONAT;
    # Southern Company Gas holds 50 %) plus Transco into northwest Georgia via
    # the Dalton Pipeline (SOCO-12 §4), and NO free public daily index exists
    # at either — the state monthly delivered series (AL / GA / MS, SOCO-12)
    # is the reachable measured input. Forward-year / fallback value only —
    # the SOCO backcast prices gas per plant off EIA-923 monthly delivered
    # cost like PJM/NYISO; the zonal hub wiring is SOCO-32's.
    "SOCO": 0.64,
}

# Per-YEAR MEASURED delivered-gas basis ($/MMBtu), by ISO — the same
# construction as :data:`GAS_BASIS_DIFFERENTIAL` above, keyed by the year whose
# receipts it was measured on instead of collapsed to one "2024 avg" scalar.
# Consulted ONLY when ``ScenarioConfig.gas_basis_differential_measured_by_year``
# is armed AND the (iso, year) pair has a row here; every other ISO, and every
# year outside a row (a forecast year, a year whose receipts are not yet
# filed), falls through to the scalar above unchanged.
#
# WHY IT EXISTS (rule 14 [R-ACCURATE], rule 23 [R-FROZEN-DERIVE]). The scalar
# is ONE year's value applied to every year, and it is documented in its own
# comment as a "forward-year / fallback value only". Lane SOCO-54 (2026-09-20)
# turned ``gas_plant_monthly_fuel_pricing`` OFF for SOCO, which promoted that
# declared FALLBACK onto SOCO's PRIMARY backcast gas-pricing path: since then
# ``resolve_annual_gas_price`` returns ``gas_price_override + 0.64`` for every
# SOCO gas unit in every year, so 2023 carries a +0.15 $/MMBtu error
# (~+$1.65/MWh at ~11 MMBtu/MWh) on the whole gas block. SOCO-54's own
# ADDENDUM declared that imprecision at full magnitude and ROUTED the repair
# rather than taking it, because taking it after seeing that lane's result
# would have been selecting a parameter on the outcome. This table is that
# routed repair, taken as its own single-delta change on the SOURCE-DATA
# citation below and never on a residual.
#
# DERIVATION — re-run at HEAD by lane SOCO-55 (2026-09-20) and reproducing
# SOCO-20's committed numbers exactly. Quantity-weighted EIA-923 Schedule-2
# delivered natural-gas cost to the SOCO balancing authority's own gas plants
# (``data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet``, plants
# taken from the run's own EIA-860 SOCO fleet), MINUS the Henry Hub annual mean
# (``data/raw/gas-prices/henry_hub_monthly.csv``):
#
#   year  plants  quantity (MMBtu)  q-wt delivered   Henry Hub   basis
#   2023      26       646,487,128          3.0288      2.5357  +0.4931
#   2024      27       650,711,973          2.8320      2.1925  +0.6395
#   2025      27       641,283,196          4.1829      3.5289  +0.6540
#
# PRECISION IS THE FAMILY CONVENTION, FIXED BEFORE THE SOLVE AND NOT
# SELECTABLE BY A RESULT (rule 1 [R-STRUCT]): every row of
# ``GAS_BASIS_DIFFERENTIAL`` is 2dp, and SOCO-20's comment publishes this
# derivation's own output at 2dp. A rule-23 re-derivation reproduces the SAME
# construction at the SAME precision and changes only the year it is keyed by.
# The 4dp values are recorded above for the record. A consequence, declared
# here rather than discovered later: at 2dp the 2024 value is UNCHANGED
# (0.6395 -> 0.64 -> 0.64), so an armed 2024 solve is predicted byte-identical
# to an unarmed one.
#
# ZERO FREE PARAMETERS (rules 21 [R-DOF] / 24 [R-REGISTRY]). Each value is a
# measurement of committed source data, not a fitted quantity; the DOF ledger
# carries them with that identification source. Rule 13 [R-MEASURED]: the same
# quantity is producible for a forward year from that year's own receipts and
# responds to changed conditions, and where no receipts exist the scalar
# forward basis is used unchanged — so this is a measured INPUT, never an
# outcome fed back.
#
# Rule 25 [R-ISO-SCOPE]: SOCO's derivation is SOCO's. No other ISO has a row
# here, and a peer lane that wants one derives it from its OWN receipts.
GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR: dict[str, dict[int, float]] = {
    "SOCO": {
        2023: 0.49,
        2024: 0.64,
        2025: 0.65,
    },
}

# CAISO citygate -> burner-tip transport adder ($/MMBtu). The CAISO gas-hub
# overlay (gas_hub_basis_overlay) reprices each gas unit at the measured SoCal /
# PG&E Citygate spot (EIA N3050CA3 - Henry Hub, data/raw/gas_basis_by_iso_month.csv).
# That citygate is the price where the interstate pipe hands to the CA LDC; a
# power plant deep in the SoCalGas / PG&E system pays the citygate PLUS the LDC
# intrastate backbone + local transmission to its burner tip, so the plant's true
# delivered fuel cost (the cost-based DEB bid in CAISO's mitigated market) is the
# citygate + that transport. The adder is the MEASURED differential between the
# two EIA series: CA delivered-to-electric-power (N3045CA3, 2024 annual $3.98/Mcf
# = $3.84/MMBtu) minus the CA citygate (N3050CA3, 2024 $3.38/MMBtu) = +$0.46. It
# is a slow-moving regulated intrastate tariff (held flat across years like the
# basis differentials) and forward-reproducible (rule #11) — NOT tuned to the
# price or interchange residual. Without it the pure citygate under-prices the
# marginal CC to ~the import price and collapses the import knife-edge (the
# discovered caiso-38 under-import); reconciling up to the measured census level
# restores it. Source: EIA N3045CA3 - N3050CA3, 2024 annual.
CAISO_CITYGATE_TRANSPORT_ADDER: float = 0.46

# --- Monthly Gas Price Seasonality Factors ---
# Source: EIA Henry Hub spot price monthly averages, 2019-2024 (excluding
#   anomalous Feb 2021 Uri event and Jan 2026 spike).
# Computed as avg monthly price / annual avg price for each year, then
#   averaged across years. Captures the winter heating premium and
#   shoulder-season discount. Applied as multiplicative factors to the
#   annual trajectory price. Sum of factors / 12 = 1.0 (budget-neutral).
GAS_MONTHLY_SEASONALITY: dict[int, float] = {
    1: 1.15,  # January — winter heating demand peak
    2: 1.10,  # February
    3: 1.02,  # March — shoulder
    4: 0.92,  # April — injection season begins
    5: 0.90,  # May
    6: 0.93,  # June — cooling demand starts
    7: 0.95,  # July
    8: 0.95,  # August
    9: 0.90,  # September — low demand
    10: 0.95,  # October — pre-winter
    11: 1.05,  # November — heating season starts
    12: 1.18,  # December — winter peak
}

# Base delivered coal prices ($/MMBtu) by ISO.
# Source: EIA AEO 2024.
COAL_PRICE_BASE: dict[str, float] = {
    "ERCOT": 2.0,  # EIA AEO 2024 — delivered coal price
    "CAISO": 2.5,  # EIA AEO 2024 — delivered coal price
    "PJM": 2.3,  # Central/Northern Appalachian bituminous + PRB-by-rail
    #   delivered blend. Source: EIA AEO 2024 delivered coal price; refined
    #   per-plant by the EIA-923 monthly fuel-cost overlay where reported.
    "NYISO": 2.3,  # NY's grid coal fleet is retired (Somerset/Cayuga, 2020),
    #   so no unit prices off this in a 2023+ backcast; carried as a defensive
    #   Appalachian-delivered fallback (≈ PJM) for any residual/legacy coal
    #   unit. Source: EIA AEO 2024 delivered coal price.
    "NEISO": 3.0,  # New England's only coal in the backcast window is
    #   Merrimack Station (NH, ~440 MW bituminous-by-rail, ~5% CF,
    #   deactivated Jun-2025). Its delivered cost is confidential (no
    #   EIA-923 Schedule-5 receipts; EIA state tables suppress NH coal), so
    #   this is the PJM bituminous blend (2.3) plus a rail-into-New-England
    #   premium — a Tier-3 placeholder that only prices a near-idle peaking
    #   coal unit. Refine in NEISO calibration (doc-08 P11/P12) if Merrimack
    #   dispatch is visibly mis-leveled.
    "MISO": 1.9,  # MISO's coal fleet burns a Powder River Basin sub-bituminous
    #   (rail-delivered to the upper-Midwest North/Central) + Illinois Basin
    #   bituminous blend, delivered cheaper than Appalachian (PRB minemouth is
    #   low-cost; ILB is local to the footprint). EIA AEO 2024 delivered coal
    #   price, PRB+ILB blend; refined per-plant by the EIA-923 monthly
    #   fuel-cost overlay where reported (MISO has full CEMS/EIA-923 coverage).
    "NWPP": 2.9,  # NWPP (registered 2026-09-14, lane NWPP-20): MEASURED, not
    #   AEO — the EIA-923 quantity-weighted delivered mean over the eight
    #   footprint coal plants with Schedule-2 receipts is $2.612 (2023) /
    #   $2.855 (2024) / $2.816 (2025) per MMBtu (data/raw/_processed-legacy/
    #   eia923_monthly_fuel_costs.parquet on the WECC-admitted footprint;
    #   PRECOMMIT-nwpp-20 §3.7), and 2.9 is the 2024 value, the same year
    #   the peer rows' "AEO 2024" anchors. The basin split is BIMODAL and
    #   legible in the price (FINDING-nwpp-12 §2.5): PRB rail-delivered Dave
    #   Johnston 1.19 / Wyodak 1.38; Green River-Kemmerer Naughton 2.59 /
    #   Jim Bridger 3.25; Uinta Bonanza 3.02 / Hunter 3.32 / Huntington 3.44;
    #   rail-delivered North Valmy 4.95 — a per-state coal price is wrong
    #   here and coal must be priced per plant. THE GAP, stated: Colstrip
    #   (1,647.4 MW, ~9-11 TWh/yr), Centralia, TS Power and Hardin — 2,911.7
    #   MW, 32.7 % of footprint coal and the ENTIRE coal fleet of zones
    #   INLAND and NW — carry ZERO receipts (mine-mouth / captive-mine), so
    #   this scalar is their only price until NWPP-12's routed follow-up
    #   (NorthWestern 2026 MT IRP Figure 61, an image) is transcribed.
    "SPP": 1.8,  # SPP's coal fleet (20.3 GW nameplate, 29 plants — KS/NE/OK/
    #   MO/TX/ND) burns rail-delivered Powder River Basin sub-bituminous:
    #   MEASURED, not AEO — the EIA-923 SWPP plant-weighted delivered mean is
    #   $1.919 (2023) / $1.810 (2024) / $1.786 (2025) per MMBtu over 30 / 29 /
    #   27 reporting plants (data/raw/_processed-legacy/eia923_monthly_fuel_
    #   costs.parquet; docs/multi-iso/spp-data-audit.md §5 row 9), and 1.8 is
    #   the 2024 value, the same year the peer rows' "AEO 2024" anchors. Mine-
    #   mouth PRB 8,800 Btu/lb was $0.78 (2024) -> $0.81 (2025) per the SPP
    #   MMU (SOM 2025 §4, PDF p. 131). Refined per-plant by the EIA-923
    #   monthly fuel-cost overlay where reported. Registered 2026-09-06 (SPP-20).
    "SOCO": 3.2,  # SOCO's coal fleet (6 plants / 12,234.7 MW, docs/multi-iso/
    #   soco-data-audit.md §2.2) is a BIT + SUB split: Barry, Gaston (AL) and
    #   Bowen (GA) burn bituminous (Energy Source 1 = BIT, 5,643.1 MW); Miller
    #   (AL), Daniel (MS) and Scherer (GA) burn rail-delivered Powder River
    #   Basin sub-bituminous (SUB, 6,591.6 MW). MEASURED, not AEO — the EIA-923
    #   SOCO plant-weighted delivered mean is $3.548 (2023) / $3.168 (2024) /
    #   $2.928 (2025) per MMBtu over 6 / 6 / 5 reporting plants (data/raw/
    #   _processed-legacy/eia923_monthly_fuel_costs.parquet, plants by EIA-860
    #   BA code SOCO), and 3.2 is the 2024 value, the year the peer rows'
    #   "AEO 2024" anchors. The Southeast's delivered coal is dear relative to
    #   the Plains (SPP 1.8) because the bituminous half is CAPP/ILB rail
    #   into Alabama and Georgia. Refined per-plant by the EIA-923 monthly
    #   fuel-cost overlay where reported. Registered 2026-09-14 (SOCO-20).
}

# Annual real escalation rate for coal prices — retained as the DEFAULT
# forward shape only where no AEO year is available (before START_YEAR, or a
# horizon extension beyond COAL_PRICE_TRAJECTORIES' last year is handled by
# the flat hold, not this rate). Reflects mine closures, rising rail transport
# costs, and declining domestic demand reducing economies of scale.
# Source: EIA AEO 2024 coal supply module — ~1% real escalation.
COAL_PRICE_ESCALATION: float = 0.01

# --- National delivered coal-price trajectories (real 2025$/MMBtu) ---
# AEO2026 Table 15 ("Coal Supply, Disposition, and Prices"), delivered to the
# electric power sector, national ("usa") — data/raw/eia-aeo/
# eia_aeo2026_fuel_prices.csv, derived via
# scripts/data/derive_fuel_trajectories.py::derive_coal_trajectory (FF-G2,
# CLAUDE.md rule 23 — the AEO2025->AEO2026 vintage bump; the original P-1D
# grounding resolved the D2 "coal flat 1%/yr" gap). Consumed as a dollar-year-
# invariant RATIO to each ISO's own COAL_PRICE_BASE anchor
# (data.fuel.resolve_annual_coal_price), so the 2024$->2025$ basis change does
# NOT shift any delivered coal price — only the AEO's real forward shape does.
# The first-knot (anchor) year is now 2025 (AEO2026 starts 2025; AEO2025 started
# 2024): the ratio renormalizes to trajectory[2025], a ~1-2% reanchoring the
# FF-G2 methodology doc's delta ledger records. FORECAST-ONLY (backcast coal
# uses the flat COAL_PRICE_ESCALATION fallback / F923 measured receipts, see
# data.fuel.resolve_fuel_prices), so this whole table is safe to re-vintage
# without touching any backcast surface. Replaces the flat forward SHAPE — each
# ISO's own COAL_PRICE_BASE level anchor is unchanged (a single national
# series can't resolve ERCOT lignite vs PJM Appalachian vs MISO PRB+ILB basin
# economics, the CLAUDE.md rule-14 misalignment exception), but the year-over-
# year real growth now tracks the AEO's modeled coal-supply dynamics instead
# of a guessed constant rate. Scenario mapping matches
# HENRY_HUB_TRAJECTORIES: highogs -> "low", ref2025 -> "mid", lowogs -> "high"
# (AEO's High/Low Oil and Gas Supply cases also vary coal-sector fuel
# competition and mining diesel costs, so the same axis is reused rather than
# inventing an independent coal scenario lever). Selected via
# ``ScenarioConfig.coal_price_path`` (default "mid").
COAL_PRICE_TRAJECTORIES: dict[str, dict[int, float]] = {
    "low": {
        2025: 2.5603,
        2026: 2.4991,
        2027: 2.3822,
        2028: 2.3469,
        2029: 2.3561,
        2030: 2.4065,
        2031: 2.3716,
        2032: 2.545,
        2033: 2.5479,
        2034: 2.5407,
        2035: 2.5311,
        2036: 2.5321,
        2037: 2.5249,
        2038: 2.5206,
        2039: 2.6232,
        2040: 2.6145,
        2041: 2.6034,
        2042: 2.618,
        2043: 2.6453,
        2044: 2.4385,
        2045: 2.3742,
        2046: 2.3735,
        2047: 2.3688,
        2048: 2.3729,
        2049: 2.3932,
        2050: 2.4005,
    },
    "mid": {
        2025: 2.5613,
        2026: 2.5155,
        2027: 2.4765,
        2028: 2.4618,
        2029: 2.483,
        2030: 2.4728,
        2031: 2.4416,
        2032: 2.4798,
        2033: 2.4986,
        2034: 2.4866,
        2035: 2.4794,
        2036: 2.4787,
        2037: 2.5029,
        2038: 2.513,
        2039: 2.5717,
        2040: 2.564,
        2041: 2.557,
        2042: 2.5755,
        2043: 2.575,
        2044: 2.4629,
        2045: 2.3251,
        2046: 2.238,
        2047: 2.4198,
        2048: 2.4233,
        2049: 2.4511,
        2050: 2.4621,
    },
    "high": {
        2025: 2.558,
        2026: 2.509,
        2027: 2.5561,
        2028: 2.5843,
        2029: 2.6078,
        2030: 2.5706,
        2031: 2.5157,
        2032: 2.6296,
        2033: 2.6447,
        2034: 2.6671,
        2035: 2.6802,
        2036: 2.6955,
        2037: 2.7131,
        2038: 2.714,
        2039: 2.7169,
        2040: 2.7087,
        2041: 2.7053,
        2042: 2.7046,
        2043: 2.6855,
        2044: 2.7028,
        2045: 2.6968,
        2046: 2.704,
        2047: 2.6961,
        2048: 2.7003,
        2049: 2.7017,
        2050: 2.716,
    },
}

# --- ERCOT lignite / PRB delivered coal cost, 2023-2025 -----------------------
# ERCOT's two coal supply classes are genuinely different costs: mine-mouth
# lignite (no transport, take-or-pay contract) vs PRB-by-rail (commodity +
# rail freight). Both are measured delivered-fuel-cost inputs — a physical/
# market input admissible under CLAUDE.md rule #13 (forward-reproducible,
# responds to changed conditions), not a fitted/residual value, despite the
# unhelpful "calibration" naming these constants used to carry.
#
# Mine-mouth lignite: held flat 2023-2025 (no transport cost to escalate),
# then compounds at COAL_PRICE_ESCALATION from 2026. Source: operator/EIA cost
# data.
LIGNITE_PRICE_2023_25: float = 1.45
# PRB-by-rail: measured delivered cost, 2023-2025 (EIA-923 Schedule-5 receipts
# / operator cost data). From 2026 the forward curve decomposes the 2023-2025
# average into commodity (42%), diesel-driven rail freight (12%, held flat —
# the model carries no forward diesel price curve) and non-diesel rail
# freight (46%, escalates at COAL_PRICE_ESCALATION); the commodity component
# holds flat through 2030 then declines 1.5%/yr as coal demand falls.
PRB_PRICE_BY_YEAR: dict[int, float] = {2023: 2.15, 2024: 2.00, 2025: 2.00}
PRB_COMMODITY_SHARE: float = 0.42
PRB_RAIL_DIESEL_SHARE: float = 0.12
PRB_RAIL_NONDIESEL_SHARE: float = 0.46
PRB_COMMODITY_DECLINE: float = 0.015  # annual, from 2031 as demand falls
PRB_COMMODITY_FLAT_THROUGH: int = 2030

# --- Coal-vs-gas passthrough sigmoid re-derivation inputs ---------------------
# Physical/measured inputs that ``scripts/data/derive_coal_sigmoid.py`` reads to
# re-derive the per-(ISO, supply) gas-keyed coal passthrough sigmoid
# (``COAL_SIGMOID_DEFAULTS`` in scenarios.py) from the EIA Annual Coal Report
# region f.o.b.-mine price + BLS PPI coal-mining series intaked in #1803
# (data/raw/coal-prices/, docs/handoffs/coal-price-data-intake-2026-07.md).
# These are grounded commodity/heat/transport facts — NOT tuned to any ISO's
# price/volume residual (CLAUDE.md rules 10/11/23). See the derive script's
# module docstring for how each feeds the floor/ceil/gas_mid/gas_slope fit.
#
# Approximate heat content of coal by rank (MMBtu per short ton). Converts the
# ACR f.o.b. $/ton price to $/MMBtu so it is comparable to gas.
# Source: EIA Monthly Energy Review, Appendix A5, "Approximate Heat Content of
# Coal and Coal Coke" (production-basis average heat contents).
COAL_HEAT_CONTENT_MMBTU_PER_TON: dict[str, float] = {
    "BIT": 24.93,  # bituminous
    "SUB": 17.46,  # subbituminous (PRB)
    "LIG": 13.30,  # lignite
    "ANT": 25.09,  # anthracite (not in any modeled fleet; completeness)
}

# Delivered-cost commodity share by delivery mode: the fraction of a coal
# plant's DELIVERED $/MMBtu that is the mine-gate (f.o.b.) commodity, the
# remainder being rail/transport. Used to lift the ACR f.o.b. price to a
# delivered cost comparable to the model's ``COAL_PRICE_BASE`` (delivered =
# f.o.b. / commodity_share). PRB-by-rail reuses the cited PRB decomposition
# (:data:`PRB_COMMODITY_SHARE`, 0.42 — long-haul rail dominates delivered
# cost). Mine-mouth lignite is ~all commodity (no rail). Interior/Appalachian
# bituminous railed short-haul into the MISO/PJM footprint carries a much
# smaller freight fraction than long-haul PRB.
# Source: EIA Coal Transportation Rates to the Electric Power Sector (rail
# freight as a share of delivered cost: ~55-60% for long-haul PRB, ~15% for
# short-haul Interior/Appalachian bituminous); mine-mouth lignite ~0.
COAL_DELIVERY_COMMODITY_SHARE: dict[str, float] = {
    "prb": PRB_COMMODITY_SHARE,  # 0.42, long-haul rail
    "subbituminous": PRB_COMMODITY_SHARE,  # same basin economics as prb
    "bituminous": 0.85,  # short-haul Interior/Appalachian rail
    "lignite": 1.00,  # mine-mouth, no transport
    "waste": 1.00,  # reclamation fuel, near-mine
}

# Representative heat rates (MMBtu/MWh) for locating the coal-vs-gas-CC merit
# crossover in gas-price space (``gas_mid``): the gas price at which a gas-CC's
# fuel cost equals the coal plant's fuel cost is
# ``gas_mid = coal_delivered$/MMBtu x COAL_HR / CC_HR``. Representative EIA
# Table 8 tested heat rates (subcritical steam coal; F-class combined cycle) —
# the class-typical values, not per-plant (the LP still prices each unit at its
# own heat rate; these only place the crossover the sigmoid centers on).
COAL_SIGMOID_REP_HR_COAL: float = 10.0  # HEAT_RATE_BINS["coal"]["subcritical"]
COAL_SIGMOID_REP_HR_GAS_CC: float = 6.7  # HEAT_RATE_BINS["gas_cc"]["f_class"]

# Minimum delivered gas price ($/MMBtu) observed over the backcast window
# (2023-2025), per ISO — the cheapest-gas anchor for the sigmoid floor: coal's
# deepest bid discount is the fraction that pulls it to merit-order parity with
# the cheapest gas it competes against (``floor = gas_min / gas_mid``). A
# market fact (the observed gas trough), not a residual.
# Source: EIA-923 Schedule-5 delivered gas cost to each ISO's gas fleet, 2024
# (the cheapest of 2023-2025); Henry Hub 2024 ~$2.19 + small regional basis.
COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU: dict[str, float] = {
    "ERCOT": 2.00,
    "MISO": 2.19,
    "PJM": 2.86,  # +0.67 EIA-923 delivered basis (GAS_BASIS_DIFFERENTIAL)
    "CAISO": 3.40,
    "NYISO": 2.74,
    "NEISO": 3.29,
    # SPP: the Panhandle Eastern 2024 annual average, $1.98/MMBtu — the
    # cheapest delivered-gas year of 2023-2025 at SPP's own reference hub
    # (2023 $2.16, 2025 $2.97-2.98; SPP MMU SOM 2025 §4, report p. 119 /
    # PDF p. 131; the SOM 2025 restatement of SOM 2024's $1.81 is used —
    # docs/multi-iso/spp-data-audit.md §5 row 8). Equivalent to the table's
    # construction HH 2024 + basis (2.19 - 0.26 = 1.93) within the two
    # publications' HH rounding. Registered 2026-09-06 (SPP-20).
    "SPP": 1.98,
    # NWPP (registered 2026-09-14, lane NWPP-20): the Sumas 2024 annual mean,
    # $2.00/MMBtu — the cheapest full year of 2023-2025 at the footprint's
    # own reference hub (2023 $4.80 across the January Pacific-Northwest
    # price spike; 2025 partial-year mean $1.98 over 31 prints, not a full
    # year; data/raw/gas-prices/sumas_weekly.csv). Equivalent to the table's
    # construction HH 2024 + basis (2.19 - 0.19 = 2.00) exactly. The EIA-923
    # quantity-weighted delivered gas to the footprint's plants reads $2.82
    # in 2024 — the burner-tip figure, which the sigmoid compares against
    # the coal plant's own delivered cost on a hub basis, so the hub value is
    # the like-for-like anchor (PRECOMMIT-nwpp-20 §3.7).
    "NWPP": 2.00,
    # SOCO: the cheapest delivered-gas year of 2023-2025 at the SOCO fleet's
    # own burner tip — the EIA-923 Schedule-5 quantity-weighted delivered cost
    # to SOCO's gas plants, 2024: $2.832/MMBtu (2023 $3.029, 2025 $4.183;
    # GAS_BASIS_DIFFERENTIAL["SOCO"] derivation) — the table's own
    # construction HH 2024 + basis = 2.19 + 0.64 = 2.83. SOCO has no traded
    # hub of its own (SONAT / Transco Zone 4 dailies are paywalled, SOCO-12
    # §4), so the plant-delivered receipts ARE the measured series here, as
    # for PJM / NYISO / NEISO above. Registered 2026-09-14 (SOCO-20).
    "SOCO": 2.83,
}

# Baseline logistic slope (per $/MMBtu) for a coal supply group whose plants
# all draw one producing region, so the annual region f.o.b. resolves no
# cross-plant crossover dispersion (e.g. MISO's all-PRB group). The physical
# crossover-sharpness prior at the mechanism's established scale; a multi-region
# group (e.g. MISO bituminous spanning IL/IN/KY/ENC) instead derives its slope
# from the real across-region delivered-cost dispersion. Clipped to
# [SLOPE_MIN, SLOPE_MAX]. PPI intra-year variability adds a (small, ~2% CV)
# fuzzing term to the dispersion.
COAL_SIGMOID_BASELINE_SLOPE: float = 2.5
COAL_SIGMOID_SLOPE_MIN: float = 1.0
COAL_SIGMOID_SLOPE_MAX: float = 4.0

# Lowest the sigmoid floor may go: a coal plant never bids below this fraction
# of full delivered fuel cost. Bounds the cheap-gas discount so the floor stays
# a merit-order discount, not an unbounded giveaway (the sunk take-or-pay
# tonnage is a SEPARATE mechanism, coal_takeorpay_from_data).
COAL_SIGMOID_FLOOR_MIN: float = 0.50

# Follower-tier (low-must-run PRB cyclers, mustrun <= coal_prb_follower_mustrun_max)
# deepen their cheap-gas discount vs the baseload PRB tier: a cycler bids nearer
# its avoidable cost. Applied as a multiplicative discount on the baseload
# floor/ceil. Matches the established baseload->follower ordering (follower
# floor/ceil below baseload).
COAL_SIGMOID_FOLLOWER_DISCOUNT: float = 0.87

# Delivered oil fuel price ($/MMBtu) for oil-fired peakers and steam units.
# Distillate (No. 2) fuel oil dominates the NYISO/ISO-NE oil peaker fleet;
# residual (No. 6) is the legacy oil-steam fuel. The blended delivered cost
# sits far above gas, so oil clears only in scarcity (peaker behaviour) —
# critical to Northeast winter price formation. Held flat (no commodity
# trajectory) since oil rarely runs and is not a price-setting baseload fuel.
# Source: EIA distillate (~$20/MMBtu) and residual (~$14/MMBtu) fuel oil
# delivered to the electric power sector, 2023-2024 average.
# Also the dual-fuel switching parity fallback: in backcast years the measured
# EIA-923 Schedule 5 monthly Petroleum receipt series
# (market_sim.data.fuel.iso_monthly_oil_prices; PJM ~$17-23/MMBtu, 2023-2025)
# takes precedence, and this flat value fills unreported months and any
# forecast year outside OIL_PRICE_TRAJECTORIES' range.
OIL_PRICE_PER_MMBTU: float = 18.0

# --- Forecast-year oil-price trajectories (real 2025$/MMBtu) ---
# AEO2026 Table 12 ("Petroleum and Other Liquids Prices"), electric-power
# distillate + residual fuel oil, averaged (same blend construction as
# OIL_PRICE_PER_MMBTU above) — data/raw/eia-aeo/
# eia_aeo2026_fuel_prices.csv, derived via
# scripts/data/derive_fuel_trajectories.py::derive_oil_trajectory (FF-G2,
# CLAUDE.md rule 23 — the AEO2025->AEO2026 vintage bump). AEO prices this
# series at $/gal; converted to $/MMBtu via EIA fuel heat contents
# (0.1385 MMBtu/gal distillate, 0.1497 MMBtu/gal residual). Now in real 2025$
# (AEO2025 was 2024$) and starting at 2025 (AEO2026's first year; AEO2025
# started 2024). FORECAST-ONLY: replaces the flat OIL_PRICE_PER_MMBTU scalar for
# forecast years (backcast months keep the measured EIA-923 receipt series;
# OIL_PRICE_PER_MMBTU stays the fallback for unreported backcast months and any
# year outside this table's range) — so it never touches a backcast surface.
# Oil rarely sets price (peaker economics), so the vintage change is
# second-order. Selected via ``ScenarioConfig.oil_price_path`` (default "mid");
# scenario mapping matches HENRY_HUB_TRAJECTORIES (highogs -> "low",
# cb2026 -> "mid", lowogs -> "high").
OIL_PRICE_TRAJECTORIES: dict[str, dict[int, float]] = {
    "low": {
        2025: 20.64,
        2026: 17.19,
        2027: 17.77,
        2028: 17.83,
        2029: 17.49,
        2030: 16.96,
        2031: 16.16,
        2032: 16.39,
        2033: 16.71,
        2034: 16.82,
        2035: 16.89,
        2036: 16.9,
        2037: 16.98,
        2038: 16.9,
        2039: 16.9,
        2040: 17.01,
        2041: 17.04,
        2042: 16.99,
        2043: 16.77,
        2044: 16.64,
        2045: 16.3,
        2046: 16.42,
        2047: 16.46,
        2048: 16.61,
        2049: 16.77,
        2050: 16.82,
    },
    "mid": {
        2025: 20.64,
        2026: 17.53,
        2027: 17.98,
        2028: 18.09,
        2029: 18.06,
        2030: 17.78,
        2031: 17.1,
        2032: 17.43,
        2033: 17.69,
        2034: 18.11,
        2035: 18.21,
        2036: 18.31,
        2037: 18.53,
        2038: 18.59,
        2039: 18.76,
        2040: 18.95,
        2041: 19.08,
        2042: 19.08,
        2043: 19.02,
        2044: 18.89,
        2045: 18.68,
        2046: 18.93,
        2047: 19.19,
        2048: 19.4,
        2049: 19.61,
        2050: 19.82,
    },
    "high": {
        2025: 20.64,
        2026: 17.84,
        2027: 18.82,
        2028: 18.78,
        2029: 18.65,
        2030: 18.38,
        2031: 17.93,
        2032: 17.91,
        2033: 18.76,
        2034: 19.1,
        2035: 19.41,
        2036: 19.73,
        2037: 20.06,
        2038: 20.29,
        2039: 20.64,
        2040: 20.89,
        2041: 21.11,
        2042: 21.23,
        2043: 21.24,
        2044: 21.11,
        2045: 20.76,
        2046: 21.01,
        2047: 21.29,
        2048: 21.56,
        2049: 21.83,
        2050: 22.08,
    },
}

# NOTE: AGT_DAILY_BASIS_CONVEXITY (the within-month NEISO daily-AGT-basis
# demand-convexity exponent, formerly 7.0) was RETIRED 2026-06. It redistributed
# the measured monthly AGT basis across a month's days proportional to NEISO
# demand raised to the exponent, with the exponent *chosen so the resulting
# gas->oil switching tracked the measured EIA-930 oil burn* — i.e. a within-month
# shape fitted to the electricity/oil outcome, which violates the measured-input
# rule (CLAUDE.md #12: never tune an input to the residual it is validated
# against). It is replaced by a real-data construction in
# market_sim.data.fuel.iso_hub_daily_gas_prices: the within-month AGT basis is
# anchored to the real Algonquin Citygate daily spot prints EIA publishes in its
# Weekly Update narrative (data/raw/gas-prices/algonquin_citygate_daily.csv,
# scripts/data/fetch_algonquin_daily_spot.py), interpolated on their true calendar
# days and mean-preserved to the measured monthly basis; sparse-print months
# borrow the measured Transco Z6 NY daily-basis shape (AGT~=Transco basis, slope
# ~0.95). Every driver is now free, EIA-sourced, forward-applicable gas-market
# data with no electricity/oil tuning. See docs/multi-iso/neiso-data-audit.md §2c.

# Delivered biomass fuel price ($/MMBtu) for wood/MSW/landfill-gas units.
# Biomass fuel is largely a low-cost waste/byproduct stream (mill residue,
# refuse, landfill gas), so its delivered cost is well below oil and roughly
# at parity with cheap coal on a $/MMBtu basis.
# Source: EIA wood & waste biomass delivered fuel cost, AEO 2024 (~$2.5/MMBtu).
BIOMASS_PRICE_PER_MMBTU: float = 2.5

# --- Nuclear fuel price ($/MMBtu, real 2024$) ---
# D2 fix (P-1D, CLAUDE.md rule 23): nuclear was priced at $0/MMBtu alongside
# wind/solar/hydro (fuel.py's non-fuel-burning default), but nuclear plants do
# burn a real, priced fuel. The EIA Uranium Marketing Annual Report publishes
# no $/MMBtu series directly (data/raw/uranium-marketing/, P-0C intake) — only
# front-end U3O8 purchase price ($/lb U3O8e) and SWU enrichment-services
# price, both nominal. This series is derived
# (scripts/data/derive_fuel_trajectories.py::derive_nuclear_fuel_trajectory) by
# deflating both to real 2024$ (INFLATION_RATE) and building up a delivered
# $/MMBtu cost from the standard LWR fuel-cycle physical constants (World
# Nuclear Association "Nuclear Fuel Cycle": ~8.9 kg natural U3O8 and ~7.3 SWU
# per kg of ~4.4% LEU at a 0.25-0.3% tails assay) plus WNA-cited conversion
# (~$10/kgU) and fabrication (~$300/kgLEU) costs — neither published as a time
# series by EIA, so held flat in real terms — divided by the heat content of
# a representative 45,000 MWd/tHM US LWR burnup (NRC/EIA-cited current-fleet
# average). 2006 is the first year with both a U3O8 and a SWU price (SWU
# series starts there); years without both are not derived (no guessing).
# Forecast years (2025-2050) hold the last derived value (2024: $0.576/MMBtu)
# flat in real terms — neither EIA nor AEO publishes a forward SWU/U3O8
# trajectory, so a hold-flat real anchor is the documented, non-speculative
# default (same "no silent compounding tail" principle as the
# fuel.resolve_annual_gas_price extrapolation fix). ScenarioConfig-overridable
# via ``nuclear_fuel_price_override`` ($/MMBtu, e.g. for a sensitivity case).
NUCLEAR_FUEL_PRICE_HISTORICAL: dict[int, float] = {
    2006: 0.5608,
    2007: 0.6831,
    2008: 0.7884,
    2009: 0.7994,
    2010: 0.8235,
    2011: 0.8528,
    2012: 0.8456,
    2013: 0.8115,
    2014: 0.7540,
    2015: 0.7175,
    2016: 0.6796,
    2017: 0.6318,
    2018: 0.5979,
    2019: 0.5551,
    2020: 0.5102,
    2021: 0.5051,
    2022: 0.5283,
    2023: 0.5568,
    2024: 0.5760,
}

# Thermal-fleet availability model by plant-group category. Three additive
# components (summed, not compounded):
#  * POF   — planned outage factor; applied only in the shoulder months.
#  * WEFOR — weighted equivalent forced outage rate; flat year-round, and
#            escalates linearly with plant age past an onset year.
#  * DERATE — weather + performance-decline capacity loss; flat year-round,
#            and likewise escalates with age past an onset year.
# A unit's availability is 1 - WEFOR(age) - DERATE(age) - POF(shoulder only),
# where WEFOR(age) = base + max(0, age - onset) * rate (and likewise DERATE).
# Each entry is (POF, WEFOR_base, WEFOR_rate, WEFOR_onset, DERATE_base,
# DERATE_rate, DERATE_onset). Source: NERC GADS by unit type and age.
THERMAL_AVAILABILITY: dict[str, tuple[float, ...]] = {
    "CC_CHP": (0.05, 0.04, 0.002, 20, 0.02, 0.001, 25),
    "CC_REGULAR": (0.05, 0.05, 0.002, 20, 0.02, 0.001, 25),
    "CT_CHP": (0.03, 0.05, 0.002, 20, 0.03, 0.001, 20),
    "CT_PEAKER": (0.03, 0.07, 0.003, 20, 0.05, 0.002, 20),
    "ST_GAS": (0.06, 0.21, 0.003, 30, 0.04, 0.002, 30),
    "ST_CHP": (0.05, 0.08, 0.002, 25, 0.03, 0.0015, 25),
    # Coal subclasses carry the deleted bare ``COAL`` key's GADS tuple
    # (COAL-SUB, owner instruction 2026-09-25).
    "COAL_LIGNITE": (0.07, 0.12, 0.005, 40, 0.03, 0.002, 35),
    "COAL_PRB": (0.07, 0.12, 0.005, 40, 0.03, 0.002, 35),
    "COAL_BIT": (0.07, 0.12, 0.005, 40, 0.03, 0.002, 35),
    "COAL_WC": (0.07, 0.12, 0.005, 40, 0.03, 0.002, 35),
    # Oil and biomass entries apply when a unit carries a matching plant-group
    # tag; EIA-classified oil/biomass units (no plant_group) fall back to the
    # flat 1 - EFORD derate. Source: NERC GADS by unit type and age.
    "OIL": (0.06, 0.10, 0.003, 30, 0.04, 0.002, 30),
    "BIOMASS": (0.07, 0.10, 0.002, 25, 0.04, 0.0015, 25),
}

# Fraction of a unit's WEFOR (forced-outage rate, from THERMAL_AVAILABILITY
# above) that applies during the summer peak; the remaining (1 - share) is
# redistributed into the shoulder months, conserving the annual outage energy.
# Winter keeps the flat WEFOR. Applied in
# ``data.fleet.arrays._apply_thermal_availability``.
#
# SOURCE: NONE — this is an UNCITED A-PRIORI HEURISTIC, declared as such rather
# than given a false provenance (CLAUDE.md rule 5 [R-NO-MAGIC]). It is the
# "flat per-plant-group POF heuristic" market-sim-build-plan.md records as
# awaiting a data-derived replacement. It was NOT fitted to any residual; no
# derivation, sweep or calibration lineage exists for the 0.30. It is declared
# in the MISO keeper's DOF ledger under identification ``residual`` — the
# strictest existing enforcement category, which forces an open root cause
# (audit_keepers.py E8) — NOT because it was tuned.
#
# It is re-homed here from ``data/fleet/arrays.py`` (miso-91, 2026-07-26) so
# that ``scripts/validate_parameters.py`` covers it: that gate scans only
# ``vars(constants)`` + ``ScenarioConfig`` defaults and skips private/
# non-uppercase names, so a private literal in a ``data/`` module was invisible
# to it three ways over — which is why it went uncited for so long
# (CLAUDE.md rule 20 [R-REGISTRY]).
#
# PHYSICS TENSION, recorded deliberately: for PLANNED outages, shifting
# maintenance away from the peak is well-founded (and the POF side is separately
# grounded by the measured MAINTENANCE_MONTHLY_SHAPE). For FORCED outages this
# reallocation runs OPPOSITE to the physics — forced outages correlate
# POSITIVELY with heat and high load. A share < 1 therefore encodes a
# forced-outage seasonality whose sign is the reverse of the expected physical
# one. Stated as an unverified directional argument, not a citation.
#
# DO NOT re-tune this value against a residual (rule 24 [R-ANSWER-KEY]): it
# governs ~3.9-5.8 GW of MISO summer-peak capability across all six non-coal
# thermal classes, the same order as the ~10 GW under-derate ledgered as the
# C3b caveat, so a hand-set value here would be an answer key for an
# already-ledgered miss. It may be REPLACED ONLY by a measured seasonal
# forced-outage shape clearing the acceptance test in
# docs/handoffs/miso-outage-grain-data-ask-2026-07.md, and per rule 23
# [R-FROZEN-DERIVE] that commit must cite the data change, never a residual.
#
# THE MEASURED REPLACEMENT EXISTS (miso-160, 2026-08-16), per the owner's
# provenance decision amending that ask at fleet grain (its §9):
# ``ScenarioConfig.summer_wefor_share_override`` carries a per-ISO value
# derived from a published ticket-based outage record — MISO first, R* =
# 1.0599 = the pooled 2023-2025 Jun-Sep/annual ratio of the MISO MOM record's
# unplanned offline MW (Derated+Forced+Unplanned; probe
# scripts/probes/_miso160_wefor_shape_instrument.py). Note the measured sign:
# summer forced-outage rates sit ABOVE annual, the reverse of this 0.30.
# This constant remains the default wherever the override is None; each ISO
# derives its own from its own record (rule 25 [R-ISO-SCOPE]).
SUMMER_WEFOR_SHARE: float = 0.30

# Additional summer (Jun-Sep) capacity derate by plant group, modeling the
# ambient-temperature output loss gas turbines suffer in the heat (worse for
# simple-cycle CTs than combined-cycle). Applied on top of the age-based
# THERMAL_AVAILABILITY model for these classes only; coal and gas steam are
# unaffected.
#
# SOURCE: the physical effect is real and well-established (gas-turbine mass
# flow falls with rising inlet air temperature, and simple-cycle units lose
# more than combined-cycle). The SPECIFIC magnitudes 0.10 / 0.125 are an
# UNCITED FLAT APPROXIMATION of it — consistent with, but not derived from, the
# 10-30% typical CT summer derate the repo's own capacity audit records against
# EIA-860 net-summer ratings (docs/capacity-audit-860-923-campd.md).
#
# A MEASURED per-class dry-bulb temperature curve exists as the
# ``temp_dependent_derate`` alternative to this flat treatment; it is
# default-off, having been probe-refuted for the ERCOT gas fleet (2026-07-09).
# Its MISO sibling ``gt_ambient_derate`` is measured PROVABLY INERT — MISO
# zone-mean TMAX clears its 35 C reference in 0 h at summer peak in any of
# 2023-2025 (FINDING-miso89 §8). So the flat approximation stands as the live
# treatment, and rule 11 [R-ACCURATE]'s "prefer the measured input" is not
# engaged: the measured alternatives were tried and adjudicated, not skipped.
#
# Re-homed here from ``data/fleet/arrays.py`` with SUMMER_WEFOR_SHARE above
# (miso-91), same registry-coverage reason. Values unchanged.
SUMMER_CLASS_DERATE: dict[str, float] = {
    "CC_REGULAR": 0.10,
    "CC_CHP": 0.10,
    "CT_PEAKER": 0.125,
    "CT_CHP": 0.125,
}

# Per-plant ERCOT coal sustained-output ceilings (fraction of capacity_mw):
# the demonstrated physical maximum a unit's CEMS record shows it can sustain
# (boiler/turbine derates below nameplate), applied as an availability ceiling
# year-round on top of the age-based THERMAL_AVAILABILITY model.
#
# Source: scripts/data/derive_coal_max_cf.py — the pooled 99th percentile of each
# plant's daily-max capacity factor (gross_mw / capacity_mw) on days it ran
# (daily-mean CF > 0.06), across all CAMPD hourly extract years on record
# (2023-2025, data/raw/campd-facility-level/TX_*.parquet). A near-maximum
# rather than the true max: robust to a single-hour telemetry spike, not
# softened by economic part-load (which compresses the mean, not the top
# tail). Re-run the script and update this table when a new CAMPD year lands;
# never hand-tune an entry to a backcast residual (CLAUDE.md rule #22).
#
# Plants whose demonstrated ceiling reached or exceeded nameplate (Oak Grove
# 6180 p99=1.02, Coleto Creek 6178 p99=1.10, San Miguel 6183 p99=1.07) carry no
# entry: their own CEMS record shows no sub-nameplate physical limit, so the
# generic age-based availability model governs them unconstrained.
COAL_MAX_CF_BY_PLANT: dict[int, float] = {
    298: 0.95,  # Limestone
    6179: 0.99,  # Fayette (Sam Seymour)
    7097: 0.95,  # J K Spruce
}

# Forecast-mode monthly planned-maintenance shape (12 weights, Jan..Dec) per
# plant group. Replaces the flat shoulder-POF heuristic (POF smeared uniformly
# across _CC_SHOULDER_MONTHS = {3,4,5,10,11}) with the historically-derived
# *timing* of spring/autumn maintenance learned from the CAMPD unit-outage
# extracts (all six ISOs, 2023-2025 pooled — a forecast shape, NOT pinned to any
# one backcast year). Each weight is the planned-maintenance excess over the
# annual-minimum (forced-outage-floor) month, normalized to a month-length-
# weighted mean of 1 (Sum w[m]*hours[m] = 8760). At apply time
# (data.fleet.generators_to_fleet_arrays, FORECAST mode only) the per-hour
# planned-maintenance derate is B_group * w[group][month], where the group's
# annual POF budget B_group = POF * shoulder_hours / 8760 comes from
# THERMAL_AVAILABILITY. Because w has a month-weighted mean of 1, the annual
# planned-outage budget is conserved EXACTLY (Sum maint[m]*hours[m] =
# POF*shoulder_hours) — only its seasonal distribution is sharpened from the
# rigid 5-month block to the measured curve (peaks Apr/Oct-Nov, ~0 in the
# Jul/Aug summer peak, modest in winter). This is methodology spec section 1.7's
# documented forecast roadmap item and is distinct from the backcast historic
# outage overlay (data/outages.py), which is untouched.
# Derivation/verify: scripts/data/derive_maintenance_shape.py (reads the committed
# data/raw/campd-unit-outages*.csv). Groups with too few observations (e.g.
# CT_PEAKER — combustion turbines are excluded from the unit-outage detector)
# fall back to the pooled all-thermal shape "_POOLED".
# The coal shape measured from the CAMPD unit-outage extracts (derived on the
# artifacts' coal-family rows); every coal subclass reads it (COAL-SUB).
_COAL_MAINTENANCE_MONTHLY_SHAPE: tuple[float, ...] = (
    0.239,
    1.125,
    1.757,
    1.923,
    1.559,
    0.568,
    0.000,
    0.174,
    1.003,
    1.442,
    1.481,
    0.772,
)

MAINTENANCE_MONTHLY_SHAPE: dict[str, tuple[float, ...]] = {
    "COAL_LIGNITE": _COAL_MAINTENANCE_MONTHLY_SHAPE,
    "COAL_PRB": _COAL_MAINTENANCE_MONTHLY_SHAPE,
    "COAL_BIT": _COAL_MAINTENANCE_MONTHLY_SHAPE,
    "COAL_WC": _COAL_MAINTENANCE_MONTHLY_SHAPE,
    "CC_REGULAR": (
        0.608,
        0.961,
        1.765,
        2.175,
        1.591,
        0.473,
        0.000,
        0.007,
        0.449,
        1.524,
        1.554,
        0.910,
    ),
    "CC_CHP": (
        0.574,
        0.851,
        1.658,
        2.217,
        1.775,
        0.516,
        0.000,
        0.072,
        0.505,
        1.736,
        1.481,
        0.623,
    ),
    "CT_PEAKER": (
        0.581,
        1.131,
        1.719,
        1.926,
        1.499,
        0.514,
        0.000,
        0.132,
        0.731,
        1.394,
        1.478,
        0.929,
    ),
    "CT_CHP": (
        1.261,
        1.336,
        1.692,
        2.107,
        1.582,
        0.874,
        0.010,
        0.000,
        0.223,
        0.787,
        1.270,
        0.907,
    ),
    "ST_GAS": (
        1.136,
        1.553,
        1.567,
        1.346,
        1.140,
        0.488,
        0.000,
        0.328,
        0.882,
        0.971,
        1.314,
        1.330,
    ),
    "ST_CHP": (
        0.867,
        0.949,
        1.495,
        1.576,
        1.174,
        0.337,
        0.000,
        0.427,
        0.753,
        1.831,
        1.620,
        0.975,
    ),
    # Pooled all-thermal fallback for sparse/excluded groups (e.g. CT_PEAKER).
    "_POOLED": (
        0.581,
        1.131,
        1.719,
        1.926,
        1.499,
        0.514,
        0.000,
        0.132,
        0.731,
        1.394,
        1.478,
        0.929,
    ),
}

# Carbon price trajectories ($/tCO2) by scenario path and year.
# Source: RFF / state programs.
CARBON_PRICE_PATHS: dict[str, dict[int, float]] = {
    "zero": {2026: 0, 2030: 0, 2040: 0, 2050: 0},  # RFF — no carbon price
    "low": {2026: 0, 2030: 8, 2040: 18, 2050: 25},  # RFF — low carbon price path
    "mid": {2026: 0, 2030: 15, 2040: 35, 2050: 50},  # RFF — mid carbon price path
    "high": {2026: 0, 2030: 30, 2040: 70, 2050: 110},  # RFF — high carbon price path
}

# State carbon-program allowance prices ($/tCO2, metric) by ISO and
# calendar year. Each year is the simple average of the four quarterly
# auction clearing prices (both programs clear each auction at one uniform
# price, and quarterly volumes are near-equal, so the simple mean is the
# volume-weighted mean to within cents). Backcasts charge this allowance
# cost on every in-state fossil unit's marginal cost via
# resolve_carbon_price (default-on; see ScenarioConfig.state_carbon_pricing).
#
# CAISO — CA cap-and-trade (CARB), $/metric ton as published.
# Source: CARB "Summary of Auction Settlement Prices and Results" /
#   CA-Quebec joint auction summary results reports (ww2.arb.ca.gov),
#   cross-checked against the WCI auction price history.
#   2022: Feb $29.15, May $30.85, Aug $27.00, Nov $26.80 -> $28.45
#   2023: Feb $27.85, May $30.33, Aug $35.20, Nov $38.73 -> $33.03
#   2024: Feb $41.76, May $37.02, Aug $30.24, Nov $31.91 -> $35.23
#   2025: Feb $29.27, May $25.87 (floor), Aug $28.76, Nov $28.32 -> $28.06
# 2022 ADDED 2026-09-07 (caiso-262, the rule-22 validation touchpoint). SAME
# SOURCE, SAME RECIPE, ZERO FREE PARAMETERS: the four CA-Quebec joint auctions
# of the calendar year (the 30th 2022-02-16, 31st 2022-05-18, 32nd Aug, 33rd
# Nov), current-vintage settlement price as published, simple mean. Each price
# is attributed to its OWN CARB press release (rows in
# data/raw/policy/carbon-auction-results/carbon-auction-results.csv) and was
# cross-checked against EDF Climate 411's independent auction commentary before
# it was written; ww2.arb.ca.gov still blocks automated fetches from this
# environment (403/405/503 on every pattern — the carbon-auction-results raw
# README), so this is the same press-release provenance the 2023-2025 rows
# carry, no stronger and no weaker.
# WHY IT MATTERS, MEASURED: without the row `state_carbon_price` returns None
# and `resolve_carbon_price(CAISO, 2022)` reads **$0.00/tCO2** against
# 33.03/35.23/28.06 in the tuned years — the NYISO-134 D-1 defect, CAISO
# edition. At the CAISO fossil fleet's ~0.41 t/MWh that is ~$11-12/MWh on a
# gas CC and it is MERIT-ORDER distorting, not a level shift, because the
# CC-to-steam rate spread is ~2.9x. A 2022 rung solved without it would be
# running a recipe the keeper was never scored on, silently.
# STILL OPEN, NAMED NOT FIXED: **2019-2021 remain absent**, so those rungs
# still resolve to $0/t. They were NOT added here because the auction-by-
# auction attribution could not be completed from this environment to the
# standard above (the 27th/May-2021 price came back self-contradictory in
# search, and the carbon-auction README's own rule is that no price or metadata
# is ever inferred). That is a data-intake item for the lane that spends the
# 2020/2021 touchpoints, not a modelling question.
# CLOSED 2026-09-24 (i-caiso, the 2019-2021 intake): 2019-2021 ADDED. SAME
# RECIPE, ZERO FREE PARAMETERS — the four CA-Quebec joint auctions of the
# calendar year, Current Auction settlement price (USD) read directly from each
# joint Summary Results Report PDF (hosted by the MELCC at
# environnement.gouv.qc.ca/changements/carbone/ventes-encheres/, reachable where
# ww2.arb.ca.gov is not), simple mean rounded half-up to the cent:
#   2019: #18 Feb $15.73, #19 May $17.45, #20 Aug $17.16, #21 Nov $17.00 -> $16.84
#   2020: #22 Feb $17.87, #23 May $16.68, #24 Aug $16.68, #25 Nov $16.93 -> $17.04
#   2021: #26 Feb $17.80, #27 May $18.80, #28 Aug $23.30, #29 Nov $28.26 -> $22.04
# (the 27th/May-2021 ambiguity named above is resolved by the PDF: $18.80.)
# Per-auction rows + PDF URLs: carbon-auction-results.csv. The recipe was
# verified against the incumbent rows first: recomputing 2022/2023/2024 from
# that CSV reproduces 28.45 / 33.03 / 35.23 exactly.
# NYISO is a RGGI state: every in-state fossil unit surrenders one RGGI CO2
# allowance per (short) ton emitted, so the auction clearing price enters
# marginal cost exactly as the CARB allowance does for CAISO. Each year is the
# simple average of that calendar year's four quarterly RGGI auction current-
# control-period clearing prices (the auctions clear at one uniform price and
# quarterly volumes are near-equal, so the simple mean is the volume-weighted
# mean to the cent). At a ~0.37 tCO2/MWh gas-CC rate this adds ~$5/MWh (2023) to
# ~$8/MWh (2025) — material to the NYISO price level though smaller than CA
# cap-and-trade (doc-07 design decision 4). Source: RGGI, Inc. auction results
# ("CO2 Allowances Sold for $X in the Nth RGGI Auction" press releases,
# rggi.org/auctions/auction-results):
#   2018: A39 (Mar) $3.79,  A40 (Jun) $4.02,  A41 (Sep) $4.50,
#         A42 (Dec) $5.35  -> $4.41
#   2019: A43 (Mar) $5.27,  A44 (Jun) $5.62,  A45 (Sep) $5.20,
#         A46 (Dec) $5.61  -> $5.42
#   2020: A47 (Mar) $5.65,  A48 (Jun) $5.75,  A49 (Sep) $6.82,
#         A50 (Dec) $7.41  -> $6.41
#   2021: A51 (Mar) $7.60,  A52 (Jun) $7.97,  A53 (Sep) $9.30,
#         A54 (Dec) $13.00 -> $9.47
#   2022: A55 (Mar) $13.50, A56 (Jun) $13.90, A57 (Sep) $13.45,
#         A58 (Dec) $12.99 -> $13.46
#   2023: A59 (Mar) $12.50, A60 (Jun) $12.73, A61 (Sep) $13.85,
#         A62 (Dec) $14.88 -> $13.49
#   2024: A63 (Mar) $16.00, A64 (Jun) $21.03, A65 (Sep) $25.75,
#         A66 (Dec) $20.05 -> $20.71
#   2025: A67 (Mar) $19.76, A68 (Jun) $19.63, A69 (Sep) $22.25,
#         A70 (Dec) $26.73 -> $22.09
# (A54 is the only pre-2023 auction that triggered the Cost Containment
# Reserve: 3,919,482 CCR allowances sold on top of the 23,121,518 offered. The
# CCR release is a quantity event, not a separate price -- the auction still
# clears at ONE uniform price, $13.00 -- so the simple-mean recipe is unchanged
# and no weighting adjustment is warranted.)
# Caveat: RGGI allowances are denominated per *short* ton CO2 while the model's
# emission_rate_co2 is per *metric* tonne, so charging these prices against the
# metric-tonne rate understates the true allowance cost by ~10.2% (1 t = 1.1023
# short tons). The understatement is small and keeps each stored value an exact,
# citable match to the published RGGI clearing prices; a future refinement can
# scale by 1.1023 if winter price fidelity demands it. Like CAISO, RGGI carries
# no border carbon adjustment on imports (contrast CARB's unspecified-import EF),
# so the NYISO import node is unaffected.
#
# NEISO — the same RGGI auctions (all six New England states are RGGI
# members, so the allowance cost applies ISO-wide; doc-08 design decision
# 3), but stored CONVERTED to the model's $/metric-tonne emission-rate
# unit at 1 short ton = 0.907185 t (x 1.10231):
#   2018: $4.41/short ton  -> $4.86/t
#   2019: $5.42/short ton  -> $5.97/t
#   2020: $6.41/short ton  -> $7.07/t
#   2021: $9.47/short ton  -> $10.44/t
#   2022: $13.46/short ton -> $14.84/t
#   2023: $13.49/short ton -> $14.87/t
#   2024: $20.71/short ton -> $22.83/t
#   2025: $22.09/short ton -> $24.35/t
# (Auction-level prices and source as the NYISO block above; press-release
# URLs rggi.org/sites/default/files/Uploads/Auction-Materials/
# {59..70}/PR*_Auction{59..70}.pdf, retrieved 2026-06-11.)
# HARMONIZATION NOTE: NYISO (above) deliberately stores the published
# short-ton clearing prices (exact citable match, ~10.2% understatement);
# NEISO stores the metric-converted values (unit-exact MC). The two RGGI
# entries should be unified one way or the other in a joint NYISO/NEISO
# calibration pass.
# EXTENDED TO 2018-2022 on 2026-08-14 (nyiso-134). Same source, same recipe,
# ZERO free parameters: the year's four quarterly RGGI clearing prices, simple
# mean, from the same RGGI, Inc. "Allowance Prices and Volumes" table that
# supplies A59-A70 (auctions A39-A58; per-auction rows land in
# data/raw/policy/carbon-auction-results/carbon-auction-results.csv and curate
# to the carbon-auction-results clean datatype). The recipe was VERIFIED against
# the incumbent years before the new rows were written: recomputing 2023/2024/
# 2025 from the published table reproduces 13.49 / 20.71 / 22.09 (NYISO) and
# 14.87 / 22.83 / 24.35 (NEISO) EXACTLY.
#
# WHY THE GAP EXISTED AND WHY IT MATTERED: state_carbon_price() returns None for
# a year absent here, and a backcast keeper ships carbon_price_path="zero", so an
# out-of-training solve silently charged $0/tCO2 with no exception and no
# warning. For NYISO 2022 that is $6.13/MWh on the fleet 0.4558 tCO2/MWh-net
# (8.2 % of the 2022 RT mean) and MERIT-ORDER distorting, since the CC-to-steam
# rate spread is 2.9x. Diagnosis: defect D-1 of
# results/calibration/ASSESSMENT-nyiso134-2022-readiness-2026-08-14.md.
#
# CAISO is deliberately NOT extended here: CARB rows come from a different
# source that blocks automated fetches (see the carbon-auction-results raw
# README), so its 2018-2022 block is a separate CAISO-lane intake (rule 25
# [R-ISO-SCOPE]) and remains an open gap for any CAISO out-of-training year.
# (Closed 2026-09-24 by i-caiso for 2019-2021 — see the CAISO block above; 2018
# remains absent.)
#
# NYISO stores the PUBLISHED short-ton clearing price; NEISO stores it
# METRIC-CONVERTED (x 1.10231) — the harmonization asymmetry documented above is
# preserved exactly for the new years.
STATE_CARBON_PRICE_BY_ISO: dict[str, dict[int, float]] = {
    "CAISO": {
        2019: 16.84,
        2020: 17.04,
        2021: 22.04,
        2022: 28.45,
        2023: 33.03,
        2024: 35.23,
        2025: 28.06,
    },
    "NYISO": {
        2018: 4.41,
        2019: 5.42,
        2020: 6.41,
        2021: 9.47,
        2022: 13.46,
        2023: 13.49,
        2024: 20.71,
        2025: 22.09,
    },
    "NEISO": {
        2018: 4.86,
        2019: 5.97,
        2020: 7.07,
        2021: 10.44,
        2022: 14.84,
        2023: 14.87,
        2024: 22.83,
        2025: 24.35,
    },
}

# PJM — the SAME RGGI auction clearing prices as the NYISO/NEISO blocks above
# (RGGI, Inc. auction results A59-A70, sources cited there), stored METRIC-
# CONVERTED like NEISO (1 short ton = 0.907185 t, x 1.10231 — unit-exact
# against the model's per-tonne emission_rate; the harmonization note above
# applies). Kept in a SEPARATE registry rather than STATE_CARBON_PRICE_BY_ISO
# because PJM's program is partial-footprint and its arming is GATED
# (ScenarioConfig.pjm_rggi_allowance_pricing, default off, pjm-146): a bare
# STATE_CARBON_PRICE_BY_ISO["PJM"] entry would silently re-arm every PJM
# backcast under the default-True state_carbon_pricing flag — a same-cache-key
# behavior change (results/cache.py epoch policy) and an uncontrolled keeper-
# semantics change. Folding this into STATE_CARBON_PRICE_BY_ISO (+
# price_key="PJM") and retiring the gate is the named promotion path, an owner
# decision on the pjm-146 A/B numbers
# (results/calibration/PREREG-pjm146-rggi-allowance-2026-08-02.md §2.2).
# Membership is NOT priced here: the per-generator member mask (NJ/MD/DE all
# years, VA 2023 only, exact per-plant EIA-860 state test with the committed
# PJM_RGGI_ZONE_SHARE fallback) is applied at the mc seam via
# policy.cap_and_trade.per_generator_membership.
#   2019: $5.42/short ton  -> $5.97/t   (A43-A46)
#   2020: $6.41/short ton  -> $7.07/t   (A47-A50)
#   2021: $9.47/short ton  -> $10.44/t  (A51-A54)
#   2022: $13.46/short ton -> $14.84/t  (A55-A58)
#   2023: $13.49/short ton -> $14.87/t
#   2024: $20.71/short ton -> $22.83/t
#   2025: $22.09/short ton -> $24.35/t
# 2020-2022 ADDED (pjm-h22, 2026-09-24) so the gated arm can solve every PJM
# year (rules 16/34(c)). Identical to the NEISO 2020-2022 values above: the
# same four quarterly auctions per year, simple mean, from
# data/raw/policy/carbon-auction-results/carbon-auction-results.csv (RGGI, Inc.
# "Allowance Prices and Volumes"), converted x 1.10231 on the rounded mean
# exactly as 2023-2025 were. Zero free parameters.
# 2019 ADDED (R-PJM, 2026-09-25), same recipe and source; equals NEISO's 2019
# metric value 5.97.
PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE: dict[int, float] = {
    2019: 5.97,
    2020: 7.07,
    2021: 10.44,
    2022: 14.84,
    2023: 14.87,
    2024: 22.83,
    2025: 24.35,
}

# CARB default emission factor for unspecified-source imported electricity
# (tCO2e/MWh). CAISO levies a border carbon adjustment on unspecified WECC
# imports at this factor x the allowance price; applied to the WECC import
# tranche prices (model/transmission.py::build_wecc_import_generators).
# Source: CARB Mandatory GHG Reporting Regulation (MRR), 17 CCR §95111(b) —
#   default emission factor for unspecified power, 0.428 MT CO2e/MWh.
CARB_UNSPECIFIED_IMPORT_EF: float = 0.428
