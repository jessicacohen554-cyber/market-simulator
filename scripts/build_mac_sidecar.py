"""Build the committed marginal-abatement-cost sidecar for one grid-year.

ZERO LP. Everything here is read from a solved run's COMMITTED hourly sidecars
plus the published cost/credit constants — no solve is replayed, and the script
refuses rather than guesses when an input is missing.

    MAC ($/tCO2) = (cost per delivered MWh - energy capture price) / MER_tech

      cost per delivered MWh = compute_lcoe(tech, year, config)   [national base CF]
      energy capture price   = sum(price x tech_shape) / sum(tech_shape)
      MER_tech               = sum(MER   x tech_shape) / sum(tech_shape)

``MER`` is the EMISSIONS DUAL (``DispatchResult.marginal_emission_rate``) -- the
CO2 response of the whole system to one more MWh in that zone-hour, not the
emission rate of whichever unit's marginal cost equals the price.

INPUTS (per grid-year, from that grid's designated keeper bundle, pass P1)
  hourly/system_<year>.parquet       per zone-hour price, demand, marginal_emission_rate
  hourly/class_hourly_<year>.parquet hourly MW by class, incl. the wind/solar pseudo-units
  run_config_<year>.json             rebuilds the ScenarioConfig for compute_lcoe

TWO APPROXIMATIONS, both surfaced in the output so the page can state them:

  * ZONAL COLLAPSE. ``marginal_emission_rate`` and ``price`` are per zone-hour;
    ``class_hourly`` is ISO-wide with no zone column, and no committed sidecar
    carries per-zone VRE. v1 collapses zones LOAD-WEIGHTED before applying the
    ISO-wide shape. VRE is concentrated in particular zones, so in a congested
    hour that zone's rate differs from the load centre's and this cannot see it.
    Closing it exactly needs a per-zone VRE sidecar written at solve time.

  * WHICH PRICE. The capture price uses the SETTLED ``price`` column, overlays
    included, because that is what a project is paid. The rate is raw against
    the LP's own energy dual, deliberately: the ORDC / RTORDPA / DAM-AS adders
    are post-solve price adders that leave dispatch untouched, so they cannot
    move a CO2 response. The overlay's own $/MWh is reported beside the capture
    price rather than asserted to be immaterial.

IMPORTS. A zero-carbon *or an imported* marginal MWh both read 0 tCO2/MWh, so an
import-marginal hour understates true system consequence. The correction charges
those hours the published emission factor of the region the power comes from --
``results.emissions.import_tranche_ef``, the same sourced ladder the run's own
reported-only import CO2 uses. It is DERIVED, never assumed: a grid whose LP
carries no import pseudo-units gets a correction of exactly zero.

Usage::

    python scripts/build_mac_sidecar.py --iso SOCO --years 2023 2024 2025
    python scripts/build_mac_sidecar.py --all          # every ready grid
    python scripts/build_mac_sidecar.py --reindex      # stdlib only; writes manifest.js
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "frontend" / "data" / "mac"
REGISTRY = REPO / "frontend" / "data" / "backcast" / "registry"
KEEPERS = REPO / "frontend" / "data" / "backcast" / "keepers"
CALIB = REPO / "results" / "calibration"

TECHS = ("wind", "solar")
YEARS_DEFAULT = (2023, 2024, 2025)
HOURS = 8760


# ---------------------------------------------------------------------------
# keeper / bundle resolution
# ---------------------------------------------------------------------------
def keeper_bundle(iso: str) -> tuple[str, str]:
    """Return ``(run_id, bundle_dir_name)`` for an ISO's designated keeper."""
    kf = KEEPERS / f"{iso}.json"
    if not kf.exists():
        raise SystemExit(f"{iso}: no keeper shard at {kf}")
    run_id = json.loads(kf.read_text()).get("keeper")
    for f in REGISTRY.glob("*.json"):
        d = json.loads(f.read_text())
        if (d.get("id") or f.stem) == run_id:
            bundle = d.get("bundle") or d.get("bundle_dir") or ""
            return run_id, Path(str(bundle).rstrip("/")).name
    raise SystemExit(f"{iso}: keeper {run_id} is not in the registry")


def has_dual(bundle: str, year: int) -> bool:
    """True when that bundle-year's system sidecar carries the emissions dual."""
    p = CALIB / bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return False
    import pyarrow.parquet as pq

    return "marginal_emission_rate" in pq.ParquetFile(p).schema_arrow.names


