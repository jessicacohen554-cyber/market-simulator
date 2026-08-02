# FINDING — nyiso-113: the rule-28(c) MATRIX-GAP SWEEP, three cells adjudicated with no solve, and the 227-3 phase reading inverted

**Date:** 2026-08-02 · **Scope:** NYISO, 2023–2025 · **Keeper under test:**
`2026-08-02-nyiso112-ramp-plus-peaker` (bundle
`results/calibration/nyiso112_combined_D`) · **Pre-registration:**
`PREREG-nyiso113-li-locational-reserve-2026-08-02.md` (committed and pushed
before either arm solved).

---

## §1 — the sweep: turning the nyiso-112 anecdote into an instrument

nyiso-112 promoted `nysdec_peaker_rule_availability` and recorded a standing
lesson for every ISO lane: *the exhausted-queue finding was true of the queue,
and the queue was incomplete — a solve-affecting field with no matrix row is a
mechanism nobody can see.* This session made that mechanical.

`scripts/probes/_nyiso113_matrix_gap_sweep.py` imports the live `ScenarioConfig`
(so the defaults are the *shipped* ones, not a parse of the source), reads every
`mechanism-matrix.js` row, and classifies each field three ways. The
classification detail that makes it correct rather than noisy: **the matrix's own
convention is that rows are ISO-NEUTRAL mechanism FAMILIES, and a per-ISO flag is
that ISO's leg of the family** — `nyiso_gas_commitment_bridge` is the NYISO leg
of row `gas_commitment_bridge`, whose `def` references it in the short form
`nyiso :2609`. Matching the literal flag name over-reports gaps for
correctly-registered legs, so the sweep matches on the **stem**.

| coverage | meaning | NYISO family |
|---|---|--:|
| `own_row` | has a row carrying its own cell + verdict | 20 |
| `prose_only` | mentioned, but only inside another row's text — **no cell** | 5 |
| `absent` | not mentioned anywhere in the matrix | **25** |

**17 of those are ARMED ON THE KEEPER with no cell anywhere.** Not sub-scalars of
a registered family — whole mechanisms: `nyiso_hydro_reserve_eligible`,
`nyiso_scr_edrp_reserve_eligible`, `nyiso_import_reconciliation`,
`nyiso_downstate_ct_gas_daily`, `nyiso_local_selfsupply`, `nyiso_firm_imports`.
Four of them are carried in the keeper's own DOF ledger, so they were *declared*
as parameters and simply never given a cell.

**Why CI never caught this, and why it generalises.** The
`check_mechanism_matrix.py` diff gate enforces rule 28(c) only for fields **added
in the same PR**. Every field predating the gate is structurally invisible to it.
That is a standing blind spot in every ISO column, not a NYISO accident, and the
sweep is cheap enough to run in any lane.

**Thirteen rows added this session** (rule 28(c)), plus one cell update. Verdicts
below are the sweep's *evidence*, not its authority — a census can mint a `U`
and nothing more; the `I` and `G` cells below each rest on their own measurement.

## §2 — `nyiso_east_reserve_families`: PROVABLY INERT, no solve spent

The published EAST rows the model omits (`east_10min_spin` 330 MW,
`east_30min_total` 1,200 MW, both $40/MW per ASM §6.8 items 2 and 12), built at
nyiso-84 as a rule-14 omission fix and **never armed in any bundle**.

A family row is `Σ_{z∈region} R[c,z] + shortfall ≥ requirement`. An armed family
with the **same reserve class**, a **subset** region and a requirement **at least
as large** therefore forces the candidate's row slack — its R-sum is a lower
bound on the candidate's over a smaller zone set. Both limbs are dominated:

| candidate | dominated by | margin |
|---|---|--:|
| `east_10min_spin` (330 MW, class 1, East) | `nyc_10min_total` (500 MW, class 1, NYC ⊂ East) | 170 MW |
| " | `east_10min_total` (1,200 MW, class 1, same region) | 870 MW |
| `east_30min_total` (1,200 MW, class 0, East) | `seny_30min_total` (1,300 MW, class 0, SENY ⊂ East) | 100 MW |

Corroborated on the keeper's own sidecars: the **max cross-zone reserve-dual
spread is exactly 0.0 in every hour of all three years**, so neither dominating
family has ever bound either. Adding these rows is structurally correct and costs
nothing; it also buys nothing, and that is the honest verdict rather than a
promotion claim. Cell `U → I`. The domination is arithmetic, not empirical — only
a change to the armed family set could reopen it (rule 28a).

