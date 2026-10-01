# NYISO-PROMOTE — keeper → `2026-08-07-nyiso-131-taxgs-arm` (owner decision D-27)

**Session nyiso-131, 2026-08-07, branch `claude/nyiso-promote-taxgs-arm-0qdupw`.**
GOVERNANCE lane, **committed artifacts only — no solve, no scoring run over the LP, no year
touched, no mechanism tested.** Owner decision **D-27**, SIGNED at the 2026-08-06 sitting
**Addendum AA.4** (2026-08-07), verbatim: *"D-27 — SIGNED AS RECOMMENDED: NYISO promotes now,
MISO defers."*

---

## 1. Step 0 verification (pre-conditions, checked before any edit)

| check | result |
|---|---|
| NYISO keeper at head still `2026-08-06-nyiso-128-solar-basis` | **YES** — promotion adjudicated against the right incumbent, no re-adjudication needed |
| arm bundle `results/calibration/nyiso131_taxgs_arm` exists | **YES** |
| registry sidecar `frontend/data/backcast/registry/2026-08-07-nyiso-131-taxgs-arm.json` exists | **YES** (years 2023, 2024, 2025) |
| run payload `frontend/data/backcast/runs/2026-08-07-nyiso-131-taxgs-arm.js` exists | **YES** (612,089 bytes, already committed) |
| working tree clean at session start | **YES** |

Because the arm and its payload were already registered by the taxonomy session, **this
promotion adds no run payload** — the largest file it touches is a JSON shard, so the
`git push` pack stays small.

## 2. The promoted run is the incumbent's OWN recipe

`2026-08-07-nyiso-131-taxgs-arm` is a same-head `replay_keeper` of the keeper's own bundle
(`nyiso128_treatment`) with owner decision **D-25** (the `gas_st` fuel taxonomy) applied.
**Verified rather than asserted**, by diffing the two `run_config.json` files:

* **693 shared `scenario_config` fields — ZERO differing.**
* 5 arm-only fields, all `ScenarioConfig` entries that landed on `main` after the keeper solved,
  **all five at default `False`**:
  `ercot_dam_availability_event_cap_reconciliation`,
  `ercot_dam_availability_event_cap_unit_scoped`,
  `miso_clean_tier_rows`,
  `miso_rps_compliance_regions`,
  **`nyiso_li_tsl_n11_security`**.
* The last of those matters specifically: it is the nyiso-130 lever **rejected on its own
  pre-registered kill gate K6** and adjudicated `R` in the matrix. It is confirmed **NOT armed**
  here, so the promotion does not smuggle a refuted mechanism in behind a taxonomy fix.

So the entire nyiso-128 lineage stays armed and unchanged: nyiso-100 SIL retirement → 109 zonal
gas-offer anchor → 117 NYC RCPF → 118 ORDC measured step span → 119 SENY increment → 120 East
River scope gate → 125 seam envelope → 128 solar basis.

**What D-25 changes.** Natural-gas steam turbines (EIA-860 prime mover `ST`, energy source `NG`)
map to the dedicated `gas_st` fuel — the fuel the CAMPD bin path always carried via
`BIN_GROUP_TO_FUEL` — instead of folding into `gas_ct`. Rule 14 `[R-ACCURATE]`: the class
structure was already right (`classify_plant` has had `ST_GAS`/`ST_CHP` all along); only the
**fuel label on the loader record** was wrong, where it set the heat-rate fallback, VOM, EFORd,
CO2/NOx and the **scoring-target fuel**. NYISO's entire solve-affecting residue is **one
synthesized-bin heat rate**: RED-Rochester ST_CHP, **11.454 → 10.3 MMBtu/MWh on 119.6 MW**.
Zero free parameters; zero `ScenarioConfig` fields.

## 3. The re-verified determination (rule 22 D-5(b))

NYISO holds `complete`, so the marker's `keeper` re-keys **and** its `determination` is
re-verified against the new run before the promotion commit lands. Command — committed artifacts
only, **never a solve**:

```
python3 scripts/calibration_verdict.py --run-id 2026-08-07-nyiso-131-taxgs-arm
```

| criterion | incumbent `nyiso-128-solar-basis` | promoted `nyiso-131-taxgs-arm` |
|---|---|---|
| **determination** | CALIBRATED-WITH-CAVEATS | **CALIBRATED-WITH-CAVEATS** |
| C1 fuel-mix by class | PASS | **PASS** |
| C2 system volume | PASS | **PASS** |
| C3a mean LMP | PASS | **PASS** |
| C3b price duration/shape | PASS | **PASS** |
| C3c price tail / scarcity | CAVEAT (ledgered) | **CAVEAT (ledgered)** |
| C4 fleet hourly dispatch corr | PASS | **PASS** |
| C6 governance gate | PASS | **PASS** |
| C8 forced-energy share (D-2) | PASS | **PASS** |
| ledgered caveats | 1 of 1 | **1 of 1** |
| D-10 free-class C1 | 14/14 all, 10/10 free | **14/14 all, 10/10 free** |

**The label is identical, so D-5(b)'s worse-determination stop DOES NOT FIRE and no escalation
is owed.** The re-verification is criterion-for-criterion, not label-only. The **only** difference
visible across the two scorer runs is an **ungated SKIPPED diagnostic line**: C3a-2023 DA
diagnostic `+6.7 %` → `+6.6 %`.

The C3c ledger carries forward unchanged in substance — 2023 model 22 h vs RT actual 10 h
(2.20×, **over**-produced, in-training, under the nyiso-130 owner directive) and 2024 model 3 h
vs 12 h (0.25×, under-produced). **No new caveat slot is spent**: an input correction with zero
free parameters creates no caveat.

## 4. Deltas, at full size

