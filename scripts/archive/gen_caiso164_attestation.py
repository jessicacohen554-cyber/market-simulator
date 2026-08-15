"""Write ``calibration_attestation.json`` for the caiso-164 CAISO keeper candidate.

caiso-164 promotes ``caiso_zonal_loss_surface``: CAISO's internal north–south
network moves from **lossless** — the model's implicit *estimate* that losses
are zero — to CAISO's **own published marginal delivery-factor surface**,
``dev_z,m = Σ MCL_z,t / Σ MCE_t``, derived by
``scripts/data/derive_caiso_loss_surface.py`` from the committed DAM component
record. It is the CAISO leg of the twice-adjudicated ``zonal_loss_surface``
family (MISO miso-76 ``R``, PJM pjm-136 ``K``); per rule 28(d) neither verdict
fills CAISO's cell, which entered as ``U`` and derives its own parameters from
its own market.

It is a **measured-input upgrade under rule 14** ``[R-ACCURATE]`` — **zero new
parameters**, no threshold moved, nothing swept, no residual consulted — so the
attestation is the incumbent keeper's, carried forward with:

1. a rewritten ``governance.attested_by`` describing the surface, what the
   lossless network was suppressing, and — stated as prominently — the
   ~80–87 % congestion majority this arm does **NOT** address, and
2. every ledgered exception's ``magnitude`` RE-MEASURED on the arm bundle.

The DOF ledger is carried **verbatim** (rule 21 ``[R-DOF]``): a published
network property introduces no free parameter, so ``n_entries`` /
``n_residual`` must be unchanged, and this script ASSERTS that rather than
trusting it.

Promotion premise, COMPUTED not typed: the arm's ``ScenarioConfig`` must differ
from BOTH the incumbent keeper's and the same-HEAD control's in EXACTLY ONE
field. ``config_drift`` uses an explicit present/absent diff rather than
``dict.get``, which collapses "absent" and "present-but-``None``".

**Liveness is asserted on FLOWS and on the loss array, never on prices** — the
caiso-162/163 lesson. This generator FAILS unless the control is measured
carrying real S→N energy on the corridor the surface makes lossy (so the
mechanism had something to act on and is not INERT), and it FAILS if any
treatment hour exceeds a caiso-163 published directional cap (the split must
not loosen the ratings it composes with).

**The adversarial ceiling** (PRECHECK §4, gate S2): the arm may not move the
NP15−ZP26 basis by MORE than the measured ``dMCL``. A larger movement would
mean the mechanism is doing something other than representing losses, and the
generator fails rather than reporting a flattering number.

Nothing here is hand-typed from a solve: every magnitude is recomputed at run
time from the bundles' own committed sidecars.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_caiso164_attestation.py
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields as dc_fields
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig

REPO = Path(__file__).resolve().parents[2]
INCUMBENT = REPO / "results/calibration/caiso163_asym_path_ratings"
ARM = REPO / "results/calibration/caiso164_zonal_loss_surface"
CONTROL = REPO / "results/calibration/caiso164_control_lossless"
SURFACE = REPO / "data/raw/iso-specific-transmission/CAISO_loss_surface.csv"
YEARS = (2023, 2024, 2025)
TOL = 1e-6

# The single intended ScenarioConfig delta.
INTENDED_DELTA = "caiso_zonal_loss_surface"

# OWNER-DECISION DEFAULT FLIPS that landed on main as merged owner decisions.
# NOT this session's choices and NOT tuning. The incumbent already carries
# them, so they do not appear as a drift here — asserted anyway, on the same two
# independent grounds gen_caiso163_attestation.py uses:
#   (1) every one is capacity-evolution / forward-entry machinery gated behind a
#       hard ``config.mode == "forecast"`` check, and this bundle is
#       mode="backcast", so none can reach the dispatch LP; and
#   (2) each holds the SAME value in the control arm and the treatment arm, so
#       none confounds the A/B.
OWNER_DEFAULT_FLIPS = {
    "retirement_rule": "D-1 (flip retirement_rule default legacy -> pipeline)",
    "entry_rate_limits": "D-2 (arm entry_rate_limits + entry_commissioning_lag)",
    "entry_commissioning_lag": "D-2 (arm entry_rate_limits + entry_commissioning_lag)",
    "net_cone_forward_escalation": "D-3a (net-CONE forward mode -> reindex_gross)",
}

# caiso-163's published WECC directional ratings, which the one-way loss split
# must preserve exactly. Listed only to be ASSERTED, never applied.
PATHS = {
    "Path15_Midway_LosBanos": (("NP15", "ZP26"), 3265.0, 5400.0),
    "Path26_Midway_Vincent": (("ZP26", "SP15_rest"), 4000.0, 3000.0),
}

# Measured CAISO DAM hub basis AND its published component split (mean $/MWh,
# TH_*_GEN-APND), computed by scripts/probes/caiso164_ns_basis_decomp.py from
# data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv. Reported against and used
# ONLY as the adversarial S2 ceiling — no model input is derived from these.
ACTUAL_BASIS = {
    2023: {
        "np15_minus_zp26": 5.947,
        "dmcc": 4.771,
        "dmcl": 1.176,
        "np15_minus_sp15": 2.337,
    },
    2024: {
        "np15_minus_zp26": 8.576,
        "dmcc": 7.475,
        "dmcl": 1.102,
        "np15_minus_sp15": 7.992,
    },
    2025: {
        "np15_minus_zp26": 5.727,
        "dmcc": 4.677,
        "dmcl": 1.049,
        "np15_minus_sp15": 6.009,
    },
}


def load_json(path: Path) -> dict:
    """Return the parsed JSON at ``path``."""
    return json.loads(path.read_text())


def config_drift(arm: dict, other: dict) -> dict:
    """Return the present/absent-aware config diff between two scenario configs.

    A ``dict.get`` diff collapses "absent" and "present-but-``None``"; this
    reports the three cases separately so schema drift cannot be mistaken for a
    config change.
    """
    return {
        "arm_only": sorted(set(arm) - set(other)),
        "other_only": sorted(set(other) - set(arm)),
        "value_diffs": {
            k: {"other": other[k], "arm": arm[k]}
            for k in sorted(set(arm) & set(other))
            if arm[k] != other[k]
        },
    }


def directional_flow(bundle: Path, year: int, pair: tuple[str, str]) -> np.ndarray:
    """Return the signed hourly P1 flow on ``pair`` (+ = the listed N->S sense).

    Sums every link joining the two zones with the sign of its own orientation,
    matching ``interchange.core.build_interface_groups`` — so the one-way pair
    the loss split creates reads as the net corridor flow, directly comparable
    to the control's single signed link.
    """
    f = pd.read_parquet(bundle / "flows.parquet")
    f = f[(f["pass"] == "P1") & (f["year"] == year)]
    a, b = pair
    net = f[(f["from_zone"] == a) & (f["to_zone"] == b)].groupby("hour")["mw"].sum()
    rev = f[(f["from_zone"] == b) & (f["to_zone"] == a)]
    if len(rev):
        net = net.subtract(rev.groupby("hour")["mw"].sum(), fill_value=0.0)
    return net.sort_index().to_numpy(dtype=float)


def zone_prices(bundle: Path, year: int) -> pd.DataFrame:
    """Return the P1 hour x zone price frame for ``year``."""
    d = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    return d[d["pass"] == "P1"].pivot_table(
        index="hour", columns="zone", values="price"
    )


def load_weighted_lambda(bundle: Path, year: int) -> float:
    """Return the P1 load-weighted mean LMP for ``year`` from a bundle sidecar."""
    d = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    price = d.pivot_table(index="hour", columns="zone", values="price")
    load = d.pivot_table(index="hour", columns="zone", values="demand")
    zones = [z for z in price.columns if load[z].sum() > 0]
    total = sum(load[z].sum() for z in zones)
    return float(sum((price[z] * load[z]).sum() for z in zones) / total)


def main() -> int:
    """Write the caiso-164 attestation onto the arm bundle."""
    argparse.ArgumentParser(description=__doc__).parse_args()

    incumbent_att = load_json(INCUMBENT / "calibration_attestation.json")
    arm_cfg = load_json(ARM / "run_config.json")["scenario_config"]
    control_cfg = load_json(CONTROL / "run_config.json")["scenario_config"]
    keeper_cfg = load_json(INCUMBENT / "run_config.json")["scenario_config"]

    drift_inc = config_drift(arm_cfg, keeper_cfg)
    drift_ctl = config_drift(arm_cfg, control_cfg)

    # PROMOTION PREMISE (rule 24 [R-REGISTRY]): the ONLY value difference that
    # may exist, against EITHER comparator, is the intended one.
    allowed = {INTENDED_DELTA} | set(OWNER_DEFAULT_FLIPS)
    for label, drift in (("incumbent", drift_inc), ("control", drift_ctl)):
        unexpected = {k: v for k, v in drift["value_diffs"].items() if k not in allowed}
        if unexpected:
            print(
                f"FATAL: unexpected ScenarioConfig deltas vs the {label} beyond "
                f"{INTENDED_DELTA}: {sorted(unexpected)}",
                file=sys.stderr,
            )
            return 1

    # Against the SAME-HEAD CONTROL the intended delta must be a genuine VALUE
    # diff — same schema both sides, so anything else means the arm did not
    # actually change the mechanism.
    if INTENDED_DELTA not in drift_ctl["value_diffs"]:
        print(
            f"FATAL: {INTENDED_DELTA} is not a value diff vs the same-HEAD "
            "control — the arm did not actually change the mechanism.",
            file=sys.stderr,
        )
        return 1
    if drift_ctl["arm_only"] or drift_ctl["other_only"]:
        print(
            "FATAL: schema drift against the same-HEAD control "
            f"(arm_only={drift_ctl['arm_only']}, "
            f"other_only={drift_ctl['other_only']}) — the two arms must share "
            "one schema or the single-field premise is not measurable.",
            file=sys.stderr,
        )
        return 1

    # Against the INCUMBENT — an OLDER head — the intended delta legitimately
    # appears as ``arm_only``: the field did not exist when that keeper solved.
    # So does every ScenarioConfig field other sessions merged in between. That
    # is a real hole (an inherited field could carry a non-default value and
    # silently change the solve), so it is CLOSED rather than waived: every
    # inherited new field must hold its ScenarioConfig DEFAULT in the arm, and
    # must be identical in the control.
    if (
        INTENDED_DELTA not in drift_inc["value_diffs"]
        and INTENDED_DELTA not in drift_inc["arm_only"]
    ):
        print(
            f"FATAL: {INTENDED_DELTA} is neither a value diff nor a new field "
            "vs the incumbent — the arm did not actually change the mechanism.",
            file=sys.stderr,
        )
        return 1
    if drift_inc["other_only"]:
        print(
            "FATAL: the incumbent carries ScenarioConfig fields the arm does "
            f"not ({drift_inc['other_only']}) — a field was REMOVED under the "
            "arm, which is not a single-field delta.",
            file=sys.stderr,
        )
        return 1
    defaults = {f.name: f.default for f in dc_fields(ScenarioConfig)}
    inherited_nondefault = {}
    for k in drift_inc["arm_only"]:
        if k == INTENDED_DELTA:
            continue
        if k not in defaults:
            inherited_nondefault[k] = "not a ScenarioConfig field"
        elif arm_cfg[k] != defaults[k]:
            inherited_nondefault[k] = {"default": defaults[k], "arm": arm_cfg[k]}
    if inherited_nondefault:
        print(
            "FATAL: ScenarioConfig fields inherited from intervening merges are "
            f"NOT at their defaults in the arm: {inherited_nondefault}. An "
            "inherited non-default is an undeclared config change, not a "
            "schema addition.",
            file=sys.stderr,
        )
        return 1
    inherited_schema = {
        k: {"default": defaults.get(k), "arm": arm_cfg[k]}
        for k in drift_inc["arm_only"]
        if k != INTENDED_DELTA
    }

    # The owner-default flips must be IDENTICAL between the control and the
    # treatment, else they confound the A/B and the single-delta premise is void.
    confounded = [
        k for k in OWNER_DEFAULT_FLIPS if control_cfg.get(k) != arm_cfg.get(k)
    ]
    if confounded:
        print(
            "FATAL: owner-default flips differ between the control and treatment "
            f"arms, so they confound the A/B: {confounded}",
            file=sys.stderr,
        )
        return 1
    if arm_cfg.get("mode") != "backcast":
        print(
            f"FATAL: expected mode='backcast', got {arm_cfg.get('mode')!r} — the "
            "owner-default flips are only admissible because the forecast-gated "
            "capacity-evolution path is unreachable in a backcast.",
            file=sys.stderr,
        )
        return 1

    # RULE 21 [R-DOF]: a published network property introduces no free
    # parameter, so the ledger must be carried VERBATIM. Assert, never trust.
    free_params = incumbent_att["free_parameters"]
    if free_params["n_entries"] != 11 or free_params["n_residual"] != 9:
        print(
            "FATAL: incumbent DOF ledger is not the expected 11 entries / "
            f"9 residual (got {free_params['n_entries']} / "
            f"{free_params['n_residual']}) — the carry-forward premise is void.",
            file=sys.stderr,
        )
        return 1

    # RULE 22: the holdout spend freeze is ACTIVE. No year outside 2023-2025 may
    # appear in either bundle or in the derived surface.
    for label, bundle in (("arm", ARM), ("control", CONTROL)):
        yrs = set(load_json(bundle / "meta.json").get("years", []))
        if not yrs <= set(YEARS):
            print(
                f"FATAL: the {label} bundle carries out-of-window years "
                f"{sorted(yrs - set(YEARS))} — holdout spend freeze breach.",
                file=sys.stderr,
            )
            return 1
    surf = pd.read_csv(SURFACE)
    bad_years = sorted(set(surf["year"]) - ({0} | set(YEARS)))
    if bad_years:
        print(
            f"FATAL: CAISO_loss_surface.csv carries years {bad_years} outside "
            "the 2023-2025 train window (0 = the pooled forecast analogue).",
            file=sys.stderr,
        )
        return 1

    # The surface must be CAISO's own and carry every model load zone.
    if set(surf["iso"].unique()) != {"CAISO"}:
        print(
            "FATAL: CAISO_loss_surface.csv carries a non-CAISO ISO — rule 25 "
            "[R-ISO-SCOPE] forbids a value crossing a market boundary.",
            file=sys.stderr,
        )
        return 1

    # LIVENESS, ON FLOWS AND THE LOSS ARRAY (the caiso-162/163 lesson).
    # (a) The control must carry real S->N energy on the corridor the surface
    #     makes lossy — otherwise the mechanism had nothing to act on and is
    #     INERT, and promotion is forbidden.
    # (b) No treatment hour may exceed a caiso-163 published cap — the split
    #     must not loosen the ratings it composes with.
    liveness: dict[str, dict] = {}
    ctl_sn_hours = 0
    arm_violation_hours = 0
    for name, (pair, ns_cap, sn_cap) in PATHS.items():
        for year in YEARS:
            ctl = directional_flow(CONTROL, year, pair)
            trt = directional_flow(ARM, year, pair)
            row = {
                "pair": f"{pair[0]}->{pair[1]}",
                "published_ns_cap_mw": ns_cap,
                "published_sn_cap_mw": sn_cap,
                "control_max_ns_mw": round(float(ctl.max()), 2),
                "control_max_sn_mw": round(float((-ctl).max()), 2),
                "arm_max_ns_mw": round(float(trt.max()), 2),
                "arm_max_sn_mw": round(float((-trt).max()), 2),
                "control_hours_sn": int((ctl < -TOL).sum()),
                "arm_hours_sn": int((trt < -TOL).sum()),
                "control_twh_sn": round(float(-ctl[ctl < 0].sum()) / 1e6, 4),
                "arm_twh_sn": round(float(-trt[trt < 0].sum()) / 1e6, 4),
                "arm_hours_over_published": int((trt > ns_cap + TOL).sum())
                + int((-trt > sn_cap + TOL).sum()),
            }
            if name.startswith("Path15"):
                ctl_sn_hours += row["control_hours_sn"]
            arm_violation_hours += row["arm_hours_over_published"]
            liveness[f"{name}_{year}"] = row

    if ctl_sn_hours == 0:
        print(
            "FATAL: the control carries ZERO south-to-north hours on Path 15 — "
            "the corridor the measured surface makes lossy never runs in the "
            "lossy direction, so the mechanism is INERT. Register it as INERT "
            "on flow evidence; do not promote.",
            file=sys.stderr,
        )
        return 1
    if arm_violation_hours != 0:
        print(
            f"FATAL: {arm_violation_hours} treatment-arm hours exceed a caiso-163 "
            "published directional cap — the one-way split LOOSENED the ratings "
            "it must preserve. Stop-the-line, not a result.",
            file=sys.stderr,
        )
        return 1

    # PRIMARY STRUCTURAL GATES, with the adversarial S2 ceiling.
    structural: dict[str, dict] = {}
    for year in YEARS:
        row: dict = {}
        for label, bundle in (("control", CONTROL), ("arm", ARM)):
            p = zone_prices(bundle, year)
            d_zp = (p["NP15"] - p["ZP26"]).to_numpy()
            row[label] = {
                "hours_np15_ne_zp26": int((np.abs(d_zp) > 0.01).sum()),
                "pct_hours_np15_ne_zp26": round(
                    100.0 * float((np.abs(d_zp) > 0.01).mean()), 3
                ),
                "hours_np15_dearer": int((d_zp > 0.01).sum()),
                "mean_np15_minus_zp26": round(float(d_zp.mean()), 4),
                "mean_np15_minus_sp15": round(
                    float((p["NP15"] - p["SP15_rest"]).mean()), 4
                ),
            }
        act = ACTUAL_BASIS[year]
        delta = (
            row["arm"]["mean_np15_minus_zp26"] - row["control"]["mean_np15_minus_zp26"]
        )
        row["actual"] = act
        row["delta_np15_minus_zp26"] = round(delta, 4)
        row["S2_ceiling_measured_dMCL"] = act["dmcl"]
        row["S2_pct_of_ceiling_used"] = round(100.0 * abs(delta) / act["dmcl"], 1)
        row["pct_of_measured_loss_component_recovered"] = round(
            100.0 * delta / act["dmcl"], 1
        )
        row["pct_of_total_measured_basis_recovered"] = round(
            100.0 * delta / act["np15_minus_zp26"], 2
        )
        structural[str(year)] = row

        # THE ADVERSARIAL CEILING (PRECHECK §4 S2 / §5 disposition 4).
        if abs(delta) > act["dmcl"] + 1e-9:
            print(
                f"FATAL (gate S2, {year}): the arm moved mean NP15-ZP26 by "
                f"{delta:+.4f} $/MWh, MORE than the measured loss component "
                f"dMCL = {act['dmcl']:.3f}. A loss mechanism cannot legitimately "
                "produce more separation than the losses it represents — this is "
                "a defect to investigate, not a result to promote.",
                file=sys.stderr,
            )
            return 1

    lam = {}
    for y in YEARS:
        c, a = load_weighted_lambda(CONTROL, y), load_weighted_lambda(ARM, y)
        lam[str(y)] = {
            "control": round(c, 4),
            "arm": round(a, 4),
            "delta": round(a - c, 4),
            "pct_of_level": round(100.0 * (a - c) / c, 4),
        }

    # Carry the exceptions forward, RE-MEASURING each magnitude on the arm bundle.
    exceptions = json.loads(json.dumps(incumbent_att["exceptions"]))
    for exc in exceptions:
        crit, year = exc.get("criterion"), exc.get("year")
        if crit == "price_mean" and year == 2025:
            exc["magnitude"] = (
                "RE-MEASURED on caiso164_zonal_loss_surface: load-weighted lambda "
                f"{lam['2025']['arm']:.4f} $/MWh vs the same-HEAD control's "
                f"{lam['2025']['control']:.4f} ({lam['2025']['delta']:+.4f}, "
                f"{lam['2025']['pct_of_level']:+.4f}% of level). THIS ARM IS NOT A "
                "C3a ARM AND DOES NOT CLAIM TO BE ONE: PRECHECK-caiso164 §0.5 "
                "registered BEFORE the solve that it is bounded ex ante at the "
                "measured loss component (19.8/12.8/18.3% of the NP15-ZP26 basis) "
                "and cannot address the 80-87% congestion majority. The caveat "
                "remains the OWNER's, on the caiso-141 A2 non-public hourly "
                "pumped-storage data wall."
            )
    attestation = json.loads(json.dumps(incumbent_att))
    attestation["exceptions"] = exceptions
    attestation["free_parameters"] = free_params
    attestation["governance"] = dict(attestation.get("governance", {}))
    attestation["governance"]["attested_by"] = (
        "caiso-164 (2026-08-04): CAISO's internal network moves from LOSSLESS — "
        "the model's implicit ESTIMATE that losses are zero — to CAISO's OWN "
        "published marginal delivery-factor surface, dev_z,m = SUM(MCL_z)/SUM(MCE), "
        "derived by scripts/data/derive_caiso_loss_surface.py from the committed "
        "DAM component record (CAISO writes LMP = MCE + MCC + MCL). Rule 14 "
        "[R-ACCURATE]: measured physical network property over a zero-estimate. "
        "ZERO free parameters — the same frozen estimator as the MISO/PJM "
        "analogues, on CAISO's own data, nothing swept and no residual consulted; "
        "the DOF ledger is carried VERBATIM at 11/9 and this generator FAILS if it "
        "moves. Rule 25 [R-ISO-SCOPE]: every value is CAISO's own, in CAISO's own "
        "file; per rule 28(d) the PJM K and MISO R verdicts do NOT fill this cell. "
        "CHARTERED ON A MEASURED DECOMPOSITION, not on the caiso-163 topology "
        "hypothesis: caiso-164 §0 used CAISO's published component split to show "
        "that 19.8/12.8/18.3% of the measured NP15-ZP26 basis is the LOSS "
        "component (+1.176/+1.102/+1.049 of +5.947/+8.576/+5.727 $/MWh), which the "
        "lossless LP had no representation of at all. WHAT THIS DOES NOT DO, "
        "stated as prominently as what it does: the remaining 80-87% is CONGESTION "
        "and is NOT addressed. §0 attributes it to an intra-SP15 corridor — "
        "LA_BASIN (77-83 TWh of load, 0.11 belly renewable/load) absorbs the entire "
        "ZP26+SP15_rest belly surplus through a never-binding 12,008 MW one-way "
        "link, so no surplus reaches Path 15 and it never binds S->N with a "
        "positive dual — and FILES it as a DATA BLOCKER: CAISO nodal/intra-zonal "
        "congestion data is not in data/raw, and per rules 1/13 it is not "
        "approximated with a fitted proxy. No compensating adder, haircut or offset "
        "was added; the north-south basis is NOT claimed as closed. Liveness is "
        "asserted on FLOWS and the loss array, never on prices (the caiso-162/163 "
        "lesson), and gate S2 is adversarial: this generator FAILS if the arm moves "
        "the basis by MORE than the measured dMCL it represents. The caiso-163 "
        "published Path 15 / Path 26 directional ratings survive the one-way split "
        "exactly — asserted here, zero treatment hours over any published cap."
    )
    attestation["caiso164"] = {
        "mechanism": INTENDED_DELTA,
        "prereg": (
            "results/calibration/PRECHECK-caiso164-zonal-loss-surface-2026-08-04.md"
        ),
        "config_drift_vs_incumbent": drift_inc,
        "config_drift_vs_control": drift_ctl,
        "inherited_schema_fields_vs_incumbent": inherited_schema,
        "inherited_schema_admissibility": (
            "the incumbent solved at an older HEAD, so fields other sessions "
            "merged since appear as arm_only; every one is ASSERTED to hold its "
            "ScenarioConfig default in the arm, so none is an undeclared config "
            "change. The single-field premise is measured against the SAME-HEAD "
            "control, where the intended delta is the only value diff and there "
            "is zero schema drift either way."
        ),
        "owner_default_flips": OWNER_DEFAULT_FLIPS,
        "owner_default_flips_admissibility": (
            "forecast-gated capacity-evolution machinery, unreachable at "
            "mode='backcast' (asserted), and identical in both arms (asserted)"
        ),
        "liveness_on_flows": liveness,
        "structural": structural,
        "load_weighted_lambda": lam,
        "surface_rows": int(len(surf)),
        "surface_zones": sorted(surf["zone"].unique().tolist()),
        "surface_interpolated_zones": sorted(
            surf.loc[surf["interpolated"], "zone"].unique().tolist()
        ),
        "derive_acceptance": "6/6 pair-years in the miso-76 B1 band, 1.04-1.06x",
    }

    out = ARM / "calibration_attestation.json"
    out.write_text(json.dumps(attestation, indent=2) + "\n")
    print(f"wrote {out}")
    for y in YEARS:
        s = structural[str(y)]
        print(
            f"  {y}: NP15-ZP26 {s['control']['mean_np15_minus_zp26']:+.4f} -> "
            f"{s['arm']['mean_np15_minus_zp26']:+.4f} "
            f"(delta {s['delta_np15_minus_zp26']:+.4f}, "
            f"{s['pct_of_measured_loss_component_recovered']:.1f} % of the "
            f"measured loss component, {s['S2_pct_of_ceiling_used']:.1f} % of the "
            "S2 ceiling)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
