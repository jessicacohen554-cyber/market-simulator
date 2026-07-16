"""PJM C3c congestion-surface decomposition (pjm-cong-1, no-LP, measured) —
the exact scarcity-hour tranches per year and zone, the model-vs-CAMPD
dispatch phantom inside them, and the measured-interface-limit materiality
adjudication for the flat zonal surface (diagnosis §5/§8.1 boundary).

Everything is computed from committed artifacts + raw measured data only
(no solve, no config flip — rule 1 diagnostic-first):

  * model side: the committed pjm-113 keeper payload
    (frontend/data/backcast/runs/2026-07-16-pjm-113-short-only.js — per-plant
    hourly LP dispatch, hourly system-price delta, zonal MONTHLY duals; the
    payload carries no hourly zonal duals and no link flows, so the east-cut
    section reconstructs the model's import requirement from the payload
    dispatch + the model's own input constructions, with every non-exact term
    bounded and biased AGAINST materiality);
  * actual side: data/raw/_validation-source/actual_lmp_hourly_PJM.parquet
    (chronological system DA/RT), data/raw/lmp-data/PJM_<yr>_rt_da_monthly_
    lmps.csv (12 hubs hourly DA/RT — the ZONAL scarcity record),
    frontend/data/backcast/bench/PJM/<yr>.json.gz (CAMPD plant hourly),
    data/raw/iso-specific-transmission/PJM_<yr>_transfer_limits_and_flows.csv
    (the ten measured interface limit+flow series), data/raw/
    zone-specific-demand/PJM<yr>_hrl_load_metered.csv (settlement zonal load),
    EIA-930 via the canonical benchmark loader.

Interface identity (PJM Manual 03 §3.8, Rev 71 eff. 2026-05-20 — verified
this session, superseding the constants.py "regional envelope" reading):
the feed's series are PJM's named REACTIVE TRANSFER INTERFACES, each a
defined 500/345 kV line set whose TLC limit is recomputed ~5-min and posted
hourly ("Average X" = the hour's average posted limit for interface X):

  Eastern   = 5059/5058 Breinigsville-Alburtis, 5009 Juniata-Alburtis,
              5066 Lauschtown-Hosensack, 5010 Peach Bottom-Limerick,
              5025 Rock Springs-Keeney, 5063 Lackawanna-Hopatcong
              -> the EHV cut into the eastern Mid-Atlantic (our EMAAC import
              boundary, spanning BOTH the Central_PA->EMAAC and the
              SWMAAC-side paths).
  Central   = 5004 Keystone-Juniata, 5005 Conemaugh-Juniata,
              5012 Conastone-Peach Bottom.
  5004/5005 = the two Keystone/Conemaugh-Juniata circuits alone — a
              WESTERN-PA->CENTRAL-PA corridor interface. The committed
              crosswalk applies it to ComEd->AEP_Ohio (Illinois!): a
              mis-attribution, measured here for the record.
  Western   = 5004 + 5005 + 5068 Vinco-Hunterstown + 5055/522 Doubs-Brighton.
  AP-South  = 583 Bismark-Doubs, 540 Greenland Gap-Meadow Brook,
              550 Mt Storm-Valley, 529 Mt Storm-Meadow Brook (WV->VA/MD).
  Bed-Bla   = 544 Black Oak-Bedington. AEP-DOM = Kanawha-Matt Funk 345,
              Wyoming-Jacksons Ferry 765, Baker-Broadford 765.
  Cleveland = the ATSI-Cleveland pocket import set (deliberately unmapped).
  (BC/PEPCO — the SWMAAC import cut — and CE-East — the ComEd import cut —
  exist in Manual 03 but are NOT in the DataMiner2 feed.)

PRE-DECLARED STOP CONDITION (pjm-cong-1 charter; fixed in this header BEFORE
the eastcut section was first executed, never moved after — the §5 style):

  The surface lane is MATERIAL for measured interface limits iff, over the
  22 summer-2025 DA-tail hours, the model's implied INTERNAL east-cut import
  requirement R_int(t) exceeds the measured cut limit (the Eastern reactive
  interface hourly series, reconciled as the joint EMAAC import cut across
  Central_PA->EMAAC + SWMAAC->EMAAC) in >= 8 of the 22 hours, with median
  exceedance >= 300 MW over the exceeding hours, under the CENTRAL estimate:
    - PS/hydro inside the cut at FULL discharge (anti-material bias: scarcity
      posture maximizes in-cut supply),
    - the model seam posture the run's own economics imply (2025 NYISO import
      rungs all $502.65 > every model tail price => zero seam import into
      EMAAC; the measured firm-export floor 1,650 MW is reported both ways
      rather than assumed),
    - non-CAMPD fossil (oil/biomass/small CT) at the 930 system oil/other
      dispatch scaled by the zone's capacity share (reality's own posture).
  Rationale for the numbers: 8 h is the minimum count that could carry
  C3c-2025 from 18 h to the 26-h gate floor if every binding hour converts
  (necessary, not sufficient — sufficiency is the LP's to prove under the
  Phase-2 gate); 300 MW is a degeneracy guard (less than one mid-merit unit
  cannot plausibly re-price a $21-89 gap). If the condition fails, the lane
  is NOT closable by measured interface limits: the null goes into the
  diagnosis, nothing is registered, the session stops (charter stop rule).

Sections (run all by default, or --section NAME):

  roster        per year 2023-2025: the exact DA>$200 scarcity tranche —
                system hours (timestamps) + per-hub counts (the ZONAL
                tranche) + model any-zone/load-weighted counts.
  events        per tail hour: each hub's DA premium over the hub mean
                (east-west spread anatomy), model system price, per-event
                aggregates; the model's monthly zonal-dual premiums printed
                alongside (the only zonal grain the payload carries).
  zonalphantom  per year, zone x class model-minus-CAMPD MW inside that
                year's tail hours (the dispatch phantom by zone), with top
                plant rows — the user-facing "what are we dispatching in
                scarcity hours vs what actually ran".
  interfaces    the ten measured series inside each year's tail hours:
                limit vs transfers vs utilization, event derates vs summer
                norms, annual binding shares — plus the corrected Manual-03
                crosswalk table for the record.
  eastcut       the adjudication: reconstructed model EMAAC-cut (and MAD-cut)
                import requirement vs the measured Eastern (and AP-South +
                AEP-DOM + Eastern) limits over the 22 tail hours; actual-side
                cross-validation of the reconstruction against the feed's own
                measured transfers; verdict vs the pre-declared threshold.

Usage: .venv/bin/python scripts/probes/_pjm_c3c_congestion_surface_decomp.py
           [--run-id 2026-07-16-pjm-113-short-only] [--section NAME]

Findings doc: docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md (§5 follow-on,
pjm-cong-1 addendum).
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
logging.disable(logging.WARNING)

from market_sim.config.constants import (  # noqa: E402
    NUCLEAR_DORMANT_UNTIL,
    NUCLEAR_MONTHLY_CF_BY_YEAR,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    _PJM_LOAD_ZONE_GROUPS,
    load_eia_hourly_benchmark,
)
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

RUNS_DIR = REPO / "frontend/data/backcast/runs"
BENCH_DIR = REPO / "frontend/data/backcast/bench/PJM"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
LMP_DIR = REPO / "data/raw/lmp-data"
XFER_DIR = REPO / "data/raw/iso-specific-transmission"
LOAD_DIR = REPO / "data/raw/zone-specific-demand"

HOURS = 8760
_MDAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MSTART = np.concatenate(([0], np.cumsum(np.array(_MDAYS) * 24)))[:12]
MONTH = np.repeat(np.arange(1, 13), np.array(_MDAYS) * 24)
HOD = np.arange(HOURS) % 24
TAIL_THR = 200.0
YEARS = (2023, 2024, 2025)
SUMMER_MONTHS = (6, 7, 8, 9)

# The joint east-cut design candidate (Phase 2): Eastern interface over both
# EMAAC import links. The MAD super-cut adds the AP-South and AEP-DOM legs.
EMAAC_CUT_LINKS = (("PJM_Central_PA", "PJM_EMAAC"), ("PJM_SWMAAC", "PJM_EMAAC"))
MAD_ZONES = ("PJM_EMAAC", "PJM_SWMAAC", "PJM_Dominion")
# NYISO seam economics in the keeper (interchange_config, measured ladder):
# 2025 import rungs all $502.65 (> every model tail-hour price) and firm
# export floor 1,650 MW out of the EMAAC border zone.
NYISO_FIRM_EXPORT_2025 = 1650.0


def load_payload(run_id: str) -> dict:
    raw = (RUNS_DIR / f"{run_id}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', raw)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def load_bench(year: int) -> dict:
    return json.loads(gzip.decompress((BENCH_DIR / f"{year}.json.gz").read_bytes()))[
        "bench"
    ]


def dec_u8(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8).astype(float) / 100.0


def dec_i16(s: str) -> np.ndarray:
    a = np.frombuffer(base64.b64decode(s), dtype="<i2").astype(float).copy()
    a[a == -32768] = np.nan
    return a


def actual_prices(year: int) -> tuple[np.ndarray, np.ndarray]:
    a = pd.read_parquet(ACTUAL_LMP)
    a = a[a.year == year].sort_values("hour")
    return a["rt"].to_numpy()[:HOURS], a["da"].to_numpy()[:HOURS]


def model_price(pay: dict, year: int) -> np.ndarray:
    """Load-weighted model hourly system price = actual RT + committed delta
    (the ordc gate counts the ANY-ZONE dual; this is the lower-bound system
    reconstruction used for gap anatomy, as in the summer-tail probe)."""
    rt, _ = actual_prices(year)
    return rt + dec_i16(pay["years"][str(year)]["lmpDeltaHr"])[:HOURS]


def tail_mask(year: int) -> np.ndarray:
    _, da = actual_prices(year)
    return da > TAIL_THR


def summer_tail_mask(year: int) -> np.ndarray:
    return tail_mask(year) & np.isin(MONTH, SUMMER_MONTHS)


def ept_hoy(ts: pd.Series) -> np.ndarray:
    """EPT wall-clock timestamps -> model-clock hour-of-year (non-leap 8760).

    The model clock is EPT prevailing: Feb 29 rows must be dropped by the
    caller; the DST fall-back repeat collapses by group-by(mean); the
    spring-forward hour simply has no row.
    """
    m = ts.dt.month.to_numpy()
    d = ts.dt.day.to_numpy()
    h = ts.dt.hour.to_numpy()
    return _MSTART[m - 1] + (d - 1) * 24 + h


def hub_da_matrix(year: int) -> pd.DataFrame:
    """(8760, n_hub) DA LMP matrix from the 12-hub raw file, model clock."""
    lm = pd.read_csv(
        LMP_DIR / f"PJM_{year}_rt_da_monthly_lmps.csv",
        usecols=["datetime_beginning_ept", "pnode_name", "total_lmp_da"],
    )
    ts = pd.to_datetime(lm.datetime_beginning_ept, format="mixed")
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    lm, ts = lm[keep], ts[keep]
    lm = lm.assign(hoy=ept_hoy(ts))
    mat = lm.pivot_table(
        index="hoy", columns="pnode_name", values="total_lmp_da", aggfunc="mean"
    ).reindex(range(HOURS))
    return mat.ffill().bfill()


def interface_frame(year: int) -> pd.DataFrame:
    """(8760 x series) long frame of measured limits+transfers, model clock."""
    df = pd.read_csv(
        XFER_DIR / f"PJM_{year}_transfer_limits_and_flows.csv",
        usecols=[
            "datetime_beginning_ept",
            "transfer_limit_area",
            "transfers",
            "transfer_limit",
        ],
    )
    ts = pd.to_datetime(df.datetime_beginning_ept, format="mixed")
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    df = df.assign(hoy=ept_hoy(ts))
    return (
        df.groupby(["transfer_limit_area", "hoy"])[["transfers", "transfer_limit"]]
        .mean()
        .reset_index()
    )


def zonal_load(year: int) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Settlement zonal MW rolled up to the 8 model zones, plus the system sum.

    This is the same 20->8 grouping the model's own zonal demand shapes use
    (eia_loader._PJM_LOAD_ZONE_GROUPS); the model distributes its EIA-930
    system demand over exactly these hourly shares.
    """
    df = pd.read_csv(
        LOAD_DIR / f"PJM{year}_hrl_load_metered.csv",
        usecols=["datetime_beginning_ept", "zone", "mw"],
    )
    df = df[df.zone != "RTO"].copy()
    df["mzone"] = df.zone.map(_PJM_LOAD_ZONE_GROUPS)
    ts = pd.to_datetime(df.datetime_beginning_ept, format="mixed")
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    df = df.assign(hoy=ept_hoy(ts))
    g = df.groupby(["mzone", "hoy"]).mw.sum().reset_index()
    out: dict[str, np.ndarray] = {}
    for z, sub in g.groupby("mzone"):
        arr = np.full(HOURS, np.nan)
        arr[sub.hoy.to_numpy()] = sub.mw.to_numpy()
        out[z] = pd.Series(arr).ffill().bfill().to_numpy()
    sys_mw = np.sum([v for v in out.values()], axis=0)
    return out, sys_mw


