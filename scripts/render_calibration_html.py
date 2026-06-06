"""Render the multi-run interactive HTML calibration report from bundles.

Self-contained (no external JS/CSS). One HTML compares several calibration
runs (configs) with a top toggle between a cross-run **Summary** page and a
per-run **Detail** page, a **Zone** multi-select (all zones or any subset), and
a Year selector. Class aggregation, capture metrics and the comparison tables
all recompute client-side from embedded per-plant series so the zone filter is
live.

Two capture scores (each in [0,100]%, see :func:`_capture`):
  * **Class capture%** — geometric mean of the class-aggregate hourly r,
    (1-NRMSE) and (1-|annual deviation|) vs CAMPD: is the class total right in
    shape and level?
  * **Plant capture%** — capacity-weighted mean of each plant's own
    geometric-mean capture%: are the *right plants* running (merit order)?
    Stays low when the class total is right but generation is on the wrong
    plants, and rises only when a config fixes the per-plant allocation.

Summary page: capture gauges per run, a per-fuel delta-vs-EIA-930 table, a
fossil-class table (Δ / r / NRMSE vs CAMPD) and a plant Δ-vs-EIA-923 table
across runs (2025 excluded — EIA-923 incomplete), plus model-vs-CAMPD monthly
lines and an annual model/EIA/CAMPD bar by fuel class. Detail page keeps the
per-plant commitment heatmaps, dispatch profile, annual and monthly charts.

Per-plant hourly CF series are embedded base64 uint8 (0-100); the CAMPD
benchmark is embedded once and shared across runs. See
docs/calibration-report.md.

Usage:
    python scripts/render_calibration_html.py [LABEL=]BUNDLE ... [--out FILE]
    # each BUNDLE is one config (may hold several years); LABEL overrides the
    # run name shown in the toggle (default: the bundle directory name).
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rcf", str(REPO / "scripts" / "run_calibration_full.py"))
rcf = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(rcf)

from market_sim.config.plant_taxonomy import (  # noqa: E402
    LABELS, class_label, classes_for_fuel930, fossil_classes, nonfossil_classes,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    CHP_BTM_PCT_BY_SECTOR, CHP_SECTOR_CLASS_BY_PLANT, CHP_ST_BTM_PCT,
    load_campd_bins, plant_tranche_bands,
)

# All class groupings derive from the canonical taxonomy
# (market_sim.config.plant_taxonomy) — the single source of truth mapping model
# plant classes to EIA-930 fuel buckets and labels. Adding a class there flows
# through every table here automatically (no hardcoded class lists). The
# per-ISO filter (in build_payload) keeps only the classes an ISO dispatches.
_group_label = class_label                  # known canonical name, else humanized
GROUP_LABEL = dict(LABELS)
_NONFOSSIL_KLASS = nonfossil_classes()
FOSSIL_GROUPS = list(fossil_classes())
MIX_GROUPS = list(FOSSIL_GROUPS)
_GAS_GROUPS = classes_for_fuel930("gas")
_COAL_GROUPS = classes_for_fuel930("coal")
_CUM = np.cumsum([0] + list(rcf._DAYS_IN_MONTH)) * 24  # month hour boundaries
_T = 8760


def _b64(cf: np.ndarray) -> str:
    """Encode a capacity-factor series (0-100) as base64 uint8 of length 8760."""
    a = np.clip(np.nan_to_num(cf), 0, 250).round().astype(np.uint8)
    if a.shape[0] < _T:
        a = np.concatenate([a, np.zeros(_T - a.shape[0], np.uint8)])
    return base64.b64encode(a[:_T].tobytes()).decode()


def _monthly_gwh(mw: np.ndarray) -> list[float]:
    """Return 12 monthly GWh totals from an hourly MW series."""
    return [round(float(mw[_CUM[m]:_CUM[m + 1]].sum()) / 1e3, 2)
            for m in range(12)]


def _pearson(m: np.ndarray, o: np.ndarray) -> float:
    m = m - m.mean(); o = o - o.mean()
    d = float(np.sqrt((m * m).sum() * (o * o).sum()))
    return float((m * o).sum() / d) if d > 0 else 0.0


def _nrmse(m: np.ndarray, o: np.ndarray) -> float:
    den = float(o.mean())
    return float(np.sqrt(((m - o) ** 2).mean()) / den) if den > 0 else 9.9


def _capture(r: float, nrmse: float, dev: float) -> float:
    """Geometric-mean capture% from r, NRMSE and annual fractional deviation."""
    rs = max(0.0, r)
    ns = max(0.0, 1.0 - nrmse)
    ls = max(0.0, 1.0 - abs(dev))
    return round(100.0 * (rs * ns * ls) ** (1.0 / 3.0), 1)


def _btm_share(plant_id: int, group: str) -> float:
    """Behind-the-meter host self-supply share of net gen for a CHP plant."""
    if group not in ("CC_CHP", "CT_CHP", "ST_CHP"):
        return 0.0
    if group == "ST_CHP":
        return CHP_ST_BTM_PCT / 100.0
    sector = CHP_SECTOR_CLASS_BY_PLANT.get(int(plant_id), "merchant")
    return CHP_BTM_PCT_BY_SECTOR.get(sector, 40.0) / 100.0


@lru_cache(maxsize=1)
def _eia860_plant_info() -> tuple[dict[int, float], dict[int, str]]:
    """Return ``({plant_id: nameplate MW}, {plant_id: name})`` from EIA-860.

    The national per-plant nameplate (summed over units) and plant name, so
    non-ERCOT bundles (PJM, etc.) — whose plants are absent from the ERCOT
    CAMPD bin sheet — still get a real capacity and label in the dashboard.
    """
    from market_sim.data.fleet import EIA_860_DIR, EIA_860_PARQUET_NAME
    path = EIA_860_DIR / EIA_860_PARQUET_NAME
    if not path.exists():
        return {}, {}
    df = pd.read_parquet(
        path, columns=["plant_id", "plant_name", "nameplate_capacity_mw"]
    )
    df["plant_id"] = df["plant_id"].astype(int)
    npl = df.groupby("plant_id")["nameplate_capacity_mw"].sum().to_dict()
    nm = df.groupby("plant_id")["plant_name"].first().to_dict()
    return ({int(k): float(v) for k, v in npl.items()},
            {int(k): str(v) for k, v in nm.items()})


def _nameplates() -> dict[int, float]:
    """Plant nameplate MW: ERCOT bin sheet first, EIA-860 fleet for the rest."""
    bins = pd.read_csv(ScenarioConfig().campd_bins_path)
    out = dict(_eia860_plant_info()[0])
    out.update(zip(bins["Plant_Code"].astype(int),
                   bins["Nameplate_MW"].astype(float)))
    return out


def _plant_names() -> dict[int, str]:
    """Plant names: ERCOT bin sheet first, EIA-860 fleet for the rest."""
    bins = pd.read_csv(ScenarioConfig().campd_bins_path)
    out = dict(_eia860_plant_info()[1])
    out.update(zip(bins["Plant_Code"].astype(int),
                   bins["Plant_Name"].astype(str)))
    return out


def _coal_group(klass: str) -> str:
    return klass


_BINS_CACHE: dict[str, dict] = {}


def _tranche_bands_for_bundle(bdir: Path) -> dict[int, list]:
    """Return ``{plant_code: tranche bands}`` for a bundle's stored config.

    Reads the bundle's ``run_config.json`` (the serialized scenario config the
    run was generated with) and computes each plant's offer-curve tranche bands
    via :func:`market_sim.data.fleet.plant_tranche_bands`, so the dashboard's
    CF chart can mark where each band engages and the multiplier priced there.
    Returns ``{}`` for bundles without a stored config.
    """
    cfg_path = bdir / "run_config.json"
    if not cfg_path.exists():
        return {}
    try:
        sc = json.loads(cfg_path.read_text())["scenario_config"]
        config = ScenarioConfig(**sc)
    except Exception:
        return {}
    bins_path = config.campd_bins_path
    rows = _BINS_CACHE.get(bins_path)
    if rows is None:
        bins = load_campd_bins(bins_path)
        rows = {int(r["Plant_Code"]): r for _, r in bins.iterrows()}
        _BINS_CACHE[bins_path] = rows
    out: dict[int, list] = {}
    for code, row in rows.items():
        bands = plant_tranche_bands(row, config)
        if bands:
            out[code] = bands
    return out


def build_payload(runs: list[tuple[str, Path]],
                  years: set[int] | None = None) -> dict:
    """Assemble the embedded data for every run, with a shared CAMPD benchmark.

    Returns a dict with: groups / labels / zones / years; ``bench`` (per year:
    per-plant CAMPD CF + annual + monthly, EIA-923 per-plant annual + monthly,
    EIA-930 per-fuel annual + hourly); and ``model`` (per run, per year:
    per-plant model CF + annual + monthly + per-plant r / NRMSE / capture%, the
    non-fossil model annual, and the system fuel-vs-930 table rows).
    """
    npl = _nameplates()
    pnames = _plant_names()
    labels = [lab for lab, _ in runs]
    years_set: set[int] = set()
    zones_set: set[str] = set()
    groups_set: set[str] = set()

    bench: dict[int, dict] = {}          # year -> benchmark payload
    model_runs: list[dict] = []          # per run -> {year -> payload}

    for ri, (label, bdir) in enumerate(runs):
        meta = json.loads((bdir / "meta.json").read_text())
        tr_bands = _tranche_bands_for_bundle(bdir)
        run_years: dict[int, dict] = {}
        e923_all = pd.read_parquet(bdir / "eia923.parquet")
        e930_all = pd.read_parquet(bdir / "eia930.parquet")
        campd_all = pd.read_parquet(bdir / "campd.parquet")
        sys_all = pd.read_parquet(bdir / "system.parquet")
        # Behind-the-meter must-run per (year, pass, class) — the same off-grid
        # CHP host self-supply the LP held out, as the calibration report uses
        # it (run_calibration_full). Drives the system-wide generation mix.
        btm_all = (pd.read_parquet(bdir / "btm.parquet")
                   if (bdir / "btm.parquet").exists() else None)
        for year in meta["years"]:
            if years is not None and int(year) not in years:
                continue
            years_set.add(int(year))
            disp = pd.read_parquet(bdir / "dispatch" / f"{year}_P1.parquet")
            e923 = e923_all[e923_all["year"] == year]
            e930 = e930_all[e930_all["year"] == year]
            campd = campd_all[campd_all["year"] == year]

            # Model hourly MW per (fossil) plant, with its zone and class.
            dm = disp[(disp["plant_code"] > 0)
                      & (disp["klass"].isin(FOSSIL_GROUPS))]
            mw_p, zone_p, grp_p = {}, {}, {}
            for (code, klass), g in dm.groupby(["plant_code", "klass"],
                                               observed=True):
                arr = (g.groupby("hour")["mw"].sum()
                       .reindex(range(_T), fill_value=0.0).to_numpy(float))
                mw_p[int(code)] = arr
                zone_p[int(code)] = str(g["zone"].iloc[0])
                grp_p[int(code)] = str(klass)
                zones_set.add(zone_p[int(code)])
                groups_set.add(str(klass))

            # CAMPD net hourly per plant (benchmark — built once on run 0).
            cn_p: dict[int, np.ndarray] = {}
            for code, g in campd.groupby("plant_id", observed=True):
                a = np.nan_to_num(g.sort_values("hour")["net_mw"]
                                  .to_numpy(float))
                cn_p[int(code)] = np.concatenate(
                    [a, np.zeros(max(0, _T - a.shape[0]))])[:_T]

            e923_ann = e923.groupby("plant_id")["annual_mwh"].sum().to_dict()
            mcols = [f"m{i:02d}" for i in range(1, 13)]
            e923_mon = {int(i): (row.to_numpy(float) / 1e3)
                        for i, row in e923.groupby("plant_id")[mcols]
                        .sum().iterrows()}

            # ---- benchmark payload (build once, on the first run) ----
            if ri == 0:
                bplants: dict[str, dict] = {}
                for code, cn in cn_p.items():
                    grp = grp_p.get(code)
                    if grp is None:
                        continue
                    cap = float(npl.get(code, 0.0)) or 1.0
                    e_ann = float(e923_ann.get(code, 0.0)) / 1e6
                    bplants[str(code)] = {
                        "name": pnames.get(code, str(code)),
                        "zone": zone_p.get(code, "?"),
                        "group": grp, "npl": round(cap),
                        # No usable CAMPD hourly series (plant absent from CEMS
                        # or all-NaN, e.g. some waste-coal units): flagged so the
                        # charts show the model without a misleading flat-zero
                        # 'actual' comparison.
                        "nodata": bool(cn.sum() <= 0.0),
                        "campd": _b64(100.0 * cn / cap),
                        "c_ann": round(float(cn.sum()) / 1e6, 4),
                        "c_mon": _monthly_gwh(cn),
                        "e_ann": round(e_ann, 4),
                        "btm": round(e_ann * _btm_share(code, grp), 4),
                        "e_mon": [round(x, 2) for x in e923_mon.get(code,
                                  np.zeros(12))],
                    }
                e = {s: e930[e930["series"] == s].sort_values("hour")["mw"]
                     .to_numpy(float) for s in e930["series"].unique()}
                # Full EIA-923 net generation per fossil class (TWh) — every
                # 923 plant of the class, NOT just the ones the model matches.
                # This is the true class total the generation-mix benchmark and
                # the zonal Δ-vs-923 are scaled to (matched plants understate
                # it, e.g. CC_REGULAR 145 TWh vs ~138 matched in 2024).
                e923_cls = e923.groupby("klass")["annual_mwh"].sum()
                # Every actual class is kept (not just the hardcoded MIX_GROUPS)
                # so the model's real plant classification — e.g. EIA-923-derived
                # coal ranks COAL_BIT / COAL_SUB / COAL_WC — carries its actual
                # into the table for every ISO. groups_set picks them up below.
                groups_set.update(str(g) for g in e923_cls.index)
                bench[int(year)] = {
                    "plants": bplants,
                    "e930": {f: round(float(e.get(f, np.zeros(1)).sum())
                                      / 1e6, 3)
                             for f in ("gas", "coal", "nuclear", "wind",
                                       "solar")},
                    "classFull": {str(g): round(float(v) / 1e6, 4)
                                  for g, v in e923_cls.items()},
                }

            # ---- model payload (per run) ----
            mplants: dict[str, dict] = {}
            for code, mw in mw_p.items():
                cap = float(npl.get(code, 0.0)) or 1.0
                grp = grp_p.get(code, "")
                # CHP add-back (report only, NOT in the LP): the host
                # behind-the-meter self-supply was held out of the grid solve,
                # but CAMPD measures the full plant. Add it back flat so the
                # plant heatmap and the plant/class r / NRMSE / capture compare
                # the full plant to the full CAMPD plant. A flat add is
                # correlation-invariant (it corrects the level, not the shape).
                if grp in ("CC_CHP", "CT_CHP", "ST_CHP"):
                    btm_mwh = float(e923_ann.get(code, 0.0)) * _btm_share(
                        code, grp)
                    if btm_mwh > 0.0:
                        mw = mw + btm_mwh / float(_T)
                cn = cn_p.get(code)
                r = nr = None
                cap_pct = None
                if cn is not None and cn.sum() > 0 and mw.std() > 0:
                    r = round(_pearson(mw, cn), 3)
                    nr = round(_nrmse(mw, cn), 3)
                    dev = (mw.sum() - cn.sum()) / cn.sum()
                    cap_pct = _capture(r, nr, dev)
                mplants[str(code)] = {
                    "m": _b64(100.0 * mw / cap),
                    "m_ann": round(float(mw.sum()) / 1e6, 4),
                    "m_mon": _monthly_gwh(mw),
                    "r": r, "nrmse": nr, "cap": cap_pct,
                }
                if code in tr_bands:
                    mplants[str(code)]["tr"] = tr_bands[code]
            # Non-fossil model annual (nuclear / wind / solar) for fuel table.
            nf = {}
            for f in ("nuclear", "wind", "solar"):
                s = disp[disp["klass"] == f]
                nf[f] = round(float(s["mw"].sum()) / 1e6, 3)
            # System fuel-vs-EIA-930 table (all zones; 930 is not zonal).
            mh = rcf._class_hourly(disp)
            e = {s: e930[e930["series"] == s].sort_values("hour")["mw"]
                 .to_numpy(float) for s in e930["series"].unique()}
            _CHP = tuple(c for c in classes_for_fuel930("gas")
                         if c.endswith("_CHP"))
            chp_flat = sum(mh.get(c, np.zeros(_T)).sum() for c in _CHP) / _T
            fuel_rows = []
            # Each EIA-930 fuel row sums the model classes that roll up to it
            # (market_sim.config.plant_taxonomy) — so any class is counted once,
            # in the right bucket, with no hardcoded membership list.
            specs = [
                (fuel, classes_for_fuel930(fuel), e.get(fuel), fuel == "gas")
                for fuel in ("gas", "coal", "nuclear", "wind", "solar")
            ]
            for fuel, classes, ob, is_gas in specs:
                ms = sum((mh.get(c, np.zeros(_T)) for c in classes),
                         np.zeros(_T))
                # gas: compare the non-CHP model grid to (930 gas - model CHP).
                if is_gas:
                    ms = sum((mh.get(c, np.zeros(_T))
                              for c in ("CC_REGULAR", "CT_PEAKER", "ST_GAS")),
                             np.zeros(_T))
                    ob = ob - chp_flat if ob is not None else None
                m_twh = float(ms.sum()) / 1e6
                b_twh = float(ob.sum()) / 1e6 if ob is not None else None
                r2 = (round(_pearson(ms, ob), 3)
                      if ob is not None and ob.std() > 0 else None)
                n2 = (round(_nrmse(ms, ob), 3) if ob is not None else None)
                fuel_rows.append({
                    "fuel": fuel, "m": round(m_twh, 2),
                    "b": round(b_twh, 2) if b_twh is not None else None,
                    "r": r2, "nrmse": n2})
            # Per-zone average LMP (load-weighted) from the system duals, for
            # the dashboard's average-LMP KPI. P1 pass; the shell averages over
            # the selected zones, weighting by demand.
            sy = sys_all[sys_all["year"] == year]
            if "pass" in sy.columns and (sy["pass"] == "P1").any():
                sy = sy[sy["pass"] == "P1"]
            lmp = {}
            for zone, zg in sy.groupby("zone", observed=True):
                dem = float(zg["demand"].sum())
                p = (float((zg["price"] * zg["demand"]).sum()) / dem
                     if dem > 0 else float(zg["price"].mean()))
                lmp[str(zone)] = {"p": round(p, 2),
                                  "d": round(dem / 1e6, 4)}
            # System-wide generation mix per fossil class (TWh): model grid LP
            # (``_class_hourly`` sum) + behind-the-meter must-run, exactly as
            # run_calibration_full's [3b] thermal table builds the model total.
            # Compared against ``bench.classFull`` (full EIA-923) it yields the
            # share-of-fossil and the pp deviation shown in the mix table.
            btm_y = {}
            if btm_all is not None:
                by = btm_all[(btm_all["year"] == year)
                             & (btm_all["pass"] == "P1")]
                btm_y = dict(zip(by["klass"], by["btm_twh"]))
            gm_model = {
                g: round(float(mh.get(g, np.zeros(_T)).sum()) / 1e6
                         + (float(btm_y.get(g, 0.0))
                            if g in ("CC_CHP", "CT_CHP", "ST_CHP") else 0.0), 4)
                for g in (set(MIX_GROUPS) | set(mh))
            }
            run_years[int(year)] = {
                "plants": mplants, "nonfossil": nf, "fuelRows": fuel_rows,
                "gmModel": gm_model, "lmp": lmp}
        model_runs.append({"label": label, "years": run_years})

    # Only the fossil classes actually present in this ISO's dispatch, in the
    # canonical order — so the class selector and its default land on a
    # populated class (PJM has no COAL_LIGNITE, so it must not default there and
    # render an empty view). ERCOT keeps all classes (all present).
    # Fossil classes actually present in this ISO's model or benchmark, in
    # canonical order first then any extra (auto-wired) classes sorted — so a
    # new classification like the EIA-923 coal ranks shows up for every ISO
    # without being hardcoded here. Non-fossil classes are excluded.
    fossil_present = {
        g for g in groups_set if g not in _NONFOSSIL_KLASS
    }
    groups = [g for g in FOSSIL_GROUPS if g in fossil_present] + sorted(
        fossil_present - set(FOSSIL_GROUPS)
    )
    groups = groups or FOSSIL_GROUPS
    return {
        "groups": groups,
        "groupLabel": {g: _group_label(g) for g in groups},
        "zones": sorted(zones_set), "years": sorted(years_set),
        "runLabels": labels, "bench": bench, "model": model_runs,
    }


def main() -> None:
    """Render the multi-run report from one or more bundles."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+",
                    help="[LABEL=]BUNDLE_DIR for each run/config")
    ap.add_argument("--out", default=str(
        REPO / "results" / "calibration" / "calibration-report.html"))
    args = ap.parse_args()
    runs: list[tuple[str, Path]] = []
    for spec in args.bundles:
        if "=" in spec:
            lab, _, d = spec.partition("=")
        else:
            d = spec; lab = Path(spec).name
        runs.append((lab, Path(d)))
    payload = build_payload(runs)
    # Gzip + base64 the payload (CF series compress ~5x); the browser inflates
    # it with DecompressionStream. Keeps the self-contained file small enough
    # for mobile and version control.
    import gzip
    gz = gzip.compress(json.dumps(payload).encode(), compresslevel=9)
    b64 = base64.b64encode(gz).decode()
    out = Path(args.out)
    out.write_text(
        TEMPLATE
        .replace("__B64__", b64)
        .replace("__GEN__", datetime.now().strftime("%Y-%m-%d %H:%M")))
    n_series = sum(len(y["plants"]) for r in payload["model"]
                   for y in r["years"].values())
    print(f"wrote {out}  ({out.stat().st_size / 1e6:.1f} MB, "
          f"{len(runs)} runs, {n_series} model series)")


