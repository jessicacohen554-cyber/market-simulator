# FINDING — capx D76 phase 3: the two deferred ISOs. **Every STOP clean in both; NYISO INERT exactly as pre-declared; NEISO's requirement is LIVE but NON-BINDING. Nothing arms. PJM is NOT re-measured.**

**Lane:** capx D76 phase 3. Branch `claude/capx-d76-p3-neiso-nyiso-pjm-sraz8b`, base
`origin/main` **`0f7a4842`**. Pre-registered in `PRECOMMIT-capx-d76-p3-2026-09-06.md`,
**pushed before the first LP** (`5259d519`). Phase 0/1 record:
`FINDING-capx-d76-2026-09-06.md`; phase 2: `FINDING-capx-d76-p2-2026-09-06.md`.
Instruments (extended, not forked): `docs/handoffs/d76/p2_predeclare.py` (`--isos`),
`p2_gate.py` (`--predeclare`), `p2_consumer_probe.py`, `p2_accreditation_probe.py`;
outputs `p3_predeclare.json`, `p3_gate_neiso.json`, `p3_gate_nyiso.json`.

**NOTHING ARMS.** §7 drafts an arming card **for** the director; drafting is not serving.

---

## 0. Result in one paragraph

**Four legs, two ISOs, one solve-code state, all rc=0; every STOP PASSES in both ISOs.**
STOP 2, the whole structural claim, lands to **0.000 MW in every year of both ISOs**. The
whole-ledger diff moves **1 to 4 fields of 30-38 per year, zero `UNCLASSIFIED` in either
ISO**. **NYISO is INERT end-to-end and this was written down before the solve**: its D52
gates make the adequacy requirement peak-independent, and its ledger moves
`screen_peak_demand_mw` and *nothing else* in all three years — the pre-declared
consequence, confirmed. **NEISO's requirement is LIVE and moves by the pre-declared
amount to within 0.045 MW — and nothing consumes it**: entering firm identical to the
cent, retirements identical, fleet identical, `floor_retained` empty. The reason is
measured, not inferred: NEISO's fleet sits **4.99-7.56 GW above** its requirement
(position 1.20-1.31), so a ±345/618 MW bar move crosses no screen threshold. The
cross-ISO picture is now complete for five of six ISOs and it **narrows further**: the
adequacy requirement is still the only live consumer, it is peak-**independent** in 2 of 6
ISOs by two different gates (PJM/D67, NYISO/D52), and **decisions move in only 2 of 6**
(CAISO's backstop build, MISO's admission cap). The VRE accreditation census is now
measured **peak-inert in all six ISOs**.

**PJM was NOT re-measured, and the charter's PJM question remains open** — §1.

---

## 1. THE CHARTER'S PJM QUESTION IS NOT ANSWERED, and why

The charter's dispatch STOP required D75-R-ARM merged to `main`. **It was not, and is
still not** (PRECOMMIT §0): `origin/main` carries no D75-R-ARM commit, the branch
`claude/capx-d75r-arm-pjm` does not exist on the remote, and `_pjm_config` does not carry
`pjm_vre_accreditation_vintage` — the field sits at its dataclass default `False`. The
ledger sequences D75-R-ARM behind D65-B-R's board write (leg 6 of 7 on `main`). **Owner
ruling Q55 ruled ARM; the arm has not been executed.**

Reported to the director, who authorized a reduced scope in session: run the two ISOs
that do not depend on the PJM ELCC vintage, defer PJM. So the charter's PJM question —
*is the accreditation census still peak-inert now that the ELCC vintage is armed?* —
**cannot be asked at this HEAD**, because the vintage is not armed at this HEAD. A PJM
leg solved now would re-measure phase 2's own verdict and stamping it "re-measured
post-Q55" would be false. **PJM's row in §6 and §7 is phase 2's, carried verbatim and
marked NOT re-measured.** This is a five-of-six card, and it is labelled as one.

## 2. The legs, and the one solve-code state

| leg | ISO | window | cache key | pre-declared? | rc |
|---|---|---|---|---|---|
| 5-C | NEISO | 2021-2023 | `ca4b163f62c4f52f` | **yes, exact** | 0 |
| 5-A | NEISO | 2021-2023 | `69688c797d7bac80` | **yes, exact** | 0 |
| 6-C | NYISO | 2021-2023 | `0641a92f61740d55` | **yes, exact** | 0 |
| 6-A | NYISO | 2021-2023 | `236b56818bed34e9` | **yes, exact** | 0 |

**Every realized key equals the value machine-emitted into `p3_predeclare.json` before the
first LP**, and every control key equals its bare recipe key. All four legs ran
SEQUENTIALLY at one base (`0f7a4842`), one LP at a time; rule 12's two-concurrent
allowance was deliberately not taken (15 GB / 4 cores).

**No commit of any kind landed between the two legs of either A/B** — the rule the
PRECOMMIT §3 added after phase 2 took a literal STOP 3 FAIL from exactly that. It worked:
**STOP 3 finds the five bookkeeping keys and no `git` difference in either ISO** (§3).

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

## 3. The STOP gates — PASS, 6 of 6, in both ISOs

| STOP | NEISO | NYISO |
|---|---|---|
| 1 — no pre-existing key moves (12 recipe keys) | **PASS** | **PASS** |
| 2 — the identity, to the MW | **PASS** | **PASS** |
| 3 — every non-peak operand byte-identical | **PASS** | **PASS** |
| 4 — footprint confined, zero UNCLASSIFIED | **PASS** | **PASS** |
| 5 — no non-target load-bearing flip | **PASS** | **PASS** |
| 6 — one measured load per armed year (by test) | **PASS** (9 passed / 14 subtests) | **PASS** (same test) |

