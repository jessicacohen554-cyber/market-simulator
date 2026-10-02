"""PJM close-out census 0a (zero-LP): model installed MW by fuel class vs IMM SOM §12.

Plan ``docs/backcast-closeout-plan-2026-10.md`` §3.6; research shard
``docs/records/governance/closeout-2026-10/SHARD-PJM-closeout-research-2026-10-02.md``
§7 and §8 row 0a. Pre-fixed reading (not changed here): PASS iff every class MW
is within +/-2 % of the IMM figure in every year 2019-2025; otherwise FAIL and
name the units (plants) that explain each out-of-band class-year (top movers
covering >= 80 % of the gap).

No LP is built or solved. Two model-side figures per class-year:

* ``model_mw`` (the scored figure) -- the keeper's year-end fleet on its own
  registry basis: EIA-860 year-matched vintage ``data/raw/eia-860/vintage_<Y>/
  eia860_generators.parquet`` (``eia860_vintage_tracks_solve_year``), status
  ``OP`` only (``admit_standby_units`` is off in the keeper), balancing
  authority PJM plus the ``ISO_BA_JOINS['PJM']`` join (OVEC), restricted to
  plants the keeper LP actually carries in year Y (plant codes present in the
  committed ``hourly/unit_marginal_<Y>.parquet``), classed by the loader's own
  ``fleet.eia860._map_fuel_type``; pmax basis = EIA-860 net summer capacity, as
  in the loader. The mid-vintage exit carry contributes nothing at 31 Dec (its
  rows are masked after their exit hour), so it shows up only in the cross-check.
  Wind/solar come from the solve's own loader
  ``data.renewables._eia860_monthly_capacity`` (nameplate, eGRID zone lookup,
  COD/retirement ramp), December column, same vintage. Hydro = the LP's own
  annual max hourly ceiling (the hydro loader's pmax is not EIA-860 net summer;
  the EIA figure for the same plants is kept as ``eia860_net_summer_ye_mw``).
* ``lp_annual_max_mw`` (cross-check) -- per plant, the max over the year's 8760
  hours of the summed hourly ``cap_mw`` of its LP tranches in the keeper bundle
  (``results/calibration/pjmnext16_A_span``). Availability-scaled, so a lower
  bound on what the LP carried, but it includes units that exited mid-year.

IMM side: IMM State of the Market for PJM, Section 12 (Planning), Table 12-1
"Existing capacity: December 31, <Y> (By zone and unit type (MW))", Total row
(summer installed capacity rating, footnote), plus its OVEC and XIC (external)
rows, fetched from monitoringanalytics.com and parsed with ``pdftotext -layout``.

Run: ``.venv/bin/python scripts/probes/_pjmco_0a_capacity_census.py``
Writes ``results/phase0/pjm/_pjmco_0a_capacity_census.json`` and ``.csv``.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/pjmnext16_A_span"
EIA = REPO / "data/raw/eia-860"
OUT = REPO / "results/phase0/pjm/_pjmco_0a_capacity_census.json"
YEARS = list(range(2019, 2026))
BAND = 0.02
IMM_URL = (
    "https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/"
    "{y}/{y}-som-pjm-sec12.pdf"
)

# Table 12-1 column layouts (data columns before "Total"), read off the printed headers.
COLS_2019 = [
    "Battery", "Combined Cycle", "CT - Natural Gas", "CT - Oil", "CT - Other",
    "Fuel Cell", "Hydro - Pumped Storage", "Hydro - Run of River", "Nuclear",
    "RICE - Natural Gas", "RICE - Oil", "RICE - Other", "Solar", "Steam - Coal",
    "Steam - Natural Gas", "Steam - Oil", "Steam - Other", "Wind",
]
COLS_2020 = [
    "Battery", "Combined Cycle", "CT - Natural Gas", "CT - Oil", "CT - Other",
    "Fuel Cell", "Hydro - Pumped Storage", "Hydro - Run of River", "Nuclear",
    "RICE - Natural Gas", "RICE - Oil", "RICE - Other", "Solar", "Solar + Storage",
    "Solar + Wind", "Steam - Coal", "Steam - Natural Gas", "Steam - Oil",
    "Steam - Other", "Wind", "Wind + Storage",
]
# Census class -> IMM Table 12-1 unit types (model taxonomy: gas_ct carries NG GT + NG IC,
# oil carries every oil-fired prime mover -- fleet.eia860._map_fuel_type).
IMM_CLASS = {
    "coal": ["Steam - Coal"],
    "gas_cc": ["Combined Cycle"],
    "gas_ct": ["CT - Natural Gas", "RICE - Natural Gas"],
    "gas_st": ["Steam - Natural Gas"],
    "oil": ["CT - Oil", "Steam - Oil", "RICE - Oil"],
    "nuclear": ["Nuclear"],
    "hydro": ["Hydro - Run of River"],
    "wind": ["Wind", "Wind + Storage"],
    "solar": ["Solar", "Solar + Storage"],
}
CLASSES = list(IMM_CLASS)
OIL_CODES = {"DFO", "RFO", "KER", "JF", "WO"}
MAX_NAMED = 8


def _num(tok: str) -> float:
    """Parse one printed IMM number ('1,234.5')."""
    return float(tok.replace(",", ""))


def fetch_imm(year: int, workdir: Path) -> dict:
    """Download and parse SOM §12 Table 12-1 for ``year`` (Total, OVEC, XIC rows)."""
    pdf = workdir / f"som{year}.pdf"
    if not pdf.exists():
        req = urllib.request.Request(IMM_URL.format(y=year), headers={"User-Agent": "Mozilla/5.0"})
        pdf.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    txt = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True
    ).stdout
    pages = txt.split("\f")
    cols = COLS_2019 if year == 2019 else COLS_2020
    pat = re.compile(rf"Table 12-1 Existing (PJM )?capacity: December 31, {year}")
    for i, page in enumerate(pages):
        m = pat.search(page)
        if not m:
            continue
        title = page[m.start():].splitlines()[0].strip()
        title = re.sub(r"\)\d+$", ")", title)  # drop the footnote marker
        rows: dict[str, list[float]] = {}
        for line in page[m.end():].splitlines():
            parts = line.split()
            if parts and parts[0] in ("Total", "OVEC", "XIC") and parts[0] not in rows:
                nums = [_num(t) for t in parts[1:]]
                if len(nums) == len(cols) + 1:
                    rows[parts[0]] = nums
            if "Total" in rows and line.strip().startswith("Table 12-2"):
                break
        if "Total" not in rows:
            continue
        tot = rows["Total"]
        if abs(sum(tot[:-1]) - tot[-1]) > 1.0:
            raise ValueError(f"{year}: Table 12-1 Total row does not add up")
        printed = re.findall(r"Report for PJM\s+(\d{2,4})|\n\s*(\d{2,4})\s+Section 12 Planning", page)
        printed_page = next((a or b for a, b in printed), None)
        out = {"table": title, "pdf_page": i + 1, "printed_page": printed_page,
               "as_of": f"{year}-12-31", "url": IMM_URL.format(y=year),
               "basis": "summer installed capacity rating, all capacity in PJM regardless of RPM (Table 12-1 footnote)"}
        for row in ("Total", "OVEC", "XIC"):
            vals = dict(zip(cols, rows.get(row, [0.0] * (len(cols) + 1))))
            out[row.lower()] = {
                c: round(sum(vals.get(t, 0.0) for t in IMM_CLASS[c]), 1) for c in CLASSES
            }
        out["total_all_types"] = tot[-1]
        return out
    raise RuntimeError(f"Table 12-1 not found in {year} SOM section 12")


def lp_plants(year: int) -> pd.DataFrame:
    """Per (plant, model fuel): annual max of summed hourly cap_mw, and presence, from the bundle."""
    d = pd.read_parquet(
        BUNDLE / f"hourly/unit_marginal_{year}.parquet",
        columns=["plant_code", "fuel", "hour", "cap_mw"],
    )
    d["fuel"] = d["fuel"].astype(str)
    d = d[(d.fuel != "import") & (d.plant_code > 0)]
    h = d.groupby(["plant_code", "fuel", "hour"], observed=True)["cap_mw"].sum()
    return h.groupby(level=[0, 1]).max().rename("lp_annual_max_mw").reset_index()


def eia_frame(year: int) -> pd.DataFrame:
    """EIA-860 vintage_<year> generators in PJM + joining BAs, with model class."""
    from market_sim.config.constants import ISO_BA_JOINS
    from market_sim.data.fleet.eia860 import _map_fuel_type

    g = pd.read_parquet(EIA / f"vintage_{year}/eia860_generators.parquet")
    bas = {"PJM", *ISO_BA_JOINS.get("PJM", {})}
    g = g[g.balancing_authority_code.astype(str).str.strip().isin(bas)].copy()
    g["status"] = g.status.astype(str).str.strip().str.upper()
    g["klass"] = [
        _map_fuel_type(t, e, p) for t, e, p in zip(g.technology, g.energy_source, g.prime_mover)
    ]
    hy = g.prime_mover.astype(str).str.upper().eq("HY")
    g.loc[hy, "klass"] = "hydro"
    g["mw"] = pd.to_numeric(g.net_summer_capacity_mw, errors="coerce").fillna(0.0)
    op = pd.read_parquet(
        EIA / f"vintage_{year}/eia860_generator_operable.parquet",
        columns=["Plant Code", "Generator ID", "Energy Source 2"],
    )
    op["key"] = op["Plant Code"].astype(str).str.split(".").str[0] + "|" + op["Generator ID"].astype(str).str.strip()
    es2 = dict(zip(op.key, op["Energy Source 2"].astype(str).str.strip().str.upper()))
    g["es2"] = (g.plant_id.astype(str).str.split(".").str[0] + "|" + g.generator_id.astype(str).str.strip()).map(es2).fillna("")
    return g


def renewables_dec(year: int) -> dict:
    """Wind/solar December MW from the solve's own loader on vintage_<year>."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.renewables import _eia860_monthly_capacity

    zones = [getattr(z, "name", z) for z in get_iso_config("PJM").zones]
    out = {}
    for f in ("wind", "solar"):
        m = _eia860_monthly_capacity("PJM", f, zones, year, data_dir=EIA / f"vintage_{year}")
        out[f] = (0.0, 0.0) if m is None else (float(m[:, 11].sum()), float(m.max(axis=1).sum()))
    return out


