"""Capture current-HEAD golden baselines for the six calibration keepers.

Stage 0 of the orchestrator-unification plan
(``docs/handoffs/orchestrator-unification-plan-2026-07.md`` §6-§7) needs a
deterministic, faithful re-solve of every registered keeper bundle *at the
current commit*, so a later refactor stage can capture an "after" set and diff
it against this "before" set for dispatch neutrality.

What this script does, per keeper:

1. Resolve the keeper id (``frontend/data/backcast/keepers.json``) to its frozen
   bundle (the registry sidecar's ``bundle`` field), then read that bundle's
   ``meta.json`` — the authoritative record of every argument the keeper was
   solved with (~134 keys, one per ``solve_and_persist`` parameter, four under
   a recorded-name alias).
2. Reconstruct the exact ``solve_and_persist`` keyword arguments from that
   ``meta.json`` (signature introspection + a four-entry alias map; every
   parameter absent from the record is left at its function default, which is
   verified benign — see the fidelity oracle below).
3. Re-solve at HEAD with determinism pinned
   (``MARKET_SIM_HIGHS_THREADS=1``, ``MARKET_SIM_WARMSTART=1``,
   ``MARKET_SIM_WARMSTART_XYEAR=0`` — cold-vs-cold at one thread is
   bit-identical; multi-threaded dual simplex is NOT — see
   ``docs/cross-year-warmstart.md``), writing the full P1 bundle
   (``dispatch/<year>_P1.parquet``, ``system.parquet``, ``flows.parquet``, …)
   into ``results/regression-goldens/<stage-tag>/<iso>/``.
4. **Fidelity oracle:** re-read the golden bundle's freshly-written
   ``meta.json`` / ``run_config.json`` and assert every key it shares with the
   keeper's record is identical. A single mismatch means a flag was dropped or
   mis-mapped; the capture fails loudly rather than emitting a worthless golden.
   Keys present only in the golden (new fields added to ``ScenarioConfig`` /
   ``meta`` since the keeper was frozen) are reported, not failed — goldens are
   current-HEAD baselines, not byte-reproductions of the July-3 bundles.
5. Write a hashes-only ``manifest.json`` (git SHA, env pins, per-file *content*
   hashes, per-keeper fidelity summary). The multi-GB parquet bundles live under
   the gitignored goldens dir; only the manifest is committed.

Determinism note: the manifest hashes the parquet *content* (canonical column
bytes), not the raw file, because parquet embeds library/version metadata that
varies run-to-run even when the data is identical. The authoritative
byte-identity check between two golden sets is
``scripts/regression_gate.py`` (which runs ``regression_check`` at
``--atol 0 --rtol 0``); the content hashes are a fast pre-screen.

Usage:
    # one keeper, in-process (all its years sequentially):
    python scripts/capture_keeper_goldens.py --iso NEISO --stage-tag stage1-before

    # all six, ≤2 concurrent per-ISO subprocesses (CLAUDE.md rule 8 memory cap):
    python scripts/capture_keeper_goldens.py --all --stage-tag stage1-before

Holdout quarantine (CLAUDE.md rule 22): this only ever solves the years already
recorded in each keeper's ``meta.json`` (all within 2023-2025). It never
introduces a 2022 or 2026 solve.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Mirror run_calibration_full.py's bootstrap: src/ for the package, REPO for the
# `scripts.` namespace-package imports that run_calibration_full performs.
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

# --- Determinism pin. Set BEFORE any solve so dispatch.py's os.environ reads
#     (dispatch.py:MARKET_SIM_HIGHS_THREADS, runner/run_calibration WARMSTART)
#     see the pinned values. Cold-vs-cold at THREADS=1 is bit-identical;
#     multi-threaded dual simplex breaks marginal ties nondeterministically. ---
DETERMINISM_ENV = {
    "MARKET_SIM_HIGHS_THREADS": "1",
    "MARKET_SIM_WARMSTART": "1",
    "MARKET_SIM_WARMSTART_XYEAR": "0",
}
for _k, _v in DETERMINISM_ENV.items():
    os.environ[_k] = _v

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("capture_keeper_goldens")


from scripts.lib import keeper_store  # noqa: E402  (after sys.path insert)

REGISTRY_DIR = REPO / "frontend" / "data" / "backcast" / "registry"
GOLDENS_ROOT = REPO / "results" / "regression-goldens"

# ``meta.json`` records four ``solve_and_persist`` parameters under a different
# (historical / recorded) key name. Every other meta key that is also a
# parameter maps by identity. Verified against the meta-dict construction in
# ``scripts/run_calibration_full.py`` (~line 2240).
META_KEY_TO_PARAM = {
    "commitment_screen_coal": "screen_coal",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}

# Meta keys that are NOT ``solve_and_persist`` parameters: run identity,
# positional args handled explicitly, gas prices (derived inside
# ``solve_and_persist`` from the reference), and two config-*derived* mirror
# values (not inputs). These are skipped when building kwargs.
META_NON_PARAM_KEYS = {
    "timestamp",
    "iso",
    "years",
    "hours",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",  # derived from _calibration_config, not a kwarg
    "td_loss_factor",  # derived from _calibration_config, not a kwarg
    "shared_inputs",
    "git_sha",
    "highspy_version",
}

# Volatile / derived keys excluded from the AUTHORITATIVE meta comparison. meta
# otherwise echoes the passed kwargs verbatim, so a golden-vs-keeper match on
# every remaining shared key proves each recorded flag was applied identically —
# and, unlike the resolved scenario_config, it does NOT drift with base-config
# code changes. ``coal_plant_monthly_pricing`` / ``td_loss_factor`` are the two
# meta values re-derived from ``_calibration_config`` (not kwarg echoes), so they
# can legitimately drift and are excluded here.
FIDELITY_IGNORE_KEYS = {
    "timestamp",
    "git_sha",
    "highspy_version",
    "shared_inputs",
    "gas_prices",  # derived from the reference; compared informationally
    "coal_plant_monthly_pricing",  # re-derived from _calibration_config
    "td_loss_factor",  # re-derived from _calibration_config
}


def _git_sha() -> str:
    """Return the short git SHA of HEAD, or ``"unknown"``."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True
        )
        return out.strip()
    except Exception:
        return "unknown"


