"""nyiso-107: NYISO hydro benchmark/input basis audit (NO LP).

Matrix §5.5 Item B, the successor nyiso-106 named when it re-framed
``hydro_budget_nameplate_aware`` before the lever was ever sized. The scoped
question was: NYISO hydro reads **+1.3 / +1.3 / -12.7 %**, but the 2025 actual
comes from the EIA-930 swap while 2023/2024 come from EIA-923 — so the shape is
measured **across a benchmark-basis switch**. Put all three years on ONE basis
and report how much of the -12.7 % survives.

What the audit finds
--------------------
The basis switch is real, and it is **not** where the -12.7 % comes from. The
miss survives on every consistent benchmark basis. The defect is one layer
earlier and on the other side of the seam: the model's own 2025 hydro **input**
is the truncated vintage (EIA-923 ``HY`` carries **4 NYIS plants in 2025 vs
150 in 2024**), while the **benchmark** is repaired to EIA-930. The keeper
carries ``hydro_backfill_year=None`` and ``hydro_eia930_monthly=False``, so
nothing repairs the input side. The model dispatches its truncated budget
exactly, and is scored against the repaired one.

This is the same one-sided-repair family as nyiso-106's solar (§A) and ``OTHER``
(§E) findings, **inverted**: there the model was injected at the carried-forward
level and scored against the raw vintage; here it is fed the raw vintage and
scored against the repaired level.

Falsification instrument (rule 13: falsifies a benchmark, never an input)
------------------------------------------------------------------------
NYISO MIS **P-63 Real-Time Fuel Mix** (``data/raw/NYISO/fuel-mix/``) publishes
**Hydro** as its own category — unlike solar (nyiso-106 §A.3), which required
the night-baseline/daylight-bulge decomposition. So NYISO's own market
telemetry is a direct, EIA-independent instrument on the hydro level.

Sections
--------
``census``   EIA-923 ``HY``/``PS`` plant + TWh census by year — the collapse.
``basis``    The benchmark under each consistent basis, and the scored error.
``falsify``  P-63 ``Hydro`` vs EIA-930 ``NG: WAT`` vs EIA-923 ``HY``.
``psfold``   Whether NYIS ``NG: WAT`` carries the MISO/PJM PS-fold signature.
``budget``   The model's own budget under the keeper config and each repair.
``inert``    ``hydro_budget_nameplate_aware`` bit-identity on the keeper config.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso107_hydro_basis_audit.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

ISO, BA = "NYISO", "NYIS"
YEARS = (2023, 2024, 2025)
FUELMIX = REPO / "data" / "raw" / "NYISO" / "fuel-mix"
E923_PARQUET = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
KEEPER_RUN = (
    REPO / "frontend/data/backcast/runs/2026-07-31-nyiso105-chp-heat-rates.js"
)
OUT_PATH = REPO / "results/calibration/_nyiso107_hydro_basis_audit.json"
_TWH = 1e6

# The keeper's own hydro posture, read from its committed meta.json. Every
# measurement below is taken at exactly these settings.
KEEPER_HYDRO = {
    "hydro_backfill_year": None,
    "hydro_eia930_monthly": False,
    "hydro_forecast_budget": False,
    "hydro_year": "normal",
    "hydro_budget_nameplate_aware": False,
    "hydro_min_flow_floor": True,
    "hydro_ror_split": False,
}


def _sha(arr: np.ndarray) -> str:
    """Short content hash of a float array (byte-identity witness)."""
    return hashlib.sha256(
        np.ascontiguousarray(arr, dtype=float).tobytes()
    ).hexdigest()[:16]


def _model_hydro_twh() -> dict[int, float]:
    """Model hydro dispatch per year, decoded from the committed keeper payload."""
    import base64
    import gzip
    import re

    src = KEEPER_RUN.read_text()
    blob = re.search(r'runGz\["[^"]+"\]="([^"]+)"', src)
    if blob is None:  # pragma: no cover - payload format is stable
        raise ValueError(f"no runGz payload in {KEEPER_RUN}")
    doc = json.loads(gzip.decompress(base64.b64decode(blob.group(1))).decode())
    return {y: float(doc["years"][str(y)]["gmModel"]["hydro"]) for y in YEARS}


def section_census() -> dict:
    """EIA-923 HY/PS plant + TWh census by year — the 2025 collapse."""
    print("\n=== census — EIA-923 NYIS by prime mover ===")
    gen = pd.read_parquet(E923_PARQUET)
    nyis = gen[gen["ba_code"] == BA]
    out = {}
    print(f"{'year':<6}{'HY_n':>7}{'HY_TWh':>11}{'PS_n':>7}{'PS_TWh':>10}{'HY+PS':>11}")
    for year in YEARS:
        sub = nyis[nyis["year"] == year]
        hy = sub[sub["prime_mover"] == "HY"]
        ps = sub[sub["prime_mover"] == "PS"]
        hy_twh = float(hy["netgen_annual_mwh"].sum()) / _TWH
        ps_twh = float(ps["netgen_annual_mwh"].sum()) / _TWH
        out[year] = {
            "hy_plants": int(len(hy)),
            "hy_twh": round(hy_twh, 4),
            "ps_plants": int(len(ps)),
            "ps_twh": round(ps_twh, 4),
            "hy_plus_ps_twh": round(hy_twh + ps_twh, 4),
        }
        print(
            f"{year:<6}{len(hy):>7}{hy_twh:>11.4f}{len(ps):>7}"
            f"{ps_twh:>10.4f}{hy_twh + ps_twh:>11.4f}"
        )
    return out


def _benchmark_parts() -> dict:
    """Raw 923 hydro, EIA-930 hydro, and the as-scored benchmark, per year."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia923 import load_monthly_generation
    from run_calibration_full import (  # type: ignore[import-not-found]
        _backfill_renewables_eia930,
        _e930_series_annual_monthly,
        _eia923_frame,
        _eia930_frame,
        _vintage_completeness,
    )

    gen = load_monthly_generation()
    ic = get_iso_config(ISO)
    parts = {}
    for year in YEARS:
        e930 = _eia930_frame(year, ISO, ic)
        raw = _eia923_frame(year, gen, ISO)
        rep = _backfill_renewables_eia930(raw.copy(), year, ISO, gen, e930)
        ann930, _ = _e930_series_annual_monthly(e930, "hydro", year)
        parts[year] = {
            "e923_raw_twh": float(
                raw[raw["klass"] == "hydro"]["annual_mwh"].sum() / _TWH
            ),
            "e930_twh": float(ann930 / _TWH),
            "as_scored_twh": float(
                rep[rep["klass"] == "hydro"]["annual_mwh"].sum() / _TWH
            ),
            "vintage_completeness": float(_vintage_completeness(year, gen, ISO, e930)),
        }
    return parts


