#!/usr/bin/env python3
"""Derive eGRID identity-reconciled heat rates for CAMPD-less fossil plants.

THE OBJECT (FINDING-nyiso150-allegany-hr-identity-2026-08-22.md): a fossil
plant the fleet knows by its EIA-860/923 plant id can carry its measured
history in eGRID under a DIFFERENT ORISPL (a two-registry identity split, the
``campd.CAMPD_UNIT_PLANT_REMAP`` / Astoria 55375↔57664 family). Such a plant
has no CAMPD record under either id, so the model prices it at the
``HEAT_RATE_BINS`` vintage class default even though a stable multi-vintage
measured rate exists. NYISO's live instance is Allegany (EIA 7784 ↔ eGRID
10619 "Allegany Station No. 133"): the 7.5 gas_cc "older" default against a
measured 7.99–8.68 across seven vintages.

THE DISCOVERY RULE — threshold-free (rules 5/21), run mechanically over the
ISO's whole population, never a per-plant carve:

* universe: EIA-923 fossil plants of the ISO's BA absent from every on-disk
  CAMPD unit-level vintage of the ISO's state extracts;
* identity: an eGRID plant row of the same state under a DIFFERENT ORISPL
  whose ``PLNGENAN`` equals the plant's EIA-923 annual net generation to
  <0.5 MWh in EVERY overlapping eGRID vintage, with >=2 overlaps. Exact
  equality across whole years of multi-GWh magnitudes is an identity, not a
  coincidence; one overlap is not enough to claim it.
* rate: pooled ΣPLHTIAN / ΣPLNGENAN over ALL overlapping vintages — declared
  a priori; arithmetic on eGRID's own published fields, never chosen
  (the posture of the accepted 55641 boundary repair). The per-vintage rates
  and the leave-one-vintage-out range are written alongside as the LOYO
  record.
* MERGED identity (nyiso-186, 2026-09-04): the same test at the TWO-plant
  sum. An EIA plant ``p`` absent from CAMPD whose generators eGRID files under
  a co-located EIA plant ``q`` of the same state — eGRID ``PLNGENAN(q)``
  equals ``netgen(p) + netgen(q)`` to the same ``MATCH_TOL_MWH`` in EVERY
  overlapping vintage, ``>= MIN_OVERLAPS`` — takes ``q``'s pooled rate: the two
  blocks ARE one eGRID plant, and the plant-grain join already prices ``q``
  from that boundary. Same tolerance, same overlap rule, same rate rule, same
  LOYO record; the row carries ``identity = merged`` and names ``q``. NYISO's
  live instance is Astoria Energy II (EIA 57664 ↔ eGRID 55375, whose six
  generators CT1–CT4 / ST1 / ST2 EIA-860 splits across 55375 and 57664; no
  eGRID row for 57664 exists in any vintage), which the one-to-one predicate
  cannot reach and the fleet therefore priced at the ``gas_cc`` f-class
  default 6.70 against a facility meter of 7.05 (running-hour, merged).

Output: ``data/raw/_processed-legacy/egrid_identity_heat_rates_<ISO>.csv``.
Consumed by ``market_sim.data.fleet.eia860.apply_egrid_identity_heat_rates``
under ``ScenarioConfig.egrid_identity_heat_rates`` (default off).

Rule 23: re-derives only when its sources update (a new eGRID vintage, a new
EIA-923 year, a new CAMPD extract); nothing here reads a model output or a
residual. ``--check`` re-derives and byte-compares against the committed
artifact.
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

E923 = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
EGRID_DIR = REPO / "data/raw/fleet-egrid"
CAMPD_DIR = REPO / "data/raw/campd-unit-level"
OUT_DIR = REPO / "data/raw/_processed-legacy"

# EIA-923 energy-source codes counted as fossil for the candidate universe.
FOSSIL_FUELS = {"NG", "DFO", "RFO", "KER", "BIT", "SUB", "LIG", "WC", "PC", "OG", "JF"}

# ISO -> (EIA-930 BA code, CAMPD state extracts, eGRID PSTATABB set). Only
# ISOs a lane has derived for appear; adding one is adding a row (rule 25 —
# each ISO's lane derives its own artifact from its own market's data).
ISO_SCOPE: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "NYISO": ("NYIS", ("NY",), ("NY",)),
}

MATCH_TOL_MWH = 0.5  # "equal to the MWh": float-format slack only, not a band
MIN_OVERLAPS = 2


def _egrid_vintages(states: tuple[str, ...]) -> dict[int, pd.DataFrame]:
    """Load every on-disk eGRID plant sheet, filtered to ``states`` rows with
    positive heat input; keyed by vintage year, indexed by ORISPL."""
    out: dict[int, pd.DataFrame] = {}
    for f in sorted(glob.glob(str(EGRID_DIR / "*.xlsx"))):
        digits = "".join(ch for ch in Path(f).name if ch.isdigit())
        if len(digits) < 4:
            continue
        year = int(digits[:4])
        xl = pd.ExcelFile(f)
        plnt = [s for s in xl.sheet_names if str(s).upper().startswith("PLNT")]
        if not plnt:
            continue
        df = pd.read_excel(f, sheet_name=plnt[0], header=1)
        need = {"ORISPL", "PSTATABB", "PLNGENAN", "PLHTIAN"}
        if not need.issubset(df.columns):
            continue
        df = df[
            df["PSTATABB"].isin(states)
            & df["PLNGENAN"].notna()
            & df["PLHTIAN"].notna()
            & (df["PLHTIAN"] > 0)
        ]
        out[year] = df.set_index(df["ORISPL"].astype(int))[["PLNGENAN", "PLHTIAN"]]
    return out


def derive(iso: str) -> pd.DataFrame:
    """Run the discovery rule for one ISO; return the artifact frame."""
    ba, campd_states, egrid_states = ISO_SCOPE[iso]
    e923 = pd.read_parquet(E923)
    pop = e923[(e923["ba_code"] == ba) & e923["fuel_type"].isin(FOSSIL_FUELS)]
    ann = pop.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum()

    campd_ids: set[int] = set()
    for st in campd_states:
        for f in sorted(glob.glob(str(CAMPD_DIR / f"{st}_*.parquet"))):
            campd_ids |= set(
                pd.read_parquet(f, columns=["facilityId"])["facilityId"]
                .astype(int)
                .unique()
            )

    egrid = _egrid_vintages(egrid_states)
    annmap = {(int(p), int(y)): float(v) for (p, y), v in ann.items()}
    years_by_plant: dict[int, list[int]] = {}
    for p, y in annmap:
        years_by_plant.setdefault(p, []).append(y)

    eia_plants = sorted(set(int(p) for p, _ in annmap))
    rows = []
    for p in sorted(set(eia_plants) - campd_ids):
        match_years: dict[int, list[int]] = {}
        # Merged-identity candidates: eGRID ORISPL -> the vintages in which
        # PLNGENAN(oris) == netgen(p) + netgen(oris). ``oris`` must itself be an
        # EIA-923 plant of the same population (a sibling block, not a stranger).
        merged_years: dict[int, list[int]] = {}
        for y in years_by_plant[p]:
            v = annmap[(p, y)]
            if v <= 0 or y not in egrid:
                continue
            hit = egrid[y][abs(egrid[y]["PLNGENAN"] - v) < MATCH_TOL_MWH]
            for oris in hit.index:
                if int(oris) != p:
                    match_years.setdefault(int(oris), []).append(y)
            for q in eia_plants:
                if q == p or (q, y) not in annmap or q not in egrid[y].index:
                    continue
                if abs(float(egrid[y].loc[q, "PLNGENAN"]) - (v + annmap[(q, y)])) < (
                    MATCH_TOL_MWH
                ):
                    merged_years.setdefault(int(q), []).append(y)
        candidates = [
            (oris, yrs, "one-to-one") for oris, yrs in sorted(match_years.items())
        ]
        candidates += [(q, yrs, "merged") for q, yrs in sorted(merged_years.items())]
        for oris, yrs, identity in candidates:
            overlap = [
                y
                for y in years_by_plant[p]
                if y in egrid
                and annmap[(p, y)] > 0
                and oris in egrid[y].index
                and (identity == "one-to-one" or (oris, y) in annmap)
            ]
            if len(yrs) >= MIN_OVERLAPS and sorted(yrs) == sorted(overlap):
                hi = sum(float(egrid[y].loc[oris, "PLHTIAN"]) for y in yrs)
                ng = sum(float(egrid[y].loc[oris, "PLNGENAN"]) for y in yrs)
                per = {
                    y: float(egrid[y].loc[oris, "PLHTIAN"])
                    / float(egrid[y].loc[oris, "PLNGENAN"])
                    for y in sorted(yrs)
                }
                loyo = [
                    (hi - float(egrid[y].loc[oris, "PLHTIAN"]))
                    / (ng - float(egrid[y].loc[oris, "PLNGENAN"]))
                    for y in sorted(yrs)
                    if ng - float(egrid[y].loc[oris, "PLNGENAN"]) > 0
                ]
                rows.append(
                    {
                        "plant_id": p,
                        "egrid_orispl": oris,
                        "heat_rate_mmbtu_mwh": round(hi / ng, 4),
                        "n_vintages": len(yrs),
                        "vintages": ";".join(str(y) for y in sorted(yrs)),
                        "per_vintage_hr": ";".join(
                            f"{y}:{per[y]:.4f}" for y in sorted(per)
                        ),
                        "loyo_min": round(min(loyo), 4) if loyo else "",
                        "loyo_max": round(max(loyo), 4) if loyo else "",
                        "source": (
                            "eGRID PLHTIAN/PLNGENAN pooled over matched "
                            "vintages; identity = exact PLNGENAN == EIA-923 annual "
                            "netgen (<0.5 MWh) in every overlapping vintage"
                            if identity == "one-to-one"
                            else "eGRID PLHTIAN/PLNGENAN pooled over matched "
                            f"vintages; identity = MERGED: exact PLNGENAN({oris}) "
                            f"== EIA-923 annual netgen({p}) + netgen({oris}) "
                            "(<0.5 MWh) in every overlapping vintage — the two EIA "
                            "plants are one eGRID plant (nyiso-186)"
                        ),
                    }
                )
    return pd.DataFrame(
        rows,
        columns=[
            "plant_id",
            "egrid_orispl",
            "heat_rate_mmbtu_mwh",
            "n_vintages",
            "vintages",
            "per_vintage_hr",
            "loyo_min",
            "loyo_max",
            "source",
        ],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="NYISO", choices=sorted(ISO_SCOPE))
    ap.add_argument(
        "--check",
        action="store_true",
        help="re-derive and byte-compare against the committed artifact",
    )
    args = ap.parse_args()
    df = derive(args.iso)
    out = OUT_DIR / f"egrid_identity_heat_rates_{args.iso}.csv"
    text = df.to_csv(index=False)
    if args.check:
        if not out.exists():
            print(f"CHECK FAIL: {out} does not exist")
            return 1
        if out.read_text() != text:
            print(f"CHECK FAIL: {out} does not reproduce")
            return 1
        print(f"CHECK OK: {out} reproduces byte-identically ({len(df)} row(s))")
        return 0
    out.write_text(text)
    print(f"wrote {out} ({len(df)} row(s))")
    for r in df.itertuples():
        print(
            f"  {r.plant_id} <-> eGRID {r.egrid_orispl}: {r.heat_rate_mmbtu_mwh} "
            f"MMBtu/MWh over {r.n_vintages} vintage(s) [{r.vintages}] "
            f"LOYO [{r.loyo_min}, {r.loyo_max}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
