#!/usr/bin/env python3
"""Derive MISO's per-seam measured band-price ladders (Q-Q duration coupling).

Fixes the MISO 2025 import starvation (gap register G-23 residual; audit box 5
of ``docs/multi-iso/miso-cc-overrun-rootcause-2026-07.md``): the reference-
price seam clears on the hourly spot spread, but the measured PJM+IESO seam
flow is a firm/scheduled base — it imports in 97.5-99.5% of ALL hours
(p10 0.9-1.7 GW), its hourly flow is uncorrelated with the RT LMP spread
(r = +0.06), and in 2025 the annual RT spread is $0.00 while 28.0 TWh flowed.
46-56% of the measured import MWh moves at spreads inside/below the $2
hurdle, so a hurdle-gated arbitrage seam structurally deletes the flow in a
zero-spread year (model 2025 gross imports 3.4 TWh vs actual net 19.0).

This derives the same replacement NEISO's audit C-6 closure used
(``scripts/derive_neiso_import_tranches.py``): the seam's *revealed supply
curve*, built by Q-Q duration coupling of two measured series —

1. **Per-seam flows** — EIA-930 BA-to-BA net interchange for MISO
   (``data/raw/eia-930-interchange/MISO interchange hourly.parquet``),
   pooled onto the model's three priced seams by
   ``interchange_config.MISO_SEAM_DIBA`` (PJM+IESO / SWPP+SPA /
   SOCO+TVA+AECI+LGEE+SIKE). Hour-ending local -> hour-beginning fixed
   non-leap calendar (Feb 29 dropped), the LP's clock.
2. **Internal clearing price** — the measured MISO Day-Ahead hub LMP
   (``data/raw/_validation-source/actual_lmp_hourly_MISO.parquet``, ``da``).
   External transactions schedule in the DA market, so DA is the price the
   seam supply curve is revealed against (same convention as NEISO).

Methodology — per-band Q-Q duration coupling
--------------------------------------------
The reference-price node already splits each seam into
``neighbor_price.SEAM_FLOW_TRANCHES`` (8) equal flow bands per direction
(``transmission.build_reference_price_node``); band ``k`` clears fully
whenever the internal price exceeds its offer. The measured counterpart of
that offer is the DA price whose exceedance duration equals the measured
duration of the seam flow exceeding the band's midpoint depth:

    import band k:  pi_k    = Quantile_DA(1 - P[flow >  L_k])
    export band k:  sigma_k = Quantile_DA(    P[flow < -L_k])
    L_k = (k - 0.5) x interface_limit / 8   (the band's midpoint depth)

i.e. the DA price duration curve and the seam flow duration curve are paired
quantile-by-quantile, per seam and per direction. A band deeper than the
measured record's deepest flow gets the sample extreme (an effectively
never-clearing scarcity/floor rung). Band CAPACITIES are untouched — the
existing 8 x interface_limit/8 structure and the measured per-seam
(month x hour-of-day) deliverability envelopes
(``eia_loader.measured_seam_import_envelope``) keep carrying the measured
capability; ONLY the price ladder changes.

Why this is the right market structure (rule #1): the MISO<->PJM interchange
is dominated by firm PTP transmission service, grandfathered agreements and
JOA firm flow entitlements — energy scheduled around the clock at prices
revealed only statistically, not a spot-spread arbitrage. The ladder encodes
that revealed willingness-to-flow as a rising supply curve the LP still
clears *economically* every hour against its own internal price: nothing is
forced (contrast the rejected ``miso_firm_import_floor`` min_gen pin), flows
respond to changed model conditions, and the pooled multi-year ladder is the
forward story (a persistent seam structure that regenerates as the measured
record extends — the NEISO static-entry pattern).

Identification (CLAUDE.md rule 23): measured-behaviour, frozen formula — the
ladders re-derive ONLY when the source data updates (a new EIA-930 /
settlement year), never because a backcast residual moved. Zero fitted
parameters: every number is a quantile of a measured series at a structurally
fixed depth grid.

Boundary reconciliations (rule 14), documented here and in
``interchange_config.MISO_SEAM_LADDER_BY_YEAR``:

* The PJM seam pools the Ontario (IESO) tie per ``MISO_SEAM_DIBA`` — the
  model has one eastern seam. IESO is +7.4/+5.2/+3.4 TWh of the seam's
  +40.9/+32.3/+28.0 TWh (2023/24/25); its surplus-baseload economics are
  absorbed into the pooled ladder's cheap base bands.
* The coupling anchor is the MISO hub-mean DA LMP (the in-repo canonical
  internal price), not the border-zone LMPs the seam physically clears
  against; the PJM-side western border anchor
  (``pjm_border_lmp_hourly_MISO.parquet``, CHICAGO GEN/AEP GEN/ATSI GEN) is
  reported per band as a diagnostic so each threshold stays interpretable as
  border price +/- premium.
* Same-seam no-wash: each seam's export ladder must sit strictly below its
  import ladder at every band (a seam cannot deeply import and export at
  once); asserted per year, with a clamp note if it ever binds. CROSS-seam
  simultaneous counterflow (import PJM while exporting South) is real
  wheel-through the multi-link external node carries physically, bounded by
  the measured per-seam envelopes.

Usage:
    python scripts/derive_miso_seam_ladders.py            # all years + pooled
    python scripts/derive_miso_seam_ladders.py --years 2025

Output is hand-rounded (prices to cents) into
``interchange_config.MISO_SEAM_LADDER_BY_YEAR``, with this script cited as
the derivation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

RAW = REPO / "data" / "raw"
INTERCHANGE_PARQUET = RAW / "eia-930-interchange" / "MISO interchange hourly.parquet"
ACTUAL_LMP_PARQUET = RAW / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
PJM_BORDER_PARQUET = RAW / "_validation-source" / "pjm_border_lmp_hourly_MISO.parquet"

YEARS = (2023, 2024, 2025)

# No-wash ordering margin ($/MWh): a seam's export sinks sit at least this far
# below its cheapest import band (same-seam reconciliation, module docstring).
NO_WASH_EPS = 0.01

# Fixed non-leap calendar helpers (identical to derive_neiso_import_tranches).
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()
_HOURS_PER_YEAR = 8760


def load_joined() -> pd.DataFrame:
    """Return the dense (year, hour) frame joining seam flows and the DA LMP.

    Columns: one import-positive MW series per seam in
    :data:`~market_sim.config.interchange_config.MISO_SEAM_DIBA` (``PJM`` /
    ``SPP`` / ``South``), plus ``da``/``rt`` ($/MWh MISO hub) and
    ``pjm_border`` ($/MWh, diagnostic anchor). Isolated gaps (DST)
    interpolated (limit=3).
    """
    from market_sim.config.interchange_config import MISO_SEAM_DIBA

    ix = pd.read_parquet(INTERCHANGE_PARQUET)
    # Hour-ending local -> hour-beginning fixed non-leap hour-of-year.
    t = pd.to_datetime(ix["local_time"]) - pd.Timedelta(hours=1)
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in t.dt.month])
    hr = base + (t.dt.day.to_numpy() - 1) * 24 + t.dt.hour.to_numpy()
    ix = ix.assign(year=t.dt.year.to_numpy(), hour=hr)
    ix.loc[(t.dt.month == 2) & (t.dt.day == 29), "hour"] = -1
    ix = ix[(ix["hour"] >= 0) & (ix["hour"] < _HOURS_PER_YEAR)]
    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    ix = ix.assign(seam=ix["diba"].astype(str).map(diba_to_seam))
    ix = ix.dropna(subset=["seam"])
    # Import-positive per seam: EIA sign is + = MISO exports to the DIBA.
    flows = -ix.pivot_table(
        index=["year", "hour"],
        columns="seam",
        values="mw",
        aggfunc="sum",
        observed=True,
    )
    lmp = pd.read_parquet(ACTUAL_LMP_PARQUET).set_index(["year", "hour"])
    border = (
        pd.read_parquet(PJM_BORDER_PARQUET)
        .groupby(["year", "hour"])["price"]
        .mean()
        .rename("pjm_border")
    )
    years = sorted(set(flows.index.get_level_values("year")))
    full = pd.MultiIndex.from_product(
        [years, range(_HOURS_PER_YEAR)], names=["year", "hour"]
    )
    df = flows.reindex(full).join(lmp).join(border)
    return df.interpolate(limit=3)


def qq_import(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Import-band price: DA quantile matching the depth's exceedance duration."""
    exceed = float((flow > level).mean())
    return float(np.quantile(price, 1.0 - exceed))


