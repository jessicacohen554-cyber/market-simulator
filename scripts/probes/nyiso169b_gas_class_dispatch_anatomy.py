"""nyiso-169b — class-dispatch anatomy: CC_CHP over-run, CT_PEAKER / ST_GAS deficit, hydro shape.

ZERO SOLVE. Reads the designated keeper's committed hourly sidecars, the
committed per-ISO benchmark parts, NYISO's CAMPD unit-level hourly record and
EIA-930 NYIS. No LP runs; nothing here is or becomes an LP input.

Rule 22 ``[R-HOLDOUT]``: every year read is 2023, 2024 or 2025.

The question
------------
Four class-level objects were raised against keeper
``2026-08-30-nyiso-159-loss-surface``, with a proposed cause for the first:
**that CC_CHP's duct-burner (``peak``) offer band is priced too low**, letting
the class over-run at high capacity factor.

The proposal is falsifiable and this probe falsifies it. A too-cheap peak band
can only bid the class in where that band is the marginal one — the **top** of
its own duration curve. Measurement B shows the over-run is monotonically
concentrated at the **bottom**: in 2025 the model sits 3.3 % BELOW measured in
the top 1 % of hours and 37.4 % ABOVE in the bottom quartile, and in 2023 it is
14.9 % below at the top. The signature is a **floor**, not a peak.

Measurements
------------
A. CLASS VOLUME — model vs the committed benchmark, every class, every year.
B. CC_CHP DURATION CURVE — model vs measured by duration band, with each band's
   share of the annual over-run. **The decisive test of the peak-band proposal.**
C. CC_CHP FLOOR — low-output percentiles and zero/near-zero hours, model vs
   measured, which is where B says the over-run actually lives.
D. MONTHLY DEFICIT — CT_PEAKER and ST_GAS by month, against the measured record.
E. HYDRO SHAPE — hourly correlation, dispersion and hour-of-day swing vs
   EIA-930, the volume being already matched.

Measured classes are built from CAMPD ``unitType`` crossed with the EIA-860 CHP
flag (``market_sim.data.chp._chp_by_plant``) — the same CHP determination the
model's own classifier uses. CAMPD reports GROSS load while the benchmark is
grid-delivered, so measurement B anchors the measured series to the committed
benchmark total and compares SHAPE only; the level comparison is measurement A,
which uses the benchmark directly.

Run: ``PYTHONPATH=.:src python scripts/probes/nyiso169b_gas_class_dispatch_anatomy.py``
Writes: ``results/calibration/_nyiso169b_gas_class_dispatch_anatomy.json``
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.chp import _chp_by_plant  # noqa: E402
from scripts.data.derive_actual_lmp import _std_hour_index  # noqa: E402

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/nyiso159_lossarm_B"
BENCH = REPO / "frontend/data/backcast/bench/NYISO"
OUT = REPO / "results/calibration/_nyiso169b_gas_class_dispatch_anatomy.json"
STD_TZ = "Etc/GMT+5"

#: Duration-curve bands, as percentiles of the class's own sorted output.
DUR_BANDS = ((0, 1), (1, 5), (5, 10), (10, 25), (25, 50), (50, 75), (75, 100))

#: Non-leap month lengths in hours, on the model's 8760 calendar.
MONTH_HOURS = (744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)


def chp_plants() -> set[int]:
    """EIA-860 CHP plant codes — the model's own CHP determination."""
    flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
    return {int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"}


def campd_hourly(year: int, kind: str, chpset: set[int]) -> pd.Series:
    """Measured hourly MW for one model class, on the model's 8760 clock."""
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitType", "date", "hour", "grossLoad"],
    )
    fid = d["facilityId"].astype(int)
    ut = d["unitType"].fillna("")
    if kind == "CC_CHP":
        d = d[ut.str.contains("Combined cycle") & fid.isin(chpset)]
    elif kind == "CT_PEAKER":
        d = d[ut.str.contains("Combustion turbine") & ~fid.isin(chpset)]
    elif kind == "ST_GAS":
        d = d[ut.str.contains("fired|boiler", case=False)]
    else:
        raise ValueError(kind)
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    idx = _std_hour_index(pd.DatetimeIndex(ts).tz_localize(STD_TZ), year, STD_TZ)
    s = pd.Series(d["grossLoad"].to_numpy())
    return s.groupby(idx).sum().reindex(range(8760)).fillna(0.0)


def model_hourly(year: int, klass: str) -> pd.Series:
    """The keeper's own P1 hourly MW for one class (rule 15: read, don't replay)."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == klass)]
    return c.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0)


def bench_classes(year: int) -> dict[str, float]:
    """Committed grid-delivered class volumes, TWh."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["classFull"]


