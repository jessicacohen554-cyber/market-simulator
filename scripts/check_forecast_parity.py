#!/usr/bin/env python3
"""Standing backcast→forecast parity check (FR-22 / FFR-1E). **No LP anywhere.**

**The failure this prevents.** A mechanism armed in an ISO's *keeper posture*
that exists only on the backcast code path. ``docs/FINDING-nyiso102-d5-parity-
wiring-2026-07-30.md`` is the incident: three NYISO downstate mechanisms were
called only from ``scripts/run_calibration.py``; ``src/market_sim/runner.py``
(the forecast orchestrator) never referenced them, so a forecast carrying the
keeper's config silently dropped them. That was found by accident. Keeper
mechanisms land weekly, so without a standing check every promotion is another
chance to fork the two paths.

**What it does.** For each ISO's CURRENT keeper (``frontend/data/backcast/
keepers/<ISO>.json`` → registry sidecar → bundle ``run_config.json``):

1. enumerate the **armed** solve-affecting mechanisms — every ``ScenarioConfig``
   field whose keeper value differs from the dataclass default;
2. resolve each to **(a)** a forecast-orchestrator consumer found in the SOURCE,
   or **(b)** an explicit row in ``scripts/lib/forecast_parity_registry.py``;
3. **fail loud** on anything in neither set.

**Evidence tiers for (a)** — strongest first, all AST-derived, never asserted:

``orchestrator``
    read in ``src/market_sim/runner.py`` itself (what the nyiso-102 fix produced).
``shared``
    attribute / ``getattr`` read in a shared ``src/market_sim/**`` builder both
    orchestrators thread their config into.
``string_key``
    the field name appears as a string constant in a shared builder — the
    ``config_field="pjm_zonal_gas_basis"`` channel, where the applier reads the
    field by name passed from its caller. Docstrings and the bookkeeping
    modules (``persist``/``flags``/``scenarios``) are excluded, so a recorded
    name is not mistaken for a consumer.
``dynamic``
    matches a curated :data:`~scripts.lib.forecast_parity_registry.DYNAMIC_CONSUMERS`
    pattern — the ``getattr(config, f"coal_{stem}_{p}")`` family, invisible to a
    name scan.

Reads in a ``backcast``-role source (both calibration entry points **and**
``pipeline/backcast_config.py``) are never forecast evidence, and reads inside
:data:`~scripts.lib.forecast_parity_registry.ARCHIVED_FUNCTIONS` (the archived
P2 pass) are discarded — that is exactly where the nyiso-102 mechanism was
mentioned while being unwired, so counting it would have made this check green
on the very incident that motivated it.

**Known limitation, stated rather than hidden.** ``shared``/``string_key``
evidence proves the field is read by a shared builder, not that the specific
call is on a live forecast call chain. Function-granularity call-graph
reachability is the hardening lever; the archived-P2 exclusion is the one case
where a shared read is known not to be live, and it is excluded explicitly.

Stdlib only (``ast`` + ``json``): no package import, no ``uv sync``, no solve.

Usage::

    python3 scripts/check_forecast_parity.py                 # sweep six keepers
    python3 scripts/check_forecast_parity.py --iso NYISO     # one ISO
    python3 scripts/check_forecast_parity.py --json          # machine-readable
    python3 scripts/check_forecast_parity.py --markdown out.md
    python3 scripts/check_forecast_parity.py \\
        --keeper-config TEST=/tmp/synthetic_run_config.json  # tests / probes

Exit codes: ``0`` every armed mechanism accounted for (filed GAPs included);
``1`` an unaccounted mechanism, a stale/invalid registry row, or an unreadable
keeper bundle. ``--strict-gaps`` additionally fails on filed GAP rows.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))

from scripts.lib import forecast_parity_registry as reg  # noqa: E402
from scripts.lib import keeper_store  # noqa: E402

_CONFIG_REL = "src/market_sim/config/scenarios.py"
_CLASS = "ScenarioConfig"


# ---------------------------------------------------------------------------
# ScenarioConfig defaults (parsed, never imported)
# ---------------------------------------------------------------------------


class _Unresolved:
    """Sentinel for a default this parser cannot evaluate (path expressions)."""

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return "<unresolved>"


UNRESOLVED = _Unresolved()


def scenario_defaults(source: str) -> dict[str, object]:
    """Return ``{field: default}`` for ``ScenarioConfig``, parsed with ``ast``.

    ``field(default_factory=...)`` resolves through the factory (``dict``/
    ``list``/``set`` builtins and ``lambda: <literal>``). A default this cannot
    evaluate — the ``str(SOME_PATH)`` artifact-path family — maps to
    :data:`UNRESOLVED`, which the sweep treats as "cannot be compared", so those
    fields must carry a registry row rather than silently passing.
    """
    tree = ast.parse(source)
    cls = next(
        (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == _CLASS),
        None,
    )
    if cls is None:
        raise SystemExit(f"{_CONFIG_REL}: class {_CLASS} not found")
    out: dict[str, object] = {}
    for node in cls.body:
        if not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)):
            continue
        out[node.target.id] = _default_value(node.value)
    return out


def _default_value(node: ast.expr | None) -> object:
    if node is None:
        return UNRESOLVED
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        pass
    if isinstance(node, ast.Call):
        factory = _keyword(node, "default_factory")
        if factory is not None:
            if isinstance(factory, ast.Name) and factory.id in {"dict", "list", "set"}:
                return {"dict": {}, "list": [], "set": set()}[factory.id]
            if isinstance(factory, ast.Lambda):
                try:
                    return ast.literal_eval(factory.body)
                except (ValueError, SyntaxError):
                    return UNRESOLVED
        default = _keyword(node, "default")
        if default is not None:
            try:
                return ast.literal_eval(default)
            except (ValueError, SyntaxError):
                return UNRESOLVED
    return UNRESOLVED


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _equal(recorded: object, default: object) -> bool:
    """Compare a JSON-round-tripped run_config value against a parsed default."""
    if default is UNRESOLVED:
        return False
    if isinstance(default, tuple):
        default = list(default)
    if isinstance(default, set):
        default = sorted(default)
        recorded = sorted(recorded) if isinstance(recorded, list) else recorded
    if isinstance(recorded, (int, float)) and isinstance(default, (int, float)):
        if isinstance(recorded, bool) != isinstance(default, bool):
            return False
        return float(recorded) == float(default)
    return recorded == default


# ---------------------------------------------------------------------------
# Source scan
# ---------------------------------------------------------------------------


@dataclass
class ReadSite:
    """One place a config field is read (or named as a lookup key)."""

    rel: str
    func: str
    lineno: int
    kind: str  # "attr" | "string"


class _Scanner(ast.NodeVisitor):
    """Collect config-field read sites in one module."""

    def __init__(self, rel: str, fields: frozenset[str]) -> None:
        self.rel = rel
        self.fields = fields
        self.sites: list[tuple[str, ReadSite]] = []
        self._stack: list[str] = []
        self._docstrings: set[int] = set()
        self._getattr_keys: set[int] = set()

    def _mark_doc(self, node: ast.AST) -> None:
        body = getattr(node, "body", None)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            self._docstrings.add(id(body[0].value))

    def visit_Module(self, node: ast.Module) -> None:
        self._mark_doc(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._mark_doc(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._mark_doc(node)
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def _record(self, name: str, lineno: int, kind: str) -> None:
        func = self._stack[0] if self._stack else "<module>"
        self.sites.append((name, ReadSite(self.rel, func, lineno, kind)))

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # ``self.<field>`` is the dataclass defining/validating itself, not a
        # consumer, so it never counts as evidence.
        is_self = isinstance(node.value, ast.Name) and node.value.id == "self"
        if isinstance(node.ctx, ast.Load) and node.attr in self.fields and not is_self:
            self._record(node.attr, node.lineno, "attr")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id == "getattr" and len(node.args) >= 2:
            key = node.args[1]
            if isinstance(key, ast.Constant) and key.value in self.fields:
                self._record(key.value, node.lineno, "attr")
                # The key literal is the attribute name, not a separate
                # string-keyed lookup — record the read once.
                self._getattr_keys.add(id(key))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if (
            isinstance(node.value, str)
            and node.value in self.fields
            and id(node) not in self._docstrings
            and id(node) not in self._getattr_keys
        ):
            self._record(node.value, node.lineno, "string")
        self.generic_visit(node)


def scan_sources(
    repo: Path, fields: frozenset[str], paths: list[Path] | None = None
) -> dict[str, list[ReadSite]]:
    """Return ``{field: [ReadSite, ...]}`` over the engine + both orchestrators.

    ``paths`` overrides the scanned file set (tests scan a synthetic tree).
    """
    if paths is None:
        paths = sorted((repo / "src" / "market_sim").rglob("*.py"))
        for rel, role in reg.SOURCE_ROLES.items():
            if role == "backcast":
                extra = repo / rel
                if extra.exists() and extra not in paths:
                    paths.append(extra)
    out: dict[str, list[ReadSite]] = {}
    for path in paths:
        rel = path.relative_to(repo).as_posix()
        if reg.SOURCE_ROLES.get(rel) == "bookkeeping":
            continue
        try:
            tree = ast.parse(path.read_text())
        except (OSError, SyntaxError):
            continue
        scanner = _Scanner(rel, fields)
        scanner.visit(tree)
        for name, site in scanner.sites:
            if (site.rel, site.func) in reg.ARCHIVED_FUNCTIONS:
                continue
            out.setdefault(name, []).append(site)
    return out


# ---------------------------------------------------------------------------
# Evidence resolution
# ---------------------------------------------------------------------------


@dataclass
class Evidence:
    """The forecast-side evidence for one field (empty ``tier`` = none found)."""

    tier: str = ""
    where: str = ""

    def __bool__(self) -> bool:
        return bool(self.tier)


def _role(rel: str) -> str:
    if rel in reg.SOURCE_ROLES:
        return reg.SOURCE_ROLES[rel]
    return "shared" if rel.startswith("src/market_sim/") else "other"


def forecast_evidence(field: str, sites: dict[str, list[ReadSite]]) -> Evidence:
    """Return the strongest forecast-side evidence for ``field``."""
    mine = sites.get(field, [])
    for site in mine:
        if site.rel == reg.FORECAST_ORCHESTRATOR:
            return Evidence("orchestrator", f"{site.rel}:{site.lineno}")
    for kind, tier in (("attr", "shared"), ("string", "string_key")):
        for site in mine:
            if site.kind == kind and _role(site.rel) == "shared":
                return Evidence(tier, f"{site.rel}:{site.lineno}")
    for dyn in reg.DYNAMIC_CONSUMERS:
        if re.fullmatch(dyn.pattern, field):
            return Evidence("dynamic", f"{dyn.module} {dyn.symbol}")
    return Evidence()


def _annotated_backcast_only(field: str, sites: dict[str, list[ReadSite]]) -> bool:
    """Whether a backcast read site carries the in-code overlay annotation.

    The convention is a comment block above the call site::

        # [measured: <source> | forecast substitute: <forward channel>]

    Reported (not required) so a BACKCAST_ONLY row backed by the codebase's own
    declaration is visibly distinguishable from one backed only by this
    registry's prose.
    """
    for site in sites.get(field, []):
        if _role(site.rel) != "backcast":
            continue
        try:
            lines = (_REPO / site.rel).read_text().splitlines()
        except OSError:
            continue
        window = lines[max(0, site.lineno - 20) : site.lineno]
        if any("forecast substitute" in ln for ln in window):
            return True
    return False


# ---------------------------------------------------------------------------
# Registry integrity
# ---------------------------------------------------------------------------


def check_registry(
    repo: Path, defaults: dict[str, object], sites: dict[str, list[ReadSite]]
) -> list[str]:
    """Return the registry's integrity failures (empty = healthy).

    A registry that can rot silently is worse than no registry, so every row is
    verified against the tree: real fields, no duplicate coverage, citations
    that exist and name the field, parents/alias gates that resolve, filed
    findings that exist — and, for ``BACKCAST_ONLY``, that the field is still
    NOT forecast-wired (a row left behind after wiring is a stale exemption).
    """
    failures: list[str] = []
    seen: dict[str, int] = {}
    for idx, row in enumerate(reg.DECLARATIONS):
        for name in row.fields:
            if name not in defaults:
                failures.append(
                    f"registry row {idx} declares {name!r}, which is not a "
                    f"{_CLASS} field (renamed or deleted — fix or drop the row)"
                )
            if name in seen:
                failures.append(
                    f"{name!r} declared twice (rows {seen[name]} and {idx}) — "
                    "one field, one row"
                )
            seen[name] = idx
        for cite in row.evidence:
            if not (repo / cite).exists():
                failures.append(f"{row.fields[0]}: evidence path {cite} does not exist")
        if row.evidence and not any(
            _names_field(repo / cite, row.fields) for cite in row.evidence
        ):
            failures.append(
                f"{row.fields[0]}: no evidence path names any of {row.fields} — "
                "citation does not back the claim"
            )
        if row.disposition == reg.BACKCAST_ONLY:
            for name in row.fields:
                ev = forecast_evidence(name, sites)
                if ev:
                    failures.append(
                        f"{name}: declared BACKCAST_ONLY but IS forecast-wired "
                        f"({ev.tier} @ {ev.where}) — stale declaration, drop the row"
                    )
        if row.disposition == reg.PARAMETER_OF:
            if row.parent not in defaults:
                failures.append(
                    f"{row.fields[0]}: parent {row.parent!r} is not a {_CLASS} field"
                )
        if row.disposition == reg.FORECAST_ALIAS:
            if row.alias_gate not in defaults:
                failures.append(
                    f"{row.fields[0]}: alias_gate {row.alias_gate!r} is not a "
                    f"{_CLASS} field"
                )
            elif not forecast_evidence(row.alias_gate, sites):
                failures.append(
                    f"{row.fields[0]}: alias_gate {row.alias_gate!r} has no "
                    "forecast-side consumer either — the alias does not hold"
                )
        if row.disposition == reg.GAP:
            if not row.finding or not (repo / row.finding).exists():
                failures.append(
                    f"{row.fields[0]}: GAP row must cite an existing findings "
                    f"doc (got {row.finding!r})"
                )
    for dyn in reg.DYNAMIC_CONSUMERS:
        path = repo / dyn.module
        if not path.exists():
            failures.append(f"dynamic consumer module {dyn.module} does not exist")
            continue
        stem = dyn.symbol.strip('f"').strip("'")[:12]
        if stem and stem not in path.read_text():
            failures.append(
                f"dynamic consumer {dyn.symbol} not found in {dyn.module} — "
                "the computed-name site moved or was renamed"
            )
    return failures


def _names_field(path: Path, fields: tuple[str, ...]) -> bool:
    try:
        text = path.read_text()
    except OSError:
        return False
    return any(name in text for name in fields)


# ---------------------------------------------------------------------------
# Keeper sweep
# ---------------------------------------------------------------------------


@dataclass
class FieldVerdict:
    """One armed field's parity verdict in one keeper."""

    field: str
    status: str  # FORECAST_WIRED | BACKCAST_ONLY | ... | UNACCOUNTED
    detail: str
    value: object = None


