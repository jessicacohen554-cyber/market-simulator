#!/usr/bin/env python3
"""R-MISO copy of _miso268_compose_span.py (adds the F1 backcast defaults and the two
outage arms to MUST_AGREE, so a leg on which any silently no-opped cannot compose in;
seven legs, 2019-2025, AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24 §5.3.3).

miso-268 header (inherited): copy of _miso266_compose_span.py (adds coal_fuel_inventory_plant_grain to MUST_AGREE).

Compose miso-268's SIX PER-YEAR LEGS into ONE registrable MISO span bundle.

Adapted verbatim from ``_miso260_compose_span.py`` (same frames, same
PARTITIONED check, same zero-LP regeneration of ``legitimacy_diagnostics.json``
over the whole composite), with ONE addition:
``unit_outage_dispatched_bin_denominator`` joins ``MUST_AGREE``, so a leg whose
``--set`` silently no-opped cannot compose in as if it had armed. Run it TWICE,
once over the six control legs and once over the six arm legs.

Under rule 36 ``[R-YEAR-ISOLATION]`` each leg is its own single-year shard, so
there are six legs rather than two — the composer already takes any number.

The inherited miso-260 header follows, and its partition reasoning still
governs: the 2023 partition is FORCED BY DATA and both composites carry it.

---

Compose miso-260's TWO PARTITION LEGS into ONE registrable MISO span bundle.

MISO's keeper is **two configs, partitioned at 2023, and the partition is FORCED
BY DATA** — measured 2026-09-16 from the miso-259 per-year bundles' own recorded
``run_config.json``:

    miso_measured_reserve_requirements   2020/21/22 False | 2023/24/25 True
    miso_reserve_online_gated            2020/21/22 False | 2023/24/25 True

and ``market_sim.data.miso_reserve_requirements.load_miso_reserve_requirements``
**hard-errors** for 2020, 2021 and 2022 (the measured cleared-reserve parquet
starts in 2023). So a single ``--years 2020..2025`` invocation is impossible for
MISO, not merely inadvisable: ``solve_and_persist`` carries ONE config per call
and this one would raise on its first year. TWO legs is the minimum, and two is
what this composes.

That also means the previous composite's base ``run_config.json`` — copied from
its FIRST year by ``_miso259_compose_span.py`` — records the VALIDATION leg's
flags for the whole span. The per-year ``run_config_<y>.json`` files carry the
truth, and ``scripts/stamp_config_partition.py`` is what records it; this script
therefore refuses to finish until the partition is stamped and ``--check`` clean.

The composition itself is mechanical and lossless:

* per-year files COPY (``dispatch/<y>_P1*.parquet``, ``floors/<y>_P1.npz``,
  ``hourly/*_<y>.parquet`` — all already year-stamped);
* bundle-root frames CONCATENATE (``system`` / ``btm`` / ``flows`` / ``storage``),
  with a ``year`` column added where the leg's frame lacks one;
* ``run_config_<y>.json`` is kept per year;
* **``legitimacy_diagnostics.json`` is REGENERATED over the composite**, never
  copied from a leg. Copying one leg's is the trap that silently sends C8 to
  SKIPPED — an unscored PROTECTIVE criterion, which downgrades the determination
  and reads exactly like a model regression. Regeneration is zero-LP (it reads
  the bundle's own dispatch and floors) and is strictly better than merging
  year-stamped lists by hand.

Every leg's config is CHECKED before anything is written: the fields that MUST
agree across the whole span agree, and the two that MUST differ differ in the
declared direction.

Usage:
    python scripts/probes/_miso266_compose_span.py \
        --leg 2020=miso266_arm_2020 --leg 2021=miso266_arm_2021 \
        --leg 2022=miso266_arm_2022 --leg 2023=miso266_arm_2023 \
        --leg 2024=miso266_arm_2024 --leg 2025=miso266_arm_2025 \
        --out results/calibration/miso266_arm_span
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
sys.path.insert(0, str(REPO))
CAL = REPO / "results" / "calibration"

ROOT_FRAMES = ("system.parquet", "btm.parquet", "flows.parquet", "storage.parquet")

#: Fields every year of the span must agree on. A disagreement here means the
#: legs are not one run and the composite would be a fiction.
MUST_AGREE = (
    "mode",
    "coal_fuel_inventory",
    "miso_seam_measured_ladder",
    "reference_price_interface",
    "miso_firm_imports",
    "miso_manitoba_seam",
    "miso_south_seam_split",
    "miso_import_sil_measured_envelope",
    "use_campd_bins",
    # miso-264: the gas-offer margin's IDENTIFICATION-POINT INDEX. The resolved
    # anchor `gas_offer_margin_anchor` is deliberately NOT here — under the
    # vintage gate it is a per-year measured value and differing IS the
    # mechanism — but the GATE itself must agree across every leg, or a leg
    # whose `--set` silently no-opped would compose in as if it had armed.
    "gas_offer_margin_anchor_vintage",
    # miso-266: the DISPATCHED-bin derate denominator. Every year of a composite
    # must carry the SAME value or the composite is not one run — and, as with
    # the anchor gate above, a leg whose `--set` silently no-opped would
    # otherwise compose in as if it had armed. The A/B's two composites
    # (control and arm) each check this independently; the check is that the
    # SIX YEARS agree, not that they carry any particular value.
    "unit_outage_dispatched_bin_denominator",
    # miso-267: the hydro-5 keeper's single delta. A leg re-solved on that keeper
    # must carry it in every year, or the composite silently reverts it.
    "hydro_ror_split",
    # miso-268: the per-coal-yard grain of coal_fuel_inventory.
    "coal_fuel_inventory_plant_grain",
    # R-MISO: F1's backcast defaults (owner instruction 2026-09-24) and the two
    # outage arms. Every year must carry them, or the composite is not one run.
    "eia860_vintage_tracks_solve_year",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
    "unit_outage_short_windows",
    "unit_outage_short_windows_gas",
    "unit_partial_outage_windows",
    "unit_outage_maxgen_events",
    # R-MISO arm B (PRECOMMIT §9): the SPP-48 mid-vintage-year exit carry.
    "mid_vintage_exit_carry",
)

#: Fields the DATA forces to differ, with the value each leg must carry. Stated
#: here so a silent flip is caught rather than composed.
PARTITIONED = {
    "miso_measured_reserve_requirements": {"validation": False, "train": True},
    "miso_reserve_online_gated": {"validation": False, "train": True},
}


def _leg_config(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())


def check_recipes(legs: dict[str, list[int]]) -> None:
    """Verify the legs agree where they must and differ where the data forces it."""
    print("verifying the two leg recipes:")
    agree: dict[str, set] = {k: set() for k in MUST_AGREE}
    agree["_surface"] = set()
    for name, years in legs.items():
        cfg = _leg_config(CAL / name)
        sc = cfg["scenario_config"]
        tier = "train" if min(years) >= 2023 else "validation"
        for k in MUST_AGREE:
            agree[k].add(json.dumps(sc.get(k)))
        agree["_surface"].add((cfg.get("solve_surface") or {}).get("fingerprint"))
        print(
            f"  {name:22s} years={years} tier={tier} "
            f"seam_ladder={sc.get('miso_seam_measured_ladder')} "
            f"coal_inv={sc.get('coal_fuel_inventory')} mode={sc.get('mode')} "
            f"surface={(cfg.get('solve_surface') or {}).get('fingerprint')}"
        )
        for field, want in PARTITIONED.items():
            got = sc.get(field)
            if got != want[tier]:
                raise SystemExit(
                    f"ABORT: {name} ({tier} tier) has {field}={got!r}, "
                    f"expected {want[tier]!r}. The keeper's data-forced partition "
                    "is not reproduced, so this is not the keeper's recipe."
                )
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded and recorded != sorted(years):
            raise SystemExit(
                f"ABORT: {name} records years {recorded}, the leg claims {sorted(years)}"
            )
    for key, values in agree.items():
        if len(values) != 1:
            raise SystemExit(
                f"ABORT: the legs disagree on {key!r}: {sorted(map(str, values))}. "
                "Only the two data-forced reserve fields may differ across the "
                "partition; anything else means these are not one run."
            )
    print(f"  OK — {len(MUST_AGREE)} shared fields agree, surface fingerprint shared,")
    print(
        f"       {len(PARTITIONED)} data-forced fields differ in the declared direction."
    )


def compose(legs: dict[str, list[int]], out: Path) -> None:
    check_recipes(legs)
    if out.exists():
        shutil.rmtree(out)
    for sub in ("dispatch", "floors", "hourly"):
        (out / sub).mkdir(parents=True)

    frames: dict[str, list[pd.DataFrame]] = {n: [] for n in ROOT_FRAMES}
    all_years: list[int] = []
    for name, years in legs.items():
        src = CAL / name
        all_years.extend(years)
        for sub in ("dispatch", "floors", "hourly"):
            for path in sorted((src / sub).glob("*")):
                if not any(str(y) in path.name for y in years):
                    raise SystemExit(f"ABORT: {path} carries no year of {years}")
                shutil.copy2(path, out / sub / path.name)
        for fname in ROOT_FRAMES:
            path = src / fname
            if not path.is_file():
                print(f"  {name}: {fname} absent, skipped")
                continue
            df = pd.read_parquet(path)
            if "year" not in df.columns:
                raise SystemExit(
                    f"ABORT: {path} has no `year` column and the leg spans "
                    f"{years} — the year cannot be inferred."
                )
            frames[fname].append(df)
        # Per-year run_config: a multi-year leg writes run_config_<y>.json itself;
        # fall back to stamping the leg's single recorded config onto its years.
        wrote_any = False
        for y in years:
            per = src / f"run_config_{y}.json"
            if per.is_file():
                shutil.copy2(per, out / f"run_config_{y}.json")
                wrote_any = True
        if not wrote_any:
            for y in years:
                shutil.copy2(src / "run_config.json", out / f"run_config_{y}.json")

    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
            print(f"  {fname}: {len(parts)} leg(s) concatenated")

    all_years = sorted(set(all_years))
    base = min(legs, key=lambda n: min(legs[n]))
    # miso-267: the base run_config echo is WIDENED to the span. Copied verbatim
    # it recorded the first leg's `calibration_flags.years` ([2020]) for a
    # six-year composite, which is what `audit_keepers` E3 warned on. The same
    # repair nwpp-42 made (`39c79724`) and `_hydro5_compose_span.py` carries.
    base_cfg = _leg_config(CAL / base)
    flags = base_cfg.setdefault("calibration_flags", {})
    flags["years"] = list(all_years)
    gas: dict[str, float] = {}
    for name in legs:
        gas.update(
            _leg_config(CAL / name).get("calibration_flags", {}).get("gas_prices") or {}
        )
    if gas:
        flags["gas_prices"] = {k: gas[k] for k in sorted(gas)}
    (out / "run_config.json").write_text(json.dumps(base_cfg, indent=2) + "\n")
    meta = json.loads((CAL / base / "meta.json").read_text())
    meta["years"] = all_years
    meta["composed_from"] = {n: sorted(y) for n, y in legs.items()}
    if gas:
        meta["gas_prices"] = {k: gas[k] for k in sorted(gas)}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _respan_shared_inputs(meta, out)
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"\ncomposed {out} — {n} files, years {all_years}")
    print(
        "  NOTE: run_config.json is the FIRST leg's (its `years` widened to the "
        "span) and therefore records the validation-tier reserve flags for the "
        "whole span. run_config_<y>.json carries the truth; "
        "stamp_config_partition.py records it."
    )


def _respan_shared_inputs(meta: dict, out: Path) -> None:
    """Re-point the year-dependent benchmark frames at the whole span (miso-267).

    ``eia930`` / ``eia923`` / ``campd`` are PER-YEAR frames (six distinct hashes
    over six single-year legs); the ``unit_outages*`` frames are shared. Copying
    the first leg's ``shared_inputs`` recorded 2020's one-year frames for a
    six-year composite, so ``--restore-shared-inputs`` rebuilt a six-year frame,
    compared it to a one-year hash and refused — whatever the builders were
    doing (``RESULT-miso266`` §5.1, Defect A). The frames are rebuilt over the
    composite's own ``meta.json`` recipe through the single builder and written
    content-addressed, exactly as ``_hydro5_compose_span.py`` does.
    """
    recorded = meta.get("shared_inputs")
    if not recorded:
        return
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


def regenerate_diagnostics(out: Path, years: list[int]) -> int:
    """Rebuild ``legitimacy_diagnostics.json`` over the WHOLE composite (zero LP)."""
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "legitimacy_diagnostics.py"),
        "--bundle",
        str(out),
        "--iso",
        "MISO",
        "--years",
        *[str(y) for y in years],
        "--json-out",
        str(out / "legitimacy_diagnostics.json"),
    ]
    print("\nregenerating legitimacy_diagnostics.json over the composite:")
    print("  " + " ".join(cmd))
    rc = subprocess.run(cmd, cwd=REPO).returncode
    # NOTE: legitimacy_diagnostics.py exits 1 whenever a GATE fails (D-1/D-2/D-4
    # carry standing MISO failures), so a nonzero exit is the normal case and
    # says nothing about whether the artifact was written. What matters is that
    # the artifact exists and spans every year — check that, not the status.
    art = out / "legitimacy_diagnostics.json"
    if not art.is_file():
        print(
            f"  NO ARTIFACT WRITTEN (exit {rc}) — C8 would score SKIPPED; do not register."
        )
        return 1
    if rc != 0:
        print(f"  (exit {rc} — a failing diagnostic gate, not a missing artifact)")
    d = json.loads(art.read_text())
    got = sorted(d.get("years") or [])
    print(f"  years in the regenerated artifact: {got}")
    if got != sorted(years):
        print(f"  MISMATCH: expected {sorted(years)} — do not register.")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--leg",
        action="append",
        required=True,
        help="YEARS=bundle_name, e.g. 2020,2021,2022=miso260_seam_v",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-diagnostics", action="store_true")
    args = ap.parse_args()

    legs: dict[str, list[int]] = {}
    for spec in args.leg:
        ys, _, name = spec.partition("=")
        legs[name] = sorted(int(y) for y in ys.split(","))
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    compose(legs, out)
    if args.skip_diagnostics:
        return 0
    return regenerate_diagnostics(out, sorted({y for ys in legs.values() for y in ys}))


if __name__ == "__main__":
    raise SystemExit(main())
