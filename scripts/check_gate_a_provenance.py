#!/usr/bin/env python3
"""FAIL when a forecast gate-(a) row cites a superseded keeper or a wrong marker.

THE DEFECT (audit board v17 finding F-5, 2026-08-31). Four of the six
``isos.<ISO>.gate.a_keeper_marker`` rows in
``frontend/data/forecast/program-status.json`` were keyed to keepers their ISO
had already superseded, and ERCOT's was VERDICT-FLIPPING: it read
``complete=False`` while ERCOT had held the rule-22 ``complete`` marker since
2026-08-31, so the board reported gate (a) closed for an ISO that meets it.
Four-instrument alignment broke on a stale stamp rather than on a model fact.

**Nothing caught it, and the reason is a correct design choice.** The gate-(a)
block deliberately avoids the ``forecast-provenance/v1`` field names, so that
``scripts/check_forecast_staleness.py`` can never read a keeper/marker
DERIVATION stamp as evidence of a forecast RE-SCORE (the block says so itself,
in ``gate_a_provenance.note``). That separation is right and this check does
not weaken it: staleness keeps reading only provenance stamps, and the two
instruments never meet.

WHY A SEPARATE SCRIPT rather than a leg inside ``check_forecast_staleness.py``.
The comparison needs the BACKCAST side — the keeper shards and
``calibration-complete.json``. Teaching the staleness checker to open those
would put the backcast instruments inside the forecast-provenance reader and
re-create by the back door exactly the conflation the field-name separation
exists to prevent. Keeping it here makes the split structural: staleness reads
provenance stamps and nothing else; this reads the gate-(a) row, the keeper
shards and the marker file, and touches no provenance stamp.

WHAT IT COMPARES — IDENTITY and MARKER STATE, and nothing else:

1. **Keeper identity.** The run id the row cites must be the ISO's CURRENT
   designated keeper in ``frontend/data/backcast/keepers/<ISO>.json``.
2. **Marker state.** The row's ``marker complete=<bool> final=<bool>`` claim
   must match membership in ``calibration-complete.json``'s two blocks.
3. **Status vs marker, one direction only.** Charter §2.1b(2)(a) makes an entry
   in the ``complete`` block a NECESSARY condition for gate (a), so a row
   reading ``pass`` for an ISO absent from ``complete`` asserts a marker the
   ISO does not hold. The converse is NOT checked: ``complete`` membership is
   necessary, not sufficient (the charter also requires a full-span keeper),
   so a ``fail`` on a ``complete`` ISO is the records lane's derivation to
   make, not this guard's.

WHAT IT DOES **NOT** DO — and this is a hard boundary, not a simplification.
**It never reads, re-derives or asserts a DETERMINATION.** Determinations come
from ``build_status.py``'s partition-aware rollup, and a guard that recomputed
one would stand up a second, competing instrument for the program's most
contested reading. The gate-(a) rows carry determination prose
("determination NOT-YET", "determination CALIBRATED"); this check skips over
it entirely, and the rows themselves say why that is correct — the
determination is *"concurring evidence, not the gate test"*.

ERCOT is the live case that makes the boundary concrete: its ISO-level
determination is the ercot-246 two-config partition rollup **CALIBRATED**
while its registered run-level determination is **NOT-YET**. Both values are
real and neither is "the" determination. This guard reads neither, so it is
correct in that case by construction rather than by picking a side.

FAIL-CLOSED. A row whose keeper citation or marker claim will not parse is
FAILED, not skipped: an unverifiable row is not a verified row, and silently
passing one is how F-5 stayed invisible. The expected phrasings are named in
the failure message so a records lane rewriting the prose knows the contract.

Usage::

    python scripts/check_gate_a_provenance.py           # all ISOs
    python scripts/check_gate_a_provenance.py --iso ERCOT

Stdlib-only (json/re/argparse) so it runs on the bare ``python3`` the stdlib CI
jobs use — no uv sync, no model import, no LP, no solve.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PROGRAM_STATUS = REPO / "frontend" / "data" / "forecast" / "program-status.json"
KEEPERS_DIR = REPO / "frontend" / "data" / "backcast" / "keepers"
CALIBRATION_COMPLETE = (
    REPO / "frontend" / "data" / "backcast" / "calibration-complete.json"
)

#: The gate-(a) row inside ``isos.<ISO>.gate``.
GATE_A_KEY = "a_keeper_marker"

#: The keeper id the row names as ITS SUBJECT — the FIRST ``keeper <run-id>``
#: in the detail prose. A row may name a superseded id later ("RE-KEYED here
#: from <old-id>"), which is history, not the citation; anchoring on the first
#: match is what keeps that from being read as the subject.
KEEPER_CITATION_RE = re.compile(r"\bkeeper\s+(20\d\d-\d\d-\d\d[\w.-]*?)(?=[\s,;(]|$)")

#: The row's marker claim.
MARKER_CLAIM_RE = re.compile(r"\bmarker\s+complete=(True|False)\s+final=(True|False)\b")

#: Non-ISO keys in the keeper store.
NON_ISO_SHARDS = frozenset({"index", "README"})


def load_json(path: Path) -> dict:
    """Read a JSON file, returning ``{}`` when it is absent.

    Args:
        path: File to read.

    Returns:
        The parsed object, or ``{}`` for an absent file (a partial checkout).

    Raises:
        json.JSONDecodeError: The file exists but is not valid JSON — a
            corrupt input must fail loudly, never widen the check.
    """
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def designated_keepers(keepers_dir: Path | None = None) -> dict[str, str]:
    """Read each ISO's CURRENT designated keeper id from its shard.

    Args:
        keepers_dir: Keeper-store override (tests); defaults to this checkout.

    Returns:
        ``{ISO: keeper id}`` for every shard carrying a ``keeper`` field.
    """
    keepers_dir = keepers_dir or KEEPERS_DIR
    out: dict[str, str] = {}
    if not keepers_dir.is_dir():
        return out
    for path in sorted(keepers_dir.glob("*.json")):
        if path.stem in NON_ISO_SHARDS:
            continue
        keeper = load_json(path).get("keeper")
        if isinstance(keeper, str) and keeper:
            out[path.stem] = keeper
    return out


def marker_membership(complete_doc: dict) -> dict[str, tuple[bool, bool]]:
    """Read ``(complete, final)`` membership per ISO from the marker file.

    Keys starting with ``_`` are notes, not ISOs — ``final`` currently holds
    only ``_note``, which is what "``final`` is EMPTY" looks like on disk.

    Args:
        complete_doc: Parsed ``calibration-complete.json``.

    Returns:
        ``{ISO: (in_complete, in_final)}`` over the union of both blocks.
    """
    blocks = {}
    for name in ("complete", "final"):
        block = complete_doc.get(name)
        blocks[name] = (
            {k for k in block if not k.startswith("_")}
            if isinstance(block, dict)
            else set()
        )
    isos = blocks["complete"] | blocks["final"]
    return {iso: (iso in blocks["complete"], iso in blocks["final"]) for iso in isos}


def check_iso(
    iso: str, row: dict, keeper: str | None, membership: tuple[bool, bool]
) -> list[str]:
    """Check one gate-(a) row's identity and marker claims.

    Args:
        iso: ISO code.
        row: The ``gate.a_keeper_marker`` object.
        keeper: The ISO's current designated keeper id, or ``None`` when the
            keeper store holds no shard for it.
        membership: ``(in_complete, in_final)`` from the marker file.

    Returns:
        Human-readable problems; empty when the row is truthful.
    """
    problems: list[str] = []
    detail = str(row.get("detail") or "")
    status = str(row.get("status") or "")
    in_complete, in_final = membership

    # --- 1. keeper IDENTITY -------------------------------------------------
    cited = KEEPER_CITATION_RE.search(detail)
    if not cited:
        problems.append(
            f"{iso}: gate.{GATE_A_KEY}.detail names no keeper id — the row cannot "
            f"be verified, so it is not verified. Expected the phrase "
            f"`keeper <run-id>` (e.g. `keeper 2026-08-25-234-eastex-identity`) "
            f"as the first keeper reference in the detail."
        )
    elif keeper is None:
        problems.append(
            f"{iso}: gate.{GATE_A_KEY} cites keeper {cited.group(1)!r} but the "
            f"keeper store has no keepers/{iso}.json shard to check it against."
        )
    elif cited.group(1) != keeper:
        problems.append(
            f"{iso}: gate.{GATE_A_KEY} cites SUPERSEDED keeper "
            f"{cited.group(1)!r}; the ISO's current designated keeper is "
            f"{keeper!r} (frontend/data/backcast/keepers/{iso}.json). Re-key the "
            f"row against the live keeper (audit board F-5). This guard compares "
            f"identity only — it asserts nothing about either keeper's "
            f"determination."
        )

    # --- 2. marker STATE ----------------------------------------------------
    claim = MARKER_CLAIM_RE.search(detail)
    if not claim:
        problems.append(
            f"{iso}: gate.{GATE_A_KEY}.detail states no marker claim — the row "
            f"cannot be verified, so it is not verified. Expected the phrase "
            f"`marker complete=<True|False> final=<True|False>`."
        )
    else:
        claimed = (claim.group(1) == "True", claim.group(2) == "True")
        if claimed != (in_complete, in_final):
            problems.append(
                f"{iso}: gate.{GATE_A_KEY} claims marker complete={claimed[0]} "
                f"final={claimed[1]}, but calibration-complete.json has "
                f"complete={in_complete} final={in_final}. A gate closed on a "
                f"marker the ISO holds (or opened on one it does not) is the "
                f"verdict-flipping half of F-5."
            )

    # --- 3. status vs marker, necessary-condition direction only ------------
    if status == "pass" and not in_complete:
        problems.append(
            f"{iso}: gate.{GATE_A_KEY} reads `pass` while the ISO is ABSENT from "
            f"the `complete` block. Charter §2.1b(2)(a) makes a `complete` entry "
            f"a NECESSARY condition for gate (a), so this row asserts a marker "
            f"the ISO does not hold."
        )

    return problems


def main(argv: list[str] | None = None) -> int:
    """Run the guard, printing problems to stderr.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code: 0 clean, 1 on any problem.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default=None, help="check one ISO only")
    args = ap.parse_args(argv)

    status_doc = load_json(PROGRAM_STATUS)
    if not status_doc:
        print(
            f"gate-(a) provenance: {PROGRAM_STATUS.relative_to(REPO)} is not in "
            f"this tree — nothing to check (partial checkout)."
        )
        return 0

    keepers = designated_keepers()
    membership = marker_membership(load_json(CALIBRATION_COMPLETE))

    problems: list[str] = []
    notes: list[str] = []
    checked = 0
    isos = status_doc.get("isos") or {}
    for iso in sorted(isos):
        if args.iso and iso != args.iso.upper():
            continue
        row = ((isos[iso] or {}).get("gate") or {}).get(GATE_A_KEY)
        if not isinstance(row, dict):
            notes.append(f"{iso}: no gate.{GATE_A_KEY} row on the board — not checked")
            continue
        checked += 1
        problems.extend(
            check_iso(iso, row, keepers.get(iso), membership.get(iso, (False, False)))
        )

    for iso in sorted(set(keepers) - set(isos)):
        if args.iso and iso != args.iso.upper():
            continue
        notes.append(f"{iso}: has a keeper shard but no entry on the forecast board")

    for note in notes:
        print(f"  note: {note}")

    if problems:
        print("gate-(a) provenance FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print(
        f"gate-(a) provenance OK ({checked} row(s) checked: keeper identity + "
        f"marker state match the backcast store; no determination read)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
