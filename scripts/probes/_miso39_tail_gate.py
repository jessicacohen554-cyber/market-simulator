"""Score the miso-39 pergen probe against the scarcity-tail gate.

Compares a --miso-reserve-pergen bundle against the miso-38 keeper-repro
baseline on the quantities the gate names (scope doc gate 4 + the
scarcity-tail session brief):

* >$200 (and >$100) tail hours, system and per zone, vs the actual
  Indiana-hub RT/DA counts and the actual South zone-mean counts;
* timing coincidence of the model's priced hours with the actual event hours;
* reserve-price distribution (does the zonal family reach the curve steps?);
* CT_PEAKER / CC_REGULAR / coal annual TWh drift vs the baseline (the
  fleet-mix symptom the tail was suppressing);
* zone-mean LMP drift (structural gates 1-3 must not degrade).

Usage:
  PYTHONPATH=.:src python scripts/probes/_miso39_tail_gate.py \
      results/calibration/MISO/miso_39_reserve_pergen \
      results/calibration/MISO/_diag_miso38_base
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_sim.config.paths import RAW_DIR  # noqa: E402

YEARS = (2023, 2024, 2025)


def _actual(year: int):
    df = pd.read_parquet(
        RAW_DIR / "_validation-source" / "actual_lmp_hourly_zonal_MISO.parquet"
    )
    d = df[df.year == year]
    ind = d[d.hub == "INDIANA.HUB"].set_index("hour").sort_index()
    south = d[d.zone == "MISO-South"].groupby("hour")[["rt", "da"]].mean()
    return ind, south


def _system(bundle: Path) -> pd.DataFrame:
    return pd.read_parquet(bundle / "system.parquet")


def _class_twh(bundle: Path, year: int) -> pd.Series:
    disp = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet", columns=["klass", "mw"]
    )
    return disp.groupby("klass")["mw"].sum() / 1e6


def main(probe: Path, base: Path) -> None:
    sysp = _system(probe)
    sysb = _system(base)
    for year in YEARS:
        sp = sysp[sysp.year == year]
        sb = sysb[sysb.year == year]
        ind, south = _actual(year)
        # zonal price matrix (hour x zone)
        zp = sp.pivot_table(index="hour", columns="zone", values="price")
        zb = sb.pivot_table(index="hour", columns="zone", values="price")
        internal = [z for z in zp.columns if "external" not in z]
        sys_price_p = zp[internal].mean(axis=1)
        sys_price_b = zb[internal].mean(axis=1)

        print(f"\n===== {year} =====")
        print("tail hours (>$200 / >$100):")
        print(
            f"  actual IND RT {int((ind.rt > 200).sum()):4d}/"
            f"{int((ind.rt > 100).sum()):4d}   DA {int((ind.da > 200).sum()):4d}/"
            f"{int((ind.da > 100).sum()):4d}   actual South-mean RT "
            f"{int((south.rt > 200).sum()):4d}/{int((south.rt > 100).sum()):4d}"
            f"   DA {int((south.da > 200).sum()):4d}/{int((south.da > 100).sum()):4d}"
        )
        for zname in internal:
            p200 = int((zp[zname] > 200).sum())
            p100 = int((zp[zname] > 100).sum())
            b200 = int((zb[zname] > 200).sum())
            if p200 or p100 or b200:
                print(
                    f"  model {zname:14s} {p200:4d}/{p100:4d}   (baseline "
                    f"{b200}/{int((zb[zname] > 100).sum())})"
                )
        print(
            f"  model system-mean {int((sys_price_p > 200).sum()):4d}/"
            f"{int((sys_price_p > 100).sum()):4d}   (baseline "
            f"{int((sys_price_b > 200).sum())}/{int((sys_price_b > 100).sum())})"
        )

        # timing: model South >$200 hours vs actual event hours
        if "MISO-South" in zp.columns:
            model_hot = zp.index[zp["MISO-South"] > 200].to_numpy()
            for label, series, thresh in (
                ("actual South RT>200", south.rt, 200.0),
                ("actual South RT>100", south.rt, 100.0),
                ("actual IND RT>200", ind.rt, 200.0),
                ("actual IND DA>200", ind.da, 200.0),
            ):
                hot = set(series.index[series > thresh])
                hit = len(hot & set(model_hot))
                print(
                    f"  model South>$200 ({len(model_hot)} h) ∩ {label} "
                    f"({len(hot)} h): {hit}"
                )

        # reserve price
        if "reserve_price" in sp.columns:
            rp = sp.groupby("hour")["reserve_price"].max()
            rb = sb.groupby("hour")["reserve_price"].max()
            print(
                "  reserve price: probe nonzero "
                f"{int((rp > 0.01).sum())} h, >=$200 {int((rp >= 199).sum())} h, "
                f"max ${rp.max():.0f}   (baseline nonzero {int((rb > 0.01).sum())} h, "
                f"max ${rb.max():.0f})"
            )

        # price level / duration (structural gates must not degrade wildly)
        print(
            f"  mean LMP: probe {sys_price_p.mean():.2f}  baseline "
            f"{sys_price_b.mean():.2f}   p50 {sys_price_p.median():.2f} vs "
            f"{sys_price_b.median():.2f}   max {sys_price_p.max():.0f} vs "
            f"{sys_price_b.max():.0f}"
        )

        # class energy drift
        tp = _class_twh(probe, year)
        tb = _class_twh(base, year)
        rows = []
        for c in (
            "CT_PEAKER",
            "CT_INTERMEDIATE",
            "CC_REGULAR",
            "COAL_BIT",
            "COAL_SUB",
            "ST_GAS",
        ):
            if c in tp.index or c in tb.index:
                a, b = float(tp.get(c, 0.0)), float(tb.get(c, 0.0))
                rows.append(f"{c} {a:.2f} ({a - b:+.2f})")
        print("  class TWh (probe, delta vs baseline): " + "; ".join(rows))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
