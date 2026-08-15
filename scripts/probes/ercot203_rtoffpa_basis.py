"""ERCOT-203: is RTOFFPA a component of the measured RTSPP we score against?

The ercot-202 (T-3b) audit established that ERCOT's NP6-905-CD adder file
carries three published Real-Time price adders — ``rtorpa`` (On-Line Reserve),
``rtoffpa`` (Off-Line Reserve) and ``rtordpa`` (On-Line Reliability Deployment)
— and that the model represents only two of them: ``rtorpa`` endogenously (the
reserve-balance dual) and ``rtordpa`` through
``results.scarcity.ercot_rtordpa_overlay_series``.  It left ONE question open,
which is a *protocol* question, not a series question: does RTOFFPA enter the
Real-Time Settlement Point Price at all?

The ERCOT Nodal Protocols answer it (§6.5.7.3(12), §6.6.1, §6.6.1.1, §6.6.1.2,
§6.7.5 — quoted in ``docs/FINDING-ercot203-rtoffpa-not-in-rtspp-2026-08-15.md``):
RTSPP = RTLMP + RTORPA + RTORDPA.  RTOFFPA prices Off-Line reserve *capacity*
through the Ancillary Service imbalance stream (§6.7.5), never energy.

This probe is the independent EMPIRICAL check on that reading, run against the
measured data alone.  Over the hours where the off-line adder is live and the
two on-line adders are not, the two readings make opposite predictions:

    protocol reading      RTSPP - system_lambda  ~  0
    alternative reading   RTSPP - system_lambda  ~  rtoffpa

so the measured basis residual discriminates between them directly.  It also
reports, over all hours, the mean absolute basis residual under each candidate
decomposition — adding a component the settlement price does not contain must
make the identity worse, not better.

Reads only committed artifacts:
  * ``data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`` (NP6-905-CD)
  * ``data/raw/lmp-data/RTMLZHBSPP_<year>.zip`` (LZ/HB settlement point prices,
    HB_HUBAVG — the ERCOT scoring basis), on the model's fixed non-leap 8760
    clock via the committed deriver's prevailing->CST shift.

Usage:
    python -m scripts.probes.ercot203_rtoffpa_basis [--years 2023 2024 2025]

Rule 13 [R-MEASURED]: read-only attribution.  No LP solve, no model input, no
year outside the {2023, 2024, 2025} training span.  Diagnostic; never registered.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.data.derive_actual_lmp import (  # noqa: E402
    _MONTH_START_HOUR as _MSH,
    _PrevailingShift,
)

_MONTH_START_HOUR = np.asarray(_MSH, dtype=np.int64)

# RTC+B retired the adders on 2025-12-05; the committed overlay applies the same
# cut (results.scarcity.RTCB_GOLIVE_HOUR), so the basis test uses the same window.
from market_sim.results.scarcity import RTCB_GOLIVE_HOUR  # noqa: E402

HOURS = 8760
SETTLEMENT_POINT = "HB_HUBAVG"


def _hubavg_hourly(year: int) -> pd.Series:
    """HB_HUBAVG 15-minute RTSPP averaged to the model's non-leap 8760 CST clock."""
    zpath = REPO / f"data/raw/lmp-data/RTMLZHBSPP_{year}.zip"
    with zipfile.ZipFile(zpath) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            book = pd.read_excel(io.BytesIO(fh.read()), sheet_name=None, engine="openpyxl")
    df = pd.concat(book.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Settlement Point Name"] == SETTLEMENT_POINT].copy()
    dt = pd.to_datetime(df["Delivery Date"])
    mo = dt.dt.month.to_numpy()
    dy = dt.dt.day.to_numpy()
    hod = df["Delivery Hour"].astype(int).to_numpy() - 1  # hour-beginning
    rep = df["Repeated Hour Flag"].astype(str).str.strip().str.upper().to_numpy() == "Y"
    keep = ~((mo == 2) & (dy == 29))
    shift = _PrevailingShift(year, "America/Chicago")
    shifts = np.array(
        [
            shift(int(m), int(d), int(h), bool(rr))
            for m, d, h, rr in zip(mo[keep], dy[keep], hod[keep], rep[keep])
        ]
    )
    df = df[keep].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[keep] - 1] + (dy[keep] - 1) * 24 + hod[keep] - shifts
    df = df[(df["hoy"] >= 0) & (df["hoy"] < HOURS)]
    return df.groupby("hoy")["Settlement Point Price"].mean().reindex(range(HOURS))


