# PRECOMMIT — ercot-170: the ~2.7 GW CC headroom/capability object, adjudicated per unit against the delivery-2023 SCED corpus

**Session ercot-170, 2026-08-05. Charter: mechanism-testing-matrix §5.1 item 11
(the ercot-163 close-out, CHARTERED). PHASE 0 — NO LP, no solve, keeper
UNCHANGED (`2026-08-05-run168b-year-curves`), no `ScenarioConfig` field
written.** This document is committed and pushed **before** any derive or probe
is run. Every threshold, band, coverage bar and verdict branch below is fixed
here and **may not be moved after measurement**, in either direction.

## 0. The object

ERCOT-163 refuted the "~8 GW cheap CC offline block" and left behind a real,
smaller, differently-shaped residual (`FINDING-ercot163…` §4). At the committed
top-100 2023 gap hours:

| | model | reality |
|---|---|---|
| CC dispatch | 30.04 GW | 29.73 GW |
| CC capacity **not** dispatched | **3.07 GW** | **0.35 GW** |

The model's CC *output* is right to +0.30 GW; its *depth* is ~9× the market's.
ERCOT-163 named the provenance as **capability, not commitment** — the model's
CC classes carry 38.83 GW nameplate (CC_REGULAR 33.12 + CC_CHP 5.71) against an
ERCOT SCED CC universe of 35.26 GW (train-grain p98 HSL) — and handed the object
forward **unchartered**, because neither of its probes could attribute it to
specific units: *"an unattributed aggregate must not be handed forward as a
mechanism premise."* This session does the attribution.

**Model-side inventory, enumerated before this document was written** (needed to
specify the join; it is fleet identity metadata, not the measured object): the
ercot168 keeper's 2023 CC fleet is **616 LP rows over 61 physical plants /
38.834 GW** — 42 CC_REGULAR plants (33.120 GW) + 19 CC_CHP plants (5.714 GW).

## 1. Instruments — imported verbatim, never re-implemented

The ercot-169 discipline: every committed construction is imported from the
probe that built it and fed delivery-year rows.

* **`scripts/lib/sced_corpus_instruments.py`** (ercot-169) supplies the
  delivery-year corpus loader, the ercot-123/144 row filters, the CPT→CST
  conversion at derivation (ercot-166) and the publication→delivery month keying
  (delivery = filename − 2). It is **EXTENDED** with the capability census; it is
  not re-written and its existing functions are not modified.
* **`scripts/probes/ercot163_cc_commitment_state_census.py`** supplies
  `_cap_ref` (per-TRAIN p98 telemetered HSL over delivery-2023, configuration
  aliases collapsed on the trailing `_<config>` segment), `_train`, `_state_of`
  and `_hoy` — **imported verbatim**. Re-deriving any of them here would make
  this session's numbers incomparable to the ercot-163 record they must bridge.
* **Model side**: `scripts.lib.bundle_fleet.reconstruct_bundle_fleet` on the
  keeper bundle `results/calibration/ercot168_yearcurves_B`, with the fidelity
  guard asserted; dispatch from the keeper's committed
  `hourly/class_hourly_2023.parquet` (P1). No LP.
* **Hour set**: the committed top-100 2023 gap hours,
  `results/calibration/_ercot161_wall_phase0.json` — the same set ERCOT-163
  scored, so the 3.07 / 0.35 GW figures are reproduced, not re-cut. Every
  statistic is additionally reported over `all` 8760 hours as a
  **non-gating** control.

### 1a. Row filters — and the ONE declared delta from ercot-123/144

* Resource Type ∈ {`CCGT90`, `CCLE90`} (the CC universe). `CLLIG` is coal and is
  not read by this session.
* **Capability census (the Term-A denominator): NO telemetered-status filter.**
  This is a deliberate, declared departure from the ercot-123/144 `ONLINE` row
  filter, and the reason is structural: a capability denominator that drops
  `OUT` / `OFF` rows is biased toward committed capacity and would measure
  commitment — the very object ercot-163 already closed — instead of capability.
  `cap_ref` is `ercot163._cap_ref` verbatim (p98 over all rows a train
  telemeters); a train that never telemeters a finite HSL is dropped and is
  **reported by name**, never silently absorbed.
