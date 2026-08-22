"""Derive the CHP lay-up cohort's price-conditional duty curve (nyiso-149).

The OFFER-SHAPE identification for ``ScenarioConfig.chp_layup_duty_curve`` —
the successor nyiso-148 §4 named when it rejected the single-band
``chp_layup_duty_split``: *"the identification the successor needs is a
price-conditional on-share, not a band level"*. The census MEMBERSHIP is the
frozen ``chp_layup_census_NYISO.csv`` (rule 23 — read, never re-derived); this
script derives, per census plant, HOW MUCH of its capacity belongs in each of
the class offer curve's existing bands.

THE STATISTIC. For each census plant, from CAMPD unit-level hourly gross load
and its own model zone's MIS real-time zonal LBMP (the exact statistic
nyiso-148 prescribed), pooled 2023-2025:

* ``s_mid`` / ``s_hi`` — metered ON-share (plant gross > 0) in hours whose
  own-zone price sits in the p40-p80 / >= p80 band of the zone-year's hourly
  distribution, measured CONDITIONAL ON ENVELOPE-LIVE HOURS (below);
* ``loading`` — mean(gross / HSL | on), the block-loading level when on, with
  HSL the census's own ``observed_hsl_mw``;
* the offer fractions, as % of the model plant capacity (census
  ``model_pmax_mw``)::

      pct_econ = 100 * s_mid * loading * hsl / pmax
      pct_peak = 100 * (s_hi - s_mid) * loading * hsl / pmax

  A duty-curve plant offers ``pct_econ`` at the class ECON band, ``pct_peak``
  at the class PEAK band, and WITHHOLDS the remainder — the measured "never
  seen at any price" share (mothballed trains do not return for a price
  spike). Offer LEVELS are the class curve's existing identified multipliers:
  zero new price constants (rule 21 [R-DOF]).

ENVELOPE CONDITIONING — why, and why it is measured-only. The availability
envelope (the committed CAMPD outage extract
``data/raw/campd-unit-outages-NYISO.csv``) already carries the cohort's
mothball spells for six of the seven plants (measured nyiso-149 phase 0:
envelope availability tracks the metered live-hour share within ~0.02
everywhere except Lockport 54041, which reads ~1.0 available against live
shares of 0.12-0.44). An on-share measured over ALL hours would double-count
those spells (offer withhold x envelope derate); one measured over live hours
only would over-produce exactly where the envelope misses them. Conditioning
the duty statistic on ENVELOPE-LIVE hours (available capacity fraction > 0.5
under the same frozen outage windows the recipe applies) makes the
composition exact BY CONSTRUCTION for every plant: where the envelope carries
the spells the offer owns only the residual conduct, and where it does not
(Lockport) the envelope-live hours are all hours and the offer owns the whole
duty. Rule 19 [R-ONE-MECH]: the envelope owns physical absence, the offer
owns the price response, and neither stacks on the other's share.

Both conditioning inputs are frozen measured artifacts derived from CAMPD by
their own scripts; no model output, price residual or mechanism verdict is
read (mechanism-blind, like the census).

Rule 13 [R-MEASURED]: the statistic regenerates for any vintage from the
CAMPD + MIS-LBMP pipelines, and responds to changed conditions — a plant
returning to service raises its own measured duty. Rule 23
[R-FROZEN-DERIVE]: re-derive ONLY when the CAMPD vintages, the LBMP archive
or the outage extract update — never because a residual moved.

Output: ``data/raw/_processed-legacy/chp_duty_curve_NYISO.csv``.
Zonal LBMP months absent from ``data/raw/lmp-data/NYISO`` are fetched from
the public MIS archive to ``.cache/nyiso149/zonal`` (the nyiso-124 G0
convention — the immutable raw root stays append-only).
"""

from __future__ import annotations

import csv
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import (  # noqa: E402
    CAMPD_UNIT_LEVEL_DIR,
    PROCESSED_DIR,
    RAW_DATA_DIR,
)
from market_sim.data.campd import states_for_iso  # noqa: E402

ISO = "NYISO"
YEARS: tuple[int, ...] = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]
LMP_DIR = REPO / "data/raw/lmp-data/NYISO"
OUT = PROCESSED_DIR / "chp_duty_curve_NYISO.csv"

