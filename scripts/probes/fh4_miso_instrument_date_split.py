"""FH-4-MISO γ-rider read: instrument-date split of the window's actual exits.

The MISO leg of the FH-4 γ rider (protocol of record
`docs/handoffs/fh-4-ercot-leg-2026-08-09.md` §1.5, executed for MISO in
`docs/handoffs/fh-4-miso-leg-2026-08-10.md`): of the actual retirements in the
leg's scoring window, how much capacity carried an enforceable instrument dated
at/before the run's confirmed-exit information cutoff
(`confirmed_registry_as_of = date(vintage, 12, 31)`)? An exit whose instrument
post-dates the cutoff — or whose instrument is superseded by a live
counter-instrument (MISO: the J H Campbell DOE FPA §202(c) chain) — is
invisible to the T1-FF confirmed-exit channel BY DESIGN, so the exit-side skill
number must never attribute it to a screen miss. Solve-independent: reads only
the committed scoring target (`capacity_actuals_miso.csv`) and the committed
confirmed-exit registry (`confirmed-retirements/miso.csv`).

Two MISO-specific disclosures the ERCOT probe did not need:

* the registry's only in-window-dated rows (Campbell 1-3, settlement date
  2025-05) are ``superseded=true`` (the rolling DOE §202(c) chain) AND absent
  from the actuals file — the units are physically still running, and the
  actuals date exits at PHYSICAL cessation — so they are reported as their own
  block rather than silently dropped;
* the registry's non-superseded instruments dated ≤ the cutoff (Monroe 1-4,
  MPSC U-21193, 2023-07-26) all carry exit years OUTSIDE the window
  (2028/2032), so they are reported as ≤-cutoff-but-out-of-window context.

Usage::

    uv run python scripts/probes/fh4_miso_instrument_date_split.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUALS = REPO / "data/raw/_validation-source/capacity_actuals_miso.csv"
REGISTRY = REPO / "data/raw/confirmed-retirements/miso.csv"

#: The FH-4-MISO vintage cutoff — date(vintage=2023, 12, 31), the same as-of
#: the runner hands load_confirmed_exits (runner.py confirmed_registry_as_of).
CUTOFF = date(2023, 12, 31)

#: Model thermal taxonomy for the thermal-only line (matches the scorer's
#: retirement per_fuel families; storage/renewable/biomass/other excluded).
THERMAL = {"coal", "gas_cc", "gas_ct", "gas_st", "nuclear", "oil"}


def _load_registry() -> pd.DataFrame:
    """Registry with parsed dates and the scorer-matching ``unit_id`` column."""
    reg = pd.read_csv(REGISTRY, comment="#")
    reg["instrument_date"] = pd.to_datetime(reg["instrument_date"]).dt.date
    reg["unit_id"] = (
        reg["plant_id"].astype(int).astype(str) + "_" + reg["generator_id"].astype(str)
    )
    reg["superseded"] = reg["superseded"].fillna(False).astype(bool)
    return reg


def split(window: tuple[int, int]) -> dict:
    """Return the instrument-date split of actual retirements in ``window``."""
    actual = pd.read_csv(ACTUALS, comment="#")
    ret = actual[
        (actual["kind"] == "retirement") & actual["year"].between(window[0], window[1])
    ].copy()
    reg = _load_registry()
    live = reg[~reg["superseded"]]
    by_unit = live.set_index("unit_id")["instrument_date"].to_dict()

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
        "instrumented_le_cutoff_mw": _mw(ret, lambda f: f["instrumented_by_cutoff"]),
        "instrumented_after_cutoff_mw": _mw(ret, lambda f: f["instrumented_after"]),
        "no_instrument_mw": _mw(ret, lambda f: f["instrument_date"].isna()),
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


def registry_context(window: tuple[int, int]) -> dict:
    """MISO registry rows that shape the split without entering it.

    (a) superseded rows whose registered exit year falls in ``window`` — the
    loader ignores them (live counter-instrument), and whether each appears in
    the physical-cessation actuals is reported rather than assumed; (b)
    non-superseded rows instrumented ≤ CUTOFF whose exit year is OUTSIDE the
    window — instruments the confirmed-exit channel can carry, none of which
    this window's scoring can see.
    """
    reg = _load_registry()
    actual = pd.read_csv(ACTUALS, comment="#")
    actual_units = set(actual.loc[actual["kind"] == "retirement", "unit_id"])
    sup = reg[reg["superseded"] & reg["exit_year"].between(window[0], window[1])]
    le_out = reg[
        ~reg["superseded"]
        & reg["instrument_date"].map(lambda d: isinstance(d, date) and d <= CUTOFF)
        & ~reg["exit_year"].between(window[0], window[1])
    ]
    return {
        "superseded_in_window_rows": [
            {
                "unit_id": r.unit_id,
                "unit_name": r.unit_name,
                "mw": r.capacity_mw,
                "registered_exit": f"{int(r.exit_year)}-{int(r.exit_month):02d}",
                "instrument_date": r.instrument_date.isoformat(),
                "in_physical_actuals": r.unit_id in actual_units,
            }
            for r in sup.itertuples()
        ],
        "le_cutoff_out_of_window_rows": [
            {
                "unit_id": r.unit_id,
                "unit_name": r.unit_name,
                "mw": r.capacity_mw,
                "registered_exit": f"{int(r.exit_year)}-{int(r.exit_month):02d}",
                "instrument_date": r.instrument_date.isoformat(),
            }
            for r in le_out.itertuples()
        ],
    }


def main() -> None:
    """Print the split for the FH-4 window and the scorer's referent window."""
    out = {
        "fh4_window": split((2023, 2025)),
        "scorer_referent_window": split((2021, 2025)),
        "registry_context": registry_context((2023, 2025)),
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
