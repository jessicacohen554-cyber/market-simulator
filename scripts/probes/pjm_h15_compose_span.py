#!/usr/bin/env python3
"""pjm-h15 (ZERO LP): compose the per-year coal-window legs into registrable bundles.

The owner directed a per-year fan-out, which rule 36 ``[R-YEAR-ISOLATION]`` (a)
has since codified as the REQUIRED shape for a backcast ("one shard per year, own
container, no warm start, composed by the parent"). Each shard pushed its FULL
bundle -- the bundle-root ``system.parquet`` and ``dispatch/<yr>_P1.parquet``
included -- so the legs compose without a re-solve, which is the precondition
rule 32(b)'s fan-out ban assumed was missing.

The recipe is ``scripts/probes/caiso287_compose_span.py``'s, reused rather than
reinvented. What differs is the posture asserted: these legs are the PJM keeper's
recipe plus the pjm-h15 arm (``coal_sync_online_frac_per_year``), so every leg
must carry the PJM keeper posture AND prove the arm actually armed in its own
recorded ``run_config.json`` -- a leg that solved the control is not this run.

Composition rules, unchanged from that recipe:

* **year-scoped files** (``hourly/*_<year>.parquet``, ``dispatch/<year>_*``,
  ``floors/<year>_*``) copy across verbatim -- their names already carry the year.
* **bundle-root parquets** carry a ``year`` column, so they CONCATENATE and
  re-sort; a root parquet without that column FAILS LOUD.
* ``meta.json`` merges ``years`` and the per-year maps; every other key must agree.
* ``metrics.json`` / ``legitimacy_diagnostics.json`` are NOT copied -- they are
  regenerated in the parent, at zero LP, by the caller. Copying a leg's is the
  trap that silently sends C8 to SKIPPED, which downgrades the determination and
  reads exactly like a model regression.

KNOWN, and tolerated by design: the ARM 2022 leg carries no ``floors/2022_P1.npz``
(the SPP-48 directory-grain ``.gitignore`` trap on ``results/calibration/*/floors/``,
which a ``/**`` negation cannot re-include). The copy loop simply finds fewer
files; ``legitimacy_diagnostics.py --rebuild-floors`` recovers it at zero LP.

Usage::

    python3 scripts/probes/pjm_h11_compose_span.py \
        --legs results/calibration/pjm_h11_arm_2023 \
               results/calibration/pjm_h11_arm_2024 \
               results/calibration/pjm_h11_arm_2025 \
        --out results/calibration/pjm_h11_keeper_span
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
}

#: Regenerated in the parent, never copied from a leg.
REGENERATED = {"metrics.json", "legitimacy_diagnostics.json"}

#: The PJM keeper's posture, read from ``pjm_d4_4_{A,TP}/run_config.json`` (which
#: are byte-identical across all 841 scenario_config fields). Asserted on EVERY
#: leg: a leg that drifted off this is not the keeper's recipe and must not
#: compose in.
KEEPER_POSTURE: dict[str, object] = {
    "mode": "backcast",
    "pjm_seam_measured_ladder": True,
    "pjm_da_virtual_bids": True,
    "pjm_measured_interface_limits": True,
    "measured_ramp_capability": True,
    "pjm_offer_midcurve_conditional": True,
    "pjm_offer_midcurve_segments": ["LONG_RUN", "CC_LIKE"],
    "pjm_external_net_position_cut": True,
    "pjm_zonal_loss_surface": True,
    # Default-off fields that must NOT have crept in (rule 24 [R-REGISTRY]).
    "measured_coal_heat_rates": None,
    "mid_vintage_exit_carry": None,
    "mustrun_window_commitment_grain": None,  # the window-PLACEMENT sibling: NOT taken
}

#: The pjm-h15 arm's signature, asserted on EVERY leg (PRECOMMIT §3): the single
#: config delta, plus the two incumbent flags it rides on. A leg missing any of
#: these solved a different recipe and must not compose in.
ARM_SIGNATURE: dict[str, object] = {
    "coal_sync_online_frac_per_year": True,   # THE ARM
    "coal_sync_srmc_tranche": True,           # the seam it acts on
    "coal_mustrun_online_pmin": True,         # its co-predicate in assembly.py
    "coal_mustrun_requires_measured_row": True,  # the pjm-h14 keeper delta
    "mustrun_online_frac_per_year": False,    # the GAS sibling stays OFF (rule 19)
}


def _leg_year(leg: Path) -> int:
    meta = json.loads((leg / "meta.json").read_text())
    years = meta.get("years") or []
    if len(years) != 1:
        raise SystemExit(f"{leg.name}: expected exactly one year, got {years}")
    return int(years[0])


def _assert_posture(leg: Path, sc: dict) -> None:
    drift = {}
    for k, want in {**KEEPER_POSTURE, **ARM_SIGNATURE}.items():
        got = sc.get(k, None)
        if want is None:
            # Must be absent or falsy -- a default-off field that never armed.
            if got not in (None, False):
                drift[k] = ("absent/False", got)
        elif got != want:
            drift[k] = (want, got)
    if drift:
        raise SystemExit(f"{leg.name}: PJM keeper posture drift (want, got) {drift}")


def compose(legs: list[Path], out: Path) -> None:
    legs = sorted(legs, key=_leg_year)
    years = [_leg_year(l) for l in legs]
    print(f"legs : {[l.name for l in legs]}\nyears: {years}")
    if len(set(years)) != len(years):
        raise SystemExit(f"duplicate years across legs: {years}")
    out.mkdir(parents=True, exist_ok=True)

    cfgs = [json.loads((l / "run_config.json").read_text()) for l in legs]
    scs = [c.get("scenario_config") or {} for c in cfgs]

    # --- posture, per leg, BEFORE anything is written ------------------------
    for leg, sc, y in zip(legs, scs, years):
        _assert_posture(leg, sc)
        sha = (cfgs[legs.index(leg)].get("git") or {}).get("sha", "?")[:12]
        print(f"  {leg.name}: posture OK (year {y}, solve sha {sha})")

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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    compose(legs, out)


if __name__ == "__main__":
    main()
