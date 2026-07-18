"""NYISO 2018-2021 + H1-2026 holdout LMP-bench intake: build + frozen-row merge.

Owner-authorized 2026-07-13 NYISO validation-ladder-extension + locked-test-
edge DATA intake (session-logged in
``frontend/data/backcast/calibration-complete.json`` ``intake_log``; no LP,
no scoring). Generalizes ``holdout_intake_nyiso_2022_lmp.py`` (which landed
the 2022 block the same way) to the remaining out-of-training years this
session covers:

* 2018, 2019, 2020, 2021 — full calendar years (validation-ladder extension,
  rule 22 tier "validation, extensible backward").
* 2026 — **H1 only** (Jan-Jun). ``mis.nyiso.com`` has not published H2-2026
  yet as of this intake (locked-test edge), so the DA/RT sources for Jul-Dec
  are simply absent; ``derive_actual_lmp.build``'s own dense-8760 assembly
  (``_caiso_densify``) already NaN-pads any hour with no source row, so this
  script does not special-case the padding — it only relaxes the coverage
  gate for 2026 to the H1 window instead of requiring near-100% full-year
  coverage.

Extends the two committed NYISO LMP bench artifacts, leaving every
pre-existing row byte-frozen:

* ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`` — the dense
  hub-mean hourly series; every row for a year already present (2022-2025 at
  minimum; more if this script is re-run after a partial success) is asserted
  byte-identical before the merged frame (sorted by year, hour) is written.
* ``data/raw/_validation-source/actual_lmp.json`` — the NYISO year map gains
  2018/2019/2020/2021/2026 (re-ordered ascending by year); every OTHER ISO's
  block, and every already-present NYISO year, is asserted byte-identical
  before writing.

Sources (staged first; see the workflow
``.github/workflows/holdout-intake-nyiso-2018-2021-h1-2026.yml``):

* DA: ``mis.nyiso.com/public/csv/damlbmp/<YYYYMM>01damlbmp_zone_csv.zip``
  (12 monthly zips per full year, 6 for H1-2026), staged inside
  ``data/raw/lmp-data/NYISO/NYISO_zonal_hourly.zip`` (the builder's expected
  outer DA container — appended to/rebuilt per year, never committed, exactly
  like the 2022 lander).
* RT: ``mis.nyiso.com/public/csv/realtime/<YYYYMM>01realtime_zone_csv.zip``
  in ``data/raw/lmp-data/NYISO/`` (same monthly-zip convention as 2022).

No independent SOM-report price anchor is wired in for these years (the 2022
script's ``SOM_ANCHORS`` are 2022-report-specific numbers this session did
not transcribe from the corresponding 2018-2021 SOM reports within its time
budget); the safety net here is the byte-freeze assertion on every
pre-existing row plus the coverage gate, not an external cross-check. A
follow-up session may add per-year SOM anchors the same way.

Usage::

    python scripts/archive/holdout_intake_nyiso_2018_2021_h1_2026_lmp.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

from derive_actual_lmp import (  # noqa: E402
    OUT,
    build,
)
from market_sim.config import paths  # noqa: E402

HOURLY = paths.CALIBRATION_DIR / "actual_lmp_hourly_NYISO.parquet"
FULL_YEARS = (2018, 2019, 2020, 2021)
PARTIAL_YEAR = 2026
PARTIAL_YEAR_MONTHS = 6  # H1 only


def _coverage(block: pd.DataFrame, kind: str, months: int | None) -> float:
    arr = block[kind].to_numpy(float)
    if months is not None:
        # Restrict the gate to the published window (Jan..months inclusive);
        # `hour` is 0-indexed hour-of-year on the model's non-leap clock.
        month_of_hour = pd.Series(
            pd.date_range("2001-01-01", periods=8760, freq="h")
        ).dt.month.to_numpy()
        mask = month_of_hour <= months
        arr = arr[mask]
    return float(np.mean(~np.isnan(arr)))


def main() -> None:
    committed_hourly = pd.read_parquet(HOURLY)
    committed_json = json.loads(OUT.read_text())
    got_years = sorted(committed_hourly["year"].unique().tolist())

    todo_full = [y for y in FULL_YEARS if y not in got_years]
    todo_partial = [PARTIAL_YEAR] if PARTIAL_YEAR not in got_years else []
    todo = todo_full + todo_partial
    if not todo:
        print(f"{HOURLY} already spans {FULL_YEARS + (PARTIAL_YEAR,)} — nothing to do")
        return

    table, hourly = build(todo, isos=["NYISO"])
    blocks = []
    recs: dict[int, dict] = {}
    for year in todo:
        rec = table.get("NYISO", {}).get(str(year))
        if rec is None:
            sys.exit(f"builder produced no NYISO {year} record — sources not staged?")
        block = hourly["NYISO"][hourly["NYISO"]["year"] == year]
        months = PARTIAL_YEAR_MONTHS if year == PARTIAL_YEAR else None
        gate = 0.95 if year == PARTIAL_YEAR else 0.99
        for kind in ("da", "rt"):
            cov = _coverage(block, kind, months)
            if cov < gate:
                sys.exit(
                    f"{year} {kind} coverage {cov:.3f} < {gate} "
                    f"(window months<= {months or 12}) — incomplete sources"
                )
            print(f"{year} {kind}: coverage {cov:.3f}, annual mean ${rec.get(kind)}")
        blocks.append(block)
        recs[year] = rec

    # ── parquet: append the new blocks, every pre-existing row byte-frozen ──
    merged = (
        pd.concat([committed_hourly, *blocks], ignore_index=True)
        .sort_values(["year", "hour"])
        .reset_index(drop=True)
    )
    key = ["year", "hour"]
    before = committed_hourly.set_index(key).sort_index()
    after = merged.set_index(key).sort_index().loc[before.index]
    if not before.equals(after):
        sys.exit("pre-existing rows would change — refusing to write")
    merged.to_parquet(HOURLY, index=False)
    reread = pd.read_parquet(HOURLY)
    reread_after = reread.set_index(key).sort_index().loc[before.index]
    assert reread_after.equals(before), "post-write verification failed"
    print(
        f"wrote {HOURLY} ({len(merged)} rows, years "
        f"{sorted(set(reread['year'].tolist()))})"
    )

    # ── JSON: add the new NYISO years (ascending); everything else frozen ───
    before_others = {
        iso: json.dumps(v, sort_keys=True)
        for iso, v in committed_json.items()
        if iso != "NYISO"
    }
    before_nyiso_existing = {
        y: json.dumps(v, sort_keys=True) for y, v in committed_json["NYISO"].items()
    }
    nyiso = dict(committed_json["NYISO"])
    for year, rec in recs.items():
        nyiso[str(year)] = rec
    committed_json["NYISO"] = {y: nyiso[y] for y in sorted(nyiso, key=int)}
    after_others = {
        iso: json.dumps(v, sort_keys=True)
        for iso, v in committed_json.items()
        if iso != "NYISO"
    }
    after_nyiso_existing = {
        y: json.dumps(v, sort_keys=True)
        for y, v in committed_json["NYISO"].items()
        if y in before_nyiso_existing
    }
    assert before_others == after_others, "non-NYISO block changed — refusing"
    assert before_nyiso_existing == after_nyiso_existing, (
        "pre-existing NYISO year(s) changed — refusing"
    )
    OUT.write_text(json.dumps(committed_json, indent=2) + "\n")
    print(f"wrote {OUT} (NYISO years {list(committed_json['NYISO'])})")


if __name__ == "__main__":
    main()
