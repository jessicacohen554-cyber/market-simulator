"""capx D75 — PJM VRE ELCC accreditation-vintage phase 0 (ZERO LP).

Measures, from COMMITTED artifacts only, what a delivery-year vintage axis on
``RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]`` would do to the model's accredited VRE
MW and to the D66 census position, for every delivery year the D57 arm-A
hindcast screens.  Nothing is built, nothing is armed, and no solve is run.

**The accreditation base, established from the code rather than assumed.**  The
census the position is measured on is produced by the retirement screen, and
that screen accredits ``prior_results``' pools at the CURRENT model year's
delivery year: ``runner.py`` L2037-2039 / L2116-2124 pass
``prior_results["wind_cap_mw"]`` / ``["solar_cap_mw"]`` with
``accreditation_year=year``, and ``retirements.py`` L3567 threads the same pools
into ``_settle_capacity_supply_clearing`` → ``accredited_firm_capacity_mw``.  So

    delivery year Y/Y+1  ⟸  model year Y  ⟸  pools recorded in evolution_{Y-1}

(``capacity_deliverability.resolve_delivery_year("PJM", Y) == f"{Y}/{Y+1}"``).
This reproduces D66's pinned Wind/Solar rows exactly (``instrument_check``
below), which is the check that this lane is measuring the same object.

Two sides, both read-only:

* MODEL — ``results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/
  f0e050e820c1159a/evolution_<year>.json``.
* PUBLISHED — PJM's own ELCC Class Ratings for each delivery year, each row
  carrying its source document, page and sha256 (:data:`PUBLISHED_ELCC_BY_DY`),
  and the requirement operands re-read from the in-repo demand-curve CSV.

**The one operand this card cannot source** is the fixed-tilt / tracking MW
split needed to blend PJM's two published solar classes into the model's single
``solar`` class.  PJM publishes no installed-MW pairing for any PRE-reform
vintage (companion FINDING §2), so the blend is reported as a BRACKET over every
candidate mix rather than as a number: rule 14 — the operand is escalated, never
estimated.

Rule 13: every published figure is an observable compared against, never an
input.  Rule 21: no value here is fitted to a residual.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARM_A = REPO / (
    "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a"
)
DEMAND_CURVE_CSV = REPO / "data/raw/capacity-market/demand-curve/pjm/pjm.csv"

# Delivery years this lane measures, and the model year whose screen prices each.
DY_TO_MODEL_YEAR = {f"{y}/{y + 1}": y for y in (2022, 2023, 2024, 2025)}

# --- INCUMBENT: what the model applies in EVERY delivery year --------------- #
# config/capacity_market.py::RENEWABLE_ELCC_CURVES_BY_ISO["PJM"], evaluated at
# the model's own installed MW.  Both classes clamp on every PJM pool in this
# window (wind >= 3,956 MW -> 0.41; solar <= 9,902 MW -> 0.1064), so the
# incumbent credit is constant across the window and the ledgers record it
# verbatim.  Provenance: PJM 2026/27 + 2027/28 BRA FINAL (marginal-ELCC) ratings.
INCUMBENT = {"wind": 0.41, "solar": 0.1064}

# --- PUBLISHED: PJM's operative ELCC Class Ratings, per delivery year ------- #
# `wind` is Onshore Wind; `solar_fixed` / `solar_tracking` are PJM's two solar
# ELCC classes ("Solar Fixed Panel"/"Solar Tracking Panel" pre-reform,
# "Fixed-Tilt Solar"/"Tracking Solar" post-reform).  `regime` distinguishes the
# pre-reform class-average construct from the ER24-99 marginal-ELCC construct
# the 2025/26 BRA was the first to clear on.
PUBLISHED_ELCC_BY_DY: dict[str, dict | None] = {
    # PRE-ELCC: PJM's ELCC construct first applied to the 2023/2024 BRA (its
    # ratings posted 2021-12-16), so this year has no published class ratings
    # of any kind and is out of this card's scope.
    "2022/2023": None,
    "2023/2024": {
        "regime": "class_average",
        "wind": 0.15,
        "solar_fixed": 0.38,
        "solar_tracking": 0.54,
        "source_doc": (
            "https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/"
            "elcc-class-ratings-for-2023-2024-bra.pdf"
        ),
        "source_page": "p.1 (the whole document is the table); posted 2021-12-16",
        "sha256": "c50890fb525dd0eb98eae29df68cabdd13c8bd390379c5028135e953745f2f69",
    },
    "2024/2025": {
        "regime": "class_average",
        "wind": 0.21,
        "solar_fixed": 0.33,
        "solar_tracking": 0.50,
        "source_doc": (
            "https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/"
            "elcc-class-ratings-for-2024-2025.pdf"
        ),
        "source_page": (
            "p.1 (the whole document is the table); posted 2023-12-29. Identical "
            "to December 2023 ELCC Report Table 2, p.5, whose Introduction (p.1) "
            "states 'only the 2024/2025 values are final'."
        ),
        "sha256": "f3fb54dbe98d19e1e2b0181c7da5dca798b836f0f4c4e6d0865c56a8589fc994",
    },
    "2025/2026": {
        "regime": "marginal",
        "wind": 0.38,
        "solar_fixed": 0.10,
        "solar_tracking": 0.14,
        "source_doc": (
            "https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/"
            "2025-26-3ia-elcc-class-ratings.pdf"
        ),
        "source_page": (
            "p.1, 'the Final ELCC Class Ratings for the 2025/2026 Delivery Year'; "
            "posted 2025-03-12 (3IA vintage — see FINDING §5 open item)"
        ),
        "sha256": "",
    },
}

# --- SUPERSEDED: the values D66 §4.5 and the D75 charter quote -------------- #
# December 2021 ELCC Report Table 2 (p.4-5) — PJM's ratings for the 2024/25 BRA
# as scheduled at that time.  The auction slipped (FERC ER23-729) and PJM RE-RAN
# the study; the December 2023 report's 2024/2025 values are the final ones.
# Carried only so the FINDING can decompose the difference.
SUPERSEDED_2024_25_DEC2021 = {
    "wind": 0.16,
    "solar_fixed": 0.36,
    "solar_tracking": 0.54,
    "source_doc": (
        "https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/"
        "elcc-report-december-2021.ashx"
    ),
    "source_page": "Table 2, p.4-5",
    "sha256": "1305626c975de30d5787482cf24b7f170f2aff7b03eeb1120e86f6fdb9610c84",
}

# --- THE BLOCKED OPERAND: candidate fixed-tilt shares of the solar fleet ---- #
# NONE of these is adopted.  The bracket exists so the FINDING can state the
# delta's range without choosing a weight (rule 14: escalate, never estimate).
MIX_CANDIDATES = {
    "admissible_lower_all_tracking": (
        0.0,
        "arithmetic bound — the whole solar pool tracking",
    ),
    "pjm_rrs_table5_2026_27": (
        1189.0 / 9902.0,
        "PJM 2025 ELCC/RRS Table 5 pp.16-17 (Fixed-Tilt 1,189 MW / Tracking "
        "8,713 MW) — the ONLY fixed/tracking MW pairing PJM publishes, and it "
        "is a POST-reform vintage; in repo at elcc/pjm/pjm.csv",
    ),
    "pjm_rrs_table5_2027_28": (
        1494.0 / 13106.0,
        "PJM 2025 ELCC/RRS Table 5 pp.16-17 (Fixed-Tilt 1,494 MW / Tracking "
        "11,612 MW) — post-reform vintage; in repo at elcc/pjm/pjm.csv",
    ),
    "eia860_pjm_states_proxy": (
        7443.3 / (7443.3 + 25184.8),
        "EIA-860 solar_operable, PJM-member states, ALL vintages, attributed "
        "rows only — a FOOTPRINT PROXY, not the PJM fleet (six of those states "
        "are only partly in PJM and no delivery-year filter is applied). A "
        "sanity check on the bracket; NOT a candidate operand.",
    ),
    "admissible_upper_all_fixed": (
        1.0,
        "arithmetic bound — the whole solar pool fixed-tilt",
    ),
}

# Charter's pre-declared phase-0 band for the DY 2024/25 accredited-VRE delta.
PREDECLARED_BAND_MW = (-1400.0, -600.0)

# D66 §3.2/§3.3's pinned VRE rows, reproduced as the instrument check.
D66_PINNED = {
    "2024/2025": {"wind": 4163.1, "solar": 484.1},
    "2025/2026": {"wind": 4778.1, "solar": 743.8},
}

# PJM's published cleared UCAP, both of D66 §1.2's frames (§1.4 / §1.2 tables;
# sources sha256-verified there).  Frame B = RPM + committed FRR (whole-RTO,
# like-for-like); Frame A = RPM only (D57/D61's comparator).
PUB_CLEARED = {
    "2023/2024": {"frame_b": 171_605.0, "frame_a": 144_870.6},
    "2024/2025": {"frame_b": 172_961.0, "frame_a": 147_478.9},
    "2025/2026": {"frame_b": 145_883.0, "frame_a": 135_684.0},
}


def _ledger(year: int) -> dict:
    return json.loads((ARM_A / f"evolution_{year}.json").read_text())


def accreditation_pools() -> dict[str, dict]:
    """VRE pools the screen accredits, per delivery year.

    ``evolution_{Y-1}``'s recorded pools, which is what ``prior_results``
    carries into model year Y's screen.  ``evolution_2022`` predates the
    adequacy-ledger block (it emits the screen and clearing blocks but no
    ``wind_cap_mw`` / ``solar_cap_mw`` / ``renewable_credit_applied``), so DY
    2023/24 falls back to D66's roll-forward — the 2021 base pools plus every
    ``renewable_additions`` row decided in 2022 — and says so in its
    ``provenance``.
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
                "renewable_additions (D66's roll-forward)"
            ),
        }
    return out


