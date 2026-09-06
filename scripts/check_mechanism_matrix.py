"""Rule-28 [R-MECH-MATRIX] mechanism-matrix guard (CI + local).

THE MATRIX IS SHARDED PER ISO since 2026-08-11 (HOUSE-3, mirroring the
2026-07-19 keeper sharding): `docs/codebase-site/data/mechanism-matrix.js` is
the mechanism-level BASE (rows: id/cat/name/def/mode/note + cross-ISO ev) and
`docs/codebase-site/data/mechanism-matrix/<ISO>.js` carries that ISO's cell
verdicts, fc postures, ev citations and keeper/gates stamps. A lane's rule-28
duty is a ONE-FILE edit — its own ISO's shard. Shared IO lives in
`scripts/lib/mech_matrix.py` (stdlib-only, like this script; bare python3
still runs both).

Two layers:

1. **Integrity validation** (always): the base parses to well-formed rows —
   unique ids, categories resolved — and every shard parses, matches its
   filename's ISO, covers EXACTLY the base's mechanism-id set, and carries
   single-char `cell`/`fc` values over the `K R I G O U .` vocabulary. A
   malformed store silently breaks the explorer page AND the ledger, so it
   hard-fails, naming the file (base or ISO shard) to fix.

2. **Keeper-stamp drift** (always advisory, escalating in the diff gate):
   each matrix shard's `keeper:` stamp must equal the id in
   `frontend/data/backcast/keepers/<ISO>.json`. Rule 28 requires the promoting
   session to re-stamp the matrix when a keeper changes, but nothing
   checked it, so three ISOs drifted silently at once (nyiso-105 missed its
   stamp; ERCOT and CAISO were still on 2026-07-29 ids after 2026-07-31
   promotions). Pre-existing drift only WARNS — it belongs to the owning ISO's
   lane, not to whichever PR happens to run next — but a PR that itself moves
   an ISO's keeper shard without re-stamping that ISO's matrix shard FAILS,
   which is exactly the duty rule 28 states.

3. **Gap ratchets** (always, BOTH modes): three shrink-only censuses that ask,
   with no diff at all, whether every `ScenarioConfig` field is named in the
   matrix or forgiven by the committed baseline
   `mechanism-matrix-gaps.json` — `gap_ratchet` for the ISO-scoped fields,
   `absent_shared_ratchet` for the shared complement, `shared_gap_ratchet` for
   the sharper keeper-armed alarm inside it. This is the POST-MERGE half of
   rule 28(c): the diff gate below can only ever see a field in the PR that
   adds it, so before these ran diff-free, a field that reached `main`
   unregistered was invisible to every later run of this script
   (`docs/handoffs/FINDING-scn-mxr-2026-09-06.md` §1.1 — PR #4870 merged five
   seconds after opening, with the diff gate red and unread). A slipped field
   is now red until its row lands, and each baseline may only SHRINK.

4. **Diff gate** (`--base <ref>`): enforces the mechanical half of rule 28(c) —
   a PR that adds a NEW `ScenarioConfig` field must mention that field in the
   matrix (its own row, or an existing row's `def`/`note` that covers it).
   Mention-anywhere is the deliberate escape hatch: not every new field is its
   own mechanism (paths, sub-scalars of an existing family belong on the
   family's row), so the gate checks registration, not taxonomy. Two advisory
   (non-failing) `::warning::` legs cover rule 28(b): a new backcast registry
   sidecar landing without a matrix touch, and new CLI flags in
   `run_calibration_full.py` absent from the matrix.

Line anchors (`<field> :<line>`) are checked in both modes and reported with
their blame, but stale DIGITS never fail this script — they are mechanically
repairable with `--fix-anchors`, they re-stale on every merge that touches
`scenarios.py`, and a guard whose red usually means "you moved line numbers" is
a guard people merge through (R4 in the finding above; see :func:`main`). Only
an anchor no command can repair — a file anchor past end of file — fails, and
only when the PR at hand created it.

Usage:
    python3 scripts/check_mechanism_matrix.py                # validate + ratchets
    python3 scripts/check_mechanism_matrix.py --base <sha>   # + diff gate

Exit codes: 0 clean, 1 gate failure (malformed matrix, an unregistered field —
new in the diff, or legacy and beyond a ratchet baseline — an un-restamped
keeper promotion, or an unrepairable anchor this PR created). WITHOUT `--base`
the diff gate does not run and the script says so on stdout: a 0 from that mode
is not a registration verdict for a field the PR itself adds.
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
sys.path.insert(0, str(REPO))

from scripts.lib import mech_matrix as mm  # noqa: E402  (after sys.path insert)

MATRIX_PATH = "docs/codebase-site/data/mechanism-matrix.js"  # the BASE file
SHARD_PATH = "docs/codebase-site/data/mechanism-matrix/{iso}.js"
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
# mistaken for a CARB field. SINGLE-SOURCED in scripts/lib/mech_matrix.py since
# y20 — this script and mechanism_matrix_gap_sweep.py carried separate copies
# under a "keep in sync" comment, and a census whose two halves disagree writes
# a baseline the other half can never satisfy.
ISO_STEMS = mm.ISO_FIELD_STEMS

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

    Scanning starts at the `window.MECH_MATRIX` assignment (a prefix — it also
    anchors `window.MECH_MATRIX_BASE` and `window.MECH_MATRIX_SHARDS`):
    everything above it is the file's block-comment header, whose prose
    legitimately contains `word: "quoted"` shapes that are not string literals
    at all.
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


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def matrix_isos(base_text: str) -> list[str]:
    """Return the base file's `isos:` list, in display/cell order."""
    m = re.search(r"isos:\s*\[([^\]]*)\]", base_text)
    return re.findall(r'"([A-Z]+)"', m.group(1)) if m else []


