# ASSESSMENT — CAISO frontier and `complete`-declaration readiness, RE-CHECKED (caiso-173)

**Date:** 2026-08-05 · **Session:** caiso-173 · **Keeper under assessment:**
`2026-08-04-caiso-172-measured-path15` (bundle `results/calibration/caiso172_measured_path15_split`)

**NO LP, NO SOLVE, NO DERIVE, NO INTAKE, no `ScenarioConfig` field, no run registered,
keeper unchanged.** Two network calls, both standing wall probes that are network by
design. Nothing in `calibration-complete.json` or `holdout-freeze.json` is touched — the
marker is an owner act (rule 22). No out-of-training year was solved, scored or read.

Instrument: `scripts/probes/caiso173_frontier_recheck.py` (committed artifacts only,
re-runs in seconds); record `results/calibration/_caiso173_frontier_recheck.json`.

---

## 0. Recommendation, up front

**NOT YET — and the reason is not CAISO's calibration.** `ASSESSMENT-caiso171` recommended
**YES**; caiso-172 then strengthened the case by closing its one outstanding item through
measurement. On the ledger those two sessions weighed, the answer would still be YES, and
§§2–5 below say so criterion by criterion.

**But the ledger changed underneath them.** FFR-4D merged as **PR #3562** while caiso-172
was in flight, carrying cache epoch **2026-08-04c**. That epoch is a **same-key
invalidation of every cached CAISO bundle**, and the designated keeper predates it. This
is **GATE 0 outcome (ii)**, and under it a YES is not available:

> **The designated CAISO keeper is PRE-EPOCH. Its committed metrics were produced on a
> flat 8,000 MW battery fleet — a *forecast* base-year constant fed to a backcast year.
> They therefore do not describe the model that exists today, and a `complete`
> determination written against them would be stale on the day it was written.**

This is measured, not inferred (§1): the keeper's own recorded `git_sha` is `789e28b8`,
which is an ancestor of FFR-4D's head; that tree contains **zero** occurrences of
`storage_measured_base_fleet` against **four** on current `main`; and the keeper's
`run_config.json` carries **no such field at all**. A run solved on a tree without the
field cannot have honoured it.

Rule 22 D-5(b) is the rule this collides with, and it collides squarely. That rule exists
so a `complete` entry's `determination` always tracks the ISO's *current* keeper, and it
requires re-verification against that keeper before a promotion commit lands. Declaring
`complete` now would write a determination that the already-owed re-solve is expected to
move — precisely the stale determination D-5(b) was signed to prevent.

**What is owed is exactly one thing, and it is a different session's work** (FFR-4D §7
D-2 states it as owed): a CAISO backcast re-solve of **2023/2024/2025 in one bundle**
(rule 16), registered per rule 15, re-gated, and the matrix cell
`storage_measured_base_fleet` moved from `O` to its adjudicated verdict. **This session
did not attempt it and must not** — it is a three-year LP run plus a full re-gate.

**Everything else is ready, and this assessment is the evidence that it is.** All six
adjudications the charter set are resolved below; all three standing walls re-verified on
live bytes; the column census is clean; the DOF ledger improved. If the re-solve returns
CALIBRATED-WITH-CAVEATS with no new FAIL, **the recommendation becomes YES with no further
frontier work required**, and §6 states that as a pre-registered condition so the next
session does not have to re-litigate it.

**The freeze is not the reason and must not be cited as one.** caiso-171's corrected §0
settled this on the record — the freeze was declared 2026-07-25 and NYISO and PJM were
both declared `complete` on 2026-07-31, six days into it; the marker and the freeze are
orthogonal instruments. That reasoning is cited, not re-derived. The blocker here is the
epoch, and only the epoch.

---

## 1. GATE 0 — the FFR-4D epoch, measured

Checked at session start **and** immediately before this recommendation was written, as
the charter requires.

