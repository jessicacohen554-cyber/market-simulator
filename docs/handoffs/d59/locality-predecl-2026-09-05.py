"""capx D59 pre-declaration instrument (ZERO solves, NO model code): the NYISO
locality positions and locality-curve prices per scored year, read off the COMMITTED
D52 curve-ON ledger (``nyiso-2021-2025-realized-t1h-d52-curveon``, key
``589f031432b6dc7d``) beside the published record — evaluated with HEAD's EXISTING
machinery only (the hindcast's own fleet loaders to rebuild the per-unit entering fleet,
``_nyiso_icap_vintage_curve`` / ``evaluate_demand_curve`` on the committed locality
curve rows, the committed LCR requirement rows), so the pre-declaration is fixed before
the mechanism exists.

    uv run python docs/handoffs/d59/locality-predecl-2026-09-05.py

Per scored year (2023–2025) and representable locality (NYC = Zone J, Long Island =
Zone K — DESIGN §1): the model's in-locality ICAP census (entering fleet ``pmax_mw`` by
fuel + the LP's zonal renewable nameplate + in-zone storage power), the published UDR
rights into the locality (ICAP Manual §4.9.6, DESIGN §2.3), the published Locational
Minimum ICAP Requirement (DESIGN §2.1), the position on the §2.6 identity (DESIGN §2.2),
the locality curve price at that position, the NYCA seam price at the ledger's own
``screen_reserve_position`` (HEAD's NYCA vintage), the §5.15.2 settled price, and — as
INFORMATION rows only — the SCR-adjusted position (LCR table ``[F]``) and the Gold Book
Table III-2a Zone J/K summer capability (the published census the model's census is
compared with; the NJ-sited Zone-J rows are listed separately). Rows + stdout are
committed beside this file. Nothing here is a fit target.
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))  # scripts.lib.clean_io for the confirmed-exit reader

from market_sim.config.capacity_market import (  # noqa: E402
    _nyiso_icap_vintage_curve,
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)
from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.announced_retirements import disposition_table  # noqa: E402
from market_sim.data.confirmed_retirements import (  # noqa: E402
    load_announced_reversal_plants,
    load_confirmed_exits,
)
from market_sim.data.fleet import (  # noqa: E402
    build_base_fleet,
    load_or_synthesize_bins,
    load_planned_additions,
)
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402
from market_sim.model.storage import (  # noqa: E402
    load_eia860_storage,
    measured_storage_base_fleet_active,
)
from market_sim.results.evolution_ledger import fleet_totals_by_fuel  # noqa: E402

RUN = REPO / "results/hindcast/nyiso-2021-2025-realized-t1h-d52-curveon"
BUNDLE = RUN / "NYISO/589f031432b6dc7d"
OUT_JSON = Path(__file__).with_suffix(".json")
ISO = "NYISO"
LOCALITIES = {"NYC": "NYC", "Long Island": "Long_Island"}  # csv area -> model zone
CURVE_AREA = {"NYC": "NYC", "Long Island": "LI"}  # csv area -> demand-curve csv area

# ICAP Manual §4.9.6 "UDRs awarded" (fetched 2026-09-05, sha256 b0104a50…; footnote 1 on
# HTP's CRIS lapse / 85 MW election) — DESIGN §2.3. (locality, line, MW, first CY, last CY)
UDR_RIGHTS = [
    ("Long Island", "Cross Sound Cable (ISO-NE -> K)", 330.0, 2000, 9999),
    ("Long Island", "Neptune (PJM -> K)", 660.0, 2000, 9999),
    ("NYC", "Linden VFT (PJM -> J)", 315.0, 2000, 9999),
    ("NYC", "Hudson Transmission Project (PJM -> J), CRIS through CY 2021/22", 660.0, 2000, 2021),
    ("NYC", "Hudson Transmission Project, 85 MW CRIS elected 2024", 85.0, 2024, 9999),
    ("NYC", "Champlain Hudson Power Express (HQ -> J), in service CY 2026/27", 1250.0, 2026, 9999),
]

# LCR Reports / 2025-26 TSL Floor Values sheet (DESIGN §2.1, §9): SCR MW [F] and forecast
# peak [A] per locality per CY — INFORMATION rows (the mechanism never consumes them).
LCR_TABLE = {  # CY start year -> area -> (peak [A], TSL [B], derate [E], SCR [F], ICAP req [G])
    2023: {"NYC": (11285.0, 2875.0, 0.045, 417.5, 9224.0), "Long Island": (5133.0, 325.0, 0.063, 33.7, 5400.0)},
    2024: {"NYC": (11171.0, 2875.0, 0.0289, 442.4, 8985.0), "Long Island": (5080.0, 275.0, 0.0885, 35.3, 5348.0)},
    2025: {"NYC": (11044.0, 2875.0, 0.0326, 478.7, 8673.0), "Long Island": (5092.0, 275.0, 0.0837, 30.6, 5423.0)},
}
# Potomac SOM summer UCAP margins (% of requirement) and full-year spot ($/kW-month) —
# DESIGN §2.5 / §6 item 2 (2025/26 margins are the IMPLIED values; the printed row is the
# 2024 carry-over).
PUBLISHED = {
    2023: {"NYCA": (4.3, 4.11), "NYC": (2.6, 15.97), "Long Island": (13.1, 4.11), "G-J": (8.5, 4.17)},
    2024: {"NYCA": (5.8, 3.47), "NYC": (5.7, 11.76), "Long Island": (11.7, 3.60), "G-J": (16.4, 3.47)},
    2025: {"NYCA": (3.5, 4.28), "NYC": (7.8, 10.98), "Long Island": (12.2, 4.28), "G-J": (17.4, 4.28)},
}
# Gold Book Table III-2a Zone J / K summer capability (data/raw/NYISO/*NYCA*Generators*.xlsx,
# summed this session; NJ-sited Zone-J rows = Linden Cogen + Bayonne EC) — INFORMATION.
GOLD_BOOK = {
    2023: {"NYC": (9231.9, 1391.1), "Long Island": (5005.7, 0.0)},
    2024: {"NYC": (8718.9, 1335.7), "Long Island": (5072.5, 0.0)},
    2025: {"NYC": (8704.7, 1353.0), "Long Island": (5195.5, 0.0)},
}


def load_config() -> ScenarioConfig:
    """The D52 curve-ON config, rebuilt from its committed run_config.json (key-checked)."""
    import dataclasses

    sc = json.loads((RUN / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    cfg = ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})
    cfg = apply_iso_scenario_defaults(cfg, ISO)
    assert cfg.cache_key() == "589f031432b6dc7d", cfg.cache_key()
    return cfg


def requirement_rows() -> dict[int, dict[str, float]]:
    """{CY start year: {area: ICAP requirement MW}} from the committed deliverability csv."""
    path = REPO / "data/raw/capacity-deliverability/nyiso/nyiso.csv"
    out: dict[int, dict[str, float]] = defaultdict(dict)
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["metric"] == "requirement" and r["value_mw"]:
                out[int(r["delivery_year"][:4])][r["area"]] = float(r["value_mw"])
    return dict(out)


def locality_curves() -> dict[str, dict[int, tuple]]:
    """{curve area: {CY start: (ARV, summer ref, summer max, length)}} from the demand-curve csv."""
    path = REPO / "data/raw/capacity-market/demand-curve/nyiso/nyiso.csv"
    rows = list(csv.DictReader(path.open(newline="")))
    out: dict[str, dict[int, dict]] = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        if r["area"] not in ("NYC", "LI", "G-J", "NYCA"):
            continue
        cy = int(r["delivery_year"][:4])
        d = out[r["area"]][cy]
        if r["metric"] == "net_cone":
            d["arv"] = float(r["y_value"])
        elif r["metric"] == "gross_cone":
            d["gross"] = float(r["y_value"])
        elif r["metric"] == "price_cap" and r["season"] in ("summer", ""):
            d.setdefault("max", float(r["y_value"]))
        elif r["metric"] == "curve_point" and r["season"] in ("summer", ""):
            if r["point_index"] == "0":
                d.setdefault("ref", float(r["y_value"]))
            else:
                d.setdefault("zero_x", float(r["x_value"]))
    return {a: dict(v) for a, v in out.items()}


def curve_price(area_rows: dict, cy: int, pos: float) -> float | None:
    """The locality vintage curve ($/kW-yr) at ``pos`` on the NYCA construction; None if no ARV."""
    d = area_rows.get(cy)
    if not d or "arv" not in d:
        return None
    length = d["zero_x"] - 1.0
    curve = _nyiso_icap_vintage_curve(d["ref"], d["max"], length)
    return evaluate_demand_curve(curve, pos) * d["arv"]


def nyca_price(year: int, pos: float) -> float:
    v = resolve_demand_curve_vintage(ISO, year)
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr


def base_fleet(cfg: ScenarioConfig):
    """The 2021 base fleet exactly as the hindcast runner builds it (runner ≈ 1466–2060)."""
    iso_config = get_iso_config(ISO)
    zone_names = [z.name for z in iso_config.zones]
    campd_bins = load_or_synthesize_bins(cfg, ISO, iso_config, [])
    planned = load_planned_additions(ISO, iso_config)
    as_of = _dt.date(cfg.eia860_vintage_year, 12, 31)
    confirmed = load_confirmed_exits(ISO, as_of=as_of, required=True)
    reversal_as_of = None if cfg.hindcast_verified_announced_exits else as_of
    reversed_plants = load_announced_reversal_plants(ISO, as_of=reversal_as_of, required=True)
    afx = disposition_table(
        ISO, verify=bool(cfg.hindcast_verified_announced_exits), reversed_plant_codes=reversed_plants
    )
    announced = [r for r in afx if r.disposition not in ("cancelled", "reversed")]
    fleet = build_base_fleet(
        campd_bins, ISO, iso_config, zone_names, cfg, [], planned, cfg.start_year,
        confirmed_exits=confirmed, announced_fossil_exits=announced,
    )
    return fleet, iso_config, zone_names


def chain_entering_fleets(fleet, ledgers: dict[int, dict]) -> dict[int, list]:
    """Entering fleet per year from the base fleet + the ledger's own per-unit events."""
    entering: dict[int, list] = {}
    current = list(fleet)
    for y in sorted(ledgers):
        led = ledgers[y]
        entering[y] = list(current)
        mine = fleet_totals_by_fuel(current)
        for fuel, mw in led["fleet_by_fuel_before"].items():
            if abs(mine.get(fuel, 0.0) - mw) >= 0.6:
                print(f"FLEET MISMATCH {y} {fuel}: mine {mine.get(fuel, 0.0):.1f} vs ledger {mw:.1f}")
        gone = {r["unit_id"] for r in led["retirements"]}
        current = [g for g in current if g.unit_id not in gone]
        for key in ("confirmed_derates", "announced_derates"):
            for d in led.get(key) or []:
                current = [
                    (g.model_copy(update={"pmax_mw": float(d["mw_after"])}) if g.unit_id == d["unit_id"] else g)
                    for g in current
                ]
        for a in led.get("thermal_additions") or []:
            current.append(
                current[0].model_copy(
                    update={"unit_id": a["unit_id"], "fuel_type": a["fuel"], "pmax_mw": float(a["mw"]), "zone": a["zone"], "name": a["unit_id"]}
                )
            )
    return entering


