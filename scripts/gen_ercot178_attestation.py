"""Generate the ercot-178 pair attestations from the ercot-176 keeper base.

``results/calibration/ercot178_control_A`` is the run176 keeper recipe
replayed at the ercot-178 HEAD with zero deltas, so its attestation is the
committed ercot176_control_A attestation with the governance ``attested_by``
re-attested for this run and the three ``price_tail`` model-class exception
magnitudes re-confirmed at this run's own tail counts.

``results/calibration/ercot178_grain_B`` is the control plus ONE mechanism
delta — ``ercot_offer_surface_continuous=true`` (matrix §5.1 item 21, the
pre-registered continuous conditioning grain,
``docs/PRECOMMIT-ercot178-continuous-netload-grain-2026-08-08.md``) — so its
attestation additionally carries one ADDED measured DOF-ledger entry
(``n_scalars 0``, ``free_parameters_added: 0``: the node tables are the
corpus's own hours carrying the family's unchanged statistics; no edge, no
grid, no clamp was chosen — precommit §3), with the tail-count magnitudes read
from the ARM's own sidecars.

Reads committed artifacts only; no solve. Run AFTER both bundles exist:
    python scripts/gen_ercot178_attestation.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "results/calibration/ercot176_control_A/calibration_attestation.json"
BUNDLES = {
    "control": REPO / "results/calibration/ercot178_control_A",
    "arm": REPO / "results/calibration/ercot178_grain_B",
}
TAIL_THRESH = 200.0  # $/MWh, the rubric C3c tail line
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}  # committed actual_tail.json counts

NEW_ENTRY = {
    "name": "ercot_offer_surface_continuous (continuous net-load-percentile "
    "conditioning grain of the measured offer-surface family)",
    "where": "run_config.scenario_config.ercot_offer_surface_continuous",
    "identification": "measured",
    "n_scalars": 0,
    "source": (
        "PRECOMMIT-ercot178-continuous-netload-grain-2026-08-08.md §2-§3: the "
        "four armed surfaces' IDENTICAL statistics (MW-weighted "
        "LADDER_QUANTILES ladders, per-hour cleared_share / pool_frac "
        "boundaries, floor/HCAP clamps) re-keyed from net-load-percentile "
        "bins to the corpus's own hour nodes; interpolation nodes are the "
        "corpus hours themselves, so there is NO edge, NO grid and NO scalar "
        "to fit (rule 20). Derives: --continuous modes of "
        "derive_dam_offer_hrmults / derive_ercot_dam_cleared_share / "
        "derive_ercot_sced_offer_wall / derive_ercot_faststart_pool, from "
        "the same frozen sources as the stepped vintages (rule 23: new "
        "vintage for a new pre-registered gate, the pjm_offer_surface_"
        "within_season precedent; stepped artifacts byte-untouched, "
        "seam-proof SP-6). Seam proof: results/calibration/"
        "ercot178_contpct_seamproof.json — SP-3 legacy-encoding "
        "byte-identity proves the machinery is grain, not level."
    ),
    "free_parameters_added": 0,
}

ATTESTED_BY = {
    "control": (
        "ercot-178 {today} — the run176 keeper recipe REPLAYED AT HEAD with "
        "ZERO deltas (scripts/replay_keeper.py, no --set), solved in-session "
        "across the full 2023-2025 span as the pre-registered A/B control "
        "(docs/PRECOMMIT-ercot178-continuous-netload-grain-2026-08-08.md §8). "
        "The DOF ledger and the exceptions ledger are INHERITED UNCHANGED "
        "from the ercot176_control_A attestation because the recipe is "
        "unchanged — no parameter was added, removed, re-identified or "
        "re-tuned on this run; n_entries stays 13 with n_residual 6. The "
        "session's mechanism ercot_offer_surface_continuous is DEFAULT-OFF "
        "and NOT armed here. Rule 22: 2023-2025 only; ERCOT holds no "
        "complete and no final marker and no out-of-training year was "
        "solved, scored, read or registered."
    ),
    "arm": (
        "ercot-178 {today} — the control plus ONE mechanism delta: "
        "ercot_offer_surface_continuous=true (scripts/replay_keeper.py "
        "--set), the pre-registered CONTINUOUS net-load-percentile "
        "conditioning grain of the four armed measured offer surfaces "
        "(docs/PRECOMMIT-ercot178-continuous-netload-grain-2026-08-08.md; "
        "matrix §5.1 item 21). The grain change re-keys the family's "
        "IDENTICAL statistics from stepped bins to the corpus's own hour "
        "nodes: zero fitted scalars, no edge to fit, forward story "
        "inherited unchanged (rule 13). One measured DOF-ledger entry is "
        "ADDED (n_scalars 0, free_parameters_added 0); n_residual is "
        "unchanged at 6. Seam proof committed pre-solve "
        "(results/calibration/ercot178_contpct_seamproof.json, "
        "ALL_ASSERTIONS_PASS true; SP-3 legacy-encoding byte-identity). "
        "Rule 22: 2023-2025 only; no out-of-training year was solved, "
        "scored, read or registered."
    ),
}


def _tail_counts(run_id: str) -> dict[int, int]:
    """Model RT tail-hour counts from the REGISTERED payload (the judged
    quantity: ``years[y].ordc.hoursGt200.model``, exactly what C3c scores)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "cv", str(REPO / "scripts/calibration_verdict.py")
    )
    cv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cv)
    payload = cv._decode_run_js(
        (REPO / "frontend/data/backcast/runs" / f"{run_id}.js").read_text()
    )
    out: dict[int, int] = {}
    for y in (2023, 2024, 2025):
        out[y] = int(payload["years"][str(y)]["ordc"]["hoursGt200"]["model"])
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control-run-id", required=True)
    ap.add_argument("--arm-run-id", required=True)
    args = ap.parse_args()
    run_ids = {"control": args.control_run_id, "arm": args.arm_run_id}

    base = json.loads(BASE.read_text())
    today = date.today().isoformat()
    for kind, bundle in BUNDLES.items():
        att = json.loads(json.dumps(base))  # deep copy
        counts = _tail_counts(run_ids[kind])
        for exc in att.get("exceptions", []):
            y = exc.get("year")
            if exc.get("criterion") == "price_tail" and y in ACTUAL_TAIL:
                exc["magnitude"] = (
                    f"model {counts[y]} h vs actual RT {ACTUAL_TAIL[y]} h "
                    f"> $200/MWh (re-confirmed at ercot-178 {kind})"
                )
        if kind == "arm":
            fp = att["free_parameters"]
            fp["entries"] = fp["entries"] + [NEW_ENTRY]
            fp["n_entries"] = len(fp["entries"])
            # n_residual unchanged: the new entry is measured, not residual.
        att["governance"]["attested_by"] = ATTESTED_BY[kind].format(today=today)
        dest = bundle / "calibration_attestation.json"
        dest.write_text(json.dumps(att, indent=1))
        print(f"wrote {dest} (tail counts {counts})")


if __name__ == "__main__":
    main()
