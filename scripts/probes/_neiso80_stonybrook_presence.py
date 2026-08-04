"""neiso-80 no-LP screen — is Stony Brook's ``CA`` steam part absent from NEISO's fleet?

Executes the pre-registered gates of
``results/calibration/PREREG-neiso80-chp-scope-gate-and-steam-part-2026-08-04.md``
§2.2 (properties Q1-Q6) **without touching the LP**.

miso-126 §8-2 handed NEISO 6081 Stony Brook ``CA1`` (96.0 MW ``DFO``) off with
presence still ``UNDETERMINED`` *even on its own basis-consistent test* — fleet
435.7 MW against EIA-860 446.6 including ``CA`` / 350.6 excluding it — and said
that lane "must resolve presence first". That is the whole question here.

Rule 25 ``[R-ISO-SCOPE]``: MISO's ``K`` transfers nothing. NEISO's parameters
are derived from NEISO's own market data and the cell enters as ``U``. CAISO
54912 Martinez is CAISO's and is **not** stamped here.

Gates, in the pre-registered order:

* **Q1 BASIS** — the comparison runs on the fleet's own ``pmax`` rule
  (summer-else-nameplate, coalesced per row; miso-126 §3's census-method
  correction). Both bases are reported; the coalesced one decides. If they
  disagree about the verdict the item stops ``UNDETERMINED``.
* **Q2 TOTALS, NEVER SIBLINGS** — presence is decided against the plant's
  EIA-860 operable **plant TOTAL**, never against block siblings (miso-125 §6,
  the test that caught 1004 Edwardsport as a 555 MW false positive).
* **Q3 PREDICATE MATCH** — 6081 ``CA1`` must satisfy
  ``fleet.eia860.cc_steam_part_generators`` verbatim.
* **Q4 THE FUEL MAP ACTUALLY DROPS IT** — ``_map_fuel_type`` returns ``None``
  for the row, and no ~96 MW 6081 generator is in NEISO's loaded fleet.
* **Q6 ``DFO`` IS NOT AUTOMATICALLY A DUCT FUEL** — the block's ``CT``
  siblings' own energy sources and the plant's metered CAMPD fuel mix, against
  the repair's premise that a ``CA`` row's ``Energy Source 1`` names the
  block's *supplementary* fuel rather than its primary energy input.

Q5 (re-running miso-126's five properties on NEISO's own data) is downstream of
Q2/Q3/Q4/Q6 and is only reached if those hold.

The fleet side is built from the NEISO KEEPER's own ``run_config.json``
settings, never the loader defaults — the miso-116 measurement trap
(``load_fleet_from_csv`` defaults ``measured_chp_heat_rates=False`` while
keepers arm it).

No LP, no solve, no write to any committed artifact. Run::

    uv run python scripts/probes/_neiso80_stonybrook_presence.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.fleet.eia860 import (  # noqa: E402
    _map_fuel_type,
    cc_steam_part_generators,
)

ISO = "NEISO"
PLANT = 6081
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results" / "calibration" / "neiso_c156_meter_screen_B"
UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"
OUT = REPO / "results" / "calibration" / "_neiso80_stonybrook_presence.json"

#: Pre-registered Q2 tolerance (prereg §2.2): the band inside which a fleet
#: total is called equal to an EIA-860 plant total. 1 MW, the same band
#: miso-126 pre-registered; it is a rounding tolerance, not a fitted number.
Q2_BAND = 1.0

#: miso-126 §8-2's published hand-off figures, reproduced here so this session
#: verifies them rather than restating them.
MISO126_HANDOFF = {
    "fleet_total_mw": 435.7,
    "eia860_plant_total_eff_mw": 446.6,
    "eia860_plant_total_excl_ca_eff_mw": 350.6,
    "status": "UNDETERMINED",
}


def keeper_fleet_kwargs() -> dict:
    """Return the NEISO KEEPER's own fleet-loader settings (miso-116 trap)."""
    cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    return {
        "measured_ct_heat_rates": bool(cfg.get("measured_ct_heat_rates", False)),
        "measured_chp_heat_rates": bool(cfg.get("measured_chp_heat_rates", False)),
    }


