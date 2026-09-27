#!/usr/bin/env python
"""R-CAISO-8 — San Diego (SDGE zone) realized net-import census vs the LCT planning cap.

ZERO-LP probe. Question: is the per-year LCT ``peak_load − requirement`` value that
``caiso_per_year_import_caps`` applies as an all-hours one-way TTC on
``SP15_rest → SDGE`` an OPERATING limit? If the measured SDGE system imports more
than that value in real hours, it is not (rule 14 `[R-ACCURATE]` misalignment
exception: a 1-in-10 N-1-1 planning-case capability is a different quantity from
the operating transfer limit the LP link represents).

Measured inputs (no model output is read):

* SDGE load — CAISO OASIS TAC-area hourly actual load, ``SDGE-TAC``
  (``data/raw/zone-specific-demand/CAISO/CAISO_tac_load_hourly_<Y>.csv``).
* In-zone thermal generation — CAMPD hourly unit ``grossLoad`` (gross ≥ net, so
  it OVERSTATES in-zone output) for every CAMPD facility whose ORIS code is an
  EIA-860 plant in San Diego or Imperial county with Balancing Authority CISO
  (the model's SDGE county set, ``zone_assignment.CAISO_SDGE_COUNTIES``).
* In-zone non-CAMPD capacity — EIA-860 operable nameplate (vintage = solve year;
  2025 uses the top-level 2025 early release) of every non-solar generator at a
  CISO plant in those counties that is not a combustion unit at a CAMPD plant
  (batteries, wind, hydro/pumped storage, small gas, biomass …).

Two measured brackets on realized net import into SDGE, per hour:

* ``import_lb`` (NIGHT hours only, hour-beginning 21:00–04:59 local standard
  time, solar ≡ 0): load − CAMPD gross − ALL non-CAMPD non-solar nameplate.
  Every in-zone MW is over-counted, so this is a strict LOWER bound on realized
  import, hence a revealed lower bound on the operating capability.
* ``import_ub`` (all hours): load − CAMPD gross. Ignores renewables/storage, so
  an UPPER bound on realized import (context only — never evidence of capability).

Optional OASIS census (``--oasis``): DAM ``PRC_NOMOGRAM`` binding-constraint
hours, per year, for every constraint of CAISO Operating Procedure 7820
("San Diego Area"; ids prefixed ``7820_``), cached under the out dir.

Output: ``results/calibration/_rcaiso8/object2_sd_census.json``.
"""

from __future__ import annotations

import argparse
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, RESULTS_ROOT

YEARS = list(range(2019, 2026))
LCT_CSV = RAW_DATA_DIR / "capacity-deliverability" / "caiso" / "caiso.csv"
LCT_AREA = "San Diego/Imperial Valley"
# 2022 LCT SD-IV row is not landed in caiso.csv (R-CAISO-7 Object 2). Values
# read from the Final 2022 LCT report, Table 3.3-83 (Load+Losses+Pumps 4,580)
# and Table 3.3-91 (P3 LCR 3,993):
# https://www.caiso.com/Documents/Final2022LocalCapacityTechnicalReport.pdf
LCT_2022_FALLBACK = {"peak_load": 4580.0, "requirement": 3993.0}
SD_COUNTIES = ("San Diego", "Imperial")
COMBUSTION_PM = {"CT", "CA", "CS", "ST", "GT", "IC", "CC"}
NIGHT_HOURS_LST = {21, 22, 23, 0, 1, 2, 3, 4}  # hour-beginning, local standard time
OASIS = "https://oasis.caiso.com/oasisapi/SingleZip"
# CAMPD reports the Carlsbad Energy Center CTs (EIA-860 plant 59002, San Diego
# county, CISO) under the retired Encina station's ORIS 302 (measured: CA_2019..
# CA_2025 carry facilityId 302 "Cabrillo Power I Encina Power Station" with
# 336-443 GWh/yr, while no facilityId 59002 exists). Alias both ways so the CTs
# are MEASURED rather than counted at nameplate.
CAMPD_ORIS_ALIAS = {302: 59002}


