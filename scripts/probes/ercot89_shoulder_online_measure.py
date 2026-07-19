"""ERCOT-89 measure-first probe: hour-level online capability in the shoulder
mid-band hours vs the model's class-day availability basis.

Charter step 1 of `docs/handoffs/ercot-shoulder-online-envelope-2026-07.md`
— MEASUREMENT ONLY, no apply seam, no mechanism, nothing here feeds the model.

The ERCOT-88 finding closed the offer-side enumeration for the $150-500
moderate-tightness band: both the ERCOT-86 online-spare wall and the ERCOT-88
offline fast-start pool are built and measured-faithful, and neither fills the
diffuse Apr/May/Jul/Oct/Dec band — the LP clears those hours on CHEAPER online
headroom. This probe measures where that headroom comes from, per covered
residual hour, from the NP3-965 60-Day SCED Gen Resource parquets already on
disk (the ERCOT-74/75/86 sample-day corpus — no new intake):

* **Measured side** — per (hour x merchant class CC/CT), the telemetered
  capability by status family: ON (dispatchable now), OFFQS/OFFNS (offline
  startable), plain OFF (offline, not intra-hour startable), OUT. The model's
  availability basis is the DAM-disclosure class-DAY only-OUT-is-out fraction
  (`ercot_thermal_dam_availability`, day-mean, flat within the day), so the
  day-mean non-OUT HSL *is* the model's capability level in MW terms — the
  overlay identity. The wedge `day-mean non-OUT − hour ON HSL` is capability
  the LP prices at base offers in that hour that the real system had offline.
* **Model side** — the ercot86-keeper replay's hourly demand-weighted system
  price (residual-hour identification: actual RT in [150, 500] and model
  < 150) and per-class dispatched MW (`dispatch/<year>_P1.parquet`), so the
  dispatch wedge (model class MW vs measured ON Base Point) separates
  "model over-dispatches the class" from "model misprices the margin".
* **Condition specificity** — the same statistics over bin-matched control
  hours (actual RT and model both < $150, same net-load bins) adjudicate
  whether the band hours are distinguishable by ON share at all: a mechanism
  needs a driver (rule 12), and if the ON share in band hours equals the
  same-net-load control share, hour-level commitment thinness has no
  conditional signature to regenerate from in a forecast (rule 13).

Provenance / admissibility (rule 13): every measured quantity is a telemetered
status or capability (HSL/HASL/Base Point); observed lambda and the model's
own price/dispatch enter ONLY as the adjudication reference. The per-hour ON
series itself is an operational OUTCOME — it may only ever be used to measure
a CONDITIONAL structure (ON share by net-load bin x season x hour block), never
pinned per-hour into a backcast (charter §6). Coverage is disclosed per bin,
never silently capped.

Usage::

    python scripts/probes/ercot89_shoulder_online_measure.py \
        [--years 2024 2025] \
        [--bundle-tpl results/calibration/_ercot89_measure_{year}] \
        [--out data/raw/_validation-source/ercot89_shoulder_online_measurement.json]
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

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HOURS,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _netload_pct,
)
from derive_ercot_sced_offer_wall import CLASS_OF_RESTYPE, SCED_DIR  # noqa: E402

DEFAULT_OUT = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot89_shoulder_online_measurement.json"
)
ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
DAM_AVAIL_CSV = REPO / "data" / "raw" / "ercot-thermal-dam-availability.csv"

_STD_TZ = "Etc/GMT+6"  # ERCOT fixed standard-time clock (derive_actual_lmp)

MID_BAND = (150.0, 500.0)  # the ERCOT-86/87/88 moderate-tightness band, $/MWh

# Telemetered status families (ERCOT Nodal Protocols §3.9.1 telemetry codes).
# ON* (ON/ONREG/ONOS/ONRUC/ONTEST/...) telemeter dispatchable-now; OFFQS is
# offline quick-start (SCED-startable within the operating hour); OFFNS is
# offline carrying a Non-Spin responsibility (startable via NSRS deployment);
# plain OFF (and any other OFF*) is offline and NOT intra-hour startable; OUT
# is the only family the model's DAM-availability overlay counts as
# unavailable (only-OUT-is-out — derive_ercot_thermal_dam_availability).
# Residual codes (STARTUP/SHUTDOWN/EMR/...) are reported as OTHER.
_FAMILIES = ("ON", "OFFQS", "OFFNS", "OFF", "OUT", "OTHER")

# Model dispatch-frame class names for the corpus's merchant scope
# (CLASS_OF_RESTYPE: CCGT90/CCLE90 -> CC, SCGT90/SCLE90 -> CT).
MODEL_KLASS = {"CC": "CC_REGULAR", "CT": "CT_PEAKER"}

_READ_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
    "HASL",
    "LSL",
    "Base Point",
]


def _load_year(year: int) -> tuple[pd.DataFrame, list[str]]:
    """ALL-status merchant gas SCED rows for ``year`` (statuses + capability)."""
    files = sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    )
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        frames.append(df[df["Resource Type"].isin(CLASS_OF_RESTYPE)].copy())
    if not frames:
        return pd.DataFrame(columns=_READ_COLS), []
    return pd.concat(frames, ignore_index=True), [p.name for p in files]


def _clock(df: pd.DataFrame) -> pd.DataFrame:
    """Attach hoy / date / class / status family on the fixed-CST clock."""
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    df = df.loc[np.asarray(ok)].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["_date"] = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)].to_numpy()
    df["_ts"] = pd.to_datetime(df["SCED Time Stamp"]).to_numpy()[np.asarray(ok)]
    df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
    stat = df["Telemetered Resource Status"].astype(str).str.strip()
    fam = np.full(len(df), "OTHER", dtype=object)
    fam[stat.str.startswith("ON").to_numpy()] = "ON"
    fam[(stat == "OFFQS").to_numpy()] = "OFFQS"
    fam[(stat == "OFFNS").to_numpy()] = "OFFNS"
    off_other = stat.str.startswith("OFF").to_numpy() & ~np.isin(
        fam, ("OFFQS", "OFFNS")
    )
    fam[off_other] = "OFF"
    fam[(stat == "OUT").to_numpy()] = "OUT"
    df["fam"] = fam
    return df


def _hourly_capability(df: pd.DataFrame) -> pd.DataFrame:
    """Interval-mean capability per (hoy, cls): HSL by family + ON BP/spare.

    Sums each SCED interval's HSL per (interval, cls, family), then averages
    the interval sums within the hour — the corpus convention (a resource
    appears once per interval).
    """
    g = df.groupby(["_ts", "hoy", "cls", "fam"], observed=True)
    per_iv = g.agg(
        hsl=("HSL", "sum"),
        bp=("Base Point", "sum"),
        n=("Resource Name", "nunique"),
    ).reset_index()
    hourly = (
        per_iv.groupby(["hoy", "cls", "fam"], observed=True)[["hsl", "bp", "n"]]
        .mean()
        .reset_index()
    )
    wide = hourly.pivot_table(
        index=["hoy", "cls"], columns="fam", values="hsl", fill_value=0.0
    ).reset_index()
    for f in _FAMILIES:
        if f not in wide.columns:
            wide[f] = 0.0
    on_bp = (
        hourly[hourly["fam"] == "ON"]
        .set_index(["hoy", "cls"])[["bp", "n"]]
        .rename(columns={"bp": "on_bp", "n": "on_n"})
    )
    wide = wide.join(on_bp, on=["hoy", "cls"]).fillna({"on_bp": 0.0, "on_n": 0.0})

    # ON-status spare above Base Point, HASL- and HSL-basis (interval-mean).
    on = df[df["fam"] == "ON"].copy()
    on["sp_hasl"] = np.maximum(
        on["HASL"].to_numpy(float) - on["Base Point"].to_numpy(float), 0.0
    )
    on["sp_hsl"] = np.maximum(
        on["HSL"].to_numpy(float) - on["Base Point"].to_numpy(float), 0.0
    )
    sp = (
        on.groupby(["_ts", "hoy", "cls"], observed=True)[["sp_hasl", "sp_hsl"]]
        .sum()
        .reset_index()
        .groupby(["hoy", "cls"], observed=True)[["sp_hasl", "sp_hsl"]]
        .mean()
    )
    wide = wide.join(sp, on=["hoy", "cls"]).fillna({"sp_hasl": 0.0, "sp_hsl": 0.0})

    wide["nonout"] = sum(wide[f] for f in ("ON", "OFFQS", "OFFNS", "OFF", "OTHER"))
    # Day-mean non-OUT HSL — the model's class-DAY availability basis in MW
    # terms (the ercot_thermal_dam_availability overlay identity: only-OUT-is-
    # out, day-mean, flat within the day).
    wide["day"] = wide["hoy"] // 24
    daymean = (
        wide.groupby(["day", "cls"], observed=True)["nonout"]
        .mean()
        .rename("day_nonout")
    )
    wide = wide.join(daymean, on=["day", "cls"])
    return wide


def _model_price(bundle: Path, year: int) -> np.ndarray | None:
    """Hourly demand-weighted P1 system price (the ERCOT-88 analyzer basis)."""
    path = bundle / "system.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    if df.empty:
        return None
    w = df["price"] * df["demand"]
    num = w.groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(HOURS)).to_numpy(float)


def _model_class_mw(bundle: Path, year: int) -> pd.DataFrame | None:
    """Hourly dispatched MW per corpus class from ``dispatch/<year>_P1.parquet``."""
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    if not path.exists():
        return None
    d = pd.read_parquet(path, columns=["pass", "klass", "hour", "mw"])
    if "pass" in d.columns:
        d = d[d["pass"].astype(str) == "P1"]
    out = {}
    for cls, mk in MODEL_KLASS.items():
        sub = d[d["klass"].astype(str) == mk]
        arr = np.zeros(HOURS)
        g = sub.groupby("hour")["mw"].sum()
        arr[g.index.to_numpy(int)] = g.to_numpy(float)
        out[cls] = arr
    return pd.DataFrame(out)


def _model_capability(
    class_mw: pd.DataFrame | None, dam: dict[str, np.ndarray]
) -> tuple[pd.DataFrame | None, dict[str, float]]:
    """Estimated model class capability per hour: ``cap_hat x day avail``.

    The bundle persists no availability, so the class capacity is inferred
    from the replay's own dispatch: ``cap_hat = max_t(mw(t) / avail_day(t))``
    over DAM-covered days — tight because the LP dispatches the full class
    capability in its scarcest hours. Disclosed as an estimate in the
    artifact; the day-flat shape is exact (the overlay broadcasts day means).
    """
    if class_mw is None:
        return None, {}
    out = {}
    caps: dict[str, float] = {}
    for cls, mk in MODEL_KLASS.items():
        av = dam.get(mk)
        if av is None:
            out[cls] = np.full(HOURS, np.nan)
            continue
        mw = class_mw[cls].to_numpy(float)
        ok = np.isfinite(av) & (av > 0.05)
        cap_hat = float(np.nanmax(mw[ok] / av[ok])) if ok.any() else np.nan
        caps[cls] = round(cap_hat, 1)
        out[cls] = cap_hat * av
    return pd.DataFrame(out), caps


EIA930_FUEL = REPO / "data" / "raw" / "ERCO_fueltype.parquet"


def _model_mix(bundle: Path, year: int) -> pd.DataFrame | None:
    """Hourly model MW per dispatch-frame class (all classes) + demand."""
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    if not path.exists():
        return None
    d = pd.read_parquet(path, columns=["pass", "klass", "hour", "mw"])
    if "pass" in d.columns:
        d = d[d["pass"].astype(str) == "P1"]
    piv = (
        d.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack("klass")
        .reindex(range(HOURS))
        .fillna(0.0)
    )
    sysdf = pd.read_parquet(bundle / "system.parquet")
    sysdf = sysdf[(sysdf["year"] == year) & (sysdf["pass"] == "P1")]
    piv["_demand"] = sysdf.groupby("hour")["demand"].sum().reindex(range(HOURS))
    return piv


def _actual_mix(year: int) -> pd.DataFrame | None:
    """Hourly EIA-930 actual MW by fuel type on the hoy clock."""
    if not EIA930_FUEL.exists():
        return None
    df = pd.read_parquet(EIA930_FUEL)
    std = pd.DatetimeIndex(df["period"]).tz_convert(_STD_TZ)
    ok = (std.year == year) & ~((std.month == 2) & (std.day == 29))
    df = df.loc[np.asarray(ok)].copy()
    stdo = std[np.asarray(ok)]
    df["hoy"] = _MONTH_START_HOUR[stdo.month - 1] + (stdo.day - 1) * 24 + stdo.hour
    return (
        df.groupby(["type_name", "hoy"], observed=True)["value_mwh"]
        .sum()
        .unstack("type_name")
        .reindex(range(HOURS))
    )


def _mix_summary(
    model_mix: pd.DataFrame | None,
    actual_mix: pd.DataFrame | None,
    mask: np.ndarray,
) -> dict:
    """Median model class MW and actual fuel MW over the masked hours."""
    out: dict = {}
    hours = np.flatnonzero(mask)
    if model_mix is not None:
        m = model_mix.iloc[hours]
        med = m.median()
        out["model"] = {
            str(k): round(float(v), 1)
            for k, v in med.sort_values(ascending=False).items()
            if abs(v) >= 50.0
        }
    if actual_mix is not None:
        a = actual_mix.iloc[hours]
        med = a.median()
        out["actual_eia930"] = {
            str(k): round(float(v), 1)
            for k, v in med.sort_values(ascending=False).items()
            if np.isfinite(v) and abs(v) >= 50.0
        }
    return out


def _dam_avail(year: int) -> dict[str, np.ndarray]:
    """Class-day DAM availability fraction on the hoy clock (NaN uncovered)."""
    if not DAM_AVAIL_CSV.exists():
        return {}
    df = pd.read_csv(DAM_AVAIL_CSV).rename(columns={"class": "klass"})
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == int(year)]
    out: dict[str, np.ndarray] = {}
    for r in df.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue
        lo = _MONTH_START_HOUR[mo - 1] + (dy - 1) * 24
        arr = out.setdefault(str(r.klass), np.full(HOURS, np.nan))
        arr[lo : lo + 24] = float(r.avail)
    return out


def _agg(rows: pd.DataFrame, cls: str) -> dict:
    """Median/mean summary of one class's per-hour records."""
    c = rows[rows["cls"] == cls]
    if c.empty:
        return {"n": 0}
    med = lambda k: round(float(c[k].median()), 1)  # noqa: E731
    return {
        "n": int(len(c)),
        "on_hsl_med": med("ON"),
        "on_share_med": round(float((c["ON"] / c["nonout"]).median()), 3),
        "on_spare_hasl_med": med("sp_hasl"),
        "on_spare_hsl_med": med("sp_hsl"),
        "offqs_ns_med": round(float((c["OFFQS"] + c["OFFNS"]).median()), 1),
        "off_plain_med": med("OFF"),
        "out_med": med("OUT"),
        "nonout_med": med("nonout"),
        "day_nonout_med": med("day_nonout"),
        "wedge_med": round(float((c["day_nonout"] - c["ON"]).median()), 1),
        "on_bp_med": med("on_bp"),
        "model_mw_med": (
            round(float(c["model_mw"].median()), 1)
            if c["model_mw"].notna().any()
            else None
        ),
        "model_cap_med": (
            round(float(c["model_cap"].median()), 1)
            if c["model_cap"].notna().any()
            else None
        ),
        "model_headroom_med": (
            round(float((c["model_cap"] - c["model_mw"]).median()), 1)
            if c["model_cap"].notna().any()
            else None
        ),
    }


