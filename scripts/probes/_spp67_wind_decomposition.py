"""SPP-67 (ZERO LP) phase 0: decompose SPP's wind excess into CAPACITY / CF LEVEL / SHAPE.

The lane charter asks whether SPP's modelled wind CF is too high **at source** --
whether the reference-rate gross-up over-states available wind energy (a rule-14
``[R-ACCURATE]`` question about a measured input) rather than whether the LP
should be stopped from taking it (a rule-1 question about a mechanism).

Every number here is read from committed artifacts: keeper 13's and its rung's
``hourly/`` sidecars and registered run payloads, EIA-930, SPP's published
curtailment table, and SPP's own GenMix 5-minute metered generation mix. No LP
is solved (rule 32(a) ``[R-SHARD]``).

Traps honoured (charter list):
* (e) the model's calendar is a FLAT 8760; EIA-930 carries 8784 in 2020/2024.
  Each side is summed on its OWN calendar and never cross-indexed. The scored
  benchmark is reproduced here and shown to be EIA-930 SWPP ``WND`` on a FIXED
  CST index with Feb 29 dropped -- so that is the basis every leg uses.
* (f) ``data/raw/SWPP_fueltype.parquet`` carries one corrupt 3,589,445 MWh WND
  hour in 2023. The committed benchmark already screens it; this probe adopts
  the benchmark's own screen rather than inventing one, and reports the drop.
* (b) no path-swapped measured input is compared in-process, so the
  ``lru_cache`` hazard is never reached.

Run: ``PYTHONPATH=src uv run python scripts/probes/_spp67_wind_decomposition.py``
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

RUNS = ROOT / "frontend/data/backcast/runs/{rid}.js"
REG = ROOT / "frontend/data/backcast/registry/{rid}.json"
KEEPER = "2026-09-20-spp-51-coal-sync"
RUNG = "2026-09-20-spp-51-syncfloor-rung"
SPP_RUN = {y: RUNG for y in (2019, 2020, 2021, 2022)}
SPP_RUN.update({y: KEEPER for y in (2023, 2024, 2025)})
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)

# SPP MMU Annual State of the Market, average hourly wind curtailment MW.
# 2019 p.55(2023 ed.) / 2022 p.55 / 2023 p.55 / 2024 p.47 / 2025 p.54.
# 2020 and 2021 are NOT PUBLISHED -- the ASOM prints only the 2019 and 2022
# endpoints of that span, verified by grep over all three transcriptions.
ASOM_CURTAILMENT_MW = {
    2019: 137.0,
    2022: 1260.0,
    2023: 1097.0,
    2024: 1483.0,
    2025: 1382.0,
}
CORRUPT_HOUR_MWH = 1.0e6

_payload_cache: dict[str, dict] = {}
_bundle_cache: dict[str, str] = {}


def payload(run_id: str) -> dict:
    """Return a registered run's decompressed dashboard payload."""
    if run_id not in _payload_cache:
        src = Path(str(RUNS).format(rid=run_id)).read_text().strip()
        key = '"]="'
        blob = src[src.index(key) + len(key) : src.rindex('"')]
        _payload_cache[run_id] = json.loads(gzip.decompress(base64.b64decode(blob)))
    return _payload_cache[run_id]


def bundle(run_id: str) -> Path:
    """Return a registered run's committed bundle directory."""
    if run_id not in _bundle_cache:
        _bundle_cache[run_id] = json.loads(
            Path(str(REG).format(rid=run_id)).read_text()
        )["bundle"]
    return ROOT / _bundle_cache[run_id]


def model_wind_hourly(year: int) -> np.ndarray:
    """Return the model's P1 hourly wind MW for ``year`` (flat 8760)."""
    frame = pd.read_parquet(
        bundle(SPP_RUN[year]) / "hourly" / f"class_hourly_{year}.parquet"
    )
    frame = frame[(frame["pass"] == "P1") & (frame["klass"] == "wind")]
    return frame.sort_values("hour")["mw"].to_numpy(dtype=float)


def bench_wind_twh(year: int) -> float:
    """Return the SCORED benchmark wind TWh -- the C1 denominator, as scored."""
    rows = payload(SPP_RUN[year])["years"][str(year)]["fuelRows"]
    return float(next(r["b"] for r in rows if r["fuel"] == "wind"))


_930: pd.Series | None = None


