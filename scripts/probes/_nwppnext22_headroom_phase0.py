"""NWPP-NEXT-22 phase 0 (zero LP): how much seam headroom did the market actually have?

NEXT-21 priced NWPP's seams at their full path ratings (COI 4,800, NEVP 1,933,
BC 3,150 MW) and exported 2-8x measured. This probe reads only measured data,
the committed registry, and keeper #20's per-year ``system_<Y>.parquet``:

A. CAISO's share of COI: CAISO OASIS hourly OTC on MALIN500_ISL + CASCADE_ITC
   over BPA's whole-path COI operating limit, per direction, 2023-2025.
B. Which CAISO ITC carries each priced CAISO leg: hourly correlation of each
   ITC's DAM schedule (``ENE_IMPORT_MW``, a diagnostic only, never an input)
   with the measured EIA-930 CISO<->BPAT / PACW / NEVP leg.
C. Crosswalk: BPA's path actual loading against the measured seam legs.
D. Price-taker seam flows against keeper #20's border-zone price
   (NEXT-20 FINDING §D construction): registered ratings vs the measured caps
   of ``nwpp_seam_limits_hourly`` vs actual.
E. NEXT-21's realized seam flows clipped at the measured caps, prices held
   (optional: pass a directory holding ``flows21_<Y>.parquet`` extracted from
   the NEXT-21 legs by full SHA).

Usage: PYTHONPATH=. python scripts/probes/_nwppnext22_headroom_phase0.py [FLOWS21_DIR]
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts/data")
sys.path.insert(0, "scripts/probes")

from _nwppnext20_seam_phase0 import SEAMS, _measured  # noqa: E402

from market_sim.config.constants import NWPP_COI_PATH_SERIES  # noqa: E402
from market_sim.data.eia930.envelopes import _diba_legs_export  # noqa: E402
from market_sim.data.neighbor_price import seam_tranche_prices  # noqa: E402
from market_sim.data.transfer_interface_limits import (  # noqa: E402
    _nwpp_cap_series,
    load_interface_hourly,
    nwpp_seam_limits_hourly,
)

YEARS = tuple(range(2019, 2026))
KEEPER = Path("results/calibration/nwppnext16c_span/hourly")
TRNS = Path("data/raw/caiso-trns-usage")


def share() -> None:
    """A: CAISO MALIN+CASCADE OTC / BPA whole-path COI limit, per direction."""
    print("\n## A. CAISO share of COI (CAISO OTC / BPA path operating limit)")
    for y in (2023, 2024, 2025):
        caiso, nwpp = (
            load_interface_hourly("CAISO", y),
            load_interface_hourly("NWPP", y),
        )
        for direction, d in (("export", "I"), ("import", "E")):
            names = (f"MALIN500_ISL|{d}|OTC", f"CASCADE_ITC|{d}|OTC")
            c = _nwpp_cap_series(caiso, names, 1.0, y, 8760, False)
            name, sign = NWPP_COI_PATH_SERIES[direction]
            p = _nwpp_cap_series(nwpp, (name,), sign, y, 8760, True)
            ok = np.isfinite(c) & (p > 0)
            r = c[ok] / p[ok]
            print(
                f"{y} {direction:6s} hours {ok.sum():5d}  ratio median "
                f"{np.median(r):.3f} p10 {np.percentile(r, 10):.3f} p90 "
                f"{np.percentile(r, 90):.3f}  CAISO mean {c[ok].mean():5.0f}  "
                f"BPA mean {p[ok].mean():5.0f}"
            )


def itc_map() -> None:
    """B: top ITC schedule correlations with each measured CAISO leg (2024, 2025)."""
    print(
        "\n## B. CAISO ITC schedule vs measured EIA-930 CISO leg (r, import direction)"
    )
    for y in (2024, 2025):
        w = pd.read_parquet(TRNS / f"caiso_trns_usage_dam_{y}.parquet")
        w = w[w["direction"] == "I"]
        sch = w.pivot_table(
            index=pd.to_datetime(w["interval_start_utc"], utc=True),
            columns="ti_id",
            values="ENE_IMPORT_MW",
            aggfunc="sum",
        )
        he = pd.DatetimeIndex(sch.index + pd.Timedelta(hours=1)).tz_localize(None)
        for diba in (("BPAT", "PACW"), ("NEVP",)):
            leg = pd.Series(
                _diba_legs_export("CISO", diba, -1.0, he)[0], index=sch.index
            )
            r = sch.corrwith(leg).dropna().sort_values(ascending=False).head(4)
            print(
                f"{y} CISO<-{'+'.join(diba):9s} mean {leg.mean():5.0f} MW  top: "
                + ", ".join(f"{k} {v:.2f}" for k, v in r.items())
            )


def crosswalk() -> None:
    """C: BPA path actual loading vs the measured seam legs (annual mean MW)."""
    print("\n## C. BPA actual loading vs measured seam leg (mean MW, export +)")
    for y in YEARS:
        nwpp = load_interface_hourly("NWPP", y)
        coi = nwpp[nwpp["interface"] == "COI|NS|OTC"]["transfer_mw"].mean()
        bc = nwpp[nwpp["interface"] == "BC|SN|OTC"]["transfer_mw"].mean()
        m = _measured(y)
        print(
            f"{y} COI path {coi:6.0f} vs CISO leg {np.nanmean(m['CAISO_COI']):6.0f} | "
            f"BC path {bc:6.0f} vs BPAT-BCHA leg {np.nanmean(m['WECC_CAN']):6.0f}"
        )


def price_taker() -> pd.DataFrame:
    """D: price-taker flows vs keeper #20 price, registered vs measured caps."""
    print(
        "\n## D. Price-taker vs keeper #20 price, TWh export + (registered / measured caps / actual)"
    )
    rows = []
    for y in YEARS:
        s = pd.read_parquet(KEEPER / f"system_{y}.parquet")
        s = s[s["pass"] == s["pass"].max()] if "pass" in s else s
        zp = s.pivot_table(index="hour", columns="zone", values="price").reindex(
            range(8760)
        )
        meas = _measured(y)
        caps = nwpp_seam_limits_hourly(y, 8760)
        for name, spec in SEAMS.items():
            if spec.anchored_years_only and y not in (spec.hr_by_year or {}):
                continue
            ex, im, _ = seam_tranche_prices(spec, y, 8760)
            bz = zp[list(spec.border_zones)].to_numpy()
            lo, hi = bz.min(axis=1), bz.max(axis=1)
            step = spec.interface_limit_mw / ex.shape[0]
            exp = ((ex - spec.hurdle) > lo[None, :]).sum(axis=0) * step
            imp = ((im + spec.hurdle) < hi[None, :]).sum(axis=0) * step
            imp_cap, exp_cap = caps.get(
                name, (np.full(8760, np.inf), np.full(8760, np.inf))
            )
            reg = exp - imp
            cap = np.minimum(exp, exp_cap) - np.minimum(imp, imp_cap)
            rows.append(
                dict(
                    year=y,
                    seam=name,
                    registered=round(reg.sum() / 1e6, 2),
                    measured_caps=round(cap.sum() / 1e6, 2),
                    actual=round(float(np.nansum(meas[name])) / 1e6, 2),
                    export_cap_mean=round(
                        float(np.mean(np.minimum(exp_cap, spec.interface_limit_mw)))
                    ),
                    r_caps=round(float(pd.Series(cap).corr(pd.Series(meas[name]))), 3),
                )
            )
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    tot = df.groupby("year")[["registered", "measured_caps", "actual"]].sum().round(1)
    print("\nsum of priced seams (TWh):\n" + tot.to_string())
    return df


