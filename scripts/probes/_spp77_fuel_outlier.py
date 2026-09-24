"""SPP-77 — the F923 fuel outlier: reproduce, root-cause and scan at zero LP.

One interpreter per year (``reconstruct_bundle_fleet`` holds per-process caches).

* ``--mode scan``: rebuild the year's bundle fleet exactly as it solved; per gas/coal
  thermal row, the monthly mean offer fuel price; flag every row-month whose fuel is
  > 3x that month's capacity-weighted class median (the brief's signature). Writes the
  flag table, the Jan CC-by-plant table, and an ``.npz`` of the thermal stack (mc, cap,
  class) for the merit re-dispatch.
* ``--mode patch``: DIAGNOSTIC COUNTERFACTUAL ONLY, never a mechanism: rebuild with the
  EIA state reference table's cells in ``--patch-cells`` (``ST:YYYY-MM``) replaced by the
  US series for that month, by pre-seeding the loader's per-path cache. Writes the
  same ``.npz`` so ``--mode compare`` can size the effect on the served thermal energy
  with SPP-76's merit instrument (``_spp76_crossover_hr.merit_dispatch``).
* ``--mode compare``: merit re-dispatch of the P1 served thermal energy over the two
  stacks; class TWh delta (proxy), plus proxy fidelity vs P1 class energy.

Usage::

    uv run python scripts/probes/_spp77_fuel_outlier.py --mode scan --year 2022 --out-dir <d>
    uv run python scripts/probes/_spp77_fuel_outlier.py --mode patch --year 2022 \
        --patch-cells MO:2022-01 --out-dir <d>
    uv run python scripts/probes/_spp77_fuel_outlier.py --mode compare --year 2022 --out-dir <d>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from scripts.probes._spp76_crossover_hr import (  # noqa: E402
    BUNDLES,
    GAS,
    THERMAL_PREFIXES,
    merit_dispatch,
)

FLAG_MULT = 3.0  # the brief's signature: row-month > 3x the class median that month


def _patch_reference(cells: list[str]) -> None:
    """Pre-seed the EIA state-reference cache with ``cells`` replaced by the US series."""
    from market_sim.data.fuel import plant_prices as pp

    pp._STATE_EP_GAS_CACHE.clear()
    table = dict(pp.load_state_electric_power_gas_prices())
    for c in cells:
        st, ym = c.split(":")
        y, m = (int(x) for x in ym.split("-"))
        table[(st, y, m)] = table[("US", y, m)]
    pp._STATE_EP_GAS_CACHE[pp.EIA_STATE_ELECTRIC_POWER_GAS_PATH] = table


def rebuild(y: int, out: Path, tag: str) -> None:
    """Rebuild the year's fleet; write the thermal stack npz and (scan) the flag tables."""
    from scripts.lib.bundle_fleet import bundle_gas_price, reconstruct_bundle_fleet
    from scripts.run_calibration_full import _coal_supply_class

    bundle = REPO / "results/calibration" / BUNDLES[y]
    gas = bundle_gas_price(json.loads((bundle / "meta.json").read_text()), y)
    if abs(gas - GAS[y]) > 0.005:
        raise SystemExit(f"HARD STOP: {y} bundle gas {gas} != brief {GAS[y]}")
    state, _ = reconstruct_bundle_fleet(bundle, y, verbose=False)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], float)
    fuel = np.broadcast_to(np.asarray(state["fuel_prices"], float).reshape(len(mc), -1), mc.shape)
    avail = np.broadcast_to(np.asarray(fa.availability, float).reshape(len(mc), -1), mc.shape)
    pmax = np.asarray(fa.pmax, float)
    codes = np.asarray(fa.plant_code).astype(int)
    klass = np.array(
        [
            _coal_supply_class(int(codes[i])) if str(g) == "COAL" else str(g)
            for i, g in enumerate(fa.plant_group)
        ],
        dtype=object,
    )
    th = np.array([str(k).startswith(THERMAL_PREFIXES) for k in klass])
    idx = np.flatnonzero(th)
    np.savez_compressed(
        out / f"stack_{y}_{tag}.npz",
        mc=mc[idx],
        cap=(pmax[:, None] * avail)[idx],
        klass=klass[idx].astype(str),
        codes=codes[idx],
    )
    if tag != "scan":
        return
    T = mc.shape[1]
    month = pd.date_range(f"{y}-01-01", periods=T, freq="h").month.to_numpy()
    fm = np.stack([fuel[:, month == m].mean(axis=1) for m in range(1, 13)], axis=1)
    states = np.asarray(fa.state).astype(str) if hasattr(fa, "state") else np.array([""] * len(mc))
    rows = []
    for k in sorted(set(klass[th].tolist())):
        s = th & (klass == k)
        if s.sum() < 3:
            continue
        for m in range(12):
            v = fm[s, m]
            order = np.argsort(v)
            cw = np.cumsum(pmax[s][order])
            med = float(v[order][np.searchsorted(cw, cw[-1] / 2.0)])
            for i in np.flatnonzero(s)[v > FLAG_MULT * med]:
                rows.append(
                    {
                        "year": y, "month": m + 1, "klass": k, "plant": int(codes[i]),
                        "state": states[i], "pmax_mw": float(pmax[i]),
                        "fuel": float(fm[i, m]), "class_median": med,
                        "ratio": float(fm[i, m] / med) if med > 0 else float("inf"),
                    }
                )
    flags = pd.DataFrame(rows)
    flags.to_csv(out / f"flags_{y}.csv", index=False)
    cc = th & (klass == "CC_REGULAR")
    jan = (
        pd.DataFrame({"plant": codes[cc], "pmax": pmax[cc], "fuel_jan": fm[cc, 0], "fuel_feb": fm[cc, 1]})
        .groupby("plant")
        .agg(pmax=("pmax", "sum"), fuel_jan=("fuel_jan", "mean"), fuel_feb=("fuel_feb", "mean"))
        .sort_values("fuel_jan", ascending=False)
    )
    jan.to_csv(out / f"cc_jan_by_plant_{y}.csv")
    summ = (
        flags.groupby(["month", "klass"]).agg(n=("plant", "size"), mw=("pmax_mw", "sum"), max_ratio=("ratio", "max"))
        if len(flags) else pd.DataFrame()
    )
    print(f"{y}: {len(flags)} flagged row-months")
    print(summ.to_string() if len(summ) else "(none)")
    print(jan.head(6).round(2).to_string())


