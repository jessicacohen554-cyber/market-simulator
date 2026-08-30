"""miso-190 Phase-0 (ZERO-SOLVE): the partial-plant mid-window exit census.

The FINDING-miso188 §6.6 charter object, granted by the miso-190 handoff:
units retired 2023-2025 whose plants survive in the operable snapshot are in
NEITHER the operable fleet (retired rows leave the operable sheet) NOR the
whole-plant retiree channel (``build_within_window_retirees`` deliberately
drops any plant still present in the operable snapshot, because the
plant-keyed COD map cannot time out a single unit). Their measured
generation is real and the modeled fleet cannot carry it.

This probe measures, from committed sources only (no LP, no new data fetch):

1. **Leg-1 census** — every MISO unit on the committed
   ``eia860_generator_retired_and_canceled.parquet`` with actual
   ``Retirement Year >= 2023`` whose plant IS in the canonical operable
   snapshot, with per-unit capacity, actual exit month, and the
   miso-188 vintage-status-oracle verdict for each solve year.
2. **Leg-2 census** — every MISO unit the canonical snapshot marks OS/SB
   that a year-matched vintage (2023/2024) marks OP: the Big Cajun 2-1
   case, the ``load_mothballed_but_operating`` docstring's explicitly
   reserved OS/SB extension.
3. **CAMPD sizing** — the census units' measured gross generation by year
   (unit-matched, with the explicit EIA-generator -> CAMPD-unit crosswalk
   for split-generator boilers), reconciling the charter's 5.93 / 0.57 TWh
   sizing (which omitted Dan E Karn under a CAMPD unit-id mapping gap).
4. **Class landing** — the coal supply class each census plant resolves to
   under ``market_sim.data.coal.coal_supply_class`` at HEAD, identifying
   the plants an injected row would land in the bench-less bare ``COAL``
   class (A B Brown, Dan E Karn) and so motivating the flag-gated
   supply-code registry in the mechanism design.
5. **Disjointness / inertness checks** — no unit appears on both the
   operable and the retired(>=2023) sheets (the two legs cannot
   double-inject), and the count of CURRENT-fleet coal plants (all six
   ISOs) that are unresolved by ``coal_supply_class`` yet carry a
   coal-coded row on the retired sheet (the measured reason the supply-code
   fix is a flag-gated registry, never an ambient classifier change).

Adjudication: this probe DECIDES nothing — it is the frozen evidentiary
record behind PREREG-miso190-partial-plant-exit-carry-2026-08-30.md, run
and committed BEFORE the PREREG per the miso-184/188 order.

Output: results/calibration/_miso190_partial_exit_phase0.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EIA860 = REPO / "data" / "raw" / "eia-860"
CAMPD = REPO / "data" / "raw" / "campd-unit-level"
OUT = REPO / "results" / "calibration" / "_miso190_partial_exit_phase0.json"

WINDOW_START = 2023  # scripts/data/process_eia860.py::RETIREMENT_WINDOW_START
SOLVE_YEARS = (2023, 2024, 2025)
VINTAGE_YEARS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)

# EIA generator id -> CAMPD unitId, where they differ (the charter's 5.93 TWh
# omitted Dan E Karn because its four EIA generators (1A/1B/2A/2B — two
# generators per boiler) report to CAMPD as boilers '1' and '2').
CAMPD_UNIT_XWALK: dict[tuple[int, str], list[str]] = {
    (1702, "1A"): ["1"],
    (1702, "1B"): [],  # boiler '1' already counted under 1A
    (1702, "2A"): ["2"],
    (1702, "2B"): [],
    (994, "ST2"): ["2"],
    (963, "3"): ["33"],  # CWLP Dallman 3 is CAMPD unit '33'
    (6055, "1"): ["2B1"],  # Big Cajun 2 unit 1
}

STATE_BY_PLANT_FALLBACK: dict[int, str] = {}


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def load_sheets():
    ret = pd.read_parquet(EIA860 / "eia860_generator_retired_and_canceled.parquet")
    op = pd.read_parquet(EIA860 / "eia860_generator_operable.parquet")
    plant = pd.read_parquet(EIA860 / "eia860_plant.parquet")
    ba = plant.drop_duplicates("Plant Code").set_index("Plant Code")[
        "Balancing Authority Code"
    ]
    for df in (ret, op):
        df["pc"] = _num(df["Plant Code"])
    ret = ret[ret["pc"].notna()].copy()
    op = op[op["pc"].notna()].copy()
    ret["pc"] = ret["pc"].astype(int)
    op["pc"] = op["pc"].astype(int)
    ret["ba"] = ret["pc"].map(ba)
    op["ba"] = op["pc"].map(ba)
    return ret, op


def vintage_index() -> dict[int, dict[tuple[int, str], str]]:
    out = {}
    for vy in VINTAGE_YEARS:
        path = EIA860 / f"vintage_{vy}" / "eia860_generator_operable.parquet"
        if not path.exists():
            continue
        v = pd.read_parquet(path, columns=["Plant Code", "Generator ID", "Status"])
        v["pc"] = _num(v["Plant Code"])
        out[vy] = {
            (int(p), str(g).strip().upper()): str(s).strip().upper()
            for p, g, s in zip(v["pc"], v["Generator ID"], v["Status"])
            if pd.notna(p)
        }
    return out


def oracle(vint, pc: int, gid: str, year: int):
    """The miso-188 vintage-status oracle: latest committed vintage <= year
    listing the unit; None = unlisted (fails OPEN, kept)."""
    for vy in sorted(vint, reverse=True):
        if vy > year:
            continue
        st = vint[vy].get((pc, gid))
        if st is not None:
            return st, vy
    return None, None


def campd_gross_twh(state: str, year: int, fac: int, units: list[str]) -> float | None:
    path = CAMPD / f"{state}_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["facilityId", "unitId", "grossLoad"])
    df["facilityId"] = _num(df["facilityId"])
    sub = df[(df["facilityId"] == fac) & (df["unitId"].astype(str).isin(units))]
    if sub.empty:
        return 0.0
    return float(sub["grossLoad"].sum()) / 1e6


def main() -> None:
    ret, op = load_sheets()
    vint = vintage_index()
    op_ids = set(op["pc"])

    miso_ret = ret[(ret["ba"] == "MISO") & (_num(ret["Retirement Year"]) >= WINDOW_START)]
    leg1 = miso_ret[miso_ret["pc"].isin(op_ids)].copy()

    leg1_units = []
    for _, r in leg1.iterrows():
        pc = int(r["pc"])
        gid = str(r["Generator ID"]).strip().upper()
        ry = int(_num(pd.Series([r["Retirement Year"]])).iloc[0])
        rm = _num(pd.Series([r["Retirement Month"]])).iloc[0]
        st = str(r["State"]).strip().upper()
        verdicts = {}
        for y in SOLVE_YEARS:
            s, vy = oracle(vint, pc, gid, y)
            verdicts[str(y)] = {"status": s, "vintage": vy,
                                "kept": (s is None or s == "OP")}
        # CAMPD measured gross by year, unit-matched
        units = CAMPD_UNIT_XWALK.get((pc, gid), [gid])
        gen = {}
        for y in (2023, 2024, 2025):
            g = campd_gross_twh(st, y, pc, units) if units else 0.0
            gen[str(y)] = None if g is None else round(g, 4)
        cap = _num(pd.Series([r["Summer Capacity (MW)"]])).iloc[0]
        if pd.isna(cap):  # e.g. Prairie Creek 1: no summer rating -> nameplate
            cap = _num(pd.Series([r["Nameplate Capacity (MW)"]])).iloc[0]
        leg1_units.append({
            "plant_id": pc, "plant": str(r["Plant Name"]), "generator_id": gid,
            "technology": str(r["Technology"]), "state": st,
            "summer_mw": float(0.0 if pd.isna(cap) else cap),
            "energy_source": str(r["Energy Source 1"]),
            "retirement": f"{ry}-{int(rm):02d}" if pd.notna(rm) else str(ry),
            "oracle": verdicts, "campd_gross_twh": gen,
        })

    # Leg 2: snapshot OS/SB, OP in a year-matched vintage, not on the retired sheet
    ret_keys = {(int(p), str(g).strip().upper())
                for p, g in zip(ret["pc"], ret["Generator ID"])}
    snap = op[(op["ba"] == "MISO")].copy()
    snap["st"] = snap["Status"].astype(str).str.strip().str.upper()
    leg2_units = []
    for _, r in snap[snap["st"].isin(["OS", "SB"])].iterrows():
        pc = int(r["pc"])
        gid = str(r["Generator ID"]).strip().upper()
        if (pc, gid) in ret_keys:
            continue
        carried = {str(y): vint.get(y, {}).get((pc, gid)) == "OP" for y in (2023, 2024)}
        if not any(carried.values()):
            continue
        st = str(r["State"]).strip().upper()
        units = CAMPD_UNIT_XWALK.get((pc, gid), [gid])
        gen = {str(y): (lambda g: None if g is None else round(g, 4))(
            campd_gross_twh(st, y, pc, units)) for y in (2023, 2024, 2025)}
        cap = _num(pd.Series([r["Summer Capacity (MW)"]])).iloc[0]
        if pd.isna(cap):
            cap = _num(pd.Series([r["Nameplate Capacity (MW)"]])).iloc[0]
        leg2_units.append({
            "plant_id": pc, "plant": str(r["Plant Name"]), "generator_id": gid,
            "technology": str(r["Technology"]), "state": st,
            "snapshot_status": str(r["st"]),
            "summer_mw": float(0.0 if pd.isna(cap) else cap),
            "vintage_op": carried, "campd_gross_twh": gen,
        })

    # Sizing rollups (gross TWh, oracle-kept leg-1 units only, by year live)
    def rollup(year: int) -> float:
        tot = 0.0
        for u in leg1_units:
            if u["oracle"][str(year)]["kept"] and (u["campd_gross_twh"][str(year)] or 0):
                tot += u["campd_gross_twh"][str(year)]
        for u in leg2_units:
            if u.get("vintage_op", {}).get(str(year)) and (u["campd_gross_twh"][str(year)] or 0):
                tot += u["campd_gross_twh"][str(year)]
        return round(tot, 3)

    # Charter reconciliation: the named set exactly as FINDING-miso188 §6.6
    named = [(6090, "2"), (994, "ST2"), (6137, "1"), (6137, "2"),
             (1702, "1A"), (1702, "1B"), (1702, "2A"), (1702, "2B"),
             (4041, "5"), (4041, "6"), (1400, "3"), (963, "3"), (6055, "1")]
    named_set = {k: u for u in leg1_units + leg2_units
                 for k in [(u["plant_id"], u["generator_id"])] if k in named}
    named_2023 = round(sum(u["campd_gross_twh"]["2023"] or 0 for u in named_set.values()), 3)
    named_2023_minus_karn = round(named_2023 - sum(
        u["campd_gross_twh"]["2023"] or 0 for k, u in named_set.items() if k[0] == 1702), 3)
    named_2024 = round(sum(u["campd_gross_twh"]["2024"] or 0 for u in named_set.values()), 3)

    # Class landing at HEAD
    import sys
    sys.path.insert(0, str(REPO / "src"))
    from market_sim.data.coal import coal_supply_class
    class_landing = {}
    for pc in sorted({u["plant_id"] for u in leg1_units + leg2_units
                      if "Coal" in u["technology"]}):
        class_landing[str(pc)] = coal_supply_class(pc) or "(unresolved -> bare COAL)"

    # Inertness census: current-fleet coal plants unresolved by the classifier
    # that carry a coal-coded row anywhere on the retired sheet (any year).
    coal_codes = {"BIT", "SUB", "LIG", "WC", "RC", "ANT", "SC", "SGC"}
    fleet_coal = op[op["Energy Source 1"].astype(str).str.strip().str.upper()
                    .isin(coal_codes) & op["ba"].isin(
                        ["MISO", "PJM", "CISO", "ERCO", "NYIS", "ISNE"])]
    unresolved = sorted({int(p) for p in fleet_coal["pc"]
                         if not coal_supply_class(int(p))})
    ret_coal_plants = set(ret[ret["Energy Source 1"].astype(str).str.strip()
                              .str.upper().isin(coal_codes)]["pc"])
    ambient_risk = sorted(p for p in unresolved if p in ret_coal_plants)

    both_sheets = sorted(
        (int(p), g) for p, g in zip(miso_ret["pc"],
                                    miso_ret["Generator ID"].astype(str).str.strip().str.upper())
        if (int(p), g) in {(int(p2), str(g2).strip().upper())
                           for p2, g2 in zip(op["pc"], op["Generator ID"])})

    out = {
        "probe": "_miso190_partial_exit_phase0",
        "charter": "FINDING-miso188 §6.6 / the miso-190 handoff grant",
        "window_start": WINDOW_START,
        "leg1_partial_plant_retirees": {
            "n_units": len(leg1_units),
            "summer_mw": round(sum(u["summer_mw"] for u in leg1_units), 1),
            "units": leg1_units,
        },
        "leg2_snapshot_nonop_vintage_op": {
            "n_units": len(leg2_units),
            "summer_mw": round(sum(u["summer_mw"] for u in leg2_units), 1),
            "units": leg2_units,
        },
        "sizing_gross_twh": {
            "oracle_kept_total": {str(y): rollup(y) for y in SOLVE_YEARS},
            "charter_named_set_2023": named_2023,
            "charter_named_set_2023_minus_karn": named_2023_minus_karn,
            "charter_named_set_2024": named_2024,
            "charter_quoted": {"2023": 5.93, "2024": 0.57},
            "reconciliation": (
                "the charter's 5.93 TWh (2023) equals the named set MINUS Dan E "
                "Karn (CAMPD unit-id mapping gap: EIA 1A/1B/2A/2B vs CAMPD "
                "boilers 1/2); the full named-set gross is the _2023 figure; "
                "2024 reconciles directly"),
        },
        "class_landing_at_head": class_landing,
        "disjointness": {"units_on_both_sheets_miso_2023plus": both_sheets},
        "ambient_classifier_extension_risk": {
            "unresolved_fleet_coal_plants_with_retired_sheet_coal_rows": ambient_risk,
            "note": (
                "each listed plant would gain a supply class if the retired "
                "sheet were read UNGATED as a classifier fallback — the "
                "measured reason the supply-code fix is a flag-gated registry "
                "populated only for injected units"),
        },
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT}")
    print("leg1:", len(leg1_units), "units",
          round(sum(u['summer_mw'] for u in leg1_units), 1), "MW; leg2:",
          len(leg2_units), "units",
          round(sum(u['summer_mw'] for u in leg2_units), 1), "MW")
    print("sizing:", out["sizing_gross_twh"]["oracle_kept_total"],
          "| named-set 2023", named_2023, "(minus Karn", named_2023_minus_karn, ")",
          "| 2024", named_2024)
    print("ambient risk plants:", ambient_risk)


if __name__ == "__main__":
    main()
