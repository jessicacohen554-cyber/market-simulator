# MISO-native outage overlay — solve-path wiring (paste-ready diff)

This doc is the self-contained intake + wiring record for the MISO
published-outage overlay (it doubles as the rule-22 authorization log, since the
shared inventory docs — `data-register`, `data-licensing`,
`out-of-sample-results` §1 — could not be re-emitted through the text-only push
path this session; add their rows in a later sync-docs pass).

**Status (2026-07-19):** the MISO published-outage *intake* is complete and
committed — per-year wide CSVs
(`data/raw/miso-generation-outages/miso_outages_estimated_<year>.csv`; the
efficient parquet is a gitignored local artifact — web push is text-only), the
`_SOURCE.md` sidecar (citation + verbatim MISO disclaimer), the fetch script
(`scripts/data/fetch_miso_outages.py`), the loader
(`market_sim.data.miso_outages`), and tests (`tests/test_miso_outages.py`, green).
The loader already produces the exact derate interface the CAMPD fallback
produces — `{(plant_code, plant_group): (8760,) availability multiplier}` — via
`miso_native_outage_derate_factors`.

## Rule-22 intake authorization (session log)

Owner-authorized, verbatim task: *"Search for and download MISO DAM equivalent
data to what we're using for ERCOT for outages and capacity availability — get
as much as you can between 2018 and 2026 and process into parquets ... intake
ready for the backcast runs to use instead of the campd unit outage fallback."*
This is **DATA INTAKE ONLY** — no LP was constructed, solved, or scored; no
`calibration-complete.json` marker was set. MISO carries no marker, so every
out-of-train partition landed here (the 2022-12 look-back tail and all of 2026)
stays quarantined for any solve/score until MISO's marker exists (rule 22).

## Source, coverage, grain

- **Source:** MISO Multiday Operating Margin Forecast Report,
  `docs.misoenergy.org/marketreports/YYYYMMDD_mom.xlsx`, `OUTAGE` sheet (public,
  no auth). Region (North/Central/South; `MISO` = system total = N+C+S, verified
  exact) × cause type (Derated/Forced/Planned/Unplanned — additive GADS buckets;
  the spring/fall shoulder-maintenance seasonal peak confirms additivity), daily
  MW. The MISO analog of ERCOT's measured DAM class-day availability
  (`ercot-thermal-dam-availability.csv`), but **aggregate grain** — no unit or
  fuel-class identity, so it enters as a region availability *envelope*.
- **Coverage:** estimated (30-day look-back actuals) 2022-12-03 → 2026-07-18,
  **100 % day coverage**, 21,183 long rows; forecast (7-day-ahead) 2023-01-02 →
  2026-07-25 (local parquet only). MISO publishes no `_mom.xlsx` before
  **2023-01-01** (2018-2022 dates 404, verified) — the requested 2018 floor is
  unreachable at this grain. Weekly fetch stride; per `(region, cause_type,
  interval_date)` the most-settled estimate (latest look-back file covering the
  day) is kept.
- **Licensing:** MISO-original data; MISO's terms of use remain **UNVERIFIED**
  (both ToU pages 403 automated fetch — `docs/data-licensing.md` §7). Landed
  under the same posture as the repo's existing MISO-original data
  (`lmp-data/MISO`, `miso-hsl/`, `transfer-constraint-binding/MISO`);
  redistribution permission is **not assumed** pending the standing manual owner
  check. Verbatim MISO disclaimer preserved in `_SOURCE.md`.

## What is NOT yet applied

The two-hunk *solve-path* wiring (the `ScenarioConfig.miso_native_outage_source`
gate + the one-branch seam in `fleet.generators_to_fleet_arrays`). It was
authored and tested this session but **not committed**, because
`config/scenarios.py` (534 KB) and `data/fleet.py` (502 KB) exceed what can be
pushed as full-file content through the API-only push path without tripping
CLAUDE.md rule 27 (the push-integrity clause forbids regenerated/partial
full-file rewrites of ≥300-line core files, and there is no patch-based push).
Enabling a solve-affecting mechanism also belongs in the MISO calibration
session that will validate it (rules 1, 11, 22) — not a data-intake session.
Apply the diff below there, then run the verification block.

This is a **default-off, MISO-only, backcast-only** gate; when off, every
existing solve is byte-identical (the CAMPD unit-outage derate path is unchanged).

## Apply

