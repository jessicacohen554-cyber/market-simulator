"""capx D75-R — phase 0 for the PJM VRE ELCC delivery-year vintage axis (ZERO LP).

Charter step 3. Measures the BUILT mechanism's accredited VRE MW by class, per
delivery year, under both vintages, and applies the chartered gate: the SIGN,
PER YEAR (director ruling R3 — D75 §3's per-year table replaces the superseded
window-wide magnitude band, which had been derived from a rating set that is no
longer operative).

**What makes this a phase 0 and not a re-run of D75's arithmetic.** D75 measured
the same quantity by hand, on paper, with nothing built. This instrument calls
the SHIPPED CODE PATH — ``resolve_renewable_capacity_credit`` /
``renewable_credits_applied`` / ``accredited_firm_capacity_mw`` — under a control
config and an armed one, so what is gated is the mechanism as it will actually
run in the screen. D75's published numbers are then used as an INDEPENDENT
CHECK on the build (``d75_cross_check``): two lanes, two constructions, the same
MW, or the build is wrong.

**Zero LP, and no fleet rebuild either.** The charter names a ``fleet_only``
rebuild as the phase-0 vehicle. It is not needed here, and the reason is
measured rather than assumed: every arm-A ledger's own ``fleet_by_fuel_after``
carries NO wind or solar key in ANY year (2021-2025), i.e. PJM's persistent
fleet holds no VRE units — so the class's whole nameplate is the zonal pool, the
penetration axis is the pool, and accredited VRE is pool x credit exactly. The
instrument asserts that from the committed ledgers (``fleet_vre_check``) instead
of taking it on trust; a rebuild could only reproduce it at the cost of minutes.

Two sides, both read-only:

* MODEL — ``results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/
  f0e050e820c1159a/evolution_<year>.json`` (D57 arm A, the shipped PJM posture).
* PUBLISHED — PJM's own per-delivery-year ELCC Class Ratings, now IN THE
  REPOSITORY as of this lane's step-1 intake
  (``data/raw/capacity-market/elcc/pjm/pjm.csv``), which is why this instrument
  reads ratings from the CODE registry rather than re-typing them: the registry
  is reconciled byte-for-byte to those committed rows by
  ``tests/unit/data/test_renewable_elcc_curves.py``.

The accreditation base (established in code by D75 §1.4, re-stated here): the
screen accredits ``prior_results``' pools at the CURRENT model year's delivery
year, so delivery year Y/Y+1 <= model year Y <= the pools recorded in
``evolution_{Y-1}``.

Rule 13: every published figure is an observable compared against, never an
input. Rule 21: nothing here is fitted to a residual. Rule 29: this gate may
KILL an arm; it can never promote one, and it is never read against the target
residual.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.capacity_market import (  # noqa: E402
    PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE,
    RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity import (  # noqa: E402
    renewable_credits_applied,
    vre_accreditation_vintage_armed,
)

ARM_A = REPO / (
    "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a"
)
DEMAND_CURVE_CSV = REPO / "data/raw/capacity-market/demand-curve/pjm/pjm.csv"

# Delivery years, and the model year whose screen prices each. 2022/23 is
# PRE-ELCC (PJM's construct began with the 2023/2024 BRA) and is carried only so
# the instrument can show the arm is inert there; rulings R2 fixes the in-scope
# set at the three below it.
DY_TO_MODEL_YEAR = {f"{y}/{y + 1}": y for y in (2022, 2023, 2024, 2025)}
IN_SCOPE_DY = ("2023/2024", "2024/2025", "2025/2026")

# THE PRE-DECLARED SIGNS, copied VERBATIM from PRECOMMIT-capx-d75-pjm-vre-elcc-
# vintage-2026-09-06.md §6, which was pushed before any lane measured against
# them. This lane grades itself against another lane's ex-ante record; that is
# the whole point of §6 existing.
D75_PREDECLARED = {
    "sign": "DOWN in all three in-scope delivery years, at every candidate mix",
    "magnitude_at_pjm_published_mix_mw": {
        "2023/2024": -754.6,
        "2024/2025": -332.9,
        "2025/2026": -148.3,
    },
    "window_total_mw": -1235.8,
    "position": (
        "residual WIDENS in 2024/25 and 2025/26 (model below published) and "
        "NARROWS in 2023/24 (model above published)"
    ),
}

# PJM's published cleared UCAP in both of D66 §1.2's frames (its §1.2/§1.4
# tables; sources sha256-verified there). Frame B = RPM + committed FRR, the
# like-for-like whole-RTO comparator; Frame A = RPM only, D57/D61's comparator.
PUB_CLEARED = {
    "2023/2024": {"frame_b": 171_605.0, "frame_a": 144_870.6},
    "2024/2025": {"frame_b": 172_961.0, "frame_a": 147_478.9},
    "2025/2026": {"frame_b": 145_883.0, "frame_a": 135_684.0},
}


def _ledger(year: int) -> dict:
    return json.loads((ARM_A / f"evolution_{year}.json").read_text())


def fleet_vre_check() -> dict:
    """Assert from the committed ledgers that PJM's fleet holds no VRE units.

    The premise that lets `accredited VRE = pool x credit` and makes a
    `fleet_only` rebuild unnecessary. Measured, per year, not assumed.
    """
    out = {}
    for year in range(2021, 2026):
        led = _ledger(year)
        fleet = led.get("fleet_by_fuel_after") or led.get("fleet_by_fuel_before") or {}
        out[str(year)] = {
            "fuels": sorted(fleet),
            "vre_mw_in_fleet": {
                k: v for k, v in fleet.items() if k in ("wind", "solar", "offshore_wind")
            },
        }
    out["holds"] = all(not v["vre_mw_in_fleet"] for k, v in out.items() if k != "holds")
    return out


def accreditation_pools() -> dict[str, dict]:
    """VRE pools the screen accredits, per delivery year.

    ``evolution_{Y-1}``'s recorded pools — what ``prior_results`` carries into
    model year Y's screen. ``evolution_2022`` predates the adequacy-ledger block
    (it emits the screen and clearing blocks but no ``wind_cap_mw`` /
    ``solar_cap_mw`` / ``renewable_credit_applied`` / ``storage_firm_mw``), so
    DY 2023/24 falls back to the roll-forward D66 used — the 2021 base pools
    plus every ``renewable_additions`` row decided in 2022, which is empty — and
    says so in its ``provenance``. That ledger gap is ROUTED, not repaired here
    (FINDING-capx-d75 §6 item 3).
    """
    out: dict[str, dict] = {}
    for dy, model_year in DY_TO_MODEL_YEAR.items():
        prior = _ledger(model_year - 1)
        if prior.get("wind_cap_mw") is not None:
            out[dy] = {
                "wind_mw": prior["wind_cap_mw"],
                "solar_mw": prior["solar_cap_mw"],
                "provenance": f"evolution_{model_year - 1}.json (prior_results)",
            }
            continue
        base = _ledger(2021)
        pools = {"wind": base["wind_cap_mw"], "solar": base["solar_cap_mw"]}
        for add in prior.get("renewable_additions") or []:
            if add.get("tech") in pools:
                pools[add["tech"]] += float(add["mw"])
        out[dy] = {
            "wind_mw": pools["wind"],
            "solar_mw": pools["solar"],
            "provenance": (
                f"evolution_{model_year - 1}.json carries no adequacy block; "
                "reconstructed as evolution_2021 pools + that year's "
                "renewable_additions (empty) — ROUTED, see FINDING §6 item 3"
            ),
        }
    return out


def published_requirements() -> dict[str, dict[str, float]]:
    """Both frames' published requirement operands, from the in-repo CSV."""
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


