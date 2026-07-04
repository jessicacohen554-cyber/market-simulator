#!/usr/bin/env python
"""ADR 0018 validation: compare the three storage-charge policies on one ISO.

Runs a single Mode B (matching-target) sweep three times — once under each
``storage_charge_policy`` (``arbitrage`` / ``excess_clean_only`` /
``excess_headroom_only``) — against an identical load, LMP and CF profile, and
prints the frontier (matching% vs premium) side by side alongside the ADR 0018
``divert_backfill_mwh`` diagnostic. This quantifies what the strict
excess-headroom-only variant costs (extra premium / lost matching) relative to
the divert-and-backfill energy it removes.

Standalone — no ``market_sim`` import (reuses the same intake/profile/LP wiring
as ``examples/run_real_sweep.py`` and ``lce_portfolio.cli``). The LMP is
resolved exactly as ``run_real_sweep.py`` does, so a synthetic (dummy) LMP is
loudly labelled; the comparison across policies is still controlled because all
three share the one resolved LMP.

Run from inside ``scope2-lce-portfolio/``::

    ../.venv/bin/python examples/validate_excess_headroom.py --iso ERCOT
    ../.venv/bin/python examples/validate_excess_headroom.py --iso ERCOT \
        --targets 0.8 0.9 0.95 0.99 1.0 --out validation_ercot.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]  # scope2-lce-portfolio/
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "examples"))

from lce_portfolio.config import PortfolioConfig  # noqa: E402
from lce_portfolio.intake import prepare_lmp, prepare_load  # noqa: E402
from lce_portfolio.profiles import build_cf_matrix, profile_source  # noqa: E402
from lce_portfolio.resources import load_resource_arrays  # noqa: E402
from lce_portfolio.sweep import run_sweep  # noqa: E402
from run_real_sweep import (  # noqa: E402
    PROFILE_SHAPE_YEAR,
    ensure_reference_load,
    generate_dummy_lmp,
    resolve_lmp_path,
)

POLICIES = ("arbitrage", "excess_clean_only", "excess_headroom_only")
DEFAULT_TARGETS = (0.80, 0.90, 0.95, 0.99, 1.00)
DEFAULT_REFERENCE_LOAD = _ROOT / "data" / "reference" / "reference_load_100mw.csv"
DEFAULT_INPUTS_DIR = _ROOT / "data" / "inputs"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iso", default="ERCOT")
    p.add_argument("--year", type=int, default=2030)
    p.add_argument("--targets", type=float, nargs="+", default=list(DEFAULT_TARGETS))
    p.add_argument("--lmp", default=None)
    p.add_argument("--load", default=str(DEFAULT_REFERENCE_LOAD))
    p.add_argument("--out", default=None, help="optional JSON dump of the comparison")
    p.add_argument(
        "--scarcity-hours",
        type=int,
        default=0,
        help="overlay a synthetic scarcity price on the top-N tightest "
        "(highest residual-load) hours, to exercise divert-and-backfill; 0 = "
        "off (use the resolved LMP as-is). Deterministic, clearly synthetic.",
    )
    p.add_argument(
        "--scarcity-price",
        type=float,
        default=2500.0,
        help="$/MWh scarcity price stamped on the --scarcity-hours tightest "
        "hours (default 2500; within ERCOT's ORDC/HCAP scarcity range)",
    )
    args = p.parse_args(argv)

    iso = args.iso.upper()
    load_path = ensure_reference_load(Path(args.load))
    lmp_path, lmp_info = resolve_lmp_path(iso, args.lmp, DEFAULT_INPUTS_DIR, args.year)
    if lmp_path is None:
        lmp_path = generate_dummy_lmp(iso, args.year, DEFAULT_INPUTS_DIR)
        lmp_info = {"source": "generated", "is_synthetic": True, "path": str(lmp_path)}
    if lmp_info["is_synthetic"]:
        print("\n" + "=" * 78)
        print("SYNTHETIC LMP — wiring/mechanism validation only, NOT priced premiums")
        print("=" * 78)
    print(f"ISO={iso}  LMP={lmp_info['source']} ({lmp_path})")
    print(f"profile shape: {profile_source(iso, PROFILE_SHAPE_YEAR)}\n")

    # Shared inputs — resolved once so all three policies see identical data.
    targets = tuple(sorted(args.targets))
    base = PortfolioConfig(
        iso=iso,
        year=args.year,
        mode="matching_target",
        matching_targets=targets,
        profile_shape_year=PROFILE_SHAPE_YEAR,
        load_file=str(load_path),
        lmp_file=str(lmp_path),
    )
    resources = load_resource_arrays(base)
    load = prepare_load(load_path, iso, base)
    lmp = prepare_lmp(lmp_path, iso)
    cf = build_cf_matrix(resources, iso, PROFILE_SHAPE_YEAR, required=True)

    # Optional scarcity overlay (mechanism stress). Divert-and-backfill only
    # occurs when the portfolio is grid-dependent AND a large price spread makes
    # it worth charging storage for a later scarcity hour; the flat reference
    # load + modest-spread synthetic LMP never trigger it (renewables dominate
    # and grid buys → 0). Stamping a scarcity price on the tightest hours — the
    # hours with the least same-hour renewable availability, where a clean
    # portfolio is most grid-exposed — recreates the ERCOT ORDC scarcity signal
    # that makes storage want charging it can only get by diverting. Purely
    # synthetic and deterministic (top-N by residual load, no RNG).
    if args.scarcity_hours > 0:
        renewable = ~resources.is_storage
        # Blended hourly renewable CF, scaled so a portfolio sized to mean-serve
        # load (capacity = load.mean() / mean_CF) has mean availability == mean
        # load. residual = load - that availability is highest exactly in the
        # high-load / low-renewable hours where a clean portfolio is grid-exposed.
        cf_mean = cf[renewable].mean(axis=0)
        avail = cf_mean * (load.mean() / cf_mean.mean())
        residual = load - avail
        tight = np.argsort(residual)[-args.scarcity_hours :]
        lmp = lmp.copy()
        lmp[tight] = np.maximum(lmp[tight], args.scarcity_price)
        print(
            f"scarcity overlay: {args.scarcity_hours} hrs @ ${args.scarcity_price:.0f}"
            f"/MWh on tightest residual-load hours (SYNTHETIC stress)\n"
        )

    # Solve each policy over the same target ladder.
    by_policy: dict[str, list] = {}
    for policy in POLICIES:
        cfg = base.with_overrides(storage_charge_policy=policy)
        sweep = run_sweep(cfg, resources, load, lmp, cf)
        by_policy[policy] = sweep.results

    # ---- report ----
    print(
        f"{'target':>7} | {'policy':<20} | {'match%':>7} | {'premium':>9} | "
        f"{'divert_bf_MWh':>13} | {'grid_buy_MWh':>12} | status"
    )
    print("-" * 92)
    comparison = []
    for i, tgt in enumerate(targets):
        row = {"target": tgt, "policies": {}}
        for policy in POLICIES:
            r = by_policy[policy][i]
            row["policies"][policy] = {
                "matching_pct": r.matching_pct,
                "premium": r.premium,
                "divert_backfill_mwh": r.divert_backfill_mwh,
                "grid_buy_mwh": r.grid_buy_mwh,
                "status": r.status,
            }
            print(
                f"{tgt:>7.2f} | {policy:<20} | {r.matching_pct * 100:>6.2f}% | "
                f"{r.premium:>9.3f} | {r.divert_backfill_mwh:>13.2f} | "
                f"{r.grid_buy_mwh:>12.1f} | {r.status}"
            )
        # premium/matching cost of the strict variant vs arbitrage.
        arb = row["policies"]["arbitrage"]
        hdr = row["policies"]["excess_headroom_only"]
        row["headroom_vs_arbitrage"] = {
            "premium_delta": hdr["premium"] - arb["premium"],
            "matching_delta": hdr["matching_pct"] - arb["matching_pct"],
            "divert_removed_mwh": arb["divert_backfill_mwh"]
            - hdr["divert_backfill_mwh"],
        }
        comparison.append(row)
        print("-" * 92)

    if args.out:
        out = {
            "iso": iso,
            "year": args.year,
            "lmp_source": lmp_info,
            "profile_source": profile_source(iso, PROFILE_SHAPE_YEAR),
            "targets": list(targets),
            "comparison": comparison,
        }
        Path(args.out).write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
