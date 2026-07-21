"""NYISO zonal gas basis: per-zone hub offsets, reconciled winter spread, and
the downstate CT interruptible/LDC-delivered gas premia.

Split out of ``data/fuel.py`` (W-D3; refactor-consolidation plan §5 item 3) as
pure code motion. Rule 25: every value here is NYISO's own (measured SOM hub
tables, EIA NG series, LDC tariffs) — nothing merges into a generic default.
``_henry_hub_monthly`` is resolved through the package namespace at call time
(:func:`.._shared._pkg_ns`) because tests patch it on the facade.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import GAS_PRICES_DIR, RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from .._shared import (
    _DAYS_IN_MONTH,
    _FUEL_ZONAL_HUB_DATATYPE,
    _GAS_FUEL_IDX,
    _GAS_PRICE_FLOOR,
    _clean_zonal_hub_frame,
    _month_index,
    _pkg_ns,
    _use_clean_data,
    logger,
)
from ..hubs import _load_winter_basis_frame


# Measured NYISO per-zone annual gas-hub prices (NYISO State of the Market
# reports, Potomac Economics, Figure A-6 annual averages). NYISO prices each
# region off a different pipeline index — the cheap western/Central zones on
# Tenn Z4 200L / Niagara, the Capital/Hudson and Long Island zones on Iroquois
# Z2 / Tenn Z6, and New York City on Transco Z6 (NY) — so the marginal gas unit
# in the east costs persistently more than in the west even when the system
# delivered-cost average (EIA-923 volume-weighted) is the same. That basis,
# at ~7 MMBtu/MWh, is the structural source of the steady upstate-cheap /
# east-dear LMP gradient (Central-East congestion realizes it); a single
# ISO-month series cannot. Consumed by :func:`apply_nyiso_zonal_gas_basis`.
NYISO_ZONAL_GAS_HUB_PATH: Path = RAW_DATA_DIR / "nyiso_zonal_gas_hub.csv"

# The east reference zone whose hub (Iroquois Z2 — the bulk of NYISO gas burns
# in the Capital/Hudson/LI pocket) anchors the offset: zones cheaper than it
# (Upstate on Tenn Z4, NYC on Transco Z6) get a negative basis, leaving the
# already-calibrated east level untouched while opening the west-to-east spread.
NYISO_GAS_HUB_REFERENCE_ZONE: str = "Capital_Hudson"


# Measured Transco Z6 NY monthly (mean of daily quotes) + the committed Iroquois
# Z2 monthly reconstruction (Transco monthly + the NYISO SOM *annual*
# Iroquois-Transco spread). Consumed by nyiso_reconciled_reference_monthly,
# which re-allocates that measured annual spread across months by the measured
# Algonquin scarcity signal (rule #13 reconciliation; see its docstring).
TRANSCO_IROQUOIS_MONTHLY_PATH: Path = GAS_PRICES_DIR / "transco_z6_iroquois_monthly.csv"


# NYISO downstate (NYC / Long Island) interruptible-gas premium: the measured
# monthly excess of the NY LDC city-gate price over the NY fleet-average
# delivered-to-electric-power gas cost (scripts/data/fetch_nyiso_downstate_gas_basis.py;
# EIA NG N3050NY3 − N3045NY3, $/MMBtu, floored 0). Consumed by
# :func:`apply_nyiso_downstate_ct_gas_basis`.
NYISO_DOWNSTATE_CT_GAS_BASIS_PATH: Path = (
    GAS_PRICES_DIR / "nyiso_downstate_ct_gas_basis_monthly.csv"
)


_NYISO_ZONAL_HUB_CLEAN_CACHE: dict[str, pd.DataFrame | None] = {}


_NYISO_ZONAL_HUB_CACHE: dict[Path, pd.DataFrame | None] = {}


def _load_nyiso_zonal_gas_hub(path: Path | None) -> pd.DataFrame | None:
    """Load the NYISO per-zone annual gas-hub table, or ``None`` if absent."""
    if path is None and _use_clean_data():
        from scripts.lib.clean_io import clean_exists

        if clean_exists(_FUEL_ZONAL_HUB_DATATYPE, iso="NYISO"):
            if "_clean" not in _NYISO_ZONAL_HUB_CLEAN_CACHE:
                _NYISO_ZONAL_HUB_CLEAN_CACHE["_clean"] = _clean_zonal_hub_frame("NYISO")
            return _NYISO_ZONAL_HUB_CLEAN_CACHE["_clean"]
    resolved = Path(path) if path else NYISO_ZONAL_GAS_HUB_PATH
    if resolved in _NYISO_ZONAL_HUB_CACHE:
        return _NYISO_ZONAL_HUB_CACHE[resolved]
    frame: pd.DataFrame | None = None
    if resolved.exists():
        loaded = pd.read_csv(resolved)
        if not loaded.empty:
            frame = loaded
    _NYISO_ZONAL_HUB_CACHE[resolved] = frame
    return frame


def nyiso_zonal_gas_offsets(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: $/MMBtu offset vs the east reference}`` for NYISO, or None.

    The offset is the zone's measured hub price (Tenn Z4 200L upstate, Iroquois
    Z2 in the Capital/Hudson/LI east, Transco Z6 NY in the city) minus the
    reference zone's hub (:data:`NYISO_GAS_HUB_REFERENCE_ZONE`, Iroquois Z2).
    The reference zone resolves to 0.0, so the calibrated east gas level is
    preserved and only the cheaper west/city zones shift down — opening the
    persistent upstate-cheap / east-dear basis the system-average series flattens.
    Returns ``None`` when the table is missing or has no rows for ``year``.
    """
    frame = _load_nyiso_zonal_gas_hub(path)
    if frame is None:
        return None
    sub = frame[frame["year"] == year]
    if sub.empty:
        return None
    hub = {str(r.zone): float(r.hub_usd_mmbtu) for r in sub.itertuples()}
    ref = hub.get(NYISO_GAS_HUB_REFERENCE_ZONE)
    if ref is None:
        return None
    return {z: price - ref for z, price in hub.items()}


