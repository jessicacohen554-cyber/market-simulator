"""ERCOT-111 — why the model runs coal the real ERCOT market left idle.

ERCOT-110 gave the coal fleet its MEASURED 60-Day DAM availability and the coal
over-run got BIGGER (64.0 -> 72.3 TWh against 62.3 actual): the statistical
derate had been silently substituting for missing coal-side economics
(``results/calibration/FINDING-ercot110-coal-dam-availability-2026-07-24.md``).
This probe answers the successor question — WHICH channel the over-run runs
through — by decomposing it against the real fleet's own measured envelope,
hour by hour, with no LP.

Three envelopes are rebuilt per hour from the 60-Day DAM Gen_Resource
disclosure (``Resource Type == CLLIG``), each a sum over the 26 registered
ERCOT coal resources:

* ``live``   — HSL of every non-``OUT`` resource: the fleet's measured physical
  capability (the quantity the ERCOT-110 overlay redistributes onto the LP);
* ``onhsl``  — HSL of every committed (``ON`` / ``ONTEST`` / ``ONOS``) resource:
  what the real market had synchronized and could have dispatched;
* ``onlsl``  — LSL of the same committed set: the real min-load floor.

The model's coal (``COAL_PRB`` + ``COAL_LIGNITE`` P1 class hourlies) minus
EIA-930's measured ERCOT coal then splits into three mutually exclusive parts:

  a) **above measured capability** — ``max(0, model - live)``: the model
     dispatching coal the fleet did not physically have;
  b) **on uncommitted capacity** — the part between ``onhsl`` and ``live``: the
     model running units the real market had OFF (the commitment channel a coal
     analogue of the ERCOT-63 gas bridge would address);
  c) **economic, inside the committed envelope** — everything else: the model
     riding coal further up its own committed LSL->HSL range than the real
     market did.

Because the model's coal ``pmax`` basis (EIA-860 capacity) and the disclosure's
rating basis (p98 HSL) differ by a fixed ~2.6 %, the measured envelopes are
scaled by ``model_pmax / dam_rating`` before differencing, so the basis gap is
not charged to any channel. Pass ``--no-rating-scale`` to see the unscaled split.

Also emitted: the two fleets' **revealed supply curves** — coal MW binned by
price, each side against its OWN price — which is where the model's coal is
shown to be about twice as price-elastic as the real fleet's.

Finding at 2023 on the ercot110 probe bundle: 99 % of the +11.7 TWh over-run is
channel (c). Capping the model at the measured LIVE envelope removes 0.01 TWh
and capping it at the measured COMMITTED envelope removes 0.17 TWh — so neither
a capability ceiling nor a commitment bridge can close it, and the residual is
an OFFER-LEVEL error on the coal econ ramp.

No LP. Reads the bundle's committed hourly sidecars + the 60-Day DAM disclosure
+ the EIA-930 ERCOT hourly extract + the committed zonal actual-price archive.

Usage:
    python -m scripts.probes.ercot111_coal_dispatch_econ <bundle> [<bundle> ...]
        [--year 2023] [--no-rating-scale] [--json OUT.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

# The DAM disclosure's coal resource type (coal + lignite steam).
COAL_RESOURCE_TYPE = "CLLIG"
# Statuses that mean "synchronized and dispatchable this hour". OFF is startable
# but uncommitted, OUT is unavailable; neither counts as committed capability.
COMMITTED_STATUSES = ("ON", "ONTEST", "ONOS")
# Model classes carrying coal. NOTE the ERCOT LP assigns the whole coal fleet
# plant_group == "COAL"; the PRB/lignite split exists only at reporting time
# (run_calibration_full._dispatch_frame via coal_supply_class), which is the
# grain the class hourlies are written at.
COAL_CLASSES = ("COAL_PRB", "COAL_LIGNITE")

PRICE_BINS = [-np.inf, 0, 10, 15, 20, 25, 30, 40, 60, 100, 200, np.inf]
PRICE_LABELS = [
    "<0", "0-10", "10-15", "15-20", "20-25", "25-30",
    "30-40", "40-60", "60-100", "100-200", ">200",
]


def _dam_envelopes(year: int) -> pd.DataFrame:
    """Per-hour measured coal ``live`` / ``onhsl`` / ``onlsl`` MW + fleet rating.

    Reads every 60-Day DAM Gen_Resource file whose delivery date falls in
    ``year``, keeps the CLLIG rows, and sums the three envelopes per
    (delivery date, hour ending). Hours the disclosure does not cover (the
    Oct/Dec-2023 publication holes) are absent from the index, so the caller
    scores on covered hours only rather than imputing a capability.
    """
    frames = []
    cols = [
        "Delivery Date", "Hour Ending", "Resource Name", "Resource Type",
        "HSL", "LSL", "Resource Status",
    ]
    pattern = f"*60d_DAM_Gen_Resource_Data_{year}_*.parquet"
    paths = sorted((REPO / "data" / "raw" / "ercot").glob(pattern))
    if not paths:
        raise SystemExit(f"no 60-Day DAM Gen_Resource files for {year}")
    for path in paths:
        df = pd.read_parquet(path, columns=cols)
        df = df[
            df["Resource Type"].astype(str).str.upper().str.strip()
            == COAL_RESOURCE_TYPE
        ]
        frames.append(df)
    dam = pd.concat(frames, ignore_index=True)

    # Fleet rating: each resource's 98th-percentile HSL over its non-OUT,
    # non-zero rows (robust to jack-bus zeros and one-off test values) — the
    # same construction the ERCOT-110 availability derive uses.
    live_rows = dam[(dam["Resource Status"] != "OUT") & (dam["HSL"] > 0)]
    rating = float(live_rows.groupby("Resource Name")["HSL"].quantile(0.98).sum())

    committed = dam["Resource Status"].isin(COMMITTED_STATUSES)
    dam = dam.assign(
        live=np.where(dam["Resource Status"] == "OUT", 0.0, dam["HSL"]),
        onhsl=np.where(committed, dam["HSL"], 0.0),
        onlsl=np.where(committed, dam["LSL"], 0.0),
    )
    hourly = (
        dam.groupby(["Delivery Date", "Hour Ending"])[["live", "onhsl", "onlsl"]]
        .sum()
        .reset_index()
    )
    ts = pd.to_datetime(hourly["Delivery Date"]) + pd.to_timedelta(
        hourly["Hour Ending"].astype(int) - 1, unit="h"
    )
    # DST fall-back repeats an hour ending; average the duplicate rather than
    # dropping one, so the envelope stays a fleet mean for that clock hour.
    out = hourly.assign(ts=ts).groupby("ts")[["live", "onhsl", "onlsl"]].mean()
    out.attrs["rating"] = rating
    return out


def _model_coal(bundle: Path, year: int) -> np.ndarray:
    """P1 model coal MW per hour (8760) from the bundle's class hourlies."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        raise SystemExit(f"{bundle.name}: no class_hourly_{year}.parquet sidecar")
    ch = pd.read_parquet(path)
    ch = ch[(ch["pass"] == "P1") & ch["klass"].isin(COAL_CLASSES)]
    return ch.groupby("hour")["mw"].sum().reindex(range(8760)).to_numpy(float)