NAME_TO_LETTER = {
    "WEST": "A",
    "GENESE": "B",
    "CENTRL": "C",
    "NORTH": "D",
    "MHK VL": "E",
    "CAPITL": "F",
    "HUD VL": "G",
    "MILLWD": "H",
    "DUNWOD": "I",
    "N.Y.C.": "J",
    "LONGIL": "K",
}
MODEL_ZONES = {
    "Upstate_West": list("ABCDE"),
    "Capital_Hudson": ["F", "G"],
    "Lower_Hudson": ["H", "I"],
    "NYC": ["J"],
    "Long_Island": ["K"],
}
# Own-zone price bands: p40-p80 (the class econ range) and >= p80 (the peak
# range) of the zone-year's hourly RT distribution. Declared a priori in the
# nyiso-149 phase-0 probe (committed before this mechanism existed) and not
# swept — binning of a measured curve, not a tuned value.
Q_ECON, Q_PEAK = 0.40, 0.80


def census_rows() -> list[dict]:
    """The frozen lay-up census (membership is NOT re-derived here)."""
    with (PROCESSED_DIR / "chp_layup_census_NYISO.csv").open(newline="") as fh:
        return [r for r in csv.DictReader(fh) if r["laid_up"].lower() == "true"]


def month_zip(year: int, month: int) -> Path:
    """Committed MIS zonal LBMP month, else fetched to the cache."""
    committed = LMP_DIR / f"{year}{month:02d}01realtime_zone_csv.zip"
    if committed.exists():
        return committed
    cache = REPO / ".cache/nyiso149/zonal" / f"{year}{month:02d}.zip"
    if not cache.exists():
        import urllib.request

        cache.parent.mkdir(parents=True, exist_ok=True)
        url = (
            "https://mis.nyiso.com/public/csv/realtime/"
            f"{year}{month:02d}01realtime_zone_csv.zip"
        )
        print(f"  fetching {url}")
        urllib.request.urlretrieve(url, cache)
    return cache


def zone_price(year: int) -> pd.DataFrame:
    """Hourly model-zone RT price keyed on (mo, dy, hr)."""
    frames = []
    for month in range(1, 13):
        with zipfile.ZipFile(month_zip(year, month)) as zf:
            for name in zf.namelist():
                if name.endswith(".csv"):
                    frames.append(pd.read_csv(zf.open(name)))
    df = pd.concat(frames, ignore_index=True)
    df.columns = ["ts", "name", "ptid", "lbmp", "loss", "cong"]
    df["letter"] = df["name"].astype(str).str.strip().map(NAME_TO_LETTER)
    df = df.dropna(subset=["letter"])
    ts = pd.to_datetime(df["ts"], format="%m/%d/%Y %H:%M:%S")
    df["mo"], df["dy"], df["hr"] = ts.dt.month, ts.dt.day, ts.dt.hour
    hourly = df.groupby(["letter", "mo", "dy", "hr"])["lbmp"].mean().unstack(0)
    out = pd.DataFrame(index=hourly.index)
    for zone, letters in MODEL_ZONES.items():
        cols = [c for c in letters if c in hourly.columns]
        out[zone] = hourly[cols].mean(axis=1)
    return out.reset_index()


def plant_gross(year: int, codes: set[int]) -> pd.DataFrame:
    """Hourly plant gross MW (units summed) keyed on (mo, dy, hr)."""
    frames = []
    for state in states_for_iso(ISO):
        path = CAMPD_UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=["facilityId", "date", "hour", "grossLoad"])
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)]
        if not df.empty:
            frames.append(df)
    if not frames:
        raise SystemExit(f"no CAMPD hours for the census in {year}")
    df = pd.concat(frames, ignore_index=True)
    ts = pd.to_datetime(df["date"])
    df["mo"], df["dy"] = ts.dt.month, ts.dt.day
    df["hr"] = pd.to_numeric(df["hour"], errors="coerce")
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    return df.groupby(["facilityId", "mo", "dy", "hr"], as_index=False)[
        "grossLoad"
    ].sum()


def envelope_live(code: int, year: int, key: pd.DataFrame) -> np.ndarray:
    """True where the outage record leaves > 0.5 of plant capacity available.

    Built from the SAME committed CAMPD unit-outage extract the recipe's
    availability envelope applies (``campd-unit-outages-NYISO.csv``, the main
    >= 5-day windows), capacity-weighted across units. A plant with no rows
    (or no capacity) is live in every hour — exactly the state the envelope
    leaves it in.
    """
    df = pd.read_csv(RAW_DATA_DIR / f"campd-unit-outages-{ISO}.csv")
    rows = df[df["facility_id"] == code]
    idx = pd.to_datetime(
        {
            "year": year,
            "month": key["mo"],
            "day": key["dy"],
            "hour": key["hr"],
        }
    )
    out_mw = np.zeros(len(key), dtype=float)
    plant_cap = float(rows["plant_capacity_mw"].max()) if len(rows) else 0.0
    for _, r in rows.iterrows():
        s, e = pd.Timestamp(r["outage_start"]), pd.Timestamp(r["outage_end"])
        out_mw += np.where((idx >= s) & (idx < e), float(r["unit_capacity_mw"]), 0.0)
    if plant_cap <= 0.0:
        return np.ones(len(key), dtype=bool)
    return (1.0 - out_mw / plant_cap) > 0.5


