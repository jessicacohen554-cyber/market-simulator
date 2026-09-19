"""ercot-268: binary-search the commit that moved the ERCOT keeper's LP inputs.

``_ercot268_drift_bisect.py`` established WHAT moved (``availability`` and
``min_gen``, in all five years, with the plant->class map bit-identical). This
finds WHICH COMMIT, by bisecting :func:`_ercot268_input_at_sha.measure` over the
first-parent commits that touch ``src/`` or ``scripts/`` -- the only commits that
CAN move a fleet rebuild, since ``data/`` is shared by symlink across every arm.

The predicate is the ``availability`` hash (``--field`` selects another). A
rebuild is ~90 s and results are cached, so a 157-commit window costs ~8 probes.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_ercot268_bisect_driver.py \\
        --good 0ebfc2da0 --bad 5926ca52 --year 2023 --meta <control meta>
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ercot268_input_at_sha import measure  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def _candidates(good: str, bad: str) -> list[str]:
    """First-parent commits in ``good..bad`` touching code, oldest first."""
    out = subprocess.run(
        [
            "git",
            "log",
            "--first-parent",
            "--format=%H",
            f"{good}..{bad}",
            "--",
            "src/market_sim",
            "scripts",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    ).stdout.split()
    return list(reversed(out))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--good", required=True, help="sha carrying the ORIGINAL value")
    ap.add_argument("--bad", required=True, help="sha carrying the MOVED value")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--field", default="availability")
    ap.add_argument(
        "--cache", type=Path, default=Path("/tmp/_ercot268_input_cache.json")
    )
    a = ap.parse_args()

    meta_path = str(Path(a.meta).resolve())
    good_v = measure(a.good, a.year, meta_path, a.cache)[a.field]
    bad_v = measure(a.bad, a.year, meta_path, a.cache)[a.field]
    print(f"good {a.good} {a.field}={good_v}\nbad  {a.bad} {a.field}={bad_v}")
    if good_v == bad_v:
        raise SystemExit(
            f"{a.field} does not differ between the endpoints — nothing to bisect"
        )

    cands = _candidates(a.good, a.bad)
    print(f"{len(cands)} code-touching first-parent commits in range", flush=True)

    lo, hi = (
        0,
        len(cands) - 1,
    )  # cands[hi] is known BAD (it is `bad` itself or before it)
    # Invariant: everything strictly below `lo` matches good; cands[hi] matches bad.
    while lo < hi:
        mid = (lo + hi) // 2
        v = measure(cands[mid], a.year, meta_path, a.cache)
        state = (
            "GOOD"
            if v[a.field] == good_v
            else ("BAD" if v[a.field] == bad_v else "OTHER")
        )
        print(
            f"  [{mid:3d}/{len(cands) - 1}] {cands[mid][:10]} {state} "
            f"{a.field}={v[a.field][:16]} sum={v[a.field + '_stats']['sum'] if a.field + '_stats' in v else ''}"
            f"  | {v['subject'][:64]}",
            flush=True,
        )
        if state == "GOOD":
            lo = mid + 1
        else:
            hi = mid
    culprit = measure(cands[hi], a.year, meta_path, a.cache)
    print(
        f"\nFIRST COMMIT WITH THE MOVED VALUE: {culprit['sha']}\n  {culprit['subject']}"
    )
    print(
        subprocess.run(
            ["git", "show", "--stat", "--format=%H%n%an%n%ci%n%n%B", culprit["sha"]],
            cwd=REPO,
            capture_output=True,
            text=True,
        ).stdout[:4000]
    )


if __name__ == "__main__":
    main()
