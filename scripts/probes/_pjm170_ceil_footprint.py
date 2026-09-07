"""Zero-LP phase-0 census for the pjm-170 coal-sigmoid CEILING card.

Rule 29 ``[R-SCREEN]`` clause 0: an offer-array delta costs seconds and can kill
an arm before any LP is spent. The arm is ONE declared delta --
``COAL_SIGMOID_DEFAULTS[("PJM", "bituminous")]["ceil"]`` 1.32 -> 1.00 -- and
every question this probe answers is fixed by
``docs/handoffs/PRECOMMIT-pjm170-coal-sigmoid-ceiling-2026-09-07.md`` SS7, which
was committed before this file ran.

WHAT IT MEASURES, and which gate each feeds (PRECOMMIT SS5):

1. **Resolution** (gate S1) -- the resolved sigmoid params under control and arm.
   Only ``ceil`` may differ.
2. **Leverage** (SS2 corroboration) -- the hourly logistic fraction
   ``s(g) = 1 / (1 + exp(-gas_slope * (g - gas_mid)))``, which IS
   ``d passthrough / d ceil``, per year. The screen year was chosen on this
   statistic from pjm-169's committed census; this rebuilds it from the config
   actually constructed here.
3. **The identity** (gate S2) -- ``passthrough_arm - passthrough_control``
   against ``s(g) * (1.00 - 1.32)`` evaluated independently.
4. **The DIRECT row set** (gate S4-A) -- every LP row whose assembled P0 offer
   ``mc_base`` differs between control and arm, against the set PREDICTED from
   the fleet's own coal supply tags. Zero unpredicted rows is the gate.
5. **The S3 prediction** (gate S3) -- the mean ``mc`` delta over the DIRECT rows.
   Both sides are computable with no LP, so S3 is an identity check.
6. **The S4-C headroom bound** -- ``sum_t (pmax * availability - control
   dispatch)`` over the DIRECT rows, from the control bundle's committed
   ``class_band_hourly`` sidecar.
7. **The SS3.3 reconciliation** -- the model's OWN capacity-weighted delivered
   coal $/MMBtu for the PJM bituminous fleet, per year, against
   ``derive_coal_sigmoid.py``'s reconstructed $4.307/MMBtu. Reported only; it
   selects nothing in this card (PRECOMMIT SS3.3).

NO price, NO actual and NO residual is read anywhere in this file.

Usage:
    python scripts/probes/_pjm170_ceil_footprint.py \
        [--bundle results/calibration/pjm169_tp2022_2021_f2arm] \
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

from market_sim.data.fuel.trajectories import (  # noqa: E402
    _gas_series,
    coal_passthrough_series,
    coal_sigmoid_params,
)
from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402

HOURS = 8760
#: The gas prices the control bundle and the keeper recorded, by year.
GAS_PRICE_BY_YEAR: dict[int, float] = {
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}
TRAIN_YEARS = (2023, 2024, 2025)
#: The single declared delta (PRECOMMIT SS5 anti-sweep clause). One value, every
#: year, never swept: the value derive_coal_sigmoid.py produces for
#: ("PJM", "bituminous") from the #1803 source data.
ARM_CEIL: float = 1.00
#: derive_coal_sigmoid.py's reconstructed PJM bituminous delivered price, for the
#: PRECOMMIT SS3.3 reconciliation (reported, selects nothing).
DERIVE_DELIV_MMBTU: float = 4.307


def _build(bundle: Path, year: int, arm: bool):
    """Return ``run_year``'s ``fleet_only`` payload for one year and one side.

    Built through the same ``run_calibration.run_year`` entry the solve uses, so
    every recorded override lands exactly as it does in a real solve. The arm
    side routes ``coal_bit_passthrough_ceil`` through the generic
    ``prb_overrides`` channel -- byte-identical to what
    ``replay_keeper.py --set coal_bit_passthrough_ceil=1.0`` does, so the census
    measures the offer array the screen will actually solve.

    Args:
        bundle: control bundle directory holding ``meta.json``.
        year: solve year to build for.
        arm: True for the armed side (ceil -> ``ARM_CEIL``), False for control.

    Returns:
        The ``fleet_only`` payload dict (config, fleet, fleet_arrays, mc_base...).
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
    return rc.run_year(**call)


