"""Byte-faithful re-solve of a committed calibration keeper from its bundle.

A keeper's ``meta.json`` is the authoritative snapshot of the keyword arguments
``run_calibration_full.solve_and_persist`` was called with (it is written from
those kwargs at solve time). This driver reads that snapshot and replays the
solve into the bundle directory, regenerating every output the registration
pipeline needs — crucially ``btm.parquet`` (the behind-the-meter CHP host steam
held out of the LP), which the parallel CAISO/PJM re-gates predate. The BTM
write is solve-invariant (``btm_twh = EIA-923 class total − grid dispatch`` and a
held-out CHP plant's grid dispatch is ~0), so the re-solve reproduces the
keeper's dispatch and only *adds* the BTM basis the original bundle lacked.

The original ``meta.timestamp`` date is preserved so the dashboard run id
(``<date>-<shorthand>``) is unchanged — the re-solve fixes the keeper in place,
it does not mint a new run.

Usage:
    python scripts/replay_keeper.py results/calibration/<bundle> [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import run_calibration_full as rcf  # noqa: E402

# meta.json key -> solve_and_persist kwarg, where the names differ.
_REMAP = {
    "commitment_screen_coal": "screen_coal",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# meta.json keys that are not solve kwargs (provenance / derived / recorded only).
_IGNORE = {
    "timestamp",
    "gas_prices",
    "passes",
    "td_loss_factor",
    "shared_inputs",
    "git_sha",
    "highspy_version",
    "iso",
    "years",
    "hours",
}


def build_kwargs(meta: dict) -> dict:
    """Map a bundle's meta.json onto solve_and_persist's keyword arguments."""
    params = set(inspect.signature(rcf.solve_and_persist).parameters)
    kwargs: dict = {}
    for k, v in meta.items():
        if k in _IGNORE:
            continue
        key = _REMAP.get(k, k)
        if key == "coal_plant_monthly_pricing":
            # Not a direct kwarg: the False case rides the prb_overrides channel
            # (default True is the per-ISO base, so only an explicit off matters).
            if v is False:
                kwargs.setdefault("prb_overrides", {})
                kwargs["prb_overrides"]["coal_plant_monthly_pricing"] = False
            continue
        if key in params:
            kwargs[key] = v
    return kwargs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", help="bundle dir, e.g. results/calibration/<name>")
    ap.add_argument(
        "--out-dir",
        default=None,
        help="solve into this dir instead of the bundle (default: in place)",
    )
    ap.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=JSON",
        help="ScenarioConfig override applied on top of the keeper config via "
        "the generic prb_overrides channel (repeatable), e.g. "
        "--set capacity_deliverability_limits=true. The value is JSON. Turns "
        "the byte-faithful replay into a single-delta A/B probe of the keeper "
        "— pair with --out-dir and --note so the probe never overwrites the "
        "keeper bundle.",
    )
    ap.add_argument(
        "--note",
        default=None,
        help="free-text run note recorded in the new bundle's run_config.json "
        "(defaults to the BTM-basis replay note)",
    )
    ap.add_argument(
        "--offer-curve-json",
        default=None,
        metavar="JSON_OR_PATH",
        help="replace the keeper's offer_curve_overrides with this "
        "class->band mapping (inline JSON or a path, same shape/validation "
        "as run_calibration_full --offer-curve-json). Single-delta offer-"
        "surface probe of the keeper — pair with --out-dir and --note.",
    )
    args = ap.parse_args()

    bundle = Path(args.bundle)
    meta = json.loads((bundle / "meta.json").read_text())
    orig_ts = meta.get("timestamp", "")

    kwargs = build_kwargs(meta)
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir) if args.out_dir else bundle
    for spec in args.overrides:
        key, _, raw = spec.partition("=")
        if not key or not raw:
            raise SystemExit(f"--set expects KEY=JSON, got {spec!r}")
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"][key] = json.loads(raw)
    if args.offer_curve_json is not None:
        kwargs["offer_curve_overrides"] = rcf._parse_offer_curve_json(
            args.offer_curve_json, flag="--offer-curve-json"
        )
    if args.note is not None:
        kwargs["note"] = args.note
    kwargs.setdefault(
        "note",
        "BTM-basis re-solve: byte-faithful replay of the committed keeper "
        "config from meta.json, adding btm.parquet (behind-the-meter CHP held "
        "out of the LP) so the benchmark scores on the grid-delivered basis.",
    )

    print(f"replaying {bundle} ({meta['iso']} {meta['years']}) ...")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")

    # Preserve the original run id: restore the meta.json timestamp date so the
    # dashboard id (<date>-<shorthand>) is unchanged. Only for byte-faithful
    # replays — an overridden run (--set / --offer-curve-json) is a NEW probe,
    # not the keeper fixed in place, and must mint its own dated id.
    if orig_ts and not args.overrides and args.offer_curve_json is None:
        new_meta = json.loads((run_dir / "meta.json").read_text())
        new_ts = new_meta.get("timestamp", "")
        new_meta["timestamp"] = orig_ts[:10] + new_ts[10:] if new_ts else orig_ts
        (run_dir / "meta.json").write_text(json.dumps(new_meta, indent=2) + "\n")
        print(f"restored meta timestamp date -> {orig_ts[:10]}")


if __name__ == "__main__":
    main()
