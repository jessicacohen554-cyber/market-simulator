"""Derive ERCOT zonal transfer limits from the NP6-86 SCED archive.

Reads ERCOT's "SCED Shadow Prices and Binding Transmission Constraints"
(NP6-86) monthly archives and summarizes every *generic transmission
constraint* (GTC) — the aggregate zonal interfaces, identified by an empty
FromStation — by how often it binds (shadow price > 0) and its mean limit.
The GTCs that map to the model's six-zone topology feed the ``ttc_mw`` values
in ``iso_configs._ercot_config``:

    WESTEX  -> West->North + West->South_Central (split ~8:3)
    PNHNDL  -> Panhandle->North
    N_TO_H  -> North->Houston

The most-binding ERCOT GTCs (NE_LOB, VALEXP, EASTEX, TRDWEL) are intra-zone
pockets the six-zone aggregation cannot represent; they are reported for
context but do not map to an inter-zone link.

Archives are read from ``data/raw/iso-specific-transmission`` (the full
2023-2024 monthly set) and, for backward compatibility, ``data/reference``.
Each ``*SCEDBTCNP686*.zip`` is a month of daily inner zips of CSVs.

Run from the repo root: ``python scripts/data/derive_ttc_limits.py``
"""

from __future__ import annotations

import io
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

# Look for the NP6-86 monthly archives in the bulk upload dir first, then the
# small curated reference dir.
SEARCH_DIRS = (
    Path("data/raw/iso-specific-transmission"),
    Path("data/reference"),
)
_USECOLS = ["SCEDTimeStamp", "ConstraintName", "ShadowPrice", "Limit", "FromStation"]

# WESTEX is one aggregate GTC; the model splits West export into two links
# (West->North and West->South_Central) in this ratio.
WESTEX_SPLIT = {"West->North": 8.0 / 11.0, "West->South_Central": 3.0 / 11.0}
# GTC -> the single model link it maps to (WESTEX handled separately above).
GTC_TO_LINK = {"PNHNDL": "Panhandle->North", "N_TO_H": "North->Houston"}


def _archive_paths() -> list[Path]:
    """Return the NP6-86 monthly archives from the first dir that has any.

    Only one directory is used (not merged) so a month present in both the bulk
    upload and the curated reference dir is not double-counted.
    """
    for d in SEARCH_DIRS:
        paths = sorted(d.glob("*SCEDBTCNP686*.zip"))
        if paths:
            return paths
    dirs = ", ".join(str(d) for d in SEARCH_DIRS)
    raise SystemExit(f"no SCEDBTCNP686 archives found under {dirs}")


def _read_month(path: Path) -> pd.DataFrame:
    """Return every constraint row in one monthly archive (nested daily zips)."""
    frames = []
    with zipfile.ZipFile(path) as outer:
        for inner_name in outer.namelist():
            if not inner_name.lower().endswith(".zip"):
                continue
            with zipfile.ZipFile(io.BytesIO(outer.read(inner_name))) as inner:
                csv_name = inner.namelist()[0]
                # Some monthly CSVs carry latin-1 bytes (e.g. 0xA0); latin-1
                # decodes every byte so the read never fails on encoding. A few
                # daily files have an off-schema header — skip those rather than
                # abort the whole month.
                try:
                    frames.append(
                        pd.read_csv(
                            io.BytesIO(inner.read(csv_name)),
                            usecols=_USECOLS,
                            encoding="latin-1",
                        )
                    )
                except (ValueError, UnicodeDecodeError):
                    continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def main() -> None:
    bind_iv: dict[str, int] = defaultdict(int)
    limit_sum: dict[str, float] = defaultdict(float)
    limit_n: dict[str, int] = defaultdict(int)
    limit_bind_sum: dict[str, float] = defaultdict(float)
    limit_bind_n: dict[str, int] = defaultdict(int)
    total_intervals = 0

    for path in _archive_paths():
        df = _read_month(path)
        if df.empty:
            print(f"  {path.name}: no data")
            continue
        total_intervals += df["SCEDTimeStamp"].nunique()
        gtc = df[df["FromStation"].isna()]  # aggregate zonal constraints
        for name, sub in gtc.groupby("ConstraintName"):
            binding = sub[sub["ShadowPrice"] > 0]
            bind_iv[name] += binding["SCEDTimeStamp"].nunique()
            limit_sum[name] += sub["Limit"].sum()
            limit_n[name] += len(sub)
            limit_bind_sum[name] += binding["Limit"].sum()
            limit_bind_n[name] += len(binding)
        print(f"  {path.name}: {df['SCEDTimeStamp'].nunique()} intervals")

    print(f"\nTotal SCED intervals: {total_intervals}\n")
    print(f"{'GTC':12s} {'binds %':>8s} {'limit_mean':>11s} {'limit@bind':>11s}")
    for name in sorted(bind_iv, key=lambda n: -bind_iv[n]):
        pct = 100.0 * bind_iv[name] / total_intervals
        lim = limit_sum[name] / max(limit_n[name], 1)
        limb = limit_bind_sum[name] / max(limit_bind_n[name], 1)
        print(f"{name:12s} {pct:8.2f} {lim:11.0f} {limb:11.0f}")

    def _limit_at_bind(name: str) -> float:
        return limit_bind_sum[name] / max(limit_bind_n[name], 1)

    print("\n=== Derived TransferLink ttc_mw (model interfaces) ===")
    westex = _limit_at_bind("WESTEX")
    for link, frac in WESTEX_SPLIT.items():
        print(f"  {link:24s} {westex * frac:7.0f}")
    for gtc, link in GTC_TO_LINK.items():
        print(f"  {link:24s} {_limit_at_bind(gtc):7.0f}")


if __name__ == "__main__":
    main()
