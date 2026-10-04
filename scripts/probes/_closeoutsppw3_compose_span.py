"""closeout-SPP-w3, zero LP: compose the seven year-isolated ARM legs into ONE SPP span bundle.

Copy of ``_closeoutsppnuc_compose_span.py`` with one change: each leg must be the keeper's
recipe PLUS the declared arm (``--arm FIELD=JSON``, repeatable), and every other field must
equal the keeper's. Every other check (one pin, one solve-surface fingerprint, complete legs)
and the mechanical composition are unchanged. Lane arm (PRECOMMIT-closeout-spp-w3-ptc-hydroenv):
``wind_ptc_vintage_offers=true`` and ``hydro_dispatch_envelope=true``.

Usage::

    python scripts/probes/_closeoutsppw3_compose_span.py --iso SPP \
        --keeper results/calibration/closeout_spp_nuc_span \
        --leg 2019=results/calibration/closeout_spp_w3_2019 ... \
        --arm wind_ptc_vintage_offers=true --arm hydro_dispatch_envelope=true \
        --pinned-sha <pin> --out results/calibration/closeout_spp_w3_span
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ROOT_FRAMES = ("system.parquet", "btm.parquet", "flows.parquet", "storage.parquet")
#: Provenance keys a re-solve writes fresh; never a recipe difference.
PROVENANCE = {"note", "timestamp", "git_sha", "basis_sha"}
#: Fields a single-config keeper records for its first year only.
YEAR_INDEXED = {"weather_year", "gas_price_override"}


def _registered_defaults() -> dict:
    """ScenarioConfig field defaults, JSON-normalised like a recorded config."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    out = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.default is not dataclasses.MISSING:
            value = f.default
        elif f.default_factory is not dataclasses.MISSING:
            value = f.default_factory()
        else:
            continue
        out[f.name] = json.loads(json.dumps(value, default=str))
    return out


def _resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else REPO / path


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _keeper_config(keeper: Path, year: int) -> dict:
    per = keeper / f"run_config_{year}.json"
    return _json(per if per.is_file() else keeper / "run_config.json")


def _fingerprint(cfg: dict) -> str | None:
    return (cfg.get("solve_surface") or {}).get("fingerprint")


def check_legs(
    keeper: Path, legs: dict[int, Path], kept: list[int], pin: str, arm: dict | None = None
) -> list[str]:
    """Assert each leg is the keeper's recipe plus exactly the declared arm; return report lines."""
    arm = arm or {}
    report: list[str] = []
    defaults = _registered_defaults()
    surfaces: dict[int, str | None] = {}
    for year, leg in sorted(legs.items()):
        cfg = _json(leg / "run_config.json")
        sc = cfg.get("scenario_config", {})
        ksc = _keeper_config(keeper, year).get("scenario_config", {})
        for field, value in arm.items():
            if json.dumps(sc.get(field), sort_keys=True) != json.dumps(value, sort_keys=True):
                raise SystemExit(f"ABORT {leg.name}: arm {field}={sc.get(field)!r}, want {value!r}")
        diffs = sorted(
            k
            for k in (set(sc) | set(ksc)) - PROVENANCE - set(arm)
            if json.dumps(sc.get(k), sort_keys=True)
            != json.dumps(ksc[k] if k in ksc else defaults.get(k), sort_keys=True)
        )
        if diffs:
            detail = "; ".join(f"{k}: {ksc.get(k)!r} -> {sc.get(k)!r}" for k in diffs)
            raise SystemExit(
                f"ABORT {leg.name}: recipe differs from {keeper.name} {year}: {detail}"
            )
        for need in (
            f"dispatch/{year}_P1.parquet",
            f"hourly/unit_marginal_{year}.parquet",
        ):
            if not (leg / need).is_file():
                raise SystemExit(f"ABORT {leg.name}: {need} missing")
        meta = _json(leg / "meta.json")
        years = sorted(int(y) for y in (meta.get("years") or [year]))
        if years != [year]:
            raise SystemExit(f"ABORT {leg.name}: meta years {years} != [{year}]")
        got = str(meta.get("git_sha") or cfg.get("git_sha") or "")
        if not got or not pin.startswith(got):
            raise SystemExit(f"ABORT {leg.name}: source sha {got!r} != pinned {pin}")
        surfaces[year] = _fingerprint(cfg)
        report.append(
            f"  {year} {leg.name}: recipe = {keeper.name} + arm {sorted(arm)} (0 other differing fields), sha {got}"
        )
    kmeta = _json(keeper / "meta.json")
    for year in kept:
        kcfg = _keeper_config(keeper, year)
        for need in (
            f"hourly/unit_marginal_{year}.parquet",
            f"hourly/system_{year}.parquet",
        ):
            if not (keeper / need).is_file():
                raise SystemExit(f"ABORT kept {year}: {keeper.name}/{need} missing")
        surfaces[year] = _fingerprint(kcfg)
        report.append(f"  {year} KEPT from {keeper.name} at {kmeta.get('git_sha')}")
    if len(set(surfaces.values())) != 1 or None in surfaces.values():
        raise SystemExit(
            f"ABORT: legs disagree on solve_surface fingerprint: {surfaces}"
        )
    report.append(
        f"  solve_surface fingerprint shared: {next(iter(surfaces.values()))}"
    )
    return report


