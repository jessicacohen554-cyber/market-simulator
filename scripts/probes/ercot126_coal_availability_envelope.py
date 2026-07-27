#!/usr/bin/env python
"""ERCOT-126 — decomposing the coal availability-envelope residual.

Phase 1 of the lane chartered after ERCOT-122/123/124/125 closed the entire coal
offer surface (level, reach, upper tail, owner split) and left the ERCOT-116/121
availability envelope as the only structurally-open coal candidate.

Diagnostic only: no LP is built, no year is solved, nothing is registered, and
no ``ScenarioConfig`` field or solve path is touched. Every model quantity is
read from the KEEPER's committed sidecars/payload rather than replayed
(CLAUDE.md rule 15 ``[R-DASHBOARD]``); every actual is read from a raw source.

Sections
--------
A  the envelope frame — coal energy against the DAM-declared COP envelope, and
   the split of the declared-minus-actual gap into COMMITMENT (declared live,
   produced nothing) vs LOADING (online, below declared)
B  the seasonal decomposition — keeper and the already-solved ERCOT-116 arm
   against actual, by month, on one denominator
C  the PIN — share of annual coal energy delivered on a flat monthly top, the
   availability-ride signature, model vs actual, per plant
D  is the declared envelope REALIZABLE? per-plant measured maxima against the
   COP declaration (the rule 14 ``[R-ACCURATE]`` misalignment test)
E  price-conditional loading — the real fleet's, the keeper's and the arm's
   response to the same measured RT price
F  the measured AS power reservation on coal, FULL SPAN, from the 60-Day DAM
   disclosure's own award block (the ERCOT-123 §2 statistic, which existed only
   on 82 probe days, re-measured on every hour of 2023-2025)
G  the time-resolution (Jensen) test — how much an 8760-hourly merit order
   over-delivers a SATURATING supply curve relative to the 15-minute market it
   is scored against, using the committed measured coal supply curve

Bases, stated once
------------------
* ``declared`` is the 60-Day DAM disclosure's accepted COP ``live_mw`` summed
  over the CLLIG resources of each model plant — the same series
  ``ercot_thermal_dam_availability_plant`` reads. It is an ERCOT HSL, i.e. NET
  at the point of interconnection.
* ``actual`` is CAMPD unit-level ``grossLoad`` over the coal-fuelled units of
  the ten ERCOT coal plants, converted to NET by the per-year factor measured
  against the committed EIA-923 bench ``classFull`` coal total. The factor is
  reported in the output; it is a measured reconciliation, not a fitted value,
  and it is the SAME factor on both sides of every ratio.
* ``model`` is the keeper's own per-plant hourly (payload, CF% of nameplate) or
  its class hourly sidecar; both agree to 0.01 TWh.

Rule 22 ``[R-HOLDOUT]``: every window is {2023, 2024, 2025}. The DAM disclosure
files carry a handful of Nov/Dec-2022 delivery rows; section F drops them
explicitly rather than letting them into an aggregate.

Sampling: sections A-F are FULL SPAN. Section G's supply curve is the committed
ERCOT-124 artifact and carries that artifact's 82-probe-day, 2024-2025 bound;
the 15-minute prices it is evaluated on are full-span.

Usage
-----
    python scripts/probes/ercot126_coal_availability_envelope.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from market_sim.config import paths  # noqa: E402

YEARS: tuple[int, ...] = (2023, 2024, 2025)
KEEPER_RUN = "2026-07-26-ercot115-coal-marginal-hr"
KEEPER_BUNDLE = "ercot115_coal_floor_only"
ARM_RUN = "2026-07-26-ercot116-coal-avail-probe"

# The ten ERCOT coal plants, from data/raw/reference/master-plant-registry.csv
# (ba_code ERCO, plant_group COAL) plus Sandy Creek, which the bin sheet carries
# but the registry's ERCO/COAL filter drops.
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

# 60-Day DAM disclosure resource registration -> model plant. Derived from the
# resource capacities alone (ERCOT-124 §2 did the same arithmetic for Fayette):
# each group's registrations sum to its model plant's nameplate.
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

# Up-direction AS award columns in the 60-Day DAM Gen Resource Data. These are
# the products ERCOT nets off HSL to form HASL, so their sum IS the measured
# power reservation rule 13 [R-MEASURED] names as an admissible input.
AS_UP_AWARD_COLS: tuple[str, ...] = (
    "RegUp Awarded", "RRSPFR Awarded", "RRSFFR Awarded", "RRSUFR Awarded",
    "NonSpin Awarded", "ECRS Awarded", "ECRSSD Awarded",
)

# ERCOT-123 §4's measured LSL/HSL, the floor the ERCOT-117 §1.1 supply-curve
# convention always takes; used only as S(0) in section G. Mean of that
# section's two per-year subsets, verbatim.
LSL_SHARE_BY_YEAR: dict[int, float] = {2024: 0.4380, 2025: 0.4538}

# Price edges for the loading-vs-price cut. Fixed from the model's own coal
# stack geometry as ERCOT-122 §3 published it (delivered-PRB basis: the
# committed/econ_low bands land near $18, econ_high near $28, the peak band
# near $31-32) plus the $15/$50 outer brackets, BEFORE any residual was read.
PRICE_EDGES = (-np.inf, 15.0, 20.0, 25.0, 30.0, 35.0, 50.0, np.inf)
PRICE_LABELS = ("<15", "15-20", "20-25", "25-30", "30-35", "35-50", ">=50")

OUT_JSON = paths.CALIBRATION_DIR / "ercot126_coal_availability_envelope.json"


# --------------------------------------------------------------------------
# loaders
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
    """Per-plant hourly model MW for the coal classes, from a run payload.

    The payload stores each plant as a uint8 CF% of the bench nameplate — the
    run explorer's own codec (``docs/codebase-site/js/backcast-runs.js`` ``dec``
    then ``* npl / 100``); this reproduces it exactly.
    """
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
    """Per-plant hourly CAMPD gross load (MW) for the ERCOT coal fleet.

    Coal-fuelled UNITS only — the ``primaryFuelInfo`` filter is what keeps
    W A Parish's gas steamers out, the contamination ERCOT-121 §1a found in the
    plant-grain bench series and carried unfixed.
    """
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


def dam_declared(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-plant hourly COP declared live MW and registration rating MW."""
    av = pd.read_parquet(paths.RAW_DIR / "ercot-thermal-dam-availability-site-hourly.parquet")
    av = av[(av["class"] == "COAL") & (av.date.str.startswith(str(year)))].copy()
    av["plant"] = av.site.map(SITE_TO_PLANT)
    av["ts"] = pd.to_datetime(av.date) + pd.to_timedelta(av.he - 1, unit="h")
    idx = hour_index(year)
    live = av.pivot_table(index="ts", columns="plant", values="live_mw", aggfunc="sum")
    rate = av.pivot_table(index="ts", columns="plant", values="rating_mw", aggfunc="sum")
    return (live.reindex(idx).ffill().fillna(0.0), rate.reindex(idx).ffill().fillna(0.0))


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def flat_top_energy_share(mw: np.ndarray, month: np.ndarray, tol: float = 0.995) -> float:
    """Share of a series' energy delivered within ``tol`` of its own monthly max.

    The availability-ride signature: a unit whose binding constraint is its
    ceiling delivers a large share of its energy AT that ceiling, and the
    monthly grain lets the ceiling move with maintenance without being mistaken
    for dispatch. Online hours only, so an outage month cannot manufacture a hit.
    """
    online = mw > 1.0
    hit = np.zeros(mw.size, dtype=bool)
    for mo in range(1, 13):
        sel = (month == mo) & online
        if sel.sum() < 24:
            continue
        hit |= sel & (mw >= tol * mw[sel].max())
    return float(mw[hit].sum() / max(mw.sum(), 1e-9))