def _model_price(bundle: Path, year: int) -> np.ndarray:
    """Demand-weighted model system price per hour (the RTSPP analogue)."""
    sy = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sy = sy[sy["pass"] == "P1"]
    price = sy.pivot(index="hour", columns="zone", values="price")
    demand = sy.pivot(index="hour", columns="zone", values="demand")
    num = (price * demand).sum(axis=1)
    den = demand.sum(axis=1).replace(0, np.nan)
    return (num / den).reindex(range(8760)).to_numpy(float)


def _model_pmax(bundle: Path) -> float | None:
    """Model coal nameplate MW, for the rating-basis scale (None if absent).

    Read from the bundle when a future meta writer records it; otherwise the
    caller supplies it with ``--model-coal-pmax`` (the ERCOT 2023 fleet build
    reports 13,964 MW) and the envelopes go unscaled without it.
    """
    meta = bundle / "meta.json"
    if not meta.exists():
        return None
    value = json.loads(meta.read_text()).get("coal_pmax_mw")
    return None if value is None else float(value)


def _actuals(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(EIA-930 measured ERCOT coal MW, actual RT settlement price) per hour."""
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    bench = load_eia_hourly_benchmark("ERCOT", year)
    if bench is None or "coal" not in bench:
        raise SystemExit(f"no EIA-930 hourly coal benchmark for ERCOT {year}")
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    rt = (
        lmp[lmp["year"] == year]
        .set_index("hour")["rt"]
        .reindex(range(8760))
        .to_numpy(float)
    )
    return np.asarray(bench["coal"], float), rt


def _decompose(frame: pd.DataFrame) -> pd.DataFrame:
    """Split model-minus-actual coal into the three envelope channels."""
    excess = frame["model"] - frame["act"]
    above_live = np.maximum(0.0, frame["model"] - frame["live"])
    uncommitted = np.maximum(
        0.0, np.minimum(frame["model"], frame["live"]) - frame["onhsl"]
    )
    return frame.assign(
        excess=excess,
        a_above_live=above_live,
        b_uncommitted=uncommitted,
        c_economic=excess - above_live - uncommitted,
    )


def _report(name: str, frame: pd.DataFrame, hours: int) -> dict:
    """Print one bundle's decomposition + revealed supply curve; return its JSON."""
    scale = 8760.0 / hours / 1e6  # covered-hour mean MW -> annualised TWh

    def twh(series) -> float:
        return float(series.sum()) * scale

    print(f"\n=== {name} — coal over-run decomposition ({hours} covered hours) ===")
    print("  annualised TWh on covered hours")
    print(f"    actual                                       {twh(frame['act']):6.2f}")
    print(
        f"    model                                        {twh(frame['model']):6.2f}"
        f"   ({twh(frame['model']) - twh(frame['act']):+.2f})"
    )
    capped_live = np.minimum(frame["model"], frame["live"])
    capped_com = np.minimum(frame["model"], frame["onhsl"])
    print(
        f"    model capped at measured LIVE capability     {twh(capped_live):6.2f}"
        f"   ({twh(capped_live) - twh(frame['act']):+.2f})"
    )
    print(
        f"    model capped at measured COMMITTED envelope  {twh(capped_com):6.2f}"
        f"   ({twh(capped_com) - twh(frame['act']):+.2f})"
    )

    total = float(frame["excess"].mean())
    print("\n  excess decomposition (mean MW over covered hours)")
    print(f"    total excess                    {total:+8.0f} MW")
    channels = {
        "a) above measured capability": "a_above_live",
        "b) on uncommitted capacity  ": "b_uncommitted",
        "c) economic, inside commit  ": "c_economic",
    }
    shares: dict[str, float] = {}
    for label, col in channels.items():
        mw = float(frame[col].mean())
        pct = 100.0 * mw / total if total else float("nan")
        shares[col] = mw
        print(f"    {label}    {mw:+8.0f} MW   ({pct:4.0f} %)")

    binned = frame.assign(bin=pd.cut(frame["p_act"], PRICE_BINS, labels=PRICE_LABELS))
    table = binned.groupby("bin", observed=False).agg(
        n=("act", "size"),
        act=("act", "mean"),
        model=("model", "mean"),
        live=("live", "mean"),
        onhsl=("onhsl", "mean"),
        onlsl=("onlsl", "mean"),
        excess=("excess", "mean"),
        c_economic=("c_economic", "mean"),
    )
    print("\n  by ACTUAL price bin ($/MWh) — MW, and each fleet vs its own envelope")
    print("    bin          n    actual   model     live   onHSL   onLSL"
          "   excess   act/live  mdl/live")
    for label, row in table.iterrows():
        if not row["n"]:
            continue
        print(
            f"    {label:<9} {int(row['n']):5d}  {row['act']:7.0f} {row['model']:7.0f}"
            f"  {row['live']:7.0f} {row['onhsl']:7.0f} {row['onlsl']:7.0f}"
            f"  {row['excess']:+7.0f}     {row['act'] / row['live']:6.3f}"
            f"    {row['model'] / row['live']:6.3f}"
        )

    print("\n  revealed supply curve — coal MW binned by EACH side's OWN price")
    own_act = frame.assign(bin=pd.cut(frame["p_act"], PRICE_BINS, labels=PRICE_LABELS))
    own_mod = frame.assign(bin=pd.cut(frame["p_mod"], PRICE_BINS, labels=PRICE_LABELS))
    a = own_act.groupby("bin", observed=False)["act"].agg(["size", "mean"])
    m = own_mod.groupby("bin", observed=False)["model"].agg(["size", "mean"])
    print("    bin           n_act   act MW    n_mdl   model MW")
    for label in PRICE_LABELS:
        if not a.loc[label, "size"] and not m.loc[label, "size"]:
            continue
        print(
            f"    {label:<9} {int(a.loc[label, 'size']):8d} {a.loc[label, 'mean']:8.0f}"
            f" {int(m.loc[label, 'size']):8d} {m.loc[label, 'mean']:10.0f}"
        )

    return {
        "bundle": name,
        "covered_hours": hours,
        "twh": {
            "actual": twh(frame["act"]),
            "model": twh(frame["model"]),
            "model_capped_live": twh(capped_live),
            "model_capped_committed": twh(capped_com),
        },
        "excess_mean_mw": total,
        "channels_mean_mw": shares,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ercot111_coal_dispatch_econ")
    ap.add_argument("bundles", nargs="+", help="calibration bundle director(ies)")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument(
        "--model-coal-pmax",
        type=float,
        default=None,
        help="model coal nameplate MW, used to put the measured envelopes on "
        "the model's capacity basis when the bundle meta does not record it "
        "(ERCOT 2023 fleet build: 13964). Without it the envelopes are "
        "UNSCALED and the ~2.6%% EIA-860-vs-p98-HSL rating gap lands in "
        "channel (a).",
    )
    ap.add_argument(
        "--no-rating-scale",
        action="store_true",
        help="do not scale the measured envelopes onto the model's capacity "
        "basis (shows the raw EIA-860-vs-p98-HSL rating gap in channel a)",
    )
    ap.add_argument("--json", default=None, help="write the summary to a JSON file")
    args = ap.parse_args(argv)

    env = _dam_envelopes(args.year)
    rating = env.attrs["rating"]
    act, p_act = _actuals(args.year)
    index = pd.date_range(f"{args.year}-01-01", periods=8760, freq="h")
    env = env.reindex(index)

    print(
        f"ERCOT-111 coal dispatch economics — {args.year}\n"
        f"  60-Day DAM coal fleet rating (sum of per-resource p98 HSL): "
        f"{rating:,.0f} MW"
    )

    out = []
    for raw in args.bundles:
        bundle = Path(raw)
        model = _model_coal(bundle, args.year)
        pmax = _model_pmax(bundle) or args.model_coal_pmax
        scale = 1.0
        if not args.no_rating_scale and pmax:
            scale = float(pmax) / rating
        elif not args.no_rating_scale:
            print(
                f"  NOTE {bundle.name}: no coal pmax available (meta has none "
                "and --model-coal-pmax not given) — envelopes UNSCALED, so the "
                "capacity-basis gap lands in channel (a)"
            )
        frame = pd.DataFrame(
            {
                "act": act,
                "model": model,
                "p_act": p_act,
                "p_mod": _model_price(bundle, args.year),
                "live": env["live"].to_numpy() * scale,
                "onhsl": env["onhsl"].to_numpy() * scale,
                "onlsl": env["onlsl"].to_numpy() * scale,
            },
            index=index,
        ).dropna(subset=["live", "act", "model", "p_act"])
        if scale != 1.0:
            print(f"  measured envelopes scaled x{scale:.4f} onto {bundle.name}'s "
                  f"coal pmax {pmax:,.0f} MW")
        out.append(_report(bundle.name, _decompose(frame), len(frame)))

    print(
        "\nCAVEATS: (1) the DAM disclosure covers ~75 % of 2023 hours (Oct/Dec "
        "publication holes); every number above is on covered hours only, "
        "annualised, never imputed. (2) EIA-930 coal is BA-net generation and "
        "the model dispatches its EIA-860 capacity basis — the ~2.6 % rating "
        "gap is removed by the envelope scale, not charged to a channel. "
        "(3) commitment state is a market OUTCOME, so the committed envelope is "
        "a DIAGNOSTIC bound here, never an input (rule 13)."
    )
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