def eia860_operable() -> pd.DataFrame:
    """Return the raw EIA-860 operable generator sheet, normalized.

    ``mw_eff`` is the fleet's own ``pmax`` rule — ``net_summer_capacity_mw``
    ELSE ``nameplate_capacity_mw`` — so both sides of the presence test are on
    one basis (miso-126 §3). The summer-only basis is carried alongside so the
    published miso-125/126 record is reproduced, never overwritten.
    """
    d = pd.read_parquet(RAW_DIR / "eia-860" / "eia860_generator_operable.parquet")
    d.columns = [c.strip() for c in d.columns]
    d["pm"] = d["Prime Mover"].astype(str).str.strip().str.upper()
    d["es"] = d["Energy Source 1"].astype(str).str.strip().str.upper()
    d["es2"] = d["Energy Source 2"].astype(str).str.strip().str.upper()
    d["uc"] = d["Unit Code"].astype(str).str.strip()
    d["mw"] = pd.to_numeric(d["Summer Capacity (MW)"], errors="coerce")
    d["np_mw"] = pd.to_numeric(d["Nameplate Capacity (MW)"], errors="coerce")
    d["mw_eff"] = d["mw"].fillna(d["np_mw"])
    return d


def _status(fleet_total: float | None, total_all: float, total_no_ca: float) -> str:
    """Q2's pre-registered three-way verdict, against the plant TOTALS."""
    if fleet_total is None:
        return "UNDETERMINED"
    if abs(fleet_total - total_no_ca) <= Q2_BAND and total_all - total_no_ca > Q2_BAND:
        return "MISSING"
    if abs(fleet_total - total_all) <= Q2_BAND:
        return "REPRESENTED"
    return "UNDETERMINED"


def campd_fuel_mix(codes: set[int]) -> dict:
    """Return the plant's metered CAMPD unit-grain fuel/load profile per year.

    Q6's evidence: if the block genuinely burns ``DFO`` as a primary energy
    input rather than as a duct fuel, that shows up as oil in the plant's own
    metered fuel mix, not as a label on one EIA-860 row.
    """
    out: dict[str, dict] = {}
    for year in YEARS:
        frames = []
        for state in campd.states_for_iso(ISO):
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            cols = ["facilityId", "unitId", "heatInput", "grossLoad"]
            have = set(pq.ParquetFile(path).schema_arrow.names)
            extra = [c for c in ("primaryFuelInfo", "unitType") if c in have]
            df = pd.read_parquet(path, columns=cols + extra)
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if not df.empty:
                frames.append(df)
        if not frames:
            out[str(year)] = {"present": False}
            continue
        df = pd.concat(frames)
        by_unit = df.assign(
            heatInput=df["heatInput"].fillna(0.0),
            grossLoad=df["grossLoad"].fillna(0.0),
        ).groupby("unitId")[["heatInput", "grossLoad"]].sum()
        fuels: dict[str, list[str]] = {}
        for col in ("primaryFuelInfo", "unitType"):
            if col not in df.columns:
                continue
            for uid, sub in df.groupby("unitId"):
                vals = sorted({str(v) for v in sub[col].dropna().unique()})
                fuels.setdefault(str(uid), []).extend(vals)
        out[str(year)] = {
            "present": True,
            "units": {
                str(u): {
                    "heat_mmbtu": round(float(r["heatInput"]), 1),
                    "gross_mwh": round(float(r["grossLoad"]), 1),
                    "fuel": fuels.get(str(u), []),
                }
                for u, r in by_unit.iterrows()
            },
        }
    return out


