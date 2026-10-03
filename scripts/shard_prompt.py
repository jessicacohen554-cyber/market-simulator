"""Print a complete, self-checking SOLVE-SHARD prompt for one ISO-year.

Every backcast year is solved in its own shard container (CLAUDE.md rule 36
``[R-YEAR-ISOLATION]``) and the parent composes the per-year bundles. The
shard prompt has eight things it must get right or the solve is wasted
(rule 32 (c)): the pinned SHA, the recipe signature, its own out-dir and
branch, the bundle push with ``dispatch/<year>_P1.parquet``, the forbidden
commands, the memory preflight (``prepare_solve_container.py`` FIRST, before any data
step — R-50), what to report, and "stop, don't repair". A PJM recipe that
arms ``pjm_da_virtual_bids`` (or cannot be read) also gets the gitignored
DA-virtuals fetch.
This script emits all eight from four arguments so the orchestrator never
re-derives them by hand.

Usage::

    python scripts/shard_prompt.py --iso SPP --year 2024 \\
        --sha $(git rev-parse HEAD) --lane spp-101 \\
        --bundle results/calibration/spp100_arm_span \\
        --set spp_mmu_offer_unavailability=true --note "SPP-101 arm" \\
        > /tmp/shard_spp101_2024.txt

Then pass the text as the ``prompt`` of
``mcp__claude-code-remote__create_session`` with ``source_revision=<sha>``.
Pass ``--all-years`` to print one prompt per solved year of the bundle.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/jessicacohen554-cyber/market-simulator"

TEMPLATE = """SOLVE SHARD {lane}-{year} — {iso} backcast year {year}, ONE year, ONE container (rule 36). Model: Opus.
DATA PROFILE: {profile}

HARD STOPS — check each FIRST; if any fails, STOP and report (do not push, do not repair):
1. `git rev-parse HEAD` == {sha}  (never pull, rebase, merge or "sync"; a SHA cannot be raced)
2. `python3 scripts/prepare_solve_container.py` — FIRST, before any data step (R-50: swap is bounded by free disk, and the data steps below eat it); report its `before:` and `swap:` lines
3. `python3 scripts/hydrate_data.py --profile {profile}` then `python3 scripts/regenerate_clean.py --solve-profile {iso}` (if that flag is absent at this SHA, run `python3 scripts/regenerate_clean.py`); both exit 0{fetch_step}
4. the recipe you will solve: `{bundle}` replayed{set_clause}; confirm by reading `{bundle}/run_config.json` and `meta.json` — the config signature the parent expects: {signature}
5. memory: the runner calls `scripts/lib/solve_container.ensure_solve_container` itself; never pass `--no-container-preflight`, never read `free` — report the `container preflight:` and `memory peak:` log lines

SOLVE (sequential, this year only):
  eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"
  python3 scripts/replay_keeper.py {bundle} --years {year} --out-dir {out_dir}{set_args}{note_arg}
Budget: {budget} minutes of wall clock for the LP. At the budget with no bundle written: STOP and report; never push a half-written bundle (rule 27).

PUSH THE WHOLE BUNDLE (rule 34 (a) — a bundle that cannot back a promotion is a wasted solve):
  git checkout -b {branch}
  printf '\\n!{out_dir}/**\\n' >> .gitignore
  git add .gitignore && git add {out_dir}
  git status --short      # MUST show nothing outside .gitignore and {out_dir}
  git commit -m "{lane}: {iso} {year} leg ({out_dir})"
  git push -u origin {branch}     # on HTTP 408/500: git config http.version HTTP/1.1, retry
`{out_dir}/dispatch/{year}_P1.parquet` MUST be in the pushed tree (`git ls-tree -r HEAD -- {out_dir}/dispatch`). A plain `git add` after the .gitignore negation — never `git add -f`, never `git add -A`, never `git add .`.

