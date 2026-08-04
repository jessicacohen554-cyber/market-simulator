# FINDING — xiso-4: the shared-stem backlog was CLOSED BY xiso-3 MID-SESSION; this session VERIFIES it independently and files ONE new live-but-mislabelled lever

**Date:** 2026-08-04 · **Lane:** cross-ISO hygiene · **Base:** `origin/main` @ `fe90fb8f`
**Pre-registration:** `PREREG-xiso4-cross-iso-shared-stem-2026-08-04.md`, committed before
any matrix byte was written and before the collision was known.

**Zero registrations made. Zero cells minted. Zero matrix bytes written. No LP, no solve,
no year touched, no keeper, default, band or derive script moved.**

**Keepers, re-read from the shards at `fe90fb8f`, ALL UNCHANGED:** ERCOT
`2026-08-03-ercot158-pool-arm` · CAISO `2026-08-04-caiso164-zonal-loss-surface` · PJM
`2026-08-03-pjm-151-seam-envelope` · MISO `2026-08-04-miso-124-dualfuel-rearm` · NYISO
`2026-08-03-nyiso-119-seny-increment` · NEISO `2026-08-03-neiso-caiso156-meter-screen`.
`complete` = {NEISO, NYISO, PJM}; `final` = EMPTY; **holdout freeze ACTIVE**, respected
trivially — nothing was solved.

> The handoff quoted MISO's keeper as `2026-08-04-miso-122b-scope-gate`. The shard read
> `2026-08-04-miso-124-dualfuel-rearm` at session start and still does. Re-read, not assumed.

---

## §1 — headline: the task was already done, by a session running in parallel

**The cross-ISO shared-stem backlog is CLOSED, and this session did not close it.**

