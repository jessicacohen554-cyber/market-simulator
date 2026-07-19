"""Build an ESTIMATED 2023 ERCOT storage-AS series by intensity transfer.

SUPERSEDED — use ``scripts/data/build_ercot_as_by_restype_from_60day.py``, which
writes the MEASURED 2023 storage-AS series from the in-repo 60-Day DAM
Disclosure Gen Resource Data (battery awards). That measured series means
~1249 MW; this transfer estimate meant only ~832 MW — it undercounts real 2023
battery AS by ~50%, because 2023's AS-per-GW intensity was well above the
2024/2025 anchors it assumes. This script is retained only as a documented
sensitivity / fallback.

The premise it was written under was wrong: real 2023 per-resource AS data IS
in the repo (``data/raw/ercot/`` — the per-generation-resource
``60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_*.parquet`` carry
battery AS awards, with ``DAMASAGGNP419_2023.parquet`` and
``ASPLANNP433_2023.parquet`` as cross-checks); only the NP3-911 *2-Day* feed in
``data/raw/ercot-AS/`` begins ~Dec-2023. The intensity transfer assumes
storage AS *per GW of battery fleet* is empirically stable in
the years we do have (2024: 2045 MW / ~6.5 GW = 0.31; 2025: 2824 / ~10 = 0.28),
so we transfer it: the 2023 battery fleet power is known (EIA-860 COD ramp,
already in the model), and 2023 storage AS is the measured 2024 series rescaled
to the 2023 fleet, month by month:

    storage_AS_2023[h] = storage_AS_2024[h] * (P2023[h] / P2024[h]) * factor

clipped to the 2023 fleet power. ``factor`` brackets the intensity (1.0 ~= 0.31;
1.3 ~= 0.40, for 2023's harder AS chase under scarcity). ECRS did not exist
before 2023-06-10, so the pre-June hours are scaled down by the 2024 ECRS share
of (non-NonSpin) AS.

This is an ESTIMATE / sensitivity, not measured — usable to test the 2023
scarcity-price hypothesis, never a keeper. Only the ``storage`` column is
populated (thermal AS was negligible in 2024/25 and is not transferred); the
other columns are zero.

Run:
    python scripts/data/build_ercot_storage_as_2023_estimate.py            # factor 1.0
    python scripts/data/build_ercot_storage_as_2023_estimate.py --factor 1.3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from market_sim.config.paths import RAW_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import _hour_to_month_index
from market_sim.model.storage import load_eia860_storage

HOURS_PER_YEAR = 8760
REPO_ROOT = Path(__file__).resolve().parents[2]
# ERCOT AS disclosure zips under the single W1 data root (paths.RAW_DIR =
# data/raw); the pre-W1 ``inputs/raw-data`` path was removed by the relocation.
AS_DIR = RAW_DIR / "ercot-AS"
# ERCOT ECRS went live 2023-06-10 (hour-of-year index on the non-leap clock).
ECRS_START_HOUR = (31 + 28 + 31 + 30 + 31 + 9) * 24  # 2023-06-10 00:00


def fleet_power(year: int) -> np.ndarray:
    """Return ERCOT's (8760,) hourly battery fleet power (MW) for ``year``.

    Uses the same EIA-860 COD ramp the backcast dispatches against
    (``storage_vintage_ramp`` on, as for run121), so mid-year commissioning is
    reflected month by month.
    """
    cfg = ScenarioConfig(
        iso="ERCOT",
        weather_year=year,
        mode="backcast",
        hours=HOURS_PER_YEAR,
        vintage_capacity_ramp=True,
        storage_vintage_ramp=True,
    )
    units = load_eia860_storage("ERCOT", year, cfg)
    month_idx = _hour_to_month_index(HOURS_PER_YEAR)
    power = np.zeros(HOURS_PER_YEAR, dtype=float)
    for u in units:
        if u.monthly_power_mw is not None:
            power += np.asarray(u.monthly_power_mw, dtype=float)[month_idx]
        else:
            power += float(u.power_cap_mw)
    return power


def ecrs_share_2024() -> float:
    """2024 ECRS share of (non-NonSpin) up-AS, to discount pre-June 2023."""
    tot = pd.read_parquet(AS_DIR / "ercot_2024_as_up_mw.parquet")
    up = (
        tot["regup_mw"]
        + tot["rrspfr_mw"]
        + tot["rrsffr_mw"]
        + tot["rrsufr_mw"]
        + tot["ecrss_mw"]
        + tot["ecrsm_mw"]
    )
    ecrs = tot["ecrss_mw"] + tot["ecrsm_mw"]
    return float(ecrs.sum() / up.sum())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_ercot_storage_as_2023_estimate")
    p.add_argument(
        "--factor",
        type=float,
        default=1.0,
        help="Intensity bracket multiplier (1.0~=0.31, 1.3~=0.40).",
    )
    args = p.parse_args(argv)

    storage_2024 = pd.read_parquet(AS_DIR / "ercot_2024_as_by_restype_hourly.parquet")[
        "storage"
    ].to_numpy(dtype=float)

    p23, p24 = fleet_power(2023), fleet_power(2024)
    ratio = np.divide(p23, p24, out=np.zeros_like(p23), where=p24 > 0)
    storage_2023 = storage_2024 * ratio * args.factor

    # Pre-June 2023: ECRS did not exist — remove its (2024) share.
    ecrs = ecrs_share_2024()
    storage_2023[:ECRS_START_HOUR] *= 1.0 - ecrs
    # Never reserve more than the fleet physically has.
    storage_2023 = np.clip(storage_2023, 0.0, p23)

    print(
        f"2023 storage-AS estimate (factor {args.factor}, ECRS share "
        f"{ecrs:.2f} removed pre-Jun):"
    )
    print(
        f"  2023 fleet power : mean {p23.mean() / 1000:.2f} GW "
        f"(Jan {p23[:744].mean() / 1000:.2f} -> Dec {p23[-744:].mean() / 1000:.2f})"
    )
    print(f"  2024 fleet power : mean {p24.mean() / 1000:.2f} GW")
    print(
        f"  storage-AS 2023  : mean {storage_2023.mean():.0f} MW, "
        f"peak {storage_2023.max():.0f} MW "
        f"(2024 was {storage_2024.mean():.0f} / {storage_2024.max():.0f})"
    )
    print(
        f"  implied intensity: {storage_2023.mean() / p23.mean():.2f} "
        f"(2024 {storage_2024.mean() / p24.mean():.2f})"
    )

    frame = pd.DataFrame({"hour": np.arange(HOURS_PER_YEAR, dtype="int64")})
    for col in ("gas_cc", "gas_ct", "gas_st", "coal", "load", "thermal_total"):
        frame[col] = 0.0  # only `storage` is estimated for 2023
    frame["storage"] = storage_2023

    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata(
        {
            "source": "ESTIMATED — intensity transfer from 2024 measured storage "
            "AS, rescaled by EIA-860 COD fleet power; NOT measured 2023.",
            "factor": str(args.factor),
            "year": "2023",
        }
    )
    out = AS_DIR / "ercot_2023_as_by_restype_hourly.parquet"
    pq.write_table(table, out)
    print(f"  Wrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