**STOP 2 — the whole structural claim — lands to 0.000 MW everywhere:**

| ISO | 2021 | 2022 | 2023 |
|---|---|---|---|
| NEISO | 0.000 | 0.000 | 0.000 |
| NYISO | 0.000 | 0.000 | 0.000 |

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

**No DECISION, FLEET or ACCOUNTING key moves in either ISO, in any year.** The partition
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

## 6. THE SIX-ISO CONSUMER TABLE — five measured, one carried

Phase 0 §4.2 enumerated six direct consumers of the seam peak. Phase 2 measured four ISOs;
this lane adds two.

| consumer (phase 0 §4.2) | measured verdict across the six ISOs |
|---|---|
| **3. adequacy requirement** | **LIVE in 4 of 6** — CAISO, ERCOT, MISO, **NEISO** (new). **INERT in 2 of 6 by two different gates**: PJM (D67-ARM, published whole-RTO RR) and **NYISO** (D52, published ICAP forecast peak) — both measured `∂R/∂peak = 0` at both peaks in every year |
| **1. CR-1 reserve position** | LIVE **only as a function of the requirement** — it moves in exactly the ISO-years the requirement moves, never independently. Confirmed again in both new ISOs |
| **5d. reserve-margin backstop** | **LIVE in CAISO only.** Armed in NEISO and NYISO and never fires in-window: NEISO's fleet is 5.0-7.6 GW long, NYISO's bar never moves |
| **5a. retirement reliability floor** | **NEVER BINDS in any ISO** — `floor_retained` empty in every year of every leg of all **six** |
| **4 / 5c. accreditation census** | **PEAK-INERT in all SIX, measured** at both peaks on each control leg's own pools (§6.1) |
| **2. D59 locality peaks** | n/a — `locality_capacity_curves` default-off in every leg of all six |

**Per-ISO decision effect, the bottom line for an arming decision:**

| ISO | requirement | decisions in the tested window | source |
|---|---|---|---|
| PJM | **no change** (D67-ARM) | **none** — byte-identical 2021-2025 | phase 2, **NOT re-measured post-Q55** |
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
| PJM | 0.41 → 0.41 (all 5 yrs) | 0.1064 → 0.1064 | phase 2 |
| CAISO | 0.16 → 0.16 | 0.18 → 0.18 | phase 2 |
| ERCOT | 0.20 → 0.20 | 0.21 → 0.21 | phase 2 |
| MISO | 0.166 / 0.08 → identical | 0.3875 → 0.3875 | phase 2 |
| **NEISO** | **0.16 → 0.16** (all 3 yrs) | **0.18 → 0.18** | **this lane** |
| **NYISO** | **0.1684 → 0.1684** (all 3 yrs) | **0.1224 → 0.1224** | **this lane** |

Corroborated in the solve: `screen_entering_firm_mw` is **identical between control and arm
in every year of both new ISOs**.

**The caveat that still stands, and it is PJM's alone.** Phase 2 §4.1 stated that PJM's
inertness rests on an ELCC curve that **clamps**, which is the defect capx D75-R is
chartered to repair, and that if `pjm_vre_accreditation_vintage` arms, PJM's census may
become peak-sensitive again. **That caveat is untouched by this lane** — Q55 ruled ARM but
the arm has not merged, so nothing here tests it. NEISO's and NYISO's rows above rest on
their own ISOs' curves and carry no PJM dependency.

## 7. THE ARMING CARD — **redrafted for the director with five ISOs measured, NOT served**

> **Card: arm `capacity_screen_peak_measured_hindcast`?** *(supersedes the phase-2 §9
> draft; five of six ISOs now measured)*
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
> outside its scored window. (c) **PJM is measured at a HEAD that owner ruling Q55 has
> already superseded** — see below.
>
> **The dependency the director should weigh, and it is now the card's main open item.**
> PJM's inertness is **conditional on the ELCC clamp** capx D75-R repairs. Q55 ruled ARM;
> **D75-R-ARM has not merged**, so PJM's row here is phase 2's verdict at a pre-Q55 HEAD.
> Arming D76 before D75-R-ARM lands buys nothing in PJM; after, it may. **The cheapest way
> to close this card is to land D75-R-ARM and then run the PJM leg alone** — two LPs,
> ~30 min, against a phase-3 protocol that is already written and whose grader is already
> parameterized.
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

Cell verdicts updated in **NEISO.js and NYISO.js only** — this lane's own two ISOs (rule 25
`[R-ISO-SCOPE]`). **PJM.js, CAISO.js, ERCOT.js and MISO.js are NOT touched**: this lane did
not test them, and PJM's phase-2 cell stands as phase 2 left it. The `fc` letter stays
**`O`** in both: the mechanism is measured but not adjudicated — arming is an owner card.

**All four bundles are DELETED from `results/hindcast/` before this PR merges** (rule
29(c)). This FINDING, the PRECOMMIT and `docs/handoffs/d76/p3_gate_{neiso,nyiso}.json` +
`p3_predeclare.json` carry **every number the lane will ever cite**; git history is the
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

1. **The charter's PJM question** (§1) — needs D75-R-ARM merged, then two PJM legs.
2. **NEISO's FC-3 retirement profile** (§8) — `gas_st` +1.833 against four large
   under-exits, identical in both legs, routed to the NEISO retirement lane.
3. **The `--help` crash** (§8.2).
