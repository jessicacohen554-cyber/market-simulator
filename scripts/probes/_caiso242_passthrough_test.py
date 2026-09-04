"""caiso-242 — does CAISO's OWN OASIS record support the fuel-invariant-margin decomposition?

NO LP, NO SOLVE, NOTHING ARMED. The ``gas_offer_net_revenue_margin`` mechanism
asserts that a gas tranche's offer is ``phys x HR_base x fuel(t) + markup_hr x
anchor`` — a physical burn that tracks fuel plus a margin that does NOT. Written
as a multiplier that assertion is

    mult(f) = phys + (markup_hr / HR_base) x anchor / f

i.e. the band multiplier must FALL as gas rises, hyperbolically.

``data/raw/_validation-source/caiso_offer_curve_measured.json`` carries
``per_year_band_mults`` — the same statistic, measured separately in 2023, 2024
and 2025, years whose delivered gas spans roughly 2x. That is a direct,
three-point, out-of-sample test of the assertion, in the very file the armed
multiplier comes from. This probe runs it, and reports:

  M1  the LEVEL basis check: the model's own delivered gas series (what the
      solve prices the tranche at) against the CA-composite citygate series the
      multipliers were measured against;
  M2  measured per-year multiplier vs the multiplier the ARMED decomposition
      implies at the model's own per-year fuel;
  M3  the resulting $/MWh offer error per band per year;
  M4  the same for every CAISO gas class carried in the measured surface, so the
      scoping is measured rather than assumed.

Writes ``results/calibration/_caiso244_passthrough_test_onrecipe.json`` (re-measured ON-RECIPE at
caiso-244 through ``replay_keeper.run_year_kwargs``; the ``_caiso242_passthrough_test.json``
artifact is frozen as the historical record — its keeper-relative numbers were
measured on a lookalike recipe and are VOID).

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso242_passthrough_test.py
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
MEASURED = REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
CITYGATE = REPO / "data/raw/gas-prices/caiso_citygate_daily.csv"
YEARS = (2023, 2024, 2025)
HOURS = 8760
OUT = REPO / "results/calibration/_caiso244_passthrough_test_onrecipe.json"

_spec = importlib.util.spec_from_file_location(
    "_caiso240_default_hr_mult_census",
    REPO / "scripts/probes/_caiso240_default_hr_mult_census.py",
)
CENSUS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CENSUS)

#: Bands the measured surface carries, and the ``phys_*`` key each maps to
#: (``offer_curves.gas_offer_margin_markup_mult``'s own band resolution).
BAND_PHYS = {
    "committed": "phys_committed",
    "econ_low": "phys_econ_low",
    "econ_high": "phys_econ_high",
    "peak": "phys_peak",
}


def model_gas(year: int) -> dict:
    """Return the model's delivered gas stats for CAISO CT_PEAKER tranches."""
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
    series = fp[sel]
    capwt = (series * w[:, None]).sum(axis=0) / max(w.sum(), 1e-9)
    return {
        "capwt_hourly_mean": round(float(capwt.mean()), 4),
        "capwt_hourly_median": round(float(np.median(capwt)), 4),
        "capwt_p10": round(float(np.quantile(capwt, 0.10)), 4),
        "capwt_p90": round(float(np.quantile(capwt, 0.90)), 4),
        "base_hr_capwt": round(
            float(
                (np.asarray(fa.heat_rate, dtype=float)[sel] * w).sum()
                / max(w.sum(), 1e-9)
            ),
            4,
        ),
    }


def citygate_stats() -> dict:
    """Per-year mean/median of the CA-composite citygate flow-day series."""
    d = pd.read_csv(CITYGATE)
    d["date"] = pd.to_datetime(d["date"])
    d["y"] = d["date"].dt.year
    out = {}
    for y in YEARS:
        s = d.loc[d["y"] == y, "ca_composite_usd_mmbtu"].dropna()
        out[y] = {
            "mean": round(float(s.mean()), 4),
            "median": round(float(s.median()), 4),
            "n_days": int(s.size),
        }
    return out


def main() -> None:
    meas = json.loads(MEASURED.read_text())
    per_year = meas["_provenance"]["per_year_band_mults"]
    cfg = json.loads((BUNDLE / "run_config.json").read_text())
    sc = cfg.get("scenario_config") or cfg
    curves = sc.get("offer_curve_by_group") or {}
    anchor = float(sc.get("gas_offer_margin_anchor") or 4.7964)

    out: dict = {
        "_provenance": {
            "session": "caiso-244 (on-recipe re-run of the caiso-242 probe)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": "2026-09-04-caiso-243-b1-f923",
            "anchor_usd_mmbtu": anchor,
            "note": "no LP, no flag delta; measured surface vs armed decomposition",
        },
        "M1_gas_basis": {"citygate_flowday": citygate_stats(), "model_delivered": {}},
        "M2_M3_passthrough": {},
    }
    for y in YEARS:
        out["M1_gas_basis"]["model_delivered"][y] = model_gas(y)

    for cls, bands in per_year.items():
        curve = curves.get(cls) or {}
        rows = {}
        for band, phys_key in BAND_PHYS.items():
            if band not in bands:
                continue
            phys = curve.get(phys_key)
            armed = curve.get(band)
            if phys is None or armed is None:
                rows[band] = {"skipped": "phys or armed multiplier absent"}
                continue
            phys = float(phys)
            armed = float(armed)
            markup_mult = max(0.0, armed - phys)
            per = {}
            for y in YEARS:
                if str(y) in bands[band]:
                    m_meas = float(bands[band][str(y)])
                elif y in bands[band]:
                    m_meas = float(bands[band][y])
                else:
                    continue
                f_model = out["M1_gas_basis"]["model_delivered"][y][
                    "capwt_hourly_mean"
                ]
                hr = out["M1_gas_basis"]["model_delivered"][y]["base_hr_capwt"]
                # the multiplier the ARMED decomposition implies at the model's
                # own delivered gas for that year
                m_armed = phys + markup_mult * anchor / f_model
                per[y] = {
                    "measured_mult": round(m_meas, 4),
                    "armed_implied_mult": round(m_armed, 4),
                    "delta_mult": round(m_armed - m_meas, 4),
                    "model_fuel": f_model,
                    # M3: the $/MWh the armed offer sits above (below) the
                    # measured multiplier form at the SAME model fuel
                    "offer_error_usd_mwh": round(
                        (m_armed - m_meas) * hr * f_model, 3
                    ),
                }
            vals = [v["measured_mult"] for v in per.values()]
            avals = [v["armed_implied_mult"] for v in per.values()]
            rows[band] = {
                "armed_mult": armed,
                "phys": phys,
                "markup_mult": round(markup_mult, 4),
                "fixed_margin_usd_mwh_at_anchor": round(
                    markup_mult
                    * out["M1_gas_basis"]["model_delivered"][2024]["base_hr_capwt"]
                    * anchor
                    if cls == "CT_PEAKER"
                    else float("nan"),
                    3,
                ),
                "measured_mult_range": round(max(vals) - min(vals), 4)
                if vals
                else None,
                "armed_implied_range": round(max(avals) - min(avals), 4)
                if avals
                else None,
                "per_year": per,
            }
        out["M2_M3_passthrough"][cls] = rows

    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
