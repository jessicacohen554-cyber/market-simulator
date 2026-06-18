"""Calibration backcast: solve, persist, and report off persisted parquet.

Each run solves the dispatch for the requested years (and the P2 commitment
pass when ``--commitment`` is set), writes the full hourly per-plant results
to a timestamped parquet bundle, and then computes the comparison report from
that bundle. Nothing is lost: the bundle is the source of truth and can be
re-queried for any ad-hoc analysis, and re-running never overwrites a prior
run (each lands in its own timestamped directory). Bundles are scoped by ISO
so backcasts for different ISOs run in parallel without colliding.

A run bundle lives in ``results/calibration/<iso>/<timestamp>/`` and holds:

  * ``dispatch/<year>_<pass>.parquet`` — every generator's hourly MW (8760h)
    with plant_code / class / fuel / supply / zone metadata, plus wind and
    solar as per-zone pseudo-units. Coal carries its supply class
    (COAL_LIGNITE / COAL_PRB) so mine-mouth and PRB can be separated.
  * ``system.parquet`` — per-zone hourly price, load slack and demand target,
    for every year and pass.
  * ``eia930.parquet`` — EIA-930 hourly benchmark series (gas, coal, wind,
    solar, nuclear, net generation).
  * ``eia923.parquet`` — EIA-923 net generation per (plant, class), annual and
    by month.
  * ``btm.parquet`` — behind-the-meter CHP must-run by class (off-grid).
  * ``meta.json`` — run metadata (timestamp, years, passes, flags, prices).

The report ([1]-[6] tables) is then computed entirely from the bundle, so the
same numbers can be reproduced from an old run with ``--report <dir>``.

Usage:
    python scripts/run_calibration_full.py --year 2023 2024
    python scripts/run_calibration_full.py --year 2023 --commitment --no-coal-p2
    python scripts/run_calibration_full.py --report results/calibration/<iso>/<ts>
"""
