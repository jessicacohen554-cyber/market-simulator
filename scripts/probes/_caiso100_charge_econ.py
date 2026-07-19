"""CAISO-100 derive-first probe: charge-side economics INSIDE the shape envelope.

The caiso-99 keeper (measured NG:OTH p95 envelope live) still over-prices the
belly (+7.7/+7.6/+6.3). FINDING-caiso99 §7 localizes the residual to charge
ECONOMICS: the zero-cycling-cost LP charges at the envelope cap in ~every
economic hour, while the measured fleet's mean belly rate sits at ~0.5-0.7 of
its own p95. This probe makes the derive-first measurement the CAISO-100
charter names: the marginal spread at which the MODEL charges vs the MEASURED
fleet's realized charge-day spread distribution.

NO new-mechanism LP — reads a SAME-MACHINE repro of the promoted keeper recipe
(``_caiso99_shape_B.py`` -> gitignored ``caiso99_shape_B``; FINDING-caiso92b
protocol) plus committed raw inputs only.

Per (year, day):
  MODEL   belly (hod 10-14) battery charge (storage.parquet, tech !=
          pumped_storage, P1) as a fraction of the EIA-860 monthly fleet and of
          the frozen p95 envelope; day spread on the MODEL lambda (demand-
          weighted CA-zone price, the _caiso92_report construction).
  MEASURED EIA-930 CISO ``NG: OTH`` charge on the same fleet basis; day spread
          on the actual RT and DA LMP (actual_lmp_hourly_CAISO.parquet).

Emits, for model and measured side by side: annual charge/discharge TWh; the
per-day envelope-utilization distribution (deciles, skip share u<0.25); the
day-median vs charge-weighted median spread (TB4 and evening-minus-belly); the
revealed marginal spread S* below which only 5/10/25 % of annual belly charge
occurs; and the implied conduct cost c* = S* - lambda_chg x (1/rte - 1),
rte = 0.86 (constants.STORAGE_TECHS li_ion_4hr) — the number to compare
against the derived cycling-degradation cost
``storage._degradation_cost_per_mwh`` (= capex_per_kwh x 1000 / cycles x
STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 285000/5000 x 0.25 = $14.25/MWh
discharged, NREL ATB 2024 capex + LFP warranty cycle life).

Usage: python scripts/probes/_caiso100_charge_econ.py <bundle_dir> [<bundle_B>]
With two bundles (caiso99_repro_A caiso99_shape_B) prints both model columns.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import set_eia860_vintage  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.storage import load_eia860_storage  # noqa: E402

EIA930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
ENV = REPO / "data" / "raw" / "reference" / "caiso-storage-shape-envelope.csv"
YEARS = (2023, 2024, 2025)
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
BELLY = np.arange(10, 15)
EVENING = np.arange(17, 22)
RTE = 0.86  # li_ion_4hr round trip (constants.STORAGE_TECHS)
DERIVED_CYCLING_COST = 285.0 * 1000.0 / 5000.0 * 0.25  # $14.25/MWh discharged


def monthly_fleet(year: int) -> np.ndarray:
    """(12,) installed CAISO battery MW per month (PS excluded) — the envelope
    denominator and the same fleet basis the LP's COD-ramped caps scale."""
    set_eia860_vintage(None)
    cfg = ScenarioConfig(mode="backcast", storage_vintage_ramp=True)
    fleet = np.zeros(12)
    for u in load_eia860_storage("CAISO", year, cfg):
        if u.tech_name == "pumped_storage":
            continue
        fleet += np.array(
            u.monthly_power_mw
            if u.monthly_power_mw is not None
            else [u.power_cap_mw] * 12,
            dtype=float,
        )
    return fleet


