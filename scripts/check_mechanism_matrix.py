"""Rule-28 [R-MECH-MATRIX] mechanism-matrix guard (CI + local).

Two layers, both stdlib-only (no repo deps, runnable with bare python3):

1. **Integrity validation** (always): `docs/codebase-site/data/mechanism-matrix.js`
   parses to well-formed rows — unique ids, 6-char cell strings over the
   `K R I G O U .` vocabulary, categories resolved, `fc` strings well-formed.
   A malformed matrix silently breaks the explorer page AND the ledger, so it
   hard-fails.

2. **Keeper-stamp drift** (always advisory, escalating in the diff gate):
   `MECH_MATRIX.keepers[ISO]` must equal the id in
   `frontend/data/backcast/keepers/<ISO>.json`. Rule 28 requires the promoting
   session to re-stamp the matrix header when a keeper changes, but nothing
   checked it, so three ISOs drifted silently at once (nyiso-105 missed its
   stamp; ERCOT and CAISO were still on 2026-07-29 ids after 2026-07-31
   promotions). Pre-existing drift only WARNS — it belongs to the owning ISO's
   lane, not to whichever PR happens to run next — but a PR that itself moves
   an ISO's keeper shard without re-stamping the header FAILS, which is
   exactly the duty rule 28 states.

3. **Diff gate** (`--base <ref>`): enforces the mechanical half of rule 28(c) —
   a PR that adds a NEW `ScenarioConfig` field must mention that field in the
   matrix (its own row, or an existing row's `def`/`note` that covers it).
   Mention-anywhere is the deliberate escape hatch: not every new field is its
   own mechanism (paths, sub-scalars of an existing family belong on the
   family's row), so the gate checks registration, not taxonomy. Two advisory
   (non-failing) `::warning::` legs cover rule 28(b): a new backcast registry
   sidecar landing without a matrix touch, and new CLI flags in
   `run_calibration_full.py` absent from the matrix.

Usage:
    python3 scripts/check_mechanism_matrix.py                # validate only
    python3 scripts/check_mechanism_matrix.py --base <sha>   # validate + diff gate

Exit codes: 0 clean, 1 gate failure (new unregistered field, un-restamped keeper
promotion, or malformed matrix).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MATRIX_PATH = "docs/codebase-site/data/mechanism-matrix.js"
SCENARIOS_PATH = "src/market_sim/config/scenarios.py"
CALIB_CLI_PATH = "scripts/run_calibration_full.py"
REGISTRY_PREFIX = "frontend/data/backcast/registry/"
KEEPER_SHARD = "frontend/data/backcast/keepers/{iso}.json"
GAPS_BASELINE_PATH = "docs/codebase-site/data/mechanism-matrix-gaps.json"

# Each ISO's own ScenarioConfig field stems, incl. the regulator prefixes whose
# fields are that ISO's exclusively (NYSDEC rules bind only New York units).
# Matched as `<stem>_`, never as a bare substring, so `carbon_price` is never
# mistaken for a CARB field. Kept in sync with
# scripts/mechanism_matrix_gap_sweep.py::ISO_STEMS.
ISO_STEMS = {
    "ERCOT": ("ercot",),
    "CAISO": ("caiso",),
    "PJM": ("pjm",),
    "MISO": ("miso",),
    "NYISO": ("nyiso", "nysdec"),
    "NEISO": ("neiso",),
}

CELL_CHARS = set("KRIGOU.")
N_ISOS = 6


def _git(*args: str) -> str:
    """Run a git command in the repo root and return stdout (empty on failure)."""
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        )
        return out.stdout
    except subprocess.CalledProcessError:
        return ""


def unbalanced_strings(text: str) -> list[str]:
    """Return errors for `key: "…"` literals holding a raw, unescaped `"`.

    The whole file is one JS object literal, so a single stray double quote
    inside a note truncates that string and cascades into a SyntaxError that
    leaves `window.MECH_MATRIX` unassigned and the explorer page blank. That is
    exactly what happened between nyiso-105 and xiso-1: a D-2 quotation written
    with double quotes broke the file on main, and this checker's regexes did
    not notice because they never parse — they scan.

    Detection without a JS runtime: walk each `key: "` literal to its next
    unescaped `"`, then require the following non-space character to be one of
    `,` `}` `]`. A truncated string lands mid-prose instead, so the next
    character is a letter, digit or punctuation that JS cannot accept there.

    Scanning starts at the `window.MECH_MATRIX` assignment: everything above it
    is the file's block-comment header, whose prose legitimately contains
    `word: "quoted"` shapes that are not string literals at all.
    """
    errors: list[str] = []
    start = text.index("window.MECH_MATRIX")
    for m in re.finditer(r'\b([a-zA-Z_]\w*)\s*:\s*"', text[start:]):
        key = m.group(1)
        i, n = start + m.end(), len(text)
        while i < n:
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == '"':
                break
            i += 1
        j = i + 1
        while j < n and text[j] in " \t\r\n":
            j += 1
        if j < n and text[j] not in ",}]":
            line = text.count("\n", 0, start + m.start()) + 1
            errors.append(
                f"line {line}: `{key}:` string is not closed cleanly — it ends "
                f'before {text[j : j + 40]!r}. A raw `"` inside the text '
                f"truncates it and breaks the whole file; use single quotes."
            )
    return errors


def validate_matrix(text: str) -> list[str]:
    """Return a list of integrity-error strings for the matrix file text."""
    errors: list[str] = []
    if "window.MECH_MATRIX" not in text:
        return ["missing `window.MECH_MATRIX` assignment"]
    errors += unbalanced_strings(text)

    cats = set(re.findall(r'\{\s*id:\s*"([a-z]+)",\s*name:', text))
    ids = re.findall(r'\{\s*id:\s*"([a-z0-9_]+)",\s*cat:\s*"([a-z]+)"', text)
    cells = re.findall(r'cells:\s*"([^"]*)"', text)
    fcs = re.findall(r'fc:\s*"([^"]*)"', text)

    if not ids:
        errors.append("no rows found (id/cat pattern matched nothing)")
    if len(ids) != len(cells):
        errors.append(f"{len(ids)} rows but {len(cells)} `cells:` strings")

    seen: set[str] = set()
    for row_id, cat in ids:
        if row_id in seen:
            errors.append(f"duplicate row id `{row_id}`")
        seen.add(row_id)
        if cat not in cats:
            errors.append(f"row `{row_id}` references unknown category `{cat}`")

    for s in cells + fcs:
        if len(s) != N_ISOS or not set(s) <= CELL_CHARS:
            errors.append(
                f"bad cell string `{s}` (need {N_ISOS} chars of K/R/I/G/O/U/.)"
            )
    return errors


def matrix_isos(text: str) -> list[str]:
    """Return the matrix's `isos:` list, in cell order."""
    m = re.search(r"isos:\s*\[([^\]]*)\]", text)
    return re.findall(r'"([A-Z]+)"', m.group(1)) if m else []


