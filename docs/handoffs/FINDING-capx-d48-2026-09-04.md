# FINDING — capx D48 Phase 1: the PJM accreditation-design devintage + DR-as-supply A/B (D45 §2.3 items 1–2), measured

**Lane:** capx D48 Phase 1 (Fable; rule-14 sign adjudication). Phase 0 (PR #4707,
`d850eac1`) landed the two DEFAULT-OFF `ScenarioConfig` gates, the DR intake, the
matrix rows and `docs/handoffs/PREDECL-capx-d48-2026-09-04.md`. This finding grades
that pre-declaration at full magnitude (§7) after ONE solve: the A/B arm
`pjm-2021-2025-realized-t1h-d48-devintage` (both fields ON) against D45-R's bare
`pjm-t1h` (`pjm-2021-2025-realized-t1h-d45r`, key `c6091bd5b62bbc3f`, both fields
absent = OFF). **NOTHING ARMS.** The arm registers SUFFIXED as `pjm-t1h-d48-devintage`;
the bare `pjm-t1h` verdict key, every keeper / shard / marker and the backcast namespace
are untouched. The arming recommendation (§8) returns to the owner on the §5 flip
condition the pre-declaration fixed before the solve.

**Gate (verified on `origin/main` `8f5cb32c` before anything ran):**
`ff-verdicts.json[pjm-t1h].provenance.run_id == pjm-2021-2025-realized-t1h-d45r`
(cache_epoch `c6091bd5b62bbc3f`) and `pjm-t1h-d45r-fixed` present — both true.

---

## 0. Verdict (one paragraph)

_TODO after solve._

## 1. Keys, environment, cost — measured before and after the solve

| item | pre-declared | realized |
|---|---|---|
| bare `pjm-t1h` recipe key (control, fields absent/False) | `c6091bd5b62bbc3f` | `c6091bd5b62bbc3f` (re-resolved at HEAD `8f5cb32c` via `build_config` → `apply_iso_scenario_defaults` → `cache_key()`) |
| A/B arm key (both fields True) | `bbe13b3f7b659d36` | `bbe13b3f7b659d36` — **match**; no collision with any committed bundle (grep over `results/`, `frontend/`, `docs/`: the only prior occurrence is the pre-declaration itself) |
| single-field keys (recorded, NOT solved) | `a0ff4a31b27d2748` / `c79fc92aaaac53cc` | same |
| posture in the resolved arm config | `fossil_announced_exits_enabled=True`, `hindcast_verified_announced_exits=True`, `entry_screen_diagnostics=True` | verified |
| wall / peak RSS | ~16–21 min / ~8.8 GB (P8) | _TODO_ |

No field landed on `origin/main` between Phase 0 and this solve that moves either key
(the bare key still reproduces D45-R's pre-declared value, which is the known-answer
check on the resolution path).

**Environment (stated, not absorbed):** 4 cores / 15 GB / no swap; full clone with
`data/raw` present; `data/clean` ABSENT at session start. `uv sync` then the five
partitions the solve's capacity-market seams read were curated first
(`confirmed-retirements`, `capacity-market-auction-supply`, `-auction-price`,
`capacity-deliverability`, `capacity-market-demand-curve`), then the full
`regenerate_clean.py` tree so the arm is solved on the SAME input surface D45-R's
control was (a partial clean tree can silently change a loader's fallback and confound
a one-field A/B). There is no separate "input-readiness check" in the harness beyond
the pre-solve forward-driver guard, which passed.

## 2. The zero-solve decomposition, refreshed on D45-R's ledgers (post-D44 fleet)

Instrument: `docs/handoffs/d48/devintage-positions-2026-09-04.py`, re-run on
`pjm-2021-2025-realized-t1h-d45r` (outputs `devintage-positions-d45r-2026-09-04.json`
/ `-stdout-…txt` beside the Phase-0 run on the D45 L1 ledgers). Same construction as
PREDECL §2: entering fleet (`fleet_by_fuel_before`) at class EFORd; VRE / hydro /
storage / tie on the ledger basis; four arms OFF / V (devintage only) / D (DR-as-supply
only) / BOTH. OFF reproduces the ledger's own `capacity_reserve_position` to +0.15 pt
(2023) / +0.66 pt (2024) — a class-EFORd reconstruction, stated.

