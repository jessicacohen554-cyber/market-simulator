# FINDING miso-188 — the retiree-channel vintage-status scope: the dark within-window retiree phantom found by the C1 phase-0 audit, dropped on EIA's own contemporaneous status, and PROMOTED on the PREREG's own rule

**Session miso-188 (2026-08-30).** Charter: the miso-188 handoff — ask A
(zero-solve validation), ask B (the C1 CC_REGULAR-2024 marginal FAIL, phase-0
first, measured-input currency), ask C (the C3a-2025 queue check). PREREG:
`PREREG-miso188-retiree-vintage-status-scope-2026-08-30.md`, committed, pushed
and blob-verified (1c00633) BEFORE the mechanism was implemented and before
any adjudicating quantity existed. Record: `_miso188_ab_gates.json`. Runs:
`2026-08-30-miso-188-control` / `2026-08-30-miso-188-rvsscope` (**KEEPER**).

## 1. Ask A — zero-solve validation

`calibration_verdict.py --run-id 2026-08-26-miso-187-nucavail` reproduces the
registered determination exactly from committed artifacts: NOT-YET on
{C3a-2025 −12.3185 %, C1 fuelmix CC_REGULAR-2024 +8.037 TWh vs ±8.00}; C3a
+2.40 / −4.64 % in-band in 2023/2024; C3c the single ledgered caveat; C6
attested; C8 PASS all years (2025 ST_GAS grounded-above-budget note carried).

## 2. Phase-0 — the C1 CC_REGULAR-2024 anatomy (zero-solve)

* **Year shape:** CC_REGULAR error (model − classFull) +1.71 (2023) /
  +8.997 raw, +8.037 scored (2024) / −1.50 (2025, preliminary vintage,
  unscoreable). 2024 is the anomaly by ~+7 TWh against both neighbours.
* **Month shape** (vs CAMPD gross): a SHOULDER object — Feb +0.60, Mar
  +0.91, Apr +1.46, May +1.16, Jun +0.43, Oct +0.58, Nov +0.39 TWh;
  Jul–Sep near-exact. Year-over-year error growth concentrates Jan–Apr.
* **Family grain:** total gas-family error ≈ 0.0 (2023) / +5.6 (2024) /
  −0.1 (2025).
* **Import exonerated:** model external import tracks measured EIA-930 TI
  at annual grain (40.6 vs 37.9 / 24.4 vs 23.0 / 18.7 vs 19.0 TWh).
* **Availability input verified sound at the LP grain:** Union Power
  (55380)'s Feb-2024 whole-plant outage applies exactly (monthly factor
  0.062); fleet CC actual/available reaches 92–93 % under Jul–Aug 2024
  stress. *(Instrument defect, disclosed: the first availability probe
  mis-keyed `weather_year` and applied 2023 overlays to a 2024 frame —
  caught by the Union factor cross-check, fixed with the `_miso156`
  `dataclasses.replace(cfg, weather_year=year)` pattern before any
  conclusion rested on it.)*
* **Utilization:** the model dispatches CC at 87–94 % of its availability
  in 2024 (saturated) vs 74–90 % in 2023; in the excess months model coal
  runs at 69–77 % of its availability while the real fleet ran 77–93 % of
  the same availability. The ~4–5 TWh displacement core is the
  adjudicated-exhausted offer/flat-stack family (miso-179 `R` /
  miso-180 `I`) — consistent with FINDING-miso187 §7(5), NOT re-opened.

## 3. The identification (the lever)

The within-window retiree channel (`load_retired_within_window`) injects
whole-plant exits and lets the COD ramp dispatch each **to its formal
EIA-860 retirement month**. Several MISO plants were deactivated years
before their paper date, and EIA's own contemporaneous vintage record says
so:

| plant | MW | formal ret | latest vintage status | CAMPD 2022/23/24 (GWh) |
|---|---|---|---|---|
| **862 Grand Tower** (CC_REGULAR) | 511 | 2024-04 | OS | 0.0 / 0.0 / 0.0 |
| 202 Carl Bailey (ST_GAS) | 122 | 2024-10 | OS | 0.0 / 0.0 / 0.0 |
| 2050 Baxter Wilson (ST_GAS) | 494 | 2023-03 | SB | 0.0 / 0.0 / — |
| 10075 Taconite Harbor | 155 | 2023-03 | SB | 0.0 / 0.0 / — |
| control: 6155 Rush Island | 1,178 | 2024-10 | **OP** | 892 / **892 / 612 (ran)** |
| accepted miss: 1047 Lansing | 241 | 2023-06 | OP | 0.0 / 0.0 / — |

