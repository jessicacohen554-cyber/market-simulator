"""PJM C3c SUMMER-tail decomposition (no-LP, measured) — the pjm-111 keeper's
missing summer scarcity hours traced to measured unit-availability events the
outage overlay structurally cannot see.

Everything here is computed from committed artifacts + raw measured data only
(no solve, no config flip — rule 1 diagnostic-first):

  * model side: the committed pjm-111 dashboard payload
    (frontend/data/backcast/runs/2026-07-15-pjm-111-cc-reconcile.js —
    per-plant hourly LP dispatch, hourly system-price delta, zonal monthly
    duals, volErr);
  * actual side: frontend/data/backcast/bench/PJM/<year>.json.gz (CAMPD plant
    hourly + EIA-923 monthly), data/raw/_validation-source/
    actual_lmp_hourly_PJM.parquet (chronological DA/RT system price),
    data/raw/lmp-data/PJM_<year>_rt_da_monthly_lmps.csv (12 hubs hourly),
    data/raw/campd-unit-level/<STATE>_<year>.parquet (CEMS unit-hourly gross),
    data/raw/campd-unit-outages-PJM.csv (the committed >=5-day extract),
    data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet (F923
    delivered fuel costs).

Sections (run all by default, or --section <name>):

  tail      2025 tail anatomy: the 51 DA>$200 hours by month/event, which the
            model catches, and the missed-hour price gaps (summer vs winter).
  phantom   class- and plant-level model-minus-CAMPD MW **in the 22 summer
            tail hours** (the phantom mid-merit cushion, measured in the
            scarcity hours themselves).
  units     unit-level decomposition of the coal tail-hour shortfall vs summer
            demonstrated capability (CAMPD p99.5 of Jun-Sep 15): full stops
            covered by the >=5-day extract vs UNCOVERED short stops vs partial
            derates (never zero, so no zero-run window can exist).
  derivers  simulate the frozen deriver identification rules on PJM CEMS:
            (a) short-window guard on raw-annual CF vs on WHEN-OPERABLE CF
            (excluding the unit's own >=5-day windows), per year, with annual
            footprint + tail-hour capture; (b) the plant-level partial-plateau
            detector (frozen constants) — measured to over-fire ~43 TWh/yr on
            PJM's cycling fleet (inadmissible as-is); (c) a unit-grain plateau
            variant at the same frozen constants.
  fuel      F923 delivered-coal price-vintage check (2024 vs 2025) and the
            Dominion-belt vs cycler-belt delivered gas comparison.
  zonal     July zonal price surface: model per-zone monthly duals vs actual
            hub DA means (the congestion-premium comparison for lead 2).
  coalhod   July coal over-run by hour-of-day + p10-CF plateau signature
            (the D-1p coal companion; the CC D-1p lives in
            _pjm_d1p_diurnal_cycling.py).

Usage: .venv/bin/python scripts/probes/_pjm_c3c_summer_tail_decomp.py
           [--run-id 2026-07-15-pjm-111-cc-reconcile] [--section NAME]

Findings doc: docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md
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

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

RUNS_DIR = REPO / "frontend/data/backcast/runs"
BENCH_DIR = REPO / "frontend/data/backcast/bench/PJM"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
UNIT_DIR = REPO / "data/raw/campd-unit-level"
EXTRACT = REPO / "data/raw/campd-unit-outages-PJM.csv"
F923 = REPO / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"

HOURS = 8760
_MDAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH = np.repeat(np.arange(1, 13), np.array(_MDAYS) * 24)
HOD = np.arange(HOURS) % 24
# States whose CAMPD unit extracts cover the PJM fleet.
PJM_STATES = (
    "PA",
    "OH",
    "WV",
    "VA",
    "MD",
    "NJ",
    "IL",
    "IN",
    "KY",
    "MI",
    "DE",
    "NC",
    "TN",
    "DC",
)
# Frozen constants inherited from the existing derivers (never re-tuned here):
# scripts/data/derive_partial_outages.py and scripts/data/derive_campd_unit_outages.py.
BASELOAD_CF = 0.55
PLATEAU_MIN_DAYS = 5
PLATEAU_SMOOTH_DAYS = 7
PLATEAU_CEILING_FRAC = 0.65
PLATEAU_RUN_FLOOR = 0.06
SHORT_MAX_HOURS = 120  # < 5 days
TAIL_THR = 200.0


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
    """Model load-weighted hourly system price = actual RT + committed delta.

    NOTE: C3c's gated count is the ANY-ZONE max dual (payload ordc block);
    this reconstruction is the load-weighted mean — a lower bound used for
    the gap/headroom anatomy, with the ordc counts quoted alongside.
    """
    rt, _ = actual_prices(year)
    return rt + dec_i16(pay["years"][str(year)]["lmpDeltaHr"])[:HOURS]


def unit_gross(year: int, pids: set[str]) -> pd.DataFrame:
    frames = []
    for st in PJM_STATES:
        p = UNIT_DIR / f"{st}_{year}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(
            p, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
        )
        d = d[d.facilityId.isin(pids)]
        if len(d):
            frames.append(d)
    u = pd.concat(frames)
    u["grossLoad"] = u.grossLoad.fillna(0.0)
    u["dt"] = pd.to_datetime(u.date) + pd.to_timedelta(u.hour, unit="h")
    base = pd.Timestamp(f"{year}-01-01")
    u["hoy"] = ((u.dt - base).dt.total_seconds() // 3600).astype(int)
    return u[(u.hoy >= 0) & (u.hoy < HOURS)]


def coal_pids(bench_plants: dict) -> set[str]:
    return {
        pid
        for pid, b in bench_plants.items()
        if b.get("group", "").startswith("COAL")
        and "campd" in b
        and not b.get("ct_only")
    }


# ---------------------------------------------------------------- tail anatomy
def sec_tail(pay: dict) -> None:
    for year in (2023, 2024, 2025):
        rt, da = actual_prices(year)
        mp = model_price(pay, year)
        ordc = pay["years"][str(year)]["ordc"]["hoursGt200"]
        print(
            f"=== {year}: actual DA>${TAIL_THR:.0f} = {(da > TAIL_THR).sum()} h | "
            f"payload ordc model(any-zone)={ordc['model']} actual(RT)={ordc['actual']} | "
            f"model(load-weighted)>{TAIL_THR:.0f} = {(mp > TAIL_THR).sum()} h"
        )
        if year != 2025:
            continue
        tail = da > TAIL_THR
        by_mon = {
            int(m): int(c) for m, c in zip(*np.unique(MONTH[tail], return_counts=True))
        }
        print("  actual DA tail by month:", by_mon)
        summer = np.isin(MONTH, (6, 7, 8, 9))
        missed = tail & ~(mp > TAIL_THR)
        for lbl, mask in (("summer", missed & summer), ("winter", missed & ~summer)):
            if mask.any():
                g = TAIL_THR - mp[mask]
                print(
                    f"  missed {lbl} hours: {mask.sum()} | gap-to-{TAIL_THR:.0f} "
                    f"p25/p50/p75/max = {np.percentile(g, [25, 50, 75]).round(0)} {g.max():.0f}"
                )
        idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        print("  summer tail-hour roster (model = load-weighted):")
        for h in np.where(tail & summer)[0]:
            print(
                f"    {idx[h].strftime('%m-%d %H:00')} DA {da[h]:5.0f} model {mp[h]:5.0f} "
                f"{'CAUGHT' if mp[h] > TAIL_THR else 'miss'}"
            )


# ------------------------------------------------------------- class phantoms
def sec_phantom(pay: dict, year: int = 2025) -> None:
    bench = load_bench(year)["plants"]
    _, da = actual_prices(year)
    tail = (da > TAIL_THR) & np.isin(MONTH, (6, 7, 8, 9))
    jun, jul = tail & (MONTH == 6), tail & (MONTH == 7)
    yp = pay["years"][str(year)]["plants"]
    print(
        f"=== {year} phantom MW in the {tail.sum()} actual summer DA-tail hours (model − CAMPD)"
    )
    rows = []
    for pref in ("COAL", "CC_REGULAR", "CT", "ST_GAS"):
        mw_m = np.zeros(HOURS)
        mw_c = np.zeros(HOURS)
        for pid, mv in yp.items():
            b = bench.get(pid)
            if not b or not b.get("group", "").startswith(pref):
                continue
            if "campd" not in b or b.get("ct_only"):
                continue
            mw_m += dec_u8(mv["m"])[:HOURS] * b["npl"]
            mw_c += dec_u8(b["campd"])[:HOURS] * b["npl"]
        d = mw_m - mw_c
        print(
            f"  {pref:12s} tail {d[tail].mean():+7.0f} MW | Jun {d[jun].mean():+7.0f} | Jul {d[jul].mean():+7.0f}"
        )
    # per-plant coal
    print("  per-plant coal phantom in tail hours (|d| >= 40 MW):")
    for pid, mv in yp.items():
        b = bench.get(pid)
        if (
            not b
            or not b.get("group", "").startswith("COAL")
            or "campd" not in b
            or b.get("ct_only")
        ):
            continue
        m = dec_u8(mv["m"])[:HOURS] * b["npl"]
        c = dec_u8(b["campd"])[:HOURS] * b["npl"]
        d = m - c
        if abs(d[tail].mean()) < 40:
            continue
        rows.append(
            (
                b["name"][:22],
                b["zone"].replace("PJM_", ""),
                b["npl"],
                d[tail].mean(),
                d[jun].mean(),
                d[jul].mean(),
            )
        )
    rows.sort(key=lambda r: -r[3])
    for r in rows:
        print(
            f"    {r[0]:22s} {r[1]:10s} {r[2]:6.0f} MW  tail {r[3]:+6.0f}  Jun {r[4]:+6.0f}  Jul {r[5]:+6.0f}"
        )


# --------------------------------------------------------- unit decomposition
def sec_units(pay: dict, year: int = 2025) -> None:
    bench = load_bench(year)["plants"]
    _, da = actual_prices(year)
    tail_idx = np.where((da > TAIL_THR) & np.isin(MONTH, (6, 7, 8, 9)))[0]
    base = pd.Timestamp(f"{year}-01-01")
    tail_dt = {base + pd.Timedelta(hours=int(h)) for h in tail_idx}
    pids = coal_pids(bench)
    u = unit_gross(year, pids)
    ext = pd.read_csv(EXTRACT, parse_dates=["outage_start", "outage_end"])
    ext = ext[ext.duration_days >= PLATEAU_MIN_DAYS]
    summer = u[(u.date >= f"{year}-06-01") & (u.date <= f"{year}-09-15")]
    cap_s = (
        summer.groupby(["facilityId", "unitId"])["grossLoad"]
        .quantile(0.995)
        .rename("cap_s")
    )
    ut = u[u.dt.isin(tail_dt)].merge(cap_s, on=["facilityId", "unitId"])
    cov = []
    for f, uid, dt in zip(ut.facilityId, ut.unitId, ut.dt):
        w = ext[
            (ext.facility_id.astype(str) == str(f))
            & (ext.unit_id.astype(str) == str(uid))
        ]
        cov.append(
            bool(
                (
                    (w.outage_start <= dt) & (dt <= w.outage_end + pd.Timedelta(days=1))
                ).any()
            )
        )
    ut["covered"] = cov
    ut["short"] = ut.grossLoad <= 0.02 * ut.cap_s
    ut["partial"] = (~ut.short) & (ut.grossLoad < 0.92 * ut.cap_s)
    ut["sf"] = (ut.cap_s - ut.grossLoad).clip(lower=0)
    n = len(tail_idx)
    print(
        f"=== {year} coal unit-level shortfall vs SUMMER demonstrated capability, {n} tail hours (mean MW):"
    )
    print(
        f"  full-stop UNCOVERED (short-outage bucket): {ut.loc[ut.short & ~ut.covered, 'sf'].sum() / n:6.0f}\n"
        f"  full-stop covered by >=5d extract:          {ut.loc[ut.short & ut.covered, 'sf'].sum() / n:6.0f}\n"
        f"  PARTIAL derate (never zero, no window):     {ut.loc[ut.partial, 'sf'].sum() / n:6.0f}"
    )
    tab = ut.groupby(["facilityId", "unitId"]).apply(
        lambda d: pd.Series(
            {
                "cap_s": float(d.cap_s.iloc[0]),
                "short_unc": float(d.loc[d.short & ~d.covered, "sf"].sum()),
                "partial": float(d.loc[d.partial, "sf"].sum()),
            }
        ),
        include_groups=False,
    )
    tab = tab[(tab.short_unc > 500) | (tab.partial > 500)].sort_values(
        ["short_unc", "partial"], ascending=False
    )
    print("  units with >500 MWh tail-hour shortfall (MWh over the tail hours):")
    for (f, uid), r in tab.iterrows():
        print(
            f"    {str(f):>6s} u{str(uid):>4s} cap_s {r.cap_s:5.0f}  short_uncov {r.short_unc:7.0f}  partial {r.partial:7.0f}"
        )


# ------------------------------------------------------- deriver simulations
def _detect_plateau(cf: np.ndarray) -> list[tuple[int, int, float]]:
    """The partial-outage deriver's frozen plateau rule (derive_partial_outages)."""
    nd = cf.shape[0] // 24
    day = cf[: nd * 24].reshape(nd, 24)
    dmax, dmean = day.max(1), day.mean(1)
    running = dmean > PLATEAU_RUN_FLOOR
    if not running.any():
        return []
    ref = float(np.percentile(dmax[running], 90))
    if ref <= 0:
        return []
    sm = (
        pd.Series(dmax)
        .rolling(PLATEAU_SMOOTH_DAYS, center=True, min_periods=4)
        .median()
        .to_numpy()
    )
    partial = running & (sm < PLATEAU_CEILING_FRAC * ref)
    out, i = [], 0
    while i < nd:
        if partial[i]:
            j = i
            while j < nd and partial[j]:
                j += 1
            if j - i >= PLATEAU_MIN_DAYS:
                out.append((i, j, min(1.0, float(np.median(dmax[i:j])) / ref)))
            i = j
        else:
            i += 1
    return out


