"""Derive the ERCOT measured RT (SCED) spare-offer wall ladder — STEAM leg.

The ERCOT-92 corpus adjudication (measure-first; docs/handoffs/
ercot-stgas-shoulder-2026-07.md §9) overturned the ERCOT-89 §8.3 working note
that the NP3-965 sample-day corpus "lacks ST restypes": all four on-disk
60-Day SCED Gen Resource parquets carry the three gas-steam resource types
(GSNONR / GSREH / GSSUP — 44 resources, 100 %-populated SCED1/SCED2 curves,
telemetered statuses, Base Point and HASL). What lacked an ST block was the
DERIVED ERCOT-86 artifact (`ercot_sced_offer_wall_condbinned.json`), whose
restype map deliberately scoped to merchant CC/CT (rule 19 as then applied);
that artifact stays byte-identical and ST-free (test-enforced) — this sibling
derive emits the steam leg into its OWN artifact for the steam-owner seam.

Construction: the ERCOT-86 wall construction exactly (`derive_ercot_sced_
offer_wall`, whose segment/geometry helpers are imported so the two artifacts
share bytes-level conventions), applied to the gas-steam restypes:

* Per SCED interval, for ON-family gas-steam resources, segment the
  energy-dispatchable **online spare** offer curve between Base Point and HASL
  (net of AS responsibility) on the SCED2 (as-dispatched) curve.
* Bin each interval by its hour's within-year net-load percentile on the SAME
  bin edges as the DAM cleared-share artifact.
* Emit, per net-load bin, capacity-weighted quantiles of the spare segments'
  price-as-effective-HR-multiplier (price / delivered-gas day, price clipped
  to HCAP) — the conditional-surface ladder convention.

Scope: the model's OWN 17-plant ST_GAS fleet (`data/raw/reference/
custom-bin-assignments.csv`, Plant_Group == ST_GAS), via the exact
resource-name map below — 36 of the corpus's 44 gas-steam resources map onto
16 of the 17 plants (CFB Power Plant never appears in the corpus, consistent
with its zero CEMS operation in the ERCOT-90 measurement); the remaining 8
resources are small industrial/municipal CHP steam OUTSIDE the model's
non-CHP fleet classing and are EXCLUDED, with their (negligible, ~0.2 % of
ON-spare MW) footprint disclosed in the provenance rather than silently
dropped. The map was validated against nameplate: per-plant sum of max HSL
tracks `custom-bin-assignments` nameplate for all 16 plants (ERCOT-92 log
entry). An unmapped gas-steam resource name in a future corpus update is a
HARD ERROR — the map is reviewed on source update, never silently extended.

Provenance / admissibility (CLAUDE.md rule 13): the SCED spare offer ladder
is an ex-ante market-design measurement (posted RT offers of online
capability, never clearing-price outcomes fed back as inputs); the driver is
the year's own net-load percentile (forward-native); zero fitted scalars.
The artifact is **YEAR-SCOPED**: no pooled fallback is emitted — a year
absent from the artifact gets NO RT steam wall (the DAM basis is retained
byte-identical). 2023 is absent by construction: the on-disk corpus carries
no 2023 sample days, and a 2024/2025-derived surface is barred from 2023's
distinct post-Uri conservative-operations regime (the ERCOT-86 clause).

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the SCED disclosure
source files update; never because a residual moved. Re-derivation commits
must cite the data change.

Usage::

    python scripts/data/derive_ercot_sced_offer_wall_steam.py \
        [--years 2024 2025] \
        [--out data/raw/_validation-source/ercot_sced_offer_wall_steam_condbinned.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    HOURS,
    LADDER_QUANTILES,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _gas_day_series,
    _netload_pct,
    _weighted_quantiles,
)
from derive_ercot_sced_offer_wall import (  # noqa: E402
    SCED_DIR,
    _SCED2_MW,
    _SCED2_PR,
    _STD_TZ,
    _spare_segments,
)

DEFAULT_OUT = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot_sced_offer_wall_steam_condbinned.json"
)

# ERCOT gas-steam resource types (Nodal Protocols resource registration):
# reheat / non-reheat / supercritical boiler steam turbines.
ST_RESTYPES: tuple[str, ...] = ("GSNONR", "GSREH", "GSSUP")

# Exact SCED resource name -> model ST_GAS plant (custom-bin-assignments.csv
# Plant_Name, Plant_Group == ST_GAS). 36 resources / 16 plants; the 17th
# model plant (CFB Power Plant) has no corpus presence. Reviewed, never
# extended silently: _scope_fleet() hard-errors on an unmapped name.
FLEET_PLANT_OF_RESOURCE: dict[str, str] = {
    "BRAUNIG_VHB1": "V H Braunig",
    "BRAUNIG_VHB2": "V H Braunig",
    "BRAUNIG_VHB3": "V H Braunig",
    "B_DAVIS_B_DAVIG1": "Barney M Davis [ST]",
    "CALAVERS_OWS1": "O W Sommers",
    "CALAVERS_OWS2": "O W Sommers",
    "CBY_CBY_G1": "Cedar Bayou",
    "CBY_CBY_G2": "Cedar Bayou",
    "DANSBY_DANSBYG1": "Dansby",
    "GIDEON_GIDEONG1": "Sim Gideon",
    "GIDEON_GIDEONG2": "Sim Gideon",
    "GIDEON_GIDEONG3": "Sim Gideon",
    "GRSES_UNIT1": "Graham",
    "GRSES_UNIT2": "Graham",
    "HLSES_UNIT3": "Handley",
    "HLSES_UNIT4": "Handley",
    "HLSES_UNIT5": "Handley",
    "LHSES_UNIT1": "Lake Hubbard",
    "LHSES_UNIT2A": "Lake Hubbard",
    "MCSES_UNIT6": "Mountain Creek",
    "MCSES_UNIT7": "Mountain Creek",
    "MCSES_UNIT8": "Mountain Creek",
    "MIL_MILLERG1": "R W Miller",
    "MIL_MILLERG2": "R W Miller",
    "MIL_MILLERG3": "R W Miller",
    "OLINGR_OLING_2": "Ray Olinger",
    "OLINGR_OLING_3": "Ray Olinger",
    "SCSES_UNIT1A": "Stryker Creek",
    "SCSES_UNIT2": "Stryker Creek",
    "SPNCER_SPNCE_4": "Spencer",
    "SPNCER_SPNCE_5": "Spencer",
    "TRSES_UNIT6": "Trinidad (TX)",
    "WAP_WAP_G1": "W A Parish [ST]",
    "WAP_WAP_G2": "W A Parish [ST]",
    "WAP_WAP_G3": "W A Parish [ST]",
    "WAP_WAP_G4": "W A Parish [ST]",
}

# Corpus gas-steam resources OUTSIDE the model's non-CHP ST_GAS fleet: small
# industrial / municipal CHP steam (Dow Chemical; Texas Petrochemicals; GEUS
# Greenville), all <= 49 MW HSL, ~0.2 % of gas-steam ON-spare MW. Excluded
# from the ladder, disclosed in provenance.
NON_FLEET_RESOURCES: frozenset[str] = frozenset(
    {
        "DOWGEN_DOW_ST64",
        "DOWGEN_DOW_ST65",
        "DOWGEN_DOW_ST84",
        "DOWGEN_DOW_ST95",
        "PR_PR_G2",
        "STEAM1A_STEAM_1",
        "STEAM_STEAM_2",
        "STEAM_STEAM_3",
    }
)

_READ_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HASL",
    "HSL",
    "Base Point",
] + [c for pair in zip(_SCED2_MW, _SCED2_PR) for c in pair]


def _scope_fleet(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Split gas-steam rows into (fleet rows, excluded-resource disclosure).

    Hard-errors on a resource name in neither the fleet map nor the disclosed
    non-fleet set, so a corpus update carrying a new gas-steam resource forces
    a map review instead of a silent scope drift (rule 23 hygiene).
    """
    names = set(df["Resource Name"].unique())
    unknown = names - set(FLEET_PLANT_OF_RESOURCE) - set(NON_FLEET_RESOURCES)
    if unknown:
        raise ValueError(
            "unmapped gas-steam resource name(s) in SCED corpus — review "
            f"FLEET_PLANT_OF_RESOURCE / NON_FLEET_RESOURCES: {sorted(unknown)}"
        )
    non = df[df["Resource Name"].isin(NON_FLEET_RESOURCES)]
    stat = non["Telemetered Resource Status"].astype(str).str.strip()
    non_on = non[stat.str.startswith("ON")]
    spare = np.maximum(
        non_on["HASL"].to_numpy(float)
        - np.maximum(non_on["Base Point"].to_numpy(float), 0.0),
        0.0,
    )
    excluded = {}
    for name in sorted(names & NON_FLEET_RESOURCES):
        hsl_max = non.loc[non["Resource Name"] == name, "HSL"].max()
        excluded[name] = {
            "rows": int((non["Resource Name"] == name).sum()),
            # all-NaN HSL (never telemetered) -> null, not NaN (strict JSON)
            "max_hsl_mw": round(float(hsl_max), 1) if pd.notna(hsl_max) else None,
            "on_spare_mw_sum": round(
                float(np.nansum(spare[(non_on["Resource Name"] == name).to_numpy()])),
                1,
            ),
        }
    return df[df["Resource Name"].isin(FLEET_PLANT_OF_RESOURCE)].copy(), excluded


