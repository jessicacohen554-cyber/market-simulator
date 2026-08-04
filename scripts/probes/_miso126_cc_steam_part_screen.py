"""miso-126 no-LP screen — the missing ``CA`` combined-cycle STEAM part at MISO.

Executes the pre-registered gates of
``results/calibration/PREREG-miso126-cc-steam-part-capacity-2026-08-04.md``
§2.1 (properties P1-P5) and §3 (KE1, KE3, KE4) **without touching the LP**.

The population is not searched for — it is *verified*. miso-125's ``ke_r`` R4
census is rebuilt verbatim (a ``CA``-prime-mover generator whose own
``Energy Source 1`` is not ``NG`` but which shares a ``Unit Code`` with ``NG``
``CT`` siblings at the same plant is the steam part of a gas-fired
combined-cycle block) and re-cross-checked against each plant's EIA-860
**TOTALS**, never against block siblings — the test that caught 1004
Edwardsport as a 555 MW false positive.

Gates, in the pre-registered order:

* **KE1** — population verification. Census + fleet-presence cross-check, with
  the two mandatory guards: EIA-860 ``Summer Capacity (MW)`` is NaN on some
  rows (Edwardsport's CT1/CT2), so plant totals are reconciled against
  ``Nameplate Capacity (MW)`` too and the candidate frame is asserted
  non-empty; and the fleet side is built from the KEEPER's own
  ``run_config.json`` settings, never the loader defaults (the miso-116
  measurement trap: ``measured_chp_heat_rates`` defaults False while the keeper
  arms it).
* **P1 ABSENCE** — fleet total == EIA-860 plant total EXCLUDING the ``CA`` rows.
* **P2 ONE METER, ONE RATE** — (a) the ``CA`` row's joined ``heat_rate`` equals
  its ``CT`` siblings'; (b) eGRID ``PLNGENAN`` implies an IMPOSSIBLE capacity
  factor on the present fleet and a possible one on the repaired fleet.
* **P3 DESIGN-SHARE COHERENCE** — the steam part's implied generation share of
  the block against its EIA-860 NAMEPLATE share of the block, the
  manufacturer's own design split. This is the falsifiable form of the
  miso-125 §4 let-down-turbine doubt.
* **P5 NO OTHER ISO MOVES** — deferred to the post-implementation check
  (``_miso126_fleet_delta.py``); nothing here can move another ISO.
* **KE3 INERT-BY-DISPATCH** — the share of hours the repaired capacity would
  NOT dispatch, from the keeper's COMMITTED sidecars and the block's own
  marginal cost at the keeper's gas prices. No replay.
* **KE4 INERT-BY-BINDING** — reported honestly: the committed sidecar is CLASS
  grain with no bound flag, so plant-grain binding is NOT measurable from it
  and no ``I`` is declared on this route.

P4 (artifact stability) is a re-derive diff and lives in the arm, not here.

No LP, no solve, no write to any committed artifact. Run::

    uv run python scripts/probes/_miso126_cc_steam_part_screen.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

ISO = "MISO"
VINTAGE = 2023
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results" / "calibration" / "miso124_dualfuel_B"
UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"
EGRID_DIR = RAW_DIR / "fleet-egrid"
OUT = REPO / "results" / "calibration" / "_miso126_cc_steam_part_screen.json"

#: Keeper gas ($/MMBtu), ``miso124_dualfuel_B/meta.json``. Used to price the
#: block's marginal cost for KE3. Not a model input here.
KEEPER_GAS = {2023: 2.54, 2024: 2.19, 2025: 3.52}

#: Pre-registered P3 band (prereg §2.1): the steam part's implied GENERATION
#: share of its block against its EIA-860 NAMEPLATE share of the same block.
#: Not an invented threshold — the comparator is the manufacturer's own design
#: split, published per generator; the band is the tolerance on that identity.
P3_BAND = 0.10

#: Pre-registered KE3 band (prereg §3): dispatch in fewer than this share of
#: hours in EVERY year bounds the added annual energy below 0.05 % of load.
KE3_DISPATCH_BAND = 0.05

#: ISO each census plant belongs to. Rule 25 [R-ISO-SCOPE]: only MISO's rows
#: are adjudicated here; CAISO's and NEISO's are reported and handed off.
_ISO_OF = {55088: "MISO", 1004: "MISO", 50973: "MISO", 6081: "NEISO", 54912: "CAISO"}


def keeper_fleet_kwargs() -> dict:
    """Return the KEEPER's own fleet-loader settings from its run_config.json.

    The miso-116 measurement trap: ``load_fleet_from_csv`` defaults
    ``measured_chp_heat_rates=False`` while the MISO keeper ARMS it, so a probe
    that scores a fleet against the keeper must build its model side from the
    keeper's recorded config, never from the loader defaults.
    """
    cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    return {
        "measured_ct_heat_rates": bool(cfg.get("measured_ct_heat_rates", False)),
        "measured_chp_heat_rates": bool(cfg.get("measured_chp_heat_rates", False)),
    }


def eia860_operable() -> pd.DataFrame:
    """Return the raw EIA-860 operable generator sheet, normalized."""
    d = pd.read_parquet(RAW_DIR / "eia-860" / "eia860_generator_operable.parquet")
    d.columns = [c.strip() for c in d.columns]
    d["pm"] = d["Prime Mover"].astype(str).str.strip().str.upper()
    d["es"] = d["Energy Source 1"].astype(str).str.strip().str.upper()
    d["uc"] = d["Unit Code"].astype(str).str.strip()
    # GUARD (a), prereg KE1: Summer Capacity is NaN on some operable rows
    # (Edwardsport's CT1/CT2). Coerce and carry nameplate alongside so a plant
    # total is never silently short by a NaN row.
    d["mw"] = pd.to_numeric(d["Summer Capacity (MW)"], errors="coerce")
    d["np_mw"] = pd.to_numeric(d["Nameplate Capacity (MW)"], errors="coerce")
    # BASIS-CONSISTENT capacity for the presence test. `_rows_to_generators`
    # builds a generator's pmax as `net_summer_capacity_mw` ELSE
    # `nameplate_capacity_mw`, so an EIA-860 plant total summed on summer alone
    # is on a DIFFERENT basis than the fleet total it is compared against
    # wherever a row's summer capacity is NaN. miso-125's census summed summer
    # only, which is why 1004 Edwardsport (CT1/CT2 both NaN-summer) and 6081
    # Stony Brook came back UNDETERMINED: their EIA side read 0.0 MW of non-CA
    # capacity against a fleet carrying the nameplate fallback. Coalescing here
    # puts both sides on the fleet's own rule and is strictly more accurate
    # (rule 14 [R-ACCURATE]); the summer-only status is still reported
    # alongside so the published miso-125 record is reproduced, never
    # overwritten.
    d["mw_eff"] = d["mw"].fillna(d["np_mw"])
    return d


def census(d: pd.DataFrame) -> list[dict]:
    """Rebuild miso-125's R4 census: CA steam parts of NG combined-cycle blocks.

    The predicate is prereg §2 verbatim: prime mover ``CA``, own
    ``Energy Source 1`` not ``NG``, non-empty ``Unit Code``, and at least one
    sibling at the same plant with the same ``Unit Code``, prime mover ``CT``
    and ``Energy Source 1`` ``NG``.
    """
    cand = d[(d.pm == "CA") & (d.es != "NG") & (d.uc != "") & (d.uc.str.lower() != "nan")]
    assert len(cand), "candidate frame is EMPTY — the CA/non-NG filter matched nothing"
    rows = []
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
        rows.append(
            {
                "plant_code": pc,
                "plant_name": str(r["Plant Name"]),
                "state": str(r["State"]),
                "generator_id": str(r["Generator ID"]),
                "unit_code": r["uc"],
                "summer_mw": None if pd.isna(r["mw"]) else float(r["mw"]),
                "nameplate_mw": None if pd.isna(r["np_mw"]) else float(r["np_mw"]),
                "energy_source_1": r["es"],
                "ng_ct_siblings": int(len(sib)),
                "sibling_summer_mw": round(float(sib["mw"].sum()), 1),
            }
        )
    return rows


def unit_table(codes: set[int], year: int) -> pd.DataFrame:
    """Annual per-unit CEMS totals for ``codes`` — miso-125's reader verbatim.

    ``facilityId`` is STRING-typed in the CAMPD extracts, so it is coerced
    numerically BEFORE the membership filter (the miso-121 silent-empty-match
    trap), and ``grossLoad`` is null — not zero — for a unit with no gross-load
    channel.
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
    by_unit["dark"] = (by_unit["grossLoad"] <= 0.0) & (by_unit["heatInput"] > 0.0)
    return by_unit


