"""ERCOT-66 rule-16 throwaway ladder: storage capability re-basis + endogenous split, 2023.

The summer-availability audit (docs/DIAGNOSIS-ercot-summer-availability-audit-
2026-07.md) exonerated the outage overlay and located the phantom-evening
defect in the storage capability basis: the EIA-860 COD-ramped battery fleet
runs ~2 GW below ERCOT's registered non-OUT PWRSTR HSL in both summers, and
the measured AS-award subtraction removes another ~3-3.5 GW at the scarcity
margin. The ladder isolates the two levers against the byte-faithful
ercot63-gas-bridge keeper reconstruction:

* ``keeper``           — zero-delta ercot63_gas_bridge reconstruction from its
                         meta.json (leg 0). Expect C3a +3.1 %, C3b 0.131,
                         C3c 171 h, storage 0.74 TWh (the ERCOT-63 row).
* ``storagecap``       — + ercot_storage_capability_measured=True (leg A: the
                         disclosure storage-MW re-basis alone; M1/M2/deploy
                         unchanged — the award still subtracts, from the
                         bigger measured cap).
* ``endog``            — + ercot_storage_as_endogenous=True (leg B: the LP
                         chooses the energy-vs-AS split; M1 cap-subtraction &
                         M2 requirement-netting auto-gate OFF;
                         ercot_storage_as_deployment must be explicitly
                         cleared — scenarios.__post_init__ forbids the pair;
                         the post-solve additive ORDC adder gates OFF so C3c
                         is fed by the co-opt's internalized scarcity + the
                         measured RTORDPA overlay the keeper carries).
* ``storagecap_endog`` — both (the ERCOT-66 candidate recipe).

Score with ``_ercot63_c3_proxy.py`` / ``_ercot63_anatomy.py`` plus this
lane's summer-window checks (Aug 18-20 2024 / Jul 30-31 + Aug 18-25 2025 —
full-span only), and validate the endogenous split against the measured
award via the bundle's ``storage_as.parquet`` honesty gate.

EXPLICITLY-LABELLED DIAGNOSTIC (rules 13/16): 2023-only, NEVER registered,
never a keeper config; bundles are throwaways.

Usage::

    python scripts/probes/_ercot66_ladder_probe.py RUNG [--years 2023]
    # RUNG in {keeper, storagecap, endog, storagecap_endog}
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ercot61_stgas_drag_probe import build_kwargs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
# The promoted ERCOT keeper (2026-07-12-ercot63-gas-bridge) bundle — its
# meta.json post-dates the ERCOT-63 meta-writer fix, so the reconstruction
# is complete.
KEEPER = ROOT / "ercot63_gas_bridge"

# ercot_storage_as_deployment=False on the endogenous rungs is REQUIRED, not
# stylistic: ScenarioConfig.__post_init__ raises on the pair (rule 19 — the
# measured-award deployment floor and the endogenous co-opt split both price
# the same energy-vs-AS choice), and under the endogenous flag M1
# (storage_as_commitment cap subtraction) and M2 (requirement netting /
# product credit) auto-gate off at their call sites.
RUNGS = {
    "keeper": {},
    "storagecap": {"ercot_storage_capability_measured": True},
    "endog": {
        "ercot_storage_as_endogenous": True,
        "ercot_storage_as_deployment": False,
    },
    "storagecap_endog": {
        "ercot_storage_capability_measured": True,
        "ercot_storage_as_endogenous": True,
        "ercot_storage_as_deployment": False,
    },
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rung", choices=sorted(RUNGS))
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    kwargs.update(RUNGS[args.rung])
    kwargs["note"] = (
        f"ercot66 rule-16 throwaway (NEVER register): '{args.rung}' rung of "
        "the storage-capability/endogenous-split ladder — ercot63-gas-bridge "
        f"keeper reconstructed from meta.json + deltas {RUNGS[args.rung]!r}. "
        "Tests the 60-Day-disclosure storage-MW re-basis "
        "(ercot_storage_capability_measured) and the endogenous energy-vs-AS "
        "co-opt split (ercot_storage_as_endogenous) against the summer "
        "phantom-evening windows."
    )

    out = ROOT / f"ercot66_{args.rung}_2023"
    out.mkdir(parents=True, exist_ok=True)
    solve_and_persist(
        args.years,
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        run_dir=out,
        **kwargs,
    )
    print(f"DONE -> {out}")


if __name__ == "__main__":
    main()