def section_a_b_c_d_e(payloads: dict[str, dict]) -> dict:
    """Sections A-E: one pass over the per-plant series per year."""
    out: dict[str, dict] = {}
    price = pd.read_parquet(paths.RAW_DIR / "_validation-source" / "actual_lmp_hourly_SPP.parquet")
    for year in YEARS:
        idx = hour_index(year)
        month = idx.month.to_numpy()
        gross = campd_coal_gross(year)
        gn = bench_coal_actual_twh(year) / (gross.to_numpy().sum() / 1e6)
        act = gross * gn                                     # -> net
        live, rate = dam_declared(year)
        keeper = payload_coal_plants(payloads["keeper"], year)
        arm = payload_coal_plants(payloads["arm"], year)

        a_f = act.sum(axis=1).to_numpy()
        d_f = live.sum(axis=1).to_numpy()
        k_f = sum(keeper.values())
        r_f = sum(arm.values())

        # A -- commitment vs loading split of the declared-minus-actual gap
        plants = {}
        commit_lost = 0.0
        for p in sorted(COAL_PLANTS):
            d = live[p].to_numpy() if p in live else np.zeros(8760)
            a = act[p].to_numpy() if p in act else np.zeros(8760)
            k = keeper.get(p, np.zeros(8760))
            r = arm.get(p, np.zeros(8760))
            declared_live = d > 1.0
            offline = declared_live & (a <= 1.0)
            online = declared_live & (a > 1.0)
            commit_lost += float(d[offline].sum())
            plants[COAL_PLANTS[p]] = {
                "declared_twh": round(d.sum() / 1e6, 3),
                "actual_twh": round(a.sum() / 1e6, 3),
                "keeper_twh": round(k.sum() / 1e6, 3),
                "arm_twh": round(r.sum() / 1e6, 3),
                "offline_while_declared_hours": int(offline.sum()),
                "offline_while_declared_twh": round(d[offline].sum() / 1e6, 3),
                "online_loading_act_over_declared": round(
                    float(a[online].sum() / max(d[online].sum(), 1e-9)), 3),
                "declared_max_over_nameplate": round(float(d.max() / max(rate[p].max(), 1e-9)), 3)
                if p in rate else None,
                "actual_max_over_declared_max": round(float(a.max() / max(d.max(), 1e-9)), 3),
                # C -- the pin
                "flat_top_energy_share_keeper": round(flat_top_energy_share(k, month), 3),
                "flat_top_energy_share_arm": round(flat_top_energy_share(r, month), 3),
                "flat_top_energy_share_actual": round(flat_top_energy_share(a, month), 3),
            }
        gap = float(d_f.sum() - a_f.sum())

        # B -- monthly
        monthly = []
        for mo in range(1, 13):
            s = month == mo
            monthly.append({
                "month": mo,
                "declared_gw": round(float(d_f[s].mean()) / 1e3, 3),
                "actual_gw": round(float(a_f[s].mean()) / 1e3, 3),
                "keeper_gw": round(float(k_f[s].mean()) / 1e3, 3),
                "arm_gw": round(float(r_f[s].mean()) / 1e3, 3),
            })

        # E -- price-conditional loading, one denominator, same hours
        rt = price[price.year == year].sort_values("hour").rt.to_numpy()[:8760]
        band = pd.cut(pd.Series(rt), PRICE_EDGES, labels=list(PRICE_LABELS))
        by_price = []
        for lab in PRICE_LABELS:
            s = (band == lab).to_numpy()
            if not s.sum():
                continue
            den = max(float(d_f[s].sum()), 1e-9)
            by_price.append({
                "band": lab, "hours": int(s.sum()),
                "actual_over_declared": round(float(a_f[s].sum()) / den, 3),
                "keeper_over_declared": round(float(k_f[s].sum()) / den, 3),
                "arm_over_declared": round(float(r_f[s].sum()) / den, 3),
            })

        out[str(year)] = {
            "gross_to_net_factor": round(gn, 4),
            "declared_twh": round(float(d_f.sum()) / 1e6, 3),
            "actual_twh": round(float(a_f.sum()) / 1e6, 3),
            "keeper_twh": round(float(k_f.sum()) / 1e6, 3),
            "arm_twh": round(float(r_f.sum()) / 1e6, 3),
            "keeper_minus_actual_twh": round(float(k_f.sum() - a_f.sum()) / 1e6, 3),
            "arm_minus_actual_twh": round(float(r_f.sum() - a_f.sum()) / 1e6, 3),
            "gap_share_commitment": round(commit_lost / max(gap, 1e-9), 3),
            "gap_share_loading": round(1.0 - commit_lost / max(gap, 1e-9), 3),
            "fleet_flat_top_energy_share": {
                "keeper": round(sum(v.sum() * flat_top_energy_share(v, month)
                                    for v in keeper.values()) / max(k_f.sum(), 1e-9), 3),
                "arm": round(sum(v.sum() * flat_top_energy_share(v, month)
                                 for v in arm.values()) / max(r_f.sum(), 1e-9), 3),
                "actual": round(sum(act[p].to_numpy().sum()
                                    * flat_top_energy_share(act[p].to_numpy(), month)
                                    for p in act) / max(a_f.sum(), 1e-9), 3),
            },
            "monthly": monthly,
            "by_price_band": by_price,
            "plants": plants,
        }
    return out


