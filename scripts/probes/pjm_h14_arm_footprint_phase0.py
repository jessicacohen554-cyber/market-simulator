"""pjm-h14 phase 0g — does `coal_mustrun_requires_measured_row` FIRE, and by how much?

ZERO LP: ``run_year(..., fleet_only=True)`` on the designated keeper pair's own
committed recipes, control vs arm, reading the coal tranche capacities the LP
would be handed.

STATED AS A FOOTPRINT, NEVER A VERDICT (pjm-h13 correction #3): these are
PRE-SOLVE tranche capacities and the asserted floor they imply. What the solve
does with them is what the shards measure; nothing here predicts a gate.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CACHE = Path("/tmp/claude-0/h14/arm")
ARM_FIELD = "coal_mustrun_requires_measured_row"
BUNDLES = {
    2020: "results/calibration/pjm_h13_meritalloc_touchpoint",
    2021: "results/calibration/pjm_h13_meritalloc_touchpoint",
    2022: "results/calibration/pjm_h13_meritalloc_touchpoint",
    2023: "results/calibration/pjm_h13_meritalloc_span",
    2024: "results/calibration/pjm_h13_meritalloc_span",
    2025: "results/calibration/pjm_h13_meritalloc_span",
}


def tranches(year: int, arm: bool) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{'arm' if arm else 'ctl'}_{year}.parquet"
    if path.exists():
        return pd.read_parquet(path)

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / BUNDLES[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        ov = dict(kw.get("prb_overrides") or {})
        ov[ARM_FIELD] = True
        kw["prb_overrides"] = ov
    gas = float(meta["gas_prices"][str(year)])
    payload = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)
    gens = payload["fleet"] if isinstance(payload, dict) and "fleet" in payload else payload
    if hasattr(gens, "generators"):
        gens = gens.generators
    rows = []
    for g in gens:
        grp = str(getattr(g, "plant_group", "") or "")
        if not grp.startswith("COAL"):
            continue
        uid = str(getattr(g, "unit_id", getattr(g, "id", "")))
        rows.append(dict(
            plant_code=int(getattr(g, "plant_code", 0) or 0),
            name=str(getattr(g, "name", "")),
            group=grp,
            band=uid.rpartition("_")[2].rstrip("0123456789") or uid.rpartition("_")[2],
            pmax=float(getattr(g, "pmax_mw", 0.0) or 0.0),
            sync_pmin=float(getattr(g, "coal_sync_pmin_mw", 0.0) or 0.0),
            sync_frac=float(getattr(g, "coal_sync_online_frac", 1.0) or 1.0),
        ))
    df = pd.DataFrame(rows)
    df.to_parquet(path)
    return df


def main() -> None:
    print("### G1 FOOTPRINT — coal tranche capacity and asserted floor, control vs arm\n")
    print("    asserted_floor_TWh = sum over coal units of sync_pmin x round(sync_frac x 8760) / 1e6\n"
          "    (the hours the online%%-scaled window actually places the floor, before availability)\n")
    out = []
    for year in sorted(BUNDLES):
        c, a = tranches(year, False), tranches(year, True)
        def floor_twh(d):
            return float((d["sync_pmin"] * (d["sync_frac"] * 8760).round()).sum() / 1e6)
        def band_mw(d, b):
            return float(d[d["band"] == b]["pmax"].sum())
        out.append(dict(
            year=year,
            ctl_mustrun_MW=band_mw(c, "mustrun"), arm_mustrun_MW=band_mw(a, "mustrun"),
            ctl_sync_MW=band_mw(c, "sync"), arm_sync_MW=band_mw(a, "sync"),
            ctl_econ_MW=float(c[c["band"].str.startswith("econ")]["pmax"].sum()),
            arm_econ_MW=float(a[a["band"].str.startswith("econ")]["pmax"].sum()),
            ctl_total_MW=float(c["pmax"].sum()), arm_total_MW=float(a["pmax"].sum()),
            ctl_floor_TWh=floor_twh(c), arm_floor_TWh=floor_twh(a),
        ))
    t = pd.DataFrame(out)
    t["released_TWh"] = t["ctl_floor_TWh"] - t["arm_floor_TWh"]
    t["capacity_moved_MW"] = t["ctl_mustrun_MW"] - t["arm_mustrun_MW"]
    t["total_MW_delta"] = t["arm_total_MW"] - t["ctl_total_MW"]
    print(t.to_string(index=False, float_format=lambda v: f"{v:11.3f}"))

    print("\n### G2 CAPACITY CONSERVATION — the arm moves capacity between bands, it never removes MW\n")
    for r in out:
        print(f"  {r['year']}: total coal capacity ctl {r['ctl_total_MW']:11.3f} MW  "
              f"arm {r['arm_total_MW']:11.3f} MW  Δ {r['arm_total_MW']-r['ctl_total_MW']:+.6f} MW")

    print("\n### G3 SCOPE — which plants move, and do any COVERED plants move? (they must not)\n")
    pooled = pd.read_csv(REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv")
    covered = set(pooled[pooled["plant_group"].astype(str) == "COAL"]["plant_code"].astype(int))
    for year in sorted(BUNDLES):
        c, a = tranches(year, False), tranches(year, True)
        cm = c[c["band"] == "mustrun"].groupby("plant_code")["pmax"].sum()
        am = a[a["band"] == "mustrun"].groupby("plant_code")["pmax"].sum()
        keys = sorted(set(cm.index) | set(am.index))
        d = (am.reindex(keys).fillna(0.0) - cm.reindex(keys).fillna(0.0))
        moved = d[d.abs() > 1e-9]
        bad = [int(k) for k in moved.index if int(k) in covered]
        print(f"  {year}: {len(moved)} plants move ({moved.sum():+.1f} MW of must-run); "
              f"COVERED plants moved: {len(bad)} {bad if bad else ''}")


if __name__ == "__main__":
    main()
