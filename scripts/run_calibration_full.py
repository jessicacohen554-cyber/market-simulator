"""Calibration backcast: solve, persist, and report off persisted parquet.

Each run solves the dispatch for the requested years (and the P2 commitment
pass when ``--commitment`` is set), writes the full hourly per-plant results
to a timestamped parquet bundle, and then computes the comparison report from
that bundle. Nothing is lost: the bundle is the source of truth and can be
re-queried for any ad-hoc analysis, and re-running never overwrites a prior
run (each lands in its own timestamped directory). Bundles are scoped by ISO
so backcasts for different ISOs run in parallel without colliding.

A run bundle lives in ``results/calibration/<iso>/<timestamp>/`` and holds:

  * ``dispatch/<year>_<pass>.parquet`` PLACEHOLDER
"""
