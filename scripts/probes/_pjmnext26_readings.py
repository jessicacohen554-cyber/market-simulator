"""PJM-NEXT-26 (zero LP): the PRECOMMIT's S1 / S2 / P1 readings, candidate vs controls.

The PJM-NEXT-25 PRECOMMIT fixes the readings; the PJM-NEXT-26 addendum fixes the
control (the W0 PJM legs, single delta) and the reported comparison (the incumbent
keeper, W0 + rows). For every year and every bundle that carries it:

- **S1**: slack + dump TWh (``system_<y>.parquet``, P1).
- **P1**: COAL_BIT P1 TWh (``class_hourly_<y>.parquet``).
- **S2**: the within-plant loading contrast (``_pjmnext24_within_across.within`` on
  the actual-RT margin) of the cohort the arm changes: the 18 plants whose COAL rows
  PJM-NEXT-25 appended (they were the default-bin cohort before the append), and the
  same contrast for the real fleet, read on each bundle's own ``unit_marginal`` layer.

Writes ``results/phase0/pjm/_pjmnext26_readings.json``.
Run: ``python3 scripts/probes/_pjmnext26_readings.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext24_loading_margin as lm  # noqa: E402
from _pjmnext24_within_across import within  # noqa: E402

CAL = REPO / "results/calibration"
OUT = REPO / "results/phase0/pjm/_pjmnext26_readings.json"
#: PRECOMMIT-pjm-next-25 §1: the 18 plants whose measured COAL rows were appended.
APPENDED = (
    594, 883, 884, 1554, 1571, 1572, 1573, 2836, 2840,
    2866, 3122, 3140, 3149, 3797, 6019, 8226, 10678, 54304,
)  # fmt: skip
YEARS = range(2019, 2026)


def bundle_hourly(name: str, year: int) -> Path | None:
    """The ``hourly/`` dir carrying ``year`` for bundle family ``name``, if on disk."""
    if name == "candidate":
        d = CAL / "pjm_next_26_span/hourly"
    elif name == "keeper":
        d = CAL / "pjmnext16_A_span/hourly"
    else:
        d = CAL / f"w0_pjm_{year}/hourly"
    return d if (d / f"unit_marginal_{year}.parquet").is_file() else None


def system_twh(hourly: Path, year: int) -> dict:
    """Slack + dump TWh and COAL_BIT TWh for one year of one bundle (P1)."""
    s = pd.read_parquet(hourly / f"system_{year}.parquet")
    if "pass" in s:
        s = s[s["pass"].astype(str) == "P1"]
    c = pd.read_parquet(hourly / f"class_hourly_{year}.parquet")
    if "pass" in c:
        c = c[c["pass"].astype(str) == "P1"]
    coal = c[c.klass.astype(str) == "COAL_BIT"].mw.sum()
    return {
        "slack_dump_twh": round(float(s.slack.sum() + s.dump.sum()) / 1e6, 4),
        "coal_bit_twh": round(float(coal) / 1e6, 2),
    }


def cohort(hourly: Path, year: int, act: pd.DataFrame) -> dict:
    """Within-plant contrast, model vs real, for the appended cohort and the rest."""
    lm.HOURLY = hourly
    p = lm.plant_hours(year, act)
    p = p[p.k == "COAL"]
    out = {}
    for tag, g in (
        ("appended", p[p.plant_code.isin(APPENDED)]),
        ("rest", p[~p.plant_code.isin(APPENDED)]),
    ):
        out[tag] = {
            "plants": int(g.plant_code.nunique()),
            "model_twh": round(float(g.mw.sum()) / 1e6, 2),
            "real_twh": round(float(g.real.sum()) / 1e6, 2),
            "within_contrast_rt": within(g, "m_rt") if len(g) else None,
        }
    return out


def main() -> None:
    """Every year, every bundle on disk."""
    act = pd.read_parquet(lm.ACTUAL)
    res: dict = {"what": __doc__.splitlines()[0], "appended": APPENDED, "years": {}}
    for y in YEARS:
        row = {}
        for name in ("candidate", "w0_control", "keeper"):
            h = bundle_hourly(name, y)
            if h is None:
                row[name] = None
                continue
            row[name] = {**system_twh(h, y), "cohort": cohort(h, y, act)}
        res["years"][str(y)] = row
        print(y, json.dumps(row, default=str)[:900], flush=True)
    OUT.write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
