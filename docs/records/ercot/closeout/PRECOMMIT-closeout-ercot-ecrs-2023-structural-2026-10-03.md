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

## Addendum 2 — owner ruling R-46: strip ×33 from 2019–22 (2026-10-03)

Owner ruling **R-46** (2026-10-03, relayed by the desk, verbatim): *"Strip the ×33 bands from 2019–22 after the 2023 result"*. The reasoning is the same as R-42 under rule 1. The ×33 bands are a residual-swept value, not a market mechanism, and 2019–22 has no ECRS at all.

The 2023 K1–K3 reading that this addendum waits on is in §A2.0. This addendum is pushed before any 2019–22 launch.


### A2.0 The 2023 reading this addendum waits on (leg `3783ae77`, pin `2e5d93a2`; bundle fetched and verified)

**K1 PASS.** The `run_config` diff from the keeper's `run_config_2023.json` is exactly the 17 band keys.

**K2 PASS.** 0.0 MWh unserved in 2023, matching the keeper's 0.

**K3 PASS on the D-2 governance read.** Every 2023 C8 class passes:

| class | forced share |
|---|---|
| CC_REGULAR | 0.0107 |
| COAL_LIGNITE | 0.0642 |
| COAL_PRB | 0.0831 |
| CT_PEAKER | 0.1499 (keeper 0.1448; peaker budget 0.15, a thin margin) |
| ST_GAS | 0.1888 |

C6 is confirmed formally on the composed span.

The 2023 D-4 FAIL set equals the keeper's plus one new row: `gas_commitment_bridge × CC_REGULAR`, plant 55223, h0-23, 0.0037 TWh, 23 binding hours.

**2023 readings, reported at full size:**
- C3a −43.2 % (model $36.95 vs actual $65.02; IMM ECRS-neutral counterfactual ≈ $35) FAIL
- C3b 0.790 FAIL
- Both are inside the pre-fixed ranges (−45 % to −30 %; 0.5 to 0.9).
- Mean ORDC adder $2.55. The 2023 shard was archived after verification.

### A2.1 Config delta (per year, the same 17 keys as 2023)

In each year's partition entry, `offer_curve_by_group.<G>.{peak, phys_peak, peak_ladder}` return to the forward (2024–25) values. These are the keys for CC_CHP, CC_INTERMEDIATE, CC_REGULAR, CT_CHP, CT_INTERMEDIATE, CT_PEAKER, ST_GAS and ST_GAS_INTERMEDIATE, all ÷33.

Every other key of the year's recipe is unchanged. That includes `ercot_offer_swcap_clip=true` and `ercot_zonal_spread_ep_referenced=true`, which is the validation partition's existing value. There is no new field and no code change.

### A2.2 Recipe proof (zero LP, solve-stubbed `replay_keeper` at each leg's own code)

For every year:
- the control's `prb_overrides.offer_curve_by_group` equals the keeper's `run_config_<Y>.json` exactly
- there are no top-level kwarg differences
- `prb_overrides` differs only in `offer_curve_by_group`, in exactly 17 band keys

| Year | Pin (leg commit; parent `106d6bb7`, zero code drift) | Leg bundle replayed | Proof |
|---|---|---|---|
| 2019 | `f4e5be977e248eee26a2f513dec73ce3b0eac3c9` | `closeout_ercot_l1_2019` | control = keeper; 17 keys only |
| 2020 | `199c5d82784732339ddb82edb0e5ef9067c1097a` | `closeout_ercot_l1b_2020` | control = keeper; 17 keys only |
| 2021 | `211c34cb8319e41f54d6400a2ea2af38474eae48` | `closeout_ercot_l1b_2021` | control = keeper; 17 keys only |
| 2022 | `cacafbfd6bb4bd4bbcfac793708e30d078ee351e` | `closeout_ercot_l1b_2022` | control = keeper; 17 keys only |

Each shard writes to its own out-dir, `results/calibration/closeout_ercot_ecrs_<Y>`, on branch `claude/closeout-ercot-ecrs-<Y>`.

### A2.3 Pre-fixed readings (measured, reported at full magnitude; not fit bars)

The keeper's values come from the repo scorers on the committed hourlies. Removing a price-raising band lowers peak-hour prices, so C3a is expected to fall in every year.

| Year | C3a keeper | C3b keeper | Expected direction |
|---|---|---|---|
| 2019 | +6.2 % PASS ($49.41 vs $46.55) | 0.216 FAIL | C3a down, likely below actual; C3b may move either way |
| 2020 | +2.5 % PASS ($26.03 vs $25.40) | 0.208 FAIL | C3a down; C3b either way |
| 2021 | +0.8 % PASS ($167.19 vs $165.95) | 0.066 PASS | C3a down (Winter Storm Uri peak hours); largest $ move |
| 2022 | −8.4 % PASS ($68.76 vs $75.08) | 0.178 PASS | C3a down, likely to FAIL (< −10 %) |

The validation scope (2019–22) is NOT-YET today on C1/C3b, and it is expected to stay NOT-YET or worsen. The ISO determination is expected to stay NOT-YET.

### A2.4 Kills, per year

- **K1 recipe.** The new `run_config` diff from the keeper's is only the 17 band keys.
- **K2 shed.** No new unserved energy versus the keeper year: 0 MWh in 2019, 2020 and 2022. In 2021 it must stay ≤ 3,012.6 MWh, with the shed hours a subset of the keeper's 6.
- **K3 governance.** C6 and C8 must pass.

If K1–K3 pass in every year, the recommendation is promotion on structure (rule 1), whatever the direction of C3a or C3b.

### A2.5 Shard protocol

- Four shards, one per year, at most 6 alive at once.
- Environment `env_016R8xUY4maDbppZ6TEns5V8`, auto mode, prompts from `scripts/shard_prompt.py`.
- Step 0: `git fetch origin <sha> && git checkout --detach <sha>`.
- Then `eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"`.
- Run the solve ONCE and stop on the first failure. A shard that stops before the LP is relaunched fresh.

### A2.6 Compose

The 7-year span is the 2019–22 strip legs, the 2023 strip leg, and the 2024 and 2025 keeper legs byte-identical. The ercot-255 `ep_referenced` repair on 2023 stays a separate item and is not folded in.
