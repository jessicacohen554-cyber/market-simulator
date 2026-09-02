# FINDING miso-200 — the outage extract MIS-ROUTES a mixed CC+ST facility's steam units onto its CC bin: the defect is REAL, TWO-SIDED and LARGE; the arm was killed at phase 0 on a proxy that over-fired, then SOLVED and PROMOTED on the owner's re-scoped bar with every gate silent (2026-09-02)

> **SUPERSEDING ADDENDUM (same session, appended after §1-§10 were written).**
> §§1-10 below were written when this session had refused to solve, and they say so.
> **That outcome was superseded in-session by an owner directive** — *"Is this a
> recommended keeper candidate? If so plz promote. If structural integrity improves
> but gates regress that may still be a keeper."* — which re-scoped the promotion
> bar and made the arm worth spending. The A/B was then solved end to end.
>
> **KEEPER AT CLOSE: `2026-09-02-miso-200-unitroute`** (bundle
> `results/calibration/miso200_unitroute_B`), promoted; `audit_keepers --iso MISO`
> PASS 0/0, independently re-verified by the `calibration-keeper-auditor` agent
> against the artifacts (0 failures, 0 repairs).
>
> **In the event NOTHING REGRESSED, so the re-scoped bar was not needed:** S-0
> BIT-IDENTICAL (9 sidecars, `max_abs_diff` 0.0), S-1 exactly one field, S-2 PASS,
> **K-1..K-5 ALL SILENT**, K-6 UNSCORED and disclosed. The gain is on **C8**: ST_GAS
> forced share **0.2002 / 0.2100 / 0.3187 → 0.1496 / 0.1520 / 0.2651**, with 2025
> crossing from ABOVE the 0.30 merchant budget (a grounded over-budget pass) to
> WITHIN it. The **K-1 risk named ex ante did NOT materialise**: CC_REGULAR-2024
> +6.748 → +7.075 and ST_GAS-2024 −7.698 → −7.854, no band exit anywhere — the §7
> capability bound (+3.3055 / −5.1916 TWh) was rigorous but very loose, the LP
> converting ~10 % and ~3 % of it. **No criterion status moves**; the determination
> is UNCHANGED at NOT-YET on `price_mean`, and **C3a-2025 is EXACTLY unchanged at
> −12.2745**, so nothing here is C3a-driven.
>
> **§5's L-3a KILL STANDS AS FIRED and is NOT renegotiated.** What licensed the
> solve was a *separable measurement*, not a reinterpretation: the fleet's ST_GAS bin
> at 1403 is EXACTLY the two units carrying those windows (742.6 + 722.8 =
> 1,465.4 MW) and at 2070 exactly one (59.0 MW), so a concurrent full stop means the
> bin is genuinely 100 % out — and availability is exactly **0.0000** in every one of
> the 1,728 / 552 / 144 and 24 / 72 / 24 overflow hours, which is the physically
> correct value. The overflow is a bookkeeping artifact with **zero dispatch
> consequence**; L-3a was a proxy for "the repair must not remove capacity that
> should be running", and measured, it never does.
>
> **A second defect, disclosed rather than absorbed:** on the FIRST scoring run K-3
> (D-4 conduct) and K-4 (D-1 shape) passed **VACUOUSLY** — a `--replay-bundle` solve
> writes no `legitimacy_diagnostics.json`, so the scorer compared empty against
> empty, and S-2's forced-share leg was unmeasurable. That is the same defect class
> this session's scorer was written to avoid. The diagnostics were generated for BOTH
> legs (D1=30, D2=23, D4=57 rows each) and the pair re-scored, at which point S-2,
> K-3 and K-4 became **real** PASSes. The promotion rests only on the re-scored run.
>
> §8's handed-on items stand unchanged — in particular the successor: the **ST-side
> denominator basis alignment**, which closes the two residual overflow cells.
> Records: `_miso200_ab_gates.json`, `scripts/gen_miso200_attestation.py`
> (n_entries 39, n_residual UNCHANGED at 2), runs `2026-09-02-miso-200-control` /
> `2026-09-02-miso-200-unitroute`.

