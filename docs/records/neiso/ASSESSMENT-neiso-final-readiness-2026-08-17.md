# ASSESSMENT — NEISO `final` (locked-test) readiness under rubric v3.3

**Session:** iso-final-readiness (PJM/NYISO/NEISO sweep) · **Date:** 2026-08-17 ·
**HEAD:** `d1932e8` · **Branch:** `claude/iso-final-readiness-assessment-gx3iei`
**Keeper:** `2026-08-17-neiso-99-joint-p1` (bundle `results/calibration/neiso99_joint_B`)
**Markers:** `complete` HELD (2026-07-07, re-keyed 2026-08-17) · `final` **EMPTY** ·
**Freeze:** `holdout-freeze.json` **ACTIVE** at HEAD.
**Locked test: NEVER GRANTED, NEVER SPENT** (owner decision D-23, 2026-08-06).

**THIS DOCUMENT GRANTS NOTHING AND SPENDS NOTHING.** No year — in or out of training — was
solved, scored or registered. No LP was constructed. Every number below is a committed
artifact, an on-disk measured input, or a published actual.

---

## 0. Recommendation

> ## **NOT YET.** On the merits — and for a reason that no amount of preparation can remove.

**Read §1 first.** NEISO's keeper reads CALIBRATED at HEAD, but that status is carried
**entirely by the v3.3 caveat re-reading**, not by a criterion that changed. Under v3.2 the
same run, on the same artifacts, reads CALIBRATED-WITH-CAVEATS. **The amendment produced no new
evidence of model standing and is therefore not declaration evidence.** NEISO is additionally
an *incidental* beneficiary — the v3.3 block records it as *"an unavoidable cross-ISO
consequence"* of an amendment requested for NYISO.

| # | ground | status |
|---|---|---|
| 1 | **2019 cannot exercise the criterion NEISO's frontier is declared on, and never will.** The 2019 market had **0** RT hours over $300; its whole-year RT maximum is **$261.35**, below the $300 threshold. The model's own formation ceiling is ~$258–281. C3c would score **0 vs 0 — a free PASS** whatever the model did (§3.3). | **blocking, and irreparable** |
| 2 | **H1-2026 is unsolvable at HEAD** — `load_demand('NEISO', 2026)` raises. This is the year that *would* discriminate: **126** actual RT tail hours in 4,343 h (§3.1). | **blocking** |
| 3 | **The Pilgrim fleet-vintage gap** — **−2.146 TWh** of missing 2019 nuclear against a 2019 C1 band of **±2.366 TWh**: 91 % of the C1 error budget consumed by a known, repairable input defect before the model's first mistake. Open cross-ISO charter (§3.4). | **blocking** |
| 4 | **Two of three validation rungs untouched, and the one that ran is stale** (§4). | **blocking** |

Plus the **ACTIVE freeze**, owner-level.

**Ground 1 is decisive and is not a preparation problem.** It is a property of the 2019
*market*, not of the model or the repo, so no input repair can touch it. NEISO's single
ledgered caveat is C3c; 2019 is the one year that cannot test it.

**A genuine correction to the record, in NEISO's favour, which still does not change the
answer:** `ASSESSMENT-neiso87-declaration-2026-08-06.md` §3.1 recorded 2019 as **unsolvable**
("no NEISO rows before 2021"). **That blocker is CLOSED at HEAD** — 2019 now resolves as a
dense full 8760, and two of neiso-87's four blocking scoring-input rows have also closed
(§3.2). NEISO is materially better prepared than it was eleven days ago. It is still not ready,
because the reasons that remain are the ones preparation cannot reach.

---

## 1. Determination — confirmed, and it **is** a v3.3 artifact

`python3 scripts/calibration_verdict.py --run-id 2026-08-17-neiso-99-joint-p1`, committed
artifacts only, no solve, run at HEAD this session:

> **CALIBRATED** · scorable years 2023, 2024, 2025

| criterion | tier | verdict |
|---|---|---|
| C1 fuel-mix by class (grid-delivered) | LOAD | **PASS** |
| C2 system volume (gas/coal families) | LOAD | **PASS** |
| C3a mean LMP | LOAD | **PASS** |
| C3b price duration/shape | LOAD | **PASS** |
| **C3c price tail / scarcity (RT hourly)** | SUPP | **CAVEAT [ledgered]** |
| C4 fleet hourly dispatch correlation | SUPP | **PASS** |
| C6 governance gate | PROT | **PASS** |
| C8 forced-energy share (D-2) | PROT | **PASS** |

