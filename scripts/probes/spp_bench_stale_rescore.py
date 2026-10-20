"""Zero-LP effect of the stale-snapshot repair on the SPP scoring benchmark (R27).

Lane UC-SPP-BENCH. Three outputs, none of which solves an LP:

1. **Benchmark effect**: per year, the annual TWh of every
   ``load_eia_hourly_benchmark("SPP", y)`` series BEFORE (the repair as
   identity) and AFTER (:func:`market_sim.data.stale_snapshot.repair_eia930_frame`).
2. **Provenance**: every repaired (hour, EIA-930 column), run-length encoded
   as ``(column, source, first hour, last hour, interval-end UTC span)``.
3. **Re-score** (``--after-bench DIR``): the SPP bundles' determination before
   and after, from committed artifacts. "Before" is the run's committed
   payload and bench parts (``calibration_verdict.load_artifacts``). "After"
   swaps in the bench parts a re-render writes under the repair (``DIR`` =
   a ``frontend/data/backcast/bench/SPP`` copy) and recomputes the payload's
   ``fuelRows`` from the bundle's committed ``hourly/class_hourly_<y>`` and
   ``hourly/unit_marginal_<y>`` (the renderer's mixed-plant OTHER_FOSSIL
   re-bucket applied to the model side). The recompute reproduces every
   committed keeper fuelRow exactly on the unrepaired benchmark, which the
   probe asserts before scoring.

Run::

    PYTHONPATH=.:src uv run python scripts/probes/spp_bench_stale_rescore.py \\
        --out <json> [--provenance <csv>] [--after-bench <dir> --run-id <id> ...]
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.data import stale_snapshot as ss  # noqa: E402
from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402
from market_sim.data.fleet import eia860  # noqa: E402

YEARS = tuple(range(2019, 2026))
FUELS = ("gas", "coal", "nuclear", "wind", "solar")


@contextmanager
def _unrepaired():
    """Run with the frame repair as identity (the pre-R27 benchmark)."""
    real = ss.repair_eia930_frame
    ss.repair_eia930_frame = lambda iso, year, frame: frame
    try:
        yield
    finally:
        ss.repair_eia930_frame = real


def benchmark(year: int, repaired: bool) -> dict[str, np.ndarray]:
    """The SPP EIA-930 scoring benchmark for ``year``, repaired or not."""
    if repaired:
        return load_eia_hourly_benchmark("SPP", year)
    with _unrepaired():
        return load_eia_hourly_benchmark("SPP", year)


def effect_table() -> dict:
    """``{year: {series: [TWh before, TWh after, ΔGWh]}}``."""
    out = {}
    for y in YEARS:
        b, a = benchmark(y, False), benchmark(y, True)
        out[y] = {
            k: [
                round(float(b[k].sum()) / 1e6, 4),
                round(float(a[k].sum()) / 1e6, 4),
                round(float(a[k].sum() - b[k].sum()) / 1e3, 1),
            ]
            for k in a
        }
    return out


def provenance_runs() -> pd.DataFrame:
    """Run-length-encoded :func:`stale_snapshot.benchmark_stale_provenance`."""
    rows = []
    for y in YEARS:
        prov = ss.benchmark_stale_provenance("SPP", y)
        for (column, source), g in prov.groupby(["column", "source"], sort=True):
            hours = g["hour"].to_numpy()
            stamps = g["interval_end_utc"].to_numpy()
            breaks = np.flatnonzero(np.diff(hours) != 1) + 1
            for idx in np.split(np.arange(hours.size), breaks):
                rows.append(
                    {
                        "year": y,
                        "column": column,
                        "source": source,
                        "first_hour": int(hours[idx[0]]),
                        "last_hour": int(hours[idx[-1]]),
                        "n_hours": int(idx.size),
                        "first_interval_end_utc": pd.Timestamp(stamps[idx[0]]),
                        "last_interval_end_utc": pd.Timestamp(stamps[idx[-1]]),
                    }
                )
    return pd.DataFrame(rows)


def model_fuel_rows(bundle: Path, year: int, bench: dict, cfull: dict) -> list[dict]:
    """Payload ``fuelRows`` for gas/coal/nuclear/wind/solar from committed sidecars.

    Mirrors ``render_calibration_html.build_payload``: model = grid LP class
    hourly (mixed plants' gas-thermal dispatch re-bucketed to OTHER_FOSSIL,
    ``eia860.apply_other_fossil_scoring``), actual = the EIA-930 series, gas
    deflated by the flat geothermal+biomass fold-in.
    """
    from scripts import render_calibration_html as r

    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == sorted(ch["pass"].unique())[-1]]
    mh = {
        k: g.sort_values("hour")["mw"].to_numpy(float)
        for k, g in ch.groupby("klass", observed=True)
    }
    mixed = eia860._pkg_ns().mixed_fossil_plants(year)
    um = pd.read_parquet(
        bundle / "hourly" / f"unit_marginal_{year}.parquet",
        columns=["pass", "plant_code", "plant_group", "hour", "mw"],
    )
    um = um[
        (um["pass"] == sorted(um["pass"].unique())[-1])
        & um["plant_code"].isin(mixed)
        & um["plant_group"].isin(eia860._GAS_THERMAL_SCORING_CLASSES)
    ]
    for klass, g in um.groupby("plant_group", observed=True):
        hourly = g.groupby("hour")["mw"].sum().reindex(range(HOURS_PER_YEAR))
        mh[klass] = mh[klass] - hourly.fillna(0.0).to_numpy(float)
    rows = []
    zero = np.zeros(HOURS_PER_YEAR)
    for fuel in FUELS:
        ms = sum((mh.get(c, zero) for c in r.classes_for_fuel930(fuel)), zero)
        ob = bench.get(fuel)
        if fuel == "gas" and ob is not None and "other" in bench:
            fold = max(
                0.0,
                float(cfull.get("OTHER", 0.0))
                + float(cfull.get("biomass", 0.0))
                - float(bench["other"].sum()) / 1e6,
            )
            ob = ob - fold * 1e6 / HOURS_PER_YEAR
        rows.append(
            {
                "fuel": fuel,
                "m": round(float(ms.sum()) / 1e6, 2),
                "b": round(float(ob.sum()) / 1e6, 2) if ob is not None else None,
                "r": round(r._pearson(ms, ob), 3)
                if ob is not None and ob.std() > 0
                else None,
                "nrmse": round(r._nrmse(ms, ob), 3) if ob is not None else None,
            }
        )
    return rows


def _bench_parts(directory: Path) -> dict[int, dict]:
    out = {}
    for path in sorted(directory.glob("*.json.gz")):
        obj = json.loads(gzip.decompress(path.read_bytes()))
        for y in obj["meta"]["years"]:
            out[int(y)] = obj["bench"]
    return out


def _flat(verdict: dict) -> dict[str, list]:
    return {
        f"{crit}|{rec.get('key')}|{rec.get('year')}": [
            rec["status"],
            rec.get("magnitude"),
        ]
        for crit, c in verdict["criteria"].items()
        for rec in c.get("records", [])
    }


def rescore(run_id: str, after_bench: Path) -> dict:
    """Determination before / after for one registered SPP run."""
    from scripts import calibration_verdict as cv

    before = cv.load_artifacts(run_id)
    bundle = REPO / before["sidecar"]["bundle"]
    after = copy.deepcopy(before)
    after["bench"] = _bench_parts(after_bench)
    for y in YEARS:
        committed = before["payload"]["years"][str(y)]["fuelRows"]
        check = {
            x["fuel"]: x
            for x in model_fuel_rows(
                bundle, y, benchmark(y, False), before["bench"][y]["classFull"]
            )
        }
        for row in committed:
            if row["fuel"] in check and check[row["fuel"]] != row:
                raise SystemExit(
                    f"{run_id} {y} {row['fuel']}: recompute {check[row['fuel']]} "
                    f"does not reproduce the committed fuelRow {row}"
                )
        new = {
            x["fuel"]: x
            for x in model_fuel_rows(
                bundle, y, benchmark(y, True), after["bench"][y]["classFull"]
            )
        }
        after["payload"]["years"][str(y)]["fuelRows"] = [
            new.get(x["fuel"], x) for x in committed
        ]
    vb = cv.determine_from_artifacts(run_id, before)
    va = cv.determine_from_artifacts(run_id, after)
    fb, fa = _flat(vb), _flat(va)
    return {
        "determination": [vb["determination"], va["determination"]],
        "changed": {k: [fb.get(k), fa.get(k)] for k in sorted(set(fb) | set(fa))
                    if fb.get(k) != fa.get(k)},
        "status_changed": sorted(
            k for k in set(fb) | set(fa)
            if (fb.get(k) or [None])[0] != (fa.get(k) or [None])[0]
        ),
    }


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--provenance", type=Path)
    ap.add_argument("--after-bench", type=Path)
    ap.add_argument("--run-id", nargs="*", default=[])
    args = ap.parse_args()
    result: dict = {"effect": effect_table()}
    for y, row in result["effect"].items():
        print(y, " ".join(f"{k} {v[2]:+.0f}" for k, v in row.items()), "GWh")
    if args.provenance:
        runs = provenance_runs()
        runs.to_csv(args.provenance, index=False)
        print(f"wrote {args.provenance} ({len(runs)} runs)")
    if args.after_bench:
        result["rescore"] = {rid: rescore(rid, args.after_bench) for rid in args.run_id}
        for rid, res in result["rescore"].items():
            print(rid, "determination", " -> ".join(res["determination"]),
                  "| status changes:", res["status_changed"] or "none")
    args.out.write_text(json.dumps(result, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