**Session:** miso-200 (2026-09-02). **Keeper at open AND at close:
`2026-09-01-miso-198-oomlevel`** (bundle `results/calibration/miso198_oom_B`) —
**UNCHANGED. Nothing was solved, nothing promoted, nothing registered** (rule 15
`[R-DASHBOARD]`: no run was produced). **Charter:** the two-way fork offered by the
miso-200 prompt — the bid-side self-schedule form, or FINDING-miso199 §7a's plant-1403
availability cell. **The availability object was taken and the bid-side lever was not
built**; the fork and its five reasons were declared in writing, before any measurement,
in `PREREG-miso200-outage-routing-mixedgas-2026-09-02.md` §1 (blob `bbae3472`).

---

## 1. The answer, in one paragraph

`_resolve_unit_group` — the routing every CAMPD outage window passes through — short-circuits
on the FACILITY's group, and its own pjm-75 justification states the premise verbatim:
*"single-group gas facilities are byte-identical"*. But the facility group is
`group_by_code[plant_code] = g.plant_group` over the fleet, **last writer wins**, so at a
facility carrying two or more model gas bins the premise is **false** and every unit is
handed to whichever bin's fleet row happened to come last. **Exactly two MISO facilities
are in that state, and one of them is enormous**: Ninemile Point 1403 (ST_GAS 1,465.4 MW +
CC_REGULAR 649.5 MW, last writer CC_REGULAR) sends its two gas-STEAM boilers — units 4 and
5, CAMPD `unitType` "Tangentially-fired", 1,651.1 MW combined — onto the **649.5 MW CC
bin**. The signature is two-sided and both halves are wrong at once: the CC bin carries a
pre-clip removed share peaking at **2.588 / 3.556 / 2.553** and above 1.0 for
**5,640 / 6,192 / 4,920 hours a year**, so it runs at a mean availability of
**0.352 / 0.288 / 0.438** — while the ST_GAS bin that actually holds those boilers receives
**zero rows** and reads availability **identically 1.0**, so its 688 MW must-run floor
asserts straight through every outage. That **closes FINDING-miso199 §7a's open cell on
this session's own frozen structural line** (all three legs TRUE). The repair — gate the
short-circuit on single-gas facilities, fall through to the resolver's own per-unit
`unitType` routing — is built, registered, unit-tested and **verified to be an exact
single object: 116 rows change and the only column that changes is `plant_group`** (L-3b
PASS). **And the arm is then KILLED by L-3a**, the session's own frozen soundness line:
routing the boilers to their proper bin **creates** over-removal where there was none
(**(1403, ST_GAS) 1.13, (2070, ST_GAS) 2.00**), because the mis-routing was **masking two
further, independent, pre-existing defects** — a numerator/denominator basis gap that
`unit_outage_lp_capacity_basis` cannot reach (it is CC-only), and an adjacent-window
boundary-day double-count. **No solve was spent.** The routing repair is correct and is
landed default-off; it is **not sufficient alone**, and its composition partner is now
named exactly.

## 2. The charter fork, and what was NOT done

The prompt required exactly one of two objects. **The availability object was taken.** The
five reasons were declared before any measurement (PREREG §1) and none of them is a
result: the repair channel already existed for this exact phenomenon
(`outages._FLEET_GROUP_OVERRIDE` carries NYISO Ravenswood 2500 with a docstring describing
the identical symptom); it is an input-accuracy defect under rule 14 `[R-ACCURATE]` rather
than a new mechanism; it was the largest single defect on the record; rule 19
`[R-ONE-MECH]` is clean (availability is not a floor, so there is no stack-or-replace
question); and the bid-side form's only clear gain was C8 headroom on a criterion that
already PASSES, while its own miso-198 M-4 record declares its C3a face **DOWN in the
body** — against the keeper's sole failing criterion — and carries
`L4a_shape_faithful=false` with `profile_r_vs_measured_oom = NaN`, i.e. its shape leg is
**undefined for a zero-forcing form and was never actually tested**.

