"""Derive CAISO WECC-corridor import rung PRICES by measured Q-Q duration coupling.

The CAISO analogue of ``scripts/derive_neiso_import_tranches.py`` (audit C-6 /
gap register G-26 / issue #1350, the caiso-83 lane). Replaces the STATIC-FITTED
``$/MWh`` values in ``interchange_config.IMPORT_TRANCHES["CAISO"]`` /
``IMPORT_TRANCHES_BY_YEAR["CAISO"]`` — Tier-3 contract-cost proxies with no
primary source — with a measured, forward-reproducible derivation.

Methodology — per-corridor Q-Q duration coupling (NEISO precedent)
-----------------------------------------------------------------
For each WECC import corridor (``WECC_PNW`` = COI/Path-66 into NP15, proxy hub
MALIN; ``WECC_DSW`` = Path-46/WOR into SP15, proxy hub PALOVRDE), the rung at
capacity level ``L`` is priced at the DA hub-price quantile whose exceedance
duration equals the measured duration of the corridor net import exceeding ``L``:

    price(L) = quantile( hub_price, 1 - P[ net_import > L ] )

i.e. the corridor's price duration curve and its flow duration curve are paired
quantile-by-quantile (the same anti-monotone coupling the NEISO/MISO/PJM seam
ladders use). Net import = -sum(EIA-930 CISO interchange over the corridor's
DIBAs) on the model clock (``eia_loader._caiso_interchange_model_clock``,
``CAISO_CORRIDOR_DIBA``). Hub prices are the measured Malin/Palo Verde intertie
DA LMPs (``data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet``);
that series has NO Jan/Feb-2023 coverage (the ladder handles those hours by
falling back on the pooled distribution — January price formation is caiso-84's
lane anyway).

Rung capacities follow the existing ladder's corridor breakpoints (the measured
depth-in-surplus evidence, caiso-82 §3: south-corridor p95 4.7/5.4/5.5 GW,
year-stable); only the PRICES are re-derived here.

Estimation-stage honesty gates (caiso-81 precedent — run BEFORE any solve)
-------------------------------------------------------------------------
  * YEAR-STABILITY: each rung's derived price is stable across 2023-2025
    (coefficient of variation ≤ ``CV_MAX``) — a revealed supply curve, not a
    per-year fit.
  * LOYO: derive on two years, predict the held-out year's rung prices; the
    held-out error must stay within ``LOYO_MAX`` (relative). A ladder that only
    reproduces in-sample is overfit and must NOT be solved.

If either gate fails the script prints FAIL and the caller files the FINDING and
does NOT solve (the derive-first discipline). No LP is run here.

Partial-ladder mode (``--partial``, the caiso-86 FINDING §4 disposition): the
full five-rung ladder FAILED the gates solely on DSW_solar_PV (CV 0.99 — the
volatile low-tail solar-glut quantile; FINDING-caiso86-import-ladder-gates-
2026-07-15 §3). ``--partial`` scores the gates on the four structurally-stable
rungs only (PNW_hydro_base, PNW_midC, DSW_CCGT, DSW_CT); DSW_solar_PV is still
derived and printed for the record but EXCLUDED from gating because in the
partial design it keeps its existing static value as an explicitly-labelled
price-taker floor rather than taking a derived price. A partial-mode PASS
admits ONLY the four-rung measured swap, never the solar rung.

Usage: python scripts/derive_caiso_import_tranches.py [--partial]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402
from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA  # noqa: E402
from market_sim.data.eia_loader import _caiso_interchange_model_clock  # noqa: E402

INTERCHANGE = (
    paths.RAW_DATA_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
)
HUB_LMP = (
    paths.RAW_DATA_DIR / "_validation-source" / "wecc_intertie_lmp_hourly_CAISO.parquet"
)

_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()
_HOURS = 8760
YEARS = (2023, 2024, 2025)

# Corridor -> proxy hub in the intertie LMP parquet.
CORRIDOR_HUB = {"WECC_PNW": "MALIN", "WECC_DSW": "PALOVRDE"}

# Rung capacity breakpoints per corridor (MW), matching the existing ladder's
# corridor structure (interchange_config.IMPORT_TRANCHES["CAISO"]). The cumulative
# level at each rung's MIDPOINT keys the Q-Q coupling.
RUNGS = {
    "WECC_PNW": [("PNW_hydro_base", 1566.0), ("PNW_midC", 1800.0)],
    "WECC_DSW": [("DSW_solar_PV", 1805.0), ("DSW_CCGT", 1800.0), ("DSW_CT", 2200.0)],
}

# Honesty-gate thresholds.
CV_MAX = 0.20  # per-rung price coefficient of variation across years
LOYO_MAX = 0.25  # held-out relative price error

# Rungs excluded from gating in --partial mode: they keep their static value as
# an explicitly-labelled price-taker floor instead of a derived price (caiso-86
# FINDING §4), so their derived-price stability is not load-bearing.
PARTIAL_EXCLUDED = ("DSW_solar_PV",)


def corridor_net_import() -> pd.DataFrame:
    """Dense (year, hour) net-import MW per corridor, on the model clock."""
    frame = pd.read_parquet(INTERCHANGE)
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    month = local.month.to_numpy()
    day = local.day.to_numpy()
    hod = local.hour.to_numpy()
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in month])
    hour = base + (day - 1) * 24 + hod
    year = local.year.to_numpy()
    keep = ~((month == 2) & (day == 29)) & (hour >= 0) & (hour < _HOURS)
    f = frame.loc[keep].copy()
    f["year"] = year[keep]
    f["hour"] = hour[keep]
    f["corridor"] = f["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    f = f.dropna(subset=["corridor"])
    # net_import = -sum(interchange) per (year, hour, corridor)
    g = f.groupby(["year", "hour", "corridor"], observed=True)["mw"].sum()
    net = (-g).unstack("corridor")
    full = pd.MultiIndex.from_product([YEARS, range(_HOURS)], names=["year", "hour"])
    return net.reindex(full)


def hub_prices() -> pd.DataFrame:
    """Dense (year, hour) DA hub price per corridor proxy ($/MWh)."""
    df = pd.read_parquet(HUB_LMP)
    piv = df.pivot_table(index=["year", "hour"], columns="hub", values="price")
    full = pd.MultiIndex.from_product([YEARS, range(_HOURS)], names=["year", "hour"])
    return piv.reindex(full)


def qq_price(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """DA hub-price quantile matching the level's net-import exceedance duration."""
    m = np.isfinite(price) & np.isfinite(flow)
    price, flow = price[m], flow[m]
    if price.size == 0:
        return float("nan")
    exceed = float((flow > level).mean())
    return float(np.quantile(price, 1.0 - exceed))


