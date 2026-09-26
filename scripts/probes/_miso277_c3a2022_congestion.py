#!/usr/bin/env python3
"""miso-277 phase 0 (zero LP): localize MISO's missing 2022 West->East congestion.

Follows ``_miso276_c3a2022_phase0.py``. Reads only committed artifacts:

* the keeper's P1 hourly sidecars
  (``results/calibration/miso275_span/hourly/system_<Y>.parquet`` — per-zone
  price and demand; the bundle carries NO flow / link sidecar, and no per-zone
  generation, so link flows are NOT observable and are inferred only from the
  price duals: in this LP two zones separate only when a link / interface
  group between them binds);
* the committed zonal RT actuals
  (``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet``;
  Plains is the MINN+ILLINOIS hub-mean PROXY there, so it is not an
  independent observation);
* the verbatim MISO hub RT LMP / MCC / MLC rows
  (``data/raw/lmp-data/MISO``; MCC/MLC exist for 2022-2025 only — the
  2019-2021 monthly family publishes LMP only);
* the 2022 CIL/CEL interface groups as the backcast wires them
  (``market_sim.model.interchange.miso.build_miso_deliverability_groups``,
  called read-only — the same call ``scripts/run_calibration.py`` makes).

Rule 13 [R-MEASURED]: MCC / binding records are ANSWER-class. They are used
here for LOCALIZATION only, never as an LP input.

All price statistics are masked to Jan-Oct (hours 0..7295 of the non-leap
clock) in every year, the window the scorer uses for 2022 (RT coverage of
Nov/Dec 2022 is partial), so years are comparable.

Usage::

    uv run python scripts/probes/_miso277_c3a2022_congestion.py \
        --out results/calibration/_miso277_c3a2022_congestion.json
"""

from __future__ import annotations

import argparse
import gzip
import io
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/miso275_span"
ACTUALS = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
HUB_DIR = REPO / "data/raw/lmp-data/MISO"
PLAINS_PROXY = ("MINN.HUB", "ILLINOIS.HUB")
ZONES = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
)
SHORT = {z: z.split("-")[1] for z in ZONES}
#: Model links L1-L6 (iso_configs._miso_config) plus the RDT corridor.
MODEL_LINKS = (
    ("MISO-West", "MISO-Plains"),
    ("MISO-West", "MISO-East"),
    ("MISO-Plains", "MISO-Illinois"),
    ("MISO-Illinois", "MISO-Indiana"),
    ("MISO-Illinois", "MISO-East"),
    ("MISO-Indiana", "MISO-East"),
    ("MISO-Plains", "MISO-South"),
)
#: Hub -> zone for the MCC decomposition (Plains has no hub).
HUB_ZONE = {
    "MINN.HUB": "MISO-West",
    "ILLINOIS.HUB": "MISO-Illinois",
    "INDIANA.HUB": "MISO-Indiana",
    "MICHIGAN.HUB": "MISO-East",
    "ARKANSAS.HUB": "MISO-South",
}
#: Jan-Oct on the fixed non-leap clock (304 days).
JAN_OCT_HOURS = 304 * 24
#: Hub-file HE index -> actuals-parquet hour key offset (measured, see hub_components).
HUB_TO_ACTUALS_SHIFT = 1
#: Separation threshold in $/MWh for "model zones are split" (dual resolution).
SEP_EPS = 0.01
#: Actual West-Indiana |spread| threshold the lane asks about, $/MWh.
BIG_SPREAD = 10.0
YEARS = tuple(range(2019, 2026))


def actual_rt(year: int) -> np.ndarray:
    """(zone, 8760) zonal RT hub-mean LMP on :data:`ZONES` order (Plains = proxy)."""
    df = pd.read_parquet(ACTUALS)
    df = df[df["year"] == year]
    pv = df.groupby(["hour", "zone"])["rt"].mean().unstack()
    pv["MISO-Plains"] = df[df["hub"].isin(PLAINS_PROXY)].groupby("hour")["rt"].mean()
    pv = pv.reindex(range(8760))
    return pv[list(ZONES)].to_numpy(float).T


