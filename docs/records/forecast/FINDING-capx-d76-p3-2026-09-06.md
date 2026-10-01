# FINDING — capx D76 phase 3: the two deferred ISOs, and PJM re-measured post-Q55. **ALL SIX ISOs NOW MEASURED. Every STOP clean in all three; NYISO and PJM INERT exactly as pre-declared; NEISO's requirement is LIVE but NON-BINDING. Nothing arms.**

**Lane:** capx D76 phase 3. Branch `claude/capx-d76-p3-neiso-nyiso-pjm-sraz8b`, base
`origin/main` **`0f7a4842`**. Pre-registered in `PRECOMMIT-capx-d76-p3-2026-09-06.md`,
**pushed before the first LP** (`5259d519`). Phase 0/1 record:
`FINDING-capx-d76-2026-09-06.md`; phase 2: `FINDING-capx-d76-p2-2026-09-06.md`.
Instruments (extended, not forked): `docs/handoffs/d76/p2_predeclare.py` (`--isos`),
`p2_gate.py` (`--predeclare`), `p2_consumer_probe.py`, `p2_accreditation_probe.py`;
outputs `p3_predeclare.json`, `p3_predeclare_addendum.json`, `p3_gate_{neiso,nyiso,pjm}.json`.

**NOTHING ARMS.** §7 drafts an arming card **for** the director; drafting is not serving.

---

## 0. Result in one paragraph

**Six legs, three ISOs, all rc=0; every STOP PASSES in all three.**
STOP 2, the whole structural claim, lands to **0.000 MW in every year of every ISO**. The
whole-ledger diff moves **0 to 4 fields of 30-39 per year, zero `UNCLASSIFIED` anywhere**. **NYISO is INERT end-to-end and this was written down before the solve**: its D52
gates make the adequacy requirement peak-independent, and its ledger moves
`screen_peak_demand_mw` and *nothing else* in all three years — the pre-declared
consequence, confirmed. **NEISO's requirement is LIVE and moves by the pre-declared
amount to within 0.045 MW — and nothing consumes it**: entering firm identical to the
cent, retirements identical, fleet identical, `floor_retained` empty. The reason is
measured, not inferred: NEISO's fleet sits **4.99-7.56 GW above** its requirement
(position 1.20-1.31), so a ±345/618 MW bar move crosses no screen threshold. The
cross-ISO picture is now **complete for all six ISOs** and it **narrows further**: the
adequacy requirement is still the only live consumer, it is peak-**independent** in 2 of 6
ISOs by two different gates (PJM/D67, NYISO/D52), and **decisions move in only 2 of 6**
(CAISO's backstop build, MISO's admission cap). The VRE accreditation census is now
measured **peak-inert in all six ISOs**.

**D75-R-ARM MERGED MID-LANE, so PJM WAS re-measured after all and the charter's question is
ANSWERED** (§1, §5A): with the ELCC vintage armed, PJM's accreditation census is **still
peak-inert**, its A/B moves the seam field and nothing else in all five years, and phase 2's
caveat **inverts** — the arming makes the inertness *stronger*, not weaker. **All six ISOs
are now measured.**

---

## 1. THE CHARTER'S PJM QUESTION — blocked at the start, ANSWERED by the end

**The sequence matters and is recorded exactly.** When this lane opened, the charter's
dispatch STOP was **unmet**: `origin/main` carried no D75-R-ARM commit, the branch
`claude/capx-d75r-arm-pjm` did not exist on the remote, and `_pjm_config` did not carry
`pjm_vre_accreditation_vintage` — Q55 had ruled ARM but the arm was never executed, and the
ledger sequenced it behind D65-B-R's board write (then at leg 6 of 7). That was reported to
the director, who authorized a reduced scope in session: run the two ISOs that do not depend
on the PJM ELCC vintage, defer PJM. **NEISO and NYISO were solved, graded and pushed under
that reduced scope** (§3-§5).

**Then D75-R-ARM merged, while this lane was still open.** `origin/main` reached
`57bc34a7` carrying **`6164231e` — "capx D75-R-ARM: `pjm_vre_accreditation_vintage` is ARMED
for PJM (owner ruling Q55)"**, and `_pjm_config.default_scenario_overrides` now contains
`"pjm_vre_accreditation_vintage": True`. Both precondition legs flipped to PASS.

