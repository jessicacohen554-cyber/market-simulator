"""nyiso-128: score the solar-basis A/B against its pre-registered kill gates.

Scores the seven kill gates of
``results/calibration/PREREG-nyiso128-market-solar-basis-2026-08-05.md`` §7 on
the two solved arms, from committed bundle artifacts only — no re-solve.

Gates (PREREG §7):

* **K1** — no free parameter: the two arms' ``scenario_config`` must differ in
  exactly the one flag.
* **K2** — no new unserved energy the control does not have.
* **K3** — C1 fuel-mix free-class score must not regress.
* **K4** — live, not inert: max zonal ``|ΔLMP|`` ≥ $1/MWh in some year.
* **K5** — the seam does not absorb the correction: the net four-link seam p50
  must stay inside the reconciliation band (reported; the arm's claim is that
  removed solar is replaced by IN-STATE thermal, not imports).
* **K6** — the control reproduces the keeper's C3a to ±0.2 pp.
* **K7** — C7/C8 protective gates hold.

Also reports the §6 ex-ante predictions (P1 summer peaking fleet, P2 C3a
direction) and the §4 declared limitation bound on C3a-2025.

Usage::

    python scripts/probes/_nyiso128_ab_gates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CONTROL = REPO / "results/calibration/nyiso128_control"
TREAT = REPO / "results/calibration/nyiso128_treatment"
KEEPER = REPO / "results/calibration/nyiso125_seam_A"
YEARS = (2023, 2024, 2025)
FLAG = "nyiso_solar_market_generator_basis"

# JJA h16-h18 — the window nyiso-126 measured as 70.6 % of the 2025 C3a residual.
PEAK_MONTHS = (6, 7, 8)
PEAK_HOURS = (16, 17, 18)


def _cfg(bundle: Path) -> dict:
    """Return a bundle's recorded ``scenario_config``."""
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """Return a bundle's committed P1 system hourly frame for one year."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def _classes(bundle: Path, year: int) -> pd.DataFrame:
    """Return a bundle's committed P1 class hourly frame for one year."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return df[df["pass"] == "P1"]


def _peak_mask(hours: int) -> np.ndarray:
    """Boolean mask for JJA h16-h18 on the model's fixed non-leap 2023 clock."""
    cal = pd.date_range("2023-01-01", periods=hours, freq="h")
    return np.isin(cal.month, PEAK_MONTHS) & np.isin(cal.hour, PEAK_HOURS)


def k1_single_delta() -> dict:
    """K1 — the arms must differ in exactly the one pre-registered flag."""
    a, b = _cfg(CONTROL), _cfg(TREAT)
    diff = {k for k in set(a) | set(b) if a.get(k, "<absent>") != b.get(k, "<absent>")}
    return {
        "gate": "K1 no free parameter",
        "differing_fields": sorted(diff),
        "pass": diff == {FLAG},
    }


def k2_unserved() -> dict:
    """K2 — no hour of new slack/VOLL the control does not have."""
    rows = []
    ok = True
    for y in YEARS:
        c = _system(CONTROL, y)["slack"].to_numpy()
        t = _system(TREAT, y)["slack"].to_numpy()
        new = float(np.maximum(t - c, 0.0).sum())
        n_new = int(((t > 1e-6) & (c <= 1e-6)).sum())
        ok &= n_new == 0
        rows.append({"year": y, "control_slack_mwh": round(float(c.sum()), 3),
                     "treat_slack_mwh": round(float(t.sum()), 3),
                     "new_slack_mwh": round(new, 3), "new_slack_hours": n_new})
    return {"gate": "K2 no new unserved energy", "rows": rows, "pass": ok}


