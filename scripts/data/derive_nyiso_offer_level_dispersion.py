"""Derive NYISO's CROSS-UNIT CONDITIONAL-LEVEL-DISPERSION vector (nyiso-246).

The measured object is the **across-unit distribution of the WITHIN-UNIT change
in offer level between a tight state and an ordinary one**::

    b_g(h)  = the unit-hour's curve BOTTOM  =  ``Dispatch $/MW1``   ($/MWh)
    beta_g,W = cap-weighted MEDIAN over h in W of b_g(h) / G(h)     (MMBtu/MWh)
    delta_g  = beta_g,TIGHT - beta_g,ORDINARY                       (MMBtu/MWh)

``delta`` is a **within-unit difference over gens present in BOTH windows**, so
unit identity, class, fuel level, market level and the ~9.4 GW fleet-scope gap
between the model's fleet and P-27's cancel **exactly**. P-27 is masked -- no
class, no fuel, no zone, no unit -- and nyiso-244 section 4 built and REFUTED the
class bridge NYISO's masking allows, so a coordinate that never asks what the
masked gen *is* is a necessity here, not a preference.

**Why a DIFFERENCE and not a level (nyiso-245's refusal, carried forward).**
nyiso-245 refused the within-unit SHAPE form on this same corpus: the market's
conditional shape response is +$0.12/MWh (+$1.03 with every price taker
excluded) against the model's +$11.34 -- the model already over-steepens by 11x
and there is no shape object to transfer. What the market does instead is
DISPERSE its level response: +$19.01 at the median, +$112.05 at p75, +$231.59 at
p90, with 112 gens / 8,774 MW / 24.3 % of declared capacity repricing by more
than $100/MWh. The model moves nearly everything by the same ~$40 and nothing by
more. This script measures that distribution.

**Rule 25 [R-ISO-SCOPE].** Reused from MISO: the method
(``derive_miso_offer_level_dispersion.py``), the population rules, the
step-function estimator and the family's frozen 199-point grid. Refused: every
MISO value. ``MISO_OFFER_SPREAD_ANCHOR_RANK`` is MISO's and is not read here.

**Rule 13 [R-MEASURED].** Every input is a submitted OFFER -- never a cleared
price, a realised dispatch, an award column or a residual. Both conditioning
coordinates (measured net load; the model's own delivered-gas series) exist in a
forecast year and respond to changed conditions; the normalization by ``G(h)``
makes ``delta`` an implied-heat-rate object that regenerates forward.

**Rule 23 [R-FROZEN-DERIVE].** The state geometry is
``docs/PRECOMMIT-nyiso246-conditional-level-dispersion-2026-09-20.md`` section
1.1, committed at ``947de8cd`` before any measurement, and is never re-tuned
against a residual.

Usage::

    PYTHONPATH=.:src python3 scripts/data/derive_nyiso_offer_level_dispersion.py
    PYTHONPATH=.:src python3 scripts/data/derive_nyiso_offer_level_dispersion.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_nyiso_offer_level_dispersion")

from scripts.data.derive_nyiso_offer_surface import (  # noqa: E402
    HOURS,
    MARKETS,
    NETLOAD_PCTS,
    YEARS,
    _MW_COLS,
    _PX_COLS,
    _SELF_COLS,
    _std_hour,
    gas_series_by_year,
    net_load_by_year,
    read_month,
)

#: Family's frozen 199-point quantile grid (miso-179 / PRECOMMIT section 1.2).
QUANTILE_GRID: np.ndarray = np.round(np.arange(0.005, 0.9951, 0.005), 4)

OUT_DEFAULT = (
    REPO / "data" / "raw" / "_validation-source" / "nyiso_offer_level_dispersion.json"
)


# --------------------------------------------------------------------------- #
# The two states (PRECOMMIT section 1.1) -- INPUT-SIDE ONLY.
# --------------------------------------------------------------------------- #
def state_windows(
    gas: dict[int, np.ndarray] | None = None,
) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray], dict]:
    """Return per-year boolean ``(tight, ordinary)`` hour masks plus metadata.

    ``gas`` is the per-year delivered-gas array the CONDITIONER bins on. It is a
    PARAMETER rather than a reach into :func:`gas_series_by_year` because that
    function returns the keeper's ``_gas_series``, which nyiso-248 G-1/G-3
    measured to be a **pure 12-value monthly step** while the array the LP prices
    gas on is DAILY. Under the monthly step ``gas_bin >= 2`` selects *an hour in
    one of the year's ~1.2 dearest MONTHS*, not a dear DAY, and the same flat
    array was also the implied-heat-rate DENOMINATOR in :func:`year_unit_rows` --
    two independent channels, each carrying about half of the reported effect
    (nyiso-248 section A2). Passing the array explicitly is what lets a caller
    move BOTH roles together; ``None`` preserves the committed artifact exactly.

    Both coordinates are binned on the registered cross-ISO percentile ladder
    ``NETLOAD_PCTS = (0.80, 0.90, 0.97)`` **within each year's own
    distribution** -- the one declared departure from nyiso-245's pooled gas
    terciles, whose measured reason is in PRECOMMIT section 1.1: 2022's MINIMUM
    delivered gas exceeds 2023's and 2024's MAXIMUM, so a pooled gas bin is a
    year selector rather than a scarcity selector.

    TIGHT     = gas_bin >= 2 AND load_bin >= 2   (both at/above the year's p90)
    ORDINARY  = gas_bin == 0 AND load_bin == 0   (both below the year's p80)
    """
    nl = net_load_by_year()
    if gas is None:
        gas = gas_series_by_year()
    tight: dict[int, np.ndarray] = {}
    ordinary: dict[int, np.ndarray] = {}
    meta: dict = {"per_year": {}}
    for year in YEARS:
        lb = np.searchsorted(
            np.quantile(nl[year], NETLOAD_PCTS), nl[year], side="right"
        )
        gb = np.searchsorted(
            np.quantile(gas[year], NETLOAD_PCTS), gas[year], side="right"
        )
        tight[year] = (gb >= 2) & (lb >= 2)
        ordinary[year] = (gb == 0) & (lb == 0)
        month = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h").month.to_numpy()
        mc = np.bincount(month[tight[year]], minlength=13)[1:]
        meta["per_year"][str(year)] = {
            "tight_hours": int(tight[year].sum()),
            "ordinary_hours": int(ordinary[year].sum()),
            "tight_month_counts": [int(x) for x in mc],
            "tight_winter_share": round(
                float(mc[[0, 1, 11]].sum() / max(1, tight[year].sum())), 4
            ),
        }
    meta["ladder"] = list(NETLOAD_PCTS)
    meta["netload_source"] = "EIA-930 NYIS Demand - NG:WND - NG:SUN, per year"
    meta["gas_source"] = "keeper's own resolved _gas_series (cached), per year"
    meta["percentile_basis"] = "WITHIN each year's own distribution, BOTH coordinates"
    return tight, ordinary, meta


def weighted_quantiles(
    values: np.ndarray, weights: np.ndarray, grid: np.ndarray
) -> np.ndarray:
    """Step-function weighted quantiles (the family's convention throughout)."""
    order = np.argsort(values, kind="stable")
    v, cum = values[order], np.cumsum(weights[order])
    cum = cum / cum[-1]
    idx = np.clip(np.searchsorted(cum, grid), 0, v.size - 1)
    return v[idx]


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Capacity-weighted median, the same step-function estimator at p = 0.5."""
    return float(weighted_quantiles(values, weights, np.array([0.5]))[0])


# --------------------------------------------------------------------------- #
# The corpus pass.
# --------------------------------------------------------------------------- #
def year_unit_rows(year: int, gas: np.ndarray) -> pd.DataFrame:
    """One row per surviving unit-hour: gen, window-agnostic bottom/G, weight.

    Population rules are the family's, adopted unchanged (a re-invented
    exclusion set is a tuning channel): ``Upper Oper Limit > 0``, not fully
    self-scheduled, hour inside the year.
    """
    frames: list[pd.DataFrame] = []
    for month in range(1, 13):
        for market in MARKETS:
            raw = read_month(year, month, market)
            if raw is None:
                continue
            uol = pd.to_numeric(raw["Upper Oper Limit"], errors="coerce").to_numpy(
                float
            )
            self_mw = (
                raw[_SELF_COLS]
                .apply(pd.to_numeric, errors="coerce")
                .fillna(0.0)
                .max(axis=1)
            ).to_numpy(float)
            ts = pd.to_datetime(
                raw["Date Time"].astype(str).str.strip(), format="%d%b%Y:%H:%M:%S"
            )
            hour = _std_hour(pd.DatetimeIndex(ts).tz_localize("UTC"), year)
            px = raw[_PX_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
            mw = raw[_MW_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
            nblocks = np.isfinite(mw).sum(axis=1)
            bottom = px[:, 0]
            keep = (
                (uol > 0.0)
                & (self_mw < uol)
                & (hour >= 0)
                & (hour < HOURS)
                & np.isfinite(bottom)
            )
            if not keep.any():
                continue
            frames.append(
                pd.DataFrame(
                    {
                        "gen": raw["Masked Gen ID"].to_numpy()[keep],
                        "hour": hour[keep],
                        "m": bottom[keep] / gas[hour[keep]],
                        "w": uol[keep],
                        "nblocks": nblocks[keep],
                    }
                )
            )
    if not frames:
        raise SystemExit(f"no P-27 rows for {year}")
    return pd.concat(frames, ignore_index=True)


def per_unit_delta(
    rows: pd.DataFrame, tight: np.ndarray, ordinary: np.ndarray
) -> pd.DataFrame:
    """Return one row per gen present in BOTH windows: ``delta``, weight, flags."""
    rows = rows.assign(
        _t=tight[rows["hour"].to_numpy()], _o=ordinary[rows["hour"].to_numpy()]
    )
    out: list[dict] = []
    for gen, grp in rows.groupby("gen", sort=False):
        t = grp[grp["_t"]]
        o = grp[grp["_o"]]
        if t.empty or o.empty:
            continue
        out.append(
            {
                "gen": gen,
                "delta": weighted_median(t["m"].to_numpy(), t["w"].to_numpy())
                - weighted_median(o["m"].to_numpy(), o["w"].to_numpy()),
                "w": float(grp["w"].mean()),
                # Multi-block = the unit submits more than one block in the
                # MEDIAN tight hour; a single-block unit is a price taker whose
                # delta can only be pulled toward zero (G3c: reported, KEPT).
                "multiblock": bool(np.median(t["nblocks"].to_numpy()) > 1),
                "tight_unit_hours": int(len(t)),
                "ordinary_unit_hours": int(len(o)),
            }
        )
    return pd.DataFrame(out)


def build(
    out_path: Path = OUT_DEFAULT,
    gas: dict[int, np.ndarray] | None = None,
    gas_label: str | None = None,
) -> dict:
    """Derive the pooled vector plus the per-year stationarity sub-vectors.

    ``gas`` enters BOTH roles -- the :func:`state_windows` conditioner and the
    :func:`year_unit_rows` implied-heat-rate denominator -- from this one place,
    so the two can never again be resolved independently (nyiso-248 section A2:
    they were, and each channel carried about half of a finding that did not
    survive their joint correction). ``None`` reproduces the committed artifact.
    """
    if gas is None:
        gas = gas_series_by_year()
    tight, ordinary, state_meta = state_windows(gas)
    if gas_label is not None:
        state_meta["gas_source"] = gas_label

    per_year: dict[int, pd.DataFrame] = {}
    for year in YEARS:
        rows = year_unit_rows(year, gas[year])
        per_year[year] = per_unit_delta(rows, tight[year], ordinary[year])
        log.info(
            "%d: %d gens in BOTH windows (tight %d h, ordinary %d h, winter share %.3f)",
            year,
            len(per_year[year]),
            state_meta["per_year"][str(year)]["tight_hours"],
            state_meta["per_year"][str(year)]["ordinary_hours"],
            state_meta["per_year"][str(year)]["tight_winter_share"],
        )

    pooled = pd.concat([per_year[y] for y in YEARS], ignore_index=True)

    def vec(df: pd.DataFrame) -> list[float]:
        if df.empty:
            return []
        return [
            round(float(x), 6)
            for x in weighted_quantiles(
                df["delta"].to_numpy(), df["w"].to_numpy(), QUANTILE_GRID
            )
        ]

    art = {
        "schema": "nyiso_offer_level_dispersion/1",
        "session": "nyiso-246",
        "precommit": (
            "docs/PRECOMMIT-nyiso246-conditional-level-dispersion-2026-09-20.md"
        ),
        "units": "MMBtu/MWh (implied offer heat rate, bottom-of-curve)",
        "corpus": "NYISO MIS P-27 genbids, DAM, 2022-2025, pooled",
        "quantile_grid": [round(float(x), 4) for x in QUANTILE_GRID],
        "state": state_meta,
        "pooled": {
            "n_gen_windows": int(len(pooled)),
            "quantiles_mmbtu_per_mwh": vec(pooled),
        },
        "pooled_multiblock_only": {
            "n_gen_windows": int(pooled["multiblock"].sum()),
            "quantiles_mmbtu_per_mwh": vec(pooled[pooled["multiblock"]]),
        },
        "per_year_stationarity_check_never_consumed": {
            str(y): {
                "n_gen_windows": int(len(per_year[y])),
                "quantiles_mmbtu_per_mwh": vec(per_year[y]),
                "multiblock_quantiles_mmbtu_per_mwh": vec(
                    per_year[y][per_year[y]["multiblock"]]
                ),
            }
            for y in YEARS
        },
        "contamination_g3c_reported_never_excluded": {
            str(y): {
                "single_block_gen_share": round(
                    float(1.0 - per_year[y]["multiblock"].mean()), 4
                ),
                "single_block_capacity_share": round(
                    float(
                        per_year[y].loc[~per_year[y]["multiblock"], "w"].sum()
                        / max(1e-9, per_year[y]["w"].sum())
                    ),
                    4,
                ),
            }
            for y in YEARS
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(art, indent=2, sort_keys=True) + "\n"
    out_path.write_text(payload)
    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    log.info("wrote %s  sha256=%s", out_path, digest)
    art["_sha256"] = digest
    return art


# --------------------------------------------------------------------------- #
# Self-test (PRECOMMIT section 1.2: T-1, T-2 LEVEL INVARIANCE, T-3).
# --------------------------------------------------------------------------- #
def self_test() -> None:
    """T-1 recovery, T-2 level invariance, T-3 an unchanged unit has delta 0."""
    tight = np.zeros(HOURS, dtype=bool)
    ordinary = np.zeros(HOURS, dtype=bool)
    tight[:10] = True
    ordinary[100:110] = True
    gas = np.full(HOURS, 5.0)

    def rows_for(bottom_t: float, bottom_o: float, shift: float = 0.0) -> pd.DataFrame:
        h = np.concatenate([np.arange(10), np.arange(100, 110)])
        b = np.concatenate(
            [np.full(10, bottom_t + shift), np.full(10, bottom_o + shift)]
        )
        return pd.DataFrame(
            {
                "gen": ["A"] * 20,
                "hour": h,
                "m": b / gas[h],
                "w": np.full(20, 100.0),
                "nblocks": np.full(20, 4),
            }
        )

    # T-1: a known answer. bottom 50 -> 100 at G = 5 is delta = 10 MMBtu/MWh.
    d = per_unit_delta(rows_for(100.0, 50.0), tight, ordinary)
    assert abs(float(d["delta"].iloc[0]) - 10.0) < 1e-9, d
    # T-2 LEVEL INVARIANCE: shifting BOTH windows by a constant changes delta by
    # exactly shift/G -- the difference removes any common LEVEL, which is what
    # makes the object immune to the ~9.4 GW fleet-scope gap.
    d2 = per_unit_delta(rows_for(100.0, 50.0, shift=25.0), tight, ordinary)
    assert abs(float(d2["delta"].iloc[0]) - 10.0) < 1e-9, d2
    # T-3: a unit whose bottom does not move between windows has delta 0.
    d3 = per_unit_delta(rows_for(70.0, 70.0), tight, ordinary)
    assert abs(float(d3["delta"].iloc[0])) < 1e-12, d3
    # Estimator: the step-function weighted quantile is the family's.
    q = weighted_quantiles(
        np.array([1.0, 2.0, 3.0]), np.array([1.0, 1.0, 1.0]), np.array([0.5])
    )
    assert abs(float(q[0]) - 2.0) < 1e-12, q
    print("SELF-TEST PASS  (T-1 recovery, T-2 level invariance, T-3 price taker)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument(
        "--gas",
        choices=("monthly", "daily"),
        default="monthly",
        help=(
            "which delivered-gas array fills BOTH roles. 'monthly' is the "
            "keeper's _gas_series and reproduces the committed artifact; "
            "'daily' is the array the LP actually prices gas on "
            "(iso_hub_daily_gas_prices, monthly-filled where uncovered), the "
            "nyiso-248 G-5 corrected coordinate."
        ),
    )
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.gas == "daily":
        from scripts.probes.nyiso248_book_daily_regrain import daily_gas

        art = build(
            args.out,
            {y: daily_gas(y) for y in YEARS},
            "iso_hub_daily_gas_prices on the keeper's own resolved config, "
            "monthly-filled where no basis row covers a month (nyiso-248 G-5 "
            "corrected coordinate), per year",
        )
    else:
        art = build(args.out)
    grid = np.asarray(art["quantile_grid"])
    for name in ("pooled", "pooled_multiblock_only"):
        v = np.asarray(art[name]["quantiles_mmbtu_per_mwh"])
        if not v.size:
            continue
        pick = [0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
        vals = "  ".join(
            f"p{int(p * 100)}={float(np.interp(p, grid, v)):.3f}" for p in pick
        )
        print(f"{name:26s} n={art[name]['n_gen_windows']:5d}  {vals}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
