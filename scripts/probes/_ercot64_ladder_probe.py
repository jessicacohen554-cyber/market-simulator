"""ERCOT-64 rule-16 throwaway ladder: the FLOOR-SCOPED LSL markdown, 2023.

The ERCOT-63 adjudication promoted the gas commitment bridge ALONE (the
committed STATE) and refuted the tranche-wide LSL markdown even in
composition (it repriced the tranche's above-floor mid-merit capacity —
spread compression, CT/CC overshoot; diagnosis §5/§7). The enumerated
remaining price-side lever is the FLOOR-SCOPED markdown built this session
(`ercot_offer_surface_lowcurve_floorscoped`): the measured committed-LSL bid
applied ONLY in the bridge's own floored plant-hours. This ladder tests it
against the byte-faithful ercot63-gas-bridge keeper reconstruction:

* ``keeper``      — zero-delta ercot63_gas_bridge reconstruction from its
                    (post-meta-writer-fix, complete) meta.json. Expect
                    C3a +3.1 %, C3b 0.131, C3c 171 h, trough h<$15 228,
                    median daily spread $14.9, storage 0.74 TWh.
* ``fs_markdown`` — + ercot_offer_surface_lowcurve_floorscoped=True (the
                    single delta).

Score with ``_ercot62_lowcurve_analyze.py`` (``--a ercot64_keeper_2023 --b
ercot64_fs_markdown_2023``), ``_ercot63_c3_proxy.py`` and
``_ercot63_anatomy.py`` against the ERCOT-64 TARGET table (2023 RT: trough
h<$10 681 / h<$15 1,493; spread $35.3; viable-arb days 247).

EXPLICITLY-LABELLED DIAGNOSTIC (rules 13/16): 2023-only, NEVER registered,
never a keeper config; bundles are throwaways.

Usage::

    python scripts/probes/_ercot64_ladder_probe.py RUNG [--years 2023]
    # RUNG in {keeper, fs_markdown}
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
# The promoted ERCOT keeper (2026-07-12-ercot63-gas-bridge) bundle — its
# meta.json post-dates the ERCOT-63 meta-writer fix, so the reconstruction
# is complete (ercot_storage_as_deployment + ercot_gas_commitment_bridge
# both recorded; no manual compensation needed).
KEEPER = ROOT / "ercot63_gas_bridge"

RUNGS = {
    "keeper": {},
    "fs_markdown": {"ercot_offer_surface_lowcurve_floorscoped": True},
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rung", choices=sorted(RUNGS))
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    kwargs.update(RUNGS[args.rung])
    kwargs["note"] = (
        f"ercot64 rule-16 throwaway (NEVER register): '{args.rung}' rung of "
        "the floor-scoped-LSL-markdown ladder — ercot63-gas-bridge keeper "
        f"reconstructed from meta.json + deltas {RUNGS[args.rung]!r}. Tests "
        "the measured committed-LSL bid applied ONLY in the gas commitment "
        "bridge's own floored plant-hours (the ERCOT-63 diagnosis §7 "
        "enumerated price-side lever) against the trough-depth/arbitrage "
        "TARGET table."
    )

    out = ROOT / f"ercot64_{args.rung}_2023"
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
