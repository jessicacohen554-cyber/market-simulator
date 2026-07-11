"""Assemble, annotate and publish the PB-5 production probability band.

The post-solve half of the PB-5 batch (``docs/handoffs/
probability-bounds-plan-2026-07.md`` §3-§4): every ensemble member has already
been solved by the sequential slice invocations (``scripts/pb5_member_slice.py``,
rule 12), so each step here is cheap post-processing over the per-member cache.

Modes (``--mode``):

* ``assemble`` — expand the sampler spec, load every cached member, and write
  the §4.1 output surface (``draws/metrics/bands.parquet`` +
  ``ensemble_meta.json``) via :func:`market_sim.ensemble.run_sampler_ensemble`
  with ``workers=1``. With ``--prior-artifact`` the committed PB-3 structural
  prior is convolved in (the ``parametric_plus_structural`` layer). The prior
  is loaded from its committed fit artifact
  (``results/ensemble/structural-prior/<version>.json``) rather than re-fitted:
  ``default_prior()`` re-reads the D-7 statmode run payloads, which the
  dashboard's top-15-per-ISO retention (CLAUDE.md rule 15) has since pruned
  from ``frontend/data/backcast/runs/`` — the committed artifact IS the
  durable record of that fit (rule 23: it re-derives only when the probes are
  re-run, never here).
* ``limitations`` — inject an honest-limitations block (a committed JSON list
  of ``{id, title, detail}``) into ``ensemble_meta.json``, where the PB-4
  exporter and fan-chart page surface it verbatim.
* ``sensitivity`` — compare the emissions bands of the A-2 gas–load rank-
  correlation sensitivity ensembles (rho=0 / rho=0.6, paired seed) against the
  main run and write ``sensitivity_a2.md`` + ``sensitivity_a2.json`` into the
  main out-dir.
* ``publish`` — build the fan-chart payload + manifest entry + markdown table
  via :mod:`scripts.export_forecast_bands`.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import replace
from pathlib import Path

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.structural_prior import IsoResidual, StructuralPrior
from market_sim.uncertainty import UncertaintySpec, draw_to_config, sample_draws

logger = logging.getLogger("pb5_assemble")

REPO = Path(__file__).resolve().parent.parent


def prior_from_artifact(path) -> StructuralPrior:
    """Reconstruct a :class:`StructuralPrior` from its committed fit artifact.

    Inverse of :func:`market_sim.structural_prior.write_prior_artifact` for the
    fields the convolution consumes. The artifact carries the full per-ISO
    residual record, so the reconstruction is exact (asserted against the
    artifact's own stored ``pooled_scale``).

    Args:
        path: Path to the committed prior artifact JSON.

    Returns:
        The reconstructed prior.

    Raises:
        ValueError: When the reconstructed scale does not reproduce the
            artifact's stored ``pooled_scale`` (a corrupted or hand-edited
            artifact must not silently drive a published band).
    """
    art = json.loads(Path(path).read_text())
    per_iso = {
        iso: IsoResidual(
            iso=rec["iso"],
            years=tuple(rec["years"]),
            model_co2=tuple(rec["model_co2"]),
            actual_co2=tuple(rec["actual_co2"]),
            eps=tuple(rec["eps"]),
            bias=rec["bias"],
            noise_sd=rec["noise_sd"],
            statmode_run_id=rec["statmode_run_id"],
            basis_stale=rec["basis_stale"],
            rescore=rec["rescore"],
        )
        for iso, rec in art["per_iso"].items()
    }
    prior = StructuralPrior(
        version=art["version"],
        nu=float(art["nu"]),
        fit_years=tuple(art["fit_years"]),
        small_sample_inflation=float(art["small_sample_inflation"]),
        pooled_noise_var=float(art["pooled_noise_var"]),
        horizon_lambda=float(art["horizon_lambda"]),
        per_iso=per_iso,
        emissions_basis=dict(art.get("emissions_basis", {})),
    )
    if abs(prior.scale(0) - float(art["pooled_scale"])) > 1e-12:
        raise ValueError(
            f"prior artifact {path}: reconstructed scale {prior.scale(0)!r} != "
            f"stored pooled_scale {art['pooled_scale']!r}"
        )
    return prior


def _load_spec(args) -> UncertaintySpec:
    """Load the sampler spec with the CLI n/seed overrides applied."""
    spec = UncertaintySpec.from_yaml(args.sampler)
    overrides = {}
    if args.draws is not None:
        overrides["n"] = args.draws
    if args.seed is not None:
        overrides["seed"] = args.seed
    return replace(spec, **overrides) if overrides else spec


def _effective_cache_key(config: ScenarioConfig, iso: str) -> str:
    """Return the cache key ``run_scenario_iso`` will actually run under.

    Mirrors the runner's config-build seam exactly: the ``policy_bundle``
    lever resolves to its underlying fields, then the ISO's
    ``default_scenario_overrides`` apply to any field the caller left at its
    dataclass default (e.g. ERCOT's ``scarcity_price_overlay=True``). The raw
    ``config.cache_key()`` differs from this whenever an ISO default fires,
    so cache probes must use this key, never the raw one.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import resolve_policy_bundle

    config = resolve_policy_bundle(config)
    iso_config = get_iso_config(iso)
    if iso_config.default_scenario_overrides:
        defaults = ScenarioConfig()
        to_apply = {
            k: v
            for k, v in iso_config.default_scenario_overrides.items()
            if getattr(config, k) == getattr(defaults, k)
        }
        if to_apply:
            config = config.with_overrides(**to_apply)
    return config.cache_key()


def do_assemble(args) -> None:
    """Load cached members and write the §4.1 surface (+ structural layer)."""
    from market_sim.ensemble import run_sampler_ensemble
    from market_sim.results import cache

    base = ScenarioConfig.from_yaml(args.config)
    spec = _load_spec(args)
    iso = (args.iso or base.iso).upper()

    # Surface any member that is NOT fully cached before committing to the
    # assembly pass: a missing member would silently re-solve for ~an hour
    # inside run_sampler_ensemble, which the operator should know about.
    drawset = sample_draws(spec)
    missing = []
    for draw in drawset:
        cfg = draw_to_config(base, draw)
        key = _effective_cache_key(cfg, iso)
        for year in range(cfg.start_year, cfg.end_year + 1):
            if not cache.is_cached(iso, key, year):
                missing.append((draw.draw_id, year))
                break
    if missing:
        logger.warning(
            "%d member(s) not fully cached (will re-solve in-process): %s",
            len(missing),
            missing[:8],
        )

    prior = prior_from_artifact(args.prior_artifact) if args.prior_artifact else None
    run_sampler_ensemble(base, spec, iso, workers=1, out_dir=args.out_dir, prior=prior)
    logger.info("assembled %s (prior=%s)", args.out_dir, bool(prior))


def do_limitations(args) -> None:
    """Merge the honest-limitations block into ``ensemble_meta.json``."""
    meta_path = Path(args.out_dir) / "ensemble_meta.json"
    meta = json.loads(meta_path.read_text())
    limitations = json.loads(Path(args.limitations).read_text())
    if not isinstance(limitations, list):
        raise ValueError(f"{args.limitations} must hold a JSON list")
    meta["honest_limitations"] = limitations
    meta_path.write_text(json.dumps(meta, separators=(",", ":"), default=str))
    logger.info(
        "injected %d honest-limitation entries into %s",
        len(limitations),
        meta_path,
    )


def _band_pivot(band_dir, layer: str, metric: str) -> pd.DataFrame:
    """Return a (year x quantile) pivot of one ensemble's band values."""
    df = pd.read_parquet(Path(band_dir) / "bands.parquet")
    df = df[(df["layer"] == layer) & (df["metric"] == metric)]
    return df.pivot(index="year", columns="quantile", values="value")


def do_sensitivity(args) -> None:
    """Write the A-2 rho-sensitivity band-delta summary into the main out-dir.

    The delta is a paired contrast: the rho=0 and rho=0.6 ensembles share the
    seed (identical LHS matrix, identical gas/tech/discrete draws), so per-draw
    only the induced load percentile moves and the band delta isolates the
    correlation assumption rather than resampling noise.
    """
    metric = "emissions_mt"
    layer = "parametric"
    main = _band_pivot(args.out_dir, layer, metric)
    rho00 = _band_pivot(args.rho00_dir, layer, metric)
    rho06 = _band_pivot(args.rho06_dir, layer, metric)

    n_main = int(pd.read_parquet(Path(args.out_dir) / "bands.parquet")["n"].iloc[0])
    n_sens = int(pd.read_parquet(Path(args.rho00_dir) / "bands.parquet")["n"].iloc[0])

    rows = []
    for year in sorted(set(main.index) & set(rho00.index) & set(rho06.index)):
        for q in (0.1, 0.5, 0.9):
            rows.append(
                {
                    "year": int(year),
                    "quantile": q,
                    "main_rho03": float(main.loc[year, q]),
                    "rho00": float(rho00.loc[year, q]),
                    "rho06": float(rho06.loc[year, q]),
                    "delta_rho06_minus_rho00": float(
                        rho06.loc[year, q] - rho00.loc[year, q]
                    ),
                }
            )
    summary = {
        "assumption": "A-2 gas-load Spearman rho (main 0.3; swept 0.0 / 0.6)",
        "design": (
            "paired: identical seed/LHS across the two sensitivity ensembles, "
            "only the induced load percentile differs per draw; "
            f"n_main={n_main}, n_sensitivity={n_sens} per variant"
        ),
        "metric": metric,
        "layer": layer,
        "rows": rows,
    }
    out_json = Path(args.out_dir) / "sensitivity_a2.json"
    out_json.write_text(json.dumps(summary, indent=1))

    lines = [
        "# A-2 sensitivity -- gas-load rank correlation (paired sweep)",
        "",
        f"Main band: rho_S = +0.3, n={n_main}. Sensitivity ensembles: rho_S = 0.0 "
        f"and +0.6, n={n_sens} each, same seed (paired draws -- only the load "
        "percentile moves).",
        "",
        f"Parametric-layer {metric} (Mt):",
        "",
        "| Year | Q | rho=0.0 | rho=0.3 (main) | rho=0.6 | delta (0.6-0.0) |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['year']} | P{int(r['quantile'] * 100)} | {r['rho00']:.2f} "
            f"| {r['main_rho03']:.2f} | {r['rho06']:.2f} "
            f"| {r['delta_rho06_minus_rho00']:+.2f} |"
        )
    (Path(args.out_dir) / "sensitivity_a2.md").write_text("\n".join(lines) + "\n")
    logger.info("wrote sensitivity summary (%d rows) into %s", len(rows), args.out_dir)


def do_publish(args) -> None:
    """Export the fan-chart payload, manifest entry and markdown table."""
    import export_forecast_bands as efb

    written = efb.export(
        args.out_dir,
        ensemble_id=args.ensemble_id,
        matrix_dir=args.matrix_dir,
        markdown_out=Path(args.out_dir) / "bands_summary.md",
    )
    for name, path in written.items():
        logger.info("publish: %s -> %s", name, path)


def main() -> None:
    """Dispatch one assembly mode."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--mode",
        required=True,
        choices=("assemble", "limitations", "sensitivity", "publish"),
    )
    ap.add_argument("--config", help="Base forecast scenario YAML (assemble).")
    ap.add_argument("--sampler", help="Sampler spec YAML (assemble).")
    ap.add_argument("--draws", type=int, default=None, help="Override spec n.")
    ap.add_argument("--seed", type=int, default=None, help="Override spec seed.")
    ap.add_argument("--iso", default=None)
    ap.add_argument("--out-dir", required=True, help="Main ensemble out-dir.")
    ap.add_argument(
        "--prior-artifact",
        default=None,
        help="Committed PB-3 prior artifact JSON (assemble; enables the "
        "parametric_plus_structural layer).",
    )
    ap.add_argument(
        "--limitations", default=None, help="Honest-limitations JSON (limitations)."
    )
    ap.add_argument("--rho00-dir", default=None, help="rho=0.0 out-dir (sensitivity).")
    ap.add_argument("--rho06-dir", default=None, help="rho=0.6 out-dir (sensitivity).")
    ap.add_argument("--ensemble-id", default=None, help="Publish id (publish).")
    ap.add_argument("--matrix-dir", default=None, help="PB-0 matrix dir (publish).")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    if args.mode == "assemble":
        do_assemble(args)
    elif args.mode == "limitations":
        do_limitations(args)
    elif args.mode == "sensitivity":
        do_sensitivity(args)
    elif args.mode == "publish":
        do_publish(args)


if __name__ == "__main__":
    main()