def main() -> int:  # noqa: C901 — one linear gate sequence, kept together
    rec: dict = {
        "session": "miso-126",
        "iso": ISO,
        "vintage": VINTAGE,
        "keeper": "2026-08-04-miso-124-dualfuel-rearm",
        "prereg": "results/calibration/PREREG-miso126-cc-steam-part-capacity-2026-08-04.md",
    }
    d = eia860_operable()
    fleet_kwargs = keeper_fleet_kwargs()
    print(f"keeper fleet-loader settings (miso-116 trap guard): {fleet_kwargs}")

    # ------------------------------------------------------------------
    # KE1 — population verification + P1 ABSENCE
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("KE1 — population verification (miso-125 R4 census, rebuilt)")
    print("=" * 78)
    rows = census(d)

    fleets: dict[str, dict[int, float]] = {}
    fleet_gens: dict[str, dict[int, list]] = {}
    for iso in sorted({_ISO_OF.get(r["plant_code"], "?") for r in rows} - {"?"}):
        f = load_fleet_from_csv(iso, get_iso_config(iso), **fleet_kwargs)
        agg: dict[int, float] = {}
        gens: dict[int, list] = {}
        for g in f:
            pc = int(g.plant_code or 0)
            agg[pc] = agg.get(pc, 0.0) + float(g.pmax_mw)
            gens.setdefault(pc, []).append(g)
        fleets[iso] = agg
        fleet_gens[iso] = gens

    print(
        "\n  presence is decided against the plant's EIA-860 TOTALS, not against\n"
        "  the block's siblings (miso-125 §6: a sibling-relative test mis-reads a\n"
        "  plant's out-of-block generators as the missing steam part).\n"
    )
    for c in rows:
        pc = c["plant_code"]
        iso = _ISO_OF.get(pc, "?")
        at_plant = d[d["Plant Code"] == pc]
        eia_all = float(at_plant["mw"].sum())
        eia_no_ca = float(at_plant[at_plant.pm != "CA"]["mw"].sum())
        # GUARD (a): if any row's summer capacity is NaN the summer totals are
        # short. Report the nameplate totals alongside so the shortfall is
        # visible rather than silent.
        n_nan = int(at_plant["mw"].isna().sum())
        np_all = float(at_plant["np_mw"].sum())
        eff_all = float(at_plant["mw_eff"].sum())
        eff_no_ca = float(at_plant[at_plant.pm != "CA"]["mw_eff"].sum())
        fleet_total = fleets.get(iso, {}).get(pc)

        def _status(total_all: float, total_no_ca: float) -> str:
            if fleet_total is None:
                return "UNDETERMINED"
            if abs(fleet_total - total_no_ca) <= 1.0 and total_all - total_no_ca > 1.0:
                return "MISSING"
            if abs(fleet_total - total_all) <= 1.0:
                return "REPRESENTED"
            return "UNDETERMINED"

        # miso-125's published status (summer-only basis), reproduced verbatim…
        status_summer = _status(eia_all, eia_no_ca)
        # …and the basis-consistent status this session adjudicates on.
        status = _status(eff_all, eff_no_ca)
        c.update(
            iso=iso,
            fleet_total_mw=None if fleet_total is None else round(fleet_total, 1),
            eia860_plant_total_mw=round(eia_all, 1),
            eia860_plant_total_excl_ca_mw=round(eia_no_ca, 1),
            eia860_plant_nameplate_total_mw=round(np_all, 1),
            eia860_plant_total_eff_mw=round(eff_all, 1),
            eia860_plant_total_excl_ca_eff_mw=round(eff_no_ca, 1),
            eia860_rows_with_nan_summer=n_nan,
            status_miso125_summer_basis=status_summer,
            status=status,
        )
        drift = "" if status == status_summer else f"  (miso-125: {status_summer})"
        print(
            f"  {pc:<7}{c['plant_name'][:30]:<31}{iso:<6}{c['generator_id']:<6}"
            f"{(c['summer_mw'] or 0.0):>7.1f} MW {c['energy_source_1']:<4}| "
            f"EIA(eff) {eff_all:>7.1f} (excl CA {eff_no_ca:>7.1f}, NaN-summer "
            f"rows {n_nan}) | fleet "
            f"{'n/a' if fleet_total is None else f'{fleet_total:7.1f}'} -> "
            f"{status}{drift}"
        )

    miso_missing = sorted(
        {r["plant_code"] for r in rows if r["iso"] == "MISO" and r["status"] == "MISSING"}
    )
    miso_missing_mw = sum(
        (r["summer_mw"] or 0.0)
        for r in rows
        if r["iso"] == "MISO" and r["status"] == "MISSING"
    )
    print(f"\n  MISO capacity measurably missing: {miso_missing_mw:,.1f} MW "
          f"over plants {miso_missing}")
    # The KE1 gate is against the COMMITTED miso-125 record
    # (`_miso125_prime_mover_split.json` KE_R.R4), not against the finding's
    # prose: MISO 290.4 MW over exactly [50973, 55088], and no MISO plant
    # outside that pair called MISSING. 1004 Edwardsport must NOT be MISSING —
    # the basis-consistent test above resolves it REPRESENTED where the
    # summer-only test could not decide it, and the fleet confirms it directly
    # (generator `1004_ST`, plant_group COAL, 555.0 MW), which is the claim
    # miso-125's §6 prose actually makes.
    edw = [r for r in rows if r["plant_code"] == 1004]
    edw_ok = all(r["status"] == "REPRESENTED" for r in edw)
    edw_fleet_coal = [
        g
        for g in fleet_gens["MISO"].get(1004, [])
        if g.plant_group == "COAL" and abs(float(g.pmax_mw) - 555.0) < 0.05
    ]
    print(
        f"\n  1004 Edwardsport direct fleet check: "
        f"{len(edw_fleet_coal)} COAL generator(s) at 555.0 MW "
        f"-> {'REPRESENTED' if edw_fleet_coal else 'ABSENT'}"
    )
    ke1_pass = (
        abs(miso_missing_mw - 290.4) < 0.05
        and miso_missing == [50973, 55088]
        and edw_ok
        and bool(edw_fleet_coal)
    )
    print(f"  KE1 vs the miso-125 COMMITTED census (290.4 MW / [50973, 55088] / "
          f"1004 not a defect): {'PASS' if ke1_pass else 'FAIL'}")
    rec["KE1"] = {
        "census": rows,
        "miso_missing_plants": miso_missing,
        "miso_missing_mw": round(miso_missing_mw, 1),
        "verdict": "PASS" if ke1_pass else "FAIL_CENSUS_DISAGREES_WITH_MISO125",
    }
    rec["P1_absence"] = {
        "test": "fleet total == EIA-860 plant total EXCLUDING CA rows (+-1 MW)",
        "per_plant": {
            str(r["plant_code"]): {
                "status": r["status"],
                "fleet_total_mw": r["fleet_total_mw"],
                "eia860_excl_ca_mw": r["eia860_plant_total_excl_ca_mw"],
                "eia860_incl_ca_mw": r["eia860_plant_total_mw"],
            }
            for r in rows
        },
        "verdict": "PASS" if ke1_pass else "FAIL",
    }
    if not ke1_pass:
        print("\n  STOP — the census disagrees with the published miso-125 record.")
        OUT.write_text(json.dumps(rec, indent=1))
        return 1

    # ------------------------------------------------------------------
    # P2 — ONE METER, ONE RATE
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("P2 — one meter, one rate (prereg §2.1 property 2)")
    print("=" * 78)
    proc = pd.read_parquet(RAW_DIR / "eia-860" / "eia860_generators.parquet")
    egrid = pd.read_excel(
        EGRID_DIR / "egrid2023_data_rev2.xlsx", sheet_name="PLNT23", header=1
    )
    egrid.columns = [str(c).strip() for c in egrid.columns]
    egrid["ORISPL"] = pd.to_numeric(egrid["ORISPL"], errors="coerce")

    p2: dict = {"per_plant": {}}
    for pc in miso_missing:
        at = d[d["Plant Code"] == pc]
        ca_rows = at[at.pm == "CA"]
        block_ucs = set(ca_rows["uc"])
        pr = proc[proc["plant_id"] == pc]
        # (a) the CA rows carry the same joined heat rate as their CT siblings
        ca_ids = set(ca_rows["Generator ID"].astype(str))
        hr_ca = sorted(
            {round(float(x), 6) for x in pr[pr["generator_id"].isin(ca_ids)]["heat_rate"]}
        )
        hr_rest = sorted(
            {
                round(float(x), 6)
                for x in pr[~pr["generator_id"].isin(ca_ids)]["heat_rate"]
            }
        )
        a_pass = hr_ca == hr_rest and len(hr_ca) == 1
        # (b) the implied capacity factor on the present vs repaired fleet
        row = egrid[egrid["ORISPL"] == pc]
        plngenan = float(pd.to_numeric(row["PLNGENAN"], errors="coerce").iloc[0])
        present_mw = float(fleets["MISO"][pc])
        added_mw = float(ca_rows["mw"].sum())
        repaired_mw = present_mw + added_mw
        cf_present = plngenan / (present_mw * 8760.0)
        cf_repaired = plngenan / (repaired_mw * 8760.0)
        b_pass = cf_present > 1.0 and cf_repaired <= 1.0
        print(
            f"\n  {pc} {at['Plant Name'].iloc[0][:40]}  (block Unit Codes "
            f"{sorted(block_ucs)})"
        )
        print(f"    (a) joined heat_rate  CA {hr_ca}  vs non-CA {hr_rest}"
              f"  -> {'PASS' if a_pass else 'FAIL'}")
        print(
            f"    (b) eGRID PLNGENAN {plngenan:,.0f} net MWh\n"
            f"        present fleet {present_mw:>7.1f} MW -> implied CF "
            f"{cf_present:7.1%}  (must be > 100 %)\n"
            f"        repaired      {repaired_mw:>7.1f} MW -> implied CF "
            f"{cf_repaired:7.1%}  (must be <= 100 %)  -> "
            f"{'PASS' if b_pass else 'FAIL'}"
        )
        p2["per_plant"][str(pc)] = {
            "heat_rate_ca": hr_ca,
            "heat_rate_non_ca": hr_rest,
            "a_pass": a_pass,
            "plngenan_net_mwh": round(plngenan, 1),
            "present_fleet_mw": round(present_mw, 1),
            "added_mw": round(added_mw, 1),
            "repaired_fleet_mw": round(repaired_mw, 1),
            "implied_cf_present": round(cf_present, 6),
            "implied_cf_repaired": round(cf_repaired, 6),
            "b_pass": b_pass,
            "verdict": "PASS" if (a_pass and b_pass) else "FAIL",
        }
    p2_admitted = [
        int(k) for k, v in p2["per_plant"].items() if v["verdict"] == "PASS"
    ]
    p2["admitted_plants"] = sorted(p2_admitted)
    p2["excluded_plants"] = sorted(set(miso_missing) - set(p2_admitted))
    rec["P2_one_meter_one_rate"] = p2
    print(f"\n  P2 admits {sorted(p2_admitted)}; excludes {p2['excluded_plants']}")

    # ------------------------------------------------------------------
    # P3 — DESIGN-SHARE COHERENCE (the miso-125 §4 let-down doubt, falsifiable)
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("P3 — design-share coherence (prereg §2.1 property 3)")
    print("=" * 78)
    print(
        "  implied generation share of the block vs its EIA-860 NAMEPLATE share.\n"
        "  A steam part producing materially MORE than its design share has an\n"
        "  independent steam source -> the miso-125 §4 let-down hypothesis is\n"
        "  live and the block-rate assumption fails. The implied share is on a\n"
        "  gross/net mixed basis and is therefore a LOWER bound, which makes the\n"
        f"  falsifier conservative. Band |implied - nameplate| <= {P3_BAND}.\n"
    )
    ut = unit_table(set(p2_admitted), VINTAGE)
    assert not ut.empty, "CEMS unit query returned EMPTY for the admitted plants"
    p3: dict = {"band": P3_BAND, "per_plant": {}}
    for pc in p2_admitted:
        at = d[d["Plant Code"] == pc]
        ca_rows = at[at.pm == "CA"]
        block_ucs = set(ca_rows["uc"])
        block = at[at["uc"].isin(block_ucs)]
        block_ca_np = float(block[block.pm == "CA"]["np_mw"].sum())
        block_all_np = float(block["np_mw"].sum())
        nameplate_share = block_ca_np / block_all_np
        # CEMS gross over the plant's POWER-TRAIN units (dark boilers excluded
        # exactly as scope gate 3 does, so boiler fuel/output never enters).
        u = ut[ut["facilityId"] == pc]
        power_gross = float(u[~u["dark"]]["grossLoad"].sum())
        plngenan = p2["per_plant"][str(pc)]["plngenan_net_mwh"]
        implied_steam_mwh = plngenan - power_gross
        # the block's own CT gross: the plant's power-train gross minus any
        # power-train unit that is NOT in the block. Resolved by capacity share
        # when CEMS unit ids do not carry the EIA unit code (they do not), so
        # this is reported as the plant-level identity it is.
        out_of_block_np = float(at[~at["uc"].isin(block_ucs)]["np_mw"].sum())
        block_ct_np = float(block[block.pm != "CA"]["np_mw"].sum())
        # attribute the plant's power-train gross to the block's CT rows in
        # proportion to nameplate — the only split the data supports, and it is
        # stated as such rather than presented as metered.
        block_ct_gross = power_gross * (
            block_ct_np / (block_ct_np + out_of_block_np)
            if (block_ct_np + out_of_block_np) > 0
            else 1.0
        )
        implied_share = (
            implied_steam_mwh / (implied_steam_mwh + block_ct_gross)
            if (implied_steam_mwh + block_ct_gross) > 0
            else np.nan
        )
        gap = abs(implied_share - nameplate_share)
        ok = bool(gap <= P3_BAND)
        print(
            f"  {pc}: nameplate share {nameplate_share:.4f} "
            f"({block_ca_np:,.1f} of {block_all_np:,.1f} MW nameplate in block "
            f"{sorted(block_ucs)})"
        )
        print(
            f"        CEMS power-train gross {power_gross:,.0f} MWh; "
            f"implied steam {implied_steam_mwh:,.0f} MWh; "
            f"block CT gross {block_ct_gross:,.0f} MWh"
        )
        print(
            f"        implied gen share {implied_share:.4f}  |gap| {gap:.4f}  -> "
            f"{'PASS' if ok else 'FAIL — let-down hypothesis LIVE'}"
        )
        p3["per_plant"][str(pc)] = {
            "nameplate_share": round(nameplate_share, 6),
            "block_ca_nameplate_mw": round(block_ca_np, 1),
            "block_total_nameplate_mw": round(block_all_np, 1),
            "cems_power_train_gross_mwh": round(power_gross, 1),
            "implied_steam_mwh": round(implied_steam_mwh, 1),
            "block_ct_gross_mwh": round(block_ct_gross, 1),
            "implied_gen_share": round(float(implied_share), 6),
            "gap": round(float(gap), 6),
            "verdict": "PASS" if ok else "FAIL",
        }
    p3_admitted = sorted(
        int(k) for k, v in p3["per_plant"].items() if v["verdict"] == "PASS"
    )
    p3["admitted_plants"] = p3_admitted
    rec["P3_design_share"] = p3
    print(f"\n  P3 admits {p3_admitted}")

    admitted = p3_admitted
    added_total = sum(
        (r["summer_mw"] or 0.0)
        for r in rows
        if r["plant_code"] in admitted and r["status"] == "MISSING"
    )
    rec["admitted_plants"] = admitted
    rec["admitted_capacity_mw"] = round(added_total, 1)
    print(f"\n  ADMITTED after P1-P3: {admitted} = {added_total:,.1f} MW")
    if not admitted:
        rec["verdict"] = "REFUTED_BY_PROPERTIES"
        OUT.write_text(json.dumps(rec, indent=1))
        return 0

    # ------------------------------------------------------------------
    # KE3 — INERT-BY-DISPATCH
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("KE3 — INERT-BY-DISPATCH (committed sidecars, no replay)")
    print("=" * 78)
    # the block's marginal cost = its measured CHP heat rate x keeper gas + VOM
    art = pd.read_csv(PROCESSED_DIR / f"chp_power_only_heat_rates_{ISO}.csv")
    zone_of: dict[int, str] = {}
    for pc in admitted:
        gs = fleet_gens["MISO"].get(pc, [])
        zs = sorted({g.zone for g in gs if g.plant_group == "CC_CHP"}) or sorted(
            {g.zone for g in gs}
        )
        zone_of[pc] = zs[0] if zs else "?"
    print(f"  zone of each admitted plant: {zone_of}")

    ke3: dict = {"band": KE3_DISPATCH_BAND, "per_plant": {}}
    for pc in admitted:
        a = art[(art["plant_code"] == pc) & (art["plant_group"] == "CC_CHP")]
        hr = float(a["heat_rate"].iloc[0]) if len(a) and a["flag"].iloc[0] == "ok" else (
            float(
                pd.unique(
                    proc[proc["plant_id"] == pc]["heat_rate"].round(6)
                )[0]
            )
        )
        vom = 0.0
        for g in fleet_gens["MISO"].get(pc, []):
            if g.plant_group == "CC_CHP":
                vom = float(g.vom)
                break
        per_year = {}
        for year in YEARS:
            sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
            sysd = sysd[(sysd["pass"] == "P1") & (sysd["zone"] == zone_of[pc])]
            mc = hr * KEEPER_GAS[year] + vom
            price = sysd["price"].to_numpy(dtype=float)
            disp = float((price > mc).mean())
            per_year[str(year)] = {
                "heat_rate": round(hr, 4),
                "vom": round(vom, 4),
                "gas": KEEPER_GAS[year],
                "marginal_cost": round(mc, 4),
                "zone": zone_of[pc],
                "hours": int(price.size),
                "dispatch_hour_share": round(disp, 6),
                "median_price": round(float(np.median(price)), 4),
            }
            print(
                f"  {pc} {year}: MC {mc:6.2f} $/MWh (hr {hr:.4f} x gas "
                f"{KEEPER_GAS[year]:.2f} + vom {vom:.2f})  zone {zone_of[pc]}  "
                f"median LMP {np.median(price):6.2f}  "
                f"-> would dispatch in {disp:.1%} of hours"
            )
        ke3["per_plant"][str(pc)] = per_year
    all_shares = [
        v["dispatch_hour_share"]
        for p in ke3["per_plant"].values()
        for v in p.values()
    ]
    ke3_inert = all(s < KE3_DISPATCH_BAND for s in all_shares)
    ke3["verdict"] = "INERT" if ke3_inert else "LIVE"
    print(
        f"\n  KE3 verdict: {ke3['verdict']} — max dispatch-hour share "
        f"{max(all_shares):.1%} vs the {KE3_DISPATCH_BAND:.0%} band"
    )
    rec["KE3_inert_by_dispatch"] = ke3

    # bounded added energy, as an UPPER bound (miso-119 guard: an upper bound is
    # an upper bound, never a prediction of the realized effect)
    load = {}
    for year in YEARS:
        sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        load[year] = float(sysd[sysd["pass"] == "P1"]["demand"].sum())
    bound = {}
    for year in YEARS:
        mwh = sum(
            (
                sum(
                    (r["summer_mw"] or 0.0)
                    for r in rows
                    if r["plant_code"] == pc and r["status"] == "MISSING"
                )
                * ke3["per_plant"][str(pc)][str(year)]["dispatch_hour_share"]
                * 8760.0
            )
            for pc in admitted
        )
        bound[str(year)] = {
            "upper_bound_added_twh": round(mwh / 1e6, 5),
            "iso_load_twh": round(load[year] / 1e6, 3),
            "upper_bound_share_of_load": round(mwh / load[year], 6),
        }
        print(
            f"  {year}: UPPER-BOUND added energy {mwh/1e6:.4f} TWh vs ISO load "
            f"{load[year]/1e6:.1f} TWh = {mwh/load[year]:.3%}"
        )
    rec["KE3_energy_upper_bound"] = bound

    # ------------------------------------------------------------------
    # KE4 — INERT-BY-BINDING, reported honestly
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("KE4 — INERT-BY-BINDING (NOT answerable from committed artifacts)")
    print("=" * 78)
    print(
        "  The committed sidecar schema is (year, pass, klass, hour, mw) at CLASS\n"
        "  grain and carries NO bound / marginality flag, so 55088's own binding\n"
        "  is NOT measurable here. The class-level statistics below are reported\n"
        "  for the record and are NOT offered as a proxy for plant-grain binding.\n"
        "  No `I` is declared on this route (prereg §3 KE4).\n"
    )
    ke4: dict = {"answerable": False, "class_statistics": {}}
    cc_cap = sum(
        float(g.pmax_mw)
        for gs in fleet_gens["MISO"].values()
        for g in gs
        if g.plant_group == "CC_CHP"
    )
    for year in YEARS:
        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        cc = ch[(ch["pass"] == "P1") & (ch["klass"] == "CC_CHP")]["mw"].to_numpy(float)
        ke4["class_statistics"][str(year)] = {
            "cc_chp_fleet_capacity_mw": round(cc_cap, 1),
            "cc_chp_max_mw": round(float(cc.max()), 1),
            "cc_chp_mean_mw": round(float(cc.mean()), 1),
            "cc_chp_p99_mw": round(float(np.percentile(cc, 99)), 1),
            "cc_chp_distinct_values": int(np.unique(np.round(cc, 6)).size),
            "cc_chp_energy_twh": round(float(cc.sum()) / 1e6, 4),
        }
        print(
            f"  {year} CC_CHP class: max {cc.max():,.1f} / mean {cc.mean():,.1f} MW "
            f"against fleet class capacity {cc_cap:,.1f} MW; "
            f"{np.unique(np.round(cc,6)).size:,} distinct values in {cc.size:,} h; "
            f"{cc.sum()/1e6:.3f} TWh"
        )
    rec["KE4_inert_by_binding"] = ke4

    rec["verdict"] = "LIVE_A_B_WARRANTED" if not ke3_inert else "INERT_NO_SOLVE"
    print(f"\nSCREEN VERDICT: {rec['verdict']}")
    OUT.write_text(json.dumps(rec, indent=1))
    print(f"written: {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