def plant_hourly(pay: dict, bench: dict, year: int, pid: str) -> tuple:
    """(model MW, campd MW or None, zone, group) for one payload plant."""
    b = bench.get(pid)
    mv = pay["years"][str(year)]["plants"].get(pid)
    if b is None or mv is None:
        return None, None, None, None
    m = dec_u8(mv["m"])[:HOURS] * b["npl"]
    c = None
    if "campd" in b and not b.get("ct_only"):
        c = dec_u8(b["campd"])[:HOURS] * b["npl"]
    return m, c, b.get("zone"), b.get("group", "")


# ------------------------------------------------------------------- roster
def sec_roster(pay: dict) -> None:
    for year in YEARS:
        rt, da = actual_prices(year)
        mp = model_price(pay, year)
        ordc = pay["years"][str(year)]["ordc"]["hoursGt200"]
        tail = da > TAIL_THR
        print(
            f"=== {year}: actual system DA>{TAIL_THR:.0f} = {tail.sum()} h "
            f"(RT {int((rt > TAIL_THR).sum())} h) | model any-zone {ordc['model']} h, "
            f"actual(RT basis) {ordc['actual']} h | model load-weighted "
            f"{int((mp > TAIL_THR).sum())} h"
        )
        hubs = hub_da_matrix(year)
        cnt = (hubs > TAIL_THR).sum().sort_values(ascending=False)
        print("  per-hub DA tranche (hours >$200):")
        for hub, n in cnt.items():
            print(f"    {hub:20s} {int(n):4d} h")
        idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        print("  system tranche roster (S=summer lane, W=winter lane):")
        for h in np.where(tail)[0]:
            lane = "S" if MONTH[h] in SUMMER_MONTHS else "W"
            nhub = int((hubs.iloc[h] > TAIL_THR).sum())
            print(
                f"    {lane} {idx[h].strftime('%m-%d %H:00')} DA {da[h]:6.0f} "
                f"model {mp[h]:6.0f} hubs>{TAIL_THR:.0f}: {nhub}/{hubs.shape[1]} "
                f"{'CAUGHT' if mp[h] > TAIL_THR else 'miss'}"
            )


