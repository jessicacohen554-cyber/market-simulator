"""ERCOT-65 rule-16 throwaway ladder: the negative-price epoch pair, 2023.

The ERCOT-64 charter named one admissible pair for the still-open
trough-depth gap (RT 2023: 1,493 lw-hours < $15, 137 of them NEGATIVE):
(i) PTC-driven negative renewable offers, (ii) the West-corridor
curtailment topology co-lane. The ERCOT-65 touchpoint audit found the
diagnosis §8 premise wrong in one respect: the keeper's wind offer is NOT
$0 — every wind MW already bids the FLAT -ira_ptc_wind = -$26
(policy.ira.compute_dispatch_credits), vintage-unscoped, so 27-40 % of
2023-25 ERCOT wind capacity whose §45 window expired (which in reality
bids ~$0) is bid at full -PTC. The admissible build is therefore the
VINTAGE SCOPING (`wind_ptc_vintage_offers`), and the ladder measures both
legs against the byte-faithful ercot63-gas-bridge keeper reconstruction:

* ``keeper``      — zero-delta ercot63_gas_bridge reconstruction from its
                    meta.json. Expect C3a +3.1 %, C3b 0.131, C3c 171 h,
                    trough h<$15 228, median daily spread $14.9, storage
                    0.74 TWh.
* ``vintage``     — + wind_ptc_vintage_offers=True (the ERCOT-65 build:
                    per-zone-month measured EIA-860 blend; West 2023
                    bids ~-$14.8 instead of -$26).
* ``wtx``         — + ercot_wtx_curtailment_driver=True (the built-but-
                    unpromoted ercot42 WP-B ceiling, composed on the
                    keeper per charter trap #3 — measures whether a
                    BOUND-forced curtailment can form negative epochs at
                    all, or is price-inert by the pinned-variable anatomy).
* ``vintage_wtx`` — both.

Score with ``_ercot62_lowcurve_analyze.py`` (now incl. the h<$0 band),
``_ercot63_c3_proxy.py``, ``_ercot63_anatomy.py`` and
``_ercot65_epoch_anatomy.py`` against the ERCOT-65 TARGET table (2023 RT:
trough h<$10 681 / h<$15 1,493 (137 negative); spread $35.3; viable-arb
days 247).

EXPLICITLY-LABELLED DIAGNOSTIC (rules 13/16): 2023-only, NEVER registered,
never a keeper config; bundles are throwaways.

Usage::

    python scripts/probes/_ercot65_ladder_probe.py RUNG [--years 2023]
    # RUNG in {keeper, vintage, wtx, vintage_wtx}
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
# is complete.
KEEPER = ROOT / "ercot63_gas_bridge"

RUNGS = {
    "keeper": {},
    "vintage": {"wind_ptc_vintage_offers": True},
    "wtx": {"ercot_wtx_curtailment_driver": True},
    "vintage_wtx": {
        "wind_ptc_vintage_offers": True,
        "ercot_wtx_curtailment_driver": True,
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
    kwargs.update(RUNGS[args.rung])
    kwargs["note"] = (
        f"ercot65 rule-16 throwaway (NEVER register): '{args.rung}' rung of "
        "the negative-price-epoch ladder — ercot63-gas-bridge keeper "
        f"reconstructed from meta.json + deltas {RUNGS[args.rung]!r}. Tests "
        "the PTC vintage scoping (wind_ptc_vintage_offers) and the WP-B "
        "curtailment-ceiling composition against the trough-depth/negative-"
        "band TARGET table."
    )

    out = ROOT / f"ercot65_{args.rung}_2023"
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
