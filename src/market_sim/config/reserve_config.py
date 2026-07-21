"""Facade: ``config/reserve_config.py`` moved to :mod:`market_sim.model.reserves.spec`.

The unified reserve co-optimization configuration — per-ISO ``ReserveDesign``
builders, reserve-product constants, and the dispatch-kwargs bridge — is
model-layer physics, and importing it from ``config/`` inverted the
config→data→model layering (its module-level ``data.fleet`` import also
dragged the 10k-line loader into the config layer). Session 3E of the
refactor-consolidation lane (plan §4 item 4 / §5 item 5, 2026-07-21) moved
the 2,932-line module INTACT to ``model/reserves/spec.py`` — rule 25: the
per-ISO ``_<iso>_design`` registries transplant byte-for-byte, no value
changes.

This module keeps every historical import path working by aliasing itself to
the moved module: after ``import market_sim.config.reserve_config``, BOTH
paths name the ONE module namespace, so ``from
market_sim.config.reserve_config import <name>`` resolves the entire
pre-move surface (public names and test/script-imported privates alike), and
any monkeypatch / attribute write through this path lands on the same
namespace the internals read — the pre-move patch semantics, unchanged.

The re-export surface is pinned by ``tests/test_config_model_layering.py``.
"""

import sys

from market_sim.model.reserves import spec as _spec

# Alias, don't copy: a from-import snapshot would fork the namespace and
# silently break monkeypatch / attribute writes through this module path
# (same pattern as model/capacity.py → model/capacity_evolution).
sys.modules[__name__] = _spec
