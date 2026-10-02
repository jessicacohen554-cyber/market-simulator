"""NWPP-NEXT-20 phase 0 (zero LP): are NWPP's three priced seams solve-ready?

Four model-free tests, all on committed / fetched measured data plus keeper #20's per-year
``system.parquet`` (extracted from its leg commits by full SHA, see the FINDING):

A. SPP-51 P0-b, copied verbatim as a method (rule 28(d)): flow follows spread. Measured
   counterparty price minus the measured NWPP-side WEIM ELAP of the reporting BA, hurdle =
   the seam's registered hurdle, sign vs the measured EIA-930 per-DIBA leg (export-positive).
   Gate >= 0.55 sign agreement over non-hold hours.
B. WECC_CAN anchor: BCHA's WEIM ELAP (``ELAP_BCHA-APND``, BC Hydro / Powerex, outside the
   footprint) as the all-hours counterparty price, against the registered Mid-C Peak proxy.
C. Wheel exposure: hours in which two seams' reference prices differ by more than the two
   hurdles (at d1aa1dce every seam shared one pooled bus; at this commit only seams sharing an
   internal border zone can arbitrage, through that zone).
D. Price-taker seam flows: the flow-responsive tranches (``seam_tranche_prices``) against keeper
   #20's border-zone prices, per seam, every year 2019-2025, vs the measured legs.

Sections A and B read only measured data. Sections C and D read the registry: at main
``d1aa1dce`` (NEXT-19's three seams on one pooled bus) they printed the "registered" tables of
FINDING §C/§D (``--next19``-era output kept verbatim in the FINDING); at this commit they read the
NEXT-20 registry (CAISO_COI / CAISO_NEVP / WECC_CAN, one zone each).

Usage: python scripts/probes/_nwppnext20_seam_phase0.py LEG_ROOT [BCHA_HOURLY_PARQUET]
(default: data/raw/nwpp-weim/weim_hourly_counterparty.parquet)
"""

from __future__ import annotations

import dataclasses
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts/data")

import build_nwpp_weim_price_index as weim  # noqa: E402

from market_sim.config.interchange_config import INTERFACE_NEIGHBORS  # noqa: E402
from market_sim.data.neighbor_price import (  # noqa: E402
    neighbor_gas_price,
    neighbor_reference_price,
    seam_tranche_prices,
)

RAW = Path("data/raw")
XDIR = RAW / "eia-930-interchange"
YEARS = tuple(range(2019, 2026))
MEAS_YEARS = (2023, 2024, 2025)
FOOTPRINT = (
    "AVA AVRN BPAT CHPD DOPD GCPD GRID IPCO NEVP NWMT PACE PACW PGE PSEI SCL TPWR WAUW"
).split()
MOUNTAIN = {"IPCO", "NWMT", "PACE", "WAUW"}
CAN = {"BCHA", "AESO"}
SEAMS = {n.name: n for n in INTERFACE_NEIGHBORS["NWPP"]}


def _clock(df: pd.DataFrame, tz: str, year: int) -> np.ndarray:
    """EIA-930 hour-ending local rows -> dense 8760 on the fixed-PST hour-beginning model clock."""
    loc = pd.DatetimeIndex(df.local_time).tz_localize(
        tz, ambiguous="NaT", nonexistent="NaT"
    )
    ok = ~loc.isna()
    utc = loc[ok].tz_convert("UTC") - pd.Timedelta(hours=1)
    s = pd.DataFrame({"hour_utc": utc, "v": df.mw.to_numpy(float)[ok]})
    return weim.to_model_clock(s, "v", year)


def legs(year: int) -> dict[str, np.ndarray]:
    """Measured per-seam net export (MW, export-positive) from the footprint BAs' own DIBA rows."""
    out: dict[str, np.ndarray] = {}
    if year in MEAS_YEARS:
        acc = {"CAISO": [], "WECC_CAN": [], "WECC_SW": []}
        for ba in FOOTPRINT:
            d = pd.read_parquet(XDIR / f"{ba} interchange hourly.parquet")
            d["diba"] = d.diba.astype(str)
            tz = "America/Denver" if ba in MOUNTAIN else "America/Los_Angeles"
            for diba, g in d[~d.diba.isin(FOOTPRINT)].groupby("diba"):
                seam = (
                    "CAISO" if diba == "CISO" else "WECC_CAN" if diba in CAN else "WECC_SW"
                )
                acc[seam].append(_clock(g, tz, year))
                out[f"{ba}->{diba}"] = acc[seam][-1]
        for k, v in acc.items():
            out[k] = np.nansum(np.vstack(v), axis=0)
    # CAISO's own report of the same three legs (sign flipped), the only per-seam record pre-2023.
    c = pd.read_parquet(XDIR / "CISO interchange hourly.parquet")
    c = c[c.diba.astype(str).isin(["BPAT", "NEVP", "PACW"])]
    out["CAISO_by_CISO"] = -np.nansum(
        np.vstack(
            [_clock(g, "America/Los_Angeles", year) for _, g in c.groupby("diba", observed=True)]
        ),
        axis=0,
    )
    return out


