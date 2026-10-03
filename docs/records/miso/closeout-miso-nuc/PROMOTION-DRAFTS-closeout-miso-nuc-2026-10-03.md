# PROMOTION DRAFTS — closeout-miso-nuc (owner ruling R-53 "Promote on structure")

These are the edits that remain this lane's after `promote_keeper.py` runs. They were drafted before the slot was granted. Every number marked `⟨post⟩` is re-read from the live scorer after promotion; every other number below is already final (RESULT §3).

**Outgoing keeper:** `2026-10-02-w0-miso-fix2` (`w0_miso_span`).
**Incoming keeper:** `2026-10-03-closeout-miso-nuc-r` (`closeout_miso_nuc_span`).

## 0. Attestation, already on the lane branch

`results/calibration/closeout_miso_nuc_span/calibration_attestation.json` is written and passes `attestation_schema.validate`. It holds:

- **`governance`:** the outgoing keeper's block, carried unchanged, with a new `attested_by` (lane, R-43, R-53, pin, recipe check) that prefixes the prior text.
  - Its four booleans are carried as they are, including the two `False` values (`levers_trace_to_measured_input`, `no_fit_to_price_residuals`). Those belong to rule 1's authorized `offer_curve_by_group` channel.
  - `promote_keeper.attest` never overwrites an existing key, so `--attested-by` cannot flip them to `True`.
- **`governance.authorized_price_tuning`:** carried unchanged — the ×1.10 bands, the CC exemption (miso-275), and the ruling text. The top-level `authorized_price_tuning: {declared: true}` agrees with it.
- **`free_parameters`:** the outgoing ledger's 5 entries, carried. `build_dof_ledger.py` refreshes them at promotion. The recipe adds zero DOF.
- **`exceptions`:** empty. `promote_keeper.py` carries the outgoing ledger forward (storage 2025, storage_shape 2025, price_tail 2023/2024/2025, price_mean 2025), re-measures the C3c entries, and refuses any entry that no longer applies.
- **`disclosures`:** the new note (a)–(c), with the outgoing note inherited as (d).

## 1. `docs/codebase-site/data/mechanism-matrix/MISO.js` — keeper and gates stamp

```js
  updated: "2026-10-03",
  keeper: "2026-10-03-closeout-miso-nuc-r",
  gates: "(2026-10-03, closeout-miso-nuc, owner rulings R-43 'Full repair + 7 MISO shards' and R-53 'Promote on structure') KEEPER 2026-10-03-closeout-miso-nuc-r (bundle closeout_miso_nuc_span, 2019-2025, 7 year-isolated shards at f98c4564) = the W0 fix-2 keeper recipe with the rule-14 nuclear repair only: NUCLEAR_MONTHLY_CF_BY_YEAR[MISO] 2019-22 rows (frozen derive), NRC daily extract 2019-2025 with Duane Arnold/Palisades pass-through (SolveEpoch 2026-10-03d, PR #7129). Zero DOF. Nuclear 2019-22 +0.3/+0.1/+0.8/+0.4 % vs EIA-923 plant-matched (was -4.6/+2.6/-2.2/-1.5). 2023-25 byte-identical. PASS->FAIL (fit-negative, accepted as baseline): C1 CC_REGULAR 2021 -6.83 -> -8.15 TWh; C3a 2020 +9.6 -> +10.2 %. Still FAIL: C1 ST_GAS 2019 -8.60 -> -8.71 TWh; C3b 2021 0.213 -> 0.219. C3a vs RT 2019..2025 +6.2/+10.2/-8.4/-6.9/⟨2023-25 unchanged⟩. Determination ⟨post⟩. Next MISO levers (R-53): C1 CC_REGULAR 2021 and C3a 2020. || PRIOR GATES: " + <the current gates string, verbatim>,
```

No cell changes. The repair is not a `ScenarioConfig` mechanism. If the desk wants an evidence line, the closest cell is `nuclear_unit_availability` (stays K):

