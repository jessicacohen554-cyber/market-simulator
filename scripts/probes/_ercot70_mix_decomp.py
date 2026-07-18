"""ERCOT-70 supply-mix decomposition on the moderate-tightness under-priced hours.

No LP solve — reads a keeper-reconstruction bundle (the ERCOT-69 leg-0
construction) and names the over-dispatched class on the hours the model
under-prices: the ERCOT-68 §4 room decomposition re-run on the MODERATE
under-priced hour sets (May-2024 shoulder-day daytime, Nov-2024, Apr-2024)
instead of the top-net-load hours.

For each target window it tabulates model dispatch-by-class against two
measured bases on the model's non-leap 8760 clock (fixed CST, Feb 29 dropped
— same convention as ``derive_actual_lmp._std_hour_index`` and
``market_sim.data.campd``):

* CAMPD on-line gross by model class (chp-export basis — the ERCOT-58 §4
  construction, ``derive_ercot_rtolcap_forward._class_hourly``) for the
  thermal class split;
* EIA-930 ERCOT fuel-type net generation (``data/raw/eia-930-hourly``) for
  the non-CAMPD rows: nuclear / wind / solar / hydro / battery / other and
  the demand basis check;
* the measured storage-AS award (``ercot_storage_as_reserve_mw``) alongside
  model vs EIA-930 battery discharge (the ERCOT-66 M4 suspect);
* West-zone gas dispatch, model vs CAMPD-by-zone (the West/Panhandle
  suspect).

Cross-check: the same-merit-order climb test — bin ALL May daytime hours by
model system price and by model gas dispatch, then read off what the model's
own dual does at reality's gas-dispatch level.

EXPLICITLY-LABELLED DIAGNOSTIC (rules 13/16): scorer-only, single-year,
never registered; reads a rule-16 throwaway bundle deleted at session end.

Usage::

    python scripts/probes/_ercot70_mix_decomp.py --bundle ercot70_keeper_2024 \
        --year 2024
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

from derive_ercot_rtolcap_forward import (  # noqa: E402
    _class_hourly,
    _fleet_class_maps,
)

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.chp import chp_btm_pct  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.results.scarcity import ercot_storage_as_reserve_mw  # noqa: E402

HOURS = 8760
_CAL = pd.date_range("2023-01-01", periods=HOURS, freq="h")  # non-leap model clock
_MONTH_START_HOUR = np.array(
    [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]
)
# ERCOT's fixed standard-time clock (derive_actual_lmp._STD_TZ).
_STD_TZ = "Etc/GMT+6"

ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
EIA930_HOURLY = REPO / "data" / "raw" / "eia-930-hourly" / "ERCO hourly.parquet"

# CAMPD-comparable thermal classes (the ERCOT-58 §4 rows).
CAMPD_CLASSES = (
    "COAL",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
)
GAS_KLASS_PREFIX = ("CC_", "CT_", "ST_")

# The May-2024 DA-shoulder family (charter / _ercot68_anatomy controls).
MAY_SHOULDER_DAYS = (9, 10, 12, 13, 21, 27, 29, 30)
DAY_H0, DAY_H1 = 10, 20  # inclusive hod window

# ERCOT-fleet CC plants with ZERO CAMPD rows (TX state extract) in 2023-2025:
# Kiamichi (OK-sited switchable — outside the TX extract), Hidalgo, Arthur Von
# Rosenberg, EG178. The CAMPD-derived outage overlay is structurally blind to
# them (no CEMS rows -> no windows), so they ride flat statistical
# availability; their measured reference here is EIA-923 monthly net gen.
NONCAMPD_CC = (55501, 55545, 7512, 56233)
# CAMPD-attribution artifacts in the _class_hourly split (corrected below):
# V H Braunig (registry plant_group OTHER -> dropped from every class) and the
# W A Parish gas-steam units (synthetic model id 34702; CAMPD reports the
# whole plant under 3470, which the split books entirely to COAL).
BRAUNIG, PARISH, PARISH_ST = 3612, 3470, 34702
EIA923_MONTHLY = (
    REPO / "data" / "raw" / "_processed-legacy" / "eia923_monthly_generation.parquet"
)
DAM_AVAIL_CSV = REPO / "data" / "raw" / "ercot-thermal-dam-availability.csv"
_MONTH_COL = {
    4: ("netgen_april_mwh", 30),
    5: ("netgen_may_mwh", 31),
    11: ("netgen_november_mwh", 30),
}


def _eia930_hourly(year: int) -> pd.DataFrame:
    """EIA-930 ERCOT fuel-type MW on the model's non-leap 8760 clock.

    Indexes the real UTC instants onto the fixed-CST chronological calendar
    (Feb 29 dropped) — the same mapping the actual-LMP sidecar uses, so every
    series here is hour-aligned with the bundle and the scored deltas.
    """
    df = pd.read_parquet(EIA930_HOURLY)
    std = pd.DatetimeIndex(df["UTC time"]).tz_localize("UTC").tz_convert(_STD_TZ)
    ok = (std.year == year) & ~((std.month == 2) & (std.day == 29))
    idx = _MONTH_START_HOUR[std.month - 1] + (std.day - 1) * 24 + std.hour
    out = df.loc[np.asarray(ok)].copy()
    out["hour_of_year"] = idx[np.asarray(ok)]
    return out.groupby("hour_of_year").first().reindex(range(HOURS))


def _series(df: pd.DataFrame, col: str) -> np.ndarray:
    return (
        df[col].to_numpy(dtype=float) if col in df.columns else np.full(HOURS, np.nan)
    )


def _pwrstr_dam_hourly(year: int) -> np.ndarray:
    """Hourly DA energy award (MW) of all PWRSTR resources, 60-Day disclosure.

    The DA-cleared battery energy schedule — the measured DA position the P1
    solve is scored against (EIA-930's BAT breakout only starts Oct-2024; before
    that ERCO folds batteries into ``Other``). Prevailing HE labels -> CST via
    the same helper the AS-by-restype series uses.
    """
    from build_ercot_as_withholding import prevailing_he_to_cst

    frames = []
    for f in sorted(
        (REPO / "data" / "raw" / "ercot").glob(
            f"60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{year}_*.parquet"
        )
    ):
        df = pd.read_parquet(
            f,
            columns=[
                "Delivery Date",
                "Hour Ending",
                "Resource Type",
                "Awarded Quantity",
            ],
        )
        frames.append(df[df["Resource Type"] == "PWRSTR"])
    if not frames:
        return np.full(HOURS, np.nan)
    big = pd.concat(frames, ignore_index=True)
    big["dd"] = pd.to_datetime(big["Delivery Date"])
    big = big[big["dd"].dt.year == year]
    ts = prevailing_he_to_cst(big["dd"], big["Hour Ending"].astype(int))
    idx = (
        _MONTH_START_HOUR[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    ok = ~((ts.dt.month.to_numpy() == 2) & (ts.dt.day.to_numpy() == 29))
    v = (
        pd.Series(big["Awarded Quantity"].to_numpy(), index=idx)[ok]
        .groupby(level=0)
        .sum()
    )
    out = np.zeros(HOURS)
    out[v.index.to_numpy()] = v.to_numpy()
    return out


def _campd_by_zone_gas(year: int) -> dict[str, np.ndarray]:
    """CAMPD gas-class on-line gross by MODEL zone (chp-export basis, MW)."""
    from market_sim.data import campd

    plant_group, _plant_cap, _derate = _fleet_class_maps(year)
    gas_plants = {
        pc for pc, grp in plant_group.items() if grp.startswith(GAS_KLASS_PREFIX)
    }
    # Dominant model zone per plant (by capacity) from the same fleet build.
    iso = get_iso_config("ERCOT")
    gens = load_fleet_from_csv("ERCOT", iso, year=year)
    zcap: dict[tuple[int, str], float] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc in gas_plants:
            zcap[(pc, g.zone)] = zcap.get((pc, g.zone), 0.0) + float(g.pmax_mw)
    zone_of: dict[int, str] = {}
    best: dict[int, float] = {}
    for (pc, z), cap in zcap.items():
        if cap > best.get(pc, -1.0):
            best[pc], zone_of[pc] = cap, z
    export = {
        pc: 1.0 - float(chp_btm_pct(pc, plant_group[pc], "ERCOT")) / 100.0
        for pc in gas_plants
        if plant_group[pc] in ("CC_CHP", "CT_CHP", "ST_CHP")
    }
    df = campd.load_campd_hourly(["TX"], [year])
    df = df[df["plant_id"].isin(gas_plants)].copy()
    ph = df.groupby(["plant_id", "hour_of_year"])["gross_mw"].sum().reset_index()
    ph["gross"] = ph["gross_mw"].clip(lower=0.0) * ph["plant_id"].map(
        lambda pc: export.get(pc, 1.0)
    )
    ph["zone"] = ph["plant_id"].map(zone_of)
    out: dict[str, np.ndarray] = {}
    for z, sub in ph.groupby("zone"):
        v = sub.groupby("hour_of_year")["gross"].sum()
        arr = np.zeros(HOURS)
        arr[v.index.to_numpy()] = v.to_numpy()
        out[str(z)] = arr
    return out


def _fmt(model: float, actual: float) -> str:
    return f"{model:8,.0f}  {actual:8,.0f}  {model - actual:+8,.0f}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="ercot70_keeper_2024")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument(
        "--under",
        type=float,
        default=5.0,
        help="under-priced subset threshold: model - actual < -X $/MWh",
    )
    args = ap.parse_args()
    year = args.year
    bdir = REPO / "results" / "calibration" / args.bundle

    month = _CAL.month.to_numpy()
    day = _CAL.day.to_numpy()
    hod = np.arange(HOURS) % 24

    # ---- model: prices / demand ---------------------------------------------
    sysq = pd.read_parquet(bdir / "system.parquet")
    sysq = sysq[(sysq["pass"] == "P1") & (sysq["year"] == year)].copy()
    lw = (
        sysq.groupby("hour")
        .apply(
            lambda g: float(
                (g["price"] * g["demand"]).sum() / max(g["demand"].sum(), 1e-9)
            ),
            include_groups=False,
        )
        .reindex(range(HOURS))
        .to_numpy(dtype=float)
    )
    dem_model = (
        sysq.groupby("hour")["demand"].sum().reindex(range(HOURS)).to_numpy(dtype=float)
    )

    # ---- model: dispatch by class + gas by zone ------------------------------
    disp = pd.read_parquet(
        bdir / "dispatch" / f"{year}_P1.parquet",
        columns=["pass", "klass", "plant_code", "zone", "hour", "mw"],
    )
    disp = disp[disp["pass"] == "P1"]
    kl = (
        disp.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=range(HOURS), fill_value=0.0)
    )

    def model_class(cls: str) -> np.ndarray:
        rows = [
            c for c in kl.index if (c.startswith("COAL") if cls == "COAL" else c == cls)
        ]
        return (
            kl.loc[rows].sum(axis=0).to_numpy(dtype=float) if rows else np.zeros(HOURS)
        )

    gas_rows = [c for c in kl.index if c.startswith(GAS_KLASS_PREFIX)]
    gas_model = kl.loc[gas_rows].sum(axis=0).to_numpy(dtype=float)
    gasz = (
        disp[disp["klass"].isin(gas_rows)]
        .groupby(["zone", "hour"], observed=True)["mw"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=range(HOURS), fill_value=0.0)
    )

    # ---- model: storage -------------------------------------------------------
    sdf = pd.read_parquet(bdir / "storage.parquet")
    sdf = sdf[(sdf["pass"] == "P1") & (sdf["year"] == year)]
    li = sdf[sdf["tech"] == "li_ion"]
    dis_li = (
        li.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS), fill_value=0.0)
    ).to_numpy()
    chg_li = (
        li.groupby("hour")["charge_mw"].sum().reindex(range(HOURS), fill_value=0.0)
    ).to_numpy()
    dis_all = (
        sdf.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS), fill_value=0.0)
    ).to_numpy()
    chg_all = (
        sdf.groupby("hour")["charge_mw"].sum().reindex(range(HOURS), fill_value=0.0)
    ).to_numpy()
    storage_as = ercot_storage_as_reserve_mw(year, HOURS)

    # ---- actuals ---------------------------------------------------------------
    act = pd.read_parquet(ACTUAL_LMP)
    act = (
        act[act["year"] == year]
        .set_index("hour")["rt"]
        .reindex(range(HOURS))
        .to_numpy(dtype=float)
    )
    e930 = _eia930_hourly(year)
    pwrstr_da = _pwrstr_dam_hourly(year)
    _, _, _, _, online_gross = _class_hourly(year, chp_export_basis=True)
    campd_gas = np.zeros(HOURS)
    for grp in CAMPD_CLASSES:
        if grp != "COAL":
            campd_gas += online_gross.get(grp, np.zeros(HOURS))[:HOURS]
    campd_zone_gas = _campd_by_zone_gas(year)

    # coverage-correction inputs: per-plant CAMPD gross, EIA-923 monthly net
    # gen, and the measured 60-Day DAM class-day live HSL (ERCOT-67 series).
    from market_sim.data import campd as _campd

    _cdf = _campd.load_campd_hourly(["TX"], [year])
    campd_plant = (
        _cdf.groupby(["plant_id", "hour_of_year"])["gross_mw"].sum().clip(lower=0)
    )
    e923 = pd.read_parquet(EIA923_MONTHLY)
    e923 = e923[e923["year"] == year]
    dam_csv = pd.read_csv(DAM_AVAIL_CSV, parse_dates=["date"])
    dam_csv = dam_csv[dam_csv["date"].dt.year == year]

    delta = lw - act

    # ---- target windows ----------------------------------------------------------
    may_sh = (
        (month == 5)
        & np.isin(day, MAY_SHOULDER_DAYS)
        & (hod >= DAY_H0)
        & (hod <= DAY_H1)
    )
    windows = [
        ("MAY-SHOULDER daytime (8d x h10-20)", may_sh, 5),
        ("MAY-SHOULDER under-priced subset", may_sh & (delta < -args.under), 5),
        ("NOV (all hours)", month == 11, 11),
        (
            f"NOV under-priced (delta < -{args.under:.0f})",
            (month == 11) & (delta < -args.under),
            11,
        ),
        ("APR (all hours)", month == 4, 4),
        (
            f"APR under-priced (delta < -{args.under:.0f})",
            (month == 4) & (delta < -args.under),
            4,
        ),
    ]

    for label, msk, win_month in windows:
        n = int(msk.sum())
        if n == 0:
            print(f"\n===== {label}: 0 h — skipped =====")
            continue

        def m(x: np.ndarray) -> float:
            return float(np.nanmean(np.asarray(x, dtype=float)[msk]))

        print(f"\n===== {label}: {n} h =====")
        print(
            f"  price  model lw {m(lw):7.2f}  actual rt {m(act):7.2f}  "
            f"delta {m(delta):+7.2f} $/MWh"
        )
        print(
            f"  demand model {m(dem_model):8,.0f}  EIA-930 {m(_series(e930, 'Demand')):8,.0f}  "
            f"(adj {m(_series(e930, 'Adjusted demand')):8,.0f}; interchange "
            f"{m(_series(e930, 'Total interchange')):+6,.0f}) MW"
        )
        print("  -- class-resolved, mean MW: model | actual | model-actual --")
        print("  [CAMPD gross basis, thermal]")
        tot_mm = tot_aa = 0.0
        for cls in CAMPD_CLASSES:
            mm = m(model_class(cls))
            aa = m(online_gross.get(cls, np.zeros(HOURS))[:HOURS])
            tot_mm, tot_aa = tot_mm + mm, tot_aa + aa
            print(f"    {cls:<11} {_fmt(mm, aa)}")
        print(f"    {'THERMAL SUM':<11} {_fmt(tot_mm, tot_aa)}")
        print(
            f"    {'gas (930)':<11} {_fmt(m(gas_model), m(_series(e930, 'NG: NG')))}"
            "   [model gas vs EIA-930 net-gen basis]"
        )
        print(
            f"    {'coal (930)':<11} {_fmt(m(model_class('COAL')), m(_series(e930, 'NG: COL')))}"
        )
        print("  [EIA-930 basis, non-thermal]")
        for label930, mcls in (
            ("NUC", "nuclear"),
            ("WND", "wind"),
            ("SUN", "solar"),
            ("WAT", "hydro"),
        ):
            print(
                f"    {mcls:<11} {_fmt(m(model_class(mcls)), m(_series(e930, f'NG: {label930}')))}"
            )
        oth_m = (
            m(model_class("biomass")) + m(model_class("OTHER")) + m(model_class("oil"))
        )
        oth_a = np.nansum([m(_series(e930, "NG: OTH")), m(_series(e930, "NG: UES"))])
        print(f"    {'other+oil':<11} {_fmt(oth_m, oth_a)}")
        bat = _series(e930, "NG: BAT")
        oth930 = _series(e930, "NG: OTH")
        print("  [storage]")
        print(
            f"    model li_ion dis {m(dis_li):7,.0f}  chg {m(chg_li):7,.0f}  "
            f"net {m(dis_li - chg_li):+7,.0f} MW"
        )
        print(
            f"    model ALL    dis {m(dis_all):7,.0f}  chg {m(chg_all):7,.0f}  "
            f"net {m(dis_all - chg_all):+7,.0f} MW"
        )
        print(
            f"    EIA-930 BAT net  {m(bat):+7,.0f} MW   "
            f"(pre-Nov-2024 breakout: batteries live in OTH — OTH here "
            f"{m(oth930):+7,.0f} MW incl ~100 MW true-other)"
        )
        print(
            f"    PWRSTR DA award  {m(pwrstr_da):7,.0f} MW   "
            f"(measured storage-AS award {m(storage_as):7,.0f} MW)"
        )
        print("  [gas by zone: model | CAMPD | diff]")
        for z in sorted(set(gasz.index) | set(campd_zone_gas)):
            zm = (
                gasz.loc[z].to_numpy(dtype=float)
                if z in gasz.index
                else np.zeros(HOURS)
            )
            za = campd_zone_gas.get(z, np.zeros(HOURS))
            print(f"    {z:<14} {_fmt(m(zm), m(za))}")

        # -- CAMPD-coverage corrections (the ERCOT-70 finding) ----------------
        # The CAMPD class rows above under-count the ACTUAL side: (a) four
        # ERCOT CC plants have no TX CAMPD rows at all (NONCAMPD_CC), (b)
        # V H Braunig is dropped from every class by its OTHER registry group,
        # (c) W A Parish gas-steam books under COAL. Correct with EIA-923
        # monthly means (a, c) and Braunig's own CAMPD gross (b).
        hrs = np.where(msk)[0]
        nh = len(hrs)
        mcol_days = _MONTH_COL.get(win_month)
        dsub = disp[disp["hour"].isin(hrs)]
        mw_by = dsub.groupby(["klass", "plant_code"], observed=True)["mw"].sum() / nh
        csub = (
            campd_plant[campd_plant.index.get_level_values(1).isin(hrs)]
            .groupby(level=0)
            .sum()
            / nh
        )
        if mcol_days is not None and "CC_REGULAR" in mw_by.index.get_level_values(0):
            mcol, ndays = mcol_days
            g923 = e923.groupby("plant_id")[mcol].sum() / (ndays * 24)
            ccp = mw_by.xs("CC_REGULAR", level=0)
            cc_model = float(ccp.sum())
            cc_nc_model = float(ccp.reindex(list(NONCAMPD_CC)).fillna(0).sum())
            cc_nc_923 = float(g923.reindex(list(NONCAMPD_CC)).fillna(0).sum())
            cc_cov = float(
                csub.reindex([int(p) for p in ccp.index if int(p) in csub.index])
                .fillna(0)
                .sum()
            )
            braunig = float(csub.get(BRAUNIG, 0.0))
            par_all = float(csub.get(PARISH, 0.0))
            p923 = e923[e923["plant_id"] == PARISH]
            st_share = float(
                p923[p923["fuel_type"] == "NG"][mcol].sum()
                / max(p923[mcol].sum(), 1e-9)
            )
            st_model = float(
                mw_by.xs("ST_GAS", level=0).sum()
                if "ST_GAS" in mw_by.index.get_level_values(0)
                else 0.0
            )
            st_campd = m(online_gross.get("ST_GAS", np.zeros(HOURS))[:HOURS])
            print("  [coverage corrections]")
            print(
                f"    CC_REGULAR corrected: model {cc_model:8,.0f} vs "
                f"(CAMPD-covered {cc_cov:8,.0f} + non-CAMPD 923-mean "
                f"{cc_nc_923:6,.0f}) -> excess {cc_model - cc_cov - cc_nc_923:+8,.0f} "
                f"(non-CAMPD phantom {cc_nc_model - cc_nc_923:+8,.0f})"
            )
            print(
                f"      Hidalgo 55545 (923: 0 MWh Apr+May): model "
                f"{float(ccp.get(55545, 0.0)):6,.0f} MW"
            )
            print(
                f"    ST_GAS corrected actual: {st_campd:8,.0f} + Braunig "
                f"{braunig:6,.0f} + Parish-ST {par_all * st_share:6,.0f} = "
                f"{st_campd + braunig + par_all * st_share:8,.0f} vs model "
                f"{st_model:8,.0f} -> {st_model - st_campd - braunig - par_all * st_share:+8,.0f}"
            )
            print(
                f"    COAL corrected actual: "
                f"{m(online_gross.get('COAL', np.zeros(HOURS))[:HOURS]) - par_all * st_share:8,.0f} "
                f"(Parish-ST share removed) vs model "
                f"{m(model_class('COAL')):8,.0f}"
            )
        # measured 60-Day DAM class-day live HSL vs model dispatch share
        dts = sorted(
            {
                pd.Timestamp(year=year, month=int(mo), day=int(dd))
                for mo, dd in zip(month[msk], day[msk])
            }
        )
        lvl = dam_csv[dam_csv["date"].isin(dts)]
        for cls in ("CC_REGULAR", "CT_PEAKER"):
            r = lvl[lvl["class"] == cls]
            if len(r) and cls in mw_by.index.get_level_values(0):
                live = float(r["live_mw"].mean())
                mm_cls = float(mw_by.xs(cls, level=0).sum())
                print(
                    f"    measured DAM live {cls}: {live:8,.0f} MW; model "
                    f"dispatch {mm_cls:8,.0f} -> share {mm_cls / live:.3f}"
                )

    # ---- same-merit-order climb cross-check (May daytime, all days) --------------
    may_day = (month == 5) & (hod >= DAY_H0) & (hod <= DAY_H1)
    print(
        f"\n===== merit-order climb cross-check: May h{DAY_H0}-{DAY_H1}, all days "
        f"({int(may_day.sum())} h) ====="
    )
    print(
        "  model-price bin: n_h | mean gas MW | net storage MW | net load MW | mean actual rt"
    )
    nld = dem_model - model_class("wind") - model_class("solar")
    bins = [(0, 35), (35, 60), (60, 100), (100, 1e9)]
    for lo, hi in bins:
        bm = may_day & (lw >= lo) & (lw < hi)
        if not bm.any():
            print(f"    ${lo:>3}-{hi if hi < 1e9 else 'inf':>4}: 0 h")
            continue
        print(
            f"    ${lo:>3}-{str(int(hi)) if hi < 1e9 else 'inf':>4}: {int(bm.sum()):4d} h | "
            f"{float(np.nanmean(gas_model[bm])):8,.0f} | "
            f"{float(np.nanmean((dis_all - chg_all)[bm])):+7,.0f} | "
            f"{float(np.nanmean(nld[bm])):8,.0f} | "
            f"{float(np.nanmean(act[bm])):7.2f}"
        )
    # what the model's own dual does at reality's gas level on the target hours
    tgt_gas_actual = float(np.nanmean(campd_gas[may_sh]))
    near = may_day & (np.abs(gas_model - tgt_gas_actual) < 500.0)
    print(
        f"  actual (CAMPD) gas on MAY-SHOULDER daytime: {tgt_gas_actual:,.0f} MW; "
        f"model gas there: {float(np.nanmean(gas_model[may_sh])):,.0f} MW"
    )
    if near.any():
        print(
            f"  May daytime hours where MODEL gas within ±500 MW of that actual level: "
            f"{int(near.sum())} h, model price mean ${float(np.nanmean(lw[near])):.2f} "
            f"(p50 ${float(np.nanmedian(lw[near])):.2f}), actual rt there "
            f"${float(np.nanmean(act[near])):.2f}"
        )


if __name__ == "__main__":
    main()
