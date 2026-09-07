"""miso-242 V-1..V-5 — is the SPP hourly ladder's derive pairing ACROSS YEARS? Zero LP.

Declared with its bars in
``results/calibration/ADDENDUM-miso242-the-derive-pairs-across-years-2026-09-07.md``
and pushed BEFORE it was run. The hypothesis it tests was formed POST-HOC from D-EDGE's
pre-declared ``quantile_recheck`` column, which is why it is written here as a falsifiable
test with three independently refuting legs rather than asserted.

    V-1  ``g_all.loc[year].join(load_spp_hub_da())`` returns exactly 3 x 8760 rows, and
         ``da`` / the SPP flow column are IDENTICAL across the three year-blocks.
    V-2  the ladder derived from that MISPAIRED frame reproduces the COMMITTED per-year
         SPP table in all 48 entries (atol 0.005, the pin test's own tolerance).
    V-3  THE CONTROL: PJM's derive (which takes no join) reproduces the committed PJM
         table in all 48 entries on the correctly paired frame.
    V-4  REPORTED, GATED NOWHERE: what the correctly paired frame would produce.
    V-5  whether the POOLED forward ladder is affected.

Any of V-1/V-2/V-3 failing REFUTES the hypothesis.

THIS PROBE REPAIRS NOTHING AND COMMITS NOTHING. PREREG section 5.2 refused a re-derive in
advance for every branch, this one by name; the frozen committed table is READ and is not
modified, and V-4's numbers are reported for magnitude only and are UN-TARGETABLE.

Usage: python3 scripts/probes/_miso242_derive_pairing_addendum.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results/calibration/_miso242_derive_pairing_addendum.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
ATOL = 0.005  # V-2 / V-3 / V-5 — the rule-23 pin test's own atol


def _ladder_delta(got: dict, ref: dict) -> float:
    """Max abs deviation over all 16 entries of one seam-year ladder."""
    worst = 0.0
    for side in ("import", "export"):
        a = np.asarray(got[side], float)
        b = np.asarray(ref[side], float)
        worst = max(worst, float(np.abs(a - b).max()))
    return worst


def main() -> int:  # noqa: PLR0915 - one linear probe, addendum section order
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED,
    )

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()
    hub_col = dm.SPP_ANCHOR_HUB
    hub_series = dm.load_spp_hub_da()
    spec_spp = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}["SPP"]
    step = float(spec_spp.interface_limit_mw) / SEAM_FLOW_TRANCHES

    report = {
        "probe": "miso-242 V-1..V-5 — does the SPP ladder's derive pair across years?",
        "addendum": (
            "results/calibration/"
            "ADDENDUM-miso242-the-derive-pairs-across-years-2026-09-07.md"
        ),
        "zero_lp": True,
        "repairs_nothing": True,
        "atol": ATOL,
        "years": {},
    }

    v1_ok = True
    v2_worst = 0.0
    v3_worst = 0.0

    for year in YEARS:
        gy = g_all.loc[year]
        mis = gy.join(hub_series, how="left")

        # ---- V-1: the join replicates the year's rows against all three hub years ----
        n_rows = int(len(mis))
        blocks = {}
        da_dev = 0.0
        flow_dev = 0.0
        if isinstance(mis.index, type(g_all.index)) and mis.index.nlevels == 2:
            hub_years = sorted(set(mis.index.get_level_values(0)))
            ref_da = None
            ref_fl = None
            for hy in hub_years:
                blk = mis.xs(hy, level=0).sort_index()
                blocks[str(hy)] = int(len(blk))
                d = blk["da"].to_numpy(float)
                f = blk["SPP"].to_numpy(float)
                if ref_da is None:
                    ref_da, ref_fl = d, f
                else:
                    n = min(len(d), len(ref_da))
                    da_dev = max(
                        da_dev,
                        float(np.nanmax(np.abs(d[:n] - ref_da[:n]))) if n else 0.0,
                    )
                    flow_dev = max(
                        flow_dev,
                        float(np.nanmax(np.abs(f[:n] - ref_fl[:n]))) if n else 0.0,
                    )
        v1 = {
            "join_rows": n_rows,
            "expected_if_replicated": 3 * HOURS,
            "rows_match": n_rows == 3 * HOURS,
            "hub_year_blocks": blocks,
            "max_abs_da_deviation_across_blocks": round(da_dev, 9),
            "max_abs_flow_deviation_across_blocks": round(flow_dev, 9),
            "PASS": bool(n_rows == 3 * HOURS and da_dev == 0.0 and flow_dev == 0.0),
        }
        v1_ok &= v1["PASS"]

        # ---- V-2: the MISPAIRED frame reproduces the COMMITTED per-year table --------
        mis_lad, mis_notes = dm.derive_spp_neighbour_hourly(gy)
        d2 = _ladder_delta(
            mis_lad, MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"]
        )
        v2_worst = max(v2_worst, d2)

        # ---- V-3 (CONTROL): PJM's derive, no join, on the correctly paired frame -----
        pjm_lad, _ = dm.derive_pjm_neighbour_hourly(gy)
        d3 = _ladder_delta(
            pjm_lad, MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]
        )
        v3_worst = max(v3_worst, d3)

        # ---- V-4: REPORTED, GATED NOWHERE — the correctly paired SPP ladder ----------
        cor = g_all.join(hub_series, how="left").loc[year]
        cor = cor.dropna(subset=[hub_col, "da", "SPP"])
        spread = (cor["da"] - cor[hub_col]).to_numpy(float)
        flow = cor["SPP"].to_numpy(float)
        notes: list[str] = []
        cor_lad = dm._derive_one(spread, flow, spec_spp, notes)
        committed = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"]
        z_committed = float(
            (
                (
                    (cor["da"].to_numpy(float) - cor[hub_col].to_numpy(float))
                    <= float(committed["import"][0])
                )
                & (
                    cor["da"].to_numpy(float)
                    >= cor[hub_col].to_numpy(float) + float(committed["export"][0])
                )
            ).mean()
        )
        z_corrected = float(
            (
                (
                    (cor["da"].to_numpy(float) - cor[hub_col].to_numpy(float))
                    <= float(cor_lad["import"][0])
                )
                & (
                    cor["da"].to_numpy(float)
                    >= cor[hub_col].to_numpy(float) + float(cor_lad["export"][0])
                )
            ).mean()
        )
        z_target = (
            1.0 - float((flow > 0.5 * step).mean()) - float((flow < -0.5 * step).mean())
        )

        report["years"][str(year)] = {
            "V1": v1,
            "V2": {
                "mispaired_ladder": mis_lad,
                "committed": {k: list(v) for k, v in committed.items()},
                "max_abs_delta": round(d2, 4),
                "PASS": bool(d2 <= ATOL),
                "notes": mis_notes,
            },
            "V3_control_pjm": {
                "derived_ladder": pjm_lad,
                "max_abs_delta": round(d3, 4),
                "PASS": bool(d3 <= ATOL),
            },
            "V4_reported_not_gated_correctly_paired": {
                "n_rows": int(len(cor)),
                "ladder": cor_lad,
                "dead_band_committed": [
                    float(committed["export"][0]),
                    float(committed["import"][0]),
                ],
                "dead_band_correctly_paired": [
                    float(cor_lad["export"][0]),
                    float(cor_lad["import"][0]),
                ],
                "dead_band_width_committed": round(
                    float(committed["import"][0]) - float(committed["export"][0]), 2
                ),
                "dead_band_width_correctly_paired": round(
                    float(cor_lad["import"][0]) - float(cor_lad["export"][0]), 2
                ),
                "Z_derive_with_committed_ladder": round(z_committed, 4),
                "Z_derive_with_correctly_paired_ladder": round(z_corrected, 4),
                "Z_target": round(z_target, 4),
                "abs_delta_committed_vs_target": round(abs(z_committed - z_target), 4),
                "abs_delta_corrected_vs_target": round(abs(z_corrected - z_target), 4),
                "notes": notes,
            },
        }

    # ---- V-5: the POOLED forward ladder ------------------------------------------
    pooled_src = g_all.loc[YEARS[0] : YEARS[-1]]
    pooled_join = pooled_src.join(hub_series, how="left")
    pooled_cor = pooled_join.dropna(subset=[hub_col, "da", "SPP"])
    sp = (pooled_cor["da"] - pooled_cor[hub_col]).to_numpy(float)
    fl = pooled_cor["SPP"].to_numpy(float)
    pooled_notes: list[str] = []
    pooled_lad = dm._derive_one(sp, fl, spec_spp, pooled_notes)
    d5 = _ladder_delta(pooled_lad, MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED["SPP"])
    report["V5_pooled"] = {
        "pooled_join_rows": int(len(pooled_join)),
        "expected_if_correctly_paired": 3 * HOURS,
        "correctly_paired": bool(len(pooled_join) == 3 * HOURS),
        "derived_from_correctly_paired": pooled_lad,
        "committed": {
            k: list(v)
            for k, v in MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED["SPP"].items()
        },
        "max_abs_delta": round(d5, 4),
        "PASS": bool(d5 <= ATOL),
        "notes": pooled_notes,
    }

    report["V1_PASS"] = bool(v1_ok)
    report["V2_PASS"] = bool(v2_worst <= ATOL)
    report["V2_max_abs_delta"] = round(v2_worst, 4)
    report["V3_PASS"] = bool(v3_worst <= ATOL)
    report["V3_max_abs_delta"] = round(v3_worst, 4)
    report["HYPOTHESIS"] = (
        "CONFIRMED" if (v1_ok and v2_worst <= ATOL and v3_worst <= ATOL) else "REFUTED"
    )
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
