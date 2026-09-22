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

1. ``eha_mode`` — EHA ``Mode`` present: a label CONTAINING "Peaking" ->
   shapeable (Peaking, Intermediate Peaking, and — since the hydro-1
   HYBRID-LABEL REPAIR of 2026-09-20 — Run-of-river/Peaking and
   Run-of-river/Upstream Peaking); Run-of-river, Canal/Conduit and
   Reregulating -> not shapeable. ``Unknown`` falls through to the completion.
   The repair is forced by nyiso-111's ex-ante measurement and is
   BYTE-IDENTICAL FOR CAISO (zero hybrid-labelled CISO plants) — see
   ``MODE_SHAPEABLE`` for the falsification and the per-ISO effect.
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

Scope: DEFAULT_ISOS registers CAISO, PJM, NYISO, SPP, NEISO and MISO (the
last three reviewed by hydro-5 — see the constant). Another ISO's lane must
run and review the same validation for its BA before adding itself — the
printed ``completion validation`` line IS that review, scored on the target
BA's own labeled subset and never transferred (rule 25 ``[R-ISO-SCOPE]``).

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
# ISOs whose lane has run and reviewed the completion validation for its own
# BA (module docstring). CAISO first (caiso-126); PJM and NYISO added by
# hydro-1 (2026-09-20) alongside the HYBRID-LABEL REPAIR below.
#
# SPP, NEISO and MISO added by hydro-5 (2026-09-22), each reviewed on its OWN
# BA's labelled subset (rule 25; docs/PRECOMMIT-hydro-5-2026-09-22.md §2):
#   SPP   (SWPP) 12/16 plants, 92.3 % of labelled MW.
#   NEISO (ISNE) 77/125 plants, 66.1 % of labelled MW.
#   MISO  (MISO) 65/135 plants, 62.5 % of labelled MW.
# The NEISO / MISO aggregates are below CAISO's 84 %, and the review is why
# they are admitted anyway: the misses are ONE-SIDED. Labelled Run-of-river
# plants the completion calls shapeable (an inventoried reservoir behind a
# small diversion or navigation dam) are 317.9 MW / 37 plants at NEISO and
# 586.3 MW / 62 plants at MISO; the reverse error is 68.0 / 54.5 MW. So a
# completion "not shapeable" verdict is right on 81.8 % (NEISO) / 84.3 %
# (MISO) / 89.6 % (SPP) of the MW it covers, and the completion UNDER-applies
# the flat treatment rather than over-applying it. The CESP-only Corps
# pattern does not fire on SPP/MISO's SWPA-marketed Corps peaking projects
# (Keystone, Blakely Mountain, Degray), which is the correct outcome there —
# rule 3's release-taker premise is a Sacramento-District fact, not a Corps one.
DEFAULT_ISOS: tuple[str, ...] = ("CAISO", "PJM", "NYISO", "SPP", "NEISO", "MISO")

EHA_XLSX = "ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx"
HILARRI_CSV = "hilarri/HILARRI_v4.csv"

# Rule 1: EHA Mode -> shapeable. "Unknown" is deliberately absent so it falls
# through to the completion rules like NaN.
#
# HYBRID-LABEL REPAIR (hydro-1, 2026-09-20). The committed rule resolved every
# hybrid label -- "Run-of-river/Peaking", "Run-of-river/Upstream Peaking",
# "Reregulating" -- to NOT shapeable, on the argument that "EHA lists the
# plant's own hydraulic mode first". nyiso-111 FALSIFIED that argument by
# measurement on NYISO, ex ante and without a solve
# (results/calibration/_nyiso111_hydro_ror_split_screen.json): under the
# committed rule NYISO's shapeable set is 1,261.6 MW, while NYISO's OWN
# measured fleet swings 1,195.0 / 1,291.6 / 1,593.1 MW on the mean diurnal
# profile in 2023/24/25 and 1,496 / 1,495 / 1,929 MW on the MEDIAN day. A fleet
# cannot swing more than its shapeable capacity, so the hybrid resolution is
# wrong: those plants demonstrably shape. The repair applies the label as EHA
# writes it -- a plant whose label CONTAINS "Peaking" peaks -- and the
# run-of-river half of a hybrid label describes its INFLOW regime, which the
# monthly energy budget already carries.
#
# Rule 25 [R-ISO-SCOPE]: no fitted number crosses an ISO boundary here. What
# crosses is a categorical labelling rule, repaired against one ISO's measured
# falsification and applied uniformly.
#
# BYTE-IDENTICAL FOR CAISO, verified from the source rather than asserted:
# the EHA Operational sheet carries ZERO hybrid-labelled CISO plants
# (196 CISO conventional-hydro rows, 0 hybrid, 0.0 MW), so CAISO's partition
# is unchanged and its keeper cannot move. PJM moves 2 plants / 81.2 MW;
# NYISO moves 23 plants / 2,639.8 MW, which is the falsification above.
MODE_SHAPEABLE: dict[str, bool] = {
    "Peaking": True,
    "Intermediate Peaking": True,
    "Run-of-river/Peaking": True,  # hybrid: peaks (nyiso-111 falsification)
    "Run-of-river/Upstream Peaking": True,  # hybrid: peaks
    "Run-of-river": False,  # unambiguous: output follows inflow
    "Canal/Conduit": False,  # unambiguous: generates on delivered water
    # UNCHANGED at False, and deliberately NOT swept up in the repair: a
    # re-regulating powerhouse exists to ABSORB an upstream peaker's discharge
    # and pass steady flow downstream. Its label carries no "Peaking", and
    # smoothing is the opposite of shaping, so the committed resolution was
    # right for this one. NYISO 3 plants / 17.0 MW, PJM 1 plant / 51.2 MW.
    "Reregulating": False,
}

# The repair as a one-line predicate, for the docstring and the tests: a plant
# whose EHA label CONTAINS "Peaking" is shapeable; "Run-of-river",
# "Canal/Conduit" and "Reregulating" are not. Kept as data above rather than a
# regex so an unrecognised future label falls through to the completion rules
# instead of being silently classified by a substring match.

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