def _weim(year: int, ba: str, bcha: pd.DataFrame) -> np.ndarray:
    w = bcha if ba == "BCHA" else pd.read_parquet(RAW / "nwpp-weim/weim_hourly_by_ba.parquet")
    return (
        w[(w.year == year) & (w.baa == ba)].set_index("hour").lmp.reindex(range(8760)).values
    )


def _hub(year: int, hub: str) -> np.ndarray:
    m = pd.read_parquet(RAW / "_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet")
    return m[(m.year == year) & (m.hub == hub)].set_index("hour").price.reindex(range(8760)).values


def p0b(bcha: pd.DataFrame) -> None:
    """A: the SPP-51 P0-b statistic per measured leg, 2023 Jun-Dec / 2024 / 2025."""
    print("\n## A. SPP-51 P0-b on the measured record: does the measured flow follow the measured spread?")
    rt = pd.read_parquet(RAW / "_validation-source/actual_lmp_hourly_CAISO.parquet")
    rows = []
    for y in MEAS_YEARS:
        L = legs(y)
        cases = [
            ("CAISO", "BPAT->CISO", _hub(y, "MALIN"), "BPAT", 3.0),
            ("CAISO", "PACW->CISO", _hub(y, "MALIN"), "PACW", 3.0),
            ("CAISO", "NEVP->CISO", rt[rt.year == y].set_index("hour").rt.reindex(range(8760)).values, "NEVP", 3.0),
            ("WECC_CAN", "BPAT->BCHA", _weim(y, "BCHA", bcha), "BPAT", 2.0),
            ("WECC_SW", "NEVP->LDWP", _hub(y, "PALOVRDE"), "NEVP", 2.0),
            ("WECC_SW", "BPAT->LDWP", _hub(y, "PALOVRDE"), "BPAT", 2.0),
            ("WECC_SW", "PACE->WACM", _hub(y, "PALOVRDE"), "PACE", 2.0),
        ]
        for seam, leg, p_nb, ba, hurdle in cases:
            f = L.get(leg)
            if f is None:
                continue
            spread = p_nb - _weim(y, ba, bcha)  # > 0: neighbour dearer -> NWPP should export
            x = pd.DataFrame({"s": spread, "f": f}).dropna()
            x = x[x.f != 0]
            nh = x[x.s.abs() > hurdle]
            rows.append(
                dict(
                    year=y,
                    seam=seam,
                    leg=leg,
                    hours=len(x),
                    mean_spread=x.s.mean(),
                    hold=1 - len(nh) / len(x),
                    agree_nonhold=(np.sign(nh.s) == np.sign(nh.f)).mean(),
                    export_share=(x.f > 0).mean(),
                    agree_if_always_export=(nh.s > 0).mean(),
                    corr=x.s.corr(x.f),
                )
            )
    print(pd.DataFrame(rows).round(3).to_string(index=False))


def anchor(bcha: pd.DataFrame) -> dict[int, float]:
    """B: the WECC_CAN anchor, BCHA ELAP vs the registered Mid-C Peak proxy, and the HR it implies."""
    print("\n## B. WECC_CAN anchor: BCHA WEIM ELAP (all hours) vs registered Mid-C Peak proxy")
    spec = SEAMS["WECC_CAN"]  # gas basis only; the anchor is recomputed here from the measured price
    hr = {}
    for y in MEAS_YEARS:
        b = _weim(y, "BCHA", bcha)
        bp = _weim(y, "BPAT", bcha)
        gas = neighbor_gas_price(spec, y)
        n = int(np.isfinite(b).sum())
        hr[y] = round(float(np.nanmean(b)) / gas, 2)
        both = np.isfinite(b) & np.isfinite(bp)
        print(
            f"{y}: BCHA hours {n}, mean {np.nanmean(b):.2f} (BPAT same hours {np.nanmean(bp[both]):.2f}, "
            f"r {np.corrcoef(b[both], bp[both])[0, 1]:.3f}); gas (HH+basis) {gas:.3f} -> HR {hr[y]:.2f} "
            f"| registered Mid-C Peak HR {spec.hr_by_year.get(y)}"
        )
    print(f"structural (mean) HR {np.mean(list(hr.values())):.2f} vs registered flat {spec.marginal_heat_rate}")
    return hr


