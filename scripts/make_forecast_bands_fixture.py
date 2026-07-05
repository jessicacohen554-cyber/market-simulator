"""Build a hand-crafted, schema-correct fixture for the forecast-bands demo (PB-4).

PB-5 (the first production ERCOT ensemble run) has not run yet -- this session
runs no solves at all (rule 22 / task instructions). Until PB-5 lands, the fan
chart page (``docs/codebase-site/forecast-bands.html``) is demoed against a
small, clearly-labelled synthetic fixture instead: schema-correct
``bands.parquet`` / ``ensemble_meta.json`` (PB-2's frozen §4.1 contract) and
``matrix.parquet`` / ``envelope.parquet`` / ``meta.json`` (PB-0's), built here
with fabricated numbers, then run through the REAL exporter
(``scripts/export_forecast_bands.py``) exactly as a genuine run would be.

No solves, no real data -- every number below is invented for demo shape only.
``ensemble_meta.json["synthetic"] = true`` is what drives the page's
"SYNTHETIC FIXTURE" banner; never unset it on a real export.

Usage:
    python scripts/make_forecast_bands_fixture.py [--out-root results/ensemble]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent

ENSEMBLE_ID = "synthetic-fixture-ercot-v1"
MATRIX_ID = "synthetic-fixture-ercot-matrix-v1"
YEARS = list(range(2026, 2051))
N_DRAWS = 24
SEED = 7

# The plan §1.2 13 named cases, given a fabricated but monotone emissions
# spread (Mt CO2, 2026 anchor ~140, corners bound the envelope) so the fan
# chart's dashed envelope and thin case lines have a plausible shape.
CASE_2026_LEVEL = {
    "REF": 140.0,
    "GAS-LO": 148.0,
    "GAS-HI": 132.0,
    "LOAD-LO": 134.0,
    "LOAD-HI": 146.0,
    "POL-TIGHT": 128.0,
    "POL-ROLLBACK": 150.0,
    "TECH-LO": 144.0,
    "TECH-HI": 136.0,
    "RET-FAST": 130.0,
    "RET-SLOW": 146.0,
    "CORNER-HI-EMIT": 158.0,
    "CORNER-LO-EMIT": 118.0,
}
# Fabricated per-case linear drift by 2050 (Mt/yr), spanning a plausible
# decarbonization range; corners drift furthest apart.
CASE_DRIFT = {
    "REF": -1.8,
    "GAS-LO": -1.2,
    "GAS-HI": -2.1,
    "LOAD-LO": -2.4,
    "LOAD-HI": -1.0,
    "POL-TIGHT": -3.2,
    "POL-ROLLBACK": -0.3,
    "TECH-LO": -1.0,
    "TECH-HI": -2.6,
    "RET-FAST": -2.8,
    "RET-SLOW": -0.9,
    "CORNER-HI-EMIT": 0.2,
    "CORNER-LO-EMIT": -4.0,
}


def _build_matrix_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fabricate matrix.parquet + envelope.parquet rows for the 13 named cases."""
    rows = []
    for case, level0 in CASE_2026_LEVEL.items():
        drift = CASE_DRIFT[case]
        for year in YEARS:
            t = year - YEARS[0]
            emissions = max(0.0, level0 + drift * t)
            rows.append(
                {
                    "case": case,
                    "year": year,
                    "emissions_mt": round(emissions, 3),
                    "cache_key": "synthetic",
                    "label": "deterministic scenario range -- NOT a probability band",
                }
            )
    matrix_df = pd.DataFrame(rows)

    env_rows = []
    for year, group in matrix_df.groupby("year"):
        min_row = group.loc[group["emissions_mt"].idxmin()]
        max_row = group.loc[group["emissions_mt"].idxmax()]
        env_rows.append(
            {
                "year": int(year),
                "min_mt": float(min_row["emissions_mt"]),
                "min_case": str(min_row["case"]),
                "max_mt": float(max_row["emissions_mt"]),
                "max_case": str(max_row["case"]),
                "label": "deterministic scenario range -- NOT a probability band",
            }
        )
    envelope_df = pd.DataFrame(env_rows).sort_values("year").reset_index(drop=True)
    return matrix_df, envelope_df


