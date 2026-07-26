"""ERCOT-113 Task A step 2: measure the SUMMER merit-order spread that drives
the coal/gas displacement candidate (c).

Step 1 (``scripts/probes/ercot113_summer_coal_decomp.py``) refuted candidates
(a) and (b) and confirmed (c): the measured DAM coal envelope is already pinned
into the model (``ercot_thermal_dam_availability_coal`` + ``_hourly`` +
``_plant``), the summer over-run is a **utilization** gap of +13 to +20 pp
against that same envelope, and ``corr(dCoal, dGas)`` is -0.95 to -0.98 by
month. So coal is being ranked ahead of gas in summer inside a correct
envelope.

This probe measures the ranking itself, with **no LP solve**: it reuses the
ERCOT-99 capture technique (monkeypatch ``run_energy_solve``, intercept the
fully-built fleet and ``mc_base``/``mc_bid_adjust``, abort before the solve) and
reports the deliverable-weighted marginal cost of the coal fleet against the
gas CC fleet, by month.

The quantity of interest is the **coal->CC spread** ``CC_offer - coal_offer``.
If that spread WIDENS in summer relative to the shoulder, the model is making
coal look relatively cheaper exactly when it over-runs, and the driver is the
summer fuel-price / heat-rate basis rather than anything on the coal
availability side.

Startup amortization is omitted (it needs the P0 dispatch); it only RAISES gas
offers, so the reported spread is a conservative LOWER bound on how much
cheaper coal looks.

Usage:
    python scripts/probes/ercot113_summer_merit_basis.py --year 2024
    python scripts/probes/ercot113_summer_merit_basis.py --all-years
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

SUMMER = (6, 7, 8, 9)
_DEFAULT_BUNDLE = "results/calibration/ercot112_coal_marginal_hr_fullspan"


class _StopAfterCapture(BaseException):
    """Abort the run after the fleet build is captured (dodges except Exception)."""


def _month_of_hour(hours: int) -> np.ndarray:
    """Month index (1-12) for each model hour (non-leap 8760 clock)."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])[:hours]


def _capture(bundle: Path, year: int) -> dict:
    """Drive the bundle's fleet build for one year; capture the P1 offer inputs."""
    import replay_keeper  # noqa: E402  (adds scripts to path, pins warmstart)
    import run_calibration_full as rcf  # noqa: E402

    rc_mod = sys.modules[rcf.run_year.__module__]
    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = replay_keeper.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(REPO / "scratch" / "ercot113_capture_junk")
    kwargs["note"] = "ERCOT-113 merit-basis capture (aborts before solve)"

    grabbed: dict = {}
    real = rc_mod.run_energy_solve

    def _patched(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kw):
        grabbed["fleet"] = fleet
        grabbed["fa"] = fleet_arrays
        grabbed["mc_base"] = np.asarray(mc_base)
        adj = kw.get("mc_bid_adjust")
        grabbed["mc_bid_adjust"] = None if adj is None else np.asarray(adj)
        raise _StopAfterCapture()

    rc_mod.run_energy_solve = _patched
    try:
        rcf.solve_and_persist(**kwargs)
    except _StopAfterCapture:
        pass
    finally:
        rc_mod.run_energy_solve = real
    return grabbed


