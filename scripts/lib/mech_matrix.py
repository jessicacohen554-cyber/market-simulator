"""Cross-ISO mechanism matrix — sharded store IO (rule 28 [R-MECH-MATRIX]).

Why shards (2026-08-11, HOUSE-3): the matrix used to pack all six ISOs' cell
verdicts into one six-character string per row (``cells: "KKKKKK"``, position =
ISO) inside a single ``docs/codebase-site/data/mechanism-matrix.js`` — so a PJM
lane and a MISO lane updating DIFFERENT ISOs' verdicts for the same mechanism
edited the same character of the same line. 21 distinct lanes touched the file
2026-08-08..10; the MISO leg alone took three union-merges (b9232406, bb1d8e32,
afc706b4) and one edit was silently lost and restored (c5593684). This mirrors
the per-ISO keeper-shard design of 2026-07-19
(``frontend/data/backcast/keepers/README.md``): per-ISO content lives in
per-ISO files, so parallel lanes never share an edit surface.

Layout:

    docs/codebase-site/data/mechanism-matrix.js         # BASE: mechanism-level
        window.MECH_MATRIX_BASE = { version, updated, isos, categories,
                                    rows: [{id, cat, name, def, mode, note,
                                            ev?: {cross-ISO keys only}, ...}] }
    docs/codebase-site/data/mechanism-matrix/<ISO>.js   # one shard per ISO
        window.MECH_MATRIX_SHARDS.<ISO> = {
            iso, updated, keeper, gates,
            cells: { <mechanism id>: { cell: "K", fc?: "O",
                                       ev?: "...", note?: "..." }, ... } }

The BASE row set (id/cat/name/def/mode + mechanism-level note) is edited ONCE,
by the single PR that adds the mechanism (rule 28c). An ISO's verdict, forecast
posture, evidence citation and per-ISO note live ONLY in that ISO's shard — a
lane's rule-28 duty is a one-file edit and two ISOs can never collide.

``load_merged()`` returns exactly the legacy monolith shape (cells/fc as
six-char strings in ``isos`` order, ``ev`` keyed E/C/P/M/N/Q/…, ``keepers`` and
``gates`` maps), so historical consumers keep one code path. The browser twin
of that assembly is ``docs/codebase-site/data/mechanism-matrix-assemble.js`` —
keep the two in sync.

Everything here is stdlib-only (the CI guard runs with bare python3). The
parser covers exactly the JS subset the matrix files use: one ``window.X = {…}``
assignment per file, object/array literals, double-quoted strings, numbers,
``/* … */`` comments, trailing commas. Import as
``from scripts.lib import mech_matrix`` (repo root on ``sys.path``) or via
``importlib`` file loading.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

BASE_PATH = "docs/codebase-site/data/mechanism-matrix.js"
SHARD_DIR = "docs/codebase-site/data/mechanism-matrix"
ASSEMBLE_PATH = "docs/codebase-site/data/mechanism-matrix-assemble.js"

# Cell order of the legacy `cells:`/`fc:` strings — must match the base file's
# `isos:` list (asserted by the CI guard, not assumed).
ISO_ORDER = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "SOCO", "NWPP")

# Per-ISO `ev` keys, as declared in the matrix header since day one (SPP added
# at SPP-21, 2026-09-06, with the seventh shard; SOCO at SOCO-21, 2026-09-13,
# with the eighth — its key is "O", ruled with the registry key at owner card
# S1, because "S" is SPP's; NWPP at NWPP-21, 2026-09-13, with the NINTH —
# "W" for Western, E C P M N Q S O being taken).
ISO_EV_KEY = {
    "ERCOT": "E",
    "CAISO": "C",
    "PJM": "P",
    "MISO": "M",
    "NYISO": "N",
    "NEISO": "Q",
    "SPP": "S",
    "SOCO": "O",
    "NWPP": "W",
}
EV_KEY_ISO = {v: k for k, v in ISO_EV_KEY.items()}
# Legacy spellings found in the pre-shard file; normalized to the canonical
# letter at the 2026-08-11 migration (key spelling only — values untouched).
EV_KEY_ALIASES = {"MISO": "M", "NE": "Q"}
PER_ISO_EV_KEYS = set(EV_KEY_ISO) | set(EV_KEY_ALIASES)

CELL_CHARS = set("KRIGOU.")

_ESCAPES = {
    '"': '"',
    "'": "'",
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "0": "\0",
}


# --------------------------------------------------------------------------
# JS-subset parser (values + source spans, so the base file can be derived
# surgically from the monolith without re-emitting untouched bytes)
# --------------------------------------------------------------------------


@dataclass
class Node:
    """One parsed JS value: ``value`` plus its [start, end) source span."""

    value: object
    start: int
    end: int
    pairs: list["Pair"] = field(default_factory=list)  # objects only
    items: list["Node"] = field(default_factory=list)  # arrays only


@dataclass
class Pair:
    """One ``key: value`` object entry with the spans a surgical cut needs."""

    key: str
    key_start: int  # offset of the key token
    node: Node
    end: int  # offset just past the value, OR past the trailing comma if any


class MatrixParseError(ValueError):
    """Parse failure, carrying the offset so callers can report a line."""

    def __init__(self, message: str, text: str, pos: int):
        line = text.count("\n", 0, pos) + 1
        super().__init__(f"line {line}: {message}")
        self.pos = pos
        self.line = line


class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.n = len(text)
        self.i = 0

    def err(self, msg: str) -> MatrixParseError:
        return MatrixParseError(msg, self.text, self.i)

    def skip_ws(self) -> None:
        t, n = self.text, self.n
        while self.i < n:
            c = t[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif t.startswith("/*", self.i):
                end = t.find("*/", self.i + 2)
                if end < 0:
                    raise self.err("unterminated /* comment")
                self.i = end + 2
            elif t.startswith("//", self.i):
                end = t.find("\n", self.i)
                self.i = n if end < 0 else end
            else:
                return

    def parse_value(self) -> Node:
        self.skip_ws()
        if self.i >= self.n:
            raise self.err("unexpected end of input")
        c = self.text[self.i]
        if c == "{":
            return self.parse_object()
        if c == "[":
            return self.parse_array()
        if c in "\"'":
            return self.parse_string()
        if c.isdigit() or c == "-":
            return self.parse_number()
        return self.parse_ident()

    def parse_object(self) -> Node:
        start = self.i
        self.i += 1  # {
        pairs: list[Pair] = []
        value: dict[str, object] = {}
        while True:
            self.skip_ws()
            if self.i >= self.n:
                raise self.err("unterminated object")
            if self.text[self.i] == "}":
                self.i += 1
                return Node(value, start, self.i, pairs=pairs)
            key_start = self.i
            key = self.parse_key()
            self.skip_ws()
            if self.i >= self.n or self.text[self.i] != ":":
                raise self.err(f"expected `:` after key `{key}`")
            self.i += 1
            node = self.parse_value()
            end = self.i
            self.skip_ws()
            if self.i < self.n and self.text[self.i] == ",":
                self.i += 1
                end = self.i
            pairs.append(Pair(key, key_start, node, end))
            if key in value:
                raise self.err(f"duplicate key `{key}`")
            value[key] = node.value

    def parse_array(self) -> Node:
        start = self.i
        self.i += 1  # [
        items: list[Node] = []
        while True:
            self.skip_ws()
            if self.i >= self.n:
                raise self.err("unterminated array")
            if self.text[self.i] == "]":
                self.i += 1
                return Node([n.value for n in items], start, self.i, items=items)
            items.append(self.parse_value())
            self.skip_ws()
            if self.i < self.n and self.text[self.i] == ",":
                self.i += 1

    def parse_key(self) -> str:
        c = self.text[self.i]
        if c in "\"'":
            return str(self.parse_string().value)
        j = self.i
        while j < self.n and (self.text[j].isalnum() or self.text[j] in "_$"):
            j += 1
        if j == self.i:
            raise self.err("expected object key")
        key = self.text[self.i : j]
        self.i = j
        return key

    def parse_string(self) -> Node:
        start = self.i
        quote = self.text[start]
        out: list[str] = []
        i, t, n = start + 1, self.text, self.n
        while i < n:
            c = t[i]
            if c == "\\":
                if i + 1 >= n:
                    raise self.err("dangling escape")
                e = t[i + 1]
                if e == "u":
                    out.append(chr(int(t[i + 2 : i + 6], 16)))
                    i += 6
                elif e == "x":
                    out.append(chr(int(t[i + 2 : i + 4], 16)))
                    i += 4
                elif e in _ESCAPES:
                    out.append(_ESCAPES[e])
                    i += 2
                else:
                    out.append(e)
                    i += 2
            elif c == quote:
                self.i = i + 1
                return Node("".join(out), start, self.i)
            elif c == "\n":
                raise self.err("unterminated string (raw newline)")
            else:
                out.append(c)
                i += 1
        raise self.err("unterminated string")

    def parse_number(self) -> Node:
        start = self.i
        j = self.i
        while j < self.n and (self.text[j].isdigit() or self.text[j] in "+-.eE"):
            j += 1
        raw = self.text[start:j]
        self.i = j
        try:
            value: object = int(raw)
        except ValueError:
            value = float(raw)
        return Node(value, start, j)

    def parse_ident(self) -> Node:
        start = self.i
        j = self.i
        while j < self.n and (self.text[j].isalnum() or self.text[j] in "_$."):
            j += 1
        raw = self.text[start:j]
        if not raw:
            raise self.err(f"unexpected character {self.text[self.i]!r}")
        self.i = j
        value = {"true": True, "false": False, "null": None}.get(raw, raw)
        return Node(value, start, j)


def parse_assignment(text: str, marker: str = "window.MECH_MATRIX") -> Node:
    """Parse the ``window.MECH_MATRIX* = {…}`` object literal out of file text.

    ``marker`` is a prefix — it matches ``window.MECH_MATRIX``,
    ``window.MECH_MATRIX_BASE`` and ``window.MECH_MATRIX_SHARDS.<ISO>`` alike.
    Only assignments at the START of a line count (the block-comment headers
    mention the marker in prose), and ``window.X = window.X || {};`` guard
    lines are skipped: the winner is the first line-start assignment whose
    right side is an object literal.
    """
    pat = re.compile(rf"^{re.escape(marker)}[\w.$]*\s*=", re.M)
    for m in pat.finditer(text):
        p = _Parser(text)
        p.i = m.end()
        p.skip_ws()
        if p.i < p.n and p.text[p.i] == "{":
            return p.parse_value()
    raise MatrixParseError(f"no `{marker} = {{…}}` assignment found", text, 0)


# --------------------------------------------------------------------------
# Loading (merged legacy shape)
# --------------------------------------------------------------------------


def shard_path(iso: str, repo: Path | None = None) -> Path:
    return (repo or REPO) / SHARD_DIR / f"{iso}.js"


def base_path(repo: Path | None = None) -> Path:
    return (repo or REPO) / BASE_PATH


def load_base(repo: Path | None = None) -> dict:
    return parse_assignment(
        base_path(repo).read_text(encoding="utf-8"), "window.MECH_MATRIX"
    ).value


def load_shard(iso: str, repo: Path | None = None) -> dict:
    return parse_assignment(
        shard_path(iso, repo).read_text(encoding="utf-8"),
        f"window.MECH_MATRIX_SHARDS.{iso}",
    ).value


def assemble(base: dict, shards: dict[str, dict]) -> dict:
    """Merge base + per-ISO shards back into the legacy monolith shape.

    Browser twin: ``mechanism-matrix-assemble.js`` — keep in sync. A mechanism
    id missing from a shard raises (the CI guard requires full coverage, so a
    landed matrix never hits this); a per-ISO ``fc`` left unset falls back to
    that ISO's backcast cell, matching the legacy convention that a row with no
    ``fc`` string has forecast posture = backcast cells.
    """
    isos = list(base.get("isos") or ISO_ORDER)
    rows = []
    for row in base["rows"]:
        rid = row["id"]
        cells, fc, any_fc = [], [], False
        ev: dict[str, str] = dict(row.get("ev") or {})
        iso_notes: dict[str, str] = {}
        for iso in isos:
            entry = shards[iso]["cells"].get(rid)
            if entry is None:
                raise KeyError(f"{iso} shard has no cell for mechanism `{rid}`")
            ch = entry["cell"]
            cells.append(ch)
            if "fc" in entry:
                any_fc = True
                fc.append(entry["fc"])
            else:
                fc.append(ch)
            if "ev" in entry:
                ev[ISO_EV_KEY[iso]] = entry["ev"]
            if "note" in entry:
                iso_notes[iso] = entry["note"]
        out = {k: v for k, v in row.items() if k not in ("ev",)}
        out["cells"] = "".join(cells)
        if any_fc:
            out["fc"] = "".join(fc)
        if ev:
            out["ev"] = ev
        if iso_notes:
            out["iso_notes"] = iso_notes
        rows.append(out)
    return {
        "version": base.get("version"),
        "updated": max(
            [str(base.get("updated") or "")]
            + [str(shards[i].get("updated") or "") for i in isos]
        ),
        "isos": isos,
        "keepers": {i: shards[i].get("keeper", "") for i in isos},
        "gates": {i: shards[i].get("gates", "") for i in isos},
        "categories": base.get("categories", []),
        "rows": rows,
    }


def load_merged(repo: Path | None = None) -> dict:
    """The full matrix in the legacy monolith shape, from the sharded store."""
    base = load_base(repo)
    isos = list(base.get("isos") or ISO_ORDER)
    return assemble(base, {iso: load_shard(iso, repo) for iso in isos})


def all_matrix_paths(repo: Path | None = None) -> list[Path]:
    """Base + every ISO shard, the full rule-28 edit surface, base first."""
    root = repo or REPO
    isos: tuple[str, ...] = ISO_ORDER
    try:
        base = load_base(root)
        isos = tuple(base.get("isos") or ISO_ORDER)
    except (OSError, ValueError):
        pass
    return [base_path(root)] + [shard_path(i, root) for i in isos]


# --------------------------------------------------------------------------
# Rule-28(c) field census — ONE recogniser, ONE predicate, both halves
# --------------------------------------------------------------------------
#
# Two scripts have to agree, exactly, about which `ScenarioConfig` fields exist
# and which of them the matrix already names: `mechanism_matrix_gap_sweep.py`
# WRITES the shrink-only baseline and `check_mechanism_matrix.py` ENFORCES it.
# When the two disagreed once before — `\b` vs substring matching, seven fields
# — the checker came out STRICTER than the sweep and the baseline it demanded
# could never be written (tests/unit/config/test_mechanism_matrix_shared_ratchet
# pins that lesson). The fix is not a comment asking for sync: it is that the
# recogniser and the predicate live here, once, and both scripts call them.

# Each ISO's own field stems, incl. the regulator prefixes whose fields are that
# ISO's exclusively (NYSDEC rules bind only New York units). Matched as
# `<stem>_`, never as a bare substring, so `carbon_price` is never read as a
# CARB field. Was duplicated in both scripts under a "keep in sync" comment.
ISO_FIELD_STEMS: dict[str, tuple[str, ...]] = {
    "ERCOT": ("ercot",),
    "CAISO": ("caiso",),
    "PJM": ("pjm",),
    "MISO": ("miso",),
    "NYISO": ("nyiso", "nysdec"),
    "NEISO": ("neiso",),
    "SPP": ("spp",),
    # NWPP-21 (2026-09-13), with the eighth shard. A NO-OP at that commit and
    # measured as one: `scenarios.py` carries ZERO `nwpp_*` fields, so every
    # ratchet line is byte-identical before and after. Registered anyway so the
    # FIRST `nwpp_*` field (NWPP-36's coupling gate, if it takes an ISO stem)
    # is classed ISO-scoped rather than silently falling into the SHARED
    # complement — the exact hole `absent_shared_fields` was written to close.
    "NWPP": ("nwpp",),
}


def iso_field_prefixes() -> tuple[str, ...]:
    """Every ISO stem as the `<stem>_` prefix the census actually matches."""
    return tuple(f"{s}_" for stems in ISO_FIELD_STEMS.values() for s in stems)


def is_iso_scoped(field: str) -> bool:
    """True when a field belongs to one ISO's family (`pjm_*`, `nysdec_*`, …).

    The complement is the SHARED family: everything an ISO-scoped census can
    never see, which is where the rule-28(c) hole this predicate closes lived.
    """
    return field.startswith(iso_field_prefixes())


def scenarioconfig_field_names(source: str) -> set[str]:
    """`ScenarioConfig` field names, parsed from `scenarios.py` source text.

    A 4-space-indented ``name:`` inside the class body, `_`-prefixed names
    dropped. Text, not an import, because the CI guard runs stdlib-only (no
    ``uv sync``) — and NAMES need no import: registration asks whether the
    matrix mentions the name, never what the field defaults to. Measured
    against the live dataclass at 798 = 798 fields, exactly (the sweep
    re-asserts that every time it writes the baseline).
    """
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


def absent_shared_fields(names: Iterable[str], matrix_text: str) -> list[str]:
    """Shared fields whose name appears NOWHERE in the matrix text.

    `matrix_text` is the base file plus every ISO shard (:func:`all_matrix_paths`
    — a field named only in one shard's ev/note counts as registered, the same
    mention-anywhere escape hatch rule 28(c) grants everywhere else).

    Case-insensitive on both sides: the sweep lowercased its mention blob and
    the checker did not, which is the same asymmetry class as the `\\b` bug.
    Lowercasing here means neither can drift into being the stricter one.
    """
    blob = matrix_text.lower()
    return sorted(f for f in names if not is_iso_scoped(f) and f.lower() not in blob)


# --------------------------------------------------------------------------
# Split (the migration transform; also what the byte-faithfulness test
# round-trips against the frozen pre-shard fixture)
# --------------------------------------------------------------------------


def _normalize_ev_key(key: str) -> str:
    return EV_KEY_ALIASES.get(key, key)


def split_monolith(text: str) -> tuple[str, dict[str, str]]:
    """Split pre-shard monolith text into (base_text, {ISO: shard_text}).

    Mechanical, not editorial: the base is the ORIGINAL text minus the per-ISO
    spans (``keepers:``/``gates:`` blocks, each row's ``cells:``/``fc:`` pair
    and per-ISO ``ev`` keys), so comments, notes and layout survive
    byte-for-byte; shards are emitted from the parsed per-ISO values. Verdict
    characters and citations are moved, never altered — the only normalization
    is legacy ``ev`` key spellings (``MISO``→``M``, ``NE``→``Q``), values
    untouched.
    """
    top = parse_assignment(text, "window.MECH_MATRIX")
    doc = top.value
    isos = list(doc.get("isos") or ISO_ORDER)
    updated = str(doc.get("updated") or "")
    cuts: list[tuple[int, int]] = []

    keepers = doc.get("keepers") or {}
    gates = doc.get("gates") or {}
    rows_node = None
    for pr in top.pairs:
        if pr.key in ("keepers", "gates"):
            cuts.append((pr.key_start, pr.end))
        elif pr.key == "rows":
            rows_node = pr.node
    if rows_node is None:
        raise MatrixParseError("monolith has no `rows`", text, top.start)

    # Per-ISO shard payloads: {iso: {rid: {cell, fc?, ev?}}}
    per_iso: dict[str, dict[str, dict[str, str]]] = {i: {} for i in isos}
    row_ids: list[str] = []

    for row_node in rows_node.items:
        row = row_node.value
        rid = row["id"]
        row_ids.append(rid)
        cells = row.get("cells")
        if not isinstance(cells, str) or len(cells) != len(isos):
            raise MatrixParseError(
                f"row `{rid}` has no {len(isos)}-char `cells` string",
                text,
                row_node.start,
            )
        fc = row.get("fc")
        for idx, iso in enumerate(isos):
            entry: dict[str, str] = {"cell": cells[idx]}
            if isinstance(fc, str) and len(fc) == len(isos):
                entry["fc"] = fc[idx]
            per_iso[iso][rid] = entry
        for pr in row_node.pairs:
            if pr.key in ("cells", "fc"):
                cuts.append((pr.key_start, pr.end))
            elif pr.key == "ev":
                sub = pr.node.pairs
                iso_subs = [s for s in sub if _normalize_ev_key(s.key) in EV_KEY_ISO]
                for s in iso_subs:
                    iso = EV_KEY_ISO[_normalize_ev_key(s.key)]
                    per_iso[iso][rid]["ev"] = str(s.node.value)
                if len(iso_subs) == len(sub):
                    cuts.append((pr.key_start, pr.end))  # ev is wholly per-ISO
                else:
                    cuts.extend((s.key_start, s.end) for s in iso_subs)

    base_text = _cut_spans(text, cuts)
    shards = {
        iso: emit_shard(
            iso,
            updated=updated,
            keeper=str(keepers.get(iso, "")),
            gates=str(gates.get(iso, "")),
            cells=per_iso[iso],
            row_order=row_ids,
        )
        for iso in isos
    }
    return base_text, shards


def _cut_spans(text: str, cuts: list[tuple[int, int]]) -> str:
    """Remove spans, tidying whitespace so own-line cuts take the whole line."""
    out = text
    for a, b in sorted(cuts, reverse=True):
        # Swallow trailing spaces; if the cut then sits at end-of-line and the
        # remainder of its own line is only indent, take the newline + indent.
        while b < len(out) and out[b] in " \t":
            b += 1
        a0 = a
        while a0 > 0 and out[a0 - 1] in " \t":
            a0 -= 1
        if (a0 == 0 or out[a0 - 1] == "\n") and b < len(out) and out[b] == "\n":
            a, b = a0, b + 1  # the pair owned its line(s): remove them fully
        out = out[:a] + out[b:]
    return out


def _js_str(value: str) -> str:
    """A double-quoted JS string literal (JSON escaping is valid JS)."""
    return json.dumps(value, ensure_ascii=False)


def emit_shard(
    iso: str,
    *,
    updated: str,
    keeper: str,
    gates: str,
    cells: dict[str, dict[str, str]],
    row_order: list[str],
    stamp_log: str = "",
) -> str:
    """Render one ISO shard file. One mechanism per line, base row order."""
    lines = [
        f"/* Cross-ISO mechanism matrix — {iso} shard (rule 28 [R-MECH-MATRIX]).",
        " *",
        f" * This file is {iso}'s COLUMN of the matrix: one line per mechanism id",
        " * (the row set lives in ../mechanism-matrix.js, which carries the",
        " * mechanism-level id/cat/name/def/mode/note). A session that tests a",
        f" * mechanism in {iso} updates ONLY this file — the cell verdict, the",
        " * forecast-lane posture (fc), the evidence citation (ev) and any",
        f" * {iso}-specific note — plus the keeper/gates stamps on promotion.",
        " * Never edit another ISO's shard (rule 25 [R-ISO-SCOPE]): a verdict",
        " * transfers to no other ISO; candidates enter the target shard as U.",
        " *",
        " * Cell codes (same vocabulary as the base header): K keeper, R rejected,",
        " * I inert, G governance-refused/closed, O open, U untested, . n/a.",
        " * `fc` is the forecast-lane posture where it DIFFERS from the backcast",
        " * cell (omitted = same as cell). `ev` is this ISO's evidence citation.",
        " *",
        f" * Append {iso} column re-stamp history as block comments at the END",
        " * of this file (the pre-2026-08-11 mixed-ISO stamp log stays frozen in",
        " * the base file's header).",
        " */",
        "window.MECH_MATRIX_SHARDS = window.MECH_MATRIX_SHARDS || {};",
        f"window.MECH_MATRIX_SHARDS.{iso} = {{",
        f"  iso: {_js_str(iso)},",
        f"  updated: {_js_str(updated)},",
        f"  keeper: {_js_str(keeper)},",
        f"  gates: {_js_str(gates)},",
        "  cells: {",
    ]
    for rid in row_order:
        entry = cells[rid]
        parts = [f"cell: {_js_str(entry['cell'])}"]
        if "fc" in entry:
            parts.append(f"fc: {_js_str(entry['fc'])}")
        if "ev" in entry:
            parts.append(f"ev: {_js_str(entry['ev'])}")
        if "note" in entry:
            parts.append(f"note: {_js_str(entry['note'])}")
        lines.append(f"    {rid}: {{ {', '.join(parts)} }},")
    lines += ["  },", "};", ""]
    if stamp_log:
        lines.append(stamp_log)
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Canonical comparison (the byte-faithfulness gate)
# --------------------------------------------------------------------------


def canonical(doc: dict) -> dict:
    """Reduce a monolith-shaped matrix doc to its comparable content.

    Per mechanism × ISO: the cell verdict char, the forecast char (with the
    legacy row-absent ⇒ cells fallback applied) and the per-ISO evidence
    citation (legacy key spellings normalized); plus every mechanism-level
    field, the keeper/gates stamps and the header lists. Two docs with equal
    ``canonical()`` carry identical verdicts and citations everywhere.
    """
    isos = list(doc.get("isos") or ISO_ORDER)
    rows_out = {}
    for row in doc["rows"]:
        ev = {_normalize_ev_key(k): v for k, v in (row.get("ev") or {}).items()}
        fc = row.get("fc")
        if not (isinstance(fc, str) and len(fc) == len(isos)):
            fc = row["cells"]
        per_iso = {
            iso: {
                "cell": row["cells"][i],
                "fc": fc[i],
                "ev": ev.get(ISO_EV_KEY[iso]),
                "note": (row.get("iso_notes") or {}).get(iso),
            }
            for i, iso in enumerate(isos)
        }
        rows_out[row["id"]] = {
            "meta": {
                k: v
                for k, v in row.items()
                if k not in ("cells", "fc", "ev", "iso_notes")
            },
            "cross_ev": {k: v for k, v in ev.items() if k not in EV_KEY_ISO},
            "per_iso": per_iso,
        }
    return {
        "isos": isos,
        "keepers": {i: doc.get("keepers", {}).get(i, "") for i in isos},
        "gates": {i: doc.get("gates", {}).get(i, "") for i in isos},
        "categories": doc.get("categories", []),
        "rows": rows_out,
    }