Measured under the keeper's own construction, Grand Tower is carried
in-merit for **3.548 TWh (2023) and 1.229 TWh (Jan–Apr 2024)** — the 2024
window landing exactly on the C1 excess months. The oracle (frozen in the
PREREG before the code existed): a retiree-channel unit is dropped for
backcast solve year Y iff its status in the **latest committed vintage ≤ Y
whose operable sheet lists it** is non-OP (OA/OS/SB); unlisted units fail
OPEN. It is the symmetric third leg of the status-basis family already in
this keeper (`carry_operating_mothballs` adds what the snapshot's OP filter
wrongly drops; `unit_outage_fleet_status_scope` drops event rows of
unmodeled units; this drops units the paper date wrongly carries). Zero
fitted scalars; rule-13 forward-regenerable; the Lansing miss is DISCLOSED
and deliberately unrepaired (the oracle is status-only — same-year CEMS
darkness as a *membership* input is refused).

Applied: 28 units / 1,434 MW dropped in every solve year; Rush Island and
Lansing kept. New gated `ScenarioConfig.retiree_vintage_status_scope`
(default off, byte-inert, default cache key unmoved at 603c2498bf71d21d,
backcast-only measured-overlay guard); matrix row + a cell in every shard
minted in the mechanism commit (rule 28c); unit tests
`tests/unit/data/test_retiree_vintage_status_scope.py`.

## 4. The A/B (PREREG-miso188 §4; record `_miso188_ab_gates.json`)

Both legs `replay_keeper` re-solves of `miso187_nuc_B` at one HEAD
(48c95b4), years 2023 2024 2025 in one invocation each, legs sequential:

* **S-0 PASS** — control value-identical to the committed keeper on every
  scored sidecar (max|diff| = 0.0 × 12), despite disclosed toolchain drift
  (numpy 2.5.2→2.4.6, scipy 1.18.1→1.17.1, pydantic 2.13.4→2.13.5,
  platform v21→v22).
* **S-1 PASS** — single config delta; every frozen witness exact: Grand
  Tower dispatch > 0 in the control in 2023 AND 2024 and exactly 0 in the
  arm in both; Carl Bailey / Baxter Wilson / Taconite Harbor arm dispatch
  exactly 0 every year; Rush Island nonzero in BOTH legs 2023+2024;
  Lansing nonzero in BOTH legs 2023.
* **S-2 PASS** — arm 2024 CC_REGULAR class energy falls **1.2114 TWh**
  (152.4707 → 151.2593; gate ≥ 0.10) — near the full 1.229 TWh phantom,
  i.e. minimal substitution. 2023 falls 2.7087 (143.5223 → 140.8136);
  2025 moves −0.0339 (136.4585 → 136.4246; see §6.3).
* **Charter kill SILENT**; **S-4 PASS** (zero D-4 conduct failures, zero
  new; C8 PASS all years).
* **S-5 at full magnitude:** **C1 fuelmix CC_REGULAR-2024 +8.037 TWh FAIL
  → +6.820 TWh PASS** — the single criterion-status flip, in the PREREG's
  predicted direction and inside its declared [−1.23, −0.30] range at
  −1.217. C3a-2024 −4.6440 → −4.3034 % (toward zero); C3a-2023 +2.4049 →
  +3.5008 % (the declared adverse face, in-band); C3a-2025 −12.3185 →
  −12.2965 % (no 2025 claim). ZERO PASS→FAIL flips; no band exits; the
  escalation condition did not fire.

**PROMOTED ON THE PREREG'S OWN RULE** (§4: S-0/S-1/S-2/S-4 clean + charter
kill silent + zero PASS→FAIL flips ⇒ promote — no owner escalation was
needed; the miso-187 §4 precedent of never self-adjudicating a structural
split does not arise because no gate split). Determination of the new
keeper: **NOT-YET on {C3a-2025} ALONE** (was {C3a-2025, C1
CC_REGULAR-2024}); C1 16/16 all classes, 12/12 free (was 15/16 · 11/12);
C3c the single ledgered caveat; C6 attested (ledger 36 entries /
n_residual 2, the new entry MEASURED: published EIA-860 vintage status);
LOYO structurally satisfied (zero fitted parameters, year-independent
identification). Keeper re-keyed in `keepers/MISO.json`, `status/MISO.js`
rebuilt, `calibration-keeper-auditor --iso MISO` PASS (0 failures), matrix
§5.4 header + queue stamp + MISO shard cell U→K + re-stamp block,
calibration-log entry appended. MISO holds no `complete`/`final` marker, so
no rule-22 D-5(b) re-key is owed.

## 5. Ask C — the C3a-2025 queue check (nothing executed, by adjudication)

§5.4's queue after miso-187 carries no named, un-adjudicated mechanism for
C3a-2025: the direction object (N→S 7/47, +0.385 GW vs measured 32/47 S→N /
−2.441 GW out) is the adjudicated ~3.3 GW mc-idled/flat-stack MODEL-CLASS
residual (offer family exhausted at both grains), folded into the standing
owner D-4 posture question with the ~1.3 GW scarce-export concession. This
session respected every standing adjudication (DO-NOT-REDO in full) and its
lever provably does not touch 2025 (every dropped unit is ramp-zeroed
pre-2025; C3a-2025 moves 0.022 pp). The C3a-2025 object remains in owner
court.