* **Conduct/loading statistics, reported alongside and NON-GATING**: the
  unchanged ercot-123/144 set — `ONLINE`, `HSL > 0`, `HSL > LSL`, `HASL` and net
  output non-null — via `sced_corpus_instruments.load_corpus_year`.
* Rule 22 `[R-HOLDOUT]`: delivery **2023 only**. `load_corpus_year` already
  refuses any year outside 2023–2025; nothing outside the training span is read,
  solved or scored.

### 1b. The crosswalk — published spine, tiered acceptance, bar fixed HERE

**Spine (published data only, no judgement).** ERCOT MIS NP4-160-SG
(`data/raw/ercot-network-model/`, ercot-160 intake):
`CCP_Resource_Names_*.csv` (68 CC logical resources) → `RESOURCE_NODE` →
`Resource_Node_to_Unit_*.csv` (`UNIT_SUBSTATION`, `UNIT_NAME`) →
`Settlement_Points_*.csv` (`SETTLEMENT_LOAD_ZONE`). The README's vintage limit is
binding and is honoured: the fetched network model is a 2026 vintage, so **this
session reports its own match rate against delivery-2023** rather than assuming
the ercot-160 CT coverage carries back.

**A model-plant ↔ SCED-train-group match is ACCEPTED only under one of:**

* **X1 — COMMITTED.** The pair appears in
  `data/raw/reference/ercot-dam-plant-crosswalk.csv` with `accepted=1`, or in
  `data/raw/reference/ercot_noncampd_dam_crosswalk.csv`. Authority: already
  hand-adjudicated under the ERCOT-97/110 review.
* **X2 — LEXICAL IDENTITY on the published spine.** After normalisation
  (upper-case, non-alphanumerics stripped), the SCED site mnemonic **or** its
  `UNIT_SUBSTATION` is a substring of the model plant's name with all its
  characters consumed in order by a *prefix of a name token* (so `RIONOG` ⊂
  `RIO NOGALES`, `JACKCNTY` ~ `JACK COUNTY`), **AND** the capacity ratio
  Σ`cap_ref` / model `pmax` ∈ **[0.70, 1.30]**.
* **X3 — PUBLISHED-EVIDENCE ADJUDICATION.** A row is accepted only on evidence
  that is **on disk or in a published file**. Exactly three admissible evidence
  classes:
  * **E1** — the ERCOT `qse` code (crosswalk file) plus capacity ratio ∈
    [0.90, 1.10] plus zone agreement leave **exactly one** surviving model plant;
  * **E2** — the `Resource_Node_to_Unit` `UNIT_NAME` set matches the plant's
    EIA-860 generator-ID set as an exact multiset;
  * **E3** — the substation name is a normalised-token superstring/substring of
    the EIA plant name **or** of its EIA-860 county.

  **No row may be accepted on model recall of ERCOT mnemonics alone.** A
  plausible-looking mnemonic expansion with no on-disk evidence is
  **AMBIGUOUS**, not accepted. This is the ercot-163 §3 lesson applied to the
  crosswalk itself: the "~8 GW" existed because a plausible reading of a
  published file was carried forward unverified.

Everything unresolved stays **UNMATCHED** on its own side (`MODEL_ONLY` /
`SCED_ONLY`) or **AMBIGUOUS** (a candidate exists but fails the test), and every
bucket is reported at MW grain.

**Coverage licence — pre-registered, NOT lowered after measurement, and NOT
lowered against the hypothesis either** (the ercot-169 §1b symmetry: a biased
instrument manufactures a false confirmation and a false refutation equally
easily):

* **L1 — SCED-side closure ≥ 0.90.** Accepted matches must cover ≥ 90 % of the
  SCED CC `cap_ref` capability. Rationale: every registered ERCOT CC resource
  should exist in the model's CAMPD-derived fleet, so a large unmatched
  *SCED-side* block means the crosswalk is broken, not the model.
* **L2 — ambiguity budget ≤ 0.10.** Model CC `pmax` in the AMBIGUOUS bucket
  ≤ 10 % of model CC `pmax` (≤ 3.883 GW).
* **L3 — zone-frame agreement: REPORTED, EXPLICITLY NOT A GATE.** Declared
  non-gating here, before measuring, with the reason: the model's 7-zone ERCOT
  topology is not ERCOT's settlement-load-zone partition (`LZ_AEN` / `LZ_CPS` /
  `LZ_LCRA` all fold into `South_Central`), so a disagreement is a
  representation artifact, not a crosswalk error. It is reported because a
  *systematic* disagreement would still be diagnostic.

