"""caiso-141 A2 — the public-source survey for an hourly CAISO pumped-storage /
conventional-hydro split, 2023-2025. NO LP, NO SOLVE, NO INTAKE — this is a
NETWORK probe (the one exception to the committed-bytes probe norm): it
re-runs, against the live public endpoints, every verification that produced
the caiso-141 WALL verdict, so the wall is re-checkable the day a source
appears.

Charter: the caiso-141 session brief (FINDING-caiso140 §E ask A2). The
+793 MW Sep-Dec belly water wedge (FINDING-caiso140 §B) needs an HOURLY
instrument separating pumped-storage net output from conventional hydro;
FINDING-caiso140 §D already adjudicated the in-repo sources (EIA-930 WAT is
PS-blind, EIA-923 is monthly, LESR is battery-only). This probe covers the
PUBLIC candidates named in the charter:

* **S1  EIA-930 ``PS`` fuel category** (the API carries one) — does CISO
  report it? -> row count for CISO x PS (measured 2026-07-30: **0 rows**;
  CISO reports only the legacy 8 categories, batteries folded into OTH).
* **S2  CAISO Today's Outlook fuel mix** (`outlook/history/<date>/
  fuelsource.csv`, the Daily Renewables Watch successor) — is its hydro
  gross-of-pumping (a split instrument against net WAT) or net? -> belly
  hydro minima and the hour-ending alignment vs 930 WAT (measured: hydro
  prints NEGATIVE belly values, e.g. -391 MW on 2025-10-15, and matches WAT
  at corr ~0.95 / |diff| ~287 MW once WAT's hour-ending stamp is shifted —
  the SAME net EMS feed, so no split).
* **S3  CAISO Today's Outlook storage page** (`storage.csv`) — battery-only
  columns (Total/Stand-alone/Hybrid batteries), no PS trace.
* **S4  CDEC hourly telemetry** at the six model PS plants' reservoirs —
  which stations carry ANY hourly sensor? (measured: Courtright CTG, Wishon
  WSN and Shaver SHV carry NONE — PG&E/SCE do not report hourly to CDEC, so
  Helms 1,053 MW and Eastwood 199.8 MW are uninstrumented; only the DWR
  facilities report, and San Luis SNL hourly storage carries a
  2022-07 -> 2024-01 outage).
* **S5  EIA-930 sub-BA route** — demand-only by schema (no fuel facet).
* **S6  OASIS ENE_SLRS** — system totals only (TOT_GEN/LOAD/IMP/EXP), no
  pumping item. (Checked in-session 2026-07-30; not re-fetched here by
  default: OASIS rate-limits and the zip round-trip is slow. ``--oasis``
  re-runs it.)

Fleet shares the wall arithmetic rests on (from the model's own EIA-860
loader, :func:`market_sim.model.storage.load_eia860_pumped_storage`):
Helms 1,053.0 / Gianelli 424.0 / Hyatt 293.1 / Eastwood 199.8 / Thermalito
82.5 / O'Neill 25.2 = 2,077.6 MW; the CDEC-instrumentable DWR share is
824.8 MW (39.7 %), the uninstrumented Helms+Eastwood share 1,252.8 MW
(60.3 %).

Usage::

    uv run python scripts/probes/_caiso141_water_source_survey.py [--oasis]

Exit is informational (prints PASS/CHANGED per check); network required.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]

EIA_FACET_URL = (
    "https://api.eia.gov/v2/electricity/rto/fuel-type-data/facet/fueltype"
    "?api_key=DEMO_KEY"
)
EIA_CISO_PS_URL = (
    "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
    "?api_key=DEMO_KEY&frequency=hourly&data[0]=value"
    "&facets[respondent][]=CISO&facets[fueltype][]=PS&length=5"
)
EIA_SUBBA_URL = (
    "https://api.eia.gov/v2/electricity/rto/region-sub-ba-data/?api_key=DEMO_KEY"
)
OUTLOOK_URL = "https://www.caiso.com/outlook/history/{day}/fuelsource.csv"
STORAGE_URL = "https://www.caiso.com/outlook/history/{day}/storage.csv"
CDEC_META_URL = "https://cdec.water.ca.gov/dynamicapp/staMeta?station_id={sta}"
OASIS_SLRS_URL = (
    "https://oasis.caiso.com/oasisapi/SingleZip?queryname=ENE_SLRS"
    "&startdatetime=20250101T08:00-0000&enddatetime=20250102T08:00-0000"
    "&version=1&resultformat=6"
)

# Reservoir stations backing the model's six CAISO PS plants (CDEC ids from
# https://cdec.water.ca.gov/misc/resinfo.html). Helms cycles Courtright<->
# Wishon; Eastwood cycles Shaver<->Balsam Meadow forebay (Shaver is the
# CDEC-listed reservoir); Gianelli cycles San Luis<->O'Neill Forebay; Hyatt/
# Thermalito cycle Oroville<->Thermalito.
CDEC_STATIONS = {
    "CTG": "Courtright (Helms upper)",
    "WSN": "Wishon (Helms lower)",
    "SHV": "Shaver (Eastwood)",
    "SNL": "San Luis (Gianelli)",
    "ORO": "Oroville (Hyatt)",
    "TAB": "Thermalito Afterbay",
}


def _get(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def s1_eia_ps() -> None:
    facets = json.loads(_get(EIA_FACET_URL))["response"]["facets"]
    ids = sorted({f["id"] for f in facets})
    has_ps = "PS" in ids
    rows = json.loads(_get(EIA_CISO_PS_URL))["response"]["total"]
    print(f"S1 EIA-930: fueltype facet ids = {ids}")
    print(f"S1 EIA-930: API carries a PS category: {has_ps}; CISO PS rows = {rows}")
    print(
        "S1 verdict:",
        "unchanged (WALL: CISO reports 0 PS rows)"
        if int(rows) == 0
        else "CHANGED — CISO now reports PS; re-open A2",
    )


def s2_outlook_netting(
    days: tuple[str, ...] = ("20250415", "20251015", "20250115"),
) -> None:
    wat = pd.read_parquet(REPO / "data/raw/CISO_fueltype.parquet")
    wat = wat[wat.fueltype == "WAT"].set_index("period")["value_mwh"]
    frames, minima = [], {}
    for day in days:
        df = pd.read_csv(io.StringIO(_get(OUTLOOK_URL.format(day=day)).decode()))
        ts = pd.to_datetime(day) + pd.to_timedelta(df["Time"] + ":00")
        df.index = ts.dt.tz_localize("America/Los_Angeles").dt.tz_convert("UTC")
        hyd = df["Large Hydro"] + df["Small hydro"]
        minima[day] = float(hyd.min())
        frames.append(hyd.resample("1h").mean())
    hyd = pd.concat(frames)
    cmp = (
        pd.DataFrame({"o": hyd})
        .join(wat.shift(-1, freq="h").rename("w"), how="inner")
        .dropna()
    )
    corr = float(cmp.o.corr(cmp.w))
    mad = float((cmp.o - cmp.w).abs().mean())
    print(f"S2 Outlook: per-day hydro minima (MW) = {minima}")
    print(
        f"S2 Outlook vs 930 WAT (hour-ending aligned): n={len(cmp)} corr={corr:.3f} mean|diff|={mad:.0f} MW"
    )
    net = min(minima.values()) < 0 and corr > 0.9
    print(
        "S2 verdict:",
        "unchanged (WALL: Outlook hydro is the same PS-NET feed as WAT)"
        if net
        else "CHANGED — netting basis differs; re-examine",
    )


def s3_storage_page(day: str = "20251015") -> None:
    cols = pd.read_csv(
        io.StringIO(_get(STORAGE_URL.format(day=day)).decode())
    ).columns.tolist()
    print(f"S3 Outlook storage.csv columns = {cols}")
    ps = [c for c in cols if "pump" in c.lower()]
    print(
        "S3 verdict:",
        "unchanged (WALL: battery-only)"
        if not ps
        else f"CHANGED — PS columns appeared: {ps}",
    )


def s4_cdec_hourly() -> None:
    walled = True
    for sta, label in CDEC_STATIONS.items():
        html = _get(CDEC_META_URL.format(sta=sta)).decode(errors="replace")
        rows = re.findall(r"<tr>.*?</tr>", html, re.S)
        hourly = []
        for r in rows:
            cells = [
                re.sub(r"<[^>]+>", "", c).strip()
                for c in re.findall(r"<td.*?</td>", r, re.S)
            ]
            if cells and any("hourly" in c.lower() for c in cells):
                hourly.append(f"{cells[0]} [{cells[1]}] {cells[-1]}")
        print(f"S4 CDEC {sta} ({label}): {len(hourly)} hourly sensors")
        for h in hourly:
            print(f"      {h}")
        if sta in ("CTG", "WSN", "SHV") and hourly:
            walled = False
    print(
        "S4 verdict:",
        "unchanged (WALL: no hourly telemetry at CTG/WSN/SHV — Helms+Eastwood uninstrumented)"
        if walled
        else "CHANGED — PG&E/SCE hourly telemetry appeared; re-open A2",
    )


def s5_subba() -> None:
    meta = json.loads(_get(EIA_SUBBA_URL))["response"]
    data_cols = sorted(meta.get("data", {}).keys())
    facet_ids = sorted(f["id"] for f in meta.get("facets", []))
    print(f"S5 EIA-930 sub-BA route: data columns = {data_cols}, facets = {facet_ids}")
    print(
        "S5 verdict:",
        "unchanged (WALL: demand-only, no fuel facet)"
        if data_cols == ["value"] and "fueltype" not in facet_ids
        else "CHANGED",
    )


def s6_oasis() -> None:
    import zipfile

    buf = io.BytesIO(_get(OASIS_SLRS_URL, timeout=120))
    with zipfile.ZipFile(buf) as z:
        name = z.namelist()[0]
        df = pd.read_csv(z.open(name))
    items = sorted(df["XML_DATA_ITEM"].unique())
    print(f"S6 OASIS ENE_SLRS data items = {items}")
    print(
        "S6 verdict:",
        "unchanged (WALL: system totals only)"
        if not any("PUMP" in i.upper() for i in items)
        else "CHANGED — pumping item appeared",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--oasis",
        action="store_true",
        help="also re-fetch the OASIS ENE_SLRS check (slow, rate-limited)",
    )
    args = ap.parse_args()
    s1_eia_ps()
    s2_outlook_netting()
    s3_storage_page()
    s4_cdec_hourly()
    s5_subba()
    if args.oasis:
        s6_oasis()
    print("survey complete — see FINDING-caiso141-water-intake-walled-2026-07-30.md")


if __name__ == "__main__":
    sys.exit(main())