def movers(year: int, klass: str, gap: float, imm: dict, g: pd.DataFrame, lp_codes: set,
           model_plants: pd.DataFrame) -> list[dict]:
    """Named contributions to IMM - model for one class-year, largest first."""
    items: list[dict] = []
    xic = imm["xic"][klass]
    if xic:
        items.append({"mover": "IMM XIC (external) row -- outside the PJM BA, not in the model footprint; IMM prints no unit names", "mw": xic})
    if klass == "coal":
        ovec_model = float(model_plants[model_plants.plant_code.isin([983, 2876])].mw.sum())
        items.append({"mover": f"OVEC rating basis: IMM OVEC zone {imm['ovec']['coal']} vs EIA-860 net summer Clifty Creek 983 + Kyger Creek 2876 = {ovec_model:.1f}",
                      "mw": round(imm["ovec"]["coal"] - ovec_model, 1)})
    k = g[g.klass == klass]
    nonop = k[k.status != "OP"]
    for (pc, name, st), mw in nonop.groupby(["plant_id", "plant_name", "status"]).mw.sum().items():
        if mw > 0:
            items.append({"mover": f"{name} ({int(pc)}) EIA status {st} -- installed per IMM, excluded by the OP-only loader", "mw": round(float(mw), 1), "plant_code": int(pc)})
    op = k[(k.status == "OP") & ~k.plant_id.isin(lp_codes)]
    for (pc, name), mw in op.groupby(["plant_id", "plant_name"]).mw.sum().items():
        if mw > 0:
            items.append({"mover": f"{name} ({int(pc)}) OP in EIA-860 PJM but absent from the keeper LP", "mw": round(float(mw), 1), "plant_code": int(pc)})
    # Dual-fuel label candidates: the loader types a gas/oil unit by Energy Source 1;
    # IMM's unit-type label can sit on the other fuel (gas_ct/gas_st surplus <-> oil deficit).
    if klass in ("gas_ct", "gas_st", "oil"):
        ye = g[(g.status == "OP") & g.plant_id.isin(lp_codes)]
        if klass == "oil":
            dual = ye[ye.klass.isin(["gas_ct", "gas_st"]) & ye.es2.isin(OIL_CODES)]
            sign, note = 1.0, "typed gas by EIA Energy Source 1 (oil secondary) -- IMM may type oil"
        else:
            dual = ye[(ye.klass == klass) & ye.es2.isin(OIL_CODES)]
            sign, note = -1.0, "dual-fuel (oil secondary), typed gas by the loader -- IMM may type oil"
        for (pc, name), mw in dual.groupby(["plant_id", "plant_name"]).mw.sum().items():
            if mw > 0:
                items.append({"mover": f"{name} ({int(pc)}) {note}", "mw": round(sign * float(mw), 1), "plant_code": int(pc), "candidate": True})
    items = [it for it in items if np.sign(it["mw"]) == np.sign(gap)]
    items.sort(key=lambda r: -abs(r["mw"]))
    chosen, acc = [], 0.0
    for it in items:
        if len(chosen) >= MAX_NAMED:
            break
        chosen.append(it)
        acc += it["mw"]
        if abs(acc) >= 0.8 * abs(gap):
            break
    rest = items[len(chosen):]
    if rest and abs(acc) < 0.8 * abs(gap):
        rmw = sum(r["mw"] for r in rest)
        rmw = rmw if abs(acc + rmw) <= abs(gap) else gap - acc
        chosen.append({"mover": f"{len(rest)} further plants of the same kinds (smaller)", "mw": round(rmw, 1)})
        acc += rmw
    resid = round(gap - acc, 1)
    chosen.append({"mover": "unattributed residual (per-unit rating basis / IMM-vs-EIA dating / unit-type labels; IMM publishes no unit list)", "mw": resid})
    return chosen


