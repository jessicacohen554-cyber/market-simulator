# ERCOT-93 session handoff (ST_GAS steam RT/SCED basis + telemetered online span)

**Verdict: REJECTED PROBE.** The mechanism is structurally faithful but trips the
pre-committed zero-spurious §6 gate on the Jan-14/15 winter cold-snap cluster.
Keeper UNCHANGED (`2026-07-20-ercot91-seasonal-drag-fullspan`). Machinery is
default-off, so nothing here needs to be applied unless you want the recorded
machinery on main for the follow-up (season-conditioned wall) round.

## Why this handoff exists (transport)

`git push` to this environment's git proxy fails with **HTTP 413** on any pack
(confirmed on a walls-only commit). `push_files` (the mandated path) works and was
used for the small files below, but the two core files exceed its practical size:
`fleet.py` (526 KB / 11,125 lines) and `scenarios.py` (540 KB / 7,981 lines).
Their +197-line mechanism wiring is therefore delivered as the git-apply-able
patch `docs/handoffs/ercot93-core-mechanism.patch` in this same commit.

## Already pushed to this branch (verified byte-for-byte via the API)

- `scripts/data/derive_ercot_shoulder_online_span_steam.py` — the new ST_GAS
  telemetered online-span derive (the "hour-level online envelope" as an
  admissible conditional distribution; reusable by the follow-up round).
- `tests/test_ercot_offer_surface_cleared_share_steam_rt.py` — 11 tests
  (flag-off byte-identical, engagement, span geometry, guards, year-scoping).

## To reconstruct the full change (owner)

1. Apply the core-file wiring:
   ```
   git apply docs/handoffs/ercot93-core-mechanism.patch
   ```
   This adds 3 default-off `ScenarioConfig` fields (in `_CACHE_KEY_OPTIONAL_FIELDS`
   + `TIER_TAGS`; `cache_key(ScenarioConfig())` stays byte-stable) and the
   fleet.py wiring: the steam RT-wall loader, the steam span loader
   (`_load_ercot_steam_online_span_tables`), the `sp = span_h.get(cls_key)`
   change, and the two guards.
2. Regenerate the frozen derive artifacts (deterministic; number-heavy JSON that
   could not be hand-reproduced for push_files). The CC/CT + steam offer-wall
   derives are already on main; only the artifacts (and the span artifact) need
   regenerating:
   ```
   # Deliverable 1 — re-derive both offer walls on the full-year NP3-965 corpus
   python scripts/data/derive_ercot_sced_offer_wall.py       --years 2023 2024 2025
   python scripts/data/derive_ercot_sced_offer_wall_steam.py --years 2023 2024 2025
   # Deliverable 2 — the ST_GAS online-span artifact
   python scripts/data/derive_ercot_shoulder_online_span_steam.py --years 2023 2024 2025
   ```
   All three are byte-identical on re-run (verified this session).
3. `python -m pytest tests/test_ercot_offer_surface_cleared_share_steam_rt.py` (11 pass).

## What was done + measured this session

- **Deliverable 1** — both offer walls re-derived on the full-year corpus.
  **2023 now populated for the first time** (the big scarcity year); the
  previously-thin b0 / 2024-b6 bins now carry real coverage. Mid-band p50s move
  DOWN vs the sample-day artifacts (those days were tail/scarcity-biased) — a
  data-basis correction, not a residual tune (rule 23). The CC/CT RT wall is
  keeper-consumed, so the refresh lowers the keeper's 2024 C3a (−2.3% → −5.0%) —
  the accurate walls reveal the model is more under-priced than the tail-biased
  sample suggested (rule 11: the open C3 tail is the real issue, not the walls).
  The ercot91 keeper should be re-solved on the refreshed walls.
- **Measurement** (ERCOT-90 harness on the ercot91 sidecars, all 3 years): the
  shoulder-hour ST_GAS over-carry is **~97-98% economic** (above the drag floor)
  — the offer surface owns it, not the drag. The online span is a clean monotonic
  forward-regenerable conditional (2023 ON-share b0→b6: 0.14 → 0.99).
- **Probe** (2024 A/B vs base = keeper on new walls): C3a HELD, mid-band fill
  improved, but **zero-spurious TRIPPED (+11)** — 10/11 new spurious hours are
  the Jan-14/15 cold-snap cluster (reality $85-107 → probe $185-216). Isolation
  (RT-only, no span) trips +10, ALL cold-snap → the trip is intrinsic to the RT
  steam WALL, not the span. Full-span confirms (C3a 2023 −18.4% / 2024 +2.5% /
  2025 +10.8%; spurious 28/18/19; 2023 tail 83 vs 181 h untouched).
- **Root cause / frontier:** the wall's price ladder is net-load-percentile-bin-
  conditioned ONLY, so the not-RT-scarce winter high-net-load cold snap draws
  the summer-scarcity-dominated expensive high-bin ladder. The span carries the
  season axis (geometry) but the WALL does not (price). Frontier = a
  season-resolved offer-wall PRICE ladder (a new derive, feasible now that the
  full-year corpus is on disk). This is a NEW charter, not this lane.

## Calibration-log entry to append (docs/calibration-log/ercot.md)

Use the ERCOT-93 entry text from this session (a full copy is in the local
working tree's `docs/calibration-log/ercot.md`; the transport could not push the
394-line file without risking the pre-existing entries). Headline:
`## 2026-07-21 — ERCOT-93 (step-2 arming + full-year corpus intake): ST_GAS steam
RT/SCED-basis wall + telemetered online span BUILT and PROBED — REJECTED
(zero-spurious cold-snap trip, intrinsic to the RT wall's net-load-bin-only price
ladder); full-year corpus re-freezes both offer walls (2023 now populated);
machinery default-off, keeper UNCHANGED (ercot91). Next number: ercot-94.`

## Incident note

An environment `git reset --hard origin/main` + clean event fired twice this
session, wiping the uncommitted working tree, the local commits, and the
full-span probe bundle (`results/calibration/ercot93_stgas_rtspan`). All code was
re-created from context and re-verified (33 tests pass). The full-span probe's
C3/spurious numbers were captured before the loss (above); the bundle itself was
not re-registered on the dashboard (the untracked bundle would be wiped again by
a reset, and the mechanism is a rejected probe — the log + this handoff are its
canonical record, per the ERCOT-91 §8.1 rejected-probe pattern).
