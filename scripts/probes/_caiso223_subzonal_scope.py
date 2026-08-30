"""caiso-223 — SUB-ZONAL TOPOLOGY PROGRAM, OPENING ROUND: the scoping probe.

Chartered by the owner's 2026-08-30 PM ruling arming caiso-222 Q2 route (iii)
as a REPRESENTATION-GRAIN PROGRAM OPENING ROUND — scope + membership + LDF
derivation, ZERO-SOLVE. Method and acceptance gates pre-registered in
``results/calibration/PRECOMMIT-caiso223-subzonal-scope-2026-08-30.md``; the
adjudication record is ``FINDING-caiso223-subzonal-scope-2026-08-30.md``.

NO LP, NO SOLVE, NOTHING ARMED. Reads committed bytes only (plus one
pre-registered OPTIONAL Attachment-B2 fetch attempt handled outside this
script): the caiso-219 deliverability census JSON, the caiso-172 Atlas
snapshots (``data/raw/caiso-atlas/``), the caiso-217 plant-hub crosswalk, the
committed caiso-172 split JSON (control), and eGRID 2023 (county fallback
tier). It reads NO model output and NO residual [R-STRUCT, R-FROZEN-DERIVE];
the derived load split satisfies the rule-13 admissibility test exactly as the
caiso-172 keeper input does (regenerates for any year from published LDFs;
responds to changed conditions) [R-MEASURED].

Sections
--------
A. Partition adjudication inputs + the machine-readable partition spec
   (committed-byte evidence: census off-peak control, atlas hub anchors, the
   SLAP_PGZP straddle sample) and the P-A/P-A'/P-B/P-C adjudication against
   the precommit's K1–K4 criteria.
B. Membership re-cut: the 446-plant crosswalk re-cut to the partition
   (tier ladder of precommit §3), the atlas gen-pnode → sub-zone map, the
   pre-registered witness set, and the honest enumeration of unassignable /
   default mass (eGRID 2023 CISO base for the unjoined remainder).
C. The sub-zonal LDF load split: the caiso-172 construction generalized to
   the partition buckets over the SAME committed Atlas bytes (helpers
   imported from the frozen derive so the construction is provably shared),
   plus the exact 2-way replication control against the committed split JSON
   and the pre-registered data gates G1–G5.

Outputs (deterministic: sorted keys, rounded floats, no timestamps)
-------------------------------------------------------------------
* ``results/calibration/_caiso223_subzonal_scope.json`` — every number.
* ``results/calibration/_caiso223_membership_recut.csv`` — the plant re-cut.
* ``results/calibration/_caiso223_pnode_subzone_map.csv`` — pnode → sub-zone
  (atlas gen universe + DLAP_PGAE load universe).

Run: ``PYTHONPATH=.:src python3 scripts/probes/_caiso223_subzonal_scope.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

import derive_caiso_path15_load_split as c172  # noqa: E402  (frozen derive — helpers reused so the construction is provably the caiso-172 one)

from market_sim.config.paths import RAW_DIR  # noqa: E402

OUT_JSON = REPO / "results" / "calibration" / "_caiso223_subzonal_scope.json"
OUT_RECUT = REPO / "results" / "calibration" / "_caiso223_membership_recut.csv"
OUT_PNODE = REPO / "results" / "calibration" / "_caiso223_pnode_subzone_map.csv"
CENSUS_JSON = REPO / "results" / "calibration" / "_caiso219_deliverability_census.json"
SPLIT_JSON = RAW_DIR / "zone-specific-demand" / "CAISO" / "CAISO_path15_load_split.json"
CROSSWALK_CSV = RAW_DIR / "reference" / "caiso-plant-hub-membership.csv"
EGRID_XLSX = RAW_DIR / "fleet-egrid" / "egrid2023_data_rev2.xlsx"

YEARS = (2023, 2024, 2025)

#: Partition sub-LAP rule (precommit §3): the load-side DEFINITION of the
#: partition. SLAP_PGF1 is the PG&E Fresno-division sub-LAP; SLAP_PGZP /
#: SLAP_PGKN are the two 100 %-ZP26 sub-LAPs (committed caiso-172 finding).
SLAP_SIDE = {"SLAP_PGF1-APND": "FSNO", "SLAP_PGZP-APND": "ZP26", "SLAP_PGKN-APND": "ZP26"}

#: County fallback tier (precommit §3 tier 3): the PGF1-division footprint as
#: evidenced in the committed LDF bytes (Merced / Atwater / Huron pnodes in
#: SLAP_PGF1) plus the census's own Fresno-area northern reach (Chowchilla /
#: Le Grand / Merced rows). Tulare deliberately EXCLUDED (SCE foothill is
#: TH_SP15 by crosswalk; PG&E Tulare fringe is SLAP_PGZP → ZP26-side).
FSNO_COUNTIES = {"Fresno", "Kings", "Madera", "Merced"}

#: The Gates-complex substation claim (precommit §3 tier 1): the boundary
#: node itself — census "PG&E Fresno" area (Gates 500/230 kV TB #11/#12 rows).
GATES_SUBS = {"GATES", "GATES1"}

#: DMM element evidence (FINDING-caiso218 §B, committed — DMM 2023 annual
#: report ch. 6 average binding limits, with 2023/2024/Q3-2025 binding
#: windows; EVIDENCE ONLY, nothing armed — the caiso-222 §(iii) "one thin
#: path" whose rule-13/14 adjudication is deliberately NOT performed here).
DMM_ELEMENTS = {
    "tesla_losbanos_1_500": {
        "constraint_id": "30040_TESLA_500_30050_LOSBANOS_500_BR_1_1",
        "name": "Tesla-Los Banos #1 500 kV",
        "direction_binding": "S->N",
        "dmm_2023_avg_binding_limit_mw": 1600.0,
        "binding_record": "2024: bound 6.5% of hours, HE10-16, winter-heavy",
    },
    "mossld_lasaguilas_230": {
        "constraint_id": "30750_MOSSLD_230_30797_LASAGUIL_230_BR_1_1",
        "name": "Moss Landing-Las Aguilas 230 kV",
        "direction_binding": "S->N",
        "dmm_2023_avg_binding_limit_mw": 340.0,
        "binding_record": "2023: >70% of congestion 9a-3p Apr-Oct; 2024: bound 24% of ALL hours; Q3-2025: 27%, HE9-16",
    },
    "gates_midway_1_500": {
        "constraint_id": "30055_GATES1_500_30060_MIDWAY_500_BR_1_1",
        "name": "Gates-Midway #1 500 kV",
        "direction_binding": "S->N",
        "dmm_2023_avg_binding_limit_mw": 2500.0,
        "binding_record": "2023: >80% of congestion 8a-3p, 90% Sep-Dec; 2024: bound 9% of ALL hours, HE9-15",
    },
    "panoche_gates_2_230": {
        "constraint_id": "30790_PANOCHE_230_30900_GATES_230_BR_2_1",
        "name": "Panoche-Gates #2 230 kV",
        "direction_binding": "S->N",
        "dmm_2023_avg_binding_limit_mw": 200.0,
        "binding_record": "2023 Q1, 9a-4p",
    },
    "midway_vincent_2_500": {
        "constraint_id": "30060_MIDWAY_500_24156_VINCENT_500_BR_2_3",
        "name": "Midway-Vincent #2 500 kV",
        "direction_binding": "N->S",
        "dmm_2023_avg_binding_limit_mw": 2100.0,
        "binding_record": "2023: 50% of congestion 5-8pm, >90% Jun-Aug; prominent again Q3-2025",
    },
    "path26_cp1_nomogram": {
        "constraint_id": "6410_CP1_NG",
        "name": "Path 26 Control Point 1 nomogram (protects Midway-Whirlwind for Midway-Vincent #1+#2 contingency)",
        "direction_binding": "N->S",
        "dmm_2023_avg_binding_limit_mw": 1600.0,
        "binding_record": "after 6pm, Jul-Sep 2023; CP6/CP10 appear in 2024/2025 censuses",
    },
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _round(obj, nd=6):
    """Recursively round floats for deterministic JSON output."""
    if isinstance(obj, float):
        return round(obj, nd)
    if isinstance(obj, dict):
        return {k: _round(v, nd) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, nd) for v in obj]
    return obj


def _latest(df: pd.DataFrame) -> pd.DataFrame:
    """Latest effective window per (APNODE_ID, PNODE_ID) — caiso-217 rule."""
    return (
        df.sort_values("EFF_START_DT")
        .drop_duplicates(subset=["APNODE_ID", "PNODE_ID"], keep="last")
        .reset_index(drop=True)
    )


def _sub(series: pd.Series) -> pd.Series:
    """Substation token of a pnode id (``SUBSTATION_voltage_id``)."""
    return series.astype(str).str.split("_").str[0]


# ---------------------------------------------------------------------------
# section A — partition adjudication inputs + the machine-readable spec
# ---------------------------------------------------------------------------


def section_a(hub_all: pd.DataFrame, ldf_all: pd.DataFrame) -> dict:
    """Assemble the committed-byte evidence and the partition spec."""
    # A.1 census off-peak control (must reproduce caiso-219 §D)
    census = json.loads(CENSUS_JSON.read_text())["census"]
    by_area: dict[str, dict[str, int]] = {}
    for row in census:
        a = by_area.setdefault(row["area"], {"constraints": 0, "off_peak": 0})
        a["constraints"] += 1
        a["off_peak"] += int(bool(row["binds_off_peak"]))
    fresno = by_area["PG&E Fresno Interconnection Area Constraints"]
    kern = by_area["PG&E Kern Interconnection Area Constraints"]
    sce_n = by_area["SCE Northern Interconnection Area Constraints"]
    tehachapi_rows = [
        r for r in census
        if r["constraint"] in ("Antelope-Vincent Constraint", "Vincent-Lugo Constraint", "Windhub Constraint")
    ]
    census_control = {
        "fresno_off_peak": [fresno["off_peak"], fresno["constraints"]],
        "kern_off_peak": [kern["off_peak"], kern["constraints"]],
        "sce_northern_off_peak": [sce_n["off_peak"], sce_n["constraints"]],
        "tehachapi_off_peak_rows": sum(r["binds_off_peak"] for r in tehachapi_rows),
        "tehachapi_rows": len(tehachapi_rows),
        "reproduces_caiso219": (
            fresno["off_peak"] == 14 and fresno["constraints"] == 19
            and kern["off_peak"] == 7 and kern["constraints"] == 10
            and sum(r["binds_off_peak"] for r in tehachapi_rows) == 0
        ),
    }

    # A.2 atlas hub anchors for the boundary substations (latest windows)
    hub_latest = _latest(hub_all)
    hub_latest = hub_latest.assign(SUB=_sub(hub_latest["PNODE_ID"]))
    anchors = {}
    for sub in ["TESLA", "MOSSLD", "LASAGUIL", "PANOCHE", "SCHLNDLR", "GATES", "MIDWAY", "DIABLO", "VINCENT", "WIRLWIND"]:
        hubs = sorted(hub_latest.loc[hub_latest["SUB"] == sub, "APNODE_ID"].unique())
        anchors[sub] = [h.replace("_GEN-APND", "").replace("TH_", "") for h in hubs]

    # A.3 the SLAP_PGZP straddle sample (K4 corroboration for the P-A kill):
    # coastal-SLO tokens alongside west-Kern-fringe tokens inside ONE sub-LAP.
    zp_nodes = sorted(ldf_all.loc[ldf_all["APNODE_ID"] == "SLAP_PGZP-APND", "PNODE_ID"].unique())
    straddle_sample = {
        "coastal_slo_examples": [n for n in zp_nodes if _sub(pd.Series([n])).iloc[0] in ("ATASCDRO", "BAYWOOD", "MORROBAY", "CAYUCOS", "SANLUS")][:6],
        "west_kern_fringe_examples": [n for n in zp_nodes if _sub(pd.Series([n])).iloc[0] in ("3EMIDIO", "BELRIDGE", "ARVIN", "ALPAUGH", "TAFT")][:6],
        "note": "name-geography is corroboration only; the operative P-A kill is K2 (no committed census/DMM element separates coast from Kern)",
    }

    # A.4 the machine-readable partition spec (P-A': the FINDING §A proposal)
    spec = {
        "proposal": "P-A-prime",
        "zones": {
            "NP15": {"status": "residual", "note": "old NP15 minus FSNO; keeps COI import"},
            "FSNO": {
                "status": "NEW",
                "carved_from": "NP15 (gen side also claims the Gates-complex substations from old ZP26; zero crosswalk plants sit there today)",
                "load_instrument": "SLAP_PGF1 share of DLAP_PGAE (section C)",
                "content": "San Joaquin Valley pocket: Los Banos / Las Aguilas / Panoche / Westlands-Kings solar belt / Fresno metro / the Gates complex",
                "purpose": "the off-peak Local-strandedness pocket the census puts at PG&E Fresno (14/19 off-peak) — lets valley surplus strand and price sub-zonally instead of flowing frictionlessly to Bay load and southern absorbers (caiso-221 §E.1)",
            },
            "ZP26": {"status": "unchanged scope", "note": "SLAP_PGZP + SLAP_PGKN load; Kern/Midway complex + SLO coastal gen (Diablo, Topaz, CVSR)"},
            "LA_BASIN": {"status": "unchanged"},
            "SDGE": {"status": "unchanged"},
            "SP15_rest": {"status": "unchanged", "note": "Tehachapi 0/3 off-peak (census): NO SP15-side cut is supported"},
            "WECC_import": {"status": "unchanged"},
        },
        "links": [
            {
                "a": "NP15", "b": "FSNO", "status": "NEW",
                "elements": [DMM_ELEMENTS["tesla_losbanos_1_500"], DMM_ELEMENTS["mossld_lasaguilas_230"]],
                "boundary_adjacent_census_rows": ["NEW-Metcalf-Mosslanding 500kV (On-Peak)"],
                "purpose": "the cut between the valley pocket and Bay/coastal load — both elements are TH_NP15-internal today, i.e. INVISIBLE at hub grain; Moss Landing-Las Aguilas is the record's highest-frequency binder (24%/27% of ALL hours 2024/Q3-2025)",
                "limit_status": "NOT ARMED — DMM 2023 scalars are evidence only; real ratings CEII (caiso-218/219)",
            },
            {
                "a": "FSNO", "b": "ZP26", "status": "NEW",
                "elements": [DMM_ELEMENTS["gates_midway_1_500"]],
                "census_boundary_rows": [
                    "Diablo-Gates 500 kV line (Off-Peak; locations Kern, Fresno)",
                    "Cal Flat-Gates 230 kV line (Off-Peak; locations Kern, Los Padres)",
                    "Gates 500/230kV TB #11 / #12 (Off-Peak; locations Fresno, Kern) — the boundary complex's own transformers",
                ],
                "purpose": "the Gates-Midway cut the charter names — the census's off-peak mass converges on this complex from both sides (Fresno 14/19 + Kern 7/10); separates Kern/coastal export mass (incl. the Tehachapi trunk arriving at Midway) from the valley pocket",
                "limit_status": "NOT ARMED",
            },
            {
                "a": "ZP26", "b": "SP15_rest", "status": "EXISTING (4,000 MW Path 26) — element identities now stated",
                "elements": [DMM_ELEMENTS["midway_vincent_2_500"], DMM_ELEMENTS["path26_cp1_nomogram"]],
                "note": "Midway-Whirlwind 500 kV (the TRTP Tehachapi collector trunk, WIRLWIND=TH_SP15 / MIDWAY=TH_ZP26 in the atlas) terminates on this boundary and is managed by the CP nomogram family",
            },
            {
                "replaced": "NP15<->ZP26 5,400 MW (Path 15, Los Banos-Gates)",
                "disposition": "REPLACED by the NP15-FSNO-ZP26 chain; Path 15 proper (Los Banos-Gates 500 kV, Panoche-Gates 230 kV #1/#2) becomes FSNO-INTERNAL spine — consistent with the DMM record, in which Los Banos-Gates itself is NOT a top binder while the two chain cuts are",
                "internal_elements": [DMM_ELEMENTS["panoche_gates_2_230"]],
            },
            {"a": "WECC_import", "b": "NP15", "status": "unchanged (COI 4,800)"},
            {"a": "WECC_import", "b": "SP15_rest", "status": "unchanged (Path 46 10,623)"},
            {"a": "SP15_rest", "b": "LA_BASIN", "status": "unchanged (LCT import cap, one-way)"},
            {"a": "SP15_rest", "b": "SDGE", "status": "unchanged (Path 44 LCT cap, one-way)"},
        ],
    }

    # A.5 adjudication against the precommit K1-K4 (committed bytes only)
    adjudication = {
        "P-B": "FAILS K3 by construction: a joint Fresno+Kern pocket makes Gates-Midway #1 500 kV pocket-INTERNAL — the named off-peak complex becomes unrepresentable",
        "P-C": "FAILS K3 (Fresno leg): leaves the larger census off-peak family (Fresno 14/19) and the highest-frequency DMM binder (Moss Landing-Las Aguilas) invisible inside NP15",
        "P-A": "FAILS K2 + K4: no committed census/DMM row names a coast<->Kern element (Diablo Canyon's second 500 kV outlet is absent from the census), and SLAP_PGZP mixes coastal-SLO with west-Kern-fringe pnodes (A.3) so the committed load instrument cannot partition coast from Kern",
        "P-A-prime": "PASSES K1 (two separate element-grounded cuts with different year-varying binding profiles express the caiso-218 §C non-monotone year vector; not a single static link), K2 (every new boundary element atlas-anchored: TESLA/MOSSLD/LASAGUIL/PANOCHE=NP15-side, GATES/MIDWAY/DIABLO=ZP26-side, VINCENT/WIRLWIND=SP15), K3 (Fresno mass inside FSNO, the Gates-Midway complex ON the FSNO<->ZP26 boundary, Kern local 115 kV family enumerated as below-zonal-grain in the sufficiency list; no SP15 cut), K4 (load = SLAP_PGF1 via the caiso-172 machinery; gen = crosswalk+atlas+county tiers, sections B/C)",
    }

    return {
        "census_control": census_control,
        "atlas_hub_anchors": anchors,
        "slap_pgzp_straddle": straddle_sample,
        "partition_spec": spec,
        "adjudication": adjudication,
    }


# ---------------------------------------------------------------------------
# section B — membership re-cut
# ---------------------------------------------------------------------------


def _sub_slap_map(ldf_all: pd.DataFrame) -> dict[str, set[str]]:
    """Substation -> set of sub-LAPs hosting load pnodes there (latest windows)."""
    slap = ldf_all[ldf_all["APNODE_ID"].str.startswith("SLAP_PG")]
    slap = _latest(slap)
    slap = slap.assign(SUB=_sub(slap["PNODE_ID"]))
    out: dict[str, set[str]] = {}
    for sub, grp in slap.groupby("SUB"):
        out[str(sub)] = set(grp["APNODE_ID"].unique())
    return out


def _side_of_slaps(slaps: set[str]) -> str | None:
    """Map a substation's sub-LAP set to a partition side, or None if mixed.

    FSNO iff exactly {PGF1}; NP15 iff non-empty and wholly non-partition
    sub-LAPs; anything touching PGZP/PGKN or mixing sides falls through
    (precommit §3 tier 2 — hub membership is measured and is never overturned
    by co-location [R-ACCURATE]).
    """
    if not slaps:
        return None
    sides = {SLAP_SIDE.get(s, "NP15") for s in slaps}
    if sides == {"FSNO"}:
        return "FSNO"
    if sides == {"NP15"}:
        return "NP15"
    return None


def section_b(hub_all: pd.DataFrame, ldf_all: pd.DataFrame) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Re-cut the crosswalk and the atlas gen-pnode universe to the partition."""
    sub2slaps = _sub_slap_map(ldf_all)
    egrid = pd.read_excel(
        EGRID_XLSX, sheet_name="PLNT23", header=1,
        usecols=["ORISPL", "PNAME", "CNTYNAME", "BACODE", "NAMEPCAP"],
    )
    county = egrid.set_index("ORISPL")["CNTYNAME"].to_dict()
    # newer-vintage fill for plants past the eGRID2023 vintage ceiling — the
    # second county instrument the precommit tier 3 names (EIA-860 plant sheet)
    e860 = pd.read_parquet(RAW_DIR / "eia-860" / "eia860_plant.parquet", columns=["Plant Code", "County"])
    county860 = e860.dropna().drop_duplicates("Plant Code").set_index("Plant Code")["County"].to_dict()

    cw = pd.read_csv(CROSSWALK_CSV)
    cw = cw.assign(SUB=_sub(cw["pnode"]))

    rows = []
    for r in cw.itertuples(index=False):
        hub, sub = r.hub, r.SUB
        cnty, cnty_src = county.get(r.plant_code), "egrid2023"
        if cnty is None:
            cnty, cnty_src = county860.get(r.plant_code), "eia860"
        if cnty is None:
            cnty_src = ""
        if hub == "TH_SP15":
            zone, method = "SP15_side", "hub:unchanged"
        elif hub == "TH_ZP26":
            if sub in GATES_SUBS:
                zone, method = "FSNO", "gates-complex-claim"
            else:
                zone, method = "ZP26", "hub:unchanged"
        else:  # TH_NP15 — tiers 2-4 discriminate FSNO vs NP15
            side = _side_of_slaps(sub2slaps.get(sub, set()))
            if side is not None:
                zone, method = side, f"slap-coloc:{'+'.join(sorted(s.replace('SLAP_', '').replace('-APND', '') for s in sub2slaps[sub]))}"
            elif cnty is not None:
                if cnty in FSNO_COUNTIES:
                    zone, method = "FSNO", f"county:{cnty}"
                else:
                    zone, method = "NP15", f"county-other:{cnty}"
            else:
                zone, method = "NP15", "default-np15"
        rows.append({
            "plant_code": r.plant_code, "plant_name": r.plant_name, "tech": r.tech,
            "capacity_mw": r.capacity_mw, "hub": hub, "pnode": r.pnode,
            "county": cnty if cnty is not None else "",
            "county_source": cnty_src,
            "subzone": zone, "method": method,
        })
    recut = pd.DataFrame(rows).sort_values(["subzone", "plant_code"]).reset_index(drop=True)

    def mw(mask) -> float:
        return float(recut.loc[mask, "capacity_mw"].sum())

    np15_pool = recut["hub"] == "TH_NP15"
    summary = {
        "plants_total": int(len(recut)),
        "mw_total": mw(slice(None)),
        "by_subzone_mw": {z: mw(recut["subzone"] == z) for z in sorted(recut["subzone"].unique())},
        "fsno": {
            "plants": int((recut["subzone"] == "FSNO").sum()),
            "mw": mw(recut["subzone"] == "FSNO"),
            "by_tech_mw": {t: float(g["capacity_mw"].sum()) for t, g in recut[recut["subzone"] == "FSNO"].groupby("tech")},
            "by_method_mw": {m: float(g["capacity_mw"].sum()) for m, g in recut[recut["subzone"] == "FSNO"].groupby("method")},
        },
        "np15_pool_honesty": {
            "th_np15_plants": int(np15_pool.sum()),
            "th_np15_mw": mw(np15_pool),
            "slap_coloc_mw": mw(np15_pool & recut["method"].str.startswith("slap-coloc")),
            "county_decided_mw": mw(np15_pool & recut["method"].str.startswith("county")),
            "county_from_eia860_mw": mw(np15_pool & (recut["county_source"] == "eia860")),
            "default_np15_mw": mw(np15_pool & (recut["method"] == "default-np15")),
            "default_np15_plants": int((np15_pool & (recut["method"] == "default-np15")).sum()),
            "note": "default-np15 mass is 'right by default', not measured — enumerated per the precommit honesty duty",
        },
    }

    # gen-pnode -> sub-zone map (atlas universe, latest windows)
    hub_latest = _latest(hub_all).assign(SUB=lambda d: _sub(d["PNODE_ID"]))
    gen_rows = []
    for r in hub_latest.itertuples(index=False):
        hub_short = r.APNODE_ID.replace("TH_", "").replace("_GEN-APND", "")
        if hub_short == "SP15":
            zone, method = "SP15_side", "hub"
        elif hub_short == "ZP26":
            zone, method = ("FSNO", "gates-complex-claim") if r.SUB in GATES_SUBS else ("ZP26", "hub")
        else:
            side = _side_of_slaps(sub2slaps.get(r.SUB, set()))
            if side is not None:
                zone, method = side, "slap-coloc"
            else:
                zone, method = "NP15", "hub-default"
        gen_rows.append({"pnode": r.PNODE_ID, "kind": "gen", "hub": hub_short, "subzone": zone, "method": method})
    gen_map = pd.DataFrame(gen_rows)

    summary["gen_pnode_map"] = {
        "n_pnodes": int(len(gen_map)),
        "by_subzone": {z: int((gen_map["subzone"] == z).sum()) for z in sorted(gen_map["subzone"].unique())},
        "np15_hub_default_n": int(((gen_map["hub"] == "NP15") & (gen_map["method"] == "hub-default")).sum()),
        "gates_claim_n": int((gen_map["method"] == "gates-complex-claim").sum()),
    }

    # witness set (precommit §3) — every expectation checked, misses reported
    def plant_zone(name_frag: str) -> str | None:
        hit = recut[recut["plant_name"].str.contains(name_frag, case=False, na=False)]
        return None if hit.empty else "/".join(sorted(hit["subzone"].unique()))

    witnesses = {
        "Mustang -> FSNO": plant_zone("Mustang"),
        "Five Points/SCHLNDLR -> FSNO": "/".join(sorted(recut.loc[recut["SUB"] == "SCHLNDLR", "subzone"].unique())) if "SUB" in recut else None,
        "Henrietta -> FSNO": plant_zone("Henrietta"),
        "Slate -> FSNO": plant_zone("Slate"),
        "American Kings -> FSNO": plant_zone("American Kings"),
        "Diablo Canyon -> ZP26": plant_zone("Diablo Canyon"),
        "Topaz -> ZP26": plant_zone("Topaz"),
        "CVSR/California Valley -> ZP26": plant_zone("California Valley"),
        "Moss Landing -> NP15": plant_zone("Moss Landing"),
        "Alta (Tehachapi) -> SP15_side": plant_zone("Alta Wind"),
    }
    # recut carries no SUB column after selection above — recompute for the witness
    witnesses["Five Points/SCHLNDLR -> FSNO"] = "/".join(
        sorted(recut.loc[_sub(recut["pnode"]) == "SCHLNDLR", "subzone"].unique())
    ) or None

    # unjoined enumeration on the eGRID 2023 CISO base (vintage stated)
    ciso = egrid[egrid["BACODE"] == "CISO"]
    joined_codes = set(cw["plant_code"])
    unjoined = ciso[~ciso["ORISPL"].isin(joined_codes)]
    summary["unjoined_egrid2023_ciso"] = {
        "note": "eGRID2023 CISO base (82.8 GW) is NOT the model member-fleet denominator (caiso-217: 94.3 GW incl. newer EIA-860 vintages); used here only to enumerate the unjoined cohort honestly",
        "plants": int(len(unjoined)),
        "mw": float(unjoined["NAMEPCAP"].sum()),
        "four_county_mw": float(unjoined.loc[unjoined["CNTYNAME"].isin(FSNO_COUNTIES), "NAMEPCAP"].sum()),
        "four_county_plants": int(unjoined["CNTYNAME"].isin(FSNO_COUNTIES).sum()),
        "helms_check": {
            "in_unjoined": bool((unjoined["PNAME"].str.contains("Helms", case=False, na=False)).any()),
            "county": str(unjoined.loc[unjoined["PNAME"].str.contains("Helms", case=False, na=False), "CNTYNAME"].iloc[0]) if (unjoined["PNAME"].str.contains("Helms", case=False, na=False)).any() else "",
        },
    }

    return {"summary": summary, "witnesses": witnesses}, recut, gen_map


