"""ERCOT ercot55 A/B runner: C2 counting fix baseline + offer-surface arm.

Reconstructs the ercot53_hsl_930fill KEEPER's exact ``solve_and_persist`` call
from its committed ``meta.json`` (the reliable path established by
``scripts/probes/_ercot49_offer_retune.py`` / ``_ercot50_offer_surface.py`` —
the curated ``calibration_flags`` subset omits ~30 non-default flags) and
layers nothing on the main arm: its whole delta vs ercot53 is ambient in the
code — the measured EIA-930 long-format fill of the ERCO extract's 48-hour
2025-12-04/05 hole (demand + benchmark series; ``eia_loader.
_fill_hourly_frame_from_long``) and the ``NG: OTH`` series threaded into the
bundle for the C2 gas fold-in (``load_ercot_other_gen``). 2023/2024 inputs are
byte-identical, so those years must reproduce ercot53 exactly.

The ``--surface`` arm additionally enables ``ercot_offer_surface_conditional``
(the measured G-22 §8 condition-responsive offer surface, unchanged
parameters) — the full-span 2023-2025 A/B on the current keeper config under
rubric v2.4 + the ORDC cap-dual fix that the ercot50 rejection record notes
was never produced (ercot50 was scored pre-v2.4, pre-cap-dual; the only
re-test since was a 2023-only throwaway).

Usage::

    python scripts/probes/_ercot55_ab.py OUT_NAME \
        [--years 2023 2024 2025] [--surface] [--ablation --ablation-of NAME] \
        [--set KEY=BOOL]
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_calibration_full as rcf  # noqa: E402
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot53_hsl_930fill"


def _with_other_series(frame_fn):
    """Wrap ``_eia930_frame``: ensure the ERCOT frame carries the NG: OTH series.

    The in-file threading of ``load_ercot_other_gen`` into ``_eia930_frame``
    (a 9-line change) could not be pushed to this branch — the ~240 KB script
    exceeds the Data-API relay's single-call ceiling and the session hit its
    spend limit for the subagent push path (2026-07-10). This guarded wrapper
    applies the identical change at the probe seam so a CI solve produces the
    same bundle as the authoring session's local solve; it is a NO-OP once the
    real threading is present (the ``"other" in series`` guard). Follow-up:
    land the threading in scripts/run_calibration_full.py and delete this.
    """

    def wrapped(year, iso, iso_config):
        frame = frame_fn(year, iso, iso_config)
        if frame is None or iso != "ERCOT" or "other" in set(frame["series"]):
            return frame
        import numpy as np
        import pandas as pd

        from market_sim.data.eia_loader import load_ercot_other_gen

        other = load_ercot_other_gen(year)
        if other is None:
            return frame
        a = np.asarray(other, dtype=float)
        return pd.concat(
            [
                frame,
                pd.DataFrame(
                    {
                        "year": np.int16(year),
                        "series": "other",
                        "hour": np.arange(a.shape[0], dtype=np.int32),
                        "mw": a,
                    }
                ),
            ],
            ignore_index=True,
        )

    return wrapped


rcf._eia930_frame = _with_other_series(rcf._eia930_frame)

# meta.json keys that are NOT real solve_and_persist kwargs (same derivation
# as _ercot48/_ercot49/_ercot50: RENAMED map to differently-named kwargs;
# DERIVED_ONLY are top-level echoes of values that really live inside
# ``coal_prb_sigmoid_overrides``; HANDLED are positional/explicit args;
# BOOKKEEPING is provenance).
RENAMED = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
DERIVED_ONLY = {
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
}
HANDLED = {"years", "iso", "hours", "commitment", "gas_prices", "passes"}
BOOKKEEPING = {"timestamp", "git_sha", "highspy_version", "shared_inputs"}


def build_kwargs(meta: dict, sig_params: set) -> dict:
    """Map the keeper's meta.json onto solve_and_persist kwargs."""
    kwargs = {}
    for k, v in meta.items():
        if k in HANDLED or k in DERIVED_ONLY or k in BOOKKEEPING:
            continue
        if k in RENAMED:
            kwargs[RENAMED[k]] = v
        elif k in sig_params:
            kwargs[k] = v
        else:
            raise ValueError(f"meta.json key {k!r} has no solve_and_persist home")
    return kwargs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_name", help="bundle name under results/calibration/")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument(
        "--surface",
        action="store_true",
        default=False,
        help="enable ercot_offer_surface_conditional (A/B arm; default OFF)",
    )
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--ablation-of", default=None, help="bundle name of the main run")
    ap.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=BOOL",
        help="override one solve_and_persist boolean kwarg (diagnostic probes only)",
    )
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    if args.surface:
        kwargs["ercot_offer_surface_conditional"] = True
    for ov in args.overrides:
        key, _, val = ov.partition("=")
        if key not in sig:
            raise ValueError(f"--set {key!r} is not a solve_and_persist kwarg")
        kwargs[key] = val.strip().lower() in ("1", "true", "yes", "on")
    kwargs["zero_forcing_ablation"] = args.ablation
    kwargs["ablation_of"] = args.ablation_of if args.ablation else None
    kwargs["note"] = (
        "ercot55: ercot53_hsl_930fill config reconstructed from meta.json, "
        "zero config deltas on the main arm — the delta is the measured "
        "EIA-930 long-format fill of the ERCO extract's 48-h 2025-12-04/05 "
        "hole (demand + benchmark; 2023/2024 byte-identical) and the NG: OTH "
        "series threaded for the C2 gas fold-in"
        + (
            "; SURFACE ARM: + ercot_offer_surface_conditional (measured G-22 "
            "§8 surface, unchanged parameters) — the missing full-span A/B on "
            "the keeper config under v2.4 + ORDC cap-dual"
            if args.surface
            else ""
        )
    )

    out = ROOT / args.out_name
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
    print(f"DONE surface={args.surface} ablation={args.ablation} -> {out}")


if __name__ == "__main__":
    main()
