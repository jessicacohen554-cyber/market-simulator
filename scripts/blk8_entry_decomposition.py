#!/usr/bin/env python
"""BLK-8 solar-entry decomposition reporter (RC-0C, plan §1.4 / §3 T-R9).

Reads the per-candidate entry-screen diagnostic ledger a hindcast run emits when
``--entry-screen-diagnostics`` is set (``entry_screen_diagnostics`` in the
evolution ledger) and tabulates, per ISO-year, the term decomposition the RC-0C
attribution table needs:

* revenue: energy / attribute / capacity ($/MW-yr)
* cost: base -> Wright -> post-ITC capex ($/kW), CRF, FOM, annualized hurdle
* the profitability margin and the queue-cap binding state

Diagnostic-only: it reads a ledger produced by a run whose fleet outcome is
byte-identical with or without the diagnostic (the sink has no decision effect).
It never solves an LP and never touches a holdout year.

Usage::

    python scripts/blk8_entry_decomposition.py \
        results/hindcast/pjm-2021-2025-realized-blk8diag [--tech solar]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from market_sim.results.evolution_ledger import (  # noqa: E402
    load_ledgers_for_run,
)


def _find_bundle(out_dir: Path) -> Path:
    """Return the ``results/<iso>/<key>/`` bundle under a hindcast out-dir."""
    meta = out_dir / "meta.json"
    if meta.exists():
        return Path(json.loads(meta.read_text())["bundle"])
    # Fallback: single ISO / key beneath out_dir.
    for iso_dir in out_dir.iterdir():
        if not iso_dir.is_dir():
            continue
        for key_dir in iso_dir.iterdir():
            if key_dir.is_dir() and any(key_dir.glob("evolution_*.json")):
                return key_dir
    raise SystemExit(f"no hindcast bundle found under {out_dir}")


def rows_for_tech(bundle: Path, tech: str) -> list[dict]:
    """Return ``[{year, ...row}]`` diagnostic rows for one technology."""
    ledgers = load_ledgers_for_run(bundle)
    out: list[dict] = []
    for year, led in ledgers.items():
        if led.get("bridge"):
            continue
        for row in led.get("entry_screen_diagnostics", []):
            if row.get("tech") == tech:
                out.append({"year": year, **row})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_dir", type=Path, help="Hindcast run out-dir (or bundle).")
    ap.add_argument("--tech", default="solar", help="Candidate technology.")
    ap.add_argument("--json", action="store_true", help="Emit raw JSON rows.")
    args = ap.parse_args(argv)

    out_dir = args.out_dir
    bundle = out_dir if any(out_dir.glob("evolution_*.json")) else _find_bundle(out_dir)
    rows = rows_for_tech(bundle, args.tech)
    if not rows:
        print(
            f"No {args.tech} diagnostic rows in {bundle}. "
            "Was the run produced with --entry-screen-diagnostics?"
        )
        return 1

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    print(f"# BLK-8 entry decomposition — {args.tech} — {bundle}")
    hdr = (
        f"{'year':>4} {'energy':>9} {'attrib':>8} {'capac':>7} | "
        f"{'hurdle':>9} {'capexITC':>9} {'crf':>6} {'fom':>5} | "
        f"{'margin':>10} {'build_MW':>8} {'binding':>16}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(
            f"{r['year']:>4} "
            f"{r.get('energy_revenue_per_mw_yr', 0):>9.0f} "
            f"{r.get('attribute_revenue_per_mw_yr', 0):>8.0f} "
            f"{r.get('capacity_revenue_per_mw_yr', 0):>7.0f} | "
            f"{r.get('annual_cost_per_mw_yr', 0):>9.0f} "
            f"{r.get('capex_after_credit_per_kw', 0):>9.1f} "
            f"{r.get('crf', 0):>6.4f} "
            f"{r.get('fom_per_kw_yr', 0):>5.0f} | "
            f"{r.get('margin_per_mw_yr', 0):>10.0f} "
            f"{r.get('build_mw', 0):>8.0f} "
            f"{str(r.get('binding_cap', '')):>16}"
        )
    print(
        "\nAll $/MW-yr. hurdle = annualized fixed cost (capex annuity + FOM); "
        "capexITC = $/kW post-Wright post-ITC. capacity=0 for VRE by construction "
        "(BLK-7 / term c)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
