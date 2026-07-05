"""ercot 33 = ercot 32 keeper (ercot_ordc_total_rtolcap_v1) with ONE delta:
ercot_dam_as_overlay=False.

Stage 0 of docs/handoffs/ercot-as-coopt-plan-2026-07.md (WS-F). This is the
ex-overlay re-baseline every later stage (WS-A/WS-B/ercot40) compares against.
Byte-faithful replay of the keeper's meta.json via replay_keeper.build_kwargs
(same mapping the BTM re-solve and the D-7 statmode probe both use), with the
single flag flipped. No offer-curve retuning, no other flag touched — measurement,
not calibration (CLAUDE.md #10/#11/#13).
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import run_calibration_full as rcf  # noqa: E402
from replay_keeper import build_kwargs  # noqa: E402

KEEPER_BUNDLE = REPO / "results/calibration/ercot_ordc_total_rtolcap_v1"
OUT_DIR = REPO / "results/calibration/ercot33_exoverlay_baseline_2026-07"

meta = json.loads((KEEPER_BUNDLE / "meta.json").read_text())

kwargs = build_kwargs(meta)
kwargs["years"] = [int(y) for y in meta["years"]]
kwargs["iso"] = meta["iso"]
kwargs["hours"] = int(meta.get("hours", 8760))
kwargs["reference"] = rcf._load_reference()
kwargs["run_dir"] = OUT_DIR

# --- the single delta under test ---
kwargs["ercot_dam_as_overlay"] = False

kwargs["note"] = (
    "ercot 33 ex-overlay baseline (WS-F / stage 0 of the AS co-opt "
    "overlay-replacement plan, docs/handoffs/ercot-as-coopt-plan-2026-07.md). "
    "Byte-faithful replay of keeper ercot_ordc_total_rtolcap_v1 (meta.json) "
    "with ONE delta: ercot_dam_as_overlay=False (was True). Everything else "
    "unchanged — RTORDPA overlay stays on (separate G2 backcast bridge, "
    "out of scope), multi-product AS co-opt + ECRS conservative-deployment + "
    "lumped ORDC total-reserve family + measured RTOLCAP/RTOFFCAP supply cap "
    "+ measured storage AS treatment + measured HH gas shape all unchanged. "
    "Probe only, not a keeper — the clean pre-overlay baseline every later "
    "WS-A/WS-B/ercot40 stage compares against (CLAUDE.md #10/#11/#13: "
    "measurement, not calibration)."
)

OUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"solving ercot33 ex-overlay baseline -> {OUT_DIR}")
run_dir = rcf.solve_and_persist(**kwargs)
rcf.report_run(run_dir)
print("ercot 33 done:", run_dir)
