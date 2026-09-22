"""hydro-5: read the solved arms against their committed keepers (zero LP).

Differences each per-year arm bundle against the keeper bundle it was replayed
from (rule 29(b) form 4 — the committed keeper IS the control), on the
statistics ``docs/PRECOMMIT-hydro-5-2026-09-22.md`` §5 pre-registered:

* **G1** — liveness: the arm's hourly hydro minimum against the mechanism's
  predicted monthly base (RoR flat base or the floor level, recomputed from
  ``build_hydro_fleet`` exactly as the phase-0 probe did).
* **G2** — annual and per-month hydro energy, arm vs keeper.
* **G3** — hours below 1 MW, p05 / p50 / p95, top-decile share and the
  within-month daily CV, arm vs keeper vs the measured EIA-930 series (the
  measured column flagged where it folds pumped storage).

Arms whose bundle is absent are listed as missing, never silently skipped.

Run: ``PYTHONPATH=.:src .venv/bin/python scripts/probes/_hydro5_arm_readout.py``
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from _hydro5_phase0 import (  # noqa: E402
    KEEPERS,
    MI,
    class_mw,
    load_mw,
    measured,
    stats,
)

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.hydro import (  # noqa: E402
    build_hydro_fleet,
    eia930_wat_level_folded,
)

# (arm tag, flag, ISO)
ARMS = [
    ("spp_floor", "hydro_min_flow_floor", "SPP"),
    ("spp_ror", "hydro_ror_split", "SPP"),
    ("neiso_ror", "hydro_ror_split", "NEISO"),
    ("miso_ror", "hydro_ror_split", "MISO"),
]


def predicted_base(iso: str, year: int, flag: str) -> np.ndarray:
    """The mechanism's monthly MW base (RoR flat sum, or floor level)."""
    kw = dict(backfill_year=2024, eia930_monthly=True)
    zones = get_iso_config(iso).zone_names
    if flag == "hydro_ror_split":
        units, _ = build_hydro_fleet(iso, year, zones, ror_split=True, **kw)
        attr = "hydro_ror_flat_monthly_mw"
    else:
        units, _ = build_hydro_fleet(iso, year, zones, min_flow_floor=True, **kw)
        attr = "hydro_min_flow_monthly_mw"
    rows = [np.asarray(getattr(u, attr)) for u in units if getattr(u, attr, None)]
    return np.sum(rows, axis=0) if rows else np.zeros(12)


def main() -> None:
    """Print the per-arm, per-year G1-G3 record as JSON."""
    logging.basicConfig(level=logging.ERROR)
    out: dict = {}
    for tag, flag, iso in ARMS:
        for keeper, years in KEEPERS[iso]:
            for y in years:
                arm_b = f"hydro5_{tag}_{y}"
                key = f"{tag} {y}"
                arm, ctl = class_mw(arm_b, y), class_mw(keeper, y)
                if arm is None:
                    out[key] = {"missing": arm_b}
                    continue
                load = load_mw(arm_b, y)
                if load is None:
                    load = load_mw(keeper, y)
                base = predicted_base(iso, y, flag)
                floor_t = base[MI]
                m_arm = np.array([arm[MI == m].sum() for m in range(12)])
                m_ctl = np.array([ctl[MI == m].sum() for m in range(12)])
                rec = {
                    "arm": stats(arm, load),
                    "keeper": stats(ctl, load),
                    "G1_min_gap_mw": round(float(np.min(arm - floor_t)), 2),
                    "G1_base_mw_min_max": [round(base.min(), 1), round(base.max(), 1)],
                    "G2_annual_pct": round(
                        100.0 * (arm.sum() - ctl.sum()) / ctl.sum(), 4
                    ),
                    "G2_max_month_pct": round(
                        float(np.max(np.abs(m_arm - m_ctl) / np.maximum(m_ctl, 1.0)))
                        * 100.0,
                        4,
                    ),
                }
                act = measured(iso, y)
                if act is not None:
                    rec["measured"] = stats(act, load)
                    rec["measured"]["admissible"] = not eia930_wat_level_folded(iso, y)
                out[key] = rec
                print(f"{key} read", file=sys.stderr)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