## §3 — `measured_ramp_capability` (PJM `K`): INERT ex-ante, no solve spent

nyiso-110 §10 refuted the aggregate ρ·P **online binder**, not a measured-MW
**per-asset qualifier**, so the transfer deserved its own screen rather than
inheritance of that verdict. The screen the brief specified: the NYISO
reserve-eligible fleet's total 10-minute deliverable ramp is **12,318.4 MW over
352 of 460 units — 18.8× the 655 MW NYCA 10-minute spinning requirement** (9.4×
the 1,310 MW 10-minute total). A qualifier that reduces admissible headroom from
~19× the requirement cannot make the row bind, so the measured input cannot move
any dual. Cell `U → I`. It stays admissible as an accuracy improvement under
rule 14 if ever armed for its own sake; it is not a lever.

## §4 — `nyiso_li_locational_reserve`: the one candidate that clears the rule-19 gate

The brief's precondition: with the in-LP reserve-**formation** family exhausted
(nyiso-110), a locational requirement is a new lever **only if it can be shown to
bind where the NYCA aggregate does not** — measured before any solve. Four
measurements, all on NYISO's own data:

**(a) Not dominated.** No armed family is Zone-K-scoped. The smallest armed
regions containing Long Island are SENY `{Lower_Hudson, NYC, Long_Island}` and
East `{+Capital_Hudson}`, whose R-sums run over strictly more zones, so neither
implies `R[c, Long_Island] ≥ 120` or `≥ 540`. Both LI families are genuinely new
rows.

**(b) The nyiso-110 §10 refutation provably cannot reach a Zone-K row.** That
refutation's mechanism is that reserve-eligible **hydro**'s own capability keeps
the aggregate rows slack in every hour (the keeper carries
`nyiso_hydro_reserve_eligible=True`, unioning hydro into both classes). Measured
**by zone**, NYISO hydro is:

| year | Upstate_West | Capital_Hudson | **Long_Island** |
|---|--:|--:|--:|
| 2023 | 4,094.9 MW | 554.3 MW | **0.0 MW** |
| 2024 | 4,035.2 MW | 551.9 MW | **0.0 MW** |
| 2025 | 4,035.2 MW | 551.9 MW | **0.0 MW** |

Upstate Niagara/St-Lawrence hydro is physically incapable of supplying a Zone-K
requirement. The resource that makes the aggregate slack cannot satisfy this row.

**(c) ~~No locational family has ever bound.~~ RETRACTED — see §8.** The screen
cited a max cross-zone `reserve_price` spread of exactly 0.0 as evidence that
only the NYCA-wide families have ever priced. That statistic is **vacuous**: the
persisted `reserve_price` is a single system-level series broadcast identically
to every zone, so it is 0.0 across zones by construction and cannot observe a
locational dual at all. The claim is withdrawn.

**(d) Zone-K headroom can physically collapse.** Long Island total thermal
capacity is **5,146.5 MW** (quick-start 4,334.0 MW) against LI peak demand of
**5,054 / 4,925 / 5,537 MW** — 2025 peak demand exceeds Zone-K thermal nameplate
before any availability derate — and the 227-3 overlay removes a further 145.5 MW
of Zone-K quick-start inside the ozone window (4,334.0 → 4,188.5 MW). Headroom
goes to near zero in exactly the summer peak hours where nyiso-92 dated the
measured RT tail and nyiso-94 measured every model `>$300` hour.

The mechanism itself is a **rule 14 `[R-ACCURATE]` omission fix with zero free
parameters**: `li_10min_total` 120 MW all hours and `li_30min_total` 270 MW
off-peak / 540 MW on-peak, both at the published $25/MW (ASM §6.8 items 10 and
15), with the on/off-peak boundary resolving to the tariff's own MST §2.15
On-Peak calendar. Pre-registered as a single-delta A/B against a same-HEAD
zero-delta control; **K3 liveness routes a non-binding arm to INERT**, and §6 of
the pre-registration carries a binding no-tuning clause on the published levels.

*Arm result: §7 below.*

## §5 — the 227-3 phase reading, INVERTED by measurement

The session brief's plausible read was that the 2023-restricted units are small
upstate/LI GTs and only the 2025 phase touches binding downstate capacity. The
compliance file resolved against the model's own fleet says the opposite:

| phase | total restricted | Long Island | NYC | Lower Hudson |
|---|--:|--:|--:|--:|
| **2023-05-01** | **203.1 MW** | **145.5 MW (72 %)** | 37.8 MW | 19.8 MW |
| **2025-05-01** (increment) | **14.5 MW** | **0.0 MW** | 14.5 MW | — |

