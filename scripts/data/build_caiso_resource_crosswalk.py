"""Build the CAISO resource-id -> EIA plant crosswalk for the outage overlay.

The CAISO curtailment reports identify units by CAISO resource id / name; the
model's availability overlay keys plants by ``(plant_code, plant_group)`` (EIA
plant code + model asset class). This script proposes a crosswalk between them,
restricted to the thermal fleet the overlay actually derates (COAL / CC / gas
steam / CHP — renewables are LP decision variables and CTs dispatch
economically, so neither needs an availability derate).

Matching is by normalized plant-name token overlap between each CAISO resource
name and the model plant name, with the resource Pmax as a secondary check.
Every proposed row carries a ``match_score`` and ``match_method``; rows at or
above ``--accept-threshold`` are auto-flagged ``accepted=1``. The output is a
**reviewable** CSV — a human can correct/confirm matches and toggle ``accepted``
— and the availability loader
(:func:`market_sim.data.caiso_outages.load_crosswalk`) uses only accepted rows,
so an unreviewed or wrong guess never silently enters a solve.

Output: data/raw/reference/caiso-resource-eia-crosswalk.csv

``--storage`` builds the battery half instead (R-CAISO-35, link 17): each CNOG
battery resource (the R-CAISO-32 census selector, :func:`is_battery_resource`)
is matched to an EIA-860 energy-storage operable plant in a CAISO zone, with
the same score, threshold and capacity sanity. It writes a SIBLING file,
``data/raw/reference/caiso-storage-resource-eia-crosswalk.csv``, so the thermal
overlay's reader (:func:`market_sim.data.caiso_outages.load_crosswalk`) never
sees a battery row. It has no runtime consumer.
"""

from __future__ import annotations

import argparse
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from market_sim.config.paths import RAW_DATA_DIR, REFERENCE_DIR  # noqa: E402

OUT_CSV = REFERENCE_DIR / "caiso-resource-eia-crosswalk.csv"
STORAGE_OUT_CSV = REFERENCE_DIR / "caiso-storage-resource-eia-crosswalk.csv"
# The consolidated DAM outage episodes (curate_caiso_dam_outages.py) — the
# resource universe to crosswalk.
DAM_OUTAGE_WINDOWS = (
    RAW_DATA_DIR / "caiso-dam-outages" / "caiso-dam-outage-windows.parquet"
)

# Model asset classes the availability overlay derates (see caiso_outages).
OVERLAY_GROUPS = ("COAL", "CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP")

# Resource-name markers of non-thermal technologies. A resource whose name
# carries any of these is a solar / wind / storage / hydro resource — often
# co-located at (and name-similar to) a thermal plant (e.g. "Pastoria Solar" at
# Pastoria Energy Facility, "Gateway Energy Storage" at Gateway Generating
# Station). Such a resource must never be crosswalked onto a thermal plant's
# availability derate, so it is dropped from the candidate set regardless of
# name score.
_NONTHERMAL_MARKERS = (
    "solar",
    "solr",
    " pv",
    "photovolt",
    "wind",
    "battery",
    "storage",
    "_bess",
    " bess",
    "esr",
    "_esr",
    "hydro",
    "pumped",
    "geothermal",
    "geysers",
    "biogas",
    "landfill",
    "fuel cell",
    "fuelcell",
)

