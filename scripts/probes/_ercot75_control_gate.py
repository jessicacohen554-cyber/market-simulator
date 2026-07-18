"""ERCOT-75 leg-0 derivation-bias gate + the RT offer-top measurement (rule-16 diagnostic; no solve).

THE PRE-REGISTERED selection-bias test for the chartered RT (SCED1) offer-top
correction to ``ercot_offer_surface_conditional`` (pre-registration written to
the session scratchpad BEFORE any control curve was fetched or read; full text
in the ERCOT-75 calibration-log entry): the ERCOT-74 tail-day SCED intake is
selection-biased toward event days, so a ladder derived from it alone would
date-pin the answer (rules 13/26). This probe measures whether the ONLINE
merchant-gas curve-top ladder differs tail-day vs control-day WITHIN the same
(net-load-percentile bin x loading-state) cell.

Control sample (deterministic, pre-registered): 46 delivery days, 2/month
2024-02..2025-12 (days closest to the 10th/20th), zero actual RT hub hours
> $200, not within +-1 day of a tail day, none of the 25 ERCOT-74 intake days
(``..._{2024,2025}_ercot75_control_days.parquet``, hod 11-22 CPT).

Measurement: per (resource, CST hour) SCED1 curve-top multiplier (max finite
SCED1 Curve-Price over the hour's intervals, clipped at HCAP $5,000, on
gas_day x class base_hr — the DAM artifact's normalizer) of ONLINE
(status ``ON*``) CC/CT resources, capacity(HSL)-weighted; cells = the
conditional surface's netload bins (0.80/0.90/0.97 edges, measured EIA-930
percentile) x diagnostic w-state thirds {loaded: w <= 1/3, mid, unloaded} on
the committed ERCOT-73 series. The thirds exist ONLY for this comparison; the
chartered build shape was threshold-free (continuous (1-w) weighting,
``loaded_ladders`` below).

THE GATE (pre-registered, one-sided): populated cell = >= 5 distinct resources
AND >= 40 resource-hours in BOTH samples; per class, rung ratios
R = tail/control at p50/p70/p90 over populated LOADED cells; CONFOUNDED iff
median R > 2.0.

MEASURED VERDICTS (2026-07-16, ERCOT-75 session — identical on SCED1 and SCED2):

* **CC: CLEAN** — median R = 1.32 over 12 populated loaded-cell comparisons
  (range 1.06-1.74). No event-anticipation confound.
* **CT: NO POPULATED CELLS** — the control sample has ZERO CT-loaded
  resource-hours in bins 1-3 (and the tail sample none in bin 0): the
  CT-loaded-in-tight-bins state occurs only on event days, so conditioning on
  it IS conditioning on the event. CT's loaded ladder is unverifiable against
  selection bias by construction.

THE ADJUDICATION THE GATE FED (the lane's terminal finding — full evidence in
the ERCOT-75 calibration-log entry and ``_ercot75_room_ladder.py``): the
gate-passing construction is PROVABLY INERT — the measured RT per-hour
curve-top quantile ladder sits BELOW the DAM mode-B ladder at every
sub-threshold rung, in every bin, in both state cells, on both samples (the
DAM ladder's per-resource max-over-3-years already prices above per-hour RT
tops), and the chartered composition ``dam + (1-w) x max(0, rt - dam)`` only
ever raises bids — so no missed hour can flip. The constructions strong
enough to carry the measured $965+ core-hour level (the CT marginal-room
tail) are exactly the ones this gate rejects as event-confounded. No build.

Usage::

    python scripts/probes/_ercot75_control_gate.py \
        [--tail PARQUET] [--control PARQUET ...] [--sced2] [--build-ladder]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

sys.path.insert(0, str(REPO / "scripts" / "data"))
from build_ercot_hsl import _prevailing_to_standard  # noqa: E402
from derive_dam_offer_hrmults import (  # noqa: E402
    HCAP_USD_MWH,
    NETLOAD_PCT_EDGES,
    PEAK_LADDER_QUANTILES,
    _wquantile,
)
from derive_ercot_dam_cleared_share import (  # noqa: E402
    _gas_day_series,
    _netload_pct,
)

DEFAULT_TAIL = (
    REPO
    / "data"
    / "raw"
    / "ercot"
    / "60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_2024_ercot74_tail_days.parquet"
)
DEFAULT_CONTROL = [
    REPO
    / "data"
    / "raw"
    / "ercot"
    / f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{y}_ercot75_control_days.parquet"
    for y in (2024, 2025)
]
DAM_SURFACE = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "offer_curve_dam_hrmults_condbinned.json"
)
STATE_JSON = (
    REPO / "data" / "raw" / "_validation-source" / "ercot_commitment_loading_state.json"
)

#: SCED Resource Type -> ladder class (the cleared-share artifact's
#: merchant-gas scope — the two classes with a measured ERCOT-73 w series).
CLASS_OF_RESTYPE: dict[str, str] = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT",
    "SCLE90": "CT",
}

#: Ladder class -> the model output group whose DAM-artifact base_hr
#: normalizes the multiplier.
OUTPUT_GROUP_OF: dict[str, str] = {"CC": "CC_REGULAR", "CT": "CT_PEAKER"}

# Pre-registered gate constants (diagnostic constructions, not solve tunables).
GATE_RUNGS = (0.50, 0.70, 0.90)
MIN_RESOURCES = 5
MIN_RESOURCE_HOURS = 40
CONFOUNDED_RATIO = 2.0
STATE_CELLS = (
    (0.0, 1 / 3, "loaded"),
    (1 / 3, 2 / 3, "mid"),
    (2 / 3, 1.0001, "unloaded"),
)
LADDER_QS = (0.10, 0.30, 0.50, 0.70, 0.90)

_META_COLS = [
    "SCED Time Stamp",
    "Repeated Hour Flag",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
]


def _hoy_nonleap(ts_cst: pd.Series) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (year, hoy, keep) mapping CST stamps onto the non-leap 8760 grid."""
    year = ts_cst.dt.year.to_numpy()
    keep = ~((ts_cst.dt.month == 2) & (ts_cst.dt.day == 29)).to_numpy()
    doy = ts_cst.dt.dayofyear.to_numpy().copy()
    leap = np.array([pd.Timestamp(f"{y}-12-31").dayofyear == 366 for y in year])
    doy = np.where(leap & (doy > 59), doy - 1, doy)
    hoy = (doy - 1) * 24 + ts_cst.dt.hour.to_numpy()
    return year, hoy, keep


