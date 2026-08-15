#!/usr/bin/env python3
"""ercot-200 probe: regime-partition arithmetic on the committed SOM anchors.

READ-ONLY. Reads exactly one committed input —
``data/raw/som-competitive-conduct/som_competitive_conduct.csv`` (the ercot-195
intake, 7 ERCOT vintages 2019-2025, each row carrying source_doc+source_page) —
and writes ``results/calibration/ercot200_regime_partition.json``.

What it computes, for the ercot-200 regime-conditioning decision card
(authorized by the L-SCAR V0-FAIL adjudication item (ii), on main at fb6d08d):

1. The market-design regime partition of the anchor vintages (the partition is
   a documented analyst choice, cited per boundary; both the coarse 4-regime
   cut and the finer 5-regime cut are emitted so the card can show the
   anchor-count consequences of the cut itself).
2. Per-regime anchor counts, midpoints, and within-regime spreads.
3. The ex-ante V0-analogue gate arithmetic: for a regime-ONLY conditioning
   variable, any function R_f(regime) must assign near-equal predictions to
   same-regime years, so its best-case error on a within-regime pair is at
   least half the pair's rent gap — the FINDING-ercot195 §4 model-free bound,
   re-run with "regime" in place of "tightness". Singleton regimes are flagged
   UNTESTABLE (leave-one-out leaves zero same-regime anchors).
4. The monitor's own design-stripped counterfactuals (2021 ex-Uri, 2023
   ex-ECRS ~= CONE), transcribed from the same CSV, as the committed basis for
   any future design-attribution assembly.

DO-NOT-REDO honored: NO tightness variable is read or fit anywhere in this
probe (V0 is the DO-NOT-REDO adjudication for tightness conditioning); the
2019-vs-2020 tightness near-tie is cited by the card from FINDING-ercot195,
never recomputed. No model artifact is read; no year is solved or scored.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSV_PATH = REPO / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
OUT_PATH = REPO / "results/calibration/ercot200_regime_partition.json"

# V0 PASS bar, verbatim from the L-SCAR charter §3 (DECISION-CARD-lscar §3 V0):
# within +-25% or +-15 $/kW-yr, whichever is LARGER, on CT and CC, every fold.
V0_PCT = 0.25
V0_ABS = 15.0

# The market-design regime partition. Boundaries are published design facts:
#  - SWCAP $9,000 through 2021, $5,000 from Jan 2022 (2021 SOM p.114 note,
#    transcribed in the CSV; PUCT post-Uri orders).
#  - "primarily due to the ORDC changes implemented at the beginning of the
#    year" — the 2022 SOM's own attribution of the 2022 level (2022 SOM p.108).
#  - ECRS launched 2023-06; the 2023 SOM attributes ~50% of new-unit net
#    revenue to ECRS price effects (2023 SOM p.108, on the CSV).
#  - 2024/2025 described as normalised by their SOMs (2024 SOM p.119,
#    2025 SOM p.125).
#  - RTC+B go-live 2025-12-05 retires the ORDC adders; first full year 2026
#    (results/scarcity.py::_RTCB_FIRST_FULL_YEAR). Zero SOM anchors exist for
#    the RTC+B regime until the 2026 SOM publishes (~mid-2027).
COARSE_CUT = {
    "ordc_pre2022_swcap9000": [2019, 2020, 2021],
    "ordc_widened_2022_swcap5000": [2022],
    "ecrs_era_2023_2025": [2023, 2024, 2025],
    "rtcb_2026_forward": [],
}
FINE_CUT = {
    "ordc_pre2022_swcap9000": [2019, 2020, 2021],
    "ordc_widened_2022_swcap5000": [2022],
    "ecrs_launch_2023": [2023],
    "ecrs_normalised_2024_2025": [2024, 2025],
    "rtcb_2026_forward": [],
}


def _load_anchors() -> dict:
    """Return {year: {"CT": midpoint, "CC": midpoint}} plus the monitor's own
    counterfactual rows, from the committed CSV only."""
    seg_map = {"new_gas_ct": "CT", "new_gas_cc": "CC"}
    vals: dict[int, dict[str, dict[str, float]]] = {}
    counterfactuals: list[dict] = []
    with open(CSV_PATH, newline="") as fh:
        for row in csv.DictReader(fh):
            if row["iso"] != "ERCOT" or row["fleet_segment"] not in seg_map:
                continue
            year = int(row["year"])
            cls = seg_map[row["fleet_segment"]]
            metric = row["metric"]
            if metric.startswith("net_revenue_ex_uri_usd_per_kw_yr"):
                counterfactuals.append(
                    {
                        "year": year,
                        "class": cls,
                        "metric": metric,
                        "value": float(row["value"]),
                        "source": f"{row['source_doc']} p.{row['source_page']}",
                    }
                )
                continue
            if metric == "ecrs_effect_share_of_net_revenue":
                counterfactuals.append(
                    {
                        "year": year,
                        "class": cls,
                        "metric": metric,
                        "value": float(row["value"]),
                        "source": f"{row['source_doc']} p.{row['source_page']}",
                    }
                )
                continue
            if not metric.startswith("net_revenue_usd_per_kw_yr"):
                continue
            side = "max" if metric.endswith("_max") else "min"
            vals.setdefault(year, {}).setdefault(cls, {})[side] = float(row["value"])
    anchors = {}
    for year, classes in sorted(vals.items()):
        anchors[year] = {}
        for cls, sides in classes.items():
            lo = sides.get("min", sides.get("max"))
            hi = sides.get("max", sides.get("min"))
            anchors[year][cls] = round((lo + hi) / 2.0, 2)
    return {"midpoints": anchors, "monitor_counterfactuals": counterfactuals}


def _fold_tolerance(held_out: float) -> float:
    """The V0 bar for one fold: max(25% of the held-out value, $15)."""
    return max(V0_PCT * abs(held_out), V0_ABS)


def _regime_gate(cut: dict, anchors: dict) -> dict:
    """Ex-ante leave-one-vintage-out arithmetic for a regime-ONLY R_f.

    For each regime: a singleton regime is UNTESTABLE (the held-out vintage's
    regime has no other anchor to predict from). For multi-anchor regimes the
    best any regime-keyed constant can do on a within-regime pair is half the
    pair's gap (the FINDING-ercot195 §4 bound with regime as the conditioner);
    each within-regime pair is checked against the V0 fold tolerance of both
    of its members.
    """
    out = {}
    for regime, years in cut.items():
        entry: dict = {"years": years, "n_anchors": len(years)}
        if not years:
            entry["gate"] = "NO ANCHORS — forward regime; nothing to fit or fold until the 2026 SOM (~mid-2027)"
            out[regime] = entry
            continue
        if len(years) == 1:
            entry["gate"] = "UNTESTABLE — singleton regime: leave-one-out leaves zero same-regime anchors"
            out[regime] = entry
            continue
        pairs = []
        for cls in ("CT", "CC"):
            ys = [y for y in years if cls in anchors.get(y, {})]
            for i, a in enumerate(ys):
                for b in ys[i + 1 :]:
                    va, vb = anchors[a][cls], anchors[b][cls]
                    gap = abs(va - vb)
                    irreducible = round(gap / 2.0, 2)
                    tol = round(min(_fold_tolerance(va), _fold_tolerance(vb)), 2)
                    pairs.append(
                        {
                            "class": cls,
                            "pair": [a, b],
                            "values": [va, vb],
                            "rent_gap": round(gap, 2),
                            "irreducible_error_regime_only": irreducible,
                            "tightest_fold_tolerance": tol,
                            "fold_passable_by_any_regime_only_fn": irreducible <= tol,
                        }
                    )
            entry["within_regime_pairs"] = pairs
            entry["gate"] = (
                "FAILS for ANY regime-only R_f"
                if any(not p["fold_passable_by_any_regime_only_fn"] for p in pairs)
                else "within-regime spread inside the V0 bar"
            )
        out[regime] = entry
    return out


def main() -> None:
    """Run the partition arithmetic and write the JSON artifact."""
    loaded = _load_anchors()
    anchors = loaded["midpoints"]
    result = {
        "probe": "ercot200_regime_partition",
        "authority": "L-SCAR V0-FAIL adjudication item (ii), on main at fb6d08d (docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md)",
        "input": str(CSV_PATH.relative_to(REPO)),
        "v0_bar": {"pct": V0_PCT, "abs_usd_per_kw_yr": V0_ABS, "rule": "max(pct*value, abs), every fold, CT and CC"},
        "anchor_midpoints_usd_per_kw_yr": {str(y): v for y, v in anchors.items()},
        "monitor_counterfactuals": loaded["monitor_counterfactuals"],
        "coarse_cut_4_regimes": _regime_gate(COARSE_CUT, anchors),
        "fine_cut_5_regimes": _regime_gate(FINE_CUT, anchors),
        "notes": [
            "Regime boundaries are documented analyst choices over published design facts; two defensible cuts are emitted to show the anchor-count consequence of the cut itself.",
            "No tightness variable is read or fit anywhere in this probe (V0 DO-NOT-REDO honored).",
            "2021 enters the pre-2022 regime as the Uri event year; the monitor's own ex-Uri counterfactual is carried alongside, not substituted.",
        ],
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")
    print(f"wrote {OUT_PATH.relative_to(REPO)}")
    for cut_name in ("coarse_cut_4_regimes", "fine_cut_5_regimes"):
        print(f"-- {cut_name}")
        for regime, entry in result[cut_name].items():
            print(f"   {regime}: n={entry['n_anchors']} gate={entry['gate']}")


if __name__ == "__main__":
    main()