**So the lane asked the question rather than closing with it open.** PRECOMMIT **Addendum 1**
was written and **pushed before the first PJM LP**: it re-audits the `0f7a4842 → 57bc34a7`
delta hunk by hunk, verifies that NEISO's and NYISO's four keys are **unmoved** by the rebase
(so §3-§5 describe the new head too), re-declares PJM's two keys at the new head
(`b518f5fe7d02f961` / `559c05579b47684b` — they *did* move, exactly as the charter predicted
they would), and records the **zero-LP census answer before the solve**. The PJM legs were
then solved at the new head with the vintage armed on **both** sides, which is what makes the
A/B isolate this lane's own gate against an already-repaired accreditation.

**PJM's row in §6 and §7 is therefore MEASURED, post-Q55, not carried.** §5A is the result.

## 2. The legs, and the one solve-code state

| leg | ISO | window | cache key | pre-declared? | rc |
|---|---|---|---|---|---|
| 5-C | NEISO | 2021-2023 | `ca4b163f62c4f52f` | **yes, exact** | 0 |
| 5-A | NEISO | 2021-2023 | `69688c797d7bac80` | **yes, exact** | 0 |
| 6-C | NYISO | 2021-2023 | `0641a92f61740d55` | **yes, exact** | 0 |
| 6-A | NYISO | 2021-2023 | `236b56818bed34e9` | **yes, exact** | 0 |
| 7-C | PJM | 2021-2025 | `b518f5fe7d02f961` | **yes, exact** (Addendum 1, at `57bc34a7`) | 0 |
| 7-A | PJM | 2021-2025 | `559c05579b47684b` | **yes, exact** (Addendum 1, at `57bc34a7`) | 0 |

**Every realized key equals the value machine-emitted before its own leg ran** — NEISO and
NYISO into `p3_predeclare.json` before the first LP, PJM into
`p3_predeclare_addendum.json` before the first PJM LP — and every control key equals its
bare recipe key at its own head. All six legs ran SEQUENTIALLY, one LP at a time; rule 12's
two-concurrent allowance was deliberately not taken (15 GB / 4 cores). **NEISO and NYISO are
at base `0f7a4842`; PJM is at `57bc34a7`** (§12) — each A/B is internally at one base, which
is the only comparison any of them makes.

**No commit of any kind landed between the two legs of any A/B** — the rule the
PRECOMMIT §3 added after phase 2 took a literal STOP 3 FAIL from exactly that. It worked:
**STOP 3 finds the five bookkeeping keys and no `git` difference in any of the three ISOs** (§3).

### 2.1 A fresh-checkout prerequisite, recorded because it cost the first attempt

The first 5-C attempt died before any LP with `RuntimeError: confirmed-retirements: clean
partition for NEISO is absent while confirmed_exits_enabled is on in forecast mode`.
`data/clean` is derived and gitignored, so a fresh checkout has none. **This is the guard
working as designed** (W1-B B3 — refusing to silently degrade to the economic screen), not
a defect. Repaired by `scripts/regenerate_clean.py` (rc=0, zero failures) and the leg
re-run from scratch. **No model, recipe or config change, and no cache key moved** —
`cache_key` hashes config, never data-file state.

**NYISO needed no partition and got none, correctly.** `data/raw/confirmed-retirements/nyiso.csv`
is a documented zero-row registry ("DATA NEEDED — zero qualifying rows"), so the curator
skips it; with the clean root now curated, `load_confirmed_exits` takes its
`_registry_curated()` branch and degrades to `[]` with a warning — the case its own
docstring names NYISO as the example of. Measured: NEISO 16 confirmed exits, NYISO 0.
**Nothing was worked around**: had the registry been missing rather than empty, the guard
would still have refused.

## 3. The STOP gates — PASS, 6 of 6, in all three ISOs

| STOP | NEISO | NYISO | PJM |
|---|---|---|---|
| 1 — no pre-existing key moves (12 recipe keys) | **PASS** | **PASS** | **PASS** |
| 2 — the identity, to the MW | **PASS** | **PASS** | **PASS** |
| 3 — every non-peak operand byte-identical | **PASS** | **PASS** | **PASS** |
| 4 — footprint confined, zero UNCLASSIFIED | **PASS** | **PASS** | **PASS** |
| 5 — no non-target load-bearing flip | **PASS** | **PASS** | **PASS** |
| 6 — one measured load per armed year (by test) | **PASS** (9 passed / 14 subtests) | **PASS** (same test) | **PASS** (same test) |

**STOP 2 — the whole structural claim — lands to 0.000 MW everywhere:**

| ISO | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| NEISO | 0.000 | 0.000 | 0.000 | — | — |
| NYISO | 0.000 | 0.000 | 0.000 | — | — |
| PJM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

`|arm screen_peak_demand_mw − pre-declared measured peak|`, MW; and
`|screen peak − the ledger's own peak_demand_mw|` = 0.000 MW in every SOLVED year. 2022 is
the **bridge** year — evolved, never solved — so the identity also proves the gate fires
where the bridge evolves the fleet against the seam peak.

