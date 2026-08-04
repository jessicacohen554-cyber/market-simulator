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
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MATRIX_PATH = "docs/codebase-site/data/mechanism-matrix.js"
MATRIX_DOC_PATH = "docs/mechanism-testing-matrix.md"
SCENARIOS_PATH = "src/market_sim/config/scenarios.py"
CALIB_CLI_PATH = "scripts/run_calibration_full.py"
REGISTRY_PREFIX = "frontend/data/backcast/registry/"
KEEPER_SHARD = "frontend/data/backcast/keepers/{iso}.json"
GAPS_BASELINE_PATH = "docs/codebase-site/data/mechanism-matrix-gaps.json"
ANCHORS_BASELINE_PATH = "docs/codebase-site/data/mechanism-matrix-anchors.json"

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


# A §5.x per-ISO prose section header, e.g. "### 5.4 MISO — target C7 ...".
DOC_SECTION_RE = re.compile(r"^### 5\.\d+ ([A-Z]+)\b.*$", re.M)
# A run id as it appears in the prose, backtick-quoted: `2026-08-04-miso-124-...`.
DOC_RUN_ID_RE = re.compile(r"`(20\d\d-\d\d-\d\d-[A-Za-z0-9._-]+)`")


def doc_header_sections(doc_text: str) -> dict[str, list[str]]:
    """Return `{ISO: [full header line, ...]}` for the §5.x prose sections.

    A list, not a single line, because duplicates are a real failure mode: §5.5
    NYISO had accumulated THREE `### 5.5` headers from merge races (sessions
    prepending a header + STATUS block instead of re-stamping the one header).
    """
    out: dict[str, list[str]] = {}
    for m in DOC_SECTION_RE.finditer(doc_text):
        out.setdefault(m.group(1), []).append(m.group(0))
    return out


def doc_header_drift(doc_text: str) -> list[tuple[str, str, str]]:
    """Return `(iso, reason, shard_id)` per §5.x prose header that is stale.

    Rule 28 [R-MECH-MATRIX] makes the promoting session re-stamp "the matrix
    header". `keeper_drift` above has always guarded the machine-readable
    `keepers:` map in the matrix JS — but NOT the prose per-ISO headers in
    ``docs/mechanism-testing-matrix.md``, and that asymmetry is precisely how
    four of six drifted undetected while CI stayed green (xiso-4, 2026-08-04:
    PJM and NYISO carried superseded keeper ids, NYISO's header additionally
    asserted a superseded DETERMINATION — CALIBRATED-WITH-CAVEATS after
    nyiso-120 moved it to NOT-YET — MISO carried no live stamp at all, and
    §5.5 carried three duplicate headers).

    Deliberately WEAK: it asserts only that the shard's keeper id appears
    somewhere in that ISO's header line, and that there is exactly one header
    per ISO. It does not police wording, determination text or ordering —
    catching staleness without dictating prose.
    """
    out: list[tuple[str, str, str]] = []
    for iso, headers in sorted(doc_header_sections(doc_text).items()):
        shard = shard_keeper(iso)
        if shard is None:
            continue  # no shard on disk: not this guard's business
        if len(headers) > 1:
            out.append(
                (iso, f"{len(headers)} duplicate `### 5.x {iso}` headers", shard)
            )
            continue
        if shard not in DOC_RUN_ID_RE.findall(headers[0]):
            out.append((iso, "header does not name the designated keeper", shard))
    return out


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