`xiso-3` (`de247065`, "close the cross-ISO shared-stem backlog on 19 existing rows", PR
#3442/#3444, merged ~04:56 UTC) registered **all 45** shared fields — 54 (ISO, field) pairs,
**nine** armed in two ISOs at once — as literal sub-scalar entries on **19 existing rows'
`def:` fields, zero new rows, zero cell mints**. It also landed `8389027e`, a standing
anchor-resolution checker plus the repair of **161 stale line anchors** (163 of 167 did not
resolve) — the tooling nyiso-121 filed as a suggestion rather than building.

Main moved `d7363b0e` → `fe90fb8f` while this session's pre-registration was being written;
the collision surfaced on the first push attempt, before any edit. **The correct response to
finding your lane already closed is to verify it and stop, not to re-do it**, so that is
what this session did.

### The measured state at `fe90fb8f` (re-swept here, byte-identical to the committed sweeps)

| ISO | family | absent | prose-only | armed-no-cell | shared-gap | live-but-invisible |
|---|---|---|---|---|---|---|
| ERCOT | 86 | 0 | 0 | 0 | **0** | 2 |
| CAISO | 62 | 0 | 0 | 0 | **0** | 1 |
| PJM | 35 | 0 | 0 | 0 | **0** | 0 |
| MISO | 25 | 0 | 0 | 0 | **0** | 3 |
| NYISO | 41 | 0 | 0 | 0 | **0** | 0 |
| NEISO | 20 | 0 | 0 | 0 | **0** | 0 |

Ratchet `mechanism-matrix-gaps.json`: **both** blocks zero for all six.
`scripts/check_mechanism_matrix.py`: **PASS** — integrity OK; anchors 178 field + 43 row +
99 path, **0 unresolvable**; keeper stamps match every shard.

**The surviving live-but-invisible entries are exactly the six this session's PREREG §4
declared OUT of scope**, all for the same stated reason — armed on **no** keeper: ERCOT
`ercot_gas_commitment_bridge` (an ISO-stem field the stem-aware family census already counts
covered; it shows here only because the `live_but_invisible` metric's literal-match leg is
stem-blind — a metric asymmetry, not a gap) and `retirement_years_coal`; CAISO
`forecast_xyear_warmstart`; MISO `retirement_years_coal`,
`federal_ces_ccs_capture_fraction`, `coal_bit_committed_takeorpay`.

## §2 — the independent cross-check, and what it is worth

This session derived its own home-row map from the code before seeing xiso-3's — that is
what PREREG §5 is, and the commit timestamp is the evidence. Comparing the two:

**43 of 46 homes agree exactly.** The three that differ, with an honest read of each:

| field | xiso-4's home | xiso-3's home | assessment |
|---|---|---|---|
| `oil_primary_bin_fuel` | `dual_fuel_switching` | `use_campd_bins` | **xiso-3 is better.** The primary read site is `data/fleet/campd_bins.py:106` (it reprices *bins*), and `use_campd_bins` is `KKKKKK` so ERCOT's cell matches the arming; `dual_fuel_switching` reads `U` for ERCOT, which would have created a leg mismatch. |
| `gas_hh_monthly_shape` | `gas_monthly_actuals` | `gas_daily_shape` | **xiso-3 is better on the same ground.** Both are defensible on mechanism (this is the monthly-shape sibling of a level swap *and* of a daily shape), but `gas_daily_shape` is `KKKKKK` and matches ERCOT's arming, where `gas_monthly_actuals` reads `G`. |
| `cc_outage_derate_from_top` | `offer_curve_by_group` | `campd_outage_windows` | **A genuine toss-up, not worth reopening.** xiso-3 wins on call-site adjacency (`fleet/arrays.py:1786` sits in the availability chain); xiso-4 wins on mechanism content (it changes no outage MW — it re-fills offer tranches in heat-rate order). Both rows are `KKKKKK`, so the arming ISOs' cells match either way. |

**Two counts in this session's own PREREG were wrong and xiso-3's are right:** nine fields
are armed on two keepers at once, not seven (the three `ct_drag_*` scalars were collapsed in
prose but not in the table); and `coal_lignite_passthrough_sigmoid`, declared here as a "+1
adjacent addition", was already in xiso-3's 45.

**Convergent-and-corrected is the useful result.** Two sessions reading the same code
independently put 43 of 46 fields on the same row and disagreed only where both answers are
defensible — and where they disagreed, the *other* session's tie-breaker (match the row's
cell to the ISO's arming) was the better rule. That is real evidence the map is sound, in a
way one session's self-report cannot be.

**xiso-3 also reached this session's pre-registered O-1 and went past it.** PREREG §6 O-1
predicted CAISO's three CT-drag coefficients would prove unreachable behind
`ct_netload_drag=False`. xiso-3 §4 measured exactly that — and **four more ERCOT instances**
(`coal_prb_passthrough_floor`, `coal_lignite_passthrough_floor` / `_ceil`,
`coal_prb_follower_floor`, all behind their `False` sigmoid gates), each with a separating
positive control. O-1 is **PASS**, and the credit is xiso-3's. Independently re-derived here
from `data/fleet/floors.py:315` (the sole gate on the only consumers, `:324-326` and the
`:389-391` log branch) and `pipeline/backcast_config.py:1599, 1616-1618`.

## §3 — THE ONE NEW THING: `gas_st_startup_spread` is PROVABLY UNREACHABLE ON FOUR OF SIX KEEPERS, and its only non-`U` cell is one of them

This is the finding this session contributes, and it is **not on any record** — not
xiso-3's (whose PREREG names the row only as a home-row alternative it rejected, never
checking its reachability), not nyiso-115's which created it, not any calibration log.

**Why no census can see it.** `gas_st_startup_spread` has its **own row**, so
`coverage()` returns `own_row` and it is invisible to both halves of the rule-28(c) sweep
by construction. The ratchet reads zero and is *correct* to. This is the class of defect one
level past the one the whole census family exists to close: **not an unregistered mechanism,
but a registered one whose cell says something the code cannot support.**

**Measured on CONSTRUCTION — no LP, no solve, no dual** (the nyiso-115 G2 / nyiso-118
lesson, and the xiso-3 §4 pattern). Four facts, each a single read site:

1. `pipeline/backcast_config.py:1692` sets `gas_st_startup_spread=True` **unconditionally
   for every ISO**. All six keepers' `run_config.json` carry `True` (default is `False`,
   `scenarios.py:6645`).
2. `pipeline/solve.py:259` is its **only** plumbing: `gas_st_season_spread =
   config.gas_st_startup_spread`.
3. `model/commitment.py:321` is its **only** read:
   `st_spread = gas_st_season_spread and gen.plant_group == "ST_GAS"` — and it sits **nine
   lines after** `commitment.py:312-313`, `if gen.fuel_type == "gas_st" and not
   gas_st_startup_cost: continue`.
4. `data/fleet/eia860.py:1897` maps `"ST_GAS" → "gas_st"`, so **every** generator
   `st_spread` can select is dropped by that `continue`. The skip is total for exactly the
   class the flag applies to.

⇒ **Whenever `gas_st_startup_cost` is off, `gas_st_startup_spread` cannot change one LP
coefficient.** At the six current keepers:

