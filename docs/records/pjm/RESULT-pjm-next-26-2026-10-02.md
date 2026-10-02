# RESULT: PJM-NEXT-26. The PJM-NEXT-25 coal-coverage rows, solved at the W0 posture: S2 and S3 falsified, not recommended

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (`pjmnext16_A_span`). Determination NOT-YET.

**Readings:** `PRECOMMIT-pjm-next-25-2026-10-02.md` §4, unchanged. The control and recipe were set before launch in
`ADDENDUM-pjm-next-26-w0-posture-2026-10-02.md`: the W0 PJM legs are the control, and the old keeper is a
reported-only comparison.

## 1. What ran

- **Seven shards, one year each (rule 36),** pinned `ef3aba035b183bc74f37611f6dee4b8935f0b2aa`. That is main
  `3ec2fd3e` plus the appended `thermal_tranches_PJM.csv` (sha256 `31455aaa…`) plus the addendum.
- **Recipe:** `pjmnext16_A_span` replayed with the ten W0 fields.
- **First launch:** all seven stopped at hard stop 1 because the platform cloned `main`. Each then fetched and
  detached `ef3aba03` and re-ran; no solve ran on the wrong commit.
- **Legs:** every leg was fetched, checked (`ls-tree` 17–18 files, bytes in hand) and its shard archived.

  | Year | Leg commit (`claude/pjm-next-26-<Y>`) | LP wall | Unserved MWh |
  |---|---|---|---|
  | 2019 | `8f4e8308a1c6ed7add8dc453ce4c38ddac136d81` | ~20 min | 205.9 |
  | 2020 | `9a8590db4d11894a277a30a8d37d1b064615cc1b` | ~15 min | 0 |
  | 2021 | `03144fcf9616473679b94865385d53348bd2d1ab` | ~15 min | 0 |
  | 2022 | `c91369ac7f27fe2121a498c6a2a77a977755eb1d` | ~20 min | 0 |
  | 2023 | `344287e96a04d30f3fd99d32591545dc38aa5b88` | ~31 min | 0 |
  | 2024 | `466990c654d8d2447637153490302cb3a8510808` | ~16 min | 1,470.8 |
  | 2025 | `a4758fd9907f4d673c5647094c5a06d14616ffb6` | ~17 min | 1,084.9 |

  The 2023 leg omits `unit_hourly_2023` (gitignored by rule 15); it carries `unit_marginal_2023`.
- **Composed** with `scripts/probes/_pjmnext26_compose_span.py` (a copy of the W0 composer). The recipe check passes:
  every leg is `pjmnext16_A_span` plus W0, one `solve_surface` fingerprint `23d4cbb5d30aefb0`, one source sha.
- **Registered locally as a probe** (`2026-10-02-pjm-next-26-coal`) for scoring only. Not committed: rule 15 keeps
  only keepers, and registering rewrote the shared PJM bench parts to the W0 membership, which is lane B's to commit
  when W0 PJM is promoted.

## 2. Readings vs the W0 control

The control is the W0 fix-2 legs `w0_pjm_{2019,2021,2022,2023}` (branches `claude/w0-pjm-<Y>-fix2`). The
`2020-fix2`, `2024` and `2025` W0 legs are no longer on the remote, so those years are read against the keeper only.
Probe: `scripts/probes/_pjmnext26_readings.py` → `results/phase0/pjm/_pjmnext26_readings.json`.

| id | reading | result | verdict |
|---|---|---|---|
| S1 | slack + dump ≤ control + 0.01 TWh | 2019 0.0002 = 0.0002; 2021–23 0 = 0; 2020/24/25 ≤ keeper | **holds** |
| S2 | the appended cohort's within-plant contrast gap (model − real, actual-RT margin) shrinks in ≥ 2 of 2019–21 | 2019: 0.98 vs control 0.41 (wider); 2021: 0.42 vs 0.34 (wider); 2020: 0.42 vs keeper 0.54 (no control) | **falsified** |
| S3 | no coal class > 30 % forced; D-4 adds no new coal off-window failure | coal D-2 max 12.5 %. **New D-4 coal unit-conduct failures at appended plants:** Waukegan 883 (2019 off-window 0.138, 2020 0.057) and Montour 3149 (2019 0.001) | **falsified** |
| S4 | 2023–25 training-tier C1/C3 verdicts unchanged | 2023 vs control: COAL_BIT +4.5 vs +3.1 TWh, CC +2.7 vs +3.4, C3a $31.03 vs $31.14, all PASS on both; 2024–25 have no control leg (arm floors 0.44 / 0 TWh) | holds where testable |
| P1 | COAL_BIT 2019 and 2021 up by 1–6 TWh | +2.44 and +1.04 TWh vs control | as predicted |
| P2 | no failing cell outside COAL_BIT / CC 2019–22 flips to PASS | none attributable to the arm | informational |

