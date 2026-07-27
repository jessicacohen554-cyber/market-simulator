#!/usr/bin/env python
"""ERCOT-127 — the coal DISPATCH band: what holds coal below its ceiling.

Phase 1 of the lane chartered by ``DIAGNOSIS-ercot126`` §5.3, which closed the
coal AVAILABILITY layer (the COP envelope is accurate and realizable; every
measured availability instrument is empty, mis-shaped or already live) and
routed the residual here: the real ERCOT coal fleet works a NARROW BAND —
loading 0.54 -> 0.72 across the entire price range, touching neither its
min-load nor its ceiling — while the model works the ENDS (0.494 at <$15,
0.767 at >=$50) and delivers 43.1/40.6/50.3 % of its coal energy on a binding
flat monthly top against the real fleet's 3.6/3.7/6.9 %.

Owner decision resolving the ERCOT-127 vs ERCOT-117 §5.3 scope fork (this
session, ex ante): **(a) ERCOT-127 SUBSUMES ERCOT-117 §5.3** — the band is ONE
phenomenon and one mechanism owns it (rule 19 ``[R-ONE-MECH]``), so both the
bottom (base share, model 0.28 vs measured 0.374-0.52) and the top (nothing
caps coal below its ceiling) are in scope here.

Diagnostic only: no LP is built, no year is solved, nothing is registered, and
no ``ScenarioConfig`` field, cache-key surface or solve path is touched. Every
model quantity is read from the KEEPER's committed payload (rule 15
``[R-DASHBOARD]``); every actual is read from a raw source. The loaders and the
gross->net convention are reused verbatim from
``scripts/probes/ercot126_coal_availability_envelope.py`` so the two lanes'
numbers are directly comparable.

Sections
--------
A  the RAMP-ENVELOPE bite, ex ante — the measured full-span CAMPD ramp
   envelope (``ScenarioConfig.ramp_limits``, an ALREADY-REGISTERED default-off
   flag whose ERCOT artifact was never derived) applied to the keeper's own
   per-plant coal hourly series and to the actual fleet's. Counts the hour
   transitions each series makes that the envelope forbids, and the energy
   implicated. This is the ERCOT-126 §3.2 test-before-you-solve: if the
   keeper's coal does not make forbidden moves, the mechanism is INERT on the
   defect and no solve is needed to know it.
B  can a ramp limit touch the PIN? — the flat-top episodes of the keeper's
   coal decomposed into ENTRY hours (reached by a move) and SUSTAIN hours
   (already there). A trajectory bound can only shave entries; if the pin is
   sustain-dominated it is out of reach of any ramp mechanism by construction.
C  CONDUCT or REPRESENTATION? (charter task a) — the per-plant loading
   DISTRIBUTION, model vs actual. A 5-tranche per-plant curve can only sit at
   a handful of discrete loadings; a real unit moves continuously. Reports the
   share of online hours each fleet spends in the interior of its own range
   and the number of distinct loading levels the model actually occupies.
D  is the band per-UNIT or fleet COMPOSITION? — the cross-plant spread of
   loading in the same hour, model vs actual, conditional on the measured RT
   price band. If reality's 0.72 aggregate at >=$50 is some plants at 0.95 and
   others at 0.45, the defect is that the model moves its plants together.
   NOTE this section's loading is an UNWEIGHTED per-plant mean (the basis the
   cross-plant dispersion column needs); section G carries the FLEET-AGGREGATE
   basis that ERCOT-126 §1.5 and the charter's G1 gate are written on. The two
   are different statistics and are not interchangeable.
E  the measured COAL committed min-load fraction, FULL SPAN — the ERCOT-62
   ``LSL/HSL`` capacity-weighted-p50 derive (the construction behind the
   already-registered ``ercot_gas_bridge_min_load_frac`` = 0.574) reproduced
   verbatim for ``Resource Type == CLLIG``, which that derive never published.
F  the EX-ANTE C8 forced share and level cost of flooring coal at that
   fraction (rule 20 ``[R-FORCED-BUDGET]``; coal forces ZERO today, so the
   charter requires the expected value stated BEFORE a solve).
G  the charter's G1 gate evaluated EX ANTE on ERCOT-126 §1.5's own
   fleet-aggregate basis — the keeper, and the keeper plus the measured floor,
   against actual in every price band.
H  what a LOW-LOADING real coal plant-hour actually IS, at UNIT grain — the
   test of whether section E's parameter is expressible at the plant grain the
   LP offers.

Bases, stated once
------------------
* ``actual`` is CAMPD unit-level ``grossLoad`` over the coal-fuelled units of
  the ten ERCOT coal plants (the ``primaryFuelInfo`` filter that keeps W A
  Parish's gas steamers out, ERCOT-121 §1a), converted to NET by the per-year
  factor measured against the committed EIA-923 bench ``classFull`` coal total
  (0.8972 / 0.9051 / 0.9069 — ERCOT-126's convention, applied to ONE side).
* ``keeper`` is ``2026-07-26-ercot115-coal-marginal-hr``'s own committed
  payload, decoded per-plant.
* ``declared`` is the 60-Day DAM accepted COP ``live_mw``, an ERCOT HSL (NET).
* The ramp envelope is derived by the FROZEN
  ``scripts/data/derive_campd_ramp_envelopes.py`` (rule 23
  ``[R-FROZEN-DERIVE]``: run, never modified; default guards) and is read from
  the probe path ``data/raw/_validation-source/`` rather than the loader path,
  so nothing can arm it by accident. It is derived on GROSS load; section A
  reports the bite on both the raw gross-basis MW and a net-rebased envelope,
  because the loader applies the MW figure directly to the model's NET columns
  (recorded as a finding, not silently reconciled).

Rule 22 ``[R-HOLDOUT]``: every window is {2023, 2024, 2025}. No 2022-or-earlier
quantity appears anywhere; the 60-Day DAM ``*_Jan-Mar`` files carry trailing
Nov/Dec-2022 delivery rows and the declared loader drops them by reindexing on
the model's own 8760 index for the year.

Usage
-----
    python scripts/probes/ercot127_coal_dispatch_band.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import base64
import gzip
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

# Same fixed edges ERCOT-126 §1.5 published, so the two lanes' price-conditional
# tables are directly comparable. Set from the model's coal stack geometry
# (ERCOT-122 §3) plus the $15/$50 outer brackets, never from a residual.
PRICE_EDGES = (-np.inf, 15.0, 20.0, 25.0, 30.0, 35.0, 50.0, np.inf)
PRICE_LABELS = ("<15", "15-20", "20-25", "25-30", "30-35", "35-50", ">=50")

RAMP_ENVELOPE = (
    paths.RAW_DIR / "_validation-source" / "ercot127_campd_ramp_envelopes_ERCOT.csv"
)
OUT_JSON = paths.CALIBRATION_DIR / "ercot127_coal_dispatch_band.json"


# --------------------------------------------------------------------------
# loaders (verbatim from the ERCOT-126 probe, so the bases match)
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


def bench_coal_actual_twh(year: int) -> float:
    """Committed EIA-923 bench coal total (net TWh), the gross->net anchor."""
    cf = load_bench(year)["bench"]["classFull"]
    return float(cf.get("COAL_PRB", 0.0)) + float(cf.get("COAL_LIGNITE", 0.0))


def campd_coal_gross(year: int) -> pd.DataFrame:
    """Per-plant hourly CAMPD gross load (MW) for the ERCOT coal fleet."""
    df = pd.read_parquet(
        paths.RAW_DIR / "campd-unit-level" / f"TX_{year}.parquet",
        columns=["facilityId", "date", "hour", "grossLoad", "primaryFuelInfo"],
    )
    coal = df.primaryFuelInfo.astype(str).str.contains("Coal|Lignite", case=False, na=False)
    df = df[coal].copy()
    df["facilityId"] = df.facilityId.astype(int)
    df = df[df.facilityId.isin(COAL_PLANTS)]
    df["ts"] = pd.to_datetime(df.date) + pd.to_timedelta(df.hour, unit="h")
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


def load_ramp_envelope() -> dict[int, tuple[float, float, float, str]]:
    """Per-coal-plant measured ST ramp envelope (up_mw, dn_mw, pmax_obs, basis).

    Plants without a well-observed ``basis == "plant"`` row take the ISO ST
    ``class_fraction`` row exactly as :func:`build_ramp_groups` would, so the
    bite measured here is the bite the LP would actually see.
    """
    df = pd.read_csv(RAMP_ENVELOPE)
    st_frac = df[(df.plant_code == 0) & (df.bucket == "ST")].iloc[0]
    out: dict[int, tuple[float, float, float, str]] = {}
    for code in COAL_PLANTS:
        row = df[(df.plant_code == code) & (df.bucket == "ST") & (df.basis == "plant")]
        if len(row):
            r = row.iloc[0]
            out[code] = (float(r.ramp_up_mw), float(r.ramp_dn_mw),
                         float(r.pmax_obs_mw), "plant")
        else:
            out[code] = (float(st_frac.ramp_up_mw), float(st_frac.ramp_dn_mw),
                         float("nan"), "class_fraction")
    return out


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def flat_top_mask(mw: np.ndarray, month: np.ndarray, tol: float = 0.995) -> np.ndarray:
    """Boolean mask of hours delivering within ``tol`` of that month's own max.

    The ERCOT-126 §1.4 pin statistic, returned as a mask so section B can split
    it into ENTRY and SUSTAIN hours. Online hours only.
    """
    online = mw > 1.0
    hit = np.zeros(mw.size, dtype=bool)
    for mo in range(1, 13):
        sel = (month == mo) & online
        if sel.sum() < 24:
            continue
        hit |= sel & (mw >= tol * mw[sel].max())
    return hit


def ramp_bite(mw: np.ndarray, up: float, dn: float) -> dict:
    """Hour transitions a series makes that a two-sided envelope forbids.

    Returns the count of violating up/down transitions and the total MWh by
    which the series exceeds the envelope — the upper bound on what a ramp row
    could remove, since the LP would have to reshape at least that much.
    """
    d = np.diff(mw)
    up_v = d > up
    dn_v = (-d) > dn
    return {
        "transitions": int(d.size),
        "up_violations": int(up_v.sum()),
        "dn_violations": int(dn_v.sum()),
        "violation_share": round(float((up_v | dn_v).sum() / d.size), 5),
        "excess_mwh": round(float((d[up_v] - up).sum() + ((-d[dn_v]) - dn).sum()), 1),
        "max_up_move_mw": round(float(d.max()) if d.size else 0.0, 1),
        "max_dn_move_mw": round(float((-d).max()) if d.size else 0.0, 1),
    }


def interior_share(mw: np.ndarray, cap: np.ndarray) -> dict:
    """How much of an online series sits in the INTERIOR of its own range.

    Loading is taken against the plant's declared ceiling. ``interior`` is the
    share of online hours strictly between 0.05 and 0.95 of the declared
    ceiling, i.e. neither near-floor nor near-ceiling; ``distinct_levels``
    counts the loading values the series actually occupies at 1 % resolution —
    a 5-tranche curve occupies few, a continuously-dispatched unit many.
    """
    online = (mw > 1.0) & (cap > 1.0)
    if online.sum() < 24:
        return {"online_hours": int(online.sum())}
    load = mw[online] / cap[online]
    return {
        "online_hours": int(online.sum()),
        "p05": round(float(np.percentile(load, 5)), 3),
        "p25": round(float(np.percentile(load, 25)), 3),
        "p50": round(float(np.percentile(load, 50)), 3),
        "p75": round(float(np.percentile(load, 75)), 3),
        "p95": round(float(np.percentile(load, 95)), 3),
        "interior_share": round(float(((load > 0.05) & (load < 0.95)).mean()), 3),
        "distinct_levels_pct_grain": int(np.unique(np.round(load, 2)).size),
    }


def section_e_coal_min_load() -> dict:
    """E -- the measured COAL committed min-load fraction, FULL SPAN.

    The ERCOT-62 derive (``scenarios.py:5699-5702``) published per-class
    committed ``LSL/HSL`` capacity-weighted p50s from the 60-Day DAM Gen
    Resource corpus and recorded CC 0.574 (the value
    ``ercot_gas_bridge_min_load_frac`` carries), CT 0.744 and ST_GAS 0.205 —
    but **no coal row**, because coal was not a bridge candidate then. This
    reproduces that construction verbatim for ``Resource Type == CLLIG``, so
    the coal parameter is identified on exactly the instrument, corpus and
    convention an already-accepted registered parameter was.

    ``committed`` is ``HSL > 0`` (the resource carries an accepted COP
    registration for the hour). Both the capacity-weighted p50 of the
    per-(resource, hour) ``LSL/HSL`` ratio and the fleet aggregate
    ``ΣLSL/ΣHSL`` (ERCOT-126 §3.1b's statistic) are reported, per year and
    pooled, so the parameter can be read on either convention and the two
    lanes reconcile.
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
        # Rule 22 [R-HOLDOUT]: the *_Jan-Mar files carry trailing Nov/Dec-2022
        # delivery rows. Dropped here, explicitly, before any aggregate.
        df = df[df.ts.dt.year.isin(YEARS)]
        parts.append(df[["ts", "Resource Name", "HSL", "LSL"]])
    S = pd.concat(parts, ignore_index=True)
    S = S[(S.HSL > 0.0) & S.LSL.notna()]
    S = S.assign(frac=(S.LSL / S.HSL).clip(0.0, 1.0))

    def _wp50(d: pd.DataFrame) -> float:
        """Capacity(HSL)-weighted median of the LSL/HSL ratio."""
        d = d.sort_values("frac")
        w = d.HSL.to_numpy(dtype=float).cumsum()
        return float(d.frac.to_numpy()[np.searchsorted(w, w[-1] / 2.0)])

    out: dict = {"convention": "ERCOT-62 derive, Resource Type CLLIG, committed = HSL>0"}
    for year in YEARS:
        d = S[S.ts.dt.year == year]
        if d.empty:
            continue
        out[str(year)] = {
            "resource_hours": int(len(d)),
            "distinct_resources": int(d["Resource Name"].nunique()),
            "cap_weighted_p50_lsl_over_hsl": round(_wp50(d), 4),
            "fleet_aggregate_lsl_over_hsl": round(float(d.LSL.sum() / d.HSL.sum()), 4),
        }
    out["pooled"] = {
        "resource_hours": int(len(S)),
        "cap_weighted_p50_lsl_over_hsl": round(_wp50(S), 4),
        "fleet_aggregate_lsl_over_hsl": round(float(S.LSL.sum() / S.HSL.sum()), 4),
    }
    return out


def section_f_forced_share(keeper_payload: dict, fracs: tuple[float, ...]) -> dict:
    """F -- the EX-ANTE C8 forced-share cost of flooring coal at ``frac``.

    Rule 20 ``[R-FORCED-BUDGET]`` / gate C8: coal forces ZERO energy today
    (D-2 carries no COAL row in any year), so any floor moves it off 0.0 % and
    the charter requires the expected value stated BEFORE a solve. This is the
    honest upper bound: the floor level is taken as ``frac`` x the plant's own
    monthly maximum in the keeper's series (the keeper's realised
    ``pmax x availability``, the same monthly grain the pin statistic uses),
    every hour the keeper runs the plant below that level is lifted TO it, and
    the lifted energy is counted as forced. The LP would redistribute — it
    would displace other supply and could re-shape coal above the floor — so
    the true forced share lands at or below this, but the SCALE is decided
    here rather than discovered after a 50-minute solve.
    """
    out: dict = {}
    for year in YEARS:
        keeper = payload_coal_plants(keeper_payload, year)
        idx = hour_index(year)
        month = idx.month.to_numpy()
        per_frac: dict[str, dict] = {}
        for frac in fracs:
            forced = base = 0.0
            for mw in keeper.values():
                floor = np.zeros_like(mw)
                for mo in range(1, 13):
                    sel = (month == mo) & (mw > 1.0)
                    if sel.sum() < 24:
                        continue
                    floor[month == mo] = frac * mw[sel].max()
                # A floor only applies where the plant is committed; the keeper
                # running a plant at ~0 for a month is an outage, not a decommit
                # the floor should undo, so hours below 1 MW are left alone only
                # when the whole month is dark (handled by the < 24 h guard).
                lift = np.maximum(0.0, floor - mw)
                forced += float(np.minimum(floor, mw + lift)[lift > 0.0].sum())
                base += float(mw.sum() + lift.sum())
            per_frac[f"{frac:.3f}"] = {
                "forced_share_of_coal_energy": round(forced / max(base, 1e-9), 4),
                "coal_energy_twh_after_floor": round(base / 1e6, 3),
            }
        out[str(year)] = per_frac
    return out


def section_g_g1_ex_ante(keeper_payload: dict, fracs: tuple[float, ...]) -> dict:
    """G -- the charter's G1 gate, evaluated EX ANTE for a coal min-load floor.

    G1 requires loading-vs-price within 0.05 of actual in EVERY price band
    INCLUDING sub-$15 — the gate the ERCOT-116 measured envelope fails at
    9-15 pp. It is computed here on ERCOT-126 §1.5's own FLEET-AGGREGATE basis
    (Σ model MW / Σ declared MW over the band's hours), so the numbers are
    directly comparable to that table and to the gate as written.

    The floored series is the keeper's own hourly dispatch lifted to
    ``frac x`` the plant's monthly maximum wherever it runs below it — the
    same construction as section F, and a HARD LOWER BOUND on what the LP
    would produce, because the floor is a lower bound the LP cannot undercut
    and coal above the floor is in-merit and would not be backed off. It
    therefore answers the gate for the bottom bands, where the floor is the
    only thing acting, without a solve.
    """
    price = pd.read_parquet(
        paths.RAW_DIR / "_validation-source" / "actual_lmp_hourly_SPP.parquet"
    )
    out: dict = {}
    for year in YEARS:
        idx = hour_index(year)
        month = idx.month.to_numpy()
        gross = campd_coal_gross(year)
        gn = bench_coal_actual_twh(year) / (gross.to_numpy().sum() / 1e6)
        act = (gross * gn).to_numpy().sum(axis=1)
        live = dam_declared(year)
        keeper = payload_coal_plants(keeper_payload, year)
        dec = live.reindex(columns=sorted(COAL_PLANTS)).fillna(0.0).to_numpy().sum(axis=1)
        kee = sum(keeper.values())

        floored: dict[float, np.ndarray] = {}
        for frac in fracs:
            tot = np.zeros(8760)
            for mw in keeper.values():
                f = np.zeros_like(mw)
                for mo in range(1, 13):
                    sel = (month == mo) & (mw > 1.0)
                    if sel.sum() < 24:
                        continue
                    f[month == mo] = frac * mw[sel].max()
                tot += np.maximum(mw, f)
            floored[frac] = tot

        p = price[price.year == year].sort_values("hour")
        ph = p.rt.to_numpy(dtype=float)[:8760]
        band = np.asarray(pd.cut(ph, PRICE_EDGES, labels=PRICE_LABELS, right=False))
        rows: dict[str, dict] = {}
        for lab in PRICE_LABELS:
            sel = band == lab
            den = dec[sel].sum()
            if sel.sum() < 24 or den <= 0:
                continue
            r = {
                "hours": int(sel.sum()),
                "actual": round(float(act[sel].sum() / den), 3),
                "keeper": round(float(kee[sel].sum() / den), 3),
            }
            for frac in fracs:
                r[f"floor_{frac:.3f}"] = round(float(floored[frac][sel].sum() / den), 3)
            rows[lab] = r
        out[str(year)] = rows
    return out


def section_h_unit_grain() -> dict:
    """H -- what a LOW-LOADING real coal plant-hour actually IS, at UNIT grain.

    The decisive test for whether the section-E min-load parameter can be
    applied at the grain the LP offers. The model represents a coal plant as
    continuous per-plant tranches with no commitment integrality, so "plant at
    20 % of capability" is necessarily "everything at 20 %". CAMPD carries the
    UNIT grain, so the same plant-hour can be decomposed into how many units
    were synchronised and what loading those units held.

    A unit counts as synchronised at ``> 0.10 x`` its own observed maximum —
    a deliberately permissive bar, so the test cannot manufacture "units off"
    out of units merely running low. ``low`` plant-hours are ``0.02 < plant
    loading < 0.35`` of plant capability: the region a plant-grain min-load
    floor at the measured 0.364 would lift.
    """
    out: dict = {}
    for year in YEARS:
        df = pd.read_parquet(
            paths.RAW_DIR / "campd-unit-level" / f"TX_{year}.parquet",
            columns=["facilityId", "unitId", "date", "hour", "grossLoad",
                     "primaryFuelInfo"],
        )
        df = df[df.primaryFuelInfo.astype(str).str.contains(
            "Coal|Lignite", case=False, na=False)]
        df["facilityId"] = df.facilityId.astype(int)
        df = df[df.facilityId.isin(COAL_PLANTS)]
        df["ts"] = pd.to_datetime(df.date) + pd.to_timedelta(df.hour, unit="h")
        umax = df.groupby(["facilityId", "unitId"]).grossLoad.max().rename("umax")
        df = df.join(umax, on=["facilityId", "unitId"])
        df["on"] = df.grossLoad > 0.10 * df.umax
        g = df.groupby(["facilityId", "ts"]).agg(
            load=("grossLoad", "sum"), cap=("umax", "sum"),
            n_on=("on", "sum"), n=("on", "size"))
        g = g[g.cap > 0]
        g["pl"] = g.load / g.cap
        g["on_frac"] = g.n_on / g.n
        on = df[df.on]
        og = on.groupby(["facilityId", "ts"]).agg(l=("grossLoad", "sum"),
                                                  c=("umax", "sum"))
        g = g.join((og.l / og.c).rename("load_of_online"))
        low = g[(g.pl > 0.02) & (g.pl < 0.35)]
        allh = g[g.pl > 0.02]
        out[str(year)] = {
            "low_plant_hours": int(len(low)),
            "online_plant_hours": int(len(allh)),
            "low_share_of_online": round(len(low) / max(len(allh), 1), 4),
            "low_units_online_frac": round(float(low.on_frac.mean()), 3),
            "low_loading_of_online_units": round(float(low.load_of_online.mean()), 3),
            "all_units_online_frac": round(float(allh.on_frac.mean()), 3),
            "all_loading_of_online_units": round(float(allh.load_of_online.mean()), 3),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "ERCOT-127 Phase 1 — the coal dispatch band. Measures the ex-ante "
            "bite of the measured CAMPD ramp envelope on the keeper's coal, "
            "whether a trajectory bound can reach the flat-top pin at all, and "
            "whether the band is a conduct property or a representation "
            "artifact. Builds no LP and solves no year."
        )
    )
    ap.add_argument("--json-out", type=Path, default=OUT_JSON)
    args = ap.parse_args()

    keeper_payload = load_run_payload(KEEPER_RUN)
    env = load_ramp_envelope()
    price = pd.read_parquet(
        paths.RAW_DIR / "_validation-source" / "actual_lmp_hourly_SPP.parquet"
    )

    result: dict = {
        "lane": "ercot127-coal-band",
        "keeper": KEEPER_RUN,
        "scope_fork": "owner chose (a): ERCOT-127 subsumes ERCOT-117 5.3",
        "ramp_envelope_source": str(RAMP_ENVELOPE.relative_to(_REPO)),
        "envelope": {
            COAL_PLANTS[c]: {
                "ramp_up_mw": v[0], "ramp_dn_mw": v[1],
                "pmax_obs_mw": v[2], "basis": v[3],
            }
            for c, v in sorted(env.items())
        },
        "years": {},
    }

    for year in YEARS:
        idx = hour_index(year)
        month = idx.month.to_numpy()
        gross = campd_coal_gross(year)
        gn = bench_coal_actual_twh(year) / (gross.to_numpy().sum() / 1e6)
        act = gross * gn
        live = dam_declared(year)
        keeper = payload_coal_plants(keeper_payload, year)

        yr: dict = {"gross_to_net_factor": round(float(gn), 4), "plants": {}}

        pin_entry_k = pin_sustain_k = 0.0
        pin_entry_forbidden_k = 0.0
        for code in sorted(COAL_PLANTS):
            name = COAL_PLANTS[code]
            a = act[code].to_numpy() if code in act else np.zeros(8760)
            k = keeper.get(code, np.zeros(8760))
            d = live[code].to_numpy() if code in live else np.zeros(8760)
            up, dn, pobs, basis = env[code]
            # class_fraction rows are FRACTIONS; resolve to MW on the plant's
            # own observed capability exactly as build_ramp_groups does.
            if basis == "class_fraction":
                cap = float(np.nanmax(a)) if np.isfinite(np.nanmax(a)) else 0.0
                up, dn = up * cap, dn * cap

            # --- A: envelope bite, keeper vs actual, gross- and net-basis
            bite_k = ramp_bite(k, up, dn)
            bite_a = ramp_bite(a, up, dn)
            bite_k_net = ramp_bite(k, up * gn, dn * gn)

            # --- B: can a ramp limit touch the pin?
            pin = flat_top_mask(k, month)
            entry = pin.copy()
            entry[1:] &= ~pin[:-1]          # first hour of each flat-top run
            sustain = pin & ~entry
            pin_entry_k += float(k[entry].sum())
            pin_sustain_k += float(k[sustain].sum())
            # entries actually REACHED by a move the envelope forbids
            dk = np.diff(k, prepend=k[0])
            pin_entry_forbidden_k += float(k[entry & (dk > up)].sum())

            yr["plants"][name] = {
                "envelope_up_mw": round(float(up), 1),
                "envelope_dn_mw": round(float(dn), 1),
                "envelope_basis": basis,
                "keeper_bite_gross_basis": bite_k,
                "keeper_bite_net_rebased": bite_k_net,
                "actual_bite": bite_a,
                "pin_hours": int(pin.sum()),
                "pin_entry_hours": int(entry.sum()),
                "pin_sustain_hours": int(sustain.sum()),
                "keeper_interior": interior_share(k, d),
                "actual_interior": interior_share(a, d),
            }

        pin_tot = pin_entry_k + pin_sustain_k
        yr["pin_decomposition"] = {
            "pin_energy_twh": round(pin_tot / 1e6, 3),
            "entry_share_of_pin": round(pin_entry_k / max(pin_tot, 1e-9), 4),
            "sustain_share_of_pin": round(pin_sustain_k / max(pin_tot, 1e-9), 4),
            "entry_reached_by_forbidden_move_share": round(
                pin_entry_forbidden_k / max(pin_tot, 1e-9), 4),
        }

        # --- D: cross-plant spread in the same hour, by price band
        # The committed actual-price sidecar is keyed (year, hour-of-year); the
        # RT column is the measured settlement price ERCOT-126 §1.5 binned on.
        p = price[price.year == year].sort_values("hour")
        ph = p.rt.to_numpy(dtype=float)
        if ph.size >= 8760:
            ph = ph[:8760]
            band = pd.cut(ph, PRICE_EDGES, labels=PRICE_LABELS, right=False)
            kmat = np.vstack([keeper.get(c, np.zeros(8760)) for c in sorted(COAL_PLANTS)])
            amat = np.vstack([
                act[c].to_numpy() if c in act else np.zeros(8760)
                for c in sorted(COAL_PLANTS)
            ])
            dmat = np.vstack([
                live[c].to_numpy() if c in live else np.zeros(8760)
                for c in sorted(COAL_PLANTS)
            ])
            with np.errstate(invalid="ignore", divide="ignore"):
                kl = np.where(dmat > 1.0, kmat / dmat, np.nan)
                al = np.where(dmat > 1.0, amat / dmat, np.nan)
            rows = {}
            for lab in PRICE_LABELS:
                sel = np.asarray(band == lab)
                if sel.sum() < 24:
                    continue
                rows[lab] = {
                    "hours": int(sel.sum()),
                    "keeper_mean_loading": round(float(np.nanmean(kl[:, sel])), 3),
                    "actual_mean_loading": round(float(np.nanmean(al[:, sel])), 3),
                    # cross-plant dispersion WITHIN the hour, averaged over hours
                    "keeper_xplant_sd": round(float(np.nanmean(np.nanstd(kl[:, sel], axis=0))), 3),
                    "actual_xplant_sd": round(float(np.nanmean(np.nanstd(al[:, sel], axis=0))), 3),
                }
            yr["loading_by_price_band"] = rows

        result["years"][str(year)] = yr

    result["coal_min_load_measured"] = section_e_coal_min_load()
    # Fracs spanning both published conventions: ERCOT-126 §3.1b's fleet
    # aggregate (0.374-0.393), ERCOT-123 §4 / ERCOT-117 §5.3's probe-day and RT
    # figures (0.45 / 0.50), and the model's own COAL physical min-stable
    # (constants.MIN_STABLE_PCT_PHYSICAL["COAL"] = 0.40, NREL WWSIS-2).
    result["forced_share_ex_ante"] = section_f_forced_share(
        keeper_payload, (0.25, 0.374, 0.40, 0.45, 0.50)
    )
    result["g1_ex_ante"] = section_g_g1_ex_ante(keeper_payload, (0.364, 0.374))
    result["unit_grain"] = section_h_unit_grain()

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.json_out}")

    # ---- console summary ----
    print("\n=== A/B: ramp-envelope bite and the pin (per year, fleet) ===")
    for year in YEARS:
        yr = result["years"][str(year)]
        upv = sum(p["keeper_bite_gross_basis"]["up_violations"] for p in yr["plants"].values())
        dnv = sum(p["keeper_bite_gross_basis"]["dn_violations"] for p in yr["plants"].values())
        aupv = sum(p["actual_bite"]["up_violations"] for p in yr["plants"].values())
        adnv = sum(p["actual_bite"]["dn_violations"] for p in yr["plants"].values())
        exc = sum(p["keeper_bite_gross_basis"]["excess_mwh"] for p in yr["plants"].values())
        pd_ = yr["pin_decomposition"]
        print(
            f"{year}: keeper forbidden moves {upv} up / {dnv} dn "
            f"({exc:,.0f} MWh excess) | actual {aupv} up / {adnv} dn | "
            f"pin {pd_['pin_energy_twh']} TWh, sustain "
            f"{pd_['sustain_share_of_pin']:.1%}, entry via forbidden move "
            f"{pd_['entry_reached_by_forbidden_move_share']:.2%}"
        )

    print("\n=== C: interior share / distinct levels (fleet-weighted plants) ===")
    for year in YEARS:
        yr = result["years"][str(year)]
        ki = [p["keeper_interior"].get("interior_share") for p in yr["plants"].values()]
        ai = [p["actual_interior"].get("interior_share") for p in yr["plants"].values()]
        kd = [p["keeper_interior"].get("distinct_levels_pct_grain") for p in yr["plants"].values()]
        ad = [p["actual_interior"].get("distinct_levels_pct_grain") for p in yr["plants"].values()]
        ki = [x for x in ki if x is not None]
        ai = [x for x in ai if x is not None]
        kd = [x for x in kd if x is not None]
        ad = [x for x in ad if x is not None]
        print(
            f"{year}: interior keeper {np.mean(ki):.3f} vs actual {np.mean(ai):.3f} | "
            f"distinct loading levels keeper {np.mean(kd):.0f} vs actual {np.mean(ad):.0f}"
        )

    print("\n=== E: measured COAL committed LSL/HSL (60-Day DAM, CLLIG) ===")
    for k, v in result["coal_min_load_measured"].items():
        if isinstance(v, dict):
            print(
                f"  {k:>7}: cap-weighted p50 {v['cap_weighted_p50_lsl_over_hsl']:.4f}"
                f"   fleet aggregate {v['fleet_aggregate_lsl_over_hsl']:.4f}"
                f"   ({v['resource_hours']:,} resource-hours)"
            )

    print("\n=== F: EX-ANTE C8 forced share if coal is floored at frac ===")
    fr = result["forced_share_ex_ante"]
    fracs = list(fr[str(YEARS[0])].keys())
    print("  frac  " + "".join(f"{y:>10}" for y in YEARS))
    for f in fracs:
        print(
            f"  {f}  "
            + "".join(
                f"{fr[str(y)][f]['forced_share_of_coal_energy']:>10.1%}" for y in YEARS
            )
        )

    print("\n=== G: G1 EX ANTE — fleet-aggregate loading vs price (ERCOT-126 1.5 basis) ===")
    for year in YEARS:
        rows = result["g1_ex_ante"][str(year)]
        print(f"-- {year}   (gate: |model - actual| <= 0.05 in EVERY band)")
        for lab, r in rows.items():
            ks = "PASS" if abs(r["keeper"] - r["actual"]) <= 0.05 else "FAIL"
            f1 = r["floor_0.364"]
            fs = "PASS" if abs(f1 - r["actual"]) <= 0.05 else "FAIL"
            print(
                f"  {lab:>6} n={r['hours']:5d}  act {r['actual']:.3f}"
                f"   keeper {r['keeper']:.3f} [{ks}]"
                f"   floor.364 {f1:.3f} [{fs}]"
            )

    print("\n=== H: what a LOW-LOADING real coal plant-hour IS, at UNIT grain ===")
    for year in YEARS:
        h = result["unit_grain"][str(year)]
        print(
            f"  {year}: low plant-hours {h['low_plant_hours']:,} "
            f"({h['low_share_of_online']:.1%} of online) -> units online "
            f"{h['low_units_online_frac']:.3f} (fleet {h['all_units_online_frac']:.3f}), "
            f"loading OF THE ONLINE units {h['low_loading_of_online_units']:.3f} "
            f"(fleet {h['all_loading_of_online_units']:.3f})"
        )

    print("\n=== D: loading and cross-plant spread by price band ===")
    for year in YEARS:
        rows = result["years"][str(year)].get("loading_by_price_band", {})
        if not rows:
            continue
        print(f"-- {year}")
        for lab, r in rows.items():
            print(
                f"  {lab:>6} n={r['hours']:5d}  loading act {r['actual_mean_loading']:.3f}"
                f" / keeper {r['keeper_mean_loading']:.3f}   x-plant sd act"
                f" {r['actual_xplant_sd']:.3f} / keeper {r['keeper_xplant_sd']:.3f}"
            )


if __name__ == "__main__":
    main()
