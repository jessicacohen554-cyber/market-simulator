# PRECOMMIT — caiso-255b: caiso-253 re-pointed the hod 22–23 gap from IMPORT to STORAGE. **Before that re-pointing can carry any weight, its instrument has to survive: is EIA-930 `NG: OTH` actually CAISO's battery fleet?** A ZERO-LP charter whose FIRST gate can kill the whole object.

**Session caiso-255 (second object), 2026-09-06.** Branch
`claude/caiso-backcast-calibration-x5v8uq`. Keeper
**`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`, `git_sha`
`fa23c1f7`) UNCHANGED, DETERMINATION **CALIBRATED**. Rule 22 `[R-HOLDOUT]`:
2023–2025 only; CAISO holds no `complete`/`final` marker; the holdout spend
freeze is ACTIVE.

**Pushed BEFORE any cell of the object is computed.** Only the *schemas* of the
keeper's committed hourlies and of the EIA-930 CISO frame have been read
(column names and row counts) — no value at hod 22–23, no storage series, and
no gap.

---

## §0 — WHY THIS OBJECT, AND WHY NOW

The granted partition object (`PRECOMMIT-caiso255-ct-only-partition-adoption`)
is **PARKED, not abandoned**: the owner stopped the OASIS re-fetch at
**336 / 1,096** trade dates. That corpus is unusable by construction —
`FINDING-caiso254 §6` DO-NOT-REDO #1 forbids scoring G-BIMODAL on a partial
corpus, because a 2023-only population returned the **opposite verdict**
(antimode 11.357, 4.93 GW, FAIL). Nothing about the grant is withdrawn and
nothing about it is spent; it resumes when a full corpus exists. **§7 records
exactly what a resuming session inherits.**

This object is the **ranked-first** open CAISO item and needs **no OASIS data at
all** (caiso-253 queue item 1, `docs/calibration-log/caiso.md`):

> the 22–23 gap is **RE-NAMED and DEMOTED as an import object** and re-pointed at
> **STORAGE** — EIA-930 `NG: OTH` at 22–23 rises 274 → 2,112 → 3,342 MW against
> the keeper's ~680 → 1,683 → 2,769 MW of storage discharge (a hypothesis with a
> named check; **EIA-930 carries no battery category**), corroborated by
> caiso-252's own P-A2 falsification.

Everything it needs is committed: the keeper's `hourly/storage_*.parquet`,
`class_hourly_*.parquet` and `system_*.parquet` for all three years, and
`data/raw/eia-930-hourly/CISO hourly.parquet`.

### §0.1 — What is actually at stake

The model's `CC_REGULAR` **over-runs +1,547 / +1,558 MW at hod 22 / 23** in 2025
— the two largest CC error hours of the day (caiso-253 G-REPRO, reproduced from
the keeper). caiso-253 refused the import arm on **admissibility**, not on
absence: the row would have cleared in **54–59 %** of those hours. So the energy
is real and something covers it in the actual market. If that something is
battery discharge the model does not produce, the CC over-run is a **storage**
defect — and the offer-side and import-side lanes have both been chasing it in
the wrong place.

---

## §1 — THE LOAD-BEARING GATE: `NG: OTH` IS A RESIDUAL CATEGORY, AND IT MUST EARN ITS IDENTIFICATION

caiso-253's own parenthesis — *"EIA-930 carries no battery category"* — is the
whole problem. `NG: OTH` is EIA-930's **catch-all**, and reading it as "CAISO's
batteries" is an **inference**, not a measurement. If it is wrong, every number
downstream of it is measuring something else, and the "storage" re-pointing is
a mis-named object rather than a demoted one.

**G-ID is therefore scored FIRST and it can end the session.** Three
discriminators, all fixed here, none of them a residual and none of them a
price:

* **G-ID-1 — SIGN. The decisive leg.** A battery fleet is a *load* in the solar
  belly and a *source* in the evening. So `NG: OTH` must go **NEGATIVE** in
  hours 10–15 in at least the largest-fleet year (2025). **A series that never
  goes negative is not a battery series**, and G-ID fails on this leg alone
  however well the other two look.
