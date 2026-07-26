"""caiso-120 — belly price-formation REGIME SPLIT on the netrev keeper's own committed bytes (no LP).

Splits every belly hour (hod 10-15, model local clock) by the ACTUAL market's
price regime — surplus (measured RT <= $20/MWh) vs firm (RT > $20) — and
compares, per regime: measured RT, the keeper's demand-weighted CA-zone model
lambda, the raw measured min-hub (min of MALIN / PALOVRDE), and the signed
interchange on both sides (measured EIA-930 CISO net import vs the keeper's
import class). Also prints the full belly / evening price-distribution table
(share <=$0 / <=$10 / <=$20 / >$35; evening >$100) that quantifies the model's
price-compression defect.

Inputs (ALL committed / raw — no solve, no gitignored parquet):
  * results/calibration/caiso_netrev_margin/hourly/system_<y>.parquet   (model zonal lambda + demand)
  * results/calibration/caiso_netrev_margin/hourly/class_hourly_<y>.parquet (model import class MW)
  * data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet          (measured RT/DA)
  * data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet   (measured MALIN/PALOVRDE)
  * EIA-930 CISO via _caiso102_evening_merit.eia930_hourly               (measured net interchange)

Finding: results/calibration/FINDING-caiso120-belly-regime-split-2026-07-26.md
Usage:   python3 scripts/probes/_caiso120_price_regime.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _caiso102_evening_merit import eia930_hourly  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results/calibration/caiso_netrev_margin"
ACT = ROOT / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
HUB = ROOT / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"

CA_ZONES = ["LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26"]
BELLY = [10, 11, 12, 13, 14, 15]  # t: model local-clock hour-of-day, lane convention
EVENING = [17, 18, 19, 20, 21]
SURPLUS_THRESHOLD = 20.0  # $/MWh: the actual market's surplus/curtailment regime
# boundary. Not a tunable — a diagnostic split point sitting between the
# curtailment-priced cluster (<= ~$15) and the gas-priced cluster (>= ~$25) of
# the measured CAISO belly RT distribution; the conclusions are insensitive to
# +-$5 (checked 15/20/25 while deriving).
YEARS = (2023, 2024, 2025)


def _model_lambda(year: int) -> np.ndarray:
    """(8760,) demand-weighted CA-zone mean model price from the keeper sidecar."""
    s = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    s = s[s.zone.isin(CA_ZONES)].copy()
    s["pw"] = s.price * s.demand
    g = s.groupby("hour")
    return (g.pw.sum() / g.demand.sum()).reindex(range(8760)).to_numpy(float)


def _model_import(year: int) -> np.ndarray:
    """(8760,) keeper import-class MW from the class sidecar."""
    c = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    return (
        c[c.klass == "import"].set_index("hour").mw.reindex(range(8760)).to_numpy(float)
    )


def _dist(x: np.ndarray, mask: np.ndarray) -> dict:
    v = x[mask]
    return {
        "mean": float(np.nanmean(v)),
        "le0": float(np.mean(v <= 0) * 100),
        "le10": float(np.mean(v <= 10) * 100),
        "le20": float(np.mean(v <= 20) * 100),
        "gt35": float(np.mean(v > 35) * 100),
    }


def main() -> None:
    act = pd.read_parquet(ACT)
    hub = pd.read_parquet(HUB)
    hod = np.arange(8760) % 24
    belly = np.isin(hod, BELLY)
    evening = np.isin(hod, EVENING)

    print("=" * 100)
    print("TABLE 1 — belly (hod 10-15) price-distribution: model vs measured RT vs raw min-hub")
    print("=" * 100)
    for y in YEARS:
        m = _model_lambda(y)
        a = act[act.year == y].set_index("hour").rt.reindex(range(8760)).to_numpy(float)
        hmin = (
            hub[hub.year == y]
            .pivot(index="hour", columns="hub", values="price")
            .min(axis=1)
            .reindex(range(8760))
            .to_numpy(float)
        )
        dm, da = _dist(m, belly), _dist(a, belly)
        print(
            f"{y} model : mean ${dm['mean']:6.1f}  <=$0 {dm['le0']:5.1f}%  <=$10 {dm['le10']:5.1f}%"
            f"  <=$20 {dm['le20']:5.1f}%  >$35 {dm['gt35']:5.1f}%"
        )
        print(
            f"{y} act RT: mean ${da['mean']:6.1f}  <=$0 {da['le0']:5.1f}%  <=$10 {da['le10']:5.1f}%"
            f"  <=$20 {da['le20']:5.1f}%  >$35 {da['gt35']:5.1f}%"
        )
        near = np.mean(np.abs(m[belly] - hmin[belly]) < 3) * 100
        ev_m = np.mean(m[evening] > 100) * 100
        ev_a = np.mean(a[evening] > 100) * 100
        print(
            f"{y} min-hub belly mean ${np.nanmean(hmin[belly]):6.1f}; model within $3 of min-hub"
            f" {near:4.1f}% of belly hours; evening >$100: model {ev_m:.1f}% vs act {ev_a:.1f}%"
        )
        print()

    print("=" * 100)
    print("TABLE 2 — belly hours split by the ACTUAL market's regime (surplus = RT <= $20)")
    print("=" * 100)
    hdr = (
        f"{'yr':4s} {'regime':16s} {'n':>4s} {'actRT':>7s} {'model':>7s} {'m-a':>6s} "
        f"{'minhub':>7s} {'m-hub':>6s} {'act GW':>7s} {'mdl GW':>7s} {'actexp%':>7s}"
    )
    print(hdr)
    for y in YEARS:
        m = _model_lambda(y)
        imp_m = _model_import(y)
        e = eia930_hourly(y)
        a = act[act.year == y].set_index("hour").rt.reindex(range(8760)).to_numpy(float)
        hmin = (
            hub[hub.year == y]
            .pivot(index="hour", columns="hub", values="price")
            .min(axis=1)
            .reindex(range(8760))
            .to_numpy(float)
        )
        for name, mask in (
            ("surplus <=20", belly & (a <= SURPLUS_THRESHOLD)),
            ("firm    >20", belly & (a > SURPLUS_THRESHOLD)),
        ):
            print(
                f"{y:<4d} {name:16s} {mask.sum():4d} {np.nanmean(a[mask]):7.1f}"
                f" {np.nanmean(m[mask]):7.1f} {np.nanmean(m[mask] - a[mask]):+6.1f}"
                f" {np.nanmean(hmin[mask]):7.1f} {np.nanmean(m[mask] - hmin[mask]):+6.1f}"
                f" {np.nanmean(e['imports'][mask]) / 1e3:7.2f}"
                f" {np.nanmean(imp_m[mask]) / 1e3:7.2f}"
                f" {np.mean(e['imports'][mask] < 0) * 100:6.1f}%"
            )
        print()


if __name__ == "__main__":
    main()
