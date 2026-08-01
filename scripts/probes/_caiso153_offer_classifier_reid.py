"""caiso-153 — re-identify the CAISO offer surface's gas-coupling classifier.

No LP in the diagnosis stage. ``FINDING-caiso152`` §I opened this as a
BLOCKING charter: the measured CAISO offer surface
(``caiso_offer_curve_measured.json`` + ``caiso_offer_surface_condbinned.json``,
armed in keeper ``2026-07-31-caiso-151-firm-selfsched``) cannot be re-derived
under the corrected RLE parse because its classifier no longer reconstitutes
the CT bucket: G1 reports a CT bucket ratio of 0.235 (old parse) / 0.280 (new)
against a ``>= 0.50`` bound, and the committed artifact — recorded at ratio
1.416 with 102 CT units — is not reproducible from its own documented script
and corpus.

The classifier identifies gas resources by regressing each masked resource's
daily body bid on the CA-composite citygate daily series; the regression SLOPE
is read as the resource's marginal heat rate (MMBtu/MWh) and the class split
is a cut on that slope. Two facts frame the diagnosis:

* caiso-152's measured lead — 71 resources / 16,329 MW clear ``r >= 0.6`` but
  land at slope **< 4 MMBtu/MWh**, which is physically impossible for a
  thermal unit. A slope that low with a correlation that high is the signature
  of an **attenuated** estimate, not of a non-gas resource.
* the population moves the way attenuation predicts: against the committed
  artifact's 55 CC / 102 CT, the current code path finds 102 CC / 25 CT — the
  whole slope distribution sits LOW, so CT-heat-rate units fall below the 8.5
  cut into CC and the tail falls out of the ``[4, 18]`` gate entirely.

Two candidate causes are testable and are tested here TOGETHER, because
either alone would attenuate the slope:

* **the body-price probe** (caiso-152's lead): ``_price_at_frac`` reads a
  SINGLE step at 35 % of a p98-estimated capacity. If that step is the
  min-load / self-commitment block rather than the SRMC body, the measured
  price responds to gas only partially.
* **the estimator**: the regressor's variance is dominated by a handful of
  extreme days. The CA-composite citygate reaches **$24.29/MMBtu** in January
  2023 against a 2023-25 median near $3-4, so a pooled OLS slope is levered on
  one month of one year. Any resource whose bid did not track that spike
  proportionally — a different CA hub, a monthly index, a cost-verified
  default energy bid on a lagged index — regresses to an attenuated slope
  with a HIGH correlation, which is exactly the reported signature.

Estimator grid (frozen ex ante, PREREG §4)
-------------------------------------------
Body probe x slope estimator, 3 x 3, the incumbent being ``P035`` x ``OLS``:

* ``P035`` — price of the step at 0.35 x cap (the incumbent ``BODY_FRAC``).
* ``BAND`` — capacity-weighted mean step price over [0.35, 0.85] x cap: the
  INTEGRATED body, insensitive to where any single breakpoint happens to sit.
* ``P060`` — price of the step at 0.60 x cap, the middle of the dispatchable
  range above a typical CC min-load block.

* ``OLS``  — ordinary least squares on every gas day (the incumbent).
* ``TS``   — Theil-Sen median-of-pairwise-slopes: resistant to both extreme
  regressor days and outlying bid days.
* ``TRIM`` — OLS restricted to days at or below the resource's own p95 gas
  price, removing the extreme-leverage tail.

Selection (frozen ex ante, PREREG §5) — blind to G1 and to the committed
artifact, so nothing here can be fitted to a gate or to a target value:

1. **Admissibility, applied first — the physical level identity.** A
   cost-based gas bid satisfies ``body ~ HR x gas + VOM + CO2_FACTOR x HR x
   P_carbon``, so the implied non-fuel adder
   ``L = median_days(body - slope x (gas + CO2_FACTOR x P_carbon))``
   must land near VOM ($2.0-3.5/MWh). An estimator is ADMISSIBLE iff its
   capacity-weighted median ``|L|`` over gas-passing resources is
   ``<= $20/MWh`` — a 5x margin over VOM for start amortization and conduct
   adders, which still excludes the ~$50 non-fuel adder an attenuated slope
   must invent to reproduce the observed bid level.
2. **Rank the admissible estimators by out-of-sample slope stability.** Each
   resource's gas days are split by ALTERNATING GAS RANK (sort by gas price,
   even index -> half A, odd -> half B) so both halves span the same regressor
   range and the test measures the estimator, not the split. The metric is the
   capacity-weighted median ``|slope_A - slope_B|`` in MMBtu/MWh. Lowest wins.
3. **If NO estimator is admissible, the classifier is NOT re-identified** —
   file and stop (``FINDING-caiso152`` §I's third branch). Shrinking every
   slope toward zero would win criterion 2 outright; criterion 1 is what makes
   that impossible, and it is applied first for exactly that reason.

``hr_cut`` stays FROZEN at 8.5 MMBtu/MWh and G1-G4 stay frozen (rule 23
``[R-FROZEN-DERIVE]``; ``FINDING-caiso152`` §H). If the re-identified slope
density puts its antimode elsewhere, that is REPORTED, never acted on here —
G2 exists to fail in that case, and moving the cut is a separate owner-visible
act, not a rescue.

Re-derivation is licensed because the SOURCE DATA changed, not because a
residual moved: caiso-152 corrected the ``dam-public-bids`` grain from one row
per RLE range to the declared one row per resource x operating hour.

Usage::

    python scripts/probes/_caiso153_offer_classifier_reid.py curate --year 2023
    python scripts/probes/_caiso153_offer_classifier_reid.py diagnose
    python scripts/probes/_caiso153_offer_classifier_reid.py derive --estimator BAND_TS
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CLASSES = ("CC_REGULAR", "CT_PEAKER")
CONSUMED_BANDS = ("econ_low", "econ_high", "peak")

#: Body probes (PREREG §4 axis A). BAND integrates the step function over the
#: dispatchable window instead of reading one step.
BODY_PROBES = ("P035", "BAND", "P060")
BAND_WINDOW = (0.35, 0.85)
#: Slope estimators (PREREG §4 axis B).
SLOPE_ESTIMATORS = ("OLS", "TS", "TRIM")
#: Admissibility bar on the implied non-fuel adder |L| ($/MWh), PREREG §5.1.
LEVEL_ADDER_MAX = 20.0
#: Trim quantile for the TRIM estimator (per-resource, on its own gas days).
TRIM_Q = 0.95

DEFAULT_OUT = REPO / "results" / "calibration" / "caiso153_classifier_reid.json"


def _clean_root(args: argparse.Namespace) -> Path:
    return Path(args.clean_root) / "clean_caiso153"


# --------------------------------------------------------------------------- #
# curate — the corrected (HEAD) parser into this probe's own clean tree
# --------------------------------------------------------------------------- #
def cmd_curate(args: argparse.Namespace) -> int:
    """Curate ONE year into the probe's clean tree.

    One year per invocation: the RLE-expanded corpus OOMs a 16 GB box when
    all three years are curated in a single process (caiso-152).
    """
    from market_sim.config import paths

    from scripts.data import curate_dam_public_bids as curate

    root = _clean_root(args)
    root.mkdir(parents=True, exist_ok=True)
    paths.CLEAN_DIR = root

    written = curate.curate(isos=["CAISO"], years=[args.year])
    print(f"year={args.year}: {len(written)} clean file(s) under {root}")
    return 0


# --------------------------------------------------------------------------- #
# the estimator grid
# --------------------------------------------------------------------------- #
def _body_daily(bids, probe: str, D):
    """Per (resource, local day) median body price, for one body probe.

    Returns a compact frame — one row per resource-day, not per resource-hour
    — so the 50M-row corpus never has more than one probe's hourly series
    alive at a time.
    """

    if probe == "P035":
        s = D._price_at_frac(bids, 0.35)
    elif probe == "P060":
        s = D._price_at_frac(bids, 0.60)
    elif probe == "BAND":
        s = D._band_price(bids, *BAND_WINDOW)
    else:  # pragma: no cover — guarded by argparse choices
        raise ValueError(probe)

    body = s.rename("p_body").reset_index()
    day = body.interval_start_utc.dt.tz_convert("US/Pacific").dt.normalize()
    body["day"] = day.dt.tz_localize(None)
    out = body.groupby(["resource_seq", "day"], as_index=False).p_body.median()
    del body, s
    return out


def _fit(x, y, estimator: str):
    """(slope, intercept) for one resource under one slope estimator."""
    import numpy as np

    if estimator == "OLS":
        slope, intercept = np.polyfit(x, y, 1)
        return float(slope), float(intercept)
    if estimator == "TRIM":
        keep = x <= np.quantile(x, TRIM_Q)
        if keep.sum() < 3 or np.std(x[keep]) < 1e-9:
            return float("nan"), float("nan")
        slope, intercept = np.polyfit(x[keep], y[keep], 1)
        return float(slope), float(intercept)
    if estimator == "TS":
        from scipy.stats import theilslopes

        slope, intercept, _, _ = theilslopes(y, x)
        return float(slope), float(intercept)
    raise ValueError(estimator)  # pragma: no cover


def _score_resources(daily, gas_plus_carbon, cap, D, estimator: str):
    """Per-resource slope / r / level-adder / split-half slopes.

    ``gas_plus_carbon`` maps day -> ``gas + CO2_FACTOR * P_carbon``: the
    physical basis the slope multiplies, so the implied non-fuel adder ``L``
    is directly comparable with VOM.
    """
    import numpy as np
    import pandas as pd

    rows = []
    for rid, g in daily.groupby("resource_seq", sort=False):
        n = len(g)
        if n < D.GAS_MIN_DAYS or g.gas.std() < 0.5:
            continue
        x = g.gas.to_numpy(float)
        y = g.p_body.to_numpy(float)
        slope, intercept = _fit(x, y, estimator)
        if not np.isfinite(slope):
            continue
        r = float(np.corrcoef(x, y)[0, 1])

        # implied non-fuel adder against the FULL physical basis (fuel+carbon)
        basis = g.day.map(gas_plus_carbon).to_numpy(float)
        level = float(np.median(y - slope * basis))

        # split-half by alternating gas rank: both halves span the same range
        order = np.argsort(x)
        ia, ib = order[0::2], order[1::2]
        sa, _ = _fit(x[ia], y[ia], estimator)
        sb, _ = _fit(x[ib], y[ib], estimator)

        rows.append(
            {
                "resource_seq": rid,
                "slope": slope,
                "intercept": intercept,
                "r": r,
                "n_days": n,
                "level_adder": level,
                "slope_a": sa,
                "slope_b": sb,
            }
        )
    res = pd.DataFrame(rows).set_index("resource_seq")
    res["cap"] = cap
    res["is_gas"] = res.slope.between(*D.GAS_SLOPE_RANGE) & (res.r >= D.GAS_MIN_R)
    return res


def cmd_diagnose(args: argparse.Namespace) -> int:
    """Score the 3x3 estimator grid and apply the frozen selection rule."""
    import numpy as np
    import pandas as pd

    from market_sim.config import paths

    paths.CLEAN_DIR = _clean_root(args)

    from scripts.data import derive_caiso_offer_surface as D

    years = list(args.years)
    geom = D._fleet_geometry()
    gas = D._gas_staircase()
    carbon = {y: D._carbon_price(y) for y in years}

    print("loading clean dam-public-bids ...", flush=True)
    bids = D._load_bids(years)
    cap_ry = bids.groupby(["resource_seq", "year"]).segment_mw.quantile(0.98)
    bids = bids.join(cap_ry.rename("cap"), on=["resource_seq", "year"])
    bids = bids[bids.cap >= D.MIN_CAP_MW]
    cap = bids.groupby("resource_seq").cap.first()
    min_mw = bids.groupby("resource_seq").segment_mw.min()
    print(f"  {len(bids):,} rows, {bids.resource_seq.nunique()} resources", flush=True)

    # day -> gas, and day -> gas + CO2_FACTOR * P_carbon (the physical basis)
    day_year = pd.Series(gas.index.year, index=gas.index)
    basis = gas + D.CO2_FACTOR * day_year.map(carbon).astype(float)

    grid: dict[str, dict] = {}
    per_resource: dict[str, pd.DataFrame] = {}
    for probe in BODY_PROBES:
        print(f"\n=== body probe {probe} ===", flush=True)
        bd = _body_daily(bids, probe, D)
        bd["gas"] = bd.day.map(gas)
        bd = bd.dropna(subset=["gas"])
        for est in SLOPE_ESTIMATORS:
            name = f"{probe}_{est}"
            res = _score_resources(bd, basis, cap, D, est)
            res["min_mw"] = min_mw
            res = res[res.min_mw >= -1.0]
            gl = res[res.is_gas]
            w = gl.cap.to_numpy(float)

            if len(gl) == 0:
                rec = {"admissible": False, "note": "no resource passes the gas gate"}
            else:
                lvl = float(
                    D._wquantile(np.abs(gl.level_adder.to_numpy(float)), w, 0.5)
                )
                ok = np.isfinite(gl.slope_a) & np.isfinite(gl.slope_b)
                half = gl[ok]
                stab = (
                    float(
                        D._wquantile(
                            np.abs(
                                half.slope_a.to_numpy(float)
                                - half.slope_b.to_numpy(float)
                            ),
                            half.cap.to_numpy(float),
                            0.5,
                        )
                    )
                    if len(half)
                    else float("nan")
                )
                rec = {
                    "level_adder_cwmed_abs": round(lvl, 2),
                    "admissible": bool(lvl <= LEVEL_ADDER_MAX),
                    "splithalf_slope_cwmed_abs_dev": round(stab, 3),
                    "n_gas_pass": int(len(gl)),
                    "gas_pass_mw": round(float(gl.cap.sum()), 0),
                    "slope_p25_p50_p75": [
                        round(float(np.percentile(gl.slope, q)), 2)
                        for q in (25, 50, 75)
                    ],
                    # reported for context, NEVER a selection input (PREREG §5)
                    "_context_bucket_mw": {
                        "CC_REGULAR": round(float(gl[gl.slope < 8.5].cap.sum()), 0),
                        "CT_PEAKER": round(float(gl[gl.slope >= 8.5].cap.sum()), 0),
                    },
                    "_context_below_gate_slope_lt4": {
                        "n": int(((res.r >= D.GAS_MIN_R) & (res.slope < 4.0)).sum()),
                        "mw": round(
                            float(
                                res[
                                    (res.r >= D.GAS_MIN_R) & (res.slope < 4.0)
                                ].cap.sum()
                            ),
                            0,
                        ),
                    },
                }
            grid[name] = rec
            per_resource[name] = res
            print(f"{name}: {json.dumps(rec)}", flush=True)
        del bd

    # ---- the frozen selection rule (PREREG §5) --------------------------- #
    admissible = {
        k: v
        for k, v in grid.items()
        if v.get("admissible")
        and np.isfinite(v.get("splithalf_slope_cwmed_abs_dev", np.nan))
    }
    if admissible:
        winner = min(
            admissible, key=lambda k: admissible[k]["splithalf_slope_cwmed_abs_dev"]
        )
        verdict = "RE-IDENTIFIED"
    else:
        winner = None
        verdict = "NOT_RE-IDENTIFIED"

    rec = {
        "years": years,
        "fleet_mw": {cls: round(geom[cls]["fleet_mw"], 0) for cls in CLASSES},
        "selection_rule": {
            "admissibility": f"cap-weighted median |level adder| <= ${LEVEL_ADDER_MAX}/MWh",
            "ranking": "cap-weighted median |slope_A - slope_B| (alternating gas rank)",
            "hr_cut": "FROZEN 8.5",
        },
        "grid": grid,
        "incumbent": "P035_OLS",
        "winner": winner,
        "verdict": verdict,
    }
    Path(args.out).write_text(json.dumps(rec, indent=1) + "\n")
    print(f"\nVERDICT {verdict} winner={winner}\n-> {args.out}")

    csv = Path(args.out).with_name("caiso153_classifier_slopes.csv")
    frames = []
    for name, df in per_resource.items():
        frames.append(df.assign(estimator=name).reset_index())
    pd.concat(frames, ignore_index=True).to_csv(csv, index=False)
    print(f"-> {csv}")
    return 0


# --------------------------------------------------------------------------- #
# derive — run the FROZEN deriver with one estimator's classifier
# --------------------------------------------------------------------------- #
def _patched_classify(estimator: str, D):
    """A ``_classify`` replacement that swaps ONLY the identification.

    Every consumed statistic, band window, ladder construction and gate is the
    deriver's own, untouched: this changes how a resource's marginal heat rate
    is measured, not what is done with it.
    """
    import numpy as np
    import pandas as pd

    probe, est = estimator.split("_", 1)

    def _classify(seg, gas, hr_cut):
        carbon = {int(y): D._carbon_price(int(y)) for y in seg.year.unique()}
        day_year = pd.Series(gas.index.year, index=gas.index)
        basis = gas + D.CO2_FACTOR * day_year.map(carbon).astype(float)

        daily = _body_daily(seg, probe, D)
        daily["gas"] = daily.day.map(gas)
        daily = daily.dropna(subset=["gas"])

        cap = seg.groupby("resource_seq").cap.first()
        min_mw = seg.groupby("resource_seq").segment_mw.min()
        res = _score_resources(daily, basis, cap, D, est)
        res["min_mw"] = min_mw
        res["is_gas"] = res.is_gas & (res.min_mw >= -1.0)
        res["cls"] = np.where(res.slope < hr_cut, "CC_REGULAR", "CT_PEAKER")
        res.loc[~res.is_gas, "cls"] = ""
        return res, daily

    return _classify


def cmd_derive(args: argparse.Namespace) -> int:
    """Re-derive the offer surface with one estimator; capture the report."""
    import ast
    import contextlib
    import io
    import re

    from market_sim.config import paths

    paths.CLEAN_DIR = _clean_root(args)

    from scripts.data import derive_caiso_offer_surface as D

    out = Path(args.out_root) / f"caiso153_{args.estimator}"
    out.mkdir(parents=True, exist_ok=True)
    D.OUT_STATIC = out / "caiso_offer_curve_measured.json"
    D.OUT_COND = out / "caiso_offer_surface_condbinned.json"
    D.OUT_CSV = out / "caiso_offer_surface_summary.csv"
    if args.estimator != "P035_OLS":
        D._classify = _patched_classify(args.estimator, D)

    class _Tee(io.TextIOBase):
        def __init__(self, real):
            self._real = real
            self.buf = io.StringIO()

        def write(self, s):  # noqa: D102
            self.buf.write(s)
            return self._real.write(s)

        def flush(self):  # noqa: D102
            self._real.flush()

    tee = _Tee(sys.stdout)
    argv = ["--years", *[str(y) for y in args.years], "--allow-gate-failures"]
    with contextlib.redirect_stdout(tee):
        rc = D.main(argv)
    log = tee.buf.getvalue()

    report: dict = {
        "estimator": args.estimator,
        "years": list(args.years),
        "derive_rc": int(rc),
    }
    m = re.search(
        r"([\d,]+) curve rows -> ([\d,]+) rows at cap .*?, (\d+) resources", log
    )
    if m:
        report["curve_rows"] = int(m.group(1).replace(",", ""))
        report["resources"] = int(m.group(3))
    m = re.search(r"^G1 (\{.*\})$", log, re.M)
    if m:
        report["G1"] = json.loads(m.group(1))
    report["static_bands"] = {
        cls: ast.literal_eval(v)
        for cls, v in re.findall(r"^(\w+): static bands (\{.*\})$", log, re.M)
    }
    report["ladder_body_p50"] = {
        cls: float(v)
        for cls, v in re.findall(r"^(\w+): ladder body_p50 ([\d.]+)$", log, re.M)
    }
    report["gates_all_pass"] = "GATES ALL PASS" in log
    report["consumed_jsons_written"] = D.OUT_STATIC.exists()
    (out / "derive_report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"estimator={args.estimator}: rc={rc} -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out-root", default=str(REPO / "results" / "calibration"))
    common.add_argument("--out", default=str(DEFAULT_OUT))
    common.add_argument("--clean-root", default=str(REPO / "results" / "calibration"))
    common.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("curate", parents=[common])
    p.add_argument("--year", type=int, required=True)
    sub.add_parser("diagnose", parents=[common])
    p = sub.add_parser("derive", parents=[common])
    p.add_argument(
        "--estimator",
        required=True,
        choices=[f"{b}_{e}" for b in BODY_PROBES for e in SLOPE_ESTIMATORS],
    )
    args = ap.parse_args(argv)
    return {"curate": cmd_curate, "diagnose": cmd_diagnose, "derive": cmd_derive}[
        args.cmd
    ](args)


if __name__ == "__main__":
    sys.exit(main())