The 2023 phase is 93 % downstate and removes 145.5 MW *directly on Long Island*
(Shoreham 65.7, Glenwood 55.1, Port Jefferson 12.9, Northport 11.8). The 2025
increment is a single 14.5 MW NYC unit (59th Street GT1) — **Astoria 1 and Arthur
Kill GT1 are no-ops, absent from the fleet vintage**. So the phase that moved C3c
adds the *least* capacity and none of it in the zone where the tail lives.

**And the 2023 phase did not do nothing.** It moved **570 Long Island hours, all
inside the ozone window**, lifted the LI max from **400.07 → 503.74 $/MWh**, and
moved `>$250` from 7 → 10 hours. What it did not do is cross the **$300
threshold C3c counts** — its mass landed in [250, 275). A threshold statistic
cannot distinguish "the mechanism did nothing" from "the mechanism moved the tail
but not across the line", and here it is emphatically the second.

**2024 is the genuinely inert year, and it is inert for a specific reason.** The
overlay moved 274 hours, but the three highest LI hours (h4528–4530, early July)
are pinned at **$297.538777 in both arms — bit-identical, $2.46 below the gate**.
The mainland roof that year is $197.34. Removing 145.5 MW of Zone-K peakers does
not reach the next offer rung in those hours, so the year's entire C3c score
turns on a $2.46 gap. That is a knife-edge, not a structural absence, and it is
the sharpest available statement of what C3c is currently measuring at NYISO.

## §6 — reported, not acted on: three hygiene items

1. **`nyiso_gas_bridge_*` sub-scalars (8 fields).** The measured commitment
   parameters (CC 0.523 / ST 0.239 / CT 0.238 min-load; 21 / 13 / 2.0 h min-run;
   `startup`, `da_horizon`) are absent from the matrix by literal name but are
   substantively carried on the `gas_commitment_bridge` family row, whose note
   names *0.523/0.239 + min-run leg*. Per the checker's own escape hatch that is
   correct registration; the CT legs and the two boolean sub-flags are the part
   the note does not reach, and are filed here rather than minted as rows.
2. **`ct_committed_hr_override` / `ct_econ_hr_override` / `ct_peak_hr_override`
   = 1.1 / 1.2 / 1.4.** Armed non-default on **every** NYISO bundle, absent from
   the matrix, and absent from the keeper's DOF ledger by name. They are *not*
   an unledgered live DOF: the ledger carries `offer_curve_by_group`
   (identification: residual), and `CT_PEAKER` and `CT_CHP` both appear in that
   map, which the code documents as superseding the legacy triples. But the
   apply site (`fleet/assembly.py:575-582`) gates the triple on
   `group == "CT_CHP"`, so whether it is live depends on an interaction between
   two offer-curve parameterizations that this session did not fully trace.
   **Filed as an open trace item, deliberately not asserted either way** — and
   flagged as a candidate rule 26 `[R-DELETE]` re-armable knob, since a future
   arm that drops CT_CHP from `offer_curve_by_group` would silently re-arm
   1.1/1.2/1.4.
3. **`caiso_ra_min_load_frac = 0.26` on every NYISO bundle.** A CAISO-scoped
   field carried non-default in another ISO's config. Expected inert (the
   consuming mechanism is CAISO-gated), but it is exactly the shape rule 25
   `[R-ISO-SCOPE]` exists to prevent and it should not be riding NYISO's recipe.

## §7 — the arm: LIVE, small, and C3c-unchanged

Arms `nyiso113_control_A` / `nyiso113_lilocational_B`, registered as
`2026-08-02-nyiso-113-control-zerodelta` and `2026-08-02-nyiso-113-li-locational`.

| gate | result |
|---|---|
| **K1** one delta | **PASS** — exactly `{nyiso_li_locational_reserve: false → true}` |
| **K2** control integrity | **PASS, BYTE-IDENTICAL** — 0.0 MW over 122,640 class-hours in each of 2023/2024/2025 |
| **K3** liveness | **PASS on a corrected instrument** (see §8) — the family binds |
| **K4** scoping | **not testable as written** (see §8) |
| **K5** span | **PASS** — 2023–2025 in one bundle per arm; holdout freeze untouched |
| **P3** feasibility | **PASS** — zero slack and zero dump in every zone-hour, both arms |

