#!/usr/bin/env python
"""ERCOT-128 — UNIT-GRAIN commitment for multi-unit coal plants: can the
measured min-load parameter be given somewhere to land?

Phase 1 of the lane routed by ``DIAGNOSIS-ercot127`` §5.3, which closed the
coal DISPATCH-BAND lane with a sharp, localised finding: the coal committed
min-load fraction is MEASURED, full span and forward-admissible (0.3500 /
0.3729 / 0.3705, pooled **0.3636**, over 627,641 resource-hours of the 60-Day
DAM Gen Resource corpus, ERCOT-62 convention) — and it has **nowhere to land**,
because a real low-loading coal plant-hour is *two-thirds of its units online
holding 0.39-0.44 and the rest SHUT DOWN*, which the model's per-plant
continuous tranches cannot distinguish from all-units-low. Applied at plant
grain the measured floor fixes the keeper's two failing G1 price bands and
breaks **thirteen** of the nineteen it already passes (8/21 against 19/21).

The question this lane owns: **can multi-unit coal plants carry unit-grain
commitment state inside the standing pure-LP / no-MIP rule?**

Sections A-G are diagnostic only: no LP is built, no year is solved, nothing is
registered, and no ``ScenarioConfig`` field, cache-key surface or solve path is
touched. (Section H, added for Phase 2, SCORES a bundle another process solved;
it still builds no LP.) Every
model quantity is read from the KEEPER's committed payload (rule 15
``[R-DASHBOARD]``); every actual is read from a raw source. The loaders, the
coal-plant filter, the gross->net convention and the price-band edges are
reused VERBATIM from ``scripts/probes/ercot127_coal_dispatch_band.py`` so this
lane's numbers are directly comparable to the one that chartered it — section
D's ``plant_0.364`` column is a deliberate CONTROL that reproduces ERCOT-127
§3.1's own ``floor_0.364`` column to +-0.001 in every band, and section F's
keeper row reproduces the keeper's committed ``legitimacy_diagnostics.json``
D-1 values (COAL_LIGNITE 2023 0.744/0.300 against the artifact's 0.745/0.294).

Sections
--------
A  the UNIT INVENTORY and the plant's MINIMUM ONLINE CONFIGURATION — per coal
   plant, the units EIA-860 registers, each unit's own ``Minimum Load (MW)``,
   and the smallest MW a plant can hold while synchronised (``min_u
   MinLoad_u``). Cross-checked against the ERCOT COP ``LSL`` the ERCOT-127 §2
   parameter was derived from. This is the unit-grain registration fact the
   whole lane turns on, and it is a *registration* quantity — forward-derivable
   for any vintage, condition-responsive (a retired unit contributes nothing) —
   not a measured outcome (rule 13 ``[R-MEASURED]``).
B  IS UNIT-GRAIN COMMITMENT EXPRESSIBLE WITHOUT INTEGRALITY? (charter task a)
   — the exact unit-commitment feasible set of each plant, enumerated over all
   2^N on/off subsets, tested for GAPS. A plant's online feasible set is
   ``U_k [min-load of configuration k, capacity of configuration k]``; where
   that union is gap-free it equals the interval ``[min_u MinLoad_u, Cap]`` and
   the LP relaxation of the plant's dispatch range is EXACT — no integrality is
   lost and unit-grain commitment costs the LP nothing. Where it has gaps the
   interval is a strict relaxation, and the section reports how much of the
   plant's range the gaps cover.
C  THE DETECTOR PROOF (charter task a, the named killer) — ERCOT-127 §5.3
   warns that a P0 run-pattern detector cannot help, because the keeper's coal
   never reaches zero, so a detector marks it committed in every hour and
   reproduces the same blanket floor. Verified here on the keeper's own
   payload, and extended: the *tranche-prefix* detector (mark online the
   minimal prefix of the merit stack that carries the hour's dispatch) is shown
   to be SELF-SATISFYING — its floor is non-binding by construction except in a
   narrow deep-low sliver, measured here rather than asserted.
D  SIZE THE PRIZE (charter task c) — the keeper's coal reconstructed at unit
   grain and re-floored three ways, then scored on the charter's own gates
   without a solve:
     * ``plant_0.364``  the ERCOT-127 blanket plant-grain floor — CONTROL,
       must reproduce 8/21;
     * ``oracle``       the floor applied only to the capacity reality actually
       held online in that hour (CAMPD unit grain). This is an ORACLE and is
       NOT a candidate mechanism — it consumes a measured outcome and is
       rule-13 inadmissible as an input. It is used ONLY as the ex-ante CEILING:
       no implementable commitment rule can beat reality's own commitment, so
       if the oracle fails the gates the lane is refuted for every rule;
     * ``min_config``   the IMPLEMENTABLE unit-grain floor — the plant may not
       be pushed below the minimum load of its smallest online configuration,
       ``min_u MinLoad_u``, a section-A registration fact requiring no
       commitment detection and no integrality (section B is the proof).
   Scored as G1 (loading-vs-price, ERCOT-126 §1.5 / ERCOT-127 §G FLEET-AGGREGATE
   basis, gate ``|model - actual| <= 0.05`` in every band), C1 (coal TWh vs
   actual) and C8 (forced share of coal energy).
E  the BOTTOM-TAIL test — ERCOT-127 §4's per-plant p05 finding (keeper 0.013-
   0.767 against actual 0.106-0.585: the model drives coal far below anything
   the real fleet does, on nearly every plant, every year) re-measured under
   each floor. This is the defect the lane exists to fix, and it is where an
   implementable floor has to show its work.
F  gate G3 — the COAL D-1 diurnal shape under each floor, evaluated ex ante.
   The charter requires ``COAL_LIGNITE`` 2023 to CLEAR both D-1 gates
   (``profile_r >= 0.8``, ``cv_ratio >= 0.5``); the keeper is a live FAIL there
   at 0.745 / 0.294, and coal is inside ``D1_GATED_CLASSES`` since rubric v2.8,
   so this is the one gate in the set that demands a WIN rather than do-no-harm.
   Built exactly as the scorer builds it, so the keeper row is a check on the
   whole section.
G  WHERE THE D-1 FAILURE COMES FROM — the off-peak (h0-14) flat-top pin share,
   model against actual, per coal class. Section F's result is structural, not
   numerical: the keeper's off-peak profile is too FLAT, and a lower bound
   applied uniformly across hour-of-day can only flatten it further. This
   section locates the flatness so the successor is routed rather than merely
   refused.
H  SCORE A SOLVED ARM (``--arm-bundle``) — Phase 2. G1 / G2 / G3 for the armed
   bundle's OWN P1 dispatch against the keeper's and the actuals, on the same
   fleet-aggregate basis, price-band edges and D-1 construction as sections D
   and F, so the arm is directly comparable to the ex-ante bound that predicted
   it. This is the authority
   ``docs/PRECOMMIT-ercot128-coal-min-config-2026-07-28.md`` §2 names for G1.
   Reads each bundle's committed ``hourly/class_hourly_<year>.parquet`` sidecar
   rather than replaying a solve (rule 15 ``[R-DASHBOARD]``). Sections A-G do
   not run in this mode.

Bases, stated once (identical to ERCOT-127)
-------------------------------------------
* ``actual`` is CAMPD unit-level ``grossLoad`` over the coal-fuelled units of
  the ten ERCOT coal plants (the ``primaryFuelInfo`` filter that keeps W A
  Parish's gas steamers out), converted to NET by the per-year factor measured
  against the committed EIA-923 bench ``classFull`` coal total (0.8972 /
  0.9051 / 0.9069), applied to ONE side only.
* ``keeper`` is ``2026-07-26-ercot115-coal-marginal-hr``'s own committed
  payload, decoded per-plant.
* ``declared`` is the 60-Day DAM accepted COP ``live_mw``, an ERCOT HSL (NET).
* A floor level is ``frac x`` the plant's own MONTHLY MAXIMUM in the keeper's
  series — the keeper's realised ``pmax x availability``, the same monthly
  grain the ERCOT-126 §1.4 pin statistic and the ERCOT-127 §3 construction use,
  so the three lanes' floors are the same object at different fractions.

Rule 22 ``[R-HOLDOUT]``: every window is {2023, 2024, 2025}. No 2022-or-earlier
quantity appears anywhere; the 60-Day DAM ``*_Jan-Mar`` files carry trailing
Nov/Dec-2022 delivery rows and section A drops them explicitly before any
aggregate, exactly as the ERCOT-126/127 probes do.

Usage
-----
    python scripts/probes/ercot128_coal_unit_grain.py [--json-out PATH]
    python scripts/probes/ercot128_coal_unit_grain.py \
        --arm-bundle results/calibration/ercot128_unit_grain \
        --json-out data/raw/_validation-source/ercot128_arm_gates.json
"""