# Generic tokens dropped before name comparison (corporate suffixes + plant
# nouns that carry no discriminating signal).
_STOP = {
    "llc",
    "inc",
    "lp",
    "llp",
    "co",
    "corp",
    "company",
    "the",
    "of",
    "and",
    "power",
    "plant",
    "energy",
    "center",
    "centre",
    "station",
    "generating",
    "generation",
    "project",
    "facility",
    "facilities",
    "cogen",
    "cogeneration",
    "hybrid",
    "unit",
    "units",
    "site",
    "authority",
    "ca",
    "california",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Battery-resource selector of the R-CAISO-32 census (Part B probe): a CAISO
# storage id suffix, or a storage/battery/BESS name, solar-only names excluded.
_STORAGE_ID = re.compile(r"_(?:BT|BX|ES|BE)\d")
_STORAGE_NAME = re.compile(r"storage|batter|bess", re.I)
_SOLAR_ONLY = re.compile(r"solar(?!.*bess)", re.I)
# Storage-specific tokens dropped from the name score (they name the technology,
# not the plant, and every storage target carries them).
_STORAGE_STOP = {"storage", "battery", "batteries", "bess", "ess", "ess"}


def _norm_tokens(name: object) -> set[str]:
    if not isinstance(name, str):
        return set()
    toks = _TOKEN_RE.findall(name.lower())
    return {t for t in toks if t not in _STOP and len(t) > 1}


def _score(res_name: str, plant_name: str) -> float:
    """Blended token-Jaccard + sequence ratio on normalized plant names."""
    a, b = _norm_tokens(res_name), _norm_tokens(plant_name)
    if not a or not b:
        return 0.0
    jacc = len(a & b) / len(a | b)
    seq = SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    return round(0.7 * jacc + 0.3 * seq, 3)


def load_targets() -> pd.DataFrame:
    """Model thermal overlay targets: (plant_code, plant_group, name, pmax)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import (
        load_fleet_from_csv,
        load_retired_within_window,
    )

    cfg = get_iso_config("CAISO")
    fleet = load_fleet_from_csv("CAISO", cfg) + load_retired_within_window("CAISO", cfg)
    rows: dict[tuple[int, str], dict] = {}
    for g in fleet:
        if g.plant_group not in OVERLAY_GROUPS:
            continue
        key = (int(g.plant_code), g.plant_group)
        r = rows.setdefault(key, {"plant_name": g.name, "plant_pmax_mw": 0.0})
        r["plant_pmax_mw"] += float(g.pmax_mw)
    return pd.DataFrame(
        [
            {
                "plant_code": k[0],
                "plant_group": k[1],
                "plant_name": v["plant_name"],
                "plant_pmax_mw": round(v["plant_pmax_mw"], 1),
            }
            for k, v in rows.items()
        ]
    )


def is_battery_resource(resource_id: object, resource_name: object) -> bool:
    """True when a CNOG resource is a battery under the R-CAISO-32 selector."""
    rid, name = str(resource_id), str(resource_name)
    return bool(
        (_STORAGE_ID.search(rid) or _STORAGE_NAME.search(name))
        and not _SOLAR_ONLY.search(name)
    )


def load_storage_targets() -> pd.DataFrame:
    """EIA-860 operable battery plants in CAISO zones: (plant_code, name, MW).

    Reads the same energy-storage operable schedule and zone lookup as
    :func:`market_sim.model.storage.load_eia860_storage` (compressed air
    excluded, as there), summed to plant level across COD years.
    """
    from market_sim.config.paths import active_eia860_dir
    from market_sim.data.zone_assignment import build_zone_lookup

    df = pd.read_parquet(active_eia860_dir() / "eia860_energy_storage_operable.parquet")
    df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
    df = df[~df["Technology"].astype(str).str.contains("Compressed Air", case=False)]
    zones = build_zone_lookup("CAISO")
    code = pd.to_numeric(df["Plant Code"], errors="coerce")
    df = df.assign(
        plant_code=code,
        mw=pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce"),
    )
    df = df[df["plant_code"].notna()]
    df = df[df["plant_code"].astype(int).isin(set(zones))]
    out = df.groupby("plant_code", as_index=False).agg(
        plant_name=("Plant Name", "first"), plant_pmax_mw=("mw", "sum")
    )
    out["plant_code"] = out["plant_code"].astype(int)
    out["plant_group"] = "BATTERY"
    out["plant_pmax_mw"] = out["plant_pmax_mw"].round(1)
    return out


def load_resources(windows_path: Path) -> pd.DataFrame:
    """Distinct CAISO resources (id, name, max reported Pmax) from the episodes."""
    df = pd.read_parquet(
        windows_path, columns=["resource_id", "resource_name", "resource_pmax_mw"]
    )
    df = df[df["resource_id"].notna()]
    agg = df.groupby("resource_id", as_index=False).agg(
        resource_name=("resource_name", "first"),
        resource_pmax_mw=("resource_pmax_mw", "max"),
    )
    return agg


def _is_nonthermal(name: object) -> bool:
    s = str(name).lower()
    return any(m in s for m in _NONTHERMAL_MARKERS)


def _score_storage(res_name: str, plant_name: str) -> float:
    """:func:`_score` with the technology tokens also dropped."""
    a = _norm_tokens(res_name) - _STORAGE_STOP
    b = _norm_tokens(plant_name) - _STORAGE_STOP
    if not a or not b:
        return 0.0
    jacc = len(a & b) / len(a | b)
    seq = SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    return round(0.7 * jacc + 0.3 * seq, 3)


def build_storage(
    windows_path: Path = DAM_OUTAGE_WINDOWS,
    accept_threshold: float = 0.6,
) -> pd.DataFrame:
    """Propose the battery crosswalk; one row per CNOG battery resource.

    Every census resource is emitted (unmatched ones with a blank plant), so
    the file is the full reviewable census; ``accepted`` uses the thermal
    builder's threshold and capacity sanity unchanged.
    """
    targets = load_storage_targets()
    resources = load_resources(windows_path)
    resources = resources[
        [
            is_battery_resource(i, n)
            for i, n in zip(resources["resource_id"], resources["resource_name"])
        ]
    ]
    out_rows = []
    for _, res in resources.iterrows():
        best_score, best = 0.0, None
        for _, tgt in targets.iterrows():
            sc = _score_storage(str(res["resource_name"]), str(tgt["plant_name"]))
            if sc > best_score:
                best_score, best = sc, tgt
        r_pmax = (
            float(res["resource_pmax_mw"]) if pd.notna(res["resource_pmax_mw"]) else 0.0
        )
        p_pmax = float(best["plant_pmax_mw"]) if best is not None else 0.0
        cap_ok = r_pmax >= 1.0 and (p_pmax <= 0.0 or r_pmax <= 2.0 * p_pmax)
        out_rows.append(
            {
                "resource_id": res["resource_id"],
                "resource_name": res["resource_name"],
                "resource_pmax_mw": res["resource_pmax_mw"],
                "plant_code": int(best["plant_code"]) if best is not None else None,
                "plant_group": "BATTERY" if best is not None else None,
                "plant_name": best["plant_name"] if best is not None else None,
                "plant_pmax_mw": p_pmax if best is not None else None,
                "match_score": best_score,
                "match_method": "name_token",
                "accepted": int(
                    best is not None and best_score >= accept_threshold and cap_ok
                ),
            }
        )
    out = pd.DataFrame(out_rows)
    if not out.empty:
        out["plant_code"] = out["plant_code"].astype("Int64")
        out = out.sort_values(
            ["accepted", "match_score"], ascending=[False, False]
        ).reset_index(drop=True)
    return out


def build(
    windows_path: Path = DAM_OUTAGE_WINDOWS,
    accept_threshold: float = 0.6,
    candidate_floor: float = 0.35,
) -> pd.DataFrame:
    """Propose the crosswalk; return the thermal-candidate frame.

    Rows whose resource name marks a non-thermal technology (solar / wind /
    storage / geothermal / ...) are dropped — they never derate a thermal
    plant even when co-located and name-similar. Only candidates at or above
    ``candidate_floor`` are emitted (the reviewable thermal set); ``accepted``
    marks those at or above ``accept_threshold`` (auto-trusted exact matches).
    """
    targets = load_targets()
    resources = load_resources(windows_path)

    out_rows = []
    for _, res in resources.iterrows():
        if _is_nonthermal(res["resource_name"]):
            continue
        best_score, best = 0.0, None
        for _, tgt in targets.iterrows():
            sc = _score(str(res["resource_name"]), str(tgt["plant_name"]))
            if sc > best_score:
                best_score, best = sc, tgt
        if best is None or best_score < candidate_floor:
            continue
        # Capacity sanity for auto-accept: a resource that maps to a plant should
        # have comparable capacity. Reject a resource far larger than its plant's
        # model capacity (a name-alike at a different/newer plant — e.g. the new
        # Huntington Beach CC vs the retired steam bin) or a trivially tiny one (a
        # co-located condenser/storage sharing the name). Name score still governs
        # everything above candidate_floor; these only gate the accepted flag.
        r_pmax = (
            float(res["resource_pmax_mw"]) if pd.notna(res["resource_pmax_mw"]) else 0.0
        )
        p_pmax = (
            float(best["plant_pmax_mw"]) if pd.notna(best["plant_pmax_mw"]) else 0.0
        )
        cap_ok = r_pmax >= 1.0 and (p_pmax <= 0.0 or r_pmax <= 2.0 * p_pmax)
        out_rows.append(
            {
                "resource_id": res["resource_id"],
                "resource_name": res["resource_name"],
                "resource_pmax_mw": res["resource_pmax_mw"],
                "plant_code": int(best["plant_code"]),
                "plant_group": best["plant_group"],
                "plant_name": best["plant_name"],
                "plant_pmax_mw": best["plant_pmax_mw"],
                "match_score": best_score,
                "match_method": "name_token",
                "accepted": int(best_score >= accept_threshold and cap_ok),
            }
        )
    out = pd.DataFrame(out_rows)
    if not out.empty:
        out = out.sort_values(
            ["accepted", "match_score"], ascending=[False, False]
        ).reset_index(drop=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--windows", default=str(DAM_OUTAGE_WINDOWS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--accept-threshold", type=float, default=0.6)
    ap.add_argument(
        "--storage",
        action="store_true",
        help="build the battery crosswalk (sibling file) instead of the thermal one",
    )
    args = ap.parse_args()

    if args.storage:
        args.out = args.out or str(STORAGE_OUT_CSV)
        out = build_storage(Path(args.windows), args.accept_threshold)
    else:
        args.out = args.out or str(OUT_CSV)
        out = build(Path(args.windows), args.accept_threshold)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    n_acc = int(out["accepted"].sum()) if not out.empty else 0
    print(f"wrote {len(out)} candidate rows ({n_acc} accepted) -> {args.out}")
    if not out.empty:
        acc = out[out["accepted"] == 1]
        print(f"  accepted plants: {acc['plant_code'].nunique()} distinct")


if __name__ == "__main__":
    main()
