"""Derive the CAISO DAM RESOURCE ID -> CAMPD ORIS facility crosswalk.

Stage 2 of the owner-directed CAISO DAM-outage intake (rule 14 measured
instrument; FINDING-caiso104 §5 / caiso-104 handoff §3): the daily Curtailed
and Non-Operational Generator reports key outages by CAISO market RESOURCE ID
(`data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet`), while the
model's unit-outage layer keys facilities by CAMPD ORIS id
(`campd-unit-outages-CAISO.csv`, `data.outages`). This derive builds the
name-match crosswalk between the two namespaces so the DAM windows can take
unit-level precedence over the CAMPD event-detected windows (CAMPD stays the
fallback — owner directive).

Matching (thermal fleet only — the outage layer derates COAL/CC/ST bins;
wind/solar/hydro/intertie resources are out of scope by construction):

  1. Universe: CAMPD facility (id, name) pairs from the CA facility-level
     parquets (2023-2025) — every combustion source >= 25 MW — augmented with
     the `campd-unit-outages-CAISO.csv` facility list and its plant_group.
  2. Names normalized (uppercase, punctuation stripped, corporate/generic
     suffix stopwords removed) and token-set scored (Jaccard); a resource
     matches a facility when the score clears MATCH_MIN_SCORE or one
     normalized token set contains the other.
  3. Non-thermal resources (solar/wind/battery/hydro/geo by name or CAISO
     id-suffix convention) and sub-15-MW resources are excluded BEFORE
     matching — they are exactly where generic place-name tokens (Valley,
     Lake, Fresno, Blythe) mis-match a thermal facility.
  4. HAND-VERIFIED prefix pins re-route the matches the token scorer gets
     wrong (same-token sister plants: Gilroy Cogen vs Gilroy Peaking,
     City-of-Lodi GTs vs Lodi Energy Center, Carson Cogeneration vs SMUD
     Carson Ice-Gen, ...) and map plants absent from the CAMPD CA list
     (Carlsbad, King City Peaking) via the EIA-860 plant table; adjudicated
     false positives are dropped by the EXCLUDE list. `match_method`
     distinguishes `verified-prefix` from `name-token` rows.

Output: ``data/raw/reference/caiso-dam-resource-crosswalk.csv`` with columns
``resource_id, resource_name, resource_pmax_mw, facility_id, facility_name,
plant_group, match_method, score``. Deterministic; re-derives only when the
DAM corpus or CAMPD source updates (rule 23 — never from a residual).

Usage: python scripts/data/derive_caiso_dam_resource_crosswalk.py
"""

import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
WINDOWS = (
    REPO / "data" / "raw" / "caiso-dam-outages" / "caiso-dam-outage-windows.parquet"
)
CAMPD_FAC = REPO / "data" / "raw" / "campd-facility-level"
CAMPD_OUT = REPO / "data" / "raw" / "campd-unit-outages-CAISO.csv"
EIA_PLANT = REPO / "data" / "raw" / "eia-860" / "eia860_plant.parquet"
OUT = REPO / "data" / "raw" / "reference" / "caiso-dam-resource-crosswalk.csv"
YEARS = (2023, 2024, 2025)

MATCH_MIN_SCORE = 0.5

# Tokens carrying no plant identity (corporate forms, generic plant words).
STOP = {
    "LLC",
    "LP",
    "INC",
    "CO",
    "COMPANY",
    "CORP",
    "CORPORATION",
    "PARTNERS",
    "LTD",
    "GEN",
    "STA",
    "STATION",
    "GENERATING",
    "GENERATION",
    "GENERATOR",
    "POWER",
    "PLANT",
    "PROJECT",
    "ENERGY",
    "CENTER",
    "CENTRE",
    "FACILITY",
    "UNIT",
    "UNITS",
    "AGGREGATE",
    "AGGREGATED",
    "COMBINED",
    "CYCLE",
    "CC",
    "CCGT",
    "COGEN",
    "COGENERATION",
    "PEAKER",
    "PEAKING",
    "THE",
    "OF",
    "AND",
    "I",
    "II",
    "III",
    "IV",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
}

