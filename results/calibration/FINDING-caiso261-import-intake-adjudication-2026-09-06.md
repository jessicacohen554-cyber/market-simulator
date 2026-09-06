# FINDING — caiso-261: the hod 22–23 price-taking import volume is **NOT a data-intake object** in 2024–2025 and is **BOUNDED, not open**, in 2023. The keeper already floors the WHOLE of CAISO's measured price-insensitive intertie position at these hours (ceiling − firm floor = 1 MW in 2025, 29 MW in 2024), and the DMM's own §17 "native load need" final values — shown RA imports on the priority-wheel ties — match that floor to **+48 / +7 MW in Jul / Aug 2025**. Nothing "beyond RA" exists in any admissible source: the one non-RA quantity the ISO names is ≤ 600 MW and appears only in an estimate. What the ~1.8 GW at 22–23 in 2025 actually is, by attribution: **~0.8 GW of dynamic WEIM net transfer plus ~1.0 GW of economic intertie import cleared at hub parity** — conduct every armed construction prices above or windows out, and that only the un-fetched public-bid economic limb could size. **ZERO LP, nothing armed, keeper UNCHANGED. Two registered predictions FAIL as written and are recorded as failures; both misses point the same way as the conclusion, and the tolerances are not widened.**

**Session caiso-261, 2026-09-06.** Branch
`claude/caiso-backcast-calibration-261-2hrovn` off `origin/main`
`8dc64272`. Keeper **`2026-09-06-caiso-260-b1-demand`**
(`caiso260_demand_vintage`, sha `e162147b`) **UNCHANGED**, DETERMINATION
**CALIBRATED** (rubric v3.6). Pre-registration
`PRECOMMIT-caiso261-import-intake-adjudication-2026-09-06.md`, pushed before
the instrument ran. Instruments:
`scripts/probes/_caiso258_hod2223_closure.py --import-stack --session
caiso-261` (re-pointed at the caiso-260 bundle; per-month floors added) →
`results/calibration/_caiso261_closure_on_caiso260.json`, and
`scripts/probes/_caiso261_import_intake_adjudication.py` →
`results/calibration/_caiso261_import_intake_adjudication.json`. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; no `complete` / `final` marker; freeze
ACTIVE. **No solve, no screen, no `ScenarioConfig` field, no derive run, no
bench regeneration, no corpus re-fetch, no run registered (none produced —
rule 15 not engaged), no bundle (rule 29(c) not engaged), no matrix verdict
moved.** G-CTRL form 4 (the keeper's committed bundle; no control solve).

---

## §0 — The exposures, re-measured on this keeper before anything else

| cell | keeper | bound | what this session measured |
|---|--:|--:|---|
| C4-2025 gas NRMSE | 0.298 | ≤ 0.30 | hod 22–23 carry **9.0 %** of the 2025 gas MSE (8.2 / 8.0 % in 2023 / 2024); zeroed, 0.284 (P-6 HOLDS). Direction only; C4 entered no conclusion. |
| C3c-2023 tail | 23 h vs 47 | ≥ 24 h | the sidecar's load-weighted price reproduces the scored **23** exactly; they are **one hour per hod of a single day** (every hod but 12), so **2 of 23** sit at hod 22–23 (P-7 HOLDS). A carrier at these hours could move the count by at most 2 in either direction; **not a target**, and not moved. |

C3a: excluded both ways, as declared (PRECOMMIT §0.3); no number from it is
cited here.

## §1 — G-REPRO on the caiso-260 keeper: P-1 / P-1b HOLD

| quantity | caiso-258 (on caiso-257) | this session (on caiso-260) | diff |
|---|--:|--:|--:|
| hod 22–23 import deficit, model − 930 net interchange (model clock), 2023 / 24 / 25 | −972 / −1,467 / −1,763 MW | **−974 / −1,466 / −1,769** | −2 / +1 / −6 |
| CC_REGULAR error hod 22 / 23, 2025, CEMS basis | +1,536 / +1,546 | **+1,459 / +1,478** | −77 / −68 |
| committed import at 22–23 vs Σ WECC capability, 2023 / 24 / 25 | 4,419 / 4,130 / 4,438 of 12,278 / 13,182 / 13,459 | **4,417 / 4,131 / 4,432 of 12,278 / 13,182 / 13,459** | ≤ 6 MW |
| C4 fit reproduced | — | 0.881/0.287, 0.912/0.260, 0.877/0.298 | = keeper |

The caiso-260 arm did not re-shape the hour: the deficit is the same to
6 MW, and the CC error moved by the −52 MW mean the arm took off CC in 2025.
(The closure probe's own caiso-258-era G-REPRO row `import_gap_2025` reads
FAIL at −107.5 MW against caiso-253's **DST-clock** number, exactly as it
did at caiso-258 §1 — caiso-258 §10 #1 is why P-1 was registered against
the model-clock figures instead.) The model-side sidecar identity residual
is unchanged at max 233 / 487 / 507 MW (caiso-258 §2.1); the 930 BA residual
at 22–23 is unchanged at +2,068 / +484 / +632 MW.

## §2 — E-1, the self-scheduled hypothesis: **P-2 HOLDS in 2024 and 2025, FAILS as registered in 2023**

The keeper's two firm rows (`WECC_PNW_PNW_hydro_base`,
`WECC_DSW_DSW_solar_PV`) carry the only non-negative floors at 22–23. Their
summed `min_gen` by month, against the caiso-151 measured price-insensitive
intertie ceiling (pooled 2023–2025 climatology, hod 22–23 mean):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **mean** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| ceiling | 2,837 | 3,194 | 3,206 | 3,176 | 4,094 | 4,228 | 4,266 | 4,043 | 3,755 | 3,295 | 3,487 | 3,888 | 3,622 |
| **2025 ceiling − floor** | 0 | 0 | 0 | 0 | 0 | 0 | 14 | 0 | 0 | 0 | 0 | 0 | **1** |
| **2024 ceiling − floor** | 269 | 0 | 0 | 0 | 0 | 0 | 76 | 0 | 0 | 0 | 0 | 0 | **29** |
| **2023 ceiling − floor** | 0 | 0 | 0 | **898** | 0 | **620** | **1,277** | 152 | 37 | 153 | 14 | **1,482** | **386** |
| 2023 floor | 2,837 | 3,194 | 3,206 | 2,277 | 4,094 | 3,608 | 2,988 | 3,890 | 3,718 | 3,142 | 3,473 | 2,406 | 3,236 |

