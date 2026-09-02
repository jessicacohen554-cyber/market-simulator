"""xiso-7 instrument: the ``prb_follower`` DOF under-count census.

Measures, across all six designated keepers, whether
:mod:`scripts.build_dof_ledger` under-counts the free parameters of the tiered
PRB coal passthrough (``FINDING-caiso236-dof-residual-ledger-audit-2026-09-02.md``
§10.3).

The defect, restated from source: ``prb_follower`` has NO sigmoid toggle of its
own. Its gate is the conjunction ``coal_prb_passthrough_sigmoid AND
coal_prb_passthrough_tiered`` (``data/fleet/assembly.py``), and when it fires
``prb_follower_passthrough_series`` resolves a SECOND four-parameter set
(``COAL_SIGMOID_DEFAULTS[(ISO, "prb_follower")]`` overlaid by the explicit
``coal_prb_follower_*`` fields). The ledger's ``n_scalars = 4 * len(sigmoids)``
enumerates only the five ``coal_*_passthrough_sigmoid`` toggles, so those four
scalars are attested nowhere.

Read-only: opens committed bundles and the keeper store, solves nothing, writes
nothing but its own JSON transcript. Pre-registration:
``results/calibration/PRECOMMIT-xiso7-prb-follower-dof-undercount-2026-09-02.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import build_ledger  # noqa: E402
from scripts.lib import keeper_store  # noqa: E402

#: The four scalars a resolved sigmoid parameter set consumes.
_PARAMS = ("floor", "ceil", "gas_mid", "gas_slope")


def follower_resolves(sc: dict, iso: str) -> tuple[bool, dict]:
    """Return whether ``(iso, "prb_follower")`` resolves, and the resolved set.

    Mirrors :func:`market_sim.data.fuel.trajectories.coal_sigmoid_params` for the
    ``prb_follower`` supply exactly: registry entry overlaid by any explicitly-set
    ``coal_prb_follower_<param>`` field, complete on all four or nothing.
    """
    from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS

    params = dict(COAL_SIGMOID_DEFAULTS.get((iso.upper(), "prb_follower"), {}))
    for name in _PARAMS:
        value = sc.get(f"coal_prb_follower_{name}")
        if value is not None:
            params[name] = value
    return all(name in params for name in _PARAMS), params


def sigmoid_row(ledger: dict) -> dict | None:
    """Return the ``COAL_SIGMOID_DEFAULTS[*]`` entry of a ledger, if any."""
    for entry in ledger.get("entries", []):
        if str(entry.get("name", "")).startswith("COAL_SIGMOID_DEFAULTS["):
            return entry
    return None


def audit_keeper(run_id: str) -> dict:
    """Census one keeper: gate state, committed ledger, generated ledger."""
    side = json.loads(
        (REPO / "frontend/data/backcast/registry" / f"{run_id}.json").read_text()
    )
    bundle, iso = REPO / side["bundle"], side["iso"]
    sc = json.loads((bundle / "run_config.json").read_text()).get("scenario_config", {})

    armed_sigmoid = bool(sc.get("coal_prb_passthrough_sigmoid"))
    armed_tiered = bool(sc.get("coal_prb_passthrough_tiered"))
    resolves, resolved = follower_resolves(sc, iso)
    # The full E-1/E-2 gate: the follower series is consumed, and it consumes a
    # parameter set distinct from the baseload prb curve, only when all three hold.
    under_counted = armed_sigmoid and armed_tiered and resolves

    generated = build_ledger(bundle, iso)
    att_path = bundle / "calibration_attestation.json"
    committed = (
        json.loads(att_path.read_text()).get("free_parameters")
        if att_path.exists()
        else None
    )
    gen_row, com_row = sigmoid_row(generated), sigmoid_row(committed or {})

    return {
        "run_id": run_id,
        "iso": iso,
        "bundle": side["bundle"],
        "gate": {
            "coal_prb_passthrough_sigmoid": armed_sigmoid,
            "coal_prb_passthrough_tiered": armed_tiered,
            "prb_follower_resolves": resolves,
            "resolved_params": resolved if resolves else None,
            "UNDER_COUNTED": under_counted,
        },
        # P-5: the tier-split threshold is engaged by the same gate. Is it counted?
        "coal_prb_follower_mustrun_max": sc.get("coal_prb_follower_mustrun_max"),
        "coal_perplant_offer_curves": bool(sc.get("coal_perplant_offer_curves")),
        "committed_ledger": None
        if committed is None
        else {
            "n_entries": committed.get("n_entries"),
            "n_residual": committed.get("n_residual"),
            "sigmoid_row": None
            if com_row is None
            else {
                "name": com_row.get("name"),
                "identification": com_row.get("identification"),
                "n_scalars": com_row.get("n_scalars"),
            },
        },
        "generated_ledger": {
            "n_entries": generated["n_entries"],
            "n_residual": generated["n_residual"],
            "sigmoid_row": None
            if gen_row is None
            else {
                "name": gen_row.get("name"),
                "identification": gen_row.get("identification"),
                "n_scalars": gen_row.get("n_scalars"),
            },
        },
        # Is the committed attestation already stale against the generator, for
        # reasons independent of this session? (P-6: decides surgical vs regenerate.)
        "committed_matches_generated": committed == generated,
        "expected_delta_scalars": 4 if under_counted else 0,
    }


def main() -> None:
    """Run the census over every designated keeper and print/emit the transcript."""
    rows = [audit_keeper(run_id) for run_id in keeper_store.keeper_list(REPO)]
    affected = [r["iso"] for r in rows if r["gate"]["UNDER_COUNTED"]]

    print(f"{'ISO':6s} {'sig':5s} {'tier':5s} {'res':5s} {'UNDER':6s} "
          f"{'perplant':9s} {'com(e/r/sc)':14s} {'gen(e/r/sc)':14s} stale?")
    for r in rows:
        g, c, n = r["gate"], r["committed_ledger"], r["generated_ledger"]
        cs = "-" if c is None else (
            f"{c['n_entries']}/{c['n_residual']}/"
            f"{(c['sigmoid_row'] or {}).get('n_scalars', '-')}"
        )
        ns = (f"{n['n_entries']}/{n['n_residual']}/"
              f"{(n['sigmoid_row'] or {}).get('n_scalars', '-')}")
        print(
            f"{r['iso']:6s} {str(g['coal_prb_passthrough_sigmoid']):5s} "
            f"{str(g['coal_prb_passthrough_tiered']):5s} "
            f"{str(g['prb_follower_resolves']):5s} "
            f"{str(g['UNDER_COUNTED']):6s} "
            f"{str(r['coal_perplant_offer_curves']):9s} {cs:14s} {ns:14s} "
            f"{'no' if r['committed_matches_generated'] else 'STALE'}"
        )
    print(f"\nAFFECTED (under-counted): {affected or 'NONE'}")
    for r in rows:
        if r["gate"]["UNDER_COUNTED"]:
            print(
                f"  {r['iso']}: mustrun_max="
                f"{r['coal_prb_follower_mustrun_max']}  "
                f"follower={r['gate']['resolved_params']}"
            )

    out = REPO / "results/calibration/_xiso7_prb_follower_dof.json"
    out.write_text(json.dumps({"keepers": rows, "affected": affected}, indent=2) + "\n")
    print(f"\nwrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
