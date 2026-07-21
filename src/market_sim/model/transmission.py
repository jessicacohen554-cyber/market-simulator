"""Facade: ``model/transmission.py`` became the :mod:`market_sim.model.interchange` package.

The 5,436-line transmission/interchange module was split into
``model/interchange/`` (core / import_nodes / caiso / miso / pjm / nyiso /
neiso / registry, alongside the session-3E spec module) on 2026-07-21
(session 3F; refactor-consolidation plan §5 item 6). This module keeps every
historical import path working by aliasing itself to the package: after
``import market_sim.model.transmission``, BOTH module paths name the one
package namespace, so

- ``from market_sim.model.transmission import <name>`` resolves the entire
  pre-split surface (public functions and script/test-imported privates
  alike),
- ``transmission.<attr>`` reads and monkeypatch writes land on the shared
  namespace, and
- ``mock.patch("market_sim.model.transmission.<name>")`` keeps intercepting
  the names production code deliberately resolves through this namespace at
  call time (``data/fleet.py``'s ``inject_neiso_gas_coldsnap_derate``,
  ``data/winter_fuel_inventory.py``'s floor kernels, the backcast
  orchestrator's function-local injector imports) — the pre-split patch
  semantics, unchanged.

The re-export surface is pinned by ``tests/test_transmission_facade.py``.
"""

import sys

from market_sim.model import interchange as _interchange

# Alias, don't copy: a from-import snapshot would fork the namespace and
# silently break every historical monkeypatch / attribute write through this
# module path (same pattern as model/capacity.py → model/capacity_evolution).
sys.modules[__name__] = _interchange