def _git_dirty() -> bool:
    """Return True if the working tree has uncommitted changes."""
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=REPO, text=True
        )
        return bool(out.strip())
    except Exception:
        return False


def resolve_keeper_bundles(only_isos: set[str] | None = None) -> dict[str, dict]:
    """Map each ISO to its keeper id and frozen bundle path.

    Reads the sharded keeper store (``keepers/<ISO>.json``, via
    ``scripts.lib.keeper_store``) for the current keeper ids and each keeper's
    registry sidecar for the bundle directory (the sidecar's ``bundle`` field —
    NOT the id-named directory, which is empty).

    Args:
        only_isos: When given, resolve (and validate) only these ISOs, so a
            scoped ``--iso`` capture does not fail on an unrelated ISO whose
            keeper bundle is missing from the tree.

    Returns:
        ``{iso: {"keeper_id": str, "bundle": Path, "years": list[int]}}``.
    """
    ids = keeper_store.keeper_list(REPO)
    out: dict[str, dict] = {}
    for keeper_id in ids:
        sidecar = REGISTRY_DIR / f"{keeper_id}.json"
        if not sidecar.is_file():
            raise FileNotFoundError(f"registry sidecar missing: {sidecar}")
        reg = json.loads(sidecar.read_text())
        iso = reg["iso"].upper()
        if only_isos is not None and iso not in only_isos:
            continue
        bundle = REPO / reg["bundle"]
        if not (bundle / "meta.json").is_file():
            raise FileNotFoundError(
                f"{keeper_id}: bundle meta.json missing at {bundle}"
            )
        out[iso] = {
            "keeper_id": keeper_id,
            "bundle": bundle,
            "years": [int(y) for y in reg["years"]],
        }
    return out


