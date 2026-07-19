"""Shared EIA-930 benchmark semantics for the calibration dashboard (stdlib-only).

The renderer (``render_calibration_html``) and the scorer (``calibration_verdict``)
must agree on how the actual fossil benchmark is built from EIA-930 + EIA-923:
which classes make up the gas/coal families, the combined-fossil vintage
reconcile deadband, which balancing authorities have a corrupted "Natural Gas"
cell, and how much geothermal+biomass a BA folds into that cell. Those facts used
to live in the renderer and be **mirrored by comment** in the scorer (two copies
that could silently drift). This module is the single home; both import it.

STDLIB-ONLY: ``calibration_verdict`` is deliberately numpy-free and the Pages
deploy runs on a bare ``python3``. The gas/coal class tuples are therefore
hard-coded here rather than derived from ``market_sim.config.plant_taxonomy``;
``tests/test_benchmark_semantics.py`` asserts they still equal the live taxonomy
roll-up, so a taxonomy change that isn't mirrored here fails CI (previously the
scorer's hard-coded copy could drift from the renderer's taxonomy-derived one
with nothing to catch it).
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Gas / coal family membership (plant_taxonomy.classes_for_fuel930 roll-up)
# --------------------------------------------------------------------------- #
# The exact tuples ``classes_for_fuel930("gas")`` / ``("coal")`` return (drift
# guarded by tests/test_benchmark_semantics.py). Order is irrelevant to every
# consumer — they are used only in family sums and set-membership — but it is
# kept equal to the taxonomy so the renderer's ``_GAS_GROUPS``/``_COAL_GROUPS``
# stay byte-identical.
GAS_CLASSES: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
)
COAL_CLASSES: tuple[str, ...] = (
    "COAL",
    "COAL_LIGNITE",
    "COAL_PRB",
    "COAL_BIT",
    "COAL_WC",
)

# The mixed gas-thermal reconciliation bucket (data.fleet.OTHER_FOSSIL_CLASS).
# EIA-930 books it under "Natural Gas", so it joins the gas family that
# reconciles to the EIA-930 grid total (else its 923 generation double-counts).
# It stays excluded from the per-class merit GATE (calibration_verdict.
# FUELMIX_EXCLUDED) — a scoring choice, separate from this reconciliation.
OTHER_FOSSIL: str = "OTHER_FOSSIL"

# The gas/coal groups the combined-fossil reconcile scales as one family
# (render_calibration_html._GAS_GROUPS / _COAL_GROUPS).
GAS_GROUPS: tuple[str, ...] = (*GAS_CLASSES, OTHER_FOSSIL)
COAL_GROUPS: tuple[str, ...] = COAL_CLASSES


# --------------------------------------------------------------------------- #
# Combined-fossil vintage reconcile deadband
# --------------------------------------------------------------------------- #
# Half-width ~3% deadband: the COMBINED fossil (gas + coal) grid-delivered
# EIA-923 total is reconciled to the complete EIA-930 grid series in BOTH
# directions, every fossil class scaling by the SAME factor so the CEMS-validated
# gas/coal SPLIT is preserved (the reconcile corrects the fossil LEVEL, never the
# split). A total already within this fraction of the grid series is left
# byte-identical (well-measured vintages unchanged; offsetting per-family misses
# that net in-band left alone). See render_calibration_html.reconcile_vintage_classes.
VINTAGE_RECONCILE_FRAC: float = 0.97


# --------------------------------------------------------------------------- #
# EIA-930 "Natural Gas" cell corruption / fold-in
# --------------------------------------------------------------------------- #
# LEGACY FALLBACK ONLY. Balancing authorities whose EIA-930 "Natural Gas" (NG:NG)
# aggregate silently folds in geothermal + biomass, used ONLY when a bundle
# predates the EIA-930 "Other Fuel Sources" (NG:OTH) series (not re-extracted),
# to keep already-committed bundles byte-identical. Re-extracting a bundle's
# eia930 parquet retires its dependence on this set (the general
# :func:`gas_foldin_deflation` then subtracts only the genuinely-folded portion).
EIA930_GAS_FOLDS_GEO_BIOMASS: frozenset[str] = frozenset({"CAISO"})

# BAs whose EIA-930 "Natural Gas" cell is demonstrably CORRUPTED against two
# independent measured sources (CEMS hourly + EIA-923), so the combined vintage
# reconcile must be CAPPED at a CEMS-anchored fossil total instead of scaling
# classFull up to the 930 cell. CAISO: from ~2024-05 the CISO NG cell carries a
# growing noon-peaked, solar-shaped block no gas fleet produced. Owner-signed
# rework 2026-07-12; results/calibration/
# FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md §3/§5. The anchor fields
# (``gas_cems_grid``/``gas_cogen_grid``/``fossil_cems_grid``) are written into the
# bench part's ``e930`` dict by the render (sole writer); other ISOs carry no
# anchor and are unchanged. (calibration_verdict names these CEMS_GAS_ANCHOR_*.)
EIA930_NG_CELL_CORRUPT: frozenset[str] = frozenset({"CAISO"})

# First VINTAGE year the corruption contaminates (CISO onset ~2024-05): the
# hourly gas actual (fuelRows / C4) switches to the CEMS+cogen basis from this
# vintage; earlier years keep 930 for continuity — the two agree pre-onset.
EIA930_NG_CORRUPT_ONSET: dict[str, int] = {"CAISO": 2024}


def gas_foldin_deflation(classfull: dict, e930: dict, iso: str) -> float:
    """TWh of geothermal+biomass a BA folded into its EIA-930 "Natural Gas" cell.

    Subtract this from the EIA-930 gas reconcile target so the gas classes don't
    scale to gas+geo+biomass. Two regimes:

    * **Re-extracted bundle** (carries the EIA-930 ``other`` = "Other Fuel
      Sources" series): the folded amount is the model's clean OTHER (geothermal)
      + biomass actuals MINUS what the BA correctly reported in its own Other
      series — only the part that *leaked* into NG. ``max(0, ...)`` self-zeroes a
      clean BA and yields the full model other+biomass for a total-fold BA.
    * **Legacy bundle** (no ``other`` series): fall back to the per-ISO
      :data:`EIA930_GAS_FOLDS_GEO_BIOMASS` allowlist. Coal never folds.
    """
    model_other_bio = float(classfull.get("OTHER", 0.0)) + float(
        classfull.get("biomass", 0.0)
    )
    if "other" in e930:
        return max(0.0, model_other_bio - float(e930.get("other", 0.0)))
    return model_other_bio if iso in EIA930_GAS_FOLDS_GEO_BIOMASS else 0.0
