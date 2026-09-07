# ASSESSMENT miso-243 — **THE PER-YEAR SPP HOURLY LADDER'S CROSS-YEAR PAIRING IS REPAIRED, AND THE FULL SPAN IS THE NEW KEEPER.** `|Z_derive − Z_target|` **0.0395 / 0.0144 / 0.0089 → 0.0003 / 0.0000 / 0.0001**. DETERMINATION **CALIBRATED**

**KEEPER PROMOTED → `2026-09-07-miso-243-spp-pairing`** (bundle
`results/calibration/miso243_sppair_K`), DETERMINATION **CALIBRATED**, C3c the single ledgered
non-downgrading caveat (rubric v3.3). **C1 16/16 all-class and 12/12 free-class; C2, C3a, C3b, C4,
C6 and C8 all PASS; grade summary scored 8 / target 7 / commercial 0 / ledgered 1 / fails 0** —
**identical to the miso-233 predecessor in every one of those.** **DOF ledger UNCHANGED at 41/2.**
Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker, so no marker entry is
re-keyed and **no out-of-training year was solved, scored or registered.** MISO carries exactly
**one** registered run (rule 15); `2026-09-07-miso-233-spp-hourly` is pruned.

Pre-registration: `PREREG-miso243-repair-the-spp-ladders-cross-year-pairing-2026-09-07.md`, pushed
with its probe and **before either ran**. Two addenda, each pushed **before the numbers it
governs**: `ADDENDUM-miso243-my-own-p2-leg-failed-and-the-screen-year-is-2024-2026-09-07.md` (this
session's own failed leg, its repair, and the screen year) and
`ADDENDUM-miso243-the-screen-cleared-all-four-gates-2026-09-07.md`. **Every decision rule applied
below was fixed in one of those three documents; none was written after seeing a number.**

Probes: `scripts/probes/_miso243_spp_pairing_repair_phase0.py` →
`_miso243_spp_pairing_repair_phase0.json`; `_miso243_screen_gates.py` → `_miso243_screen_gates.json`.

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** — the only lever in the lane with
a confirmed construction defect behind it.

**Basis.** The Indiana-hub **RT** series builds the finite-hour `ok` mask, byte-identically to
miso-235…242. Every **spread** is the Indiana-hub **DA**; the SPP anchor is the measured SPP
**NORTH** hub DA; `p_bus` is the keeper's committed `MISO_external` P1 price. They correlate only
+0.402 / +0.424 / +0.553 and are never interchanged. miso-232's measured decile column
(+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

---

## 0. STATED FIRST, AGAINST INTEREST — five disclosures, and the first two cost this session something

### 0a. **THIS SESSION'S OWN P-2 LEG FAILED**, and the failure was published before it was repaired

Nine of ten pre-registered legs passed on the first run. **P-2, this session's own byte-identity
leg, FAILED at 0.01** on PJM 2023 and South 2023 / 2024 against a 0.005 bar.

**Diagnosed against the leg, not against the repair.** P-2 was written to test *"the caller change
moves nothing else"* but **measured** the repaired caller's output against the **committed registry
table** — two claims, conflated. Measured directly: `derive(g.loc[y])` vs `derive(g.loc[[y]])` is
**EXACTLY 0.0 on every seam in every year.** The one cent is a **PRE-EXISTING** gap between the
committed **incumbent** `MISO_SEAM_LADDER_BY_YEAR` and its own derive at HEAD, magnitude exactly
`NO_WASH_EPS`, present with the old caller and **not created here**.

The repair was declared in a **pushed addendum before the repaired numbers existed**, **no bar was
moved**, and it is **stricter**: P-2′'s bar is **exactly 0.0**, not a tolerance. The pre-existing
gap is **reported, not fixed here** — a different object, outside this queue item — and handed
forward as a named successor (§7).

### 0b. **G-2 AS PRE-REGISTERED WAS NOT MEASURABLE**, disclosed before the screen ran

PREREG §3's G-2 asked for a per-seam gross-flow comparison. **The committed sidecars carry no
per-seam split** — only an aggregate net `import` class. The available per-seam route is miso-241's
**reconstruction** (corr 0.9917 / 0.9935 / 0.9935 — close, not 1), and **this session declined to
gate on a reconstruction when a directly measured quantity was available.** G-2′ replaced the
unmeasurable comparison with two directly-measured falsifiable limbs; G-2's second limb is
unchanged verbatim and **G-1, G-3 and G-4 were untouched.**

### 0c. **THE SCREEN YEAR IS 2024. THE HANDOFF EXPECTED 2023, AND THE PRE-REGISTERED RULE OVERRULED IT**

`F(year)` = the share of derive rows whose SPP band-count vector `(n_i, n_e)` changes:
**0.0910 / 0.2376 / 0.1722**. The rule `argmax F` was fixed in the PREREG **before either number
existed**, and stated explicitly that *if `F` names a different year, `F` wins*. It named **2024**.
Both `F` and the handoff's `|Z_derive − Z_target|` are **footprint** measures and **neither is a
residual**; they rank differently because a dead-band **edge** displacement need not move many
**hours** across band thresholds. *Reported, not part of the rule: on the model basis the 2023
pre-solve effect is **+5.25 MW** on a 3,350 MW mean seam — a screen there would have measured
almost nothing.*

### 0d. **THIS SESSION'S INDEPENDENTLY DERIVED VALUES AGREE WITH miso-242 §5a TO THE CENT**

Band 1 import **13.44 / 17.26 / 18.58**, export **−2.39 / +1.44 / −2.37**. The handoff declared
miso-242's numbers **UN-TARGETABLE**; these were derived here from source and **nothing was tuned,
selected or reconciled to them**. The agreement is **expected** — the estimator is deterministic and
both sessions ran the same one on the same measured series — and it is disclosed rather than
presented as independent corroboration.

### 0e. **THE BANDS DID NOT MOVE IN THIS SESSION'S FAVOUR ON NET, AND THAT IS NOT A REASON TO REVERT**

On the full span the collateral gate reads **zero flips** and **23 scored moves split 11 TOWARD /
12 AWAY** (§4). Rule 1 `[R-STRUCT]` says a structurally-correct mechanism is never judged by the
residual and is never reverted because the residual didn't move, and the owner frame the handoff
carries forward says the same. **The basis for this keeper is the restored identity (§3), not a
band.** Every band is published at full magnitude in §4 either way.

---

## 1. THE DEFECT, AND WHY IT IS A CONSTRUCTION DEFECT RATHER THAN A DATA CHANGE

`derive_spp_neighbour_hourly(g)` does `work = g.join(load_spp_hub_da(), how="left")`.
`load_spp_hub_da()` is **`(year, hour)`-MultiIndexed**; both callers passed **`df.loc[year]`**,
whose index is **`hour` alone**. pandas partial-joins on the shared level name, so each of the
year's 8,760 MISO rows was replicated against **all three years'** SPP hub price for that hour.
`derive_pjm_neighbour_hourly` performs **no join** — that asymmetry is the signature.

**What was and was not contaminated, exactly.** The 3× replication leaves every **flow** exceedance
share untouched (replicating a sample three times does not change a share), so the estimator's
**targets** `P(flow > +mid_k)` and `P(flow < −mid_k)` were **correct**. **The quantile was drawn
from a three-year mixture of the spread instead of the year's own.**

**Rule 23 `[R-FROZEN-DERIVE]` asks a re-derive to cite its cause. The cause cited is the join.**
Not a source-data update, and not a residual that moved. Rule 14 `[R-ACCURATE]` governs directly and
its misalignment exception **cannot** apply: the mispaired sample is not a differently-bounded
measured series, it is the same series joined wrongly. Rule 1 `[R-STRUCT]`: **the pairing was not
selected by which arm scores better** — both ladders are fully determined by the frozen estimator
before any solve runs, so there was nothing to select. Rule 21 `[R-DOF]`: **zero free parameters
added**; the repair removes an error, it does not add a knob, and the ledger stays **41/2**.

---

## 2. THE PROVENANCE GATE — **ALL SIX LEGS PASS**, and three of them could have killed the diagnosis

| leg | what it reproduces, in the predecessor's own metric | bar | **measured** |
|---|---|---:|---:|
| **G-T** | the committed SPP + PJM hourly tuples = PREREG §0 F4; monotonicity both seams, all years | exact / 0 | **exact, 0** |
| **G-V1** | miso-242's V-1 — the mispaired join = **26,280** rows in three 8,760 blocks, `da`/flow deviation | exact / 0.0 | **exact, 0.0** |
| **G-V2** | miso-242's V-2 — the **mispaired** frame reproduces the **COMMITTED** table, all 48 entries | ≤ 0.005 | **0.0** |
| **G-V3** *(CONTROL)* | miso-242's V-3 — PJM's **no-join** derive reproduces its own committed table, all 48 | ≤ 0.005 | **0.0** |
| **G-V5** | miso-242's V-5 — the **POOLED** forward ladder is correctly paired, all 16 | ≤ 0.005 | **0.0** |
| **G-DOC** | the derive script's **own docstring** `corr(measured flow, derive spread)` = +0.041 / −0.020 / +0.050 | ≤ 0.002 | **PASS** |
| **P-2′** | OLD caller vs NEW caller, every seam, every year (§0a) | **exactly 0.0** | **0.0** |

**G-V2 and G-V3 are jointly falsifiable**: had the committed table not come from the mispaired path,
or had PJM's no-join derive also failed to reproduce, the diagnosis would have died here. The
diagnosis is confirmed on this session's own independent code path.

---

## 3. **THE BASIS FOR THE KEEPER — THE Q-Q IDENTITY IS RESTORED.** The falsifiable leg, and it could have failed

The estimator asserts an identity: on the derive's own spread, the dead band
`[δ_1^export, δ_1^import]` captures `P(|flow| ≤ 250 MW)` **by construction**. Dead-band membership
evaluated in the instrument's **own two operand forms** (the import leg a subtraction, the export
leg an addition — miso-242's §0a repair, carried forward):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `Z_target` (measured flow alone, no price) | 0.3501 | 0.3580 | 0.3698 |
| `Z_derive` — **COMMITTED** (mispaired) | 0.3897 | 0.3724 | 0.3787 |
| `Z_derive` — **REPAIRED** | **0.3498** | **0.3580** | **0.3696** |
| `|Z_derive − Z_target|` committed | 0.0395 | 0.0144 | 0.0089 |
| **`|Z_derive − Z_target|` REPAIRED** | **0.0003** | **0.0000** | **0.0001** |
| bar, fixed before the number | ≤ 0.005 | ≤ 0.005 | ≤ 0.005 |

**A bar four times tighter than miso-242's Q-A used, met with two orders of magnitude to spare in
every year.** miso-242's Q-A read IDENTITY **FAILS** on 2023 against the committed table; on the
repaired table the identity is essentially exact. **This, and not any band, is why the run is a
keeper.**

**The repaired ladder, all 48 entries** — every one an output of the frozen estimator; nothing
rounded, damped, re-spaced or chosen, `K` unchanged at 8, and the no-wash reconciliation raised no
clamp note:

| year | `import` band 1…8 | `export` band 1…8 |
|---|---|---|
| 2023 | 13.44, 30.30, 50.82, 83.92, 123.33, 152.94, 152.94, 152.94 | −2.39, −21.49, −41.89, −90.15, −178.51, −212.03, −212.03, −212.03 |
| 2024 | 17.26, 37.56, 65.15, 139.78, 230.88, 230.88, 230.88, 230.88 | 1.44, −12.98, −23.83, −33.09, −43.06, −48.41, −55.24, −66.13 |
| 2025 | 18.58, 41.90, 78.87, 152.95, 197.69, 237.84, 271.99, 338.83 | −2.37, −19.00, −31.11, −44.88, −70.49, −122.45, −254.63, −254.63 |

### 3a. **THE DEFECT CANNOT RETURN**, and the pin test was made stricter in the same commit

1. **The derive itself raises** if the hub join changes the row count. A left join can never
   legitimately add rows, so this is an **invariant of the operation**, not a tolerance, and it
   fires from **any** caller. Verified: it raises on the old caller in all three years.
2. **The rule-23 pin test was repaired IN THE SAME COMMIT** — it would otherwise have kept passing
   on the mispaired table, since it invoked the same defective call. It now passes
   `joined.loc[[year]]` **and additionally asserts the join's row count**, which is the assertion
   that would have caught this. **No `atol` was loosened and no assertion removed.** It reproduces
   the repaired table at **exactly 0.0** in all three years.
3. The **POOLED forward ladder** was always correctly paired (`df.loc[a:b]` keeps the MultiIndex)
   and is **untouched**. **Rule 13's forward story is intact**; only the per-year backcast table was
   implicated.

---

## 4. THE SCREEN, AND THE FULL SPAN — every band at full magnitude, and gated in neither direction

**Rule 29 `[R-SCREEN]` end to end.** Zero-LP phase 0 first. **ONE** screen year — **2024**, named by
the footprint rule (§0c), on the mechanism's own measured footprint and **never** the residual.
Control = **the miso-233 keeper's COMMITTED bundle** (G-CTRL form 4). **No control solve was
spent**, on a G-DRIFT audit recorded in the PREREG before any arm was solved (§6).

**All four pre-registered STRUCTURAL STOP-only gates cleared**, none of them the target residual:

| gate | bar, fixed before the solve | **measured** |
|---|---|---:|
| **G-1 CONFINEMENT** | slack + dump not above keeper; must-take within 0.5 % | slack **19,566.915 → 19,566.915 MWh** (Δ 1.5e-11), dump **0 → 0**, must-take **0.00 %** |
| **G-2′(a) DISPLACEMENT** | `Σ|Δ class| / |Δ import|` ≤ 4.0 | **0.9991** (imports −423,500 MWh, generation +423,112 MWh) |
| **G-2′(b) SCALE** | served energy ≤ 0.5 % | **−0.00006 %** |
| **G-3 DIRECTION & MAGNITUDE** | NEGATIVE sign; `Δq ∈ [−430.60, −26.91] MW` | **−48.345 MW**, ratio **0.4491** |
| **G-4 COLLATERAL** | zero PASS → FAIL flips | **0** |

**G-2′(a) at 0.9991 is the informative one**: the seam's lost imports are replaced almost exactly
one-for-one by MISO generation — a seam change and its direct displacement, not a fleet re-shuffle.
The bar allowed a factor of 4. **G-3 landed at 0.449 of the pre-solve prediction**, in the direction
the addendum stated *before* the solve: the measured `(month × hod)` ceiling can only **clip** the
band response, so `Δq̂` is an upper bound and the window's **lower** limit is the binding side.

### 4a. THE FULL SPAN, REPORTED AND NOT GATED — **zero flips, 23 scored moves, 11 TOWARD / 12 AWAY**

| criterion · year · row | keeper → **arm** | |
|---|---|---|
| C1 2023 CC_REGULAR / CC_CHP / CT_PEAKER | −6.445 → −6.460 · −1.991 → −1.994 · −3.052 → −3.056 | away |
| C1 2023 ST_GAS | 0.409 → 0.401 | toward |
| C1 2023 ST_CHP / COAL_PRB / COAL_LIGNITE / COAL_BIT | −2.717 → −2.718 · −1.768 → −1.781 · −0.683 → −0.684 · −2.952 → −2.953 | away |
| C1 2024 CC_REGULAR | 3.755 → 3.870 | away |
| C1 2024 CC_CHP / CT_PEAKER / ST_GAS / ST_CHP | −0.746 → −0.712 · −1.934 → −1.830 · −5.079 → −5.038 · −2.762 → −2.759 | toward |
| C1 2024 COAL_PRB / COAL_LIGNITE / COAL_BIT | −3.443 → −3.360 · −0.773 → −0.772 · −3.562 → −3.532 | toward |
| C2 2023 gas / coal | −13.80 → −13.83 · −5.25 → −5.26 | away |
| C2 2024 gas / coal | −6.76 → −6.47 · −7.66 → −7.55 | toward |
| C3a 2023 / 2024 / 2025 | 2.12 → 2.11 · 1.14 → 1.19 · −2.36 → −2.40 | toward / away / away |

**2023's moves are away and small; 2024's are toward and larger.** Every 2025 C1/C2 row is SKIPPED
on both sides (preliminary EIA-923 vintage) — **a 2025 C1 pass is never read as evidence.**

**Also reported, never gated, and named with its basis:** model net imports
**44.17 → 44.22 / 29.34 → 28.92 / 20.62 → 21.06 TWh** against a measured **32.52 / 20.02 / 19.95**;
`corr(model net imports, measured Indiana-hub **DA**)` **−0.2606 → −0.2616 / −0.2289 → −0.2304 /
−0.2867 → −0.2882** against a measured **−0.1937 / −0.1416 / −0.0829** — **marginally further from
measured in all three years.** C5a CO2 −4.2 / −4.6 / −0.2 % → **−4.2 / −4.5 / −0.3 %**. C3c tail
**3 / 7 / 11 h** > $200 against a measured 30 / 37 / 88 h, unchanged.

**None of these is a criterion in either direction.** They are recorded so the direction of travel
is visible rather than selected from.

---

## 5. Rule 19 `[R-ONE-MECH]` — the enumeration, and why nothing stacks

What sets the MISO–SPP seam on this keeper is unchanged in **kind**: the armed hourly SPP neighbour
anchor (`miso_seam_neighbour_hourly_spp`); the frozen Q-Q `δ_k` ladders — **the one object this
session repaired, in place**; the incumbent MISO-hub ladder it displaces (an alternative, never
stacked); the measured `(month × hod)` deliverability envelope; the 4,000 MW interface limit and its
eight 500 MW bands; the `MISO_external` border-link TTCs; the 8,700 MW `MISO_simultaneous_import`
SIL; and the published CIL/CEL groups. **Nothing was added**, so nothing replaces and nothing must
be reconciled, and the mechanism count is unchanged.

---

## 6. Governance

Rule 1 `[R-STRUCT]`: the repair is argued on construction and rule 14, **never on a residual**;
every gate was structural and STOP-only; the screen year came from a footprint rule containing zero
model output; §0e states plainly that the bands did not move in this session's favour on net and
that this is not a reason to revert. Rule 12 `[R-PARALLEL]`: years **sequential** in one invocation,
solved in-session, never on CI. Rule 13 `[R-MEASURED]`: no measured outcome entered any solve; the
forward ladder is untouched and regenerates as before. Rule 14 `[R-ACCURATE]`: the accurate pairing
is preferred **whatever it does to the residual**; the envelope, its percentile and every interface
limit are untouched. Rule 15 `[R-DASHBOARD]`: registered, superseded run pruned, keeper `hourly/`
sidecars committed; MISO carries exactly one registered run. Rule 16 `[R-ALLYEARS]`: 2023 + 2024 +
2025 in ONE invocation and ONE bundle; the 2024 screen is a throwaway probe, never registered, and
its year was re-solved inside the full bundle. Rule 17 `[R-FLOOR-WINDOW]`: no floor added. Rule 19
`[R-ONE-MECH]`: nothing added (§5). Rule 21 `[R-DOF]`: **41/2, unchanged**; zero free parameters
added. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; no `complete` marker, none sought, no out-of-training
year touched. Rule 23 `[R-FROZEN-DERIVE]`: a re-derive citing a **construction defect**, stated as
such in the commit, the table, the attestation and here — and the pin test repaired in the same PR
and made **stricter**. Rule 24 `[R-REGISTRY]`: **no field created**, no env knob, no CLI flag.
Rule 25 `[R-ISO-SCOPE]`: MISO's shard, section, keeper and lane only; the SPP hub series is read as
a measured **price input**, never as SPP's calibration, and SPP's own lane is untouched. Rule 26
`[R-DELETE]`: the defective caller is **replaced**, not left behind a flag. Rule 27 `[R-PUSH]`:
on-disk edits only; every pushed blob ≥ 300 lines verified against local after push. Rule 28(a): the
handoff's recommended item taken; every standing adjudication is corroborated or untouched, never
re-tested. Rule 28(b): the cell's evidence and the keeper/gates stamp updated in **MISO's shard
only**, in-session. Rule 29 `[R-SCREEN]`: clause 0 (zero-LP phase 0), clause 1 (one screen year on
the mechanism's own footprint), clause 2 (full span only after the gate cleared), clause (b)
(**G-DRIFT `e852c85c..HEAD`, every hunk classified INERT — capx D76 verified inert at the object
level, and the one genuinely shared data seam `_screen_fuel_spike_columns` **measured** at 0
repaired MISO cells in all three years — corroborated by `surface_stamp` reproducing the keeper's
fingerprint `8ee657ee4c7c49b0` with `moved:{}`; **no control solve spent**), and clause (c) (the
screen bundle is `.gitignore`d and never reached `main`). Rule 31 `[R-RETAIN]`: **nothing solved was
deleted**; the screen bundle is on local disk and the promotion question is surfaced explicitly.

---

## 7. What is handed forward

1. **NAMED SUCCESSOR, with its exact magnitude and location:** the **incumbent** table
   `MISO_SEAM_LADDER_BY_YEAR` does not reproduce its own derive to the cent on **PJM 2023 (0.01)**,
   **South 2023 (0.01)** and **South 2024 (0.01)** — magnitude exactly `NO_WASH_EPS`.
   **Pre-existing, not created here, not gated on here.** **South is the seam actually cleared on
   that table**, and South is the larger remaining cancelling seam.
2. **THE STRUCTURAL ITEM RULE 1 NAMES IS UNTOUCHED AND THIS REPAIR DOES NOT CLOSE IT.** The model's
   SPP seam is 0.70–0.79 spread-correlated while the measured one is +0.0409 / −0.0200 / +0.0502.
   The seam being idle is not the anomaly; its being spread-driven is. Any future SPP work should
   start from **that**.
3. **C3c remains the designated frontier** (model 3 / 7 / 11 h > $200 vs measured 30 / 37 / 88 h).
   It opens only by a new admissible measured identification under its own charter **plus an owner
   ruling**, never by an offer adder, an ORDC offset, a scarcity multiplier or any level tuned to
   the tail. **No such thing was proposed, computed or armed here.**
4. **SOUTH stays excluded from the hourly form** and that stays a **data boundary**: SOCO and TVA
   publish no hub price.
5. **UNCHANGED AND NOT RE-TESTED:** the SPP quantity-side charter stays **REFUSED — no DOF-free
   form** (miso-241 §5, C1–C7, and its C7 census is not re-run); queue item 1 stays **ANSWERED AND
   DECOMPOSED**; the merit test's sign and basis stay **REFUTED as a defect**; the PJM/SPP idle
   contrast stays a **measured-record** fact; the external-bus-price half stays **CLOSED**; the
   per-seam external-node split **REFUSED at zero LP**; saturation **REFUTED**; miso-239 Q-A
   **MIXED** / Q-C **SURVIVES**; miso-240 Q-B **UNRESOLVED**; the `(month × hod)` template
   hypothesis **REMOVED**; the PJM import/export asymmetry **CLOSED FOR PJM**; South's
   neighbour-state route **CLOSED**; `miso_manitoba_seam` **CLOSED as already-armed**;
   `internal_congestion_split` **G**; `vre_reference_rate_curtailment_grossup` **K**;
   `measured_interface_limits` **R**; `miso_rdt_measured_limit` **R**; `m2m_seam_entitlement_cap`
   **G**; `miso_south_firm_export_block` **G**; `miso_south_export_ladder_rt_tail` **R**;
   `miso_south_gas_delivered_cost_basis` **R**.
6. **Manitoba determinism**, **the CC_REGULAR 2024→2025 shape emergence** and **Q-B's bus-price
   volatility successor** are untouched and stay where they are filed.

## 8. Non-claims

1. **No new mechanism exists.** No `ScenarioConfig` field changed, none was created, and the DOF
   ledger is unchanged. The delta is a committed derived table, re-derived correctly.
2. **The repair does not close the SPP seam**, does not touch C3c, and does not claim to move the
   system interchange ratio; the reconstruction-based ratio was **not re-measured here** and is
   **not** restated as reproduced.
3. **No out-of-training year was solved, scored or registered**, and no marker was sought.
4. **MISO has no failing gate**, this session did not invent one, and nothing here trades a passing
   gate for anything.
5. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage** on both sides; no 2025 C1 pass is
   read as evidence.
6. **The screen promoted nothing** — all four gates are STOP gates — and the screen's numbers are
   not quoted as keeper numbers.