**2024 and 2025: the clip binds** (29 / 1 MW mean; max month 269 / 14). The
keeper already floors the entire measured price-insensitive intertie
position at these hours. By CAISO's own bid record — the ceiling is a
one-sided upper bound on the true price-insensitive *import* position,
built from ALL intertie self-schedules plus import-classified economic MW
at or below $0 (caiso-150 §B) — **no self-scheduled or ≤ $0 intertie volume
remains un-carried in the two years where the object is largest**
(−1,466 / −1,769 MW). The self-scheduled limb of H-INTAKE is falsified
there.

**2023: P-2 FAILS as registered** (386 MW mean against the ≤ 150 MW band)
and the §5.2 alternative-object trigger (≥ 500 MW on the mean) does **not**
fire; the max month, 1,482 MW in December, was not the registered
statistic and is reported here at full magnitude rather than folded into
one. What the 2023 room is: the floor in Apr / Jun / Jul / Dec sits at the
**shaped DMM 2023 level** (2,323 MW × the caiso-73 shape — 2,277 / 3,608 /
2,988 / 2,406 MW), i.e. the *published* cap binds there, not the measured
one, and the pooled ceiling — equal-weighted across a 2,323-MW year and two
3,371-MW years — leaves room above it. So in 2023 the self-scheduled limb
is **bounded, not falsified**: at most 386 MW mean (≤ 1,482 MW in the worst
month, 0 in eight months) of price-insensitive import could exist that the
floor does not carry, against a 974 MW deficit; the true figure is ≤ that,
and a 2023-only ceiling (the derive's per-year table, not shipped) would
sit lower than the pooled one in a year whose RA-import level was 31 %
below the pooled mean. **No source names a higher 2023 contracted level
than the DMM's own table**, so this is not an intake either; it is a bound
on the record.

## §3 — E-2, the showing hypothesis: **P-4 HOLDS; P-3 FAILS as registered, in June, by 28 MW, in the direction that says the showing is SMALLER than the floor**

The DMM 2025 §17 "native load need" is, by the report's own definition
(p. 340), *shown import RA plus non-RA contracts LSEs may show* — a
**monthly transmission set-aside**, published for Jun–Sep 2025 only, on the
priority-wheel tie points only (NOB, Malin 500, Palo Verde,
Adelanto–Victorville), as bar charts. Its **final value is shown RA imports
alone**; the non-RA term appears only inside the ISO's historic
*estimate*. Chart reads (±100 MW), each reproducing the report's own text
(over-estimates 1,500 / 900 / 1,600 / 2,100 MW = 42 / 22 / 39 / 52 %) to
within 50 MW:

| 2025 | final shown RA (PWT ties) | ceiling at 22–23 | keeper 2025 firm floor at 22–23 | final − ceiling | final − floor |
|---|--:|--:|--:|--:|--:|
| Jun | 3,600 | 4,228 | 4,228 | **−628** | **−628** |
| Jul | 4,300 | 4,266 | 4,252 | +34 | **+48** |
| Aug | 4,050 | 4,043 | 4,043 | +7 | **+7** |
| Sep | 4,150 | 3,755 | 3,755 | +395 | +395 |

**Jul and Aug are the result of this section: the ISO's final shown-RA
import set-aside on the priority-wheel ties equals the keeper's firm floor
at hod 22–23 to within 50 MW** — two independent constructions (a
regulatory showing; a bid-record ceiling clipping a DMM level × EIA-930
shape) landing on the same number. The showing IS the price-insensitive
intertie position the ceiling measures; it is on a subset of ties, and it
is **not additive** to the firm block.

**P-3 FAILS as registered**: June reads −628 against a ±600 two-sided band.
The miss is 28 MW past a tolerance set at 6× the read error, and it is
**below** the floor — the showing is smaller than what the keeper already
forces, which is the opposite of the "beyond-ceiling quantity ≥ 0.5 GW" the
stop rule's §5.3 gloss names as the thing that would earn an intake. It is
recorded as a FAIL; the band is not widened; and the conclusion it bears on
(no additive showing exists) is, if anything, strengthened by it.

**P-4 HOLDS**: the historic non-RA component of the estimate reads ≈ 250 /
50 / 600 / 300 MW (≤ 700), never in a final value. Malin finals 1,050 /
980 / 1,010 (Jul–Sep), NOB 900 / 980 / 900 / 820 (Jun–Sep) — the two ties
caiso-252 §6.1 named — sum to ~2.0 GW against the keeper's ~1.6 GW PNW
firm floor there (`PNW_hydro_base` 1,636 MW mean at 22–23 in 2025); the
difference is inside the read error plus the corridor-split convention.

**The CPUC RA showings (S-6) were not fetched**: by construction they are
the same object as this final value and the DMM RA-import row, on a
CPUC-jurisdictional boundary the firm block's own rule-14 comment already
rejects for CARB / CEC series.

## §4 — E-3, what the residual IS (class C, diagnostic only): **P-5 HOLDS**

DMM Figure 4.2 (net inter-regional dynamic WEIM transfers by hour,
5-minute market; base schedules excluded per footnote 148): the "California
ISO" bar at hours 22–24 reads a net **import** of ≈ 800 / 700 / 900 / 800 MW
in 2025 Q1–Q4 (±150), mean **≈ 0.8 GW**; Figure 1.53's after-transfer line
sits above its before-transfer line by a similar amount in those hours.
Against the 2025 deficit of 1,769 MW that leaves **≈ 0.97 GW** — economic
intertie import cleared at or below λ ≈ $44, i.e. bids priced at hub parity
that the model's economic rungs price at delivered hub cost, $4–20 above
(caiso-258 §5; caiso-252 §3.2: the measured night price equals the hubs).

So the object has two halves and neither is a contracted volume:

1. **~0.8 GW dynamic WEIM net transfer** — the model's representation is
   the at-hub clean-transfer rows, which have zero capability at 22–23 by
   window; caiso-253 refused extending them on the measured raw-hub
   discriminator (2023 fails at both hours). **Refused stays refused.**
2. **~1.0 GW economic intertie import at hub parity** — the model's
   representation is the priced ladder, whose $/MWh are the
   "static-fitted-pending-measured" Tier-3 proxies of gap-register G-26 /
   audit C-6. The only *measured* source that could size this half is the
   economic limb of `PUB_DAM_GRP` (S-7: import-classified economic curves,
   classifiable by monotonicity — 149 import / 162 export at caiso-150 —
   unlike the self-schedules behind the wall), and the corpus is off disk.
   **Not proposed on this residual** (caiso-252 §7 #2; caiso-258 §10 #4).
   Raised to the owner as the G-26 decision it already is (§8).

Both halves are realised-flow attributions (class C) and enter nothing.

## §5 — Stop rule, applied as written

| clause | condition | fired? | disposition |
|---|---|---|---|
| **5.1** H-INTAKE falsified | P-2 ∧ P-3 ∧ P-4 | **NO, as written** (P-2 fails 2023; P-3 fails Jun) | **In substance, YES for 2024–2025**: both limbs falsified in the two years that carry the object; 2023 bounded (§2). Stated as such, not re-scored. |
| 5.2 clip not binding | mean ≥ 500 MW any year | NO (2023 mean 386) | the 1,482-MW December month is disclosed; not an object |
| 5.3 an intake to name | P-3 or P-4 falsified | **formally YES** (P-3, Jun) | **substantively NO**: the gloss's trigger is a beyond-ceiling quantity ≥ 0.5 GW; the miss is −628 MW *below*. No intake exists to name; none is named. |

**Every branch of the stop rule was STOP-only and no branch solves. The
session ends with no arm.** The judgment in reading 5.1 / 5.3 by their
substance rather than their letter is mine and is disclosed (§7 #1); the
two literal FAILs stand in the artifact as `holds: false`.

## §6 — PREDICTIONS, SCORED

| # | registered | measured | verdict |
|---|---|---|---|
| P-1 | deficit within ±300 of −972 / −1,467 / −1,763 | −974 / −1,466 / −1,769 | **HOLDS** |
| P-1b | CC err 2025 within ±300 of +1,536 / +1,546 | +1,459 / +1,478 | **HOLDS** |
| **P-2** | ceiling − floor mean ≤ 150 every year | 386 / 29 / 1 | **FAILS (2023)**; holds 2024–25; 5.2 not triggered |
| **P-3** | S-1 final within ±600 of ceiling and floor, Jun–Sep | −628 / +34 / +7 / +395 (ceiling); −628 / +48 / +7 / +395 (floor) | **FAILS (Jun, −628, below)**; holds Jul–Sep |
| P-4 | non-RA ≤ 700, never in a final | ≤ 600; estimate only | **HOLDS** |
| P-5 | WEIM 22–24 in [0.4, 1.2] GW; residual ≥ 0.6 GW | 0.8 GW; 0.97 GW | **HOLDS** |
| P-6 | 22–23 share of 2025 gas MSE in [8, 11] % | 9.0 % | **HOLDS** |
| P-7 | ≤ 3 of the 23 tail hours at 22–23 | 2 (and the sidecar reproduces 23) | **HOLDS** |

Six hold, two fail as written. Both failures are stated at full magnitude
and neither was re-scored.

## §7 — DISCLOSURES AGAINST INTEREST

1. **I read two literal FAILs by their substance.** P-2's 2023 miss and
   P-3's June miss both stand as `holds: false` in the artifact; the
   conclusion (no admissible source carries a contracted or self-scheduled
   volume beyond the firm block) rests on 2024–2025, where every registered
   check holds, and on the sign of the June miss. A reader who wants the
   letter has it: 5.1 did not fire as written.
2. **The DMM pages were read before the PRECOMMIT was pushed** (source
   scoping; PRECOMMIT §3 discloses it). The transcribed values are chart
   reads at ±100 / ±150 MW, cross-checked to the report's own text for §17;
   Figure 4.2 has no text cross-check and its ±150 is my estimate of a bar
   height on a 4,000-MW axis.
3. **The ceiling is a pooled climatology**, so the 2023 room in §2 is
   partly a pooling artifact of a 2,323-MW year against two 3,371-MW years.
   The per-year 2023 table exists only inside the derive's gates and was not
   re-derived (caiso-150 §H forbids re-measuring the ceiling).
4. **The 2024 DMM Annual Report was not fetched** — the URL on the
   caiso.com pattern 404s — so the §17 comparison is 2025-only. The
   definition is the same in both reports and the object is 2025's, so the
   adjudication does not depend on it; a 2024 §17 read would add a second
   year of the Jul/Aug coincidence or break it.
5. **G-DRIFT was not run** (no solve at stake); the identity probe is
   re-pointed and ready. The closure probe's D-3 leg rebuilt `fleet_only`
   at HEAD, not at `e162147b` (as caiso-258 §8 #9) — its cross-checks
   passed (`mic_partition` 16,055 / 16,452 / 16,148; no fallback line;
   committed import ≤ Σ capability every hour), and the LP-input
   identity `c78f6d94 → e162147b` was measured bit-identical at caiso-260.
6. **The C4-2025 exposure is stated, not spent.** No arm exists, so the
   pre-solve statistic was not computed; D-4's 9.0 % / 0.284-if-zeroed is a
   direction statement and enters no basis.
7. **The 2023 committed-import pattern at 22–23 is odd and not pursued**:
   8,139 / 6,078 / 6,072 MW in Jan–Mar against a floor of 2,837–3,206 —
   the model over-imports at these hours in a wet winter (the 2023 deficit
   by hod is +591 … +1,142 MW overnight and +2.2–2.5 GW at hod 8–15, i.e.
   the import-shape mirror caiso-252 §3.1 already named). Reported; not an
   object of this PRECOMMIT.
8. **No ninth C3a direction exists** because no arm was solved; the
   PRECOMMIT §0.3 declaration stands for any successor.

## §8 — OWNER ASKS (raised, not granted)

1. **The `complete` marker** (rule 22) — CAISO is CALIBRATED; raised again.
2. **The 2022 price source** (caiso-259 §7 #2).
3. **The stale `program-status.json` `isos.CAISO.keeper` stamp** — not
   touched; ask before touching.
4. **The C3a weight basis**; **the per-zone storage/class sidecar** (the
   identity residual re-measured unchanged here, max 233 / 487 / 507 MW);
   **S2**; **the DMM 2025 RA-import basis**.
5. **The G-26 / audit C-6 CAISO closure** — a measured intertie economic
   offer surface from `PUB_DAM_GRP` (S-7): the only measured source that
   could size the ~1.0 GW economic half of the 22–23 residual. Not proposed
   on this residual; if funded it needs the corpus re-fetched (~1,096 daily
   zips, ≥ 6 s each, 0.5–0.9 GB), its own PRECOMMIT with C3a / C4 excluded
   and the C4-2025 / C3c-2023 exposures re-stated, and the caiso-150 §H
   wall respected. **Fund, defer, or refuse.**

## §9 — DO-NOT-REDO ADDS

1. **Never re-adjudicate the DMM §17 native load need as an intake for the
   22–23 volume.** It is shown RA imports on the priority-wheel ties,
   Jun–Sep, a monthly transmission set-aside, chart-only; it matches the
   keeper's firm floor to +48 / +7 MW in Jul / Aug 2025, and its one non-RA
   term (≤ 600 MW) is an estimate component, never a shown value.
2. **Never read the 2023 ceiling-minus-floor room (386 MW mean) as
   un-carried self-scheduled volume.** It is a one-sided bound on a pooled
   climatology above a 2023 published level; no source names a higher 2023
   contracted level.
3. **Never propose the CPUC RA showings as a source "beyond" the DMM
   RA-import row.** Same object, narrower boundary.
4. **Never wire DMM Figure 4.2 / 1.53 WEIM transfers or EIA-930 net
   interchange as an input.** Class C — realised flows; diagnostic only.
5. **Never select the G-26 CAISO intertie offer surface on this residual.**
   It is an audit item with its own charter; a session that reaches for it
   because the 22–23 gap is 1.0 GW is doing what caiso-252 §7 #2 forbids.
6. caiso-260 §9, caiso-258 §10, caiso-257 §10 and every section they carry
   stand in full.

## §10 — QUEUE

1. **The hod 22–23 object is CLOSED as a data-intake object** (2024–2025)
   and **re-named by attribution**: ~0.8 GW dynamic WEIM net transfer (the
   window caiso-253 refused; stays refused) plus ~1.0 GW economic intertie
   import at hub parity (sizable only by S-7, an owner decision under G-26).
   In 2023 the self-scheduled limb is bounded at ≤ 386 MW mean. **No
   executable calibration lane remains on it without an owner decision.**
2. **2022 readiness** (caiso-259 §1–§2; caiso-260 §10 #4) — H-1 buildable;
   H-2 / H-3 the owner's price-source decision.
3. The whole-plant-off days (caiso-187/192, DO-NOT-REDO); the sidecar
   identity residual (unchanged); Panoche / the CT volume miss.
4. Carried, raised not granted: the `complete` marker; the
   `program-status.json` stamp; the C3a weight basis; the DMM 2025 RA-import
   basis; S2; and now the G-26 CAISO closure.

## §11 — DELIVERABLES

`PRECOMMIT-caiso261-import-intake-adjudication-2026-09-06.md` (pushed
first); `scripts/probes/_caiso258_hod2223_closure.py` (re-pointed at
`caiso260_demand_vintage`; `--out` / `--session` flags; per-month floors and
capability at 22–23 in D-3) → `_caiso261_closure_on_caiso260.json`;
`scripts/probes/_caiso261_import_intake_adjudication.py` →
`_caiso261_import_intake_adjudication.json`; the caiso-260 §8 #8
housekeeping (`_caiso255_gdrift_identity.py`, `_caiso260_screen.py`
re-pointed, the screen probe's keeper C4 baseline updated); this finding;
the `docs/calibration-log/caiso.md` entry; rule-28 CAISO matrix-shard
**evidence appends** on `import_hub_pricing` and
`caiso_firm_selfsched_floor` (no verdict move — no mechanism was tested);
the §5.2 clause in `docs/mechanism-testing-matrix.md`.

**No run registered (none produced), no keeper change, no `ScenarioConfig`
field, no new matrix row, no matrix verdict move, no `complete`
declaration, no out-of-training year touched, freeze ACTIVE. Next number:
caiso-262.**
