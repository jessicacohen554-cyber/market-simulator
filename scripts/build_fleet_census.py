"""Per ISO-year fleet census: what the LP carried vs EIA-860 vs the ISO's report.

W0 E.7 (owner ruling R-2 / Q8, 2026-10-02; audit
``docs/records/governance/closeout-2026-10/AUDIT-eia860-capacity-vintage-settlement-2026-10-02.md``
§E.7). One script, one ledger: ``fleet_census_<Y>.json`` per ISO-year, committed
in every keeper bundle and refused by ``scripts/promote_keeper.py`` preflight
when absent. Zero LP.

Rows, one per thermal family (COAL / CC / CT / ST_GAS / NUCLEAR / OIL /
BIOMASS / OTHER) plus a TOTAL_THERMAL row (BIOMASS and OTHER are reported
but unscored: most ISOs carry them as EIA-923-injected must-run classes, not
LP capacity, so they sit outside the tolerance total):

* ``eia860_nameplate_mw`` / ``eia860_summer_mw`` / ``eia860_winter_mw`` — the
  solved year's own vintage (``vintage_<Y>/``), status ``OP`` + ``SB`` (E.4),
  the region's load-time footprint (BA code + NWPP's NERC key, E.6);
* ``model_pmax_mw`` — Σ pmax of the LP units online at any point in Y;
* ``model_summer_mw`` / ``model_winter_mw`` — the LP's seasonal capability
  (pmax × the unit's published seasonal share under the W0 basis, × its COD
  online fraction in July / January); outages excluded, so it is commensurable
  with the published ratings;
* ``model_available_jul_mw`` / ``model_available_jan_mw`` — mean Σ pmax ×
  availability over the month's hours (outages included);
* ``iso_report_mw`` + ``iso_report_basis`` — null until the ISO's own report
  is on disk (audit §F 6-13), stated rather than guessed;
* ``delta_summer_pct`` / ``delta_winter_pct`` vs EIA-860 and the verdicts
  against the ruled tolerances (1 % per family, 0.5 % total thermal; 3 % vs
  the ISO report after the stated basis translation).

Every family outside tolerance carries its explained residual rows: the plants
whose model-minus-860 MW accounts for the gap, each with a mechanical reason
(``not carried``, ``carried, not OP/SB in the vintage``, ``rating differs``).

Two further zero-LP measurements ride along because the ruling asks for them
to be reported, never fitted: the ``OA``/``OS`` envelope (plants in the
footprint whose every vintage unit is out of service — the population the
EIA-923 benchmark may count while the fleet does not, E.4) and the MW of
operable units whose ``Planned Retirement`` falls in or before Y (E.5: must
be 0 under year-matched vintages).

Model sources (exactly one):

* ``--bundle DIR`` — a registered bundle's committed
  ``hourly/unit_marginal_<Y>.parquet`` (the rule-15 slim layer);
* ``--rebuild DIR`` — a zero-LP ``run_year(fleet_only=True)`` rebuild of the
  bundle's recipe (``replay_keeper.run_year_kwargs``), at ``--posture w0``
  (every W0 field armed: the settlement posture) or ``--posture recorded``
  (each W0 field at its recorded value, else its registration-time default:
  the bundle as it was solved).

``--ercot-csv-audit`` adds the Q5 per-vintage audit of ERCOT's curated bin
sheet: thermal plants in the vintage's ERCO footprint absent from the sheet,
and sheet plants absent from the vintage.

Usage::

    python scripts/build_fleet_census.py --iso MISO --year 2023 \\
        --rebuild results/calibration/miso280_span --posture w0 \\
        --out results/calibration/miso280_span/fleet_census_2023.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
for _p in (".", "scripts", "src"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

#: Ruled tolerances (owner ruling R-2 / Q8): |Δ| vs the EIA-860 season rating.
TOL_FAMILY_PCT = 1.0
TOL_TOTAL_PCT = 0.5
#: |Δ| vs the ISO's own report, after the stated basis translation.
TOL_ISO_REPORT_PCT = 3.0

#: Thermal families the census reports, in display order.
FAMILIES: tuple[str, ...] = (
    "COAL",
    "CC",
    "CT",
    "ST_GAS",
    "NUCLEAR",
    "OIL",
    "BIOMASS",
    "OTHER",
)

#: EIA-860 ``Technology`` string -> census family. Anything thermal not listed
#: is ``OTHER``; non-thermal technologies (wind, solar, hydro, storage,
#: geothermal) are out of the census by construction.
_TECH_FAMILY: dict[str, str] = {
    "Conventional Steam Coal": "COAL",
    "Coal Integrated Gasification Combined Cycle": "COAL",
    "Natural Gas Fired Combined Cycle": "CC",
    "Natural Gas Fired Combustion Turbine": "CT",
    "Natural Gas Internal Combustion Engine": "CT",
    "Natural Gas Steam Turbine": "ST_GAS",
    "Natural Gas with Compressed Air Storage": "OTHER",
    "Nuclear": "NUCLEAR",
    "Petroleum Liquids": "OIL",
    "Petroleum Coke": "OTHER",
    "Wood/Wood Waste Biomass": "BIOMASS",
    "Municipal Solid Waste": "BIOMASS",
    "Landfill Gas": "BIOMASS",
    "Other Waste Biomass": "BIOMASS",
    "Other Gases": "OTHER",
    "Other Natural Gas": "OTHER",
    "All Other": "OTHER",
}

#: The W0 fields a ``--posture w0`` rebuild arms (scenarios._W0_BACKCAST_DEFAULT_FIELDS).
_ADMITTED_STATUSES = frozenset({"OP", "SB"})
_OUT_OF_SERVICE = frozenset({"OA", "OS"})
_JULY_HOUR = 24 * 196  # mid-July (day-of-year 197, 0-based hour)
_JANUARY_HOUR = 24 * 15  # mid-January


#: LP fuels that are not thermal generating capacity (out of the census).
_NON_THERMAL_FUELS: frozenset[str] = frozenset(
    {"import", "hydro", "wind", "solar", "storage", "battery", "pumped_storage"}
)

#: Families the model represents as EIA-923-INJECTED must-run classes rather
#: than LP capacity in most ISOs: reported, but outside the tolerance total.
INJECTED_FAMILIES: frozenset[str] = frozenset({"BIOMASS", "OTHER"})


def model_family(plant_group: str, fuel: str) -> str | None:
    """Census family of one LP unit from its plant group, else its fuel.

    ``None`` for a non-thermal LP unit (imports, hydro, renewables, storage).
    """
    g = str(plant_group or "")
    f = str(fuel or "")
    if f in _NON_THERMAL_FUELS:
        return None
    if g.startswith("COAL") or f == "coal":
        return "COAL"
    if g in ("CC_REGULAR", "CC_CHP") or f in ("gas_cc", "gas_cc_ccs"):
        return "CC"
    if g in ("CT_PEAKER", "CT_CHP") or f == "gas_ct":
        return "CT"
    if g in ("ST_GAS", "ST_CHP") or f == "gas_st":
        return "ST_GAS"
    if f == "nuclear":
        return "NUCLEAR"
    if f == "oil":
        return "OIL"
    if f == "biomass":
        return "BIOMASS"
    return "OTHER"


def _vintage_dir(year: int) -> Path:
    """The EIA-860 directory the solved year reads (vintage, else canonical)."""
    from market_sim.config.paths import EIA_860_DIR

    candidate = EIA_860_DIR / f"vintage_{int(year)}"
    return candidate if candidate.is_dir() else EIA_860_DIR


def eia860_vintage_frame(iso: str, year: int) -> pd.DataFrame:
    """The ISO's thermal EIA-860 rows of the solved year's vintage, all statuses.

    Columns: ``plant, gen, family, status, nameplate, summer, winter,
    planned_ret_year``. Footprint = the plant sheet's BA code (+ NWPP's NERC
    key), applied at load time exactly as the fleet does (E.6).
    """
    from market_sim.data.fleet.models import footprint_plant_mask

    vdir = _vintage_dir(year)
    op = pd.read_parquet(vdir / "eia860_generator_operable.parquet")
    op.columns = [str(c).strip() for c in op.columns]
    plant = pd.read_parquet(vdir / "eia860_plant.parquet")
    plant.columns = [str(c).strip() for c in plant.columns]
    plant["_pc"] = pd.to_numeric(plant["Plant Code"], errors="coerce")
    plant = plant.dropna(subset=["_pc"]).drop_duplicates("_pc")
    nerc = plant["NERC Region"] if "NERC Region" in plant.columns else None
    keep = footprint_plant_mask(iso, plant["Balancing Authority Code"], nerc)
    plants = set(plant.loc[keep, "_pc"].astype(int))
    pc = pd.to_numeric(op["Plant Code"], errors="coerce")
    op = op[pc.isin(plants)].copy()
    fam = op["Technology"].astype(str).str.strip().map(_TECH_FAMILY)
    op = op[fam.notna()].copy()
    return pd.DataFrame(
        {
            "plant": pd.to_numeric(op["Plant Code"], errors="coerce").astype(int),
            "gen": op["Generator ID"].astype(str).str.strip(),
            "family": fam[fam.notna()].values,
            "status": op["Status"].astype(str).str.strip().str.upper(),
            "nameplate": pd.to_numeric(op["Nameplate Capacity (MW)"], errors="coerce"),
            "summer": pd.to_numeric(op["Summer Capacity (MW)"], errors="coerce"),
            "winter": pd.to_numeric(op.get("Winter Capacity (MW)"), errors="coerce"),
            "planned_ret_year": pd.to_numeric(
                op.get("Planned Retirement Year"), errors="coerce"
            ),
        }
    ).reset_index(drop=True)


def eia860_side(frame: pd.DataFrame) -> pd.DataFrame:
    """Per-(plant, family) EIA-860 MW over the admitted (OP + SB) population.

    A blank summer takes the nameplate and a blank winter the summer — the
    loader's own fallbacks (E.1), so the two sides read one rule.
    """
    adm = frame[frame["status"].isin(_ADMITTED_STATUSES)].copy()
    adm["summer"] = adm["summer"].where(adm["summer"] > 0, adm["nameplate"])
    adm["winter"] = adm["winter"].where(adm["winter"] > 0, adm["summer"])
    return (
        adm.groupby(["plant", "family"])[["nameplate", "summer", "winter"]]
        .sum()
        .reset_index()
    )


def model_from_unit_marginal(bundle: Path, year: int) -> pd.DataFrame:
    """Per-(plant, family) model MW from a bundle's committed slim layer.

    ``cap_mw`` is the unit-hour available MW (pmax × availability); a unit's
    pmax is its maximum over the year, and the seasonal capability is the
    unit's maximum over July / January hours (the outage-free envelope the
    slim layer can recover).
    """
    path = bundle / "hourly" / f"unit_marginal_{int(year)}.parquet"
    df = pd.read_parquet(
        path, columns=["unit_id", "plant_code", "plant_group", "fuel", "hour", "cap_mw"]
    )
    df = df.drop_duplicates(["unit_id", "hour"])
    month = pd.to_datetime(f"{int(year)}-01-01") + pd.to_timedelta(df["hour"], "h")
    df["month"] = month.dt.month.values
    per_unit = df.groupby("unit_id").agg(
        plant=("plant_code", "first"),
        group=("plant_group", "first"),
        fuel=("fuel", "first"),
        pmax=("cap_mw", "max"),
    )
    per_unit["summer"] = df[df["month"] == 7].groupby("unit_id")["cap_mw"].max()
    per_unit["winter"] = df[df["month"] == 1].groupby("unit_id")["cap_mw"].max()
    per_unit["avail_jul"] = df[df["month"] == 7].groupby("unit_id")["cap_mw"].mean()
    per_unit["avail_jan"] = df[df["month"] == 1].groupby("unit_id")["cap_mw"].mean()
    per_unit = per_unit.fillna(0.0)
    per_unit["family"] = [
        model_family(g, f) for g, f in zip(per_unit["group"], per_unit["fuel"])
    ]
    per_unit = per_unit[per_unit["family"].notna()]
    per_unit["plant"] = pd.to_numeric(per_unit["plant"], errors="coerce").fillna(0)
    per_unit["plant"] = per_unit["plant"].astype(int)
    return (
        per_unit.groupby(["plant", "family"])[
            ["pmax", "summer", "winter", "avail_jul", "avail_jan"]
        ]
        .sum()
        .reset_index()
    )


def _w0_fields() -> tuple[str, ...]:
    from market_sim.config import scenarios as scen

    return tuple(scen._W0_BACKCAST_DEFAULT_FIELDS)


def rebuild_fleet(
    bundle: Path, year: int, posture: str, overrides: dict | None = None
) -> dict:
    """Zero-LP ``run_year(fleet_only=True)`` of the bundle's recipe at ``posture``.

    ``overrides`` (``--set``) are applied last, through the same generic
    ``prb_overrides`` channel ``replay_keeper --set`` uses — for a mechanism
    downstream of the fleet whose input is not in this checkout (PJM's
    ``pjm_da_virtual_bids``); the census records them.
    """
    from market_sim.config.scenarios import registration_time_default
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    kw["prb_overrides"] = copy.deepcopy(kw.get("prb_overrides") or {})
    recorded = _recorded_config(bundle, year)
    for field in _w0_fields():
        if posture == "w0":
            kw["prb_overrides"][field] = True
        else:
            kw["prb_overrides"][field] = recorded.get(
                field, registration_time_default(field)
            )
    kw["prb_overrides"].update(overrides or {})
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _recorded_config(bundle: Path, year: int) -> dict:
    """The bundle's recorded ``scenario_config`` for ``year`` (else the span's)."""
    for name in (f"run_config_{int(year)}.json", "run_config.json"):
        path = bundle / name
        if path.is_file():
            return json.loads(path.read_text()).get("scenario_config", {})
    return {}


def model_from_fleet(res: dict, year: int) -> pd.DataFrame:
    """Per-(plant, family) model MW from a zero-LP fleet rebuild."""
    from market_sim.data import cod_ramp

    fleet = res["fleet"]
    fa = res["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    hours = avail.shape[1]
    month = (
        pd.to_datetime(f"{int(year)}-01-01") + pd.to_timedelta(np.arange(hours), "h")
    ).month.values
    jul, jan = month == 7, month == 1
    cod_map = cod_ramp.load_cod_map()
    unit_map = cod_ramp.load_unit_cod_map()
    rows = []
    for i, g in enumerate(fleet):
        mask, _ = cod_ramp.generator_online_mask(
            int(g.plant_code),
            g.plant_group,
            int(g.online_year),
            int(g.online_month),
            g.retirement_year,
            g.retirement_month,
            bool(g.is_campd_bin),
            cod_map,
            unit_map,
            int(year),
        )
        mask = np.asarray(mask, dtype=float)
        family = model_family(g.plant_group, g.fuel_type)
        if family is None or float(mask.max()) <= 0.0:
            continue
        sf = g.summer_capability_frac
        wf = g.winter_capability_frac
        rows.append(
            {
                "plant": int(g.plant_code),
                "family": family,
                "pmax": float(g.pmax_mw),
                "summer": float(g.pmax_mw) * (1.0 if sf is None else sf) * mask[6],
                "winter": float(g.pmax_mw) * (1.0 if wf is None else wf) * mask[0],
                "avail_jul": float(pmax[i] * avail[i, jul].mean()),
                "avail_jan": float(pmax[i] * avail[i, jan].mean()),
            }
        )
    df = pd.DataFrame(rows)
    return (
        df.groupby(["plant", "family"])[
            ["pmax", "summer", "winter", "avail_jul", "avail_jan"]
        ]
        .sum()
        .reset_index()
    )


def _pct(model: float, ref: float) -> float | None:
    return None if ref <= 0.0 else round(100.0 * (model - ref) / ref, 3)


def _residual_rows(
    eia: pd.DataFrame, model: pd.DataFrame, family: str, limit: int = 12
) -> list[dict]:
    """The plants that account for a family's summer gap, largest first."""
    e = eia[eia["family"] == family].set_index("plant")["summer"]
    m = model[model["family"] == family].set_index("plant")["summer"]
    joined = pd.concat([e.rename("eia"), m.rename("model")], axis=1).fillna(0.0)
    joined["delta"] = joined["model"] - joined["eia"]
    joined = joined[joined["delta"].abs() > 0.5]
    joined = joined.reindex(joined["delta"].abs().sort_values(ascending=False).index)
    out = []
    for plant, row in joined.head(limit).iterrows():
        if row["model"] == 0.0:
            reason = "not carried in this family (status / class / footprint / exit)"
        elif row["eia"] == 0.0:
            reason = "carried, not OP/SB in this family of the vintage (exit channel, class boundary)"
        else:
            reason = "rating differs (block / guard clip / steam part / COD fraction)"
        out.append(
            {
                "plant": int(plant),
                "eia860_summer_mw": round(float(row["eia"]), 1),
                "model_summer_mw": round(float(row["model"]), 1),
                "delta_mw": round(float(row["delta"]), 1),
                "reason": reason,
            }
        )
    return out


