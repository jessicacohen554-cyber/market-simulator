# HANDOFF → nyiso-142 — execute the pre-registered Astoria stack-duplication A/B

**From session nyiso-141, 2026-08-17.** The correction is landed, tested and
verified at the data seam; the A/B is written and unexecuted. This is the
shortest-path brief for finishing it.

---

## 1. WHAT LANDED (do not redo)

* **The identification.** `results/calibration/FINDING-nyiso141-astoria-stack-duplication-2026-08-17.md`.
  Astoria (ORIS 8906) files units 30 and 50 as reheat/superheat pairs that repeat
  the generator's full `grossLoad` on both rows while splitting heat and masses.
  Three independent channels, none a residual. **Closed — do not re-litigate.**
* **The fix.** `campd.CAMPD_STACK_DUPLICATE_UNITS` + the two call sites +
  `_FACILITIES_NEEDING_UNIT_ROWS`. Zero new DOF. Regression tests
  `tests/curation/test_campd.py::TestStackDuplicateCorrection` (6 tests).
* **The pre-registration.** `PREREG-nyiso141-astoria-stack-duplication-2026-08-17.md`,
  written before any solve. **Use it as written** — its predictions are the
  session's ex-ante commitments and re-writing them after seeing the result
  destroys their only value.
* **The probe.** `scripts/probes/_nyiso141_astoria_stack_duplication.py`,
  reproduces all five identification steps in ~2 min.
* Docs + calibration-log entry.

Nothing was registered on the dashboard: no run was produced, so there was
nothing to register.

## 2. THE ONE BLOCKER — read §4.2 of the finding BEFORE touching the artifact

`plant_emission_rates_v2.parquet` still carries Astoria's **defective** rates,
so the arm is not yet expressible. It **must not** be regenerated on the default
path: that path REPLACES rather than merges, and the committed artifact holds
**2018** rows (no longer buildable — rule 22 dropped 2018 from
`regenerate_clean`) plus the **2022 / 2026 holdout-intake** rows, which are
*unrepeatable by construction* (`--holdout-intake` "may only run once").

Two admissible routes:

1. **Surgical update** of the eight `(8906, unit, year)` rows against the target
   values in finding §4.1, with every other row asserted byte-frozen — the same
   discipline `--holdout-intake` already applies.
2. **Owner decision** on a merge-mode regeneration path for this artifact.

Route 1 is the smaller change and needs no new authority. Whichever is chosen,
verify the diff is Astoria-only before committing — that is also the A/B's K4.

The corrected `data/clean/emissions-unit-annual/` is already rebuilt with the
fix (2019–2021, 2023–2025; 2022 correctly skipped as quarantined), so the target
values are directly readable and do not need re-derivation.

## 3. THE A/B

Per the pre-registration. Both runs `--year 2023 2024 2025` in ONE bundle,
sequential within the run (rules 12, 16); register control AND arm in the same
session (rule 15); NYISO matrix shard only (rule 25).

* control `2026-08-17-nyiso-141-control` — keeper recipe replayed at HEAD.
* arm `…-astoria-stackdup` — same recipe, corrected intake.

**Note the unusual shape, already adjudicated in the prereg:** there is no
`ScenarioConfig` field, so `run_config.json` will be byte-identical between the
runs and **K1 as normally written is inapplicable** — it is replaced by a
diff-scope check. And **K5 / K6′ are declawed**: a correction to a measurement
cannot be vetoed by the score computed from that measurement (nyiso-140 is the
precedent — promoted with a worse fit).

Practical: a fresh probe bundle has no `calibration_attestation.json`, so C6
reads UNATTESTED and the run reads NOT-YET however clean the gates are. Write
the attestation before judging a determination.

**Resourcing is why nyiso-141 stopped here:** 4 cores and 15 GB, with
`plant_level_fleet=True`. Budget for 6 sequential year-solves and do not start
the pair without room to finish both — a half-registered pair is worse than
none.

## 4. WHAT THE A/B WILL *NOT* SETTLE — the successor is still open

The correction accounts for ≈35 % of the 2025 ST_GAS under-production and
**none** of 2023 or 2024. Still open, and still the object nyiso-140 §7 named:

* **2025: ≈ −2.4 TWh** of genuine downstate ST_GAS under-production remains.
* **2023: +2.26 TWh** over-production — untouched by this fix.
* **The substitution itself.** 2023→2025, reality replaced a falling hydro year
  with **steam** (ST_GAS +7.30, CC_REGULAR +0.12); the model replaced it with
  **CC** (ST_GAS +1.30, CC +8.97). The model's CC/ST merit-order boundary does
  not move the way the market's did. Note the model also over-drops hydro
  (−7.34 vs actual −3.93), which is a second, possibly related hole.

Candidate objects for that residual, none yet tested: downstate gas basis
(`nyiso_downstate_ct_gas_basis` is default-**off** on the keeper), CC
availability/outages in 2025, and the CC-vs-ST offer-margin anchoring. Check the
NYISO lever queue and matrix shard before picking — and nothing in the DO-NOT-REDO
list of the nyiso-141 prompt has been reopened.

## 5. GOVERNANCE CONSEQUENCE TO CARRY FORWARD

Because the 2025 benchmark falls, **every NYISO run ever scored on 2025 was
scored against an inflated ST_GAS target**, keeper included. Post-correction
numbers are not comparable to the committed 2025 figures across this change; say
so wherever both appear.

Keeper `2026-08-16-nyiso-140-layup-exclusion` is untouched and still designated
(re-verified this session: CALIBRATED-WITH-CAVEATS, C3c the lone ledgered
caveat). NYISO holds `complete` (validation only), is ABSENT from `final`,
frontier CLEARED, holdout spend freeze ACTIVE and untouched.

Next number: **nyiso-142**.
