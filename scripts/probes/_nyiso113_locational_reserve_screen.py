"""nyiso-113 probe C — the rule-19 no-LP screen for NYISO's UNTESTED locational
reserve families, and the `measured_ramp_capability` transfer screen.

The session brief sets a hard precondition before ANY reserve-family arm may be
proposed: the in-LP reserve-FORMATION family is EXHAUSTED (nyiso-110 §10), so a
locational requirement is a new lever **only if it can be shown to bind where
the NYCA aggregate does not** — and that must be measured with no LP.

This screen answers it three ways, all from committed artifacts:

**§1 Domination algebra (decisive, no data needed).** A family row is
``sum_{z in region} R[c,z] + shortfall >= requirement``. A NEW family is
*provably inert* when an ALREADY-ARMED family forces its row slack: same
reserve class, a subset region, and a requirement at least as large. Applied to
the two untested candidates:

* `nyiso_east_reserve_families` adds `east_10min_spin` (330 MW, class 1, East)
  and `east_30min_total` (1,200 MW, class 0, East). Both are dominated —
  see the table this probe prints.
* `nyiso_li_locational_reserve` adds `li_10min_total` (120 MW, class 1) and
  `li_30min_total` (270/540 MW, class 0) scoped to **Long_Island alone**. No
  armed family is scoped to Zone K, so neither is dominated: they are genuinely
  new rows.

**§2 Where the aggregate is satisfied and a Zone-K row would not be.** The
nyiso-110 §10 refutation is that reserve-eligible HYDRO's own capability keeps
the aggregate rows slack in every hour (the keeper carries
`nyiso_hydro_reserve_eligible=True`, which unions hydro into BOTH the full and
quick-start classes). That argument is zone-blind — so this probe measures the
reserve-eligible capability **by model zone**. If NYISO's hydro is upstate and
Long Island carries none, a Zone-K-scoped row cannot be satisfied by the very
resource that makes the aggregate slack. That is exactly the brief's test.

**§3 Observed locational incidence.** The keeper's own per-zone `reserve_price`
across all three years. A locational family that binds prices its member zones
ABOVE the non-member zones; identical duals in every zone is a measurement that
**no** locational family has ever bound.

**§4 `measured_ramp_capability` (PJM `K`) transfer screen.** nyiso-110 §10
refuted the aggregate rho*P online binder, NOT a measured-MW per-asset
qualifier. The screen the brief asks for: is the reserve-eligible fleet's total
10-minute deliverable ramp anywhere near the 655 MW NYCA spinning requirement?
If the fleet's ramp capability dwarfs the requirement, a per-asset ramp
qualifier cannot bind the aggregate row and the transfer is inert before a
solve is spent.

Governance: reads the committed fleet, reserve spec and keeper sidecars only.
No price residual enters any test; the verdicts are statements about
representability and domination, never about fit (rule 1 [R-STRUCT], rule 25
[R-ISO-SCOPE] — every number is NYISO's own).

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso113_locational_reserve_screen.py
Writes: results/calibration/_nyiso113_locational_reserve_screen.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/nyiso112_combined_D"
OUT = REPO / "results/calibration/_nyiso113_locational_reserve_screen.json"
YEARS = (2023, 2024, 2025)

# NYCA spinning requirement (NYISO_RCPF_PRODUCTS nyca_10min_spin).
NYCA_SPIN_MW = 655.0


def reserve_class_of(name: str) -> int:
    """Reproduce spec.py's family->reserve-class rule for a family name."""
    if "spin_online" in name:
        return 2
    return 1 if ("10min" in name or "spin" in name) else 0