Failing L1 or L2 ⇒ **FILED-UNLICENSED** (§2), verdict withheld in both
directions.

### 1c. The attribution identity — exact, and fixed here

At the gap hours (mean MW over hours), with the reality side taken at train
grain over states {`ONLINE`, `ONTEST`, `OFFLINE_STARTABLE`, `TRANSITION`} (the
committed-or-startable capability; `OUT` and plain `OFF` are reported separately
and are **not** counted as reality-side capability):

```
C_m = model CC available          = Σ pmax × availability
D_m = model CC dispatch           (keeper class_hourly_2023, P1)
H_r = reality telemetered HSL     (committed-or-startable states)
C_r = reality energy-dispatchable = HASL on those states, + offline-startable
D_r = reality Base Point

U_m − U_r  =  (C_m − D_m) − (C_r − D_r)
           =  [C_m − H_r]  +  [H_r − C_r]  −  [D_m − D_r]
              -----A-----     -----B-----     -----C-----
```

* **Term A = C_m − H_r** — the **CAPABILITY gap**. THIS session's object; the
  crosswalk splits it per unit.
* **Term B = H_r − C_r** — reality's AS reservation on committed CC (HSL − HASL).
  An ancillary-services-lane term. Measured and reported; **not** this lane's.
* **Term C = D_m − D_r** — the dispatch difference (ERCOT-163: +0.30 GW).

The identity is exact by construction, so the three terms must sum to the
measured `U_m − U_r`; a residual > 0.01 GW is a **construction error** and stops
the session (reported, not patched).

Term A is split per unit into, with signs as written:

| bucket | definition |
|---|---|
| `A_absent` | model plants with **no** SCED counterpart — their whole `pmax × availability` |
| `A_derate` | ACCEPTED-matched plants where model capability > matched SCED HSL |
| `A_short` | ACCEPTED-matched plants where model capability < matched SCED HSL (**negative**) |
| `A_sced_only` | SCED trains with no model plant (**negative**) |
| `A_ambiguous` | the L2 bucket, unattributed by construction |

`A_named ≡ A_absent + A_derate + A_short` — the signed contribution of plants
this session can name. Every plant contributing ≥ 25 MW to any bucket is listed
by name, EIA plant code, MW and share in the FINDING.

## 2. The decision rule — PRE-REGISTERED, branches mutually exclusive

Evaluated in order; the first branch that fires is the verdict.

1. **FILED-UNLICENSED** — if **L1 < 0.90 or L2 > 0.10**. The per-unit attribution
   is not licensed. Unlicensed magnitudes MAY be surfaced (they are the session's
   substantive content) but they are **not verdicts and not a licence to arm
   anything** (rule 13). No mechanism named. Session files and stops.
2. **REDIRECTED** — if licensed but **A / (U_m − U_r) < 0.60**. The headroom
   object is then not principally a capability object; the finding reports which
   term (B or C) owns it, re-points item 11, and **stops**. In particular, if
   term **B** dominates, the object belongs to the ancillary-services lane and
   this session does not touch it (rule 19 `[R-ONE-MECH]`).
3. **ACTIONABLE** — if licensed, `A / (U_m − U_r) ≥ 0.60`, **and**
   `A_named / A ≥ 0.60` with every contributing plant named. The object is then a
   rule-14 `[R-ACCURATE]` fleet-scope correction on the **existing**
   `ercot_thermal_dam_availability_*` channel. This session **specifies** the
   correction and its gates (§3); it does **not** build or arm it without an
   explicit owner adjudication in-session.
4. **FILED-NULL** — otherwise (licensed, A dominant, but `A_named / A < 0.60`).
   The object is real and not per-unit attributable on committed data. **FILE AND
   STOP**, naming exactly what data would unblock it. Per the ercot-170 charter
   fences a null result is a complete session.

**The 0.60 bars are chosen for one reason, stated before measuring:** a majority
plus margin, so that the *named* units and not the *residual* carry the object.
Below it, any mechanism premise would again rest on an unattributed aggregate —
precisely what ERCOT-163 §3 forbids.

