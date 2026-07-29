"""pjm-138 M1 + M3 (no LP): WHO sets the model's price in the hours Dominion's
turbines run, and HOW STEEP is the model's supply curve where it clears?

pjm-138 M2 (`_pjm138_mec_gap_shape.py`) measured the SHAPE of the
system-energy half of the Dominion CT-hour deficit: it is not a level problem
(annual load-weighted the model reproduces PJM's own MEC to +$0.47 / +$2.62 /
+$8.48) but a DISPERSION problem, running $4.9–5.8/MWh too DEAR in the slackest
net-load decile and $14.3 / $21.6 / $39.9 too CHEAP in the tightest. This probe
asks the two questions that shape leaves open.

* **M1 — marginal ownership.** In an LP the price setter is not a matter of
  interpretation: every unit strictly cheaper than the dual is at its upper
  bound, every unit dearer is off, and **the units whose offer equals the dual
  are the marginal set**. So the ownership census needs the offers and the
  duals and nothing else — no per-unit dispatch, hence no solve. Ownership is
  reported by class, bucketed by the model's own price band ($0–40 / $40–150 /
  > $150, the pjm-122 bands) and by net-load decile, and again restricted to
  the hours the real Dominion CT fleet is running. The pjm-122 charge is that
  fitted coal rungs own the $40–150 region the measured DataMiner2 corpus
  assigns to the CC top belt and CT_FAST; this re-runs that census on the
  CURRENT keeper.
* **M3 — the supply-curve slope, i.e. the G-20b sizing that has never been
  done.** `FINDING-guard-falseneg-audit-2026-07-27` §3 measured that the
  merit-order guard returns **~2.8–5.0 GW** of capacity to PJM's tightest
  net-load quartile, and §7 declined to write a fix because no instrument
  sized the *price* consequence. It is sizeable with no solve: removing ΔMW of
  inframarginal capacity moves the clearing point ΔMW up the same offer stack,
  so the price response is `mc(Q + Δ) − mc(Q)` read straight off the hour's own
  sorted offer curve. If 3–5 GW buys a few dollars, the lead is inert whatever
  its population statistics say; if it buys tens of dollars, it is live.

The keeper fleet is reconstructed through the AUTHORITATIVE path — the bundle's
`meta.json` replayed through `replay_keeper`'s own meta→kwarg mapping into
`solve_and_persist`, with `run_year` intercepted and forced to `fleet_only=True`
so the offers built are byte-for-byte the offers the keeper solved on and no LP
is ever constructed. Mirroring the kwargs by hand (the
`derive_pjm_ordc_overlay._run_year_kwargs` shortcut) would silently drop the
keeper's own flags — `measured_ct_heat_rates`, `pjm_zonal_loss_surface`, the
reliability-floor overrides — and price a fleet the keeper never had.

Nothing is written outside `results/probes/`.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm138_marginal_ownership.py
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm138_marginal_ownership.py \
        --bundle results/calibration/pjm137_ctheatrate_B --years 2025
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

# Same reproducibility pin replay_keeper.py sets, for the same reason: the
# fleet reconstruction must not depend on the ambient warm-start setting.
os.environ.setdefault("MARKET_SIM_WARMSTART_XYEAR", "0")

HOURS = 8760
EXTERNAL_ZONE = "PJM_external"
DOM = "PJM_Dominion"

#: Price bands shared with pjm-122 §2 and with the pjm-138 M2 readout.
BANDS = ((-1e9, 40.0), (40.0, 150.0), (150.0, 1e9))
BAND_LABS = ("0-40", "40-150", ">150")

#: Offer-price windows above the clearing price used for the headroom shelf.
SHELVES = (1.0, 5.0, 10.0, 25.0, 50.0)

#: Capacity withdrawals (MW) priced against the hour's own offer stack. The
#: 2.8-5.0 GW band is the guard-audit §3 figure for PJM's tightest quartile.
WITHDRAWALS_MW = (1000.0, 2000.0, 3000.0, 5000.0, 8000.0)

#: Marginal-set half-width ($/MWh). An LP's price setter offers AT the dual;
#: the window only absorbs float noise and tranche granularity.
EPS = 1.0

OUT_PATH = Path("results/probes/pjm138_marginal_ownership.json")


class _FleetCaptured(Exception):
    """Raised to unwind ``solve_and_persist`` once the fleet state is in hand."""


def _keeper_fleet(bundle: Path, year: int) -> dict:
    """Rebuild the EXACT fleet/offer arrays the keeper solved against — no LP.

    Replays `meta.json` through ``replay_keeper``'s mapping into
    ``solve_and_persist`` with ``run_year`` intercepted: the interceptor forces
    ``fleet_only=True`` (which returns the built arrays instead of constructing
    the LP), stashes the state and unwinds. The kwargs therefore come from the
    same code path the keeper's own solve used.
    """
    spec = importlib.util.spec_from_file_location(
        "_replay_keeper", REPO / "scripts" / "replay_keeper.py"
    )
    rk = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(rk)

    from scripts import run_calibration
    from scripts import run_calibration_full as rcf

    kwargs = rk.build_kwargs(json.loads((bundle / "meta.json").read_text()))
    kwargs["years"] = [year]

    captured: dict = {}
    real_run_year = run_calibration.run_year

    def _intercept(*args, **kw):
        kw["fleet_only"] = True
        captured["state"] = real_run_year(*args, **kw)
        raise _FleetCaptured

    run_calibration.run_year = _intercept
    rcf.run_year = _intercept
    try:
        rcf.solve_and_persist(**kwargs)
    except _FleetCaptured:
        pass
    finally:
        run_calibration.run_year = real_run_year
        rcf.run_year = real_run_year

    if "state" not in captured:
        raise SystemExit("fleet reconstruction did not reach run_year")
    return captured["state"]


def _model_prices(bundle: Path, year: int) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Keeper P1 duals per internal zone, plus load-weighted price and net load."""
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"] != EXTERNAL_ZONE)]
    price = sysf.pivot(index="hour", columns="zone", values="price")
    dem = sysf.pivot(index="hour", columns="zone", values="demand")
    load = dem.sum(axis=1).to_numpy(float)
    lw = (price * dem).sum(axis=1).to_numpy(float) / load

    cls = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    ren = (
        cls[cls["klass"].isin(("wind", "solar"))]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(HOURS))
        .fillna(0.0)
        .to_numpy(float)
    )
    return price, lw, load - ren


