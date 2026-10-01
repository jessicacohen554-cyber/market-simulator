"""Extract CAISO RTM storage end-of-hour SOC bounds from the OASIS public-bid zips.

R-CAISO-31 (link 13), DATA INTAKE ONLY, REPORT-ONLY. Reads the gitignored
``PUB_RTM_GRP`` daily zips that ``scripts/data/fetch_caiso_public_bids.py
--market rtm`` writes to ``data/raw/caiso-public-bids/zips-rtm/`` and keeps
only the storage end-of-hour state-of-charge bid parameter
(``MINEOHSTATEOFCHARGE`` / ``MAXEOHSTATEOFCHARGE``, ESDER 4) plus the storage
universe it is measured against. The full zips (~1.5 MB/day, ~1.7 GB for
2023-25) are too large to commit; this compact extract IS committed, because
OASIS retention rolls (earliest RTM trade date served on 2026-10-01:
2021-09-01) and the zips are regenerable only while retained.

Outputs, one set per Pacific trade-date year, under
``data/raw/caiso-rtm-eoh-soc/``:

* ``caiso_rtm_eoh_soc_<year>.parquet`` -- one row per (masked resource,
  bid hour) that carries an EOH bound: ``trade_date``, ``interval_start_utc``,
  ``resourcebid_seq``, ``sc_seq``, ``min_eoh_soc_mwh``, ``max_eoh_soc_mwh``.
  The bound is constant across every product/segment row of a resource-hour
  (asserted per day), so this reshape is lossless for the two EOH fields.
* ``caiso_rtm_storage_universe_<year>.parquet`` -- one row per (trade date,
  resource) that is storage by the caiso-178 S1 test (an EN bid curve
  spanning <= -1 MW withdrawal and >= +1 MW injection) or that submits an EOH
  bound: ``en_min_mw`` / ``en_max_mw`` (EN curve x-axis extremes),
  ``n_en_hours``, ``is_storage_s1``, ``submits_eoh``. The denominator for
  coverage shares.
* ``manifest_<year>.csv`` -- one row per trade date: zip sha256 and bytes,
  CSV rows, and counts, so the committed extract is traceable to the exact
  source bytes.

Dropped (regenerable from OASIS while retained): every bid-curve price and
segment, AS bids, self-schedules, non-storage generators, interties and
participating loads.

Rule 13: the EOH bound is an OPTIONAL participant-declared conduct parameter
(R-CAISO-28 FINDING section 1 point 4). It has no forward driver and is NEVER
a solve input; this extract feeds diagnostics only.

Usage::

    python scripts/data/extract_caiso_rtm_eoh_soc.py --years 2023 2024 2025
    python scripts/data/extract_caiso_rtm_eoh_soc.py --years 2024 --workers 4
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.data.fetch_caiso_public_bids import _out_path  # noqa: E402

OUT_DIR = RAW_DATA_DIR / "caiso-rtm-eoh-soc"

#: caiso-178 S1 storage test: |MW| on the EN curve that counts as real
#: withdrawal / injection (same threshold as scripts/probes/_rcaiso28_eoh_soc.py).
WD_MW_EPS = 1.0

#: Published RTM bid rows are hourly (caiso-281 2023 Q1 FINDING section 0).
BID_INTERVAL = pd.Timedelta(hours=1)

_COLS = [
    "RESOURCE_TYPE",
    "SCHEDULINGCOORDINATOR_SEQ",
    "RESOURCEBID_SEQ",
    "MARKETPRODUCTTYPE",
    "TIMEINTERVALSTART_GMT",
    "SCH_BID_TIMEINTERVALSTART_GMT",
    "SCH_BID_TIMEINTERVALSTOP_GMT",
    "SCH_BID_XAXISDATA",
    "MINEOHSTATEOFCHARGE",
    "MAXEOHSTATEOFCHARGE",
]


def extract_day(
    zip_path: Path, day: dt.date
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (EOH rows, storage universe, manifest row) for one trade date."""
    body = zip_path.read_bytes()
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if len(names) != 1 or not names[0].endswith(".csv"):
            raise ValueError(f"{zip_path.name}: unexpected members {names}")
        raw = pd.read_csv(zf.open(names[0]), usecols=_COLS, dtype=str)
    gen = raw[raw["RESOURCE_TYPE"] == "GENERATOR"]
    num = lambda s: pd.to_numeric(s, errors="raise")  # noqa: E731

    # --- EOH bounds: one value pair per resource-hour --------------------
    soc = gen[gen["MINEOHSTATEOFCHARGE"].notna() | gen["MAXEOHSTATEOFCHARGE"].notna()]
    start = pd.to_datetime(
        soc["SCH_BID_TIMEINTERVALSTART_GMT"].fillna(soc["TIMEINTERVALSTART_GMT"]),
        utc=True,
    )
    stop = pd.to_datetime(soc["SCH_BID_TIMEINTERVALSTOP_GMT"], utc=True)
    span = (stop - start).dropna()
    if len(span) and not (span == BID_INTERVAL).all():
        raise ValueError(f"{day}: non-hourly EOH bid interval {span.unique()[:5]}")
    eoh = pd.DataFrame(
        {
            "trade_date": pd.Timestamp(day),
            "interval_start_utc": start.to_numpy(),
            "resourcebid_seq": num(soc["RESOURCEBID_SEQ"]).astype("int64").to_numpy(),
            "sc_seq": num(soc["SCHEDULINGCOORDINATOR_SEQ"]).astype("int64").to_numpy(),
            "min_eoh_soc_mwh": num(soc["MINEOHSTATEOFCHARGE"])
            .astype("float64")
            .to_numpy(),
            "max_eoh_soc_mwh": num(soc["MAXEOHSTATEOFCHARGE"])
            .astype("float64")
            .to_numpy(),
        }
    )
    key = ["resourcebid_seq", "interval_start_utc"]
    n_distinct = eoh.groupby(key)[
        ["min_eoh_soc_mwh", "max_eoh_soc_mwh", "sc_seq"]
    ].nunique(dropna=False)
    if (n_distinct > 1).any().any():
        raise ValueError(f"{day}: EOH bound is not unique per resource-hour")
    eoh = eoh.drop_duplicates(key).sort_values(key).reset_index(drop=True)

    # --- storage universe (caiso-178 S1) ---------------------------------
    en = gen[(gen["MARKETPRODUCTTYPE"] == "EN") & gen["SCH_BID_XAXISDATA"].notna()]
    en = en.assign(
        x=num(en["SCH_BID_XAXISDATA"]).astype("float64"),
        rid=num(en["RESOURCEBID_SEQ"]).astype("int64"),
        sc=num(en["SCHEDULINGCOORDINATOR_SEQ"]).astype("int64"),
        h=en["SCH_BID_TIMEINTERVALSTART_GMT"],
    )
    rng = en.groupby("rid").agg(
        sc_seq=("sc", "first"),
        en_min_mw=("x", "min"),
        en_max_mw=("x", "max"),
        n_en_hours=("h", "nunique"),
    )
    rng["is_storage_s1"] = (rng["en_min_mw"] <= -WD_MW_EPS) & (
        rng["en_max_mw"] >= WD_MW_EPS
    )
    eoh_ids = set(eoh["resourcebid_seq"])
    rng["submits_eoh"] = rng.index.isin(eoh_ids)
    missing = sorted(eoh_ids - set(rng.index))
    if missing:  # an EOH submitter with no EN curve that day
        extra = (
            eoh[eoh["resourcebid_seq"].isin(missing)]
            .groupby("resourcebid_seq")["sc_seq"]
            .first()
        )
        rng = pd.concat(
            [
                rng,
                pd.DataFrame(
                    {
                        "sc_seq": extra,
                        "en_min_mw": np.nan,
                        "en_max_mw": np.nan,
                        "n_en_hours": 0,
                        "is_storage_s1": False,
                        "submits_eoh": True,
                    }
                ),
            ]
        )
    uni = rng[rng["is_storage_s1"] | rng["submits_eoh"]].rename_axis("resourcebid_seq")
    uni = uni.reset_index().assign(trade_date=pd.Timestamp(day))
    uni = uni[
        [
            "trade_date",
            "resourcebid_seq",
            "sc_seq",
            "en_min_mw",
            "en_max_mw",
            "n_en_hours",
            "is_storage_s1",
            "submits_eoh",
        ]
    ].astype({"n_en_hours": "int64", "sc_seq": "int64"})

    man = {
        "trade_date": day.isoformat(),
        "zip_name": zip_path.name,
        "zip_bytes": len(body),
        "zip_sha256": hashlib.sha256(body).hexdigest(),
        "csv_rows": len(raw),
        "eoh_csv_rows": len(soc),
        "eoh_resource_hours": len(eoh),
        "eoh_resources": len(eoh_ids),
        "storage_s1_resources": int(uni["is_storage_s1"].sum()),
    }
    return eoh, uni, man