def load_store() -> tuple[dict | None, dict[str, dict], list[str]]:
    """Parse base + every ISO shard. Returns (base_doc, shard_docs, errors).

    Every error string is prefixed `<file>: ` so a failing lane knows which
    file — the base, or which ISO's shard — it must fix.
    """
    errors: list[str] = []
    base_text = _read(REPO / MATRIX_PATH)
    if base_text is None:
        return None, {}, [f"{MATRIX_PATH}: missing or unreadable"]
    errors += [f"{MATRIX_PATH}: {e}" for e in unbalanced_strings(base_text)]
    base_doc: dict | None = None
    try:
        base_doc = mm.parse_assignment(base_text, "window.MECH_MATRIX").value
    except ValueError as exc:
        errors.append(f"{MATRIX_PATH}: {exc}")
    shards: dict[str, dict] = {}
    isos = matrix_isos(base_text) or list(mm.ISO_ORDER)
    for iso in isos:
        rel = SHARD_PATH.format(iso=iso)
        text = _read(REPO / rel)
        if text is None:
            errors.append(f"{rel}: missing shard file for ISO {iso}")
            continue
        errors += [f"{rel}: {e}" for e in unbalanced_strings(text)]
        try:
            shards[iso] = mm.parse_assignment(
                text, f"window.MECH_MATRIX_SHARDS.{iso}"
            ).value
        except ValueError as exc:
            errors.append(f"{rel}: {exc}")
    return base_doc, shards, errors


