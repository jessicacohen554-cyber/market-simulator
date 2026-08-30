"""ercot-242 Phase-1: the room-axis armed run + kill-gated A/B score.

Control = the COMMITTED carve-out keeper bundle
``results/calibration/ercot236_k33_clip`` (its hourly sidecars + registered
officials — validated zero-solve by ``ercot226_official_score.py
--validate-keeper`` before any armed scoring; the drift contingency is
PRECOMMIT-ercot242 §2). Armed = ``results/calibration/ercot242_room_armed``
(the SAME recipe replayed 2023-only with ONLY
``ercot_offer_surface_cleared_share_rt_room=true``). Kills and outcome rules
are fixed in ``docs/PRECOMMIT-ercot242-room-axis-phase1-2026-08-30.md`` §2–§3:
K-SHED / K-OFFSEASON / K-COAL148 / K-SPUR (lidless no-increase) / K-CTST
(±1.0 TWh), the ercot-239 r2 constructions verbatim, all measured vs the
control; officials via ``ercot226_official_score.py``; actual band counts
DERIVED (never hardcoded — the ercot-238 ruling-1 discipline). Report-only:
the 14-hour missed-event family recomputed on both members and the 12 object
hours' prices (the declared-reach grading input, never selection).

Run:
    python scripts/probes/ercot242_room_ab.py --validate-keeper  # V-0k
    python scripts/probes/ercot242_room_ab.py --run-armed        # solve
    python scripts/probes/ercot242_room_ab.py --score            # A/B score
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CTL = REPO / "results" / "calibration" / "ercot236_k33_clip"
ARMED = REPO / "results" / "calibration" / "ercot242_room_armed"
OUT_JSON = REPO / "results" / "calibration" / "ercot242_room_ab.json"

GAS_CLASSES = ("CT_PEAKER", "ST_GAS")

#: The committed 14-hour missed-event family + the 12-hour object set
#: (PRECOMMIT-ercot241 §1; the wind pair stays excluded from the object set).
FAMILY_HOURS = sorted(
    [2058, 2971, 4578, 4623, 4626, 5369, 5484, 5777, 5943, 5945, 6399, 7001,
     7145, 7480]
)
WIND_PAIR = (6399, 7145)
OBJECT_HOURS = [h for h in FAMILY_HOURS if h not in WIND_PAIR]


def run_armed() -> None:
    """Solve the armed member 2023-only via replay_keeper (the ONE solve)."""
    cmd = [
        sys.executable,
        str(REPO / "scripts/replay_keeper.py"),
        str(CTL),
        "--out-dir",
        str(ARMED),
        "--years",
        "2023",
        "--set",
        "ercot_offer_surface_cleared_share_rt_room=true",
        "--note",
        "ercot-242 Phase-1: room-axis extension of the armed RT wall "
        "(PRECOMMIT-ercot242-room-axis-phase1 section 1)",
    ]
    subprocess.run(cmd, check=True)


def validate_keeper() -> None:
    """V-0k: assert the committed control reproduces its registered officials."""
    subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/probes/ercot226_official_score.py"),
            "--validate-keeper",
        ],
        check=True,
    )
    print("V-0k PASS: committed keeper officials validated zero-solve")


def _lw(bundle: Path):
    df = pd.read_parquet(bundle / "hourly" / "system_2023.parquet")
    df = df[(df["year"] == 2023) & (df["pass"] == "P1")]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    g = df.groupby("hour")
    rng = range(8760)
    return (
        (num / den).reindex(rng).to_numpy(float),
        den.reindex(rng).to_numpy(float),
        g["slack"].sum().reindex(rng).fillna(0.0).to_numpy(float),
        g["price"].max().reindex(rng).to_numpy(float),
    )


def _class_twh(bundle: Path, classes) -> dict:
    ch = pd.read_parquet(bundle / "hourly" / "class_hourly_2023.parquet")
    ch = ch[(ch["year"] == 2023) & (ch["pass"] == "P1")]
    return {c: float(ch[ch["klass"] == c]["mw"].sum() / 1e6) for c in classes}


def actual_band_counts(a: np.ndarray) -> dict:
    """DERIVED actual band counts, cross-checked vs the committed tail record."""
    af = a[np.isfinite(a)]
    counts = {
        "200_500": int(((af >= 200) & (af < 500)).sum()),
        "500_1000": int(((af >= 500) & (af < 1000)).sum()),
        "ge_1000": int((af >= 1000).sum()),
    }
    tail = json.loads(
        (REPO / "frontend/data/backcast/tail/actual_tail.json").read_text()
    )["isos"]["ERCOT"]["2023"]
    if sum(counts.values()) != tail["rt_gt"]:
        raise AssertionError(
            f"actual band counts {counts} != actual_tail rt_gt {tail['rt_gt']}"
        )
    return counts


def _official(bundle: Path) -> dict:
    out = bundle / "official_2023.json"
    subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/probes/ercot226_official_score.py"),
            "--bundle",
            str(bundle),
            "--years",
            "2023",
            "--json-out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(out.read_text())


def score() -> None:
    """Full A/B: V-0k identity, kills vs the committed control, officials."""
    validate_keeper()
    m_c, dem_c, slack_c, _ = _lw(CTL)
    m_a, dem_a, slack_a, lam_a = _lw(ARMED)
    a = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    a = a[a["year"] == 2023].sort_values("hour")["rt"].to_numpy(float)[:8760]
    act = actual_band_counts(a)
    aa = np.nan_to_num(a, nan=1e9)
    cum = np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
    mon = np.searchsorted(cum, np.arange(8760), side="right")

    off_c = _official(CTL)
    off_a = _official(ARMED)

    # K-SHED: new shed hours vs control.
    new_shed = sorted(
        set(np.where(slack_a > 1e-6)[0]) - set(np.where(slack_c > 1e-6)[0])
    )
    # K-OFFSEASON: the ercot-235 construction, armed vs control.
    monthly = {}
    offseason_kill = False
    for mo in range(1, 13):
        k = mon == mo

        def _m(x, w):
            return float(np.nansum(x[k] * w[k]) / np.nansum(w[k]))

        mm, cc, aa_ = _m(m_a, dem_a), _m(m_c, dem_c), _m(a, dem_c)
        monthly[mo] = {
            "armed": round(mm, 2),
            "control": round(cc, 2),
            "actual": round(aa_, 2),
        }
        if mo in (1, 2, 3, 4, 5, 10, 11, 12) and abs(mm - aa_) > abs(cc - aa_) + 5.0:
            offseason_kill = True
    # K-COAL148.
    coal_c = _class_twh(CTL, ("COAL_LIGNITE", "COAL_PRB"))
    coal_a = _class_twh(ARMED, ("COAL_LIGNITE", "COAL_PRB"))
    coal_rise = sum(coal_a.values()) - sum(coal_c.values())
    # K-SPUR (lidless, Option A) no-increase vs control.
    mc = np.nan_to_num(m_c)
    ma = np.nan_to_num(m_a)
    spur_c = int(((mc >= 150) & (aa < 150)).sum())
    spur_a = int(((ma >= 150) & (aa < 150)).sum())
    # K-CTST.
    ctst_c = _class_twh(CTL, GAS_CLASSES)
    ctst_a = _class_twh(ARMED, GAS_CLASSES)
    ctst_delta = {c: round(ctst_a[c] - ctst_c[c], 4) for c in GAS_CLASSES}

    kills = {
        "K_SHED_new_hours": [int(h) for h in new_shed],
        "K_OFFSEASON": bool(offseason_kill),
        "K_COAL148_rise_twh": round(coal_rise, 4),
        "K_SPUR_lidless": {"control": spur_c, "armed": spur_a},
        "K_CTST_delta_twh": ctst_delta,
    }
    fired = {
        "K_SHED": len(new_shed) > 0,
        "K_OFFSEASON": offseason_kill,
        "K_COAL148": coal_rise > 0.5,
        "K_SPUR": spur_a > spur_c,
        "K_CTST": any(abs(v) > 1.0 for v in ctst_delta.values()),
    }

    def bands(x):
        xx = np.nan_to_num(x)
        return {
            "200_500": int(((xx >= 200) & (xx < 500)).sum()),
            "500_1000": int(((xx >= 500) & (xx < 1000)).sum()),
            "ge_1000": int((xx >= 1000).sum()),
        }

    # Report-only: the missed-event family + object-hour reach (declared in
    # PRECOMMIT-ercot242 §2 — grading input for the FINDING, never selection).
    def _family(m):
        mm_ = np.nan_to_num(m, nan=0.0)
        return sorted(int(h) for h in np.where((mm_ < 200.0) & (aa >= 500.0)
                                               & (aa < 1e9))[0])

    fam_c = _family(m_c)
    fam_a = _family(m_a)
    object_rows = {
        str(h): {
            "actual": round(float(a[h]), 2),
            "control": round(float(m_c[h]), 2),
            "armed": round(float(m_a[h]), 2),
        }
        for h in FAMILY_HOURS
    }

    res = {
        "session": "ercot-242 Phase-1",
        "precommit": "docs/PRECOMMIT-ercot242-room-axis-phase1-2026-08-30.md",
        "control": "committed ercot236_k33_clip bundle (V-0k validated)",
        "control_official": off_c,
        "armed_official": off_a,
        "kills": kills,
        "kills_fired": fired,
        "any_kill": any(fired.values()),
        "bands_model_vs_actual": {
            "control": bands(m_c),
            "armed": bands(m_a),
            "actual": act,
        },
        "spur_banded": {
            "control": int(((mc >= 150) & (mc <= 500) & (aa < 150)).sum()),
            "armed": int(((ma >= 150) & (ma <= 500) & (aa < 150)).sum()),
        },
        "clip_saturated_hours_armed": int((np.nan_to_num(lam_a) >= 4999.0).sum()),
        "monthly_lw": monthly,
        "ctst_levels_twh": {"control": ctst_c, "armed": ctst_a},
        "missed_event_family": {
            "control": fam_c,
            "armed": fam_a,
            "n_control": len(fam_c),
            "n_armed": len(fam_a),
            "object_hours": OBJECT_HOURS,
            "rows": object_rows,
        },
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))
    print(
        json.dumps(
            {
                k: res[k]
                for k in (
                    "kills_fired",
                    "any_kill",
                    "kills",
                    "bands_model_vs_actual",
                    "spur_banded",
                    "missed_event_family",
                )
            },
            indent=1,
        )
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate-keeper", action="store_true")
    ap.add_argument("--run-armed", action="store_true")
    ap.add_argument("--score", action="store_true")
    args = ap.parse_args()
    if args.validate_keeper and not args.score:
        validate_keeper()
    if args.run_armed:
        run_armed()
    if args.score:
        score()


if __name__ == "__main__":
    main()