# Hand-verified RESOURCE-ID prefix -> plant-code pins, for resources the
# auto-matcher mis-routes (a same-token sister plant outranks the right one)
# or whose plant is absent from the CAMPD CA facility list (name then comes
# from the EIA-860 plant table — same ORIS/EIA plant-code namespace). Each
# pin verified in-session against EIA-860 plant names + capacity (caiso-105
# review; see the FINDING). Keyed by resource_id PREFIX (the substation half
# before the first "_").
VERIFIED_PREFIX: dict[str, int] = {
    "CARLS1": 59002,  # Carlsbad Energy Center (not in CAMPD CA parquets)
    "CARLS2": 59002,  # Carlsbad Energy Center unit 2 resource
    "KNGCTY": 55811,  # King City Peaking (EIA) — NOT King City Power Plant
    "GILROY": 10034,  # Gilroy Power Plant / Calpine Gilroy Cogen (120 MW) —
    #   NOT Gilroy Peaking Energy Center 55810 (which keeps GILRPP_*)
    "GRNLF2": 10349,  # Greenleaf 2 Power Plant (EIA; CAMPD name "Yuba City
    #   Energy Center" — same facility, renamed) — NOT Greenleaf 1 (10350)
    "SMPRIP": 50299,  # AltaGas Ripon Energy (ex Ripon Cogeneration) — NOT
    #   Ripon Generation Station 56135
    "LODI25": 7451,  # City of Lodi GTs (EIA "Lodi") — NOT Lodi Energy Center
    "LGHTHP": 10169,  # Carson Cogeneration (Carson CA, in-CAISO; ORIS 7527
    #   "Carson Ice-Gen Project" is SMUD/BANC, outside the CAISO BA)
    "SUNSET": 52169,  # Midway Sunset Cogen — NOT Midway Peaking 56639
}

# Hand-review EXCLUDES: (resource_id, facility_id) auto-matches adjudicated
# FALSE (shared token is a place name, not the same plant) or unresolvable.
EXCLUDE: set[tuple[str, int]] = {
    ("DIABLO_7_UNIT 1", 57027),  # Diablo Canyon nuclear, not Canyon Power
    ("DIABLO_7_UNIT 2", 57027),
    ("TENGEN_2_PL1X2", 57027),  # Placerita Canyon Cogen, not Canyon Power
    ("PNOCHE_1_PL1X2", 56803),  # "Panoche Peaker" ambiguous: Wellhead Power
    #   Panoche (55874) vs CalPeak Panoche Peaker Plant (55508) — same size,
    #   unresolvable from names alone; left unmapped
    ("STIGCT_2_LODI", 57978),  # NCPA STIG unit, not Lodi Energy Center;
    #   exact ORIS unresolved
    ("ULTPFR_1_UNIT 1", 10156),  # Rio Bravo Fresno (biomass), not Fresno
    #   Cogeneration Partners
}


def norm_tokens(name: str) -> frozenset[str]:
    """Normalized informative token set of a plant/resource name."""
    s = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper())
    return frozenset(t for t in s.split() if t and t not in STOP)


# The outage layer derates thermal (COAL/CC/ST) plant bins only; resources
# that are solar / wind / battery / hydro / geothermal by their own market
# name or id-suffix convention are out of scope, and they are exactly where
# generic place-name tokens (Valley, Lake, Fresno, Blythe...) mis-match a
# thermal facility. Suffix conventions: *SOLAR*, *WND*, trailing SR#/LR#
# (solar), BT# (battery), plus name keywords.
_NONTHERMAL_NAME = re.compile(
    r"SOLAR|PHOTOVOLT|\bPV\b|WIND\b|BESS|STORAGE|BATTERY|HYDRO|PUMP|GEO\b|"
    r"GEOTHERMAL|RECOVERY|\bLAKE\b|BIOMASS|LANDFILL|DIGESTER"
)
_NONTHERMAL_SUFFIX = re.compile(r"(SOLAR\d*|WND\d*|[SL]R\d|BT\d)$")
# Resources below this size cannot move a plant-level derate materially and
# are dominated by rooftop/aggregation pseudo-resources.
MIN_RESOURCE_MW = 15.0


def is_nonthermal(resource_id: str, resource_name: str) -> bool:
    """True when the market resource is outside the thermal outage scope."""
    if _NONTHERMAL_NAME.search(str(resource_name).upper()):
        return True
    tail = str(resource_id).split("_")[-1]
    return bool(_NONTHERMAL_SUFFIX.search(tail))


