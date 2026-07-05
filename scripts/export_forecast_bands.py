"""Export forecast probability bands for the codebase-site fan-chart page (PB-4).

Reads a PB-2 sampler-ensemble out-dir (``bands.parquet`` + ``ensemble_meta.json``,
written by :func:`market_sim.ensemble.export_sampler_ensemble`) and, optionally,
a PB-0 scenario-matrix out-dir (``matrix.parquet`` + ``envelope.parquet`` +
``meta.json``, written by :func:`market_sim.matrix.write_matrix_outputs`), and
writes the SAME committed-payload pattern the backcast dashboard uses
(``scripts/render_backcast.py``): a gzip+base64 JS file the page lazy-loads,
plus a small hand-maintained manifest so the page knows which ensembles exist.

Unlike the backcast dashboard, there is no separate deploy-workflow-owned
build step here yet -- ``frontend/data/forecast/manifest.json`` is a plain
committed file this script updates in place (read-modify-write, one entry per
ensemble id), not a generated artifact. Follow the CLAUDE.md 413 push workflow
(``mcp__github__push_files``) when committing payloads.

``bands.parquet``'s ``layer`` column is the frozen enum
``{scenario_envelope, parametric, parametric_plus_structural}`` (plan §4.1);
this script reads whichever layers are actually present in the file and
degrades gracefully -- it never assumes a layer exists. PB-3 (the structural
prior) appends ``parametric_plus_structural`` to the same ``bands.parquet``
schema in a separate change; nothing here needs updating when it lands.

Usage:
    python scripts/export_forecast_bands.py \
        --ensemble-dir results/ensemble/ercot_v1 \
        --matrix-dir results/ensemble/ercot_scenario_matrix_a1b2c3d4e5 \
        [--ensemble-id ercot_v1] [--metric emissions_mt] \
        [--markdown-out results/ensemble/ercot_v1/bands_summary.md]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO / "frontend" / "data" / "forecast"

# The frozen §4.1 layer enum, in the order the fan chart draws them (back to
# front): the deterministic envelope is a backdrop, the parametric fan is the
# middle layer, and the published (+structural) fan is the most authoritative
# -- drawn last/on top. Rendering code and markdown-table layer preference
# both walk this list.
LAYER_ORDER: tuple[str, ...] = (
    "scenario_envelope",
    "parametric",
    "parametric_plus_structural",
)
DEFAULT_METRIC = "emissions_mt"


def _gzb64(obj) -> str:
    """Return gzip+base64 of a JSON-serializable object (byte-deterministic).

    Mirrors ``scripts/render_backcast.py``'s ``_gzb64`` exactly (``mtime=0``)
    so re-exporting unchanged data produces byte-identical output.
    """
    return base64.b64encode(
        gzip.compress(
            json.dumps(obj, sort_keys=True).encode(), compresslevel=9, mtime=0
        )
    ).decode()


def is_dispatch_conditional(meta: dict) -> bool:
    """Return whether the published band must carry the dispatch-conditional caveat.

    Plan §3.4: the fleet-path structural-error term λ(h) is set to 0 and
    flagged UNMEASURED until PP-0.3 (the capacity hindcast) lands, and every
    published artifact must carry the caveat until then. No ensemble emitted
    by :mod:`market_sim.ensemble` as of this writing carries a structured
    λ(h) field, so the honest default here is conservative: **True** (show
    the caveat) unless ``ensemble_meta.json`` explicitly declares the term
    measured via a top-level ``lambda_h_status`` or nested
    ``structural_prior.lambda_h_status`` field equal to ``"measured"``
    (case-insensitive). This lets the flag flip automatically once PP-0.3
    lands, with no code change here -- "the chart never displays a band the
    metadata cannot defend" cuts both ways: absence of proof is not proof of
    measurement.
    """
    status = meta.get("lambda_h_status")
    if status is None:
        status = (meta.get("structural_prior") or {}).get("lambda_h_status")
    if status is None:
        return True
    return str(status).strip().lower() != "measured"


def read_ensemble(ensemble_dir) -> dict:
    """Read a PB-2 sampler-ensemble out-dir into a plain-dict payload fragment.

    Args:
        ensemble_dir: Directory holding ``bands.parquet`` and
            ``ensemble_meta.json`` (:func:`market_sim.ensemble.export_sampler_ensemble`'s
            output).

    Returns:
        A dict with ``iso``, ``meta`` (the raw ``ensemble_meta.json``),
        ``layers_present`` (sorted by :data:`LAYER_ORDER`, derived from the
        actual ``bands.parquet`` contents -- never trusted from meta alone),
        ``metrics`` (sorted metric names present), ``quantiles`` (sorted
        distinct quantiles present), ``n_draws``, ``dispatch_conditional``,
        and ``bands`` (nested ``bands[layer][metric][year-as-str]`` ->
        ``{quantile-as-str: {value, n, bootstrap_lo, bootstrap_hi}}``).

    Raises:
        FileNotFoundError: When either input file is missing.
    """
    ensemble_dir = Path(ensemble_dir)
    bands_path = ensemble_dir / "bands.parquet"
    meta_path = ensemble_dir / "ensemble_meta.json"
    if not bands_path.exists():
        raise FileNotFoundError(f"missing {bands_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"missing {meta_path}")

    meta = json.loads(meta_path.read_text())
    df = pd.read_parquet(bands_path)

    layers_present = [l for l in LAYER_ORDER if l in set(df["layer"])]
    metrics = sorted(df["metric"].unique().tolist()) if not df.empty else []
    quantiles = sorted(df["quantile"].unique().tolist()) if not df.empty else []

    n_draws = None
    sampler = meta.get("sampler") or {}
    if isinstance(sampler, dict) and sampler.get("n") is not None:
        n_draws = int(sampler["n"])
    elif meta.get("members"):
        n_draws = len(meta["members"])
    elif not df.empty:
        n_draws = int(df["n"].iloc[0])

    bands: dict = {}
    for layer, layer_df in df.groupby("layer"):
        by_metric: dict = {}
        for metric, metric_df in layer_df.groupby("metric"):
            by_year: dict = {}
            for year, year_df in metric_df.groupby("year"):
                by_quantile = {}
                for _, row in year_df.iterrows():
                    by_quantile[str(row["quantile"])] = {
                        "value": float(row["value"]),
                        "n": int(row["n"]),
                        "bootstrap_lo": float(row["bootstrap_lo"]),
                        "bootstrap_hi": float(row["bootstrap_hi"]),
                    }
                by_year[str(int(year))] = by_quantile
            by_metric[metric] = by_year
        bands[layer] = by_metric

    return {
        "iso": meta.get("iso"),
        "meta": meta,
        "layers_present": layers_present,
        "metrics": metrics,
        "quantiles": quantiles,
        "n_draws": n_draws,
        "dispatch_conditional": is_dispatch_conditional(meta),
        "synthetic": bool(meta.get("synthetic", False)),
        "label_text": meta.get("label", ""),
        "quantile_estimator": meta.get("quantile_estimator", ""),
        "bands": bands,
    }


def read_matrix(matrix_dir) -> dict:
    """Read a PB-0 scenario-matrix out-dir into a plain-dict payload fragment.

    Args:
        matrix_dir: Directory holding ``matrix.parquet``, ``envelope.parquet``
            and ``meta.json`` (:func:`market_sim.matrix.write_matrix_outputs`'s
            output).

    Returns:
        A dict with ``matrix_id``, ``label`` (the deterministic-scenario-range
        label, plan §1.3/§4.2), ``cases`` (sorted case names), ``envelope``
        (``{year-as-str: {min, min_case, max, max_case}}``) and
        ``trajectories`` (``{case: {year-as-str: emissions_mt}}`` -- the 13
        named-case reference lines).

    Raises:
        FileNotFoundError: When any of the three input files is missing.
    """
    matrix_dir = Path(matrix_dir)
    matrix_path = matrix_dir / "matrix.parquet"
    envelope_path = matrix_dir / "envelope.parquet"
    meta_path = matrix_dir / "meta.json"
    for p in (matrix_path, envelope_path, meta_path):
        if not p.exists():
            raise FileNotFoundError(f"missing {p}")

    meta = json.loads(meta_path.read_text())
    matrix_df = pd.read_parquet(matrix_path)
    envelope_df = pd.read_parquet(envelope_path)

    trajectories: dict = {}
    for case, case_df in matrix_df.groupby("case"):
        trajectories[case] = {
            str(int(row["year"])): float(row["emissions_mt"])
            for _, row in case_df.iterrows()
        }

    envelope: dict = {}
    for _, row in envelope_df.iterrows():
        envelope[str(int(row["year"]))] = {
            "min": float(row["min_mt"]),
            "min_case": str(row["min_case"]),
            "max": float(row["max_mt"]),
            "max_case": str(row["max_case"]),
        }

    return {
        "matrix_id": meta.get("matrix_id"),
        "label": meta.get("label", ""),
        "cases": sorted(trajectories),
        "envelope": envelope,
        "trajectories": trajectories,
    }


def build_payload(
    ensemble_id: str,
    ensemble: dict,
    matrix: dict | None,
    default_metric: str = DEFAULT_METRIC,
) -> dict:
    """Assemble the page-ready JSON payload from an ensemble (+ optional matrix).

    Args:
        ensemble_id: The id this payload is published under.
        ensemble: :func:`read_ensemble`'s return value.
        matrix: :func:`read_matrix`'s return value, or ``None`` when no
            scenario-matrix envelope is available for this ensemble.
        default_metric: The metric the page selects on first load; falls back
            to the first available metric if absent.

    Returns:
        The full payload dict written to ``frontend/data/forecast/<id>.js``.
    """
    metrics = ensemble["metrics"]
    default_metric = (
        default_metric
        if default_metric in metrics
        else (metrics[0] if metrics else default_metric)
    )
    return {
        "ensemble_id": ensemble_id,
        "iso": ensemble["iso"],
        "synthetic": ensemble["synthetic"],
        "dispatch_conditional": ensemble["dispatch_conditional"],
        "n_draws": ensemble["n_draws"],
        "layers_present": ensemble["layers_present"],
        "metrics": metrics,
        "default_metric": default_metric,
        "quantiles": ensemble["quantiles"],
        "label_text": ensemble["label_text"],
        "quantile_estimator": ensemble["quantile_estimator"],
        "bands": ensemble["bands"],
        "matrix": matrix,
    }


def write_payload_js(
    payload: dict, ensemble_id: str, frontend_dir=FRONTEND_DIR
) -> Path:
    """Write the gzip+base64 payload JS file, mirroring ``render_backcast.py``.

    Args:
        payload: :func:`build_payload`'s return value.
        ensemble_id: The id to publish under; determines the filename and the
            ``window.FB.bandsGz`` key.
        frontend_dir: Output directory; created if absent.

    Returns:
        The path written.
    """
    frontend_dir = Path(frontend_dir)
    frontend_dir.mkdir(parents=True, exist_ok=True)
    out_path = frontend_dir / f"{ensemble_id}.js"
    out_path.write_text(
        "window.FB=window.FB||{};window.FB.bandsGz=window.FB.bandsGz||{};"
        f"window.FB.bandsGz[{json.dumps(ensemble_id)}]="
        + json.dumps(_gzb64(payload))
        + ";"
    )
    return out_path


def update_manifest(payload: dict, frontend_dir=FRONTEND_DIR) -> Path:
    """Merge this ensemble's summary entry into the committed manifest.json.

    Plain read-modify-write (not deploy-workflow-generated, unlike the
    backcast ``manifest.js``): every export call upserts its own entry keyed
    by ``ensemble_id``, so concurrent exports for different ids never
    conflict and re-exporting the same id just refreshes its row.

    Args:
        payload: :func:`build_payload`'s return value.
        frontend_dir: Directory holding (or to hold) ``manifest.json``.

    Returns:
        The path written.
    """
    frontend_dir = Path(frontend_dir)
    frontend_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = frontend_dir / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text())
        if manifest_path.exists()
        else {"ensembles": {}}
    )
    manifest.setdefault("ensembles", {})[payload["ensemble_id"]] = {
        "iso": payload["iso"],
        "synthetic": payload["synthetic"],
        "dispatch_conditional": payload["dispatch_conditional"],
        "n_draws": payload["n_draws"],
        "layers_present": payload["layers_present"],
        "has_matrix": payload["matrix"] is not None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path


def _best_layer(layers_present: list[str]) -> str | None:
    """Return the most-authoritative layer present, per :data:`LAYER_ORDER`."""
    for layer in reversed(LAYER_ORDER):
        if layer in layers_present:
            return layer
    return None


def write_markdown_table(payload: dict, out_path, metric: str | None = None) -> Path:
    """Write a plain-markdown P10/P50/P90-by-year table for reports (plan §4.2).

    Uses the most-authoritative probability layer present
    (``parametric_plus_structural`` over ``parametric``); if only the
    deterministic ``scenario_envelope`` layer is available -- no probability
    band exists at all -- emits the min/max envelope instead, with an
    explicit "NOT a probability band" caption rather than silently mislabeling
    an envelope as P10/P90.

    Args:
        payload: :func:`build_payload`'s return value.
        out_path: File to write.
        metric: Metric to tabulate; defaults to ``payload["default_metric"]``.

    Returns:
        The path written.

    Raises:
        ValueError: When no layer has any data for the chosen metric.
    """
    metric = metric or payload["default_metric"]
    layer = _best_layer(payload["layers_present"])
    lines = [f"# Forecast band -- {payload['ensemble_id']} -- {metric}", ""]
    if payload["synthetic"]:
        lines += ["**SYNTHETIC FIXTURE -- not a real forecast run.**", ""]

    if layer is None:
        raise ValueError("payload has no layers; nothing to tabulate")

    by_year = payload["bands"].get(layer, {}).get(metric)
    if layer == "scenario_envelope" or by_year is None:
        # Only the deterministic matrix envelope is available for this metric.
        envelope = (payload.get("matrix") or {}).get("envelope")
        if not envelope:
            raise ValueError(f"no data for metric {metric!r} in any layer")
        lines += [
            f"**{(payload['matrix'] or {}).get('label', 'deterministic scenario range')}"
            " -- NOT a probability band.**",
            "",
            "| Year | Min | Min case | Max | Max case |",
            "|---|---|---|---|---|",
        ]
        for year in sorted(envelope, key=int):
            row = envelope[year]
            lines.append(
                f"| {year} | {row['min']:.2f} | {row['min_case']} | "
                f"{row['max']:.2f} | {row['max_case']} |"
            )
        out_path = Path(out_path)
        out_path.write_text("\n".join(lines) + "\n")
        return out_path

    label = (
        "published (parametric + structural)"
        if layer == "parametric_plus_structural"
        else "parametric"
    )
    caveat = (
        " Dispatch-conditional -- excludes fleet-path structural error (plan §3.4)."
        if payload["dispatch_conditional"]
        else ""
    )
    lines += [
        f"**{label} probability band, n={payload['n_draws']} draws.**{caveat}",
        "",
        "| Year | P10 | P50 | P90 |",
        "|---|---|---|---|",
    ]
    for year in sorted(by_year, key=int):
        q = by_year[year]
        p10 = q.get("0.1", {}).get("value")
        p50 = q.get("0.5", {}).get("value")
        p90 = q.get("0.9", {}).get("value")
        fmt = lambda v: f"{v:.2f}" if v is not None else "—"
        lines.append(f"| {year} | {fmt(p10)} | {fmt(p50)} | {fmt(p90)} |")

    out_path = Path(out_path)
    out_path.write_text("\n".join(lines) + "\n")
    return out_path


def export(
    ensemble_dir,
    ensemble_id: str | None = None,
    matrix_dir=None,
    metric: str = DEFAULT_METRIC,
    markdown_out=None,
    frontend_dir=FRONTEND_DIR,
) -> dict[str, Path]:
    """End-to-end export: read inputs, build the payload, write every artifact.

    Args:
        ensemble_dir: PB-2 sampler-ensemble out-dir (see :func:`read_ensemble`).
        ensemble_id: Publish id; defaults to ``ensemble_dir``'s basename.
        matrix_dir: Optional PB-0 scenario-matrix out-dir (see :func:`read_matrix`).
        metric: Default metric for the page and the markdown table.
        markdown_out: Optional path for the plain-markdown summary table.
        frontend_dir: Output directory for the payload JS + manifest.

    Returns:
        A dict mapping artifact name to path written (``payload``, ``manifest``,
        and ``markdown`` when requested).
    """
    ensemble_dir = Path(ensemble_dir)
    ensemble_id = ensemble_id or ensemble_dir.name
    ensemble = read_ensemble(ensemble_dir)
    matrix = read_matrix(matrix_dir) if matrix_dir is not None else None
    payload = build_payload(ensemble_id, ensemble, matrix, default_metric=metric)

    out: dict[str, Path] = {
        "payload": write_payload_js(payload, ensemble_id, frontend_dir),
        "manifest": update_manifest(payload, frontend_dir),
    }
    if markdown_out is not None:
        out["markdown"] = write_markdown_table(payload, markdown_out, metric=metric)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--ensemble-dir", required=True, help="PB-2 sampler ensemble out-dir."
    )
    ap.add_argument(
        "--matrix-dir", default=None, help="PB-0 scenario matrix out-dir (optional)."
    )
    ap.add_argument(
        "--ensemble-id", default=None, help="Publish id; defaults to the dir name."
    )
    ap.add_argument(
        "--metric", default=DEFAULT_METRIC, help="Default metric for the page/table."
    )
    ap.add_argument(
        "--markdown-out", default=None, help="Optional markdown summary table path."
    )
    ap.add_argument(
        "--frontend-dir",
        default=str(FRONTEND_DIR),
        help="Output dir for the payload + manifest (default frontend/data/forecast).",
    )
    args = ap.parse_args()

    written = export(
        args.ensemble_dir,
        ensemble_id=args.ensemble_id,
        matrix_dir=args.matrix_dir,
        metric=args.metric,
        markdown_out=args.markdown_out,
        frontend_dir=args.frontend_dir,
    )
    for name, path in written.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
