"""ERCOT-74 leg-0 tail-hour SET anatomy (rule-16 diagnostic; no solve).

Scores HOUR-SET FIDELITY of the ERCOT RT scarcity tail — the ERCOT-74 charter's
primary metric — between a bundle's model tail (max zonal settled > threshold,
the C3c construction) and the actual RT tail (the committed single-hub hourly
series), producing the three sets the lane adjudicates on:

* ``caught``   — model > threshold AND actual RT > threshold (hour-matched);
* ``missed``   — actual > threshold, model below;
* ``invented`` — model > threshold, actual below.

Every tail hour is joined to the measured NP6-905 reserve/price-adder telemetry
(``data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet``) so each MISSED
hour tests the standing keeper-ledger claim (measured RTORPA <= $3 on the
missed shoulder days => reality's print formed on the ENERGY side) and each
INVENTED hour names the model mechanism that priced it:

* actual side: rt, da (in-DA-tail?), system_lambda, rtorpa, rtordpa, rtolcap,
  and ``rt_minus_adders`` = rt - (rtorpa + rtordpa) — still above the threshold
  means the print survives with ERCOT's reserve adders removed entirely, i.e.
  energy-side (offer-curve) formation;
* model side: settled zonal-max ``zmax`` and its persisted decomposition
  (``rtordpa_overlay`` — the measured overlay; ``ordc_adder`` — the co-opt
  reserve-family dual; energy dual = price - both), plus load-shed slack;
* optional SCED-interval grain (``--intervals`` parquet, scratchpad-only,
  built by re-parsing the NP6-905 annual archive): per tail hour the count of
  ~5-minute intervals whose ``lambda + rtorpa + rtordpa`` settlement proxy
  exceeds the threshold. An hourly-mean crossing carried by a small minority
  of intervals is a sub-hourly transient — out of representation for an
  hourly LP (ledger evidence, not a mechanism lane).

MISSED-hour classes (priority order, one label per hour):

* ``transient`` — interval data present and <= TRANSIENT_MAX_SHARE of the
  hour's intervals cross the threshold (the mean rides a short spike);
* ``reserve``  — ``rt_minus_adders`` < threshold (the crossing needed the
  measured reserve adders => reserve-scarcity formation, would REFUTE the
  ledger claim for that hour);
* ``energy``   — everything else: the print stands on the energy side alone.

INVENTED-hour attribution: ``energy-dual`` if the settled zmax minus both
overlay columns still crosses the threshold (the LP's own price formation —
offer surface / wall / scarcity slack), else whichever overlay column is
decisive (``ordc_adder`` / ``rtordpa_overlay``); ``shed`` flags nonzero slack.

Usage::

    python scripts/probes/_ercot74_anatomy.py BUNDLE [BUNDLE ...]
        [--year 2024] [--threshold 200] [--intervals PATH] [--csv PATH]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "results" / "calibration"
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
RESERVES = REPO / "data" / "raw" / "ercot" / "ercot_{year}_ordc_reserves_hourly.parquet"

# The model's non-leap 8760 clock (same convention as _ercot68_anatomy /
# fetch_ercot_ordc_reserves: Feb 29 dropped, fixed CST).
_CAL = pd.date_range("2023-01-01", periods=8760, freq="h")

# A missed hour is a sub-hourly TRANSIENT when at most this share of its SCED
# intervals crosses the threshold: the hourly mean is then carried by a short
# spike (<= ~20 min of a 12-interval hour), which an hourly deterministic LP
# cannot represent (the same out-of-representation argument that DA-gates the
# other five ISOs' C3c — derive_actual_tail.py docstring). Classification
# cutoff for a diagnostic probe, not a tunable of any solve.
TRANSIENT_MAX_SHARE = 1 / 3


def _hourly_actual(year: int) -> pd.DataFrame:
    act = pd.read_parquet(ACTUAL)
    a = act[act["year"] == year].set_index("hour").reindex(range(8760))
    res = (
        pd.read_parquet(str(RESERVES).format(year=year))
        .set_index("hour")
        .reindex(range(8760))
    )
    df = pd.DataFrame(
        {
            "date": _CAL.strftime("%m-%d"),
            "hod": np.arange(8760) % 24,
            "rt": a["rt"].to_numpy(dtype=float),
            "da": a["da"].to_numpy(dtype=float),
            "lam": res["system_lambda"].to_numpy(dtype=float),
            "rtorpa": res["rtorpa"].to_numpy(dtype=float),
            "rtordpa": res["rtordpa"].to_numpy(dtype=float),
            "rtolcap": res["rtolcap"].to_numpy(dtype=float),
        }
    )
    df["adders"] = df["rtorpa"] + df["rtordpa"]
    df["rt_minus_adders"] = df["rt"] - df["adders"]
    return df


def _interval_shares(path: Path, year: int, threshold: float) -> pd.Series:
    """Per model-clock hour: share of SCED intervals with lambda+adders > threshold."""
    iv = pd.read_parquet(path)
    # ``ts`` is fetch_ercot_ordc_reserves._read_intervals's CST-converted stamp.
    ts = pd.to_datetime(iv["ts"])
    iv = iv[ts.dt.year == year].copy()
    ts = pd.to_datetime(iv["ts"])
    # Non-leap clock: drop Feb 29, then hour index = position on the 8760 grid.
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    iv, ts = iv[keep], ts[keep]
    doy = ts.dt.dayofyear.to_numpy()
    # After dropping Feb 29 in a leap year, days after Feb 28 sit one dayofyear
    # too high on the non-leap grid.
    if pd.Timestamp(f"{year}-12-31").is_leap_year:
        doy = np.where(doy > 59, doy - 1, doy)
    hour_idx = (doy - 1) * 24 + ts.dt.hour.to_numpy()
    proxy = (
        iv["system_lambda"].to_numpy(dtype=float)
        + iv["rtorpa"].to_numpy(dtype=float)
        + iv["rtordpa"].to_numpy(dtype=float)
    )
    g = pd.DataFrame({"hour": hour_idx, "hit": proxy > threshold}).groupby("hour")[
        "hit"
    ]
    return (g.sum() / g.count()).reindex(range(8760))


def _model_hourly(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "system.parquet")
    df = df[(df["pass"] == "P1") & (df["year"] == year)].copy()
    zmax_idx = df.groupby("hour")["price"].idxmax()
    top = df.loc[zmax_idx].set_index("hour").reindex(range(8760))
    out = pd.DataFrame(
        {
            "zmax": top["price"].to_numpy(dtype=float),
            "zone": top["zone"].to_numpy(),
            "shed": df.groupby("hour")["slack"].sum().reindex(range(8760)).to_numpy(),
        }
    )
    for col in ("rtordpa_overlay", "ordc_adder"):
        out[col] = (
            top[col].to_numpy(dtype=float) if col in top.columns else np.zeros(8760)
        )
    out["energy_dual"] = out["zmax"] - out["rtordpa_overlay"] - out["ordc_adder"]
    return out


def classify_missed(row: pd.Series, threshold: float) -> str:
    if not np.isnan(row.get("iv_share", np.nan)) and (
        row["iv_share"] <= TRANSIENT_MAX_SHARE
    ):
        return "transient"
    if row["rt_minus_adders"] < threshold:
        return "reserve"
    return "energy"


def classify_invented(row: pd.Series, threshold: float) -> str:
    label = (
        "energy-dual"
        if row["energy_dual"] > threshold
        else (
            "ordc_adder"
            if row["zmax"] - row["ordc_adder"] <= threshold
            else "rtordpa_overlay"
        )
    )
    if row["shed"] > 0:
        label += "+shed"
    return label


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--threshold", type=float, default=200.0)
    ap.add_argument(
        "--intervals",
        default=None,
        help="scratchpad NP6-905 SCED-interval parquet (timestamp, system_lambda,"
        " rtorpa, rtordpa ...) for the transient classification",
    )
    ap.add_argument("--csv", default=None, help="write the per-hour table here")
    args = ap.parse_args()

    thr = args.threshold
    hourly = _hourly_actual(args.year)
    if args.intervals:
        hourly["iv_share"] = _interval_shares(
            Path(args.intervals), args.year, thr
        ).to_numpy()
    else:
        hourly["iv_share"] = np.nan
    actual_tail = hourly["rt"] > thr
    hourly["in_da_tail"] = hourly["da"] > thr
    print(
        f"actual {args.year} RT tail: {int(actual_tail.sum())} h "
        f"(DA tail: {int(hourly['in_da_tail'].sum())} h)"
    )

    for name in args.bundles:
        model = _model_hourly(ROOT / name, args.year)
        j = pd.concat([hourly, model], axis=1)
        j["actual_tail"] = actual_tail
        j["model_tail"] = j["zmax"] > thr
        caught = j[j["actual_tail"] & j["model_tail"]]
        missed = j[j["actual_tail"] & ~j["model_tail"]].copy()
        invented = j[~j["actual_tail"] & j["model_tail"]].copy()
        missed["class"] = missed.apply(classify_missed, axis=1, threshold=thr)
        invented["driver"] = invented.apply(classify_invented, axis=1, threshold=thr)

        print(f"\n===== {name} ({args.year}, threshold ${thr:.0f}) =====")
        print(
            f"caught {len(caught)} | missed {len(missed)} "
            f"({missed['class'].value_counts().to_dict()}) | "
            f"invented {len(invented)} "
            f"({invented['driver'].value_counts().to_dict()})"
        )

        print("\n-- per-cluster (actual-tail dates) --")
        print(
            f"{'date':>6} {'n':>2} {'caught':>6} {'missed':>6}  "
            f"{'missed hods (class)':<40} {'RTORPA<=3 all?':>14}"
        )
        for d, g in j[j["actual_tail"]].groupby("date"):
            gm = missed[missed["date"] == d]
            det = ", ".join(
                f"h{int(r.hod)}({r['class'][:5]})" for _, r in gm.iterrows()
            )
            orpa_ok = "Y" if (g["rtorpa"] <= 3.0).all() else "N"
            print(
                f"{d:>6} {len(g):>2} {int((g['zmax'] > thr).sum()):>6} "
                f"{len(gm):>6}  {det:<40} {orpa_ok:>14}"
            )

        if len(missed):
            print("\n-- MISSED hours --")
            cols = [
                "date",
                "hod",
                "rt",
                "da",
                "in_da_tail",
                "lam",
                "rtorpa",
                "rtordpa",
                "rt_minus_adders",
                "iv_share",
                "zmax",
                "energy_dual",
                "class",
            ]
            print(missed[cols].round(2).to_string())
        if len(invented):
            print("\n-- INVENTED hours --")
            cols = [
                "date",
                "hod",
                "rt",
                "da",
                "zmax",
                "zone",
                "energy_dual",
                "rtordpa_overlay",
                "ordc_adder",
                "shed",
                "driver",
            ]
            print(invented[cols].round(2).to_string())
        if args.csv:
            j[j["actual_tail"] | j["model_tail"]].round(3).to_csv(args.csv, index=True)
            print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