def matrix_keepers(text: str) -> dict[str, str]:
    """Return the matrix header's `keepers:` map, `{ISO: keeper_id}`."""
    m = re.search(r"keepers:\s*\{([^}]*)\}", text)
    if not m:
        return {}
    return dict(re.findall(r'([A-Z]+):\s*"([^"]*)"', m.group(1)))


def shard_keeper(iso: str) -> str | None:
    """Return the keeper id from an ISO's keeper shard, or None if unreadable."""
    path = REPO / KEEPER_SHARD.format(iso=iso)
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("keeper") or "")
    except (OSError, ValueError):
        return None


def keeper_drift(text: str) -> list[tuple[str, str, str]]:
    """Return `(iso, header_id, shard_id)` for every ISO whose stamp disagrees."""
    header = matrix_keepers(text)
    drift: list[tuple[str, str, str]] = []
    for iso in matrix_isos(text):
        shard = shard_keeper(iso)
        if shard is None:
            continue  # no shard on disk: not this guard's business
        if header.get(iso, "") != shard:
            drift.append((iso, header.get(iso, "<missing>"), shard))
    return drift


def scenarioconfig_fields(source: str) -> set[str]:
    """Extract ScenarioConfig dataclass field names from scenarios.py source."""
    m = re.search(r"^class ScenarioConfig\b", source, re.M)
    if not m:
        return set()
    body = source[m.end() :]
    end = re.search(r"^(?:class |def |@dataclass)", body, re.M)
    if end:
        body = body[: end.start()]
    return {
        name
        for name in re.findall(r"^    ([a-z][a-z0-9_]*)\s*:", body, re.M)
        if not name.startswith("_")
    }


