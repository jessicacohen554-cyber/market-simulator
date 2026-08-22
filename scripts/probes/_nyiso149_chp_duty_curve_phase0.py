"""nyiso-149 phase 0 — the CHP lay-up cohort's PRICE-CONDITIONAL duty, measured.

The identification nyiso-148 §4 named for the chp_layup_duty_split successor:
*"each census plant's metered on-share as a function of its own zone's realized
price"*. This probe MEASURES that statistic — mechanism-blind: it reads only
CAMPD unit-level gross load and the NYISO MIS real-time zonal LBMP, never a
model output, a residual, or a mechanism verdict.

Per census plant (the FROZEN 7-plant membership of
``data/raw/_processed-legacy/chp_layup_census_NYISO.csv`` — rule 23: read, not
re-derived), per year 2023–2025 and pooled:

* **on-share by own-zone price decile** — the duty curve itself;
* **banded duty** s_lo / s_mid / s_hi at price bands <p40 / p40–p80 / ≥p80 of
  the zone-year's hourly RT price (quantile conditioning regenerates for any
  vintage and responds to changed conditions — rule 13);
* **loading when on** L = mean(gross/HSL | on), HSL = the census's own
  ``observed_hsl_mw`` (frozen);
* a **live-hour variant** excluding hours inside CAMPD-zero runs ≥ 120 h — the
  SAME ≥5-day full-stop window the economic-layup outage channel detects
  (``outages.unit_layup_csv_for_iso``), cited rather than invented, so the
  duty statistic can compose with the availability envelope without
  double-counting the mothball months (rule 19 [R-ONE-MECH]);
* the **model-capacity utilization by band** U_b = s_b · L · HSL / pmax — the
  quantity an offer-tranche encoding would have to reproduce.

Clock note: CAMPD hours and the MIS LBMP stamps are joined on local
(month, day, hour); the DST offset is ≤ 1 h against 10–43 h median runs and
banded statistics, second-order here.

Output: ``results/calibration/_nyiso149_chp_duty_curve_phase0.json``.
"""

from __future__ import annotations

import csv
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import (  # noqa: E402
    CAMPD_UNIT_LEVEL_DIR as UNIT_LEVEL_DIR,
    PROCESSED_DIR,
)
from market_sim.data.campd import states_for_iso  # noqa: E402

ISO = "NYISO"
YEARS: tuple[int, ...] = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]
LMP_DIR = REPO / "data/raw/lmp-data/NYISO"
OUT = REPO / "results/calibration/_nyiso149_chp_duty_curve_phase0.json"

# NYISO load-zone letters -> model zones (config/iso_configs.py::_nyiso_config).
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

# The economic-layup outage channel's own full-stop window (>=5 days;
# outages.unit_layup_csv_for_iso docstring) — cited, not a new constant.
LAYUP_RUN_HOURS = 120

BANDS = {"lo": (0.0, 0.40), "mid": (0.40, 0.80), "hi": (0.80, 1.0001)}


def census() -> list[dict]:
    """The frozen 7-plant lay-up census (membership is NOT re-derived)."""
    with (PROCESSED_DIR / "chp_layup_census_NYISO.csv").open(newline="") as fh:
        return [r for r in csv.DictReader(fh) if r["laid_up"].lower() == "true"]


def _month_zip(year: int, month: int) -> Path:
    """The month's MIS zonal LBMP zip: committed copy, else fetched to cache.

    Mirrors the nyiso-124 G0 convention — months absent from the immutable raw
    root are fetched on demand from the public MIS archive to a cache dir, so
    the raw tree stays append-only and the probe stays reproducible.
    """
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
    """Hourly model-zone RT price: (mo, dy, hr) keyed, mean of member letters."""
    frames = []
    for month in range(1, 13):
        path = _month_zip(year, month)
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.endswith(".csv"):
                    frames.append(pd.read_csv(zf.open(name)))
    df = pd.concat(frames, ignore_index=True)
    df.columns = ["ts", "name", "ptid", "lbmp", "loss", "cong"]
    df["letter"] = df["name"].astype(str).str.strip().map(NAME_TO_LETTER)
    df = df.dropna(subset=["letter"])
    ts = pd.to_datetime(df["ts"], format="%m/%d/%Y %H:%M:%S")
    df["mo"], df["dy"], df["hr"] = ts.dt.month, ts.dt.day, ts.dt.hour
    hourly = (
        df.groupby(["letter", "mo", "dy", "hr"])["lbmp"].mean().unstack(0)
    )
    out = pd.DataFrame(index=hourly.index)
    for zone, letters in MODEL_ZONES.items():
        cols = [c for c in letters if c in hourly.columns]
        out[zone] = hourly[cols].mean(axis=1)
    return out.reset_index()


