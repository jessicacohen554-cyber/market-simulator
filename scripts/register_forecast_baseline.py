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
invariant chips), and the richer forecast run explorer (FF-5A) will read these
sidecars by ``kind``. The page is regenerated exactly as hindcast registration
does, via ``register_hindcast.render_page`` over every committed sidecar.

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
    verbatim — used to record a CES leg's premium level / case / campaign. The
    two FF-1F posture defaults resolved by forecast mode
    (``datacenter_load_path="mid"``, ``correlated_forced_outage=True``) are
    recorded in ``meta`` so the "before" leg is self-describing.
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

    meta = {
        "iso": iso,
        "kind": kind,
        "label": label,
        "variant": "forecast-baseline",
        "mode": "forecast",
        "start_year": start,
        "end_year": end,
        "capacity_market_clearing": summary.get("capacity_market_clearing", False),
        # FF-1F posture defaults resolved by forecast mode at HEAD (S2.1a c/d).
        "datacenter_load_path": "mid",
        "correlated_forced_outage": True,
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
        page = RH.render_page(RH._load_all_sidecars())
        RH.PAGE_PATH.write_text(page)
        print(f"[register-forecast] regenerated {RH.PAGE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
