"""ISO-NE capacity-market-elcc spec.

ISO-NE's seasonal-claimed-capability-derived and (where adopted) ELCC-based
accreditation for intermittent/limited-duration resources. Uses the ``NEISO``
ISO label (matching ``config/iso_configs.py``).
"""

from __future__ import annotations

from . import IsoSpec, register

_RESOURCE_CLASS_ALIASES = {
    "battery_4hr": "storage_4hr",
    "onshore_wind": "wind",
    "offshore_wind": "wind_offshore",
}

SPEC = register(
    IsoSpec(
        iso="NEISO",
        resource_class_aliases=_RESOURCE_CLASS_ALIASES,
    )
)