def _one(day: dt.date):
    """Worker: extract one day, or report it missing."""
    path = _out_path(day, "rtm")
    if not path.exists() or path.stat().st_size <= 10_000:
        return None, None, {"trade_date": day.isoformat(), "zip_name": None}
    return extract_day(path, day)


def extract_year(year: int, workers: int = 4) -> list[Path]:
    """Extract every trade date of ``year`` and write the committed outputs."""
    days = list(pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D").date)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(_one, days, chunksize=4))
    eoh = pd.concat([r[0] for r in results if r[0] is not None], ignore_index=True)
    uni = pd.concat([r[1] for r in results if r[1] is not None], ignore_index=True)
    man = pd.DataFrame([r[2] for r in results])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = [
        OUT_DIR / f"caiso_rtm_eoh_soc_{year}.parquet",
        OUT_DIR / f"caiso_rtm_storage_universe_{year}.parquet",
        OUT_DIR / f"manifest_{year}.csv",
    ]
    eoh.to_parquet(out[0], index=False, compression="zstd")
    uni.to_parquet(out[1], index=False, compression="zstd")
    man.to_csv(out[2], index=False)
    n_missing = int(man["zip_name"].isna().sum())
    print(
        f"{year}: {len(days) - n_missing}/{len(days)} days, {len(eoh):,} EOH resource-hours, "
        f"{eoh['resourcebid_seq'].nunique()} submitters; missing days: "
        f"{man.loc[man['zip_name'].isna(), 'trade_date'].tolist()}",
        flush=True,
    )
    return out


def write_sha256sums() -> Path:
    """Rewrite SHA256SUMS.txt over every committed extract file."""
    lines = []
    for p in sorted(OUT_DIR.glob("*.parquet")) + sorted(OUT_DIR.glob("manifest_*.csv")):
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    out = OUT_DIR / "SHA256SUMS.txt"
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    for year in args.years:
        extract_year(year, workers=args.workers)
    print("wrote", write_sha256sums().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