def main() -> None:
    rows = census_rows()
    codes = {int(r["plant_code"]) for r in rows}
    out_rows = []
    acc: dict[int, list[pd.DataFrame]] = {c: [] for c in codes}
    for year in YEARS:
        zp = zone_price(year)
        pg = plant_gross(year, codes)
        for r in rows:
            code = int(r["plant_code"])
            zone = r["zone"]
            zcol = zp[["mo", "dy", "hr", zone]].rename(columns={zone: "price"})
            g = pg[pg["facilityId"] == code][["mo", "dy", "hr", "grossLoad"]]
            j = zcol.merge(g, on=["mo", "dy", "hr"], how="left").fillna(
                {"grossLoad": 0.0}
            )
            j = j.sort_values(["mo", "dy", "hr"]).reset_index(drop=True)
            j["q"] = j["price"].rank(pct=True)
            j["live"] = envelope_live(code, year, j[["mo", "dy", "hr"]])
            acc[code].append(j[["q", "grossLoad", "live"]])
    for r in rows:
        code = int(r["plant_code"])
        pool = pd.concat(acc[code], ignore_index=True)
        on = pool["grossLoad"].to_numpy(float) > 0.0
        q = pool["q"].to_numpy(float)
        live = pool["live"].to_numpy(bool)
        hsl = float(r["observed_hsl_mw"])
        pmax = float(r["model_pmax_mw"])
        mid = (q >= Q_ECON) & (q < Q_PEAK) & live
        hi = (q >= Q_PEAK) & live
        s_mid = float(on[mid].mean()) if mid.any() else 0.0
        s_hi = float(on[hi].mean()) if hi.any() else 0.0
        loading = float((pool["grossLoad"].to_numpy(float)[on] / hsl).mean())
        # The duty is a MW quantity — basis-free (PREREG §7: expressing it as
        # a fraction of one capacity basis and applying it to another re-based
        # it; the seams consume these MW directly).
        econ_mw = s_mid * loading * hsl
        peak_mw = max(0.0, s_hi - s_mid) * loading * hsl
        pct_econ = 100.0 * econ_mw / pmax
        pct_peak = 100.0 * peak_mw / pmax
        out_rows.append(
            {
                "iso": ISO,
                "plant_code": code,
                "plant_name": r["plant_name"],
                "zone": r["zone"],
                "pmax_mw": pmax,
                "hsl_mw": hsl,
                "s_mid_env": round(s_mid, 4),
                "s_hi_env": round(s_hi, 4),
                "loading_when_on": round(loading, 4),
                "econ_mw": round(econ_mw, 2),
                "peak_mw": round(peak_mw, 2),
                "pct_econ": round(pct_econ, 2),
                "pct_peak": round(pct_peak, 2),
                "years": "-".join(str(y) for y in YEARS),
                "source": (
                    "CAMPD unit-level hourly grossLoad (data/raw/campd-unit-level) "
                    "x own-model-zone MIS RT zonal LBMP hourly mean; on-share by "
                    f"zone-year price quantile bands (p{int(Q_ECON * 100)}-"
                    f"p{int(Q_PEAK * 100)} econ, >=p{int(Q_PEAK * 100)} peak), "
                    "conditional on envelope-live hours "
                    "(campd-unit-outages-NYISO.csv available fraction > 0.5); "
                    "membership FROZEN from chp_layup_census_NYISO.csv; "
                    "derive_nyiso_chp_duty_curve.py (nyiso-149)"
                ),
            }
        )
    out_rows.sort(key=lambda x: x["plant_code"])
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {OUT} ({len(out_rows)} plants)")
    for row in out_rows:
        print(
            f"  {row['plant_code']} {row['plant_name'][:28]:<29} "
            f"s_mid/hi={row['s_mid_env']:.3f}/{row['s_hi_env']:.3f} "
            f"L={row['loading_when_on']:.3f} "
            f"econ/peak={row['pct_econ']:.2f}/{row['pct_peak']:.2f} %pmax"
        )


if __name__ == "__main__":
    main()
