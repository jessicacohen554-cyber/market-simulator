"""End-to-end minimal example: generate synthetic inputs, run a premium sweep.

Run from the project root::

    python examples/run_sample_sweep.py

Generates a deterministic synthetic 8760 load and BAU LMP for a single
``SAMPLE`` ISO (written to ``data/sample/``), then runs the default premium-cap
sweep and writes Parquet outputs to ``data/outputs/``. This proves the whole
pipeline — intake -> resources -> profiles -> LP -> sweep -> outputs — without
any external data or ``market_sim`` dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Make the package importable when run as a plain script.
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig  # noqa: E402
from lce_portfolio.intake import prepare_load  # noqa: E402
from lce_portfolio.outputs import summarize, write_outputs  # noqa: E402
from lce_portfolio.profiles import build_cf_matrix  # noqa: E402
from lce_portfolio.resources import load_resource_arrays  # noqa: E402
from lce_portfolio.sweep import run_sweep  # noqa: E402

ISO = "SAMPLE"


def make_sample_inputs(sample_dir: Path) -> tuple[Path, Path]:
    """Write deterministic synthetic load + LMP CSVs; return their paths."""
    sample_dir.mkdir(parents=True, exist_ok=True)
    hours = np.arange(HOURS_PER_YEAR)
    hod = hours % 24
    doy = hours // 24

    # Load: 500 MW base with a daytime commercial peak and mild summer envelope.
    daily = 1.0 + 0.35 * np.sin((hod - 8) / 24.0 * 2 * np.pi)
    seasonal = 1.0 + 0.15 * np.sin((doy - 172) / 365.0 * 2 * np.pi)
    load = 500.0 * np.clip(daily, 0.4, None) * seasonal

    # BAU LMP: cheap overnight, expensive on summer afternoons (net-load driven).
    peak = np.clip(np.sin((hod - 9) / 24.0 * 2 * np.pi), 0, None)
    lmp = 22.0 + 45.0 * peak * seasonal + 3.0 * np.sin(hours / 13.0)
    lmp = np.clip(lmp, 5.0, None)

    load_df = pd.DataFrame(
        {"hour": hours, "iso": ISO, "facility": "plant_A", "load_mwh": load}
    )
    lmp_df = pd.DataFrame({"hour": hours, "iso": ISO, "lmp": lmp})
    load_path = sample_dir / "sample_load.csv"
    lmp_path = sample_dir / "sample_lmp.csv"
    load_df.to_csv(load_path, index=False)
    lmp_df.to_csv(lmp_path, index=False)
    return load_path, lmp_path


def main() -> int:
    """Generate inputs, run the default premium sweep, print + write results."""
    sample_dir = _ROOT / "data" / "sample"
    out_dir = _ROOT / "data" / "outputs"
    load_path, lmp_path = make_sample_inputs(sample_dir)

    # excess_sale_fraction < 1 credits surplus clean generation at a haircut to
    # wholesale, so over-building to dump excess is not "free". This is a PS-02
    # decision; the demo uses 0.3 to produce an illustrative rising frontier
    # (the library default is 1.0 / full resale).
    config = PortfolioConfig(iso=ISO, mode="premium_cap", excess_sale_fraction=0.3)
    resources = load_resource_arrays(config)
    load = prepare_load(load_path, ISO, config)
    lmp = pd.read_csv(lmp_path).sort_values("hour")["lmp"].to_numpy(dtype=float)
    cf = build_cf_matrix(resources, ISO, config.year)

    sweep = run_sweep(config, resources, load, lmp, cf)
    paths = write_outputs(sweep, out_dir)
    print(summarize(sweep))
    print(f"\nwrote: {paths['frontier']}\n       {paths['build_mix']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
