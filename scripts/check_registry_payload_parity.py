"""CI gate: registry sidecars and run payloads must be in 1:1 parity.

`scripts/build_manifest.py` silently skips a `registry/<id>.json` sidecar
whose `runs/<id>.js` payload is absent (the "half-synced checkout" guard) —
that is the right behavior for an incomplete local checkout, but it means a
sidecar pushed WITHOUT its payload is invisible in the Run Explorer with no
error anywhere. This happened in practice: several probes (nyiso-54, nyiso-58,
pjm-84, pjm-85, caiso-66) were registered sidecar-only and never rendered
(2026-07 loading-issue investigation). This script makes that failure loud
instead of silent, and additionally catches dangling `ablation_twin` /
`ablation_of` cross-references (a link to a sidecar-only or nonexistent run).

It checks BOTH directions of the parity so retention can never leave a store
behind:

* sidecar -> payload: a `registry/<id>.json` with no `runs/<id>.js` (above).
* payload -> sidecar: a `runs/<id>.js` **orphan** with no `registry/<id>.json`.
  These arise when a sidecar is pruned without its payload — the exact drift
  `dashboard_add_run.py`'s three-store retention exists to prevent — leaving a
  dead payload committed forever (it is never rendered, since only registered
  runs appear in the manifest).

Since the Class-E retention rule's adoption (2026-08-16, closing BLOAT-2 —
rule text: `frontend/data/backcast/keepers/README.md`) it also sweeps the
THIRD retention store, per the rule's point 4:

* bundle -> sidecar: a top-level `results/calibration/<bundle>/` DIRECTORY
  that no retained registry sidecar's `bundle` field maps and that is not
  otherwise keep-required (`check_bundle_retention`). Retention
  (`dashboard_add_run.prune_iso`) deletes sidecar + payload + bundle
  together, so an unmapped bundle dir is the last drift channel — dead solve
  output committed forever with nothing rendering or scoring it. The rule
  asked for a quarterly sweep; living in this always-on CI gate is a strict
  superset of that cadence.

It also asserts the namespace BOUNDARY (audit FR-24, added by FFR-1D): a
forecast-family run — T1-F / T1-X / T1-H / crossover / CES-POC / readiness —
must never be registered into the backcast registry. Those runs belong to the
separate forecast namespace (`frontend/data/forecast/**`, registered via
`scripts/register_forecast_run.py`), and CLAUDE.md rule 15 plus forecast plan
§7.5 say the two never mix: a forecast run in the backcast registry would put a
2026-2050 solve in front of `audit_keepers` and the rule-22 quarantine gates,
which reason about calibration years. The check reads only the backcast entry's
OWN fields — it never opens the forecast namespace, so the backcast gates stay
blind to it exactly as §7.5 requires.

Usage: ``python scripts/check_registry_payload_parity.py`` (exit 1 on any gap).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import keeper_store  # noqa: E402  (after sys.path insert)
from scripts.lib.known_unsynced_keepers import (  # noqa: E402
    UNSYNCED_RUN_PAYLOADS,
)

REGISTRY_DIR = ba.REGISTRY
RUNS_DIR = ba.RUNS

# Class-E retention rule point 4 (keepers/README.md): keep-required bundle
# dirs that legitimately hold NO retained sidecar mapping. Admissible classes
# are the rule's immunity set when a bundle outlives its sidecar — a
# `keeper_at_declaration` or structural-prior (STATMODE_PROBE_RUNS) bundle
# whose registry entry was retired — which is the EXCEPTION: the prune
# immunity (`dashboard_add_run._protected_run_ids`) normally keeps those
# sidecars alive, so their bundles are mapped the ordinary way. Every entry
# names the top-level dir and carries a reason comment; a stale entry is a
# re-armable hole in the gate (delete it when the bundle goes). Empty at
# adoption (2026-08-16): every non-`_` dir on the tree was sidecar-mapped.
KEEP_REQUIRED_UNMAPPED_BUNDLES: frozenset[str] = frozenset(
    {
        # miso-170b independent-replication evidence (2026-08-19): this pair
        # was solved concurrently with — and verified BIT-IDENTICAL to — the
        # registered miso170_membership_A/B (probe --identity, max|diff|=0 on
        # every scored sidecar of every year). Their duplicate registrations
        # were reconciled away in favour of the canonical ids, but the bundles
        # are cited by the 2026-08-19-miso-170-sitegrain keeper's promotion
        # note and RESULT-miso170b-sitegrain-execution-2026-08-19.md as the
        # replication record (which also proves the intervening merges
        # MISO-inert), so they legitimately outlive their sidecars.
        "miso170_layup_A",
        "miso170_layup_B",
    }
)

# Namespace-boundary vocabulary (FR-24). `kind`/`mode` are FORECAST-sidecar
# fields — a backcast registry entry has neither — so their presence with a
# forecast value is a registration that went to the wrong namespace.
FORECAST_KINDS = frozenset(
    {"t1f", "t1x", "t1h", "crossover", "hindcast", "ces-poc", "adequacy", "readiness"}
)
# Result-tree roots the forecast/hindcast harnesses write to. A backcast bundle
# lives under results/calibration/.
FORECAST_BUNDLE_PREFIXES = (
    "results/hindcast/",
    "results/full-horizon/",
    "results/crossover/",
    "results/ff-",
    "results/ces-",
)
BACKCAST_RUNS_PREFIX = "frontend/data/backcast/runs/"


def check_namespace_boundary(rid: str, rec: dict) -> list[str]:
    """Return problems if ``rec`` is a forecast-family run in the backcast registry.

    Args:
        rid: The run id.
        rec: The registry sidecar's parsed contents.

    Returns:
        A list of human-readable problems; empty when the entry is a backcast
        registration.
    """
    problems: list[str] = []
    remedy = (
        "Forecast-family runs register on the forecast namespace via "
        "scripts/register_forecast_run.py (CLAUDE.md rule 15; forecast plan "
        "§7.5 — the backcast gates must never see a forecast run)."
    )
    kind = rec.get("kind") or (rec.get("meta") or {}).get("kind")
    mode = rec.get("mode") or (rec.get("meta") or {}).get("mode")
    if kind in FORECAST_KINDS:
        problems.append(f"{rid}: kind={kind!r} is a FORECAST run kind. {remedy}")
    if mode == "forecast":
        problems.append(f"{rid}: mode='forecast' in the BACKCAST registry. {remedy}")
    bundle = str(rec.get("bundle") or "")
    if bundle.startswith(FORECAST_BUNDLE_PREFIXES):
        problems.append(
            f"{rid}: bundle {bundle!r} is under a forecast/hindcast results "
            f"root. {remedy}"
        )
    file_ref = str(rec.get("file") or "")
    if file_ref and not file_ref.startswith(BACKCAST_RUNS_PREFIX):
        problems.append(
            f"{rid}: file {file_ref!r} points outside "
            f"{BACKCAST_RUNS_PREFIX} — a backcast payload lives there. {remedy}"
        )
    return problems


def check_bundle_retention(
    sidecars: dict[str, dict], *, repo: Path | None = None
) -> tuple[list[str], int]:
    """Class-E retention rule point 4: sweep `results/calibration/` bundle dirs.

    Fails any top-level DIRECTORY under `results/calibration/` that no
    retained sidecar's `bundle` field maps and that is not keep-required
    (rule text: `frontend/data/backcast/keepers/README.md`). Keep-required
    carve-outs, in the order tested:

    * `_`-prefixed dirs — the §5.2 working/archive dirs
      (`docs/bloat-removal-plan-2026-08.md` §5.2, citation-checked KEEP);
      never run bundles.
    * dirs a `results/regression-goldens/*/manifest.json` capture record
      references in a `keepers.<ISO>.bundle` field.
    * the documented `KEEP_REQUIRED_UNMAPPED_BUNDLES` allowlist (a
      keep-required bundle that legitimately outlives its sidecar).

    Out of scope by construction: root-level loose records (files, not
    dirs), and the `results/hindcast/` / `results/regression-goldens/`
    roots (different trees). The current keeper, ablation-referenced and
    structural-prior bundles need no carve-out here — the prune immunity
    keeps their sidecars retained, so they are mapped the ordinary way.

    Args:
        sidecars: Parsed retained registry sidecars, keyed by run id.
        repo: Repo root override (tests); defaults to this checkout.

    Returns:
        ``(problems, swept)`` — human-readable failures, and how many bundle
        dirs the sweep examined. An absent `results/calibration/` (partial
        checkout) sweeps nothing and returns no problems, mirroring the
        RUNS_DIR guard.
    """
    repo = repo or REPO
    calib_root = repo / "results" / "calibration"
    goldens_root = repo / "results" / "regression-goldens"
    if not calib_root.is_dir():
        return [], 0

    mapped: set[str] = set()
    for rec in sidecars.values():
        b = ba.bundle_dir_for(rec, repo=repo, calib_root=calib_root)
        if b is None:
            continue  # no bundle field, or outside the root (safety guard)
        rel = b.resolve().relative_to(calib_root.resolve())
        if rel.parts:  # a sidecar may map a nested path; the dir is top-level
            mapped.add(rel.parts[0])

    golden_refs: set[str] = set()
    for manifest in sorted(goldens_root.glob("*/manifest.json")):
        try:
            doc = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            continue  # unreadable capture record never widens the carve-out
        for entry in (doc.get("keepers") or {}).values():
            raw = str((entry or {}).get("bundle") or "")
            parts = Path(raw).parts
            if parts[:2] == ("results", "calibration") and len(parts) > 2:
                golden_refs.add(parts[2])

    problems: list[str] = []
    swept = 0
    for path in sorted(p for p in calib_root.iterdir() if p.is_dir()):
        name = path.name
        if name.startswith("_"):
            continue
        swept += 1
        if name in mapped or name in golden_refs:
            continue
        if name in KEEP_REQUIRED_UNMAPPED_BUNDLES:
            continue
        problems.append(
            f"results/calibration/{name}: bundle dir maps to no retained "
            f"sidecar `bundle` field and is not keep-required — dead solve "
            f"output (Class-E retention rule point 4, "
            f"frontend/data/backcast/keepers/README.md). Either register "
            f"it, prune it (dashboard_add_run.prune_iso deletes the three "
            f"stores together), or record why it must outlive its sidecar "
            f"in KEEP_REQUIRED_UNMAPPED_BUNDLES."
        )
    return problems, swept


def main() -> int:
    problems: list[str] = []
    # Pre-existing sidecar-only registrations whose payloads were never
    # committed (scripts/lib/known_unsynced_keepers.py). Reported as tracked
    # warnings so this gate stays green for unrelated PRs; any OTHER missing
    # payload still fails. Not a blanket ignore.
    warnings: list[str] = []
    sidecars: dict[str, dict] = {}
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: invalid JSON ({exc})")
            continue
        rid = rec.get("id", path.stem)
        sidecars[rid] = rec
        problems.extend(check_namespace_boundary(rid, rec))
        if not (RUNS_DIR / f"{rid}.js").exists():
            msg = (
                f"{path.name}: registry sidecar has no matching "
                f"runs/{rid}.js payload — invisible in the Run Explorer"
            )
            (warnings if rid in UNSYNCED_RUN_PAYLOADS else problems).append(msg)

    # payload -> sidecar: an orphan runs/<id>.js with no registry sidecar. A
    # sidecar pruned without its payload leaves this dead file committed
    # forever; retention (dashboard_add_run.prune_iso) deletes both together, so
    # any orphan here is a parity break to fix.
    if RUNS_DIR.exists():
        for path in sorted(RUNS_DIR.glob("*.js")):
            rid = path.stem
            if rid not in sidecars:
                problems.append(
                    f"runs/{path.name}: orphan payload has no registry/{rid}.json "
                    f"sidecar — dead file, never rendered"
                )

    for rid, rec in sidecars.items():
        for field in ("ablation_twin", "ablation_of"):
            ref = rec.get(field)
            if not ref or not ref.startswith("20"):  # skip prose placeholders
                continue
            if ref not in sidecars:
                problems.append(f"{rid}: {field} -> {ref!r} has no registry sidecar")
            elif not (RUNS_DIR / f"{ref}.js").exists():
                problems.append(
                    f"{rid}: {field} -> {ref!r} has a sidecar but no runs/{ref}.js payload"
                )

    for iso, rid in keeper_store.keeper_ids().items():
        if rid not in sidecars:
            problems.append(
                f"keepers/{iso}.json: keeper {rid!r} has no registry sidecar"
            )
        elif not (RUNS_DIR / f"{rid}.js").exists():
            msg = f"keepers/{iso}.json: keeper {rid!r} has no runs/{rid}.js payload"
            (warnings if rid in UNSYNCED_RUN_PAYLOADS else problems).append(msg)

    # bundle -> sidecar (Class-E retention rule point 4).
    bundle_problems, swept_bundles = check_bundle_retention(sidecars)
    problems.extend(bundle_problems)

    if warnings:
        print(
            "registry/payload parity: known-unsynced runs (tracked, not a gate "
            "failure — see scripts/lib/known_unsynced_keepers.py):",
            file=sys.stderr,
        )
        for w in warnings:
            print(f"  ! {w}", file=sys.stderr)

    if problems:
        print("registry/payload parity FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print(
        f"registry/payload parity OK ({len(sidecars)} runs checked, "
        f"{swept_bundles} bundle dirs swept, "
        f"{len(warnings)} known-unsynced tolerated)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
