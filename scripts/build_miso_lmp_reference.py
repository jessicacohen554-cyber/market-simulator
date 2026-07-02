"""Build MISO's actual-LMP reference block from the hourly validation source.

The other multi-zone ISOs (PJM/CAISO/NYISO/NEISO) derive their
``data/raw/_validation-source/actual_lmp.json`` block straight from raw market
price exports in ``scripts/derive_actual_lmp.py``. MISO's raw hub exports are
not staged in the repo; instead the measured hourly system series is already
committed as ``data/raw/_validation-source/actual_lmp_hourly_MISO.parquet``
(columns ``year``, ``hour``, ``rt``, ``da`` on the model's fixed non-leap
8760-hour local calendar — the same sidecar shape the other ISOs' builders
emit). This script reduces that committed parquet to the JSON block the
backcast scorer reads, mirroring the ``_pjm`` record schema exactly:

    "MISO": {"2023": {"da": ..., "rt": ...,
                      "da_mon": [...12...], "rt_mon": [...12...],
                      "da_pct": {min, p1, ..., p99, max},
                      "rt_pct": {...},
                      "src": "..."}, ...}

The block is the SCORING target derived from measured market data — never
pinned to or derived from model output. It is merged into ``actual_lmp.json``
in place; every other ISO's block is left byte-identical (the file round-trips
through ``json.dumps(..., indent=2)``).

Hub -> model-zone mapping: when the per-hub zonal parquet
(``actual_lmp_hourly_zonal_MISO.parquet``, scope decision D6 — built by
``scripts/derive_miso_hub_lmp.py`` from the eight named trading hubs) is
present, the MISO record additionally carries the ``zones`` sub-dict the
other zonal ISOs (NYISO/NEISO) carry: ``{model_zone: {da, rt, da_mon,
rt_mon}}``, each zone the simple mean of its member hubs (MINN.HUB -> West,
ILLINOIS.HUB -> Illinois, INDIANA.HUB -> Indiana, MICHIGAN.HUB -> East,
ARKANSAS/LOUISIANA/TEXAS/MS.HUB -> South). MISO-Plains (LRZ 3+5, IA/MO) has
no trading hub; its entry is the documented proxy — the simple mean of
MINN.HUB and ILLINOIS.HUB, the two hubs bracketing the Iowa/Missouri
wheel-through corridor — and is flagged ``"proxy"`` in the record. Without
the zonal parquet the six model zones share the system price, as before.

Usage:
    python scripts/build_miso_lmp_reference.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# Reuse the exact helpers/constants the other ISO builders use so the MISO
# record is schema-identical (same percentile levels, monthly reducer, calendar
# and output path) rather than a parallel re-implementation that could drift.
from derive_actual_lmp import (  # noqa: E402
    OUT,
    _HOURS_PER_YEAR,
    _MONTH_START_HOUR,
    _by_month,
    _pct,
)
from market_sim.config import paths  # noqa: E402  (resolves the data root)

DEFAULT_YEARS = (2023, 2024, 2025)
HOURLY_PARQUET = paths.CALIBRATION_DIR / "actual_lmp_hourly_MISO.parquet"
ZONAL_PARQUET = paths.CALIBRATION_DIR / "actual_lmp_hourly_zonal_MISO.parquet"
MISO_SRC = (
    "MISO RT/DA LMP, system reference hourly series (actual_lmp_hourly_MISO."
    "parquet — verified hour-for-hour identical to the INDIANA.HUB series in "
    "the D6 per-hub staging, i.e. MISO's usual Indiana Hub price reference)"
)
MISO_ZONAL_SRC = (
    "MISO RT-final/DA-ex-post LMP, named trading hubs mapped to model zones "
    "(actual_lmp_hourly_zonal_MISO.parquet; MISO-Plains = MINN+ILLINOIS hub "
    "mean proxy, no LRZ 3/5 hub exists)"
)

# MISO-Plains (LRZ 3+5, IA/MO) has no named trading hub. Documented proxy:
# the simple mean of the two hubs bracketing the Iowa/Missouri wheel-through
# corridor (scope decision D6, miso-zonal-refinement-scope.md §7).
PLAINS_ZONE = "MISO-Plains"
PLAINS_PROXY_HUBS = ("MINN.HUB", "ILLINOIS.HUB")


def _month_of_hour() -> np.ndarray:
    """Month label (1-12) for each fixed non-leap hour-of-year (0..8759).

    The dense parquet calendar is the same Feb-29-dropped clock used by
    ``derive_actual_lmp._hour_index``; ``_MONTH_START_HOUR`` gives each month's
    starting hour, so a searchsorted over those bounds recovers the month for
    every hour. Lets the monthly reducer reuse ``_by_month`` unchanged.
    """
    bounds = np.asarray(_MONTH_START_HOUR[1:])  # starts of Feb..Dec
    return np.searchsorted(bounds, np.arange(_HOURS_PER_YEAR), side="right") + 1


def _record(g: pd.DataFrame, months: np.ndarray) -> dict:
    """Build one year's ``{da, rt, da_mon, rt_mon, da_pct, rt_pct, src}`` record.

    ``g`` is the year's dense hourly frame (``hour`` 0..8759, ``rt``/``da``
    columns, NaN where the local calendar has no value); ``months`` the matching
    per-hour month labels. Means/percentiles ignore NaN, exactly as the other
    ISO builders do.
    """
    g = g.sort_values("hour")
    rt = g["rt"].to_numpy(float)
    da = g["da"].to_numpy(float)
    return {
        "da": round(float(np.nanmean(da)), 2),
        "rt": round(float(np.nanmean(rt)), 2),
        "da_mon": _by_month(da, months),
        "rt_mon": _by_month(rt, months),
        "da_pct": _pct(da),
        "rt_pct": _pct(rt),
        "src": MISO_SRC,
    }


def _zone_records(zdf: pd.DataFrame, months: np.ndarray) -> dict:
    """Build the ``zones`` sub-dict for one year of the zonal hub parquet.

    Each mapped zone is the simple mean of its member hubs per hour;
    MISO-Plains is the documented MINN+ILLINOIS hub-mean proxy (no LRZ 3/5
    hub exists) and carries a ``proxy`` marker. Record shape mirrors the
    NYISO/NEISO ``zones`` entries: ``{da, da_mon, rt, rt_mon}``.
    """
    zones: dict[str, dict] = {}
    per_zone = zdf.groupby(["zone", "hour"])[["rt", "da"]].mean()
    plains = (
        zdf[zdf["hub"].isin(PLAINS_PROXY_HUBS)].groupby("hour")[["rt", "da"]].mean()
    )
    for zone in sorted(zdf["zone"].unique()) + [PLAINS_ZONE]:
        g = plains if zone == PLAINS_ZONE else per_zone.loc[zone]
        g = g.reindex(range(_HOURS_PER_YEAR))
        rt = g["rt"].to_numpy(float)
        da = g["da"].to_numpy(float)
        rec = {
            "da": round(float(np.nanmean(da)), 2),
            "da_mon": _by_month(da, months),
            "rt": round(float(np.nanmean(rt)), 2),
            "rt_mon": _by_month(rt, months),
        }
        if zone == PLAINS_ZONE:
            rec["proxy"] = "+".join(PLAINS_PROXY_HUBS) + " mean (no LRZ 3/5 hub)"
        zones[zone] = rec
    return zones


def build(years) -> dict:
    """Return ``{str(year): record}`` for MISO over ``years`` present in the parquet."""
    df = pd.read_parquet(HOURLY_PARQUET)
    zonal = pd.read_parquet(ZONAL_PARQUET) if ZONAL_PARQUET.is_file() else None
    months = _month_of_hour()
    out: dict[str, dict] = {}
    for year in years:
        g = df[df["year"] == int(year)]
        if g.empty:
            continue
        rec = _record(g, months)
        if zonal is not None:
            zg = zonal[zonal["year"] == int(year)]
            if not zg.empty:
                rec["zones"] = _zone_records(zg, months)
                rec["zones_src"] = MISO_ZONAL_SRC
        out[str(int(year))] = rec
        zn = len(rec.get("zones", {}))
        print(f"  MISO {year}: da ${rec['da']} rt ${rec['rt']} ({zn} zones)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    args = ap.parse_args()
    block = build(args.years)
    if not block:
        raise SystemExit(f"no MISO years built from {HOURLY_PARQUET}")
    # Merge in place: load the committed reference, replace only the MISO block,
    # and re-dump with the same indent so every other ISO stays byte-identical.
    merged: dict[str, dict] = {}
    if OUT.exists():
        merged = json.loads(OUT.read_text())
    merged.setdefault("MISO", {}).update(block)
    OUT.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"wrote {OUT} (MISO: {len(block)} years)")


if __name__ == "__main__":
    main()
