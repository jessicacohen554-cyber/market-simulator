"""Bundle persistence / provenance helpers (ex-``scripts/run_calibration_full.py``).

Orchestrator-unification lane, Stage-D persist half, first increment
(refactor-consolidation plan §5): the audit-trail writers and their closure
— the environment block, git provenance capture, the JSON encoder fallback,
the offer-curve JSON validator, and ``write_run_config`` — moved here
verbatim. ``run_calibration_full.py`` keeps permanent same-name
``_``-prefixed aliases (its exported symbols are a frozen surface:
``replay_keeper.py`` reads ``rcf._environment_block`` /
``rcf._parse_offer_curve_json``, tests import the same names). Subsequent
Stage-D increments move the frame writers and ``solve_and_persist`` itself;
each increment stays under the file-integrity guard's shrink threshold or
carries the ``intentional-shrink`` label.

``run_config.json`` / ``meta.json`` key sets are FROZEN surfaces (replay,
goldens, and ``--reuse-solved`` all reconstruct from them) — this move
relocates the writers without touching a key.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from market_sim.config.paths import REPO_ROOT
from market_sim.config.plant_taxonomy import fossil_classes

logger = logging.getLogger(__name__)

__all__ = [
    "ENVIRONMENT_PACKAGES",
    "GIT_STATE_EXCLUDE",
    "highspy_version",
    "environment_block",
    "json_default",
    "git_sha",
    "git_cmd",
    "git_state",
    "parse_offer_curve_json",
    "write_run_config",
]


def highspy_version() -> str:
    """Return the installed highspy version, or '' if unavailable."""
    try:
        from importlib.metadata import version

        return version("highspy")
    except Exception:
        return ""


# Packages whose versions can move alternate-optimal vertices (and thus a
# bundle's per-class TWh at an identical objective). Recorded so a byte-identity
# claim is checkable across environments.
ENVIRONMENT_PACKAGES = ("highspy", "numpy", "scipy", "pandas", "pyarrow", "pydantic")


def environment_block() -> dict:
    """Capture the runtime environment for cross-environment reproducibility.

    Records the Python version, platform string, and the installed versions of
    the solver/numerics stack in :data:`ENVIRONMENT_PACKAGES`. Stamped into
    both ``meta.json`` and ``run_config.json``. ``replay_keeper`` warns (never
    fails) on a mismatch; the ``--reuse-solved`` gate ignores this block (reuse
    is pinned by the persisted ``scenario_config`` plus the dedicated highspy
    version gate), so adding it does not change any reuse decision.
    """
    import platform
    from importlib.metadata import PackageNotFoundError, version

    versions: dict[str, str] = {}
    for name in ENVIRONMENT_PACKAGES:
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = ""
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "packages": versions,
    }


def json_default(obj: object) -> object:
    """JSON encoder fallback for bundle metadata.

    ``set``/``frozenset`` (e.g. ``ScenarioConfig.wefor_residual_groups``,
    carried through the generic prb_overrides channel) serialize as a sorted
    list; anything else falls back to ``str`` so the dump never crashes
    mid-bundle (the run-104..106 failure mode: a frozenset in the override
    record aborted meta.json after the parquets were already written).
    """
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    return str(obj)


def git_sha() -> str:
    """Return the current git short SHA, or '' if unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def git_cmd(*args: str) -> str:
    """Run a git command in the repo root and return stripped stdout (or '')."""
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


# Paths excluded from the manifest's git state: a run's own outputs (and other
# bundles) are not "model changes" and would just be noise.
GIT_STATE_EXCLUDE = (":(exclude)results", ":(exclude)outputs")