def _build_bands_frame() -> pd.DataFrame:
    """Fabricate parametric-layer bands.parquet rows (no structural layer yet).

    The published PB-3 structural layer (``parametric_plus_structural``) is a
    parallel in-flight change -- this fixture deliberately omits it so the
    exporter's "missing layer" path is exercised for real, not just in unit
    tests: this fixture *is* the "layer absent" case.
    """
    rows = []
    for year in YEARS:
        t = year - YEARS[0]
        center = CASE_2026_LEVEL["REF"] + CASE_DRIFT["REF"] * t
        # Spread widens with horizon, loosely tracking the matrix envelope so
        # the parametric fan sits plausibly inside the deterministic range.
        spread = 6.0 + 0.35 * t
        p10 = max(0.0, center - spread)
        p90 = center + spread
        boot_jitter = 0.4 + 0.02 * t
        for q, val in ((0.1, p10), (0.5, center), (0.9, p90)):
            rows.append(
                {
                    "year": year,
                    "metric": "emissions_mt",
                    "layer": "parametric",
                    "quantile": q,
                    "value": round(float(val), 3),
                    "n": N_DRAWS,
                    "bootstrap_lo": round(float(val - boot_jitter), 3),
                    "bootstrap_hi": round(float(val + boot_jitter), 3),
                }
            )
    return pd.DataFrame(rows)


def _build_ensemble_meta() -> dict:
    return {
        "iso": "ERCOT",
        "base_config": {
            "mode": "forecast",
            "iso": "ercot",
            "note": "synthetic fixture -- no real base config",
        },
        "spec": {
            "n": N_DRAWS,
            "seed": SEED,
            "note": "fabricated for PB-4 demo, not a real UncertaintySpec",
        },
        "sampler": {"n": N_DRAWS, "seed": SEED},
        "members": {f"draw-{i:04d}": "synthetic" for i in range(N_DRAWS)},
        "band_quantiles": [0.1, 0.5, 0.9],
        "layers_present": ["parametric"],
        "quantile_estimator": (
            "numpy Hyndman-Fan type 7 (method='linear'); n reported per quantile; "
            "bootstrap 90% CI, 1000 resamples (plan §2.4) -- FABRICATED for this fixture"
        ),
        "label": (
            "parametric probability band (PB-2); dispatch-conditional -- excludes "
            "the structural-error prior (PB-3) and the deterministic scenario "
            "envelope (PB-0), and excludes fleet-path structural error until PP-0.3"
        ),
        "synthetic": True,
        "note": (
            "Hand-built fixture for the PB-4 forecast-bands demo "
            "(scripts/make_forecast_bands_fixture.py). No solves were run; every "
            "number is fabricated for display shape only. Never treat as a real "
            "calibration or forecast result."
        ),
    }


def _build_matrix_meta(matrix_df: pd.DataFrame) -> dict:
    return {
        "matrix_id": MATRIX_ID,
        "iso": "ERCOT",
        "label": "deterministic scenario range -- NOT a probability band",
        "matrix_path": "synthetic-fixture (scripts/make_forecast_bands_fixture.py)",
        "cases": {case: "synthetic" for case in CASE_2026_LEVEL},
        "base_config": {
            "mode": "forecast",
            "iso": "ercot",
            "note": "synthetic fixture -- no real base config",
        },
        "years_present": sorted(int(y) for y in matrix_df["year"].unique()),
        "synthetic": True,
    }


def build(out_root) -> tuple[Path, Path]:
    """Write the ensemble dir and matrix dir fixtures under ``out_root``.

    Returns:
        ``(ensemble_dir, matrix_dir)`` paths written.
    """
    out_root = Path(out_root)
    ensemble_dir = out_root / ENSEMBLE_ID
    matrix_dir = out_root / MATRIX_ID
    ensemble_dir.mkdir(parents=True, exist_ok=True)
    matrix_dir.mkdir(parents=True, exist_ok=True)

    _build_bands_frame().to_parquet(ensemble_dir / "bands.parquet", index=False)
    (ensemble_dir / "ensemble_meta.json").write_text(
        json.dumps(_build_ensemble_meta(), indent=2, sort_keys=True) + "\n"
    )

    matrix_df, envelope_df = _build_matrix_frames()
    matrix_df.to_parquet(matrix_dir / "matrix.parquet", index=False)
    envelope_df.to_parquet(matrix_dir / "envelope.parquet", index=False)
    (matrix_dir / "meta.json").write_text(
        json.dumps(_build_matrix_meta(matrix_df), indent=2, sort_keys=True) + "\n"
    )

    return ensemble_dir, matrix_dir


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-root", default=str(REPO / "results" / "ensemble"))
    args = ap.parse_args()
    ensemble_dir, matrix_dir = build(args.out_root)
    print(f"ensemble_dir: {ensemble_dir}")
    print(f"matrix_dir: {matrix_dir}")


if __name__ == "__main__":
    main()
