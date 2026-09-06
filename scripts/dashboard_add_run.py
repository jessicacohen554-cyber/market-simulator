"""Register one calibration bundle on the dashboard, conflict-free.

A single calibration run adds itself to the dashboard by writing only files in
namespaces unique to this run (or byte-deterministic per-ISO parts) — hence
any number of runs landing at once, across any mix of ISOs, never conflict:

  * ``frontend/data/backcast/registry/<id>.json`` — the sidecar: the COMPLETE
    manifest entry (id, label, date, shorthand, definition, years, iso, file)
    plus the bundle path. ``scripts/build_manifest.py`` assembles
    ``manifest.js`` from sidecars alone, so edit the sidecar to refine a
    label/definition.
  * ``frontend/data/backcast/runs/<id>.js`` — this run's own payload.
  * ``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` — the per-(ISO, year)
    benchmark parts for this run's years (newest run covering a year supplies
    it; unchanged content re-renders to identical bytes, so these only appear
    in the diff when the benchmark genuinely changed).

The shared ``manifest.js`` / ``benchmark.js`` are GENERATED — rebuilt from
sidecars + parts by ``scripts/build_manifest.py`` locally and at deploy time
(the deploy workflow is their single writer). Never hand-commit them. The
results surface is the codebase site: ``docs/codebase-site/backcast-runs.html``
(run explorer) and ``calibration-status.html`` (all-ISO keeper summary).

Commit: the bundle dir, the sidecar, ``runs/<id>.js``, and anything changed
under ``bench/``. Prints ``RUN_ID=<id>`` on stdout so callers can stage by id.

REGISTRATION-TIME HOLDOUT GATE (owner ruling R-AZ, 2026-09-06): this script is
the single seam where a run's solve years become a committed sidecar, so it
re-checks the rule-22 tier marker HERE — a marker held when the solve launched
does not authorize a registration after it was withdrawn. See
``enforce_registration_marker_gate``. There is no bypass flag.

Usage:
    python scripts/dashboard_add_run.py --label "ct sweep 1.5" \
        --bundle results/calibration/ct_sweep_15
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import render_backcast as rb  # noqa: E402  (after sys.path insert)
from scripts.lib import holdout_policy, keeper_store  # noqa: E402

from market_sim.config.constants import STATMODE_PROBE_RUNS  # noqa: E402


DATA_DIR = REPO / "frontend" / "data" / "backcast"
REGISTRY_DIR = DATA_DIR / "registry"
RUNS_DIR = DATA_DIR / "runs"
CALIB_ROOT = REPO / "results" / "calibration"

# Retention rule (2026-06-21, user-set; supersedes the 10-run rule): the
# dashboard keeps the top-15 runs per ISO. When a registration pushes an ISO
# over the cap, ``prune_iso`` drops the displaced OLDEST runs — deleting the
# registry sidecar, the ``runs/<id>.js`` payload AND the mapped
# ``results/calibration/<bundle>/`` dir together, so the three stores can never
# drift into orphans (keepers and ablation-referenced twins are never pruned).
KEEP_PER_ISO = 15


def _protected_run_ids() -> set[str]:
    """Return run ids retention must never prune, whatever their age.

    * Every current keeper in the sharded keeper store (``keepers/<ISO>.json``,
      via ``scripts.lib.keeper_store``) — dropping its bundle would break the
      all-ISO Calibration Status page (whose verdicts read the bundle).
    * Any run referenced by a surviving sidecar's ``ablation_twin`` /
      ``ablation_of`` link — pruning it would dangle the cross-reference that
      ``check_registry_payload_parity.py`` enforces.
    * Every D-7 statmode probe run named in ``STATMODE_PROBE_RUNS`` — the
      structural-error prior's committed source (``structural_prior``). A
      prior prune already deleted several of these ``runs/<id>.js`` payloads as
      collateral damage (ercot32/nyiso/neiso), which is exactly why the prior
      was inverted onto a committed artifact (item 8); protecting them here
      keeps the payload-vs-artifact consistency check runnable and stops the
      frozen ``STATMODE_PROBE_RUNS`` provenance from dangling again.
    """
    protected: set[str] = set(keeper_store.keeper_list())
    # Config-partition members (the two-config keeper structure, owner ruling
    # 2026-08-26): every run a shard's `config_partition` designates is a live
    # keeper config — the Calibration Status page scores it on every rebuild,
    # so pruning it would break the page exactly like pruning the keeper.
    for iso in keeper_store.iso_list():
        shard = keeper_store.load_shard(iso) or {}
        for cfg in (shard.get("config_partition") or {}).get("configs", []):
            rid = cfg.get("run_id")
            if isinstance(rid, str) and rid:
                protected.add(rid)
    # Structural-prior source payloads (frozen provenance) are never pruned.
    protected.update(STATMODE_PROBE_RUNS.values())
    for path in REGISTRY_DIR.glob("*.json"):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        for field in ("ablation_twin", "ablation_of"):
            ref = rec.get(field)
            if isinstance(ref, str) and ref.startswith("20"):
                protected.add(ref)
    return protected


def _bundle_dir(rec: dict) -> Path | None:
    """Resolve a sidecar's ``bundle`` field to a path under
    ``results/calibration`` (None if absent or — as a hard safety guard —
    outside that root, so retention can never delete an arbitrary path)."""
    raw = rec.get("bundle")
    if not raw:
        return None
    p = Path(raw)
    p = p if p.is_absolute() else REPO / p
    try:
        p.resolve().relative_to(CALIB_ROOT.resolve())
    except ValueError:
        return None
    return p


def resolve_bundle(raw: str | Path) -> Path:
    """Return ``raw`` as the absolute bundle directory, independent of the CWD.

    An absolute path is taken as-is; a relative one is anchored at the repo
    root — the documented ``results/calibration/<name>`` form, the same
    convention ``_bundle_dir`` applies to the sidecar's repo-relative
    ``bundle`` field. Anchoring once here keeps every downstream use of the
    path (the ``meta.json`` guard, rendering, and the ``metrics.json``
    sidecar write) pointed at the bundle dir. Previously ``main`` used the
    raw CLI path, so a relative ``--bundle`` composed against the process
    CWD: run from outside the repo root the metrics sidecar landed under the
    CWD, and even from the repo root the relative path broke the
    ``relative_to(REPO)`` completion message, which the best-effort handler
    then misreported as a determination failure (the ercot-193 tooling
    defect, docs/calibration-log/ercot.md ercot-193 Disclosures).
    """
    p = Path(raw)
    return p if p.is_absolute() else REPO / p


def _load_json_doc(path: Path) -> dict:
    """Return a parsed JSON document, or ``{}`` when it is absent.

    Fail-closed by construction for the holdout gate: an absent or empty
    marker file authorizes nothing (``holdout_policy.authorized`` reads a
    missing block as empty), and an absent freeze file freezes nothing while
    an ACTIVE one with no parseable scope freezes every tier
    (``holdout_policy.frozen_tiers``). A malformed document is a hard error,
    never a silent pass.
    """
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def enforce_registration_marker_gate(iso: str, years, repo: Path | None = None) -> None:
    """Refuse to register a run whose solve years are not authorized NOW.

    The registration-time half of the rule-22 spend gate, minted by owner
    ruling **R-AZ** (audit-program director sitting 2026-09-06, card "Marker
    gate": *"Re-check at registration"*). The launch-time gate
    (``run_calibration_full.enforce_holdout_year_gate``) reads the marker once,
    when the LP starts; a multi-hour solve can outlive the authorization it
    launched under. Z-6 is the case
    (``docs/handoffs/holdout-2022-completeness-ercot-nyiso-2026-09-05.md``
    §1a): a NYISO 2022 solve launched under the D56-R ``complete`` marker,
    ``main`` withdrew that marker (nyiso-193) mid-solve, and only the lane's
    own discipline kept the run un-registered at merge. This closes that at
    the seam where solve years become a committed artifact.

    The policy itself is NOT re-implemented here — the tier map, the freeze
    precedence and the marker lookup all come from
    ``scripts.lib.holdout_policy`` (rule 19 ``[R-ONE-MECH]`` in spirit: one
    policy module), so this gate and the launch gate can never disagree about
    which year needs which block. Both marker documents are read from disk on
    every call, which is the freshness the ruling is about.

    There is deliberately NO bypass flag: a registration that fails this check
    is not a registration. It runs before the sidecar, the ``runs/<id>.js``
    payload and the bench parts are written, so a refused run leaves nothing
    behind.

    Args:
        iso: Model ISO id of the run being registered.
        years: The run's solve years (the bundle ``meta.json`` ``years``).
        repo: Repo root; defaults to the module ``REPO`` read at call time.

    Raises:
        SystemExit: with the ISO, years, tier, marker/freeze state and the
            ruling, when any out-of-training year is unauthorized.
    """
    root = repo or REPO
    marker_doc = _load_json_doc(root / holdout_policy.MARKER_FILE)
    freeze_doc = _load_json_doc(root / holdout_policy.FREEZE_FILE)
    refusals = holdout_policy.registration_refusals(years, iso, marker_doc, freeze_doc)
    if not refusals:
        return
    sys.exit(
        "error: REGISTRATION REFUSED (CLAUDE.md rule 22 [R-HOLDOUT]; owner "
        "ruling R-AZ, 2026-09-06 — the tier marker is re-checked at "
        "registration, not only at solve launch).\n  "
        + "\n  ".join(refusals)
        + "\nThere is no bypass flag. Either the ISO's marker is restored by "
        "an explicit owner act and the run is re-registered, or the run is "
        "not registered — git history is the record (rule 15)."
    )


def prune_iso(
    iso: str, *, keep: int = KEEP_PER_ISO, dry_run: bool = False
) -> list[str]:
    """Enforce the top-``keep``-per-ISO retention rule across all three stores.

    Keeps the ``keep`` newest runs for ``iso`` (by date, then id) plus every
    protected id, and for each displaced run deletes its registry sidecar,
    ``runs/<id>.js`` payload and mapped ``results/calibration/<bundle>/`` dir
    together. A bundle shared by a surviving sidecar is left in place (only its
    orphaned sidecar/payload go). Returns the pruned ids; caller stages the
    deletions with the rest of the commit.
    """
    protected = _protected_run_ids()
    entries: list[tuple[str, str, dict, Path]] = []
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if rec.get("iso") != iso:
            continue
        entries.append((rec.get("date", ""), rec.get("id", path.stem), rec, path))
    # Newest first (date, then id); the oldest beyond the cap fall off the end.
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)

    to_prune = [
        (rid, rec, sidecar)
        for _, rid, rec, sidecar in entries[keep:]
        if rid not in protected
    ]
    pruned_ids = {rid for rid, _, _ in to_prune}
    # Bundle paths still referenced by any run that is NOT being pruned — never
    # delete a directory another sidecar still points at.
    kept_bundles: set[Path] = set()
    for path in REGISTRY_DIR.glob("*.json"):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if rec.get("id", path.stem) in pruned_ids:
            continue
        b = _bundle_dir(rec)
        if b is not None:
            kept_bundles.add(b.resolve())

    pruned: list[str] = []
    for rid, rec, sidecar in to_prune:
        payload = RUNS_DIR / f"{rid}.js"
        bundle = _bundle_dir(rec)
        drop_bundle = (
            bundle if (bundle and bundle.resolve() not in kept_bundles) else None
        )
        targets = [sidecar, payload] + ([drop_bundle] if drop_bundle else [])
        existing = [t for t in targets if t.exists()]
        note = " [dry-run]" if dry_run else ""
        print(
            f"  prune {rid}: "
            + (
                ", ".join(str(t.relative_to(REPO)) for t in existing)
                or "(nothing on disk)"
            )
            + note
        )
        if not dry_run:
            sidecar.unlink(missing_ok=True)
            payload.unlink(missing_ok=True)
            if drop_bundle and drop_bundle.exists():
                shutil.rmtree(drop_bundle)
        pruned.append(rid)
    return pruned


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--label", required=True, help="Dashboard display label / shorthand source."
    )
    ap.add_argument(
        "--bundle", required=True, help="Bundle dir, e.g. results/calibration/<name>."
    )
    ap.add_argument(
        "--no-prune",
        action="store_true",
        help="Skip the top-15-per-ISO retention sweep after registering.",
    )
    ap.add_argument(
        "--keep-per-iso",
        type=int,
        default=KEEP_PER_ISO,
        help=f"Retention cap per ISO (default {KEEP_PER_ISO}).",
    )
    args = ap.parse_args()

    bundle = resolve_bundle(args.bundle)
    if not (bundle / "meta.json").exists():
        sys.exit(f"bundle {bundle} is missing meta.json; nothing to register.")

    # Derive the full manifest entry exactly as render_backcast.generate does,
    # so the sidecar id matches the runs/<id>.js it writes and build_manifest
    # can list the run without ever opening the bundle.
    entry = rb.manifest_entry(args.label, bundle)
    rid, iso = entry["id"], entry["iso"]

    # Rule 22 / R-AZ: re-check the tier marker HERE, at the seam where the
    # run's solve years become a committed sidecar — before anything is
    # written, so a refused registration leaves no artifact behind.
    enforce_registration_marker_gate(iso, entry.get("years") or [])

    # Store the bundle path relative to the repo root so the sidecar is portable
    # across checkouts (CI clones to a different absolute path).
    try:
        rel_bundle = str(bundle.resolve().relative_to(REPO))
    except ValueError:
        rel_bundle = str(bundle)

    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    sidecar = REGISTRY_DIR / f"{rid}.json"
    sidecar.write_text(json.dumps({**entry, "bundle": rel_bundle}, indent=2) + "\n")

    # Render this single run: writes its runs/<id>.js + the bench/<ISO>/<year>
    # parts for its years, and refreshes the LOCAL preview manifest/benchmark.
    # Commit the bundle, the sidecar, runs/<id>.js and any changed bench parts
    # — never the shared manifest.js/benchmark.js (deploy-workflow-owned).
    rb.generate([(args.label, bundle)])

    print(f"registered {rid!r} (iso={iso}, bundle={rel_bundle})")
    print(f"RUN_ID={rid}")

    # Re-determination trigger (docs/calibration-determination-rubric.md §6):
    # registering a run re-runs the scorer on its freshly-written committed
    # artifacts, so every registered run prints its calibration determination.
    # Also writes the plaintext metrics.json sidecar (G-49,
    # docs/verifying-dashboard-numbers.md) into the bundle so a verifier can
    # read the headline scored metrics without decoding runs/<id>.js.
    # Best-effort — a scorer error must never block registration.
    try:
        from scripts import calibration_verdict as cv

        verdict = cv.determine(rid)
        print(cv.headline(verdict))
        metrics_path = cv.write_metrics_sidecar(bundle, verdict)
        print(f"wrote {metrics_path.relative_to(REPO)}")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"determination: unavailable ({exc})")

    # Retention: enforce the top-15-per-ISO cap for the ISO we just registered
    # into, deleting the sidecar + payload + bundle of any displaced oldest run
    # together (see KEEP_PER_ISO / prune_iso). Keepers and ablation-referenced
    # twins are never pruned. The caller stages the deletions with the commit.
    if not args.no_prune:
        pruned = prune_iso(iso, keep=args.keep_per_iso)
        if pruned:
            print(
                f"pruned {len(pruned)} run(s) beyond top-{args.keep_per_iso} "
                f"{iso} retention: {pruned}"
            )


if __name__ == "__main__":
    main()
