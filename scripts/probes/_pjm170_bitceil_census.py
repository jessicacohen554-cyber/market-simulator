"""Zero-LP phase-0 census for the pjm-170 coal-sigmoid `ceil` card.

Rule 29 ``[R-SCREEN]`` clause (0): an offer-array delta that costs ~minutes and
can kill an arm before any LP is spent. Two measurements, both on the keeper's
own resolved config through ``run_calibration.run_year(fleet_only=True)`` — the
same resolution path the solve uses, never a hand reconstruction:

**A. The FOOTPRINT census** (the screen-year selector declared in
``docs/handoffs/PRECOMMIT-pjm170-coal-sigmoid-ceil-2026-09-07.md`` §4). For each
year, the resolved PJM bituminous passthrough under the control ``ceil`` and
under the arm ``ceil``, and the declared statistic
``mean |passthrough_arm(t) - passthrough_control(t)|``. Reported beside it, and
NOT a selector: the on-``ceil`` occupancy. No price, no actual, no residual is
read anywhere in this file.

**B. The S4a DIRECT PRICING CONFINEMENT measurement and the S3 prediction.**
Assembles the P0 offer array ``mc_base`` for the screen year twice — control
recipe and arm recipe — and diffs it cell by cell, classifying every changed
``(generator, hour)`` cell as inside or outside the set the mechanism may reach
by construction (PJM coal, ``coal_supply == "bituminous"``, tranche above
must-run: not ``_mustrun``, not ``_sync``). Emits the mean ``ΔMC`` over the
changed cells, which is the value PRECOMMIT §7 fixes as the S3 prediction.

Usage:
    python scripts/probes/_pjm170_bitceil_census.py \
        [--bundle results/calibration/pjm169_tp2022_2021_f2arm] \
        [--years 2021 2022 2023 2024 2025] [--screen-year 2022] [--json OUT]
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

from market_sim.data.fuel.trajectories import (  # noqa: E402
    _gas_series,
    coal_passthrough_series,
    coal_sigmoid_params,
)
from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402

HOURS = 8760
#: Gas prices the keeper and its touchpoint bundle recorded, by year (pjm-169).
GAS_PRICE_BY_YEAR: dict[int, float] = {
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}
TRAIN_YEARS = (2023, 2024, 2025)
#: The one declared delta (PRECOMMIT §3).
ARM_CEIL = 1.0
#: Supplies whose curves must NOT move (PRECOMMIT gate S1).
OTHER_SUPPLIES = ("prb", "subbituminous", "lignite", "waste")


def build_config(bundle: Path, year: int, arm: bool, want_arrays: bool = False):
    """Return the resolved config (and, optionally, the fleet/offer arrays).

    Built through the same ``run_calibration.run_year`` entry the solve uses,
    in ``fleet_only`` mode, so every recipe override resolves exactly as it does
    in a real solve. The arm applies the ONE declared delta through the generic
    ``prb_overrides`` ScenarioConfig channel — the same route
    ``replay_keeper --set`` uses, so the census and the screen resolve the
    identical config.

    Args:
        bundle: control bundle directory holding ``meta.json``.
        year: solve year to build for.
        arm: when True, apply ``coal_bit_passthrough_ceil = ARM_CEIL``.
        want_arrays: when True, return the whole ``fleet_only`` payload.

    Returns:
        The resolved ``ScenarioConfig``, or the full payload when *want_arrays*.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    if arm:
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"] = dict(kwargs["prb_overrides"])
        kwargs["prb_overrides"]["coal_bit_passthrough_ceil"] = ARM_CEIL
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
    out = rc.run_year(**call)
    return out if want_arrays else out["config"]


