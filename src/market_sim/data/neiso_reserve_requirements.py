"""Measured ISO-NE hourly reserve-requirement series (NEISO Limb A).

The condition-varying requirement channel for the NEISO in-LP energy+reserve
co-optimization (``config.reserve_config._neiso_design``): each reserve
family's static published requirement is replaced, when
``ScenarioConfig.neiso_dynamic_reserve_requirements`` is on, by the MEASURED
as-enforced hourly requirement ISO-NE actually enforced in real time for that
(location, product) — the ISO Express "Hourly Reserve Requirements" report,
the exact ISO-NE analogue of the NYISO issue-#1344 Ask-B intake
(``data.nyiso_reserve_requirements``). The measured series is a market-design
*input* (CLAUDE.md rule #13 admissible: it regenerates for a forward year as
the published static base plus ISO-NE's published condition rules — largest
first/second contingency, cold-weather and gas-contingency events — applied
to forward states, and it responds to changed conditions). The measured
reserve *prices* are the validation target and are NEVER read here.

Data contract (the ``reserve-requirements`` clean datatype):

* raw: ``data/raw/NEISO-AS/requirements/requirements_<start>_<end>.csv``
  (gitignored window CSVs; ``scripts/fetch_neiso_reserve_requirements.py``
  regenerates them from the public report)
* clean: ``data/clean/reserve-requirements/NEISO/<year>/`` via
  ``scripts/curate_reserve_requirements.py`` (schema
  ``data/dictionary/schema/reserve-requirements.schema.yaml``)

The loader raises when the clean partition is absent — the flag must never
quietly solve on the static requirements it claims to replace (no silent
fallback; CLAUDE.md rule #23's no-off-registry-channels spirit). A family
absent from the measured mapping keeps its static published value in the
design (partial coverage is expected: the local reserve zones SWCT/CT/
NEMABSTN publish a 30-minute total with no in-LP family today).
"""

from __future__ import annotations

import numpy as np

#: (location, product) -> in-LP reserve family name
#: (reserve_config._neiso_design / NEISO_RCPF_PRODUCTS). ROS is the
#: system-wide requirement row; the local reserve zones (SWCT, CT, NEMABSTN)
#: are deliberately absent — the NEISO design carries no locational reserve
#: families (the model's 4-zone topology has no SWCT boundary).
FAMILY_BY_LOCATION_PRODUCT: dict[tuple[str, str], str] = {
    ("ROS", "30min_total"): "ne_30min_total",
    ("ROS", "10min_total"): "ne_10min_total",
    ("ROS", "10min_spin"): "ne_10min_spin",
}


def _import_clean_io():
    """Import the shared ``scripts.lib.clean_io`` reader seam, lazily.

    ``clean_io`` lives under ``scripts/`` (not an installed package), so the
    repo root is put on ``sys.path`` the way the curation scripts do. Done
    lazily so only the opt-in dynamic-requirements path pays the cost.
    """
    import sys

    from market_sim.config import paths

    root = str(paths.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.lib import clean_io  # noqa: E402

    return clean_io


def load_neiso_reserve_requirements(year: int, hours: int) -> dict[str, np.ndarray]:
    """Load the measured hourly reserve-requirement series for ``year``.

    Args:
        year: Backcast year (the fleet-clock year the solve runs on).
        hours: LP horizon length T; each returned series is trimmed/validated
            to exactly this many values on the model's hour clock (row 0 =
            the year's first local hour, UTC-ordered, local Feb 29 dropped in
            a leap year — the ``eia_loader`` convention).

    Returns:
        ``{family_name: (hours,) float array of requirement MW}`` for every
        (location, product) in :data:`FAMILY_BY_LOCATION_PRODUCT`.

    Raises:
        FileNotFoundError: The clean partition is absent — the
            ``neiso_dynamic_reserve_requirements`` flag hard-errors rather
            than silently reverting to the static requirements. Regenerate
            with ``scripts/fetch_neiso_reserve_requirements.py`` then
            ``scripts/curate_reserve_requirements.py``.
        ValueError: A mapped series is missing from the clean data, does not
            cover the full horizon, or contains non-finite/negative values.
    """
    clean_io = _import_clean_io()
    if not clean_io.clean_exists("reserve-requirements", iso="NEISO", year=int(year)):
        raise FileNotFoundError(
            f"neiso_dynamic_reserve_requirements=True but the measured "
            f"requirement series is absent: no clean partition "
            f"reserve-requirements/NEISO/{year}. Regenerate raw with "
            f"scripts/fetch_neiso_reserve_requirements.py, then curate with "
            f"scripts/curate_reserve_requirements.py — the flag must not "
            f"solve on the static requirements it claims to replace."
        )
    df = clean_io.read_clean("reserve-requirements", iso="NEISO", year=int(year))

    # Model hour clock: UTC-sorted local year with a leap year's local
    # Feb 29 dropped (see data.eia_loader._eia_hourly_frame).
    local = df["interval_start_local"]
    df = df[~((local.dt.month == 2) & (local.dt.day == 29))]

    out: dict[str, np.ndarray] = {}
    for (location, product), family in FAMILY_BY_LOCATION_PRODUCT.items():
        sub = df[(df["location"] == location) & (df["product"] == product)]
        sub = sub.sort_values("interval_start_utc")
        series = sub["requirement_mw"].to_numpy(dtype=float)
        if series.shape[0] < int(hours):
            raise ValueError(
                f"reserve-requirements NEISO {year}: series {location}/"
                f"{product} covers {series.shape[0]} hours < horizon {hours} "
                f"— a mapped series must cover the full year (no silent "
                f"gap-filling)."
            )
        series = series[: int(hours)]
        if not np.all(np.isfinite(series)) or np.any(series < 0):
            raise ValueError(
                f"reserve-requirements NEISO {year}: series {location}/"
                f"{product} contains non-finite or negative values."
            )
        out[family] = series
    return out