def build_solve_kwargs(meta: dict, solve_fn) -> tuple[dict, list[str]]:
    """Reconstruct ``solve_and_persist`` kwargs from a keeper's ``meta.json``.

    For every ``solve_and_persist`` parameter, use the value recorded in
    ``meta`` (mapping the four alias keys), else leave it at the function
    default. Returns the kwargs and the list of parameters left at default that
    are *invisible* to the record (params with no meta key at all) — the
    explicit, documented residual blind-spot for the fidelity report.

    Args:
        meta: The keeper bundle's parsed ``meta.json``.
        solve_fn: The ``solve_and_persist`` callable (for signature
            introspection).

    Returns:
        ``(kwargs, defaulted_unrecorded_params)``.
    """
    sig = inspect.signature(solve_fn)
    params = set(sig.parameters)
    # Positional / explicitly-handled args are not filled from the generic scan.
    handled = {
        "years",
        "iso",
        "hours",
        "reference",
        "commitment",
        "screen_coal",
        "run_dir",
        "note",
        "persist_p2_state",
    }

    kwargs: dict = {}
    for meta_key, value in meta.items():
        if meta_key in META_NON_PARAM_KEYS:
            continue
        param = META_KEY_TO_PARAM.get(meta_key, meta_key)
        if param in params and param not in handled:
            kwargs[param] = value

    # Params with no representation anywhere in meta → left at default. Record
    # which ones so the fidelity report names the exact blind spot instead of
    # silently dropping. (Verified across all six keepers: every such param is
    # ISO-irrelevant or default-only — see the plan §7.3 note.)
    recorded_params = {
        META_KEY_TO_PARAM.get(k, k) for k in meta if k not in META_NON_PARAM_KEYS
    }
    defaulted = sorted(
        p for p in params if p not in handled and p not in recorded_params
    )
    return kwargs, defaulted


def _content_hash(path: Path) -> str:
    """Hash a parquet file's *content* (stable across library metadata).

    Reads the frame, sorts columns, and hashes each column's float64 bytes in
    order plus the shape — reproducible whenever the underlying data is
    identical, unlike a raw-file hash which picks up parquet's embedded
    creation metadata.
    """
    import numpy as np
    import pandas as pd

    df = pd.read_parquet(path)
    h = hashlib.sha256()
    h.update(str(df.shape).encode())
    for col in sorted(map(str, df.columns)):
        h.update(col.encode())
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            h.update(np.ascontiguousarray(series.to_numpy(dtype="float64")).tobytes())
        else:
            h.update(series.astype(str).str.cat(sep="\x00").encode())
    return h.hexdigest()


def _hash_bundle(run_dir: Path) -> dict[str, str]:
    """Content-hash every result parquet in a golden bundle."""
    hashes: dict[str, str] = {}
    for pat in ("dispatch/*.parquet", "*.parquet"):
        for p in sorted(run_dir.glob(pat)):
            rel = str(p.relative_to(run_dir))
            hashes[rel] = _content_hash(p)
    return hashes


def _fidelity_check(keeper_bundle: Path, golden_dir: Path) -> dict:
    """Assert the golden re-solve applied every recorded keeper flag.

    Compares the golden's freshly-written ``meta.json`` and
    ``run_config.json`` (``scenario_config``) against the keeper's on the
    intersection of keys. Any mismatch is a dropped/mis-mapped flag → the
    returned dict carries a non-empty ``mismatched`` list and the caller fails.

    Returns a summary dict with ``matched`` / ``mismatched`` / ``golden_only`` /
    ``keeper_only`` for both meta and scenario_config.
    """

    def _load(d: Path, name: str) -> dict:
        p = d / name
        return json.loads(p.read_text()) if p.is_file() else {}

    def _compare(keep: dict, gold: dict, ignore: set) -> dict:
        kk = set(keep) - ignore
        gk = set(gold) - ignore
        shared = kk & gk
        mismatched = []
        for k in sorted(shared):
            a, b = keep[k], gold[k]
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                if abs(float(a) - float(b)) > 1e-12:
                    mismatched.append({"key": k, "keeper": a, "golden": b})
            elif a != b:
                mismatched.append({"key": k, "keeper": a, "golden": b})
        return {
            "matched": len(shared) - len(mismatched),
            "mismatched": mismatched,
            "keeper_only": sorted(kk - gk),
            "golden_only": sorted(gk - kk),
        }

    keep_meta = _load(keeper_bundle, "meta.json")
    gold_meta = _load(golden_dir, "meta.json")
    keep_cfg = _load(keeper_bundle, "run_config.json").get("scenario_config", {})
    gold_cfg = _load(golden_dir, "run_config.json").get("scenario_config", {})

    return {
        "meta": _compare(keep_meta, gold_meta, FIDELITY_IGNORE_KEYS),
        "scenario_config": _compare(keep_cfg, gold_cfg, set()),
    }


