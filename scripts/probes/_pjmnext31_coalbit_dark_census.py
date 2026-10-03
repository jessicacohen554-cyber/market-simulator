"""PJM-NEXT-31 (ZERO LP): COAL_BIT whole-unit dark hours the keeper's windows miss.

Readings fixed ex ante in
``docs/records/pjm/FINDING-pjm-next-31-coalbit-dark-census-2026-10-03.md`` §1.

Per year, for each CAMPD unit of a keeper COAL_BIT plant: unit-dark hours (``opTime == 0``
or no row), their dark-run length, coverage by the three committed extracts the keeper
reads, and the reason class C0..C5 of every uncovered dark hour. Per plant-hour, the
unreflected dark MW = max(0, K* x sum(dark unit shares) - (K* - K(h))), with K the keeper
``cap_mw``. Also the revealed-tight share (EIA-930 local high-net-load mask) and the S2
(real implied HR >= HI_HR) subset, so totals compare with NEXT-30's K-twin pieces.

Writes ``results/phase0/pjm/_pjmnext31_coalbit_dark_census.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
sys.path.insert(0, str(REPO))
from _pjmnext28_sunk_noload import _parquet, gas_daily  # noqa: E402
from _pjmnext29_coalbit_bins import GROUP, HI_HR, T  # noqa: E402
from _pjmnext29_lowhour_setters import real_low_hours  # noqa: E402

from scripts.data.derive_campd_unit_outages import SHORT_BASELOAD_CF  # noqa: E402
from scripts.lib.outage_detect import (  # noqa: E402
    MIN_INMERIT_HOURS,
    filter_revealed_outages,
    high_load_mask,
)

OUT = REPO / "results/phase0/pjm/_pjmnext31_coalbit_dark_census.json"
UNIT_DIR = REPO / "data/raw/campd-unit-level"
RAW = REPO / "data/raw"
#: The three committed extracts the keeper resolves (FINDING §1 table).
EXTRACTS = {
    "long": RAW / "campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv",
    "short": RAW / "campd-unit-outages-short-rederive-PJM.csv",
    "shortgas": RAW / "campd-unit-outages-shortgas-PJM.csv",
}
YEARS = tuple(range(2019, 2026))
POOL = (2019, 2020, 2021)
CLASSES = ("C0", "C1", "C2", "C3", "C4", "C5")
#: Dark-run length bands (hours): the short layer's 1-day floor, the long layer's 5-day floor.
DAY_H = 24
LONG_H = 120


def _runs(mask: np.ndarray):
    """(start, stop) of each maximal True run."""
    if not mask.any():
        return
    idx = np.flatnonzero(np.diff(np.r_[0, mask.view(np.int8), 0]))
    yield from zip(idx[::2].tolist(), idx[1::2].tolist())


def extract_masks(y: int) -> tuple[dict, dict]:
    """(unit -> covered hour mask, unit -> long-only mask) at the loader's day grain."""
    y0 = pd.Timestamp(f"{y}-01-01")
    cov: dict[tuple[int, str], np.ndarray] = {}
    lng: dict[tuple[int, str], np.ndarray] = {}
    for name, path in EXTRACTS.items():
        df = pd.read_csv(path)
        df["outage_start"] = pd.to_datetime(df["outage_start"])
        df["outage_end"] = pd.to_datetime(df["outage_end"])
        df = df[(df["outage_end"].dt.year >= y) & (df["outage_start"].dt.year <= y)]
        for r in df.itertuples():
            k = (int(r.facility_id), str(r.unit_id))
            s = int((r.outage_start - y0) / pd.Timedelta(hours=1))
            e = int((r.outage_end + pd.Timedelta(days=1) - y0) / pd.Timedelta(hours=1))
            s, e = max(s, 0), min(e, T)
            if e <= s:
                continue
            for d in (cov, lng) if name == "long" else (cov,):
                d.setdefault(k, np.zeros(T, bool))[s:e] = True
    return cov, lng


def unit_frame(y: int, plants: set[int]) -> pd.DataFrame:
    """CAMPD unit-level rows for ``plants`` (facilityId dtype mixes across files)."""
    fr = []
    for f in sorted(UNIT_DIR.glob(f"*_{y}.parquet")):
        x = (
            ds.dataset(str(f), format="parquet")
            .to_table(
                columns=[
                    "facilityId",
                    "unitId",
                    "date",
                    "hour",
                    "opTime",
                    "grossLoad",
                    "primaryFuelInfo",
                ]
            )
            .to_pandas()
        )
        x["facilityId"] = pd.to_numeric(x["facilityId"], errors="coerce")
        fr.append(x[x["facilityId"].isin(plants)])
    d = pd.concat(fr, ignore_index=True)
    d["hoy"] = (
        pd.to_datetime(d["date"]) - pd.Timestamp(f"{y}-01-01")
    ).dt.days * 24 + d["hour"].astype(int)
    d = d[(d["hoy"] >= 0) & (d["hoy"] < T)]
    d["unitId"] = d["unitId"].astype(str)
    return d


