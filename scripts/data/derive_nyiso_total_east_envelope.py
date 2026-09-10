"""Derive the measured TOTAL EAST cutset transfer envelope for NYISO.

    uv run python scripts/data/derive_nyiso_total_east_envelope.py

Prints the ``constants.NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH`` literal — one
12-element list (Jan..Dec) of MW per backcast year for the model's single
``Upstate_West -> Capital_Hudson`` link.

WHY THIS EXISTS (rule 14 ``[R-ACCURATE]``, misalignment exception). The model's
five-zone NYISO reduction collapses NYISO load zones A-E into ``Upstate_West``,
so that one link IS the A-E -> F+ cutset. NYISO's own name for that cutset is
**TOTAL EAST**. ``constants.NYISO_INTERFACE_TTC_BY_MONTH`` instead caps the link
at the posted **CENT EAST** DAM TTC, which is a *nested sub-cutset* of Total East
— the single-GTC-for-several-parallel-paths case rule 14 names verbatim. Measured
consequence, from the same postings: the CENT EAST cap sits BELOW the measured
Total East flow in 86.3 / 95.8 / 61.3 / 58.2 % of the hours of 2022-2025.

THE CONSTRUCTION IS INHERITED, NOT CHOSEN (rule 21 ``[R-DOF]``: zero free
parameters). It is verbatim the construction already armed for NYISO's border
links by ``nyiso_seam_deliverability_envelope`` (nyiso-125, matrix cell K): the
**p90 of the directionally-clipped measured transfer** within each bin. The bin
here is the calendar month, which is the bin ``NYISO_INTERFACE_TTC_BY_MONTH``
already uses, so the arm re-uses that one seam rather than adding a second
(rule 19 ``[R-ONE-MECH]``); values are rounded to 25 MW, which is that table's
own rounding. Measured: the month x hour-of-day bin of nyiso-125's border
construction and this monthly bin give binding shares of 9.85 % and 10.06 % in
2022 — indistinguishable — so the coarser bin costs nothing and keeps one seam.

Source: ``data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_<year>.csv.gz``
(NYISO MIS hourly interface flow/limit postings, fetched by
``scripts/data/fetch_nyiso_interface_flows.py``) — the same producer as the
CENT EAST table this one sits beside.

FORWARD STORY (rule 13 ``[R-MEASURED]``): identical to the CENT EAST table's and
inherited from it — the envelope is a BACKCAST-ONLY measured limit; the forward
channel for the level is the transmission-expansion registry
(``data/raw/transmission-expansion/nyiso.csv``) over the static topology value.
"""

from __future__ import annotations

import pandas as pd

from market_sim.config import paths

INTERFACE = "TOTAL EAST"
QUANTILE = 0.90
ROUND_MW = 25.0
YEARS = (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)


def monthly_envelope(year: int) -> list[float] | None:
    """Return the 12 calendar-month p90 MW for ``year``, or ``None`` if absent."""
    src = (
        paths.RAW_DIR
        / "NYISO"
        / "interface-flows"
        / f"NYISO_interface_flows_hourly_{year}.csv.gz"
    )
    if not src.exists():
        return None
    frame = pd.read_csv(src)
    rows = frame[frame["interface"] == INTERFACE].copy()
    if rows.empty:
        return None
    rows["ts"] = pd.to_datetime(rows["interval_start_local"], errors="coerce", utc=True)
    rows = rows.dropna(subset=["ts"])
    # Directionally clipped: the link's positive (upstate -> east) capability.
    rows["pos"] = rows["flow_mw"].clip(lower=0.0)
    p90 = rows.groupby(rows["ts"].dt.month)["pos"].quantile(QUANTILE)
    if len(p90) != 12:
        return None
    return [round(float(v) / ROUND_MW) * ROUND_MW for v in p90.sort_index()]


def main() -> None:
    print(
        "NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH: "
        "dict[int, dict[tuple[str, str], list[float]]] = {"
    )
    for year in YEARS:
        env = monthly_envelope(year)
        if env is None:
            continue
        print(f"    {year}: {{")
        print('        ("Upstate_West", "Capital_Hudson"): [')
        for value in env:
            print(f"            {value:.1f},")
        print("        ]")
        print("    },")
    print("}")


if __name__ == "__main__":
    main()
