"""nyiso-245 — cache the keeper's assembled fleet state to .npz (INFRASTRUCTURE, not a measurement).

ZERO LP (rule 32 ``[R-SHARD]`` (a)). This dumps the model's own assembled
arrays so the phase-0 probes read them in seconds instead of re-running a
~4 min fleet rebuild per year. It computes NO gated statistic — every number
gated by ``PRECOMMIT-nyiso245`` is derived downstream from this dump.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nyiso245_fleet_cache.py --year 2022
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
HOURS = 8760


def dump(year: int) -> "tuple[Path, dict]":
    """Write one year's assembled fleet arrays to ``_nyiso245_cache/<year>.npz``."""
    from scripts.probes.nyiso242_tail_reachability import fleet_state

    st = fleet_state(year)
    fa = st["fleet_arrays"]
    gens = st.get("generators") or st.get("fleet") or []

    def col(name: str, default=0.0):
        return np.array([getattr(g, name, default) for g in gens], dtype=object)

    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    av = np.asarray(fa.availability, dtype=float)
    if av.ndim == 1:
        av = np.repeat(av[:, None], HOURS, axis=1)

    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{year}.npz"
    payload = {
        "unit_ids": np.array([str(u) for u in fa.unit_ids]),
        "plant_group": np.array([str(k) for k in fa.plant_group]),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "availability": av,
        "mc_base": mc,
        "fuel_prices": np.asarray(st["fuel_prices"], dtype=float),
    }
    if len(gens):
        payload["gen_plant_code"] = np.array([str(x) for x in col("plant_code", "")])
        payload["gen_markup_hr"] = np.array(
            [float(x or 0.0) for x in col("offer_markup_hr", 0.0)], dtype=float
        )
        payload["gen_margin_anchor"] = np.array(
            [float(x or 0.0) for x in col("offer_margin_anchor", 0.0)], dtype=float
        )
        payload["gen_pmax_mw"] = np.array(
            [float(x or 0.0) for x in col("pmax_mw", 0.0)], dtype=float
        )
        payload["gen_unit_id"] = np.array([str(x) for x in col("unit_id", "")])
        payload["gen_plant_group"] = np.array([str(x) for x in col("plant_group", "")])
        payload["gen_bin_label"] = np.array([str(x) for x in col("bin_label", "")])
    np.savez_compressed(out, **payload)
    print(f"wrote {out}  rows={len(payload['unit_ids'])}  gens={len(gens)}")
    print("  state keys:", sorted(st.keys()))
    return out, st


def dump_gas(year: int, st: dict | None = None) -> Path:
    """Write the keeper's own resolved delivered-gas series to ``gas_<year>.npy``.

    The gas pass :func:`derive_nyiso_offer_surface.gas_series_by_year` names.
    It resolves ``_gas_series`` from the keeper's OWN reconstructed config (the
    one the fleet-only rebuild built), so the derive and the solve-side applier
    bin on ONE gas object and never on two independently built ones
    (rule 19 ``[R-ONE-MECH]`` in spirit).
    """
    from market_sim.data.fuel.trajectories import _gas_series

    if st is None:
        from scripts.probes.nyiso242_tail_reachability import fleet_state

        st = fleet_state(year)
    cfg = None
    for key in ("config", "scenario", "scenario_config", "cfg"):
        if isinstance(st, dict) and st.get(key) is not None:
            cfg = st[key]
            break
    if cfg is None:
        raise SystemExit(
            "no ScenarioConfig in the fleet-only state; keys: "
            + ", ".join(sorted(st)) if isinstance(st, dict) else str(type(st))
        )
    series = np.asarray(_gas_series(cfg, year, HOURS), dtype=float)
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"gas_{year}.npy"
    np.save(out, series)
    print(
        f"wrote {out}  min={series.min():.4f} max={series.max():.4f} "
        f"mean={series.mean():.4f}"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=[2022])
    ap.add_argument("--gas-only", action="store_true")
    args = ap.parse_args()
    for y in args.year:
        st = None
        if not args.gas_only:
            _, st = dump(y)
        dump_gas(y, st)


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
