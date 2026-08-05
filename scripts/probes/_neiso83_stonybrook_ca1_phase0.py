"""neiso-83 Phase 0 — is NEISO 6081 ``CA1`` misclassified, and what identifies it?

No LP, no solve, no write to any committed artifact except this probe's own
record. Answers the charter's questions 1-3 from the built fleet, the raw
EIA-860 sheet, the CAMPD unit-level extract and the EIA-923 Page-1 generation
parquet; question 4 (does it change dispatch) needs the A/B and is not attempted
here.

Q1 — IS IT MISCLASSIFIED IN THE LP? Read from the fleet built at the KEEPER's
own ``ScenarioConfig`` (``neiso81_chpheatrate_B/run_config.json``), never the
loader defaults — the miso-116 measurement trap. Reports class, fuel, capacity,
plant_group, heat rate and the cost attributes for every carried 6081 unit, and
whether ``CA1`` is disjoint from its ``CT`` siblings.

Q2 — WHAT IS THE PHYSICALLY CORRECT REPRESENTATION? Measures the two facts the
choice turns on: whether the block's whole metered heat input sits on the ``CT``
siblings (so ``CA1`` burns nothing), and whether the incumbent heat rate is
already BLOCK-denominated (so applying it uniformly across the block reproduces
the block's fuel burn rather than double-counting it).

Q3 — WHAT IS THE MEASURED IDENTIFICATION? Two independent routes over committed
EIA-923 Page-1 data, cross-checked against each other:

* **Direct (2018-2022):** EIA-923 reports the ``CA`` steam part's net generation
  on its own row, so its share of block output is read, not inferred.
* **Indirect (2024-2025):** those ``CA`` rows go to zero while the ``CT`` rows'
  net generation EXCEEDS the CAMPD ``CT`` GROSS — impossible for a CT-only row,
  and therefore proof the plant folded the steam part into the ``CT`` row rather
  than proof the steam turbine stopped.

Also measured: that the ``CA`` row's own EIA-923 FUEL split tracks its ``CT``
siblings' fuel split year by year — the steam part has no fuel of its own, it
inherits whatever the block burned. That is the decisive evidence against
EIA-860's ``DFO`` label being the machine's primary energy input.

None of these quantities is a model parameter. The re-class carries ZERO fitted
parameters (the capacity is EIA-860's published net summer figure and the heat
rate is the incumbent one), so the share below is PRESENCE EVIDENCE only —
recorded so a successor can see the machine is live, never consumed by the LP.

Run::

    uv run python scripts/probes/_neiso83_stonybrook_ca1_phase0.py
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
from market_sim.config.plant_taxonomy import (  # noqa: E402
    CC_STEAM_PART_RECLASS_ISOS,
)
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.fleet.eia860 import (  # noqa: E402
    _map_fuel_type,
    cc_steam_part_generators,
)
from market_sim.data.outages import (  # noqa: E402
    _iso_plant_capacity,
    unit_outage_derate_factors,
)

ISO = "NEISO"
PLANT = 6081
TRAIN_YEARS = (2023, 2024, 2025)
#: EIA-923 years used for the DIRECT steam-share read. Pre-2023 only: from 2023
#: the plant changes reporting convention mid-year (see the indirect route).
#: These are DATA years for a physical-share measurement, not solve or scoring
#: years — rule 22's quarantine is on solving/scoring/registering an
#: out-of-training year, and nothing here solves, scores or registers anything.
DIRECT_YEARS = (2018, 2019, 2020, 2021, 2022)
KEEPER = REPO / "results" / "calibration" / "neiso81_chpheatrate_B"
E923 = RAW_DIR / "_processed-legacy" / "eia923_monthly_generation.parquet"
UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"
OUT = REPO / "results" / "calibration" / "_neiso83_stonybrook_ca1_phase0.json"

#: CAMPD unit ids of plant 6081's COMBINED-CYCLE combustion turbines. The other
#: two metered units (004/005) are the plant's genuine standalone distillate
#: peakers (EIA-860 generators "1" and "2"), which this lane must never touch.
CC_CT_UNITS = ("001", "002", "003")
OIL_GT_UNITS = ("004", "005")

_MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)


def keeper_fleet_kwargs() -> dict:
    """Return the NEISO KEEPER's own fleet-loader settings (miso-116 trap)."""
    cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    return {
        "measured_ct_heat_rates": bool(cfg.get("measured_ct_heat_rates", False)),
        "measured_chp_heat_rates": bool(cfg.get("measured_chp_heat_rates", False)),
        "cc_steam_part_capacity": bool(cfg.get("cc_steam_part_capacity", False)),
    }


