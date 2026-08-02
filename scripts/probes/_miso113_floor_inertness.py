"""miso-113 Phase-1 probe: is the regulated-PRB NIGHT-LEVEL floor inert?

The ex-ante kill check pre-registered in
``results/calibration/PREREG-miso113-prb-night-floor-2026-08-01.md`` §5, run
BEFORE any code is written and before any LP.

miso-111 PREREG §8 retired the commitment-bridge form as "provably inert"
because it sized the floor at the measured LSL (plant-basis loading-when-on
p5 = 0.182), which sits BELOW every plant's ``_mustrun`` band (0.30-0.52) —
a floor under a floor cannot bind. That argument is statistic-specific. This
probe re-runs it against the level miso-113 actually proposes, the measured
WITHIN-RUN NIGHT level ``night_p50``
(``data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv``, frozen
deriver ``scripts/data/derive_prb_committed_split.py`` — rule 23, not
re-derived here).

Reports, over the regulated (``eia860_selfcommit_scope_plants``) MISO
COAL_PRB plants that carry a ``thermal_tranches_MISO.csv`` COAL row (the
runtime basis — ``COAL_MUSTRUN_BY_PLANT`` holds no MISO plant and the keeper
sets ``coal_prb_mustrun_override=None``, so ``pct_mr`` IS the sheet's
``mustrun_pct``):

* per plant, the incremental floor ``max(0, night_p50 - pct_mr/100) x
  nameplate`` — the MW the floor adds ABOVE the always-there ``_mustrun``
  band, which is what must be non-trivial for the mechanism to exist;
* how many plants clear (floor > 0.5 MW) and their share of class capacity;
* how much of each plant's floor lands on ``_committed`` and how much spills
  into ``_econ`` (the FILL-order question the mechanism has to answer).

KILL RULE (pre-registered): fewer than 5 plants clearing, or under 5 % of
regulated-PRB class capacity carrying a floor, kills the lane ex ante — no
LP, register the finding.

Source-data + fleet-parameter readout only; no model output enters.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.coal import _coal_class_for  # noqa: E402
from market_sim.data.fleet.eia860 import (  # noqa: E402
    eia860_selfcommit_scope_plants,
)

SPLIT = REPO / "data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv"
TRANCHES = REPO / "data/raw/_processed-legacy/thermal_tranches_MISO.csv"


def main() -> None:
    night = pd.read_csv(SPLIT)
    tr = pd.read_csv(TRANCHES)
    tr = tr[tr["plant_group"].astype(str).str.upper().str.startswith("COAL")]
    tr = tr.drop_duplicates(subset=["plant_code"], keep="first").set_index("plant_code")
    reg = eia860_selfcommit_scope_plants()

    rows = []
    for rec in night.to_dict("records"):
        pc = int(rec["plant_code"])
        if pc not in reg:
            continue
        if _coal_class_for(pc) != "COAL_PRB":
            continue
        if pc not in tr.index:
            print(f"  !! plant {pc} regulated PRB but NO thermal_tranches row")
            continue
        t = tr.loc[pc]
        nameplate = float(t["nameplate_mw"])
        pct_mr = float(t["mustrun_pct"])
        committed_cap = nameplate * float(t["committed_pct"]) / 100.0
        mustrun_cap = nameplate * pct_mr / 100.0
        n50 = float(rec["night_p50"])
        # The floor the mechanism ADDS above the always-there _mustrun band.
        floor_mw = max(0.0, n50 - pct_mr / 100.0) * nameplate
        rows.append(
            {
                "plant_code": pc,
                "nameplate_mw": nameplate,
                "pct_mr": pct_mr,
                "night_p50": n50,
                "mustrun_cap": mustrun_cap,
                "committed_cap": committed_cap,
                "floor_mw": floor_mw,
                "on_committed": min(floor_mw, committed_cap),
                "spill_to_econ": max(0.0, floor_mw - committed_cap),
                "clears": floor_mw > 0.5,
            }
        )

    df = pd.DataFrame(rows).sort_values("nameplate_mw", ascending=False)
    pd.set_option("display.width", 200)
    print(
        df.to_string(
            index=False,
            float_format=lambda v: f"{v:,.3f}",
        )
    )

    cap_tot = df["nameplate_mw"].sum()
    cl = df[df["clears"]]
    print()
    print(f"regulated MISO COAL_PRB plants on the runtime basis : {len(df)}")
    print(f"  clearing (floor > 0.5 MW)                         : {len(cl)}")
    print(
        f"  their share of regulated-PRB nameplate            : "
        f"{cl['nameplate_mw'].sum() / cap_tot:.1%} "
        f"({cl['nameplate_mw'].sum():,.0f} of {cap_tot:,.0f} MW)"
    )
    print(
        f"  total incremental floor at the night level        : {df['floor_mw'].sum():,.0f} MW"
    )
    print(
        f"    of which lands on _committed                    : "
        f"{df['on_committed'].sum():,.0f} MW"
    )
    print(
        f"    of which SPILLS past _committed into _econ      : "
        f"{df['spill_to_econ'].sum():,.0f} MW "
        f"({int((df['spill_to_econ'] > 0.5).sum())} plants)"
    )
    print(
        f"  cap-wtd night_p50                                 : "
        f"{(df['night_p50'] * df['nameplate_mw']).sum() / cap_tot:.4f}"
    )
    print(
        f"  cap-wtd pct_mr/100 (the _mustrun band)            : "
        f"{(df['pct_mr'] / 100.0 * df['nameplate_mw']).sum() / cap_tot:.4f}"
    )
    kill = len(cl) < 5 or (cl["nameplate_mw"].sum() / cap_tot) < 0.05
    print()
    print(
        f"PRE-REGISTERED KILL RULE (<5 plants or <5% capacity): {'FIRES' if kill else 'does NOT fire'}"
    )


if __name__ == "__main__":
    main()
