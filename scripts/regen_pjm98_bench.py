"""Regenerate the PJM bench parts on the G-21 corrected benchmark basis (no LP solve).

Recomputes each year's ``classFull`` exactly as
``render_calibration_html.build_payload`` does — the fixed unit-class CAMPD
backfill (``_benchmark_eia923_frame`` + ``_fleet_group_by_code``, G-21 defect b)
minus the behind-the-meter CHP hold-out (``_btm_frame``, a pure function of
committed inputs), the variable-renewable EIA-930 override, then the fixed
combined-family reconcile (``reconcile_vintage_classes``, G-21 defect a) — and
splices ONLY ``classFull`` into the committed
``frontend/data/backcast/bench/PJM/<year>.json.gz`` part. Every other bench
field (e930, avgLMP, co2, plants, monthly, storage) is left byte-for-byte, and
the write uses the same deterministic gzip (compresslevel=9, mtime=0) as
``render_backcast._write_bench_part``, so re-running is idempotent.

This is the actual-side of the #2049 keeper re-score: it needs only the
committed EIA-923 / EIA-930 / CAMPD / LMP reference data (no dispatch, no
transfer-interface-limits), so it reproduces the corrected benchmark on any
runner without a solve. See docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO / "src", _REPO, _REPO / "scripts"):
    sys.path.insert(0, str(_p))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, str(_REPO / rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rcf = _load("rcf", "scripts/run_calibration_full.py")
rch = _load("rch", "scripts/render_calibration_html.py")

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.results.calibration import (  # noqa: E402
    EIA930_SOURCE,
    actuals_source,
)

ISO = "PJM"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BTM_BACKFILL_YEAR = 2024  # pjm-98 meta.btm_backfill_year
BENCH_DIR = _REPO / "frontend" / "data" / "backcast" / "bench" / ISO

# G-21 §2 corrected-basis guard rails (CC_REGULAR is the headline class the fix
# moves); the run FAILS LOUDLY if the recompute drifts, so a data mismatch on a
# runner can never silently commit a wrong benchmark.
_GUARD = {2023: (325.0, 326.5), 2024: (334.0, 336.5)}


def main() -> int:
    gen = rcf.load_monthly_generation()
    parasitic = rcf._parasitic_factor_map()
    cfg = get_iso_config(ISO)

    for year in YEARS:
        group_by_code = rcf._fleet_group_by_code(ISO, cfg, year)
        campd_year = rcf._campd_hourly_frame(year, ISO, parasitic, HOURS)
        campd_active = set(
            campd_year.groupby("plant_id")["net_mw"]
            .sum()
            .pipe(lambda s: s[s > 0].index.astype(int))
        )
        e930 = rcf._eia930_frame(year, ISO, cfg)
        e923 = rcf._benchmark_eia923_frame(
            year, gen, ISO, campd_year, group_by_code, e930
        )
        e923_cls = e923.groupby("klass")["annual_mwh"].sum()
        btm = rcf._btm_frame(
            year,
            "P1",
            gen,
            btm_backfill_year=BTM_BACKFILL_YEAR,
            campd_active=campd_active,
            iso=ISO,
            group_by_code=group_by_code,
        )
        btm_cls = dict(zip(btm["klass"].astype(str), btm["btm_twh"].astype(float)))

        part_path = BENCH_DIR / f"{year}.json.gz"
        obj = json.loads(gzip.decompress(part_path.read_bytes()))
        e930d = dict(obj["bench"]["e930"])  # committed EIA-930 (unchanged by the fix)
        old_cf = obj["bench"]["classFull"]

        cf = {
            str(g): round(float(v) / 1e6 - float(btm_cls.get(str(g), 0.0)), 4)
            for g, v in e923_cls.items()
        }
        for vre in (
            "wind",
            "solar",
        ):  # variable renewables ride the EIA-930 grid series
            if actuals_source(vre, ISO) == EIA930_SOURCE:
                if vre in cf and vre in e930d:
                    cf[vre] = round(float(e930d[vre]), 4)
            elif vre in cf:
                e930d[vre] = round(float(cf[vre]), 4)
        rch.reconcile_vintage_classes(cf, e930d, ISO)

        lo, hi = _GUARD.get(year, (0.0, 1e9))
        cc = cf.get("CC_REGULAR", 0.0)
        if not (lo <= cc <= hi):
            raise SystemExit(
                f"GUARD FAIL PJM {year}: CC_REGULAR classFull {cc:.2f} outside "
                f"[{lo}, {hi}] — corrected benchmark did not reproduce (data mismatch?)"
            )

        # Replace classFull in place, preserving existing key order.
        new_cf = {k: cf.get(k, old_cf[k]) for k in old_cf}
        for k in cf:
            new_cf.setdefault(k, cf[k])
        obj["bench"]["classFull"] = new_cf
        part_path.write_bytes(
            gzip.compress(json.dumps(obj).encode(), compresslevel=9, mtime=0)
        )
        print(
            f"PJM {year}: classFull spliced ({len(new_cf)} classes), "
            f"CC_REGULAR {old_cf.get('CC_REGULAR', 0.0):.2f} -> {new_cf['CC_REGULAR']:.2f}"
        )
    print("regen_pjm98_bench: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
