"""R-SPP phase-0 zero-LP census: the incumbent SPP keeper recipe vs the R-SPP recipe, per year.

Executes ``docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md`` §5.3.9 step 0.
No LP is built or solved: every number is a ``run_year(..., fleet_only=True)`` rebuild from the
sanctioned ``bundle_fleet.full_run_year_kwargs`` (the same reconstruction ``replay_keeper.py``
uses), plus direct reads of the committed CAMPD outage extracts.

Variants (one interpreter each, so the process-global EIA-860 vintage never leaks):

* ``ctl`` — the incumbent recipe with every ``measured_*_heat_rates`` flag and
  ``unit_partial_outage_windows`` forced **False**: the F1 eGRID-year-matched layer alone.
* ``arm`` — the R-SPP recipe: the incumbent recipe + all five measured flags True +
  ``unit_partial_outage_windows`` True (``eia860_vintage_tracks_solve_year`` already True).

Per year and variant it writes the thermal rows (plant, class, heat rate, pmax, mean availability)
and the active EIA-860 directory; ``--summarize`` then reports (a) the vintage resolved, (b) thermal
MW at a class-table heat rate (EXACT measure: the plant's active source row carries no joined eGRID
heat rate AND no measured artifact row the loader applies — listed per plant), (c) outage windows /
MW-h per family by start year, and the availability MWh the partial family removes.

Usage::

    uv run python scripts/probes/_rspp_phase0_census.py --year 2022 --variant arm --out d
    uv run python scripts/probes/_rspp_phase0_census.py --summarize d
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLES = {
    **{y: "hydro5_spp_floor_rung" for y in (2019, 2020, 2021, 2022)},
    **{y: "hydro5_spp_floor_span" for y in (2023, 2024, 2025)},
}
HR_FIELDS = (
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
)
ARM_FIELDS = HR_FIELDS + ("unit_partial_outage_windows",)
THERMAL_GROUPS = (
    "COAL",
    "CC_REGULAR",
    "CC_CHP",
    "ST_GAS",
    "ST_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "OIL",
)
PROCESSED = REPO / "data/raw/_processed-legacy"
RAW = REPO / "data/raw"
# measured artifact -> the plant_groups it prices (loader scope; CHP rows carry their own group)
ARTIFACTS = {
    "campd_ct_heat_rates_SPP.csv": ("CT_PEAKER",),
    "campd_coal_heat_rates_SPP.csv": ("COAL",),
    "campd_st_heat_rates_SPP.csv": ("ST_GAS",),
    "campd_cc_heat_rates_SPP.csv": ("CC_REGULAR",),
}
OUTAGE_FILES = {
    "std": "campd-unit-outages-SPP.csv",
    "short_coal": "campd-unit-outages-short-SPP.csv",
    "short_gas": "campd-unit-outages-shortgas-SPP.csv",
    "partial": "campd-partial-outages-SPP.csv",
}


def build(year: int, variant: str, out: Path) -> None:
    """Rebuild the year's fleet (no LP) and write per-row thermal state + provenance."""
    from market_sim.config.paths import active_eia860_dir
    from scripts.lib.bundle_fleet import bundle_gas_price, full_run_year_kwargs
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / BUNDLES[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = full_run_year_kwargs(meta)
    pov = dict(kw.get("prb_overrides") or {})
    val = variant == "arm"
    for f in ARM_FIELDS:
        pov[f] = val
        if f in kw:
            kw[f] = val
    kw["prb_overrides"] = pov
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(bundle, year),
    )
    cfg = state["config"]
    got = {f: bool(getattr(cfg, f)) for f in ARM_FIELDS}
    if any(v != val for v in got.values()):
        raise SystemExit(f"HARD STOP: {variant} config flags {got}")
    if not cfg.eia860_vintage_tracks_solve_year:
        raise SystemExit("HARD STOP: eia860_vintage_tracks_solve_year is off")
    fa = state["fleet_arrays"]
    av = np.asarray(fa.availability, float)
    df = pd.DataFrame(
        {
            "unit_id": [str(u) for u in fa.unit_ids],
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "plant_group": [str(g) for g in fa.plant_group],
            "heat_rate": np.asarray(fa.heat_rate, float),
            "pmax": np.asarray(fa.pmax, float),
            "avail_mean": av.mean(axis=1) if av.ndim == 2 else av,
        }
    )
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / f"{variant}_{year}.parquet")
    info = {
        "year": year,
        "variant": variant,
        "active_eia860_dir": str(Path(active_eia860_dir()).relative_to(REPO)),
        "flags": got,
        "eia860_vintage_tracks_solve_year": bool(cfg.eia860_vintage_tracks_solve_year),
        "mid_vintage_exit_carry": bool(getattr(cfg, "mid_vintage_exit_carry", False)),
        "unit_outage_short_windows": bool(cfg.unit_outage_short_windows),
        "unit_outage_short_windows_gas": bool(cfg.unit_outage_short_windows_gas),
        "rows": int(len(df)),
    }
    (out / f"{variant}_{year}.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))


def _null_plants(src_dir: Path) -> set[int]:
    """SPP plant codes whose active EIA-860 generator rows carry no joined eGRID heat rate."""
    from market_sim.data.fleet.eia860 import ba_codes

    df = pd.read_parquet(src_dir / "eia860_generators.parquet")
    codes = ba_codes("SPP")
    if codes and "balancing_authority_code" in df.columns:
        df = df[df["balancing_authority_code"].astype(str).str.strip().isin(codes)]
    hr = (
        pd.to_numeric(df.get("heat_rate"), errors="coerce")
        if "heat_rate" in df
        else None
    )
    ids = pd.to_numeric(df["plant_id"], errors="coerce")
    if hr is None:
        return set(ids.dropna().astype(int))
    return set(ids[hr.isna() | (hr <= 0)].dropna().astype(int))


def _measured_cover(year: int) -> set[tuple[int, str]]:
    """(plant, group) the loader prices from a measured artifact in ``year`` (own-year ok, else pooled ok)."""
    cov: set[tuple[int, str]] = set()
    for f, groups in ARTIFACTS.items():
        d = pd.read_csv(PROCESSED / f)
        d = d[(d.flag == "ok") & (d.heat_rate > 0) & d.year.isin([0, year])]
        for p in d.plant_code.astype(int).unique():
            for g in groups:
                cov.add((int(p), g))
    chp = pd.read_csv(PROCESSED / "chp_power_only_heat_rates_SPP.csv")
    chp = chp[(chp.flag == "ok") & chp.year.isin([0, year])]
    for r in chp.itertuples():
        cov.add((int(r.plant_code), str(r.plant_group)))
    return cov


def _outage_census() -> dict:
    """Windows and removed MW-h by family and start year, straight from the committed extracts."""
    res = {}
    for fam, fname in OUTAGE_FILES.items():
        path = RAW / fname
        d = pd.read_csv(path)
        start = pd.to_datetime(d[[c for c in d.columns if "start" in c.lower()][0]])
        end = pd.to_datetime(d[[c for c in d.columns if "end" in c.lower()][0]])
        hours = (end - start).dt.total_seconds() / 3600.0
        capcol = next(
            (c for c in ("unit_capacity_mw", "capacity_mw") if c in d.columns), None
        )
        mw = (
            pd.to_numeric(d[capcol], errors="coerce")
            if capcol
            else pd.Series(np.nan, index=d.index)
        )
        if "derate_factor" in d.columns:
            mw = mw * (1.0 - pd.to_numeric(d["derate_factor"], errors="coerce"))
        import hashlib

        res[fam] = {
            "file": f"data/raw/{fname}",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "by_year": {
                int(y): {
                    "windows": int((start.dt.year == y).sum()),
                    "gwh": round(
                        float((mw * hours)[start.dt.year == y].sum()) / 1e3, 1
                    ),
                }
                for y in range(2019, 2026)
            },
        }
    return res


def summarize(d: Path) -> dict:
    """Assemble the census from the per-year parquet/json pairs."""
    out: dict = {"years": {}, "outages": _outage_census()}
    for y in range(2019, 2026):
        row: dict = {}
        for v in ("ctl", "arm"):
            pq = d / f"{v}_{y}.parquet"
            if not pq.exists():
                continue
            info = json.loads((d / f"{v}_{y}.json").read_text())
            df = pd.read_parquet(pq)
            th = df[df.plant_group.isin(THERMAL_GROUPS)]
            null = _null_plants(REPO / info["active_eia860_dir"])
            cover = _measured_cover(y) if v == "arm" else set()
            is_ct = th.apply(
                lambda r: (
                    r.plant_code in null and (r.plant_code, r.plant_group) not in cover
                ),
                axis=1,
            )
            per_class = {}
            for g, s in th.groupby("plant_group"):
                per_class[g] = {
                    "mw": round(float(s.pmax.sum()), 1),
                    "hr_cw": round(float(np.average(s.heat_rate, weights=s.pmax)), 4)
                    if s.pmax.sum() > 0
                    else None,
                    "avail_mwh_twh": round(
                        float((s.pmax * s.avail_mean).sum() * 8760 / 1e6), 3
                    ),
                }
            plants = (
                th[is_ct]
                .groupby(["plant_code", "plant_group"])
                .pmax.sum()
                .round(1)
                .reset_index()
                .sort_values("pmax", ascending=False)
            )
            row[v] = {
                "active_eia860_dir": info["active_eia860_dir"],
                "mid_vintage_exit_carry": info["mid_vintage_exit_carry"],
                "thermal_mw": round(float(th.pmax.sum()), 1),
                "class_table_mw": round(float(th.pmax[is_ct].sum()), 1),
                "class_table_plants": plants.to_dict("records"),
                "per_class": per_class,
            }
        out["years"][y] = row
    return out


def main() -> int:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int)
    ap.add_argument("--variant", choices=("ctl", "arm"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--summarize", type=Path)
    args = ap.parse_args()
    if args.summarize:
        res = summarize(args.summarize)
        (args.summarize / "summary.json").write_text(
            json.dumps(res, indent=1, default=str)
        )
        print(json.dumps(res, default=str)[:4000])
        return 0
    build(args.year, args.variant, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