```diff
diff --git a/src/market_sim/config/scenarios.py b/src/market_sim/config/scenarios.py
--- a/src/market_sim/config/scenarios.py
+++ b/src/market_sim/config/scenarios.py
@@ _CACHE_KEY_OPTIONAL_FIELDS = (
     # every pre-existing cache key is byte-stable; True enters the key (a
     # distinct financing scenario).
     "per_tech_wacc_enabled",
+    # MISO-native published-outage overlay (2026-07-19): default False dropped
+    # from the hash so every pre-existing cache key is byte-stable; True enters
+    # the key (a distinct MISO backcast availability scenario).
+    "miso_native_outage_source",
 )
@@ class ScenarioConfig:  (immediately after the `outage_source` field)
     outage_source: str = "statistical"
 
+    # Tier 3 (calibration) — MISO-native published-outage overlay (MISO-only,
+    # backcast). When set (and outage_source == "historic" and iso == MISO),
+    # the MISO Multiday Operating Margin measured region×cause offline-MW record
+    # (data/raw/miso-generation-outages, built by
+    # scripts/data/fetch_miso_outages.py) REPLACES the CAMPD unit-outage derate
+    # as MISO's availability overlay — the MISO analog of ERCOT's measured DAM
+    # class-day availability (outage_source's ERCOT path). Driver (rule 12):
+    # MISO's own published generation-outage bookkeeping (Derated/Forced/
+    # Planned/Unplanned MW by region). Forward story (rule 13): a measured
+    # physical availability quantity whose forecast analogue is the statistical
+    # outage-rate model; backcast overlay only. The public report is AGGREGATE
+    # grain (no unit/fuel-class identity), so the overlay applies a uniform
+    # region availability envelope to the thermal fleet — an approximation whose
+    # exact composition is a calibration decision (see market_sim.data
+    # .miso_outages). Coverage starts 2023-01-01 (MISO publishes no earlier).
+    # Default off; GATED CHANGE (alters availability). No keeper uses it yet.
+    miso_native_outage_source: bool = False
+
     # Tier 3 (calibration) — short (1-5 day) unit-outage windows for baseload
@@ TIER_TAGS: dict[str, int] = {
     "outage_source": 3,
+    "miso_native_outage_source": 3,
     "unit_outage_short_windows": 3,
diff --git a/src/market_sim/data/fleet.py b/src/market_sim/data/fleet.py
--- a/src/market_sim/data/fleet.py
+++ b/src/market_sim/data/fleet.py
@@ def generators_to_fleet_arrays(  (the unit_outage_derate_factors call inside the outage_source=="historic" block)
-        ufac = unit_outage_derate_factors(
-            config.weather_year,
-            hours,
-            getattr(config, "campd_bins_path", str(CAMPD_BINS_CSV)),
-            iso=_iso or "ERCOT",
-        )
+        # MISO-native published-outage overlay (gated, config
+        # .miso_native_outage_source, MISO-only). Substitutes MISO's measured
+        # Multiday Operating Margin region×cause offline-MW record for the CAMPD
+        # unit-outage extract as the availability derate — the MISO analog of
+        # ERCOT's measured DAM class-day availability. Aggregate grain (no unit
+        # identity in the public report), so it applies a uniform region
+        # availability envelope to the thermal bins; see
+        # market_sim.data.miso_outages. Default off — no keeper uses it yet — so
+        # when off, MISO keeps the CAMPD unit-outage derate below (byte-identical).
+        if _iso == "MISO" and getattr(config, "miso_native_outage_source", False):
+            from market_sim.data.miso_outages import (
+                miso_native_outage_derate_factors,
+            )
+
+            ufac = miso_native_outage_derate_factors(
+                config.weather_year, hours, iso=_iso
+            )
+        else:
+            ufac = unit_outage_derate_factors(
+                config.weather_year,
+                hours,
+                getattr(config, "campd_bins_path", str(CAMPD_BINS_CSV)),
+                iso=_iso or "ERCOT",
+            )
         if ufac:
```

## Verify after applying

```python
# 1. default-off + cache-key fork
from market_sim.config.scenarios import ScenarioConfig
base = ScenarioConfig(iso="MISO", mode="backcast", weather_year=2024)
assert base.miso_native_outage_source is False
assert base.cache_key() != base.with_overrides(miso_native_outage_source=True).cache_key()
assert ScenarioConfig().cache_key() == "8d34373ad73eb071"   # default ERCOT key unchanged
```

Then re-enable the gate assertions in `tests/test_miso_outages.py` (the
`test_gate_default_off_and_forks_cache_key` case, dropped from the intake commit
because the field was not yet present) and run the full suite.

## Composition to settle in calibration (not decided here)

The default derate sums all four cause types (total capacity offline) and
divides by the model's MISO thermal fleet (`_THERMAL_GROUPS`, ~118 GW). The
calibration session should decide: (a) whether to exclude `Planned` (to avoid
double-counting the statistical planned-outage model) or instead drop the
statistical POF for the covered classes the way ERCOT's DAM path does; (b)
replace-vs-multiply against the statistical availability; and score any verdict
flip leave-one-year-out within 2023–2025 before promotion (rule 22). Coverage is
2023–2026 only — MISO publishes no `_mom.xlsx` before 2023, so a pre-2023
backcast keeps the CAMPD/​statistical path regardless.