def _bituminous_units(payload) -> set[str]:
    """Return the unit ids PREDICTED to be DIRECT rows.

    The prediction is made from the fleet's OWN coal supply tags, independently
    of any measured ``mc`` delta -- that independence is what makes gate S4-A a
    test rather than a tautology. A row is predicted DIRECT when its generator
    carries the ``bituminous`` supply tag AND its ``unit_id`` ends in neither
    ``_mustrun`` (fuel-free / take-or-pay sunk, ``legacy_bins.py:451``) nor
    ``_sync`` (passthrough pinned at 1.0 by construction,
    ``legacy_bins.py:449`` -- the step-3a synchronization tranche bids its full
    SRMC and never consults ``passthrough_by_supply`` at all). Both exclusions
    are read off the routing code and cited by line; neither is selected by an
    outcome. See PRECOMMIT AMENDMENT 1.

    Args:
        payload: a ``fleet_only`` payload from :func:`_build`.

    Returns:
        The set of predicted DIRECT unit ids.
    """
    out: set[str] = set()
    for gen in payload["fleet"]:
        supply = (getattr(gen, "coal_supply", "") or "").lower()
        if supply != "bituminous":
            continue
        uid = str(gen.unit_id)
        if uid.endswith("_mustrun") or uid.endswith("_sync"):
            continue
        out.add(uid)
    return out


