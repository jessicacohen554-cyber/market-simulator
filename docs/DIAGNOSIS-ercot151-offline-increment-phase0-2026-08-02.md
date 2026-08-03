# ERCOT-151 — the 2023 tail's phantom cheap DEPTH is measured at the missed hours; the offline-increment re-pricing lane (ERCOT-107/108 scope-correction successor) is CONFIRMED identifiable and chartered; the identification is DATA-BLOCKED on an NP3-965 corpus re-upload

> **§4 ask 1 RESOLVED 2026-08-03 (ercot-157).** The owner re-uploaded the
> delivery-2023 NP3-965 corpus to `data/raw/ercot/SCED/` (315 shards, verified
> complete: all 365 delivery days, 35.8M rows; two failed upload batches caught
> and re-supplied same-day). The pool's 2023 CT year block is derived and
> committed (`ercot_faststart_pool_condbinned.json`), the CC/CT wall's 2023
> block refreshed full-year (the committed block was the Jan–Oct post-purge
> slice; scarcity-tail bins 5–6 byte-identical), and the steam wall gained its
> first 2023 block. The ERCOT-152 refusal of the CC tier stands (the pool is
> CT-only by measured conduct). **§4 ask 2 — the ERCOT-89 §7 step-2 design
> round / arming decision — remains open and owner-gated.** Full record:
> `docs/calibration-log/ercot.md` ERCOT-157.

**Session 2026-08-02. Keeper: `2026-08-02-ercot150b-zonal-anchor` (NOT-YET; open
gates C3a 2023-only −32.6 %, C3b 2023-only 0.616, C3c, C7 2023-lignite cv-leg).
Phase 0 only — NO LP built, NO year solved, NO mechanism armed, keeper
UNCHANGED.** Probes: `scripts/probes/ercot151_offline_phase0.py` +
`ercot151_offline_phase0b.py` (committed record
`results/calibration/ercot151_offline_phase0.json`); all inputs committed
(60-Day DAM Gen Resource 2023 parquets, keeper hourly sidecars,
`actual_lmp_hourly_ERCOT.parquet`, the ERCOT-88 pool artifact).

This session also merged PR #3298 (the ercot-150 zonal-anchor keeper promotion)
into the working branch — conflict resolved by regenerating `manifest.js` from
the merged sidecars; `audit_keepers --iso ERCOT` PASS.

## 0. Verdict

1. **The chartered offline-increment re-pricing lane is the single live,
   never-run, structurally-correct lever for the 2023 price gates** (C3a/C3b/
   C3c-2023 are one physical residual, 97 % of the mean-price gap in the >$300
   tail, 97 % of the tail price in the ENERGY dual — ERCOT-101/103). Every
   alternative family is adjudicated closed: reserve-side (ERCOT-97/102/103/
   107/108 — bistable envelope, inert realized adder, slack measured AS),
   requirement-side (ERCOT-102), physical inputs (ERCOT-98), topology
   (ERCOT-104/117), offer LEVEL on the online fleet (ERCOT-99/100/118/119/
   136–140/144/150 — the whole SCED-TPO program).
2. **Phase 0 measures the phantom depth directly, on committed data, at the
   ercot150b keeper's own missed hours.** At the 91 missed hours (of 144 actual
   RT >$300 in 2023; keeper load-weighted price mean **$105** vs actual
   **$860**), the config-collapsed 60-Day DAM disclosure shows the real market
   held **18.1 GW of startable-but-OFF CC+CT** (CC 10.3 / CT 7.8; plus ST 3.6)
   against only **14.5 GW ON (CC 13.7 / CT 0.8)** — and **~13.5 GW of that
   CC+CT OFF increment carried submitted DAM offer curves at or below $200**
   (~15.0 GW ≤$200 across all gas). The model's availability basis
   (only-OUT-is-out, correct per rule 13 — startability is physical) hands the
   LP that entire block **at base offers with no start economics**, so ~15 GW
   of phantom-cheap depth caps the model at ~$105 where reality cleared $860.
   The model's cushion below $200 at these hours is ~0.5 GW (ERCOT-101): the
   defect is three orders of magnitude larger than the margin that would need
   to move.