def footprint_row(cfg_ctl, cfg_arm, year: int) -> dict:
    """Return the year's footprint row (PRECOMMIT §4's declared statistic).

    Args:
        cfg_ctl: resolved control ``ScenarioConfig`` for *year*.
        cfg_arm: resolved arm ``ScenarioConfig`` for *year*.
        year: the solve year.

    Returns:
        Passthrough statistics for both arms plus the declared footprint.
    """
    gas = np.asarray(_gas_series(cfg_ctl, year, HOURS), dtype=float)
    p_ctl = np.asarray(
        coal_passthrough_series(cfg_ctl, year, HOURS, "bituminous"), dtype=float
    )
    p_arm = np.asarray(
        coal_passthrough_series(cfg_arm, year, HOURS, "bituminous"), dtype=float
    )
    par_ctl = coal_sigmoid_params(cfg_ctl, "bituminous")
    par_arm = coal_sigmoid_params(cfg_arm, "bituminous")
    d = p_arm - p_ctl
    # On-`ceil` occupancy: within 1e-3 of the asymptote (pjm-169's convention).
    on_ceil_ctl = float(np.mean(p_ctl >= par_ctl["ceil"] - 1e-3))
    return {
        "year": year,
        "gas_mean": float(gas.mean()),
        "params_control": par_ctl,
        "params_arm": par_arm,
        "pt_control_mean": float(p_ctl.mean()),
        "pt_control_max": float(p_ctl.max()),
        "pt_arm_mean": float(p_arm.mean()),
        "pt_arm_max": float(p_arm.max()),
        # THE DECLARED FOOTPRINT STATISTIC (PRECOMMIT §4).
        "footprint_mean_abs_delta": float(np.abs(d).mean()),
        "footprint_max_abs_delta": float(np.abs(d).max()),
        # Reported, NOT a selector.
        "hours_on_ceil_control_frac": on_ceil_ctl,
        # Gate S2 evidence.
        "s2_arm_max_le_one": bool(p_arm.max() <= 1.0 + 1e-9),
        "s2_arm_never_above_control": bool(np.all(p_arm <= p_ctl + 1e-12)),
    }


def other_supplies_identical(cfg_ctl, cfg_arm, year: int) -> dict:
    """Return per-supply byte-identity of every non-bituminous coal curve (S1)."""
    out = {}
    for supply in OTHER_SUPPLIES:
        a = coal_passthrough_series(cfg_ctl, year, HOURS, supply)
        b = coal_passthrough_series(cfg_arm, year, HOURS, supply)
        a_arr, b_arr = np.atleast_1d(np.asarray(a, float)), np.atleast_1d(
            np.asarray(b, float)
        )
        out[supply] = bool(a_arr.shape == b_arr.shape and np.array_equal(a_arr, b_arr))
    return out


def _directly_priced_mask(fleet) -> np.ndarray:
    """Return the boolean row mask of tranches the mechanism may reach.

    PJM coal generators tagged ``bituminous`` whose tranche is above must-run —
    ``campd_tranche_fuel_frac`` returns 0.0 for ``_mustrun`` and 1.0 for
    ``_sync`` regardless of the supply curve, so neither can move.
    """
    return np.array(
        [
            (g.fuel_type == "coal")
            and (getattr(g, "coal_supply", "") == "bituminous")
            and not g.unit_id.endswith("_mustrun")
            and not g.unit_id.endswith("_sync")
            for g in fleet
        ],
        dtype=bool,
    )


