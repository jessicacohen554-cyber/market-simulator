"""ERCOT-67 rule-16 throwaway ladder: measured thermal availability on the ercot66 base.

The May-2024/2025 (and Nov/Apr-2024) broad under-pricing lane, owner-opened
2026-07-15 ("prob outages we're maybe not capturing"). The record already
half-answers it: ERCOT-57 measured the statistical availability stack running
+1.5-4.1 GW too LOOSE across May 2-16 2024 and its measured rescale
(`ercot_thermal_dam_availability`) CURED May-2024 (-33.2% -> -1.6%) — but
collapsed summer-2023 (C3a -45.4%), whose fit rode the phantom TIGHTNESS
compensating for missing committed-state structure and the storage
under-discharge (the ERCOT-58 joint round's +2.4 GW binding-regime excess,
leading component: storage). Since then BOTH compensations gained real
structure: the ERCOT-63 gas commitment bridge and the ERCOT-66 measured
storage-capability re-basis (now the keeper). This ladder re-probes the
measured availability on that base:

* ``keeper``     — zero-delta reconstruction of the promoted ercot66 keeper
                   (2026-07-15-ercot66-storage-rebasis) from its meta.json.
* ``thermavail`` — + ercot_thermal_dam_availability=True (the ERCOT-57
                   measured class-day CC_REGULAR/CT_PEAKER rescale, CSV
                   re-derived 2026-07-15 with the Nov-Dec-2025 coverage).

Isolation runs are SINGLE-YEAR throwaways: 2024 first (the May-cure test on
the new base), then 2023 (the collapse test). Score with
``_ercot63_c3_proxy.py`` + monthly anatomy; promotion decisions only ever
from a full-span 2023-2025 bundle (rule 16).

EXPLICITLY-LABELLED DIAGNOSTIC (rules 13/16): single-year, NEVER registered,
never a keeper config; bundles are throwaways.

Usage::

    python scripts/probes/_ercot67_ladder_probe.py RUNG --years 2024
    # RUNG in {keeper, thermavail}
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
# The promoted ERCOT keeper (2026-07-15-ercot66-storage-rebasis).
KEEPER = ROOT / "ercot66_storage_rebasis_measuredas"

RUNGS = {
    "keeper": {},
    "thermavail": {"ercot_thermal_dam_availability": True},
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rung", choices=sorted(RUNGS))
    ap.add_argument("--years", type=int, nargs="+", default=[2024])
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    kwargs.update(RUNGS[args.rung])
    kwargs["note"] = (
        f"ercot67 rule-16 throwaway (NEVER register): '{args.rung}' rung — "
        "ercot66-storage-rebasis keeper reconstructed from meta.json + deltas "
        f"{RUNGS[args.rung]!r}. Tests the measured class-day thermal "
        "availability (ERCOT-57 rescale) on the post-bridge post-storage-"
        "re-basis base against the May-2024/2025 under-pricing exposure."
    )

    ytag = "_".join(str(y) for y in args.years)
    out = ROOT / f"ercot67_{args.rung}_{ytag}"
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