def cli_flags(source: str) -> set[str]:
    """Extract --flag names added via argparse in a runner script."""
    return set(re.findall(r'add_argument\(\s*"(--[a-z0-9-]+)"', source))


def gap_ratchet(matrix_text: str, source: str) -> list[str]:
    """Errors for ISO-scoped fields absent from BOTH the matrix and the baseline.

    Closes the standing blind spot the nyiso-113/114 census measured: the diff
    gate above enforces rule 28(c) only for fields **added in the same PR**, so
    every field predating that gate is structurally invisible to it. The census
    found **161 ISO-scoped fields absent from the matrix across the six ISOs,
    95 of them armed on a keeper** — none of which any CI run could see.

    A full audit cannot be a hard gate today (that backlog is each ISO lane's
    own work, and rule 25/28(d) forbid one lane minting verdict-bearing rows for
    another's market). So this is a RATCHET: the committed baseline
    ``mechanism-matrix-gaps.json`` enumerates the known-absent fields per ISO,
    and a field absent from the matrix AND absent from the baseline FAILS. The
    list can only shrink — a new ISO-scoped field must land with its
    registration, and closing a legacy gap refreshes the baseline
    (``scripts/mechanism_matrix_gap_sweep.py --write-baseline``).

    Stdlib-only by the same contract as the rest of this checker: field names
    come from the ``scenarios.py`` regex, not from importing ``market_sim``.
    """
    path = REPO / GAPS_BASELINE_PATH
    if not path.exists():
        return []
    try:
        allowed = json.loads(path.read_text(encoding="utf-8")).get("absent", {})
    except (OSError, ValueError) as exc:
        return [f"{GAPS_BASELINE_PATH} is unreadable ({exc})"]
    fields = scenarioconfig_fields(source)
    out: list[str] = []
    for iso, stems in ISO_STEMS.items():
        allow = set(allowed.get(iso, ()))
        for f in sorted(fields):
            if not any(f.startswith(f"{s}_") for s in stems):
                continue
            # Same stem convention as the matrix itself: a per-ISO flag is that
            # ISO's leg of an ISO-neutral family row, so the family name (the
            # field minus its ISO prefix) counts as registration.
            #
            # SUBSTRING, not `\b`: a stem sits mid-identifier in the row that
            # owns it (`gas_bridge_startup` inside `nyiso_gas_bridge_startup`),
            # where the preceding `_` is a word character and `\b` never
            # matches. Using `\b` here made the ratchet fire on seven fields the
            # sweep counts as registered — so the two disagreed and the baseline
            # could never be satisfied. This must stay identical to
            # ``mechanism_matrix_gap_sweep.coverage``, which writes the baseline.
            stem = next((f[len(s) + 1 :] for s in stems if f.startswith(f"{s}_")), f)
            named = f in matrix_text or (stem and stem in matrix_text)
            if not named and f not in allow:
                out.append(
                    f"{iso}-scoped field `{f}` is in neither {MATRIX_PATH} nor "
                    f"the {GAPS_BASELINE_PATH} ratchet (rule 28c). Add its row "
                    f"(or name it in the owning family row's def/note)."
                )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="git ref to diff against (PR base sha)")
    args = parser.parse_args()

    matrix_text = (REPO / MATRIX_PATH).read_text(encoding="utf-8")
    errors = validate_matrix(matrix_text)
    for e in errors:
        print(f"::error file={MATRIX_PATH}::mechanism-matrix integrity: {e}")
    if errors:
        return 1
    print(f"mechanism-matrix: integrity OK ({MATRIX_PATH})")

    # --- rule 28: header keeper stamp vs the per-ISO keeper shard -------------
    drift = keeper_drift(matrix_text)
    if not drift:
        print("mechanism-matrix: keeper stamps match every keepers/<ISO>.json")
    if not args.base:
        for iso, header, shard in drift:
            print(
                f"::warning file={MATRIX_PATH}::{iso} keeper stamp drift: header "
                f"`{header}` != keepers/{iso}.json `{shard}` (rule 28). The "
                f"promoting session re-stamps the header in the same session."
            )
        return 0

    changed = _git("diff", "--name-only", args.base, "HEAD").splitlines()
    matrix_touched = MATRIX_PATH in changed

    # --- rule 28(c): new ScenarioConfig fields must be registered ------------
    failed = False

    # A PR that MOVES a keeper shard owns that ISO's header stamp: fail. Drift
    # this PR did not create only warns — it belongs to the owning ISO's lane.
    for iso, header, shard in drift:
        if KEEPER_SHARD.format(iso=iso) in changed:
            failed = True
            print(
                f"::error file={MATRIX_PATH}::{iso} keeper promoted to `{shard}` in "
                f"this PR but the matrix header still reads `{header}`. Rule 28 "
                f"[R-MECH-MATRIX]: the promoting session re-stamps the header (and "
                f"re-checks that ISO's column) in the SAME session."
            )
        else:
            print(
                f"::warning file={MATRIX_PATH}::{iso} keeper stamp drift (pre-existing, "
                f"not this PR): header `{header}` != keepers/{iso}.json `{shard}`. "
                f"Belongs to the {iso} lane."
            )
    if SCENARIOS_PATH in changed:
        base_src = _git("show", f"{args.base}:{SCENARIOS_PATH}")
        head_src = (REPO / SCENARIOS_PATH).read_text(encoding="utf-8")
        new_fields = scenarioconfig_fields(head_src) - scenarioconfig_fields(base_src)
        for field in sorted(new_fields):
            if not re.search(rf"\b{re.escape(field)}\b", matrix_text):
                failed = True
                print(
                    f"::error file={SCENARIOS_PATH}::new ScenarioConfig field "
                    f"`{field}` is not registered in {MATRIX_PATH} (rule 28c "
                    f"[R-MECH-MATRIX]). Add a row for the mechanism, or name the "
                    f"field in the owning row's def/note."
                )
        if new_fields and not failed:
            print(f"mechanism-matrix: {len(new_fields)} new field(s) all registered")

    # --- rule 28(c) RATCHET: ISO-scoped fields absent from matrix AND baseline
    ratchet = gap_ratchet(matrix_text, (REPO / SCENARIOS_PATH).read_text("utf-8"))
    for e in ratchet:
        failed = True
        print(f"::error file={SCENARIOS_PATH}::mechanism-matrix gap ratchet: {e}")
    if not ratchet:
        print("mechanism-matrix: gap ratchet OK (no new ISO-scoped field is invisible)")

    # --- rule 28(b) advisories ----------------------------------------------
    added = _git(
        "diff", "--name-only", "--diff-filter=A", args.base, "HEAD"
    ).splitlines()
    new_runs = [p for p in added if p.startswith(REGISTRY_PREFIX)]
    if new_runs and not matrix_touched:
        print(
            f"::warning::PR registers {len(new_runs)} new backcast run(s) but does "
            f"not touch {MATRIX_PATH}. If this run tested a mechanism (probe, "
            f"candidate, or keeper), rule 28b requires its cell verdict updated in "
            f"the same session. Ignore if the run re-exercises an already-recorded "
            f"recipe."
        )
    if CALIB_CLI_PATH in changed:
        base_cli = _git("show", f"{args.base}:{CALIB_CLI_PATH}")
        head_cli = (REPO / CALIB_CLI_PATH).read_text(encoding="utf-8")
        for flag in sorted(cli_flags(head_cli) - cli_flags(base_cli)):
            token = flag.lstrip("-").replace("-", "_")
            if not re.search(rf"\b{re.escape(token)}\b", matrix_text):
                print(
                    f"::warning::new calibration CLI flag `{flag}` is not mentioned "
                    f"in {MATRIX_PATH}. If it arms a solve-affecting mechanism, add "
                    f"or extend its row (rule 28c)."
                )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
