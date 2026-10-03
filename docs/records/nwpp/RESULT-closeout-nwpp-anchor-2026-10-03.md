# RESULT closeout-nwpp-anchor: NWPP re-solve on the roster-free plant-basis anchor (2026-10-03)

**Reading: NOT-YET → NOT-YET. Zero record flips. The largest per-record movement is 0.010 TWh. C3a is unchanged.**

**Recommendation: PROMOTE on structure** (PRECOMMIT §3 decision rule). The decoupled anchor is the structurally
correct input (rule 1, rule 14). It costs nothing on any gate, and it ends the anchor's dependence on the
keeper's roster (owner ruling R-28).

## Provenance

- **Charter:** owner ruling R-28, "Keep old figures, fix later" (PR #7076).
- **Records:** `FINDING-closeout-nwpp-anchor-2026-10-03.md`; `PRECOMMIT-closeout-nwpp-anchor-2026-10-03.md` (§5 is
  the re-pin onto NEXT-22b).
- **Code:** PR #7103, merged as `dad1205a2a75a3079874880c879846a346c54dc5`. It carries the derive, the CSV, the
  `nwpp-plant-basis-energy` schema, the test and SolveEpoch 2026-10-03a.
- **Control:** the incumbent keeper `2026-10-03-nwpp-next-22b-w0` (`results/calibration/nwppnext22b_span`, legs at
  `2b8da72a`). Its committed bundle is the control (rule 29(b)); there was no control solve.
- **Candidate:** probe `2026-10-03-closeout-nwpp-anchor-roster`, bundle `results/calibration/closeout_nwpp_anchor_span`.
  - Composed with `scripts/probes/_nwpp42_compose_span.py`: every `scenario_config` field agrees across the seven legs.
  - Attestation from `scripts/gen_closeout_nwpp_anchor_attestation.py`: the keeper's switches and an empty
    exceptions ledger, identical to NEXT-22b's.
- **Scoring basis:** both runs were scored by `calibration_verdict.py --json` on main's kept NWPP bench parts.
  Registration re-rendered the parts; they were reverted per R-28.

## Legs

Each leg is one shard at `dad1205a`, replaying `nwppnext22b_span` with `--years Y` and no `--set`. Every leg has 18
files and contains both `dispatch/<Y>_P1.parquet` and `hourly/unit_marginal_<Y>.parquet`. All shards are archived.

| year | leg SHA (branch `claude/closeout-nwpp-anchor-<Y>`) | notes |
|---|---|---|
| 2019 | `ac4e3caf47646417f7ad9bf65d4de67fed7035f3` | about 91 min; budget extended to 160 min (P0 is cold and slow) |
| 2020 | `016e73188e219c06124b5a7e961a510e3d886960` | about 37 min; peak memory 4.23 GiB |
| 2021 | `6c7dc2d0439e22ed74ac40c0052424c661fa21fd` | |
| 2022 | `18c197b8ce3fb5c83b22324ed9e87bc2ef4ede39` | |
| 2023 | `7e4bbebf4be3c9601bd1f6a7b9f8c17bbcb86b81` | |
| 2024 | `d2494e35dc257bc321daeb85734f63740dc15ac2` | |
| 2025 | `6edd13fcf31cf8c655b17781a97b4939d3e315b9` | P0 877 s, P1 1,297 s |

Unserved energy is 0 MWh in every year. The container preflight warned that ceiling plus swap is 22.4 GiB, below
the 24 GiB target. That warning is about MISO and PJM; NWPP peaked at about 4 GiB.

## Readings, fixed in PRECOMMIT §3

| reading | keeper NEXT-22b | candidate | verdict |
|---|---|---|---|
| Determination | NOT-YET (fuelmix, price_mean, price_shape, dispatch_corr) | NOT-YET (same four) | same |
| FAIL records | 10 | 10 | **0 flips** in either direction |
| C1, all classes | in band except CC_REGULAR 2019 +12.65, 2024 +15.39, 2025 +8.86 TWh | +12.66 / +15.39 / +8.86 TWh | holds (Δ ≤ 0.006 TWh) |
| C3a 2023 vs WEIM ELAP | −10.4 % FAIL (model 40.98 vs 45.72 $/MWh) | −10.4 % FAIL (40.98) | unchanged |
| C3a 2024 | −27.1 % FAIL (29.62 vs 40.65) | −27.1 % FAIL (29.62) | unchanged |
| C3a 2025 ¹ | −0.4 % PASS (32.00 vs 32.13) | −0.4 % PASS (32.00) | unchanged |
| C4 coal 2023 | r 0.770 / NRMSE 0.267 PASS | r 0.771 / 0.267 PASS | holds |
| C4 coal, other years | r 0.743–0.816, all PASS | r 0.741–0.817, all PASS | holds |
| Largest |Δ model| on any record | | 0.010 TWh (sysvol gas 2025) | |
| sysvol, governance (C6), forced_share (C8) | PASS | PASS | same |
| D-1 diurnal (diagnostic) | COAL_BIT / COAL_WC FAIL in several years | same classes | pre-existing, not a new failure |

¹ 2025 carries the EIA-923 data drift: the bench is on the Final vintage since closeout-A, while the completeness
part still marks it preliminary, so the anchor writes COL/NG only. Its readings are labelled accordingly.

The decision rule holds. No criterion worsens in any year, no class leaves its band, and C3a moves by 0.0 pp
against a 2 pp hold bar. That matches the zero-LP expectation (FINDING §3): the anchor re-splits at most 0.13 TWh
between the COL, NG and OTH shapes of the same requirement.

## What a promotion costs

- **Run:** `scripts/promote_keeper.py --iso NWPP --bundle results/calibration/closeout_nwpp_anchor_span …`. It
  registers (already done locally: sidecar plus `runs/<id>.js`), attests, designates, re-keys, audits, and prunes
  NEXT-22b's three stores.
- **Bundle size:** about 196 MB on disk, which includes the gitignored full `unit_hourly`. The span is local to this
  container and does not survive it (rule 31). The seven leg branches above hold every byte, so a later session
  can re-compose without re-solving.
- **Bench parts:** stay at main's render (R-28), because the scoring here used them. The anchor no longer reads
  them, so re-rendering the bench at this or any later promotion would not move the anchor. That re-render is now
  a free choice for the desk.
- **Promotion slot:** this lane holds the next NWPP slot (desk, 01:57Z). NEXT-23 pins after #7103.

## Branches

| branch | state |
|---|---|
| `claude/closeout-nwpp-anchor` | PR #7103, merged (`dad1205a`); deletable |
| `claude/closeout-nwpp-anchor-2019` … `-2025` | the seven held result legs; **not deletable** until promotion lands or the owner declines |
| `claude/closeout-nwpp-anchor-result` | this RESULT + the attestation generator + the matrix cell |

## Promotion (owner ruling R-48, 2026-10-03: "Promote on structure")

The desk relayed the ruling and assigned the NWPP promotion slot at 04:46Z. `scripts/promote_keeper.py --iso NWPP
--bundle results/calibration/closeout_nwpp_anchor_span` designates `2026-10-03-closeout-nwpp-anchor-roster`.

Before the run:

- The attestation was rebuilt on main's G3 schema (`authorized_price_tuning`, `lane_blocks`), with
  `governance.attested_by` set to R-48. `attestation_schema.py --check` reports it valid.
- The span is committed slim, per the repo's gitignore rules. The per-year dispatch stays on the leg branches above.

The run itself:

- **Pruned:** the outgoing keeper `2026-10-03-nwpp-next-22b-w0` (`nwppnext22b_span`).
- **Bench parts:** stay at main's render (R-28). Registration re-renders them, so they were restored and the status
  part was rebuilt on the kept parts.
