# PRECOMMIT — caiso-267: turn caiso-266's belly **conduct** inference into a measurement, or ledger it

**Session caiso-267, 2026-09-09.** Branch `claude/busy-volta-u6dlvt`.
Keeper **`2026-09-06-caiso-260-b1-demand`** (`caiso260_demand_vintage`),
**CALIBRATED** (rubric v3.6, 8 scored, 0 FAILs, one ledgered C3c caveat).
CAISO holds the `complete` marker; the holdout freeze is tier-scoped to
locked_test only. **Every read in this session stays inside 2023–2025**
(rule 22 `[R-HOLDOUT]`).

**PUSHED BEFORE THE FIRST INSTRUMENT RUNS.** No corpus request has been
issued, no bid price has been read, and no probe script exists at the moment
this document is committed. caiso-266 §10 disclosure 1 recorded a late
precommit; this one is early, and the ordering is verifiable from the branch
history (this commit precedes every artifact this session produces).

---

## §0 — The object, restated exactly as caiso-266 left it

~1,000 h/yr (h6–h15, Mar–Jun weighted; **1,001 / 1,222 / 1,020 hours**)
in which the model is thermal-marginal at **$26–29** with dump **0.000 MW**
and the market cleared at **$7–10**. In **70.5 / 81.7 / 56.2 %** of them the
market cleared *below* the carbon+VOM cost of a CAISO CC burning **free gas**
($16.01 / $16.94 / $13.90 per MWh; the keeper charges CARB at
$33.03 / $35.23 / $28.06 per tonne). On the bench's own 85-plant CAMPD panel
reality runs **7,204 / 7,080 / 5,952 MW** of gas online at **0.349 / 0.373 /
0.383** loading for the same energy the model makes from ~2–3 GW.

caiso-266 §8's conclusion — *"reality's belly is priced by price-taking supply
below its own cost floor"* — is **inference from two measured numbers** (its own
disclosure 5), never a reading of anyone's bids. This session tests it against
the bids, or says it cannot be tested.

## §1 — What is already settled and is NOT re-opened (DO-NOT-REDO)

Carried from caiso-266 §11 and the CAISO shard; nothing below is re-tested:

* the **renewable-FLOOR family** (floor depth, a graduated curtailment curve,
  `renewable_keep_running_value`) — dead, caiso-266 §4;
* the **offer-LEVEL door** on the caiso-254/255/257 classifier — closed,
  caiso-266 §7; re-opens only on a move in the MEASURED surface;
* **local curtailment** / `caiso_fsno_subzonal_topology` (R) — moves this
  residual the wrong way, caiso-266 §9 #1;
* the **DSW→CA corridor** — closed on measured volume (the model over-imports
  +1,627 / +1,715 / +1,608 MW in the carrying hours), caiso-266 §9 #2;
* **storage** — caiso-256's fence, caiso-266 §9 #3;
* **Panoche CT volume** — declared permanent residual (caiso-261), and the
  §2 wall below is why it stays one;
* the **hod 22–23 import** object — closed as data-intake (caiso-261);
* the **EIA-930 `NG: NG` basis trap** — caiso-266 §5.1. Every gas comparison
  in this session is made on the committed **85-plant CAMPD bench panel**, never
  on the CISO balancing-authority aggregate.

## §2 — The instrument, and the two walls it is already known to hit

**Instrument:** the **thermal side** of CAISO OASIS `PUB_DAM_GRP` "Public Bid
Data" — every scheduling resource's as-submitted DAM bid: full piecewise energy
curves (cumulative-MW / price breakpoints), **self-schedule MW**, AS bids.
90-day publication lag (CAISO tariff §6.5.2.2). caiso-178 landed the storage
side; caiso-231/242/254/255 landed the gas *classification* on a different
(CAMPD) instrument. **Nobody has read what CAISO's fleet actually bids at Pmin
in the solar belly.**

Two walls are already adjudicated in this repo and this session accepts both
rather than trying to route around them:

* **caiso-150 §B — the masking wall.** `RESOURCEBID_SEQ` is masked and there
  is **no public crosswalk to a named unit**. No unit-level attribution is
  attempted, and no plant (Panoche included) is named from this corpus.
* **caiso-150 §H — the self-schedule direction wall.** Economic curves are
  classifiable import/export by monotonicity; **self-schedules are not**. No
  import/export split of self-schedule MW is attempted by any route.

**Rows are RLE-expanded before any hourly statistic** (caiso-152; the parser
`scripts/lib/dam_public_bids/caiso.py::parse_day` already does this — keying on
the start stamp alone carried only 36 % of real curve-hours).

## §3 — PHASE 0, ZERO COST: the funding statement (rule 29 `[R-SCREEN]` step 0)

The corpus payload is **gitignored and stripped from history** — recovery is
**re-fetch only**. Before any fetch this session states, from
`data/raw/caiso-public-bids/README.md` and the caiso-261 card-3 charter:

* **Coverage:** 2023–2025 = **1,096 trade dates**; caiso-178 fetched **1,095**
  of them. **Hole rate 1/1,096 = 0.091 %** — the single miss is **2023-06-01**,
  a genuine OASIS archive hole (`ERR_CODE 1000` XML inside a valid zip), not a
  throttle failure.