def wheel(seams: dict) -> None:
    """C: hours where two seams landing in one internal zone can arbitrage each other through it."""
    print("\n## C. Same-zone seam arbitrage: hours with |P_i - P_j| > h_i + h_j for seams sharing a border zone")
    names = list(seams)
    rows = []
    for y in YEARS:
        p = {k: neighbor_reference_price(v, y, 8760)[0] for k, v in seams.items()}
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                if not set(seams[a].border_zones) & set(seams[b].border_zones):
                    continue
                d = p[a] - p[b]
                band = seams[a].hurdle + seams[b].hurdle
                rows.append(
                    dict(year=y, pair=f"{a}|{b}", hours=int((np.abs(d) > band).sum()),
                         b_dearer=int((d < -band).sum()), mean_spread_b_minus_a=round(float(-d.mean()), 1))
                )
    print(pd.DataFrame(rows).to_string(index=False))


def _measured(year: int) -> dict[str, np.ndarray]:
    """Each priced seam's measured legs on the model clock (export-positive), via the solve's own reader."""
    from market_sim.config.interchange_config import NWPP_PRICED_SEAM_LEGS
    from market_sim.data.eia930.envelopes import _diba_legs_export
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    utc = pd.DatetimeIndex(_eia_hourly_frame_filled("NWPP", year)["UTC time"])
    return {
        seam: sum(_diba_legs_export(r, d, sgn, utc)[0] for r, d, sgn in legs)
        for seam, legs in NWPP_PRICED_SEAM_LEGS.items()
    }


def price_taker(root: Path, seams: dict) -> None:
    """D: per-seam flow if each band clears against keeper #20's border-zone price; vs measured."""
    print("\n## D. Price-taker seam flows vs keeper #20 price (registry at this commit), TWh export-positive")
    rows = []
    for y in YEARS:
        s = pd.read_parquet(root / f"results/calibration/nwppnext16c_{y}/system.parquet")
        s = s[s["pass"] == s["pass"].max()] if "pass" in s else s
        zp = s.pivot_table(index="hour", columns="zone", values="price").reindex(range(8760))
        meas_all = _measured(y)
        for name, spec in seams.items():
            ex, im, _ = seam_tranche_prices(spec, y, 8760)
            bz = zp[list(spec.border_zones)].to_numpy()
            lo, hi = bz.min(axis=1), bz.max(axis=1)
            step = spec.interface_limit_mw / ex.shape[0]
            exp = ((ex - spec.hurdle) > lo[None, :]).sum(axis=0) * step
            imp = ((im + spec.hurdle) < hi[None, :]).sum(axis=0) * step
            net = exp - imp
            meas = meas_all[name]
            rows.append(
                dict(
                    year=y,
                    seam=name,
                    ref_mean=round(float(neighbor_reference_price(spec, y, 8760)[0].mean()), 1),
                    nwpp_border_mean=round(float(np.nanmean(lo)), 1),
                    pt_net_TWh=round(net.sum() / 1e6, 2),
                    pt_export_h=int((net > 0).sum()),
                    pt_at_export_limit_h=int((exp >= spec.interface_limit_mw - 1e-6).sum()),
                    meas_net_TWh=round(float(meas.sum()) / 1e6, 2),
                    meas_export_h=int((meas > 0).sum()),
                    r_hourly=round(float(pd.Series(net).corr(pd.Series(meas))), 3),
                )
            )
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\nsum of priced seams (TWh): price-taker", df.groupby("year").pt_net_TWh.sum().round(2).to_dict(),
          "| measured", df.groupby("year").meas_net_TWh.sum().round(2).to_dict())


def main() -> None:
    """Run A-D."""
    root = Path(sys.argv[1])
    bcha_path = Path(sys.argv[2]) if len(sys.argv) > 2 else RAW / "nwpp-weim/weim_hourly_counterparty.parquet"
    bcha = pd.read_parquet(bcha_path)
    p0b(bcha)
    anchor(bcha)
    wheel(SEAMS)
    price_taker(root, SEAMS)


if __name__ == "__main__":
    main()