**S2 caveat, stated rather than used:** the within-plant contrast only counts plants with enough hours in both
margin bins. The qualifying subset shrinks on the candidate: in 2019, 2 plants against 9 in the control. The reading
is the pre-fixed one and is not re-read.

**Energy:** the appended cohort's model excess grows. In 2019 it is 37.0 vs real 25.7 TWh (control 33.1); in 2021,
30.6 vs 25.1 (control 28.8). The measured must-run floors add coal in exactly the years where coal already over-runs.

**Decision rule** (PRECOMMIT §4): S1–S4 do not all hold, so **the arm is not recommended.** S4 did not fail, and
nothing in the training tier moved because of the arm.

## 3. Candidate vs the incumbent keeper (reported only: this is W0 + rows)

| cell | candidate | keeper |
|---|---|---|
| C1 CC_REGULAR 2020 / 2022 / 2023 | PASS +4.3 / +7.1 / +2.7 | FAIL +9.8 / +10.9 / +8.5 |
| C1 COAL_BIT 2019 / 2020 / 2021 | FAIL +22.3 / +16.3 / +17.6 | FAIL +18.7 / +11.9 / +17.1 |
| C1 CT_PEAKER 2021 | FAIL −8.3 | FAIL −9.6 |
| C3a 2022 / 2025 | FAIL −17.1 % / FAIL −11.6 % | FAIL −17.4 % / PASS −9.6 % |
| C3b 2022 / 2025 | FAIL 0.288 / FAIL 0.222 | FAIL 0.292 / PASS 0.182 |

The CC passes and the 2025 C3a/C3b regressions come from **W0, not the arm**:

- Against the W0 control legs, the arm moves the load-weighted LMP by only −$0.10 to −$0.17 and CC_REGULAR by
  −0.7 to −2.1 TWh.
- In 2025 the arm floors zero TWh, yet the candidate sits $1.00 below the keeper.

This is what lane B's W0 PJM promotion will have to carry: W0 alone clears CC 2020/22/23 and puts 2025 C3a/C3b at
risk. Confirm against the composed W0 span when it lands.

## 4. Root cause and next lever

The PRECOMMIT's known limit is the likely cause of S3, and plausibly of S2. The appended plants have no per-year
`online_frac` row (`thermal_tranches_online_frac_by_year_PJM.csv`), so under `coal_sync_online_frac_per_year` they keep
a pooled operating-years fraction. The must-run window is then too wide in the years a plant was cycling or winding
down (Waukegan 2019–20; Montour, which converted to gas in 2023).

The rule-14 repair is to derive the per-year `online_frac` rows for the 18 plants from their own CEMS years. That is
zero DOF and the same deriver. Then re-solve the rows and the per-year fractions together as one data delta. This is
the "discovered bug elsewhere" rule 14 points at; it is not a reason to drop the measured rows.

## 5. Side card (a): IMM balancing credits by zone

`FINDING-pjm-next-26-bor-zone-census-2026-10-02.md`.

- **Weakly CONFIRMED under the correct sign** (3 of 4 testable years): the zones where the model under-runs CTs
  (AEP-Ohio, Dominion) take the largest real balancing-credit shares.
- **Sign correction:** the keeper over-runs ComEd CTs; it does not under-run them.
- **Consequence:** evidence for the CT_PEAKER 2021 ledger entry (out-of-merit commitment), not a lever.

## 6. Bundles and promotion cost

- **Composed span:** `results/calibration/pjm_next_26_span` (1.2 GB), local to this container only. The seven legs
  are on their shard branches (transport, rule 33) until this lane's PR merges.
- **If the owner rules to promote anyway:**
  - Re-run the compose from the leg branches.
  - Run `scripts/promote_keeper.py` after the W0 PJM keeper lands (unit_marginal is present for every year;
    `fleet_census_<Y>.json` is built by the promote preflight).
- **Not on `main`:** nothing from this solve is on `main`.

## 7. Owner ruling (2026-10-02, decision card)

**"Hold; fix fractions."**
- Do not promote.
- The next lane derives per-year `online_frac` rows for the 18 appended plants (rule 14, zero DOF).
- It re-solves the rows and the fractions together as one data delta, after the W0 PJM keeper lands.
