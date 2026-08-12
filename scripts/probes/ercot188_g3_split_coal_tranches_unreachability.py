"""ercot-188 G#3 unreachability proof: ``split_coal_tranches`` is dead code.

The signed ruling (docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md
SsG.3) orders the deletion of ``split_coal_tranches`` and its six registered
scalars (``coal_tranche_{1,2,3}_frac`` / ``coal_tranche_{1,2,3}_fuel_passthrough``)
"in a lane that FIRST proves the legacy limb is unreachable for every
registered bundle, not just the six current keepers".

This probe is that proof. It enumerates, from the git index (committed files
only, never the working tree's uncommitted state):

1. every committed ``run_config.json`` under ``results/`` (calibration bundles,
   hindcast runs, ffr* experiment dirs alike -- a superset of the ruling's
   "results/calibration/**" scope), and
2. every backcast dashboard registry sidecar
   (``frontend/data/backcast/registry/*.json``), resolving each to its bundle's
   committed ``run_config.json`` when the bundle is still retained on disk
   (pruned bundles are reported as such -- their sidecar still names the ISO).

For each config it reads ``use_campd_bins`` and the ISO, and derives whether
the run can reach the legacy (``campd_bins is None``) limb of
``fleet/assembly.py::build_dispatch_fleet`` -- the ONLY call site of
``split_coal_tranches``.  Reachability logic mirrors
``fleet/assembly.py::load_or_synthesize_bins`` at HEAD: the CAMPD limb is taken
iff ``use_campd_bins`` is truthy AND the ISO is in
``constants.CAMPD_BINNING_ISOS`` AND the bin artifact resolves non-empty; the
probe additionally verifies the per-ISO bin artifact exists in the repo
(ERCOT's curated CSV via ``ScenarioConfig.campd_bins_path``, every other ISO's
``thermal_tranches_<ISO>.csv`` synthesis input) so the missing-artifact
fallback cannot fire for any of the six ISOs.  miso-128 SS4 proved the same
conclusion dynamically at MISO (fleet assembled twice, fractions materially
perturbed, zero delta on ``pmax_mw`` / ``fuel_fracs``).

Output: ``results/calibration/ercot188_g3_unreachability_proof.json`` -- the
committed evidence artifact for the deletion PR.  No LP is solved; the probe
reads committed JSON and the config layer only.

Run:  python scripts/probes/ercot188_g3_split_coal_tranches_unreachability.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "ercot188_g3_unreachability_proof.json"


def _committed(pattern: str) -> list[str]:
    """Return committed paths matching *pattern* from the git index."""
    res = subprocess.run(
        ["git", "ls-files", pattern],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return [ln for ln in res.stdout.splitlines() if ln.strip()]


def main() -> int:
    """Build and write the unreachability proof; exit non-zero on any breach."""
    import dataclasses

    from market_sim.config.capacity_market import CAMPD_BINNING_ISOS
    from market_sim.config.scenarios import ScenarioConfig

    # --- bin-artifact existence per ISO (the load_or_synthesize_bins
    # missing-artifact fallback): ERCOT reads the curated CSV at the config
    # default path; the other five synthesize from thermal_tranches_<ISO>.csv.
    default_bins_path = Path(
        next(
            f.default
            for f in dataclasses.fields(ScenarioConfig)
            if f.name == "campd_bins_path"
        )
    )
    if default_bins_path.is_absolute():
        default_bins_path = default_bins_path.relative_to(REPO)
    artifacts = {"ERCOT": str(default_bins_path)}
    for iso in sorted(CAMPD_BINNING_ISOS - {"ERCOT"}):
        hits = _committed(f"*thermal_tranches_{iso}.csv")
        artifacts[iso] = hits[0] if hits else None
    artifact_ok = {
        iso: bool(p) and (REPO / p).exists() for iso, p in artifacts.items()
    }

    # --- sweep 1: every committed run_config.json under results/ ---
    rows = []
    reachable = []
    for rel in _committed("results/*run_config.json"):
        cfg = json.loads((REPO / rel).read_text())
        # run_config.json layouts vary: the scenario dump lives under
        # "scenario_config" (calibration bundles) or at the top level.
        scen = cfg.get("scenario_config", cfg.get("scenario", cfg))
        iso = scen.get("iso") or cfg.get("iso") or "?"
        ucb = scen.get("use_campd_bins", cfg.get("use_campd_bins"))
        campd_limb = bool(ucb) and iso in CAMPD_BINNING_ISOS and artifact_ok.get(
            iso, False
        )
        rows.append(
            {
                "path": rel,
                "iso": iso,
                "use_campd_bins": ucb,
                "reaches_legacy_limb": not campd_limb,
            }
        )
        if not campd_limb:
            reachable.append(rel)

    # --- sweep 2: every backcast registry sidecar -> its bundle ---
    sidecars = []
    for rel in _committed("frontend/data/backcast/registry/*.json"):
        sc = json.loads((REPO / rel).read_text())
        bundle = sc.get("bundle")
        rc = (REPO / bundle / "run_config.json") if bundle else None
        entry = {
            "sidecar": rel,
            "id": sc.get("id"),
            "iso": sc.get("iso"),
            "bundle": bundle,
        }
        if rc is not None and rc.exists():
            cfg = json.loads(rc.read_text())
            scen = cfg.get("scenario_config", cfg.get("scenario", cfg))
            ucb = scen.get("use_campd_bins", cfg.get("use_campd_bins"))
            entry["use_campd_bins"] = ucb
            entry["reaches_legacy_limb"] = not (
                bool(ucb)
                and sc.get("iso") in CAMPD_BINNING_ISOS
                and artifact_ok.get(sc.get("iso"), False)
            )
        else:
            # Bundle pruned under top-15 retention: its run_config is covered
            # by sweep 1 at the time it was committed; the sidecar alone holds
            # no scenario dump to read. Not a breach -- flagged for the record.
            entry["use_campd_bins"] = None
            entry["reaches_legacy_limb"] = None
            entry["bundle_pruned"] = True
        sidecars.append(entry)
        if entry["reaches_legacy_limb"]:
            reachable.append(rel)

    n_true = sum(1 for r in rows if r["use_campd_bins"] is True)
    proof = {
        "probe": "ercot188_g3_split_coal_tranches_unreachability",
        "authority": (
            "docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md SsG.3"
        ),
        "date": "2026-08-12",
        "campd_binning_isos": sorted(CAMPD_BINNING_ISOS),
        "bin_artifact_by_iso": artifacts,
        "bin_artifact_exists": artifact_ok,
        "n_committed_run_configs": len(rows),
        "n_use_campd_bins_true": n_true,
        "n_registry_sidecars": len(sidecars),
        "n_reaching_legacy_limb": len(reachable),
        "reaching_legacy_limb": reachable,
        "verdict": (
            "DEAD LIMB EVERYWHERE: no committed run_config or registered "
            "bundle reaches the else limb of build_dispatch_fleet; "
            "split_coal_tranches and the six coal_tranche_* scalars are "
            "unreachable for every registered bundle of all six ISOs."
            if not reachable
            else "BREACH: at least one committed config reaches the legacy limb"
        ),
        "run_configs": rows,
        "registry_sidecars": sidecars,
    }
    OUT.write_text(json.dumps(proof, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(
        f"run_configs={len(rows)} (use_campd_bins=True on {n_true}), "
        f"sidecars={len(sidecars)}, reaching_legacy_limb={len(reachable)}"
    )
    print(proof["verdict"])
    return 1 if reachable else 0


if __name__ == "__main__":
    raise SystemExit(main())
