"""Derive the committed REPORTED-ONLY system-lambda reference part for the status page.

Writes ``frontend/data/backcast/reference/system_lambda.json`` — per (ISO, year) the
operator's own FERC Form 714 Part II Schedule 6 hourly system lambda, summarised to
the annual mean / median and the 12 monthly means (simple hourly means, $/MWh).

Owner ruling 2026-09-27 (soco-82 decision card, verbatim "Intake, reported-only"):
the series is shown beside the model's own price on the Calibration Status page and
feeds NO gate, NO scorer path and NO LP. A system lambda is the operator's reported
marginal cost of its own economic dispatch, not an LMP, so it is never a C3
benchmark here (rubric v3.8's no-price class stands for SOCO).

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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated_by": "scripts/data/derive_system_lambda_reference.py",
                "status": "REPORTED-ONLY (owner ruling 2026-09-27, soco-82)",
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
