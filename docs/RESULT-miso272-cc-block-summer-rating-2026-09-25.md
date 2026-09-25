# RESULT — miso-272: the Edwardsport 481 MW phantom. v1 is withdrawn on measured evidence; v2 (Edwardsport only) has solved 6 of 7 years

```
LANE     : miso-272 (charter candidate 1)
PREREG   : docs/PRECOMMIT-miso272-cc-block-summer-rating-2026-09-25.md (v1 pin 8e85889b; v2 addendum §9, pin 5efb86f3)
KEEPER   : 2026-09-25-miso-271-wefor-stack (miso271_span, 2019-2025) — unchanged
DELTA    : cc_block_summer_rating=true (new ScenarioConfig field, default off). DOF +0; multipliers unchanged
CONTROL  : keeper bundle (G-DRIFT: all upstream hunks INERT, rule 29(b) form 4); no control solves
STATUS   : v1 registered (2026-09-25-miso-272-cc-block) and NOT recommended.
           v2: 6/7 legs verified; 2022 still solving at 11:15 UTC (see §4)
```

## 1. The defect

Some EIA-860 filers report a combined-cycle block's **whole** net summer rating on its steam-part (CA) row and leave
every gas-turbine (CT) row blank. The loader fills each blank CT with its nameplate, so the block is carried as its
rating **plus** its CT nameplates.

The census found this pattern at 7 MISO plants in every vintage 2019–2025.

**MISO 1004 Edwardsport (a coal IGCC)** is the plain case:
- The keeper carries **1,036–1,068 MW of coal** for a 555–595 MW machine.
- CAMPD 2023 corroborates the rating: max 480 MW gross, zero hours above 555.

## 2. v1 — all 7 plants — withdrawn

v1 is registered as `2026-09-25-miso-272-cc-block`: 7 single-year legs pinned to `8e85889b`, composite
`miso272_span`. Every structural gate passed, and every direction matched the PRECOMMIT.

| gate | keeper | v1 |
|---|---|---|
| C1 CC_REGULAR 2021 / 2022 / 2023 (TWh) | −7.69 / −6.77 / −5.06, PASS | −9.63 / −8.73 / −8.23, **FAIL** |
| C3a 2019 / 2020 | +10.8 / +10.9 % | +11.7 / +12.1 % |
| C3b 2021 | 0.304 | 0.310 |
| train tier 2023–2025 | CALIBRATED | NOT-YET (C1 2023) |

**The gates are not why v1 is withdrawn.** Measured data is. For each of the six NG blocks, the CAMPD 2023 hourly
record shows the plant operating above its published summer rating (gross × 0.97 > rating):

| plant | hours above the rating |
|---|---:|
| Hinds | 3,566 |
| Attala | 4,143 |
| Ouachita | 1,187 |
| Perryville | 858 |
| Union | 653 |
| Hot Spring | 51 |

- The keeper's CAMPD-p999 cap and the CC guard were already the better bound for these plants: they bound by
  measured capability, which the CC guard's own doctrine says always wins.
- v1 replaced that measured bound with the lower published rating (a rule-13 defect).
- The charter had already flagged this ("the NG ones are already capped by cc_capacity_reconcile — rule 19").

PRECOMMIT §9.1 carries the full table.

## 3. v2 — the predicate scoped to non-NG blocks (Edwardsport only)

- **Change:** v2 adds one predicate condition: no CA row is NG-fuelled.
- **Why:** gas blocks stay with the measured CC guard and cap (rule 19).
- **Zero-LP check:** only plant 1004 moves.
  - Every other unit, including every heat rate, is byte-identical.
  - 2019–2022: −473.0 MW coal. 2023–2024: −481.2 MW.
  - 2025: −328.6 MW COAL_BIT and −152.6 MW CC_REGULAR. The canonical 2025 file labels the CTs NG.

**Legs.** Each was fetched, `ls-tree` > 0, checked out, and passed the recipe, inputs, vintage and classifier checks
on the parent's bytes. Each is compared with the keeper, and the load-weighted price is the load-weighted internal
LMP.

| year | leg commit | CC_REGULAR | COAL_BIT | COAL_PRB | CT_PEAKER | ST_GAS | import | LW price $/MWh |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 2019 | `913b5917` | −0.274 | +0.092 | +0.304 | +0.031 | +0.150 | −0.243 | 29.272 → 29.319 (+0.047) |
| 2020 | `19c9c225` | +0.117 | −1.109 | +0.419 | +0.180 | +0.280 | −0.031 | 25.505 → 25.594 (+0.089) |
| 2021 | `b4e4a7bf` | +0.021 | −0.098 | −0.274 | +0.134 | +0.124 | +0.040 | 42.312 → 42.475 (+0.162) |
| 2022 | still solving | | | | | | | |
| 2023 | `8f83d7ae` | −0.335 | −0.227 | +0.120 | +0.350 | +0.139 | −0.006 | 34.682 → 34.750 (+0.068) |
| 2024 | `a178595d` | −0.148 | −0.990 | +0.320 | +0.472 | +0.160 | +0.172 | 31.858 → 31.974 (+0.115) |
| 2025 | `17b0b38c` | −0.356 | −1.513 | +0.425 | +0.580 | +0.257 | +0.367 | 43.703 → 44.002 (+0.299) |

**Expected gate outcome (arithmetic on the keeper's scored values, not yet the scorer's):**
- C1 CC_REGULAR moves at most 0.36 TWh in any year, so 2021 and 2023 stay PASS (2023 ≈ −5.40).
- C3a 2019/2020 rises about 0.2–0.4 pp. It stays FAIL at about +11.0 / +11.2 %.
- Train-tier inputs move by hundredths of a TWh and cents per MWh, so no train-tier criterion is expected to flip.
- The composite still has to be scored before any claim is made.

## 4. Open

- **2022 v2 leg.** Session `session_01BZSju52WUzgmx77WVTjGRP`, branch `claude/miso272b-arm-2022`.
  - Launched 08:28. It has restarted at least once and was still in its P1 solve at 11:14 UTC, at about 18.4 GiB,
    swap-bound.
  - A backup shard never got a container and was archived.
  - When it lands, the steps are: compose `miso272b_span` → stamp → attestation → register → score.
  - If it fails, the cost is one more 2022 re-solve, about 60–70 min.
- **Promotion question.** Pending the full v2 score, which is the owner's decision (rule 31).
- **v1 bundle and legs.** The bundle is registered here, and the v1 legs sit on `claude/miso272-arm-<Y>`. Its
  per-year dispatch exists on this session's local disk only (gitignored). A promotion of v1 is not recommended.

## 5. Routed, not fixed (unchanged from PRECOMMIT §7)

1. **Coal statistical-WEFOR stack.** This needs a per-unit-year baseload-screen artifact from
   `derive_campd_unit_outages.py`.
2. **Outage numerator basis at block plants.** Edwardsport's one-train share is 39 % in the keeper and 73 % under
   the fix, against a true 50 %. Hot Spring already sits at 61 %.
3. **C3a 2019/2020.** Only the owner's rule-1 coal band multiplier reaches it (owner decision).
4. **C3b 2021.** Waits on owner decision D1, the storm-month gas convention.