* **Cost of the FULL corpus:** 1,096 requests at the ≥ 6 s OASIS
  acceptable-use throttle = **≈ 110 min of wall clock**, **422 MB** on disk
  (caiso-178 measured; the caiso-261 card quotes 0.5–0.9 GB). caiso-178 measured
  **zero rate-limit failures and zero retries** at that spacing.
* **Already funded, for a sibling question.** Owner card 3, caiso-261
  (`ASSESSMENT-caiso261-complete-declaration-2026-09-06.md` §3) **FUNDED** this
  same corpus as the G-26 / audit C-6 closure — the *intertie economic* limb.
  That charter is **not** this session's, and this session does **not** execute
  it; but the corpus's cost has already been put to the owner and accepted once.
* **This session is a NEW spend, because the container is ephemeral.** The
  caiso-261 fetch has not been run; nothing is on disk (`data/raw/caiso-public-bids/`
  holds only `README.md`). Anything fetched here dies with the container.

**The fetch is therefore surfaced to the owner as a decision before it runs,
with two sized options** (the sizing itself costs nothing and is pre-registered
here so the choice cannot be made by what the data says):

| option | days | requests | wall clock | disk |
|---|--:|--:|--:|--:|
| **A — stratified sample** (every 7th calendar day, 2023-01-01 → 2025-12-31) | 157 | 157 | **≈ 16 min** | ≈ 60 MB |
| **B — full corpus** (the caiso-261 card-3 scope) | 1,096 | 1,096 | ≈ 110 min | ≈ 422 MB |

**Option A's day grid is fixed HERE and is residual-blind**: a fixed 7-day
stride from a fixed anchor (2023-01-01), which covers every calendar month and
— because 7 divides the week — is then *offset-corrected* by taking stride 7
with a rotating +1-day offset each year (2023 anchor Jan 1, 2024 anchor Jan 2,
2025 anchor Jan 3) so all seven weekdays appear. **No day is chosen by its
price, its residual, or its month.** A sample of 157 days carries ~50 belly
hours/day × ~1,300 resources ≈ 10⁷ resource-hours, which is not the binding
constraint on any statistic below.

**A single 1-day REACHABILITY PROBE (2024-04-10) may run before the funding
answer.** It is pre-registered here, it is one request and ~0.5 MB, and it
reads **only**: does a zip return, its byte size, its row count, and its
column set. **No price, no MW and no statistic is read from it.** Its sole
purpose is that a cost estimate for an unreachable endpoint is worthless — if
OASIS is unreachable through this environment's proxy the honest answer is
"the corpus cannot be recovered", which is §7's REFUSED branch.

## §4 — The population: **BELLY**, defined structurally and price-blind

Fixed here, before any bid is read, and deliberately **not** caiso-266's
`regime G ∧ actual < $20` cut (which is price-informed and would make every
statistic below circular):

* **BELLY = operating hours beginning 06:00–15:00 Pacific Prevailing Time**
  (h6–h15 local, ten hours/day), **every day of 2023, 2024 and 2025.** This is
  the CAISO net-load belly on the clock, nothing more.
* **DEEP-BELLY** (reported alongside, never substituted): BELLY hours whose
  **measured** CISO net load (EIA-930 `Demand` − `NG: SUN` − `NG: WND`) is below
  that year's own **p20** of BELLY net load. Purely physical; no price enters.

Month and hour breakdowns are **reported** so a reader can see whether the
Mar–Jun concentration caiso-266 measured reproduces. The conclusion is stated on
BELLY, with DEEP-BELLY as the robustness leg.

## §5 — The measurements (T0–T4), fixed before any price is read

**T0 — census, price-blind.** Days returned, hole rate, resources per hour by
`RESOURCE_TYPE`, offered MW, self-schedule MW. Confirms the corpus is what the
README says.

**T1 — the price-insensitive block (THE LOAD-BEARING STATISTIC).** Per BELLY
hour, over `product = EN`:
  `PI_MW = Σ self_sched_mw  +  Σ economic curve MW offered at price ≤ $0`,
against **metered CISO demand** for the same hour (EIA-930, the same extract
caiso-266 used). Reported: median over BELLY hours of `PI_MW`, of
`PI_MW / demand`, and the share of BELLY hours with `PI_MW ≥ demand`.
**Self-schedule MW carries no price at all**, so this leg is price-blind on the
self-schedule side by construction.

