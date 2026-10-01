"""capx D78-ARM completion — STOP **S4**, checked on the ARMED run alone.

``PRECOMMIT-capx-d78arm-2026-09-06.md`` §5.1 S4, verbatim: the STOP fires on

    "any sector-1 row in ``decided``, ``entry_capped``, ``floor_retained``,
     ``throughput_deferred``, any ``pipeline_events`` row, or ``retirements``
     with ``reason == 'economic'``, in any of the five years; or a year whose
     ledger lacks the ``sector_gated`` block"

This is the identity the mechanism ASSERTS about itself, graded arm-only — no
control leg and zero LP. It reuses ``docs/handoffs/d78/screen_compare.py``'s
``sectors`` / ``sector_of`` readers rather than re-implementing "what sector-1
means", so this lane and D78 / D78-R / D78-R2 cannot drift on the definition.

A unit whose plant code is absent from the 2020-vintage EIA-860 plant table
reads ``"unknown"`` and is NOT counted as a violation — the gate fails OPEN to
the screen for an unknown sector (D32 C5/R3), so an unknown row reaching a
decision ledger is the designed behaviour, not a breach. Counted and reported
separately so the number is visible either way.

    python docs/handoffs/d78arm/s4_identity_check.py --arm <out-dir> [--out <json>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "d78"))

from screen_compare import sector_of, sectors  # noqa: E402  (path-inserted above)

#: The six ledger surfaces S4 names. Each maps a top-level ``evolution_<year>``
#: block to the key its rows carry the unit id under.
LEDGER_BLOCKS: tuple[str, ...] = (
    "decided",
    "entry_capped",
    "floor_retained",
    "throughput_deferred",
    "pipeline_events",
)

#: Row keys a ledger row may carry its unit identity under, in priority order.
UID_KEYS: tuple[str, ...] = ("unit_id", "uid", "id", "plant_unit", "unit")


def _uid(row: object) -> str | None:
    if isinstance(row, str):
        return row
    if isinstance(row, dict):
        for k in UID_KEYS:
            v = row.get(k)
            if isinstance(v, str):
                return v
    return None


def _rows(block: object) -> list:
    """Yield the row objects of a ledger block, whatever shape it ships in."""
    if isinstance(block, list):
        return block
    if isinstance(block, dict):
        out: list = []
        for v in block.values():
            out.extend(_rows(v))
        return out
    return []


def check(arm_dir: Path) -> dict:
    sec = sectors()
    led_dir = next((arm_dir / "PJM").iterdir())
    result: dict = {
        "bundle": str(arm_dir),
        "cache_key": led_dir.name,
        "years": {},
        "violations": [],
        "unknown_sector_rows": 0,
    }
    for path in sorted(led_dir.glob("evolution_*.json")):
        year = path.stem.split("_")[-1]
        led = json.loads(path.read_text())
        yr: dict = {"sector_gated_block": "sector_gated" in led, "counts": {}}
        if not yr["sector_gated_block"]:
            result["violations"].append(
                {"year": year, "kind": "missing sector_gated block"}
            )
        surfaces: list[tuple[str, list]] = [
            (b, _rows(led.get(b))) for b in LEDGER_BLOCKS
        ]
        econ = [
            r
            for r in _rows(led.get("retirements"))
            if isinstance(r, dict) and r.get("reason") == "economic"
        ]
        surfaces.append(("retirements[reason=economic]", econ))
        for name, rows in surfaces:
            n1 = 0
            for row in rows:
                uid = _uid(row)
                if uid is None:
                    continue
                s = sector_of(uid, sec)
                if s == "unknown":
                    result["unknown_sector_rows"] += 1
                elif s == "1":
                    n1 += 1
                    result["violations"].append(
                        {"year": year, "kind": name, "unit_id": uid}
                    )
            yr["counts"][name] = {"rows": len(rows), "sector_1": n1}
        result["years"][year] = yr
    result["S4"] = "PASS" if not result["violations"] else "FIRED"
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    res = check(args.arm)
    print(json.dumps(res, indent=2)[:4000])
    print(f"\nS4: {res['S4']}  ({len(res['violations'])} violation rows)")
    if args.out:
        args.out.write_text(json.dumps(res, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