from __future__ import annotations

import argparse
import base64
import gzip
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from market_sim.config import paths  # noqa: E402

YEARS: tuple[int, ...] = (2023, 2024, 2025)
KEEPER_RUN = "2026-07-26-ercot115-coal-marginal-hr"

# ERCOT-127 §2 pooled cap-weighted p50 LSL/HSL for Resource Type CLLIG over
# 627,641 resource-hours. Carried as the measured min-load fraction so this
# lane's control column is the same object ERCOT-127 §3 refuted.
MEASURED_MIN_LOAD_FRAC = 0.3636

COAL_PLANTS: dict[int, str] = {
    298: "Limestone",
    3470: "W A Parish",
    6146: "Martin Lake",
    6178: "Coleto Creek",
    6179: "Fayette",
    6180: "Oak Grove",
    6183: "San Miguel",
    7030: "Major Oak",
    7097: "J K Spruce",
    56611: "Sandy Creek",
}

SITE_TO_PLANT: dict[str, int] = {
    "CALAVERS_JKS1": 7097, "CALAVERS_JKS2": 7097,
    "COLETO_COLETOG1": 6178,
    "FPPYD1_FPP_G1_J01": 6179, "FPPYD1_FPP_G1_J02": 6179,
    "FPPYD1_FPP_G2_J01": 6179, "FPPYD1_FPP_G2_J02": 6179, "FPPYD2_FPP_G3": 6179,
    "LEG_LEG_G1": 298, "LEG_LEG_G2": 298,
    "MLSES_UNIT1": 6146, "MLSES_UNIT2": 6146, "MLSES_UNIT3": 6146,
    "OGSES_UNIT1A": 6180, "OGSES_UNIT2": 6180,
    "SANMIGL_G1": 6183,
    "SCES_UNIT1_J01": 56611, "SCES_UNIT1_J02": 56611,
    "SCES_UNIT1_J03": 56611, "SCES_UNIT1_J04": 56611,
    "TNP_ONE_TNP_O_1": 7030, "TNP_ONE_TNP_O_2": 7030,
    "WAP_WAP_G5": 3470, "WAP_WAP_G6": 3470, "WAP_WAP_G7": 3470, "WAP_WAP_G8": 3470,
}

COAL_FUEL_CODES = ("BIT", "SUB", "LIG", "RC", "WC")

# Same fixed edges ERCOT-126 §1.5 and ERCOT-127 §G published.
PRICE_EDGES = (-np.inf, 15.0, 20.0, 25.0, 30.0, 35.0, 50.0, np.inf)
PRICE_LABELS = ("<15", "15-20", "20-25", "25-30", "30-35", "35-50", ">=50")

G1_TOL = 0.05

OUT_JSON = paths.CALIBRATION_DIR / "ercot128_coal_unit_grain.json"


# --------------------------------------------------------------------------
# loaders (verbatim from the ERCOT-127 probe, so the bases match)
# --------------------------------------------------------------------------
def hour_index(year: int) -> pd.DatetimeIndex:
    """Return the model's 8760-hour index for a year (Feb 29 dropped)."""
    idx = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
    idx = idx[~((idx.month == 2) & (idx.day == 29))]
    return idx[:8760]


def load_run_payload(run_id: str) -> dict:
    """Decode a committed dashboard run payload (frontend/data/backcast/runs)."""
    src = _REPO / "frontend" / "data" / "backcast" / "runs" / f"{run_id}.js"
    blob = re.search(r'"(H4sI[^"]+)"', src.read_text()).group(1)
    return json.loads(gzip.decompress(base64.b64decode(blob)))


def load_bench(year: int) -> dict:
    """Decode the committed ERCOT benchmark sidecar for a year."""
    p = _REPO / "frontend" / "data" / "backcast" / "bench" / "ERCOT" / f"{year}.json.gz"
    with gzip.open(p) as fh:
        return json.load(fh)


def payload_coal_plants(payload: dict, year: int) -> dict[int, np.ndarray]:
    """Per-plant hourly model MW for the coal classes, from a run payload."""
    bench = load_bench(year)["bench"]["plants"]
    out: dict[int, np.ndarray] = {}
    for code, rec in payload["years"][str(year)]["plants"].items():
        grp = str(bench.get(code, {}).get("group", ""))
        if not grp.startswith("COAL"):
            continue
        npl = float(bench[code]["npl"])
        out[int(code)] = (
            np.frombuffer(base64.b64decode(rec["m"]), dtype=np.uint8).astype(float)
            * npl / 100.0
        )
    return out


def payload_coal_pmax(payload: dict, year: int) -> dict[int, float]:
    """Per-plant model capacity (the payload's own ``npl``) for the coal classes."""
    bench = load_bench(year)["bench"]["plants"]
    out: dict[int, float] = {}
    for code in payload["years"][str(year)]["plants"]:
        grp = str(bench.get(code, {}).get("group", ""))
        if grp.startswith("COAL"):
            out[int(code)] = float(bench[code]["npl"])
    return out


