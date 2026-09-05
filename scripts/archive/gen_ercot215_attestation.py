"""Write the ercot-215 counterpart-decontamination bundle's governance attestation.

The ercot-215 promotion (`docs/PRECOMMIT-ercot215-counterpart-decontamination-
2026-08-17.md`, owner-instructed per its §0) arms ONE boolean on the ercot-213
keeper recipe and adds **ZERO fitted scalars**:

* ``ercot_ordc_adder_family_counterpart`` (ercot-215) — inside the armed
  published-anchor branch, the additive RTORPA's counterpart is decontaminated
  to the ORDC component of the all-tier cap dual,
  ``gamma' = min(gamma_all, gamma_ordc_family)``, dropping the AS-product
  shortfall-ramp term the ercot-214 decomposition isolated exactly in 808/808
  writing hours (a price-formation channel the 2023-25 design cannot emit —
  no RT per-product scarcity pricing; a product-vs-capability squeeze triggers
  RUC, not a price).

Both operands are LP duals of the same solve; nothing is fitted. So
``free_parameters`` is not edited here — it is rebuilt by
``scripts/build_dof_ledger.py`` and asserted to carry the SAME residual count
as the superseded keeper.

The C3c exceptions ledger is RE-DERIVED, and here the honest direction is the
reverse of ercot-213's: the decontamination removes the phantom channel that
was carrying the keeper's tail, so 2023 (67 h vs actual 181) and 2024 (22 vs
53) move back OUT of their bands and their ledger entries are RE-ADDED — the
2023/2024 reason chains are carried from the ercot-204 attestation (the last
keeper that ledgered them, with the full owner-decision genealogy), and 2025's
from the ercot-213 keeper's own entry. All three magnitudes are re-measured on
this bundle and reported at full magnitude, per the precommit §4's
pre-registered post-promotion scorecard.

Usage::

    PYTHONPATH=.:src python scripts/gen_ercot215_attestation.py \
        --bundle results/calibration/ercot215_decontam_B
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}
# Source of each year's reason chain: 2023/2024 re-enter the ledger, so their
# chains come from the LAST keeper that ledgered them (ercot-204, full
# owner-decision genealogy); 2025 never left, so its chain is the current
# keeper's (ercot-213).
CHAIN_SOURCE = {
    2023: "ercot204_rule26_delete",
    2024: "ercot204_rule26_delete",
    2025: "ercot213_anchor_B",
}

_ATTEST = (
    "ercot-215 session (2026-08-17): the counterpart decontamination of the "
    "published-anchor additive RTORPA, built from the ercot-214 exact "
    "identification (docs/FINDING-ercot214-gspur-phase0-2026-08-17.md) and "
    "promoted ON DIRECT OWNER INSTRUCTION given in advance (PRECOMMIT-ercot215 "
    "§0) over the pre-registered G-C3c kill. ONE boolean on the ercot-213 "
    "keeper recipe, ZERO fitted scalars, ZERO new numeric values: "
    "ercot_ordc_adder_family_counterpart writes the ORDC component of the "
    "all-tier reserve-supply-cap dual instead of the contaminated sum — "
    "gamma' = min(gamma_all, gamma_ordc_family), where gamma_ordc_family is "
    "the ercot_ordc_total family's own balance-row dual (the same series every "
    "bundle persists to the reserve_family sidecar). The dropped term is the "
    "AS-product shortfall-ramp step (VOLL / ercot_as_n_ramp = $416.67), "
    "measured to decompose the cap dual EXACTLY (integer k) in 808/808 "
    "adder-writing hours across 2023-25; the 2023-25 design cannot emit it as "
    "a price (no RT per-product scarcity pricing — a product-vs-capability "
    "squeeze triggers RUC commitment, not a price; "
    "model/reserves/spec.py, the ercot_ordc_only_scarcity citation block), "
    "and the family dual is the faithful published-RTORPA mirror in both "
    "regimes (rank-corr 0.709/0.807/0.758). Anchor, single-counterpart form, "
    "protocol cap and netting UNTOUCHED; the ramp's in-LP withholding role is "
    "untouched — only its export into the written price stops. Both operands "
    "are LP duals of the same solve: nothing is fitted and nothing is tuned "
    "to a residual. Verified by the pre-registered G-EXACT gate: the armed "
    "member reproduces the ercot-214 pre-solve counterfactual exactly "
    "(spurious hour sets, adder incidence 564/175/37 // 177/36/3 // 67/5/0, "
    "max adders 4701.14/355.98/14.61, zero G-CAP violations) with every "
    "non-system hourly sidecar byte-identical to the keeper's. Per "
    "docs/PRECOMMIT-ercot215-counterpart-decontamination-2026-08-17.md."
)
_CARRY = (
    " CARRIED ONTO THE ercot-215 COUNTERPART-DECONTAMINATION PROMOTION, AND "
    "RE-OPENED AT FULL WIDTH: the ercot-213 keeper's tail gains (2023 123/181, "
    "2024 33/53) were measured at ercot-214 §2 to ride the AS-product "
    "shortfall-ramp leak — a phantom price-formation channel (116/117 of "
    "2023's deep adder hours contaminated; published settled RTORPA p50 $14.2 "
    "there, > $100 in only 15 h vs the arm's 117; the real 2023 tail was "
    "conduct-made, actual > $200 in 181 h against 17 h of > $100 published "
    "adder). Removing the channel returns the tail to this model-class "
    "ledger where ercot-209/211 adjudicated it: the accepted limitation is "
    "unchanged in kind — an LP on competitive/measured offers cannot form "
    "ERCOT's realized RT tail equilibrium, and a decontaminated reserve adder "
    "no longer manufactures it through a channel the market does not have. "
    "The count is re-measured on this run and reported at full magnitude."
)


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year, on the SCORER'S OWN max-zonal basis
    (reproduces ``ordc.hoursGt200.model`` — see gen_ercot192_attestation)."""
    out: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        out[year] = int((df.groupby("hour")["price"].max() > 200.0).sum())
    return out


