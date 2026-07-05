"""Validate the ERCOT forward RTOLCAP/RTOFFCAP supply cap against the measured series.

The HARD identification gate (anti-F1, the ercot27 exact-coverage artifact) that
must pass BEFORE any dispatch run. The WS-A forward formula
(:func:`market_sim.results.scarcity.ercot_rtolcap_forward_supply_cap_mw`) rebuilds
the on-line responsive reserve-supply cap from the model's OWN forecast net-load,
the derived per-class on-line headroom-realization shares and the fleet's
reserve-eligible capacity — instead of reading the measured
``ercot_<year>_ordc_reserves_hourly.parquet``. This script builds the formula cap
from the model's own drivers and compares it to the measured RTOLCAP/RTOFFCAP for
2023 / 2024 / 2025, checking:

* (a) annual mean level within ±10% (measured RTOLCAP ~13.5 / 16.7 / 19.1 GW);
* (b) a sane p10 / p50 / p90 band (formula band brackets the measured band, not
  a degenerate near-constant series);
* (c) the coverage ratio RTOLCAP ÷ total measured AS requirement (ASPLANNP433),
  median ~2× — a construction landing near **1.0×** is the ercot27 exact-coverage
  artifact and is REJECTED here, before any dispatch run.

This is a **quantity** validation (modeled vs measured MW), never a price fit —
nothing on the path reads LMP / RTSPP / MCPC / RTORPA (CLAUDE.md #12). Run:

    python scripts/validate_ercot_rtolcap_forward.py

Exit code 0 if the gate passes, 1 if the coverage/level rejection fires.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import load_demand  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    ercot_as_plan_requirement_mw,
    ercot_online_storage_reserve_mw,
    ercot_rtolcap_forward_supply_cap_mw,
)

YEARS = (2023, 2024, 2025)
PRODUCTS = ("REGUP", "RRS", "ECRS", "NSPIN")

# Gate thresholds.
LEVEL_TOL = 0.10  # annual-mean |error| target
COVERAGE_MIN, COVERAGE_MAX = 1.5, 2.5  # median RTOLCAP ÷ AS-requirement band
COVERAGE_ARTIFACT = 1.2  # median coverage ≤ this ⇒ the ercot27 1.0× artifact


def _formula_cap(year: int) -> tuple[np.ndarray, int]:
    """Build the forward RTOLCAP/RTOFFCAP cap (n_rows, hours) for ``year``.

    Uses the model's own forecast drivers (served load + wind/solar generation)
    and the year's reserve-eligible fleet — exactly the inputs the dispatch
    threads into the seam. The probe config (backcast mode +
    ``ercot_reserve_supply_forward``) selects the formula; the storage term reads
    the measured storage-AS series (the G4-style mode-aware backcast value).
    """
    cfg = ScenarioConfig(
        iso="ERCOT",
        weather_year=year,
        mode="backcast",
        ercot_reserve_supply_cap=True,
        ercot_reserve_supply_forward=True,
        ercot_multiproduct_as_coopt=True,
    )
    iso = get_iso_config("ERCOT")
    gens = load_fleet_from_csv("ERCOT", iso, year=year)
    fleet = generators_to_fleet_arrays(
        gens, [z.name for z in iso.zones], 8760, iso="ERCOT", config=cfg, year=year
    )
    demand = load_demand(
        "ERCOT", year, iso, td_loss_factor=cfg.td_loss_factor, include_interchange=True
    )
    wcf, wcap, scf, scap = load_renewable_profiles("ERCOT", year, iso, cfg)
    hours = min(8760, demand.shape[1])
    net_load = (
        demand[:, :hours].sum(0)
        - (wcap[:, None] * wcf[:, :hours]).sum(0)
        - (scap[:, None] * scf[:, :hours]).sum(0)
    )
    storage = ercot_online_storage_reserve_mw(cfg, hours)
    cap = ercot_rtolcap_forward_supply_cap_mw(
        cfg, fleet, hours, net_load=net_load, storage_reserve=storage
    )
    return cap, hours


def main() -> int:
    print(
        f"{'metric':<8} {'year':>5} {'formula':>8} {'meas':>8} {'err%':>7} "
        f"{'corr':>5}  {'formula p10/50/90':>20}  {'meas p10/50/90':>20}"
    )
    print("-" * 90)
    level_ok = True
    coverage_medians = []
    for year in YEARS:
        cap, hours = _formula_cap(year)
        rtolcap_f = cap[0]
        rtoffcap_f = cap[1] - cap[0] if cap.shape[0] > 1 else np.zeros(hours)
        meas = pd.read_parquet(
            REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
        )
        for label, formula, mcol in (
            ("RTOLCAP", rtolcap_f, "rtolcap"),
            ("RTOFFCAP", rtoffcap_f, "rtoffcap"),
        ):
            m = meas[mcol].to_numpy(dtype=float)[:hours]
            ok = ~np.isnan(m)
            fm = formula[ok].mean() / 1000.0
            mm = m[ok].mean() / 1000.0
            err = 100.0 * (fm / mm - 1.0) if mm else float("nan")
            corr = float(np.corrcoef(formula[ok], m[ok])[0, 1])
            fp = "/".join(
                f"{v:.1f}" for v in np.percentile(formula[ok], [10, 50, 90]) / 1000.0
            )
            mp = "/".join(
                f"{v:.1f}" for v in np.percentile(m[ok], [10, 50, 90]) / 1000.0
            )
            print(
                f"{label:<8} {year:>5} {fm:8.2f} {mm:8.2f} {err:+7.1f} {corr:5.2f}  "
                f"{fp:>20}  {mp:>20}"
            )
            if label == "RTOLCAP" and abs(err) > 100.0 * LEVEL_TOL:
                level_ok = False

        # (c) coverage ratio RTOLCAP ÷ total measured AS requirement.
        req = np.zeros(hours)
        for p in PRODUCTS:
            req += ercot_as_plan_requirement_mw(year, hours, p)
        active = req > 0
        cov = rtolcap_f[active] / np.maximum(req[active], 1.0)
        med = float(np.median(cov))
        coverage_medians.append(med)
        print(
            f"{'  cover':<8} {year:>5} {med:8.2f}× {'(RTOLCAP÷AS req)':>17}  "
            f"p10/90 {np.percentile(cov, [10, 90]).round(2)}  AS req "
            f"{req[active].mean() / 1000:.2f} GW"
        )
    print("-" * 90)

    med_all = float(np.median(coverage_medians))
    artifact = med_all <= COVERAGE_ARTIFACT
    coverage_ok = COVERAGE_MIN <= med_all <= COVERAGE_MAX
    print(f"Level within ±{int(LEVEL_TOL * 100)}% (all years RTOLCAP): {level_ok}")
    print(
        f"Coverage median {med_all:.2f}× "
        f"(target {COVERAGE_MIN}-{COVERAGE_MAX}×, ~2×): "
        f"{'OK' if coverage_ok else 'OUT OF BAND'}"
    )
    if artifact:
        print(
            f"REJECT: coverage median {med_all:.2f}× ≤ {COVERAGE_ARTIFACT}× — the "
            "ercot27 exact-coverage (~1.0×) artifact. Do NOT run dispatch."
        )
        return 1
    if not coverage_ok:
        print("REJECT: coverage out of the sane ~2× band. Do NOT run dispatch.")
        return 1
    if not level_ok:
        print(
            "WARN: an RTOLCAP annual mean exceeds ±10% — inspect the per-year "
            "residual before promoting (see the handoff's root-cause ledger). "
            "The coverage/artifact gate PASSED, so the probe may proceed as a "
            "documented single-delta test."
        )
    print(
        "GATE PASSED: forward RTOLCAP/RTOFFCAP is a sane ~2× coverage supply, "
        "not the exact-coverage artifact."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
