"""PJM-NEXT-17 card 1 (zero LP): where, by plant and hour, does the COAL_BIT over-run sit?

Keeper ``2026-09-30-pjm-next16-ovec`` (bundle ``pjmnext16_A_span``). Reuses the PJM-NEXT-16
partition (``_pjmnext16_cc_loading.py``): per bench COAL_BIT plant-hour, model - CAMPD
(rescaled to EIA-923 net) is split exactly into
  LOAD (both on: mod - act), ON (model on, actual off: mod), OFF (actual on only: -act).

Adds, per plant and year:
- on-hours (model / actual), mean loading-when-on as a fraction of nameplate, and the share
  of on-hours at >= 0.9 x nameplate ("full");
- the LOAD term split night / day and by actual-demand tercile;
- the night coal/CC ordering: per hour, the bench COAL_BIT gap vs the bench CC_REGULAR gap
  (same partition), and the class-band composition of model COAL_BIT energy (mustrun /
  committed / sync / econ / peak) from ``hourly/class_band_hourly_<y>.parquet``.

Writes ``results/phase0/pjm/_pjmnext17_coal_census.json``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pjmnext16_cc_loading import _dec, _e930, _lag, _payload  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend/data/backcast/bench/PJM"
RUN = REPO / "frontend/data/backcast/runs/2026-09-30-pjm-next16-ovec.js"
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
OUT = REPO / "results/phase0/pjm/_pjmnext17_coal_census.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
ON_FRAC = 0.05  # same on/off threshold as the NEXT-16 CC census
FULL_FRAC = 0.9
T = 8760


def _partition(klass: str, y: int, plants: dict, bench: dict) -> tuple[dict, dict]:
    """Return the class-wide hourly partition and the per-plant records."""
    part = {k: np.zeros(T) for k in ("LOAD", "ON", "OFF", "MOD", "ACT")}
    per: dict[str, dict] = {}
    for pid, bp in bench["plants"].items():
        if bp.get("group") != klass or bp.get("nodata") or not bp.get("campd"):
            continue
        npl = float(bp.get("npl") or 0.0)
        kp = plants.get(pid, {})
        if npl <= 0 or not kp.get("m"):
            continue
        act = _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))
        mod = _dec(kp["m"], kp.get("m_ann"))
        on_m, on_a = mod > ON_FRAC * npl, act > ON_FRAC * npl
        p = {
            "LOAD": np.where(on_m & on_a, mod - act, 0.0),
            "ON": np.where(on_m & ~on_a, mod, 0.0),
            "OFF": np.where(~on_m & on_a, -act, 0.0),
            "MOD": mod,
            "ACT": act,
        }
        for k in part:
            part[k] += p[k]
        per[pid] = {
            "name": bp.get("name"),
            "zone": bp.get("zone", "").replace("PJM_", ""),
            "npl": npl,
            "p": p,
            "on_m": on_m,
            "on_a": on_a,
            "mod": mod,
            "act": act,
        }
    return part, per


def main() -> None:
    """Census every year and write the JSON artifact."""
    pay = {int(y): rec["plants"] for y, rec in _payload(RUN)["years"].items()}
    res: dict = {"what": "PJM-NEXT-17 card 1 - COAL_BIT census. ZERO LP.", "years": {}}
    plant_tot: dict[str, dict] = {}
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        coal, per = _partition("COAL_BIT", y, pay[y], bench)
        cc, _ = _partition("CC_REGULAR", y, pay[y], bench)

        sysd = pd.read_parquet(HOURLY / f"system_{y}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        dm = sysd.groupby("hour").demand.sum().reindex(range(T)).values
        a = _e930(y)
        lag = _lag(dm, a.demand.values)
        a = a.apply(lambda s: np.roll(s.values, lag))
        he = a.he.values.astype(int)
        night = ~((he >= 8) & (he <= 23))
        terc = np.clip(
            np.searchsorted(
                np.quantile(a.demand.values, [1 / 3, 2 / 3]), a.demand.values
            ),
            0,
            2,
        )

        band = pd.read_parquet(HOURLY / f"class_band_hourly_{y}.parquet")
        band = band[(band["pass"] == "P1") & (band.klass == "COAL_BIT")]
        band["grp"] = band.band.astype(str).str.replace(r"econ.*", "econ", regex=True)
        bp = (
            band.pivot_table(index="hour", columns="grp", values="mw", aggfunc="sum")
            .reindex(range(T))
            .fillna(0.0)
        )

        def twh(v: np.ndarray, m: np.ndarray | None = None) -> float:
            return round(float((v if m is None else v[m]).sum()) / 1e6, 2)

        d_coal = coal["MOD"] - coal["ACT"]
        d_cc = cc["MOD"] - cc["ACT"]
        rec = {
            "lag_h": lag,
            "coal": {k: twh(v) for k, v in coal.items()},
            "coal_night": {k: twh(v, night) for k, v in coal.items()},
            "coal_day": {k: twh(v, ~night) for k, v in coal.items()},
            "coal_LOAD_by_demand_tercile": [
                twh(coal["LOAD"], terc == i) for i in range(3)
            ],
            "cc": {k: twh(v) for k, v in cc.items()},
            "cc_night": {k: twh(v, night) for k, v in cc.items()},
            # Ordering: hours where coal over-runs AND CC under-runs (a swap) vs both over.
            "night_hours_coal_over_cc_under": int(
                ((d_coal > 0) & (d_cc < 0) & night).sum()
            ),
            "night_hours_coal_over_cc_over": int(
                ((d_coal > 0) & (d_cc > 0) & night).sum()
            ),
            "hourly_corr_dcoal_dcc": round(float(np.corrcoef(d_coal, d_cc)[0, 1]), 3),
            "bands_twh": {c: twh(bp[c].values) for c in bp.columns},
            "bands_night_twh": {c: twh(bp[c].values, night) for c in bp.columns},
        }
        plants = []
        for pid, r in per.items():
            npl = r["npl"]
            lw_m = r["mod"][r["on_m"]].mean() / npl if r["on_m"].any() else 0.0
            lw_a = r["act"][r["on_a"]].mean() / npl if r["on_a"].any() else 0.0
            full_m = (
                (r["mod"][r["on_m"]] >= FULL_FRAC * npl).mean()
                if r["on_m"].any()
                else 0.0
            )
            full_a = (
                (r["act"][r["on_a"]] >= FULL_FRAC * npl).mean()
                if r["on_a"].any()
                else 0.0
            )
            row = {
                "pid": pid,
                "name": r["name"],
                "zone": r["zone"],
                "npl": npl,
                "gap": twh(r["mod"] - r["act"]),
                "LOAD": twh(r["p"]["LOAD"]),
                "LOAD_night": twh(r["p"]["LOAD"], night),
                "ON": twh(r["p"]["ON"]),
                "OFF": twh(r["p"]["OFF"]),
                "onh_m": int(r["on_m"].sum()),
                "onh_a": int(r["on_a"].sum()),
                "lw_m": round(float(lw_m), 3),
                "lw_a": round(float(lw_a), 3),
                "full_m": round(float(full_m), 3),
                "full_a": round(float(full_a), 3),
            }
            plants.append(row)
            t = plant_tot.setdefault(
                pid, {"name": r["name"], "zone": r["zone"], "gap": {}}
            )
            t["gap"][y] = row["gap"]
        plants.sort(key=lambda r: -r["gap"])
        rec["plants"] = plants
        # Fleet loading-when-on, nameplate-weighted, model vs actual.
        on_npl_m = sum(r["npl"] * r["onh_m"] for r in plants)
        on_npl_a = sum(r["npl"] * r["onh_a"] for r in plants)
        rec["fleet_lw_m"] = round(
            sum(r["lw_m"] * r["npl"] * r["onh_m"] for r in plants) / on_npl_m, 3
        )
        rec["fleet_lw_a"] = round(
            sum(r["lw_a"] * r["npl"] * r["onh_a"] for r in plants) / on_npl_a, 3
        )
        rec["fleet_full_m"] = round(
            sum(r["full_m"] * r["npl"] * r["onh_m"] for r in plants) / on_npl_m, 3
        )
        rec["fleet_full_a"] = round(
            sum(r["full_a"] * r["npl"] * r["onh_a"] for r in plants) / on_npl_a, 3
        )
        res["years"][str(y)] = rec
        c = rec["coal"]
        print(
            y,
            f"gap {c['MOD'] - c['ACT']:+.1f} LOAD {c['LOAD']:+.1f} (night {rec['coal_night']['LOAD']:+.1f})",
            f"ON {c['ON']:+.1f} OFF {c['OFF']:+.1f}",
            f"| lw {rec['fleet_lw_m']}/{rec['fleet_lw_a']} full {rec['fleet_full_m']}/{rec['fleet_full_a']}",
            f"| terc {rec['coal_LOAD_by_demand_tercile']}",
            f"| corr dcoal-dcc {rec['hourly_corr_dcoal_dcc']}",
            flush=True,
        )
    res["plant_totals"] = plant_tot
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
