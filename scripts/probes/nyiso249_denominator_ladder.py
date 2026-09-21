"""nyiso-249 — IS THE SURVIVING UPPER TAIL CONDUCT, OR A DELIVERED-FUEL ARTIFACT?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Gates **G-1** (re-derivation) and **G-2**
(the discriminator).

nyiso-248 G-5 corrected the P-27 book's tight-minus-ordinary implied offer heat
rate from ``+2.035 / +11.928 / +27.880`` (p50/p75/p90) to
``-0.123 / +4.685 / +21.974`` by swapping the 12-value MONTHLY STEP out of BOTH
roles it occupied (the conditioner and the implied-heat-rate denominator). The
median rise did not survive; **the upper tail did**, and this lane was briefed to
build a form for it.

**Before a form, one more denominator question has to be settled, and it is the
same species of question nyiso-248 answered.** The implied heat rate is

    m = bid bottom block ($/MWh) / G(hour) ($/MMBtu)

and ``G`` is a *choice of denominator*. nyiso-248 moved it from a monthly step to
the daily **HUB** (Transco Z6 NY). But a NYISO generator does not buy gas at the
hub: it pays a **delivered** price — hub commodity plus that zone's LDC delivery
charge — and the LDC charge is not constant across states of the system. If a
unit bids ``HR x P_delivered`` while this estimator divides by ``P_hub``, then

    m = HR x (P_delivered / P_hub)

and **any widening of the delivered-over-hub basis in tight hours manufactures a
positive tight-minus-ordinary delta from a unit whose true heat rate never
moved** — exactly the artifact shape nyiso-248 found twice already.

This matters because **the model already prices part of that basis**. The keeper
arms ``nyiso_downstate_ct_gas_daily``, which SETS every NYC / Long Island
``CT_PEAKER`` to the measured per-zone delivered index (Transco Z6 NY daily spot
+ the measured LDC non-firm transport rate). If the measured upper tail is that
same delivered basis, it is a mechanism this ISO **already has**, and adding an
offer-dispersion form on top of it is the rule 19 ``[R-ONE-MECH]`` stack that
rule forbids.

**THE LADDER.** The conditioner is held at nyiso-248's corrected DAILY coordinate
throughout, so the arms differ in **exactly one thing**: the denominator.

    A   monthly step   (= the committed artifact; REPRODUCTION CHECK ONLY)
    D   daily hub      (= nyiso-248's corrected arm D; the brief's baseline)
    E   the model's own cap-weighted DELIVERED gas for the price-setting rungs
        (CC_REGULAR + ST_GAS), read out of the keeper's own assembled
        ``fuel_prices`` -- i.e. what those units are actually charged in the LP
    F   the measured NYC LDC DELIVERED index -- the identical series
        ``apply_nyiso_downstate_ct_gas_daily`` already SETS on downstate
        CT_PEAKER, so an arm-F collapse names a mechanism that is ARMED

**PRE-REGISTERED READING (fixed here, before the numbers).**

* Tail SURVIVES under BOTH E and F  -> not a fuel artifact; the object is
  conduct and a form is warranted.
* Tail COLLAPSES under F but survives under E -> the object is the missing
  LDC delivered basis on the classes that set price. That is a rule 14
  ``[R-ACCURATE]`` measured-INPUT question, **not** an offer-dispersion
  mechanism, and the lane routes it as one rather than building a form.
* Tail COLLAPSES under E -> already armed. Report and stop (rule 19).

"Collapses" is fixed as **p90 falling below +8.0 MMBtu/MWh**, a third of the
corrected +21.974 -- chosen as a round fraction before any arm was run, never
swept.

Everything runs the family's OWN estimator (``year_unit_rows``,
``per_unit_delta``, ``weighted_quantiles``, the frozen 199-point
``QUANTILE_GRID``, the registered ``NETLOAD_PCTS`` ladder) with only the gas
array swapped, because re-implementing the population rules would itself be a
tuning channel -- the derive's own docstring forbids it.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso249_denominator_ladder.py
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
OUT = REPO / "results" / "calibration" / "_nyiso249_denominator_ladder.json"
REPORT_AT = (0.10, 0.25, 0.50, 0.75, 0.90, 0.99)

#: p90 bar below which the tail is declared COLLAPSED. Fixed ex ante (docstring).
COLLAPSE_P90 = 8.0

#: The price-setting rungs. CC_REGULAR + ST_GAS are the 16.4 GW that set a
#: NYISO price (nyiso-248 section 3); CT_PEAKER is excluded from arm E precisely
#: because it is the class that ALREADY carries the delivered index, so
#: including it would blend the armed and unarmed halves.
PRICE_SETTING = ("CC_REGULAR", "ST_GAS")


def delivered_price_setting(year: int) -> np.ndarray:
    """Cap-weighted delivered gas ($/MMBtu) for CC_REGULAR + ST_GAS, ``(8760,)``.

    Read straight out of the keeper's own assembled ``fuel_prices`` in the
    fleet cache -- the array the LP charges those rows, after every armed basis
    and dual-fuel applier has run. No new statistic is formed: this is the
    capacity-weighted mean over the rows of the two classes, the same weighting
    the offer book uses over units.
    """
    d = np.load(CACHE / f"{year}.npz", allow_pickle=True)
    pg = d["plant_group"].astype(str)
    fp = np.asarray(d["fuel_prices"], dtype=float)
    pm = np.asarray(d["pmax"], dtype=float)
    m = np.isin(pg, PRICE_SETTING)
    if not m.any():
        raise SystemExit(f"no {PRICE_SETTING} rows for {year}")
    w = pm[m]
    w = w / w.sum()
    return (fp[m] * w[:, None]).sum(axis=0)


def delivered_ldc_nyc(year: int) -> np.ndarray | None:
    """The measured NYC LDC delivered index ($/MMBtu), ``(8760,)``.

    Exactly the series ``apply_nyiso_downstate_ct_gas_daily`` SETS on downstate
    CT_PEAKER: measured Transco Z6 NY daily spot + the measured monthly KEDNY
    SC-22 non-firm transport rate. Returns ``None`` if the curated series is
    not present, so the arm is reported as unavailable rather than guessed.
    """
    from market_sim.data.fuel.basis.nyiso import (
        _downstate_delivered_gas_hourly_by_zone,
    )

    by_zone = _downstate_delivered_gas_hourly_by_zone("NYISO", year, 8760)
    if not by_zone or "NYC" not in by_zone:
        return None
    return np.asarray(by_zone["NYC"], dtype=float)


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
    from scripts.probes.nyiso248_book_daily_regrain import daily_gas, windows

    years = args.year or list(YEARS)
    nl = net_load_by_year()

    series: dict[str, dict[int, np.ndarray]] = {
        "monthly": {y: np.asarray(gas_series_by_year()[y], float) for y in years},
        "daily_hub": {y: daily_gas(y) for y in years},
        "delivered_ccst": {y: delivered_price_setting(y) for y in years},
    }
    ldc = {y: delivered_ldc_nyc(y) for y in years}
    if all(v is not None for v in ldc.values()):
        series["delivered_ldc_nyc"] = {y: ldc[y] for y in years}

    # Level census, so a denominator swap can never be read as a level claim.
    census = {
        name: {
            str(y): {
                "mean": round(float(s[y].mean()), 4),
                "p50": round(float(np.median(s[y])), 4),
                "p99": round(float(np.quantile(s[y], 0.99)), 4),
                "max": round(float(s[y].max()), 4),
                "distinct": int(np.unique(np.round(s[y], 6)).size),
            }
            for y in years
        }
        for name, s in series.items()
    }

    # Rows depend ONLY on the denominator -- build each once, reuse across arms.
    rows_by_den = {
        name: {y: year_unit_rows(y, s[y]) for y in years} for name, s in series.items()
    }

    arms: dict[str, tuple[str, str]] = {
        "A_month_cond_month_den": ("monthly", "monthly"),
        "D_daily_cond_hub_den": ("daily_hub", "daily_hub"),
        "E_daily_cond_delivered_ccst_den": ("daily_hub", "delivered_ccst"),
    }
    if "delivered_ldc_nyc" in series:
        arms["F_daily_cond_delivered_ldc_den"] = ("daily_hub", "delivered_ldc_nyc")

    idx = {p: int(np.argmin(np.abs(QUANTILE_GRID - p))) for p in REPORT_AT}
    result: dict = {
        "gate": "G-1/G-2",
        "session": "nyiso-249",
        "years": years,
        "collapse_bar_p90": COLLAPSE_P90,
        "denominator_level_census": census,
        "arms": {},
    }

    for name, (cond, den) in arms.items():
        frames, per_year_n, per_year_q = [], {}, {}
        for y in years:
            t, o = windows(series[cond][y], nl[y], NETLOAD_PCTS)
            d = per_unit_delta(rows_by_den[den][y], t, o)
            per_year_n[str(y)] = int(len(d))
            if len(d):
                v = weighted_quantiles(
                    d["delta"].to_numpy(), d["w"].to_numpy(), QUANTILE_GRID
                )
                per_year_q[str(y)] = {
                    f"p{int(p * 100)}": round(float(v[idx[p]]), 4) for p in REPORT_AT
                }
            frames.append(d)
        pooled = pd.concat(frames, ignore_index=True)
        vec = weighted_quantiles(
            pooled["delta"].to_numpy(), pooled["w"].to_numpy(), QUANTILE_GRID
        )
        q = {f"p{int(p * 100)}": round(float(vec[idx[p]]), 4) for p in REPORT_AT}
        result["arms"][name] = {
            "conditioner": cond,
            "denominator": den,
            "n_gen_windows": int(len(pooled)),
            "per_year_n": per_year_n,
            "per_year_quantiles": per_year_q,
            "quantiles": q,
            "tail_collapsed": bool(q["p90"] < COLLAPSE_P90),
            "full_vector": [round(float(x), 6) for x in vec],
        }

    if ART.exists():
        ref = np.asarray(
            json.loads(ART.read_text())["pooled"]["quantiles_mmbtu_per_mwh"], float
        )
        got = np.asarray(result["arms"]["A_month_cond_month_den"]["full_vector"], float)
        if ref.size == got.size:
            err = float(np.abs(ref - got).max())
            result["A_reproduction_max_abs_err"] = round(err, 6)
            result["A_reproduces_committed_artifact"] = bool(err < 1e-4)

    hdr = "  ".join(f"{'p' + str(int(p * 100)):>9}" for p in REPORT_AT)
    print(f"\n{'arm':<34} {'n':>6}  {hdr}   collapsed")
    for name, a in result["arms"].items():
        q = a["quantiles"]
        row = "  ".join(f"{q['p' + str(int(p * 100))]:>9.3f}" for p in REPORT_AT)
        print(f"{name:<34} {a['n_gen_windows']:>6}  {row}   {a['tail_collapsed']}")
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