@dataclass
class IsoReport:
    """One ISO's parity sweep."""

    iso: str
    run_id: str
    bundle: str
    verdicts: list[FieldVerdict] = dc_field(default_factory=list)
    errors: list[str] = dc_field(default_factory=list)

    def by_status(self, status: str) -> list[FieldVerdict]:
        return [v for v in self.verdicts if v.status == status]


def armed_fields(run_config: dict, defaults: dict[str, object]) -> dict[str, object]:
    """Return ``{field: value}`` for every armed (non-default) config field."""
    sc = run_config.get("scenario_config", run_config)
    out: dict[str, object] = {}
    for name, value in sc.items():
        if name not in defaults:
            continue
        if not _equal(value, defaults[name]):
            out[name] = value
    return out


def sweep_config(
    iso: str,
    run_id: str,
    bundle: str,
    run_config: dict,
    defaults: dict[str, object],
    sites: dict[str, list[ReadSite]],
) -> IsoReport:
    """Resolve every armed mechanism in one run_config to (a), (b) or a failure."""
    report = IsoReport(iso=iso, run_id=run_id, bundle=bundle)
    armed = armed_fields(run_config, defaults)
    for name in sorted(armed):
        report.verdicts.append(_resolve(name, armed, sites))
    return report


def _resolve(
    name: str, armed: dict[str, object], sites: dict[str, list[ReadSite]]
) -> FieldVerdict:
    value = armed[name]
    ev = forecast_evidence(name, sites)
    if ev:
        return FieldVerdict(name, "FORECAST_WIRED", f"{ev.tier} @ {ev.where}", value)
    row = reg.declaration_for(name)
    if row is None:
        return FieldVerdict(
            name,
            "UNACCOUNTED",
            "no forecast-orchestrator consumer and no registry declaration",
            value,
        )
    if row.disposition == reg.PARAMETER_OF:
        if row.parent not in armed:
            return FieldVerdict(
                name, "INERT", f"parameter of {row.parent}, which is not armed", value
            )
        parent = _resolve(row.parent, armed, sites)
        return FieldVerdict(
            name,
            parent.status,
            f"parameter of {row.parent} → {parent.status} ({parent.detail})",
            value,
        )
    if row.disposition == reg.FORECAST_ALIAS:
        gate = forecast_evidence(row.alias_gate or "", sites)
        return FieldVerdict(
            name,
            "FORECAST_ALIAS",
            f"forecast path gates on {row.alias_gate} ({gate.tier} @ {gate.where})",
            value,
        )
    if row.disposition == reg.BACKCAST_ONLY:
        annotated = _annotated_backcast_only(name, sites)
        mark = (
            "in-code [measured|forecast substitute] annotation"
            if annotated
            else ("registry declaration only")
        )
        return FieldVerdict(name, "BACKCAST_ONLY", f"{row.why} [{mark}]", value)
    if row.disposition == reg.GAP:
        return FieldVerdict(name, "GAP", f"{row.why} (filed: {row.finding})", value)
    return FieldVerdict(name, row.disposition, row.why, value)


