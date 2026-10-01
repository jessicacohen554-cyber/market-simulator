# ASSESSMENT — neiso-98: the frontier and `complete` declarations re-verified on the neiso-97 keeper's OWN artifacts

**Date:** 2026-08-17 · **Session:** neiso-98 · **Branch:** `claude/neiso-98-frontier-verification-vy6u5x`
(off `origin/main` @ `7d127a8`) · **Keeper UNCHANGED:** `2026-08-17-neiso-97-dstrepair`
**NO LP CONSTRUCTED. NO RUN PRODUCED. NOTHING REGISTERED.** Committed artifacts only —
the neiso-95 pattern applied to the neiso-97 keeper.

**Rule 22 `[R-HOLDOUT]` posture:** the holdout spend freeze is **ACTIVE** at HEAD and was
**never engaged**. No year of any tier was solved, scored or registered. `holdout-freeze.json`
and `calibration-complete.json` are **unedited**. The only 2019–2022 reads are of **measured
input series with no model side** — unrestricted under rule 22 as amended 2026-08-06 ("what is
held out is the SCORE, never the DATA"). NEISO's locked test remains **NEVER GRANTED and NEVER
SPENT**.

**Instruments** (all committed with their JSON records):
`scripts/probes/neiso98_declaration_recheck.py` → `_neiso98_declaration_recheck.json` ·
`scripts/probes/neiso98_escalations_and_final_readiness.py` → `_neiso98_escalations.json` ·
`scripts/probes/neiso98_scored_pass_identity.py` → `_neiso98_scored_pass_identity.json`.

---

## Verdict in one line

**The 2026-07-11 frontier declaration and the `complete` marker's determination both hold, now
established DIRECTLY on the current keeper's own committed bytes rather than transitively; the
`final` answer is still NOT YET on the merits and nothing is granted; and a fourth measurement
sharpens audit row O5 — NEISO is not merely RUNNING the archived P2 pass, it is SCORED on it.**

---

## 1. `frontier` — RE-ESTABLISHED on the keeper's own sidecars, closing the transitive loop

neiso-97 re-verified the declaration **by measured bit-identity** to the superseded
`2026-08-14-neiso-93-envelope`, whose own basis neiso-95 had established directly. That chain is
sound, but the same promotion **pruned** the neiso-93 bundle from the site, so the chain now
terminates in an artifact no longer in the repo (`results/calibration/neiso93_envelope_A` is
absent at HEAD — confirmed). This session re-derives the declaration from
`results/calibration/neiso97_dstrepair_A/hourly/` directly.

### 1.1 C3c model tail — **0 hours, every year, BOTH passes**

Recomputed under the pinned `render_calibration_html._tail_hours` definition (max across zones,
NaN → −inf) against the NEISO $300/MWh threshold:

| year | P1 | P2 | payload `ordc.hoursGt200.model` | RT actual |
|---|---|---|---|---|
| 2023 | **0 h** | **0 h** | 0 | 15 |
| 2024 | **0 h** | **0 h** | 0 | 8 |
| 2025 | **0 h** | **0 h** | 0 | 20 |

The recomputation **agrees with the registered payload** in all three years, so the artifact and
the published number are one measurement, not two.

**It is not a near miss, and the margin is stated on both passes** — the whole-run maximum of the
max-across-zones price:

| year | P1 max | short of $300 by | P2 max | short of $300 by |
|---|---|---|---|---|
| 2023 | 248.97 | $51.03 | 249.50 | $50.50 |
| 2024 | 218.24 | $81.76 | 256.93 | $43.07 |
| 2025 | **280.85** | **$19.15** | **280.85** | **$19.15** |

The model never reaches the threshold in any hour of any year on either pass; the closest
approach is 2025 at 93.6 % of $300. That is the dual-fuel oil-parity cap showing up directly in
the price distribution — a **formation** gap, not a magnitude one, exactly as the ledgered caveat
says.

### 1.2 Reserve-family dormancy — at the PUBLISHED statics, not merely at whatever the run carried

`reserve_family_<year>.parquet` is the only artifact in which a locational family's binding is
observable (rule 15). Across **all 157,680 family-hours** (3 years × 8,760 h × 3 families ×
2 persisted passes):

* `shortfall_mw = 0.0` in every one — **no hour goes reserve-short**;
* `held_mw ≥ requirement_mw` in every one;
* `|dual|` max **1.42e-14 $/MWh** (a single family-year: 2024 P1 `ne_30min_total`) — floating-point
  noise, stated that way rather than rounded to zero;
* every family's requirement is **static** and equals its **published** ISO-NE RCPF value checked
  against `model/reserves/spec.py::NEISO_RCPF_PRODUCTS` rather than read off the artifact:
  `ne_30min_total` 1,800 · `ne_10min_total` 1,200 · `ne_10min_spin` 600 MW.

The in-LP ISO-NE RCPF co-optimization is therefore **DORMANT**, which is the second load-bearing
leg of the declaration.

**THE DECLARATION HOLDS. No C3c evidence moved in either direction, and no lever was opened.**

### 1.3 An inconsistency inside the shard, resolved: **the scored pass is P2**

The shard's `frontier.reverified` (neiso-84) states the bundle is scored on **P2** and quotes
maxima 249.50 / 256.93 / 280.85; `carried_forward_through` (neiso-95) quotes 248.97 / 218.24 /
280.85, which are the **P1** maxima. Both are correct arithmetic on different passes, and the
shard has been carrying both without saying so — a 18 % spread on the 2024 figure.

Decided on the current keeper's own bytes by the two independent routes neiso-84 used, and they
**agree in all three years — the registered payload is rendered from P2**:

| year | payload `HQ_import` mean λ | P1 err | P2 err | payload `gmModel` class-TWh abs err, P1 | P2 |
|---|---|---|---|---|---|
| 2023 | 38.48 | 0.0585 | **0.0010** | 0.0992 | **0.0714** |
| 2024 | 43.71 | 0.0130 | **0.0020** | 0.0795 | **0.0717** |
| 2025 | 69.44 | 0.0411 | **0.0033** | 0.0106 | **0.0003** |

(NEISO's five model zones clear at one λ in this keeper — no binding internal constraint — so the
payload's load-zone `p` carries the ACTUAL hub mean and `HQ_import`, which has no actual
counterpart, carries the MODEL mean. That is what discriminates. The 2025 class-TWh route is
decisive on its own: 0.0003 vs 0.0106 TWh.)

**This does not disturb the declaration**, because §1.1 measured the tail as **0 h on both
passes** — the frontier basis is pass-independent. It is a documentation defect, and it is
repaired in the shard by this session rather than left for a reader to trip over.

---

## 2. `complete` — the determination REPRODUCES, and M1 passes

`scripts/calibration_verdict.py --run-id 2026-08-17-neiso-97-dstrepair` (committed artifacts
only, **no solve**) returns exactly what the marker records:

* **CALIBRATED-WITH-CAVEATS**
* **0 FAILs**
* **1 ledgered caveat** — C3c price tail / scarcity (RT hourly), the sole ledgerable criterion
* **C1 all 12/12 · free 8/8** (pinned, excluded from free: CC_CHP, ST_CHP)
* grade summary **`{scored 8, target_grade 7, commercial_grade 0, ledgered 1, fails 0}`**

So the rule 22 D-5(b) re-key neiso-97 performed is **reproducible, not merely asserted**. The
marker's `keeper` field reads `2026-08-17-neiso-97-dstrepair`; NEISO is in `complete` and
**absent from `final`** (which holds only `_note`).

`scripts/audit_keepers.py --iso NEISO`: **PASS, 0 failures / 0 warnings**, check M1 included, all
four scopes (keeper / holdout / marker / status) clean.

**Data wait unchanged, nothing estimated around it:** the final 2025 EIA-923 vintage has not
landed, so the 2025 C1 CC rows stay SKIPPED by design (CC_REGULAR 13/30 prior plants missing,
57 % reporting; CC_CHP 3/7) and C2's 2025 gas row is SKIPPED at +2.8 %.

---

## 3. `final` readiness, re-answered on the merits (updates neiso-96 §4): **NOT YET — and this grants nothing**

Both halves re-measured at HEAD. The neiso-96 recommendation to **SPLIT** the block stands
unchanged; the split, like the grant, is the owner's call and nothing here declares either.

### 3.1 The 2019 half — still NO, and now confirmed ON THE REPAIRED INSTRUMENT

The neiso-94/96 measurement (RT max $261.35, 0 hours > $300) predates the neiso-97 repair, which
touched 2019 — 47 RT cells and 46 DA cells, max |Δ| $19.48/$19.54. Re-measured at HEAD on the
repaired series:

| year | RT max | RT h > $300 | DA max | DA h > $300 | coverage |
|---|---|---|---|---|---|
| **2019** | **261.35** | **0** | 178.43 | 0 | 1.0000 |

**$261.35 is bit-unchanged by the repair**, which is what the finding's max-affected-value bound
of $138.65 predicts, so the claim survives its own instrument change. Coverage went 0.9999 →
**1.0000**: the one NaN per market-year is filled with the market's published value — an
independent confirmation of the repair's NaN accounting at HEAD.

**2019 therefore cannot exercise C3c** — the criterion NEISO's frontier is *declared on*. Spending
the touch-once year would buy a verdict silent on the open question. The second live reason is
unchanged: the **Pilgrim fleet-vintage gap** (EIA 1590 ran Jan–May 2019 for 2.177 TWh before
retiring and is absent from the EIA-860 operable snapshot, so a 2019 solve is short ~2.18 TWh of
nuclear regardless of the overlay) — a **cross-ISO charter**, a hard precondition, and **not a
NEISO lane item**.

**The stale clause neiso-95 flagged is still in the marker and is now measured false at HEAD, not
merely withdrawn by argument.** The `complete` entry's `locked_test` field still reads "2019 is
UNSOLVABLE at HEAD (`eia_demand_profiles.parquet` carries NEISO 2021-2025 only, so the LP cannot
be constructed)". Its premise about that file is true — the fallback carries 2021–2025 — but the
**primary** path resolves: `data/raw/ISNE_region.parquet` carries 2015–2026, and calling
`eia930.frames._eia_hourly_frame('ISNE', y)` directly returns **8,760 rows for 2019, 2020, 2021,
2022 and 2023**. The clause is misleading, the conclusion it supports is unaffected (the C3c leg
above is live and sufficient), and it is **left unedited** — this session's authority over that
file is the D-5(b) determination re-verification, not a rewrite of the owner's `locked_test`
reasoning. Flagged for the owner / a governance lane, second session running.

### 3.2 The H1-2026 half — still NO, and the blocker is NOT NEISO's

The six-ISO partial-year solve gate is **live at HEAD**, measured directly rather than read:

```
_eia_hourly_frame('ISNE', 2019..2023) -> OK, 8760 rows each
_eia_hourly_frame('ISNE', 2026)       -> None  (REJECTED)
```

`ISNE_region.parquet` holds 13,460 rows for 2026 against 35,040 for a full year, and
`frames.py` gates on `len(df) != HOURS_PER_YEAR`. The gate is in shared code and blind to ISO:
**the model cannot build a partial-year solve for anybody.** This is structural, six-ISO and
tractable, and it belongs to that lane, not this one.

### 3.3 The validation ladder now runs entirely on the repaired instrument — and a 2022 re-iteration is **NOT worth requesting**

The corrected 2018–2023 SMD instrument covers **every** validation-ladder year (the ladder bottoms
out at 2020), so any future authorized touchpoint iteration measures against the repaired series.
Per-year, measured:

| year | in repaired span | RT cells changed | max abs Δ | max affected value | RT max | RT h > $300 |
|---|---|---|---|---|---|---|
| 2020 | yes | 46 | $34.95 | $88.65 | 236.11 | **0** |
| 2021 | yes | 47 | $39.02 | $112.05 | 375.28 | **2** |
| 2022 | yes | 47 | **$40.17** | **$138.65** | 2,254.35 | **117** |

**Recommendation: DO NOT request an owner freeze-lift for a 2022 re-iteration on
instrument-repair grounds.** The like-for-like caveat is real — the standing touchpoint
`2026-08-06-neiso-2022-corrected-basis` was scored on the pre-repair instrument — but the repair
**provably cannot move that touchpoint's determination**:

* **C3c is untouched by construction.** 2022's max affected cell is $138.65 against the $300
  threshold, so the 117-hour actual tail is bit-identical on both instruments (and
  `actual_tail.json` is byte-unchanged).
* **C3a is untouched to any scored precision.** 47 of 8,760 RT cells move, bounding the annual-mean
  effect at ~$0.06/MWh and measured at ≤ $0.008 — inside any C3a band by orders of magnitude.
* **The model side has not moved either.** neiso-97 measured the keeper's dispatch bit-identical to
  the incumbent's in every sidecar of every year on both passes.

A re-iteration would therefore reproduce the standing record essentially by construction, at the
cost of an owner lift, a multi-GB three-year solve and a registration. **The better use of the
next 2022 spend is after a change that actually moves the model side** — settling O5 (§4.1) and
the Stony Brook routing (§4.2) in one re-solve, which does. Until then the standing touchpoint's
record stands as scored, with the pre-repair instrument noted.

Worth recording for whoever plans that spend: **of the whole ladder only 2022 exercises C3c
decisively** (117 RT hours > $300). 2021 offers 2 hours and **2020 offers none at all** — 2020 is
C3c-degenerate in the same way 2019 is, which neiso-96 did not report.

---

## 4. Owner escalations — RE-MEASURED at HEAD, both still OPEN, neither resolvable without a re-solve

### 4.1 O5 — the legacy-P2 basis, and a **sharpening**: NEISO is not merely running P2, it is SCORED on it

Measured on all six designated keepers' own `meta.json`:

| ISO | keeper | `commitment` | `passes` |
|---|---|---|---|
| CAISO | 2026-08-16-caiso-197-w2-r5 | false | `["P1"]` |
| ERCOT | 2026-08-16-ercot213-arm-pubanchor | false | `["P1"]` |
| MISO | 2026-08-16-miso-160-wefor-shape | false | `["P1"]` |
| **NEISO** | **2026-08-17-neiso-97-dstrepair** | **true** | **`["P1","P2"]`** |
| NYISO | 2026-08-16-nyiso-140-layup-exclusion | false | `["P1"]` |
| PJM | 2026-08-15-pjm-162-inputclock | false | `["P1"]` |

**NEISO remains the sole ISO of six on the archived pass** — neiso-84's escalation neither
resolved nor worsened across three keeper generations. §1.3 adds the part that makes it bite:
**the registered payload, and therefore every published NEISO number and the scored determination,
is rendered from P2**, confirmed by two independent routes on the current keeper. CLAUDE.md's
"Dispatch & Commitment" states P0/P1 are the only production passes, that every run is scored on
P1, and that no keeper uses P2. The materiality is small on the means (mean λ +0.058 / +0.011 /
+0.038 $/MWh) but **+18 % on the 2024 annual maximum** ($218.24 → $256.93) — a price-formation
statistic. **Not acted on here:** resolving it needs a re-solve decision, which is the owner's,
and it is best settled together with §4.2 in one re-solve so the two are not confounded.

### 4.2 Stony Brook plant 6081 outage routing — unchanged

`data/raw/campd-unit-outages-NEISO.csv` still routes the DIESEL peakers to the CC block:

| unit | rows | `plant_group` |
|---|---|---|
| 001 / 002 / 003 | 22 / 30 / 7 | CC_REGULAR |
| **004 / 005** | **74 / 74** | **CC_REGULAR** |

Mechanism confirmed at neiso-96 and unchanged: the `plant_group` enum has no oil or diesel member,
and `derive_campd_unit_outages.py` keys the map by **plant code**, so the diesel peakers inherit
the CC units' group.

### 4.3 The NYISO-lane disclosure — LIVE, and the target keeper has MOVED

The neiso-97 finding filed this against NYISO keeper `2026-08-08-nyiso-133-cod-arm`. NYISO has
since promoted twice; measured at HEAD, the **current** keeper
`2026-08-16-nyiso-140-layup-exclusion` still carries `nyiso_import_hub_prices = true`, so it still
prices its ISONE_tie tranche off the repaired NEISO DA hub series (47 of its 2023 input cells
moved, max $20.12; 2024–2025 byte-identical). **Rule 25 `[R-ISO-SCOPE]`: filed, re-pointed at the
current keeper, and NOT acted on — it is NYISO's call.**

---

## 5. One text defect found and reported, deliberately NOT repaired

**All 7 entries of the NEISO keeper's exceptions ledger open with a sentence attributing the
carry-forward to a CAISO session**: *"CARRIED FORWARD from the incumbent keeper unchanged in
substance. **caiso-159** promotes an INPUT CORRECTION with zero free parameters, so it creates no
new caveat and spends no new ledger slot."* The sentence's **substance is true of neiso-97** (it
is precisely an input correction with zero free parameters, and it spent no new slot); only the
session attribution is wrong.

