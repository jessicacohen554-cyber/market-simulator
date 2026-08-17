"""miso-161 — RE-RUN of the pre-registered miso-156 three-channel decomposition
on the NEW keeper ``2026-08-16-miso-160-wefor-shape`` (bundle ``miso160_wefor_B``).

NO SOLVE. NO NEW INSTRUMENT. This wrapper executes the miso-156 probe
(`scripts/probes/_miso156_c3a_decomposition.py`, pre-registered at
``PREREG-miso156-c3a-three-channel-decomposition-2026-08-13.md``, pushed
``162a51d`` blob ``7f124d18``) exactly as written, with the THREE repoints its
own T-1 discipline prescribes for a keeper change — nothing else is altered:

1. **BUNDLE** -> ``results/calibration/miso160_wefor_B`` (both the probe's own
   module global and the ``_miso134`` helper it drives), asserted after set.
2. **V1 targets** -> the NEW keeper's registered C3a. Computed from the
   committed bundle + bench by the scorer's own statistic (demand-weighted P1
   price over the six carry zones vs ``bench.avgLMP.rt_lw``):
   **+0.6165 / -4.7978 / -12.5201 %** (published headline +0.6 / -4.8 / -12.5,
   FINDING-miso160-measured-summer-wefor-shape-2026-08-16.md section 4).
   The +/-0.5 pp V1 tolerance is unchanged.
3. **OUT** -> ``results/calibration/_miso161_c3a_decomposition.json``.

V4 (n_gen 2929/2923/2923) is UNCHANGED — miso-160's own V3 gate measured the
identical fleet on both arms. V2's targets remain miso-155's committed floor
record: the miso-160 arm changes summer availability, so V2 is EXPECTED to
drift there; it is report-only for the decomposition (the probe gates the
decomposition on V1+V4, and the FLOORS_OFF twin brackets any floor error —
miso-156 section 3 measured 0.0000 $/MWh across all 27 cells).

The keeper config rebuilt from ``miso160_wefor_B/run_config.json`` carries
``summer_wefor_share_override = 1.0599``, so the availability matrix this
probe assembles is the ARMED one — the decomposition therefore measures the
residual Delta-1/Delta-2/Delta-3 AFTER the measured seasonal outage shape.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds neither marker.

Usage::

    PYTHONPATH=$PWD:$PWD/src .venv/bin/python \\
        scripts/probes/_miso161_c3a_decomposition.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso156_c3a_decomposition as _m156  # noqa: E402

# T-1: repoint BOTH module globals to THIS session's keeper, then assert.
BUNDLE = REPO / "results/calibration/miso160_wefor_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE
_m156.BUNDLE = BUNDLE
assert _m134.BUNDLE == BUNDLE and _m156.BUNDLE == BUNDLE, "T-1: repoint failed"

# V1: the NEW keeper's registered C3a (scorer's own statistic on the committed
# bundle + bench; published +0.6 / -4.8 / -12.5 %). Tolerance unchanged.
_m156.V1_PUBLISHED_C3A = {2023: 0.006165, 2024: -0.047978, 2025: -0.125201}

# The output record travels under this session's id.
OUT = REPO / "results/calibration/_miso161_c3a_decomposition.json"


def main() -> dict:
    """The miso-156 main loop verbatim, MINUS its S-FLOORBLIND control-demand
    leg: that leg read ``miso155_p0_C``'s hourly sidecars to root-cause
    miso-156's own V2 miss, and those sidecars are no longer on disk (the
    bundle keeps only meta/metrics/run_config after pruning). It was
    instrumentation for a question this re-run does not ask; everything the
    decomposition itself needs is driven through ``_m156``'s own functions.
    """
    import json

    cfg = _m156.keeper_config()
    out = {
        "prereg": "PREREG-miso156-c3a-three-channel-decomposition-2026-08-13.md",
        "prereg_commit": "162a51d", "prereg_blob": "7f124d18",
        "reran_for": "miso-161",
        "keeper": "2026-08-16-miso-160-wefor-shape",
        "bundle": BUNDLE.name, "years": {},
    }
    for year in _m156.YEARS:
        mb = _m156.model_year(cfg, year)
        v4 = {
            "n_gen": len(mb["fleet"]), "published_n_gen": _m156.V4_NGEN[year],
            "carry_zones": len(mb["carry_idx"]),
            "pass": bool(
                len(mb["fleet"]) == _m156.V4_NGEN[year]
                and len(mb["carry_idx"]) == 6
            ),
        }
        v2 = _m156.v2_floor_gate(mb, year)
        v1 = _m156.v1_c3a_gate(mb, year)
        rec = {"V4_fleet": v4, "V2_floors": v2, "V1_c3a": v1}
        if v1["pass"] and v4["pass"]:
            rec["decomposition"] = _m156.decompose(mb, year)
            mb0 = _m156.model_year(cfg, year, apply_floors=False)
            rec["decomposition_FLOORS_OFF"] = _m156.decompose(mb0, year)
        else:
            rec["decomposition"] = {"SKIPPED": "validity gate failed"}
        out["years"][str(year)] = rec
        print(f"[{year}] V4 {v4['pass']}  V2 {v2['pass']} "
              f"(ct {v2['ct_floor_mwh']/1e6:.4f} TWh vs "
              f"{v2['m155_ct_floor_mwh']/1e6:.4f}, "
              f"{100*(v2['ct_floor_mwh']/v2['m155_ct_floor_mwh']-1):+.2f}%, "
              f"rows {v2['ct_rows_floored']}/{v2['m155_ct_rows_floored']})  "
              f"V1 {v1['pass']} ({v1['c3a_pct']:+.2f}% vs "
              f"{v1['published_c3a_pct']:+.2f}%)", flush=True)
        d = rec["decomposition"]
        if "annual" in d:
            for grain in ("annual", "jun_jul", "top200"):
                a = d[grain]
                print(f"    {grain:8s} gap {a['gap_usd_mwh']:+7.3f}  "
                      f"D1 {a['D1_identity_usd_mwh']:+7.3f} "
                      f"({100*(a['D1_share'] or 0):5.1f}%)  "
                      f"D2 {a['D2_costlevel_usd_mwh']:+7.3f} "
                      f"({100*(a['D2_share'] or 0):5.1f}%)  "
                      f"D3 {a['D3_abovecost_usd_mwh']:+7.3f} "
                      f"({100*(a['D3_share'] or 0):5.1f}%)", flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
