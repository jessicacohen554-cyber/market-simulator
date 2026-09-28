"""soco-82 zero-LP probe: the perunitdark-SOCO derive drift and the 2019 cycler conduct.

Rule 32 ``[R-SHARD]`` (a): never solves. Three instruments:

``drift``  — differences a HEAD re-derive of ``campd-unit-outages-perunitdark-SOCO.csv``
             (``--head``) against the committed artifact and, with ``--prefix``, against a
             re-derive run with the pre-F1 retiree parquet swapped in (``git show
             31e54d8a5^:data/raw/eia-860/eia860_generator_retired_within_window.parquet``).
             Byte-identity of the latter is the attribution (rule 23).

``greedy`` — price-blind availability bound of regenerating the file. For every ADDED
             window whose facility is in the keeper's LP fleet that year (only Wansley
             6052 in 2019-2021; Gorgas 8 / Hammond 708 are not in any SOCO LP fleet),
             the keeper's committed hourly MW at that plant is clipped to the plant's
             nameplate minus the dark units' share in window hours. The clipped energy
             is (a) LOST and (b) refilled 1:1 by the rest of coal (two bounds on the
             COAL_BIT row). C1 through ``calibration_verdict.score_fuelmix``; C4 through
             ``_soco73_phase0.c4_coal``.

``lambda`` — Southern Company's own FERC-714 Part II Sch. 6 hourly system lambda
             (2019-2020, PUDL raw archive, Zenodo record 21738524 ``ferc714.zip``,
             sha256 a2797ab2...d2d67; scratch-only, not committed) against the keeper's
             P1 price and against each coal plant's P1 offer in its CEMS-synced hours.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco82_dark_drift.py drift --head H.csv [--prefix P.csv]
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco82_dark_drift.py greedy --head H.csv
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco82_dark_drift.py lambda --lambda L.parquet
"""

from __future__ import annotations

import argparse
import base64
import filecmp
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(_ROOT / "scripts"), str(_ROOT / "scripts" / "probes"), str(_ROOT / "src")]

import _soco73_phase0 as s73  # noqa: E402

KEEPER = "2026-09-27-soco81-coal-incremental-hr"
SPAN = _ROOT / "results/calibration/soco81_span"
COMMITTED = _ROOT / "data/raw/campd-unit-outages-perunitdark-SOCO.csv"
T = 8760
#: facility ids present in the keeper's LP fleet per year (fleet_only rebuilds, soco-82 §2)
IN_FLEET = {2019: {6052}, 2020: {6052}, 2021: {6052}, 2022: set()}

s73.KEEPER_ID = KEEPER
s73.SPAN = SPAN


def added(head: Path) -> pd.DataFrame:
    """Rows in the HEAD re-derive that the committed artifact lacks."""
    a, b = pd.read_csv(COMMITTED), pd.read_csv(head)
    m = b.merge(a, how="left", indicator=True)
    lost = a.merge(b, how="left", indicator=True)
    assert (lost._merge == "both").all(), "HEAD re-derive DROPS committed rows"
    return m[m._merge == "left_only"].drop(columns="_merge")


def main_drift(head: Path, prefix: Path | None) -> None:
    """Print the added rows by facility/unit/year and the pre-F1 identity check."""
    d = added(head)
    d["year"] = d.outage_start.str[:4].astype(int)
    print(f"added rows: {len(d)}")
    print(d.groupby(["facility_name", "facility_id", "unit_id", "year"])
          .agg(n=("duration_days", "size"), days=("duration_days", "sum")).to_string())
    print("capacity_source:", d.capacity_source.value_counts().to_dict())
    if prefix is not None:
        same = filecmp.cmp(prefix, COMMITTED, shallow=False)
        print(f"pre-F1-retiree re-derive byte-identical to committed: {same}")


def main_greedy(head: Path) -> None:
    """Availability bound of the added windows on the keeper payload."""
    import calibration_verdict as cv

    art = cv.load_artifacts(KEEPER)
    d = added(head)
    idx = pd.date_range("2019-01-01", periods=T * 4 + 24, freq="h")
    for y in (2019, 2020, 2021, 2022):
        pay = art["payload"]["years"][str(y)]["plants"]
        bench = art["bench"][y]["plants"]
        hours = pd.date_range(f"{y}-01-01", periods=T, freq="h")
        coal_dt = np.zeros(T)
        lost = 0.0
        for fac in sorted(IN_FLEET[y]):
            w = d[(d.facility_id == fac)]
            share = np.zeros(T)
            for r in w.itertuples():
                on = (hours >= pd.Timestamp(r.outage_start)) & (hours < pd.Timestamp(r.outage_end))
                share[on] += r.unit_pct_of_plant / 100.0
            share = np.clip(share, 0, 1)
            bks = [k for k, v in bench.items() if int(str(k).split(":")[0]) == fac
                   and str(v.get("group", "")).startswith("COAL")]
            if not bks:
                continue
            bv = bench[bks[0]]
            pk = bks[0] if bks[0] in pay else str(fac)
            npl = float(bv["npl"])
            m = np.frombuffer(base64.b64decode(pay[pk]["m"])[:T], dtype=np.uint8) * npl / 100.0
            cap = npl * (1.0 - share)
            cut = np.maximum(0.0, m - cap)
            lost += cut.sum() / 1e6
            coal_dt -= cut
            print(f"{y} {fac}: model {m.sum()/1e6:.3f} TWh, dark-share mean {share.mean():.3f}, "
                  f"clipped {cut.sum()/1e6:.3f} TWh")
        for label, delta in (
            ("lost->CC", {"COAL_BIT": -lost, "CC_REGULAR": +lost}),
            ("refilled-by-coal", {}),
        ):
            c1 = s73.c1_rows(y, delta)
            r = c1[c1.cls == "COAL_BIT"].iloc[0]
            print(f"  {y} [{label}] C1 COAL_BIT {r.pp0:+.2f} {r.st0} -> {r.pp1:+.2f} {r.st1}")
        r0, n0, r1, n1 = s73.c4_coal(y, coal_dt)
        print(f"  {y} C4 coal (lost bound) r/NRMSE {r0:.3f}/{n0:.3f} -> {r1:.3f}/{n1:.3f}")


def main_lambda(lam: Path) -> None:
    """Keeper P1 price and coal offers vs Southern's reported system lambda."""
    L = pd.read_parquet(lam)
    for y in (2019, 2020):
        ly = L[L.report_yr == y].sort_values("ts").lam.to_numpy(float)[:T]
        s = pd.read_parquet(SPAN / f"hourly/system_{y}.parquet")
        p = s[s.zone == "SOCO_AL"].sort_values("hour").price.to_numpy(float)[:T]
        n = min(len(p), len(ly))
        print(f"{y}: model P1 mean {p[:n].mean():.2f} median {np.median(p[:n]):.2f} | "
              f"lambda mean {np.nanmean(ly):.2f} median {np.nanmedian(ly):.2f} | "
              f"r {np.corrcoef(p[:n], ly[:n])[0, 1]:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("drift", "greedy", "lambda"))
    ap.add_argument("--head", type=Path)
    ap.add_argument("--prefix", type=Path)
    ap.add_argument("--lambda", dest="lam", type=Path)
    a = ap.parse_args()
    {"drift": lambda: main_drift(a.head, a.prefix),
     "greedy": lambda: main_greedy(a.head),
     "lambda": lambda: main_lambda(a.lam)}[a.mode]()
