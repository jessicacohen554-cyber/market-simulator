#!/usr/bin/env python
"""FFR-2E probe — diff two capacity-hindcast arms' fleet paths.

Reads the persisted evolution ledgers of a *shipped-posture* bundle and its
*fixed-net-CONE* twin and reports, per solve year, whether the build/retire path
diverges: retirements by reason, additions by channel, the reserve margin and the
end-of-year fleet by fuel. This is the fleet-level half of the FFR-2E posture
measurement (the input-side half is ``_ffr2e_posture_price_sweep.py``).

Comparison only — it reads committed run output and computes nothing that could
feed back into a solve (rules 1 / 14).

Usage::

    python scripts/probes/_ffr2e_arm_diff.py \\
        --shipped results/hindcast/neiso-2021-2025-shipped-ffr2e \\
        --fixed   results/hindcast/neiso-2021-2025-fixed-ffr2e \\
        --iso NEISO
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Ledger scalars compared per year (present directly on the ledger).
SCALARS: tuple[str, ...] = (
    "reserve_margin",
    "peak_demand_mw",
    "firm_clean_mw",
    "storage_firm_mw",
    "storage_power_mw",
    "wind_cap_mw",
    "solar_cap_mw",
    "rps_dual",
)


def _load(bundle: Path, iso: str) -> dict[int, dict]:
    """Return ``{year: ledger}`` for a run out-dir (walks ``<iso>/<key>/``)."""
    ledgers: dict[int, dict] = {}
    for path in sorted(bundle.glob(f"{iso}/*/evolution_*.json")):
        year = int(path.stem.split("_")[1])
        ledgers[year] = json.loads(path.read_text())
    return ledgers


def _retire_mw(led: dict) -> dict[str, float]:
    """Aggregate ``retirements`` rows to ``{reason: MW}`` plus a total."""
    out: dict[str, float] = {}
    for row in led.get("retirements") or []:
        reason = str(row.get("reason") or "unknown")
        out[reason] = out.get(reason, 0.0) + float(row.get("mw", 0.0) or 0.0)
    out["TOTAL"] = sum(out.values())
    return out


def _add_mw(led: dict) -> dict[str, float]:
    """Aggregate the three addition lists to ``{channel: MW}``."""
    out: dict[str, float] = {}
    for key, label in (
        ("thermal_additions", "thermal"),
        ("renewable_additions", "renewable"),
        ("storage_additions", "storage"),
    ):
        rows = [r for r in (led.get(key) or []) if isinstance(r, dict)]
        out[label] = sum(float(r.get("mw", 0.0) or 0.0) for r in rows)
        if key == "thermal_additions":
            # Split by source so an economic-entry change is not masked by a
            # planned-pipeline commissioning that both arms share.
            for row in rows:
                src = str(row.get("source") or "unknown")
                out[f"thermal:{src}"] = out.get(f"thermal:{src}", 0.0) + float(
                    row.get("mw", 0.0) or 0.0
                )
    out["TOTAL"] = (
        out.get("thermal", 0.0) + out.get("renewable", 0.0) + out.get("storage", 0.0)
    )
    return out


def _fleet(led: dict) -> dict[str, float]:
    """End-of-year fleet MW by fuel."""
    fleet = led.get("fleet_by_fuel_after") or {}
    return {k: float(v or 0.0) for k, v in fleet.items()}


def main(argv: list[str] | None = None) -> int:
    """CLI entry point — print the per-year arm diff."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shipped", type=Path, required=True)
    parser.add_argument("--fixed", type=Path, required=True)
    parser.add_argument("--iso", required=True)
    parser.add_argument("--json", help="write the diff to this JSON path")
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    a = _load(args.shipped, iso)
    b = _load(args.fixed, iso)
    years = sorted(set(a) | set(b))
    if not years:
        print("no evolution ledgers found in either bundle")
        return 1

    rows: list[dict] = []
    any_diff = False

    def emit(year: int, group: str, metric: str, va: float, vb: float) -> None:
        nonlocal any_diff
        delta = float(va) - float(vb)
        rows.append(
            {
                "year": year,
                "group": group,
                "metric": metric,
                "shipped": va,
                "fixed": vb,
                "delta": delta,
            }
        )
        if abs(delta) > 1e-6:
            any_diff = True
            print(
                f"{year:>6} {group:<10} {metric:<22} "
                f"{va:>14,.3f} {vb:>14,.3f} {delta:>14,.3f}"
            )

    print(
        f"{'year':>6} {'group':<10} {'metric':<22} {'shipped':>14} {'fixed':>14} {'Δ':>14}"
    )
    print("-" * 90)
    for year in years:
        la, lb = a.get(year) or {}, b.get(year) or {}
        if la.get("bridge") or lb.get("bridge"):
            continue
        for name in SCALARS:
            va, vb = la.get(name), lb.get(name)
            if va is None and vb is None:
                continue
            emit(year, "scalar", name, float(va or 0.0), float(vb or 0.0))
        ra, rb = _retire_mw(la), _retire_mw(lb)
        for reason in sorted(set(ra) | set(rb)):
            emit(year, "retire", reason, ra.get(reason, 0.0), rb.get(reason, 0.0))
        aa, ab = _add_mw(la), _add_mw(lb)
        for channel in sorted(set(aa) | set(ab)):
            emit(year, "add", channel, aa.get(channel, 0.0), ab.get(channel, 0.0))
        fa, fb = _fleet(la), _fleet(lb)
        for fuel in sorted(set(fa) | set(fb)):
            emit(year, "fleet", fuel, fa.get(fuel, 0.0), fb.get(fuel, 0.0))

    if not any_diff:
        print("(no metric differs — the two arms produced the same fleet path)")
    print(f"\nARMS DIVERGE: {any_diff}")

    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {"iso": iso, "diverges": any_diff, "years": years, "rows": rows},
                indent=2,
            )
        )
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
