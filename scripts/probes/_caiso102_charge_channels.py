"""CAISO-102 derive-first probe: the INELASTIC-CONDUCT charge channels.

caiso-100/101 established that the measured CAISO battery fleet buys its full
charge volume DESPITE a revealed $11-17/MWh conduct cost — charge volume is
inelastic to marginal cost (the $14.25 marginal bid adder was REJECTED on the
pre-registered volume gates), so the belly's remaining over-price
(+6.0/+6.6/+5.0 post-caiso-101) must live in the conduct channels that FIX the
volume upstream of the RT margin. This probe measures the three channels the
caiso-101 handoff charters, from the committed CAISO Daily Energy Storage
Report quarterly xlsx (`data/raw/storage-as-awards/CAISO/`, market_output
sheet: TRADE_DATE | HOUR (1..25 DST-aware hour-ending) | INTERVAL |
MARKET (IFM/RTD) | RES_TYPE (LESR/HYBD) | TYPE (EN/SOC/RU/RD/SR/NR) | VALUE):

(a) DA-AWARD ALLOCATION — how much of the fleet's realized (RTD) charge was
    already scheduled day-ahead (IFM EN < 0), per hour-of-day window: the
    DA-fixed share of realized charge, cov = min(chg_IFM, chg_RTD) summed over
    hours. A high DA share means the charge decision is made in the DAM
    against DA prices — not re-optimized at the RT margin the LP prices.
(b) AS-DEPLOYMENT CHARGING VARIANCE — the RT re-dispatch DELTA
    (EN_RTD − EN_IFM) conditioned on the fleet's own AS awards (RU/RD/SR/NR,
    IFM): how much extra-RT charge arrives in high-reg-down-award hours, the
    OLS slope of the delta on the RD award, and the AS-award hod profile
    (the overnight/shoulder reg positioning the LP does not carry).
(c) SHOULDER/OVERNIGHT INELASTIC CHARGE — the measured non-belly charge
    (the −4/−8 % annual under-charge lives OUTSIDE the belly,
    FINDING-caiso100 §5) split DA-scheduled vs RT-added, its charge-weighted
    RT/DA lambda vs the same-day belly floor (is the fleet paying MORE than
    the belly glut price for it — arbitrage-irrational, obligation-rational),
    and the model's non-belly charge against it (optional bundle args).

NO LP is built or solved by this probe (caiso-93/94 derive-first protocol);
any mechanism it motivates goes to an owner ask.

Clock: TRADE_DATE+HOUR are prevailing-Pacific hour-ending physical-hour labels
(storage_as_awards.caiso intake, verified 2023-2025), so hod = HOUR−1 with the
fall-back 25th hour dropped and Feb-29 dropped (model 8760 calendar); the ≤2
DST transition days/year are window-immaterial. EIA-930 CISO `NG: OTH` and
`actual_lmp_hourly_CAISO.parquet` follow the _caiso100_charge_econ loaders.

Basis: LESR only (standalone + co-located batteries — the NG:OTH/EIA-860
battery basis of caiso-98/99/100; HYBD rows are the combined solar+storage
resource whose EN mixes PV output and are reported only as a coverage note).

Usage:
  python scripts/probes/_caiso102_charge_channels.py [--cache <parquet>]
      [<bundle_dir> ...]
Bundle dirs (optional, e.g. the same-machine caiso102_repro_A) add the model's
charge column to channel (c). --cache points at a pre-parsed concat of the
market_output sheets (same columns); without it the xlsx are parsed (~5 min).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "storage-as-awards" / "CAISO"
EIA930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
YEARS = (2023, 2024, 2025)
WINDOWS = {
    "overnight(0-5)": range(0, 6),
    "morning(6-9)": range(6, 10),
    "belly(10-14)": range(10, 15),
    "pm-shldr(15-16)": range(15, 17),
    "evening(17-21)": range(17, 22),
    "late(22-23)": range(22, 24),
}
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def load_market_output(cache: Path | None) -> pd.DataFrame:
    """All market_output rows, LESR + HYBD, 2023-2025."""
    if cache is not None:
        return pd.read_parquet(cache)
    frames = []
    for f in sorted(RAW.glob("storage-report-*.xlsx")):
        frames.append(pd.read_excel(f, sheet_name="market_output"))
    return pd.concat(frames, ignore_index=True)


def hourly_pivot(mo: pd.DataFrame) -> pd.DataFrame:
    """LESR rows -> one row per (date, hod) with IFM/RTD EN + IFM AS awards.

    RTD 5-min intervals are hour-averaged (MW ~ MWh/h). Fall-back 25th hour
    and Feb-29 dropped (model 8760 calendar).
    """
    d = mo[mo.RES_TYPE == "LESR"].copy()
    d["TRADE_DATE"] = pd.to_datetime(d["TRADE_DATE"])
    d = d[(d.TRADE_DATE.dt.month != 2) | (d.TRADE_DATE.dt.day != 29)]
    d["hod"] = d.HOUR - 1
    d = d[d.hod < 24]
    # hour-average the intervals (IFM is hourly, INTERVAL=1; RTD has 12)
    g = d.groupby(["TRADE_DATE", "hod", "MARKET", "TYPE"], as_index=False).VALUE.mean()
    p = g.pivot_table(
        index=["TRADE_DATE", "hod"],
        columns=["MARKET", "TYPE"],
        values="VALUE",
        aggfunc="mean",
    )
    p.columns = [f"{m}_{t}" for m, t in p.columns]
    return p.reset_index()


def measured_930_chg(year: int) -> np.ndarray:
    """(n_days, 24) EIA-930 NG:OTH charge MW (basis cross-check)."""
    d = pd.read_parquet(EIA930, columns=["Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    dy = d[
        (d["Local date"].dt.year == year)
        & ((d["Local date"].dt.month != 2) | (d["Local date"].dt.day != 29))
    ].sort_values(["Local date", "Hour"])
    v = np.nan_to_num(dy["NG: OTH"].to_numpy(dtype=float))
    v = v[: 365 * 24]
    if len(v) < 365 * 24:  # 2025 file ends 8751 h — zero-pad the tail
        v = np.pad(v, (0, 365 * 24 - len(v)))
    return np.clip(-v.reshape(365, 24), 0.0, None)


def model_chg(bundle: Path, year: int) -> np.ndarray:
    """(365, 24) model battery charge MW (P1, PS excluded)."""
    s = pd.read_parquet(
        bundle / "storage.parquet",
        columns=["pass", "year", "tech", "hour", "charge_mw"],
    )
    s = s[(s["pass"] == "P1") & (s.year == year) & (s.tech != "pumped_storage")]
    g = (
        s.groupby("hour")
        .charge_mw.sum()
        .reindex(range(8760), fill_value=0.0)
        .sort_index()
    )
    return g.to_numpy()[: 365 * 24].reshape(365, 24)


def actual_lmp(year: int) -> pd.DataFrame:
    """(8760,) rt/da actual LMP as (365,24) frames."""
    a = pd.read_parquet(LMP)
    a = a[a.year == year].sort_values("hour")
    out = {}
    for k in ("rt", "da"):
        v = np.nan_to_num(a[k].to_numpy(dtype=float)[: 365 * 24])
        if len(v) < 365 * 24:
            v = np.pad(v, (0, 365 * 24 - len(v)))
        out[k] = v.reshape(365, 24)
    return out


def wmean(x: np.ndarray, w: np.ndarray) -> float:
    """Weighted mean, nan-safe."""
    return float((x * w).sum() / w.sum()) if w.sum() > 0 else float("nan")


def year_table(p: pd.DataFrame, year: int, bundles: list[Path]) -> None:
    """Print all three channels for one year."""
    py = p[p.TRADE_DATE.dt.year == year].copy()
    ndays = py.TRADE_DATE.nunique()
    # full (365,24) grids, zero-filled where a slot is absent
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    days = days[(days.month != 2) | (days.day != 29)]
    idx = pd.MultiIndex.from_product([days, range(24)], names=["TRADE_DATE", "hod"])
    py = py.set_index(["TRADE_DATE", "hod"]).reindex(idx).fillna(0.0).reset_index()

    def grid(col: str) -> np.ndarray:
        return (
            py[col].to_numpy(dtype=float).reshape(len(days), 24)
            if col in py
            else np.zeros((len(days), 24))
        )

    en_ifm, en_rtd = grid("IFM_EN"), grid("RTD_EN")
    en_rtpd = grid("RTPD_EN")
    chg_ifm = np.clip(-en_ifm, 0.0, None)
    chg_rtd = np.clip(-en_rtd, 0.0, None)
    chg_rtpd = np.clip(-en_rtpd, 0.0, None)
    dis_rtd = np.clip(en_rtd, 0.0, None)
    cov = np.minimum(chg_ifm, chg_rtd)  # DA-scheduled part of realized charge
    cov_rtpd = np.minimum(chg_rtpd, chg_rtd)  # FMM-committed part
    rt_added = chg_rtd - cov
    rd, ru = grid("IFM_RD"), grid("IFM_RU")
    sr, nr = grid("IFM_SR"), grid("IFM_NR")
    m930 = measured_930_chg(year)
    lmps = actual_lmp(year)
    models = {b.name: model_chg(b, year) for b in bundles}

    print(f"===== {year} (LESR, {ndays} report days) =====")
    print(
        f"  annual: RTD chg {chg_rtd.sum() / 1e6:5.2f} dis {dis_rtd.sum() / 1e6:5.2f} "
        f"| IFM chg {chg_ifm.sum() / 1e6:5.2f} TWh | EIA-930 chg {m930.sum() / 1e6:5.2f}"
        f" | DA-share of realized chg {cov.sum() / chg_rtd.sum():.3f}"
        f" | FMM(RTPD) chg {chg_rtpd.sum() / 1e6:5.2f} covers {cov_rtpd.sum() / chg_rtd.sum():.3f}"
    )
    # -- channel (a) + (c): window table ------------------------------------
    hdr = (
        f"  {'window':16s} {'chgRTD':>7s} {'chgIFM':>7s} {'DAshr':>6s} {'RTadd':>6s}"
        f" {'930chg':>7s} {'lam_rt':>6s} {'lam_da':>6s} {'RTadd_lam':>9s}"
    )
    for name in models:
        hdr += f" {('mdl:' + name[:12]):>17s}"
    print(hdr)
    for wname, hods in WINDOWS.items():
        h = list(hods)
        row = (
            f"  {wname:16s} {chg_rtd[:, h].sum() / 1e6:7.3f}"
            f" {chg_ifm[:, h].sum() / 1e6:7.3f}"
            f" {cov[:, h].sum() / max(chg_rtd[:, h].sum(), 1e-9):6.3f}"
            f" {rt_added[:, h].sum() / 1e6:6.3f}"
            f" {m930[:, h].sum() / 1e6:7.3f}"
            f" {wmean(lmps['rt'][:, h], chg_rtd[:, h]):6.1f}"
            f" {wmean(lmps['da'][:, h], chg_ifm[:, h]):6.1f}"
            f" {wmean(lmps['rt'][:, h], rt_added[:, h]):9.1f}"
        )
        for name, mc in models.items():
            row += f" {mc[:, h].sum() / 1e6:8.3f} ({wmean(np.zeros_like(mc[:, h]) + 1, mc[:, h]):3.0f})"
        print(row)
    # belly-floor reference for channel (c): same-day belly charge-wtd rt
    belly = list(WINDOWS["belly(10-14)"])
    belly_lam = wmean(lmps["rt"][:, belly], chg_rtd[:, belly])
    nb = [h for h in range(24) if h not in belly]
    print(
        f"  non-belly: chgRTD {chg_rtd[:, nb].sum() / 1e6:5.2f} TWh"
        f" DA-shr {cov[:, nb].sum() / max(chg_rtd[:, nb].sum(), 1e-9):.3f}"
        f" lam_rt {wmean(lmps['rt'][:, nb], chg_rtd[:, nb]):5.1f}"
        f" vs belly chg-wtd lam {belly_lam:5.1f}"
        + "".join(
            f" | mdl {name[:12]} {mc[:, nb].sum() / 1e6:5.2f} TWh"
            for name, mc in models.items()
        )
    )
    # -- channel (b): AS awards + RT re-dispatch ----------------------------
    delta = en_rtd - en_ifm  # negative = extra RT charge vs DA schedule
    extra_rt_chg = np.clip(-delta, 0.0, None)
    print(
        f"  AS awards (IFM avg MW): RU {ru.mean():6.0f} RD {rd.mean():6.0f}"
        f" SR {sr.mean():6.0f} NR {nr.mean():6.0f}"
        f" | RD hod-profile (0-5/6-9/10-14/15-16/17-21/22-23): "
        + "/".join(f"{rd[:, list(h)].mean():.0f}" for h in WINDOWS.values())
    )
    f_delta, f_rd = delta.ravel(), rd.ravel()
    msk = np.isfinite(f_delta) & np.isfinite(f_rd)
    slope = (
        np.polyfit(f_rd[msk], f_delta[msk], 1)[0] if msk.sum() > 100 else float("nan")
    )
    hi_rd = f_rd > np.quantile(f_rd[msk], 0.75)
    print(
        f"  RT-redispatch delta (RTD-IFM EN): mean {f_delta[msk].mean():6.0f} MW"
        f" sd {f_delta[msk].std():5.0f} | corr(delta, RD) "
        f"{np.corrcoef(f_delta[msk], f_rd[msk])[0, 1]:6.3f}"
        f" slope {slope:6.3f} MW/MW-RD"
        f" | extra-RT-chg share in top-RD-quartile hours "
        f"{extra_rt_chg.ravel()[msk & hi_rd].sum() / max(extra_rt_chg.ravel()[msk].sum(), 1e-9):.3f}"
    )
    # SOC hod profile (RTD, fleet MWh) — overnight restoration signature
    if "RTD_SOC" in py:
        soc = grid("RTD_SOC").mean(0)
        print(
            "  RTD SOC hod-mean (GWh): "
            + " ".join(f"{soc[h] / 1e3:.1f}" for h in range(0, 24, 3))
            + "  (hod 0,3,..21)"
        )
    print()


def main() -> int:
    args = sys.argv[1:]
    cache = None
    if args and args[0] == "--cache":
        cache = Path(args[1])
        args = args[2:]
    bundles = [Path(a) for a in args]
    mo = load_market_output(cache)
    n_hybd = int((mo.RES_TYPE == "HYBD").sum())
    p = hourly_pivot(mo)
    p["TRADE_DATE"] = pd.to_datetime(p["TRADE_DATE"])
    print(
        "# CAISO-102 inelastic-charge channels probe (LESR; "
        f"{n_hybd} HYBD rows present but excluded — combined-resource EN mixes PV)\n"
    )
    for year in YEARS:
        year_table(p, year, bundles)
    return 0


if __name__ == "__main__":
    sys.exit(main())
