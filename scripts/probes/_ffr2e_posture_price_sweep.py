#!/usr/bin/env python
"""FFR-2E probe — analytic (LP-free) capacity-price divergence, shipped vs fixed.

Sweeps the ONE shared capacity-price seam
(:meth:`market_sim.config.capacity_market.MarketDesign.capacity_price_per_firm_mw_yr`,
rule 19) across the reserve-position domain for both postures a capacity
hindcast can run:

* **shipped** — the production ``ScenarioConfig`` defaults, i.e.
  ``capacity_market_clearing_by_iso`` left at its dataclass default
  (``{"PJM": True, "MISO": True, "CAISO": True, "NEISO": True}``);
* **fixed**   — ``capacity_market_clearing_by_iso=None`` + the scalar off, the
  pre-FFR-2E harness default and the flat net-CONE comparison arm.

This is the *input-side* half of the FFR-2E measurement: it says exactly where
in (ISO, solve year, reserve position) the two arms feed different $/firm-MW-yr
into the retirement / thermal-entry / VRE-entry / storage-entry screens. It
tunes nothing and solves no LP; the fleet-level consequence is the paired
capacity-hindcast legs the findings doc registers.

Reads only published registry parameters (rule 13) — every number traces to
``data/raw/capacity-market/demand-curve`` via ``MARKET_DESIGN`` /
``MARKET_DESIGN_VINTAGES``.

Usage::

    python scripts/probes/_ffr2e_posture_price_sweep.py --json out.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field

from market_sim.config.capacity_market import (
    MARKET_DESIGN,
    MARKET_DESIGN_VINTAGES,
    resolve_capacity_market_clearing,
    resolve_demand_curve_vintage,
)
from market_sim.config.scenarios import ScenarioConfig

# Reserve positions swept: accredited firm capacity / the shared adequacy
# requirement. The published curves live on [0.95, 1.10]; the sweep brackets
# every ISO's cap point and zero-cross (or floor) with a fine enough grid to
# resolve the piecewise-linear kinks.
SWEEP_POSITIONS: tuple[float, ...] = (
    0.95,
    0.97,
    0.99,
    1.00,
    1.01,
    1.015,
    1.02,
    1.03,
    1.045,
    1.06,
    1.08,
    1.10,
    1.15,
)

# Solve years probed. 2021/2023-2025 is the T1-H hindcast window; 2026-2028 is
# the T0 window that reaches PJM's 2028/29 vintage (the FFR-2C re-anchor whose
# published price floor removes the demand curve's zero-cross).
SWEEP_YEARS: tuple[int, ...] = (2021, 2023, 2024, 2025, 2026, 2027, 2028)


@dataclass
class _FixedArmConfig:
    """Minimal duck-typed config for the fixed net-CONE arm.

    The seam reads both clearing fields through ``getattr``, so the arm needs
    no ``ScenarioConfig`` construction (which would drag the whole validation
    surface in for a two-field read).
    """

    capacity_market_clearing: bool = False
    capacity_market_clearing_by_iso: dict[str, bool] | None = None


@dataclass
class _ShippedArmConfig:
    """Duck-typed mirror of the production ``ScenarioConfig`` clearing fields."""

    capacity_market_clearing: bool = field(
        default_factory=lambda: bool(ScenarioConfig.capacity_market_clearing)
    )
    capacity_market_clearing_by_iso: dict[str, bool] | None = field(
        default_factory=lambda: _production_by_iso_default()
    )


def _production_by_iso_default() -> dict[str, bool] | None:
    """Return the ``capacity_market_clearing_by_iso`` production default.

    Read off the dataclass field so the probe follows a future owner flip
    (FFR-3A step 0) without an edit here — never a hardcoded copy (rule 24).
    """
    fields = getattr(ScenarioConfig, "__dataclass_fields__", {})
    spec = fields.get("capacity_market_clearing_by_iso")
    if spec is None:
        return None
    factory = getattr(spec, "default_factory", None)
    if factory is None or factory is getattr(spec, "MISSING", None):
        return None
    try:
        return dict(factory())
    except TypeError:  # pragma: no cover - defensive; field has a plain default
        return None


def sweep_iso(iso: str) -> dict:
    """Return the per-(year, position) price pair for one ISO, both arms."""
    design = MARKET_DESIGN[iso]
    shipped = _ShippedArmConfig()
    fixed = _FixedArmConfig()
    rows: list[dict] = []
    for year in SWEEP_YEARS:
        vintage = resolve_demand_curve_vintage(iso, year)
        for pos in SWEEP_POSITIONS:
            p_shipped = design.capacity_price_per_firm_mw_yr(
                shipped, pos, iso=iso, year=year
            )
            p_fixed = design.capacity_price_per_firm_mw_yr(
                fixed, pos, iso=iso, year=year
            )
            rows.append(
                {
                    "year": year,
                    "delivery_year": (
                        vintage.delivery_year if vintage is not None else ""
                    ),
                    "reserve_position": pos,
                    "shipped_usd_per_firm_mw_yr": p_shipped,
                    "fixed_usd_per_firm_mw_yr": p_fixed,
                    "delta_usd": p_shipped - p_fixed,
                    "ratio": (p_shipped / p_fixed) if p_fixed else None,
                }
            )
    return {
        "iso": iso,
        "clearing_gate_shipped": resolve_capacity_market_clearing(
            _ShippedArmConfig(), iso
        ),
        "clearing_gate_fixed": resolve_capacity_market_clearing(_FixedArmConfig(), iso),
        "registry_has_curve": bool(design.demand_curve or design.seasonal_rbdc),
        "fixed_anchor_per_kw_yr": design.net_cone_per_kw_yr,
        "vintage_count": len(MARKET_DESIGN_VINTAGES.get(iso, ())),
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point — print the divergence table and optionally dump JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="write the full sweep to this JSON path")
    args = parser.parse_args(argv)

    out = {"isos": [sweep_iso(iso) for iso in MARKET_DESIGN]}
    for block in out["isos"]:
        iso = block["iso"]
        diverging = [r for r in block["rows"] if abs(r["delta_usd"]) > 1e-9]
        print("=" * 78)
        print(
            f"{iso}: shipped gate={block['clearing_gate_shipped']} "
            f"fixed gate={block['clearing_gate_fixed']} "
            f"registry curve={block['registry_has_curve']} "
            f"fixed anchor=${block['fixed_anchor_per_kw_yr']}/kW-yr"
        )
        if not diverging:
            print("   NO DIVERGENCE anywhere in the swept domain (arms identical)")
            continue
        years = sorted({r["year"] for r in diverging})
        print(f"   diverges in solve years: {years}")
        for year in years:
            yr_rows = [r for r in diverging if r["year"] == year]
            dy = yr_rows[0]["delivery_year"]
            lo = min(yr_rows, key=lambda r: r["delta_usd"])
            hi = max(yr_rows, key=lambda r: r["delta_usd"])
            print(
                f"   {year} (DY {dy}): "
                f"min Δ ${lo['delta_usd']:>12,.0f} @ pos {lo['reserve_position']}"
                f"  |  max Δ ${hi['delta_usd']:>12,.0f} @ pos {hi['reserve_position']}"
            )
        # The long-position tail is where a price FLOOR (a non-zero rightmost
        # curve point) shows up: flat-extrapolation carries it out forever.
        tail = [
            r for r in block["rows"] if r["reserve_position"] == max(SWEEP_POSITIONS)
        ]
        for r in tail:
            if r["shipped_usd_per_firm_mw_yr"] > 0.0:
                print(
                    f"   FLOOR at pos {r['reserve_position']} year {r['year']}: "
                    f"shipped ${r['shipped_usd_per_firm_mw_yr']:,.0f} vs "
                    f"fixed ${r['fixed_usd_per_firm_mw_yr']:,.0f}"
                )

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