def validate_store(base_doc: dict | None, shards: dict[str, dict]) -> list[str]:
    """Integrity errors for the parsed sharded store (see module docstring)."""
    errors: list[str] = []
    if base_doc is None:
        return errors  # parse errors already reported by load_store
    rows = base_doc.get("rows") or []
    isos = list(base_doc.get("isos") or mm.ISO_ORDER)
    cats = {c.get("id") for c in base_doc.get("categories", [])}
    seen: set[str] = set()
    for row in rows:
        rid = str(row.get("id", "<missing id>"))
        if rid in seen:
            errors.append(f"{MATRIX_PATH}: duplicate row id `{rid}`")
        seen.add(rid)
        if row.get("cat") not in cats:
            errors.append(
                f"{MATRIX_PATH}: row `{rid}` references unknown category "
                f"`{row.get('cat')}`"
            )
        for key in ("cells", "fc"):
            if key in row:
                errors.append(
                    f"{MATRIX_PATH}: row `{rid}` carries a `{key}:` string — "
                    f"per-ISO verdicts live in mechanism-matrix/<ISO>.js "
                    f"(one `cell`/`fc` char per shard), not in the base"
                )
        per_iso = set(row.get("ev") or {}) & mm.PER_ISO_EV_KEYS
        if per_iso:
            errors.append(
                f"{MATRIX_PATH}: row `{rid}` base ev carries per-ISO key(s) "
                f"{sorted(per_iso)} — per-ISO citations live in the owning "
                f"ISO's shard `ev`; only cross-ISO keys (e.g. `All`) stay here"
            )
    if not rows:
        errors.append(f"{MATRIX_PATH}: no rows found")
    for iso in isos:
        if iso not in shards:
            continue  # missing/unparseable: load_store already reported it
        rel = SHARD_PATH.format(iso=iso)
        doc = shards[iso]
        if doc.get("iso") != iso:
            errors.append(f"{rel}: `iso:` field reads `{doc.get('iso')}`")
        cells = doc.get("cells")
        if not isinstance(cells, dict):
            errors.append(f"{rel}: no `cells:` map")
            continue
        missing = sorted(seen - set(cells))
        extra = sorted(set(cells) - seen)
        if missing:
            errors.append(
                f"{rel}: missing cell(s) for {len(missing)} mechanism(s): "
                + ", ".join(missing[:6])
                + (", …" if len(missing) > 6 else "")
                + " (every base row id needs a line in every shard; use "
                '`cell: "."` for n/a and `cell: "U"` for untested)'
            )
        if extra:
            errors.append(
                f"{rel}: cell(s) for unknown mechanism id(s): "
                + ", ".join(extra[:6])
                + (", …" if len(extra) > 6 else "")
                + f" (no such row in {MATRIX_PATH})"
            )
        for rid, entry in cells.items():
            if not isinstance(entry, dict):
                errors.append(f"{rel}: `{rid}` entry is not an object")
                continue
            for key in ("cell", "fc"):
                if key == "cell" and key not in entry:
                    errors.append(f"{rel}: `{rid}` has no `cell:`")
                elif key in entry and (
                    len(str(entry[key])) != 1 or str(entry[key]) not in CELL_CHARS
                ):
                    errors.append(
                        f"{rel}: `{rid}` bad `{key}` value `{entry[key]}` "
                        f"(need one char of K/R/I/G/O/U/.)"
                    )
    return errors


def matrix_all_text() -> str:
    """Base + every shard, concatenated — the full rule-28 text surface.

    Mention-style checks (the gap ratchets, the new-field diff gate, the CLI
    advisory) search this: a field registered in a row's def/note (base) or in
    an ISO shard's ev/note counts either way.
    """
    parts = []
    for path in matrix_paths():
        text = _read(REPO / path)
        if text is not None:
            parts.append(text)
    return "\n".join(parts)


def matrix_paths() -> list[str]:
    """Repo-relative base + shard paths (shards in base `isos:` order)."""
    base_text = _read(REPO / MATRIX_PATH) or ""
    isos = matrix_isos(base_text) or list(mm.ISO_ORDER)
    return [MATRIX_PATH] + [SHARD_PATH.format(iso=iso) for iso in isos]


def matrix_keepers(shards: dict[str, dict]) -> dict[str, str]:
    """The per-ISO matrix shards' `keeper:` stamps, `{ISO: keeper_id}`."""
    return {iso: str(doc.get("keeper") or "") for iso, doc in shards.items()}


def shard_keeper(iso: str) -> str | None:
    """Return the keeper id from an ISO's keeper shard, or None if unreadable."""
    path = REPO / KEEPER_SHARD.format(iso=iso)
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("keeper") or "")
    except (OSError, ValueError):
        return None


