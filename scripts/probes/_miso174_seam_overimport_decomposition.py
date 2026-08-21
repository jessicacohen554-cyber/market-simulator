"""miso-174 Phase 0 — decompose MISO's +1.33 GW scarce-hour over-import by seam.

READ-ONLY. **No LP is solved and nothing here re-enters a solve** (rule 13
``[R-MEASURED]``): every number is a measurement of committed artifacts against
measured actuals, written to a JSON record for the finding.

The object (miso-166/167 §2d, standing OPEN ever since): in the summer hours
MISO's own RT market priced above $200 the model carries **+1.33 GW** more net
interchange than EIA-930 measures (2023 +1.76, 2024 +1.01) — phantom outside
energy arriving exactly when MISO was tight. The named candidate lever is the
matrix cell ``measured_interface_limits`` (MISO ``U``).

Stages:
  1 object    — reproduce the aggregate defect on the CURRENT keeper
                (``miso173_layupmask``), annual / summer / scarce sets, 3 years.
  2 measured  — per-seam measured net import (EIA-930 BA-to-BA DIBA product,
                pooled by ``MISO_SEAM_DIBA``) in the same hour sets, with the
                hour-key alignment SOLVED against the BALANCE ``TI`` series
                rather than assumed.
  3 model     — per-seam model net flow from the priced-seam pseudo-generators
                (``*_refimp_<seam>#k`` / ``*_refexp_<seam>#k``). The only MISO
                bundle carrying ``unit_hourly`` is ``miso169_gated_A``; its
                aggregate drift vs the current keeper is measured, not assumed.
  4 binding   — THE PRE-CHECK. Rebuild the ARMED p90 (month x hour-of-day)
                deliverability envelope with the PRODUCTION loader
                (``measured_seam_import_envelope``) and measure, per seam and
                hour set: model flow vs cap vs measured flow, the at-cap share,
                and the headroom a tighter measured limit would have to cross
                before it could move anything.
  5 attrib    — where the +1.33 GW actually sits: seam x direction attribution
                of the model-minus-measured gap, and the share of it that any
                IMPORT-side ceiling could reach at all.

Hour key: the model's chronological non-leap 8760 CST calendar (the key
``scripts/data/derive_miso_hub_lmp.py`` writes the validation series on), so
model and actual are hour-for-hour comparable with no re-alignment. The DIBA
product's own ``local_time`` key is resolved to that calendar in stage 2 by
maximising correlation against the independently-keyed BALANCE ``TI`` series.

Run:  python3 scripts/probes/_miso174_seam_overimport_decomposition.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE  # noqa: E402
from market_sim.config.interchange_config import MISO_SEAM_DIBA  # noqa: E402
from market_sim.data.eia930 import measured_seam_import_envelope  # noqa: E402

CAL = ROOT / "results" / "calibration"
KEEPER = CAL / "miso173_layupmask" / "hourly"          # current keeper (no unit_hourly)
UNITBUNDLE = CAL / "miso169_gated_A" / "hourly"        # only MISO bundle with unit_hourly
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
E930_REGION = ROOT / "data" / "raw" / "MISO_region.parquet"
E930_DIBA = ROOT / "data" / "raw" / "eia-930-interchange" / "MISO interchange hourly.parquet"
OUT = CAL / "_miso174_seam_overimport_decomposition.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30 inclusive
SCARCE_RT = 200.0   # miso-167 §1: a scarcity hour is one MISO's RT market priced above this
FORESEEN_DA = 150.0  # miso-167 §5 DA-foreseen line
TOPN = 47           # the FINDING-miso167 §1 / FINDING-miso170 §7 top-load scarce set


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------
def model_system(bundle: Path, year: int) -> pd.DataFrame:
    """Load-weighted P1 system price, total demand and slack per hour."""
    d = pd.read_parquet(bundle / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    d["pw"] = d["price"] * d["demand"]
    g = d.groupby("hour").agg(
        pw=("pw", "sum"), demand=("demand", "sum"), slack=("slack", "sum")
    )
    g["price"] = g["pw"] / g["demand"]
    return g.drop(columns="pw").reset_index()


def model_net_import(bundle: Path, year: int) -> pd.Series:
    """P1 net interchange per hour (MW) = the signed ``import`` class total.

    The class pools the priced seam's positive-output import tranches and its
    negative-output export sinks, so it is NET, directly comparable to -TI.
    """
    cls = pd.read_parquet(bundle / f"class_hourly_{year}.parquet")
    cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
    return cls.groupby("hour")["mw"].sum().reindex(range(HOURS), fill_value=0.0)


def actual_lmp(year: int) -> pd.DataFrame:
    """MISO's measured RT and DA hub LMP for ``year``, on the model hour key."""
    a = pd.read_parquet(ACTUAL)
    return a[a["year"] == year][["hour", "rt", "da"]].reset_index(drop=True)