def _year_result(year: int) -> dict:
    adders = pd.read_parquet(
        REPO / "data/raw/ercot" / f"ercot_{year}_ordc_reserves_hourly.parquet"
    ).set_index("hour")
    spp = _hubavg_hourly(year)

    lam = adders["system_lambda"].reindex(range(HOURS)).to_numpy(dtype=float)
    orpa = adders["rtorpa"].reindex(range(HOURS)).to_numpy(dtype=float)
    offpa = adders["rtoffpa"].reindex(range(HOURS)).to_numpy(dtype=float)
    ordpa = adders["rtordpa"].reindex(range(HOURS)).to_numpy(dtype=float)
    price = spp.to_numpy(dtype=float)

    valid = np.isfinite(price) & np.isfinite(lam) & np.isfinite(orpa)
    valid &= np.isfinite(offpa) & np.isfinite(ordpa)
    if year == 2025:  # pre-RTC+B window only, matching the overlay's own gate
        valid &= np.arange(HOURS) < RTCB_GOLIVE_HOUR

    # Candidate decompositions of the measured settlement price.
    cand = {
        "lambda_only": lam,
        "protocol_RTLMP+RTORPA+RTORDPA": lam + orpa + ordpa,
        "alternative_+RTOFFPA": lam + orpa + ordpa + offpa,
    }
    allhours = {
        k: {
            "mae": float(np.mean(np.abs(price[valid] - v[valid]))),
            "mean_signed": float(np.mean(price[valid] - v[valid])),
        }
        for k, v in cand.items()
    }

    # The discriminating test.  The off-line adder is NEVER live while both
    # on-line adders are dark (the three come off the same ORDC/PBMCL curve, so
    # RTOFFPA > 0 implies RTORPA > 0 in every hour of 2023-2025) — so the two
    # readings must be separated on the *residual left after* the protocol
    # decomposition, over the hours where RTOFFPA is live:
    #     protocol reading      RTSPP - (lambda + RTORPA + RTORDPA)  ~  0
    #     alternative reading   the same residual                    ~  RTOFFPA
    resid_full = price - (lam + orpa + ordpa)

    def _subset(mask: np.ndarray, label: str) -> dict:
        r, o = resid_full[mask], offpa[mask]
        n = int(mask.sum())
        return {
            "subset": label,
            "n_hours": n,
            "mean_rtoffpa": float(np.mean(o)) if n else None,
            "mean_residual_after_protocol_terms": float(np.mean(r)) if n else None,
            "median_residual_after_protocol_terms": float(np.median(r)) if n else None,
            "mae_if_rtoffpa_excluded": float(np.mean(np.abs(r))) if n else None,
            "mae_if_rtoffpa_included": float(np.mean(np.abs(r - o))) if n else None,
            "corr_residual_vs_rtoffpa": (
                float(np.corrcoef(r, o)[0, 1]) if n > 2 and o.std() > 0 else None
            ),
        }

    discriminating = [
        _subset(valid & (offpa > 0.0), "rtoffpa > 0"),
        _subset(valid & (offpa >= 5.0), "rtoffpa >= $5/MWh"),
        _subset(valid & (offpa >= 25.0), "rtoffpa >= $25/MWh"),
    ]

    # Least-squares attribution of the measured basis (RTSPP - System Lambda)
    # onto the three published adders.  The protocol reading predicts loadings
    # of ~1 on RTORPA and RTORDPA and ~0 on RTOFFPA.  RTORPA and RTOFFPA are
    # collinear by construction (same curve), so the pairwise correlation is
    # reported alongside — the coefficients are indicative, the subset MAEs
    # above are the load-bearing test.
    X = np.column_stack([orpa[valid], ordpa[valid], offpa[valid]])
    y = price[valid] - lam[valid]
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    attribution = {
        "loading_rtorpa": float(coef[0]),
        "loading_rtordpa": float(coef[1]),
        "loading_rtoffpa": float(coef[2]),
        "corr_rtorpa_rtoffpa": float(np.corrcoef(orpa[valid], offpa[valid])[0, 1]),
        "n_hours_rtoffpa_positive": int((valid & (offpa > 0.0)).sum()),
        "n_hours_rtoffpa_positive_and_rtorpa_zero": int(
            (valid & (offpa > 0.0) & (orpa <= 0.0)).sum()
        ),
    }
    return {
        "year": year,
        "n_valid_hours": int(valid.sum()),
        "all_hours_basis_identity": allhours,
        "discriminating_subsets": discriminating,
        "basis_attribution_lstsq": attribution,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ercot203_rtoffpa_basis")
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    parser.add_argument(
        "--out", default="results/calibration/ercot203_rtoffpa_basis.json"
    )
    args = parser.parse_args(argv)

    for y in args.years:  # rule 22 [R-HOLDOUT]: ERCOT holds no marker
        if y not in (2023, 2024, 2025):
            raise SystemExit(f"year {y} is outside ERCOT's authorized training span")

    out = {"settlement_point": SETTLEMENT_POINT, "years": [_year_result(y) for y in args.years]}
    path = REPO / args.out
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
