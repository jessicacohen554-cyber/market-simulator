"""miso-125 no-LP probe — the CHP **prime-mover** rate split at MISO 55088.

Executes the four pre-registered gates of
``results/calibration/PREREG-miso125-chp-prime-mover-split-2026-08-04.md`` §3
without touching the LP:

* **KE1** prime-mover resolvability at CAMPD unit grain, with the miso-121
  empty-query guard (``facilityId`` is STRING-typed) and a reconciliation of the
  recomputed CEMS total against the committed artifact's ``cems_heat_mmbtu``.
* **KE2** the population of ``(plant, class)`` rows whose plant carries more than
  one target-class row, and which of them are applied (``flag == 'ok'``).
* **KE3** the split magnitudes ``hr_m = hr_plant * (f_m / g_m)`` and the
  INERT-BY-ARITHMETIC band (2 % of the plant rate, priced at the keeper's own
  gas).
* **KE4** the INERT-BY-MARGINALITY route, read from the keeper's COMMITTED
  ``hourly/class_hourly_<year>.parquet`` sidecars — no replay. The sidecar
  schema is ``(year, pass, klass, hour, mw)``, which carries **no marginality
  and no bound flags**, so this reports the dispatch-freedom statistics it can
  actually support and says so, rather than substituting a proxy for
  marginality (prereg §3 KE4).

No LP, no solve, no write to any committed artifact. Run::

    uv run python scripts/probes/_miso125_chp_prime_mover_split.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402

ISO = "MISO"
VINTAGE = 2023
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results" / "calibration" / "miso124_dualfuel_B"
UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"
OUT = REPO / "results" / "calibration" / "_miso125_prime_mover_split.json"

#: Prime-mover family prefixes, taken verbatim from the derive module
#: (``scripts/data/derive_chp_power_only_heat_rates.py`` ``_CC_PREFIX`` /
#: ``_CT_PREFIX``) so the probe and the derive cannot disagree about bucketing.
_CC_PREFIX = "combined cycle"
_CT_PREFIX = "combustion turbine"

#: Keeper gas, ``miso124_dualfuel_B/meta.json`` — used only to price the KE3
#: band in $/MWh. Not a model input here.
KEEPER_GAS = {2023: 2.54, 2024: 2.19, 2025: 3.52}

#: Pre-registered KE3 band (prereg §3): a split under this is arithmetically
#: unable to reorder the plant's tranches against their neighbours.
KE3_BAND = 0.02


def family_of(unit_type: str) -> str:
    """Bucket a CAMPD ``unitType`` string into a prime-mover family."""
    s = str(unit_type).strip().lower()
    if s.startswith(_CC_PREFIX):
        return "CC"
    if s.startswith(_CT_PREFIX):
        return "CT"
    return "OTHER"


def unit_table(codes: set[int], year: int) -> pd.DataFrame:
    """Return annual per-unit CEMS totals for ``codes``, with family labels.

    Mirrors the derive's own read exactly: ``facilityId`` is STRING-typed in the
    CAMPD extracts, so it is coerced numerically BEFORE the membership filter
    (miso-121 hit the silent-empty-match trap twice), ``grossLoad`` is null —
    not zero — for a unit with no gross-load channel, and both channels are
    filled before aggregating.
    """
    frames: list[pd.DataFrame] = []
    for state in campd.states_for_iso(ISO):
        path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path,
            columns=["facilityId", "unitId", "heatInput", "grossLoad", "unitType"],
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)]
        if df.empty:
            continue
        frames.append(
            df.assign(
                heatInput=df["heatInput"].fillna(0.0),
                grossLoad=df["grossLoad"].fillna(0.0),
            )
        )
    if not frames:
        return pd.DataFrame(
            columns=["facilityId", "unitId", "heatInput", "grossLoad", "unitType"]
        )
    raw = pd.concat(frames, ignore_index=True)
    by_unit = (
        raw.groupby(["facilityId", "unitId"])
        .agg(
            heatInput=("heatInput", "sum"),
            grossLoad=("grossLoad", "sum"),
            unitType=("unitType", "first"),
        )
        .reset_index()
    )
    by_unit["family"] = by_unit["unitType"].map(family_of)
    by_unit["dark"] = (by_unit["grossLoad"] <= 0.0) & (by_unit["heatInput"] > 0.0)
    return by_unit


def main() -> int:
    rec: dict = {"session": "miso-125", "iso": ISO, "vintage": VINTAGE}

    art_path = PROCESSED_DIR / f"chp_power_only_heat_rates_{ISO}.csv"
    art = pd.read_csv(art_path)

    # ---------------- KE2: population scope -------------------------------
    print("=" * 78)
    print("KE2 — population: plants carrying MORE THAN ONE target-class row")
    print("=" * 78)
    counts = art.groupby("plant_code")["plant_group"].nunique()
    multi = sorted(counts[counts > 1].index.astype(int).tolist())
    ke2_rows = []
    for code in multi:
        sub = art[art["plant_code"] == code]
        for r in sub.itertuples(index=False):
            ke2_rows.append(
                {
                    "plant_code": int(r.plant_code),
                    "plant_name": str(r.plant_name),
                    "plant_group": str(r.plant_group),
                    "class_capacity_mw": float(r.class_capacity_mw),
                    "heat_rate": None if pd.isna(r.heat_rate) else float(r.heat_rate),
                    "flag": str(r.flag),
                    "applied": str(r.flag) == "ok",
                }
            )
        print(
            f"  {code:<7} {sub['plant_name'].iloc[0][:38]:<38} "
            + " | ".join(
                f"{r.plant_group} {r.class_capacity_mw:>7.1f}MW {r.flag}"
                for r in sub.itertuples(index=False)
            )
        )
    applied_multi = sorted({r["plant_code"] for r in ke2_rows if r["applied"]})
    applied_mw = sum(r["class_capacity_mw"] for r in ke2_rows if r["applied"])
    print(f"\n  multi-class plants:            {multi}")
    print(f"  with >=1 APPLIED (ok) row:     {applied_multi}")
    print(f"  applied capacity in scope:     {applied_mw:,.1f} MW")
    rec["KE2"] = {
        "multi_class_plants": multi,
        "applied_multi_class_plants": applied_multi,
        "applied_capacity_mw": round(applied_mw, 3),
        "rows": ke2_rows,
    }

    if not applied_multi:
        print("\n  KE2 FAIL — no applied multi-class plant. Nothing to correct.")
        rec["KE2"]["verdict"] = "FAIL_NO_POPULATION"
        OUT.write_text(json.dumps(rec, indent=1))
        return 0
    rec["KE2"]["verdict"] = "PASS"

    # ---------------- KE1: prime-mover resolvability ----------------------
    print()
    print("=" * 78)
    print("KE1 — prime-mover resolvability at CAMPD unit grain")
    print("=" * 78)
    codes = set(applied_multi)
    ke1: dict = {"guard_empty_query": None, "per_year": {}}
    per_year_units: dict[int, pd.DataFrame] = {}
    for year in YEARS:
        ut = unit_table(codes, year)
        per_year_units[year] = ut
        if ut.empty:
            print(f"  {year}: EMPTY — facilityId filter matched zero rows")
            ke1["per_year"][str(year)] = {"empty": True}
            continue
        print(f"\n  --- {year} ---")
        print(
            f"  {'unit':<8}{'family':<8}{'unitType':<34}"
            f"{'heat MMBtu':>14}{'gross MWh':>14}{'dark':>6}"
        )
        for r in ut.sort_values("heatInput", ascending=False).itertuples(index=False):
            print(
                f"  {str(r.unitId):<8}{r.family:<8}{str(r.unitType)[:33]:<34}"
                f"{r.heatInput:>14,.0f}{r.grossLoad:>14,.0f}{str(r.dark):>6}"
            )
        power = ut[~ut["dark"]]
        fams = sorted(power["family"].unique().tolist())
        ke1["per_year"][str(year)] = {
            "empty": False,
            "n_units": int(len(ut)),
            "n_power_train_units": int(len(power)),
            "power_train_families": fams,
            "n_families": len(fams),
            "unmapped_other_units": int((power["family"] == "OTHER").sum()),
            "cems_total_mmbtu": float(ut["heatInput"].sum()),
            "cems_dark_mmbtu": float(ut[ut["dark"]]["heatInput"].sum()),
        }
        print(
            f"  power-train families: {fams}  "
            f"(units {len(power)} of {len(ut)}; "
            f"unmapped OTHER {(power['family']=='OTHER').sum()})"
        )

    # guard (a): non-empty
    empty_years = [y for y in YEARS if per_year_units[y].empty]
    ke1["guard_empty_query"] = "PASS" if not empty_years else f"FAIL {empty_years}"

    # guard (b): reconcile the vintage year against the committed artifact
    committed = art[
        (art["plant_code"].isin(applied_multi)) & (art["flag"] == "ok")
    ].drop_duplicates("plant_code")
    recon = {}
    for r in committed.itertuples(index=False):
        code = int(r.plant_code)
        ut = per_year_units[VINTAGE]
        mine = float(ut[ut["facilityId"] == code]["heatInput"].sum())
        theirs = float(r.cems_heat_mmbtu) if not pd.isna(r.cems_heat_mmbtu) else np.nan
        ratio = mine / theirs if theirs else np.nan
        recon[str(code)] = {
            "probe_cems_mmbtu": round(mine, 1),
            "artifact_cems_mmbtu": None if np.isnan(theirs) else round(theirs, 1),
            "ratio": None if np.isnan(ratio) else round(ratio, 6),
        }
        print(
            f"\n  reconcile {code} @ {VINTAGE}: probe {mine:,.0f} vs artifact "
            f"{theirs:,.0f} MMBtu -> ratio {ratio:.6f}"
        )
    ke1["artifact_reconciliation"] = recon
    ke1_ok = (
        not empty_years
        and all(
            ke1["per_year"][str(y)].get("n_families", 0) >= 2
            and ke1["per_year"][str(y)].get("unmapped_other_units", 1) == 0
            for y in YEARS
        )
        and all(
            v["ratio"] is not None and abs(v["ratio"] - 1.0) < 0.01
            for v in recon.values()
        )
    )
    ke1["verdict"] = "PASS" if ke1_ok else "FAIL"
    print(f"\n  KE1 verdict: {ke1['verdict']}")
    rec["KE1"] = ke1

    # ---------------- KE3: split magnitude --------------------------------
    print()
    print("=" * 78)
    print("KE3 — split magnitude and the INERT-BY-ARITHMETIC band")
    print("=" * 78)
    ke3: dict = {"band": KE3_BAND, "plants": {}}
    for code in applied_multi:
        row = art[(art["plant_code"] == code)].iloc[0]
        hr_plant = float(row.heat_rate)
        entry: dict = {"hr_plant": hr_plant, "per_year": {}}
        for year in YEARS:
            ut = per_year_units[year]
            power = ut[(ut["facilityId"] == code) & (~ut["dark"])]
            tot_f = float(power["heatInput"].sum())
            tot_g = float(power["grossLoad"].sum())
            if tot_f <= 0 or tot_g <= 0:
                entry["per_year"][str(year)] = {"unavailable": True}
                continue
            fam: dict = {}
            for m, sub in power.groupby("family"):
                f_m = float(sub["heatInput"].sum()) / tot_f
                g_m = float(sub["grossLoad"].sum()) / tot_g
                hr_m = hr_plant * (f_m / g_m) if g_m > 0 else np.nan
                fam[str(m)] = {
                    "fuel_share": round(f_m, 6),
                    "gen_share": round(g_m, 6),
                    "ratio": round(f_m / g_m, 6) if g_m > 0 else None,
                    "hr_m": round(hr_m, 4),
                    "delta_vs_plant_pct": round(100.0 * (hr_m / hr_plant - 1.0), 3),
                }
            # identity check: sum_m g_m * hr_m == hr_plant
            ident = sum(v["gen_share"] * v["hr_m"] for v in fam.values())
            fam_max = max(abs(v["hr_m"] / hr_plant - 1.0) for v in fam.values())
            entry["per_year"][str(year)] = {
                "families": fam,
                "identity_sum_g_hr": round(ident, 6),
                "identity_error": round(abs(ident - hr_plant), 9),
                "max_abs_rel_delta": round(fam_max, 6),
                "band_dollars_per_mwh": {
                    str(y): round(KE3_BAND * hr_plant * KEEPER_GAS[y], 4)
                    for y in YEARS
                },
            }
            print(f"\n  --- plant {code}, {year} (hr_plant = {hr_plant:.4f}) ---")
            for m, v in sorted(fam.items()):
                print(
                    f"    {m:<6} f={v['fuel_share']:.4f}  g={v['gen_share']:.4f}  "
                    f"f/g={v['ratio']:.4f}  hr={v['hr_m']:>8.4f}  "
                    f"({v['delta_vs_plant_pct']:+.2f} % vs plant)"
                )
            print(
                f"    identity  sum(g*hr) = {ident:.6f}  vs hr_plant "
                f"{hr_plant:.6f}   err {abs(ident-hr_plant):.2e}"
            )
            print(f"    max |rel delta| = {fam_max:.4f}   band = {KE3_BAND}")
        ke3["plants"][str(code)] = entry
    overall_max = max(
        y["max_abs_rel_delta"]
        for p in ke3["plants"].values()
        for y in p["per_year"].values()
        if "max_abs_rel_delta" in y
    )
    ke3["overall_max_abs_rel_delta"] = round(overall_max, 6)
    ke3["verdict"] = "INERT_BY_ARITHMETIC" if overall_max < KE3_BAND else "LIVE"
    print(f"\n  overall max |rel delta| = {overall_max:.4f}  ->  KE3 {ke3['verdict']}")
    rec["KE3"] = ke3

    # ---------------- KE4: marginality / dispatch freedom -----------------
    print()
    print("=" * 78)
    print("KE4 — INERT-BY-MARGINALITY, from the keeper's COMMITTED sidecars")
    print("=" * 78)
    print(
        "  sidecar schema is (year, pass, klass, hour, mw): it carries NO\n"
        "  marginality flag and NO bound flags, so clause (a) of prereg KE4 is\n"
        "  NOT ANSWERABLE from committed artifacts. Reported below is clause\n"
        "  (b) only — dispatch freedom — stated as such, not as a proxy for\n"
        "  marginality (prereg 3 KE4).\n"
    )
    ke4: dict = {
        "clause_a_marginal_share": "NOT_ANSWERABLE_FROM_COMMITTED_SIDECARS",
        "per_year": {},
    }
    for year in YEARS:
        path = KEEPER / "hourly" / f"class_hourly_{year}.parquet"
        if not path.exists():
            ke4["per_year"][str(year)] = {"missing": True}
            continue
        d = pd.read_parquet(path)
        d = d[d["pass"] == "P1"]
        yr: dict = {}
        for klass in ("CC_CHP", "CT_CHP"):
            s = d[d["klass"] == klass]["mw"].to_numpy(dtype=float)
            if s.size == 0:
                yr[klass] = {"absent": True}
                continue
            lo = float(s.min())
            n_at_min = int(np.isclose(s, lo, rtol=0, atol=1e-3).sum())
            yr[klass] = {
                "hours": int(s.size),
                "min_mw": round(lo, 4),
                "max_mw": round(float(s.max()), 4),
                "mean_mw": round(float(s.mean()), 4),
                "std_mw": round(float(s.std()), 6),
                "cv": round(float(s.std() / s.mean()), 6) if s.mean() else None,
                "n_distinct_values": int(np.unique(np.round(s, 3)).size),
                "share_hours_at_annual_min": round(n_at_min / s.size, 6),
                "annual_twh": round(float(s.sum()) / 1e6, 4),
            }
            v = yr[klass]
            print(
                f"  {year} {klass:<7} hours {v['hours']}  min {v['min_mw']:.1f}  "
                f"max {v['max_mw']:.1f}  cv {v['cv']:.4f}  "
                f"distinct {v['n_distinct_values']}  "
                f"at-min {v['share_hours_at_annual_min']:.4f}  "
                f"{v['annual_twh']:.3f} TWh"
            )
        ke4["per_year"][str(year)] = yr
    # clause (b): pinned in >99 % of hours in ALL years, BOTH classes
    def pinned(v: dict) -> bool:
        return bool(v.get("share_hours_at_annual_min", 0.0) > 0.99)

    all_pinned = all(
        pinned(ke4["per_year"][str(y)].get(k, {}))
        for y in YEARS
        for k in ("CC_CHP", "CT_CHP")
        if not ke4["per_year"][str(y)].get(k, {}).get("absent")
    )
    ke4["clause_b_all_pinned_gt_99pct"] = bool(all_pinned)
    ke4["verdict"] = "INERT_BY_MARGINALITY" if all_pinned else "LIVE_OR_UNDETERMINED"
    print(f"\n  KE4 clause (b) all-pinned>99%: {all_pinned}  ->  {ke4['verdict']}")
    rec["KE4"] = ke4

    rec["KE_R"] = ke_r(art, per_year_units)

    OUT.write_text(json.dumps(rec, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def ke_r(art: pd.DataFrame, per_year_units: dict[int, pd.DataFrame]) -> dict:
    """Validity check the pre-registration did NOT anticipate — and it REFUTES.

    Prereg §2 property 2 states the construction's load-bearing assumption: the
    gross-to-net factor must be common **across families at one plant**. This
    tests it, because KE3 came back with ``hr_CC > hr_CT`` — backwards from
    turbine physics, which is the signature of a denominator defect rather than
    a real efficiency ordering.

    Four steps, each a measurement:

    * **R1** eGRID ``PLNGENAN`` against the CEMS power-train GROSS total. Net
      cannot exceed gross on the same machines, so a ratio > 1 is proof that
      eGRID counts generation CEMS never metered.
    * **R2** the implied capacity factor on the capacity the LP actually holds.
    * **R3** the EIA-860 generator roster, which names the missing machine.
    * **R4** the systemic census: ``CA``-prime-mover generators whose own
      ``Energy Source 1`` is not ``NG`` but which share a ``Unit Code`` with
      ``NG`` ``CT`` siblings — i.e. the steam part of a gas-fired combined-cycle
      block — cross-checked against each ISO's loaded fleet so a row is only
      called missing when it is measurably absent.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    print()
    print("=" * 78)
    print("KE-R — validity of the construction's own assumption (NOT pre-registered)")
    print("=" * 78)
    out: dict = {}

    code = 55088
    row = art[(art["plant_code"] == code) & (art["plant_group"] == "CC_CHP")].iloc[0]
    net_mwh = float(row.net_mwh)
    hr_plant = float(row.heat_rate)

    # ---- R1: net vs gross ------------------------------------------------
    r1 = {}
    for year in YEARS:
        ut = per_year_units[year]
        power = ut[(ut["facilityId"] == code) & (~ut["dark"])]
        gross = float(power["grossLoad"].sum())
        r1[str(year)] = {
            "cems_power_train_gross_mwh": round(gross, 1),
            "egrid_plngenan_net_mwh": round(net_mwh, 1),
            "net_over_gross": round(net_mwh / gross, 4) if gross else None,
            "unmetered_mwh": round(net_mwh - gross, 1),
        }
    print(
        f"  R1 eGRID PLNGENAN {net_mwh:,.0f} net MWh vs CEMS power-train GROSS "
        f"{r1[str(VINTAGE)]['cems_power_train_gross_mwh']:,.0f} MWh"
    )
    print(
        f"     net/gross = {r1[str(VINTAGE)]['net_over_gross']}  -> "
        f"{r1[str(VINTAGE)]['unmetered_mwh']:,.0f} MWh eGRID counts and CEMS "
        f"never metered. NET CANNOT EXCEED GROSS on the same machines."
    )
    out["R1_net_vs_gross"] = r1

    # ---- R2: implied capacity factor on the LP's own capacity ------------
    fleet_mw = float(
        art[(art["plant_code"] == code) & (art["flag"] == "ok")][
            "class_capacity_mw"
        ].sum()
    )
    cf = net_mwh / (fleet_mw * 8760.0)
    out["R2_implied_cf"] = {
        "model_fleet_capacity_mw": fleet_mw,
        "egrid_net_mwh": round(net_mwh, 1),
        "implied_capacity_factor": round(cf, 4),
        "physically_possible": bool(cf <= 1.0),
    }
    print(
        f"\n  R2 implied CF on the LP's {fleet_mw:,.1f} MW = {cf:.1%}  "
        f"-> physically possible: {cf <= 1.0}"
    )

    # ---- R3 + R4: EIA-860 roster and the systemic census -----------------
    d = pd.read_parquet(RAW_DIR / "eia-860" / "eia860_generator_operable.parquet")
    d.columns = [c.strip() for c in d.columns]
    d["pm"] = d["Prime Mover"].astype(str).str.strip().str.upper()
    d["es"] = d["Energy Source 1"].astype(str).str.strip().str.upper()
    d["uc"] = d["Unit Code"].astype(str).str.strip()
    d["mw"] = pd.to_numeric(d["Summer Capacity (MW)"], errors="coerce")

    roster = d[d["Plant Code"] == code][
        ["Generator ID", "Technology", "pm", "uc", "mw", "es"]
    ]
    out["R3_eia860_roster_55088"] = roster.to_dict(orient="records")
    print("\n  R3 EIA-860 roster at 55088:")
    for r in roster.itertuples(index=False):
        print(
            f"     {str(r[0]):<6}{str(r[1])[:34]:<35}pm={r.pm:<3} "
            f"unit={r.uc:<6}{r.mw:>7.1f} MW  fuel={r.es}"
        )

    cand = d[(d.pm == "CA") & (d.es != "NG") & (d.uc != "") & (d.uc.str.lower() != "nan")]
    census = []
    for _, r in cand.sort_values("mw", ascending=False).iterrows():
        pc = int(r["Plant Code"])
        sib = d[
            (d["Plant Code"] == pc)
            & (d.uc == r["uc"])
            & (d.pm == "CT")
            & (d.es == "NG")
        ]
        if not len(sib):
            continue
        census.append(
            {
                "plant_code": pc,
                "plant_name": str(r["Plant Name"]),
                "state": str(r["State"]),
                "generator_id": str(r["Generator ID"]),
                "unit_code": r["uc"],
                "summer_mw": float(r["mw"]) if pd.notna(r["mw"]) else None,
                "energy_source_1": r["es"],
                "ng_ct_siblings": int(len(sib)),
                "sibling_mw": round(float(sib["mw"].sum()), 1),
            }
        )
    # fleet-presence cross-check, so "missing" is measured and never inferred
    iso_of = {55088: "MISO", 1004: "MISO", 50973: "MISO", 6081: "NEISO", 54912: "CAISO"}
    fleets: dict[str, dict[int, float]] = {}
    for iso in sorted(set(iso_of.values())):
        f = load_fleet_from_csv(iso, get_iso_config(iso))
        agg: dict[int, float] = {}
        for g in f:
            agg[int(g.plant_code or 0)] = agg.get(int(g.plant_code or 0), 0.0) + float(
                g.pmax_mw
            )
        fleets[iso] = agg
    print("\n  R4 census — CA/non-NG steam parts of NG combined-cycle blocks:")
    print(
        "     presence is decided against the plant's EIA-860 TOTALS, not against\n"
        "     the block's siblings: a plant can host generators outside the block\n"
        "     (55088's standalone GTP1 does), so a sibling-relative test\n"
        "     mis-reads those as the missing steam part.\n"
    )
    for c in census:
        iso = iso_of.get(c["plant_code"], "?")
        fleet_total = fleets.get(iso, {}).get(c["plant_code"])
        at_plant = d[d["Plant Code"] == c["plant_code"]]
        eia_all = float(at_plant["mw"].sum())
        eia_no_ca = float(at_plant[at_plant.pm != "CA"]["mw"].sum())
        if fleet_total is None:
            status = "UNDETERMINED"
        elif abs(fleet_total - eia_no_ca) <= 1.0 and eia_all - eia_no_ca > 1.0:
            status = "MISSING"
        elif abs(fleet_total - eia_all) <= 1.0:
            status = "REPRESENTED"
        else:
            status = "UNDETERMINED"
        c.update(
            iso=iso,
            fleet_total_mw=None if fleet_total is None else round(fleet_total, 1),
            eia860_plant_total_mw=round(eia_all, 1),
            eia860_plant_total_excl_ca_mw=round(eia_no_ca, 1),
            status=status,
        )
        print(
            f"     {c['plant_code']:<7}{c['plant_name'][:31]:<32}{iso:<6}"
            f"{c['summer_mw']:>7.1f} MW {c['energy_source_1']:<4} | EIA-860 plant "
            f"{eia_all:>7.1f} (excl CA {eia_no_ca:>7.1f}) | fleet "
            f"{'n/a' if fleet_total is None else f'{fleet_total:7.1f}'}  ->  {status}"
        )
    miso_missing = sum(
        c["summer_mw"] for c in census if c["iso"] == "MISO" and c["status"] == "MISSING"
    )
    out["R4_census"] = census
    out["R4_miso_missing_mw"] = round(miso_missing, 1)
    print(f"\n     MISO capacity measurably missing: {miso_missing:,.1f} MW")

    out["verdict"] = "PREREGISTERED_CONSTRUCTION_REFUTED"
    out["reason"] = (
        "The construction's stated assumption (prereg 2 property 2 — a common "
        "gross-to-net factor across prime-mover families at one plant) is "
        "violated at the only plant it reaches: EIA-860 ST1 (250 MW, prime mover "
        "CA, Unit Code SINT shared with the two NG CT gas turbines, Energy Source "
        "1 = BFG) is the steam part of the combined-cycle block, has no CEMS "
        "stack, and is absent from the model fleet. Its generation is inside "
        "eGRID's PLNGENAN and outside CEMS grossLoad, so g_CC is structurally "
        "understated and the split returns hr_CC > hr_CT, backwards from turbine "
        "physics. The ST output cannot be attributed between the CC and CT "
        "families from any available source, so no repaired split is derivable "
        "here. Rule 14 [R-ACCURATE] named-exception case: the datum is defined "
        "on a different boundary than the model's representation."
    )
    print(f"\n  KE-R verdict: {out['verdict']}")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