def clip(flows_dir: Path) -> None:
    """E: NEXT-21 realized seam flow clipped at the measured caps, prices held."""
    print("\n## E. NEXT-21 realized seam flow clipped at measured caps (TWh, export +)")
    for y in YEARS:
        path = flows_dir / f"flows21_{y}.parquet"
        if not path.exists():
            continue
        f = pd.read_parquet(path)
        f = f[f["pass"] == f["pass"].max()]
        caps = nwpp_seam_limits_hourly(y, 8760)
        for seam, zone in (("CAISO_COI", "NWPP_ext_COI"), ("WECC_CAN", "NWPP_ext_BC")):
            net = (
                -f[f["from_zone"] == zone]
                .groupby("hour")["mw"]
                .sum()
                .reindex(range(8760))
                .fillna(0.0)
                .to_numpy()
            )
            imp_cap, exp_cap = caps[seam]
            clipped = np.clip(net, -imp_cap, exp_cap)
            print(
                f"{y} {seam:9s} arm {net.sum() / 1e6:6.2f}  clipped {clipped.sum() / 1e6:6.2f}  "
                f"h export>cap {int((net > exp_cap).sum()):5d}  h import>cap {int((-net > imp_cap).sum()):5d}"
            )


def main() -> None:
    """Run A-E."""
    share()
    itc_map()
    crosswalk()
    price_taker()
    if len(sys.argv) > 1:
        clip(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