* **G-ID-2 — GROWTH.** CAISO's battery fleet roughly **doubled then doubled
  again** across 2023–2025. `NG: OTH`'s annual gross throughput must grow
  monotonically 2023 → 2024 → 2025. A flat or shrinking series is some other
  residual.
* **G-ID-3 — ENERGY NEUTRALITY.** A battery is an energy-*moving* device, not an
  energy-*making* one. Annual **net** `NG: OTH` energy must be small against its
  annual **gross** throughput: `|Σ net| / Σ |NG: OTH|` ≤ **0.35**. A large
  positive net is generation (biomass, "other" thermal), not storage.

**G-ID FAILS ⇒ the re-pointing is REFUSED on its own instrument.** The session
reports which leg failed, closes the storage reading of the 22–23 gap the way
caiso-253 closed the window question, and **nothing is armed**. That is a real
and registered outcome, not a fallback.

---

## §2 — G-FLEET: IS THE GAP A DISPATCH DEFECT OR A FLEET DEFECT? (different object, different owner)

Only if G-ID passes. Compare the **model's own installed storage power
capacity**, per year, against the fleet `NG: OTH`'s magnitude implies.

This leg exists because the two answers demand *opposite* repairs and are
trivially confusable:

* the model's storage fleet is **short** ⇒ the gap is an **INPUT** problem
  (`storage_measured_base_fleet` / the base-year fleet), and no dispatch
  mechanism can close it. Rule 14 `[R-ACCURATE]` territory.
* the model's storage fleet is **right** but sits idle at 22–23 ⇒ the gap is a
  **DISPATCH** problem (arbitrage value, SOC binding, the ε tiebreaker, an AS
  reservation), which is a mechanism object.

**Registering the confusion in advance is the point:** a session that measured
only the discharge gap would call a fleet shortfall a dispatch defect and go
looking for a mechanism that cannot exist.

---

## §3 — G-GAP: the gap itself, and the SIGN FLIP already visible in the published numbers

Only if G-ID passes. Per year, over hod 22–23, model storage **net** discharge
(`discharge_mw − charge_mw`, P1) against `NG: OTH`.

caiso-253's own published pair is **680 → 1,683 → 2,769 MW model** against
**274 → 2,112 → 3,342 MW actual**. Read plainly, that is the model
**OVER**-discharging in 2023 and **UNDER**-discharging in 2024 and 2025 — a
**sign flip**, not a one-directional shortfall. I register **now**, before
re-measuring, that a sign flip is **hostile** to the simple story: a single
mechanism that adds evening discharge would make 2023 worse. Any arm this object
ever proposes must explain the flip, and **no arm is proposed in this document.**

---

## §4 — G-ENERGY: are the CC over-run and the storage gap THE SAME ENERGY?

Only if G-ID passes. The claim implicit in the re-pointing is that the model
covers with CC what the market covers with batteries. That is testable and it is
not automatic: the model could be over-running CC *and* under-discharging
storage for unrelated reasons, and the two would then merely co-occur.

Scored at hod 22–23, per year: is the CC_REGULAR error the **mirror** of the
storage gap — opposite sign, and within a factor of **2** in magnitude? If the
CC over-run is much larger than the storage gap, storage is at most a *part* of
the object and the rest is still unexplained. **The honest answer may be
"partly", and this gate is built to say so** rather than to return a verdict.

---

## §5 — PREDICTIONS, WRITTEN TO BIND