def git_state() -> dict:
    """Capture git provenance so a bundle records exactly which code ran.

    Returns the short SHA, branch, a ``dirty`` flag, the list of changed model
    files, and a diffstat. ``results/`` and ``outputs/`` are excluded so the
    state reflects model/source edits, not the run's own artifacts. When dirty
    the run included uncommitted model changes; the caller snapshots the diff.
    """
    porcelain = git_cmd("status", "--porcelain", "--", *GIT_STATE_EXCLUDE)
    changed = [ln[3:] for ln in porcelain.splitlines()] if porcelain else []
    return {
        "sha": git_cmd("rev-parse", "--short", "HEAD"),
        "branch": git_cmd("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(porcelain),
        "changed_files": changed,
        "diffstat": git_cmd("diff", "--stat", "HEAD", "--", *GIT_STATE_EXCLUDE),
    }


def parse_offer_curve_json(
    raw: str | None, flag: str = "--offer-curve-json"
) -> dict | None:
    """Parse an offer-curve JSON argument, failing fast on bad input.

    Accepts an inline JSON object, a path to a ``.json`` file, or ``None``.
    Returns the parsed ``{class: {band: number}}`` mapping, or ``None`` when
    nothing was given. Used for both the absolute ``--offer-curve-json`` and
    the relative ``--offer-curve-delta-json`` (same shape: class -> band ->
    number). Raises ``SystemExit`` with a clear, ``flag``-tagged message on
    malformed JSON or the wrong shape so a CI run fails loudly rather than
    silently solving against the wrong curve.
    """
    if raw is None or not str(raw).strip():
        return None
    text = raw
    candidate = Path(raw)
    if not raw.lstrip().startswith("{") and candidate.exists():
        text = candidate.read_text()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"{flag}: invalid JSON ({exc}). Expected an object "
            'like {"CT_PEAKER":{"committed":1.40,"econ_low":1.27}}.'
        )
    if not isinstance(parsed, dict):
        raise SystemExit(
            f"{flag}: top level must be a JSON object keyed by "
            f"fleet class, got {type(parsed).__name__}."
        )
    valid_classes = set(fossil_classes())
    for cls, bands in parsed.items():
        # Fail loudly on a class key the offer-curve router will never read
        # (e.g. COAL_SUB after the SUB -> COAL_PRB taxonomy rename): a dead
        # knob silently tunes nothing, which is worse than an error.
        if cls not in valid_classes:
            raise SystemExit(
                f"{flag}: unknown fleet class {cls!r} — the offer-curve "
                f"router only reads {sorted(valid_classes)}. (Sub-bituminous "
                "coal is COAL_PRB; COAL_SUB no longer exists.)"
            )
        if not isinstance(bands, dict):
            raise SystemExit(
                f"{flag}: value for {cls!r} must be an object of "
                f"band->number, got {type(bands).__name__}."
            )
        for band, val in bands.items():
            if band == "peak_ladder":
                # Measured peak-band quantile ladder: a list of
                # [capacity_share, multiplier] rungs (derive_dam_offer_hrmults
                # --peak-ladder). Shares must be positive and sum to ~1 so the
                # rungs exactly re-partition the peak tranche's capacity.
                if not (
                    isinstance(val, list)
                    and val
                    and all(
                        isinstance(r, (list, tuple))
                        and len(r) == 2
                        and all(
                            isinstance(x, (int, float)) and not isinstance(x, bool)
                            for x in r
                        )
                        and r[0] > 0
                        for r in val
                    )
                ):
                    raise SystemExit(
                        f"{flag}: {cls}.peak_ladder must be a non-empty list of "
                        f"[capacity_share, multiplier] pairs, got {val!r}."
                    )
                total = sum(float(r[0]) for r in val)
                if not 0.99 <= total <= 1.01:
                    raise SystemExit(
                        f"{flag}: {cls}.peak_ladder capacity shares must sum to "
                        f"1.0 (±0.01), got {total:.3f}."
                    )
                continue
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise SystemExit(f"{flag}: {cls}.{band} must be a number, got {val!r}.")
    return parsed


def write_run_config(
    run_dir: Path, cfg, meta: dict, note: str = "", ablation_of: str | None = None
) -> None:
    """Write ``run_config.json`` (and ``model_changes.diff`` if dirty).

    A discrete, self-contained record of what was run: the full resolved
    ``ScenarioConfig`` (every knob), the calibration flags, git provenance,
    and any free-text note describing pre-run model changes. The companion
    ``model_changes.diff`` snapshots uncommitted edits so the exact code is
    reproducible from the bundle alone.

    ``ablation_of`` (D-3, CLAUDE.md rule 20): when this bundle is a zero-forcing
    ablation twin, the base keeper bundle name it ablates is recorded at the top
    level so the twin is self-identifying and the calibration-report skill can
    link it from the keeper's sidecar ``ablation_twin`` field.
    """
    import dataclasses

    git = git_state()
    payload = {
        "timestamp": meta.get("timestamp"),
        "git": git,
        "model_changes_note": note,
        "ablation_of": ablation_of,
        "calibration_flags": {
            k: meta.get(k)
            for k in (
                "iso",
                "years",
                "hours",
                "passes",
                "commitment",
                "commitment_screen_coal",
                "gas_prices",
                "outage_source",
                "coal_lignite_mustrun",
                "coal_prb_mustrun",
                "coal_prb_passthrough",
                "coal_prb_passthrough_sigmoid",
                "coal_mustrun_per_plant",
                "retiree_cems_cap",
                "ct_mustrun_per_plant",
                "ct_mustrun_floor_frac",
                "coal_drop_pof",
                "coal_prb_passthrough_tiered",
                "coal_prb_sigmoid_overrides",
                "coal_bit_passthrough_sigmoid",
                "coal_bit_sigmoid_overrides",
                "coal_plant_monthly_pricing",
                "td_loss_factor",
                "offer_curve_overrides",
                "offer_curve_deltas",
                "priced_interchange",
                "ercot_rtordpa_overlay",
                "ercot_dam_as_overlay",
                "ercot_dam_as_overlay_from_year",
                "ercot_dam_as_scarcity_threshold",
                "temp_dependent_derate",
                "nyiso_dynamic_reserve_requirements",
                "git_sha",
            )
        },
        "scenario_config": dataclasses.asdict(cfg),
        # Runtime environment mirror (same block stamped into meta.json). Kept
        # OUTSIDE scenario_config so the --reuse-solved comparator — which only
        # diffs scenario_config — is unaffected.
        "environment": meta.get("environment") or environment_block(),
    }
    if "reuse" in meta:
        # Mixed --reuse-solved bundle: mirror the reuse labeling into the
        # self-contained run record. Absent the flag this key never exists
        # and the payload is byte-identical to before the flag was added.
        payload["reuse"] = meta["reuse"]
    (run_dir / "run_config.json").write_text(
        json.dumps(payload, indent=2, default=json_default)
    )
    if git["dirty"]:
        diff = git_cmd("diff", "HEAD", "--", *GIT_STATE_EXCLUDE)
        if diff:
            (run_dir / "model_changes.diff").write_text(diff)
