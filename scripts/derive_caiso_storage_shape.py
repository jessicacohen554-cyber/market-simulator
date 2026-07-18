"""Derive the measured CAISO battery dispatch-shape envelope (caiso-99 Mechanism B).

Writes ``data/raw/reference/caiso-storage-shape-envelope.csv``: per (year,
hour-of-day) quantiles of the CAISO battery fleet's MEASURED charge and
discharge rates, expressed as fractions of the installed battery fleet MW in
that hour's month. The p95 column is the anchor statistic the LP consumes
(``ScenarioConfig.caiso_storage_shape_anchor``); p90/p99 are emitted for
transparency only and are never solved against.

Sources (both committed raw inputs, no LP output in the loop):
  - EIA-930 CISO wide-hourly ``NG: OTH`` — the measured CAISO battery net
    (discharge +, charge −). The net-generation identity closes to <1 MW/h on
    the reported fuel components, so OTH carries the whole battery term
    (FINDING-caiso98 §2/§8 provenance).
  - EIA-860 energy-storage operable schedule via
    ``market_sim.model.storage.load_eia860_storage`` — the monthly installed
    battery fleet MW (COD month-precise), the SAME fleet basis the LP's vintage
    ramp dispatches. Pumped storage is excluded from both numerator and
    denominator (not an LESR; EIA-930 OTH does not carry Helms pumping).

Derivation is fleet-normalized so the envelope regenerates for any future
year: env[hod] × (that year's fleet MW) is the capability bound. The p95
across days is the repo-standard measured-capability statistic (the corridor
measured-p95 ATC / GTC p95 convention) — chosen a priori, NOT swept against
any residual (rule 25).

Rule 23: this derivation re-runs ONLY when its source data (EIA-930 CISO
hourly, EIA-860 energy-storage schedule) updates — never because a backcast
residual moved. Re-derivation commits must cite the data change.

Usage: python scripts/derive_caiso_storage_shape.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import set_eia860_vintage  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.storage import load_eia860_storage  # noqa: E402

EIA930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
OUT = REPO / "data" / "raw" / "reference" / "caiso-storage-shape-envelope.csv"
YEARS = (2023, 2024, 2025)
QUANTILES = (0.90, 0.95, 0.99)
# Hours per month of a non-leap 8760 model year (the model frame).
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def monthly_battery_fleet_mw(year: int) -> np.ndarray:
    """Return the (12,) installed CAISO battery MW per month of ``year``.

    Uses the canonical EIA-860 snapshot exactly as the backcast solve does
    (``set_eia860_vintage(None)``; ``load_eia860_storage`` filters units
    commissioned after ``year`` and masks each unit to its COD month), so the
    envelope denominator is the same fleet basis the LP's caps scale.
    """
    set_eia860_vintage(None)
    cfg = ScenarioConfig(mode="backcast", storage_vintage_ramp=True)
    units = load_eia860_storage("CAISO", year, cfg)
    fleet = np.zeros(12)
    for u in units:
        if u.tech_name == "pumped_storage":
            continue
        fleet += np.array(
            u.monthly_power_mw
            if u.monthly_power_mw is not None
            else [u.power_cap_mw] * 12,
            dtype=float,
        )
    return fleet


def measured_net_battery(year: int) -> np.ndarray:
    """Return the (8760,) measured net-battery MW (discharge +, charge −)."""
    d = pd.read_parquet(EIA930, columns=["Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    dy = d[d["Local date"].dt.year == year].sort_values(["Local date", "Hour"])
    v = np.nan_to_num(dy["NG: OTH"].to_numpy(dtype=float))
    return v[:8760] if len(v) >= 8760 else np.pad(v, (0, 8760 - len(v)))


def main() -> int:
    rows = []
    month_of_hour = np.repeat(np.arange(12), np.array(DAYS_IN_MONTH) * 24)[:8760]
    hod = np.arange(8760) % 24
    for year in YEARS:
        net = measured_net_battery(year)
        fleet = monthly_battery_fleet_mw(year)
        fleet_h = fleet[month_of_hour]
        chg_rate = np.clip(-net, 0.0, None) / fleet_h
        dis_rate = np.clip(net, 0.0, None) / fleet_h
        for h in range(24):
            m = hod == h
            row = {"year": year, "hod": h}
            for q in QUANTILES:
                tag = f"p{int(q * 100)}"
                row[f"chg_frac_{tag}"] = round(float(np.quantile(chg_rate[m], q)), 4)
                row[f"dis_frac_{tag}"] = round(float(np.quantile(dis_rate[m], q)), 4)
            rows.append(row)
        print(
            f"{year}: fleet Jan {fleet[0]:.0f} -> Dec {fleet[-1]:.0f} MW; "
            f"chg p95 belly(10-14) "
            f"{np.mean([r['chg_frac_p95'] for r in rows if r['year'] == year and 10 <= r['hod'] <= 14]):.3f}; "
            f"dis p95 evening(17-21) "
            f"{np.mean([r['dis_frac_p95'] for r in rows if r['year'] == year and 17 <= r['hod'] <= 21]):.3f}"
        )
    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
