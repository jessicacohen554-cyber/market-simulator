#!/usr/bin/env python
"""FH-5 Phase B — build the horizon-degradation table from committed scores.

Reads the ``crossover_score.json`` of every registered T1-FF arm (Phase A,
base 2023, and Phase B, base 2021) and emits the per-ISO / per-metric read of
how forward skill decays with horizon.

**Horizon** ``h`` = scored year − base year, i.e. the number of evolution steps
the fleet has taken from the base snapshot (the bridged 2022 counts as a step —
the fleet evolves through it, it is only never *solved*). The two phases score
the SAME three years (2023–2025) against the same actuals, the same bench and
the same keeper comparator, so the pairing holds year effects fixed and moves
only ``h``:

======  ==============  ==============
Year    Phase A (2023)  Phase B (2021)
======  ==============  ==============
2023    h = 0           h = 2
2024    h = 1           h = 3
2025    h = 2           h = 4
======  ==============  ==============

Phase A 2025 and Phase B 2023 are both ``h = 2`` on different calendar years —
the pre-registered control that separates a horizon effect from a year effect.

Solve-independent: it reads committed artifacts only, never a bundle's parquets
and never a solve. Nothing here scores, registers or tunes.

Usage::

    python scripts/probes/fh5_horizon_table.py
    python scripts/probes/fh5_horizon_table.py --json out.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BUNDLE_ROOT = Path("results/hindcast")
ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")
#: The §2.1b metric set. ``co2`` is reported, never a determination input.
METRICS = ("price_mean", "price_shape", "fuelmix")
SCORED_YEARS = (2023, 2024, 2025)


def find_score(run_id: str) -> "Path | None":
    """Return the ``crossover_score.json`` of a registered run, if present.

    The bundle lands under ``<out-dir>/<ISO>/<runtime-key>/`` and the runtime
    key is not knowable from the run id (the D-13 hazard), so this globs for it
    rather than reconstructing the path.

    Args:
        run_id: The registered run id (the bundle directory's basename).

    Returns:
        The score path, or ``None`` when the run is absent or unscored.
    """
    hits = sorted((BUNDLE_ROOT / run_id).glob("*/*/crossover_score.json"))
    return hits[0] if hits else None


def read_arm(run_id: str) -> "dict | None":
    """Return ``{metric: {year: {...}}}`` for one arm, or ``None`` if absent.

    Args:
        run_id: The registered run id.

    Returns:
        The arm's dispatch-skill metric block, plus its base year and keeper
        comparator; ``None`` when the run has not been solved/scored here.
    """
    path = find_score(run_id)
    if path is None:
        return None
    doc = json.loads(path.read_text())
    skill = doc.get("dispatch_skill", {})
    return {
        "base_year": doc.get("base_year"),
        "keeper": skill.get("keeper_run_id"),
        "metrics": skill.get("metrics", {}),
    }


def arm_ids(iso: str) -> dict:
    """Return the four run ids of an ISO's Phase-A / Phase-B arm pair.

    Phase A's ERCOT Arm R doubled as the FH-1 step-0 gate probe, so it carries
    the ``-fh4gate`` suffix rather than ``-fh4`` (protocol §1.2).

    Args:
        iso: ISO name.

    Returns:
        ``{(phase, arm): run_id}`` for phases ``A``/``B`` and arms ``R``/``K``.
    """
    lo = iso.lower()
    a_r = (
        "ercot-2023-2025-t1ff-armr-fh4gate"
        if iso == "ERCOT"
        else f"{lo}-2023-2025-t1ff-armr-fh4"
    )
    return {
        ("A", "R"): a_r,
        ("A", "K"): f"{lo}-2023-2025-t1ff-armk-fh4",
        ("B", "R"): f"{lo}-2021-2025-t1ff-armr-fh5",
        ("B", "K"): f"{lo}-2021-2025-t1ff-armk-fh5",
    }


def collect() -> dict:
    """Return the full nested read for every ISO, arm and phase present.

    Returns:
        ``{iso: {"A"|"B": {"R"|"K": arm-block or None}}}``.
    """
    out: dict = {}
    for iso in ISOS:
        ids = arm_ids(iso)
        out[iso] = {
            phase: {arm: read_arm(ids[(phase, arm)]) for arm in ("R", "K")}
            for phase in ("A", "B")
        }
    return out


def _cell(block: "dict | None", metric: str, year: int) -> "dict | None":
    """Return one (metric, year) score cell from an arm block."""
    if not block:
        return None
    return (block.get("metrics", {}).get(metric, {}) or {}).get(str(year))


def _fmt(cell: "dict | None") -> str:
    """Render one score cell's forecast error, or a dash when unavailable.

    A metric can be absent (arm not solved here) or present-but-null (the
    scorer deferred it for that ISO-year); both print as an em dash rather than
    a fabricated zero.

    Args:
        cell: The score cell, or ``None``.

    Returns:
        A formatted error string.
    """
    if cell is None:
        return "—"
    err = cell.get("forecast_err")
    return "—" if err is None else f"{float(err):.3f}"


def render(data: dict) -> str:
    """Render the horizon-degradation table as markdown.

    Args:
        data: The nested read from :func:`collect`.

    Returns:
        A markdown document: one section per ISO, one table per metric, with
        the h=2 control line appended wherever both of its legs exist.
    """
    lines: list[str] = []
    for iso, phases in data.items():
        have = {
            (p, a)
            for p in ("A", "B")
            for a in ("R", "K")
            if phases[p][a] is not None
        }
        if not have:
            continue
        lines.append(f"\n### {iso}\n")
        keeper = next(
            (phases[p][a]["keeper"] for (p, a) in sorted(have) if phases[p][a]),
            None,
        )
        lines.append(f"Keeper comparator: `{keeper}`\n")
        for metric in METRICS:
            lines.append(f"\n**{metric}**\n")
            lines.append(
                "| Year | h (A) | Arm R err (A) | Arm K err (A) "
                "| h (B) | Arm R err (B) | Arm K err (B) |"
            )
            lines.append("|---|---|---|---|---|---|---|")
            for year in SCORED_YEARS:
                row = [str(year)]
                for phase, base in (("A", 2023), ("B", 2021)):
                    row.append(str(year - base))
                    for arm in ("R", "K"):
                        row.append(_fmt(_cell(phases[phase][arm], metric, year)))
                    # keep column order: h, R, K
                lines.append(
                    "| "
                    + " | ".join(
                        [row[0], row[1], row[2], row[3], row[4], row[5], row[6]]
                    )
                    + " |"
                )
            ctl_a = _cell(phases["A"]["R"], metric, 2025)
            ctl_b = _cell(phases["B"]["R"], metric, 2023)
            if ctl_a and ctl_b and ctl_a.get("forecast_err") is not None:
                lines.append(
                    f"\n*h=2 control (Arm R): 2025@A = {_fmt(ctl_a)} "
                    f"vs 2023@B = {_fmt(ctl_b)} — same horizon, "
                    "different calendar year.*"
                )
    return "\n".join(lines) if lines else "(no scored arms found on disk)"


def main(argv: "list[str] | None" = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument vector (for tests).

    Returns:
        Process exit code (always 0).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None, help="also dump raw JSON")
    args = parser.parse_args(argv)
    data = collect()
    print(render(data))
    if args.json:
        args.json.write_text(json.dumps(data, indent=1))
        print(f"\n[wrote {args.json}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
