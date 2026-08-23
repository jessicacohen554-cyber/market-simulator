"""Derive MISO's ACROSS-UNIT offer-level dispersion quantile vector (miso-179).

The measured object is the **across-unit distribution of base offer LEVELS**
on the price-setting-eligible mass of MISO's masked DA energy-offer book,
normalized to a delivered-gas monthly reference so the vector is a markup
DISTRIBUTION that regenerates forward (PREREG
``PREREG-miso179-offer-level-dispersion-2026-08-23.md`` §3, committed BEFORE
this derive ran).

Construction, verbatim from the PREREG:

* **Corpus** — ``data/clean/energy-offers/MISO/DA/energy-offers_{2023..2025}
  .parquet`` (JJA, curated from the manifest-verified refetch; award columns
  dropped at curation, rule 13).
* **Population (BOOK-ELIG)** — unit-hours with ``unit_available_flag AND
  economic_flag AND NOT must_run_flag``; weight
  ``max(0, ecomax_mw - self_scheduled_mw)``. Emergency-limited mass excludes
  itself (ecomax <= 0 carries zero weight). A self-scheduled or must-run
  unit's energy is price-taking, so the conduct distribution the model
  consumes is identified on the mass that CAN set price.
* **Base offer level** — the unit-hour's step-1 price (the cleared-agnostic
  declaration at the unit's own operating point; the within-unit rise above
  step 1 is a CLOSED family, miso-151).
* **Normalization** — ``m = base_level / G_ref(month)`` with G_ref = Henry
  Hub monthly + the measured MISO hub basis row (the miso-156 PRIMARY gas
  basis). m is an implied-offer-heat-rate (MMBtu/MWh): it regenerates for a
  forward year from a forward gas trajectory (rule 13 admissibility test).
* **Pooling** — all three JJA years into ONE vector; per-year sub-vectors
  are reported as a stationarity check, never consumed.
* **The vector** — capacity-weighted quantiles of m on the frozen grid
  p = 0.5%, 1.0%, ..., 99.5% (199 points), step-function estimator
  (sort, cumulative weight, ``searchsorted`` — the miso-151 convention).

Rule 23 ``[R-FROZEN-DERIVE]``: re-derives only when the corpus updates, and
such a commit cites the data change. Rule 13 ``[R-MEASURED]``: no LMP and no
residual anywhere in this file's inputs. Rule 22 ``[R-HOLDOUT]``: the corpus
span is 2023-2025 (the fetcher's own year gate enforced it).

Usage::

    uv run --no-project --with pyarrow,pandas,numpy --python 3.12 \\
      python scripts/data/derive_miso_offer_level_dispersion.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_miso_offer_level_dispersion")

ISO = "MISO"
YEARS: tuple[int, ...] = (2023, 2024, 2025)
#: JJA — the corpus's landed span (data/raw/miso-energy-offers/README.md).
MONTHS: tuple[int, ...] = (6, 7, 8)
MARKET = "DA"

#: Frozen quantile grid (PREREG §3): 0.5% .. 99.5% in 0.5% steps, 199 points.
QUANTILE_GRID: np.ndarray = np.round(np.arange(0.005, 0.9951, 0.005), 4)

OUT_PATH = (
    paths.REPO_ROOT
    / "data"
    / "raw"
    / "_validation-source"
    / "miso_offer_level_dispersion.json"
)

_READ_COLS = [
    "unit_code",
    "interval_start_local",
    "step_idx",
    "step_price_usd_per_mwh",
    "ecomax_mw",
    "self_scheduled_mw",
    "economic_flag",
    "must_run_flag",
    "unit_available_flag",
]


def gas_reference() -> dict[tuple[int, int], float]:
    """Return G_ref[(year, month)] — Henry Hub monthly + measured MISO basis.

    The miso-156 PRIMARY gas basis (``measured_gas_monthly``), restricted to
    the corpus months. Hard-errors on a missing month: a silent gap would
    move quantiles without a cited data change (rule 23).
    """
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_monthly.csv")
    bs = pd.read_csv(REPO / "data/raw/gas_basis_by_iso_month.csv")
    bs = bs[bs["iso"] == ISO]
    out: dict[tuple[int, int], float] = {}
    for year in YEARS:
        h = hh[hh["year"] == year].set_index("month")["price_usd_mmbtu"]
        b = bs[bs["year"] == year].set_index("month")["basis_usd_mmbtu"]
        for m in MONTHS:
            if m not in h.index or m not in b.index:
                raise SystemExit(f"G_ref missing for {year}-{m:02d}")
            out[(year, m)] = float(h.loc[m]) + float(b.loc[m])
    return out


def weighted_quantiles(
    values: np.ndarray, weights: np.ndarray, grid: np.ndarray
) -> np.ndarray:
    """Step-function weighted quantiles (the miso-151 G-4/G-5 convention)."""
    order = np.argsort(values, kind="stable")
    v, cum = values[order], np.cumsum(weights[order])
    cum = cum / cum[-1]
    idx = np.clip(np.searchsorted(cum, grid), 0, v.size - 1)
    return v[idx]


def load_year_base_rows(year: int) -> pd.DataFrame:
    """Return one row per DA unit-hour: base level, weights, masks, month."""
    path = paths.clean_path("energy-offers", iso=ISO, year=year, market=MARKET)
    df = pd.read_parquet(path, columns=_READ_COLS, filters=[("step_idx", "==", 1)])
    ts = pd.to_datetime(df["interval_start_local"])
    hour = (
        (ts - pd.Timestamp(year=year, month=1, day=1)) // pd.Timedelta(hours=1)
    ).astype(int)
    df = df.assign(month=ts.dt.month.to_numpy(), year=year, hour=hour.to_numpy())
    df = df[df["month"].isin(MONTHS)]
    w_all = np.clip(df["ecomax_mw"].to_numpy(float), 0.0, None)
    w_elig = np.clip(
        df["ecomax_mw"].to_numpy(float)
        - np.nan_to_num(df["self_scheduled_mw"].to_numpy(float)),
        0.0,
        None,
    )
    elig = (
        df["unit_available_flag"].to_numpy(bool)
        & df["economic_flag"].to_numpy(bool)
        & ~df["must_run_flag"].to_numpy(bool)
    )
    return pd.DataFrame(
        {
            "year": df["year"].to_numpy(),
            "month": df["month"].to_numpy(),
            "hour": df["hour"].to_numpy(),
            "unit_code": df["unit_code"].to_numpy(),
            "base_level": df["step_price_usd_per_mwh"].to_numpy(float),
            "available": df["unit_available_flag"].to_numpy(bool),
            "eligible": elig,
            "w_all": w_all,
            "w_elig": w_elig,
        }
    )


def main() -> dict:
    """Derive the pooled vector + per-year sub-vectors and write the artifact."""
    argparse.ArgumentParser(description=__doc__).parse_args()

    gref = gas_reference()
    frames = [load_year_base_rows(y) for y in YEARS]
    pooled = pd.concat(frames, ignore_index=True)

    g = np.array([gref[(y, m)] for y, m in zip(pooled["year"], pooled["month"])])
    pooled = pooled.assign(m_markup=pooled["base_level"].to_numpy() / g)

    def _vec(df: pd.DataFrame) -> dict:
        sel = df["eligible"].to_numpy() & (df["w_elig"].to_numpy() > 0)
        v = df["m_markup"].to_numpy()[sel]
        w = df["w_elig"].to_numpy()[sel]
        q = weighted_quantiles(v, w, QUANTILE_GRID)
        return {
            "n_unit_hours": int(sel.sum()),
            "n_units": int(df["unit_code"][sel].nunique()),
            "weight_gw_mean_per_hour": round(float(w.sum() / max(1, sel.sum())), 6),
            "quantiles_mmbtu_per_mwh": [round(float(x), 6) for x in q],
        }

    record: dict = {
        "schema": "miso-offer-level-dispersion/v1",
        "session": "miso-179",
        "prereg": "PREREG-miso179-offer-level-dispersion-2026-08-23.md",
        "iso": ISO,
        "market": MARKET,
        "years": list(YEARS),
        "months": list(MONTHS),
        "population": (
            "BOOK-ELIG: unit_available AND economic AND NOT must_run; "
            "weight max(0, ecomax_mw - self_scheduled_mw); base level = "
            "step-1 price; m = base_level / G_ref(month)"
        ),
        "reference": "Henry Hub monthly + measured MISO hub basis (miso-156 PRIMARY)",
        "g_ref_usd_per_mmbtu": {
            f"{y}-{m:02d}": round(gref[(y, m)], 6) for (y, m) in sorted(gref)
        },
        "quantile_grid": [float(p) for p in QUANTILE_GRID],
        "pooled": _vec(pooled),
        "per_year": {str(y): _vec(pooled[pooled["year"] == y]) for y in YEARS},
    }

    # Stationarity report (never consumed): max abs divergence of the per-year
    # vectors from the pooled one, over the interior grid (p in [0.05, 0.95]).
    interior = (QUANTILE_GRID >= 0.05) & (QUANTILE_GRID <= 0.95)
    pooled_q = np.array(record["pooled"]["quantiles_mmbtu_per_mwh"])
    for y in YEARS:
        yq = np.array(record["per_year"][str(y)]["quantiles_mmbtu_per_mwh"])
        record["per_year"][str(y)]["max_abs_div_from_pooled_interior"] = round(
            float(np.max(np.abs(yq[interior] - pooled_q[interior]))), 6
        )

    # Reproducibility inventory: the raw manifest digest + clean row counts.
    man_path = REPO / "data/raw/miso-energy-offers/manifest.json"
    record["raw_manifest_sha256"] = hashlib.sha256(man_path.read_bytes()).hexdigest()
    man = json.loads(man_path.read_text())
    record["raw_manifest_n_files"] = int(man["n_files"])
    record["clean_rows"] = {}
    for y in YEARS:
        p = paths.clean_path("energy-offers", iso=ISO, year=y, market=MARKET)
        import pyarrow.parquet as pq

        record["clean_rows"][f"DA/{y}"] = int(pq.ParquetFile(p).metadata.num_rows)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(record, indent=1))
    digest = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
    log.info("wrote %s (sha256 %s)", OUT_PATH, digest)
    pq_ = record["pooled"]["quantiles_mmbtu_per_mwh"]
    grid = list(QUANTILE_GRID)

    def at(p: float) -> float:
        return pq_[int(np.argmin(np.abs(np.array(grid) - p)))]

    log.info(
        "pooled m quantiles (MMBtu/MWh): p10 %.3f p50 %.3f p90 %.3f p95 %.3f p99 %.3f  (n=%d unit-hours, %d units)",
        at(0.10),
        at(0.50),
        at(0.90),
        at(0.95),
        at(0.995 if 0.99 not in grid else 0.99),
        record["pooled"]["n_unit_hours"],
        record["pooled"]["n_units"],
    )
    return record


if __name__ == "__main__":
    main()
