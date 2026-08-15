"""Generate the miso-83 (gas-offer net-revenue margin keeper) calibration_attestation.json.

miso-83 is the miso-81-phantom-outage keeper recipe with a SINGLE delta —
``gas_offer_margin=true`` (``gas_offer_net_revenue_margin``, anchor 3.0492
$/MMBtu) — promoted to the MISO keeper by OWNER OVERRIDE (CLAUDE.md rule 1:
right market structure first; the fuel-invariant $/MWh net-revenue margin is
the more structurally-faithful gas bid than the fuel-scaled heat-rate
multiplier, so it is kept DESPITE worsening the backcast fit). Same cross-ISO
decision as ERCOT-100 / CAISO / NYISO-72 the same week.

The attestation carries the miso-81 keeper attestation (governance clauses +
the hand-curated measured-physical DOF rows ``build_dof_ledger`` does not
enumerate from config) VERBATIM and adds exactly ONE grounded DOF entry for
the net-revenue-margin anchor — zero fitted scalars, zero DOF delta otherwise
(the markup LEVELS are the already-registered ``offer_curve_by_group`` surface;
only the markup's gas-elasticity changes 1->0). The determination DOWNGRADES to
NOT-YET: two load-bearing gates flip PASS->FAIL vs the miso-81 keeper, both
marginal single-threshold crossings and both real margin effects, left
UNLEDGERED as MODEL MISSes per rule 1/10 (a determination is never rescued by
caveats): C1 fuelmix CC_REGULAR 2023 (-8.62 TWh, over +/-8.0) and C3b
price_shape 2025 (monthly-NRMSE 0.204, over the <=0.20 veto). The inherited
{C3a-2025, C3c} + storage caveats stand verbatim (the price_mean-2025 magnitude
is refreshed to the margin value -16.2%).

Usage: python scripts/gen_miso83_attestation.py  (after the bundle is solved)
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC81 = REPO / "results/calibration/miso81_phantom_outage/calibration_attestation.json"
DST = REPO / "results/calibration/miso_netrev_margin"

# The one grounded DOF entry the net-revenue-margin form adds (mirrors the
# same-week nyiso-72 anchor entry; the anchor is a measured identification
# constant, rule 23, not a fitted scalar — n_residual UNCHANGED at 2).
ANCHOR_ENTRY = {
    "name": "gas_offer_net_revenue_margin",
    "where": (
        "run_config.scenario_config.gas_offer_net_revenue_margin=True, "
        "gas_offer_margin_anchor=3.0492"
    ),
    "identification": "grounded",
    "lineage_solves": "charter neiso-61 precedent + miso-83 promotion (2026-07-24)",
    "value": (
        "Markup gas-elasticity 1->0 on the already-registered offer surface. "
        "Adds NO free parameter: the per-band markup LEVELS are the existing "
        "offer_curve_by_group residual (already counted above); the physical "
        "basis (phys_committed/econ_low/econ_high/peak) is measured CAMPD "
        "marginal-HR p50s (miso_campd_marginal_hr_summary.csv); the anchor "
        "3.0492 $/MMBtu is the measured 2023-25 delivered-gas overlay mean "
        "(GAS_OFFER_MARGIN_ANCHOR_BY_ISO['MISO']; per-plant EIA-923 monthly "
        "level + mean-preserving daily shape, year means 2.8392/2.4893/3.8190), "
        "not fitted. Re-derivable for a forward year from forward delivered gas "
        "+ the same CAMPD physical basis (rule 13). n_residual UNCHANGED at 2."
    ),
}

ATTESTED_BY = (
    "miso-83 gas-offer net-revenue margin keeper 2026-07-24 (OWNER OVERRIDE, "
    "CLAUDE.md rule 1 — right market structure first: the fuel-invariant $/MWh "
    "net-revenue margin is the more structurally-faithful gas bid than the "
    "fuel-scaled heat-rate multiplier, so it is promoted DESPITE worsening the "
    "backcast fit; same cross-ISO decision as ERCOT-100 / CAISO / NYISO-72 the "
    "same week). SINGLE delta gas_offer_margin=true on the "
    "2026-07-20-miso-81-phantom-outage keeper recipe (replay_keeper.build_kwargs "
    "strict replay of miso81_phantom_outage meta.json + --set "
    "gas_offer_margin=true), full span 2023-2025 per-year chained with "
    "--reuse-solved (rule 12, 15 GB box). Carries the miso-81 attestation + "
    "lever set verbatim; adds ONE grounded DOF entry for the anchor, zero "
    "fitted scalars, zero DOF delta otherwise."
)

NOTE = (
    "NET-REVENUE MARGIN FORM (gas_offer_net_revenue_margin=true, anchor 3.0492 "
    "$/MMBtu): each registered gas band's markup above its MEASURED physical "
    "basis (miso_campd_marginal_hr_summary.csv phys_* p50s) is repriced from "
    "the fuel-scaled multiplicative form to a fuel-INVARIANT $/MWh net-revenue "
    "margin — the structurally-correct offer form (rule 1). At anchor gas the "
    "offers reduce EXACTLY to the registered offer_curve_by_group multipliers; "
    "the markup's gas-elasticity goes 1->0 (fuel-scaled multiplier -> fixed "
    "$/MWh margin; the mc-side compression fires on 591/597/595 gas tranches in "
    "2023/2024/2025, median fixed margin ~9.7 $/MWh). ZERO fitted scalars: the "
    "markup LEVELS are the already-registered offer surface, only the elasticity "
    "changes; the anchor is the measured 2023-25 delivered-gas overlay mean, "
    "re-derives only on a gas source-data change (rule 23). Determination "
    "NOT-YET — an owner-override promotion for STRUCTURAL FIDELITY, not fit "
    "(rule 1): two load-bearing gates flip PASS->FAIL vs the miso-81 keeper, "
    "both marginal single-threshold crossings and both real margin effects, "
    "left UNLEDGERED as MODEL MISSes per rule 1/10 — C1 fuelmix CC_REGULAR 2023 "
    "model 133.20 vs actual 141.82 TWh = -8.62 TWh (over +/-8.0; the "
    "below-anchor firming sheds ~0.86 TWh CC dispatch) and C3b price_shape 2025 "
    "monthly-NRMSE 0.204 (over the <=0.20 veto). Kept per rule 1 (structure over "
    "fit), NOT rescued by tuning. Inherited {C3a-2025 price_mean -16.2%, C3c "
    "price_tail 0/6/0 vs RT 30/37/88} + storage C5b/C5c caveats still apply. The "
    "A/B refuted the charter's pre-registered C3b bar (margin duration-NRMSE "
    "worse all three years) — the promotion is a rule-1 structural call, not a "
    "fit result. Supersedes 2026-07-20-miso-81-phantom-outage."
)

DISCLOSURE_NOTE = (
    "See metrics.json determination + reasons (NOT-YET). Owner-override "
    "promotion for structural fidelity (rule 1): the net-revenue margin is the "
    "go-forward gas offer form (cross-ISO ERCOT-100 / CAISO / NYISO-72). The "
    "A/B refuted the charter's pre-registered C3b bar (margin duration-NRMSE "
    "worse all three years); the promotion is a rule-1 structural call, not a "
    "fit result, and nothing was tuned to rescue it (rule 1/10). The two new "
    "FAILs (fuelmix CC_REGULAR 2023, price_shape 2025) are UNLEDGERED MODEL "
    "MISSes; the inherited {C3a-2025, C3c} + storage caveats stand."
)


def main() -> None:
    """Write the miso-83 attestation from the miso-81 keeper attestation."""
    att = json.loads(SRC81.read_text())

    fp = att["free_parameters"]
    have = {e["name"] for e in fp["entries"]}
    if ANCHOR_ENTRY["name"] not in have:
        fp["entries"].append(ANCHOR_ENTRY)
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e["identification"] == "residual"
    )

    att["governance"]["attested_by"] = ATTESTED_BY
    att["governance"]["note"] = NOTE
    att["disclosures"]["note"] = DISCLOSURE_NOTE

    # Refresh the inherited price_mean-2025 caveat magnitude to the margin value
    # (the only inherited exception whose number moved; storage + C3c are
    # byte-identical to the miso-81 keeper).
    for e in att.get("exceptions", []):
        if e.get("criterion") == "price_mean" and int(e.get("year", -1)) == 2025:
            e["magnitude"] = (
                "model $38.05 vs actual RT $45.39 (-16.2%; vs DA $46.29 -17.8%) "
                "— the ledgered {C3a-2025} scarcity-tail level gap (miso-82 "
                "external-validation frontier), unchanged in kind by the margin"
            )

    DST.joinpath("calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {DST / 'calibration_attestation.json'}  "
        f"(ledger {fp['n_entries']} entries / {fp['n_residual']} residual)"
    )


if __name__ == "__main__":
    main()
