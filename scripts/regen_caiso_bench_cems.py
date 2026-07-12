"""Regenerate the CAISO bench parts on the CEMS-anchored benchmark basis (no LP solve).

Owner-signed rework 2026-07-12 (results/calibration/
FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md §5): the CISO EIA-930
"Natural Gas" cell carries a growing noon-peaked, solar-shaped block no gas
fleet produced (onset ~2024-05), and the G-21 combined reconcile was scaling
the whole CAISO fossil ``classFull`` up to it (×1.104/×1.211/×1.444 in
2023/24/25). This script rebuilds each year's actual-side benchmark exactly as
``render_calibration_html.build_payload`` now does — same frames, same
reconcile — with the CEMS-anchor fields written into ``bench.e930`` so the
reconcile caps at the measured fossil total:

* ``gas_cems_grid``  — CEMS bench-gas net (committed ``plants[].c_ann``,
  CAMPD hourly-integrated × parasitic factor) minus the measured BTM CHP host
  supply, i.e. the grid-delivered CEMS gas block. Coverage basis = the
  committed bench part's own plant map (the render's ``grp_p``), mirroring the
  ``coal_cems`` convention.
* ``gas_cogen_grid`` — the EIA-923 non-CEMS gas-class block (plants with no
  usable CAMPD series), grid-delivered; the preliminary 2025 vintage carries
  the 2024 (latest complete) block — the prelim survey under-counts exactly
  these cogens.
* ``fossil_cems_grid`` — gas anchor + the 923 coal grid block: the combined
  vintage-reconcile cap (``reconcile_vintage_classes``).

It then re-runs the (now capped) reconcile to produce the honest
``classFull``, and rebuilds the 2025 ``co2`` actual on the same
complete-coverage basis (fossil class generation scaled to the CEMS-anchored
FULL-plant total before the committed per-class intensities — the caiso-76
FINDING §4 vintage-understatement repair). 2023/24 CO2 actuals are booked
complete-vintage EIA-923 and are untouched. Every other bench field (plants,
avgLMP, storage, the raw e930 cells) is left byte-for-byte; the write uses the
same deterministic gzip (compresslevel=9, mtime=0) as
``render_backcast._write_bench_part``, so re-running is idempotent.

Needs only committed raw reference data (EIA-923 / EIA-930 / CAMPD /
completeness parts) — no dispatch, no solve — so it reproduces the corrected
benchmark on any runner. Guard rails fail LOUDLY if (a) the UNCAPPED
recompute does not reproduce the committed classFull (input parity), or (b)
the CEMS gas block drifts from the FINDING §3 measured values.
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
from market_sim.data.fleet import apply_other_fossil_scoring  # noqa: E402
from market_sim.results.calibration import (  # noqa: E402
    EIA930_SOURCE,
    actuals_source,
)

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BENCH_DIR = _REPO / "frontend" / "data" / "backcast" / "bench" / ISO
GAS_GRPS = set(rch._GAS_GROUPS)
COAL_GRPS = set(rch._COAL_GROUPS)

# FINDING §3 measured CEMS bench-gas values (TWh, CAMPD net, bench coverage);
# the recompute FAILS LOUDLY outside these windows so a data mismatch on a
# runner can never silently commit a wrong anchor.
_CEMS_GUARD = {2023: (62.4, 63.4), 2024: (55.0, 56.0), 2025: (45.6, 46.6)}
# Committed-classFull reproduction tolerance (TWh) for the UNCAPPED recompute:
# covers rounding + the sub-0.03 e923-snapshot drift observed on 2023.
_PARITY_TOL = 0.06


def main() -> int:
    gen = rcf.load_monthly_generation()
    parasitic = rcf._parasitic_factor_map()
    cfg = get_iso_config(ISO)
    cogen_by_year: dict[int, tuple[float, float]] = {}  # year -> (grid, full)

    for year in YEARS:
        group_by_code = rcf._fleet_group_by_code(ISO, cfg, year)
        campd_year = rcf._campd_hourly_frame(year, ISO, parasitic, HOURS)
        campd_active = set(
            campd_year.groupby("plant_id")["net_mw"]
            .sum()
            .pipe(lambda s: s[s > 0].index.astype(int))
        )
        e930 = rcf._eia930_frame(year, ISO, cfg)
        e923 = apply_other_fossil_scoring(
            rcf._benchmark_eia923_frame(
                year, gen, ISO, campd_year, group_by_code, e930
            ),
            year,
            plant_col="plant_id",
        )
        e923_cls = e923.groupby("klass")["annual_mwh"].sum()
        btm = rcf._btm_frame(
            year,
            "P1",
            gen,
            btm_backfill_year=None,
            campd_active=campd_active,
            iso=ISO,
            group_by_code=group_by_code,
        )
        btm_cls = dict(zip(btm["klass"].astype(str), btm["btm_twh"].astype(float)))

        part_path = BENCH_DIR / f"{year}.json.gz"
        obj = json.loads(gzip.decompress(part_path.read_bytes()))
        bplants = obj["bench"]["plants"]
        old_cf = obj["bench"]["classFull"]
        e930d = dict(obj["bench"]["e930"])

        # ---- CEMS-anchor fields (bench-part coverage basis) ----
        gas_bench = [
            p for p in bplants.values() if p["group"] in GAS_GRPS and not p["nodata"]
        ]
        cems_full = sum(float(p["c_ann"]) for p in gas_bench)
        cems_grid = cems_full - sum(float(p["btm"]) for p in gas_bench)
        lo, hi = _CEMS_GUARD[year]
        if not (lo <= cems_full <= hi):
            raise SystemExit(
                f"GUARD FAIL {ISO} {year}: CEMS bench-gas {cems_full:.2f} TWh "
                f"outside [{lo}, {hi}] (FINDING §3) — data mismatch?"
            )
        cems_ids = {int(c) for c, p in bplants.items() if not p["nodata"]}
        nc = e923[
            e923["klass"].isin(GAS_GRPS) & ~e923["plant_id"].astype(int).isin(cems_ids)
        ]
        cogen_full = float(nc["annual_mwh"].sum()) / 1e6
        cogen_grid = sum(
            float(r["annual_mwh"])
            / 1e6
            * (1.0 - rch._btm_share(int(r["plant_id"]), str(r["klass"]), ISO))
            for _, r in nc.iterrows()
        )
        if rch._eia923_gas_family_incomplete(ISO, year):
            prior = [y for y in sorted(cogen_by_year) if y < year]
            if prior:
                cogen_grid, cogen_full = cogen_by_year[prior[-1]]
        else:
            cogen_by_year[year] = (cogen_grid, cogen_full)
        coal_grid = sum(
            float(e923_cls.get(c, 0.0)) / 1e6 - float(btm_cls.get(c, 0.0))
            for c in COAL_GRPS
            if c in e923_cls.index
        )
        coal_full = sum(
            float(e923_cls.get(c, 0.0)) / 1e6 for c in COAL_GRPS if c in e923_cls.index
        )

        # ---- classFull recompute, exactly as the render builds it ----
        cf = {
            str(g): round(float(v) / 1e6 - float(btm_cls.get(str(g), 0.0)), 4)
            for g, v in e923_cls.items()
        }
        for vre in ("wind", "solar"):
            if actuals_source(vre, ISO) == EIA930_SOURCE:
                if vre in cf and vre in e930d:
                    cf[vre] = round(float(e930d[vre]), 4)
            elif vre in cf:
                e930d[vre] = round(float(cf[vre]), 4)
        pre = dict(cf)

        # Parity guard: the UNCAPPED reconcile must reproduce the committed
        # part (proves frame parity on this runner) before the cap is applied.
        legacy = dict(pre)
        legacy_e930 = {
            k: v
            for k, v in e930d.items()
            if k not in ("gas_cems_grid", "gas_cogen_grid", "fossil_cems_grid")
        }
        rch.reconcile_vintage_classes(legacy, legacy_e930, ISO)
        for k, v_old in old_cf.items():
            if k not in legacy:
                continue  # run-scoped class (e.g. OTHER_FOSSIL) — carried below
            if abs(float(legacy[k]) - float(v_old)) > _PARITY_TOL:
                raise SystemExit(
                    f"GUARD FAIL {ISO} {year}: uncapped recompute {k} "
                    f"{legacy[k]:.4f} vs committed {v_old:.4f} — input parity "
                    "broken; refusing to write."
                )

        e930d["gas_cems_grid"] = round(cems_grid, 3)
        e930d["gas_cogen_grid"] = round(cogen_grid, 3)
        e930d["fossil_cems_grid"] = round(cems_grid + cogen_grid + coal_grid, 3)
        rch.reconcile_vintage_classes(cf, e930d, ISO)

        # Uniform-scale bookkeeping for classes the run-scoped transform put in
        # the committed part but the raw recompute lacks (2023 OTHER_FOSSIL):
        # carry committed / old_scale * new_scale so they stay on the same
        # honest level as their family.
        fossil = [g for g in (*GAS_GRPS, *COAL_GRPS, "OTHER_FOSSIL")]
        old_scale = (
            float(old_cf["CC_REGULAR"]) / float(pre["CC_REGULAR"])
            if pre.get("CC_REGULAR")
            else 1.0
        )
        new_scale = (
            float(cf["CC_REGULAR"]) / float(pre["CC_REGULAR"])
            if pre.get("CC_REGULAR")
            else 1.0
        )
        new_cf = {}
        for k in old_cf:
            if k in cf:
                new_cf[k] = cf[k]
            elif k in fossil:
                new_cf[k] = round(float(old_cf[k]) / old_scale * new_scale, 4)
            else:
                new_cf[k] = old_cf[k]
        for k in cf:
            new_cf.setdefault(k, cf[k])
        obj["bench"]["classFull"] = new_cf
        obj["bench"]["e930"] = e930d

        # ---- 2025 CO2 actual: complete-coverage (full-plant) rebuild ----
        co2_note = ""
        if rch._eia923_gas_family_incomplete(ISO, year):
            co2 = obj["bench"]["co2"]
            intensity = {k: float(v) for k, v in co2["intensity"].items()}
            class_full = {str(g): round(float(v) / 1e6, 4) for g, v in e923_cls.items()}
            anchor_full = cems_full + cogen_full + coal_full
            fcl = [g for g in class_full if g in fossil]
            cur_full = sum(class_full[g] for g in fcl)
            if cur_full > 0.0 and not (
                rch._VINTAGE_RECONCILE_FRAC * anchor_full
                <= cur_full
                <= anchor_full / rch._VINTAGE_RECONCILE_FRAC
            ):
                sc = anchor_full / cur_full
                for g in fcl:
                    class_full[g] = round(class_full[g] * sc, 4)
            old_egrid = co2["egrid"]
            new_egrid, new_by = rch._fossil_co2(class_full, intensity)
            co2["egrid"] = new_egrid
            co2["byClass"] = new_by
            co2_note = f"; co2 egrid {old_egrid} -> {new_egrid}"

        part_path.write_bytes(
            gzip.compress(json.dumps(obj).encode(), compresslevel=9, mtime=0)
        )
        print(
            f"{ISO} {year}: fossil_cems_grid {e930d['fossil_cems_grid']} "
            f"(cems {cems_grid:.2f} + cogen {cogen_grid:.2f} + coal {coal_grid:.2f}); "
            f"CC_REGULAR {old_cf.get('CC_REGULAR', 0.0):.2f} -> "
            f"{new_cf['CC_REGULAR']:.2f}{co2_note}"
        )
    print("regen_caiso_bench_cems: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
