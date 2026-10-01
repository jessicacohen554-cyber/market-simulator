# FF-G5 — nuclear fleet forward-lifetime registry: session record + forward-channel design memo

**Date:** 2026-07-20 · **Session:** FF-G5 [OPUS] (lane L-INP, coordinates L-CAP)
· **Branch:** `claude/nuclear-license-status-registry-0qadkf` · **Scope:** deep-
research grounding — build the registry + design the forward channel. **No
mechanism code, no ScenarioConfig field, no constants.py value, zero LP solves.**
Companion: `docs/nuclear-fleet-forward-methodology-2026-07.md` (sources, per-ISO
tables, SLR census, field survey, maintenance rules).

## 1. What shipped (session record)

New datatype `nuclear-license-status` (data-intake skill, end to end):

- **Schema** `data/dictionary/schema/nuclear-license-status.schema.yaml` — one row
  per unit; keyed `(iso, eia_plant_id, unit)`; four closed vocabularies
  (`license_stage`, `slr_status`, `uprate_status`, `restart_status`).
- **Raw registry** `data/raw/nuclear-license-status/<iso>.csv` — **59 units**
  (CAISO 2, ERCOT 4, NEISO 3, MISO 14, NYISO 4, PJM 32), every date carrying a
  primary NRC/state/licensee instrument citation. `README.md` (per-source table +
  sha256 pins + re-query list), `md/` snapshots (NRC SLR status, expected-uprate,
  approved-uprate — sha256-pinned).
- **Registry lib** `scripts/lib/nuclear_license_status/` (`IsoSpec` + `register` +
  generic parser + four-vocabulary `validate_tidy`, one module per ISO — no
  if-iso ladders), mirroring `scripts/lib/confirmed_retirements`.
- **Curate** `scripts/data/curate_nuclear_license_status.py` — EIA-860 spine
  validation (identity + MW within 5 %); registered in `regenerate_clean.py`
  DATATYPES and `render_data_dictionary.py` (data-dictionary re-rendered).
- **Fetch** `scripts/data/fetch_nuclear_license_status.py` — re-queries the four
  consolidated NRC pages, prints sha256 (living pages; md/ snapshots are the
  pinned artifacts).
