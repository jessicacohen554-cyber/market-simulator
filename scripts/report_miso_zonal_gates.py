"""Report the MISO zonal-refinement structural gates from a calibration bundle.

Phase-1 validation of docs/multi-iso/miso-zonal-refinement-scope.md §7 — gate
on congestion EXISTING, not on the price residual (CLAUDE.md rule #1):

  1. **Links bind.** Per-interface binding-hour counts per year: each Midwest
     zone's CIL (import) / CEL (export) deliverability group, and the RDT
     one-way pair (net N→S at 3,000 MW / net S→N at 2,500 MW).
  2. **Prices separate.** Hours with max inter-zone spread > $1/MWh; per-zone
     mean LMP; the model's zone-mean sign pattern. When
     the measured per-hub actuals are present
     (``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet``,
     scope decision D6 — scripts/data/derive_miso_hub_lmp.py), the same statistics
     are printed for the ACTUAL hub prices (zone = member-hub mean;
     MISO-Plains = MINN+ILLINOIS hub-mean proxy, no LRZ 3/5 hub exists), so
     spread sign AND magnitude are scored against the market, not eyeballed.
  3. **LCR consistency.** In each zone's top-price (scarcity) hours, is the
     zone importing at its CIL? Illinois should show near-zero local scarcity
     (its LCR collapses to ~452 MW in PY2024-25).

Reads ``flows.parquet`` + ``system.parquet`` from the bundle and rebuilds the
same seasonal CIL/CEL hourly vectors the LP was solved with
(:func:`market_sim.model.transmission.build_miso_deliverability_groups`), so
the binding test compares the flow against the exact cap it was bounded by.

Usage:
    python scripts/report_miso_zonal_gates.py --bundle results/calibration/MISO/<run>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.model.transmission import (  # noqa: E402
    build_miso_deliverability_groups,
)

# A flow is "binding" when it sits within this tolerance of its cap (MW).
_BIND_TOL_MW = 1.0

# Scarcity hours per zone-year for gate 3: the top-N hours by that zone's LMP.
_SCARCITY_TOP_N = 50

# Measured per-hub actuals (D6). Zone actual = simple mean of member hubs;
# MISO-Plains has no hub -> MINN+ILLINOIS hub-mean proxy (documented in
# scripts/data/derive_miso_hub_lmp.py).
_ZONAL_ACTUALS = (
    REPO_ROOT / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
)
_PLAINS_PROXY_HUBS = ("MINN.HUB", "ILLINOIS.HUB")


def _actual_zone_prices(year: int, market: str) -> pd.DataFrame | None:
    """Return the actual hourly zone-price pivot for ``year``, or ``None``.

    Columns are the six model zones (Plains via the documented hub proxy),
    index hour-of-year, values the ``market`` ("rt" or "da") hub-mean LMP.
    """
    if not _ZONAL_ACTUALS.is_file():
        return None
    df = pd.read_parquet(_ZONAL_ACTUALS)
    df = df[df["year"] == year]
    if df.empty:
        return None
    pv = df.groupby(["hour", "zone"])[market].mean().unstack()
    pv["MISO-Plains"] = (
        df[df["hub"].isin(_PLAINS_PROXY_HUBS)].groupby("hour")[market].mean()
    )
    return pv


def _zone_groups(links) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Return ``{zone: (link_idx, signs)}`` for the internal incident links."""
    out: dict[str, tuple[list[int], list[float]]] = {}
    for zone in (
        "MISO-West",
        "MISO-Plains",
        "MISO-Illinois",
        "MISO-Indiana",
        "MISO-East",
    ):
        idx: list[int] = []
        signs: list[float] = []
        for i, ln in enumerate(links):
            if not (
                ln.from_zone.startswith("MISO-") and ln.to_zone.startswith("MISO-")
            ):
                continue
            if ln.to_zone == zone:
                idx.append(i)
                signs.append(1.0)
            elif ln.from_zone == zone:
                idx.append(i)
                signs.append(-1.0)
        out[zone] = (np.array(idx, dtype=int), np.array(signs))
    return out