**STOP 3** finds exactly the five pre-registered bookkeeping keys (`cache_key`, `run_dir`,
`scenario_config`, `scenario_config_source`, `timestamp`) and **no sixth**; the nested
`scenario_config` differs in **exactly one field, this lane's own gate**; and the 2021
pre-screen ledger differs in `screen_peak_demand_mw` alone, of 36 fields, with every
DECISION field identical.

**STOP 5** — both `score.json` differ in **exactly one path, `generated_utc`** (1 s apart
in NEISO, 9 s in NYISO). Every scored metric is identical, so no criterion flips in either
direction.

### 3.1 The whole-ledger diff (D81 rec 4) — zero UNCLASSIFIED

| ISO | year | moved / total | keys (class) |
|---|---|---|---|
| NEISO | 2021 | 1/36 | `screen_peak_demand_mw` (SEAM) |
| NEISO | 2022 | 3/30 | + `screen_adequacy_requirement_mw`, `screen_reserve_position` (SCREEN) |
| NEISO | 2023 | 4/38 | + `capacity_reserve_position` (SCREEN) |
| NYISO | 2021 | 1/36 | `screen_peak_demand_mw` (SEAM) |
| NYISO | 2022 | **1/30** | `screen_peak_demand_mw` (SEAM) |
| NYISO | 2023 | **1/38** | `screen_peak_demand_mw` (SEAM) |
| PJM | 2021 | 1/36 | `screen_peak_demand_mw` (SEAM) |
| PJM | 2022 | 1/31 | `screen_peak_demand_mw` (SEAM) |
| PJM | 2023 | 1/39 | `screen_peak_demand_mw` (SEAM) |
| PJM | 2024 | **0/39** | — (the weather year: both paths are the same object) |
| PJM | 2025 | 1/39 | `screen_peak_demand_mw` (SEAM) |

**No DECISION, FLEET or ACCOUNTING key moves in any of the three ISOs, in any year.** The partition
was fixed in the PRECOMMIT before the first LP and was not widened.

## 4. NYISO — INERT end-to-end, and the pre-declaration hit exactly

PRECOMMIT §2.2 and §4.2 pre-declared, before the solve: *"NYISO's whole-ledger diff moves
`screen_peak_demand_mw` and nothing else, in every year."* **That is what happened, in all
three years.**

| | 2022 | 2023 |
|---|---:|---:|
| `screen_peak_demand_mw` control → arm | 28,316.918 → 30,505.000 | 28,651.483 → 30,206.000 |
| `screen_adequacy_requirement_mw` | 34,277.584 → **34,277.584** | 34,559.078 → **34,559.078** |
| `screen_entering_firm_mw` | 36,163.560 → **identical** | 35,162.924 → **identical** |
| `screen_reserve_position` | 1.055021 → **identical** | 1.017473 → **identical** |
| `retirements` | 1 row / 1,036.3 MW → **identical** | 4 rows / 420.306 MW → **identical** |
| `reserve_margin` | — | 0.150256 → **identical** |

The seam peak moves by **+2,188.082 MW (2022)** and **+1,554.517 MW (2023)** — 7.2 % and
5.4 % of load — and **not one downstream quantity responds.** The consumer probe shows why,
at both gross and net: `d = 0.0` in every year, both levels. NYISO's D52 gates
(`nyiso_requirement_forecast_peak` + `nyiso_requirement_vintage_factors`, both `True` by
ISO default) make the requirement the published ICAP forecast peak × the adopted IRM,
which has no term in the model's own peak.

**This is a second, independent confirmation of phase 2's central finding.** PJM's
inertness came from D67 (a published whole-RTO Reliability Requirement); NYISO's comes
from D52 (a published ICAP forecast peak). Two different gates, two different ISOs, the
same consequence: **mooting the requirement moots the mechanism.**

## 5. NEISO — the requirement is LIVE, moves as predicted, and NOTHING CONSUMES IT

| | 2022 | 2023 |
|---|---:|---:|
| `screen_peak_demand_mw` control → arm | 23,897.789 → 24,233.000 | 24,075.732 → **23,475.000** |
| `screen_adequacy_requirement_mw` | 24,581.432 → 24,926.232 (**+344.800**) | 24,764.465 → 24,146.548 (**−617.917**) |
| pre-declared Δ | +344.845 | −617.887 |
| **miss** | **0.045** | **0.030** |
| `screen_reserve_position` | 1.307568 → 1.289481 | 1.201617 → **1.232367** |
| `screen_entering_firm_mw` | 32,141.893 → **identical to the cent** | 29,757.413 → **identical to the cent** |
| `retirements` | 29 rows / 2,032.033 MW → **identical** | 1 row / 26.0 MW → **identical** |
| `floor_retained` | **empty, both legs** | **empty, both legs** |
| `fleet_by_fuel_after` | **identical** | **identical** |