**No claim is made that the bid-side form is refuted.** It was not tested, not adjudicated,
and **its cell is not minted**. The rule-28(a) DO-NOT-REDO argument it would have needed
against MISO's `R`/`I` offer-level verdicts (miso-179 `R`, miso-180 `I`, miso-178 lever 1
`R`) **stays unwritten rather than stretched** — the charter's own stand-down instruction,
exercised rather than argued around. Those three verdicts are neither re-opened nor cited
as licensing anything.

**A correction to the charter's own citation, reported because a successor will follow it.**
The prompt cites "FINDING-miso198 §§3-4 … the M-4 design-form matrix, which is where form
(c) is specified". **The M-4 matrix is not in FINDING-miso198 at all** — neither the finding
nor `PREREG-miso198` contains the string. It lives in the docstring of
`scripts/probes/_miso198_stgas_oom_conduct_phase0.py` (lines 121-141), with its results in
`_miso198_stgas_oom_conduct_phase0.json` under `m4.forms.c`. miso-199 §8(1) passed the
mis-citation on and the charter inherited it. The content is real and unchanged; only the
address was wrong.

## 3. The cell entered, and why no verdict binds it

| MISO cell | verdict | binds? |
|---|---|---|
| `outage_artifact_provenance` | **`O` (open)** | No — open is the invitation, and §7 adds the first quantification it has ever carried |
| `unit_outage_lp_capacity_basis` | `U` | No — untested; §6 now names it as the composition partner and shows it does not reach ST_GAS |
| `campd_outage_windows` | `K` | No — the MECHANISM is not re-tested; the POPULATION it reads is repaired. miso-195 refuted a *fleet-grain remove-only cap* on a different source |
| `dam_availability_rebasis` | `R` (miso-85/86) | No — a different SOURCE |
| `mustrun_online_frac_per_year` | `R` (miso-172) | No — not touched; this is not a window lever |

## 4. N-1 / N-2 — the defect, measured (zero solve)

Instrument `scripts/probes/_miso200_outage_routing_phase0.py`, rule frozen in its own
docstring and **pushed + blob-verified at `c5d1aad1` before any adjudicating quantity**;
record `_miso200_outage_routing_phase0.json`.

**Satisfiability, which is what licenses the census.** The rebuilt 2023 ST_GAS floor equals
the keeper's own logged **9.9319 TWh** (the miso-199 regression test, kept verbatim), and
the **pre-clip removed-share reconstruction reproduces the production derate arrays
EXACTLY on all 121 bins** — N-2 needs the pre-clip share that `unit_outage_derate_factors`
hides behind its clip, and a reconstruction that did not reproduce production would be
measuring something else.

### N-1 — the mis-routing population

| year | multi-gas facilities | mis-routed units | **mis-routed MW (unique)** |
|---|---:|---:|---:|
| 2023 | 2 | 3 | **1,740.1** |
| 2024 | 2 | 3 | **1,719.1** |
| 2025 | 2 | 3 | **1,717.1** |

| facility | model bins | last writer | mis-routed unit | CAMPD `unitType` | extract → repaired |
|---|---|---|---|---|---|
| **1403 Ninemile Point** | ST_GAS 1,465.4 + CC_REGULAR 649.5 | CC_REGULAR | **4 (763.0 MW)** | Tangentially-fired | CC_REGULAR → **ST_GAS** |
| **1403 Ninemile Point** | " | " | **5 (895.1 MW)** | Tangentially-fired | CC_REGULAR → **ST_GAS** |
| **2070 Moselle** | ST_GAS 59.0 + CC_REGULAR 268.0 + CT_PEAKER 150.0 | CC_REGULAR | **3 (59.0 MW)** | Dry bottom wall-fired boiler | CC_REGULAR → **ST_GAS** |