def lct_caps() -> dict[int, dict]:
    """Return per-year SD-IV LCT peak, requirement and implied import cap."""
    d = pd.read_csv(LCT_CSV)
    d = d[(d.area == LCT_AREA) & (d.season == "annual")]
    out = {}
    for y in YEARS:
        r = d[d.delivery_year == y].set_index("metric")["value_mw"]
        if "peak_load" in r and "requirement" in r:
            pk, req, src = float(r["peak_load"]), float(r["requirement"]), "caiso.csv"
        elif y == 2022:
            pk, req = LCT_2022_FALLBACK["peak_load"], LCT_2022_FALLBACK["requirement"]
            src = "Final2022 LCT report (not landed in caiso.csv)"
        else:
            continue
        out[y] = {"peak_load": pk, "requirement": req, "lct_cap_mw": pk - req, "source": src}
    return out


def sdge_load(year: int) -> pd.Series:
    """SDGE-TAC hourly load (MW) indexed by UTC hour."""
    d = pd.read_csv(RAW_DATA_DIR / "zone-specific-demand" / "CAISO" / f"CAISO_tac_load_hourly_{year}.csv")
    d = d[d.tac_area == "SDGE-TAC"]
    idx = pd.to_datetime(d.interval_start_gmt, utc=True).dt.floor("h")
    s = pd.Series(d.mw.to_numpy(float), index=idx)
    return s.groupby(level=0).mean()


