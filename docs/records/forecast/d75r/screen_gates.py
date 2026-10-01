"""capx D75-R — the SCREEN gate table (rule 29 [R-SCREEN]), and the full-window A/B.

Differences an ARM bundle against its SAME-HEAD CONTROL and reports the four
structural legs the PRECOMMIT pre-declared, plus the position at full magnitude
on both of D66 §1.2's frames. Pure read of committed solve artifacts; no LP.

The gate is a STOP gate only: it may kill the arm, it may never promote one, and
no leg is read against the target residual (PRECOMMIT §6).

Usage:
    python docs/handoffs/d75r/screen_gates.py <control_dir> <arm_dir> [--label L]
where each dir is the per-key bundle, e.g.
    results/hindcast/d75r-screen-ctl/PJM/afda79ba04cbfdbf
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

# Phase 0's arithmetic, which the identity leg checks the SOLVE against. Credits
# are the shipped registry's; accredited MW are pool x credit on the committed
# arm-A pools (docs/handoffs/d75r/vre-elcc-vintage-phase0-2026-09-06.json).
PHASE0 = {
    2022: {"dy": "2022/2023", "credit": None, "delta_mw": 0.0},
    2023: {
        "dy": "2023/2024",
        "credit": {"wind": 0.15, "solar": 0.520788},
        "delta_mw": -754.633,
    },
    2024: {
        "dy": "2024/2025",
        "credit": {"wind": 0.21, "solar": 0.479587},
        "delta_mw": -332.854,
    },
    2025: {
        "dy": "2025/2026",
        "credit": {"wind": 0.38, "solar": 0.135197},
        "delta_mw": -148.315,
    },
}
INCUMBENT_CREDIT = {"wind": 0.41, "solar": 0.1064}

PUB_CLEARED = {
    "2023/2024": {"frame_b": 171_605.0, "frame_a": 144_870.6},
    "2024/2025": {"frame_b": 172_961.0, "frame_a": 147_478.9},
    "2025/2026": {"frame_b": 145_883.0, "frame_a": 135_684.0},
}
DEMAND_CURVE_CSV = REPO / "data/raw/capacity-market/demand-curve/pjm/pjm.csv"


def published_requirements() -> dict[str, dict[str, float]]:
    import csv

    rows: dict[str, dict[str, float]] = {}
    with DEMAND_CURVE_CSV.open(newline="") as fh:
        for rec in csv.DictReader(fh):
            if rec["metric"] in {
                "reliability_requirement",
                "reliability_requirement_frr_adj",
                "ee_addback",
            }:
                rows.setdefault(rec["delivery_year"], {})[rec["metric"]] = float(
                    rec["y_value"]
                )
    need = {"reliability_requirement", "reliability_requirement_frr_adj", "ee_addback"}
    return {
        dy: {
            "frame_b": v["reliability_requirement"],
            "frame_a": v["reliability_requirement_frr_adj"] + v["ee_addback"],
        }
        for dy, v in rows.items()
        if need <= v.keys()
    }


def _led(d: Path, year: int) -> dict | None:
    p = d / f"evolution_{year}.json"
    return json.loads(p.read_text()) if p.is_file() else None


def _thermal_firm_by_fuel(led: dict) -> dict[str, float]:
    """Accredited thermal MW by fuel, from the clearing stack's own rows.

    The CONFINEMENT leg's thermal operand: it must be byte-identical between
    arms, since the D48 thermal half is armed in BOTH and this mechanism
    touches supply's VRE term only.
    """
    out: dict[str, float] = {}
    for row in (led.get("capacity_clearing") or {}).get("offer_stack") or []:
        # offer_stack rows are positional; the fuel and accredited MW are read
        # defensively so a schema change surfaces as a None rather than a lie.
        if isinstance(row, dict):
            fuel, mw = row.get("fuel"), row.get("accredited_mw")
        else:
            fuel, mw = (
                # Positional row: [unit_id, fuel, offer $/MW-day, ACCREDITED
                # MW, cleared flag]. Index 3 is the accredited MW; index 2 is
                # the OFFER and index 4 a bool — the misread D62 recorded
                # against itself, named here rather than re-made.
                (row[1] if len(row) > 1 else None),
                (row[3] if len(row) > 3 else None),
            )
        if fuel is None or mw is None:
            continue
        out[str(fuel)] = out.get(str(fuel), 0.0) + float(mw)
    return {k: round(v, 6) for k, v in out.items()}


def year_row(ctl: dict, arm: dict, year: int, prior_ctl: dict | None = None) -> dict:
    exp = PHASE0.get(year, {})
    dy = exp.get("dy")
    cc_c = ctl.get("capacity_clearing") or {}
    cc_a = arm.get("capacity_clearing") or {}
    cr_c = ctl.get("renewable_credit_applied") or {}
    cr_a = arm.get("renewable_credit_applied") or {}
    # THE POOLS THE SCREEN ACCREDITS are ``prior_results``' — i.e.
    # evolution_{Y-1}'s — not this year's end-of-year pools (which include the
    # year's own additions). Using the wrong vintage here inverts the sign of
    # the reported delta in any year with VRE additions, which is exactly the
    # instrument defect this lane caught on its own full-window run and fixed.
    # `gate_identity.holds` was always computed on the CREDITS and so was never
    # affected; only the reported MW were.
    _pools_src = prior_ctl if prior_ctl is not None else ctl
    wind_pool = _pools_src.get("wind_cap_mw")
    solar_pool = _pools_src.get("solar_cap_mw")

    row: dict = {
        "delivery_year": dy,
        "renewable_credit_applied": {"control": cr_c, "arm": cr_a},
        "expected_credit_arm": exp.get("credit"),
        "pools_end_of_year": {
            "control": {"wind": wind_pool, "solar": solar_pool},
            "arm": {"wind": arm.get("wind_cap_mw"), "solar": arm.get("solar_cap_mw")},
        },
        "screen_entering_firm_mw": {
            "control": ctl.get("screen_entering_firm_mw"),
            "arm": arm.get("screen_entering_firm_mw"),
        },
        "screen_adequacy_requirement_mw": {
            "control": ctl.get("screen_adequacy_requirement_mw"),
            "arm": arm.get("screen_adequacy_requirement_mw"),
        },
        "screen_reserve_position": {
            "control": ctl.get("screen_reserve_position"),
            "arm": arm.get("screen_reserve_position"),
        },
        "storage_firm_mw": {
            "control": ctl.get("storage_firm_mw"),
            "arm": arm.get("storage_firm_mw"),
        },
        "clearing": {
            f: {"control": cc_c.get(f), "arm": cc_a.get(f)}
            for f in (
                "census_mw",
                "census_position",
                "requirement_mw",
                "cleared_mw",
                "cleared_position",
                "price_usd_per_mw_day",
                "n_offers",
                "n_uncleared",
                "price_takers_mw",
                "how",
            )
        },
        "retirements_total_mw": {
            "control": round(
                sum(float(r.get("mw", 0.0)) for r in ctl.get("retirements") or []),
                3,
            ),
            "arm": round(
                sum(float(r.get("mw", 0.0)) for r in arm.get("retirements") or []),
                3,
            ),
        },
        "thermal_accredited_by_fuel_identical": (
            _thermal_firm_by_fuel(ctl) == _thermal_firm_by_fuel(arm)
        ),
    }

    # --- LEG 1: IDENTITY — the solve's own credits are phase 0's ------------ #
    if exp.get("credit"):
        row["gate_identity"] = {
            "expected_arm_credit": exp["credit"],
            "solved_arm_credit": cr_a,
            "holds": all(
                cr_a.get(k) is not None and abs(cr_a[k] - v) < 1e-9
                for k, v in exp["credit"].items()
            ),
            "control_on_incumbent": all(
                cr_c.get(k) is not None and abs(cr_c[k] - v) < 1e-9
                for k, v in INCUMBENT_CREDIT.items()
            ),
        }
        if wind_pool is not None and solar_pool is not None:
            # The accredited-VRE delta the SOLVE realises, on its own pools.
            d_solved = wind_pool * (
                cr_a.get("wind", 0.0) - cr_c.get("wind", 0.0)
            ) + solar_pool * (cr_a.get("solar", 0.0) - cr_c.get("solar", 0.0))
            row["gate_identity"]["accredited_vre_delta_mw_solved"] = round(d_solved, 3)
            row["gate_identity"]["accredited_vre_delta_mw_phase0"] = exp["delta_mw"]
    else:
        # Out-of-scope year: LEG 4, inertness.
        row["gate_inert"] = {
            "credits_identical": cr_c == cr_a,
            "census_identical": cc_c.get("census_mw") == cc_a.get("census_mw"),
            "requirement_identical": ctl.get("screen_adequacy_requirement_mw")
            == arm.get("screen_adequacy_requirement_mw"),
            "retirements_identical": (
                row["retirements_total_mw"]["control"]
                == row["retirements_total_mw"]["arm"]
            ),
        }
        row["gate_inert"]["holds"] = all(
            v for k, v in row["gate_inert"].items() if k != "holds"
        )

    # --- LEG 2: CONFINEMENT — requirement / thermal / storage unmoved ------- #
    row["gate_confinement"] = {
        "requirement_identical": ctl.get("screen_adequacy_requirement_mw")
        == arm.get("screen_adequacy_requirement_mw"),
        "thermal_accredited_identical": row["thermal_accredited_by_fuel_identical"],
        "storage_firm_identical": ctl.get("storage_firm_mw")
        == arm.get("storage_firm_mw"),
    }
    row["gate_confinement"]["holds"] = all(row["gate_confinement"].values())

    # --- position at full magnitude, both frames ---------------------------- #
    reqs = published_requirements()
    if dy in PUB_CLEARED and dy in reqs and cc_c.get("census_position") is not None:
        pub = {f: PUB_CLEARED[dy][f] / reqs[dy][f] for f in ("frame_a", "frame_b")}
        pc, pa = cc_c["census_position"], cc_a.get("census_position")
        row["position"] = {
            "published": {f: round(v, 5) for f, v in pub.items()},
            "model_control": round(pc, 5),
            "model_arm": round(pa, 5) if pa is not None else None,
            "gap_pt_control": {f: round(100.0 * (v - pc), 3) for f, v in pub.items()},
            "gap_pt_arm": (
                {f: round(100.0 * (v - pa), 3) for f, v in pub.items()}
                if pa is not None
                else None
            ),
        }
        if pa is not None:
            row["position"]["residual"] = {
                f: (
                    "narrows"
                    if abs(pub[f] - pa) < abs(pub[f] - pc)
                    else (
                        "unchanged"
                        if abs(pub[f] - pa) == abs(pub[f] - pc)
                        else "widens"
                    )
                )
                for f in ("frame_a", "frame_b")
            }
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("control", type=Path)
    ap.add_argument("arm", type=Path)
    ap.add_argument("--label", default="screen")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    out: dict = {
        "label": args.label,
        "control": str(args.control),
        "arm": str(args.arm),
        "years": {},
    }
    for year in range(2021, 2026):
        ctl, arm = _led(args.control, year), _led(args.arm, year)
        if ctl is None or arm is None:
            continue
        # The accrediting pools are evolution_{Y-1}'s. Where that ledger
        # carries no adequacy block (the evolution_2022 gap this lane routes),
        # roll forward from the last ledger that does, exactly as phase 0 does.
        prior = _led(args.control, year - 1)
        if prior is not None and prior.get("wind_cap_mw") is None:
            base = _led(args.control, year - 2)
            if base is not None and base.get("wind_cap_mw") is not None:
                pools = {
                    "wind": base["wind_cap_mw"],
                    "solar": base["solar_cap_mw"],
                }
                for add in prior.get("renewable_additions") or []:
                    if add.get("tech") in pools:
                        pools[add["tech"]] += float(add["mw"])
                prior = {
                    "wind_cap_mw": pools["wind"],
                    "solar_cap_mw": pools["solar"],
                }
        out["years"][str(year)] = year_row(ctl, arm, year, prior)

    legs = {"identity": [], "confinement": [], "inert": []}
    for y, row in out["years"].items():
        for name, key in (
            ("identity", "gate_identity"),
            ("confinement", "gate_confinement"),
            ("inert", "gate_inert"),
        ):
            if key in row:
                legs[name].append((y, bool(row[key].get("holds"))))
    out["gate_summary"] = {
        name: {"years": dict(v), "PASS": all(h for _, h in v) if v else None}
        for name, v in legs.items()
    }
    out["GATE_PASS"] = all(
        v["PASS"] for v in out["gate_summary"].values() if v["PASS"] is not None
    )

    path = args.out or (Path(__file__).parent / f"{args.label}-gates.json")
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["gate_summary"], indent=2))
    print("GATE_PASS:", out["GATE_PASS"])
    print("wrote", path.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
