# RESULT (interim): UC-4-MISO arm U4 — uc-1.7 + DA-forecast commitment + per-unit ut_h/mlf + VLR, ST_GAS floor off

**Verdict: NOT ADJUDICATED (coverage).** This is not R and not G. UC-DESK ruling (c), 2026-10-15 13:12Z, closes the lane on
2019–20 coverage. 2021–2025 are **held at 3/4 memory attempts** (Addendum D): no container of the required size could be
obtained.
- The PRECOMMIT targets T-1 (C1 CC 2021/22) and T-3 (C4 gas 2021) cannot be read.
- The three reserve years (2023–25) cannot be read.
- The 2019–20 readings below are **partial evidence only**.

- **PRECOMMIT:** `PRECOMMIT-ucmilp4-miso-u4-2026-10-15.md`, written and pushed before any shard (`742707db`).
  - Addendum A: FIX-8 hold.
  - Addendum B: pin `7c93273e`, G-DRIFT, gate ruling.
  - Addendum C: gate re-basing, MISO unchanged at 22.4.
  - Addendum D: hold the 4th memory attempt.
- **Pin:** `7c93273ec9056b1cd9f6e4fcf387e812f78f6e8a` (uc-1.7 + FIX-8 #7267).
- **Control:** the keeper's committed bundle `closeout_miso_nuc_span` (rule 29(b)); no control solve.
- **Comparators:** arm V (UC-MISO-VLR, uc-1.6) and UC-3 arms A and B (uc-1.5).
- **Nothing registered or promoted** (E13).
  - Scoring used a local probe registration, excluded from git via `.git/info/exclude` and never committed.
- Lane session `session_013RW9CFeUzG69bPAc9RqMrr`, chartered by UC-DESK `session_01WX9W5tgYMre3Z134LZoGF6`.

## 0. Headline

**On 2019–20, committing on the day-ahead load forecast removes most of the price rise the UC stage carried in arm V.**
- C3a returns to the keeper's level: +6.2 % / +10.6 %, against keeper +6.2 / +10.2 and arm V +9.1 / +13.8.
- C4 gas fits slightly better than the keeper.
- No PASS→FAIL flip on any kill cell.
- The VLR rows stay grounded.
- **Arm V's open under-cycling item (V-3) closes:** pocket ST_GAS starts are 0.98× and 1.67× CEMS, against 0.44 / 1.12 in V.

The years that decided arm V's R are unread: the C4 gas 2021 flip (shared by arms A, B and V) and the 2023–25 reserve years. So this
partial picture **cannot be adjudicated**.

## 1. Gate table, control → U4 (2019 / 2020)

C1 = model − EIA-923 (TWh). C3a = mean LMP vs RT. C3b = monthly NRMSE. C4 = fleet hourly NRMSE (pass bar ≤ 0.30). C8 = forced share.

| reading | 2019 control → U4 | 2020 control → U4 | note |
|---|---|---|---|
| C1 CC_REGULAR | +3.17 → +5.89 | −1.24 → +1.56 | PASS both |
| C1 CC_CHP | −5.25 → −4.76 | −4.49 → −3.87 | PASS |
| C1 COAL_PRB | +4.56 → +5.47 | +3.87 → +4.47 | PASS |
| C1 COAL_BIT | −2.79 → −2.48 | −4.66 → −4.37 | PASS |
| C1 CT_PEAKER | +2.01 → +2.10 | −3.03 → −2.50 | PASS |
| C1 ST_GAS | −8.71 F → −10.38 F | −7.09 P → **−9.55 F** | rule-19 replacement: **reported only** (PRECOMMIT §3.3, §4) |
| C3a | +6.2 % → +6.2 % | +10.2 % F → +10.6 % F | 2020 FAIL in both |
| C3b | 0.091 → 0.093 | 0.147 → 0.149 | PASS |
| C4 gas NRMSE | 0.196 → 0.189 | 0.201 → 0.195 | PASS, improves |
| C4 coal NRMSE | 0.108 → 0.106 | 0.130 → 0.126 | PASS, improves |
| C8 ST_GAS | 26.3 % → 18.2 % | 20.0 % → 12.5 % | PASS |
| C8 CC_REGULAR | 0.0 % → 8.0 % | 0.0 % → 7.1 % | PASS (MECH 28 floor) |
| C3c | 0 h vs 17 h → same | 0 h vs 8 h → same | 2019 CAVEAT → FAIL is the known unattested-probe artefact; magnitude unchanged, not counted |
| P1 unserved / dump (MWh) | 0 / 0 | 0 / 0 | U-1 pass |

**Kill #3:** no PASS → FAIL on any kill cell (C1 non-ST_GAS, C3a, C3b, C4, C8) in 2019–20. Kills #1, #2 and #4 also do not fire.

## 2. Readings against the PRECOMMIT (2019–20 only)

**Binding**
- **U-1 (unserved): pass.** 0 MWh in both years.
- **U-2 (VLR on-share vs CEMS, ±0.15):** pass. Within ±0.04 everywhere.

  | | DSG | WOTAB | Western |
  |---|---|---|---|
  | 2019 | 0.932 vs 0.940 | 1.000 vs 0.952 | 1.000 vs 1.000 |
  | 2020 | 0.959 vs 0.944 | 0.989 vs 0.995 | 0.927 vs 0.939 |

- **U-3 (binding hours with CEMS dark; FAIL ≥ 50 %):** pass.
  - DSG / WOTAB / Western: 0.0 / 4.9 / 0.0 % (2019); 2.7 / 0.0 / 0.1 % (2020).
  - Amite South (declared expected): 4.4 / 19.5 %.
- **U-4 (C8 ST_GAS):** pass, 18.2 / 12.5 %.
- **U-5 (engine):** pass on both legs.
  - Version uc-1.7.
  - `da_forecast` / `eia930_da_forecast` set.
  - 4 VLR sets with n_req 1/1/1/2; WOTAB:C unmatched.
  - 365/365 windows with `pocket_rows ≥ 96` and 0 skipped.

**Targets**

| id | reading | bar | U4 | reads |
|---|---|---|---|---|
| T-1 | C1 CC_REGULAR 2021 / 2022 | ≥ −9.05 / ≥ −8.72 | — | **unread (held)** |
| T-2 | C3a 2020 / 2019 | ≤ +11.9 % / ≤ +10 % | +10.6 % / +6.2 % | **met** |
| T-3 | C4 gas 2021 | ≤ 0.30 | — | **unread (held)** |

**Reported**
- **Starts ÷ CEMS** (U4; UC-3 arms A / B in brackets):

  | | 2019 | 2020 |
  |---|---|---|
  | CC_REGULAR | 0.27 [0.30 / 0.26] | 0.40 [0.37 / 0.36] |
  | ST_GAS (all) | 0.79 [0.68 / 0.75] | 1.11 [1.01 / 1.08] |
  | ST_GAS pocket sets | 127/129 = 0.98 (V 0.44) | 185/111 = 1.67 (V 1.12) |
  | COAL_PRB | 3.0 | 2.8 |
  | COAL_BIT | 3.7 | 4.6 |

- **Min-up revisit trigger (owner ruling r14).** CC starts are still well below CEMS, while CC is online *more* than CEMS: 209,263 vs
  192,423 unit-hours in 2019, and 218,573 vs 198,278 in 2020. The UC holds CC in long blocks. The DA-forecast commitment did not change
  that. r14's "revisit after UC-4 only if CC starts stay well below CEMS" is therefore triggered.
- **Commitment-demand increment** (`engine.commitment_demand`):
  - 2019: mean +2,313 MW; top-100 median +3,350 MW (ranked on P1 zonal demand); QA-dropped 6 h.
  - 2020: mean +1,962 MW; top-100 median +4,835 MW; QA-dropped 24 h.
  - The means and QA counts equal the zero-LP phase 0 (§2.1).
- **Uplift** (`uc_uplift`, make-whole > 0):
  - 2019: $64.9 M = 0.37 % of P1 energy payments ($17.71 B); pocket plants $39.4 M.
  - 2020: $47.9 M = 0.32 % of $15.12 B; pocket plants $25.3 M.
  - Both are under the 2 % sanity bar.
- **D-1 (legitimacy):**
  - COAL_PRB 2020 cv_ratio: keeper 0.409 FAIL → U4 0.462 FAIL.
  - COAL_LIGNITE 2020: 0.485 FAIL → 0.517 pass.
  - No new D-row FAIL. The leg-local "legitimacy gate FAIL" the shards logged is this keeper-inherited D-1 row.
- **Cost:**

  | | 2019 | 2020 |
  |---|---|---|
  | wall (s) | 7,091 | 6,349 |
  | UC stage (s) | 5,278 | 4,432 |
  | P0 + P1 (s) | 1,509 | 1,614 |
  | UC ÷ (P0 + P1) | 3.5× | 2.7× |
  | time-limit hits | 0 | 0 |
  | integer set | 71 | 76 |
  | peak RSS+swap (GiB) | 16.99 | 16.73 |

  Both peaks are ≤ 17.89, so the gate needs no re-base (Addendum C).

## 3. Coverage: held years and attempt log

The keeper carries 2019–2025 (rule 16). U4 solved 2019 and 2020.
- 2021–2025 each hit the memory gate three times on 16.4–18.4 GiB containers (free disk 9.9–11.3 GiB). They are **held at 3/4**
  pending the owner's gate ruling (Addendum D).
- They are relaunchable unchanged when a larger pool exists: same pin, same prompts, about 2–2.5 h each (2022: 720-min budget).
- 2 of the 18 containers that reached the gate cleared 22.36 GiB (two more launches were FIX-8 defect stops, interrupted before the gate).
- Under the desk's rule (gate = 1.25 × the max observed peak, 17.89), MISO's gate is 22.4 under any ruling on the table.

Full log: `data/ucmilp4_miso_readings/attempt_log.tsv`.

| year | attempts | outcome |
|---|---|---|
| 2019 | 2 (16.4; 22.36) | **solved** `17117ee` |
| 2020 | 1 (+1 FIX-8 defect stop) | **solved** `52e66dc` |
| 2021 | 3 (17.4 / 16.4 / 16.4) (+1 defect stop) | held |
| 2022 | 3 (17.4 / 16.4 / 17.4) | held |
| 2023 | 3 (17.4 / 17.4 / 16.4) | held |
| 2024 | 3 (16.4 / 16.4 / ~18.4) | held |
| 2025 | 3 (16.4 / 17.4 / ~17.4) | held |

No gate-stopped shard read data, solved or pushed. Every shard is archived.

## 4. Defects found (none repaired here)

1. **`scripts/shard_prompt.py` does not shell-quote a JSON-string `--set`.** It emits `--set uc_commitment_demand_source="da_forecast"`.
   Bash strips the quotes and `replay_keeper.py`'s `json.loads` exits. The lane's prompts single-quote the argument. This affects every
   UC-4 lane that arms `da_forecast`.
2. **FIX-8 (resolved by #7267).** At `7dbfe20f`, the `da_forecast` increment did not map onto `IMPORT_ZONE` pseudo-zones
   (`MISO_external`). Every MISO leg would have raised at UC prep. Phase 0 (§2.1) missed it because it tested the BA series, not the zone
   split.
3. **The bundle `.gitignore` negation over-reaches.** The shard prompt's `!results/calibration/<out>/**` also un-ignores
   `hourly/unit_hourly_<y>.parquet` (91–94 MB/yr). By rule 15 that file stays gitignored; only `unit_marginal` is committed.
   - Both legs pushed it on their shard branches (transport only).
   - Nothing under it reaches `main` from this lane: the slim span below carries `unit_marginal` only.
   - The negation in `shard_prompt.py` should re-ignore `unit_hourly_*`.

## 5. Verdict → matrix

**NOT ADJUDICATED (coverage)** (UC-DESK ruling (c)). The MISO matrix cells (`uc_commitment_demand_source`,
`unit_commitment_milp`, `vlr_pocket_commitment`) **stay as on main**. No cell changes in this PR.

## 6. Where the evidence is; what completing the span would cost

| what | where | status |
|---|---|---|
| 2 leg bundles (full, incl. `dispatch/<y>_P1`, and `unit_hourly` as transport) | `claude/ucmilp4-miso-u4-2019` @ `17117ee`, `claude/ucmilp4-miso-u4-2020` @ `52e66dc` | shard branches are transport (rule 33); the owner cuts them |
| slim span | `data/ucmilp4_miso_readings/span_u4_2019_2020/`: system, uc_schedule, uc_uplift, unit_marginal (no `unit_hourly`), uc_solve_log, run_config(s), regenerated diagnostics, meta, metrics | in this PR |
| readings | `data/ucmilp4_miso_readings/`: see below | in this PR |
| composite and local registration | `results/calibration/ucmilp4_miso_u4_span` and the frontend sidecar in the lane container (excluded) | lost with the container |

Files in `data/ucmilp4_miso_readings/`:
- control and U4 verdict JSONs for 2019–20;
- `m1_u4_2019_2020.json` (starts and online hours);
- `u_reads_2019_2020.json` (U-2/U-3, pocket starts);
- the attempt log and leg ledger;
- scratch scripts as `.txt`: composer, gate table, key rows, recipe gate, screen, u-reads.

- **No promotion is proposed.**
- **To complete the span:** 5 shards on ≥ 22.4 GiB containers at the same pin, then re-compose and rescore. The verdict is adjudicable
  only once 2021 (T-1/T-3) and at least one reserve year land.

## Log entry

- 2026-10-15 · UC-4-MISO · arm U4 at `7c93273e` (uc-1.7 + FIX-8).
  - 20 launches (18 reached the memory gate; 2 FIX-8 defect stops) → 2 legs (2019, 2020) solved and verified.
  - 2021–25 held at 3/4 memory attempts (16.4–18.4 GiB vs 22.4).
  - **NOT ADJUDICATED (coverage)** (UC-DESK (c)).
  - Partial: no kill flip; C3a back to the keeper level (+6.2 / +10.6 % vs V +9.1 / +13.8); C4 gas improves; pocket starts 0.98 / 1.67×
    CEMS (V-3 closes).
  - CC starts 0.27 / 0.40× CEMS with online hours above CEMS: r14 min-up revisit triggered.
  - Defects: `shard_prompt` quoting, FIX-8, `unit_hourly` negation.
  - Matrix unchanged. Nothing registered.