# ------------------------------------------------------------------- events
EVENT_HUBS = (
    "EASTERN HUB",
    "NEW JERSEY HUB",
    "DOMINION HUB",
    "WESTERN HUB",
    "AEP-DAYTON HUB",
    "ATSI GEN HUB",
    "N ILLINOIS HUB",
)
HUB2ZONE = {
    "EASTERN HUB": "PJM_EMAAC",
    "NEW JERSEY HUB": "PJM_EMAAC",
    "DOMINION HUB": "PJM_Dominion",
    "WESTERN HUB": "PJM_West_APS",
    "AEP-DAYTON HUB": "PJM_AEP_Ohio",
    "ATSI GEN HUB": "PJM_ATSI",
    "N ILLINOIS HUB": "PJM_ComEd",
}


def sec_events(pay: dict) -> None:
    for year in YEARS:
        stail = summer_tail_mask(year)
        if not stail.any():
            print(f"=== {year}: no summer tail hours")
            continue
        hubs = hub_da_matrix(year)
        mp = model_price(pay, year)
        _, da = actual_prices(year)
        idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        avail = [h for h in EVENT_HUBS if h in hubs.columns]
        print(
            f"=== {year} summer tail hub-premium anatomy ({int(stail.sum())} h; "
            "premium = hub DA − all-hub mean that hour):"
        )
        print(
            "    hour            sysDA  model | "
            + " ".join(f"{h[:7]:>8s}" for h in avail)
        )
        for h in np.where(stail)[0]:
            hub_mean = hubs.iloc[h].mean()
            prem = [hubs.iloc[h][hb] - hub_mean for hb in avail]
            print(
                f"    {idx[h].strftime('%m-%d %H:00')} {da[h]:6.0f} {mp[h]:6.0f} | "
                + " ".join(f"{p:+8.1f}" for p in prem)
            )
        # per-event means
        ev = {}
        for h in np.where(stail)[0]:
            key = f"{MONTH[h]:02d}-{(h - _MSTART[MONTH[h] - 1]) // 24 + 1:02d}"
            ev.setdefault(key[:2], []).append(h)
        for mon, hrs in sorted(ev.items()):
            hub_mean = hubs.iloc[hrs].mean(axis=1)
            print(f"  month {mon} event mean premium over {len(hrs)} tail h:")
            for hb in avail:
                p = (hubs.iloc[hrs][hb] - hub_mean).mean()
                print(f"    {hb:16s} {p:+7.1f}")
        # model zonal grain: monthly duals (the only zonal payload grain)
        y = pay["years"][str(year)]
        for mon in sorted({MONTH[h] for h in np.where(stail)[0]}):
            zp = {
                z: v["pMon"][mon - 1]
                for z, v in y["lmp"].items()
                if z != "PJM_external"
            }
            zmean = float(np.mean(list(zp.values())))
            spread = {z.replace("PJM_", ""): round(v - zmean, 1) for z, v in zp.items()}
            print(f"  model month-{mon} zonal dual premiums (monthly grain): {spread}")