def bench_coal_actual_twh(year: int) -> float:
    """Committed EIA-923 bench coal total (net TWh), the gross->net anchor."""
    cf = load_bench(year)["bench"]["classFull"]
    return float(cf.get("COAL_PRB", 0.0)) + float(cf.get("COAL_LIGNITE", 0.0))


def campd_coal_units(year: int) -> pd.DataFrame:
    """CAMPD unit-level coal rows for the ERCOT coal fleet, on the model index."""
    df = pd.read_parquet(
        paths.RAW_DIR / "campd-unit-level" / f"TX_{year}.parquet",
        columns=["facilityId", "unitId", "date", "hour", "grossLoad", "primaryFuelInfo"],
    )
    df = df[df.primaryFuelInfo.astype(str).str.contains(
        "Coal|Lignite", case=False, na=False)]
    df["facilityId"] = df.facilityId.astype(int)
    df = df[df.facilityId.isin(COAL_PLANTS)]
    df["ts"] = pd.to_datetime(df.date) + pd.to_timedelta(df.hour, unit="h")
    return df


def campd_coal_gross(year: int) -> pd.DataFrame:
    """Per-plant hourly CAMPD gross load (MW) for the ERCOT coal fleet."""
    df = campd_coal_units(year)
    return (
        df.pivot_table(index="ts", columns="facilityId", values="grossLoad", aggfunc="sum")
        .reindex(hour_index(year))
        .fillna(0.0)
    )


def dam_declared(year: int) -> pd.DataFrame:
    """Per-plant hourly COP declared live MW (an ERCOT HSL, NET)."""
    av = pd.read_parquet(paths.RAW_DIR / "ercot-thermal-dam-availability-site-hourly.parquet")
    av = av[(av["class"] == "COAL") & (av.date.str.startswith(str(year)))].copy()
    av["plant"] = av.site.map(SITE_TO_PLANT)
    av["ts"] = pd.to_datetime(av.date) + pd.to_timedelta(av.he - 1, unit="h")
    live = av.pivot_table(index="ts", columns="plant", values="live_mw", aggfunc="sum")
    return live.reindex(hour_index(year)).ffill().fillna(0.0)


# --------------------------------------------------------------------------
# A -- the unit inventory and the minimum online configuration
# --------------------------------------------------------------------------
def eia860_coal_units() -> pd.DataFrame:
    """EIA-860 operable coal generators at the ten ERCOT coal plants.

    Returns one row per (plant, generator) with the registered summer capacity
    and the registered ``Minimum Load (MW)``. Both are REGISTRATION facts filed
    by the operator, not measured operation, so they are rule-13 admissible as
    forward inputs: they exist for any vintage, they respond to condition
    (a retired unit leaves the file), and nothing in them is an outcome of the
    dispatch being validated.
    """
    g = pd.read_parquet(paths.RAW_DIR / "eia-860" / "eia860_generator_operable.parquet")
    g["Plant Code"] = pd.to_numeric(g["Plant Code"], errors="coerce")
    g = g[g["Plant Code"].isin(COAL_PLANTS)]
    g = g[g["Energy Source 1"].astype(str).str.upper().isin(COAL_FUEL_CODES)]
    out = pd.DataFrame({
        "plant": g["Plant Code"].astype(int),
        "unit": g["Generator ID"].astype(str),
        "cap_mw": pd.to_numeric(g["Summer Capacity (MW)"], errors="coerce"),
        "nameplate_mw": pd.to_numeric(g["Nameplate Capacity (MW)"], errors="coerce"),
        "min_load_mw": pd.to_numeric(g["Minimum Load (MW)"], errors="coerce"),
        "status": g["Status"].astype(str),
    })
    return out.dropna(subset=["cap_mw", "min_load_mw"]).reset_index(drop=True)


def dam_unit_lsl() -> pd.DataFrame:
    """Per-RESOURCE minimum committed ``LSL`` and maximum ``HSL`` from the COP.

    The ERCOT-127 §2 corpus, aggregated to the resource rather than pooled into
    a fraction — the cross-check on section A's EIA-860 ``Minimum Load``, on a
    completely independent filing. Rule 22: the ``*_Jan-Mar`` files carry
    trailing Nov/Dec-2022 delivery rows and they are dropped explicitly here,
    before any aggregate.
    """
    files = sorted((paths.RAW_DIR / "ercot").glob(
        "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_20*.parquet"))
    files = [f for f in files if "2026" not in f.name]
    parts: list[pd.DataFrame] = []
    for f in files:
        df = pd.read_parquet(f)
        df = df[df["Resource Type"] == "CLLIG"]
        if df.empty:
            continue
        ts = (pd.to_datetime(df["Delivery Date"])
              + pd.to_timedelta(df["Hour Ending"].astype(str).str.slice(0, 2).astype(int) - 1,
                                unit="h"))
        df = df.assign(ts=ts)
        df = df[df.ts.dt.year.isin(YEARS)]
        parts.append(df[["ts", "Resource Name", "HSL", "LSL"]])
    S = pd.concat(parts, ignore_index=True)
    S = S[(S.HSL > 0.0) & S.LSL.notna() & (S.LSL > 0.0)]
    S["plant"] = S["Resource Name"].map(SITE_TO_PLANT)
    S = S[S.plant.notna()]
    g = S.groupby(["plant", "Resource Name"]).agg(
        lsl_p50=("LSL", "median"), hsl_max=("HSL", "max"), hours=("LSL", "size"))
    return g.reset_index().rename(columns={"Resource Name": "resource"})


def section_a_unit_inventory(pmax: dict[int, float]) -> dict:
    """A -- per-plant unit inventory and the MINIMUM ONLINE CONFIGURATION.

    ``min_config_mw`` is the smallest load a synchronised plant can hold: the
    minimum over its units of the unit's own registered minimum load. It is the
    exact lower endpoint of the plant's unit-commitment feasible set given at
    least one unit online, and section B tests when the interval above it is
    gap-free.
    """
    e = eia860_coal_units()
    dam = dam_unit_lsl()
    out: dict = {"eia860_units": int(len(e)), "plants": {}}
    for code, name in COAL_PLANTS.items():
        u = e[e.plant == code]
        if u.empty:
            out["plants"][str(code)] = {"name": name, "eia860_rows": 0}
            continue
        d = dam[dam.plant == code]
        cap = float(u.cap_mw.sum())
        mc = float(u.min_load_mw.min())
        mpx = float(pmax.get(code, float("nan")))
        out["plants"][str(code)] = {
            "name": name,
            "n_units": int(len(u)),
            "unit_cap_mw": [round(float(x), 1) for x in sorted(u.cap_mw)],
            "unit_min_load_mw": [round(float(x), 1) for x in sorted(u.min_load_mw)],
            "eia860_cap_mw": round(cap, 1),
            "model_pmax_mw": round(mpx, 1),
            "min_config_mw": round(mc, 1),
            # the implementable floor, expressed on the MODEL's own capacity
            # scale so it can be applied as a fraction of pmax x availability
            "min_config_frac_of_model_pmax": round(mc / mpx, 4) if mpx > 0 else None,
            "min_config_frac_of_eia860_cap": round(mc / cap, 4),
            # what the ERCOT-127 blanket floor would have demanded instead
            "blanket_floor_frac": MEASURED_MIN_LOAD_FRAC,
            "unit_min_load_over_unit_cap": [
                round(float(a / b), 3) for a, b in
                sorted(zip(u.min_load_mw, u.cap_mw))
            ],
            "dam_resources": int(len(d)),
            "dam_min_resource_lsl_p50_mw": round(float(d.lsl_p50.min()), 1) if len(d) else None,
            "dam_sum_resource_hsl_max_mw": round(float(d.hsl_max.sum()), 1) if len(d) else None,
            "status": sorted(set(u.status)),
        }
    # fleet roll-ups
    caps = {c: v["eia860_cap_mw"] for c, v in
            ((int(k), v) for k, v in out["plants"].items()) if "eia860_cap_mw" in v}
    mcs = {c: v["min_config_mw"] for c, v in
           ((int(k), v) for k, v in out["plants"].items()) if "min_config_mw" in v}
    tot = sum(caps.values())
    out["fleet"] = {
        "eia860_cap_mw": round(tot, 1),
        "sum_min_config_mw": round(sum(mcs.values()), 1),
        "cap_weighted_min_config_frac": round(sum(mcs.values()) / tot, 4),
        "blanket_floor_frac": MEASURED_MIN_LOAD_FRAC,
        "unit_min_load_cap_weighted_frac": round(
            float(e.min_load_mw.sum() / e.cap_mw.sum()), 4),
    }
    return out


