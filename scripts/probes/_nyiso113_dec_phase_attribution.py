"""nyiso-113 probe B — what the 2023-05-01 227-3 phase DID, and what it did not (no LP).

nyiso-112 armed `nysdec_peaker_rule_availability` and C3c moved in **2025
only**: 7 -> 14 hours >$300 against a measured 42, with 2023 (3 of 10) and 2024
(0 of 12) reported unchanged. The session brief's plausible read is that the
2023-restricted units are small upstate/LI GTs and only the 2025 phase touches
binding downstate capacity. **This probe measures that rather than assuming it**,
because the compliance file itself does not obviously support it: the
2023-05-01 phase carries four Zone-K (Long Island) plants and one Zone-J (NYC)
plant, and every model >$300 hour at NYISO is Long Island (nyiso-94).

Construction (all from committed artifacts — no solve):

A. **Phase composition.** Resolve every APPLIED 227-3 row (`ozone_season_oos`
   only — the STAR-designated, statutory-2030, retired and none-documented
   kinds are audit rows the overlay never applies) against the model's own
   loaded NYISO fleet for each year, so the reported MW is the MW the LP
   actually loses, per zone and per compliance phase. A row whose unit is
   absent from the fleet vintage is reported as a no-op, not as restricted MW.

B. **Near-gate price mass.** The keeper's own Long Island P1 price against the
   pre-227-3 arm (`nyiso111_rampenv_B`, the same-HEAD predecessor), counted at
   a ladder of thresholds. This separates "the phase did nothing" from "the
   phase moved the tail but not across the $300 gate" — two very different
   verdicts that a >$300 count alone cannot distinguish.

C. **Where the moved hours sit.** For each year, the hours whose LI price
   changed between the two arms: how many are inside the ozone window
   (h2880-6552), what their price was before and after, and how far the
   near-gate hours sit below $300.

D. **The roof.** Mainland (non-LI) max dual per year vs the LI max, so the
   "roof-blocked" reading (nyiso-94) is re-measured on the current keeper
   rather than carried forward from a superseded bundle.

Governance: reads committed bundles and the committed compliance CSV only.
It measures the mechanism's own footprint; it never proposes sizing anything
to the residual, and the compliance file carries a binding no-tuning clause
(PREREG-nyiso112) that this probe does not touch.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso113_dec_phase_attribution.py
Writes: results/calibration/_nyiso113_dec_phase_attribution.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/nyiso112_combined_D"
CONTROL = REPO / "results/calibration/nyiso111_rampenv_B"
OUT = REPO / "results/calibration/_nyiso113_dec_phase_attribution.json"
YEARS = (2023, 2024, 2025)
OZONE = (2880, 6552)
THRESHOLDS = (100, 150, 200, 250, 275, 300, 350, 400)

# Model zone for each NYISO load-zone letter used in the compliance CSV.
# NYISO's 11 load zones fold onto the model's five (config/iso_configs.py);
# only the letters the 227-3 file uses are needed here.
ZONE_OF_LETTER = {"G": "Lower_Hudson", "J": "NYC", "K": "Long_Island"}


def phase_composition() -> dict:
    """Resolve the applied 227-3 rows against the model's own NYISO fleet."""
    from market_sim.config.iso_configs import get_iso_config  # noqa: PLC0415
    from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: PLC0415
    from market_sim.data.outages import nysdec_peaker_restrictions  # noqa: PLC0415

    import pandas as pd  # noqa: PLC0415

    csv = pd.read_csv(REPO / "data/raw/reference/nysdec-227-3-peaker-compliance.csv")
    meta = {
        int(r.plant_code): {"name": r.plant_name, "letter": str(r.zone).strip()}
        for r in csv.itertuples(index=False)
    }
    # effective_date is the compliance PHASE label the regulation sets.
    phase_of = defaultdict(set)
    for r in csv.itertuples(index=False):
        if str(r.restriction).strip() == "ozone_season_oos":
            phase_of[int(r.plant_code)].add(str(r.effective_date)[:10])

    out: dict = {}
    for year in YEARS:
        fleet = load_fleet_from_csv("NYISO", get_iso_config("NYISO"), year=year)
        by_plant = defaultdict(list)
        for g in fleet:
            by_plant[int(g.plant_code)].append(g)

        rows = []
        for r in nysdec_peaker_restrictions(year, 8760):
            code, scope = r["plant_code"], r["scope"]
            gens = by_plant.get(code, [])
            if scope == "oil":
                hit = [
                    g
                    for g in gens
                    if g.fuel_type == "oil"
                    and (
                        not r["unit_ids"]
                        or any(str(g.unit_id).endswith(f"_{u}") for u in r["unit_ids"])
                    )
                ]
                restricted = float(sum(g.pmax_mw for g in hit))
            else:  # gas_ct — the plant's simple-cycle CT-class tranches
                hit = [g for g in gens if g.plant_group in ("CT_PEAKER", "CT_CHP")]
                class_mw = float(sum(g.pmax_mw for g in hit))
                mw = r["restricted_mw"]
                frac = 1.0 if mw is None else min(1.0, mw / max(class_mw, 1e-9))
                restricted = class_mw * frac
            m = meta.get(code, {})
            rows.append(
                {
                    "plant_code": code,
                    "plant_name": m.get("name", "?"),
                    "zone_letter": m.get("letter", "?"),
                    "model_zone": ZONE_OF_LETTER.get(m.get("letter", ""), "?"),
                    "scope": scope,
                    "phases": sorted(phase_of.get(code, [])),
                    "n_units_in_fleet": len(hit),
                    "restricted_mw": round(restricted, 2),
                    "window_hours": [r["h_lo"], r["h_hi"]],
                    "no_op_reason": "unit absent from fleet vintage" if not hit else None,
                }
            )

        by_zone = defaultdict(float)
        by_phase = defaultdict(float)
        for row in rows:
            by_zone[row["model_zone"]] += row["restricted_mw"]
            for p in row["phases"] or ["?"]:
                by_phase[p] += row["restricted_mw"]
        out[year] = {
            "rows": rows,
            "restricted_mw_by_model_zone": {k: round(v, 2) for k, v in sorted(by_zone.items())},
            "restricted_mw_by_phase": {k: round(v, 2) for k, v in sorted(by_phase.items())},
            "total_restricted_mw": round(sum(r["restricted_mw"] for r in rows), 2),
        }
    return out


