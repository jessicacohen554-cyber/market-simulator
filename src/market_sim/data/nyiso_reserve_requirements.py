"""Measured NYISO hourly locational reserve-requirement series (issue #1344).

The condition-varying requirement channel for the NYISO in-LP energy+reserve
co-optimization (``config.reserve_config._nyiso_design``): each reserve
family's static published requirement is replaced, when
``ScenarioConfig.nyiso_dynamic_reserve_requirements`` is on, by the MEASURED
as-enforced hourly requirement NYISO actually scheduled into RTD/RTC for that
(region, product). The measured series is a market-design *input* (CLAUDE.md
rule #13 admissible: it regenerates for a forward year as the published static
base plus the published condition rules — thunderstorm alerts, gas
contingencies, largest-source changes — applied to forward states, and it
responds to changed conditions). The measured reserve *prices*
(``data/raw/NYISO-AS/NYISO_as_{rt,da}_{year}.csv``) are the validation target
and are NEVER read here.

Data contract (the Ask-B intake, ``docs/handoffs/nyiso-data-asks-2026-07.md``):

* ``data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_{year}.csv``
* columns: ``Time Stamp`` (Eastern wall-clock, hour-beginning — the same
  convention as the processed AS price CSVs), ``region`` (``NYCA`` / ``East``
  / ``SENY`` / ``NYC``), ``product`` (``30min_total`` / ``10min_total`` /
  ``10min_spin``), ``requirement_mw``.
* sub-hourly rows are aggregated to the hour-beginning mean; each present
  (region, product) series must cover the full year (no silent gap-filling
  beyond the hour-mean aggregation).

The loader raises when the file is absent — the flag must never quietly solve
on the static requirements it claims to replace (no silent fallback,
CLAUDE.md rule #23's no-off-registry-channels spirit). A (region, product)
absent from the file keeps its static published value in the design (partial
coverage is expected: e.g. only the downstate regions may be measured).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

#: Drop zone for the Ask-B intake (docs/handoffs/nyiso-data-asks-2026-07.md).
NYISO_RESERVE_REQUIREMENTS_DIR: Path = RAW_DATA_DIR / "NYISO-AS" / "requirements"

#: (region, product) -> in-LP reserve family name (reserve_config._nyiso_design).
#: Keys mirror the published NYISO reserve regions/products the design builds
#: from NYISO_RCPF_PRODUCTS (NYCA tier) and NYISO_RCPF_LOCATIONAL (East ⊃ SENY
#: ⊃ NYC); the synchronised-reserve scaffold families (nyc_spin_*) are
#: deliberately absent — they have no published measured requirement series.
FAMILY_BY_REGION_PRODUCT: dict[tuple[str, str], str] = {
    ("NYCA", "30min_total"): "nyca_30min_total",
    ("NYCA", "10min_total"): "nyca_10min_total",
    ("NYCA", "10min_spin"): "nyca_10min_spin",
    ("East", "30min_total"): "east_30min_total",
    ("SENY", "30min_total"): "seny_30min_total",
    ("NYC", "30min_total"): "nyc_30min_total",
    ("NYC", "10min_total"): "nyc_10min_total",
}


def requirements_path(year: int) -> Path:
    """Return the on-disk path of the measured requirement CSV for ``year``."""
    return NYISO_RESERVE_REQUIREMENTS_DIR / f"NYISO_reserve_requirements_{year}.csv"


def load_nyiso_reserve_requirements(
    year: int,
    hours: int,
    path: Path | None = None,
) -> dict[str, np.ndarray]:
    """Load the measured hourly reserve-requirement series for ``year``.

    Args:
        year: Backcast year (the fleet-clock year the solve runs on).
        hours: LP horizon length T; each returned series is trimmed/validated
            to exactly this many hour-beginning values.
        path: Optional explicit CSV path (tests); defaults to
            :func:`requirements_path`.

    Returns:
        ``{family_name: (hours,) float array of requirement MW}`` for every
        (region, product) present in the file, keyed per
        :data:`FAMILY_BY_REGION_PRODUCT`.

    Raises:
        FileNotFoundError: The intake file is absent — the
            ``nyiso_dynamic_reserve_requirements`` flag hard-errors rather
            than silently reverting to the static requirements (see the Ask-B
            data ask, ``docs/handoffs/nyiso-data-asks-2026-07.md``).
        ValueError: Unknown (region, product) rows, or a present series that
            does not cover the full horizon.
    """
    src = path if path is not None else requirements_path(year)
    if not src.exists():
        raise FileNotFoundError(
            f"nyiso_dynamic_reserve_requirements=True but the measured "
            f"requirement series is absent: {src}. This is the Ask-B external "
            f"data intake (docs/handoffs/nyiso-data-asks-2026-07.md); the flag "
            f"must not solve on the static requirements it claims to replace."
        )

    df = pd.read_csv(src)
    required_cols = {"Time Stamp", "region", "product", "requirement_mw"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"{src}: missing column(s) {sorted(missing)}; expected "
            f"{sorted(required_cols)}"
        )

    unknown = set(map(tuple, df[["region", "product"]].drop_duplicates().values))
    unknown -= set(FAMILY_BY_REGION_PRODUCT)
    if unknown:
        raise ValueError(
            f"{src}: unknown (region, product) pairs {sorted(unknown)}; known "
            f"pairs are {sorted(FAMILY_BY_REGION_PRODUCT)}"
        )

    df = df.copy()
    ts = pd.to_datetime(df["Time Stamp"])
    # Hour-beginning aggregation: sub-hourly postings mean to their hour, the
    # same convention scripts/process_nyiso_as.py uses for the price CSVs.
    df["_hour"] = ts.dt.floor("h")

    out: dict[str, np.ndarray] = {}
    for (region, product), grp in df.groupby(["region", "product"], sort=False):
        family = FAMILY_BY_REGION_PRODUCT[(str(region), str(product))]
        hourly = grp.groupby("_hour", sort=True)["requirement_mw"].mean().to_numpy()
        if hourly.shape[0] < hours:
            raise ValueError(
                f"{src}: series {region}/{product} covers {hourly.shape[0]} "
                f"hours < horizon {hours} — a present series must cover the "
                f"full year (no silent gap-filling)."
            )
        series = np.asarray(hourly[:hours], dtype=float)
        if not np.all(np.isfinite(series)) or np.any(series < 0):
            raise ValueError(
                f"{src}: series {region}/{product} contains non-finite or "
                f"negative requirement values."
            )
        out[family] = series
    return out
