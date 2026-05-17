"""Derive ERCOT West/Panhandle transfer limits from NP6-86 SCED data.

Reads the ERCOT "SCED Shadow Prices and Binding Transmission Constraints"
(NP6-86) archive under ``data/reference/`` and summarizes the WESTEX and
PNHNDL generic transmission constraints — the West Texas Export and
Panhandle export GTCs that the model's West/Panhandle ``TransferLink``s
represent. Prints each GTC's observed limit and how often it binds; the
mean limits feed the ``ttc_mw`` values in ``iso_configs._ercot_config``.

Run from the repo root: ``python scripts/derive_ttc_limits.py``
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

REF = Path("data/reference")
# WESTEX is one aggregate GTC; the model splits West export into two links
# (West->North and West->South_Central) in this ratio.
WESTEX_SPLIT = {"West->North": 8.0 / 11.0, "West->South_Central": 3.0 / 11.0}


def _load_constraints() -> pd.DataFrame:
    """Return every SCED binding-constraint row from the NP6-86 archive."""
    outer_zips = sorted(REF.glob("*SCEDBTCNP686*.zip"))
    if not outer_zips:
        raise SystemExit(f"no SCEDBTCNP686 archive found under {REF}/")
    frames = []
    for outer_path in outer_zips:
        with zipfile.ZipFile(outer_path) as outer:
            for inner_name in outer.namelist():
                if not inner_name.lower().endswith(".zip"):
                    continue
                with zipfile.ZipFile(io.BytesIO(outer.read(inner_name))) as inner:
                    csv_name = inner.namelist()[0]
                    frames.append(pd.read_csv(io.BytesIO(inner.read(csv_name))))
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    df = _load_constraints()
    intervals = df["SCEDTimeStamp"].nunique()
    print(f"SCED intervals: {intervals}   constraint rows: {len(df)}\n")

    for gtc in ("WESTEX", "PNHNDL"):
        sub = df[df["ConstraintName"] == gtc]
        if sub.empty:
            print(f"{gtc}: not present in archive\n")
            continue
        binding = sub[sub["ShadowPrice"] > 0]
        limit = sub["Limit"]
        print(f"=== {gtc} ===")
        print(f"  active in {len(sub)} of {intervals} intervals")
        print(f"  limit MW: mean {limit.mean():.0f}  median {limit.median():.0f}"
              f"  min {limit.min():.0f}  max {limit.max():.0f}")
        print(f"  binds (shadow price > 0): {100 * len(binding) / len(sub):.1f}%"
              f"  of active intervals")
        print()

    westex_mean = df.loc[df["ConstraintName"] == "WESTEX", "Limit"].mean()
    pnhndl_mean = df.loc[df["ConstraintName"] == "PNHNDL", "Limit"].mean()
    print("=== Derived TransferLink ttc_mw ===")
    for link, frac in WESTEX_SPLIT.items():
        print(f"  {link:24s} {westex_mean * frac:7.0f}")
    print(f"  {'Panhandle->North':24s} {pnhndl_mean:7.0f}")


if __name__ == "__main__":
    main()
