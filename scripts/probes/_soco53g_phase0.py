"""soco-53g phase 0 (ZERO LP): is ``coal_prb_proxy_own_iso`` live at SOCO at all?

``FINDING-soco-53f`` §9 item 1 routed SOCO-53g on the reading that SOCO's three
PRB plants (6002 Miller, 6073 Daniel, 6257 Scherer) are priced off the
hand-curated ERCOT-only reporter pool and are therefore under-priced by
+0.85 / +0.75 / +0.85 $/MMBtu, ~$9.7/MWh. Both pooled numbers are right; the
inference is not, because **neither pool reaches the LP**. This probe establishes
that mechanically, before any solve (rule 29 ``[R-SCREEN]`` clause 0):

* ``series``     -- re-derives BOTH pooled series from scratch, monthly, and
  reports level vs shape (the write-up must say which this mechanism is);
* ``coverage``   -- reporter depth per pool and the count of NaN-FILLED months,
  which decides whether rule 14's misalignment exception can apply;
* ``decompose``  -- replays ``run_calibration.py``'s exact fuel-price mutation
  sequence by hand (``resolve_fuel_prices(apply_monthly=False)`` ->
  ``apply_coal_supply_pricing`` -> ``apply_plant_monthly_fuel_prices``) with the
  proxy OFF and ON, snapshotting after each step, so the step at which the
  mechanism is erased is visible rather than inferred;
* ``rule19``     -- the two-grain rule 19 ``[R-ONE-MECH]`` proof on ``fuel_prices``
  AND ``mc_base`` from ``run_year(..., fleet_only=True)`` rebuilds off the
  keeper's own bundle. The fleet-build grain shows nothing by construction: this
  mechanism moves FUEL PRICE, not heat rate.

Measured 2026-09-20 against ``2026-09-20-soco53f-measured-coal-hr``: 2023 and
2024 move **zero** rows at max |d| exactly 0.000000000000; 2025 moves four
tranche rows of ONE plant (6073 Daniel) for 744 contiguous hours (January),
because Daniel filed no January-2025 receipt and the nearby-plant fallback did
not reach it. Full record: ``PRECOMMIT-soco-53g-2026-09-20.md`` §2-§4.

Run::

    python3 scripts/probes/_soco53g_phase0.py series
    python3 scripts/probes/_soco53g_phase0.py coverage
    python3 scripts/probes/_soco53g_phase0.py decompose 2023 2024 2025 --bundle <dir>
    python3 scripts/probes/_soco53g_phase0.py rule19    2023 2024 2025 --bundle <dir>
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

#: The keeper's recomposed span. A slim committed bundle is NOT enough -- the
#: ``fleet_only`` rebuild needs ``derived_run_year_inputs``, so re-compose the
#: per-year legs first (``scripts/probes/soco53f_compose_span.py``).
DEFAULT_BUNDLE = Path("results/calibration/soco53f_coal_hr")

#: SOCO's PRB population, from ``coal_supply_by_iso("SOCO")``. Declared here so
#: the probe cannot be silently re-pointed. 3 Barry / 26 Gaston / 703 Bowen are
#: ``bituminous`` and are outside this mechanism entirely -- ``price_by_supply``
#: carries only ``lignite`` and ``prb`` keys, so a bituminous row is skipped.
SOCO_PRB = (6002, 6073, 6257)


def _series() -> None:
    import market_sim.data.fuel.coal as fc
    from market_sim.data.coal import COAL_PLANT_SUPPLY, coal_supply_by_iso

    print(
        "ERCOT-default pool:",
        sorted(p for p, s in COAL_PLANT_SUPPLY.items() if s == "prb"),
    )
    print("SOCO map          :", dict(sorted(coal_supply_by_iso("SOCO").items())))
    a, b = fc._prb_monthly_actuals(None), fc._prb_monthly_actuals("SOCO")
    for y in sorted(set(a) & set(b)):
        da, db = a[y], b[y]
        print(f"\n--- {y} ---")
        print("  default:", np.array2string(da, precision=4, max_line_width=200))
        print("  SOCO   :", np.array2string(db, precision=4, max_line_width=200))
        print(
            f"  mean {da.mean():.4f} -> {db.mean():.4f}  (d {db.mean() - da.mean():+.4f})"
        )
        print(
            f"  LEVEL-vs-SHAPE: monthly ratio {np.min(db / da):.4f}-{np.max(db / da):.4f}, "
            f"corr {np.corrcoef(da, db)[0, 1]:+.4f}, cv {da.std() / da.mean():.4f} -> "
            f"{db.std() / db.mean():.4f}"
        )


def _coverage() -> None:
    from market_sim.data.coal import COAL_PLANT_SUPPLY, coal_supply_by_iso
    from market_sim.data.fuel._shared import _pkg_ns

    costs = _pkg_ns()._load_monthly_cache(None)
    pools = {
        "ERCOT-default": sorted(p for p, s in COAL_PLANT_SUPPLY.items() if s == "prb"),
        "SOCO-own": sorted(
            p
            for p, s in coal_supply_by_iso("SOCO").items()
            if s in ("prb", "subbituminous")
        ),
    }
    for label, pool in pools.items():
        sub = costs[
            costs["plant_id"].isin(pool)
            & (costs["fuel_group"] == "Coal")
            & costs["price_per_mmbtu"].notna()
            & (costs["quantity"] > 0)
        ]
        print(
            f"\n==== {label}: {len(pool)} listed, {sub['plant_id'].nunique()} filing ===="
        )
        for year in sorted(sub["year"].unique()):
            ry = sub[sub["year"] == year]
            per_m = ry.groupby("month")["plant_id"].nunique()
            byp = ry.groupby("plant_id").agg(
                months=("month", "nunique"), qty=("quantity", "sum")
            )
            byp["share"] = byp["qty"] / byp["qty"].sum()
            print(
                f"  {int(year)}: months {len(per_m)}/12  NaN-FILLED {12 - len(per_m)}  "
                f"reporters/month {per_m.min()}-{per_m.max()} (mean {per_m.mean():.2f})  "
                + str(
                    {
                        int(k): (int(v.months), round(float(v.share), 4))
                        for k, v in byp.iterrows()
                    }
                )
            )


def _build(bundle: Path, year: int, arm: bool):
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        # NOT a solve_and_persist kwarg -- ScenarioConfig only, so `--set` and
        # this probe both route it through the generic prb_overrides channel.
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"]["coal_prb_proxy_own_iso"] = True
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _decompose(bundle: Path, years: list[int]) -> None:
    from market_sim.data.fuel import (
        apply_coal_supply_pricing,
        apply_plant_monthly_fuel_prices,
        resolve_fuel_prices,
    )

    for year in years:
        built = _build(bundle, year, arm=False)
        cfg, fleet, fa = built["config"], built["fleet"], built["fleet_arrays"]

        def seq(proxy: bool):
            c = dataclasses.replace(cfg, coal_prb_proxy_own_iso=proxy)
            fp = resolve_fuel_prices(c, fa, year, apply_monthly=False)
            base = fp.copy()
            apply_coal_supply_pricing(fp, fleet, c, year)
            after = fp.copy()
            mask = apply_plant_monthly_fuel_prices(fp, fa, c, year)
            return base, after, fp.copy(), mask

        b0, s0, f0, m0 = seq(False)
        b1, s1, f1, _ = seq(True)
        mx = lambda x, y: float(np.max(np.abs(x - y)))  # noqa: E731
        print(f"\n===== {year} mutation sequence, proxy OFF vs ON =====")
        print(
            f"  1 resolve_fuel_prices(apply_monthly=False)  max|d| = {mx(b0, b1):.12f}"
        )
        print(
            f"  2 after apply_coal_supply_pricing           max|d| = {mx(s0, s1):.12f}"
        )
        print(
            f"  3 after apply_plant_monthly_fuel_prices     max|d| = {mx(f0, f1):.12f}"
        )
        r2 = np.where(np.abs(s0 - s1).max(axis=1) > 0)[0]
        r3 = np.where(np.abs(f0 - f1).max(axis=1) > 0)[0]
        print(f"  rows moved at step 2: {len(r2)}   STILL moved at step 3: {len(r3)}")
        for i in r2:
            g = fleet[i]
            wrote = int(np.asarray(m0)[i].sum()) if m0 is not None else -1
            print(
                f"    idx={i:3d} plant={getattr(g, 'plant_code', None)} "
                f"{getattr(g, 'name', None)!r:38s} overlay wrote {wrote}/8760  "
                f"step2 {s0[i].mean():.4f}->{s1[i].mean():.4f}  "
                f"step3 {f0[i].mean():.4f}->{f1[i].mean():.4f} "
                f"(max|d| {np.abs(f0[i] - f1[i]).max():.12f})"
            )
        if len(r3):
            hrs = np.where(np.abs(f0 - f1).max(axis=0) > 0)[0]
            idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
            print(
                f"  LIVE HOURS: {len(hrs)}/8760, contiguous={len(hrs) == hrs.max() - hrs.min() + 1}, "
                f"{idx[hrs.min()]} .. {idx[hrs.max()]}, months "
                f"{dict(pd.Series(idx.month).iloc[hrs].value_counts().sort_index())}"
            )


def _rule19(bundle: Path, years: list[int]) -> None:
    for year in years:
        ctl, arm = _build(bundle, year, False), _build(bundle, year, True)
        cf, af = ctl["fuel_prices"], arm["fuel_prices"]
        cm, am = np.asarray(ctl["mc_base"]), np.asarray(arm["mc_base"])
        fleet = ctl["fleet"]
        print(f"\n===== {year} rule 19, two grains =====")
        print(
            f"  resolved coal_prb_proxy_own_iso ctl="
            f"{getattr(ctl['config'], 'coal_prb_proxy_own_iso', None)} "
            f"arm={getattr(arm['config'], 'coal_prb_proxy_own_iso', None)}   rows={len(fleet)}"
        )
        by_f: dict[str, float] = defaultdict(float)
        by_m: dict[str, float] = defaultdict(float)
        for i, g in enumerate(fleet):
            cls = (
                str(getattr(g, "unit_id", "") or getattr(g, "name", "")).split("_")[0]
                or "?"
            )
            by_f[cls] = max(by_f[cls], float(np.max(np.abs(af[i] - cf[i]))))
            by_m[cls] = max(by_m[cls], float(np.max(np.abs(am[i] - cm[i]))))
        nf = int((np.abs(af - cf).max(axis=1) > 0).sum())
        nm = int((np.abs(am - cm).max(axis=1) > 0).sum())
        print(
            f"  fuel_prices rows moved {nf}/{len(fleet)}   mc_base rows moved {nm}/{len(fleet)}"
        )
        for cls in sorted(set(by_f) | set(by_m)):
            print(
                f"      {cls:18s} fuel {by_f[cls]:.12f} $/MMBtu   mc {by_m[cls]:.12f} $/MWh"
            )
        for i in np.where(np.abs(am - cm).max(axis=1) > 0)[0]:
            g = fleet[i]
            d = (am[i] - cm[i])[np.abs(am[i] - cm[i]) > 0]
            print(
                f"    MOVED idx={i:3d} {getattr(g, 'name', None)!r:38s} "
                f"hours={d.size}  d_mean={d.mean():+.4f} d_max={d.max():+.4f} $/MWh"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("series", "coverage", "decompose", "rule19"))
    ap.add_argument("years", nargs="*", type=int)
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    a = ap.parse_args()
    years = a.years or [2023, 2024, 2025]
    if a.mode == "series":
        _series()
    elif a.mode == "coverage":
        _coverage()
    elif a.mode == "decompose":
        _decompose(Path(a.bundle), years)
    else:
        _rule19(Path(a.bundle), years)


if __name__ == "__main__":
    main()
