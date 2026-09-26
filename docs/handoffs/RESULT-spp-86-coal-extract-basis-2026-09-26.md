# RESULT: SPP-86, coal outage share on the extract's own basis (7-year arm), PROMOTED

Records:
- PRECOMMIT `PRECOMMIT-spp-86-coal-extract-basis-2026-09-26.md`, pinned `d72e5f107a6fe7ca59f94307f37b239e1a48c14f`
  before any shard launched.
- Phase 0 `FINDING-spp-86-coal-floor-conduct-2026-09-26.md`.

The run is registered as `2026-09-26-spp-86-coal-extract`, bundle `results/calibration/spp86_arm_span`.

## 0. Promotion (rule 35 order)

The owner's standing instruction, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If
structural integrity improves but gates regress that may still be a keeper."* and *"When done promote if a
good candidate"*. Steps, in order:

1. **Year set** {2019..2025}, fully covered by `spp86_arm_span`.
2. **Keeper shard.** `keepers/SPP.json` → `2026-09-26-spp-86-coal-extract`, with `config_partition` repointed
   (same tiers).
3. **Audit.** `audit_keepers --iso SPP` passes E1 with the incoming keeper registered.
4. **Prune.** `prune_iso_runs --iso SPP --force-uncite` removed `2026-09-26-spp-85-netload-mask` and
   `spp85_arm_span`. Git history is the record.
5. **Re-key.** `calibration-complete.json` and the forecast board's SPP gate-(a) row now name the new keeper.
   Status is rebuilt: SPP reads **CALIBRATED**.
6. **Matrix.** Cell `unit_outage_coal_extract_basis_share` O → **K**; keeper and gates stamps and §5.7 header updated.
7. **Final audit.** `audit_keepers --iso SPP`: 0 failures. `check_registry_payload_parity`: OK.

## 1. What ran

- **Seven shards, one per year** (rule 36), at the pinned SHA: the keeper recipe plus
  `--set unit_outage_coal_extract_basis_share=true`.
- **No control solve.** G-DRIFT was all-INERT (PRECOMMIT §3), so rule 29(b) form 4 applies: the committed
  keeper is the control.
- **Shard check PASS on all 7 legs.** Recipe = keeper + exactly the one field; gas price matches; six extract
  sha256 match; the resolved path is `-netloadmask-`.
- **Composed** by `_rspp_compose.py --require unit_outage_coal_extract_basis_share=true`.
- **DOF ledger** `--check` reads current: zero new free parameters.

Retrievability (rule 34(e)): the composite is on `main` in registered shape. Leg SHAs are listed in
`.gitignore` as provenance only (rule 33(d)).

## 2. Arm − keeper, P1

| year | COAL_PRB TWh | COAL_LIG TWh | CC_REG TWh | CT_PEAK TWh | ST_GAS TWh | wind TWh | price $/MWh |
|---|---|---|---|---|---|---|---|
| 2019 | +0.667 | −0.037 | −0.221 | −0.323 | −0.062 | −0.002 | −0.134 |
| 2020 | +0.805 | −0.009 | −0.314 | −0.316 | −0.111 | −0.038 | −0.171 |
| 2021 | +1.117 | −0.013 | −0.575 | −0.386 | −0.057 | −0.060 | −0.529 |
| 2022 | +1.096 | −0.033 | −0.593 | −0.321 | −0.085 | −0.053 | −0.671 |
| 2023 | +1.002 | −0.027 | −0.339 | −0.411 | −0.143 | −0.058 | −0.236 |
| 2024 | +1.198 | −0.023 | −0.417 | −0.496 | −0.160 | −0.078 | −0.718 |
| 2025 | +0.791 | −0.025 | −0.273 | −0.317 | −0.107 | −0.035 | −0.220 |

## 3. Scored (rubric at HEAD)

**Determinations:**
- Train tier 2023–25: CALIBRATED → **CALIBRATED** (lone ledgered C3c).
- Validation 2019–22: NOT-YET → NOT-YET (reported, not gating; rule 30(c)).

| criterion | keeper → arm |
|---|---|
| C3a mean LMP | 2019 +12.2 → +11.5 % F; 2020 +18.6 → +17.6 % F; 2021 +4.4 → +3.0 %; 2022 −3.6 → −5.1 %; **2023 −5.2 → −6.1 %; 2024 −6.8 → −9.6 %; 2025 −4.2 → −5.0 %** |
| C3b | 2020 0.264 → 0.259 F |
| C1 COAL_PRB | 2021 +10.31 → +11.43 F; 2022 +12.40 → +13.49 F |
| C1 CC_REGULAR | 2021 −8.98 → −9.54 F; 2022 −9.72 → −10.31 F |
| C4 gas NRMSE | 2021 0.316 → 0.326 F; 2022 0.354 → 0.365 F |
| C3c >$200 h | 2024: 8 → 3 (vs 59) |
| C8 ST_GAS 2022 | 31.5 → 32.1 %, GROUNDED pass |
| **D-4** | **Holcomb 108 `coal_mustrun`: FAIL in 2019 / 20 / 21 / 22 / 24 → PASS in all 7 years** (dark share ≤ 0.10). New row: Harrington 6193 ST_GAS 2024 (binding h 1,526 → 267, zero share 0.34 → 0.985). FAIL rows 11 → 7. |

**2024 C3a sits at −9.6 %, near the −10 % edge.** That is the declared cost (E5), and it is not re-tuned.

## 4. Against the pre-registered rule (PRECOMMIT §6)

| condition | verdict |
|---|---|
| (a) E1 every leg | PASS |
| (b) E2 sign every year (coal up) | PASS |
| (c) E6 slack / dump | PASS: slack MWh keeper → arm 2022 46.8 → 0, 2024 787.1 → 55.5, 2025 76.9 → 76.9, others 0; dump 0 throughout |
| (d) zero new DOF | PASS |
| (e) Holcomb row passes all years **and** no new D-4 row | **Holcomb PASS; one new row → narrow HOLD** |

**The Harrington row is a dilution effect, not new forcing.**
- Restored coal availability carries the plant's lit hours on its coal bin, so the ST_GAS floor's binding hours
  fall from 1,526 to 267.
- The dark binding hours fall too, from about 517 to about 263. Only the share crosses 50 %.

**The pre-registered rule reads HOLD narrowly.** It was promoted on the owner's standing instruction
(structural integrity improves) and on rule 14.

## 5. What the result says

- **The keeper's coal outage share is now one construction, and Holcomb's standing rule-17 row is gone.**
  The input moves toward SPP's published coal outage.
- **As with SPP-85, the more accurate input worsens the 2021–22 coal-vs-CC validation rows.** That is the
  rule-14 signature of compensation elsewhere. FINDING §3 locates most of the gas deficit in wind (EIA-930
  basis) and a 5–7 TWh EIA-923/930 coal disagreement.

## 6. Housekeeping for the owner (sessions cannot delete refs)

Unmerged shard branches `claude/spp86-2019` … `claude/spp86-2025`, plus the earlier `claude/rspp-*` and
`claude/spp85-*`.