def offer_delta(bundle: Path, year: int) -> dict:
    """Return the S4a confinement measurement and the S3 ΔMC prediction.

    Args:
        bundle: control bundle directory.
        year: the screen year.

    Returns:
        Cell-level classification of the control-vs-arm offer-array diff.
    """
    ctl = build_config(bundle, year, arm=False, want_arrays=True)
    arm = build_config(bundle, year, arm=True, want_arrays=True)
    fleet = ctl["fleet"]
    mc_c = np.asarray(ctl["mc_base"], dtype=float)
    mc_a = np.asarray(arm["mc_base"], dtype=float)
    if mc_c.shape != mc_a.shape:
        raise SystemExit(f"offer-array shape mismatch {mc_c.shape} vs {mc_a.shape}")
    if len(fleet) != mc_c.shape[0]:
        raise SystemExit("fleet/offer-array row mismatch")
    if [g.unit_id for g in fleet] != [g.unit_id for g in arm["fleet"]]:
        raise SystemExit("fleet row ORDER differs between control and arm")
    diff = mc_a - mc_c
    changed = np.abs(diff) > 0.0
    mask = _directly_priced_mask(fleet)
    inside = changed & mask[:, None]
    outside = changed & ~mask[:, None]
    rows_changed = np.flatnonzero(changed.any(axis=1))
    rows_outside = np.flatnonzero(outside.any(axis=1))
    d_in = diff[inside]
    return {
        "year": year,
        "n_gen_rows": int(mc_c.shape[0]),
        "hours": int(mc_c.shape[1]),
        "n_directly_priced_rows": int(mask.sum()),
        "n_rows_changed": int(rows_changed.size),
        "n_rows_changed_outside_set": int(rows_outside.size),
        "unit_ids_changed_outside_set": [
            fleet[i].unit_id for i in rows_outside[:20]
        ],
        "n_cells_changed": int(changed.sum()),
        "n_cells_changed_outside_set": int(outside.sum()),
        # THE S3 PREDICTION, fixed before the solve.
        "mean_delta_mc_usd_mwh": float(d_in.mean()) if d_in.size else 0.0,
        "min_delta_mc_usd_mwh": float(d_in.min()) if d_in.size else 0.0,
        "max_delta_mc_usd_mwh": float(d_in.max()) if d_in.size else 0.0,
        "directly_priced_pmax_mw": float(
            sum(float(g.pmax_mw or 0.0) for g, m in zip(fleet, mask) if m)
        ),
        "s4a_pass": bool(outside.sum() == 0),
    }


def main() -> None:
    """CLI: print the pjm-170 phase-0 census and optionally write it as JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/pjm169_tp2022_2021_f2arm")
    ap.add_argument("--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--screen-year", type=int, default=2022)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    bundle = Path(args.bundle)
    rows, ident = [], {}
    for year in args.years:
        cfg_c = build_config(bundle, year, arm=False)
        cfg_a = build_config(bundle, year, arm=True)
        rows.append(footprint_row(cfg_c, cfg_a, year))
        ident[year] = other_supplies_identical(cfg_c, cfg_a, year)

    print("\nA. FOOTPRINT CENSUS — declared statistic: mean |Δ passthrough|")
    print(
        f"{'year':>6} {'gas':>7} {'pt_ctl':>8} {'pt_arm':>8} "
        f"{'FOOTPRINT':>10} {'xin-win':>8} {'on-ceil':>8}"
    )
    in_win = max(
        r["footprint_mean_abs_delta"] for r in rows if r["year"] in TRAIN_YEARS
    )
    for r in rows:
        print(
            f"{r['year']:>6} {r['gas_mean']:>7.3f} {r['pt_control_mean']:>8.4f} "
            f"{r['pt_arm_mean']:>8.4f} {r['footprint_mean_abs_delta']:>10.4f} "
            f"{r['footprint_mean_abs_delta'] / in_win:>8.2f} "
            f"{r['hours_on_ceil_control_frac'] * 100:>7.1f}%"
        )
    winner = max(rows, key=lambda r: r["footprint_mean_abs_delta"])["year"]
    print(f"\n  largest footprint: {winner}  (declared screen year: {args.screen_year})")
    print(f"  S2 arm max <= 1.0 : {all(r['s2_arm_max_le_one'] for r in rows)}")
    print(f"  S2 arm <= control : {all(r['s2_arm_never_above_control'] for r in rows)}")
    print(f"  S1 other supplies identical: {all(all(v.values()) for v in ident.values())}")

    print("\nB. S4a DIRECT PRICING CONFINEMENT + S3 prediction")
    od = offer_delta(bundle, args.screen_year)
    for k, v in od.items():
        print(f"  {k}: {v}")

    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {"footprint": rows, "other_supplies_identical": ident, "offer_delta": od},
                indent=1,
                default=str,
            )
        )
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