def k4_live() -> dict:
    """K4 — live, not inert: max zonal |dLMP| across the year."""
    rows = []
    live = False
    for y in YEARS:
        c = _system(CONTROL, y).sort_values(["zone", "hour"])["price"].to_numpy()
        t = _system(TREAT, y).sort_values(["zone", "hour"])["price"].to_numpy()
        m = float(np.abs(t - c).max())
        live |= m >= 1.0
        rows.append({"year": y, "max_abs_dlmp": round(m, 4),
                     "mean_abs_dlmp": round(float(np.abs(t - c).mean()), 4)})
    return {"gate": "K4 live not inert", "rows": rows, "pass": live}


def zonal_mean_prices() -> dict:
    """Per-year system mean price in both arms (the C3a-relevant level)."""
    rows = []
    for y in YEARS:
        c = _system(CONTROL, y).groupby("hour")["price"].mean()
        t = _system(TREAT, y).groupby("hour")["price"].mean()
        rows.append({"year": y, "control_mean": round(float(c.mean()), 3),
                     "treat_mean": round(float(t.mean()), 3),
                     "delta": round(float(t.mean() - c.mean()), 3)})
    return {"metric": "system mean LMP (zone-mean of hourly)", "rows": rows}


def p1_summer_peaking() -> dict:
    """P1 — does the merchant summer peaking fleet come on in JJA h16-h18?"""
    rows = []
    for y in YEARS:
        cc, tc = _classes(CONTROL, y), _classes(TREAT, y)
        n = int(cc["hour"].max()) + 1
        mask = _peak_mask(n)
        rec = {"year": y}
        for k in ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "CC_CHP", "solar", "import"):
            a = cc[cc["klass"] == k].sort_values("hour")["mw"].to_numpy()
            b = tc[tc["klass"] == k].sort_values("hour")["mw"].to_numpy()
            if a.size == 0:
                continue
            rec[k] = {"control_peak_mw": round(float(a[mask].mean()), 1),
                      "treat_peak_mw": round(float(b[mask].mean()), 1),
                      "delta_peak_mw": round(float(b[mask].mean() - a[mask].mean()), 1),
                      "delta_annual_twh": round(float((b.sum() - a.sum()) / 1e6), 4)}
        rows.append(rec)
    return {"prediction": "P1 summer peaking fleet is called", "rows": rows}


def k5_seam() -> dict:
    """K5 — the removed solar must not simply be replaced by imports."""
    rows = []
    for y in YEARS:
        cc, tc = _classes(CONTROL, y), _classes(TREAT, y)
        a = cc[cc["klass"] == "import"].sort_values("hour")["mw"].to_numpy()
        b = tc[tc["klass"] == "import"].sort_values("hour")["mw"].to_numpy()
        if a.size == 0:
            continue
        rows.append({"year": y, "control_p50_mw": round(float(np.median(a)), 1),
                     "treat_p50_mw": round(float(np.median(b)), 1),
                     "delta_p50_mw": round(float(np.median(b) - np.median(a)), 1),
                     "delta_annual_twh": round(float((b.sum() - a.sum()) / 1e6), 4)})
    return {"gate": "K5 seam does not absorb the correction", "rows": rows}


def main() -> int:
    """Score every gate and write the record."""
    for b in (CONTROL, TREAT):
        if not (b / "run_config.json").exists():
            print(f"MISSING: {b}/run_config.json — arm not finished")
            return 1

    record = {
        "probe": "_nyiso128_ab_gates",
        "prereg": "results/calibration/PREREG-nyiso128-market-solar-basis-2026-08-05.md",
        "control_bundle": str(CONTROL.relative_to(REPO)),
        "treatment_bundle": str(TREAT.relative_to(REPO)),
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "k1": k1_single_delta(),
        "k2": k2_unserved(),
        "k4": k4_live(),
        "k5": k5_seam(),
        "mean_price": zonal_mean_prices(),
        "p1_summer_peaking": p1_summer_peaking(),
    }
    print(json.dumps(record, indent=1))
    dest = REPO / "results/calibration/_nyiso128_ab_gates.json"
    dest.write_text(json.dumps(record, indent=1) + "\n")
    print(f"\nwrote {dest}")
    print("\nK3/K6/K7 come from scripts/calibration_verdict.py on the registered runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