# --------------------------------------------------------------------------
# B -- is unit-grain commitment expressible without integrality?
# --------------------------------------------------------------------------
def section_b_lp_expressibility() -> dict:
    """B -- the exact unit-commitment feasible set of each plant, gap-tested.

    A plant with units ``u`` each carrying ``[MinLoad_u, Cap_u]`` has the exact
    online feasible set

        F = U_{S subset of units, S nonempty} [ sum_{u in S} MinLoad_u ,
                                                sum_{u in S} Cap_u ]

    which is a union of intervals. If that union is CONNECTED, it equals the
    single interval ``[min_u MinLoad_u, sum_u Cap_u]`` — and then a plant-grain
    LP variable bounded by exactly that interval represents the plant's
    unit-commitment dispatch range EXACTLY. No integrality is lost, no MIP is
    needed, and unit-grain commitment costs the LP nothing but a lower bound.

    Where the union is disconnected the interval is a strict RELAXATION; the
    section reports the gaps and the share of the plant's range they cover, so
    the approximation is stated rather than assumed. (A relaxation is still
    valid — it never forbids something the real plant can do, which is the
    direction rule 14 ``[R-ACCURATE]`` cares about — but it does admit plant
    levels no unit combination can deliver, and that has to be on the record.)
    """
    e = eia860_coal_units()
    out: dict = {"plants": {}}
    for code, name in COAL_PLANTS.items():
        u = e[e.plant == code]
        if u.empty:
            continue
        mins = u.min_load_mw.to_numpy(dtype=float)
        caps = u.cap_mw.to_numpy(dtype=float)
        n = len(mins)
        ivals: list[tuple[float, float]] = []
        for r in range(1, n + 1):
            for S in itertools.combinations(range(n), r):
                ivals.append((float(mins[list(S)].sum()), float(caps[list(S)].sum())))
        ivals.sort()
        merged: list[list[float]] = [list(ivals[0])]
        for lo, hi in ivals[1:]:
            if lo <= merged[-1][1] + 1e-9:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        lo_all, hi_all = merged[0][0], merged[-1][1]
        gaps = [(round(merged[i][1], 1), round(merged[i + 1][0], 1))
                for i in range(len(merged) - 1)]
        gap_mw = sum(b - a for a, b in gaps)
        out["plants"][str(code)] = {
            "name": name,
            "n_units": int(n),
            "n_configurations": int(2 ** n - 1),
            "exact_lower_endpoint_mw": round(lo_all, 1),
            "capacity_mw": round(hi_all, 1),
            "connected": bool(len(merged) == 1),
            "gaps_mw": gaps,
            "gap_share_of_range": round(gap_mw / max(hi_all - lo_all, 1e-9), 4),
        }
    conn = [v for v in out["plants"].values() if v["connected"]]
    cap_conn = sum(v["capacity_mw"] for v in conn)
    cap_all = sum(v["capacity_mw"] for v in out["plants"].values())
    out["fleet"] = {
        "plants_connected": len(conn),
        "plants_total": len(out["plants"]),
        "capacity_share_exactly_representable": round(cap_conn / cap_all, 4),
        "max_gap_share_of_range": round(
            max(v["gap_share_of_range"] for v in out["plants"].values()), 4),
    }
    return out


# --------------------------------------------------------------------------
# C -- the detector proof
# --------------------------------------------------------------------------
def section_c_detector(keeper: dict, pmax: dict[int, float]) -> dict:
    """C -- can a P0/P1 run-pattern detector separate the units reality shut off?

    Two tests, both on the keeper's OWN committed payload, because ERCOT-127
    §5.3 names this as the single most likely killer of any detector-based
    design.

    ``plant_detector``: the existing bridge family detects commitment from the
    run pattern of the LP unit — here the whole plant. If the keeper's coal
    plant series essentially never reaches zero, the detector marks the plant
    committed in every hour and a floor gated on it is the SAME blanket floor
    ERCOT-127 §3 refuted. Reported as the share of hours below a permissive
    off bar.

    ``prefix_detector``: the natural unit-grain detector — mark online the
    minimal PREFIX of the merit stack (cheapest tranche first) whose capacity
    carries the hour's dispatch, then floor at ``frac x`` that online capacity.
    Because the prefix is chosen to cover the dispatch, ``C_on(t) < P(t) +
    c_last``, so the floor binds only where ``P(t) < frac/(1-frac) x c_last`` —
    a narrow deep-low sliver, and one whose width is set by the LAST unit's
    size rather than by anything the detector learned. The detector is
    therefore SELF-SATISFYING: it cannot force a unit on that the LP chose to
    leave off, because it infers "off" from the LP's own choice. Measured here
    (binding hours and lifted energy) rather than asserted.
    """
    e = eia860_coal_units()
    out: dict = {}
    f = MEASURED_MIN_LOAD_FRAC
    for year in YEARS:
        kee = keeper[year]
        rows: dict[str, dict] = {}
        tot_h = off_h = 0
        bind_h = 0
        lift_mwh = 0.0
        energy = 0.0
        for code, mw in kee.items():
            u = e[e.plant == code]
            if u.empty:
                continue
            mpx = float(pmax[year].get(code, 0.0))
            if mpx <= 0:
                continue
            # unit capacities rescaled onto the model's own plant capacity, so
            # the prefix stack is the model's megawatts, not EIA-860's
            caps = np.sort(u.cap_mw.to_numpy(dtype=float))[::-1]
            caps = caps * (mpx / caps.sum())
            cum = np.cumsum(caps)
            tot_h += mw.size
            off_h += int((mw <= 0.01 * mpx).sum())
            energy += float(mw.sum())
            # minimal prefix covering the dispatch
            k = np.searchsorted(cum, np.maximum(mw, 1e-9), side="left")
            k = np.minimum(k, caps.size - 1)
            c_on = cum[k]
            floor = f * c_on
            binding = (mw > 0.01 * mpx) & (floor > mw)
            bind_h += int(binding.sum())
            lift_mwh += float((floor - mw)[binding].sum())
            rows[str(code)] = {
                "name": COAL_PLANTS[code],
                "off_hours_share": round(float((mw <= 0.01 * mpx).mean()), 4),
                "prefix_binding_hours": int(binding.sum()),
                "prefix_lift_mwh": round(float((floor - mw)[binding].sum()), 1),
            }
        out[str(year)] = {
            "plant_detector": {
                "off_bar": "keeper plant MW <= 1 % of model pmax",
                "off_hours": off_h,
                "plant_hours": tot_h,
                "off_share": round(off_h / max(tot_h, 1), 5),
                "verdict": (
                    "detector marks coal COMMITTED in effectively every hour; a "
                    "floor gated on it IS the ERCOT-127 blanket floor"
                    if off_h / max(tot_h, 1) < 0.02 else "detector separates hours"
                ),
            },
            "prefix_detector": {
                "binding_hours": bind_h,
                "plant_hours": tot_h,
                "binding_share": round(bind_h / max(tot_h, 1), 5),
                "lift_twh": round(lift_mwh / 1e6, 4),
                "lift_share_of_coal_energy": round(lift_mwh / max(energy, 1e-9), 5),
            },
            "per_plant": rows,
        }
    return out