# ------------------------------------------------------------- zonalphantom
def sec_zonalphantom(pay: dict) -> None:
    for year in YEARS:
        tail = tail_mask(year)
        stail = summer_tail_mask(year)
        if not tail.any():
            print(f"=== {year}: no tail hours")
            continue
        bench = load_bench(year)["plants"]
        yp = pay["years"][str(year)]["plants"]
        zones = sorted({b.get("zone") for b in bench.values() if b.get("zone")})
        classes = ("COAL", "CC_REGULAR", "CT", "ST_GAS")
        n_t, n_s = int(tail.sum()), int(stail.sum())
        print(
            f"=== {year} zone x class phantom, model − CAMPD mean MW in the "
            f"{n_t} tail hours ({n_s} summer):"
        )
        header = (
            "    "
            + f"{'zone':16s}"
            + " ".join(f"{c:>11s}" for c in classes)
            + f" {'TOTAL':>9s}"
        )
        print(header)
        ztot: dict[str, float] = {}
        for z in zones:
            row = []
            for cls in classes:
                d = np.zeros(HOURS)
                for pid in yp:
                    m, c, pz, grp = plant_hourly(pay, bench, year, pid)
                    if m is None or c is None or pz != z:
                        continue
                    if not grp.startswith(cls):
                        continue
                    if (
                        cls == "COAL"
                        or grp == cls
                        or grp.startswith(cls + "_")
                        or grp == cls
                    ):
                        d += m - c
                row.append(d[tail].mean())
            tot = 0.0
            d_all = np.zeros(HOURS)
            for pid in yp:
                m, c, pz, grp = plant_hourly(pay, bench, year, pid)
                if m is None or c is None or pz != z:
                    continue
                d_all += m - c
            tot = d_all[tail].mean()
            ztot[z] = tot
            print(
                "    "
                + f"{z.replace('PJM_', ''):16s}"
                + " ".join(f"{v:+11.0f}" for v in row)
                + f" {tot:+9.0f}"
            )
        east = sum(v for z, v in ztot.items() if z in MAD_ZONES)
        west = sum(v for z, v in ztot.items() if z not in MAD_ZONES)
        print(
            f"  MAD (EMAAC+SWMAAC+Dominion) fossil phantom {east:+.0f} MW | "
            f"west-of-MAD {west:+.0f} MW  -> the model wheels ~{west - east:+.0f} MW "
            "more west->east than reality in these hours (fossil basis)"
        )
        # top plants either direction
        rows = []
        for pid in yp:
            m, c, pz, grp = plant_hourly(pay, bench, year, pid)
            if m is None or c is None:
                continue
            d = (m - c)[tail].mean()
            if abs(d) >= 60:
                rows.append((d, bench[pid]["name"][:22], pz.replace("PJM_", ""), grp))
        rows.sort(reverse=True)
        print("  top plant phantoms (|d|>=60 MW):")
        for d, nm, z, grp in rows[:14]:
            print(f"    {nm:22s} {z:12s} {grp:12s} {d:+7.0f}")
        for d, nm, z, grp in rows[-6:]:
            if d < 0:
                print(f"    {nm:22s} {z:12s} {grp:12s} {d:+7.0f}")