def run_year(y: int, gas: pd.Series, coal_only: bool = False) -> dict:
    """Census one year (``coal_only``: the post-hoc sensitivity, coal-fuel CAMPD units only)."""
    rl = real_low_hours(y, gas).reindex(range(T))
    s2 = (rl["p_real"] / rl["gas"]).to_numpy() >= HI_HR
    tight = high_load_mask("PJM", y, T)
    assert tight is not None, "PJM EIA-930 net-load mask missing"
    um = _parquet(
        f"unit_marginal_{y}.parquet",
        columns=["plant_code", "hour", "cap_mw"],
        filters=[("plant_group", "=", GROUP)],
    )
    cap = (
        um.groupby(["plant_code", "hour"], observed=True)["cap_mw"]
        .sum()
        .unstack(0)
        .reindex(range(T))
        .fillna(0.0)
    )
    cap.columns = cap.columns.astype(int)
    plants = set(cap.columns)
    d = unit_frame(y, plants)
    if coal_only:
        fuel = d.groupby(["facilityId", "unitId"])["primaryFuelInfo"].agg(
            lambda v: v.dropna().astype(str).str.contains("Coal").any()
        )
        coal = set(fuel[fuel].index)
        d = d[[k in coal for k in zip(d["facilityId"], d["unitId"])]]
    cov, lng = extract_masks(y)

    acc = {
        "all": {c: 0.0 for c in CLASSES},
        "s2": {c: 0.0 for c in CLASSES},
        "tight_all": {c: 0.0 for c in CLASSES},
    }
    unref = np.zeros(T)
    unref_unc = np.zeros(T)
    dark_mw_tot = np.zeros(T)
    whole_year_dark_units = 0
    matched = set()
    for pc, g in d.groupby("facilityId"):
        pc = int(pc)
        K = cap[pc].to_numpy()
        kstar = float(K.max())
        if kstar <= 0:
            continue
        units = {}
        for uid, gu in g.groupby("unitId"):
            gross = np.zeros(T)
            op = np.zeros(T)
            gross[gu["hoy"].to_numpy()] = gu["grossLoad"].fillna(0.0).to_numpy()
            op[gu["hoy"].to_numpy()] = gu["opTime"].fillna(0.0).to_numpy()
            if gross.max() <= 0:
                whole_year_dark_units += 1
                continue
            units[uid] = (gross, op <= 0.0)
        if not units:
            continue
        matched.add(pc)
        peak = {u: v[0].max() for u, v in units.items()}
        ptot = sum(peak.values())
        dark_share = np.zeros(T)
        unc_share = np.zeros(T)
        for uid, (gross, dark) in units.items():
            u = peak[uid] / ptot
            dark_share += u * dark
            w = u * kstar
            k = (pc, uid)
            c_mask = cov.get(k, np.zeros(T, bool))
            l_mask = lng.get(k, np.zeros(T, bool))
            cf = gross / peak[uid]
            oper = ~l_mask
            oper_cf = float(cf[oper].mean()) if oper.any() else 0.0
            cls = np.full(T, -1, np.int8)
            for s, e in _runs(dark):
                L = e - s
                seg = slice(s, e)
                kept = bool(
                    filter_revealed_outages([(s, e)], tight, cf, MIN_INMERIT_HOURS)
                )
                if L < DAY_H:
                    c = 1
                elif L < LONG_H and oper_cf < SHORT_BASELOAD_CF:
                    c = 2
                elif L < LONG_H and not kept:
                    c = 3
                elif L >= LONG_H and not kept:
                    c = 4
                else:
                    c = 5
                cls[seg] = c
            cls[dark & c_mask] = 0
            unc_share += u * (dark & ~c_mask)
            for i, name in enumerate(CLASSES):
                m = cls == i
                acc["all"][name] += w * float(m.sum())
                acc["s2"][name] += w * float((m & s2).sum())
                acc["tight_all"][name] += w * float((m & tight).sum())
        dmw = kstar * dark_share
        red = kstar - K
        dark_mw_tot += dmw
        ur = np.maximum(0.0, dmw - red)
        unref += ur
        # Info only: the part of the unreflected MW explained by uncovered dark units.
        unref_unc += np.minimum(ur, kstar * unc_share)

    n_s2 = int(s2.sum())
    return {
        "plants_keeper": len(plants),
        "plants_matched": len(matched),
        "whole_year_dark_units": whole_year_dark_units,
        "h_s2": n_s2,
        "K_s2_mean": float(cap.to_numpy()[s2].sum(axis=1).mean()),
        "unreflected_mw_s2_mean": float(unref[s2].mean()),
        "unreflected_mw_all_mean": float(unref.mean()),
        "unreflected_uncovered_mw_s2_mean": float(unref_unc[s2].mean()),
        "tight_base_rate": float(tight.mean()),
        "dark_mw_s2_mean": float(dark_mw_tot[s2].mean()),
        "dark_mwh_by_class_all": acc["all"],
        "dark_mwh_by_class_s2": acc["s2"],
        "dark_mwh_by_class_tight": acc["tight_all"],
    }


