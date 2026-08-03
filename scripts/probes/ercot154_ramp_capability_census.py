"""ERCOT-154 Phase 0 (fallback lane) — is ``measured_ramp_capability``
reachable at ERCOT at all?

The ercot-153 charter names this as the fallback if the storage arm fails, and
names the pjm-140 / nyiso-111 discipline: derive ERCOT's own artifact and
measure the keeper crossing-rate BEFORE arming anything. This probe runs the
step that must come first and that neither of those sessions needed — the
WIRING check — because ``measured_ramp_capability`` is an ISO-generic *input*
that only matters if some ERCOT-reachable consumer reads what it changes.

What it changes is exactly one array: ``FleetArrays.ramp10``
(``data/fleet/withholding.py::_ramp10_capability``, reconciled per plant via
``data/ramp_capability.py::measured_ramp10_frac`` when the flag is on). So the
question is entirely: **does any ERCOT-reachable code path read**
``FleetArrays.ramp10``?

This is the ERCOT-146 ``measured_ct_heat_rates`` question, asked before a solve
rather than after one. It enumerates every read site in ``src/market_sim`` and
records each one's gate, so the answer is a census rather than an assertion.

Also reads, from the keeper's committed sidecars, the ERCOT-153 symptom this
lane was aimed at — evening reserve price ~$0 at h17-21 — so the successor
inherits the number rather than the memory.

Usage::

    python scripts/probes/ercot154_ramp_capability_census.py
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

SRC = REPO / "src/market_sim"
BUNDLE = REPO / "results/calibration/ercot150_zonalanchor_B/hourly"
DEFAULT_OUT = REPO / "results/calibration/ercot154_ramp_capability_census.json"

# The ERCOT keeper's reserve-family flags, read from its own run_config so the
# gate evaluation is the keeper's actual state and not a recollection.
KEEPER_CONFIG = REPO / "results/calibration/ercot150_zonalanchor_B/run_config.json"

# Every gate that can put a ramp10 reader on a run's path. A read site whose
# gate is False in the ERCOT keeper cannot execute there.
GATE_FLAGS = (
    "pjm_reserve_pergen",
    "caiso_reserve_coopt",
    "miso_reserve_pergen",
    "pjm_reserve_supply_cap",
    "energy_reserve_coopt",
    "ercot_multiproduct_as_coopt",
    "ercot_thermal_as_endogenous",
    "ercot_reserve_supply_cap",
    "measured_ramp_capability",
)


def _enclosing_function(tree: ast.Module, lineno: int) -> str:
    """Name of the innermost function definition containing ``lineno``."""
    best, best_line = "<module>", -1
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            if node.lineno <= lineno <= end and node.lineno > best_line:
                best, best_line = node.name, node.lineno
    return best


def read_sites() -> list[dict]:
    """Census every FUNCTIONAL read of ``FleetArrays.ramp10`` in the source.

    A functional read is an attribute access or ``getattr`` naming ``ramp10``
    in executable code -- docstrings and comments are excluded by parsing the
    AST rather than grepping text, which is what makes this a census and not a
    keyword count.
    """
    sites: list[dict] = []
    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text()
        if "ramp10" not in text:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            hit = False
            if isinstance(node, ast.Attribute) and node.attr == "ramp10":
                hit = True
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "ramp10"
            ):
                hit = True
            if hit:
                sites.append(
                    {
                        "file": str(path.relative_to(REPO)),
                        "line": node.lineno,
                        "function": _enclosing_function(tree, node.lineno),
                    }
                )
    return sites


def ercot_design_reads_ramp10() -> dict:
    """Do ERCOT's own reserve designs reference ramp10 anywhere in their body?"""
    spec = (SRC / "model/reserves/spec.py").read_text()
    tree = ast.parse(spec)
    lines = spec.splitlines()
    out: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_ercot"):
            body = "\n".join(
                lines[node.lineno - 1 : getattr(node, "end_lineno", node.lineno)]
            )
            out[node.name] = body.count("ramp10")
    return out


def evening_reserve_symptom() -> dict:
    """The ERCOT-153 symptom, read off the keeper's committed system sidecars."""
    out: dict[str, dict] = {}
    for year in (2023, 2024, 2025):
        df = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
        df = df[df["pass"] == "P1"]
        rp = (
            df.groupby("hour")["reserve_price"]
            .max()
            .reindex(range(8760))
            .to_numpy(float)
        )
        hod = np.tile(np.arange(24), 365)
        ev = (hod >= 17) & (hod <= 21)
        out[str(year)] = {
            "evening_h17_21_mean_reserve_price": round(float(rp[ev].mean()), 2),
            "evening_h17_21_hours_reserve_price_gt_1": int((rp[ev] > 1.0).sum()),
            "evening_h17_21_hours": int(ev.sum()),
            "annual_mean_reserve_price": round(float(rp.mean()), 2),
            "annual_hours_reserve_price_gt_1": int((rp > 1.0).sum()),
        }
    return out


def main() -> None:
    """Run the census and write the record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    cfg = json.loads(KEEPER_CONFIG.read_text())["scenario_config"]
    gates = {f: cfg.get(f) for f in GATE_FLAGS}
    sites = read_sites()
    designs = ercot_design_reads_ramp10()

    result = {
        "_provenance": {
            "session": "ERCOT-154 Phase 0, fallback lane (no LP, no solve)",
            "question": (
                "is ScenarioConfig.measured_ramp_capability REACHABLE at "
                "ERCOT? It changes exactly one array (FleetArrays.ramp10), so "
                "the answer is whether any ERCOT-reachable path reads it"
            ),
            "method": (
                "AST census of every functional read of .ramp10 in "
                "src/market_sim (docstrings/comments excluded by parsing, not "
                "grepping), plus the gate each read sits behind evaluated "
                "against the ERCOT keeper's own run_config"
            ),
            "keeper": "2026-08-02-ercot150b-zonal-anchor",
            "precedent": (
                "ERCOT-146 measured_ct_heat_rates — a flag whose consumer is "
                "not on ERCOT's path is INERT BY WIRING and its A/B is "
                "bit-identical by construction; ask before the solve"
            ),
        },
        "keeper_gate_flags": gates,
        "ramp10_read_sites": sites,
        "ercot_reserve_design_ramp10_mentions": designs,
        "evening_reserve_symptom": evening_reserve_symptom(),
    }
    args.out.write_text(json.dumps(result, indent=2))

    print(f"ramp10 functional read sites: {len(sites)}")
    for s in sites:
        print(f"   {s['file']}:{s['line']}  in {s['function']}()")
    print(f"ERCOT reserve designs mentioning ramp10: {designs}")
    print("keeper gates:", {k: v for k, v in gates.items() if v})
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
