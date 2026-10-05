#!/usr/bin/env python3
"""closeout-chp-transfer (ZERO LP): the MISO/CAISO CHP corrections, censused on every other ISO.

Three CHP corrections moved MISO (w3e/w3f) and CAISO (w6): the measured EIA-923
Schedules 6/7 behind-the-meter share (``*_chp_btm_measured``), the startup-markup
exemption (``chp_startup_covered``) and the chp=Y host biomass/OTHER holdout
(``mustrun_chp_btm_holdout``). This probe measures, per ISO and year, from the
committed keeper bundle and measured data only:

a) CENSUS. Per keeper-bench CHP plant (``bench.plants[code].group`` in
   CC_CHP / CT_CHP / ST_CHP -- the same plant -> group map the BTM frame keys
   on): EIA-923 class net x (default ``chp_btm_pct`` - measured share), the
   measured share pooled CY2022-2024 from Schedules 6/7 exactly as
   ``scripts/data/derive_caiso_chp_btm_share.py`` defines it (grid = resale +
   tolling + outgoing). The bench CHP actual rises by that dE (less BTM
   subtracted). The family reconcile (``reconcile_vintage_classes``) is then
   re-checked: unscaled years from the committed family, scaled years from the
   pre-scale family estimated as committed / s with s the committed-vs-raw
   ratio of the non-CHP gas classes (validated on unscaled years). The fold
   test (SOCO-60): EIA-930 gas minus the EIA-923 gas FULL of member plants,
   against the fold F the deflation subtracts.
   Model side (an arm): each covered plant's grid MW scaled by
   (1 - m)/(1 - d) at its own solved utilisation, walked down the solved stack
   at or below the hour's marginal offer (the w3d walk).
b) COMMITMENT. Per CHP plant with CEMS output: CAMPD online share and starts
   vs the keeper's (online = > 5 % of series max). Static release of
   ``chp_startup_covered``: committed-tranche headroom in hours its econ-low
   tranche is at cap and the committed offer sits > $0.5 above it, walked down
   the stack (the w3f reach). Bands read from the ``unit_id`` suffix.
c) HOLDOUT. The chp=Y rows of the injected residual classes (biomass, OTHER)
   in the member-plant EIA-923 frame, against EIA-930 OTH.

Output: results/phase0/governance/_closeout_chp_transfer_census.json
Usage: .venv/bin/python scripts/probes/_closeout_chp_transfer_census.py [--isos ...] [--no-campd]
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO), str(REPO / "scripts")]

import scripts.run_calibration_full as rcf  # noqa: E402
from market_sim.data.chp import chp_btm_pct, measured_chp_btm_pct_for_iso  # noqa: E402
from scripts.lib import benchmark_semantics as bs  # noqa: E402

OUT = REPO / "results/phase0/governance/_closeout_chp_transfer_census.json"
BENCH = REPO / "frontend/data/backcast/bench"
DISP = REPO / "data/raw/eia-923-disposition/eia923_disposition_2019_2025.csv"
GEN = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
KEEPER = {
    "ERCOT": "closeout_ercot_l1_span",
    "PJM": "closeout_pjm_nuc_full_span",
    "SPP": "closeout_spp_nuc_span",
    "SOCO": "closeout_soco_3_span",
    "NWPP": "nwppnext27_span",
    "NYISO": "w0_nyiso_span",
    "NEISO": "w0_neiso_span",
}
CHP = ("CC_CHP", "CT_CHP", "ST_CHP")
NO_WALK = ("nuclear", "hydro")
POOL = (2022, 2023, 2024)
YEARS = range(2019, 2026)


def measured_shares(disp: pd.DataFrame) -> tuple[dict, dict]:
    """Pooled CY2022-24 and same-year Schedules 6/7 BTM share per plant (0-1)."""
    d = disp.copy()
    d["net"] = d.gross_mwh - d.station_use_mwh
    d["grid"] = d.sales_for_resale_mwh + d.tolling_mwh + d.outgoing_mwh
    p = d[d.year.isin(POOL)].groupby("plant_id")[["net", "grid"]].sum()
    p = p[p.net > 0]
    pooled = (1.0 - p.grid / p.net).clip(0, 1).to_dict()
    y = d[d.net > 0].set_index(["plant_id", "year"])
    same = (1.0 - y.grid / y.net).clip(0, 1).to_dict()
    return pooled, same


def bench(iso: str, y: int) -> dict | None:
    """The committed bench part for (iso, year), or None."""
    f = BENCH / iso / f"{y}.json.gz"
    return json.load(gzip.open(f))["bench"] if f.exists() else None


def family(cf: dict, e930: dict) -> tuple[list[str], float, float]:
    """Reconcile family members, committed family total, raw 930 target."""
    fam = [*bs.GAS_GROUPS, *bs.COAL_GROUPS]
    tgt = float(e930.get("gas", 0.0)) + float(e930.get("coal", 0.0))
    if e930.get("oil") is not None:
        fam += list(bs.OIL_GROUPS)
        tgt += float(e930["oil"])
    return fam, sum(cf.get(g, 0.0) for g in fam), tgt


def census(iso: str, y: int, gen: pd.DataFrame, pooled: dict, same: dict) -> dict:
    """Part (a) bench side + part (c) for one ISO-year."""
    b = bench(iso, y)
    cf, e930 = b["classFull"], b["e930"]
    f = rcf._eia923_frame(y, gen, iso)
    fh = rcf._eia923_frame(y, gen, iso, mustrun_chp_btm_holdout=True)
    ctot = f.groupby(["plant_id", "klass"]).annual_mwh.sum()
    bench_meas = measured_chp_btm_pct_for_iso(iso)
    rows = []
    for code, p in b["plants"].items():
        grp = p.get("group")
        if grp not in CHP:
            continue
        pid = int(str(code).split(":")[0])
        e = float(ctot.get((pid, grp), 0.0))
        # the bench subtrahend's own share: an ISO's measured artifact where it
        # exists (NYISO Gold Book, nyiso-149), else the sector default
        dflt = bench_meas.get(pid, chp_btm_pct(pid, grp, iso=iso)) / 100.0
        m = pooled.get(pid)
        rows.append(
            {
                "plant": pid,
                "name": p.get("name"),
                "group": grp,
                "netgen_twh": e / 1e6,
                "default": dflt,
                "measured": m,
                "measured_same_year": same.get((pid, y)),
                "dE_twh": (e * (dflt - m) / 1e6) if m is not None else 0.0,
            }
        )
    df = pd.DataFrame(rows)
    by = df.groupby("group").agg(netgen=("netgen_twh", "sum"), dE=("dE_twh", "sum"))
    cov = df[df.measured.notna()]
    fam, cur, raw = family(cf, e930)
    F = bs.gas_foldin_deflation(cf, e930, iso)
    tgt = raw - F
    fired = abs(cur - tgt) < 0.01
    # pre-scale family: the non-CHP gas classes against their raw 923 totals
    k923 = f.groupby("klass").annual_mwh.sum() / 1e6
    ref = [g for g in ("CC_REGULAR", "CT_PEAKER", "ST_GAS") if g in cf]
    s = sum(cf[g] for g in ref) / max(sum(float(k923.get(g, 0.0)) for g in ref), 1e-9)
    pre = cur / s if fired else cur
    dE = float(df.dE_twh.sum())
    lo, hi = bs.VINTAGE_RECONCILE_FRAC * tgt, tgt / bs.VINTAGE_RECONCILE_FRAC
    new = pre + dE
    new_fires = not (lo <= new <= hi)
    scale_new = tgt / new if new_fires else 1.0
    # fold test (SOCO-60): 930 gas vs 923 gas FULL of member plants
    full = float(f[f.klass.isin(bs.GAS_GROUPS)].annual_mwh.sum()) / 1e6
    # part (c): chp=Y host biomass/OTHER in the injected residual classes
    inj_k = rcf._INJECTED_MUSTRUN_CLASSES
    inj = f[f.klass.isin(inj_k)].groupby("klass").annual_mwh.sum()
    kept = fh[fh.klass.isin(inj_k)].groupby("klass").annual_mwh.sum()
    host = inj.sub(kept, fill_value=0.0)
    return {
        "plants_chp": int(len(df)),
        "plants_in_sched67": int(len(cov)),
        "netgen_twh": round(float(df.netgen_twh.sum()), 3),
        "netgen_twh_covered": round(float(cov.netgen_twh.sum()), 3),
        "btm_default_twh": round(float((df.netgen_twh * df["default"]).sum()), 3),
        "btm_measured_twh": round(
            float((df.netgen_twh * df.measured.fillna(df["default"])).sum()), 3
        ),
        "dE_bench_twh": round(dE, 3),
        "dE_by_group": {g: round(float(r.dE), 3) for g, r in by.iterrows()},
        "netgen_by_group": {g: round(float(r.netgen), 3) for g, r in by.iterrows()},
        "default_shares": sorted({round(v, 3) for v in df["default"]}),
        "top": cov.assign(a=cov.dE_twh.abs())
        .sort_values("a", ascending=False)
        .head(6)[
            [
                "plant",
                "name",
                "group",
                "netgen_twh",
                "default",
                "measured",
                "measured_same_year",
                "dE_twh",
            ]
        ]
        .round(3)
        .to_dict("records"),
        "reconcile": {
            "family_committed": round(cur, 3),
            "raw_930": round(raw, 3),
            "fold_F": round(F, 3),
            "target": round(tgt, 3),
            "fired_committed": fired,
            "s_est": round(s, 4),
            "family_pre_est": round(pre, 3),
            "ratio_pre": round(pre / tgt, 4),
            "family_new": round(new, 3),
            "ratio_new": round(new / tgt, 4),
            "fires_new": new_fires,
            "scale_new": round(scale_new, 4),
            "upper_margin_new_twh": round(hi - new, 3),
            "lower_margin_new_twh": round(new - lo, 3),
            "ratio_new_fold_refuted": round(new / raw, 4),
            "fires_new_fold_refuted": not (
                bs.VINTAGE_RECONCILE_FRAC * raw
                <= new
                <= raw / bs.VINTAGE_RECONCILE_FRAC
            ),
        },
        "fold_test": {
            "e930_gas": round(float(e930.get("gas", 0.0)), 2),
            "eia923_gas_full": round(full, 2),
            "gap_930_minus_923": round(float(e930.get("gas", 0.0)) - full, 2),
            "fold_F": round(F, 2),
        },
        "holdout": {
            "e930_other": e930.get("other"),
            "bench_OTHER": round(float(cf.get("OTHER", 0.0)), 3),
            "bench_biomass": round(float(cf.get("biomass", 0.0)), 3),
            "inj_total_twh": round(float(inj.sum()) / 1e6, 3),
            "inj_chpY_twh": round(float(host.sum()) / 1e6, 3),
            "inj_chpY_by_class": (host / 1e6).round(3).to_dict(),
        },
        "_shares": {
            (int(r.plant), r.group): (float(r["default"]), float(r.measured))
            for _, r in cov.iterrows()
        },
    }


def recheck(yrs: dict) -> None:
    """Re-check scaled years with the ISO's unscaled-year s as the reference.

    s (committed / raw 923 over the non-CHP gas classes) is below 1 even in an
    unscaled year (backfills, membership), so a scaled year's pre-scale family
    is committed x s_ref / s, s_ref the mean s over the ISO's unscaled years.
    """
    ref = [
        v["reconcile"]["s_est"]
        for v in yrs.values()
        if not v["reconcile"]["fired_committed"]
    ]
    s_ref = float(np.mean(ref)) if ref else 1.0
    lo_f = bs.VINTAGE_RECONCILE_FRAC
    for v in yrs.values():
        c = v["reconcile"]
        c["s_ref"] = round(s_ref, 4)
        if not c["fired_committed"]:
            continue
        pre = c["family_committed"] * s_ref / c["s_est"]
        new = pre + v["dE_bench_twh"]
        tgt, raw = c["target"], c["raw_930"]
        c.update(
            {
                "family_pre_est": round(pre, 3),
                "ratio_pre": round(pre / tgt, 4),
                "family_new": round(new, 3),
                "ratio_new": round(new / tgt, 4),
                "fires_new": not (lo_f * tgt <= new <= tgt / lo_f),
                "upper_margin_new_twh": round(tgt / lo_f - new, 3),
                "lower_margin_new_twh": round(new - lo_f * tgt, 3),
                "ratio_new_fold_refuted": round(new / raw, 4),
                "fires_new_fold_refuted": not (lo_f * raw <= new <= raw / lo_f),
            }
        )
        c["scale_new"] = round(tgt / new, 4) if c["fires_new"] else 1.0


def _walk(um: pd.DataFrame, add_h: pd.Series) -> dict:
    """Walk an hourly MW addition down the solved stack at or below marginal."""
    price = um[um.marginal == 1].groupby("hour").mc.max()
    w = um.assign(price=um.hour.map(price))
    w = w[
        ~w.plant_group.isin(CHP)
        & ~w.fuel.isin(NO_WALK)
        & (w.mw > 0)
        & (w.mc <= w.price + 1e-6)
    ].copy()
    w = w.sort_values(["hour", "mc"], ascending=[True, False])
    w["above"] = w.groupby("hour").mw.cumsum() - w.mw
    w["need"] = w.hour.map(add_h).fillna(0.0).clip(lower=0.0)
    w["cut"] = (w.need - w.above).clip(lower=0.0).clip(upper=w.mw)
    cls = (w.groupby("plant_group", observed=True).cut.sum() / 1e6).round(3)
    unabs = (
        add_h.clip(lower=0) - w.groupby("hour").cut.sum().reindex(add_h.index).fillna(0)
    ).sum() / 1e6
    return {
        "displaced_twh_by_class": {
            k: float(v) for k, v in cls.items() if abs(v) >= 0.005
        },
        "unabsorbed_twh": round(float(unabs), 3),
    }


def _load_um(iso: str, y: int) -> pd.DataFrame | None:
    """The keeper's committed unit_marginal sidecar for (iso, year)."""
    f = (
        REPO
        / "results/calibration"
        / KEEPER[iso]
        / "hourly"
        / f"unit_marginal_{y}.parquet"
    )
    if not f.exists():
        return None
    um = pd.read_parquet(
        f,
        columns=[
            "unit_id",
            "plant_code",
            "plant_group",
            "fuel",
            "hour",
            "mw",
            "cap_mw",
            "mc",
            "marginal",
        ],
    )
    for c in ("plant_group", "fuel", "unit_id"):
        um[c] = um[c].astype("category")
    for c in ("mw", "cap_mw", "mc"):
        um[c] = um[c].astype("float32")
    return um