def section_f_as_reservation() -> dict:
    """F -- the measured up-AS power reservation on coal, full span.

    ERCOT-123 §2 measured ``HSL - HASL`` and the awarded block on the 82 SCED
    probe days. The 60-Day DAM disclosure carries the award block for every
    hour of 2023-2025, so the same quantity is measurable full span — which is
    what a keeper needs (rule 16 ``[R-ALLYEARS]``) and what the SCED instrument
    cannot give.
    """
    files = sorted((paths.RAW_DIR / "ercot").glob(
        "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_20*.parquet"))
    files = [f for f in files if "2026" not in f.name]
    acc: dict[pd.Timestamp, dict[str, float]] = {}
    for f in files:
        df = pd.read_parquet(f)
        df = df[df["Resource Type"] == "CLLIG"]
        if df.empty:
            continue
        cols = [c for c in AS_UP_AWARD_COLS if c in df.columns]
        df = df.assign(_up=df[cols].fillna(0.0).sum(axis=1))
        ts = (pd.to_datetime(df["Delivery Date"])
              + pd.to_timedelta(df["Hour Ending"].astype(str).str.slice(0, 2).astype(int) - 1,
                                unit="h"))
        df = df.assign(ts=ts)
        # Rule 22 [R-HOLDOUT]: the *_Jan-Mar files carry trailing Nov/Dec-2022
        # delivery rows. Drop them here, explicitly, rather than in a later mean.
        df = df[df.ts.dt.year.isin(YEARS)]
        for t, row in df.groupby("ts").agg(hsl=("HSL", "sum"), lsl=("LSL", "sum"),
                                           up=("_up", "sum")).iterrows():
            a = acc.setdefault(t, {"hsl": 0.0, "lsl": 0.0, "up": 0.0})
            for k in a:
                a[k] += float(row[k])
    S = pd.DataFrame(acc).T.sort_index()
    S.index = pd.DatetimeIndex(S.index)
    out = {}
    for year in YEARS:
        s = S[S.index.year == year]
        if s.empty:
            continue
        out[str(year)] = {
            "hours_covered": int(len(s)),
            "fleet_hsl_gw_mean": round(float(s.hsl.mean()) / 1e3, 3),
            "fleet_lsl_over_hsl": round(float(s.lsl.sum() / s.hsl.sum()), 4),
            "up_as_gw_mean": round(float(s.up.mean()) / 1e3, 4),
            "up_as_share_of_hsl": round(float(s.up.sum() / s.hsl.sum()), 4),
            "up_as_twh_equivalent": round(float(s.up.sum()) / 1e6, 3),
        }
    return out


