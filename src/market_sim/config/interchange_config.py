"""Facade: ``config/interchange_config.py`` moved to :mod:`market_sim.model.interchange.spec`.

The unified ``InterchangeSpec`` system — per-ISO corridors, reference-price
neighbors, firm imports, seam ladders, and the interchange fleet/topology
builders — is model-layer physics, and importing it from ``config/``
inverted the config→data→model layering (its module-level ``data.fleet``
import also dragged the 10k-line loader into the config layer). Session 3E
of the refactor-consolidation lane (plan §4 item 4 / §5 item 5, 2026-07-21)
moved the 1,919-line module INTACT to ``model/interchange/spec.py`` (which
session 3F extends with the relocated ``model/transmission.py``); the only
content change is the deletion of the two duplicated constants
(``CARB_UNSPECIFIED_IMPORT_EF``, ``_GAS_BASIS_NYISO``) in favour of the
canonical ``config.constants`` definitions — rule 25: deleted means deleted,
and the per-ISO seam/tranche registries transplant byte-for-byte.

This module keeps every historical import path working by aliasing itself to
the moved module: after ``import market_sim.config.interchange_config``,
BOTH paths name the ONE module namespace, so ``from
market_sim.config.interchange_config import <name>`` resolves the entire
pre-move surface (public names and test/script-imported privates alike), and
any monkeypatch / attribute write through this path lands on the same
namespace the internals read — the pre-move patch semantics, unchanged.

The re-export surface is pinned by ``tests/test_config_model_layering.py``.
"""

import sys

from market_sim.model.interchange import spec as _spec

# Alias, don't copy: a from-import snapshot would fork the namespace and
# silently break monkeypatch / attribute writes through this module path
# (same pattern as model/capacity.py → model/capacity_evolution).
sys.modules[__name__] = _spec
