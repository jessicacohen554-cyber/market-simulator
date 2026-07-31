"""pjm-143 A/B: the EIA-923 `HY` hydro LEVEL vs the PS-inclusive `NG: WAT` pin.

Scores the PRE-REGISTERED predictions of
``results/calibration/PREREG-pjm143-hydro-level-923hy-2026-07-31.md`` (§4 sign
and magnitude, §5 kill/keep) from the two solved bundles — no solve, and no
statistic that is not in the prereg.

Arm A = the ``2026-07-30-pjm-140-rampenv`` keeper recipe replayed at HEAD with
the ``NG: WAT`` level pin still armed. Arm B = the same recipe at the same HEAD
with ``"PJM"`` listed in ``constants.EIA930_PS_FOLDED_INTO_WAT``, so the pin is
refused and the monthly level stays on EIA-923 ``HY`` — the same series and the
same plant population the per-plant budget is built from.

Sections::

  §1 level        — the hydro energy actually dispatched in each arm, against
                    both the pinned target and the corrected 923 `HY` budget.
  §2 re-service   — where the removed zero-marginal-cost energy went: per-class
                    dispatch deltas and the imports/storage/slack residual.
  §3 price        — load-weighted and simple-mean LMP per arm, against the
                    benchmark's DA/RT load-weighted actuals (the C3a basis).
  §4 prereg §4    — the declared sign, checked limb by limb, and the declared
                    magnitude band (+0.3 to +1.5 $/MWh) checked against what
                    actually happened. A refuted prediction is REPORTED AS
                    REFUTED, never re-written (the pjm-137/140 precedent).
  §5 seasonality  — the fold is summer-peaked and diurnally peak-shaped, so the
                    price effect should concentrate there; measured per month
                    and per hour-of-day rather than asserted.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_pjm143_hydro_level_ab.py \
        --control results/calibration/pjm143_control_A \
        --arm results/calibration/pjm143_hy_level_B
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "PJM"

# Pre-registered magnitude band on the load-weighted LMP rise (PREREG §4).
PREREG_LMP_LO, PREREG_LMP_HI = 0.3, 1.5
# Pre-registered per-year level deltas (PREREG §1, measured no-LP before solving).
PREREG_LEVEL_DELTA_TWH = {2023: -6.474, 2024: -6.955, 2025: -7.039}


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """Return the P1 system frame (one row per zone-hour) for ``year``."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"] if "P1" in set(df["pass"]) else df


def _classes(bundle: Path, year: int) -> pd.Series:
    """Return ``class -> annual TWh`` from the P1 class-hourly sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"] if "P1" in set(df["pass"]) else df
    return df.groupby("klass")["mw"].sum() / 1e6


def _load_weighted(sysf: pd.DataFrame) -> float:
    """Return the load-weighted mean LMP ($/MWh) — the C3a model basis."""
    return float((sysf["price"] * sysf["demand"]).sum() / sysf["demand"].sum())


def _bench(year: int) -> dict:
    """Return the committed benchmark block for ``year``."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]


def section_1_level(a: Path, b: Path) -> dict[int, tuple[float, float]]:
    """Print the dispatched hydro energy in each arm; return the per-year pair."""
    print("\n== §1 hydro energy DISPATCHED (P1), control vs candidate ==")
    print("   the pinned level is the PS-inclusive EIA-930 NG: WAT total;")
    print("   the corrected level is the EIA-923 HY budget the LP units ARE.")
    out: dict[int, tuple[float, float]] = {}
    for year in YEARS:
        ha = float(_classes(a, year).get("hydro", 0.0))
        hb = float(_classes(b, year).get("hydro", 0.0))
        out[year] = (ha, hb)
        pre = PREREG_LEVEL_DELTA_TWH[year]
        print(
            f"  {year}: control {ha:7.3f} TWh -> candidate {hb:7.3f} TWh "
            f"({hb - ha:+7.3f} TWh) | prereg budget delta {pre:+7.3f} TWh"
        )
    return out


def section_2_reservice(a: Path, b: Path) -> None:
    """Print where the removed zero-marginal-cost energy was re-served."""
    print("\n== §2 re-service: per-class dispatch delta (candidate - control) ==")
    for year in YEARS:
        ca, cb = _classes(a, year), _classes(b, year)
        delta = (cb - ca).reindex(sorted(set(ca.index) | set(cb.index))).fillna(0.0)
        moved = delta[delta.abs() >= 0.001].sort_values()
        print(f"  -- {year}: total {delta.sum():+7.3f} TWh")
        for klass, d in moved.items():
            base = float(ca.get(klass, 0.0))
            pct = (d / base * 100) if base > 1e-9 else float("nan")
            print(f"     {klass:16s} {d:+8.4f} TWh ({pct:+6.2f} % of its own)")


