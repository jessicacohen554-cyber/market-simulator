# FINDING — SPP-94: SPP did publish 2020 and 2021 wind curtailment. The rows are on `main`; the solve is blocked by session nesting.

**Lane** SPP-94 · keeper `2026-09-26-spp-86-coal-extract` (bundle `spp86_arm_span`) unchanged ·
PRECOMMIT `docs/handoffs/PRECOMMIT-spp-94-curtail-rows-2026-09-27.md`, merged to `main` at
**`020bb1c5cb38b73da686dc4e83d1620c415b1437`** (PR #6812) before any model output existed · nothing solved, nothing
registered, no promotion question yet (rule 31).

## 1. What was found

SPP-67 armed `vre_reference_rate_year_own` (cell **K**) but left 2020 and 2021 on the 9.65 % 2023–25 mean, stating
that "SPP published no curtailment MW for them". An SPP-7x audit repeated that reading. **It is wrong.** Only the
2023–25 State of the Market reports had been read; the earlier editions publish both years.

| year | published avg hourly curtailment | source | year-own rate | rate the keeper applied |
|---|---:|---|---:|---:|
| 2020 | **244 MW** | ASOM 2022, printed p. 53 | **2.55 %** | 9.65 % |
| 2021 | **725 MW** | ASOM 2021, printed p. 60 (figure axis: "Average hourly curtailments") | **6.37 %** | 9.65 % |

- **Basis check:** both figures are wind, on the same average-hourly-MW basis as every committed row. The 2021
  edition's 2019 value (136) matches the later restatement (137). The 2022 edition's 2022 value (1,260) matches the
  committed row exactly.
- The 2019 and 2020 editions print no curtailment MW; 2020's figure comes from the 2022 edition, just as 2019's
  comes from the 2023 edition.

## 2. What it changes, at zero LP (`docs/handoffs/spp94/census.json`)

Wind headroom above delivered, as the keeper builds it:

| year | now | with the published rows | change |
|---|---:|---:|---:|
| 2020 | 8.76 TWh | 2.14 TWh | **−6.62 TWh** |
| 2021 | 9.92 TWh | 6.32 TWh | **−3.60 TWh** |
| every other year | — | byte-identical | 0 |

- **Pre-solve STOP legs:** S1 adequacy PASS (0 MW moved in the 500 highest-net-load hours, both years); S2 basis PASS.
- **G-DRIFT** `325674da → ceeb47a4`: all INERT (PRECOMMIT §2).
- **Solve surface** 317 → 317, 0 moved.
- **Expected direction**, declared before any solve: 2020/2021 wind down, thermal up, price up or flat. 2020
  `price_mean` (+17.6 %) is expected to **worsen**. It is rule 14 that justifies the change, not the residual.

## 3. Why nothing was solved

The seven shards (one per year, rule 36) were written and pinned to `020bb1c5`. `create_session` refused all seven:
**"caller session is at lineage depth 8 (limit 8)"**. Rule 32(a) forbids the parent from solving, so the lane stops
here. The shard prompt template is `docs/handoffs/spp94/shard_prompt_template.txt`. Cost when run: SPP is a 2-zone ISO, so each shard is minutes;
the whole span is about 500 s of LP.

## 4. State left behind (read before G-DRIFT)

- **The two rows are on `main`** (rule 14: a published measurement is never reverted to the estimate). A HEAD replay
  of the keeper therefore differs from its committed bundle **in 2020 and 2021 only**. Until the arm is solved and
  the owner rules, any G-DRIFT must classify `020bb1c5` as **LIVE for 2020/2021, INERT for 2019 and 2022–25**.
- Cell `vre_reference_rate_year_own` stays **K**. The evidence line records the data correction and that the solve
  is pending.
- The keeper, the dashboard and every registered run are unchanged.

## 5. Next step

Run the seven shards exactly as PRECOMMIT §4 specifies. They go in a session that can spawn children, i.e. a new
chain. Then compose, attest, score, register (`--no-prune`), and put the promotion question to the owner under
PRECOMMIT §5's fixed rule. `complete` / `frontier`: unchanged. The train tier 2023–25 is CALIBRATED (lone ledgered
C3c). The validation tier 2019–22 is NOT-YET. **`frontier` is NOT reached.**

**Owner ruling (decision card, 2026-09-28): "New chain (Recommended)".** The solve runs in a fresh session chain (SPP-95),
not in this one.
