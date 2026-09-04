"""caiso-242 — is the measured CAISO offer surface normalised on the SAME gas series the solve prices gas at?

NO LP, NO SOLVE, NOTHING ARMED.

``derive_caiso_offer_surface.py`` builds every armed CAISO band multiplier as

    mult = (bid_price - VOM - carbon) / (base_HR_class x gas_flow_day)

where ``gas_flow_day`` is, per its own recorded provenance, the **CA-composite
citygate daily spot** (``data/raw/gas-prices/caiso_citygate_daily.csv``,
trade+1 flow-day staircase).

The solve then prices the tranche at ``mult x base_HR x fuel(t)``, where
``fuel(t)`` is the model's delivered-gas series AS THE KEEPER RECIPE BUILDS IT.
(The caiso-242 run of this probe described that series as the EIA N3050CA3
monthly citygate + 0.46 adder — which was the LOOKALIKE the by-name recipe
pattern rebuilt, not the keeper; the keeper carries
``caiso_citygate_spot_level=True``, the daily CA citygate spot level of
caiso-84. Re-measured on-recipe at caiso-244; the caiso-242 §3 ratios
1.298/1.310/1.327 are VOID.)

A multiplier is dimensionless ONLY with respect to its own denominator. If the
two series differ, every armed multiplier is applied against a different fuel
level than the one it was measured against, and the model's CAISO gas offer is
scaled by exactly their ratio. This probe measures that ratio month by month and
year by year, and converts it to $/MWh on the CT_PEAKER econ band.

Writes ``results/calibration/_caiso244_gas_basis_identity_onrecipe.json``
(the caiso-242 artifact is frozen as the historical record).

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso242_gas_basis_identity.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

# caiso-244: re-measured ON-RECIPE against the CURRENT keeper. The caiso-242
# artifact (``_caiso242_*.json``, measured on caiso241 through the by-name
# pattern) is frozen as the historical record and never regenerated.
BUNDLE = REPO / "results/calibration/caiso243_b1_f923_fallback_guard"
CITYGATE = REPO / "data/raw/gas-prices/caiso_citygate_daily.csv"
YEARS = (2023, 2024, 2025)
HOURS = 8760
OUT = REPO / "results/calibration/_caiso244_gas_basis_identity_onrecipe.json"

#: CAMPD class base heat rate for CT_PEAKER — the derive's own ``base_HR_class``
#: (``data/raw/reference/caiso_campd_marginal_hr_summary.csv``).
CT_BASE_HR = 10.862
#: The armed CT_PEAKER econ_low multiplier (caiso-231 measured surface).
CT_ECON_LOW_MULT = 1.145

_spec = importlib.util.spec_from_file_location(
    "_caiso240_default_hr_mult_census",
    REPO / "scripts/probes/_caiso240_default_hr_mult_census.py",
)
CENSUS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CENSUS)


def model_gas_hourly(year: int) -> tuple[np.ndarray, float]:
    """Return the model's cap-weighted CT_PEAKER delivered gas ``(8760,)``."""
    from run_calibration import run_year
    from replay_keeper import run_year_kwargs

    meta = json.loads((BUNDLE / "meta.json").read_text())
    # ON-RECIPE (caiso-244 repair of the caiso-243 §7.3 instrument defect): the
    # strict, remapping meta -> run_year reconstruction. The by-parameter-NAME
    # filter this replaced dropped ``coal_prb_sigmoid_overrides`` ->
    # ``prb_overrides`` (36 CAISO structural flags, incl. the daily citygate
    # spot level) and rebuilt a lookalike recipe; every keeper-relative number
    # this probe published at caiso-242 is VOID until re-measured here.
    kwargs = run_year_kwargs(meta)
    CENSUS._clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
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
    gens = st.get("fleet") or []
    group = np.array([str(getattr(g, "plant_group", "")) for g in gens])
    fp = np.asarray(st["fuel_prices"], dtype=float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    sel = group == "CT_PEAKER"
    w = np.asarray(fa.pmax, dtype=float)[sel]
    capwt = (fp[sel] * w[:, None]).sum(axis=0) / max(w.sum(), 1e-9)
    return capwt, float(w.sum())


def month_of_hour(n: int) -> np.ndarray:
    """Return the 1-indexed calendar month of each of ``n`` hours (365-day)."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    idx = np.concatenate([np.full(d * 24, m + 1) for m, d in enumerate(days)])
    return idx[:n] if idx.size >= n else np.resize(idx, n)


def main() -> None:
    cg = pd.read_csv(CITYGATE)
    cg["date"] = pd.to_datetime(cg["date"])
    out: dict = {
        "_provenance": {
            "session": "caiso-244 (on-recipe re-run of the caiso-242 probe)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": "2026-09-04-caiso-243-b1-f923",
            "derive_denominator": (
                "CA-composite citygate daily spot, trade+1 flow-day staircase "
                "(data/raw/gas-prices/caiso_citygate_daily.csv), per "
                "caiso_offer_curve_measured.json _provenance.gas_basis"
            ),
            "model_numerator": (
                "the keeper recipe's own delivered-gas series, rebuilt ON-RECIPE "
                "through replay_keeper.run_year_kwargs (caiso-244). The caiso-242 "
                "run described this as 'EIA N3050CA3 monthly citygate + 0.46 "
                "adder' — that was the LOOKALIKE recipe the by-name pattern "
                "rebuilt; the keeper's actual gas level is set by the flags in "
                "recipe_flags (caiso_citygate_spot_level = daily CA citygate "
                "spot level, caiso-84)"
            ),
            "recipe_flags": {
                k: json.loads((BUNDLE / "run_config.json").read_text())[
                    "scenario_config"
                ].get(k)
                for k in (
                    "caiso_citygate_spot_level",
                    "caiso_citygate_flow_date",
                    "gas_hub_basis_overlay",
                    "gas_hub_basis_daily",
                    "gas_monthly_actuals",
                )
            },
            "voided_caiso242_ratios": [1.298, 1.310, 1.327],
            "note": "no LP, no flag delta",
        },
        "years": {},
    }
    for y in YEARS:
        capwt, cap_mw = model_gas_hourly(y)
        mo = month_of_hour(capwt.size)
        cgy = cg[cg["date"].dt.year == y]
        by_month = {}
        for m in range(1, 13):
            model_m = float(capwt[mo == m].mean())
            s = cgy.loc[cgy["date"].dt.month == m, "ca_composite_usd_mmbtu"].dropna()
            if s.empty:
                by_month[m] = {"model": round(model_m, 4), "citygate": None}
                continue
            cg_m = float(s.mean())
            by_month[m] = {
                "model": round(model_m, 4),
                "citygate": round(cg_m, 4),
                "ratio": round(model_m / cg_m, 4),
                "diff": round(model_m - cg_m, 4),
            }
        have = [v for v in by_month.values() if v.get("citygate")]
        model_mean = float(np.mean([v["model"] for v in have]))
        cg_mean = float(np.mean([v["citygate"] for v in have]))
        ratio = model_mean / cg_mean
        out["years"][y] = {
            "ct_peaker_cap_mw": round(cap_mw, 1),
            "model_gas_annual_mean": round(model_mean, 4),
            "citygate_annual_mean": round(cg_mean, 4),
            "ratio_model_over_derive_basis": round(ratio, 4),
            "diff_usd_mmbtu": round(model_mean - cg_mean, 4),
            "months_ratio_min": round(min(v["ratio"] for v in have), 4),
            "months_ratio_max": round(max(v["ratio"] for v in have), 4),
            "months_ratio_median": round(
                float(np.median([v["ratio"] for v in have])), 4
            ),
            # what the mismatch is worth on the CT_PEAKER econ_low band
            "econ_low_offer_on_model_basis_usd_mwh": round(
                CT_ECON_LOW_MULT * CT_BASE_HR * model_mean, 3
            ),
            "econ_low_offer_on_derive_basis_usd_mwh": round(
                CT_ECON_LOW_MULT * CT_BASE_HR * cg_mean, 3
            ),
            "econ_low_offer_inflation_usd_mwh": round(
                CT_ECON_LOW_MULT * CT_BASE_HR * (model_mean - cg_mean), 3
            ),
            "by_month": by_month,
        }
        print(f"--- {y} ---")
        print(
            json.dumps({k: v for k, v in out["years"][y].items() if k != "by_month"}, indent=2)
        )
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
