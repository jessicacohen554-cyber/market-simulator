"""Derive the RESERVE-DUTY (capacity-only) combined-cycle cohort from the meter.

The membership basis for ``ScenarioConfig.cc_reserve_duty_split`` (nyiso-146):
the duty-role cohort of CC_REGULAR plants that hold capacity but essentially
never sell energy — NYISO's Seneca Power Partners fleet (Sterling, Batavia,
Massena, Carthage) and its peers, which the Gold Book lists as market
generators with CRIS ratings while their meters read 1-5 % of hours online.
The LP, seeing only their (competitive) heat rates, runs them 87-99 % of
hours — the nyiso-145 defect B "merit-order inversion" (model/EIA-923 ratios
of 25-225x). The split routes the cohort's whole dispatchable capacity to the
class offer curve's PEAK band — the duty-role mirror of
``cc_intermediate_split`` (which flattens offers for the HIGH-CF cohort;
this steepens them for the RESERVE cohort), assigning an offer *shape*,
never a pin to measured output, admissible on the same basis (rule 13; see
the ``ct_intermediate_plants`` docstring lineage).

QUALIFYING TEST — measured, mechanism-blind, pooled 2023-2025:

* plants with a CEMS record: plant-summed-series ONLINE SHARE
  (``grossLoad >= max(_ONLINE_MW, 0.05 x plant HSL)``, the lay-up artifact's
  own construction) at or below :data:`_ONLINE_SHARE_MAX`;
* plants with NO CEMS record at all (Allegany 7784, a CAMPD-less cogen the
  model classes CC_REGULAR): pooled EIA-923 annual net capacity factor at or
  below the same threshold — the same meter class, the universal filing.

THE THRESHOLD IS A POPULATION GAP, not a tuned value (rules 5/21): measured
on NYISO's live CC fleet the on-share distribution is
{0.012, 0.024, 0.025, 0.040, 0.047, 0.064} then a 2.7x gap to
{0.17 Pinelawn, 0.22 Castleton, 0.34 Carr Street, ...} — the qualifying set
stops at 0.064 and the nearest non-qualifier sits at 0.17, so any threshold
inside (0.064, 0.17) selects the identical set; 0.10 is the round midpoint.
Carr Street (0.34) and Pinelawn (0.17) — the "mild" 2-3x plants — are
deliberately NOT in the cohort: they are cyclers whose over-run is an
offer/commitment question, and pushing them out of merit by membership would
bury that error (the nyiso-144 plant-7314 discipline).

Output: ``data/raw/_processed-legacy/reserve_duty_cc_{ISO}.csv``. Governance
(rules 13/23): a measured duty-role membership in the same admissibility
class as the lay-up census — regenerates from the meters for any new vintage,
responds to changed conduct (a reactivated plant exits the cohort), and
re-derives ONLY when the source data updates, never because a residual moved.

Usage::

    python scripts/data/derive_reserve_duty_cc.py --iso NYISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_campd_gas_commitment_params import (  # noqa: E402
    _HSL_PCTILE,
    _ONLINE_FRAC,
    class_plant_codes,
)
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"
E923_PATH = RAW_DIR / "_processed-legacy" / "eia923_monthly_generation.parquet"

# Reserve-duty ceiling on the pooled measured on-share / capacity factor.
# A population-gap separator, not a tuned value — see the module docstring.
_ONLINE_SHARE_MAX: float = 0.10

TARGET_CLASS = "CC_REGULAR"


def derive(iso: str, years: list[int]) -> pd.DataFrame:
    """Measure every CC plant's duty statistic and mark the qualifying set."""
    mapping, ambiguous = class_plant_codes(iso, (TARGET_CLASS,))
    if ambiguous:
        print(
            f"  ({len(ambiguous)} mixed-class plant code(s) unattributable at "
            f"CAMPD facility level keep their class offer curve: {ambiguous})"
        )
    codes = set(mapping)

    # Plant-summed CAMPD series per (facility, year) — the lay-up construction.
    by_plant: dict[int, dict[int, list[np.ndarray]]] = {}
    names: dict[int, str] = {}
    for state in states_for_iso(iso):
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "facilityName",
                    "unitId",
                    "date",
                    "hour",
                    "grossLoad",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            df = df.sort_values(["facilityId", "unitId", "date", "hour"])
            for (fid, _uid), g in df.groupby(["facilityId", "unitId"], sort=False):
                fid = int(fid)
                by_plant.setdefault(fid, {}).setdefault(year, []).append(
                    g["grossLoad"].fillna(0.0).to_numpy(dtype=float)
                )
                names[fid] = str(g["facilityName"].iloc[0])

    # EIA-923 pooled CF fallback needs each plant's capacity: use the model
    # fleet's own pmax sum (the denominator the LP dispatches against).
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    pmax_by_code: dict[int, float] = {}
    name_by_code: dict[int, str] = {}
    for g in fleet:
        c = int(g.plant_code or 0)
        if c in codes and g.plant_group == TARGET_CLASS:
            pmax_by_code[c] = pmax_by_code.get(c, 0.0) + float(g.pmax_mw)
            name_by_code.setdefault(c, g.name)
    e923 = pd.read_parquet(E923_PATH)
    e923 = e923[e923["year"].isin(years)]
    e923_by_code = e923.groupby("plant_id")["netgen_annual_mwh"].sum().to_dict()

    rows = []
    for code in sorted(codes):
        if code in by_plant:
            yearly = []
            for year in sorted(by_plant[code]):
                chunks = by_plant[code][year]
                n = min(c.size for c in chunks)
                yearly.append(np.sum([c[:n] for c in chunks], axis=0))
            pooled = np.concatenate(yearly)
            hsl = float(np.percentile(pooled, _HSL_PCTILE))
            if hsl <= _ONLINE_MW:
                basis, value = "campd_degenerate", 0.0
            else:
                thresh = max(_ONLINE_MW, _ONLINE_FRAC * hsl)
                basis, value = "campd_online_share", float((pooled >= thresh).mean())
        else:
            cap = pmax_by_code.get(code, 0.0)
            gen = float(e923_by_code.get(code, 0.0))
            if cap <= 0.0:
                continue
            basis = "e923_pooled_cf"
            value = gen / (cap * 8760.0 * len(years))
        rows.append(
            {
                "iso": iso,
                "plant_code": code,
                "plant_name": names.get(code, name_by_code.get(code, "")),
                "plant_class": TARGET_CLASS,
                "basis": basis,
                "duty_stat": round(value, 4),
                "reserve_duty": bool(value <= _ONLINE_SHARE_MAX),
                "years": "-".join(str(y) for y in years),
                "source": (
                    "CAMPD plant-summed online share (grossLoad >= "
                    f"max({_ONLINE_MW} MW, {_ONLINE_FRAC} x plant "
                    f"HSL=p{_HSL_PCTILE})) where a CEMS record exists, else "
                    "EIA-923 pooled net CF over the model plant pmax; "
                    f"reserve_duty iff <= {_ONLINE_SHARE_MAX} (population-gap "
                    "separator, see derive_reserve_duty_cc.py)"
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Derive and write the reserve-duty cohort artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True)
    parser.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    iso = args.iso.upper()
    df = derive(iso, args.years)
    if df.empty:
        raise SystemExit(f"{iso}: no {TARGET_CLASS} plants measured")
    out = Path(args.out) if args.out else PROCESSED_DIR / f"reserve_duty_cc_{iso}.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} rows, {int(df.reserve_duty.sum())} qualifying)")
    print(df.sort_values("duty_stat").to_string(index=False))


if __name__ == "__main__":
    main()
