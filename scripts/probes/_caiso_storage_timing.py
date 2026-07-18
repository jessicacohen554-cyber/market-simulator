"""EVENING-STORAGE-TIMING decomposition (CAISO-98 charter lane, no new LP).

The caiso-97 promotion left C3a-2025 with two remaining masses (FINDING-caiso94
§5, FINDING-caiso95 §4): (i) the BELLY hod 10-14 over-price (the caiso-87
trigger-ON battery sub-regime) and (ii) the CT_PEAKER EVENING ramp (the model
under-serves the evening peak and over-imports it). This charter names storage
timing as the owner of BOTH. This script is the derive-first measurement: it
reads the CURRENT keeper's storage dispatch + LMP from a SAME-MACHINE repro
(``_caiso98_repro_A.py`` -> gitignored ``caiso98_repro_A``, FINDING-caiso92b
protocol — committed bundles are never the baseline, cross-machine HiGHS spread
0.5-1.2 TWh/yr) and compares it against the metered CAISO battery fleet, then
decomposes the belly over-price against the model's storage-active hours.

NO LP here; derive-first (caiso-86b/88/93/94/95 discipline).

MODEL storage: bundle/storage.parquet (charge_mw, discharge_mw per unit-hour,
P1 pass); collapse to a system net-battery hod profile.
MODEL lambda: bundle/system.parquet demand-weighted CA-zone price (the
_caiso92_report.py construction, WECC import node excluded).
MEASURED battery: EIA-930 CISO wide-hourly ``NG: OTH`` — the CAISO battery net
(discharge +, charge -). The +/-3-4 GW midday-charge / evening-discharge diurnal
swing IS the storage fleet; the net-generation identity closes to <1 MW/h on
the reported fuel components, so OTH carries the whole battery term (a small
flat genuine-"other" component is embedded but immaterial to TIMING).
MEASURED price: actual_lmp_hourly_CAISO.parquet (rt).

Usage: python scripts/probes/_caiso_storage_timing.py <bundle_dir>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EIA930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
)
YEARS = (2023, 2024, 2025)
BELLY = list(range(10, 15))  # hod 10-14 (the caiso-94 belly)
EVENING = list(range(17, 22))  # hod 17-21 (the caiso-97 evening window)
MIDDAY_CHG = list(range(9, 17))  # hod 9-16 measured charging window
ACTIVE_MW = 50.0  # per-hour system net-battery threshold for "storage-active"


def measured_battery() -> dict[int, np.ndarray]:
    """Per-year 8760 measured net-battery MW (discharge +, charge -), NG:OTH."""
    d = pd.read_parquet(EIA930, columns=["Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    out = {}
    for y in YEARS:
        dy = d[d["Local date"].dt.year == y].copy()
        dy = dy.sort_values(["Local date", "Hour"])
        v = dy["NG: OTH"].to_numpy(dtype=float)
        v = v[:8760] if len(v) >= 8760 else np.pad(v, (0, 8760 - len(v)))
        out[y] = np.nan_to_num(v)
    return out


def model_storage(bundle: Path) -> dict[int, pd.DataFrame]:
    """Per-year system net-battery per hour from storage.parquet (P1)."""
    s = pd.read_parquet(bundle / "storage.parquet")
    s = s[s["pass"] == "P1"]
    out = {}
    for y in YEARS:
        sy = s[s.year == y]
        g = sy.groupby("hour")[["charge_mw", "discharge_mw"]].sum().sort_index()
        g = g.reindex(range(8760), fill_value=0.0)
        # discharge_mw is stored as the dispatched (>=0) discharge; charge_mw >=0.
        g["net"] = g.discharge_mw.abs() - g.charge_mw.abs()  # + = net discharge
        g["hod"] = g.index.to_numpy() % 24
        out[y] = g
    return out


def model_lambda(bundle: Path) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Per-year (demand-weighted CA-zone lambda[8760], demand[8760])."""
    sys_df = pd.read_parquet(bundle / "system.parquet")
    out = {}
    for y in YEARS:
        s = sys_df[(sys_df.year == y) & (sys_df["pass"] == "P1")]
        ca = s[~s.zone.str.startswith("WECC")]
        dw = (
            ca.assign(pw=ca.price * ca.demand)
            .groupby("hour")[["pw", "demand"]]
            .sum()
            .sort_index()
            .reindex(range(8760))
        )
        lam = (dw.pw / dw.demand).to_numpy()
        out[y] = lam, dw.demand.to_numpy()
    return out


def actual_rt() -> dict[int, np.ndarray]:
    a = pd.read_parquet(ACTUAL_LMP)
    out = {}
    for y in YEARS:
        ay = a[a.year == y].sort_values("hour")
        out[y] = ay.rt.to_numpy(dtype=float)[:8760]
    return out


