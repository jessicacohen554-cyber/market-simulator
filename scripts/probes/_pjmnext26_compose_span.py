"""PJM-NEXT-26, zero LP: compose the seven year-isolated legs into ONE span bundle.

A copy of closeout-B's generic W0 composer (``_w0_compose_span.py`` at
``fca1454d``), because PJM-NEXT-26 solves the PJM-NEXT-25 data arm (appended
COAL rows in ``thermal_tranches_PJM.csv``) at the W0 posture: each leg is
``pjmnext16_A_span`` replayed with the ten W0 fields armed
(docs/records/pjm/ADDENDUM-pjm-next-26-w0-posture-2026-10-02.md). The arm is
data only, so the recipe check is unchanged from the W0 one:

1. **recipe** — each leg's recorded ``scenario_config`` equals the incumbent
   keeper's recorded config for that year on every field except the W0 fields,
   which must read their W0 posture (rule-26 deleted knobs tolerated only when
   off on both sides, which covers the retired ``nyiso_firm_imports``).
2. **one run** — every leg records the same ``solve_surface`` fingerprint and
   the pinned source sha (``--pinned-sha``).
3. **complete** — every leg carries ``dispatch/<y>_P1.parquet`` and
   ``hourly/unit_marginal_<y>.parquet``.

Usage::

    python scripts/probes/_pjmnext26_compose_span.py --iso PJM \\
        --keeper results/calibration/pjmnext16_A_span \\
        --leg 2019=results/calibration/pjm_next_26_2019 ... \\
        --pinned-sha <40-char sha> --out results/calibration/pjm_next_26_span
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
DENOMINATOR = "unit_outage_dispatched_bin_denominator"
#: Alternative denominators the dispatched-bin companion yields to (PRECOMMIT §2.1).
ALTERNATIVE_DENOMINATORS = (
    "unit_outage_extract_basis_share",
    "unit_outage_coal_extract_basis_share",
    "unit_outage_lp_capacity_basis",
)
#: Provenance keys a re-solve writes fresh; never a recipe difference.
PROVENANCE = {"note", "timestamp", "git_sha", "basis_sha"}
#: Fields a single-config keeper records for its first year only.
YEAR_INDEXED = {"weather_year", "gas_price_override"}


def _w0_fields() -> tuple[str, ...]:
    from market_sim.config import scenarios

    return tuple(scenarios._W0_BACKCAST_DEFAULT_FIELDS)


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


def expected_w0(keeper_sc: dict) -> dict[str, bool]:
    """The W0 posture a leg must record, given the keeper's own recipe."""
    want = {f: True for f in _w0_fields()}
    if any(keeper_sc.get(k) for k in ALTERNATIVE_DENOMINATORS):
        want[DENOMINATOR] = False
    elif keeper_sc.get(DENOMINATOR):
        want[DENOMINATOR] = True
    return want