| ISO | `gas_st_startup_spread` | `gas_st_startup_cost` (the gate) | reachable? | matrix cell |
|---|---|---|---|---|
| ERCOT | True | **True** | yes | `U` |
| CAISO | True | False | **NO** | `U` |
| PJM | True | False | **NO** | `U` |
| MISO | True | **True** | yes | `U` |
| **NYISO** | True | False | **NO** | **`K`** |
| NEISO | True | False | **NO** | `U` |

**The row is wrong in both directions at once**, which is why it is worth filing rather than
shrugging at:

* **NYISO's `K` — the row's only non-`U` cell — is armed-looking but dead.** Its `ev` reads
  "the NYISO cell records that the field is armed on NYISO's own designated keeper"
  (nyiso-115). It *is* armed; it is also unreachable, because the NYISO keeper leaves
  `gas_st_startup_cost` off. This is precisely the caiso-161 §5 / pjm-151 / nyiso-121 G-1 /
  xiso-3 §4 shape — **a `run_config.json` overstating what the solve read** — reaching a
  matrix cell for the first time rather than an unregistered scalar.
* **ERCOT's and MISO's `U` are the mirror error.** Both keepers arm the flag *and* its gate,
  so the mechanism is live in two published keepers whose cells say "never tested here".

**NOT ADJUDICATED, and no cell moved (rule 28(d), and this session's own kill rule K-3).**
Whether NYISO's cell should read `I`, whether ERCOT's and MISO's should move at all, and
whether an unconditional per-ISO default behind an ISO-gated flag is a rule 19
`[R-ONE-MECH]` or rule 26 `[R-DELETE]` question, all belong to lanes that may adjudicate
those ISOs. **A census may not.** Filed for NYISO's, ERCOT's and MISO's lanes.

**One caveat stated rather than buried:** this is a construction proof over the *committed*
call sites, not an A/B. The natural confirmation is xiso-3's own instrument — build the
markup twice at one HEAD with the flag on and off and assert `np.array_equal`, with a
positive control that separates (flip `gas_st_startup_cost` on). It is cheap and needs no
LP. It is **not run here** because the adjudication it would feed is not this lane's to
make; a lane that takes the cell should run it first.

## §4 — a second, smaller item: a mis-attributed INERT annotation

`scenarios.py:850` records, inside `_BACKCAST_ONLY_OVERLAY_FIELDS`:

> `"carry_operating_mothballs": "measured mothball state (INERT since 2026-07-17)"`

**The "(INERT since 2026-07-17)" belongs to a different field.** The comment block carrying
that phrase (`scenarios.py:1913-1927`) sits *between* `carry_operating_mothballs`
(`:1912`) and `historic_outage_overlay` (`:1928`), and its text is unambiguously about the
latter — "the facility-summed CAMPD outage overlay this flag gated was removed … so this
flag no longer changes a solve", with the `historic_outage_overlay` row already carrying `I`
in five columns. It attached to the wrong neighbour on the way into the dict.

`carry_operating_mothballs` is **not** inert: it is armed on the MISO keeper, it carries a
live `measured-physical` DOF-ledger entry in `miso124_dualfuel_B`'s
`calibration_attestation.json` ("OA-but-operating re-carry, vintage-status oracle",
`fleet.load_mothballed_but_operating`), and miso-88 measured its effect — Cottonwood 55358
carried at 1153.0/1149.1 MW in 2023/2024 rather than 580.4
(`docs/calibration-log/miso.md` §"Defect 2 … was NOT LIVE — already fixed").

**Reported, not fixed.** It is a one-parenthetical edit to a core file, and this lane
declared no code changes (K-5); a field description that mislabels a live measured overlay
as inert is a rule-13 `[R-MEASURED]` provenance hazard worth a moment of a MISO or
governance lane's time, not a census's unilateral touch.

## §5 — the pre-registered criteria, scored honestly against what actually happened

Criteria 1–3 were written to score **this** session's registrations. There were none, so
they are scored against **xiso-3's** work, verified independently at `fe90fb8f`, and that
re-basing is stated rather than hidden.

| # | criterion | result |
|---|---|---|
| 1 | shared-gap → 0 in all six | **PASS** (xiso-3's) — 14/5/18/17/0/0 → 0 everywhere, re-swept here |
| 2 | `check_mechanism_matrix.py` passes; ratchet 0 and only shrunk | **PASS** — integrity OK, 0 unresolvable anchors, keeper stamps match; both ratchet blocks 0 |
| 3 | every `cells:` byte-identical, zero mints, zero new rows | **PASS** (xiso-3's) — and **PASS trivially for this session**, which wrote no matrix byte |
| 4a | predicted `live_but_invisible` E 2 / M 3 / C 1 / P 0 / N 0 / Q 0 | **PASS — exact, all six.** Predicted in PREREG §7 against `d7363b0e` *before* the closure was known; measured at `fe90fb8f` after it |
| 4b | anti-leak invariant | **PASS, and re-derived independently.** Every (ISO, field) pair that left a list has that ISO's own keeper arming the field — verified against the six keepers' `run_config.json`, not asserted. Nothing dropped from an ISO's list merely because another ISO's registration named it: the nine double-armed fields sit on shared family rows carrying **both** ISOs' cells |
| 4c | family counts unchanged, 0/0/0 all six | **PASS** — no `ScenarioConfig` field added or removed by either session |
| 5 | O-1 and O-2 reported with pre-registered verdicts | **O-1 PASS, credited to xiso-3** (§2), which found four instances beyond the one predicted. **O-2 superseded** — the K-3 by-name census of un-adjudicated armed fields was to accompany registrations this session did not make; xiso-3's §4/§8 covers the same ground for the fields it registered |
| 6 | rule 27 blob verification on any ≥300-line push | **N/A by construction** — the only files this session pushes are two new markdown records; `mechanism-matrix.js` was never opened for writing |

**Criterion 4a is the one worth noticing.** It was written against `d7363b0e` as a
*prediction* about a closure this session intended to perform, and it names all six ISOs'
post-closure counts and the six surviving fields by name. Measured after a *different*
session performed the closure, it is exact. Two independent derivations landing on the same
six residual fields is a stronger check on the census boundary than either would have been
alone.

## §6 — what this session did NOT do

* **Registered nothing, minted nothing, wrote no matrix byte.** Not one of the 183 rows was
  opened. The `matrix_gap_census` audit row is untouched, NEISO's `O` on it included — that
  mint remains NEISO's lane's call (nyiso-121 §6.1, rules 25 / 28(d)).
* **Adjudicated nothing.** §3 and §4 are filed observations with citations, not verdicts.
  No verdict crossed an ISO boundary; the `gas_st_startup_spread` table reports each ISO
  separately from that ISO's own committed config.
* **Re-did nothing xiso-3 had done.** No duplicate registration, no competing home-row edit,
  no "improvement" to a merged closure. Where the two maps differed, xiso-3's stands and
  the reasoning is recorded in §2 rather than acted on.
* **Opened no MISO lever.** MISO's C7 COAL_PRB remains the sole failing criterion in that
  column and remains un-chartered: nyiso-121 §8 records that no MISO lever is tested,
  chartered or queued, and neither that census nor this one surfaced a never-adjudicated
  armable candidate. A new one needs its own identification from MISO's own data first
  (rule 25) — a solving lane's work.
* **Solved nothing.** No LP was built. No year outside 2023–2025 was solved, scored, read or
  intaken; the holdout freeze and both tier markers are untouched. Rule 15 is satisfied
  vacuously — no run was produced, so there is nothing to register on the dashboard (the
  ercot-156 / caiso-161 / nyiso-121 / xiso-3 precedent).

## §7 — what the next lane inherits

xiso-3 §9 lists three filed, un-adjudicated items (ERCOT's four unreadable coal scalars and
its `coal_nameplate_summer_derate` cell mismatch; CAISO's three unreadable CT-drag
coefficients; NEISO's available `matrix_gap_census` mint). **This session adds two, and
sharpens the standing risk:**

4. **`gas_st_startup_spread` (§3)** — unreachable on four of six keepers including NYISO,
   whose `K` is the row's only non-`U` cell, while ERCOT's and MISO's `U` sit on a
   mechanism their keepers actually run. Three lanes' calls, none of them a census's. The
   confirming A/B is cheap and LP-free and is specified in §3.
5. **`scenarios.py:850` (§4)** — a live measured overlay described as INERT, the annotation
   having attached to the wrong neighbouring field.

**The sharpened risk.** xiso-3 closed both halves of the rule-28(c) census and gated anchor
decay mechanically, and its §9 already notes the checker "cannot tell a *correct* literal
from a *wrong* one". §3 is the concrete next case: **both ratchets now read zero, and a
mechanism can still be mislabelled in the matrix without either of them moving.** The
remaining exposure is no longer *unregistered* mechanisms — it is **registered ones whose
cell asserts something the code contradicts**, and nothing in CI looks for that. The
gate-reachability probe xiso-3 built for §4 is the natural instrument; run across every
keeper-armed flag with a gate, it would be the third ratchet.