- **Read-only loader stub** `src/market_sim/data/nuclear_license.py` —
  `load_nuclear_license_status(iso) -> list[NuclearUnitStatus]`. **Nothing in the
  solve path consumes it** (this session's hard constraint); the stub exists so
  the implementing session and its tests have a stable seam.
- **Tests** `tests/test_curate_nuclear_license_status.py` — 10 tests, curate +
  loader round-trip, spine cross-check, vocabulary + SLR/stage-consistency
  failures, tmp-CLEAN_DIR pattern. All green.

Headline data facts (full tables in the methodology doc):
- **11 SLR-granted** (→80 yr): Monticello, Point Beach 1-2, Dresden 2-3, North
  Anna 1-2, Peach Bottom 2-3, Surry 1-2 — mostly expiring 2049–2060, i.e. **past
  the 2050 horizon**.
- **2 SLR under review** (NMP1, Ginna); **2 announced intent** (Palisades, Crane).
- **2 on original license** (Clinton 2027, Perry 2026 — initial renewals pending).
- **44 with no SLR pathway yet**, but most `renewed_60` with expiries 2032–2053.
- **2 restarts** in progress (Palisades → 2026; Crane/TMI-1 → 2027).
- **Diablo Canyon** is the only nuclear unit in `confirmed-retirements` (SB 846
  state ceiling) — cross-referenced here via `confirmed_retirement_ref`, **not
  duplicated**.

## 2. The forward-channel design memo

**Problem.** How should a nuclear unit's licensed life enter the forecast, given
rule 19 (ONE mechanism per phenomenon) and the three exit mechanisms already in
the model: (a) the confirmed-exit channel (`apply_confirmed_exits`, registry-
driven, instrument-dated, bypasses the reliability floor); (b)
`apply_announced_retirements` (honors a dated non-fossil EIA-860 retirement within
`EIA860_OPERABLE_VINTAGE + NONFOSSIL_ANNOUNCED_HORIZON_YEARS` ≈ 2030); (c) the
economic-retirement screen.

### 2.1 The phenomenon, named

A nuclear unit's **licensed-life ceiling** is a *distinct phenomenon* from both a
binding early-exit instrument and economic death:

- It is a **ceiling** (the latest date the unit may legally operate), not a
  decision to retire. Empirically, healthy units file SLR and continue — 11 of 59
  are already SLR-granted, actual nuclear retirements in the modeled ISOs are ~0,
  and two shut units are restarting.
- It is **not** a confirmed exit (channel a). A consent decree / statute /
  deactivation forces a unit *off before* its license end (Diablo Canyon). A bare
  license expiry with a live SLR pathway forces nothing.
- It is **not** economic death (channel c), which BLK-9 shows the model currently
  gets backwards for nuclear.

By rule 19, the license ceiling wants ONE well-defined home — not a fourth ad-hoc
floor, and not conflated into (a) or (c).

### 2.2 The three options, evaluated

**(i) Fold no-SLR-pathway expiries into the confirmed-exit channel.**
*Rejected as the base mechanism.* The confirmed channel force-retires at an
instrument date and bypasses the reliability floor — correct for a consent decree,
wrong for a license clock, because a license expiry with a live SLR pathway is
*not* a decision to exit. Folding renewed_60 units (expiries 2032–2040) into
confirmed-exits would force-retire units that in reality overwhelmingly renew —
over-retirement with no forward analogue (fails rule 13's "responds to changed
conditions": it wouldn't respond to an SLR grant). The confirmed channel's closed
`confirmation_class` vocab (rto_deactivation/consent_decree/statute/
regulatory_order/rmr_end) also has no member for "license expiry," by design. The
genuinely-binding subset — a license that will *not* be renewed because a statute
caps it (Diablo Canyon) or the licensee has filed a no-renewal instrument —
already belongs in `confirmed-retirements` and is handled there.

**(ii) A separate license-horizon input consumed by the announced channel.**
*Adopted as the mechanism LOCATION.* `apply_announced_retirements` already IS "the
one place a dated, non-economic, non-fossil retirement lives," gated by a
credibility horizon. The registry's license expiry is a strictly *better-grounded*
version of the very signal that step consumes: an **NRC instrument** instead of an
EIA-860 self-report. The horizon gate (vintage+5 ≈ 2030) exists precisely because
self-reported dates are speculative past ~2030 (constants.py comment); an NRC
license date is **not** speculative, so the registry both (a) replaces the EIA-860
self-report as the nuclear input to this step and (b) *justifies lifting the
horizon gate for nuclear*, because the reason for the gate (speculation) does not
apply to an instrument. This is the rule-19-clean move: upgrade the existing
step's nuclear input, don't add a mechanism.

**(iii) License expiry as an upper bound, economic screen governs earlier exit.**
*Adopted as the SEMANTICS.* The license clock is a **ceiling**: nuclear runs until
the *earlier* of (economic death, license end), and SLR *extends* the ceiling —
`exit = min(economic_exit, license_ceiling)`, exactly symmetric to how the
confirmed channel composes `min(economic, confirmed_date)`. This is the most
physically faithful representation and the field consensus (§2.4).

**Synthesis (recommended): (iii) semantics, located in (ii)'s home.** Implement
the nuclear license ceiling *inside* the announced-retirement step, with the
registry replacing the EIA-860 self-report for nuclear and the horizon gate lifted
for nuclear (because the date is now instrument-grounded), and **ceiling**
semantics (a latest-exit bound, not a deterministic force-retire) so the economic
screen still governs any earlier exit and SLR extends the bound. Confirmed early
exits stay in (a). This adds **zero new mechanisms** — it upgrades one input and
sharpens one step's semantics.

### 2.3 Where restarts and uprates enter

- **Restarts ≈ planned-additions channel.** A restart is a return-to-service with
  an instrument-gated COD — the exact shape of `load_planned_additions`' U/V/TS
  construction-committed additions. Recommend: a restart-pathway unit enters as a
  planned addition with COD = `restart_target_year`, gated on the restart
  instrument (Palisades → 2026, NRC reauthorization; Crane → 2027, NRC CCEC
  review). This reuses the additions machinery (one mechanism per phenomenon) and
  is forecast-forward by construction. Until wired, these units' EIA-860 status
  (Palisades `OA`) already keeps them near-fleet; the registry makes the COD
  explicit and instrument-dated.
- **Uprates ≈ capacity derate in reverse.** An approved uprate raises `pmax`/
  nameplate at the amendment date. Recommend: a `announced_uprate_mw` with an
  approved instrument applies as a positive capacity step at the approval date.
  **Deferred in practice:** the NRC Expected-Uprate list publishes **no per-unit
  MW**, so `announced_uprate_mw` is currently blank fleet-wide (the six PJM rows
  are `announced_intent`, MW DATA NEEDED). Base case = no forward uprate until the
  MW lands; this is a small effect (the fleet is already largely uprated — the
  historical NRC approved-uprate list is in EIA-860 nameplate).

### 2.4 Field-survey grounding (detail in methodology §6)

EIA AEO/EMM (life extension, now the 40→60→80 SLR ladder), NREL ReEDS (60–80-yr
age-based lifetime, 80 yr in decarbonization analyses), and EPA IPM (license-
renewal-aware) all treat a US nuclear unit's default forward life as its **NRC
license clock**, not an economic-retirement outcome. That is direct support for
ceiling semantics (iii) with the economic screen as an accelerant only.

### 2.5 Reconciliation with BLK-9 (must-read)

BLK-9 (`gap-register` §3.9) is that the **economic screen is inverted against
nuclear** — the flat capacity payment clears FOM for every fossil class but leaves
nuclear the only class below 1.0×, so the PJM hindcast false-retired 4.1 GW of
nuclear (100 % false). **This registry does NOT fix BLK-9 and must never be used to
hide it.** A license ceiling only stops nuclear living *past* its license; it does
nothing to stop the economic screen killing a healthy unit *early*. So:

- The load-bearing fix is BLK-9 itself — the capacity-revenue accreditation chain
  (BLK-3 + BLK-4), owned by **L-CAP**, *never a payment haircut* (rule 13).
- The license ceiling is **necessary but not sufficient**: enable it *with or
  after* the BLK-9 fix, never as a substitute. If the ceiling were switched on
  while the screen is still inverted, nuclear would still false-retire
  economically before its ceiling — the ceiling would mask nothing and fix
  nothing. Sequencing is an owner decision (DB-5).
- **Rule 1/11 guard:** do not tune the ceiling, or the base-case SLR assumption,
  to move the nuclear-retirement residual. The ceiling is the published NRC basis;
  the residual is closed by fixing the screen, not by bending the ceiling.

### 2.6 R5c precedent (cited)

R5c (`gap-register` §3.10; `docs/handoffs/ff-2b-adequacy-basis-2026-07.md`) found
conventional hydro **excluded** from the accredited-supply ledger and fixed it by
passing the model's own hydro capability into `accredited_firm_capacity_mw` **at
each ISO's published RA accreditation basis** (CPUC QC / NYISO CAF / ISO-NE QC),
mirroring wind/solar — a clean-firm resource entering the forward accounting *on
its own published basis*, not a generic guess and not a residual-tuned value. The
nuclear license clock is the direct analogue: the **NRC license is nuclear's
published forward-life basis**, exactly as CPUC QC is hydro's published RA basis.
The registry brings nuclear lifetime into the forward accounting on its published
instrument basis — the same move R5c made for hydro accreditation, applied to
nuclear lifetime. And, like R5c (which left CAISO/NYISO base-year I7 FAIL rather
than over-credit — rule 1/11), this registry must not over-reach into the BLK-9
economic-screen fix that isn't its charter.

## 3. Owner-decision boxes

> **DB-1 — Primary mechanism.** Adopt the synthesis: **ceiling semantics (iii)
> located in the announced-retirement step (ii)** — the registry replaces the
> EIA-860 self-report as the nuclear lifetime input, the horizon gate is lifted for
> nuclear (instrument-grounded), the license expiry is a latest-exit bound (not a
> force-retire), the economic screen governs earlier exit, SLR extends the bound,
> and confirmed early exits stay in `confirmed-retirements`. **Recommended.**
> Alternatives: pure (i) confirmed-channel fold (rejected — over-retires renewing
> units); pure deterministic honor-the-date (over-retires; ignores SLR).

> **DB-2 — Base-case SLR assumption (the key modeling decision).** For a
> `renewed_60` unit whose 60-yr expiry falls in 2026–2050 with
> `slr_status ∈ {none, under_review, announced_intent}`, does the base case assume
> SLR (ceiling → 80 yr) or not (ceiling = 60 yr)?
> **Recommended: assume-SLR / 80-yr default**, per-unit overridable, because the
> industry trend is overwhelming (11/59 already granted, 4 in-flight, ~0 actual
> retirements, restarts happening) and it matches AEO/ReEDS. The **no-further-SLR /
> retire-at-60** case becomes the downside scenario. (This choice is a scenario
> knob, not a tuned value — it must not be set to fit a residual, rule 1.)

> **DB-3 — Restart channel.** Route restarts (Palisades → 2026, Crane → 2027)
> through the **planned-additions channel** with COD = `restart_target_year`,
> instrument-gated. **Recommended.** Alternative: a bespoke restart step (rejected
> — duplicates additions machinery, violates rule 19).

> **DB-4 — Uprate channel.** Apply an approved uprate as a positive capacity step
> at the amendment date. **Deferred in practice** — the NRC Expected-Uprate list
> has no per-unit MW, so base case = no forward uprate until the MW lands (small
> effect; fleet already largely uprated). Decision: confirm defer, or authorize a
> per-licensee MW research pass.

> **DB-5 — Sequencing vs BLK-9.** The license ceiling is necessary-not-sufficient
> and must be enabled **with or after** the BLK-9 economic-screen fix (L-CAP), never
> as a substitute or a residual mask. **Recommended: gate it default-off and do not
> promote a keeper that relies on it until BLK-9 lands.** Decision: confirm the
> ordering and the default-off gate.

> **DB-6 — Config surface.** A single `ScenarioConfig` gate (e.g.
> `nuclear_license_ceiling_enabled`, default off) + the clean path, mirroring
> `confirmed_exits_enabled` — no other knob (rule 24). The base-case SLR assumption
> (DB-2) is a second field (e.g. `nuclear_slr_base_case ∈ {assume, none}`).
> **Recommended.** Decision: confirm the two-field surface.

The implementing session is chartered from DB-1…DB-6 once resolved. It will add the
mechanism (announced-step nuclear ceiling + additions-channel restarts), the
ScenarioConfig field(s), tests (unit retires at ceiling; SLR extends; economic
screen still accelerates; restart COD; default-off byte-identity), and a
leave-one-year-out score within 2023–2025 for any verdict-flipping change (rule
17/22) — **after** or **with** BLK-9.

## 3a. Landing note — three large-file edits DEFERRED to a safe channel (push-integrity)

`mcp__github__push_files` (the only sanctioned push path — `git push` 413s) takes
full file **content**, so landing a change to a large existing file means replacing
its entire content. Three edits this session touch large existing files:
`CHANGELOG.md` (4566 lines), `scripts/render_data_dictionary.py` (1234),
`data/dictionary/data-dictionary.md` (1679, generated). Hand-reconstructing a
full-file rewrite of a 4566/1679/1234-line file whose prior content I do not hold
verbatim is exactly the rule-16 truncation hazard (the incident that clipped
`constants.py` 6,368→33 lines). **So these three edits were made locally but NOT
pushed** — pushing them safely needs a channel that transfers the exact on-disk
bytes (a local `git`/editor apply, or the owner running the one command below),
not an API full-content rewrite. All FUNCTIONAL and DATA deliverables (schema, raw
registry, lib, curate, fetch, loader, tests, methodology + this handoff) and the
small `scripts/regenerate_clean.py` registration ARE pushed. The follow-ups:

1. **`scripts/render_data_dictionary.py`** — register the datatype (already done
   locally): add `"nuclear-license-status"` to `DATATYPE_ORDER` (after
   `"confirmed-retirements"`) and its `{summary, reconciles}` metadata block, then
   run `python scripts/render_data_dictionary.py` to regenerate
   `data/dictionary/data-dictionary.md`. Until this lands,
   `test_data_dictionary_sync::test_every_schema_has_a_section` and
   `::test_coverage_matrix_lists_every_datatype` list `nuclear-license-status`
   among the (already 4-datatype pre-existing) mismatches — a documented cosmetic
   consequence in an already-74-red suite, not a new CI-gate failure.
2. **`CHANGELOG.md`** — prepend the entry (verbatim block below):

```markdown
## 2026-07-20 — Nuclear fleet forward-lifetime registry (FF-G5): new `nuclear-license-status` datatype + forward-channel design memo

Grounds 2035–2050 clean-firm supply. **Data + design only — no mechanism code, no
ScenarioConfig field, no constants.py value, zero LP solves; solve output
byte-identical** (nothing in the solve path consumes the registry yet). Full
methodology + per-ISO tables: `docs/nuclear-fleet-forward-methodology-2026-07.md`;
session record + design memo + owner-decision boxes:
`docs/handoffs/ff-g5-nuclear-registry-2026-07.md`.

- New raw datatype `data/raw/nuclear-license-status/` — one row per operating (or
  restart-pathway) power reactor unit in the six modeled ISOs (59 units), NRC
  license expiry + stage (original / renewed_60 / slr_granted_80), SLR status,
  announced uprate, restart pathway, and `confirmed_retirement_ref` cross-ref
  (Diablo Canyon's SB 846 exit stays in `confirmed-retirements`). Primary NRC /
  state / licensee citations (rule 13); README + sha256 + `md/` snapshots + fetch
  script.
- Schema, per-ISO intake lib, curate (EIA-860 spine ±5% MW), read-only loader stub
  `data.nuclear_license.load_nuclear_license_status` (no solve-path consumer yet),
  10-test suite. Registered in `regenerate_clean.py` + `render_data_dictionary.py`.
- Design memo: nuclear license expiry as a **ceiling** on unit life (SLR extends
  it), in the announced-retirement step; restarts via planned-additions; uprates as
  reverse-derate (deferred, no per-unit MW). Reconciled with BLK-9 (necessary-not-
  sufficient; never masks the inverted economic screen — that's L-CAP) and the R5c
  precedent. Six owner-decision boxes.
```

The `CHANGELOG.md` bullet in the design-memo body and §5 assume this entry lands;
it is authored and staged, pending the safe apply.

## 4. Doc-status note (per task instruction)

The FF plan **§1.2-11 frontier row** and gap-register **§3.11 FF-G5 row** — which
the task says "both landed 2026-07-19 via the FF-G1 core-wiring patch" — are
**ABSENT on `origin/main`** at this session's base (gap-register ends at §3.10;
`docs/forecast-development-plan-2026-07.md` has no FF-G5 / §1.2-11 entry; the
FF-G1 patch is present only as `docs/handoffs/patches/ff-g1-core-wiring.patch`, not
applied to the live docs). Per the task's explicit instruction ("if absent on
main, note in your handoff — do not create them"), I did **not** create §3.11 or
the frontier row. When the FF-G1 patch lands, the FF-G5 row status should be
updated to reflect this registry + design memo (data + design DONE; mechanism
chartered to a follow-up). I did not edit
`docs/handoffs/ff-wave-manager-ledger-2026-07.md` (manager-owned).

## 5. Verification

- `tests/test_curate_nuclear_license_status.py` — 10/10 green (curate + loader
  round-trip, spine cross-check, four-vocabulary + SLR/stage-consistency failures).
- Curate against the real EIA-860 spine: all 59 rows pass identity + MW-within-5 %.
- Full pytest (4571 passed, 16 skipped, 7 xfailed, 61 xpassed; **74 failed, all
  pre-existing and unrelated**): the failures span seven modules —
  `test_runner`, `test_soundness`, `test_storage_metric_payload`,
  `test_structural_prior`, `test_transmission_expansion`, and the two
  set-difference-drift assertions `test_data_dictionary_sync::test_every_schema_has_a_section`
  and `test_clean_io::TestRegenerateEntrypoint::test_datatype_list_matches_schemas`.
  **Zero involve nuclear-license-status**, and none are in a module that a new
  raw-data datatype + read-only loader stub could touch. The two drift assertions
  concern four UNRELATED datatypes (pjm-outages, lmp-components,
  transmission-expansion, dam-public-bids) whose schemas exist on `HEAD` and are
  absent from `DATATYPE_ORDER`/`DATATYPES`; my edit adds only
  `nuclear-license-status`, symmetrically to both the schema set and the registered
  lists, so the offending set difference is unchanged (`nuclear-license-status` is
  correctly present in every list). The `nuclear-license-status`,
  confirmed-retirements, and clean_io suites are otherwise green.
- **Byte-identity is trivial: nothing in the solve path consumes the registry**
  (this session shipped data + a read-only loader stub only), so no solve output
  can change. Stated explicitly per the task.
