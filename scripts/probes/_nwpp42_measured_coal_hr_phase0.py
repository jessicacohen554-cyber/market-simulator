"""nwpp-42 phase 0 (ZERO LP): offer-array delta of ``measured_coal_heat_rates``.

Rebuilds the registered NWPP keeper's fleet on its OWN recipe via the
sanctioned ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
(``run_year(..., fleet_only=True)``), once as the CONTROL (the posture the
registered run solved under) and once with ``measured_coal_heat_rates`` armed,
and diffs the assembled marginal-cost array row-for-row.

The questions it answers before any solve (rule 29 ``[R-SCREEN]`` clause 0,
which survives as the practice):

1. **Is the arm CONFINED?** Only ``COAL`` rows may move. A coal site's
   gas-converted boilers (Jim Bridger, Naughton, North Valmy — 1,571 MW that
   the model classes ``ST_GAS``) must be byte-identical, as must ``pmax`` and
   ``availability`` everywhere: this mechanism reprices, it does not re-rate.
2. **How large is the move, in $/MWh?** The artifact's measured rates are
   below the assigned eGRID rates at every covered plant, so every covered coal
   row's offer must fall, and by the plant's own measured amount times its own
   delivered fuel price.
3. **Where does the moved stack sit against the price the keeper cleared?**
   Reported per year against the committed ``hourly/system_<year>.parquet``
   duals, so the merit-order consequence is on the record BEFORE the solve and
   cannot be written to fit the result.

Run: ``python3 scripts/probes/_nwpp42_measured_coal_hr_phase0.py 2023 2024 2025``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp41_span_A")


def _clear_caches() -> None:
    """Drop every lru_cache that memoizes the heat-rate resolution chain."""
    import importlib

    for mod in (
        "market_sim.data.fleet",
        "market_sim.data.fleet.campd_bins",
        "market_sim.data.fleet.eia860",
    ):
        m = importlib.import_module(mod)
        for name in dir(m):
            obj = getattr(m, name, None)
            if hasattr(obj, "cache_clear"):
                try:
                    obj.cache_clear()
                except Exception:
                    pass


def build(year: int, arm: bool):
    """Assemble the keeper's fleet for ``year``, with or without the arm."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    if arm:
        kw["measured_coal_heat_rates"] = True
    _clear_caches()
    try:
        return run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
    finally:
        _clear_caches()


def _arrays(state) -> dict:
    """Return the comparison surface from a ``fleet_only`` state dict."""
    fa = state["fleet_arrays"]
    return {
        "unit_ids": list(fa.unit_ids),
        "groups": list(getattr(fa, "plant_group", [])),
        "codes": list(getattr(fa, "plant_code", [])),
        "mc": np.asarray(state["mc_base"], dtype=float),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "avail": np.asarray(fa.availability, dtype=float),
        "hr": np.asarray(fa.heat_rate, dtype=float),
    }


def _zone_prices(year: int) -> np.ndarray | None:
    """Load-weighted P1 zonal duals from the keeper's committed sidecar."""
    import pandas as pd

    path = BUNDLE / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        return None
    d = pd.read_parquet(path)
    if "pass" in d.columns:
        d = d[d["pass"] == "P1"]
    return d["price"].to_numpy(dtype=float)


def main() -> None:
    years = [int(a) for a in sys.argv[1:] if a.isdigit()] or [2023, 2024, 2025]
    for year in years:
        ctl = _arrays(build(year, arm=False))
        arm = _arrays(build(year, arm=True))
        print(f"\n===== {year} =====")
        print(f"  rows  ctl {len(ctl['unit_ids'])}  arm {len(arm['unit_ids'])}")
        if ctl["unit_ids"] != arm["unit_ids"]:
            print("  UNIT ID LIST DIFFERS -- comparison aborted")
            continue

        coal = [i for i, g in enumerate(ctl["groups"]) if str(g) == "COAL"]
        other = [i for i in range(len(ctl["unit_ids"])) if str(ctl["groups"][i]) != "COAL"]
        for lab, idx in (("COAL", coal), ("NON-COAL", other)):
            if not idx:
                print(f"  {lab}: no rows")
                continue
            dmc = np.abs(arm["mc"][idx] - ctl["mc"][idx])
            dpm = np.abs(arm["pmax"][idx] - ctl["pmax"][idx])
            dav = np.abs(arm["avail"][idx] - ctl["avail"][idx])
            nmoved = int((dmc.max(axis=1) > 0).sum())
            print(
                f"  {lab:9s} n={len(idx):4d}  offer max|d| ${dmc.max():.10f}/MWh  "
                f"rows moved {nmoved}  pmax max|d| {dpm.max():.10f}  "
                f"avail max|d| {dav.max():.12f}"
            )

        # Per-band capacity-weighted coal offer, both legs, against the price.
        bands = ("mustrun", "committed", "econlo", "econhi", "peak")
        px = _zone_prices(year)
        if px is not None:
            print(
                f"  keeper P1 zonal price: mean ${px.mean():.2f}  "
                f"p25 ${np.percentile(px, 25):.2f}  p50 ${np.percentile(px, 50):.2f}  "
                f"p75 ${np.percentile(px, 75):.2f}  p90 ${np.percentile(px, 90):.2f}"
            )
        print(
            f"  {'band':<10}{'cap MW':>10}{'ctl $/MWh':>12}{'arm $/MWh':>12}"
            f"{'delta':>10}{'ctl %hrs<=px':>14}{'arm %hrs<=px':>14}"
        )
        for band in bands:
            idx = [i for i in coal if str(ctl["unit_ids"][i]).endswith("_" + band)]
            if not idx:
                continue
            w = ctl["pmax"][idx]
            c = float((ctl["mc"][idx].mean(axis=1) * w).sum() / w.sum())
            a = float((arm["mc"][idx].mean(axis=1) * w).sum() / w.sum())
            if px is not None:
                # Share of the keeper's own zone-hours whose price clears the
                # capacity-weighted band offer. A merit-position READING of the
                # committed control, never a prediction of the arm's dispatch.
                cin = float((px >= c).mean() * 100.0)
                ain = float((px >= a).mean() * 100.0)
            else:
                cin = ain = float("nan")
            print(
                f"  {band:<10}{float(w.sum()):>10.1f}{c:>12.3f}{a:>12.3f}"
                f"{a - c:>+10.3f}{cin:>14.1f}{ain:>14.1f}"
            )

        # Per-plant detail on the rows that moved most.
        moved = sorted(
            (
                (
                    float(np.abs(arm["mc"][i] - ctl["mc"][i]).mean()),
                    str(ctl["unit_ids"][i]),
                    float(ctl["hr"][i]),
                    float(arm["hr"][i]),
                    float(ctl["pmax"][i]),
                )
                for i in coal
            ),
            reverse=True,
        )[:8]
        print("  largest movers (mean |d offer|, heat rate ctl -> arm):")
        for d, uid, h0, h1, pm in moved:
            print(
                f"    {uid:<34} pmax {pm:>8.1f}  HR {h0:>7.3f} -> {h1:>7.3f}  "
                f"mean |d| ${d:>7.3f}/MWh"
            )


if __name__ == "__main__":
    main()
