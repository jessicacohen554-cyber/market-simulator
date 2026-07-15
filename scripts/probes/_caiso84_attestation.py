"""Write the caiso-84 probe attestation.

Derives the bundle's ``calibration_attestation.json`` from the caiso-80 keeper
attestation already committed in the repo (same lever set and DOF ledger — the
probe adds NO free parameter: the single delta is the gated
``caiso_citygate_spot_level`` measured-series swap,
FINDING-caiso-winter-gas-level-2026-07-15), swapping the ``attested_by`` line
and appending the probe's single-delta note. Deterministic from repo state
(_caiso80/82_attestation.py pattern).

Usage: python scripts/probes/_caiso84_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso80_supply_consistent_demand" / "calibration_attestation.json"

DELTA84 = (
    " PLUS the single caiso-84 delta: caiso_citygate_spot_level=True "
    "(FINDING-caiso-winter-gas-level-2026-07-15). The CAISO gas hub overlay "
    "(gas_hub_basis_overlay, default-on for CAISO) is RE-LEVELLED from the EIA "
    "N3050CA3 monthly citygate SURVEY (an LDC purchase-portfolio average "
    "acquisition cost — bidweek contracts, storage withdrawals, hedges — sitting "
    ">1.2x daily spot in 24/33 covered months, Jan-2023 $28.08 vs $16.1) onto "
    "the measured California Composite Average daily citygate SPOT series the "
    "cost-based DEB actually prices the marginal unit at "
    "(data/raw/gas-prices/caiso_citygate_daily.csv, the EIA NG Weekly compact "
    "spot table Transco Z6 NY is read from), taking BOTH the within-month shape "
    "and the monthly level from the daily series "
    "(fuel._caiso_hub_daily_gas_prices spot_level=True: each month's absolute "
    "calendar-interpolated daily prices, not renormalized to the survey level). "
    "Coverage is unchanged — a pure LEVEL swap on the keeper's covered months; a "
    "survey-uncovered month (CAISO 2025 Sep-Nov, no basis row) stays on the base "
    "EIA-923 series exactly as in the keeper. The +$0.46 "
    "CAISO_CITYGATE_TRANSPORT_ADDER still applies. ZERO new free parameters, "
    "zero fitted values: both series are measured EIA data and the "
    "marginal-offer representation requires the daily spot (rule 15); "
    "identification is the EIA Weekly compact spot table, re-derives only on "
    "source updates (rule 23), never an output pinned back (rule 14 — the level "
    "is the measured daily-spot mean, not tuned to the LMP residual; the "
    "sign of the survey-vs-spot wedge REVERSES in Mar/Oct-2023, which a "
    "residual-fitted knob could not do). Forward story unchanged: forecast years "
    "have no daily realization and keep the HH-forward + climatological-basis "
    "path (F923 delivered-price admissibility class, rule 13). No residual-tuned "
    "adder is armed in this run; the DOF ledger is identical to the caiso-80 "
    "keeper (no scalar added)."
)

TARGETS = [
    (
        "caiso84_gas_spot_level",
        "caiso-84 measured daily-spot gas-level probe session 2026-07-15",
        DELTA84,
    ),
]


def main() -> None:
    """Derive and write the probe attestation."""
    base = json.loads(BASE.read_text())
    for bundle, attested_by, delta in TARGETS:
        out_dir = ROOT / bundle
        if not out_dir.exists():
            print(f"[skip] {bundle}: bundle dir absent")
            continue
        d = json.loads(json.dumps(base))
        d["governance"]["attested_by"] = attested_by
        d["governance"]["note"] = d["governance"]["note"] + delta
        (out_dir / "calibration_attestation.json").write_text(json.dumps(d, indent=1))
        print(f"[ok  ] {bundle}")


if __name__ == "__main__":
    main()