# --------------------------------------------------------------------------
# D -- size the prize
# --------------------------------------------------------------------------
def _monthly_max(mw: np.ndarray, month: np.ndarray) -> np.ndarray:
    """Per-hour plant availability proxy: that month's own maximum in the series.

    The ERCOT-126 §1.4 / ERCOT-127 §3 convention, reused verbatim. Months the
    plant is dark for (< 24 online hours) carry a zero ceiling, so a floor never
    resurrects an outage.
    """
    out = np.zeros_like(mw)
    for mo in range(1, 13):
        sel = (month == mo) & (mw > 1.0)
        if sel.sum() < 24:
            continue
        out[month == mo] = mw[sel].max()
    return out


def _oracle_online_frac(year: int) -> dict[int, np.ndarray]:
    """Per-plant hourly share of CAPACITY the real fleet held synchronised.

    ORACLE ONLY — this consumes measured unit-level operation and is rule-13
    INADMISSIBLE as a model input. It is used exclusively to bound what a
    perfect commitment rule could buy: no implementable rule can hold a better
    set of units online than the set reality actually held. A unit counts as
    synchronised at ``> 0.10 x`` its own observed maximum, the same permissive
    bar ERCOT-127 §H used.
    """
    df = campd_coal_units(year)
    umax = df.groupby(["facilityId", "unitId"]).grossLoad.max().rename("umax")
    df = df.join(umax, on=["facilityId", "unitId"])
    df = df[df.umax > 0]
    df["on_cap"] = np.where(df.grossLoad > 0.10 * df.umax, df.umax, 0.0)
    g = df.groupby(["facilityId", "ts"]).agg(on_cap=("on_cap", "sum"),
                                             cap=("umax", "sum"))
    frac = (g.on_cap / g.cap).unstack(0).reindex(hour_index(year)).fillna(0.0)
    return {int(c): frac[c].to_numpy(dtype=float) for c in frac.columns}


def _floor_variants(
    keeper: dict[int, np.ndarray],
    month: np.ndarray,
    minconfig: dict[int, float],
    oracle: dict[int, np.ndarray],
    pmax: dict[int, float],
) -> dict[str, dict[int, np.ndarray]]:
    """Build the three floored per-plant series (see the module docstring, D)."""
    out: dict[str, dict[int, np.ndarray]] = {
        "plant_0.364": {}, "oracle": {}, "min_config": {}}
    for code, mw in keeper.items():
        ceil = _monthly_max(mw, month)
        out["plant_0.364"][code] = np.maximum(mw, MEASURED_MIN_LOAD_FRAC * ceil)
        of = oracle.get(code)
        of = np.zeros_like(mw) if of is None else of
        out["oracle"][code] = np.maximum(mw, MEASURED_MIN_LOAD_FRAC * of * ceil)
        mc = minconfig.get(code)
        if mc is None or pmax.get(code, 0.0) <= 0:
            out["min_config"][code] = mw.copy()
        else:
            out["min_config"][code] = np.maximum(mw, (mc / pmax[code]) * ceil)
    return out


def section_d_prize(keeper: dict, pmax: dict[int, float], inv: dict) -> dict:
    """D -- G1 / C1 / C8 for the control, the ORACLE ceiling and the candidate."""
    price = pd.read_parquet(
        paths.RAW_DIR / "_validation-source" / "actual_lmp_hourly_SPP.parquet"
    )
    minconfig = {
        int(c): v["min_config_mw"]
        for c, v in inv["plants"].items() if "min_config_mw" in v
    }
    out: dict = {}
    for year in YEARS:
        idx = hour_index(year)
        month = idx.month.to_numpy()
        gross = campd_coal_gross(year)
        gn = bench_coal_actual_twh(year) / (gross.to_numpy().sum() / 1e6)
        act = (gross * gn).to_numpy().sum(axis=1)
        dec = (dam_declared(year).reindex(columns=sorted(COAL_PLANTS))
               .fillna(0.0).to_numpy().sum(axis=1))
        kee = keeper[year]
        variants = _floor_variants(kee, month, minconfig,
                                   _oracle_online_frac(year), pmax[year])

        series: dict[str, np.ndarray] = {"keeper": sum(kee.values())}
        for k, d in variants.items():
            series[k] = sum(d.values())

        # ---- C1 level ----
        act_twh = float(act.sum() / 1e6)
        c1 = {k: round(float(v.sum() / 1e6) - act_twh, 3) for k, v in series.items()}
        c1["actual_twh"] = round(act_twh, 3)

        # ---- C8 forced share ----
        # In an hour the floor binds, the plant delivers exactly the floor, so
        # the WHOLE hour's energy is forced — the same convention D-2 uses
        # (``at_floor_mask`` attributes the dispatch, not the lift).
        c8: dict[str, float] = {}
        for k, d in variants.items():
            forced = sum(float(d[c][d[c] > kee[c]].sum()) for c in d)
            c8[k] = round(forced / max(float(series[k].sum()), 1e-9), 4)

        # ---- G1 bands ----
        p = price[price.year == year].sort_values("hour")
        ph = p.rt.to_numpy(dtype=float)[:8760]
        band = np.asarray(pd.cut(ph, PRICE_EDGES, labels=PRICE_LABELS, right=False))
        bands: dict[str, dict] = {}
        passes: dict[str, int] = {k: 0 for k in series}
        nband = 0
        for lab in PRICE_LABELS:
            sel = band == lab
            den = dec[sel].sum()
            if sel.sum() < 24 or den <= 0:
                continue
            nband += 1
            a = float(act[sel].sum() / den)
            row = {"hours": int(sel.sum()), "actual": round(a, 3)}
            for k, v in series.items():
                m = float(v[sel].sum() / den)
                ok = abs(m - a) <= G1_TOL
                passes[k] += int(ok)
                row[k] = round(m, 3)
                row[f"{k}_pass"] = bool(ok)
            bands[lab] = row
        out[str(year)] = {"c1_delta_twh": c1, "c8_forced_share": c8,
                          "g1_bands": bands,
                          "g1_pass": {k: f"{v}/{nband}" for k, v in passes.items()}}
    return out


