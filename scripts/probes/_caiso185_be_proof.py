"""caiso-185 P0-4 — byte-equivalence and rule-25 scope proof (ercot-174 BE discipline).

PRECHECK-caiso185 §6. Three legs:

* **BE-1 / G-SIXISO** — no ISO other than CAISO can be reached. This session adds **no
  ScenarioConfig field and modifies no file under ``src/``**, so the only solve-path
  difference available to it is the value of the pre-existing default-``False``
  ``cc_capacity_reconcile``. The leg is therefore proven two ways: (a) a git diff over
  ``src/`` must be EMPTY, and (b) for each of the six ISOs the flag's default must be
  ``False`` on a freshly-built config, so an unarmed ISO reads no table at all.
* **BE-2 / rule 25** — ``cc_capacity_reconcile_path`` defaults to ``None`` and resolves
  per-ISO in ``ScenarioConfig.__post_init__``. Bar: each ISO's resolved path basename
  carries **that ISO's own name**, the six paths are pairwise distinct, and arming CAISO
  leaves every other ISO's resolved path unchanged. This is what stops one ISO's
  demonstrated peaks reaching another's fleet.
* **BE-3** — no data file is re-derived or rewritten: a sha256 ledger over all six
  ``cc_capacity_reconcile_*.csv``, the CAISO CAMPD unit-outage extract, and the EIA-860
  operable generator table.

Usage::

    python scripts/probes/_caiso185_be_proof.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import (  # noqa: E402
    EIA_860_DIR,
    cc_capacity_reconcile_path,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.outages import unit_outage_csv_for_iso  # noqa: E402

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")
OUT = REPO / "results" / "calibration" / "_caiso185_be_proof.json"


def _sha(path: Path) -> str | None:
    """sha256 of a file, or ``None`` when it is absent."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """Run BE-1 / BE-2 / BE-3 and write the record."""
    src_diff = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", "src/"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()

    be1: dict[str, dict] = {}
    be2: dict[str, dict] = {}
    for iso in ISOS:
        cfg = ScenarioConfig(iso=iso)
        armed = ScenarioConfig(iso=iso, cc_capacity_reconcile=True)
        be1[iso] = {
            "default_cc_capacity_reconcile": bool(cfg.cc_capacity_reconcile),
            "cache_key_default": cfg.cache_key(),
            "cache_key_armed": armed.cache_key(),
            "key_moves_when_armed": cfg.cache_key() != armed.cache_key(),
        }
        resolved = Path(cfg.cc_capacity_reconcile_path)
        be2[iso] = {
            "resolved_path": str(resolved.relative_to(REPO)),
            "basename": resolved.name,
            "carries_own_iso_name": iso in resolved.name,
            "exists": resolved.exists(),
            "matches_paths_helper": resolved == cc_capacity_reconcile_path(iso),
        }

    # Arming CAISO must not move any other ISO's resolved path.
    caiso_armed = ScenarioConfig(iso="CAISO", cc_capacity_reconcile=True)
    cross = {
        iso: ScenarioConfig(iso=iso).cc_capacity_reconcile_path
        for iso in ISOS
        if iso != "CAISO"
    }
    cross_stable = all(
        Path(p) == cc_capacity_reconcile_path(iso) for iso, p in cross.items()
    )

    be3 = {
        **{
            f"cc_capacity_reconcile_{iso}.csv": _sha(cc_capacity_reconcile_path(iso))
            for iso in ISOS
        },
        "campd_unit_outages_CAISO": _sha(Path(unit_outage_csv_for_iso("CAISO"))),
        "eia860_generator_operable.parquet": _sha(
            EIA_860_DIR / "eia860_generator_operable.parquet"
        ),
    }

    out = {
        "be1_src_diff_empty": src_diff == "",
        "be1_src_diff": src_diff,
        "be1_per_iso": be1,
        "be1_pass": src_diff == ""
        and all(not v["default_cc_capacity_reconcile"] for v in be1.values()),
        "be2_per_iso": be2,
        "be2_caiso_armed_path": str(
            Path(caiso_armed.cc_capacity_reconcile_path).relative_to(REPO)
        ),
        "be2_other_isos_paths_stable": cross_stable,
        "be2_paths_distinct": len({v["resolved_path"] for v in be2.values()})
        == len(ISOS),
        "be2_pass": all(v["carries_own_iso_name"] for v in be2.values())
        and all(v["matches_paths_helper"] for v in be2.values())
        and cross_stable
        and len({v["resolved_path"] for v in be2.values()}) == len(ISOS),
        "be3_sha256": be3,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
