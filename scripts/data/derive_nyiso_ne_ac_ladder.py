"""Derive the NYISO NE AC tie node ladder and the pooled ladder without it.

NYISO-NEXT-11 (owner ruling Q-a, 2026-09-28;
``docs/PRECOMMIT-nyiso-next11-ne-ac-node-2026-09-28.md``). The NY-New England
AC tie (P-32 ``SCH - NE - NY``, New Scotland / Pleasant Valley, landing zone
F-G = ``Capital_Hudson``) leaves the pooled ``NYISO_external`` star node for its
own TWO-WAY node, priced at the neighbour's own measured price. Two tables are
derived here, both by FROZEN formulas and both from measured inputs only:

1. :data:`~market_sim.model.interchange.spec.NYISO_NE_AC_LADDER_BY_YEAR` — per
   year, ``SEAM_FLOW_TRANCHES`` (8) equal import bands and 8 equal export bands,
   sized on the year's MEDIAN posted import / export limit of the tie (P-32
   ``positive_limit_mw`` / ``-negative_limit_mw``), each band carrying an
   OFFSET to the hourly ISO-NE ``.I.ROSETON 345 1`` DA LMP. The offsets are the
   PJM neighbour-hourly Q-Q duration coupling transferred in kind
   (``derive_pjm_seam_ladders._derive_one_spread``: ``qq_import`` /
   ``qq_export`` at the midpoint-depth grid, same-seam no-wash clamp) applied to
   the tie's own flow and its own spread ``CAPITL DA - Roseton DA``. NEXT-10's
   phase 0 (S1-S3) is exactly the admissibility test of that coupling, and
   NE_AC passed it in every year. Band k's hourly offer is
   ``Roseton(t) + offset_k``: it clears iff ``spread(t) > offset_k`` (import)
   or ``spread(t) < offset_k`` (export).
2. :data:`~market_sim.model.interchange.spec.NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR`
   — the incumbent pooled NYISO ladder formula
   (``derive_nyiso_import_tranches.derive``, byte-for-byte) on net import
   WITHOUT the NE AC row, so the tie's volume is counted once (rule 19).

Rule 23: re-derive only when the P-32 posting or either DA price series
extends. Coverage 2021-2025 (the ``seam-neighbour-price`` intake).

Usage::

    uv run python scripts/data/derive_nyiso_ne_ac_ladder.py
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "data"))

import derive_nyiso_import_tranches as dnit  # noqa: E402
from derive_pjm_seam_ladders import NO_WASH_EPS, qq_export, qq_import  # noqa: E402

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES  # noqa: E402

YEARS = (2021, 2022, 2023, 2024, 2025)
SNP = RAW_DATA_DIR / "seam-neighbour-price"
FLOW_DIR = RAW_DATA_DIR / "NYISO" / "interface-flows"
NE_ROW = "SCH - NE - NY"
ROSETON_ID = 4011  # ISO-NE ``.I.ROSETON 345 1`` (seam-neighbour-price README)
LANDING_ZONE = "CAPITL"  # NYISO zone F (the tie's landing zone)
H = 8760
_SENTINEL = (
    9000.0  # P-32 posts +-9999 for "no limit"; curate_nyiso_interface_flows nulls it
)


def _hoy(local: pd.Series) -> np.ndarray:
    """Hour-of-year on the local clock — ``derive_nyiso_import_tranches``'s convention."""
    return ((local.dt.dayofyear - 1) * 24 + local.dt.hour).to_numpy()


def _on_clock(hoy: np.ndarray, values: np.ndarray) -> np.ndarray:
    s = pd.Series(values).groupby(hoy).mean()
    return s.reindex(range(H)).interpolate(limit=3).to_numpy(dtype=float)