**The reversal cell fires directionally and is the lane's own falsifiability.** PRECOMMIT
§5 fixed the sign table before the solve: five ISO-years with a HIGHER arm bar and **one**
with a LOWER bar — NEISO 2023. Measured: the arm's 2023 screen peak is **600.732 MW
LOWER** than the control's, the requirement falls 617.917 MW and the position rises
1.201617 → 1.232367. **All six directional cells HIT.** A mechanism that only ever
lengthened the fleet would be indistinguishable from a one-way retention adder; this one
moves both ways.

**Why nothing downstream moves — measured, not inferred.** NEISO's entering firm census
sits far above its requirement:

| year | entering firm | requirement | **slack** | position |
|---|---:|---:|---:|---:|
| 2022 | 32,141.893 | 24,581.432 | **+7,560.5 MW** | 1.308 |
| 2023 | 29,757.413 | 24,764.465 | **+4,992.9 MW** | 1.202 |

A bar that moves by 345-618 MW against 5.0-7.6 GW of slack crosses no screen threshold.
The signal changes; in this window nothing consumes it. **This is the same shape as phase
2's ERCOT** (§6.3 there: position moved 1.2246 → 1.0179 and zero decisions followed) —
with the difference that ERCOT is energy-only, whereas NEISO has a capacity market and a
backstop that is **armed** (`resolve_reserve_margin_build_enabled → True`) and simply
never fires in-window because the fleet is long.

**Against my own §4.2 pre-declaration:** I wrote that NEISO 2023 decision/fleet movement
was "plausible — the reversal year, with the backstop ON, is where a decision change is
most likely". It did not happen. The prediction was hedged ("plausible", never required),
and the measured reason — slack, not a broken channel — is stated above rather than
absorbed.

## 5A. PJM, RE-MEASURED POST-Q55 — still inert, and the caveat INVERTS

Legs 7-C `b518f5fe7d02f961` (== the bare recipe key at this head) and 7-A
`559c05579b47684b`, **2021-2025**, both at `57bc34a7` with `pjm_vre_accreditation_vintage`
armed, sequential, no commit between them. **STOPs 1-6 all PASS.**

**STOP 2 lands to 0.000 MW in all five years** (149,590.0 / 148,528.0 / 147,605.0 /
153,121.0 / 160,560.0), and 0.000 MW against the ledger's own `peak_demand_mw` in every
solved year. **The whole-ledger diff moves `screen_peak_demand_mw` and nothing else**:
1/36, 1/31, 1/39, **0/39** (2024, the weather year — both paths are the same object), 1/39.
Zero UNCLASSIFIED, zero SCREEN, zero DECISION, zero FLEET. **STOP 5 PASS**: the two
`score.json` differ in exactly one path, `generated_utc`, 3 s apart.

**The charter's question, answered on the leg's own committed pools.** The credits at both
peaks, per delivery year — identical to the zero-LP declaration in Addendum 1 §A1.4, which
was pushed before the solve:

| DY | wind (seam → measured) | solar (seam → measured) | DR-as-supply |
|---|---|---|---|
| 2021 | 0.41 → 0.41 | 0.1064 → 0.1064 | 11,886.8 → 11,886.8 |
| 2022 | 0.41 → 0.41 | 0.1064 → 0.1064 | 10,513.0 → 10,513.0 |
| 2023 | 0.15 → 0.15 | 0.520788 → 0.520788 | 10,116.7 → 10,116.7 |
| 2024 | 0.21 → 0.21 | 0.479587 → 0.479587 | 10,146.4 → 10,146.4 |
| 2025 | 0.38 → 0.38 | 0.135197 → 0.135197 | 6,084.8 → 6,084.8 |

**PHASE 2's CAVEAT INVERTS, and this is the lane's most substantive PJM finding.** Phase 2
§4.1 said PJM's inertness "rests on an ELCC curve that CLAMPS … If
`pjm_vre_accreditation_vintage` arms, PJM's census may become peak-sensitive again."
**Measured: it does not — and the arming makes the inertness STRONGER rather than weaker.**
The evidence is in the *shape* of the rows, not just their equality: probing the resolver
across installed-MW levels (5 / 12 / 25 GW), the 2021-2022 credits still vary with
penetration (solar 0.1064 → 0.08839 → 0.0789) while **2023-2025 are constant across
installed MW**. That is the armed vintage replacing the penetration-indexed *curve* with
PJM's **published per-delivery-year class rating**, whose functional form contains **neither
a peak term nor a penetration term**. Phase 2's inertness was **accidental** — a curve that
happened to saturate; this one is **structural** — a rating the peak cannot enter. The
2021-2022 edge years fall through to the old curve and are peak-independent there too.