def main() -> None:
    """Print the three structural gates for every year in the bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--pass-label", default=None, help="default: last pass present")
    args = ap.parse_args()
    bundle = Path(args.bundle)

    flows = pd.read_parquet(bundle / "flows.parquet")
    system = pd.read_parquet(bundle / "system.parquet")
    label = args.pass_label or sorted(flows["pass"].unique())[-1]
    flows = flows[flows["pass"] == label]
    system = system[system["pass"] == label]

    cfg = get_iso_config("MISO")
    # Reconstruct the solved link order from the frame (stable within a year).
    link_pairs = list(
        flows[["from_zone", "to_zone"]].drop_duplicates().itertuples(index=False)
    )

    class _Ln:  # minimal shim matching TransferLink's fields used here
        def __init__(self, a, b):
            self.from_zone, self.to_zone = a, b

    links = [_Ln(a, b) for a, b in link_pairs]
    groups = _zone_groups(links)
    rdt_fwd = next(
        i
        for i, ln in enumerate(links)
        if ln.from_zone.startswith("MISO-") and ln.to_zone == "MISO-South"
    )
    rdt_rev = next(
        i
        for i, ln in enumerate(links)
        if ln.from_zone == "MISO-South" and ln.to_zone.startswith("MISO-")
    )
    rdt_n_to_s = float(
        cfg.links[
            [(ln.from_zone, ln.to_zone) for ln in cfg.links].index(
                (links[rdt_fwd].from_zone, links[rdt_fwd].to_zone)
            )
        ].ttc_mw
    )
    rdt_s_to_n = float(
        cfg.links[
            [(ln.from_zone, ln.to_zone) for ln in cfg.links].index(
                (links[rdt_rev].from_zone, links[rdt_rev].to_zone)
            )
        ].ttc_mw
    )

    for year in sorted(flows["year"].unique()):
        fy = flows[flows["year"] == year]
        hours = int(fy["hour"].max()) + 1
        # (n_links, T) matrix in link_pairs order.
        fmat = np.zeros((len(links), hours))
        for i, (a, b) in enumerate(link_pairs):
            sub = fy[(fy["from_zone"] == a) & (fy["to_zone"] == b)]
            fmat[i, sub["hour"].to_numpy()] = sub["mw"].to_numpy()

        seasonal = build_miso_deliverability_groups(cfg.links, int(year), hours)
        # Map seasonal groups (built on cfg.links order) to zones via signs on
        # cfg.links; rebuild caps per zone.
        caps: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        cfg_groups = _zone_groups(cfg.links)
        for idx, cil, _b, cel, signs in seasonal:
            for zone, (zidx, zsigns) in cfg_groups.items():
                if len(zidx) == len(idx) and set(zidx) == set(idx):
                    caps[zone] = (cil, cel)
                    break

        print(f"\n=== MISO {year} ({label}) — structural gates ===")
        print("\n[Gate 1] Interface binding hours (of %d)" % hours)
        print(f"  {'interface':<28}{'bind_import(CIL)':>17}{'bind_export(CEL)':>17}")
        for zone, (zidx, zsigns) in groups.items():
            net = (zsigns[:, None] * fmat[zidx]).sum(axis=0)
            cil, cel = caps.get(zone, (None, None))
            bi = int((net >= cil - _BIND_TOL_MW).sum()) if cil is not None else -1
            be = int((net <= -(cel - _BIND_TOL_MW)).sum()) if cel is not None else -1
            print(f"  {zone + ' CIL/CEL group':<28}{bi:>17}{be:>17}")
        net_rdt = fmat[rdt_fwd] - fmat[rdt_rev]  # + = N->S
        b_ns = int((net_rdt >= rdt_n_to_s - _BIND_TOL_MW).sum())
        b_sn = int((net_rdt <= -(rdt_s_to_n - _BIND_TOL_MW)).sum())
        print(f"  {'RDT net N->S @3000':<28}{b_ns:>17}")
        print(f"  {'RDT net S->N @2500':<28}{b_sn:>17}")

        sy = system[system["year"] == year]
        internal = sy[sy["zone"].str.startswith("MISO-")]
        pv = internal.pivot(index="hour", columns="zone", values="price")
        spread = pv.max(axis=1) - pv.min(axis=1)
        print("\n[Gate 2] Price separation")
        print(f"  hours with max spread > $1: {int((spread > 1.0).sum())}")
        print(f"  hours with max spread > $5: {int((spread > 5.0).sum())}")
        print(f"  max spread: ${spread.max():.2f}")
        means = pv.mean().sort_values(ascending=False)
        print("  zone mean LMP: " + "  ".join(f"{z}={v:.2f}" for z, v in means.items()))
        # Sign pattern is scored against the MEASURED hub actuals below (the
        # pairwise agreement line), not a hardcoded expectation: the D6 hub
        # data shows actual South mean LMP sits BELOW every Midwest zone in
        # 2023-2025 (cheap Entergy nuclear/gas behind the RDT), so the scope
        # doc's original "South above West" heuristic was wrong on sign.
        west = pv["MISO-West"].mean()
        model_sign = (
            f"South {'>' if pv['MISO-South'].mean() > west else '<'} West, "
            f"East {'>' if pv['MISO-East'].mean() > west else '<'} West"
        )
        print(f"  model sign pattern: {model_sign}")
        for market in ("rt", "da"):
            apv = _actual_zone_prices(int(year), market)
            if apv is None:
                if market == "rt":
                    print("  (no measured hub actuals — run derive_miso_hub_lmp.py)")
                break
            aspread = apv.max(axis=1) - apv.min(axis=1)
            ameans = apv.mean().sort_values(ascending=False)
            print(f"  ACTUAL ({market}, hub-mean zones; Plains = MINN+ILL proxy)")
            print(
                f"    hours spread > $1: {int((aspread > 1.0).sum())}"
                f"   > $5: {int((aspread > 5.0).sum())}"
                f"   max: ${aspread.max():.2f}"
            )
            print(
                "    zone mean LMP: "
                + "  ".join(f"{z}={v:.2f}" for z, v in ameans.items())
            )
            # Model-vs-actual sign agreement on every zone pair (share of the
            # 15 pairwise mean-orderings the model reproduces).
            zones_both = [z for z in pv.columns if z in apv.columns]
            agree = total = 0
            for i, za in enumerate(zones_both):
                for zb in zones_both[i + 1 :]:
                    total += 1
                    if (pv[za].mean() - pv[zb].mean()) * (
                        apv[za].mean() - apv[zb].mean()
                    ) > 0:
                        agree += 1
            print(
                f"    pairwise mean-order sign agreement (model vs {market}): "
                f"{agree}/{total}"
            )

        print(
            "\n[Gate 3] LCR consistency (top %d price hours per zone)" % _SCARCITY_TOP_N
        )
        slack = sy.groupby("zone")["slack"].sum()
        for zone in ("MISO-East", "MISO-South", "MISO-West", "MISO-Illinois"):
            top = pv[zone].nlargest(_SCARCITY_TOP_N).index.to_numpy()
            if zone == "MISO-South":
                util = (net_rdt[top] / rdt_n_to_s).mean()
                cap_name = "RDT N->S"
            else:
                zidx, zsigns = groups[zone]
                net = (zsigns[:, None] * fmat[zidx]).sum(axis=0)
                cil, _ = caps.get(zone, (None, None))
                util = (net[top] / cil[top]).mean() if cil is not None else np.nan
                cap_name = "CIL"
            print(
                f"  {zone:<14} mean import/{cap_name} in scarcity hours: "
                f"{util:6.1%}   slack MWh (year): {slack.get(zone, 0.0):,.0f}"
            )


if __name__ == "__main__":
    main()