3. **The price magnitude the re-pricing needs is already measured and
   committed.** The ERCOT-88 fast-start pool artifact
   (`ercot_faststart_pool_condbinned.json`) carries the measured start-inclusive
   SCED2 ladders of the offline-CT pool: p50 rungs **$271–707**, p90
   **$641–1,010** (2024, by net-load bin) — scarcity-price magnitudes, from the
   fleet's own conduct. A constants-based startup amortization (physical
   startup $/MW over min-run at LSL ≈ **$20–30/MWh**) is the WRONG
   identification by ~30×: the measured offline offer is an opportunity-cost /
   commitment-risk price, not a fuel-plus-start price. This kills the
   "derive it from committed physical constants" shortcut ex ante — the
   identification must be corpus-measured conduct, exactly like the ERCOT-88
   CT ladder and the ERCOT-105 RT wall.
4. **Why ERCOT-88's pool never moved the tail (and is not a refuted cell):**
   eligibility gates on unit physics (min-down ≤ `FASTSTART_POOL_MIN_DOWN_
   HOURS`), so it repriced only the fast-start CT slice; the LP "cleared
   around it" on the un-repriced cheap CC offline block (ERCOT-107/108 scope
   correction). Phase 0 quantifies the clear-around: CC is **10.3 GW** of the
   18.1 GW increment, 8.2 GW of it ≤$200. The chartered successor is the
   **CC (slow-start) widening** — a second physics tier at its own measured
   start-inclusive ladder — plus the pool's missing **2023 year block** (the
   artifact is 2024/2025-only because of the then-standing 2023 SCED bar,
   which ERCOT-105's owner authorization has since lifted).
5. **The lane is DATA-BLOCKED on a corpus re-upload, and on nothing else.**
   The full-year NP3-965 corpus (799 shards, ~3.26 GB, 2023 complete) was
   owner-uploaded 2026-07-21, consumed by the ERCOT-105 wall re-derive, and
   **purged by the `cleanup-large-blobs.yml` history rewrite of 2026-07-22**
   (the FF ledger turn-45 commit records the force-pushed filtered history) —
   which is also why ERCOT-101 (07-24) wrongly concluded "no 2023 SCED source
   exists" before its same-session correction. Only the derived wall JSONs
   survived (they carry 2023); the pool derive needs the raw shards. The free
   MIS path cannot substitute: NP3-965 rolling retention reaches delivery
   ~2024-01 (fetcher header, verified 2026-07-16), so 2023 is unreachable
   without the owner's copy (or the credentialed data.ercot.com archive,
   previously owner-declined).

## 1. Where this sits in the adjudicated history (do-not-redo map)

The 2023 residual chain, compressed — every cell here is closed and cited; do
not re-open any of them for this lane:

* **C3a/C3b/C3c-2023 are ONE residual**: 97 % of the −$17.6/MWh mean gap is the
  >$300 tail (`ercot101_price_decomp`); the tail is 97 % energy dual / 3 %
  RTORPA on ERCOT's own settlement series (ERCOT-103 §1.1). Reserve-side
  mechanisms are capped at ~$42/MWh of effect by that decomposition and the
  family is closed on a completed 2×2 (ERCOT-107/108: in-LP envelope → +680–700 %
  C3a, whole year repriced; pricing-only → −36 %, tail slack).
* **The energy dual at the missed hours is set by RT re-offer conduct** the
  model's DAM-basis offer stack cannot see ($25–130 DAM offers re-offered
  $500–5,000 in SCED). The 2023 RT wall (ERCOT-105, recovered) is armed and
  **fit-neutral** (keeper $46.76 → $46.50) because the wall reprices the ON
  fleet's ladder — while the *depth* that caps the price is the OFF increment
  below it. The bound is **depth, not height** (ERCOT-107/108 correction).