def keeper_drift(stamps: dict[str, str]) -> list[tuple[str, str, str]]:
    """Return `(iso, matrix_stamp, keeper_shard_id)` per disagreeing ISO.

    `stamps` is the matrix shards' keeper map (see :func:`matrix_keepers`);
    the authority is `frontend/data/backcast/keepers/<ISO>.json`.
    """
    drift: list[tuple[str, str, str]] = []
    for iso, stamp in stamps.items():
        shard = shard_keeper(iso)
        if shard is None:
            continue  # no keeper shard on disk: not this guard's business
        if stamp != shard:
            drift.append((iso, stamp or "<missing>", shard))
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
    """Extract ScenarioConfig dataclass field names from scenarios.py source.

    Delegates to the shared recogniser (y20): the sweep that WRITES the gap
    baselines calls the same function, so the enforcing half can never see a
    different field set than the writing half.
    """
    return mm.scenarioconfig_field_names(source)


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
                    f"{iso}-scoped field `{f}` is in neither the mechanism "
                    f"matrix (base {MATRIX_PATH} + ISO shards) nor the "
                    f"{GAPS_BASELINE_PATH} ratchet (rule 28c). Add its row "
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
                f"({default!r} -> {value!r}) but is in neither the mechanism "
                f"matrix (base {MATRIX_PATH} + ISO shards) nor the "
                f"{GAPS_BASELINE_PATH} shared ratchet (rule 28c). Add its "
                f"row, or name it in the owning family row's def/note."
            )
    return out


def absent_shared_ratchet(matrix_text: str, source: str) -> list[str]:
    """Errors for SHARED fields the matrix never mentions, keeper-armed or not.

    THE POST-MERGE HALF of rule 28(c), and the hole
    ``docs/handoffs/FINDING-scn-mxr-2026-09-06.md`` §1.1 diagnosed. Before this
    leg, exactly one check inspected a NEW field's registration — the ``--base``
    diff gate — so a field that reached ``main`` without its row was invisible
    to every later run of this script, on ``main`` and on every subsequent PR
    (whose diff no longer contains it). PR #4870 is the worked example: the
    diff gate ran, FAILED on ``federal_ces_acp_usd_per_mwh`` and
    ``federal_ces_target_by_year``, and the PR merged five seconds after it
    opened — after which nothing could see those two fields again. Neither
    diff-free ratchet could: :func:`gap_ratchet` only looks at ``<iso>_*``
    fields, and :func:`shared_gap_ratchet` only at fields a designated BACKCAST
    keeper arms, which a forecast-only field defaulting to ``None`` can never
    be.

    So this leg drops both qualifiers. Its census is every SHARED (non-ISO
    stemmed) ``ScenarioConfig`` field, by NAME — no default value is parsed and
    no bundle is read, because registration asks only whether the matrix names
    the field. Together with :func:`gap_ratchet`'s ISO-scoped half it covers
    every field in the class, and both run with no ``--base`` (see :func:`main`),
    which is what makes a slipped field red until its row lands.

    Same shrink-only contract and the same mention-anywhere escape hatch as its
    two siblings; the baseline block is ``absent_shared``, written by
    ``scripts/mechanism_matrix_gap_sweep.py --write-baseline``. It opens LARGE
    (185 legacy fields at y20) because it is the first check ever to look at
    this class — that backlog is the owning desks' work, one row at a time, and
    the ratchet's job is only that it never grows.

    :func:`shared_gap_ratchet` is deliberately NOT subsumed: it stays the
    sharper alarm on the same class (a field shaping a PUBLISHED keeper) with
    its own, empty, baseline — so a field forgiven here still fails there the
    moment a keeper arms it.
    """
    path = REPO / GAPS_BASELINE_PATH
    if not path.exists():
        return []
    try:
        allowed = set(
            json.loads(path.read_text(encoding="utf-8")).get("absent_shared", ())
        )
    except (OSError, ValueError) as exc:
        return [f"{GAPS_BASELINE_PATH} is unreadable ({exc})"]
    absent = mm.absent_shared_fields(scenarioconfig_fields(source), matrix_text)
    return [
        f"shared field `{f}` is in neither the mechanism matrix (base "
        f"{MATRIX_PATH} + ISO shards) nor the {GAPS_BASELINE_PATH} "
        f"`absent_shared` ratchet (rule 28c). Add its row (plus a cell line in "
        f"each mechanism-matrix/<ISO>.js shard), or name it in the owning "
        f"family row's def/note."
        for f in absent
        if f not in allowed
    ]


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