def keeper_configs(
    repo: Path, isos: list[str] | None
) -> list[tuple[str, str, str, dict]]:
    """Return ``(iso, run_id, bundle, run_config)`` for each current keeper."""
    out: list[tuple[str, str, str, dict]] = []
    for run_id in keeper_store.keeper_list(repo):
        side_path = repo / "frontend/data/backcast/registry" / f"{run_id}.json"
        if not side_path.exists():
            out.append(("?", run_id, "", {"__error__": f"missing sidecar {side_path}"}))
            continue
        side = json.loads(side_path.read_text())
        iso = side.get("iso", "?")
        if isos and iso not in isos:
            continue
        bundle = side.get("bundle", "")
        rc_path = repo / bundle / "run_config.json"
        if not rc_path.exists():
            out.append((iso, run_id, bundle, {"__error__": f"missing {rc_path}"}))
            continue
        out.append((iso, run_id, bundle, json.loads(rc_path.read_text())))
    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_STATUS_ORDER = (
    "UNACCOUNTED",
    "GAP",
    "BACKCAST_ONLY",
    "FORECAST_ALIAS",
    "SCENARIO_INPUT",
    "INERT",
    "FORECAST_WIRED",
)


def render_markdown(reports: list[IsoReport], registry_failures: list[str]) -> str:
    """Render the six-ISO parity report as markdown."""
    lines = ["# Backcast→forecast parity report", ""]
    lines.append(
        "| ISO | keeper | armed | wired | backcast-only | gaps | unaccounted |"
    )
    lines.append("|---|---|--:|--:|--:|--:|--:|")
    for rep in reports:
        lines.append(
            f"| {rep.iso} | `{rep.run_id}` | {len(rep.verdicts)} | "
            f"{len(rep.by_status('FORECAST_WIRED'))} | "
            f"{len(rep.by_status('BACKCAST_ONLY'))} | "
            f"{len(rep.by_status('GAP'))} | {len(rep.by_status('UNACCOUNTED'))} |"
        )
    lines.append("")
    for rep in reports:
        lines.append(f"## {rep.iso} — `{rep.run_id}`")
        lines.append("")
        for err in rep.errors:
            lines.append(f"* **ERROR** {err}")
        for status in _STATUS_ORDER:
            rows = rep.by_status(status)
            if not rows or status == "FORECAST_WIRED":
                continue
            lines.append(f"**{status}** ({len(rows)})")
            lines.append("")
            for v in rows:
                lines.append(f"* `{v.field}` = `{v.value}` — {v.detail}")
            lines.append("")
        lines.append(
            f"_{len(rep.by_status('FORECAST_WIRED'))} armed mechanisms resolve to a "
            "forecast-side consumer (not listed individually)._"
        )
        lines.append("")
    if registry_failures:
        lines.append("## Registry integrity failures")
        lines.append("")
        lines.extend(f"* {f}" for f in registry_failures)
    return "\n".join(lines) + "\n"


