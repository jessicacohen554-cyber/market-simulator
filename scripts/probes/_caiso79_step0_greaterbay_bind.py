"""STEP-0 (caiso-79, no LP): Greater Bay LCT import-cap ex-ante bind test.

Decide-before-solving gate for the CT_PEAKER local-commitment granularity lane
(docs/handoffs/caiso-79-next-run-plan-2026-07-12.md §3): with the measured
Greater Bay import capability ``import_cap = peak_load − LCR`` from the CAISO
Final LCT reports (2023: 11,136 − 7,312 = 3,824; 2024: 11,081 − 7,329 = 3,752;
2025: 11,992 − 7,441 = 4,551 MW), does the pocket's evening residual
``GB_load(h) − import_cap − in-pocket non-CT supply`` go positive often enough
to call ~0.4–1 GW of CT? (The LA_BASIN lesson: an LCT cap ≈ pocket load never
binds — this verifies Greater Bay is tighter BEFORE building the NP15 split.)

Measured inputs only, no LP and no derived artifact (rule-15 visibility —
prints, writes nothing):

* Pocket membership: county rule (San Francisco / San Mateo / Santa Clara /
  Alameda / Contra Costa wholly inside) + the LCT area-definition substation
  rule for boundary plants — "Moss Landing is in" (Monterey), "Lambie SW Sta
  is in" (Solano Lambie-bus peakers) — Final 2023 LCT §3.3.5.1.
* Pocket hourly load: measured PGE-TAC hourly (zone-specific-demand raw) ×
  the LCT planning share (GB Load+Losses+Pumps ÷ NP26 Table 3.2-1 forecast:
  0.537 / 0.531 / 0.567) — same planning-basis pairing as the committed
  LA Basin / SDGE peak_load rows.
* In-pocket supply: CAMPD net hourly per plant (parasitic-scaled), split
  CT_PEAKER vs non-CT on the committed bench part's own class map; the
  non-CEMS block (battery / MUNI-QF / wind / DR "At Peak" credits from the
  LCT area table) enters as a static bound, reported both ways.

Residuals reported:
* resid_A — non-CT thermal at its MEASURED output (+ static credit): does
  reality's own non-CT dispatch leave a gap only CT can fill, and does that
  gap match the measured GB CT output (the caiso-72 ~388 MW evening signal)?
* resid_B — non-CT thermal at CAPACITY × 0.93 availability (+ static
  credit): even with every non-CT resource maxed, must CT run? (The strong
  form: if this binds, no import/CC re-dispatch can substitute for pocket CT.)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (_REPO / "src", _REPO, _REPO / "scripts"):
    sys.path.insert(0, str(_p))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, str(_REPO / rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rcf = _load("rcf", "scripts/run_calibration_full.py")

import base64  # noqa: E402
import gzip  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402

YEARS = (2023, 2024, 2025)
T = 8760
# Final LCT report measured parameters (Table 3.3-29/-27 Load+Losses+Pumps;
# LCR requirement rows already committed in capacity-deliverability csv).
GB = {
    2023: dict(peak=11136.0, lcr=7312.0, np26=20748.0, static=1616.0, battery=932.0),
    2024: dict(peak=11081.0, lcr=7329.0, np26=20867.0, static=1912.0, battery=982.0),
    2025: dict(peak=11992.0, lcr=7441.0, np26=21140.0, static=2254.0, battery=1337.0),
}
GB_COUNTIES = {"San Francisco", "San Mateo", "Santa Clara", "Alameda", "Contra Costa"}
# SP26 zonal forecast peaks (Table 3.2-1) for the whole-CAISO share fallback.
GB_SP26 = {2023: 28149.0, 2024: 28310.0, 2025: 27736.0}
# LCT §3.3.5.1 substation rule: Moss Landing bus is IN (Monterey county);
# Lambie SW Sta is IN (Solano county Lambie-bus peakers). Names matched on
# the EIA-860 plant table.
SUBSTATION_IN_PLANTS = {260}  # Moss Landing
SUBSTATION_IN_NAME_PAT = re.compile(
    r"lambie|goose ?haven|creed", re.IGNORECASE
)  # Solano Lambie-bus LM6000s
EVENING = list(range(17, 23))  # HE18-23 local (hour-beginning 17-22)
NONCT_AVAIL = 0.93  # strong-form availability on non-CT thermal capacity

plant860 = pd.read_parquet(_REPO / "data/raw/eia-860/eia860_plant.parquet")
plant860 = plant860[["Plant Code", "Plant Name", "County", "State"]].rename(
    columns={"Plant Code": "pid", "Plant Name": "name", "County": "county"}
)
plant860["pid"] = plant860["pid"].astype(int)
p_county = dict(zip(plant860["pid"], plant860["county"].astype(str)))
p_name = dict(zip(plant860["pid"], plant860["name"].astype(str)))

parasitic = rcf._parasitic_factor_map()
cfg = get_iso_config("CAISO")

# caiso-78 payload (model side, the scorers' own decode) for the contrast row.
raw = (_REPO / "frontend/data/backcast/runs/2026-07-12-caiso-78-cc-hr.js").read_text()
pay = json.loads(
    gzip.decompress(
        base64.b64decode(re.search(r'runGz\["[^"]+"\]="([^"]+)"', raw).group(1))
    )
)


def _dec(b64s: str, cap: float) -> np.ndarray:
    a = np.frombuffer(base64.b64decode(b64s), dtype=np.uint8).astype(float)
    return a[:T] * cap / 100.0


def _gb_member(pid: int, name: str) -> str | None:
    if pid in SUBSTATION_IN_PLANTS or SUBSTATION_IN_NAME_PAT.search(name or ""):
        return "substation-rule"
    if p_county.get(pid) in GB_COUNTIES:
        return "county-rule"
    return None


for year in YEARS:
    g = GB[year]
    import_cap = g["peak"] - g["lcr"]
    share = g["peak"] / g["np26"]

    part = json.loads(
        gzip.decompress(
            (_REPO / f"frontend/data/backcast/bench/CAISO/{year}.json.gz").read_bytes()
        )
    )
    bp = part["bench"]["plants"]

    # Pocket hourly load. Primary basis: measured PGE-TAC hourly × the GB
    # planning share of NP26. The committed 2023 TAC file covers January only
    # (744 h), so 2023 falls back to the EIA-930 CISO Demand hourly × the GB
    # planning share of the WHOLE-CAISO forecast peak (NP26+SP26); 2024 prints
    # both bases so the fallback's bias is visible.
    tac = pd.read_csv(
        _REPO / f"data/raw/zone-specific-demand/CAISO/CAISO_tac_load_hourly_{year}.csv"
    )
    tac = tac[tac["tac_area"] == "PGE-TAC"].copy()
    ts = pd.to_datetime(tac["interval_start_gmt"], utc=True).dt.tz_convert(
        ZoneInfo("America/Los_Angeles")
    )
    tac["hoy"] = (ts.dt.dayofyear - 1) * 24 + ts.dt.hour
    pge_hours = tac["hoy"].nunique()
    pge = (
        tac.groupby("hoy")["mw"]
        .mean()
        .reindex(range(T))
        .ffill()
        .bfill()
        .to_numpy(float)
    )
    # CISO demand = net_gen − interchange (930 sign: net-export positive).
    e930 = rcf._eia930_frame(year, "CAISO", cfg)
    _ng = e930[e930["series"] == "net_gen"].sort_values("hour")["mw"].to_numpy(float)
    _ix = (
        e930[e930["series"] == "interchange"].sort_values("hour")["mw"].to_numpy(float)
    )
    ciso_dem = (_ng - _ix) if (_ng.size == T and _ix.size == T) else None
    share_ciso = g["peak"] / (g["np26"] + GB_SP26[year])
    gb_load_tac = share * pge
    gb_load_930 = share_ciso * ciso_dem if ciso_dem is not None else None
    if pge_hours >= 8000:
        gb_load = gb_load_tac
        basis = f"PGE-TAC × {share:.3f}"
    else:
        gb_load = gb_load_930
        basis = f"EIA-930 CISO demand × {share_ciso:.3f} (TAC file has {pge_hours} h)"

    campd = rcf._campd_hourly_frame(year, "CAISO", parasitic, T)
    cn = {}
    for pid, gg in campd.groupby("plant_id"):
        a = np.nan_to_num(gg.sort_values("hour")["net_mw"].to_numpy(float))
        cn[int(pid)] = np.concatenate([a, np.zeros(max(0, T - a.shape[0]))])[:T]

    ct = np.zeros(T)
    nonct = np.zeros(T)
    ct_cap = nonct_cap = 0.0
    members = []
    model_gb = np.zeros(T)
    ypay = pay["years"].get(str(year), {})
    for code, q in bp.items():
        pid = int(code)
        rule = _gb_member(pid, p_name.get(pid, q.get("name", "")))
        if rule is None:
            continue
        members.append((pid, q["name"], q["group"], q["npl"], rule))
        series = cn.get(pid, np.zeros(T))
        if q["group"] == "CT_PEAKER":
            ct += series
            ct_cap += float(q["npl"])
        else:
            nonct += series
            nonct_cap += float(q["npl"])
        pp = (ypay.get("plants") or {}).get(code)
        if pp and pp.get("m"):
            model_gb += _dec(pp["m"], float(q["npl"]))

    hod = np.arange(T) % 24
    eve = np.isin(hod, EVENING)
    resid_a = gb_load - import_cap - nonct - g["static"]
    resid_b = gb_load - import_cap - NONCT_AVAIL * nonct_cap - g["static"]
    resid_b_nobat = resid_b + g["battery"]  # strong form w/o any battery credit

    def _st(x, sel):
        v = x[sel]
        return (
            f"p50 {np.percentile(v, 50):7.0f}  p90 {np.percentile(v, 90):7.0f}  "
            f"max {v.max():7.0f}  >0 share {(v > 0).mean() * 100:5.1f}%"
        )

    print(f"\n===== {year} =====")
    print(
        f" GB peak {g['peak']:.0f}  LCR {g['lcr']:.0f}  import_cap {import_cap:.0f}"
        f"  NP26 share {share:.3f}  static credit {g['static']:.0f}"
    )
    print(
        f" members: {len(members)} plants — CT cap {ct_cap:.0f} MW, "
        f"non-CT cap {nonct_cap:.0f} MW"
    )
    print(f" GB load evening: {_st(gb_load, eve)}")
    print(f" measured GB CT gen evening: {_st(ct, eve)}")
    print(f" measured GB non-CT gen evening: {_st(nonct, eve)}")
    print(f" model (caiso-78) GB thermal evening: {_st(model_gb, eve)}")
    print(f" resid_A (non-CT at ACTUAL) evening: {_st(resid_a, eve)}")
    print(f" resid_A all hours: {_st(resid_a, np.ones(T, bool))}")
    print(
        f" resid_B (non-CT at {NONCT_AVAIL:.0%} CAPACITY) evening: {_st(resid_b, eve)}"
    )
    print(f" resid_B all hours: {_st(resid_b, np.ones(T, bool))}")
    print(
        f" resid_B w/o battery credit all hours: {_st(resid_b_nobat, np.ones(T, bool))}"
    )
    print(f" load basis: {basis}")
    if gb_load_930 is not None and pge_hours >= 8000:
        d = gb_load_930 - gb_load_tac
        print(f" basis cross-check (930-based − TAC-based): {_st(d, eve)}")
    if year == 2023:
        print(" membership:")
        for pid, name, grp, npl, rule in sorted(members, key=lambda x: -x[3]):
            print(f"   {pid:6d} {name[:42]:42s} {grp:11s} {npl:6.0f} MW  {rule}")