def renewable_movers(year: int, fuel: str, gap: float, imm: dict) -> list[dict]:
    """Named wind/solar movers: PJM-BA OP plants the loader's eGRID zone lookup drops."""
    from market_sim.data.zone_assignment import build_zone_lookup

    code = {"wind": "WND", "solar": "SUN"}[fuel]
    lk = set(build_zone_lookup("PJM"))
    g = pd.read_parquet(EIA / f"vintage_{year}/eia860_generators.parquet")
    g = g[(g.energy_source == code) & (g.status.astype(str).str.upper() == "OP")]
    pjm = g[g.balancing_authority_code.astype(str).str.strip() == "PJM"]
    miss = pjm[~pjm.plant_id.isin(lk)]
    out: list[dict] = []
    if imm["xic"][fuel]:
        out.append({"mover": "IMM XIC (external) row", "mw": imm["xic"][fuel]})
    tot = float(miss.nameplate_capacity_mw.sum())
    if tot > 0:
        top = miss.groupby(["plant_id", "plant_name"]).nameplate_capacity_mw.sum().sort_values(ascending=False)
        names = ", ".join(f"{n} ({int(pc)}) {mw:.0f}" for (pc, n), mw in top.head(MAX_NAMED).items())
        out.append({"mover": f"{len(top)} PJM-BA OP {fuel} plants absent from the eGRID zone lookup (dropped by the loader); largest: {names}",
                    "mw": round(tot, 1)})
    acc = sum(o["mw"] for o in out)
    out.append({"mover": "residual: EIA-860 nameplate (model) vs IMM summer installed rating / market-registration basis; IMM publishes no unit list",
                "mw": round(gap - acc, 1)})
    return out


