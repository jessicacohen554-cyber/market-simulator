"""miso-203 — G-E: WHAT ARE THE 15 SCARCE HOURS? (descriptive, post-hoc, no decision rule)

Phase 0's G-C returned a result its own PREREG prediction P1 did not anticipate:
the top-1 %-of-actual-price Jun-Jul hours sit **1.4 to 8.4 degC BELOW** the
summer peak-demand rating condition in all 18 zone-years.  If the scarce hours
are not the hottest hours, the natural next question is whether they are even
the tightest hours — and that is a question about the OBJECT, not about the
refused lever.

This probe is **descriptive and explicitly post-hoc**: it carries no gate, no
decision rule and no PASS/FAIL, and nothing in it licenses or refuses anything.
It exists so the next session's lever choice is made against a measured
characterisation of the 15 hours rather than an assumption about them.

Every input is a committed artifact; **no LP is solved**.  Rule 22
``[R-HOLDOUT]`` — 2023/2024/2025 only.

Usage::

    python3 scripts/probes/_miso203_scarce_hour_identity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia_loader import iso_zone_hourly_drybulb  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER = REPO / "results/calibration/miso202_unitclip_B"
HUB_LMP = REPO / "data/raw/lmp-data/MISO"
OUT = REPO / "results/calibration/_miso203_scarce_hour_identity.json"

RENEW = ("wind", "solar")
MONTH_LENS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _hour_month(hours: int = HOURS) -> np.ndarray:
    """Calendar month per hour on the model's FIXED non-leap 8760 clock."""
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)])[
        :hours
    ]


def _stamp(h: int) -> str:
    """'MM-DD HE' on the model's own 8760 clock (Feb is 28 days in every year)."""
    doy, hod = divmod(int(h), 24)
    m = 0
    while doy >= MONTH_LENS[m]:
        doy -= MONTH_LENS[m]
        m += 1
    return f"{m + 1:02d}-{doy + 1:02d} h{hod:02d}"


def hub_hourly_rt(year: int) -> np.ndarray | None:
    """Hub-average hourly RT LMP — the anatomy's own series, same construction."""
    path = HUB_LMP / f"miso_hub_lmp_{year}_rt.csv.gz"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["value"] == "LMP"]
    he = [f"he{i:02d}" for i in range(1, 25)]
    df["date"] = pd.to_datetime(df["date"])
    arr = df.groupby("date")[he].mean().sort_index().to_numpy().ravel()
    return arr[:HOURS] if len(arr) >= HOURS else None


def _pctile_rank(series: np.ndarray, idx: np.ndarray, within: np.ndarray) -> float:
    """Mean percentile rank of ``idx`` within the ``within`` population."""
    pop = series[within]
    return float(np.mean([(pop < series[i]).mean() for i in idx]) * 100.0)