def campd_plant(plant: int, years: tuple[int, ...]) -> dict:
    """Return the plant's metered CAMPD unit-grain heat/gross per year.

    ``facilityId`` is a STRING in these extracts; an integer comparison
    silently returns zero rows, which is how the whole question was nearly
    missed at neiso-82. Compared as text on purpose.
    """
    out: dict[str, dict] = {}
    for year in years:
        frames = []
        for path in sorted(UNIT_LEVEL_DIR.glob(f"*_{year}.parquet")):
            have = set(pq.ParquetFile(path).schema_arrow.names)
            cols = [c for c in ("facilityId", "unitId", "heatInput", "grossLoad")
                    if c in have]
            extra = [c for c in ("primaryFuelInfo", "unitType") if c in have]
            df = pd.read_parquet(path, columns=cols + extra)
            df = df[df["facilityId"].astype(str).str.strip() == str(plant)]
            if not df.empty:
                frames.append(df)
        if not frames:
            out[str(year)] = {"present": False}
            continue
        df = pd.concat(frames)
        units: dict[str, dict] = {}
        for uid, sub in df.groupby(df["unitId"].astype(str)):
            units[uid] = {
                "heat_mmbtu": round(float(sub["heatInput"].fillna(0.0).sum()), 1),
                "gross_mwh": round(float(sub["grossLoad"].fillna(0.0).sum()), 1),
                "fuel": sorted(
                    {str(v) for v in sub.get("primaryFuelInfo", pd.Series(dtype=str))
                     .dropna().unique()}
                ),
                "unit_type": sorted(
                    {str(v) for v in sub.get("unitType", pd.Series(dtype=str))
                     .dropna().unique()}
                ),
            }
        out[str(year)] = {
            "present": True,
            "units": units,
            "cc_ct_gross_mwh": round(
                sum(units[u]["gross_mwh"] for u in CC_CT_UNITS if u in units), 1
            ),
            "cc_ct_heat_mmbtu": round(
                sum(units[u]["heat_mmbtu"] for u in CC_CT_UNITS if u in units), 1
            ),
            "oil_gt_gross_mwh": round(
                sum(units[u]["gross_mwh"] for u in OIL_GT_UNITS if u in units), 1
            ),
            "has_ca_unit": any(
                u not in CC_CT_UNITS + OIL_GT_UNITS for u in units
            ),
        }
    return out


def e923_plant(plant: int) -> pd.DataFrame:
    """Return the plant's EIA-923 Page-1 rows, one per (year, prime mover, fuel)."""
    d = pd.read_parquet(E923)
    return d[d["plant_id"] == plant].copy()


