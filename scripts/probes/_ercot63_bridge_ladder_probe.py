"""ERCOT-63 rule-16 throwaway ladder: the REAL gas commitment bridge, 2023.

The ERCOT-62b monkeypatch probe (`_ercot62b_bridge_probe.py`) showed the
committed-state bridge + measured LSL markdown is the first composition that
moves the storage/spread circle the RIGHT way. This ladder tests the REAL
mechanism built this session (`ercot_gas_commitment_bridge` — own gate,
CC-only scope, measured min-load p50 0.574, DA-operating-day horizon on the
economic leg, no startup-aware screen) against the byte-faithful keeper
reconstruction, one rung per composition:

* ``keeper``     — zero-delta ercot59-storage-deploy reconstruction
                   (expect C3a +3.9 %, C3b 0.133, C3c 171 h);
* ``bridge``     — + ercot_gas_commitment_bridge alone (state, no markdown);
* ``bridge_md``  — + ercot_offer_surface_lowcurve (state + price — the 62b
                   composition, expect >= its row: trough h<$15 292,
                   spread $13.7, storage 0.59 TWh);
* ``bridge_md_nohorizon`` — the 62b-exact construction (economic bridges at
                   any gap length) to isolate the DA-horizon cap's effect.

Score each with ``scripts/probes/_ercot62_lowcurve_analyze.py``
(``--a ercot63_keeper_2023 --b <rung>``).

EXPLICITLY-LABELLED DIAGNOSTIC (rules 13/16): 2023-only, NEVER registered,
never a keeper config; bundles are throwaways.

Usage::

    python scripts/probes/_ercot63_bridge_ladder_probe.py RUNG [--years 2023]
    # RUNG in {keeper, bridge, bridge_md, bridge_md_nohorizon}
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ercot61_stgas_drag_probe import build_kwargs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
# The promoted ERCOT keeper (2026-07-12-ercot59-storage-deploy) bundle.
KEEPER = ROOT / "ercot_storage_deploy"

RUNGS = {
    "keeper": {},
    "bridge": {"ercot_gas_commitment_bridge": True},
    "bridge_md": {
        "ercot_gas_commitment_bridge": True,
        "ercot_offer_surface_lowcurve": True,
    },
    "bridge_md_nohorizon": {
        "ercot_gas_commitment_bridge": True,
        "ercot_gas_bridge_da_horizon": False,
        "ercot_offer_surface_lowcurve": True,
    },
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rung", choices=sorted(RUNGS))
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    # The keeper's meta.json predates the ERCOT-63 meta-writer fix and is
    # missing its own defining delta (recorded in the bundle's
    # run_config.json: ercot_storage_as_deployment=true, from_year 2023) —
    # set it explicitly so the reconstruction is ercot59, not ercot56.
    kwargs.setdefault("ercot_storage_as_deployment", True)
    kwargs.setdefault("ercot_storage_as_deployment_from_year", 2023)
    kwargs.update(RUNGS[args.rung])
    kwargs["note"] = (
        f"ercot63 rule-16 throwaway (NEVER register): '{args.rung}' rung of "
        "the real-gas-commitment-bridge ladder — ercot59-storage-deploy keeper "
        "base reconstructed from meta.json "
        f"+ deltas {RUNGS[args.rung]!r}. Scores the promoted "
        "ercot_gas_commitment_bridge (CC-only, measured LSL/HSL p50 0.574, "
        "DA-horizon economic leg, no startup-aware screen) against the "
        "ERCOT-62b monkeypatch row (diagnosis §6)."
    )

    out = ROOT / f"ercot63_{args.rung}_2023"
    out.mkdir(parents=True, exist_ok=True)
    solve_and_persist(
        args.years,
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        run_dir=out,
        **kwargs,
    )
    print(f"DONE -> {out}")


if __name__ == "__main__":
    main()
