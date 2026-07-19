"""Generate / refresh the parameter-citation registry from the model code.

The registry (``frontend/data/parameters.json`` and its human companion
``docs/parameter-citations.md``) must carry one entry for every constant in
``config/constants.py`` and every ``ScenarioConfig`` default, or
``scripts/validate_parameters.py`` fails CI. As the model grows, new
parameters outpace the hand-maintained registry. This generator closes the
gap:

* It reuses ``validate_parameters.expected_param_ids()`` so the ``param_id``
  and value of every entry match the validator exactly.
* **Existing curated entries are preserved** (their hand-written source,
  notes, url, tier …); only their ``value`` is refreshed to the current code
  value so value-mismatch warnings clear.
* **Missing parameters get a new entry** with the value and a best-effort
  citation harvested from the inline / preceding ``#`` comment on the
  constant (the project keeps a citation comment on every constant). When no
  usable source text is found the entry is flagged ``needs-citation`` and left
  with an empty ``source_date`` so the validator queues it for review — the
  number is registered (CI passes) but the human still owes a primary source.
* Orphan entries (registry ids no longer in the code) are kept untouched.

Run::

    python scripts/generate_parameter_registry.py          # write both files
    python scripts/generate_parameter_registry.py --check   # write, then validate

This is intentionally idempotent: re-running after adding constants appends
only the new ids.
"""

from __future__ import annotations

import ast
import dataclasses
import datetime as dt
import io
import json
import re
import sys
import tokenize
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
CONSTANTS_PY = SRC / "market_sim" / "config" / "constants.py"
SCENARIOS_PY = SRC / "market_sim" / "config" / "scenarios.py"
REGISTRY_PATH = REPO / "frontend" / "data" / "parameters.json"
CITATIONS_MD = REPO / "docs" / "parameter-citations.md"

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(REPO / "scripts"))

from validate_parameters import expected_param_ids  # noqa: E402
from market_sim.config.scenarios import TIER_TAGS  # noqa: E402

TODAY = dt.date.today().strftime("%Y-%m-%d")
_DATE_RE = re.compile(r"\b(19|20)\d{2}(?:-\d{2})?\b")

# param_id keyword -> reporting domain, first match wins.
_DOMAIN_RULES: list[tuple[str, str]] = [
    ("heat_rate", "Supply Stack"),
    ("tranche", "Supply Stack"),
    ("offer_curve", "Supply Stack"),
    ("commitment", "Supply Stack"),
    ("startup", "Supply Stack"),
    ("vom", "Supply Stack"),
    ("ccs", "Supply Stack"),
    ("ccus", "Supply Stack"),
    ("storage", "Storage"),
    ("elcc", "Storage"),
    ("market_design", "Market Design"),
    ("emission", "Emissions"),
    ("co2", "Emissions"),
    ("nox", "Emissions"),
    ("so2", "Emissions"),
    ("carbon", "Emissions"),
    ("eford", "Reliability"),
    ("wefor", "Reliability"),
    ("availability", "Reliability"),
    ("outage", "Reliability"),
    ("reserve", "Reliability"),
    ("retirement", "Reliability"),
    ("voll", "Reliability"),
    ("demand", "Demand"),
    ("growth", "Demand"),
    ("load", "Demand"),
    ("gas", "Fuel Prices"),
    ("coal", "Fuel Prices"),
    ("fuel", "Fuel Prices"),
    ("henry_hub", "Fuel Prices"),
    ("price", "Fuel Prices"),
    ("hydrogen", "Emerging Tech"),
    ("h2", "Emerging Tech"),
    ("electrolyzer", "Emerging Tech"),
    ("geothermal", "Emerging Tech"),
    ("offshore", "Emerging Tech"),
    ("ira", "Policy"),
    ("rps", "Policy"),
    ("ptc", "Policy"),
    ("itc", "Policy"),
    ("eac", "Policy"),
    ("learning", "Cost Trajectories"),
    ("capex", "Cost Trajectories"),
    ("crf", "Cost Trajectories"),
    ("discount", "Cost Trajectories"),
    ("ttc", "Transmission"),
    ("zone", "Transmission"),
    ("basis", "Transmission"),
    ("hydro", "Hydro"),
    ("nuclear", "Supply Stack"),
]


