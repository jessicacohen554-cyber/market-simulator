# FINDING — nyiso-120: neither meter is wrong about East River. They AGREE, to 1.0 %, and what they agree on is that the model has been double-counting boiler fuel into a 306 MW NYC gas tranche

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry:** `2026-08-03-nyiso-118-seny-span`, CALIBRATED-WITH-CAVEATS,
C3c (`price_tail`) the sole ledgered caveat.

**Prereg (committed BEFORE any statistic, any derive and any solve):**
`results/calibration/PREREG-nyiso120-eastriver-scope-gate-2026-08-04.md`.
**Probes:** `scripts/probes/_nyiso120_eastriver_boundary.py` (no LP),
`scripts/probes/_nyiso120_scope_gate_ab.py`.
**Records:** `results/calibration/_nyiso120_eastriver_boundary.json`,
`_nyiso120_scope_gate_ab.json`, `_nyiso120_artifact_A.csv`.

**Session provenance.** The brief opened on **NEISO**, whose queue is
owner-gated end to end (matrix §5.6: item 1 SPENT, items 3/4/6/7/8 closed,
item 2 ceiling-bounded, items 5 / 5b / C3c-2023 all requiring an owner
green-light that is not granted), and directed a **cross-ISO** cell. This is
NYISO's, and it was minted one day earlier by **miso-122 §7 handoff item 1**,
which measured the defect, declined to act on it under rule 25
`[R-ISO-SCOPE]`, and left one question open: *"which meter is wrong about East
River's boundary, and it is not answerable from MISO's data."*

**It is answerable from NYISO's data, and the answer is that neither is.**

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **KE1** | is eGRID's `CHPCHTI` at East River the same object as the CAMPD dark-boiler fuel? | **13,629,047 ÷ 13,493,031 = 1.0101** | **PASS** — the same object to **1.0 %**. eGRID's "CHP credit" here is not a topping-cycle steam credit; it is the fuel of two boilers that make no electricity |
| **KE2** | do two independent meters agree on the power-only rate? | CAMPD power-train fuel ÷ eGRID `PLNGENAN` = **7.3763** vs eGRID's credited **7.4205** — ratio **0.9940** | **PASS** — they agree to **0.6 %**, and they agree on **7.4**, not on the 11.8032 the keeper charges |
| **KE3** | is the dark set boilers, and is it machinery rather than a reporting spike? | **100.0 %** of dark fuel in `Dry bottom wall-fired boiler` in all three years; share **37.51 / 30.79 / 30.64 %**, max/min **1.22** | **PASS** — R2 (selection artifact) is refuted |
| **H vs R1** | double-count, or genuine boundary ambiguity? | KE1 + KE2 jointly | **H CONFIRMED.** `PLHTIAN` *is* the power train's fuel, so `PLHTRT = 7.4205` is *already* the power-only rate and the add-back **double-counts** |
| **KE4** | does the HEAD re-derive change only what it advertises? | **exactly one** applied row moves (2493/`CT_CHP`, `ok` → `below_credited`); zero other flag changes, zero other applied-rate changes | **PASS** |
| — | the applied-map change | East River's offer heat rate **11.8032 → 7.4205, −37.1 %**, on **306.0 MW** of NYC `CT_CHP` | ships under rule 14 `[R-ACCURATE]` |

---

## §1 — the object, and why it looked like a contradiction

The `measured_chp_heat_rates` mechanism replaces eGRID's **steam-credited**
`PLHTRT` with `(PLHTIAN + CHPCHTI) / PLNGENAN` — eGRID's own published CHP
useful-thermal allocation added back on the same net denominator. Its premise
is that at a **topping-cycle** cogen the process steam is recovered from the
prime mover's exhaust, so it is a free co-product and *all* the fuel belongs to
the power.

