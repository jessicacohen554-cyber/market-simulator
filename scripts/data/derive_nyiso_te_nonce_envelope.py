"""Derive the measured non-CENTRAL-EAST TOTAL EAST envelope for NYISO.

    uv run python scripts/data/derive_nyiso_te_nonce_envelope.py

Prints the ``constants.NYISO_TE_NONCE_ENVELOPE_BY_MONTH`` literal — one
12-element list (Jan..Dec) of MW per backcast year for the
``Upstate_West -> Lower_Hudson`` link that ``ScenarioConfig.nyiso_fg_split``
(NYISO-NEXT-17) adds.

WHY THIS EXISTS. Under the F/G re-partition, ``Capital_Hudson`` is NYISO load
zone F alone and ``Lower_Hudson`` is G+H+I, so the A-E -> F+ cutset (TOTAL EAST)
has two physical legs in the model: CENTRAL EAST (E -> F), capped at its posted
DAM TTC (``constants.NYISO_INTERFACE_TTC_BY_MONTH``), and the remaining TOTAL
EAST paths, which enter the east at zone G. This script measures that second
leg as ``TOTAL EAST - CENTRAL EAST`` hour by hour from the same posting.

THE CONSTRUCTION IS INHERITED, NOT CHOSEN (rule 21 ``[R-DOF]``: zero free
parameters). It is verbatim ``derive_nyiso_total_east_envelope.py``: the p90 of
the directionally-clipped measured transfer per calendar month, rounded to
25 MW. Only the series differs (TOTAL EAST minus CENTRAL EAST, per hour).

Rule 14 ``[R-ACCURATE]`` misalignment, declared: the posting does not attribute
the non-CE paths to a landing zone; they are assigned to G on the interface
definitions (the A-E -> F+ cutset less its E -> F subset).

Source: ``data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_<year>.csv.gz``
(NYISO MIS P-32 postings). Backcast-only, on the identical classification as
the tables it sits beside (rule 13 ``[R-MEASURED]``).
"""

from __future__ import annotations

import pandas as pd

from market_sim.config import paths

TOTAL_EAST = "TOTAL EAST"
CENTRAL_EAST = "CENTRAL EAST - VC"
QUANTILE = 0.90
ROUND_MW = 25.0
YEARS = (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)


def monthly_envelope(year: int) -> list[float] | None:
    """Return the 12 calendar-month p90 MW of TE minus CE for ``year``, or ``None``."""
    src = (
        paths.RAW_DIR
        / "NYISO"
        / "interface-flows"
        / f"NYISO_interface_flows_hourly_{year}.csv.gz"
    )
    if not src.exists():
        return None
    frame = pd.read_csv(src)
    rows = frame[frame["interface"].isin([TOTAL_EAST, CENTRAL_EAST])].copy()
    if rows.empty:
        return None
    rows["ts"] = pd.to_datetime(rows["interval_start_local"], errors="coerce", utc=True)
    wide = rows.pivot_table(
        index="ts", columns="interface", values="flow_mw", aggfunc="mean"
    ).dropna()
    if TOTAL_EAST not in wide or CENTRAL_EAST not in wide:
        return None
    # Directionally clipped: the link's positive (upstate -> east) capability.
    rest = (wide[TOTAL_EAST] - wide[CENTRAL_EAST]).clip(lower=0.0)
    p90 = rest.groupby(rest.index.month).quantile(QUANTILE)
    if len(p90) != 12:
        return None
    return [round(float(v) / ROUND_MW) * ROUND_MW for v in p90.sort_index()]


def main() -> None:
    """Print the constants literal."""
    print(
        "NYISO_TE_NONCE_ENVELOPE_BY_MONTH: "
        "dict[int, dict[tuple[str, str], list[float]]] = {"
    )
    for year in YEARS:
        env = monthly_envelope(year)
        if env is None:
            continue
        print(f"    {year}: {{")
        print('        ("Upstate_West", "Lower_Hudson"): [')
        for value in env:
            print(f"            {value:.1f},")
        print("        ]")
        print("    },")
    print("}")


if __name__ == "__main__":
    main()