**Hard fences (ercot-159/163, binding, not re-litigated here).** Whatever the
verdict, this session will NOT propose: a new commitment gate; an aggregate cap
(`energy_online_capability_cap` is `R`); a per-hour telemetered-HSL cap (rule 13
`[R-MEASURED]`-forbidden — it pins the model to a measured outcome); a re-pricing
of CC (ERCOT-152, upheld ERCOT-158). The **only** admissible channel is the
existing `ercot_thermal_dam_availability_*` fleet-scope path.

## 3. If a mechanism follows — kill gates, fixed HERE

Reached **only** under branch 3 **and** only on an explicit in-session owner
adjudication. Any A/B is full-span `--year 2023 2024 2025` in one bundle (rules
15/16) and every run is registered whatever the outcome.

* **G-BIT — byte-identity on years the arm must not touch.** If the correction is
  identified per-year from each year's own corpus it touches all three years, so
  G-BIT is **declared N/A with that reason recorded pre-solve** and replaced by
  **G-SCOPE** below. If the correction is 2023-scoped, G-BIT is live: all
  2024+2025 hourly sidecars (`class_hourly`, `system`, `reserve_family`) must be
  sha256-byte-identical A→B.
* **G-SCOPE** — no class outside {CC_REGULAR, CC_CHP} may move annual energy by
  more than **0.5 %** in any year. A capability correction on CC that
  re-dispatches coal or storage is not a capability correction.
* **G-SPUR** — spurious mid-band tail-hour count must not increase in any year.
* **G-SHED** — shed-hour count must not increase in any year.
* **G-C3c** — the three ledgered tail counts (61/181, 25/53, 3/31) must not
  degrade.
* **G-DOF** — **zero** new fitted scalars. Every number is a measured MW or an
  accepted crosswalk row (rule 20 `[R-DOF]`); a residual that can only be closed
  by a tuned value is an open root-cause issue, not a parameter.
* **G-D2** — no class's forced share may cross its rule-20 `[R-FORCED-BUDGET]`
  cap as a result of the arm.
* **Rule 22 LOYO** — leave-one-year-out within 2023–2025 before any promotion.

Failing any live gate ⇒ the arm is REJECTED-AS-ARMED and reported as such; the
gates are not renegotiated after the solve.

## 4. Scope fences and DO-NOT-REDO honoured

Standing, all carried unchanged: the "~8 GW cheap CC offline block" **DOES NOT
EXIST** (ERCOT-163 — not reopened); `energy_online_capability_cap` `R`
(ERCOT-159); `ercot_storage_rt_offer_surface` `R` (ERCOT-162); per-year CT
re-identification REFUSED (ERCOT-147, modal identity 11/160); lignite offer SLOPE
(ERCOT-143 as adjudicated); `coal_min_load_floor` both grains; lignite daily unit
commitment; coal seasonal LEVEL split; `coal_offer_level_rebasis` `R`;
`tranche_startup_amortization` `G`; ercot-168 **OPTION B** stays DEFERRED; the
ercot-167 SOC-reserve re-gate waits on the H4-item-4 2024 maintenance-season
availability defect; the West/Panhandle topology split is **CLOSED**
(`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10).

**Item 11's extreme-hour face** (the 4 phantom shed hours and the 1.7–3.1 GW gas
shortness at the top-10 actual hours) is **explicitly out of scope for this
session** and stays chartered under item 11.

**Carried forward, surfaced not decided (ercot-169 §6):** the OPEN owner decision
on the 2023 application of `COAL_OFFER_MARGIN_LEVEL_BY_ISO` (ERCOT-137) and
`COAL_PEAK_OFFER_LEVEL_BY_ISO` (ERCOT-140), both NOT-IDENTIFIABLE-2023. The
pre-registered REFUTED branch was not reached, so **no candidate arm is named and
none may be built** without a fresh owner adjudication. This session does not act
on it.

**Governance.** Rule 25 `[R-ISO-SCOPE]`: ERCOT-scoped throughout; no other ISO's
cell or artifact is read or written. Rule 15: no solve ⇒ no bundle ⇒ no dashboard
registration; if any solve is run, every run is registered across all three
training years in one bundle. Rule 28(b)/(c): matrix §5.1 item 11 is stamped in
this session and any mechanism cell this session tests is re-cited, rejections
included.

**Next shorthand: ercot-171.**