def _scenarioconfig_defaults(source: str) -> dict[str, object]:
    """``ScenarioConfig`` field -> shipped default, parsed WITHOUT importing.

    The mechanism-matrix guard runs stdlib-only (no ``uv sync``), so the default
    values have to come out of the source text. Only simple literal defaults are
    parsed — ``bool``/``int``/``float``/``str``/``None``/tuple. Anything the
    parser cannot read (a ``field(default_factory=...)``, a computed default) is
    OMITTED, which makes the shared ratchet below CONSERVATIVE by construction:
    it can only ever gate fewer fields than
    ``mechanism_matrix_gap_sweep``, which imports the live class and writes the
    baseline. That direction matters — a checker STRICTER than the sweep would
    demand a baseline the sweep can never write, which is precisely how the
    ``\\b``-vs-substring mismatch made the earlier ratchet unsatisfiable.
    """
    out: dict[str, object] = {}
    for m in re.finditer(
        r"^    (?P<name>[a-z_][a-z0-9_]*)\s*:\s*[^=\n]+?=\s*(?P<default>.+?)\s*$",
        source,
        re.MULTILINE,
    ):
        raw = m.group("default").split("  #")[0].strip()
        try:
            out[m.group("name")] = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            continue  # not a literal — omitted on purpose (see docstring)
    return out


def _keeper_run_config(iso: str) -> dict:
    """The ISO's designated keeper's committed ``run_config.json`` scenario block.

    keepers/<ISO>.json -> registry/<id>.json -> the bundle's run_config.json,
    every hop a committed file, so this stays stdlib-only and needs no solve.
    Returns ``{}`` when any hop is missing, which SKIPS the shared ratchet for
    that ISO rather than failing it — a keeper whose bundle is not in the
    checkout is not evidence of a matrix gap.
    """
    try:
        shard = json.loads(
            (REPO / "frontend/data/backcast/keepers" / f"{iso}.json").read_text("utf-8")
        )
        reg = (
            REPO / "frontend/data/backcast/registry" / f"{shard.get('keeper', '')}.json"
        )
        bundle = json.loads(reg.read_text("utf-8")).get("bundle", "")
        cfg = REPO / "results/calibration" / Path(bundle).name / "run_config.json"
        doc = json.loads(cfg.read_text("utf-8"))
    except (OSError, ValueError, KeyError):
        return {}
    return doc.get("scenario_config", doc)


def shared_gap_ratchet(matrix_text: str, source: str) -> list[str]:
    """Errors for SHARED fields a keeper ARMS that no matrix row mentions.

    The nyiso-115 blind spot. :func:`gap_ratchet` above only ever looks at
    ``<iso>_*`` fields, so a SHARED mechanism armed on a designated keeper with
    no row anywhere is invisible to it — the same 227-3 shape, one class wider.
    nyiso-114 closed NYISO's ISO-scoped column to 0 absent / 0 prose-only /
    0 armed-no-cell while **twelve** shared fields sat armed on its keeper with
    zero matrix mention, and every other lane carries the same class (CAISO 28,
    ERCOT 40, MISO 33, PJM 34, NEISO 13).

    Keyed on the DESIGNATED KEEPER, not on "any bundle": a keeper is the
    configuration an ISO is actually calibrated at, so a field it arms with no
    cell is a mechanism shaping a published result that no session can see.

    Same ratchet contract as the ISO-scoped leg — the baseline may only SHRINK —
    and the same escape hatch: naming the field in an owning family row's
    ``def``/``note`` counts as registration. Declared false positives come from
    the baseline's ``shared_census_exclusions`` block, which
    ``mechanism_matrix_gap_sweep --write-baseline`` writes from its own
    ``SHARED_CENSUS_EXCLUSIONS``, so the two cannot drift apart.
    """
    path = REPO / GAPS_BASELINE_PATH
    if not path.exists():
        return []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{GAPS_BASELINE_PATH} is unreadable ({exc})"]
    allowed = doc.get("shared_armed_on_keeper", {})
    excluded = set(doc.get("shared_census_exclusions", {}))
    defaults = _scenarioconfig_defaults(source)
    iso_prefixes = tuple(f"{s}_" for stems in ISO_STEMS.values() for s in stems)
    out: list[str] = []
    for iso in sorted(ISO_STEMS):
        keeper_cfg = _keeper_run_config(iso)
        if not keeper_cfg:
            continue
        allow = set(allowed.get(iso, ()))
        for field, default in sorted(defaults.items()):
            if field.startswith(iso_prefixes) or field in excluded:
                continue
            if field not in keeper_cfg:
                continue
            value = keeper_cfg[field]
            # JSON has no tuple; the sweep normalises the same way.
            if value == (list(default) if isinstance(default, tuple) else default):
                continue
            if field in matrix_text or field in allow:
                continue
            out.append(
                f"shared field `{field}` is ARMED on the {iso} keeper "
                f"({default!r} -> {value!r}) but is in neither {MATRIX_PATH} nor "
                f"the {GAPS_BASELINE_PATH} shared ratchet (rule 28c). Add its "
                f"row, or name it in the owning family row's def/note."
            )
    return out