def compare(y: int, out: Path) -> None:
    """Merit re-dispatch of the P1 served thermal energy over the scan vs patched stacks."""
    a = np.load(out / f"stack_{y}_scan.npz", allow_pickle=False)
    b = np.load(out / f"stack_{y}_patch.npz", allow_pickle=False)
    assert (a["codes"] == b["codes"]).all()
    bundle = REPO / "results/calibration" / BUNDLES[y]
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{y}.parquet")
    ch = ch[(ch["pass"] == "P1") & ch["klass"].astype(str).str.startswith(THERMAL_PREFIXES)]
    T = a["mc"].shape[1]
    served = ch.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy()
    p1 = (ch.groupby("klass")["mw"].sum() / 1e6).to_dict()
    e0 = merit_dispatch(a["mc"], a["cap"], served)
    e1 = merit_dispatch(b["mc"], b["cap"], served)
    kl = a["klass"]
    moved = np.abs(a["mc"] - b["mc"]).max(axis=1) > 1e-9
    res = {
        "year": y,
        "rows_repriced": int(moved.sum()),
        "mw_repriced": float(a["cap"][moved].max(axis=1).sum()),
        "classes": {
            k: {
                "p1_twh": float(p1.get(k, 0.0)),
                "proxy_ctrl_twh": float(e0[kl == k].sum() / 1e6),
                "delta_twh": float((e1[kl == k].sum() - e0[kl == k].sum()) / 1e6),
            }
            for k in sorted(set(kl.tolist()))
        },
    }
    (out / f"compare_{y}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("year", "rows_repriced", "mw_repriced")}))
    for k in ("CC_REGULAR", "COAL_PRB", "ST_GAS", "CT_PEAKER"):
        if k in res["classes"]:
            print(k, {q: round(v, 3) for q, v in res["classes"][k].items()})


def main() -> int:
    """Dispatch on ``--mode``."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("scan", "patch", "compare"), required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--patch-cells", nargs="*", default=[])
    ap.add_argument("--out-dir", type=Path, required=True)
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    if a.mode == "scan":
        rebuild(a.year, a.out_dir, "scan")
    elif a.mode == "patch":
        _patch_reference(a.patch_cells)
        rebuild(a.year, a.out_dir, "patch")
    else:
        compare(a.year, a.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
