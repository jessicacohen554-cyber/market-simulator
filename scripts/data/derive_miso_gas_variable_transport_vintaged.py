"""Derive MISO gas VARIABLE transport per receipt year (the vintaged companion).

miso-299 (owner ruling 2026-10-01, miso-298 card *"Per-year transport phase 0"*).
The frozen table ``data/raw/reference/miso_gas_variable_transport.csv`` is one
value per plant fitted on the 2023-2025 receipts pooled
(:mod:`derive_miso_gas_variable_transport`).  miso-298 solved the owner-ruled
gas form with it over 2019-2025 and was killed by K-1; its RESULT attributes the
early-year cost to that table's level sitting above the 2019-2022 print-over-hub
wedge.  The one admissible successor is a data question, not a parameter: the
SAME estimator on each receipt year's OWN rows.

Rule 23 ``[R-FROZEN-DERIVE]``: this is a re-derive on NEW source years — the
2019-2022 EIA-923 gas receipts (``eia923_monthly_fuel_costs.parquet``) were
never in the frozen fit — so it is admissible, and it NEVER overwrites the
frozen table.  It writes a sibling directory of per-year tables, one
``<year>.csv`` + ``<year>.pool.csv`` pair per receipt year, each in exactly the
frozen table's format so the same consumer
(:func:`market_sim.data.fuel.basis.miso._load_miso_gas_variable_transport`)
reads it unchanged.

NOTHING IS RE-TUNED.  The estimator (burn-weighted WLS of ``print - hub`` on
``1/burn``), the own-plant bars (``MIN_MONTHS`` 12, ``MIN_BURN_SPREAD`` 2.0),
the fallback ladder (own -> zone|group -> group -> MISO-wide) and the hub
staircases are imported from the frozen script and called with
``years=(year,)``.  With a single year a plant carries its own rung only when
every one of its twelve months has an admissible receipt, so own-plant coverage
is lower than the pooled table's; the ladder absorbs the rest, as declared.
The coverage is reported, not adjusted.

Forward analogue (rule 13): a forecast year carries the latest receipt year's
table forward, exactly as the frozen table already is.

Usage (repo root)::

    uv run python scripts/data/derive_miso_gas_variable_transport_vintaged.py
    # -> data/raw/reference/miso_gas_variable_transport_vintaged/<year>.csv (+ .pool.csv)
    #    results/phase0/miso/_miso299_vintaged_tables.json (the per-year summary)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.data import derive_miso_gas_variable_transport as frozen  # noqa: E402

OUT_DIR = ROOT / "data/raw/reference/miso_gas_variable_transport_vintaged"
SUMMARY = ROOT / "results/phase0/miso/_miso299_vintaged_tables.json"
#: Every receipt year the keeper carries (rule 16).  2026 is a partial year and
#: is not a solve year; it is excluded.
YEARS: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
REPORT_GROUPS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")


def _cap_wtd(frame: pd.DataFrame, col: str, mask) -> float | None:
    """Nameplate-weighted mean of ``col`` over ``mask`` rows."""
    sub = frame[mask]
    if sub.empty or sub["nameplate_mw"].sum() <= 0:
        return None
    return round(
        float((sub[col] * sub["nameplate_mw"]).sum() / sub["nameplate_mw"].sum()), 4
    )


def _write(frame: pd.DataFrame, year: int, out_dir: Path) -> tuple[Path, Path]:
    """Write ``<year>.csv`` + ``<year>.pool.csv`` in the frozen table's format."""
    out = out_dir / f"{year}.csv"
    header = [
        "# MISO gas VARIABLE transport over the zone's traded hub ($/MMBtu), "
        f"RECEIPT YEAR {year} ALONE (vintaged companion, miso-299).",
        "# Derived by scripts/data/derive_miso_gas_variable_transport_vintaged.py: the "
        "frozen estimator of derive_miso_gas_variable_transport.py (burn-weighted WLS "
        f"of print - hub on 1/burn, MIN_MONTHS {frozen.MIN_MONTHS}, MIN_BURN_SPREAD "
        f"{frozen.MIN_BURN_SPREAD}) called with years=({year},).",
        "# Rule 23 [R-FROZEN-DERIVE]: a re-derive on NEW source years; the frozen "
        "2023-2025 pooled table is untouched.",
        "# Consumers resolve a plant absent from this table down the declared ladder "
        "own -> zone_group -> group -> miso, whose rungs are in the sibling .pool.csv.",
        f"# Pooled fallback rungs: MISO-wide v = {frame.attrs['pooled_iso']:.6f} "
        "$/MMBtu; per (zone|group) rungs in the sibling .pool.csv.",
    ]
    with out.open("w") as handle:
        handle.write("\n".join(header) + "\n")
        frame.to_csv(handle, index=False)
    pool = pd.DataFrame(
        [
            {"rung": "zone_group", "key": k, "v_usd_mmbtu": round(v, 6)}
            for k, v in sorted(frame.attrs["pooled_zone_group"].items())
        ]
        + [
            {"rung": "group", "key": k, "v_usd_mmbtu": round(v, 6)}
            for k, v in sorted(frame.attrs["pooled_group"].items())
        ]
        + [
            {
                "rung": "miso",
                "key": "__MISO__",
                "v_usd_mmbtu": round(frame.attrs["pooled_iso"], 6),
            }
        ]
    )
    pool_path = out.with_suffix(".pool.csv")
    pool.to_csv(pool_path, index=False)
    return out, pool_path