| screen | arm | thermal firm | DR | firm | requirement | **position** | Δ vs OFF (pts) | $curve | published cleared / offered | zero-cross | exit budget |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 2022 (bridge; 2021 fleet + peak) | OFF | 137,055 | 0 | 148,033 | 130,295 | 1.1361 | — | $0 | 1.051 / 1.220 | 1.066 | +17,738 |
| | V | 163,772 | 0 | 174,750 | 156,126 | 1.1193 | −1.68 | $0 | | | +18,624 |
| | D | 137,055 | 10,513 | 158,546 | 135,677 | 1.1686 | +3.25 | $0 | | | +22,869 |
| | **BOTH** | 163,772 | 10,513 | 185,263 | 162,574 | **1.1396** | **+0.35** | $0 | | | +22,689 |
| 2023 | OFF | 135,757 | 0 | 146,737 | 128,566 | 1.1413 (ledger 1.1398) | — | $0 | 1.055 / 1.141 | 1.065 | +18,170 |
| | V | 162,702 | 0 | 173,681 | 154,522 | 1.1240 | −1.73 | $0 | | | +19,159 |
| | D | 135,757 | 10,117 | 156,853 | 133,876 | 1.1716 | +3.03 | $0 | | | +22,977 |
| | **BOTH** | 162,702 | 10,117 | 183,798 | 160,904 | **1.1423** | **+0.10** | $0 | | | +22,894 |
| 2024 | OFF | 135,244 | 0 | 147,103 | 133,371 | 1.1030 (ledger 1.0964) | — | $0 | 1.056 / 1.126 | 1.064 | +13,732 |
| | V | 162,195 | 0 | 174,054 | 160,194 | 1.0865 | −1.65 | $0 | | | +13,860 |
| | D | 135,244 | 10,146 | 157,249 | 138,879 | 1.1323 | +2.93 | $0 | | | +18,370 |
| | **BOTH** | 162,195 | 10,146 | 184,201 | 166,810 | **1.1043** | **+0.13** | $0 | | | +17,391 |
| 2025 (post-CIFP: V inert) | OFF | 125,567 | 0 | 137,686 | 144,632 | 0.9520 (ledger 0.9617) | — | $164.84 (cap) | 1.005 / 1.005 | 1.067 | −6,946 |
| | **BOTH** (= D) | 125,567 | 6,085 | 143,770 | 150,605 | **0.9546** | **+0.26** | $164.84 (cap) | | | −6,835 |

Read against the Phase-0 table (D45 L1 ledgers): the dated exits D44 armed lower every
OFF position by 0.4–4.0 pts (2024 most: 1.1432 → 1.1030), but the two halves' SIGNS and
MAGNITUDES are fleet-independent to the decimal — V −1.65…−1.73, D +2.93…+3.25 — so BOTH
is within +0.10…+0.35 pt of OFF in every pre-CIFP screen and every arm remains 3–9 pts
past its vintage zero-cross. The zero-solve re-screen at each arm's own position passes
**0 MW** of the failing pool in every arm (88,602 MW in 2022 / 73,441 in 2023 / 87,132
in 2024 — smaller than the D45 L1 pools because the dated plants are exempt, D45 §4.0).
The requirement rows move by +25 % (2023 / 2024: V +20.2 % × D +4.1 %) and +4.1 %
(2025); the exit budget GROWS by +3.7…+5.0 GW.

## 3. What the solve measured — the A/B on the live stack

_TODO after solve (§3.1 position table; §3.2 FC-3 rows; §3.3 capacity-revenue leg and
exits; §3.4 entry; §3.5 the ledger rows that moved)._

## 4. The P9 sign test (rule 22, zero free parameters)

_TODO after solve._

## 5. Explicitly NOT built, routed

1. **D45 §2.3 item 3 — the clearing half.** On the auction's own basis the model's
   CENSUS position (§2/§3) still sits between the market's committed position ((1+RM)/(1+IRM)
   ≈ 1.05) and its OFFERED position (1.13–1.22), and the price forms at the CLEARED
   quantity, not at the census — so the curve pays $0 at the census in 2022–2024 under
   every arm while the published curve at the published cleared position pays $15–21/kW-yr
   (D45 §2.1). The faithful representation is "clear the VRR curve against the fleet's
   net-ACR offer stack" (Manual 18 §6 / MSOC; every ingredient — per-unit going-forward cost
   and E&AS margin — is already the retirement screen's own operand). **NOT BUILT HERE**,
   deliberately: it is a second mechanism with its own identification (the BRA reports'
   offered-vs-cleared quantities as validation observables, rule 13) and its own
   pre-declaration; stacking it into this A/B would make the devintage's own sign
   unreadable (rule 19). Routed to the director as the successor PJM lane; this finding's
   value to it is that the accounting is now on the auction's basis, so a clearing half
   inherits a position it can clear against.
2. **The VRE / storage ELCC devintage** (PREDECL §3 item 3). PJM's VRE ELCC began at
   delivery year 2023/24 (not 2025/26), so wind/solar/storage carry a SEPARATE two-date
   construction (Manual 21 class values 14.7 % / 38 % before 2023/24; ELCC class ratings
   after). At HEAD's ledger credits (wind 0.41, solar 0.106, hydro 0.38 accredited) the
   whole limb is worth +447 MW / +0.3 pt on the 2021 fleet — immaterial to any row here —
   and it is NOT part of either D48 field. Routed as a not-built limb with its own dates.
3. **Beyond the table (2028/29+) the DR series holds the last published ratio** (7,298.6 /
   152,400 of the gross requirement, 4.79 %) — the forward-edge convention P7 names; not
   solved in this lane (T1-H only).

## 6. Matrix (rule 28) and registration

_TODO after solve._

## 7. The pre-declaration, graded at full magnitude

_TODO after solve._

## 8. Arming recommendation — on the pre-stated §5 condition

_TODO after solve._

## 9. Governance attestation

_TODO after solve._