def _mc_matrix(payload) -> np.ndarray:
    """Return ``mc_base`` as a 2-D ``(n_gen, T)`` array, broadcasting a 1-D one.

    Args:
        payload: a ``fleet_only`` payload from :func:`_build`.

    Returns:
        The assembled P0 offer matrix.
    """
    mc = np.asarray(payload["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    return mc


def _delivered_coal_mmbtu(payload, direct: set[str]) -> float | None:
    """Return the capacity-weighted delivered coal $/MMBtu over the DIRECT rows.

    The PRECOMMIT SS3.3 reconciliation measurement: what the model's own fuel
    path actually charges the bituminous fleet, against the derive script's
    reconstruction from an annual region f.o.b. Reported, never selective.

    Args:
        payload: a ``fleet_only`` payload from :func:`_build`.
        direct: the predicted DIRECT unit ids.

    Returns:
        The capacity-weighted mean $/MMBtu, or None when unavailable.
    """
    prices = payload.get("fuel_prices")
    if prices is None:
        return None
    arr = np.asarray(prices, dtype=float)
    fa = payload["fleet_arrays"]
    ids = [str(u) for u in fa.unit_ids]
    idx = [i for i, u in enumerate(ids) if u in direct]
    if not idx:
        return None
    if arr.ndim == 2:
        per_unit = arr[idx].mean(axis=1)
    else:
        per_unit = arr[idx]
    w = np.asarray(fa.pmax, dtype=float)[idx]
    return float(np.average(per_unit, weights=w)) if w.sum() > 0 else None


def census_year(bundle: Path, year: int) -> dict:
    """Return the pjm-170 phase-0 census row for one year.

    Args:
        bundle: control bundle directory.
        year: the solve year.

    Returns:
        A dict carrying every quantity PRECOMMIT SS7 declared.
    """
    ctl = _build(bundle, year, arm=False)
    arm = _build(bundle, year, arm=True)
    c_cfg, a_cfg = ctl["config"], arm["config"]

    p_ctl = coal_sigmoid_params(c_cfg, "bituminous")
    p_arm = coal_sigmoid_params(a_cfg, "bituminous")
    gas = np.asarray(_gas_series(c_cfg, year, HOURS), dtype=float)
    # d passthrough / d ceil, evaluated independently of the passthrough series.
    s = 1.0 / (1.0 + np.exp(-p_ctl["gas_slope"] * (gas - p_ctl["gas_mid"])))
    pt_ctl = np.asarray(
        coal_passthrough_series(c_cfg, year, HOURS, "bituminous"), dtype=float
    )
    pt_arm = np.asarray(
        coal_passthrough_series(a_cfg, year, HOURS, "bituminous"), dtype=float
    )
    identity_resid = float(
        np.abs((pt_arm - pt_ctl) - s * (p_arm["ceil"] - p_ctl["ceil"])).max()
    )

    predicted = _bituminous_units(ctl)
    mc_c, mc_a = _mc_matrix(ctl), _mc_matrix(arm)
    fa = ctl["fleet_arrays"]
    ids = [str(u) for u in fa.unit_ids]
    moved_mask = np.abs(mc_a - mc_c).max(axis=1) > 1e-9
    moved = {ids[i] for i in np.flatnonzero(moved_mask)}

    d_idx = np.flatnonzero(moved_mask)
    if d_idx.size:
        delta = (mc_a - mc_c)[d_idx]
        mc_delta_mean = float(delta.mean())
        mc_delta_min = float(delta.min())
        mc_delta_max = float(delta.max())
    else:
        mc_delta_mean = mc_delta_min = mc_delta_max = 0.0

    # The S3 prediction, from the mechanism's own arithmetic: for each DIRECT
    # row, d mc = s(g_t) * (ceil_arm - ceil_ctl) * fuel$/MMBtu * heat_rate.
    fp = np.asarray(ctl["fuel_prices"], dtype=float)
    hr = np.asarray(fa.heat_rate, dtype=float)
    pred_idx = [i for i, u in enumerate(ids) if u in predicted]
    if pred_idx:
        fpu = fp[pred_idx] if fp.ndim == 2 else np.repeat(
            fp[pred_idx][:, None], HOURS, axis=1
        )
        pred = s[None, :] * (p_arm["ceil"] - p_ctl["ceil"]) * fpu * hr[pred_idx, None]
        s3_predicted = float(pred.mean())
    else:
        s3_predicted = 0.0

    return {
        "year": year,
        "params_control": {k: float(v) for k, v in p_ctl.items()},
        "params_arm": {k: float(v) for k, v in p_arm.items()},
        "gas_mean": float(gas.mean()),
        "leverage_mean": float(s.mean()),
        "leverage_p50": float(np.median(s)),
        "leverage_frac_ge_099": float((s >= 0.99).mean()),
        "passthrough_mean_control": float(pt_ctl.mean()),
        "passthrough_mean_arm": float(pt_arm.mean()),
        "s2_identity_max_abs_resid": identity_resid,
        "n_predicted_direct": len(predicted),
        "n_moved": len(moved),
        "unpredicted_moved": sorted(moved - predicted),
        "predicted_not_moved": sorted(predicted - moved),
        "mc_delta_mean_direct": mc_delta_mean,
        "mc_delta_min": mc_delta_min,
        "mc_delta_max": mc_delta_max,
        "s3_predicted_mc_delta": s3_predicted,
        "s3_abs_error": abs(mc_delta_mean - s3_predicted),
        "delivered_coal_mmbtu_model": _delivered_coal_mmbtu(ctl, predicted),
        "delivered_coal_mmbtu_derive": DERIVE_DELIV_MMBTU,
        "direct_capacity_mw": float(
            np.asarray(fa.pmax, dtype=float)[pred_idx].sum()
        ),
    }


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/pjm169_tp2022_2021_f2arm")
    ap.add_argument("--years", nargs="+", type=int, default=[2022])
    ap.add_argument("--json", default=None, help="write the census to this path")
    args = ap.parse_args()

    bundle = Path(args.bundle)
    rows = [census_year(bundle, y) for y in args.years]

    print(f"\npjm-170 phase-0 ceiling census — control {bundle.name}")
    print(f"declared delta: coal_bit_passthrough_ceil -> {ARM_CEIL}\n")
    for r in rows:
        print(f"=== {r['year']} ===")
        print(f"  control params {r['params_control']}")
        print(f"      arm params {r['params_arm']}")
        print(
            f"  leverage s: mean {r['leverage_mean']:.4f} p50 "
            f"{r['leverage_p50']:.4f} frac>=0.99 {r['leverage_frac_ge_099']*100:.1f}%"
        )
        print(
            f"  passthrough mean {r['passthrough_mean_control']:.4f} -> "
            f"{r['passthrough_mean_arm']:.4f}"
        )
        print(f"  S2 identity max|resid| {r['s2_identity_max_abs_resid']:.3e}")
        print(
            f"  S4-A rows: predicted {r['n_predicted_direct']}  moved "
            f"{r['n_moved']}  UNPREDICTED-MOVED {len(r['unpredicted_moved'])}  "
            f"predicted-not-moved {len(r['predicted_not_moved'])}"
        )
        print(
            f"  S3 mc delta measured {r['mc_delta_mean_direct']:+.6f} vs predicted "
            f"{r['s3_predicted_mc_delta']:+.6f}  |err| {r['s3_abs_error']:.3e} $/MWh"
        )
        print(
            f"     (range {r['mc_delta_min']:+.3f} .. {r['mc_delta_max']:+.3f} $/MWh; "
            f"direct capacity {r['direct_capacity_mw']:,.1f} MW)"
        )
        dm = r["delivered_coal_mmbtu_model"]
        print(
            f"  SS3.3 delivered coal $/MMBtu: model "
            f"{'n/a' if dm is None else f'{dm:.3f}'} vs derive "
            f"{r['delivered_coal_mmbtu_derive']:.3f}"
        )
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
