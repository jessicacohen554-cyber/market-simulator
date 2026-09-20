"""soco-55 (ZERO LP): compose the per-year legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) requires each backcast year in its own shard
container, and rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its
FULL bundle -- the bundle-root ``system.parquet`` and ``dispatch/<yr>_P1.parquet``
included -- so the legs compose without a re-solve. That is the precondition
rule 32(b) ``[R-SHARD]``'s fan-out ban assumes is missing.

The recipe is ``scripts/probes/caiso287_compose_span.py``'s (itself
``nyiso238_compose_span.py``'s), reused rather than reinvented. What differs is
the assertion, because this lane composes BOTH an arm and a control:

* every leg must carry SOCO's keeper posture (:data:`KEEPER_POSTURE`), so a leg
  solved on a drifted recipe cannot compose in;
* ``gas_basis_differential_measured_by_year`` is asserted EXPLICITLY, to the
  value ``--expect-measured`` names, on every leg. It is THIS lane's single delta,
  and the assertion reads the RESOLVED ``scenario_config`` -- never the
  ``prb_overrides`` bag the CLI routed it through, which is what ``audit_keepers``
  E11 sees (``PRECOMMIT-soco-55`` §3.2). A leg that silently solved the keeper's
  own recipe would compose in looking like a null result, so this is not optional;
  ``gas_plant_monthly_fuel_pricing`` is now SOCO-54's INHERITED posture and moves
  into :data:`KEEPER_POSTURE`, asserted False on every leg;
* every leg must carry a live ``marginal_emission_rate`` column, which SOCO's
  keeper carries and which the rule-15 hourly duty requires.

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

    python3 scripts/probes/soco55_compose_span.py --expect-measured true \\
        --legs results/calibration/soco55_arm_{2023,2024,2025} \\
        --out  results/calibration/soco55_peryear_basis
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

#: SOCO's keeper posture (2026-09-20-soco53f-measured-coal-hr). Asserted on
#: EVERY leg: these legs replay that keeper's own ``meta.json``, so any drift
#: here means the leg is not the keeper's recipe. ``measured_coal_heat_rates``
#: was 53f's own single delta and ``gas_plant_monthly_fuel_pricing`` was 54's, so
#: both are soco-55's inherited baseline and both sit in the posture.
#: ``gas_basis_differential_measured_by_year`` is deliberately NOT here: it is THIS
#: lane's single delta and is asserted separately, to ``--expect-measured``.
KEEPER_POSTURE: dict[str, object] = {
    "measured_ct_heat_rates": True,
    "egrid_family_heat_rates": True,
    "measured_st_heat_rates": True,
    "soco_gas_st_campaign_commitment": True,
    "measured_coal_heat_rates": True,
    "gas_plant_monthly_fuel_pricing": False,
    "coal_plant_monthly_pricing": True,
}


def _leg_year(leg: Path) -> int:
    meta = json.loads((leg / "meta.json").read_text())
    years = meta.get("years") or []
    if len(years) != 1:
        raise SystemExit(f"{leg.name}: expected exactly one year, got {years}")
    return int(years[0])


#: The FOUR price-tuning bands rule 1 ``[R-STRUCT]``'s carve-out names. The other
#: ``offer_curve_by_group`` keys — ``econ_low_share``, ``pct_peaking`` — are
#: STRUCTURAL shares the carve-out explicitly EXCLUDES, they are not 1.0 on any
#: ISO, and they arrive verbatim from the ISO-agnostic ``GENERIC_BASE_OFFER_CURVE``.
#: Checking them for the identity would be a category error.
PRICE_TUNING_BANDS = ("committed", "econ_low", "econ_high", "peak")


def _assert_bands_identity(leg: Path, sc: dict) -> None:
    """Gate G17: every price-tuning band stays at the identity 1.0.

    SOCO has no price benchmark, so the rule-1 authorized price-tuning channel
    is unreachable here rather than merely unused. A non-1.0 band on any leg is
    a governance failure, not a composition detail.
    """
    bands = sc.get("offer_curve_by_group") or {}
    off = {
        f"{grp}.{band}": row[band]
        for grp, row in bands.items()
        if isinstance(row, dict)
        for band in PRICE_TUNING_BANDS
        if band in row and float(row[band]) != 1.0
    }
    if off:
        raise SystemExit(f"{leg.name}: offer_curve_by_group bands off identity: {off}")


def _assert_mer(leg: Path, year: int) -> dict:
    """A leg with no live marginal_emission_rate defeats the rule-15 duty."""
    p = leg / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        raise SystemExit(f"{leg.name}: missing {p.name}")
    df = pd.read_parquet(p)
    if "marginal_emission_rate" not in df.columns:
        raise SystemExit(f"{leg.name}: NO marginal_emission_rate column")
    m = df["marginal_emission_rate"]
    if m.isna().all() or (m.fillna(0.0) == 0.0).all():
        raise SystemExit(f"{leg.name}: marginal_emission_rate is all-null/all-zero")
    return {"rows": int(len(df)), "nonzero": int((m.fillna(0.0) != 0.0).sum())}


def _assert_dispatch(leg: Path, year: int) -> None:
    """``render_calibration_html.build_payload`` reads this per year."""
    p = leg / "dispatch" / f"{year}_P1.parquet"
    if not p.exists():
        raise SystemExit(
            f"{leg.name}: missing dispatch/{year}_P1.parquet -- registration "
            "would raise FileNotFoundError and the per-plant D-1/D-2/D-4 "
            "diagnostics would PASS VACUOUSLY on zero rows (rule 32(b))"
        )


def compose(legs: list[Path], out: Path, expect_measured: bool) -> None:
    legs = sorted(legs, key=_leg_year)
    years = [_leg_year(leg) for leg in legs]
    print(f"legs : {[leg.name for leg in legs]}\nyears: {years}")
    print(f"expecting gas_basis_differential_measured_by_year = {expect_measured} on every leg")
    if len(set(years)) != len(years):
        raise SystemExit(f"duplicate years across legs: {years}")
    out.mkdir(parents=True, exist_ok=True)

    cfgs = [json.loads((leg / "run_config.json").read_text()) for leg in legs]
    scs = [c.get("scenario_config") or {} for c in cfgs]

    # --- posture + the single delta + MER, per leg, BEFORE anything is written
    for leg, sc, year in zip(legs, scs, years):
        drift = {k: (v, sc.get(k)) for k, v in KEEPER_POSTURE.items() if sc.get(k) != v}
        if drift:
            raise SystemExit(f"{leg.name}: posture drift (want, got) {drift}")
        got = bool(sc.get("gas_basis_differential_measured_by_year"))
        if got != expect_measured:
            raise SystemExit(
                f"{leg.name}: gas_basis_differential_measured_by_year is "
                f"{sc.get('gas_basis_differential_measured_by_year')!r}, expected "
                f"{expect_measured} -- this leg solved the WRONG side of the A/B"
            )
        # `--set` routes this field through the generic ``prb_overrides`` channel
        # (it is not a ``solve_and_persist`` kwarg), which `meta.json` records as
        # a ``coal_prb_sigmoid_overrides`` diff and ``audit_keepers`` E11 flags.
        # Benign -- PRECOMMIT-soco-54 §7 -- but the RESOLVED value must stay
        # null, or the override bag leaked into the sigmoid registry for real.
        if sc.get("coal_prb_sigmoid_overrides") not in (None, {}):
            raise SystemExit(
                f"{leg.name}: resolved coal_prb_sigmoid_overrides is "
                f"{sc.get('coal_prb_sigmoid_overrides')!r}, expected null -- the "
                "prb_overrides channel leaked into the PRB sigmoid registry"
            )
        _assert_bands_identity(leg, sc)
        _assert_dispatch(leg, year)
        cen = _assert_mer(leg, year)
        print(
            f"  {leg.name}: posture OK, gas_basis_differential_measured_by_year={got}, bands 1.0, "
            f"dispatch present, "
            f"MER live ({cen['nonzero']}/{cen['rows']} nonzero)"
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

    envs = {
        json.dumps((c.get("environment") or {}).get("packages"), sort_keys=True)
        for c in cfgs
    }
    if len(envs) != 1:
        raise SystemExit(
            f"legs solved on DIFFERENT dependency sets -- refusing to compose: {envs}"
        )
    print(f"environment.packages identical across legs: {envs.pop()}")

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
    for leg, year in zip(legs, years):
        for src in sorted(leg.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(leg)
            if rel.name in REGENERATED or rel.name in ("meta.json", "run_config.json"):
                continue
            if src.suffix == ".parquet" and rel.parent == Path("."):
                continue  # bundle-root parquet: concatenated below
            if str(year) not in rel.name:
                continue
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    print(f"year-scoped files copied: {copied}")

    root_names = sorted({p.name for leg in legs for p in leg.glob("*.parquet")})
    for name in root_names:
        frames = []
        for leg, year in zip(legs, years):
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
            if got != [year]:
                raise SystemExit(
                    f"{leg.name}/{name} carries years {got}, expected [{year}]"
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
        "metrics.json / legitimacy_diagnostics.json NOT copied -- regenerate in the parent."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--expect-measured",
        required=True,
        choices=("true", "false"),
        help="the value gas_basis_differential_measured_by_year MUST carry on "
        "every leg ('true' for the soco-55 arm, 'false' for the keeper control)",
    )
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    compose(legs, out, a.expect_measured == "true")


if __name__ == "__main__":
    main()