def arm_reach(um: pd.DataFrame, shares: dict) -> dict:
    """Model-side static reach of the measured carve (w3d method)."""
    chp = um[um.plant_group.isin(CHP)].copy()
    f = np.array(
        [
            shares.get((int(p), g), (0.0, 0.0))
            for p, g in zip(chp.plant_code, chp.plant_group)
        ]
    )
    d, m = f[:, 0], f[:, 1]
    scale = np.where(d < 1.0, (d - m) / np.maximum(1.0 - d, 1e-9), 0.0)
    chp["add"] = chp.mw.to_numpy() * scale
    add_h = chp.groupby("hour").add.sum()
    out = {
        "model_add_twh": round(float(add_h.sum() / 1e6), 3),
        "model_add_by_group": (
            chp.groupby("plant_group", observed=True).add.sum() / 1e6
        )
        .round(3)
        .to_dict(),
        "model_chp_twh": (chp.groupby("plant_group", observed=True).mw.sum() / 1e6)
        .round(3)
        .to_dict(),
    }
    out.update(_walk(um, add_h))
    return out


def holdout_reach(um: pd.DataFrame, removed_twh: float) -> dict:
    """Static take-up of the holdout's removed injection (flat MW, up-walk).

    The holdout drops chp=Y host biomass/OTHER from the must-run injection, so
    the LP's residual demand rises by that energy. Static: each hour's added
    MW is met by the cheapest units with headroom (mw < cap), marginal unit
    first, nuclear/hydro excluded -- the mirror of the w3d down-walk.
    """
    add = removed_twh * 1e6 / 8760.0
    w = um[~um.fuel.isin(NO_WALK) & (um.cap_mw - um.mw > 1e-6)].copy()
    w["room"] = w.cap_mw - w.mw
    w = w.sort_values(["hour", "mc"])
    w["below"] = w.groupby("hour").room.cumsum() - w.room
    w["got"] = (add - w.below).clip(lower=0.0).clip(upper=w.room)
    cls = (w.groupby("plant_group", observed=True).got.sum() / 1e6).round(3)
    return {
        "removed_twh": round(removed_twh, 3),
        "taken_twh_by_class": {k: float(v) for k, v in cls.items() if abs(v) >= 0.005},
    }


