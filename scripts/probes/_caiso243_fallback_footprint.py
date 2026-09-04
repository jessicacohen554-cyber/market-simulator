"""caiso-243 — the F923 low-volume fallback defect: repair-form FOOTPRINTS, zero LP.

NO LP, NO SOLVE, NOTHING ARMED. Every variant below rebuilds the committed
keeper's OWN recipe (``caiso241_b1_ctpeaker_committed/meta.json``) through the
real ``run_year(fleet_only=True)`` path with ONE thing patched at the F923
plant-monthly overwrite, and diffs the resulting delivered fuel-price array
against the unpatched rebuild cell by cell (generator x hour). The unpatched
rebuild is itself checked against the keeper's committed hourly sidecar
(``class_band_hourly_2025``) so the baseline is the keeper, not a re-derivation.

The object (FINDING-caiso242 §5): three compounding defects deliver one EIA-923
row (plant 55077, NV, 96.161 $/MMBtu on 2 % of its own normal volume) to
2,816 MW of CAISO gas for all of November 2025 —

  D1  ``state`` is EMPTY on 100 % of the CAISO gas fleet, so the state tier
      (the only tier with a donor-count guard) is skipped fleet-wide;
  D2  the zone tier has NO donor-count guard and serves from a pool of ONE;
  D3  the source row itself is a fixed charge over a near-zero denominator.

The candidate repairs, each measured here as a footprint and NONE armed:

  (a)  extend the EXISTING ``nearby_fuel_price_min_state_plants`` guard to the
       zone tier (no new constant);
  (c)  populate ``state`` on the CAMPD-bin fleet from the plant's EIA-860
       state (``eia860_plant.parquet``), so the guarded tier is reachable
       (no new constant);
  (a)+(c) together;
  (b)  a volume-admissibility guard on F923 rows, at the census's SWEPT cuts
       (each one a NEW parameter — reported for the owner's sizing, never
       selected here; rule 5 [R-NO-MAGIC]).

Also measured: the D1 ROOT CAUSE (``bins_to_fleet`` never sets
``Generator.state`` — a code-path fact, ISO-generic), the tier attribution of
every CAISO gas generator-month in the LIVE (hub-overlay-uncovered) months,
and the residual each form leaves behind (55077's own row under (a)/(c)).

Writes ``results/calibration/_caiso243_fallback_footprint.json`` and caches
each variant's fuel-price array under the scratch dir so a later stage can
re-diff without rebuilding.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso243_fallback_footprint.py \
        --years 2025 --variants keeper a c ac b_0.02_2.0
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/caiso241_b1_ctpeaker_committed"
OUT = REPO / "results/calibration/_caiso243_fallback_footprint.json"
EIA860_PLANT = REPO / "data/raw/eia-860/eia860_plant.parquet"
CACHE = Path(
    os.environ.get(
        "C243_CACHE",
        "/tmp/claude-0/-home-user-market-simulator/8996884f-b2f8-5b4c-a42b-d6af63597aea/scratchpad/c243v2",
    )
)
HOURS = 8760
YEARS_ALL = (2023, 2024, 2025)
GAS_GROUPS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.concatenate([np.full(d * 24, m) for m, d in enumerate(_DAYS)])[
    :HOURS
]


# --------------------------------------------------------------------------- #
# Variant machinery: everything is a patch on the F923 plant-monthly pass.
# --------------------------------------------------------------------------- #
def eia860_state_map() -> dict[int, str]:
    """``{plant_code: USPS state}`` from the EIA-860 plant table (form (c))."""
    df = pd.read_parquet(EIA860_PLANT, columns=["Plant Code", "State"])
    df = df.dropna()
    return {
        int(p): str(s).strip().upper() for p, s in zip(df["Plant Code"], df["State"])
    }


def keeper_min_state_plants() -> int:
    """The donor floor the keeper resolves (``run_config.json``), reused verbatim by form (a)."""
    rc = json.loads((BUNDLE / "run_config.json").read_text())
    return int(rc["scenario_config"]["nearby_fuel_price_min_state_plants"])


def _guarded_nearby_class(min_zone: int):
    """Subclass of ``_NearbyFuelPrices`` applying the donor-count guard to the zone tier (form (a))."""
    from market_sim.data.fuel import plant_prices as pp

    class _Guarded(pp._NearbyFuelPrices):
        def _grids(self, fuel_group, klass=None):
            key = ("zc", fuel_group, klass)
            cached = self._cache.get(key)
            if cached is not None:
                return cached
            state_price, state_count, zone_price = super()._grids(fuel_group, klass)
            sub = self._iso_costs[self._iso_costs["fuel_group"] == fuel_group]
            if klass is not None:
                donor_class = self._plant_class.get(fuel_group, {})
                sub = sub[
                    sub["plant_id"].map(lambda p: donor_class.get(int(p))) == klass
                ]
            zone_count: dict[int, np.ndarray] = {}
            if not sub.empty:
                z = sub.assign(zone=sub["plant_id"].map(self._plant_to_zone)).dropna(
                    subset=["zone"]
                )
                for zone, grp in z.groupby("zone", sort=False):
                    cnt = np.zeros(12)
                    for m, g in grp.groupby("month"):
                        if 1 <= int(m) <= 12:
                            cnt[int(m) - 1] = g["plant_id"].nunique()
                    zone_count[int(zone)] = cnt
            guarded_zone = {
                z: np.where(zone_count.get(z, np.zeros(12)) >= min_zone, p, np.nan)
                for z, p in zone_price.items()
            }
            result = (state_price, state_count, guarded_zone)
            self._cache[key] = result
            return result

    return _Guarded


def _filtered_costs(
    costs: pd.DataFrame, qty_frac: float, price_mult: float
) -> pd.DataFrame:
    """Drop gas plant-months failing the (b) volume-admissibility cut."""
    d = costs.copy()
    gas = (d["fuel_group"] == "Natural Gas") & (d["quantity"] > 0)
    g = d[gas].groupby(["plant_id", "year"])
    qmed = g["quantity"].transform("median")
    spend = (
        (d.loc[gas, "price_per_mmbtu"] * d.loc[gas, "quantity"])
        .groupby([d.loc[gas, "plant_id"], d.loc[gas, "year"]])
        .transform("sum")
    )
    qsum = g["quantity"].transform("sum")
    vw = spend / qsum
    bad = (d.loc[gas, "quantity"] <= qty_frac * qmed) & (
        d.loc[gas, "price_per_mmbtu"] >= price_mult * vw
    )
    drop_idx = d.loc[gas].index[bad.values]
    return d.drop(index=drop_idx)


class Variant:
    """One patched F923 pass. ``name`` in {keeper, a, c, ac, b_<q>_<p>, ...}."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.guard_zone = name in ("a", "ac")
        self.fill_state = name in ("c", "ac")
        self.filter = None
        if name.startswith("b_"):
            _, q, p = name.split("_")
            self.filter = (float(q), float(p))

    @contextlib.contextmanager
    def active(self):
        """Patch the seam(s) this variant changes, for the duration of a rebuild."""
        import run_calibration as rc
        import market_sim.data.fuel as facade
        from market_sim.data.fuel import plant_prices as pp

        orig_apply = pp.apply_plant_monthly_fuel_prices
        orig_nearby = pp._NearbyFuelPrices
        # ``apply_plant_monthly_fuel_prices`` resolves the cache loader through
        # the package facade (``_pkg_ns()._load_monthly_cache``), so form (b)
        # patches the FACADE attribute, not the module's.
        orig_cache = facade._load_monthly_cache
        smap = eia860_state_map() if self.fill_state else None
        filt = self.filter

        def patched_apply(fuel_prices, fleet, config, year, monthly_costs_path=None):
            if smap is not None:
                fleet.state = np.array(
                    [
                        smap.get(int(p), "") if int(p) > 0 else ""
                        for p in fleet.plant_code
                    ],
                    dtype=object,
                )
            return orig_apply(fuel_prices, fleet, config, year, monthly_costs_path)

        def patched_cache(path=None):
            frame = orig_cache(path)
            if frame is None or filt is None:
                return frame
            return _filtered_costs(frame, *filt)

        try:
            if self.guard_zone:
                pp._NearbyFuelPrices = _guarded_nearby_class(keeper_min_state_plants())
            if filt is not None:
                facade._load_monthly_cache = patched_cache
            rc.apply_plant_monthly_fuel_prices = patched_apply
            pp.apply_plant_monthly_fuel_prices = patched_apply
            yield
        finally:
            rc.apply_plant_monthly_fuel_prices = orig_apply
            pp.apply_plant_monthly_fuel_prices = orig_apply
            pp._NearbyFuelPrices = orig_nearby
            facade._load_monthly_cache = orig_cache