Genealogy, measured: the sentence originates in `scripts/archive/gen_caiso159_attestation.py` and
is present at HEAD in `results/calibration/neiso97_dstrepair_A/calibration_attestation.json` (7×),
`frontend/data/backcast/status/NEISO.js`, and the CAISO artifacts it belongs to. It entered the
NEISO lane **no later than neiso-95** (`edca6f5`), i.e. it predates neiso-97, whose generator
carried the ledger **verbatim and asserted that it did** — correct behaviour, faithfully executed.
The 2022 touchpoint's attestation is clean (0 occurrences).

**Not repaired here.** The attestation is a registered run's evidence record of what was asserted
at promotion; retroactively editing it would falsify that record. It changes no number, no
criterion and no determination — the ledger count is right, only the attributing session name is
wrong. Reported for the owner / a governance lane, the same posture neiso-95 took with the
`locked_test` clause.

---

## 6. What this session changed

Text and stamps only; **nothing here can change a solve**.

* `frontend/data/backcast/keepers/NEISO.json` — `frontier.reverified` rewritten for this
  verification (the neiso-84 text is preserved inside it, labelled, including its correct
  P2 identification); `frontier.carried_forward_through` re-stamped with the direct
  re-establishment and the pass-basis resolution. `keeper` untouched.
