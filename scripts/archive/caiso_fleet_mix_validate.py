"""CAISO fleet-mix / commitment decomposition — model vs EIA-923 + EIA-930.

TASK-2 diagnostic (handoff 2026-06): the CAISO 2024 backcast gets the right
TOTAL gas (~+4%) on the WRONG units — CC_REGULAR/ST_GAS over-run, CT_PEAKER and
CC_CHP under-run. This validator localizes WHERE (which class) and WHEN (which
hour-of-day) the gas mix goes wrong, so the commitment bug can be isolated
before any model change.

Two views:

  [A] Per-class annual volume — model dispatch (grouped by ``klass``, the real
      plant_group, after the same OTHER_FOSSIL re-bucketing the scorecard uses)
      vs the authoritative ``classFull`` benchmark (EIA-923 net gen per class,
      grid-delivered = minus the held-out BTM CHP supply, then any incomplete
      fossil vintage scaled up to the EIA-930 fuel total — replicated exactly
      from render_calibration_html.build_payload). This is the smoking-gun
      table the dashboard scorecard scores.

  [B] Per-hour-of-day gas dispatch — the model's gas classes by hour-of-day
      (mean MW), and the model TOTAL non-CHP gas vs the EIA-930 gas series by
      hour. EIA-930 carries only aggregate gas (no CC/CT/ST split), so the
      within-gas split is the model's own — which reveals whether the model
      meets the evening ramp (h17-21) with fast peakers (CT_PEAKER) or with
      must-run CC/steam (the suspected commitment defect).

Usage:
    .venv/bin/python scripts/archive/caiso_fleet_mix_validate.py BUNDLE_DIR [--year 2024]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import importlib.util  # noqa: E402

from market_sim.config.plant_taxonomy import classes_for_fuel930  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    OTHER_FOSSIL_CLASS,
    apply_other_fossil_scoring,
)

_spec = importlib.util.spec_from_file_location(
    "bundle_io", str(REPO / "scripts" / "lib" / "bundle_io.py")
)
_bio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bio)
bundle_input_path = _bio.bundle_input_path

_MWH_PER_TWH = 1e6
_VINTAGE_RECONCILE_FRAC = 0.97
_GAS_GROUPS = classes_for_fuel930("gas")
_COAL_GROUPS = classes_for_fuel930("coal")
# The gas classes that dispatch to the GRID (the EIA-930 "gas" series the model
# is scored against subtracts the BTM CHP, so the grid comparison is non-CHP).
_GAS_GRID = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
_GAS_ALL = ("CC_REGULAR", "CC_CHP", "CT_CHP", "CT_PEAKER", "ST_GAS", OTHER_FOSSIL_CLASS)


def _class_hourly(disp: pd.DataFrame) -> dict[str, np.ndarray]:
    piv = (
        disp.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack("klass", fill_value=0.0)
        .sort_index()
    )
    return {c: piv[c].to_numpy(float) for c in piv.columns}


def _class_full_bench(
    bdir: Path, year: int
) -> tuple[dict[str, float], dict[str, float]]:
    """Replicate build_payload's ``classFull`` AND the raw EIA-923 per-class (TWh).

    Returns ``(raw923, classFull)``. ``raw923`` is the grid-delivered EIA-923 net
    gen per class (BTM subtracted) — the "+4% total" benchmark the handoff table
    uses. ``classFull`` additionally scales each fossil fuel's classes up to the
    EIA-930 fuel total when the 923 vintage is incomplete (< 0.97x) — the
    dashboard scorecard's benchmark (the 17-TWh 923-vs-930 gas gap, hypothesis 4).
    """
    e923 = pd.read_parquet(bundle_input_path(bdir, "eia923"))
    e923 = e923[e923["year"] == year]
    e923 = apply_other_fossil_scoring(e923, year, plant_col="plant_id")
    e923_cls = e923.groupby("klass")["annual_mwh"].sum()

    btm_path = bundle_input_path(bdir, "btm")
    btm_cls: dict[str, float] = {}
    if btm_path is not None:
        btm_all = pd.read_parquet(btm_path)
        _by = btm_all[(btm_all["year"] == year) & (btm_all["pass"] == "P1")]
        btm_cls = dict(zip(_by["klass"], _by["btm_twh"]))

    raw923 = {
        str(g): float(v) / _MWH_PER_TWH - float(btm_cls.get(str(g), 0.0))
        for g, v in e923_cls.items()
    }
    cfull = dict(raw923)

    # EIA-930 fuel totals (for the incomplete-vintage scale-up).
    e930 = pd.read_parquet(bundle_input_path(bdir, "eia930"))
    e930 = e930[e930["year"] == year]
    e930d = {
        f: float(e930[e930["series"] == f]["mw"].sum()) / _MWH_PER_TWH
        for f in ("gas", "coal")
    }
    for fuel, klasses in (("gas", _GAS_GROUPS), ("coal", _COAL_GROUPS)):
        present = [g for g in klasses if g in cfull]
        cur = sum(cfull[g] for g in present)
        tgt = float(e930d.get(fuel, 0.0))
        if tgt > 0.0 and 0.0 < cur < _VINTAGE_RECONCILE_FRAC * tgt:
            scale = tgt / cur
            for g in present:
                cfull[g] *= scale
    return raw923, cfull


def _e930_gas_hourly(bdir: Path, year: int) -> np.ndarray | None:
    e930 = pd.read_parquet(bundle_input_path(bdir, "eia930"))
    e930 = e930[(e930["year"] == year) & (e930["series"] == "gas")].sort_values("hour")
    return e930["mw"].to_numpy(float) if len(e930) else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--pass", dest="pass_label", default="P2")
    args = ap.parse_args()

    bdir, year = args.bundle, args.year
    disp_path = bdir / "dispatch" / f"{year}_{args.pass_label}.parquet"
    disp = apply_other_fossil_scoring(
        pd.read_parquet(disp_path), year, plant_col="plant_code"
    )
    T = int(disp["hour"].max()) + 1

    mh = _class_hourly(disp)
    model_twh = {k: v.sum() / _MWH_PER_TWH for k, v in mh.items()}
    raw923, bench = _class_full_bench(bdir, year)

    print(
        f"\n=== [A] CAISO {year} per-class volume  {bdir.name} ({args.pass_label}) ==="
    )
    print("    (raw923 = EIA-923 grid-delivered; 930scl = scaled to EIA-930 gas total)")
    print(
        f"    {'class':<14}{'model':>8}{'raw923':>8}{'Δ923':>8}"
        f"{'930scl':>8}{'Δ930':>8}{'Δ930%':>7}"
    )
    classes = [c for c in _GAS_ALL if c in model_twh or c in bench]
    extra = sorted(
        set(list(model_twh) + list(bench))
        - set(_GAS_ALL)
        - {"wind", "solar", "nuclear", "hydro", "biomass", "import", "OTHER", "oil"}
    )
    gm = g923 = g930 = 0.0
    for c in classes + extra:
        m, r, b = model_twh.get(c, 0.0), raw923.get(c, 0.0), bench.get(c, 0.0)
        d930 = m - b
        dp = 100 * d930 / b if b else float("nan")
        flag = "  <<<" if (c in _GAS_ALL and abs(d930) >= 1.0) else ""
        if c in _GAS_ALL:
            gm += m
            g923 += r
            g930 += b
        print(
            f"    {c:<14}{m:>8.2f}{r:>8.2f}{m - r:>+8.2f}"
            f"{b:>8.2f}{d930:>+8.2f}{dp:>+7.0f}{flag}"
        )
    print(
        f"    {'GAS TOTAL':<14}{gm:>8.2f}{g923:>8.2f}{gm - g923:>+8.2f}"
        f"{g930:>8.2f}{gm - g930:>+8.2f}{100 * (gm - g930) / g930:>+7.0f}"
    )
    print(
        f"    -> model gas {gm:.1f} is {100 * (gm - g923) / g923:+.0f}% vs EIA-923 "
        f"({g923:.1f}) but {100 * (gm - g930) / g930:+.0f}% vs EIA-930-scaled "
        f"({g930:.1f}); 923-vs-930 gap = {g930 - g923:.1f} TWh."
    )

    # [B] per-hour-of-day gas dispatch
    hod = np.arange(T) % 24
    print(f"\n=== [B] CAISO {year} gas dispatch by hour-of-day (mean MW) ===")
    head = "    h   " + "".join(
        f"{c.replace('CC_', 'CC').replace('CT_', 'CT').replace('ST_', 'ST'):>9}"
        for c in _GAS_ALL
    )
    print(head + f"{'GASgrid':>9}{'EIA930':>9}{'Δgas':>8}")
    e930_gas = _e930_gas_hourly(bdir, year)
    grid_by_h = np.zeros(24)
    e930_by_h = np.zeros(24)
    for h in range(24):
        sel = hod == h
        row = f"    h{h:02d} "
        for c in _GAS_ALL:
            v = mh.get(c, np.zeros(T))[sel].mean()
            row += f"{v:>9.0f}"
        grid = sum(mh.get(c, np.zeros(T))[sel].mean() for c in _GAS_GRID)
        grid_by_h[h] = grid
        e9 = e930_gas[:T][sel].mean() if e930_gas is not None else float("nan")
        e930_by_h[h] = e9
        row += f"{grid:>9.0f}{e9:>9.0f}{grid - e9:>+8.0f}"
        print(row)

    # Evening-ramp focus: who meets h17-21
    print("\n=== [C] evening ramp h17-21 — model gas-class composition (mean MW) ===")
    ev = np.isin(hod, [17, 18, 19, 20, 21])
    night = np.isin(hod, [0, 1, 2, 3, 4])
    for label, sel in (("overnight h00-04", night), ("evening h17-21", ev)):
        comp = {c: mh.get(c, np.zeros(T))[sel].mean() for c in _GAS_ALL}
        tot = sum(comp.values())
        print(f"  {label}: total gas {tot:7.0f} MW")
        for c in _GAS_ALL:
            if comp[c] > 1:
                print(f"      {c:<14}{comp[c]:>8.0f} MW  ({100 * comp[c] / tot:4.0f}%)")
    # ramp delivered by each class evening-minus-overnight
    print("  RAMP (evening - overnight) delivered by class:")
    for c in _GAS_ALL:
        dv = mh.get(c, np.zeros(T))[ev].mean() - mh.get(c, np.zeros(T))[night].mean()
        if abs(dv) > 1:
            print(f"      {c:<14}{dv:>+8.0f} MW")


if __name__ == "__main__":
    main()
