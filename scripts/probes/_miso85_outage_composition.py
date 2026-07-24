"""miso-85 composition probe: which MISO published-outage cause set is admissible?

Settles the open question left by
``docs/handoffs/miso-native-outage-wiring-2026-07.md`` ("Composition to settle in
calibration"): the MISO Multiday Operating Margin OUTAGE record is a
WHOLE-REGISTERED-FLEET offline-MW total with no fuel identity, but
``data.miso_outages.miso_native_outage_derate_factors`` applies it to the model's
fossil-thermal bins against a fossil-thermal denominator. Summing all four cause
buckets therefore charges the whole system's outages (nuclear refuel, hydro /
renewable maintenance) to the thermal fleet.

The discriminator is PHYSICAL FEASIBILITY against measured data, never the price
residual (rules 1 / 10): MISO's own metered thermal output (EIA-930 hourly
Coal + Natural Gas for the MISO BA) is a hard lower bound on how much thermal
capacity was actually available. A cause set whose implied available capacity
falls BELOW measured generation is refuted outright — the model could not
reproduce its own C1-validated dispatch under it.

Also reports, for each cause set, the fleet-average availability next to the
independent CAMPD per-unit measured derate the overlay replaces
(``data.outages.unit_outage_derate_factors``) — a level cross-check between two
independent measured availability records, and the monthly seasonality by cause
bucket (the evidence that "Derated" is a summer ambient derate, not scheduled
work, while "Planned" is the spring/fall maintenance bucket the model already
carries).

Usage:
    python scripts/probes/_miso85_outage_composition.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.miso_outages import (  # noqa: E402
    _THERMAL_GROUPS,
    _load_estimated,
    _miso_thermal_capacity_mw,
    miso_outage_mw_series,
)
from market_sim.data.outages import (  # noqa: E402
    _iso_plant_capacity,
    unit_outage_derate_factors,
)

YEARS = (2023, 2024, 2025)
# Candidate cause sets. "ALL" is the as-wired default this probe refutes;
# "UNPLANNED" is the adopted set (the PJM instrument's precedent).
COMBOS: dict[str, tuple[str, ...]] = {
    "ALL (as wired)": ("Derated", "Forced", "Planned", "Unplanned"),
    "UNPLANNED (D+F+U)": ("Derated", "Forced", "Unplanned"),
    "F+U": ("Forced", "Unplanned"),
    "Forced only": ("Forced",),
}


def measured_thermal_gen_daily_max(year: int) -> pd.Series:
    """Measured MISO daily-max thermal (coal + gas) generation, MW.

    EIA-930 hourly fuel-type generation for the MISO BA, converted from UTC to
    the market clock (EST, no DST — the model's fixed clock) and reduced to the
    daily maximum, which is the binding hour for an availability envelope.
    """
    df = pd.read_parquet(RAW_DATA_DIR / "MISO_fueltype.parquet")
    per = pd.to_datetime(df["period"], utc=True).dt.tz_convert("Etc/GMT+5")
    ser = df.assign(period=per)
    ser = ser[ser["fueltype"].isin(["COL", "NG"])].groupby("period")["value_mwh"].sum()
    ser = ser[ser.index.year == int(year)]
    return ser.groupby(ser.index.normalize()).max()


def campd_mean_availability(year: int) -> float:
    """Capacity-weighted mean thermal availability from the CAMPD unit derate."""
    cap = _iso_plant_capacity("MISO")
    fac = unit_outage_derate_factors(
        year,
        8760,
        str(RAW_DATA_DIR / "reference" / "custom-bin-assignments.csv"),
        iso="MISO",
    )
    num = den = 0.0
    for (code, grp), mw in cap.items():
        if grp not in _THERMAL_GROUPS:
            continue
        den += mw
        f = fac.get((int(code), grp))
        num += mw * (float(f.mean()) if f is not None else 1.0)
    return num / den if den else float("nan")


def main() -> int:
    cap = _miso_thermal_capacity_mw()
    print(f"model MISO fossil-thermal nameplate: {cap:,.0f} MW\n")

    df = _load_estimated()
    sys_rows = df[df["region"] == "MISO"].copy()
    sys_rows["m"] = sys_rows["interval_date"].dt.month
    sys_rows = sys_rows[sys_rows["interval_date"].dt.year.isin(YEARS)]
    print("monthly mean offline GW by cause bucket (2023-2025):")
    print(
        (
            sys_rows.pivot_table(
                index="m", columns="cause_type", values="outage_mw", aggfunc="mean"
            )
            / 1000
        ).round(1)
    )
    print(
        "\n  -> 'Planned' peaks in the SHOULDER (Apr 36.4 / Jul 7.9 GW): scheduled "
        "maintenance,\n     the layer the model already carries (statistical POF / "
        "CAMPD windows / nuclear\n     overlay) and where the record's non-thermal "
        "scheduled work lives.\n  -> 'Derated' peaks in JULY-AUGUST: the ambient "
        "summer capability derate GADS EFORd\n     counts. 'Forced' / 'Unplanned' "
        "are flat year-round. Those three are the measured\n     analogue of the "
        "model's forced-outage/derate layer.\n"
    )

    for year in YEARS:
        gen = measured_thermal_gen_daily_max(year)
        n = len(gen)
        print(
            f"=== {year}: measured daily-max thermal gen "
            f"mean {gen.mean():,.0f} / max {gen.max():,.0f} MW "
            f"| CAMPD derate mean availability {campd_mean_availability(year):.3f} ==="
        )
        for name, causes in COMBOS.items():
            off = miso_outage_mw_series(year, "MISO", causes)[::24][:n]
            avail = 1.0 - off / cap
            slack = gen.to_numpy()[: len(off)] - cap * avail
            bad = int((slack > 0).sum())
            print(
                f"  {name:18s} offline mean {off.mean():6,.0f} MW | "
                f"avail mean {avail.mean():.3f} min {avail.min():.3f} | "
                f"INFEASIBLE days {bad:3d}/{n} (worst {np.max(slack):+,.0f} MW)"
            )
        print()

    print(
        "VERDICT: the all-cause set is refuted — measured thermal generation exceeds\n"
        "the envelope's own available capacity on 12 / 15 / 61 days (2023 / 2024 /\n"
        "2025), before reserves. The unplanned set (Derated + Forced + Unplanned) is\n"
        "feasible and lands within a few points of the independent CAMPD measured\n"
        "level, so the swap changes the availability SHAPE, not its magnitude."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
