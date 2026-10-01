# PRECOMMIT — nyiso-243: the chartered availability intake, and the kill test it must survive

**Session** nyiso-243 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container**).
**Date** 2026-09-20. **Base** `origin/main` at `48151074`.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle `results/calibration/nyiso241_ctcommitted_span`, years {2022, 2023, 2024, 2025}. **UNCHANGED by this document.**
**Charter** `docs/RESULT-nyiso242-cc-winter-refused-and-the-intake-charter-2026-09-20.md` §2.5.
**Object** the missed RT price tail, worth **$5.44/MWh** on 2022 (`FINDING-nyiso242-…` §2); its winter cluster needs ~**4,716 MW** of model-believed-available capacity to not be there (§3.2).

**This document is written and committed BEFORE any price-conditioned number is
computed, so the gate cannot be written to fit the result.** What had been
computed when it was written: the corpus exists, its schema, its row counts, and
an unconditioned January-2022 total (mean 33,002 MW offered, range 30,410–35,525).
No window, no price join, no verdict.

---

## 1. THE SOURCE — NYISO MIS **P-27, "NYISO Bid Data"** (masked generator bids)

The charter's requirement is the whole point of it: *"The intake must state
AVAILABILITY, not OPERATION. CAMPD meters what ran."* P-27 does.

| | |
|---|---|
| endpoint | `https://mis.nyiso.com/public/csv/biddata/<YYYYMM01>biddata_genbids_csv.zip` |
| auth | none |
| archive | monthly, **1999-11 → present** |
| grain | one row per **masked generator × hour × market** |
| markets | **DAM** (day-ahead bid) and **HAM** (hour-ahead / RTC bid, resubmittable ~75 min out) |
| 2022 scope | 332 masked gens, 182 masked bidders, 720 hourly stamps/month, ~390 k rows/month |
| fetched | 2022–2025, 48/48 archives, 172 MB, `scripts/data/fetch_nyiso_bid_data.py` |

**The availability field is `Upper Oper Limit` (UOL)** — the MW the resource
itself told the ISO it could produce in that hour. Beside it: `Emer Oper Limit`,
`Fixed Min Gen MW`, the 12-block economic bid curve, start-up and min-gen costs,
self-commit schedule, and the resource's own **ancillary-service offers**
(10-min non-synch / spin, 30-min non-synch / spin, regulation).

**Why this source and not the others the charter listed.** NYISO's P-54A/B/C
outage reports are **transmission-line** outages (verified: the `outSched`
archive's rows are `FARRAGUT_345KV_5W`, `RAMAPO___345KV_35-4500-5` — line, bus
and breaker facilities, no generators). P-15 *Generation Maintenance Report* is
a genuine fleet-wide forced-plus-planned outage MW series — **but it is a
31-day forward snapshot with no archive**, so it cannot reach 2022. P-27 is the
one public NYISO product that states per-resource availability and keeps history.

**What this source cannot do, stated at the gate.** `Masked Gen ID` has no
published crosswalk to a PTID or a plant, and the file carries no zone, no fuel
and no class. **It can key a fleet- or cohort-level availability measurement; it
cannot key a per-unit derate.** Any mechanism built on it must be honest about
that, and this PRECOMMIT does not assume one is buildable.

**Rule 13 `[R-MEASURED]` admissibility.** An offered upper operating limit is a
measured market/physical availability statement; the identical construction
regenerates for any year from the same public archive and responds to changed
conditions. It is an admissible input. It becomes inadmissible the moment its
magnitude is set by the price residual (rules 1 / 13) — which is what §3 exists
to prevent.

---

## 2. THE CONFOUNDER THAT KILLED THE PREDECESSOR, AND WHY THIS SOURCE SEPARATES IT

nyiso-242 §2.3 refuted the CAMPD census because a unit metering zero in a
high-price hour has three candidate causes and CAMPD separates none of them:
(1) genuinely unavailable, (2) not committed day-ahead, (3) **available and
being held as reserve**. Measured, the CAMPD fleet sat at a flat ~50 % of its own
ceiling across *every* price condition — a coincidence factor, not a signal.

P-27 separates all three by construction:

* (1) is `Upper Oper Limit` — the unit's own statement, not an inference;
* (2) is the DAM/HAM split — HAM is resubmitted ~75 min ahead, so a derate that
  appeared after the DAM close is visible in HAM and absent from DAM;
* (3) is the AS-offer block — a CT held as 10-minute reserve carries a positive
  `10 Min Non-Synch MW`, and is therefore demonstrably **available**.

---

## 3. THE PRE-REGISTERED KILL TEST — BINDING, AND IT BINDS BEFORE ANY SOLVE

The charter's bar, verbatim: *"the derived derate must **deepen with price**,
more again in DA-anticipated hours than the flat ~50 % baseline; flat across
price conditions = refused at the gate."* Operationalized here, with every
threshold fixed now:

### 3.1 Construction

Per hour *h* of 2022 (and, as a replication, 2025), on the model's own
chronological EST 8760 calendar (`derive_actual_lmp._std_hour_index`,
`_STD_TZ["NYISO"] = Etc/GMT+5`; the P-27 stamps are UTC — validated by the
January file spanning `01JAN:05:00 → 31JAN:04:00` and the July file, which must
span `01JUL:04:00 → 01AUG:03:00` if and only if the stamps are UTC):

