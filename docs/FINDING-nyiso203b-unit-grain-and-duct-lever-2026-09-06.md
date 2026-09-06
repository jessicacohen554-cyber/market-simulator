# FINDING nyiso-203b — the two open items before a `complete` / `frontier` re-declaration, measured: the **unit-grain C8 breach is real but has narrowed to 2 of 3 years**, and the owner's named duct-tranche lever **bounds at 22 % of its own target**

**Session:** nyiso-203 (`claude/nyiso-nyc-persistent-base-limb-4lrj23`), 2026-09-06.
**Keeper, unchanged: `2026-09-06-nyiso-202-startup-aware`** — CALIBRATED, grade 7/8, fails 0,
C3c the lone ledgered caveat (re-verified this session from committed artifacts,
`scripts/calibration_verdict.py --run-id`, no solve).
**ONE LP spent:** an **identity-verified replay** of the keeper's own recipe, run solely to
recover two gitignored sidecars the committed bundle does not carry. No arm, no screen, no new
mechanism, no `ScenarioConfig` change, nothing registered. **Bundle deleted before merge.**
**Rule 22:** 2023–2025 only; no held-out year touched.
**Machine records:** `_nyiso203_c8_unit_grain.json`, `_nyiso203_duct_lever_disposition.json`,
`_nyiso203_d4_layup_census.json` (all under `results/calibration/`).

**Neither item is a rubric failure.** NYISO reads fails 0. These are the two items standing in
front of an owner re-declaration, and both were open questions rather than defects.

---

## 0. The replay, and why its numbers are the keeper's

`nyiso192_c8_unit_grain.py` needs `hourly/unit_hourly_<year>.parquet` and
`floors/<year>_P1.npz`; both are gitignored, so the committed keeper bundle cannot answer the
question and the nyiso-193 card's measurement necessarily stood on a **superseded** keeper. The
recipe was therefore replayed unchanged
(`run_calibration_full.py --replay-bundle results/calibration/nyiso202_startup_aware`, which
takes every solve kwarg from the bundle) and **verified identical before anything was read off
it**:

| check | result |
|---|---|
| zonal prices, 2023 + 2024 + 2025 | **0 of 157,680 differ**, max abs 0.0 |
| class energy, 14 classes × 3 years | identical to **0.000000 MWh** |

So these are the keeper's numbers, not a near-miss re-solve. The bundle is **deleted before
merge** — every number it produced lives in this document and in the three machine records, and
git history is the record for the bytes (rule 15 `[R-DASHBOARD]`; the registry/payload parity
sweep treats an unregistered bundle dir as a gate RED, so it must not reach `main`).

---

# ITEM 1 — the D-2 unit-grain C8 exposure (nyiso-193 card, UNRULED)

## 1.1 The measurement the card asked for, on the keeper the owner would actually rule on

| year | `ST_GAS` **unit grain** | committed **plant grain** | cap | verdict |
|---|---:|---:|---:|---|
| 2023 | **0.351** (3.5374 TWh) | 0.155 | 0.30 | **BREACH** |
| 2024 | **0.3431** (3.0294 TWh) | 0.199 | 0.30 | **BREACH** |
| 2025 | **0.268** (2.6233 TWh) | 0.172 | 0.30 | pass |

Other classes are clear at unit grain: `CC_REGULAR` 0.0971 / 0.0990 / 0.0981, `CT_PEAKER` 0.000
in all three years, `CC_CHP` 0.2732 / 0.2193 / 0.2072 (and `CC_CHP` is a `d2_exempt_class`).

