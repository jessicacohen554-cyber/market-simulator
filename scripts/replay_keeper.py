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
import dataclasses
import inspect
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# Reproducibility pin: a byte-faithful keeper replay must be basis-independent,
# so force the cross-year LP warm-start OFF regardless of the ambient
# environment. Cross-year warm-start is basis-neutral on the calibration path
# (objective/prices/total-gen bit-identical) but reshuffles marginal-tie
# dispatch by ~0.003%, which would make a replay's per-plant parquet differ from
# the cold-solved committed bundle and break the D-13 bench-repro byte-identity
# gate. Set BEFORE importing run_calibration_full so the solve core
# (pipeline.solve) reads the pinned value. Mirrors capture_keeper_goldens.py.
# solve_and_persist is called directly here (not via the CLI main()), so it
# never sees the calibration CLI's default-ON gate.
os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"

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
    # --reuse-solved labeling block: which years a mixed bundle byte-copied
    # from which source bundle. Pure provenance — the recipe kwargs above are
    # complete regardless, and a replay of a mixed bundle re-solves every
    # year fresh (which is exactly what "reused years are not fresh
    # evidence" demands of a re-gate).
    "reuse",
}
# Recorded-only env-gated probe values: resolved inside backcast_config from
# env vars (ERCOT_ZONAL_GAS / ERCOT_WEST_NETLOAD_GAS /
# ERCOT_WEST_GAS_DELIVERED_FLOOR — no solve_and_persist kwarg exists, rule-24
# exception; see the meta-writer comment in run_calibration_full.py). The
# meta.json value is provenance. A kwargs replay can reproduce only the INERT
# state; a bundle that ARMED one must re-solve with the same env var, so
# build_kwargs hard-errors rather than silently dropping the mechanism.
_ENV_GATED_INERT: dict = {
    "ercot_zonal_gas_basis": False,
    "ercot_west_netload_gas_shape": False,
    "ercot_west_gas_delivered_floor": None,
}


def build_kwargs(meta: dict) -> dict:
    """Map a bundle's meta.json onto solve_and_persist's keyword arguments.

    STRICT: every meta key must map to a solve kwarg or be a curated
    provenance/recorded-only key — an unmapped key is a hard error, never a
    silent drop. This is the closure of the miso-50..53 regression class
    (recipes reconstructed from a lossy channel silently dropped the whole
    keeper structure; see the CLAUDE.md critical lesson and
    results/calibration/FINDING-miso-august-scarcity-2026-07.md §1): the
    meta.json replay is the ONLY sanctioned recipe reconstruction, and it
    refuses to lose structure quietly.
    """
    params = set(inspect.signature(rcf.solve_and_persist).parameters)
    kwargs: dict = {}
    unmapped: list[str] = []
    for k, v in meta.items():
        if k in _IGNORE:
            continue
        if k in _ENV_GATED_INERT:
            if v != _ENV_GATED_INERT[k]:
                raise SystemExit(
                    f"bundle armed the env-gated probe {k}={v!r}, which has no "
                    "solve kwarg — a kwargs replay cannot reproduce it; re-run "
                    "with the original env var set instead"
                )
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
        else:
            unmapped.append(k)
    if unmapped:
        raise SystemExit(
            "meta.json keys not bound to solve_and_persist kwargs: "
            f"{sorted(unmapped)} — extend replay_keeper._REMAP/_IGNORE "
            "deliberately; silent drops are the miso-50..53 regression class"
        )
    # Pre-driver bundle backstop: the WP-B curtailment driver became the ERCOT
    # backcast default-ON (owner GO 2026-07-07), and its solve kwarg is
    # tri-state (None = per-ISO backcast_config default). A bundle solved
    # before the driver existed carries no key in meta.json — replaying it
    # byte-faithfully means the driver OFF, not today's default, so pin the
    # kwarg to False when meta is silent. Post-driver bundles record their
    # resolved True/False (or an explicit null) and are unaffected.
    if (
        meta.get("iso", "").upper() == "ERCOT"
        and "ercot_wtx_curtailment_driver" not in meta
    ):
        kwargs["ercot_wtx_curtailment_driver"] = False
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
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="solve only these years instead of the bundle's full span — the "
        "per-year invocation chain of CLAUDE.md rule 12 (a single year's "
        "per-plant LP already needs most of a small box's RAM, so a fresh "
        "process per year avoids heap-fragmentation OOM). Pair later "
        "invocations with --reuse-solved so already-solved years byte-copy "
        "forward. A partial-years replay is a NEW run, never the keeper "
        "fixed in place (its meta timestamp is not restored).",
    )
    ap.add_argument(
        "--reuse-solved",
        default=None,
        metavar="BUNDLE",
        help="byte-copy already-solved years from this prior bundle when its "
        "recipe matches exactly (run_calibration_full.plan_reuse_solved — "
        "same gate as the calibration CLI's --reuse-solved). Reused years "
        "are copies, not fresh evidence.",
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
    kwargs["years"] = [int(y) for y in (args.years or meta["years"])]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir) if args.out_dir else bundle
    if args.reuse_solved is not None:
        kwargs["reuse_solved"] = Path(args.reuse_solved)
    # --set routes through BOTH channels: the explicit solve_and_persist kwarg
    # (when one exists) AND the generic prb_overrides ScenarioConfig channel
    # (when the key is a config field). run_year's override application order
    # is mixed — prb_overrides applies after most explicit kwargs but BEFORE a
    # trailing block of them (e.g. ercot_ecrs_conservative_deployment at
    # run_calibration.py::run_year), so a prb-only --set of such a key is
    # silently re-stomped by the meta's kwarg value (the ERCOT-65 defect class,
    # kwarg-over-prb direction — discovered when an ecrs A/B replayed the
    # keeper byte-identically, ercot84 2026-07-18). Writing the same value to
    # both channels makes the last-applied channel carry it either way, and
    # keeps the recorded meta/run_config internally consistent.
    if args.overrides:
        from market_sim.config.scenarios import ScenarioConfig

        cfg_fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
        solve_params = set(inspect.signature(rcf.solve_and_persist).parameters)
    for spec in args.overrides:
        key, _, raw = spec.partition("=")
        if not key or not raw:
            raise SystemExit(f"--set expects KEY=JSON, got {spec!r}")
        val = json.loads(raw)
        routed = False
        if key in solve_params:
            kwargs[key] = val
            routed = True
        if key in cfg_fields:
            kwargs.setdefault("prb_overrides", {})
            kwargs["prb_overrides"][key] = val
            routed = True
        if not routed:
            raise SystemExit(
                f"--set {key}: neither a solve_and_persist kwarg nor a "
                "ScenarioConfig field — nothing would consume it"
            )
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
    # full-span replays — an overridden run (--set / --offer-curve-json) or a
    # partial-years chain invocation (--years) is a NEW run, not the keeper
    # fixed in place, and must mint its own dated id.
    if (
        orig_ts
        and not args.overrides
        and args.offer_curve_json is None
        and args.years is None
    ):
        new_meta = json.loads((run_dir / "meta.json").read_text())
        new_ts = new_meta.get("timestamp", "")
        new_meta["timestamp"] = orig_ts[:10] + new_ts[10:] if new_ts else orig_ts
        (run_dir / "meta.json").write_text(json.dumps(new_meta, indent=2) + "\n")
        print(f"restored meta timestamp date -> {orig_ts[:10]}")


if __name__ == "__main__":
    main()