## 6. Reported against interest

1. **C3a-2023 worsens** +2.4049 → +3.5008 % — the declared adverse face of
   removing 2.71 TWh of 2023 phantom supply; reported at full magnitude,
   in-band.
2. **The accepted miss stands:** Lansing (1047, 241 MW coal) is OP in its
   latest vintage but measured dark in 2023 — ~0.80 TWh of in-merit
   phantom remains, deliberately unrepaired (no CEMS-as-membership).
3. **2025 is not bit-identical:** CC_REGULAR-2025 moves −0.0339 TWh and
   C3a-2025 by +0.022 pp although every dropped unit is already
   ramp-zeroed in 2025 — a small cross-year interaction through pooled
   constructions (reserve/floor pool membership changes with fleet
   membership), disclosed; no 2025 criterion status moves.
4. **The phase-0 instrument defect** (weather_year mis-key) — caught and
   fixed before any conclusion rested on it (§2).
5. **Registration prunes** under top-15 retention removed
   `2026-08-20-miso-172-control` and `2026-08-20-miso-172-p25mw`
   (tool-decided; committed with the registrations).
6. **The partial-plant mid-window exit gap is NAMED, SIZED and NOT BUILT:**
   units retired 2023–2025 whose plants survive are in neither the
   operable snapshot nor the whole-plant retiree channel (the builder
   drops them deliberately — the plant-keyed COD map would hold the whole
   plant online). MISO: Sherco-2 (682 MW), Petersburg-ST2 (422), A B Brown
   1+2 (485), Dan E Karn ×4 (486), South Oak Creek 5+6 (496), Teche-3
   (250), Dallman-3 (159); plus OS-in-snapshot Big Cajun 2-1 (517).
   Measured actual generation of the missing set: **5.93 TWh (2023) /
   0.57 TWh (2024, mostly January)** — real, mostly a 2023 coal-side
   under-carry, and NOT this session's C1-2024 lever. The repair needs
   unit-grain exit timing in the COD mechanism — its own charter.
7. **Winter coal ceiling observation** (actual coal generation above the
   probe's availability ceiling in Jan/Dec) is contaminated by the
   CAMPD-gross vs net-summer-pmax basis and is NOT adjudicated here.

## 7. Standing OWNER items (restated, not decided)

(1) the C8 provenance-materiality floor; (2) committed-vs-regenerated
diagnostics exposure; (3) `RHO_CLIP` cross-ISO band; (4) **D-4 posture — the
C3a-2025 direction object** (~3.3 GW mc-idled block; ~1.3 GW scarce-export
model-class concession) — unchanged by this session; (5) ~~the C1 fuelmix
CC_REGULAR-2024 band exceedance~~ **CLOSED by this keeper** (+6.820 PASS);
(6) the MISO-Illinois $8.22/MMBtu scarce delivered-gas observation; NEW (7)
the partial-plant mid-window exit charter (§6.6).

## 8. Governance

Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; MISO holds neither marker; the
spend freeze untouched; no new data fetch. Rules 15/16: BOTH legs
registered, full span, one invocation each. Rule 12: years sequential
within each leg; legs sequential; 8 GB swapfile + MARKET_SIM_HIGHS_THREADS=4.
Rules 5/13/14/19/23/24: the field is registered (4-site discipline, same
commit); measured-identified, zero fitted scalars; no deriver re-tuned; the
oracle reads the same vintage record `carry_operating_mothballs` reads.
Rule 25: only MISO's shard cells/keeper/gates were adjudicated (the new
mechanism's base row + `U` cells in every shard are the rule-28(c)
deliberately non-parallel edit, in the mechanism commit). Rule 27
`[R-PUSH]`: exact on-disk bytes; every pushed blob ≥300 lines verified on
`git push`. Rule 28: header + queue stamp + shard cell + re-stamp block +
calibration-log entry in-session; `check_mechanism_matrix.py` clean. No new
`.github/workflows`. THE OWNER MERGES; no PR opened.

## 9. Reproduction

```
cd <repo root>
python3 scripts/probes/_miso188_ab_gates.py           # gates from committed bundles
python3 scripts/calibration_verdict.py --run-id 2026-08-30-miso-188-rvsscope
python3 -m pytest tests/unit/data/test_retiree_vintage_status_scope.py -q
```

Reads the committed `miso187_nuc_B` sidecars, the `miso188_rvs_A/B`
bundles, `data/raw/eia-860/vintage_{2018..2024}/`,
`data/raw/eia-860/eia860_generator_retired_within_window.parquet`,
`data/raw/campd-unit-level/<ST>_<year>.parquet`. PREREG: 1c006331;
mechanism: 48c95b4.