# --------------------------------------------------------------- interfaces
def sec_interfaces(pay: dict) -> None:
    print(
        "=== Manual-03 crosswalk vs the committed PJM_INTERFACE_LINK_MAP:\n"
        "    series           Manual-03 boundary                committed model link\n"
        "    50045005 Post    western-PA -> Juniata 500kV cut    ComEd->AEP_Ohio  (MIS-ATTRIBUTED)\n"
        "    Average Western  5004/5005+Vinco-Hunterstown+Doubs  AEP_Ohio->West_APS (envelope reading)\n"
        "    Average Central  5004/5005+Conastone-PeachBottom    ATSI->Central_PA (envelope reading)\n"
        "    Average Eastern  the 7-line EMAAC EHV import cut    Central_PA->EMAAC ONLY (SWMAAC->EMAAC\n"
        "                                                        static 5,000 MW runs in parallel)\n"
        "    AP-South pre/post WV->VA/MD 500kV cut               West_APS->SWMAAC\n"
        "    Bed-Bla pre/post  Black Oak-Bedington               West_APS->Central_PA\n"
        "    AEP/DOM Post      AEP->Dominion 765/345 cut         AEP_Ohio->Dominion\n"
        "    Cleveland         ATSI-Cleveland pocket             (unmapped, correct)\n"
        "    BC/PEPCO, CE-East NOT in the DataMiner2 feed        (SWMAAC / ComEd import cuts)"
    )
    for year in YEARS:
        tail = tail_mask(year)
        stail = summer_tail_mask(year)
        fr = interface_frame(year)
        summer = np.isin(MONTH, SUMMER_MONTHS)
        print(
            f"=== {year} measured interfaces in the {int(tail.sum())} tail hours "
            f"({int(stail.sum())} summer):"
        )
        print(
            "    series                      tail_lim  tail_xfer  util% | "
            "summer_lim p05_lim | bind>=98% h/yr"
        )
        for name, sub in fr.groupby("transfer_limit_area"):
            lim = np.full(HOURS, np.nan)
            xf = np.full(HOURS, np.nan)
            lim[sub.hoy.to_numpy()] = sub.transfer_limit.to_numpy()
            xf[sub.hoy.to_numpy()] = sub.transfers.to_numpy()
            with np.errstate(invalid="ignore"):
                util = np.abs(xf) / np.where(lim > 0, lim, np.nan)
            mask = stail if stail.any() else tail
            if not mask.any():
                continue
            bind = int(np.nansum(util >= 0.98))
            print(
                f"    {name:26s} {np.nanmean(lim[mask]):9.0f} "
                f"{np.nanmean(xf[mask]):9.0f} {100 * np.nanmean(util[mask]):6.1f} | "
                f"{np.nanmean(lim[summer]):9.0f} {np.nanpercentile(lim[summer], 5):8.0f} | "
                f"{bind:5d}"
            )