miso-122's hybrid-cogen scope gate then found that at some plants a slice of
the metered fuel burns in units with **zero gross load all year** — direct-fired
boilers that make no electricity at all — and that slice cannot be a topping
cycle's co-product either. At NYISO ORIS **2493 East River** the gate measured
that slice at **37.5 %** of 2023 fuel, and removing it produced **7.3763**,
which sits **below eGRID's own credited 7.4205**. The gate's response is the
`below_credited` flag: exclude the plant, on the stated ground that "the two
sources disagree about where the plant's boundary is."

That reading is what this session was sent to test, and it is **too
pessimistic**. The two sources do not disagree.

---

## §2 — the measurement (no LP), on NYISO's own data

CAMPD unit-grain, facility 2493, all four units, all three years — the
behavioural dark rule (`heatInput > 0`, `grossLoad ≤ 0` over the whole year) is
the derive's own, called directly rather than re-implemented; `unitType` is read
only to **check** the selection (rule 24 `[R-REGISTRY]` forbids the allowlist):

| year | unit | `unitType` | heat MMBtu | gross MWh | dark |
|---|---|---|--:|--:|:--:|
| 2023 | 1 | Combined cycle | 11,676,993 | 1,087,690 | — |
| 2023 | 2 | Combined cycle | 11,032,476 | 1,045,798 | — |
| 2023 | **70** | **Dry bottom wall-fired boiler** | **6,922,906** | **0** | **dark** |
| 2023 | **60** | **Dry bottom wall-fired boiler** | **6,706,140** | **0** | **dark** |
| 2024 | 1 / 2 / 60 / 70 | as above | 12,124,977 / 12,038,754 / 6,789,992 / 3,959,851 | 1,120,840 / 1,138,171 / 0 / 0 | 60, 70 |
| 2025 | 1 / 2 / 70 / 60 | as above | 11,905,619 / 11,510,467 / 5,675,265 / 4,668,050 | 1,093,484 / 1,095,160 / 0 / 0 | 70, 60 |

Two generating `Combined cycle` units and two boilers at **exactly zero** gross
load in every hour of every year. This is the hybrid Dearborn shape, and eGRID's
plant-level CHP split cannot see it — one ORIS code, two different machines.

