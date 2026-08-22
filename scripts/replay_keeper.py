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

After the solve the driver regenerates ``legitimacy_diagnostics.json`` for the
output bundle through the same ``scripts/legitimacy_diagnostics.py`` post-step
the normal calibration path uses, so C8 always has a fresh committed artifact
to score (closes the ercot-193-disclosed replay-path gap).

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
sys.path.insert(0, str(REPO))
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

from scripts import run_calibration_full as rcf  # noqa: E402

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
    # Origin-durable basis anchor (run_calibration_full._basis_sha). Pure
    # provenance, written fresh by every solve_and_persist — a replay must
    # carry the REPLAY's basis, never the original's, so this is ignored on
    # the way in and (unlike the timestamp date) never restored on the way
    # out; see _restore_display_date (caiso-122 §1 / caiso-123).
    "basis_sha",
    "highspy_version",
    # Runtime environment block (python/platform + numerics stack versions).
    # Provenance only — never a solve kwarg. main() surfaces a mismatch as a
    # loud non-fatal WARNING; here it must be ignored so build_kwargs (and the
    # --reuse-solved comparator that calls it) does not treat it as unmapped.
    "environment",
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
# ScenarioConfig fields DELETED by rule-26 [R-DELETE] collapses AFTER some
# registered bundles solved: their meta.json still records the field, and the
# recorded value is provenance. Keyed field -> (owning_iso, unconditional
# value the collapse made the only behaviour). Outside the owning ISO the
# mechanism was never reachable (rule 25 [R-ISO-SCOPE]), so the recorded
# default is inert and the key is skipped; inside it, only a bundle recording
# the now-unconditional value replays at HEAD — the other polarity selected a
# basis that no longer parses, and its epoch note says "read, never
# replayed", so build_kwargs hard-errors rather than silently replaying a
# different mechanism.
_RULE26_DELETED_UNCONDITIONAL: dict[str, tuple[str, object]] = {
    # nyiso-136 collapse (cache.py epoch 2026-08-15): market-solar
    # cod_basis=True is now NYISO's only basis. First keeper meta carrying
    # the recorded key: pjm-162 inputclock (solved at c447199 while the
    # field lived; promoted pjm-163, 2026-08-16).
    "nyiso_solar_registry_cod_dates": ("NYISO", True),
    # miso-177 (2026-08-22): the transient session field that delivered the
    # measured-rho arm before the same-day owner ruling deleted the RHO_CLIP
    # floor globally (nyiso-151, decision-card option A) — the field was
    # removed in the same session's reconciliation, never reaching main.
    # True (the arm/keeper 2026-08-22-miso-177-rho-measured) is the
    # unconditional post-ruling behaviour: the seam consumes the measured
    # 0.1764 by default, so the recorded key replays byte-equivalently.
    # False (the control 2026-08-22-miso-177-control) selected the deleted
    # 0.5-floor basis and correctly hard-errors as historical-record-only —
    # the same non-replayability the owner's ruling gave every pre-ruling
    # MISO bundle, the miso-175 keeper included.
    "miso_online_rho_no_floor": ("MISO", True),
}


def _strip_rule26_from_override_dict(channel: str, overrides: dict, meta: dict) -> dict:
    """Drop rule-26-deleted fields recorded INSIDE a generic override dict.

    ``_RULE26_DELETED_UNCONDITIONAL`` is applied to top-level meta keys, but the
    same field can also reach ``ScenarioConfig`` through a generic
    override channel that is splatted with ``with_overrides(**d)`` —
    ``coal_prb_sigmoid_overrides`` is one, and NYISO keepers record ~33 flags in
    it. A field deleted from ``ScenarioConfig`` then raises ``TypeError`` from
    inside ``run_year`` no matter how carefully the top-level keys were mapped,
    which is what made the designated NYISO keeper unreplayable at HEAD
    (discovered nyiso-140).

    Applies the SAME polarity check as the top-level path rather than dropping
    blindly: a recorded value equal to the now-unconditional behaviour is inert
    and safely dropped; the other polarity selected a basis that no longer
    exists, so it hard-errors instead of silently replaying a different
    mechanism (the miso-50..53 strictness).

    Args:
        channel: The override-dict meta key, for the error message.
        overrides: The recorded override mapping.
        meta: The whole bundle meta (for the solve's ISO).

    Returns:
        *overrides* without the rule-26-deleted entries (a copy only when one
        was present, so the common path is unchanged).
    """
    hits = [k for k in overrides if k in _RULE26_DELETED_UNCONDITIONAL]
    if not hits:
        return overrides
    out = dict(overrides)
    for k in hits:
        owner_iso, unconditional = _RULE26_DELETED_UNCONDITIONAL[k]
        v = out.pop(k)
        if meta.get("iso") == owner_iso and v != unconditional:
            raise SystemExit(
                f"bundle records the rule-26-deleted field {k}={v!r} inside "
                f"{channel} on an {owner_iso} solve: the basis that value "
                f"selected no longer exists at HEAD (the collapse made "
                f"{unconditional!r} unconditional), so a kwargs replay would "
                "run a DIFFERENT mechanism than the bundle. Historical record "
                "— read, never replayed (see the cache.py epoch note)."
            )
    return out


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
        if k in _RULE26_DELETED_UNCONDITIONAL:
            owner_iso, unconditional = _RULE26_DELETED_UNCONDITIONAL[k]
            if meta.get("iso") == owner_iso and v != unconditional:
                raise SystemExit(
                    f"bundle records the rule-26-deleted field {k}={v!r} on an "
                    f"{owner_iso} solve: the basis that value selected no "
                    f"longer exists at HEAD (the collapse made {unconditional!r} "
                    "unconditional), so a kwargs replay would run a DIFFERENT "
                    "mechanism than the bundle. Historical record — read, "
                    "never replayed (see the cache.py epoch note)."
                )
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
            if isinstance(v, dict) and v:
                v = _strip_rule26_from_override_dict(k, v, meta)
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
    # Same backstop for the coal econ marginal-HR floor, which became the ERCOT
    # backcast default-ON at the ercot-115 promotion (2026-07-26) and whose
    # solve kwarg is likewise tri-state. A bundle solved before the promotion
    # carries no key in meta.json; replaying it byte-faithfully means the floor
    # OFF, not today's default. Post-promotion bundles record their resolved
    # value and are unaffected.
    if (
        meta.get("iso", "").upper() == "ERCOT"
        and "coal_econ_marginal_hr_bound" not in meta
    ):
        kwargs["coal_econ_marginal_hr_bound"] = False
    return kwargs


