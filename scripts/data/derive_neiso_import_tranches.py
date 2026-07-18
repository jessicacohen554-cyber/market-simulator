#!/usr/bin/env python3
"""Derive NEISO's import/export tranche ladders from measured seam data.

Replaces the residual-fitted ``IMPORT_TRANCHES["NEISO"]`` /
``EXPORT_TRANCHES["NEISO"]`` rungs (model-legitimacy audit C-6: "replace
year-keyed rungs with measured hub prices / published wheeling costs per
seam") with ladders derived by a frozen formula from three measured sources:

1. **Per-seam flows** — EIA-930 BA-to-BA net interchange for ISNE
   (``data/raw/eia-930-interchange/ISNE interchange hourly.parquet``,
   ``scripts/data/fetch_eia930_interchange.py``): the HQT (Hydro-Québec),
   NBSO (New Brunswick) and NYIS (New York) seams, hourly, 2023-2025.
2. **Internal clearing price** — the measured ISO-NE Day-Ahead hub LMP
   (``data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet``, from the
   ISO-NE SMD hourly workbooks). External transactions schedule in the DA
   market, so DA is the price the seam supply curve is revealed against.
3. **Neighbor-hub anchors** — the NYISO proxy-bus DA LBMPs
   (``data/raw/_validation-source/nyiso_proxy_lmp_hourly_NEISO.parquet``,
   ``scripts/data/build_nyiso_proxy_lmp_neiso.py``): ``NYISO_NPX`` (the NY-side
   price at the NY-NE interface — the measured source price of NYISO-seam
   imports) and ``NYISO_HQ`` (HQ's measured opportunity cost in its
   alternative export market). Reported as anchor diagnostics on every rung
   so the derived thresholds stay interpretable as hub price ± premium.

Methodology — per-seam Q-Q duration coupling
--------------------------------------------
The priced node is a step supply curve: rung ``k`` (capacity ``c_k``, price
``pi_k``) clears fully whenever the internal price exceeds ``pi_k``. The
measured counterpart of ``pi_k`` is therefore the DA price whose exceedance
duration equals the measured duration of the seam flow exceeding the rung's
cumulative-capacity midpoint:

    pi_k = Quantile_DA(1 - P[flow_seam > L_k]),   L_k = midpoint of rung k

i.e. the price duration curve and the seam flow duration curve are paired
quantile-by-quantile — the same anti-monotone coupling
``derive_import_tranches.py``'s bundle mode uses, but driven by the
*measured* DA price (no solved bundle in the loop, so nothing is fitted to a
model residual) and applied per seam so each rung stays attached to a
physical interface. Export sinks use the mirrored coupling
(``Quantile_DA(P[flow < -L])``). Rung capacities come from the measured flow
distribution (``CAP_PCTL``) and published interface ratings (Highgate).

This is measured-behaviour identification (CLAUDE.md rule 23): the ladders
re-derive ONLY when the source data updates (a new year of EIA-930 / SMD /
NYISO archives), never because a backcast residual moved. Forward story
(rule 15): the pooled-sample static ladder is the multi-year revealed seam
supply curve — a persistent market structure (HQ energy-limited water
value, NY-NE arbitrage parity, NB surplus) that regenerates whenever the
measured record extends.

Single-node reconciliation (rule 14): the model hosts all seams on one
pooled ``HQ_import`` node, which cannot represent simultaneous counterflow
(wheel-through: real hours import from HQ while exporting to NY). A sink
priced above an import rung would therefore be a same-node wash-trade money
pump, so sink prices are clamped to (cheapest import rung - $0.01). The
clamp is reported whenever it binds.

Usage:
    python scripts/data/derive_neiso_import_tranches.py            # all years + pooled
    python scripts/data/derive_neiso_import_tranches.py --years 2024

Output is hand-rounded into ``interchange_config.IMPORT_TRANCHES["NEISO"]``,
``IMPORT_TRANCHES_BY_YEAR["NEISO"]``, ``EXPORT_TRANCHES["NEISO"]`` and
``EXPORT_TRANCHES_BY_YEAR["NEISO"]`` (capacities to 5 MW, prices to cents),
with this script cited as the derivation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
RAW = REPO / "data" / "raw"
INTERCHANGE_PARQUET = RAW / "eia-930-interchange" / "ISNE interchange hourly.parquet"
PROXY_PARQUET = RAW / "_validation-source" / "nyiso_proxy_lmp_hourly_NEISO.parquet"
ACTUAL_LMP_PARQUET = RAW / "_validation-source" / "actual_lmp_hourly_NEISO.parquet"

YEARS = (2023, 2024, 2025)

# --- Fixed derivation structure (frozen; re-derive only on source update) ---

# Highgate back-to-back HVDC converter rating (VT-Québec tie). Source: ISO-NE
# Regional System Plan external-interface ratings; VELCO Highgate converter
# ~225 MW. The only sub-seam split not observable in EIA-930 (HQT folds
# Phase II + Highgate), so the published rating carves the baseload rung.
HIGHGATE_RATING_MW = 225.0

# Rung-capacity percentile of the measured seam import distribution: the
# routinely deliverable depth (p98 ~ the deepest sustained deliveries,
# clipping single-hour spikes). Same envelope convention as the topology's
# link TTC comment (iso_configs.py, "envelopes the deepest measured import").
CAP_PCTL = 98.0

# Emergency-depth percentile for the scarcity rung (total across seams).
SCARCITY_PCTL = 99.9

# Export-sink capacity percentile of the export-side distribution (mirror of
# CAP_PCTL: p98 of export depth = 2nd percentile of signed import flow).
EXPORT_CAP_PCTL = 2.0

# NYISO seam rungs: two equal blocks (base / peak halves of the AC + cable
# tie set), thresholds at the quarter-capacity midpoints.
NYISO_RUNG_MIDPOINTS = (0.25, 0.75)

# Minimum sink capacity worth a rung (MW) — below this the seam's export
# side is noise (NBSO 2023 exports).
MIN_SINK_MW = 100.0

# No-wash ordering margin ($/MWh): sinks sit at least this far below the
# cheapest import rung (single-node reconciliation, module docstring).
NO_WASH_EPS = 0.01

# Fixed non-leap calendar helpers (identical to the border-lmp builders).
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()
_HOURS_PER_YEAR = 8760


def load_joined() -> pd.DataFrame:
    """Return the dense (year, hour) frame joining flows, DA LMP and anchors.

    Columns: ``HQT``/``NBSO``/``NYIS`` (MW, EIA sign: negative = ISNE
    imports), ``NYISO_HQ``/``NYISO_NPX`` ($/MWh anchors), ``da``/``rt``
    ($/MWh ISO-NE hub). Isolated gaps (DST) interpolated (limit=3).
    """
    ix = pd.read_parquet(INTERCHANGE_PARQUET)
    # Hour-ending local -> hour-beginning fixed non-leap hour-of-year.
    t = ix["local_time"] - pd.Timedelta(hours=1)
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in t.dt.month])
    hr = base + (t.dt.day.to_numpy() - 1) * 24 + t.dt.hour.to_numpy()
    ix["year"] = t.dt.year
    ix["hour"] = np.where((t.dt.month == 2) & (t.dt.day == 29), -1, hr)
    ix = ix[(ix["hour"] >= 0) & (ix["hour"] < _HOURS_PER_YEAR)]
    flows = ix.pivot_table(
        index=["year", "hour"], columns="diba", values="mw", observed=True
    )
    proxy = pd.read_parquet(PROXY_PARQUET).pivot_table(
        index=["year", "hour"], columns="hub", values="price"
    )
    lmp = pd.read_parquet(ACTUAL_LMP_PARQUET).set_index(["year", "hour"])
    years = sorted(set(flows.index.get_level_values("year")))
    full = pd.MultiIndex.from_product(
        [years, range(_HOURS_PER_YEAR)], names=["year", "hour"]
    )
    df = flows.reindex(full).join(proxy).join(lmp)
    return df.interpolate(limit=3)


def qq_threshold(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Import-rung price: DA quantile matching the level's exceedance duration."""
    exceed = float((flow > level).mean())
    return float(np.quantile(price, 1.0 - exceed))


