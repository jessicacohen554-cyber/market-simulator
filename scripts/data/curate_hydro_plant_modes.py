"""Curate per-plant conventional-hydro operational modes (RoR-split classifier).

Builds the ``hydro-plant-modes`` clean datatype: one row per (iso, EIA plant
id) with the binary ``shapeable`` classification the RoR-split dispatch
mechanism (``ScenarioConfig.hydro_ror_split``, caiso-126) consumes — True for
reservoir/peaking plants that can shape output within their monthly energy
budget, False for run-of-river/canal plants whose output follows inflow.

Sources (both committed under ``data/raw``, immutable):

* ``data/raw/ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx`` — the ORNL EHA
  FY2024 plant database. Its ``Mode`` field is the authoritative per-plant
  operational-mode label, keyed to the EIA plant id (``EIA_PtID``).
* ``data/raw/hilarri/HILARRI_v4.csv`` — ORNL HILARRI v4, the plant->dam->
  reservoir linkage table used ONLY to complete plants whose EHA ``Mode`` is
  NaN (100 of 201 CISO plants, 4.66 of ~6.7 GW; the FY2023 EHA vintage
  carries the identical gap, so no earlier vintage can complete it).

Classification rules, in order (every rule categorical — no numeric
threshold enters, so no free parameter; CLAUDE.md rules 13/24):

1. ``eha_mode`` — EHA ``Mode`` present: Peaking / Intermediate Peaking ->
   shapeable; Run-of-river / Canal/Conduit -> not shapeable. Hybrid national
   labels (Run-of-river/Peaking, Run-of-river/Upstream Peaking,
   Reregulating) -> not shapeable: EHA lists the plant's own hydraulic mode
   first, and a reregulating/RoR powerhouse cannot chase price whatever its
   upstream neighbours do. ``Unknown`` falls through to the completion.
   (None of the hybrid labels occurs in CISO.)
2. ``hilarri_canal`` — Mode-NaN and any HILARRI ``prjct_type`` for the plant
   contains canal/conduit: not shapeable. A conduit plant generates on water
   delivered for another purpose (irrigation/municipal aqueduct flow) — the
   same physics as EHA's own Canal/Conduit label.
3. ``corps_dam`` — Mode-NaN and the EHA ``Dam_Own`` names the U.S. Army
   Corps of Engineers (district codes ``CESP*`` — e.g. CESPK, Sacramento —
   or USACE/Corps spelled out): not shapeable. Releases at a Corps
   flood-control dam are scheduled by the Corps' water-control manual
   (flood-control + irrigation deliveries); the hydro operator is a
   release-taker, not a price-shaper (CISO: Pine Flat/KRCD and five small
   Corps projects).
4. ``hilarri_no_reservoir`` — Mode-NaN and NO HILARRI linkage row for the
   plant says "associated with reservoir": not shapeable. With no
   inventoried storage there is nothing to shape with.
5. ``hilarri_reservoir`` — Mode-NaN, reservoir-associated, operator-
   controlled dam: shapeable (the remaining case).

Validation (residual-blind, printed on every run): applying rules 2-5 to the
EHA-LABELED CISO subset (101 plants — pretending their Mode were unknown)
reproduces the label for 85/101 plants and 84 % of labeled MW. The
mis-classifications are concentrated in small (<30 MW) diversion-pond plants
EHA labels Run-of-river despite an inventoried reservoir (12 plants) and
pondage peakers whose forebay is not inventoried (4 plants, incl. Pit 5 /
Cresta). This skill check is against the EXTERNAL labels only — no model
residual enters the rule choice, and per rule 21 the rule re-derives only
when the EHA/HILARRI sources update.

Scope: DEFAULT_ISOS registers CAISO only. The completion rule was reviewed
against CAISO's labeled subset; another ISO's lane must run and review the
same validation for its BA before adding itself.

Usage:
  PYTHONPATH=.:src python scripts/data/curate_hydro_plant_modes.py [--iso CAISO]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from market_sim.data.fleet import ba_codes  # noqa: E402
from scripts.lib import clean_io  # noqa: E402

DATATYPE = "hydro-plant-modes"
# CAISO only: the completion rule's validation (module docstring) was reviewed
# on CAISO's labeled subset. Other ISOs opt in after their own review.
DEFAULT_ISOS: tuple[str, ...] = ("CAISO",)

EHA_XLSX = "ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx"
HILARRI_CSV = "hilarri/HILARRI_v4.csv"

# Rule 1: EHA Mode -> shapeable. Hybrids/reregulating are NOT shapeable (see
# module docstring); "Unknown" is deliberately absent so it falls through to
# the completion rules like NaN.
MODE_SHAPEABLE: dict[str, bool] = {
    "Peaking": True,
    "Intermediate Peaking": True,
    "Run-of-river": False,
    "Canal/Conduit": False,
    "Run-of-river/Peaking": False,
    "Run-of-river/Upstream Peaking": False,
    "Reregulating": False,
}

# Rule 3: Corps-district dam-owner markers (CESPK = Sacramento District etc.).
CORPS_DAM_PATTERN = r"CESP|USACE|Corps"

# HILARRI categorical markers (rules 2 and 4).
CANAL_PATTERN = r"conduit|canal"
RESERVOIR_PATTERN = r"associated with reservoir"


def _load_eha(raw_root: Path, ba_code: str) -> pd.DataFrame:
    """Return the EHA Operational rows for one balancing authority.

    Filters to conventional-hydro plants (``CH_MW`` > 0 — pure pumped-storage
    plants carry NaN CH_MW and are storage resources, not budget hydro) with
    an EIA plant id.
    """
    df = pd.read_excel(raw_root / EHA_XLSX, sheet_name="Operational")
    sub = df[(df["BACode"] == ba_code) & (df["CH_MW"] > 0)].copy()
    sub = sub[sub["EIA_PtID"].notna()]
    sub["EHA_PtID"] = sub["EHA_PtID"].astype(str)
    return sub


def _hilarri_flags(raw_root: Path, eha_ptids: pd.Series) -> pd.DataFrame:
    """Return per-EHA-plant HILARRI evidence flags (canal, reservoir).

    A plant can carry several HILARRI linkage rows (one per dam/reservoir);
    the flags aggregate over all of them: ``canal`` if ANY row's project type
    is canal/conduit, ``has_reservoir`` if ANY row's ``dataset`` says the
    plant/dam is associated with an inventoried reservoir.
    """
    hil = pd.read_csv(raw_root / HILARRI_CSV, dtype={"eha_ptid": str}, low_memory=False)
    sub = hil[hil["eha_ptid"].isin(set(eha_ptids))]
    flags = sub.groupby("eha_ptid").agg(
        canal=(
            "prjct_type",
            lambda s: s.astype(str).str.contains(CANAL_PATTERN, case=False).any(),
        ),
        has_reservoir=(
            "dataset",
            lambda s: s.astype(str).str.contains(RESERVOIR_PATTERN, case=False).any(),
        ),
    )
    return flags


def _classify(eha: pd.DataFrame, flags: pd.DataFrame) -> pd.DataFrame:
    """Apply the ordered classification rules to the EHA rows (module doc)."""
    df = eha.join(flags, on="EHA_PtID")
    df["canal"] = df["canal"].fillna(False).astype(bool)
    df["has_reservoir"] = df["has_reservoir"].fillna(False).astype(bool)
    corps = (
        df["Dam_Own"].astype(str).str.contains(CORPS_DAM_PATTERN, case=False, na=False)
    )

    known = df["Mode"].map(MODE_SHAPEABLE)
    completion = np.select(
        [df["canal"], corps, ~df["has_reservoir"]],
        [False, False, False],
        default=True,
    )
    method = np.select(
        [
            known.notna(),
            df["canal"],
            corps,
            ~df["has_reservoir"],
        ],
        ["eha_mode", "hilarri_canal", "corps_dam", "hilarri_no_reservoir"],
        default="hilarri_reservoir",
    )
    df["shapeable"] = known.where(known.notna(), pd.Series(completion, df.index))
    df["shapeable"] = df["shapeable"].astype(bool)
    df["method"] = method
    return df


def _validate_completion(df: pd.DataFrame) -> str:
    """Score the completion rules against the EHA-labeled subset (skill check).

    Residual-blind: compares the rules-2-to-5 prediction with the EXTERNAL
    EHA label on the plants that have one. Returned as a printable summary;
    never mutates the classification.
    """
    lab = df[df["Mode"].isin(MODE_SHAPEABLE)].copy()
    if lab.empty:
        return "completion validation: no labeled plants in scope"
    truth = lab["Mode"].map(MODE_SHAPEABLE).astype(bool)
    corps = (
        lab["Dam_Own"].astype(str).str.contains(CORPS_DAM_PATTERN, case=False, na=False)
    )
    pred = ~lab["canal"] & ~corps & lab["has_reservoir"]
    ok = pred == truth
    mw = lab["CH_MW"].to_numpy(dtype=float)
    return (
        f"completion validation vs EHA labels: {int(ok.sum())}/{len(lab)} plants, "
        f"{mw[ok].sum() / mw.sum():.1%} of labeled MW reproduced"
    )


def curate(
    raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> list[Path]:
    """Build and write the ``hydro-plant-modes`` clean partition per ISO.

    Args:
        raw_root: Root of the raw tree (defaults to ``paths.RAW_DIR``); tests
            point it at a fixture directory.
        isos: ISOs to curate (defaults to :data:`DEFAULT_ISOS`).

    Returns:
        The written clean-partition paths.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    written: list[Path] = []
    for iso in isos or DEFAULT_ISOS:
        codes = ba_codes(iso)
        if not codes:
            print(f"[skip] {iso}: no balancing-authority code mapping")
            continue
        # One EHA read per member BA (NWPP is seventeen; the 1:1 regions one).
        eha = pd.concat(
            [_load_eha(raw_root, code) for code in codes], ignore_index=True
        )
        if eha.empty:
            print(f"[skip] {iso}: no EHA conventional-hydro rows for {codes}")
            continue
        flags = _hilarri_flags(raw_root, eha["EHA_PtID"])
        cls = _classify(eha, flags)
        print(f"[{iso}] {_validate_completion(cls)}")

        # Aggregate to the EIA plant-id grain (a few EIA ids carry two EHA
        # plants, e.g. CISO 10253 Haypress/Lower Haypress): shapeable if ANY
        # constituent is (max-composition keeps a peaking unit shapeable
        # beside an RoR sibling); capacity sums; labels join.
        cls["plant_id"] = cls["EIA_PtID"].astype(int)
        rows = (
            cls.sort_values(["plant_id", "EHA_PtID"])
            .groupby("plant_id")
            .agg(
                eha_ptid=("EHA_PtID", "|".join),
                plant_name=("PtName", "first"),
                ch_mw=("CH_MW", "sum"),
                mode=("Mode", "first"),
                shapeable=("shapeable", "any"),
                method=("method", "first"),
                fc_dock=("FC_Dock", "first"),
                dam_own=("Dam_Own", "first"),
            )
            .reset_index()
        )
        rows.insert(0, "iso", iso.upper())
        # Schema dtypes are explicit, not inferred: the string columns can
        # arrive all-NaN (object/float) from a sparse source slice.
        rows["ch_mw"] = rows["ch_mw"].astype(float)
        for col in ("eha_ptid", "plant_name", "mode", "method", "fc_dock", "dam_own"):
            rows[col] = rows[col].astype(object).where(rows[col].notna(), None)
            rows[col] = rows[col].map(lambda v: None if v is None else str(v))
        n_ror = int((~rows["shapeable"]).sum())
        print(
            f"[{iso}] {len(rows)} plants ({rows['ch_mw'].sum():.0f} MW EHA CH): "
            f"{n_ror} run-of-river-class, {len(rows) - n_ror} reservoir-class; "
            f"methods {rows['method'].value_counts().to_dict()}"
        )
        path = clean_io.write_clean(
            rows,
            DATATYPE,
            iso=iso.upper(),
            year=None,
            source=f"{EHA_XLSX} + {HILARRI_CSV}",
        )
        clean_io.validate_clean(path)
        written.append(path)
        print(f"[{iso}] wrote {path}")
    return written


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--iso",
        nargs="+",
        default=None,
        help=f"ISOs to curate (default: {' '.join(DEFAULT_ISOS)})",
    )
    args = ap.parse_args()
    written = curate(isos=args.iso)
    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main())
