#!/usr/bin/env python3
"""capx D85 key-provenance census — reproduce, then CLASSIFY, every committed
``run_config.json`` whose recorded ``cache_key`` the current rules cannot
reproduce (owner ruling Q59, capx ledger §0bb.3(a), r#57).

**What it measures.** The same census ``capxd76arm_default_flip_key_census``
runs (hash each committed ``scenario_config`` payload under the LIVE drop
rules and compare to its own recorded ``cache_key``), and then, for every
payload that does NOT reproduce, a ladder of named RECIPES, each one a
documented way a key could legitimately have been produced by an earlier rule
set or a different solve environment:

``lag``
    a field registered in ``_CACHE_KEY_OPTIONAL_FIELDS`` AFTER the bundle
    solved: the solving code hashed it, today's rule drops it. Reproduced by
    UN-dropping that one field.
``pre-ledger-flip``
    a field whose live default flipped BEFORE the 2026-09-01 (b′-1)
    re-baseline (the R-A storage-entry pair, PR #4442, 2026-08-31). The
    pre-(b′-1) rule dropped it at the LIVE default of the day, so a bundle
    that recorded the old value had it dropped then and hashed now.
    Reproduced by dropping every ``_CACHE_KEY_REGISTRATION_TIME_DEFAULTS``
    field the payload carries at its registration-time value.
``split-root``
    the solve ran with ``MARKET_SIM_DATA_ROOT`` relocated away from the
    checkout (the D21 / D26 fc6 sessions: repo worktree
    ``/home/user/msim-vintage``, data root ``/home/user/market-simulator``),
    so ``_normalize_cache_key_paths`` folded the same path strings to
    ``<data_root>`` instead of ``<repo>``. Reproduced by re-folding under the
    recorded roots.
``vintage``
    the payload hashed under the rules AS THEY STOOD at the bundle's own
    ``git.sha`` — ``_CACHE_KEY_OPTIONAL_FIELDS`` / ``_DEFAULTS`` /
    ``_RETIRED_FIELDS``, the dataclass defaults and the ``cache_key`` body,
    all extracted by AST from that commit's ``scenarios.py`` (never imported).
    Needs the blob; a shallow clone must ``git fetch --depth=1 origin <sha>``
    first. Optionally ``+resolved``: the payload with the vintage's
    ``default_scenario_overrides`` applied, for a writer that serialized the
    REQUEST config while the runner hashed the RESOLUTION.

Combinations are tried in a fixed order and the FIRST reproducing recipe is
recorded, so the record is deterministic. A row no recipe reproduces is the
finding, and the script exits 1 on it.

Usage::

    uv run python docs/handoffs/d85/key_provenance_census.py \
        --out docs/handoffs/d85/key-provenance-census.json

Exit 0 iff every non-reproducing row is classified; 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import subprocess
import sys
from dataclasses import fields
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
for _p in (_REPO, _REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.config.solve_surface import SOLVE_EPOCHS, moved_rows  # noqa: E402
from market_sim.config.scenarios import (  # noqa: E402
    _CACHE_KEY_OPTIONAL_FIELDS,
    _CACHE_KEY_REGISTRATION_TIME_DEFAULTS,
    _CACHE_KEY_RETIRED_FIELDS,
    ScenarioConfig,
    _cache_key_path_roots,
    _normalize_cache_key_paths,
    _resolve_declared_default,
    cache_key_drop_defaults,
)

#: Fold roots of the one documented relocated-data-root solve environment
#: (FINDING-capx-d21-fc6-battery-2026-08-31.md finding 6; FINDING-capx-d26-p1
#: §3). Listed as (sentinel, prefix) exactly as ``_cache_key_path_roots``
#: returns them: DATA_ROOT first, then REPO_ROOT.
SPLIT_ROOTS: tuple[tuple[str, str], ...] = (
    ("<data_root>", "/home/user/market-simulator"),
    ("<repo>", "/home/user/msim-vintage"),
)


def _jsonable(value):
    """Round-trip through JSON so tuples/lists and Paths/strings compare equal."""
    return json.loads(json.dumps(value, default=str))


def _hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# HEAD rules
# --------------------------------------------------------------------------- #
def head_key(
    payload: dict, *, undrop=(), extra_drop=(), roots=None, surface=False
) -> str:
    """Hash under the live rules (the D76-ARM construction), with recipe knobs.

    ``undrop`` names registered fields to keep in the hash even at their drop
    value (the ``lag`` recipe); ``extra_drop`` names fields to remove
    unconditionally (the ``pre-ledger-flip`` recipe); ``roots`` replaces the
    checkout's fold roots (the ``split-root`` recipe).

    ``surface=False`` (the default, and the D76-ARM construction) hashes the
    solve surface AT ITS DECLARATION — the ``__solve_surface__`` block is
    omitted, which is what ``ScenarioConfig.cache_key`` does while every row
    sits at its frozen declaration. ``surface=True`` appends the LIVE
    ``moved_rows(iso)`` block exactly as ``cache_key`` does today, so the two
    keys differ iff the ISO's surface has moved off its declaration since the
    bundle solved (capx D79's designed re-key). ``__solve_epochs__`` is not
    modelled: ``SOLVE_EPOCHS`` is empty at HEAD, asserted below.
    """
    drop_at = {n: _jsonable(v) for n, v in cache_key_drop_defaults().items()}
    out = dict(payload)
    for name in _CACHE_KEY_OPTIONAL_FIELDS:
        if name in undrop:
            continue
        if name in drop_at and name in out and out[name] == drop_at[name]:
            out.pop(name)
    for name in extra_drop:
        out.pop(name, None)
    for name, retired_default in _CACHE_KEY_RETIRED_FIELDS.items():
        out.setdefault(name, _jsonable(retired_default))
    if surface:
        moved = moved_rows(str(payload.get("iso") or "").upper() or None)
        if moved:
            out["__solve_surface__"] = moved
    out = _normalize_cache_key_paths(
        out, roots if roots is not None else _cache_key_path_roots()
    )
    return _hash(out)


def pre_ledger_flip_fields(payload: dict) -> tuple[str, ...]:
    """Fields the pre-(b′-1) rule would have dropped for this payload.

    A field in ``_CACHE_KEY_REGISTRATION_TIME_DEFAULTS`` whose payload value
    equals its registration-time default (the live default before its flip)
    but not its frozen declaration (the value it drops at today).
    """
    drop_at = {n: _jsonable(v) for n, v in cache_key_drop_defaults().items()}
    out = []
    for name, src in _CACHE_KEY_REGISTRATION_TIME_DEFAULTS.items():
        try:
            original = _jsonable(_resolve_declared_default(src))
        except ValueError:
            continue
        if (
            name in payload
            and payload[name] == original
            and drop_at.get(name) != original
        ):
            out.append(name)
    return tuple(out)


# --------------------------------------------------------------------------- #
# Vintage rules (AST-extracted from the bundle's own commit)
# --------------------------------------------------------------------------- #
def _lit(node):
    """Evaluate a default node: a literal, or ``field(default_factory=lambda: lit)``."""
    try:
        return ast.literal_eval(node)
    except Exception:
        pass
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "field":
        for kw in node.keywords:
            if kw.arg == "default_factory" and isinstance(kw.value, ast.Lambda):
                try:
                    return ast.literal_eval(kw.value.body)
                except Exception:
                    return ("<unevaluable>", ast.unparse(kw.value.body))
    return ("<unevaluable>", ast.unparse(node))


class VintageRules:
    """The cache-key rules of one ``scenarios.py`` blob, by AST, never imported."""

    def __init__(self, scenarios_src: str, iso_configs_src: str | None = None):
        tree = ast.parse(scenarios_src)
        self.optional: tuple[str, ...] = ()
        self.declared: dict | None = None
        self.retired: dict = {}
        self.defaults: dict = {}
        self.folds_paths = "_normalize_cache_key_paths(payload_dict" in scenarios_src
        self.drops_at_declared = "drop_at = cache_key_drop_defaults()" in scenarios_src
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                tgt = node.targets[0] if isinstance(node, ast.Assign) else node.target
                name, val = getattr(tgt, "id", None), node.value
                if val is None:
                    continue
                if name == "_CACHE_KEY_OPTIONAL_FIELDS":
                    self.optional = tuple(ast.literal_eval(val))
                elif name == "_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS":
                    self.declared = {
                        k: _lit(ast.parse(v, mode="eval").body)
                        for k, v in ast.literal_eval(val).items()
                    }
                elif name == "_CACHE_KEY_RETIRED_FIELDS":
                    self.retired = ast.literal_eval(val)
            elif isinstance(node, ast.ClassDef) and node.name == "ScenarioConfig":
                for st in node.body:
                    if isinstance(st, ast.AnnAssign) and st.value is not None:
                        self.defaults[st.target.id] = _lit(st.value)
        self.iso_overrides: dict[str, dict] = {}
        if iso_configs_src:
            itree = ast.parse(iso_configs_src)
            for node in itree.body:
                if isinstance(node, ast.FunctionDef) and node.name.endswith("_config"):
                    iso = node.name.strip("_").removesuffix("_config").upper()
                    for n in ast.walk(node):
                        if (
                            isinstance(n, ast.keyword)
                            and n.arg == "default_scenario_overrides"
                        ):
                            try:
                                self.iso_overrides[iso] = ast.literal_eval(n.value)
                            except Exception:
                                self.iso_overrides[iso] = {}

    def drop_values(self) -> dict:
        out = {}
        for n in self.optional:
            if self.drops_at_declared and self.declared and n in self.declared:
                out[n] = self.declared[n]
            elif n in self.defaults:
                out[n] = self.defaults[n]
        return {k: _jsonable(v) for k, v in out.items()}

    def key(self, payload: dict, *, roots=None) -> str:
        drop = self.drop_values()
        out = dict(payload)
        for n in self.optional:
            if n in drop and n in out and out[n] == drop[n]:
                out.pop(n)
        for n, d in self.retired.items():
            out.setdefault(n, _jsonable(d))
        if self.folds_paths:
            out = _normalize_cache_key_paths(
                out, roots if roots is not None else _cache_key_path_roots()
            )
        return _hash(out)

    def resolved(self, payload: dict, iso: str) -> dict:
        """Apply this vintage's ISO ``default_scenario_overrides`` the way
        ``run_scenario_iso`` did — only where the payload sits at the dataclass default."""
        out = dict(payload)
        for k, v in self.iso_overrides.get(iso.upper(), {}).items():
            if k in out and out[k] == _jsonable(self.defaults.get(k)):
                out[k] = _jsonable(v)
        return out

    def describe(self) -> dict:
        return {
            "n_optional": len(self.optional),
            "has_declared_ledger": self.declared is not None,
            "drops_at_declared": self.drops_at_declared,
            "n_retired": len(self.retired),
            "folds_paths": self.folds_paths,
            "n_dataclass_fields": len(self.defaults),
        }


def _git_blob(sha: str, rel: str) -> str | None:
    try:
        full = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return subprocess.run(
            ["git", "show", f"{full}:{rel}"],
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None


def load_vintage(sha: str) -> VintageRules | None:
    src = _git_blob(sha, "src/market_sim/config/scenarios.py")
    if src is None:
        return None
    return VintageRules(src, _git_blob(sha, "src/market_sim/config/iso_configs.py"))


# --------------------------------------------------------------------------- #
# Classification ladder
# --------------------------------------------------------------------------- #
def classify(
    payload: dict, want: str, iso: str, sha: str | None, vintages: dict
) -> dict:
    """Return the FIRST recipe that reproduces ``want``, or ``unclassified``."""
    drop_at = {n: _jsonable(v) for n, v in cache_key_drop_defaults().items()}
    lag_cands = [
        n
        for n in _CACHE_KEY_OPTIONAL_FIELDS
        if n in payload and payload[n] == drop_at.get(n)
    ]
    flip = pre_ledger_flip_fields(payload)

    # A payload may carry SEVERAL pre-ledger-flip fields at their old value,
    # and only the ones whose flip POSTDATES the solve were dropped by the
    # solving code (the others were already hashed then). The solve date is
    # not knowable from HEAD alone, so subsets are tried smallest-first and
    # the first reproducing subset names the fields that flipped after it.
    flip_subsets = [
        s for n in range(1, len(flip) + 1) for s in itertools.combinations(flip, n)
    ]

    ladder: list[tuple[str, dict, callable]] = []
    for c in lag_cands:
        ladder.append(
            ("lag", {"undrop": [c]}, lambda c=c: head_key(payload, undrop=(c,)))
        )
    for s in flip_subsets:
        ladder.append(
            (
                "pre-ledger-flip",
                {"drop": list(s)},
                lambda s=s: head_key(payload, extra_drop=s),
            )
        )
    for s in flip_subsets:
        ladder.append(
            (
                "pre-ledger-flip+split-root",
                {"drop": list(s), "roots": SPLIT_ROOTS},
                lambda s=s: head_key(payload, extra_drop=s, roots=SPLIT_ROOTS),
            )
        )
    for s in flip_subsets:
        for c in lag_cands:
            ladder.append(
                (
                    "lag+pre-ledger-flip",
                    {"undrop": [c], "drop": list(s)},
                    lambda c=c, s=s: head_key(payload, undrop=(c,), extra_drop=s),
                )
            )
    ladder.append(
        (
            "split-root",
            {"roots": SPLIT_ROOTS},
            lambda: head_key(payload, roots=SPLIT_ROOTS),
        )
    )
    for a, b in itertools.combinations(lag_cands, 2):
        ladder.append(
            (
                "lag×2",
                {"undrop": [a, b]},
                lambda a=a, b=b: head_key(payload, undrop=(a, b)),
            )
        )

    for name, detail, fn in ladder:
        if fn() == want:
            return {"class": name, "recipe": detail, "reproduced": True}

    # Vintage rules, if the bundle's commit is reachable.
    if sha:
        v = vintages.get(sha)
        if v is None and sha not in vintages:
            v = vintages[sha] = load_vintage(sha)
        if v is not None:
            trials = [
                ("vintage", {"sha": sha}, lambda: v.key(payload)),
                (
                    "vintage+split-root",
                    {"sha": sha, "roots": SPLIT_ROOTS},
                    lambda: v.key(payload, roots=SPLIT_ROOTS),
                ),
                (
                    "vintage+resolved",
                    {"sha": sha, "iso_overrides": v.iso_overrides.get(iso.upper(), {})},
                    lambda: v.key(v.resolved(payload, iso)),
                ),
            ]
            for name, detail, fn in trials:
                if fn() == want:
                    return {
                        "class": name,
                        "recipe": detail,
                        "reproduced": True,
                        "vintage_rules": v.describe(),
                    }
            return {
                "class": "unclassified",
                "reproduced": False,
                "vintage_rules": v.describe(),
                "vintage_key": v.key(payload),
            }
        return {
            "class": "unclassified",
            "reproduced": False,
            "vintage": "commit not reachable",
        }
    return {"class": "unclassified", "reproduced": False}


def _committed_run_configs() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*run_config.json"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [_REPO / rel for rel in sorted(out)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write the JSON record here")
    args = ap.parse_args(argv)

    live_fields = {f.name for f in fields(ScenarioConfig)}
    rows, mismatches = [], []
    vintages: dict = {}
    for path in _committed_run_configs():
        record = json.loads(path.read_text())
        payload = record.get("scenario_config")
        if not isinstance(payload, dict):
            continue
        payload = _jsonable(payload)
        recorded = record.get("cache_key")
        key = head_key(payload)
        key_live = head_key(payload, surface=True)
        reproduces = (
            (recorded == key) if isinstance(recorded, str) and recorded else None
        )
        git = record.get("git") or {}
        sha = (git.get("sha") if isinstance(git, dict) and git else None) or record.get(
            "git_sha"
        )
        row = {
            "run_config": str(path.relative_to(_REPO)),
            "iso": payload.get("iso"),
            "mode": payload.get("mode"),
            "hindcast": bool(payload.get("hindcast", False)),
            "solved_at": record.get("timestamp"),
            "git_sha": sha,
            "git_dirty": git.get("dirty") if isinstance(git, dict) else None,
            "recorded_cache_key": recorded,
            "key_head_rules": key,
            "key_live_rules_with_surface": key_live,
            "reproduces_recorded_key": reproduces,
            # True iff the recorded key is reproducible ONLY with the surface at
            # its declaration, i.e. the ISO's surface has since moved (class c).
            "reproduces_at_declaration_only": bool(reproduces) and key_live != key,
            "fields_missing_unregistered": sorted(
                n
                for n in live_fields - set(payload)
                if n not in _CACHE_KEY_OPTIONAL_FIELDS
            ),
            "retired_fields_carried": sorted(
                n for n in _CACHE_KEY_RETIRED_FIELDS if n in payload
            ),
        }
        if reproduces is False:
            row["classification"] = classify(
                payload, recorded, str(payload.get("iso") or ""), sha, vintages
            )
            # Independent cross-check, recorded whenever the solve commit is
            # reachable: the key under the bundle's OWN vintage rules. A
            # HEAD-recipe class that also reproduces here is doubly derived;
            # a vintage miss with a HEAD-recipe hit (the dirty-tree fc6 arms,
            # whose recorded ``git.sha`` understates the tree) is stated.
            if sha and sha not in vintages:
                vintages[sha] = load_vintage(sha)
            v = vintages.get(sha) if sha else None
            if v is not None:
                vk = v.key(payload)
                row["vintage_check"] = {
                    "sha": sha,
                    "key_vintage_rules": vk,
                    "reproduces": vk == recorded,
                    "rules": v.describe(),
                }
            else:
                row["vintage_check"] = {
                    "sha": sha,
                    "reproduces": None,
                    "reason": "commit not reachable",
                }
            mismatches.append(row)
        rows.append(row)

    by_class: dict[str, int] = {}
    for m in mismatches:
        by_class[m["classification"]["class"]] = (
            by_class.get(m["classification"]["class"], 0) + 1
        )
    unclassified = [m for m in mismatches if not m["classification"]["reproduced"]]
    assert not SOLVE_EPOCHS, (
        "SOLVE_EPOCHS is non-empty: model __solve_epochs__ before trusting key_live"
    )
    surface_moved = {
        iso: moved_rows(iso)
        for iso in sorted({str(r["iso"]).upper() for r in rows if r["iso"]})
        if moved_rows(iso)
    }
    at_declaration_only: dict[str, int] = {}
    for r in rows:
        if r["reproduces_at_declaration_only"]:
            at_declaration_only[r["iso"]] = at_declaration_only.get(r["iso"], 0) + 1
    record_out = {
        "probe": "capxd85_key_provenance_census",
        "ruling": "Q59 (capx ledger §0bb.3(a), r#57) — D85 key-provenance audit",
        "head": subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "configs_checked": len(rows),
        "instrument_validated": sum(
            1 for r in rows if r["reproduces_recorded_key"] is True
        ),
        "instrument_unvalidatable_no_recorded_key": sum(
            1 for r in rows if r["reproduces_recorded_key"] is None
        ),
        "instrument_mismatch": len(mismatches),
        "mismatch_by_class": dict(sorted(by_class.items())),
        "unclassified": len(unclassified),
        # Class (c): the surface rows currently off their declaration, and the
        # validated keys that reproduce only with the surface AT declaration.
        "surface_moved_rows_by_iso": surface_moved,
        "reproduces_at_declaration_only_by_iso": at_declaration_only,
        "split_roots_recipe": SPLIT_ROOTS,
        "mismatch_detail": mismatches,
        "rows": rows,
    }
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(record_out, indent=2) + "\n")

    print(
        f"{len(rows)} committed run configs at {record_out['head']}: "
        f"{record_out['instrument_validated']} reproduce, "
        f"{record_out['instrument_unvalidatable_no_recorded_key']} have no key, "
        f"{len(mismatches)} MISMATCH"
    )
    for m in mismatches:
        c = m["classification"]
        print(
            f"  {c['class']:28s} {m['recorded_cache_key']}  {m['run_config']}  {c.get('recipe', '')}"
        )
    print(f"  by class: {record_out['mismatch_by_class']}")
    print(f"  surface rows off declaration: {surface_moved}")
    print(
        f"  validated keys reproducible only at declaration (class c): {at_declaration_only}"
    )
    if unclassified:
        print(f"FAIL: {len(unclassified)} recorded key(s) reproduce under NO recipe")
        return 1
    print("ok: every mismatch classified")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
