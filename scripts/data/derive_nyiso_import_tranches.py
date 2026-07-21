#!/usr/bin/env python3
"""Derive NYISO's import tranche ladder from measured seam data.

Replaces the residual-fitted ``IMPORT_TRANCHES["NYISO"]`` /
``IMPORT_TRANCHES_BY_YEAR["NYISO"]`` rungs (model-legitimacy audit C-6 / gap
register G-26 / issue #1350: "replace year-keyed rungs with measured hub
prices per seam") with a ladder derived by a frozen formula from two measured
sources:

1. **External-seam flows** — the NYISO MIS ExternalLimitsFlows posting,
   curated to hourly per interface
   (``data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_<year>.csv.gz``,
   ``scripts/data/fetch_nyiso_interface_flows.py``). The four external seams —
   HQ (Chateauguay/Cedars), IESO (Ontario), PJM (Keystone AC + HTP + Neptune +
   Linden VFT) and NE (NPX + Cross Sound) — sum to the hourly NET external
   import (NYISO sign convention: positive = import into NY).
2. **Internal clearing price** — the measured NYISO Day-Ahead zonal-mean LBMP
   (``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet``). External
   transactions schedule in the DA market, so DA is the price the seam supply
   curve is revealed against.

Methodology — total-net Q-Q duration coupling (rule 14 single-node)
------------------------------------------------------------------
The model hosts every NYISO seam on ONE import node (``NYISO_external``), so
the object the LP needs is the *aggregate* net-import supply curve, not the
per-seam curves — reconciling the measured per-interface data to the model's
single-node representation means aggregating (rule 14). The priced node is a
step supply curve: rung ``k`` (capacity ``c_k``, price ``pi_k``) clears fully
whenever the internal price exceeds ``pi_k``. The measured counterpart of
``pi_k`` is the DA price whose exceedance duration equals the measured
duration of the net import exceeding the rung's cumulative-capacity midpoint:

    pi_k = Quantile_DA(1 - P[net_import > L_k]),   L_k = midpoint of rung k

i.e. the price duration curve and the net-import duration curve are paired
quantile-by-quantile (the same anti-monotone coupling
``derive_import_tranches.py``'s bundle mode uses, but driven by the *measured*
DA price — no solved bundle in the loop, so nothing is fitted to a model
residual). This reproduces the measured aggregate import supply curve by
construction, which is precisely what a coarse fitted ladder cannot: the
audit-flagged NYISO fit jumped IESO $22.5 → PJM_west $34.2 with nothing
between, pinning ~3000 off-peak hours (that really cleared at $20-28) onto the
$34.2 rung.

Rung structure (frozen; re-derive only on a source-data update, rule 23):
  * ``HQ_hydro`` — the firm Hydro-Québec baseload (Chateauguay contract), kept
    at its established ``FIRM_BASE_MW`` so the always-on firm-import floor
    (``NYISO_FIRM_IMPORT_FLOOR_FRAC["HQ_hydro"]`` = 1.0,
    ``transmission.inject_nyiso_firm_imports``) is byte-unchanged. Priced at
    the low-quantile coupling (cosmetic — the block is must-flow).
  * five economic rungs spanning ``[FIRM_BASE_MW, SIL]`` in equal-MW steps —
    the clearable range under the published ~4,350 MW Simultaneous Import Limit
    (``EXTERNAL_SIMULTANEOUS_LIMITS["NYISO"]``), so a rung midpoint sits at the
    off-peak operating depth (~2,600 MW) and reprices it measured.
  * ``import_scarcity`` — the deep tail beyond the SIL (``[SIL, p99.9]``);
    mostly SIL-blocked in dispatch (kept for structural completeness / the
    forward story).

The seam-order labels (IESO_Ontario / PJM_shoulder / PJM_west / eastern_mid /
ISONE_tie) are retained from the prior ladder as depth markers — the measured
derivation is on TOTAL net import (single node), so a label names the seam that
historically dominates the marginal transfer at roughly that depth, not an
isolated per-seam curve.

Forward story (rule 15): the pooled-sample static ladder is the multi-year
revealed aggregate seam supply curve — a persistent market structure that
regenerates whenever the measured record extends, and whose price level scales
with the DA price of a forward year.

Usage:
    python scripts/data/derive_nyiso_import_tranches.py            # all years + pooled
    python scripts/data/derive_nyiso_import_tranches.py --years 2023

Output is hand-rounded into ``interchange_config.IMPORT_TRANCHES["NYISO"]`` and
``IMPORT_TRANCHES_BY_YEAR["NYISO"]`` (capacities to 5 MW, prices to cents),
with this script cited as the derivation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

RAW = REPO / "data" / "raw"
FLOW_DIR = RAW / "NYISO" / "interface-flows"
DA_LMP_PARQUET = RAW / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"

YEARS = (2023, 2024, 2025)

# --- Fixed derivation structure (frozen; re-derive only on source update) ---

# The four external interfaces, each a list of the raw "SCH - *" interface
# names that land on it (NYISO MIS ExternalLimitsFlows). Internal interfaces
# (CENTRAL EAST, TOTAL EAST, UPNY CONED, MOSES SOUTH, DYSINGER, WEST CENTRAL,
# SPR/DUN) are NOT external transfers and are excluded.
EXTERNAL_SEAMS: dict[str, list[str]] = {
    "HQ": ["SCH - HQ - NY", "SCH - HQ_CEDARS", "SCH - HQ_IMPORT_EXPORT"],
    "IESO": ["SCH - OH - NY"],
    "PJM": ["SCH - PJ - NY", "SCH - PJM_HTP", "SCH - PJM_NEPTUNE", "SCH - PJM_VFT"],
    "NE": ["SCH - NE - NY", "SCH - NPX_1385", "SCH - NPX_CSC"],
}

# Firm HQ baseload (Chateauguay contract) — the always-on firm-import floor's
# capacity; kept at the ladder's established value so the floor is unchanged.
FIRM_BASE_MW = 900.0

# Published NYISO Simultaneous Import Limit (Gold Book / IRM-LCR;
# EXTERNAL_SIMULTANEOUS_LIMITS["NYISO"]). The economic rungs span the clearable
# [firm, SIL] range so a rung lands at the off-peak operating depth.
SIL_MW = 4350.0

# Number of equal-MW economic rungs between the firm base and the SIL.
N_ECONOMIC_RUNGS = 5

# Emergency-depth percentile for the scarcity rung (deep tail beyond the SIL).
SCARCITY_PCTL = 99.9

# Cheapest-first rung labels (depth markers; see module docstring).
RUNG_NAMES = (
    "HQ_hydro",
    "IESO_Ontario",
    "PJM_shoulder",
    "PJM_west",
    "eastern_mid",
    "ISONE_tie",
    "import_scarcity",
)

_HOURS_PER_YEAR = 8760


def load_net_import(year: int) -> np.ndarray:
    """Return the hourly (8760,) total net external import (MW, import-positive)."""
    path = FLOW_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz"
    df = pd.read_csv(path)
    df["t"] = pd.to_datetime(df["interval_start_local"])
    piv = df.pivot_table(
        index="t", columns="interface", values="flow_mw", aggfunc="mean"
    )
    net = sum(
        piv[[c for c in cols if c in piv.columns]].sum(axis=1)
        for cols in EXTERNAL_SEAMS.values()
    )
    fd = pd.DataFrame({"net": net})
    fd["hoy"] = (fd.index.dayofyear - 1) * 24 + fd.index.hour
    return (
        fd.groupby("hoy")["net"]
        .mean()
        .reindex(range(_HOURS_PER_YEAR))
        .to_numpy(dtype=float)
    )


def load_da_lmp(year: int) -> np.ndarray:
    """Return the hourly (8760,) measured NYISO Day-Ahead zonal-mean LBMP."""
    lmp = pd.read_parquet(DA_LMP_PARQUET)
    lmp = lmp[lmp["year"] == year].set_index("hour")
    return lmp["da"].reindex(range(_HOURS_PER_YEAR)).to_numpy(dtype=float)


def qq_threshold(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Import-rung price: DA quantile matching the level's exceedance duration."""
    mask = ~np.isnan(price) & ~np.isnan(flow)
    p, f = price[mask], flow[mask]
    exceed = float((f > level).mean())
    return float(np.quantile(p, 1.0 - exceed))


