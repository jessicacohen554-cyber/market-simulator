"""Build a backcast benchmark ("bench") part for a year with NO LP solve.

A bench part (``frontend/data/backcast/bench/<ISO>/<year>.json.gz``) is the
per-year ACTUALS payload the Run Explorer, the verdict and several derives read
(per-plant CAMPD hourly, EIA-923 per-plant/class, EIA-930 per-fuel, the
CEMS-anchor fields). Its canonical writer is the registration render
(``render_calibration_html.build_payload`` ->
``backcast_artifacts.write_bench_part``), which reads a SOLVED bundle. That made
a new year circular for any derive that needs its bench part BEFORE the year can
be solved — CAISO's supply-consistent demand artifact
(``derive_caiso_supply_consistent_demand.py``) is exactly that, and caiso-262
broke the circle for 2022 with an LP "bench scaffold solve"
(``results/calibration/ADDENDUM-caiso262-inputs-2026-09-07.md`` §5).

The LP is not needed. The bench part depends on the run in ONE place only: the
dispatch frame's per-plant ``(plant_code, klass, zone)`` membership, which
decides which CAMPD/EIA-923 plants enter the part and under which class. The
dispatched MW never enters the bench. Everything else is a pure function of
``(year, iso)`` and committed data — ``run_calibration_full.
build_benchmark_frames`` (EIA-923 with CAMPD backfill, EIA-930, CAMPD net) and
``_btm_frame`` (measured CHP host shares) say so in their own docstrings.

So this script rebuilds the fleet with ``run_year(..., fleet_only=True)`` from a
bundle's recipe (``replay_keeper.run_year_kwargs`` — the only sanctioned
fleet-only reconstruction), writes a SCAFFOLD bundle into a scratch directory
whose dispatch frame carries that fleet at 0 MW (built by the solve's own
``_dispatch_frame``), plus the solve's own benchmark and BTM frames, then calls
the canonical render and keeps ONLY the bench year it produces. The scaffold is
disposable and never registered; nothing model-side it renders is kept.

VALIDATION (the reason to trust it): run against a year whose part was built
from a real solve and diff with ``--check``; every field the bench consumers
read must reproduce. ``avgLMP`` is not a solve product either — it follows the
committed ``actual_lmp.json`` at render time.

Usage::

    python scripts/data/build_bench_part_zero_lp.py \\
        --bundle results/calibration/xiso8_leftedge_span --years 2022 --check
    python scripts/data/build_bench_part_zero_lp.py \\
        --bundle results/calibration/xiso8_leftedge_span --years 2019 2020 2021 \\
        --set eia860_vintage_tracks_solve_year=true --set measured_st_heat_rates=true
"""

from __future__ import annotations

