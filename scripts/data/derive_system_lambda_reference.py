"""Derive the committed REPORTED-ONLY system-lambda reference part for the status page.

Writes ``frontend/data/backcast/reference/system_lambda.json`` — per (ISO, year) the
operator's own FERC Form 714 Part II Schedule 6 hourly system lambda, summarised to
the annual mean / median and the 12 monthly means (simple hourly means, $/MWh).

Owner ruling 2026-09-27 (soco-82 decision card, verbatim "Intake, reported-only"):
the series is shown beside the model's own price on the Calibration Status page.
SUPERSEDED IN PART 2026-09-28 (owner ruling "Score C3a vs lambda", lane soco-84):
the lambda is now SOCO's C3a/C3b system benchmark, but the gate reads the
load-weighted ``actual_lmp.json`` block (``derive_actual_lmp.py``), never this part;
this part stays a display summary. The Southern Company Energy Auction hour-ahead
line beside it (owner ruling 2026-09-28 "Yes, reported-only") is REPORTED-ONLY.

The part is committed (not built at deploy time) because the Pages deploy reads
committed files only and ``scripts/build_status.py`` is stdlib-only.

Source: ``data/raw/ferc-714/soco_hourly_system_lambda_2019_2025.csv`` through
:func:`market_sim.data.ferc714.load_ferc714_system_lambda` (README in that folder).
The hour grid is converted to the operator's reported clock (fixed UTC-6, the
README's clock finding) before months are cut, so a month is the operator's month.

Usage::

    PYTHONPATH=src .venv/bin/python scripts/data/derive_system_lambda_reference.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))

from market_sim.config.paths import FERC_714_DIR  # noqa: E402
from market_sim.data.ferc714 import load_ferc714_system_lambda  # noqa: E402
from market_sim.config.paths import SOCO_ENERGY_AUCTION_DIR  # noqa: E402
from market_sim.data.soco_energy_auction import load_soco_energy_auction_hourly  # noqa: E402

OUT = _ROOT / "frontend/data/backcast/reference/system_lambda.json"
#: ISO -> the lambda source file (its respondent is the loader's default for SOCO).
SOURCES = {"SOCO": FERC_714_DIR / "soco_hourly_system_lambda_2019_2025.csv"}
#: The operator's reported clock relative to UTC (data/raw/ferc-714/README.md:
#: 24 values on every day incl. DST transitions => a fixed-offset clock).
LOCAL_OFFSET_HOURS = -6


def summarise(iso: str) -> dict:
    """Annual + monthly summary of one ISO's lambda, keyed by year string."""
    import pandas as pd

    L = load_ferc714_system_lambda()
    idx = L.index.tz_convert(None) if L.index.tz is not None else L.index
    s = pd.Series(
        L["system_lambda_usd_mwh"].to_numpy(float),
        index=idx + pd.Timedelta(hours=LOCAL_OFFSET_HOURS),
    )
    out = {}
    for y, g in s.groupby(s.index.year):
        mon = g.groupby(g.index.month).mean()
        out[str(int(y))] = {
            "hours": int(g.size),
            "mean": round(float(g.mean()), 2),
            "median": round(float(g.median()), 2),
            "mon": [round(float(mon.get(m, float("nan"))), 2) for m in range(1, 13)],
        }
    return out


#: ISO -> the operator's own voluntary energy-auction hour-ahead clearing prices
#: (REPORTED-ONLY, owner ruling 2026-09-28 "Yes, reported-only", lane soco-84).
AUCTION_SOURCES = {"SOCO": SOCO_ENERGY_AUCTION_DIR}


def summarise_auction(iso: str) -> dict:
    """Per year: hour-ahead auction mean vs the lambda IN THE SAME CLEARED HOURS.

    The auction clears only in some hours, so a plain annual mean would compare
    different hours; every statistic here is on the intersection of cleared
    hours with the lambda's hours, on the lambda's local clock.
    """
    import numpy as np
    import pandas as pd

    L = load_ferc714_system_lambda()["system_lambda_usd_mwh"]
    a = load_soco_energy_auction_hourly(AUCTION_SOURCES[iso])
    j = pd.concat([a.rename("ha"), L.rename("lam")], axis=1, join="inner").dropna()
    j.index = j.index + pd.Timedelta(hours=LOCAL_OFFSET_HOURS)
    out = {}
    for y, g in j.groupby(j.index.year):
        out[str(int(y))] = {
            "hours": int(g.shape[0]),
            "ha_mean": round(float(g["ha"].mean()), 2),
            "lam_mean_same_hours": round(float(g["lam"].mean()), 2),
            "r": round(float(np.corrcoef(g["ha"], g["lam"])[0, 1]), 2)
            if g.shape[0] > 2
            else None,
        }
    return out


def main() -> None:
    """Write the reference part."""
    isos = {}
    for iso, src in SOURCES.items():
        isos[iso] = {
            "source": str(src.relative_to(_ROOT)),
            "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "series": "FERC Form 714 Part II Schedule 6 hourly system lambda",
            "years": summarise(iso),
        }
        if iso in AUCTION_SOURCES:
            sums = AUCTION_SOURCES[iso] / "SHA256SUMS.txt"
            isos[iso]["energy_auction"] = {
                "status": "REPORTED-ONLY (owner ruling 2026-09-28, soco-84)",
                "series": "Southern Company Energy Auction hour-ahead clearing price "
                "(voluntary auction; cleared hours only)",
                "source": str(AUCTION_SOURCES[iso].relative_to(_ROOT)),
                "sha256sums_sha256": hashlib.sha256(sums.read_bytes()).hexdigest(),
                "years": summarise_auction(iso),
            }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated_by": "scripts/data/derive_system_lambda_reference.py",
                "status": (
                    "display summary; the lambda is SOCO's C3a/C3b benchmark via "
                    "actual_lmp.json since 2026-09-28 (soco-84); the energy auction "
                    "line is REPORTED-ONLY"
                ),
                "isos": isos,
            },
            indent=1,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"wrote {OUT.relative_to(_ROOT)}")


if __name__ == "__main__":
    main()