def _runs(on: np.ndarray) -> int:
    """Number of True runs (starts) in a boolean series."""
    d = np.diff(np.concatenate([[0], on.astype(int), [0]]))
    return int((d == 1).sum())


def commitment(iso: str, y: int, um: pd.DataFrame, campd: pd.DataFrame | None) -> dict:
    """Part (b): CEMS vs keeper online/starts and the startup-covered release."""
    chp = um[um.plant_group.isin(CHP)].copy()
    chp["plant_group"] = chp.plant_group.astype(str)
    chp["band"] = chp.unit_id.astype(str).str.split("_").str[-1]
    out: dict = {"bands": sorted(chp.band.unique().tolist())[:12]}
    rows = []
    if campd is not None:
        for pid, u in chp.groupby("plant_code"):
            c = (
                campd[campd.plant_id == pid]
                .groupby("hour")
                .net_mw.sum()
                .reindex(range(8760), fill_value=0.0)
                .to_numpy()
            )
            if c.max() <= 0:
                continue
            on = c > 0.05 * c.max()
            g = (
                u.groupby("hour")
                .agg(mw=("mw", "sum"), cap=("cap_mw", "sum"))
                .reindex(range(8760), fill_value=0.0)
            )
            mon = (g.mw > 0.05 * max(g.cap.max(), 1e-9)).to_numpy()
            rows.append(
                {
                    "plant": int(pid),
                    "group": str(u.plant_group.iloc[0]),
                    "cems_twh": c.sum() / 1e6,
                    "model_twh": float(g.mw.sum()) / 1e6,
                    "cems_on": float(on.mean()),
                    "cems_starts": _runs(on),
                    "model_on": float(mon.mean()),
                    "model_starts": _runs(mon),
                }
            )
    if rows:
        df = pd.DataFrame(rows)
        wt = df.cems_twh / df.cems_twh.sum()
        out["census"] = {
            "plants": len(df),
            "cems_twh": round(float(df.cems_twh.sum()), 3),
            "model_twh_same_plants": round(float(df.model_twh.sum()), 3),
            "cems_on_wmean": round(float((df.cems_on * wt).sum()), 3),
            "model_on_wmean": round(float((df.model_on * wt).sum()), 3),
            "cems_starts_median": float(df.cems_starts.median()),
            "model_starts_median": float(df.model_starts.median()),
        }
    com = chp[chp.band == "committed"].set_index(["plant_code", "hour"])
    lo = (
        chp[chp.band.isin(["econlo", "econ"])]
        .groupby(["plant_code", "hour"])[["mw", "cap_mw", "mc"]]
        .agg({"mw": "sum", "cap_mw": "sum", "mc": "min"})
        .add_suffix("_lo")
    )
    if com.empty or lo.empty:
        out["release"] = {
            "gain_twh": 0.0,
            "note": "no committed/econ-low CHP band pair",
        }
        return out
    j = com.join(lo, how="inner")
    bind = (
        (j.mw_lo >= 0.98 * j.cap_mw_lo)
        & (j.mw < 0.98 * j.cap_mw)
        & (j.mc > j.mc_lo + 0.5)
    )
    add = (j.cap_mw - j.mw) * bind
    add_h = add.groupby(level="hour").sum()
    inv = j.mc - j.mc_lo
    rel = {
        "gain_twh": round(float(add.sum() / 1e6), 3),
        "gain_by_group": (add.groupby(j.plant_group).sum() / 1e6).round(3).to_dict(),
        "markup_mean": round(float(inv.mean()), 2),
        "plants_inverted": int((inv.groupby(level=0).mean() > 0.5).sum()),
        "plants": int(inv.index.get_level_values(0).nunique()),
    }
    rel.update(_walk(um, add_h))
    out["release"] = rel
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="+", default=list(KEEPER))
    ap.add_argument("--no-campd", action="store_true")
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    gen = pd.read_parquet(GEN)
    pooled, same = measured_shares(pd.read_csv(DISP))
    out = a.out
    res = json.loads(out.read_text()) if out.exists() else {}
    pf = None if a.no_campd else rcf._parasitic_factor_map()
    for iso in a.isos:
        res.setdefault(iso, {})
        for y in a.years:
            if bench(iso, y) is None or str(y) in res[iso]:
                continue
            r = census(iso, y, gen, pooled, same)
            shares = r.pop("_shares")
            um = _load_um(iso, y)
            if um is not None:
                r["arm_reach"] = arm_reach(um, shares)
                r["holdout_reach"] = holdout_reach(um, r["holdout"]["inj_chpY_twh"])
                campd = None
                if not a.no_campd:
                    try:
                        campd = rcf._campd_hourly_frame(y, iso, pf, 8760)
                    except Exception as exc:  # noqa: BLE001 -- data absent is a finding
                        r["campd_error"] = repr(exc)[:200]
                r["commitment"] = commitment(iso, y, um, campd)
            res[iso][str(y)] = r
            print(
                iso,
                y,
                json.dumps({k: r[k] for k in ("dE_bench_twh", "dE_by_group")}),
                flush=True,
            )
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(res, indent=1, default=float))
        recheck(res[iso])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
