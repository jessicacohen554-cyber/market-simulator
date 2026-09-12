"""miso-255 screen gates for ``miso_import_sil_measured_envelope``.

Scores the six STOP-only structural gates fixed in
``docs/PRECOMMIT-miso255-measured-sil-2026-09-12.md`` §3, differencing an ARM
bundle against the COMMITTED control bundle (rule 29(b) form 4 — no control
solve). Every gate is structural; **none reads C1 CC_REGULAR, C3a or the gas
volume**, which are reported under G-6 and gate nothing.

Usage::

    uv run python scripts/probes/_miso255_screen_gates.py \\
        --arm results/calibration/miso255_sil_2021 \\
        --control results/calibration/miso251_tp2021 --year 2021
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402
from market_sim.data.eia930.envelopes import (  # noqa: E402
    measured_boundary_transfer_envelope,
)
from market_sim.model.interchange.spec import (  # noqa: E402
    EXTERNAL_SIMULTANEOUS_LIMITS,
)

T = 8760
SIL_MW = EXTERNAL_SIMULTANEOUS_LIMITS["MISO"][1]
TOL_MW = 1.0
G4_RAIL_MAX = 0.80  # pre-registered: <80 % of the year at >=99 % of the envelope


def _import_series(bundle: Path, year: int) -> np.ndarray:
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"] == "import")]
    return (
        ch.groupby("hour")["mw"]
        .sum()
        .reindex(range(T))
        .fillna(0.0)
        .to_numpy(dtype=float)
    )


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    return (ch.groupby("klass")["mw"].sum() / 1e6).to_dict()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--log", default=None, help="solve log to scan for G-1")
    ap.add_argument("--out", default=None, help="write the gate record here")
    a = ap.parse_args()

    arm, ctl, year = Path(a.arm), Path(a.control), a.year
    m_arm, m_ctl = _import_series(arm, year), _import_series(ctl, year)
    imp_env, exp_env = measured_boundary_transfer_envelope(
        "MISO", year, T, percentile=None, hour_ending_key=True
    )
    meter = -np.asarray(
        load_eia_hourly_benchmark("MISO", year)["interchange"], dtype=float
    )[:T]

    rec: dict[str, object] = {"year": year, "arm": str(arm), "control": str(ctl)}
    gates: dict[str, dict] = {}

    # G-1 LIVENESS
    marker = "aggregate simultaneous-transfer limit REPLACED"
    if a.log and Path(a.log).exists():
        txt = Path(a.log).read_text(errors="replace")
        gates["G1_liveness"] = {
            "pass": marker in txt and "8700" in txt,
            "detail": next(
                (ln.strip() for ln in txt.splitlines() if marker in ln), "MARKER ABSENT"
            ),
        }
    else:
        gates["G1_liveness"] = {"pass": None, "detail": "no --log given"}

    # G-2 FOOTPRINT CONFINEMENT — the arm must satisfy the injected bounds
    over_i = float(np.clip(m_arm - imp_env, 0.0, None).max())
    over_e = float(np.clip(-m_arm - exp_env, 0.0, None).max())
    gates["G2_confinement"] = {
        "pass": over_i <= TOL_MW and over_e <= TOL_MW,
        "max_import_violation_mw": over_i,
        "max_export_violation_mw": over_e,
        "hours_import_violating": int((m_arm - imp_env > TOL_MW).sum()),
        "hours_export_violating": int((-m_arm - exp_env > TOL_MW).sum()),
    }

    # G-3 THE RAIL MUST BREAK — nothing can sit on a scalar that is gone
    rail_arm = int((np.abs(m_arm) >= SIL_MW - TOL_MW).sum())
    rail_ctl = int((np.abs(m_ctl) >= SIL_MW - TOL_MW).sum())
    gates["G3_rail_broken"] = {
        "pass": rail_arm == 0,
        "control_rail_hours": rail_ctl,
        "arm_rail_hours": rail_arm,
    }

    # G-4 NOT A PIN — the arm must not merely relocate the rail onto the envelope
    pos = imp_env > 0.0
    util = np.where(pos, m_arm / np.where(pos, imp_env, 1.0), 0.0)
    at_env = float((util >= 0.99).mean())
    gates["G4_not_a_pin"] = {
        "pass": at_env < G4_RAIL_MAX,
        "frac_hours_at_99pct_of_envelope": at_env,
        "line": G4_RAIL_MAX,
        "distinct_hourly_import_values_arm": int(np.unique(np.round(m_arm, 1)).size),
        "distinct_hourly_import_values_control": int(
            np.unique(np.round(m_ctl, 1)).size
        ),
    }

    # G-5 NO NON-TARGET LOAD-BEARING FLIP — C2 / C6 / C8 must hold
    def _verdict(b: Path) -> dict:
        p = b / "metrics.json"
        return json.loads(p.read_text()) if p.exists() else {}

    gates["G5_non_target"] = {
        "pass": None,
        "note": "score with scripts/calibration_verdict.py; C2/C6/C8 must not flip",
        "arm_metrics_present": (arm / "metrics.json").exists(),
        "arm_legitimacy_present": (arm / "legitimacy_diagnostics.json").exists(),
    }

    # G-6 REPORTED, NEVER A GATE
    ct_arm, ct_ctl = _class_twh(arm, year), _class_twh(ctl, year)
    gas = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
    rec["G6_reported"] = {
        "import_twh_control": float(m_ctl.sum() / 1e6),
        "import_twh_arm": float(m_arm.sum() / 1e6),
        "import_twh_meter": float(meter.sum() / 1e6),
        "import_env_ceiling_twh": float(imp_env.sum() / 1e6),
        "gas_twh_control": float(sum(ct_ctl.get(k, 0.0) for k in gas)),
        "gas_twh_arm": float(sum(ct_arm.get(k, 0.0) for k in gas)),
        "cc_regular_twh_control": float(ct_ctl.get("CC_REGULAR", 0.0)),
        "cc_regular_twh_arm": float(ct_arm.get("CC_REGULAR", 0.0)),
        "class_delta_twh": {
            k: round(ct_arm.get(k, 0.0) - ct_ctl.get(k, 0.0), 3)
            for k in sorted(set(ct_arm) | set(ct_ctl))
            if abs(ct_arm.get(k, 0.0) - ct_ctl.get(k, 0.0)) >= 0.005
        },
    }

    # the mechanism's own pre-registered direction check
    rec["direction_check"] = {
        "abs_import_move_twh": abs(float((m_arm - m_ctl).sum() / 1e6)),
        "note": "2022's move must exceed 2021's in absolute MWh (PRECOMMIT §3)",
    }
    rec["gates"] = gates
    rec["verdict"] = (
        "STOP"
        if any(g.get("pass") is False for g in gates.values())
        else "no STOP fired"
    )

    print(json.dumps(rec, indent=2, default=float))
    if a.out:
        Path(a.out).write_text(json.dumps(rec, indent=2, default=float))


if __name__ == "__main__":
    main()
