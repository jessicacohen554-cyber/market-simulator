# Kept-leg byte-inert proof: W0 phase 3 mixed-SHA composes (MISO, PJM, NWPP, SOCO), 2026-10-02

**Zero LP.** Desk ruling (14:31): every leg whose LP inputs are NOT byte-identical between its solve SHA and
fix-2 `25da6022` re-solves from `25da6022`, with no materiality threshold. Every leg that is kept needs a zero-LP proof
that its LP inputs are byte-identical at `25da6022`. This note is that proof. The composer records it as
`meta.mixed_solve_sha.inert_proof` (`scripts/probes/_w0_compose_span.py --pinned-sha YEAR=SHA --inert-proof`).

## Kept legs

| ISO | Year | Solve SHA | Shard branch @ commit | Link 1: drift to eec4eb5c | Link 2: #7047 (eec4eb5c → 837556d2) | Link 3: fix-2 #7049 (837556d2 → 25da6022) |
|---|---|---|---|---|---|---|
| ~~NWPP~~ | ~~2019~~ | ~~306f2c00~~ | ~~`claude/w0-nwpp-2019` @ 0b3385eb~~ | SUPERSEDED: the leg records `unit_outage_dispatched_bin_live_denominator=False`, a rule-26-deleted field that NWPP owns, so False is not inert. Preflight 0d refused it, and 2019 was re-solved at `25da6022` (`claude/w0-nwpp-2019-fix2` @ 7a0c9242). | | |
| SOCO | 2019 | 306f2c00 | `claude/w0-soco-2019` @ 2cde5e95 | INERT | identical | identical |
| SOCO | 2020 | 306f2c00 | `claude/w0-soco-2020` @ cb211a43 | INERT | identical | identical |
| SOCO | 2021 | 306f2c00 | `claude/w0-soco-2021` @ 3f5b8c1d | INERT | identical | identical |
| SOCO | 2022 | 837556d2 | `claude/w0-soco-2022-fix` @ e033f991 | (solved at 837556d2) | (solved at 837556d2) | identical |
| PJM | 2024 | ce8820dd | `claude/w0-pjm-2024` @ 481ca491 | INERT | identical | identical |
| PJM | 2025 | ce8820dd | `claude/w0-pjm-2025` @ 1d3c6510 | INERT | identical | identical |

No MISO leg is kept: all seven re-solve at `25da6022`.

## The three links

1. **Drift audit (G-DRIFT, code only).**
   - 306f2c00 → eec4eb5c:
     - `renewables.py` and `zone_assignment.py` (#7040) are gated on `fleet_zone_vintage_coords`, which is OFF in the MISO, NWPP, SOCO and NEISO keepers. The `zone_assignment` signature is identical under the defaults. **INERT.**
     - `constants.py` touches NYISO anchor rows only (rule 25). **INERT.**
     - `cache.py` changes prose and the ledger only. **INERT.**
   - ce8820dd → eec4eb5c (PJM): NYISO-only constants plus cache prose. **INERT.**
2. **#7047** (eec4eb5c → 837556d2; the only `src/` change in that range).
   - Evidence: `W0-denominator-fix/inert_sweep.json`. It hashes availability, pmax, pmin and min_gen per keeper-year, before vs after.
   - Byte-identical: NWPP 2019, SOCO 2019–21, PJM 2024–25.
3. **Fix-2 #7049** (837556d2 → 25da6022).
   - Evidence: `RESULT-closeout-w0-denominator-fix-2-2026-10-02.md` §4 and `W0-denominator-fix-2/sweep/`.
   - Byte-identical on all four arrays: NWPP 2019–20, SOCO 2019–22, PJM 2024–25, MISO 2020 and NEISO 2019–25.
   - NWPP 2019 is identical only with the 1.0 clip on `cod_ramp.bin_online_fraction`. That clip is part of #7049 (`test_one_ulp_over_one_is_fully_online`).

The chain is closed for every kept leg: each leg's LP inputs at its solve SHA equal its LP inputs at `25da6022`.

## Legs that re-solve, and why

| ISO | Years | Reason |
|---|---|---|
| MISO | 2019, 2021–25 | moved under fix-2 |
| MISO | 2020 | its only leg is at 306f2c00, and #7047 moved it (−0.033 TWh) |
| NWPP | 2021–25 | moved under fix-2 |
| NWPP | 2020 | its only leg is at 306f2c00, and #7047 moved it (−0.199 TWh); fix-2 is identical, but link 2 fails |
| PJM | 2019–23 | moved under fix-2 (2020: −0.001 TWh) |
| SOCO | 2023–25 | moved under fix-2 |

## Composer checks that still bind

- One `solve_surface` fingerprint per ISO across all legs. Verified pre-compose: MISO a4ebec6b29ae93a1, NWPP cdfc3a53f739fab0, PJM 23d4cbb5d30aefb0, SOCO 3625249cfeb04343. SolveEpoch 2026-10-02d re-keys `cache_key`, not the surface fingerprint.
- Each leg must match its pinned SHA.
- The recipe is the keeper's plus W0 on every field.
- `promote_keeper` preflight 0d (replay recipe, with the rule-26 deletion registry from #7052) must pass.
