"""R-CAISO-28 (link 10) — scoping probe: per-resource storage SOC in CAISO OASIS public bids.

ZERO LP. Reads nothing the model solves on. Question: does CAISO publish a
PER-RESOURCE (or per-duration-class) behavioural battery input for 2023–25?

The one candidate found is the pair of columns ``MINEOHSTATEOFCHARGE`` /
``MAXEOHSTATEOFCHARGE`` in OASIS ``PUB_RTM_GRP`` (caiso-281 saw them populated
on 53 resources on 2025-08-15; always empty in ``PUB_DAM_GRP``). This probe
samples one RTM trade date per quarter-mid month, 2023–25, and measures:

- how many masked resources submit an EOH SOC bound, and on how many hours;
- the storage universe on the same day (EN curves spanning withdrawal and
  injection, the caiso-178 S1 test) and the MW share that submits a bound;
- implied duration = max(MAXEOH) / max injection MW per resource
  (only meaningful if the bound is in MWh);
- the hour-of-day profile of the fleet-summed MIN bound (an evening hold
  would show as a rising min-SOC floor into h17–19).

Usage::

    python3 scripts/probes/_rcaiso28_eoh_soc.py            # 12 sample days
    python3 scripts/probes/_rcaiso28_eoh_soc.py --dates 2025-08-15

Output (gitignored scratch): results/calibration/_rcaiso28/eoh_soc.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.data.fetch_caiso_public_bids import _fetch_day  # noqa: E402

OUT = REPO / "results" / "calibration" / "_rcaiso28" / "eoh_soc.json"
SLEEP_S = 8.0  # OASIS acceptable-use spacing (fetcher README: >~5 s)
WD_MW_EPS = 1.0  # caiso-178 S1: |MW| that counts as real withdrawal/injection
DEFAULT_DATES = [f"{y}-{m:02d}-15" for y in (2023, 2024, 2025) for m in (2, 5, 8, 11)]


def _load(day: dt.date) -> pd.DataFrame | None:
    """Fetch one RTM trade date and return its CSV as a DataFrame."""
    body = _fetch_day(day, market="rtm")
    if body is None:
        return None
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        name = z.namelist()[0]
        return pd.read_csv(z.open(name), low_memory=False)


def summarize(day: dt.date, df: pd.DataFrame) -> dict:
    """Coverage of the EOH SOC bounds against the day's storage universe."""
    gen = df[df["RESOURCE_TYPE"] == "GENERATOR"]
    en = gen[(gen["MARKETPRODUCTTYPE"] == "EN") & gen["SCH_BID_XAXISDATA"].notna()]
    rng = en.groupby("RESOURCEBID_SEQ")["SCH_BID_XAXISDATA"].agg(["min", "max"])
    storage = rng[(rng["min"] <= -WD_MW_EPS) & (rng["max"] >= WD_MW_EPS)]

    soc = gen[gen["MINEOHSTATEOFCHARGE"].notna() | gen["MAXEOHSTATEOFCHARGE"].notna()]
    soc_ids = set(soc["RESOURCEBID_SEQ"].unique())
    st_ids = set(storage.index)
    per_res = soc.groupby("RESOURCEBID_SEQ").agg(
        lo=("MINEOHSTATEOFCHARGE", "min"),
        hi=("MAXEOHSTATEOFCHARGE", "max"),
        hours=("SCH_BID_TIMEINTERVALSTART_GMT", "nunique"),
    )
    inj = rng["max"].reindex(per_res.index)
    dur = (per_res["hi"] / inj).replace([np.inf, -np.inf], np.nan).dropna()

    # hour-of-day profile of the fleet-summed MIN bound (UTC hour of the row)
    t = pd.to_datetime(
        soc["TIMEINTERVALSTART_GMT"].fillna(soc["SCH_BID_TIMEINTERVALSTART_GMT"]),
        utc=True,
        errors="coerce",
    )
    one = soc.assign(h=((t.dt.hour - 8) % 24)).drop_duplicates(["RESOURCEBID_SEQ", "h"])
    prof = one.groupby("h")[["MINEOHSTATEOFCHARGE", "MAXEOHSTATEOFCHARGE"]].sum()

    return {
        "date": day.isoformat(),
        "n_storage_resources": len(st_ids),
        "storage_inj_mw": float(storage["max"].sum()),
        "n_soc_resources": len(soc_ids),
        "n_soc_rows": int(len(soc)),
        "soc_in_storage_set": len(soc_ids & st_ids),
        "soc_storage_inj_mw": float(storage.loc[list(soc_ids & st_ids), "max"].sum()),
        "mw_share": float(
            storage.loc[list(soc_ids & st_ids), "max"].sum() / storage["max"].sum()
        )
        if len(st_ids)
        else None,
        "median_hours_per_resource": float(per_res["hours"].median())
        if len(per_res)
        else None,
        "implied_duration_h_p10_p50_p90": [
            float(x) for x in dur.quantile([0.1, 0.5, 0.9])
        ]
        if len(dur)
        else None,
        "min_soc_sum_by_pst_hour": {
            int(k): float(v) for k, v in prof["MINEOHSTATEOFCHARGE"].items()
        },
        "max_soc_sum_by_pst_hour": {
            int(k): float(v) for k, v in prof["MAXEOHSTATEOFCHARGE"].items()
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Sample RTM trade dates and write the coverage record."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dates", nargs="+", default=DEFAULT_DATES)
    a = ap.parse_args(argv)
    rows = []
    for i, s in enumerate(a.dates):
        if i:
            time.sleep(SLEEP_S)
        day = dt.date.fromisoformat(s)
        df = _load(day)
        if df is None:
            rows.append({"date": s, "error": "no data"})
            continue
        r = summarize(day, df)
        rows.append(r)
        print(
            s,
            r["n_storage_resources"],
            round(r["storage_inj_mw"]),
            r["n_soc_resources"],
            r["soc_in_storage_set"],
            None if r["mw_share"] is None else round(r["mw_share"], 3),
            r["implied_duration_h_p10_p50_p90"],
            flush=True,
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=1))
    print("wrote", OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