def solar_blend(rating: dict, fixed_share: float) -> float:
    """MW-weighted blend of PJM's two solar ELCC classes at ``fixed_share``."""
    return rating["solar_fixed"] * fixed_share + rating["solar_tracking"] * (
        1.0 - fixed_share
    )


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
    return {
        dy: {
            "frame_b": v["reliability_requirement"],
            "frame_a": v["reliability_requirement_frr_adj"] + v["ee_addback"],
        }
        for dy, v in rows.items()
        if {"reliability_requirement", "reliability_requirement_frr_adj", "ee_addback"}
        <= v.keys()
    }


def main() -> dict:
    pools = accreditation_pools()
    out: dict = {
        "accreditation_pools": pools,
        "mix_candidates": {
            name: {"fixed_share": share, "provenance": prov}
            for name, (share, prov) in MIX_CANDIDATES.items()
        },
        "blocked_operand": True,
        "years": {},
    }

    # --- instrument check: reproduce D66's pinned VRE rows exactly ---------- #
    check = {}
    for dy, pinned in D66_PINNED.items():
        ours = {
            "wind": pools[dy]["wind_mw"] * INCUMBENT["wind"],
            "solar": pools[dy]["solar_mw"] * INCUMBENT["solar"],
        }
        check[dy] = {
            "d66": pinned,
            "ours": {k: round(v, 3) for k, v in ours.items()},
            "max_abs_diff_mw": round(
                max(abs(ours[k] - pinned[k]) for k in ("wind", "solar")), 3
            ),
        }
    out["instrument_check"] = check

    reqs = published_requirements()

    for dy, model_year in DY_TO_MODEL_YEAR.items():
        led = _ledger(model_year)
        clearing = led.get("capacity_clearing") or {}
        p = pools[dy]
        row: dict = {
            "model_year": model_year,
            "wind_pool_mw": p["wind_mw"],
            "solar_pool_mw": p["solar_mw"],
            "pool_provenance": p["provenance"],
            "census_mw": clearing.get("census_mw"),
            "census_position": clearing.get("census_position"),
            "requirement_mw": clearing.get("requirement_mw"),
            "accredited_vre_mw_incumbent": round(
                p["wind_mw"] * INCUMBENT["wind"] + p["solar_mw"] * INCUMBENT["solar"], 3
            ),
        }
        rating = PUBLISHED_ELCC_BY_DY[dy]
        if rating is None:
            row["status"] = "PRE-ELCC delivery year — PJM published no class ratings"
            out["years"][dy] = row
            continue
        row["published_regime"] = rating["regime"]
        row["published"] = {
            k: rating[k] for k in ("wind", "solar_fixed", "solar_tracking")
        }
        row["source_doc"] = rating["source_doc"]
        row["source_page"] = rating["source_page"]

        wind_delta = p["wind_mw"] * (rating["wind"] - INCUMBENT["wind"])
        row["wind_delta_mw"] = round(wind_delta, 3)
        row["by_mix"] = {}
        for name, (share, _prov) in MIX_CANDIDATES.items():
            blend = solar_blend(rating, share)
            solar_delta = p["solar_mw"] * (blend - INCUMBENT["solar"])
            net = wind_delta + solar_delta
            entry = {
                "solar_blend_credit": round(blend, 6),
                "solar_delta_mw": round(solar_delta, 3),
                "net_accredited_vre_delta_mw": round(net, 3),
            }
            if clearing:
                after = clearing["census_mw"] + net
                entry["census_mw_after"] = round(after, 3)
                entry["census_position_after"] = round(
                    after / clearing["requirement_mw"], 6
                )
                entry["position_delta_pt"] = round(
                    100.0 * net / clearing["requirement_mw"], 4
                )
                pos_pub = {
                    f: PUB_CLEARED[dy][f] / reqs[dy][f] for f in ("frame_a", "frame_b")
                }
                entry["gap_pt_vintaged"] = {
                    f: round(100.0 * (v - after / clearing["requirement_mw"]), 3)
                    for f, v in pos_pub.items()
                }
            row["by_mix"][name] = entry
        if clearing and dy in PUB_CLEARED:
            pos_pub = {
                f: PUB_CLEARED[dy][f] / reqs[dy][f] for f in ("frame_a", "frame_b")
            }
            row["published_position"] = {f: round(v, 5) for f, v in pos_pub.items()}
            row["published_requirement_mw"] = {
                f: round(reqs[dy][f], 1) for f in ("frame_a", "frame_b")
            }
            row["gap_pt_incumbent"] = {
                f: round(100.0 * (v - clearing["census_position"]), 3)
                for f, v in pos_pub.items()
            }
        out["years"][dy] = row

    # --- the chartered pre-declared band, tested on DY 2024/25 -------------- #
    y = out["years"]["2024/2025"]
    nets = [v["net_accredited_vre_delta_mw"] for v in y["by_mix"].values()]
    lo, hi = PREDECLARED_BAND_MW
    out["predeclared_band_test"] = {
        "band_mw": list(PREDECLARED_BAND_MW),
        "measured_range_mw": [round(min(nets), 3), round(max(nets), 3)],
        "sign_declared": "DOWN",
        "sign_holds_at_every_mix": max(nets) < 0.0,
        "magnitude_in_band_at_every_mix": all(lo <= n <= hi for n in nets),
        "magnitude_in_band_at_pjm_published_mixes": all(
            lo <= y["by_mix"][name]["net_accredited_vre_delta_mw"] <= hi
            for name in ("pjm_rrs_table5_2026_27", "pjm_rrs_table5_2027_28")
        ),
    }

    # --- the SAME arithmetic on the superseded Dec-2021 ratings ------------- #
    # (same pools — the ONLY difference is the rating vintage), which is how the
    # charter's band was derived.
    p = pools["2024/2025"]
    wd = p["wind_mw"] * (SUPERSEDED_2024_25_DEC2021["wind"] - INCUMBENT["wind"])
    sup = {}
    for name, (share, _prov) in MIX_CANDIDATES.items():
        net = wd + p["solar_mw"] * (
            solar_blend(SUPERSEDED_2024_25_DEC2021, share) - INCUMBENT["solar"]
        )
        sup[name] = {
            "charter_basis_mw": round(net, 3),
            "operative_mw": y["by_mix"][name]["net_accredited_vre_delta_mw"],
            "rating_vintage_leg_mw": round(
                y["by_mix"][name]["net_accredited_vre_delta_mw"] - net, 3
            ),
        }
    sup_nets = [v["charter_basis_mw"] for v in sup.values()]
    out["charter_basis_decomposition"] = {
        "note": (
            "Same pools as the operative row — the pools are NOT in dispute "
            "(instrument_check). The only difference is the rating vintage."
        ),
        "wind_delta_mw": round(wd, 3),
        "charter_basis_range_mw": [round(min(sup_nets), 3), round(max(sup_nets), 3)],
        "charter_basis_in_band_at_every_mix": all(lo <= n <= hi for n in sup_nets),
        "by_mix": sup,
    }

    # --- window totals and the DY 2024/25 sign break-even ------------------- #
    scored = [dy for dy in ("2023/2024", "2024/2025", "2025/2026")]
    out["window_totals_mw_by_mix"] = {
        name: round(
            sum(
                out["years"][dy]["by_mix"][name]["net_accredited_vre_delta_mw"]
                for dy in scored
            ),
            3,
        )
        for name in MIX_CANDIDATES
    }
    rating = PUBLISHED_ELCC_BY_DY["2024/2025"]
    p = pools["2024/2025"]
    blend_star = INCUMBENT["solar"] - (
        p["wind_mw"] * (rating["wind"] - INCUMBENT["wind"])
    ) / p["solar_mw"]
    out["dy_2024_25_sign_flip"] = {
        "blend_credit_at_zero": round(blend_star, 6),
        "fixed_share_at_zero": round(
            (rating["solar_tracking"] - blend_star)
            / (rating["solar_tracking"] - rating["solar_fixed"]),
            6,
        ),
        "note": (
            "Negative fixed_share_at_zero means the delta is DOWN across the "
            "whole admissible mix range — no fixed share can flip its sign."
        ),
    }

    # --- |gap| summed over the three scored delivery years, per frame ------- #
    abs_sum = {
        "incumbent": {
            f: round(
                sum(abs(out["years"][dy]["gap_pt_incumbent"][f]) for dy in scored), 3
            )
            for f in ("frame_a", "frame_b")
        },
        "by_mix": {
            name: {
                f: round(
                    sum(
                        abs(out["years"][dy]["by_mix"][name]["gap_pt_vintaged"][f])
                        for dy in scored
                    ),
                    3,
                )
                for f in ("frame_a", "frame_b")
            }
            for name in MIX_CANDIDATES
        },
    }
    out["abs_gap_pt_sum"] = abs_sum
    return out


if __name__ == "__main__":
    result = main()
    Path(__file__).with_suffix(".json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result["instrument_check"], indent=2))
    print(json.dumps(result["predeclared_band_test"], indent=2))
