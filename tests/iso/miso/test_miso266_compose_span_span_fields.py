"""The MISO span composer writes SPAN-level provenance, not its first leg's.

``scripts/probes/_miso266_compose_span.py`` composes rule-36 single-year legs
into one registrable bundle. It copied the first leg's ``run_config.json`` and
``meta.json`` verbatim, so a six-year composite recorded
``calibration_flags.years == [2020]`` (``audit_keepers`` E3) and 2020's ONE-year
``eia930 / eia923 / campd`` frames in ``shared_inputs`` (``RESULT-miso266`` §5.1
Defect A: ``--restore-shared-inputs`` then rebuilt a six-year frame and refused
against a one-year hash). miso-267 widens the one and re-spans the other. The
frame rebuild is replaced by a recorder here — this pins what the composer asks
for and records, not the builder.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest
from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "miso266_compose",
    str(REPO_ROOT / "scripts" / "probes" / "_miso266_compose_span.py"),
)
comp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(comp)


def _leg(cal: Path, name: str, year: int) -> None:
    """One single-year leg with the keeper's data-forced reserve partition."""
    train = year >= 2023
    sc = {k: "same" for k in comp.MUST_AGREE}
    sc["miso_measured_reserve_requirements"] = train
    sc["miso_reserve_online_gated"] = train
    d = cal / name
    (d / "hourly").mkdir(parents=True)
    pd.DataFrame({"year": [year], "hour": [0]}).to_parquet(
        d / "hourly" / f"system_{year}.parquet", index=False
    )
    pd.DataFrame({"year": [year], "mw": [1.0]}).to_parquet(
        d / "system.parquet", index=False
    )
    cfg = {
        "scenario_config": sc,
        "solve_surface": {"fingerprint": "f"},
        "calibration_flags": {"years": [year], "gas_prices": {str(year): 3.0}},
    }
    (d / "run_config.json").write_text(json.dumps(cfg))
    meta = {
        "iso": "MISO",
        "years": [year],
        "shared_inputs": {
            "eia923": f"../_shared/MISO/eia923-{year}.parquet",
            "unit_outages": "../_shared/MISO/unit_outages-shared.parquet",
        },
    }
    (d / "meta.json").write_text(json.dumps(meta))


@pytest.fixture
def composed(tmp_path, monkeypatch):
    cal = tmp_path / "calibration"
    legs = {f"leg{y}": [y] for y in (2020, 2021, 2023)}
    for name, (y,) in legs.items():
        _leg(cal, name, y)
    monkeypatch.setattr(comp, "CAL", cal)
    asked: list[Path] = []

    import scripts.run_calibration_full as rcf

    def fake_build(bundle):
        asked.append(Path(bundle))
        return "MISO", {"eia923": pd.DataFrame({"year": [2020, 2021, 2023]})}

    monkeypatch.setattr(rcf, "build_benchmark_frames", fake_build)
    out = cal / "span"
    comp.compose(legs, out)
    return out, asked


def test_run_config_years_are_the_span(composed):
    out, _ = composed
    flags = json.loads((out / "run_config.json").read_text())["calibration_flags"]
    assert flags["years"] == [2020, 2021, 2023]
    assert flags["gas_prices"] == {"2020": 3.0, "2021": 3.0, "2023": 3.0}


def test_per_year_frames_are_rebuilt_over_the_composite(composed):
    out, asked = composed
    assert asked == [out], "the span frames must be built over the COMPOSITE's meta"
    shared = json.loads((out / "meta.json").read_text())["shared_inputs"]
    assert "eia923-2020" not in shared["eia923"], "leg 1's one-year frame survived"
    assert shared["unit_outages"].endswith("unit_outages-shared.parquet")