def eia860(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """EIA-860 plant + operable-generator tables at the solve-year vintage."""
    base = RAW_DATA_DIR / "eia-860"
    vdir = base / f"vintage_{year}"
    if not (vdir / "eia860_plant.parquet").exists():
        vdir = base
    return (pd.read_parquet(vdir / "eia860_plant.parquet"),
            pd.read_parquet(vdir / "eia860_generator_operable.parquet"))


def in_zone_fleet(year: int, campd_ids: set[int]) -> dict:
    """In-zone CISO plant codes and non-CAMPD non-solar nameplate (MW)."""
    plant, gen = eia860(year)
    p = plant[(plant.State == "CA") & plant.County.isin(SD_COUNTIES)
              & (plant["Balancing Authority Code"] == "CISO")]
    codes = set(pd.to_numeric(p["Plant Code"], errors="coerce").dropna().astype(int))
    for campd_id, eia_id in CAMPD_ORIS_ALIAS.items():
        if eia_id in codes:
            codes.add(campd_id)
            if campd_id in campd_ids:
                campd_ids = campd_ids | {eia_id}
    g = gen[pd.to_numeric(gen["Plant Code"], errors="coerce").isin(codes)].copy()
    g["pc"] = pd.to_numeric(g["Plant Code"]).astype(int)
    g["mw"] = pd.to_numeric(g["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0)
    tech = g.Technology.fillna("")
    solar = tech.str.contains("Solar")
    measured = g.pc.isin(campd_ids) & g["Prime Mover"].isin(COMBUSTION_PM)
    rest = g[~solar & ~measured]
    return {
        "plant_codes": codes,
        "non_campd_nonsolar_mw": float(rest.mw.sum()),
        "non_campd_nonsolar_by_tech_mw": rest.groupby("Technology").mw.sum().round(1).to_dict(),
        "solar_mw": float(g[solar].mw.sum()),
        "campd_combustion_nameplate_mw": float(g[measured].mw.sum()),
    }


def campd_gross(year: int, codes: set[int]) -> tuple[pd.Series, list[str]]:
    """CAMPD hourly gross MW summed over in-zone facilities, indexed by UTC hour."""
    c = pd.read_parquet(RAW_DATA_DIR / "campd-unit-level" / f"CA_{year}.parquet",
                        columns=["facilityId", "facilityName", "date", "hour", "grossLoad"])
    c = c.assign(facilityId=pd.to_numeric(c.facilityId, errors="coerce"))  # CAMPD ships ORIS as str
    c = c[c.facilityId.isin(codes)]
    # CAMPD reports local STANDARD time (UTC-8 for California).
    ts = (pd.to_datetime(c.date) + pd.to_timedelta(c.hour, unit="h")).dt.tz_localize("Etc/GMT+8")
    utc = pd.DatetimeIndex(ts.dt.tz_convert("UTC"))
    s = pd.Series(c.grossLoad.fillna(0.0).to_numpy(float), index=utc).groupby(level=0).sum()
    return s, sorted(c.facilityName.unique().tolist())


def pct(x: np.ndarray) -> dict:
    """p50/p95/p99/max summary."""
    if x.size == 0:
        return {}
    return {k: round(float(v), 1) for k, v in zip(
        ("p50", "p95", "p99", "max"), np.percentile(x, [50, 95, 99, 100]))}


def oasis_7820_hours(year: int, cache: Path) -> dict:
    """DAM PRC_NOMOGRAM hours per 7820_* (San Diego Area OP) constraint for ``year``."""
    cache.mkdir(parents=True, exist_ok=True)
    frames = []
    empty_months = []
    for m in range(1, 13):
        s0 = pd.Timestamp(year, m, 1, 8)
        e0 = (s0 + pd.offsets.MonthBegin(1)).replace(hour=8)
        mid = s0 + pd.Timedelta(days=15)
        # Two half-month chunks: OASIS returns an XML error (no zip CSV) for some
        # full-month DAM windows (measured: May/Jul/Aug/Oct every year).
        for tag, s, e in (("a", s0, mid), ("b", mid, e0)):
            f = cache / f"prc_nomogram_dam_{year}{m:02d}{tag}.csv"
            if not f.exists():
                url = (f"{OASIS}?queryname=PRC_NOMOGRAM&market_run_id=DAM&version=1&resultformat=6"
                       f"&startdatetime={s:%Y%m%dT%H:%M}-0000&enddatetime={e:%Y%m%dT%H:%M}-0000")
                for attempt in range(4):
                    try:
                        raw = urllib.request.urlopen(url, timeout=180).read()
                        zf = zipfile.ZipFile(io.BytesIO(raw))
                        name = zf.namelist()[0]
                        if name.endswith(".xml"):  # OASIS error payload: retry
                            raise ValueError(zf.read(name)[:300])
                        f.write_bytes(zf.read(name))
                        break
                    except Exception:  # noqa: BLE001 — OASIS rate-limit / transient
                        time.sleep(10 * (attempt + 1))
                time.sleep(6)
            if f.exists():
                frames.append(pd.read_csv(f, usecols=lambda c: c in {"NOMOGRAM_ID_XML", "OPR_DT", "OPR_HR", "PRC"}))
            else:
                empty_months.append(f"{year}-{m:02d}{tag}")
    if not frames:
        return {"status": "no data"}
    d = pd.concat(frames)
    d = d[d.NOMOGRAM_ID_XML.astype(str).str.startswith("7820_")]
    d = d[d.PRC.abs() > 0]
    by = d.groupby("NOMOGRAM_ID_XML").apply(lambda x: x[["OPR_DT", "OPR_HR"]].drop_duplicates().shape[0])
    hours_any = d[["OPR_DT", "OPR_HR"]].drop_duplicates().shape[0]
    return {"half_months_cached": len(frames), "half_months_missing": empty_months, "hours_any_7820_binding": int(hours_any),
            "hours_by_constraint": {k: int(v) for k, v in by.sort_values(ascending=False).items()}}


def main() -> None:
    """Run the census and write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=RESULTS_ROOT / "calibration" / "_rcaiso8" / "object2_sd_census.json")
    ap.add_argument("--oasis", action="store_true", help="fetch/cache OASIS DAM PRC_NOMOGRAM (7820_*)")
    a = ap.parse_args()
    caps = lct_caps()
    res = {"method": __doc__.split("Output:")[0].strip(), "years": {}}
    for y in YEARS:
        load = sdge_load(y)
        all_codes = set(pd.read_parquet(RAW_DATA_DIR / "campd-unit-level" / f"CA_{y}.parquet",
                                        columns=["facilityId"]).facilityId.pipe(pd.to_numeric, errors="coerce").dropna().astype(int).unique())
        fleet = in_zone_fleet(y, all_codes)
        gross, fac = campd_gross(y, fleet["plant_codes"])
        df = pd.DataFrame({"load": load}).join(gross.rename("campd"), how="left").fillna({"campd": 0.0})
        df = df.dropna()
        lst_hour = (df.index - pd.Timedelta(hours=8)).hour
        night = df[np.isin(lst_hour, list(NIGHT_HOURS_LST))]
        imp_lb = (night.load - night.campd - fleet["non_campd_nonsolar_mw"]).to_numpy()
        imp_ub = (df.load - df.campd).to_numpy()
        cap = caps.get(y, {}).get("lct_cap_mw")
        row = {
            "hours": int(len(df)), "night_hours": int(len(night)),
            "sdge_load_mw": pct(df.load.to_numpy()),
            "campd_facilities": fac,
            "campd_gross_mw": pct(df.campd.to_numpy()),
            "fleet": {k: v for k, v in fleet.items() if k != "plant_codes"},
            "import_lb_night_mw": pct(imp_lb),
            "import_ub_allhours_mw": pct(imp_ub),
            "lct": caps.get(y),
        }
        if cap is not None:
            row["night_hours_import_lb_exceeds_lct_cap"] = int((imp_lb > cap).sum())
            row["share_night_hours_import_lb_exceeds_lct_cap"] = round(float((imp_lb > cap).mean()), 4)
            row["max_import_lb_over_lct_cap_mw"] = round(float(imp_lb.max() - cap), 1)
            row["allhours_import_ub_exceeds_lct_cap"] = int((imp_ub > cap).sum())
        if a.oasis:
            row["oasis_dam_7820"] = oasis_7820_hours(y, a.out.parent / "oasis_cache")
        res["years"][y] = row
        print(y, json.dumps({k: row[k] for k in row if k not in ("campd_facilities", "fleet", "method")}, default=str))
    res["candidate_operating_limits"] = {
        "WECC_Path_45_SDGE_CFE_S_to_N_mw": {
            "value": 800.0, "note": "CFE->SDG&E import leg only (Tijuana I-Otay Mesa + La Rosita-IV); not the SD boundary",
            "source": "WECC 2026 Path Rating Catalog Public V4, Path 45 (p.44)"},
        "CAISO_SDGE_SIL_post_Sunrise_2008_assumption": {
            "value": 4200.0, "n1_g1_value": 3500.0,
            "note": "CAISO planning ASSUMPTION for post-Sunrise SDG&E Simultaneous Import Limit, all lines in service "
            "(N-0); G-1/N-1 non-simultaneous 3,500 MW. Pre-dates Sunrise energization (2012) and SONGS retirement "
            "(2013); not a measured operating limit and not per-year",
            "source": "CPUC D.08-12-058 (Sunrise CPCN), https://docs.cpuc.ca.gov/publishedDocs/published/FINAL_DECISION/95750.htm, fn 331"},
        "WECC_Path_44_South_of_SONGS": {"value": None, "note": "path DELETED from the catalog Feb 2015 (post-SONGS)"},
        "CAISO_OP_7820_SDGE_import_nomogram": {
            "value": None, "note": "control points 'SDGE import' / 'SDGE/CFE import' exist (OP 2210Z Table 3A for 7820) "
            "but OP 7820 is flagged non-public (market/proprietary/system sensitive) in the OP index"},
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1, default=str))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