* `frontend/data/backcast/status/NEISO.js` — rebuilt via `build_status.py --iso NEISO`.
* `docs/calibration-log/neiso.md` — the neiso-98 entry.
* `docs/audit/third-party-audit-2026-08.md` — row **O5** gains its HEAD re-measurement and the
  scored-on-P2 sharpening. Row O8 untouched (RESOLVED at neiso-97).
* Three probes + their JSON records.

**Not changed:** `calibration-complete.json`, `holdout-freeze.json`, the run payload, the registry
sidecar, the bundle, `actual_tail.json`, the mechanism matrix (no mechanism was tested, no cell
verdict moved, and the NEISO shard's keeper/gates stamps already read
`2026-08-17-neiso-97-dstrepair` — rule 28d).

**Next shorthand: `neiso-99`.** No NEISO tuning lever is open — the frontier is declared and
re-verified, and DO-NOT-REDO applies to every `R`/`I`/`G` cell in the NEISO matrix shard. Further
C3c work needs a NEW measured identification and its own charter; this session found none it could
name from committed artifacts and therefore requests none. The lane's standing items are the
**two owner escalations** (§4.1 O5 and §4.2), best settled together in one re-solve. **Not NEISO
lane items:** the partial-year solve gate (six-ISO), the fleet-vintage/Pilgrim charter (cross-ISO),
the `_dual_fuel_plant_groups` vintage seam, the `complete`-entry stale clause (§3.1) and the
ledger attribution defect (§5).