| check | result |
|---|---|
| `git merge-base --is-ancestor 58c22e32 origin/main` | **TRUE** — FFR-4D is merged (PR #3562, merge commit `4942dace`) |
| `origin/main` at re-check | `783833bb` (advanced during the session; nothing CAISO landed — FFR-4C/MISO and a workstream sitting) |
| keeper `run_config.json` → `git_sha` | `789e28b8` — *"caiso-172 Phase 0: CAISO DOES resolve sub-TAC load"* |
| `789e28b8` is an ancestor of FFR-4D head | **TRUE** — the keeper solved before the epoch |
| `storage_measured_base_fleet` in `scenarios.py` **at `789e28b8`** | **0 occurrences** |
| `storage_measured_base_fleet` in `scenarios.py` **at `main`** | **4 occurrences** |
| `storage_measured_base_fleet` in the keeper's `run_config.json` | **ABSENT** |
| **verdict** | **KEEPER IS PRE-EPOCH** |

The `run_config` signal is the authoritative one because it needs no git history to
interpret: the field is registered in `_CACHE_KEY_OPTIONAL_FIELDS` and would be recorded
if it had existed.

**What the keeper's battery fleet actually was, against what operated** (FFR-4D §5,
EIA-860 2025 Early Release):

| year | measured year-end battery MW | keeper ran on | delta | direction |
|---|---:|---:|---:|---|
| 2023 | 7,492.4 | 8,000.0 flat | **−507.6** | keeper ran **6.8 % OVER** |
| 2024 | 11,131.3 | 8,000.0 flat | **+3,131.3** | keeper ran **28.1 % short** |
| 2025 | 15,448.4 | 8,000.0 flat | **+7,448.4** | keeper ran **48.2 % short** |

**A precision the headline loses:** the defect is *not* uniformly "short". It reverses
sign in 2023, where the flat scalar **over-fleeted** the model. Any successor reasoning
about direction of effect must carry that, and a re-solve is the only thing that settles
it — which is exactly why this cannot be adjudicated on paper.

**FFR-4D §5's hypothesis is carried as an OPEN LEAD, weighed as evidence for neither
side.** FFR-4D writes, in its own words *"HYPOTHESIS, EXPLICITLY NOT CLAIMED"*, that the
C3a-2025 caveat (mean LMP +14.4 % hot) may be partly this fleet defect — 7.4 GW of missing
evening-peak battery leaving that load to thermal is the right direction and roughly the
right place. It is untested. It is **not** grounds to discount the caveat, and **not**
grounds to expect the re-solve to clear it. It is a reason the re-solve is informative.

---

## 2. The six adjudications

### A. Does §3's "highest ISO-specific residual DOF" finding survive at 3? — **YES, narrowed**

caiso-171 §3's headline was *"CAISO carries the most ISO-specific residual DOF of any ISO
measured"* (4, vs PJM 1 / NYISO 2 / NEISO 0). caiso-172 closed one. Re-measured (probe F2):

| ISO | entries | residual | core | **ISO-specific** | `complete` marker | the ISO-specific entries |
|---|---:|---:|---:|---:|---|---|
| **CAISO** | 11 | **8** | 5 | **3** | **no** | `battery_dispatch_adder`, `WECC_import_simultaneous.cap_mw`, `IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]` |
| PJM | 19 | 6 | 5 | 1 | yes | `wefor_residual` |
| NYISO | 34 | 6 | 4 | 2 | yes | `NYISO_LOCAL_SELFSUPPLY_FRAC['Long_Island']`, `IMPORT_TRANCHES/EXPORT_TRANCHES[NYISO]` |
| NEISO | 13 | 5 | 5 | **0** | yes (locked test SPENT) | — |
| MISO | 28 | 2 | 2 | 0 | no | — |

**The finding survives: CAISO is still the sole highest, now at 3 rather than 4.** The gap
narrowed by one and did not close.

