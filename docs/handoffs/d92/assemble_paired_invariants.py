#!/usr/bin/env python3
"""Assemble one FC-6 ``paired_invariants.json`` from four SLIM arm records.

capx D92 measurement helper. A shard ships its arm's
``full_horizon_summary.json``, ``run_config.json``, ``config.yaml`` and the 25
``evolution_<year>.json`` — never the multi-GB dispatch cache — so the four
paired rows are assembled here from the artifact grain each row supports. Every
path is validated against the committed ``bau-d46/fc6/paired_invariants.json``
in ``PRECOMMIT-capx-d92-2026-09-10-ADDENDUM-A.md`` §A.2 BEFORE this lane's own
arms existed:

``P1.premise``  :func:`check_forecast_invariants.run_paired_run_configs` — exact.
``P3``          ``run_paired(..., "gas_pm5")`` over LEDGER-ONLY dirs — exact.
``P2``          ``run_paired_summaries(..., "gas_up")`` — exact but for the
                ``objective↑`` sub-check, which the summary grain cannot carry
                and which is reported ``not_scored`` (ADDENDUM A §A.3).
``P1``          the ONE row with no artifact-grain path in the instrument:
                :func:`check_p1_co2_monotone` reads the dispatch parquets. It is
                reproduced here from ``trajectory[].co2_mt`` using the
                instrument's OWN comparison and detail format, having been shown
                to reproduce BOTH operands of the committed d46 row exactly.

Emission shape is the ``--json`` shape (``data`` omitted when ``None``) so the
file is a drop-in for ``forecast_verdict.py --paired-invariants``.

Not standing tooling: the measurement record for
``docs/handoffs/FINDING-capx-d92-2026-09-10.md``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]


def _load_instrument():
    spec = importlib.util.spec_from_file_location(
        "cfi", _REPO / "scripts" / "check_forecast_invariants.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cfi"] = mod
    spec.loader.exec_module(mod)
    return mod


def _cache_dir(arm_dir: Path) -> Path:
    """The one ``<arm>/NEISO/<key>/`` cache directory a leg writes."""
    cands = sorted(p for p in (arm_dir / "NEISO").iterdir() if p.is_dir())
    if len(cands) != 1:
        raise SystemExit(f"{arm_dir}: expected exactly one cache dir, found {len(cands)}")
    return cands[0]


def cumulative_co2_mt(summary: dict) -> float:
    """Sum ``trajectory[].co2_mt`` — the summary-grain cumulative CO2, Mt."""
    return sum(
        float(r["co2_mt"]) for r in summary["trajectory"] if r.get("co2_mt") is not None
    )


def p1_from_summaries(cfi, base: dict, high: dict):
    """P1 on the summary grain, using the instrument's own rule and format."""
    cb, ch = cumulative_co2_mt(base), cumulative_co2_mt(high)
    status = cfi.PASS if ch < cb else cfi.FAIL
    return cfi.Result(
        "P1",
        "CO2 monotone vs carbon",
        status,
        f"cumulative CO2 base {cb:.2f} Mt vs high {ch:.2f} Mt",
    )


def assemble(root: Path) -> list[dict]:
    cfi = _load_instrument()
    arms = {a: root / a for a in ("base", "carbon_plus25", "gasup150", "gaspm5")}
    summ = {
        a: json.loads((d / "full_horizon_summary.json").read_text())
        for a, d in arms.items()
    }
    results = [
        p1_from_summaries(cfi, summ["base"], summ["carbon_plus25"]),
        *[
            r
            for r in cfi.run_paired_run_configs(
                arms["base"] / "run_config.json",
                arms["carbon_plus25"] / "run_config.json",
            )
            if r.ident != "P1"  # the premise row only; P1 above carries the score
        ],
        *cfi.run_paired_summaries(
            arms["base"] / "full_horizon_summary.json",
            arms["gasup150"] / "full_horizon_summary.json",
            "gas_up",
        ),
        *cfi.run_paired(_cache_dir(arms["base"]), _cache_dir(arms["gaspm5"]), "gas_pm5"),
    ]
    return [
        {k: v for k, v in r.__dict__.items() if not (k == "data" and v is None)}
        for r in results
    ]


def main(argv: list[str]) -> int:
    rows = assemble(Path(argv[1]))
    for r in rows:
        print(f"{r['ident']:12} {r['status']:5} {r['detail']}")
    if len(argv) > 2:
        Path(argv[2]).write_text(json.dumps(rows, indent=1) + "\n")
        print(f"\nwrote {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