def main() -> None:
    cfg = load_config()
    ledgers = {y: json.loads((BUNDLE / f"evolution_{y}.json").read_text()) for y in (2021, 2022, 2023, 2024, 2025)}
    fleet, iso_config, zone_names = base_fleet(cfg)
    entering = chain_entering_fleets(fleet, ledgers)
    _, wind_cap, _, solar_cap = load_renewable_profiles(ISO, cfg.weather_year, iso_config, cfg)
    ren_zone = {z: (float(wind_cap[i]), float(solar_cap[i])) for i, z in enumerate(zone_names)}
    storage = load_eia860_storage(ISO, cfg.start_year, cfg) if measured_storage_base_fleet_active(cfg, ISO) else []
    stor_zone: dict[str, float] = defaultdict(float)
    for u in storage:
        stor_zone[u.zone] += float(u.power_cap_mw)
    req = requirement_rows()
    curves = locality_curves()
    load_share = {z.name: z.load_share for z in iso_config.zones}

    rows = []
    for y in (2023, 2024, 2025):
        led = ledgers[y]
        nyca_pos = led["screen_reserve_position"]
        p_nyca = nyca_price(y, nyca_pos)
        for area, zone in LOCALITIES.items():
            units = [g for g in entering[y] if g.zone == zone]
            by_fuel = fleet_totals_by_fuel(units)
            fleet_icap = sum(by_fuel.values())
            w, s = ren_zone[zone]
            st = stor_zone.get(zone, 0.0)
            udr = sum(mw for a, _n, mw, f, l in UDR_RIGHTS if a == area and f <= y <= l)
            supply = fleet_icap + w + s + st + udr
            r = req[y][area]
            pos = supply / r
            pos_no_udr = (supply - udr) / r
            peak, tsl, derate, scr, g_req = LCR_TABLE[y][area]
            pos_scr = (supply + scr) / r
            p_loc = curve_price(curves[CURVE_AREA[area]], y, pos)
            settled = max(p_nyca, p_loc) if p_loc is not None else p_nyca
            pub_margin, pub_spot = PUBLISHED[y][area]
            gb_total, gb_nj = GOLD_BOOK[y][area]
            rows.append(
                dict(
                    year=y, locality=area, zone=zone,
                    fleet_icap_by_fuel={k: round(v, 1) for k, v in sorted(by_fuel.items())},
                    fleet_icap_mw=round(fleet_icap, 1), wind_mw=round(w, 1), solar_mw=round(s, 1), storage_mw=round(st, 1),
                    udr_icap_mw=udr, supply_icap_mw=round(supply, 1), requirement_icap_mw=r,
                    position=round(pos, 4), position_without_udr=round(pos_no_udr, 4), position_with_scr_info=round(pos_scr, 4),
                    scr_mw_info=scr, tsl_floor_info=round((peak - tsl) / peak, 4), below_tsl_floor=bool(pos < 1.0),
                    locality_price_kw_yr=(round(p_loc, 2) if p_loc is not None else None),
                    nyca_position_ledger=nyca_pos, nyca_price_kw_yr=round(p_nyca, 2), settled_price_kw_yr=round(settled, 2),
                    published_summer_margin_pct=pub_margin, published_position=round(1 + pub_margin / 100.0, 3),
                    published_spot_kw_yr=round(pub_spot * 12.0, 1),
                    gap_pts_vs_published=round((pos - (1 + pub_margin / 100.0)) * 100.0, 1),
                    gap_pts_scr_adjusted=round((pos_scr - (1 + pub_margin / 100.0)) * 100.0, 1),
                    gold_book_zone_summer_cap_mw=gb_total, gold_book_nj_sited_zone_j_mw=gb_nj,
                    model_fleet_minus_gold_book_mw=round(fleet_icap - gb_total, 1),
                    model_fleet_minus_gold_book_ex_nj_mw=round(fleet_icap - (gb_total - gb_nj), 1),
                )
            )
    # The 2025 NYC gas_st cohort (the D52 wave's NYC share) and the P1 test.
    led25 = ledgers[2025]
    nyc_gas_st = [r for r in led25["retirements"] if "_NYC_" in r["unit_id"] and r["fuel"] == "gas_st"]
    nyc_row = next(r for r in rows if r["year"] == 2025 and r["locality"] == "NYC")
    p1 = dict(
        nyc_gas_st_2025_mw=round(sum(r["mw"] for r in nyc_gas_st), 1), n_units=len(nyc_gas_st),
        settled_nyc_price=nyc_row["settled_price_kw_yr"],
        pass_threshold_kw_yr=37.6, cohort_passes=bool(nyc_row["settled_price_kw_yr"] >= 37.6),
        nyc_position_threshold=1.132, nyc_position=nyc_row["position"],
    )
    out = {"generated": _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"), "comparator_key": "589f031432b6dc7d",
           "rows": rows, "p1_nyc_gas_st_2025": p1,
           "zonal_renewable_nameplate_mw": {z: {"wind": round(a, 1), "solar": round(b, 1)} for z, (a, b) in ren_zone.items()},
           "storage_power_by_zone_mw": {z: round(v, 1) for z, v in stor_zone.items()}, "load_share": load_share}
    OUT_JSON.write_text(json.dumps(out, indent=1))
    hdr = "year locality | fleet ICAP  +VRE  +stor  +UDR = supply | req    | pos    (noUDR / +SCR) | P_loc   P_NYCA  settled | pub pos  pub spot | model-GB(exNJ)"
    print(hdr)
    for r in rows:
        print(
            f"{r['year']} {r['locality']:<11}| {r['fleet_icap_mw']:8.0f} {r['wind_mw']+r['solar_mw']:5.0f} {r['storage_mw']:5.0f} {r['udr_icap_mw']:5.0f} = {r['supply_icap_mw']:6.0f} | {r['requirement_icap_mw']:6.0f} | {r['position']:.3f} ({r['position_without_udr']:.3f} / {r['position_with_scr_info']:.3f}) | {str(r['locality_price_kw_yr']):>7} {r['nyca_price_kw_yr']:7.2f} {r['settled_price_kw_yr']:7.2f} | {r['published_position']:.3f} {r['published_spot_kw_yr']:8.1f} | {r['model_fleet_minus_gold_book_mw']:+.0f} ({r['model_fleet_minus_gold_book_ex_nj_mw']:+.0f})"
        )
    print("P1:", json.dumps(p1))
    for r in rows:
        print(r["year"], r["locality"], "by fuel:", r["fleet_icap_by_fuel"])


if __name__ == "__main__":
    main()
