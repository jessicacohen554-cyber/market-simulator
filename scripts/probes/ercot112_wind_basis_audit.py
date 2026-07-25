"""ERCOT-112 Task-B prerequisites: audit the wind CF basis, round-trip and bound bias.

No LP. Answers the two cheap prerequisites the ERCOT-112 charter puts ahead of
any per-zone wind-shape work, plus the quintile decomposition that motivates it:

(a) **Double-count audit of** ``ercot_wtx_curtailment_driver``. The charter's
    premise is that "the EIA-930 wind bound is DELIVERED output", which would
    make the West/Panhandle curtailment ceiling a second curtailment on an
    already-curtailed series. That premise only holds on the
    :func:`~market_sim.data.renewables._eia_hourly_cf_profile` fallback branch.
    This probe reports which branch actually fires for each ERCOT backcast year.

(b) **CF round-trip capacity vintage.** The bound is built
    ``MW -> CF -> MW``: ``_mw_to_cf`` divides by the month's online capacity and
    ``_distribute_by_eia860`` multiplies back by December capacity times the
    vintage ramp. Algebraically the two legs cancel to a single scale factor
    ``installed_mw / monthly_capacity[:, -1].sum()``, so the round trip is exact
    iff those agree. This probe measures the realized factor, and separately
    counts the hours lost to the ``_CF_MAX = 1.0`` clip inside ``_mw_to_cf`` —
    the one place the round trip can leak energy even when the vintage matches.

(c) **Quintile bias.** Model wind bound vs EIA-930 delivered actual, binned by
    the actual's own quintile, which is the ERCOT-111 observation that opened
    the wind lane (+7.0 % at the lowest actual-wind quintile, -2.1 % at the
    highest) and the thing a per-zone shape would or would not explain.

Usage:
    python scripts/probes/ercot112_wind_basis_audit.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import renewables as rn  # noqa: E402

ISO = "ERCOT"
FUEL = "wind"


def _branch_report(year: int, monthly: np.ndarray) -> tuple[str, np.ndarray | None]:
    """Return which backcast CF branch fires for ``year`` and its MW series.

    Mirrors the branch ladder in
    :func:`~market_sim.data.renewables.load_renewable_profiles` exactly: HSL
    first, then the uncurtailed-fallback gross-up, then delivered EIA-930.
    """
    hsl = rn.hsl_potential_mw(ISO, year, FUEL)
    if hsl is not None:
        return "HSL (uncurtailed potential)", hsl
    if ISO in rn._UNCURTAILED_FALLBACK_ISOS:
        cf = rn._forecast_uncurtailed_cf(ISO, year, FUEL, monthly)
        if cf is not None:
            return "forecast-uncurtailed gross-up", None
    return "EIA-930 delivered (CURTAILMENT ALREADY BAKED IN)", None


def _delivered_mw(year: int) -> np.ndarray | None:
    """EIA-930 delivered wind MW for ``year``, or ``None`` when unmapped."""
    gen = rn.load_eia_hourly_renewable_gen(ISO, year)
    if gen is None or FUEL not in gen:
        return None
    return np.asarray(gen[FUEL], dtype=float)


def audit_year(year: int) -> None:
    """Print the (a)/(b)/(c) audit for one ERCOT backcast year."""
    cfg = ScenarioConfig(mode="backcast")
    iso_cfg = get_iso_config(ISO)
    monthly = rn._eia860_monthly_capacity(ISO, FUEL, iso_cfg.zone_names, year)
    if monthly is None:
        print(f"{year}: no EIA-860 monthly capacity — skipped")
        return

    december_total = float(monthly[:, -1].sum())
    installed_mw = december_total  # backcast branch, renewables.py:2019-2020

    branch, hsl_mw = _branch_report(year, monthly)

    # (b) realized round-trip: rebuild the bound the same way the LP does.
    wind_cf, wind_cap, _, _ = rn.load_renewable_profiles(ISO, year, iso_cfg, cfg)
    bound_mw = (wind_cf * wind_cap[:, None]).sum(axis=0)

    print(f"\n=== ERCOT {year} wind ===")
    print(f"(a) CF branch fired            : {branch}")
    print(f"    EIA-860 Dec capacity       : {december_total:,.0f} MW")
    print(f"    installed_mw used          : {installed_mw:,.0f} MW")
    print(f"    round-trip scale factor    : {installed_mw / december_total:.6f}")

    if hsl_mw is not None:
        src_twh = hsl_mw.sum() / 1e6
        bnd_twh = bound_mw.sum() / 1e6
        online = monthly.sum(axis=0)[rn._hour_to_month_index(rn.HOURS_PER_YEAR)]
        raw_cf = np.divide(
            hsl_mw, online, out=np.zeros_like(hsl_mw), where=online > 0.0
        )
        clipped = int((raw_cf > rn._CF_MAX).sum())
        lost_twh = float(np.clip(raw_cf - rn._CF_MAX, 0.0, None) @ online) / 1e6
        print(f"(b) source HSL potential      : {src_twh:8.3f} TWh")
        print(f"    rebuilt LP bound          : {bnd_twh:8.3f} TWh")
        print(
            f"    round-trip delta          : {bnd_twh - src_twh:+8.3f} TWh "
            f"({(bnd_twh / src_twh - 1) * 100:+.3f} %)"
        )
        print(f"    hours clipped at CF=1.0   : {clipped} / {rn.HOURS_PER_YEAR}")
        print(f"    energy lost to the clip   : {lost_twh:8.3f} TWh")

    # (c) quintile decomposition of the bound against delivered actual.
    actual = _delivered_mw(year)
    if actual is None:
        print("(c) no EIA-930 delivered series — quintile bias skipped")
        return
    print(f"(c) delivered actual          : {actual.sum() / 1e6:8.3f} TWh")
    print(f"    model bound               : {bound_mw.sum() / 1e6:8.3f} TWh")
    edges = np.quantile(actual, [0.2, 0.4, 0.6, 0.8])
    idx = np.digitize(actual, edges)
    print("    quintile (by actual wind):  actual MW   bound MW     delta")
    for q in range(5):
        m = idx == q
        a, b = actual[m].mean(), bound_mw[m].mean()
        print(f"      Q{q + 1} (n={int(m.sum()):4d})           {a:9,.0f} {b:9,.0f}"
              f"   {(b / a - 1) * 100:+7.1f} %")


def main() -> None:
    """Run the wind-basis audit over the requested ERCOT backcast years."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    for year in ap.parse_args().years:
        audit_year(year)


if __name__ == "__main__":
    main()
