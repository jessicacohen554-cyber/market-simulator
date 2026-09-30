#!/usr/bin/env python
"""Derive each ERCOT CC / ST_GAS plant's measured commitment PROFILE per year (R-ERCOT-19).

The input to two backcast-only sub-gates, both reading the PRIOR year (Y-1):

* ``ScenarioConfig.cc_committed_prior_year_commitment_eligibility`` — the
  ERCOT-139 below-cost CC committed-block level
  (``offer_curves.apply_cc_committed_offer_margin``) is weighted by the plant's
  measured probability of being online in that month x hour-of-day.
* ``ScenarioConfig.netload_drag_prior_year_hour_profile`` — each plant's ST_GAS
  net-load drag floor (``fleet.floors.apply_gas_st_netload_drag_floor``) is
  reshaped across hours by the same probability (mean-preserving per plant).

Why it exists. The ERCOT-139 level is a measurement of how ONLINE CCs offer
their min-load block (60-Day SCED TPO-Price1 over online resources). The LP has
no commitment state, so it makes that below-cost block available in EVERY
available hour, and the model part-loads high-heat-rate CCs through hours the
meter says they are off: across every ERCOT CC plant, corr(measured heat rate,
log model/EIA-923) is 0.68-0.80 in all seven years, while 2024-25 60-Day DAM
first-segment offers are heat-rate-flat (corr +0.19 / -0.16) and DAM ON-share
falls with heat rate (corr -0.60 / -0.34)
(``docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md``).
The same hour-eligibility question is what convicts the residual
``st_netload_drag`` D-4 rows (3452, 3628, 3491): the floor binds in hours the
plant's own meter says it is off.

Construction — nothing here reads a model output, a price or a residual:

* Fleet: ``custom-bin-assignments.csv`` CC_REGULAR plants and drag-covered
  ST_GAS plants (not in ``ST_GAS_PEAKER_PLANTS``).
* Units: CAMPD unit-level ``TX_<year>.parquet``. CC plants keep their
  combustion-turbine / combined-cycle units (a co-sited boiler belongs to
  another bin); ST_GAS plants keep their non-CT/CC units, with the two split
  facilities routed exactly as ``data.outages`` and the drag derive do
  (34702 = W A Parish non-coal steamers, 49392 = Barney M Davis unit 1; the
  parents 3470 / 4939 never count those units twice).
* On-state: ``opTime > 0`` (the unit operated in that hour), falling back to
  ``grossLoad > 0`` where ``opTime`` is null. Units are weighted by their own
  measured annual max gross load, so ``on_frac`` is the plant's online
  CAPACITY share.
* Clock: the model's fixed local-standard non-leap 8760 (Feb 29 dropped), then
  averaged to month x hour-of-day (12 x 24 = 288 rows per plant-year).
* A plant with no CAMPD units that year is NOT written to the CSV (it is
  listed under ``unmetered`` in the ``.meta.json`` sidecar, with each year's
  source sha256); consumers leave such a plant untouched.

Frozen (rule 23 [R-FROZEN-DERIVE]): re-derive only when the CAMPD unit-level
source updates or a new year's vintage lands — never because a residual moved.

Usage::

    python scripts/data/derive_ercot_prior_year_commitment_profile.py \
        [--years 2019 2020 2021 2022 2023 2024] \
        [--out data/raw/_validation-source/ercot_prior_year_commitment_profile.csv]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))  # repo root: canonical scripts.* sibling imports
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402

from scripts.data.derive_ercot_dam_cleared_share import HOURS  # noqa: E402
from scripts.probes.ercot90_stgas_shoulder_measure import (  # noqa: E402
    _MONTH_OF_HOY,
    _MONTH_START_HOUR,
    _SPLIT_PARENT,
    _WAP_COAL_UNITS,
    BIN_CSV,
    CAMPD_UNIT_DIR,
    _st_gas_plants,
)

DEFAULT_OUT = CALIBRATION_DIR / "ercot_prior_year_commitment_profile.csv"
# Vintages consumed as Y-1 by the 2020-2025 backcast years (2019 has no TX
# 2018 extract on disk, so it fails closed in the consumers).
DEFAULT_YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def _sha256(path: Path) -> str:
    """Return the hex sha256 of ``path`` (source-identity record)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _plants() -> pd.DataFrame:
    """CC_REGULAR plants plus drag-covered ST_GAS plants: ``plant_code, klass``."""
    bins = pd.read_csv(BIN_CSV)
    cc = bins.loc[bins["Plant_Group"] == "CC_REGULAR", ["Plant_Code"]].copy()
    cc["klass"] = "CC_REGULAR"
    st = _st_gas_plants()
    st = st.loc[st["drag_covered"], ["Plant_Code"]].copy()
    st["klass"] = "ST_GAS"
    out = pd.concat([cc, st], ignore_index=True)
    out["Plant_Code"] = out["Plant_Code"].astype(int)
    return out.drop_duplicates().rename(columns={"Plant_Code": "plant_code"})