def build_census(
    iso: str,
    year: int,
    model: pd.DataFrame,
    model_source: str,
    iso_report: dict | None = None,
) -> dict:
    """Assemble the ``fleet_census_<Y>.json`` ledger for one ISO-year."""
    frame = eia860_vintage_frame(iso, year)
    eia = eia860_side(frame)
    rows = []
    totals = {k: 0.0 for k in ("np", "s", "w", "mp", "ms", "mw", "aj", "an")}
    for fam in FAMILIES:
        e = eia[eia["family"] == fam]
        m = model[model["family"] == fam]
        vals = {
            "np": float(e["nameplate"].sum()),
            "s": float(e["summer"].sum()),
            "w": float(e["winter"].sum()),
            "mp": float(m["pmax"].sum()),
            "ms": float(m["summer"].sum()),
            "mw": float(m["winter"].sum()),
            "aj": float(m["avail_jul"].sum()),
            "an": float(m["avail_jan"].sum()),
        }
        if not any(vals.values()):
            continue
        injected = fam in INJECTED_FAMILIES
        if not injected:
            for k in totals:
                totals[k] += vals[k]
        ds, dw = _pct(vals["ms"], vals["s"]), _pct(vals["mw"], vals["w"])
        within = injected or all(
            d is None or abs(d) <= TOL_FAMILY_PCT for d in (ds, dw)
        )
        rows.append(
            {
                "family": fam,
                "eia860_nameplate_mw": round(vals["np"], 1),
                "eia860_summer_mw": round(vals["s"], 1),
                "eia860_winter_mw": round(vals["w"], 1),
                "model_pmax_mw": round(vals["mp"], 1),
                "model_summer_mw": round(vals["ms"], 1),
                "model_winter_mw": round(vals["mw"], 1),
                "model_available_jul_mw": round(vals["aj"], 1),
                "model_available_jan_mw": round(vals["an"], 1),
                "delta_summer_pct": ds,
                "delta_winter_pct": dw,
                "within_tolerance": within,
                "scored": not injected,
                "explained_residual_rows": (
                    [] if within else _residual_rows(eia, model, fam)
                ),
            }
        )
    ds, dw = _pct(totals["ms"], totals["s"]), _pct(totals["mw"], totals["w"])
    total_ok = all(d is None or abs(d) <= TOL_TOTAL_PCT for d in (ds, dw))
    report = iso_report or {}
    rep_mw = report.get("mw")
    d_iso = _pct(totals["ms"], float(rep_mw)) if rep_mw else None
    oos = _out_of_service_envelope(frame)
    planned = frame[
        frame["status"].isin(_ADMITTED_STATUSES)
        & (frame["planned_ret_year"] <= int(year))
    ]
    return {
        "schema": 1,
        "iso": iso,
        "year": int(year),
        "eia860_vintage": _vintage_dir(year).name,
        "model_source": model_source,
        "tolerances_pct": {
            "family_vs_860": TOL_FAMILY_PCT,
            "total_thermal_vs_860": TOL_TOTAL_PCT,
            "total_vs_iso_report": TOL_ISO_REPORT_PCT,
        },
        "families": rows,
        "total_thermal": {
            "eia860_nameplate_mw": round(totals["np"], 1),
            "eia860_summer_mw": round(totals["s"], 1),
            "eia860_winter_mw": round(totals["w"], 1),
            "model_pmax_mw": round(totals["mp"], 1),
            "model_summer_mw": round(totals["ms"], 1),
            "model_winter_mw": round(totals["mw"], 1),
            "model_available_jul_mw": round(totals["aj"], 1),
            "model_available_jan_mw": round(totals["an"], 1),
            "delta_summer_pct": ds,
            "delta_winter_pct": dw,
            "within_tolerance": total_ok,
        },
        "iso_report": {
            "mw": rep_mw,
            "basis": report.get("basis"),
            "source": report.get("source"),
            "delta_pct": d_iso,
            "within_tolerance": (
                None if d_iso is None else abs(d_iso) <= TOL_ISO_REPORT_PCT
            ),
            "status": "compared" if rep_mw else "UNAVAILABLE (report not on disk)",
        },
        "out_of_service_envelope": oos,
        "planned_retirement_binding_mw": round(float(planned["nameplate"].sum()), 1),
        "verdict": (
            "WITHIN"
            if total_ok and all(r["within_tolerance"] for r in rows)
            else "OUTSIDE"
        ),
    }


