"""Backfill the ``nonfossilHr`` Charts-tab panels into an ALREADY-REGISTERED run.

WHY THIS EXISTS. ``nonfossilHr`` (nuclear / hydro / the renewables / oil / other
/ net interchange hourly, model vs EIA-930 — see
``render_calibration_html.build_nonfossil_hourly``) is built by the standard
render path, so every future registration of every ISO carries it automatically
with no per-run action. But a run registered BEFORE the field existed can only
gain it two ways: re-solve, or splice. Re-solving a keeper to add a *view* is
never justified, and a full re-render is not even possible — the committed
bundles are SLIM:

    results/calibration/<name>/          # committed
      meta.json  run_config.json  metrics.json  calibration_attestation.json
      legitimacy_diagnostics.json
      hourly/class_hourly_<year>.parquet # <- rule 14 put this here for exactly
      hourly/system_<year>.parquet       #    this kind of session
    dispatch/  system.parquet  _shared/{campd,eia923,eia930}-*.parquet
                                         # ^ ALL GITIGNORED — absent on a fresh
                                         #   clone, so build_payload cannot run

So this script rebuilds ONLY the new field, from committed/reproducible inputs,
and splices it into the run's existing ``runs/<id>.js`` payload, leaving every
other field byte-identical. It is a one-way backfill for historical runs, not
part of the registration path.

INPUTS, in preference order (each falls back to the next):

  * model hourly by class — the bundle's ``dispatch/<year>_P1.parquet`` if the
    unit-hour frames happen to be present locally, else the COMMITTED
    ``hourly/class_hourly_<year>.parquet`` sidecar (cols year, pass, klass,
    hour, mw; filtered to the primary pass). The sidecar is the fresh-clone path
    and the reason historical backfill is possible at all.
  * EIA-930 hourly actual — the bundle's ``eia930`` shared-store extract if
    resolvable, else rebuilt from ``data/raw/eia-930-hourly/<BA> hourly.parquet``
    through ``run_calibration_full._eia930_frame`` — the SAME function that wrote
    the extract in the first place (ERCOT's dedicated loaders included), so the
    fallback cannot drift from the render path.

GUARDS. CLAUDE.md rule 22: years are restricted to the in-sample calibration
window (2023-2025) unless the ISO carries a calibration-complete marker AND
``--holdout-authorized`` is passed — reusing ``run_calibration_full``'s own
``enforce_holdout_year_gate`` rather than a second copy of the policy. Rendering
a heatmap of a quarantined year is a scoring event, so the default is the
intersection of the run's own years with the calibration window.

This script changes no solve, no scorer, no rubric criterion and no keeper
determination — it adds a diagnostic view to a payload.

Usage:
    python scripts/backfill_nonfossil_hourly.py --run 2026-07-23-nyiso-72-netrev-margin
    python scripts/backfill_nonfossil_hourly.py --run <id> --years 2023 2024 --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import render_calibration_html as rch  # noqa: E402
from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import bundle_io  # noqa: E402

rcf = rch.rcf  # run_calibration_full, already loaded by the renderer

from market_sim.config.iso_configs import get_iso_config  # noqa: E402

PRIMARY_PASS = "P1"


def _rel(path: Path) -> str:
    """Repo-relative display string for a path that may already be relative."""
    try:
        return str(Path(path).resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def model_hourly_by_class(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Return ``{klass: (8760,) MW}`` for one year from a bundle.

    Prefers the unit-hour ``dispatch/<year>_P1.parquet`` when present (the
    renderer's own source), and otherwise reads the committed
    ``hourly/class_hourly_<year>.parquet`` sidecar — identical content, since the
    sidecar is that frame grouped to (year, pass, klass, hour) by
    ``run_calibration_full._write_class_hourly_sidecar``.

    Raises:
        FileNotFoundError: when neither source is present for the year.
    """
    disp = bundle_io.dispatch_path(bundle, year, PRIMARY_PASS)
    if disp.exists():
        df = pd.read_parquet(disp, columns=["klass", "hour", "mw"])
        return rcf._class_hourly(df)

    sidecar = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not sidecar.exists():
        raise FileNotFoundError(
            f"no model hourly for {year}: neither {_rel(disp)} nor "
            f"{_rel(sidecar)} exists. A slim committed bundle should "
            "carry the hourly/ sidecar (CLAUDE.md rule 14)."
        )
    df = pd.read_parquet(sidecar)
    if "pass" in df.columns:
        passes = set(map(str, df["pass"].unique()))
        keep = PRIMARY_PASS if PRIMARY_PASS in passes else sorted(passes)[-1]
        df = df[df["pass"].astype(str) == keep]
    return rcf._class_hourly(df[["klass", "hour", "mw"]])


