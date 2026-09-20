"""nyiso-248 — RE-MEASURE THE P-27 BOOK ON A DAILY GAS SERIES (2x2 decomposition).

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Gate **G-5**.

nyiso-248 G-1/G-3 measured that ``_gas_series`` — the array
``derive_nyiso_offer_level_dispersion`` uses — is a PURE 12-VALUE MONTHLY STEP,
while the array the LP prices gas on is daily and carries 90-120 % of the
measured Transco Z6 within-month swing. That monthly step enters the book
measurement in **TWO** places, not one:

    CONDITIONER   state_windows(): gas_bin >= 2 selects an hour in one of the
                  year's ~1.2 dearest MONTHS, not a dear DAY.
    DENOMINATOR   year_unit_rows(): m = bottom / gas[hour] -- the implied offer
                  heat rate divides the bid's bottom block by that same flat
                  monthly price.

The denominator channel has a PREDICTABLE SIGN and it pushes the same way as the
reported finding: inside one month a flat denominator inflates ``m`` on the dear
days and deflates it on the cheap days, which manufactures a positive
tight-minus-ordinary delta even from a unit whose true implied heat rate is
constant. So the measured object (nyiso-246: pooled delta +2.035 / +11.928 /
+27.880 MMBtu/MWh at p50/p75/p90) cannot be read as clean until the two channels
are separated.

This probe runs the family's OWN estimator -- ``year_unit_rows``,
``per_unit_delta``, ``weighted_quantiles``, the frozen 199-point
``QUANTILE_GRID``, the registered ``NETLOAD_PCTS`` ladder -- and swaps ONLY the
gas array, in each role independently (re-implementing the population rules
would be a tuning channel, which the derive's own docstring forbids):

    A  monthly conditioner, monthly denominator   = the committed artifact
    B  DAILY   conditioner, monthly denominator   = conditioner channel alone
    C  monthly conditioner, DAILY   denominator   = denominator channel alone
    D  DAILY   conditioner, DAILY   denominator   = the corrected measurement

Arm A is a REPRODUCTION CHECK: it must land on the committed
``nyiso_offer_level_dispersion.json`` vector, or the harness is wrong and
nothing else here may be read.

The daily series is ``iso_hub_daily_gas_prices`` on the keeper's own resolved
config -- i.e. exactly what ``_hub_overlay_series`` would return if it honoured
``gas_hub_basis_daily`` the way ``apply_hub_basis_overlay`` already does -- with
uncovered months falling back to the monthly series, the same way the array
path's ``covered`` mask does.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso248_book_daily_regrain.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
ART = REPO / "data" / "raw" / "_validation-source" / "nyiso_offer_level_dispersion.json"
OUT = REPO / "results" / "calibration" / "_nyiso248_book_daily_regrain.json"
REPORT_AT = (0.10, 0.25, 0.50, 0.75, 0.90, 0.99)


def daily_gas(year: int) -> np.ndarray:
    """The daily hub series, monthly-filled where no basis row covers a month."""
    from market_sim.data.fuel.hubs import iso_hub_daily_gas_prices

    from scripts.probes.nyiso242_tail_reachability import fleet_state

    cfg = fleet_state(year)["config"]
    d = iso_hub_daily_gas_prices(cfg, year)
    base = np.load(CACHE / f"gas_{year}.npy").astype(float)
    if d is None:
        return base
    d = np.asarray(d, dtype=float)
    return np.where(np.isnan(d), base, d)


def windows(gas: np.ndarray, netload: np.ndarray, pcts) -> tuple:
    """state_windows' registered binning, with the gas array injected."""
    lb = np.searchsorted(np.quantile(netload, pcts), netload, side="right")
    gb = np.searchsorted(np.quantile(gas, pcts), gas, side="right")
    return (gb >= 2) & (lb >= 2), (gb == 0) & (lb == 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=None)
    args = ap.parse_args()

    from scripts.data.derive_nyiso_offer_level_dispersion import (
        QUANTILE_GRID,
        per_unit_delta,
        weighted_quantiles,
        year_unit_rows,
    )
    from scripts.data.derive_nyiso_offer_surface import (
        NETLOAD_PCTS,
        YEARS,
        gas_series_by_year,
        net_load_by_year,
    )

    years = args.year or list(YEARS)
    monthly = gas_series_by_year()
    nl = net_load_by_year()
    dly = {y: daily_gas(y) for y in years}

    # rows depend ONLY on the denominator, so build each once and reuse.
    rows_by_den: dict[str, dict[int, pd.DataFrame]] = {}
    for den in ("monthly", "daily"):
        rows_by_den[den] = {
            y: year_unit_rows(y, monthly[y] if den == "monthly" else dly[y])
            for y in years
        }

    arms = {
        "A_month_cond_month_den": ("monthly", "monthly"),
        "B_daily_cond_month_den": ("daily", "monthly"),
        "C_month_cond_daily_den": ("monthly", "daily"),
        "D_daily_cond_daily_den": ("daily", "daily"),
    }

    idx = {p: int(np.argmin(np.abs(QUANTILE_GRID - p))) for p in REPORT_AT}
    result: dict = {"gate": "G-5", "years": years, "arms": {}}

    for name, (cond, den) in arms.items():
        frames = []
        per_year_n = {}
        for y in years:
            g = monthly[y] if cond == "monthly" else dly[y]
            t, o = windows(g, nl[y], NETLOAD_PCTS)
            d = per_unit_delta(rows_by_den[den][y], t, o)
            per_year_n[str(y)] = int(len(d))
            frames.append(d)
        pooled = pd.concat(frames, ignore_index=True)
        vec = weighted_quantiles(
            pooled["delta"].to_numpy(), pooled["w"].to_numpy(), QUANTILE_GRID
        )
        result["arms"][name] = {
            "conditioner": cond,
            "denominator": den,
            "n_gen_windows": int(len(pooled)),
            "per_year_n": per_year_n,
            "quantiles": {f"p{int(p*100)}": round(float(vec[idx[p]]), 4) for p in REPORT_AT},
            "full_vector": [round(float(x), 6) for x in vec],
        }

    # Arm A must reproduce the committed artifact.
    if ART.exists():
        ref = np.asarray(
            json.loads(ART.read_text())["pooled"]["quantiles_mmbtu_per_mwh"], float
        )
        got = np.asarray(result["arms"]["A_month_cond_month_den"]["full_vector"], float)
        if ref.size == got.size:
            result["A_reproduction_max_abs_err"] = round(
                float(np.abs(ref - got).max()), 6
            )
            result["A_reproduces_committed_artifact"] = bool(
                result["A_reproduction_max_abs_err"] < 1e-4
            )

    print(f"\n{'arm':<26} {'n':>6}  " + "  ".join(f"{'p'+str(int(p*100)):>9}" for p in REPORT_AT))
    for name, a in result["arms"].items():
        q = a["quantiles"]
        print(
            f"{name:<26} {a['n_gen_windows']:>6}  "
            + "  ".join(f"{q['p'+str(int(p*100))]:>9.3f}" for p in REPORT_AT)
        )
    if "A_reproduces_committed_artifact" in result:
        print(
            f"\nARM A reproduces the committed artifact: "
            f"{result['A_reproduces_committed_artifact']} "
            f"(max abs err {result['A_reproduction_max_abs_err']})"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
