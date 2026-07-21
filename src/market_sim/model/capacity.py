"""Facade: ``model/capacity.py`` became the :mod:`market_sim.model.capacity_evolution` package.

The 4,269-line capacity-evolution module was split into
``model/capacity_evolution/`` (retirements / new_entry / adequacy / ccs /
evolve) on 2026-07-21 (W-D4; refactor-consolidation plan §5 item 4). This
module keeps every historical import path working by aliasing itself to the
package: after ``import market_sim.model.capacity``, BOTH module paths name
the one package namespace, so

- ``from market_sim.model.capacity import <name>`` resolves the entire
  pre-split surface (public functions and script/test-imported privates
  alike),
- ``capacity.<attr>`` reads and monkeypatch writes land on the shared
  namespace, and
- ``mock.patch("market_sim.model.capacity.<name>")`` /
  ``mock.patch.dict("market_sim.model.capacity.MARKET_DESIGN", ...)`` and
  probe-style ``capacity.<name> = wrapped`` keep intercepting the names the
  package internals deliberately resolve through this namespace at call time
  (the six ``evolve_fleet`` step functions and
  ``estimate_expected_revenue``) — the pre-split patch semantics, unchanged.

The re-export surface is pinned by ``tests/test_capacity_evolution_facade.py``.
"""

import sys

from market_sim.model import capacity_evolution as _capacity_evolution

# Alias, don't copy: a from-import snapshot would fork the namespace and
# silently break every historical monkeypatch / attribute write through this
# module path.
sys.modules[__name__] = _capacity_evolution