**A correction to how this table is produced, which matters for whether it can be
trusted.** caiso-171's instrument pinned the comparison bundles as literals. Three of its
four comparison ISOs have promoted since — NYISO to `nyiso125_seam_A`, NEISO to
`neiso81_chpheatrate_B`, MISO to `miso127_onlinepmin_B` — so re-running caiso-171's probe
today would describe **stale runs**. The caiso-173 instrument resolves every bundle from
`keepers/<ISO>.json` → the registry sidecar, so the table tracks promotions. The
re-measured entry counts (NYISO 33→34, NEISO 12→13, MISO 27→28) are that correction
landing; the ISO-specific column is unchanged for all four.

**`storage_measured_base_fleet` does NOT increment CAISO's count, and this was checked
rather than assumed.** It is default-ON, carries **zero free parameters**, and selects a
**measured EIA-860 fleet** over a hand-rounded forecast scalar. It is a rule-14
`[R-ACCURATE]` identification, the same object class as caiso-172's own closure — a DOF
*reduction* in kind, not an addition. The keeper's ledger reads `n_entries` 11 /
`n_residual` 8 and the field appears in neither.

**Verdict on A:** the one substantive gap caiso-171 named between CAISO and the
marker-holding ISOs **narrowed but persists**. It was not disqualifying at 4 and is not at
3 — `complete` is not a certificate of a clean DOF ledger (caiso-171 §0's corrected
criterion), and NYISO holds the marker at 2 carrying an unledgered criterion FAIL.

### B. The three standing walls — **ALL THREE HOLD**

| wall | probe / census | result |
|---|---|---|
| **1** — C3a: non-public hourly pumped storage (caiso-141 A2) | `_caiso141_water_source_survey.py`, **live network** | **5/5 `unchanged`.** S1 EIA-930 carries `PS` but **CISO PS rows = 0**; S2 Outlook hydro vs 930 WAT n=72 **corr 0.950**, mean abs diff **287 MW** — the same PS-NET feed; S3 `storage.csv` battery-only; S4 CDEC **CTG 0 / WSN 0 / SHV 0** hourly sensors (Helms + Eastwood, 60.3 % of the fleet, uninstrumented); S5 sub-BA demand-only |
| **2** — Arm B: no published intra-SP15 transfer limit | `data/raw` census | **HOLDS.** The only corridor numbers on disk remain the LCT-derived pocket import capabilities in `data/raw/capacity-deliverability/caiso/caiso.csv`, and those are **already armed per-year** (`caiso_per_year_import_caps = True` on the keeper). The wall is not "no number exists" — it is *the published number is armed at its published value and the corridor does not bind there*, so any tighter limit would have to be invented |
| **3** — C3c: the SoCalGas OFO declaration record | `data/raw` census | **HOLDS.** The only hit is `data/raw/gas-prices/pge_socal_citygate_weekly.csv`, a **price** series. Nothing on disk carries OFO event windows |

**caiso-172's five walls were also re-run live and all five return `unchanged`** — S1
`SLD_FCST` TAC-grain under every `market_run_id`; S2b `ENE_SLRS`'s `TAC_NORTH` proven to
span Path 15; S3 `PRC_LMP` items all $/MWh; S4 FERC-714 still **HTTP 403** (CEC 404); S5
sub-BA demand-only. S2 remains **AVAILABLE** — that is the door caiso-172 walked through,
and re-running it reproduces the measured split **NP15 0.8844 / ZP26 0.1156** against the
retired estimate's 0.86/0.14.

**No intake has landed that would make any wall the lane instead.**

### C. MWD-TAC — **(ii) a recorded open item; it does NOT block**

caiso-172 §1.1 opened this and did not close it. Adjudicated here on measurement rather
than on its ~208 MW / ~0.9 % estimate.

**What it is.** `MWD-TAC` (Metropolitan Water District) is a real CAISO TAC area. The live
`SLD_FCST` domain carries **six** CAISO-internal areas
(`CA ISO-TAC, MWD-TAC, PGE-TAC, SCE-TAC, SDGE-TAC, VEA-TAC`); the committed series
`CAISO_tac_load_hourly_<year>.csv` carries **five**, MWD absent, and
`CAISO_TAC_ZONE_WEIGHTS` has no MWD row. Both re-confirmed this session (probe F6/F7).

