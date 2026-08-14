"""ercot-196 HYGIENE: the ERCOT-137 anchoring-convention issue, measured.

Filed as an OPEN item in the DOF ledger at ercot-192, on the
``coal_offer_margin_level / _anchor`` (ERCOT-137, limb A) entry:

    "this identification pools the four subsets' bot_p50 RAW, with no fuel
    anchoring, while its registered anchor 1.7387 is the THREE-year mean and
    the pool sits at the 2024/25 res-hours mean fuel ~1.7040 — anchoring it
    consistently would move the level +0.38 = 0.41x its own band."

That entry recorded a single pooled scalar. This probe does two things it did
not: it grounds the inconsistency in the **mechanism's own identity** rather
than in a foreign arithmetic, and it resolves the displacement **per coal
plant** instead of at one blended heat rate.

**The identity.** ``legacy_bins.py`` applies the ERCOT-137 limb as

    mc[g, :] += coal_level - heat_rate[g] * coal_anchor - vom[g]

on top of an ``mc`` that already carries ``heat_rate[g] * fuel[g, t] + vom[g]``,
so the offer the LP sees is

    offer(g, t) = coal_level + heat_rate[g] * (fuel[g, t] - coal_anchor)

i.e. **at delivered fuel == anchor the offer reduces EXACTLY to
``coal_level``**, and the fuel-response slope is the unit's OWN assembled heat
rate. The level is therefore only well-formed if it is the measured offer level
**evaluated at the anchor**. ERCOT-137 measures it at the corpus's own
res-hours mean delivered coal and registers the three-year-mean anchor, so the
two disagree by ``heat_rate x (anchor - corpus_fuel)``.

This is a **sibling inconsistency**, not a foreign-arithmetic artifact:
ERCOT-139 (``cc_committed_offer_level``) removes its corpus's own measured fuel
response, and ERCOT-140 (``coal_peak_offer_level``) anchors on its measured gas
response. ERCOT-137 alone pools raw.

**Nothing is re-derived here** (rule 23 ``[R-FROZEN-DERIVE]``). This probe is
read-only and changes no constant; the repair is a named successor with its own
precommit, because it is solve-affecting on every coal ``_mustrun`` row. It
also raises a rule-23 question only the owner can answer, recorded in the
output: rule 23 re-derives on a SOURCE-DATA change, and a derivation-convention
repair is neither a data update nor a residual chase.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot196_ercot137_anchoring.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BIN_SHEET = REPO / "data/raw/reference/custom-bin-assignments.csv"
BOUND = REPO / "results/calibration/ercot192_coal_limbs_bound.json"
OUT = REPO / "results/calibration/ercot196_ercot137_anchoring.json"

# The ledgered ERCOT-137 identification, as armed on the run192 keeper.
ARMED_LEVEL = 15.8807
ARMED_ANCHOR = 1.7387  # registered three-year-mean delivered coal, $/MMBtu
CORPUS_FUEL = 1.7040  # the four 2024/25 subsets' res-hours mean delivered coal
BAND = 0.93  # the identification's own +/- band, $/MWh
# COAL's must-run heat-rate multiplier default (campd_bins._DEFAULT_HR_MULT_BY_GROUP).
COAL_MR_HR_MULT = 1.00


def _coal_rows() -> pd.DataFrame:
    """The curated coal bin rows with their assembled must-run heat rate."""
    df = pd.read_csv(BIN_SHEET)
    coal = df[df["Plant_Group"].astype(str).str.upper().str.startswith("COAL")].copy()
    coal["hr_mustrun"] = coal["Plant_Avg_HR_MMBtu_MWh"] * coal[
        "HR_Mult_Must_Run"
    ].fillna(COAL_MR_HR_MULT)
    return coal


def main() -> None:
    """Measure the displacement per plant and write the record."""
    coal = _coal_rows()
    d_fuel = ARMED_ANCHOR - CORPUS_FUEL
    coal["displacement_usd_mwh"] = coal["hr_mustrun"] * d_fuel
    coal["displacement_over_band"] = coal["displacement_usd_mwh"] / BAND

    cap = coal["Nameplate_MW"]
    hr_capwtd = float((coal["hr_mustrun"] * cap).sum() / cap.sum())
    disp_capwtd = hr_capwtd * d_fuel

    per_plant = [
        {
            "plant_code": int(r.Plant_Code),
            "plant_name": str(r.Plant_Name),
            "nameplate_mw": float(r.Nameplate_MW),
            "hr_mustrun_mmbtu_mwh": round(float(r.hr_mustrun), 4),
            "displacement_usd_mwh": round(float(r.displacement_usd_mwh), 4),
            "displacement_over_band": round(float(r.displacement_over_band), 4),
        }
        for r in coal.itertuples()
    ]
    per_plant.sort(key=lambda p: p["displacement_usd_mwh"])

    bound = json.loads(BOUND.read_text()) if BOUND.exists() else {}
    gneut = bound.get("G_NEUT", {}).get("coal_mustrun", {})

    rec = {
        "_provenance": {
            "probe": "scripts/probes/ercot196_ercot137_anchoring.py",
            "precommit": (
                "docs/PRECOMMIT-ercot196-rule18-grain-successor-2026-08-14.md §10"
            ),
            "filed_at": "ercot-192 DOF ledger, coal_offer_margin_level entry",
            "read_only": True,
            "nothing_rederived": True,
        },
        "mechanism_identity": {
            "site": "src/market_sim/data/fleet/legacy_bins.py:1055-1059",
            "applied": "mc[g,:] += coal_level - heat_rate[g]*coal_anchor - vom[g]",
            "effective_offer": (
                "offer(g,t) = coal_level + heat_rate[g] * (fuel[g,t] - coal_anchor)"
            ),
            "implication": (
                "at fuel == anchor the offer reduces EXACTLY to coal_level, and "
                "the fuel-response slope is the unit's OWN assembled heat rate — "
                "so the level is well-formed only if measured AT the anchor"
            ),
        },
        "armed": {
            "coal_offer_margin_level": ARMED_LEVEL,
            "coal_offer_margin_anchor": ARMED_ANCHOR,
            "band_usd_mwh": BAND,
            "corpus_res_hours_mean_fuel": CORPUS_FUEL,
            "anchor_minus_corpus_fuel": round(d_fuel, 6),
            "ercot192_pooled_point_raw": gneut.get("pooled_point"),
            "ercot192_per_subset_point": gneut.get("per_subset_point"),
            "ercot192_pool_arithmetic": gneut.get("pool_arithmetic"),
        },
        "sibling_convention": {
            "ERCOT_137_coal_mustrun": "pools the four subsets' bot_p50 RAW (NO anchoring)",
            "ERCOT_139_cc_committed": "removes the corpus's OWN measured fuel response",
            "ERCOT_140_coal_peak": "anchored on the corpus's own measured GAS response",
            "verdict": (
                "ERCOT-137 is the ONLY one of the three armed margin "
                "identifications that does not anchor — a sibling inconsistency "
                "in the committed derivation, not an artifact of applying a "
                "foreign arithmetic to it"
            ),
        },
        "displacement": {
            "capacity_weighted_hr_mmbtu_mwh": round(hr_capwtd, 4),
            "capacity_weighted_usd_mwh": round(disp_capwtd, 4),
            "capacity_weighted_over_band": round(disp_capwtd / BAND, 4),
            "min_usd_mwh": per_plant[0]["displacement_usd_mwh"],
            "max_usd_mwh": per_plant[-1]["displacement_usd_mwh"],
            "all_inside_band": bool(
                all(abs(p["displacement_over_band"]) < 1.0 for p in per_plant)
            ),
            "per_plant": per_plant,
        },
        "DISPOSITION": {
            "arming_unchanged": True,
            "rederived_here": False,
            "status": "RE-FILED WITH A MEASUREMENT",
            "why_not_repaired_here": (
                "Correcting the level is SOLVE-AFFECTING — it raises every coal "
                "_mustrun row's offer by its own heat rate x 0.0347 $/MMBtu "
                "(+0.33 to +0.39 $/MWh) — so it needs its own precommit, its own "
                "A/B and its own kill gates. Folding it into the ercot-196 "
                "rule-18 grain A/B would make that a two-delta comparison."
            ),
            "successor": (
                "a re-derivation of coal_offer_margin_level under the anchoring "
                "convention its two siblings already use, via "
                "scripts/data/derive_coal_offer_margin_anchor.py, with a "
                "single-delta A/B on the then-current keeper"
            ),
            "OWNER_QUESTION": (
                "Rule 23 [R-FROZEN-DERIVE] licenses a re-derivation when the "
                "SOURCE DATA updates, and forbids one because a residual moved. "
                "This trigger is NEITHER: it is a defect in the derivation's own "
                "convention, measured against the mechanism's own identity, with "
                "no residual consulted anywhere. Whether that is an admissible "
                "re-derivation trigger is an owner ruling, not a session call — "
                "so it is surfaced here rather than taken."
            ),
        },
    }
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec["displacement"] | rec["DISPOSITION"], indent=1)[:1600])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