def measure_year(year: int, bundle: Path, actual: pd.DataFrame) -> dict:
    """Measure the shoulder-hour online-capability wedge for one year."""
    df, files = _load_year(year)
    if df.empty:
        return {"source_files": files, "note": "no SCED sample days on disk"}
    df = _clock(df)
    cap = _hourly_capability(df)

    price_h = _model_price(bundle, year)
    class_mw = _model_class_mw(bundle, year)
    dam = _dam_avail(year)
    model_cap, cap_hat = _model_capability(class_mw, dam)
    model_mix = _model_mix(bundle, year)
    actual_mix = _actual_mix(year)

    act = actual[actual["year"] == year].set_index("hour")["rt"]
    rt = act.reindex(range(HOURS)).to_numpy(float)

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")

    covered_hoys = np.array(sorted(cap["hoy"].unique()), dtype=int)
    in_band = (rt >= MID_BAND[0]) & (rt <= MID_BAND[1])
    covered_mask = np.zeros(HOURS, dtype=bool)
    covered_mask[covered_hoys[covered_hoys < HOURS]] = True

    if price_h is not None:
        model_below = price_h < MID_BAND[0]
        model_in_band = (price_h >= MID_BAND[0]) & (price_h <= MID_BAND[1])
    else:
        model_below = np.ones(HOURS, dtype=bool)
        model_in_band = np.zeros(HOURS, dtype=bool)

    resid_mask = in_band & model_below & covered_mask  # un-formed band hours
    formed_mask = in_band & model_in_band & covered_mask
    control_mask = (rt < MID_BAND[0]) & (rt > 0) & model_below & covered_mask
    resid_bins = set(hour_bin[resid_mask].tolist())
    control_mask &= np.isin(hour_bin, list(resid_bins))  # bin-matched controls

    def _records(mask: np.ndarray) -> pd.DataFrame:
        hoys = np.flatnonzero(mask)
        rows = cap[cap["hoy"].isin(hoys)].copy()
        rows["lambda"] = rt[rows["hoy"].to_numpy(int)]
        rows["model_price"] = (
            price_h[rows["hoy"].to_numpy(int)] if price_h is not None else np.nan
        )
        rows["bin"] = hour_bin[rows["hoy"].to_numpy(int)]
        if class_mw is not None:
            rows["model_mw"] = [
                class_mw[c][h] for c, h in zip(rows["cls"], rows["hoy"].to_numpy(int))
            ]
            rows["model_cap"] = [
                model_cap[c][h] for c, h in zip(rows["cls"], rows["hoy"].to_numpy(int))
            ]
        else:
            rows["model_mw"] = np.nan
            rows["model_cap"] = np.nan
        return rows

    resid = _records(resid_mask)
    formed = _records(formed_mask)
    control = _records(control_mask)

    # Per-hour residual records (quotable evidence, one dict per hour x class).
    hours_out = []
    for hoy, g in resid.groupby("hoy"):
        rec = {
            "hoy": int(hoy),
            "hh": int(hoy) % 24,
            "lambda": round(float(rt[int(hoy)]), 1),
            "model_price": (
                round(float(price_h[int(hoy)]), 1) if price_h is not None else None
            ),
            "bin": int(hour_bin[int(hoy)]),
        }
        for _, r in g.iterrows():
            cls = r["cls"]
            rec[cls] = {
                "on_hsl": round(float(r["ON"]), 1),
                "on_bp": round(float(r["on_bp"]), 1),
                "on_spare_hasl": round(float(r["sp_hasl"]), 1),
                "offqs_ns": round(float(r["OFFQS"] + r["OFFNS"]), 1),
                "off_plain": round(float(r["OFF"]), 1),
                "out": round(float(r["OUT"]), 1),
                "nonout": round(float(r["nonout"]), 1),
                "day_nonout": round(float(r["day_nonout"]), 1),
                "model_mw": (
                    round(float(r["model_mw"]), 1)
                    if np.isfinite(r["model_mw"])
                    else None
                ),
                "model_cap": (
                    round(float(r["model_cap"]), 1)
                    if np.isfinite(r["model_cap"])
                    else None
                ),
            }
        hours_out.append(rec)

    # Bin-resolved ON-share comparison: residual vs bin-matched control.
    by_bin: dict[str, dict] = {}
    for cls in ("CC", "CT"):
        rows_r = resid[resid["cls"] == cls]
        rows_c = control[control["cls"] == cls]
        per = {}
        for b in sorted(resid_bins):
            rr = rows_r[rows_r["bin"] == b]
            cc = rows_c[rows_c["bin"] == b]
            per[str(b)] = {
                "resid_n": int(len(rr)),
                "control_n": int(len(cc)),
                "resid_on_share": (
                    round(float((rr["ON"] / rr["nonout"]).mean()), 3)
                    if len(rr)
                    else None
                ),
                "control_on_share": (
                    round(float((cc["ON"] / cc["nonout"]).mean()), 3)
                    if len(cc)
                    else None
                ),
                "resid_on_spare_hasl": (
                    round(float(rr["sp_hasl"].mean()), 1) if len(rr) else None
                ),
                "control_on_spare_hasl": (
                    round(float(cc["sp_hasl"].mean()), 1) if len(cc) else None
                ),
            }
        by_bin[cls] = per

    dam_cov = {
        k: round(float(np.nanmean(v[covered_mask & in_band])), 4)
        for k, v in dam.items()
        if np.isfinite(v[covered_mask & in_band]).any()
    }

    return {
        "source_files": files,
        "bundle": str(bundle),
        "model_side": price_h is not None,
        "n_band_hours_actual": int(in_band.sum()),
        "n_band_hours_covered": int((in_band & covered_mask).sum()),
        "n_residual_covered": int(resid_mask.sum()),
        "n_formed_covered": int(formed_mask.sum()),
        "n_control_covered": int(control_mask.sum()),
        "dam_avail_mean_at_covered_band_hours": dam_cov,
        "model_cap_hat_mw": cap_hat,
        "residual_summary": {c: _agg(resid, c) for c in ("CC", "CT")},
        "formed_summary": {c: _agg(formed, c) for c in ("CC", "CT")},
        "control_summary": {c: _agg(control, c) for c in ("CC", "CT")},
        "on_share_by_bin": by_bin,
        "supply_mix_residual": _mix_summary(model_mix, actual_mix, resid_mask),
        "supply_mix_control": _mix_summary(model_mix, actual_mix, control_mask),
        "residual_hours": hours_out,
    }


