"""FH-4-NYISO γ-rider read: instrument-date split of the window's actual exits.

The NYISO sibling of ``scripts/probes/fh4_instrument_date_split.py`` (the AG.2
γ rider, protocol of record ``docs/handoffs/fh-4-ercot-leg-2026-08-09.md``
§1.5), pointed at the NYISO committed artifacts. Of the actual retirements in
the leg's scoring window, how much capacity carried an enforceable instrument
dated at/before the run's confirmed-exit information cutoff
(``confirmed_registry_as_of = date(vintage, 12, 31)``)? An exit whose
instrument post-dates the cutoff is invisible to the T1-FF confirmed-exit
channel BY DESIGN, so the exit-side skill number must never attribute it to a
screen miss.

NYISO registry fact, visible at prereg: ``confirmed-retirements/nyiso.csv`` is
an AUDITED ZERO (zero qualifying rows; every completed deactivation notice
reversed, withdrawn or retained — re-verified 2026-07-05 / 2026-07-31 /
2026-08-03 in the file's own header). The split is therefore expected to be
degenerate — 0 MW instrumented at ANY date, 100 % of the window's actual exit
MW carrying no instrument in the registry — and this probe computes and
records that from the artifacts rather than asserting it.

Solve-independent: reads only the committed scoring target
(``capacity_actuals_nyiso.csv``) and the committed confirmed-exit registry
(``confirmed-retirements/nyiso.csv``).

Usage::

    uv run python scripts/probes/fh4_nyiso_instrument_date_split.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUALS = REPO / "data/raw/_validation-source/capacity_actuals_nyiso.csv"
REGISTRY = REPO / "data/raw/confirmed-retirements/nyiso.csv"

#: The FH-4-NYISO vintage cutoff — date(vintage=2023, 12, 31), the same as-of
#: the runner hands load_confirmed_exits (runner.py confirmed_registry_as_of).
CUTOFF = date(2023, 12, 31)

#: Model thermal taxonomy for the thermal-only line (matches the scorer's
#: retirement per_fuel families; storage/renewable/biomass/other excluded).
THERMAL = {"coal", "gas_cc", "gas_ct", "gas_st", "nuclear", "oil"}


def split(window: tuple[int, int]) -> dict:
    """Return the instrument-date split of actual retirements in ``window``."""
    actual = pd.read_csv(ACTUALS, comment="#")
    ret = actual[
        (actual["kind"] == "retirement") & actual["year"].between(window[0], window[1])
    ].copy()
    reg = pd.read_csv(REGISTRY, comment="#")
    reg = reg[~reg["superseded"].fillna(False).astype(bool)].copy()
    reg["instrument_date"] = pd.to_datetime(reg["instrument_date"]).dt.date
    # An empty registry (the NYISO audited zero) maps every unit to NaN below.
    reg["unit_id"] = (
        reg["plant_id"].astype("Int64").astype(str)
        + "_"
        + reg["generator_id"].astype(str)
    )
    by_unit = reg.set_index("unit_id")["instrument_date"].to_dict()

    ret["instrument_date"] = ret["unit_id"].map(by_unit)
    ret["instrumented_by_cutoff"] = ret["instrument_date"].map(
        lambda d: isinstance(d, date) and d <= CUTOFF
    )
    ret["instrumented_after"] = ret["instrument_date"].map(
        lambda d: isinstance(d, date) and d > CUTOFF
    )
    thermal = ret[ret["fuel"].isin(THERMAL)]

    def _mw(frame: pd.DataFrame, mask=None) -> float:
        sel = frame if mask is None else frame[mask(frame)]
        return round(float(sel["mw"].sum()), 1)

    return {
        "window": f"{window[0]}-{window[1]}",
        "cutoff": CUTOFF.isoformat(),
        "actual_retired_mw_all": _mw(ret),
        "actual_retired_mw_thermal": _mw(thermal),
        "actual_retired_mw_by_fuel": {
            k: round(float(v), 1)
            for k, v in ret.groupby("fuel")["mw"].sum().items()
        },
        "instrumented_le_cutoff_mw": _mw(ret, lambda f: f["instrumented_by_cutoff"]),
        "instrumented_after_cutoff_mw": _mw(ret, lambda f: f["instrumented_after"]),
        "no_instrument_mw": _mw(ret, lambda f: f["instrument_date"].isna()),
        "registry_rows": int(len(reg)),
        "instrumented_after_rows": [
            {
                "unit_id": r.unit_id,
                "fuel": r.fuel,
                "mw": r.mw,
                "year": int(r.year),
                "instrument_date": r.instrument_date.isoformat(),
            }
            for r in ret[ret["instrumented_after"]].itertuples()
        ],
    }


def main() -> None:
    """Print the split for the FH-4 window and the scorer's unfiltered window."""
    out = {
        "fh4_window": split((2023, 2025)),
        "scorer_unfiltered_window": split((2021, 2025)),
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