def _print_text(reports: list[IsoReport], registry_failures: list[str]) -> None:
    for rep in reports:
        counts = {s: len(rep.by_status(s)) for s in _STATUS_ORDER}
        print(f"\n=== {rep.iso}  {rep.run_id}  ({len(rep.verdicts)} armed)")
        for err in rep.errors:
            print(f"  ERROR   {err}")
        print(
            "  wired {FORECAST_WIRED}  alias {FORECAST_ALIAS}  "
            "backcast-only {BACKCAST_ONLY}  input {SCENARIO_INPUT}  "
            "inert {INERT}  GAP {GAP}  UNACCOUNTED {UNACCOUNTED}".format(**counts)
        )
        for status in _STATUS_ORDER:
            if status == "FORECAST_WIRED":
                continue
            for v in rep.by_status(status):
                print(f"  {status:<14} {v.field} = {v.value!r}")
                print(f"                 {v.detail}")
    if registry_failures:
        print("\n=== REGISTRY INTEGRITY FAILURES")
        for f in registry_failures:
            print(f"  FAIL  {f}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    repo: Path,
    isos: list[str] | None = None,
    extra_configs: list[tuple[str, Path]] | None = None,
) -> tuple[list[IsoReport], list[str]]:
    """Run the full check. Returns ``(reports, registry_failures)``."""
    defaults = scenario_defaults((repo / _CONFIG_REL).read_text())
    sites = scan_sources(repo, frozenset(defaults))
    registry_failures = check_registry(repo, defaults, sites)
    reports: list[IsoReport] = []
    sources: list[tuple[str, str, str, dict]] = []
    if extra_configs:
        for iso, path in extra_configs:
            sources.append((iso, path.name, str(path), json.loads(path.read_text())))
    else:
        sources = keeper_configs(repo, isos)
    for iso, run_id, bundle, rc in sources:
        if "__error__" in rc:
            rep = IsoReport(iso=iso, run_id=run_id, bundle=bundle)
            rep.errors.append(str(rc["__error__"]))
            reports.append(rep)
            continue
        reports.append(sweep_config(iso, run_id, bundle, rc, defaults, sites))
    return reports, registry_failures


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (see the module docstring for usage and exit codes)."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", type=Path, default=_REPO, help="repo root")
    ap.add_argument("--iso", action="append", help="restrict to these ISOs")
    ap.add_argument(
        "--keeper-config",
        action="append",
        default=[],
        metavar="ISO=PATH",
        help="sweep a run_config.json directly instead of the keeper store "
        "(synthetic postures for tests/probes)",
    )
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--markdown", type=Path, help="write the markdown report here")
    ap.add_argument(
        "--strict-gaps",
        action="store_true",
        help="also fail on filed GAP rows (default: report, do not fail)",
    )
    args = ap.parse_args(argv)

    extra: list[tuple[str, Path]] = []
    for spec in args.keeper_config:
        iso, _, path = spec.partition("=")
        if not path:
            ap.error(f"--keeper-config expects ISO=PATH, got {spec!r}")
        extra.append((iso, Path(path)))

    reports, registry_failures = run(args.repo, args.iso, extra or None)

    unaccounted = [
        (r.iso, v.field) for r in reports for v in r.by_status("UNACCOUNTED")
    ]
    gaps = [(r.iso, v.field) for r in reports for v in r.by_status("GAP")]
    errors = [(r.iso, e) for r in reports for e in r.errors]

    if args.json:
        print(
            json.dumps(
                {
                    "reports": [
                        {
                            "iso": r.iso,
                            "run_id": r.run_id,
                            "bundle": r.bundle,
                            "errors": r.errors,
                            "verdicts": [
                                {
                                    "field": v.field,
                                    "status": v.status,
                                    "detail": v.detail,
                                    "value": v.value,
                                }
                                for v in r.verdicts
                            ],
                        }
                        for r in reports
                    ],
                    "registry_failures": registry_failures,
                    "unaccounted": unaccounted,
                    "gaps": gaps,
                },
                indent=2,
                default=str,
            )
        )
    else:
        _print_text(reports, registry_failures)

    if args.markdown:
        args.markdown.write_text(render_markdown(reports, registry_failures))

    if not args.json:
        print(
            f"\nSUMMARY: {len(reports)} keeper posture(s); "
            f"{len(unaccounted)} unaccounted, {len(gaps)} filed gap(s), "
            f"{len(registry_failures)} registry failure(s), {len(errors)} error(s)"
        )
        for iso, fld in unaccounted:
            print(
                f"  FAIL  {iso}: {fld} is armed in the keeper with no "
                "forecast-orchestrator consumer and no registry declaration "
                "(scripts/lib/forecast_parity_registry.py)"
            )

    bad = bool(unaccounted or registry_failures or errors)
    if args.strict_gaps and gaps:
        bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
