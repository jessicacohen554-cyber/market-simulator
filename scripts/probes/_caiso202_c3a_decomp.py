"""caiso-202 lane 1 — C3a 2024/2025 mean-LMP overrun decomposition on the
caiso-200 keeper (`2026-08-17-caiso-200-h1-memberpanel`). NO LP, NO SOLVE —
committed bytes only.

Charter: the caiso-202 owner re-opening (2026-08-18). Questions answered here,
each from the keeper's committed ``hourly/`` sidecars + the committed actual
LMP reference:

* **A** — the month × hod-band residual map for 2024/2025 (2023 control), on
  the rubric's rt_lw weights (the caiso-131 §2 / caiso-140 §A convention:
  cells sum exactly to the printed annual weighted gap).
* **B** — level vs basis: the same map scored against the DA actual. The
  caiso-202 charter's +2.9 % (2024 vs DA) demands the RT−DA basis share of
  the RT-basis overrun be quantified BEFORE any mechanism is touched.
* **C** — the price-state of the overrun: per actual-RT price bucket, the
  weighted contribution — is the overrun sitting on reality's low/negative
  hours (the caiso-140 plateau/export-seam story) or spread across mid-price
  hours (an offer-level story)?
* **D** — the marginal-rung witness: in overrun hours, the CA λ − WECC node λ
  spread (parity-priced ⇒ import tranche marginal, the caiso-140 §C regime
  split re-measured on THIS keeper), plus where CA λ sits against the gas-rung
  band when it is NOT at parity.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso202_c3a_decomp.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso200_h1_memberpanel"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"

DEFECT_MONTHS = (9, 10, 11, 12)
DEFECT_HODS = (10, 11, 12, 13, 14, 15)


def actuals(year: int) -> pd.DataFrame:
    a = pd.read_parquet(ACTUAL_LMP)
    a = a[a["year"] == year].set_index("hour").reindex(range(HOURS))
    return a


def sidecars(year: int) -> dict:
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    price = d.pivot_table(index="hour", columns="zone", values="price")
    demand = d.pivot_table(index="hour", columns="zone", values="demand")
    return {"price": price, "demand": demand}


def ca_lambda(sc: dict) -> np.ndarray:
    ca = [z for z in sc["price"].columns if not str(z).startswith("WECC")]
    p = (sc["price"][ca] * sc["demand"][ca]).sum(axis=1) / sc["demand"][ca].sum(axis=1)
    return p.to_numpy()


def rubric_weights(year: int) -> np.ndarray:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    return np.asarray(load_demand(ISO, year, get_iso_config(ISO))).sum(axis=0)[:HOURS]


def month_of_hour(year: int) -> np.ndarray:
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(HOURS + 24), "h")
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def band_masks(hd: np.ndarray) -> dict:
    return {
        "belly10-15": np.isin(hd, DEFECT_HODS),
        "eve17-21": np.isin(hd, (17, 18, 19, 20, 21)),
        "night0-6": np.isin(hd, (0, 1, 2, 3, 4, 5, 6)),
        "other": ~(
            np.isin(hd, DEFECT_HODS)
            | np.isin(hd, (17, 18, 19, 20, 21))
            | np.isin(hd, (0, 1, 2, 3, 4, 5, 6))
        ),
    }


def weighted_map(lam, act, w, mo, hd, label):
    ok = ~np.isnan(act)
    wsum = w[ok].sum()
    contrib = np.where(ok, w * (lam - np.where(ok, act, 0.0)), 0.0) / wsum
    gap = contrib.sum()
    amean = np.average(act[ok], weights=w[ok])
    mmean = np.average(lam[ok], weights=w[ok])
    print(
        f"\n  [{label}] weighted model {mmean:.2f} vs actual {amean:.2f} "
        f"-> gap {gap:+.2f} $/MWh = {gap / amean * 100:+.1f}%  (n={ok.sum()} h)"
    )
    bands = band_masks(hd)
    hdr = "".join(f"{b:>12}" for b in bands)
    print(f"    {'month':<6}{hdr}{'total':>12}")
    for m in range(1, 13):
        mrow = [float(contrib[(mo == m) & mask].sum()) for mask in bands.values()]
        tot = float(contrib[mo == m].sum())
        flag = " <--" if m in DEFECT_MONTHS else ""
        print(
            f"    {m:<6}" + "".join(f"{v:+12.3f}" for v in mrow) + f"{tot:+12.3f}{flag}"
        )
    band_tot = {b: float(contrib[mask].sum()) for b, mask in bands.items()}
    print(
        f"    {'ALL':<6}"
        + "".join(f"{band_tot[b]:+12.3f}" for b in bands)
        + f"{gap:+12.3f}"
    )
    sepdec = float(contrib[np.isin(mo, DEFECT_MONTHS)].sum())
    print(f"    Sep-Dec {sepdec:+.2f} ({sepdec / gap * 100 if gap else 0:.0f}% of gap)")
    return gap, amean, contrib, ok


def price_buckets(lam, act, w, ok, label):
    """Weighted gap contribution per actual-RT price bucket."""
    edges = [-1e9, 0, 10, 20, 30, 40, 60, 100, 1e9]
    names = ["<0", "0-10", "10-20", "20-30", "30-40", "40-60", "60-100", ">100"]
    wsum = w[ok].sum()
    print(f"\n  [{label}] contribution per ACTUAL price bucket:")
    print(
        f"    {'bucket':>8}{'hours':>7}{'act_mean':>10}{'mod_mean':>10}"
        f"{'gap$':>9}{'share':>8}"
    )
    total = np.sum(w[ok] * (lam[ok] - act[ok])) / wsum
    for lo, hi, nm in zip(edges[:-1], edges[1:], names):
        m = ok & (act >= lo) & (act < hi)
        if m.sum() == 0:
            continue
        g = np.sum(w[m] * (lam[m] - act[m])) / wsum
        print(
            f"    {nm:>8}{m.sum():>7}{np.average(act[m], weights=w[m]):>10.2f}"
            f"{np.average(lam[m], weights=w[m]):>10.2f}{g:>+9.3f}"
            f"{g / total * 100:>7.0f}%"
        )


def parity_witness(sc, lam, act, w, ok, year):
    """Where is CA λ relative to the WECC node λ in the overrun hours?"""
    dsw = sc["price"]["WECC_DSW"].to_numpy()
    pnw = sc["price"]["WECC_PNW"].to_numpy()
    node = np.maximum(dsw, pnw)  # the higher import node is the binding parity
    spread_dsw = lam - dsw
    spread_pnw = lam - pnw
    # overrun-hours = model above actual (contribution-positive), weighted
    over = ok & (lam > act)
    wsum = w[ok].sum()
    contrib = np.where(ok, w * (lam - np.where(ok, act, 0.0)), 0.0) / wsum
    pos = contrib > 0
    at_dsw = np.abs(spread_dsw) < 0.01
    at_pnw = np.abs(spread_pnw) < 0.01
    at_any = at_dsw | at_pnw
    print(f"\n  [{year}] parity witness over POSITIVE-contribution hours:")
    print(
        f"    hours w/ contrib>0: {pos.sum()}  their gap sum "
        f"{contrib[pos].sum():+.2f} (vs neg {contrib[contrib < 0].sum():+.2f})"
    )
    for nm, mask in [
        ("lam == DSW node (|d|<0.01)", at_dsw),
        ("lam == PNW node (|d|<0.01)", at_pnw),
        ("lam == either node", at_any),
        ("lam > both nodes (CA-internal rung)", (spread_dsw > 0.01) & (spread_pnw > 0.01)),
        ("lam < both nodes (export-ish)", (spread_dsw < -0.01) & (spread_pnw < -0.01)),
    ]:
        g = contrib[pos & mask].sum()
        print(
            f"    {nm:<38} {(pos & mask).sum():>5} h  gap {g:+.3f} "
            f"({g / contrib[pos].sum() * 100:.0f}% of positive)"
        )
    # where CA-internal: model lambda level vs actual
    inner = pos & (spread_dsw > 0.01) & (spread_pnw > 0.01)
    if inner.sum():
        print(
            f"    CA-internal-rung hours: model lam p25/50/75 = "
            f"{np.percentile(lam[inner], 25):.1f}/{np.percentile(lam[inner], 50):.1f}/"
            f"{np.percentile(lam[inner], 75):.1f}  actual = "
            f"{np.percentile(act[inner], 25):.1f}/{np.percentile(act[inner], 50):.1f}/"
            f"{np.percentile(act[inner], 75):.1f}"
        )
    # node price levels themselves in positive hours
    print(
        f"    node lam in contrib>0 hours: DSW p50 {np.percentile(dsw[pos], 50):.2f}, "
        f"PNW p50 {np.percentile(pnw[pos], 50):.2f}"
    )


def main() -> None:
    for year in YEARS:
        print("=" * 78)
        print(f"YEAR {year}")
        print("=" * 78)
        sc = sidecars(year)
        lam = ca_lambda(sc)
        a = actuals(year)
        rt = a["rt"].to_numpy()
        da = a["da"].to_numpy()
        w = rubric_weights(year)
        mo = month_of_hour(year)
        hd = np.arange(HOURS) % 24

        gap_rt, amean_rt, contrib, ok = weighted_map(lam, rt, w, mo, hd, "vs RT")
        gap_da, amean_da, _, okd = weighted_map(lam, da, w, mo, hd, "vs DA")
        basis = np.nansum(
            np.where(ok & okd, w * (da - rt), 0.0)
        ) / w[ok].sum()
        print(
            f"\n  LEVEL-vs-BASIS: RT-basis gap {gap_rt:+.2f} "
            f"({gap_rt / amean_rt * 100:+.1f}%), DA-basis gap {gap_da:+.2f} "
            f"({gap_da / amean_da * 100:+.1f}%), weighted DA-RT basis "
            f"{basis:+.2f} $/MWh"
        )
        price_buckets(lam, rt, w, ok, f"{year} vs RT")
        parity_witness(sc, lam, rt, w, ok, year)


if __name__ == "__main__":
    main()