def load_resource_hours(parquets: list[Path], fam: str = "SCED1") -> pd.DataFrame:
    """One row per (cls, resource, year, hoy): online SCED curve-top multiplier.

    The pre-registered measurement (identical for tail and control samples);
    see the module docstring. Resource-hour grain, NOT per-resource max over a
    bin: the state key makes the hour the conditioning unit, and a max over
    unequal day counts would bias the larger sample upward.
    """
    pr_cols = [f"{fam} Curve-Price{i}" for i in range(1, 36)]
    frames = []
    for parquet in parquets:
        df = pd.read_parquet(parquet, columns=_META_COLS + pr_cols)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        online = df["Telemetered Resource Status"].astype(str).str.upper()
        df = df[online.str.startswith("ON")].copy()

        ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
        ts_cst = _prevailing_to_standard(
            ts, df["Repeated Hour Flag"].fillna("N").astype(str).str.upper().eq("Y")
        )
        ok = ts_cst.notna().to_numpy()
        df, ts_cst = df[ok], ts_cst[ok]
        year, hoy, keep = _hoy_nonleap(ts_cst)
        df = df[keep].copy()
        df["year"], df["hoy"] = year[keep], hoy[keep]
        df["date"] = ts_cst[keep].dt.normalize().to_numpy()
        df["top_price"] = np.clip(
            np.nanmax(df[pr_cols].to_numpy(dtype=float), axis=1), None, HCAP_USD_MWH
        )
        df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
        frames.append(
            df.groupby(["cls", "Resource Name", "year", "hoy"], sort=False)
            .agg(
                top_price=("top_price", "max"),
                cap=("HSL", "median"),
                date=("date", "first"),
            )
            .reset_index()
        )
    rh = pd.concat(frames, ignore_index=True)

    dam = json.loads(DAM_SURFACE.read_text())
    base_hr = {c: float(dam[g]["base_hr"]) for c, g in OUTPUT_GROUP_OF.items()}
    gas_day = _gas_day_series()
    rh["gas"] = rh["date"].map(gas_day)
    rh = rh[np.isfinite(rh["gas"]) & (rh["gas"] > 0) & (rh["cap"] > 0)].copy()
    rh["mult"] = rh["top_price"] / (rh["gas"] * rh["cls"].map(base_hr))

    state = json.loads(STATE_JSON.read_text())
    edges = np.asarray(NETLOAD_PCT_EDGES, dtype=float)
    rh["bin"] = -1
    rh["w"] = np.nan
    for y in sorted(rh["year"].unique()):
        pct = _netload_pct(int(y))
        my = (rh["year"] == y).to_numpy()
        rh.loc[my, "bin"] = np.searchsorted(
            edges, pct[rh.loc[my, "hoy"].to_numpy(int)], side="right"
        )
        for cls in rh["cls"].unique():
            tbl = state.get(cls, {}).get("years", {}).get(str(int(y)))
            if tbl is None:
                continue
            w = np.asarray(tbl, dtype=float)
            m = my & (rh["cls"] == cls).to_numpy()
            rh.loc[m, "w"] = np.clip(w[rh.loc[m, "hoy"].to_numpy(int)], 0.0, 1.0)
    return rh[np.isfinite(rh["w"])].reset_index(drop=True)


