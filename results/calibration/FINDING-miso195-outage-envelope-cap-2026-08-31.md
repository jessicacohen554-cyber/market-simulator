# FINDING miso-195 — the remove-only measured cap on the MISO outage envelope is REFUTED at phase 0: its only converting hours are the hours its own removal is provably infeasible (2026-08-31)

**Session:** miso-195 (2026-08-31). **Keeper:** `2026-08-30-miso-191-bexit`
(bundle `results/calibration/miso191_bax_B`), **UNCHANGED**. **No LP solved,
nothing armed, no `ScenarioConfig` field added or re-semanticized, no run
registered** (the miso-142/…/192/194 no-LP precedent; rule 15 `[R-DASHBOARD]`
not engaged).

**Charter.** FINDING-miso194 §7's named successor: charter the FLEET-GRAIN,
REMOVE-ONLY measured cap on the armed CAMPD outage envelope, fed by MISO's own
published Multiday Operating Margin unplanned record, argued from the NET-LOAD
channel (the summer target owning 60% of C3a-2025). The form was charter-forced
(miso-176 K-2: no apportionment may be invented; remove-only: the pjm-145
resurrection channel unreachable by construction). Gate `miso_native_outage_source`
(default off, armed in zero bundles) would carry it; its substitution semantics
are separately R (miso-85/86) and were not re-tested.

Instrument (read-only, idempotent, committed):
`scripts/probes/_miso195_outage_envelope_phase0.py` →
`results/calibration/_miso195_outage_envelope_phase0.json`. Every gated number
below reproduces by running that script. **The full adjudication rule — bases,
population, the cause-type basis settle, witnesses W1–W6 with their lines, the
directional prereg (C3a-2025 UP, confidence 0.40, ≥ +0.30 pp materiality) — was
frozen in the probe docstring and pushed at `09f70160` BEFORE any adjudicating
quantity was computed** (the miso-193/194 pattern; mechanical satisfiability of
every basis verified on the control first, no adjudicating value read).

---

## 0. Ask A — the zero-solve validation, reproduced exactly as handed off

| gate | result |
|---|---|
| `calibration_verdict --run-id 2026-08-30-miso-191-bexit` | **NOT-YET** on **{C3a-2025 −12.3%} ALONE** |
| C1 / C2 / C3b / C4 | PASS (C1 16/16 · free 12/12) |
| C3c | the single **ledgered** caveat (all three years) |
| C6 / C8 | PASS; C8 carries its two grounded notes (2023 CT_PEAKER 15.6%, 2025 ST_GAS 34.2%) |
| `audit_keepers --iso MISO` | PASS, 0/0 |
| `build_status --iso MISO --check` | in sync |
| `check_mechanism_matrix.py` | integrity OK |

Distance to band unchanged, **+2.34 pp**.

## 1. The cause-type basis, settled ex ante (charter ask C)

FROZEN before measurement: the cap reads the record's **UNPLANNED components
(Derated + Forced + Unplanned)**, never all-cause. (1) The with-Planned form is
already owner-adjudicated infeasible against MISO's own metered output
(miso-85: 12/15/61 days; in every binding hour the capped availability equals
the substitution's, so the refutation applies verbatim). (2) Congruence where
the mechanism lives: `Planned` bottoms out in July (7.9 GW vs 36.4 GW April,
mostly non-thermal even then) and the model's own planned-window component is
likewise out of the peak — smallest mismatch exactly in the target window,
and everywhere else the mismatch's sign (the armed envelope carries planned
windows the basis excludes) makes the cap strictly conservative in the
shoulder, protecting the over-priced 2023/2024 body by construction. (3)
Lineage continuity: unplanned is what miso-85 (substitution), miso-160 (the
armed summer share) and miso-161 (the peak-shape measurement) all read. The
against-interest face — unplanned-vs-armed-total under-binds, the pjm-161
"definitional mismatch → never binds" arm — was named and handed to W3 to
measure. **W3 answered it: the cap binds fine (§3). The basis was not what
killed the lever.**

## 2. What phase 0 measured about the landscape (the levels, first honest look)