def sec_derivers(pay: dict) -> None:
    ext = pd.read_csv(EXTRACT, parse_dates=["outage_start", "outage_end"])
    ext5 = ext[ext.duration_days >= PLATEAU_MIN_DAYS]
    for year in (2023, 2024, 2025):
        bench = load_bench(year)["plants"]
        pids = coal_pids(bench)
        u = unit_gross(year, pids)
        rt, da = actual_prices(year)
        mp = model_price(pay, year)
        tail = da > TAIL_THR
        base = pd.Timestamp(f"{year}-01-01")
        recov_frozen = np.zeros(HOURS)
        recov_oper = np.zeros(HOURS)
        recov_up = np.zeros(HOURS)
        twh_frozen = twh_oper = twh_up = 0.0
        nf = no = nu = 0
        for (pid, uid), d in u.groupby(["facilityId", "unitId"]):
            g = np.zeros(HOURS)
            g[d.hoy.to_numpy()] = d.grossLoad.to_numpy()
            cap = np.percentile(g, 99.5)
            if cap <= 60:  # skip CT-scale/tiny units (overlay convention)
                continue
            w = ext5[
                (ext5.facility_id.astype(str) == str(pid))
                & (ext5.unit_id.astype(str) == str(uid))
            ]
            oper = np.ones(HOURS, dtype=bool)
            for r in w.itertuples(index=False):
                m0 = max(0, int((r.outage_start - base).total_seconds() // 3600))
                m1 = min(
                    HOURS,
                    int(
                        (r.outage_end + pd.Timedelta(days=1) - base).total_seconds()
                        // 3600
                    ),
                )
                if m1 > m0:
                    oper[m0:m1] = False
            ann_cf = g.mean() / cap
            oper_cf = g[oper].mean() / cap if oper.any() else 0.0
            off = g <= 0.02 * cap
            idx = 0
            while idx < HOURS:
                if off[idx]:
                    k = idx
                    while k < HOURS and off[k]:
                        k += 1
                    if 24 <= k - idx < SHORT_MAX_HOURS and oper[idx:k].all():
                        if ann_cf >= BASELOAD_CF:
                            recov_frozen[idx:k] += cap
                            twh_frozen += cap * (k - idx) / 1e6
                            nf += 1
                        if oper_cf >= BASELOAD_CF:
                            recov_oper[idx:k] += cap
                            twh_oper += cap * (k - idx) / 1e6
                            no += 1
                    idx = k
                else:
                    idx += 1
            if oper_cf >= BASELOAD_CF:
                for i, j, f in _detect_plateau(g / cap):
                    recov_up[i * 24 : j * 24] += (1 - f) * cap
                    twh_up += (1 - f) * cap * (j - i) * 24 / 1e6
                    nu += 1
        print(
            f"=== {year} deriver-rule simulation (coal units, no in-merit filter — upper bounds):"
        )
        print(
            f"  SHORT frozen guard (raw annual CF>={BASELOAD_CF}):   {nf:3d} win | "
            f"{twh_frozen:5.2f} TWh/yr | tail capture {recov_frozen[tail].mean() if tail.any() else 0:5.0f} MW"
        )
        print(
            f"  SHORT when-operable guard (oper CF>={BASELOAD_CF}):  {no:3d} win | "
            f"{twh_oper:5.2f} TWh/yr | tail capture {recov_oper[tail].mean() if tail.any() else 0:5.0f} MW"
        )
        print(
            f"  UNIT-grain plateau (frozen constants):        {nu:3d} win | "
            f"{twh_up:5.2f} TWh/yr | tail capture {recov_up[tail].mean() if tail.any() else 0:5.0f} MW"
        )
        for gap in (25, 50, 90):
            nm = (mp > TAIL_THR - gap) & (mp <= TAIL_THR)
            both = recov_oper + recov_up
            print(
                f"    model near-misses within ${gap}: {nm.sum():3d} h; "
                f">=500 MW recovered (A+B) in {int(((both >= 500) & nm).sum())} of them"
            )
    # plant-level plateau over-fire measurement (2025)
    bench = load_bench(2025)["plants"]
    recov = 0.0
    for pid, b in bench.items():
        if pid not in coal_pids(bench):
            continue
        cf = dec_u8(b["campd"])[:HOURS]
        for i, j, f in _detect_plateau(cf):
            recov += (1 - f) * b["npl"] * (j - i) * 24 / 1e6
    print(
        f"=== plant-level plateau detector at frozen constants, PJM-2025 coal: "
        f"{recov:.1f} TWh/yr removal — OVER-FIRES on a cycling fleet (economic part-load "
        f"read as outage); INADMISSIBLE for PJM without unit grain."
    )


# ------------------------------------------------------------------ fuel costs
def sec_fuel() -> None:
    df = pd.read_parquet(F923)
    coal = df[df.fuel_group == "Coal"]
    pjm_states = [s for s in PJM_STATES if s != "DC"]
    print("=== F923 delivered coal, PJM states, quantity-weighted $/MMBtu:")
    for yr in (2023, 2024, 2025):
        d = coal[(coal.year == yr) & (coal.state.isin(pjm_states))]
        qw = (d.price_per_mmbtu * d.quantity).sum() / d.quantity.sum()
        dj = d[d.month.isin([6, 7])]
        qwj = (dj.price_per_mmbtu * dj.quantity).sum() / dj.quantity.sum()
        print(f"  {yr}: annual {qw:.2f} | Jun-Jul {qwj:.2f} | rows {len(d)}")
    print(
        "  (model annual HH gas: 2023 $2.54, 2024 $2.19, 2025 $3.52 — the 2025 coal-vs-gas"
    )
    print("   merit shift is real commodity movement, not an F923 vintage artifact.)")
    gas = df[df.fuel_group == "Natural Gas"]
    belts = {
        "Dominion belt": {59913: "Greensville", 58260: "Brunswick", 55939: "Warren"},
        "cycler belt": {
            55524: "York",
            55736: "HangingRock",
            55502: "Lawrenceburg",
            55297: "NewCovert",
        },
    }
    print(
        "=== delivered gas $/MMBtu (Jun-Jul own-reported; n=0 -> pool-filled in the model):"
    )
    for yr in (2024, 2025):
        for lbl, pl in belts.items():
            for pid, nm in pl.items():
                r = gas[(gas.plant_id == pid) & (gas.year == yr)]
                jj = r[r.month.isin([6, 7])].price_per_mmbtu.mean()
                print(
                    f"  {yr} {lbl:13s} {nm:12s} n={len(r):2d} JunJul={jj if len(r) else float('nan'):5.2f}"
                )


# ---------------------------------------------------------------- zonal surface
HUB2ZONE = {
    "DOMINION HUB": "PJM_Dominion",
    "WESTERN HUB": "PJM_West_APS",
    "AEP-DAYTON HUB": "PJM_AEP_Ohio",
    "N ILLINOIS HUB": "PJM_ComEd",
    "EASTERN HUB": "PJM_EMAAC",
    "NEW JERSEY HUB": "PJM_EMAAC",
    "ATSI GEN HUB": "PJM_ATSI",
}


def sec_zonal(pay: dict) -> None:
    for yr in (2024, 2025):
        lm = pd.read_csv(
            REPO / f"data/raw/lmp-data/PJM_{yr}_rt_da_monthly_lmps.csv",
            usecols=["datetime_beginning_ept", "pnode_name", "total_lmp_da"],
        )
        lm["mon"] = pd.to_datetime(lm.datetime_beginning_ept, format="mixed").dt.month
        hub_jul = lm[lm.mon == 7].groupby("pnode_name").total_lmp_da.mean()
        sys_jul = hub_jul.mean()
        y = pay["years"][str(yr)]
        zp = {z: v["pMon"][6] for z, v in y["lmp"].items() if z != "PJM_external"}
        sys_m = float(np.mean(list(zp.values())))
        print(
            f"=== July {yr} congestion surface: actual hub mean {sys_jul:.1f} vs model zone mean {sys_m:.1f}"
        )
        for hub, z in HUB2ZONE.items():
            a = hub_jul.get(hub, np.nan)
            m = zp.get(z, np.nan)
            print(
                f"  {hub:16s} act {a:6.1f} ({a - sys_jul:+5.1f}) | {z:14s} mod {m:6.1f} ({m - sys_m:+5.1f})"
            )
        fr = {f["fuel"]: (f["m"], f["b"], f.get("r")) for f in y["fuelRows"]}
        print("  interchange (model, actual, r):", fr.get("interchange"))


# --------------------------------------------------------------- coal HOD shape
def sec_coalhod(pay: dict, year: int = 2025) -> None:
    bench = load_bench(year)["plants"]
    yp = pay["years"][str(year)]["plants"]
    jul = MONTH == 7
    d_tot = np.zeros(HOURS)
    p10m, p10c = [], []
    for pid, mv in yp.items():
        b = bench.get(pid)
        if (
            not b
            or not b.get("group", "").startswith("COAL")
            or "campd" not in b
            or b.get("ct_only")
        ):
            continue
        m = dec_u8(mv["m"])[:HOURS] * b["npl"]
        c = dec_u8(b["campd"])[:HOURS] * b["npl"]
        d_tot += m - c
        if b["npl"] >= 500:
            p10m.append(np.percentile(m[jul] / b["npl"], 10))
            p10c.append(np.percentile(c[jul] / b["npl"], 10))
    dj = d_tot[jul]
    night = HOD[jul] <= 6
    print(
        f"=== July {year} coal over-run: {dj.sum() / 1e6:.2f} TWh | overnight (h0-6) mean "
        f"{dj[night].mean():+.0f} MW vs day {dj[~night].mean():+.0f} MW "
        f"(share of positive over-run in h0-6: {100 * dj[night].clip(min=0).sum() / dj.clip(min=0).sum():.0f}%)"
    )
    print(
        f"  July p10 CF, >=500 MW coal plants: model {np.mean(p10m):.2f} vs CAMPD {np.mean(p10c):.2f} "
        f"(committed-floor flatness — the level/shape residual, DOF issue #1302; NOT the tail driver)"
    )


SECTIONS = {
    "tail": lambda pay: sec_tail(pay),
    "phantom": lambda pay: sec_phantom(pay),
    "units": lambda pay: sec_units(pay),
    "derivers": lambda pay: sec_derivers(pay),
    "fuel": lambda pay: sec_fuel(),
    "zonal": lambda pay: sec_zonal(pay),
    "coalhod": lambda pay: sec_coalhod(pay),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-id", default="2026-07-15-pjm-111-cc-reconcile")
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
