#!/usr/bin/env python3
"""Derive each PJM neighbor's price-vs-load convexity from its OWN realized LMP.

The reference-price seam prices each neighbor at
``gas x heat_rate x (load[h] / mean_load) ** load_shape_exponent`` and the
flow-responsive tranches (``neighbor_price.seam_tranche_prices``) slide that
price up/down the neighbor's own load axis as the ISO imports/exports. With
``load_shape_exponent = 1.0`` (price linear in load) the slope is too gentle:
displacing a ≤7.3 GW seam flow against a ~75 GW neighbor moves its price only a
few percent, not enough to close the structural PJM-vs-neighbor spread, so the
export pins near the interface cap (the ``pjm_31`` residual). A real marginal
supply curve is **convex** — price rises steeply as the fleet nears its top —
so the exponent should be > 1.

This script recovers that exponent as a *measured market quantity* (claude.md
rule #11), never tuned to PJM's net-MWh target: it regresses the neighbor's
realized hourly real-time LMP on its own EIA-930 load in log-log space,

    log(LMP[h]) = a + b * log(load[h] / mean_load) + e ,

so the slope ``b`` is exactly the ``load_shape_exponent`` that reproduces the
neighbor's own price–load elasticity. The level (intercept) is left to the
existing ``marginal_heat_rate`` gas anchor; only the *shape* steepness ``b`` is
taken from here. The exponent is dimensionless and regenerable for a forward
year, so it stays forecast-native.

Two regressors are reported per neighbor:

* **gross** load (EIA-930 ``Demand``) — the series the model actually multiplies
  in :func:`~market_sim.data.neighbor_price.seam_tranche_prices`, so this is the
  *model-consistent* exponent and the one wired into the registry.
* **net** load (``Demand - Wind - Solar``) — the physically purer residual
  thermal demand, reported as a diagnostic. For a low-renewables neighbor
  (NYISO) gross ≈ net; for a solar/wind-heavy market the two diverge sharply
  (CAISO gross convexity collapses because solar decouples price from gross
  load), which is *why* the model uses gross only where renewables are small.

DATA AVAILABILITY (the binding constraint): a realized hourly LMP extract is
shipped only for the organized markets ERCOT / PJM / CAISO / NYISO / NEISO
(``inputs/calibration/actual_lmp_hourly_<ISO>.parquet``). Of PJM's three
neighbors that means **only NYISO** can have its convexity self-derived here.
MISO publishes LMP but no extract is in the repo, and the Carolinas/Southeast
is not an organized market (no LMP at all). Those two are reported as
``no realized LMP`` and their exponent must be sourced by decision (see the
module's caller / the registry comment), not silently invented.

Cross-check markets (CAISO; ERCOT/NEISO if their hourly extract is present) are
regressed too — not PJM neighbors, but they show the price–load convexity is a
real, stable, market-wide structural quantity rather than a NYISO artifact.

Run from the repo root::

    python scripts/derive_neighbor_convexity.py
    python scripts/derive_neighbor_convexity.py --check   # assert constants match
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from market_sim.config.constants import INTERFACE_NEIGHBORS
from market_sim.data.eia_loader import _eia_hourly_frame_filled

# PJM neighbor name -> realized-LMP parquet key (the
# inputs/calibration/actual_lmp_hourly_<KEY>.parquet stem). NYISO ships in the
# repo; MISO (Indiana Hub ex-post LMP) and Carolinas (Duke FERC-714 system
# lambda) are fetched by scripts/fetch_neighbor_lmp.py via the
# fetch-neighbor-lmp workflow. A neighbor whose parquet is absent is reported
# "no realized LMP" rather than silently invented.
NEIGHBOR_LMP_KEY: dict[str, str] = {
    "NYISO": "NYISO",
    "MISO": "MISO",
    "Carolinas": "Carolinas",
}

# Non-neighbor organized markets regressed as structural cross-checks (each has
# both a realized-LMP extract and a load shape), to show price-vs-load convexity
# is a market-wide property and not specific to NYISO.
CROSSCHECK: dict[str, str] = {
    "CAISO": "CISO",
    "ERCOT": "ERCO",
    "NEISO": "ISNE",
}

YEARS = (2023, 2024, 2025)

# Exponents this script derives, committed to INTERFACE_NEIGHBORS["PJM"]. Kept
# here so --check can assert the registry still matches the regression after a
# data refresh. Filled in once the derivation + sourcing decision is settled.
# NYISO is the only PJM neighbor with a realized-LMP extract in the repo, so it
# is the only one whose exponent is self-derived and guarded here. MISO and the
# Carolinas adopt this same value as the organized-thermal-neighbor convexity
# (see INTERFACE_NEIGHBORS comment) until their own LMP is fetched; they are not
# listed here because --check can only assert a SELF-derived value.
COMMITTED_EXPONENT: dict[str, float] = {"NYISO": 1.63}


def _realized_rt_lmp(lmp_key: str, year: int) -> np.ndarray | None:
    """Return the realized hourly real-time LMP for ``lmp_key`` in ``year``.

    The ``actual_lmp_hourly_<KEY>.parquet`` extract is indexed by ``year`` and
    ``hour`` (0..8759, the model's local-hour-of-year clock), so the returned
    series aligns row-for-row with :func:`_neighbor_load`. Returns ``None`` when
    the extract or the year is absent.
    """
    from market_sim.config.paths import CALIBRATION_DIR

    path = CALIBRATION_DIR / f"actual_lmp_hourly_{lmp_key}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    sub = df[df["year"] == year]
    if sub.empty:
        return None
    return sub.sort_values("hour")["rt"].to_numpy(dtype=float)


def _gross_net_load(
    ba_code: str, proxy_ba: str | None, year: int
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return ``(gross, net)`` hourly load (MW) for the BA (or its proxy).

    ``gross`` is the EIA-930 ``Demand`` series the model multiplies; ``net`` is
    ``Demand - Wind - Solar`` (the residual thermal demand) where the renewable
    columns are present, else equal to gross. ``None`` when no load resolves.
    """
    for ba in (ba_code, proxy_ba):
        if ba is None:
            continue
        frame = _eia_hourly_frame_filled(ba, year)
        if frame is None or "Demand" not in frame.columns:
            continue
        gross = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
        wnd = (
            frame["NG: WND"].fillna(0.0).to_numpy(dtype=float)
            if "NG: WND" in frame.columns
            else np.zeros_like(gross)
        )
        sun = (
            frame["NG: SUN"].fillna(0.0).to_numpy(dtype=float)
            if "NG: SUN" in frame.columns
            else np.zeros_like(gross)
        )
        net = np.clip(gross - wnd - sun, 1.0, None)
        return gross, net
    return None


def _loglog_xy(
    load: np.ndarray, lmp: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return the cleaned ``(log(load/mean), log(lmp))`` regression pair.

    Hours with a non-positive LMP (negative-price / log-undefined) or a missing
    / non-positive load are dropped, so the same filtering is reused by the
    per-year and pooled fits.
    """
    mask = (lmp > 1.0) & np.isfinite(lmp) & np.isfinite(load) & (load > 1.0)
    return np.log(load[mask] / load[mask].mean()), np.log(lmp[mask])


def _fit_xy(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return ``(exponent, R2)`` of the OLS ``y ~ a + b*x``.

    ``b`` is the price–load elasticity = the ``load_shape_exponent`` that
    reproduces the realized shape.
    """
    design = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ coef
    r2 = 1.0 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    return float(coef[0]), float(r2)


def _derive_one(
    lmp_key: str, ba_code: str, proxy_ba: str | None
) -> dict | None:
    """Regress one market's realized LMP on its load, per year and pooled.

    Returns a dict with per-year and pooled gross/net exponents, or ``None``
    when no year yields both a realized LMP and a load shape.
    """
    rows: list[dict] = []
    gx: list[np.ndarray] = []
    gy: list[np.ndarray] = []
    nx: list[np.ndarray] = []
    ny: list[np.ndarray] = []
    for year in YEARS:
        lmp = _realized_rt_lmp(lmp_key, year)
        loads = _gross_net_load(ba_code, proxy_ba, year)
        if lmp is None or loads is None:
            continue
        gross, net = loads
        n = min(len(lmp), len(gross))
        lmp, gross, net = lmp[:n], gross[:n], net[:n]
        xg, yg = _loglog_xy(gross, lmp)
        xn, yn = _loglog_xy(net, lmp)
        eg, rg = _fit_xy(xg, yg)
        en, rn = _fit_xy(xn, yn)
        rows.append(
            {
                "year": year,
                "exp_gross": eg,
                "r2_gross": rg,
                "exp_net": en,
                "r2_net": rn,
                "mean_lmp": float(np.exp(yg).mean()),
                "n": len(yg),
            }
        )
        gx.append(xg)
        gy.append(yg)
        nx.append(xn)
        ny.append(yn)
    if not rows:
        return None

    def _pool(xs: list[np.ndarray], ys: list[np.ndarray]) -> tuple[float, float]:
        return _fit_xy(np.concatenate(xs), np.concatenate(ys))

    pooled_gross = _pool(gx, gy)
    pooled_net = _pool(nx, ny)
    return {"rows": rows, "pooled_gross": pooled_gross, "pooled_net": pooled_net}


def _report(title: str, name: str, lmp_key: str, ba: str, proxy: str | None) -> dict | None:
    res = _derive_one(lmp_key, ba, proxy)
    print(f"\n{title}: {name}  (LMP={lmp_key}, load={ba}"
          f"{'' if proxy is None else f'/{proxy}'})")
    if res is None:
        print("  no realized LMP + load overlap — exponent not self-derivable")
        return None
    print(f"  {'year':>5s} {'exp_gross':>9s} {'R2g':>5s} "
          f"{'exp_net':>8s} {'R2n':>5s} {'meanLMP':>8s} {'n':>6s}")
    for r in res["rows"]:
        print(f"  {r['year']:>5d} {r['exp_gross']:9.2f} {r['r2_gross']:5.2f} "
              f"{r['exp_net']:8.2f} {r['r2_net']:5.2f} {r['mean_lmp']:8.1f} "
              f"{r['n']:6d}")
    pg, pgr = res["pooled_gross"]
    pn, pnr = res["pooled_net"]
    print(f"  POOLED  gross exp={pg:.2f} (R2={pgr:.2f}) | "
          f"net exp={pn:.2f} (R2={pnr:.2f})")
    return res


def derive() -> dict[str, float]:
    """Print the convexity table and return the derived gross exponents."""
    derived: dict[str, float] = {}
    print("Neighbor price-vs-load convexity from realized RT LMP "
          f"(log-log, pooled {YEARS}):")

    for neighbor in INTERFACE_NEIGHBORS.get("PJM", []):
        key = NEIGHBOR_LMP_KEY.get(neighbor.name)
        if key is None:
            print(f"\nNEIGHBOR: {neighbor.name}  (load={neighbor.ba_code}"
                  f"{'' if neighbor.proxy_ba is None else f'/{neighbor.proxy_ba}'})")
            print("  no realized LMP extract in repo — exponent not "
                  "self-derivable (source by decision)")
            continue
        res = _report("NEIGHBOR", neighbor.name, key,
                      neighbor.ba_code, neighbor.proxy_ba)
        if res is not None:
            derived[neighbor.name] = round(res["pooled_gross"][0], 2)

    for iso, ba in CROSSCHECK.items():
        _report("CROSS-CHECK", iso, iso, ba, None)

    return derived


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="assert the committed exponents match the data")
    args = ap.parse_args()

    derived = derive()

    if args.check:
        if not COMMITTED_EXPONENT:
            print("\n(no COMMITTED_EXPONENT yet — nothing to check)")
            return
        bad = {n: (derived.get(n), COMMITTED_EXPONENT[n])
               for n in COMMITTED_EXPONENT
               if derived.get(n) != COMMITTED_EXPONENT[n]}
        if bad:
            raise SystemExit(
                f"neighbor exponents drifted from committed constants: {bad}")
        print("\nOK: derived exponents match COMMITTED_EXPONENT.")


if __name__ == "__main__":
    main()