> closeout-miso-nuc (2026-10-03, R-43/R-53, KEEPER): the extract now spans 2019-2025 (Duane Arnold/Palisades pass-through; River Bend 2019 rename aliased); verified in the solve (Palisades 2021 hourly cap r=1.00 vs NRC daily; Duane Arnold Sep 2020 0 MW). WEDGE_TOL drops most 2019-22 months (1/3/3/4 kept), where the fleet anchor row stands.

## 2. `docs/mechanism-testing-matrix.md` — §5.4 MISO header

Prepend the following, and demote the current header to `PRIOR HEADER:`:

> ### 5.4 MISO — **KEEPER 2026-10-03 (lane closeout-miso-nuc, owner rulings R-43 / R-53 "Promote on structure"): `2026-10-03-closeout-miso-nuc-r`** (bundle `results/calibration/closeout_miso_nuc_span`), 2019–2025: the W0 fix-2 recipe plus the rule-14 nuclear data repair only (2019–22 measured monthly CF rows; NRC daily extract 2019–2025 with Duane Arnold/Palisades; SolveEpoch 2026-10-03d). Zero DOF. Nuclear 2019–22 within +0.8 % of EIA-923. Fit-negative, accepted as baseline: C1 CC_REGULAR 2021 PASS → FAIL (−8.15 TWh), C3a 2020 PASS → FAIL (+10.2 %); ST_GAS 2019 −8.71, C3b 2021 0.219 still FAIL. **Next levers (R-53): C1 CC_REGULAR 2021, C3a 2020.** Records: `docs/records/miso/closeout-miso-nuc/`. PRIOR HEADER: …

## 3. `docs/calibration-log/miso.md` — entry

```markdown
## closeout-miso-nuc — 2026-10-03 — MISO nuclear 2019–2022 at measured data (R-43), PROMOTED (R-53)

**Change.** The rule-14 data repair only, landed as PR #7129 (merge `f98c4564`):
- `NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"]` 2019–2022 rows from the frozen derive;
- the NRC daily extract re-derived 2019–2025, with Duane Arnold and Palisades as pass-through rows;
- SolveEpoch 2026-10-03d.

**Solve.** Seven year-isolated shards at the pin, composed with `_w0_compose_span.py`. Dispatch legs 2019 and 2021–25 are zstd-9 re-encodings (GH001 transport, table-equal).

**Nuclear vs EIA-923 (plant-matched):** +0.3 / +0.1 / +0.8 / +0.4 % (was −4.6 / +2.6 / −2.2 / −1.5). 2023–25 are byte-identical to the outgoing keeper.

**Promoted 2026-10-03 (owner ruling R-53 "Promote on structure").** `promote_keeper.py` ran at commit ⟨post⟩. The outgoing ledger carried ⟨post: entries / re-measured C3c⟩, the DOF ledger was refreshed, `w0_miso_span` was pruned, and audit and parity are ⟨post⟩.

**The keeper is `2026-10-03-closeout-miso-nuc-r`.** Determination NOT-YET ⟨post: scored / target / ledgered / fail⟩.

| Year | C1 | C2 | C3a | C3b | C4 | C8 |
|---|---|---|---|---|---|---|
| 2019 | **FAIL** ST_GAS −8.71 | PASS | PASS +6.2 % | PASS 0.091 | PASS | PASS |
| 2020 | PASS | PASS | **FAIL** +10.2 % | PASS 0.147 | PASS | PASS |
| 2021 | **FAIL** CC_REGULAR −8.15 | PASS | PASS −8.4 % | **FAIL** 0.219 | PASS | PASS |
| 2022 | PASS | PASS | PASS −6.9 % | PASS 0.127 | PASS | PASS |
| 2023 | ⟨post: unchanged⟩ | | | | | |
| 2024 | ⟨post: unchanged⟩ | | | | | |
| 2025 | ⟨post: unchanged; price_mean 2025 ledgered⟩ | | | | | |