def measure_a(year: int) -> dict:
    """Class volume, model vs the committed benchmark."""
    b = bench_classes(year)
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    m = c[c["pass"] == "P1"].groupby("klass")["mw"].sum() / 1e6
    out = {}
    for k in sorted(set(list(b) + list(m.index))):
        mv, av = float(m.get(k, 0.0)), float(b.get(k, 0.0))
        out[k] = dict(
            model_twh=round(mv, 4),
            actual_twh=round(av, 4),
            delta_twh=round(mv - av, 4),
            delta_pct=(round((mv - av) / av * 100, 2) if av else None),
        )
    return out


def measure_b(year: int, chpset: set[int]) -> dict:
    """CC_CHP duration curve — THE test of the peak-band proposal."""
    mod = model_hourly(year, "CC_CHP")
    meas = campd_hourly(year, "CC_CHP", chpset)
    anchor = bench_classes(year)["CC_CHP"] * 1e6
    scale = anchor / float(meas.sum())
    meas = meas * scale  # level anchored to the benchmark; SHAPE is the object

    ms = np.sort(mod.to_numpy())[::-1]
    xs = np.sort(meas.to_numpy())[::-1]
    total = float(ms.sum() - xs.sum())

    bands = []
    for lo, hi in DUR_BANDS:
        a, b = int(8760 * lo / 100), int(8760 * hi / 100)
        dm, dx = float(ms[a:b].mean()), float(xs[a:b].mean())
        bands.append(
            dict(
                band=f"{lo}-{hi}",
                n=b - a,
                model_mw=round(dm, 1),
                measured_mw=round(dx, 1),
                delta_mw=round(dm - dx, 1),
                delta_pct=round((dm - dx) / dx * 100, 2) if dx else None,
                share_of_overrun_pct=(
                    round((float(ms[a:b].sum() - xs[a:b].sum())) / total * 100, 1)
                    if total
                    else None
                ),
            )
        )
    top = bands[0]
    bottom = bands[-1]
    return dict(
        campd_gross_twh=round(float(meas.sum() / scale / 1e6), 4),
        benchmark_twh=round(anchor / 1e6, 4),
        anchor_scale=round(scale, 4),
        bands=bands,
        peak_band_proposal_supported=bool(
            (top["delta_pct"] or 0) > 0
            and (top["delta_pct"] or 0) > (bottom["delta_pct"] or 0)
        ),
        rule=(
            "A too-cheap duct-burner (peak) band can bid the class in only where "
            "that band is marginal — the TOP of its own duration curve. The "
            "proposal is supported only if the over-run is positive at the top "
            "AND larger there than at the bottom."
        ),
    )


def measure_c(year: int, chpset: set[int]) -> dict:
    """CC_CHP low-output behaviour — where measurement B says the over-run lives."""
    mod = model_hourly(year, "CC_CHP")
    meas = campd_hourly(year, "CC_CHP", chpset)
    cap = float(max(mod.max(), meas.max()))
    out = {}
    for nm, s in (("model", mod), ("measured", meas)):
        out[nm] = dict(
            p01_mw=round(float(np.percentile(s, 1)), 1),
            p05_mw=round(float(np.percentile(s, 5)), 1),
            p25_mw=round(float(np.percentile(s, 25)), 1),
            hours_below_10pct_cap=int((s < 0.10 * cap).sum()),
            hours_near_zero=int((s < 1.0).sum()),
        )
    out["p05_excess_pct"] = round(
        (out["model"]["p05_mw"] - out["measured"]["p05_mw"])
        / out["measured"]["p05_mw"]
        * 100,
        1,
    )
    out["reference_cap_mw"] = round(cap, 1)
    return out


def measure_d(year: int, chpset: set[int]) -> dict:
    """CT_PEAKER and ST_GAS monthly deficit against the measured record."""
    mon = np.repeat(np.arange(12), MONTH_HOURS)
    out = {}
    for k in ("CT_PEAKER", "ST_GAS"):
        mod, meas = model_hourly(year, k), campd_hourly(year, k, chpset)
        rows = []
        for i in range(12):
            mv = float(mod[mon == i].sum())
            av = float(meas[mon == i].sum())
            rows.append(
                dict(
                    month=i + 1,
                    model_gwh=round(mv / 1e3, 1),
                    measured_gwh=round(av / 1e3, 1),
                    delta_pct=round((mv - av) / av * 100, 1) if av else None,
                )
            )
        deltas = [r["delta_pct"] for r in rows if r["delta_pct"] is not None]
        out[k] = dict(
            months=rows,
            worst_month=int(np.argmin(deltas) + 1),
            best_month=int(np.argmax(deltas) + 1),
            all_months_negative=bool(all(d < 0 for d in deltas)),
        )
    return out