def model(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(zone, 8760) keeper P1 price and demand."""
    s = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot(index="hour", columns="zone", values="price").reindex(range(8760))
    d = s.pivot(index="hour", columns="zone", values="demand").reindex(range(8760))
    return p[list(ZONES)].to_numpy(float).T, d[list(ZONES)].to_numpy(float).T


def hub_components(year: int) -> dict[str, dict[str, np.ndarray]] | None:
    """Hub RT {type: {hub: (8760,) array}} for LMP/MCC/MLC, or None if no MCC rows.

    Hour index = (day-of-year on the non-leap clock) * 24 + (HE - 1); Feb 29 dropped.
    """
    gz = HUB_DIR / f"miso_hub_lmp_{year}_rt.csv.gz"
    if gz.exists():
        df = pd.read_csv(gz)
    else:
        parts = sorted(HUB_DIR.glob(f"miso_hub_lmp_{year}_rt_p*.csv"))
        if not parts:
            return None
        df = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    if "MCC" not in set(df["value"]):
        return None
    d = pd.to_datetime(df["date"])
    keep = ~((d.dt.month == 2) & (d.dt.day == 29))
    df, d = df[keep], d[keep]
    doy = (d - pd.Timestamp(f"{year}-01-01")).dt.days.to_numpy()
    doy = np.where(d.dt.is_leap_year & (d.dt.month > 2), doy - 1, doy)
    he = [f"he{h:02d}" for h in range(1, 25)]
    out: dict[str, dict[str, np.ndarray]] = {}
    for typ in ("LMP", "MCC", "MLC"):
        out[typ] = {}
        for hub in HUB_ZONE:
            m = ((df["value"] == typ) & (df["node"] == hub)).to_numpy()
            arr = np.full(8760, np.nan)
            vals = df.loc[m, he].to_numpy(float)
            idx = (doy[m][:, None] * 24 + np.arange(24)[None, :]).ravel()
            ok = idx < 8760
            arr[idx[ok]] = vals.ravel()[ok]
            # Align to the committed actuals parquet's hour key (the scorer's):
            # measured lag -1 gives r = 1.000 vs 0.59/0.34 unshifted (2022/2023).
            out[typ][hub] = np.roll(arr, -HUB_TO_ACTUALS_SHIFT)
    return out


def r2(x: float) -> float:
    """Round to 2 dp, NaN-safe for JSON."""
    return None if not np.isfinite(x) else round(float(x), 2)


def pair_stats(act: np.ndarray, mod: np.ndarray, mask: np.ndarray) -> dict:
    """Mean signed / absolute spread, actual vs model, for every zone pair."""
    out = {}
    for i, j in itertools.combinations(range(len(ZONES)), 2):
        a = act[i, mask] - act[j, mask]
        m = mod[i, mask] - mod[j, mask]
        out[f"{SHORT[ZONES[i]]}-{SHORT[ZONES[j]]}"] = {
            "actual_mean": r2(a.mean()),
            "model_mean": r2(m.mean()),
            "actual_mean_abs": r2(np.abs(a).mean()),
            "model_mean_abs": r2(np.abs(m).mean()),
            "model_share_separated": round(float((np.abs(m) > SEP_EPS).mean()), 4),
            "actual_share_abs_gt_10": round(float((np.abs(a) > BIG_SPREAD).mean()), 4),
        }
    return out


def probe_year(year: int) -> dict:
    """All price-side measurements for one year, Jan-Oct masked."""
    act = actual_rt(year)
    mod, dem = model(year)
    t = np.arange(8760)
    mask = (
        (t < JAN_OCT_HOURS)
        & np.isfinite(act).all(axis=0)
        & np.isfinite(mod).all(axis=0)
    )
    ts = pd.Timestamp("2021-01-01") + pd.to_timedelta(t, "h")  # non-leap clock
    month, hod = ts.month.to_numpy(), ts.hour.to_numpy()
    iw, ii = ZONES.index("MISO-West"), ZONES.index("MISO-Indiana")
    a_wi = act[ii] - act[iw]  # Indiana minus West (positive = West->East congestion)
    m_wi = mod[ii] - mod[iw]
    res = {
        "hours_scored": int(mask.sum()),
        "zone_mean_actual": {
            SHORT[z]: r2(act[k, mask].mean()) for k, z in enumerate(ZONES)
        },
        "zone_mean_model": {
            SHORT[z]: r2(mod[k, mask].mean()) for k, z in enumerate(ZONES)
        },
        "pairs": pair_stats(act, mod, mask),
        "link_spread_abs_actual": {
            f"{SHORT[a]}-{SHORT[b]}": r2(
                np.abs(act[ZONES.index(a), mask] - act[ZONES.index(b), mask]).mean()
            )
            for a, b in MODEL_LINKS
        },
        "indiana_minus_west": {
            "actual_mean": r2(a_wi[mask].mean()),
            "model_mean": r2(m_wi[mask].mean()),
            "actual_share_abs_gt_10": round(
                float((np.abs(a_wi[mask]) > BIG_SPREAD).mean()), 4
            ),
            "actual_share_gt_10_west_low": round(
                float((a_wi[mask] > BIG_SPREAD).mean()), 4
            ),
            "model_share_west_below_indiana": round(
                float((m_wi[mask] > SEP_EPS).mean()), 4
            ),
            "model_share_west_above_indiana": round(
                float((m_wi[mask] < -SEP_EPS).mean()), 4
            ),
            "by_month": {
                int(mo): {
                    "actual": r2(a_wi[mask & (month == mo)].mean()),
                    "model": r2(m_wi[mask & (month == mo)].mean()),
                }
                for mo in range(1, 11)
            },
            "by_hod": {
                int(h): {
                    "actual": r2(a_wi[mask & (hod == h)].mean()),
                    "model": r2(m_wi[mask & (hod == h)].mean()),
                }
                for h in range(24)
            },
        },
        "model_midwest_separated_share": round(
            float(
                (
                    np.nanmax(mod[:5, mask], axis=0) - np.nanmin(mod[:5, mask], axis=0)
                    > SEP_EPS
                ).mean()
            ),
            4,
        ),
    }
    comp = hub_components(year)
    if comp is not None:
        cm = (
            mask
            & np.isfinite(comp["MCC"]["INDIANA.HUB"])
            & np.isfinite(comp["MCC"]["MINN.HUB"])
        )
        lmp_d = comp["LMP"]["INDIANA.HUB"] - comp["LMP"]["MINN.HUB"]
        mcc_d = comp["MCC"]["INDIANA.HUB"] - comp["MCC"]["MINN.HUB"]
        mlc_d = comp["MLC"]["INDIANA.HUB"] - comp["MLC"]["MINN.HUB"]
        # alignment check vs the committed actuals parquet
        corr = np.corrcoef(comp["LMP"]["INDIANA.HUB"][cm], act[ii, cm])[0, 1]
        res["mcc_decomposition_indiana_minus_minn"] = {
            "hours": int(cm.sum()),
            "hub_vs_actuals_corr": round(float(corr), 4),
            "lmp_spread": r2(lmp_d[cm].mean()),
            "mcc_spread": r2(mcc_d[cm].mean()),
            "mlc_spread": r2(mlc_d[cm].mean()),
            "mcc_by_hub_mean": {h: r2(comp["MCC"][h][cm].mean()) for h in HUB_ZONE},
            "mlc_by_hub_mean": {h: r2(comp["MLC"][h][cm].mean()) for h in HUB_ZONE},
            "mcc_spread_by_month": {
                int(mo): r2(mcc_d[cm & (month == mo)].mean()) for mo in range(1, 11)
            },
        }
    return res


CAPDEL_CSV = REPO / "data/raw/capacity-deliverability/miso/miso.csv"
#: Model zone -> member LRZs (config.capacity_area_crosswalk._MISO_LRZ_TO_ZONE, Midwest only).
ZONE_LRZ = {
    "MISO-West": ("LRZ 1",),
    "MISO-Plains": ("LRZ 3", "LRZ 5"),
    "MISO-Illinois": ("LRZ 4",),
    "MISO-Indiana": ("LRZ 6",),
    "MISO-East": ("LRZ 2", "LRZ 7"),
}


def cil_cel_from_csv(delivery_year: str = "2022/2023") -> dict:
    """Per-zone CIL/CEL straight from the raw LOLE CSV, the builder's member-sum rule.

    2022 backcast months all resolve to PY2022/2023 ``annual``: Jan-May's
    PY2021/22 is absent from the extraction, so the builder backfills from the
    earliest available PY. A blank CEL ("No Limit Found") -> unconstrained.
    """
    df = pd.read_csv(CAPDEL_CSV)
    df = df[(df["delivery_year"] == delivery_year) & (df["area_type"] == "lrz")]
    out = {}
    for zone, lrzs in ZONE_LRZ.items():
        sub = df[df["area"].isin(lrzs)]
        imp = sub[sub["metric"] == "import_limit"]["value_mw"]
        exp = sub[sub["metric"] == "export_limit"]["value_mw"]
        out[zone] = {
            "cil_mw": float(imp.sum()) if imp.notna().sum() == len(lrzs) else None,
            "cel_mw": float(exp.sum()) if exp.notna().sum() == len(lrzs) else None,
            "source": sorted(set(sub["source_doc"])),
        }
    return out


def cil_cel_2022() -> dict:
    """2022 per-zone CIL/CEL groups as the backcast wires them (read-only builder call).

    Falls back to :func:`cil_cel_from_csv` when the curated clean partition is
    absent in this checkout (the builder then returns no groups).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.interchange.miso import build_miso_deliverability_groups

    cfg = get_iso_config("MISO")
    groups = build_miso_deliverability_groups(cfg.links, 2022, 8760)
    out = {
        "internal_link_ttc_mw": {
            f"{l.from_zone}->{l.to_zone}": l.ttc_mw for l in cfg.links
        },
        "static_fallback_py2025_26_summer": {
            lim.name: {"cap_mw": lim.cap_mw, "reverse_cap_mw": lim.reverse_cap_mw}
            for lim in cfg.interface_limits
        },
        "from_raw_csv_py2022_23_annual": cil_cel_from_csv(),
        "groups": [],
    }
    for idx, cil, _bi, cel, signs in groups:
        into = [cfg.links[k] for k in idx]
        # the zone every member link touches with sign +1 as to_zone
        zone = into[0].to_zone if signs[0] > 0 else into[0].from_zone
        out["groups"].append(
            {
                "zone": zone,
                "members": [f"{l.from_zone}->{l.to_zone}" for l in into],
                "cil_mw_distinct": sorted({float(x) for x in np.unique(cil)}),
                "cel_mw_distinct": sorted({float(x) for x in np.unique(cel)}),
            }
        )
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res: dict = {"years": {str(y): probe_year(y) for y in args.years}}
    try:
        res["cil_cel_2022"] = cil_cel_2022()
    except Exception as exc:  # report, never fail the probe on the config read
        res["cil_cel_2022"] = {"error": repr(exc)}
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    for y, r in res["years"].items():
        iw = r["indiana_minus_west"]
        print(y, "act", r["zone_mean_actual"], "\n     mod", r["zone_mean_model"])
        print(
            "   IN-W act/mod",
            iw["actual_mean"],
            iw["model_mean"],
            "|>10|",
            iw["actual_share_abs_gt_10"],
            "model sep W<IN",
            iw["model_share_west_below_indiana"],
            "W>IN",
            iw["model_share_west_above_indiana"],
            "midwest sep",
            r["model_midwest_separated_share"],
        )
        print("   link |d| act", r["link_spread_abs_actual"])
        if "mcc_decomposition_indiana_minus_minn" in r:
            print("   MCC", r["mcc_decomposition_indiana_minus_minn"])
    print(json.dumps(res["cil_cel_2022"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