import argparse
import dataclasses
import gzip
import inspect
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
for _p in (_REPO / "src", _REPO, _REPO / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.results.outputs import FleetContext  # noqa: E402

BENCH_DIR = _REPO / "frontend" / "data" / "backcast" / "bench"
HOURS = 8760


def _apply_overrides(kwargs: dict, overrides: dict) -> None:
    """Route ``--set`` overrides through both run_year channels.

    The same two-channel rule ``replay_keeper --set`` applies (explicit kwarg
    when ``run_year`` takes one AND the ``prb_overrides`` ScenarioConfig bag
    when the key is a config field), so a flag cannot be re-stomped by the
    other channel. A key neither channel consumes is refused.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from scripts.run_calibration import run_year

    cfg_fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    params = set(inspect.signature(run_year).parameters)
    kwargs["prb_overrides"] = dict(kwargs.get("prb_overrides") or {})
    for key, val in overrides.items():
        routed = False
        if key in params:
            kwargs[key] = val
            routed = True
        if key in cfg_fields:
            kwargs["prb_overrides"][key] = val
            routed = True
        if not routed:
            raise SystemExit(f"--set {key}: nothing would consume it")


def _scaffold_bundle(bundle: Path, year: int, overrides: dict, scratch: Path) -> Path:
    """Write a zero-MW scaffold bundle for ``year`` and return its directory."""
    import scripts.run_calibration_full as rcf
    from scripts.lib.bundle_io import write_shared_input
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    iso = meta["iso"]
    base_zones = list(get_iso_config(iso).zone_names)

    kwargs = run_year_kwargs(meta)
    _apply_overrides(kwargs, overrides)
    built = run_year(year, iso, HOURS, 3.0, {}, fleet_only=True, **kwargs)
    fa = built["fleet_arrays"]
    # The year's topology-extended config (external corridor nodes): the fleet's
    # zone_idx indexes ITS zone list. Rows on a zone outside the base ISO
    # footprint are the import tranches; the bench never reads them (it keeps
    # plant_code > 0 fossil classes), and they are dropped below as the solve's
    # own endogenous-WECC exclusion drops them.
    iso_config = built["iso_config"]
    zone_names = list(iso_config.zone_names)
    ctx = FleetContext.from_arrays(
        fa,
        iso_config,
        built["wind_cf"],
        built["wind_cap"],
        built["solar_cf"],
        built["solar_cap"],
        np.zeros(0),
    )
    n_gen, n_z = len(fa.unit_ids), len(zone_names)
    zeros_z = np.zeros((n_z, HOURS), dtype=np.float32)
    result = SimpleNamespace(
        dispatch=np.zeros((n_gen, HOURS), dtype=np.float32),
        prices=zeros_z,
        slack=zeros_z,
        dump=zeros_z,
        wind_dispatched=zeros_z,
        solar_dispatched=zeros_z,
        reserve_price=None,
    )

    run_dir = scratch / f"bench_scaffold_{iso}_{year}"
    (run_dir / "dispatch").mkdir(parents=True, exist_ok=True)
    disp = rcf._dispatch_frame(year, "P1", result, ctx, zone_names, iso=iso)
    disp = disp[disp["zone"].astype(str).isin(base_zones)]
    disp.to_parquet(run_dir / "dispatch" / f"{year}_P1.parquet", index=False)
    rcf._system_frame(
        year, "P1", result, np.zeros((n_z, HOURS)), zone_names, iso=iso
    ).to_parquet(run_dir / "system.parquet", index=False)

    smeta = dict(meta)
    smeta["years"] = [int(year)]
    smeta["passes"] = ["P1"]
    smeta.pop("shared_inputs", None)
    smeta.pop("composed_from", None)
    (run_dir / "meta.json").write_text(json.dumps(smeta, indent=2) + "\n")
    rc = bundle / "run_config.json"
    if rc.exists():
        (run_dir / "run_config.json").write_text(rc.read_text())

    _, frames = rcf.build_benchmark_frames(run_dir)
    shared = {
        name: write_shared_input(f, name, iso, run_dir) for name, f in frames.items()
    }
    smeta["shared_inputs"] = shared
    (run_dir / "meta.json").write_text(json.dumps(smeta, indent=2) + "\n")

    campd = frames.get("campd")
    active = None
    if campd is not None:
        by_plant = campd.groupby("plant_id")["net_mw"].sum()
        active = set(by_plant[by_plant > 0.0].index.astype(int))
    rcf._btm_frame(
        year,
        "P1",
        rcf.load_monthly_generation(),
        btm_backfill_year=meta.get("btm_backfill_year"),
        campd_active=active,
        iso=iso,
        group_by_code=rcf._fleet_group_by_code(iso, get_iso_config(iso), year),
        nyiso_chp_btm_measured=bool(meta.get("nyiso_chp_btm_measured")),
    ).to_parquet(run_dir / "btm.parquet", index=False)
    return run_dir


def build_bench_year(
    bundle: Path, year: int, overrides: dict, scratch: Path
) -> tuple[dict, dict]:
    """Return ``(meta, bench_year)`` for ``year`` from a zero-LP scaffold."""
    from scripts import render_calibration_html as rch

    run_dir = _scaffold_bundle(bundle, year, overrides, scratch)
    payload = rch.build_payload([("scaffold", run_dir)], years={int(year)})
    meta = {k: payload[k] for k in ("groups", "groupLabel", "zones") if k in payload}
    return meta, payload["bench"][int(year)]


def _parse_set(specs: list[str]) -> dict:
    out: dict = {}
    for spec in specs:
        key, _, raw = spec.partition("=")
        if not key or not raw:
            raise SystemExit(f"--set expects KEY=JSON, got {spec!r}")
        out[key] = json.loads(raw)
    return out


def main() -> int:
    """CLI: build (or ``--check``) bench parts for the given years."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle", type=Path, required=True, help="bundle whose recipe to rebuild"
    )
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        help="KEY=JSON recipe override",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="diff against the committed part; write nothing",
    )
    args = ap.parse_args()
    overrides = _parse_set(args.overrides)
    meta_b = json.loads((args.bundle / "meta.json").read_text())
    iso = meta_b["iso"]

    from scripts.lib import backcast_artifacts as ba

    with tempfile.TemporaryDirectory() as tmp:
        for year in args.years:
            meta, bench_year = build_bench_year(args.bundle, year, overrides, Path(tmp))
            path = BENCH_DIR / iso / f"{year}.json.gz"
            if args.check:
                committed = json.loads(gzip.decompress(path.read_bytes()))["bench"]
                fresh = json.loads(json.dumps(bench_year))
                diff = sorted(
                    k
                    for k in set(committed) | set(fresh)
                    if committed.get(k) != fresh.get(k)
                )
                print(f"{iso} {year}: top-level keys differing: {diff or 'NONE'}")
                for k in diff:
                    c, f = committed.get(k), fresh.get(k)
                    if isinstance(c, dict) and isinstance(f, dict):
                        sub = sorted(x for x in set(c) | set(f) if c.get(x) != f.get(x))
                        print(f"   {k}: {len(sub)} sub-keys differ, e.g. {sub[:8]}")
                        for x in sub[:4]:
                            print(
                                f"      {x}: committed={str(c.get(x))[:120]} fresh={str(f.get(x))[:120]}"
                            )
                continue
            out = ba.write_bench_part(BENCH_DIR, iso, year, meta, bench_year)
            print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
