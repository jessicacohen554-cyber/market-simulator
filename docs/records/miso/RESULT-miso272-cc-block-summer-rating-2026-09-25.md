# RESULT — miso-272: the Edwardsport 481 MW phantom removed (v2, Edwardsport only). No gate flips, train tier stays CALIBRATED. RECOMMENDED for promotion; the owner decides. v1 is withdrawn on measured evidence.

```
LANE     : miso-272 (charter candidate 1)
PREREG   : docs/PRECOMMIT-miso272-cc-block-summer-rating-2026-09-25.md (v1 pin 8e85889b; v2 addendum §9, pin 5efb86f3)
KEEPER   : 2026-09-25-miso-271-wefor-stack (miso271_span, 2019-2025) — unchanged
DELTA    : cc_block_summer_rating=true (new ScenarioConfig field, default off). DOF +0; multipliers unchanged
CONTROL  : keeper bundle (G-DRIFT: all upstream hunks INERT, rule 29(b) form 4); no control solves
STATUS   : v2 registered 2026-09-25-miso-272-edwardsport-block (miso272b_span, 2019-2025). RECOMMENDED.
           v1 registered 2026-09-25-miso-272-cc-block (miso272_span). NOT recommended.
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
| 2022 | `a09e729d` | −0.100 | −0.073 | −0.081 | +0.104 | +0.080 | +0.080 | 62.591 → 62.667 (+0.076) |
| 2023 | `8f83d7ae` | −0.335 | −0.227 | +0.120 | +0.350 | +0.139 | −0.006 | 34.682 → 34.750 (+0.068) |
| 2024 | `a178595d` | −0.148 | −0.990 | +0.320 | +0.472 | +0.160 | +0.172 | 31.858 → 31.974 (+0.115) |
| 2025 | `17b0b38c` | −0.356 | −1.513 | +0.425 | +0.580 | +0.257 | +0.367 | 43.703 → 44.002 (+0.299) |

### 3.1 Scored (live scorer, same bench parts for both runs)

| criterion | keeper miso-271 | v2 miso-272 |
|---|---|---|
| C1 fuel mix (all classes, all years) | PASS | PASS |
| C1 CC_REGULAR TWh model / actual 2021 · 2022 · 2023 | 96.55 / 104.47 · 118.58 / 125.57 · 136.82 / 142.25 | 96.56 · 118.48 · 136.49 |
| C1 COAL_BIT TWh 2020 · 2023 (model / actual) | 61.60 / 66.37 · 52.99 / 57.14 | 60.49 · 52.76 |
| C2 / C4 / C6 / C8 | PASS | PASS |
| C3a 2019 · 2020 | +10.8 % · +10.9 % FAIL | +11.0 % · +11.3 % FAIL |
| C3b 2021 | 0.304 FAIL | 0.305 FAIL |
| C3c | ledgered caveat | ledgered caveat |
| **train tier 2023–2025** | **CALIBRATED 8 / 7 / 1 / 0** | **CALIBRATED 8 / 7 / 1 / 0** |
| full span | NOT-YET (price_mean, price_shape) | NOT-YET (same set) |

**What the scores show:**
- **No criterion flips in any year.**
- **The cost:**
  - +0.2 / +0.4 pp on the already-failing C3a 2019 / 2020 (+$0.05–0.30/MWh in load-weighted price).
  - +0.001 on C3b 2021.
  - Removing 473–481 MW of available coal raises price slightly, which is the declared direction.
- **Composite legitimacy diagnostics:** the D-1 row for COAL_BIT 2024 reports a FAIL. C8 reaches D-1 only for a
  class above its forced-energy budget, and COAL_BIT is well under it, so C8 PASSES. The row is reported, not gated.
- **The recipe is identical to the keeper's apart from the one field.**
  - `stamp_config_partition --check` passes, and the partition is byte-identical to the keeper's.
  - DOF +0.

### 3.2 Recommendation

**Promote v2.** It removes a physically impossible 481 MW of coal capacity, confirmed by the plant's own CAMPD
record, through a zero-parameter reconciliation of EIA-860's block-on-one-row filing (rules 13, 14 and 19).

It flips no criterion and leaves the train tier CALIBRATED. The only gate cost is a few tenths of a point on C3a,
which is already failing (rule 1: structure first).

This is the owner's decision (rule 31). Nothing has been promoted or pruned.

## 4. Where the bytes are and what a promotion costs

**v2 composite `miso272b_span`.** It holds the slim bundle, the `hourly/` sidecars, the attestation, the diagnostics,
the registry sidecar and the run payload. It lands on `main` with this lane's PR, so **promoting from there costs
zero re-solves.**

Its per-year dispatch exists on this session's local disk only (gitignored). The v2 legs are on
`claude/miso272b-arm-<Y>`. Those SHAs are provenance, not storage (rule 33(d)); they are in the attestation.

**v1** (`miso272_span`) is registered and superseded by v2. If v2 is promoted, rule 35 prunes the keeper
`miso271_span` and v1 together.

**2022 leg.** It took about 3 h 7 min, with at least one container restart and a swap-bound P1. The backup shard
never received a container and was archived. All 15 shards are archived: 7 v1, 7 v2, and the backup.

## 5. Routed, not fixed (unchanged from PRECOMMIT §7)

1. **Coal statistical-WEFOR stack.** This needs a per-unit-year baseload-screen artifact from
   `derive_campd_unit_outages.py`.
2. **Outage numerator basis at block plants.** Edwardsport's one-train share is 39 % in the keeper and 73 % under
   the fix, against a true 50 %. Hot Spring already sits at 61 %.
3. **C3a 2019/2020.** Only the owner's rule-1 coal band multiplier reaches it (owner decision).
4. **C3b 2021.** Waits on owner decision D1, the storm-month gas convention.

## 6. Promotion executed (rule 35) — 2026-09-25

The owner ruled, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper.."*

1. **Year set checked before any deletion.** Outgoing {2019–2025}, incoming {2019–2025}: covered, so the promotion
   does not shrink the year set (rule 35(c)).
2. **Promoted.** `keepers/MISO.json` now names `2026-09-25-miso-272-edwardsport-block`.
   - Both `config_partition` tiers were re-keyed to `miso272b_span`, and the partition is byte-identical.
   - The ISO headline was re-verified on the live scorer: **CALIBRATED** (train tier 8/7/1/0).
   - `status/MISO.js` was rebuilt.
   - The attestation was stamped with the ruling.
   - The matrix keeper stamp was updated, `cc_block_summer_rating` moved O → **K**, and the §5.4 header was updated.
   - MISO has no `calibration-complete.json` entry, so there was nothing to re-key there.
3. **Verified.** `audit_keepers --iso MISO` resolved the incoming keeper. The only failures were E13 for the two
   superseded runs, cleared in step 4.
4. **Deleted.** `prune_iso_runs.py --iso MISO --force-uncite` removed `2026-09-25-miso-271-wefor-stack`
   (`miso271_span`) and the withdrawn v1 `2026-09-25-miso-272-cc-block` (`miso272_span`), each with its sidecar and
   payload. Git history holds them.
5. **After.** `audit_keepers --iso MISO` PASS (0 failures). Registry parity shows no committed RED; the only unmapped dirs are this session's gitignored per-year legs on local disk (rule 31).