**L-1a MATERIAL — clears the frozen ≥500 MW line in 3 of 3 years** (the line asked for 2).

### N-2 — the two-sided signature, on the incumbent extract

| year | **(1403, CC_REGULAR)** max pre-clip share | hours > 1.0 | mean availability | **(1403, ST_GAS)** coverage |
|---|---:|---:|---:|---|
| 2023 | **2.588** | 5,640 | **0.3521** | **ZERO rows — availability ≡ 1.0** |
| 2024 | **3.556** | 6,192 | **0.2877** | **ZERO rows — availability ≡ 1.0** |
| 2025 | **2.553** | 4,920 | **0.4384** | **ZERO rows — availability ≡ 1.0** |

**L-1b — the 1403 cell IS the mis-routing family, on THIS session's own line.** All three
frozen structural legs are TRUE: (i) `(1403, ST_GAS)` is zero-coverage in 2024; (ii) units
4, 5, 6A and 6B all carry February-2024 windows in the incumbent extract; (iii) units 4 and
5 route to `ST_GAS`. The charter's CAUTION is honoured: **miso-199's frozen L-X1b, which
missed its online-share leg by 5.7 pp, is nowhere cited as a passed test** — this
classification is structural (extract + fleet membership), not a threshold on a residual,
and it was frozen before it was computed.

**REPORTED AGAINST THIS SESSION'S OWN INTEREST — the over-removal signature does NOT
identify this family.** Over-removal is **widespread** at MISO: **238 bin-years** at
cap ≥ 100 MW carry a pre-clip share above 1.0, median max-share **1.128**, 22 of them at
≥ 2.0, and 1403-2024 ranks only **19th of 238 by hours-over-1** even though it holds the
single largest max-share (3.556). What identifies this family is the **routing census**,
which finds exactly two facilities. The share evidence corroborates; it does not define.
The remaining population is a different object (§6, §8).

## 5. The repair, and the KILL

`ScenarioConfig.unit_outage_mixed_gas_routing` (GATED, **default off**). The gate lives in
the **shared** `_resolve_unit_group`, so both derivers that use it inherit it: the ≥5-day
std extract and the declared-event maxgen extract move **together**, because a unit routed
to `ST_GAS` in one and `CC_REGULAR` in the other would leave the object half-repaired
(rule 19). The short-window layer is out of scope **by construction** (baseload COAL only,
so it carries no mixed-gas rows) — measured, not assumed. **Zero free parameters**
(rule 21): the discriminator is CAMPD's own published `unitType`, and the fall-through it
reaches is the resolver's OWN existing routing. **Rule 13 forward-regenerable** — `unitType`
is a static unit attribute — which is why the field is **deliberately absent** from
`_BACKCAST_ONLY_OVERLAY_FIELDS`, with that reasoning recorded at the exclusion site.
**Cache-key neutral** (the default key is unchanged with the field present and off, and
distinct when armed) and byte-inert off. 24 unit tests (`tests/unit/data/test_unit_outage_mixed_gas_routing.py`),
including that the coal and neiso-99 liquid-CT guards still run **ahead** of the new gate.
Matrix row + a cell in all six shards, same PR (rule 28(c)).

**Why the arm's extract is a RELABEL and not a re-derivation** (`_miso200_relabel_extract.py`).
A fresh unrepaired re-derivation at this HEAD **does not reproduce the committed extract**
(§7), so an A/B on a re-derived file would carry the routing repair *and* that drift and
could attribute neither. The arm's extract is therefore the committed extract with exactly
one column rewritten, by the **production resolver**, on exactly the rows it re-routes.
`plant_group` is the only column the overlay reads for routing — the derate denominator is
the FLEET bin capacity `cap[tgt]`, never the extract's own `plant_capacity_mw`. The
deriver's `--mixed-gas-routing` flag is the forward path; the relabel is how *this* session
isolates the object.

### L-3b PASS — the delta is exactly one object