**Next levers (R-53):** C1 CC_REGULAR 2021, C3a 2020.
```

## 4. RESULT — §6 Promotion (to append)

```markdown
## 6. Promotion

Owner ruling **R-53** (2026-10-03): "Promote on structure". `promote_keeper.py` ran at ⟨post commit⟩ in the desk-granted MISO slot:
- register;
- attest — governance carried with the two rule-1 `False` values, the outgoing exceptions ledger carried, C3c re-measured ⟨post⟩;
- designate, fold, re-key;
- status rebuild;
- audit;
- prune `w0_miso_span` (MISO only);
- parity ⟨post⟩.

The keeper is `2026-10-03-closeout-miso-nuc-r`. The determination is NOT-YET ⟨post⟩. The year set 2019–2025 is unchanged.
```

## 5. `frontend/data/backcast/keepers/MISO.json` — superseded block and `config_partition` re-key

`promote_keeper.py` writes `keeper`. The lane adds the following, following the miso-280 block pattern:

```json
"keeper_at_promotion_closeout_miso_nuc": {
  "from": "2026-10-02-w0-miso-fix2",
  "to": "2026-10-03-closeout-miso-nuc-r",
  "delta": "rule-14 nuclear data repair only (R-43): NUCLEAR_MONTHLY_CF_BY_YEAR[MISO] 2019-22 rows + NRC daily extract 2019-2025 (Duane Arnold/Palisades pass-through) + SolveEpoch 2026-10-03d; recipe otherwise identical (no --set)"
},
"promotion_note_closeout_miso_nuc": "PROMOTED (closeout-miso-nuc) ON THE OWNER'S RULING R-53 2026-10-03 ('Promote on structure') on docs/records/miso/closeout-miso-nuc/RESULT-closeout-miso-nuc-2026-10-03.md. Nuclear 2019-22 within +0.8 % of EIA-923 (was -4.6..+2.6). Full magnitude: PASS->FAIL C1 CC_REGULAR 2021 -6.83 -> -8.15 TWh and C3a 2020 +9.6 -> +10.2 % (fit-negative, MISO's new baseline, rule 14); C1 ST_GAS 2019 -8.60 -> -8.71; C3b 2021 0.213 -> 0.219; 2023-25 byte-identical. Zero DOF. Next levers: C1 CC_REGULAR 2021, C3a 2020."
```

`config_partition.iso_determination_ruling` re-key: prepend

> UPDATED AT THE closeout-miso-nuc PROMOTION (2026-10-03, R-53, re-verified against the live scorer): on the CURRENT keeper 2026-10-03-closeout-miso-nuc-r, MISO's train tier {2023, 2024, 2025} is byte-identical to the outgoing keeper and scores ⟨post⟩. The validation years 2019-2022 stay published per-year at full magnitude (C1 ST_GAS 2019 −8.71 TWh, CC_REGULAR 2021 −8.15 TWh FAIL; C3a 2020 +10.2 % FAIL; C3b 2021 0.219 FAIL). --- prior text: …

Also refresh `determination_at_head` from `iso_determination` ⟨post⟩. `build_status.py` overwrites the published value.

## 6. Order once "MISO slot GRANTED" arrives

1. `git fetch origin main && git merge origin/main` on the lane branch. Re-run the gates.
2. `python scripts/promote_keeper.py --iso MISO --bundle results/calibration/closeout_miso_nuc_span --label "closeout-miso-nuc R-43 MISO nuclear 2019-22 measured repair (7-yr re-solve)"`, with no `--attested-by` (governance is already complete) and no `--dry-run` before the slot. If it is refused, report and stop.
3. Apply §1–§5, filling ⟨post⟩ from `calibration_verdict.py --run-id 2026-10-03-closeout-miso-nuc-r`.
4. Run `check_mechanism_matrix.py --base origin/main`, `audit_keepers.py`, and the fast lane.
5. Commit and push. Open the PR with the standard footer and self-merge on green. If refused, report and stop.