Verdict grain: nothing moves. Hourly grain: not byte-identical (source:
`docs/handoffs/taxonomy-gas-st-2026-08-07.md` §4.1).

| year | class energy deltas (TWh, arm − control) | demand-wt ΔLMP | max zonal \|ΔLMP\| |
|---|---|--:|--:|
| 2023 | ST_CHP +0.037; ST_GAS −0.016; CC_REGULAR −0.011; CC_CHP −0.007 | −0.013 $/MWh | 1.25 |
| 2024 | ST_CHP +0.052; CC_REGULAR −0.023; CC_CHP −0.016; ST_GAS −0.012 | −0.023 $/MWh | 3.85 |
| 2025 | ST_CHP +0.005; CC_REGULAR −0.002; CC_CHP −0.001; ST_GAS −0.001 | −0.002 $/MWh | 2.71 |

34 of 188 numeric verdict fields move; **no gate is approached, let alone crossed**. Direction is
physical and follows from the sign of the correction: the corrected (cheaper, EIA Table 8.2) heat
rate lets the cogen bin run more, displacing merchant CC and the ST_GAS class.

## 5. Gates run

| gate | result |
|---|---|
| `scripts/audit_keepers.py --iso NYISO` (**M1**) | **PASS — 0 failures, 0 warnings** (NYISO keeper, holdout, marker, status all clean) |
| `scripts/check_mechanism_matrix.py` | **clean on all four checks**: integrity OK; 189 field + 44 row + 128 path anchors, 0 unresolvable beyond the ratchet; keeper stamps match every shard; §5.x prose headers match every shard |
| `calibration_verdict.py --run-id` (both runs) | determinations identical — §3 |
| `build_status.py --iso NYISO` | rebuilt, reads `CALIBRATED-WITH-CAVEATS`; `status/shared.js` byte-unchanged (rubric didn't move) |

The matrix guard initially flagged **`NYISO §5.x prose header drift`** (the header still named the
old keeper); the §5.5 prose header was re-stamped in the same session and the guard now passes.

## 6. Matrix re-stamp (rule 28)

* `keepers.NYISO` → `2026-08-07-nyiso-131-taxgs-arm`.
* Header comment block: new NYISO stamp paragraph recording the promotion, the 693/693 config
  verification, why D-25 books **no matrix row** under rule 28(c) (it adds **no `ScenarioConfig`
  field** — an unflagged loader-taxonomy correction), the unchanged open gates and the unchanged
  lever queue.
* `gates.NYISO`: appended clause **(8, nyiso-131, 2026-08-07)** — the board's running log had
  ended at nyiso-124, so the current state is now stated explicitly: open-gate set **unchanged**,
  C3c still the sole non-passing criterion at budget 1 of 1.
* `docs/mechanism-testing-matrix.md` §5.5 prose header re-stamped with the same content.

**NO cell verdict moved and no row was added** — no mechanism was tested this session.
`vre_market_generator_basis` NYISO stays `K`; `nyiso_li_tsl_n11_security` NYISO stays `R`.

## 7. What this promotion does NOT do

* **Does not close, narrow or re-open C3c.** Tail counts are the incumbent's; the diagnosed owner
  is unchanged (100 % of the modelled tail in all three years is Long Island inside HB14-21 with
  both Zone-K import paths at their bound). The successor stays the **chartered joint
  reconciliation** of the Zone-K transfer bound and the downstate ST_GAS `min_gen` floor under
  rule 19 `[R-ONE-MECH]`. The bare 940 MW number swap is adjudicated `R` — **do not re-test it**.
* **Does not restore frontier status.** NYISO's frontier was CLEARED 2026-08-06; it stays cleared.
* **Does not touch the holdout posture.** `complete` (validation only) untouched, NYISO stays
  **absent from `final`**, ACTIVE holdout spend freeze unaffected. 2023–2025 only.
* **Does not change the lever queue:** (1) the joint Long Island transfer-bound / `min_gen`
  reconciliation; (2) the NYISO solar **CF level** (`RENEWABLE_AVG_CF` 0.15 Tier-3, realized
  ~0.133, vs a measured 0.1955 on the registered fleet).
* **Does not touch MISO or any other ISO.** D-27 defers MISO explicitly: its paired `taxgs` arm
  stays registered-not-promoted until the MISO lane settles the Addendum AA.2 rubric-v3.1 C3a
  re-score question, because promoting into a disputed determination would entangle two changes.
  No MISO file — shard, marker entry, matrix cell or log — was edited. The NEISO 9.3 MW tail
  rides whichever NEISO session solves next.

## 8. Files changed

| file | change |
|---|---|
| `frontend/data/backcast/keepers/NYISO.json` | keeper → new id; promotion note (prior note retained verbatim); `superseded` block added with the prior one nested under `prior` |
| `frontend/data/backcast/status/NYISO.js` | rebuilt via `build_status.py --iso NYISO` |
| `frontend/data/backcast/calibration-complete.json` | D-5(b) re-key: `complete.NYISO.keeper`, re-verified `determination`, `keeper_at_prior_rekey`, third `rekey_history` entry. `keeper_at_declaration`, `tier_authorized`, `locked_test`, `freeze_interaction`, `frontier_status` untouched |
| `docs/codebase-site/data/mechanism-matrix.js` | keeper stamp + header paragraph + `gates.NYISO` clause |
| `docs/mechanism-testing-matrix.md` | §5.5 prose header re-stamp |
| `docs/calibration-log/nyiso.md` | dated nyiso-131 entry citing D-27 |
| `docs/handoffs/nyiso-taxgs-promotion-2026-08-07.md` | this note |

**Session numbering:** `nyiso-131` is consumed by this promotion (the run id already carries it).
Next number: **nyiso-132**.