**The card's premise holds, and the exposure has narrowed.** On the keeper it measured
(`2026-09-05-nyiso-189-steam-identity`) `ST_GAS` read **0.393 / 0.414 / 0.305** — 3 of 3 years
breaching. On the current keeper it is **0.351 / 0.343 / 0.268** — **2 of 3**, with 2025 now
inside the cap. Two promotions of structural repair (the Cricket Valley unit-id-collision fix,
then the bridge's startup-aware run screen) bought that, without either being aimed at it.

The gap between the two instruments is roughly **2×** in every year, exactly the mechanism
nyiso-181 §6 described: `aggregate_floors_by_plant` tests the PLANT total against the PLANT
floor, so a unit pinned at its own floor inside a plant whose other units run freely is above
the plant floor in aggregate and vanishes from the count.

## 1.2 Rule 20's escalation path — and it fails on the leg the card predicted

A material class over the cap is **not** an automatic fail under rule 20 `[R-FORCED-BUDGET]`; it
escalates to a conditional pass on **(a) D-4 off-window provenance** and **(b) D-1 shape**. From
the keeper's own committed `legitimacy_diagnostics.json`:

| leg | gate | result |
|---|---|---|
| (b) shape | `D1.passed` | **True** ✓ |
| (a) provenance | `D4.passed` | **False** ✗ |

So a C8 re-based to unit grain would **FAIL NYISO `ST_GAS` in 2023 and 2024** — the card's
prediction, now confirmed on the current keeper rather than inferred from a superseded one.

## 1.3 But leg (a) is failing on almost no energy — and 3 of its 6 rows are removable today

The six D-4 unit-conduct FAIL rows, at full magnitude:

| year | mechanism | plant | forced TWh | binding h | median MW | zero share |
|---|---|---:|---:|---:|---:|---:|
| 2023 | `reliability_floor × ST_GAS` | **8906** | **0.2271** | 5,400 | 0.0 | 0.521 |
| 2023 | `reliability_floor × ST_GAS` | 2480 | 0.0014 | 153 | 0.0 | 1.000 |
| 2023 | `nyiso_gas_commitment_bridge × ST_GAS` | 8906 | 0.0011 | 34 | 0.0 | 0.559 |
| 2024 | `reliability_floor × ST_GAS` | 2480 | **0.0002** | 23 | 0.0 | 1.000 |
| 2024 | `nyiso_gas_commitment_bridge × CC_REGULAR` | 54574 | 0.0028 | 86 | 0.0 | 0.535 |
| 2025 | `reliability_floor × ST_GAS` | 8006 | 0.0010 | 17 | 0.0 | 0.588 |

**Five of six are trivial** (≤ 0.0028 TWh). The one that is not is Astoria 8906 in 2023, which
this session's companion finding
(`docs/FINDING-nyiso203-nyc-persistent-base-basis-2026-09-06.md`) characterises: its basis is
**sound as built** on window, membership and operator, so no basis change reaches it.

**The sharpest single fact here:** in **2024** — the year with the worse unit-grain breach —
the **only** `ST_GAS` D-4 failure is Danskammer 2480 at **0.0002 TWh**, i.e. **0.007 %** of that
class-year's 3.0294 TWh of unit-grain forced energy. Leg (a) fails 2024 on **200 MWh**.

**And that row, plus 2 of the other 5, sits in a channel that is already armed and already
adjudicated.** `reliability_floor_plant_exclusions` is **True** on this keeper and carries
**exactly one** entry (Port Jefferson 2517, nyiso-140 + owner ruling 2026-08-16). Censusing every
D-4 failing plant against nyiso-140's criterion, from CAMPD conduct alone
(`_nyiso203_d4_layup_census.py`):

| plant | zone | class | zero cells | median MW | online | verdict |
|---|---|---|---:|---:|---:|---|
| Danskammer **2480** | Capital_Hudson | ST_GAS | **12/12** | 0.0 | **0.029** | **QUALIFIES a fortiori** |
| Roseton **8006** | Capital_Hudson | ST_GAS | **12/12** | 0.0 | **0.146** | **QUALIFIES a fortiori** |
| Astoria 8906 | NYC | ST_GAS | 0/12 | 166.0 | 0.704 | does NOT qualify |
| Saranac 54574 | Upstate_West | CC_REGULAR | 9/12 | 0.0 | 0.442 | does NOT qualify |
| *Port Jefferson 2517* | *Long_Island* | *ST_GAS* | *10/12* | *0.0* | *0.386* | *REFERENCE — already excluded* |

The verdict is stated **a fortiori** rather than on a cell count, because the census statistic
here (a per-(year, block) zero-median over raw metered `grossLoad`) is not byte-for-byte
nyiso-140's (a cool-day when-available CF), and 2517 reads 10/12 on mine against 18/18 on
nyiso-201's. The comparison that does not depend on the statistic: **2480 and 8006 have every
cell at a zero median AND are online 2.9 % / 14.6 % of the year, against 38.6 % for the plant
the owner already excluded.** They cannot be closer calls than the adjudicated case. 8906 and
54574 do not qualify on any reading — confirming nyiso-201 §5 a third time.

**What that implies, arithmetically:** excluding 2480 and 8006 removes the 2023 2480 row, the
**2024 2480 row (the only `ST_GAS` D-4 failure that year)** and the 2025 8006 row — leaving
2023's 8906 row as the sole material `ST_GAS` provenance failure, and **zero** `ST_GAS` D-4
failures in 2024 and 2025.

**This is NOT armed, screened or recommended-by-default here.** It is a new arm: it owes its own
PREREG, a rule-29 screen year chosen by its own footprint, and a span — and the D-4 gate is
computed per bundle, so the leg-(a) consequence must be *measured*, not inferred from the row
list. What this finding establishes is only that the cheapest route to leg (a) is a **zero-DOF
membership entry in an already-armed channel under an already-adjudicated criterion**, not new
structure.

## 1.4 What the card still needs from the owner

Unchanged, and this measurement does not decide it: options (A) re-base D-2/C8 to unit grain,
(B) keep plant grain by explicit ruling with the unit-grain number reported alongside, or
(C) measure every ISO first. What is new is that **NYISO's own exposure is now a number on the
current keeper** (2 of 3 years, not 3 of 3), and that its leg-(a) blocker is 200 MWh in the worse
year. Option (C)'s NYISO row is done; the other five ISOs are untouched and remain unmeasured —
this lane may not run them (rule 25 `[R-ISO-SCOPE]`; the instrument is one file scored for six
ISOs).

---

# ITEM 2 — the owner's named duct-tranche lever: does it still have a subject?

`calibration-complete.json`'s `withdrawn.NYISO.reentry` names ONE route back to `complete` — the
owner's ruling in the nyiso-193 promotion sentence, verbatim: *"tune the cc regular offer curve
up for the duct burner peaking tranche because it's merit order is wrong it runs more often at
lower CF and is running hot over 80% CF in all years"* — *"which targets exactly the cell-G
`CC_REGULAR` over-run that took C1-2024 out of band."* nyiso-198 measured against it on a
superseded keeper and stated the numbers "for the owner court, not decided". Re-taken here on
the current keeper, zero LP.

## 2.1 The premise is CORRECT — `CC_REGULAR` does run hot, at plant grain

This is worth stating plainly, because a band-level answer alone would be answering the wrong
question. Model vs actual annual capacity factor, per plant:

| plant | 2023 model / actual | 2024 model / actual | 2025 model / actual |
|---|---|---|---|
| Astoria Energy 55375 | **0.851** / 0.764 | **0.845** / 0.777 | 0.762 / 0.729 |
| Zeltmann 56196 | **0.827** / 0.694 | **0.825** / 0.750 | 0.719 / 0.548 |
| Bethlehem 2539 | 0.607 / 0.557 | 0.759 / 0.465 **(+0.294)** | 0.730 / 0.439 **(+0.291)** |
| Caithness 56234 | **0.801** / 0.778 | 0.608 / 0.585 | 0.774 / 0.754 |

Model CF exceeds 0.80 at **3 / 2 / 1** plants; the actual exceeds it at **0 / 1 / 0**. The
class over-runs its meter in every year, and C1 says so independently: `CC_REGULAR`
**+0.37 TWh (2023)** and **+2.39 TWh / +2.1 pp (2024)**. *(2025 `CC_REGULAR` is SKIPPED by C1 —
preliminary EIA-923 vintage, 45 % plant reporting — so 2025 bears on none of this.)*

## 2.2 But the named tranche is not where that energy is

`CC_REGULAR` band structure on the keeper, capacity and dispatched energy:

| band | capacity | CF 2023 / 2024 / 2025 | energy 2024 |
|---|---:|---|---:|
| `committed` | 3,214–3,219 MW | 0.656 / **0.695** / 0.662 | 19.608 TWh |
| `econc00`–`econc05` (6 tranches) | ~507 MW each | 0.53–0.62 each | ~2.76 TWh each |
| **`peak` (the duct tranche)** | **1,158 MW** | **0.041 / 0.052 / 0.112** | **0.529 TWh** |

No band runs at 80 % CF; the maximum is `committed` at 0.695. **The over-run lives in the
`committed` and `econ` tranches; the peak band carries 1.23 / 1.44 / 3.19 % of class energy.**

## 2.3 The bound — the number the disposition turns on

Raising an offer can displace at most the band's own energy. So:

| | 2023 | 2024 |
|---|---:|---:|
| C1 `CC_REGULAR` over-run | +0.37 TWh | **+2.39 TWh** |
| entire `peak` band energy | 0.412 TWh | **0.529 TWh** |
| **maximum possible closure** | 111 % | **22 %** |

**In 2024 — the year that actually took the marker down — displacing every MWh the duct tranche
dispatches closes at most 22 % of the over-run.** At the withdrawal, when the over-run was
+3.68 TWh, the same bound was **14 %**. The lever cannot reach its own stated target.

## 2.4 And 80.7 % of that band is not duct capability

From EIA-860's own `Duct Burners` attribute, via nyiso-198's committed per-plant row-scoped
percentages: of the 1,158 MW in `CC_REGULAR`'s peak band, only **223 MW** sits on rows the
filing flags duct-capable (CA/CS with `Duct Burners = Y`); **935 MW (80.7 %)** is CT rows, every
one of which reads `X` (not applicable) because a duct burner fires into the HRSG and raises the
STEAM turbine. Their nameplate-vs-summer gap is **site/ambient derate**, not duct capability.
Raising "the duct tranche" offer would therefore mostly raise the offer on ordinary
ambient-derated capacity — the same misclassification `cc_duct_peaking_row_scoped` was built to
repair and was **rejected (R)** for.

## 2.5 Disposition, for the owner court — not decided here

**The diagnosis is right and the named instrument is aimed at the wrong tranche.** The
successor that stays inside the same authorized channel is the `offer_curve_by_group` multiplier
on **`committed` / `econ_low` / `econ_high`** — the bands that actually carry the energy — which
is rule 1 `[R-STRUCT]`'s authorized price-tuning carve-out and would bind every one of its
conditions: (a) band multipliers only, (b) **one config across every scored year**, (c) set
**ex ante in the PREREG and never swept against the gates**, (d) merit-order movement is
intended, (e) declared in `authorized_price_tuning` and carried as a free parameter in the DOF
ledger. This lane states it and does not take it: condition (c) means the value must be declared
before a solve, and that is an owner act, not a lane's.

**Also relevant to whether the lever is still needed at all:** its stated target has already
been met by other means. C1-2024 `CC_REGULAR` was **+3.68 TWh / +3.0 pp** (out of band) at the
withdrawal and is **+2.39 TWh / +2.1 pp** now — inside the ±3.0 pp band by 0.9 pp, on C1 14/14
free 10/10.

---

## 3. What this means for `complete` and `frontier`

**Neither item blocks either marker on the merits.** The withdrawal's stated bar was the Q5
uniform rule — *"a `complete` marker cannot stand on a NOT-YET keeper"* — and the keeper reads
**CALIBRATED, grade 7/8, fails 0**, re-verified this session from committed artifacts. The
`reentry` clause asks for one thing: *"a NEW explicit owner declaration on a designated keeper
that scores CALIBRATED."* The forecast board's gate (a) says the same in terms — *"an OWNER ACT,
not a calibration task."* The `frontier` mechanism-set limb was never retracted
(`ASSESSMENT-nyiso192` §4); only the determination limb fell, and the determination is CALIBRATED
again. Card **C-19 / Q51** has been ruled HOLD twice and is **PARKED at owner direction** as of
capx refresh #46; its re-serve condition (*"nyiso-197 lands AND the keeper is CALIBRATED"*) is
**met**.

What the two measurements change is the **risk picture**, which is what a fourth withdrawal
would turn on:

1. **The unit-grain exposure is real but shrinking and now bounded**: 2 of 3 years, not 3 of 3,
   and the leg-(a) blocker in the worse year is 200 MWh at a plant that qualifies a fortiori for
   an already-armed, already-adjudicated exclusion channel. The card stays the owner's to rule.
2. **The named route back is aimed at the wrong tranche and its target is already met.** Ruling
   it moot explicitly — rather than leaving a `reentry` clause pointing at a lever that bounds at
   22 % — would remove the only thing that reads like an unmet precondition.

---

## 4. Disposition

**KEEPER UNCHANGED: `2026-09-06-nyiso-202-startup-aware`.** No arm, no `ScenarioConfig` field, no
coefficient edit, no scorer change, nothing registered — the replay bundle is deleted before
merge and no run exists to register. No marker was edited: `complete` and `frontier` re-entry are
owner acts and this lane does not take them. The NYISO matrix shard is re-stamped in this session
per rule 26 `[R-MECH-MATRIX]` duty (b).

*(nyiso-203b, 2026-09-06. One identity-verified keeper replay, deleted before merge; three
zero-LP measurements. Both items answered; both dispositions left where they belong.)*