# ------------------------------------------------------------------ eastcut
def _zone_caps(year: int) -> dict[str, dict[str, float]]:
    """Model fleet capacity by zone for nuclear + non-CAMPD-visible classes."""
    cfg = get_iso_config("PJM")
    gens = load_fleet_from_csv("PJM", cfg, year=year)
    out: dict[str, dict[str, float]] = {}
    for g in gens:
        if g.fuel_type == "nuclear" and year < NUCLEAR_DORMANT_UNTIL.get(
            int(g.plant_code), 0
        ):
            continue
        z = out.setdefault(g.zone, {})
        z[g.fuel_type] = z.get(g.fuel_type, 0.0) + g.pmax_mw
    return out


# In-cut pumped-storage/hydro discharge capability, EIA-860 nameplate
# (probe-local bound, anti-material full-discharge assumption): EMAAC carries
# Yards Creek (420 MW PS) + Conowingo (572 MW conventional, PECO-interconnected);
# Muddy Run (1,070 MW PS) sits in Central_PA in the model's zone assignment,
# i.e. OUTSIDE the EMAAC cut (it supplies the cut through the interface).
# MAD adds Bath County (3,003 MW PS, Dominion) + SWMAAC small hydro (~20 MW).
PS_HYDRO_CAP = {"EMAAC": 992.0, "MAD": 992.0 + 3023.0}


