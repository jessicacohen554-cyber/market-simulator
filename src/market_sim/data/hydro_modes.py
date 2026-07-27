"""Reader for the ``hydro-plant-modes`` clean datatype (RoR-split classifier).

The consumption seam for the per-plant conventional-hydro operational-mode
classification curated by ``scripts/data/curate_hydro_plant_modes.py`` (ORNL
EHA FY2024 ``Mode`` + the documented HILARRI/Corps-dam completion — see that
script's docstring for the rules and their labeled-subset validation). The
dispatch mechanism (``ScenarioConfig.hydro_ror_split``) consumes only the
binary ``shapeable`` column; the provenance columns stay in the clean table.

The classification is a static plant attribute (not per-year): a plant's
hydraulic mode does not change with the water year, so the same table serves
every backcast and forecast year — the forward story is the classification
itself (rule 13: an external measured input that regenerates for a future
year by re-running the curation against updated EHA/HILARRI vintages).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def load_hydro_shapeable(iso: str) -> dict[int, bool] | None:
    """Return ``{plant_id: shapeable}`` for the ISO's classified hydro plants.

    Reads the curated ``hydro-plant-modes`` clean partition through the
    frozen ``clean_io`` seam. Returns ``None`` when the partition does not
    exist for ``iso`` (the classifier has only been reviewed/registered for
    some ISOs — CAISO first), so the caller can hard-distinguish "no
    classifier" from "empty classifier".
    """
    from scripts.lib.clean_io import read_clean

    try:
        df = read_clean(
            "hydro-plant-modes", iso=iso.upper(), columns=["plant_id", "shapeable"]
        )
    except FileNotFoundError:
        logger.warning(
            "no hydro-plant-modes clean partition for %s — run "
            "scripts/data/curate_hydro_plant_modes.py (and review the "
            "completion rule for this ISO first)",
            iso,
        )
        return None
    return {int(pid): bool(sh) for pid, sh in zip(df["plant_id"], df["shapeable"])}