def check_legs(
    keeper: Path, legs: dict[int, Path], pinned_sha: dict[int, str]
) -> list[str]:
    """Assert each leg is the keeper's recipe plus W0; return the report lines."""
    report: list[str] = []
    w0 = set(_w0_fields())
    surfaces: set = set()
    shas: set = set()
    for year, leg in sorted(legs.items()):
        cfg = _json(leg / "run_config.json")
        sc = cfg.get("scenario_config", {})
        ksc = _keeper_config(keeper, year).get("scenario_config", {})
        want = expected_w0(ksc)
        for field, value in want.items():
            if bool(sc.get(field)) is not value:
                raise SystemExit(
                    f"ABORT {leg.name}: {field}={sc.get(field)!r}, W0 posture wants {value}"
                )
        # A field registered after the keeper was solved is absent from its
        # recorded config; the replay resolves it to the registered default,
        # which is the keeper's behaviour by construction (no difference).
        defaults = _registered_defaults()
        diffs = sorted(
            k
            for k in (set(sc) | set(ksc)) - w0 - PROVENANCE
            if json.dumps(sc.get(k), sort_keys=True)
            != json.dumps(ksc[k] if k in ksc else defaults.get(k), sort_keys=True)
        )
        if not (keeper / f"run_config_{year}.json").is_file():
            # The keeper recorded ONE config (its first year's); the replay
            # re-derives the year-indexed pair per year from the keeper's meta.
            if sc.get("weather_year") != year:
                raise SystemExit(
                    f"ABORT {leg.name}: weather_year {sc.get('weather_year')} != {year}"
                )
            diffs = [k for k in diffs if k not in YEAR_INDEXED]
            report.append(
                f"  {year}: year-indexed from the replay: weather_year={year}, "
                f"gas_price_override={sc.get('gas_price_override')}"
            )
        # A knob deleted from ScenarioConfig (rule 26) after the keeper or a
        # kept leg was solved is inert only if both carried it off. An armed
        # deleted knob is a real recipe difference.
        deleted = [
            k
            for k in diffs
            if k not in defaults
            and sc.get(k) in (False, None, 0)
            and ksc.get(k) in (False, None, 0)
        ]
        if deleted:
            report.append(
                f"  {year}: deleted knobs, off in the keeper (rule 26): {deleted}"
            )
            diffs = [k for k in diffs if k not in deleted]
        if diffs:
            detail = "; ".join(f"{k}: {ksc.get(k)!r} -> {sc.get(k)!r}" for k in diffs)
            raise SystemExit(
                f"ABORT {leg.name}: recipe differs from {keeper.name} {year} beyond "
                f"the W0 fields: {detail}"
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
        surfaces.add((cfg.get("solve_surface") or {}).get("fingerprint"))
        shas.add(meta.get("git_sha") or cfg.get("git_sha"))
        report.append(
            f"  {year} {leg.name}: recipe = {keeper.name} + W0 "
            f"({DENOMINATOR}={want[DENOMINATOR]})"
        )
    if len(surfaces) != 1:
        raise SystemExit(
            f"ABORT: legs disagree on solve_surface fingerprint: {surfaces}"
        )
    for year, leg in sorted(legs.items()):
        pin = pinned_sha.get(year)
        if not pin:
            continue
        got = str(_json(leg / "meta.json").get("git_sha") or "")
        if not got or not pin.startswith(got):
            raise SystemExit(f"ABORT {leg.name}: source sha {got!r} != pinned {pin}")
    report.append(f"  solve_surface fingerprint shared: {next(iter(surfaces))}")
    report.append(f"  source sha(s): {sorted(map(str, shas))}")
    return report


def compose(legs: dict[int, Path], out: Path, keeper: Path) -> None:
    """Copy per-year files, concatenate root frames, write meta/run_config."""
    if out.exists():
        raise SystemExit(f"ABORT: {out} exists; refusing to overwrite (rule 31)")
    for sub in ("dispatch", "floors", "hourly"):
        (out / sub).mkdir(parents=True)
    frames: dict[str, list[pd.DataFrame]] = {n: [] for n in ROOT_FRAMES}
    for year, leg in sorted(legs.items()):
        for sub in ("dispatch", "floors", "hourly"):
            for path in sorted((leg / sub).glob("*")):
                if str(year) not in path.name:
                    raise SystemExit(f"ABORT: {path} carries no year {year}")
                shutil.copy2(path, out / sub / path.name)
        for fname in ROOT_FRAMES:
            path = leg / fname
            if path.is_file():
                df = pd.read_parquet(path)
                if "year" not in df.columns:
                    df = df.assign(year=year)
                frames[fname].append(df)
        per = leg / f"run_config_{year}.json"
        shutil.copy2(
            per if per.is_file() else leg / "run_config.json",
            out / f"run_config_{year}.json",
        )
        for extra in (f"fleet_census_{year}.json",):
            if (leg / extra).is_file():
                shutil.copy2(leg / extra, out / extra)
    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
    # The base run_config follows the keeper's own base year (its weather_year,
    # when a leg carries it): a different base year reads as an armed change
    # on any year-indexed shared field (check_mechanism_matrix shared ratchet).
    kyear = (
        _json(keeper / "run_config.json").get("scenario_config", {}).get("weather_year")
    )
    first = kyear if kyear in legs else min(legs)
    # The base run_config is WIDENED to the span (miso-267): copied verbatim it
    # would record the first leg's one-year `calibration_flags.years` and gas.
    base_cfg = _json(legs[first] / "run_config.json")
    flags = base_cfg.setdefault("calibration_flags", {})
    flags["years"] = sorted(legs)
    gas: dict = {}
    for leg in legs.values():
        cfg = _json(leg / "run_config.json")
        gas.update(cfg.get("calibration_flags", {}).get("gas_prices") or {})
    if gas:
        flags["gas_prices"] = {k: gas[k] for k in sorted(gas)}
    (out / "run_config.json").write_text(json.dumps(base_cfg, indent=2) + "\n")
    if (legs[first] / "solve_surface.json").is_file():
        shutil.copy2(legs[first] / "solve_surface.json", out / "solve_surface.json")
    meta = _json(legs[first] / "meta.json")
    meta["years"] = sorted(legs)
    meta["composed_from"] = {legs[y].name: [y] for y in sorted(legs)}
    if gas:
        meta["gas_prices"] = {k: gas[k] for k in sorted(gas)}
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    _respan_shared_inputs(meta, out)
    # The base meta is ONE leg's recipe (the keeper's base year). Legs that
    # solved a different recipe (a partitioned keeper such as ERCOT's
    # forward / carve-out / validation configs) must be recorded as a
    # per-year overlay or replay_keeper solves the base recipe for them —
    # the W0 phase-3 w0_ercot_span defect. Derived from each year's own
    # run_config, never hand-typed; a single-recipe span gets no block.
    from scripts.replay_keeper import CONFIG_PARTITION_KEY
    from scripts.stamp_config_partition import build_block

    block = build_block(
        out, [([y], f"run_config_{y}.json") for y in sorted(legs)], "run_config.json"
    )
    meta.pop(CONFIG_PARTITION_KEY, None)
    if any(not k.startswith("_") for k in block):
        meta[CONFIG_PARTITION_KEY] = block
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"composed {out.relative_to(REPO)}: {n} files, years {sorted(legs)}")


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
    ap.add_argument(
        "--keeper",
        action="append",
        required=True,
        help="incumbent bundle; repeat as YEARS=bundle for a split keeper",
    )
    ap.add_argument("--leg", action="append", required=True, metavar="YEAR=BUNDLE")
    ap.add_argument(
        "--pinned-sha",
        action="append",
        default=[],
        help="SHA for every leg, or YEAR=SHA per leg (repeat)",
    )
    ap.add_argument(
        "--inert-proof",
        help="zero-LP byte-inert proof; required when legs pin to more than one sha",
    )
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args(argv)
    legs = {int(y): _resolve(b) for y, _, b in (s.partition("=") for s in args.leg)}
    pins: dict[int, str] = {}
    for spec in args.pinned_sha:
        y, sep, sha = spec.partition("=")
        if sep:
            pins[int(y)] = sha
        else:
            pins.update({yy: spec for yy in legs if yy not in pins})
    mixed = len(set(pins.values())) > 1
    if mixed and not args.inert_proof:
        raise SystemExit(
            "ABORT: legs pin to more than one sha; --inert-proof is required"
        )
    keepers: dict[int, Path] = {}
    for spec in args.keeper:
        ys, sep, b = spec.partition("=")
        if sep:
            for y in ys.split(","):
                keepers[int(y)] = _resolve(b)
        else:
            keepers.update({y: _resolve(ys) for y in legs if y not in keepers})
    lines: list[str] = []
    for kb in sorted(set(keepers.values())):
        lines += check_legs(kb, {y: legs[y] for y in legs if keepers[y] == kb}, pins)
    print("recipe check:\n" + "\n".join(lines))
    if args.check_only:
        return 0
    if not args.out:
        raise SystemExit("--out is required unless --check-only")
    out = _resolve(args.out)
    compose(legs, out, keepers[min(legs)])
    if mixed:
        meta_path = out / "meta.json"
        meta = _json(meta_path)
        meta["mixed_solve_sha"] = {
            "per_year": {str(y): pins[y] for y in sorted(pins)},
            "inert_proof": args.inert_proof,
        }
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return regenerate_diagnostics(out, args.iso.upper(), sorted(legs))


if __name__ == "__main__":
    raise SystemExit(main())