def summarize(frame: pd.DataFrame, panel: pd.DataFrame, year: int) -> dict:
    """Per-year report: coverage, ``v`` by class, the burn-weighted wedge by class."""
    own = frame["v_source"] == "own"
    out: dict = {
        "year": year,
        "plants_in_table": int(len(frame)),
        "plants_own": int(own.sum()),
        "plant_months": int(len(panel)),
        "own_cap_share_of_table": round(
            float(frame.loc[own, "nameplate_mw"].sum() / frame["nameplate_mw"].sum()), 4
        ),
        "sources": {k: int(v) for k, v in frame["v_source"].value_counts().items()},
        "pooled_iso": round(float(frame.attrs["pooled_iso"]), 6),
        "pooled_group": {
            k: round(float(v), 6) for k, v in frame.attrs["pooled_group"].items()
        },
        "v_cap_wtd": {},
        "v_own_cap_wtd": {},
        "wedge_burn_wtd": {},
        "v_topquartile_own_cap_wtd": {},
    }
    groups = list(REPORT_GROUPS) + ["__ALL_GAS__"]
    for g in groups:
        fm = np.ones(len(frame), bool) if g == "__ALL_GAS__" else (frame["group"] == g)
        pm = np.ones(len(panel), bool) if g == "__ALL_GAS__" else (panel["group"] == g)
        out["v_cap_wtd"][g] = _cap_wtd(frame, "v_usd_mmbtu", fm)
        out["v_own_cap_wtd"][g] = _cap_wtd(frame, "v_usd_mmbtu", fm & own)
        out["v_topquartile_own_cap_wtd"][g] = _cap_wtd(
            frame, "v_topquartile_usd_mmbtu", fm & own
        )
        sub = panel[pm]
        out["wedge_burn_wtd"][g] = (
            round(
                float(
                    (sub["wedge_usd_mmbtu"] * sub["burn_mmbtu"]).sum()
                    / sub["burn_mmbtu"].sum()
                ),
                4,
            )
            if not sub.empty
            else None
        )
    return out


def main() -> None:
    """Derive every receipt year alone, write the companions and the summary."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    frozen_tab = pd.read_csv(frozen.OUT, comment="#")
    summary: dict = {
        "_rule": {
            "estimator": "frozen derive_miso_gas_variable_transport.derive(years=(Y,)) per year",
            "bars": {
                "MIN_MONTHS": frozen.MIN_MONTHS,
                "MIN_BURN_SPREAD": frozen.MIN_BURN_SPREAD,
            },
            "frozen_table_years": list(frozen.YEARS),
            "source": str(frozen.F923.relative_to(ROOT)),
        },
        "frozen_table": {
            "plants": int(len(frozen_tab)),
            "plants_own": int((frozen_tab["v_source"] == "own").sum()),
            "v_cap_wtd": {
                g: _cap_wtd(
                    frozen_tab,
                    "v_usd_mmbtu",
                    np.ones(len(frozen_tab), bool)
                    if g == "__ALL_GAS__"
                    else (frozen_tab["group"] == g),
                )
                for g in list(REPORT_GROUPS) + ["__ALL_GAS__"]
            },
        },
        "years": {},
    }
    for year in args.years:
        frame = frozen.derive((year,))
        panel = frozen.build_panel((year,))
        out, pool = _write(frame, year, args.out_dir)
        rep = summarize(frame, panel, year)
        # Plant-level agreement with the frozen table, where both carry an own rung.
        both = frame.merge(
            frozen_tab[["plant_id", "v_usd_mmbtu", "v_source"]],
            on="plant_id",
            suffixes=("", "_frozen"),
        )
        own_both = both[
            (both["v_source"] == "own") & (both["v_source_frozen"] == "own")
        ]
        rep["own_vs_frozen_own"] = {
            "n_plants": int(len(own_both)),
            "corr": round(
                float(
                    np.corrcoef(
                        own_both["v_usd_mmbtu"], own_both["v_usd_mmbtu_frozen"]
                    )[0, 1]
                ),
                3,
            )
            if len(own_both) > 2
            else None,
            "mean_diff_cap_wtd": _cap_wtd(
                own_both.assign(
                    d=own_both["v_usd_mmbtu"] - own_both["v_usd_mmbtu_frozen"]
                ),
                "d",
                np.ones(len(own_both), bool),
            ),
        }
        rep["files"] = [str(out.relative_to(ROOT)), str(pool.relative_to(ROOT))]
        summary["years"][str(year)] = rep
        print(
            f"{year}: plants {rep['plants_in_table']} own {rep['plants_own']} "
            f"(own cap share {rep['own_cap_share_of_table']:.2f}); v cap-wtd "
            f"CC {rep['v_cap_wtd']['CC_REGULAR']} CT {rep['v_cap_wtd']['CT_PEAKER']} "
            f"ST {rep['v_cap_wtd']['ST_GAS']} all {rep['v_cap_wtd']['__ALL_GAS__']}; "
            f"wedge CC {rep['wedge_burn_wtd']['CC_REGULAR']} all {rep['wedge_burn_wtd']['__ALL_GAS__']}; "
            f"MISO pool {rep['pooled_iso']:+.4f}",
            flush=True,
        )
    args.summary.write_text(json.dumps(summary, indent=1))
    print(f"wrote {args.summary}")


if __name__ == "__main__":
    main()
