"""EIA-860 vintage-to-vintage unit diffs (W0 E.2, audit §E.2).

When a unit's ``Operating Year`` / ``Operating Month``, rating or status differs
between consecutive Final releases, the SOLVED year's own vintage wins (the
loader reads ``vintage_<Y>/``); this writes the diff so the change is visible
rather than discovered through a price residual. One CSV per consecutive pair,
``<Y>_<Y+1>.csv``: every ``(plant, generator)`` present in both operable sheets
with any compared field changed, plus units present in only one (``side``).

Derived evidence, not a model input (nothing on the solve path reads it), so it
is written under the W0 census records rather than ``data/raw``.

Usage::

    python scripts/data/derive_eia860_vintage_diffs.py \\
        --out docs/records/governance/closeout-2026-10/W0-census/vintage_diffs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

#: Operable-sheet fields compared across vintages.
FIELDS: tuple[str, ...] = (
    "Operating Year",
    "Operating Month",
    "Nameplate Capacity (MW)",
    "Summer Capacity (MW)",
    "Winter Capacity (MW)",
    "Status",
    "Technology",
)


def _sheet(vdir: Path) -> pd.DataFrame:
    df = pd.read_parquet(vdir / "eia860_generator_operable.parquet")
    df.columns = [str(c).strip() for c in df.columns]
    df["plant"] = pd.to_numeric(df["Plant Code"], errors="coerce")
    df = df.dropna(subset=["plant"])
    df["plant"] = df["plant"].astype(int)
    df["gen"] = df["Generator ID"].astype(str).str.strip()
    keep = ["plant", "gen"] + [f for f in FIELDS if f in df.columns]
    return df[keep].drop_duplicates(["plant", "gen"]).set_index(["plant", "gen"])


def vintage_diff(a: Path, b: Path) -> pd.DataFrame:
    """Unit-level differences between two vintage directories' operable sheets."""
    x, y = _sheet(a), _sheet(b)
    both = x.index.intersection(y.index)
    rows = []
    for field in FIELDS:
        if field not in x.columns or field not in y.columns:
            continue
        xa = x.loc[both, field]
        ya = y.loc[both, field]
        xn, yn = pd.to_numeric(xa, errors="coerce"), pd.to_numeric(ya, errors="coerce")
        numeric = xn.notna() | yn.notna()
        changed = (numeric & ~((xn == yn) | (xn.isna() & yn.isna()))) | (
            ~numeric & (xa.astype(str).str.strip() != ya.astype(str).str.strip())
        )
        for (plant, gen), old, new in zip(
            xa[changed].index, xa[changed].values, ya[changed].values
        ):
            rows.append(
                {"plant": plant, "gen": gen, "field": field, "old": old, "new": new}
            )
    for side, idx in (
        ("only_" + a.name, x.index.difference(y.index)),
        ("only_" + b.name, y.index.difference(x.index)),
    ):
        for plant, gen in idx:
            rows.append(
                {"plant": plant, "gen": gen, "field": "side", "old": side, "new": ""}
            )
    return pd.DataFrame(rows, columns=["plant", "gen", "field", "old", "new"])


def main(argv: list[str] | None = None) -> int:
    """Write one diff CSV per consecutive committed vintage pair."""
    from market_sim.config.paths import EIA_860_DIR

    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    vintages = sorted(
        int(p.name.split("_")[1]) for p in EIA_860_DIR.glob("vintage_*") if p.is_dir()
    )
    for y0, y1 in zip(vintages, vintages[1:]):
        diff = vintage_diff(
            EIA_860_DIR / f"vintage_{y0}", EIA_860_DIR / f"vintage_{y1}"
        )
        path = args.out / f"{y0}_{y1}.csv"
        diff.to_csv(path, index=False)
        print(f"{path.name}: {len(diff)} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