def _shares(x: dict) -> dict:
    tot = sum(v for k, v in x.items() if k != "C0")
    return {k: (v / tot if tot else 0.0) for k, v in x.items() if k != "C0"}


def readings(res: dict) -> dict:
    """Apply FINDING §1 Q1..Q5 as fixed."""
    n30 = json.loads(
        (REPO / "results/phase0/pjm/_pjmnext30_coalbit_loading.json").read_text()
    )
    out: dict = {}

    def pool(key: str, yrs) -> dict:
        return {c: sum(res[y][key][c] for y in yrs) for c in CLASSES}

    # Q1: unreflected S2 MW vs NEXT-30 K-twin (derate + offline) x unit-dark share, pooled 2019-21.
    num = den = 0.0
    q1_by_year = {}
    n30y = {int(e["year"]): e for e in n30["years"]}
    for y in POOL:
        yr = n30y[y]
        twin = yr["twin_pieces_mw"]
        ref = (twin["derate"] + twin["offline"]) * yr[
            "unit_dark_share_of_derate_offline"
        ]
        num += res[y]["unreflected_mw_s2_mean"] * res[y]["h_s2"]
        den += ref * res[y]["h_s2"]
        q1_by_year[y] = {"census": res[y]["unreflected_mw_s2_mean"], "n30_ref": ref}
    out["Q1"] = {
        "ratio": num / den if den else None,
        "by_year": q1_by_year,
        "verdict": None
        if not den
        else ("ACCOUNTS" if num / den >= 0.5 else "SHORTFALL"),
    }
    # Q2: class shares of uncovered dark MWh.
    s_all = _shares(pool("dark_mwh_by_class_s2", YEARS))
    s_pool = _shares(pool("dark_mwh_by_class_s2", POOL))
    a_all = _shares(pool("dark_mwh_by_class_all", YEARS))
    top = sorted(s_all, key=s_all.get, reverse=True)
    out["Q2"] = {
        "s2_shares_2019_25": s_all,
        "s2_shares_2019_21": s_pool,
        "allhours_shares_2019_25": a_all,
        "dominant": top[0] if s_all[top[0]] >= 0.5 else None,
        "top_two": top[:2],
        "covered_C0_mwh_s2": pool("dark_mwh_by_class_s2", YEARS)["C0"],
    }
    lead = out["Q2"]["dominant"] or top[0]
    pa, pt = (
        pool("dark_mwh_by_class_all", YEARS),
        pool("dark_mwh_by_class_tight", YEARS),
    )
    tight_share = {c: (pt[c] / pa[c] if pa[c] else None) for c in CLASSES}
    out["Q3"] = {
        "class": lead,
        "tight_share_by_class": tight_share,
        "verdict": "ADMISSIBLE"
        if (tight_share[lead] or 0) >= 0.5
        else "NOT ADMISSIBLE",
    }
    gate = lead in ("C1", "C2", "C3", "C4")
    out["Q4"] = {
        "verdict": "CHARTERED"
        if gate and out["Q3"]["verdict"] == "ADMISSIBLE"
        else "NOT CHARTERED",
        "family": lead,
    }
    out["Q5"] = {
        y: res[y]["dark_mwh_by_class_s2"][lead]
        / max(res[y]["h_s2"], 1)
        / res[y]["K_s2_mean"]
        for y in YEARS
    }
    return out


def main() -> None:
    """Run every year, apply the readings, write the JSON (``--coal-only``: sensitivity)."""
    coal_only = "--coal-only" in sys.argv
    out_path = OUT.with_name(OUT.stem + "_coalonly.json") if coal_only else OUT
    gas = gas_daily()
    res = {}
    for y in YEARS:
        res[y] = run_year(y, gas, coal_only)
        print(
            y,
            json.dumps(
                {k: v for k, v in res[y].items() if not k.startswith("dark_mwh")}
            ),
        )
        print("   s2", {k: round(v) for k, v in res[y]["dark_mwh_by_class_s2"].items()})
    out = {"coal_only": coal_only, "years": res, "readings": readings(res)}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out["readings"], indent=2, default=str))


if __name__ == "__main__":
    main()
