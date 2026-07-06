"""Every committed bundled data file ships a REAL-solve provenance sidecar.

HP-05 final-QA guard. The tool commits two families of bundled market-sim
outputs — the ADR 0011 BAU LMP CSVs (``data/bundled/lmp/*.csv``) and the ADR
0013 hourly fossil-only average CO2-rate parquets
(``data/emissions/*.parquet``). Each MUST carry a matching
``<file>.provenance.json`` sidecar recording which calibrated backcast keeper
solve produced it (source keeper id, bundle, solve date), so the committed
number is always traceable to a real run and flagged validation-only. The
LMP sidecars existed from the start; the emissions sidecars were missing until
HP-05 (Fix A) -- this test locks in the pairing for both so neither family can
regain a committed data file with no provenance again.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_PORTFOLIO_ROOT = Path(__file__).resolve().parents[1]

# Keys every REAL-solve sidecar must carry (the shared schema of the LMP and
# emissions sidecars; the summary-stat keys differ per family and are checked
# separately below).
_REQUIRED_KEYS = (
    "contract",
    "iso",
    "source_keeper_id",
    "source_bundle",
    "solve_date",
    "mode",
    "simulation_year",
    "hours",
    "backcast_validation_only",
    "generator",
)


def _bundled_data_files() -> list[Path]:
    """Every committed bundled data file that must have a provenance sidecar."""
    lmp = sorted((_PORTFOLIO_ROOT / "data" / "bundled" / "lmp").glob("*.csv"))
    emissions = sorted((_PORTFOLIO_ROOT / "data" / "emissions").glob("*.parquet"))
    return lmp + emissions


def test_bundled_data_files_are_discoverable() -> None:
    """Sanity check: the six-ISO LMP + CO2-rate bundles are actually present,
    so an empty glob can't make the pairing test pass vacuously."""
    files = _bundled_data_files()
    assert len(files) >= 12, f"expected >=12 bundled data files, found {len(files)}"


@pytest.mark.parametrize("data_file", _bundled_data_files(), ids=lambda p: p.name)
def test_bundled_file_has_provenance_sidecar(data_file: Path) -> None:
    """Each bundled data file has a ``<file>.provenance.json`` sidecar carrying
    the required REAL-solve keys and a per-family summary stat."""
    sidecar = data_file.with_suffix(data_file.suffix + ".provenance.json")
    assert sidecar.exists(), f"missing provenance sidecar for {data_file.name}"

    prov = json.loads(sidecar.read_text(encoding="utf-8"))
    missing = [k for k in _REQUIRED_KEYS if k not in prov]
    assert not missing, f"{sidecar.name} missing required keys: {missing}"

    assert prov["backcast_validation_only"] is True, sidecar.name
    assert prov["iso"] in data_file.name, (
        f"{sidecar.name} iso {prov['iso']!r} does not match file name"
    )

    # Per-family summary statistics: LMP sidecars carry lmp_*, emissions
    # sidecars carry co2_rate_*.
    stat_prefix = "lmp" if data_file.suffix == ".csv" else "co2_rate"
    for stat in (f"{stat_prefix}_mean", f"{stat_prefix}_min", f"{stat_prefix}_max"):
        assert stat in prov, f"{sidecar.name} missing summary stat {stat!r}"