def e930_balance(year: int) -> pd.DataFrame:
    """EIA-930 MISO demand (D) and total interchange (TI) on the CST hour key."""
    d = pd.read_parquet(E930_REGION)
    d = d[d["type"].isin(["D", "TI"])].copy()
    d["cst"] = d["period"] - pd.Timedelta(hours=6)
    d = d[d["cst"].dt.year == year]
    d = d[~((d["cst"].dt.month == 2) & (d["cst"].dt.day == 29))]
    w = d.pivot_table(index="cst", columns="type", values="value_mwh", aggfunc="first").sort_index()
    w["hour"] = np.arange(len(w))
    return w.reset_index()[["hour", "D", "TI"]]


def diba_wide(year: int, shift_h: int) -> pd.DataFrame:
    """Measured per-DIBA net import (MW, + = MISO imports) on the model hour key.

    ``shift_h`` converts the file's ``local_time`` stamp to the model's CST
    hour-of-year; stage 2 solves for it rather than assuming a convention.
    EIA sign is + when MISO EXPORTS, so net import is the negation.

    The hour key is the model's FIXED NON-LEAP 8760 clock: Feb 29 is dropped and
    every later day shifts back one, so a leap year maps onto the same 8760
    positions as a common year. (Computing elapsed hours from Jan 1 instead
    leaves a leap year's Mar-Dec 24 hours late — a bug that shows up as 2024
    alone failing to reconcile against the BALANCE ``TI`` series.)
    """
    d = pd.read_parquet(E930_DIBA).copy()
    ts = pd.DatetimeIndex(d["local_time"]) + pd.Timedelta(hours=shift_h)
    keep = (ts.year == year) & ~((ts.month == 2) & (ts.day == 29))
    d = d[keep]
    ts = ts[keep]
    doy = ts.dayofyear.to_numpy()
    leap = bool(pd.Timestamp(f"{year}-12-31").dayofyear == 366)
    if leap:
        doy = np.where(doy > 60, doy - 1, doy)  # Feb 29 is day-of-year 60
    d = d.assign(hour=(doy - 1) * 24 + ts.hour.to_numpy())
    d = d[(d["hour"] >= 0) & (d["hour"] < HOURS)]
    w = d.pivot_table(index="hour", columns="diba", values="mw", aggfunc="first")
    return (-w).reindex(range(HOURS))  # net import


def model_seam_flows(year: int) -> pd.DataFrame:
    """Per-seam model net flow (MW, + = import) from the priced-seam rows."""
    d = pd.read_parquet(
        UNITBUNDLE / f"unit_hourly_{year}.parquet", columns=["pass", "unit_id", "fuel", "hour", "mw"]
    )
    d = d[(d["pass"] == "P1") & (d["fuel"].astype(str) == "import")]
    uid = d["unit_id"].astype(str)
    seam = uid.str.extract(r"_ref(?:imp|exp)_([A-Za-z]+)#", expand=False)
    side = np.where(uid.str.contains("_refimp_"), "imp", "exp")
    work = pd.DataFrame({"seam": seam.to_numpy(), "side": side, "hour": d["hour"].to_numpy(),
                         "mw": d["mw"].to_numpy()})
    net = work.pivot_table(index="hour", columns="seam", values="mw", aggfunc="sum")
    by_side = work.pivot_table(index="hour", columns=["seam", "side"], values="mw", aggfunc="sum")
    net = net.reindex(range(HOURS)).fillna(0.0)
    by_side = by_side.reindex(range(HOURS)).fillna(0.0)
    return net, by_side


