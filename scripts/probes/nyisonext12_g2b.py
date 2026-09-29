"""NYISO-NEXT-12 G-2 (b) "counted once" (ZERO LP): reconstruction at the pin.

``docs/PRECOMMIT-nyiso-next11-ne-ac-node-2026-09-28.md`` sec. 6, G-2 (b), per year
2021-2025:

* B1 -- the pooled ladder the armed spec serves equals
  ``NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR[y]``, AND that table re-derives
  byte-for-byte from measured inputs (``derive_nyiso_ne_ac_ladder.derive_year``,
  the incumbent pooled formula on net import WITHOUT the NE row);
* B2 -- the node ladder re-derives to ``NYISO_NE_AC_LADDER_BY_YEAR[y]``;
* B3 -- the pooled Capital_Hudson link envelope the armed runner path produces
  (``nyiso_par_attributed_ttc_hourly(exclude_rows=(NE row,))``) equals the
  attribution of the P-32 frame with the NE row removed, and differs from the
  attribution that includes it (the NE row is out of the pooled envelope).

Record: ``results/calibration/_nyisonext12_g2b.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "src", REPO, REPO / "scripts" / "data"):
    sys.path.insert(0, str(p))

import derive_nyiso_ne_ac_ladder as dl  # noqa: E402

from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.nyiso_par_attribution import (  # noqa: E402
    attributed_envelope_by_zone,
    nyiso_par_attributed_ttc_hourly,
)
from market_sim.model.interchange.spec import (  # noqa: E402
    IMPORT_ZONE,
    NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR,
    NYISO_NE_AC_LADDER_BY_YEAR,
    NYISO_NE_AC_LANDING,
    NYISO_NE_AC_SEAM_ROW,
    apply_interchange_topology,
    get_interchange_spec,
)
from scripts.lib.clean_io import read_clean  # noqa: E402

T = 8760


def year_block(y: int) -> dict:
    """B1-B3 for one year."""
    cfg = ScenarioConfig(iso="NYISO", mode="backcast", nyiso_ne_ac_node=True)
    spec = get_interchange_spec(cfg, "NYISO", year=y)
    r = dl.derive_year(y)
    split = [tuple(x) for x in NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR[y]]
    b1 = [tuple(x) for x in spec.import_tranches] == split and [
        tuple(x) for x in r["pooled_without_ne"]
    ] == split
    node = NYISO_NE_AC_LADDER_BY_YEAR[y]
    b2 = r["node"] == {
        k: node[k] for k in ("import_mw", "export_mw", "import", "export")
    }

    topo = apply_interchange_topology(get_iso_config("NYISO"), spec, cfg, year=y)
    ttc = np.array([float(link.ttc_mw) for link in topo.links])
    fwd, rev = nyiso_par_attributed_ttc_hourly(
        ttc, topo, y, T, exclude_rows=(NYISO_NE_AC_SEAM_ROW,)
    )
    pooled = IMPORT_ZONE["NYISO"]
    i = next(
        k
        for k, link in enumerate(topo.links)
        if link.from_zone == pooled and link.to_zone == NYISO_NE_AC_LANDING
    )
    frame = read_clean("nyiso-interface-flows", iso="NYISO", year=y, validate=False)
    wo = attributed_envelope_by_zone(
        frame[frame["interface"] != NYISO_NE_AC_SEAM_ROW],
        y,
        T,
        NYISO_SEAM_FLOW_PERCENTILE,
    )[NYISO_NE_AC_LANDING]
    wi = attributed_envelope_by_zone(frame, y, T, NYISO_SEAM_FLOW_PERCENTILE)[
        NYISO_NE_AC_LANDING
    ]
    b3_eq = bool(np.array_equal(fwd[:, i], wo[0]) and np.array_equal(rev[:, i], wo[1]))
    b3_ne_out = bool(
        not (np.array_equal(wo[0], wi[0]) and np.array_equal(wo[1], wi[1]))
    )
    return {
        "B1_pooled_ladder": bool(b1),
        "B2_node_ladder": bool(b2),
        "B3_envelope_equals_ne_excluded": b3_eq,
        "B3_ne_row_changes_envelope": b3_ne_out,
        "CH_import_env_mean_mw": {
            "with_ne": round(float(wi[0].mean()), 1),
            "arm": round(float(fwd[:, i].mean()), 1),
        },
        "CH_export_env_mean_mw": {
            "with_ne": round(float(wi[1].mean()), 1),
            "arm": round(float(rev[:, i].mean()), 1),
        },
        "pass": bool(b1 and b2 and b3_eq and b3_ne_out),
    }


if __name__ == "__main__":
    ys = [int(x) for x in sys.argv[1:]] or [2021, 2022, 2023, 2024, 2025]
    res = {str(y): year_block(y) for y in ys}
    (REPO / "results/calibration/_nyisonext12_g2b.json").write_text(
        json.dumps(res, indent=1)
    )
    print(json.dumps(res, indent=1))