def _unit_mask(raw: pd.DataFrame, fid: np.ndarray, code: int, klass: str) -> np.ndarray:
    """Boolean row mask of the CAMPD units that belong to one model plant bin."""
    ut = raw["unitType"].astype(str).str.lower()
    is_ct_cc = (
        ut.str.contains("combustion turbine") | ut.str.contains("combined cycle")
    ).to_numpy()
    unit = raw["unitId"].astype(str).to_numpy()
    if klass == "CC_REGULAR":
        return (fid == code) & is_ct_cc
    parent = _SPLIT_PARENT.get(code, code)
    m = (fid == parent) & ~is_ct_cc
    if code == 34702:  # W A Parish gas steamers = non-coal, non-CT units
        m &= ~np.isin(unit, list(_WAP_COAL_UNITS))
    elif parent == 3470:
        m &= False
    if code == 49392:  # Barney M Davis steam unit 1
        m &= unit == "1"
    elif parent == 4939:
        m &= False
    return m


def _profile(sub: pd.DataFrame) -> np.ndarray | None:
    """Capacity-weighted online share per model hour (8760) for one plant's units."""
    if sub.empty:
        return None
    dt = pd.to_datetime(sub["date"])
    mo = dt.dt.month.to_numpy()
    dy = dt.dt.day.to_numpy()
    hh = pd.to_numeric(sub["hour"], errors="coerce").to_numpy(int)
    ok = ~((mo == 2) & (dy == 29))
    hoy = np.asarray(_MONTH_START_HOUR)[mo - 1] + (dy - 1) * 24 + hh
    gross = pd.to_numeric(sub["grossLoad"], errors="coerce").to_numpy(float)
    op = pd.to_numeric(sub["opTime"], errors="coerce").to_numpy(float)
    on = np.where(np.isnan(op), np.nan_to_num(gross, nan=0.0) > 0.0, op > 0.0)
    unit = sub["unitId"].astype(str).to_numpy()
    cap = pd.Series(np.nan_to_num(gross, nan=0.0)).groupby(unit).transform("max")
    w = cap.to_numpy(float)
    valid = ok & (hoy >= 0) & (hoy < HOURS)
    num = np.zeros(HOURS)
    np.add.at(num, hoy[valid], (w * on)[valid])
    w_tot = float(pd.Series(w, index=unit).groupby(level=0).max().sum())
    if w_tot <= 0.0:
        return None
    return num / w_tot


def derive(years: list[int]) -> pd.DataFrame:
    """Per-(plant, year, month, hour) measured online capacity share.

    Args:
        years: Calendar years to derive; each needs ``TX_<year>.parquet``.

    Returns:
        DataFrame with columns ``iso, plant_code, klass, year, month, hour,
        on_frac, metered, source_sha256``.
    """
    plants = _plants()
    hod = np.arange(HOURS) % 24
    rows = []
    for year in years:
        src = CAMPD_UNIT_DIR / f"TX_{year}.parquet"
        if not src.exists():
            raise SystemExit(f"{src} not on disk — cannot derive {year}")
        sha = _sha256(src)
        raw = pd.read_parquet(
            src,
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "opTime",
                "grossLoad",
                "unitType",
            ],
        )
        fid = (
            pd.to_numeric(raw["facilityId"], errors="coerce")
            .fillna(-1)
            .astype(int)
            .to_numpy()
        )
        for r in plants.itertuples(index=False):
            prof = _profile(raw.loc[_unit_mask(raw, fid, int(r.plant_code), r.klass)])
            if prof is None:
                grid = None
            else:
                grid = (
                    pd.DataFrame({"m": _MONTH_OF_HOY, "h": hod, "p": prof})
                    .groupby(["m", "h"])["p"]
                    .mean()
                )
            for m in range(1, 13):
                for h in range(24):
                    rows.append(
                        {
                            "iso": "ERCOT",
                            "plant_code": int(r.plant_code),
                            "klass": r.klass,
                            "year": int(year),
                            "month": m,
                            "hour": h,
                            "on_frac": (
                                round(float(np.clip(grid.loc[(m, h)], 0.0, 1.0)), 3)
                                if grid is not None
                                else None
                            ),
                            "metered": grid is not None,
                            "source_sha256": sha,
                        }
                    )
    return pd.DataFrame(rows)


def write_artifact(df: pd.DataFrame, out: Path) -> None:
    """Write the slim CSV (metered rows only) and its ``.meta.json`` provenance.

    The CSV carries ``iso, plant_code, klass, year, month, hour, on_frac`` for
    METERED plant-years only; the sidecar records each year's source sha256 and
    the unmetered plant-years, so the 64-character sha is not repeated per row.
    """
    import json

    met = df[df["metered"]]
    met[["iso", "plant_code", "klass", "year", "month", "hour", "on_frac"]].to_csv(
        out, index=False
    )
    unmet = (
        df.loc[~df["metered"], ["klass", "plant_code", "year"]]
        .drop_duplicates()
        .sort_values(["year", "klass", "plant_code"])
    )
    meta = {
        "derive": "scripts/data/derive_ercot_prior_year_commitment_profile.py",
        "source": "data/raw/campd-unit-level/TX_<year>.parquet",
        "source_sha256": {
            str(int(y)): str(g["source_sha256"].iloc[0]) for y, g in df.groupby("year")
        },
        "unmetered": [
            {"year": int(r.year), "klass": r.klass, "plant_code": int(r.plant_code)}
            for r in unmet.itertuples(index=False)
        ],
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=1) + "\n")


def main() -> None:
    """Derive the per-plant commitment-profile table and write the frozen artifact."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    df = derive(args.years)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_artifact(df, args.out)
    ann = df[df["metered"]].groupby(["klass", "plant_code", "year"])["on_frac"].mean()
    print(ann.unstack("year").round(3).to_string())
    print(f"wrote {len(df)} rows -> {args.out}")


if __name__ == "__main__":
    main()