def qq_export(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Export-band price: DA quantile matching the export-depth duration."""
    depth = float((flow < -level).mean())
    return float(np.quantile(price, depth))


def derive(g: pd.DataFrame) -> tuple[dict, list[str]]:
    """Derive ``{seam: {"import": [...], "export": [...]}}`` from sample ``g``.

    ``g`` is one year of :func:`load_joined` (or the pooled multi-year frame
    for the static forward ladder). Prices are per band 1..SEAM_FLOW_TRANCHES
    at the midpoint-depth grid of each seam's interface limit. ``notes``
    carries no-wash clamp diagnostics (expected empty — the measured record
    orders every seam naturally).
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    g = g.dropna(subset=["da"] + [n.name for n in INTERFACE_NEIGHBORS["MISO"]])
    da = g["da"].to_numpy(dtype=float)
    out: dict[str, dict[str, list[float]]] = {}
    notes: list[str] = []
    for spec in INTERFACE_NEIGHBORS["MISO"]:
        flow = g[spec.name].to_numpy(dtype=float)
        step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
        mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step
        imp = [qq_import(da, flow, m) for m in mids]
        exp = [qq_export(da, flow, m) for m in mids]
        # Same-seam no-wash: every export band strictly below the cheapest
        # import band (rule 14 single-seam reconciliation).
        lim = min(imp) - NO_WASH_EPS
        for k, s in enumerate(exp):
            if s > lim:
                notes.append(
                    f"{spec.name} export band {k + 1}: sink ${s:.2f} clamped "
                    f"to ${lim:.2f} (same-seam no-wash vs cheapest import band)"
                )
                exp[k] = lim
        out[spec.name] = {
            "import": [round(p, 2) for p in imp],
            "export": [round(p, 2) for p in exp],
        }
    return out, notes


def offline_score(g: pd.DataFrame, ladders: dict) -> dict[str, dict[str, float]]:
    """Score each seam's ladder against its measured flow, driven by actual DA.

    The offline analogue of the NEISO derivation's P9 diagnostic: simulate the
    band clearing ``sum(step x 1[DA > pi_k]) - sum(step x 1[DA < sigma_k])``
    on the measured DA price and compare to the measured seam net flow
    (volume, duration RMSE, import-hour share, hourly correlation). The live
    LP additionally applies the measured per-seam deliverability envelopes and
    its own internal price, so this is the derivation sanity check, not the
    calibration score.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    g = g.dropna(subset=["da"] + list(ladders))
    da = g["da"].to_numpy(dtype=float)
    scores: dict[str, dict[str, float]] = {}
    for spec in INTERFACE_NEIGHBORS["MISO"]:
        lad = ladders[spec.name]
        step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
        act = g[spec.name].to_numpy(dtype=float)
        sim = sum(step * (da > p) for p in lad["import"]) - sum(
            step * (da < p) for p in lad["export"]
        )
        scores[spec.name] = {
            "sim_twh": sim.sum() / 1e6,
            "act_twh": act.sum() / 1e6,
            "dur_rmse": float(np.sqrt(np.mean((np.sort(sim) - np.sort(act)) ** 2))),
            "imp_hrs_sim": 100.0 * float((sim > 0).mean()),
            "imp_hrs_act": 100.0 * float((act > 0).mean()),
            "hourly_corr": float(np.corrcoef(sim, act)[0, 1]),
        }
    return scores


def _print_ladder(label: str, g: pd.DataFrame) -> None:
    """Derive, score and print one sample's ladders + anchor diagnostics."""
    ladders, notes = derive(g)
    gg = g.dropna(subset=["da"])
    da_mean = float(gg["da"].mean())
    border_mean = float(gg["pjm_border"].mean())
    print(f"\n=== {label} ===")
    print(
        f"  anchors: MISO hub DA mean ${da_mean:.2f}, "
        f"PJM western-border DA mean ${border_mean:.2f}"
    )
    for seam, lad in ladders.items():
        anchor = f"  [PJM border anchor ${border_mean:.2f}]" if seam == "PJM" else ""
        print(f'    "{seam}": {{{anchor}')
        print(f'        "import": {tuple(lad["import"])},')
        print(f'        "export": {tuple(lad["export"])},')
        print("    },")
    for n in notes:
        print(f"  note: {n}")
    for seam, s in offline_score(g, ladders).items():
        print(
            f"  offline P9 {seam}: {s['sim_twh']:+.2f} TWh vs {s['act_twh']:+.2f} "
            f"actual; duration RMSE {s['dur_rmse']:.0f} MW; import hours "
            f"{s['imp_hrs_sim']:.0f}% vs {s['imp_hrs_act']:.0f}%; "
            f"hourly corr {s['hourly_corr']:+.2f}"
        )


def main() -> None:
    """CLI entry point: derive per-year ladders and the pooled forward ladder."""
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