# --------------------------------------------------------------------------
# hour sets
# --------------------------------------------------------------------------
def hour_sets(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """The four scored hour sets, as boolean masks over the 8760 clock."""
    su = (df["hour"] >= SUMMER[0]) & (df["hour"] < SUMMER[1])
    scarce = su & (df["rt"] > SCARCE_RT)
    top = np.zeros(len(df), dtype=bool)
    idx = df.loc[su].nlargest(TOPN, "demand").index
    top[idx] = True
    return {
        "annual": np.ones(len(df), dtype=bool),
        "summer": su.to_numpy(),
        "summer_scarce_rt200": scarce.to_numpy(),
        "summer_top47_load": top,
        "scarce_da_foreseen": (scarce & (df["da"] > FORESEEN_DA)).to_numpy(),
        "scarce_rt_only": (scarce & (df["da"] <= FORESEEN_DA)).to_numpy(),
    }


def _mean(a: np.ndarray, m: np.ndarray) -> float:
    return float(np.nanmean(a[m])) if m.sum() else float("nan")


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------
def stage1_object(frames: dict[int, pd.DataFrame]) -> dict:
    """Reproduce the aggregate over-import on the CURRENT keeper."""
    out: dict = {}
    for y, df in frames.items():
        sets = hour_sets(df)
        row: dict = {}
        for name, m in sets.items():
            row[name] = {
                "n": int(m.sum()),
                "model_net_import_gw": _mean(df["model_net"].to_numpy(), m) / 1000,
                "e930_net_import_gw": _mean(-df["TI"].to_numpy(), m) / 1000,
                "over_import_gw": _mean(df["model_net"].to_numpy() + df["TI"].to_numpy(), m) / 1000,
                "model_price": _mean(df["price"].to_numpy(), m),
                "actual_rt": _mean(df["rt"].to_numpy(), m),
                "model_demand_gw": _mean(df["demand"].to_numpy(), m) / 1000,
                "e930_demand_gw": _mean(df["D"].to_numpy(), m) / 1000,
            }
        out[str(y)] = row
    return out


def stage2_alignment_and_measured(frames: dict[int, pd.DataFrame]) -> tuple[dict, dict]:
    """Solve the DIBA hour key, then decompose the MEASURED side by seam."""
    # --- alignment: correlate DIBA-sum net import against BALANCE -TI ---
    align: dict = {}
    best_shift = None
    best_score = -np.inf
    for shift in range(-3, 4):
        scores = []
        for y, df in frames.items():
            w = diba_wide(y, shift)
            tot = w.sum(axis=1, min_count=1).to_numpy()
            ref = -df["TI"].to_numpy()
            ok = np.isfinite(tot) & np.isfinite(ref)
            if ok.sum() > 1000:
                scores.append(float(np.corrcoef(tot[ok], ref[ok])[0, 1]))
        s = float(np.mean(scores)) if scores else float("nan")
        align[str(shift)] = {"mean_r": s, "per_year_r": scores}
        if np.isfinite(s) and s > best_score:
            best_score, best_shift = s, shift
    align["chosen_shift_h"] = best_shift
    align["chosen_mean_r"] = best_score

    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    measured: dict = {}
    for y, df in frames.items():
        w = diba_wide(y, best_shift)
        sets = hour_sets(df)
        per_seam = {}
        for seam in MISO_SEAM_DIBA:
            cols = [c for c in w.columns if diba_to_seam.get(str(c)) == seam]
            per_seam[seam] = w[cols].sum(axis=1, min_count=1).to_numpy() if cols else np.full(HOURS, np.nan)
        unmapped = [c for c in w.columns if str(c) not in diba_to_seam]
        per_seam["_unmapped"] = (
            w[unmapped].sum(axis=1, min_count=1).to_numpy() if unmapped else np.zeros(HOURS)
        )
        row: dict = {"unmapped_dibas": [str(c) for c in unmapped],
                     "dibas_present": [str(c) for c in w.columns]}
        for name, m in sets.items():
            row[name] = {
                "n": int(m.sum()),
                **{f"{s}_gw": _mean(v, m) / 1000 for s, v in per_seam.items()},
                "diba_total_gw": _mean(
                    np.nansum(np.vstack(list(per_seam.values())), axis=0), m
                ) / 1000,
                "balance_ti_net_import_gw": _mean(-df["TI"].to_numpy(), m) / 1000,
            }
        measured[str(y)] = row
    return align, measured


def stage3_model_seams(frames: dict[int, pd.DataFrame]) -> dict:
    """Per-seam MODEL flow, plus the vintage drift of the unit_hourly bundle."""
    out: dict = {}
    for y, df in frames.items():
        net, by_side = model_seam_flows(y)
        proxy_agg = net.sum(axis=1).to_numpy()
        keeper_agg = df["model_net"].to_numpy()
        sets = hour_sets(df)
        row: dict = {
            "vintage_note": (
                "per-seam split read from miso169_gated_A (the only MISO bundle "
                "carrying unit_hourly); the current keeper miso173_layupmask "
                "commits no unit_hourly. Drift below is measured, not assumed."
            ),
            "drift_vs_keeper": {
                name: {
                    "proxy_gw": _mean(proxy_agg, m) / 1000,
                    "keeper_gw": _mean(keeper_agg, m) / 1000,
                    "drift_gw": _mean(proxy_agg - keeper_agg, m) / 1000,
                    "max_abs_drift_mw": float(np.nanmax(np.abs((proxy_agg - keeper_agg)[m])))
                    if m.sum() else float("nan"),
                }
                for name, m in sets.items()
            },
        }
        for name, m in sets.items():
            row[name] = {
                "n": int(m.sum()),
                **{f"{s}_gw": _mean(net[s].to_numpy(), m) / 1000 for s in net.columns},
                **{
                    f"{s}_{side}_gw": _mean(by_side[(s, side)].to_numpy(), m) / 1000
                    for (s, side) in by_side.columns
                },
                "total_gw": _mean(proxy_agg, m) / 1000,
            }
        out[str(y)] = row
    return out


def stage4_binding(frames: dict[int, pd.DataFrame]) -> dict:
    """THE PRE-CHECK: is the armed p90 envelope what holds the scarce-hour import?"""
    out: dict = {}
    for y, df in frames.items():
        imp_env = measured_seam_import_envelope("MISO", y, HOURS, None, "import") or {}
        exp_env = measured_seam_import_envelope("MISO", y, HOURS, None, "export") or {}
        net, by_side = model_seam_flows(y)
        sets = hour_sets(df)
        row: dict = {"percentile": float(MISO_SEAM_FLOW_PERCENTILE), "seams": {}}
        for seam, cap in imp_env.items():
            if (seam, "imp") not in by_side.columns:
                continue
            gross_imp = by_side[(seam, "imp")].to_numpy()
            gross_exp = by_side[(seam, "exp")].to_numpy()
            netflow = net[seam].to_numpy()
            ecap = exp_env.get(seam, np.zeros(HOURS))
            seam_row: dict = {}
            for name, m in sets.items():
                if not m.sum():
                    continue
                head = cap[m] - gross_imp[m]
                seam_row[name] = {
                    "n": int(m.sum()),
                    "model_gross_import_gw": float(np.mean(gross_imp[m])) / 1000,
                    "model_gross_export_gw": float(np.mean(gross_exp[m])) / 1000,
                    "model_net_gw": float(np.mean(netflow[m])) / 1000,
                    "import_cap_gw": float(np.mean(cap[m])) / 1000,
                    "export_cap_gw": float(np.mean(ecap[m])) / 1000,
                    "headroom_gw": float(np.mean(head)) / 1000,
                    # "at cap" = within 1 % of the seam's own hourly ceiling
                    "at_import_cap_share": float(np.mean(head <= 0.01 * np.maximum(cap[m], 1.0))),
                    "import_cap_binding_share": float(np.mean(head <= 1.0)),
                }
            row["seams"][seam] = seam_row
        out[str(y)] = row
    return out


def stage5_attribution(frames: dict[int, pd.DataFrame], align_shift: int) -> dict:
    """Seam x direction attribution of the model-minus-measured net-flow gap."""
    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    out: dict = {}
    for y, df in frames.items():
        w = diba_wide(y, align_shift)
        net, by_side = model_seam_flows(y)
        sets = hour_sets(df)
        row: dict = {}
        for name, m in sets.items():
            if not m.sum():
                continue
            per_seam = {}
            for seam in MISO_SEAM_DIBA:
                cols = [c for c in w.columns if diba_to_seam.get(str(c)) == seam]
                meas = w[cols].sum(axis=1, min_count=1).to_numpy() if cols else np.full(HOURS, np.nan)
                mod = net[seam].to_numpy() if seam in net.columns else np.zeros(HOURS)
                gap = mod - meas
                per_seam[seam] = {
                    "model_gw": float(np.mean(mod[m])) / 1000,
                    "measured_gw": _mean(meas, m) / 1000,
                    "gap_gw": _mean(gap, m) / 1000,
                    "model_gross_import_gw": float(np.mean(by_side[(seam, "imp")].to_numpy()[m])) / 1000
                    if (seam, "imp") in by_side.columns else 0.0,
                    "model_gross_export_gw": float(np.mean(by_side[(seam, "exp")].to_numpy()[m])) / 1000
                    if (seam, "exp") in by_side.columns else 0.0,
                }
            unmapped = [c for c in w.columns if str(c) not in diba_to_seam]
            per_seam["_unmapped_measured_gw"] = (
                _mean(w[unmapped].sum(axis=1, min_count=1).to_numpy(), m) / 1000 if unmapped else 0.0
            )
            row[name] = {"n": int(m.sum()), "per_seam": per_seam}
        out[str(y)] = row
    return out


# --------------------------------------------------------------------------
def build_frames() -> dict[int, pd.DataFrame]:
    """Return one per-hour frame per year joining keeper output to measured actuals."""
    frames = {}
    for y in YEARS:
        df = model_system(KEEPER, y).merge(actual_lmp(y), on="hour").merge(
            e930_balance(y), on="hour", how="left"
        )
        df["model_net"] = model_net_import(KEEPER, y).to_numpy()
        frames[y] = df
    return frames


def main() -> None:
    """Run all five stages, write the JSON record and print the console summary."""
    frames = build_frames()
    stage1 = stage1_object(frames)
    align, measured = stage2_alignment_and_measured(frames)
    stage3 = stage3_model_seams(frames)
    stage4 = stage4_binding(frames)
    stage5 = stage5_attribution(frames, align["chosen_shift_h"])

    rec = {
        "session": "miso-174",
        "keeper_bundle": "miso173_layupmask",
        "unit_hourly_bundle": "miso169_gated_A",
        "scarce_definition": {"summer": "Jun 1 - Sep 30", "rt_threshold": SCARCE_RT,
                              "top_load_n": TOPN, "da_foreseen": FORESEEN_DA},
        "stage1_object": stage1,
        "stage2_alignment": align,
        "stage2_measured_by_seam": measured,
        "stage3_model_by_seam": stage3,
        "stage4_binding_precheck": stage4,
        "stage5_attribution": stage5,
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT}")

    # --- console summary ---
    print("\n== stage 1: the object, on the CURRENT keeper ==")
    for y in YEARS:
        s = stage1[str(y)]["summer_scarce_rt200"]
        print(f"  {y} scarce(RT>200,n={s['n']:3d})  model {s['model_net_import_gw']:+.2f} "
              f"e930 {s['e930_net_import_gw']:+.2f}  OVER-IMPORT {s['over_import_gw']:+.2f} GW")
    allgap = np.mean([stage1[str(y)]["summer_scarce_rt200"]["over_import_gw"] for y in YEARS])
    print(f"  3-yr mean over-import in scarce hours: {allgap:+.2f} GW")

    print(f"\n== stage 2: DIBA alignment shift = {align['chosen_shift_h']:+d} h "
          f"(mean r = {align['chosen_mean_r']:.4f}) ==")
    for y in YEARS:
        r = measured[str(y)]["summer_scarce_rt200"]
        print(f"  {y} measured by seam (GW net import): " + "  ".join(
            f"{k[:-3]} {v:+.2f}" for k, v in r.items() if k.endswith("_gw")))

    print("\n== stage 4: the pre-check — model import vs the ARMED p90 cap ==")
    for y in YEARS:
        print(f"  {y}")
        for seam, sr in stage4[str(y)]["seams"].items():
            b = sr.get("summer_scarce_rt200")
            if not b:
                continue
            print(f"    {seam:9s} gross_imp {b['model_gross_import_gw']:.2f}  "
                  f"cap {b['import_cap_gw']:.2f}  head {b['headroom_gw']:+.2f} GW  "
                  f"at-cap {b['at_import_cap_share']*100:5.1f}%  "
                  f"binding(<=1MW) {b['import_cap_binding_share']*100:5.1f}%")

    print("\n== stage 5: attribution of the gap (scarce hours) ==")
    for y in YEARS:
        r = stage5[str(y)]["summer_scarce_rt200"]["per_seam"]
        print(f"  {y}  " + "  ".join(
            f"{k} {v['gap_gw']:+.2f}" for k, v in r.items() if isinstance(v, dict)))


if __name__ == "__main__":
    main()