def section_g_resolution() -> dict:
    """G -- the time-resolution (Jensen) gap on a saturating supply curve.

    S(p) is the committed ERCOT-124 measured coal RT supply curve (share of
    HASL offered at or below p, floored at LSL/HASL per the ERCOT-117 §1.1
    convention). Evaluated two ways on the SAME 15-minute ERCOT settlement
    prices: the mean of S over the four intervals (what a 15-minute market
    delivers) against S at the hourly mean price (what an hourly merit order
    delivers). The difference is a pure artifact of time resolution — no model
    quantity and no fitted value enters.
    """
    art_path = paths.RAW_DIR / "_validation-source" / "offer_curve_sced_coal_uppertail.json"
    art = json.loads(art_path.read_text())
    out = {}
    for year in (2024, 2025):                      # the artifact's own two years
        z = zipfile.ZipFile(paths.RAW_DIR / "lmp-data" / f"RTMLZHBSPP_{year}.zip")
        xl = pd.ExcelFile(io.BytesIO(z.read(z.namelist()[0])))
        d = pd.concat([xl.parse(s) for s in xl.sheet_names], ignore_index=True)
        d = d[(d["Settlement Point Name"] == "HB_BUSAVG") & (d["Repeated Hour Flag"] == "N")]
        d = d.assign(ts=pd.to_datetime(d["Delivery Date"])
                     + pd.to_timedelta(d["Delivery Hour"] - 1, unit="h"))
        p = d["Settlement Point Price"].to_numpy(float)
        year_out = {"intervals": int(len(d)), "hours": int(d.ts.nunique()),
                    "mean_price": round(float(p.mean()), 2),
                    "mean_intra_hour_sd": round(float(d.groupby("ts")["Settlement Point Price"]
                                                      .std().mean()), 2)}
        for variant in ("ex_owner_split", "all"):
            cum = art[str(year)][variant]["cumulative_supply_share_of_hasl"]
            xs = [0.0] + [float(k[2:]) for k in cum]
            ys = [LSL_SHARE_BY_YEAR[year]] + list(cum.values())
            S = lambda q: np.interp(np.clip(q, 0.0, 5000.0), xs, ys)  # noqa: E731
            fine = d.assign(s=S(p)).groupby("ts").s.mean()
            coarse = pd.Series(S(d.groupby("ts")["Settlement Point Price"].mean().to_numpy()),
                               index=fine.index)
            year_out[variant] = {
                "supply_15min_market": round(float(fine.mean()), 4),
                "supply_hourly_merit_order": round(float(coarse.mean()), 4),
                "resolution_gap_pp_of_hasl": round(100.0 * float((coarse - fine).mean()), 3),
            }
        out[str(year)] = year_out
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=None,
                    help="Output JSON path (default the calibration validation dir).")
    ap.add_argument("--skip-resolution", action="store_true",
                    help="Skip section G (it parses two full-year 15-minute price workbooks).")
    args = ap.parse_args()

    payloads = {"keeper": load_run_payload(KEEPER_RUN), "arm": load_run_payload(ARM_RUN)}
    result = {
        "_provenance": {
            "lane": "ercot126-coal-avail-envelope",
            "keeper": KEEPER_RUN,
            "keeper_bundle": f"results/calibration/{KEEPER_BUNDLE}",
            "arm": ARM_RUN,
            "model_source": "committed dashboard payloads + bench sidecars; NO replay, NO solve",
            "actual_source": "CAMPD unit-level TX_<year>.parquet, coal-fuelled units of the ten "
                             "ERCOT coal plants, gross load converted to net by the per-year "
                             "factor measured against the committed EIA-923 bench classFull",
            "declared_source": "60-Day DAM disclosure accepted COP live_mw "
                               "(data/raw/ercot-thermal-dam-availability-site-hourly.parquet), "
                               "the series ercot_thermal_dam_availability_plant reads; ERCOT HSL, "
                               "net at the point of interconnection",
            "holdout": "rule 22 [R-HOLDOUT]: every window is {2023, 2024, 2025}; section F drops "
                       "the Nov/Dec-2022 delivery rows the DAM Jan-Mar files carry",
            "rule23_citation": "no parameter is chosen against a residual; the price edges are "
                               "the model's own published coal stack geometry (ERCOT-122 §3) and "
                               "the flat-top tolerance/grain are fixed a priori",
            "sampling": "sections A-F full span; section G's supply curve carries the committed "
                        "ERCOT-124 artifact's 82-probe-day 2024-2025 bound",
        },
        "envelope": section_a_b_c_d_e(payloads),
        "as_reservation_full_span": section_f_as_reservation(),
    }
    if not args.skip_resolution:
        result["time_resolution"] = section_g_resolution()

    out = Path(args.json_out) if args.json_out else OUT_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")

    for year in YEARS:
        e = result["envelope"][str(year)]
        print(f"{year}  declared {e['declared_twh']:7.2f}  actual {e['actual_twh']:6.2f}  "
              f"keeper {e['keeper_twh']:6.2f} ({e['keeper_minus_actual_twh']:+.2f})  "
              f"arm {e['arm_twh']:6.2f} ({e['arm_minus_actual_twh']:+.2f})  TWh")
        print(f"       gap split  commitment {e['gap_share_commitment']:.3f} / "
              f"loading {e['gap_share_loading']:.3f}   |   flat-top energy share "
              f"keeper {e['fleet_flat_top_energy_share']['keeper']:.3f} "
              f"arm {e['fleet_flat_top_energy_share']['arm']:.3f} "
              f"actual {e['fleet_flat_top_energy_share']['actual']:.3f}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