def sec_eastcut(pay: dict, year: int = 2025) -> None:
    stail = summer_tail_mask(year)
    n = int(stail.sum())
    hrs = np.where(stail)[0]
    idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    bench = load_bench(year)["plants"]
    yp = pay["years"][str(year)]["plants"]
    zl, sys_metered = zonal_load(year)
    e930 = load_eia_hourly_benchmark("PJM", year)
    demand = (
        np.asarray(e930.get("demand", sys_metered), dtype=float)[:HOURS]
        if e930
        else sys_metered
    )
    scale = demand / np.where(sys_metered > 0, sys_metered, np.nan)
    caps = _zone_caps(year)
    cf = np.asarray(NUCLEAR_MONTHLY_CF_BY_YEAR["PJM"][year], dtype=float)

    fr = interface_frame(year)

    def series(name: str, col: str) -> np.ndarray:
        sub = fr[fr.transfer_limit_area == name]
        out = np.full(HOURS, np.nan)
        out[sub.hoy.to_numpy()] = sub[col].to_numpy()
        return out

    east_lim = series("Average Eastern", "transfer_limit")
    east_xf = series("Average Eastern", "transfers")

    for cut_name, cut_zones, ps_cap in (
        ("EMAAC", ("PJM_EMAAC",), PS_HYDRO_CAP["EMAAC"]),
        ("MAD", MAD_ZONES, PS_HYDRO_CAP["MAD"]),
    ):
        load_cut = np.sum([zl[z] for z in cut_zones], axis=0) * scale
        # model fossil inside the cut: every payload plant with a zone tag
        fossil_m = np.zeros(HOURS)
        fossil_a = np.zeros(HOURS)
        for pid in yp:
            m, c, pz, _ = plant_hourly(pay, bench, year, pid)
            if m is None or pz not in cut_zones:
                continue
            fossil_m += m
            if c is not None:
                fossil_a += c
        nuc_pmax = sum(caps.get(z, {}).get("nuclear", 0.0) for z in cut_zones)
        nuc_m = nuc_pmax * cf[MONTH - 1]

        # renewables + oil/biomass central estimate: 930 system series scaled
        # by the cut's share of PJM capacity in that class (fleet where known;
        # renewables use the class's system series directly x share).
        def sys_share(ft: str) -> float:
            tot = sum(z.get(ft, 0.0) for z in caps.values())
            inc = sum(caps.get(z, {}).get(ft, 0.0) for z in cut_zones)
            return inc / tot if tot > 0 else 0.0

        wind = np.asarray(e930.get("wind", np.zeros(HOURS)))[:HOURS]
        solar = np.asarray(e930.get("solar", np.zeros(HOURS)))[:HOURS]
        oil = np.asarray(e930.get("oil", np.zeros(HOURS)))[:HOURS]
        other = np.asarray(e930.get("other", np.zeros(HOURS)))[:HOURS]
        # wind/solar shares: no fleet table here — use load share as the
        # spatial proxy, disclosed (EMAAC utility renewables are small).
        lshare = float(
            np.mean(np.sum([zl[z] for z in cut_zones], axis=0) / sys_metered)
        )
        renew = (wind + solar) * lshare
        noncampd = (oil * sys_share("oil")) + (other * sys_share("biomass"))
        gen_cut_m = fossil_m + nuc_m + renew + noncampd + ps_cap
        r_total = load_cut - gen_cut_m  # required TOTAL inflow (internal+seam)
        if cut_name == "EMAAC":
            seam_in = 0.0  # NYISO import rungs $502.65 > model tail prices
            r_int_central = r_total - seam_in
            r_int_firmexp = r_total + (NYISO_FIRM_EXPORT_2025 if year == 2025 else 0.0)
            lim = east_lim + 0.0
            lim_label = "AvgEastern"
        else:
            apsouth = np.fmin(
                series("AP-South Pre-Contingency", "transfer_limit"),
                series("AP-South Post-Contingency", "transfer_limit"),
            )
            aepdom = series("AEP/DOM Post-Contingency", "transfer_limit")
            # WAPS->Dominion has no published series: static 3,000 stays.
            lim = east_lim + apsouth + aepdom + 3000.0
            seam_carolina_tva = 2400.0 + 1600.0  # southern seams, cheap rungs
            r_int_central = r_total - seam_carolina_tva
            r_int_firmexp = r_int_central + (
                NYISO_FIRM_EXPORT_2025 if year == 2025 else 0.0
            )
            lim_label = "AvgE+APS+AEPDOM+3000"
        # actual-side cross-validation (EMAAC cut only, vs measured transfers)
        if cut_name == "EMAAC":
            act_gen = fossil_a + nuc_pmax * 1.0 + renew + noncampd + ps_cap
            act_inflow = load_cut - act_gen
            xv = np.nanmean((act_inflow - east_xf)[stail])
            print(
                f"=== {year} {cut_name} cut — actual-side cross-validation over the "
                f"{n} tail hours: reconstructed actual inflow − measured Eastern "
                f"transfers = {xv:+.0f} MW mean (the unmonitored-path + nuclear-at-"
                "cap + PS wedge; |wedge| ~< 1.5 GW validates the construction)"
            )
        exceed_c = r_int_central - lim
        exceed_f = r_int_firmexp - lim
        nx_c = int(np.nansum(exceed_c[stail] > 0))
        nx_f = int(np.nansum(exceed_f[stail] > 0))
        med_c = (
            float(np.nanmedian(exceed_c[stail][exceed_c[stail] > 0])) if nx_c else 0.0
        )
        print(
            f"=== {year} {cut_name} cut adjudication ({lim_label}); PS at full "
            f"{ps_cap:.0f} MW discharge (anti-material):"
        )
        print(
            "    hour           load_cut fossil_m  nuc_m renew+nc  R_int(c) "
            f"{lim_label[:10]:>10s}  margin(c) margin(+firmexp)"
        )
        for h in hrs:
            print(
                f"    {idx[h].strftime('%m-%d %H:00')} {load_cut[h]:8.0f} "
                f"{fossil_m[h]:8.0f} {nuc_m[h]:6.0f} {renew[h] + noncampd[h]:8.0f} "
                f"{r_int_central[h]:9.0f} {lim[h]:10.0f} {exceed_c[h]:+10.0f} "
                f"{exceed_f[h]:+10.0f}"
            )
        print(
            f"  -> central: exceeds in {nx_c}/{n} h (median exceedance "
            f"{med_c:+.0f} MW); with the measured 1,650 MW NYISO firm-export "
            f"floor: {nx_f}/{n} h"
        )
        if cut_name == "EMAAC":
            verdict = nx_c >= 8 and med_c >= 300.0
            print(
                f"  PRE-DECLARED STOP CONDITION (>=8/22 h AND median >=300 MW on "
                f"the central estimate): {'MATERIAL' if verdict else 'NULL — stop'}"
            )


SECTIONS = {
    "roster": sec_roster,
    "events": sec_events,
    "zonalphantom": sec_zonalphantom,
    "interfaces": sec_interfaces,
    "eastcut": sec_eastcut,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-id", default="2026-07-16-pjm-113-short-only")
    ap.add_argument("--section", choices=sorted(SECTIONS), default=None)
    args = ap.parse_args()
    pay = load_payload(args.run_id)
    for name, fn in SECTIONS.items():
        if args.section and name != args.section:
            continue
        print(f"\n########## {name} ##########")
        fn(pay)
    return 0


if __name__ == "__main__":
    sys.exit(main())