def _domain_for(pid: str) -> str:
    low = pid.lower()
    for kw, dom in _DOMAIN_RULES:
        if kw in low:
            return dom
    return "Structural" if pid.startswith("scenario.") else "Uncategorized"


def _display_name(pid: str) -> str:
    tail = pid.split(".", 1)[1] if pid.startswith("scenario.") else pid
    return tail.replace("_", " ").replace(".", " / ").title()


def harvest_comments(path: Path) -> tuple[dict[int, str], set[int]]:
    """Return ``(inline_by_line, standalone_lines)`` for a source file.

    ``inline_by_line[n]`` is the text (``#`` stripped) of a comment that shares
    line ``n`` with code; ``standalone_lines`` holds line numbers that are
    comment-only, used to walk a preceding comment block.
    """
    inline: dict[int, str] = {}
    standalone: set[int] = set()
    src = path.read_text()
    lines = src.splitlines()
    try:
        toks = tokenize.generate_tokens(io.StringIO(src).readline)
        for tok in toks:
            if tok.type != tokenize.COMMENT:
                continue
            row, col = tok.start
            text = tok.string.lstrip("#").strip()
            before = lines[row - 1][:col] if row - 1 < len(lines) else ""
            if before.strip():
                inline[row] = text
            else:
                standalone.add(row)
    except tokenize.TokenError:
        pass
    return inline, standalone


def _block_before(
    lineno: int, inline: dict[int, str], standalone: set[int], raw: list[str]
) -> str:
    """Concatenate the run of comment-only lines immediately above ``lineno``."""
    out: list[str] = []
    n = lineno - 1
    while n >= 1 and n in standalone:
        out.append(raw[n - 1].strip().lstrip("#").strip())
        n -= 1
    return " ".join(reversed(out)).strip()


def _top_level_ranges(path: Path) -> dict[str, tuple[int, int]]:
    """Map each upper-case top-level constant to its ``(lineno, end_lineno)``."""
    tree = ast.parse(path.read_text())
    ranges: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for t in targets:
            if isinstance(t, ast.Name) and t.id.isupper():
                ranges[t.id] = (node.lineno, getattr(node, "end_lineno", node.lineno))
    return ranges


def _scenario_field_lines(path: Path) -> dict[str, int]:
    """Map each ``ScenarioConfig`` field name to the line of its definition."""
    tree = ast.parse(path.read_text())
    out: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ScenarioConfig":
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(
                    stmt.target, ast.Name
                ):
                    out[stmt.target.id] = stmt.lineno
    return out


def _source_for_constant_leaf(
    pid: str,
    name_map: dict[str, str],
    ranges: dict[str, tuple[int, int]],
    inline: dict[int, str],
    standalone: set[int],
    raw: list[str],
) -> str:
    """Best-effort citation text for a constants.py param_id."""
    root_lower = pid.split(".")[0]
    cname = name_map.get(root_lower)
    if cname is None or cname not in ranges:
        return ""
    lo, hi = ranges[cname]
    block = _block_before(lo, inline, standalone, raw)
    if "." not in pid:  # whole-constant leaf (scalar / list / year-dict)
        return (inline.get(lo) or block or "").strip()
    # Nested leaf: find the line in the constant's range carrying the last key.
    last = pid.split(".")[-1]
    pats = (f'"{last}"', f"'{last}'", f"{last}:", f"{last} ")
    for ln in range(lo, hi + 1):
        text = raw[ln - 1] if ln - 1 < len(raw) else ""
        stripped = text.strip()
        if any(stripped.startswith(p) for p in pats) or any(
            p in stripped for p in pats[:2]
        ):
            if ln in inline:
                return inline[ln].strip()
    return block.strip()


def _make_entry(pid: str, value: object, source: str, tier: int) -> dict:
    source = (source or "").strip()
    date_m = _DATE_RE.search(source)
    source_date = date_m.group(0) if date_m else ""
    flags = ["auto-generated"]
    if not source:
        source = "NEEDS CITATION — no source comment found in code"
        flags.append("needs-citation")
    elif not source_date:
        # has prose but no parseable date — still wants a dated primary source
        flags.append("needs-citation")
    return {
        "param_id": pid,
        "display_name": _display_name(pid),
        "value": value,
        "unit": "",
        "domain": _domain_for(pid),
        "tier": tier,
        "source": source,
        "source_date": source_date,
        "page_or_table": "",
        "url": "",
        "notes": "Auto-generated entry; citation harvested from the constant's "
        "inline comment. Verify and complete before relying on it.",
        "old_repo_location": "",
        "last_verified": "",
        "flags": flags,
    }