def _config(armed: bool) -> ScenarioConfig:
    """The two phase-0 postures, as the harness resolves them for PJM.

    Both carry the D57 arm-A gates (``_pjm_config``'s own overrides arm the two
    D48 fields; the ELCC curve gate ships on), so control and arm differ in
    EXACTLY ONE field — which is the confinement the screen then re-checks on a
    real solve.
    """
    return ScenarioConfig(
        mode="forecast",
        iso="PJM",
        hindcast=True,
        renewable_elcc_curves=True,
        pjm_accreditation_design_vintage=True,
        pjm_demand_response_supply=True,
        pjm_vre_accreditation_vintage=armed,
    )


def main() -> dict:
    control, armed = _config(False), _config(True)
    pools = accreditation_pools()
    reqs = published_requirements()

    out: dict = {
        "lane": "capx D75-R phase 0 (zero LP)",
        "arm_a_bundle": str(ARM_A.relative_to(REPO)),
        "gate": (
            "PER YEAR, ON THE SIGN: accredited VRE MW must fall in every "
            "in-scope delivery year (director ruling R3). A STOP gate only "
            "(rule 29): it may kill the arm, never promote it, and it is not "
            "read against the target residual."
        ),
        "declared_solar_mix": {
            "fixed_tilt_share": PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE,
            "basis": (
                "PJM ELCC/RRS Table 5 pp.16-17, 2026/2027 BRA installed MW "
                "(Fixed-Tilt 1,189 / Tracking 8,713) — a declared CROSS-VINTAGE "
                "reconciliation under rule 14's misalignment exception "
                "(director ruling R1), never a fitted weight"
            ),
        },
        "gate_armed_check": {
            "control": vre_accreditation_vintage_armed(control, "PJM"),
            "arm": vre_accreditation_vintage_armed(armed, "PJM"),
        },
        "fleet_vre_check": fleet_vre_check(),
        "accreditation_pools": pools,
        "d75_predeclared": D75_PREDECLARED,
        "years": {},
    }

    for dy, model_year in DY_TO_MODEL_YEAR.items():
        p = pools[dy]
        led = _ledger(model_year)
        clearing = led.get("capacity_clearing") or {}
        row: dict = {
            "model_year": model_year,
            "in_scope": dy in IN_SCOPE_DY,
            "wind_pool_mw": p["wind_mw"],
            "solar_pool_mw": p["solar_mw"],
            "pool_provenance": p["provenance"],
            "census_mw": clearing.get("census_mw"),
            "census_position": clearing.get("census_position"),
            "requirement_mw": clearing.get("requirement_mw"),
        }

        # THE CODE PATH, both postures. No arithmetic is done here that the
        # solve will not do: the credits come from the shipped resolver.
        for label, config in (("incumbent", control), ("vintaged", armed)):
            credits = renewable_credits_applied(
                [],
                p["wind_mw"],
                p["solar_mw"],
                "PJM",
                peak_demand_mw=led.get("screen_peak_demand_mw")
                or led.get("peak_demand_mw"),
                elcc_curves_enabled=True,
                config=config,
                accreditation_year=model_year,
            )
            row[label] = {
                "credit": {k: round(v, 6) for k, v in credits.items()},
                "accredited_wind_mw": round(p["wind_mw"] * credits["wind"], 3),
                "accredited_solar_mw": round(p["solar_mw"] * credits["solar"], 3),
                "accredited_vre_mw": round(
                    p["wind_mw"] * credits["wind"] + p["solar_mw"] * credits["solar"], 3
                ),
            }

        delta = row["vintaged"]["accredited_vre_mw"] - row["incumbent"]["accredited_vre_mw"]
        row["delta_accredited_vre_mw"] = round(delta, 3)
        row["delta_by_class_mw"] = {
            "wind": round(
                row["vintaged"]["accredited_wind_mw"]
                - row["incumbent"]["accredited_wind_mw"],
                3,
            ),
            "solar": round(
                row["vintaged"]["accredited_solar_mw"]
                - row["incumbent"]["accredited_solar_mw"],
                3,
            ),
        }
        row["published_ratings_applied"] = (
            {
                k: round(v, 6)
                for k, v in RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"][dy].items()
            }
            if dy in RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"]
            else None
        )

        # Position at full magnitude, both of D66 §1.2's frames. PJM's fleet
        # carries no VRE units (fleet_vre_check), and PJM's internal-supply
        # accounting ratio is the neutral 1.0, so the accredited-VRE delta
        # flows 1:1 into the census.
        if clearing and dy in PUB_CLEARED and dy in reqs:
            after = clearing["census_mw"] + delta
            pos_before = clearing["census_position"]
            pos_after = after / clearing["requirement_mw"]
            pub_pos = {f: PUB_CLEARED[dy][f] / reqs[dy][f] for f in ("frame_a", "frame_b")}
            row["position"] = {
                "model_before": round(pos_before, 5),
                "model_after": round(pos_after, 5),
                "delta_pt": round(100.0 * (pos_after - pos_before), 4),
                "published": {f: round(v, 5) for f, v in pub_pos.items()},
                "gap_pt_before": {
                    f: round(100.0 * (v - pos_before), 3) for f, v in pub_pos.items()
                },
                "gap_pt_after": {
                    f: round(100.0 * (v - pos_after), 3) for f, v in pub_pos.items()
                },
            }
            row["position"]["residual"] = {
                f: (
                    "narrows"
                    if abs(pub_pos[f] - pos_after) < abs(pub_pos[f] - pos_before)
                    else "widens"
                )
                for f in ("frame_a", "frame_b")
            }
        out["years"][dy] = row

    # --- THE GATE: per year, on the sign -------------------------------------#
    per_year = {}
    for dy in IN_SCOPE_DY:
        d = out["years"][dy]["delta_accredited_vre_mw"]
        per_year[dy] = {
            "delta_mw": d,
            "declared_sign": "DOWN",
            "sign_holds": d < 0.0,
            "d75_predeclared_magnitude_mw": D75_PREDECLARED[
                "magnitude_at_pjm_published_mix_mw"
            ][dy],
        }
    out["sign_gate"] = {
        "per_year": per_year,
        "PASS": all(v["sign_holds"] for v in per_year.values()),
        "window_total_delta_mw": round(
            sum(out["years"][dy]["delta_accredited_vre_mw"] for dy in IN_SCOPE_DY), 3
        ),
    }

    # --- INDEPENDENT CHECK: the built code vs D75's hand arithmetic ---------- #
    # Two lanes, two constructions, one number. A miss here is a build defect,
    # not a disagreement about PJM's ratings.
    out["d75_cross_check"] = {
        dy: {
            "d75_hand_mw": D75_PREDECLARED["magnitude_at_pjm_published_mix_mw"][dy],
            "d75r_code_mw": out["years"][dy]["delta_accredited_vre_mw"],
            "abs_diff_mw": round(
                abs(
                    out["years"][dy]["delta_accredited_vre_mw"]
                    - D75_PREDECLARED["magnitude_at_pjm_published_mix_mw"][dy]
                ),
                3,
            ),
        }
        for dy in IN_SCOPE_DY
    }
    out["d75_cross_check"]["max_abs_diff_mw"] = max(
        v["abs_diff_mw"] for v in out["d75_cross_check"].values() if isinstance(v, dict)
    )

    # --- INERTNESS: the pre-ELCC year the arm must not touch ---------------- #
    out["inert_check"] = {
        "2022/2023": {
            "delta_accredited_vre_mw": out["years"]["2022/2023"][
                "delta_accredited_vre_mw"
            ],
            "expected": 0.0,
            "holds": out["years"]["2022/2023"]["delta_accredited_vre_mw"] == 0.0,
            "why": (
                "PRE-ELCC: PJM's ELCC construct first applied to the 2023/2024 "
                "BRA, so this delivery year has no published class rating of "
                "any kind and is out of scope (ruling R2). The registry has no "
                "row and the resolver falls through to the incumbent curve."
            ),
        }
    }
    return out


if __name__ == "__main__":
    result = main()
    path = Path(__file__).with_suffix(".json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["sign_gate"], indent=2))
    print(json.dumps(result["d75_cross_check"], indent=2))
    print(json.dumps(result["inert_check"], indent=2))
    print(f"\nwrote {path.relative_to(REPO)}")
