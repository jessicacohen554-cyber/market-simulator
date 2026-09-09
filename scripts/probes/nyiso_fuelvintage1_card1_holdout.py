"""CARD 1 across the HOLDOUT years — is the EP-level seam byte-identical there too?

The session FINDING proved ``gas_electric_power_monthly_level`` LP-inert for NYISO
in 2023/2024/2025 (``fuel_prices`` and ``mc_base`` byte-identical), on the
mechanism reason that ``gas_hub_basis_overlay`` (Transco Z6) covers 12/12 months
of EVERY year 2019-2025 and is applied LAST. This extends the MEASUREMENT to the
years the validation touchpoints actually spend, so the touchpoint recipe question
("is a flag-off touchpoint the same solve as a flag-on one?") is answered by
measurement rather than by inference from the coverage table.

It also RE-DERIVES 2023 through ``replay_keeper.run_year_kwargs`` — the STRICT
meta->kwarg mapping — rather than the parameter-name filter the phase-0 probe
used, so the earlier result is confirmed on the sanctioned reconstruction.

Zero LP: ``run_year(fleet_only=True)`` builds the fleet, fuel prices and offers
and returns before any matrix is built. Rule 22 ``[R-HOLDOUT]``: inspecting an
input is not a spend -- only solving, scoring or registering a year is.

Usage:
    uv run python scripts/probes/nyiso_fuelvintage1_card1_holdout.py 2021 2022
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402

BUNDLE = REPO / "results/calibration/nyiso213_summer_seam"


def build(year: int, arm: bool) -> dict:
    """Return ``run_year``'s ``fleet_only`` payload for one year and one side.

    Args:
        year: Solve year to build for.
        arm: True to arm ``gas_electric_power_monthly_level`` through the same
            generic ``prb_overrides`` channel ``replay_keeper --set`` uses.

    Returns:
        The ``fleet_only`` payload dict.
    """
    meta = json.loads((BUNDLE / "meta.json").read_text())
    call = rk.run_year_kwargs(meta)
    call.update(
        year=year,
        iso=meta["iso"],
        hours=8760,
        fleet_only=True,
        gas_price=meta["gas_prices"][str(min(max(year, 2023), 2025))],
        ttc_overrides={},
    )
    if arm:
        call["prb_overrides"] = dict(call.get("prb_overrides") or {})
        call["prb_overrides"]["gas_electric_power_monthly_level"] = True
    return rc.run_year(**call)


def main() -> None:
    """Measure the armed-vs-control delta on the LP's own input arrays."""
    print(f"{'year':6s} {'n_gen':>6s} {'max|d fuel_prices|':>20s} {'max|d mc_base|':>16s}  verdict")
    for year in (int(a) for a in sys.argv[1:]):
        ctl = build(year, False)
        arm = build(year, True)
        df = float(
            np.abs(
                np.asarray(arm["fuel_prices"], float) - np.asarray(ctl["fuel_prices"], float)
            ).max()
        )
        dm = float(
            np.abs(np.asarray(arm["mc_base"], float) - np.asarray(ctl["mc_base"], float)).max()
        )
        ok = "BYTE-IDENTICAL" if (df == 0.0 and dm == 0.0) else "*** MOVED ***"
        n = np.asarray(ctl["fuel_prices"]).shape[0]
        print(f"{year:<6d} {n:6d} {df:20.10f} {dm:16.10f}  {ok}")


if __name__ == "__main__":
    main()
