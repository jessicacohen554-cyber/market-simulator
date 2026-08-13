#!/usr/bin/env python
"""Identify the ERCOT screen residual scarcity-rent function ``R_f(tau)``.

The identification half of lane L-SCAR (option L-1), chartered and signed at
``docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md`` (S1/S2/S3, owner,
2026-08-13).  The mechanism it feeds is a default-off, ERCOT-only,
forecast/hindcast-only revenue-stack term in the capacity-evolution
retirement/entry screen:

    term_f(y) = max(0, R_f(tau_model(y)) - S_f(y))          [$ /kW-yr]

This script identifies ``R_f`` ONLY.  It runs the charter's pre-registered
**V0 identification gate** and, per the charter, it is the V0 gate -- never a
model residual -- that selects the conditioning-variable form and decides
whether the lane proceeds at all.

WHAT IS FITTED, AND AGAINST WHAT (rule 13 ``[R-MEASURED]``)
-----------------------------------------------------------
Both coordinates of every fitted point are MEASURED.  No model quantity, no
model residual and no price forecast appears anywhere in the fit:

* **y -- the rent anchor.**  The Potomac Economics ERCOT State-of-the-Market
  "Net Revenue Analysis" new-entrant CT/CC net revenue, $/kW-yr, read from the
  data contract (``som-competitive-conduct``, ISO=ERCOT).  Each vintage's value
  is the value that report states in prose for its OWN subject year.  (The SOM
  prints its multi-year history only as unlabelled bar charts, so a later
  report's history figure is NOT a transcribable source -- see
  ``data/raw/som-competitive-conduct/README.md``.)
* **x -- measured system tightness.**  Computed from ERCOT's committed
  NP6-905-CD reserve telemetry, ``data/raw/ercot/ercot_<year>_ordc_reserves_
  hourly.parquet``, using the Physical Responsive Capability (``prc``) series.

**Honesty gate, inherited from the RTOLCAP derive family:** the tightness side
reads a **MW QUANTITY only**.  ``system_lambda``, ``rtorpa``, ``rtoffpa`` and
``rtordpa`` are price columns of the same parquet and are NEVER read here.  A
price-conditioned tightness variable would make ``tau_model`` inherit the
model's own measured under-formation of the scarcity tail, so ``R_f(tau_model)``
would be evaluated at an artificially loose point and the term would silently
defeat itself; it would also move the construction toward the outcome-pinning
branch rule 13 forbids.

THE CONDITIONING VARIABLE (charter Section 2.2)
-----------------------------------------------
The charter names three candidate forms and pre-registers that the V0 gate --
"the form with the best leave-one-vintage-out reproduction of the anchors,
chosen against measured data only, never against a model run" -- selects one,
which is then FROZEN (rule 23 ``[R-FROZEN-DERIVE]``).  The candidates
implemented here are all pure reserve-quantity statistics, each design- or
distribution-grounded rather than a tuned threshold:

* ``prc_mean``   -- mean PRC over the year (the reserve-margin analogue, form i)
* ``prc_p1``     -- 1st-percentile PRC (the tail of the reserve distribution)
* ``frac_below_x``  -- fraction of hours with PRC < X (the tight-hour count,
  form iii), X the ORDC minimum contingency level
* ``depth_below_x`` -- mean ``max(0, X - PRC)`` (tight-hour count weighted by
  how far below the knee the system actually went)

``tau_model`` is the SAME statistic evaluated on the screen's own price/fleet
object, which is what makes the term regenerate forward (charter Section 2.3).

V0 -- THE PRE-REGISTERED IDENTIFICATION GATE (charter Section 3)
----------------------------------------------------------------
* **Vintage floor: >= 5 anchor vintages.**  "with only the 3 on-disk vintages
  the lane STOPS at V0 and reports -- no 3-point fit proceeds."
* **Leave-one-vintage-out:** fit ``R_f`` on N-1 vintages, predict the held-out
  vintage's anchor.
* **PASS bar: within +-25 % or +-15 $/kW-yr (whichever is LARGER), on CT and
  CC, on EVERY fold.**

A V0 failure is a finding, not something to widen a band around: the charter
routes a miss to diagnosis and forbids re-fitting against it.

Run ``python scripts/data/derive_screen_scarcity_rent.py`` for the full report,
``--emit constant`` for the paste-ready frozen-parameter block.

Rule 23 re-derive triggers (source-data changes ONLY, never a residual): a new
published SOM vintage, or a new/restated NP6-905-CD telemetry vintage.  The
first RTC+B-era SOM vintage additionally re-derives with a regime term (charter
Section 2.5).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.clean_io import read_clean  # noqa: E402

# --- Cited constants ---------------------------------------------------------

# ERCOT ORDC minimum contingency level.  Below this reserve level the ORDC's
# loss-of-load probability is administratively 1.0 and the curve prices at the
# full VOLL offset (results/scarcity.py docstring; OBDRR038).  Used here purely
# as the design-grounded threshold defining a "tight hour" -- it is NOT a fitted
# or swept value (rules 5 / 24).
ORDC_MINIMUM_CONTINGENCY_LEVEL_MW: float = 3000.0

# The charter's V0 PASS bar (Section 3, pre-registered before any fit).
V0_REL_TOL: float = 0.25
V0_ABS_TOL_USD_PER_KW_YR: float = 15.0
V0_MIN_VINTAGES: int = 5

# The identification span.  2019-2025 is the program's working span (CLAUDE.md
# rule 22: "2018 and earlier are DROPPED"); it is also exactly the span for
# which a prose-stated ERCOT SOM anchor exists (the 2018 SOM is absent from the
# Potomac document library).
ANCHOR_YEARS: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)

# The two merchant thermal classes the SOM publishes new-entrant anchors for.
ANCHOR_CLASSES: tuple[str, ...] = ("new_gas_ct", "new_gas_cc")

TELEMETRY_TEMPLATE = "data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"

# Price columns of the telemetry parquet.  Listed so the honesty gate is
# enforced in code, not merely asserted in the docstring.
_FORBIDDEN_PRICE_COLUMNS = ("system_lambda", "rtorpa", "rtoffpa", "rtordpa")


@dataclass(frozen=True)
class TightnessForm:
    """One candidate conditioning-variable form.

    Attributes:
        name: Identifier used in the report and in the frozen constant block.
        describe: One-line human description for the report.
    """

    name: str
    describe: str


TIGHTNESS_FORMS: tuple[TightnessForm, ...] = (
    TightnessForm("prc_mean", "mean Physical Responsive Capability (MW)"),
    TightnessForm("prc_p1", "1st-percentile PRC (MW)"),
    TightnessForm(
        "frac_below_x",
        "fraction of hours with PRC < X (X = ORDC minimum contingency level)",
    ),
    TightnessForm("depth_below_x", "mean max(0, X - PRC) (MW)"),
)


def measured_tightness(year: int) -> dict[str, float]:
    """Compute every candidate tightness statistic for one measured year.

    Reads the committed NP6-905-CD reserve telemetry and returns the candidate
    conditioning statistics.  Only the ``prc`` MW-quantity column is read; the
    parquet's price columns are never touched (the honesty gate).

    Args:
        year: Market year to summarise.

    Returns:
        Mapping of tightness-form name to value, plus ``n_hours`` (the number
        of telemetry hours actually present, which is < 8760 for 2025 because
        the ORDC telemetry ends at RTC+B go-live on 2025-12-05).

    Raises:
        FileNotFoundError: If the year's telemetry parquet is not committed.
    """
    path = REPO_ROOT / TELEMETRY_TEMPLATE.format(year=year)
    if not path.exists():
        raise FileNotFoundError(f"missing ERCOT ORDC reserve telemetry: {path}")
    frame = pd.read_parquet(path, columns=["prc"])
    prc = frame["prc"].to_numpy(dtype=float)
    prc = prc[np.isfinite(prc)]
    x = ORDC_MINIMUM_CONTINGENCY_LEVEL_MW
    return {
        "n_hours": float(prc.size),
        "prc_mean": float(prc.mean()),
        "prc_p1": float(np.percentile(prc, 1.0)),
        "frac_below_x": float((prc < x).mean()),
        "depth_below_x": float(np.maximum(0.0, x - prc).mean()),
    }


def _anchor_value(rows: pd.DataFrame, metric_stem: str) -> float | None:
    """Return one anchor level, averaging a published ``_min``/``_max`` range.

    The SOM states a year's net revenue either as a single number or as a
    locational range across settlement zones.  A range is reduced to its
    midpoint -- the class-level anchor the charter's ``R_f`` is defined on.

    Args:
        rows: The ``som-competitive-conduct`` rows for one (year, class).
        metric_stem: Metric name stem, e.g. ``net_revenue_usd_per_kw_yr``.

    Returns:
        The anchor in $/kW-yr, or None when this vintage publishes neither the
        single value nor a complete range.
    """
    by_metric = dict(zip(rows["metric"], rows["value"]))
    if metric_stem in by_metric:
        return float(by_metric[metric_stem])
    lo, hi = by_metric.get(f"{metric_stem}_min"), by_metric.get(f"{metric_stem}_max")
    if lo is not None and hi is not None:
        return float((float(lo) + float(hi)) / 2.0)
    return None


def load_anchors(*, ex_uri: bool = False) -> pd.DataFrame:
    """Load the measured SOM net-revenue anchors from the data contract.

    Args:
        ex_uri: When True, substitute the 2021 vintage's OWN published
            Winter-Storm-Uri counterfactual ("net revenues would have ranged
            from ... but for Winter Storm Uri") for that year's headline. Both
            are the monitor's published numbers; the sensitivity exists because
            2021's headline was earned under the then-$9,000/MWh system-wide
            offer cap, which has since been lowered to $5,000.

    Returns:
        Frame indexed by year with one column per anchor class.
    """
    som = read_clean("som-competitive-conduct", iso="ERCOT", validate=False)
    out: dict[int, dict[str, float]] = {}
    for year in ANCHOR_YEARS:
        row: dict[str, float] = {}
        for cls in ANCHOR_CLASSES:
            sel = som[(som["year"] == year) & (som["fleet_segment"] == cls)]
            if sel.empty:
                continue
            value = None
            if ex_uri:
                value = _anchor_value(sel, "net_revenue_ex_uri_usd_per_kw_yr")
            if value is None:
                value = _anchor_value(sel, "net_revenue_usd_per_kw_yr")
            if value is not None:
                row[cls] = value
        if row:
            out[year] = row
    return pd.DataFrame.from_dict(out, orient="index").sort_index()


def _fit_predict(
    tau_train: np.ndarray,
    y_train: np.ndarray,
    tau_test: float,
    *,
    log_space: bool,
) -> float:
    """Fit a one-variable rent function on N-1 vintages and predict one point.

    Args:
        tau_train: Measured tightness of the training vintages.
        y_train: Measured rent anchors of the training vintages.
        tau_test: Measured tightness of the held-out vintage.
        log_space: Fit ``log(rent)`` rather than ``rent``.  Rent is strongly
            right-skewed (two orders of magnitude across the span), so the
            log-space variant is the natural second functional form.

    Returns:
        Predicted rent for the held-out vintage, in $/kW-yr.
    """
    target = np.log(y_train) if log_space else y_train
    slope, intercept = np.polyfit(tau_train, target, 1)
    pred = slope * tau_test + intercept
    return float(np.exp(pred)) if log_space else float(pred)


def run_v0(
    anchors: pd.DataFrame, tightness: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Run the charter's pre-registered V0 leave-one-vintage-out gate.

    For every (conditioning form x functional form), fit on N-1 vintages and
    predict the held-out vintage, for each anchor class.  The gate PASSES only
    if every fold of every class lands within the pre-registered tolerance.

    Args:
        anchors: Measured rent anchors, indexed by year, one column per class.
        tightness: Measured tightness statistics, indexed by year.

    Returns:
        A ``(folds, summary)`` pair: the per-fold frame, and a summary dict
        with the best candidate and whether the gate passed.
    """
    years = [y for y in anchors.index if y in tightness.index]
    records: list[dict[str, object]] = []
    for form in TIGHTNESS_FORMS:
        for log_space in (False, True):
            for cls in ANCHOR_CLASSES:
                if cls not in anchors.columns:
                    continue
                series = anchors[cls].dropna()
                usable = [y for y in years if y in series.index]
                for held in usable:
                    train = [y for y in usable if y != held]
                    pred = _fit_predict(
                        tightness.loc[train, form.name].to_numpy(float),
                        series.loc[train].to_numpy(float),
                        float(tightness.loc[held, form.name]),
                        log_space=log_space,
                    )
                    actual = float(series.loc[held])
                    tol = max(V0_REL_TOL * actual, V0_ABS_TOL_USD_PER_KW_YR)
                    records.append(
                        {
                            "form": form.name,
                            "space": "log" if log_space else "linear",
                            "class": cls,
                            "held_out": held,
                            "actual": actual,
                            "predicted": pred,
                            "abs_err": abs(pred - actual),
                            "tol": tol,
                            "within": abs(pred - actual) <= tol,
                        }
                    )
    folds = pd.DataFrame(records)
    if folds.empty:
        return folds, {"passed": False, "reason": "no usable folds"}

    grouped = folds.groupby(["form", "space"])
    scoreboard = grouped.agg(
        folds_within=("within", "sum"),
        n_folds=("within", "size"),
        max_abs_err=("abs_err", "max"),
        median_abs_err=("abs_err", "median"),
    ).reset_index()
    scoreboard["all_within"] = scoreboard["folds_within"] == scoreboard["n_folds"]
    scoreboard = scoreboard.sort_values(
        ["folds_within", "median_abs_err"], ascending=[False, True]
    )
    best = scoreboard.iloc[0]
    return folds, {
        "passed": bool(best["all_within"]),
        "best_form": str(best["form"]),
        "best_space": str(best["space"]),
        "folds_within": int(best["folds_within"]),
        "n_folds": int(best["n_folds"]),
        "scoreboard": scoreboard,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the identification report / V0 gate.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code: 0 when V0 passes, 1 when it fails or the vintage
        floor is not met.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--ex-uri",
        action="store_true",
        help="use the 2021 SOM's own ex-Winter-Storm-Uri counterfactual anchor",
    )
    parser.add_argument("--emit", choices=["report", "constant"], default="report")
    args = parser.parse_args(argv)

    anchors = load_anchors(ex_uri=args.ex_uri)
    tight = pd.DataFrame.from_dict(
        {y: measured_tightness(y) for y in ANCHOR_YEARS}, orient="index"
    ).sort_index()

    print("=" * 78)
    print("L-SCAR / L-1  -- R_f identification, V0 gate")
    print("  anchors : Potomac ERCOT SOM Net Revenue Analysis (measured)")
    print("  tau     : NP6-905-CD PRC reserve telemetry (measured MW quantity)")
    if args.ex_uri:
        print("  variant : 2021 ex-Uri counterfactual anchor")
    print("=" * 78)
    table = tight.join(anchors)
    print(table.round(4).to_string())
    print()

    n_vintages = int(anchors.dropna(how="all").shape[0])
    print(f"anchor vintages available: {n_vintages} (floor {V0_MIN_VINTAGES})")
    if n_vintages < V0_MIN_VINTAGES:
        print("V0 STOP: vintage floor not met; no fit proceeds (charter Section 3).")
        return 1

    folds, summary = run_v0(anchors, tight)
    print()
    print("--- V0 scoreboard (folds within the pre-registered bar) ---")
    print(summary["scoreboard"].round(3).to_string(index=False))
    print()
    best_form, best_space = summary["best_form"], summary["best_space"]
    sel = folds[(folds["form"] == best_form) & (folds["space"] == best_space)]
    print(f"--- best candidate: {best_form} / {best_space} ---")
    print(sel.round(2).to_string(index=False))
    print()
    print(
        f"V0 {'PASS' if summary['passed'] else 'FAIL'}: "
        f"{summary['folds_within']}/{summary['n_folds']} folds within bar "
        f"(bar = max(+-{V0_REL_TOL:.0%}, +-${V0_ABS_TOL_USD_PER_KW_YR:.0f}/kW-yr), "
        "required on EVERY fold)"
    )
    if not summary["passed"]:
        print(
            "\nPer the charter (Section 3) a V0 miss routes to DIAGNOSIS -- never to "
            "widening the band or re-fitting R_f against the miss."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
