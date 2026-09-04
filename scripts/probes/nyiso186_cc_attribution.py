#!/usr/bin/env python3
"""nyiso-186 — attribute the 2024 ``CC_REGULAR`` excess by plant, NO LP.

PREREG-nyiso186-cc-regular-2024-class §3 (M1–M6), every bar read verbatim:

* **M1** per-plant model energy from a bundle's ``hourly/unit_hourly_<year>.parquet``
  (the control replay is bit-identical to the keeper, so its sidecars ARE the
  keeper's dispatch; the arm's sidecars measure the repair).
* **M2** measured energy on two bases: EIA-923 plant × class net MWh
  (:func:`eia860._eia923_plant_class_totals`, the scorer's own basis) and
  CAMPD gross over the plant's CC units on the keeper's crosswalk
  (:func:`corrected_unit_class`, stack duplicates merged BEFORE any sum).
* **M3** concentration ``C3`` = share of the positive excess carried by the
  three largest plants; ≥ 0.60 CONCENTRATED, ≤ 0.40 DIFFUSE.
* **M4** ``r`` = model base heat rate ÷ CAMPD running-hour HR (merged), each
  top-3 plant against the peers' ``[min, max]``.
* **M5** B1 ``pmax / p99.9`` with the deliverable-energy guard; B2 ``a_p`` =
  model mean availability ÷ CAMPD online share, against the peers' band.
* **M6** the class accounting against the bench (gas-family identity) and the
  when-online loading comparison for the carriers.

Rule 13: everything measured here diagnoses; nothing feeds the LP.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO), str(_REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.data import campd  # noqa: E402
from market_sim.data.campd import (  # noqa: E402
    merge_stack_duplicate_units,
    stack_duplicate_mask,
)
from market_sim.data.fleet.eia860 import _eia923_plant_class_totals  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402
from scripts.lib.campd_measured_classes import (  # noqa: E402
    campd_unittype_class,
    corrected_unit_class,
)
from scripts.lib.outage_detect import (  # noqa: E402
    MERIT_HR_MAX,
    MERIT_HR_MIN,
    MIN_REAL_RUN_HOURS,
    REAL_RUN_CF,
)

KEEPER = _REPO / "results" / "calibration" / "nyiso185_family_hr"
CONTROL = _REPO / "results" / "calibration" / "nyiso186_control"
RAW = _REPO / "data" / "raw"
ISO = "NYISO"
KLASS = "CC_REGULAR"
YEARS = (2023, 2024, 2025)
COMMITTED_MULT = 0.90  # the registered CC_REGULAR committed band multiplier
# PREREG §3 bars, verbatim.
C3_CONCENTRATED, C3_DIFFUSE = 0.60, 0.40
B1_PMAX_RATIO = 1.05
PEER_MIN_CF = 0.20
ONLINE_FRAC_OF_PEAK = 0.05


def _fleet(year: int, bundle: Path) -> tuple[pd.DataFrame, dict[int, set[str]]]:
    """Per-LP-unit frame (plant, class, pmax, hr, mean availability) for a year."""
    st, _ = reconstruct_bundle_fleet(bundle, year, verbose=False)
    fa = st["fleet_arrays"]
    df = pd.DataFrame(
        {
            "unit": np.asarray(fa.unit_ids, dtype=object),
            "plant": np.asarray(fa.plant_code).astype(int),
            "klass": np.asarray(fa.plant_group).astype(str),
            "pmax": np.asarray(fa.pmax, dtype=float),
            "hr": np.asarray(fa.heat_rate, dtype=float),
            "avail": np.asarray(fa.availability, dtype=float).mean(axis=1),
        }
    )
    groups: dict[int, set[str]] = {}
    for p, k in zip(df["plant"], df["klass"]):
        groups.setdefault(int(p), set()).add(str(k))
    return df, groups


def _campd_rows(year: int, plants: set[int]) -> pd.DataFrame:
    frames = []
    for st in campd.states_for_iso(ISO):
        path = RAW / "campd-unit-level" / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path,
            columns=[
                "facilityId",
                "unitId",
                "unitType",
                "date",
                "hour",
                "grossLoad",
                "heatInput",
            ],
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(plants)]
        if len(df):
            frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    raw = df["unitId"].astype(str)
    df["unit"] = merge_stack_duplicate_units(df["facilityId"], raw)
    dup = stack_duplicate_mask(df["facilityId"], raw)
    df["gross"] = (
        pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0).mask(dup, 0.0)
    )
    df["heat"] = pd.to_numeric(df["heatInput"], errors="coerce").fillna(0.0)
    return df


def measured(
    year: int, fleet: pd.DataFrame, groups: dict[int, set[str]]
) -> pd.DataFrame:
    """M2 — per plant: EIA-923 class net MWh, CAMPD gross / online share / p99.9 / HR."""
    plants = sorted(set(fleet[fleet["klass"] == KLASS]["plant"]))
    e923 = _eia923_plant_class_totals(year)
    df = _campd_rows(year, set(plants))
    df["klass"] = [
        corrected_unit_class(campd_unittype_class(t, False), groups.get(int(f)))
        for t, f in zip(df["unitType"], df["facilityId"])
    ]
    rows = []
    for p in plants:
        rec: dict = {
            "plant": p,
            "model_mw": float(
                fleet[(fleet["plant"] == p) & (fleet["klass"] == KLASS)]["pmax"].sum()
            ),
            "e923_cc_mwh": e923.get(p, {}).get(KLASS, np.nan),
        }
        cc = df[(df["facilityId"] == p) & (df["klass"] == KLASS)]
        if cc.empty:
            rec["campd_units"] = 0
            rows.append(rec)
            continue
        rec["campd_units"] = int(cc["unit"].nunique())
        rec["campd_cc_gross_mwh"] = float(cc["gross"].sum())
        ph = cc.groupby(["date", "hour"])["gross"].sum()
        peak = float(np.percentile(ph, 99.9))
        rec["p999"] = peak
        rec["online_share"] = float(
            (ph >= max(1.0, ONLINE_FRAC_OF_PEAK * float(np.percentile(ph, 99.5)))).sum()
            / 8760.0
        )
        rec["load_when_on"] = (
            float(ph[ph >= ONLINE_FRAC_OF_PEAK * peak].mean() / peak)
            if peak > 0
            else np.nan
        )
        per = cc.groupby(["unit", "date", "hour"], sort=False)[["gross", "heat"]].sum()
        out = []
        for u, g in per.groupby(level="unit"):
            gr, ht = g["gross"].to_numpy(), g["heat"].to_numpy()
            pk = float(gr.max()) if gr.size else 0.0
            if pk <= 0:
                continue
            run = gr / pk >= REAL_RUN_CF
            if int(run.sum()) < MIN_REAL_RUN_HOURS or gr[run].sum() <= 0:
                continue
            out.append(
                (
                    float(
                        np.clip(
                            ht[run].sum() / gr[run].sum(), MERIT_HR_MIN, MERIT_HR_MAX
                        )
                    ),
                    float(gr[run].sum()),
                )
            )
        if out:
            w = sum(x[1] for x in out)
            rec["hr_run"] = sum(h * x for h, x in out) / w
        rows.append(rec)
    return pd.DataFrame(rows)


def model(year: int, bundle: Path, fleet: pd.DataFrame) -> pd.DataFrame:
    """M1 — per-plant model MWh, mean available MW and when-online loading."""
    u = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["plant_code", "plant_group", "hour", "mw", "cap_mw"],
    )
    u = u[u["plant_group"] == KLASS]
    g = (
        u.groupby("plant_code")
        .agg(model_mwh=("mw", "sum"), cap_mwh=("cap_mw", "sum"))
        .reset_index()
        .rename(columns={"plant_code": "plant"})
    )
    ph = (
        u.groupby(["plant_code", "hour"])
        .agg(mw=("mw", "sum"), cap=("cap_mw", "sum"))
        .reset_index()
    )
    lw = {}
    for p, d in ph.groupby("plant_code"):
        cmax = float(d["cap"].max())
        on = d["mw"] >= ONLINE_FRAC_OF_PEAK * cmax
        lw[int(p)] = (
            float(on.mean()),
            float(d["mw"][on].mean() / cmax) if on.any() and cmax > 0 else np.nan,
        )
    g["model_on_share"] = [lw.get(int(p), (np.nan, np.nan))[0] for p in g["plant"]]
    g["model_load_when_on"] = [lw.get(int(p), (np.nan, np.nan))[1] for p in g["plant"]]
    av = (
        fleet[fleet["klass"] == KLASS]
        .groupby("plant")
        .apply(
            lambda d: float((d["pmax"] * d["avail"]).sum() / d["pmax"].sum()),
            include_groups=False,
        )
    )
    g["avail_mean"] = g["plant"].map(av)
    com = fleet[
        (fleet["klass"] == KLASS) & fleet["unit"].astype(str).str.endswith("_committed")
    ]
    base = {int(p): float(h) / COMMITTED_MULT for p, h in zip(com["plant"], com["hr"])}
    g["base_hr"] = g["plant"].map(base)
    return g


def year_record(year: int, bundle: Path) -> dict:
    fleet, groups = _fleet(year, bundle)
    m = measured(year, fleet, groups)
    t = model(year, bundle, fleet).merge(m, on="plant", how="outer")
    t["E_twh"] = (t["model_mwh"] - t["e923_cc_mwh"]) / 1e6
    t["r"] = t["base_hr"] / t["hr_run"]
    t["pmax_over_p999"] = t["model_mw"] / t["p999"]
    t["a_p"] = t["avail_mean"] / t["online_share"]
    t["e923_cf"] = t["e923_cc_mwh"] / (t["model_mw"] * 8760.0)
    t = t.sort_values("E_twh", ascending=False).reset_index(drop=True)
    epos = float(t["E_twh"].clip(lower=0).sum())
    top3 = t.head(3)
    c3 = float(top3["E_twh"].clip(lower=0).sum() / epos) if epos > 0 else np.nan
    verdict = (
        "CONCENTRATED"
        if c3 >= C3_CONCENTRATED
        else ("DIFFUSE" if c3 <= C3_DIFFUSE else "MIXED")
    )
    peers = t[
        (t["e923_cf"] >= PEER_MIN_CF) & ~t["plant"].isin(top3["plant"]) & t["r"].notna()
    ]
    band_r = [float(peers["r"].min()), float(peers["r"].max())]
    peers_a = t[
        (t["e923_cf"] >= PEER_MIN_CF)
        & ~t["plant"].isin(top3["plant"])
        & t["a_p"].notna()
    ]
    band_a = [float(peers_a["a_p"].min()), float(peers_a["a_p"].max())]
    tests = {}
    for _, r in top3.iterrows():
        p = int(r["plant"])
        deliverable = (
            r["p999"] * 8760.0 * r["online_share"] if pd.notna(r["p999"]) else np.nan
        )
        tests[p] = {
            "E_twh": round(float(r["E_twh"]), 3),
            "r": None if pd.isna(r["r"]) else round(float(r["r"]), 3),
            "H_A_fires": bool(pd.notna(r["r"]) and r["r"] < band_r[0]),
            "pmax_over_p999": None
            if pd.isna(r["pmax_over_p999"])
            else round(float(r["pmax_over_p999"]), 3),
            "model_twh": round(float(r["model_mwh"]) / 1e6, 3),
            "deliverable_twh": None
            if pd.isna(deliverable)
            else round(float(deliverable) / 1e6, 3),
            "H_B1_fires": bool(
                pd.notna(r["pmax_over_p999"])
                and r["pmax_over_p999"] > B1_PMAX_RATIO
                and r["model_mwh"] > deliverable
            ),
            "a_p": None if pd.isna(r["a_p"]) else round(float(r["a_p"]), 3),
            "H_B2": (
                "UNTESTABLE (no own CAMPD record)"
                if pd.isna(r["a_p"])
                else ("FIRES" if r["a_p"] > band_a[1] else "no")
            ),
            "model_on_share": round(float(r["model_on_share"]), 3),
            "model_load_when_on": round(float(r["model_load_when_on"]), 3),
            "meter_on_share": None
            if pd.isna(r["online_share"])
            else round(float(r["online_share"]), 3),
            "meter_load_when_on": None
            if pd.isna(r["load_when_on"])
            else round(float(r["load_when_on"]), 3),
        }
    cols = [
        "plant",
        "model_mw",
        "model_mwh",
        "e923_cc_mwh",
        "campd_cc_gross_mwh",
        "E_twh",
        "base_hr",
        "hr_run",
        "r",
        "p999",
        "pmax_over_p999",
        "avail_mean",
        "online_share",
        "a_p",
        "e923_cf",
        "model_on_share",
        "model_load_when_on",
        "load_when_on",
    ]
    return {
        "year": year,
        "class_model_twh": round(float(t["model_mwh"].sum()) / 1e6, 3),
        "class_e923_twh": round(float(t["e923_cc_mwh"].sum()) / 1e6, 3),
        "E_plus_twh": round(epos, 3),
        "top3": [int(p) for p in top3["plant"]],
        "C3": round(c3, 3),
        "M3_verdict": verdict,
        "M4_band_r": [round(x, 3) for x in band_r],
        "M5_band_a_p": [round(x, 3) for x in band_a],
        "top3_tests": tests,
        "plants": json.loads(t[cols].round(4).to_json(orient="records")),
    }


def m6(year: int, bundle: Path) -> dict:
    """M6 — class accounting against the bench (the gas-family identity)."""
    import gzip

    b = json.load(
        gzip.open(
            _REPO / "frontend" / "data" / "backcast" / "bench" / ISO / f"{year}.json.gz"
        )
    )["bench"]
    cf = b.get("classFull") or {}
    c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"] if "pass" in c.columns else c
    m = (c.groupby("klass")["mw"].sum() / 1e6).to_dict()
    gas = ["CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"]
    out = {
        k: {
            "model": round(m.get(k, 0.0), 3),
            "actual": round(cf.get(k, np.nan) / 1e6, 3),
            "delta": round(m.get(k, 0.0) - cf.get(k, np.nan) / 1e6, 3),
        }
        for k in gas
        if k in cf
    }
    out["gas_family"] = {
        "model": round(sum(m.get(k, 0.0) for k in gas), 3),
        "eia930_gas": round((b.get("e930") or {}).get("gas", np.nan) / 1e6, 3),
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bundle",
        default=str(CONTROL),
        help="bundle whose unit_hourly sidecars are read",
    )
    ap.add_argument(
        "--out",
        default=str(
            _REPO / "results" / "calibration" / "_nyiso186_cc_attribution.json"
        ),
    )
    ap.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    args = ap.parse_args()
    bundle = Path(args.bundle)
    rec = {
        "session": "nyiso-186",
        "prereg": "results/calibration/PREREG-nyiso186-cc-regular-2024-class.md",
        "bundle": str(bundle.relative_to(_REPO))
        if bundle.is_relative_to(_REPO)
        else str(bundle),
        "years": {},
    }
    for y in args.years:
        yr = year_record(y, bundle)
        yr["M6"] = m6(y, bundle)
        rec["years"][str(y)] = yr
        print(
            f"{y}: C3={yr['C3']} {yr['M3_verdict']} top3={yr['top3']} E+={yr['E_plus_twh']} class {yr['class_model_twh']} vs {yr['class_e923_twh']}"
        )
        for p, tst in yr["top3_tests"].items():
            print(f"   {p}: {tst}")
    Path(args.out).write_text(json.dumps(rec, indent=1) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
