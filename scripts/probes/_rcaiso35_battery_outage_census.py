"""R-CAISO-35 probe: battery-outage census and the rule-19 test vs the shape anchor.

Zero LP, report-only (handoff R-CAISO-35, link 17; tests pre-registered in
``docs/records/caiso/r-caiso-35/PRECOMMIT-r-caiso-35-battery-outage-census-2026-10-02.md``).
Re-run in R-CAISO-36 (link 18) after the crosswalk review and the selector fix
in ``build_caiso_resource_crosswalk.is_battery_resource``; the census
population follows that selector, and coverage is also split by
``match_method``.

Per hour of 2023-25 on the EIA-930 CISO row clock the envelope was derived on
(``scripts/derive_caiso_storage_shape.py``: first 8760 rows of each year),
battery MW offline in the CNOG episodes (per resource, overlapping curtailments
summed and capped at the resource Pmax) is divided by the EIA-860 monthly
battery fleet MW, giving ``o(t)`` and ``a(t) = 1 - o(t)``.

- T1 (primary): share of hours where the p95 envelope ``e_d[hod]`` exceeds
  ``a(t)`` (the envelope grants MW the outages removed), d in {chg, dis}.
  Sensitivities: RTM storage bidding fleet denominator; crosswalk-accepted
  population only.
- T2: share of hours where measured ``|NG: OTH|`` / fleet exceeds ``a(t)``.
- T3: within-quarter Spearman of daily mean ``o`` vs daily max measured
  discharge / fleet (descriptive).

R-CAISO-38 (link 20) adds the opt-in ``--pre-cod-basis`` block (PRECOMMIT
``docs/records/caiso/r-caiso-38/``): offline MW of resources whose plant is
not in the denominator fleet in the hour's month, split into accepted pre-COD
(A), accepted absent for another reason (B) and unaccepted (U), and ``o_860``
/ T1 primary / T2 re-read with A+B, then A+B+U, removed from the numerator.
A sensitivity beside the adjudicated reading; without the flag the output is
unchanged.

Usage::

    python3 scripts/probes/_rcaiso35_battery_outage_census.py \
        --out docs/records/caiso/r-caiso-35/battery_outage_census.json \
        [--pre-cod-basis]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from build_caiso_resource_crosswalk import is_battery_resource  # noqa: E402
from derive_caiso_storage_shape import (  # noqa: E402
    DAYS_IN_MONTH,
    EIA930,
    monthly_battery_fleet_mw,
)

YEARS = (2023, 2024, 2025)
WINDOWS = REPO / "data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet"
ENVELOPE = REPO / "data/raw/reference/caiso-storage-shape-envelope.csv"
XWALK = REPO / "data/raw/reference/caiso-storage-resource-eia-crosswalk.csv"
UNIVERSE = REPO / "data/raw/caiso-rtm-eoh-soc"
EIA860M = REPO / "data/raw/eia-860m/august_generator2026.operating.parquet"
TZ = "America/Los_Angeles"
#: PRECOMMIT §4 bands on max over (year, direction) of B.
CARRIED_MAX, MARGINAL_MAX = 0.01, 0.05


def eia930_rows(year: int) -> pd.DataFrame:
    """The derive's 8760 rows of ``year``: hour-beginning UTC, local date, OTH."""
    d = pd.read_parquet(EIA930, columns=["UTC time", "Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    d = d[d["Local date"].dt.year == year].sort_values(["Local date", "Hour"])
    d = d.iloc[:8760].reset_index(drop=True)
    d["hb_utc"] = pd.to_datetime(d["UTC time"]) - pd.Timedelta(hours=1)
    d["oth"] = np.nan_to_num(d["NG: OTH"].to_numpy(dtype=float))
    if len(d) < 8760:  # the derive zero-pads a short year; extend the clock alike
        n = 8760 - len(d)
        last = d.iloc[-1]
        pad = pd.DataFrame(
            {
                "hb_utc": last["hb_utc"] + pd.to_timedelta(np.arange(1, n + 1), "h"),
                "Local date": last["Local date"],
                "oth": 0.0,
            }
        )
        d = pd.concat([d, pad], ignore_index=True)
    return d


def offline_mw(win: pd.DataFrame, grid_utc: pd.DatetimeIndex) -> np.ndarray:
    """Hourly battery MW offline on ``grid_utc`` (hour-beginning, UTC)."""
    total = np.zeros(len(grid_utc))
    for _, g in win.groupby("resource_id"):
        cur = np.zeros(len(grid_utc))
        pmax = float(g["resource_pmax_mw"].max())
        for st, en, mw in zip(g["start_utc"], g["end_utc"], g["curtailment_mw"]):
            a, b = grid_utc.searchsorted(st), grid_utc.searchsorted(en)
            cur[a:b] += float(mw)
        total += np.minimum(cur, pmax)
    return total


def offline_by_resource(win: pd.DataFrame, grid_utc: pd.DatetimeIndex) -> dict:
    """Per-resource hourly offline MW on ``grid_utc`` (the :func:`offline_mw` terms)."""
    return {rid: offline_mw(g, grid_utc) for rid, g in win.groupby("resource_id")}


def denominator_by_plant(year: int) -> tuple[dict[int, np.ndarray], set[int]]:
    """Per-plant (12,) MW of ``monthly_battery_fleet_mw(year)``, and its plant set.

    Rebuilds ``storage.load_eia860_storage``'s row filters (canonical vintage,
    status OP, compressed air out, ``Operating Year <= year``, the COD/retirement
    month mask, CAISO zone lookup) keyed by ``Plant Code`` instead of zone. The
    second return is every in-zone OP plant with the COD filter ignored, so an
    accepted plant absent from the month's fleet can be attributed to its COD.
    """
    from market_sim.config.paths import active_eia860_dir, set_eia860_vintage
    from market_sim.data.zone_assignment import build_zone_lookup
    from market_sim.model.storage import _optional_numeric, _unit_monthly_mask

    set_eia860_vintage(None)
    zl = build_zone_lookup("CAISO")
    df = pd.read_parquet(active_eia860_dir() / "eia860_energy_storage_operable.parquet")
    df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
    if "Technology" in df.columns:
        df = df[
            ~df["Technology"].astype(str).str.contains("Compressed Air", case=False)
        ]
    power = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
    oy = pd.to_numeric(df["Operating Year"], errors="coerce")
    om = pd.to_numeric(df["Operating Month"], errors="coerce")
    ry = _optional_numeric(df, "Planned Retirement Year")
    rm = _optional_numeric(df, "Planned Retirement Month")
    by_plant: dict[int, np.ndarray] = {}
    known: set[int] = set()
    for code, p, y, m, r1, r2 in zip(df["Plant Code"], power, oy, om, ry, rm):
        if p != p or p <= 0.0:
            continue
        try:
            c = int(code)
        except (TypeError, ValueError):
            continue
        if zl.get(c) is None:
            continue
        known.add(c)
        if y == y and y > year:
            continue
        mask = _unit_monthly_mask(y, m, r1, r2, year)
        if mask.any():
            by_plant[c] = by_plant.get(c, np.zeros(12)) + float(p) * mask
    return by_plant, known


def cod_860m() -> dict[int, tuple[int, int]]:
    """Earliest EIA-860M ``Batteries`` (year, month) COD per plant, operating sheet."""
    d = pd.read_parquet(EIA860M)
    d = d[d["Technology"].astype(str).str.strip() == "Batteries"]
    d = d.assign(
        pc=pd.to_numeric(d["Plant ID"], errors="coerce"),
        y=pd.to_numeric(d["Operating Year"], errors="coerce"),
        m=pd.to_numeric(d["Operating Month"], errors="coerce"),
    ).dropna(subset=["pc", "y", "m"])
    first = d.sort_values(["y", "m"]).groupby("pc").first()
    return {int(k): (int(r.y), int(r.m)) for k, r in first.iterrows()}


def readings(off: np.ndarray, f860: np.ndarray, e: dict, oth: np.ndarray) -> dict:
    """``o_860`` stats, T1 primary and T2 for one numerator (PRECOMMIT R0-R2)."""
    a = 1 - off / f860
    meas = {
        "chg": np.clip(-oth, 0, None) / f860,
        "dis": np.clip(oth, 0, None) / f860,
    }
    return {
        "offline_mw_mean": round(float(off.mean())),
        "o_860_mean": round(float((1 - a).mean()), 4),
        "o_860_p99": round(float(np.quantile(1 - a, 0.99)), 4),
        "o_860_max": round(float((1 - a).max()), 4),
        "T1_primary": {d: t1(v, a, f860) for d, v in e.items()},
        "T2_measured_over_available_share": {
            d: round(float((v > a).mean()), 5) for d, v in meas.items()
        },
    }


def pre_cod_basis(
    win: pd.DataFrame,
    xw: pd.DataFrame,
    envelope: pd.DataFrame,
    month_of_row: np.ndarray,
) -> dict:
    """R-CAISO-38: the numerator/denominator plant-basis mismatch, A / B / U."""
    acc = xw[xw["accepted"] == 1]
    plant_of = dict(zip(acc["resource_id"], acc["plant_code"].astype(int)))
    method_of = dict(zip(acc["resource_id"], acc["match_method"]))
    m860 = cod_860m()
    hod = np.arange(8760) % 24
    out: dict = {"years": {}}
    for year in YEARS:
        rows = eia930_rows(year)
        grid = pd.DatetimeIndex(rows["hb_utc"])
        by_plant, known = denominator_by_plant(year)
        f860_m = monthly_battery_fleet_mw(year)
        gap = float(np.abs(sum(by_plant.values()) - f860_m).max())
        if gap > 1e-6:
            raise SystemExit(f"{year}: per-plant denominator off by {gap} MW")
        f860 = f860_m[month_of_row]
        per = offline_by_resource(win, grid)
        off_all = offline_mw(win, grid)
        cls = {k: np.zeros(8760) for k in ("A", "B", "U")}
        res: dict = {k: {} for k in cls}
        for rid, v in per.items():
            if not v.any():
                continue
            pc = plant_of.get(rid)
            if pc is None:
                cls["U"] += v
                res["U"][rid] = float(v.sum())
                continue
            in_fleet = by_plant.get(pc, np.zeros(12))[month_of_row] > 0
            for m in range(12):
                hit = (month_of_row == m) & ~in_fleet & (v > 0)
                if not hit.any():
                    continue
                cod = m860.get(pc) if method_of[rid] == "reviewed_eia860m" else None
                pre = pc in known or (cod is not None and cod > (year, m + 1))
                k = "A" if pre else "B"
                cls[k][hit] += v[hit]
                res[k][rid] = res[k].get(rid, 0.0) + float(v[hit].sum())
        ey = envelope[envelope["year"] == year].sort_values("hod")
        e = {
            "chg": ey["chg_frac_p95"].to_numpy()[hod],
            "dis": ey["dis_frac_p95"].to_numpy()[hod],
        }
        oth = rows["oth"].to_numpy()
        tot = float(off_all.sum())
        yr: dict = {
            "classes": {
                k: {
                    "offline_mw_mean": round(float(v.mean()), 1),
                    "offline_mw_p99": round(float(np.quantile(v, 0.99)), 1),
                    "offline_mwh_share": round(float(v.sum()) / tot, 4),
                    "o_860_pp_mean": round(float((v / f860).mean()) * 100, 2),
                    "resources": len(res[k]),
                    "offline_mwh_share_by_method": {
                        m: round(
                            sum(
                                x
                                for r, x in res[k].items()
                                if method_of.get(r, "unaccepted") == m
                            )
                            / tot,
                            4,
                        )
                        for m in sorted(
                            {method_of.get(r, "unaccepted") for r in res[k]}
                        )
                    },
                    "top_resources_mwh": {
                        r: round(x)
                        for r, x in sorted(res[k].items(), key=lambda kv: -kv[1])[:10]
                    },
                }
                for k, v in cls.items()
            },
            "R0_adjudicated": readings(off_all, f860, e, oth),
            "R1_pre_cod_removed": readings(off_all - cls["A"] - cls["B"], f860, e, oth),
            "R2_not_in_denominator_removed": readings(
                off_all - cls["A"] - cls["B"] - cls["U"], f860, e, oth
            ),
        }
        out["years"][str(year)] = yr
    for r in ("R0_adjudicated", "R1_pre_cod_removed", "R2_not_in_denominator_removed"):
        out[f"{r}_T1_max_bind_share"] = max(
            out["years"][str(y)][r]["T1_primary"][d]["bind_share"]
            for y in YEARS
            for d in ("chg", "dis")
        )
    return out


def localize(ts: pd.Series) -> pd.Series:
    """Pacific prevailing naive stamps -> UTC (DST gaps shifted forward)."""
    return (
        pd.to_datetime(ts)
        .dt.tz_localize(TZ, ambiguous="NaT", nonexistent="shift_forward")
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
    )


def rtm_fleet(year: int, local_dates: pd.Series) -> np.ndarray:
    """Daily RTM storage bidding fleet MW (Σ en_max_mw, s1) mapped to rows."""
    u = pd.read_parquet(UNIVERSE / f"caiso_rtm_storage_universe_{year}.parquet")
    f = u[u["is_storage_s1"]].groupby("trade_date")["en_max_mw"].sum()
    f.index = pd.to_datetime(f.index)
    return local_dates.map(f).ffill().bfill().to_numpy(dtype=float)


def t1(e: np.ndarray, a: np.ndarray, fleet: np.ndarray) -> dict:
    """Share of hours (and MW-h) where the envelope exceeds the available share."""
    over = e > a
    return {
        "bind_share": round(float(over.mean()), 5),
        "bind_hours": int(over.sum()),
        "excess_mwh_share_of_envelope": round(
            float((np.clip(e - a, 0, None) * fleet).sum() / (e * fleet).sum()), 5
        ),
    }


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--pre-cod-basis",
        action="store_true",
        help="add the R-CAISO-38 pre-COD basis block (default output unchanged)",
    )
    args = ap.parse_args()

    win = pd.read_parquet(WINDOWS)
    win = win[
        [
            is_battery_resource(i, n)
            for i, n in zip(win["resource_id"], win["resource_name"])
        ]
    ].copy()
    win["start_utc"], win["end_utc"] = localize(win["start"]), localize(win["end"])
    win = win.dropna(subset=["start_utc", "end_utc"])
    xw = pd.read_csv(XWALK)
    accepted = set(xw.loc[xw["accepted"] == 1, "resource_id"])
    # R-CAISO-36: the name-token-only population (the pre-registered method)
    # beside the reviewed additions, so the coverage lift stays attributable.
    by_method = {
        m: set(g.loc[g["accepted"] == 1, "resource_id"])
        for m, g in xw.groupby("match_method")
    }
    env = pd.read_csv(ENVELOPE)
    month_of_row = np.repeat(np.arange(12), np.array(DAYS_IN_MONTH) * 24)[:8760]
    hod = np.arange(8760) % 24

    result: dict = {
        "population": {
            "census_resources": int(win["resource_id"].nunique()),
            "crosswalk_rows": int(len(xw)),
            "crosswalk_accepted": int(len(accepted)),
            "crosswalk_accepted_plants": int(
                xw.loc[xw["accepted"] == 1, "plant_code"].nunique()
            ),
            "crosswalk_accepted_by_method": {m: len(v) for m, v in by_method.items()},
        },
        "years": {},
    }
    for year in YEARS:
        rows = eia930_rows(year)
        grid = pd.DatetimeIndex(rows["hb_utc"])
        off_all = offline_mw(win, grid)
        off_acc = offline_mw(win[win["resource_id"].isin(accepted)], grid)
        f860 = monthly_battery_fleet_mw(year)[month_of_row]
        frtm = rtm_fleet(year, rows["Local date"])
        ey = env[env["year"] == year].sort_values("hod")
        e = {
            "chg": ey["chg_frac_p95"].to_numpy()[hod],
            "dis": ey["dis_frac_p95"].to_numpy()[hod],
        }
        a860 = 1 - off_all / f860
        artm = 1 - off_all / frtm
        aacc = 1 - off_acc / f860
        yr: dict = {
            "fleet_860_mw_mean": round(float(f860.mean())),
            "fleet_rtm_mw_mean": round(float(frtm.mean())),
            "offline_mw_mean": round(float(off_all.mean())),
            "offline_mw_p99": round(float(np.quantile(off_all, 0.99))),
            "o_860_mean": round(float((1 - a860).mean()), 4),
            "o_860_p99": round(float(np.quantile(1 - a860, 0.99)), 4),
            "o_860_max": round(float((1 - a860).max()), 4),
            "o_rtm_mean": round(float((1 - artm).mean()), 4),
            "coverage_accepted_offline_mwh_share": round(
                float(off_acc.sum() / off_all.sum()), 4
            ),
            "coverage_by_method_offline_mwh_share": {
                m: round(
                    float(offline_mw(win[win["resource_id"].isin(v)], grid).sum())
                    / float(off_all.sum()),
                    4,
                )
                for m, v in by_method.items()
            },
            "envelope_max": {d: round(float(v.max()), 4) for d, v in e.items()},
            "min_headroom_a_minus_e": {
                d: round(float((a860 - v).min()), 4) for d, v in e.items()
            },
            "T1_primary": {d: t1(v, a860, f860) for d, v in e.items()},
            "T1_sens_rtm_denominator": {d: t1(v, artm, frtm) for d, v in e.items()},
            "T1_sens_crosswalk_only": {d: t1(v, aacc, f860) for d, v in e.items()},
        }
        meas = {
            "chg": np.clip(-rows["oth"].to_numpy(), 0, None) / f860,
            "dis": np.clip(rows["oth"].to_numpy(), 0, None) / f860,
        }
        yr["T2_measured_over_available_share"] = {
            d: round(float((v > a860).mean()), 5) for d, v in meas.items()
        }
        day = (
            pd.DataFrame(
                {
                    "date": rows["Local date"].to_numpy(),
                    "o": 1 - a860,
                    "dis": meas["dis"],
                }
            )
            .groupby("date")
            .agg(o=("o", "mean"), dis=("dis", "max"))
        )
        day["q"] = pd.to_datetime(day.index).quarter
        rhos = {}
        for q, g in day.groupby("q"):
            rhos[f"Q{q}"] = round(float(g["o"].corr(g["dis"], method="spearman")), 3)
        yr["T3_spearman_daily_o_vs_peak_dis"] = rhos
        result["years"][str(year)] = yr

    def worst(key: str) -> float:
        return max(
            result["years"][str(y)][key][d]["bind_share"]
            for y in YEARS
            for d in ("chg", "dis")
        )

    def band(x: float) -> str:
        if x <= CARRIED_MAX:
            return "CARRIED"
        return "MARGINAL" if x <= MARGINAL_MAX else "NOT CARRIED"

    prim = worst("T1_primary")
    sens = {k: worst(k) for k in ("T1_sens_rtm_denominator", "T1_sens_crosswalk_only")}
    order = ["CARRIED", "MARGINAL", "NOT CARRIED"]
    reading = max([band(prim)] + [band(v) for v in sens.values()], key=order.index)
    t2_max = max(
        v
        for y in YEARS
        for v in result["years"][str(y)]["T2_measured_over_available_share"].values()
    )
    result["adjudication"] = {
        "T1_primary_max_bind_share": prim,
        "T1_primary_band": band(prim),
        "T1_sensitivity_max_bind_share": sens,
        "reading": reading,
        "T2_max_share": t2_max,
        "T2_caveat": t2_max > 0.01,
    }
    if args.pre_cod_basis:
        result["pre_cod_basis"] = pre_cod_basis(win, xw, env, month_of_row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