def main() -> None:
    """Run the measurement and write the JSON artifact + console summary."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    ap.add_argument(
        "--bundle-tpl",
        default="results/calibration/_ercot89_measure_{year}",
        help="model bundle path template ({year} substituted)",
    )
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    actual = pd.read_parquet(ACTUAL_LMP)
    result: dict = {
        "_provenance": {
            "probe": "ercot89_shoulder_online_measure",
            "charter": "docs/handoffs/ercot-shoulder-online-envelope-2026-07.md §4",
            "role": (
                "MEASUREMENT ONLY — quantifies the hour-level online-"
                "capability wedge behind the mid-band residual; not a model "
                "input, no apply seam. The per-hour ON series is an "
                "operational outcome: only its CONDITIONAL structure (net-"
                "load bin x season) may ever drive a mechanism (rule 13)."
            ),
            "mid_band_usd_mwh": list(MID_BAND),
            "status_families": list(_FAMILIES),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "merchant_scope": dict(CLASS_OF_RESTYPE),
            "model_klass_map": dict(MODEL_KLASS),
            "caveat_hourly_lambda": (
                "actual RT is hourly (mean of 4-12 SCED intervals); intra-hour "
                "spikes are smoothed"
            ),
            "caveat_model_cap": (
                "model_cap = cap_hat x DAM class-day avail, with cap_hat "
                "inferred from the replay's own peak dispatch/avail ratio "
                "(no availability is persisted in bundles) — an estimate, "
                "tight because the LP dispatches full class capability in "
                "its scarcest hours"
            ),
            "caveat_overlay_identity": (
                "day_nonout (day-mean non-OUT HSL) is the model's capability "
                "level via the ercot_thermal_dam_availability overlay identity "
                "(only-OUT-is-out, class-day mean, flat within the day) — the "
                "comparison needs no fleet reconstruction"
            ),
        }
    }
    for y in args.years:
        bundle = REPO / args.bundle_tpl.format(year=y)
        result[str(y)] = measure_year(y, bundle, actual)
        r = result[str(y)]
        print(
            f"\n=== {y}: {r.get('n_residual_covered', 0)} residual / "
            f"{r.get('n_formed_covered', 0)} formed / "
            f"{r.get('n_control_covered', 0)} control covered hours "
            f"(model side: {r.get('model_side')}) ==="
        )
        for cls in ("CC", "CT"):
            rs = r.get("residual_summary", {}).get(cls, {})
            cs = r.get("control_summary", {}).get(cls, {})
            if rs.get("n"):
                print(
                    f"  {cls}: resid ON share {rs['on_share_med']} vs control "
                    f"{cs.get('on_share_med')} | wedge (day nonOUT - ON) "
                    f"{rs['wedge_med']} MW | ON spare {rs['on_spare_hasl_med']} MW"
                    f" | model MW {rs['model_mw_med']} vs ON BP {rs['on_bp_med']}"
                )
    args.out.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
