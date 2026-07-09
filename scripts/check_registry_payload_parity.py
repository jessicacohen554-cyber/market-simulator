"""CI gate: every committed registry sidecar must have its run payload.

`scripts/build_manifest.py` silently skips a `registry/<id>.json` sidecar
whose `runs/<id>.js` payload is absent (the "half-synced checkout" guard) —
that is the right behavior for an incomplete local checkout, but it means a
sidecar pushed WITHOUT its payload is invisible in the Run Explorer with no
error anywhere. This happened in practice: several probes (nyiso-54, nyiso-58,
pjm-84, pjm-85, caiso-66) were registered sidecar-only and never rendered
(2026-07 loading-issue investigation). This script makes that failure loud
instead of silent, and additionally catches dangling `ablation_twin` /
`ablation_of` cross-references (a link to a sidecar-only or nonexistent run).

Usage: ``python scripts/check_registry_payload_parity.py`` (exit 1 on any gap).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY_DIR = REPO / "frontend" / "data" / "backcast" / "registry"
RUNS_DIR = REPO / "frontend" / "data" / "backcast" / "runs"
KEEPERS_PATH = REPO / "frontend" / "data" / "backcast" / "keepers.json"


def main() -> int:
    problems: list[str] = []
    sidecars: dict[str, dict] = {}
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: invalid JSON ({exc})")
            continue
        rid = rec.get("id", path.stem)
        sidecars[rid] = rec
        if not (RUNS_DIR / f"{rid}.js").exists():
            problems.append(
                f"{path.name}: registry sidecar has no matching "
                f"runs/{rid}.js payload — invisible in the Run Explorer"
            )

    for rid, rec in sidecars.items():
        for field in ("ablation_twin", "ablation_of"):
            ref = rec.get(field)
            if not ref or not ref.startswith("20"):  # skip prose placeholders
                continue
            if ref not in sidecars:
                problems.append(f"{rid}: {field} -> {ref!r} has no registry sidecar")
            elif not (RUNS_DIR / f"{ref}.js").exists():
                problems.append(
                    f"{rid}: {field} -> {ref!r} has a sidecar but no runs/{ref}.js payload"
                )

    if KEEPERS_PATH.exists():
        keepers = json.loads(KEEPERS_PATH.read_text())
        for rid in keepers.get("keepers", []):
            if rid not in sidecars:
                problems.append(f"keepers.json: keeper {rid!r} has no registry sidecar")
            elif not (RUNS_DIR / f"{rid}.js").exists():
                problems.append(
                    f"keepers.json: keeper {rid!r} has no runs/{rid}.js payload"
                )

    if problems:
        print("registry/payload parity FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print(f"registry/payload parity OK ({len(sidecars)} runs checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
