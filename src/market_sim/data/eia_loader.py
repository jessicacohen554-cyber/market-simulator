"""Facade: ``data/eia_loader.py`` became the :mod:`market_sim.data.eia930` package.

The 3,239-line EIA-930 loader module was split into ``data/eia930/``
(frames / demand / zonal_shares / envelopes / weather / actuals) on
2026-07-20 (W-D2; refactor-consolidation plan §5 item 2). This module keeps
every historical import path working by aliasing itself to the package:
after ``import market_sim.data.eia_loader``, BOTH module paths name the one
package namespace, so

- ``from market_sim.data.eia_loader import <name>`` resolves the entire
  pre-split surface (public loaders and script/test-imported privates alike),
- ``eia_loader.<attr>`` reads and monkeypatch writes land on the shared
  namespace, and
- ``mock.patch("market_sim.data.eia_loader.<name>")`` keeps intercepting the
  names the package internals deliberately resolve through this namespace at
  call time (``load_zonal_shares``, the per-ISO demand loaders,
  ``CALIBRATION_DIR``, ``EIA_HOURLY_DIR``) — the pre-split patch semantics,
  unchanged.

The re-export surface is pinned by ``tests/test_eia930_facade.py``.
"""

import sys

from market_sim.data import eia930 as _eia930

# Alias, don't copy: a from-import snapshot would fork the namespace and
# silently break every historical monkeypatch / attribute write through this
# module path.
sys.modules[__name__] = _eia930