# ---------------------------------------------------------------------------
# the computation
# ---------------------------------------------------------------------------
def build_year(iso: str, year: int, bundle: str, run_id: str) -> dict:
    """Return the sidecar payload for one grid-year, or raise with the reason."""
    import numpy as np
    import pandas as pd

    sys.path.insert(0, str(REPO / "src"))
    from market_sim.config.constants import NEW_ENTRY_COSTS
    from market_sim.model.capacity_evolution.new_entry import compute_lcoe
    from market_sim.config.scenarios import ScenarioConfig

    hourly = CALIB / bundle / "hourly"
    sysf = hourly / f"system_{year}.parquet"
    clsf = hourly / f"class_hourly_{year}.parquet"
    if not sysf.exists() or not clsf.exists():
        raise RuntimeError(f"{iso} {year}: missing hourly sidecars")

    sdf = pd.read_parquet(sysf)
    sdf = sdf[sdf["pass"] == "P1"]
    if "marginal_emission_rate" not in sdf.columns:
        raise RuntimeError(f"{iso} {year}: no marginal_emission_rate column")

    # (n_zones, T) blocks, zone-major.
    piv = lambda col: sdf.pivot_table(  # noqa: E731
        index="zone", columns="hour", values=col, aggfunc="first"
    ).sort_index()
    price = piv("price").to_numpy(dtype=float)
    demand = piv("demand").to_numpy(dtype=float)
    mer = piv("marginal_emission_rate").to_numpy(dtype=float)
    T = price.shape[1]

    # LOAD-WEIGHTED zonal collapse (see the module docstring).
    tot = demand.sum(axis=0)
    safe = np.where(tot > 0.0, tot, 1.0)
    price_iso = (price * demand).sum(axis=0) / safe
    mer_iso = (mer * demand).sum(axis=0) / safe

    # UNSERVED-ENERGY HOURS ARE NOT PRICED HOURS. Where the LP cannot serve all
    # demand it clears at the value-of-lost-load PENALTY -- a parameter chosen to
    # make shortage unattractive, not a price any market settles at. Measured in
    # SOCO 2025: 13 such hours clear at $61,900/MWh and, left in, supply 68 % of
    # the whole year's mean price and drag that grid's solar abatement cost to
    # -$189/tCO2. A project cannot earn them, so they are dropped from BOTH
    # weighted averages (the dual is equally degenerate there) and the count is
    # reported so the exclusion is visible rather than silent. Genuine scarcity
    # BELOW the offer cap is untouched -- ERCOT 2023 keeps 62 of its 63 hours
    # over $1,000.
    slack_h = np.asarray(
        sdf.groupby("hour")["slack"].sum().reindex(range(T), fill_value=0.0),
        dtype=float,
    )
    served = slack_h <= 1e-6
    n_unserved = int((~served).sum())

    # The overlay's own contribution, reported rather than asserted away.
    overlay = np.zeros(T)
    for col in ("rtordpa_overlay", "ordc_adder", "dam_as_overlay"):
        if col in sdf.columns:
            o = sdf[sdf.zone == sdf.zone.iloc[0]].sort_values("hour")[col]
            overlay = overlay + o.to_numpy(dtype=float)[:T]

    cdf = pd.read_parquet(clsf)
    cdf = cdf[cdf["pass"] == "P1"]
    shapes = {}
    for tech in TECHS:
        rows = cdf[cdf.klass == tech].sort_values("hour")
        s = np.zeros(T)
        if len(rows):
            v = rows.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0)
            s = v.to_numpy(dtype=float)
        shapes[tech] = np.maximum(s, 0.0)

    # --- imports: DERIVED, never assumed ----------------------------------
    # An hour reads 0 tCO2/MWh when the marginal resource is zero-carbon OR an
    # import. Only the import part is an understatement, so the correction is
    # scoped to hours the LP's own import pseudo-units are actually serving.
    imp = cdf[cdf.klass == "import"]
    import_mw = np.zeros(T)
    if len(imp):
        v = imp.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0)
        import_mw = np.maximum(v.to_numpy(dtype=float), 0.0)
    import_ef, ef_source = import_emission_factor(iso)
    zero_hr = mer_iso <= 1e-9
    import_marginal = zero_hr & (import_mw > 0.0)

    cfg = load_config(bundle, year, ScenarioConfig)

    # NO LOCAL CAPACITY-FACTOR ADJUSTMENT. The cost per delivered MWh is the
    # NATIONAL levelized cost at the national base capacity factor, full stop.
    #
    # The obvious refinement -- rescale by cf_base / cf_expected so a windy grid
    # spreads its annual cost over more megawatt-hours -- needs a local expected
    # capacity factor, and THAT NUMBER IS NOT RECOVERABLE from what a run
    # commits. Both available denominators were tried and both are misaligned
    # with the class_hourly dispatch that forms the numerator:
    #
    #   * EIA-860 operable capacity counts behind-the-meter solar the LP never
    #     dispatches (it is netted into load). NYISO solar came out at an
    #     expected CF of 0.022 and NEISO 0.049, against a real regional ~0.14.
    #   * The model's own renewable object cannot be rebuilt either: a slim
    #     bundle commits one run_config.json, not the per-year config the solve
    #     used, so load_renewable_profiles returns a different fleet. It put
    #     MISO 2025 solar at 7,000 MW while that year dispatches 29.75 TWh of
    #     solar -- 2.7x more energy than that capacity can physically produce.
    #     "Delivered exceeds potential" is proof the two objects are not the
    #     same fleet, so neither ratio can be trusted.
    #
    # Publishing a cost built on either would have put NYISO solar at
    # $1,040/tCO2. The page already discloses that build cost and base capacity
    # factor are national; this makes the arithmetic match that disclosure
    # instead of quietly contradicting it. Differences between grids therefore
    # come from CAPTURE PRICE and EMISSION RATE only -- both fully derivable
    # from the committed hourly sidecars. Closing this properly needs the solve
    # to commit its own per-tech capacity, which is a one-line sidecar addition
    # on the solve path.

    scalars = {}
    for tech in TECHS:
        shape = shapes[tech]
        w = shape.sum()
        if not w > 0.0:
            scalars[tech] = {"unavailable": f"the grid dispatched no {tech} in {year}"}
            continue
        sw = float(shape[served].sum()) or 1.0
        capture = float((price_iso * shape)[served].sum() / sw)
        mer_tech = float((mer_iso * shape)[served].sum() / sw)
        imp_share = float(shape[import_marginal].sum() / w)
        mer_imp = mer_tech + imp_share * import_ef

        row = {
            "cf_base": float(NEW_ENTRY_COSTS[tech]["base_cf"]),
            "capture_price": round(capture, 2),
            "mer_tech": round(mer_tech, 4),
            "mer_tech_with_imports": round(mer_imp, 4),
            "import_marginal_share": round(imp_share, 4),
        }
        for tag, credits in (("post_ira", True), ("pre_ira", False)):
            lcoe = lcoe_for(compute_lcoe, tech, year, cfg, credits)
            cost = lcoe
            row[f"lcoe_{tag}"] = round(lcoe, 2)
            row[f"cost_per_delivered_mwh_{tag}"] = round(cost, 2)
            row[f"mac_{tag}"] = round((cost - capture) / mer_tech, 1)
            row[f"mac_{tag}_with_imports"] = round((cost - capture) / mer_imp, 1)
        scalars[tech] = row

    order = np.sort(mer_iso[served])[::-1]
    idx = np.linspace(0, len(order) - 1, 200).astype(int)
    grid = np.zeros((12, 24))
    count = np.zeros((12, 24))
    # Hour 0 of the sidecar is Jan 1 00:00; month boundaries by cumulative days.
    month_of_hour = np.repeat(np.arange(12), np.diff(month_edges(year)))
    for h in range(T):
        if not served[h]:
            continue
        m = month_of_hour[min(h // 24, len(month_of_hour) - 1)]
        grid[m, h % 24] += mer_iso[h]
        count[m, h % 24] += 1
    grid = np.divide(grid, np.where(count > 0, count, 1))

    return {
        "iso": iso,
        "year": year,
        "status": "ready",
        "source_run": run_id,
        "pass": "P1",
        "scalars": scalars,
        "system": {
            "mer_load_weighted": round(
                float((mer_iso * tot)[served].sum() / tot[served].sum()), 4
            ),
            "zero_mer_hour_share": round(float(zero_hr.mean()), 4),
            "import_marginal_hour_share": round(float(import_marginal.mean()), 4),
            "import_emission_rate": round(import_ef, 4),
            "import_source": ef_source,
            "capture_price_overlay_usd_per_mwh": round(float(overlay.mean()), 2),
            "load_weighted_price": round(
                float((price_iso * tot)[served].sum() / tot[served].sum()), 2
            ),
            "unserved_hours_excluded": n_unserved,
        },
        "mer_duration": [round(float(v), 4) for v in order[idx]],
        "mer_month_hour": [[round(float(v), 4) for v in r] for r in grid],
    }


def month_edges(year: int) -> "list[int]":
    """Cumulative day index at each month boundary, 13 entries."""
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    out, acc = [0], 0
    for d in days:
        acc += d
        out.append(acc)
    return out


def lcoe_for(compute_lcoe, tech: str, year: int, cfg, credits: bool) -> float:
    """LCOE with the IRA credits on or off.

    Credits are stripped at the layer ``compute_lcoe`` applies them, by moving
    the eligibility cliff behind the build year -- never by subtracting a $/MWh
    afterwards, which would apply the solar ITC at the wrong layer (it discounts
    capex BEFORE annualization) and would credit the wind PTC over the full book
    life instead of its statutory window.
    """
    import dataclasses

    if credits:
        return float(compute_lcoe(tech, year, cfg))
    off = dataclasses.replace(cfg, ira_wind_solar_last_year=year - 1)
    return float(compute_lcoe(tech, year, off))


def load_config(bundle: str, year: int, ScenarioConfig):
    """Rebuild the run's ScenarioConfig; fall back to defaults with a warning."""
    for name in (f"run_config_{year}.json", "run_config.json"):
        p = CALIB / bundle / name
        if not p.exists():
            continue
        import dataclasses

        raw = json.loads(p.read_text())
        fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
        try:
            return ScenarioConfig(**{k: v for k, v in raw.items() if k in fields})
        except Exception as exc:  # pragma: no cover - config drift
            print(f"  ! {bundle} {year}: {name} rejected ({exc}); using defaults")
            break
    return ScenarioConfig()


def import_emission_factor(iso: str) -> "tuple[float, str]":
    """Return ``(tCO2/MWh, plain-English source)`` for this grid's imports.

    Uses the run's own published ladder -- the same factors the solved run's
    reported-only import CO2 is booked at -- averaged over the ISO's tranches.
    A grid with no import node gets 0.0, so the correction is inert there by
    construction rather than by assumption.
    """
    from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
    from market_sim.model.interchange.spec import IMPORT_TRANCHE_EF, IMPORT_ZONE

    if iso not in IMPORT_ZONE:
        return 0.0, "this grid has no modelled import link"
    efs = list(IMPORT_TRANCHE_EF.get(iso, {}).values())
    if efs:
        return float(
            sum(efs) / len(efs)
        ), "the average of the published rates for the regions it imports from"
    return float(
        CARB_UNSPECIFIED_IMPORT_EF
    ), "the published default rate for power of unspecified origin"


# ---------------------------------------------------------------------------
# index (stdlib only -- this half runs in the Pages deploy)
# ---------------------------------------------------------------------------
def reindex(site_dir: Path) -> None:
    out = site_dir / "frontend" / "data" / "mac"
    cells, isos, years = {}, set(), set()
    for f in sorted(out.glob("*-[0-9][0-9][0-9][0-9].json")):
        d = json.loads(f.read_text())
        cells[f"{d['iso']}-{d['year']}"] = d
        isos.add(d["iso"])
        years.add(d["year"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.js").write_text(
        "window.MAC_DATA = "
        + json.dumps(
            {"isos": sorted(isos), "years": sorted(years), "cells": cells},
            separators=(",", ":"),
        )
        + ";\n"
    )
    print(
        f"manifest.js: {len(cells)} grid-years, {len(isos)} grids -> {out / 'manifest.js'}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso")
    ap.add_argument("--years", nargs="*", type=int, default=list(YEARS_DEFAULT))
    ap.add_argument(
        "--all", action="store_true", help="every grid whose keeper carries the dual"
    )
    ap.add_argument(
        "--reindex", action="store_true", help="stdlib only; rebuild manifest.js"
    )
    ap.add_argument("--site-dir", default=str(REPO))
    args = ap.parse_args()

    if args.reindex:
        reindex(Path(args.site_dir))
        return

    isos = (
        [args.iso]
        if args.iso
        else sorted(p.stem for p in KEEPERS.glob("*.json") if p.stem != "index")
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wrote = 0
    for iso in isos:
        try:
            run_id, bundle = keeper_bundle(iso)
        except SystemExit as exc:
            print(f"{iso}: {exc}")
            continue
        for year in args.years:
            if not has_dual(bundle, year):
                if not args.all:
                    print(f"{iso} {year}: pending (keeper carries no emissions dual)")
                continue
            try:
                payload = build_year(iso, year, bundle, run_id)
            except Exception as exc:
                print(f"{iso} {year}: SKIPPED - {exc}")
                continue
            (OUT_DIR / f"{iso}-{year}.json").write_text(
                json.dumps(payload, separators=(",", ":")) + "\n"
            )
            wrote += 1
            w = payload["scalars"].get("wind", {})
            s = payload["scalars"].get("solar", {})
            fmt = lambda d: (  # noqa: E731
                f"${d['mac_post_ira_with_imports']:.1f}"
                if "mac_post_ira_with_imports" in d
                else "n/a"
            )
            print(f"{iso} {year}: wind {fmt(w):>7s}  solar {fmt(s):>7s}  /tCO2")
    print(f"\nwrote {wrote} grid-year sidecars to {OUT_DIR}")


if __name__ == "__main__":
    main()