def _warn_on_environment_mismatch(meta: dict) -> None:
    """Print a loud (non-fatal) WARNING when the runtime environment drifted.

    A byte-faithful replay is only meaningful under the same solver/numerics
    stack the keeper was solved with (alternate-optimal vertices move across
    versions). We surface any drift so a non-reproducing replay can be traced to
    it — but never fail: a bundle solved before the environment block existed
    records nothing, and the operator may deliberately replay on a new stack.
    """
    recorded = meta.get("environment")
    if not recorded:
        return  # pre-environment-block bundle; nothing to compare
    current = rcf._environment_block()
    diffs: list[str] = []
    for field in ("python_version", "platform"):
        if recorded.get(field) != current.get(field):
            diffs.append(
                f"{field}: bundle {recorded.get(field)!r} != now {current.get(field)!r}"
            )
    rec_pkgs = recorded.get("packages") or {}
    cur_pkgs = current.get("packages") or {}
    for name in sorted(set(rec_pkgs) | set(cur_pkgs)):
        if rec_pkgs.get(name) != cur_pkgs.get(name):
            diffs.append(
                f"{name}: bundle {rec_pkgs.get(name)!r} != now {cur_pkgs.get(name)!r}"
            )
    if diffs:
        print(
            "WARNING: replay environment differs from the bundle's recorded "
            "environment — byte-identity is not guaranteed:\n  " + "\n  ".join(diffs),
            file=sys.stderr,
        )


def _write_legitimacy_diagnostics(run_dir: Path, iso: str) -> None:
    """Generate ``<run_dir>/legitimacy_diagnostics.json`` via the S1 suite.

    The normal calibration path produces this artifact as a post-solve step:
    the operator runs ``scripts/legitimacy_diagnostics.py --bundle <dir>
    --iso <ISO> --json-out <dir>/legitimacy_diagnostics.json`` (the
    ``calibration_verdict._LEGIT_HOWTO`` contract), and the rubric's C7/C8
    score from the committed artifact without ever recomputing it. The replay
    driver historically stopped at the solve, leaving a replayed bundle with
    no artifact for C8 to score — the ercot-193-disclosed tooling gap
    (calibration-log "Disclosures" block / FINDING-ercot193-soc-regate §4).
    Close it by invoking the SAME entry point on the replayed bundle: same
    suite, same CLI surface, no second implementation ([R-ONE-MECH] spirit).
    A replayed bundle has everything the post-step needs — the solve just
    rewrote ``floors/*.npz`` and the dispatch parquets — so nothing is
    approximated.

    A diagnostics gate FAIL does not fail the replay: ``--json-out`` is
    written before the suite's exit code is decided, and the artifact's job
    is disclosure (the rubric scores from its contents). Likewise a hard
    error in the suite is reported loudly with the manual fallback command
    rather than discarding a completed multi-hour solve at the finish line.
    """
    from scripts import legitimacy_diagnostics as ld

    json_out = run_dir / "legitimacy_diagnostics.json"
    argv = ["--bundle", str(run_dir), "--iso", iso, "--json-out", str(json_out)]
    try:
        rc = ld.main(argv)
    except (Exception, SystemExit) as exc:
        print(
            "WARNING: legitimacy diagnostics generation failed "
            f"({exc!r}) — the replayed bundle carries no fresh "
            "legitimacy_diagnostics.json; run scripts/legitimacy_diagnostics.py "
            f"--bundle {run_dir} --iso {iso} --json-out {json_out} manually",
            file=sys.stderr,
        )
        return
    print(f"legitimacy diagnostics written -> {json_out}")
    if rc != 0:
        print(
            "WARNING: legitimacy diagnostics gate FAIL on the replayed bundle "
            "(artifact still written; C7/C8 score from its contents — see the "
            "report above)",
            file=sys.stderr,
        )


