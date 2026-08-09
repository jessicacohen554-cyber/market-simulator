"""miso-145 probe — G-A coverage/structure verdicts for the MISO offer corpus.

PREREG ``results/calibration/PREREG-miso145-summer-offer-conduct-2026-08-09.md``
§3, predictions **P-A1 … P-A5**.  Structural checks only: file availability,
unit and row counts, hour grain, the absence of any fuel/technology attribute,
masked-ID persistence, and offer-curve monotonicity.  **No conduct statistic,
no price level, no aggregate supply curve** — those are ``_miso145_offer_conduct.py``.

Reads the immutable raw mirror (``data/raw/miso-energy-offers/``) and its
``manifest.json`` directly, so the verdicts are about the SOURCE and cannot be
laundered through the curation step.

Probe hygiene (miso-140b §6): repo root on ``sys.path``, ``load_zonal_shares``
asserted non-None via ``_miso143_stack.hygiene``.

Usage::

    python scripts/probes/_miso145_coverage.py [--out results/calibration/_miso145_coverage.json]
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso143_stack import hygiene  # noqa: E402
from market_sim.config import paths  # noqa: E402

YEARS = (2023, 2024, 2025)
MARKETS = ("da", "rt")
#: P-A3 — the absence assertion under test, re-verified on the full landed span.
FUEL_PAT = re.compile(r"fuel|type|technolog", re.IGNORECASE)
#: Sample days per (year, market) for the row-level structural checks.
SAMPLE_DAYS = ("0601", "0715", "0831")


def _read(path: Path) -> pd.DataFrame:
    """Return the single CSV member of one daily ``*_co.zip``."""
    with zipfile.ZipFile(path) as z:
        return pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), low_memory=False)


def _header(path: Path) -> list[str]:
    """Return the header field names of one daily zip without parsing the body."""
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as fh:
            return fh.readline().decode("utf-8-sig").strip().split(",")


def run(out_path: Path | None = None) -> dict:
    """Execute P-A1 … P-A5 and return the verdict record."""
    hygiene()
    root = paths.MISO_ENERGY_OFFERS_DIR
    manifest = json.loads((root / "manifest.json").read_text())
    rows = manifest["files"]

    # ---------------------------------------------------- P-A1 availability
    ok = [r for r in rows if r["status"] in ("fetched", "cached")]
    p_a1 = {
        "n_requested": len(rows),
        "n_ok": len(ok),
        "frac_ok": round(len(ok) / max(1, len(rows)), 4),
        "n_members_not_1": sum(1 for r in ok if r.get("n_members") != 1),
        "total_mb": round(sum(r.get("bytes", 0) for r in ok) / 1e6, 1),
        "bad": [
            {"market": r["market"], "day": r["day"], "status": r["status"]}
            for r in rows
            if r["status"] not in ("fetched", "cached")
        ],
        "PASS": len(ok) / max(1, len(rows)) >= 0.99,
    }

    # ------------------------------------- P-A3 absence of any fuel/type field
    fuel_hits: dict[str, list[str]] = {}
    headers: dict[str, list[str]] = {}
    for market in MARKETS:
        for p in sorted((root / market).glob(f"*_{market}_co.zip")):
            cols = _header(p)
            headers.setdefault(market, cols)
            hits = [c for c in cols if FUEL_PAT.search(c)]
            if hits:
                fuel_hits[p.name] = hits
    p_a3 = {
        "n_files_scanned": sum(
            len(list((root / m).glob(f"*_{m}_co.zip"))) for m in MARKETS
        ),
        "files_with_fuel_like_column": fuel_hits,
        "da_header": headers.get("da", []),
        "rt_header": headers.get("rt", []),
        "PASS": not fuel_hits,
    }

    # ------------------------- P-A2 / P-A5 / duplicates, on the sample days
    per_day: list[dict] = []
    for market in MARKETS:
        ts_col = (
            "Date/Time Beginning (EST)" if market == "da" else "Mkthour Begin (EST)"
        )
        for year in YEARS:
            for mmdd in SAMPLE_DAYS:
                p = root / market / f"{year}{mmdd}_{market}_co.zip"
                if not p.exists():
                    continue
                df = _read(p)
                mw = df[[f"MW{i}" for i in range(1, 11)]].to_numpy(float)
                pr = df[[f"Price{i}" for i in range(1, 11)]].to_numpy(float)
                d_mw, d_pr = np.diff(mw, axis=1), np.diff(pr, axis=1)
                both = np.isfinite(d_mw) & np.isfinite(d_pr)
                dup = int(df.duplicated(subset=["Unit Code", ts_col]).sum())
                per_day.append(
                    {
                        "market": market,
                        "day": f"{year}{mmdd}",
                        "n_rows": int(len(df)),
                        "n_units": int(df["Unit Code"].nunique()),
                        "n_hours": int(df[ts_col].nunique()),
                        "regions": sorted(df["Region"].dropna().unique().tolist()),
                        "n_h12_17_rows": int(
                            pd.to_datetime(df[ts_col], format="%m/%d/%Y %H:%M:%S")
                            .dt.hour.between(12, 17)
                            .sum()
                        ),
                        "dup_unit_hour_rows": dup,
                        "dup_are_exact_copies": bool(
                            dup == int(df.duplicated().sum())
                        ),
                        "mw_monotone_frac": round(
                            float((d_mw[both] >= -1e-9).mean()), 5
                        ),
                        "price_monotone_frac": round(
                            float((d_pr[both] >= -1e-9).mean()), 5
                        ),
                    }
                )

    p_a2 = {
        "per_day": per_day,
        "units_min": min(d["n_units"] for d in per_day),
        "units_max": max(d["n_units"] for d in per_day),
        "rows_min": min(d["n_rows"] for d in per_day),
        "rows_max": max(d["n_rows"] for d in per_day),
        "all_24_hours": all(d["n_hours"] == 24 for d in per_day),
        "h12_17_populated_everywhere": all(d["n_h12_17_rows"] > 0 for d in per_day),
        "PASS": (
            all(900 <= d["n_units"] <= 1600 for d in per_day)
            and all(d["n_hours"] == 24 for d in per_day)
            and all(d["n_h12_17_rows"] > 0 for d in per_day)
        ),
    }
    p_a5 = {
        "mw_monotone_frac_min": min(d["mw_monotone_frac"] for d in per_day),
        "price_monotone_frac_min": min(d["price_monotone_frac"] for d in per_day),
        "PASS": (
            min(d["mw_monotone_frac"] for d in per_day) >= 0.99
            and min(d["price_monotone_frac"] for d in per_day) >= 0.99
        ),
    }

    # --------------------------------------- P-A4 within-year ID persistence
    persist: dict[str, dict] = {}
    for market in MARKETS:
        for year in YEARS:
            a = root / market / f"{year}0601_{market}_co.zip"
            b = root / market / f"{year}0831_{market}_co.zip"
            if not (a.exists() and b.exists()):
                continue
            ua = set(_read(a)["Unit Code"].astype(str))
            ub = set(_read(b)["Unit Code"].astype(str))
            persist[f"{market}|{year}"] = {
                "n_jun01": len(ua),
                "n_aug31": len(ub),
                "overlap_frac_of_jun01": round(len(ua & ub) / max(1, len(ua)), 4),
            }
    p_a4 = {
        "per_market_year": persist,
        "min_overlap": round(
            min(v["overlap_frac_of_jun01"] for v in persist.values()), 4
        ),
        "PASS": all(v["overlap_frac_of_jun01"] >= 0.90 for v in persist.values()),
    }

    result = {
        "prereg": "results/calibration/PREREG-miso145-summer-offer-conduct-2026-08-09.md",
        "gate": "G-A intake coverage (P-A1..P-A5); structural checks only",
        "source": manifest["source"],
        "span": "Jun 1 - Aug 31, 2023/2024/2025, both markets (rule 22: no year outside 2023-2025)",
        "P_A1_availability": p_a1,
        "P_A2_grain": p_a2,
        "P_A3_no_fuel_attribute": p_a3,
        "P_A4_id_persistence": p_a4,
        "P_A5_curve_monotonicity": p_a5,
    }
    if out_path:
        out_path.write_text(json.dumps(result, indent=1))
    return result


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out", default="results/calibration/_miso145_coverage.json", type=Path
    )
    args = ap.parse_args()
    res = run(out_path=args.out)
    for k, v in res.items():
        if isinstance(v, dict) and "PASS" in v:
            print(f"{k}: {'PASS' if v['PASS'] else 'FAIL'}")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