def keeper_recipe_kwargs(meta: dict, run_year) -> dict:
    """The keeper recipe as ``run_year`` kwargs, via the SAME mapping the solve uses.

    Since caiso-244 a thin wrapper over the shared
    :func:`scripts.replay_keeper.run_year_kwargs` (the strict, remapping
    reconstruction this probe first built inline at caiso-243 when the lane's
    by-parameter-name pattern was found to drop ``prb_overrides``). The
    ``run_year`` argument is kept for signature compatibility with the cached
    artifacts' call sites; the helper introspects the canonical module itself.
    """
    from replay_keeper import run_year_kwargs

    return run_year_kwargs(meta)


def rebuild(year: int, variant: Variant) -> dict:
    """Rebuild the keeper recipe's fleet + fuel prices for ``year`` under ``variant``."""
    import importlib.util

    from run_calibration import run_year

    spec = importlib.util.spec_from_file_location(
        "_c240", REPO / "scripts/probes/_caiso240_default_hr_mult_census.py"
    )
    c240 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c240)

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = keeper_recipe_kwargs(meta, run_year)
    c240._clear_fleet_caches()
    buf = io.StringIO()
    with variant.active(), contextlib.redirect_stderr(buf):
        st = run_year(
            year,
            meta["iso"],
            HOURS,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kwargs,
        )
    fa = st["fleet_arrays"]
    gens = st.get("fleet") or []
    fp = np.asarray(st["fuel_prices"], dtype=float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    # the min_state resolved on THIS config (the guard's donor floor)
    min_state = int(getattr(st["config"], "nearby_fuel_price_min_state_plants", 2))
    mc = st.get("mc_base")
    mc = np.asarray(mc, dtype=float) if mc is not None else np.zeros_like(fp)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    out = {
        "fuel": fp,
        # the ASSEMBLED P0 offer the LP is handed (fuel + VOM + carbon + NOx +
        # margin reform), so the price-leg envelope reads the same offers the
        # solve will see, never a fuel-only re-derivation
        "mc": mc,
        "pmax": np.asarray(fa.pmax, float),
        "heat_rate": np.asarray(fa.heat_rate, float),
        "plant_code": np.asarray(fa.plant_code, int),
        "zone_idx": np.asarray(fa.zone_idx, int),
        "fuel_type_idx": np.asarray(fa.fuel_type_idx, int),
        "group": np.array(
            [str(getattr(g, "plant_group", "")) for g in gens], dtype=object
        ),
        "state": np.array(
            [str(s) for s in (fa.state if fa.state is not None else [""] * fa.n_gen)],
            dtype=object,
        ),
        "unit": np.array([str(u) for u in fa.unit_ids], dtype=object),
        "min_state": min_state,
        "log": buf.getvalue(),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        CACHE / f"{variant.name}_{year}.npz",
        **{k: v for k, v in out.items() if k not in ("log", "min_state")},
    )
    (CACHE / f"{variant.name}_{year}.log").write_text(out["log"])
    return out


def load_cached(year: int, name: str) -> dict | None:
    p = CACHE / f"{name}_{year}.npz"
    if not p.exists():
        return None
    z = np.load(p, allow_pickle=True)
    d = {k: z[k] for k in z.files}
    d["log"] = (
        (CACHE / f"{name}_{year}.log").read_text()
        if (CACHE / f"{name}_{year}.log").exists()
        else ""
    )
    return d


# --------------------------------------------------------------------------- #
# Measurement
# --------------------------------------------------------------------------- #
def hub_covered_months(year: int) -> list[int]:
    """Calendar months (1-12) the CAISO hub-basis overlay covers in ``year``."""
    df = pd.read_csv(REPO / "data/raw/gas_basis_by_iso_month.csv")
    sub = df[(df["iso"] == "CAISO") & (df["year"] == year)]
    return sorted(int(m) for m in sub["month"].unique())


def gas_mask(d: dict) -> np.ndarray:
    return np.isin(d["group"], GAS_GROUPS)


def diff_footprint(base: dict, var: dict, year: int, zone_names: list[str]) -> dict:
    """Cells, rows, MW and $ that move between two rebuilds of the same year."""
    assert (
        base["unit"].shape == var["unit"].shape and (base["unit"] == var["unit"]).all()
    ), "fleet identity"
    dfp = var["fuel"] - base["fuel"]
    moved = ~np.isclose(dfp, 0.0, atol=1e-9)
    rows = moved.any(axis=1)
    gm = gas_mask(base)
    out = {
        "cells_moved": int(moved.sum()),
        "rows_moved": int(rows.sum()),
        "rows_moved_nongas": int((rows & ~gm).sum()),
        "mw_moved": round(float(base["pmax"][rows].sum()), 1),
        "plants_moved": sorted(int(p) for p in np.unique(base["plant_code"][rows])),
        "months_moved": sorted(
            int(m) + 1 for m in np.unique(MONTH_OF_HOUR[moved.any(axis=0)])
        ),
        "by_group_mw": {},
        "by_plant": [],
        "by_month": {},
    }
    for g in GAS_GROUPS:
        sel = rows & (base["group"] == g)
        if sel.any():
            out["by_group_mw"][g] = round(float(base["pmax"][sel].sum()), 1)
    for p in out["plants_moved"]:
        sel = rows & (base["plant_code"] == p)
        w = base["pmax"][sel]
        rec = {
            "plant": p,
            "state_eia860": eia860_state_map().get(p, ""),
            "zone": zone_names[int(base["zone_idx"][sel][0])],
            "group": sorted(set(base["group"][sel].tolist())),
            "mw": round(float(w.sum()), 1),
            "months": {},
        }
        for m in range(12):
            hm = MONTH_OF_HOUR == m
            cell = moved[sel][:, hm]
            if cell.any():
                b = (base["fuel"][sel][:, hm] * w[:, None]).sum() / (w.sum() * hm.sum())
                v = (var["fuel"][sel][:, hm] * w[:, None]).sum() / (w.sum() * hm.sum())
                hr = base["heat_rate"][sel]
                dmc = (
                    (var["fuel"][sel][:, hm] - base["fuel"][sel][:, hm])
                    * hr[:, None]
                    * w[:, None]
                ).sum() / (w.sum() * hm.sum())
                rec["months"][m + 1] = {
                    "base_usd_mmbtu": round(float(b), 4),
                    "variant_usd_mmbtu": round(float(v), 4),
                    "d_mc_usd_mwh_capwt": round(float(dmc), 3),
                }
        out["by_plant"].append(rec)
    for m in range(12):
        hm = MONTH_OF_HOUR == m
        cell = moved[:, hm]
        if cell.any():
            r = cell.any(axis=1)
            w = base["pmax"][r]
            b = (base["fuel"][r][:, hm] * w[:, None]).sum() / (w.sum() * hm.sum())
            v = (var["fuel"][r][:, hm] * w[:, None]).sum() / (w.sum() * hm.sum())
            hr = base["heat_rate"][r]
            mcb = ((base["fuel"][r][:, hm] * hr[:, None] * w[:, None]).sum()) / (
                w.sum() * hm.sum()
            )
            mcv = ((var["fuel"][r][:, hm] * hr[:, None] * w[:, None]).sum()) / (
                w.sum() * hm.sum()
            )
            out["by_month"][m + 1] = {
                "rows": int(r.sum()),
                "mw": round(float(w.sum()), 1),
                "base_usd_mmbtu_capwt": round(float(b), 4),
                "variant_usd_mmbtu_capwt": round(float(v), 4),
                "base_fuel_mc_usd_mwh_capwt": round(float(mcb), 2),
                "variant_fuel_mc_usd_mwh_capwt": round(float(mcv), 2),
                "capability_mwh_at_stake": round(float(w.sum() * hm.sum()), 0),
            }
    return out


def tier_attribution(
    base: dict, year: int, live_months: list[int], zone_names: list[str], min_state: int
) -> dict:
    """Which fallback tier prices each CAISO gas generator-month, on the keeper's own path (instrumented replica)."""
    from market_sim.data.eia923 import (
        load_monthly_fuel_costs,
        plant_month_price_grid,
        state_month_price_grid,
    )

    costs = load_monthly_fuel_costs()
    gm = gas_mask(base)
    iso_costs = costs[
        (costs["year"] == year)
        & (costs["plant_id"].isin(set(int(p) for p in base["plant_code"] if p > 0)))
    ]
    sub = iso_costs[iso_costs["fuel_group"] == "Natural Gas"]
    own = plant_month_price_grid(costs, year, "Natural Gas")
    sp, sc = state_month_price_grid(sub, year, "Natural Gas")
    zone_of = {
        int(p): int(z) for p, z in zip(base["plant_code"], base["zone_idx"]) if p > 0
    }
    zone_n = {}
    for zone, grp in (
        sub.assign(zone=sub["plant_id"].map(zone_of))
        .dropna(subset=["zone"])
        .groupby("zone")
    ):
        zone_n[int(zone)] = {
            int(m): int(g["plant_id"].nunique()) for m, g in grp.groupby("month")
        }
    out = {
        "live_months": live_months,
        "state_empty_gas_rows": int((base["state"][gm] == "").sum()),
        "gas_rows": int(gm.sum()),
        "state_empty_gas_mw": round(
            float(base["pmax"][gm & (base["state"] == "")].sum()), 1
        ),
        "gas_mw": round(float(base["pmax"][gm].sum()), 1),
        "tiers_live_months": {},
        "zone_pool_sizes": {zone_names[z]: n for z, n in zone_n.items()},
        "state_reporter_counts": {s: [int(x) for x in c] for s, c in sc.items()},
    }
    smap = eia860_state_map()
    tiers = {}
    for i in np.flatnonzero(gm):
        p = int(base["plant_code"][i])
        st = str(base["state"][i])
        z = int(base["zone_idx"][i])
        for m in live_months:
            mi = m - 1
            if p in own and not np.isnan(own[p][mi]):
                t = "own"
            elif (
                st and st in sp and sc[st][mi] >= min_state and not np.isnan(sp[st][mi])
            ):
                t = "state"
            elif zone_n.get(z, {}).get(m, 0) > 0:
                t = f"zone(pool={zone_n[z][m]})"
            else:
                t = "default(HH+basis)"
            key = (t, zone_names[z], smap.get(p, "?"))
            rec = tiers.setdefault(key, {"rows": 0, "mw": 0.0, "plants": set()})
            rec["rows"] += 1
            rec["mw"] += float(base["pmax"][i])
            rec["plants"].add(p)
    out["tiers_live_months"] = [
        {
            "tier": k[0],
            "zone": k[1],
            "eia860_state": k[2],
            "rows": v["rows"],
            "mw": round(v["mw"], 1),
            "plants": sorted(v["plants"]),
        }
        for k, v in sorted(tiers.items(), key=lambda kv: -kv[1]["mw"])
    ]
    return out


def keeper_sidecar_check(base: dict, year: int) -> dict:
    """Does the unpatched rebuild reproduce the keeper's committed class-band fuel price? (baseline = keeper)"""
    p = BUNDLE / "hourly" / f"class_band_hourly_{year}.parquet"
    if not p.exists():
        return {"available": False}
    df = pd.read_parquet(p)
    cols = df.columns.tolist()
    return {"available": True, "columns": cols[:20], "rows": int(len(df))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2025])
    ap.add_argument("--variants", nargs="+", default=["keeper", "a", "c", "ac"])
    ap.add_argument(
        "--reuse", action="store_true", help="use cached rebuilds where present"
    )
    args = ap.parse_args()
    from market_sim.config.iso_configs import get_iso_config

    zone_names = list(get_iso_config("CAISO").zone_names)
    result = json.loads(OUT.read_text()) if OUT.exists() else {}
    result["_provenance"] = {
        "session": "caiso-243",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "keeper_run_id": "2026-09-03-caiso-241-b1-ctpeaker",
        "note": "no LP, nothing armed; each variant is a monkeypatch on the F923 plant-monthly pass inside the real run_year(fleet_only=True) rebuild of the keeper recipe",
        "d1_root_cause": "data/fleet/assembly.py::bins_to_fleet constructs Generator(...) without `state`; Generator.state defaults to '' (data/fleet/__init__.py); only the EIA-860 loader path (data/fleet/eia860.py) sets it — so every ISO on plant_level_fleet/use_campd_bins has an empty state tier",
        "state_source_for_c": str(EIA860_PLANT.relative_to(REPO))
        + " (Plant Code -> State)",
    }
    result.setdefault("years", {})
    for year in args.years:
        live = [m for m in range(1, 13) if m not in hub_covered_months(year)]
        yr = result["years"].setdefault(str(year), {})
        yr["hub_overlay_covered_months"] = hub_covered_months(year)
        yr["live_months"] = live
        builds = {}
        for name in args.variants:
            cached = load_cached(year, name) if args.reuse else None
            if cached is None:
                print(f"[rebuild] {year} {name}", flush=True)
                cached = rebuild(year, Variant(name))
            builds[name] = cached
            hub_line = [
                ln for ln in cached["log"].splitlines() if "hub-basis overlay" in ln
            ]
            f923_line = [
                ln for ln in cached["log"].splitlines() if "F923 fuel costs" in ln
            ]
            yr.setdefault("log_lines", {})[name] = {
                "hub": hub_line[-1][-120:] if hub_line else "",
                "f923": f923_line[-1][-120:] if f923_line else "",
            }
        base = builds.get("keeper") or load_cached(year, "keeper")
        if base is None:
            raise SystemExit("need the keeper rebuild first")
        min_state = int(np.asarray(base.get("min_state", 2)))
        yr["tier_attribution_keeper"] = tier_attribution(
            base, year, live, zone_names, min_state
        )
        yr["keeper_sidecar"] = keeper_sidecar_check(base, year)
        yr.setdefault("footprints", {})
        for name, b in builds.items():
            if name == "keeper":
                continue
            yr["footprints"][name] = diff_footprint(base, b, year, zone_names)
            print(
                f"{year} {name}: rows {yr['footprints'][name]['rows_moved']} mw {yr['footprints'][name]['mw_moved']} months {yr['footprints'][name]['months_moved']}"
            )
    OUT.write_text(
        json.dumps(
            result,
            indent=2,
            default=lambda o: int(o) if isinstance(o, np.integer) else float(o),
        )
        + "\n"
    )
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
