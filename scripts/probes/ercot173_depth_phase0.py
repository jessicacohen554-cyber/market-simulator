"""ercot-173 Phase 0 (NO LP): the 2023 depth object at the tail hours.

Executes `docs/PRECOMMIT-ercot173-2023-depth-and-ceiling-reconciliation-2026-08-06.md`
§2–§4 exactly. Three questions, all no-LP, all on committed inputs:

(a) what sets the model's $196.5 ceiling in the 123 missed >$200 hours — the
    marginal tranche/class and its P1 bid, plus the cleared stack by class;
(b) the depth split per class: X_c = [A_model − A_mkt] (AVAILABILITY face) +
    [W_r − W_m] (OFFER face), against M(h) = the model's undispatched
    sub-$200 capability (the MW that must not be there for the price to
    cross $200);
(c) the four 2023 phantom shed hours re-run through the ercot-172 per-plant
    tables (E from the flag-toggled captures, f_window/f_partial/f_COP/f_CEMS)
    — SAME-DEFECT vs OPPOSITE/OTHER.

Instruments imported verbatim (precommit §1): the ercot148 availability
capture (subprocess, UNMODIFIED), `reconstruct_bundle_fleet` +
`ercot161_afternoon_wall_phase0._compose_markups` for the P1 bid matrix,
`market_sim.data.outages` loaders, the DAM site-hourly parquet, CAMPD TX
hourly. Rule 22: 2023 only (a training year). No LP, no network.

Usage:
    PYTHONPATH=.:src python scripts/probes/ercot173_depth_phase0.py \
        [--work /tmp/ercot173_captures] \
        [--out results/calibration/ercot173_depth_phase0.json]
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

YEAR = 2023
BUNDLE = REPO / "results/calibration/ercot168_yearcurves_B"
ACTUAL = RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
CORPUS = RAW_DATA_DIR / "ercot" / "SCED"
CAPTURE = REPO / "scripts" / "probes" / "ercot148_availability_capture.py"
DEFAULT_OUT = REPO / "results/calibration/ercot173_depth_phase0.json"

# Precommit §0 — the 2023 phantom shed census (identified pre-measurement).
SHED = {
    4097: ("2023-06-20 17:00", 213.0),
    5490: ("2023-08-17 18:00", 555.9),
    5682: ("2023-08-25 18:00", 1266.0),
    5802: ("2023-08-30 18:00", 1428.7),
}
# Precommit §3/§4 bars — read, never recomputed.
BAR_L1, BAR_L2, BAR_SHARE = 0.90, 0.90, 0.60
PRICE_BAR = 200.0

# Coarse-class maps (precommit §2 scope S; storage/renewables/nuclear OUT).
MODEL_CLS = {
    "COAL": "COAL",
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "CT_PEAKER": "CT",
    "CT_CHP": "CT",
    "ST_GAS": "ST_GAS",
}
COP_CLS = {"COAL": "COAL", "CC_REGULAR": "CC", "CT_PEAKER": "CT", "ST_GAS": "ST_GAS"}
RESTYPE_CLS = {
    "CLLIG": "COAL",
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT",
    "SCLE90": "CT",
    "GSREH": "ST_GAS",
    "GSNONR": "ST_GAS",
    "GSSUP": "ST_GAS",
}
ONLINE = {"ON", "ONRUC", "ONTEST", "ONREG", "ONREGL", "ONHOLD", "ONOS", "ONOSREG"}
STARTABLE = {"OFFQS", "OFFNS"}
MW_COLS = [f"SCED1 Curve-MW{i}" for i in range(1, 11)]
PR_COLS = [f"SCED1 Curve-Price{i}" for i in range(1, 11)]
COARSE = ("COAL", "CC", "CT", "ST_GAS")


def model_clock(year: int) -> pd.DatetimeIndex:
    """The model's fixed non-leap hourly clock for ``year``."""
    return pd.DatetimeIndex(
        [
            t
            for t in pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
            if not (t.month == 2 and t.day == 29)
        ][:8760]
    )


