"""NYISO 2022 holdout LMP-bench intake: build + frozen-row merge (rule 22).

Owner-authorized 2026-07-12 NYISO 2022 validation-holdout DATA intake
(session-logged in ``frontend/data/backcast/calibration-complete.json``
``intake_log``; no LP, no scoring). Extends the two committed NYISO LMP bench
artifacts with a 2022 block, leaving every in-sample (2023-2025) row
byte-frozen:

* ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`` — the dense
  hub-mean hourly series; the committed 2023-2025 rows are asserted unchanged
  and the 2022 block is APPENDED (the NYISO builder cannot rebuild 2023-2025
  here: their DA source zips are staged out of the repo — the committed
  parquet is the durable record, per ``derive_actual_lmp.build``'s docstring).
* ``data/raw/_validation-source/actual_lmp.json`` — the NYISO year map gains
  ``2022`` (re-ordered ascending); every OTHER ISO's block is asserted
  byte-identical before writing.

The 2022 numbers come from the exact committed derivation
(``scripts/derive_actual_lmp.py`` ``_nyiso``/``build``) run on the same MIS
source lineage as the committed 2023-2025 years:

* DA: ``mis.nyiso.com/public/csv/damlbmp/2022MM01damlbmp_zone_csv.zip``
  (12 monthly zips), staged inside ``data/raw/lmp-data/NYISO/
  NYISO_zonal_hourly.zip`` (the builder's expected outer container; the
  container itself stays out of git exactly like the 2023-2025 one).
* RT: ``mis.nyiso.com/public/csv/realtime/2022MM01realtime_zone_csv.zip``
  (12 monthly zips) in ``data/raw/lmp-data/NYISO/`` (the committed years'
  naming convention).

Independent cross-check: the derived per-model-zone ANNUAL means are anchored
against the NYISO 2022 State of the Market report's published 2022 averages
(``SOM_ANCHORS`` — Figure A-2 load-weighted DA LBMP by region + the Executive
Summary RT range), an MMU-computed publication independent of this parser.
The SOM numbers are load-weighted while ours are equal-hour, so the gate is a
ratio band, not equality. (The ``dartmonthlylmpindex_*.csv`` files that look
like a NYISO monthly index are actually ISO-NE reports — including the copies
misfiled under ``lmp-data/NYISO/`` — so no NYISO-published machine-readable
monthly index exists in-repo; see the register note.)

``frontend/data/backcast/tail/actual_tail.json`` is deliberately NOT touched:
``derive_actual_tail.py`` is marker-aware and will emit the NYISO 2022 row
from the extended parquet automatically once (and only once) the NYISO
calibration-complete marker exists — the data is ready, the emission is
marker-gated by design.

Usage (sources staged first; see the workflow
``.github/workflows/holdout-intake-nyiso-2022.yml``)::

    python scripts/holdout_intake_nyiso_2022_lmp.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from derive_actual_lmp import (  # noqa: E402
    NYISO_ZONE_MAP,
    OUT,
    build,
)
from market_sim.config import paths  # noqa: E402

HOURLY = paths.CALIBRATION_DIR / "actual_lmp_hourly_NYISO.parquet"
IN_SAMPLE_YEARS = (2023, 2024, 2025)
YEAR = 2022

#: Independent published anchors — NYISO 2022 State of the Market report
#: (Potomac Economics, 2023-05-16; the SAME document family the committed
#: nyiso_som_hub_fuel_annual.csv transcribes). Figure A-2 (p. A-9) table:
#: 2022 annual LOAD-WEIGHTED average day-ahead LBMP by region; Executive
#: Summary (p. ii): 2022 real-time averages "from $50.46 per MWh in the North
#: Zone to $108 per MWh in Long Island". Our derived means are EQUAL-HOUR, so
#: they sit systematically BELOW the load-weighted anchors (high-load hours
#: price higher, and 2022's winter tails amplify the wedge); the gate is a
#: level anchor, not an equality: derived/anchor must fall in
#: ``ANCHOR_BAND`` for every 1:1-mappable zone. Catches unit/zone/parse
#: errors an in-lineage rerun cannot.
SOM_ANCHORS: dict[tuple[str, str], float] = {
    ("NYC", "da"): 89.07,  # Fig A-2, NYC (Zone J)
    ("Long_Island", "da"): 104.02,  # Fig A-2, LI (Zone K)
    ("Capital_Hudson", "da"): 100.13,  # Fig A-2, Capital (Zone F)
    ("Long_Island", "rt"): 108.0,  # Exec Summary p. ii
}
ANCHOR_BAND = (0.80, 1.02)


def cross_check(rec: dict) -> None:
    """Derived 2022 zone annual means vs the published SOM 2022 anchors."""
    assert set(z for z, _ in SOM_ANCHORS) <= set(NYISO_ZONE_MAP)
    for (zone, kind), anchor in SOM_ANCHORS.items():
        mine = float(rec["zones"][zone][kind])
        ratio = mine / anchor
        status = "PASS" if ANCHOR_BAND[0] <= ratio <= ANCHOR_BAND[1] else "FAIL"
        print(
            f"cross-check {zone}/{kind}: derived equal-hour ${mine:.2f} vs "
            f"SOM-2022 load-weighted ${anchor:.2f} (ratio {ratio:.3f}) {status}"
        )
        if status == "FAIL":
            sys.exit("SOM anchor cross-check failed — refusing to write")


def main() -> None:
    committed_hourly = pd.read_parquet(HOURLY)
    committed_json = json.loads(OUT.read_text())
    got_years = sorted(committed_hourly["year"].unique().tolist())
    if got_years != list(IN_SAMPLE_YEARS):
        if YEAR in got_years:
            print(f"{HOURLY} already spans {YEAR} — nothing to do")
            return
        sys.exit(f"unexpected committed years {got_years}")

    table, hourly = build([YEAR], isos=["NYISO"])
    rec = table.get("NYISO", {}).get(str(YEAR))
    if rec is None:
        sys.exit("builder produced no NYISO 2022 record — sources not staged?")
    block = hourly["NYISO"]
    for kind in ("da", "rt"):
        cov = float(np.mean(~np.isnan(block[kind].to_numpy(float))))
        if cov < 0.99:
            sys.exit(f"2022 {kind} coverage {cov:.3f} < 0.99 — incomplete sources")
        print(f"2022 {kind}: coverage {cov:.3f}, annual mean ${rec[kind]}")

    cross_check(rec)

    # ── parquet: append the 2022 block, in-sample rows byte-frozen ──────────
    merged = pd.concat([committed_hourly, block], ignore_index=True)
    head = merged.iloc[: len(committed_hourly)].reset_index(drop=True)
    if not head.equals(committed_hourly.reset_index(drop=True)):
        sys.exit("in-sample rows would change — refusing to write")
    merged.to_parquet(HOURLY, index=False)
    reread = pd.read_parquet(HOURLY)
    assert (
        reread.iloc[: len(committed_hourly)]
        .reset_index(drop=True)
        .equals(committed_hourly.reset_index(drop=True))
    ), "post-write verification failed"
    print(
        f"wrote {HOURLY} ({len(merged)} rows, years "
        f"{sorted(set(reread['year'].tolist()))})"
    )

    # ── JSON: add NYISO 2022 (ascending), all other ISOs byte-identical ─────
    before_others = {
        iso: json.dumps(v, sort_keys=True)
        for iso, v in committed_json.items()
        if iso != "NYISO"
    }
    nyiso = dict(committed_json["NYISO"])
    nyiso[str(YEAR)] = rec
    committed_json["NYISO"] = {y: nyiso[y] for y in sorted(nyiso)}
    after_others = {
        iso: json.dumps(v, sort_keys=True)
        for iso, v in committed_json.items()
        if iso != "NYISO"
    }
    assert before_others == after_others, "non-NYISO block changed — refusing"
    OUT.write_text(json.dumps(committed_json, indent=2) + "\n")
    print(f"wrote {OUT} (NYISO years {list(committed_json['NYISO'])})")


if __name__ == "__main__":
    main()
