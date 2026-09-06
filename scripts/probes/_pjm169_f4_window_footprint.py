"""Zero-LP phase-0 footprint census for the pjm-169 F4 hypothesis.

F4 asks whether the PJM keeper's OFFER-ORDERING constants, all identified on
the 2023-2025 training window, are being extrapolated onto 2021/2022 fuel
regimes their identification data never visited (rule 29 ``[R-SCREEN]``
clause 0 -- an offer-array delta that costs seconds and can kill an arm before
any LP is spent).

Two constants are in scope, and this probe measures BOTH at the grain the
solve applies them:

* ``constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"]`` (3.3483 $/MMBtu), the
  identification point of ``apply_gas_offer_margin``'s net-revenue markup
  compression ``mc += markup_hr x (anchor - fuel)``. Outside the window the
  ``(anchor - fuel)`` term is a linear extrapolation with no saturation.
* ``scenarios.COAL_SIGMOID_DEFAULTS[("PJM", <supply>)]``, the gas-keyed coal
  passthrough logistic. Its ``ceil`` asymptote is (per that table's own
  docstring) "pinned by the dearest observed year" -- so the question is
  whether the 2023-2025 window ever REACHES it, and what fraction of a
  2021/2022 year sits on it.

Reports, per year, the quantities a PRECOMMIT needs to choose a screen year on
FOOTPRINT rather than on any residual: the delivered gas series the offer path
prices against, the anchor gap ``|anchor - fuel|``, and the resolved coal
passthrough. NO price, no actual, no residual is read anywhere in this file.

Usage:
    python scripts/probes/_pjm169_f4_window_footprint.py \
        [--bundle results/calibration/pjm_debugb_inputclock_A] \
        [--years 2021 2022 2023 2024 2025] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402

from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO  # noqa: E402
from market_sim.data.fuel.trajectories import (  # noqa: E402
    _gas_series,
    coal_passthrough_series,
    coal_sigmoid_params,
)
from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402

HOURS = 8760
#: The gas prices the keeper and its touchpoint bundle recorded, by year.
GAS_PRICE_BY_YEAR: dict[int, float] = {
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}
TRAIN_YEARS = (2023, 2024, 2025)


def keeper_config(bundle: Path, year: int):
    """Return the keeper recipe's resolved ScenarioConfig for *year*.

    Built through the same ``run_calibration.run_year`` entry the solve uses,
    in ``fleet_only`` mode, so every CLI-armed override (notably
    ``gas_offer_margin`` resolving the ISO anchor) is applied exactly as it is
    in a real solve rather than reconstructed by hand.

    Args:
        bundle: keeper bundle directory holding ``meta.json``.
        year: solve year to build the config for.

    Returns:
        The resolved ``ScenarioConfig``.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    sig = set(rc.run_year.__code__.co_varnames[: rc.run_year.__code__.co_argcount])
    call = {k: v for k, v in kwargs.items() if k in sig}
    call.update(
        year=year,
        iso=meta["iso"],
        hours=HOURS,
        fleet_only=True,
        gas_price=GAS_PRICE_BY_YEAR[year],
        ttc_overrides={},
    )
    return rc.run_year(**call)["config"]


def census_year(config, year: int) -> dict:
    """Return the F4 footprint row for one year.

    Args:
        config: resolved keeper ``ScenarioConfig`` for *year*.
        year: the solve year.

    Returns:
        A dict of the anchor-gap and coal-passthrough statistics.
    """
    anchor = float(GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"])
    gas = np.asarray(_gas_series(config, year, HOURS), dtype=float)
    gap = anchor - gas
    row = {
        "year": year,
        "anchor_mmbtu": anchor,
        "gas_mean": float(gas.mean()),
        "gas_min": float(gas.min()),
        "gas_max": float(gas.max()),
        # THE FOOTPRINT METRIC: how far outside its identification point the
        # net-revenue margin term is asked to operate. Signed mean says which
        # way the markup is pushed; abs-max says how far.
        "gap_mean": float(gap.mean()),
        "gap_absmax": float(np.abs(gap).max()),
        "hours_gas_above_anchor": int((gas > anchor).sum()),
        "coal": {},
    }
    for supply in ("bituminous", "subbituminous"):
        params = coal_sigmoid_params(config, supply)
        if params is None:
            continue
        pt = np.asarray(
            coal_passthrough_series(config, year, HOURS, supply), dtype=float
        )
        ceil = float(params["ceil"])
        row["coal"][supply] = {
            "params": {k: float(v) for k, v in params.items()},
            "passthrough_mean": float(pt.mean()),
            "passthrough_max": float(pt.max()),
            # Saturation is the identification question: an hour within 1 % of
            # the ceiling is priced by an asymptote, not by the data.
            "frac_hours_within_1pct_of_ceil": float(
                (pt >= ceil - 0.01 * (ceil - float(params["floor"]))).mean()
            ),
        }
    return row


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/pjm_debugb_inputclock_A")
    ap.add_argument("--years", nargs="+", type=int, default=sorted(GAS_PRICE_BY_YEAR))
    ap.add_argument("--json", default=None, help="write the census to this path")
    args = ap.parse_args()

    bundle = Path(args.bundle)
    rows = [census_year(keeper_config(bundle, y), y) for y in args.years]

    train = [r for r in rows if r["year"] in TRAIN_YEARS]
    train_absmax = max((r["gap_absmax"] for r in train), default=float("nan"))
    print(f"\nF4 phase-0 footprint census — keeper {bundle.name}")
    print(f"in-window (2023-2025) max |anchor - fuel| = {train_absmax:.4f} $/MMBtu\n")
    hdr = f"{'year':>6} {'gas_mean':>9} {'gas_max':>8} {'gap_mean':>9} {'gap_absmax':>11} {'xWindow':>8} {'h>anchor':>9}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        ratio = r["gap_absmax"] / train_absmax if train_absmax else float("nan")
        print(
            f"{r['year']:>6} {r['gas_mean']:>9.3f} {r['gas_max']:>8.3f} "
            f"{r['gap_mean']:>9.3f} {r['gap_absmax']:>11.4f} {ratio:>7.2f}x "
            f"{r['hours_gas_above_anchor']:>9}"
        )
    print("\ncoal passthrough (gas-keyed sigmoid), by supply:")
    for r in rows:
        for supply, c in r["coal"].items():
            print(
                f"  {r['year']} {supply:<14} mean {c['passthrough_mean']:.4f} "
                f"max {c['passthrough_max']:.4f} ceil {c['params']['ceil']:.3f} "
                f"gas_mid {c['params']['gas_mid']:.3f} "
                f"hours-on-ceiling {c['frac_hours_within_1pct_of_ceil']*100:.1f}%"
            )
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