def _dominion_ct(year: int) -> np.ndarray:
    """Measured hourly Dominion CT_PEAKER output (pjm-137's roster and filter)."""
    spec = importlib.util.spec_from_file_location(
        "_p137", REPO / "scripts" / "probes" / "_pjm137_dominion_ct_congestion.py"
    )
    p137 = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(p137)
    return p137._dominion_ct_hourly(year)[0]


def _band_of(x: np.ndarray) -> np.ndarray:
    """Price-band label per hour."""
    out = np.empty(len(x), dtype=object)
    for lab, (lo, hi) in zip(BAND_LABS, BANDS):
        out[(x >= lo) & (x < hi)] = lab
    return out


def _deciles(x: np.ndarray) -> np.ndarray:
    order = np.argsort(np.argsort(x))
    return (order * 10 // len(x) + 1).astype(int)


def measure_year(bundle: Path, year: int) -> dict:
    state = _keeper_fleet(bundle, year)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)  # (n_gen, T) the LP's offers
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    avail = np.asarray(fa.pmax, dtype=float)[:, None] * np.asarray(
        fa.availability, dtype=float
    )
    grp = (
        np.asarray(fa.plant_group, dtype=object)
        if getattr(fa, "plant_group", None) is not None
        else np.array(["?"] * mc.shape[0], dtype=object)
    )
    grp = np.array([str(g) if g else "?" for g in grp], dtype=object)

    price, lw, netload = _model_prices(bundle, year)
    zones = list(price.columns)
    # `zone_idx` indexes the ISO's own ordered zone list; the external star node
    # sits past the internal zones and is excluded by `internal` below.
    from market_sim.config.iso_configs import get_iso_config

    all_zone_names = list(get_iso_config("PJM").zone_names)
    zi = np.asarray(fa.zone_idx, dtype=int)
    zone_name = np.array(
        [all_zone_names[i] if i < len(all_zone_names) else EXTERNAL_ZONE for i in zi],
        dtype=object,
    )
    internal = np.isin(zone_name, zones)

    ct = _dominion_ct(year)
    dec = _deciles(netload)
    band = _band_of(lw)

    # Per-unit hourly dual of its OWN zone.
    zprice = {z: price[z].to_numpy(float) for z in zones}
    dual = np.zeros_like(mc)
    for z in zones:
        m = zone_name == z
        if m.any():
            dual[m, :] = zprice[z][None, :]

    def _census(hour_sel: np.ndarray, weight: np.ndarray) -> dict:
        """Marginal-class shares and headroom shelf over the selected hours."""
        w = weight[hour_sel]
        if w.sum() <= 0:
            return {}
        sub_mc = mc[:, hour_sel]
        sub_av = avail[:, hour_sel]
        sub_du = dual[:, hour_sel]
        live = internal[:, None] & (sub_av > 1.0)
        at = live & (np.abs(sub_mc - sub_du) <= EPS)

        classes = sorted(set(grp[internal]))
        marg_mw: dict[str, float] = {}
        marg_h: dict[str, float] = {}
        shelf: dict[str, dict] = {}
        any_at = at.any(axis=0)
        for c in classes:
            cm = (grp == c) & internal
            if not cm.any():
                continue
            atc = at[cm]
            # MW-weighted ownership: the class's available MW sitting at the dual
            marg_mw[c] = float(((sub_av[cm] * atc).sum(axis=0) * w).sum() / w.sum())
            # hour-share ownership: hours where this class has ANY unit at the dual
            marg_h[c] = float((atc.any(axis=0) * w).sum() / w.sum() * 100)
            row = {}
            for s in SHELVES:
                inb = live[cm] & (sub_mc[cm] > sub_du[cm]) & (
                    sub_mc[cm] <= sub_du[cm] + s
                )
                row[f"above_dual_within_{int(s)}_gw"] = float(
                    ((sub_av[cm] * inb).sum(axis=0) * w).sum() / w.sum() / 1e3
                )
            row["available_gw"] = float(
                ((sub_av[cm] * live[cm]).sum(axis=0) * w).sum() / w.sum() / 1e3
            )
            row["below_dual_gw"] = float(
                (
                    (sub_av[cm] * (live[cm] & (sub_mc[cm] < sub_du[cm]))).sum(axis=0)
                    * w
                ).sum()
                / w.sum()
                / 1e3
            )
            shelf[c] = row
        tot = sum(marg_mw.values()) or 1.0
        return {
            "hours": int(hour_sel.sum()),
            "mean_model_price": float((lw[hour_sel] * w).sum() / w.sum()),
            "hours_with_no_unit_at_dual_pct": float(
                ((~any_at) * w).sum() / w.sum() * 100
            ),
            "marginal_share_pct_by_mw": {
                k: round(v / tot * 100, 2) for k, v in sorted(marg_mw.items()) if v > 0
            },
            "marginal_hour_share_pct": {
                k: round(v, 2) for k, v in sorted(marg_h.items()) if v > 0.05
            },
            "shelf_gw": shelf,
        }

    # ---- M3 the supply-curve slope: price response to a capacity withdrawal
    def _withdrawal_curve(hour_sel: np.ndarray) -> dict:
        """`mc(Q+Δ) − mc(Q)` on each selected hour's own sorted offer stack.

        Q is read as the MW of internal available capacity offered strictly
        BELOW that hour's load-weighted dual — the inframarginal block. Removing
        Δ MW of it moves the clearing point Δ MW up the SAME stack, so the price
        response is the offer at cumulative `Q+Δ` minus the dual. Renewables and
        storage are outside this stack, so the number is an upper bound on the
        thermal-only response and a lower bound on nothing.
        """
        hrs = np.where(hour_sel)[0]
        resp = {f"{int(d / 1000)}gw": [] for d in WITHDRAWALS_MW}
        for h in hrs:
            m = internal & (avail[:, h] > 1.0)
            p = mc[m, h]
            q = avail[m, h]
            order = np.argsort(p, kind="stable")
            p, q = p[order], q[order]
            cum = np.cumsum(q)
            p0 = float(lw[h])
            k = int(np.searchsorted(p, p0, side="right"))
            q0 = float(cum[k - 1]) if k > 0 else 0.0
            for d in WITHDRAWALS_MW:
                i = min(int(np.searchsorted(cum, q0 + d, side="left")), len(p) - 1)
                resp[f"{int(d / 1000)}gw"].append(float(p[i] - p0))
        return {
            k: {
                "mean": float(np.mean(v)) if v else float("nan"),
                "p50": float(np.median(v)) if v else float("nan"),
                "p90": float(np.percentile(v, 90)) if v else float("nan"),
            }
            for k, v in resp.items()
        }

    all_h = np.ones(HOURS, dtype=bool)
    out: dict = {
        "n_gen_internal": int(internal.sum()),
        "classes": sorted(set(grp[internal])),
        "all_hours": _census(all_h, np.maximum(netload, 1.0)),
        "by_price_band": {
            lab: _census(band == lab, np.maximum(netload, 1.0)) for lab in BAND_LABS
        },
        "by_netload_decile": {
            str(d): _census(dec == d, np.maximum(netload, 1.0)) for d in (1, 5, 9, 10)
        },
        "dominion_ct_hours": _census(ct > 0, np.maximum(ct, 0.0)),
        "withdrawal_price_response": {
            "top_decile": _withdrawal_curve(dec == 10),
            "deciles_9_10": _withdrawal_curve(dec >= 9),
        },
    }
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle", type=Path, default=Path("results/calibration/pjm137_ctheatrate_B")
    )
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args(argv)

    payload = {"bundle": str(args.bundle), "years": args.years, "M1_M3": {}}
    for year in args.years:
        print(f"pjm-138 M1/M3 — {year} …", flush=True)
        payload["M1_M3"][str(year)] = measure_year(args.bundle, year)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=1))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