**The mechanism is live, and it binds exactly where its own requirement says it
should.** Measured on the arm's own unit-hourly sidecar, Zone-K thermal headroom
falls below `li_30min_total`'s **hourly** requirement (270 MW off-peak / 540 MW
on-peak) in **exactly 5 hours of 2025 — h4193–4195 and h4217–4218** — and in
**0 hours of 2023 and 2024** once the published on/off-peak step is honoured (the
single sub-540 MW hour in 2024 is an *off*-peak hour where the requirement is
270 MW, and headroom there is 526 MW). The solved system reserve dual then moves
in **exactly those five hours plus five more** in 2025, in 2 hours of 2023, and
in **0 hours of 2024**. Those five 2025 hours are the June 24–25 event — the same
hours that carry the five highest Long Island prices in the keeper.

`li_10min_total` never binds: Zone-K quick-start headroom bottoms out at
596.8 / 490.7 / 379.7 MW, i.e. **3.2–5.0× the 120 MW requirement**, and is never
below it in any hour of any year.

**The price effect is small, and C3c does not move.**

| year | LI >$300 (measured) | control → arm | LI >$250 | LI max |
|---|--:|--:|--:|--:|
| 2023 | 10 | 3 → **3** | 10 → 10 | 503.74 → 503.74 |
| 2024 | 12 | 0 → **0** | 5 → 5 | 297.54 → 297.54 |
| 2025 | 42 | 14 → **14** | 19 → 19 | 483.37 → **489.62** |

The whole visible effect is **+$6.25 on the 2025 Long Island maximum** — which is
the $25/MW demand-curve tier doing precisely what its published value permits, no
more. Non-LI zones move by at most $1.78–2.28, the system-level reserve dual
propagating.

**Verdict: cell stays `O`, NOT promoted.** The pre-registration's kill gates
P1 (C3a band), P2 (C1) and P4 (C7/C8) require scorer output the replay path does
not produce — both bundles register `DETERMINATION: NOT-YET` with governance
UNATTESTED — so no promotion verdict is reachable from this session's evidence,
and claiming one would breach the pre-registration. What the mechanism now has is
a demonstrated liveness and a byte-identical control; what it still needs is a
scored keeper-candidate arm, not another identification. It remains a zero-DOF
rule 14 `[R-ACCURATE]` omission fix of a requirement NYISO publishes and the
model omits.

## §8 — two corrections this session owes its own record

**(1) The pre-registered K3/K4 instrument was invalid.** Both gates were
specified on the per-zone `reserve_price` column of `system_<year>.parquet`. That
column is built at `run_calibration_full.py:925` as a single `(T,)` system-level
series and written **identically into every zone's rows** at line 1028 — it has
no zone index. It is therefore 0.0 across zones *by construction* and cannot
observe a locational family's dual. Scored on it, the arm read "INERT — no LI
dual in any hour", which is an artifact, not a result; K4's "non-LI duals moved"
was likewise the system-level dual propagating, not a scoping violation. The
gates were re-run on the unit-hourly headroom and the solved dual's *timing*,
which is what produced §7. **The same invalidity retracts §4(c) of this finding
and the corroborating sentence in the `nyiso_east_reserve_families` matrix
note** — the domination verdict there is untouched, because it is arithmetic on
the family rows and never depended on a dual measurement.

**(2) The screen's capacity-vs-demand argument does not imply a headroom
collapse.** §4(d) reasoned from LI peak demand (5,537 MW) exceeding Zone-K
thermal nameplate (5,146.5 MW) to a collapse in Zone-K reserve headroom. That
inference is invalid for two reasons the measurement makes plain: reserve class 1
is **idle-allowed**, so the binding condition is "fewer than 120 MW of Zone-K
quick-start is *idle*", not "Zone K is short of energy"; and **Long Island
imports a large share of its own peak load**, so its local peakers never reach
the utilisation the nameplate comparison implies (82.2 / 84.0 / 90.6 % at each
year's own peak-price hour). **A capacity-vs-demand screen is not a headroom
screen for any importing zone with an idle-allowed reserve class** — that
generalises to every ISO and every locational reserve candidate.

**Standing gap, all six ISOs.** No bundle persists a **per-family reserve dual**:
`DispatchResult.reserve_price_by_family` exists in memory (it is what
`results/scarcity.py` consumes) and is discarded at persist time. So *no
locational reserve family's binding is observable from a committed bundle in any
ISO*. Every prior claim of the form "family X never binds", here or elsewhere,
rests on either the aggregate series or a re-solve. A per-family dual sidecar is
a prerequisite for adjudicating any locational reserve mechanism from bundles,
and it is cheap — the array already exists.