**KE1 — the identity test.** eGRID's 2023 `CHPCHTI` is **13,493,031 MMBtu**.
The CAMPD dark-boiler fuel is **13,629,047 MMBtu**. Ratio **1.0101**, inside the
committed `[0.90, 1.10]` two-meter band (miso-118's, reused not reinvented).
**eGRID's entire CHP thermal allocation at East River is the boiler fuel.**

**KE2 — the basis-matched two-meter comparator.** CAMPD power-train fuel
(units 1+2) is **22,709,469 MMBtu**; over eGRID's **3,078,707 MWh** of net
generation that is **7.3763 MMBtu/MWh**, against eGRID's own credited
**7.4205**. Ratio **0.9940**. Two independent meters — EPA's stack CEMS and
EPA's eGRID plant sheet — agree on the power-only rate to **0.6 %**.

**Together KE1 and KE2 settle it.** If `CHPCHTI` is the boiler fuel, then
`PLHTIAN = total − CHPCHTI` is the power train's fuel, and
`PLHTRT = PLHTIAN / PLNGENAN` is **already the power-only rate**. Adding
`CHPCHTI` back charges the boilers' fuel to the turbines a second time. The
model has been offering 306 MW of NYC `CT_CHP` at **11.8032** — **59 % above**
what the machine actually burns per MWh.

**KE3 — persistence and composition.** 100.0 % of the dark fuel is in a boiler
`unitType` in all three years; the share is 37.51 / 30.79 / 30.64 % with
max/min **1.22**. Machinery, not a reporting spike. R2 is refuted.

### §2.1 — a corroborating physical fact, reported (not pre-registered, not gated)

CEMS gross load at the two generating units is **2,133,488 MWh** in 2023 against
eGRID's **3,078,707 MWh** net — a gross/net ratio of **0.693**, which is
`G_gross < 1`, the **physically impossible** signature miso-118 identified. It
means the plant makes ~0.95 TWh/yr of electricity that CEMS's `grossLoad`
channel never sees: HRSG steam turbines, which burn no fuel of their own and are
not Part-75 monitored. That is exactly why **7.4** and not **10.6** (the naive
CEMS-gross rate) is the right number, and it is why the correct denominator is
`PLNGENAN` — the same denominator the incumbent already divides by. It is
reported because it independently corroborates KE2 from the *generation* side
rather than the *fuel* side; it was not pre-registered and gates nothing.

### §2.2 — what this does NOT claim

It does not claim to know eGRID's allocation *intent*. The claim is the measured
identity — `CHPCHTI` ≈ dark-boiler fuel (KE1) **and** `PLHTIAN / PLNGENAN` ≈
CAMPD power-train fuel ÷ `PLNGENAN` (KE2) — which is sufficient for the
conclusion and does not require reading EPA's mind. It also claims nothing about
any other plant: the other three NYISO rows carrying dark fuel
(50368 Cornell 100 %, 10025 RED-Rochester 100 %, 52168 Riverbay 50.4 %) were
already excluded by the **earlier** scope gates (`not_unfired_topping`,
`basis_mismatch`) and their applied rates are byte-unchanged.

---

## §3 — the re-derive, and KE4

`python scripts/data/derive_chp_power_only_heat_rates.py --iso NYISO`, HEAD,
**unmodified** — the gate is miso-122's, shipped exactly as committed; this
session edited no derive logic (rule 23 `[R-FROZEN-DERIVE]`: the re-derivation
is motivated by a **scope-gate logic change on measured grounds** and cites it,
never by a residual).

| | A (committed, pre-gate) | B (HEAD re-derive) |
|---|---|---|
| sha256 | `407baa55…6ab2` | `c954bf06…588e` |
| `flag` census | ok=18, … | **ok=17**, `below_credited`=1, … |
| 2493 `CT_CHP` flag | `ok` | **`below_credited`** |
| 2493 `CT_CHP` **effective** rate | **11.8032** | **7.4205** |

**KE4 PASSES exactly**: one applied-rate row changes, zero other flag changes,
zero other applied-rate changes. The only other differences are that same row's
`heat_rate` / `model_over_measured` and three purely **additive** columns
(`cems_dark_heat_mmbtu`, `dark_fuel_share`, `heat_rate_all_fuel`).

**The direction is unambiguous only because NYISO carries no hand factor.**
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` is `{CAISO, PJM}`; NYISO is not in it, so
an excluded row reverts to the **plain eGRID rate** (7.4205) and the change is a
**37.1 % cut**. In a hand-factor ISO the same exclusion would push the rate
**up** — asserted in the scorer (`k6_direction_integrity`), not assumed.

---

## §4 — the A/B, and the control that had to be re-solved

**Arms.** `2026-08-04-nyiso-120a2-control-samehead` (control, pre-gate artifact)
vs `2026-08-04-nyiso-120b-scope-gate` (treatment, gated artifact), both
`replay_keeper` of `nyiso118_seny_span`, 2023–2025 in one invocation each.

**THE FIRST CONTROL WAS INVALID AND IS SUPERSEDED — reported, not buried.**
`2026-08-04-nyiso-120a-control` solved at a **pre-rebase HEAD**; main then added
three `ScenarioConfig` fields (`caiso_zonal_loss_surface`,
`ercot_energy_online_capability_cap`, `pjm_seam_envelope_by_neighbor`), so
against arm B it read **3 differing config keys** and failed the prereg's KE5
same-HEAD requirement. It stays registered as the record of that, and **no
number in this finding is quoted against it.** The valid control was re-solved
at the treatment's own HEAD. That it was needed at all is the FINDING-nyiso114
§2 hazard biting from the other direction — not keeper drift, but *my own
rebase* between arms.

**And the re-solve settles the drift question by measurement:** arm A2 is
**byte-identical to the committed keeper** (K2 byte basis `True`, max class-hour
|ΔMW| ≤ 1e-6 in all three years) with an identical scorecard and determination.
So main's three new fields are **inert at NYISO**, and every delta below is the
scope gate's and nothing else's.

**Gates — all six construction gates PASS, no kill fires, verdict LIVE.**

| gate | result |
|---|---|
| K1 artifact fidelity | PASS — sha differs, config identical, **exactly one** effective row moves: `2493:CT_CHP` 11.8032 → 7.4205 (**−37.13 %**) |
| K2 control integrity | PASS — control scorecard == keeper scorecard, **and byte-identical** |
| K3 liveness | **PASS / LIVE** — max zonal \|Δλ\| **0.1287 / 0.1371 / 0.3875** $/MWh, clearing the 0.10 bar in **3 of 3** years |
| K4 zero config delta | PASS — **zero** differing keys |
| K5 year span | PASS — [2023, 2024, 2025] both arms |
| K6 direction integrity | PASS — no effective rate rises, **no zone's λ rises in any year**, system λ −0.127 / −0.139 / −0.384 |

**W2 — the mechanism fired.** `CT_CHP` energy **+0.3113 / +0.1921 / +0.4214 TWh**,
displacing `ST_GAS` (−0.131 / −0.093 / −0.138), `CC_REGULAR` (−0.098 / −0.065 /
−0.164) and `CC_CHP` (−0.069 / −0.022 / −0.060). A merit-order reshuffle of the
expected sign and size: one 306 MW plant made 37 % cheaper.

**Zonal incidence is systemic, not local** — every zone falls by roughly the same
amount (2025: NYC −0.3875, Lower_Hudson −0.3820, Upstate_West −0.3827,
Capital_Hudson −0.3816, Long_Island −0.2962), because East River displaces
marginal gas across the mainland rather than only in Zone J.

### §4.1 — the P gates, and the one that fires

| gate | result |
|---|---|
| P1 free-class C1 | **PASS — no regression**: all 14/14 and free 10/10 in **both** arms |
| **P2 no new FAIL** | **FIRES** — `price_mean` (C3a) FAILs in B and not in the control |
| P3 protective | PASS — governance + forced_share PASS |
| P4 slack/dump | PASS |
| P5 no fitted follow-up | PASS — zero free parameters, no threshold, derive shipped unmodified |
| P6 no C3c claim | PASS — `price_tail` CAVEAT in **both** arms, unchanged |

**C3a, the whole of the regression, per year:**

| year | control | treatment | model mean LMP | actual RT |
|---|--:|--:|--:|--:|
| 2023 | +7.6 % PASS | **+7.2 % PASS** | 34.77 → 34.64 | 32.30 |
| 2024 | −0.5 % PASS | −0.9 % PASS | 37.99 → 37.85 | 38.20 |
| 2025 | **−9.5 % PASS** | **−10.0 % FAIL** | 60.24 → **59.85** | 66.53 |

**Stated plainly: 2023 IMPROVES, 2024 stays deep inside the band, and 2025
crosses a knife-edge.** The control already sat **0.5 pp** from the ±10 % edge,
and the correction moves the 2025 system mean by **−$0.39/MWh** on a $60 mean.
The 2025 C3a gap is **$6.68/MWh**; this correction is **6 %** of it and the other
**94 % is pre-existing and untouched**. It did not create NYISO's 2025
under-pricing — it tipped a criterion that was already at its edge.

**This was pre-registered.** Prereg §4.1 declared *in advance* that the
correction makes a NYC unit cheaper, that the expected direction is lower
prices, and that a gate moving the wrong way does not revert it (rules 1 / 14).
The prereg named C3c; the criterion that actually moved was C3a. **That
difference is recorded rather than smoothed over** — the anticipated *mechanism*
(cheaper NYC capacity ⇒ lower λ) is exactly what happened; it landed on the
level criterion instead of the tail one, and C3c is bit-unchanged.

---

## §4.2 — THE KEEPER MOVED MID-SESSION, SO EVERYTHING ABOVE WAS RE-RUN ON THE RIGHT BASE

**The A/B in §4/§4.1 is on the `nyiso-118` recipe, and it is SUPERSEDED as the
promotion evidence.** The NYISO keeper advanced
`2026-08-03-nyiso-118-seny-span` → **`2026-08-03-nyiso-119-seny-increment`**
*during* this session, after the arms were launched. A `nyiso-118`-based
treatment is therefore **not** a valid keeper candidate: promoting it would have
**silently disarmed `nyiso_seny_rcpf_increment_step`**, the mechanism nyiso-119
armed and the owner promoted a day earlier. That was caught before it landed —
the keeper shard edit was made, checked, and **reverted** — and both arms were
re-solved on the `nyiso-119` recipe so the correction **composes** onto the
current keeper instead of reverting it.

**Deciding arms:** `2026-08-04-nyiso-120-c119-control` vs
**`2026-08-04-nyiso-120-c119-scope`**. The control reproduces the nyiso-119
keeper's C3a **exactly** (34.77 / 37.99 / 60.22). The promoted run carries
`nyiso_seny_rcpf_increment_step = True`, verified explicitly.

**The result replicates on the correct base** — which is itself worth stating,
because it means the finding is a property of the input, not of the recipe:

| gate | nyiso-118 pair | **nyiso-119 pair (deciding)** |
|---|---|---|
| six construction gates | all PASS, LIVE | **all PASS, LIVE** |
| max zonal \|Δλ\| | 0.1287 / 0.1371 / 0.3875 | **0.1278 / 0.1379 / 0.3887** |
| `CT_CHP` ΔTWh | +0.3113 / +0.1921 / +0.4214 | **+0.3103 / +0.1927 / +0.4213** |
| C1 | 14/14 all, 10/10 free both arms | **unchanged, both arms** |
| P2 | fires on C3a | **fires on C3a** |
| C3a 2025 | −9.5 % → −10.0 % | **−9.5 % → −10.1 %** |
| C3a 2023 | +7.6 % → +7.2 % | **+7.6 % → +7.2 %** |

The three residual config differences against the nyiso-119 keeper
(`exit_rate_limits`, `caiso_zonal_loss_surface`,
`ercot_energy_online_capability_cap`) are **HEAD drift, not deltas introduced
here** — all three are new fields main added after nyiso-119 solved, they are
non-NYISO-scoped or backcast-inert, and the c119 **control carries them
identically**, which is why K4 reads **zero** config delta between the two arms.

---

## §5 — the determination, and the governance stop

**Control: CALIBRATED-WITH-CAVEATS** (C3c sole caveat).
**Treatment: NOT-YET** — C3a is load-bearing, so a single-year FAIL carries the
determination down a full tier.

**Recommendation: arm B IS the recommended keeper candidate**, on the owner's
standing standard (*"if structural integrity improves but gates regress that may
still be a keeper"*):

1. **The input was wrong and is now right**, established by two independent
   meters agreeing to **0.6 %** and **1.0 %** — not by a fit. Zero free
   parameters, no threshold, no derive edit.
2. **Rules 1 and 14 are explicit** that a structurally-correct input is never
   reverted because a residual moved the wrong way.
3. **The regression is 0.5 pp on a ±10 % band**, worth −$0.39/MWh, while 2023
   improves and C1 / C3b / C3c / C4 / C6 / C7 / C8 are all unchanged.
4. **It moves the worst-matched class toward reality.** The incumbent keeper's
   own `_open_items` records `CT_CHP` under-dispatched **−67.9 / −67.6 /
   −62.0 %**; this adds 0.19–0.42 TWh/yr to exactly that class.
5. **It closes a reproducibility seam.** The incumbent keeper solved on the
   pre-gate artifact and is **no longer reproducible from HEAD** — the same seam
   miso-122 opened at MISO and closed by promoting its treatment.

**BUT THE PROMOTION IS STOPPED, AND NOT BY ME.** NYISO holds a
`calibration-complete` **`complete`** marker, so rule 22's **D-5(b)** governs:
the entry's `determination` must be re-verified against the new keeper before
the promotion commit lands, and *"a re-verified determination that is **worse**
stops the promotion and escalates to the owner; it is never silently written."*
CALIBRATED-WITH-CAVEATS → NOT-YET is worse, and it would change NYISO's
**published calibration status**. So this is escalated with the numbers above
rather than taken under the standing standard — the standing standard is
general, D-5(b) is specific to a `complete` ISO and specifically names
escalation.

**OWNER RULING: PROMOTE.** Escalated with the numbers above; the owner ruled
promote. **NYISO keeper → `2026-08-04-nyiso-120-c119-scope`** (the nyiso-119-based
treatment, §4.2 — *not* the nyiso-118-based arm B, which would have disarmed
`nyiso_seny_rcpf_increment_step`). `calibration-complete.json` re-keyed with the
worse determination **written explicitly, not softened**;
`audit_keepers --iso NYISO` PASSES 0 failures / 0 warnings.

The ledgered-caveat budget is **unspent** by this change (1 of 3, C3c only). The
C3a FAIL is a criterion failure, **not** a new ledger entry, and is deliberately
not ledgered — it is an open residual whose named object is the 2025
under-pricing this correction did not create.

---

## §6 — reported against interest

1. **My own rebase invalidated the first control**, cost a full re-solve, and is
   reported in §4 rather than quietly replaced.
2. **I committed nine bundle JSONs containing unresolved conflict markers** —
   five of them another lane's (nyiso-119's) — by blanket-resolving a
   rename/rename conflict on the assumption each path was uniquely owned by one
   side. It reached `origin/main`. Found, stopped for, and repaired
   (`scripts/probes/_nyiso120_resolve_rename_conflicts.py`; the nyiso-119 files
   restored **byte-exactly** from their own session's commit `4e1b1274`, not from
   a parser). Zero markers remain. Recorded because a silent repair of another
   lane's committed bytes would be worse than the original error.
3. **The prereg named C3c and C3a is what moved.** The mechanism anticipated was
   right; the criterion was not. Reported as a miss in the pre-registration, not
   re-narrated as a hit.
4. **`heat_rate_credited` is not independently verified as *correct*, only as
   *corroborated*.** KE2 shows CAMPD's power-train fuel over eGRID's net
   generation agrees with eGRID's credited rate to 0.6 %. Both use `PLNGENAN` as
   the denominator, so the agreement is on the *numerator* — the fuel — and a
   common error in `PLNGENAN` would cancel. What is established is that the
   **add-back is wrong**, which is what the correction acts on.
5. **The 306 MW is a class-capacity figure**, not a claim about East River's
   instantaneous output; the LP dispatches it against its own availability.

---

## §7 — governance

Rule 12: years sequential; the two arms swap a fixed-path input file so they ran
sequentially, never concurrently. Rule 13: no measured outcome enters any solve;
every measured price is a validation target. Rule 15: all three runs registered
and committed **this session**. Rule 16: 2023–2025, one bundle each, one
invocation. Rule 21: DOF ledger carried over **unchanged** (32 entries,
`n_residual` 6) — the correction adds no degree of freedom. Rule 22: training
years only; the holdout spend freeze is ACTIVE and untouched; the D-5(b) re-key
duty is **why the promotion is escalated** rather than taken. Rule 23: the
re-derive cites miso-122's scope-gate logic change, never a residual. Rule 25:
only NYISO's artifact was re-derived; **NEISO 1595 Kendall (206 MW, −1.2 %)
stays in NEISO's lane and no cell outside NYISO is stamped.** Rule 26: nothing
deprecated; the open rule-26 queue is untouched. Rule 28 duty (b): the
`measured_chp_heat_rates` NYISO cell is stamped this session.