| rows added | rows dropped | rows changed | columns changed | out of scope |
|---:|---:|---:|---|---:|
| **0** | **0** | **116** | **`plant_group` only** | **0** |

### L-3a FAIL — and the arm is killed on it

> *"no MISO bin-hour in 2023–2025 whose pre-clip removed share exceeds 1.0 after the repair
> but did not before. The repair must REMOVE overflow, never add it. **A violation KILLS the
> arm.**"* — frozen in the PREREG and in the probe docstring, before any number.

| new-overflow cell | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **(1403, ST_GAS)** max share (hours > 1) | **1.1472** (1,728) | **1.1329** (552) | **1.1315** (144) |
| **(2070, ST_GAS)** max share (hours > 1) | **2.0000** (24) | **2.0000** (72) | **2.0000** (24) |

**It fires, and it is not renegotiated.** The threshold was frozen before the number and
the mechanical verdict stands as the instrument returned it (the miso-172 discipline the
charter names). **The arm is killed at phase 0 and NO SOLVE WAS SPENT** — solving an arm
its own soundness gate has already killed would only invite re-litigating the kill against
the C1/C3a numbers it produced.

**REPORTED AGAINST THE KILL'S INTEREST, and it does NOT change the verdict.** On a NET
basis the repair removes far more overflow than it adds:

| year | bin-hours over 1.0 | excess capability (TWh) |
|---|---|---|
| 2023 | 195,504 → **192,048** (−3,456) | 20.8025 → **18.8169** (−1.9856) |
| 2024 | 211,416 → **207,432** (−3,984) | 23.0591 → **21.1731** (−1.8860) |
| 2025 | 352,224 → **348,384** (−3,840) | 21.0718 → **20.3369** (−0.7350) |

A *net* overflow test would have passed comfortably. **That is not the test that was
frozen**, and a threshold is not re-chosen after its number is read.

## 6. WHY it fires — two further pre-existing defects the mis-routing was masking

This is the session's substantive result, and it is why the kill is not a refutation of the
repair. The two new-overflow cells have **different root causes, and neither is created by
the routing change**:

1. **(1403, ST_GAS) → 1.13 is a NUMERATOR/DENOMINATOR BASIS GAP.** The extract's own
   capacities for units 4 + 5 sum to **1,651.1 MW** against a fleet ST_GAS bin of
   **1,465.4 MW** — ratio **1.1267**, matching the measured 1.13. This is precisely the
   Stony Brook family (`unit_outage_lp_capacity_basis`, NEISO 6081, caiso-184). **But that
   flag cannot reach it**: `outages._CC_NAMEPLATE_BASIS_GROUPS` is
   `("CC_REGULAR", "CC_CHP")`, so the basis raise is **CC-only** and never touches an
   ST_GAS bin. The composition partner this repair needs **does not yet exist** — it is the
   ST-side analogue of an existing, registered, `U`-celled mechanism.
2. **(2070, ST_GAS) → exactly 2.00 is an ADJACENT-WINDOW BOUNDARY-DAY DOUBLE-COUNT.** Unit
   3's bin capacity (59.0 MW) equals its extract capacity (59.0 MW) exactly, so a single
   window gives share 1.0 — the 2.0 is **two rows of the SAME unit overlapping on one day**:
   `2023-03-20..2023-03-27` and `2023-03-27..2023-04-04` both cover 2023-03-27 under the
   overlay's own `[start 00:00, end + 1 day)` day-grain reconstruction. A self-overlap in
   the extract, at day grain, worth 24/72/24 hours a year.

**Both were invisible while the rows were mis-routed** — divided into a 649.5 MW or 268.0 MW
CC bin they contributed shares that stayed under 1.0, or were swamped by an overflow already
clipped. **The mis-routing was masking them**, which is rule 14 `[R-ACCURATE]`'s own
compensating-error pattern arriving one level deeper than usual: not "the accurate input
makes the fit worse", but *"the accurate input makes a second latent defect observable."*