def main() -> int:
    w = pd.read_parquet(WINDOWS)
    res = (
        w.groupby(["resource_id", "resource_name"], as_index=False)
        .agg(resource_pmax_mw=("resource_pmax_mw", "max"))
        .drop_duplicates("resource_id")
    )
    res["prefix"] = res.resource_id.str.split("_").str[0]

    # facility universe
    frames = []
    for y in YEARS:
        p = CAMPD_FAC / f"CA_{y}.parquet"
        if p.exists():
            frames.append(
                pd.read_parquet(
                    p, columns=["facilityId", "facilityName"]
                ).drop_duplicates()
            )
    fac = pd.concat(frames, ignore_index=True).drop_duplicates("facilityId")
    # facilityId is a string column in the CAMPD parquets (the LA_BASIN
    # crosswalk convention in _caiso102_evening_merit) — key by int.
    fac["facilityId"] = pd.to_numeric(fac.facilityId, errors="coerce").astype(int)
    fac = fac.drop_duplicates("facilityId")
    grp = (
        pd.read_csv(CAMPD_OUT)[["facility_id", "plant_group"]]
        .drop_duplicates("facility_id")
        .set_index("facility_id")
        .plant_group
    )
    fac["plant_group"] = fac.facilityId.map(grp)
    fac["toks"] = fac.facilityName.map(norm_tokens)

    # EIA-860 plant-name fallback for VERIFIED_PREFIX pins whose plant is not
    # a CAMPD CA facility (Carlsbad, King City Peaking, ...): same EIA/ORIS
    # plant-code namespace the model fleet keys on.
    missing = set(VERIFIED_PREFIX.values()) - set(fac.facilityId)
    if missing:
        eia = pd.read_parquet(EIA_PLANT, columns=["Plant Code", "Plant Name"])
        eia = eia[eia["Plant Code"].isin(missing)].drop_duplicates("Plant Code")
        add = pd.DataFrame(
            {
                "facilityId": eia["Plant Code"].astype(int),
                "facilityName": eia["Plant Name"],
                "plant_group": "",
                "toks": eia["Plant Name"].map(norm_tokens),
            }
        )
        fac = pd.concat([fac, add], ignore_index=True)

    rows = []
    for r in res.itertuples(index=False):
        if r.resource_pmax_mw < MIN_RESOURCE_MW or is_nonthermal(
            r.resource_id, r.resource_name
        ):
            continue
        method, score, hit = "", 0.0, None
        if r.prefix in VERIFIED_PREFIX:
            fid = VERIFIED_PREFIX[r.prefix]
            frow = fac[fac.facilityId == fid]
            if frow.empty:
                continue
            method, score, hit = "verified-prefix", 1.0, frow.iloc[0]
        else:
            rt = norm_tokens(r.resource_name)
            if not rt:
                continue
            best_s, best = 0.0, None
            for f in fac.itertuples(index=False):
                ft = f.toks
                if not ft:
                    continue
                inter = len(rt & ft)
                if inter == 0:
                    continue
                s = inter / len(rt | ft)
                if rt <= ft or ft <= rt:
                    s = max(s, 0.9)
                if s > best_s:
                    best_s, best = s, f
            if best is None or best_s < MATCH_MIN_SCORE:
                continue
            method, score, hit = "name-token", round(best_s, 3), best
        rows.append(
            {
                "resource_id": r.resource_id,
                "resource_name": r.resource_name,
                "resource_pmax_mw": r.resource_pmax_mw,
                "facility_id": int(hit.facilityId),
                "facility_name": hit.facilityName,
                "plant_group": hit.plant_group if pd.notna(hit.plant_group) else "",
                "match_method": method,
                "score": score,
            }
        )

    out = pd.DataFrame(rows)
    out = out[
        ~out.apply(lambda r: (r.resource_id, r.facility_id) in EXCLUDE, axis=1)
    ].sort_values(["facility_id", "resource_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(
        f"wrote {OUT}: {len(out)} resources -> {out.facility_id.nunique()} "
        f"facilities ({(out.match_method == 'verified-prefix').sum()} verified, "
        f"{(out.match_method == 'name-token').sum()} name-token)"
    )

    if "--report" in sys.argv:
        # Hand-review report: every match (for false-positive pruning), then
        # the biggest unmatched resources by non-ambient curtailed MW-days
        # (for VERIFIED_PREFIX candidates the name-matcher cannot see).
        print("\n=== ALL MATCHES (review for false positives) ===")
        print(out.to_string())
        nw = w[w.nature_of_work != "AMBIENT_DUE_TO_TEMP"]
        mwd = (
            nw.assign(mwd=nw.curtailment_mw * nw.days_reported)
            .groupby("resource_id")
            .mwd.sum()
        )
        unm = res[~res.resource_id.isin(set(out.resource_id))].copy()
        unm["mwd"] = unm.resource_id.map(mwd).fillna(0.0)
        print("\n=== TOP UNMATCHED by non-ambient curtailed MW-days ===")
        print(
            unm.sort_values("mwd", ascending=False)
            .head(40)[["resource_id", "resource_name", "resource_pmax_mw", "mwd"]]
            .to_string()
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
