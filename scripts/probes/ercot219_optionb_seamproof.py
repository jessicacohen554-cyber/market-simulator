#!/usr/bin/env python3
"""ercot-219 Option-B seam proof (PRECOMMIT-ercot219 §4) — no LP built.

Four assertions on real reconstructed fleets (``run_year(fleet_only=True)``,
the ercot-188 SP pattern):

* **SP-1 gate-off byte-identity ×3 years (array grain):** at HEAD with the
  three fields at their defaults, the ERCOT keeper bundle's reconstructed
  availability / pmax / min_gen / storage-vom fingerprints are byte-identical
  to the PRE-EDIT tree's (a worktree at the precommit commit dumps the
  baseline with ``--dump-fingerprints``). The FULL-SOLVE gate-off identity is
  the control replay itself (G-REPRO).
* **SP-1b stage-1 liveness (reported):** with stage 1 armed on the ERCOT
  bundle, availability CHANGES (the mechanism is live, not silently dead) and
  only tightens (max over rows/hours of armed − control ≤ 0).
* **SP-2 cross-ISO byte-identity, ARMED (all five non-ERCOT ISOs):** with all
  three booleans forced TRUE on each ISO's own registered-bundle recipe, the
  reconstructed fleet fingerprints are byte-identical to gate-off — the
  ``iso == "ERCOT"`` gates make the arm unreachable (rule 25).
* **SP-3 no-price-input audit:** the stage-1 loader's parquet reads are
  column-scoped to the named quantity columns in source text; the read /
  refused sets are re-asserted and written into the output.
* **SP-4 cache-key discipline:** pinned default key ``603c2498bf71d21d``
  unmoved; the armed ERCOT backcast key distinct.

Usage:
    # pre-edit baseline (run from a worktree at the pre-build commit):
    python scripts/probes/ercot219_optionb_seamproof.py \
        --dump-fingerprints /tmp/pre_edit_fp.json
    # full proof (run at HEAD):
    python scripts/probes/ercot219_optionb_seamproof.py \
        --baseline /tmp/pre_edit_fp.json \
        --out results/calibration/ercot219_seamproof.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

ERCOT_BUNDLE = REPO / "results/calibration/ercot215_decontam_B"
YEARS = (2023, 2024, 2025)
#: SP-2 panel: one CURRENT registered bundle per non-ERCOT ISO (the ercot-188
#: panel's bundles were pruned from the roster; these are the live ones).
#: READ-ONLY (rule 25): no other ISO's files are modified by this lane.
CROSS_ISO_BUNDLES: dict[str, str] = {
    "CAISO": "caiso200_h1_memberpanel",
    "PJM": "pjm158_novirt_B",
    "NYISO": "nyiso140_control",
    "NEISO": "neiso99_basis_A",
    "MISO": "miso160_wefor_A",
}
CROSS_ISO_YEAR = 2023
ARM = {
    "ercot_capability_reconciliation": True,
    "ercot_exhaustion_expectation": True,
    "ercot_storage_reservation_offer": True,
}
PINNED_DEFAULT_KEY = "603c2498bf71d21d"


def _sha(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _build(bundle: Path, year: int, **over) -> dict:
    """Reconstruct a bundle's fleet with no LP (bundle_fleet machinery)."""
    from scripts.lib.bundle_fleet import bundle_gas_price, full_run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    if over:
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"] = {**(kwargs["prb_overrides"] or {}), **over}
    return run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kwargs
    )


def _fingerprint(state: dict) -> dict:
    fa = state["fleet_arrays"]
    return {
        "availability_sha": _sha(fa.availability),
        "pmax_sha": _sha(fa.pmax),
        "min_gen_sha": _sha(fa.min_gen),
        "storage_vom_sha": _sha(np.asarray(state["storage"].vom, dtype=float)),
        "n_rows": int(fa.pmax.size),
        "total_pmax_mw": round(float(fa.pmax.sum()), 3),
        "avail_mean": round(float(fa.availability.mean()), 10),
    }


def sp1_gateoff_fingerprints() -> dict:
    return {str(y): _fingerprint(_build(ERCOT_BUNDLE, y)) for y in YEARS}