def _load_year(year: int) -> tuple[pd.DataFrame, dict, list[str]]:
    """ON-status fleet gas-steam SCED rows + excluded disclosure + file names."""
    files = sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    )
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        frames.append(df[df["Resource Type"].isin(ST_RESTYPES)])
    if not frames:
        return pd.DataFrame(columns=_READ_COLS), {}, []
    fleet, excluded = _scope_fleet(pd.concat(frames, ignore_index=True))
    stat = fleet["Telemetered Resource Status"].astype(str).str.strip()
    fleet["_status"] = stat
    return fleet[stat.str.startswith("ON")].copy(), excluded, [p.name for p in files]


def derive_year(year: int, gas_day: pd.Series) -> tuple[dict, dict, list[str]]:
    """Return ``({"ST": {"ladder": [...]}}, coverage, source_files)`` for one year."""
    df, excluded, files = _load_year(year)
    if df.empty:
        return {}, {}, files

    # CPT -> fixed CST -> non-leap hour-of-year (the ERCOT-86 clock handling;
    # Feb 29 dropped to match the model's 8760 clock and _netload_pct).
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    df = df.loc[np.asarray(ok)].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["cls"] = "ST"
    df["plant"] = df["Resource Name"].map(FLEET_PLANT_OF_RESOURCE)
    df["_ts_key"] = df["SCED Time Stamp"].to_numpy()
    df["_date"] = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)].to_numpy()

    gas = gas_day.reindex(pd.DatetimeIndex(df["_date"])).to_numpy(float)
    df["gas_day"] = gas
    df = df[df["gas_day"] > 0].copy()

    segments = _spare_segments(df)
    date_by_ts = dict(zip(df["_ts_key"], df["gas_day"]))
    segments["mult"] = segments["price"] / segments["ts"].map(date_by_ts).astype(float)

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,)
    n_bins = len(edges) + 1
    segments["bin"] = hour_bin[np.minimum(segments["hoy"].to_numpy(int), HOURS - 1)]

    ladders: list[list[list[float]]] = []
    cov_bins: list[dict] = []
    for b in range(n_bins):
        gb = segments[segments["bin"] == b]
        n_iv = int(gb["ts"].nunique())
        n_days = int(pd.Series(gb["hoy"] // 24).nunique())
        qs = (
            _weighted_quantiles(
                gb["mult"].to_numpy(float),
                gb["mw"].to_numpy(float),
                LADDER_QUANTILES,
            )
            if len(gb)
            else [float("nan")] * len(LADDER_QUANTILES)
        )
        ladders.append([[float(q), round(m, 3)] for q, m in zip(LADDER_QUANTILES, qs)])
        cov_bins.append(
            {
                "intervals": n_iv,
                "days": n_days,
                "mean_spare_gw": round(float(gb["mw"].sum()) / max(n_iv, 1) / 1e3, 3),
            }
        )

    # Steam-specific disclosure: which plants carry the surface, under which
    # telemetered status families, and what was excluded as out-of-fleet.
    spare_row = np.maximum(
        df["HASL"].to_numpy(float) - np.maximum(df["Base Point"].to_numpy(float), 0.0),
        0.0,
    )
    per_plant = (
        pd.DataFrame({"plant": df["plant"].to_numpy(), "spare": spare_row})
        .groupby("plant")["spare"]
        .agg(["count", "sum"])
    )
    total_spare = float(per_plant["sum"].sum()) or 1.0
    coverage = {
        "bins": cov_bins,
        "plants": {
            p: {
                "on_rows": int(r["count"]),
                "on_spare_share": round(float(r["sum"]) / total_spare, 4),
            }
            for p, r in per_plant.iterrows()
        },
        "status_rows": df["_status"].value_counts().to_dict(),
        "excluded_non_fleet": excluded,
        "fleet_plants_absent": sorted(
            set(FLEET_PLANT_OF_RESOURCE.values()) - set(per_plant.index)
        ),
    }
    return {"ST": {"ladder": ladders}}, coverage, files


def main() -> None:
    """Derive and write the RT (SCED) spare-offer wall STEAM ladder JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    gas_day = _gas_day_series()
    per_year: dict[int, dict] = {}
    coverage: dict[str, dict] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        per_year[y], coverage[str(y)], sources[str(y)] = derive_year(y, gas_day)
        if "ST" in per_year[y]:
            entry = per_year[y]["ST"]
            p50 = [lad[2][1] for lad in entry["ladder"]]
            ivs = [c["intervals"] for c in coverage[str(y)]["bins"]]
            print(f"{y} ST: wall p50 mult by bin = {p50}")
            print(f"          intervals by bin     = {ivs}")

    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data, scoped sample "
                "days, delivery years " + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "per-interval Base Point -> HASL segments of the SCED2 "
                "(as-dispatched) offer curve of ON-status gas-steam resources "
                "(the energy-dispatchable online spare, net of AS "
                "responsibility), MW-weighted quantile ladder of segment "
                "prices as effective-HR multipliers (price / "
                "HH-daily+ERCOT-basis gas), derived within "
                "net-load-percentile bins — the ERCOT-86 wall construction, "
                "steam leg"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - wind "
                "- solar), forward-native (a forecast year's bins regenerate "
                "from its own load+VRE)"
            ),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "classes": {"ST": list(ST_RESTYPES)},
            "fleet_scope": {
                "basis": (
                    "the model's own 17-plant ST_GAS fleet "
                    "(custom-bin-assignments.csv, Plant_Group == ST_GAS) via "
                    "the exact resource-name map FLEET_PLANT_OF_RESOURCE (36 "
                    "corpus resources -> 16 plants; map validated per-plant "
                    "against nameplate, ERCOT-92); non-fleet industrial/CHP "
                    "gas-steam resources excluded and disclosed per year in "
                    "coverage.excluded_non_fleet; an unmapped corpus name is "
                    "a hard error"
                ),
                "resource_map": FLEET_PLANT_OF_RESOURCE,
                "non_fleet_resources": sorted(NON_FLEET_RESOURCES),
                "cfb_note": (
                    "CFB Power Plant (the 17th model plant) never appears in "
                    "the corpus — consistent with its zero CEMS operation in "
                    "the ERCOT-90 measurement artifact"
                ),
            },
            "year_scoped": (
                "NO pooled fallback by design (rule 13): the SCED corpus is "
                "scoped sample days and the RT offer surface is regime-bound "
                "— a year absent from this artifact gets NO RT steam wall "
                "(the DAM basis is retained); 2023 is absent by construction "
                "(no 2023 sample days on disk, and a 2024/2025-derived "
                "ladder is barred from 2023's post-Uri "
                "conservative-operations regime)"
            ),
            "sample_day_files": sources,
            "coverage": coverage,
            "adjudication": (
                "ERCOT-92: supersedes the ERCOT-89 §8.3 working note 'the "
                "corpus lacks ST restypes' — the raw corpus carries "
                "GSNONR/GSREH/GSSUP with full curves and statuses; only the "
                "derived CC/CT artifact excluded them (rule-19 scope). The "
                "CC/CT artifact (ercot_sced_offer_wall_condbinned.json) "
                "stays byte-identical and ST-free; this artifact is the "
                "steam-owner seam's basis"
            ),
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update, never because a residual moved"
            ),
        }
    }
    for y in args.years:
        if "ST" in per_year[y]:
            result.setdefault("ST", {"years": {}})["years"][str(y)] = per_year[y]["ST"]

    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