def plant_gross(year: int, codes: set[int]) -> pd.DataFrame:
    """Hourly plant gross MW (units summed), (mo, dy, hr) keyed."""
    frames = []
    for state in states_for_iso(ISO):
        path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path, columns=["facilityId", "date", "hour", "grossLoad"]
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)]
        if not df.empty:
            frames.append(df)
    if not frames:
        raise SystemExit(f"no CAMPD rows for the census in {year}")
    df = pd.concat(frames, ignore_index=True)
    ts = pd.to_datetime(df["date"])
    df["mo"], df["dy"] = ts.dt.month, ts.dt.day
    df["hr"] = pd.to_numeric(df["hour"], errors="coerce")
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    return df.groupby(["facilityId", "mo", "dy", "hr"], as_index=False)[
        "grossLoad"
    ].sum()


def live_mask(on: np.ndarray) -> np.ndarray:
    """True where the hour is NOT inside a zero-run >= LAYUP_RUN_HOURS."""
    live = np.ones(on.shape[0], dtype=bool)
    n = on.shape[0]
    i = 0
    while i < n:
        if not on[i]:
            j = i
            while j < n and not on[j]:
                j += 1
            if j - i >= LAYUP_RUN_HOURS:
                live[i:j] = False
            i = j
        else:
            i += 1
    return live


def main() -> None:
    rows = census()
    codes = {int(r["plant_code"]) for r in rows}
    meta = {
        int(r["plant_code"]): {
            "name": r["plant_name"],
            "zone": r["zone"],
            "pmax": float(r["model_pmax_mw"]),
            "hsl": float(r["observed_hsl_mw"]),
        }
        for r in rows
    }
    out = {
        "session": "nyiso-149",
        "statistic": (
            "metered on-share conditional on own-zone RT price (deciles + "
            "lo/mid/hi bands at p40/p80), loading-when-on vs census HSL, all "
            "hours AND live hours (zero-runs >= 120 h excluded); membership "
            "FROZEN from chp_layup_census_NYISO.csv"
        ),
        "plants": {},
    }
    per_plant: dict[int, dict] = {
        c: {"years": {}, "pooled_acc": []} for c in codes
    }
    for year in YEARS:
        zp = zone_price(year)
        pg = plant_gross(year, codes)
        for code in sorted(codes):
            m = meta[code]
            zcol = zp[["mo", "dy", "hr", m["zone"]]].rename(
                columns={m["zone"]: "price"}
            )
            g = pg[pg["facilityId"] == code][["mo", "dy", "hr", "grossLoad"]]
            j = zcol.merge(g, on=["mo", "dy", "hr"], how="left").fillna(
                {"grossLoad": 0.0}
            )
            j = j.sort_values(["mo", "dy", "hr"]).reset_index(drop=True)
            price = j["price"].to_numpy(float)
            gross = j["grossLoad"].to_numpy(float)
            on = gross > 0.0
            q = pd.Series(price).rank(pct=True).to_numpy()
            live = live_mask(on)
            yr = {
                "hours": int(len(j)),
                "on_share": round(float(on.mean()), 4),
                "loading_when_on": (
                    round(float((gross[on] / m["hsl"]).mean()), 4)
                    if on.any()
                    else 0.0
                ),
                "decile_on_share": [
                    round(float(on[(q >= d / 10) & (q < (d + 1) / 10)].mean()), 4)
                    for d in range(10)
                ],
                "live_hour_share": round(float(live.mean()), 4),
            }
            for label, (a, b) in BANDS.items():
                sel = (q >= a) & (q < b)
                yr[f"s_{label}"] = round(float(on[sel].mean()), 4)
                sel_live = sel & live
                yr[f"s_{label}_live"] = (
                    round(float(on[sel_live].mean()), 4) if sel_live.any() else None
                )
            per_plant[code]["years"][year] = yr
            per_plant[code]["pooled_acc"].append(
                pd.DataFrame({"price_q": q, "on": on, "gross": gross, "live": live})
            )
    for code in sorted(codes):
        m = meta[code]
        pool = pd.concat(per_plant[code]["pooled_acc"], ignore_index=True)
        on = pool["on"].to_numpy(bool)
        q = pool["price_q"].to_numpy(float)
        live = pool["live"].to_numpy(bool)
        gross = pool["gross"].to_numpy(float)
        pooled = {
            "on_share": round(float(on.mean()), 4),
            "loading_when_on": (
                round(float((gross[on] / m["hsl"]).mean()), 4) if on.any() else 0.0
            ),
        }
        for label, (a, b) in BANDS.items():
            sel = (q >= a) & (q < b)
            sel_live = sel & live
            pooled[f"s_{label}"] = round(float(on[sel].mean()), 4)
            pooled[f"s_{label}_live"] = (
                round(float(on[sel_live].mean()), 4) if sel_live.any() else None
            )
            # model-capacity utilization the encoding must reproduce
            u = float(on[sel].mean()) * pooled["loading_when_on"] * m["hsl"] / m["pmax"]
            pooled[f"U_{label}_of_pmax"] = round(u, 4)
        out["plants"][str(code)] = {
            "name": m["name"],
            "zone": m["zone"],
            "pmax_mw": m["pmax"],
            "hsl_mw": m["hsl"],
            "pooled": pooled,
            "years": per_plant[code]["years"],
        }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
