"""caiso-184 — solve one arm of the LP-capacity-basis A/B.

Pre-registered in ``results/calibration/PRECHECK-caiso184-capacity-basis-2026-08-08.md``
§8 (CONTROL). Both arms go through the SAME shipped replay path,
``run_calibration_full.run_replay_bundle``'s own recipe reconstruction
(``replay_keeper.build_kwargs`` over the keeper bundle's ``meta.json``) — never a
remembered CLI string — so the control reproduces the keeper by construction and the
treated arm differs from it by **exactly one kwarg**.

``--replay-bundle`` on the CLI ignores every other solve flag ("the bundle IS the
config"), which is correct for a data-delta A/B (caiso-183) but cannot express a
**config**-delta arm. This driver therefore rebuilds the identical kwargs and injects
the single override, so the delta is visible and auditable rather than smuggled through
a hand-typed flag list.

**The cache purge between arms is load-bearing** (caiso-183 §6): ``runner.py``
short-circuits on ``is_cached(iso, cache_key, year)``. Here the delta IS in
``ScenarioConfig``, so the cache key does move — but the purge is kept anyway and
distinctness is ASSERTED afterwards by ``_caiso183_arm_identity.check_arms_distinct``
(the hourly-signature check; caiso-180's derate-census check is invalid for an
input-only delta) rather than trusted.

Usage::

    python scripts/probes/_caiso184_solve_arm.py control
    python scripts/probes/_caiso184_solve_arm.py treated
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results" / "calibration" / "caiso183_b1_hourgrain"
ARMS = {
    "control": (
        REPO / "results" / "calibration" / "caiso184_c0_control",
        None,
        "caiso-184 ARM C0 CONTROL: the caiso-183-b1-hour keeper recipe replayed at "
        "THIS head with no config delta. Establishes the same-head noise floor "
        "before any treated delta is read (PRECHECK §8 CONTROL). Recipe rebuilt "
        "from the keeper bundle's own meta.json via replay_keeper.build_kwargs — "
        "never a remembered CLI string.",
    ),
    "treated": (
        REPO / "results" / "calibration" / "caiso184_c1_lpbasis",
        True,
        "caiso-184 ARM C1 TREATED: the caiso-183-b1-hour keeper recipe replayed at "
        "THIS head with ONE kwarg changed — unit_outage_lp_capacity_basis=True. The "
        "CAMPD unit-outage derate share is taken against the capacity the multiplier "
        "is applied to in the LP (fleet_to_bins' nameplate-raised CC bin) instead of "
        "the fleet's net-summer sum, restoring the same-basis invariant the extract "
        "deriver already declares. ZERO DOF, zero fitted scalars, monotone (a removed "
        "fraction can only fall). No data file changed; detection untouched.",
    ),
}


def main() -> None:
    """Solve the named arm and print the standard report."""
    if len(sys.argv) != 2 or sys.argv[1] not in ARMS:
        sys.exit(f"usage: {Path(sys.argv[0]).name} {{control|treated}}")
    arm = sys.argv[1]
    out_dir, override, note = ARMS[arm]

    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf

    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["hours"] = int(meta.get("hours", 8760))
    # Rule 22: 2023-2025 only, and the gate is asked rather than assumed.
    rcf.enforce_holdout_year_gate(kwargs["years"], kwargs["iso"], False)
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = out_dir
    kwargs["note"] = note
    if override is not None:
        kwargs["unit_outage_lp_capacity_basis"] = override

    # Purge the ISO's solve cache so no arm can inherit the other's parquet.
    cache = REPO / "results" / kwargs["iso"]
    if cache.exists():
        shutil.rmtree(cache)
        print(f"purged solve cache {cache.relative_to(REPO)}")

    print(f"=== caiso-184 ARM {arm.upper()} -> {out_dir.relative_to(REPO)}")
    print(f"    years={kwargs['years']}  delta=unit_outage_lp_capacity_basis={override}")
    run_dir = rcf.solve_and_persist(**kwargs)
    rcf.report_run(run_dir)


if __name__ == "__main__":
    main()