D-10 free-class C1: all 12/12 · free 8/8. 0 FAILs, **1 ledgered caveat**.
Determination basis, verbatim: *"1 ledgered caveat(s) (measured-input or model-class) —
REPORTED, and NOT determination-downgrading under rubric v3.3: C3c price tail / scarcity
(RT hourly)."*

### **Is CALIBRATED carried by the v3.3 re-reading, or by criteria that actually pass?**

> **By the v3.3 re-reading. Plainly: this status is a relabelling, not a result — and for NEISO
> it is an incidental one.**

1. **The determination basis line carries nothing but the ledgered caveat** (compare PJM's
   *"all criteria pass, governance attested"*).
2. **The marker's preserved prior text** records the same run reading
   **CALIBRATED-WITH-CAVEATS** before the amendment.
3. **The v3.3 amendment block names this run explicitly** as one of the two keepers that
   flipped, and characterises NEISO's flip as *"an unavoidable cross-ISO consequence: the
   scorer is ONE instrument and an ISO-scoped verdict rule would be an off-registry tuning
   channel in spirit."* The amendment was requested for NYISO. **NEISO's determination improved
   as a side effect of another ISO's owner decision.** That is correct scorer design — and it
   is emphatically not evidence about NEISO.

**What did not change.** C3c reads **CAVEAT, never PASS**, at full magnitude:

| year | model RT h > $300 | actual | ratio |
|---|---|---|---|
| 2023 | **0** | 15 | **0.00×** |
| 2025 | **0** | 20 | **0.00×** |

**The model forms zero scarcity hours in every training year.** This is a *formation ceiling*,
not a tuning residual: the LP is never capacity-short and never reserve-short (every reserve
family dual is exactly $0.00 in all 26,280 training hours), so price is always the marginal
cost of the most expensive dispatched unit — dual-fuel oil parity, max λ ≈ $249 / $218 / $281.
No hour in any training year *can* reach $300.

**Implication for `final`:** a determination that improved without a single criterion moving —
in response to a different ISO's amendment — supplies no new evidence for the most irreversible
decision in the policy.

## 2. Rule 22 D-5(b) re-key — verified, no drift, no repair required

`python3 scripts/audit_keepers.py` → **PASS: 0 failure(s), 0 warning(s)**.

| check | NEISO state |
|---|---|
| `complete.NEISO.keeper` | `2026-08-17-neiso-99-joint-p1` — **matches the current designated keeper** |
| `complete.NEISO.determination` | re-verified 2026-08-17 without a solve, under v3.3; not worse (improves); D-5(b) stop correctly did not fire |
| `keeper_at_declaration` | `2026-07-08-neiso-54-steamgas-ct` — preserved |
| `keeper_rekey_history` | present and complete through neiso-93 → 97 → 99 |
| `locked_test` / `locked_test_note` | **NEVER GRANTED, NOT SPENT** (D-23 correction intact; the false `locked_test_scored_on` is renamed-not-deleted so the retraction stays legible) |
| check **M1** | **PASS** |

**No drift found; nothing was edited in NEISO's shard or anywhere else.**

## 3. `final` readiness on the merits

### 3.1 H1-2026 is unsolvable — and it is the year that would have been worth spending

```
NEISO 2026: BLOCKED  ValueError: No EIA-930 data for ISO 'NEISO' in year 2026
```

`eia_demand_profiles.parquet` carries 2021–2025 only. Yet H1-2026 is precisely the
discriminating year for NEISO's open question: **126 actual RT hours > $300 in 4,343 covered
hours**, against a model that has never formed one. A locked test on H1-2026 would be a real
test of the C3c formation ceiling. **It cannot be run.**

### 3.2 2019 IS solvable — neiso-87's hard blocker is CLOSED, and two scoring gaps with it

Data-layer resolvability probe (no LP built, no model output produced):

| year | shape | system peak | annual energy | zero hours |
|---|---|---|---|---|
| **2019** | (5, 8760) | **20,617 MW** | **95.5 TWh** | 0 |
| **2020** | (5, 8760) | 21,524 MW | 92.1 TWh | 0 |
| 2023 | (5, 8760) | 20,347 MW | 96.9 TWh | 0 |

neiso-87 §3.1 recorded `NEISO 2019: BLOCKED — No EIA-930 data` and `NEISO 2020: BLOCKED`.
**Both now resolve**, as dense full-8760 series in family with the training years.

Re-auditing neiso-87 §3.2's four **BLOCKING** rows at HEAD:

