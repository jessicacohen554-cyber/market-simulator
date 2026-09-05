"""Write the ercot-213 published-anchor bundle's governance attestation.

The ercot-213 promotion (`docs/PRECOMMIT-ercot213-published-anchor-2026-08-16.md`,
`docs/FINDING-ercot213-published-anchor-2026-08-16.md`) arms two booleans on the
ercot-204 keeper recipe and adds **ZERO fitted scalars**:

* ``ercot_reserve_supply_cap_net_credits`` (ercot-212) — the measured LR +
  storage-AS credit series are netted off the measured reserve-supply caps, so
  the same MW cannot be credited on the demand side while riding a supply cap
  whose telemetry already contains it;
* ``ercot_ordc_adder_published_anchor`` (ercot-213) — the cap-additive RTORPA is
  priced on the published ``(VOLL - lambda)`` anchor from a SINGLE counterpart
  (the all-tier total-reserve cap dual), capped at ``VOLL - lambda``.

Every input is an already-armed measured series, a published design parameter,
or an LP dual: VOLL is the registered ``ScenarioConfig.ordc_voll``, lambda is
the LP's own demand-weighted energy dual, the counterpart is a cap-row dual.
So ``free_parameters`` is not edited here — it is rebuilt by
``scripts/build_dof_ledger.py`` and asserted to carry the SAME residual count as
the superseded keeper.

The C3c exceptions ledger is re-derived rather than carried verbatim, because
the arm moves two of the three years INTO their bands: 2023 (123 h vs actual
181) and 2024 (33 vs 53) now PASS and their ledger entries are DROPPED, leaving
2025 as the only remaining C3c caveat. Dropping a spent caveat is the honest
direction — a ledger entry for a passing year would overstate what the run needs
excused.

Usage::

    PYTHONPATH=.:src ./.venv/bin/python scripts/gen_ercot213_attestation.py \
        --bundle results/calibration/ercot213_anchor_B
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}
# Years whose C3c still FAILS on this bundle's own scorecard, i.e. the years
# that still need a ledger entry (calibration_verdict.py, run
# 2026-08-16-ercot213-arm-pubanchor: 2023 and 2024 pass their bands).
STILL_FAILING = (2025,)

_ATTEST = (
    "ercot-213 session (2026-08-16): the ANCHORING-CORRECT successor named by "
    "docs/FINDING-ercot212-reserve-basis-phase0-2026-08-16.md §5. Two booleans "
    "on the ercot-204 keeper recipe, ZERO fitted scalars, ZERO new numeric "
    "values: (1) ercot_reserve_supply_cap_net_credits nets the ALREADY-ARMED "
    "measured LR RRS-UFR + storage AS-award credit series off the measured "
    "RTOLCAP/RTOFFCAP supply caps, an arithmetic consistency repair of the "
    "armed construction (the telemetry already contains the credited MW, so "
    "leaving the caps gross let the ORDC total family's marginal level reach "
    "cap + credits); (2) ercot_ordc_adder_published_anchor prices the "
    "cap-additive RTORPA on the PUBLISHED (VOLL - lambda) anchor from a SINGLE "
    "counterpart (the all-tier total-reserve cap dual), capped at "
    "VOLL - lambda. The in-LP ORDC demand curve is VOLL-anchored, which is the "
    "co-optimization-correct form (an LP objective coefficient must be a "
    "constant and lambda is endogenous); writing that dual verbatim into an "
    "ADDITIVE channel, summed over BOTH headroom tiers, over-prices by the "
    "missing lambda subtraction and can emit 2 x VOLL — a price ERCOT's own "
    "protocol cap (lambda + adders <= VOLL) cannot produce. VOLL is the "
    "registered ordc_voll, lambda is the LP's own demand-weighted energy dual, "
    "the counterpart is an LP dual: nothing is fitted and nothing is tuned to "
    "a residual. Verified by the pre-registered G-CAP gate on this bundle's own "
    "committed sidecars: ZERO protocol-cap violations in all 26,280 solved "
    "hours, with 2023's maximum landing at lambda $298.86 + adder $4,701.14 = "
    "exactly $5,000.00 = VOLL. Per "
    "docs/PRECOMMIT-ercot213-published-anchor-2026-08-16.md."
)
_CARRY = (
    " CARRIED ONTO THE ercot-213 PUBLISHED-ANCHOR PROMOTION, AND NARROWED: "
    "this run repairs the additive RTORPA's basis and price form, which moves "
    "the modelled scarcity tail materially TOWARD the actual in every year "
    "(2023 58 -> 123 of 181, 2024 22 -> 33 of 53, 2025 1 -> 3 of 31) and "
    "brings 2023 and 2024 INSIDE their bands, so their ledger entries are "
    "DROPPED and only this one remains. The accepted model-class limitation is "
    "unchanged in kind: an LP on competitive/measured offers cannot form "
    "ERCOT's realized RT tail equilibrium, and a correctly anchored reserve "
    "adder narrows that gap without closing it. The count is re-measured on "
    "this run and reported at full magnitude."
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
    """Write the promoted bundle's attestation from the ercot-204 keeper's."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument(
        "--keeper",
        type=Path,
        default=REPO / "results/calibration/ercot204_rule26_delete",
    )
    args = ap.parse_args()

    keeper_attest = json.loads(
        (args.keeper / "calibration_attestation.json").read_text()
    )
    att = json.loads(json.dumps(keeper_attest))  # deep copy
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST

    counts = _tail_counts(args.bundle)
    kept = []
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") != "price_tail":
            kept.append(exc)
            continue
        if year not in STILL_FAILING:
            continue  # band now met on this bundle — a spent caveat is dropped
        exc["magnitude"] = (
            f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
            f"> $200/MWh (re-measured on the ercot-213 published-anchor run)"
        )
        exc["reason"] = (
            re.sub(r"\s*CARRIED ONTO THE ercot-2[0-9]+.*$", "", exc.get("reason", ""))
            + _CARRY
        )
        kept.append(exc)
    att["exceptions"] = kept

    path = args.bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; C3c ledger entries kept: "
        f"{[e['year'] for e in kept if e.get('criterion') == 'price_tail']}; "
        "free_parameters left to build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
