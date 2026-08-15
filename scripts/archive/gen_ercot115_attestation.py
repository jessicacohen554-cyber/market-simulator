"""Generate the ercot-115 keeper bundle's DOF ledger (CLAUDE.md rule 20).

Derives the new ERCOT keeper's ``calibration_attestation.json`` from the
outgoing keeper's, applying exactly one delta — the one the ercot-115 promotion
makes:

``COAL_PRB.econ_low`` leaves the residual-identified surface. It was a FITTED
0.400 with no measurement behind it, tuned on the price/volume residual across
the ERCOT lineage. The promotion replaces it with the ISO's own measured CAMPD
marginal (incremental) heat rate, 0.886 — a rule-13 measured input, frozen
against residuals (rule 23) and re-derived only when its source data updates.
So the ``offer_curve_by_group`` ledger entry drops that band (112 -> 111 free
scalars) and a new ``measured-physical`` entry records where the value now
comes from.

**No governance block is written.** The C6 gate requires asserting all four
claims, including ``levers_trace_to_measured_input``; that is FALSE for this
configuration, which still carries eight residual-identified DOF entries. The
outgoing keeper is UNATTESTED for the same reason, so the new keeper is
like-for-like. Retiring one fitted scalar is progress on that surface, not the
end of it — asserting otherwise to turn a gate green is the self-deception the
rubric exists to catch.

Run from the repo root:
    python scripts/gen_ercot115_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SOURCE = REPO / "results" / "calibration" / "ercot_netrev_margin"
TARGET = REPO / "results" / "calibration" / "ercot115_coal_floor_only"

# The band the promotion retires from the fitted surface, and its measured
# replacement (data/raw/reference/ercot_campd_marginal_hr_summary.csv, COAL row,
# marg_econ_low_p50; scripts/data/derive_campd_marginal_hr.py).
RETIRED_CLASS, RETIRED_BAND = "COAL_PRB", "econ_low"
FITTED_VALUE, MEASURED_VALUE = 0.400, 0.886


def build(source: dict) -> dict:
    """Return the new ledger: one band moved from residual to measured."""
    out = json.loads(json.dumps(source))  # deep copy
    fp = out["free_parameters"]
    entries = fp["entries"]

    curve = next(e for e in entries if e["name"] == "offer_curve_by_group")
    bands = curve["value"][RETIRED_CLASS]
    if RETIRED_BAND not in bands:
        raise SystemExit(
            f"{RETIRED_CLASS}.{RETIRED_BAND} is not in the outgoing ledger — "
            "the source attestation is not the expected pre-promotion keeper"
        )
    curve["value"][RETIRED_CLASS] = [b for b in bands if b != RETIRED_BAND]
    curve["n_scalars"] = int(curve["n_scalars"]) - 1
    curve["source"] = (
        curve["source"]
        + f" — MINUS {RETIRED_CLASS}.{RETIRED_BAND}, which the ercot-115 "
        "promotion moved to the measured CAMPD marginal-HR basis (entry below)"
    )

    entries.append(
        {
            "name": "coal_econ_marginal_hr_bound floor (COAL econ bands)",
            "where": (
                "backcast_config(iso='ERCOT').coal_econ_marginal_hr_bound -> "
                "data.coal.apply_coal_econ_marginal_hr_floor"
            ),
            "identification": "measured-physical",
            "lineage_solves": (
                "0 residual solves — the value is read from the frozen derive "
                "artifact, never tuned (rule 23)"
            ),
            "value": {
                f"{RETIRED_CLASS}.{RETIRED_BAND}": MEASURED_VALUE,
                "was_fitted": FITTED_VALUE,
                "marg_econ_high_p50": 0.898,
            },
            "n_scalars": 0,
            "source": (
                "data/raw/reference/ercot_campd_marginal_hr_summary.csv, COAL "
                "row, marg_econ_low_p50 / marg_econ_high_p50 — the slope "
                "d(heatInput)/d(grossLoad) of each unit's own CEMS "
                "input-output curve at the band-representative load, "
                "capacity-weighted over 25 units and pooled across the "
                "available years (scripts/data/derive_campd_marginal_hr.py). "
                "An already-committed unit's next MWh cannot cost less than "
                "its own measured incremental burn, so this is the physical "
                "LOWER bound on the band's offer multiplier, not a fit."
            ),
            "root_cause": (
                "CLOSED as a free parameter: the band is no longer identified "
                "from the residual. It is a measured input that regenerates "
                "for a forward year from the same CEMS derivation and responds "
                "to changed conditions (rule 13), and it is frozen against "
                "residuals — re-derived only on a source-data update (rule 23). "
                "Only bands BELOW the measured basis are lifted; a genuine "
                "markup above it stays on the fitted surface above."
            ),
        }
    )

    fp["n_entries"] = len(entries)
    fp["n_residual"] = sum(1 for e in entries if e["identification"] == "residual")
    fp["seeded"] = (
        str(fp.get("seeded", ""))
        + " | amended 2026-07-26 (ercot-115 promotion): COAL_PRB.econ_low "
        "0.400 (fitted) -> 0.886 (measured CAMPD marginal HR); "
        "offer_curve_by_group 112 -> 111 free scalars"
    )
    return out


def main() -> None:
    """Write the new bundle's attestation from the outgoing keeper's."""
    src = json.loads((SOURCE / "calibration_attestation.json").read_text())
    out = build(src)
    path = TARGET / "calibration_attestation.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    fp = out["free_parameters"]
    print(f"wrote {path.relative_to(REPO)}")
    print(f"  entries {fp['n_entries']} (residual {fp['n_residual']})")
    curve = next(e for e in fp["entries"] if e["name"] == "offer_curve_by_group")
    print(f"  offer_curve_by_group free scalars: {curve['n_scalars']}")
    print(f"  {RETIRED_CLASS} bands now: {curve['value'][RETIRED_CLASS]}")


if __name__ == "__main__":
    main()
