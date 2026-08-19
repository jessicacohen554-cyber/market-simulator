# RESULT miso-170b — the site-grain re-stamp: arm-2 of the lay-up membership correction

**Session miso-170b (this session), 2026-08-19.** Executes
`PREREG-miso170-stgas-floor-membership-2026-08-19.md` **§7 (the dated K-1
amendment)** on the promoted keeper `2026-08-19-miso-170-membership`.
Outcome: **ALL KILLS SILENT — promoted to keeper
`2026-08-19-miso-170-sitegrain`** under the owner's standing same-session
instruction and the PREREG's own candidate rule (the structure-over-gates
clause was not needed).

## 1. What arm-2 is

The SAME 15-plant lay-up census the keeper arms, with ONE data change: the
`--patch-reliability-coeffs` step amended to stamp each census **SITE** on
every `(zone, plant_class)` limb its model tranches occupy, instead of only
the census row's majority class. 9 CT_PEAKER-limb cells change
(`MISO-Plains: 1104;2123`, `MISO-South: 1464`, `MISO-West: 6358`);
first-17-column identity byte-verified; census CSV byte-identical; default
cache key unmoved at `603c2498bf71d21d`; no ScenarioConfig change. Solved as
`replay_keeper --set reliability_floor_plant_exclusions=true --set
mustrun_plant_exclusions=true --out-dir results/calibration/miso170_layup_B2`,
years 2023–2025 sequential in one invocation (15 GB recipe).

Rationale (PREREG §7): the census verdict is computed on the
**facility-summed** meter — every unit included — so lay-up is a property of
the SITE, and the majority-class stamping under-implemented the prereg's own
identification. The live repair is Burlington (1104): its CT_PEAKER tranches
were floored 777/763 unit-hours (2023/2025) by the MISO-Plains CT netload
limb **while the site metered dark in 98.7 % / 91.8 % of exactly those
binding hours** — rule 17 verbatim. The 1464/2123/6358 CT stamps are guards,
measured live-inert (no solved arm floors those sites' CT tranches).

This is the **substantive** repair of the miso-170 K-1 residual. The
predecessor disclosure's *instrument* item — `aggregate_floors_by_plant`
labels a mixed-class plant by its most common unit group, charging a CT floor
to ST_GAS's provenance leg — **stands separately** as an open cross-ISO
scorer defect, now decoupled from MISO's C8.

## 2. Gates (`results/calibration/_miso170b_sitegrain_ab.json`, arm-2 vs the canonical control `miso170_membership_A`)

| gate | result |
|---|---|
| K-1 membership exactness | **PASS** — zero census rows remain on either mechanism in any year |
| K-2 liveness | **PASS** in band — shed 0.5336 / 0.8766 / 0.9487 TWh vs predicted 0.5044 / 0.7531 / 0.7853 ± 50 % |
| K-3 conduct failures | **PASS** — 18 → **1**, zero new, zero new off-window; the pre-named 1402 survivor present |
| K-4 C8 | 2024 FAIL → **PASS**, 2025 FAIL → **PASS** (both grounded above budget: all binding mechanisms clear D-4; D-1 shape gates clear); **2023 FAIL on 1402 exactly as pre-registered** |
| K-5 record flips | **PASS** — zero PASS→FAIL flips over the full scorer output |
| K-6 ST_GAS shape | **PASS** — profile_r 0.951/0.958/0.975, cv_ratio 1.422/1.109/1.265 |

Chain of control integrity: the canonical miso-170 K-0 (control bit-identical
to the miso-169 keeper) plus this session's **independent replication** —
`miso170_layup_A/B`, solved separately at a later MISO-inert HEAD, reproduce
`miso170_membership_A/B` **bit-identically** (probe `--identity`,
max|diff| = 0 on every scored sidecar of every year).

## 3. Determination (registered run `2026-08-19-miso-170-sitegrain`)

**NOT-YET on C3a-2025 (−12.1 %, the miso-163/miso-170 model-class lane) +
C8-2023 alone.** C3c stays the single ledgered caveat; C6 PASS on a fresh
attestation (`scripts/gen_miso170b_attestation.py`; 33 ledger entries / 2
residual; **zero new free parameters** — the delta is a stamping of an
existing measured set). C3a-2025 is unchanged to the reported digit (the
removed floor is ~0.01 TWh over three years); nothing here is claimed against
the scarcity lane.

## 4. What still fails, and whose it is

- **C8-2023, plant 1402 Little Gypsy** — the pre-registered expected
  survivor. A REAL window defect: the per-plant must-run window uses an
  `online_frac` POOLED over 2023–2025 (0.508) against per-year metered
  online shares 0.2495 / 0.6134 / 0.6548 — a ~2.3× 2023 over-commitment.
  Named successor: **per-year online_frac** (own prereg, own A/B, own DOF
  answer). 1402 is never added to the census (rules 1/14; held three times).
- **C3a-2025** — the summer-scarcity lane, owned by the miso-171 charter
  (reserve-requirement decomposition → sub-regional gating lever or the
  end-to-end model-class closure). Untouched here.
- **The D-4 plant-grain attribution defect** — cross-ISO scorer item
  (mixed-class sites in all six ISOs), no longer MISO's C8 blocker.

## 5. Session provenance note

This session (`claude/miso-2025-pricing-analysis-a4cby5`) ran concurrently
with the session that landed the miso-170 implementation and keeper. The
duplicate registrations that resulted were reconciled in-session (the
canonical `2026-08-19-miso-170-control` sidecar restored; the duplicate arm
registration removed; the bit-identity of the duplicate pair recorded above
as replication evidence). The same session also produced the no-LP
congestion/ELMP adjudication
(`FINDING-miso170-congestion-elmp-assessment-2026-08-19.md`) and the Ames
(1122) p25-level basis diagnosis carried there as a named successor.
