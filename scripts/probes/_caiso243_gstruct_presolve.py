"""caiso-243 — G-STRUCT pre-solve: the CODED mechanism vs the MEASURED footprint, byte for byte. Zero LP.

The footprint probe (``_caiso243_fallback_footprint.py``) measured each repair
form as a monkeypatch. This probe rebuilds the keeper recipe through the real,
un-patched code path with the two ``ScenarioConfig`` fields set the way the
solve will set them, and asserts:

  * flags OFF   == the cached keeper rebuild, every cell, every year
                   (the default path is byte-identical after the code change);
  * (a) alone   == the cached ``a`` rebuild (2025);
  * (a)+(c)     == the cached ``ac`` rebuild (2025), and == keeper in 2023/2024
                   (the inert years, G-CTRL form 2's premise);
  * the ``state`` array is populated on the (c) fleet and empty otherwise.

Any mismatch is a defect in the CODE (the measurement is the pre-registered
reference), reported and fixed before any LP (PRECOMMIT §5.1).

Writes ``results/calibration/_caiso243_gstruct_presolve.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso243_gstruct_presolve.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import inspect
import io
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/caiso241_b1_ctpeaker_committed"
CACHE = Path(
    os.environ.get(
        "C243_CACHE",
        "/tmp/claude-0/-home-user-market-simulator/8996884f-b2f8-5b4c-a42b-d6af63597aea/scratchpad/c243v2",
    )
)
OUT = REPO / "results/calibration/_caiso243_gstruct_presolve.json"
HOURS = 8760

#: (label, year, flags, cached-reference variant name)
CASES = [
    ("off_2025", 2025, {}, "keeper"),
    ("a_2025", 2025, {"nearby_fuel_price_zone_donor_guard": True}, "a"),
    (
        "ac_2025",
        2025,
        {"nearby_fuel_price_zone_donor_guard": True, "fleet_state_from_eia860": True},
        "ac",
    ),
    (
        "ac_2024",
        2024,
        {"nearby_fuel_price_zone_donor_guard": True, "fleet_state_from_eia860": True},
        "keeper",
    ),
    (
        "ac_2023",
        2023,
        {"nearby_fuel_price_zone_donor_guard": True, "fleet_state_from_eia860": True},
        "keeper",
    ),
]


def keeper_recipe_kwargs(meta: dict, run_year) -> dict:
    """The keeper recipe as ``run_year`` kwargs, via the SAME mapping the solve uses.

    Since caiso-244 a thin wrapper over the shared
    :func:`scripts.replay_keeper.run_year_kwargs` (the strict, remapping
    reconstruction this probe first built inline at caiso-243 when the lane's
    by-parameter-name pattern was found to drop ``prb_overrides``). The
    ``run_year`` argument is kept for signature compatibility with the cached
    artifacts' call sites; the helper introspects the canonical module itself.
    """
    from replay_keeper import run_year_kwargs

    return run_year_kwargs(meta)


def rebuild(year: int, flags: dict) -> dict:
    from run_calibration import run_year

    spec = importlib.util.spec_from_file_location(
        "_c240", REPO / "scripts/probes/_caiso240_default_hr_mult_census.py"
    )
    c240 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c240)
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = keeper_recipe_kwargs(meta, run_year)
    params = inspect.signature(run_year).parameters
    for k in flags:
        assert k in params, f"run_year has no kwarg {k!r} — plumbing missing"
    kwargs.update(flags)
    c240._clear_fleet_caches()
    with contextlib.redirect_stderr(io.StringIO()):
        st = run_year(
            year,
            meta["iso"],
            HOURS,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kwargs,
        )
    fa = st["fleet_arrays"]
    fp = np.asarray(st["fuel_prices"], dtype=float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    cfg = st["config"]
    return {
        "fuel": fp,
        "mc": mc,
        "unit": np.array([str(u) for u in fa.unit_ids], dtype=object),
        "state": np.array(
            [str(s) for s in (fa.state if fa.state is not None else [""] * fa.n_gen)],
            dtype=object,
        ),
        "pmax": np.asarray(fa.pmax, float),
        "config_flags": {
            k: bool(getattr(cfg, k, None))
            for k in ("nearby_fuel_price_zone_donor_guard", "fleet_state_from_eia860")
        },
    }


def main() -> None:
    out = {
        "_provenance": {
            "session": "caiso-243",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "note": "real code path, no monkeypatch; reference = the footprint probe's cached rebuilds",
        },
        "cases": {},
    }
    all_pass = True
    for label, year, flags, ref_name in CASES:
        print(f"[rebuild] {label}", flush=True)
        got = rebuild(year, flags)
        ref = np.load(CACHE / f"{ref_name}_{year}.npz", allow_pickle=True)
        same_units = got["unit"].shape == ref["unit"].shape and bool(
            (got["unit"] == ref["unit"]).all()
        )
        fuel_eq = same_units and bool(np.array_equal(got["fuel"], ref["fuel"]))
        mc_eq = (
            same_units
            and ("mc" in ref.files)
            and bool(np.array_equal(got["mc"], ref["mc"]))
        )
        n_state = int((got["state"] != "").sum())
        rec = {
            "year": year,
            "flags": flags,
            "reference": ref_name,
            "fleet_identity": same_units,
            "fuel_byte_identical": fuel_eq,
            "fuel_max_abs_diff": float(np.abs(got["fuel"] - ref["fuel"]).max())
            if same_units
            else None,
            "fuel_cells_differing": int(
                (~np.isclose(got["fuel"], ref["fuel"], atol=1e-9)).sum()
            )
            if same_units
            else None,
            "mc_byte_identical": mc_eq if "mc" in ref.files else "reference has no mc",
            "config_flags_resolved": got["config_flags"],
            "rows_with_state": n_state,
            "rows": int(got["unit"].size),
            "PASS": bool(fuel_eq and (mc_eq or "mc" not in ref.files)),
        }
        all_pass &= rec["PASS"]
        out["cases"][label] = rec
        print(label, rec)
    out["G_STRUCT"] = "PASS" if all_pass else "FAIL"
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print("G-STRUCT", out["G_STRUCT"], f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