FORBIDDEN, by name: git add -A / git add . ; any edit under src/ or scripts/ ; dashboard_add_run.py, build_manifest.py, build_status.py, prune_iso_runs.py, promote_keeper.py, anything under frontend/data/ (registration is the parent's job, once) ; opening a PR ; deleting any result (rule 31) ; solving any other year.

REPORT in your final message, in numbers: HEAD sha; the `container preflight:` and `memory peak:` lines; LP wall time; for {year}: objective, total generation TWh by class, mean and p99 price per zone, unserved energy MWh; the commit sha and branch; `git ls-tree` count under {out_dir}; and any hard stop that fired. A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.
"""

PROFILE = {
    "ERCOT": "ercot",
    "CAISO": "caiso",
    "PJM": "pjm",
    "MISO": "miso",
    "NYISO": "nyiso",
    "NEISO": "neiso",
    "SPP": "spp",
    "NWPP": "nwpp",
    "SOCO": "soco",
}


def _signature(bundle: Path, sets: list[str]) -> str:
    """A short config signature the shard can check: the overrides plus the
    bundle's model-changes note, so a wrong recipe is visible at a glance."""
    cfg = {}
    rc = bundle / "run_config.json"
    if rc.exists():
        try:
            cfg = json.loads(rc.read_text())
        except json.JSONDecodeError:
            cfg = {}
    note = (cfg.get("model_changes") or cfg.get("note") or "")[:160]
    parts = [f"{k}" for k in sets] or ["(keeper recipe unchanged)"]
    return "; ".join(parts) + (f" | bundle note: {note!r}" if note else "")


#: The recipe field whose arming needs the gitignored PJM DA virtual-bid
#: parquets on disk (``data.virtual_bids`` hard-fails without them).
DA_VIRTUALS_FIELD = "pjm_da_virtual_bids"

DA_VIRTUALS_FETCH = (
    "\n   then `uv run python scripts/data/fetch_pjm_da_virtuals.py --years {year} "
    "--feeds hrl_da_incs_decs` ({why}; the parquets under data/raw/pjm-da-virtuals/ "
    "are gitignored — never commit them); exits 0"
)

#: Why the fetch is emitted, by :func:`da_virtuals_fetch_reason`'s outcome.
_ARMED = "the recipe arms `pjm_da_virtual_bids`"
_UNREADABLE = "fetch unconditionally; recipe unreadable"


def da_virtuals_fetch_reason(iso: str, bundle: Path, sets: list[str]) -> str | None:
    """Why this shard needs the PJM DA-virtuals fetch, or ``None`` if it does not.

    PJM only (the mechanism is PJM-gated). The bundle's ``run_config.json``
    ``scenario_config`` value is the recipe; a ``--set
    pjm_da_virtual_bids=<json>`` overrides it (last one wins), as it does in
    ``replay_keeper``. Recipe-gated rather than ISO-gated because the field is
    default off, so a PJM recipe without it needs no fetch — but a PJM recipe
    that cannot be read fetches unconditionally rather than silently skipping.
    """
    if iso.upper() != "PJM":
        return None
    armed: bool | None = None
    try:
        cfg = json.loads((bundle / "run_config.json").read_text())
        armed = bool((cfg.get("scenario_config") or {}).get(DA_VIRTUALS_FIELD, False))
    except (OSError, json.JSONDecodeError, AttributeError):
        armed = None
    for spec in sets:
        key, _, value = spec.partition("=")
        if key.strip() == DA_VIRTUALS_FIELD:
            try:
                armed = bool(json.loads(value))
            except json.JSONDecodeError:
                armed = value.strip().lower() == "true"
    if armed is None:
        return _UNREADABLE
    return _ARMED if armed else None


def render(
    iso: str,
    year: int,
    sha: str,
    lane: str,
    bundle: str,
    sets: list[str],
    note: str | None,
    budget: int,
) -> str:
    """Fill :data:`TEMPLATE` for one ISO-year shard."""
    iso = iso.upper()
    b = REPO / bundle
    out_dir = f"results/calibration/{lane.replace('-', '_')}_{year}"
    return TEMPLATE.format(
        lane=lane,
        year=year,
        iso=iso,
        profile=PROFILE.get(iso, iso.lower()),
        sha=sha,
        bundle=bundle,
        out_dir=out_dir,
        branch=f"claude/{lane}-{year}",
        set_clause=(" with " + ", ".join(sets)) if sets else "",
        set_args="".join(f" --set {s}" for s in sets),
        note_arg=f" --note {json.dumps(note)}" if note else "",
        signature=_signature(b, sets),
        budget=budget,
        fetch_step=(
            DA_VIRTUALS_FETCH.format(year=year, why=why)
            if (why := da_virtuals_fetch_reason(iso, b, sets))
            else ""
        ),
    )


def main() -> None:
    """CLI entry point: print one shard prompt per requested year."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--iso", required=True)
    ap.add_argument("--year", type=int, help="one year (or --all-years)")
    ap.add_argument(
        "--all-years",
        action="store_true",
        help="one prompt per year in the bundle's meta.json",
    )
    ap.add_argument("--sha", required=True, help="full 40-char SHA the shard pins")
    ap.add_argument("--lane", required=True, help="lane id, e.g. spp-101")
    ap.add_argument(
        "--bundle",
        required=True,
        help="keeper bundle whose recipe is replayed (results/calibration/<name>)",
    )
    ap.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="FIELD=JSON",
        help="replay_keeper --set override; repeatable",
    )
    ap.add_argument("--note", help="run note recorded in the new bundle")
    ap.add_argument(
        "--budget", type=int, default=90, help="LP wall-clock budget, minutes"
    )
    args = ap.parse_args()
    if len(args.sha) != 40:
        raise SystemExit(
            "--sha must be the FULL 40-character commit SHA (rule 32 (c)(1))"
        )
    if not args.year and not args.all_years:
        raise SystemExit("give --year or --all-years")
    years = [args.year]
    if args.all_years:
        meta = json.loads((REPO / args.bundle / "meta.json").read_text())
        years = sorted(
            int(y) for y in (meta.get("years") or meta.get("solved_years") or [])
        )
        if not years:
            raise SystemExit("bundle meta.json names no years")
    for i, y in enumerate(years):
        if i:
            print("\n" + "=" * 100 + "\n")
        sys.stdout.write(
            render(
                args.iso,
                y,
                args.sha,
                args.lane,
                args.bundle,
                args.set,
                args.note,
                args.budget,
            )
        )


if __name__ == "__main__":
    main()
