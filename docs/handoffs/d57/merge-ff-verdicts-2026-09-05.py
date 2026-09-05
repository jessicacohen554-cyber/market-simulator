"""capx D57: merge the two arm verdicts into the committed FF-2D snapshot and preserve D45-R's key.

``frontend/data/forecast/ff-verdicts.json`` is the COMMITTED verdict snapshot the forecast
registry bakes at deploy time (keyed by verdict key, one entry = the bundle's
``forecast_verdict.json`` plus ``provenance.run_id`` / ``provenance.session``). After the
2026-09-05 owner ruling (FINDING-capx-d57 §8.1) the shipped PJM T1-H posture is arm A, so:

* the current ``pjm-t1h`` entry (D45-R's census leg) moves VERBATIM to ``pjm-t1h-pre-d57``;
* ``pjm-t1h`` becomes arm A's verdict (``pjm-2021-2025-realized-t1h-d57-clearing``);
* ``pjm-t1h-d57-clearing-headbasis`` is added (arm B).

Idempotent: a re-run leaves the file unchanged. Run from the repo root:
``uv run python docs/handoffs/d57/merge-ff-verdicts-2026-09-05.py``
"""

import json
from pathlib import Path

SNAP = Path("frontend/data/forecast/ff-verdicts.json")
ARMS = {
    "pjm-t1h": "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing",
    "pjm-t1h-d57-clearing-headbasis": (
        "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing-headbasis"
    ),
}

snap = json.loads(SNAP.read_text())
prior = snap.get("pjm-t1h")
if prior and prior.get("provenance", {}).get("run_id") == "pjm-2021-2025-realized-t1h-d45r":
    snap["pjm-t1h-pre-d57"] = prior
    print("preserved D45-R's pjm-t1h entry at pjm-t1h-pre-d57")
for key, bundle in ARMS.items():
    v = json.loads((Path(bundle) / "forecast_verdict.json").read_text())
    v.setdefault("provenance", {})["run_id"] = Path(bundle).name
    v["provenance"]["session"] = "capx-D57"
    snap[key] = v
    print(f"{key} <- {Path(bundle).name}: {v.get('determination')}")
SNAP.write_text(json.dumps(snap, indent=1) + "\n")
print("wrote", SNAP, "keys:", sorted(k for k in snap if k.startswith("pjm-t1h")))