def month_table(bundle: Path, year: int) -> pd.DataFrame:
    """Deliverable-weighted monthly offer by class, plus the coal->CC spread."""
    g = _capture(bundle, year)
    fleet, fa = g["fleet"], g["fa"]
    mc = g["mc_base"]
    adj = g["mc_bid_adjust"]
    if adj is not None:
        mc = mc + adj
    avail = np.asarray(fa.availability, float)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], mc.shape)
    pmax = np.asarray(fa.pmax, float)
    deliverable = pmax[:, None] * avail  # (n_gen, T)

    cls = np.array(
        [(getattr(x, "plant_group", None) or "?") for x in fleet], dtype=object
    )
    is_coal = np.array([str(c).upper().startswith("COAL") for c in cls])
    is_cc = np.array([str(c).upper().startswith("CC_") for c in cls])

    mo = _month_of_hour(mc.shape[1])
    rows = []
    for m in range(1, 13):
        sel = mo == m

        def _w(mask: np.ndarray) -> tuple[float, float]:
            """Deliverable-weighted mean offer and mean deliverable MW."""
            if not mask.any():
                return np.nan, np.nan
            o = mc[mask][:, sel]
            d = deliverable[mask][:, sel]
            tot = d.sum()
            return (float((o * d).sum() / tot) if tot > 0 else np.nan,
                    float(d.sum(axis=0).mean()))

        coal_o, coal_d = _w(is_coal)
        cc_o, cc_d = _w(is_cc)
        rows.append({
            "month": m,
            "coal_offer": coal_o,
            "cc_offer": cc_o,
            "spread": cc_o - coal_o,
            "coal_deliv_mw": coal_d,
            "cc_deliv_mw": cc_d,
        })
    return pd.DataFrame(rows).set_index("month")


def main(argv: list[str] | None = None) -> int:
    """Print the monthly coal/CC offer basis and the summer-vs-shoulder spread."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=_DEFAULT_BUNDLE)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--all-years", action="store_true")
    ap.add_argument("--out", default=None, help="optional CSV of the monthly tables")
    args = ap.parse_args(argv)

    years = (2023, 2024, 2025) if args.all_years else [args.year or 2024]
    bundle = REPO / args.bundle

    tables: dict[int, pd.DataFrame] = {}
    for y in years:
        print(f"[capture] {y} — building fleet (no solve)...", flush=True)
        tables[y] = month_table(bundle, y)

    for y, t in tables.items():
        print(f"\n=== {y} — model offer basis by month (deliverable-weighted) ===")
        print(f"{'mo':>3}{'coal $':>10}{'CC $':>10}{'spread':>10}"
              f"{'coal MW':>10}{'CC MW':>10}")
        for m, r in t.iterrows():
            print(f"{m:>3}{r['coal_offer']:10.2f}{r['cc_offer']:10.2f}"
                  f"{r['spread']:10.2f}{r['coal_deliv_mw']:10.0f}"
                  f"{r['cc_deliv_mw']:10.0f}")

    print("\n\n############ SUMMER MERIT-ORDER SPREAD ############")
    print(f"{'year':>6}{'season':>10}{'coal $':>10}{'CC $':>10}{'spread':>10}")
    for y, t in tables.items():
        for name, sel in (("shoulder", ~t.index.isin(SUMMER)),
                          ("summer", t.index.isin(SUMMER))):
            s = t[sel]
            print(f"{y:>6}{name:>10}{s['coal_offer'].mean():10.2f}"
                  f"{s['cc_offer'].mean():10.2f}{s['spread'].mean():10.2f}")
    print(f"\n{'year':>6}{'shoulder spread':>18}{'summer spread':>16}{'widening':>11}")
    for y, t in tables.items():
        sh = t[~t.index.isin(SUMMER)]["spread"].mean()
        su = t[t.index.isin(SUMMER)]["spread"].mean()
        print(f"{y:>6}{sh:18.2f}{su:16.2f}{su - sh:+11.2f}")
    print(
        "  READ: a POSITIVE widening = coal looks relatively CHEAPER against gas CC in\n"
        "  summer than in the shoulder, i.e. the model's summer fuel/heat-rate basis is\n"
        "  the driver of the confirmed displacement. A widening near zero means the\n"
        "  ranking basis is seasonally flat and the summer over-run must come from the\n"
        "  QUANTITY side (what else is on the margin in summer), not the price side."
    )

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        pd.concat({y: t for y, t in tables.items()}, names=["year"]).to_csv(out)
        print(f"\n[out] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