**So D76 does not touch PJM at either head, and the reason has changed for the better.**
Phase 1's headline `gas_st` survival (+7,333.7 / +9,464.5 MW) remains gone.

**FC-3 at full magnitude, identical in both legs** (report, never gate) — and this is the
**post-D75-R-ARM** board figure, which independently corroborates that the arm is live in
this control: `retire.total_gw` actual 15.062 / model **17.294** / err_frac **+0.148** FAIL,
against phase 2's pre-arm 18.058 / +0.199 — D75-R's own measured improvement, reproduced
here. `false_retire` 7.596 GW = 43.9 % of model FAIL (phase 2: 8.065 / 44.7 %);
`unit_recall_gt300` 0.650 (13/20), plant 0.700 FAIL — unchanged. Per fuel: `gas_st` 2.702 /
10.297 / **+2.811** and `coal` 10.299 / 6.797 / −0.340 are **unchanged from phase 2**;
`gas_cc` moved 0.903 → **0.139** GW (err_frac +1.081 → −0.679), which is the whole of the
total's improvement. **D75-R-ARM did not touch the steam over-exit**: `gas_st` is still
10.297 GW modelled against 2.702 GW actual, so D74's object survives the arm intact and
D76 remains not a contributing cause at either head.

## 6. THE SIX-ISO CONSUMER TABLE — ALL SIX MEASURED

Phase 0 §4.2 enumerated six direct consumers of the seam peak. Phase 2 measured four ISOs;
this lane adds two.

| consumer (phase 0 §4.2) | measured verdict across the six ISOs |
|---|---|
| **3. adequacy requirement** | **LIVE in 4 of 6** — CAISO, ERCOT, MISO, **NEISO** (new). **INERT in 2 of 6 by two different gates**: PJM (D67-ARM, published whole-RTO RR — **re-confirmed post-Q55**) and **NYISO** (D52, published ICAP forecast peak) — both measured `∂R/∂peak = 0` at both peaks in every year |
| **1. CR-1 reserve position** | LIVE **only as a function of the requirement** — it moves in exactly the ISO-years the requirement moves, never independently. Confirmed again in both new ISOs |
| **5d. reserve-margin backstop** | **LIVE in CAISO only.** Armed in NEISO and NYISO and never fires in-window: NEISO's fleet is 5.0-7.6 GW long, NYISO's bar never moves |
| **5a. retirement reliability floor** | **NEVER BINDS in any ISO** — `floor_retained` empty in every year of every leg of all **six** |
| **4 / 5c. accreditation census** | **PEAK-INERT in all SIX, measured** at both peaks on each control leg's own pools (§6.1) — PJM's now measured **with the ELCC vintage ARMED**, where the inertness is structural rather than accidental (§5A) |
| **2. D59 locality peaks** | n/a — `locality_capacity_curves` default-off in every leg of all six |

**Per-ISO decision effect, the bottom line for an arming decision:**

| ISO | requirement | decisions in the tested window | source |
|---|---|---|---|
| PJM | **no change** (D67-ARM) | **none** — seam field only, all 5 years (2024: 0/39) | **this lane, RE-MEASURED post-Q55 with the vintage ARMED** |
| CAISO | +7,445 / −2,380 MW | **−2,532.391 MW** backstop gas CT (2023) | phase 2, carried verbatim |
| ERCOT | +14,362 / +10,410 MW | none in-window (energy-only; position crosses below 1.0) | phase 2, carried verbatim |
| MISO | +7,189 / +5,578 MW | **343.312 MW** coal saved from a 2024 exit | phase 2, carried verbatim |
| **NEISO** | **+344.800 / −617.917 MW** | **none** — fleet 5.0-7.6 GW above requirement | **this lane** |
| **NYISO** | **0.0 MW, all years** | **none** — requirement peak-independent (D52) | **this lane** |

**Decisions move in 2 of 6 ISOs.** That is the number an arming card has to weigh, and it
is lower than phase 0's code-level enumeration implied — for the reason phase 2 identified
and this lane confirms in a second requirement-moot ISO.

### 6.1 The accreditation census is peak-inert in all six — now complete

`p2_accreditation_probe.py` at the seam peak and the measured peak, on each control leg's
own committed VRE pools:

| ISO | wind credit (seam → measured) | solar credit | source |
|---|---|---|---|
| PJM (**post-Q55, vintage armed**) | 0.41 / 0.41 / **0.15 / 0.21 / 0.38** → identical | 0.1064 / 0.1064 / **0.5208 / 0.4796 / 0.1352** → identical | **this lane** |
| CAISO | 0.16 → 0.16 | 0.18 → 0.18 | phase 2 |
| ERCOT | 0.20 → 0.20 | 0.21 → 0.21 | phase 2 |
| MISO | 0.166 / 0.08 → identical | 0.3875 → 0.3875 | phase 2 |
| **NEISO** | **0.16 → 0.16** (all 3 yrs) | **0.18 → 0.18** | **this lane** |
| **NYISO** | **0.1684 → 0.1684** (all 3 yrs) | **0.1224 → 0.1224** | **this lane** |

Corroborated in the solve: `screen_entering_firm_mw` is **identical between control and arm
in every year of both new ISOs**.

**The caveat phase 2 raised is now CLOSED, and it closed in the direction it feared least.**
Phase 2 §4.1 warned that PJM's inertness rested on a **clamping** ELCC curve and that arming
`pjm_vre_accreditation_vintage` might make the census peak-sensitive again. D75-R-ARM merged
mid-lane and the census was re-measured with it armed: **still peak-inert, and now
structurally so** — the published per-DY class rating has no peak term at all, where the old
curve was inert only because it saturated (§5A). NEISO's and NYISO's rows rest on their own
ISOs' curves and never carried a PJM dependency.

## 7. THE ARMING CARD — **redrafted for the director with five ISOs measured, NOT served**

> **Card: arm `capacity_screen_peak_measured_hindcast`?** *(supersedes the phase-2 §9
> draft; **ALL SIX ISOs now measured**, PJM at the post-Q55 head)*
>
> **What it is.** One gate, one seam, **zero scalar fields, zero free parameters**
> (rules 21/24). Armed, the capacity screens test the solve year's **own measured load** —
> the identical array the LP dispatches — instead of the weather year's load de-grown
> across the span. Rule 14 `[R-ACCURATE]` in its plainest form: a measured input replaces a
> synthesized estimate. Rule 13's forward test is met by construction — a forecast year has
> no measured load, so the growth path remains THE forecast methodology and the gate is
> inert in every forecast year, every crossover forward year and every backcast.
>
> **What arming would change, measured rather than enumerated** — the §6 table. Decisions
> move in **2 of 6 ISOs**: CAISO (−2,532.391 MW of backstop gas CT it does not need) and
> MISO (343.312 MW of coal saved from a 2024 exit, outside the scored window). **Four ISOs
> see no decision change at all**, for three distinct reasons: the requirement is
> peak-independent (PJM/D67, NYISO/D52), the ISO is energy-only so nothing reads the
> position (ERCOT), or the fleet is too long for the bar to matter (NEISO, 5.0-7.6 GW of
> slack).
>
> **The case FOR.** The defect is a construction error on its own terms: the screens test a
> synthesized historical peak against which the same year's LP dispatches a different,
> measured load, wrong by −23.3 % to +15.4 % across the six ISOs. Across **twelve legs in
> six ISOs** every STOP is structurally clean, the identity lands to 0.000 MW everywhere,
> the footprint stays inside the pre-declared partition with **zero unclassified movement
> in any ISO**, and **no determination flips anywhere**. Where it bites it removes phantom
> capacity.
>
> **The case AGAINST, at the same strength.** (a) The **blast radius is real** — it changes
> the screen operand of every hindcast bundle in the repository and every FC-3 T1-H row on
> the board, and every affected ISO's frontier bundle would need re-solving. (b) The
> measured benefit is **narrow and got narrower**: phase 2 read 1 of 4 ISOs with a moving
> scored metric; at 6 ISOs it is **2 of 6 with any decision change**, one of which lands
> outside its scored window. (c) At six ISOs the mechanism is measured **inert in four**, so
> arming buys a *correct operand* rather than a *changed answer* across most of the fleet —
> which is a real argument for arming on rule 14 grounds and a real argument against
> spending a repository-wide re-solve on it now.
>
> **The dependency phase 2 flagged is RESOLVED, and it resolves against arming buying
> anything in PJM.** Phase 2 held that PJM's inertness was conditional on the ELCC clamp
> D75-R repairs, and that arming D76 after D75-R landed "may buy something". D75-R-ARM
> merged mid-lane and PJM was re-measured with the vintage armed: **it buys nothing** — the
> census is peak-inert *more* firmly than before, because the published per-DY class rating
> has no peak term where the old curve merely saturated. **There is no longer an open
> measurement blocking this card.** The decision now rests entirely on the trade in the two
> paragraphs above: a correct operand everywhere against a re-solve of every hindcast bundle
> in the repository, for a measured decision change in two ISOs.
>
> **What this lane recommends.** Nothing — a rule-29 screen may kill an arm and may never
> promote one, and the charter's precondition is a STOP. The measured basis is above; the
> decision is the director's.