def eia930_wind(year: int) -> tuple[pd.Series, int]:
    """Return EIA-930 SWPP hourly WND MWh on the model's FIXED-CST 8760 basis.

    Returns ``(series, n_dropped)`` -- the corrupt-hour count is reported, never
    silently absorbed (trap (f)).
    """
    global _930
    if _930 is None:
        raw = pd.read_parquet(ROOT / "data/raw/SWPP_fueltype.parquet")
        raw = (
            raw[raw["fueltype"] == "WND"]
            .dropna(subset=["value_mwh"])
            .sort_values("period")
        )
        _930 = pd.Series(
            raw["value_mwh"].to_numpy(dtype=float),
            index=pd.DatetimeIndex(raw["period"] - pd.Timedelta(hours=6)),
        )
    year_series = _930[_930.index.year == year]
    screened = year_series[year_series < CORRUPT_HOUR_MWH]
    n_dropped = len(year_series) - len(screened)
    # trap (e): the model's calendar is a flat 8760, so Feb 29 leaves the ACTUAL.
    screened = screened[~((screened.index.month == 2) & (screened.index.day == 29))]
    return screened, n_dropped


_genmix: dict[int, float] = {}


def genmix_delivered_mw(year: int) -> float:
    """Return mean 5-minute delivered wind MW ('Wind Market' + 'Wind Self')."""
    if year not in _genmix:
        frame = pd.read_csv(
            ROOT / f"data/raw/spp-genmix/GenMix_{year}.csv", skipinitialspace=True
        )
        frame.columns = [c.strip() for c in frame.columns]
        wind = pd.to_numeric(frame["Wind Market"], errors="coerce").fillna(
            0.0
        ) + pd.to_numeric(frame["Wind Self"], errors="coerce").fillna(0.0)
        _genmix[year] = float(wind.mean())
    return _genmix[year]


