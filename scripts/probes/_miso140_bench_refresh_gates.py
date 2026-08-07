"""miso-140 — verify the committed MISO bench ``*_lw`` refresh (queue item 1).

Runs the three non-scorer gates of
``results/calibration/PREREG-miso140-bench-refresh-verification-2026-08-07.md``:

* **G-1** — recompute ``rt_lw``/``da_lw`` and both 12-month vectors for MISO
  2023-2025 from the committed ``actual_lmp_hourly_MISO.parquet`` times the
  model's own ``eia_loader.load_demand``, through the deriver's OWN
  ``_lw_fields``/``_lw_stats`` path, and compare against the committed bench
  parts at HEAD. PASS iff every scalar and all 72 monthly entries reproduce to
  the deriver's 2-dp rounding.
* **G-2** — the model-side demand vintage. Compare the keeper bundle's committed
  ``hourly/system_<year>.parquet`` demand against ``load_demand`` at HEAD. The
  diagnosed defect was a vintage MISMATCH, so refreshing the actual side only
  closes it if the model side is on today's vintage too.
* **G-3** — scope completeness: which committed MISO *comparator* artifacts
  resolve through ``load_demand`` at all.

Committed artifacts only; no LP is solved and nothing is written outside
``results/calibration/_miso140_bench_refresh_gates.json``. Rule 22: 2023-2025.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
# BOTH entries are load-bearing, and the second one is not obvious. ``ROOT/scripts``
# resolves ``data.derive_actual_lmp`` (the deriver's own path, G-1). ``ROOT`` itself
# resolves ``scripts.data.curate_zonal_shares``, which ``eia930.zonal_shares.
# _zonal_shares_from_raw`` imports as the RAW fallback whenever ``data/clean`` is
# absent (it is gitignored, so it is absent in a fresh clone). Without ``ROOT`` that
# import fails, ``load_zonal_shares`` returns None **silently**, and ``load_demand``
# drops to the static Gold-Book ``load_share`` — same ISO total, different zonal
# split. Measured at miso-140: that silent fallback moves MISO's per-zone hourly
# demand by up to 7.2 GW while leaving the annual ISO energy identical to the MWh.
# ``run_calibration_full.py:74`` and ``calibration_verdict.py:51`` both insert ROOT,
# so the solve and scoring paths are unaffected; ad-hoc probes are the exposure.
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

YEARS = (2023, 2024, 2025)
ISO = "MISO"
KEEPER_BUNDLE = ROOT / "results" / "calibration" / "miso132_ccmin_B"
BENCH_DIR = ROOT / "frontend" / "data" / "backcast" / "bench" / ISO
OUT = ROOT / "results" / "calibration" / "_miso140_bench_refresh_gates.json"

# The deriver's own rounding grain: ``_lw_stats``/``_lw_fields`` round to 2 dp,
# so an exact reproduction is |delta| <= 0.005 on the unrounded comparison.
ROUND_TOL = 0.005


def committed_bench(year: int) -> dict:
    """The committed bench ``avgLMP`` block for one MISO year."""
    with gzip.open(BENCH_DIR / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["avgLMP"]


def gate_1() -> dict:
    """G-1 — independent recomputation of the committed ``*_lw`` fields."""
    from data.derive_actual_lmp import _lw_fields  # deriver's own path

    rows, ok = [], True
    for year in YEARS:
        got = _lw_fields(ISO, year)
        have = committed_bench(year)
        if got is None:
            rows.append({"year": year, "error": "deriver returned None"})
            ok = False
            continue
        for kind in ("rt", "da"):
            key = f"{kind}_lw"
            recomputed, committed = float(got[key]), float(have[key])
            d = recomputed - committed
            mon_r = got[f"{kind}_lw_mon"]
            mon_c = have[f"{kind}_lw_mon"]
            mon_bad = [
                {"month": i + 1, "recomputed": mon_r[i], "committed": mon_c[i]}
                for i in range(12)
                if mon_r[i] is None
                or mon_c[i] is None
                or abs(float(mon_r[i]) - float(mon_c[i])) > ROUND_TOL
            ]
            passed = abs(d) <= ROUND_TOL and not mon_bad
            ok &= passed
            rows.append(
                {
                    "year": year,
                    "basis": kind.upper(),
                    "recomputed": recomputed,
                    "committed": committed,
                    "delta": round(d, 6),
                    "monthly_mismatches": mon_bad,
                    "pass": passed,
                }
            )
    return {"gate": "G-1 refresh correctness", "pass": ok, "rows": rows}


def gate_2() -> dict:
    """G-2 — is the MODEL side on the same demand vintage as the refreshed actual?"""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    from market_sim.data.eia930 import load_zonal_shares

    cfg = get_iso_config(ISO)
    zone_names = [z.name for z in cfg.zones]
    # Fail loudly rather than compare against the static-share fallback: a silent
    # None here is what made this gate read a spurious 7 GW mismatch on its first
    # run (see the sys.path note at module scope).
    for y in YEARS:
        if load_zonal_shares(ISO, y, zone_names) is None:
            raise RuntimeError(
                f"measured zonal shares unavailable for {ISO} {y} — load_demand "
                "would fall back to static load_share and this gate would compare "
                "two different zonal splits"
            )
    rows, ok = [], True
    for year in YEARS:
        head = np.asarray(load_demand(ISO, year, cfg), dtype=float)
        sysp = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"system_{year}.parquet")
        sysp = sysp[sysp["pass"] == "P1"]
        # Rebuild the bundle's (n_zones, T) demand in the config's zone order.
        piv = (
            sysp.pivot_table(
                index="zone", columns="hour", values="demand", aggfunc="first"
            )
            .reindex(zone_names)
            .to_numpy(dtype=float)
        )
        n = min(head.shape[1], piv.shape[1])
        a, b = head[:, :n], piv[:, :n]
        # Zones the model carries but the loader does not populate (external
        # nodes) are all-zero on both sides; NaN on the bundle side means the
        # zone is absent from the sidecar entirely.
        absent = [z for z, r in zip(zone_names, piv) if np.isnan(r).all()]
        m = ~np.isnan(b)
        max_abs = float(np.nanmax(np.abs(a[m] - b[m]))) if m.any() else float("nan")
        e_head, e_bundle = float(a[m].sum()), float(b[m].sum())
        rel = (e_head - e_bundle) / e_bundle if e_bundle else float("nan")
        passed = abs(rel) <= 1e-4 and max_abs < 1.0
        ok &= passed
        rows.append(
            {
                "year": year,
                "hours_compared": int(n),
                "zones_absent_from_sidecar": absent,
                "annual_energy_head_MWh": round(e_head, 3),
                "annual_energy_bundle_MWh": round(e_bundle, 3),
                "rel_energy_delta": rel,
                "max_abs_hourly_delta_MW": max_abs,
                "pass": passed,
            }
        )
    return {"gate": "G-2 model-side vintage", "pass": ok, "rows": rows}


def gate_3() -> dict:
    """G-3 — every committed MISO *comparator* that resolves through load_demand."""
    import re

    hits = []
    for p in sorted((ROOT / "scripts").rglob("*.py")):
        if "probes" in p.parts or "archive" in p.parts:
            continue
        txt = p.read_text(errors="ignore")
        if re.search(r"\bload_demand\b", txt):
            hits.append(str(p.relative_to(ROOT)))
    # Classification is stated in the PREREG's candidate set; a COMPARATOR is an
    # artifact the model is SCORED AGAINST, an INPUT is one the model dispatches
    # ON. Only the former can carry a scorer-side vintage mismatch.
    kind = {
        "scripts/data/derive_actual_lmp.py": "COMPARATOR (actual_lmp.json *_lw -> bench avgLMP)",
        "scripts/data/build_calibration_reference.py": "INPUT (calibration_reference.json demand totals)",
        "scripts/data/derive_import_tranches.py": "INPUT (import tranche sizing)",
        "scripts/data/curate_zonal_shares.py": "INPUT (zonal demand shares)",
        "scripts/data/curate_demand_profile.py": "INPUT (the demand series itself)",
        "scripts/run_calibration_full.py": "INPUT (solve driver)",
        "scripts/run_calibration.py": "INPUT (solve driver)",
    }
    tail = (ROOT / "scripts" / "data" / "derive_actual_tail.py").read_text(
        errors="ignore"
    )
    comparators = [h for h in hits if kind.get(h, "").startswith("COMPARATOR")]
    return {
        "gate": "G-3 scope completeness",
        "pass": len(comparators) == 1 and "load_demand" not in tail,
        "load_demand_call_sites": [{"path": h, "role": kind.get(h, "OTHER")} for h in hits],
        "demand_weighted_comparators": comparators,
        "actual_tail_uses_load_demand": "load_demand" in tail,
    }


def main() -> None:
    res = {"session": "miso-140", "iso": ISO, "years": list(YEARS)}
    for fn in (gate_1, gate_2, gate_3):
        g = fn()
        res[g["gate"].split()[0]] = g
        print(f"{g['gate']}: {'PASS' if g['pass'] else 'FAIL'}")
        print(json.dumps(g, indent=2, default=str))
        print()
    OUT.write_text(json.dumps(res, indent=2, default=str) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
