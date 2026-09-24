"""R-CAISO (ZERO LP): compose the per-year CAISO legs into one span bundle.

Adapted from ``scripts/probes/xiso8_compose_span.py`` (same ISO, same composition
rules). What differs: the ARM is the R-CAISO input-correction posture
(docs/handoffs/r-caiso/PRECOMMIT-r-caiso-2026-09-24.md §1), asserted field by field
on every leg, and ``eia860_vintage_year`` is allowed to differ per leg (the
year-matched vintage is per-year by construction).

Original xiso-8 docstring follows.

xiso-8 (ZERO LP): compose the four per-year CAISO legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` requires one shard per backcast year, and rule 34
``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its FULL bundle -- the
bundle-root parquets and ``dispatch/<yr>_P1.parquet`` included -- so the legs
compose here without a re-solve.

The recipe is ``scripts/probes/caiso287_compose_span.py``'s, reused rather than
reinvented because it was written for the same ISO and the same situation. What
differs is one assertion: these legs are an ARM, so every one of them must carry
``gas_flow_date_year_start_package=True``. A leg without it is the keeper's own
recipe and composing it would silently produce a "span" that is half control.

Composition rules, unchanged:

* **year-scoped files** (``hourly/*_<year>.parquet``, ``dispatch/<year>_*``) copy
  across verbatim -- their names already carry the year.
* **bundle-root parquets** carry a ``year`` column, so they CONCATENATE and
  re-sort; a root parquet without that column FAILS LOUD.
* ``meta.json`` merges ``years`` and the per-year maps; every other key must
  agree across legs.
* ``metrics.json`` / ``legitimacy_diagnostics.json`` are NOT copied -- they are
  regenerated in the parent, at zero LP, by the caller.

Usage::

    python3 scripts/probes/xiso8_compose_span.py \\
        --legs results/calibration/xiso8_leftedge_{2022,2023,2024,2025} \\
        --out  results/calibration/xiso8_leftedge_span
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

#: Fields ``replay_keeper`` legitimately re-derives per solved year. Any OTHER
#: scenario_config difference between legs is a composition error.
PER_YEAR_CONFIG_FIELDS = {
    "gas_price_override",
    "weather_year",
    "gas_offer_margin_anchor_by_zone",
    "start_year",
    "end_year",
    "years",
    "eia860_vintage_year",
}
#: Regenerated in the parent, never copied from a leg.
REGENERATED = {"metrics.json", "legitimacy_diagnostics.json"}

#: The CAISO keeper's posture. Asserted on EVERY leg -- these legs are a replay
#: of the keeper's own recipe, so any drift here means the leg is not the keeper.
KEEPER_POSTURE: dict[str, object] = {
    "caiso_ra_mustoffer": True,
    "caiso_ra_startup_bridge": True,
    "caiso_ra_bridge_decommit": True,
    "caiso_ra_bridge_startup_aware": True,
    "caiso_ra_startup_trajectory": True,
    "caiso_ra_min_load_frac": 0.26,
    "negative_renewable_offers": True,
    "renewable_keep_running_value": 20.0,
    "caiso_ra_mustoffer_quantity_gate": False,
    "caiso_ra_bridge_curtailment_release": False,
    "caiso_import_gas_coupling": True,
}

#: THE ARM. Every leg must carry it: a leg without it is the keeper's own recipe,
#: and composing one in would make the "span" half control (xiso-8).
ARM_FIELDS: dict[str, object] = {
    "gas_flow_date_year_start_package": True,
    "eia860_vintage_tracks_solve_year": True,
    "measured_ct_heat_rates": True,
    "measured_chp_heat_rates": True,
    "measured_st_heat_rates": True,
    "measured_cc_heat_rates": True,
    "egrid_family_heat_rates": True,
    "unit_outage_short_windows": True,
    "unit_outage_short_windows_gas": True,
    "unit_partial_outage_windows": True,
    "caiso_dam_outages": False,
    "mode": "backcast",
}


def _leg_year(leg: Path) -> int:
    meta = json.loads((leg / "meta.json").read_text())
    years = meta.get("years") or []
    if len(years) != 1:
        raise SystemExit(f"{leg.name}: expected exactly one year, got {years}")
    return int(years[0])


def _assert_mer(leg: Path, year: int) -> dict:
    """A leg with no live marginal_emission_rate defeats the whole promotion."""
    p = leg / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        raise SystemExit(f"{leg.name}: missing {p.name}")
    df = pd.read_parquet(p)
    if "marginal_emission_rate" not in df.columns:
        raise SystemExit(
            f"{leg.name}: NO marginal_emission_rate column. This leg was solved "
            "without the emissions dual and composing it would produce a span "
            "with no marginal-carbon data -- the one thing the promotion is for."
        )
    m = df["marginal_emission_rate"]
    if m.isna().all() or (m.fillna(0.0) == 0.0).all():
        raise SystemExit(f"{leg.name}: marginal_emission_rate is all-null/all-zero")
    return {"rows": int(len(df)), "nonzero": int((m.fillna(0.0) != 0.0).sum())}


def compose(legs: list[Path], out: Path) -> None:
    legs = sorted(legs, key=_leg_year)
    years = [_leg_year(l) for l in legs]
    print(f"legs : {[l.name for l in legs]}\nyears: {years}")
    if len(set(years)) != len(years):
        raise SystemExit(f"duplicate years across legs: {years}")
    out.mkdir(parents=True, exist_ok=True)

    cfgs = [json.loads((l / "run_config.json").read_text()) for l in legs]
    scs = [c.get("scenario_config") or {} for c in cfgs]

    # --- posture + MER, per leg, BEFORE anything is written ------------------
    for leg, sc, y in zip(legs, scs, years):
        drift = {
            k: (v, sc.get(k)) for k, v in KEEPER_POSTURE.items() if sc.get(k) != v
        }
        if drift:
            raise SystemExit(f"{leg.name}: posture drift (want, got) {drift}")
        arm_bad = {k: (v, sc.get(k)) for k, v in ARM_FIELDS.items() if sc.get(k) != v}
        if arm_bad:
            raise SystemExit(f"{leg.name}: R-CAISO arm posture wrong (want, got) {arm_bad}")
        cen = _assert_mer(leg, y)
        print(
            f"  {leg.name}: posture OK, R-CAISO arm OK, MER live "
            f"({cen['nonzero']}/{cen['rows']} nonzero)"
        )

    base_sc = scs[0]
    for leg, sc in zip(legs[1:], scs[1:]):
        diff = {k for k in set(base_sc) | set(sc) if base_sc.get(k) != sc.get(k)}
        unexpected = diff - PER_YEAR_CONFIG_FIELDS
        if unexpected:
            raise SystemExit(
                f"{legs[0].name} vs {leg.name}: scenario_config differs outside the "
                f"per-year allowance on {sorted(unexpected)} -- refusing to compose"
            )
    fps = {c.get("solve_surface", {}).get("fingerprint") for c in cfgs}
    if len(fps) != 1:
        raise SystemExit(f"legs carry DIFFERENT solve-surface fingerprints: {fps}")
    print(f"solve_surface fingerprint: {fps.pop()} (identical across legs)")

    base = dict(cfgs[0])
    base["scenario_config"] = base_sc
    base["composed_from"] = [l.name for l in legs]
    base["per_leg_provenance"] = {
        str(y): {"timestamp": c.get("timestamp"), "git": c.get("git")}
        for y, c in zip(years, cfgs)
    }
    cf = dict(base.get("calibration_flags") or {})
    if cf:
        cf["years"] = years
        leg_cfs = [c.get("calibration_flags") or {} for c in cfgs]
        for key, val in list(cf.items()):
            if isinstance(val, dict):
                merged: dict = {}
                for lc in leg_cfs:
                    lv = lc.get(key)
                    if isinstance(lv, dict):
                        merged.update(lv)
                if merged:
                    cf[key] = merged
        base["calibration_flags"] = cf
        print(f"calibration_flags: years -> {years}, per-year maps merged")
    (out / "run_config.json").write_text(json.dumps(base, indent=2, sort_keys=True))

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
                continue
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    print(f"year-scoped files copied: {copied}")

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
                    f"{leg.name}/{name} has no `year` column -- cannot compose safely"
                )
            got = sorted(df.year.unique().tolist())
            if got != [y]:
                raise SystemExit(f"{leg.name}/{name} carries years {got}, expected [{y}]")
            frames.append(df)
        if not frames:
            continue
        cat = pd.concat(frames, ignore_index=True)
        cat = cat.sort_values(
            [c for c in ("year", "pass", "zone", "hour") if c in cat.columns]
        )
        cat.to_parquet(out / name, index=False)
        print(
            f"  root {name}: {[len(f) for f in frames]} -> {len(cat)} rows, "
            f"years {sorted(cat.year.unique().tolist())}"
        )

    metas = [json.loads((l / "meta.json").read_text()) for l in legs]
    meta = dict(metas[0])
    meta["years"] = years
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
    print("metrics.json / legitimacy_diagnostics.json NOT copied -- regenerate in the parent.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    compose(legs, out)


if __name__ == "__main__":
    main()
