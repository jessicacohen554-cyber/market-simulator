"""neiso-89 — replay a keeper with CROSS-YEAR WARM-START ON, as the CLI solves it.

THE HYPOTHESIS THIS TESTS. ``scripts/replay_keeper.py`` pins
``MARKET_SIM_WARMSTART_XYEAR=0`` before importing the solve core, on the stated
grounds that cross-year warm-start is *"basis-neutral on the calibration path
(objective/prices/total-gen bit-identical)"* and only *"reshuffles marginal-tie
dispatch by ~0.003%"*. But ``run_calibration.py::main`` sets that same variable
to ``"1"`` — the calibration CLI's default — and the CLI is how every committed
keeper was actually solved. So a keeper is SOLVED with the gate ON and REPLAYED
with it OFF, and if the neutrality claim is wrong the replay cannot reproduce
the bundle.

That is the candidate cause of the NEISO keeper's 2025 non-reproduction
(neiso-87 §4.0, owner decision D-88.3). This probe removes the pin — and
nothing else — so the two states can be compared directly.

``pipeline.solve.run_energy_solve`` reads the variable at CALL time, not at
import, so re-setting it after importing ``replay_keeper`` is sufficient and no
patching of the driver is required.

Rule 16: a diagnostic probe. Its output is never registered as a keeper.
Rule 22: in-sample years only (2023-2025).

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_neiso89_replay_xyear.py \\
        results/calibration/neiso83_ca1reclass_B \\
        --out-dir /home/user/bisect-out/HEAD_XYEAR_CHAIN
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

# Import the driver first: it pins the gate OFF at module scope. Then flip it
# back ON, which is the single variable under test.
from scripts import replay_keeper  # noqa: E402

os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "1"


def main() -> None:
    """Run ``replay_keeper.main`` with the cross-year gate forced ON."""
    assert os.environ["MARKET_SIM_WARMSTART_XYEAR"] == "1"
    print("[neiso-89] MARKET_SIM_WARMSTART_XYEAR=1 (CLI default), replay pin removed")
    replay_keeper.main()


if __name__ == "__main__":
    main()