def _scenarios_field_lines(source: str) -> dict[str, int]:
    """Map each ``ScenarioConfig`` field to the 1-based line that defines it.

    Same recogniser as :func:`scenarioconfig_fields` (a 4-space-indented
    ``name:`` inside the class body), so a field this returns is exactly a
    field that function reports.
    """
    m = re.search(r"^class ScenarioConfig\b", source, re.M)
    if not m:
        return {}
    out: dict[str, int] = {}
    in_body = False
    for i, line in enumerate(source.splitlines(), start=1):
        if re.match(r"^class ScenarioConfig\b", line):
            in_body = True
            continue
        if not in_body:
            continue
        if re.match(r"^(?:class |def |@dataclass)", line):
            break
        fm = re.match(r"^    ([a-z][a-z0-9_]*)\s*:", line)
        if fm and not fm.group(1).startswith("_") and fm.group(1) not in out:
            out[fm.group(1)] = i
    return out


def _py_file_index() -> dict[str, list[Path]]:
    """Index every repo ``*.py`` by basename, for file-style anchor resolution."""
    skip = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache"}
    idx: dict[str, list[Path]] = {}
    for p in REPO.rglob("*.py"):
        if any(part in skip for part in p.parts):
            continue
        idx.setdefault(p.name, []).append(p)
    return idx


def _resolve_anchor_path(raw: str, index: dict[str, list[Path]]) -> Path | None:
    """Resolve a matrix file anchor (``model/lp/rows.py``) to a repo file.

    Returns ``None`` when the path is ambiguous or unknown — an unresolvable
    path is SKIPPED and counted, never guessed at and never silently dropped.
    """
    direct = REPO / raw
    if direct.is_file():
        return direct
    cands = [p for p in index.get(Path(raw).name, ()) if str(p).endswith(raw)]
    return cands[0] if len(cands) == 1 else None


