"""CLI end-to-end test on the real-CF-profile path (vs. the synthetic default).

test_cli.py's end-to-end test always runs iso="SAMPLE", which never touches
the real-profile branch of build_cf_matrix (profiles.py). The CLI itself
never exposes a ``profiles_dir`` flag or config field — it always calls
``build_cf_matrix(resources, config.iso, config.year)`` with the module
default — so this test reaches the real-data path by monkeypatching
``lce_portfolio.profiles.DEFAULT_PROFILES_DIR`` onto the committed ERCOT
fixture directory (the same fixture test_profiles_real.py uses), keeping the
run data-free while exercising the full CLI pipeline against real CF shapes.

Uses only wind+solar (no storage): a full-8760 solve with a storage tech
against the *real* (noisy, non-smooth) CF profile takes 15-20s+ under IPM
(vs. ~3s for the same system on synthetic shapes — see the PP-07 final
report), which would blow the suite's speed budget for one CLI smoke test.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from lce_portfolio.cli import main
from lce_portfolio.config import HOURS_PER_YEAR

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "profiles"


def _ercot_fixtures(tmp_path):
    hours = np.arange(HOURS_PER_YEAR)
    hod = hours % 24
    load = 500.0 + 150.0 * np.clip(np.sin((hod - 8) / 24.0 * 2 * np.pi), 0, None)
    lmp = 25.0 + 15.0 * np.clip(np.sin((hod - 9) / 24.0 * 2 * np.pi), 0, None)

    load_path = tmp_path / "load.csv"
    lmp_path = tmp_path / "lmp.csv"
    pd.DataFrame({"hour": hours, "iso": "ERCOT", "load_mwh": load}).to_csv(
        load_path, index=False
    )
    pd.DataFrame({"hour": hours, "iso": "ERCOT", "lmp": lmp}).to_csv(
        lmp_path, index=False
    )
    return load_path, lmp_path


def test_cli_end_to_end_real_ercot_profile(tmp_path, monkeypatch) -> None:
    """--config with load_file/lmp_file, iso=ERCOT, real CF shapes via the
    profiles_dir seam; outputs exist and matching lands in (0, 1]."""
    monkeypatch.setattr("lce_portfolio.profiles.DEFAULT_PROFILES_DIR", FIXTURE_DIR)

    load_path, lmp_path = _ercot_fixtures(tmp_path)
    out_dir = tmp_path / "out"
    config_path = tmp_path / "run.json"
    config_path.write_text(
        json.dumps(
            {
                "iso": "ERCOT",
                "year": 2024,  # matches the fixture filename ERCOT_2024.parquet
                "load_file": str(load_path),
                "lmp_file": str(lmp_path),
                "active_resources": ["solar_pv", "onshore_wind"],
                "premium_deltas": [10.0],
            }
        )
    )

    rc = main(["--config", str(config_path), "--out-dir", str(out_dir)])

    assert rc == 0
    frontier = pd.read_parquet(out_dir / "ERCOT_frontier.parquet")
    assert len(frontier) == 1
    matching = float(frontier.iloc[0]["matching_pct"])
    assert 0.0 < matching <= 1.0
    assert frontier.iloc[0]["status"] == "Optimal"

    build_mix = pd.read_parquet(out_dir / "ERCOT_build_mix.parquet")
    assert set(build_mix["resource"]) == {"solar_pv", "onshore_wind"}
    assert (out_dir / "ERCOT_run_metadata.json").exists()