def price_effect() -> dict:
    """Near-gate LI price mass and the moved hours, keeper vs pre-227-3 arm."""
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    out: dict = {}
    for year in YEARS:
        k = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        c = pd.read_parquet(CONTROL / f"hourly/system_{year}.parquet")
        k = k[k["pass"] == "P1"]
        c = c[c["pass"] == "P1"]
        kl = k[k.zone == "Long_Island"].sort_values("hour").reset_index(drop=True)
        cl = c[c.zone == "Long_Island"].sort_values("hour").reset_index(drop=True)
        d = kl.price.to_numpy() - cl.price.to_numpy()
        moved = np.flatnonzero(np.abs(d) > 1e-6)
        in_oz = moved[(moved >= OZONE[0]) & (moved < OZONE[1])]

        # Mainland roof: max dual over every zone that is not Long Island.
        mainland = k[k.zone != "Long_Island"]
        # Hours sitting just under the gate on the keeper.
        near = kl[(kl.price >= 250) & (kl.price < 300)].price.to_numpy()

        out[year] = {
            "li_counts_control": {str(t): int((cl.price > t).sum()) for t in THRESHOLDS},
            "li_counts_keeper": {str(t): int((kl.price > t).sum()) for t in THRESHOLDS},
            "li_max_control": round(float(cl.price.max()), 2),
            "li_max_keeper": round(float(kl.price.max()), 2),
            "n_hours_moved": int(moved.size),
            "n_hours_moved_in_ozone": int(in_oz.size),
            "moved_all_inside_ozone": bool(moved.size == in_oz.size),
            "max_price_delta": round(float(d.max()), 2) if moved.size else 0.0,
            "sum_abs_delta": round(float(np.abs(d).sum()), 2),
            "mainland_max_dual": round(float(mainland.price.max()), 2),
            "li_gap_to_gate_at_250_300": {
                "n": int(near.size),
                "closest_below_300": round(float(300 - near.max()), 2) if near.size else None,
            },
            "measured_h300": {"2023": 10, "2024": 12, "2025": 42}[str(year)],
        }
    return out


def main() -> None:
    result = {
        "probe": "nyiso-113 227-3 phase attribution",
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "control_bundle": str(CONTROL.relative_to(REPO)),
        "phase_composition": phase_composition(),
        "price_effect": price_effect(),
    }
    OUT.write_text(json.dumps(result, indent=2, default=str))

    print("=== A. 227-3 phase composition resolved against the model fleet ===")
    for year, blk in result["phase_composition"].items():
        print(f"\n{year}: total restricted {blk['total_restricted_mw']} MW")
        print(f"   by model zone : {blk['restricted_mw_by_model_zone']}")
        print(f"   by phase date : {blk['restricted_mw_by_phase']}")
        for r in blk["rows"]:
            flag = f"  <-- NO-OP ({r['no_op_reason']})" if r["no_op_reason"] else ""
            print(
                f"     {r['plant_name'][:28]:<30}{r['zone_letter']}/{r['model_zone']:<14}"
                f"{r['scope']:<8}{r['restricted_mw']:>8.1f} MW  n={r['n_units_in_fleet']}"
                f"  phases={r['phases']}{flag}"
            )

    print("\n=== B/C/D. Long Island price effect ===")
    for year, blk in result["price_effect"].items():
        print(f"\n{year}  (measured >$300 = {blk['measured_h300']} h)")
        print(f"   control >$: {blk['li_counts_control']}")
        print(f"   keeper  >$: {blk['li_counts_keeper']}")
        print(f"   LI max  : {blk['li_max_control']} -> {blk['li_max_keeper']}")
        print(f"   mainland max dual (roof): {blk['mainland_max_dual']}")
        print(
            f"   hours moved: {blk['n_hours_moved']} "
            f"(in ozone {blk['n_hours_moved_in_ozone']}, "
            f"all inside = {blk['moved_all_inside_ozone']}), "
            f"max delta {blk['max_price_delta']}"
        )
        print(f"   near-gate [250,300): {blk['li_gap_to_gate_at_250_300']}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
