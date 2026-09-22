"""SOCO hydro-4: write ``calibration_attestation.json`` for one hydro-physics probe arm.

Adapted from :mod:`scripts.gen_soco58_attestation` (the SOCO desk's convention),
whose ``_verify`` is REUSED unchanged to assert everything this lane inherits
from the keeper ``2026-09-22-soco58-warm-committed``: the four price-tuning
bands at the identity 1.0, no overrides/deltas/smoothing, historic outages,
``coal_warm_committed`` armed with no second coal-committed mechanism, the
keeper recipe, SOCO-55's measured gas basis and SOCO's own rule-25 source.

What this module adds is the lane's own delta, asserted on the RESOLVED
``scenario_config`` and ``meta.json``:

* ``--arm mff`` — ``hydro_min_flow_floor`` ON, ``hydro_ror_split`` OFF;
* ``--arm ror`` — ``hydro_ror_split`` ON, ``hydro_min_flow_floor`` OFF
  (rule 19 ``[R-ONE-MECH]``: the two are one family and are never stacked);
* both — ``hydro_backfill_year = 2024`` (SOCO-53b), a measured no-op on the
  2023/2024 budgets and the 2025 early-release repair (PRECOMMIT addendum A).

Both hydro gates are registered booleans with no scalar of their own. The floor
LEVEL is the measured EIA-930 monthly Q05 of ``NG: WAT``; the RoR flat level is
each plant's own EIA-923 monthly budget over the month's hours, and the RoR
partition is the categorical ORNL EHA ``Mode`` label. No value is chosen, so
``n_residual`` is unchanged. Pre-registration:
``docs/handoffs/PRECOMMIT-soco-hydro-4-2026-09-22.md``.

Usage::

    python3 scripts/gen_soco_h4_attestation.py --arm mff \\
        --bundle results/calibration/soco_h4_mff_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gen_soco58_attestation import (  # noqa: E402
    MEASURED_BASIS,
    PRICE_TUNING_BANDS,
    _verify as _verify_inherited,
)

#: arm tag -> (the arm's delta field, the family member that must stay OFF).
ARMS: dict[str, tuple[str, str]] = {
    "mff": ("hydro_min_flow_floor", "hydro_ror_split"),
    "ror": ("hydro_ror_split", "hydro_min_flow_floor"),
}
#: PRECOMMIT addendum A — the SOCO-53b 2025 budget repair.
REPAIR_BACKFILL_YEAR = 2024

HYDRO_ENTRY_BASIS = {
    "hydro_min_flow_floor": (
        "Boolean gate, n_scalars=0. The floor LEVEL is the measured monthly Q05 of "
        "SOCO's own EIA-930 NG: WAT for the solve year "
        "(eia930/envelopes.measured_hydro_min_flow_level, HYDRO_MIN_FLOW_PERCENTILE), "
        "allocated pro-rata by each plant's own EIA-923 monthly budget and clipped to "
        "it. Stated misalignment (rule 14): SOCO's NG: WAT folds pumped-storage "
        "discharge before 2024-07-15; measured in 2025, where both series exist, the "
        "fold moves the monthly Q05 by <= +11 MW. EIA-930 WAT is missing "
        "2024-11-25..12-31, so December 2024 carries no floor (empty month -> 0)."
    ),
    "hydro_ror_split": (
        "Boolean gate, n_scalars=0. The partition is the categorical ORNL EHA FY2024 "
        "Mode label (curate_hydro_plant_modes.py --iso SOCO: 45 plants, 17 "
        "run-of-river-class; 94 % of hydro energy by direct EHA label, completion "
        "rules 5.5-6.4 %, completion validation 30/40 plants / 71.3 % of labelled MW). "
        "The flat level is each RoR plant's own EIA-923 monthly budget / hours, "
        "clipped to nameplate (<= 211 MWh/yr clipped)."
    ),
}


def verify(sc: dict, meta: dict, arm: str) -> None:
    """Raise unless the bundle is exactly the declared hydro-4 arm off the keeper."""
    _verify_inherited(sc)
    field, other = ARMS[arm]
    if sc.get(field) is not True or sc.get(other) is not False:
        raise SystemExit(
            f"{field}={sc.get(field)!r} {other}={sc.get(other)!r}: expected "
            f"{field}=True, {other}=False (rule 19, never stacked)"
        )
    for name in (
        "hydro_pondage_bound",
        "hydro_dispatch_envelope",
        "hydro_budget_period_by_instrument",
        "hydro_cascade_coupling",
    ):
        if sc.get(name):
            raise SystemExit(f"{name} armed alongside {field} (rule 19)")
    if meta.get("hydro_backfill_year") != REPAIR_BACKFILL_YEAR:
        raise SystemExit(
            f"meta hydro_backfill_year={meta.get('hydro_backfill_year')!r}"
        )
    if meta.get("hydro_eia930_monthly"):
        raise SystemExit("hydro_eia930_monthly armed — SOCO's PS split is unregistered")


def retag(att: dict, sc: dict, arm: str) -> None:
    """Carry SOCO's offer-curve re-tag, the inherited basis, and the hydro entries."""
    fp = att.get("free_parameters")
    if not fp:
        raise SystemExit("free_parameters absent — run build_dof_ledger.py first")
    oc = sc.get("offer_curve_by_group") or {}
    bands = {
        b: sorted({oc[g][b] for g in oc if b in oc[g]}) for b in PRICE_TUNING_BANDS
    }
    for entry in fp["entries"]:
        if entry["name"] in ("offer_curve_by_group", "offer_curve_smoothing"):
            entry["identification"] = "measured-physical"
            entry["basis"] = (
                f"Price-tuning bands at the identity (distinct values {bands}); "
                "overrides/deltas/smoothing null — machine-verified by "
                "gen_soco58_attestation._verify. SOCO has no price benchmark."
            )
            entry.pop("root_cause", None)
    have = {e["name"] for e in fp["entries"]}
    for year, value in sorted(MEASURED_BASIS.items()):
        name = f"GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'][{year}]"
        if name not in have:
            fp["entries"].append(
                {
                    "name": name,
                    "value": value,
                    "identification": "measured-physical",
                    "basis": "INHERITED FROM SOCO-55 (EIA-923 Sch-2 delivered gas minus Henry Hub).",
                }
            )
    field = ARMS[arm][0]
    if field not in have:
        fp["entries"].append(
            {
                "name": field,
                "value": True,
                "identification": "measured-physical",
                "n_scalars": 0,
                "basis": HYDRO_ENTRY_BASIS[field],
            }
        )
    if "hydro_backfill_year" not in have:
        fp["entries"].append(
            {
                "name": "hydro_backfill_year",
                "value": REPAIR_BACKFILL_YEAR,
                "identification": "measured-physical",
                "n_scalars": 0,
                "basis": (
                    "SOCO-53b data repair, not a tuned value: the 2025 EIA-923 early "
                    "release carries 5 of 42 SOCO hydro plants (0.328 TWh vs 5.926 TWh "
                    "EIA-930 measured); backfilling from the 2024 final census restores "
                    "42 plants / 6.329 TWh (+6.8 % vs measured, 2024 monthly shape). "
                    "Array-equal no-op on the 2023 and 2024 budgets (asserted by "
                    "scripts/probes/soco_h4_compose_span.py)."
                ),
            }
        )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )


def main() -> None:
    """Verify the arm and write its attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--bundle", required=True)
    a = ap.parse_args()
    bundle = Path(a.bundle)
    att_path = bundle / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    sc = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    meta = json.loads((bundle / "meta.json").read_text())
    verify(sc, meta, a.arm)
    field, other = ARMS[a.arm]
    att["schema"] = "calibration-attestation/v1"
    att["exceptions"] = []
    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "attested_by": (
            f"SOCO hydro-4 (lane), PROBE arm '{a.arm}'. Against keeper "
            "2026-09-22-soco58-warm-committed, TWO things move, each machine-verified: "
            f"(1) {field}=True with {other}=False — one member of the hydro "
            "run-of-river-inflow family, never stacked (rule 19); (2) "
            "hydro_backfill_year=2024, the SOCO-53b repair of the 2025 EIA-923 "
            "early-release budget (5 of 42 plants), a measured array-equal no-op on "
            "2023/2024 — so 2023/2024 are single-delta legs against the keeper and "
            "the 2025 arm is single-delta against a repair-only control leg "
            "(soco_h4_fix_2025, not registered: a control, rule 29(c)). "
            "Every inherited posture is asserted by gen_soco58_attestation._verify. "
            "RULE 13: no measured OUTCOME is fed back — the floor level is a measured "
            "physical availability quantity (the fleet's Q05 sustained release), the "
            "RoR partition a categorical plant attribute, and the flat level the "
            "plant's own monthly water; all regenerate forward. Neither mechanism may "
            "move a monthly total: annual hydro TWh moved 0.0000 % in every leg (G2). "
            "RULE 21/24: zero free parameters added; both gates are registered "
            "booleans. GATE G17: SOCO has no price benchmark; every "
            "offer_curve_by_group band is 1.0, AUTHORIZED PRICE TUNING IS DECLARED "
            "NONE (no authorized_price_tuning key, SOCO convention). Gates were "
            "pre-registered in docs/handoffs/PRECOMMIT-soco-hydro-4-2026-09-22.md "
            "before any solve; no criterion selects between the two arms (rule 1)."
        ),
    }
    att["disclosures"] = {
        "precommit": "docs/handoffs/PRECOMMIT-soco-hydro-4-2026-09-22.md",
        "probe": True,
        "eia930_wat_gap": "SOCO NG: WAT missing 2024-11-25..12-31 (1,343 h) and 121 h of 2025-01",
        "ps_fold": "SOCO NG: WAT folds PS discharge before 2024-07-15; floor bias <= +11 MW",
    }
    retag(att, sc, a.arm)
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path} (n_residual={att['free_parameters']['n_residual']})")


if __name__ == "__main__":
    main()
