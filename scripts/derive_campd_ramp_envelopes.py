"""Derive measured plant-level hourly ramp envelopes from CAMPD gross load.

Source basis for the P1 ramp-limit rows (``ScenarioConfig.ramp_limits``,
``model/dispatch._build_ramp_rows``; design: docs/ramp-locational-design-2026-07.md
§1). Engineering per-minute ramp rates (CC ~5 %/min) exceed pmax at hourly LP
resolution, so a class-typical ramp row never binds. The binding physics at
hourly resolution is the start-to-dispatchable trajectory plus operational
practice — a commitment envelope, not a MW/min rate — and the measured
plant-level hourly delta captures exactly that, because every start, warm-up
and shutdown the plant ever performed is in its CEMS trace.

For every model-fleet thermal plant with CAMPD coverage, pooled across the
requested vintages (default 2023-2025), per (facility, unit-class bucket):

- ``ramp_up_mw``  = the MAX observed 1-h increase in summed gross load. Max,
  not a quantile: the envelope must never make the backcast fleet unable to do
  something it actually did — the bound removes only moves never observed
  (and the max includes every start trajectory).
- ``ramp_dn_mw``  = the max observed 1-h decrease EXCLUDING trip-to-offline
  deltas (deltas ending below ``TRIP_FLOOR_FRAC`` x observed pmax). A trip is
  an availability event — already modelled by the outage overlay — not a
  dispatch choice; leaving trips in would inflate the down-envelope to ~pmax
  and disarm it.
- Hours adjacent to CEMS reporting gaps are excluded from the diffs.
- Facilities with fewer than ``MIN_OBS_HOURS`` observed online hours fall back
  to the ISO-class row (``plant_code = 0``): the capacity-weighted median
  envelope FRACTION of the measured plants in the bucket, applied by the
  loader as ``frac x plant pmax``.

The unit-class *bucket* mirrors the model's plant_group families so a plant
with both a combined-cycle block and standalone peakers is enveloped
separately per family (CAMPD ``unitType`` -> CC / CT / ST). CT buckets are
derived and written for the audit record, but the loader prunes any group
whose envelope cannot bind (envelope >= plant capacity) — bang-bang CTs prune
out naturally, so no class-name gate exists anywhere (CLAUDE.md rule 18:
physics by parameters, not class names).

Output: ``data/raw/_processed-legacy/campd_ramp_envelopes_{ISO}.csv``,
consumed by :func:`market_sim.data.fleet.load_campd_ramp_envelopes`.

Governance (CLAUDE.md rules #12/#13/#23): a measured physical-capability
parameter in the same admissibility class as the CAMPD min-stable loads,
committed shares and measured run lengths — it regenerates from the CAMPD
pipeline for any vintage, responds to fleet change, and never reads a price
or volume residual. It re-derives only when its source data updates.

Usage::

    python scripts/derive_campd_ramp_envelopes.py --iso CAISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import (  # noqa: E402
    CAMPD_UNIT_PLANT_REMAP,
    states_for_iso,
)
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

# CAMPD unitType -> model plant_group family bucket. Mirrors the fleet's
# CC_*/CT_*/ST_*/COAL split so a mixed facility is enveloped per family.
_UNIT_TYPE_BUCKET = {
    "Combined cycle": "CC",
    "Combustion turbine": "CT",
}
# Everything else (tangentially/wall-fired boilers, cyclone, stoker, bubbling
# fluidized bed, ...) is a steam unit: coal or gas-steam alike ramp as boilers.
_DEFAULT_BUCKET = "ST"

# A down-delta ending below this fraction of observed pmax is a trip/shutdown
# to offline — an availability event, excluded from the down-envelope.
TRIP_FLOOR_FRAC = 0.05
# Facilities with fewer observed online hours fall back to the class row.
MIN_OBS_HOURS = 4000
# Ignore micro-facilities whose envelope noise would pollute the class medians.
MIN_PMAX_MW = 25.0


def _bucket(unit_type: str) -> str:
    """Map a CAMPD ``unitType`` string onto the CC/CT/ST family bucket."""
    for key, bucket in _UNIT_TYPE_BUCKET.items():
        if key.lower() in str(unit_type).lower():
            return bucket
    return _DEFAULT_BUCKET


def derive_envelopes(iso: str, years: list[int]) -> pd.DataFrame:
    """Return the pooled per-(facility, bucket) hourly ramp envelope table."""
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    fleet_plants = {int(g.plant_code) for g in fleet if g.plant_code}

    frames = []
    for state in states_for_iso(iso):
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "unitId",
                    "date",
                    "hour",
                    "grossLoad",
                    "unitType",
                ],
            )
            # CAMPD facilityId is the ORIS code as a string; the fleet's
            # plant_code is the same code as int.
            df["facilityId"] = pd.to_numeric(df.facilityId, errors="coerce")
            # CEMS-to-EIA split-plant remap (campd.CAMPD_UNIT_PLANT_REMAP):
            # repowered CCGTs filing under a legacy boiler ORIS move to the
            # EIA plant the model fleet knows them by (315/CT* -> 62115, ...).
            for (fac, unit), eia_plant in CAMPD_UNIT_PLANT_REMAP.items():
                mask = (df.facilityId == fac) & (df.unitId == unit)
                if mask.any():
                    df.loc[mask, "facilityId"] = eia_plant
            df = df[df.facilityId.isin(fleet_plants)]
            if len(df):
                frames.append(df)
    if not frames:
        raise SystemExit(f"no CAMPD unit-level data found for {iso} years {years}")
    df = pd.concat(frames, ignore_index=True)
    df["bucket"] = df.unitType.map(_bucket)

    # Facility-bucket-hour aggregate gross load (MW). NaN gross load = offline
    # or not reported; sum with min_count=1 keeps all-NaN hours as NaN so the
    # diff across a reporting gap is excluded rather than treated as a ramp.
    ph = (
        df.groupby(["facilityId", "bucket", "date", "hour"])["grossLoad"]
        .sum(min_count=1)
        .reset_index()
    )
    ph["ts"] = pd.to_datetime(ph.date) + pd.to_timedelta(ph.hour, unit="h")

    rows = []
    class_pool: dict[str, list[tuple[float, float, float]]] = {}
    for (fid, bucket), g in ph.groupby(["facilityId", "bucket"]):
        # asfreq('h') inserts NaN at gap hours -> diff() is NaN across gaps.
        s = g.set_index("ts")["grossLoad"].sort_index().asfreq("h").fillna(0.0)
        # Reinstate NaN at true reporting gaps: hours absent from the extract
        # entirely (asfreq-inserted) stay 0 <- offline is a legitimate 0 in
        # CAMPD (grossLoad null when not operating), so a 0 here is "offline",
        # and start/stop deltas are real ramps we must keep. Only hours the
        # extract never covered (outside its date span) are excluded by the
        # span itself.
        d = s.diff()
        pmax_obs = float(s.max())
        n_online = int((s > 0).sum())
        if pmax_obs < MIN_PMAX_MW:
            continue
        up = float(d.max()) if len(d) else np.nan
        # Down-envelope: exclude trip-to-offline deltas (endpoint below the
        # trip floor). A shutdown *trajectory* (high -> mid -> low over hours)
        # stays in; a one-hour collapse to ~0 is a trip/availability event.
        dn_mask = (d < 0) & (s >= TRIP_FLOOR_FRAC * pmax_obs)
        dn = float(-d[dn_mask].min()) if dn_mask.any() else 0.0
        basis = "plant" if n_online >= MIN_OBS_HOURS else "sparse"
        rows.append(
            {
                "plant_code": int(fid),
                "bucket": bucket,
                "pmax_obs_mw": round(pmax_obs, 1),
                "n_online_hours": n_online,
                "ramp_up_mw": round(up, 1),
                "ramp_dn_mw": round(dn, 1),
                "basis": basis,
            }
        )
        if basis == "plant":
            class_pool.setdefault(bucket, []).append((pmax_obs, up, dn))

    out = pd.DataFrame(rows)
    # ISO-class fallback rows (plant_code = 0): capacity-weighted median
    # envelope fraction across the well-observed plants of each bucket.
    for bucket, pool in sorted(class_pool.items()):
        arr = np.array(pool)  # (n, 3): pmax, up, dn
        up_frac = float(np.median(arr[:, 1] / arr[:, 0]))
        dn_frac = float(np.median(arr[:, 2] / arr[:, 0]))
        out = pd.concat(
            [
                out,
                pd.DataFrame(
                    [
                        {
                            "plant_code": 0,
                            "bucket": bucket,
                            "pmax_obs_mw": np.nan,
                            "n_online_hours": int(arr.shape[0]),
                            "ramp_up_mw": round(up_frac, 4),
                            "ramp_dn_mw": round(dn_frac, 4),
                            "basis": "class_fraction",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    return out.sort_values(["bucket", "plant_code"]).reset_index(drop=True)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()

    out = derive_envelopes(args.iso.upper(), args.years)
    dest = PROCESSED_DIR / f"campd_ramp_envelopes_{args.iso.upper()}.csv"
    out.to_csv(dest, index=False)
    measured = out[out.basis == "plant"]
    print(f"wrote {dest} ({len(out)} rows, {len(measured)} well-observed plants)")
    for bucket, g in measured.groupby("bucket"):
        frac = g.ramp_up_mw / g.pmax_obs_mw
        print(
            f"  {bucket}: {len(g)} plants, up-envelope frac "
            f"median {frac.median():.2f} / p90 {frac.quantile(0.9):.2f}"
        )


if __name__ == "__main__":
    main()