def domination_table() -> dict:
    """Which candidate families are forced slack by an already-armed family."""
    from market_sim.model.reserves.spec import (  # noqa: PLC0415
        NYISO_LI_30MIN_ONPEAK_MW,
        NYISO_RCPF_EAST_FAMILIES,
        NYISO_RCPF_LOCATIONAL,
        NYISO_RCPF_LOCATIONAL_LI,
        NYISO_RCPF_PRODUCTS,
    )

    all_zones = ("Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island")
    armed: list[dict] = []
    for name, req, _crit, pen in NYISO_RCPF_PRODUCTS:
        armed.append(
            {"name": name, "req": req, "pen": pen, "zones": set(all_zones), "cls": reserve_class_of(name)}
        )
    for region in NYISO_RCPF_LOCATIONAL.values():
        for name, req, _crit, pen in region["products"]:
            armed.append(
                {
                    "name": name,
                    "req": req,
                    "pen": pen,
                    "zones": set(region["zones"]),
                    "cls": reserve_class_of(name),
                }
            )

    candidates: list[dict] = []
    for name, req, _crit, pen in NYISO_RCPF_EAST_FAMILIES:
        candidates.append(
            {
                "flag": "nyiso_east_reserve_families",
                "name": name,
                "req": req,
                "pen": pen,
                "zones": set(NYISO_RCPF_LOCATIONAL["East"]["zones"]),
                "cls": reserve_class_of(name),
            }
        )
    for name, req, _crit, pen in NYISO_RCPF_LOCATIONAL_LI["LI"]["products"]:
        # li_30min_total's on-peak level is the binding one; report both.
        candidates.append(
            {
                "flag": "nyiso_li_locational_reserve",
                "name": name,
                "req": (NYISO_LI_30MIN_ONPEAK_MW if name == "li_30min_total" else req),
                "req_offpeak": req if name == "li_30min_total" else None,
                "pen": pen,
                "zones": set(NYISO_RCPF_LOCATIONAL_LI["LI"]["zones"]),
                "cls": reserve_class_of(name),
            }
        )

    rows = []
    for c in candidates:
        doms = [
            a
            for a in armed
            # Same reserve class, region a SUBSET of the candidate's (so its
            # R-sum is a lower bound on the candidate's), requirement at least
            # as large => the candidate's row is slack whenever the armed one is.
            if a["cls"] == c["cls"] and a["zones"] <= c["zones"] and a["req"] >= c["req"]
        ]
        rows.append(
            {
                "flag": c["flag"],
                "family": c["name"],
                "requirement_mw": c["req"],
                "requirement_offpeak_mw": c.get("req_offpeak"),
                "reserve_class": c["cls"],
                "zones": sorted(c["zones"]),
                "penalty_per_mw": c["pen"],
                "dominated_by": [
                    {
                        "family": d["name"],
                        "req": d["req"],
                        "zones": sorted(d["zones"]),
                        "penalty": d["pen"],
                        "slack_margin_mw": round(d["req"] - c["req"], 1),
                    }
                    for d in doms
                ],
                "verdict": "PROVABLY INERT (dominated)" if doms else "NEW BINDING ROW (not dominated)",
            }
        )
    return {"rows": rows}