* **The C6 attestation draft** (`docs/handoffs/ercot-101-governance-attestation-
  draft-2026-07.md`) already scopes its 2023 exception to the reserve-side
  family and names this lane as the open successor: *"Sign this exception only
  as an accepted limitation of the CURRENT keeper, not as a finding that the
  tail is unimprovable."*
* **Cross-ISO queue check (rule 28a duty, this session):** the ERCOT column's
  live transfer candidates were reviewed. `gas_offer_margin_zonal_anchor` was
  tested and promoted by the parallel ercot-150 session (now K, merged here);
  `dynamic_reserve_requirements` (PJM/MISO/NYISO K) is **already satisfied at
  ERCOT in substance** — the multiproduct co-opt holds the measured hourly
  ASPLANNP433 plan (ERCOT-102 §1: the "AS-holdout" premise was refuted because
  the holdout is already in place and slack at the missed hours), so no ERCOT
  arm exists to test; `maxgen_emergency_tier_pricing` (MISO K) has no ERCOT
  analogue instrument (no declared-window ELMP tiers; ERCOT's administrative
  actions enter through the armed measured RTORDPA overlay); `diurnal_price_
  amplitude` (xiso-1) remains a live *audit* lane — its ERCOT peak-half deficit
  is this same scarcity/near-tail formation family, so it rides on this lane
  rather than preceding it.
* **Third-party check (this session):** the IMM's 2023 SOM attributes >$12 B of
  2023 RT cost to *artificial scarcity* from the June-2023 ECRS launch
  (withheld 10-min reserves ~doubled; released only manually). The model
  already carries exactly this structure as measured inputs — the ECRS family
  holds the measured plan rigidly at VOLL through the 2024-08-01 release
  reform (`ercot_ecrs_conservative_deployment`, date-gated), which is the
  keeper's only working tail-former (binds 41/42 of the HIT hours). The IMM
  story is therefore already in the model where it is reserve-side; what the
  model misses is the CONDUCT half — QSEs re-offering the energy stack at
  scarcity prices during those perceived-shortage windows — which is this
  lane. Commercial production-cost practice (PLEXOS VoRS / scarcity-slice
  adders tuned to history) is the rule-13-forbidden version of the same thing;
  the admissible construction is the measured conduct surface, which ERCOT's
  60-day disclosures uniquely license.

## 2. Phase-0 measurement (committed record `ercot151_offline_phase0.json`)

Basis: 2023, actual RT >$300 = 144 h (scorer parquet); missed = keeper
load-weighted zonal system price <$200 = **91 h** (model mean $105 / actual
mean $860). Config-collapse per `derive_ercot_thermal_dam_availability._site`
(max-across-configs; ON netted out of the OFF increment per site).

| class | ON (GW) | startable-OFF increment (GW) | of it submitted-DAM ≤$200 (GW) |
|---|---|---|---|
| CC | 13.66 | **10.32** | 8.24 |
| CT | 0.81 | **7.81** | 5.22 |
| ST | 3.84 | 3.61 | 1.53 |
| **CC+CT** | 14.48 | **18.13** | **13.46** |

Cross-checks: ERCOT-107/108 measured 16.94 GW CC+CT startable-OFF at the 146
actual >$300 hours with a slightly different ON-status set — same order, same
composition. The DAM-OFF CT at 0.8 GW ON confirms the phenomenon: the real CT
fleet is DAM-uncommitted at these hours and its RT starts price at RT re-offers
(the pool ladder), not at its cheap DAM curve — the model instead dispatches
that curve directly.

## 3. The chartered arm (design, for the owner-authorized round)

One mechanism family, two measured artifacts, zero fitted parameters:

