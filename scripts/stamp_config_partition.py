"""Derive and stamp a COMPOSITE bundle's per-year recipe map (ercot-260).

A composite calibration bundle spans years that solved under DIFFERENT
configurations — ERCOT is the standing case (owner ruling 2026-08-26, the
two-config keeper: ``keepers/ERCOT.json`` ``config_partition``, a FORWARD
config for 2024-2025 and a CARVE-OUT for 2021-2023). Its ``meta.json`` can
record only ONE of them, and it records the forward one, so the carve-out
keys — ``ercot_offer_swcap_clip=true`` and the x33.0 ``offer_curve_by_group``
peak bands — appeared in no ``meta.json`` at all and had no CLI flag. A
``--replay-bundle`` of that keeper therefore solved the FORWARD config on a
carve-out year and reported the result as the keeper's
(``docs/RESULT-ercot259-drag-merit-allocation-2026-09-09.md`` §4: the control
replayed 2023 and solved ``swcap=False`` / CC_REGULAR ``peak=4.576``, C3a
-39.6 %, against the keeper's own ``peak=151.008`` and C3a -7.3 %). That is
the defect ``RESULT-ercot256`` §10 named and left open, and it blocked any
ERCOT full-span re-solve by any lane.

This is the WRITER half of the fix; ``replay_keeper.config_partition_overlay``
and ``enforce_single_recipe_partition`` are the consumer half. It writes
``meta.json[config_partition_overrides]``: per solved year, the EXACT extra
``ScenarioConfig`` keys that year carried on top of the meta recipe.

**The map is DERIVED, never hand-typed.** Each leg's own committed
``run_config*.json`` records the resolved ``scenario_config`` it solved, so
the overlay for a leg is that dump diffed against the bundle's base
``run_config.json`` — the one whose config ``meta.json`` matches. Nothing is
transcribed by hand and nothing is fitted: the source of every value is a
committed artifact of the solve it describes. ``--check`` re-derives and
compares without writing, so CI or a later session can prove a stamped block
still reproduces from the artifacts under it.

YEAR-DRIVEN fields are excluded (:data:`YEAR_DRIVEN_FIELDS`): they differ
between legs because the legs cover different YEARS, not because the recipe
differs, so replaying them would pin a year's inputs onto another year.

Usage::

    # derive from the bundle's own run_config*.json legs and stamp meta.json
    python scripts/stamp_config_partition.py results/calibration/<bundle> \\
        --leg 2021,2022=run_config_carveout_2021_2022.json \\
        --leg 2023=run_config_carveout_2023.json \\
        --leg 2024,2025=run_config_forward_2024_2025.json

    # verify a stamped block still re-derives from those same artifacts
    python scripts/stamp_config_partition.py results/calibration/<bundle> \\
        --leg ... --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.replay_keeper import (  # noqa: E402
    CONFIG_PARTITION_KEY,
    CONFIG_PARTITION_SCHEMA,
)

#: ``scenario_config`` fields that differ between legs because the legs cover
#: different YEARS, not because the recipe differs. They are a pure function of
#: the solve year and are re-derived by every solve, so recording them as a
#: recipe overlay would pin one year's inputs onto another year's replay.
#:
#: * ``weather_year`` — pinned to the solve year in backcast mode.
#: * ``gas_price_override`` — that year's measured Henry Hub actual.
#: * ``ordc_voll`` / ``ordc_mcl_mw`` — ERCOT's OWN PUBLISHED ORDC parameters by
#:   year (VOLL fell $9,000 -> $5,000 and MCL rose 2,000 -> 3,000 MW after
#:   2021). ``RESULT-ercot256`` §8a measured this directly: neither is present
#:   in any ``meta.json``, and the ``run_config`` difference that "looked like
#:   config drift" is the published year parameter, not a recipe choice.
YEAR_DRIVEN_FIELDS = frozenset(
    {
        "weather_year",
        "gas_price_override",
        "ordc_voll",
        "ordc_mcl_mw",
    }
)


def parse_leg(spec: str) -> tuple[list[int], str]:
    """Parse a ``YEARS=run_config_file`` leg spec into ``([years], filename)``."""
    years_part, _, filename = spec.partition("=")
    if not years_part or not filename:
        raise SystemExit(f"--leg expects YEARS=run_config_file, got {spec!r}")
    try:
        years = [int(y) for y in years_part.split(",") if y.strip()]
    except ValueError as exc:
        raise SystemExit(f"--leg {spec!r}: bad year list ({exc})") from exc
    if not years:
        raise SystemExit(f"--leg {spec!r}: no years")
    return years, filename


def _scenario_config(path: Path) -> dict:
    """The resolved ``scenario_config`` dump a run_config file records."""
    if not path.exists():
        raise SystemExit(f"missing run_config file: {path}")
    sc = (json.loads(path.read_text()) or {}).get("scenario_config")
    if not isinstance(sc, dict):
        raise SystemExit(f"{path} has no scenario_config block")
    return sc


def derive_overlay(base: dict, leg: dict) -> dict:
    """The recipe keys a leg carries on top of ``base``, year-driven excluded.

    Both arguments are resolved ``scenario_config`` dumps, so this is the whole
    difference between what the leg solved and what the bundle's base recipe
    solves — with no interpretation beyond dropping
    :data:`YEAR_DRIVEN_FIELDS`.
    """
    keys = (set(base) | set(leg)) - YEAR_DRIVEN_FIELDS
    return {k: leg[k] for k in sorted(keys) if k in leg and base.get(k) != leg[k]}


def build_block(
    bundle: Path, legs: list[tuple[list[int], str]], base_name: str
) -> dict:
    """Derive the full ``config_partition_overrides`` block for a bundle."""
    base = _scenario_config(bundle / base_name)
    block: dict = {
        "_schema": CONFIG_PARTITION_SCHEMA,
        "_why": (
            "meta.json carries ONE config (for a composite bundle, the base "
            f"recipe recorded in {base_name}). These are the EXACT extra "
            "ScenarioConfig keys each other year solved under, DERIVED by "
            "diffing that year's own committed run_config scenario_config "
            "against the base — never hand-typed. Year-driven fields "
            f"({', '.join(sorted(YEAR_DRIVEN_FIELDS))}) are excluded: they "
            "differ because the legs cover different YEARS, not because the "
            "recipe differs. Consumed by "
            "replay_keeper.enforce_single_recipe_partition; re-derivable with "
            "scripts/stamp_config_partition.py --check."
        ),
    }
    for years, filename in legs:
        overlay = derive_overlay(base, _scenario_config(bundle / filename))
        if not overlay:
            continue  # the leg IS the base recipe; absence means exactly that
        for year in years:
            block[str(year)] = dict(overlay)
    return block


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bundle", type=Path, help="composite bundle directory")
    ap.add_argument(
        "--leg",
        action="append",
        default=[],
        metavar="YEARS=run_config_file",
        help="one solve leg: the years it covered and the run_config file in "
        "the bundle recording the scenario_config it solved (repeatable)",
    )
    ap.add_argument(
        "--base",
        default="run_config.json",
        help="the run_config whose config meta.json records (default: run_config.json)",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="re-derive and compare against the stamped block; write nothing "
        "and exit non-zero on any difference",
    )
    args = ap.parse_args()

    if not args.leg:
        raise SystemExit("at least one --leg YEARS=run_config_file is required")
    bundle = args.bundle
    meta_path = bundle / "meta.json"
    if not meta_path.exists():
        raise SystemExit(f"missing {meta_path}")
    meta = json.loads(meta_path.read_text())

    legs = [parse_leg(spec) for spec in args.leg]
    covered = [y for years, _ in legs for y in years]
    if len(covered) != len(set(covered)):
        raise SystemExit(f"--leg year lists overlap: {sorted(covered)}")
    bundle_years = {int(y) for y in meta.get("years") or []}
    missing = bundle_years - set(covered)
    if missing:
        raise SystemExit(
            f"legs do not cover every solved year: {sorted(missing)} unassigned. "
            "A composite's map must say what EVERY year solved under, or a "
            "replay of the uncovered year silently falls back to the base "
            "recipe — the defect this block closes."
        )
    extra = set(covered) - bundle_years
    if extra:
        raise SystemExit(f"--leg names years the bundle never solved: {sorted(extra)}")

    derived = build_block(bundle, legs, args.base)
    per_year = {k: v for k, v in derived.items() if not k.startswith("_")}

    if args.check:
        stamped = meta.get(CONFIG_PARTITION_KEY) or {}
        stamped_py = {k: v for k, v in stamped.items() if not k.startswith("_")}
        base = _scenario_config(bundle / args.base)
        # EFFECTIVE-CONFIG equivalence, not raw dict equality. What the block
        # promises is the config each year replays under, so the test is
        # whether stamped and derived RESOLVE the same — a stamped key whose
        # value already equals the base is a redundant pin, not drift (the
        # ercot-256 hand-typed block pins ercot_zonal_spread_ep_referenced=True
        # for 2021/2022, which is the base value; the derivation omits it as
        # the no-op it is). Raw equality would fail on that and say nothing
        # true. A key that resolves DIFFERENTLY is real drift and still fails.
        years = sorted(set(stamped_py) | set(per_year), key=int)
        mismatched = [
            y
            for y in years
            if {**base, **stamped_py.get(y, {})} != {**base, **per_year.get(y, {})}
        ]
        if not mismatched:
            redundant = {
                y: sorted(set(stamped_py.get(y, {})) - set(per_year.get(y, {})))
                for y in years
                if set(stamped_py.get(y, {})) - set(per_year.get(y, {}))
            }
            print(
                f"OK: {CONFIG_PARTITION_KEY} re-derives from the committed "
                f"run_config legs — every year resolves identically "
                f"({len(per_year)} overlaid year(s): "
                f"{', '.join(sorted(per_year)) or 'none'})"
            )
            for year, keys in sorted(redundant.items()):
                print(
                    f"  note: {year} pins {', '.join(keys)} at the base value "
                    "(redundant, behaviour-identical)"
                )
            return
        detail = []
        for y in mismatched:
            st, dv = stamped_py.get(y, {}), per_year.get(y, {})
            keys = sorted(
                k
                for k in set(st) | set(dv)
                if {**base, **st}.get(k) != {**base, **dv}.get(k)
            )
            detail.append(f"{y} on {', '.join(keys)}")
        raise SystemExit(
            f"{CONFIG_PARTITION_KEY} does NOT re-derive from the committed "
            "run_config legs — these years would REPLAY UNDER A DIFFERENT "
            "CONFIG than their own run_config records: " + "; ".join(detail)
        )

    meta[CONFIG_PARTITION_KEY] = derived
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(f"stamped {CONFIG_PARTITION_KEY} into {meta_path}")
    for year in sorted(per_year):
        print(f"  {year}: {', '.join(sorted(per_year[year]))}")


if __name__ == "__main__":
    main()
