"""PJM-NEXT-7 zero-LP phase 0: where the COAL_BIT surplus sits, per plant.

Reads ONLY committed artifacts of keeper ``2026-09-28-pjm-next-6-f2``
(bundle ``results/calibration/pjmnext6_sp_span``): the registered run payload
(per-plant hourly model MW), the bench (per-plant CAMPD net hourly MW, EIA-923
annual), the per-unit CAMPD extracts ``data/raw/campd-unit-level/*_<y>.parquet``
(``hydrate_data.py --profile pjm``) and the keeper's two outage extracts. No LP.

For each COAL_BIT bench plant and year it splits model - CAMPD energy into:

* ``above_synced`` -- model MWh above the net capacity of the plant's coal
  units that CAMPD shows SYNCHRONISED (opTime > 0) that hour, i.e. energy the
  model makes on capacity that was actually offline. Attributed (capacity
  share, hour by hour) to the kind of dark state of the offline units:
  ``win`` (covered by a keeper outage window), ``<24h`` / ``1-5d`` / ``5-30d`` /
  ``>30d`` (dark run length, NOT windowed), ``fullyr`` (dark all year, no
  window);
* ``within_synced`` -- the remainder: loading difference on synced capacity;
* ``unmeasurable`` -- plants whose CEMS rows carry no gross load (cogens).

Usage: ``python3 scripts/probes/_pjmnext7_coal_phase0.py [--years 2019 2021 2023]``
Record: ``docs/FINDING-pjm-next-7-coal-phase0-2026-09-28.md``.
"""

from __future__ import annotations

import argparse
import base64
import glob
import gzip
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "2026-09-28-pjm-next-6-f2"
RUN_JS = f"frontend/data/backcast/runs/{RUN_ID}.js"
BENCH = "frontend/data/backcast/bench/PJM/{y}.json.gz"
OUTAGE_FILES = (
    "data/raw/campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv",
    "data/raw/campd-unit-outages-short-rederive-PJM.csv",
)
CATS = ("win", "<24h", "1-5d", "5-30d", ">30d", "fullyr")
KLASS = "COAL_BIT"


def load_run_payload() -> dict:
    """Decode the registered run payload (working tree, else ``git show HEAD``)."""
    p = ROOT / RUN_JS
    s = (
        p.read_text()
        if p.exists()
        else subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"HEAD:{RUN_JS}"], text=True
        )
    )
    b64 = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b64)))["years"]


