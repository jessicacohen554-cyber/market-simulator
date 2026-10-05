"""Rebase an ISO's measured heat-rate artifacts onto its measured parasitic factors.

The four measured-HR derives (``derive_campd_{coal,cc,ct,gas_st}_heat_rates``) measure each plant's GROSS rate
from CAMPD and convert it to net with ONE plant factor, the same for all of the plant's units:
``hr_net = hr_gross / parasitic_factor(plant)``. The factor comes from the pooled rows of
``parasitic_load_factors.parquet``, falling back to the class default (``campd.DEFAULT_PARASITIC_LOAD_PCT``) when
the plant has no row.

When ``derive_parasitic_load.py`` back-fills an ISO's measured factors (a SOURCE-DATA change, rule 23), the frozen
construction says each artifact's net columns move to ``hr_gross / factor_new`` and nothing else does. Re-running a
derive end to end at a later HEAD can also move the gross measurement for unrelated reasons (fleet or attribution
code that changed after the artifact was cut; closeout-SOCO-w3 measured this for SOCO's CT, ST and tranche artifacts).
So this script applies exactly the net conversion to the committed rows and nothing more:

* rows whose plant has a MEASURED pooled factor: ``heat_rate *= factor_old / factor_new``,
  ``parasitic_factor = factor_new``, ``model_over_measured = model_heat_rate_egrid / heat_rate``;
* the physical-band flag is re-evaluated with the derive's own band constants, only on rows whose flag is already
  ``ok`` / ``below_physical_band`` / ``above_physical_band`` (boundary and pairing refusals keep precedence);
* ``eia923_identity`` rows (their rate is EIA-923 heat / net, not a CAMPD conversion) are left unchanged;
* plants without a measured factor keep their class default.

Usage:
    python scripts/data/rebase_measured_hr_parasitic.py --iso SOCO [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402

#: class key -> (derive module under scripts.data, band-constant names)
_CLASSES: dict[str, tuple[str, tuple[str, str]]] = {
    "coal": ("derive_campd_coal_heat_rates", ("_HR_MIN_NET", "_HR_MAX_NET")),
    "cc": ("derive_campd_cc_heat_rates", ("_HR_MIN_NET", "_HR_MAX_NET")),
    "ct": ("derive_campd_ct_heat_rates", ("_HR_MIN", "_HR_MAX")),
    "st": ("derive_campd_gas_st_heat_rates", ("_HR_MIN_NET", "_HR_MAX_NET")),
}
_BAND_FLAGS = ("ok", "below_physical_band", "above_physical_band")
_UNCHANGED_FLAGS = ("eia923_identity",)


def measured_factors() -> dict[int, float]:
    """Return ``{plant_id: factor}`` from the pooled MEASURED rows of the parasitic artifact."""
    par = pd.read_parquet(PROCESSED_DIR / "parasitic_load_factors.parquet")
    pooled = par[
        (par["year"] == 0) & par["source"].isin(("measured", "measured_running"))
    ]
    return dict(
        zip(pooled["plant_id"].astype(int), pooled["parasitic_factor"].astype(float))
    )


def band(module: str, names: tuple[str, str]) -> tuple[float, float]:
    """Return the derive's own net physical band."""
    import importlib

    mod = importlib.import_module(f"scripts.data.{module}")
    return float(getattr(mod, names[0])), float(getattr(mod, names[1]))


def rebase(
    table: pd.DataFrame, factors: dict[int, float], lo: float, hi: float
) -> tuple[pd.DataFrame, int]:
    """Return the rebased table and the number of rows moved."""
    t = table.copy()
    new = t["plant_code"].astype(int).map(factors)
    move = new.notna() & ~t["flag"].isin(_UNCHANGED_FLAGS)
    old = t.loc[move, "parasitic_factor"].astype(float)
    t.loc[move, "heat_rate"] = (
        t.loc[move, "heat_rate"].astype(float) * old / new[move]
    ).round(4)
    t.loc[move, "parasitic_factor"] = new[move].round(6)
    t.loc[move, "model_over_measured"] = (
        t.loc[move, "model_heat_rate_egrid"].astype(float) / t.loc[move, "heat_rate"]
    ).round(4)
    reflag = move & t["flag"].isin(_BAND_FLAGS)
    hr = t.loc[reflag, "heat_rate"].astype(float)
    t.loc[reflag, "flag"] = np.where(
        hr < lo, "below_physical_band", np.where(hr > hi, "above_physical_band", "ok")
    )
    return t, int(move.sum())


def main(argv: list[str] | None = None) -> int:
    """Rebase every measured-HR artifact the ISO has."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument(
        "--dry-run", action="store_true", help="report the moves, write nothing"
    )
    a = ap.parse_args(argv)
    iso = a.iso.upper()
    factors = measured_factors()
    for cls, (module, names) in _CLASSES.items():
        path = PROCESSED_DIR / f"campd_{cls}_heat_rates_{iso}.csv"
        if not path.exists():
            continue
        table = pd.read_csv(path)
        lo, hi = band(module, names)
        out, n = rebase(table, factors, lo, hi)
        flips = int((out["flag"] != table["flag"]).sum())
        pooled = out["year"] == 0
        d = (out.loc[pooled, "heat_rate"] - table.loc[pooled, "heat_rate"]).astype(
            float
        )
        print(
            f"{path.name}: {n} rows rebased, {flips} flag changes, pooled HR delta "
            f"min {d.min():+.4f} median {d.median():+.4f} max {d.max():+.4f}"
        )
        if not a.dry_run and n:
            out.to_csv(path, index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
