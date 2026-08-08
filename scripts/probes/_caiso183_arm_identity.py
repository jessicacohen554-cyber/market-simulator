"""caiso-183 ARM B: arm identity, sha ladder, DOF ledger and scoring.

Pre-registered in ``results/calibration/PRECHECK-caiso183-hedge-grain-2026-08-08.md``
§7. This is a thin driver over the **REUSED** ``_caiso180_arm_identity``
instrument — the PRECHECK requires reuse, not re-implementation, so the L1/L2/L3
``scenario_config`` split, the sha-ladder construction, the DOF-ledger assertion
and the rubric-v3.1 rescoring are all the caiso-180 code, pointed at this
session's two arms.

Its **§3a leg-2 ordering gate stays WITHDRAWN AS MALFORMED** (window count is not
envelope depth) and is not reinstated here.

Two arms, one delta:

* **B0 CONTROL** — the keeper recipe on the COMMITTED day-grain envelope.
  caiso-180 and caiso-181 both measured same-head drift at exactly ``$0.000``;
  if this arm does not reproduce the keeper to the cent, THAT is the finding and
  B1's numbers are not interpretable.
* **B1 TREATED** — the same recipe on the REPAIRED hour-grain envelope.

**The cache purge between arms is load-bearing.** ``runner.py`` short-circuits on
``is_cached(iso, cache_key, year)`` and ``cache_key`` hashes ``ScenarioConfig``
only — the outage extract's bytes are NOT in it. B0 and B1 share a recipe, so
without purging ``results/CAISO`` between them B1 would silently load B0's
parquet and read as a perfect no-op. This driver asserts the two arms are
distinct rather than trusting that the purge happened.

Usage::

    python scripts/probes/_caiso183_arm_identity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes import _caiso180_arm_identity as a180  # noqa: E402

YEARS = (2023, 2024, 2025)

#: PRECHECK §7. Both arms' envelope states; each value is a sha256 of the exact
#: bytes that arm's solve read.
ENVELOPES = {
    "B0": (
        "COMMITTED day-grain",
        "c4ded33df08de5927fd58fa7200320353e73ceedfeb0084586ffd2e32f93ff5e",
    ),
    "B1": (
        "REPAIRED hour-grain (--hour-grain)",
        "25360e90a9d11f32c293edf3224047da0d6fab447b551fac81b983e2da1166c6",
    ),
}

ARMS = {
    "B0": REPO / "results/calibration/caiso183_b0_control",
    "B1": REPO / "results/calibration/caiso183_b1_hourgrain",
}

SHA_LEDGER = REPO / "results/calibration/_caiso183_sha_ledger.json"
RUN_IDS = REPO / "results/calibration/_caiso183_run_ids.json"
OUT = REPO / "results/calibration/_caiso183_arm_identity.json"


def check_arms_distinct(present: dict[str, Path]) -> dict:
    """Assert B0 and B1 did not silently solve the same input.

    The hazard the solve cache creates (see the module docstring): identical
    metrics across both arms would mean the treated arm never re-solved. Uses
    the system hourlies rather than any scored criterion, so the check is about
    the SOLVE being distinct and never about which direction it moved.
    """
    import pandas as pd

    sig: dict[str, dict[int, float]] = {}
    for arm, bundle in present.items():
        per_year: dict[int, float] = {}
        for year in YEARS:
            f = bundle / "hourly" / f"system_{year}.parquet"
            if not f.exists():
                continue
            df = pd.read_parquet(f)
            col = "price" if "price" in df.columns else df.columns[0]
            per_year[year] = round(float(pd.to_numeric(df[col]).sum()), 6)
        sig[arm] = per_year
    if len(sig) == 2 and sig.get("B0") == sig.get("B1"):
        raise a180.Failure(
            "B0 and B1 produced an IDENTICAL hourly signature in every year — "
            "the treated arm almost certainly loaded B0's cached parquet "
            "(runner.is_cached keys on ScenarioConfig only, and the outage "
            "bytes are not in it). Purge results/CAISO between arms and re-run."
        )
    return {"hourly_signature": sig, "arms_distinct": True}


def main() -> None:
    """Run every reused check against this session's arms, then write the record."""
    # Point the REUSED instrument at this session's arms (PRECHECK §7).
    a180.ENVELOPES = ENVELOPES
    a180.ARMS = ARMS
    a180.SHA_LEDGER = SHA_LEDGER

    present = {a: b for a, b in ARMS.items() if (b / "run_config.json").exists()}
    if not present:
        sys.exit("no arm bundles found; solve B0 first.")

    rec: dict = {
        "session": "caiso-183",
        "precheck": "results/calibration/PRECHECK-caiso183-hedge-grain-2026-08-08.md",
        "reused_instrument": "scripts/probes/_caiso180_arm_identity.py",
        "withdrawn_gate": (
            "caiso-180 PRECHECK §3a leg 2 (the availability ORDERING inferred "
            "from window COUNT) stays WITHDRAWN AS MALFORMED and is NOT "
            "reinstated."
        ),
        "arms_present": sorted(present),
        "arms_expected": sorted(ARMS),
        "partial_audit": sorted(present) != sorted(ARMS),
    }
    rec["config_identity"] = a180.check_config_identity(present)
    rec["sha_ladder"] = a180.check_sha_ladder(present)
    rec["dof_ledger"] = a180.check_dof_ledger(present)
    rec["arm_distinctness"] = check_arms_distinct(present)
    if RUN_IDS.exists():
        rec["scoring"] = a180.score(json.loads(RUN_IDS.read_text()))

    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(json.dumps({k: v for k, v in rec.items() if k != "scoring"}, indent=1)[:2500])


if __name__ == "__main__":
    main()