# --------------------------------------------------------------------------
# E -- the bottom tail
# --------------------------------------------------------------------------
def section_e_bottom_tail(keeper: dict, pmax: dict[int, float], inv: dict) -> dict:
    """E -- per-plant p05 loading against the COP declaration, under each floor.

    ERCOT-127 §4's decisive per-plant statistic: the keeper's p05 runs 0.013-
    0.767 against the real fleet's 0.106-0.585, i.e. the model drives coal far
    below anything the real fleet does. This is the defect the lane exists to
    close, so each floor is scored on it directly.
    """
    minconfig = {
        int(c): v["min_config_mw"]
        for c, v in inv["plants"].items() if "min_config_mw" in v
    }
    out: dict = {}
    for year in YEARS:
        idx = hour_index(year)
        month = idx.month.to_numpy()
        live = dam_declared(year)
        gross = campd_coal_gross(year)
        gn = bench_coal_actual_twh(year) / (gross.to_numpy().sum() / 1e6)
        kee = keeper[year]
        variants = _floor_variants(kee, month, minconfig,
                                   _oracle_online_frac(year), pmax[year])
        rows: dict[str, dict] = {}
        for code in sorted(kee):
            if code not in live.columns:
                continue
            cap = live[code].to_numpy(dtype=float)
            a = (gross[code].to_numpy(dtype=float) * gn) if code in gross.columns else None

            def _p05(mw: np.ndarray) -> float | None:
                on = (mw > 1.0) & (cap > 1.0)
                if on.sum() < 24:
                    return None
                return round(float(np.percentile(mw[on] / cap[on], 5)), 3)

            rows[str(code)] = {
                "name": COAL_PLANTS[code],
                "actual": _p05(a) if a is not None else None,
                "keeper": _p05(kee[code]),
                **{k: _p05(v[code]) for k, v in variants.items()},
            }
        out[str(year)] = rows
    return out


# --------------------------------------------------------------------------
# F -- the D-1 diurnal gate (G3), evaluated ex ante
# --------------------------------------------------------------------------
def _decode_cf_bytes(rec: dict) -> np.ndarray:
    """``legitimacy_diagnostics.py::_decode_cf_bytes``, reproduced for one plant.

    The bench stores the CAMPD actual as ``round(100 x mw / nameplate)`` bytes;
    where the annual total ``c_ann`` is present the series is rescaled to it
    exactly, which is what removes the byte quantization from every energy sum.
    """
    raw = np.frombuffer(base64.b64decode(rec["campd"]), dtype=np.uint8).astype(float)
    ann = rec.get("c_ann")
    tot = raw.sum()
    if ann is not None and tot > 0.0:
        return raw * (float(ann) * 1e6 / tot)
    return raw / 100.0 * float(rec.get("npl") or 0.0)


def _d1_metrics(model: np.ndarray, actual: np.ndarray) -> tuple[float, float, float]:
    """``scripts/legitimacy_diagnostics.py::d1_shape_metrics``, reproduced.

    Profile is the hour-of-day mean; the CVs are taken over the profile's
    off-peak points h0-14 (``D1_OFFPEAK_LAST_HOUR``). Copied rather than
    imported so this probe stays a read-only diagnostic with no dependency on
    the scorer's module-level state; the values it produces for the keeper are
    checked against the keeper's own committed ``legitimacy_diagnostics.json``
    in the console summary.
    """
    prof_m = model.reshape(-1, 24).mean(axis=0)
    prof_a = actual[: model.size].reshape(-1, 24).mean(axis=0)
    r = 0.0 if (prof_m.std() <= 0.0 or prof_a.std() <= 0.0) else float(
        np.corrcoef(prof_m, prof_a)[0, 1])
    off = np.arange(24) <= 14

    def _cv(x: np.ndarray) -> float:
        m = float(x.mean())
        return float(x.std() / m) if m > 1e-9 else 0.0

    return r, _cv(prof_m[off]), _cv(prof_a[off])


def section_f_d1(keeper: dict, pmax: dict[int, float], inv: dict) -> dict:
    """F -- gate G3: the COAL D-1 diurnal shape under each floor, ex ante.

    The charter's G3 requires ``COAL_LIGNITE`` 2023 to clear BOTH D-1 gates
    (``profile_r >= 0.8``, ``cv_ratio >= 0.5``) in the committed legitimacy
    artifact; the keeper is a LIVE FAIL there at 0.745 / 0.294. Model and
    actual class series are built exactly as the scorer builds them
    (``legitimacy_diagnostics.py:2006-2015``): per-plant model dispatch and the
    bench's own per-plant ``mw`` actual, summed over the plants of a ``group``.
    """
    minconfig = {
        int(c): v["min_config_mw"]
        for c, v in inv["plants"].items() if "min_config_mw" in v
    }
    out: dict = {}
    for year in YEARS:
        bench = load_bench(year)["bench"]["plants"]
        idx = hour_index(year)
        month = idx.month.to_numpy()
        kee = keeper[year]
        variants = _floor_variants(kee, month, minconfig,
                                   _oracle_online_frac(year), pmax[year])
        allser = {"keeper": kee, **variants}
        classes = sorted({str(bench[str(c)]["group"]) for c in kee if str(c) in bench})
        rows: dict[str, dict] = {}
        for klass in classes:
            members = [c for c in kee
                       if str(c) in bench and str(bench[str(c)]["group"]) == klass
                       and bench[str(c)].get("campd") and not bench[str(c)].get("nodata")]
            if not members:
                continue
            actual = np.zeros(8760)
            for c in members:
                actual += _decode_cf_bytes(bench[str(c)])[:8760]
            row: dict = {"plants": [COAL_PLANTS[c] for c in members]}
            for k, d in allser.items():
                model = np.zeros(8760)
                for c in members:
                    model += d[c][:8760]
                r, cvm, cva = _d1_metrics(model, actual)
                ratio = cvm / cva if cva > 1e-9 else float("nan")
                row[k] = {
                    "profile_r": round(r, 3),
                    "model_offpeak_cv": round(cvm, 3),
                    "actual_offpeak_cv": round(cva, 3),
                    "cv_ratio": round(ratio, 3) if np.isfinite(ratio) else None,
                    "gates_cleared": bool(r >= 0.8 and np.isfinite(ratio)
                                          and ratio >= 0.5),
                }
            rows[klass] = row
        out[str(year)] = rows
    return out


