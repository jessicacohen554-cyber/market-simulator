"""Backfill the fossil CO2 metric into already-committed dashboard payloads.

The CO2 metric (``bench[year].co2`` / ``run.years[year].co2``) was added to
``render_calibration_html.build_payload`` after the registered runs were
rendered, so their committed ``runs/<id>.js`` and ``bench/<ISO>/<year>.json.gz``
parts lack it and the C5a CO2 verdict stays SKIPPED. Re-rendering needs a full
re-solve (bundles do not commit dispatch parquets), but the metric does not: the
**model** side is already in each run payload's ``gmModel`` (grid-delivered class
TWh), and the **actual** side needs only the committed ``eia923.parquet`` plus
the eGRID/CAMPD rate artifact. This script patches both in place, applying the
exact same per-class intensity logic ``build_payload`` uses — so a later full
render of the same bundle reproduces byte-identical payloads.

Per (ISO, year) it computes one net-generation-weighted CO2 intensity from the
newest covering run's committed EIA-923 fossil plants, writes the actual into the
bench part, and applies that same intensity to every covering run's ``gmModel``
for the model side. Years no committed run can anchor are left untouched (their
C5a stays SKIPPED). Writers are reused from ``render_backcast`` so the bytes
match the deploy assembler's expectations.

Usage:
    python scripts/retrofit_co2_payloads.py            # all ISOs
    python scripts/retrofit_co2_payloads.py --iso PJM  # one ISO
    python scripts/retrofit_co2_payloads.py --dry-run  # report only, no writes
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

_spec = importlib.util.spec_from_file_location(
    "render_backcast", str(REPO / "scripts" / "render_backcast.py")
)
rb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rb)
rch = rb.rch  # render_calibration_html (already loaded by render_backcast)

from market_sim.data import egrid  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("retrofit_co2")

REGISTRY_DIR = rb.DATA_DIR / "registry"
RUNS_DIR = rb.RUNS_DIR
BENCH_DIR = rb.BENCH_DIR


def _intensity_for(bundle: Path, year: int):
    """Return ``(intensity, covPct)`` from a bundle's EIA-923, or ``None``.

    Mirrors ``build_payload``: the bundle's EIA-923 frame is filtered to the
    year and the fossil classes (after the OTHER_FOSSIL scoring transform), the
    plants are mapped to their CO2 rate, and the rates are net-generation-
    weighted to a tonnes/MWh intensity per class. ``covPct`` is the share of
    fossil-class generation carrying a plant-specific rate.
    """
    p = rch.bundle_input_path(bundle, "eia923")
    if p is None:
        return None
    e = pd.read_parquet(p)
    e = e[e["year"] == year]
    if e.empty:
        return None
    e = rch.apply_other_fossil_scoring(e, year, plant_col="plant_id")
    e = e[e["klass"].isin(rch.FOSSIL_GROUPS)]
    if e.empty:
        return None
    rate = egrid.fossil_co2_rate_map(int(year))
    intensity = egrid.class_co2_intensity(
        e, rate, plant_col="plant_id", klass_col="klass", gen_col="annual_mwh"
    )
    if not intensity:
        return None
    fr = e.assign(rate=e["plant_id"].astype(int).map(rate))
    gcov = float(fr.loc[fr["rate"].notna(), "annual_mwh"].sum())
    gall = float(fr["annual_mwh"].sum())
    return intensity, (round(100.0 * gcov / gall, 1) if gall > 0 else 0.0)


def _sidecars_by_iso(iso_filter: str | None) -> dict[str, list[dict]]:
    """Return ``{iso: [sidecar, ...]}`` for every registered run (id-sorted)."""
    by_iso: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        rec = json.loads(path.read_text())
        iso = rec.get("iso", "ERCOT")
        if iso_filter and iso.upper() != iso_filter.upper():
            continue
        by_iso[iso].append(rec)
    for iso in by_iso:
        by_iso[iso].sort(key=lambda r: r["id"])
    return by_iso


def _intensity_by_year(recs: list[dict]) -> tuple[dict[int, dict], dict[int, float]]:
    """Per-year CO2 intensity from the newest covering run with committed 923.

    Matches the dashboard's "newest run covering a year supplies the benchmark"
    rule: years are anchored by the highest-id run that both covers the year and
    has a readable EIA-923 bundle.
    """
    years = sorted({int(y) for r in recs for y in r.get("years", [])})
    intensity_by_year: dict[int, dict] = {}
    cov_by_year: dict[int, float] = {}
    for year in years:
        for rec in reversed(recs):  # newest (highest id) first
            if year not in {int(y) for y in rec.get("years", [])}:
                continue
            res = _intensity_for(REPO / rec["bundle"], year)
            if res is not None:
                intensity_by_year[year], cov_by_year[year] = res
                break
    return intensity_by_year, cov_by_year


def _patch_bench_part(
    iso: str, year: int, intensity: dict, cov: float, dry_run: bool
) -> bool:
    """Inject the actual CO2 into one bench part; return whether it changed."""
    part = BENCH_DIR / iso / f"{year}.json.gz"
    if not part.exists():
        return False
    obj = json.loads(gzip.decompress(part.read_bytes()))
    class_full = obj.get("bench", {}).get("classFull", {})
    actual_mt, by = rch._fossil_co2(class_full, intensity)
    obj["bench"]["co2"] = {
        "egrid": actual_mt,
        "byClass": by,
        "intensity": {k: round(v, 5) for k, v in intensity.items()},
        "covPct": cov,
    }
    if not dry_run:
        rb._write_bench_part(iso, year, obj.get("meta", {}), obj["bench"])
    return True


def _patch_run(rec: dict, intensity_by_year: dict[int, dict], dry_run: bool) -> int:
    """Inject the model CO2 into one run payload; return years patched."""
    run_path = RUNS_DIR / f"{rec['id']}.js"
    if not run_path.exists():
        return 0
    model = rch_decode(run_path.read_text())
    patched = 0
    for ystr, ypay in (model.get("years") or {}).items():
        year = int(ystr)
        intensity = intensity_by_year.get(year)
        if intensity is None:
            continue
        # build_payload applies the ROUNDED (stored) intensity to the model side.
        rounded = {k: round(v, 5) for k, v in intensity.items()}
        model_mt, by = rch._fossil_co2(ypay.get("gmModel") or {}, rounded)
        ypay["co2"] = {"model": model_mt, "byClass": by}
        patched += 1
    if patched and not dry_run:
        rid = rec["id"]
        js = (
            "window.BC=window.BC||{};window.BC.runGz=window.BC.runGz||{};"
            f"window.BC.runGz[{json.dumps(rid)}]=" + json.dumps(rb._gzb64(model)) + ";"
        )
        run_path.write_text(js)
    return patched


def rch_decode(text: str) -> dict:
    """Decode a ``runs/<id>.js`` payload (``window.BC.runGz[..]="<b64>"``)."""
    import base64
    import re

    m = re.search(r'=\s*"([A-Za-z0-9+/=]+)"', text)
    if not m:
        raise ValueError("no gzip+base64 payload found in run js")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default=None, help="Restrict to one ISO.")
    parser.add_argument("--dry-run", action="store_true", help="Report, do not write.")
    args = parser.parse_args()

    by_iso = _sidecars_by_iso(args.iso)
    total_bench = total_runs = 0
    for iso, recs in by_iso.items():
        intensity_by_year, cov_by_year = _intensity_by_year(recs)
        if not intensity_by_year:
            logger.info("%s: no year could be anchored (no committed EIA-923)", iso)
            continue
        n_bench = sum(
            _patch_bench_part(
                iso, y, intensity_by_year[y], cov_by_year[y], args.dry_run
            )
            for y in intensity_by_year
        )
        n_runs = sum(
            _patch_run(rec, intensity_by_year, args.dry_run) > 0 for rec in recs
        )
        years = ", ".join(
            f"{y}({cov_by_year[y]:.0f}%)" for y in sorted(intensity_by_year)
        )
        logger.info(
            "%s: anchored years %s -> %d bench parts, %d run payloads%s",
            iso,
            years,
            n_bench,
            n_runs,
            " [dry-run]" if args.dry_run else "",
        )
        total_bench += n_bench
        total_runs += n_runs
    logger.info(
        "done: %d bench parts, %d run payloads%s",
        total_bench,
        total_runs,
        " [dry-run]" if args.dry_run else "",
    )


if __name__ == "__main__":
    main()