def measured_chg_dis(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(8760,) measured battery charge MW and discharge MW from NG:OTH."""
    d = pd.read_parquet(EIA930, columns=["Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    dy = d[d["Local date"].dt.year == year].sort_values(["Local date", "Hour"])
    v = np.nan_to_num(dy["NG: OTH"].to_numpy(dtype=float))
    v = v[:8760] if len(v) >= 8760 else np.pad(v, (0, 8760 - len(v)))
    return np.clip(-v, 0.0, None), np.clip(v, 0.0, None)


def model_chg_dis(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """(8760,) model battery charge/discharge MW (P1, PS excluded)."""
    s = pd.read_parquet(
        bundle / "storage.parquet",
        columns=["pass", "year", "tech", "hour", "charge_mw", "discharge_mw"],
    )
    s = s[(s["pass"] == "P1") & (s.year == year) & (s.tech != "pumped_storage")]
    g = (
        s.groupby("hour")[["charge_mw", "discharge_mw"]]
        .sum()
        .reindex(range(8760), fill_value=0.0)
        .sort_index()
    )
    return g.charge_mw.to_numpy(), g.discharge_mw.to_numpy()


def model_lambda(bundle: Path, year: int) -> np.ndarray:
    """(8760,) demand-weighted CA-zone model lambda (_caiso92_report basis)."""
    sys_df = pd.read_parquet(bundle / "system.parquet")
    s = sys_df[(sys_df.year == year) & (sys_df["pass"] == "P1")]
    ca = s[~s.zone.str.startswith("WECC")]
    dw = (
        ca.assign(pw=ca.price * ca.demand)
        .groupby("hour")[["pw", "demand"]]
        .sum()
        .sort_index()
        .reindex(range(8760))
    )
    return (dw.pw / dw.demand).to_numpy()


def day_spreads(px: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(365,) TB4, evening-minus-belly, belly-mean from an (8760,) price."""
    p = np.nan_to_num(px, nan=np.nanmean(px))[: 365 * 24].reshape(365, 24)
    srt = np.sort(p, axis=1)
    return (
        srt[:, -4:].mean(1) - srt[:, :4].mean(1),
        p[:, EVENING].mean(1) - p[:, BELLY].mean(1),
        p[:, BELLY].mean(1),
    )


def wq(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Weighted quantile of ``values`` under mass ``weights``."""
    i = np.argsort(values)
    v, w = values[i], weights[i]
    if w.sum() <= 0:
        return float("nan")
    return float(np.interp(q, np.cumsum(w) / w.sum(), v))


def side(tag, chg, dis, lam, fleet_h, p95) -> None:
    """Print one side's (model or measured) stats for one year."""
    chg_d = chg[: 365 * 24].reshape(365, 24)
    belly_mwh = chg_d[:, BELLY].sum(1)
    u = (chg / fleet_h)[: 365 * 24].reshape(365, 24)[:, BELLY].mean(1) / p95
    tb4, eb, belly_l = day_spreads(lam)
    dec = np.round(np.quantile(u, [0.1, 0.25, 0.5, 0.75, 0.9]), 2)
    lam_c = wq(belly_l, belly_mwh, 0.5)
    eff = lam_c * (1.0 / RTE - 1.0)
    print(
        f"  [{tag}] chg {chg.sum() / 1e6:5.2f} dis {dis.sum() / 1e6:5.2f} TWh | "
        f"u mean {u.mean():.2f} dec {dec} skip(u<.25) {(u < 0.25).mean():.2f}"
    )
    for name, S in (("TB4", tb4), ("eve-belly", eb)):
        parts = []
        for q in (0.05, 0.10, 0.25):
            s_star = wq(S, belly_mwh, q)
            parts.append(f"S{int(q * 100):02d} {s_star:5.1f} (c* {s_star - eff:5.1f})")
        print(
            f"      {name:9s} day-med {np.median(S):6.1f} chg-wtd med "
            f"{wq(S, belly_mwh, 0.5):6.1f} | " + "  ".join(parts)
        )
    print(f"      lam_chg(wtd med) {lam_c:5.1f} -> eff-loss floor {eff:4.1f} $/MWh")


def main() -> int:
    bundles = [Path(p) for p in sys.argv[1:]]
    if not bundles:
        print(__doc__)
        return 2
    env = pd.read_csv(ENV)
    lmp = pd.read_parquet(LMP)
    moh = np.repeat(np.arange(12), np.array(DAYS_IN_MONTH) * 24)[:8760]
    print(
        f"# CAISO-100 charge-economics probe — derived cycling cost "
        f"${DERIVED_CYCLING_COST:.2f}/MWh discharged\n"
    )
    for year in YEARS:
        fleet_h = monthly_fleet(year)[moh]
        p95 = float(env[(env.year == year) & env.hod.isin(BELLY)].chg_frac_p95.mean())
        print(
            f"===== {year} (belly p95 {p95:.3f}, fleet Dec {fleet_h[-1]:.0f} MW) ====="
        )
        m_chg, m_dis = measured_chg_dis(year)
        a = lmp[lmp.year == year].sort_values("hour")
        side("meas/RT", m_chg, m_dis, a.rt.to_numpy(dtype=float)[:8760], fleet_h, p95)
        side("meas/DA", m_chg, m_dis, a.da.to_numpy(dtype=float)[:8760], fleet_h, p95)
        for b in bundles:
            chg, dis = model_chg_dis(b, year)
            side(f"model/{b.name}", chg, dis, model_lambda(b, year), fleet_h, p95)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
