"""Re-base the fossil CO2 metric in already-committed dashboard payloads.

Originally the backfill tool that added the CO2 metric (``bench[year].co2`` /
``run.years[year].co2``) to payloads rendered before the metric existed. Now it
also carries committed payloads onto the **full-plant CHP-inclusive basis** of
rubric v2.3 (owner amendment 2026-07-09): the eGRID/CAMPD per-plant rates that
anchor the C5a actual are measured over each cogen's FULL net generation (host
self-supply + grid delivery), so comparing them against grid-delivered totals
understated both sides by the behind-the-meter CHP burn that eGRID counts. The
re-based blocks add the measured BTM host supply back on BOTH sides:

- actual = (``classFull`` + per-class BTM) x intensity  — the full EIA-923
  class totals the intensities were weighted on;
- model  = (``gmModel``  + per-class BTM) x intensity  — the grid LP dispatch
  plus the exact hold-out the LP never dispatched.

Re-rendering needs a full re-solve (bundles do not commit dispatch parquets),
but the re-base does not: the per-class intensity is already committed in each
bench part, ``classFull``/``gmModel`` are committed, and the BTM add-back is a
pure function of committed inputs (``run_calibration_full._btm_frame`` — EIA-923
class net generation x measured host shares, never the model's dispatch), so it
recomputes here exactly as the runs computed their ``btm.parquet``. Two knobs
are taken from committed artifacts: ``btm_backfill_year`` from the anchoring
bundle's ``meta.json``, and the CAMPD-active gate from the bench part's own
plants (``nodata`` is false exactly when the plant had positive CAMPD net —
the same set ``run_calibration_full`` derives from the CAMPD frame).

Per (ISO, year) the anchoring run is the newest (highest-id) registered run
covering the year, matching the dashboard's benchmark rule. Years whose bench
part lacks a committed intensity fall back to the anchoring bundle's EIA-923
(the original backfill path) and are skipped when neither exists.

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

_rcf_spec = importlib.util.spec_from_file_location(
    "run_calibration_full", str(REPO / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_rcf_spec)
_rcf_spec.loader.exec_module(rcf)

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data import egrid  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402

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
    fossil-class generation carrying a plant-specific rate. Fallback path for
    bench parts that predate the committed intensity.
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


def _bench_part(iso: str, year: int) -> dict | None:
    """Load one committed bench part, or ``None`` when absent."""
    part = BENCH_DIR / iso / f"{year}.json.gz"
    if not part.exists():
        return None
    return json.loads(gzip.decompress(part.read_bytes()))


def _anchor_rec(recs: list[dict], year: int) -> dict | None:
    """Newest (highest-id) registered run covering ``year``."""
    for rec in reversed(recs):
        if year in {int(y) for y in rec.get("years", [])}:
            return rec
    return None


def _btm_class(iso: str, year: int, anchor: dict | None, bench_obj: dict) -> dict:
    """Per-class measured BTM CHP host supply (TWh) for one ISO-year.

    Recomputes the runs' ``btm.parquet`` sizing from committed inputs via
    ``run_calibration_full._btm_frame`` (a pure function of EIA-923 class
    totals x measured host shares — byte-identical across rebuilds, rule #13).
    ``btm_backfill_year`` comes from the anchoring bundle's ``meta.json``; the
    CAMPD-active gate is reconstructed from the bench part's plants (``nodata``
    is set exactly when the plant's CAMPD net was non-positive).
    """
    backfill = None
    if anchor is not None:
        meta_path = REPO / anchor["bundle"] / "meta.json"
        if meta_path.exists():
            backfill = json.loads(meta_path.read_text()).get("btm_backfill_year")
    campd_active = {
        int(code)
        for code, p in (bench_obj.get("bench", {}).get("plants") or {}).items()
        if not p.get("nodata")
    } or None
    group_by_code = None
    if iso != "ERCOT":
        group_by_code = rcf._fleet_group_by_code(iso, get_iso_config(iso), year)
    frame = rcf._btm_frame(
        year,
        "P1",
        load_monthly_generation(),
        btm_backfill_year=int(backfill) if backfill else None,
        campd_active=campd_active,
        iso=iso,
        group_by_code=group_by_code,
    )
    if frame.empty:
        return {}
    return {
        str(k): float(v) for k, v in zip(frame["klass"], frame["btm_twh"]) if v > 0.0
    }


def _patch_bench_part(
    iso: str, year: int, intensity: dict, cov: float, btm: dict, dry_run: bool
) -> bool:
    """Re-base the actual CO2 in one bench part; return whether it was written.

    Full-plant basis: ``classFull`` (grid-delivered) plus the per-class BTM
    add-back reconstructs the full EIA-923 class totals the intensities were
    weighted on. ``btmClass``/``basis`` mark the part as rubric-v2.3.
    """
    part = BENCH_DIR / iso / f"{year}.json.gz"
    if not part.exists():
        return False
    obj = json.loads(gzip.decompress(part.read_bytes()))
    class_full = obj.get("bench", {}).get("classFull", {})
    full = {
        str(k): round(float(class_full.get(k, 0.0)) + float(btm.get(k, 0.0)), 4)
        for k in sorted(set(class_full) | set(btm))
    }
    actual_mt, by = rch._fossil_co2(full, intensity)
    obj["bench"]["co2"] = {
        "egrid": actual_mt,
        "byClass": by,
        "intensity": {k: round(v, 5) for k, v in intensity.items()},
        "covPct": cov,
        "btmClass": {k: round(v, 4) for k, v in sorted(btm.items())},
        "basis": "full-plant",
    }
    if not dry_run:
        rb._write_bench_part(iso, year, obj.get("meta", {}), obj["bench"])
    return True


def _patch_run(
    rec: dict,
    intensity_by_year: dict[int, dict],
    btm_by_year: dict[int, dict],
    dry_run: bool,
) -> int:
    """Re-base the model CO2 in one run payload; return years patched."""
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
        btm = btm_by_year.get(year, {})
        # build_payload applies the ROUNDED (stored) intensity to the model side.
        rounded = {k: round(v, 5) for k, v in intensity.items()}
        gm = ypay.get("gmModel") or {}
        gm_full = {
            str(k): round(float(gm.get(k, 0.0)) + float(btm.get(k, 0.0)), 4)
            for k in sorted(set(gm) | set(btm))
        }
        model_mt, by = rch._fossil_co2(gm_full, rounded)
        ypay["co2"] = {"model": model_mt, "byClass": by, "basis": "full-plant"}
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
        years = sorted({int(y) for r in recs for y in r.get("years", [])})
        intensity_by_year: dict[int, dict] = {}
        cov_by_year: dict[int, float] = {}
        btm_by_year: dict[int, dict] = {}
        for year in years:
            bench_obj = _bench_part(iso, year)
            if bench_obj is None:
                continue
            anchor = _anchor_rec(recs, year)
            co2 = bench_obj.get("bench", {}).get("co2") or {}
            if co2.get("intensity"):
                intensity_by_year[year] = dict(co2["intensity"])
                cov_by_year[year] = float(co2.get("covPct", 0.0))
            elif anchor is not None:
                res = _intensity_for(REPO / anchor["bundle"], year)
                if res is None:
                    logger.warning(
                        "%s %s: no committed intensity or EIA-923", iso, year
                    )
                    continue
                intensity_by_year[year], cov_by_year[year] = res
            else:
                continue
            btm_by_year[year] = _btm_class(iso, year, anchor, bench_obj)
        if not intensity_by_year:
            logger.info("%s: no year could be anchored", iso)
            continue
        n_bench = sum(
            _patch_bench_part(
                iso,
                y,
                intensity_by_year[y],
                cov_by_year[y],
                btm_by_year.get(y, {}),
                args.dry_run,
            )
            for y in intensity_by_year
        )
        n_runs = sum(
            _patch_run(rec, intensity_by_year, btm_by_year, args.dry_run) > 0
            for rec in recs
        )
        years_lbl = ", ".join(
            f"{y}(btm {sum(btm_by_year.get(y, {}).values()):.1f} TWh)"
            for y in sorted(intensity_by_year)
        )
        logger.info(
            "%s: re-based years %s -> %d bench parts, %d run payloads%s",
            iso,
            years_lbl,
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