**T2 — the as-bid stack, and the marginal rung.** Per BELLY hour, build the
cumulative as-bid supply curve (self-schedule MW at −∞, then every economic
breakpoint by ascending price, RLE-expanded, volume convention exactly
caiso-178's: price `p_i` applies on `[mw_i, mw_{i+1})`), and read:
  (a) MW offered at ≤ $0, ≤ $16 (caiso-266's zero-fuel CC carbon+VOM floor),
      and ≤ $26 (the model's own belly λ);
  (b) the **price of the marginal rung at metered demand**.

**T3 — validation, out-of-construction.** T2(b) vs the committed hourly
**DA** actual (`actual_lmp_hourly_CAISO.parquet`, `da` column) over BELLY hours.
Reported: Pearson r and median absolute error.

**T4 — gas attribution, CONTAMINATION DECLARED BEFORE THE ANSWER.** A
price-blind thermal subset: `RESOURCE_TYPE = GENERATOR`, never
withdrawal-capable (caiso-178's S1/S2 stages, reused verbatim, not re-cut), and
a **flat top breakpoint** — within-day coefficient of variation of the curve's
maximum MW < 0.15 (thermal Pmax is flat; a VER's traces its forecast).
**This subset necessarily also contains hydro, geothermal and biomass**, every
one of which bids at or near zero fuel cost, so **every contaminant it can admit
biases the measured bid DOWN — i.e. toward the conclusion this session expects.**
T4 is therefore **reported, never load-bearing**: no decision in §6 rests on it,
and a low T4 number is treated as uninformative rather than as evidence.

## §6 — DECISION RULES, fixed before any price is read

Read on **BELLY**, in **≥ 2 of the 3 training years**:

* **MEASURED → LEDGER.** `median(PI_MW / demand) ≥ 0.85` **AND** T2(a)'s
  ≤ $16 offered MW ≥ metered demand. That is: the belly clears inside a block
  of supply offered at or below the cost floor of the cheapest CARB-charged
  CAISO gas unit. The object is then **measured, not inferred**, and the honest
  outcome is a **ledgered model-class limitation for a cost-based LP** —
  *no lever, no `ScenarioConfig` field, no LP, no keeper change.*
* **LIVE → REPORT AND STOP.** `median(PI_MW / demand) < 0.85` **AND** the T2(b)
  marginal rung is **at or above** the model's own belly λ ($26–29). caiso-266
  §8's inference would then be wrong and the object re-opens — but this session
  **still selects no mechanism**: it files the falsification and stops, so that
  no lever is ever chosen by the measurement that motivated it (rule 1
  `[R-STRUCT]` condition (c)).
* **INDETERMINATE.** Either wall bites — T3 fails its floor (`r < 0.40` **or**
  median absolute error > $25/MWh in ≥ 2 years, i.e. the reconstruction is not
  faithful enough to speak about the margin), **or** the corpus cannot be
  recovered. Report as unmeasurable and ledger the object from caiso-266's
  evidence, naming what a valid instrument would need (the caiso-221 precedent:
  *"the residual is attributed and no admissible representation exists"* is an
  acceptable answer).

The rules are symmetric in cost — every branch ends the session as a
measurement — so none carries an incentive. **No band multiplier is used,
swept, or proposed.** No value anywhere below is chosen by whether a criterion
passes.

## §7 — If the fetch is REFUSED or the corpus cannot be recovered

State it plainly and **ledger the object from caiso-266's committed evidence**:
the belly residual is attributed (composition measured, four candidate families
killed, the carbon-floor arithmetic verified against the keeper's own
`run_config.json`) and no admissible in-model representation exists at this
grain. That is the outcome, not a failure to reach one.

## §8 — Governance

* **Rule 22 `[R-HOLDOUT]`** — identification on **2023–2025 only**. The corpus
  fetcher's own `DEFAULT_YEARS` is `(2023, 2024, 2025)`; no 2022 or 2019 day is
  requested by any option above. 2022 is **not** touched, not even as a re-test,
  because nothing here produces a mechanism to re-test.
* **Rule 29 `[R-SCREEN]`** — zero-LP phase 0 first (§3). **No screen year is
  named, because no arm exists**: every §6 branch ends without a mechanism. If a
  future session earns one, its screen year is named in *its* precommit, chosen
  by the mechanism's own measured footprint and never by the residual.
  **G-CTRL form 4** — the keeper's committed bundle is the control; **no control
  solve**. G-DRIFT is owed only if a solve is earned; caiso-265 measured the
  CAISO backcast path inert to HEAD drift and no solve is planned.
* **Rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — the authorized band-multiplier
  channel is **available and deliberately unused**. No adder, haircut, offset,
  load proxy or gas discount is proposed by any branch.
* **Rule 31 `[R-RETAIN]`** — nothing solved is deleted. No bundle is expected;
  if one appears it is gitignored, never `rm`'d, and the promotion question is
  surfaced explicitly before the session ends.
* **Rule 15 `[R-DASHBOARD]`** — anything solved is registered. Nothing is
  expected to be solved.
* **Rule 28 `[R-MECH-MATRIX]`** — the CAISO shard is touched only if a cell's
  evidence or verdict actually moves. Expected: an evidence append on
  `gas_offer_curve_tranches` / `measured_offer_surface`, no verdict move.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no committed derive is re-run or re-cut.
  caiso-178's classifier stages are **reused verbatim** in T4, never re-tuned.
* **The caiso-265 §4 `rt_lw` retrofit stays INERT.** No CAISO run covering 2022
  is produced here, so the bench part is not rewritten and 2022's C3a stays at
  +21.1 % as scored. A future 2022 re-solve moving it to +13.3 % **with no code
  change in its diff** is that landed retrofit, **not a regression**.

**Next number: caiso-268.**
