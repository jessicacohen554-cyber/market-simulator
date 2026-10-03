# PRECOMMIT — closeout-ERCOT-ECRS: the structural 2023 config (R-39, option A)

Written before any shard is launched. It takes effect only on the desk's relayed "go" for option A.
Phase 0: `FINDING-closeout-ercot-ecrs-phase0-2026-10-03.md`.

## 1. The config delta (one 2023 partition entry, no new field)

The 2023 leg is the keeper's own 2023 recipe (`closeout_ercot_l1b_2023` at `106d6bb7`). Its only change is that `offer_curve_by_group.<G>.{peak, phys_peak, peak_ladder}` return to the forward (2024–25) values. These are the 17 keys across CC_CHP, CC_INTERMEDIATE, CC_REGULAR, CT_CHP, CT_INTERMEDIATE, CT_PEAKER, ST_GAS and ST_GAS_INTERMEDIATE, all ÷33.

**Everything else is unchanged**, including the armed 2023 ECRS stack:
- `ercot_ecrs_conservative_deployment`: rigid at VOLL for the whole of 2023, on the measured ASPLANNP433 plan from go-live h3839
- `ercot_nonreleasable_as_withholding`
- `ercot_multiproduct_as_coopt`
- `ercot_ordc_total_reserve` with the R-ERCOT-24b published curve
- the RTORDPA overlay
- `ercot_offer_swcap_clip = true`. It is retained as the SWCAP protocol cap and stays inert below the cap (ercot-236 V-0). It is also what binds the R-6 configuration-exception caveat (`CONFIG_EXCEPTION_ENTRIES.config_signature`).
- `ercot_zonal_spread_ep_referenced = false`. Out of R-39 scope; flagged for the owner.

With the ×33 bands gone, the 2023 config's ECRS content is carried only by its real mechanism, date-keyed to the published instruments. That is R-39's "unique config for 2023 … reflects the market reality".

- **Rule 24.** No new ScenarioConfig field and no off-registry channel. The 2023 partition entry in `meta.json` `config_partition_overrides` and `run_config_2023.json` carries it. No matrix row is added. The `offer_curve_by_group` and `ercot_multiproduct_as` cells get evidence notes.
- **Rule 26.** No field becomes dead. The bands stay in use for the 2024–25 forward values and the 2019–22 ×33 validation recipe, which is out of R-39 scope (see §6).
- **Rule 21.** The DOF ledger loses the 2023 ×33 band values, which were residual-identified (ercot-236 §4, min |C3a-2023| over k).
- **Tests.** No code changes, so no new test. The briefed "withheld MW lift the ORDC adder" test belongs to the killed element. The withheld-at-VOLL behaviour is already covered by the existing `ercot_ecrs_conservative_deployment` unit tests.

**Recipe proof (zero LP).** At `106d6bb7`'s own `replay_keeper`, with `solve_and_persist` stubbed, the captured kwargs with and without the `--set` differ **only** in `prb_overrides.offer_curve_by_group`, and only in the 17 keys above. The control's bands equal the keeper's `run_config_2023.json` exactly.
- The composed keeper `meta.json` is **not** replayable at `106d6bb7`: "meta.json keys not bound". So the shard replays the leg bundle.

## 2. Shard (one: 2023)

- **Pin.** `2e5d93a24222e75b04b802ddff85b945de1699ca`, the l1b-2023 leg commit. It is `106d6bb7` plus the leg bundle, so code drift is zero and no G-DRIFT audit applies.
- **Solve command.** `python3 scripts/replay_keeper.py results/calibration/closeout_ercot_l1b_2023 --years 2023 --out-dir results/calibration/closeout_ercot_ecrs_2023 --set offer_curve_by_group=<the 2023 dict with forward peak/phys_peak/peak_ladder>`
- **Environment.** `env_016R8xUY4maDbppZ6TEns5V8`, auto mode, prompt from `scripts/shard_prompt.py`.
  - Step 0: `git fetch origin <sha> && git checkout --detach <sha>`.
  - Before the solve: `eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"`, if that script exists at the pin.
  - Never `--no-container-preflight`.
