#!/usr/bin/env python
"""Derive each coal plant's MINIMUM ONLINE CONFIGURATION from EIA-860.

The unit-grain min-load instrument behind
``ScenarioConfig.ercot_coal_min_config_floor`` (lane ercot128-unit-grain;
`docs/DIAGNOSIS-ercot128-coal-unit-grain-2026-07-28.md`).

What it measures
----------------
A multi-unit coal plant cannot be pushed below the minimum load of its
**smallest online configuration** — the least MW it can hold with at least one
unit synchronised, ``min over units u of MinLoad_u``. That is a property of the
plant's unit inventory, not of any hour's commitment, so it needs no commitment
state and no integrality: the model's LP unit is the plant, and this value is
its ``pmin``.

**Why a plant-grain LP variable represents it exactly.** A plant's exact online
unit-commitment feasible set is the union, over all non-empty subsets ``S`` of
its units, of ``[Σ_S MinLoad_u, Σ_S Cap_u]``. Where that union is CONNECTED it
equals the single interval ``[min_u MinLoad_u, Σ_u Cap_u]`` and the plant-grain
bound is a zero-error representation of unit-grain commitment's lower envelope.
Adjacent configurations overlap whenever ``MinLoad/Cap < 0.5``, which holds for
every ERCOT coal unit except San Miguel (0.639) and Major Oak (0.625) — so the
union is connected for 9 of 10 plants and 97.76 % of ERCOT coal capacity. The
``connected`` column records the test per plant; where it is False the interval
is a strict RELAXATION (it admits levels no unit combination delivers), which is
the safe direction under rule 14 ``[R-ACCURATE]`` — it never forbids something
the real plant did — but it is written to the artifact rather than assumed away.

Rule 13 ``[R-MEASURED]`` admissibility
--------------------------------------
``Minimum Load (MW)`` and ``Summer Capacity (MW)`` are **registration** facts
filed by the operator on EIA-860, not measured operation and not an outcome of
the dispatch being validated. They exist for any vintage and they respond to
condition — a retired unit leaves the file, an uprate changes the value — so the
same quantity regenerates for a forward year, which is the admissibility test.
Corroboration (never a substitute): the ERCOT COP ``LSL`` from the 60-Day DAM
Gen Resource corpus agrees EXACTLY on the three plants whose COP resources are
whole units (Coleto Creek 175, Oak Grove 348, J K Spruce 130) and disagrees only
where a resource is an ownership SHARE of a unit rather than the unit (Fayette 5
resources on 3 units, Sandy Creek 4 on 1), which is why EIA-860 is the source
here and the COP is the check.

Rule 23 ``[R-FROZEN-DERIVE]``
-----------------------------
This script is frozen against residuals. It re-derives ONLY when
``data/raw/eia-860/eia860_generator_operable.parquet`` updates; a re-derivation
commit must cite the data change. No value here may be chosen, rounded or
filtered to move a backcast residual — there is no residual input to this
script, by construction: it reads one registration file and takes a minimum.

Usage
-----
    python scripts/data/derive_eia860_coal_min_config.py --iso ERCOT
    python scripts/data/derive_eia860_coal_min_config.py --iso ERCOT --dry-run
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from market_sim.config import paths  # noqa: E402

# EIA-860 ``Energy Source 1`` codes that make a generator coal-fired. Matches
# the taxonomy's coal ranks (bituminous / sub-bituminous / lignite / refined
# coal / waste coal); a plant's gas-steam units (W A Parish 3470) are excluded
# by this filter, exactly as the ERCOT-126/127/128 probes exclude them.
COAL_FUEL_CODES: tuple[str, ...] = ("BIT", "SUB", "LIG", "RC", "WC")

# EIA-860 statuses that mean the unit exists and can be committed. ``OS`` (out
# of service but not retired) is KEPT: an OS unit still carries a registered
# minimum load, and whether it runs in a given year is the availability layer's
# job, not this artifact's.
OPERABLE_STATUSES: tuple[str, ...] = ("OP", "SB", "OA", "OS")


def iso_coal_plant_codes(iso: str) -> set[int]:
    """Return the EIA plant codes the ISO's own fleet carries as COAL.

    Read from the ISO's bin-assignment sheet rather than filtered by state, so
    the artifact can never pick up a coal plant that sits in the same state but
    belongs to a neighbouring market (SPP/MISO plants in Texas), and can never
    miss one the model does carry. ERCOT drives off the curated
    ``reference/custom-bin-assignments.csv``; other ISOs off the exported
    ``_processed-legacy/bin_assignments_<ISO>.csv``.
    """
    if iso.upper() == "ERCOT":
        path = paths.RAW_DIR / "reference" / "custom-bin-assignments.csv"
    else:
        path = paths.PROCESSED_DIR / f"bin_assignments_{iso.upper()}.csv"
    if not path.exists():
        raise SystemExit(f"no bin-assignment sheet for {iso}: {path}")
    df = pd.read_csv(path)
    grp = df["Plant_Group"].astype(str).str.upper()
    return {int(c) for c in df.loc[grp.str.startswith("COAL"), "Plant_Code"]}


def coal_min_config(iso: str) -> pd.DataFrame:
    """Return one row per coal plant with its minimum online configuration.

    Columns: ``plant_code``, ``plant_name``, ``state``, ``n_units``,
    ``cap_mw``, ``min_config_mw``, ``min_config_frac_of_cap``, ``connected``,
    ``gap_mw``, ``status``, ``source``.
    """
    g = pd.read_parquet(paths.RAW_DIR / "eia-860" / "eia860_generator_operable.parquet")
    g["Plant Code"] = pd.to_numeric(g["Plant Code"], errors="coerce")
    g = g[g["Plant Code"].isin(iso_coal_plant_codes(iso))]
    g = g[g["Energy Source 1"].astype(str).str.upper().isin(COAL_FUEL_CODES)]
    g = g[g["Status"].astype(str).str.upper().isin(OPERABLE_STATUSES)]

    units = pd.DataFrame(
        {
            "plant_code": g["Plant Code"],
            "plant_name": g["Plant Name"].astype(str),
            "state": g["State"].astype(str).str.upper(),
            "cap_mw": pd.to_numeric(g["Summer Capacity (MW)"], errors="coerce"),
            "min_load_mw": pd.to_numeric(g["Minimum Load (MW)"], errors="coerce"),
        }
    ).dropna(subset=["plant_code", "cap_mw", "min_load_mw"])
    units = units[(units.cap_mw > 0.0) & (units.min_load_mw > 0.0)]
    units["plant_code"] = units.plant_code.astype(int)

    rows: list[dict] = []
    for code, u in units.groupby("plant_code"):
        mins = u.min_load_mw.to_numpy(dtype=float)
        caps = u.cap_mw.to_numpy(dtype=float)
        n = len(mins)
        # Exact online feasible set = union over non-empty unit subsets.
        # Enumeration is 2^n - 1 and n is at most a handful of coal units per
        # plant, so this is exact rather than approximated.
        ivals = sorted(
            (float(mins[list(S)].sum()), float(caps[list(S)].sum()))
            for r in range(1, n + 1)
            for S in itertools.combinations(range(n), r)
        )
        merged: list[list[float]] = [list(ivals[0])]
        for lo, hi in ivals[1:]:
            if lo <= merged[-1][1] + 1e-9:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        gap_mw = sum(merged[i + 1][0] - merged[i][1] for i in range(len(merged) - 1))
        rows.append(
            {
                "plant_code": int(code),
                "plant_name": u.plant_name.iloc[0],
                "state": u.state.iloc[0],
                "n_units": int(n),
                "cap_mw": round(float(caps.sum()), 1),
                "min_config_mw": round(float(mins.min()), 1),
                "min_config_frac_of_cap": round(float(mins.min() / caps.sum()), 5),
                "connected": bool(len(merged) == 1),
                "gap_mw": round(float(gap_mw), 1),
                "status": "ok",
                "source": "eia860_generator_operable: min over units of Minimum Load (MW)",
            }
        )
    return pd.DataFrame(rows).sort_values("plant_code").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Derive each coal plant's minimum online configuration (min over "
            "its units of the EIA-860 registered Minimum Load) — the unit-grain "
            "min-load instrument consumed by "
            "ScenarioConfig.ercot_coal_min_config_floor. Frozen against "
            "residuals (rule 23): re-derive only when EIA-860 updates."
        )
    )
    ap.add_argument("--iso", default="ERCOT", help="ISO code (default ERCOT)")
    ap.add_argument(
        "--dry-run", action="store_true", help="print the frame and write nothing"
    )
    args = ap.parse_args()

    df = coal_min_config(args.iso)
    if df.empty:
        raise SystemExit(
            f"no coal generators with a registered Minimum Load for {args.iso}"
        )

    print(df.to_string(index=False))
    tot_cap = float(df.cap_mw.sum())
    conn_cap = float(df[df.connected].cap_mw.sum())
    print(
        f"\n{len(df)} plants · {tot_cap:,.0f} MW · "
        f"cap-weighted min-config frac "
        f"{float(df.min_config_mw.sum()) / tot_cap:.4f} · "
        f"{int(df.connected.sum())}/{len(df)} plants gap-free "
        f"({conn_cap / tot_cap:.4f} of capacity exactly representable)"
    )

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return
    out = paths.PROCESSED_DIR / f"coal_min_config_{args.iso.upper()}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nwrote {out.relative_to(_REPO)}")


if __name__ == "__main__":
    main()