## 7. N-4 and the provenance drift — reported, gating nothing

**N-4, the capability bound (a rigorous UPPER bound; L-4 gates nothing on it, by design,
because no rigorous LOWER bound on a CLASS decrement exists — other ST_GAS plants can
substitute).** Mean bin availability and the signed capability change:

| year | (1403, CC_REGULAR) avail | (1403, ST_GAS) avail | **CC_REGULAR bound** | **ST_GAS bound** |
|---|---|---|---:|---:|
| 2023 | 0.3521 → **0.9466** | 1.0000 → **0.5817** | **+3.4746 TWh** | **−5.4602 TWh** |
| 2024 | 0.2877 → **0.8110** | 1.0000 → **0.6217** | **+3.3055 TWh** | **−5.1916 TWh** |
| 2025 | 0.4384 → **0.8959** | 1.0000 → **0.7398** | **+2.8340 TWh** | **−3.5690 TWh** |

Against the **K-1 headroom named ex ante** — CC_REGULAR-2024 **+6.748** with **1.252 TWh**
to the +8.00 edge, ST_GAS-2024 **−7.553** with **0.447 TWh** — both 2024 bounds exceed
their headroom by a wide margin. **This is reported, not used**: the kill is L-3a's, and
L-4's no-refuse-without-solving clause is honoured rather than quietly converted into one.

**The committed MISO extract is NOT reproducible at HEAD** (the first quantification the
open `outage_artifact_provenance` cell has carried). A fresh **unrepaired** derivation at
this HEAD over 2019–2026:

| | committed | fresh at HEAD |
|---|---:|---:|
| rows 2019–2026 | 9,298 | **11,141** |
| identical window rows (both) | 9,107 | 9,107 |
| rows only on this side | 191 | **2,034** |
| 2023 / 2024 / 2025 | 1,210 / 1,255 / 1,194 | **1,429 / 1,490 / 1,424** (+219 / +235 / +230) |

Roughly **+19 % rows per year**. Not adjudicated here, not this charter's, and it is
exactly why the arm's extract is a relabel rather than a re-derivation (§5).

**A boundary, disclosed rather than absorbed.** The committed extract also carries 2018
rows (1,106) whose CAMPD unit-level source parquets are **untracked** (the BLOAT-S2 prune),
so a full-span re-derivation cannot reproduce them. The relabel path is unaffected — it
transforms the committed file in place and **fails closed**, keeping the committed group
for any in-scope unit with no CAMPD attribute row (exactly one: `(56309, 'NET0-923')`, an
EIA-923-fallback synthetic id). 2018 is outside the program's working span and unsolvable
under rule 22 regardless.

## 8. Handed on

1. **THE COMPOSITION PARTNER, named exactly: an ST-SIDE denominator basis alignment.**
   `unit_outage_lp_capacity_basis` is CC-only (`_CC_NAMEPLATE_BASIS_GROUPS`), so it cannot
   clear (1403, ST_GAS)'s 1.13. The successor's object is the ST_GAS/ST_CHP analogue —
   putting the extract's `unit_capacity_mw` numerator and the fleet bin denominator on one
   basis for steam bins. **`unit_outage_mixed_gas_routing` should be re-offered WITH it, as
   a composed arm**, and is expected to clear L-3a's 1403 leg then.
2. **THE ADJACENT-WINDOW BOUNDARY-DAY DOUBLE-COUNT.** Two windows of the same unit sharing
   an end/start date double-count for 24 hours under the `[start, end + 1 day)`
   reconstruction. Small (24-72 h/yr at 2070) but it is a **deriver/overlay defect, not a
   routing one**, and it will fire again wherever a unit's own capacity is close to its
   bin's.
3. **THE PRE-EXISTING OVER-REMOVAL POPULATION IS LARGE AND UNADJUDICATED**: 238 bin-years
   at cap ≥ 100 MW above 1.0 on the incumbent extract, median max-share 1.128, 22 at ≥ 2.0,
   totalling **20.8 / 23.1 / 21.1 TWh** of excess removed capability a year. That is the
   `unit_outage_lp_capacity_basis` `U` cell's magnitude, measured here for the first time.
