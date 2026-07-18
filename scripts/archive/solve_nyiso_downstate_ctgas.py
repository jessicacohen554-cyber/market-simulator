"""One-delta gate solve: nyiso-41 keeper config at HEAD + the downstate CT
interruptible-gas premium (nyiso_downstate_ct_gas_basis), all 3 years, one
bundle. Replays the keeper meta.json (so it inherits HEAD's de-leaked offer
curve, exactly like nyiso-48) and adds ONLY nyiso_downstate_ct_gas_basis=True as
a first-class solve_and_persist kwarg (recorded in the new meta.json, so the run
is reproducible from its bundle — the nyiso-48 reproducibility lesson)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "nyiso41_hubprices"
OUT = REPO / "results" / "calibration" / "nyiso50_downstate_ctgas"


def main() -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = OUT
    # Enable the mechanism via the generic prb_overrides config-override channel
    # (run_calibration.run_year applies it with config.with_overrides), the same
    # path replay_keeper --set uses — so no bespoke solve_and_persist plumbing is
    # needed. Reproduces identically:
    #   replay_keeper.py results/calibration/nyiso41_hubprices --out-dir <dir> \
    #       --set nyiso_downstate_ct_gas_basis=true
    kwargs.setdefault("prb_overrides", {})["nyiso_downstate_ct_gas_basis"] = True
    kwargs["note"] = (
        "nyiso-41 keeper config at HEAD (de-leaked offer curve, = nyiso-48 "
        "baseline) + the NYISO downstate CT interruptible city-gate gas premium "
        "(nyiso_downstate_ct_gas_basis): each NYC/Long Island CT_PEAKER unit's "
        "delivered gas lifted by the measured monthly LDC city-gate premium (EIA "
        "NG N3050NY3 - N3045NY3, floored 0), the rule-13 delivered-fuel structural "
        "fix for the B-NYI-1 de-leak CT_PEAKER over-run (issue #1344). One-delta "
        "vs nyiso-48."
    )
    print(
        f"solving {OUT.name}: nyiso-41 config + downstate CT gas premium, "
        f"years {kwargs['years']}"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