def loaded_ladders(rh: pd.DataFrame) -> dict[str, list[list[list[float]]]]:
    """Per class: the capacity x (1-w)-weighted curve-top quantile ladder per bin.

    The build ladder the charter's mechanism WOULD have used (pre-registered
    shape — continuous state conditioning, no threshold in the solve path).
    Measured outcome: every rung sits below its DAM mode-B counterpart at the
    sub-threshold levels, so the only-ever-rise composition is provably inert
    (the reason no artifact was derived and no flag exists).
    """
    n_bins = len(NETLOAD_PCT_EDGES) + 1
    share = round(1.0 / len(PEAK_LADDER_QUANTILES), 3)
    out: dict[str, list[list[list[float]]]] = {}
    for cls, d in rh.groupby("cls"):
        ladders: list[list[list[float]]] = []
        for b in range(n_bins):
            db = d[d["bin"] == b]
            wgt = (db["cap"] * (1.0 - db["w"])).to_numpy(float)
            v = db["mult"].to_numpy(float)
            m = np.isfinite(v) & (wgt > 0)
            if m.sum() < 1 or wgt[m].sum() <= 0:
                ladders.append([])
                continue
            ladders.append(
                [
                    [share, round(_wquantile(v[m], wgt[m], q), 3)]
                    for q in PEAK_LADDER_QUANTILES
                ]
            )
        out[cls] = ladders
    return out


