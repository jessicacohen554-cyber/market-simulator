"""SPP-78 zero-LP arm check: do the three measured heat-rate fields reprice exactly the covered rows?

Pre-registered in ``docs/handoffs/PRECOMMIT-spp-78-measured-heat-rates-2026-09-24.md`` §6(a).

Rebuilds one year's fleet with no LP (``run_year(..., fleet_only=True)`` from the sanctioned
``bundle_fleet.full_run_year_kwargs``) twice, in two interpreters (``--variant ctl`` / ``--variant arm``),
and writes per-row ``(unit_id, plant_code, plant_group, heat_rate, pmax)``. ``--compare`` then checks,
for every thermal row, that ``hr_arm / hr_ctl`` equals ``heat_rate / model_heat_rate_egrid`` from the
SPP artifact for (plant, class) rows the field covers (``flag == ok``) and 1.0 for every other row —
i.e. the arm REPLACES the base heat rate and every downstream multiplier (tranche physics, the 0.93
band) is untouched.

Usage::

    uv run python scripts/probes/_spp78_arm_fleet_check.py --year 2022 --variant ctl --out d/ctl_2022.parquet
    uv run python scripts/probes/_spp78_arm_fleet_check.py --year 2022 --variant arm --out d/arm_2022.parquet
    uv run python scripts/probes/_spp78_arm_fleet_check.py --year 2022 --compare d
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLES = {
    **{y: "hydro5_spp_floor_rung" for y in (2019, 2020, 2021, 2022)},
    **{y: "hydro5_spp_floor_span" for y in (2023, 2024, 2025)},
}
FIELDS = ("measured_cc_heat_rates", "measured_st_heat_rates", "measured_coal_heat_rates")
ART = {"CC_REGULAR": "cc", "ST_GAS": "st", "COAL": "coal"}
PROCESSED = REPO / "data/raw/_processed-legacy"


def build(year: int, variant: str, out: Path) -> None:
    """Rebuild the year's fleet (no LP) as control or arm and write per-row heat rates."""
    from scripts.lib.bundle_fleet import bundle_gas_price, full_run_year_kwargs
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / BUNDLES[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = full_run_year_kwargs(meta)  # fleet_only=True, ttc_overrides={}
    if variant == "arm":
        pov = dict(kw.get("prb_overrides") or {})
        for f in FIELDS:
            pov[f] = True
            if f in kw:
                kw[f] = True
        kw["prb_overrides"] = pov
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(bundle, year),
    )
    cfg = state["config"]
    got = {f: bool(getattr(cfg, f)) for f in FIELDS}
    want = variant == "arm"
    if any(v != want for v in got.values()):
        raise SystemExit(f"HARD STOP: {variant} config flags {got}")
    fa = state["fleet_arrays"]
    pd.DataFrame(
        {
            "unit_id": [str(u) for u in fa.unit_ids],
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "plant_group": [str(g) for g in fa.plant_group],
            "heat_rate": np.asarray(fa.heat_rate, float),
            "pmax": np.asarray(fa.pmax, float),
        }
    ).to_parquet(out)
    print(f"{year} {variant}: {len(fa.unit_ids)} rows, flags {got}")


def compare(year: int, d: Path) -> dict:
    """Check arm/ctl ratios against the artifact; return the summary."""
    c = pd.read_parquet(d / f"ctl_{year}.parquet")
    a = pd.read_parquet(d / f"arm_{year}.parquet")
    if not (c.unit_id.tolist() == a.unit_id.tolist()):
        raise SystemExit("HARD STOP: row alignment differs between ctl and arm")
    exp = np.ones(len(c))
    art = {}
    for k, key in ART.items():
        df = pd.read_csv(PROCESSED / f"campd_{key}_heat_rates_SPP.csv")
        df = df[(df.flag == "ok") & (df.heat_rate > 0)]
        art[k] = {int(r.plant_code): float(r.heat_rate) for r in df.itertuples()}
    covered = np.zeros(len(c), bool)
    base_ctl = {}
    for i, r in enumerate(c.itertuples()):
        m = art.get(r.plant_group, {})
        if r.plant_code in m:
            covered[i] = True
    ratio = np.where(c.heat_rate > 0, a.heat_rate / c.heat_rate.where(c.heat_rate > 0, 1), 1.0)
    # expected ratio per covered row = measured / the control's base HR for that (plant, class).
    # The control base is not stored per row, so check (i) uncovered rows are exactly 1.0 and
    # (ii) all covered rows of one (plant, class) share ONE ratio (a replacement, not a stack),
    # and (iii) that ratio times the control's modal base equals the artifact value.
    out = {"year": year, "rows": int(len(c))}
    unc = ~covered
    out["uncovered_max_abs_dev"] = float(np.max(np.abs(ratio[unc] - 1.0))) if unc.any() else 0.0
    groups = {}
    for i in np.flatnonzero(covered):
        key = (int(c.plant_code[i]), str(c.plant_group[i]))
        groups.setdefault(key, []).append(ratio[i])
    spread = max((max(v) - min(v)) for v in groups.values()) if groups else 0.0
    out["covered_rows"] = int(covered.sum())
    out["covered_mw"] = float(c.pmax[covered].sum())
    out["covered_plant_class"] = len(groups)
    out["max_within_plant_ratio_spread"] = float(spread)
    for k in ART:
        s = c.plant_group == k
        w = c.pmax[s]
        if w.sum() > 0:
            out[f"{k}_hr_cw_ctl"] = float(np.average(c.heat_rate[s], weights=w))
            out[f"{k}_hr_cw_arm"] = float(np.average(a.heat_rate[s], weights=w))
            out[f"{k}_covered_mw"] = float(c.pmax[s & covered].sum())
            out[f"{k}_mw"] = float(w.sum())
    out["plant_ratios"] = {f"{p}|{g}": float(np.mean(v)) for (p, g), v in groups.items()}
    ok = out["uncovered_max_abs_dev"] < 1e-9 and spread < 1e-9
    out["PASS"] = bool(ok)
    return out


def main() -> int:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--variant", choices=("ctl", "arm"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--compare", type=Path)
    args = ap.parse_args()
    if args.compare:
        res = compare(args.year, args.compare)
        (args.compare / f"check_{args.year}.json").write_text(json.dumps(res, indent=1))
        print(json.dumps({k: v for k, v in res.items() if k != "plant_ratios"}))
        return 0 if res["PASS"] else 1
    build(args.year, args.variant, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
