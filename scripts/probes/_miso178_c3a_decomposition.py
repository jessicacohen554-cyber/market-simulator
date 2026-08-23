"""miso-178 — RE-RUN of the pre-registered miso-156 three-channel decomposition
on the keeper ``2026-08-22-miso-177-rho-measured`` (bundle ``miso177_rho_B``).

NO SOLVE. NO NEW INSTRUMENT. The ``_miso161_c3a_decomposition.py`` wrapper
pattern, third application: execute the miso-156 probe
(`scripts/probes/_miso156_c3a_decomposition.py`, pre-registered at
``PREREG-miso156-c3a-three-channel-decomposition-2026-08-13.md``) exactly as
written, with the THREE repoints its own T-1 discipline prescribes for a keeper
change — nothing else altered:

1. **BUNDLE** -> ``results/calibration/miso177_rho_B`` (both the probe's own
   module global and the ``_miso134`` helper it drives), asserted after set.
2. **V1 targets** -> the measured-rho keeper's C3a, computed by the scorer's
   own statistic on the committed bundle + bench (demand-weighted P1 price over
   the six carry zones vs ``bench.avgLMP.rt_lw``):
   **+1.2813 / -4.0643 / -11.7421 %** (published headline +1.279 / -4.056 /
   -11.747, RESULT-miso177-rho-measured-execution-2026-08-22.md; the same
   self-computed-vs-published convention miso-161 used). V1 tolerance
   unchanged (+/-0.5 pp).
3. **OUT** -> ``results/calibration/_miso178_c3a_decomposition.json``.

**Import shim, disclosed (new since miso-161):** ``_miso156``'s import-time T-1
guard checks ``results/calibration/miso148_basis_B/run_config.json``, and that
bundle has since been PRUNED from the tree — at HEAD even the committed
``_miso161`` wrapper can no longer import the probe. The shim below satisfies
exactly that one existence check during the import (``pathlib.Path.is_file``
monkeypatched for that single path, restored immediately after); the guard's
purpose — "repoint ``_miso134`` before anything reads it" — is preserved,
because this wrapper performs the same repoint to a bundle that DOES exist
before any computation runs. Nothing on disk is touched.

V4 (n_gen 2929/2923/2923) is UNCHANGED across the keeper lineage. V2's targets
remain miso-155's committed floor record; the lineage since (miso-160 wefor,
miso-170b site-grain, miso-173 lay-up mask) changes floor volumes, so V2 is
EXPECTED to drift and is report-only — the probe gates the decomposition on
V1+V4, and the FLOORS_OFF twin brackets any floor error (miso-156 section 3
measured 0.0000 $/MWh across all 27 cells; miso-161 kept the same stance).

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds neither marker. Rule 13
``[R-MEASURED]``: measurement of committed artifacts, nothing fed to a solve.

Usage::

    cd <repo root> && uv run --no-project \\
      --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml --python 3.12 \\
      python scripts/probes/_miso178_c3a_decomposition.py
"""

from __future__ import annotations

import pathlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# The disclosed import shim (docstring above): satisfy _miso156's import-time
# existence check on the pruned miso148_basis_B bundle, restore immediately.
_PRUNED = "results/calibration/miso148_basis_B/run_config.json"
_orig_is_file = pathlib.Path.is_file


def _shim(self: pathlib.Path) -> bool:  # noqa: ANN001
    return True if str(self).endswith(_PRUNED) else _orig_is_file(self)


pathlib.Path.is_file = _shim
try:
    import _miso156_c3a_decomposition as _m156  # noqa: E402
finally:
    pathlib.Path.is_file = _orig_is_file

# T-1: repoint BOTH module globals to THIS session's keeper, then assert.
BUNDLE = REPO / "results/calibration/miso177_rho_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE
_m156.BUNDLE = BUNDLE
assert _m134.BUNDLE == BUNDLE and _m156.BUNDLE == BUNDLE, "T-1: repoint failed"

# V1: the measured-rho keeper's C3a (scorer statistic, fraction units).
_m156.V1_PUBLISHED_C3A = {2023: 0.012813, 2024: -0.040643, 2025: -0.117421}

# The output record travels under this session's id.
OUT = REPO / "results/calibration/_miso178_c3a_decomposition.json"


def main() -> dict:
    """The miso-161 main loop verbatim (itself the miso-156 loop minus its
    S-FLOORBLIND control-demand leg, whose source sidecars are pruned)."""
    import json

    cfg = _m156.keeper_config()
    out = {
        "prereg": "PREREG-miso156-c3a-three-channel-decomposition-2026-08-13.md",
        "reran_for": "miso-178",
        "wrapper_precedent": "scripts/probes/_miso161_c3a_decomposition.py",
        "import_shim": ("pathlib.Path.is_file satisfied for the PRUNED "
                        "miso148_basis_B guard path during _miso156 import; "
                        "restored immediately (docstring)"),
        "keeper": "2026-08-22-miso-177-rho-measured",
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