1. **Re-derive `ercot_faststart_pool_condbinned.json` with the 2023 year
   block** (fast-start CT tier; the ERCOT-88 deriver unchanged, the 2023 bar
   lifted per the ERCOT-105 authorization). Year-scoped (rule 13), absent
   years byte-identical — the 2024/2025 blocks must reproduce byte-identically
   as the derive-integrity check (the ERCOT-105 precedent).
2. **Widen the re-priced slice to the slow-start OFF increment (CC, and ST if
   its row survives the ERCOT-90/91 steam-lane reconciliation)** as a SECOND
   physics tier (min-down 4–8 h), each at its OWN measured start-inclusive
   SCED2 ladder derived from OFF-status resources per net-load bin — the
   ERCOT-88 construction, new tier, new flag (e.g.
   `ercot_offline_commit_offer`), REPLACE-BY-MASK composition with the
   existing surfaces (rule 19: in the increment's row-hours the pool price is
   the sole owner; an offer-availability, never a floor — no min_gen, no
   forced energy, D-2/D-4 vacuous by construction).
   Rule-19 reconciliation to enumerate in the precommit: `ercot_gas_
   commitment_bridge` owns the ON committed CC min-gen state (disjoint — the
   increment is above the site's ON HSL); P1's startup amortization owns
   started-run pricing (the tier must replace, not stack, for the OFF-tier
   rows); the RT wall owns the ON fleet's ladder (disjoint by status).
   Forward story (rule 13): the surface is conditional conduct (net-load-bin ×
   physics tier), regenerates for a forward year from forward net load exactly
   like the DAM/RT walls already do; it responds to changed conditions.
3. **Falsifiers to pre-register** (the precommit, pushed before any solve):
   (a) the ERCOT-89 zero-spurious/C3a guards that killed the shoulder-span
   arms (the pool must not reprice sub-$150 same-cell hours — the pool's
   net-load-bin scoping is the protection); (b) C3c formation must come with
   matched hours, not invented quiet-day scarcity (the ercot148/149 anatomy
   discipline); (c) 2024/2025 must hold their PASSes (LOYO within 2023–25,
   rule 22); (d) the D-2 attribution must show zero forced energy (it is an
   offer mechanism).

**Expected magnitude (Phase-0 arithmetic, not a promise):** repricing the
~13.5 GW cheap OFF increment onto ladders whose p50 is $271–707 moves the
missed-hour marginal from the $105 cushion into the wall/pool band; the model
needs only ~0.5 GW of depth to flip. The risk is over-formation in shoulder
hours — exactly what the net-load-bin conditioning and the pre-registered
guards exist to catch.

## 4. The owner asks (both required before any build)

1. **Re-upload the NP3-965 60-Day SCED Gen Resource corpus** — at minimum the
   publication months covering delivery-2023 (~2023-03 through 2024-02;
   ~250 shards, ~1 GB), ideally the full 799-shard set so the CC/ST tier
   ladders derive full-span. The uploaded copy is consumed by the derives and
   may be purged again afterwards; the committed deliverables are the compact
   condbinned JSONs (the wall precedent). If preferred, land it outside git
   (the cleanup workflow's Git-LFS/external-store recommendation stands) —
   the derives only need a readable path.
2. **Authorize the design round** (this is the ERCOT-89 §7 step-2 owner gate,
   still standing): the CC-tier widening + 2023 pool block + full-span
   single-delta A/B off the ercot150b keeper, guards as §3.3 above.

## 5. Governance

* No mechanism tested, no solve, no dashboard registration (no-LP measurement
  session — the ERCOT-142/143 pattern). Keeper untouched; holdouts untouched
  (2023-only, a training year).
* Matrix duty 28(c) repair executed this session: `ercot_faststart_pool_offer`
  had NO matrix row (it predates the guard). Row added as `O` (ERCOT) with the
  ERCOT-88/107-108/151 citation chain; no other cell claimed.
* PR #3298 (ercot-150 keeper) merged into this branch; dashboard manifest
  regenerated from sidecars; `audit_keepers --iso ERCOT` PASS.

Next number: ercot-152.