def derive_year(net: pd.DataFrame, hub: pd.DataFrame, years) -> dict[str, float]:
    """Derive {rung_name: price} from the pooled sample over ``years``."""
    out: dict[str, float] = {}
    sel = [y for y in years]
    for corridor, rungs in RUNGS.items():
        proxy = CORRIDOR_HUB[corridor]
        flow = np.concatenate([net.loc[y][corridor].to_numpy() for y in sel])
        price = np.concatenate([hub.loc[y][proxy].to_numpy() for y in sel])
        cum = 0.0
        for name, cap in rungs:
            mid = cum + cap / 2.0
            out[name] = qq_price(price, flow, mid)
            cum += cap
    return out


def main() -> None:
    partial = "--partial" in sys.argv[1:]
    net = corridor_net_import()
    hub = hub_prices()

    # Per-year derived rungs.
    per_year = {y: derive_year(net, hub, [y]) for y in YEARS}
    names = list(next(iter(per_year.values())).keys())
    gated = [nm for nm in names if not (partial and nm in PARTIAL_EXCLUDED)]

    mode = "PARTIAL four-rung (caiso-86 FINDING §4)" if partial else "FULL ladder"
    print("=== per-year derived rung prices ($/MWh, Q-Q duration coupling) ===")
    print(f"    gate mode: {mode}")
    hdr = "rung".ljust(16) + "".join(f"{y:>10}" for y in YEARS) + "     CV   gate"
    print(hdr)
    stability_ok = True
    for nm in names:
        vals = np.array([per_year[y][nm] for y in YEARS], dtype=float)
        cv = (
            float(np.nanstd(vals) / np.nanmean(vals))
            if np.nanmean(vals)
            else float("nan")
        )
        row = nm.ljust(16) + "".join(f"{v:>10.1f}" for v in vals)
        if nm not in gated:
            print(f"{row}   {cv:>5.2f}   excluded (static price-taker floor)")
            continue
        ok = np.isfinite(cv) and cv <= CV_MAX
        stability_ok = stability_ok and ok
        print(f"{row}   {cv:>5.2f}   {'ok' if ok else 'FAIL'}")

    # LOYO: derive on the other two years, predict the held-out year.
    print("\n=== LOYO (derive on 2 years, predict the held-out year) ===")
    loyo_ok = True
    for held in YEARS:
        train = [y for y in YEARS if y != held]
        pred = derive_year(net, hub, train)
        act = per_year[held]
        errs = []
        for nm in gated:
            a, p = act[nm], pred[nm]
            if np.isfinite(a) and np.isfinite(p) and a:
                errs.append(abs(p - a) / abs(a))
        worst = max(errs) if errs else float("nan")
        ok = np.isfinite(worst) and worst <= LOYO_MAX
        loyo_ok = loyo_ok and ok
        print(
            f"  held-out {held}: worst relative rung error {worst:.2%}   {'ok' if ok else 'FAIL'}"
        )

    print("\n=== GATE VERDICT ===")
    print(f"  gate mode: {mode} ({len(gated)}/{len(names)} rungs gated)")
    print(f"  year-stability (CV<= {CV_MAX}): {'PASS' if stability_ok else 'FAIL'}")
    print(f"  LOYO (worst<= {LOYO_MAX:.0%}):     {'PASS' if loyo_ok else 'FAIL'}")
    passed = stability_ok and loyo_ok
    print(
        f"  OVERALL: {'PASS — ladder admissible, may solve' if passed else 'FAIL — file FINDING, do NOT solve'}"
    )
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