def actual_930_series(bundle: Path, iso: str, year: int) -> dict[str, np.ndarray]:
    """Return ``{series: (T,) MW}`` of EIA-930 hourly actuals for one year.

    Reads the bundle's ``eia930`` extract when the shared store is available,
    else regenerates the same frame from ``data/raw/eia-930-*`` via
    ``run_calibration_full._eia930_frame`` (the extract's own writer). Long
    format in, ``{series: array}`` out — the shape
    :func:`rch.build_nonfossil_hourly` consumes.

    Raises:
        FileNotFoundError: when neither the extract nor the raw source resolves.
    """
    frame: pd.DataFrame | None = None
    try:
        path = bundle_io.bundle_input_path(bundle, "eia930")
        if path is not None and Path(path).exists():
            allyears = pd.read_parquet(path)
            frame = allyears[allyears["year"] == year]
            if frame.empty:
                frame = None
    except (FileNotFoundError, KeyError, OSError):
        frame = None

    if frame is None:
        # Fresh-clone / slim-bundle fallback: rebuild from the raw 930 tree.
        frame = rcf._eia930_frame(year, iso, get_iso_config(iso))
        if frame is None:
            raise FileNotFoundError(
                f"no EIA-930 hourly actual for {iso} {year}: bundle extract "
                "absent and data/raw/eia-930-hourly has no usable rows."
            )
    return {
        s: g.sort_values("hour")["mw"].to_numpy(float)
        for s, g in frame.groupby("series", observed=True)
    }


def _verify_clock_alignment(
    bundle: Path, iso: str, year: int, actual: dict[str, np.ndarray]
) -> str:
    """Assert the model and EIA-930 hours are on the SAME clock (lag 0 wins).

    A one-hour pairing error manufactures a fake diurnal band and sends the next
    session chasing a mechanism that does not exist (see
    docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md,
    where exactly that happened to the LMP delta map). Both sides here are built
    on the model's chronological fixed-standard-time 8760 calendar, so this is a
    verification, not a correction: cross-correlate the model's own demand
    (``hourly/system_<year>.parquet``) against the 930 demand implied by the
    BA's net generation and interchange, and require lag 0 to dominate.

    Returns a short human-readable report line. Skipped (with a note) when the
    bundle carries no system sidecar or the 930 aggregates are absent.

    Raises:
        AssertionError: when a nonzero lag correlates better than lag 0.
    """
    sysfile = bundle / "hourly" / f"system_{year}.parquet"
    if not sysfile.exists() or "net_gen" not in actual:
        return f"    {year}: clock check SKIPPED (no system sidecar / no net_gen)"
    sy = pd.read_parquet(sysfile)
    if "pass" in sy.columns:
        sy = sy[sy["pass"].astype(str) == PRIMARY_PASS]
    hours = len(actual["net_gen"])
    model_dem = (
        sy.groupby("hour")["demand"]
        .sum()
        .reindex(range(hours), fill_value=0.0)
        .to_numpy(float)
    )
    a_dem = actual["net_gen"] - actual.get("interchange", np.zeros(hours))
    best, scores = 0, {}
    for lag in (-2, -1, 0, 1, 2):
        x = model_dem[lag:] if lag > 0 else model_dem[: hours + lag or None]
        y = a_dem[: hours - lag] if lag > 0 else a_dem[-lag or None :]
        n = min(len(x), len(y))
        if n < 100 or np.std(x[:n]) == 0 or np.std(y[:n]) == 0:
            continue
        scores[lag] = float(np.corrcoef(x[:n], y[:n])[0, 1])
    if not scores:
        return f"    {year}: clock check SKIPPED (degenerate demand series)"
    best = max(scores, key=lambda k: scores[k])
    assert best == 0, (
        f"{iso} {year}: model/EIA-930 clock MISALIGNED — lag {best:+d} "
        f"(r={scores[best]:.4f}) beats lag 0 (r={scores.get(0, float('nan')):.4f}). "
        "Refusing to emit hourly panels: a shifted pairing manufactures a fake "
        "diurnal band. See the ERCOT clock-artifact diagnosis."
    )
    return (
        f"    {year}: clock OK — lag 0 r={scores[0]:.4f} "
        f"(±1 h: {scores.get(-1, float('nan')):.4f}/{scores.get(1, float('nan')):.4f})"
    )


