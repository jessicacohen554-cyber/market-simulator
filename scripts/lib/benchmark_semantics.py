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

# The liquid-petroleum class, and the THIRD member of the reconcile family
# (nyiso-239, 2026-09-16). EIA-923 books a plant's generation under the fuel it
# BURNED, so `_classify_f923` routes every DFO / RFO / JF / KER / WO / PC row to
# `oil` — while a dual-fuel plant's CC/CT/ST MWh stay in the gas classes. EIA-930
# books the SAME generation hour by hour under `NG: OIL`. Comparing the 923 gas
# classes against the 930 `gas` cell alone therefore straddles a fuel boundary,
# and in a year with a material oil-labelled block it reads a false LEVEL error:
# NYISO 2022 reads +5.13 % on the gas-only basis and +0.08 % with oil on both
# sides, so the reconcile fired and deflated every NYISO fossil class by
# x0.951167 — 1.62 TWh of it on `CC_REGULAR`, which is the whole of that year's
# C1 band breach. This is the same failure mode the reconcile ALREADY refuses to
# propagate one fuel over: its docstring declines to force EIA-930's coal/gas
# attribution onto the 923 split because that attribution is unreliable against
# CAMPD. Evidence, four independent arbiters and the cross-ISO census:
# docs/FINDING-nyiso239-c1-2022-bench-oil-attribution-2026-09-16.md.
OIL_GROUPS: tuple[str, ...] = ("oil",)


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

# BAs whose EIA-930 "Natural Gas" cell is MEASURED NOT to fold in the 923
# OTHER + biomass that is absent from the BA's own "Other" series, so
# :func:`gas_foldin_deflation` must return 0 for them. The deflation's premise
# ("923 other+biomass not in 930 Other leaked into NG") is a hypothesis about
# WHERE that energy sits in 930; it can also sit nowhere in 930 at all —
# behind-the-meter mill self-generation the BA never meters. The two are told
# apart by the gas cell itself: a fold of F TWh makes 930 gas exceed the 923 gas
# classes by ~F.
#
# SOCO (lane SOCO-60, 2026-09-23, rule 25 — SOCO's own data only; probe
# scripts/probes/_soco60b_phase0.py): the deflation would subtract 6.35 TWh
# (2024; 923 biomass 9.30 + OTHER -0.48 - 930 Other 2.48), i.e. assert 930 gas
# holds 6.35 TWh of biomass. Measured, 930 SOCO gas vs the 923 gas classes of
# the plants in the SOCO BA (FULL, CHP host steam included) is 125.06/127.88,
# 125.88/126.08, 120.99/121.89, 130.64/130.96, 129.59/130.23, 126.08/129.54 TWh
# in 2019-2024 — 930 gas is AT OR BELOW 923 gas in every year, so there is no
# room for any fold, let alone 6-7 TWh. SOCO's 923 biomass is 82 % / 84 %
# CHP-flagged (2023 / 2024) and 60 % black liquor (BLQ 5.14 / 5.56 of 8.82 /
# 9.32 TWh) — pulp-mill recovery-boiler generation the BA does not meter. Applying the
# deflation fired the combined reconcile at x0.956 (2024) on every SOCO fossil
# class — coal included, where 930 and 923 agree to 0.7 %. Benchmark-only:
# no solve reads this.
EIA930_GAS_FOLD_REFUTED: frozenset[str] = frozenset({"SOCO"})

# First VINTAGE year the corruption contaminates: the hourly gas actual
# (fuelRows / C4) switches to the CEMS+cogen basis from this vintage; earlier
# years keep 930.
#
# CAISO 2024 -> 2023 (owner ruling 2026-07-26, caiso-121; evidence
# results/calibration/FINDING-caiso115-c4-freshlook-and-separability-2026-07-23.md
# §"2023 fail is a BENCHMARK-BASIS artifact" + the caiso-121 three-source level
# test). The original 2024 onset kept 2023 on the 930 cell "for continuity — the
# two agree pre-onset"; they do not. On the SAME two independent measured
# sources that condemned the cell for 2024+ (FINDING-caiso-c2c4-bench-basis-
# 930ng-2026-07-12.md §5.2), CAISO 2023 grid gas is EIA-923 67.20 TWh and CAMPD
# CEMS + non-CEMS cogen 68.74 TWh — agreeing within 2.3% — while the
# fold-in-deflated 930 NG cell reads 74.23 TWh: +10.5% over 923, +8.0% over
# CEMS, far outside the 3% VINTAGE_RECONCILE_FRAC deadband. Deflated-930 over
# EIA-923 runs +10.5% (2023) -> +21.1% (2024) -> +32.8% (2025), so the
# contamination is a monotone ramp and any onset year is a threshold on a
# continuum, not a step at 2024-05.
EIA930_NG_CORRUPT_ONSET: dict[str, int] = {"CAISO": 2023}


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

    A BA in :data:`EIA930_GAS_FOLD_REFUTED` returns 0: its gas cell is measured
    not to carry the fold (SOCO-60).
    """
    if iso in EIA930_GAS_FOLD_REFUTED:
        return 0.0
    model_other_bio = float(classfull.get("OTHER", 0.0)) + float(
        classfull.get("biomass", 0.0)
    )
    if "other" in e930:
        return max(0.0, model_other_bio - float(e930.get("other", 0.0)))
    return model_other_bio if iso in EIA930_GAS_FOLDS_GEO_BIOMASS else 0.0
