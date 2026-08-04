"""FFR-4B probe reader: compare the lane's four MISO entry-screen arms.

Reads each arm's per-year capacity-evolution ledgers straight out of its own
cache directory — ``<out-dir>/MISO/<cache_key>/evolution_<year>.json``, NOT
the out-dir root (FFR-3C blocker 10: :func:`load_ledgers_for_run` returns
``{}`` rather than raising, so a wrong path reads as "no evolution happened",
which in an entry-screen lane looks exactly like a null result).

Prints, per arm and decision year: the ``entry_screen_diagnostics`` row for
every VRE candidate (revenue decomposition, annualized fixed cost, margin,
binding cap), the adequacy state (peak, reserve margin), and the realized
build by technology — so the gate leg and the accreditation leg can each be
read alone against the paired control.

Usage::

    uv run python scripts/probes/ffr4b_read_arms.py <label>=<out-dir> ...
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_arm(out_dir: Path) -> dict[int, dict]:
    """Return ``{year: ledger}`` for the single cache key under ``out_dir``."""
    iso_dir = out_dir / "MISO"
    if not iso_dir.is_dir():
        return {}
    ledgers: dict[int, dict] = {}
    for key_dir in sorted(p for p in iso_dir.iterdir() if p.is_dir()):
        for path in sorted(key_dir.glob("evolution_*.json")):
            try:
                year = int(path.stem.replace("evolution_", ""))
            except ValueError:
                continue
            payload = json.loads(path.read_text())
            payload["_cache_key"] = key_dir.name
            ledgers[year] = payload
    return dict(sorted(ledgers.items()))


def build_by_tech(ledger: dict) -> dict[str, float]:
    """Aggregate the year's realized additions to ``{tech: MW}``."""
    out: dict[str, float] = {}
    for row in ledger.get("renewable_additions", []):
        out[row["tech"]] = out.get(row["tech"], 0.0) + float(row["mw"])
    for row in ledger.get("thermal_additions", []):
        key = f"{row['fuel']}[{row.get('source', '?')}]"
        out[key] = out.get(key, 0.0) + float(row["mw"])
    for row in ledger.get("storage_additions", []):
        out["storage"] = out.get("storage", 0.0) + float(row["mw"])
    return out


def print_arm(label: str, out_dir: Path) -> dict[int, dict]:
    """Print one arm's decision-year screen rows and adequacy state."""
    ledgers = load_arm(out_dir)
    print(f"\n{'=' * 78}\nARM {label}   {out_dir}")
    if not ledgers:
        print("  NO LEDGERS FOUND — check the path (rule: <out-dir>/MISO/<key>/)")
        return {}
    keys = {lg["_cache_key"] for lg in ledgers.values()}
    print(f"  cache_key(s): {sorted(keys)}   years: {sorted(ledgers)}")
    for year, lg in ledgers.items():
        # A bridge year evolves but never solves, so its ledger carries None
        # for the solved-state fields — print them as 0 rather than crashing.
        peak = lg.get("peak_demand_mw") or 0.0
        rm = lg.get("reserve_margin") or 0.0
        print(f"\n  --- {year}  peak={peak:,.0f} MW  reserve_margin={rm:.4%}")
        rows = lg.get("entry_screen_diagnostics") or []
        for row in rows:
            tech = row.get("tech", "?")
            if tech not in ("solar", "wind"):
                continue
            print(
                f"      {tech:<8} margin={row.get('margin_per_mw_yr', 0.0):>12,.0f}"
                f"  energy={row.get('energy_revenue_per_mw_yr', 0.0):>10,.0f}"
                f"  attr={row.get('attribute_revenue_per_mw_yr', 0.0):>9,.0f}"
                f"  cap={row.get('capacity_revenue_per_mw_yr', 0.0):>10,.0f}"
                f"  cost={row.get('annual_cost_per_mw_yr', 0.0):>10,.0f}"
                f"  cap_bind={row.get('binding_cap', '?')}"
                f"  mw={row.get('build_mw', 0.0):>9,.1f}"
            )
        for row in rows:
            tech = row.get("tech", "?")
            if tech in ("solar", "wind"):
                continue
            print(
                f"      {tech:<8} margin={row.get('margin_per_mw_yr', 0.0):>12,.0f}"
                f"  cap_rev={row.get('capacity_revenue_per_mw_yr', 0.0):>10,.0f}"
                f"  cap_bind={row.get('binding_cap', '?')}"
                f"  mw={row.get('build_mw', 0.0):>9,.1f}"
            )
        built = build_by_tech(lg)
        if built:
            print(
                "      BUILT: "
                + ", ".join(f"{k}={v:,.1f}" for k, v in sorted(built.items()))
            )
        rets = lg.get("retirements", [])
        if rets:
            by_reason: dict[str, float] = {}
            for r in rets:
                by_reason[r["reason"]] = by_reason.get(r["reason"], 0.0) + float(r["mw"])
            print(
                "      RETIRED: "
                + ", ".join(f"{k}={v:,.1f}" for k, v in sorted(by_reason.items()))
            )
    return ledgers


def main(argv: list[str]) -> int:
    """Print every arm named on the command line, then a cumulative summary."""
    if not argv:
        print(__doc__)
        return 2
    arms: dict[str, dict[int, dict]] = {}
    for spec in argv:
        label, _, path = spec.partition("=")
        arms[label] = print_arm(label, Path(path))
    print(f"\n{'=' * 78}\nCUMULATIVE BUILD BY ARM (MW commissioned, all years)")
    techs: set[str] = set()
    totals: dict[str, dict[str, float]] = {}
    for label, ledgers in arms.items():
        agg: dict[str, float] = {}
        for lg in ledgers.values():
            for tech, mw in build_by_tech(lg).items():
                agg[tech] = agg.get(tech, 0.0) + mw
        totals[label] = agg
        techs |= set(agg)
    header = "  " + "tech".ljust(26) + "".join(lbl.rjust(14) for lbl in arms)
    print(header)
    for tech in sorted(techs):
        line = "  " + tech.ljust(26)
        for label in arms:
            line += f"{totals[label].get(tech, 0.0):>14,.1f}"
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
