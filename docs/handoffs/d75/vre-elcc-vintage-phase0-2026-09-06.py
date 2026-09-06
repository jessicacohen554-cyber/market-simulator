"""capx D75 — PJM VRE ELCC accreditation-vintage phase 0 (ZERO LP).

Measures, from COMMITTED artifacts only, what a delivery-year vintage axis on
``RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]`` would do to the model's accredited VRE
MW and to the D66 census position, for every delivery year the D57 arm-A
hindcast screens.  Nothing is built, nothing is armed, and no solve is run.

Two sides, both read-only:

* MODEL — ``results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/
  f0e050e820c1159a/evolution_<year>.json``: ``wind_cap_mw`` / ``solar_cap_mw``
  (the ISO-wide VRE pools; PJM's persistent ``fleet`` carries no wind or solar
  units, so the pools ARE the accreditation base), ``renewable_credit_applied``
  (the credit the ledger actually resolved) and ``capacity_clearing``.
* PUBLISHED — PJM's own ELCC Class Ratings for each delivery year, each row
  carrying its source document, page and sha256 (:data:`PUBLISHED_ELCC_BY_DY`).

**The one operand this card cannot source** is the fixed-tilt / tracking MW
split needed to blend PJM's two published solar classes into the model's single
``solar`` class.  PJM publishes no installed-MW pairing for any PRE-reform
vintage (see the module's companion FINDING §2), so the blend is reported as a
BRACKET over every candidate mix rather than as a number: rule 14 — the operand
is escalated, never estimated.

Rule 13: every published figure is an observable compared against, never an
input.  Rule 21: no value here is fitted to a residual.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARM_A = REPO / (
    "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a"
)

# Model calendar year -> the delivery year the gate would key on.  This is the
# MODEL'S OWN mapping, ``capacity_deliverability.resolve_delivery_year("PJM", Y)
# == f"{Y}/{Y+1}"``, and it is what ``accreditation_year=year`` resolves to at
# every D48 call site.  It agrees with D66's instrument (its ``SCREEN_TO_DY``)
# and with that finding's §1.1 verification of ``evolution_2022.json`` against
# the published 2022/23 row.
MODEL_YEAR_TO_DY = {y: f"{y}/{y + 1}" for y in range(2021, 2026)}

# --- INCUMBENT: what the model applies in EVERY delivery year --------------- #
# config/capacity_market.py::RENEWABLE_ELCC_CURVES_BY_ISO["PJM"], evaluated at
# the model's own installed MW.  Both classes clamp on the observed PJM pools
# (wind pool >= 3,956 MW -> 0.41; solar pool <= 9,902 MW -> 0.1064), so the
# incumbent credit is constant across 2022/23-2026/27 and the ledgers confirm
# it verbatim.  Provenance: PJM 2026/27 + 2027/28 BRA FINAL (marginal-ELCC)
# class ratings.
INCUMBENT = {"wind": 0.41, "solar": 0.1064}

# --- PUBLISHED: PJM's operative ELCC Class Ratings, per delivery year ------- #
# `wind` is Onshore Wind; `solar_fixed` / `solar_tracking` are PJM's two solar
# ELCC classes (named "Solar Fixed Panel"/"Solar Tracking Panel" pre-reform and
# "Fixed-Tilt Solar"/"Tracking Solar" post-reform).  `regime` distinguishes the
# pre-reform class-average construct from the ER24-99 marginal-ELCC construct
# the 2025/26 BRA was the first to clear on.
PUBLISHED_ELCC_BY_DY = {
    # PRE-ELCC: PJM's ELCC construct first applied to the 2023/2024 BRA
    # (ratings posted 2021-12-16), so these two years have no published
    # class ratings of any kind and are out of this card's scope.
    "2021/2022": None,
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
        "source_page": "p.1 (whole document is the table); posted 2021-12-16",
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
            "p.1 (whole document is the table); posted 2023-12-29. Identical to "
            "December 2023 ELCC Report Table 2, p.5, whose Introduction (p.1) "
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
            "p.1, 'Final ELCC Class Ratings for the 2025/2026 Delivery Year'; "
            "posted 2025-03-12 (3IA vintage — see FINDING §4 open item)"
        ),
        "sha256": "",  # recorded in the FINDING; not needed for the arithmetic
    },
    "2026/2027": {
        "regime": "marginal",
        "wind": 0.41,
        "solar_fixed": 0.08,
        "solar_tracking": 0.11,
        "source_doc": (
            "https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/"
            "2026-27-bra-elcc-class-ratings.pdf"
        ),
        "source_page": "p.1; in repo at data/raw/capacity-market/elcc/pjm/pjm.csv",
        "sha256": "",
    },
}

# --- SUPERSEDED: the values D66 §4.5 and the D75 charter quote -------------- #
# The December 2021 ELCC Report's Table 2 (p.4-5) — PJM's ratings for the
# 2024/25 BRA as scheduled at that time.  The auction slipped (FERC ER23-729)
# and PJM RE-RAN the study; the December 2023 report's 2024/2025 values are the
# final ones.  Carried here only so the FINDING can show both.
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
        "PJM 2025 ELCC/RRS Table 5 p.16-17 (Fixed-Tilt 1,189 MW / Tracking "
        "8,713 MW) — the ONLY fixed/tracking MW pairing PJM publishes, and it "
        "is a POST-reform vintage; in repo at elcc/pjm/pjm.csv",
    ),
    "pjm_rrs_table5_2027_28": (
        1494.0 / 13106.0,
        "PJM 2025 ELCC/RRS Table 5 p.16-17 (Fixed-Tilt 1,494 MW / Tracking "
        "11,612 MW) — post-reform vintage; in repo at elcc/pjm/pjm.csv",
    ),
    "eia860_pjm_states_proxy": (
        7443.3 / (7443.3 + 25184.8),
        "EIA-860 solar_operable, PJM-member states, ALL vintages, attributed "
        "rows only — a FOOTPRINT PROXY, not the PJM fleet (six of the states "
        "are only partly in PJM and no delivery-year filter is applied). "
        "Sanity check on the bracket only; NOT a candidate operand.",
    ),
    "admissible_upper_all_fixed": (
        1.0,
        "arithmetic bound — the whole solar pool fixed-tilt",
    ),
}

# Charter's pre-declared phase-0 band for the DY 2024/25 accredited-VRE delta.
PREDECLARED_BAND_MW = (-1400.0, -600.0)


def solar_blend(rating: dict, fixed_share: float) -> float:
    """MW-weighted blend of PJM's two solar ELCC classes at ``fixed_share``."""
    return (
        rating["solar_fixed"] * fixed_share
        + rating["solar_tracking"] * (1.0 - fixed_share)
    )


