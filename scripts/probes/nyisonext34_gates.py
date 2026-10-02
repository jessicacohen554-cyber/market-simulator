"""NYISO-NEXT-34 gates G-2 / G-3 / G-5 / G-6 / G-7 (zero LP), arm vs the keeper's committed bundles.

Pre-registered in ``docs/records/nyiso/PRECOMMIT-nyiso-next34-measured-oil-burn-2026-10-02.md`` sec. 3:

* G-2: the leg's log reports the measured oil-burn writer active (``--g2-lines``, one shard
  report line per year; checked for "measured oil burn (NYISO <year>)" and > 0 generator-hours);
* G-3: per year/zone P1 demand within 0.1 GWh of the keeper's; load slack <= keeper + 1 GWh;
* G-5: no D-4 FAIL row keyed (year, check, floor, plant) absent from the keeper AND >= 5 GWh;
* G-6: (a) Feb 2023 system load-weighted P1 |error| vs RT < the keeper's; (b) sum |daily err| vs
  RT on the off-cap high-oil days (FINDING sec. 2 population, read from
  ``_nyisonext34_oilburn_offcap.json``) falls in >= 4 of 5 years;
* G-7: from the two verdict JSONs (``calibration_verdict.py --json``): C3a within +-10 % every
  year and 2025 >= -9.6 %; C3b NRMSE rise <= 0.02 every year; C1 / C2 / C4 not downgraded.

G-1 is ``nyisonext34_compose_span.py --check-only``; G-4 is the scorer's C6 / C8.

Usage::

    python3 scripts/probes/nyisonext34_gates.py --verdict-arm a.json a2021.json \\
        --verdict-keeper k.json k2021.json --g2-lines g2.txt --out <json>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
CAL = REPO / "results" / "calibration"
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet"
POP = REPO / "results/phase0/nyiso/_nyisonext34_oilburn_offcap.json"
D4_MIN_GWH = 5.0  # PRECOMMIT sec. 3 G-5, fixed ex ante
C3A_BAND = 10.0  # rubric C3a band, percent
C3A_2025_FLOOR = -9.6  # PRECOMMIT G-7: no erosion of the keeper's 2025 margin
C3B_RISE = 0.02  # PRECOMMIT G-7


def _names(prefix: str) -> dict[int, str]:
    return {2021: f"{prefix}_2021", **{y: f"{prefix}_span" for y in range(2022, 2026)}}


ARM, KEEPER = _names("nyisonext34"), _names("nyisonext26p")


def _sys(b: str, y: int) -> pd.DataFrame:
    """P1 system frame (committed hourly sidecar)."""
    s = pd.read_parquet(CAL / b / "hourly" / f"system_{y}.parquet")
    return s[s["pass"] == "P1"]


def _d4_fail(b: str, y: int) -> dict:
    """D-4 FAIL rows for ``y`` keyed (year, check, floor, plant) -> GWh floored."""
    ld = json.loads((CAL / b / "legitimacy_diagnostics.json").read_text())
    out = {}
    for r in ld["diagnostics"].get("D4", {}).get("rows", []):
        if r.get("year") == y and str(r.get("verdict", "")).upper() == "FAIL":
            key = (r.get("year"), r.get("check"), r.get("floor"), str(r.get("plant")))
            t = r.get("floored_twh")
            out[key] = round(1e3 * float(t), 3) if t not in ("", None) else None
    return out


def _joined(b: str, y: int) -> pd.DataFrame:
    """P1 zonal price joined to measured RT on the 8760 clock (RT gaps filled with DA)."""
    a = pd.read_parquet(ZONAL)
    a = a[a.year == y][["zone", "hour", "rt", "da"]]
    m = _sys(b, y)[["zone", "hour", "price", "demand"]].merge(a, on=["zone", "hour"])
    m["rt"] = m.rt.fillna(m.da)
    return m


def _daily(m: pd.DataFrame, y: int) -> pd.DataFrame:
    day = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(m.hour // 24, "D")
    g = m.assign(date=day.dt.strftime("%Y-%m-%d").to_numpy()).groupby("date")
    return pd.DataFrame(
        {
            c: g.apply(lambda x, c=c: np.average(x[c], weights=x.demand))
            for c in ("price", "rt")
        }
    )


def _feb(m: pd.DataFrame) -> pd.DataFrame:
    """February rows of a 2023 joined frame."""
    mon = (pd.Timestamp("2023-01-01") + pd.to_timedelta(m.hour, "h")).dt.month
    return m[(mon == 2).to_numpy()]


def _records(v: dict, crit: str) -> dict[int, dict]:
    return {
        int(r["year"]): r
        for r in v["criteria"][crit]["records"]
        if r.get("key") is None and r.get("year") is not None
    }


def _merge_verdicts(paths: list[Path]) -> dict:
    """Union of per-year criterion records across verdict JSONs (span + 2021 run)."""
    out: dict = {"criteria": {}}
    for p in paths:
        v = json.loads(p.read_text())
        for crit, body in v["criteria"].items():
            out["criteria"].setdefault(crit, {"records": []})["records"] += body.get(
                "records", []
            )
    return out


def _pct(r: dict) -> float:
    return float(str(r["magnitude"]).split("%")[0])


def main() -> None:
    """Print (and optionally write) the gate table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verdict-arm", nargs="+", type=Path, required=True)
    ap.add_argument("--verdict-keeper", nargs="+", type=Path, required=True)
    ap.add_argument("--g2-lines", type=Path, required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    pop = {r["year"]: r for r in json.loads(POP.read_text())}
    va, vk = _merge_verdicts(a.verdict_arm), _merge_verdicts(a.verdict_keeper)
    g2txt = a.g2_lines.read_text()
    out: dict = {"arm": ARM, "keeper": KEEPER, "years": {}}
    g6b_improved = 0
    for y in range(2021, 2026):
        s, k = _sys(ARM[y], y), _sys(KEEPER[y], y)
        dem = (s.groupby("zone").demand.sum() - k.groupby("zone").demand.sum()).abs().max() / 1e3  # fmt: skip
        sl = (s.slack.sum() - k.slack.sum()) / 1e3
        fa, fk = _d4_fail(ARM[y], y), _d4_fail(KEEPER[y], y)
        new = {str(key): g for key, g in fa.items() if key not in fk}
        blocking = {key: g for key, g in new.items() if g is None or g >= D4_MIN_GWH}
        hit = re.search(
            rf"measured oil burn \(NYISO {y}\).*?in (\d+) generator-hours", g2txt
        )
        ma, mk = _joined(ARM[y], y), _joined(KEEPER[y], y)
        da, dk = _daily(ma, y), _daily(mk, y)
        days = [d["date"] for d in pop[y]["days"] if not d["cap_binds"]]
        e_arm = float((da.loc[days, "price"] - da.loc[days, "rt"]).abs().sum())
        e_kpr = float((dk.loc[days, "price"] - dk.loc[days, "rt"]).abs().sum())
        g6b_improved += int(e_arm < e_kpr)
        cap_days = [d["date"] for d in pop[y]["days"] if d["cap_binds"]]
        rec: dict = {
            "G2_generator_hours": int(hit.group(1)) if hit else None,
            "G2_pass": bool(hit and int(hit.group(1)) > 0),
            "G3_max_zone_demand_dgwh": round(float(dem), 4),
            "G3_slack_dgwh": round(float(sl), 4),
            "G3_pass": bool(dem <= 0.1 and sl <= 1.0),
            "G5_new_d4_fail_gwh": new,
            "G5_pass": not blocking,
            "G6b_offcap_high_oil_days": len(days),
            "G6b_sum_abs_err_vs_rt": {
                "keeper": round(e_kpr, 1),
                "arm": round(e_arm, 1),
            },
            "reported_cap_binding_high_oil_sum_abs_err_vs_rt": {
                "keeper": round(
                    float(
                        (dk.loc[cap_days, "price"] - dk.loc[cap_days, "rt"]).abs().sum()
                    ),
                    1,
                ),  # fmt: skip
                "arm": round(
                    float(
                        (da.loc[cap_days, "price"] - da.loc[cap_days, "rt"]).abs().sum()
                    ),
                    1,
                ),  # fmt: skip
            },
        }
        ca, ck = _records(va, "price_mean")[y], _records(vk, "price_mean")[y]
        ba, bk = _records(va, "price_shape")[y], _records(vk, "price_shape")[y]
        c3a = _pct(ca)
        rec["G7_c3a"] = {"keeper": _pct(ck), "arm": c3a}
        rec["G7_c3b"] = {"keeper": bk["model"], "arm": ba["model"]}
        downgrades = []
        for crit in ("fuelmix", "sysvol", "dispatch_corr"):
            rank = {"PASS": 0, "SKIPPED": 0, "CAVEAT": 1, "FAIL": 2}
            sa = [
                r["status"]
                for r in va["criteria"][crit]["records"]
                if r.get("year") == y
            ]
            sk = [
                r["status"]
                for r in vk["criteria"][crit]["records"]
                if r.get("year") == y
            ]
            if max((rank.get(x, 0) for x in sa), default=0) > max((rank.get(x, 0) for x in sk), default=0):  # fmt: skip
                downgrades.append(crit)
        rec["G7_downgraded"] = downgrades
        rec["G7_pass"] = bool(
            abs(c3a) <= C3A_BAND
            and (y != 2025 or c3a >= C3A_2025_FLOOR)
            and float(ba["model"]) - float(bk["model"]) <= C3B_RISE
            and not downgrades
        )
        if y == 2023:
            fa_, fk_ = _feb(ma), _feb(mk)
            ea = 100 * (np.average(fa_.price, weights=fa_.demand) / np.average(fa_.rt, weights=fa_.demand) - 1)  # fmt: skip
            ek = 100 * (np.average(fk_.price, weights=fk_.demand) / np.average(fk_.rt, weights=fk_.demand) - 1)  # fmt: skip
            rec["G6a_feb2023_pct_vs_rt"] = {"keeper": round(float(ek), 2), "arm": round(float(ea), 2)}  # fmt: skip
            out["G6a_pass"] = bool(abs(ea) < abs(ek))
        out["years"][y] = rec
    out["G6b_years_improved"] = g6b_improved
    out["G6b_pass"] = g6b_improved >= 4
    out["all_pass"] = bool(
        out["G6a_pass"]
        and out["G6b_pass"]
        and all(
            r["G2_pass"] and r["G3_pass"] and r["G5_pass"] and r["G7_pass"]
            for r in out["years"].values()
        )
    )
    txt = json.dumps(out, indent=1, default=str)
    if a.out:
        Path(a.out).write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