def main() -> None:
    """Build the census, write JSON + CSV, print the table."""
    work = Path(tempfile.mkdtemp(prefix="pjmco0a_"))
    rows, detail, sources = [], {}, {}
    for y in YEARS:
        imm = fetch_imm(y, work)
        sources[y] = {k: imm[k] for k in ("table", "pdf_page", "printed_page", "as_of", "url", "basis", "total_all_types")}
        lp = lp_plants(y)
        lp_codes = set(lp.plant_code.astype(int))
        g = eia_frame(y)
        hydro_codes = set(lp[lp.fuel == "hydro"].plant_code.astype(int))
        member = np.where(g.klass.eq("hydro"), g.plant_id.isin(hydro_codes), g.plant_id.isin(lp_codes))
        ye = g[(g.status == "OP") & member & g.klass.isin(CLASSES)]
        mp = ye.groupby(["plant_id", "plant_name", "klass"]).mw.sum().reset_index().rename(columns={"plant_id": "plant_code"})
        lpmax = lp.groupby("fuel").lp_annual_max_mw.sum()
        ren = renewables_dec(y)
        detail[y] = {}
        for c in CLASSES:
            if c in ("wind", "solar"):
                model, lpx = ren[c][0], ren[c][1]
            elif c == "hydro":
                # The hydro loader does not carry EIA-860 net summer as pmax (2025: LP 2,771 vs
                # EIA 3,244 MW over the same plants), so the LP's own hourly ceiling is the model MW.
                lpx = float(lpmax.get(c, 0.0))
                model = lpx
            else:
                model = float(mp[mp.klass == c].mw.sum())
                lpx = float(lpmax.get(c, 0.0))
            immv = imm["total"][c]
            diff = (model - immv) / immv if immv else float("nan")
            ok = bool(abs(diff) <= BAND)
            rows.append({"year": y, "class": c, "model_mw": round(model, 1), "imm_mw": immv,
                         "diff_pct": round(100 * diff, 2), "verdict": "PASS" if ok else "FAIL",
                         "imm_xic_mw": imm["xic"][c], "imm_ex_xic_mw": round(immv - imm["xic"][c], 1),
                         "diff_ex_xic_pct": round(100 * (model - (immv - imm["xic"][c])) / (immv - imm["xic"][c]), 2) if immv - imm["xic"][c] else None,
                         "lp_annual_max_mw": round(lpx, 1),
                         "eia860_net_summer_ye_mw": round(float(mp[mp.klass == c].mw.sum()), 1) if c not in ("wind", "solar") else None})
            if not ok and c not in ("wind", "solar"):
                detail[y][c] = movers(y, c, immv - model, imm, g, lp_codes, mp[mp.klass == c])
            elif not ok:
                detail[y][c] = renewable_movers(y, c, immv - model, imm)
        if 2020 == y:
            coal_plants = mp[mp.klass == "coal"].sort_values("mw", ascending=False)
            detail[y]["_coal_plants_model"] = coal_plants.round(1).to_dict("records")
    df = pd.DataFrame(rows)
    overall = "PASS" if (df.verdict == "PASS").all() else "FAIL"
    # 2020 coal: plants carried by the LP during the year but gone at 31 Dec (exit carry).
    lp20 = lp_plants(2020)
    g20 = eia_frame(2020)
    ye_codes = set(g20[(g20.status == "OP") & (g20.klass == "coal")].plant_id.astype(int))
    carry = lp20[(lp20.fuel == "coal") & ~lp20.plant_code.isin(ye_codes)]
    names = {}
    for v in (2019, 2020):
        gg = pd.read_parquet(EIA / f"vintage_{v}/eia860_generator_retired_and_canceled.parquet") if (EIA / f"vintage_{v}/eia860_generator_retired_and_canceled.parquet").exists() else None
        if gg is not None:
            names.update(dict(zip(gg["Plant Code"], gg["Plant Name"])))
    carry_list = [{"plant_code": int(r.plant_code), "name": names.get(r.plant_code, ""), "lp_annual_max_mw": round(float(r.lp_annual_max_mw), 1)} for r in carry.itertuples()]
    # gas_cc step 2022 -> 2023: model YoY by plant (IMM prints 56,278.2 -> 56,124.2).
    def _cc(y: int) -> pd.Series:
        codes = set(lp_plants(y).plant_code.astype(int))
        g = eia_frame(y)
        return g[(g.status == "OP") & g.plant_id.isin(codes) & (g.klass == "gas_cc")].groupby(["plant_id", "plant_name"]).mw.sum()

    cc_yoy = _cc(2023).sub(_cc(2022), fill_value=0.0).sort_values()
    cc_yoy_list = [{"plant_code": int(pc), "name": n, "mw": round(float(v), 1)} for (pc, n), v in cc_yoy.items() if abs(v) >= 50]
    out = {
        "census": "PJM close-out 0a -- installed MW by class, model vs IMM SOM §12 Table 12-1, 31 Dec 2019-2025",
        "pre_fixed_reading": "PASS iff every class within +/-2 % of IMM in every year; else FAIL and name the units",
        "overall": overall,
        "keeper_bundle": str(BUNDLE.relative_to(REPO)),
        "model_basis": "EIA-860 vintage_<Y> net summer (OP, BA PJM + OVEC join, plants carried by the keeper LP in Y); wind/solar nameplate via data.renewables._eia860_monthly_capacity December",
        "caveats": [
            "Fleet rebuild through run_year(fleet_only=True) was not run in this session (tool permission denied); membership = plant codes present in the keeper's own unit_marginal sidecar, MW = EIA-860 vintage net summer per the loader's pmax rule.",
            "The committed 2025 keeper leg was solved on the EIA-860 2025 Early Release; vintage_2025 is now the Final (PJM OP -0.77 GW nameplate per data/raw/eia-860/README.md). lp_annual_max_mw reflects what the LP carried.",
            "IMM Total includes the XIC (external) zone; diff_ex_xic_pct shows the comparison without it.",
        ],
        "rows": rows,
        "movers": {str(k): v for k, v in detail.items()},
        "coal_2020_exit_carry_plants": carry_list,
        "gas_cc_model_yoy_2022_2023": {"model_total_mw": round(float(cc_yoy.sum()), 1), "imm_total_mw": -154.0, "plants_ge_50mw": cc_yoy_list},
        "sources": {str(k): v for k, v in sources.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float))
    df.to_csv(OUT.with_suffix(".csv"), index=False)
    print(df.to_string(index=False))
    print("overall", overall)


if __name__ == "__main__":
    main()
