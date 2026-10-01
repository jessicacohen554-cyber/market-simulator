"""NYISO-NEXT-5 phase 0 (ZERO LP): the Long Island external-tie gap, per line.

Measures, hourly per year, the keeper's ``NYISO_external>Long_Island`` import
capability against NYISO's own per-line P-32 schedules (Neptune HVDC, Cross-Sound
Cable, Northport-Norwalk 1385) and how the difference co-occurs with the keeper's
Long Island price miss.

Inputs (all read-only):
* ``data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_<y>.csv.gz`` — the
  already-committed MIS P-32 hourly aggregation (Ask D1). Per line: the mean
  scheduled flow and the hour's posted positive (import) limit.
* the keeper's committed ``hourly/system_<y>.parquet`` (Long_Island price).
* NYISO 5-min zonal RT (LONGIL): 2022 zips in repo, other years via ``NYRT_DIR``.

The committed sidecars carry no per-link flow, so the model's LI import is NOT
observed here. What is observed exactly is its CAP: the keeper arms
``nyiso_seam_deliverability_envelope``, whose LI import cap is rebuilt below with
the production function :func:`seam_envelope_by_zone` at the production
percentile. nyiso-225 §4 measured that link AT its bound in 99.6 % of 2022 hours,
so cap - measured is the model's over-import to within that bound share.

Definitions fixed before any number was read:
* gap_h = cap_h - measured LI net_h (MW); positive = model can import more than
  the market scheduled.
* line outage hour: that line's posted positive limit is 0.
* LI miss_h = model LI price_h - actual LONGIL RT_h ($/MWh).
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE
from market_sim.data.nyiso_seam_envelope import (
    NYISO_SEAM_TIE_LANDING,
    seam_envelope_by_zone,
)

REPO = Path(__file__).resolve().parents[2]
FLOWS = REPO / "data/raw/NYISO/interface-flows"
BUNDLES = {
    2021: REPO / "results/calibration/nyisonext3_2021/hourly",
    **{
        y: REPO / "results/calibration/nyisonext3_span/hourly"
        for y in (2022, 2023, 2024, 2025)
    },
}
LMPDIR = REPO / "data/raw/lmp-data/NYISO"
EXTRA = Path(os.environ.get("NYRT_DIR", "/nonexistent"))
OUT = REPO / "results/phase0/nyiso/_nyisonext5_li_tie_gap.json"
TIES = NYISO_SEAM_TIE_LANDING["Long_Island"]
SHORT = {
    "SCH - PJM_NEPTUNE": "neptune",
    "SCH - NPX_CSC": "csc",
    "SCH - NPX_1385": "l1385",
}
H = 8760


def _flows(y: int) -> pd.DataFrame:
    f = pd.read_csv(FLOWS / f"NYISO_interface_flows_hourly_{y}.csv.gz")
    f["interval_start_local"] = pd.to_datetime(f["interval_start_local"])
    return f


def _hourly_lines(f: pd.DataFrame, y: int) -> pd.DataFrame:
    """Per-line flow and posted import limit on the bench's hour index."""
    s = f[f.interface.isin(TIES)].copy()
    s["hour"] = (
        (s.interval_start_local - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h")
    ).astype(int)
    s = s[(s.hour >= 0) & (s.hour < H)]
    # DST fall-back gives one duplicated local hour; average it.
    fl = s.pivot_table(
        index="hour", columns="interface", values="flow_mw", aggfunc="mean"
    )
    lim = s.pivot_table(
        index="hour", columns="interface", values="positive_limit_mw", aggfunc="min"
    )
    out = pd.DataFrame(index=pd.RangeIndex(H, name="hour"))
    for t in TIES:
        out[SHORT[t]] = fl[t]
        out[SHORT[t] + "_lim"] = lim[t]
    out = out.ffill().bfill()  # the spring-forward missing local hour only
    out["net"] = out[[SHORT[t] for t in TIES]].sum(axis=1)
    return out


def _li_price(y: int) -> pd.DataFrame:
    s = pd.read_parquet(BUNDLES[y] / f"system_{y}.parquet")
    s = s[(s["pass"] == "P1") & (s.zone == "Long_Island")].set_index("hour")
    rows = []
    for zf in sorted(
        list(LMPDIR.glob(f"{y}*realtime_zone_csv.zip"))
        + list(EXTRA.glob(f"{y}*realtime_zone_csv.zip"))
    ):
        with zipfile.ZipFile(zf) as z:
            for n in z.namelist():
                r = pd.read_csv(io.BytesIO(z.read(n)))
                rows.append(r[r.Name == "LONGIL"])
    r = pd.concat(rows)
    r["ts"] = pd.to_datetime(r["Time Stamp"]).dt.floor("h")
    a = r.groupby("ts")["LBMP ($/MWHr)"].mean()
    a.index = ((a.index - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h")).astype(int)
    d = pd.DataFrame({"model": s.price, "D": s.demand}).join(
        a.rename("act"), how="inner"
    )
    return d


def _year(y: int) -> dict:
    f = _flows(y)
    cap = seam_envelope_by_zone(f, H, NYISO_SEAM_FLOW_PERCENTILE)["Long_Island"][0]
    L = _hourly_lines(f, y)
    L["cap"] = cap
    L["gap"] = L.cap - L.net
    d = _li_price(y).join(L, how="inner")
    d["miss"] = d.model - d.act
    W = d.D.sum()

    def lw(x, m=None) -> float:
        """Load-weighted mean of ``x`` over mask ``m`` (all hours if None)."""
        if m is None:
            return float(np.average(x, weights=d.D))
        return float(np.average(x[m], weights=d.D[m]))

    res = {
        "hours_matched": int(len(d)),
        "measured_mw": {
            k: round(float(L[k].mean()), 1) for k in ("neptune", "csc", "l1385", "net")
        },
        "cap_mw_mean": round(float(L.cap.mean()), 1),
        "gap_mw": {
            "mean": round(float(L.gap.mean()), 1),
            "p10": round(float(L.gap.quantile(0.1)), 1),
            "p50": round(float(L.gap.quantile(0.5)), 1),
            "p90": round(float(L.gap.quantile(0.9)), 1),
            "gap_twh": round(float(L.gap.sum()) / 1e6, 3),
        },
        "li_miss_usd": round(lw(d.miss), 2),
        "li_model_mean": round(lw(d.model), 2),
        "li_act_mean": round(lw(d.act), 2),
        "corr_gap_miss": round(float(np.corrcoef(d.gap, d.miss)[0, 1]), 3),
        "corr_gap_miss_ex_tail": round(
            float(np.corrcoef(d.gap[d.act <= 300], d.miss[d.act <= 300])[0, 1]), 3
        ),
    }
    # per-line outage windows (posted import limit == 0) and the gap inside them
    out = {}
    for k in ("neptune", "csc", "l1385"):
        m = L[k + "_lim"] <= 0
        dm = d[k + "_lim"] <= 0
        out[k] = {
            "outage_hours": int(m.sum()),
            "gap_mw_in_outage": round(float(L.gap[m].mean()), 1) if m.any() else None,
            "gap_twh_in_outage": round(float(L.gap[m].sum()) / 1e6, 3),
            "li_miss_contrib_usd": round(float((d.D[dm] * d.miss[dm]).sum() / W), 2),
        }
    res["line_outage"] = out
    anyo = (L[["neptune_lim", "csc_lim", "l1385_lim"]] <= 0).any(axis=1)
    res["gap_twh_all_lines_up"] = round(float(L.gap[~anyo].sum()) / 1e6, 3)
    # per-line under-scheduling relative to posted limit when UP (economic, not physical)
    res["unused_posted_mw_when_up"] = {
        k: round(float((L[k + "_lim"] - L[k])[L[k + "_lim"] > 0].mean()), 1)
        for k in ("neptune", "csc", "l1385")
    }
    # CANDIDATE LEVER (physical availability): cap the envelope at the sum of the
    # three lines' POSTED import limits in the hour (a line on outage posts 0).
    lim = L[["neptune_lim", "csc_lim", "l1385_lim"]].sum(axis=1)
    red = np.clip(L.cap - lim, 0.0, None)
    dr = red.reindex(d.index) > 0
    res["posted_limit_cap"] = {
        "hours_cut": int((red > 0).sum()),
        "cut_twh": round(float(red.sum()) / 1e6, 3),
        "cut_share_of_gap": round(float(red.sum() / L.gap.sum()), 3),
        "mean_cut_mw_in_cut_hours": round(float(red[red > 0].mean()), 1)
        if (red > 0).any()
        else 0.0,
        "li_miss_in_cut_hours_usd": round(lw(d.miss, dr), 2) if dr.any() else None,
        "li_miss_contrib_cut_hours_usd": round(
            float((d.D[dr] * d.miss[dr]).sum() / W), 2
        ),
    }
    # miss by gap quartile
    q = pd.qcut(d.gap, 4, labels=["q1", "q2", "q3", "q4"], duplicates="drop")
    res["li_miss_by_gap_quartile"] = {
        str(k): {
            "gap_mw": round(float(d.gap[q == k].mean()), 0),
            "miss_usd": round(lw(d.miss, q == k), 2),
            "contrib_usd": round(float((d.D[q == k] * d.miss[q == k]).sum() / W), 2),
        }
        for k in q.cat.categories
    }
    # tail split of the LI miss
    t = d.act > 300
    res["li_miss_contrib_tail_usd"] = round(float((d.D[t] * d.miss[t]).sum() / W), 2)
    res["li_miss_contrib_nontail_usd"] = round(
        float((d.D[~t] * d.miss[~t]).sum() / W), 2
    )
    return res


def main() -> None:
    """Run the per-year measurement and write the JSON record."""
    res = {y: _year(y) for y in BUNDLES}
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
