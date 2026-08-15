"""miso-159 Phase 0 — the ``commission_year_cod_fallback`` instrument gates. **NO LP.**

PREREG: ``results/calibration/PREREG-miso159-commission-year-cod-fallback-2026-08-15.md``
(pushed and byte-verified BEFORE this probe ran). Gates implemented here:

* **V1** — with the flag ON, the production fleet's per-class capacity-weighted
  ``online_year`` reproduces the miso-158 census's ``true_capwt_online_year``
  to ±1.0 yr per class. The census weighted by bin-sheet NAMEPLATE while the
  LP fleet weights by dispatch ``pmax`` (the CHP classes' LP capacity is the
  grid-facing remainder of nameplate — the census's own V-C1 scope note), so
  the nameplate-weighted companion is computed unconditionally alongside; a
  breach attributable to the weighting basis is debugged against it per the
  S-V1 protocol rather than silently waived.
* **V2** — with the flag OFF (default), every ``THERMAL_AVAILABILITY``-classed
  row still carries ``online_year == 2010`` exactly (the miso-157 census), so
  the off path is behavior-identical to HEAD; and the two arms' config cache
  keys DIFFER (the S-CACHE pre-check — an armed run must never resolve the
  control's cached fleet).
* **V3** — both arms carry the keeper's fleet (n_gen 2929/2923/2923; 6 carry
  zones).
* **P-1** — the production-path availability delta (arm − off), per class and
  fleet-total, at annual / Jun–Sep / Jun–Sep-h12-17 grains, in GW — the
  fleet-path restatement of the census's overstatement table.

The fleet chain is the blessed production reconstruction
(``_miso134_ct_night_order_screen.build_year`` — runner.py's own chain), with
``_miso134.BUNDLE`` repointed to the current keeper and asserted (trap T-1).
Rule 22: 2023/2024/2025 only; nothing is solved, scored or registered here.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# T-1: the shared builder must read the CURRENT keeper bundle.
_m134.BUNDLE = REPO / "results/calibration/miso148_basis_B"
assert _m134.BUNDLE.is_dir(), "T-1: keeper bundle miso148_basis_B missing"

from market_sim.config.fuel_trajectories import (  # noqa: E402
    SUMMER_WEFOR_SHARE,
    THERMAL_AVAILABILITY,
)
from market_sim.data.cod_ramp import load_cod_map  # noqa: E402

# T-8: production functions, never re-implementations.
assert load_cod_map.__module__ == "market_sim.data.cod_ramp", "T-8: load_cod_map"
assert (
    _m134.build_year.__module__ == "_miso134_ct_night_order_screen"
), "T-8: build_year provenance"

YEARS = (2023, 2024, 2025)
V3_NGEN = {2023: 2929, 2024: 2923, 2025: 2923}
V1_TOL_YR = 1.0
# The model's fixed non-leap clock (shared with _miso134's MO/HOD).
MO, HOD = _m134.MO, _m134.HOD
SUMMER = np.isin(MO, (6, 7, 8, 9))
SUMMER_PEAK = SUMMER & (HOD >= 12) & (HOD < 18)

CENSUS_PATH = REPO / "results/calibration/_miso158_vintage_census.json"
OUT = REPO / "results/calibration/_miso159_cod_vintage_instrument.json"

# P-1 pre-registered bands (PREREG §5), capability REMOVED = off − on, GW.
P1_SUMMER_NONCHP_GW = (1.8, 2.8)
P1_ANNUAL_NONCHP_GW = (3.0, 5.0)


def _class_stats(fleet, arrays) -> dict:
    """Per-class online-year and availability-capability reductions."""
    labels = np.array([str(g.plant_group or "") for g in fleet])
    oy = np.array([int(g.online_year) for g in fleet], dtype=float)
    pmax = np.asarray(arrays.pmax, dtype=float)
    avail = arrays.availability  # (n_gen, 8760)
    out: dict = {"classes": {}, "n_gen": int(len(fleet))}
    for cls in sorted(THERMAL_AVAILABILITY):
        m = labels == cls
        if not m.any():
            continue
        w = pmax[m]
        cap_gw = float(w.sum() / 1000.0)
        availcap = avail[m] * w[:, None]
        out["classes"][cls] = {
            "rows": int(m.sum()),
            "lp_cap_gw": cap_gw,
            "capwt_online_year": float(np.average(oy[m], weights=w))
            if w.sum() > 0
            else None,
            "n_distinct_online_year": int(len(set(oy[m].tolist()))),
            "rows_at_2010": int((oy[m] == 2010.0).sum()),
            "cap_at_2010_gw": float(w[oy[m] == 2010.0].sum() / 1000.0),
            "availcap_annual_gw": float(availcap.sum(axis=0).mean() / 1000.0),
            "availcap_summer_gw": float(
                availcap[:, SUMMER].sum(axis=0).mean() / 1000.0
            ),
            "availcap_summer_peak_gw": float(
                availcap[:, SUMMER_PEAK].sum(axis=0).mean() / 1000.0
            ),
        }
    return out


def _nameplate_capwt(census_classes: dict, oy_by_plant: dict) -> dict:
    """Census-basis (bin-sheet nameplate) cap-weighted online year per class.

    The S-V1 attribution companion: re-weights the SAME per-plant online years
    the armed fleet carries by the census's own nameplate weights, so a V1 miss
    caused purely by the LP-vs-nameplate weighting basis is demonstrable.
    """
    bins = pd.read_csv(
        REPO / "data/raw/_processed-legacy/bin_assignments_MISO.csv",
        usecols=["Plant_Code", "Plant_Group", "Nameplate_MW"],
    )
    out = {}
    for cls, d in bins.groupby("Plant_Group"):
        if cls not in census_classes:
            continue
        oy = np.array(
            [oy_by_plant.get(int(pc), np.nan) for pc in d["Plant_Code"]], dtype=float
        )
        w = d["Nameplate_MW"].to_numpy(dtype=float)
        ok = ~np.isnan(oy)
        if ok.any():
            out[cls] = float(np.average(oy[ok], weights=w[ok]))
    return out


def main() -> dict:
    census = json.loads(CENSUS_PATH.read_text())["isos"]["MISO"]["classes"]
    true_oy = {c: v["true_capwt_online_year"] for c, v in census.items()}

    cfg0 = _m134.keeper_config()
    assert cfg0.commission_year_cod_fallback is False, (
        "keeper run_config must not carry the new flag"
    )

    # V2 cache-key half (S-CACHE pre-check): the armed config hashes distinctly.
    key_off = cfg0.cache_key()
    key_on = dataclasses.replace(cfg0, commission_year_cod_fallback=True).cache_key()
    assert key_off != key_on, "S-CACHE: armed config does not move the cache key"

    rec: dict = {
        "prereg": "PREREG-miso159-commission-year-cod-fallback-2026-08-15.md",
        "keeper_bundle": _m134.BUNDLE.name,
        "summer_wefor_share": float(SUMMER_WEFOR_SHARE),
        "cache_key_off": key_off,
        "cache_key_on": key_on,
        "years": {},
        "gates": {},
    }

    v1_rows, v2_ok, v3_ok = [], True, True
    for year in YEARS:
        cfg_off = dataclasses.replace(cfg0, weather_year=year)
        cfg_on = dataclasses.replace(cfg_off, commission_year_cod_fallback=True)
        yrec: dict = {}
        arm_stats: dict = {}
        oy_by_plant_on: dict = {}
        for arm, cfg in (("off", cfg_off), ("on", cfg_on)):
            # T-6: weather_year pinned per solve year.
            assert cfg.weather_year == year, "T-6: weather_year not pinned"
            _raw, fleet, arrays, _fp, _mc, zone_names = _m134.build_year(cfg, year)
            # T-5: the six carry zones only.
            assert len(zone_names) == 6, "T-5: carry-zone count != 6"
            stats = _class_stats(fleet, arrays)
            # V3: the keeper's own fleet, both arms.
            if stats["n_gen"] != V3_NGEN[year]:
                v3_ok = False
            if arm == "on":
                for g in fleet:
                    cls = str(g.plant_group or "")
                    if cls in THERMAL_AVAILABILITY:
                        oy_by_plant_on[int(g.plant_code)] = int(g.online_year)
            arm_stats[arm] = stats
            del fleet, arrays, _raw, _fp, _mc
            gc.collect()

        # V2 fleet half: off arm is byte-inert (every classed row still 2010).
        for cls, s in arm_stats["off"]["classes"].items():
            if s["n_distinct_online_year"] != 1 or s["rows_at_2010"] != s["rows"]:
                v2_ok = False

        # V1: armed per-class cap-weighted online year vs the census truth.
        nameplate_companion = _nameplate_capwt(census, oy_by_plant_on)
        for cls, s in arm_stats["on"]["classes"].items():
            tgt = true_oy.get(cls)
            got = s["capwt_online_year"]
            row = {
                "year": year,
                "class": cls,
                "capwt_online_year_lp": got,
                "census_true": tgt,
                "delta_yr_lp_basis": (got - tgt) if tgt is not None else None,
                "capwt_online_year_nameplate_basis": nameplate_companion.get(cls),
                "delta_yr_nameplate_basis": (
                    nameplate_companion[cls] - tgt
                    if tgt is not None and cls in nameplate_companion
                    else None
                ),
                "pass_lp": (
                    abs(got - tgt) <= V1_TOL_YR if tgt is not None else None
                ),
            }
            v1_rows.append(row)

        # P-1: the capability delta, off − on = capability REMOVED (GW).
        deltas: dict = {}
        tot = {"annual": 0.0, "summer": 0.0, "summer_peak": 0.0}
        tot_nonchp = {"annual": 0.0, "summer": 0.0, "summer_peak": 0.0}
        for cls, s_off in arm_stats["off"]["classes"].items():
            s_on = arm_stats["on"]["classes"][cls]
            d = {
                grain: s_off[f"availcap_{grain}_gw"] - s_on[f"availcap_{grain}_gw"]
                for grain in ("annual", "summer", "summer_peak")
            }
            deltas[cls] = {f"removed_{k}_gw": v for k, v in d.items()}
            for k in tot:
                tot[k] += d[k]
                if not cls.endswith("_CHP"):
                    tot_nonchp[k] += d[k]
        yrec["arms"] = arm_stats
        yrec["capability_removed_gw"] = deltas
        yrec["capability_removed_total_gw"] = tot
        yrec["capability_removed_total_nonchp_gw"] = tot_nonchp
        yrec["p1_summer_nonchp_in_band"] = bool(
            P1_SUMMER_NONCHP_GW[0] <= tot_nonchp["summer"] <= P1_SUMMER_NONCHP_GW[1]
        )
        yrec["p1_annual_nonchp_in_band"] = bool(
            P1_ANNUAL_NONCHP_GW[0] <= tot_nonchp["annual"] <= P1_ANNUAL_NONCHP_GW[1]
        )
        rec["years"][str(year)] = yrec

    rec["gates"]["V1_rows"] = v1_rows
    rec["gates"]["V1_pass_lp_all"] = all(
        r["pass_lp"] for r in v1_rows if r["pass_lp"] is not None
    )
    rec["gates"]["V2_off_arm_all_2010"] = v2_ok
    rec["gates"]["V2_cache_key_distinct"] = key_off != key_on
    rec["gates"]["V3_ngen_pass"] = v3_ok

    OUT.write_text(json.dumps(rec, indent=1, default=float))
    print(json.dumps(rec["gates"], indent=1, default=float)[:4000])
    print(
        json.dumps(
            {
                y: {
                    "removed_nonchp": rec["years"][y][
                        "capability_removed_total_nonchp_gw"
                    ],
                    "p1_summer_in_band": rec["years"][y]["p1_summer_nonchp_in_band"],
                    "p1_annual_in_band": rec["years"][y]["p1_annual_nonchp_in_band"],
                }
                for y in rec["years"]
            },
            indent=1,
            default=float,
        )
    )
    print(f"wrote {OUT.relative_to(REPO)}")
    return rec


if __name__ == "__main__":
    main()
