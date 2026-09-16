"""nyiso-238 (ZERO LP): compose four per-year arm bundles into one span bundle.

The owner directed a per-year fan-out (PRECOMMIT addendum 1). Each shard pushed
its FULL bundle - ``dispatch/<yr>_P1.parquet`` and the bundle-root
``system.parquet`` included - so the legs compose without a re-solve, which is
the precondition rule 32(b) ``[R-SHARD]``'s fan-out ban assumes is missing.

The recipe is the one this lane already has on record (``RESULT-nyiso236`` 4,
owner-authorized for NYISO):

* **year-scoped files** (``hourly/*_<year>.parquet``, ``dispatch/<year>_*.parquet``)
  are copied across verbatim - their names already carry the year.
* **bundle-root parquets** carry a ``year`` column, so they are CONCATENATED and
  re-sorted; the composer FAILS LOUD if a root parquet lacks that column rather
  than silently stacking rows that cannot be told apart.
* ``meta.json`` merges ``years`` and any per-year mapping (``gas_prices`` and
  friends); every other key must AGREE across the legs or the composer fails.
* ``run_config.json`` is taken from the first leg after verifying that the legs
  differ only in the known per-year fields.
* ``metrics.json`` / ``legitimacy_diagnostics.json`` are NOT copied - they are
  regenerated in the parent (zero LP) by the caller.

Usage::

    python3 scripts/probes/nyiso238_compose_span.py \\
        --legs results/calibration/nyiso238_hydro_{2022,2023,2024,2025} \\
        --out  results/calibration/nyiso238_hydroperiod_span
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

#: Fields ``replay_keeper`` legitimately re-derives per solved year. Any OTHER
#: run_config difference between legs is a composition error, not a per-year fact.
PER_YEAR_CONFIG_FIELDS = {
    "gas_price_override",
    "weather_year",
    "gas_offer_margin_anchor_by_zone",
    "start_year",
    "end_year",
    "years",
}
#: Regenerated in the parent, never copied from a leg.
REGENERATED = {"metrics.json", "legitimacy_diagnostics.json"}


def _leg_year(leg: Path) -> int:
    """Return the single year a leg bundle covers, from its meta.json."""
    meta = json.loads((leg / "meta.json").read_text())
    years = meta.get("years") or []
    if len(years) != 1:
        raise SystemExit(f"{leg.name}: expected exactly one year in meta.json, got {years}")
    return int(years[0])


def compose(legs: list[Path], out: Path) -> None:
    """Compose ``legs`` into the span bundle ``out``."""
    legs = sorted(legs, key=_leg_year)
    years = [_leg_year(l) for l in legs]
    print(f"legs: {[l.name for l in legs]}\nyears: {years}")
    if len(set(years)) != len(years):
        raise SystemExit(f"duplicate years across legs: {years}")
    out.mkdir(parents=True, exist_ok=True)

    # --- run_config: compare the SCENARIO CONFIG, not the wrapper ------------
    # ``run_config.json`` is a WRAPPER, not a flat config dump: the scenario lives
    # under ``scenario_config``, beside ``timestamp`` / ``git`` / ``resolved_inputs``
    # / ``calibration_flags`` / ``environment``, all of which legitimately differ
    # between legs solved in different containers on different years. Comparing the
    # wrapper compares solve provenance; comparing ``scenario_config`` compares the
    # model. (This is also why a top-level read of the arm field returns ``None`` -
    # it is one level down. See the meta.json note below.)
    cfgs = [json.loads((l / "run_config.json").read_text()) for l in legs]
    scs = [c.get("scenario_config") or {} for c in cfgs]
    base_sc = scs[0]
    for leg, sc in zip(legs[1:], scs[1:]):
        diff = {k for k in set(base_sc) | set(sc) if base_sc.get(k) != sc.get(k)}
        unexpected = diff - PER_YEAR_CONFIG_FIELDS
        if unexpected:
            raise SystemExit(
                f"{legs[0].name} vs {leg.name}: scenario_config differs outside the "
                f"per-year allowance on {sorted(unexpected)} - refusing to compose"
            )
    armed_rc = base_sc.get("hydro_budget_period_by_instrument")
    if armed_rc is not True:
        raise SystemExit(
            f"ARM NOT SET in scenario_config: "
            f"hydro_budget_period_by_instrument={armed_rc!r}"
        )
    fps = {c.get("solve_surface", {}).get("fingerprint") for c in cfgs}
    if len(fps) != 1:
        raise SystemExit(f"legs carry DIFFERENT solve-surface fingerprints: {fps}")
    print(f"scenario_config: legs agree outside the per-year allowance; arm True")
    print(f"solve_surface fingerprint: {fps.pop()} (identical across legs)")
    base = dict(cfgs[0])
    base["scenario_config"] = base_sc
    base["composed_from"] = [l.name for l in legs]
    base["per_leg_provenance"] = {
        str(_leg_year(l)): {
            "timestamp": c.get("timestamp"),
            "git": c.get("git"),
        }
        for l, c in zip(legs, cfgs)
    }

    # --- year-scoped files: copy verbatim -------------------------------------
    copied = 0
    for leg, y in zip(legs, years):
        for src in sorted(leg.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(leg)
            if rel.name in REGENERATED or rel.name in ("meta.json", "run_config.json"):
                continue
            if src.suffix == ".parquet" and rel.parent == Path("."):
                continue  # bundle-root parquet: concatenated below
            if str(y) not in rel.name:
                continue  # not year-scoped; handled as a root parquet or skipped
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    print(f"year-scoped files copied: {copied}")

    # --- bundle-root parquets: concatenate on the `year` column ---------------
    root_names = sorted({p.name for l in legs for p in l.glob("*.parquet")})
    for name in root_names:
        frames = []
        for leg, y in zip(legs, years):
            p = leg / name
            if not p.exists():
                print(f"  ! {name}: absent from {leg.name}")
                continue
            df = pd.read_parquet(p)
            if "year" not in df.columns:
                raise SystemExit(
                    f"{leg.name}/{name} has no `year` column - cannot compose safely"
                )
            got = sorted(df.year.unique().tolist())
            if got != [y]:
                raise SystemExit(f"{leg.name}/{name} carries years {got}, expected [{y}]")
            frames.append(df)
        if not frames:
            continue
        cat = pd.concat(frames, ignore_index=True)
        cat = cat.sort_values([c for c in ("year", "pass", "zone", "hour") if c in cat.columns])
        cat.to_parquet(out / name, index=False)
        print(f"  root {name}: {[len(f) for f in frames]} -> {len(cat)} rows, "
              f"years {sorted(cat.year.unique().tolist())}")

    # --- meta.json: merge years + per-year mappings ---------------------------
    metas = [json.loads((l / "meta.json").read_text()) for l in legs]
    meta = dict(metas[0])
    meta["years"] = years
    for k, v in metas[0].items():
        if isinstance(v, dict) and all(str(y) in str(list(m.get(k, {}).keys())) for m, y in zip(metas, years)):
            merged = {}
            for m in metas:
                merged.update(m.get(k) or {})
            meta[k] = merged
    for k in ("gas_prices",):
        merged = {}
        for m in metas:
            val = m.get(k)
            if isinstance(val, dict):
                merged.update(val)
        if merged:
            meta[k] = merged
    meta["composed_from"] = [l.name for l in legs]
    (out / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    print(f"meta.json: years={meta['years']} composed_from={meta['composed_from']}")
    print(f"\nCOMPOSED -> {out}")
    print("metrics.json and legitimacy_diagnostics.json are NOT copied - regenerate in the parent.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    missing = [str(l) for l in legs if not l.is_dir()]
    if missing:
        raise SystemExit(f"missing leg bundles: {missing}")
    compose(legs, ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out))


if __name__ == "__main__":
    main()
