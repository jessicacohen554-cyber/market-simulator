"""Write the ercot-223 event-realized-release A/B pair's governance attestations.

The ercot-223 repair (`docs/PRECOMMIT-ercot223-event-release-guard-2026-08-19.md`)
arms ONE default-off boolean on the CURRENT keeper recipe
(`2026-08-19-ercot221-arm-adaptive`) with ZERO new numeric constants:

* ``ercot_adaptive_event_release`` — mask the ercot-221 adaptive floor at
  in-window hours whose pass-1 settle basis (the identical series the
  mechanism's own day-max event detector reads; pure model path, zero
  measured content) is >= ``ERCOT_ADAPTIVE_EVENT_USD`` ($1,000, the
  mechanism's existing frozen event constant reused at hour granularity).
  Repairs the keeper's manufactured 2024 h3066 load shed (its one failing
  kill gate), whose root cause — offer-as-cost debasing the storage SOC
  shadow against the co-opt's floor-free reserve-headroom value — is
  measured in ``results/calibration/ercot223_shed_phase0.json``.

``free_parameters`` is not edited here — it is rebuilt by
``scripts/build_dof_ledger.py`` afterwards (G-DOF reads that).

Usage::

    PYTHONPATH=.:src python scripts/gen_ercot223_attestation.py \
        --arm results/calibration/ercot223_release_arm \
        --control results/calibration/ercot223_control_replay \
        --still-failing 2023 2024 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}
KEEPER = REPO / "results/calibration/ercot221_adaptive_B"

_ATTEST_ARM = (
    "ercot-223 session (2026-08-19): the EVENT-REALIZED RELEASE guard "
    "(PRECOMMIT-ercot223-event-release-guard-2026-08-19.md), ONE default-off "
    "boolean on the ercot-221 keeper recipe (ercot_adaptive_event_release) "
    "with ZERO new numeric constants — the mask threshold is the mechanism's "
    "own existing frozen event constant ERCOT_ADAPTIVE_EVENT_USD ($1,000) "
    "reused at hour granularity. Grounding: the Phase-0 diagnosis "
    "(scripts/probes/ercot223_shed_phase0.py -> ercot223_shed_phase0.json, "
    "committed read-only from the promoted keeper's own bundles) measured "
    "the keeper's manufactured 2024 h3066 shed to the identity level: the "
    "cost-form conduct floor debases the storage SOC shadow mu one-for-one "
    "(576 -> 184 $/MWh) against the co-opt's floor-free reserve-headroom "
    "value sigma, failing the h3065 pre-peak top-up (+79 -> -225 $/MWh) and "
    "swapping 195.1 MW of storage energy into reserve-counted headroom at "
    "the kill hour (DeltaNonSpin-held == shed == 17.887 MW exactly). The "
    "guard is the structural yield (rule 17): the conduct floor is an OFFER "
    "— withhold in anticipation OF the spike — and at hours the model's own "
    "pass-1 path marks the spike as REALIZED, a cleared offer does not "
    "withhold physical energy. Driver: the measured event-hour fleet "
    "discharge conduct (the real May-8-2024 evening: RT $2,451, the fleet "
    "discharged, no shed). Window: pass-1 settle >= $1,000 within h17-20; "
    "measured breadth 8/776 (2023) and 5/568 (2024) floored hours masked, "
    "0 in 2025 (no floors). Forward story: regenerates from the model's own "
    "pass-1 path exactly as the floor does; zero measured content in the "
    "armed path (rule 13). Judged ONLY by the PRECOMMIT-ercot223 §3 "
    "direction-blind kill-gate table (ercot223_gates.json) with G-SHED "
    "tightened to zero NEW shed hours vs the ORIGINAL 0/1/0; the mechanical "
    "verdict is recorded unrewritten and promotion is a separate owner "
    "decision (the owner's standing structural standard was given in "
    "advance this session)."
)

_ATTEST_CTL = (
    "ercot-223 session (2026-08-19): CONTROL member of the "
    "event-realized-release A/B — the CURRENT keeper recipe "
    "(2026-08-19-ercot221-arm-adaptive) replayed at HEAD (replay_keeper "
    "from the keeper bundle's meta.json, no --set). G-REPRO record, both "
    "legs measured honestly: (a) EDIT-INERTNESS, the strongest form — a "
    "replay at pure origin/main 9c3e45c (no ercot-223 edit) is 7/7 hourly "
    "sidecars sha256-identical to this HEAD replay, so the guard code is "
    "byte-inert flag-off; (b) the committed-bundle byte-identity form "
    "FAILS on pre-existing main drift (41cc6f1..9c3e45c, not this "
    "session's edit): adaptive floors byte-identical all three years, "
    "2024 slack/shed and reserve balances EXACT (shed set {3066, 3067} "
    "reproduced to 1e-6), prices reshuffled within degenerate ties "
    "(2024 dw mean 29.14 -> 29.22, +0.25%). "
    "ercot_adaptive_event_release is at its default (off); "
    "ercot_storage_adaptive_expectation is armed (the keeper's own flag)."
)


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year on the scorer's max-zonal basis."""
    out: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        out[year] = int((df.groupby("hour")["price"].max() > 200.0).sum())
    return out


def _write(
    bundle: Path,
    attested_by: str,
    still_failing: list[int],
    run_label: str,
) -> None:
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = attested_by
    counts = _tail_counts(bundle)
    kept = []
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") != "price_tail":
            kept.append(exc)
            continue
        if year not in still_failing:
            continue  # band met on this bundle — a spent caveat is dropped
        exc["magnitude"] = (
            f"model {counts.get(year, '?')} h vs actual RT "
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on {run_label})"
        )
        kept.append(exc)
    att["exceptions"] = kept
    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; ledger years "
        f"{[e['year'] for e in kept if e.get('criterion') == 'price_tail']}; "
        "free_parameters left to build_dof_ledger.py)"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument(
        "--still-failing",
        type=int,
        nargs="*",
        default=list(YEARS),
        help="years whose C3c still FAILS on the ARM's own scorecard "
        "(default: all three — the keeper's own ledger state)",
    )
    ap.add_argument(
        "--control-still-failing",
        type=int,
        nargs="*",
        default=list(YEARS),
        help="years whose C3c still FAILS on the CONTROL's scorecard",
    )
    args = ap.parse_args()
    _write(
        args.control,
        _ATTEST_CTL,
        args.control_still_failing,
        "the ercot-223 control replay",
    )
    _write(
        args.arm,
        _ATTEST_ARM,
        args.still_failing,
        "the ercot-223 event-realized-release arm",
    )


if __name__ == "__main__":
    main()