| input | neiso-87 (2026-08-06) | **HEAD (2026-08-17)** |
|---|---|---|
| `eia_demand_profiles` / demand | ❌ BLOCKING (2021–2025) | ✅ **CLOSED** — 2019 and 2020 resolve |
| `calibration_reference.json` | ❌ BLOCKING (2021–2025) | ✅ **CLOSED** — NEISO block now carries **2019, 2020**, 2021–2025 |
| `NEISO_<y>_renewable_capacity.csv` | ❌ BLOCKING (2021–2025) | ✅ **CLOSED** — `NEISO_2019_…csv` and `NEISO_2020_…csv` now exist |
| `actual_tail.json` | ❌ BLOCKING (2022–2025) | ⚠️ **by design** — no 2019 row for any ISO; `derive_actual_tail.py` sets `ALLOWED_YEARS = CALIBRATION_YEARS` and emits out-of-training rows only on the tier marker. Materializes on grant; correctly fail-closed, not a gap. (Its `CONSIDERED_HOLDOUT_YEARS` second ladder was deleted at neiso-89.) |

**Three of four closed; the fourth is not a gap.** `actual_lmp_hourly_NEISO.parquet` covers
2018–2026 with 8760 rows/yr. **NEISO's 2019 preparation is in good shape** — which is exactly
why the remaining reasons deserve to be stated on their own merits rather than hidden behind a
data blocker that no longer exists.

### 3.3 2019 cannot exercise the criterion NEISO's frontier is declared on — irreparably

Actuals-only, from the committed `actual_lmp_hourly_NEISO.parquet` hub series. No model output
involved. `TAIL_THRESHOLD["NEISO"] = 300.0`, `TAIL_SMALL_COUNT = 10`.

| year | 2018 | **2019** | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | H1-2026 |
|---|---|---|---|---|---|---|---|---|---|
| RT h > $300 | 32 | **0** | 0 | 2 | 117 | 15 | 8 | 20 | **126** |
| RT mean $/MWh | 43.54 | **30.67** | 23.39 | 44.84 | 84.92 | 35.70 | 39.54 | 65.88 | 78.82 |
| **RT max $/MWh** | 2,455 | **261.35** | 236.11 | 375 | 2,254 | 1,162 | 2,113 | 1,110 | 777 |

Two facts compose into a certainty:

* **The actual 2019 market never once reached $300** — its whole-year maximum is **$261.35**.
  Actual count 0 < `TAIL_SMALL_COUNT`, so any model tail of **0–10 h PASSES**.
* **The model's formation ceiling is ~$258–281** and it produces **0 hours in every year**.

So the 2019 C3c outcome is **known in advance: 0 vs 0, PASS.** It is not a test. Spending the
one-touch year would purchase a guaranteed free PASS on the exact criterion NEISO is caveated
on, and it could never be re-run to do better. This reproduces neiso-87 §3.3 and neiso-90 §3
verbatim, and — unlike every other blocker in this document — **it cannot be prepared away.**

2019 would still exercise C1/C2/C3a/C3b/C4, which is real value. That is an argument for
spending it *after* the C3c lane resolves, not before.

### 3.4 The Pilgrim fleet-vintage gap is a live 2019 disqualifier

From `ASSESSMENT-neiso94-final-readiness-2026-08-15` §2, re-checked as still open at HEAD
(`docs/calibration-log/neiso.md` records the fleet-vintage/Pilgrim charter as **cross-ISO and
unassigned**, explicitly *"NOT a NEISO lane item"*, and neiso-95/98/99 did not close it):

Pilgrim (~670 MW) is absent from every `eia860_generator*.parquet` in the repo and the fleet
builder reads the 2025-operable snapshot, so a 2019 solve is short **−2.146 TWh** of nuclear
concentrated in Jan–May 2019 — against a 2019 C1 fuel-mix band of **±2.366 TWh**. **91 % of the
entire C1 error budget is consumed by a known, already-diagnosed, repairable input defect
before the model makes its first mistake.** Worse, because nuclear is a pinned class C1 never
scores, the shortfall does not surface where it originates: energy balance exports it onto the
C1-scored gas row and the seam imports, where it is **indistinguishable from model error**.

Scope: 264 plants / 21.5 GW across all six ISOs; NEISO 21/914 units, of which **Pilgrim is
670 MW = 73 %**.

### 3.5 The freeze is ACTIVE

`"active": true`, re-armed 2026-08-06 after the narrow neiso-86 lift, scope `isos: ALL`, tiers
`[validation, locked_test]`. Checked before the marker, fails closed. Its basis — the CAMPD
economic-layup residual — is unchanged; the charter's §9 *recommends* closing with cause and
lifting fully, and the owner has deliberately **not** taken that step.