def decode(b64: str, ann: object, npl: float) -> np.ndarray:
    """Decode a CF%-byte 8760 series to MW, rescaled to its annual TWh."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    t = raw.sum()
    return raw * (float(ann) * 1e6 / t) if (ann and t > 0) else raw / 100 * npl


def run_lengths(b: np.ndarray) -> np.ndarray:
    """Length of the True-run each element belongs to (0 where False)."""
    out = np.zeros(len(b))
    i, n = 0, len(b)
    while i < n:
        if b[i]:
            j = i
            while j < n and b[j]:
                j += 1
            out[i:j] = j - i
            i = j
        else:
            i += 1
    return out


def load_units(year: int, fids: set[int]) -> pd.DataFrame:
    """Coal-unit CAMPD hourly rows for the given facilities."""
    parts = []
    for f in glob.glob(str(ROOT / f"data/raw/campd-unit-level/*_{year}.parquet")):
        d = pd.read_parquet(
            f,
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "opTime",
                "grossLoad",
                "primaryFuelInfo",
            ],
        )
        d = d[d.facilityId.astype(int).isin(fids)]
        if len(d):
            parts.append(d)
    d = pd.concat(parts)
    d["facilityId"] = d.facilityId.astype(int)
    d["unitId"] = d.unitId.astype(str).str.strip()
    return d[d.primaryFuelInfo.fillna("").str.contains("Coal")]


def analyse_year(year: int, run: dict, outages: pd.DataFrame, gmax: pd.Series):
    """Per-plant decomposition for one year; returns (rows, category totals)."""
    bench = json.load(gzip.open(ROOT / BENCH.format(y=year)))["bench"]["plants"]
    mp = run[str(year)]["plants"]
    keys = [
        k
        for k, b in bench.items()
        if b["group"] == KLASS and k in mp and not b.get("nodata")
    ]
    cu = load_units(year, {int(k.split(":")[0]) for k in keys})
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    rows, cat_tot = [], dict.fromkeys(CATS, 0.0)
    for k in keys:
        b = bench[k]
        fid, npl = int(k.split(":")[0]), b["npl"]
        m = decode(mp[k]["m"], mp[k]["m_ann"], npl)
        c = decode(b["campd"], b["c_ann"], npl)
        d = (m - c).sum() / 1e6
        e923 = float(b.get("e_ann") or 0.0)
        x = cu[cu.facilityId == fid]
        gsum = x.grossLoad.fillna(0).sum()
        row = dict(
            key=k,
            name=b["name"][:26],
            npl=npl,
            model=m.sum() / 1e6,
            campd=c.sum() / 1e6,
            e923=e923,
            d=d,
            hrs_m=int((m > 0.5).sum()),
            hrs_a=int((c > 0.5).sum()),
        )
        if x.empty or gsum <= 0:
            row.update(unmeasurable=True, above=np.nan, within=np.nan)
            rows.append(row)
            continue
        x = x.assign(ts=pd.to_datetime(x.date) + pd.to_timedelta(x.hour, "h"))
        on = (
            x.pivot_table(index="ts", columns="unitId", values="opTime", aggfunc="sum")
            .reindex(idx)
            .fillna(0)
            > 0
        )
        caps = {}
        for u in on.columns:
            r = outages[(outages.facility_id == fid) & (outages.unit_id == u)]
            caps[u] = (
                float(r.unit_capacity_mw.max())
                if len(r)
                else float(gmax.get((fid, u), np.nan))
            )
        capv = pd.Series(caps)
        miss = capv.isna() | (capv == 0)
        if miss.any():
            capv[miss] = (
                (max(npl - capv[~miss].sum(), 0) / miss.sum()) if npl > 1 else 0
            )
        ratio = c.sum() / gsum  # CAMPD net/gross, the bench's own basis
        a_on = (on.astype(float) * capv).sum(axis=1).values * ratio
        exc = np.clip(m - a_on, 0, None)
        catcap = np.zeros((len(CATS), 8760))
        for u in on.columns:
            dark = ~on[u].values
            cov = np.zeros(8760, bool)
            for r in outages[
                (outages.facility_id == fid) & (outages.unit_id == u)
            ].itertuples():
                cov |= (idx >= r.outage_start) & (
                    idx < r.outage_end + pd.Timedelta("1D")
                )
            rl = run_lengths(dark & ~cov)
            unc = dark & ~cov
            cat = np.full(8760, -1)
            cat[dark & cov] = 0
            cat[unc & (rl < 24)] = 1
            cat[unc & (rl >= 24) & (rl < 120)] = 2
            cat[unc & (rl >= 120) & (rl < 720)] = 3
            cat[unc & (rl >= 720) & (rl < 8760)] = 4
            cat[unc & (rl >= 8760)] = 5
            for i in range(len(CATS)):
                catcap[i] += (cat == i) * capv[u] * ratio
        tc = catcap.sum(0)
        share = np.divide(catcap, tc, out=np.zeros_like(catcap), where=tc > 0)
        e = (share * exc).sum(1) / 1e6
        for i, cn in enumerate(CATS):
            cat_tot[cn] += e[i]
            row[cn] = e[i]
        row.update(
            unmeasurable=False, above=exc.sum() / 1e6, within=d - exc.sum() / 1e6
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("d", ascending=False), cat_tot


def main() -> None:
    """Print the per-year decomposition and the top-10 plant table."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2019, 2021, 2023])
    args = ap.parse_args()
    run = load_run_payload()
    outages = pd.concat(
        pd.read_csv(ROOT / f, parse_dates=["outage_start", "outage_end"])
        for f in OUTAGE_FILES
    )
    outages["unit_id"] = outages.unit_id.astype(str).str.strip()
    allu = pd.concat(
        load_units(y, set(outages.facility_id.astype(int))) for y in args.years
    )
    gmax = allu.groupby(["facilityId", "unitId"]).grossLoad.max()
    for y in args.years:
        df, cat = analyse_year(y, run, outages, gmax)
        tot = df.d.sum()
        un = df[df.unmeasurable].d.sum()
        ab = sum(cat.values())
        print(
            f"== {y}: model-CAMPD {tot:+.2f} TWh (vs EIA-923 {df.model.sum() - df.e923.sum():+.2f})"
            f" | above-synced {ab:+.2f} {{"
            + ", ".join(f"{c}: {v:.2f}" for c, v in cat.items())
            + f"}} | within-synced {tot - ab - un:+.2f} | cogen/no-gross {un:+.2f}"
            f" | top-10 plants {df.d.head(10).sum():+.2f}"
        )
        cols = [
            "key",
            "name",
            "npl",
            "model",
            "campd",
            "d",
            "hrs_m",
            "hrs_a",
            "above",
            "within",
        ]
        print(df.head(10)[cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