def capture_one(iso: str, stage_tag: str, info: dict) -> dict:
    """Re-solve one keeper at HEAD into the golden dir; return its manifest entry.

    Raises:
        RuntimeError: if the fidelity oracle finds any applied-flag mismatch.
    """
    # Heavy import deferred until after the determinism env is pinned.
    from scripts.run_calibration import _load_reference
    from scripts.run_calibration_full import solve_and_persist

    meta = json.loads((info["bundle"] / "meta.json").read_text())
    years = [int(y) for y in meta["years"]]
    hours = int(meta["hours"])
    kwargs, defaulted = build_solve_kwargs(meta, solve_and_persist)

    golden_dir = GOLDENS_ROOT / stage_tag / iso
    golden_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "[%s] re-solving keeper %s years=%s hours=%s (%d recorded flags, "
        "%d params defaulted)",
        iso,
        info["keeper_id"],
        years,
        hours,
        len(kwargs),
        len(defaulted),
    )

    reference = _load_reference()
    solve_and_persist(
        years,
        iso,
        hours,
        reference,
        commitment=bool(meta["commitment"]),
        screen_coal=bool(meta["commitment_screen_coal"]),
        run_dir=golden_dir,
        note=f"regression-golden {stage_tag} (Stage-0 baseline; not a keeper)",
        **kwargs,
    )

    fidelity = _fidelity_check(info["bundle"], golden_dir)
    meta_bad = fidelity["meta"]["mismatched"]
    cfg_bad = fidelity["scenario_config"]["mismatched"]

    # HARD gate: the meta comparison. meta echoes the passed kwargs verbatim, so
    # any mismatch on a shared key is a dropped or mis-mapped flag — fail.
    if meta_bad:
        for m in meta_bad[:30]:
            logger.error(
                "[%s] META FLAG MISMATCH %s: keeper=%r golden=%r",
                iso,
                m["key"],
                m["keeper"],
                m["golden"],
            )
        raise RuntimeError(
            f"{iso}: fidelity oracle failed — {len(meta_bad)} recorded flag(s) "
            f"diverged between keeper and golden meta.json; the golden does not "
            f"faithfully replay the keeper's flags."
        )

    # INFORMATIONAL: scenario_config is the RESOLVED config, which legitimately
    # drifts with HEAD base-config changes (goldens are current-HEAD baselines,
    # not byte-reproductions of the July-3 bundles). Surface the drift so a
    # reviewer can sanity-check it, but do not fail on it.
    if cfg_bad:
        logger.warning(
            "[%s] scenario_config drift vs keeper on %d field(s) (expected if "
            "base config moved since the keeper was frozen): %s",
            iso,
            len(cfg_bad),
            ", ".join(m["key"] for m in cfg_bad[:15]),
        )

    logger.info(
        "[%s] fidelity OK: %d recorded flags replayed identically "
        "(%d HEAD-only meta keys); scenario_config %d matched, %d drifted",
        iso,
        fidelity["meta"]["matched"],
        len(fidelity["meta"]["golden_only"]),
        fidelity["scenario_config"]["matched"],
        len(cfg_bad),
    )

    entry = {
        "keeper_id": info["keeper_id"],
        "bundle": str(info["bundle"].relative_to(REPO)),
        "years": years,
        "hours": hours,
        "recorded_flag_count": len(kwargs),
        "defaulted_unrecorded_params": defaulted,
        "fidelity": {
            "meta_matched": fidelity["meta"]["matched"],
            "meta_head_only": fidelity["meta"]["golden_only"],
            "meta_keeper_only": fidelity["meta"]["keeper_only"],
            "scenario_config_matched": fidelity["scenario_config"]["matched"],
            "scenario_config_head_only": fidelity["scenario_config"]["golden_only"],
            "scenario_config_drift": [
                m["key"] for m in fidelity["scenario_config"]["mismatched"]
            ],
        },
        "content_hashes": _hash_bundle(golden_dir),
    }
    return entry


