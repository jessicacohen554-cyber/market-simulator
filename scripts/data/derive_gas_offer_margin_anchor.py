"""Derive the gas-offer net-revenue margin ANCHOR ($/MMBtu) for an ISO.

The identification constant of the ``gas_offer_net_revenue_margin`` mechanism
(``constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO``; design doc
``docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md``): the mean of
the model's own merit-order delivered-gas series
(:func:`market_sim.data.fuel.trajectories._gas_series` — measured EIA Henry
Hub monthly × the ISO's measured hub basis, the exact series the registered
``offer_curve_by_group`` band multipliers were calibrated against) over the
training window 2023–2025. At ``fuel == anchor`` the reformed offer reduces
EXACTLY to the registered band multiplier, so the anchor is the point where
the multiplicative and fixed-margin forms are observationally equivalent —
the identification point, not a tunable.

Rule-23 frozen derive: re-run ONLY when the underlying gas source data
changes (``data/raw/gas-prices/`` workbooks — Henry Hub monthly/daily, the
ISO hub basis series — or the EIA-923 ISO-month receipts), and cite that data
change in the re-derivation commit. NEVER because a price residual moved.

It is a REPORTING / derivation tool only — default-off in every solve path.
The single model artifact it informs is the hand-set
``GAS_OFFER_MARGIN_ANCHOR_BY_ISO`` entry in ``config/constants.py`` (cited
back to this script), consumed by the harness only under
``--gas-offer-margin``.

With ``--net-revenue-check`` it also prints the per-band fixed margins the
anchor implies for the ISO's registered curve (markup × base_HR × anchor) and
the Potomac-SOM-style peaker cross-check — the offer-side analogue of
``model/capacity_evolution/retirements.py``'s net-revenue screen: the
scarcity margin's implied cost-recovery run-hours,
``fixed_om_gas_ct × 1000 / margin``. Documentation only; never a tuning
channel.

Usage::

    python scripts/data/derive_gas_offer_margin_anchor.py --iso NEISO
    python scripts/data/derive_gas_offer_margin_anchor.py --iso NEISO --net-revenue-check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fuel.trajectories import _gas_series  # noqa: E402

# Training window (CLAUDE.md rule 22: 2023–2025 is the ONLY tuned-against
# span) with the measured EIA annual Henry Hub spot averages every keeper
# recipe carries (calibration_flags.gas_prices — EIA Natural Gas Spot Price,
# Henry Hub, annual averages). The override only levels months the measured
# ISO-month / hub-basis overlays leave uncovered.
TRAIN_WINDOW_HH: dict[int, float] = {2023: 2.54, 2024: 2.19, 2025: 3.52}

# Per-ISO gas flag recipe for the delivered series — mirrors the calibration
# harness (each ISO's KEEPER backcast_config gas overlay): monthly EIA-923
# actuals + the ISO's measured hub/basis overlay. The daily within-month shape
# (gas_daily_shape / gas_hub_basis_daily) is mean-preserved to the monthly hub
# level by construction, so the ANNUAL mean — hence the anchor — is identical
# with or without the daily leg; the daily flags are carried only to mirror the
# keeper exactly. Each entry is the True gas-flag set of the ISO's keeper
# run_config.json (2026-07-23 keepers: ercot99 / pjm-gasshape-interpfix /
# caiso-102 / miso-81 / nyiso-70 / neiso-61), so the anchor is derived on the
# exact delivered-gas series the registered offer_curve_by_group multipliers
# were calibrated against (rule 24 — anchors never cross ISO boundaries).
GAS_SERIES_FLAGS: dict[str, dict[str, bool]] = {
    # ERCOT keeper (ercot99): annual Henry Hub + seasonality only — no monthly
    # actuals, no hub-basis overlay (E1: ERCOT stays on annual + shape).
    "ERCOT": {
        "gas_seasonality": True,
    },
    # PJM keeper: --gas-monthly-actuals (its keeper passes it explicitly) +
    # the mean-preserving daily HH shape. No citygate/basin hub overlay.
    "PJM": {
        "gas_seasonality": True,
        "gas_monthly_actuals": True,
        "gas_daily_shape": True,
    },
    # CAISO keeper: monthly actuals + the SoCal/PG&E Citygate hub-basis overlay
    # (the measured CA trading hub the marginal CC prices off) + daily shape.
    "CAISO": {
        "gas_seasonality": True,
        "gas_monthly_actuals": True,
        "gas_hub_basis_overlay": True,
        "gas_daily_shape": True,
    },
    # MISO keeper: per-plant EIA-923 monthly level with the mean-preserving
    # daily HH swing on top (no ISO-month actuals flag, no hub overlay).
    "MISO": {
        "gas_seasonality": True,
        "gas_daily_shape": True,
    },
    # NYISO keeper: monthly actuals + the (mean-zero) zonal pipeline-hub basis +
    # the Transco Z6 daily hub overlay + daily shape.
    "NYISO": {
        "gas_seasonality": True,
        "gas_monthly_actuals": True,
        "gas_hub_basis_overlay": True,
        "gas_hub_basis_daily": True,
        "gas_daily_shape": True,
        "nyiso_zonal_gas_basis": True,
    },
    "NEISO": {
        "gas_seasonality": True,
        "gas_monthly_actuals": True,
        "gas_hub_basis_overlay": True,
        "gas_hub_basis_daily": True,
    },
}


def derive_anchor(iso: str) -> tuple[dict[int, float], float]:
    """Return ({year: delivered mean}, window anchor) for ``iso``."""
    if iso not in GAS_SERIES_FLAGS:
        raise SystemExit(
            f"{iso}: no delivered-gas series recipe registered in this derive "
            "script — add the ISO's calibration gas flags (mirroring "
            "backcast_config) before deriving an anchor (rule 24: anchors "
            "never cross ISO boundaries)"
        )
    base = ScenarioConfig(
        iso=iso, mode="backcast", hours=HOURS_PER_YEAR, **GAS_SERIES_FLAGS[iso]
    )
    year_means: dict[int, float] = {}
    for year, hh in sorted(TRAIN_WINDOW_HH.items()):
        series = _gas_series(
            base.with_overrides(gas_price_override=hh), year, HOURS_PER_YEAR
        )
        year_means[year] = float(np.nanmean(series))
    anchor = float(np.mean(list(year_means.values())))
    return year_means, anchor


#: ISOs whose keeper applies a PER-ZONE delivered-gas basis, so the ISO-level
#: series :func:`derive_anchor` reads is NOT the price their units actually pay.
#: Only these ISOs have a zone-resolved anchor to derive; every other ISO's
#: unit fuel IS the ISO series, so its single anchor is already identified at
#: the grain the mechanism's own definition requires. Rule 25 — an entry here is
#: that ISO's own measured basis table and never transfers.
ZONAL_BASIS_ISOS: frozenset[str] = frozenset({"NYISO"})


def derive_zonal_anchors(
    iso: str,
) -> tuple[dict[str, dict[int, float]], dict[str, float]]:
    """Return ({zone: {year: delivered mean}}, {zone: anchor}) for ``iso``.

    The zone-resolved identification point of ``gas_offer_net_revenue_margin``.
    :func:`derive_anchor` reads ``_gas_series``, which is ISO-level: it carries
    the hub overlay but NOT the per-zone basis, which the solve applies later on
    the ``(n_gen, T)`` array (``data.fuel.basis.nyiso.apply_nyiso_zonal_gas_basis``,
    anchored so the REFERENCE zone is unchanged and every other zone shifts
    down). So on an ISO with a zonal basis the single anchor is the reference
    zone's level, while a unit outside that zone pays persistently less — and
    ``apply_gas_offer_margin``'s ``markup_hr × (anchor − fuel)`` then hands that
    unit a margin uplift the band multipliers were never calibrated to carry.
    The mechanism's own identity — *at ``fuel == anchor`` the reformed offer
    reduces EXACTLY to the registered band multiplier* — is a statement about a
    unit's OWN delivered fuel, so the anchor has to be measured on the same
    series that unit's fuel comes from.

    This applies the RUNTIME transform (never a re-derivation of it) to a
    synthetic one-gas-row-per-zone fleet, so the zonal levels here are by
    construction the levels the solve prices those units at.

    Rule-23 frozen derive, exactly like :func:`derive_anchor`: re-run ONLY when
    the underlying gas source data changes (``data/raw/gas-prices/`` workbooks,
    the ISO hub-basis series, or the per-zone hub table), and cite that data
    change in the re-derivation commit. NEVER because a price residual moved.
    """
    if iso not in ZONAL_BASIS_ISOS:
        raise SystemExit(
            f"{iso}: no per-zone delivered-gas basis is armed on this ISO's "
            "keeper, so its single anchor is already identified at the grain "
            "its units' fuel is drawn at — there is no zonal anchor to derive "
            "(rule 25: never transfer another ISO's zonal table)"
        )
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import FleetArrays
    from market_sim.data.fuel._shared import _GAS_FUEL_IDX
    from market_sim.data.fuel.basis import ZONAL_BASIS_APPLIERS

    zone_names = list(get_iso_config(iso).zone_names)
    n = len(zone_names)
    gas_idx = int(sorted(_GAS_FUEL_IDX)[0])
    base = ScenarioConfig(
        iso=iso, mode="backcast", hours=HOURS_PER_YEAR, **GAS_SERIES_FLAGS[iso]
    )
    apply_basis = ZONAL_BASIS_APPLIERS[iso]
    by_zone: dict[str, dict[int, float]] = {z: {} for z in zone_names}
    for year, hh in sorted(TRAIN_WINDOW_HH.items()):
        cfg = base.with_overrides(gas_price_override=hh)
        series = _gas_series(cfg, year, HOURS_PER_YEAR)
        prices = np.repeat(series[None, :], n, axis=0)
        # One synthetic gas row per zone: the applier keys only on
        # ``fuel_type_idx`` and ``zone_idx``, so this measures its transform
        # exactly as the solve applies it.
        fleet = FleetArrays(
            pmax=np.ones(n),
            pmin=np.zeros(n),
            heat_rate=np.full(n, 7.0),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.arange(n),
            fuel_type_idx=np.full(n, gas_idx),
            availability=np.ones((n, HOURS_PER_YEAR)),
            unit_ids=[f"probe_{z}" for z in zone_names],
            efficiency_bin=np.zeros(n, dtype=int),
            plant_code=np.zeros(n, dtype=int),
        )
        apply_basis(prices, fleet, cfg, year)
        for i, zone in enumerate(zone_names):
            by_zone[zone][year] = float(np.nanmean(prices[i]))
    anchors = {z: float(np.mean(list(v.values()))) for z, v in by_zone.items()}
    return by_zone, anchors


def _net_revenue_check(iso: str, anchor: float) -> None:
    """Print the fixed margins the anchor implies + the SOM-style cross-check."""
    from market_sim.data.offer_curves import gas_offer_margin_markup_mult
    from market_sim.pipeline.backcast_config import backcast_config

    # Resolve the ISO's DEFAULT backcast offer curve (base ternaries + per-ISO
    # merge + the phys_* keys), so this works uniformly — including ERCOT, whose
    # phys keys live in a phys-only _ERCOT_OFFER_CURVE deep-merged onto the
    # shared base (the recipe's --offer-curve overrides are NOT applied here;
    # this is the base-curve documentation cross-check, not the keeper's live
    # peak wall).
    curve = backcast_config(2024, iso, HOURS_PER_YEAR, anchor).offer_curve_by_group
    if not any(any(k.startswith("phys_") for k in bands) for bands in curve.values()):
        print(f"[net-revenue-check] no phys-keyed curve registered for {iso}")
        return
    # Class base heat rates from the ISO's CAMPD marginal-HR artifact (the
    # same measurement the phys_* keys come from).
    import csv

    base_hr_path = (
        Path(__file__).resolve().parents[2]
        / "data/raw/reference"
        / f"{iso.lower()}_campd_marginal_hr_summary.csv"
    )
    base_hr = {
        row["class"]: float(row["base_hr"])
        for row in csv.DictReader(open(base_hr_path))
    }
    print(f"\nFixed margins at anchor {anchor:.4f} $/MMBtu (markup x HR x anchor):")
    for cls, bands in sorted(curve.items()):
        hr = base_hr.get(cls)
        # Only the phys-keyed gas classes carry the mechanism (coal / neutral
        # classes have no phys_* keys → markup 0, skipped to keep the table tight).
        if hr is None or not any(k.startswith("phys_") for k in bands):
            continue
        margins = {}
        for suffix, mult_key in (
            ("committed", "committed"),
            ("econlo", "econ_low"),
            ("econhi", "econ_high"),
            ("peak", "peak"),
        ):
            mult = bands.get(mult_key)
            if mult is None:
                continue
            mk = gas_offer_margin_markup_mult(suffix, float(mult), bands)
            margins[mult_key] = mk * hr * anchor
        print(f"  {cls:12s} " + "  ".join(f"{k}={v:7.2f}" for k, v in margins.items()))
    # Offer-side Potomac-SOM cross-check (retirements.py net-revenue logic
    # inverted): the CT scarcity margin's implied cost-recovery run-hours
    # against a FOM-only going-forward cost.
    ct = curve.get("CT_PEAKER")
    if ct and "phys_peak" in ct:
        hr = base_hr["CT_PEAKER"]
        margin = gas_offer_margin_markup_mult("peak", float(ct["peak"]), ct) * hr
        margin_usd = margin * anchor
        fom = ScenarioConfig(iso=iso).fixed_om_gas_ct  # $/kW-yr
        if margin_usd > 0:
            hours = fom * 1000.0 / margin_usd
            print(
                f"\n[net-revenue-check] CT_PEAKER scarcity margin "
                f"{margin_usd:.1f} $/MWh recovers FOM-only GFC "
                f"({fom:.0f} $/kW-yr) over {hours:.0f} expected scarcity "
                "run-hours/yr — the missing-money construction "
                "(retirements.py::apply_economic_retirements, offer side)."
            )


def main() -> None:
    """Derive and print the anchor; optionally the margin table."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--iso", default="NEISO")
    parser.add_argument(
        "--net-revenue-check",
        action="store_true",
        help="Also print the per-band fixed margins the anchor implies and "
        "the SOM-style peaker cost-recovery cross-check (documentation only).",
    )
    parser.add_argument(
        "--by-zone",
        action="store_true",
        help="Also derive the ZONE-resolved anchors (ISOs whose keeper arms a "
        "per-zone delivered-gas basis; register in constants."
        "GAS_OFFER_MARGIN_ANCHOR_BY_ZONE, cite this script).",
    )
    args = parser.parse_args()
    year_means, anchor = derive_anchor(args.iso)
    print(f"{args.iso} delivered-gas anchor derivation (train window):")
    for year, mean in year_means.items():
        print(f"  {year}: mean delivered = {mean:.4f} $/MMBtu")
    print(
        f"ANCHOR = {anchor:.4f} $/MMBtu  (register in constants."
        "GAS_OFFER_MARGIN_ANCHOR_BY_ISO, cite this script)"
    )
    if args.by_zone:
        by_zone, anchors = derive_zonal_anchors(args.iso)
        print(
            f"\n{args.iso} ZONE-resolved anchors (the same series with each "
            "zone's own measured basis applied — what its gas units pay):"
        )
        for zone in sorted(anchors, key=lambda z: -anchors[z]):
            years = "  ".join(f"{y}: {v:.4f}" for y, v in sorted(by_zone[zone].items()))
            print(
                f"  {zone:<16} {years}   ANCHOR = {anchors[zone]:.4f} "
                f"(ISO anchor {anchor:+.4f} -> {anchors[zone] - anchor:+.4f})"
            )
        print(
            "  (register in constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE, cite "
            "this script)"
        )
    if args.net_revenue_check:
        _net_revenue_check(args.iso, anchor)


if __name__ == "__main__":
    main()