def compose(legs: dict[int, Path], kept: list[int], out: Path, keeper: Path) -> None:
    """Copy per-year files from legs and kept keeper years; write meta/run_config."""
    if out.exists():
        raise SystemExit(f"ABORT: {out} exists; refusing to overwrite (rule 31)")
    for sub in ("dispatch", "floors", "hourly"):
        (out / sub).mkdir(parents=True)
    frames: dict[str, list[pd.DataFrame]] = {n: [] for n in ROOT_FRAMES}
    sources = {y: legs[y] for y in legs} | {y: keeper for y in kept}
    for year, src in sorted(sources.items()):
        for sub in ("dispatch", "floors", "hourly"):
            for path in sorted((src / sub).glob(f"*{year}*")):
                shutil.copy2(path, out / sub / path.name)
        if year in legs:
            for path in (legs[year] / "dispatch").glob("*"):
                if str(year) not in path.name:
                    raise SystemExit(f"ABORT: {path} carries no year {year}")
            for fname in ROOT_FRAMES:
                path = legs[year] / fname
                if path.is_file():
                    df = pd.read_parquet(path)
                    if "year" not in df.columns:
                        df = df.assign(year=year)
                    frames[fname].append(df)
            per = legs[year] / f"run_config_{year}.json"
            shutil.copy2(
                per if per.is_file() else legs[year] / "run_config.json",
                out / f"run_config_{year}.json",
            )
        else:
            shutil.copy2(_keeper_path(keeper, year), out / f"run_config_{year}.json")
        if (src / f"fleet_census_{year}.json").is_file():
            shutil.copy2(
                src / f"fleet_census_{year}.json", out / f"fleet_census_{year}.json"
            )
    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
    years = sorted(sources)
    # Base run_config / meta follow the keeper's own (identical recipe), widened
    # to the span; the keeper's base year is a kept or re-solved leg either way.
    base_cfg = _json(keeper / "run_config.json")
    flags = base_cfg.setdefault("calibration_flags", {})
    flags["years"] = years
    (out / "run_config.json").write_text(json.dumps(base_cfg, indent=2) + "\n")
    first = min(legs)
    if (legs[first] / "solve_surface.json").is_file():
        shutil.copy2(legs[first] / "solve_surface.json", out / "solve_surface.json")
    meta = _json(keeper / "meta.json")
    leg_meta = _json(legs[first] / "meta.json")
    for k in ("timestamp", "git_sha", "basis_sha", "note"):
        if k in leg_meta:
            meta[k] = leg_meta[k]
    meta["years"] = years
    meta["composed_from"] = {legs[y].name: [y] for y in sorted(legs)} | {
        keeper.name: list(kept)
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    _respan_shared_inputs(meta, out)
    from scripts.replay_keeper import CONFIG_PARTITION_KEY
    from scripts.stamp_config_partition import build_block

    block = build_block(
        out, [([y], f"run_config_{y}.json") for y in years], "run_config.json"
    )
    meta.pop(CONFIG_PARTITION_KEY, None)
    if any(not k.startswith("_") for k in block):
        meta[CONFIG_PARTITION_KEY] = block
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"composed {out.relative_to(REPO)}: {n} files, years {years}")


def _keeper_path(keeper: Path, year: int) -> Path:
    per = keeper / f"run_config_{year}.json"
    return per if per.is_file() else keeper / "run_config.json"