def _restore_display_date(run_dir: Path, orig_ts: str) -> str:
    """Restore ONLY the original date prefix of the replayed meta timestamp.

    The dashboard run id is ``<date>-<shorthand>``, so a byte-faithful
    in-place replay keeps the original DATE (id stability) while the
    time-of-day stays the replay's. Every other meta.json field —
    ``basis_sha`` and ``git_sha`` above all — is left as solve_and_persist
    freshly wrote it: a replayed bundle's provenance must date the bytes on
    disk, not the destroyed original session (caiso-122 §1: the hybrid
    timestamp plus a dead ``git_sha`` left the keeper with no usable basis
    anchor; ``basis_sha`` is that anchor and restoring it here would re-open
    the defect). Returns the timestamp written back.
    """
    meta_path = run_dir / "meta.json"
    new_meta = json.loads(meta_path.read_text())
    new_ts = new_meta.get("timestamp", "")
    new_meta["timestamp"] = orig_ts[:10] + new_ts[10:] if new_ts else orig_ts
    meta_path.write_text(json.dumps(new_meta, indent=2) + "\n")
    return new_meta["timestamp"]


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
        "--holdout-authorized",
        action="store_true",
        help="acknowledge that --years names an out-of-training year (rule 22). "
        "Required, and NOT sufficient: the spend freeze must be lifted and the "
        "target ISO must carry the marker for that year's TIER ('complete' for "
        "the validation ladder, 'final' for the touch-once locked test).",
    )
    ap.add_argument(
        "--enable-legacy-p2",
        action="store_true",
        help="unlock the ARCHIVED P2 commitment pass when the REPLAYED RECIPE "
        "arms it (meta.json commitment/persist_p2_state/...). Without this a "
        "bundle recorded with commitment=true is a hard error instead of a "
        "silent re-arm: P0/P1 are the only production passes and every run is "
        'scored on P1 (CLAUDE.md "Dispatch & Commitment"). To move a recipe '
        "onto the production basis instead, pass --set commitment=false.",
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
    _warn_on_environment_mismatch(meta)

    kwargs = build_kwargs(meta)
    kwargs["years"] = [int(y) for y in (args.years or meta["years"])]
    kwargs["iso"] = meta["iso"]
    # Rule 22 gate. This driver calls solve_and_persist DIRECTLY rather than
    # through run_calibration_full.main(), so until 2026-08-05 it reached the
    # solver without passing the freeze or marker checks at all: --years 2022
    # on any keeper bundle solved a holdout year with no gate. That is the same
    # hole holdout-policy-memo-2026-07.md (b)(2) closed at the calibration CLI's
    # own entry point, reopened by a second entry point. Gate here too, with the
    # identical function, so the two paths cannot diverge.
    rcf.enforce_holdout_year_gate(
        kwargs["years"], kwargs["iso"], args.holdout_authorized
    )
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
    # ARCHIVED-P2 gate on the RECONSTRUCTED recipe (audit row O5). Placed AFTER
    # the --set loop so `--set commitment=false` is what disarms it, and before
    # the solve so a bundle recorded with commitment=true can never re-arm P2
    # implicitly. run_calibration_full's own CLI gate only sees parsed CLI args
    # and is blind to this path.
    rcf.enforce_legacy_p2_kwargs(kwargs, args.enable_legacy_p2)
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
    # full-span replays IN PLACE — an overridden run (--set /
    # --offer-curve-json), a partial-years chain invocation (--years), or a
    # solve redirected to a different --out-dir is a NEW run, not the keeper
    # fixed in place, and must mint its own dated id.
    #
    # The --out-dir clause is miso-117: a ZERO-DELTA CONTROL arm takes no
    # --set, so it satisfied every other condition and inherited the keeper's
    # date — dating a bundle solved 2026-08-03 as 2026-07-31, three days before
    # its own treatment arm (which carries --set and is dated correctly). One
    # A/B, two dates, and the control's dashboard id claiming a solve date it
    # does not have. The bundle is not the keeper's, so its id is not the
    # keeper's either.
    redirected = args.out_dir is not None and Path(args.out_dir).resolve() != (
        bundle.resolve()
    )
    if (
        orig_ts
        and not args.overrides
        and args.offer_curve_json is None
        and args.years is None
        and not redirected
    ):
        _restore_display_date(run_dir, orig_ts)
        print(f"restored meta timestamp date -> {orig_ts[:10]}")

    # Post-solve diagnostics artifact, exactly as the normal calibration path
    # produces it (see _write_legitimacy_diagnostics). After the date restore
    # so the suite reads the bundle in its final on-disk state.
    _write_legitimacy_diagnostics(run_dir, meta["iso"])


if __name__ == "__main__":
    main()