def qq_sink(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Export-sink price: DA quantile matching the export-depth duration."""
    depth = float((flow < -level).mean())
    return float(np.quantile(price, depth))


def _round_cap(mw: float) -> float:
    """Round a rung capacity to 5 MW."""
    return float(round(mw / 5.0) * 5.0)


def derive(g: pd.DataFrame) -> tuple[list, list, list[str]]:
    """Derive (imports, exports, notes) from a joined sample ``g``.

    ``g`` is one year of :func:`load_joined` (or the pooled multi-year frame
    for the static forward ladder). Import entries are
    ``(name, capacity_mw, price)`` cheapest-first within seam order; export
    entries likewise. ``notes`` carries clamp/skip diagnostics.
    """
    g = g.dropna()
    da = g["da"].to_numpy(dtype=float)
    hq = -g["HQT"].to_numpy(dtype=float)  # import-positive
    nb = -g["NBSO"].to_numpy(dtype=float)
    ny = -g["NYIS"].to_numpy(dtype=float)
    total = hq + nb + ny
    notes: list[str] = []

    imports: list[tuple[str, float, float]] = []
    # HQ seam: Highgate baseload rung (published rating) + Phase II remainder.
    hg_cap = HIGHGATE_RATING_MW
    ph_cap = _round_cap(np.percentile(hq, CAP_PCTL) - hg_cap)
    imports.append(("Highgate", hg_cap, qq_threshold(da, hq, hg_cap / 2.0)))
    imports.append(("HQ_PhaseII", ph_cap, qq_threshold(da, hq, hg_cap + ph_cap / 2.0)))
    # New Brunswick seam: single rung.
    nb_cap = _round_cap(np.percentile(nb, CAP_PCTL))
    imports.append(("NB_north", nb_cap, qq_threshold(da, nb, nb_cap / 2.0)))
    # NYISO seam: base/peak halves.
    ny_cap = _round_cap(np.percentile(ny, CAP_PCTL))
    half = _round_cap(ny_cap / 2.0)
    for tag, mid in zip(("base", "peak"), NYISO_RUNG_MIDPOINTS):
        imports.append((f"NYISO_CT_{tag}", half, qq_threshold(da, ny, ny_cap * mid)))
    # Scarcity rung: emergency depth beyond the per-seam rungs, priced at the
    # total-flow coupling.
    routine = sum(c for _, c, _ in imports)
    sc_cap = _round_cap(max(0.0, np.percentile(total, SCARCITY_PCTL) - routine))
    if sc_cap > 0:
        imports.append(
            (
                "import_scarcity",
                sc_cap,
                qq_threshold(da, total, routine + sc_cap / 2.0),
            )
        )
    else:
        notes.append("import_scarcity: no depth beyond per-seam rungs — omitted")

    exports: list[tuple[str, float, float]] = []
    for name, flow in (("export_NYISO", ny), ("export_NB", nb), ("export_HQ", hq)):
        cap = _round_cap(max(0.0, -np.percentile(flow, EXPORT_CAP_PCTL)))
        if cap < MIN_SINK_MW:
            notes.append(
                f"{name}: export depth {cap:.0f} MW < {MIN_SINK_MW:.0f} — omitted"
            )
            continue
        exports.append((name, cap, qq_sink(da, flow, cap / 2.0)))

    # Single-node no-wash reconciliation (rule 14): every sink strictly below
    # the cheapest import rung.
    floor_price = min(p for _, _, p in imports)
    clamped = []
    for name, cap, price in exports:
        lim = floor_price - NO_WASH_EPS
        if price > lim:
            notes.append(
                f"{name}: sink ${price:.2f} clamped to ${lim:.2f} "
                f"(no-wash ordering vs cheapest import rung)"
            )
            price = lim
        clamped.append((name, cap, round(price, 2)))
    imports = [(n, c, round(p, 2)) for n, c, p in imports]
    return imports, clamped, notes


def offline_score(g: pd.DataFrame, imports: list, exports: list) -> dict[str, float]:
    """Score the ladder against the measured net import, driven by actual DA.

    The offline analogue of the P9 diagnostic: simulate the node's clearing
    ``sum(c_k * 1[DA > pi_k]) - sum(s_j * 1[DA < sigma_j])`` on the measured
    DA price and compare to the measured total net import (volume, duration
    RMSE, import-hour share, diurnal correlation, hourly correlation).
    """
    g = g.dropna()
    da = g["da"].to_numpy(dtype=float)
    net = -(g["HQT"] + g["NBSO"] + g["NYIS"]).to_numpy(dtype=float)
    sim = sum(c * (da > p) for _, c, p in imports) - sum(
        c * (da < p) for _, c, p in exports
    )
    n24 = len(sim) // 24 * 24
    d24s = sim[:n24].reshape(-1, 24).mean(axis=0)
    d24a = net[:n24].reshape(-1, 24).mean(axis=0)
    return {
        "sim_twh": sim.sum() / 1e6,
        "act_twh": net.sum() / 1e6,
        "dur_rmse": float(np.sqrt(np.mean((np.sort(sim) - np.sort(net)) ** 2))),
        "imp_hrs_sim": 100.0 * float((sim > 0).mean()),
        "imp_hrs_act": 100.0 * float((net > 0).mean()),
        "diurnal_corr": float(np.corrcoef(d24s, d24a)[0, 1]),
        "hourly_corr": float(np.corrcoef(sim, net)[0, 1]),
    }


def _print_ladder(label: str, g: pd.DataFrame) -> None:
    """Derive, score and print one sample's ladders + anchor diagnostics."""
    imports, exports, notes = derive(g)
    gg = g.dropna()
    hq_anchor = float(gg["NYISO_HQ"].mean())
    npx_anchor = float(gg["NYISO_NPX"].mean())
    print(f"\n=== {label} ===")
    print(
        f"  anchors: NYISO_HQ mean ${hq_anchor:.2f}, NYISO_NPX mean ${npx_anchor:.2f}"
    )
    for name, cap, price in imports:
        anchor = (
            f"  [{price - hq_anchor:+.1f} vs HQ anchor]"
            if name in ("Highgate", "HQ_PhaseII")
            else f"  [{price - npx_anchor:+.1f} vs NPX anchor]"
            if name.startswith("NYISO_CT")
            else ""
        )
        print(f'    ("{name}", {cap:.1f}, {price:.2f}),{anchor}')
    for name, cap, price in exports:
        print(f'    ("{name}", {cap:.1f}, {price:.2f}),  # sink')
    for n in notes:
        print(f"  note: {n}")
    s = offline_score(g, imports, exports)
    print(
        f"  offline P9 (actual-DA-driven): {s['sim_twh']:+.2f} TWh vs "
        f"{s['act_twh']:+.2f} actual; duration RMSE {s['dur_rmse']:.0f} MW; "
        f"import hours {s['imp_hrs_sim']:.0f}% vs {s['imp_hrs_act']:.0f}%; "
        f"diurnal corr {s['diurnal_corr']:+.2f}; hourly corr {s['hourly_corr']:+.2f}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    args = ap.parse_args()

    df = load_joined()
    for year in args.years:
        _print_ladder(str(year), df.loc[year])
    if len(args.years) > 1:
        pooled = df.loc[args.years[0] : args.years[-1]]
        _print_ladder(
            f"pooled {args.years[0]}-{args.years[-1]} (static forward ladder)", pooled
        )


if __name__ == "__main__":
    main()
