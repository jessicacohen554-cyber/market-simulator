"""Reader for the ``vlr-pocket-groups`` clean datatype.

The units an ISO's voltage-and-local-reliability operating guides name, per
load pocket and outage-study group (``scripts/data/curate_vlr_pocket_groups.py``;
schema ``data/dictionary/schema/vlr-pocket-groups.schema.yaml``). Read only when
``ScenarioConfig.vlr_pocket_commitment`` is armed; there is no raw fallback, so
an absent partition raises instead of silently dropping the requirement.
"""

from __future__ import annotations

import pandas as pd

#: The clean datatype name (schema stem).
VLR_POCKET_GROUPS_DATATYPE = "vlr-pocket-groups"


def load_vlr_pocket_groups(iso: str) -> pd.DataFrame:
    """The ISO's ``vlr-pocket-groups`` partition; raises when absent."""
    from scripts.lib.clean_io import read_clean

    try:
        return read_clean(VLR_POCKET_GROUPS_DATATYPE, iso=str(iso).upper())
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "vlr_pocket_commitment is on but no clean vlr-pocket-groups "
            f"partition covers {iso} — run scripts/regenerate_clean.py "
            f"--solve-profile {iso} (the requirement never silently no-ops)"
        ) from exc