def main() -> dict:
    out: dict = {"years": {}, "mix_candidates": {}, "blocked_operand": True}
    for name, (share, prov) in MIX_CANDIDATES.items():
        out["mix_candidates"][name] = {"fixed_share": share, "provenance": prov}

    for model_year, dy in MODEL_YEAR_TO_DY.items():
        led = json.loads((ARM_A / f"evolution_{model_year}.json").read_text())
        wind_mw = led.get("wind_cap_mw")
        solar_mw = led.get("solar_cap_mw")
        applied = led.get("renewable_credit_applied")
        clearing = led.get("capacity_clearing") or {}
        row: dict = {
            "delivery_year": dy,
            "wind_pool_mw": wind_mw,
            "solar_pool_mw": solar_mw,
            "credit_applied": applied,
            "census_mw": clearing.get("census_mw"),
            "census_position": clearing.get("census_position"),
            "requirement_mw": clearing.get("requirement_mw"),
        }
        if wind_mw is None or applied is None:
            # 2022's ledger predates the pool fields — recorded, never guessed.
            row["status"] = "ledger carries no VRE pool fields; not measurable"
            out["years"][model_year] = row
            continue

        assert applied == INCUMBENT, (model_year, applied)
        incumbent_mw = wind_mw * INCUMBENT["wind"] + solar_mw * INCUMBENT["solar"]
        row["accredited_vre_mw_incumbent"] = round(incumbent_mw, 3)

        rating = PUBLISHED_ELCC_BY_DY[dy]
        if rating is None:
            row["status"] = "PRE-ELCC delivery year — PJM published no class ratings"
            out["years"][model_year] = row
            continue
        row["published_regime"] = rating["regime"]
        row["published"] = {
            k: rating[k] for k in ("wind", "solar_fixed", "solar_tracking")
        }
        row["source_doc"] = rating["source_doc"]
        row["source_page"] = rating["source_page"]

        wind_delta = wind_mw * (rating["wind"] - INCUMBENT["wind"])
        row["wind_delta_mw"] = round(wind_delta, 3)
        row["by_mix"] = {}
        for name, (share, _prov) in MIX_CANDIDATES.items():
            blend = solar_blend(rating, share)
            solar_delta = solar_mw * (blend - INCUMBENT["solar"])
            net = wind_delta + solar_delta
            entry = {
                "solar_blend_credit": round(blend, 6),
                "solar_delta_mw": round(solar_delta, 3),
                "net_accredited_vre_delta_mw": round(net, 3),
            }
            if clearing:
                req = clearing["requirement_mw"]
                entry["census_mw_after"] = round(clearing["census_mw"] + net, 3)
                entry["census_position_after"] = round(
                    (clearing["census_mw"] + net) / req, 6
                )
                entry["position_delta_pt"] = round(100.0 * net / req, 4)
            row["by_mix"][name] = entry
        out["years"][model_year] = row

    # Charter's pre-declared band, tested on DY 2024/25 (model year 2024).
    y24 = out["years"][2024]
    nets = [v["net_accredited_vre_delta_mw"] for v in y24["by_mix"].values()]
    lo, hi = PREDECLARED_BAND_MW
    out["predeclared_band_test"] = {
        "band_mw": list(PREDECLARED_BAND_MW),
        "measured_range_mw": [round(min(nets), 3), round(max(nets), 3)],
        "sign_declared": "DOWN",
        "sign_holds": max(nets) < 0.0,
        "magnitude_in_band_at_every_mix": all(lo <= n <= hi for n in nets),
    }

    # The same arithmetic on the SUPERSEDED Dec-2021 ratings the charter quotes,
    # so the FINDING can show that the band was derived from those.
    led = json.loads((ARM_A / "evolution_2024.json").read_text())
    w, s = led["wind_cap_mw"], led["solar_cap_mw"]
    wd = w * (SUPERSEDED_2024_25_DEC2021["wind"] - INCUMBENT["wind"])
    sup_nets = [
        wd + s * (solar_blend(SUPERSEDED_2024_25_DEC2021, share) - INCUMBENT["solar"])
        for share, _ in MIX_CANDIDATES.values()
    ]
    out["superseded_dec2021_2024_25"] = {
        "note": (
            "The Dec-2021 ratings applied to DY 2024/25's OWN pools "
            "(model year 2024). D66 §4.5 applied them to model year 2023's "
            "pools, which its own §1.4 assigns to DY 2023/24."
        ),
        "wind_delta_mw": round(wd, 3),
        "net_range_mw": [round(min(sup_nets), 3), round(max(sup_nets), 3)],
        "magnitude_in_band_at_every_mix": all(
            lo <= n <= hi for n in sup_nets
        ),
    }

    # ---------------------------------------------------------------- #
    # The charter's / D66 §4.5's basis, reconstructed, and the two-step
    # decomposition of the difference.  D66's instrument freezes the VRE
    # pools at ``evolution_2021.json`` and reuses them for EVERY delivery
    # year (its own comment says the pool "is the base year's pool plus
    # every addition decided in 2021..Y-1", but the code never adds them),
    # so §4.5's "2024/25's own pools" are the 2021 base pools.  Both legs
    # are shown at every candidate mix so the difference is attributable.
    # ---------------------------------------------------------------- #
    base = json.loads((ARM_A / "evolution_2021.json").read_text())
    frozen_w, frozen_s = base["wind_cap_mw"], base["solar_cap_mw"]
    own = out["years"][2024]
    own_w, own_s = own["wind_pool_mw"], own["solar_pool_mw"]
    live = PUBLISHED_ELCC_BY_DY["2024/2025"]
    sup = SUPERSEDED_2024_25_DEC2021
    decomp = {}
    for name, (share, _prov) in MIX_CANDIDATES.items():
        def net(w, s_mw, rating, share=share):
            return w * (rating["wind"] - INCUMBENT["wind"]) + s_mw * (
                solar_blend(rating, share) - INCUMBENT["solar"]
            )

        a = net(frozen_w, frozen_s, sup)   # D66 §4.5 / the charter's basis
        b = net(own_w, own_s, sup)         # + the pool-year correction
        c = net(own_w, own_s, live)        # + the rating-vintage correction
        decomp[name] = {
            "charter_basis_mw": round(a, 3),
            "after_pool_year_correction_mw": round(b, 3),
            "after_rating_vintage_correction_mw": round(c, 3),
            "pool_year_leg_mw": round(b - a, 3),
            "rating_vintage_leg_mw": round(c - b, 3),
        }
    out["charter_basis_decomposition"] = {
        "frozen_pools_mw": {"wind": frozen_w, "solar": frozen_s},
        "dy_2024_25_own_pools_mw": {"wind": own_w, "solar": own_s},
        "by_mix": decomp,
    }

    # ---------------------------------------------------------------- #
    # D66 §3.2 / §3.3 VRE rows, recomputed on each delivery year's OWN
    # pools.  Row convention is D66's: published cleared − model.
    # ---------------------------------------------------------------- #
    D66_PUBLISHED_CLEARED = {  # 2024/25 BRA Report Table 9 p.14 / 2027/28 Table 6 p.11
        "2024/2025": {"wind": 1396.0, "solar": 4232.0},
        "2025/2026": {"wind": 2618.0, "solar": 1337.0},
    }
    rows = {}
    for dy, pub in D66_PUBLISHED_CLEARED.items():
        my = int(dy[:4])
        r = out["years"][my]
        model_w = r["wind_pool_mw"] * INCUMBENT["wind"]
        model_s = r["solar_pool_mw"] * INCUMBENT["solar"]
        d66_w = frozen_w * INCUMBENT["wind"]
        d66_s = frozen_s * INCUMBENT["solar"]
        rows[dy] = {
            "model_wind_accredited_mw": round(model_w, 3),
            "model_solar_accredited_mw": round(model_s, 3),
            "d66_wind_accredited_mw": round(d66_w, 3),
            "d66_solar_accredited_mw": round(d66_s, 3),
            "row_wind_corrected_mw": round(pub["wind"] - model_w, 3),
            "row_solar_corrected_mw": round(pub["solar"] - model_s, 3),
            "row_wind_d66_mw": round(pub["wind"] - d66_w, 3),
            "row_solar_d66_mw": round(pub["solar"] - d66_s, 3),
            "supply_leg_shift_mw": round(
                (pub["wind"] - model_w + pub["solar"] - model_s)
                - (pub["wind"] - d66_w + pub["solar"] - d66_s),
                3,
            ),
        }
    out["d66_vre_rows_on_own_pools"] = rows

    # Window total per mix (the three in-scope delivery years) and the
    # fixed-tilt share at which DY 2024/25's net delta changes sign.
    totals = {}
    for name in MIX_CANDIDATES:
        totals[name] = round(
            sum(
                out["years"][y]["by_mix"][name]["net_accredited_vre_delta_mw"]
                for y in (2023, 2024, 2025)
            ),
            3,
        )
    r24 = out["years"][2024]
    rating = PUBLISHED_ELCC_BY_DY["2024/2025"]
    # net = W*(w-inc_w) + S*(blend-inc_s) = 0, blend = tracking - (tracking-fixed)*f
    blend_star = INCUMBENT["solar"] - (
        r24["wind_pool_mw"] * (rating["wind"] - INCUMBENT["wind"])
    ) / r24["solar_pool_mw"]
    f_star = (rating["solar_tracking"] - blend_star) / (
        rating["solar_tracking"] - rating["solar_fixed"]
    )
    out["window_totals_mw_by_mix"] = totals
    out["dy_2024_25_sign_flip"] = {
        "blend_credit_at_zero": round(blend_star, 6),
        "fixed_share_at_zero": round(f_star, 6),
        "all_window_totals_negative": all(v < 0.0 for v in totals.values()),
    }

    return out


if __name__ == "__main__":
    result = main()
    dest = Path(__file__).with_suffix(".json")
    dest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