def section_basis(parts: dict, model: dict[int, float]) -> dict:
    """The scored error under each CONSISTENT benchmark basis — the scoped ask."""
    print("\n=== basis — scored error on one basis at a time ===")
    prior_complete = parts[2024]["e923_raw_twh"]
    bases: dict[str, dict[int, float]] = {
        "as_scored_mixed_923_923_930": {y: parts[y]["as_scored_twh"] for y in YEARS},
        "all_eia930": {y: parts[y]["e930_twh"] for y in YEARS},
        "all_eia923_carry_corrected": {
            2023: parts[2023]["e923_raw_twh"],
            2024: parts[2024]["e923_raw_twh"],
            # The nyiso-106 carry: prior complete year x vintage completeness.
            2025: prior_complete * parts[2025]["vintage_completeness"],
        },
    }
    out = {}
    print(f"{'basis':<32}" + "".join(f"{y:>12}" for y in YEARS))
    for name, act in bases.items():
        errs = {y: (model[y] / act[y] - 1.0) * 100.0 for y in YEARS}
        out[name] = {
            "actual_twh": {y: round(act[y], 4) for y in YEARS},
            "error_pct": {y: round(errs[y], 2) for y in YEARS},
        }
        print(f"{name:<32}" + "".join(f"{errs[y]:>+11.2f}%" for y in YEARS))
    return out