def main() -> None:
    """Write the promoted bundle's attestation from the keeper lineage's."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument(
        "--keeper",
        type=Path,
        default=REPO / "results/calibration/ercot213_anchor_B",
    )
    args = ap.parse_args()

    keeper_attest = json.loads(
        (args.keeper / "calibration_attestation.json").read_text()
    )
    att = json.loads(json.dumps(keeper_attest))  # deep copy
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST

    # Reason-chain sources, keyed by bundle dir name.
    chains: dict[int, dict] = {}
    for year, src in CHAIN_SOURCE.items():
        src_att = json.loads(
            (
                REPO / "results/calibration" / src / "calibration_attestation.json"
            ).read_text()
        )
        for exc in src_att.get("exceptions", []):
            if exc.get("criterion") == "price_tail" and int(exc.get("year", 0)) == year:
                chains[year] = json.loads(json.dumps(exc))
    missing = [y for y in YEARS if y not in chains]
    if missing:
        raise SystemExit(f"no source price_tail chain found for {missing}")

    counts = _tail_counts(args.bundle)
    non_tail = [
        e for e in att.get("exceptions", []) if e.get("criterion") != "price_tail"
    ]
    tail_entries = []
    for year in YEARS:
        exc = chains[year]
        exc["magnitude"] = (
            f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
            f"> $200/MWh (re-measured on the ercot-215 counterpart-"
            "decontamination run)"
        )
        exc["reason"] = (
            re.sub(r"\s*CARRIED ONTO THE ercot-2[0-9]+.*$", "", exc.get("reason", ""))
            + _CARRY
        )
        tail_entries.append(exc)
    att["exceptions"] = non_tail + tail_entries

    path = args.bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; C3c ledger entries: "
        f"{[e['year'] for e in tail_entries]}; "
        "free_parameters left to build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