def main() -> int:  # noqa: C901 — one linear gate sequence, kept together
    """Run the pre-registered Q1-Q6 screen and write the record."""
    rec: dict = {
        "session": "neiso-80",
        "iso": ISO,
        "plant_code": PLANT,
        "keeper": "2026-08-03-neiso-caiso156-meter-screen",
        "prereg": (
            "results/calibration/"
            "PREREG-neiso80-chp-scope-gate-and-steam-part-2026-08-04.md"
        ),
        "miso126_handoff": MISO126_HANDOFF,
    }
    d = eia860_operable()
    at_plant = d[d["Plant Code"] == PLANT]
    if at_plant.empty:
        raise SystemExit(f"{PLANT}: no EIA-860 operable rows — census is empty")

    kwargs = keeper_fleet_kwargs()
    print(f"keeper fleet-loader settings (miso-116 trap guard): {kwargs}")
    fleet = load_fleet_from_csv(ISO, get_iso_config(ISO), **kwargs)
    at_fleet = [g for g in fleet if int(g.plant_code or 0) == PLANT]
    fleet_total = sum(float(g.pmax_mw) for g in at_fleet) if at_fleet else None

    print()
    print("=" * 78)
    print(f"EIA-860 operable rows at {PLANT} {at_plant['Plant Name'].iloc[0].strip()}")
    print("=" * 78)
    for _, r in at_plant.sort_values("Generator ID").iterrows():
        print(
            f"  gen {str(r['Generator ID']):<6} pm {r['pm']:<3} es1 {r['es']:<4} "
            f"es2 {r['es2']:<5} uc {r['uc'] or '(none)':<8} "
            f"summer {('NaN' if pd.isna(r['mw']) else f'{r.mw:7.1f}'):>7} "
            f"nameplate {r['np_mw']:7.1f}  eff {r['mw_eff']:7.1f}  "
            f"op {r.get('Operating Year', '?')}"
        )
    rec["eia860_rows"] = [
        {
            "generator_id": str(r["Generator ID"]).strip(),
            "prime_mover": r["pm"],
            "energy_source_1": r["es"],
            "energy_source_2": r["es2"],
            "unit_code": r["uc"],
            "summer_mw": None if pd.isna(r["mw"]) else float(r["mw"]),
            "nameplate_mw": float(r["np_mw"]),
            "eff_mw": float(r["mw_eff"]),
            "operating_year": (
                None if pd.isna(r.get("Operating Year")) else int(r["Operating Year"])
            ),
        }
        for _, r in at_plant.sort_values("Generator ID").iterrows()
    ]

    print()
    print(f"NEISO fleet generators at {PLANT}:")
    for g in sorted(at_fleet, key=lambda x: x.unit_id):
        print(
            f"  {g.unit_id:<22} {g.plant_group:<12} pmax {float(g.pmax_mw):7.1f} MW  "
            f"fuel {getattr(g, 'fuel_type', '?')}"
        )
    if not at_fleet:
        print("  (none)")
    rec["fleet_rows"] = [
        {
            "unit_id": g.unit_id,
            "plant_group": g.plant_group,
            "pmax_mw": round(float(g.pmax_mw), 1),
            "fuel_type": str(getattr(g, "fuel_type", "")),
        }
        for g in sorted(at_fleet, key=lambda x: x.unit_id)
    ]

    # ------------------------------------------------------------------
    # Q1 BASIS + Q2 TOTALS
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("Q1 BASIS + Q2 PRESENCE (against the plant TOTALS, never siblings)")
    print("=" * 78)
    sum_all = float(at_plant["mw"].sum())
    sum_no_ca = float(at_plant[at_plant.pm != "CA"]["mw"].sum())
    eff_all = float(at_plant["mw_eff"].sum())
    eff_no_ca = float(at_plant[at_plant.pm != "CA"]["mw_eff"].sum())
    n_nan = int(at_plant["mw"].isna().sum())
    status_summer = _status(fleet_total, sum_all, sum_no_ca)
    status_eff = _status(fleet_total, eff_all, eff_no_ca)
    ft = "n/a" if fleet_total is None else f"{fleet_total:.1f}"
    print(f"  fleet total                       {ft:>9} MW")
    print(f"  EIA-860 total, summer basis       {sum_all:9.1f} MW "
          f"(excl CA {sum_no_ca:.1f}; NaN-summer rows {n_nan})")
    print(f"  EIA-860 total, summer-else-nameplate "
          f"{eff_all:6.1f} MW (excl CA {eff_no_ca:.1f})")
    print(f"  status, summer-only basis (miso-125 form)   {status_summer}")
    print(f"  status, basis-consistent (decides)          {status_eff}")
    q1_agree = status_summer == status_eff
    print(f"  Q1: bases agree -> {q1_agree}"
          + ("" if q1_agree else "  (prereg Q1 falsifier: verdict is basis-dependent)"))
    rec.update(
        fleet_total_mw=None if fleet_total is None else round(fleet_total, 1),
        eia860_plant_total_summer_mw=round(sum_all, 1),
        eia860_plant_total_excl_ca_summer_mw=round(sum_no_ca, 1),
        eia860_plant_total_eff_mw=round(eff_all, 1),
        eia860_plant_total_excl_ca_eff_mw=round(eff_no_ca, 1),
        eia860_rows_with_nan_summer=n_nan,
        status_summer_basis=status_summer,
        status=status_eff,
        q1_bases_agree=bool(q1_agree),
    )
    # Reproduce miso-126's published hand-off rather than restate it.
    drift = {
        k: (rec.get(k), v)
        for k, v in MISO126_HANDOFF.items()
        if k != "status" and abs(float(rec.get(k) or 0.0) - float(v)) > 0.05
    }
    if MISO126_HANDOFF["status"] != status_eff:
        drift["status"] = (status_eff, MISO126_HANDOFF["status"])
    rec["miso126_handoff_reproduced"] = not drift
    rec["miso126_handoff_drift"] = drift
    print(f"  miso-126 hand-off reproduced: {not drift}"
          + (f"  DRIFT {drift}" if drift else ""))

    # ------------------------------------------------------------------
    # Q3 PREDICATE MATCH
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("Q3 PREDICATE MATCH (fleet.eia860.cc_steam_part_generators, verbatim)")
    print("=" * 78)
    predicate = cc_steam_part_generators()
    hits = sorted(k for k in predicate if int(k[0]) == PLANT)
    print(f"  national predicate population: {len(predicate)} row(s)")
    for k in sorted(predicate):
        print(f"    {k}")
    print(f"  rows at {PLANT}: {hits or '(none)'}")
    rec["predicate_population"] = [list(map(str, k)) for k in sorted(predicate)]
    rec["predicate_hits_at_plant"] = [list(map(str, k)) for k in hits]
    rec["q3_predicate_match"] = bool(hits)

    # ------------------------------------------------------------------
    # Q4 THE FUEL MAP ACTUALLY DROPS IT
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("Q4 THE FUEL MAP DROPS IT (only a dropped row can be RESTORED)")
    print("=" * 78)
    ca_rows = at_plant[at_plant.pm == "CA"]
    q4 = {}
    for _, r in ca_rows.iterrows():
        tech = str(r.get("Technology", "")).strip()
        mapped = _map_fuel_type(tech, r["es"], r["pm"])
        gid = str(r["Generator ID"]).strip()
        q4[gid] = {"energy_source_1": r["es"], "technology": tech,
                   "mapped_fuel": None if mapped is None else str(mapped)}
        print(f"  gen {gid:<6} es1 {r['es']:<4} tech {tech[:34]:<35} "
              f"-> _map_fuel_type = {mapped}")
    ca_eff = float(ca_rows["mw_eff"].sum())
    near = [g for g in at_fleet if abs(float(g.pmax_mw) - ca_eff) <= Q2_BAND]
    print(f"  CA capacity at plant: {ca_eff:.1f} MW; fleet rows within "
          f"{Q2_BAND} MW of it: {[g.unit_id for g in near] or '(none)'}")
    rec["q4_ca_rows"] = q4
    rec["q4_ca_capacity_eff_mw"] = round(ca_eff, 1)
    rec["q4_fuel_map_drops_all_ca"] = all(v["mapped_fuel"] is None for v in q4.values())
    rec["q4_fleet_rows_matching_ca_capacity"] = [g.unit_id for g in near]

    # ------------------------------------------------------------------
    # Q6 DFO IS NOT AUTOMATICALLY A DUCT FUEL
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("Q6 IS `DFO` THE BLOCK'S DUCT FUEL OR ITS PRIMARY ENERGY INPUT?")
    print("=" * 78)
    blocks = sorted({r["uc"] for _, r in ca_rows.iterrows() if r["uc"]})
    sib = {}
    for uc in blocks:
        s = at_plant[(at_plant.uc == uc) & (at_plant.pm != "CA")]
        sib[uc] = [
            {
                "generator_id": str(r["Generator ID"]).strip(),
                "prime_mover": r["pm"],
                "energy_source_1": r["es"],
                "energy_source_2": r["es2"],
                "eff_mw": float(r["mw_eff"]),
                "operating_year": (
                    None if pd.isna(r.get("Operating Year"))
                    else int(r["Operating Year"])
                ),
            }
            for _, r in s.sort_values("Generator ID").iterrows()
        ]
        print(f"  block {uc}: siblings "
              + ", ".join(
                  f"{x['generator_id']}({x['prime_mover']}/{x['energy_source_1']}"
                  f"/{x['energy_source_2']}, {x['eff_mw']:.1f} MW, {x['operating_year']})"
                  for x in sib[uc]
              )
              or "  (none)")
    rec["q6_block_siblings"] = sib
    mix = campd_fuel_mix({PLANT})
    for y, m in mix.items():
        if not m.get("present"):
            print(f"  CAMPD {y}: plant not present in the unit-level extract")
            continue
        print(f"  CAMPD {y}:")
        for u, v in sorted(m["units"].items()):
            hr = (v["heat_mmbtu"] / v["gross_mwh"]) if v["gross_mwh"] else float("nan")
            print(f"    unit {u:<6} heat {v['heat_mmbtu']:>14,.1f} MMBtu  "
                  f"gross {v['gross_mwh']:>12,.1f} MWh  implied HR {hr:6.3f}  "
                  f"fuel {v['fuel']}")
    rec["q6_campd_fuel_mix"] = mix

    # ------------------------------------------------------------------
    # ROW-GRAIN RECONCILIATION — why the TOTALS test cannot decide this plant
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("ROW-GRAIN RECONCILIATION (what the TOTALS test could not see)")
    print("=" * 78)
    carried = {g.unit_id for g in at_fleet}
    recon = []
    for _, r in at_plant.sort_values("Generator ID").iterrows():
        gid = str(r["Generator ID"]).strip()
        uid = f"{PLANT}_{gid}"
        recon.append(
            {
                "generator_id": gid,
                "prime_mover": r["pm"],
                "energy_source_1": r["es"],
                "eff_mw": float(r["mw_eff"]),
                "carried_as": uid if uid in carried else None,
            }
        )
        print(f"  {gid:<7} pm {r['pm']:<3} es1 {r['es']:<4} eff {r['mw_eff']:7.1f} -> "
              + (f"CARRIED as {uid}" if uid in carried else "NOT CARRIED"))
    not_carried = sum(x["eff_mw"] for x in recon if x["carried_as"] is None)
    print(f"\n  EIA-860 capacity the thermal fleet does NOT carry: {not_carried:.1f} MW")
    print(f"  {eff_all:.1f} - {not_carried:.1f} = {eff_all - not_carried:.1f} MW"
          f"  vs fleet total {fleet_total:.1f} MW")
    rec["row_reconciliation"] = recon
    rec["eia860_capacity_not_carried_mw"] = round(not_carried, 1)
    rec["reconciles_exactly"] = bool(
        fleet_total is not None and abs(eff_all - not_carried - fleet_total) <= 0.05
    )

    # ------------------------------------------------------------------
    # INERTNESS PROOF — measured at the loader grain, never inferred
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("INERTNESS PROOF (arm the flag with NEISO enrolled and diff the fleet)")
    print("=" * 78)
    print("  miso-126 §4's discipline in reverse: a claim that a mechanism CANNOT")
    print("  move an ISO is proven by running it, not by reading the predicate.")
    import market_sim.config.plant_taxonomy as _tax
    import market_sim.data.fleet.eia860 as _e860
    _saved = _tax.CC_STEAM_PART_REPAIR_ISOS
    try:
        patched = frozenset(set(_saved) | {ISO})
        _tax.CC_STEAM_PART_REPAIR_ISOS = patched
        _e860.CC_STEAM_PART_REPAIR_ISOS = patched
        armed = load_fleet_from_csv(
            ISO, get_iso_config(ISO), cc_steam_part_capacity=True, **kwargs
        )
    finally:
        _tax.CC_STEAM_PART_REPAIR_ISOS = _saved
        _e860.CC_STEAM_PART_REPAIR_ISOS = _saved

    base_d = {g.unit_id: g.model_dump() for g in fleet}
    armed_d = {g.unit_id: g.model_dump() for g in armed}
    added = sorted(set(armed_d) - set(base_d))
    removed = sorted(set(base_d) - set(armed_d))
    changed = sorted(u for u in set(base_d) & set(armed_d) if base_d[u] != armed_d[u])
    print(f"  NEISO fleet size  off {len(base_d)}  armed {len(armed_d)}")
    print(f"  added {added or '(none)'}")
    print(f"  removed {removed or '(none)'}")
    print(f"  changed {changed or '(none)'}")
    identical = not (added or removed or changed)
    print(f"  BYTE-IDENTICAL: {identical}")
    rec["inertness_proof"] = {
        "iso_set_patched_to": sorted(set(_saved) | {ISO}),
        "fleet_size_off": len(base_d),
        "fleet_size_armed": len(armed_d),
        "added": added,
        "removed": removed,
        "changed": changed,
        "byte_identical": bool(identical),
    }

    # ------------------------------------------------------------------
    # verdict
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    print(f"  Q1 bases agree                 {rec['q1_bases_agree']}")
    print(f"  Q2 presence, TOTALS test       {rec['status']}")
    print(f"  Q3 predicate match             {rec['q3_predicate_match']}")
    print(f"  Q4 fuel map drops every CA row {rec['q4_fuel_map_drops_all_ca']}")
    print(f"  row-grain reconciles exactly   {rec['reconciles_exactly']}")
    print(f"  armed fleet byte-identical     {identical}")
    resolved = (
        "REPRESENTED"
        if not rec["q4_fuel_map_drops_all_ca"] and rec["q4_fleet_rows_matching_ca_capacity"]
        else rec["status"]
    )
    rec["presence_resolved"] = resolved
    print(f"\n  PRESENCE RESOLVED: {resolved}")
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