## 4. Touchpoint loop (rule 22) — one rung resolved, and it has gone stale

| rung | run | determination | state |
|---|---|---|---|
| **2022** | `2026-08-06-neiso-2022-corrected-basis` | **CALIBRATED-WITH-CAVEATS** (C3c carried; nothing degraded) | **resolved — but STALE** |
| **2021** | — | — | **never run; refused on data readiness** |
| **2020** | — | — | **never run** |

**2022 — the loop worked exactly as specified, once.** The first spend
(`2026-08-05-neiso-2022-touchpoint`) scored **NOT-YET** with C3a and C3b degraded. Step 2
diagnosed an **object, not a residual**: neiso-85 found NEISO's hub-basis series *seasonally
inverted* (sourced from the EIA N3050MA3 LDC city-gate portfolio average, whose summer $/Mcf
balloons as fixed reservation charges spread over collapsed summer throughput — the model was
burning gas at $6–8/MMBtu in winter and $14–19 in summer, backwards for a pipeline-constrained
New England). neiso-86 replaced it with the measured ISO-NE Massachusetts index. The re-test
came back **CALIBRATED-WITH-CAVEATS with zero degradations**. **Zero free parameters were
introduced and nothing was ever fitted to 2022.** This is the model case for the rule-22 loop.

**But the rung is now stale.** The 2022 touchpoint was measured on the keeper of the day
(descended from `2026-08-06-neiso-87-control`). The keeper has since moved **twice**, both
times on measured-input repairs applied to every year:

* **neiso-97** — the corrected 2018–2023 ISO-NE SMD clock;
* **neiso-99** — the CAMPD unit-outage routing guard (the current keeper).

Neither is a tuning change and both are rule-22-correct (*the score is held out, never the
data*), but the consequence stands: **no registered 2022 result measures the current frozen
recipe.** Under rule 22's own instruction — *when we hit go, the config is already precisely
the frontier keeper, with nothing left to prepare* — the ladder should be re-walked on the
current recipe before the tier above it is spent.

**2021 was formally refused on data readiness** (`ASSESSMENT-neiso92-2021-readiness-2026-08-13`):
four inputs DEGRADED against the 2022–2025 standard, one — **nuclear availability** — severe
enough on its own to reproduce the neiso-85 failure mode. All four are fixable with data prep
alone (every upstream source is on disk), which needs no marker and no lift. **That prep has
not landed.** **2020 has never been assessed.**

**Net:** one of three rungs has been resolved, and it no longer reflects the current keeper.
That is not a walked ladder.

## 5. What would change the answer

1. **Re-walk the validation ladder on the current recipe** — re-spend 2022 on
   `2026-08-17-neiso-99-joint-p1` (owner lift only), then prepare and spend 2021 and 2020.
2. **Close the fleet-vintage/Pilgrim charter** — cross-ISO, currently unassigned; it is a
   2019 disqualifier for NEISO and touches 264 plants / 21.5 GW across all six ISOs.
3. **Land the neiso-92 2021 data prep** (nuclear availability first). Unrestricted; no grant
   needed.
4. **Make H1-2026 solvable** (demand-profile coverage past 2025). This is the highest-value
   item on the list: H1-2026 is the *only* locked-test year that can discriminate on NEISO's
   open criterion, at 126 actual tail hours against a model that forms zero.
5. **Resolve the C3c formation ceiling itself**, or the owner rules it a permanently accepted
   model-class limitation. Until then, spending 2019 buys a guaranteed free PASS on it.
6. The owner **lifts the freeze**.

Items 1–4 need no `final` grant. **If the owner wishes to scope a NEISO locked test, the
defensible shape is H1-2026 once solvable — not 2019**, which cannot discriminate on the one
thing NEISO is caveated on and can never be re-run to try again.

---

*Precedent and direct predecessors: `ASSESSMENT-neiso87-declaration-2026-08-06.md` (the
NOT-YET-on-the-merits template; its §3.1 hard blocker is CLOSED at HEAD — see §3.2 above),
`ASSESSMENT-neiso90-final-reassessment-2026-08-07.md`,
`ASSESSMENT-neiso92-2021-readiness-2026-08-13.md`,
`ASSESSMENT-neiso94-final-readiness-2026-08-15.md`.
This assessment re-confirms NOT YET under rubric v3.3, adds the v3.3 determination analysis
(§1), and updates the 2019 preparedness record (§3.2).*
