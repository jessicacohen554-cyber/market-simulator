# MISO HSL (uncurtailed renewable potential) — DATA NEEDED

This directory is intentionally empty. MISO publishes wind & solar curtailment
in its Market Reports, but those reports live on misoenergy.org, which is
**allowlist-blocked from the build environment (HTTP 403)**, so no reproducible
hourly uncurtailed-potential (HSL) series could be built. Re-checked
2026-07-05 (L1 audit closure, docs/model-legitimacy-audit-2026-07.md §4):
`misoenergy.org` and `cdn.misoenergy.org` both still return HTTP 403.

Until a curtailment series can be pulled, the MISO backcast uses EIA-930 MISO
delivered wind/solar generation (which embeds the historical curtailment);
`market_sim.data.renewables._hsl_file` returns the parquet below when present,
else `None`.

To populate (when misoenergy.org is reachable): download the MISO "Wind & Solar
Curtailment" reports for 2023-2025, then build per-year parquets following
`scripts/build_caiso_hsl.py` with `HSL = EIA-930 delivered + reported
curtailment` (schema `renewables._HSL_COLUMNS`):

    data/raw/miso-hsl/miso_<year>_hsl_hourly.parquet

The loader picks them up automatically.