TEMPLATE = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Calibration — Multi-Run Comparison</title><style>
:root{--bg:#f6f7f9;--card:#fff;--bd:#e3e7ec;--ink:#1a1f29;--mut:#6b7480;
 --model:#ef7d2b;--campd:#2f9bd6;--e923:#2e9e5b;--e930:#8b5cf6;--mr:#7b8794;
 --r0:#ef7d2b;--r1:#2e9e5b;--r2:#8b5cf6;}
*{box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0;padding:18px}
.wrap{max-width:1080px;margin:0 auto}h1{font-size:23px;margin:0 0 2px}.sub{color:var(--mut);font-size:14px;margin:0 0 14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px 18px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.row{display:flex;flex-wrap:wrap;gap:16px;align-items:center}
.lab{font-size:12px;letter-spacing:.06em;color:var(--mut);font-weight:600;text-transform:uppercase;margin-right:6px}
.seg{display:inline-flex;background:#eef1f4;border-radius:9px;padding:3px;flex-wrap:wrap}
.seg button{border:0;background:transparent;padding:7px 13px;border-radius:7px;font-size:14px;cursor:pointer;color:var(--mut);font-weight:600}
.seg button.on{background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.12)}
.chips{display:inline-flex;gap:6px;flex-wrap:wrap}
.chip{border:1px solid var(--bd);background:#fff;border-radius:20px;padding:5px 12px;font-size:13px;cursor:pointer;color:var(--mut)}
.chip.on{background:var(--campd);color:#fff;border-color:var(--campd)}
select{font-size:15px;padding:8px 11px;border:1px solid var(--bd);border-radius:8px;background:#fff;max-width:100%}
h2{font-size:19px;margin:2px 0}h3{font-size:16px;margin:18px 0 8px}h4{font-size:14px;margin:14px 0 6px;color:#3a4250}
.hsub{color:var(--mut);font-size:13px;margin:0 0 10px}
canvas.heat{width:100%;height:170px;image-rendering:pixelated;border:1px solid var(--bd);border-radius:6px;background:#eef3f7;display:block}
.ax{display:flex;justify-content:space-between;color:var(--mut);font-size:12px;margin:3px 2px 0}
.legend{display:flex;align-items:center;gap:16px;font-size:13px;color:var(--mut);margin:10px 0;flex-wrap:wrap}
.swatch{display:inline-block;width:22px;height:0;border-top-width:3px;border-top-style:solid;vertical-align:middle;margin-right:5px}
.ramp{height:11px;width:170px;border-radius:3px;background:linear-gradient(90deg,#e8f3f7,#7fc4e6,#86c98f,#f2d65c,#ef8f3c,#c0392b)}
.gaugegrid{display:flex;flex-wrap:wrap;gap:14px}
.gcard{flex:1;min-width:210px;background:#f8fafc;border:1px solid var(--bd);border-radius:10px;padding:12px 14px}
.gcard h4{margin:0 0 2px}.grow{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.gcard svg{max-width:220px;margin:0 auto}.runblk{flex:1;min-width:280px}
.tablewrap{width:100%;overflow-x:auto;margin:6px 0 14px;border:1px solid var(--bd);border-radius:8px}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.5px}
th,td{padding:7px 10px;border-bottom:1px solid #eef1f4;text-align:left;white-space:nowrap}
th{background:#f0f3f6;font-size:11.5px;text-transform:uppercase;color:#46505f;position:sticky;top:0}
td.num{text-align:right;font-variant-numeric:tabular-nums}.good{color:#0f7d3d}.ok{color:#9a6700}.bad{color:#c01c28;font-weight:600}
tr.sumrow td{border-top:2px solid #cfd6dd;font-weight:700;background:#f8fafc}
.kpis{display:flex;flex-wrap:wrap;gap:10px}.kpi{flex:1;min-width:130px;background:#f8fafc;border:1px solid var(--bd);border-radius:9px;padding:10px 13px}
.kpik{font-size:12px;color:var(--mut);text-transform:uppercase}.kpiv{font-size:21px;font-weight:700;margin-top:3px}
.hide{display:none}svg{width:100%;height:auto;display:block}
#tip{position:fixed;display:none;pointer-events:none;background:#1a1f29;color:#fff;font-size:13px;line-height:1.5;padding:8px 11px;border-radius:8px;box-shadow:0 4px 14px rgba(0,0,0,.28);z-index:99}
canvas.heat,svg{cursor:crosshair}
@media(max-width:640px){
 body{padding:9px}.card{padding:12px}.wrap{max-width:100%}
 h1{font-size:19px}h2{font-size:17px}h3{font-size:15px}
 th,td{padding:6px 7px;font-size:12.5px}
 .row{gap:10px}.row>div{flex:1 1 100%}
 .lab{display:block;margin-bottom:3px}
 select{width:100%}
 .gaugegrid{gap:10px}.gcard{min-width:100%}.runblk{min-width:100%}
 .gcard svg{max-width:100%}
 canvas.heat{height:130px}
 .seg{width:100%;justify-content:center}.seg button{flex:1}
}
</style></head><body><div class=wrap>
<div id=tip></div>
<h1>Calibration — Multi-Run Comparison</h1>
<p class=sub>Model vs EPA CAMPD / EIA actuals · generated __GEN__</p>
<noscript><div class=card style="border-color:#c01c28;color:#c01c28">Interactive — needs JavaScript. Download and open in a browser.</div></noscript>
<div id=diag class=card style="border-color:#e0a800;color:#9a6700">Loading… if this stays, your viewer blocks JavaScript — download and open in a browser.</div>

<div class=card><div class=row>
 <div><span class=lab>View</span><span class=seg id=pageSel></span></div>
 <div><span class=lab>Year</span><span class=seg id=yearSel></span></div>
 <div><span class=lab>Zones</span><span class=chips id=zoneSel></span></div>
</div></div>

<!-- ===== SUMMARY ===== -->
<div id=summary-view>
 <div class=card><h2>Capture scores by class</h2>
  <p class=hsub>Class capture% = aggregate shape &amp; level vs CAMPD. Plant capture% = capacity-weighted per-plant capture (the "right total, wrong plants" / merit-order signal).</p>
  <div id=gauges></div></div>
 <div class=card><h2>Fuel totals vs EIA-930 <span class=hsub>(system-wide; EIA-930 is not zonal)</span></h2>
  <div class=tablewrap id=tblFuel></div></div>
 <div class=card><h2>Fossil classes — model grid vs EIA-923−BTM (r/NRMSE vs CAMPD)</h2>
  <div class=tablewrap id=tblFossil></div></div>
 <div class=card><h2>Plant Δ vs EIA-923 <span class=hsub>(2025 excluded — 923 incomplete)</span></h2>
  <div class=tablewrap id=tblPlant></div></div>
 <div class=card><div class=row><span class=lab>Class</span><select id=sumClass></select></div>
  <h3>Monthly — model (per run) vs CAMPD actual (GWh)</h3>
  <div class=legend id=legMon></div><svg id=sumMonthly viewBox="0 0 720 340"></svg>
  <h3>Annual total — model (per run) vs CAMPD &amp; EIA (TWh)</h3>
  <svg id=sumAnnual viewBox="0 0 720 320"></svg></div>
</div>

<!-- ===== DETAIL ===== -->
<div id=detail-view class=hide>
 <div class=card><div class=row>
  <div><span class=lab>Run</span><select id=runSel></select></div>
  <div><span class=lab>Class</span><select id=groupSel></select></div>
  <div><span class=lab>Plant</span><select id=plantSel></select></div></div></div>
 <div class=card><div class=grow style="flex-wrap:wrap"><div id=dGauge1 style=flex:1;min-width:240px></div><div id=dGauge2 style=flex:1;min-width:240px></div></div>
  <div class=kpis id=kpi style=margin-top:12px></div></div>
 <div class=card><h2>Commitment heatmap</h2><p class=hsub id=heatSub></p>
  <div class=legend><span>0%</span><span class=ramp></span><span>100% CF</span></div>
  <h4>CAMPD actual</h4><canvas class=heat id=heatC width=365 height=24></canvas><div class=ax id=axC></div>
  <h4>Model</h4><canvas class=heat id=heatM width=365 height=24></canvas><div class=ax id=axM></div></div>
 <div class=card><h2>Average daily profile (CF%)</h2><p class=hsub id=dispSub></p>
  <div class=legend>
   <span><i class=swatch style="border-top-color:var(--campd)"></i><b>CAMPD</b></span>
   <span><i class=swatch style="border-top-color:var(--model)"></i><b>Model</b></span></div>
  <svg id=profile viewBox="0 0 720 340"></svg></div>
 <div class=card><h2>Monthly (GWh)</h2><svg id=monthly viewBox="0 0 720 320"></svg></div>
</div>

<script id=payload type="application/gzip-base64">__B64__</script>
<script>
let D=null;const MONTHS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const DIM=[31,28,31,30,31,30,31,31,30,31,30,31],CUM=[0];for(const d of DIM)CUM.push(CUM[CUM.length-1]+d*24);
const RC=["#ef7d2b","#2e9e5b","#8b5cf6","#0d9488","#db2777"];
const NS="http://www.w3.org/2000/svg";const T=8760;
let st;
function dec(b){const s=atob(b),a=new Float32Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a;}
function pearson(m,o){let mm=0,oo=0,n=m.length;for(let i=0;i<n;i++){mm+=m[i];oo+=o[i];}mm/=n;oo/=n;
 let a=0,b=0,c=0;for(let i=0;i<n;i++){const x=m[i]-mm,y=o[i]-oo;a+=x*y;b+=x*x;c+=y*y;}const d=Math.sqrt(b*c);return d>0?a/d:0;}
function nrmse(m,o){let s=0,om=0,n=m.length;for(let i=0;i<n;i++){s+=(m[i]-o[i])**2;om+=o[i];}om/=n;return om>0?Math.sqrt(s/n)/om:9.9;}
function capScore(r,nr,dev){const rs=Math.max(0,r),ns=Math.max(0,1-nr),ls=Math.max(0,1-Math.abs(dev));return 100*Math.cbrt(rs*ns*ls);}
// plants of the current run+year in the selected class & zones
function plantsOf(ri,year,grp){const M=D.model[ri].years[year],B=D.bench[year];if(!M||!B)return [];
 return Object.keys(M.plants).filter(c=>{const b=B.plants[c];return b&&b.group===grp&&st.zones.has(b.zone);});}
// class aggregate hourly (MW) for model & campd over selected zones (cached)
const _aggC={};
function aggMW(ri,year,grp){const key=ri+"|"+year+"|"+grp+"|"+[...st.zones].sort().join(",");
 if(_aggC[key])return _aggC[key];
 const M=D.model[ri].years[year],B=D.bench[year];const mm=new Float32Array(T),cc=new Float32Array(T);
 let cAnn=0,mAnn=0,eAnn=0,bAnn=0;for(const c of plantsOf(ri,year,grp)){const b=B.plants[c],npl=b.npl;
  const md=dec(M.plants[c].m),cd=dec(b.campd);for(let i=0;i<T;i++){mm[i]+=md[i]*npl/100;cc[i]+=cd[i]*npl/100;}
  mAnn+=M.plants[c].m_ann;cAnn+=b.c_ann;eAnn+=b.e_ann;bAnn+=(b.btm||0);}
 return _aggC[key]={mm,cc,mAnn,cAnn,eAnn,bAnn};}
// metric 1 (class capture%) and metric 2 (capacity-weighted plant capture%)
function classMetrics(ri,year,grp){const ps=plantsOf(ri,year,grp);if(!ps.length)return null;
 const a=aggMW(ri,year,grp);const r=pearson(a.mm,a.cc),nr=nrmse(a.mm,a.cc),dev=a.cAnn>0?(a.mAnn-a.cAnn)/a.cAnn:0;
 const m1=a.cc.reduce((s,v)=>s+v,0)>0?capScore(r,nr,dev):null;
 const M=D.model[ri].years[year],B=D.bench[year];let wsum=0,csum=0;
 for(const c of ps){const w=B.plants[c].npl,cp=M.plants[c].cap;if(cp!=null){wsum+=w;csum+=w*cp;}}
 const m2=wsum>0?csum/wsum:null;
 return {m1,m2,r,nr,dev,mAnn:a.mAnn,cAnn:a.cAnn,eAnn:a.eAnn,bench923:a.eAnn-a.bAnn,n:ps.length};}
// ---- gauge ----
function gauge(pct,label,sub){const w=200,h=120,cx=100,cy=104,R=78;const v=pct==null?0:Math.max(0,Math.min(100,pct));
 const ang=Math.PI*(1-v/100);const x=cx+R*Math.cos(ang),y=cy-R*Math.sin(ang);
 const col=v>=80?"#0f7d3d":v>=60?"#9a6700":"#c01c28";
 const arc=(a0,a1,c,wd)=>{const x0=cx+R*Math.cos(a0),y0=cy-R*Math.sin(a0),x1=cx+R*Math.cos(a1),y1=cy-R*Math.sin(a1);
  return `<path d="M${x0.toFixed(1)} ${y0.toFixed(1)} A${R} ${R} 0 0 1 ${x1.toFixed(1)} ${y1.toFixed(1)}" fill=none stroke="${c}" stroke-width="${wd}" stroke-linecap=round/>`;};
 return `<div class=gcard><h4>${label}</h4><div class=hsub style=margin:0>${sub||""}</div>
  <svg viewBox="0 0 ${w} ${h}" style=max-width:220px>
   ${arc(Math.PI,0,"#e6eaee",13)}${arc(Math.PI,ang,col,13)}
   <line x1=${cx} y1=${cy} x2=${x.toFixed(1)} y2=${y.toFixed(1)} stroke="${col}" stroke-width=3/>
   <circle cx=${cx} cy=${cy} r=5 fill="${col}"/>
   <text x=${cx} y=${cy-14} text-anchor=middle font-size=30 font-weight=700 fill="${col}">${pct==null?"—":v.toFixed(0)}</text>
   <text x=${cx} y=${cy+12} text-anchor=middle font-size=12 fill=#6b7480>capture %</text></svg></div>`;}
const tip=document.getElementById("tip");
function showTip(h,e){tip.innerHTML=h;tip.style.display="block";const p=14,w=tip.offsetWidth,ht=tip.offsetHeight;
 let x=e.clientX+p,y=e.clientY+p;if(x+w>innerWidth)x=e.clientX-w-p;if(y+ht>innerHeight)y=e.clientY-ht-p;tip.style.left=x+"px";tip.style.top=y+"px";}
function hideTip(){tip.style.display="none";}
function mk(t,a,txt){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;return e;}
function clear(s){while(s.firstChild)s.removeChild(s.firstChild);}
function hoverX(svg,xs,rows){svg.onmousemove=e=>{const r=svg.getBoundingClientRect(),vx=(e.clientX-r.left)/r.width*720;
 let bi=0,bd=1e9;for(let i=0;i<xs.length;i++){const dd=Math.abs(xs[i]-vx);if(dd<bd){bd=dd;bi=i;}}showTip(rows[bi],e);};svg.onmouseleave=hideTip;}
function line(svg,sets,ymax,xl,unit,labels){const W=720,H=svg.viewBox.baseVal.height,L=58,R=16,TT=16,B=44,pw=W-L-R,ph=H-TT-B,n=sets[0].pts.length;
 clear(svg);const g=mk("g",{"font-size":13,fill:"#8a93a0"});
 for(let i=0;i<=4;i++){const y=TT+ph*i/4;g.appendChild(mk("line",{x1:L,y1:y,x2:W-R,y2:y,stroke:"#eef1f4"}));g.appendChild(mk("text",{x:L-9,y:y+5,"text-anchor":"end"},(ymax*(1-i/4)).toFixed(0)+unit));}
 xl.forEach((lb,i)=>{if(lb)g.appendChild(mk("text",{x:L+(n>1?pw*i/(n-1):0),y:H-15,"text-anchor":"middle"},lb));});svg.appendChild(g);
 const X=i=>L+(n>1?pw*i/(n-1):0),Y=v=>TT+ph*(1-Math.min(Math.max(Number(v)||0,0),ymax)/ymax);
 for(const set of sets){const dd=set.pts.map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1)).join(" ");
  svg.appendChild(mk("path",{d:dd,fill:"none",stroke:set.color,"stroke-width":set.w||2.6,"stroke-dasharray":set.dash||""}));}
 const xs=[],rows=[];for(let i=0;i<n;i++){xs.push(X(i));let rr=`<b>${(labels&&labels[i])||xl[i]||i}</b>`;
  for(const set of sets)rr+=`<br><span style="color:${set.color}">●</span> ${set.name}: ${(Number(set.pts[i])||0).toFixed(1)}${unit}`;rows.push(rr);}hoverX(svg,xs,rows);}
function bars(svg,bs,ymax,unit){const W=720,H=svg.viewBox.baseVal.height,L=58,R=16,TT=16,B=50,pw=W-L-R,ph=H-TT-B;
 clear(svg);const g=mk("g",{"font-size":13,fill:"#8a93a0"});
 for(let i=0;i<=4;i++){const y=TT+ph*i/4;g.appendChild(mk("line",{x1:L,y1:y,x2:W-R,y2:y,stroke:"#eef1f4"}));g.appendChild(mk("text",{x:L-9,y:y+5,"text-anchor":"end"},(ymax*(1-i/4)).toFixed(1)));}svg.appendChild(g);
 const bw=pw/bs.length*0.5;bs.forEach((b,i)=>{const cx=L+pw*(i+.5)/bs.length,h=ph*Math.min(b.v,ymax)/ymax,y=TT+ph-h;
  svg.appendChild(mk("rect",{x:cx-bw/2,y:y,width:bw,height:h,rx:3,fill:b.color}));
  svg.appendChild(mk("text",{x:cx,y:H-30,"text-anchor":"middle","font-size":13,fill:"#46505f"},b.label));
  svg.appendChild(mk("text",{x:cx,y:y-7,"text-anchor":"middle","font-size":13,fill:"#46505f","font-weight":700},b.v.toFixed(1)));});}
function dcls(d){const a=Math.abs(d);return a<5?"good":a<15?"ok":"bad";}
function numcell(v,cls){return `<td class="num ${cls||''}">${v}</td>`;}
// ---- SUMMARY ----
function renderGauges(){const wrap=document.getElementById("gauges");let h="";
 for(const grp of D.groups){const cards=D.model.map((run,ri)=>{const m=classMetrics(ri,st.year,grp);
   if(!m)return "";return `<div class=runblk>
    <div style="font-weight:600;font-size:13px;color:#46505f;margin:0 0 6px">${run.label}</div>
    <div class=grow>${gauge(m.m1,"Class","shape & level")}${gauge(m.m2,"Plant","merit order")}</div></div>`;}).join("");
  if(cards.replace(/\s/g,""))h+=`<h3>${D.groupLabel[grp]}</h3><div class=gaugegrid>${cards}</div>`;}
 wrap.innerHTML=h||"<p class=hsub>No plants in the selected zones.</p>";}
function renderFuelTable(){let body="";const years=D.years;
 // per run: system fuel rows (zone filter does not apply to EIA-930)
 let h="<table><thead><tr><th>fuel</th>"+D.model.map(r=>`<th>${r.label} Δ</th>`).join("")+"<th>EIA-930</th></tr></thead><tbody>";
 for(const yr of years){h+=`<tr class=sumrow><td colspan=${D.model.length+2}>${yr}</td></tr>`;
  const fuels=["gas","coal","nuclear","wind","solar"];
  for(const f of fuels){let row=`<tr><td class=lbl>${f}</td>`;let b=null;
   for(const run of D.model){const fr=(run.years[yr]?.fuelRows||[]).find(x=>x.fuel===f);
    if(!fr||fr.b==null){row+="<td class=num>—</td>";continue;}b=fr.b;const d=100*(fr.m-fr.b)/fr.b;
    row+=numcell((d>=0?"+":"")+d.toFixed(1)+"%",dcls(d));}
   row+=numcell(b==null?"—":b.toFixed(1));h+=row+"</tr>";}}
 h+="</tbody></table>";document.getElementById("tblFuel").innerHTML=h;}
function renderFossilTable(){let h="<table><thead><tr><th>class</th><th>year</th>"
  +D.model.map(r=>`<th>${r.label} Δ923</th><th>r</th><th>NRMSE</th>`).join("")+"</tr></thead><tbody>";
 for(const grp of D.groups){for(const yr of D.years){let any=false;let row=`<tr><td class=lbl>${D.groupLabel[grp]}</td><td>${yr}</td>`;
   for(let ri=0;ri<D.model.length;ri++){const m=classMetrics(ri,yr,grp);
    if(!m){row+="<td class=num>—</td><td class=num>—</td><td class=num>—</td>";continue;}any=true;
    const bench=m.bench923;const dd=bench>0.02?100*(m.mAnn-bench)/bench:null;
    row+=numcell(dd==null?"—":(dd>=0?"+":"")+dd.toFixed(1),dd==null?"":dcls(dd));
    row+=numcell(m.r!=null?m.r.toFixed(3):"—");row+=numcell(m.nr!=null?m.nr.toFixed(3):"—");}
   if(any)h+=row+"</tr>";}}
 h+="</tbody></table>";document.getElementById("tblFossil").innerHTML=h;}
function renderPlantTable(){const years=D.years.filter(y=>y!==2025);
 let h="<table><thead><tr><th>plant</th><th>class</th><th>year</th>"
  +D.model.map(r=>`<th>${r.label} Δ923%</th>`).join("")+"</tr></thead><tbody>";
 // union of plants across runs in selected zones
 for(const yr of years){const B=D.bench[yr];if(!B)continue;
  const codes=Object.keys(B.plants).filter(c=>st.zones.has(B.plants[c].zone)&&B.plants[c].e_ann>0.001)
   .sort((a,b)=>B.plants[a].group.localeCompare(B.plants[b].group)||B.plants[a].zone.localeCompare(B.plants[b].zone));
  for(const c of codes){const b=B.plants[c];let row=`<tr><td class=lbl>${c}</td><td class=lbl>${D.groupLabel[b.group]||b.group}</td><td>${yr}</td>`;
   for(const run of D.model){const mp=run.years[yr]?.plants[c];if(!mp){row+="<td class=num>—</td>";continue;}
    const d=100*(mp.m_ann-b.e_ann)/b.e_ann;row+=numcell((d>=0?"+":"")+d.toFixed(0),dcls(d));}
   h+=row+"</tr>";}}
 h+="</tbody></table>";document.getElementById("tblPlant").innerHTML=h;}
function renderSummaryCharts(){const grp=st.sumClass,yr=st.year;
 const mon=D.model.map((run,ri)=>{const ps=plantsOf(ri,yr,grp);const a=new Array(12).fill(0);
   for(const c of ps){run.years[yr].plants[c].m_mon.forEach((v,i)=>a[i]+=v);}return {label:run.label,pts:a};});
 const B=D.bench[yr];const camp=new Array(12).fill(0);if(B)plantsOf(0,yr,grp).forEach(c=>B.plants[c].c_mon.forEach((v,i)=>camp[i]+=v));
 const sets=mon.map((m,i)=>({pts:m.pts,color:RC[i%RC.length],name:m.label,dash:"4 3"}));
 sets.push({pts:camp,color:"#2f9bd6",name:"CAMPD",w:3});
 const ymax=Math.max(1,...sets.flatMap(s=>s.pts))*1.15;
 line(document.getElementById("sumMonthly"),sets,ymax,MONTHS,"",MONTHS);
 document.getElementById("legMon").innerHTML=sets.map(s=>`<span><i class=swatch style="border-top-color:${s.color}"></i><b>${s.name}</b></span>`).join("");
 // annual bars: per-run model + CAMPD + EIA
 const bs=D.model.map((run,ri)=>{const ps=plantsOf(ri,yr,grp);let a=0;ps.forEach(c=>a+=run.years[yr].plants[c].m_ann);return {label:run.label,v:a,color:RC[ri%RC.length]};});
 let cAnn=0,eAnn=0;if(B)plantsOf(0,yr,grp).forEach(c=>{cAnn+=B.plants[c].c_ann;eAnn+=B.plants[c].e_ann;});
 bs.push({label:"CAMPD",v:cAnn,color:"#2f9bd6"});bs.push({label:"EIA-923",v:eAnn,color:"#2e9e5b"});
 bars(document.getElementById("sumAnnual"),bs,Math.max(0.1,...bs.map(b=>b.v))*1.25," TWh");}
function renderSummary(){renderGauges();renderFuelTable();renderFossilTable();renderPlantTable();renderSummaryCharts();}
// ---- DETAIL ----
const MM=["00","06","12","18","23"];
function cfColor(v){if(v<=1)return[232,243,247];const t=Math.min(v,100)/100,
 S=[[0,232,243,247],[.04,127,196,230],[.30,134,201,143],[.55,242,214,92],[.78,239,143,60],[1,192,57,43]];
 for(let i=1;i<S.length;i++)if(t<=S[i][0]){const a=S[i-1],b=S[i],f=(t-a[0])/(b[0]-a[0]);return[a[1]+f*(b[1]-a[1]),a[2]+f*(b[2]-a[2]),a[3]+f*(b[3]-a[3])];}return[192,57,43];}
function drawHeat(cv,cf){const x=cv.getContext("2d"),im=x.createImageData(365,24);
 for(let h=0;h<8760;h++){const day=h/24|0,hod=h%24;if(day>364)break;const c=cfColor(cf[h]),i=(hod*365+day)*4;im.data[i]=c[0];im.data[i+1]=c[1];im.data[i+2]=c[2];im.data[i+3]=255;}x.putImageData(im,0,0);}
function profileArr(cf){const o=Array(24).fill(0),n=Array(24).fill(0);for(let h=0;h<8760;h++){o[h%24]+=cf[h];n[h%24]++;}return o.map((v,i)=>n[i]?v/n[i]:0);}
function detailPlants(){const ri=st.run,yr=st.year,grp=st.group;return plantsOf(ri,yr,grp);}
function fillPlants(){const ps=detailPlants();const B=D.bench[st.year];
 plantSel.innerHTML=`<option value=agg>Aggregate (${ps.length} plants)</option>`+ps.map(c=>`<option value=${c}>${c} · ${B.plants[c].zone}</option>`).join("");
 if(![...plantSel.options].some(o=>o.value===st.plant)){st.plant="agg";}plantSel.value=st.plant;}
function detailSeries(){const ri=st.run,yr=st.year,grp=st.group,B=D.bench[yr],M=D.model[ri].years[yr];
 if(st.plant!=="agg"&&M.plants[st.plant]){const b=B.plants[st.plant],mp=M.plants[st.plant];
  return {mcf:dec(mp.m),ccf:dec(b.campd),npl:b.npl,name:st.plant+" · "+b.zone,
   m_ann:mp.m_ann,c_ann:b.c_ann,e_ann:b.e_ann,r:mp.r,nr:mp.nrmse,cap:mp.cap,
   m_mon:mp.m_mon,c_mon:b.c_mon,e_mon:b.e_mon};}
 const a=aggMW(ri,yr,grp);const mcf=new Float32Array(T),ccf=new Float32Array(T);let npl=0;
 for(const c of detailPlants())npl+=B.plants[c].npl;
 for(let i=0;i<T;i++){mcf[i]=npl>0?100*a.mm[i]/npl:0;ccf[i]=npl>0?100*a.cc[i]/npl:0;}
 const m_mon=Array(12).fill(0),c_mon=Array(12).fill(0),e_mon=Array(12).fill(0);
 for(const c of detailPlants()){M.plants[c].m_mon.forEach((v,i)=>m_mon[i]+=v);B.plants[c].c_mon.forEach((v,i)=>c_mon[i]+=v);B.plants[c].e_mon.forEach((v,i)=>e_mon[i]+=v);}
 const mt=classMetrics(ri,yr,grp);
 return {mcf,ccf,npl,name:D.groupLabel[grp]+" (aggregate)",m_ann:a.mAnn,c_ann:a.cAnn,e_ann:a.eAnn,
  r:mt?+mt.r.toFixed(3):null,nr:mt?+mt.nr.toFixed(3):null,cap:mt?mt.m1:null,m_mon,c_mon,e_mon};}
function renderDetail(){const mt=classMetrics(st.run,st.year,st.group);
 document.getElementById("dGauge1").innerHTML=gauge(mt?mt.m1:null,"Class capture","shape & level vs CAMPD");
 document.getElementById("dGauge2").innerHTML=gauge(mt?mt.m2:null,"Plant capture","merit order (cap-wtd)");
 const d=detailSeries();const dl=d.e_ann?100*(d.m_ann-d.e_ann)/d.e_ann:null;
 kpi.innerHTML=[["Model TWh",d.m_ann.toFixed(2)],["CAMPD TWh",d.c_ann.toFixed(2)],["EIA-923 TWh",d.e_ann.toFixed(2)],
  ["Δ vs 923",dl==null?"—":(dl>=0?"+":"")+dl.toFixed(1)+"%"],["r / NRMSE",(d.r??"—")+" / "+(d.nr??"—")]]
  .map(k=>`<div class=kpi><div class=kpik>${k[0]}</div><div class=kpiv>${k[1]}</div></div>`).join("");
 heatSub.textContent=`24h × 365d — ${d.name} — ${st.year} — ${d.npl.toLocaleString()} MW`;
 drawHeat(heatC,d.ccf);drawHeat(heatM,d.mcf);axC.innerHTML=axM.innerHTML=MONTHS.map(m=>`<span>${m}</span>`).join("");
 const pc=profileArr(d.ccf),pm=profileArr(d.mcf);const xl=Array(24).fill("");[0,6,12,18,23].forEach(h=>xl[h]=("0"+h).slice(-2));
 dispSub.textContent=d.name;
 line(document.getElementById("profile"),[{pts:pc,color:"#2f9bd6",name:"CAMPD"},{pts:pm,color:"#ef7d2b",name:"Model",dash:"4 3"}],
  Math.max(40,...pc,...pm)*1.1,xl,"%",Array.from({length:24},(_,h)=>("0"+h).slice(-2)+":00"));
 const ms=[{pts:d.c_mon,color:"#2f9bd6",name:"CAMPD"},{pts:d.m_mon,color:"#ef7d2b",name:"Model",dash:"4 3"}];
 if(d.e_mon&&d.e_mon.some(v=>v>0))ms.push({pts:d.e_mon,color:"#2e9e5b",name:"EIA-923",dash:"1 4"});
 line(document.getElementById("monthly"),ms,Math.max(1,...d.c_mon,...d.m_mon)*1.15,MONTHS,"",MONTHS);}
// ---- shell ----
function render(){if(st.page==="summary")renderSummary();else{fillPlants();renderDetail();}}
function build(){
 pageSel.innerHTML='<button data-p=summary class=on>Summary</button><button data-p=detail>Detail</button>';
 pageSel.onclick=e=>{const p=e.target.dataset.p;if(!p)return;st.page=p;[...pageSel.children].forEach(b=>b.classList.toggle("on",b.dataset.p===p));
  document.getElementById("summary-view").classList.toggle("hide",p!=="summary");document.getElementById("detail-view").classList.toggle("hide",p!=="detail");render();};
 yearSel.innerHTML=D.years.map(y=>`<button data-y=${y} class=${y==st.year?"on":""}>${y}</button>`).join("");
 yearSel.onclick=e=>{if(e.target.dataset.y){st.year=+e.target.dataset.y;[...yearSel.children].forEach(b=>b.classList.toggle("on",+b.dataset.y===st.year));render();}};
 zoneSel.innerHTML=`<span class="chip on" data-z=__all>All</span>`+D.zones.map(z=>`<span class="chip on" data-z="${z}">${z}</span>`).join("");
 zoneSel.onclick=e=>{const z=e.target.dataset.z;if(!z)return;
  if(z==="__all"){st.zones=new Set(D.zones);}else{if(st.zones.has(z))st.zones.delete(z);else st.zones.add(z);if(!st.zones.size)st.zones=new Set(D.zones);}
  [...zoneSel.children].forEach(c=>{const zz=c.dataset.z;c.classList.toggle("on",zz==="__all"?st.zones.size===D.zones.length:st.zones.has(zz));});render();};
 runSel.innerHTML=D.runLabels.map((l,i)=>`<option value=${i}>${l}</option>`).join("");runSel.onchange=()=>{st.run=+runSel.value;render();};
 groupSel.innerHTML=D.groups.map(g=>`<option value=${g}>${D.groupLabel[g]}</option>`).join("");groupSel.onchange=()=>{st.group=groupSel.value;render();};
 plantSel.onchange=()=>{st.plant=plantSel.value;renderDetail();};
 sumClass.innerHTML=D.groups.map(g=>`<option value=${g}>${D.groupLabel[g]}</option>`).join("");sumClass.onchange=()=>{st.sumClass=sumClass.value;renderSummaryCharts();};
}
async function boot(){
 try{
  const b64=document.getElementById("payload").textContent.trim();
  const bin=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));
  if(typeof DecompressionStream==="undefined")throw new Error("browser lacks DecompressionStream — use a current browser");
  const ds=new DecompressionStream("gzip");
  const ab=await new Response(new Blob([bin]).stream().pipeThrough(ds)).arrayBuffer();
  D=JSON.parse(new TextDecoder().decode(ab));
  st={page:"summary",year:D.years[0],zones:new Set(D.zones),
      run:0,group:D.groups[0],plant:"agg",sumClass:D.groups[0]};
  build();render();diag.style.display="none";
 }catch(e){diag.style.color="#c01c28";diag.style.borderColor="#c01c28";
  diag.textContent="Render error: "+((e&&e.message)||e)+" "+(e&&e.stack||"");}
}
boot();
</script></div></body></html>"""


if __name__ == "__main__":
    main()