Annual-mean offline MW, armed model envelope (M, the full load-bearing build:
WEFOR/POF × CAMPD windows × short/maxgen/status/layup × CHP-temp × summer
basis, over the loader's own 115.3 GW thermal population) vs the published
record:

| GW | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| M (armed envelope) | 37.04 | 36.50 | 36.82 |
| P unplanned (D+F+U) | 21.76 | 24.20 | 28.06 |
| P all-cause | 42.35 | 41.82 | 48.69 |

- **W2 PASS** — the pjm-161 level refutation does NOT transfer: MISO's armed
  envelope (36.8) sits well under the whole-fleet all-cause record (48.7),
  where PJM's model asserted MORE outage on fossil alone than PJM published
  for its entire system. The remove-only direction is level-legitimate here.
- The armed M is ~11 GW deeper than the CAMPD component alone (the statistical
  stack multiplies in) — the annual residual-vs-unplanned is *negative* in
  every year, which is miso-85's "residual composition is inert" note
  reproduced at the armed envelope. **The deficit is a shape object, not a
  level object**: monthly M bottoms at **24.5 GW in July 2025** (the armed
  envelope's year-minimum, in the scarcest month) while the record reads
  **31.7 GW** — the zero-generation detector's blindness at the peak, now
  measured at full-fleet grain. ρ(deficit, net load) = +0.43/+0.47/+0.54.

## 3. The frozen gate: three witnesses pass, and what they establish

| witness | line | result |
|---|---|---|
| W1 composition census | 0 armed daily-level consumers | **PASS** (the same-source `summer_wefor_share_override` consumes the seasonal RATIO; the cap's deficit is net of the full armed envelope, double-count impossible by construction) |
| W2 level congruence | M(2025) < P_all(2025) | **PASS** 36.8 < 48.7 |
| W3 bind in the scarce set | ≥ 25% of top-200 | **PASS 91.5%** (183/200) |
| W5 reach ceiling at actuals | ≥ +0.30 pp | **PASS +11.79 pp** (S-only +4.76; adverse exposure 1.85; m160-slope linear projection +0.62) |

And the miso-161 confrontation resolved in the lever's favor on magnitude
(R2, 2025): deficit at the scarce set = **5.94 GW mean** = Jun–Sep level gap
**+2.20** (the record's summer level ABOVE the armed envelope's) + the model's
own sag at the peak **+2.94** (the miso-194 W6 inversion term) + the record's
peak increment **+0.69** (the miso-161 quantity, reproduced to the decimal).
The anti-list's "MOM daily-grain outage shape ≲ 0.11 pp" bounded only that
third term; the deficit is ~10× it, ~2/3 from terms the record-internal
measurement could not contain. The binding footprint is summer-selective
exactly as designed: 2025 monthly binding share Jun 60% / Jul 97% / Aug 81%,
shoulder ~0 (the basis conservatism delivering), removed 11.2 TWh·h of
capability; top-1% net-load binding 80.7/88.6/**94.3%** across years.

## 4. The two witnesses that refute it — and why together they are decisive

**W4 CONVERSION — FAIL, 16.9% vs the frozen 25% line.** Among the 183 binding
scarce-set hours, the median removal (**6.65 GW**) sits against the keeper's
own median idle thermal capability of **18.3 GW** (total headroom, leg A:
converts **0** hours) and a median **10.95 GW** of idle CT_PEAKER + ST_GAS
alone (past-the-peakers leg B: converts **31** hours). The miso-194 absorption
regime, milder but standing: the model's surplus in the scarce set exceeds the
measured removal in five of six binding hours. (Disclosed ex ante and still
true: leg B under-credits walks *within* the peaking stack; the frozen line
pre-committed the call precisely so closeness could not be re-litigated
post hoc.)

**W6 PHYSICAL FEASIBILITY — FAIL, 6 violation days in 2025 vs the ≤3 line.**
On the unplanned basis, the capped availability (population capacity minus
max(armed offline, record)) falls below MISO's own **measured** EIA-930
daily-max coal+gas generation on **Jun 23, Jun 24, Jul 23, Jul 28, Jul 29,
Jul 30 of 2025** (plus 2 days of 2023; zero in 2024). Post-gate attribution
(disclosed as post-gate; it verifies the frozen relation rather than amending
it): **all 8 violation days are CAP-CAUSED** — the incumbent envelope is
feasible on every one; the cap's removal breaches measured output by **0.57 to
4.58 GW**. Jul 28 2025 is the exhibit: the real fleet delivered **86.6 GW** of
coal+gas while the record charges 33.4 GW of whole-fleet unplanned outage to a
115.3 GW thermal population, leaving at most **82.0 GW** — the record's
numerator provably carries ≥ **4.6 GW** of non-population outage MW (wind
derates, nuclear, non-modelled steel) **on the exact heat-event day the
mechanism exists to reprice**, and the fleet-grain form has no fuel identity
to strip it with.

**The coherence measurement that settles the adjudication** (post-gate
diagnostic 2): **28 of the 31 converting W4 hours sit on the 6 cap-caused
violation days** (Jul 28: 9 h, Jul 29: 8 h, Jul 23: 7 h, Jun 23/24: 2+2 h;
3 stray hours elsewhere). Had the cap been armed, essentially its entire price
action would have been scarcity manufactured from removal that MISO's own
metered output proves excessive. That is reaching the right number through a
mechanism that is not doing the thing it is defended by — rule 1
`[R-STRUCT]`'s forbidden path — measured before any solve was spent.

## 5. Verdict, and exactly what is and is not closed

**REFUTED at the pre-frozen phase-0 gate: `CHARTER_AB = false` on W4 ∧ W6.**
No A/B, no arm, no PREREG (charter F: one lever per session). The MISO
`campd_outage_windows` cell stays **K** (the armed CAMPD envelope is the
keeper mechanism); its ev note now records this adjudication of the registered
sub-mechanism.

**Closed by this session (DO-NOT-REDO without new evidence):** the fleet-grain
remove-only cap on the unplanned basis against this keeper family — and a
fortiori the all-cause cap (feasibility-refuted harder, miso-85 + W6). With
the substitution R (miso-85/86), the attribution split refused-at-charter
(miso-87), and now the remove-only composition refuted, **every admissible
composition of `miso_native_outage_source` at the public record's aggregate
grain is adjudicated.** Repairing the envelope inversion from this record now
requires a class-resolved source — the standing data ask
(`docs/handoffs/miso-outage-grain-data-ask-2026-07.md`; candidates 1–3 closed,
candidate 4 "MISO data request" unchanged) — not a new composition rule over
the old one.

**NOT closed, stated against the refutation's interest:** the defect itself.
The envelope inversion is real, measured, and unrepaired — miso-194's
ρ(offline, net load) −0.61…−0.70 and cold-inversion, this session's July-2025
year-minimum armed envelope (24.5 GW) against the record's 31.7 GW, the
94.3% top-1% binding share, the +11.8 pp W5 ceiling, and the R2 decomposition
all stand as evidence the CAMPD detector hands the LP its most capacity in the
tightest hours. What is refuted is this cap as its repair, on grain — the
miso-86 conclusion, reproduced in the remove-only direction with the
contamination now bounded in MW on the days that matter (≥ 0.6–4.6 GW).

**Not touched** (charter "not yours to decide"): the D-4 posture ruling, the
miso-141 §11 nameplate-basis switch, the C8 provenance-materiality floor, the
RHO_CLIP band, the miso-189 §7.3 residue, the `correlated_forced_outage`
backcast-coercion default. No holdout year: MISO holds no `complete`/`final`
marker and the holdout freeze is active; the probe reads 2023–2025 only.

## 6. The successor handed on (named, not chartered — one lever per session)

**`cc_outage_derate_from_top`** (charter's second candidate): armed on the
CAISO and PJM keepers, False on MISO's, no new field, no new row — the
application-shape leg of this same row. It addresses the same defect at
TRANCHE grain (a partial outage truncates the expensive end of a CC plant's
curve instead of dragging the cheap committed floor down with the plant), and
its face must be declared honestly by whoever charters it: it makes MORE cheap
and LESS expensive capacity available, and miso-193 measured that shrinking
the expensive top band moves C3a-2025 **down** (−12.34 → −13.33 on the cap
arm). Structurally right, predicted adverse on the 2025 level — a rule-1 case,
never a level lever. This session took no measurement of it (the frozen rule
was spent on the chartered lever; charter F says stop).

Census queue after this session, unchanged otherwise:
`egrid_identity_heat_rates` (K@NYISO), `tac_load_coverage` (K@CAISO),
`lcr_tsl_published` (K@CAISO+NYISO).

## 7. Reproduction

```
python3 scripts/probes/_miso195_outage_envelope_phase0.py
```

Record: `results/calibration/_miso195_outage_envelope_phase0.json` (frozen rule
pushed at `09f70160` before any adjudicating quantity; the two post-gate
attribution diagnostics are §4's tables, disclosed as post-gate — they verify
the frozen W6 relation's attribution and the W4/W6 overlap, and change no
verdict). Holdout: 2023–2025 only (rule 22; MISO holds neither marker; freeze
active; the actual-price parquet's 2022/2026 rows are never read).