| # | prediction | uncomfortable reading if it fails |
|---|---|---|
| **P-1** | **G-ID-1**: `NG: OTH` goes NEGATIVE in hours 10–15 in 2025 | it is not a battery series, the re-pointing is mis-named, and caiso-253's queue item 1 is refused on its own instrument |
| **P-2** | the instrument reproduces caiso-253's published pair to **±5 %**: `NG: OTH` 22–23 = 274 / 2,112 / 3,342 MW and keeper storage = 680 / 1,683 / 2,769 MW | I am not measuring what caiso-253 measured, and nothing downstream is comparable — stop |
| **P-3** | **G-ID-2 and G-ID-3 both pass** — throughput grows monotonically and `\|net\|/gross` ≤ 0.35 | a growing-but-not-neutral series is probably a mix, and no clean read is available from EIA-930 alone |
| **P-4** | **the sign flip is real**: the model OVER-discharges at 22–23 in 2023 and UNDER-discharges in 2024/2025 | if 2023 is actually short too, §3's warning was wrong and the object is simpler than I registered |
| **P-5** | **G-FLEET**: the model's storage fleet is NOT materially short — the gap is dispatch-side, not fleet-side | a short fleet moves this object out of the mechanism lane entirely and into a measured-input repair |
| **P-6** | **G-ENERGY**: the 22–23 CC over-run and the storage gap are opposite in sign and within a factor of 2 in 2025 | they are not the same energy, and storage is at most a fraction of the 22–23 object |

**No prediction is made about C3a, C4, or any rubric criterion.** This document
proposes no arm, so there is no residual it could move.

---

## §6 — STOP RULE

1. **G-ID failing on ANY leg ⇒ the storage re-pointing is refused and the
   session closes the object.** Nothing measured downstream of a failed
   identification is quoted.
2. **P-2 failing ⇒ stop.** An instrument that cannot reproduce the published
   pair is not one I may extend.
3. **NO ARM IS CODED AND NO SOLVE IS SPENT BY THIS DOCUMENT.** It is a
   diagnostic charter. Any mechanism it motivates needs its own PRECOMMIT, its
   own rule-29 `[R-SCREEN]` screen and its own G-DRIFT — none of which this
   document authorizes.
4. **No `ScenarioConfig` field is added**, so rule 28(c) is not engaged.
5. **No `complete` marker is declared** (owner act, rule 22 — raised, never
   granted here), and
   `frontend/data/forecast/program-status.json`'s stale top-level
   `isos.CAISO.keeper` stamp is **not touched** (owner ask open).
6. **The keeper does not move.** No registration follows from this object,
   because no run is produced (rule 15 is not engaged).
7. **A calendar- or season-scoped reading is inadmissible** (caiso-94 §8,
   re-affirmed by caiso-253 DO-NOT-REDO), whatever the monthly structure shows.

---

## §7 — WHAT THE PARKED PARTITION OBJECT LEAVES FOR A RESUMING SESSION

Recorded here so the grant is not lost with this container:

* **The owner's grant of FINDING-caiso254 §4 OPTION 1 STANDS**, pre-registered
  in `PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md` (merged).
* `--st-split-report-only` is **implemented and merged** (`f721b582`): three-way
  classification, two-way consumption, ST_GAS published under
  `_provenance.reported_not_consumed` with its G4 FAIL verbatim.
* The **consolidated G-DRIFT audit** is merged (`9c921d91`) and is now
  **re-runnable in one command** — `scripts/probes/_caiso255_gdrift_identity.py`,
  written this session, reproduces all three instruments against any HEAD and
  exits non-zero if the LP inputs diverge.
* The **phase-0 instrument defect is fixed and merged** (`d2f914d2`): the probe
  swapped one artifact where the keeper consumes two, so arm B was a hybrid and
  the footprint was blind to the P1 channel. Both artifacts now swap together;
  `argmax_y F` on the REGISTERED statistic still names the screen year, with
  `F_p1` reported beside it and any divergence recorded as a power caveat.
* **What remains** is exactly: re-fetch the full 1,095/1,096-day corpus
  (~110 min at OASIS's 6 s rate limit), `--pass1` the reduced store (~7 min),
  run the derive, then phase 0 → screen → the 2023–2025 bundle.
* **ZERO LP has been spent on the partition object**, in this session or in the
  one before it.
