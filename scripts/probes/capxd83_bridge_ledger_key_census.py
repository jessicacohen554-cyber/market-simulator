#!/usr/bin/env python3
"""capx D83 key census — what the bridge-ledger writer repair does to every
committed cache key.

**The question this exists to answer.** The D83 repair (``runner.py``, the
``if is_bridge:`` evolution-ledger writer) restores the eight fleet-state /
accreditation-trail fields a bridge year's ledger was silently dropping. The
charter's binding condition is **ZERO key moves**: a recording repair must not
re-key a single committed bundle, or every existing run would be re-solved to
say the same thing.

**Why the answer should be zero, and why it is still MEASURED.**
``ScenarioConfig.cache_key`` hashes the config payload plus the capx D79
``__solve_surface__`` fingerprint over :data:`~market_sim.config.solve_surface.
SURFACE_MODULES` — seven ``config`` / value modules. ``runner.py`` is not one
of them and is not imported by ``scenarios.py``, so the repair is outside the
key's input set by construction. That is an argument; this probe is the
measurement. It computes the LIVE ``cache_key()`` for every committed
``run_config.json`` payload and writes the census, so the same command run on
the pre-repair tree and the post-repair tree produces two files that must be
byte-identical.

Instrument validation is reported, never silently averaged in: a payload whose
recomputed key does not reproduce its own recorded ``cache_key`` is counted
under ``instrument_mismatch``. Those records still participate in the
before/after diff — the diff is what this lane claims, and it differences the
SAME construction on both sides — but the reproduction count says how much of
the corpus the instrument reads exactly. (The standing census that gates
non-reproducing records against a committed exception list is
``scripts/check_key_provenance.py``; capx D85-R.)

Usage::

    # on the pre-repair tree
    git stash && python3 scripts/probes/capxd83_bridge_ledger_key_census.py \
        --out docs/handoffs/d83/key-census-before.json && git stash pop
    # on the post-repair tree
    python3 scripts/probes/capxd83_bridge_ledger_key_census.py \
        --out docs/handoffs/d83/key-census-after.json
    diff docs/handoffs/d83/key-census-{before,after}.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402


def _committed_run_configs() -> list[Path]:
    """Every ``run_config.json`` tracked by git, forecast and backcast alike."""
    out = subprocess.run(
        ["git", "ls-files", "*run_config.json"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [_REPO / rel for rel in sorted(out)]


def _live_key(payload: dict) -> str | None:
    """The LIVE ``cache_key()`` for one committed payload, or ``None``.

    Fields the payload carries that the live dataclass no longer defines are
    dropped (a retired field cannot be constructed); a payload that still fails
    to build is reported rather than guessed at.
    """
    fields = set(ScenarioConfig.__dataclass_fields__)
    try:
        return ScenarioConfig(
            **{k: v for k, v in payload.items() if k in fields}
        ).cache_key()
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    rows: dict[str, str] = {}
    unbuildable: list[str] = []
    mismatch: list[str] = []
    for path in _committed_run_configs():
        rel = str(path.relative_to(_REPO))
        try:
            doc = json.loads(path.read_text())
        except Exception:
            unbuildable.append(rel)
            continue
        payload = doc.get("scenario_config")
        if not isinstance(payload, dict):
            continue
        key = _live_key(payload)
        if key is None:
            unbuildable.append(rel)
            continue
        rows[rel] = key
        recorded = doc.get("cache_key")
        if isinstance(recorded, str) and recorded != key:
            mismatch.append(rel)

    census = {
        "payloads_hashed": len(rows),
        "instrument_reproduced": len(rows) - len(mismatch),
        "instrument_mismatch": sorted(mismatch),
        "unbuildable": sorted(unbuildable),
        "keys": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(census, indent=1, sort_keys=True) + "\n")
    print(
        f"hashed {len(rows)} committed payloads -> {args.out} "
        f"(reproduced {len(rows) - len(mismatch)}, mismatch {len(mismatch)}, "
        f"unbuildable {len(unbuildable)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