def _respan_shared_inputs(meta: dict, out: Path) -> None:
    """Re-point the per-year benchmark frames at the whole span (miso-267).

    ``eia930`` / ``eia923`` / ``campd`` are one-year frames per single-year leg;
    the first leg's hashes would make ``--restore-shared-inputs`` compare a
    span rebuild to a one-year hash and refuse. Rebuilt over the composite's
    own ``meta.json`` recipe through the single builder, content-addressed —
    the ``_miso280_compose_span.py`` construction.
    """
    recorded = meta.get("shared_inputs")
    if not recorded:
        return
    sys.path.insert(0, str(REPO))
    from scripts.lib.bundle_io import SHARED_INPUT_NAMES
    from scripts.run_calibration_full import build_benchmark_frames, write_shared_input

    stale = [n for n in SHARED_INPUT_NAMES if n in recorded]
    if not stale:
        return
    iso, built = build_benchmark_frames(out)
    for name in sorted(stale):
        if name not in built:
            raise SystemExit(f"compose: span rebuild produced no {name!r} frame")
        was = recorded[name]
        recorded[name] = write_shared_input(built[name], name, iso, out)
        print(f"  shared {name:<7} {Path(was).name} -> {Path(recorded[name]).name}")
    meta["shared_inputs"] = recorded


def regenerate_diagnostics(out: Path, iso: str, years: list[int]) -> int:
    """Rebuild ``legitimacy_diagnostics.json`` over the whole composite (zero LP)."""
    art = out / "legitimacy_diagnostics.json"
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "legitimacy_diagnostics.py"),
        "--bundle",
        str(out),
        "--iso",
        iso,
        "--years",
        *map(str, years),
        "--json-out",
        str(art),
    ]
    rc = subprocess.run(cmd, cwd=REPO).returncode
    if not art.is_file():
        print(f"NO legitimacy_diagnostics.json written (exit {rc}); do not register")
        return 1
    got = sorted(_json(art).get("years") or [])
    if got != sorted(years):
        print(f"legitimacy_diagnostics years {got} != {sorted(years)}; do not register")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--keeper", required=True, help="incumbent bundle")
    ap.add_argument("--leg", action="append", required=True, metavar="YEAR=BUNDLE")
    ap.add_argument("--kept", default="", help="comma list of years kept from --keeper")
    ap.add_argument(
        "--pinned-sha", required=True, help="40-char sha of every re-solved leg"
    )
    ap.add_argument(
        "--inert-proof", help="zero-LP byte-inert proof (required with --kept)"
    )
    ap.add_argument("--arm", action="append", default=[], metavar="FIELD=JSON",
                    help="declared arm field; the only allowed recipe difference")
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args(argv)
    legs = {int(y): _resolve(b) for y, _, b in (s.partition("=") for s in args.leg)}
    kept = sorted(int(y) for y in args.kept.split(",") if y)
    if set(kept) & set(legs):
        raise SystemExit("ABORT: a year is both re-solved and kept")
    if kept and not args.inert_proof:
        raise SystemExit("ABORT: kept legs need --inert-proof")
    if len(args.pinned_sha) != 40:
        raise SystemExit("ABORT: --pinned-sha must be the full 40-char sha")
    keeper = _resolve(args.keeper)
    arm = {k: json.loads(v) for k, _, v in (a.partition("=") for a in args.arm)}
    lines = check_legs(keeper, legs, kept, args.pinned_sha, arm)
    print("recipe check:\n" + "\n".join(lines))
    if args.check_only:
        return 0
    if not args.out:
        raise SystemExit("--out is required unless --check-only")
    out = _resolve(args.out)
    compose(legs, kept, out, keeper)
    if kept:
        kmeta = _json(keeper / "meta.json")
        per_year = {str(y): args.pinned_sha for y in sorted(legs)} | {
            str(y): str(kmeta.get("git_sha")) for y in kept
        }
        (out / "mixed_solve_sha.json").write_text(
            json.dumps(
                {"per_year": per_year, "inert_proof": args.inert_proof}, indent=2
            )
            + "\n"
        )
    years = sorted(set(legs) | set(kept))
    return regenerate_diagnostics(out, args.iso.upper(), years)


if __name__ == "__main__":
    raise SystemExit(main())
