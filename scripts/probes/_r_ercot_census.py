"""R-ERCOT phase 0: zero-LP fleet census of the 2019-2025 re-solve recipe.

AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24 §5.3.2, step 0. For each
year rebuilds the recipe's LP fleet with ``run_year(fleet_only=True)`` (the
sanctioned replay_keeper reconstruction) and reports (a) the EIA-860 source
resolved, (b) bin heat-rate sources (measured / eGRID / sheet / class default)
and the class-default plant list, (c) outage-family window counts, plus
per-class nameplate / availability / mc_base means for the arm vs the
incumbent recipe at HEAD, so every input delta is attributed before any LP.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_r_ercot_census.py \
        --years 2019 2020 2021 2022 2023 2024 2025 --out <json>
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(p))

BUNDLE = REPO / "results/calibration/ercot_mer20260919_five_year"

#: The arm's deltas over the incumbent recipe (PRECOMMIT §3).
ARM_SET = {
    "eia860_vintage_tracks_solve_year": True,
    "measured_ct_heat_rates": True,
    "measured_coal_heat_rates": True,
    "measured_st_heat_rates": True,
    "measured_cc_heat_rates": True,
    "measured_chp_heat_rates": True,
    "unit_outage_short_windows": True,
    "unit_outage_short_windows_gas": True,
}
#: The recipe group each year takes (PRECOMMIT §2): 2019/2020 join 2021/2022.
OVERLAY_YEAR = {2019: 2021, 2020: 2021, 2021: 2021, 2022: 2022, 2023: 2023,
                2024: 2024, 2025: 2025}


def build(year: int, arm: bool) -> dict:
    """Return the fleet-only state for ``year`` under the arm or the incumbent."""
    from replay_keeper import (apply_config_overlay, config_partition_overlay,
                               run_year_kwargs)
    from run_calibration import run_year
    from run_calibration_full import _henry_hub_actual, _load_reference
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw["inject_biomass_mustrun"] = True  # every ERCOT keeper year: True (sidecar)
    apply_config_overlay(kw, config_partition_overlay(meta, OVERLAY_YEAR[year]))
    if arm:
        kw.setdefault("prb_overrides", {})
        kw["prb_overrides"] = dict(kw["prb_overrides"], **ARM_SET)
    else:
        # the incumbent posture at HEAD: pin the F1-flipped defaults back off
        kw.setdefault("prb_overrides", {})
        kw["prb_overrides"] = dict(
            kw["prb_overrides"],
            **{k: False for k in ARM_SET},
        )
    clear_fleet_caches()
    gp = float(_henry_hub_actual(_load_reference(), year))
    with contextlib.redirect_stdout(io.StringIO()):
        st = run_year(year, "ERCOT", 8760, gp, {}, fleet_only=True, **kw)
    return st


def _wmedian(x: np.ndarray, w: np.ndarray) -> float:
    """Capacity-weighted median (the band means are dominated by peak rungs)."""
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return round(float(x[o][np.searchsorted(c, 0.5 * c[-1])]), 3) if c[-1] > 0 else float("nan")


def summarize(st: dict) -> dict:
    """Per-class nameplate, mean availability, cap-weighted mc_base."""
    fa = st["fleet_arrays"]
    grp = np.array([str(g) for g in fa.plant_group])
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    mc = np.asarray(st["mc_base"], float)
    mc_mean = mc.mean(axis=1) if mc.ndim == 2 else mc
    out = {}
    for g in sorted(set(grp)):
        m = grp == g
        w = pmax[m]
        out[g] = {
            "mw": round(float(w.sum()), 1),
            "avail_mw_mean": round(float((av[m] * w[:, None]).sum(axis=0).mean()), 1),
            "n_units": int(m.sum()),
            "mc_base_capw_median": _wmedian(mc_mean[m], w),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from market_sim.config.paths import CAMPD_BINS_CSV
    from market_sim.data.fleet.campd_bins import resolve_bin_heat_rates
    detail = pd.read_csv(CAMPD_BINS_CSV)
    res = {}
    for y in args.years:
        flags = {k: True for k in ARM_SET if k.startswith("measured_")}
        hr, src = resolve_bin_heat_rates(detail, "ERCOT", y, flags, True)
        mw = detail["Nameplate_MW"].astype(float)
        dflt = detail[src == "default"]
        rec = {
            "bin_hr_mw_by_source": {k: round(float(mw[src == k].sum()), 1)
                                    for k in ("measured", "egrid", "sheet", "default")},
            "class_default_plants": [
                f"{int(r.Plant_Code)} {r.Plant_Name} ({r.Plant_Group}, {r.Nameplate_MW} MW)"
                for r in dflt.itertuples()],
            "bin_hr_capw_by_class": {
                g: {"sheet": round(float(np.average(
                        detail.loc[m, "Plant_Avg_HR_MMBtu_MWh"].fillna(hr[m]).fillna(10.0),
                        weights=mw[m])), 3),
                    "arm": round(float(np.average(hr[m].fillna(10.0), weights=mw[m])), 3)}
                for g, m in ((g, detail["Plant_Group"] == g)
                             for g in sorted(detail["Plant_Group"].unique()))},
        }
        for tag, arm in (("incumbent", False), ("arm", True)):
            try:
                st = build(y, arm)
                rec[tag] = summarize(st)
                cfg = st.get("config")
                if cfg is not None:
                    rec[tag + "_eia860_dir"] = str(getattr(cfg, "eia860_dir", ""))
            except Exception as exc:  # report, never mask
                rec[tag] = {"ERROR": f"{type(exc).__name__}: {exc}"}
        res[str(y)] = rec
        print(y, json.dumps(rec)[:600], flush=True)
    Path(args.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
