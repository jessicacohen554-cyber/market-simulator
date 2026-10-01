# PRECOMMIT — caiso-258: the hod 22–23 CC over-run has had two carriers named and both removed (import REFUSED on admissibility at caiso-253; storage on the WRONG SIDE at caiso-255b/256). **This session does not name a third from a mechanism looking for a home. It writes the energy balance at hod 22–23 on BOTH sides — the keeper's LP identity and the EIA-930 balancing-authority identity — and lets the closure say what the market ran instead.** ZERO LP by construction: no arm is coded and no solve is spent by this document.

**Session caiso-258, 2026-09-06.** Branch
`claude/caiso-258-backcast-calibration-b1nal9` off `main` `4b4df964`. Keeper
**`2026-09-06-caiso-257-b1-ctonly`** (bundle `caiso257_ctonly`) UNCHANGED,
DETERMINATION **CALIBRATED** (rubric v3.6), C3c-2024 the single ledgered
caveat. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; CAISO holds no
`complete`/`final` marker (re-raised at caiso-257, owner again declined); the
holdout spend freeze is ACTIVE.

**Pushed BEFORE any cell of the object is computed.** §8 lists exactly what
was read before this push — schemas and published numbers only; **no value at
hod 22 or 23 of any series has been read on this keeper.**

---

## §0 — WHY THIS OBJECT, AND WHY A CLOSURE RATHER THAN A CANDIDATE

The handoff ranks the hod 22–23 CC over-run first because it is the lane's
**only open structural object with a live measurement and no named carrier**.
The record on it, in order:

| session | what it established | status |
|---|---|---|
| caiso-252 §2.2 / caiso-253 G-REPRO | CC_REGULAR over-runs **+1,547 / +1,558 MW** at hod 22 / 23 in 2025 (CEMS basis) — the two largest CC error hours of the day | the object |
| caiso-253 P-5 | the keeper is SHORT of net import there: **−984 / −1,405 / −1,662 MW** (2023/24/25), hours 22–23 being the two worst import-deficit hours of the day in every year | measured, not a lever |
| caiso-253 G-WEDGE | an at-hub clean-transfer row at 22–23 is **REFUSED on admissibility** — in 2023 CAISO clears BELOW the raw Palo Verde hub on DA at both hours, because the DSW peaks later (Arizona keeps no DST) | CLOSED as an import-PRICE object |
| caiso-255b / caiso-256 | storage is on the **WRONG SIDE**: the model is LONG storage at 22–23 in every year (all-tech +532 / +549 / +707 MW; battery-only +235/+199, +161/+191, +276/+414 MW) | REFUTED as a storage object |

So the two obvious carriers are out, and the handoff's instruction is exact:
*"A candidate MUST come from what the market actually ran in those hours —
start from the measured record (CAMPD unit conduct, EIA-930, the CAISO
outage/RA record), not from a mechanism looking for a home."*

**What has never been written down is the full closure.** Every prior
measurement was one pair at a time — CC vs CEMS, import vs 930, storage vs
`NG: OTH`. Nobody has put the whole hour on one page and checked that the
pieces sum: the model serves a *different demand* from EIA-930's (caiso-247
§4.5: 205.6 vs 223.8 TWh in 2025, a mid-day-shaped gap), the CEMS basis and
the 930 `NG: NG` basis are not the same gas, the model's `hydro` klass and
EIA-930's `NG: WAT` may or may not both carry pumped storage, and EIA-930's
`NG: GEO` column is **NaN all year** (schema read, §8) so ~14 TWh/yr of CAISO
geothermal + biomass sit somewhere that has to be named before any category
is differenced. A "carrier" read off one pair while the closure is unwritten
is how the storage re-pointing happened.

**The deliverable is therefore the closure itself**, with the attribution
that falls out of it — and if the closure names a carrier, that carrier's
admissibility question is stated, not answered, here. §6's stop rule refuses
an arm from this document.

### §0.1 — THE C3a PATTERN, STATED UP FRONT (handoff instruction)