def hour_sets() -> dict:
    """H123 / H61 / shed hours from the committed keeper sidecar + actuals."""
    sysf = pd.read_parquet(BUNDLE / "hourly" / f"system_{YEAR}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    pr = sysf.pivot_table(index="hour", columns="zone", values="price").to_numpy()
    dm = sysf.pivot_table(index="hour", columns="zone", values="demand").to_numpy()
    model = (pr * dm).sum(1) / dm.sum(1)
    act = pd.read_parquet(ACTUAL)
    actual = act[act.year == YEAR].set_index("hour")["rt"].reindex(range(8760)).to_numpy()
    h123 = np.where((actual > PRICE_BAR) & (model <= PRICE_BAR))[0]
    h61 = np.where(actual > 1000.0)[0]
    slack = sysf.groupby("hour")["slack"].sum().reindex(range(8760)).to_numpy()
    assert len(h123) == 123 and len(h61) == 61, (len(h123), len(h61))
    assert set(np.where(slack > 1.0)[0]) == set(SHED), "shed census drift"
    return {"model": model, "actual": actual, "h123": h123, "h61": h61, "slack": slack}


def run_capture(tag: str, year: int, work: Path, sets: list[str]) -> Path:
    """One ercot148 availability capture (UNMODIFIED, subprocess), cached."""
    out = work / f"avail_{year}_{tag}.npz"
    if out.exists():
        return out
    cmd = [sys.executable, str(CAPTURE), str(BUNDLE), "--year", str(year), "--out", str(out)]
    for s in sets:
        cmd += ["--set", s]
    print(f"  capturing {out.name} ...", flush=True)
    subprocess.run(cmd, check=True, cwd=str(REPO), stdout=subprocess.DEVNULL)
    return out


def model_state() -> tuple[dict, np.ndarray]:
    """Keeper 2023 fleet/offer state + P1 bid matrix (no LP)."""
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    import ercot161_afternoon_wall_phase0 as e161

    state, _meta = reconstruct_bundle_fleet(
        BUNDLE, YEAR, required_flags=e161.ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    marks = e161._compose_markups(state)
    return state, np.asarray(marks["mc_bid"])


def class_dispatch() -> dict[str, np.ndarray]:
    """P1 class dispatch (MW) from the keeper's committed sidecar, coarse-keyed."""
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{YEAR}.parquet")
    ch = ch[ch["pass"] == "P1"]
    out: dict[str, np.ndarray] = {c: np.zeros(8760) for c in COARSE}
    for klass, d in ch.groupby("klass"):
        k = str(klass)
        coarse = (
            "COAL"
            if k.startswith("COAL")
            else "CC"
            if k.startswith("CC")
            else "CT"
            if k.startswith("CT")
            else "ST_GAS"
            if k == "ST_GAS"
            else None
        )
        if coarse:
            out[coarse] += (
                d.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0).to_numpy()
            )
    return out


def cop_live_mw() -> dict[str, np.ndarray]:
    """Measured COP live MW per coarse class on the model clock (NaN uncovered)."""
    sh = pd.read_parquet(
        RAW_DATA_DIR / "ercot-thermal-dam-availability-site-hourly.parquet",
        columns=["date", "class", "he", "live_mw"],
    )
    sh["date"] = pd.to_datetime(sh["date"])
    sh = sh[sh.date.dt.year == YEAR].copy()
    sh["coarse"] = sh["class"].map(COP_CLS)
    sh = sh.dropna(subset=["coarse"])
    # HE h covers [h-1, h) — model hour index = (dayofyear-1)*24 + (he-1).
    sh["h"] = (sh.date.dt.dayofyear - 1) * 24 + (sh.he.astype(int) - 1)
    out: dict[str, np.ndarray] = {}
    for c, d in sh.groupby("coarse"):
        arr = np.full(8760, np.nan)
        g = d.groupby("h")["live_mw"].sum()
        idx = g.index.to_numpy(int)
        keep = (idx >= 0) & (idx < 8760)
        arr[idx[keep]] = g.to_numpy(float)[keep]
        out[str(c)] = arr
    return out


def market_stack(hours: np.ndarray) -> dict:
    """SCED-corpus per-class offered depth at ``hours`` (all 12 delivery months).

    Returns per coarse class, per hour: online HSL sum, sub-$200 offered MW
    (V_r seg construction, the ercot-172-addendum machinery), startable
    (OFFQS/OFFNS) HSL and its sub-$200 offered MW. Interval-mean per hour.
    """
    clock = model_clock(YEAR)
    want_ts = clock[hours]
    want = set(want_ts.strftime("%Y-%m-%d %H"))
    months_needed = sorted(set(want_ts.month))
    # delivery month m lives in filename month m+2 (rolls into the next year).
    shard_keys = []
    for m in months_needed:
        fy, fm = (YEAR, m + 2) if m + 2 <= 12 else (YEAR + 1, m + 2 - 12)
        shard_keys.append(f"{fy}-{fm:02d}")
    files: list[str] = []
    for k in sorted(set(shard_keys)):
        files += sorted(glob.glob(str(CORPUS / f"{k}.part*.parquet")))
    if not files:
        raise SystemExit("no SCED corpus shards for the requested hours")
    from zoneinfo import ZoneInfo

    cpt = ZoneInfo("America/Chicago")
    frames = []
    for f in files:
        t = pq.read_table(
            f,
            columns=[
                "SCED Time Stamp",
                "Resource Type",
                "Telemetered Resource Status",
                "HSL",
                *MW_COLS,
                *PR_COLS,
            ],
        ).to_pandas()
        t = t[t["Resource Type"].isin(RESTYPE_CLS)]
        if t.empty:
            continue
        ts = pd.to_datetime(
            t["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
        )
        # Corpus stamps are CPT (prevailing). Convert to fixed CST via the
        # zone's UTC offset: CST hour = CPT − (offset + 6 h).
        loc = ts.dt.tz_localize(cpt, nonexistent="NaT", ambiguous="NaT")
        cst = loc.dt.tz_convert("Etc/GMT+6").dt.tz_localize(None)
        key = cst.dt.strftime("%Y-%m-%d %H")
        keep = key.isin(want)
        if keep.any():
            sub = t[keep].copy()
            sub["cst_hour"] = key[keep]
            sub["stamp"] = t.loc[keep, "SCED Time Stamp"]
            frames.append(sub)
    df = pd.concat(frames, ignore_index=True)
    df["coarse"] = df["Resource Type"].map(RESTYPE_CLS)
    stat = df["Telemetered Resource Status"].astype(str).str.upper().str.strip()
    df["state"] = np.where(
        stat.str.startswith("ON"), "online", np.where(stat.isin(STARTABLE), "startable", "other")
    )
    mw = df[MW_COLS].apply(pd.to_numeric, errors="coerce").to_numpy()
    prc = df[PR_COLS].apply(pd.to_numeric, errors="coerce").to_numpy()
    seg = np.clip(np.diff(np.nan_to_num(mw, nan=0.0), axis=1, prepend=0.0), 0, None)
    fin = np.isfinite(prc)
    df["sub200"] = (seg * (fin & (prc < PRICE_BAR))).sum(axis=1)
    df["offered"] = (seg * fin).sum(axis=1)
    df["hsl"] = pd.to_numeric(df["HSL"], errors="coerce").fillna(0.0)
    n_iv = df.groupby("cst_hour")["stamp"].nunique()
    out: dict[str, dict[str, pd.Series]] = {}
    for (c, st), d in df.groupby(["coarse", "state"]):
        g = d.groupby("cst_hour")[["hsl", "sub200", "offered"]].sum()
        g = g.div(n_iv.reindex(g.index), axis=0)
        out.setdefault(str(c), {})[str(st)] = g
    hour_key = pd.Series(want_ts.strftime("%Y-%m-%d %H"), index=hours)
    covered = sorted(set(df["cst_hour"]))
    return {
        "per_class": out,
        "hour_key": hour_key,
        "n_hours_covered": len(covered),
        "n_hours_wanted": len(want),
        "coverage": len(covered) / len(want),
    }


def cems_2023() -> pd.DataFrame:
    """CAMPD TX hourly gross load per (facility, coal?) on the 2023 clock."""
    d = pd.read_parquet(
        RAW_DATA_DIR / "campd-unit-level" / f"TX_{YEAR}.parquet",
        columns=["facilityId", "primaryFuelInfo", "grossLoad", "date", "hour"],
    )
    d["fid"] = pd.to_numeric(d.facilityId, errors="coerce")
    d["gl"] = d.grossLoad.fillna(0.0)
    d["isCoal"] = d.primaryFuelInfo.astype(str).str.contains("Coal", na=False)
    # 2023 is non-leap: no Feb-29 drop, no day-shift term (ercot-172 was 2024).
    d["h"] = (d.date.dt.dayofyear - 1) * 24 + d.hour
    return (
        d.groupby(["fid", "isCoal", "h"])["gl"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=range(8760), fill_value=0.0)
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", default="/tmp/claude-0/ercot173_captures")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    print("== hour sets (committed artifacts) ==", flush=True)
    hs = hour_sets()
    h123, h61 = hs["h123"], hs["h61"]

    print("== captures A/B (ercot148 machinery, unmodified) ==", flush=True)
    cap_a = run_capture("A", YEAR, work, [])
    cap_b = run_capture(
        "B",
        YEAR,
        work,
        [
            "ercot_dam_availability_coal_event_cap=false",
            "ercot_dam_availability_gas_event_cap=false",
        ],
    )
    A = np.load(cap_a, allow_pickle=True)
    B = np.load(cap_b, allow_pickle=True)
    avail_a, avail_b = A["availability"].astype(float), B["availability"].astype(float)
    pmax, codes = A["pmax"].astype(float), A["plant_code"].astype(int)
    groups = np.array([str(g) for g in A["group"]])
    names = np.array([str(n) for n in A["name"]])
    # G-EXACT / G-SEAM semantics (ercot-172): the toggle only ever raises B.
    if float(np.max(avail_a - avail_b)) > 1e-9:
        raise SystemExit("G-EXACT violated: capture A above capture B somewhere")

    print("== model state + P1 bid matrix (no LP) ==", flush=True)
    state, mc_bid = model_state()
    fa = state["fleet_arrays"]
    st_avail = np.asarray(fa.availability, dtype=float)
    st_codes = np.array([int(c) for c in np.asarray(fa.plant_code)])
    if not (len(st_codes) == len(codes) and (st_codes == codes).all()):
        raise SystemExit("tranche axis mismatch between capture and reconstruction")
    drift = float(np.abs(st_avail[:, :8760] - avail_a[:, :8760]).max())
    print(f"  reconstruction-vs-capture availability max|delta| = {drift:.2e}")
    if drift > 1e-4:
        raise SystemExit("reconstructed availability diverges from capture A")
    coarse_of = np.array([MODEL_CLS.get(g, "") for g in groups])
    in_scope = coarse_of != ""

    print("== market side: SCED corpus at the tail hours ==", flush=True)
    all_hours = np.unique(np.concatenate([h123, h61, np.array(sorted(SHED))]))
    mkt = market_stack(all_hours)
    print(
        f"  corpus hour coverage {mkt['n_hours_covered']}/{mkt['n_hours_wanted']}"
        f" = {mkt['coverage']:.4f} (L1 bar {BAR_L1})"
    )

    print("== COP live MW ==", flush=True)
    cop = cop_live_mw()

    dispatch = class_dispatch()
    cap_hourly = avail_a[:, :8760] * pmax[:, None]
    bid = mc_bid[:, :8760]

    def face_tables(hours: np.ndarray) -> dict:
        rows: dict[str, dict[str, list[float]]] = {
            c: {k: [] for k in (
                "A_model", "V_m", "W_m", "A_mkt", "V_r", "W_r", "X", "dA", "dOffer", "M"
            )}
            for c in COARSE
        }
        hk = mkt["hour_key"]
        for h in hours:
            key = hk.get(h)
            for c in COARSE:
                m = in_scope & (coarse_of == c)
                caph = cap_hourly[m, h]
                bh = bid[m, h]
                a_model = float(caph.sum())
                v_m = float(caph[bh < PRICE_BAR].sum())
                w_m = a_model - v_m
                # cheapest-first fill of the class's sidecar dispatch.
                order = np.argsort(bh, kind="stable")
                cum = np.cumsum(caph[order])
                disp = float(dispatch[c][h])
                left = np.clip(cum - disp, 0.0, None)
                undisp = float(left[-1]) if len(cum) else 0.0
                # undispatched sub-$200: capacity below the $200 boundary not consumed
                nb = int(np.searchsorted(np.sort(bh), PRICE_BAR))
                sub_cap = float(cum[nb - 1]) if nb > 0 else 0.0
                m_h = max(0.0, sub_cap - min(disp, sub_cap))
                pc = mkt["per_class"].get(c, {})
                onl = pc.get("online")
                stb = pc.get("startable")
                v_r = 0.0
                a_mkt = np.nan
                if key is not None:
                    if onl is not None and key in onl.index:
                        v_r += float(onl.loc[key, "sub200"])
                    if stb is not None and key in stb.index:
                        v_r += float(stb.loc[key, "sub200"])
                cop_c = cop.get(c)
                if cop_c is not None and np.isfinite(cop_c[h]):
                    a_mkt = float(cop_c[h])
                w_r = a_mkt - v_r if np.isfinite(a_mkt) else np.nan
                x = v_m - v_r
                rows[c]["A_model"].append(a_model)
                rows[c]["V_m"].append(v_m)
                rows[c]["W_m"].append(w_m)
                rows[c]["A_mkt"].append(a_mkt)
                rows[c]["V_r"].append(v_r)
                rows[c]["W_r"].append(w_r)
                rows[c]["X"].append(x)
                rows[c]["dA"].append(a_model - a_mkt if np.isfinite(a_mkt) else np.nan)
                rows[c]["dOffer"].append(w_r - w_m if np.isfinite(w_r) else np.nan)
                rows[c]["M"].append(m_h)
        out = {}
        for c in COARSE:
            out[c] = {
                k: {
                    "mean": float(np.nanmean(v)),
                    "p50": float(np.nanmedian(v)),
                }
                for k, v in rows[c].items()
            }
            out[c]["_n_finite_Amkt"] = int(np.isfinite(rows[c]["A_mkt"]).sum())
            out[c]["_n"] = len(hours)
        # totals across classes, per hour then aggregated
        tot = {}
        for k in ("X", "dA", "dOffer", "M", "V_m", "V_r"):
            per_h = np.nansum([rows[c][k] for c in COARSE], axis=0)
            tot[k] = {"mean": float(np.mean(per_h)), "p50": float(np.median(per_h))}
        xm = np.nansum([rows[c]["X"] for c in COARSE], axis=0)
        mm = np.nansum([rows[c]["M"] for c in COARSE], axis=0)
        ratio = np.where(mm > 0, xm / np.maximum(mm, 1e-9), np.nan)
        tot["X_over_M_p50"] = float(np.nanmedian(ratio))
        da = np.nansum([rows[c]["dA"] for c in COARSE], axis=0)
        do = np.nansum([rows[c]["dOffer"] for c in COARSE], axis=0)
        tot["dA_share_of_X_p50"] = float(np.nanmedian(np.where(np.abs(xm) > 1e-9, da / xm, np.nan)))
        tot["dOffer_share_of_X_p50"] = float(
            np.nanmedian(np.where(np.abs(xm) > 1e-9, do / xm, np.nan))
        )
        return {"per_class": out, "totals": tot}

    print("== (a)+(b): depth split over H123 / H61 ==", flush=True)
    # (a) the marginal tranche at each missed hour
    sysf = pd.read_parquet(BUNDLE / "hourly" / f"system_{YEAR}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    adders = (
        sysf.groupby("hour")[["reserve_price", "ordc_adder", "rtordpa_overlay"]]
        .max()
        .reindex(range(8760))
        .fillna(0.0)
    )
    marg = []
    for h in h123:
        p = hs["model"][h]
        b_star = p - float(adders.loc[h].sum())
        m = in_scope
        near = np.abs(bid[m, h] - b_star) <= 2.0
        cls = pd.Series(coarse_of[m][near]).value_counts().to_dict()
        marg.append(
            {"h": int(h), "price": round(float(p), 2), "b_star": round(b_star, 2), "marginal_classes": cls}
        )
    marg_cls = pd.Series(
        [max(m["marginal_classes"], key=m["marginal_classes"].get) for m in marg if m["marginal_classes"]]
    ).value_counts().to_dict()

    faces123 = face_tables(h123)
    faces61 = face_tables(h61)

    print("== (c): the four phantom shed hours, per plant ==", flush=True)
    from market_sim.data.outages import (
        partial_outage_derate_factors,
        unit_outage_derate_factors,
        ercot_thermal_dam_availability_plant_series,
    )

    fwin = unit_outage_derate_factors(YEAR, 8760, iso="ERCOT")
    fpar = partial_outage_derate_factors(YEAR, 8760)
    fcop = ercot_thermal_dam_availability_plant_series(YEAR, 8760)
    cems = cems_2023()
    shed_face = {}
    for h, (label, shed_mw) in sorted(SHED.items()):
        e_p = (avail_b[:, h] - avail_a[:, h]) * pmax
        d = pd.DataFrame(
            {"code": codes, "group": groups, "name": names, "E": e_p, "pmax": pmax,
             "avail_a": avail_a[:, h], "avail_b": avail_b[:, h]}
        )
        agg = d.groupby(["code", "group"]).agg(
            E=("E", "sum"), pmax=("pmax", "sum"), name=("name", "first")
        ).reset_index()
        agg = agg.sort_values("E", ascending=False)
        named = agg[agg.E >= 25.0]
        plants = []
        for r in named.itertuples(index=False):
            key = (int(r.code), str(r.group))
            fw = float(fwin[key][h]) if key in fwin else 1.0
            fp = float(fpar[int(r.code)][h]) if int(r.code) in fpar else 1.0
            fc = np.nan
            if fcop and int(r.code) in fcop:
                v = fcop[int(r.code)][h]
                fc = float(v) if np.isfinite(v) else np.nan
            is_coal = str(r.group) == "COAL"
            gl = 0.0
            try:
                gl = float(cems.loc[(float(r.code), is_coal), h])
            except KeyError:
                # fall back to facility total when the fuel split is absent
                try:
                    gl = float(cems.xs(float(r.code), level=0).sum()[h])
                except KeyError:
                    gl = np.nan
            f_cems = gl / float(r.pmax) if np.isfinite(gl) and r.pmax > 0 else np.nan
            plants.append(
                {
                    "code": int(r.code), "name": str(r.name), "group": str(r.group),
                    "E_mw": round(float(r.E), 1), "f_window": round(fw, 4),
                    "f_partial": round(fp, 4), "f_ceiling": round(fw * fp, 4),
                    "f_min": round(min(fw, fp), 4),
                    "f_COP": None if not np.isfinite(fc) else round(fc, 4),
                    "f_CEMS": None if not np.isfinite(f_cems) else round(f_cems, 4),
                    "ceiling_lt_cems": bool(
                        np.isfinite(f_cems) and (fw * fp) < f_cems - 1e-9
                    ),
                }
            )
        e_tot = float(agg.E.sum())
        e_named = float(named.E.sum())
        n_below = sum(1 for p in plants if p["ceiling_lt_cems"])
        shed_face[label] = {
            "hour": int(h), "shed_mw": shed_mw, "E_total": round(e_tot, 1),
            "E_named": round(e_named, 1),
            "E_over_shed": round(e_tot / shed_mw, 2),
            "n_named": len(plants), "n_ceiling_below_cems": n_below,
            "same_defect": bool(e_tot >= shed_mw and n_below >= max(1, len(plants) // 2)),
            "plants": plants,
        }

    # ---- decision rule (precommit §4) --------------------------------------
    l1 = mkt["coverage"]
    l2 = {c: faces123["per_class"][c]["_n_finite_Amkt"] / len(h123) for c in COARSE}
    tot = faces123["totals"]
    licensed = l1 >= BAR_L1 and all(v >= BAR_L2 for v in l2.values())
    xm = tot["X_over_M_p50"]
    da_share, do_share = tot["dA_share_of_X_p50"], tot["dOffer_share_of_X_p50"]
    if not licensed:
        branch = "FILED-UNLICENSED"
    elif not (xm >= BAR_SHARE):
        branch = "FILED-REDIRECTED"
    elif max(da_share, do_share) >= BAR_SHARE:
        branch = "ACTIONABLE-FACE-" + ("AVAIL" if da_share >= do_share else "OFFER")
    else:
        branch = "FILED-NULL"

    out = {
        "session": "ercot-173", "phase": 0, "lp_solved": False, "year": YEAR,
        "bundle": str(BUNDLE.relative_to(REPO)),
        "licence": {"L1_corpus": round(l1, 4), "L2_cop_by_class": {k: round(v, 4) for k, v in l2.items()},
                    "bars": {"L1": BAR_L1, "L2": BAR_L2, "share": BAR_SHARE}},
        "a_marginal": {"by_hour_head": marg[:12], "modal_marginal_class": marg_cls},
        "b_faces_H123": faces123, "b_faces_H61": faces61,
        "c_shed_face": shed_face,
        "decision": {"X_over_M_p50": xm, "dA_share_p50": da_share,
                     "dOffer_share_p50": do_share, "branch": branch},
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out["decision"], indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
