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
# harness (backcast_config): monthly EIA-923 actuals + the ISO's measured hub
# basis overlay. The daily within-month shape is mean-preserved to the
# monthly hub level by construction, so the ANNUAL mean is identical with or
# without the daily leg.
GAS_SERIES_FLAGS: dict[str, dict[str, bool]] = {
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


def _net_revenue_check(iso: str, anchor: float) -> None:
    """Print the fixed margins the anchor implies + the SOM-style cross-check."""
    from market_sim.data.offer_curves import gas_offer_margin_markup_mult
    from market_sim.pipeline.backcast_config import _NEISO_OFFER_CURVE

    curves = {"NEISO": _NEISO_OFFER_CURVE}
    if iso not in curves:
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
    for cls, bands in sorted(curves[iso].items()):
        hr = base_hr.get(cls)
        if hr is None:
            continue
        margins = {}
        for suffix, mult_key in (
            ("committed", "committed"),
            ("econlo", "econ_low"),
            ("econhi", "econ_high"),
            ("peak", "peak"),
        ):
            mult = float(bands[mult_key])
            mk = gas_offer_margin_markup_mult(suffix, mult, bands)
            margins[mult_key] = mk * hr * anchor
        print(f"  {cls:12s} " + "  ".join(f"{k}={v:7.2f}" for k, v in margins.items()))
    # Offer-side Potomac-SOM cross-check (retirements.py net-revenue logic
    # inverted): the CT scarcity margin's implied cost-recovery run-hours
    # against a FOM-only going-forward cost.
    ct = curves[iso].get("CT_PEAKER")
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
    args = parser.parse_args()
    year_means, anchor = derive_anchor(args.iso)
    print(f"{args.iso} delivered-gas anchor derivation (train window):")
    for year, mean in year_means.items():
        print(f"  {year}: mean delivered = {mean:.4f} $/MMBtu")
    print(
        f"ANCHOR = {anchor:.4f} $/MMBtu  (register in constants."
        "GAS_OFFER_MARGIN_ANCHOR_BY_ISO, cite this script)"
    )
    if args.net_revenue_check:
        _net_revenue_check(args.iso, anchor)


if __name__ == "__main__":
    main()