def _round_cap(mw: float) -> float:
    """Round a rung capacity to 5 MW."""
    return float(round(mw / 5.0) * 5.0)


def derive(net: np.ndarray, da: np.ndarray) -> list[tuple[str, float, float]]:
    """Derive the cheapest-first import ladder from one sample's (net, da)."""
    boundaries = [0.0, FIRM_BASE_MW]
    boundaries += list(np.linspace(FIRM_BASE_MW, SIL_MW, N_ECONOMIC_RUNGS + 1))[1:]
    p999 = float(np.nanpercentile(net, SCARCITY_PCTL))
    boundaries.append(max(p999, SIL_MW + 5.0))
    rungs: list[tuple[str, float, float]] = []
    for name, lo, hi in zip(RUNG_NAMES, boundaries[:-1], boundaries[1:]):
        cap = _round_cap(hi - lo)
        price = round(qq_threshold(da, net, (lo + hi) / 2.0), 2)
        rungs.append((name, cap, price))
    return rungs


def offline_score(
    net: np.ndarray, da: np.ndarray, rungs: list[tuple[str, float, float]]
) -> dict[str, float]:
    """Score the ladder vs measured net import, driven by actual DA (SIL-capped).

    Simulates the node's clearing ``min(SIL, sum(c_k * 1[DA > pi_k]))`` on the
    measured DA price and compares to the measured net import (volume, duration
    RMSE, import-hour share, diurnal & hourly correlation) — the offline
    analogue of the priced-node diagnostic, no LP in the loop.
    """
    mask = ~np.isnan(net) & ~np.isnan(da)
    net, da = net[mask], da[mask]
    raw = sum(c * (da > p) for _, c, p in rungs)
    sim = np.minimum(raw, SIL_MW)
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


