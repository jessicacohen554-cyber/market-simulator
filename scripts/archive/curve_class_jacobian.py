"""Empirical cross-class offer-curve Jacobian from the calibration run history.

Every calibration bundle records the exact ``offer_curve_by_group`` its LP
solved against (``run_config.json``) plus the full per-class dispatch
(``dispatch/<year>_P1.parquet``). Across the run history those curves were
tuned band by band, so the history is a designed-ish experiment: regressing
per-class annual energy on the curve-band values yields an empirical Jacobian

    J[class_twh, band] = d(class TWh) / d(band multiplier)

— which band moves energy from which class — to guide a *joint* curve move
instead of one-knob-at-a-time tuning.

Method:

1. Collect every ERCOT bundle whose ``run_config.json`` records
   ``offer_curve_by_group`` and whose dispatch holds the requested years.
   Bundles are filterable by name prefix (``--runs Run- step``) so the
   regression can be restricted to a structurally comparable era — mixing
   eras confounds the band coefficients with unrelated model changes.
2. Per bundle-year observation: response = annual TWh by dispatch class
   (P1 pass); predictors = the recorded band multipliers of every
   (class, band) that VARIES across the selected bundles.
3. Year fixed effects: responses and predictors are demeaned within each
   year, so gas-price / demand / outage differences between years drop out
   and only cross-run curve variation identifies the coefficients.
4. Ridge-regularized least squares (the history moves several bands at
   once, so the design is collinear; ridge keeps the coefficients finite
   and shrinks the poorly identified ones toward zero — read magnitudes as
   relative leverage, not exact derivatives).

Output: the Jacobian table (TWh per +0.01 band multiplier), the bands'
observed ranges, and a per-class R^2. Optionally writes the tidy Jacobian
to CSV (``--out``).

Usage:
    python scripts/archive/curve_class_jacobian.py                  # all 3-yr runs
    python scripts/archive/curve_class_jacobian.py --runs Run- step1
    python scripts/archive/curve_class_jacobian.py --years 2024 --ridge 0.5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

CALIB_ROOT = REPO / "results" / "calibration"

# Dispatch classes whose annual energy is regressed. Wind/solar/nuclear are
# excluded (no offer curve); OTHER/pseudo classes carry no curve either.
_RESPONSE_CLASSES: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "ST_GAS",
    "COAL_LIGNITE",
    "COAL_PRB",
    "COAL_BIT",
)

# Curve bands considered as predictors (per class, when they vary).
_BANDS: tuple[str, ...] = (
    "committed",
    "econ_low",
    "econ_high",
    "peak",
    "pct_peaking",
)

_MWH_PER_TWH = 1.0e6


def _load_bundles(
    prefixes: list[str] | None,
    years: list[int],
) -> list[tuple[str, dict, Path]]:
    """Return ``(name, offer_curve, dispatch_dir)`` for matching ERCOT bundles.

    A bundle qualifies when it records ``offer_curve_by_group``, is an ERCOT
    run, and its dispatch directory holds a P1 parquet for every requested
    year. ``prefixes`` filters by directory-name prefix (case-insensitive);
    ``None`` admits every bundle.
    """
    out = []
    for d in sorted(CALIB_ROOT.iterdir()):
        if prefixes and not any(d.name.lower().startswith(p.lower()) for p in prefixes):
            continue
        rc, meta_p = d / "run_config.json", d / "meta.json"
        if not (rc.exists() and meta_p.exists() and (d / "dispatch").exists()):
            continue
        meta = json.loads(meta_p.read_text())
        if meta.get("iso", "ERCOT") != "ERCOT":
            continue
        if not all((d / "dispatch" / f"{y}_P1.parquet").exists() for y in years):
            continue
        curve = (
            json.loads(rc.read_text())
            .get("scenario_config", {})
            .get("offer_curve_by_group")
        )
        if curve:
            out.append((d.name, curve, d / "dispatch"))
    return out


def _class_twh(dispatch_dir: Path, year: int) -> dict[str, float]:
    """Return annual TWh by dispatch class from a bundle-year P1 parquet."""
    df = pd.read_parquet(dispatch_dir / f"{year}_P1.parquet", columns=["klass", "mw"])
    twh = df.groupby("klass", observed=True)["mw"].sum() / _MWH_PER_TWH
    return {k: float(twh.get(k, 0.0)) for k in _RESPONSE_CLASSES}


def _varying_features(
    bundles: list[tuple[str, dict, Path]],
) -> list[tuple[str, str]]:
    """Return the (class, band) pairs that vary across the selected bundles."""
    seen: dict[tuple[str, str], set[float]] = {}
    for _, curve, _ in bundles:
        for cls, bands in curve.items():
            for band in _BANDS:
                v = bands.get(band)
                if v is not None:
                    seen.setdefault((cls, band), set()).add(round(float(v), 6))
    return sorted(k for k, vals in seen.items() if len(vals) > 1)


def build_design(
    bundles: list[tuple[str, dict, Path]],
    years: list[int],
) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """Assemble the observation frame: one row per (bundle, year).

    Columns: the varying ``cls.band`` predictors, the ``_RESPONSE_CLASSES``
    TWh responses, plus ``bundle`` / ``year`` identifiers. A bundle missing a
    varying band (e.g. ``peak`` absent before the flat-peak era) contributes
    NaN for it and is dropped for fits involving that feature.
    """
    feats = _varying_features(bundles)
    rows = []
    for name, curve, ddir in bundles:
        for y in years:
            row: dict[str, object] = {"bundle": name, "year": y}
            for cls, band in feats:
                v = curve.get(cls, {}).get(band)
                row[f"{cls}.{band}"] = float(v) if v is not None else np.nan
            row.update(_class_twh(ddir, y))
            rows.append(row)
    return pd.DataFrame(rows), feats


def fit_jacobian(
    obs: pd.DataFrame,
    feats: list[tuple[str, str]],
    ridge: float,
) -> pd.DataFrame:
    """Ridge-regress within-year-demeaned class TWh on demeaned band values.

    Returns the Jacobian as a frame indexed by response class with one
    column per ``cls.band`` feature, in TWh per +0.01 multiplier, plus an
    ``r2`` column (in-sample, demeaned space).
    """
    cols = [f"{c}.{b}" for c, b in feats]
    use = obs.dropna(subset=cols)
    # Demean predictors and responses within each year (year fixed effects).
    demean = lambda g: g - g.mean()  # noqa: E731 — tiny, used twice
    X = use.groupby("year")[cols].transform(demean).to_numpy()
    rows = {}
    for klass in _RESPONSE_CLASSES:
        if klass not in use:
            continue
        y = use.groupby("year")[klass].transform(demean).to_numpy()
        # Ridge: (X'X + a I)^-1 X'y, a scaled to the feature variance so the
        # penalty is comparable across bands measured in different units.
        a = ridge * np.trace(X.T @ X) / max(X.shape[1], 1)
        beta = np.linalg.solve(X.T @ X + a * np.eye(X.shape[1]), X.T @ y)
        pred = X @ beta
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float((y**2).sum())
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        rows[klass] = dict(zip(cols, beta * 0.01), r2=r2, n=len(y))
    return pd.DataFrame(rows).T


def pair_diffs(pairs: list[str], years: list[int]) -> None:
    """Print curve-band diffs and per-class dTWh for bundle pairs ``A:B``.

    The regression Jacobian is collinearity-diluted when the history moves
    several bands at once; a pair of consecutive runs that changed only one
    or two bands is a far sharper sensitivity estimate. Empirical scale from
    the ERCOT history (2024): CT_PEAKER.committed -0.20 -> CT +2.1 TWh;
    CC_REGULAR.econ_high +-0.10 -> CC -+1.8 TWh; COAL_PRB.committed
    -0.10 -> PRB +1.3 TWh — roughly 6x the ridge-fit coefficients.
    """
    for pair in pairs:
        a, b = pair.split(":")
        cfg = {}
        for name in (a, b):
            cfg[name] = json.loads((CALIB_ROOT / name / "run_config.json").read_text())[
                "scenario_config"
            ]["offer_curve_by_group"]
        diffs = {
            f"{cls}.{band}": round(cfg[b][cls][band] - cfg[a][cls][band], 4)
            for cls in cfg[a]
            for band in cfg[a][cls]
            if cls in cfg[b]
            and band in cfg[b][cls]
            and abs(cfg[b][cls][band] - cfg[a][cls][band]) > 1e-9
        }
        print(f"\n{a} -> {b}")
        print(f"  band diffs: {diffs}")
        for y in years:
            ta = _class_twh(CALIB_ROOT / a / "dispatch", y)
            tb = _class_twh(CALIB_ROOT / b / "dispatch", y)
            d = {k: round(tb[k] - ta[k], 2) for k in ta if abs(tb[k] - ta[k]) > 0.05}
            print(f"  dTWh {y}: {d}")


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--runs",
        nargs="*",
        default=None,
        metavar="PREFIX",
        help="Bundle-name prefixes to include (default: all "
        "ERCOT bundles covering the years).",
    )
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--ridge", type=float, default=0.1, help="Ridge penalty scale (default 0.1)."
    )
    ap.add_argument(
        "--out", default=None, metavar="CSV", help="Write the tidy Jacobian to CSV."
    )
    ap.add_argument(
        "--pairs",
        nargs="*",
        default=None,
        metavar="A:B",
        help="Sharp one-move sensitivities: print curve-band "
        "diffs and per-class dTWh for each bundle pair "
        "(e.g. Run-71:Run-72). Skips the regression.",
    )
    args = ap.parse_args()

    if args.pairs:
        pair_diffs(args.pairs, args.years)
        return

    bundles = _load_bundles(args.runs, args.years)
    if len(bundles) < 3:
        sys.exit(f"only {len(bundles)} qualifying bundles — need >= 3")
    print(f"{len(bundles)} bundles x {len(args.years)} years:")
    for name, _, _ in bundles:
        print(f"  {name}")

    obs, feats = build_design(bundles, args.years)
    cols = [f"{c}.{b}" for c, b in feats]
    print("\nVarying bands (range observed):")
    for col in cols:
        print(f"  {col:28s} {obs[col].min():.3f} – {obs[col].max():.3f}")

    jac = fit_jacobian(obs, feats, args.ridge)
    print(
        f"\nJacobian — TWh per +0.01 band multiplier "
        f"(ridge={args.ridge}, year fixed effects):"
    )
    body = jac.drop(columns=["r2", "n"]).T  # rows = bands, cols = classes
    with pd.option_context(
        "display.width", 200, "display.float_format", "{:+.3f}".format
    ):
        print(body)
        print("\nfit quality (in-sample, demeaned):")
        print(jac[["r2", "n"]])
    print(
        "\nRead magnitudes as relative leverage, not exact derivatives: "
        "the run history moves several bands at once (collinear design) "
        "and bundles also differ in non-curve changes."
    )

    if args.out:
        tidy = (
            jac.drop(columns=["r2", "n"])
            .reset_index(names="response_class")
            .melt(id_vars="response_class", var_name="band", value_name="twh_per_0p01")
        )
        tidy.to_csv(args.out, index=False)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