def section_falsify(parts: dict) -> dict:
    """NYISO P-63 `Hydro` — the EIA-independent instrument on the level."""
    print("\n=== falsify — NYISO MIS P-63 Hydro vs the EIA series ===")
    out = {}
    print(
        f"{'year':<6}{'P63_Hydro':>11}{'EIA930_WAT':>12}"
        f"{'EIA923_HY+PS':>14}{'P63_vs_930':>12}"
    )
    for year in YEARS:
        fm = pd.read_csv(FUELMIX / f"NYISO_fuelmix_hourly_{year}.csv.gz")
        hyd = fm[fm["fuel_category"] == "Hydro"]
        p63 = float(hyd["gen_mw"].sum()) / _TWH
        e930 = parts[year]["e930_twh"]
        out[year] = {
            "p63_hydro_twh": round(p63, 4),
            "p63_hours": int(len(hyd)),
            "e930_twh": round(e930, 4),
            "e923_raw_twh": round(parts[year]["e923_raw_twh"], 4),
            "p63_vs_930_pct": round((p63 / e930 - 1.0) * 100.0, 2),
        }
        print(
            f"{year:<6}{p63:>11.4f}{e930:>12.4f}"
            f"{parts[year]['e923_raw_twh']:>14.4f}"
            f"{(p63 / e930 - 1.0) * 100.0:>+11.2f}%"
        )
    return out


def section_psfold(census: dict, parts: dict) -> dict:
    """Does NYIS `NG: WAT` carry the MISO/PJM pumped-storage-fold signature?

    MISO/PJM (``EIA930_PS_FOLDED_INTO_WAT``) file no ``NG: PS`` column and their
    ``NG: WAT`` runs ABOVE EIA-923 ``HY``. NYIS files no ``NG: PS`` either, so
    the same question must be asked before its ``NG: WAT`` is admitted as a
    LEVEL for a conventional-hydro-only unit population (rule 14).
    """
    print("\n=== psfold — is NYIS NG: WAT pumped-storage-inflated? ===")
    from market_sim.config.constants import EIA930_PS_FOLDED_INTO_WAT

    out = {"eia930_ps_folded_into_wat": sorted(EIA930_PS_FOLDED_INTO_WAT)}
    print(f"{'year':<6}{'930_WAT':>10}{'923_HY':>10}{'930/923_HY':>13}")
    for year in YEARS:
        hy = census[year]["hy_twh"]
        wat = parts[year]["e930_twh"]
        out[year] = {"e930_wat_twh": round(wat, 4), "e923_hy_twh": round(hy, 4),
                     "ratio": round(wat / hy, 4)}
        print(f"{year:<6}{wat:>10.4f}{hy:>10.4f}{wat / hy:>13.4f}")
    return out


def section_budget() -> dict:
    """The model's OWN hydro budget: keeper config vs each available repair."""
    print("\n=== budget — the model's hydro input, keeper vs repairs ===")
    import numpy as np

    from market_sim.data.eia_loader import measured_monthly_hydro
    from market_sim.data.hydro import (
        _nameplate_aware_scale,
        hours_per_month,
        load_hydro_budget,
    )

    out: dict = {"per_year_keeper_config": {}}
    print(f"{'year':<6}{'plants':>8}{'budget_TWh':>13}{'max_MW':>10}")
    for year in YEARS:
        hb = load_hydro_budget(ISO, year)
        rec = {
            "plants": int(len(hb.plant_ids)),
            "budget_twh": round(float(hb.monthly_energy.sum()) / _TWH, 4),
            "max_mw": round(float(hb.max_mw.sum()), 1),
        }
        out["per_year_keeper_config"][year] = rec
        print(f"{year:<6}{rec['plants']:>8}{rec['budget_twh']:>13.4f}{rec['max_mw']:>10.1f}")

    tgt = np.asarray(measured_monthly_hydro(ISO, 2025), dtype=float)
    print(f"\n2025 repair ladder (930 pin target {tgt.sum() / _TWH:.4f} TWh):")
    print(f"{'config':<40}{'plants':>8}{'budget_TWh':>13}{'max_MW':>10}")
    ladder = {
        "bare_KEEPER": {},
        "backfill_2024": {"backfill_year": 2024},
        "backfill_2024_plus_930pin": {
            "backfill_year": 2024,
            "monthly_target_mwh": tgt,
        },
        "backfill_2024_plus_930pin_plus_nameplate_aware": {
            "backfill_year": 2024,
            "monthly_target_mwh": tgt,
            "nameplate_aware_target": True,
        },
        "930pin_ONLY_no_backfill": {"monthly_target_mwh": tgt},
    }
    out["repair_ladder_2025"] = {}
    for lbl, kw in ladder.items():
        hb = load_hydro_budget(ISO, 2025, **kw)
        rec = {
            "plants": int(len(hb.plant_ids)),
            "budget_twh": round(float(hb.monthly_energy.sum()) / _TWH, 4),
            "max_mw": round(float(hb.max_mw.sum()), 1),
        }
        out["repair_ladder_2025"][lbl] = rec
        print(f"{lbl:<40}{rec['plants']:>8}{rec['budget_twh']:>13.4f}{rec['max_mw']:>10.1f}")

    # How much work the nameplate-aware re-allocation would actually do, once
    # its prerequisite target exists.
    hpm = hours_per_month().astype(float)
    out["nameplate_aware_work_under_pin"] = {}
    print("\nnameplate-aware re-allocation once a target exists:")
    for lbl, bk in (("with_backfill_2024", 2024), ("without_backfill", None)):
        hb = load_hydro_budget(ISO, 2025, backfill_year=bk)
        cap = hb.max_mw[:, np.newaxis] * hpm[np.newaxis, :]
        _me, stats = _nameplate_aware_scale(hb.monthly_energy, cap, tgt)
        moved = float(stats["moved_mwh"])
        rec = {
            "clipped_plant_months": int(stats["clipped"]),
            "moved_mwh": round(moved, 1),
            "moved_pct_of_budget": round(moved / float(tgt.sum()) * 100.0, 4),
            "physically_unattainable_mwh": round(float(stats["short_mwh"]), 1),
        }
        out["nameplate_aware_work_under_pin"][lbl] = rec
        print(f"  {lbl:<22}{rec}")
    return out


