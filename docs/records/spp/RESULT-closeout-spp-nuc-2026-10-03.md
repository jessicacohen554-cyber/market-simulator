# RESULT — closeout-SPP-nuc: SPP keeper re-solved with the measured 2019–22 nuclear monthly CF rows, 2026-10-03

- **Lane:** closeout-spp-nuc. Desk session_01ALecU5Wjde4tkbLrnMExT9. Owner rulings R-35 / R-38.
- **PRECOMMIT:** `PRECOMMIT-closeout-spp-nuc-2026-10-03.md`, pushed at 2db7192d before any shard. Addendum A
  was pushed before any 2019–22 number was read.
- **Control (rule 29(b)):** keeper `2026-10-02-w0-spp107r`, bundle `w0_sppr_span`, all legs at 15a351a1.
- **Run:** `2026-10-03-closeout-spp-nuc-keeper`, bundle `results/calibration/closeout_spp_nuc_span`
  (2019–2025). Registered on the dashboard as a probe.
- **Recipe:** the keeper's, replayed with 0 differing fields and no `--set`.
  - All seven legs are at pin `8c3ea46192074cfd422fff6532acc035d37297bb` (#7109). They share one
    `solve_surface` fingerprint, `4187973695945d73`.
  - The only input change is `NUCLEAR_MONTHLY_CF_BY_YEAR` SPP 2019–22.
  - Zero free parameters added. Offer bands are untouched.
- **Solve:** 7 year-isolated shards (rules 32/36). The parent ran no LP.

## 1. Shards and where the bytes are

| year | shard session (archived) | branch @ commit | bundle |
|---|---|---|---|
| 2019 | session_01MskoNY8nFTKxC7VN3JdzAB | `claude/closeout-spp-nuc-2019` @ 7308a542507350a8677b8b003b2b84d3a1f5c980 | 17 files, incl. dispatch P1 + unit_marginal |
| 2020 | session_01PhCyBHKgmUHCDGJFPiv1pW | `claude/closeout-spp-nuc-2020` @ b49b5e868071ec150a1820d76f0689cbff483069 | 17 |
| 2021 | session_01His8sepoZGeNhSxPXazkax | `claude/closeout-spp-nuc-2021` @ 8effdab327090dc1594663eace9f6b8a82bc876d | 17 |
| 2022 | session_0132YBZaZwWorzz78qwHGEUn | `claude/closeout-spp-nuc-2022` @ a547b82956a0df6193a9dc84bf8c1f5dff35afc7 | 17 |
| 2023 | session_01R7ZyGNoYkPWQjJikKEmmoh | `claude/closeout-spp-nuc-2023` @ 03ba2664d5f5b68f430a519ae52d4711b53dcc63 | 17 |
| 2024 | session_01HQhpETvbRBiMSi3sAGg8Bc | `claude/closeout-spp-nuc-2024` @ 9ccbc7fdcd40402229bcf104ec351bf40a79ca7b | 17 |
| 2025 | session_019tFKqSc8PgA9AvtjAepFqp | `claude/closeout-spp-nuc-2025` @ 975323c14d596dbe86619c43ecef30d1d14b312d | 17 |

- Every leg's parent is the pin, and each commit touches only its own out-dir and `.gitignore`.
- Before each shard was archived, the parent checked out its bytes and verified them with `git ls-tree`
  (rule 34).
- **On `main` (this PR):** the slim span `closeout_spp_nuc_span` carries the configs, attestation,
  diagnostics, metrics and every `hourly/` sidecar, including `unit_marginal_<y>` for all seven years.
  This is the same slim form as `w0_sppr_span`.
  - `dispatch/<y>_P1.parquet` exists only on the shard branches (rule 33 transport) and is gitignored at
    the span.
  - `fleet_census_<y>.json` is not written by a replay leg, so the span does not carry it. The keeper's
    census files describe the same fleet for 2023–25.
- **Promotion cost:** one `promote_keeper.py` call. Nothing has to be re-solved. SPP's `config_partition`
  is re-keyed by hand (W0 RESULT §5 item 5); the composed meta carries no partition block because the
  recipe is single-config.

## 2. G-DRIFT and E-INERT (PRECOMMIT §1, addendum A)

- **Zero-LP identity at the pin:** only 2019–22 `availability` and `min_gen` move. 2023–25 LP inputs are
  bit-identical. At `93bce699`, before #7109, all seven years are bit-identical. Reading 66 files found
  nothing else LIVE.
- **Kept legs refused, then re-solved.** SolveEpoch 2026-10-03b is part of the surface fingerprint and has no
  year scope. Correction: PRECOMMIT §1 claimed the epoch moves only the cache key, and that was wrong. So
  2023–25 were re-solved rather than kept, and the composer check was not weakened.
- **E-INERT PASS.** The re-solved 2023–25 legs reproduce the keeper's `system`, `class_hourly`,
  `unit_marginal`, `class_band_hourly` and `storage` sidecars with max relative difference **0.0**. The
  zero-LP inert proof is confirmed by solve.

## 3. Readings

### R1 + R3 — nuclear and where it went (P1, TWh, run − keeper)

| year | nuclear Δ | FINDING zero-LP Δ (new − old fleet TWh) | model − EIA-923, keeper → run | other classes Δ | unserved / dump | load-weighted price |
|---|---:|---:|---|---|---|---|
| 2019 | **+0.38** | +0.37 | −0.40 → −0.03 | PRB −0.17, CC −0.09, CT −0.08, ST_GAS −0.03 | 0 / 0 | 23.44 → 23.40 |
| 2020 | **+1.04** | +1.02 | −0.97 → +0.05 | CC −0.32, PRB −0.30, CT −0.24, ST_GAS −0.09, wind −0.02 | 0 / 0 | 21.23 → 21.10 |
| 2021 | **−0.12** | −0.12 | +0.34 → +0.23 | wind +0.11, PRB +0.04, CC +0.03, CT −0.03 | 0 / 0 | 40.14 → 40.00 |
| 2022 | **−0.96** | −0.94 | +1.20 → +0.26 | CT +0.32, CC +0.19, PRB +0.16, wind +0.12, ST_GAS +0.11 | 0 / 0 | 41.83 → 41.95 |
| 2023–25 | 0 | 0 | unchanged | none | 0 / 0 | unchanged |

- **The measured rows land where the derive said, within 0.02 TWh.** SPP's nuclear gap to EIA-923 closes
  from up to 1.2 TWh to at most 0.26 TWh, the residual being the LP pmax clip the FINDING documents.
- **PRECOMMIT §2 transcription error, stated.** Its "expected nuclear Δ" column (−0.40 / −0.97 / +0.35 /
  +1.20) was copied from the charter. Those are the keeper's model − EIA-923 gaps (FINDING table, column 8),
  not the change, so their sign is the opposite of the correction.
  - R1 as literally written ("sign right") therefore fails in all four years.
  - Against the FINDING's own zero-LP Δ, which is what the rows were derived to do, the solve matches to
    0.02 TWh.
  - R1 was reported, not gating. No gate reads it.
- In 2021 the nuclear increment is small (−0.12 TWh) and wind takes most of it back: curtailment falls.

### R2 — per-(criterion, year) diff vs `w0_sppr_span` (`calibration_verdict.py`, rubric as on main)

**No status flips in any year. Determination NOT-YET → NOT-YET.** 2023–25 are identical on every row.

| year | criterion | keeper → run |
|---|---|---|
| 2019 | C3a mean LMP | +12.4 % → +12.3 % (FAIL both) |
| 2019 | C3b NRMSE | 0.158 → 0.160 (PASS) |
| 2019 | C1 COAL_PRB / CC / CT / ST_GAS | +0.42 → +0.24 / +2.33 → +2.25 / +1.58 → +1.49 / −4.93 → −4.96 TWh (all PASS) |
| 2019 | C4 gas / coal | r 0.967 → 0.966, NRMSE 0.131 → 0.133 / r 0.951 → 0.953, NRMSE 0.125 → 0.124 (PASS) |
| 2020 | C3a | **+28.5 % → +27.7 %** (FAIL both; toward band) |
| 2020 | C3b | **0.356 → 0.345** (FAIL both; toward band) |
| 2020 | C1 COAL_PRB / CC / CT / ST_GAS | −2.73 → −3.03 / +1.92 → +1.60 / +6.38 → +6.15 / −3.34 → −3.42 TWh (all PASS) |
| 2020 | C4 gas / coal | NRMSE 0.187 → 0.182 / 0.181 → 0.184 (PASS) |
| 2021 | C3a | +7.4 % → +7.1 % (PASS) |
| 2021 | C3b | 0.171 → 0.176 (PASS) |
| 2021 | C1 CC_REGULAR | −8.95 → −8.92 TWh (FAIL both; toward band) |
| 2021 | C1 COAL_PRB | +10.95 → +10.98 TWh (FAIL both; away, +0.03) |
| 2021 | C3c | 374 h → 372 h vs 140 (CAVEAT both) |
| 2021 | C4 gas | NRMSE 0.279 → 0.276 (PASS) |
| 2022 | C3a | −5.1 % → −4.8 % (PASS) |
| 2022 | C3b | 0.188 → 0.175 (PASS) |
| 2022 | C1 CC_REGULAR | −9.35 → −9.16 TWh (FAIL both; toward band) |
| 2022 | C1 COAL_PRB | +10.59 → +10.75 TWh (FAIL both; away, +0.16) |
| 2022 | C1 CT_PEAKER | −1.70 → −1.39 TWh (PASS) |
| 2022 | C4 gas | NRMSE 0.320 → 0.313 (FAIL both; toward band) |
| 2022 | C8 ST_GAS forced | 34.6 % → 33.8 % (grounded conditional PASS both) |

**Watch rows (PRECOMMIT §3):**
- C1 COAL_PRB 2021/22 moves away by +0.03 / +0.16 TWh. In 2022 the measured Wolf Creek / Cooper fall
  outage hands 0.96 TWh back to thermal, and coal takes 0.16 of it.
- C1 CC_REGULAR 2021/22 moves toward the band by +0.03 / +0.19.
- None of these crosses a band edge.

### R4 — legitimacy diagnostics

- D-4: the same 7 FAIL rows as the keeper (1230 2019; 3008 2019/20/21/23/24; 6193 2024). None new, none gone.
- C8: PASS in all years.
- C6 governance: PASS (attestation carried forward with this lane's entry).

## 4. Regression rule and recommendation (PRECOMMIT §3)

| gate | result |
|---|---|
| no PASS → FAIL / CAVEAT → FAIL flip, any year | **PASS** (0 flips) |
| every leg Optimal | **PASS** (7/7 bundles written and complete) |
| unserved not up > 500 MWh vs keeper | **PASS** (0 → 0 in every year) |
| no new D-4 FAIL row | **PASS** (identical 7) |
| C8 PASS | **PASS** |
| E-INERT (addendum A) | **PASS** (bit-identical 2023–25) |

**RECOMMEND PROMOTE on structure (rule 14 [R-ACCURATE]).**
- Measured EIA-923 nuclear availability replaces a year-invariant fallback, and SPP's nuclear volume error
  closes from up to 1.2 TWh to ≤ 0.26 TWh.
- The cost is +0.03 / +0.16 TWh on two already-failing COAL_PRB rows.
- The gain is C3a / C3b 2020 moving toward the band, and C4 gas 2022 and CC 2021/22 moving toward the band.
- The train tier 2023–25 is bit-identical, and the determination is unchanged.
- Promotion happens only on the owner ruling relayed by the desk, in the desk's slot (rule 31).
- Nothing was deleted, and every leg is on its shard branch until this PR merges.

## 5. Promotion (desk, 2026-10-03)

Owner ruling **R-44 "Promote on structure"** (card answered 2026-10-03, relayed by the desk; recorded in
`docs/backcast-closeout-plan-2026-10.md` §5.0). The lane's own `promote_keeper.py` call was refused by its
permission classifier ("Modify Shared Resources"), so the desk ran the identical command on this branch:
register → attest (outgoing exceptions ledger `[]`; DOF ledger written) → designate keeper
`2026-10-03-closeout-spp-nuc-keeper` → gate.a marker `w0-spp107r` → new keeper → status rebuild (SPP NOT-YET)
→ audit (E13 tolerated, then the strict audit stopped on E12: `config_partition.configs[].run_id` named the
pruned `w0-spp107r`; re-keyed by hand to the new run and bundle, the W0 RESULT §5 item 5 precedent, after
which the audit is clean) → prune `w0_sppr_span` (own ISO) → parity OK. The dispatch legs were copied from
the seven shard branches into the span's gitignored `dispatch/` for the preflight only; the keeper bundle on
`main` is the slim layer plus `fleet_census_<y>.json` built by the preflight.