caiso-257 was the **eighth consecutive** CAISO promotion whose C3a moved
favourably while C3a was formally excluded from the promotion basis. Each
exclusion was correct and pre-registered. A lane in which every promotion
moves the same residual the same way is nonetheless the exact shape selection
bias takes. **This session solves nothing, so it cannot extend the streak to
nine** — but it is stated here so it is on the record in the PRECOMMIT and not
discovered in the FINDING: any arm this object ever produces will be a
night/evening-import or CC-displacement arm, i.e. an arm whose *first-order
direction on C3a is favourable by construction* (less CC at 22–23 ⇒ lower λ
there ⇒ a smaller C3a overshoot). A future PRECOMMIT on this object must
declare that direction as UNUSABLE before its solve, exactly as caiso-255
§3.1 did, and must find its evidence in something that contains no price.

### §0.2 — THE C4-2025 CONSTRAINT (handoff item B)

C4-2025 gas NRMSE sits at **0.300 against a ≤ 0.30 bound** with zero margin.
No arm is proposed here, so the pre-solve check is not spent. What this
document DOES register is the object's own exposure: the hod 22–23 CC error is
*part of* the 2025 gas MSE (D-4 below measures the share), so a carrier that
reduced it would move C4-2025 in the favourable direction — a fact about
direction, stated so no later session mistakes it for evidence, and one more
reason C4 stays excluded from any promotion basis on this object.

---

## §1 — G-REPRO: the instrument reproduces three published quantities, ON THE NEW KEEPER

Before any new cell is read, the probe must reproduce, from the committed
`caiso257_ctonly` artifacts, three quantities published on the *prior* keeper.
The keeper changed identity at caiso-257 (`FINDING-caiso257 §10 #5`), so the
tolerances are set from caiso-257's own measured deltas (CC_REGULAR −0.19 TWh
≈ −21 MW mean; import −0.017 TWh; storage unmoved), not to zero:

| quantity | published (caiso-252 keeper) | tolerance on caiso-257 |
|---|---|---|
| CC_REGULAR error, hod 22 / 23, 2025, scorer's CEMS basis | +1,547 / +1,558 MW | **±100 MW** each |
| keeper `import` − EIA-930 net interchange, hod 22–23, 2023/24/25 | −984 / −1,405 / −1,662 MW | **±100 MW** each |
| model net storage (all-tech) − `NG: OTH`, hod 22–23, 2023/24/25, loader clock | +532 / +549 / +707 MW | **±100 MW** each |

**G-REPRO FAILS ⇒ STOP.** An instrument that cannot reproduce the record on the
keeper it reads is not one I may extend (the caiso-255b P-2 standard).

Constructions are the lane's committed ones, verbatim: the CEMS basis is
`_caiso253_hod2223_gates._cc_regular_error` (the class term of
`calibration_verdict._cems_gas_hourly_fit`, no fleet fill); every EIA-930
actual comes through `eia930.frames._eia_hourly_frame_filled` (row k = local
hour k on the model's clock — caiso-255b §6 #1, never the raw parquet stamps);
the model's hourlies are the keeper's committed `hourly/` sidecars, `pass ==
"P1"`.

---

## §2 — G-CLOSE: both identities must close before anything is differenced

**Model side (an LP identity).** Over the five CAISO load zones (NP15, ZP26,
SP15_rest, LA_BASIN, SDGE), hour by hour:

> Σ_klass `mw` + Σ_tech (`discharge_mw` − `charge_mw`) + `slack` − `dump` = Σ_zone `demand`

where `import` is one of the klasses. This must close to **< 1 MW in every
hour**. If it does not, the `import` klass is not the net inflow the sidecar
implies and the model-side decomposition is re-based on `demand − (everything
else)`, with the discrepancy reported.

**Measured side (the EIA-930 BA identity).** `Demand` − `Net generation` −
(−`Total interchange`) is EIA-930's own balancing residual; it is not zero in
the published data and it must be **shown**, not absorbed. The closure is
written on `Net generation` + net import against `Demand`, and the residual is
carried as its own row.

**G-CAT — category identification, resolved from ANNUAL totals before any
hour is read.** Each EIA-930 column is mapped to model klasses and the map is
checked on annual energy: `NG: NG` ↔ {CC_REGULAR, CC_CHP, CT_PEAKER, CT_CHP,
ST_GAS}; `NG: NUC` ↔ nuclear; `NG: WAT` ↔ hydro (+ pumped-storage net, both
readings shown); `NG: SUN` ↔ solar; `NG: WND` ↔ wind; `NG: OTH` ↔ li_ion net
(caiso-255b G-ID); `NG: OIL` ↔ oil; `NG: COL` ↔ COAL. **`NG: GEO` is NaN all
year**, so the model's `OTHER` + `biomass` (~14 TWh/yr of geothermal and
biomass) have no 930 column; the probe locates them by the one test that can:
`Net generation` − Σ(mapped NG columns), whose annual energy and flat diurnal
shape identify a baseload remainder. Whatever the answer, the closure carries
that remainder as an explicit `unmapped` row. **A closure whose category map
is wrong is worse than no closure**; that is why this leg precedes D-1.