def section_inert() -> dict:
    """`hydro_budget_nameplate_aware` on the keeper config: bit-identity test."""
    print("\n=== inert — hydro_budget_nameplate_aware at the keeper's settings ===")
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.hydro import build_hydro_fleet

    zones = [z.name for z in get_iso_config(ISO).zones]
    out: dict = {"per_year": {}, "bit_identical_all_years": True}
    print(f"{'year':<6}{'flag':<7}{'units':>7}{'budget_TWh':>13}{'energy_sha':>18}{'pmax_sha':>18}")
    for year in YEARS:
        sig = {}
        for flag in (False, True):
            units, energy = build_hydro_fleet(
                ISO,
                year,
                zones,
                backfill_year=KEEPER_HYDRO["hydro_backfill_year"],
                eia930_monthly=KEEPER_HYDRO["hydro_eia930_monthly"],
                forecast_budget=KEEPER_HYDRO["hydro_forecast_budget"],
                min_flow_floor=KEEPER_HYDRO["hydro_min_flow_floor"],
                ror_split=KEEPER_HYDRO["hydro_ror_split"],
                nameplate_aware_target=flag,
                hydro_year=KEEPER_HYDRO["hydro_year"],
            )
            pmax = np.array([g.pmax_mw for g in units], dtype=float)
            sig[flag] = (_sha(energy), _sha(pmax), len(units))
            print(
                f"{year:<6}{str(flag):<7}{len(units):>7}"
                f"{energy.sum() / _TWH:>13.4f}{_sha(energy):>18}{_sha(pmax):>18}"
            )
        same = sig[False] == sig[True]
        out["per_year"][year] = {
            "energy_sha_off": sig[False][0],
            "energy_sha_on": sig[True][0],
            "pmax_sha_off": sig[False][1],
            "pmax_sha_on": sig[True][1],
            "units": sig[False][2],
            "bit_identical": same,
        }
        out["bit_identical_all_years"] &= same
    print(f"\nBIT-IDENTICAL in every year: {out['bit_identical_all_years']}")
    return out


def main() -> None:
    model = _model_hydro_twh()
    parts = _benchmark_parts()
    census = section_census()
    payload = {
        "session": "nyiso-107",
        "iso": ISO,
        "years": list(YEARS),
        "keeper": "2026-07-31-nyiso105-chp-heat-rates",
        "keeper_hydro_config": KEEPER_HYDRO,
        "model_hydro_twh": {y: round(model[y], 4) for y in YEARS},
        "census_eia923": census,
        "benchmark_parts": {
            y: {k: round(v, 4) for k, v in parts[y].items()} for y in YEARS
        },
        "basis": section_basis(parts, model),
        "falsify_p63": section_falsify(parts),
        "psfold": section_psfold(census, parts),
        "budget": section_budget(),
        "inert": section_inert(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=1, default=str) + "\n")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