def zonal_reserve_capability() -> dict:
    """Reserve-eligible capability by model zone — the nyiso-110 §10 zone test."""
    from market_sim.config.iso_configs import get_iso_config  # noqa: PLC0415
    from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: PLC0415
    from market_sim.data.outages import nysdec_peaker_restrictions  # noqa: PLC0415
    from market_sim.data.hydro import build_hydro_fleet  # noqa: PLC0415

    out: dict = {}
    for year in YEARS:
        fleet = load_fleet_from_csv("NYISO", get_iso_config("NYISO"), year=year)
        # Class 1 (10-minute quick-start) is the gas_ct/oil pool; class 0
        # (30-minute) draws the whole thermal reserve fleet.
        quick = defaultdict(float)
        full = defaultdict(float)
        for g in fleet:
            full[g.zone] += float(g.pmax_mw)
            if g.fuel_type in ("gas_ct", "oil") or g.plant_group in ("CT_PEAKER", "CT_CHP"):
                quick[g.zone] += float(g.pmax_mw)

        # Hydro — the resource nyiso-110 §10 says keeps the aggregate slack.
        hydro = defaultdict(float)
        zone_names = list(get_iso_config("NYISO").zone_names)
        try:
            # Same pair the keeper arms (--hydro-backfill-year 2024 +
            # --hydro-eia930-monthly, the nyiso-108 rule-14 input repair).
            hf, _ = build_hydro_fleet(
                "NYISO", year, zone_names, backfill_year=2024, eia930_monthly=True
            )
            for h in hf:
                hydro[getattr(h, "zone", "?")] += float(getattr(h, "pmax_mw", 0.0))
        except Exception as exc:  # noqa: BLE001 - reported, not fatal
            hydro["<unavailable>"] = str(exc)  # type: ignore[assignment]

        # 227-3 removes this much Zone-K quick-start inside the ozone window.
        dec_k = 0.0
        by_plant = defaultdict(list)
        for g in fleet:
            by_plant[int(g.plant_code)].append(g)
        for r in nysdec_peaker_restrictions(year, 8760):
            gens = [g for g in by_plant.get(r["plant_code"], []) if g.zone == "Long_Island"]
            if r["scope"] == "oil":
                gens = [
                    g
                    for g in gens
                    if g.fuel_type == "oil"
                    and (
                        not r["unit_ids"]
                        or any(str(g.unit_id).endswith(f"_{u}") for u in r["unit_ids"])
                    )
                ]
                dec_k += float(sum(g.pmax_mw for g in gens))
        out[year] = {
            "quick_start_mw_by_zone": {k: round(v, 1) for k, v in sorted(quick.items())},
            "full_thermal_mw_by_zone": {k: round(v, 1) for k, v in sorted(full.items())},
            "hydro_mw_by_zone": {
                k: (round(v, 1) if isinstance(v, float) else v) for k, v in sorted(hydro.items())
            },
            "li_quick_start_mw": round(quick.get("Long_Island", 0.0), 1),
            "li_hydro_mw": round(float(hydro.get("Long_Island", 0.0) or 0.0), 1)
            if isinstance(hydro.get("Long_Island", 0.0), float)
            else hydro.get("Long_Island"),
            "dec_227_3_li_quick_start_removed_mw": round(dec_k, 1),
            "li_quick_start_mw_in_ozone_window": round(quick.get("Long_Island", 0.0) - dec_k, 1),
        }
    return out


def observed_locational_incidence() -> dict:
    """Per-zone reserve duals on the keeper: has ANY locational family bound?"""
    import pandas as pd  # noqa: PLC0415

    out: dict = {}
    for year in YEARS:
        d = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        d = d[d["pass"] == "P1"]
        piv = d.pivot_table(index="hour", columns="zone", values="reserve_price")
        spread = (piv.max(axis=1) - piv.min(axis=1)).to_numpy()
        out[year] = {
            "hours_reserve_dual_positive": int((piv.max(axis=1) > 0).sum()),
            "max_cross_zone_reserve_spread": round(float(spread.max()), 8),
            "hours_with_any_cross_zone_spread": int((spread > 1e-6).sum()),
            "per_zone_positive_hours": {
                z: int((piv[z] > 0).sum()) for z in sorted(piv.columns)
            },
            "interpretation": (
                "a locational family that binds prices its member zones ABOVE "
                "non-member zones; a zero cross-zone spread in every hour means "
                "only the NYCA-wide families have ever bound"
            ),
        }
    return out


