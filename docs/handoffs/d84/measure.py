"""capx D84 — the post-solve MEASUREMENT: consumers, published comparators, attribution.

Run AFTER `gates.py`. The gate verdict lives there and is not restated; this
records, at full magnitude and in both directions, everything the FINDING cites:

* the per-consumer move in DY 2025/2026 (the only window delivery year on the
  axis), against PRECOMMIT §5's enumeration;
* the D57 clearing identity reconciliation (fully-uncleared MW + the marginal
  unit's uncleared remainder == census - cleared) so no MW is unaccounted;
* the PUBLISHED comparators the move is reported against -- PJM's own DY
  2025/2026 BRA clearing price and cleared MW, and its Reliability Requirement
  -- read from the committed csvs, never typed. Rule 13: these are observables
  COMPARED AGAINST, never operands;
* the ATTRIBUTION of the newly-uncleared set to EIA-860 `Sector`, which is what
  explains why a 3,105.6 MW census move produces zero decision move.

Rule 29: nothing here is a gate. Rule 1/14: the residual is REPORTED, and it is
not the reason for the mechanism.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.fleet.eia860 import eia860_plant_sectors  # noqa: E402

CTL = (
    REPO
    / "results/hindcast/pjm-2021-2025-realized-t1h-d84-control/PJM/f736025631d0d27e"
)
ARM = (
    REPO
    / "results/hindcast/pjm-2021-2025-realized-t1h-d84-thermalvintage/PJM/b9fa47dedb6c3319"
)
TARGET = 2025
TARGET_DY = "2025/2026"

# Frame B (RPM cleared + committed FRR), the like-for-like whole-RTO comparator
# D66 §1.2 defines; carried here as D75-R's phase 0 carried it, sourced there.
PUB_CLEARED_FRAME_B = 145_883.0


def _led(root: Path, year: int) -> dict:
    return json.loads((root / f"evolution_{year}.json").read_text())


def published() -> dict:
    price = cleared = None
    for r in csv.DictReader(
        (REPO / "data/raw/capacity-market/auction-price/pjm/pjm.csv").open()
    ):
        if (
            r["delivery_year"] == TARGET_DY
            and r["area_type"] == "rto"
            and r["auction_round"] == "base_residual_auction"
        ):
            price, cleared = float(r["clearing_price"]), float(r["cleared_mw"])
    req = {}
    for r in csv.DictReader(
        (REPO / "data/raw/capacity-market/demand-curve/pjm/pjm.csv").open()
    ):
        if r.get("delivery_year") == TARGET_DY and r.get("metric") in {
            "reliability_requirement",
            "reliability_requirement_frr_adj",
            "ee_addback",
        }:
            req[r["metric"]] = float(r["y_value"])
    return {
        "bra_clearing_price_usd_per_mw_day": price,
        "bra_cleared_mw_frame_a_rpm_only": cleared,
        "cleared_mw_frame_b_rpm_plus_committed_frr": PUB_CLEARED_FRAME_B,
        "reliability_requirement_mw": req.get("reliability_requirement"),
        "source": (
            "data/raw/capacity-market/auction-price/pjm/pjm.csv (RTO, "
            "base_residual_auction) + demand-curve/pjm/pjm.csv; frame B from "
            "D66 §1.2 as carried by the D75-R phase 0 instrument"
        ),
    }


def consumers() -> dict:
    c, a = _led(CTL, TARGET), _led(ARM, TARGET)
    cc, ac = c["capacity_clearing"], a["capacity_clearing"]

    def pair(x, y):
        d = None
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            d = y - x
        return {"control": x, "arm": y, "delta": d}

    return {
        "MOVED_1_accredited_and_position": {
            "screen_entering_firm_mw": pair(
                c["screen_entering_firm_mw"], a["screen_entering_firm_mw"]
            ),
            "screen_reserve_position": pair(
                c["screen_reserve_position"], a["screen_reserve_position"]
            ),
            "capacity_reserve_position": pair(
                c["capacity_reserve_position"], a["capacity_reserve_position"]
            ),
        },
        "MOVED_4_d57_clearing": {
            k: pair(cc.get(k), ac.get(k))
            for k in (
                "census_mw",
                "census_position",
                "offered_mw",
                "price_takers_mw",
                "cleared_mw",
                "cleared_position",
                "price_usd_per_mw_day",
                "price_per_firm_mw_yr",
                "n_uncleared",
                "n_offers",
            )
        }
        | {
            "how": pair(cc.get("how"), ac.get("how")),
            "marginal_unit": pair(cc.get("marginal_unit"), ac.get("marginal_unit")),
            "uncleared_mw_by_fuel": pair(
                cc.get("uncleared_mw_by_fuel"), ac.get("uncleared_mw_by_fuel")
            ),
        },
        "NOT_MOVED_measured": {
            k: {"identical": c.get(k) == a.get(k), "value": c.get(k)}
            for k in (
                "screen_adequacy_requirement_mw",
                "adequacy_requirement_mw",
                "screen_peak_demand_mw",
                "peak_demand_mw",
                "retirements",
                "entry_decided_mw_by_tech",
                "floor_retained",
                "fleet_by_fuel_after",
                "renewable_credit_applied",
                "storage_firm_mw",
                "wind_cap_mw",
                "solar_cap_mw",
                "sector_gated",
            )
        },
    }


def clearing_reconciliation() -> dict:
    a = _led(ARM, TARGET)
    ac = a["capacity_clearing"]
    st = ac[
        "offer_stack"
    ]  # [unit_id, fuel, offer_usd_per_mw_day, accredited_mw, cleared]
    full_unc = sum(r[3] for r in st if r[4] is False)
    not_cleared = ac["census_mw"] - ac["cleared_mw"]
    return {
        "census_minus_cleared_mw": not_cleared,
        "fully_uncleared_mw": full_unc,
        "marginal_unit_uncleared_remainder_mw": not_cleared - full_unc,
        "identity_I1_price_takers_plus_offers_equals_census": {
            "computed": ac["price_takers_mw"] + sum(r[3] for r in st),
            "census_mw": ac["census_mw"],
            "abs_gap_mw": abs(
                ac["price_takers_mw"] + sum(r[3] for r in st) - ac["census_mw"]
            ),
        },
    }


def attribution() -> dict:
    """Why a 3,105.6 MW census move produces ZERO decision move."""
    sec = eia860_plant_sectors()
    a = _led(ARM, TARGET)
    ac = a["capacity_clearing"]
    st = ac["offer_stack"]
    rows = [r for r in st if r[4] is False] + [
        r for r in st if r[0] == ac["marginal_unit"]
    ]
    per: dict[str, dict] = {}
    for r in rows:
        m = re.search(r"_p(\d+)_", r[0])
        pid = int(m.group(1)) if m else -1
        e = per.setdefault(
            str(pid),
            {"eia860_sector": sec.get(pid), "tranches": 0, "accredited_mw": 0.0},
        )
        e["tranches"] += 1
        e["accredited_mw"] += r[3]
    return {
        "newly_uncleared_plants": per,
        "all_sector_1": all(v["eia860_sector"] == 1 for v in per.values()),
        "sector_1_share_of_uncleared_mw": (
            sum(v["accredited_mw"] for v in per.values() if v["eia860_sector"] == 1)
            / sum(v["accredited_mw"] for v in per.values())
        ),
        "why_it_matters": (
            "EIA-860 Sector 1 is a regulated electric utility. Under owner "
            "ruling Q56 (retirement_sector_gate, ARMED for PJM) a sector-1 unit "
            "still OFFERS its accredited MW into the D57 clearing at its net-ACR "
            "cap, but is PARTITIONED OUT of the step-3 economic exit decision. "
            "So the arm's entire newly-uncleared set is exempt from exiting BY "
            "CONSTRUCTION, and the screen's failing set can move without any "
            "retirement moving. This is a COLLISION BETWEEN TWO ARMED "
            "MECHANISMS, reported, not resolved here."
        ),
    }


def residual() -> dict:
    """The published residual, reported at full magnitude. NEVER the reason."""
    p = published()
    c, a = (
        _led(CTL, TARGET)["capacity_clearing"],
        _led(ARM, TARGET)["capacity_clearing"],
    )
    out = {}
    for name, pub, key in (
        (
            "cleared_mw_frame_b",
            p["cleared_mw_frame_b_rpm_plus_committed_frr"],
            "cleared_mw",
        ),
        ("cleared_mw_frame_a", p["bra_cleared_mw_frame_a_rpm_only"], "cleared_mw"),
        (
            "clearing_price",
            p["bra_clearing_price_usd_per_mw_day"],
            "price_usd_per_mw_day",
        ),
    ):
        gc, ga = c[key] - pub, a[key] - pub
        out[name] = {
            "published": pub,
            "control": c[key],
            "arm": a[key],
            "control_gap": gc,
            "arm_gap": ga,
            "direction": "TOWARD published"
            if abs(ga) < abs(gc)
            else "AWAY from published",
            "abs_gap_change": abs(ga) - abs(gc),
        }
    return out


def main() -> dict:
    return {
        "lane": "capx D84 measurement (post-solve; the gate verdict is in screen-gates.json)",
        "control_bundle": str(CTL.relative_to(REPO)),
        "arm_bundle": str(ARM.relative_to(REPO)),
        "target_delivery_year": TARGET_DY,
        "published_comparators": published(),
        "consumers": consumers(),
        "clearing_reconciliation": clearing_reconciliation(),
        "attribution": attribution(),
        "published_residual_reported_never_the_reason": residual(),
    }


if __name__ == "__main__":
    res = main()
    Path(__file__).with_name("measurement.json").write_text(
        json.dumps(res, indent=1) + "\n"
    )
    print(json.dumps(res["published_residual_reported_never_the_reason"], indent=1))
    print(
        json.dumps(
            {
                k: v
                for k, v in res["attribution"].items()
                if k != "newly_uncleared_plants"
            },
            indent=1,
        )
    )
    print(json.dumps(res["clearing_reconciliation"], indent=1))
