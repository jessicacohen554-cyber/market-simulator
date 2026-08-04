#!/usr/bin/env python
"""Derive CAISO's fleet-average VRE accreditation from the published NQC report.

**What this produces.** One class-average accreditation factor per month for
``solar`` and ``wind`` — the firm fraction of nameplate CAISO's OWN resource
adequacy ledger counts, on the CPUC/CAISO Net Qualifying Capacity basis. The
output is the reviewable digitized artifact that
:data:`market_sim.config.constants.RENEWABLE_NQC_CURVES_BY_ISO` cites and that
``tests/unit/data/test_caiso_nqc_class_factors.py`` reconciles the registry
literals against (the same digitize-then-reconcile discipline the PJM / MISO /
NYISO ELCC curves already follow).

**Why it has to be derived rather than read off.** CAISO publishes the
accreditation as a per-(technology, region) monthly *technology factor* — Solar
Fixed / Solar Tracking / Solar Thermal x Norcal / Socal, and Wind x Norcal /
Socal / AZ / NM / WA-OR — while the model carries ONE ``solar`` class and ONE
``wind`` class ISO-wide. Collapsing the published sub-class ratings onto the
model's classes needs the fleet's MW mix across those sub-classes, and that mix
is in the SAME document: the NQC List's per-resource monthly NQC MW. So this is
same-document arithmetic (the construction PJM's blended solar rating already
uses), not an outside weighting.

**How the mix is recovered.** CAISO does not publish Pmax in the NQC report, but
it publishes NQC and the factor, and ``NQC_r(m) = Pmax_r x factor_class(r)(m)``
holds exactly. Each non-dispatchable resource's 12-month NQC vector is therefore
a scalar multiple of exactly one published profile; least-squares against every
profile recovers both the resource's class (the best-fitting profile) and its
Pmax (the fitted scale). Matches are kept only at a relative residual below
``_MATCH_TOL``, so a resource whose vector is NOT a clean multiple of a published
profile (hybrids, partially-deliverable and capped resources) is DROPPED rather
than assigned a guessed class.

Two published quirks the fit has to respect, both verified against the raw rows:

* the ``0.1`` entries in the solar tables are a 0.1 **MW** floor on the NQC, not
  a 0.1 factor (a 20 MW solar resource posts ``0.1``, not ``2.0``), so those
  months are excluded from the fit;
* Energy-Only resources post zero NQC in every month. They are excluded too:
  their zero is a DELIVERABILITY outcome, not an accreditation factor, and the
  model prices deliverability separately (``capacity_deliverability_limits``).

**Rule 23 [R-FROZEN-DERIVE].** This script re-derives ONLY when its source data
updates — i.e. when CAISO publishes a new compliance-year NQC report and that
workbook is intaken under ``data/raw/capacity-market/nqc/caiso/``. It must NEVER
be re-run, re-parameterised or re-pointed because a model residual moved. There
is no free parameter here to move: every number out is a published factor times
a published MW.

**Rule 13 [R-MEASURED].** The output is a published market-design input that
regenerates for a forward year (CAISO publishes the report annually, ahead of
the compliance year) and responds to changed conditions (the exceedance factors
are re-derived from a rolling production window; the mix moves as the fleet
builds). It is not an outcome and nothing in it is fitted to the model.

Usage::

    uv run python scripts/data/derive_caiso_nqc_class_factors.py
    uv run python scripts/data/derive_caiso_nqc_class_factors.py \\
        --workbook data/raw/capacity-market/nqc/caiso/<newer>.xlsx --year 2027
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.paths import RAW_DIR  # noqa: E402

logger = logging.getLogger(__name__)

NQC_DIR: Path = RAW_DIR / "capacity-market" / "nqc" / "caiso"
DEFAULT_WORKBOOK: Path = NQC_DIR / "net-qualifying-capacity-report-cy2026.xlsx"
DEFAULT_YEAR: int = 2026
OUT: Path = NQC_DIR / "caiso_nqc_class_factors.csv"

MONTHS: tuple[str, ...] = (
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
)

# CAISO's own peak-risk months. The registry takes the MINIMUM published factor
# over these three, so the accredited credit holds in whichever of them the
# model's annual peak lands in — the identical selection rule
# HYDRO_ACCREDITATION_CREDIT_BY_ISO["CAISO"] already applies to the
# non-dispatchable hydro factor from this same tab (FFR-1C).
PEAK_RISK_MONTHS: tuple[str, ...] = ("JUL", "AUG", "SEP")

# Cell coordinates of each published technology-factor block on the
# "<year> Tech Factors" tab. (row0, column) of the first month's value; each
# block runs 12 rows. Stable across the CY2025 / CY2026 / CY2027-draft
# vintages (verified); a future layout change fails loudly in _read_profiles.
_SOLAR_ROW0, _WIND_ROW0 = 6, 21
_PROFILE_CELLS: dict[str, tuple[int, int]] = {
    "solar_fixed_norcal": (_SOLAR_ROW0, 1),
    "solar_fixed_socal": (_SOLAR_ROW0, 2),
    "solar_tracking_norcal": (_SOLAR_ROW0, 5),
    "solar_tracking_socal": (_SOLAR_ROW0, 6),
    "solar_thermal_socal": (_SOLAR_ROW0, 9),
    "wind_norcal": (_WIND_ROW0, 1),
    "wind_socal": (_WIND_ROW0, 2),
    "wind_az": (_WIND_ROW0, 3),
    "wind_nm": (_WIND_ROW0, 4),
    "wind_waor": (_WIND_ROW0, 5),
    # The three-year-average column of the production-based blocks. Not blended
    # into a model class here (the model accredits hydro through
    # HYDRO_ACCREDITATION_CREDIT_BY_ISO and does not carry geothermal/cogen/
    # biomass VRE classes), but carried as fit candidates so a hydro or biomass
    # resource cannot be mis-assigned to a solar or wind class.
    "hydro_nondispatchable": (36, 4),
    "geothermal": (51, 4),
    "cogeneration": (66, 4),
    "biomass": (81, 4),
}

# Sub-classes that roll up into each model class. The out-of-state wind
# geographies (AZ / NM / WA-OR) are DELIBERATELY excluded from the model's
# `wind` class: they accredit imported wind, which the model represents at the
# WECC_import node and credits through ADEQUACY_EXTERNAL_TIE_FIRM_MW, not
# through the in-ISO wind pool. Including them would double-count the seam
# (the _firm_import_mw discipline).
_MODEL_CLASS_MEMBERS: dict[str, tuple[str, ...]] = {
    "solar": (
        "solar_fixed_norcal",
        "solar_fixed_socal",
        "solar_tracking_norcal",
        "solar_tracking_socal",
        "solar_thermal_socal",
    ),
    "wind": ("wind_norcal", "wind_socal"),
}

# The published 0.1 entries in the solar tables are a 0.1 MW NQC floor, not a
# factor (verified: a 20 MW tracking resource posts 0.1, not 2.0). Months whose
# published value is exactly this sentinel carry no factor information and are
# excluded from the profile fit.
_FLOOR_SENTINEL: float = 0.1

# Relative residual below which a resource's NQC vector is accepted as a clean
# scalar multiple of one published profile. Clean matches land at ~1e-3; the
# next-best population sits above 0.03, so the threshold is not a knife edge.
_MATCH_TOL: float = 0.02

# A resource whose largest monthly NQC is at or below the floor is Energy-Only
# (or unqualified) and carries no accreditation information.
_MIN_NQC_MW: float = 0.11


def _read_profiles(workbook: Path, year: int) -> dict[str, np.ndarray]:
    """Published (technology, region) monthly factor vectors from the workbook.

    Returns one 12-element array per entry of :data:`_PROFILE_CELLS`, read at
    the fixed block coordinates. Raises ``ValueError`` if any block does not
    parse as twelve finite numbers, so a layout change in a future vintage
    fails loudly instead of silently producing a wrong blend.
    """
    tab = pd.ExcelFile(workbook).parse(f"{year} Tech Factors", header=None)
    profiles: dict[str, np.ndarray] = {}
    for name, (row0, col) in _PROFILE_CELLS.items():
        try:
            vec = np.array(
                [float(tab.iloc[row0 + i, col]) for i in range(12)], dtype=float
            )
        except (TypeError, ValueError, IndexError) as exc:  # pragma: no cover
            raise ValueError(
                f"{workbook.name}: technology-factor block {name!r} did not parse "
                f"at (row {row0}, col {col}) — the tab layout changed"
            ) from exc
        if not np.all(np.isfinite(vec)) or np.all(vec <= 0.0):
            raise ValueError(f"{workbook.name}: block {name!r} is empty or non-finite")
        profiles[name] = vec
    return profiles


def _classify(
    nqc: np.ndarray, profiles: dict[str, np.ndarray]
) -> tuple[str, float, float]:
    """Best-fitting published profile for one resource's 12-month NQC vector.

    Returns ``(class_name, relative_residual, fitted_pmax_mw)``. The fit is a
    one-parameter least squares (the scale IS the Pmax) over the months whose
    published factor is not the 0.1 MW floor sentinel.
    """
    best = ("unmatched", float("inf"), 0.0)
    for name, factor in profiles.items():
        keep = np.abs(factor - _FLOOR_SENTINEL) > 1e-9
        if keep.sum() < 4:
            continue
        y, f = nqc[keep], factor[keep]
        scale = float(y @ f / (f @ f))
        if scale <= 0.0:
            continue
        resid = float(np.linalg.norm(y - scale * f) / np.linalg.norm(y))
        if resid < best[1]:
            best = (name, resid, scale)
    return best


def derive(workbook: Path, year: int) -> pd.DataFrame:
    """Fleet-weighted monthly accreditation factor per model VRE class.

    One row per (model class, month) carrying the blended factor, the matched
    nameplate it is weighted over, and the sub-class mix behind it, so a
    reviewer can reproduce the blend from the published tables by hand.
    """
    profiles = _read_profiles(workbook, year)
    rows = pd.ExcelFile(workbook).parse(f"{year} NQC List", header=0)
    rows.columns = [str(c).strip() for c in rows.columns]
    nondisp = rows[rows["Dispatchable"].astype(str).str.strip().str.upper() == "N"]
    values = nondisp[list(MONTHS)].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    matched: dict[str, float] = {}
    counts: dict[str, int] = {}
    for vec in values.to_numpy(dtype=float):
        if vec.max() <= _MIN_NQC_MW:
            continue  # Energy-Only / unqualified: a deliverability zero.
        name, resid, pmax = _classify(vec, profiles)
        if resid >= _MATCH_TOL or pmax <= 0.0:
            continue
        matched[name] = matched.get(name, 0.0) + pmax
        counts[name] = counts.get(name, 0) + 1

    out: list[dict[str, object]] = []
    for model_class, members in _MODEL_CLASS_MEMBERS.items():
        weights = {m: matched.get(m, 0.0) for m in members if matched.get(m, 0.0) > 0.0}
        total_mw = sum(weights.values())
        if total_mw <= 0.0:
            raise ValueError(
                f"{workbook.name}: no resource matched any {model_class} sub-class"
            )
        mix = "; ".join(f"{m}={weights[m]:.1f}MW" for m in sorted(weights))
        for i, month in enumerate(MONTHS):
            blended = sum(w * profiles[m][i] for m, w in weights.items()) / total_mw
            out.append(
                {
                    "iso": "CAISO",
                    "model_class": model_class,
                    "compliance_year": year,
                    "month": month,
                    "class_average_factor": round(blended, 6),
                    "matched_nameplate_mw": round(total_mw, 1),
                    "n_resources": sum(counts.get(m, 0) for m in weights),
                    "subclass_mix_mw": mix,
                }
            )
    return pd.DataFrame(out)


def main(argv: list[str] | None = None) -> int:
    """Derive the CAISO NQC class factors and write the review CSV."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    table = derive(args.workbook, args.year)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)
    logger.info("wrote %s (%d rows)", args.out, len(table))

    for model_class in _MODEL_CLASS_MEMBERS:
        sub = table[table["model_class"] == model_class].set_index("month")
        peak = sub.loc[list(PEAK_RISK_MONTHS), "class_average_factor"]
        binding = peak.idxmin()
        logger.info(
            "%s: peak-risk months %s -> registry value %.4f (%s), "
            "matched nameplate %.1f MW over %d resources",
            model_class,
            {m: round(float(peak[m]), 4) for m in PEAK_RISK_MONTHS},
            float(peak.min()),
            binding,
            float(sub["matched_nameplate_mw"].iloc[0]),
            int(sub["n_resources"].iloc[0]),
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
