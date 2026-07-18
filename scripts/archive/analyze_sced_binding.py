"""Rank ERCOT's binding transmission constraints from the SCED NP6-86 archive.

The decisive pre-test for the finer-zone question (docs/audit-followup-tests-
2026-06.md / the spatial axis): *which* internal constraints actually bind, how
hard, and whether they correspond to a North<->South_Central zone split (which
would redistribute the CC_REGULAR over-run) or to deep intra-zonal pockets a
modest split would not form. No LP solve — pure aggregation of the published
5-minute binding-constraint shadow prices.

For every SCED interval in `data/raw/iso-specific-transmission/
*SCEDBTCNP686*.zip` (nested zips), accumulate per ConstraintName:
  - binding intervals (ShadowPrice > 0) and their share,
  - sum / max ShadowPrice ($/MWh-interval) — the congestion-rent proxy,
  - From/To station + kV (locates the constraint), and a backbone flag
    (>=200 kV = inter-regional; <200 kV = local pocket).
Writes a ranked CSV and prints the top constraints by total shadow price.
"""

from __future__ import annotations

import io
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "inputs" / "raw-data" / "iso-specific-transmission"
COLS = [
    "ConstraintName",
    "ShadowPrice",
    "FromStation",
    "ToStation",
    "FromStationkV",
    "ToStationkV",
]


def _iter_interval_frames(monthly_zip: Path):
    """Yield each interval's binding-constraint DataFrame from a monthly zip."""
    with zipfile.ZipFile(monthly_zip) as outer:
        for name in outer.namelist():
            try:
                inner = zipfile.ZipFile(io.BytesIO(outer.read(name)))
            except zipfile.BadZipFile:
                continue
            for member in inner.namelist():
                raw = inner.read(member)
                try:
                    yield pd.read_csv(io.BytesIO(raw), usecols=COLS, encoding="latin-1")
                except Exception:  # noqa: BLE001 — skip a malformed interval
                    continue


def main() -> None:
    months = sorted(SRC.glob("*SCEDBTCNP686*.zip"))
    if not months:
        sys.exit(f"no SCED archive under {SRC}")
    # Per-constraint accumulators.
    n_bind = defaultdict(int)  # intervals with ShadowPrice > 0
    n_seen = defaultdict(int)  # intervals the constraint was monitored
    sum_sp = defaultdict(float)  # sum of binding shadow prices
    max_sp = defaultdict(float)
    meta: dict[str, tuple] = {}  # From/To/kV (first seen)
    total_intervals = 0

    for mz in months:
        for df in _iter_interval_frames(mz):
            total_intervals += 1
            sp = pd.to_numeric(df["ShadowPrice"], errors="coerce").fillna(0.0)
            for name, s, fr, to, fkv, tkv in zip(
                df["ConstraintName"],
                sp,
                df["FromStation"],
                df["ToStation"],
                df["FromStationkV"],
                df["ToStationkV"],
            ):
                n_seen[name] += 1
                if s > 0:
                    n_bind[name] += 1
                    sum_sp[name] += s
                    if s > max_sp[name]:
                        max_sp[name] = s
                if name not in meta:
                    meta[name] = (fr, to, fkv, tkv)
        print(
            f"  processed {mz.name}  (cum intervals: {total_intervals})",
            file=sys.stderr,
        )

    rows = []
    for name in sum_sp:
        fr, to, fkv, tkv = meta.get(name, ("", "", 0, 0))
        kv = max(
            pd.to_numeric(fkv, errors="coerce") or 0,
            pd.to_numeric(tkv, errors="coerce") or 0,
        )
        rows.append(
            {
                "constraint": name,
                "from": fr,
                "to": to,
                "kV": int(kv),
                "backbone": kv >= 200,
                "bind_intervals": n_bind[name],
                "bind_share_pct": round(100 * n_bind[name] / max(n_seen[name], 1), 1),
                "sum_shadow": round(sum_sp[name], 0),
                "max_shadow": round(max_sp[name], 0),
            }
        )
    out = pd.DataFrame(rows).sort_values("sum_shadow", ascending=False)
    dest = REPO / "docs" / "sced-binding-constraints-2023-2025.csv"
    out.to_csv(dest, index=False)

    total_sp = out["sum_shadow"].sum()
    print(f"\nTotal SCED intervals processed: {total_intervals}")
    print(f"Distinct constraints that ever bound: {len(out)}")
    print(f"Total binding shadow price (congestion-rent proxy): {total_sp:,.0f}")
    print(
        "\nTop 30 binding constraints by total shadow price "
        "(share of all congestion rent in parens):"
    )
    pd.set_option("display.width", 200)
    top = out.head(30).copy()
    top["rent_pct"] = (100 * top["sum_shadow"] / total_sp).round(1)
    print(
        top[
            [
                "constraint",
                "from",
                "to",
                "kV",
                "backbone",
                "bind_share_pct",
                "sum_shadow",
                "rent_pct",
                "max_shadow",
            ]
        ].to_string(index=False)
    )
    bb = out[out["backbone"]]["sum_shadow"].sum()
    print(
        f"\nBackbone (>=200 kV, inter-regional) share of rent: "
        f"{100 * bb / total_sp:.0f}%  |  local pocket (<200 kV): "
        f"{100 * (1 - bb / total_sp):.0f}%"
    )
    print(f"\nWrote {dest}")


if __name__ == "__main__":
    main()