**What it is NOT, and this is the finding that decides the adjudication.** It is **not
missing load**. `data/eia930/zonal_shares.py::load_zonal_shares` returns *fractional*
shares **normalised to sum to 1.0 across zones each hour** — the module comment is
explicit that *"the 'CA ISO-TAC' system-total rows are dropped and shares are normalized
over the component TACs."* The ISO's total demand does not come from this series. So MWD's
load is **re-apportioned pro-rata across the four modelled TACs**, not dropped. The defect
is a **misapportionment**, and its magnitude is bounded accordingly:

| year | ISO total | unmodelled residual (MWD) | % of ISO | PG&E's pro-rata slice | → landing north of Path 15 | % of ISO |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 24,083.1 | 125.8 | 0.52 % | 0.462 | **58.1 MW** | **0.241 %** |
| 2024 | 25,598.8 | 171.6 | 0.67 % | 0.444 | **76.0 MW** | **0.297 %** |
| 2025 | 25,664.4 | 144.1 | 0.56 % | 0.434 | **62.3 MW** | **0.243 %** |

caiso-172's "~0.9 % of ISO load" was **high**; measured against the committed series it is
**0.52–0.67 %**, and the part that actually crosses a model boundary — MWD is SP15-side,
so the PG&E slice is the misplaced part — is **0.24–0.30 % of ISO load**.

**Why it does not block limb (b):**

1. **It is orthogonal to caiso-172's measurement, provably.** Removing a *pro-rata* slice
   from `PGE-TAC` scales that area's level without touching its internal NP15/ZP26 ratio.
   The measured Path-15 split is unaffected; this is a level error on the wrong side of a
   different boundary.
2. **The magnitude is an order below the caveats it would have to matter against.** 0.24–
   0.30 % of load misplaced, against a C3a caveat of +11.5 %/+14.4 % on mean LMP.
3. **Limb (b) asks whether everything testable has been *tested*, not whether every intake
   has been *performed*.** caiso-172 found it by running the survey — the route is
   measured, characterised and documented. Closing it means **re-fetching the TAC series
   with `MWD-TAC` and adding its weights row**: a demand-input intake with its own
   authorization, in its own session.
4. **Nothing here may be re-picked against a residual** (rules 5/13/21/24). The fix is an
   intake or it is nothing; re-weighting the existing four areas to absorb MWD would be an
   outcome pin.

**Recommendation:** record it in the declaration as a named open demand-input gap, as
caiso-172 asked. **Keep it OUT of the FFR-4D re-solve** — that run already carries a
default-ON same-key invalidation, and folding an unrelated demand intake into it would
confound the one delta the re-gate needs to attribute (rule 19 `[R-ONE-MECH]` in spirit).

### D. `battery_dispatch_adder` and the `IMPORT/EXPORT_TRANCHES` fallback — **neither blocks**

caiso-171 said neither is a blocker. **Confirmed, and now on precedent rather than
assertion:**

- **`IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]`** — probe F2 measures that **NYISO carries the
  structurally identical entry** (`IMPORT_TRANCHES/EXPORT_TRANCHES[NYISO]`) as one of its
  two ISO-specific residuals **while holding the `complete` marker**. An entry class a
  marker-holding ISO carries cannot be a bar to another ISO's marker. On CAISO's keeper it
  is additionally *largely superseded on the binding path* — the seam is priced off
  measured hub prices and the fitted year-keyed ladder survives as the fallback. Named
  forward-valid replacement exists (the NEISO derive precedent,
  `derive_neiso_import_tranches.py`); issue **#1350**.
- **`battery_dispatch_adder = 5.0`** — live and genuinely calibrated. Inside the literature
  range (NREL ATB 2024 ~$15–25/MWh; Xu et al. 2018 $25–50/MWh) but the specific value is
  not identified. Named forward-valid replacement: measured AS power reservation
  (`storage_as_commitment`) + ATB-derived degradation cost. It is CAISO's one genuinely
  open DOF lane and **the right next non-lever work**, but `complete` is not a certificate
  of a clean ledger.
