# FINDING — caiso-198: the Desert Star (EIA 55077) NV extract re-derive — control BIT-ZERO and baseline byte-identity PROVEN, but the committed recipe's re-derive is NOT strictly additive: the merit-order panel is FLEET-BLIND, so the NV state-list widening re-identifies the layup classifier for 15 CA facilities — **the pre-registered kill criterion fires, NO ARM SOLVES**, and the panel-scope question is escalated to the owner with the strictly-additive candidate measured, sha-pinned and ready

**Pre-registration:** `PRECHECK-caiso198-desertstar-extract-2026-08-16.md`,
committed and pushed at `ddebbfd94` BEFORE any solve of this session ran. Gates
applied as written; no band edited; the §5 kill criterion ("any non-55077 byte ⇒
void — its own investigation, not this arm") fired exactly as pre-registered.
**Keeper UNCHANGED** at `2026-08-16-caiso-197-w2-r5`; **the committed extract
UNCHANGED** at sha256 `5f3e35c5…` (the in-place re-derive was voided and
`data/raw` restored to the committed bytes — nothing landed). **ZERO arm LP.**
Registered run: **`2026-08-16-caiso-198-f0-control`** only (NOT-YET / C6
UNATTESTED — the standard non-keeper control posture; its paired arm never came
into being, so no A/B exists and no single-mechanism statement can be issued).
2023–2025 only; both holdout markers and the spend freeze untouched (the
2018–2026 derive spans are data preparation, spend-only gates unaffected).

## 0. Direction-hazard regime (verbatim from the PRECHECK, binding)

> The expected sign of this repair is **ANTI-C3a-favorable**: it can only ADD
> measured outage removal (a plant that previously carried no overlay gains its
> real windows), which lowers availability and raises price, while C3a 2024/2025
> already FAIL high (+12.1/+15.6 %). C3a movement is inadmissible as evidence for
> or against acceptance in EITHER direction (rules 1, 13, 14).

No arm solved, so no arm C3a exists and none was read. The control's C3a is the
keeper's own, reproduced bit-zero (§2). No price series was consulted anywhere in
the §4 investigation (the RCC panel comparison reads CAMPD operation and
delivered fuel prices — the guard's own inputs — never an LMP).

## 1. Gate tally — the session died at G-DELTA leg (b), before the arm

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-CTRL** | f0 within \|ΔC3a\| ≤ 0.1 pp/yr, \|ΔC3b\| ≤ 0.005/yr of the committed keeper | **BIT-ZERO**: max \|Δ\| = 0.0 over every zone-hour of `hourly/system_*.parquet` (prices included) AND every class-hour of `hourly/class_hourly_*.parquet`, all three years (`_caiso198_ctrl_tolerance.json`). Noise floor exactly 0.0 pp / 0.000, quoted before any treated delta. Seam caps 16055/16452/16148 log-verified; `hydro_ror_split=false` disclosed; warm-start pinned off; environment identical to the keeper's recorded stack (python 3.11.15, highspy 1.14.0, numpy 2.4.6, pandas 3.0.3). The caiso-184/188/196/197 norm holds. | **PASS** |
| **G-DELTA (a)** | baseline: NV-excluded re-derive reproduces the committed bytes exactly | With `ISO_STATES["CAISO"]` temporarily `("CA",)` (scratch `--out`, edit restored immediately), the committed recipe reproduces the extract at sha256 `5f3e35c5…` **byte-identically** and the layup companion at `1475a577…` byte-identically. The NV state addition is the ONLY free variable at this head. | **PASS** |
| **G-DELTA (b)** | re-derive strictly additive, facility-55077 rows only, both files | **FAIL — KILL.** In place (committed recipe, committed CA+NV states): main extract 4,561 → 4,820 rows = +158 facility-55077 rows **plus 188 layup→mechanical and 87 mechanical→layup reclassifications of CA-facility windows** (layup companion 810 → 709). Shas `bee2ef1a…`/`12f6d7a6…`, recorded and then **VOIDED**: `data/raw` restored to the committed bytes. Full accounting: `_caiso198_extract_delta.json`. | **FAIL ⇒ arm void** |
| G-DELTA (c), G-ENGAGE, G-SIXISO, G-DOF (arm), G-C8 (arm) | — | **NEVER MEASURED** — no arm exists to measure them on. Control-side G-DOF: ledger built at **10/7**, byte-consistent with the keeper's composed ledger; control G-C8: `legitimacy_diagnostics.json` shipped and scored (the D-1 ST_GAS 2024/2025 FAIL rows reproduce the keeper's own pre-existing, non-gating rows — caiso-196 §1 precedent). | — |

The pre-registered C1-2023 CC_REGULAR flip watch never armed (no arm solve; the
−4.13 TWh row stands untouched in the keeper).

## 2. The control (registered)

`2026-08-16-caiso-198-f0-control` (bundle `caiso198_f0_control`) — the
caiso-197 keeper recipe replayed per PRECHECK §3, solved BEFORE the repair
touched the tree. Bit-zero identity to the committed keeper as tabled above; DOF
ledger 10/7; hourly sidecars committed as the durable G-CTRL evidence
(caiso-188/196 precedent).

## 3. The kill, in bytes — what the re-derive actually changed and why

**The Desert Star detection content is clean and invariant.** All three
re-derive variants (§4) emit the IDENTICAL 158 facility-55077 windows (units
EDE1/EDE2; capacity source `observed_peak`, the PRECHECK §1 ex-ante note — CAMPD
`EDE1`/`EDE2` vs EIA-860 `ED01`/`ED02`/`ED03` misses both id heuristics, shipped
fallback operating as documented). Detection is not the problem.

**The churn is entirely the merit-order panel.**
`outage_detect.build_merit_order_panel` is **deliberately fleet-blind**: "
self-contained by design", it re-reads the CAMPD unit-level parquets for the
ISO's **state list** and builds the revealed-clearing-cost (RCC) panel from
every non-cogeneration unit it can price — with no fleet membership filter. The
`ISO_STATES` NV comment ("cannot leak non-CAISO NV plants into CAISO") is true
of the fleet-filtered DETECTION path it describes, but the PANEL is a different
consumer of the same state list, and it has no such filter. Measured
composition effect of the NV widening (`_caiso198_extract_delta.json`
`panel_census`):

* Panel grows +61/+66/+64 units in 2023/2024/2025, of which **59/64/63 belong
  to the 13–14 NON-CAISO NV facilities** (the NV Energy fleet: Fort Churchill
  2322, Clark 2330, Harry Allen 2336/56224, Tracy 7082/55687, North Valmy 8224,
  Chuck Lenzie 55841, Silverhawk 55322, Higgins 54854, …). Only Desert Star's 2
  units are CAISO fleet.
* The RCC moves in 87–97 % of hours: **mean +3.45 $/MWh in 2024, +2.41 in
  2025** (2023 mixed, mean −0.46/p50 +0.14). In 2025 the RCC also becomes
  *defined* in **720 more hours** (6,576 → 7,296) — NV units priced hours no CA
  unit could, changing classification denominators.
* Result: **275 CA-facility windows reclassify** (188 layup→mechanical, 87
  mechanical→layup) at 15 facilities — Yuba City 34, King City 30, Glenarm 18,
  Sanger 18, Live Oak 17, … — concentrated in the SOLVE YEARS (2023: 21, 2024:
  107, 2025: 43 of the 188). The movers were not all marginal calls: their
  committed out-of-merit shares run 0.901–1.000 (mean 0.971).

**Attribution, run end-to-end** (probe `_caiso198_extract_delta.py`; detection
states committed CA+NV in all three variants, panel dir scoped):

| variant | panel scope | result vs committed |
|---|---|---|
| in-place | CA+NV (recipe as shipped) | +158×55077 **+ 188/87 churn** (VOIDED) |
| **run X** | **CA only (the committed panel)** | **STRICTLY ADDITIVE: committed bytes + the 158×55077 rows, layup companion BYTE-IDENTICAL** — main sha256 `da33e509…` |
| run Y | CA + facility 55077 only | +158×55077, and Desert Star's own panel entry moves **9** windows mechanical→layup (efficient CC lowers RCC slightly) |

So 100 % of the non-55077 movement is panel composition; the dominant driver is
the non-CAISO NV fleet (net RCC **rise** — North Valmy's coal and the running NV
units price high hours), with Desert Star's own entry a small opposite-signed
term. The committed recipe operated exactly as shipped in every variant — the
baseline proof (§1) pins that; nothing in this session's execution deviated.

## 4. G-COV on the strictly-additive candidate (no-LP; the §6-handoff expectation, measured)

`_caiso198_gcov_remeasure.py --extract <run X>` (record
`_caiso198_gcov_remeasure.json`, sha-pinned to the candidate `da33e509…`;
clearly labeled — the repair has NOT landed):

* **CC_REGULAR: extract population 1.000000 — 100 % of the roster, uncovered
  list EMPTY** (the FINDING-caiso193 §2 arc closes: El Segundo repaired at
  caiso-196, Desert Star covered by this candidate); strict CEMS reading
  0.990880 (residual: Harbor + Agnews, the known `eia923_netzero` 2023–24 blind
  spot). Both readings ≥ 0.95 — **the lane-2 premise can only STRENGTHEN**, and
  the frozen `wefor_residual = 0.0` is invariant by construction (X_c can only
  rise).
* CC_CHP: 0.678375 / 0.635703 — **unchanged, stays excluded fail-closed** (the
  real CEMS-exemption limit; 12 of 21 plants have no CAMPD record).

## 5. The owner escalation package (nothing below executed by this session)

The chartered repair is PAUSED at its own pre-registered gate, one decision
short of landing. The decision is **the merit-order panel's identification
scope**, and it is the owner's because either resolution changes a committed
instrument (rule 23 — derive scripts are frozen; the caiso-192 gates adjudicated
the guard AS BUILT on the CA-scope panel):

1. **Pin the panel's scope (a rule-23 recipe charter).** Scope
   `build_merit_order_panel` to the ISO's own fleet — or equivalently pin its
   state list independently of the detection state list. Evidence FOR: the
   panel's docstring identifies its object as "the revealed marginal cost …
   set by the capacity that was actually running" *of the ISO's own market*,
   and NV Energy's fleet does not clear CAISO's merit order; a state-list
   widening made for DETECTION coverage silently re-identified the layup
   classifier for every CA facility — exactly the instrument instability
   rule 23 exists to prevent; and the strictly-additive candidate (run X) then
   lands the Desert Star repair with zero collateral movement, reproducing the
   committed extract for everything else byte-for-byte. Evidence AGAINST /
   scope caution: the panel was never fleet-pure — the committed CA-only panel
   already contains non-CAISO CA units (LADWP, municipal utilities: whatever
   files CEMS under CA and prices), so a FLEET filter (as opposed to a
   state-list pin) would change the committed extract too and needs its own
   baseline measurement; and the same fleet-blindness exists at NYISO (NY+NJ:
   PJM-side NJ units in the panel), PJM/MISO (shared states, ERCOT-side TX in
   MISO's list) — a cross-ISO recipe question, rule 25: each ISO's lane
   measures its own, this FINDING adjudicates none of them.
2. **Accept the shipped fleet-blind panel as the honest recipe output.** The
   in-place re-derive (sha `bee2ef1a…`, fully reproducible) is then the
   repaired extract: the 158 Desert Star rows PLUS the 275-window
   reclassification. That path needs a FRESH pre-registration (the caiso-198
   PRECHECK's G-DELTA cannot admit it) whose gates pre-register the churn
   explicitly, and the C1-2023 CC_REGULAR flip watch (−4.13 TWh vs the ~4.4
   band) is live in BOTH directions: net +101 windows retained as mechanical is
   net-more removal (anti-C3a-favorable), concentrated 2024/2025.
3. **Either way, the Desert Star content itself is settled**: 158 windows,
   invariant to the panel question, G-COV → 100 %/0.9909 measured on the
   candidate. The only open question is the panel scope, not the plant.

**Queue posture unchanged:** the in-model queue remains EXHAUSTED; this is the
same chartered rule-22/23 repair, paused at its own gate — no new lane is
opened or implied. The two standing owner objects (the walled hourly PS
water-state intake, caiso-141/ruling 4; the 8,800 MW declared residual,
caiso-191 §4) are untouched, and the frontier/complete-readiness ASSESSMENT
route (owner ruling 5: C3a genuinely fails, NOT-YET is the honest fallback)
remains available if the owner judges the lane done as-is.

## 6. Artifacts

Registered run `2026-08-16-caiso-198-f0-control` (bundle
`results/calibration/caiso198_f0_control`: slim files + hourly sidecars +
`legitimacy_diagnostics.json` + attestation with free_parameters 10/7).
Records: `_caiso198_ctrl_tolerance.json` (bit-zero control),
`_caiso198_extract_delta.json` (the kill + attribution),
`_caiso198_gcov_remeasure.json` (candidate coverage, sha-pinned). Probes:
`scripts/probes/_caiso198_ctrl_tolerance.py`, `_caiso198_ab_gates.py` (written
pre-kill; its G-DELTA/G-ENGAGE halves never ran — no arm),
`_caiso198_extract_delta.py` (the reproducible three-variant investigation),
`_caiso198_gcov_remeasure.py`. PRECHECK @ `ddebbfd94`. The committed extract
pair is byte-UNCHANGED at `5f3e35c5…`/`1475a577…` (restored; verified). Bench
parts byte-unchanged (the extract never feeds the actuals side; the Desert Star
CEMS series entered the bench at the caiso-197 registration). Matrix duty (b):
`campd_outage_windows` CAISO evidence appended — the recorded extract sha does
NOT supersede (nothing landed); the caiso-198 measurement and the candidate sha
are on the record. Calibration-log entry in `docs/calibration-log/caiso.md`.
Environment: full clone; MIC partition materialized in-session (386 rows);
python 3.11.15 / highspy 1.14.0 — the keeper's recorded stack.
