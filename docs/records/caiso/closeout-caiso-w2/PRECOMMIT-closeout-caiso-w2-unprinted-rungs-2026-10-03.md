# PRECOMMIT closeout-CAISO-w2: daytime + late-evening DSW clean rungs in the unprinted hours (2026-10-03)

**CONDITIONAL.** Nothing here is solved unless the owner rules option A ("Arm daytime + late-evening pre-2021") on
the desk card raised from this lane's ask of 2026-10-03. On B ("Keep the ledger"), this PRECOMMIT lapses unsolved
and the flag stays default-off and unarmed. Written before any solve. Evidence:
`FINDING-closeout-caiso-w2-phase0-2026-10-03.md` §4.

## 1. What it is

An OWNER-RULED TRANSFER of the R-CAISO-20 pattern, **not** a rule-13 measured admission (R-CAISO-19 FINDING §3).

One field: `caiso_dsw_daytime_lateevening_unprinted_arm` (default off, CAISO-only, backcast-only; cache-key
registered).
- `inject_caiso_dsw_daytime_clean(unprinted_year_arm=)`: the hod 6–21 evidence gate also admits the R-CAISO-18
  unprinted-year hours (`_caiso_dsw_unprinted_hours` = `envelopes.measured_intertie_hub_unprinted_year_mask`, the
  overnight arm's mask).
- `inject_caiso_dsw_lateevening_clean(unprinted_year_arm=)`: the same for hod 22–23.
- There is no print in those hours, so there is no caiso-87 trigger (the surplus rung stays 0 MW) and no DA-hub spread
  cell.
- Handed in only with `caiso_intertie_unprinted_year_measured_gas` (the pricing).
- Printed hours are byte-unchanged, and 2022–25 are inert by construction. Fast-lane tests pin all of this:
  `tests/iso/caiso/test_caiso_w2_daytime_lateevening_unprinted.py`.

**Depth (pre-registered, not re-sized, rule 1).** The window-matched p95 of the EIA-930 WECC_DSW corridor net import
over every hod 6–21 / 22–23 hour of the year:

| MW | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| daytime (hod 6–21) | 7,348 | 7,122 | 5,733 (static) |
| late-evening (hod 22–23) | 6,922 | 7,281 | 6,415 (static) |

2021 keeps its ordinary depth because its printed May–Dec hours already ride it (one year, one depth; the R-CAISO-20
rule).

**Pricing:** formula hub + EF 0 + ε, no wheel.

**Headroom:** net of the firm block and every sibling clean rung (rule 19).

## 2. Recipe and shards

- **Arm:** the keeper recipe (`closeout_caiso_w1_a2_span`, replayed by `scripts/replay_keeper.py`) plus
  `--set caiso_dsw_daytime_lateevening_unprinted_arm=true`. That is the only delta.
- **Shards:** seven, one per year 2019–2025 (rules 32/34/36). Each is pinned to one full 40-char SHA of the build PR
  and runs the one `--years <y>` invocation.
- **Control:** the keeper's committed bundle (rule 29(b)).

## 3. G-DRIFT (rule 29(b)), before launch

The keeper legs were solved at `566bc8fa`. The base `1e3e4177` carries 86 changed `src/` files since then, so a
zero-LP audit is required before any shard.

| Year | Audit | If LIVE |
|---|---|---|
| 2022–25 | the arm is inert by construction; the leg at the build SHA is compared record-by-record against the keeper | any record beyond noise (C1 ±0.5 TWh, C3a ±0.5 pp, C4 NRMSE ±0.01) means HEAD drift is LIVE: stop, classify, report |
| 2019–21 | fleet-only rebuild at the build SHA vs the keeper's committed fleet census (unit count and capacity by class) | every LIVE hunk is named in the RESULT; the arm's effect is read as arm-leg − keeper and labelled confounded where a LIVE hunk touches the year |

## 4. Bars (fixed ex ante)

**Target.**

| Gate | Bar |
|---|---|
| T1 C1 CC_REGULAR 2021 | +6.59 → ≤ +4.83 TWh (PASS), i.e. moves ≥ −1.76 |
| T2 C1 CC_REGULAR 2019 | +5.63 → ≤ +4.84 TWh (PASS), i.e. moves ≥ −0.79 |
| T3 C1 CC_REGULAR 2020 | reported; ≤ +4.60 needs −8.86 and is NOT claimed |
| T4 C4 gas NRMSE 2019–21 | reported; a PASS is not claimed |

**C1 PASS → FAIL declared ex ante:** none. CC_CHP, CT_PEAKER, ST_GAS, ST_CHP and COAL_BIT in 2019–21 are all
expected to stay in band.

**Kill rules (any one stops promotion):**
1. **K1:** any undeclared C1 PASS → FAIL in any year.
2. **K2:** whole-year |DSW net import − EIA-930| grows in any fold year (the R-CAISO-20 backstop).
3. **K3:** C4 gas NRMSE worsens by > 0.02 in any fold year.
4. **K4:** C3a 2021 (covered window) worse than +13.7 % (keeper +12.7 %, band 1.0 pp); C3b 2021 NRMSE worse than
   0.158.
5. **K5:** any 2022–25 record moves beyond noise (§3 G-DRIFT).
6. **K6:** C2 gas leaves its band in any year.

**Expected (first order, FINDING §4):** added DSW import +5–12 / +6–14 / +1.3–3 TWh in 2019 / 2020 / 2021. Over-run
risk in 2019 is guarded by K2.

## 5. Decision rule

- **K1–K6 all clear and T1 or T2 met:** send the desk the scored flips and request the promotion slot. The attestation
  declares the arm as an owner ruling, as R-CAISO-20 does.
- **K1–K6 clear, neither T1 nor T2 met:** report. The owner's ruling decides whether a structure-only promotion is
  wanted.
- **Any kill:** NOT PROMOTED. The RESULT records the reach and the cell moves U → R with the reason.

The determination is expected to stay NOT-YET under every outcome, since 2020 C1 and C4 are not claimed.

## 6. DOF

Zero fitted parameters. The two depth tables are measured p95 values of an existing statistic over the window the
capability arms. The arming window is authorised by the ruling and ledgered as such (rule 21).
