"""Decompose the NYISO solar CF realization gap (nyiso-132, PREREG §1-§2).

Settles two of the four items ``PREREG-nyiso130-solar-cf-level-2026-08-06.md``
§4 handed forward, from the model's own loader path at HEAD and with **no
solve**:

* **Item 1 — population identity.** Shows that
  ``RENEWABLE_AVG_CF["NYISO"]["solar"]`` (an ISO-wide normalization) is applied
  to the *registered market fleet's* capacity array once
  ``nyiso_solar_market_generator_basis`` is armed, so the constant and the
  fleet 0.1955 was measured on are the same population. The load-bearing step
  is that NYISO solar never reaches the measured-profile branch:
  ``_eia_hourly_cf_profile`` returns ``None`` (EIA-930 NYIS reports SUN as
  identically zero) and NYISO is not in ``_UNCURTAILED_FALLBACK_ISOS``, so
  control falls through to ``_eia930_cf`` → ``derive_cf_profile(values,
  RENEWABLE_AVG_CF[iso][fuel])``.

* **Item 2 — the 0.15 → 0.133 gap.** The nyiso-130 prereg attributed it to
  "clipping and the donor profile". This measures that claim: it reports the
  distribution sum, the realized hourly mean CF, the clipped-hour count, and
  the realized CF under BOTH denominator conventions (year-end capacity, which
  is what ``installed_mw`` uses, vs mean-monthly exposure). The gap is a
  denominator artifact on a growing fleet, not a level defect — clipping is
  zero and the mean lands on the constant exactly.

Rule 13 ``[R-MEASURED]``: identified from the registry and the loader path, never
from the price residual — no price series is read here.

Usage::

    python scripts/probes/_nyiso132_cf_realization_decomposition.py
    python scripts/probes/_nyiso132_cf_realization_decomposition.py --json-out \
        results/calibration/_nyiso132_cf_realization.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from market_sim.config.constants import HOURS_PER_YEAR, RENEWABLE_AVG_CF
from market_sim.config.iso_configs import get_iso_config
from market_sim.data import renewables as R

ISO = "NYISO"
FUEL = "solar"
YEARS = (2023, 2024, 2025)


def _shape_values(year: int) -> tuple["object", str]:
    """Return the hourly distribution the model uses, and its source label."""
    profiles = R.load_generation_profiles(ISO, year)
    values = R._extract_fuel_values(profiles, FUEL)
    if R._is_diurnally_degenerate(values):
        repaired = R._donor_shaped_distribution(ISO, year, FUEL)
        if repaired is not None:
            donor = R._DEGENERATE_SHAPE_DONOR_ISO[ISO]
            return repaired, f"donor-repaired ({donor})"
    return values, "eia930-native"


def decompose() -> dict:
    """Measure the per-year realization decomposition. No solve, no prices."""
    zones = get_iso_config(ISO).zone_names
    avg_cf = RENEWABLE_AVG_CF[ISO][FUEL]
    month_index = R._hour_to_month_index(HOURS_PER_YEAR)

    rows = []
    for year in YEARS:
        values, source = _shape_values(year)
        cf = R.derive_cf_profile(values, avg_cf)

        bases = {}
        candidates = {
            "eia860": R._eia860_monthly_capacity(ISO, FUEL, zones, year),
            "registered": R.load_market_solar_monthly(ISO, year, zones),
        }
        for name, monthly in candidates.items():
            if monthly is None:
                continue
            total = monthly.sum(axis=0)
            energy_mwh = float((cf * total[month_index]).sum())
            bases[name] = {
                "first_month_mw": float(total[0]),
                "year_end_mw": float(total[-1]),
                "mean_monthly_mw": float(total.mean()),
                "mean_over_year_end": float(total.mean() / total[-1]),
                "energy_gwh": energy_mwh / 1000.0,
                # installed_mw uses year-end capacity, so this is the
                # convention the "realized ~0.133" figure was reported under.
                "realized_cf_vs_year_end": energy_mwh
                / (float(total[-1]) * HOURS_PER_YEAR),
                "realized_cf_vs_mean_monthly": energy_mwh
                / (float(total.mean()) * HOURS_PER_YEAR),
            }

        rows.append(
            {
                "year": year,
                "shape_source": source,
                "values_sum": float(values.sum()),
                "hourly_mean_cf": float(cf.mean()),
                "hours_clipped_at_max": int((cf >= R._CF_MAX).sum()),
                "bases": bases,
            }
        )

    return {
        "iso": ISO,
        "fuel": FUEL,
        "constant": {
            "symbol": "RENEWABLE_AVG_CF['NYISO']['solar']",
            "value": avg_cf,
            "tier": "Tier-3 approximation, carries needs-citation",
        },
        "measured_target_cf_2025": 0.1955,
        "years": rows,
    }


def _render(record: dict) -> None:
    c = record["constant"]
    print(f"{c['symbol']} = {c['value']}  ({c['tier']})\n")
    for row in record["years"]:
        print(f"--- {row['year']} --- shape: {row['shape_source']}")
        print(
            f"  values.sum()={row['values_sum']:.6f}"
            f"  hourly MEAN cf={row['hourly_mean_cf']:.6f}"
            f"  clipped hours={row['hours_clipped_at_max']}"
        )
        for name, b in row["bases"].items():
            print(
                f"  [{name:10s}] cap {b['first_month_mw']:.1f}->{b['year_end_mw']:.1f} MW"
                f" (mean/year-end {b['mean_over_year_end']:.4f})"
                f" | realized CF vs year-end {b['realized_cf_vs_year_end']:.4f}"
                f" vs mean-monthly {b['realized_cf_vs_mean_monthly']:.4f}"
            )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, help="write the record as JSON")
    args = parser.parse_args()

    record = decompose()
    _render(record)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