def _out_of_service_envelope(frame: pd.DataFrame) -> dict:
    """Plants whose every vintage unit is OA/OS (E.4: reported, never fitted)."""
    by_plant = frame.groupby("plant")["status"].agg(lambda s: set(s))
    dark = [p for p, st in by_plant.items() if st and st <= _OUT_OF_SERVICE]
    mw = float(frame[frame["plant"].isin(dark)]["nameplate"].sum())
    return {"plants": len(dark), "nameplate_mw": round(mw, 1)}


def ercot_csv_audit(year: int, csv_path: Path | None = None) -> dict:
    """Q5: ERCOT's curated bin sheet vs the solved year's vintage footprint."""
    from market_sim.config.paths import RAW_DATA_DIR

    path = csv_path or RAW_DATA_DIR / "reference" / "custom-bin-assignments.csv"
    sheet = pd.read_csv(path)
    sheet_plants = set(
        pd.to_numeric(sheet["Plant_Code"], errors="coerce").dropna().astype(int)
    )
    frame = eia860_vintage_frame("ERCOT", year)
    fossil = frame[
        frame["family"].isin(("COAL", "CC", "CT", "ST_GAS"))
        & frame["status"].isin(_ADMITTED_STATUSES)
    ]
    vint = fossil.groupby("plant")["nameplate"].sum()
    missing = vint[~vint.index.isin(sheet_plants)].sort_values(ascending=False)
    extra = sorted(
        p
        for p in sheet_plants - set(vint.index)
        if int(str(p)[:-1] or 0) not in set(vint.index)
    )
    # A plant the sheet carries can still be SHORT of the vintage's units —
    # Decker Creek 3548: the sheet holds its four GTs while the vintage's
    # steam units ST1/ST2 (724 MW to 2020, 404 MW to Mar-2022) are absent
    # (closeout-ERCOT, docs/records/ercot/closeout/
    # FINDING-closeout-w1-zero-lp-censuses-2026-10-02.md row 6). Flag every
    # carried plant whose vintage fossil nameplate exceeds the sheet's by more
    # than the family tolerance.
    # The sheet splits a plant on a class boundary into a CHILD code = parent
    # code + one digit (W A Parish 3470 -> 34702 ST, Wharton 3469 -> 34693 CT,
    # Barney Davis 4939 -> 49392 ST); a child that is not itself a vintage
    # plant is folded back into its parent before the comparison.
    codes = pd.to_numeric(sheet["Plant_Code"], errors="coerce")
    vintage_plants = set(vint.index)

    def _parent(code: float) -> float:
        text = str(int(code))
        if int(code) not in vintage_plants and int(text[:-1] or 0) in vintage_plants:
            return float(text[:-1])
        return code

    sheet_np = (
        sheet.assign(_pc=codes.map(lambda c: _parent(c) if pd.notna(c) else c))
        .dropna(subset=["_pc"])
        .groupby("_pc")["Nameplate_MW"]
        .sum()
    )
    sheet_np.index = sheet_np.index.astype(int)
    both = vint[vint.index.isin(sheet_np.index)]
    gap = both - sheet_np.reindex(both.index)
    short = gap[gap > both * TOL_FAMILY_PCT / 100.0].sort_values(ascending=False)
    return {
        "year": int(year),
        "vintage": _vintage_dir(year).name,
        "sheet": str(path.relative_to(REPO))
        if path.is_relative_to(REPO)
        else str(path),
        "vintage_fossil_plants_absent_from_sheet": [
            {"plant": int(p), "nameplate_mw": round(float(mw), 1)}
            for p, mw in missing.items()
        ],
        "absent_mw": round(float(missing.sum()), 1),
        "sheet_plants_absent_from_vintage": extra,
        "carried_plants_short_of_vintage": [
            {
                "plant": int(p),
                "vintage_nameplate_mw": round(float(both[p]), 1),
                "sheet_nameplate_mw": round(float(sheet_np[p]), 1),
                "short_mw": round(float(mw), 1),
            }
            for p, mw in short.items()
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; see the module docstring."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--year", type=int, required=True)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--bundle", type=Path, help="read hourly/unit_marginal_<Y>")
    src.add_argument("--rebuild", type=Path, help="zero-LP fleet rebuild of a recipe")
    ap.add_argument("--posture", choices=("w0", "recorded"), default="w0")
    ap.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="FIELD=JSON",
        help="extra recipe override (recorded in the census); repeatable",
    )
    ap.add_argument("--iso-report-json", type=Path, default=None)
    ap.add_argument("--ercot-csv-audit", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    iso = args.iso.upper()
    if args.bundle is not None:
        model = model_from_unit_marginal(args.bundle, args.year)
        source = f"unit_marginal:{args.bundle.name}"
    else:
        overrides = {
            k: json.loads(v) for k, v in (spec.split("=", 1) for spec in args.set)
        }
        res = rebuild_fleet(args.rebuild, args.year, args.posture, overrides)
        model = model_from_fleet(res, args.year)
        source = f"rebuild:{args.rebuild.name}:{args.posture}"
        if overrides:
            source += f":set={json.dumps(overrides, sort_keys=True)}"
    report = (
        json.loads(args.iso_report_json.read_text()) if args.iso_report_json else None
    )
    census = build_census(iso, args.year, model, source, report)
    if args.ercot_csv_audit and iso == "ERCOT":
        census["ercot_csv_audit"] = ercot_csv_audit(args.year)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(census, indent=2, sort_keys=False) + "\n")
    tot = census["total_thermal"]
    print(
        f"{iso} {args.year}: model summer {tot['model_summer_mw']:,.0f} vs 860 "
        f"{tot['eia860_summer_mw']:,.0f} ({tot['delta_summer_pct']}%), winter "
        f"{tot['model_winter_mw']:,.0f} vs {tot['eia860_winter_mw']:,.0f} "
        f"({tot['delta_winter_pct']}%) -> {census['verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