# ---------------------------------------------------------------------------
# section C — the sub-zonal LDF load split (+ the 2-way replication control)
# ---------------------------------------------------------------------------


def _assign_3way(ldf_rows: pd.DataFrame, sub2hub: pd.Series) -> pd.DataFrame:
    """Assign each DLAP_PGAE load pnode to {FSNO, ZP26, NP15} for one window.

    Precedence (precommit §3, load rule): partition sub-LAP first (it IS the
    load-side partition definition), then the caiso-172 hub tiers for the
    remainder (tier 1 substation hub match; tier 2 sub-LAP dominant hub).
    """
    pg = ldf_rows[ldf_rows["APNODE_ID"] == c172.PGAE_LAP][["PNODE_ID", "DIST_FACTOR"]].copy()
    pg = pg.drop_duplicates(subset="PNODE_ID")

    # pnode -> sub-LAP (this window); the rare multi-sub-LAP pnodes go mixed
    slap = ldf_rows[ldf_rows["APNODE_ID"].str.startswith(c172.SUBLAP_PREFIX)]
    n_slaps = slap.groupby("PNODE_ID")["APNODE_ID"].nunique()
    single = slap[slap["PNODE_ID"].map(n_slaps) == 1]
    node2slap = single.drop_duplicates("PNODE_ID").set_index("PNODE_ID")["APNODE_ID"]

    pg["SLAP"] = pg["PNODE_ID"].map(node2slap)
    pg["BUCKET"] = pg["SLAP"].map(SLAP_SIDE)  # FSNO / ZP26 via partition sub-LAPs

    # remainder: caiso-172 tier 1 (substation hub), tier 2 (sub-LAP dominant hub)
    rest = pg["BUCKET"].isna()
    hub_t1 = _sub(pg["PNODE_ID"]).map(sub2hub)
    pg.loc[rest & hub_t1.isin(c172.ZONES), "BUCKET"] = hub_t1[rest & hub_t1.isin(c172.ZONES)]

    still = pg["BUCKET"].isna()
    if still.any():
        dom: dict[str, str] = {}
        for slap_id in slap["APNODE_ID"].unique():
            nodes = slap.loc[slap["APNODE_ID"] == slap_id, "PNODE_ID"].drop_duplicates()
            vc = _sub(nodes).map(sub2hub).value_counts()
            vc = vc[vc.index.isin(c172.ZONES)]
            if len(vc):
                dom[slap_id] = vc.idxmax()
        pg.loc[still, "BUCKET"] = pg.loc[still, "SLAP"].map(dom)
    return pg


