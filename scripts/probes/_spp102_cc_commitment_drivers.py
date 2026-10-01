"""SPP-102 phase 0 (zero LP): what keys SPP CC units ONLINE in low-LMP hours?

Charter: SPP-102 (owner card "Charter commitment lane", 2026-09-29). Object: in 2021/22 actual CC ran
7.3 / 4.8 TWh in hours with actual RT LMP <= $15, the keeper 2.2 / 0.6 TWh
(`results/phase0/spp/_spp89_coal_cc_swap.json`).

Per SPP CC_REGULAR plant with a CEMS series (bench `campd`, uint8 % of nameplate, model clock) the
ONLINE state is CF >= 5 % (the SPP-97 convention). The keeper's state is its payload CF >= 1 %.
Low-price hours L are actual SPP RT system LMP <= $15 (`actual_lmp_hourly_SPP.parquet`).

Candidate drivers, each scored as the AUC of a plant-hour online classifier INSIDE L (threshold-free,
so no parameter is fitted to score it), per year:
  * nl_now       net load now (EIA-930 SWPP demand - wind - solar)
  * nl_fwd24     max net load over the next 24 h (a "committed for tomorrow's peak" story)
  * nl_gasday    max net load over the gas day containing t (09:00-09:00 CPT, NAESB)
  * load_fwd24   max gross demand over the next 24 h (no VRE)
  * month_cold   heating-season flag (Nov-Mar)
  * da_low       day-ahead LMP <= $15 in the same hour (a MARKET OUTCOME; diagnostic only, rule 13)
  * conduct_lyo  the plant's leave-year-out pooled on-frequency (a unit-conduct attribute,
                 SPP-100 `chp_steam_floor_conduct_scope` precedent; never the target year's data)
Plus, per year: the run-length structure of actual CC online spells that cover L hours (how many
L-hours sit inside spells > 48 h — the "kept on through the trough" signature of commitment cost /
min-down physics), and a fleet-level decomposition of the L-hour online MWh by plant conduct class.

Writes docs/records/spp/spp102/cc_commitment_drivers.json. Usage:
  uv run python scripts/probes/_spp102_cc_commitment_drivers.py <decoded payload.json>
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

YEARS = [str(y) for y in range(2019, 2026)]
ON_CEMS = 5  # % of nameplate, SPP-97 FINDING §4 convention
ON_MODEL = 1  # %, SPP-97 convention
LOW = 15.0  # $/MWh, the SPP-89 bucket edge the charter quotes
MIN_LOAD = 0.209  # SPP CC plant-basis min-load, FINDING-spp-44-2026-09-07.md §1
CST_OFFSET_H = 6  # model clock = fixed CST (UTC-6), frames.py
LONG_SPELL_H = 48


def dec(s: str) -> np.ndarray:
    """Decode a payload/bench base64 uint8 CF % series."""
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8).astype(float)


def auc(score: np.ndarray, y: np.ndarray) -> float | None:
    """Mann-Whitney AUC of `score` for binary `y` (ties averaged); None if one class is empty."""
    y = y.astype(bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return None
    r = pd.Series(score).rank(method="average").to_numpy()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def eia930(y: int) -> dict[str, np.ndarray]:
    """EIA-930 SWPP demand / wind / solar on the model clock (hour-ending period shifted to hour-beginning)."""
    start = pd.Timestamp(f"{y}-01-01 {CST_OFFSET_H:02d}:00", tz="UTC")
    idx = pd.date_range(start, periods=8760, freq="h")
    reg = pd.read_parquet(RAW_DATA_DIR / "SWPP_region.parquet")
    fu = pd.read_parquet(RAW_DATA_DIR / "SWPP_fueltype.parquet")

    def ser(df: pd.DataFrame) -> np.ndarray:
        s = df.set_index(df["period"] - pd.Timedelta(hours=1))["value_mwh"]
        s = s[~s.index.duplicated()]
        return s.reindex(idx).interpolate(limit=6).fillna(0.0).to_numpy(float)

    d = ser(reg[reg["type"] == "D"])
    w = ser(fu[fu["fueltype"] == "WND"])
    so = ser(fu[fu["fueltype"] == "SUN"])
    return {
        "load": d,
        "wind": w,
        "solar": so,
        "nl": d - w - so,
        "local": idx - pd.Timedelta(hours=CST_OFFSET_H),
    }


def fwd_max(x: np.ndarray, w: int) -> np.ndarray:
    """max(x[t : t+w]) with the tail truncated at year end."""
    return pd.Series(x[::-1]).rolling(w, min_periods=1).max().to_numpy()[::-1]


def spells(on: np.ndarray) -> np.ndarray:
    """Length of the online spell each hour belongs to (0 where offline)."""
    out = np.zeros(len(on), int)
    idx = np.flatnonzero(on)
    if not len(idx):
        return out
    br = np.flatnonzero(np.diff(idx) > 1)
    st, en = np.r_[idx[0], idx[br + 1]], np.r_[idx[br], idx[-1]]
    for s, e in zip(st, en):
        out[s : e + 1] = e - s + 1
    return out


def main() -> int:
    """Run the driver census for every keeper year."""
    pay = json.load(open(sys.argv[1]))
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    bench = {
        y: json.load(gzip.open(REPO / f"frontend/data/backcast/bench/SPP/{y}.json.gz"))[
            "bench"
        ]["plants"]
        for y in YEARS
    }
    # plant series per year
    series: dict[str, dict[str, dict]] = {}
    for y in YEARS:
        mp = pay["years"][y]["plants"]
        series[y] = {}
        for k, v in bench[y].items():
            if (
                v["group"] != "CC_REGULAR"
                or v.get("nodata") in (True, "True")
                or not v.get("campd")
            ):
                continue
            key = k if k in mp else f"{k}:CC_REGULAR"
            c = dec(v["campd"])
            m = dec(mp[key]["m"]) if key in mp else np.zeros(len(c))
            if len(c) != 8760 or len(m) != 8760:
                continue
            series[y][k] = {
                "c": c,
                "m": m,
                "npl": float(v["npl"]),
                "name": v.get("name", k),
            }
    # leave-year-out conduct: pooled on-frequency over the OTHER years
    onh = {
        y: {k: (s["c"] >= ON_CEMS).sum() for k, s in series[y].items()} for y in YEARS
    }

    def conduct_lyo(y: str, k: str) -> float:
        num = sum(onh[o][k] for o in YEARS if o != y and k in onh[o])
        den = 8760 * sum(1 for o in YEARS if o != y and k in onh[o])
        return num / den if den else np.nan

    out: dict = {}
    for y in YEARS:
        yi = int(y)
        L = lmp[lmp.year == yi].set_index("hour").reindex(range(8760))
        rt, da = L["rt"].to_numpy(float), L["da"].to_numpy(float)
        low = rt <= LOW
        e = eia930(yi)
        loc = e["local"]
        month = loc.month.to_numpy()
        gasday = (loc - pd.Timedelta(hours=9)).normalize()
        nl_gd = (
            pd.Series(e["nl"]).groupby(gasday.to_numpy()).transform("max").to_numpy()
        )
        drivers = {
            "nl_now": e["nl"],
            "nl_fwd24": fwd_max(e["nl"], 24),
            "nl_gasday": nl_gd,
            "load_fwd24": fwd_max(e["load"], 24),
            "month_cold": np.isin(month, [11, 12, 1, 2, 3]).astype(float),
            "da_low": (da <= LOW).astype(float),
        }
        Y, M, P, S, C, NPL = [], [], [], [], [], []
        per_plant = {}
        for k, s in series[y].items():
            on = s["c"] >= ON_CEMS
            mon = s["m"] >= ON_MODEL
            sp = spells(on)
            cd = conduct_lyo(y, k)
            Y.append(on[low])
            M.append(mon[low])
            S.append(sp[low])
            C.append(np.full(low.sum(), cd))
            NPL.append(np.full(low.sum(), s["npl"]))
            P.append(np.flatnonzero(low))
            per_plant[k] = {
                "name": s["name"],
                "npl": s["npl"],
                "conduct_lyo": round(float(cd), 3),
                "on_all": round(float(on.mean()), 3),
                "on_low": round(float(on[low].mean()), 3) if low.any() else None,
                "model_on_low": round(float(mon[low].mean()), 3) if low.any() else None,
                "low_online_twh_minload": round(
                    float((on & low).sum() * MIN_LOAD * s["npl"] / 1e6), 3
                ),
                "gap_twh_minload": round(
                    float((on & ~mon & low).sum() * MIN_LOAD * s["npl"] / 1e6), 3
                ),
            }
        Y, M, S, C, NPL, P = map(np.concatenate, (Y, M, S, C, NPL, P))
        res = {
            "low_hours": int(low.sum()),
            "da_low_share_of_low_rt": round(float((da[low] <= LOW).mean()), 3),
            "plant_hours": int(len(Y)),
            "cems_online_rate_low": round(float(Y.mean()), 3),
            "model_online_rate_low": round(float(M.mean()), 3),
            "cems_online_rate_all": round(
                float(
                    np.mean([(s["c"] >= ON_CEMS).mean() for s in series[y].values()])
                ),
                3,
            ),
            "gap_twh_minload": round(float(((Y & ~M) * NPL).sum() * MIN_LOAD / 1e6), 3),
            "auc": {},
            "long_spell_share_of_low_online": round(
                float((S[Y] > LONG_SPELL_H).mean()), 3
            ),
            "median_spell_h_of_low_online": float(np.median(S[Y])) if Y.any() else None,
        }
        for nm, x in drivers.items():
            res["auc"][nm] = None if auc(x[P], Y) is None else round(auc(x[P], Y), 3)
        res["auc"]["conduct_lyo"] = round(auc(np.nan_to_num(C, nan=0.0), Y), 3)
        # within-plant AUC (removes the plant-identity effect): capacity-weighted mean over plants
        wp = {}
        for nm, x in drivers.items():
            vals, wts = [], []
            for k, s in series[y].items():
                on = (s["c"] >= ON_CEMS)[low]
                a = auc(x[low], on)
                if a is not None:
                    vals.append(a)
                    wts.append(s["npl"])
            wp[nm] = round(float(np.average(vals, weights=wts)), 3) if vals else None
        res["auc_within_plant"] = wp
        # conduct-class split of the L-hour online energy
        for lab, lo_, hi_ in (
            ("always_on_gt0.8", 0.8, 1.01),
            ("mid_0.5_0.8", 0.5, 0.8),
            ("cycler_lt0.5", -1, 0.5),
        ):
            sel = (C > lo_) & (C <= hi_) if lab != "cycler_lt0.5" else (C < hi_)
            res[f"class_{lab}"] = {
                "cems_on_rate_low": round(float(Y[sel].mean()), 3)
                if sel.any()
                else None,
                "model_on_rate_low": round(float(M[sel].mean()), 3)
                if sel.any()
                else None,
                "gap_twh_minload": round(
                    float(((Y & ~M & sel) * NPL).sum() * MIN_LOAD / 1e6), 3
                ),
                "cems_low_online_twh_minload": round(
                    float(((Y & sel) * NPL).sum() * MIN_LOAD / 1e6), 3
                ),
            }
        # precision / recall of the zero-parameter conduct rule "online iff conduct_lyo > 0.5"
        pred = C > 0.5
        tp = (pred & Y).sum()
        res["rule_conduct_gt0.5"] = {
            "precision": round(float(tp / pred.sum()), 3) if pred.any() else None,
            "recall": round(float(tp / Y.sum()), 3) if Y.any() else None,
            "reach_twh_minload_where_model_off": round(
                float(((pred & ~M) * NPL).sum() * MIN_LOAD / 1e6), 3
            ),
            "correct_reach_twh_minload": round(
                float(((pred & ~M & Y) * NPL).sum() * MIN_LOAD / 1e6), 3
            ),
        }
        res["plants"] = per_plant
        out[y] = res
        print(y, {k: v for k, v in res.items() if k != "plants"})
    p = REPO / "docs/records/spp/spp102"
    p.mkdir(parents=True, exist_ok=True)
    (p / "cc_commitment_drivers.json").write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
