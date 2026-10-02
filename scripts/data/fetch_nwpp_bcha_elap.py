"""Fetch BC Hydro's (Powerex) WEIM load-aggregation price, ``ELAP_BCHA-APND``.

NWPP-NEXT-20 (closeout-NWPP wave 1; owner card 2026-10-02 "Fix both, then
solve"). The WECC_CAN seam in ``INTERFACE_NEIGHBORS["NWPP"]`` was anchored on
the Mid-C **Peak** ICE index — peak-only, declared upward-biased, $12–38 above
measured BPAT in 2023–25 (FINDING-nwppnext19 §6b). This pulls the all-hours
replacement: the 15-minute RTPD LMP at BCHA's own WEIM load-aggregation point,
i.e. the price on the CANADIAN side of the seam (Canada is outside the
footprint, ruling N1), the same construction as the CAISO seam's MALIN anchor
(CAISO's side of Path 66). It is never the footprint's own WEIM price (rule 13).

Same OASIS client, month windows and hour rule as the NWPP-13 store
(``build_nwpp_weim_price_index``); retention begins 2023-06 (README §3), so
2023 is a partial year and the anchor is a matched-window ratio.

Output ``data/raw/nwpp-weim/bcha_elap_hourly.parquet``:
``hour_utc · lmp · n_intervals`` (UTC hour-beginning; an hour with fewer than
``MIN_INTERVALS_PER_HOUR`` 15-minute prints is NaN, nothing filled).

    python scripts/data/fetch_nwpp_bcha_elap.py [--start 2023-06-01]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
from scripts.data.build_nwpp_weim_price_index import (  # noqa: E402
    FETCH_END_UTC,
    MIN_INTERVALS_PER_HOUR,
    PREVAILING_TZ,
    PULL_DIR,
    RAW_DIR,
    _month_windows,
    _stamp,
    oasis_get,
)

NODE = "ELAP_BCHA-APND"
OUT_PATH: Path = RAW_DIR / "bcha_elap_hourly.parquet"


def fetch(start_day: dt.date) -> pd.DataFrame:
    """Pull every month window from ``start_day`` to ``FETCH_END_UTC``; resume-safe."""
    start = (
        pd.Timestamp(dt.datetime.combine(start_day, dt.time(0, 0)), tz=PREVAILING_TZ)
        .tz_convert("UTC")
        .tz_localize(None)
        .to_pydatetime()
    )
    frames = []
    for a, b in _month_windows(start, FETCH_END_UTC):
        out = PULL_DIR / f"bcha_lmp_{a:%Y%m%dT%H%M}_{b:%Y%m%dT%H%M}.csv"
        if not out.exists():
            csv_text, note = oasis_get(
                {
                    "queryname": "PRC_RTPD_LMP",
                    "market_run_id": "RTPD",
                    "node": NODE,
                    "startdatetime": _stamp(a),
                    "enddatetime": _stamp(b),
                }
            )
            if csv_text is None:
                print(f"EMPTY {a:%Y-%m-%d}->{b:%Y-%m-%d}: {note}", flush=True)
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(csv_text, encoding="utf-8")
        df = pd.read_csv(out)
        df = df[df["LMP_TYPE"] == "LMP"]
        print(f"{out.name} rows={len(df)}", flush=True)
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    raw["interval_start_utc"] = pd.to_datetime(raw["INTERVALSTARTTIME_GMT"], utc=True)
    raw = raw.drop_duplicates("interval_start_utc")
    raw["hour_utc"] = raw["interval_start_utc"].dt.floor("h")
    g = raw.groupby("hour_utc")["PRC"].agg(["mean", "count"]).reset_index()
    g["lmp"] = g["mean"].where(g["count"] >= MIN_INTERVALS_PER_HOUR)
    out_df = g.rename(columns={"count": "n_intervals"})[
        ["hour_utc", "lmp", "n_intervals"]
    ]
    out_df["lmp"] = out_df["lmp"].astype("float32")
    out_df["n_intervals"] = out_df["n_intervals"].astype("int8")
    return out_df


def bcha_anchor_heat_rates(
    path: Path = OUT_PATH,
    hh_monthly: Path = REPO / "data/raw/gas-prices/henry_hub_monthly.csv",
) -> pd.DataFrame:
    """Return the WECC_CAN seam's measured HR anchor per year from the BCHA ELAP store.

    One rule for every year (the SPP-51 / NWPP-20 construction, extended to a
    partial year): ``hr = mean(lmp over the priced hours) / mean(HH_month(h) +
    basis over the same hours)``, HH the measured EIA monthly spot, basis
    ``GAS_BASIS_DIFFERENTIAL["NWPP"]`` (the seam's own registered basis). For a
    full year this is the annual-mean ratio the other seams use; for 2023
    (retention starts in June) the gas side is matched to the priced window, so
    the window's season does not leak into the heat rate through the gas level.
    Year = the fixed-PST year of the hour (the model clock).
    """
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL

    df = pd.read_parquet(path).dropna(subset=["lmp"])
    pst = pd.to_datetime(df["hour_utc"], utc=True).dt.tz_convert("Etc/GMT+8")
    df = df.assign(year=pst.dt.year, month=pst.dt.month)
    hh = pd.read_csv(hh_monthly).set_index(["year", "month"])["price_usd_mmbtu"]
    df["gas"] = (
        hh.reindex(pd.MultiIndex.from_arrays([df["year"], df["month"]])).to_numpy()
        + GAS_BASIS_DIFFERENTIAL["NWPP"]
    )
    g = df.groupby("year").agg(
        hours=("lmp", "size"),
        first=("hour_utc", "min"),
        lmp_mean=("lmp", "mean"),
        gas_mean=("gas", "mean"),
    )
    g["hr"] = g["lmp_mean"] / g["gas_mean"]
    return g


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", default="2023-06-01", type=dt.date.fromisoformat)
    args = ap.parse_args(argv)
    df = fetch(args.start)
    df.to_parquet(OUT_PATH, index=False)
    print(
        f"wrote {OUT_PATH} hours={len(df)} first={df.hour_utc.min()} last={df.hour_utc.max()}"
    )


if __name__ == "__main__":
    main()
