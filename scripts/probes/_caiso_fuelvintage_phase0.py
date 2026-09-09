"""Phase-0 for session caiso-fuelvintage-1 — both cards, zero LP, one year per call.

Card A: rebuild CAISO's fleet twice on the committed keeper recipe, swapping ONLY the
retiree parquet vintage (2019-window at HEAD vs a >=2023 filter that reproduces the
pre-`7934e92c` artifact), and measure whether the widened window is inert in a training
year. The PJM lane measured this NOT inert (docs/FINDING-pjm-retiree-window-
redistribution-2026-09-09.md); CAISO's tabulated exposure is 480.0 MW.

Card B: rebuild the fleet twice at HEAD with `gas_electric_power_monthly_level` off and
on, and census which fuel-price / offer cells the seam actually reaches under the
keeper's `gas_plant_monthly_fuel_pricing = True` print path (handoff addendum A2).

Usage:
    uv run python scripts/probes/_caiso_fuelvintage_phase0.py <year> {A|B}
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/market-simulator")
sys.path.insert(0, str(ROOT))

from market_sim.config import paths  # noqa: E402
from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402

BUNDLE = ROOT / "results/calibration/caiso260_demand_vintage"
NAME = "eia860_generator_retired_within_window.parquet"


def build(year: int, arm: bool = False) -> dict:
    """Return ``run_year``'s ``fleet_only`` payload for one year and one side.

    Built through the same ``run_calibration.run_year`` entry a real solve uses, off the
    committed keeper's own ``meta.json``, so every recorded override lands exactly as it
    does in the LP. The armed side routes the new field through ``prb_overrides``, which
    is byte-identical to what ``replay_keeper.py --set`` does for a ``ScenarioConfig``
    field.

    Args:
        year: Solve year to build for.
        arm: True to arm ``gas_electric_power_monthly_level``.

    Returns:
        The ``fleet_only`` payload dict.
    """
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = rk.build_kwargs(meta)
    sig = set(rc.run_year.__code__.co_varnames[: rc.run_year.__code__.co_argcount])
    call = {k: v for k, v in kw.items() if k in sig}
    call.update(
        year=year,
        iso=meta["iso"],
        hours=8760,
        fleet_only=True,
        gas_price=meta["gas_prices"][str(year)],
        ttc_overrides={},
    )
    if arm:
        call["prb_overrides"] = dict(call.get("prb_overrides") or {})
        call["prb_overrides"]["gas_electric_power_monthly_level"] = True
    return rc.run_year(**call)


def ids(payload: dict) -> list[str]:
    """Return one stable unit id per LP row, in row order.

    Args:
        payload: A ``fleet_only`` payload.

    Returns:
        A list of unit-id strings, one per LP row.
    """
    fa = payload["fleet_arrays"]
    for attr in ("unit_ids", "unit_id", "gen_ids", "ids", "names"):
        v = getattr(fa, attr, None)
        if v is not None and len(v) == fa.n_gen:
            return [str(x) for x in v]
    return [
        str(getattr(g, "unit_id", getattr(g, "name", i)))
        for i, g in enumerate(payload["fleet"])
    ]


def _repoint_to_old_vintage() -> Path:
    """Point ``paths.active_eia860_dir`` at a >=2023-filtered retiree parquet.

    Nothing under ``data/raw`` is modified: the alternate vintage is a temp directory of
    symlinks with only the retiree parquet rewritten.

    Returns:
        The temp directory now serving as the EIA-860 vintage.
    """
    real = paths.active_eia860_dir()
    tmp = Path(tempfile.mkdtemp(prefix="eia860_pre7934_"))
    for f in os.listdir(real):
        if f != NAME:
            os.symlink(real / f, tmp / f)
    full = pd.read_parquet(real / NAME)
    full[full.planned_retirement_year >= 2023].reset_index(drop=True).to_parquet(
        tmp / NAME, index=False
    )
    paths.active_eia860_dir = lambda *a, **k: tmp
    for name in list(sys.modules):
        mod = sys.modules[name]
        if not (name.startswith("market_sim") or name.startswith("scripts")):
            continue
        if getattr(mod, "active_eia860_dir", None) is not None:
            try:
                mod.active_eia860_dir = lambda *a, **k: tmp
            except Exception:
                pass
        for attr in dir(mod):
            obj = getattr(mod, attr, None)
            if hasattr(obj, "cache_clear"):
                try:
                    obj.cache_clear()
                except Exception:
                    pass
    return tmp


def card_a(year: int) -> None:
    """Measure the retiree-window vintage delta on CAISO's fleet for one year.

    Args:
        year: Solve year to build for.
    """
    new = build(year)
    _repoint_to_old_vintage()
    old = build(year)

    ni, oi = ids(new), ids(old)
    idx = {u: i for i, u in enumerate(ni)}
    oidx = {u: i for i, u in enumerate(oi)}
    fa, fo = new["fleet_arrays"], old["fleet_arrays"]
    pn = np.asarray(fa.pmax, float)
    po = np.asarray(fo.pmax, float)
    an = np.asarray(fa.availability, float)
    ao = np.asarray(fo.availability, float)
    effn = pn[:, None] * an
    effo = po[:, None] * ao

    print(f"\n=== CARD A — CAISO {year}: 2019-window (HEAD) vs 2023-window (pre-7934e92c) ===")
    extra = sorted(set(ni) - set(oi))
    missing = sorted(set(oi) - set(ni))
    print(f"  rows {len(ni)} vs {len(oi)}   extra={len(extra)}  missing={len(missing)}")
    if extra:
        ex = np.array([idx[u] for u in extra])
        print(f"  extra rows nameplate pmax sum         = {pn[ex].sum():.4f} MW")
        print(f"  extra rows EFFECTIVE MW-h             = {effn[ex].sum():.10f}")
        print(f"  extra rows max effective MW in any h  = {effn[ex].max():.10f}")

    common = [u for u in ni if u in oidx]
    cn = np.array([idx[u] for u in common])
    co = np.array([oidx[u] for u in common])
    dp = np.abs(pn[cn] - po[co])
    da = np.abs(an[cn] - ao[co])
    dm = np.abs(new["mc_base"][cn] - old["mc_base"][co])
    tn, to = effn[cn].sum(), effo[co].sum()
    print(f"  SHARED rows ({len(common)}):")
    print(f"    max|d pmax|    = {dp.max():.10f} MW")
    print(f"    max|d avail|   = {da.max():.10f}")
    print(f"    max|d mc_base| = {dm.max():.10f} $/MWh")
    print(f"    effective MW-h: HEAD {tn:.6f}  pre {to:.6f}  delta {tn - to:+.6f} ({(tn - to) / to * 100:+.6f}%)")
    moved = [common[i] for i in np.where(dp > 1e-9)[0]]
    print(f"    rows with moved pmax: {len(moved)}")
    for u in moved[:20]:
        i, j = idx[u], oidx[u]
        print(f"      {u}: pmax {po[j]:.4f} -> {pn[i]:.4f} ({pn[i] - po[j]:+.4f} MW)")


def card_b(year: int) -> None:
    """Census which cells ``gas_electric_power_monthly_level`` reaches for one year.

    Args:
        year: Solve year to build for.
    """
    c = build(year, arm=False)
    a = build(year, arm=True)
    print(f"\n=== CARD B — CAISO {year}: seam OFF vs ON at HEAD ===")
    for key in ("fuel_prices", "mc_base"):
        x = np.asarray(c[key], float)
        y = np.asarray(a[key], float)
        if x.shape != y.shape:
            print(f"  {key}: SHAPE MISMATCH {x.shape} vs {y.shape}")
            continue
        d = np.abs(y - x)
        n = int((d > 1e-12).sum())
        print(f"  {key}: shape {x.shape}  cells moved {n}/{d.size}  max|d| {d.max():.10f}  mean|d| {d.mean():.10f}")
        if n:
            rows = np.unique(np.where(d > 1e-12)[0])
            print(f"    rows touched: {len(rows)}/{d.shape[0]}")


if __name__ == "__main__":
    yr = int(sys.argv[1])
    which = sys.argv[2].upper()
    if which == "A":
        card_a(yr)
    else:
        card_b(yr)
