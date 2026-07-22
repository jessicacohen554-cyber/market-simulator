"""Facade: ``model/dispatch.py`` became the :mod:`market_sim.model.lp` package.

The 4,974-line dispatch LP module was split into ``model/lp/`` (layout /
costs / rows / reserve_rows / bounds / model, with the pickle-borne
``DispatchResult`` / ``CrossYearBasis`` and ``solve_dispatch`` defined
physically in the package ``__init__``) on 2026-07-22
(refactor-consolidation plan §5 item 7). This module keeps every historical
import path working by aliasing itself to the package: after
``import market_sim.model.dispatch``, BOTH module paths name the one package
namespace, so

- ``from market_sim.model.dispatch import <name>`` resolves the entire
  pre-split surface (public functions and script/test-imported privates
  alike),
- ``dispatch.<attr>`` reads and monkeypatch writes land on the shared
  namespace, and
- ``mock.patch("market_sim.model.dispatch.<name>")`` keeps intercepting the
  names production code resolves through this namespace at call time (the
  pipeline orchestrators' function-local ``solve_dispatch`` imports) — the
  pre-split patch semantics, unchanged.

The re-export surface is pinned by ``tests/test_dispatch_facade.py``; the
pickle-identity contract (``__module__ == "market_sim.model.dispatch"`` for
the three physically-defined names) by ``tests/test_persisted_identity.py``.
"""

import sys

from market_sim.model import lp as _lp

# Alias, don't copy: a from-import snapshot would fork the namespace and
# silently break every historical monkeypatch / attribute write through this
# module path (same pattern as model/transmission.py -> model/interchange).
sys.modules[__name__] = _lp
