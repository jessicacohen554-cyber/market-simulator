#!/usr/bin/env python3
"""pjm-h19 (ZERO LP): compose the per-year PJM ``demand_balance_screen`` legs into registrable bundles.

``hydro2_pjm_compose_span.py`` reused verbatim except for the posture it
asserts: the hydro-2 arm (``hydro_ror_split``) is now the KEEPER's own recipe
and joins the incumbent posture, and the one field separating arm from
control is ``demand_balance_screen``
(docs/PRECOMMIT-pjm-h19-demand-balance-screen-2026-09-23.md §1).

Usage::

    python3 scripts/probes/pjm_h19_compose_span.py --side arm \\
        --legs results/calibration/pjm_h19_dbs_2023 ... \\
        --out results/calibration/pjm_h19_dbs_span
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

#: The PJM keeper's posture, asserted on EVERY leg of EITHER side: a leg that
#: drifted off this is not the keeper's recipe and must not compose in. The
#: pjm-h15 arm is here because it is now the KEEPER's own recipe.
KEEPER_POSTURE: dict[str, object] = {
    "mode": "backcast",
    "pjm_seam_measured_ladder": True,
    "pjm_da_virtual_bids": True,
    "pjm_measured_interface_limits": True,
    "measured_ramp_capability": True,
    "pjm_offer_midcurve_conditional": True,
    "pjm_external_net_position_cut": True,
    "pjm_zonal_loss_surface": True,
    "coal_sync_srmc_tranche": True,
    "coal_mustrun_online_pmin": True,
    "coal_mustrun_requires_measured_row": True,
    "coal_sync_online_frac_per_year": True,  # the pjm-h15 keeper delta
    "coal_sync_window_commitment_grain": True,  # the pjm-h16 keeper delta
    "hydro_ror_split": True,  # the hydro-2 keeper delta
    # PRECOMMIT-hydro-2 §6 / rule 14: both read PS-folded EIA-930 NG: WAT.
    "hydro_min_flow_floor": None,
    "hydro_dispatch_envelope": None,
    "hydro_pondage_bound": None,
    # Default-off fields that must NOT have crept in (rule 24 [R-REGISTRY]).
    "measured_coal_heat_rates": None,
    "mid_vintage_exit_carry": None,
    # Rule 19 [R-ONE-MECH]: the GAS window-grain sibling stays OFF on both
    # sides, and so does SPP-71's third placement rule for the same floor.
    "mustrun_window_commitment_grain": None,
    "mustrun_online_frac_per_year": None,
    "coal_sync_ensemble_level": None,
}

#: The ONE field that separates the two sides (PRECOMMIT-pjm-h19 §1).
ARM_FIELD = "demand_balance_screen"


def _leg_year(leg: Path) -> int:
    meta = json.loads((leg / "meta.json").read_text())
    years = meta.get("years") or []
    if len(years) != 1:
        raise SystemExit(f"{leg.name}: expected exactly one year, got {years}")
    return int(years[0])


def _flat(sc: dict) -> dict:
    """scenario_config with one level of override dicts flattened in.

    ``replay_keeper`` packs ``--set`` overrides through ``prb_overrides``, which
    land nested inside a sibling override dict rather than at the top level, so
    a naive ``sc.get(field)`` reads ``None`` for a field that IS armed.
    """
    out = dict(sc)
    for v in sc.values():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                out.setdefault(k2, v2)
    return out


def _assert_posture(leg: Path, sc: dict, armed: bool) -> None:
    flat = _flat(sc)
    want_all = {**KEEPER_POSTURE, ARM_FIELD: True if armed else None}
    drift = {}
    for k, want in want_all.items():
        got = flat.get(k, None)
        if want is None:
            # Must be absent or falsy — a default-off field that never armed.
            if got not in (None, False):
                drift[k] = ("absent/False", got)
        elif got != want:
            drift[k] = (want, got)
    if drift:
        raise SystemExit(f"{leg.name}: PJM keeper posture drift (want, got) {drift}")


def compose(legs: list[Path], out: Path, armed: bool) -> None:
    legs = sorted(legs, key=_leg_year)
    years = [_leg_year(leg) for leg in legs]
    side = "ARM" if armed else "CONTROL"
    print(f"side : {side} ({ARM_FIELD} {'True' if armed else 'absent/False'})")
    print(f"legs : {[leg.name for leg in legs]}\nyears: {years}")
    if len(set(years)) != len(years):
        raise SystemExit(f"duplicate years across legs: {years}")
    out.mkdir(parents=True, exist_ok=True)

    cfgs = [json.loads((leg / "run_config.json").read_text()) for leg in legs]
    scs = [c.get("scenario_config") or {} for c in cfgs]

    # --- posture, per leg, BEFORE anything is written ------------------------
    for leg, sc, cfg, y in zip(legs, scs, cfgs, years):
        _assert_posture(leg, sc, armed)
        sha = (cfg.get("git") or {}).get("sha", "?")[:12]
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

    shas = {(c.get("git") or {}).get("sha") for c in cfgs}
    print(f"solve sha(s): {sorted(s[:12] for s in shas if s)}")

    base = dict(cfgs[0])
    base["scenario_config"] = base_sc
    base["composed_from"] = [leg.name for leg in legs]
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

    root_names = sorted({p.name for leg in legs for p in leg.glob("*.parquet")})
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
                raise SystemExit(
                    f"{leg.name}/{name} carries years {got}, expected [{y}]"
                )
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

    metas = [json.loads((leg / "meta.json").read_text()) for leg in legs]
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
    meta["composed_from"] = [leg.name for leg in legs]
    (out / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    print(f"meta.json: years={meta['years']} composed_from={meta['composed_from']}")
    print(f"\nCOMPOSED -> {out}")
    print(
        "metrics.json / legitimacy_diagnostics.json NOT copied -- regenerate in the "
        "parent over the COMPOSITE (pjm-h13 method note), and run "
        "run_calibration_full.py --rebuild-benchmark on the composite before "
        "registering (pjm-h15 correction #1: a composed bundle inherits its FIRST "
        "LEG's single-year shared_inputs and registration dies in build_payload)."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--side", choices=("arm", "control"), required=True)
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    compose(legs, out, armed=a.side == "arm")


if __name__ == "__main__":
    main()