- **Compose.** Single-SHA: 2019 from l1, 2020–22 and 2024–25 from l1b, all at `106d6bb7`. The 2023 leg is the new one at the same code. The other six legs stay byte-identical.

## 3. Pre-fixed reading (a measurement, not a fit bar)

| quantity | keeper (×33) | expected (option A) | basis |
|---|---|---|---|
| C3a 2023 | −24.7 % ($48.98 vs $65.02) | −45 % to −30 % | forward-band 2023 on earlier keepers: −39.7 % (ercot-226/227), −33.2 % (ercot-217 lineage) |
| C3b 2023 | 0.393 | 0.5 to 0.9 | ercot-227 forward-band 0.729 |
| carve-out-2023 scope determination | CALIBRATED (R-6 caveat) | CALIBRATED (R-6 caveat, signature retained) | `calibration_verdict` |
| ISO determination | NOT-YET (forward C3a 2024; validation C1/C3b) | unchanged | worst-of |

The C3a/C3b numbers are reported at full magnitude beside the IMM ECRS-neutral counterfactual (≈ $35 load-weighted).

## 4. Kill gates (legitimacy; pre-registered)

- **K1 recipe.** The new `run_config_2023.json` `scenario_config` differs from the keeper's only in the 17 band keys. Any other diff voids the leg.
- **K2 shed.** The keeper has 0 MWh of 2023 unserved energy. Any new unserved energy is a FAIL.
- **K3 governance.** C6 and C8 2023 must stay PASS.
- **K4, reported only.** Any C1/C2/C4 2023 status change is reported but does not gate.

## 5. Recommendation rule (fixed now)

If K1–K3 pass, recommend **promotion whatever the direction of C3a**. Rule 1: the most structurally faithful run is the keeper, and a worse fit after removing a residual-swept band is the honest reading. The 2023 miss is the adjudicated model-class object (Door D).

Promotion follows the relayed ruling and the desk's slot grant. At promotion:
- the partition is re-keyed by hand (W0 RESULT §5 item 5)
- the attestation gains an explicit `authorized_price_tuning` block: "none under the channel", because the ERCOT bands pre-date and do not satisfy the 2026-09-05 channel

## 6. Flagged for the owner (out of R-39 scope, no action)

- The 2019–22 validation legs carry the same ×33 bands, and that period has no ECRS. If the bands are not an ECRS object in 2023, they are not one in 2019–22 either. Stripping them is four shards and would be a separate ruling.
- 2023 lacks the ercot-255 `ercot_zonal_spread_ep_referenced` repair that the forward config carries.
- The composed bundle includes 2025, so the card carries the **2025 EIA-923 data-drift label**.

## Addendum 1 — owner ruling R-42 and launch (2026-10-03)

Owner ruling **R-42** (2026-10-03, relayed by the desk, verbatim): *"A: Remove ×33 from 2023"*. Option A is executed exactly as written above. K1–K3 are the only kills. The recommendation is promotion whatever the direction of C3a, reported at full size beside the IMM ECRS-neutral ≈ $35. The 2019–22 ×33 strip is a separate ruling and is not launched. Promotion runs only after the desk grants the ERCOT slot.

Shard `session_016m22us1qUxP2JmFqPEg9ob`, environment `env_016R8xUY4maDbppZ6TEns5V8`, auto mode, pin `2e5d93a24222e75b04b802ddff85b945de1699ca`, out-dir `results/calibration/closeout_ercot_ecrs_2023`, branch `claude/closeout-ercot-ecrs-2023`.

Launch note: the session was first created with a one-word placeholder prompt by mistake. It was interrupted at once and given the full shard_prompt.py text, with step-0 checkout, prepare_solve_container exports, the K1 recipe-diff check and the single-quote `--set` instruction. No solve ran under the placeholder.
