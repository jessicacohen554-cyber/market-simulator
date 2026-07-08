"""Full-keeper A/B probe: NYISO temperature-dependent derate, 2023-2025.

Reproduces the 2026-07-07-nyiso-56-measured-zonal keeper's exact recorded
solve kwargs (read byte-faithfully from its own meta.json via
``replay_keeper.build_kwargs`` -- the same reliable path ``replay_keeper.py``
and ``run_nyiso56_ablation_twin.py`` use, rather than hand-translating flags
through the CLI) for all three train years in one bundle (rule 16), flipping
only ``temp_dependent_derate`` on -- the flat EIA-860 net-summer /
`_SUMMER_CLASS_DERATE` capacity treatment vs the new per-class dry-bulb
temperature curve (fleet.generators_to_fleet_arrays).

Full three-year keeper rerun per
docs/handoffs/temp-derate-keeper-rerun-playbook-2026-07.md -- registered as a
dashboard PROBE (nyiso-58), never a keeper promotion.

Usage: python scripts/probes/_nyiso_tempderate_ab.py {main|ablation}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

ROOT = REPO / "results" / "calibration"
KEEPER = ROOT / "nyiso56_measuredshares"
MAIN_OUT = ROOT / "nyiso58_tempderate"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [2023, 2024, 2025]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    out = ROOT / (MAIN_OUT.name + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)
    kwargs["run_dir"] = out
    kwargs["temp_dependent_derate"] = True
    kwargs["zero_forcing_ablation"] = ablate
    kwargs["ablation_of"] = MAIN_OUT.name if ablate else None
    kwargs["note"] = (
        f"temp-derate full-keeper {mode} -- 2026-07-07-nyiso-56-measured-zonal "
        "config (byte-faithful replay via replay_keeper.build_kwargs) + "
        "temp_dependent_derate=True, 2023-2025"
    )
    print(f"solving {out.name} years {kwargs['years']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"DONE {mode} -> {run_dir}")


if __name__ == "__main__":
    main(sys.argv[1])
