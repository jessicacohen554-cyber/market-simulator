"""Every committed ``configs/**/*.yaml`` loads through its intended loader.

A cheap, no-solve guard that the shipped scenario / sweep / uncertainty YAML
files stay loadable as the code that consumes them evolves. Each file is routed
to exactly one loader by its location/name:

* ``configs/scenarios/*.yaml``              -> ``ScenarioConfig.from_yaml``
* ``configs/*matrix*.yaml``                 -> ``SweepDefinition.from_yaml``
* ``configs/uncertainty_*.yaml``            -> ``UncertaintySpec.from_yaml``
* ``configs/data-profiles.yaml``            -> ``scripts.hydrate_data.load_manifest``

A new config file that matches none of these patterns fails the test on
purpose — add it (and its loader) to the routing below.
"""

from __future__ import annotations

import glob

import pytest

from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.uncertainty import UncertaintySpec
from tests.helpers import REPO_ROOT

_CONFIG_FILES = sorted(
    glob.glob(str(REPO_ROOT / "configs" / "**" / "*.yaml"), recursive=True)
)


def _load_data_profiles(path: str):
    """Load the hydration manifest through its consumer, ``scripts.hydrate_data``.

    ``load_manifest`` reads the fixed repo path, so first assert the
    parametrized file IS that path, then check the keys profile resolution
    relies on (``isos`` token table, ``profiles`` with the default ``code``).
    """
    from pathlib import Path

    from scripts import hydrate_data

    assert Path(path).resolve() == hydrate_data.MANIFEST.resolve()
    manifest = hydrate_data.load_manifest()
    assert manifest["version"] == 1
    assert manifest["isos"] and all(t for t in manifest["isos"].values())
    assert "code" in manifest["profiles"]
    return manifest


def _loader_for(path: str):
    name = path.replace("\\", "/")
    if "/configs/scenarios/" in name:
        return ScenarioConfig.from_yaml
    if "matrix" in name.rsplit("/", 1)[-1]:
        return SweepDefinition.from_yaml
    if name.rsplit("/", 1)[-1].startswith("uncertainty_"):
        return UncertaintySpec.from_yaml
    if name.rsplit("/", 1)[-1] == "data-profiles.yaml":
        return _load_data_profiles
    return None


def test_config_files_discovered():
    # Guard the guard: if the glob silently finds nothing the parametrization
    # below is vacuous, so assert we actually have configs to check.
    assert _CONFIG_FILES, "no configs/**/*.yaml found — glob or layout changed"


@pytest.mark.parametrize("path", _CONFIG_FILES, ids=lambda p: p.rsplit("/", 1)[-1])
def test_config_yaml_loads_through_its_loader(path):
    loader = _loader_for(path)
    assert loader is not None, (
        f"{path} matches no known config kind — add it to _loader_for's routing"
    )
    obj = loader(path)
    assert obj is not None