4. **THE COMMITTED EXTRACT'S PROVENANCE DRIFT** (§7) — `outage_artifact_provenance` `O`.
5. **THE BID-SIDE FORM IS UNTOUCHED AND STILL OPEN** — not refuted, not adjudicated, cell
   not minted; and the miso-198 M-4 citation is corrected in §2 for whoever takes it.
6. Unchanged from miso-199 §8: fragmentation (the floor's 76.7 h / 123.6-run shape against
   a 1,575.8 h / 13.8-run commitment state); the `D4_WINDOWS` "self-windowing by
   construction" wording, which is self-**sizing**, not self-**placing**; the lay-up census
   cycler/mothball boundary; `CT_CHP` as the visible half of the steam-host family;
   `ST_CHP`'s CEMS invisibility with `profile_r` negative every year; the standing wind
   +5 TWh/yr over EIA-930; the 2023 import +2.0 TWh face; `_CC_PMAX_RECONCILED_PLANTS`
   (observed again here — it reconciles 1403's CC bin 896.0 → 649.5 MW).
7. **The charter's inherited "11 failing cache-key pin tests" item is CLOSED — corrected
   here rather than repeated.** It was true of the `main` this session opened against
   (measured: **8**, not 11, and identical to this branch's, so zero were introduced). It
   is **no longer true of `main` at the time of writing**: the default key has moved back
   to `603c2498bf71d21d` and `tests/unit/config` is **642 passed, 0 failed** on clean
   `main` and **unchanged with this branch applied**. A successor should not carry the item
   forward, and should re-measure rather than inherit any pinned key literal — this
   session's own first measurement (`7a57fadff595ca83`) was against the older base and is
   superseded.

## 9. Governance

Rule 22 `[R-HOLDOUT]`: **2023–2025 only**; MISO holds no `complete`/`final` marker; the
holdout freeze is untouched and **no marker was read or written**. Data prep is unrestricted
by the same rule and the 2018 boundary above is a coverage fact, not a spend. Rule 12
`[R-PARALLEL]`: **no solve was run at all**, and none was offloaded to CI. Rule 15
`[R-DASHBOARD]`: **no run was produced, so there is nothing to register** — the deliverable
is the committed instruments, the census record, the gated mechanism and this finding.
Rule 21 `[R-DOF]`: zero free parameters. Rule 24 `[R-REGISTRY]`: the field is in
`ScenarioConfig` and in both cache-key registries, registered in the same commit as the
field. Rule 25 `[R-ISO-SCOPE]`: only MISO's shard and only MISO's extracts; the resolver
change is shared code and its cross-ISO blast radius is reported (every other ISO's
committed extract is untouched and every other shard cell is `U`, or `.` at ERCOT, whose
branch never reaches the gate). Rule 27 `[R-PUSH]`: every push touching a ≥300-line file
was blob-verified against a fresh fetch. Rule 28(b): the cell is stamped in MISO's shard
in-session; rule 28(c): the new field's base row plus a cell in **all six** shards landed
in the same PR.

## 10. Reproduction

```
python3 scripts/probes/_miso200_outage_routing_phase0.py --satisfiability
python3 scripts/probes/_miso200_relabel_extract.py --iso MISO
python3 scripts/probes/_miso200_relabel_extract.py --iso MISO --maxgen
python3 scripts/probes/_miso200_outage_routing_phase0.py
python3 -m pytest tests/unit/data/test_unit_outage_mixed_gas_routing.py
# the forward derivation path (not used for the A/B extract -- see section 5):
python3 scripts/data/derive_campd_unit_outages.py --iso MISO --mixed-gas-routing
python3 scripts/data/derive_campd_maxgen_outages.py --iso MISO --mixed-gas-routing
```