def main() -> None:
    report: dict = {
        "charter": (
            "miso-203 G-E — descriptive characterisation of the 15 scarce hours. "
            "POST-HOC and NOT PRE-REGISTERED: it carries no gate and licenses "
            "nothing. Written because phase-0's G-C falsified prediction P1 in a "
            "direction that raises a question about the OBJECT."
        ),
        "keeper": "2026-09-03-miso-202-unitclip",
        "basis": "committed artifacts only — no solve",
        "years": {},
    }

    mon = _hour_month()
    jun_jul = np.isin(mon, (6, 7))
    summer = np.isin(mon, (6, 7, 8, 9))
    hod = np.arange(HOURS) % 24
    zones = [z.name for z in get_iso_config(ISO).zones]

    for year in YEARS:
        act = hub_hourly_rt(year)
        if act is None:
            report["years"][str(year)] = {"error": "no committed hub RT file"}
            continue
        jj = np.where(jun_jul)[0]
        thr = float(np.percentile(act[jj], 99.0))
        scarce = jj[act[jj] >= thr]

        sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        load = sysd.groupby("hour")["demand"].sum().sort_index().to_numpy()[:HOURS]
        price_model = (
            sysd.groupby("hour")["price"].mean().sort_index().to_numpy()[:HOURS]
        )

        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        disp = {
            k: g.sort_values("hour")["mw"].to_numpy()[:HOURS]
            for k, g in ch.groupby("klass")
        }
        vre = np.zeros(HOURS)
        for r in RENEW:
            if r in disp:
                vre += np.asarray(disp[r], float)
        netload = load - vre

        temps = {}
        for z in zones:
            t = iso_zone_hourly_drybulb(ISO, year, HOURS, zone=z)
            if t is not None:
                temps[z] = np.asarray(t, float)
        iso_t = (
            np.mean(np.vstack(list(temps.values())), axis=0)
            if temps
            else np.zeros(HOURS)
        )

        # Where do the 15 hours sit in the Jun-Jul distributions of each driver?
        ranks = {
            "load_pctile_in_jun_jul": round(_pctile_rank(load, scarce, jun_jul), 1),
            "netload_pctile_in_jun_jul": round(
                _pctile_rank(netload, scarce, jun_jul), 1
            ),
            "drybulb_pctile_in_jun_jul": round(_pctile_rank(iso_t, scarce, jun_jul), 1),
            "load_pctile_in_summer": round(_pctile_rank(load, scarce, summer), 1),
            "netload_pctile_in_summer": round(_pctile_rank(netload, scarce, summer), 1),
            "drybulb_pctile_in_summer": round(_pctile_rank(iso_t, scarce, summer), 1),
        }

        # How many of the 15 are also in the top 1 % of Jun-Jul load / net load?
        def _topk(series, k):
            return set(jj[np.argsort(series[jj])[-k:]].tolist())

        k = int(scarce.size)
        overlap = {
            "n_scarce": k,
            "n_also_in_top_load_hours": len(set(scarce.tolist()) & _topk(load, k)),
            "n_also_in_top_netload_hours": len(
                set(scarce.tolist()) & _topk(netload, k)
            ),
            "n_also_in_top_drybulb_hours": len(set(scarce.tolist()) & _topk(iso_t, k)),
        }

        rows = []
        for h in sorted(scarce.tolist()):
            rows.append(
                {
                    "hour": int(h),
                    "stamp": _stamp(h),
                    "actual_hub_usd": round(float(act[h]), 2),
                    "model_price_usd": round(float(price_model[h]), 2),
                    "load_mw": round(float(load[h]), 0),
                    "load_pctile_jj": round(
                        float((load[jj] < load[h]).mean() * 100), 1
                    ),
                    "netload_mw": round(float(netload[h]), 0),
                    "netload_pctile_jj": round(
                        float((netload[jj] < netload[h]).mean() * 100), 1
                    ),
                    "iso_drybulb_c": round(float(iso_t[h]), 1),
                    "drybulb_pctile_jj": round(
                        float((iso_t[jj] < iso_t[h]).mean() * 100), 1
                    ),
                }
            )

        # Driver contrast: the 15 scarce hours against the 15 highest GROSS-load
        # Jun-Jul hours, on the same drivers. If the two sets differ in solar and
        # in the 3-hour net-load ramp but not in load, the tail is an evening
        # ramp phenomenon rather than a peak-load one.
        top_load = jj[np.argsort(load[jj])[-k:]]
        ramp3 = np.full(HOURS, np.nan)
        ramp3[3:] = netload[3:] - netload[:-3]

        def _drivers(idx):
            return {
                "load_mw": round(float(load[idx].mean()), 0),
                "wind_mw": round(
                    float(
                        np.asarray(disp.get("wind", np.zeros(HOURS)), float)[idx].mean()
                    ),
                    0,
                ),
                "solar_mw": round(
                    float(
                        np.asarray(disp.get("solar", np.zeros(HOURS)), float)[
                            idx
                        ].mean()
                    ),
                    0,
                ),
                "netload_mw": round(float(netload[idx].mean()), 0),
                "netload_3h_ramp_mw": round(float(np.nanmean(ramp3[idx])), 0),
                "iso_drybulb_c": round(float(iso_t[idx].mean()), 1),
                "hour_of_day_mean": round(float(hod[idx].mean()), 1),
            }

        driver_contrast = {
            "scarce_hours": _drivers(scarce),
            "top_gross_load_hours": _drivers(top_load),
            "all_jun_jul": _drivers(jj),
        }

        report["years"][str(year)] = {
            "driver_contrast": driver_contrast,
            "threshold_usd_per_mwh": round(thr, 2),
            "n_scarce_hours": k,
            "hour_of_day_histogram": {
                str(int(x)): int(c)
                for x, c in zip(*np.unique(hod[scarce], return_counts=True))
            },
            "n_distinct_days": int(len(set((scarce // 24).tolist()))),
            "mean_ranks": ranks,
            "overlap_with_driver_extremes": overlap,
            "jun_jul_peaks_for_reference": {
                "max_load_mw": round(float(load[jj].max()), 0),
                "max_netload_mw": round(float(netload[jj].max()), 0),
                "max_iso_drybulb_c": round(float(iso_t[jj].max()), 1),
            },
            "hours": rows,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT}")
    for y in YEARS:
        d = report["years"].get(str(y))
        if d and "mean_ranks" in d:
            r, o = d["mean_ranks"], d["overlap_with_driver_extremes"]
            print(
                f"{y}: scarce hours sit at load p{r['load_pctile_in_jun_jul']}, "
                f"netload p{r['netload_pctile_in_jun_jul']}, "
                f"drybulb p{r['drybulb_pctile_in_jun_jul']} of Jun-Jul; "
                f"{o['n_also_in_top_netload_hours']}/{o['n_scarce']} are also "
                f"top-{o['n_scarce']} net-load hours"
            )


if __name__ == "__main__":
    main()