def ramp_capability_screen() -> dict:
    """`measured_ramp_capability` transfer screen: fleet ramp10 vs 655 MW spin."""
    from market_sim.config.iso_configs import get_iso_config  # noqa: PLC0415
    from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: PLC0415

    out: dict = {}
    try:
        from market_sim.data.fleet.arrays import _ramp10_capability  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        return {"error": f"_ramp10_capability unavailable: {exc}"}

    for year in YEARS:
        fleet = load_fleet_from_csv("NYISO", get_iso_config("NYISO"), year=year)
        import numpy as np  # noqa: PLC0415

        pmax = np.array([float(g.pmax_mw) for g in fleet])
        try:
            ramp = _ramp10_capability(fleet, pmax)
        except Exception as exc:  # noqa: BLE001
            return {"error": f"_ramp10_capability({year}) failed: {exc}"}
        tot = float(sum(ramp))
        n_pos = int(sum(1 for r in ramp if r > 0))
        by_zone = defaultdict(float)
        for g, r in zip(fleet, ramp):
            by_zone[g.zone] += float(r)
        out[year] = {
            "fleet_units": len(fleet),
            "units_with_positive_ramp10": n_pos,
            "total_ramp10_mw": round(tot, 1),
            "nyca_spin_requirement_mw": NYCA_SPIN_MW,
            "ratio_fleet_ramp_to_spin_req": round(tot / NYCA_SPIN_MW, 2),
            "ramp10_mw_by_zone": {k: round(v, 1) for k, v in sorted(by_zone.items())},
        }
    return out


def main() -> None:
    result = {
        "probe": "nyiso-113 locational reserve + ramp-capability screen (no LP)",
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "domination": domination_table(),
        "zonal_capability": zonal_reserve_capability(),
        "observed_locational_incidence": observed_locational_incidence(),
        "ramp_capability_screen": ramp_capability_screen(),
    }
    OUT.write_text(json.dumps(result, indent=2, default=str))

    print("=== §1 DOMINATION ALGEBRA ===")
    for r in result["domination"]["rows"]:
        print(f"\n  {r['flag']} :: {r['family']}")
        print(
            f"     req {r['requirement_mw']} MW  class {r['reserve_class']}  "
            f"pen ${r['penalty_per_mw']}/MW  zones {r['zones']}"
        )
        for d in r["dominated_by"]:
            print(
                f"     dominated by {d['family']} (req {d['req']} MW, zones {d['zones']}, "
                f"${d['penalty']}/MW) — margin {d['slack_margin_mw']} MW"
            )
        print(f"     => {r['verdict']}")

    print("\n=== §2 RESERVE-ELIGIBLE CAPABILITY BY ZONE ===")
    for year, blk in result["zonal_capability"].items():
        print(f"\n  {year}")
        print(f"     quick-start (class 1) MW: {blk['quick_start_mw_by_zone']}")
        print(f"     hydro MW                : {blk['hydro_mw_by_zone']}")
        print(
            f"     Long Island: quick-start {blk['li_quick_start_mw']} MW, "
            f"hydro {blk['li_hydro_mw']}; 227-3 removes "
            f"{blk['dec_227_3_li_quick_start_removed_mw']} MW in the ozone window "
            f"-> {blk['li_quick_start_mw_in_ozone_window']} MW"
        )

    print("\n=== §3 OBSERVED LOCATIONAL INCIDENCE (keeper) ===")
    for year, blk in result["observed_locational_incidence"].items():
        print(
            f"  {year}: reserve dual >0 in {blk['hours_reserve_dual_positive']} h; "
            f"max cross-zone spread {blk['max_cross_zone_reserve_spread']}; "
            f"hours with any spread {blk['hours_with_any_cross_zone_spread']}"
        )

    print("\n=== §4 measured_ramp_capability SCREEN ===")
    rc = result["ramp_capability_screen"]
    if "error" in rc:
        print(f"  {rc['error']}")
    else:
        for year, blk in rc.items():
            print(
                f"  {year}: fleet ramp10 {blk['total_ramp10_mw']} MW over "
                f"{blk['units_with_positive_ramp10']}/{blk['fleet_units']} units = "
                f"{blk['ratio_fleet_ramp_to_spin_req']}x the {NYCA_SPIN_MW} MW spin requirement"
            )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