## 8. Reported, never gated

**FC-3 at full magnitude, identical in both legs of both ISOs** (so this is the control's
and the arm's number alike). Scored window `[2023, 2024, 2025]` against a 2021-2023 bundle,
so only 2023 is covered — a partial-window read that applies **equally to both legs** and
therefore cannot affect any A/B comparison, but which should not be quoted as a full T1-H
FC-3 score:

| row | NEISO | NYISO |
|---|---|---|
| `retire.total_gw` | actual 4.997 / model 2.721, err_frac **−0.456** — FAIL | actual 1.711 / model 1.457, err_frac **−0.149** — FAIL |
| `retire.unit_recall_gt300` | 0.500 (3/6); plant 0.667 — FAIL | **1.000 (1/1); plant 1.000 — PASS** |
| `retire.false_retire` | 0.879 GW, 32.3 % of model — FAIL | 0.256 GW, 17.6 % of model — FAIL |

Per fuel (actual GW / model GW / err_frac) — **NEISO**: `gas_st` 0.480 / 1.359 / **+1.833**;
`gas_cc` 1.884 / 0.678 / −0.640; `coal` 0.846 / 0.129 / −0.848; `oil` 1.208 / 0.547 /
−0.547; `gas_ct` 0.319 / 0.006 / −0.980; `biomass` 0.262 / 0.002 / −0.993. **NYISO**:
`nuclear` 1.012 / 1.036 / **+0.024**; `gas_ct` 0.189 / 0.420 / +1.227; `oil` 0.390 / 0.0 /
−1.000; `biomass` 0.064 / 0.0 / −1.000; `gas_cc` 0.057 / 0.0 / −1.000.

**None of this is an argument for or against the gate** (rule 1 `[R-STRUCT]`): it is
identical in both legs, so the mechanism moves none of it. NEISO's `gas_st` over-exit
(+1.833) and its four large under-exits are its own object and are **routed, not absorbed**
— they belong to the NEISO retirement lane, not to D76.

### 8.1 A reproduction note, against interest

The runner's own **control** seam peak differs from the zero-LP pre-declaration by
**0.005 to 0.065 MW** (NEISO 2023: ledger 24,075.732 vs pre-declared 24,075.667; NYISO
2022: 28,316.918 vs 28,316.913) — up to 2.7×10⁻⁶ relative, float accumulation order in
`add_load_layers`. **This is an order of magnitude larger than phase 2's 0.004-0.007 MW**,
and the likely reason is stated as a hypothesis rather than a finding: NEISO has no
committed zonal load file for 2021-2024, so both legs fall back to the system-load path,
which accumulates differently. It does **not** touch STOP 2, which tests the **arm's**
screen peak against the **measured** peak — there the match is exact at 0.000 MW — and it
propagates to the requirement misses in §5 (0.045 / 0.030 MW), which are of the same order.

### 8.2 An incidental defect, reported and not fixed here

`scripts/run_capacity_hindcast.py --help` **crashes** with `ValueError: unsupported format
character ','` — an unescaped `%` in an argparse help string. It blocks nothing (the flags
are readable in source) and is outside this lane's scope, so it is reported rather than
repaired mid-lane. Worth a one-line fix in whichever lane next touches that file.

## 9. Matrix (rule 28) and retention (rule 29(c))

Cell verdicts updated in **NEISO.js, NYISO.js and PJM.js** — the three ISOs this lane
actually tested (rule 25 `[R-ISO-SCOPE]`). **CAISO.js, ERCOT.js and MISO.js are NOT
touched**: this lane did not re-test them and their phase-2 cells stand. The `fc` letter
stays **`O`** in all three: the mechanism is measured but not adjudicated — arming is an
owner card.

**All six bundles are DELETED from `results/hindcast/` before this PR merges** (rule
29(c)). This FINDING, the PRECOMMIT and `docs/handoffs/d76/p3_gate_{neiso,nyiso,pjm}.json` +
`p3_predeclare.json` / `p3_predeclare_addendum.json` carry **every number the lane will ever cite**; git history is the
record for the bytes. Nothing is registered on any dashboard — a screen bundle is never
registered, and `KEEP_REQUIRED_UNMAPPED_BUNDLES` is not the route for one.

## 10. Reproduction

```bash
.venv/bin/python scripts/regenerate_clean.py            # fresh checkout only (§2.1)
.venv/bin/python docs/handoffs/d76/p2_predeclare.py --isos NEISO NYISO \
    --out docs/handoffs/d76/p3_predeclare.json          # the pre-solve declaration, zero LP
# four legs, sequential, one at a time, NO commit between the legs of an A/B:
#   scripts/run_capacity_hindcast.py --iso <ISO> --start-year 2021 --end-year 2023 \
#     --vintage 2020 --entry-screen-diagnostics [--no-]capacity-screen-peak-measured-hindcast \
#     --out-dir results/hindcast/d76p3-<iso>-<control|arm>
.venv/bin/python docs/handoffs/d76/p2_gate.py --iso <ISO> \
    --control results/hindcast/d76p3-<iso>-control --arm results/hindcast/d76p3-<iso>-arm \
    --predeclare docs/handoffs/d76/p3_predeclare.json --out docs/handoffs/d76/p3_gate_<iso>.json
.venv/bin/python scripts/score_capacity_hindcast.py --bundle <each of the four>   # STOP 5
.venv/bin/python -m pytest tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py  # STOP 6
.venv/bin/python docs/handoffs/d76/p2_consumer_probe.py --predeclare docs/handoffs/d76/p3_predeclare.json
.venv/bin/python docs/handoffs/d76/p2_accreditation_probe.py --predeclare docs/handoffs/d76/p3_predeclare.json \
    --bundle NEISO=results/hindcast/d76p3-neiso-control NYISO=results/hindcast/d76p3-nyiso-control
```

## 11. What is still open

1. ~~The charter's PJM question~~ — **CLOSED in this lane** (§1, §5A): D75-R-ARM merged
   mid-lane, PJM was re-measured with the vintage armed, and the census is still peak-inert.
   No measurement now blocks the arming card.
2. **NEISO's FC-3 retirement profile** (§8) — `gas_st` +1.833 against four large
   under-exits, identical in both legs, routed to the NEISO retirement lane.
3. **PJM's steam over-exit survives D75-R-ARM untouched** (§5A) — `gas_st` still 10.297 GW
   modelled against 2.702 GW actual, `err_frac` +2.811, unchanged from phase 2 across the
   arm. D74's object, restated with post-arm evidence.
4. **The `--help` crash** (§8.2).


---

## 12. ADDENDUM — the order of work, recorded so the record cannot be read as tidier than it was

This lane did **not** run as one clean sweep, and the sequence is material to how its claims
should be read:

1. The charter's **dispatch STOP was unmet** at session start. Reported; the director
   authorized a reduced scope in session (NEISO + NYISO, PJM deferred).
2. `PRECOMMIT-capx-d76-p3-2026-09-06.md` pushed (`5259d519`) **before the first LP**,
   declaring the STOP failure, the reduced scope, the four keys and the two ISOs' expected
   verdicts.
3. A **fresh-checkout prerequisite** cost the first NEISO attempt (§2.1) — `data/clean`
   absent, the W1-B B3 guard refusing to degrade. Repaired with `regenerate_clean.py`; no
   config, recipe or key change.
4. **NEISO and NYISO solved, graded, and pushed** (`fd4fb62a`), with the FINDING stating in
   its own §1 that the PJM question was open and that the card was a five-of-six card.
5. **D75-R-ARM merged to `main` while this lane was open.** The branch was rebased onto
   `57bc34a7`; the rebase dropped the PRECOMMIT commit as already-merged, and the re-audit
   verified NEISO's and NYISO's keys unmoved.
6. **PRECOMMIT Addendum 1 pushed BEFORE the first PJM LP**, carrying the hunk-by-hunk
   re-audit, the re-declared PJM keys, and the **zero-LP census answer** — so the
   prediction is on the record ahead of the evidence.
7. **PJM solved, graded, and this FINDING updated** from five-of-six to six-of-six.

**What that ordering does and does not buy.** The NEISO and NYISO numbers were fixed before
D75-R-ARM existed and are unaffected by it (verified: keys and pre-declared rows unmoved).
PJM's numbers were predicted at zero LP in a pushed document and then measured — the
strongest form available here, since the prediction could not be revised after the result.
What it does **not** buy is a single-base lane: PJM sits at `57bc34a7` and the other two at
`0f7a4842`. That is stated rather than smoothed over, and it is why **no cross-ISO claim in
this FINDING rests on differencing PJM against NEISO or NYISO** — each ISO's A/B is
internally at one base, which is the only comparison any of them makes.