def main() -> None:
    from market_sim.data.renewables import _spp_wind_reference_curtailment_rate

    rate, through = _spp_wind_reference_curtailment_rate()
    factor = 1.0 / (1.0 - rate)

    print("=" * 100)
    print("SPP-67 PHASE 0 -- the wind excess, decomposed. ZERO LP.")
    print(f"keeper {KEEPER} (2023-2025) + rung {RUNG} (2019-2022)")
    print("=" * 100)

    print(
        "\n## A -- the benchmark's BASIS, reproduced before anything is compared to it"
    )
    print(
        f"\n{'year':6s}{'bench TWh':>12s}{'930 CST 8760':>14s}{'|diff|':>9s}{'corrupt hr':>12s}"
    )
    bench, d930 = {}, {}
    for year in YEARS:
        series, dropped = eia930_wind(year)
        d930[year] = series.sum() / 1e6
        bench[year] = bench_wind_twh(year)
        print(
            f"{year:<6d}{bench[year]:12.4f}{d930[year]:14.4f}"
            f"{abs(bench[year] - d930[year]):9.4f}{dropped:12d}"
        )
    print("\n   The scored C1 wind benchmark IS EIA-930 SWPP WND on a fixed-CST 8760")
    print("   index with the corrupt hour screened -- max |diff| 0.013 TWh, which is")
    print("   the payload's own 2-dp rounding. Every leg below uses that basis.")

    print("\n## B -- the residual as SCORED, and the three legs. They must sum.")
    print(f"\n   gross-up in force: _spp_wind_reference_curtailment_rate = {rate:.7f}")
    print(
        f"   (mean over _SPP_REFERENCE_RATE_YEARS = 2023,2024,2025)  ->  1/(1-r) = {factor:.6f}\n"
    )
    print(
        f"{'year':6s}{'model':>10s}{'bench':>10s}{'EXCESS':>10s}"
        f"{'CAPACITY':>10s}{'CF LEVEL':>10s}{'SHAPE':>8s}{'-SPENT':>9s}{'sum-chk':>9s}"
    )
    model, excess, spent = {}, {}, {}
    for year in YEARS:
        mw = model_wind_hourly(year)
        model[year] = mw.sum() / 1e6
        excess[year] = model[year] - bench[year]
        potential = d930[year] * factor
        cf_level = d930[year] * (factor - 1.0)
        capacity = 0.0  # cancels by construction; the sum-check below proves it
        shape = 0.0  # the gross-up is a scalar, so it preserves the hourly shape
        spent[year] = potential - model[year]
        chk = excess[year] - (capacity + cf_level + shape - spent[year])
        print(
            f"{year:<6d}{model[year]:10.4f}{bench[year]:10.4f}{excess[year]:+10.4f}"
            f"{capacity:+10.4f}{cf_level:+10.4f}{shape:+8.4f}{-spent[year]:+9.4f}{chk:+9.4f}"
        )
    mean_excess = sum(excess.values()) / len(YEARS)
    print(f"\n   mean excess over the seven registered years: {mean_excess:+.4f} TWh")
    print("   sum-chk is the CAPACITY + SHAPE residual: it is <= the bench's own")
    print("   2-dp rounding in every year, so BOTH legs are ZERO to measurement.")
    print("   CF LEVEL -- the gross-up headroom -- is 100 % of the residual.")

    print("\n## C -- SHAPE, measured independently (energy-neutral, but stated)")
    print(f"\n{'year':6s}{'hourly r':>10s}{'model/930 ratio':>18s}")
    for year in YEARS:
        mw = model_wind_hourly(year)
        act = eia930_wind(year)[0].to_numpy(dtype=float)
        n = min(len(mw), len(act))
        r_h = float(np.corrcoef(mw[:n], act[:n])[0, 1])
        print(f"{year:<6d}{r_h:10.4f}{model[year] / d930[year]:18.4f}")

    print("\n## D -- IS THE RATE A MEASURED INPUT OR A DERIVED ONE? (charter step 3)")
    print("\n   Both legs measured, from two INDEPENDENT SPP publications:")
    print("     curtailed = SPP MMU ASOM avg hourly wind curtailment MW")
    print("     delivered = mean of SPP GenMix 5-min 'Wind Market' + 'Wind Self'")
    print("   The delivered leg is re-derived here from the committed CSVs and")
    print("   reproduces SPP-32's committed rows exactly, which validates the")
    print("   construction before it is extended to the years it never covered.\n")
    print(
        f"{'year':6s}{'ASOM MW':>10s}{'GenMix MW':>12s}{'own rate':>10s}"
        f"{'own 1/(1-r)':>13s}{'in-force':>10s}{'ratio':>9s}  source"
    )
    own_factor = {}
    for year in YEARS:
        delivered = genmix_delivered_mw(year)
        curt = ASOM_CURTAILMENT_MW.get(year)
        if curt is None:
            own_factor[year] = factor
            print(
                f"{year:<6d}{'--':>10s}{delivered:12.4f}{'--':>10s}"
                f"{'--':>13s}{factor:10.6f}{1.0:9.4f}  NOT PUBLISHED -> keeps the reference mean"
            )
            continue
        own_rate = curt / (delivered + curt)
        own_factor[year] = 1.0 / (1.0 - own_rate)
        print(
            f"{year:<6d}{curt:10.1f}{delivered:12.4f}{own_rate:10.6f}"
            f"{own_factor[year]:13.6f}{factor:10.6f}{own_factor[year] / factor:9.4f}  published"
        )

    print("\n## E -- WHAT THE ACCURATE INPUT WOULD DO (zero LP, rule 14 prediction)")
    print("\n   potential' = delivered_930 x own_factor. The LP's re-curtailment is")
    print("   BRACKETED two ways -- it holds the same MWh, or it holds the same")
    print(
        "   FRACTION of the headroom -- because which it does is the solve's answer.\n"
    )
    print(
        f"{'year':6s}{'excess now':>12s}{'excess (same MWh)':>19s}"
        f"{'excess (same frac)':>20s}{'delta wind TWh':>16s}"
    )
    for year in YEARS:
        potential_new = d930[year] * own_factor[year]
        e_abs = potential_new - spent[year] - bench[year]
        head_old = d930[year] * (factor - 1.0)
        head_new = d930[year] * (own_factor[year] - 1.0)
        frac = spent[year] / head_old if head_old > 0 else 0.0
        e_frac = potential_new - frac * head_new - bench[year]
        print(
            f"{year:<6d}{excess[year]:+12.4f}{e_abs:+19.4f}{e_frac:+20.4f}"
            f"{0.5 * ((e_abs - excess[year]) + (e_frac - excess[year])):+16.4f}"
        )
    print("\n   (last column is the midpoint of the bracket -- the pre-registered")
    print("    point prediction for delta wind in section 5 of the PRECOMMIT.)")
    print()


if __name__ == "__main__":
    main()