def _json_safe(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: _json_safe(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, (set, frozenset)):
        # Sets iterate in per-process-random order (randomized string
        # hashing), so an unsorted conversion churns the registry value on
        # every regeneration (seen with RGGI_MEMBER_STATES_BY_YEAR's
        # frozensets). Sort for a deterministic representation.
        return sorted((_json_safe(v) for v in value), key=str)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _tier_for(pid: str) -> int:
    if pid.startswith("scenario."):
        return TIER_TAGS.get(pid[len("scenario.") :], 2)
    # Structural-ish constants default to Tier 0; everything else Tier 2.
    low = pid
    if any(low.startswith(p) for p in ("hours", "voll", "iso", "zone")):
        return 0
    return 2


def _repair_stale_script_paths(entries: list[dict]) -> int:
    """Repair provenance citations whose ``scripts/<...>.py`` path went stale.

    The registry preserves each existing entry's harvested/hand-written
    ``source`` across regenerations (only ``value`` is refreshed). When a cited
    derivation script is *moved* on disk — e.g. the 2026-07 ``scripts/`` reorg
    that relocated the ``derive_*``/``fetch_*``/``curate_*`` builders under
    ``scripts/data/`` — the preserved citation keeps pointing at the old path and
    silently dangles. This pass rewrites any ``scripts/<...>.py`` token in a
    ``source`` that no longer resolves to the *unique* current on-disk location
    of that basename under ``scripts/``. Ambiguous (multiple matches) or vanished
    (no match) basenames are left untouched so a genuine deletion still surfaces
    for a human. Deterministic and filesystem-driven, so a re-run after any
    future move self-heals the citation.

    Returns the number of tokens rewritten.
    """
    locs: dict[str, list[str]] = {}
    for p in sorted((REPO / "scripts").rglob("*.py")):
        locs.setdefault(p.name, []).append(p.relative_to(REPO).as_posix())

    token_re = re.compile(r"scripts/(?:[A-Za-z0-9_./-]+/)?[A-Za-z0-9_.-]+\.py")
    repaired = 0

    def _repl(m: re.Match[str]) -> str:
        nonlocal repaired
        ref = m.group(0)
        if (REPO / ref).exists():
            return ref  # still resolves — leave it
        cands = [c for c in locs.get(Path(ref).name, []) if c != ref]
        if len(cands) == 1:
            repaired += 1
            return cands[0]
        return ref  # 0 or >1 candidates: gone/ambiguous — leave for a human

    for e in entries:
        src = e.get("source")
        if isinstance(src, str) and "scripts/" in src:
            e["source"] = token_re.sub(_repl, src)
    return repaired


def build_registry() -> tuple[dict, dict]:
    expected = expected_param_ids()

    registry = json.loads(REGISTRY_PATH.read_text())
    entries = registry["parameters"] if isinstance(registry, dict) else registry
    by_id = {e["param_id"]: e for e in entries}

    # Harvest comment context from both source files.
    const_inline, const_standalone = harvest_comments(CONSTANTS_PY)
    const_raw = CONSTANTS_PY.read_text().splitlines()
    const_ranges = _top_level_ranges(CONSTANTS_PY)
    name_map = {n.lower(): n for n in const_ranges}

    scen_inline, scen_standalone = harvest_comments(SCENARIOS_PY)
    scen_raw = SCENARIOS_PY.read_text().splitlines()
    scen_field_lines = _scenario_field_lines(SCENARIOS_PY)

    stats = {"existing": 0, "value_fixed": 0, "added": 0}

    for pid, value in expected.items():
        jvalue = _json_safe(value)
        if pid in by_id:
            stats["existing"] += 1
            if by_id[pid].get("value") != jvalue:
                by_id[pid]["value"] = jvalue
                stats["value_fixed"] += 1
            continue
        # Missing — harvest a citation and synthesize an entry.
        if pid.startswith("scenario."):
            fname = pid[len("scenario.") :]
            ln = scen_field_lines.get(fname)
            source = ""
            if ln:
                source = scen_inline.get(ln) or _block_before(
                    ln, scen_inline, scen_standalone, scen_raw
                )
        else:
            source = _source_for_constant_leaf(
                pid, name_map, const_ranges, const_inline, const_standalone, const_raw
            )
        entry = _make_entry(pid, jvalue, source, _tier_for(pid))
        by_id[pid] = entry
        entries.append(entry)
        stats["added"] += 1

    # Re-key into a deterministic order: existing curated ids first (original
    # order), then newly added ids sorted by param_id.
    existing_order = [e for e in entries if "auto-generated" not in e.get("flags", [])]
    added = sorted(
        (e for e in entries if "auto-generated" in e.get("flags", [])),
        key=lambda e: e["param_id"],
    )
    ordered = existing_order + added

    # Self-heal citations whose scripts/ provenance path moved (e.g. the 2026-07
    # scripts/ reorg). Preserved sources otherwise keep dangling silently.
    stats["script_paths_repaired"] = _repair_stale_script_paths(ordered)

    out = registry if isinstance(registry, dict) else {"parameters": ordered}
    if isinstance(out, dict):
        out["parameters"] = ordered
        out["generated"] = TODAY
        out.setdefault("schema_version", 1)
    return out, stats


# --- human-readable markdown rendering ------------------------------------

_MD_HEADER = """# Parameter Citation Registry

_Generated {date}. Every numeric input to the model traces to a primary source
here. This file is rendered from `frontend/data/parameters.json` by
`scripts/generate_parameter_registry.py`; edit citations in the JSON (or the
constant's comment, then re-run the generator), not here._

This document is the human-readable companion to `frontend/data/parameters.json`
(the machine-readable registry). `scripts/validate_parameters.py` fails CI if any
constant in `src/market_sim/config/constants.py` or any `ScenarioConfig` default
lacks an entry.

Entries flagged **needs-citation** were auto-registered from the constant's
inline comment and still need a dated primary source — search the table for
`needs-citation`.

## How `param_id` is derived

- A module-level constant in `constants.py` becomes its lower-cased name (e.g.
  `HOURS_PER_YEAR` -> `hours_per_year`).
- Nested dicts with string keys are flattened with dots (e.g.
  `HEAT_RATE_BINS["gas_cc"]["h_class"]` -> `heat_rate_bins.gas_cc.h_class`).
- A dict whose keys are all years is treated as a single leaf.
- `ScenarioConfig` dataclass defaults are prefixed with `scenario.`.

"""


def render_markdown(registry: dict) -> str:
    entries = registry["parameters"] if isinstance(registry, dict) else registry
    by_domain: dict[str, list[dict]] = {}
    for e in entries:
        by_domain.setdefault(e.get("domain", "Uncategorized"), []).append(e)

    parts = [_MD_HEADER.format(date=TODAY)]
    total = len(entries)
    needs = sum(1 for e in entries if "needs-citation" in e.get("flags", []))
    parts.append(
        f"**{total} parameters registered** ({needs} flagged `needs-citation`).\n"
    )
    for domain in sorted(by_domain):
        rows = sorted(by_domain[domain], key=lambda e: e["param_id"])
        parts.append(f"\n## {domain}\n")
        parts.append("| param_id | value | tier | source | date | flags |")
        parts.append("|---|---|---|---|---|---|")
        for e in rows:
            val = e.get("value")
            vstr = json.dumps(val) if isinstance(val, (dict, list)) else str(val)
            if len(vstr) > 40:
                vstr = vstr[:37] + "…"
            src = (e.get("source") or "").replace("|", "\\|")
            if len(src) > 70:
                src = src[:67] + "…"
            flags = ", ".join(e.get("flags", []))
            parts.append(
                f"| `{e['param_id']}` | {vstr} | {e.get('tier', '')} | "
                f"{src} | {e.get('source_date', '')} | {flags} |"
            )
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    registry, stats = build_registry()
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    CITATIONS_MD.write_text(render_markdown(registry))

    print(f"Registry written: {REGISTRY_PATH.relative_to(REPO)}")
    print(
        f"  preserved {stats['existing']} existing "
        f"(value-refreshed {stats['value_fixed']}), added {stats['added']} new"
    )
    print(f"  repaired {stats['script_paths_repaired']} stale scripts/ citation(s)")
    print(f"Citations rendered: {CITATIONS_MD.relative_to(REPO)}")

    if "--check" in argv:
        print("\n--- validate_parameters.py ---")
        from validate_parameters import main as validate

        return validate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