def anchor_findings(matrix_text: str, source: str) -> tuple[list[dict], dict[str, int]]:
    """Every matrix line anchor that does NOT resolve, plus a coverage tally.

    **Why this exists.** A line anchor is a pointer into files every lane edits,
    so it decays with nobody touching the matrix — and nothing checked it.
    nyiso-121 found all 20 MISO anchors stale (eight by ~1,000 lines) and filed
    a standing check as a suggestion; xiso-3 measured the whole file and found
    **163 of 167 checkable anchors unresolvable**. A correct field literal on a
    wrong anchor still sends a reader to unrelated code, so the literal name is
    the durable identifier and the anchor is a convenience that must be
    verified, not trusted.

    Three legs, each returning ``{kind, key, detail, fix}`` dicts (``fix`` is
    the correct line where one is mechanically derivable, else ``None``):

    * ``field`` — a ``<field> :<line>`` sub-scalar registration must resolve to
      a ``scenarios.py`` line defining ``<field>``. **Existence is gated
      first**: a token that is not a ``ScenarioConfig`` field is skipped, which
      is what preserves the deliberate ``miso_pjm_lmp :2914`` defect QUOTATION
      in ``import_hub_pricing``'s repair note (and ordinary prose collisions
      like ``a stale :2138``). Do not "fix" those.
    * ``row`` — a row whose ``id`` is itself a field and whose ``def`` carries
      ``scenarios.py:<line>`` must resolve the same way.
    * ``path`` — any ``<file>.py:<line>`` must be within that file. Only
      out-of-range fails; an unresolvable path is skipped and counted.
    """
    fields = _scenarios_field_lines(source)
    out: list[dict] = []
    tally = {
        "field_checked": 0,
        "field_skipped_nonfield": 0,
        "row_checked": 0,
        "path_checked": 0,
        "path_skipped_unresolvable": 0,
    }

    # --- leg A: `<field> :<line>` sub-scalar registrations -------------------
    for name, ln in re.findall(r"\b([a-z][a-z0-9_]{3,}) :(\d+)\b", matrix_text):
        if name not in fields:
            tally["field_skipped_nonfield"] += 1
            continue
        tally["field_checked"] += 1
        if int(ln) != fields[name]:
            out.append(
                {
                    "kind": "field",
                    "key": f"{name} :{ln}",
                    "detail": (
                        f"`{name} :{ln}` does not resolve — the field is defined "
                        f"at {SCENARIOS_PATH}:{fields[name]}"
                    ),
                    "fix": fields[name],
                }
            )

    # --- leg B: row-id anchors (`def: "scenarios.py:<line>"`) ----------------
    for chunk in re.split(r'\n\s*\{\s*id:\s*"', matrix_text)[1:]:
        rid, _, body = chunk.partition('"')
        if rid not in fields:
            continue
        d = re.search(r'def:\s*"(.*?)",\s*mode', body, re.S)
        if not d:
            continue
        m = re.search(r"scenarios\.py:(\d+)", d.group(1))
        if not m:
            continue
        tally["row_checked"] += 1
        if int(m.group(1)) != fields[rid]:
            out.append(
                {
                    "kind": "row",
                    "key": f"row:{rid} scenarios.py:{m.group(1)}",
                    "detail": (
                        f"row `{rid}` anchors scenarios.py:{m.group(1)} but its "
                        f"field is defined at {SCENARIOS_PATH}:{fields[rid]}"
                    ),
                    "fix": fields[rid],
                }
            )

    # --- leg C: file anchors must be in range --------------------------------
    index = _py_file_index()
    for raw, ln in re.findall(r"\b([\w/]+\.py):(\d+)\b", matrix_text):
        target = _resolve_anchor_path(raw, index)
        if target is None:
            tally["path_skipped_unresolvable"] += 1
            continue
        tally["path_checked"] += 1
        n_lines = len(target.read_text(encoding="utf-8").splitlines())
        if int(ln) > n_lines:
            out.append(
                {
                    "kind": "path",
                    "key": f"{raw}:{ln}",
                    "detail": f"`{raw}:{ln}` is past end of file ({n_lines} lines)",
                    "fix": None,
                }
            )
    return out, tally


def anchor_ratchet(findings: list[dict]) -> list[dict]:
    """Unresolvable anchors that the committed baseline does not already allow.

    Same shrink-only contract as the two gap ratchets: the baseline enumerates
    the anchors known not to resolve, and anything unresolvable that is NOT in
    it is reportable. Refresh with ``--fix-anchors``, which repairs every
    mechanically derivable anchor (digits only) and rewrites the baseline with
    whatever is left. Target state is an EMPTY baseline, which xiso-3
    established.

    Returns the findings themselves so the caller can split them by BLAME —
    see :func:`main`. A line anchor is an absolute line number into
    ``scenarios.py``, which nearly every calibration lane edits, so ANY PR that
    inserts a field silently stales every anchor below it. Failing that PR for
    drift it merely inherited is how a gate gets disabled, so the blame split
    is what makes this check survivable.
    """
    path = REPO / ANCHORS_BASELINE_PATH
    allowed: set[str] = set()
    if path.exists():
        try:
            allowed = set(json.loads(path.read_text(encoding="utf-8")).get("stale", ()))
        except (OSError, ValueError) as exc:
            return [{"key": ANCHORS_BASELINE_PATH, "detail": f"unreadable ({exc})"}]
    return [f for f in findings if f["key"] not in allowed]


def _anchor_message(finding: dict) -> str:
    """One reportable anchor finding, with the repair command."""
    return (
        f"{finding['detail']}. Run `python3 scripts/check_mechanism_matrix.py "
        f"--fix-anchors` (repairs the digits only; the field NAME is the "
        f"durable identifier)."
    )