- *(The third, `WECC_import_simultaneous.cap_mw = 7500.0`, is not a backcast defect at all:
  superseded in the keeper by the published branch-group MIC sum and measured binding in
  **0/0/0 hours** at caiso-157. It survives as a forecast-mode parity item, issue #1373.)*

### E. FFR-4D's D-1 and D-4 — **forecast-lane objects; they do NOT block a backcast `complete`**

Both are, in kind, exactly what limb (b) targets: known, measurable, unused CAISO inputs.
They are adjudicated as non-blocking, and the reason is **verified rather than asserted**.

- **D-1** — CAISO is absent from `STORAGE_ELCC_BY_DURATION_BY_ISO` (which holds PJM only)
  while CAISO **publishes** a whole-class realized battery accreditation of
  **13,365 / 14,131 = 0.9458** against the model's generic blended **0.6875**. On the
  corrected 15,450 MW fleet that is **+3,990.6 MW** — the largest single term left in
  CAISO's base-year adequacy ledger.
- **D-4** — CAISO's storage-ELCC portfolio dilution is a hard **1.0**
  (`STORAGE_ELCC_DILUTION_*` hold ERCOT only) — cheap at 8,000 MW of storage, not at
  15,450.

**Why they do not bear on a *backcast* `complete`.** Traced to their call sites: both live
in `model/capacity_evolution/` — `_elcc_for_duration` feeds the storage capacity-value /
entry screen, `STORAGE_ELCC_DILUTION_*` feeds `retirements.py` and, through
`accredited_firm_capacity_mw`, the reliability floor and the reserve-margin backstop.
Those are the **adequacy ledger**: the retirement screen, the build backstop, CR-1.

The decisive check is not the call graph but the **scorecard**. The keeper's own
`metrics.json` enumerates the nine criteria a CAISO backcast is graded on:

> `dispatch_corr` · `forced_share` · `fuelmix` · `governance` · `price_mean` ·
> `price_shape` · `price_tail` · `shape` · `sysvol`

**Not one of them reads accreditation, reserve margin, or capacity value.** D-1 and D-4
cannot move a backcast determination because no backcast criterion is a function of them.
They are **FFR-lane items** and belong to the forecast program's §2.1b gate board, not to
this marker.

**Stated rather than omitted, per the charter — and if the reading were otherwise it would
change the recommendation.** It does not: the recommendation is already NOT YET on the
epoch, and D-1/D-4 neither add to nor subtract from that.

### F. The matrix — **0/0/0/0/0, and the `O` cell IS the GATE 0 fact**

**Reported as run, not as expected:** `mechanism_matrix_gap_sweep.py --iso CAISO` returns

```
family fields 63 | ABSENT 0 | prose-only 0 | ARMED-NO-CELL 0 | live-but-invisible 0
```

— **0 / 0 / 0 / 0 / 0**, unchanged after FFR-4D merged. The sweep is a *visibility* check
(is every armed ISO-scoped field represented by a cell?), not an *adjudication* check, so
an `O` cell passes it by construction. That is correct behaviour and not a gap.

CAISO's column census is now **60 K · 20 U · 13 I · 6 R · 5 G · 6 O** (caiso-171 read
59/19/13/6/5/**4**). The two new `O`s are `storage_measured_base_fleet` (FFR-4D) and
`thermal_tranche_artifact_coverage` (xiso-1); the `K` gain is caiso-172's
`path15_load_split`. The six `O` cells:

| cell | lane | bears on a backcast `complete`? |
|---|---|---|
| **`storage_measured_base_fleet`** | **BACKCAST, default-ON** | **YES — this is the blocker** |
| `caiso_nqc_accreditation` | forecast (default-off, held by owner decision D.1) | no |
| `economic_retirement_screen` | forecast | no |
| `entry_dampers` | forecast | no |
| `thermal_tranche_artifact_coverage` | cross-ISO artifact census | no |
| `caiso_firm_selfsched_floor` | backcast, default-off | no — an untested optional lever |

**Is an open `O` compatible with limb (b)? For five of the six, yes** — caiso-171
recommended YES carrying four of them, and an untested *default-off* lever is an open
queue item, not a failure to test what was testable.

**`storage_measured_base_fleet` is different in kind, and the difference is the whole
point.** It is **backcast-scoped and default-ON**: it is not an optional lever awaiting a
probe, it is an **armed change to the production path that the designated keeper
predates**. Its `O` does not say "nobody has tried this yet" — it says "the current keeper
was not solved on the current model." That is the same fact as GATE 0, recorded in the
matrix. FFR-4D entered it as `O` rather than `K` deliberately, so the default-ON arming
would not be misread as a tested verdict; that discipline is what makes the cell readable
here.

**The re-solve resolves this cell and the marker question in the same act.** FFR-4D's own
evidence note says so: *"What would adjudicate it is a CAISO backcast 2023-2025 (rule 16),
which is also what the keeper re-solve owed at §7 D-2 requires; the same run settles
both."*

---

## 3. Keeper state — unchanged, and unchanged is the point

| check | result |
|---|---|
| `calibration_verdict.py --run-id 2026-08-04-caiso-172-measured-path15` | **CALIBRATED-WITH-CAVEATS**, **0 FAIL**, 2 ledgered caveats (C3a mean LMP, C3c price tail), D-10 free-class C1 **12/12** · free **8/8** |
| ledgered rows (probe F1) | `price_tail` 2023, `price_tail` 2024, `price_mean` 2024, `price_mean` 2025 — **2 of 3** non-protective criterion slots |
| `audit_keepers.py --iso CAISO` | **PASS** — 0 failures, 0 warnings (keeper, holdout, marker, status) |

**caiso-171 §2.1's qualifier stands and is UNCHANGED by caiso-172.** The C3a criterion
covers **two** years, not one: `price_mean` 2024 was owner-ledgered 2026-08-04 when the
caiso-166 loss arm moved it +9.5 % → **+11.5 %**, and 2025 stands at **+14.4 %** against
the caiso-145 ledger text's +10.9 %. caiso-172 is determination-neutral against its own
bit-identical control and leaves both magnitudes unmoved. **A declaration must carry the
two-year framing, not the single-year one it would inherit.**

---

## 4. Open root-cause issues carried — NAMED, not buried

### KNOWN-OPEN 1 — the N–S congestion majority. **Still wide open; it moved toward, not to.**

Re-measured on the **current** keeper (probe F3; annual means, clock-invariant, so the
`FINDING-caiso168` Feb-29/UTC alignment defect cannot touch it):

| year | measured `NP15−ZP26` | `dMCC` | `dMCL` | congestion share | **model** | model / measured | *(was, caiso-166)* |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | +5.947 | +4.771 | +1.176 | **80.2 %** | +0.333 | **5.6 %** | *4.0 %* |
| 2024 | +8.576 | +7.475 | +1.102 | **87.2 %** | +0.217 | **2.5 %** | *1.5 %* |
| 2025 | +5.727 | +4.677 | +1.049 | **81.7 %** | +0.179 | **3.1 %** | *1.9 %* |

caiso-172's measured split moved the model **toward** the measured basis in all three
years — and the model still reproduces only **2.5–5.6 %** of it. The **congestion majority
— 80–87 % of a $5.7–8.6/MWh basis — remains unrepresented.** This was pre-registered as
reported-not-gated and stays so. **No N–S topology lever is chartered off it**; caiso-164
§0/§6 stands and caiso-172 explicitly declined to.

### KNOWN-OPEN 2 — the within-day storage placement pointer (caiso-170). **Untested.**

Carried unchanged, with its framing correction intact: on a like-for-like battery basis the
"overnight over-position" **reverses sign in 2024 and 2025**, so no successor may scope
itself to "remove overnight discharge."

**A live interaction the next session must weigh:** this pointer was measured on a
**pre-epoch** fleet. Its within-day storage placement statistics were computed against a
fleet up to 48 % short of the one that operated. **The re-solve may move this pointer, and
KNOWN-OPEN 2 should be re-read after it rather than carried forward as measured.**

### Also carried, not open lanes

The **SDGE limb inversion** re-measured on the current keeper (probe F4): model
`SDGE − SP15_rest` runs **−2.080 / −4.755** in the 2024/2025 belly against a measured
`|dMCC|` of **+4.038 / +6.451** — the sign inversion caiso-171 flagged, unmoved. The
`LA_BASIN − SP15_rest` limb now separates 100 % of belly hours in 2024/2025 but with ratio
sd **0.0038 / 0.0026**, i.e. a **proportional loss wedge, not congestion** — the corridor
still does not bind, which is what keeps Wall 2 standing.

---

## 5. Follow-on work

1. **THE ONE BLOCKER — the FFR-4D re-solve.** CAISO backcast, **2023/2024/2025 in one
   bundle** (rule 16), at post-epoch `main`, registered per rule 15, re-gated, and the
   `storage_measured_base_fleet` cell moved off `O`. **This is the gate on the marker.**
2. **MWD-TAC intake** (§2 C) — re-fetch the TAC load series including `MWD-TAC`, add its
   weights row. Its own session; **keep it out of the re-solve.**
3. **`battery_dispatch_adder`** (§2 D) — CAISO's one genuinely open DOF lane, with a named
   forward-valid replacement.
4. **KNOWN-OPEN 1 and 2 stay named** (§4). Neither is chartered; the N–S topology lever
   remains forbidden.
5. **When the freeze lifts**, re-audit the keeper on the corrected availability envelope
   before spending 2022, per the freeze's own `held` rationale.
6. **Routed, not fixed — a red lint on `main` that is not CAISO's.**
   `src/market_sim/config/scenarios.py:758` declares `"ercot_storage_rt_offer_surface"`
   a second time (already at :736) in the cache-key declared-defaults table, tripping
   ruff **F601**. Both values are `"False"` so it is behaviourally inert and
   `check_cache_key_registration.py` still passes, but it is a lint failure on clean
   `origin/main`. It arrived with FFR-4D's D-6 backfill colliding with an existing
   entry. **Deleting one line is a one-character fix, and this session deliberately did
   not make it**: it declared no `src/` edits, and a duplicate-key removal in the
   cache-key table is the kind of change that should be made by the lane that owns it
   with that lane's guards run. Flagged for whoever touches `scenarios.py` next.

---

## 6. The pre-registered condition — what makes this a YES

Stated here so the successor session does not re-litigate the frontier question. **Every
frontier limb is satisfied on this ledger except the epoch.** Therefore:

> **If the FFR-4D re-solve returns `CALIBRATED-WITH-CAVEATS` with no NEW criterion FAIL
> and no new caveat slot spent, the recommendation on `complete` becomes YES, and no
> further frontier work is required to support it.** The re-solving session should cite
> this section, re-run `scripts/probes/caiso173_frontier_recheck.py` against the new
> keeper (G0 will flip to post-epoch), and recommend YES on that record.

If instead the re-solve **degrades the determination** — a new FAIL, or a third caveat
slot — that is a calibration finding in its own right, the marker question reopens on
substance rather than on vintage, and it escalates to the owner rather than being written
silently (rule 22 D-5(b)'s posture, applied prospectively).

**And what a YES would authorize, unchanged from caiso-171 §6:** the `complete` block
authorizes the **validation ladder and nothing else** (2022 and its backward extension);
it is **iterable by design**, so a 2022 number is model-**selection** evidence and must
never be quoted as a certified out-of-sample skill number; the locked test (2019, H1-2026)
needs the separate **`final`** block, which is still deliberately empty; the **holdout
freeze outranks the marker** and is checked first, so a `complete` CAISO may still solve
nothing outside 2023–2025 until the owner lifts it; and it creates a **standing rule-22
D-5(b) obligation** on every future CAISO promotion — re-key the entry's `keeper` and
**re-verify its `determination`** against the new run, in the promotion commit itself.

---

## 7. Verification performed this session

| check | result |
|---|---|
| GATE 0 — `merge-base --is-ancestor 58c22e32 origin/main` (start **and** pre-recommendation) | **TRUE** both times → **outcome (ii)** |
| keeper pre-epoch (three independent signals) | **PRE-EPOCH** — sha ancestry, field absent at `789e28b8`, field absent from `run_config.json` |
| post-epoch CAISO run registered? | **NONE** — the newest CAISO registry entry is the pre-epoch keeper itself |
| `calibration_verdict.py --run-id 2026-08-04-caiso-172-measured-path15` | **CALIBRATED-WITH-CAVEATS**, 0 FAIL, 2 ledgered caveats, D-10 12/12 · free 8/8 |
| `audit_keepers.py --iso CAISO` | **PASS** — 0 failures, 0 warnings |
| `_caiso141_water_source_survey.py` (live network) | **5/5 `unchanged`** — wall 1 holds |
| `_caiso172_subtac_load_survey.py` (live network) | **5 walls `unchanged`**, S2 still `AVAILABLE` (reproduces 0.8844/0.1156) |
| Arm B / C3c `data/raw` census | no intra-SP15 transfer limit; no OFO record — walls 2 and 3 hold |
| §5.2 evidence documents (probe F5) | **19 of 19 resolved, 0 missing** (caiso-171's 16 + caiso-172's finding, precheck and the caiso-171 assessment) |
| `mechanism_matrix_gap_sweep.py --iso CAISO` | **0 / 0 / 0 / 0 / 0** (63 family fields) |
| CAISO matrix column census | 60 K · 20 U · 13 I · 6 R · 5 G · **6 O** |
| `check_mechanism_matrix.py --base origin/main` | gap ratchet **OK**, shared ratchet **OK** (anchor + NEISO-stamp warnings pre-existing, other lanes) |
| `check_registry_payload_parity.py` | **OK** — 92 runs, 0 unsynced |
| `check_cache_key_registration.py` | **ok** — 683 fields, 130 registered, all resolve, 130 declared defaults match HEAD |
| `derive_caiso_path15_load_split.py --acceptance` | **10/10**; re-derived artifact byte-identical (no drift) |
| `derive_caiso_loss_surface.py --acceptance` | **12/12** pair-years in band |
| `ruff check scripts/ src/` | 2 errors, **both pre-existing on clean `origin/main`, neither in this session's diff** (which touches no `src/`): `scripts/gen_miso126_attestation.py:124` F841 (the known one), and **NEW — arrived with the rebase onto `783833bb`** — `src/market_sim/config/scenarios.py:758` **F601 duplicate dict key** `"ercot_storage_rt_offer_surface"` in the cache-key declared-defaults table (also at :736, same value `"False"`, so behaviourally benign but a red lint). **Reported, not fixed** — `scenarios.py` is outside this no-solve assessment's declared scope and belongs to the lane that backfilled the entry (FFR-4D D-6). See §5 item 6 |
| `node --check` on the matrix | **OK** |
| `calibration-complete.json` | `complete` = NEISO, NYISO, PJM — **CAISO ABSENT**; `final` empty. **UNTOUCHED** |
| `holdout-freeze.json` | **`active: true`**, ALL ISOs, BOTH tiers. **UNTOUCHED** |
| years touched | **2023/2024/2025 only** — no solve of any kind was run |

**Nothing was registered on the dashboard** — no run was produced. **No cell verdict
moves** — no mechanism was tested.

---

## 8. Files

- This assessment.
- `scripts/probes/caiso173_frontier_recheck.py` — the instrument (no LP, no solve, no network).
- `results/calibration/_caiso173_frontier_recheck.json` — its record.
- `docs/mechanism-testing-matrix.md` §5.2 header — assessment + verdict recorded (rule 28 duty b).
- `docs/calibration-log/caiso.md` — appended.