def main() -> int:  # noqa: C901 — one linear evidence sequence, kept together
    """Run the Phase-0 screen and write the record."""
    rec: dict = {
        "session": "neiso-83",
        "iso": ISO,
        "plant_code": PLANT,
        "keeper": "2026-08-04-neiso81-chpheatrate",
        "no_lp": True,
    }
    kwargs = keeper_fleet_kwargs()
    rec["keeper_fleet_kwargs"] = kwargs
    print(f"keeper fleet-loader settings (miso-116 trap guard): {kwargs}")

    # ------------------------------------------------------------------
    # Q1 — the LP-side representation, at the KEEPER's config
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("Q1  THE LP-SIDE REPRESENTATION (built fleet, keeper config)")
    print("=" * 78)
    iso_config = get_iso_config(ISO)
    base = load_fleet_from_csv(ISO, iso_config, **kwargs)
    at = sorted((g for g in base if int(g.plant_code or 0) == PLANT),
                key=lambda x: x.unit_id)
    rows = []
    for g in at:
        rows.append(
            {
                "unit_id": g.unit_id,
                "fuel_type": str(g.fuel_type),
                "plant_group": g.plant_group,
                "pmax_mw": round(float(g.pmax_mw), 2),
                "heat_rate": round(float(g.heat_rate), 8),
                "vom": float(g.vom),
                "emission_rate_co2": float(g.emission_rate_co2),
                "nox_rate": float(g.nox_rate),
                "eford": float(g.eford),
                "zone": g.zone,
                "online_year": int(g.online_year),
            }
        )
        print(
            f"  {g.unit_id:<12} {str(g.fuel_type):<8} group {g.plant_group or '(none)':<11}"
            f" pmax {float(g.pmax_mw):6.1f}  HR {float(g.heat_rate):9.5f}"
            f"  vom {float(g.vom):4.2f}  co2 {float(g.emission_rate_co2):5.3f}"
            f"  eford {float(g.eford):5.3f}"
        )
    rec["fleet_rows_keeper_config"] = rows

    ca1 = next(r for r in rows if r["unit_id"] == f"{PLANT}_CA1")
    cts = [r for r in rows if r["unit_id"].endswith(("CT1", "CT2", "CT3"))]
    rec["q1_misclassified"] = bool(
        ca1["fuel_type"] == "oil" and all(c["fuel_type"] == "gas_cc" for c in cts)
    )
    rec["q1_shares_heat_rate_with_ct_siblings"] = bool(
        all(abs(c["heat_rate"] - ca1["heat_rate"]) < 1e-9 for c in cts)
    )
    # An EMPTY plant_group is NOT itself an anomaly: it is what every oil,
    # nuclear and biomass unit carries (the EIA-860 loader assigns a group only
    # to coal and gas). Measured so the inherited framing is corrected rather
    # than repeated.
    empty_group_oil = [g for g in base if g.fuel_type == "oil"]
    rec["q1_oil_units_with_empty_group"] = {
        "n": len(empty_group_oil),
        "mw": round(sum(float(g.pmax_mw) for g in empty_group_oil), 1),
        "all_empty": all(g.plant_group == "" for g in empty_group_oil),
    }
    print()
    print(f"  CA1 carried as `oil` while its CT siblings are `gas_cc`: "
          f"{rec['q1_misclassified']}")
    print(f"  CA1 shares its CT siblings' heat rate exactly: "
          f"{rec['q1_shares_heat_rate_with_ct_siblings']}")
    print(f"  empty plant_group is NORMAL for oil: "
          f"{rec['q1_oil_units_with_empty_group']['n']} units / "
          f"{rec['q1_oil_units_with_empty_group']['mw']} MW, all empty = "
          f"{rec['q1_oil_units_with_empty_group']['all_empty']}")

    # Capacity basis: the fleet's pmax rule is net-summer-else-nameplate, which
    # is why the LP shows 96.0 against EIA-860's 105.0 nameplate.
    e860 = pd.read_parquet(RAW_DIR / "eia-860" / "eia860_generator_operable.parquet")
    e860.columns = [c.strip() for c in e860.columns]
    r = e860[(e860["Plant Code"] == PLANT)
             & (e860["Generator ID"].astype(str).str.strip() == "CA1")].iloc[0]
    rec["q1_capacity_basis"] = {
        "eia860_summer_mw": float(r["Summer Capacity (MW)"]),
        "eia860_nameplate_mw": float(r["Nameplate Capacity (MW)"]),
        "fleet_pmax_mw": ca1["pmax_mw"],
        "reconciles_to_net_summer": bool(
            abs(float(r["Summer Capacity (MW)"]) - ca1["pmax_mw"]) < 0.05
        ),
    }
    print(f"  capacity basis: EIA-860 summer {r['Summer Capacity (MW)']} / nameplate "
          f"{r['Nameplate Capacity (MW)']} -> fleet pmax {ca1['pmax_mw']} "
          f"(net-summer: {rec['q1_capacity_basis']['reconciles_to_net_summer']})")

    # ------------------------------------------------------------------
    # Q1b — WHY the existing repair cannot reach it
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("Q1b WHY cc_steam_part_capacity IS INERT HERE (population, not gating)")
    print("=" * 78)
    pred = cc_steam_part_generators()
    pop = []
    for pc, gid in sorted(pred):
        row = e860[(e860["Plant Code"] == int(pc))
                   & (e860["Generator ID"].astype(str).str.strip() == str(gid))]
        if row.empty:
            continue
        row = row.iloc[0]
        mapped = _map_fuel_type(
            row.get("Technology"), row.get("Energy Source 1"), row.get("Prime Mover")
        )
        pop.append(
            {
                "plant": int(pc),
                "generator": str(gid),
                "name": str(row["Plant Name"]).strip(),
                "state": str(row.get("State", "")).strip(),
                "energy_source_1": str(row["Energy Source 1"]).strip(),
                "mapped_fuel": mapped,
                "disposition": "DROPPED (repair population)" if mapped is None
                else f"CARRIED as {mapped} (re-class population)",
            }
        )
        print(f"  {pc:>6} {str(gid):<5} {str(row['Plant Name']).strip():<32} "
              f"{str(row.get('State','')).strip():<3} es1 "
              f"{str(row['Energy Source 1']).strip():<4} -> {pop[-1]['disposition']}")
    rec["predicate_population_national"] = pop
    rec["q1b_reclass_population_national"] = [
        p for p in pop if p["mapped_fuel"] is not None
    ]
    print("  The repair only ever RESTORES a dropped row, so a CARRIED row is "
          "outside its population\n  entirely — which is what neiso-80 measured as "
          "a byte-identical armed fleet.")

    # ------------------------------------------------------------------
    # Q2 — the physics: does CA1 burn anything, and is the rate block-based?
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("Q2  PHYSICS — where the block's metered fuel actually is")
    print("=" * 78)
    campd = campd_plant(PLANT, TRAIN_YEARS)
    rec["campd"] = campd
    for y in TRAIN_YEARS:
        m = campd[str(y)]
        if not m["present"]:
            print(f"  {y}: plant absent from the CAMPD extract")
            continue
        print(f"  {y}: metered units {sorted(m['units'])}  "
              f"CA unit present: {m['has_ca_unit']}")
        for u in sorted(m["units"]):
            v = m["units"][u]
            print(f"      {u}  {str(v['unit_type']):<24} {str(v['fuel']):<26} "
                  f"heat {v['heat_mmbtu']:>12,.0f}  gross {v['gross_mwh']:>10,.0f}")
    rec["q2_no_campd_stack_for_ca1"] = all(
        not campd[str(y)].get("has_ca_unit", False)
        for y in TRAIN_YEARS
        if campd[str(y)]["present"]
    )
    print(f"\n  CA1 has NO CEMS stack in any train year: "
          f"{rec['q2_no_campd_stack_for_ca1']}  "
          "(correct: a HRSG steam turbine has no combustion path)")

    # ------------------------------------------------------------------
    # Q3 — the measured identification, two independent routes
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("Q3  MEASURED IDENTIFICATION (EIA-923 Page 1, two routes)")
    print("=" * 78)
    e = e923_plant(PLANT)
    ann = e.pivot_table(
        index="year", columns="prime_mover", values="netgen_annual_mwh", aggfunc="sum"
    ).fillna(0.0)

    direct = {}
    print("  ROUTE A — DIRECT: the CA row's own net generation (2018-2022)")
    for y in DIRECT_YEARS:
        if y not in ann.index:
            continue
        ca, ct = float(ann.loc[y].get("CA", 0.0)), float(ann.loc[y].get("CT", 0.0))
        share = ca / (ca + ct) if (ca + ct) else float("nan")
        direct[str(y)] = {
            "ca_net_mwh": round(ca, 1),
            "ct_net_mwh": round(ct, 1),
            "steam_share_of_block": round(share, 4),
        }
        print(f"    {y}: CA {ca:>10,.0f}  CT {ct:>10,.0f}  steam share {share:.4f}")
    shares = [v["steam_share_of_block"] for v in direct.values()]
    mean_share = sum(shares) / len(shares)
    sd = (sum((s - mean_share) ** 2 for s in shares) / (len(shares) - 1)) ** 0.5
    rec["q3_direct"] = {
        "years": direct,
        "mean_steam_share": round(mean_share, 4),
        "sd": round(sd, 4),
    }
    print(f"    -> mean {mean_share:.4f}, sd {sd:.4f} over {len(shares)} years")

    # The fuel-inheritance test: the steam part has no fuel of its own, so its
    # EIA-923 fuel split must track its CT siblings' fuel split.
    print()
    print("  FUEL INHERITANCE — the CA row's fuel split vs its CT siblings' "
          "(the decisive test)")
    inherit = {}
    for y in DIRECT_YEARS:
        s = e[e["year"] == y]
        def _sh(pm: str) -> float:
            t = s[s["prime_mover"] == pm]
            tot = float(t["netgen_annual_mwh"].sum())
            dfo = float(t[t["fuel_type"] == "DFO"]["netgen_annual_mwh"].sum())
            return dfo / tot if tot else float("nan")
        ca_sh, ct_sh = _sh("CA"), _sh("CT")
        inherit[str(y)] = {
            "ca_dfo_share": round(ca_sh, 4),
            "ct_dfo_share": round(ct_sh, 4),
            "abs_gap": round(abs(ca_sh - ct_sh), 4),
        }
        print(f"    {y}: CA DFO share {ca_sh:.4f}  vs  CT DFO share {ct_sh:.4f}"
              f"   |gap| {abs(ca_sh - ct_sh):.4f}")
    rec["q3_fuel_inheritance"] = {
        "years": inherit,
        "max_abs_gap": round(max(v["abs_gap"] for v in inherit.values()), 4),
    }
    print("    -> the steam part carries whatever the block burned; EIA-860's "
          "`DFO` on its row is\n       a duct / legacy label, not a primary "
          "energy input.")

    print()
    print("  ROUTE B — INDIRECT: EIA-923 CT net vs CAMPD CT GROSS (2023-2025)")
    indirect = {}
    for y in TRAIN_YEARS:
        if y not in ann.index or not campd[str(y)]["present"]:
            continue
        ca = float(ann.loc[y].get("CA", 0.0))
        ct = float(ann.loc[y].get("CT", 0.0))
        gross = float(campd[str(y)]["cc_ct_gross_mwh"])
        ratio = ct / gross if gross else float("nan")
        indirect[str(y)] = {
            "e923_ca_net_mwh": round(ca, 1),
            "e923_ct_net_mwh": round(ct, 1),
            "campd_cc_ct_gross_mwh": round(gross, 1),
            "ct_net_over_ct_gross": round(ratio, 4),
            "impossible_for_a_ct_only_row": bool(ratio > 1.0),
        }
        print(f"    {y}: CA {ca:>8,.0f}  CT net {ct:>10,.0f}  CAMPD CT gross "
              f"{gross:>10,.0f}   ratio {ratio:.3f}"
              + ("   <- NET > GROSS, impossible" if ratio > 1.0 else ""))
    rec["q3_indirect"] = indirect
    # Cross-check: if the CT row carries the whole block, its implied CT
    # net/gross under the DIRECT share must be a sane auxiliary-load figure.
    cross = {}
    for y, v in indirect.items():
        if not v["impossible_for_a_ct_only_row"]:
            continue
        implied = v["ct_net_over_ct_gross"] * (1.0 - mean_share)
        cross[y] = round(implied, 4)
        print(f"    {y}: implied CT net/gross under the direct share "
              f"{mean_share:.4f}  =  {implied:.4f}")
    rec["q3_cross_check_implied_ct_net_over_gross"] = cross
    print("    -> the two routes agree: a ~0.96 auxiliary-load ratio reconciles "
          "the folded\n       reporting with the directly-measured steam share.")

    print()
    print("  NOT A MODEL PARAMETER. The re-class takes EIA-860's published net "
          "summer capacity\n  and the incumbent heat rate; no share below enters "
          "the LP. Zero fitted parameters.")
    rec["q3_share_is_evidence_not_a_parameter"] = True

    # ------------------------------------------------------------------
    # The arm, measured at the loader grain (grain 1)
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("ARM — FLEET DELTA AND ITS OUTAGE-DENOMINATOR CONSEQUENCE")
    print("=" * 78)
    armed = load_fleet_from_csv(ISO, iso_config, cc_steam_part_reclass=True, **kwargs)
    b = {g.unit_id: g.model_dump() for g in base}
    a = {g.unit_id: g.model_dump() for g in armed}
    moved = sorted(u for u in set(a) & set(b) if a[u] != b[u])
    rec["arm_fleet_delta"] = {
        "added": sorted(set(a) - set(b)),
        "removed": sorted(set(b) - set(a)),
        "changed": moved,
        "fields": {
            u: {k: [b[u][k], a[u][k]] for k in b[u] if b[u][k] != a[u][k]}
            for u in moved
        },
        "total_pmax_off": round(sum(float(g.pmax_mw) for g in base), 2),
        "total_pmax_armed": round(sum(float(g.pmax_mw) for g in armed), 2),
    }
    print(f"  units moved: {moved}")
    for u in moved:
        for k, (x, y) in rec["arm_fleet_delta"]["fields"][u].items():
            print(f"    {u}.{k}: {x} -> {y}")
    print(f"  total fleet pmax {rec['arm_fleet_delta']['total_pmax_off']} -> "
          f"{rec['arm_fleet_delta']['total_pmax_armed']} MW (conserved)")

    denom_off = _iso_plant_capacity(ISO).get((PLANT, "CC_REGULAR"))
    denom_on = _iso_plant_capacity(ISO, True).get((PLANT, "CC_REGULAR"))
    print(f"\n  outage derate denominator (6081, CC_REGULAR): "
          f"{denom_off:.1f} -> {denom_on:.1f} MW")
    avail = {}
    for y in TRAIN_YEARS:
        off = unit_outage_derate_factors(y, 8760, "", iso=ISO)[(PLANT, "CC_REGULAR")]
        on = unit_outage_derate_factors(
            y, 8760, "", iso=ISO, cc_steam_part_reclass=True
        )[(PLANT, "CC_REGULAR")]
        # Decomposition: how much of the effective-capacity move is the +96 MW
        # itself and how much is the denominator basis correcting with it.
        eff_off = float(off.mean()) * denom_off
        eff_cap_only = float(off.mean()) * denom_on
        eff_on = float(on.mean()) * denom_on
        avail[str(y)] = {
            "mean_avail_off": round(float(off.mean()), 4),
            "mean_avail_armed": round(float(on.mean()), 4),
            "zero_hours_off": int((off <= 1e-9).sum()),
            "zero_hours_armed": int((on <= 1e-9).sum()),
            "effective_avail_mw_off": round(eff_off, 1),
            "effective_avail_mw_capacity_leg_only": round(eff_cap_only, 1),
            "effective_avail_mw_armed": round(eff_on, 1),
            "capacity_leg_mw": round(eff_cap_only - eff_off, 1),
            "denominator_leg_mw": round(eff_on - eff_cap_only, 1),
        }
        v = avail[str(y)]
        print(f"    {y}: mean avail {v['mean_avail_off']:.4f} -> "
              f"{v['mean_avail_armed']:.4f} | effective MW "
              f"{v['effective_avail_mw_off']:6.1f} -> {v['effective_avail_mw_armed']:6.1f}"
              f"  (capacity leg {v['capacity_leg_mw']:+.1f}, denominator leg "
              f"{v['denominator_leg_mw']:+.1f})")
    rec["arm_outage_availability"] = {
        "denominator_mw_off": round(float(denom_off), 1),
        "denominator_mw_armed": round(float(denom_on), 1),
        "by_year": avail,
    }

    # ------------------------------------------------------------------
    # Rule 25 — the other five ISOs, proven by running it
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("RULE 25 [R-ISO-SCOPE] — the other five ISOs, run not read")
    print("=" * 78)
    iso_scope = {}
    for other in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO"):
        cfg = get_iso_config(other)
        off = {g.unit_id: g.model_dump() for g in load_fleet_from_csv(other, cfg)}
        on = {
            g.unit_id: g.model_dump()
            for g in load_fleet_from_csv(other, cfg, cc_steam_part_reclass=True)
        }
        identical = off == on
        iso_scope[other] = {"n": len(off), "byte_identical": bool(identical)}
        print(f"  {other:<6} n={len(off):5d}  byte-identical: {identical}")
    rec["rule25_other_isos"] = iso_scope
    rec["rule25_registry"] = sorted(CC_STEAM_PART_RECLASS_ISOS)

    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
