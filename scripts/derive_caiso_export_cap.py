#!/usr/bin/env python3
"""Derive the CAISO aggregate WECC export-direction cap from measured interchange.

Re-derivation of ``transmission.CAISO_BIDIR_EXPORT_CAP_MW`` (2026-07 scalar
remediation, audit item C-14). The legacy value (3,500 MW) was a hand-fitted
"measured export-direction peak" read off the EIA-930 CISO net-interchange
curve ("~+3.5 GW in the midday solar glut") — a fitted level, not a reproducible
capability ceiling. This script re-grounds it on the SAME measured series the
caiso-51 keeper's per-hub corridor export envelopes already use
(``eia_loader.measured_corridor_flow_envelope(direction="export")``), so the
superseded single-aggregate ``caiso_bidir_intertie`` fallback and the live
per-hub successor share one measured convention (rule #19).

**Why not OASIS ATC directly.** The scalar-remediation plan names the "OASIS
export-direction ATC envelope" as the source. The Claude remote environment
cannot reach ``oasis.caiso.com`` (see ``.github/workflows/fetch-caiso-oasis.yml``);
the realized ATC proxy already on disk is the EIA-930 BA-to-BA net interchange
(``eia_loader.measured_corridor_flow_envelope`` docstring: "This is an ATC
proxy"). We use that on-disk measured series and cite it; refreshing against a
true OASIS export-ATC pull is left as an open follow-up (the fetch workflow
exists but runs on a GitHub runner).

**rule-23 source-data change.** The citable trigger is the caiso-51 keeper
(registry id ``2026-07-03-caiso-51-firm-base``), which landed the measured
per-hub corridor export-deliverability envelopes that supersede the fitted
scalar. This derive commit cites that keeper, not a residual.

**Methodology.** For each hour 2023-2025 (the 2022 / H1-2026 holdouts are
EXCLUDED — rule #22), sum EIA-930 CISO interchange across all 11 neighboring
balancing areas into one system net export (EIA sign: ``+`` = CISO exports to
the DIBA, so aggregate net export = ``sum(mw)``). The single aggregate cap is
the capability ceiling at the *peak export bucket*: the maximum over all
(month, hour-of-day) buckets of that bucket's ``CAISO_CORRIDOR_FLOW_PERCENTILE``
(p95) net export. This is exactly the per-(month, hod) p95 convention the
corridor flow envelopes use, reduced to one aggregate ceiling by taking the
binding (peak) bucket — a capability limit the LP clears below (rule #12), not
the fitted "typical peak day" the 3,500 encoded.

Run: ``python scripts/derive_caiso_export_cap.py`` — writes nothing; prints the
value to hand-copy into ``transmission.CAISO_BIDIR_EXPORT_CAP_MW`` after review
(the frozen-derive-script convention, rule #23: a reviewed, cited commit, not an
automatic write).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config.interchange_config import (
    CAISO_CORRIDOR_DIBA,
    CAISO_CORRIDOR_FLOW_PERCENTILE,
)
from market_sim.config.paths import RAW_DIR

# Holdout quarantine (rule #22): only in-sample calibration years may be scored.
DERIVE_YEARS = (2023, 2024, 2025)


def derive_export_cap_mw() -> float:
    """Return the measured aggregate CAISO WECC export-direction cap (MW).

    Reads ``data/raw/eia-930-interchange/CISO interchange hourly.parquet``,
    restricts to :data:`DERIVE_YEARS`, aggregates net export across all CISO
    DIBAs, and returns the peak-bucket :data:`CAISO_CORRIDOR_FLOW_PERCENTILE`
    net export (max over month x hour-of-day buckets).
    """
    path = RAW_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    frame = pd.read_parquet(path)
    local = pd.DatetimeIndex(frame["local_time"])
    mask = np.isin(local.year, DERIVE_YEARS)
    frame = frame.loc[mask].copy()
    frame["mw"] = pd.to_numeric(frame["mw"], errors="coerce")
    # Sanity: flag any DIBA missing from the corridor map. The single aggregate
    # cap sums every DIBA regardless (it is system-wide), but a gap here would
    # also silently under-count the per-corridor envelopes, so surface it.
    unmapped = sorted(set(frame["diba"].astype(str)) - set(CAISO_CORRIDOR_DIBA))
    if unmapped:
        print(f"NOTE: DIBAs not in CAISO_CORRIDOR_DIBA (still summed): {unmapped}")
    agg = frame.groupby("local_time")["mw"].sum().rename("net_export")
    idx = pd.DatetimeIndex(agg.index)
    buck = agg.groupby([idx.month, idx.hour]).apply(
        lambda v: float(np.percentile(v.to_numpy(), CAISO_CORRIDOR_FLOW_PERCENTILE))
    )
    peak_month, peak_hod = buck.idxmax()
    cap = float(buck.max())
    print(
        f"years                {list(DERIVE_YEARS)}  "
        f"({len(agg)} hours, 2026 holdout excluded)"
    )
    print(
        f"percentile           p{CAISO_CORRIDOR_FLOW_PERCENTILE:g} (per month x hod bucket)"
    )
    print(f"peak export bucket   month={peak_month}, hour-of-day={peak_hod}")
    print(
        f"aggregate p99        {float(np.percentile(agg, 99)):8.1f} MW  (legacy 3,500 ~ p99)"
    )
    print(
        f"CAISO_BIDIR_EXPORT_CAP_MW = {round(cap, 1)}  MW  <- copy into transmission.py"
    )
    return cap


if __name__ == "__main__":
    derive_export_cap_mw()