def section_c(ldf_all: pd.DataFrame, hub_all: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Day-weighted 3-way split per year + the exact caiso-172 2-way control."""
    buckets = ("FSNO", "ZP26", "NP15")
    rows = []
    per_year_nodes = None
    for year in YEARS:
        y0, y1 = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31")
        days = pd.date_range(y0, y1, freq="D")
        acc = {b: 0.0 for b in buckets}
        unassigned = ldf_sum = 0.0
        tier1 = n_windows = 0
        starts = sorted({s for s in ldf_all["EFF_START_DT"] if s <= y1})
        edges = [d for d in days if d in set(pd.to_datetime(starts))]
        marks = sorted({y0, *[e for e in edges if y0 < e <= y1]})
        for i, mark in enumerate(marks):
            nxt = marks[i + 1] if i + 1 < len(marks) else y1 + pd.Timedelta(days=1)
            w = (nxt - mark).days / len(days)
            if w <= 0:
                continue
            ldf_rows, hub_rows = c172._live(ldf_all, mark), c172._live(hub_all, mark)
            if ldf_rows.empty or hub_rows.empty:
                continue
            sub2hub = c172._sub_to_hub(hub_rows)
            pg = _assign_3way(ldf_rows, sub2hub)
            by = pg.groupby(pg["BUCKET"].fillna("UNASSIGNED"))["DIST_FACTOR"].sum()
            for b in buckets:
                acc[b] += w * float(by.get(b, 0.0))
            unassigned += w * float(by.get("UNASSIGNED", 0.0))
            ldf_sum += w * float(pg["DIST_FACTOR"].sum())
            tier1 = max(tier1, int(_sub(pg["PNODE_ID"]).map(sub2hub).isin(c172.ZONES).sum()))
            n_windows += 1
            if year == YEARS[-1]:
                per_year_nodes = pg  # last window snapshot for the pnode map
        known = sum(acc.values())
        rows.append({
            "year": year,
            **{f"{b.lower()}_pts": round(acc[b], 4) for b in buckets},
            "unassigned_pts": round(unassigned, 4),
            "ldf_sum": round(ldf_sum, 4),
            "n_tier1_nodes": tier1,
            "n_windows": n_windows,
            **{f"{b.lower()}_weight": round(acc[b] / known, 6) for b in buckets},
        })
    split = pd.DataFrame(rows)

    # the exact caiso-172 2-way replication (control vs the committed JSON)
    two_way = c172.derive(YEARS)
    committed = json.loads(SPLIT_JSON.read_text())
    control = {
        "replicated_zp26_weight_mean": round(float(two_way["zp26_weight"].mean()), 6),
        "committed_zp26_weight": committed["zp26_weight"],
        "replicated_per_year": [round(float(x), 6) for x in two_way["zp26_weight"]],
        "committed_per_year": [r["zp26_weight"] for r in committed["per_year"]],
        "exact_match": [round(float(x), 6) for x in two_way["zp26_weight"]] == [r["zp26_weight"] for r in committed["per_year"]],
    }

    # gates G1-G5 (precommit §4)
    checks = []
    for r in split.itertuples(index=False):
        checks.append((f"G1 {r.year} LDF partitions the LAP", r.ldf_sum >= c172.MIN_LDF_SUM, f"sum={r.ldf_sum:.3f}"))
        checks.append((f"G2 {r.year} residue bounded", r.unassigned_pts <= c172.MAX_UNASSIGNED_PTS, f"{r.unassigned_pts:.3f} <= {c172.MAX_UNASSIGNED_PTS}"))
        checks.append((f"G3 {r.year} tier-1 support", r.n_tier1_nodes >= c172.MIN_TIER1_NODES, f"{r.n_tier1_nodes} >= {c172.MIN_TIER1_NODES}"))
    for b in buckets:
        spread = float(split[f"{b.lower()}_weight"].max() - split[f"{b.lower()}_weight"].min())
        checks.append((f"G4 {b} inter-year stability", spread <= c172.MAX_YEAR_SPREAD, f"spread={spread:.4f}"))
    d_zp26 = abs(float(split["zp26_weight"].mean()) - committed["zp26_weight"])
    checks.append(("G5 hub-level reconciliation |dZP26| <= 0.010", d_zp26 <= 0.010, f"|{float(split['zp26_weight'].mean()):.6f} - {committed['zp26_weight']}| = {d_zp26:.6f}"))
    gates = {name: {"pass": bool(ok), "detail": detail} for name, ok, detail in checks}
    gates["all_pass"] = all(ok for _, ok, _ in checks)

    out = {
        "per_year": split.to_dict(orient="records"),
        "mean_weights": {b: round(float(split[f"{b.lower()}_weight"].mean()), 6) for b in buckets},
        "iso_level_reporting_only": {
            "note": "PG&E TAC total share 0.4615 x bucket weight — REPORTING, nothing armed",
            "shares": {b: round(0.4615 * float(split[f"{b.lower()}_weight"].mean()), 6) for b in buckets},
        },
        "two_way_control": control,
        "gates": gates,
    }
    return out, per_year_nodes


def main() -> int:
    ldf_all, hub_all = c172._load_atlas("ATL_LDF"), c172._load_atlas("ATL_PNODE_MAP")

    a = section_a(hub_all, ldf_all)
    b, recut, gen_map = section_b(hub_all, ldf_all)
    c, load_nodes = section_c(ldf_all, hub_all)

    recut.to_csv(OUT_RECUT, index=False)
    load_rows = load_nodes[["PNODE_ID", "BUCKET", "SLAP"]].copy()
    load_rows = load_rows.rename(columns={"PNODE_ID": "pnode", "BUCKET": "subzone", "SLAP": "slap"})
    load_rows["kind"] = "load(DLAP_PGAE, last 2025 window)"
    load_rows["hub"] = ""
    load_rows["method"] = load_rows["slap"].map(lambda s: "partition-slap" if s in SLAP_SIDE else "hub-tiers")
    pnode_map = pd.concat(
        [gen_map[["pnode", "kind", "hub", "subzone", "method"]],
         load_rows[["pnode", "kind", "hub", "subzone", "method"]]],
        ignore_index=True,
    ).sort_values(["kind", "pnode"]).reset_index(drop=True)
    pnode_map.to_csv(OUT_PNODE, index=False)

    result = {
        "probe": "caiso-223 sub-zonal scope (zero-solve; precommit-registered)",
        "precommit": "results/calibration/PRECOMMIT-caiso223-subzonal-scope-2026-08-30.md",
        "sources": {
            "census": "results/calibration/_caiso219_deliverability_census.json",
            "atlas": "data/raw/caiso-atlas/{ATL_LDF,ATL_PNODE_MAP}.csv (caiso-172 snapshots)",
            "crosswalk": "data/raw/reference/caiso-plant-hub-membership.csv (caiso-217)",
            "committed_split": str(SPLIT_JSON.relative_to(REPO)),
            "egrid": "data/raw/fleet-egrid/egrid2023_data_rev2.xlsx PLNT23 (county tier only)",
            "dmm_elements": "FINDING-caiso218-path-limit-survey-2026-08-24.md §B (DMM 2023 annual ch.6)",
        },
        "A_partition": a,
        "B_membership": b,
        "C_ldf_split": c,
    }
    OUT_JSON.write_text(json.dumps(_round(result), indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT_JSON}\nwrote {OUT_RECUT} ({len(recut)} rows)\nwrote {OUT_PNODE} ({len(pnode_map)} rows)")
    print("\nLDF split:", json.dumps(c["mean_weights"]))
    print("gates all_pass:", c["gates"]["all_pass"])
    print("witnesses:", json.dumps(b["witnesses"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
