"""Driver: PJM 96 — pjm-94 keeper recipe + measured seam ladder (single-delta A/B).

pjm-94 (2026-07-09-pjm-94-stgas-netload, current PJM keeper post pjm-95 demotion,
PR #1933/#1939, rule 24) verbatim, plus ScenarioConfig.pjm_seam_measured_ladder=True
— the measured PJM interface seam pricing merged 2026-07-10, previously untested
in any dispatch solve (only the offline P9 seam-volume check ran pre-merge).

Deliberately NOT stacked with the internal-interface-limit overlay (that work is
a separate data-intake session) — single-delta A/B against pjm-94 so any C1/zonal
movement is attributable to the seam mechanism alone (rule 19/21 precedent:
pjm-78/79 same-SHA A/B).

Recipe is read from results/calibration/pjm94_stgas_netload_drag/meta.json via
scripts/replay_keeper.build_kwargs (byte-faithful remap), not hand-copied, so
pjm-96 cannot silently drift from the keeper it's diffed against.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
from run_calibration_full import _load_reference, report_run, solve_and_persist  # noqa: E402

PJM94_BUNDLE = REPO / "results" / "calibration" / "pjm94_stgas_netload_drag"


def main() -> int:
    meta = json.loads((PJM94_BUNDLE / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)

    kwargs["pjm_seam_measured_ladder"] = True
    kwargs["run_dir"] = REPO / "results" / "calibration" / "pjm96_seam_ladder"
    kwargs["note"] = (
        "PJM 96: pjm-94 keeper recipe (byte-faithful via replay_keeper.build_kwargs) "
        "+ pjm_seam_measured_ladder=True. Single-delta A/B vs pjm-94 isolating the "
        "measured PJM interface seam pricing (merged 2026-07-10, PJM_SEAM_LADDER_BY_YEAR, "
        "interchange_config.PJM_SEAM_TIE) — targets the C1 CC_REGULAR seam-driven miss "
        "(pjm-95 root-cause lead: 46% import-hours modeled vs ~2% measured, 2023) and the "
        "eastern-zone CC/CT under-run (Dominion/EMAAC/SWMAAC) this displaces phantom "
        "MISO/NYISO imports for. Not stacked with the internal transfer-interface-limit "
        "overlay (separate session, static ttc_mw unchanged here) — attribution stays clean."
    )

    reference = _load_reference()
    kwargs["reference"] = reference
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["hours"] = int(meta.get("hours", 8760))

    print(
        "=== pjm-96 solve kwargs (delta vs pjm-94: pjm_seam_measured_ladder=True) ==="
    )
    print(f"years={kwargs['years']} iso={kwargs['iso']} hours={kwargs['hours']}")
    print(f"out_dir={kwargs['run_dir']}")

    run_dir = solve_and_persist(**kwargs)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