def wavg(x, w, m):
    m = m & np.isfinite(x) & np.isfinite(w)
    return float(np.average(x[m], weights=w[m])) if m.sum() else float("nan")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    meas = measured_battery()
    mod = model_storage(bundle)
    lam = model_lambda(bundle)
    rt = actual_rt()

    print(f"# EVENING-STORAGE-TIMING decomposition — bundle {bundle.name}\n")

    # ---- (1) battery diurnal timing: model vs measured -----------------
    print("## (1) net-battery MW by hod (+discharge / -charge): model | measured")
    for y in YEARS:
        g = mod[y]
        hod_m = g.groupby("hod").net.mean().reindex(range(24)).to_numpy()
        mb = meas[y]
        hod_c = pd.Series(mb).groupby(np.arange(8760) % 24).mean().to_numpy()
        print(f"  {y}:")
        print("    model m:", " ".join(f"{v:6.0f}" for v in hod_m))
        print("    meas  c:", " ".join(f"{v:6.0f}" for v in hod_c))
    print()

    # ---- (2) charge/discharge energy budget ----------------------------
    print("## (2) storage energy budget (TWh): model | measured")
    print(
        f"  {'year':<6}{'chg_m':>7}{'chg_c':>7}{'dis_m':>7}{'dis_c':>7}"
        f"{'eveDis_m':>9}{'eveDis_c':>9}{'belChg_m':>9}{'belChg_c':>9}"
    )
    for y in YEARS:
        g = mod[y]
        mb = meas[y]
        mb_hod = np.arange(8760) % 24
        chg_m = g.charge_mw.abs().sum() / 1e6
        dis_m = g.discharge_mw.abs().sum() / 1e6
        chg_c = (-np.clip(mb, None, 0)).sum() / 1e6
        dis_c = np.clip(mb, 0, None).sum() / 1e6
        eve = np.isin(g.hod.to_numpy(), EVENING)
        eve_c = np.isin(mb_hod, EVENING)
        bel = np.isin(g.hod.to_numpy(), BELLY)
        bel_c = np.isin(mb_hod, BELLY)
        eveDis_m = g.discharge_mw.abs().to_numpy()[eve].sum() / 1e6
        eveDis_c = np.clip(mb[eve_c], 0, None).sum() / 1e6
        belChg_m = g.charge_mw.abs().to_numpy()[bel].sum() / 1e6
        belChg_c = (-np.clip(mb[bel_c], None, 0)).sum() / 1e6
        print(
            f"  {y:<6}{chg_m:>7.2f}{chg_c:>7.2f}{dis_m:>7.2f}{dis_c:>7.2f}"
            f"{eveDis_m:>9.2f}{eveDis_c:>9.2f}{belChg_m:>9.2f}{belChg_c:>9.2f}"
        )
    print()

    # ---- (3) belly over-price decomposed by model storage state --------
    print(
        "## (3) belly hod 10-14: lambda residual (model-rt), split by model storage state"
    )
    print(
        f"  {'year':<6}{'block':<12}{'n':>5}{'lam_m':>7}{'rt':>7}{'resid':>7}"
        f"{'chgMW_m':>8}{'chgMW_c':>8}"
    )
    for y in YEARS:
        lm, dem = lam[y]
        r = rt[y]
        g = mod[y]
        mb = meas[y]
        hod = np.arange(8760) % 24
        bel = np.isin(hod, BELLY)
        net_m = g.net.to_numpy()
        charging = net_m < -ACTIVE_MW  # model net-charging hours
        idle_dis = ~charging
        for lbl, mask in (
            ("belly-ALL", bel),
            ("belly-charging", bel & charging),
            ("belly-idle/dis", bel & idle_dis),
        ):
            n = int(mask.sum())
            lam_m = wavg(lm, dem, mask)
            rtb = wavg(r, dem, mask)
            resid = wavg(lm - r, dem, mask)
            chg_m = g.charge_mw.abs().to_numpy()[mask].mean() if n else float("nan")
            chg_c = (-np.clip(mb, None, 0))[mask].mean() if n else float("nan")
            print(
                f"  {y:<6}{lbl:<12}{n:>5}{lam_m:>7.1f}{rtb:>7.1f}{resid:>+7.1f}"
                f"{chg_m:>8.0f}{chg_c:>8.0f}"
            )
    print()

    # ---- (4) evening over/under: discharge + import vs CT rung ----------
    print("## (4) evening hod 17-21: lambda residual + net-battery MW (model|meas)")
    print(
        f"  {'year':<6}{'lam_m':>7}{'rt':>7}{'resid':>7}{'netBat_m':>9}{'netBat_c':>9}"
    )
    for y in YEARS:
        lm, dem = lam[y]
        r = rt[y]
        g = mod[y]
        mb = meas[y]
        hod = np.arange(8760) % 24
        eve = np.isin(hod, EVENING)
        lam_m = wavg(lm, dem, eve)
        rtb = wavg(r, dem, eve)
        resid = wavg(lm - r, dem, eve)
        nb_m = g.net.to_numpy()[eve].mean()
        nb_c = mb[eve].mean()
        print(f"  {y:<6}{lam_m:>7.1f}{rtb:>7.1f}{resid:>+7.1f}{nb_m:>9.0f}{nb_c:>9.0f}")
    print()

    # ---- (5) storage-active share of hours by block --------------------
    print("## (5) model storage-active hour share (|net|>ACTIVE_MW) by block")
    for y in YEARS:
        g = mod[y]
        net = g.net.to_numpy()
        hod = g.hod.to_numpy()
        for lbl, hrs in (("belly", BELLY), ("evening", EVENING), ("all", range(24))):
            m = np.isin(hod, list(hrs))
            act = (np.abs(net[m]) > ACTIVE_MW).mean()
            chg = (net[m] < -ACTIVE_MW).mean()
            dis = (net[m] > ACTIVE_MW).mean()
            print(
                f"  {y} {lbl:<8} active {act:4.0%}  charging {chg:4.0%}  discharging {dis:4.0%}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