def load_ne_ac(year: int) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """Return (raw P-32 frame, NE AC flow, posted import limit, posted export limit)."""
    df = pd.read_csv(FLOW_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz")
    ne = df[df["interface"] == NE_ROW]
    hoy = _hoy(pd.to_datetime(ne["interval_start_local"]))
    pos = ne["positive_limit_mw"].where(ne["positive_limit_mw"].abs() < _SENTINEL)
    neg = ne["negative_limit_mw"].where(ne["negative_limit_mw"].abs() < _SENTINEL)
    return (
        df,
        _on_clock(hoy, ne["flow_mw"].to_numpy(dtype=float)),
        _on_clock(hoy, pos.to_numpy(dtype=float)),
        _on_clock(hoy, -neg.to_numpy(dtype=float)),
    )


def load_capitl_da(year: int) -> np.ndarray:
    """NYISO DA LBMP at the landing zone, on the local hour-of-year clock."""
    path = SNP / "nyiso" / f"NYISO_dam_proxy_lbmp_{year}.csv.gz"
    with gzip.open(path, "rt") as f:
        d = pd.read_csv(f)
    d = d[d["name"] == LANDING_ZONE]
    local = pd.to_datetime(d["time_stamp"], format="%m/%d/%Y %H:%M")
    return _on_clock(_hoy(local), d["lbmp"].to_numpy(dtype=float))


def load_roseton_da(year: int) -> np.ndarray:
    """ISO-NE DA LMP at Roseton, on the local hour-of-year clock."""
    n = pd.read_csv(SNP / "neiso" / f"NEISO_ny_ext_node_lmp_{year}.csv")
    n = n[n["location_id"] == ROSETON_ID].sort_values(["date", "seq"])
    he = n["hour_ending"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    local = pd.to_datetime(n["date"]) + pd.to_timedelta(he - 1, unit="h")
    return _on_clock(_hoy(local), n["da_lmp"].to_numpy(dtype=float))


def derive_offsets(
    spread: np.ndarray, flow: np.ndarray, limit_imp: float, limit_exp: float
) -> tuple[list[float], list[float], int]:
    """Q-Q offsets on the spread, per direction; returns (import, export, n_clamped)."""
    ok = np.isfinite(spread) & np.isfinite(flow)
    s, f = spread[ok], flow[ok]
    grid = np.arange(SEAM_FLOW_TRANCHES) + 0.5
    imp = [qq_import(s, f, m) for m in grid * limit_imp / SEAM_FLOW_TRANCHES]
    exp = [qq_export(s, f, m) for m in grid * limit_exp / SEAM_FLOW_TRANCHES]
    lim = min(imp) - NO_WASH_EPS
    clamped = sum(1 for e in exp if e > lim)
    exp = [min(e, lim) for e in exp]
    return [round(x, 2) for x in imp], [round(x, 2) for x in exp], clamped


def derive_year(year: int) -> dict:
    """Both tables' entries for one year, plus the inputs the probe reuses."""
    df, flow, lim_i, lim_e = load_ne_ac(year)
    spread = load_capitl_da(year) - load_roseton_da(year)
    imp_mw, exp_mw = float(np.nanmedian(lim_i)), float(np.nanmedian(lim_e))
    imp, exp, clamped = derive_offsets(spread, flow, imp_mw, exp_mw)
    net_all = dnit.load_net_import(year)
    net_wo = net_all - np.nan_to_num(flow)
    da = dnit.load_da_lmp(year)
    return {
        "node": {
            "import_mw": imp_mw,
            "export_mw": exp_mw,
            "import": imp,
            "export": exp,
        },
        "export_clamped": clamped,
        "pooled_without_ne": dnit.derive(net_wo, da),
        "pooled_with_ne": dnit.derive(net_all, da),
        "frame": df,
        "flow": flow,
        "limit_import": lim_i,
        "limit_export": lim_e,
        "spread": spread,
        "net_all": net_all,
        "net_without_ne": net_wo,
    }


def main() -> None:
    """Print both tables as Python literals for ``model/interchange/spec.py``."""
    res = {y: derive_year(y) for y in YEARS}
    print("NYISO_NE_AC_LADDER_BY_YEAR: dict[int, dict] = {")
    for y, r in res.items():
        n = r["node"]
        print(f"    {y}: {{")
        print(f'        "import_mw": {n["import_mw"]},')
        print(f'        "export_mw": {n["export_mw"]},')
        print(f'        "import": {n["import"]},')
        print(f'        "export": {n["export"]},')
        print("    },")
    print("}")
    print("NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR: dict[int, list] = {")
    for y, r in res.items():
        print(f"    {y}: [")
        for name, cap, price in r["pooled_without_ne"]:
            print(f'        ("{name}", {cap}, {price}),')
        print("    ],")
    print("}")
    for y, r in res.items():
        if r["export_clamped"]:
            print(f"# {y}: {r['export_clamped']} export offset(s) no-wash clamped")


if __name__ == "__main__":
    main()
