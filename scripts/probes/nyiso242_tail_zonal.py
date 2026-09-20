"""nyiso-242 phase 0B — the missed 2022 tail, zone by zone, on a like-for-like statistic.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Phase 0A established that the C3c gate
compares two DIFFERENT statistics: the actual side is the **simple mean of the
eleven internal NYISO zones** (``derive_actual_lmp._nyiso_wide`` →
``actual_lmp_hourly_NYISO.parquet``), while the model side is the **max zonal
dual** (``calibration_verdict.score_price_tail`` over ``ordc.hoursGt200``).
The model is therefore measured on the MORE generous statistic and still falls
short, so the miss is real — but the asymmetry hides WHERE the actual price
lives, and that is the thing a successor mechanism has to reproduce.

This probe rebuilds the actual per-model-zone hourly RT series from the raw
monthly ``realtime_zone`` zips using the SAME clock convention
``derive_actual_lmp`` adjudicated (5-minute stamps are interval-ENDING), maps
the eleven zones onto the five model zones with ``NYISO_ZONE_MAP``, and asks
of every hour the model misses: what did each zone actually do, and what did
the model's own zone do?

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso242_tail_zonal.py [--year 2022]
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
LMP_DIR = REPO / "data" / "raw" / "lmp-data" / "NYISO"
ACTUAL_HUB = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"
THRESHOLD = 300.0

NYISO_INTERNAL = (
    "WEST", "GENESE", "CENTRL", "NORTH", "MHK VL", "CAPITL",
    "HUD VL", "MILLWD", "DUNWOD", "N.Y.C.", "LONGIL",
)
NYISO_ZONE_MAP: dict[str, list[str]] = {
    "Upstate_West": ["WEST", "GENESE", "CENTRL", "NORTH", "MHK VL"],
    "Capital_Hudson": ["CAPITL"],
    "Lower_Hudson": ["HUD VL", "MILLWD", "DUNWOD"],
    "NYC": ["N.Y.C."],
    "Long_Island": ["LONGIL"],
}
_EASTERN = "America/New_York"


def _localize_ordered(ts: pd.Series, by: pd.Series) -> pd.DatetimeIndex:
    """DST-safe localization: the fall-back hour's second instance is the later.

    Mirrors ``derive_actual_lmp._localize_ordered`` — within each (zone, day)
    a stamp at or below the running max is the repeated (second) instance.
    """
    ns = ts.astype("int64").to_numpy()
    prev_max = (
        pd.Series(ns)
        .groupby([by.to_numpy(), ts.dt.normalize().to_numpy()], sort=False)
        .transform(lambda x: x.cummax().shift(1))
    )
    second = ns <= prev_max.to_numpy()
    return pd.DatetimeIndex(ts).tz_localize(_EASTERN, ambiguous=~second, nonexistent="raise")


def actual_zonal(year: int) -> pd.DataFrame:
    """Hourly actual RT price per MODEL zone, indexed by hour-of-year."""
    frames = []
    for path in sorted(LMP_DIR.glob(f"{year}*realtime_zone_csv.zip")):
        with zipfile.ZipFile(path) as z:
            for dn in z.namelist():
                if dn.endswith(".csv"):
                    frames.append(pd.read_csv(io.BytesIO(z.read(dn))))
    if not frames:
        raise SystemExit(f"no raw RT zips for {year} under {LMP_DIR}")
    df = pd.concat(frames, ignore_index=True)
    col = [c for c in df.columns if "LBMP" in c and "Losses" not in c and "Congestion" not in c][0]
    df = df[df["Name"].isin(NYISO_INTERNAL)].copy()
    ts = pd.to_datetime(df["Time Stamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
    keep = ts.notna()
    df, ts = df[keep], ts[keep]
    utc = _localize_ordered(ts, df["Name"]).tz_convert("UTC")
    # RT 5-minute stamps are interval-ENDING (adjudicated in derive_actual_lmp).
    df["ts"] = (pd.DatetimeIndex(utc) - pd.Timedelta(seconds=1)).floor("h")
    df["price"] = pd.to_numeric(df[col], errors="coerce")
    wide = df.pivot_table(index="ts", columns="Name", values="price", aggfunc="mean")
    wide = wide.sort_index()
    out = pd.DataFrame(index=range(len(wide)))
    # The eleven-zone SIMPLE MEAN is the gate's own actual statistic.
    out["actual_hub11"] = wide[list(NYISO_INTERNAL)].mean(axis=1).to_numpy()
    for mz, zs in NYISO_ZONE_MAP.items():
        out[f"actual_{mz}"] = wide[zs].mean(axis=1).to_numpy()
    return out


def model_zonal(year: int) -> pd.DataFrame:
    sysf = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"] != "NYISO_external")]
    wide = sysf.pivot_table(index="hour", columns="zone", values="price")
    dem = sysf.pivot_table(index="hour", columns="zone", values="demand")
    out = pd.DataFrame(index=wide.index)
    for z in wide.columns:
        out[f"model_{z}"] = wide[z]
    out["model_max"] = wide.max(axis=1)
    # The model's like-for-like analogue of the gate's actual statistic: the
    # simple mean across the five model zones. It is NOT the eleven-zone mean
    # (five model zones aggregate eleven at different weights), so it is
    # reported as an approximation and never substituted for the gate.
    out["model_mean5"] = wide.mean(axis=1)
    out["model_lw"] = (wide * dem).sum(axis=1) / dem.sum(axis=1)
    out["load_mw"] = dem.sum(axis=1)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument(
        "--out",
        default=str(REPO / "results" / "calibration" / "_nyiso242_tail_zonal.json"),
    )
    args = ap.parse_args()
    year = args.year

    act = actual_zonal(year)
    mod = model_zonal(year)
    n = min(len(act), len(mod))
    df = pd.concat([act.iloc[:n].reset_index(drop=True), mod.iloc[:n].reset_index(drop=True)], axis=1)

    # Cross-check the rebuilt hub against the committed gate series.
    hub = pd.read_parquet(ACTUAL_HUB)
    hub = hub[hub["year"] == year].sort_values("hour")["rt"].to_numpy()[:n]
    delta = (df["actual_hub11"].to_numpy() - hub)
    rebuild = {
        "hours": int(n),
        "max_abs_delta_vs_committed_hub": float(pd.Series(delta).abs().max()),
        "mean_abs_delta": float(pd.Series(delta).abs().mean()),
        "committed_gt300": int((hub > THRESHOLD).sum()),
        "rebuilt_gt300": int((df["actual_hub11"] > THRESHOLD).sum()),
    }

    a_hot = df["actual_hub11"] > THRESHOLD
    m_hot = df["model_max"] > THRESHOLD
    missed = df[a_hot & ~m_hot]

    zcols = [f"actual_{z}" for z in NYISO_ZONE_MAP]
    mcols = [f"model_{z}" for z in NYISO_ZONE_MAP]

    rec = {
        "year": year,
        "rebuild_check": rebuild,
        "missed_hours": int(len(missed)),
        # WHERE the actual price lives in the hours the model misses.
        "actual_zone_median_in_missed": {
            c.replace("actual_", ""): float(missed[c].median()) for c in zcols
        },
        "model_zone_median_in_missed": {
            c.replace("model_", ""): float(missed[c].median()) for c in mcols
        },
        # Is the actual event STATEWIDE or a downstate pocket? An hour whose
        # eleven-zone simple mean clears $300 with upstate near it is a level
        # shift; one carried by LONGIL alone is a pocket.
        "actual_upstate_over_300_in_missed": int((missed["actual_Upstate_West"] > THRESHOLD).sum()),
        "actual_all5_over_300_in_missed": int(
            (missed[zcols] > THRESHOLD).all(axis=1).sum()
        ),
        "actual_only_downstate_over_300": int(
            ((missed["actual_Long_Island"] > THRESHOLD) | (missed["actual_NYC"] > THRESHOLD))
            & (missed["actual_Upstate_West"] <= THRESHOLD)
        ).__int__() if False else int(
            (
                ((missed["actual_Long_Island"] > THRESHOLD) | (missed["actual_NYC"] > THRESHOLD))
                & (missed["actual_Upstate_West"] <= THRESHOLD)
            ).sum()
        ),
        # The like-for-like level gap, per zone, in those hours.
        "median_gap_actual_minus_model": {
            z: float((missed[f"actual_{z}"] - missed[f"model_{z}"]).median())
            for z in NYISO_ZONE_MAP
        },
        "model_mean5_median_in_missed": float(missed["model_mean5"].median()),
        "actual_hub11_median_in_missed": float(missed["actual_hub11"].median()),
        "load_pct_of_peak_median": float(
            100.0 * missed["load_mw"].median() / df["load_mw"].max()
        ),
    }

    # Month split — the 2022 miss is winter-dominated; separate the winter
    # cluster from the summer one so a successor is not aimed at an average
    # of two different phenomena.
    ts = pd.date_range(f"{year}-01-01", periods=n, freq="h")
    mon = pd.Series(ts.month, index=df.index)
    for label, months in (("winter_JanFebDec", (1, 2, 12)), ("summer_JunJulAug", (6, 7, 8))):
        sel = missed[mon[missed.index].isin(months)]
        if not len(sel):
            continue
        rec[label] = {
            "hours": int(len(sel)),
            "actual_hub11_median": float(sel["actual_hub11"].median()),
            "model_mean5_median": float(sel["model_mean5"].median()),
            "model_max_median": float(sel["model_max"].median()),
            "load_pct_of_peak_median": float(
                100.0 * sel["load_mw"].median() / df["load_mw"].max()
            ),
            "actual_upstate_median": float(sel["actual_Upstate_West"].median()),
            "model_upstate_median": float(sel["model_Upstate_West"].median()),
            "actual_LI_median": float(sel["actual_Long_Island"].median()),
            "model_LI_median": float(sel["model_Long_Island"].median()),
        }

    print(json.dumps(rec, indent=2))
    Path(args.out).write_text(json.dumps(rec, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