def _anchor_findings_all(scen_src: str) -> tuple[list[dict], dict[str, int]]:
    """Anchor findings across base + every shard, each tagged with `path`."""
    findings: list[dict] = []
    tally: dict[str, int] = {}
    for rel in matrix_paths():
        text = _read(REPO / rel)
        if text is None:
            continue
        found, t = anchor_findings(text, scen_src)
        for f in found:
            f["path"] = rel
        findings += found
        for k, v in t.items():
            tally[k] = tally.get(k, 0) + v
    return findings, tally


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

    base_doc, shard_docs, errors = load_store()
    errors += validate_store(base_doc, shard_docs)
    for e in errors:
        # Each error string is `<file>: <detail>` — surface the file to fix.
        rel, _, detail = e.partition(": ")
        print(f"::error file={rel}::mechanism-matrix integrity: {detail}")
    if errors:
        return 1
    print(
        f"mechanism-matrix: integrity OK ({MATRIX_PATH} + {len(shard_docs)} ISO shards)"
    )
    matrix_text = matrix_all_text()

    # --- rule 28: line anchors must resolve (the nyiso-121 decay) ------------
    scen_src = (REPO / SCENARIOS_PATH).read_text(encoding="utf-8")
    findings, tally = _anchor_findings_all(scen_src)
    if args.fix_anchors:
        n_fixed = 0
        for rel in matrix_paths():
            per_file = [f for f in findings if f["path"] == rel]
            if not per_file:
                continue
            text = (REPO / rel).read_text(encoding="utf-8")
            text, fixed = fix_anchors(text, per_file)
            if fixed:
                (REPO / rel).write_text(text, encoding="utf-8")
                n_fixed += fixed
        matrix_text = matrix_all_text()
        findings, tally = _anchor_findings_all(scen_src)
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
    drift = keeper_drift(matrix_keepers(shard_docs))
    if not drift:
        print("mechanism-matrix: keeper stamps match every keepers/<ISO>.json")

    # Same rule, the PROSE half (added xiso-4 2026-08-04 — see doc_header_drift).
    doc_text = (REPO / MATRIX_DOC_PATH).read_text(encoding="utf-8")
    doc_drift = doc_header_drift(doc_text)
    if not doc_drift:
        print("mechanism-matrix: §5.x prose headers match every keepers/<ISO>.json")

    # --- rule 28(c) RATCHETS: diff-free, shrink-only, BOTH modes --------------
    #
    # These three run BEFORE the validate-only return, which is the whole
    # post-merge half of the repair (FINDING-scn-mxr-2026-09-06 §1.4 R2). They
    # need no diff by construction — each asks "is this field named in the
    # matrix or forgiven by the committed baseline?", a question about the tree
    # as it stands — so a field that reached `main` unregistered is red here on
    # every later run until its row lands, instead of being invisible forever
    # the moment its own PR merged. Between them they cover EVERY
    # `ScenarioConfig` field: `gap_ratchet` the ISO-scoped ones,
    # `absent_shared_ratchet` the shared complement, `shared_gap_ratchet` the
    # sharper keeper-armed alarm inside that complement.
    ratchet_failed = False
    for leg, clean, errs in (
        (
            "gap ratchet",
            "no ISO-scoped field is invisible",
            gap_ratchet(matrix_text, scen_src),
        ),
        (
            "shared ratchet",
            "no keeper arms an unregistered shared field",
            shared_gap_ratchet(matrix_text, scen_src),
        ),
        (
            "absent-shared ratchet",
            "every shared field is registered or baselined",
            absent_shared_ratchet(matrix_text, scen_src),
        ),
    ):
        for e in errs:
            ratchet_failed = True
            print(f"::error file={SCENARIOS_PATH}::mechanism-matrix {leg}: {e}")
        if not errs:
            print(f"mechanism-matrix: {leg} OK ({clean})")

    if not args.base:
        for f in anchor_errs:
            print(
                f"::warning file={f.get('path', MATRIX_PATH)}::mechanism-matrix "
                f"anchor: {_anchor_message(f)}"
            )
        for iso, header, shard in drift:
            print(
                f"::warning file={SHARD_PATH.format(iso=iso)}::{iso} keeper stamp "
                f"drift: matrix shard `{header}` != keepers/{iso}.json `{shard}` "
                f"(rule 28). The promoting session re-stamps its ISO's matrix "
                f"shard in the same session."
            )
        for iso, reason, shard in doc_drift:
            print(
                f"::warning file={MATRIX_DOC_PATH}::{iso} §5.x prose header drift: "
                f"{reason} (designated keeper `{shard}`, rule 28). The promoting "
                f"session re-stamps the prose header in the same session."
            )
        # R3 (FINDING-scn-mxr-2026-09-06 §1.4): SAY WHAT WAS NOT CHECKED. Three
        # desk readings recorded "CI exited 0" from this mode, which asserts
        # store integrity and the ratchets above but CANNOT see a field added by
        # the PR at hand — that is the diff gate's job and it does not run here.
        print(
            "mechanism-matrix: diff gate NOT RUN — pass --base <sha> to check "
            "new-field registration, keeper-promotion stamps and anchor blame. "
            "A 0 from this mode is not a registration verdict for a NEW field."
        )
        return 1 if ratchet_failed else 0

    changed = _git("diff", "--name-only", args.base, "HEAD").splitlines()
    matrix_files = set(matrix_paths())
    matrix_touched = any(p in matrix_files for p in changed)

    # --- rule 28(c): new ScenarioConfig fields must be registered ------------
    failed = ratchet_failed

    # ANCHOR BLAME, and its severity (R4, y20). An anchor already stale at the
    # base warns — it belongs to whoever last moved scenarios.py, not to
    # whichever PR happens to run next. An anchor THIS PR staled warns too when
    # the repair is mechanical (`fix` is a derived line number: the `field` and
    # `row` kinds, digits only) and FAILS only when it is not (`fix is None` —
    # a file anchor past end of file, which no command can compute a correct
    # value for and which therefore needs a human).
    #
    # WHY the derivable class was downgraded from a hard fail. A line anchor is
    # an ABSOLUTE line number into a file nearly every lane edits, so one
    # inserted field stales every anchor beneath it: PR #4870 inherited 100+
    # such errors from its own 132 inserted lines, and the two REAL rule-28(c)
    # registration errors were the last two lines of a job that was red for
    # anchors anyway — the PR merged through all of it
    # (FINDING-scn-mxr-2026-09-06 §1.2). Worse, the class is a treadmill: xiso-3
    # shipped this check with an empty ratchet and main re-staled 214 anchors
    # within the day, so a PR that clears them can be stale again before it
    # merges. A gate whose red usually means "you moved line numbers" trains
    # everyone to merge through red, which costs exactly the registration
    # failure it is stacked on top of. The check is NOT removed and nothing
    # about its measurement changes: every stale anchor is still reported with
    # its blame and its one-command repair, the shrink-only baseline still
    # holds, and the field NAME — the durable identifier, per this script's own
    # `--fix-anchors` message — was never what was at risk. What changes is only
    # that digit drift no longer decides this job's exit code, so a red guard
    # now means a mechanism is unregistered.
    base_stale: set[str] = set()
    try:
        base_scen = _git("show", f"{args.base}:{SCENARIOS_PATH}")
        # The pre-shard monolith AND the sharded files both live under these
        # paths across the migration boundary — collect whatever the base ref
        # actually has, so blame stays correct on either side.
        for rel in matrix_paths():
            old = _git("show", f"{args.base}:{rel}")
            if not old:
                continue
            base_findings, _ = anchor_findings(old, base_scen)
            base_stale |= {f["key"] for f in base_findings}
    except (subprocess.CalledProcessError, OSError):
        base_stale = set()  # base blobs unreachable: fail closed, blame nobody
    for f in anchor_errs:
        blame = (
            "pre-existing, not this PR"
            if f["key"] in base_stale
            else "staled by this PR"
        )
        if f["key"] not in base_stale and f["fix"] is None:
            failed = True
            print(
                f"::error file={f.get('path', MATRIX_PATH)}::mechanism-matrix "
                f"anchor ({blame}, NOT mechanically repairable): "
                f"{_anchor_message(f)}"
            )
        else:
            print(
                f"::warning file={f.get('path', MATRIX_PATH)}::mechanism-matrix "
                f"anchor ({blame}): {_anchor_message(f)}"
            )

    # A PR that MOVES a keeper shard owns that ISO's matrix stamp: fail. Drift
    # this PR did not create only warns — it belongs to the owning ISO's lane.
    for iso, header, shard in drift:
        matrix_shard = SHARD_PATH.format(iso=iso)
        if KEEPER_SHARD.format(iso=iso) in changed:
            failed = True
            print(
                f"::error file={matrix_shard}::{iso} keeper promoted to `{shard}` "
                f"in this PR but {matrix_shard} still stamps `{header}`. Rule 28 "
                f"[R-MECH-MATRIX]: the promoting session re-stamps its ISO's "
                f"matrix shard (keeper + gates, and re-checks that ISO's column) "
                f"in the SAME session."
            )
        else:
            print(
                f"::warning file={matrix_shard}::{iso} keeper stamp drift "
                f"(pre-existing, not this PR): matrix shard `{header}` != "
                f"keepers/{iso}.json `{shard}`. Belongs to the {iso} lane."
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
        unregistered = 0
        for field in sorted(new_fields):
            if not re.search(rf"\b{re.escape(field)}\b", matrix_text):
                failed = True
                unregistered += 1
                print(
                    f"::error file={SCENARIOS_PATH}::new ScenarioConfig field "
                    f"`{field}` is not registered in the mechanism matrix (rule "
                    f"28c [R-MECH-MATRIX]). Add its row in {MATRIX_PATH} (plus a "
                    f"cell line in each mechanism-matrix/<ISO>.js shard), or "
                    f"name the field in the owning row's def/note."
                )
        # Reported on the DIFF GATE's own result, not on `failed` — which now
        # carries the diff-free ratchets' verdict from above, so an unrelated
        # legacy gap would otherwise silence this line.
        if new_fields and not unregistered:
            print(f"mechanism-matrix: {len(new_fields)} new field(s) all registered")

    # --- rule 28(b) advisories ----------------------------------------------
    added = _git(
        "diff", "--name-only", "--diff-filter=A", args.base, "HEAD"
    ).splitlines()
    new_runs = [p for p in added if p.startswith(REGISTRY_PREFIX)]
    if new_runs and not matrix_touched:
        isos_hit = sorted(
            {
                iso
                for p in new_runs
                for iso in shard_docs
                if iso.lower() in Path(p).name.lower()
            }
        )
        hint = (
            " or ".join(SHARD_PATH.format(iso=i) for i in isos_hit)
            or "its ISO's mechanism-matrix/<ISO>.js shard"
        )
        print(
            f"::warning::PR registers {len(new_runs)} new backcast run(s) but does "
            f"not touch the mechanism matrix. If this run tested a mechanism "
            f"(probe, candidate, or keeper), rule 28b requires its cell verdict "
            f"updated in the same session — edit {hint}. Ignore if the run "
            f"re-exercises an already-recorded recipe."
        )
    if CALIB_CLI_PATH in changed:
        base_cli = _git("show", f"{args.base}:{CALIB_CLI_PATH}")
        head_cli = (REPO / CALIB_CLI_PATH).read_text(encoding="utf-8")
        for flag in sorted(cli_flags(head_cli) - cli_flags(base_cli)):
            token = flag.lstrip("-").replace("-", "_")
            if not re.search(rf"\b{re.escape(token)}\b", matrix_text):
                print(
                    f"::warning::new calibration CLI flag `{flag}` is not mentioned "
                    f"in the mechanism matrix (base {MATRIX_PATH} or any ISO "
                    f"shard). If it arms a solve-affecting mechanism, add or "
                    f"extend its row (rule 28c)."
                )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
