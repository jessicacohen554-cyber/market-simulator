#!/usr/bin/env python
"""Register a T1-F forecast-baseline run on the forecast-validation dashboard.

The T1-F short forecast (plan S2.1, 2026-2030, HEAD defaults) is a *forecast*
probe, not a capacity hindcast, so it is produced by ``run_full_horizon.py``
(one ``full_horizon_summary.json`` per ISO) rather than by
``run_capacity_hindcast.py``. This helper turns that summary into a sidecar in
the SAME namespace ``register_hindcast.py`` uses (``frontend/data/hindcast/``,
the forecast-validation namespace - never the backcast registry, plan S2.3/S7.5)
so the run shows on the forecast-validation page and is reusable as a Wave-1/2
"before" leg (FF-0B: solve once, reuse forever).

The sidecar mirrors the hindcast sidecar shape - ``run_id`` / ``meta`` /
``score`` / ``invariants`` / ``registered_utc`` - with ``score`` left ``null``
(a t1f run has no retirement/addition-band score.json; the capacity-hindcast
scorer does not apply) and ``kind="t1f"`` / ``label`` recorded in ``meta``. The
existing self-contained page renderer tolerates ``score=null`` (it shows the
invariant chips), and the richer forecast run explorer (FF-5A) reads these
sidecars by ``kind``. The dashboard is regenerated exactly as hindcast
registration does — since FF-5A that means ``register_forecast_run.reindex``
over every committed sidecar, not the retired ``register_hindcast.render_page``.

Usage::

    python scripts/register_forecast_baseline.py \
        --summary results/ff-t1f-baseline/miso/full_horizon_summary.json \
        --label ff-t1f-baseline
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts import register_hindcast as RH  # noqa: E402
from scripts.lib.run_record import (  # noqa: E402
    Derived,
    FromConfig,
    RecordSpec,
    config_field_names,
)

_SRC = _ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from market_sim.config.capacity_market import (  # noqa: E402
    resolve_capacity_market_clearing,
)

#: The forecast sidecar's config-describing block (FFR-3R). Before this, three
#: of these keys were sourced from neither the config NOR ``args`` but from
#: HARDCODED LITERALS mirroring the shipped defaults ("the FF-1F posture
#: defaults resolved by forecast mode at HEAD") — the same defect class one
#: step worse, since a mirrored literal cannot even track a flag. FFR-3D
#: recorded the cost of exactly that pattern in ``build_config``: "a mirrored
#: literal here would have silently overridden both flips and made the signed
#: decisions inert". They are now read off the run's OWN resolved
#: ``ScenarioConfig`` dump.
SIDECAR_RECORD_SPEC = RecordSpec(
    {
        "iso": FromConfig(),
        "mode": FromConfig(),
        "start_year": FromConfig(),
        "end_year": FromConfig(),
        # The RESOLVED per-ISO clearing gate, not the scalar field — under
        # --golden-posture the scalar stays False while the by-ISO dict carries
        # the curve-ON ISOs, and forecast_verdict._curve_on reads this key
        # (FFR-2E).
        "capacity_market_clearing": Derived(
            lambda cfg, ctx: bool(resolve_capacity_market_clearing(cfg, ctx["iso"])),
            "the RESOLVED per-ISO gate (FFR-2E), not the scalar field",
        ),
        "datacenter_load_path": FromConfig(),
        "correlated_forced_outage": FromConfig(cast=bool),
    },
    name="forecast-baseline sidecar meta",
)


def _extra_meta_spec(meta: dict) -> RecordSpec:
    """Auto-declare every config-named key a campaign merged into ``meta``.

    ``--extra-meta`` (and a leg driver's summary block) can contribute keys this
    registrar has no vocabulary for — the CES legs record
    ``federal_ces_crediting`` that way. Rejecting them as undeclared would break
    a legitimate provenance channel; leaving them unchecked is the FFR-3R defect
    with a longer fuse. So each is declared ``FromConfig`` on the spot, which
    means it must EQUAL the run's own resolved config: a hand-typed claim about
    the solve is allowed through only when the solve agrees with it.

    Args:
        meta: The assembled sidecar meta.

    Returns:
        A spec declaring the config-named keys not already in
        ``SIDECAR_RECORD_SPEC``.
    """
    extra = (config_field_names() & set(meta)) - set(SIDECAR_RECORD_SPEC.sources)
    return RecordSpec(
        {k: FromConfig() for k in sorted(extra)}, name="campaign extra_meta"
    )


def resolved_config(summary_path: Path, summary: dict) -> dict | None:
    """Return the run's RESOLVED ``ScenarioConfig`` dump, or ``None``.

    ``run_full_horizon.write_run_config`` writes ``run_config.json`` beside the
    summary from the solve's own ``run_dir/config.yaml`` — the faithful
    post-``__post_init__`` resolution, which is what a record must describe.
    Falls back to reading that ``config.yaml`` directly when the run predates
    the sidecar artifact but its cache directory is still on disk.

    Returns ``None`` when neither exists. A caller must then record the
    config-describing keys as ``None`` (unknown) rather than substitute a
    default: fabricating a value is how the record starts lying, and rubric §4
    forbids authoring an artifact after the fact.

    Args:
        summary_path: Path to the ``full_horizon_summary.json``.
        summary: Its parsed contents (for ``run_dir``).

    Returns:
        The resolved config mapping, or ``None``.
    """
    rc = summary_path.parent / "run_config.json"
    if rc.exists():
        payload = json.loads(rc.read_text())
        sc = payload.get("scenario_config")
        if isinstance(sc, dict) and sc:
            return sc
    run_dir = summary.get("run_dir")
    if run_dir:
        cfg_yaml = Path(run_dir) / "config.yaml"
        if cfg_yaml.exists():
            import yaml

            resolved = yaml.safe_load(cfg_yaml.read_text())
            if isinstance(resolved, dict) and resolved:
                return resolved
    return None


def build_sidecar(
    summary_path: Path,
    label: str,
    kind: str = "t1f",
    extra_meta: dict | None = None,
) -> dict:
    """Assemble the forecast-validation sidecar dict from a full-horizon summary.

    ``summary_path`` is a ``full_horizon_summary.json`` written by
    ``run_full_horizon.py`` (or a leg summary of the same shape, e.g. the
    FF-3B CES POC driver); ``label`` is the campaign tag (e.g.
    ``ff-t1f-baseline`` or ``ces-poc-bau``). ``kind`` records the run family the
    FF-5A forecast run explorer groups by (``t1f`` default; ``ces-poc`` for a
    T1-scale CES proof-of-concept leg). ``extra_meta`` is merged into ``meta``
    verbatim — used to record a CES leg's premium level / case / campaign.

    The config-describing keys (``mode``, the resolved ``capacity_market_clearing``
    gate, ``datacenter_load_path``, ``correlated_forced_outage``, the window) are
    read from the run's OWN resolved ``ScenarioConfig`` dump through
    ``SIDECAR_RECORD_SPEC`` and asserted against it before the sidecar is
    returned (FFR-3R). They were previously LITERALS mirroring the shipped
    forecast-mode defaults, so the sidecar asserted a posture rather than
    reporting one; a default flip or a new control-arm flag would have made
    every sidecar silently wrong, which is exactly the FFR-3D history. Keys the
    dump cannot answer are recorded ``null``, never defaulted.

    ``extra_meta`` is merged AFTER the block and is re-checked, so a hand-typed
    ``--extra-meta`` cannot overwrite a config-describing key with a claim the
    solve contradicts.
    """
    summary = json.loads(summary_path.read_text())
    iso = summary["iso"]
    start, end = summary["start_year"], summary["end_year"]
    run_id = f"{iso.lower()}-{start}-{end}-{label}"

    # run_full_horizon records invariants with key ``id``; the page renderer
    # reads ``ident`` (the hindcast sidecar key). Map it through.
    invariants = [
        {
            "ident": inv.get("id", inv.get("ident")),
            "name": inv.get("name"),
            "status": inv.get("status"),
            "detail": inv.get("detail", ""),
        }
        for inv in summary.get("invariants", [])
    ]

    # Compact per-year comparison summary - the essential "before leg" metrics for
    # a Wave-1/2 diff (RM, price, CO2, scarcity proxy, evolution deltas). The full
    # per-hour trajectory + capacity_by_fuel dicts stay in the findings doc tables
    # and the (gitignored) full_horizon_summary.json; the committed sidecar mirrors
    # the lean hindcast-sidecar convention (headline meta + invariants).
    def _rnd(x, n):
        return round(x, n) if isinstance(x, (int, float)) else x

    year_summary = [
        {
            "year": r["year"],
            "reserve_margin": _rnd(r.get("reserve_margin"), 4),
            "lw_price": _rnd(r.get("lw_price"), 2),
            "max_hourly_price": _rnd(r.get("max_hourly_price"), 1),
            "co2_mt": _rnd(r.get("co2_mt"), 2),
            "hours_ge_500": r.get("hours_ge_500"),
            "retire_mw": _rnd(r.get("retire_mw"), 1),
            "builds_thermal_mw": _rnd(r.get("builds_thermal_mw"), 1),
            "builds_renew_mw": _rnd(r.get("builds_renew_mw"), 1),
            "builds_storage_mw": _rnd(r.get("builds_storage_mw"), 1),
        }
        for r in summary.get("trajectory", [])
    ]

    # Config-describing keys come from the run's OWN resolved ScenarioConfig
    # dump (FFR-3R), never from a literal mirroring today's shipped default.
    # When the dump is missing they are recorded as null — "not recoverable
    # from this bundle" is the truthful statement; a substituted default is the
    # defect (see resolved_config).
    resolved = resolved_config(summary_path, summary)
    if resolved is not None:
        config_block = SIDECAR_RECORD_SPEC.build(resolved, {"iso": iso})
    else:
        config_block = {k: None for k in SIDECAR_RECORD_SPEC.sources}
        config_block["iso"] = iso
        config_block["start_year"] = start
        config_block["end_year"] = end

    meta = {
        "kind": kind,
        "label": label,
        "variant": "forecast-baseline",
        **config_block,
        "cache_key": summary.get("cache_key"),
        "bundle": summary.get("run_dir"),
        "solved_years": summary.get("solved_years", []),
        "n_solved_years": summary.get("n_solved_years", 0),
        "error": summary.get("error"),
        "total_wall_s": summary.get("total_wall_s"),
        "global_peak_rss_mb": summary.get("global_peak_rss_mb"),
        "per_year_perf": summary.get("per_year_perf", []),
        "year_summary": year_summary,
        "started_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # No hindcast bridge/holdout concept in a pure-forecast run.
        "bridged_years": [],
    }
    if extra_meta:
        meta.update(extra_meta)
    if resolved is not None:
        # Re-checked AFTER the extra_meta merge: --extra-meta is a hand-typed
        # JSON blob on the command line, the most direct way there is to assert
        # something the solve did not do. Any key it adds that names a
        # ScenarioConfig field is AUTO-DECLARED FromConfig and thereby checked
        # for equality against the run's own resolved config — a campaign
        # vocabulary this registrar cannot know in advance (the CES legs record
        # federal_ces_crediting here) stays usable, but only when it is true.
        SIDECAR_RECORD_SPEC.merged(_extra_meta_spec(meta)).assert_sourced(
            meta, resolved, {"iso": iso}
        )
    return {
        "run_id": run_id,
        "meta": meta,
        "score": None,
        "invariants": invariants,
        "registered_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        type=Path,
        required=True,
        help="full_horizon_summary.json produced by run_full_horizon.py.",
    )
    parser.add_argument(
        "--label",
        default="ff-t1f-baseline",
        help="Campaign tag recorded in the run_id and meta (default ff-t1f-baseline).",
    )
    parser.add_argument(
        "--kind",
        default="t1f",
        help="Run family the FF-5A explorer groups by (default t1f; "
        "'ces-poc' for a T1-scale CES proof-of-concept leg).",
    )
    parser.add_argument(
        "--extra-meta",
        default=None,
        help="Optional JSON object merged verbatim into meta (e.g. a CES leg's "
        'premium level: \'{"premium_usd_per_mwh": 20.0, "case": "CES-20"}\').',
    )
    parser.add_argument(
        "--no-page",
        action="store_true",
        help="Write the sidecar only; skip regenerating forecast-validation.html.",
    )
    args = parser.parse_args(argv)

    extra_meta = json.loads(args.extra_meta) if args.extra_meta else None
    RH.SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
    sidecar = build_sidecar(
        args.summary, args.label, kind=args.kind, extra_meta=extra_meta
    )
    sidecar_path = RH.SIDECAR_DIR / f"{sidecar['run_id']}.json"
    sidecar_path.write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n")
    print(f"[register-forecast] wrote sidecar {sidecar_path}")

    if not args.no_page:
        # FF-5A: forecast-validation.html is retired (redirect stub). Register the
        # run into the live forecast namespace via the single path instead of
        # regenerating the retired self-contained page.
        from scripts import register_forecast_run as RF  # noqa: PLC0415

        RF.register_one(sidecar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