# --------------------------------------------------------------------------
# G -- what the D-1 failure actually IS
# --------------------------------------------------------------------------
def section_g_flatness(keeper: dict) -> dict:
    """G -- attribute the COAL D-1 cv_ratio failure, so the successor is routed.

    Section F shows every floor — the ORACLE included — moves both D-1 metrics
    the WRONG way, which is a structural statement, not a numerical accident:
    the keeper's off-peak profile is too FLAT (model CV 0.017 against actual
    0.057 for COAL_LIGNITE 2023), and a lower bound applied uniformly across
    hour-of-day can only raise the trough, i.e. flatten it further. This
    section measures where the flatness comes from, on the off-peak window the
    gate is computed over, using the ERCOT-126 §1.4 flat-top pin statistic
    (hours delivering within 0.5 % of that plant-month's own maximum) split by
    off-peak / on-peak.
    """
    out: dict = {}
    for year in YEARS:
        bench = load_bench(year)["bench"]["plants"]
        idx = hour_index(year)
        month = idx.month.to_numpy()
        hod = idx.hour.to_numpy()
        off = hod <= 14
        kee = keeper[year]
        rows: dict[str, dict] = {}
        classes = sorted({str(bench[str(c)]["group"]) for c in kee if str(c) in bench})
        for klass in classes:
            members = [c for c in kee
                       if str(c) in bench and str(bench[str(c)]["group"]) == klass
                       and bench[str(c)].get("campd") and not bench[str(c)].get("nodata")]
            if not members:
                continue
            m_pin_off = m_off = a_pin_off = a_off = 0.0
            m_tot = np.zeros(8760)
            a_tot = np.zeros(8760)
            for c in members:
                mw = kee[c]
                act = _decode_cf_bytes(bench[str(c)])[:8760]
                m_tot += mw
                a_tot += act
                for series, acc in ((mw, "m"), (act, "a")):
                    pin = np.zeros(8760, dtype=bool)
                    online = series > 1.0
                    for mo in range(1, 13):
                        sel = (month == mo) & online
                        if sel.sum() < 24:
                            continue
                        pin |= sel & (series >= 0.995 * series[sel].max())
                    if acc == "m":
                        m_pin_off += float(series[pin & off].sum())
                        m_off += float(series[off].sum())
                    else:
                        a_pin_off += float(series[pin & off].sum())
                        a_off += float(series[off].sum())
            rows[klass] = {
                "plants": [COAL_PLANTS[c] for c in members],
                "model_offpeak_pin_share": round(m_pin_off / max(m_off, 1e-9), 4),
                "actual_offpeak_pin_share": round(a_pin_off / max(a_off, 1e-9), 4),
                "model_hod_profile": [round(float(x), 1) for x in
                                      m_tot.reshape(-1, 24).mean(axis=0)],
                "actual_hod_profile": [round(float(x), 1) for x in
                                       a_tot.reshape(-1, 24).mean(axis=0)],
            }
        out[str(year)] = rows
    return out


