"""UC-3-ERCOT: score a composed span WITHOUT touching the repo's frontend/data.

Copies frontend/data/backcast into a scratch dir, repoints every dashboard path
constant at the copy, registers the bundle there (render + sidecar, no prune) and
prints calibration_verdict.determine(rid) as JSON.

Usage: score_local.py <bundle_rel> <label> <out.json>
"""

import json
import shutil
import sys
from pathlib import Path

REPO = Path("/home/user/market-simulator")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

bundle_rel, label, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
scratch = out.parent / f"bc_data_{Path(bundle_rel).name}"
if scratch.exists():
    shutil.rmtree(scratch)
shutil.copytree(REPO / "frontend/data/backcast", scratch)

from scripts.lib import backcast_artifacts as ba  # noqa: E402

ba.DATA, ba.REGISTRY, ba.RUNS, ba.BENCH = (
    scratch,
    scratch / "registry",
    scratch / "runs",
    scratch / "bench",
)
from scripts import render_backcast as rb  # noqa: E402

for k, v in {
    "DATA_DIR": scratch,
    "RUNS_DIR": scratch / "runs",
    "BENCH_DIR": scratch / "bench",
}.items():
    if hasattr(rb, k):
        setattr(rb, k, v)
from scripts import calibration_verdict as cv  # noqa: E402

for k, v in {
    "DATA_DIR": scratch,
    "REGISTRY_DIR": scratch / "registry",
    "RUNS_DIR": scratch / "runs",
    "BENCH_DIR": scratch / "bench",
    "COMPLETENESS_DIR": scratch / "completeness",
    "AMPLITUDE_DIR": scratch / "amplitude",
    "TAIL_DIR": scratch / "tail",
}.items():
    if hasattr(cv, k):
        setattr(cv, k, v)

# guard: no module may still point into the repo's frontend/data
for m in (ba, rb, cv):
    for k, v in vars(m).items():
        if isinstance(v, Path) and "frontend/data/backcast" in str(v):
            raise SystemExit(f"unpatched path {m.__name__}.{k} = {v}")

bundle = REPO / bundle_rel
entry = rb.manifest_entry(label, bundle)
rid = entry["id"]
(scratch / "registry").mkdir(parents=True, exist_ok=True)
(scratch / "registry" / f"{rid}.json").write_text(
    json.dumps({**entry, "bundle": bundle_rel}, indent=2) + "\n"
)
rb.generate([(label, bundle)])
verdict = cv.determine(rid)
out.write_text(json.dumps(verdict, indent=2, default=str))
print("RID", rid)
print(cv.headline(verdict))
