# RESULT — closeout-PJM-nuc: PJM re-solve on the measured nuclear CF rows (R-35 / R-38)

Lane `claude/closeout-pjm-nuc`, 2026-10-03. Desk: session_01ALecU5Wjde4tkbLrnMExT9.
PRECOMMIT: `PRECOMMIT-closeout-pjm-nuc-2026-10-03.md`, committed before any solve.
Incumbent: `2026-10-02-w0-pjm-fix2` (`w0_pjm_span`). Pin: `8c3ea46192074cfd422fff6532acc035d37297bb` (the
merge of #7109). Probe registered: **`2026-10-03-closeout-pjm-nuc-6yr`** (`results/calibration/closeout_pjm_nuc_span`).

## Headline

**HOLD.** The pre-fixed decision rule fires for two independent reasons:
1. **One PASS→FAIL flip: 2022 C1 CC_REGULAR**, +7.95 → +8.96 TWh against the ±8 TWh band.
2. **2021 could not be solved** in the shard containers (see §4). The bundle carries 6 of the keeper's 7
   years, so rule 35 refuses a promotion in any case.

The input change itself behaves exactly as predicted. In every year, model nuclear moves by the measured-row
amount to within 0.02 TWh:

| | 2019 | 2020 | 2022 |
|---|---|---|---|
| Δ predicted | −0.19 | +1.75 | −2.10 |
| Δ solved | **−0.17** | **+1.75** | **−2.09** |

The 2023–25 legs reproduce the keeper to the MWh. The 2022 flip is the same measured correction exposing a
CC_REGULAR over-dispatch that already stood at +7.95 TWh, 0.05 TWh inside the band. Of the 2.09 TWh of nuclear the
2022 row removes, CC_REGULAR picks up 1.0 TWh.

## 1. Legs

All legs are on `8c3ea461`, run once per year in their own shard container (rule 36). Each was verified by `git
ls-tree` and the bytes are in hand (18 files each, including `dispatch/<Y>_P1.parquet` and
`hourly/unit_marginal_<Y>.parquet`).

| Year | Shard branch @ commit | Session (archived) | Peak (RSS / +swap) |
|---|---|---|---|
| 2019 | `claude/closeout-pjm-nuc-2019` @ 959cae91 | session_01XzUjXbXdF6mtvcjZdTRtuY | 13.36 / — GiB |
| 2020 | `claude/closeout-pjm-nuc-2020` @ df0a3478 | session_01CsWJeQqDBibZhr3tepXCiM | 13.36 / 17.84 GiB |
| 2021 | — (not solved; owner card, §4) | 3 attempts, all archived | killed at 13.36 GiB |
| 2022 | `claude/closeout-pjm-nuc-2022` @ 47a9db84 | session_01KZGW4sZqKnu8gkshHoPYBm | 13.36 / 17.92 GiB |
| 2023 | `claude/closeout-pjm-nuc-2023` @ fbc78864 | session_011ydS3yQrKgPgK7F51G2mZu | 13.36 / 17.50 GiB |
| 2024 | `claude/closeout-pjm-nuc-2024` @ 998b3905 | session_01M8VjpDCphiByNhAH2t4sGD | — |
| 2025 | `claude/closeout-pjm-nuc-2025` @ 57bdb18b | session_019hNRvAVXaE1aQH7ZEgoLH5 | — |

**Compose.** `scripts/probes/_pjmnext26_compose_span.py --keeper results/calibration/w0_pjm_span --pinned-sha
8c3ea461…` returned "recipe = w0_pjm_span + W0" for every leg:
- No `ScenarioConfig` field differs from the keeper.
- One shared `solve_surface` fingerprint, **`d8230f36c0059245`**, against the keeper's `23d4cbb5d30aefb0`. This
  confirms the PRECOMMIT §2 reason that 2023–25 could not be kept legs.
- `legitimacy_diagnostics.json` is rebuilt over the six years.

## 2. Readings (fixed in the PRECOMMIT §3)

**R1, nuclear.** Δ is within 0.02 TWh of the prediction in every year: **PASS**.

**R2, displacement.** Each class's Δ vs keeper, TWh:

| Class | 2019 | 2020 | 2022 |
|---|---|---|---|
| nuclear | −0.174 | +1.749 | −2.092 |
| CC_REGULAR | −0.071 | −0.502 | +1.005 |
| COAL_BIT | −0.079 | −0.447 | +0.350 |
| CT_PEAKER | +0.056 | −0.605 | +0.337 |
| ST_GAS | −0.011 | −0.123 | +0.109 |
| COAL_PRB / COAL_WC | +0.101 / +0.020 | −0.054 / — | — / +0.052 |
| net import (export −) | +0.099 | −0.007 | +0.167 |

- **2020 and 2022: PASS.** Thermal moves opposite to nuclear, and Σ|Δ thermal| ≤ |Δ nuclear| + 0.5 TWh.
- **2019: PASS** under its stated small-move exception (|Δ| ≤ 0.5 TWh). There the classes shuffle by ≤ 0.1 TWh in
  mixed directions.
- 2021 is unscored (missing leg).

**R3, price.** **PASS.**
- C3a 2020 is +9.0 % (keeper +9.6 %), so it stays ≤ +10 %.
- Every C3a move is ≤ 0.6 pp; every C3b move is ≤ 0.006.

**R4, reproduction 2023–25.** No class moves by more than 0.005 TWh. C3a, C3b, C1, C4 and CO2 are identical. The
only differences are in the third decimal of the D-1 profile r / CV ratio, which come from rebuilding diagnostics
over the composite. **PASS.**

**R5, 2025 benchmark.** No 2025 score moved, so **no EIA-923 data drift** is present.

## 3. Per-(criterion, year) diff vs `w0_pjm_span`

Rows that changed status or magnitude (rubric 3.18). 2023–25 and every unlisted row are unchanged.

| Year | Criterion | Keeper | Probe | Note |
|---|---|---|---|---|
| 2019 | C1 COAL_BIT | FAIL +19.81 | FAIL +19.73 | |
| 2019 | C1 COAL_PRB / CT / CC | PASS | PASS | moves ≤ 0.1 TWh |
| 2019 | C3a / C3b | +1.9 % / 0.086 | +1.7 % / 0.082 | |
| 2019 | C3c | CAVEAT 6 h vs 14 h | FAIL* 5 h vs 14 h | *see note |
| 2019 | C4 gas / coal r | 0.940 / 0.949 | 0.946 / 0.952 | |
| 2019 | CO2 | +4.2 % | +4.3 % | |
| 2020 | C1 COAL_BIT | FAIL +13.18 | FAIL +12.74 | improves |
| 2020 | C1 CC_REGULAR | PASS +6.50 | PASS +6.00 | |
| 2020 | C1 CT_PEAKER | PASS −4.43 | PASS −5.04 | |
| 2020 | C3a / C3b | +9.6 % / 0.144 | +9.0 % / 0.138 | |
| 2020 | C8 CT_PEAKER forced | 28.4 % grounded | 30.5 % grounded | |
| 2020 | CO2 | +3.3 % | +2.9 % | |
| **2022** | **C1 CC_REGULAR** | **PASS +7.95** | **FAIL +8.96** | **flip** |
| 2022 | C2 sysvol gas | PASS | PASS (flags CC_REGULAR) | |
| 2022 | C1 COAL_BIT | PASS +6.62 | PASS +6.97 | |
| 2022 | C3a / C3b | FAIL −16.9 % / 0.287 | FAIL −16.7 % / 0.293 | |
| 2022 | C3c | CAVEAT 2 h vs 92 h | FAIL* 2 h vs 92 h | *see note |
| 2022 | CO2 | +3.2 % | +3.5 % | |
| — | C6 governance | PASS | UNATTESTED | probe, no attestation |

**\* The C3c status change is a registration artefact, not a solve change.**
- The keeper's attestation carries no exceptions ledger. Its C3c CAVEAT is rule 22's auto-ledger, which applies
  only when governance (C6) passes.
- A probe carries no attestation, so C6 reads UNATTESTED and the same C3c rows read FAIL.
- The 2022 magnitudes are identical; 2019 moves by one hour.
- At a promotion the attestation would restore C6 and the auto-ledger.

**Determination.**
- Probe: NOT-YET, from the governance gate.
- Keeper: NOT-YET, from C1 COAL_BIT 2019–21, CT 2021, and C3a/C3b 2022 and 2025.
- Promoted with an attestation, the probe's undocumented-FAIL set would be the keeper's set plus **C1 CC_REGULAR
  2022**, minus 2021 (unscored).

## 4. 2021 — owner card (the missing leg)

Three attempts were made, all on the unchanged recipe, all pinned at 8c3ea461, none of which reached HiGHS:

1. **First attempt** (session_01KGxdVVGLWU6hp7qoGNPqBt).
   - The shard prompt had no DA-virtuals fetch step, so it stopped pre-LP. The desk then sent the fetch step.
   - The same-container retry found the first run's 9 GiB `/swapfile-marketsim` inactive. It could not
     re-provision swap and was killed (exit 137) during the LP build.
2. **Second attempt, fresh container** (session_01UgSLYaJP3rMXfn8xahuZra).
   - The preflight provisioned only **3 GiB** of swap (`ceiling 13.36 + swap 3.0 = 16.4 GiB`).
   - It was killed (exit 137) after 422 s, during the LP build after "PJM PER-GEN reserve co-opt ON". The cgroup
     max was 14,345,035,776 B and only 3.3 MiB of swap was used.
3. **Third attempt, fresh container** (session_019rxHs4V4MR7yNXPxhEoR4L), with the desk's hard stop 5: swap
   ≥ 9 GiB and ceiling+swap ≥ 22 GiB.
   - The preflight provisioned **4 GiB** (`ceiling+swap 17.4 GiB`; free disk 10.1 → 6.1 GiB). The stop fired
     before `replay_keeper`.

The legs that solved peaked at 13.36 GiB RAM + 4.1–4.6 GiB swap (17.5–17.9 GiB), always with 9 GiB of swap
provisioned. On identical prompts, the swap the preflight provisioned varied from 3 to 9 GiB, depending on free
disk after `hydrate_data` + `regenerate_clean` + the virtuals fetch.

**This is a container-envelope limit, not recipe growth.** The same recipe solved for six years.

**Unblock.** A container with ≥ 19 GiB free disk at preflight, or swap provisioned before hydration (an
infra/owner change, not patched here). Then one 2021 shard, recompose with seven legs, and re-score.

## 5. Recommendation to the desk / owner

- **HOLD the promotion.** Rule 35 refuses it without 2021, and the pre-fixed rule holds on the 2022 CC flip.
- **The owner ruling needed is on the 2022 flip.**
  - Rule 14 [R-ACCURATE] says a worse fit after swapping in measured data is a bug found elsewhere. The measured
    rows are not reverted.
  - What the flip exposes is a pre-existing 2022 CC_REGULAR over-dispatch (+7.95 → +8.96 TWh). That is the
    natural next PJM lever, and it is consistent with the 2022 C3a −16.9 % / C3b 0.287 misses the keeper already
    carries.
  - My recommendation, once 2021 is solved: **promote on structure (rule 14)**. Record the 2022 CC_REGULAR C1 as a
    NOT-YET criterion with this attribution, rather than holding the measured nuclear rows back.
  - That changes the pre-fixed decision rule, so it is the owner's call.
- **Promotion cost when ruled:**
  - one 2021 shard, about 20 minutes of LP, in a ≥ 22 GiB envelope;
  - recompose (zero LP);
  - `promote_keeper.py`, which carries unit_marginal for all seven years, `fleet_census_<Y>.json` (build or carry
    — the legs do not write it), the R-36/R-37 ledger entries carried forward, and an `authorized_price_tuning`
    block declaring "none under the channel".
  - It goes in the desk's slot after closeout-PJM-impl (#7110).

## 6. Desk items (tooling; not patched in this lane)

1. `scripts/shard_prompt.py` does not emit the `fetch_pjm_da_virtuals.py --years Y --feeds hrl_da_incs_decs` step
   for a PJM recipe that arms `pjm_da_virtual_bids`. All six first-wave shards stopped pre-LP on it.
2. Container memory is 13.36 GiB RAM, with swap that varies by free disk: 9 / 3 / 4 GiB were provisioned on
   identical prompts. The 24 GiB target is never reached, and a PJM leg needs ≈ 18 GiB. Provisioning swap before
   hydration would likely secure 9 GiB.
3. A stale swapfile survives a failed run. After a pre-LP stop, a same-container retry finds
   `/swapfile-marketsim` on disk but inactive, so it cannot re-provision. A PJM shard whose first attempt stops
   before the LP must be relaunched fresh, never resumed (2022's same-container resume worked only because its
   swap was still active).
4. The shard `**` negation also commits `hourly/unit_hourly_<Y>.parquet` (~80 MB) on shard branches. This is
   transport only; the composite keeps it gitignored (rule 15).
5. 2019 unserved energy: 499.9 MWh, against the keeper's 205.9 MWh, out of ~800 TWh. This is noted only; it is
   immaterial.

## 7. Where things are (rule 34)

- **Composite:** `results/calibration/closeout_pjm_nuc_span` on `claude/closeout-pjm-nuc`. It is slim, by the
  keeper convention (`hourly/` sidecars including `unit_marginal_<Y>`; the `dispatch/` and `unit_hourly` files
  stay gitignored).
- **Full legs:** including `dispatch/<Y>_P1.parquet`, on the six shard branches above, recorded here by SHA as
  provenance (rule 33). The local copies will not survive this container.
- **Retention (rule 31):** no solved bundle was deleted. The incumbent keeper is untouched.