---

## §3 — D-1: THE CLOSURE TABLE (the deliverable)

Per year, at hod 22 and hod 23 separately (annual mean MW, loader clock), one
row per category, Δ = model − measured:

> demand · gas (CEMS basis, per class: CC_REGULAR, CT_PEAKER, CC_CHP, CT_CHP, ST_GAS) · gas (930 `NG: NG` basis, total) · nuclear · hydro (+PS) · solar · wind · storage (li_ion net) · unmapped/other · net import · 930 balance residual · slack/dump

with the identity check that the Δ rows sum to Δdemand on each side. The
**attribution** is then mechanical: rank the non-gas rows by |Δ| against ΔCC,
and state which rows, and how much of each, are the counterpart of the CC
over-run *after* the demand basis is taken out. Two readings are reported side
by side because they answer different questions:

* **the CEMS reading** — the scorer's own basis, the one C4 is scored on;
* **the 930 reading** — the BA's whole gas fleet, which is what the market ran.

If the two gas readings disagree by more than the non-CEMS gas fleet plausibly
carries (CHP and sub-25 MW units), that disagreement is itself a result and is
reported before either is used.

---

## §4 — D-2: CAMPD UNIT CONDUCT AT hod 22–23 — what the real CC fleet DID

From the committed bench part (per-plant CAMPD hourly at nameplate scale) and
the keeper payload (per-plant model hourly), for every CEMS-covered CC_REGULAR
plant, 2025 first and the other years beside it:

1. **State at 22–23**: OFF (CEMS < 5 % of nameplate), PART (5–80 %), HIGH
   (≥ 80 %) — actual vs model, plant-hour counts.
2. **Where the over-run comes from**: the +1.55 GW split into (a) plants OFF
   in reality that the model runs, (b) plants ON in reality that the model
   runs higher, (c) plants the model runs lower (negative contributions).
3. **The 21 → 23 transition**: plant-hours in which the real unit goes from
   ≥ 20 % at hod 21 to < 5 % by hod 23 (an evening SHUTDOWN), against the
   model's count of the same transition.

This is the handoff's "CAMPD unit conduct" leg. It distinguishes a
**turn-down** object (the fleet stays on and ramps down — a dispatch/energy
question) from a **shutdown** object (units cycle off after the evening peak —
a commitment question under rules 18 `[R-PHYSICS]` / 12 `[R-FLOOR-WINDOW]`,
the same family as the Panoche object). The two need different mechanisms and
are trivially confusable from a class-level error.

---

## §5 — D-3: THE MODEL'S IMPORT STACK AT hod 22–23 — capability gap or price gap?

caiso-253 §3.3 measured that a *hypothetical* clean row would have cleared in
54–59 % of these hours. Nobody has measured what the **armed** rows do. On an
on-recipe `fleet_only` rebuild of the keeper (`replay_keeper.run_year_kwargs`
+ `derived_run_year_inputs`, the caiso-252 firm-block probe's pattern;
`data/clean` partitions materialised first per `ADDENDUM-caiso257 §7` so the
seam cap reads `mic_partition`, verified in the rebuild), read every
`WECC_*` import row's capability, floor and offer at hod 22–23 against the
keeper's committed WECC node duals:

