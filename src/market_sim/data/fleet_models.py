"""Leaf re-export of the fleet data-model types (``Generator`` / ``FleetArrays``).

Session 3E of the refactor-consolidation lane (plan §5 item 5): config- and
model-layer code needs to *name* the two fleet data-model types without
importing :mod:`market_sim.data.fleet`, the 10k-line loader module — that
module-level import was half of the inverted config→data layering edge the
3E fix removes. This leaf is the types-only import target.

RE-EXPORT SHIM ONLY (until session 3H): ``Generator`` and ``FleetArrays``
STAY DEFINED in :mod:`market_sim.data.fleet`. The committed ``p2_state``
pickles resolve both classes by ``__module__ == "market_sim.data.fleet"``
(pinned by ``tests/test_persisted_identity.py``), so the class bodies must
not move before session 3H converts ``data/fleet.py`` into a package that
defines them physically in its ``__init__`` (``data/fleet/models.py``
absorbs this leaf then). Until 3H this shim still imports the loader at
import time; its value is the *stable import target*, so 3H can hollow it
out without touching any consumer.
"""

from market_sim.data.fleet import FleetArrays, Generator

__all__ = ["FleetArrays", "Generator"]