# --------------------------------------------------------------------------
# H -- score a SOLVED arm bundle on the pre-commit's gates
# --------------------------------------------------------------------------
def _bundle_coal_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Per-COAL-class hourly P1 MW from a bundle's committed ``hourly`` sidecar.

    Reads ``hourly/class_hourly_<year>.parquet`` (written by every solve since
    2026-07-19) rather than replaying the solve — rule 15 ``[R-DASHBOARD]``:
    a keeper replay is justified only for unit-level questions, and G1/G2/G3
    are all class-level.
    """
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & df.klass.astype(str).str.startswith("COAL")]
    out: dict[str, np.ndarray] = {}
    for klass, g in df.groupby("klass"):
        mw = np.zeros(8760)
        g = g.sort_values("hour")
        h = g.hour.to_numpy(dtype=int)
        sel = h < 8760
        mw[h[sel]] = g.mw.to_numpy(dtype=float)[sel]
        out[str(klass)] = mw
    return out


def section_h_score_arm(bundle: Path, keeper_bundle: Path) -> dict:
    """H -- G1 / G2 / G3 for a SOLVED arm, against the keeper and the actuals.

    This is the authority the pre-commit
    (``docs/PRECOMMIT-ercot128-coal-min-config-2026-07-28.md`` §2) names for
    G1, and it scores the arm's own solved P1 dispatch — not the section-D
    ex-ante lift, which was only ever a bound. Same fleet-aggregate basis,
    same price-band edges, same D-1 construction as the rest of this probe, so
    the arm's numbers are directly comparable to the keeper's.
    """
    price = pd.read_parquet(
        paths.RAW_DIR / "_validation-source" / "actual_lmp_hourly_SPP.parquet"
    )
    out: dict = {}
    for year in YEARS:
        gross = campd_coal_gross(year)
        gn = bench_coal_actual_twh(year) / (gross.to_numpy().sum() / 1e6)
        act = (gross * gn).to_numpy().sum(axis=1)
        dec = (dam_declared(year).reindex(columns=sorted(COAL_PLANTS))
               .fillna(0.0).to_numpy().sum(axis=1))
        arm_cls = _bundle_coal_hourly(bundle, year)
        kee_cls = _bundle_coal_hourly(keeper_bundle, year)
        series = {"keeper": sum(kee_cls.values()), "arm": sum(arm_cls.values())}

        act_twh = float(act.sum() / 1e6)
        c1 = {k: round(float(v.sum() / 1e6) - act_twh, 3) for k, v in series.items()}
        c1["actual_twh"] = round(act_twh, 3)

        p = price[price.year == year].sort_values("hour")
        ph = p.rt.to_numpy(dtype=float)[:8760]
        band = np.asarray(pd.cut(ph, PRICE_EDGES, labels=PRICE_LABELS, right=False))
        bands: dict[str, dict] = {}
        passes = {k: 0 for k in series}
        nband = 0
        for lab in PRICE_LABELS:
            sel = band == lab
            den = dec[sel].sum()
            if sel.sum() < 24 or den <= 0:
                continue
            nband += 1
            a = float(act[sel].sum() / den)
            row = {"hours": int(sel.sum()), "actual": round(a, 3)}
            for k, v in series.items():
                m = float(v[sel].sum() / den)
                ok = abs(m - a) <= G1_TOL
                passes[k] += int(ok)
                row[k] = round(m, 3)
                row[f"{k}_pass"] = bool(ok)
            bands[lab] = row

        # D-1 on the SAME per-class construction the scorer uses, from the
        # bench actual for the plants of each coal class.
        bench = load_bench(year)["bench"]["plants"]
        d1: dict[str, dict] = {}
        for klass in sorted(set(arm_cls) | set(kee_cls)):
            members = [c for c, r in bench.items()
                       if str(r.get("group")) == klass and r.get("campd")
                       and not r.get("nodata") and int(c) in COAL_PLANTS]
            if not members:
                continue
            actual = np.zeros(8760)
            for c in members:
                actual += _decode_cf_bytes(bench[c])[:8760]
            row: dict = {}
            for k, cls in (("keeper", kee_cls), ("arm", arm_cls)):
                mw = cls.get(klass)
                if mw is None:
                    continue
                r, cvm, cva = _d1_metrics(mw, actual)
                ratio = cvm / cva if cva > 1e-9 else float("nan")
                row[k] = {
                    "profile_r": round(r, 3),
                    "cv_ratio": round(ratio, 3) if np.isfinite(ratio) else None,
                }
            d1[klass] = row

        out[str(year)] = {"c1_delta_twh": c1, "g1_bands": bands,
                          "g1_pass": {k: f"{v}/{nband}" for k, v in passes.items()},
                          "d1": d1}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "ERCOT-128 Phase 1 -- unit-grain commitment for multi-unit coal "
            "plants. Tests whether the ERCOT-127 measured min-load parameter "
            "has an LP-expressible place to land, and bounds ex ante what "
            "perfect unit-grain commitment could buy. Builds no LP and solves "
            "no year."
        )
    )
    ap.add_argument("--json-out", type=Path, default=OUT_JSON,
                    help="where to write the full section dump (JSON)")
    ap.add_argument("--arm-bundle", type=Path, default=None,
                    help=(
                        "score a SOLVED arm bundle on the pre-commit gates "
                        "(section H) instead of running the ex-ante sections "
                        "A-G. Compares the arm's own P1 dispatch to the keeper's"
                    ))
    ap.add_argument("--keeper-bundle", type=Path,
                    default=Path("results/calibration/ercot115_coal_floor_only"),
                    help="keeper bundle the arm is scored against (--arm-bundle only)")
    args = ap.parse_args()

    if args.arm_bundle is not None:
        res = {
            "arm_bundle": str(args.arm_bundle),
            "keeper_bundle": str(args.keeper_bundle),
            "H_arm_gates": section_h_score_arm(args.arm_bundle, args.keeper_bundle),
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(res, indent=2))
        print(f"\n=== ERCOT-128 arm gates — {args.arm_bundle} ===")
        for y in YEARS:
            d = res["H_arm_gates"][str(y)]
            print(f"\n  {y}  G1 {d['g1_pass']}")
            print(f"       C1 delta TWh {d['c1_delta_twh']}")
            for klass, row in d["d1"].items():
                cells = "  ".join(
                    f"{k} {row[k]['profile_r']:.3f}/{row[k]['cv_ratio']}"
                    for k in ("keeper", "arm") if k in row
                )
                print(f"       D-1 {klass:<13} {cells}")
            for lab, r in d["g1_bands"].items():
                print(f"         {lab:<7} act {r['actual']:.3f}  keeper {r['keeper']:.3f}"
                      f"{'' if r['keeper_pass'] else ' FAIL'}  arm {r['arm']:.3f}"
                      f"{'' if r['arm_pass'] else ' FAIL'}")
        print(f"\nwrote {args.json_out}")
        return

    payload = load_run_payload(KEEPER_RUN)
    keeper = {y: payload_coal_plants(payload, y) for y in YEARS}
    pmax = {y: payload_coal_pmax(payload, y) for y in YEARS}

    inv = section_a_unit_inventory(pmax[2024])
    res = {
        "run": KEEPER_RUN,
        "measured_min_load_frac": MEASURED_MIN_LOAD_FRAC,
        "A_unit_inventory": inv,
        "B_lp_expressibility": section_b_lp_expressibility(),
        "C_detector": section_c_detector(keeper, pmax),
        "D_prize": section_d_prize(keeper, pmax, inv),
        "E_bottom_tail": section_e_bottom_tail(keeper, pmax, inv),
        "F_d1_gate": section_f_d1(keeper, pmax, inv),
        "G_flatness": section_g_flatness(keeper),
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(res, indent=2))

    # ---- console summary ----
    print(f"\n=== ERCOT-128 Phase 1 — keeper {KEEPER_RUN} ===")
    print("\nA. minimum online configuration (EIA-860 unit grain)")
    print(f"{'plant':<14}{'N':>3}{'cap MW':>9}{'minCfg MW':>11}"
          f"{'frac pmax':>11}{'DAM minLSL':>12}")
    for c, v in inv["plants"].items():
        if "min_config_mw" not in v:
            continue
        print(f"{v['name']:<14}{v['n_units']:>3}{v['eia860_cap_mw']:>9.0f}"
              f"{v['min_config_mw']:>11.0f}"
              f"{(v['min_config_frac_of_model_pmax'] or 0):>11.3f}"
              f"{(v['dam_min_resource_lsl_p50_mw'] or 0):>12.0f}")
    print(f"  fleet cap-weighted min-config frac "
          f"{inv['fleet']['cap_weighted_min_config_frac']:.4f}  vs blanket "
          f"{MEASURED_MIN_LOAD_FRAC}")

    b = res["B_lp_expressibility"]["fleet"]
    print(f"\nB. LP-expressibility: {b['plants_connected']}/{b['plants_total']} plants "
          f"gap-free; {b['capacity_share_exactly_representable']:.3f} of coal "
          f"capacity EXACTLY representable by an interval; max gap share "
          f"{b['max_gap_share_of_range']:.3f}")

    print("\nC. detector")
    for y in YEARS:
        d = res["C_detector"][str(y)]
        print(f"  {y}: plant-detector off-share {d['plant_detector']['off_share']:.4f} "
              f"| prefix-detector binds {d['prefix_detector']['binding_share']:.4f} of "
              f"hours, lift {d['prefix_detector']['lift_twh']:.3f} TWh")

    print("\nD. the prize")
    for y in YEARS:
        d = res["D_prize"][str(y)]
        print(f"  {y}  G1 {d['g1_pass']}")
        print(f"       C1 delta TWh {d['c1_delta_twh']}")
        print(f"       C8 forced {d['c8_forced_share']}")

    print("\nF. D-1 gate (G3) — profile_r / cv_ratio, gates r>=0.8 & ratio>=0.5")
    for y in YEARS:
        for klass, row in res["F_d1_gate"][str(y)].items():
            cells = "  ".join(
                f"{k} {row[k]['profile_r']:.3f}/{row[k]['cv_ratio']}"
                for k in ("keeper", "min_config", "oracle", "plant_0.364")
            )
            print(f"  {y} {klass:<13} {cells}")

    print("\nG. where the D-1 flatness comes from — off-peak (h0-14) flat-top pin share")
    for y in YEARS:
        for klass, row in res["G_flatness"][str(y)].items():
            print(f"  {y} {klass:<13} model {row['model_offpeak_pin_share']:.4f}  "
                  f"actual {row['actual_offpeak_pin_share']:.4f}")

    print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