def backfill(
    run_id: str,
    years: list[int] | None = None,
    *,
    holdout_authorized: bool = False,
    dry_run: bool = False,
) -> dict[int, dict]:
    """Splice ``nonfossilHr`` into a registered run's payload for each year.

    Returns ``{year: panels}`` for the years populated. Writes
    ``frontend/data/backcast/runs/<run_id>.js`` in place (unless ``dry_run``),
    preserving every other payload field exactly.
    """
    sidecar = ba.REGISTRY / f"{run_id}.json"
    if not sidecar.exists():
        raise SystemExit(f"no registry sidecar for run {run_id!r} ({sidecar})")
    rec = json.loads(sidecar.read_text())
    iso = rec.get("iso", "ERCOT")
    bundle = bundle_io.resolve_bundle(rec["bundle"])
    payload_file = ba.RUNS / f"{run_id}.js"
    if not payload_file.exists():
        raise SystemExit(f"no committed payload for run {run_id!r} ({payload_file})")
    payload = ba.decode_run_js(payload_file.read_text())

    # Years: the run's own, intersected with the in-sample window unless a
    # holdout one-shot is explicitly authorized for a marked ISO (rule 22).
    have = sorted(int(y) for y in payload.get("years", rec.get("years", [])))
    want = sorted(set(years) & set(have)) if years else have
    if not want:
        raise SystemExit(
            f"no renderable years for {run_id}: requested {years}, payload has {have}"
        )
    rcf.enforce_holdout_year_gate(want, iso, holdout_authorized)

    print(f"{run_id} (iso={iso}, bundle={_rel(bundle)})")
    out: dict[int, dict] = {}
    for year in want:
        mh = model_hourly_by_class(bundle, year)
        actual = actual_930_series(bundle, iso, year)
        print(_verify_clock_alignment(bundle, iso, year, actual))
        panels = rch.build_nonfossil_hourly(mh, actual, hours=rch._T)
        # Reconcile against the payload's OWN fuelRows (built by the original
        # render, untouched here) — the interchange sign check in particular.
        yr_payload = payload.get("years", {}).get(str(year)) or payload.get(
            "years", {}
        ).get(year, {})
        rch._assert_nonfossil_hourly_reconciles(
            panels, mh, yr_payload.get("fuelRows", []), iso=iso, year=year
        )
        for panel, e in panels.items():
            a_txt = "       —" if e["aTwh"] is None else format(e["aTwh"], "+8.3f")
            r_txt = "—" if e["r"] is None else format(e["r"], ".3f")
            print(
                f"    {year} {panel:9s} model {e['mTwh']:+8.3f} TWh  "
                f"actual {a_txt} TWh  r={r_txt}"
            )
        if yr_payload:
            yr_payload["nonfossilHr"] = panels
        out[year] = panels

    if dry_run:
        print("  [dry-run] payload not written")
        return out
    before = payload_file.stat().st_size
    payload_file.write_text(ba.encode_run_js(run_id, payload))
    after = payload_file.stat().st_size
    print(
        f"  wrote {_rel(payload_file)}: "
        f"{before / 1024:.1f} KB -> {after / 1024:.1f} KB "
        f"(+{(after - before) / 1024:.1f} KB, +{100 * (after - before) / before:.0f}%)"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--run", required=True, help="Registered run id (registry sidecar)."
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="Restrict to these years (default: every year in the run payload, "
        "intersected with the rule-22 calibration window).",
    )
    ap.add_argument(
        "--holdout-authorized",
        action="store_true",
        help="Rule 22 one-shot: permit a year outside 2023-2025. Also requires "
        "the ISO to carry a calibration-complete marker.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and report the panels without rewriting the payload.",
    )
    args = ap.parse_args()
    backfill(
        args.run,
        args.years,
        holdout_authorized=args.holdout_authorized,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