def cell_ladders(rh: pd.DataFrame) -> pd.DataFrame:
    """Ladder + counts per (cls, bin, state cell) at the diagnostic thirds."""
    rows = []
    for (cls, b), d in rh.groupby(["cls", "bin"]):
        for lo, hi, name in STATE_CELLS:
            dc = d[(d["w"] > lo) & (d["w"] <= hi)] if lo > 0 else d[d["w"] <= hi]
            row = {
                "cls": cls,
                "bin": int(b),
                "state": name,
                "n_res": dc["Resource Name"].nunique(),
                "n_rh": len(dc),
                "cap_gw": dc["cap"].sum() / 1e3,
                "gas_mean": dc["gas"].mean(),
            }
            v, w = dc["mult"].to_numpy(float), dc["cap"].to_numpy(float)
            m = np.isfinite(v) & (w > 0)
            for q in LADDER_QS:
                row[f"p{int(q * 100)}"] = (
                    _wquantile(v[m], w[m], q) if m.sum() else np.nan
                )
            rows.append(row)
    return pd.DataFrame(rows).set_index(["cls", "bin", "state"]).sort_index()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tail", type=Path, nargs="+", default=[DEFAULT_TAIL])
    ap.add_argument("--control", type=Path, nargs="+", default=DEFAULT_CONTROL)
    ap.add_argument(
        "--sced2", action="store_true", help="re-measure on the SCED2 curve family"
    )
    ap.add_argument(
        "--build-ladder",
        action="store_true",
        help="also print the pooled (1-w)-weighted ladder vs the DAM ladder "
        "(the inertness measurement)",
    )
    args = ap.parse_args()
    fam = "SCED2" if args.sced2 else "SCED1"

    samples = {}
    loaded = {}
    for name, paths in (("tail", args.tail), ("control", args.control)):
        rh = load_resource_hours(paths, fam=fam)
        print(
            f"{name}: {len(rh):,} resource-hours over {rh['date'].nunique()} days "
            f"({rh['Resource Name'].nunique()} resources), years "
            f"{sorted(int(y) for y in rh['year'].unique())}"
        )
        samples[name] = cell_ladders(rh)
        loaded[name] = rh

    if args.build_ladder:
        rh_all = pd.concat(loaded.values(), ignore_index=True)
        lads = loaded_ladders(rh_all)
        dam = json.loads(DAM_SURFACE.read_text())
        print("\n===== pooled (1-w)-weighted build ladder vs DAM mode-B ladder =====")
        for cls, group in OUTPUT_GROUP_OF.items():
            dam_lad = dam[group]["binned_ladder"]
            for b, lad in enumerate(lads.get(cls, [])):
                rt = [round(m, 2) for _, m in lad]
                dm = [round(m, 2) for _, m in dam_lad[b]]
                print(f"  {group} bin {b}: RT {rt} vs DAM {dm}")

    tail, ctrl = samples["tail"], samples["control"]
    print(f"\n===== per-cell ladders ({fam}; mult on gas x base_hr) =====")
    print(
        f"{'cls':>3} {'bin':>3} {'state':>8} | "
        f"{'n_res T/C':>10} {'n_rh T/C':>12} | "
        + " ".join(f"{'p' + str(int(q * 100)) + ' T/C':>14}" for q in LADDER_QS)
    )
    for key in sorted(set(tail.index) | set(ctrl.index)):
        t = tail.loc[key] if key in tail.index else None
        c = ctrl.loc[key] if key in ctrl.index else None
        f = lambda r, col: (
            f"{r[col]:.2f}" if r is not None and np.isfinite(r[col]) else "--"
        )  # noqa: E731
        fi = lambda r, col: f"{int(r[col])}" if r is not None else "--"  # noqa: E731
        print(
            f"{key[0]:>3} {key[1]:>3} {key[2]:>8} | "
            f"{fi(t, 'n_res'):>4}/{fi(c, 'n_res'):<5} {fi(t, 'n_rh'):>6}/{fi(c, 'n_rh'):<6} | "
            + " ".join(
                f"{f(t, 'p' + str(int(q * 100))):>6}/{f(c, 'p' + str(int(q * 100))):<7}"
                for q in LADDER_QS
            )
        )

    print(
        "\n===== THE GATE (pre-registered): loaded-cell rung ratios tail/control ====="
    )
    verdicts = {}
    for cls in sorted({k[0] for k in tail.index}):
        ratios = []
        for b in range(len(NETLOAD_PCT_EDGES) + 1):
            key = (cls, b, "loaded")
            if key not in tail.index or key not in ctrl.index:
                continue
            t, c = tail.loc[key], ctrl.loc[key]
            if (
                min(t["n_res"], c["n_res"]) < MIN_RESOURCES
                or min(t["n_rh"], c["n_rh"]) < MIN_RESOURCE_HOURS
            ):
                print(f"  {cls} bin {b}: NOT populated (below pre-registered counts)")
                continue
            for q in GATE_RUNGS:
                col = f"p{int(q * 100)}"
                if np.isfinite(t[col]) and np.isfinite(c[col]) and c[col] > 0:
                    r = t[col] / c[col]
                    ratios.append(r)
                    print(
                        f"  {cls} bin {b} {col}: {t[col]:.2f} / {c[col]:.2f} = {r:.2f}"
                    )
        med = float(np.median(ratios)) if ratios else np.nan
        verdict = (
            "NO POPULATED CELLS"
            if not ratios
            else ("CONFOUNDED" if med > CONFOUNDED_RATIO else "CLEAN")
        )
        verdicts[cls] = verdict
        print(
            f"  {cls}: median R = {med:.2f} over {len(ratios)} comparisons -> {verdict}"
        )

    print("\n===== non-gating: mid/unloaded-cell median ratios =====")
    for state in ("mid", "unloaded"):
        for cls in sorted({k[0] for k in tail.index}):
            ratios = []
            for b in range(len(NETLOAD_PCT_EDGES) + 1):
                key = (cls, b, state)
                if key not in tail.index or key not in ctrl.index:
                    continue
                t, c = tail.loc[key], ctrl.loc[key]
                if (
                    min(t["n_res"], c["n_res"]) < MIN_RESOURCES
                    or min(t["n_rh"], c["n_rh"]) < MIN_RESOURCE_HOURS
                ):
                    continue
                for q in GATE_RUNGS:
                    col = f"p{int(q * 100)}"
                    if np.isfinite(t[col]) and np.isfinite(c[col]) and c[col] > 0:
                        ratios.append(t[col] / c[col])
            if ratios:
                print(
                    f"  {cls} {state}: median R = {np.median(ratios):.2f} (n={len(ratios)})"
                )

    print(f"\nGATE VERDICTS: {verdicts}")


if __name__ == "__main__":
    main()