def fix_anchors(matrix_text: str, findings: list[dict]) -> tuple[str, int]:
    """Rewrite every mechanically derivable anchor. ONLY the digits change."""
    fixed = 0
    for f in findings:
        if f["fix"] is None:
            continue
        if f["kind"] == "field":
            name, _, old = f["key"].partition(" :")
            new_text = matrix_text.replace(f"{name} :{old}", f"{name} :{f['fix']}")
        else:  # row-id anchor: only inside that row's def
            rid = f["key"].split()[0].removeprefix("row:")
            old = f["key"].rsplit(":", 1)[1]
            head, sep, rest = matrix_text.partition(f'{{ id: "{rid}"')
            new_text = (
                head
                + sep
                + rest.replace(f"scenarios.py:{old}", f"scenarios.py:{f['fix']}", 1)
            )
        if new_text != matrix_text:
            matrix_text, fixed = new_text, fixed + 1
    return matrix_text, fixed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="git ref to diff against (PR base sha)")
    parser.add_argument(
        "--fix-anchors",
        action="store_true",
        help="repair every mechanically derivable stale line anchor in the "
        "matrix (digits only) and refresh the anchor ratchet baseline.",
    )
    args = parser.parse_args()

    matrix_text = (REPO / MATRIX_PATH).read_text(encoding="utf-8")
    errors = validate_matrix(matrix_text)
    for e in errors:
        print(f"::error file={MATRIX_PATH}::mechanism-matrix integrity: {e}")
    if errors:
        return 1
    print(f"mechanism-matrix: integrity OK ({MATRIX_PATH})")

    # --- rule 28: line anchors must resolve (the nyiso-121 decay) ------------
    scen_src = (REPO / SCENARIOS_PATH).read_text(encoding="utf-8")
    findings, tally = anchor_findings(matrix_text, scen_src)
    if args.fix_anchors:
        matrix_text, n_fixed = fix_anchors(matrix_text, findings)
        (REPO / MATRIX_PATH).write_text(matrix_text, encoding="utf-8")
        findings, tally = anchor_findings(matrix_text, scen_src)
        (REPO / ANCHORS_BASELINE_PATH).write_text(
            json.dumps(
                {
                    "_comment": (
                        "Shrink-only ratchet of matrix line anchors that do NOT "
                        "resolve, enforced by scripts/check_mechanism_matrix.py. A "
                        "line anchor points into files every lane edits, so it "
                        "decays with nobody touching the matrix (nyiso-121 found "
                        "all 20 MISO anchors stale; xiso-3 found 163 of 167 "
                        "file-wide). The field NAME is the durable identifier; the "
                        "anchor is a convenience. Anchors whose token is not a "
                        "ScenarioConfig field are skipped by construction, which "
                        "preserves the deliberate `miso_pjm_lmp :2914` defect "
                        "QUOTATION in import_hub_pricing's repair note — do not "
                        "'fix' it. Refresh with --fix-anchors."
                    ),
                    "stale": sorted(f["key"] for f in findings),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            f"mechanism-matrix: repaired {n_fixed} line anchor(s); "
            f"{len(findings)} left in the ratchet"
        )
    anchor_errs = anchor_ratchet(findings)
    print(
        f"mechanism-matrix: anchors checked "
        f"({tally['field_checked']} field + {tally['row_checked']} row + "
        f"{tally['path_checked']} path; skipped "
        f"{tally['field_skipped_nonfield']} non-field token(s) and "
        f"{tally['path_skipped_unresolvable']} unresolvable path(s)) — "
        f"{len(anchor_errs)} unresolvable beyond the ratchet"
    )

    # --- rule 28: header keeper stamp vs the per-ISO keeper shard -------------
    drift = keeper_drift(matrix_text)
    if not drift:
        print("mechanism-matrix: keeper stamps match every keepers/<ISO>.json")

    # Same rule, the PROSE half (added xiso-4 2026-08-04 — see doc_header_drift).
    doc_text = (REPO / MATRIX_DOC_PATH).read_text(encoding="utf-8")
    doc_drift = doc_header_drift(doc_text)
    if not doc_drift:
        print("mechanism-matrix: §5.x prose headers match every keepers/<ISO>.json")

    if not args.base:
        for f in anchor_errs:
            print(
                f"::warning file={MATRIX_PATH}::mechanism-matrix anchor: "
                f"{_anchor_message(f)}"
            )
        for iso, header, shard in drift:
            print(
                f"::warning file={MATRIX_PATH}::{iso} keeper stamp drift: header "
                f"`{header}` != keepers/{iso}.json `{shard}` (rule 28). The "
                f"promoting session re-stamps the header in the same session."
            )
        for iso, reason, shard in doc_drift:
            print(
                f"::warning file={MATRIX_DOC_PATH}::{iso} §5.x prose header drift: "
                f"{reason} (designated keeper `{shard}`, rule 28). The promoting "
                f"session re-stamps the prose header in the same session."
            )
        return 0

    changed = _git("diff", "--name-only", args.base, "HEAD").splitlines()
    matrix_touched = MATRIX_PATH in changed

    # --- rule 28(c): new ScenarioConfig fields must be registered ------------
    failed = False

    # A PR that STALES an anchor owns it: fail. An anchor already stale at the
    # base only warns — it belongs to whoever last moved scenarios.py, not to
    # whichever PR happens to run next. Exactly the keeper-drift rule below,
    # and the reason this gate is survivable: anchors are ABSOLUTE line numbers
    # into a file nearly every lane edits, so a single inserted field stales
    # every anchor beneath it. (xiso-3 shipped this check with an empty ratchet
    # and main re-staled 214 anchors within the day — a hard gate would have
    # gone red for lanes that touched nothing.)
    base_stale: set[str] = set()
    try:
        base_findings, _ = anchor_findings(
            _git("show", f"{args.base}:{MATRIX_PATH}"),
            _git("show", f"{args.base}:{SCENARIOS_PATH}"),
        )
        base_stale = {f["key"] for f in base_findings}
    except (subprocess.CalledProcessError, OSError):
        base_stale = set()  # base blobs unreachable: fail closed, blame nobody
    for f in anchor_errs:
        if f["key"] in base_stale:
            print(
                f"::warning file={MATRIX_PATH}::mechanism-matrix anchor "
                f"(pre-existing, not this PR): {_anchor_message(f)}"
            )
        else:
            failed = True
            print(
                f"::error file={MATRIX_PATH}::mechanism-matrix anchor: "
                f"{_anchor_message(f)}"
            )

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

    # Prose half, same escalation: a PR that MOVES a keeper shard owns that
    # ISO's §5.x prose header. Drift it did not create only warns — it belongs
    # to the owning ISO's lane, not to whichever PR happens to run next.
    for iso, reason, shard in doc_drift:
        if KEEPER_SHARD.format(iso=iso) in changed:
            failed = True
            print(
                f"::error file={MATRIX_DOC_PATH}::{iso} keeper promoted to `{shard}` "
                f"in this PR but its §5.x prose header is stale: {reason}. Rule 28 "
                f"[R-MECH-MATRIX]: the promoting session re-stamps the header (and "
                f"re-checks that ISO's column) in the SAME session."
            )
        else:
            print(
                f"::warning file={MATRIX_DOC_PATH}::{iso} §5.x prose header drift "
                f"(pre-existing, not this PR): {reason} (designated keeper "
                f"`{shard}`). Belongs to the {iso} lane."
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

    # --- rule 28(c) RATCHET, SHARED leg: a keeper-armed shared field with no row
    shared = shared_gap_ratchet(matrix_text, (REPO / SCENARIOS_PATH).read_text("utf-8"))
    for e in shared:
        failed = True
        print(f"::error file={SCENARIOS_PATH}::mechanism-matrix shared ratchet: {e}")
    if not shared:
        print(
            "mechanism-matrix: shared ratchet OK "
            "(no keeper arms an unregistered shared field)"
        )

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