def measure_e(year: int) -> dict:
    """Hydro shape against EIA-930 — the volume is already matched."""
    e = pd.read_parquet(RAW_DATA_DIR / "eia-930-hourly/NYIS hourly.parquet")
    ts = pd.DatetimeIndex(pd.to_datetime(e["UTC time"], utc=True))
    idx = _std_hour_index(ts, year, STD_TZ)
    a = pd.Series(e["NG: WAT"].to_numpy(), index=idx)
    a = a[a.index >= 0].groupby(level=0).mean().reindex(range(8760))

    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    m = c[c["klass"] == "hydro"].groupby("hour")["mw"].sum().reindex(range(8760)).fillna(0.0)

    ok = a.notna() & m.notna()
    am, mm = a[ok], m[ok]
    hod_m = mm.groupby(mm.index % 24).mean()
    hod_a = am.groupby(am.index % 24).mean()
    return dict(
        hourly_r=round(float(np.corrcoef(mm, am)[0, 1]), 4),
        hod_r=round(float(np.corrcoef(hod_m, hod_a)[0, 1]), 4),
        model_twh=round(float(mm.sum() / 1e6), 4),
        eia930_twh=round(float(am.sum() / 1e6), 4),
        model_cv=round(float(mm.std() / mm.mean()), 4),
        eia930_cv=round(float(am.std() / am.mean()), 4),
        model_hod_swing_mw=round(float(hod_m.max() - hod_m.min()), 1),
        eia930_hod_swing_mw=round(float(hod_a.max() - hod_a.min()), 1),
        hours=int(ok.sum()),
    )


def main() -> int:
    """Run every measurement for 2023-2025 and write the probe record."""
    chpset = chp_plants()
    rec: dict = {
        "probe": "nyiso169b_gas_class_dispatch_anatomy",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "bundle": str(KEEPER.relative_to(REPO)),
        "years": list(YEARS),
        "n_eia860_chp_plants": len(chpset),
        "by_year": {},
    }

    for year in YEARS:
        print(f"[{year}]")
        a = measure_a(year)
        for k in ("CC_CHP", "CC_REGULAR", "CT_PEAKER", "ST_GAS", "hydro"):
            v = a[k]
            print(
                f"  A  {k:<11} model {v['model_twh']:6.2f} TWh"
                f"  actual {v['actual_twh']:6.2f}  {v['delta_pct']:+7.1f}%"
            )
        b = measure_b(year, chpset)
        print(
            f"  B  CC_CHP duration: top1% {b['bands'][0]['delta_pct']:+.1f}%"
            f"  bottom25% {b['bands'][-1]['delta_pct']:+.1f}%"
            f"  -> peak-band proposal supported: {b['peak_band_proposal_supported']}"
        )
        c = measure_c(year, chpset)
        print(
            f"  C  CC_CHP floor: model p05 {c['model']['p05_mw']:.0f} MW vs"
            f" measured {c['measured']['p05_mw']:.0f} MW ({c['p05_excess_pct']:+.1f}%)"
        )
        d = measure_d(year, chpset)
        for k in ("CT_PEAKER", "ST_GAS"):
            print(
                f"  D  {k:<10} all months negative: {d[k]['all_months_negative']}"
                f"  worst m{d[k]['worst_month']}  best m{d[k]['best_month']}"
            )
        e = measure_e(year)
        print(
            f"  E  hydro r {e['hourly_r']:.3f}  cv {e['model_cv']:.3f} vs"
            f" {e['eia930_cv']:.3f}  volume {e['model_twh']:.2f} vs {e['eia930_twh']:.2f} TWh"
        )
        rec["by_year"][str(year)] = {
            "A_class_volume": a,
            "B_ccchp_duration": b,
            "C_ccchp_floor": c,
            "D_monthly_deficit": d,
            "E_hydro_shape": e,
        }

    rec["verdict"] = dict(
        peak_band_proposal_supported_any_year=bool(
            any(
                rec["by_year"][str(y)]["B_ccchp_duration"]["peak_band_proposal_supported"]
                for y in YEARS
            )
        ),
        note=(
            "The CC_CHP over-run is concentrated at the BOTTOM of the class's own "
            "duration curve and the model sits at or below measured at the TOP in "
            "every year, so the duct-burner (peak) offer band cannot be its "
            "carrier. The signature is a floor / minimum-load object."
        ),
    )
    print(
        "\n  PEAK-BAND PROPOSAL SUPPORTED IN ANY YEAR:"
        f" {rec['verdict']['peak_band_proposal_supported_any_year']}"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
