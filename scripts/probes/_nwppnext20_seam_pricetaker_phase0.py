"""NWPP-NEXT-20 phase 0 (zero LP): the fixed NWPP seams as a price-taker against keeper #20.

For each registered NWPP seam (``INTERFACE_NEIGHBORS["NWPP"]``, after the NEXT-20 fixes: CAISO on
CISO net load, WECC_CAN anchored on BC Hydro's own WEIM ELAP price) and for the pre-fix forms,
every flow tranche is cleared against keeper #20's P1 zonal price (mean over the seam's border
zones): export tranche k flows when its price less the hurdle exceeds the NWPP price, import
tranche k when its price plus the hurdle is below it. This is the LP's seam with NWPP's own price
held fixed — an upper bound on the seam's reach, not a forecast of the armed solve (the armed LP
moves NWPP's price toward the seam and self-limits).

Measured counterpart: the per-counterparty EIA-930 interchange of the 17 member BAs
(``data/raw/eia-930-interchange/<BA> interchange hourly.parquet``, 2023-2025, + = the member
exports), internal pairs dropped, external DIBAs mapped to the three seams by the registry's
counterparty sets (CISO -> CAISO; BCHA, AESO -> WECC_CAN; everything else -> WECC_SW).

Also prints the BC Hydro ELAP anchor derivation (``bcha_anchor_heat_rates``) and every seam's
reference-price annual mean for 2019-2025. Reads committed files only.

Usage: python scripts/probes/_nwppnext20_seam_pricetaker_phase0.py
"""

from __future__ import annotations

import dataclasses
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.interchange_config import INTERFACE_NEIGHBORS  # noqa: E402
from market_sim.data.fleet.models import NWPP_BAS  # noqa: E402
from market_sim.data.neighbor_price import (  # noqa: E402
    neighbor_reference_price,
    seam_tranche_prices,
)
from scripts.data.fetch_nwpp_bcha_elap import bcha_anchor_heat_rates  # noqa: E402

warnings.filterwarnings("ignore")

BUNDLE = REPO / "results/calibration/nwppnext16c_span/hourly"
INTERCHANGE = REPO / "data/raw/eia-930-interchange"
WEIM = REPO / "data/raw/nwpp-weim/weim_hourly_by_ba.parquet"
YEARS = (2023, 2024, 2025)
CAN_DIBAS = {"BCHA", "AESO"}
#: The pre-NEXT-20 WECC_CAN anchor (Mid-C Peak ICE / (HH + basis)), for the before/after table.
_MIDC_PEAK_HR = {2023: 37.11, 2024: 30.73, 2025: 13.90}
_MIDC_PEAK_FLAT = 27.25


def _seams() -> dict[str, dict[str, object]]:
    """Return {seam: {"fixed": registered, "prior": pre-NEXT-20 form}}."""
    out: dict[str, dict[str, object]] = {}
    for n in INTERFACE_NEIGHBORS["NWPP"]:
        if n.name == "CAISO":
            prior = dataclasses.replace(n, load_shape_kind="gross")
        elif n.name == "WECC_CAN":
            prior = dataclasses.replace(
                n, marginal_heat_rate=_MIDC_PEAK_FLAT, hr_by_year=dict(_MIDC_PEAK_HR)
            )
        else:
            prior = n
        out[n.name] = {"fixed": n, "prior": prior}
    return out


def _zone_price(year: int) -> pd.DataFrame:
    """Return keeper #20's P1 price, hours x zones."""
    s = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return s.pivot(index="hour", columns="zone", values="price").sort_index()


def price_taker(neighbor, year: int, zp: pd.DataFrame) -> tuple[float, float, float]:
    """Return (export TWh, import TWh, net export TWh) of the price-taker seam."""
    ex, im, _ba = seam_tranche_prices(neighbor, year, 8760)
    p = zp[list(neighbor.border_zones)].mean(axis=1).to_numpy()
    step = neighbor.interface_limit_mw / ex.shape[0]
    exp_mwh = ((ex - neighbor.hurdle) > p[None, :]).sum() * step
    imp_mwh = ((im + neighbor.hurdle) < p[None, :]).sum() * step
    return exp_mwh / 1e6, imp_mwh / 1e6, (exp_mwh - imp_mwh) / 1e6


def measured_by_seam(year: int) -> dict[str, float]:
    """Return measured net export TWh per seam (+ = the footprint exports)."""
    members = set(NWPP_BAS)
    acc = {"CAISO": 0.0, "WECC_SW": 0.0, "WECC_CAN": 0.0}
    for ba in NWPP_BAS:
        f = INTERCHANGE / f"{ba} interchange hourly.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(f)
        d = d[pd.to_datetime(d["local_time"]).dt.year == year]
        d = d[~d["diba"].astype(str).isin(members)]
        for diba, mw in d.groupby(d["diba"].astype(str))["mw"].sum().items():
            seam = (
                "CAISO"
                if diba == "CISO"
                else "WECC_CAN"
                if diba in CAN_DIBAS
                else "WECC_SW"
            )
            acc[seam] += float(mw) / 1e6
    return acc


def main() -> None:
    """Print every table of the NEXT-20 phase-0 FINDING."""
    print("## A. BC Hydro ELAP anchor (matched-window HR)")
    print(bcha_anchor_heat_rates().round(3).to_string())
    seams = _seams()
    print("\n## B. Seam reference price annual mean $/MWh (prior -> fixed)")
    w = pd.read_parquet(WEIM)
    for y in range(2019, 2026):
        cells = []
        for k, v in seams.items():
            a = neighbor_reference_price(v["prior"], y, 8760)[0].mean()
            b = neighbor_reference_price(v["fixed"], y, 8760)[0].mean()
            cells.append(f"{k} {a:.1f}->{b:.1f}")
        meas = ""
        if y in YEARS:
            m = w[w.year == y].groupby("baa").lmp.mean()
            meas = " | WEIM " + ", ".join(
                f"{b} {m[b]:.1f}" for b in ("BPAT", "PACE", "IPCO")
            )
        print(f"{y}: " + ", ".join(cells) + meas)
    print(
        "\n## C. Price-taker vs keeper #20 P1 zonal price, TWh (export / import / net export)"
    )
    rows = []
    for y in YEARS:
        zp = _zone_price(y)
        meas = measured_by_seam(y)
        for k, v in seams.items():
            pe, pi, pn = price_taker(v["prior"], y, zp)
            fe, fi, fn = price_taker(v["fixed"], y, zp)
            rows.append(
                dict(
                    year=y,
                    seam=k,
                    prior_exp=pe,
                    prior_imp=pi,
                    prior_net=pn,
                    fixed_exp=fe,
                    fixed_imp=fi,
                    fixed_net=fn,
                    measured_net=meas[k],
                )
            )
    t = pd.DataFrame(rows)
    print(t.round(2).to_string(index=False))
    tot = t.groupby("year")[["prior_net", "fixed_net", "measured_net"]].sum()
    print("\nfootprint net export, TWh:\n" + tot.round(2).to_string())
    print("\n## D. 2019-2022 fallback heat rates (flat marginal_heat_rate)")
    for k, v in seams.items():
        print(f"{k}: {v['fixed'].marginal_heat_rate}")


if __name__ == "__main__":
    np.set_printoptions(suppress=True)
    main()