def _print_ladder(label: str, net: np.ndarray, da: np.ndarray) -> None:
    rungs = derive(net, da)
    print(f"\n=== {label} ===")
    print(
        f"  net import mean {np.nanmean(net):.0f} MW, "
        f"DA LMP mean ${np.nanmean(da):.2f}"
    )
    cum = 0.0
    for name, cap, price in rungs:
        cum += cap
        print(f'    ("{name}", {cap:.1f}, {price:.2f}),   # cum {cum:.0f} MW')
    s = offline_score(net, da, rungs)
    print(
        f"  offline (actual-DA-driven, SIL-capped): {s['sim_twh']:+.2f} TWh vs "
        f"{s['act_twh']:+.2f} actual; duration RMSE {s['dur_rmse']:.0f} MW; "
        f"import hours {s['imp_hrs_sim']:.0f}% vs {s['imp_hrs_act']:.0f}%; "
        f"diurnal corr {s['diurnal_corr']:+.2f}; hourly corr {s['hourly_corr']:+.2f}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    args = ap.parse_args()

    nets = {y: load_net_import(y) for y in args.years}
    das = {y: load_da_lmp(y) for y in args.years}
    for year in args.years:
        _print_ladder(str(year), nets[year], das[year])
    if len(args.years) > 1:
        pooled_net = np.concatenate([nets[y] for y in args.years])
        pooled_da = np.concatenate([das[y] for y in args.years])
        _print_ladder(
            f"pooled {args.years[0]}-{args.years[-1]} (static forward ladder)",
            pooled_net,
            pooled_da,
        )


if __name__ == "__main__":
    main()