def nyiso_reconciled_reference_monthly(
    year: int,
    hub_path: Path | None = None,
    basis_path: Path | None = None,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Reconciled Iroquois Z2 monthly hub price, winter-weighted from measured data.

    The committed reference construction (``transco_z6_iroquois_monthly.csv``)
    distributes the **measured annual** NYISO-SOM Iroquois−Transco spread FLAT
    across months, which mis-states the winter physics: Iroquois Z2 is a
    Connecticut trading point inside the New England pipeline complex, and its
    premium over Transco Z6 NY concentrates in exactly the constrained winter
    months when Algonquin blows out (Dec-2024: flat construction $3.16/MMBtu vs
    the ~$9 complex it physically trades in). No free Iroquois series exists to
    replace it (verified: zero prints in 146 NGWU weekly pages 2023–25; NGI/ICE
    paywalled), so per rule #13 this is the documented **reconciled version of
    the real data** rather than a guess:

      ``iroquois_m = transco_m + annual_spread × 12 × w_m``
      ``w_m = max(agt_basis_m, 0) / Σ max(agt_basis_m, 0)``

    - ``transco_m`` — the measured Transco Z6 NY monthly (mean of daily quotes);
    - ``annual_spread`` — the measured SOM annual Iroquois−Transco spread,
      preserved EXACTLY (scarcity-shaped up to the measured Algonquin-Citygate
      monthly ceiling below; the ceiling-shaved remainder re-enters as a
      year-round base differential water-filled into months with headroom);
    - ``w_m`` — the **measured Algonquin (MA-citygate) monthly basis**, the New
      England pipeline-scarcity signal that physically causes the Iroquois
      premium; unconstrained months (basis ≤ 0) carry zero premium (summer Z2
      trades at Transco backhaul parity).

    No fitted constant, nothing reads a model output or price residual; a
    forecast year regenerates it from the forward basis seasonality and it
    responds to changed conditions (a mild winter ⇒ low AGT basis ⇒ low
    premium). Returns ``(iroquois_m, transco_m)`` as two ``(12,)`` arrays, or
    ``None`` when any input series is incomplete for ``year`` (the caller then
    keeps the flat committed construction, byte-identical).
    """
    resolved = Path(hub_path) if hub_path else TRANSCO_IROQUOIS_MONTHLY_PATH
    if not resolved.exists():
        return None
    frame = pd.read_csv(resolved)
    sub = frame[frame["date"].astype(str).str.startswith(f"{year}-")]
    transco = np.full(12, np.nan)
    iroq = np.full(12, np.nan)
    for r in sub.itertuples():
        m = int(str(r.date)[5:7]) - 1
        if 0 <= m < 12:
            transco[m] = float(r.transco_z6_ny_usd_mmbtu)
            iroq[m] = float(r.iroquois_z2_usd_mmbtu)
    if np.isnan(transco).any() or np.isnan(iroq).any():
        return None
    annual_spread = float((iroq - transco).mean())
    bframe = _load_winter_basis_frame(basis_path)
    if bframe is None:
        return None
    agt_rows = bframe[(bframe["iso"] == "NEISO") & (bframe["year"] == year)]
    agt = np.full(12, np.nan)
    for _, row in agt_rows.iterrows():
        m = int(row["month"]) - 1
        if 0 <= m < 12:
            agt[m] = float(row["basis_usd_mmbtu"])
    if np.isnan(agt).any():
        return None
    w = np.clip(agt, 0.0, None)
    total = float(w.sum())
    if total <= 0.0:
        return None
    spread_m = annual_spread * 12.0 * w / total
    iroq_rec = transco + spread_m
    # Measured-ceiling reconciliation (rule #14): Iroquois Z2 is a Connecticut
    # trading point delivering INTO the New England market area, so its
    # monthly level cannot exceed the Algonquin Citygate — the demand ceiling
    # of the complex it feeds (Z2 gas flows on toward the citygate; a CT
    # buyer never pays more at Z2 than at the citygate it can buy instead).
    # Re-allocating 12x the SOM annual spread onto the few positive-basis
    # months has no per-month magnitude anchor and can breach that ceiling in
    # the most-constrained months (Feb-2023 reconstruction $13.21 vs the
    # measured $8.13 Algonquin month; Jan-2024 $8.60 vs $7.68). Cap each
    # month at the measured Algonquin Citygate monthly (Henry Hub month +
    # the same measured NEISO basis row the weights come from — the series
    # the NEISO keeper itself prices on), floored at Transco so the cap can
    # never invert the hubs. The shaved excess is not left as scarcity
    # premium — it re-enters as a year-round base differential water-filled
    # across the months with ceiling headroom (see below), so the measured
    # SOM ANNUAL spread is preserved exactly while no month out-prices the
    # ceiling.
    hh = _pkg_ns()._henry_hub_monthly(None)
    hh_m = np.array([hh.get((year, m + 1), np.nan) for m in range(12)])
    if not np.isnan(hh_m).any():
        alg_m = hh_m + agt
        # Floor the ceiling at the committed FLAT construction level
        # (transco + annual spread): the Z2<=citygate ordering is firm in the
        # constrained winter months the re-allocation loads (citygate blowouts
        # far exceed Z2), but inside unconstrained months the two hubs trade
        # within transport noise and the flat level is the better-measured
        # datum — the cap must only shave scarcity-month excess, never push a
        # month below the committed annually-exact construction.
        ceil_m = np.maximum(alg_m, transco + annual_spread)
        capped = np.minimum(iroq_rec, ceil_m)
        # Preserve the measured SOM ANNUAL spread (rule #13 — the annual
        # total is a measured datum, not disposable): the scarcity months
        # could not hold the full AGT-shaped re-allocation under the measured
        # Algonquin ceiling, so the shaved remainder is by construction a
        # year-round (non-scarcity) base differential — Z2 is a premium point
        # over Transco outside blowout months too (Waddington/TransCanada
        # supply pricing), which is why the measured SOM annual exceeds what
        # the scarcity months alone can carry. Water-fill it uniformly across
        # the months with ceiling headroom (the minimal-assumption
        # allocation), never above the ceiling; any residual that the whole
        # ceiling cannot hold is dropped and the annual under-delivers (no
        # 2023-25 year does).
        excess = float((iroq_rec - capped).sum())
        for _ in range(12):
            if excess <= 1e-9:
                break
            room = ceil_m - capped
            open_m = room > 1e-9
            if not open_m.any():
                break
            step = np.minimum(np.full(12, excess / open_m.sum()) * open_m, room)
            capped = capped + step
            excess -= float(step.sum())
        iroq_rec = capped
    return iroq_rec, transco


def nyiso_zonal_gas_ratios_monthly(
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
    basis_path: Path | None = None,
    henry_hub_path: Path | None = None,
) -> dict[str, np.ndarray] | None:
    """Return ``{zone: (12,) monthly ratio}`` vs the reconciled reference hub.

    The month-varying companion of :func:`nyiso_zonal_gas_offsets`, active only
    under ``config.nyiso_iroquois_winter_spread``. With the reference
    (Iroquois Z2) carrying its winter-concentrated premium, the flat annual
    ADDITIVE offsets would (a) wrongly drag the non-Iroquois zones up with the
    winter premium and (b) leave NYC's daily spikes amplified by the reference
    level, so each zone instead prices at the reference hourly series times its
    OWN measured hub-to-reference monthly ratio — preserving the zone's
    measured monthly mean exactly and scaling the within-month daily swing to
    the zone's own level:

    - **NYC** (Transco Z6 NY): ``transco_m / iroquois_m`` — the city resolves
      to its own measured hub monthly exactly.
    - **Iroquois-mapped zones** (Capital_Hudson / Lower_Hudson / Long_Island,
      annual level equal to the reference): ratio 1 — they ARE the reference.
    - **Upstate_West** (Tenn Z4 200L, a Marcellus supply point with no New
      England scarcity premium): its measured SOM annual level riding the
      Henry Hub within-year shape, over the reference —
      ``(annual + hh_m − mean(hh_m)) / iroquois_m`` — so its annual mean stays
      the measured SOM value.

    Every input is a measured series; no fitted constant. Returns ``None``
    when the flag is off or any series is incomplete (caller falls back to the
    annual additive offsets, byte-identical).
    """
    if config.iso != "NYISO" or not getattr(
        config, "nyiso_iroquois_winter_spread", False
    ):
        return None
    rec = nyiso_reconciled_reference_monthly(year, basis_path=basis_path)
    if rec is None:
        return None
    iroq_m, transco_m = rec
    if (iroq_m <= 0).any():
        return None
    frame = _load_nyiso_zonal_gas_hub(path)
    if frame is None:
        return None
    sub = frame[frame["year"] == year]
    if sub.empty:
        return None
    hub = {str(r.zone): float(r.hub_usd_mmbtu) for r in sub.itertuples()}
    ref_ann = hub.get(NYISO_GAS_HUB_REFERENCE_ZONE)
    if ref_ann is None:
        return None
    hh = _pkg_ns()._henry_hub_monthly(henry_hub_path)
    hh_m = np.array([hh.get((year, m + 1), np.nan) for m in range(12)])
    if np.isnan(hh_m).any():
        return None
    hh_shape = hh_m - float(hh_m.mean())
    ratios: dict[str, np.ndarray] = {}
    for z, price_ann in hub.items():
        if z == "NYC":
            ratios[z] = transco_m / iroq_m
        elif abs(price_ann - ref_ann) < 1e-9:
            ratios[z] = np.ones(12)
        else:
            ratios[z] = np.maximum(price_ann + hh_shape, _GAS_PRICE_FLOOR) / iroq_m
    return ratios


def apply_nyiso_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Shift each NYISO gas unit's price by its zone's measured hub basis.

    NYISO's regions buy gas off different, persistently-priced pipeline indices
    (:data:`NYISO_ZONAL_GAS_HUB_PATH`): the marginal gas unit in the Capital/
    Hudson east pays Iroquois Z2 / Tenn Z6 while the western and Central zones
    pay the cheaper Tenn Z4 200L / Niagara, so the east marginal gas costs
    ~$1-3/MMBtu more than the west all year. The EIA-923 volume-weighted
    ISO-month series and the thin per-plant F923 receipts (only ~5 NY plants
    report Schedule-5 gas) both wash this gradient out, leaving the model's
    west-to-east LMP spread a knife-edge fuel-merit accident. This adds the
    measured per-zone offset (:func:`nyiso_zonal_gas_offsets`, anchored so the
    east reference zone is unchanged) to every gas unit's delivered price,
    floored at a small positive so a deep negative basis cannot drive fuel
    cost below zero. Runs after the F923 plant-monthly overwrite and before
    :func:`apply_dual_fuel_pricing`, so oil parity still caps any winter spike.

    Gated on ``config.nyiso_zonal_gas_basis`` and ``config.iso == "NYISO"``
    (off by default; the calibration harness enables it for NYISO), so every
    other ISO and all forecasts are byte-identical. Mutates ``fuel_prices`` in
    place; idempotent given the same inputs.
    """
    if not getattr(config, "nyiso_zonal_gas_basis", False):
        return
    if config.iso != "NYISO":
        return
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    if gas_rows.size == 0:
        return
    # Month-varying ratios under the reconciled winter spread (each zone
    # prices at the reference hourly series times its own measured
    # hub-to-reference monthly ratio; see nyiso_zonal_gas_ratios_monthly).
    monthly_ratios = nyiso_zonal_gas_ratios_monthly(config, year, path)
    if monthly_ratios is not None:
        month_of_hour = _month_index(fuel_prices.shape[1])
        ratio_matrix = np.array(
            [monthly_ratios.get(name, np.ones(12)) for name in zone_names],
            dtype=float,
        )
        gen_ratio = ratio_matrix[fleet.zone_idx[gas_rows]][:, month_of_hour]
        fuel_prices[gas_rows, :] = np.maximum(
            fuel_prices[gas_rows, :] * gen_ratio, _GAS_PRICE_FLOOR
        )
        logger.info(
            "NYISO zonal gas basis (%d, monthly reconciled): %d gas units "
            "scaled by zone-month hub ratio (min %.2f, max %.2f vs %s)",
            year,
            gas_rows.size,
            float(gen_ratio.min()),
            float(gen_ratio.max()),
            NYISO_GAS_HUB_REFERENCE_ZONE,
        )
        return
    offsets = nyiso_zonal_gas_offsets(year, path)
    if offsets is None:
        return
    # Per-generator additive offset from its zone (0.0 for the reference zone
    # and any zone absent from the table — e.g. the priced external node).
    offset_by_zone_idx = np.array(
        [offsets.get(name, 0.0) for name in zone_names], dtype=float
    )
    gen_offset = offset_by_zone_idx[fleet.zone_idx[gas_rows]]
    floored = np.maximum(
        fuel_prices[gas_rows, :] + gen_offset[:, np.newaxis], _GAS_PRICE_FLOOR
    )
    fuel_prices[gas_rows, :] = floored
    logger.info(
        "NYISO zonal gas basis (%d): %d gas units shifted by zone hub offset "
        "(min %.2f, max %.2f $/MMBtu vs %s)",
        year,
        gas_rows.size,
        float(gen_offset.min()),
        float(gen_offset.max()),
        NYISO_GAS_HUB_REFERENCE_ZONE,
    )


_NYISO_DOWNSTATE_CT_BASIS_CACHE: dict[Path, dict[int, np.ndarray]] = {}

# Downstate load pockets served off the NYC / Long Island LDC city gates.
NYISO_DOWNSTATE_CT_ZONES: frozenset[str] = frozenset({"NYC", "Long_Island"})


def nyiso_downstate_ct_gas_premium(
    year: int, path: Path | None = None
) -> np.ndarray | None:
    """Return the ``(12,)`` monthly downstate-peaker interruptible-gas premium.

    The measured monthly excess ($/MMBtu, floored at 0) of the NY LDC city-gate
    price over the Transco Zone 6 NY pipeline hub the model prices downstate gas
    at — the delivered-cost increment a non-firm downstate (NYC / Long Island)
    peaker faces buying interruptible city-gate gas instead of firm pipeline-hub
    gas. Positive year-round; floors to 0 only in months the pipeline hub itself
    spikes above the city gate (arctic events). Read from
    :data:`NYISO_DOWNSTATE_CT_GAS_BASIS_PATH` (built by
    ``scripts/data/fetch_nyiso_downstate_gas_basis.py`` from EIA NG series N3050NY3
    minus the measured Transco Z6 NY monthly). Returns ``None`` when the table is
    missing or has no rows for ``year`` (e.g. a forward year without the series
    extended).
    """
    resolved = Path(path) if path else NYISO_DOWNSTATE_CT_GAS_BASIS_PATH
    cache = _NYISO_DOWNSTATE_CT_BASIS_CACHE.setdefault(resolved, {})
    if year in cache:
        return cache[year]
    if not resolved.exists():
        cache[year] = None  # type: ignore[assignment]
        return None
    frame = pd.read_csv(resolved)
    sub = frame[frame["year"] == year]
    if sub.empty:
        cache[year] = None  # type: ignore[assignment]
        return None
    monthly = np.zeros(12, dtype=float)
    for r in sub.itertuples():
        m = int(r.month) - 1
        if 0 <= m < 12:
            monthly[m] = float(r.premium_usd_mmbtu)
    cache[year] = monthly
    return monthly


def apply_nyiso_downstate_ct_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Add the interruptible city-gate gas premium to downstate NYISO peakers.

    NYISO's downstate combustion-turbine PEAKERS (NYC zone J + Long Island zone
    K, ``CT_PEAKER`` / ``gas_ct`` — the Bayonne / Equus / Edgewood /
    Glenwood-Landing LM6000 fleet) run only a few hundred hours a year, so they
    cannot justify firm interstate pipeline transportation: they take gas off
    the local LDC (Con Edison / National Grid) **city gate** on interruptible
    service, so their delivered fuel index is the LDC city gate, not the
    interstate pipeline hub the model prices downstate gas at (Transco Z6 NY via
    ``gas_monthly_actuals`` + the hub-basis overlay). Pricing these peakers at
    the pipeline hub, the energy-only LP sees a heat-rate-9-10 LM6000 undercut
    the heat-rate-11-12 downstate steam fleet and runs them near-baseload
    year-round (the CT_PEAKER over-run the de-leaked offer curve exposes, B-NYI-1
    / issue #1344 — dominated by the Long Island gas-island peakers).

    This adds the **measured** monthly premium
    (:func:`nyiso_downstate_ct_gas_premium` — the EIA NY city-gate price minus
    the measured Transco Z6 NY hub, floored at 0) to each downstate
    ``CT_PEAKER`` unit's delivered gas price, lifting it from the pipeline hub to
    its actual LDC-delivered index. The premium is positive year-round (the city
    gate carries interstate-pipeline demand charges + distribution + an
    interruptible premium over the hub every month) and widens in summer when NYC
    gas-for-power cooling demand makes downstate interruptible gas scarce; it
    floors to 0 only when the pipeline hub itself spikes above the city gate
    (arctic events), where the model's base gas already exceeds the delivered
    price. It is a delivered fuel price (CLAUDE.md rule #13's canonical
    admissible input): the city gate and the hub publish monthly and project
    forward, so a forecast year regenerates the premium and it responds to
    changed conditions (a tight winter/summer widens it). Nothing is fitted to a
    price/volume residual (rules #1/#11/#12).

    Runs after :func:`apply_nyiso_zonal_gas_basis` and before
    :func:`apply_dual_fuel_pricing`, so the oil-parity cap still bounds any
    winter spike. Gated on ``config.nyiso_downstate_ct_gas_basis`` and
    ``config.iso == "NYISO"`` (off by default; the calibration harness enables
    it for NYISO), so every other ISO and all forecasts are byte-identical.
    Mutates ``fuel_prices`` in place; idempotent given the same inputs.
    """
    if not getattr(config, "nyiso_downstate_ct_gas_basis", False):
        return
    if config.iso != "NYISO":
        return
    if fleet.plant_group is None:
        return
    premium = nyiso_downstate_ct_gas_premium(year, path)
    if premium is None:
        return
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    plant_group = np.asarray(fleet.plant_group)
    # Downstate model-zone indices (NYC / Long Island). Membership is checked by
    # index so units on the priced external node (a zone_idx beyond the model
    # zone list) are ignored, not an out-of-range lookup.
    downstate_idx = np.array(
        [i for i, name in enumerate(zone_names) if name in NYISO_DOWNSTATE_CT_ZONES],
        dtype=int,
    )
    is_gas_ct = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    ct_rows = np.nonzero(
        is_gas_ct
        & (plant_group == "CT_PEAKER")
        & np.isin(fleet.zone_idx, downstate_idx)
    )[0]
    if ct_rows.size == 0:
        return
    month_of_hour = _month_index(fuel_prices.shape[1])
    premium_hourly = premium[month_of_hour]  # (T,)
    fuel_prices[ct_rows, :] = np.maximum(
        fuel_prices[ct_rows, :] + premium_hourly[np.newaxis, :], _GAS_PRICE_FLOOR
    )
    logger.info(
        "NYISO downstate CT interruptible-gas basis (%d): %d downstate "
        "CT_PEAKER units lifted by the LDC city-gate premium "
        "(monthly min %.2f, max %.2f $/MMBtu; summer-peaked)",
        year,
        ct_rows.size,
        float(premium.min()),
        float(premium.max()),
    )


def _zone_delivered_hourly(
    by_md: dict[int, dict[int, float]], hours: int
) -> np.ndarray:
    """Expand one zone's ``{month:{day:val}}`` onto the model's 8760 calendar.

    Each calendar day's value is repeated across its 24 hours, mirroring the
    mean-preserving daily overlay's calendar walk
    (:func:`nyiso_reconciled_reference_monthly`); a leap-year Feb-29 row is never
    referenced. Returns a ``(hours,)`` array (may hold NaN only where a whole
    month is missing, which the caller resolves).
    """
    out = np.full(hours, np.nan, dtype=float)
    hour = 0
    for m in range(12):  # m = 0-based month
        n_days = _DAYS_IN_MONTH[m]
        dated = by_md.get(m + 1, {})
        if dated and hour < hours:
            day_vals = np.array(
                [dated.get(d, np.nan) for d in range(1, n_days + 1)], dtype=float
            )
            # A single non-trading gap should never leave a NaN hole; the daily
            # series is already gap-filled at curation, but guard defensively.
            if np.isnan(day_vals).any():
                day_vals = pd.Series(day_vals).ffill().bfill().to_numpy()
            shaped = np.repeat(day_vals, 24)[: max(0, hours - hour)]
            out[hour : hour + len(shaped)] = shaped
        hour += n_days * 24
    return out


def _downstate_delivered_gas_hourly_by_zone(
    iso: str, year: int, hours: int
) -> dict[str, np.ndarray] | None:
    """Return ``{zone: (hours,) delivered-gas index}`` per downstate zone, or ``None``.

    Expands the curated per-zone ``nyiso-downstate-gas`` daily index
    (:func:`market_sim.data.nyiso_downstate_gas.delivered_gas_by_zone_month_day` —
    measured Transco Z6 NY daily spot + monthly LDC non-firm transport rate, per
    zone) onto the model's fixed 365-day (28-day-February) calendar. ``None`` when
    the datatype has no rows for the year (a forward year without the series
    extended), so the caller falls back to the monthly-premium path.
    """
    from market_sim.data.nyiso_downstate_gas import delivered_gas_by_zone_month_day

    by_zone = delivered_gas_by_zone_month_day(iso, year)
    if not by_zone:
        return None
    out: dict[str, np.ndarray] = {}
    for zone, by_md in by_zone.items():
        arr = _zone_delivered_hourly(by_md, hours)
        if np.isnan(arr).all():
            continue
        # Any residual NaN (a month with no rows) falls back to surrounding
        # measured days so the CT gas is always defined where the class dispatches.
        if np.isnan(arr).any():
            arr = pd.Series(arr).ffill().bfill().to_numpy()
        out[zone] = arr
    return out or None


def apply_nyiso_downstate_ct_gas_daily(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
) -> None:
    """Re-ground downstate NYISO CT-peaker gas on the measured DAILY delivered index.

    The daily-resolution successor to :func:`apply_nyiso_downstate_ct_gas_basis`
    (the monthly-premium adder) for the same NYC / Long Island ``CT_PEAKER``
    LM6000 fleet (Bayonne / Equus / Edgewood / Glenwood-Landing). Rather than
    lift the pipeline-hub *monthly* base by a statewide monthly premium, this
    **sets** each downstate CT_PEAKER unit's delivered gas directly to the curated
    per-zone ``nyiso-downstate-gas`` daily index — the measured Transco Zone 6 NY
    pipeline-hub **daily** spot (the peaker's own commodity) plus the measured
    **monthly** LDC **non-firm transportation** delivery rate for that unit's zone
    (KEDNY SC-22 for NYC, KEDLI SC-19 for Long Island;
    :func:`_downstate_delivered_gas_hourly_by_zone`).

    Why this is the correct grounding (rules #11/#12/#13): these interruptible
    peakers run only a few hundred hours a year, concentrated on the coldest days
    when the downstate pipeline hub blows out (Transco Z6 NY hit $23.90/MMBtu in
    Jan-2024). The monthly mean smears that spike across the whole month, pricing
    the peaker's scarce-day gas far too cheap on exactly the hours it clears —
    letting an HR~9-10 LM6000 undercut the dearer downstate steam fleet. Pricing
    the daily hub spot lifts the peaker offer on the scarce days it runs. And
    because they are transportation customers (buy their own commodity, pay the
    LDC a non-firm transport charge), the adder over the hub is the measured LDC
    non-firm transportation delivery rate — not the statewide firm citygate the v1
    construction used — and it is per-zone because the LI gas island (KEDLI) and
    the NYC system (KEDNY) carry materially different delivery costs. Each input
    is a measured, forward-native market/tariff series (the daily Transco spot and
    the monthly LDC transport rate both publish forward and step at rate cases /
    respond to changed conditions), so a forecast year regenerates it; nothing is
    fitted to a price or volume residual (rules #1/#11/#12/#13).

    Runs immediately after :func:`apply_nyiso_downstate_ct_gas_basis` in the
    fuel-price pipeline and before :func:`apply_dual_fuel_pricing`, so the
    oil-parity cap still bounds any winter spike. Gated on
    ``config.nyiso_downstate_ct_gas_daily`` and ``config.iso == "NYISO"`` (off by
    default; the calibration harness enables it for NYISO). It supersedes the
    monthly adder for this class — set ``nyiso_downstate_ct_gas_basis=False`` when
    this is on (one mechanism per phenomenon, rule 19); if both were set, the
    daily SET here overwrites the monthly ADD, so the level is still the daily
    delivered index. Mutates ``fuel_prices`` in place; idempotent given the same
    inputs; every other ISO and all forecasts without the series are byte-identical.
    """
    if not getattr(config, "nyiso_downstate_ct_gas_daily", False):
        return
    if config.iso != "NYISO":
        return
    if fleet.plant_group is None:
        return
    by_zone = _downstate_delivered_gas_hourly_by_zone(
        config.iso, year, fuel_prices.shape[1]
    )
    if not by_zone:
        return
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    plant_group = np.asarray(fleet.plant_group)
    is_gas_ct = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    total_rows = 0
    lo = hi = None
    # Each downstate zone's CT_PEAKER units take that zone's own LDC-delivered
    # index (membership by zone index so a priced external node is ignored).
    for zone, delivered in by_zone.items():
        if zone not in NYISO_DOWNSTATE_CT_ZONES or zone not in zone_names:
            continue
        z_idx = zone_names.index(zone)
        ct_rows = np.nonzero(
            is_gas_ct & (plant_group == "CT_PEAKER") & (fleet.zone_idx == z_idx)
        )[0]
        if ct_rows.size == 0:
            continue
        fuel_prices[ct_rows, :] = np.maximum(delivered[np.newaxis, :], _GAS_PRICE_FLOOR)
        total_rows += int(ct_rows.size)
        zmin, zmax = float(delivered.min()), float(delivered.max())
        lo = zmin if lo is None else min(lo, zmin)
        hi = zmax if hi is None else max(hi, zmax)
    if total_rows == 0:
        return
    logger.info(
        "NYISO downstate CT per-zone daily delivered-gas re-grounding (%d): %d "
        "downstate CT_PEAKER units SET to their zone's measured daily delivered "
        "index (Transco Z6 NY daily + LDC non-firm transport rate; "
        "range %.2f-%.2f $/MMBtu across zones %s)",
        year,
        total_rows,
        float(lo),
        float(hi),
        list(by_zone),
    )