* `U_DAM(h)`, `U_HAM(h)` = Σ over masked gens of `Upper Oper Limit`;
* windows are the **actual** hub series `actual_lmp_hourly_NYISO.parquet`
  (`rt`, `da`) — the same series the C3c gate counts;
* the **baseline is within-season**, because a shoulder-month maintenance
  trough is not a cold-snap signal: winter windows are compared against
  ordinary Jan/Feb/Dec hours, summer against ordinary Jun/Jul/Aug hours, where
  "ordinary" is that season's hours with `rt` below the season's median.

### 3.2 Leg 1 — DOES IT DEEPEN WITH PRICE? *(self-normalized; uses no model quantity at all)*

The DA price ladder of nyiso-242 §2.3, reproduced exactly so the two
instruments are comparable: `DA > $300`, `> $200`, `> $150`, `> $100`; plus
`RT > $300 & DA-anticipated` against `RT > $300 & DA-surprise`; plus the 100
missed tail hours; each against the within-season ordinary baseline.

> **PASS** requires BOTH:
> **(a) magnitude** — median offered availability in the extreme-price window is
>   **≥ 1,000 MW BELOW** the within-season ordinary baseline. 1,000 MW is ~21 %
>   of the 4,716 MW object; below it the mechanism cannot matter even if real.
> **(b) monotonicity** — the deficit is **non-decreasing across the DA ladder**
>   ($100 → $150 → $200 → $300), i.e. it deepens with price rather than sitting flat.
>
> **REFUSED AT THE GATE**, with no solve and no shard, if the deficit is
> **< 1,000 MW**, or is **wrong-signed** (availability *higher* in extreme
> hours), or is **non-monotone** across the ladder. This is the same
> `G-NOCONTRA`-style bar caiso-186 used and the same one nyiso-242's own design
> failed.

### 3.3 Leg 2 — DOES IT REACH? *(the magnitude leg, against the model)*

Total measured offered availability against the keeper's **own believed-available
fleet** in the same hours (fleet-only rebuild, zero LP, the
`nyiso242_tail_reachability.fleet_state` path). The comparison is
whole-fleet-to-whole-fleet, since masking forbids a thermal-only cut on the
measured side.

> **PASS** requires the measured-minus-believed deficit in the winter cluster to
> exceed its within-season ordinary-hour level by **≥ 1,000 MW**. Reported at
> full magnitude either way, and reported **against the 4,716 MW the object
> needs** so the reader can see the fraction rather than a bare number.

### 3.4 Leg 3 — THE RESERVE CONTROL *(diagnostic, not a gate)*

Of the capacity offered-but-not-dispatched in the missed hours, how much carries
a positive AS offer? This cannot pass or fail the intake; it is reported because
it is the quantity that explains nyiso-242's flat 50 %, and a successor will
otherwise re-derive it.

### 3.5 What a PASS would and would not authorize

A PASS authorizes **designing** a mechanism and bringing it back for a screen.
It does **not** authorize arming one, and it does not by itself make one
buildable — §1's masking limit stands whatever the numbers say. A mechanism
whose magnitude came from the price residual rather than from these measured MW
is refused under rule 1 `[R-STRUCT]` however well this test goes.

---

## 4. EXPECTED VALUE, STATED UP FRONT

The charter's own words: *"A successor should expect to refute rather than to
arm."* The prior is unfavourable — the sub-5-day CAMPD outage family peaks at
2.4 GW against a 4.7 GW requirement, and its ST_GAS leg (2,080 MW of the 4,716)
is closed by the `NYISO.js:121` blanket DO-NOT-REDO. This intake is worth its
cost because the object is worth **$5.44/MWh** and every other route to it is
foreclosed, **not** because success is likely.

---

## 5. GOVERNANCE

* **Rule 28 `[R-MECH-MATRIX]` (a)** — the NYISO lever queue and the DO-NOT-REDO
  set were read first. Nothing in the closed set is re-tested: this is a **new
  data source**, never intaken in this repo, not a re-run of
  `unit_outage_short_windows` / `temp_dependent_derate` /
  `cc_winter_capability_basis` / any ST_GAS availability lever. **No cell moves
  on this document** — no mechanism has been tested.
* **Rule 32 `[R-SHARD]` (a)** — zero LP; the only model-side call is the
  fleet-only rebuild, which enters no LP.
* **Rules 21 / 24** — no `ScenarioConfig` field, no new literal, no tunable.
  The thresholds in §3 are **gate thresholds for this session's decision**, not
  model parameters, and they are fixed here rather than chosen later.
* **Rule 31 `[R-RETAIN]`** — nothing deleted.
* **Rule 15 `[R-DASHBOARD]`** — no run produced; the keeper's dashboard entry is
  untouched.
* **Corpus retention** — the 172 MB payload is **gitignored** under the
  corpus-conversion class (`docs/bloat-removal-plan-2026-08.md` §4); the tracked
  record is `scripts/data/fetch_nyiso_bid_data.py` + `README.md` +
  `SHA256SUMS.txt`, and re-fetch is the recovery route.
