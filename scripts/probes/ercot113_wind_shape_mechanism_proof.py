"""ERCOT-113 Task B: no-LP proof that the per-zone wind SHAPE fires and that it
preserves the ISO aggregate exactly.

Two of the pre-committed criteria in
``results/calibration/PRECOMMIT-ercot113-wind-zone-shape-2026-07-26.md`` can be
established at the DATA layer, without a solve:

* **W0 arming proof** — the gated loader returns a per-zone SHAPE and that shape
  materially relocates wind between zones (the nocturnal-jet West/Panhandle
  against the Gulf-sea-breeze South).
* **W1 aggregate-preservation falsifier** — ``_redistribute_preserving_total``
  holds the ISO-wide total in EVERY hour, so annual wind energy and the
  ISO-wide bound cannot move. This is the invariant that makes annual wind TWh
  an invalid scoring criterion for this lane.

This matters because the ERCOT calibration bundles carry no zone-resolved wind
sidecar (only ISO-wide ``class_hourly`` and per-zone ``system``), so a moved
wind split is not directly readable from a bundle. Running the mechanism here
against the committed shape artifacts proves the behaviour independently.

The ISO-wide CF series is a deterministic pseudo-random stand-in: the
redistribution is *linear in the system series*, so the per-zone shares and the
preservation invariant do not depend on which profile is used. Capacities are
the model's ERCOT zone order.

Usage:
    python scripts/probes/ercot113_wind_shape_mechanism_proof.py --year 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import wind_shape_dir  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.renewables import (  # noqa: E402
    _redistribute_preserving_total,
    _wind_zone_reanalysis_shapes,
)

HOURS = 8760
# Indicative ERCOT zone nameplate MW, in the shape artifact's column order.
# Only the RELATIVE split matters here — the invariant and the per-zone shares
# are scale-free — so these are order-of-magnitude, not a calibrated input.
_ZONE_CAP_MW = (12000.0, 7000.0, 9000.0, 900.0, 6000.0, 700.0, 1500.0)
_PRESERVATION_TOL_MW = 1e-6


def main(argv: list[str] | None = None) -> int:
    """Print the per-zone reallocation and the hourly preservation invariant."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args(argv)

    d = wind_shape_dir("ERCOT")
    if d is None:
        print("ERCOT has no registered wind-shape directory")
        return 1
    path = d / f"ercot_{args.year}_wind_zone_shape.parquet"
    if not path.exists():
        print(f"missing shape artifact: {path}")
        return 1
    zones = [c for c in pd.read_parquet(path).columns if c != "hour"]

    off = _wind_zone_reanalysis_shapes(
        "ERCOT", "wind", zones, args.year, config=ScenarioConfig()
    )
    shapes = _wind_zone_reanalysis_shapes(
        "ERCOT", "wind", zones, args.year,
        config=ScenarioConfig(ercot_wind_zone_shape=True),
    )
    print(f"gate OFF -> {off!r}  (must be None)")
    if shapes is None:
        print("gate ON returned None — mechanism INERT")
        return 1
    print(f"gate ON  -> shape {shapes.shape}")

    cap = np.array(_ZONE_CAP_MW[: len(zones)], dtype=float)
    ramp = np.ones((len(zones), HOURS))
    cf = np.clip(np.random.default_rng(0).random(HOURS), 0.0, 1.0)

    cf_flat = cf[None, :] * ramp                      # legacy: one profile, all zones
    cf_shaped = _redistribute_preserving_total(cf, cap, ramp, shapes)
    mw_flat = cap[:, None] * cf_flat
    mw_shaped = cap[:, None] * cf_shaped

    print(f"\n{'zone':<16}{'flat TWh':>10}{'shaped TWh':>12}{'delta':>11}{'%':>8}")
    for i, z in enumerate(zones):
        f, s = mw_flat[i].sum() / 1e6, mw_shaped[i].sum() / 1e6
        print(f"{z:<16}{f:10.3f}{s:12.3f}{s - f:+11.3f}{(s / f - 1) * 100:+7.1f}%")

    worst = float(np.abs(mw_shaped.sum(axis=0) - mw_flat.sum(axis=0)).max())
    print(f"\nISO total  flat {mw_flat.sum() / 1e6:.4f} TWh   "
          f"shaped {mw_shaped.sum() / 1e6:.4f} TWh")
    print(f"max |hourly ISO-total difference| = {worst:.3e} MW")
    ok = worst < _PRESERVATION_TOL_MW
    print(f"W1 aggregate preserved EVERY hour: {ok}")

    hod = np.arange(HOURS) % 24
    night, aft = hod < 6, (hod >= 12) & (hod < 18)
    print("\nDiurnal signature (share of ISO wind held by the zone):")
    print(f"{'zone':<16}{'night flat':>12}{'night shaped':>14}"
          f"{'aft flat':>11}{'aft shaped':>12}")
    for i, z in enumerate(zones):
        print(
            f"{z:<16}"
            f"{mw_flat[i, night].sum() / mw_flat[:, night].sum():12.3f}"
            f"{mw_shaped[i, night].sum() / mw_shaped[:, night].sum():14.3f}"
            f"{mw_flat[i, aft].sum() / mw_flat[:, aft].sum():11.3f}"
            f"{mw_shaped[i, aft].sum() / mw_shaped[:, aft].sum():12.3f}"
        )
    print(
        "\nREAD: the flat columns are identical by construction (one profile on every\n"
        "zone), so any night-vs-afternoon separation in the shaped columns is the\n"
        "mechanism firing — the nocturnal-jet West/Panhandle gaining night share while\n"
        "the Gulf-sea-breeze South loses it — with the ISO total untouched every hour."
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
