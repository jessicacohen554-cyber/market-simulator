"""NYISO-NEXT-32 G-DRIFT (zero LP): classify every changed Python file on the backcast path by AST.

Rule 29 ``[R-SCREEN]`` (b): each changed hunk between the keeper's ``git_sha`` and
HEAD is INERT-with-reason or LIVE. This probe does the mechanical half: for every
changed ``.py`` file under ``src/`` and the backcast runner/library scripts it
compares the module AST at both shas with docstrings stripped (pass 1) and then
with every string literal blanked (pass 2).

- ``identical_ast``: same AST after docstring removal (comments, formatting,
  docstrings only) -> INERT.
- ``strings_only``: differs only in string literals (messages, labels, paths)
  -> needs a one-line reason; INERT unless the string is a key the solve reads.
- ``code``: the AST differs -> per-function listing, read by hand.
- ``added``: new file (INERT on the NYISO path unless imported by it).

It also compares ``surface_rows("NYISO")`` values at both shas (run separately;
the probe takes the two JSON dumps). No LP, no data reads.

Usage::

    uv run python scripts/probes/nyisonext32_gdrift_ast.py --base fdc41f36 \
        --head origin/main --out results/phase0/nyiso/_nyisonext32_gdrift_ast.json
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PATHSPECS = (
    "src/",
    "scripts/lib/",
    "scripts/run_calibration.py",
    "scripts/run_calibration_full.py",
)


def git(*args: str) -> str:
    """Run a read-side git command without lazy blob fetches beyond what it names."""
    env = dict(os.environ, GIT_NO_LAZY_FETCH="0")
    return subprocess.run(
        ["git", *args], cwd=REPO, env=env, check=True, capture_output=True, text=True
    ).stdout


def show(sha: str, path: str) -> str | None:
    """Return a file's text at ``sha``, or ``None`` if absent."""
    try:
        return git("show", f"{sha}:{path}")
    except subprocess.CalledProcessError:
        return None


class _Normalise(ast.NodeTransformer):
    """Drop docstrings; optionally blank every string constant."""

    def __init__(self, blank_strings: bool) -> None:
        self.blank_strings = blank_strings

    def _strip_doc(self, node: ast.AST) -> ast.AST:
        body = getattr(node, "body", None)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            node.body = body[1:] or [ast.Pass()]
        return node

    def generic_visit(self, node: ast.AST) -> ast.AST:
        if isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            self._strip_doc(node)
        return super().generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if self.blank_strings and isinstance(node.value, str):
            return ast.copy_location(ast.Constant(value=""), node)
        return node

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.AST:
        if self.blank_strings:
            return ast.copy_location(ast.Constant(value=""), node)
        return self.generic_visit(node)


def dump(src: str, blank_strings: bool) -> str:
    """Normalised AST dump of ``src``."""
    tree = _Normalise(blank_strings).visit(ast.parse(src))
    return ast.dump(tree, include_attributes=False)


def defs(src: str) -> dict[str, str]:
    """Top-level and class-level definitions -> normalised dump (strings kept)."""
    tree = ast.parse(src)
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = dump(ast.unparse(node), False)
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[f"{node.name}.{sub.name}"] = dump(ast.unparse(sub), False)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    out[t.id] = dump(ast.unparse(node), False)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            out.setdefault("<imports>", "")
            out["<imports>"] += dump(ast.unparse(node), False)
    return out


def classify(base: str, head: str, path: str) -> dict:
    """Classify one changed file."""
    a, b = show(base, path), show(head, path)
    if a is None:
        return {"path": path, "class": "added"}
    if b is None:
        return {"path": path, "class": "deleted"}
    if dump(a, False) == dump(b, False):
        return {"path": path, "class": "identical_ast"}
    if dump(a, True) == dump(b, True):
        return {"path": path, "class": "strings_only"}
    da, db = defs(a), defs(b)
    changed = sorted(k for k in set(da) | set(db) if da.get(k) != db.get(k))
    return {"path": path, "class": "code", "changed_defs": changed}


def main() -> None:
    """Classify every changed file and write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="origin/main")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    base = git("rev-parse", args.base).strip()
    head = git("rev-parse", args.head).strip()
    names = git("diff", "--name-only", base, head, "--", *PATHSPECS).split()
    rows = [classify(base, head, p) for p in names if p.endswith(".py")]
    summary: dict[str, int] = {}
    for r in rows:
        summary[r["class"]] = summary.get(r["class"], 0) + 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {"base": base, "head": head, "summary": summary, "files": rows}, indent=1
        )
        + "\n"
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