def _run_subprocess(iso: str, stage_tag: str) -> int:
    """Re-invoke this script for a single ISO in its own process."""
    env = dict(os.environ)
    env.update(DETERMINISM_ENV)
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--iso",
        iso,
        "--stage-tag",
        stage_tag,
        "--_single",
    ]
    logger.info("[%s] launching subprocess", iso)
    return subprocess.call(cmd, env=env, cwd=REPO)


def write_manifest(stage_tag: str, entries: dict[str, dict]) -> Path:
    """Write / merge the hashes-only manifest for a stage tag."""
    import highspy

    manifest_path = GOLDENS_ROOT / stage_tag / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text()).get("keepers", {})
    existing.update(entries)
    payload = {
        "stage_tag": stage_tag,
        "git_sha": _git_sha(),
        "git_dirty": _git_dirty(),
        "env": DETERMINISM_ENV,
        "highspy_version": getattr(highspy, "__version__", "unknown"),
        "hash_scheme": "sha256-of-canonical-column-float64-bytes",
        "note": (
            "Current-HEAD regression baselines (Stage-0). NOT byte-reproductions "
            "of the registered July-3 keeper bundles. Multi-GB bundles are "
            "gitignored; only this manifest is committed."
        ),
        "keepers": existing,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    logger.info("manifest written: %s (%d keepers)", manifest_path, len(existing))
    return manifest_path


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iso",
        nargs="+",
        default=None,
        help="ISO(s) to capture (e.g. NEISO, or ERCOT CAISO). Omit with --all.",
    )
    parser.add_argument("--all", action="store_true", help="Capture all six keepers.")
    parser.add_argument(
        "--stage-tag",
        required=True,
        help="Golden subdir tag, e.g. stage1-before / stage1-after / aa-run1.",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=2,
        help="Max concurrent per-ISO subprocesses (CLAUDE.md rule 8: ≤2 for "
        "per-plant multi-zone LPs). Default 2.",
    )
    parser.add_argument(
        "--_single",
        action="store_true",
        help=argparse.SUPPRESS,  # internal: in-process single-ISO solve
    )
    args = parser.parse_args()

    only = {i.upper() for i in args.iso} if args.iso and not args.all else None
    bundles = resolve_keeper_bundles(only_isos=only)
    if args.all:
        isos = sorted(bundles)
    elif args.iso:
        isos = [i.upper() for i in args.iso]
    else:
        parser.error("provide --iso <ISO...> or --all")

    for iso in isos:
        if iso not in bundles:
            parser.error(f"{iso} is not a registered keeper ISO ({sorted(bundles)})")

    # Single in-process ISO (also the subprocess-child path).
    if args._single or len(isos) == 1:
        rc = 0
        for iso in isos:
            try:
                entry = capture_one(iso, args.stage_tag, bundles[iso])
                write_manifest(args.stage_tag, {iso: entry})
            except Exception:
                logger.exception("[%s] capture failed", iso)
                rc = 1
        return rc

    # Multiple ISOs: fan out to ≤max_concurrency subprocesses (memory cap).
    rc = 0
    with ThreadPoolExecutor(max_workers=max(1, args.max_concurrency)) as ex:
        futures = {ex.submit(_run_subprocess, iso, args.stage_tag): iso for iso in isos}
        for fut in as_completed(futures):
            iso = futures[fut]
            code = fut.result()
            if code != 0:
                logger.error("[%s] subprocess exited %d", iso, code)
                rc = 1
    logger.info(
        "all captures complete (rc=%d); manifest at %s",
        rc,
        GOLDENS_ROOT / args.stage_tag / "manifest.json",
    )
    return rc


if __name__ == "__main__":
    sys.exit(main())