* capability at 22–23 vs the committed `import` dispatch (is the stack
  **at its cap** in those hours?);
* MW of capability **priced out** (offer > node dual) at 22–23, by row;
* the firm RA rows' capability and floor at 22–23 vs their AAH values.

The reading is binary and is registered as such: **capability gap** (the
armed stack is at cap; more import needs more *contracted volume*, a
rule-13 data-intake question — caiso-252 §6.1's object A) versus **price gap**
(armed capability sits idle above λ; and caiso-252 §7 #2 forbids re-pricing
it). Either way this document arms nothing; the point is that the two send a
future session to different places.

A rebuild is not a solve. Its arrays are cross-checked against the committed
sidecar (committed hourly `import` ≤ Σ row capability in every hour) so a
recipe or code drift between the keeper's `git_sha` and HEAD would show as a
violated bound rather than pass silently.

---

## §5a — D-4: the object's C4-2025 exposure (handoff item B, measured not argued)

Share of the 2025 gas-fleet MSE (the scorer's `_cems_gas_hourly_fit`
construction, reproduced by `_caiso252_c4_gas_nrmse_anatomy` G-REPRO) carried
by the 730 hour-slots at hod 22–23; and the NRMSE the cell would read with
those two hours' error set to zero. A direction statement only.

---

## §6 — PREDICTIONS, WRITTEN TO BIND

| # | prediction | uncomfortable reading if it fails |
|---|---|---|
| **P-1** | G-REPRO holds within ±100 MW on all nine numbers | I am not measuring what the record measured; stop |
| **P-2** | the model-side identity closes to < 1 MW in every hour with `import` as a klass | the sidecar's `import` klass is not the net inflow, and every prior "import vs 930" pair in this lane needs re-reading |
| **P-3** | the model's demand at hod 22–23 is BELOW EIA-930 `Demand` by **0.3–2.0 GW** in 2025 (annual mean gap 2.08 GW, mid-day-shaped) | if the night gap is ≥ 2.0 GW the demand basis, not any supply row, is the largest single row in the closure and the object is a demand-basis object before it is anything else |
| **P-4** | `Net generation` − Σ(mapped NG columns) is a **+1.0 to +2.0 GW, diurnally flat** remainder — the geothermal/biomass baseload with no 930 column — and `NG: OTH` does NOT carry it (its 2023 neutrality ratio is 0.005) | geothermal/biomass sit inside a mapped column, that column's Δ is contaminated, and the closure is re-based before any attribution is read |
| **P-5** | after the demand basis is removed, **net import is the largest counterpart** of the CC over-run at 22–23 in 2025, carrying ≥ 60 % of it; storage is same-sign (long), hydro and unmapped each < 400 MW | if hydro or the unmapped remainder is the largest counterpart, the object is a hydro-shape or category object and the import reading is refuted on the closure |
| **P-6** | D-2: ≥ 50 % of the 2025 CC over-run at 22–23 comes from plants that are **ON in reality at lower load** (turn-down), not from plants OFF in reality | a majority from plants OFF in reality makes this a **shutdown/commitment** object — rule 18 territory, not a dispatch-energy object |
| **P-7** | D-3: at hod 22–23 in 2025 the armed import stack is a **capability gap** — committed `import` ≥ 90 % of Σ capability in those hours and < 500 MW of capability priced out | > 500 MW priced out means armed rows sit idle above λ at 22–23, i.e. the model's own stack disagrees with its price there — reported, never re-priced (caiso-252 §7 #2) |
| **P-8** | D-4: hod 22–23 carries **8–16 %** of the 2025 gas MSE; zeroing them would read NRMSE ≈ 0.28 | if it is < 8 % the 22–23 object is small in the C4 cell and the constraint on the next arm is elsewhere in the day |

**No prediction is made about C3a or any determination.** No arm exists to
move one.

---

## §7 — STOP RULE

1. **G-REPRO fails ⇒ STOP** before any new cell is quoted.
2. **G-CLOSE fails on the model side ⇒ the decomposition is re-based** as §2
   says and the failure is the first line of the FINDING; the 930 residual is
   reported whatever it is.
3. **NO ARM IS CODED AND NO SOLVE IS SPENT BY THIS DOCUMENT.** It is a
   diagnostic charter. If the closure names a carrier whose mechanism is
   already registered and admissible, that arm needs its own PRECOMMIT (or an
   ADDENDUM to this one pushed **before any code**) carrying: rule-29(a)'s
   screen year named on the mechanism's own **footprint**, a structural
   STOP-only screen gate with C3a and C4 excluded, the **C4-2025 pre-solve
   check**, G-DRIFT by measurement (`_caiso255_gdrift_identity.py
   --keeper-sha <caiso257 git_sha>`), G-CTRL form 4 with **no control solve**,
   and the §7 solve preconditions of `ADDENDUM-caiso257`. Nothing here
   authorizes it.
4. **No `ScenarioConfig` field is added** (rule 28(c) not engaged); **no
   `complete` marker** is declared (owner act, rule 22 — raised again, never
   granted here); the stale `program-status.json` top-level `isos.CAISO.keeper`
   stamp is **not touched** (owner ask open).
5. **The keeper does not move.** No run is produced, so rule 15 registration
   is not engaged.
6. **A calendar- or season-scoped reading is inadmissible** (caiso-94 §8,
   caiso-253 §7 #2), whatever the monthly structure of the closure shows.
7. **Never a plant-level pin.** D-2 reads Panoche and the LA-basin peakers'
   CEMS conduct as conduct; nothing in it becomes an input (rule 13; the
   caiso-119 R4 guardrail).
8. **`co2` is never differenced** (`import_co2_tons` is the standing LIVE
   hunk; `co2` is not in `CRITERIA`).
9. The three probes hard-coding the pruned `caiso252_b1_notrim` path are
   **not re-used** by this session; the new probe reads `caiso257_ctonly`
   and its own registry id.

---

## §8 — DISCLOSURE: EVERYTHING READ BEFORE THIS PUSH

* The required documents in full (caiso-252, -253, -255b, -256 ×2, -257 +
  ADDENDUM; the caiso.md tail; the keeper shard; the matrix shard header;
  the §5.2 queue prose).
* **Schemas only** of the keeper's sidecars: column names/dtypes, the klass
  list (14 klasses incl. `import`, `OTHER`, `biomass`, `oil`), the tech list
  (`li_ion`, `pumped_storage`), the zone list (five CAISO zones + `WECC_DSW`,
  `WECC_PNW`), the band list, and the **first three rows** of each 2025 file
  (hours 0–2 of NP15 price/demand, CC_CHP hours 0–2, li_ion hours 0–2).
* The EIA-930 loader frame's column list, its 2025 rows for hours 0–2 of
  1 January, and the **per-column NaN counts** for 2023/24/25 — which is how
  `NG: GEO` being NaN all year (8,760 / 8,760 / 8,385) was found.
* `run_config.json`'s `resolved_inputs` block (seam cap `mic_partition`
  16,055 / 16,452 / 16,148 MW; hydro partition present, flag off) and
  `meta.json`'s head.
* The four lane probes named above, read for their constructions.
* `data/clean` is EMPTY at session start (ADDENDUM-caiso257 §7); the two
  curate scripts will be run before D-3's rebuild and nothing else.

**No value at hod 22 or 23 of any series, on any basis, has been read on
`caiso257_ctonly`.** Every published number quoted above is from the record.

---

## §9 — DELIVERABLES

This PRECOMMIT (pushed first); `scripts/probes/_caiso258_hod2223_closure.py`
→ `results/calibration/_caiso258_hod2223_closure.json`;
`FINDING-caiso258-hod2223-closure-2026-09-06.md`; the
`docs/calibration-log/caiso.md` entry; the rule-28 CAISO matrix-shard
**evidence append** (no verdict move — no mechanism is tested) and the
§5.2 queue-item refresh. No bundle, no registration, no keeper change, no
`ScenarioConfig` field, no marker.

**Next number after this session: caiso-259.**