def sp1b_stage1_liveness() -> dict:
    out: dict = {}
    for y in YEARS:
        ctl = _build(ERCOT_BUNDLE, y)
        arm = _build(ERCOT_BUNDLE, y, ercot_capability_reconciliation=True)
        d = arm["fleet_arrays"].availability - ctl["fleet_arrays"].availability
        out[str(y)] = {
            "changed": bool(np.any(d != 0.0)),
            "max_delta": float(d.max()),  # tighten-only => <= 0
            "min_delta": float(d.min()),
            "tightened_row_hours": int((d < 0).sum()),
            "tighten_only_ok": bool(d.max() <= 1e-12),
        }
    return out


def sp2_cross_iso() -> dict:
    out: dict = {}
    for iso, name in CROSS_ISO_BUNDLES.items():
        bundle = REPO / "results/calibration" / name
        ctl = _fingerprint(_build(bundle, CROSS_ISO_YEAR))
        arm = _fingerprint(_build(bundle, CROSS_ISO_YEAR, **ARM))
        out[iso] = {
            "bundle": name,
            "control": ctl,
            "armed": arm,
            "byte_identical": ctl == arm,
        }
    return out


def sp3_no_price_input_audit() -> dict:
    src = (REPO / "src/market_sim/data/outages.py").read_text()
    basis = json.loads(
        (REPO / "results/calibration/ercot219_basis_phase0.json").read_text()
    )
    return {
        "loader_reads_column_scoped": {
            "ordc_parquet_rtolhsl_only": 'columns=["rtolhsl"]' in src,
            "hsl_parquet_wind_solar_only": 'columns=["wind_hsl_mw", "solar_hsl_mw"]'
            in src,
        },
        "mechanism_read": basis["mechanism_read"],
        "mechanism_refused": basis["mechanism_refused"],
    }


def sp4_cache_key() -> dict:
    from market_sim.config.scenarios import ScenarioConfig

    cfg = ScenarioConfig()
    base = cfg.with_overrides(mode="backcast")
    armed = base.with_overrides(**ARM)
    return {
        "default_key": cfg.cache_key(),
        "default_key_unmoved": cfg.cache_key() == PINNED_DEFAULT_KEY,
        "backcast_key": base.cache_key(),
        "armed_key": armed.cache_key(),
        "armed_distinct": armed.cache_key() != base.cache_key(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump-fingerprints", default=None, metavar="OUT")
    ap.add_argument("--baseline", default=None, metavar="PRE_EDIT_FP")
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/ercot219_seamproof.json")
    )
    args = ap.parse_args()

    if args.dump_fingerprints:
        fp = sp1_gateoff_fingerprints()
        Path(args.dump_fingerprints).write_text(json.dumps(fp, indent=1) + "\n")
        print(f"wrote {args.dump_fingerprints}")
        return 0

    head_fp = sp1_gateoff_fingerprints()
    sp1: dict = {"head_gateoff": head_fp}
    if args.baseline:
        base_fp = json.loads(Path(args.baseline).read_text())
        sp1["pre_edit"] = base_fp
        sp1["byte_identical_x3"] = all(
            head_fp[str(y)] == base_fp[str(y)] for y in YEARS
        )
    out = {
        "probe": "ercot219_optionb_seamproof",
        "charter": "PRECOMMIT-ercot219-option-b-phase1-2026-08-18.md §4",
        "sp1_gateoff": sp1,
        "sp1b_stage1_liveness": sp1b_stage1_liveness(),
        "sp2_cross_iso_armed": sp2_cross_iso(),
        "sp3_no_price_input": sp3_no_price_input_audit(),
        "sp4_cache_key": sp4_cache_key(),
    }
    ok = (
        sp1.get("byte_identical_x3", None) in (True, None)
        and all(v["byte_identical"] for v in out["sp2_cross_iso_armed"].values())
        and all(v["tighten_only_ok"] for v in out["sp1b_stage1_liveness"].values())
        and all(v["changed"] for v in out["sp1b_stage1_liveness"].values())
        and all(out["sp3_no_price_input"]["loader_reads_column_scoped"].values())
        and out["sp4_cache_key"]["default_key_unmoved"]
        and out["sp4_cache_key"]["armed_distinct"]
    )
    out["all_assertions_pass"] = bool(ok and sp1.get("byte_identical_x3", False))
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}; all_assertions_pass={out['all_assertions_pass']}")
    return 0 if out["all_assertions_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