def section_3_price(a: Path, b: Path) -> dict[int, tuple[float, float]]:
    """Print each arm's price level against the benchmark; return the pairs."""
    print("\n== §3 price: load-weighted LMP per arm vs the benchmark actual ==")
    out: dict[int, tuple[float, float]] = {}
    for year in YEARS:
        pa, pb = _load_weighted(_system(a, year)), _load_weighted(_system(b, year))
        out[year] = (pa, pb)
        lmp = _bench(year).get("avgLMP", {})
        da = float(lmp.get("da_lw", float("nan")))
        ea, eb = (pa / da - 1) * 100, (pb / da - 1) * 100
        print(
            f"  {year}: control {pa:7.3f} -> candidate {pb:7.3f} $/MWh "
            f"({pb - pa:+6.3f}, {(pb / pa - 1) * 100:+5.2f} %) | "
            f"actual DA lw {da:6.2f} | C3a error {ea:+6.2f} % -> {eb:+6.2f} % "
            f"({'unchanged vs' if abs(eb) == abs(ea) else 'toward' if abs(eb) < abs(ea) else 'AWAY from'} actual)"
        )
    return out


def section_4_prereg(
    level: dict[int, tuple[float, float]],
    price: dict[int, tuple[float, float]],
    a: Path,
    b: Path,
) -> None:
    """Check the pre-registered sign and magnitude, limb by limb."""
    print("\n== §4 PREREG §4 checks — declared BEFORE the first solve ==")
    for year in YEARS:
        ha, hb = level[year]
        pa, pb = price[year]
        ca, cb = _classes(a, year), _classes(b, year)
        fossil = [
            k
            for k in set(ca.index) | set(cb.index)
            if k.startswith(("CC_", "CT_", "COAL", "ST_", "OTHER_FOSSIL"))
        ]
        d_fossil = float(sum(cb.get(k, 0.0) - ca.get(k, 0.0) for k in fossil))
        rise = pb - pa
        limbs = [
            ("hydro FALLS", hb < ha),
            ("fossil volume RISES", d_fossil > 0),
            ("load-weighted LMP RISES", rise > 0),
        ]
        print(f"  -- {year}:")
        for name, ok in limbs:
            print(f"     [{'HOLDS' if ok else 'REFUTED'}] {name}")
        band = PREREG_LMP_LO <= rise <= PREREG_LMP_HI
        print(
            f"     [{'HOLDS' if band else 'REFUTED'}] magnitude in the declared "
            f"+{PREREG_LMP_LO}..+{PREREG_LMP_HI} $/MWh band — actual {rise:+.3f}"
        )
        print(f"     fossil delta {d_fossil:+.3f} TWh")


def section_5_seasonality(a: Path, b: Path) -> None:
    """Measure where in the year and the day the price effect concentrates."""
    print("\n== §5 where the price effect lands (the fold is summer/peak-shaped) ==")
    for year in YEARS:
        sa, sb = _system(a, year), _system(b, year)
        # Zone-hour frames -> one system price series per hour (load-weighted).
        def _hourly(df: pd.DataFrame) -> np.ndarray:
            g = df.groupby("hour").apply(
                lambda d: (d["price"] * d["demand"]).sum() / d["demand"].sum(),
                include_groups=False,
            )
            return g.sort_index().to_numpy(dtype=float)

        pa, pb = _hourly(sa), _hourly(sb)
        n = min(len(pa), len(pb))
        d = pb[:n] - pa[:n]
        hod = np.arange(n) % 24
        # Month from the model clock (8760 hours, no leap day).
        month = (
            pd.date_range(f"{year}-01-01", periods=n, freq="h")
            .to_series()
            .dt.month.to_numpy()
        )
        by_month = [float(np.nanmean(d[month == m])) for m in range(1, 13)]
        summer = float(np.nanmean(d[np.isin(month, (6, 7, 8, 9))]))
        other = float(np.nanmean(d[~np.isin(month, (6, 7, 8, 9))]))
        peak = float(np.nanmean(d[np.isin(hod, range(13, 21))]))
        night = float(np.nanmean(d[np.isin(hod, range(0, 6))]))
        print(f"  -- {year}: mean price delta by month ($/MWh)")
        print("     " + " ".join(f"{v:6.3f}" for v in by_month))
        print(
            f"     Jun-Sep {summer:+.3f} vs rest {other:+.3f} | "
            f"HE14-21 {peak:+.3f} vs HE01-06 {night:+.3f}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    args = ap.parse_args()
    a, b = args.control, args.arm
    print(f"control (pin armed)   : {a}")
    print(f"candidate (923 HY)    : {b}")
    level = section_1_level(a, b)
    section_2_reservice(a, b)
    price = section_3_price(a, b)
    section_4_prereg(level, price, a, b)
    section_5_seasonality(a, b)


if __name__ == "__main__":
    main()
