# PRECOMMIT: UC-MISO-VLR, VLR commitment requirement replacing the ST_GAS per-plant floor, at uc-1.6

**In force.** Written and pushed before the build PR and before any shard. Values in ⟨⟩ (the pin and the G-DRIFT
result) are filled in Addendum A after the build PR merges. Nothing else may change there.

**Owner rulings (2026-10-15, relayed by UC-DESK `session_01WX9W5tgYMre3Z134LZoGF6`) on
`FINDING-ucmiso-vlr-phase0-2026-10-15.md` §5:**
- **Q1 = A.** ≥ 1 committed unit per MTEP15 group, 0 fitted DOF. The Amite South D-4 FAIL is declared ex ante.
- **Q2 = accept.** The non-pocket floor energy is lost under rule 19. No self-commitment lane.
- **Q3 = current `uc-params` mlf.** The CEMS-LSL min-load gap is routed to lane UC-DATA-UT.

UC-DESK GO for the build PR; the arm-V shards follow its merge.

## 1. Control, arms, pin

- **Control.** The keeper's committed bundle `results/calibration/closeout_miso_nuc_span` (rule 29(b)). G-DRIFT
  runs `2dd69d5a → ⟨pin⟩` zero-LP; only LIVE hunks are named.
- **Arm V (the one logical delta).** The UC-3 arm B recipe, which is keeper + `unit_commitment_milp=true` +
  `st_gas_mustrun_per_plant=false`, plus `vlr_pocket_commitment=true`. The new field:
  - adds, in each UC window, the row `Σ_{c∈G_k} u[c,t] ≥ min(N_k, available units)` for each MTEP15 pocket group k
    (option A: N_k = 1 per group; WOTAB groups D + E share Sabine's one n=4 cluster, so N = 2 on that cluster);
  - takes its group sets from a committed source table `vlr-pocket-groups` (MTEP15, PUCT 46416 CWL-5, data-intake
    skill, schema-first; one row per group: pocket, group, EIA plant code, units, N_k, source page);
  - is default off, byte-identical off, cache-keyed and registered on the solve surface, with a matrix row plus a
    cell in every shard (rule 28).
- **Rule 19.** Arm V removes the per-plant floor on **every** plant, pocket and non-pocket alike (FINDING §5 Q2).
  The p25/oom level sub-flags go inert with it (UC-3 PRECOMMIT §1).
- **Comparator arm.** UC-3 arm B 2019–22 legs are reused as evidence, not re-solved. 2023–25 B is not required.
- **Pin.** The merge SHA of the build PR (uc-1.6 + the VLR row), as a full 40-char SHA.
- **Recipe gate per leg.** As in the UC-3 PRECOMMIT §1. Allowed diffs: `unit_commitment_milp`, the `uc_*`
  defaults, `st_gas_mustrun_per_plant=false`, `vlr_pocket_commitment=true`.

## 2. Years and shards

All 7 years, 2019–2025, one shard each (rules 16, 32, 36). Containers ≥ 22.4 GiB, launched serially (r11 infra
note). Composed by `_ucmilp_compose_span.py`; diagnostics are regenerated.

## 3. Readings, fixed ex ante

**Binding (verdict).**

| id | reading | pass bar |
|---|---|---|
| V-1 | P1 unserved, every year | ≤ keeper + 500 MWh (2024: ≤ 8,856.9) |
| V-2 | eligible-group on-share vs CEMS ≥ 1 share (FINDING §4 table), DSG / WOTAB / Western | within ±0.15 of CEMS in ≥ 6 of 7 years per pocket |
| V-3 | ST_GAS starts ÷ CEMS (pocket plants) | in [0.5, 2.0] every year (arm B 0.64–1.08; keeper 3.2–6.4) |
| V-4 | D-4 rows on the VLR mechanism | 0 FAIL in DSG / WOTAB / Western. Amite South FAIL rows **declared expected** (owner ruling Q1) and reported, not binding |
| V-5 | ST_GAS D-2 forced share (C8) | ≤ cap every year (MECH 28 + VLR combined) |

**Target (sign + bar, half the distance to the band).**

| id | reading | bar |
|---|---|---|
| T-1 | C1 ST_GAS gap vs arm B (2019–22) | narrows by ≥ 0.7 TWh in each year (≈ half the §4 sizing lower bound, 1.1–1.5) |
| T-2 | C3a 2019 vs arm B | moves toward 0 (arm B +13.3 %) |

**Reported, not binding.**
- C1 by class, C3b, C3c magnitude, C4.
- Price by load band (the UC-3 price_diag rows).
- Uplift share and VLR-row duals; the duals are integer rows, so they are **not** priced (Wang 2018) and never
  enter the LMP.
- Non-pocket ST_GAS energy loss (Harding Street etc.) vs keeper.

## 4. Kills (GATESPEC §5; any ⇒ record and stop, no re-tune)

1. An infeasible window. An engine defect, not a tuning invitation.
2. The schedule hash differs across two runs of one recipe.
3. A control flip: PASS→FAIL on any registered year vs the **keeper** on C1 (classes other than ST_GAS), C3a,
   C3b or C4. ST_GAS C1 vs keeper is reported only: arm V is a rule-19 replacement, which is the UC-3 Addendum-0
   convention.
4. V-1 breached in any year.

**No sweeps.** N_k, the group sets, the window and mlf are fixed here. `uc_*` stays at defaults. No band
multiplier is touched (rule 1).

## 5. Verdict → matrix

K is not available: nothing is registered (charter). The verdict is one of:
- **supports replacement**: V-1…V-5 pass and T-1 met;
- **R**: a kill, or V-2/V-3/V-4 fail;
- **I**: V pass, T-1 not met. The structure holds but does not restore energy. Route the min-load question.

The cell is `scuc_load_pocket_commitment` (MISO) plus the new mechanism's row, both cited to the RESULT.

## 6. Cost

- **Build.** One engine PR: the row, the field, the intake, tests (1 gen / 1 pocket / 24 h first). Opus/Fable.
- **Solve.** 7 shards × ~2–2.5 h.
