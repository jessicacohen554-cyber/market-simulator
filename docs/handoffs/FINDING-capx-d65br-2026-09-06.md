# FINDING — capx D65-B-R: the coupled-arming BATCH under corrected per-ISO gates

**Session:** capx D65-B-R · **Date:** 2026-09-06 · **Branch:** `claude/capx-d65br-batch-nmrwww`
**Authority:** OWNER RULING **Q47** (*"Arm coupled, after D60-R3"*), completed under **director
adjudication r#48 §3(a)** (`capx-director-ledger-2026-08.md` §0as.3) — D65-B's G1 and G3 were
**charter defects**, the ERCOT screen is **NOT re-run**, and the batch proceeds under structural
gates re-derived per ISO from **D64 §2.4's own rows**.
**Pre-registration:** `PRECOMMIT-capx-d65b-2026-09-06.md` **Addendum C**, committed and pushed
(`5c82c9d7`) **before any batch leg solved**.

---

## 0. The verdicts

**THE BATCH VERDICT: the coupled arm is MEASURED ON ALL SEVEN LEGS, every solve key equal to its
pre-declaration to the digit, and the seam behaves as constructed.** Three gates fired across the
seven legs; **none of the three is the arm's**, and §0.2 records why with its arithmetic rather than
by assertion. Nothing was armed by this batch beyond the two acts already on `main`, no
determination was written, and no gate was retro-declared passed.

### 0.1 The board — seven legs, seven rows

| # | leg | run_id | solve key | = pre-declaration | wall / RSS | gates | verdict |
|---|---|---|---|---|---|---|---|
| 1 | `ercot-t1f` | `ercot-2026-2030-d65br-arm` | `9b9e5a48e3ca5c8e` | Addendum C ✓ | 14.7 min / 3.92 GB | G0'–G6' **all PASS** | **ALL CLEAR** |
| 2 | `neiso-t1f` | `neiso-2026-2030-d65br-arm` | `c3519b861f920bbe` | Addendum C ✓ | 10.6 min / 3.30 GB | **G5' FIRED** → VOIDED as a STOP (r#51 §3(b)); all others PASS; 14/14 invariants | REGISTERED, unbinding REPORTED |
| 3 | `nyiso-t1f` | `nyiso-2026-2030-d65br-arm` | `f62431376dd9df03` | Addendum C ✓ | 14.2 min / 3.15 GB | **G5' FIRED ×2** → VOIDED (r#51 §3(b)); all others PASS; 14/14 | REGISTERED, unbinding REPORTED |
| 4 | `caiso-t1f` | `caiso-2026-2030-d65br-arm` | `17770cdad3230938` | Addendum C ✓ | 35.5 min / 4.53 GB | G0'–G6' **all PASS**; G4' `changed: none` | **ALL CLEAR — the control case** |
| 5 | `pjm-t1f` | `pjm-2026-2030-d65br-arm` | `542eeedadab83ee1` | **Addendum E** ✓ | 55.6 min / 8.69 GB | G0'–G6' **all PASS**; G4' `changed: none` | **ALL CLEAR** |
| 6 | `miso-t1f` | `miso-2026-2030-d65br-arm` | `74359fedbf2eadd6` | Addendum C ✓ | 53.9 min / 9.63 GB | retrofit gates **PASS**; **G4' FIRED** | REGISTERED, flip attributed (§5.6) |
| 7 | `neiso-t3` GOLDEN-3 | `neiso-2026-2050-t3-golden3-d65br` | `0fc42cb56c24d544` | Addendum C ✓ | 30.1 min / 3.56 GB | G0'–G6' **all PASS**; G4' identical fail set | **ALL CLEAR** |

Every row reconciles to a committed artifact — its sidecar under `frontend/data/hindcast/`, its
bundle under `results/`, and its key re-verified at four successive HEADs (Addenda C, D/E, G, H).

### 0.2 THE BASIS DISCLOSURE — three fired gates, ONE root

Leg 6 established the general form, and it is quoted here rather than paraphrased because §0 owes
it in these terms:

> **All three fired gates share one root: Addendum C compares a HEAD solve against a prior that
> predates HEAD, and two of the three are measuring that gap, not the arm.**

The director graded it a step further at r#52 — *"THREE of three fired gates in that batch my
Addendum-C basis rather than the arm"* — and the arithmetic below is why. **This is a BASIS
DISCLOSURE, not a re-grade.** No leg's numbers change, no gate is retro-declared passed, no prior is
re-solved, and every fired gate stays reported at full magnitude on its own leg.

**(a) G5' on `neiso-t1f` and `nyiso-t1f` — the comparator is a census taken on another shape.**
D64 §2.4's per-ISO cells are evaluated **at the hour ceiling** (every hour in merit) on the
**shipped** posture, which makes them an **upper bound** on what a solve converts. Addendum C
quoted NEISO's and NYISO's cells as *"cap-bound"* and wrote the STOP as *"the 3 GW/yr cap does NOT
bind in a year"* — promoting a ceiling-census cell into a **floor on a solved quantity**. That is
the same "a band is a window, never a floor" error Addendum C itself warns about for ERCOT's G1',
committed one paragraph later in its own table. And the source it read from says the opposite in
terms: D64 §2.3, *"a year converting materially below the cap would be **the informative surprise,
not a STOP**"* — naming **NEISO and NYISO together**. Director adjudication **r#51 §3(b)** VOIDED
G5' as a STOP for the cap-bound legs and reclassified it to **REPORTED**; both legs registered
exactly as the three cleared legs did, and **the CEILING form of G5' on `ercot`/`pjm`/`miso` is
untouched** and passed on all three.

**(b) G4' on `miso-t1f` — the comparator is a prior on the old demand table.** G4' asks whether a
non-target load-bearing FC row flips PASS → FAIL **against the leg's `-pre-d65b` prior**, and MISO's
only available prior (`ff-t1f-d60/miso`) was solved at `2ef4326e`, which D65-B §5's own G-DRIFT
table names as **PRE-hunk on SCN-LOAD `d14a7ed0`** (`DEMAND_GROWTH_RATES`, all six ISOs). Higher
demand growth ⇒ more unserved energy ⇒ I3 fails and the load-weighted price leaves I14's band. So
the firing is a **cross-vintage** reading, and D65-B §5 consequence 2 pre-registered exactly this
before the batch ran: *"the batch's board-level before/after is confounded by the demand vintage for
the four pre-hunk ISOs … reported at full magnitude and attributed, never netted"* — naming
`2ef4326e (miso)` as one of the four.

**And the flip is provably not the acts', on the arm's own arithmetic — three independent legs:**
I3 fails **starting in 2026** (`2026: slack 0.02 % of load, 19 h, 111.6 GWh`; `2027: 0.03 %`);
`apply_ccs_retrofit` **returns at `if year < config.ccs_retrofit_available_year`** (2028) before
reading either field, and that call site is the only consumer of both; and **G0' independently
measured 0 retrofit rows in 2026 and 2027** on this very leg. *A mechanism that does not execute
cannot have caused a failure in the years it does not execute in.*

**What the disclosure does not do.** It does not convert a FIRED gate into a PASS. NEISO's and
NYISO's G5' firings are recorded as FIRED and voided **by the director, not by the session that
wrote them** — a STOP a lane may edit on seeing the number is not a STOP (D65-B §6.6; rules 1
`[R-STRUCT]` / 29 `[R-SCREEN]`). MISO's G4' stands as FIRED on its leg, attributed and not netted.

### 0.3 What the batch actually established

1. **The seam's thesis reproduced, not asserted.** Both RGGI ISOs start cap-bound at MW-weighted
   `k` ≈ 1.0 and unbind as the surviving host pool passes `k` > 1.2 (NEISO 0.9952 → 1.3032, 59.5 %
   of cap in 2030; NYISO 1.0544 → 1.2235, 33.3 %), while **CAISO — the third carbon-priced ISO,
   armed identically — never leaves `k` 1.03–1.08 and stays cap-bound at 96.4 %.** The unbinding is
   a **fleet-composition effect predicted by `k` and by nothing else**: the efficient hosts are
   consumed first, and the expensive tail cannot carry the accurate per-tonne cost.
2. **Two ISOs, two bands, each in its own.** ERCOT's rows land at `er/phys` **0.9672–1.0456** inside
   D64's ERCOT row **0.95–1.05**; PJM's at **1.2668–1.4886** inside **1.27–1.49**; MISO's at
   **1.2898–1.3930** inside **1.26–1.39**. That is the **empirical vindication** of director
   adjudication r#48 §3(a), which had ruled on documentary grounds alone that D65-B's `≥ 1.27`
   floor was PJM/MISO's band transcribed onto an ERCOT screen.
3. **G2' is answered for the first time.** D65-B could not evaluate it at all — the ledger dropped
   the scaling record. After step 0 it reads straight off the bundle: `fixed_cost_scale ==
   capex_scale` on **every** row of **every** leg, and `capex/k` host-invariant **to three decimals**
   across hosts spanning `k` = 1.0025 → 1.6907. The cross-year fall is the **learning curve**, not a
   broken identity.
4. **A zero-LP census and a full 8760 dispatch agreeing to four parts in a thousand.** PJM's 2028
   solved value is **408.2 MW** against D64 §2.4's **0.41 GW** hour-ceiling census — **99.6 %** of a
   prediction computed months earlier with no LP at all.
5. **The GOLDEN-3 horizon answers D64 §2.3's own conditional, and the answer is not a level
   effect.** §2.3 wrote that the horizon *"is only re-solved if the NEISO t1f arm shows the cap
   unbinding"*; leg 2 showed it, so leg 7 was **positively indicated by the source document**. It
   measures the unbinding **persisting and deepening** — 2030 to 59.5 % of the cap, 2031 to
   **33.3 %** — and then **not one retrofit row in 2032–2050**, across nineteen years over which the
   RGGI ladder climbs to **$67/t by 2040**. A carbon price that roughly doubles does not reclaim the
   `k` > 1.2 tail, and §45Q's 2032 expiry is not the binding constraint because conversion stops the
   year *before* it. **The host pool is exhausted, not priced out** — which is what §5.4's CAISO
   control predicted from composition alone. D64 §2.3's *"not expected to move in kind"* is
   **confirmed as measured**: 29 rows, every one `gas_cc → gas_cc_ccs`, no class gained in either
   direction.
6. **A cross-horizon reproduction nobody asked for.** Leg 7 (2026–2050) reproduces leg 2
   (2026–2030) **byte-for-byte on every overlapping retrofit year** — 12 / 2,965.4 MW, 9 / 2,939.8,
   7 / 1,786.1, with identical MW-weighted `er`/`hr`/`k` and identical `capex/k` to three decimals.
   Two independent solves at two horizons and two cache keys, one ledger. **The screen is
   horizon-independent inside its own window**, so §5.2's unbinding is not an artefact of where the
   t1f window stopped.
7. **The `ff-verdicts.json` question is answered NO, from the code path** (§7), and the
   D72-prehunk `neiso-t1f` residue key is **DISCHARGED** (§6.5).

---

## 1. Step 0 — G2 made evaluable, at zero LP

D65-B could not evaluate its own G2 gate: `evolve_fleet` recorded a conversion as
`{unit_id, mw, from_fuel, to_fuel}` and **dropped** the `retrofit_log` that carries the island
sizing, so the seam's own identity and host band had to be reconstructed offline from CAMPD
(FINDING-capx-d65b §6.4) — the D65 §3d defect class, *a diagnostic blind to the mechanism it exists
to make visible.*

Each `ccs_retrofits` ledger row now carries the screen's own values for **`capex_scale`,
`fixed_cost_scale`, `retrofit_capex_per_mw`, `annual_net_savings_per_mw`** (the in-window uplift),
**`vom_adder_per_mwh`**, and the host's pre-conversion **`old_hr` / `old_emission_rate`**. The last
two are what remove the offline CAMPD step: the `er`/`phys` band a host-population gate is stated
over is now read straight off the bundle.

**Cache-neutral, asserted rather than argued** (this lane's batch is itself a re-key event, so a
step-0 key move would be indistinguishable from Act B's): no `ScenarioConfig` field bears any of
these names, none is a `cache_key_drop_defaults()` member, and an unarmed run writes the inert
`1.0` scales so the row shape does not depend on which gates are armed.
Guard: `test_ccs_retrofit.py::TestRetrofitLedgerCarriesTheScalingRecord` (4 cases).

## 2. Step 1 — the re-pin holds and G-DRIFT is all-INERT

**1a — 14 / 14 bare keys UNMOVED** at HEAD against PRECOMMIT §3's POST-D65B column. No
re-declaration owed, no moving hunk to name.

**1b — G-DRIFT `002cfa8d → 2485e611`, `constants.py` FIRST: ZERO hunks there** — the check a matched
cache key cannot make, because `constants.py` is outside the key. 13 files / +733−54, classified
hunk by hunk with each gate **measured**; the full table is PRECOMMIT Addendum C §C.0. The load-
bearing one: **D78's `exit_exempt_unit_ids` is INERT because the arming intersection is empty** —
the sector gate is on at **MISO alone** and MISO's D57 clearing is **off**; PJM is the converse
(clearing on, gate off) — and D78's own byte-identity test for the clearing-off case passes under
both decision rules. **Every hunk INERT, zero LIVE**, so no control solve is earned and G-CTRL
form 4 is valid.

**1c — an independent confirmation stronger than the bare-key match.** For all seven legs, undoing
*exactly the two D65-B acts* on the leg's HEAD-resolved config reproduces its **committed pre-D65-B
bundle key to the digit** (Addendum C table). So the recipe reconstructed here **is** the
incumbents' recipe, and the only thing moving each solve key is the two acts.

## 3. What this session found that was on nobody's list

### 3.1 D65-B's screen ran WITHOUT `--golden-posture`

Measured by rebuilding the screen's own HEAD (`a5c30c6a`) out of `git archive` and enumerating the
recipe grid. Both of D65-B's declared keys reproduce on the **shipped**-posture row
(arm `d0fb7534671b4c91`, control `6cfa33538294713c`) and **neither** on the golden one
(`9b9e5a48e3ca5c8e` / `0c3e9cd5b5993bdf`, which is the batch's ERCOT leg).

So the screen screened a **neighbouring config**, not the one the board's `ercot-t1f` row carries.
Consequences, recorded in Addendum C §C.1 **before the batch ran**:

1. The screen's arm-vs-same-HEAD-control differencing is **valid, for the shipped posture**, and its
   mechanism evidence is untouched — a control of 0 rows in every year reproducing D64 §2.4's ERCOT
   census, an arm of 7 rows at `er/phys` 0.9458–1.0000, the 2030 cap binding exactly.
2. **The ERCOT leg below is the FIRST golden-posture measurement of the coupled arm**, gated on its
   own rows and reported against D64 §2.4 — never netted against the screen's.
3. The ERCOT golden-posture key is **identical at `a5c30c6a` and at HEAD**, which re-confirms
   step 1b across the whole window rather than only from `002cfa8d`.

This overturns no adjudication and re-opens no gate. It is recorded because a screen that screened a
neighbouring config is a fact about the evidence.

### 3.2 Two cache-key pins were red on `main`, and they are this lane's family's debt

`test_capacity.py::test_pjm_iso_override_arms_forecast_only` and
`::test_cache_key_registration_and_backcast_coercion` fail on clean `main`. Both were written
2026-09-05 and broken the next day by **D65-B's Act B**, which is not a `_CACHE_KEY_OPTIONAL_FIELDS`
member and therefore re-keys every config unconditionally. **Measured, not assumed:** undoing the
two acts restores all four previous literals exactly, so the refresh is a re-key refresh with a
named cause and the Q44 posture each test asserts is unchanged.

## 4. The gate grader, and its validation

Addendum C's G0'/G1'/G2'/G5' are graded from **committed-shape artifacts only** (the per-year
evolution ledgers), which is the point of step 0. Validated before use against two committed D50
bundles, where it reproduces **D64 §2.3's own numbers exactly**: PJM 2029 = **2 rows / 909.8 MW**;
NEISO 2028/29/30 = **15 / 2,982.2**, **12 / 2,996.7**, **12 / 2,982.6 MW**. On those pre-step-0
bundles it correctly reports **G2' NOT EVALUABLE** — the defect step 0 removes.

## 5. The batch

### 5.1 `ercot-t1f` — ALL GATES CLEARED

Solve key **`9b9e5a48e3ca5c8e`** = Addendum C's pre-declaration exactly (the STOP *"a realized key
≠ its pre-declared value"* does not fire). HEAD guard clean. **5/5 years, 14.7 min, 3.92 GB.**

| year | rows | MW | MW-wtd `er` | MW-wtd `hr` | MW-wtd `k` |
|---|---:|---:|---:|---:|---:|
| 2026 / 2027 / 2028 | 0 | 0.0 | — | — | — |
| 2029 | 6 | 2,763.8 | 0.4106 | 7.227 | 1.1433 |
| 2030 | 1 | 3,000.0 | 0.3600 | 6.300 | 1.0025 |

| gate | verdict |
|---|---|
| **G0'** inert below 2028 | **PASS** — no row before 2028 |
| **G1'** ERCOT's D64 §2.4 band **0.95–1.05** | **PASS** — all 7 rows, measured **0.9672–1.0456** |
| **G2'** the identity, on step 0's persisted fields | **PASS** — `fixed_cost_scale == capex_scale` on all 7 rows; `capex/k` host-invariant **to the digit** within each year (2029 `1,271,849.014`; 2030 `1,177,983.346` $/MW) |
| **G3'** Act-A `k = 1` invariance | **PASS** — discharged at zero LP by `test_reference_host_is_invariant_on_and_off` |
| **G4'** no non-target load-bearing PASS → FAIL | **PASS** — vs the committed `ercot-t1f`: I3 and I12 were **already FAIL** pre-D65-B; **zero PASS → FAIL flips** |
| **G5'** vs D64 §2.4's ERCOT ceilings 0 / 5.68 / 3.80 GW | **PASS** — 0 / 2.764 / 3.000 GW; 2030 pins the 3 GW/yr cap exactly |
| **G6'** wall/RSS | **PASS** — 14.7 min, 3.92 GB |

**Three things worth stating at full magnitude.**

1. **G2' is answered for the first time.** D65-B could not evaluate it at all. The identity does not
   merely hold approximately — `capex/k` is identical **to three decimals across hosts spanning
   `k` = 1.0025 → 1.3096**, which is the seam's construction shown rather than asserted.
2. **The cross-year `capex/k` fall is the LEARNING CURVE, not a broken identity.** 2029's 2.76 GW of
   conversions enter the experience base and `_adjust_retrofit_capex(base_capex_kw, cumulative_gw)`
   lowers 2030's bar by **7.4 %** (`1,271,849 → 1,177,983`, ratio 0.9262). *This session's first
   grader pooled years and read that as a G2' STOP.* Addendum C says **host**-invariant, and a year
   is not a host, so the fix is a grader defect repair — the gate text is unchanged and was not
   reinterpreted on seeing a number.
3. **The golden-posture leg reproduces D65-B's shipped-posture screen EXACTLY** — 6 rows /
   2,763.8 MW in 2029 and 1 row / 3,000.0 MW in 2030, the same counts and the same MW. Given §3.1
   (the screen ran on a *different* recipe), that agreement is evidence the two acts' effect on this
   ISO is posture-insensitive, and it retires the concern §3.1 raised rather than leaving it open.
   The `er/phys` span differs slightly (0.9672–1.0456 here vs 0.9458–1.0000 there) because the host
   set is reached through a different fleet build; both are inside D64's ERCOT row.

I13 moves PASS → WARN. It is **not** attributed to either act: D65-B measured the same move on
**both** its legs at one HEAD and attributed it to the SCN-LOAD `DEMAND_GROWTH_RATES` hunk.

### 5.2 `neiso-t1f` — **G5' FIRES**, and the gate contradicts its own source. ROUTED, not resolved.

Solve key **`c3519b861f920bbe`** = Addendum C's pre-declaration exactly. **5/5 years, 10.6 min,
3.30 GB, 0 FAIL / 0 WARN on all 14 invariants** (the cleanest leg on the board).

| year | rows | MW | % of the 3 GW/yr cap | MW-wtd `er` | MW-wtd `hr` | MW-wtd `k` |
|---|---:|---:|---:|---:|---:|---:|
| 2028 | 12 | 2,965.4 | 98.8 % | 0.3574 | 7.103 | 0.9952 |
| 2029 | 9 | 2,939.8 | 98.0 % | 0.4793 | 7.259 | 1.3347 |
| **2030** | 7 | **1,786.1** | **59.5 %** | 0.4680 | 7.617 | 1.3032 |

| gate | verdict |
|---|---|
| **G0'** | **PASS** |
| **G1'** | **NOT GATED** — D64 §2.4 publishes no band for NEISO. Reported: `er/phys` 0.8074–1.4964 over 28 rows |
| **G2'** | **PASS** — all 28 rows; `capex/k` host-invariant within every year (2028 `1,323,595.6`; 2029 `1,201,226.4`; 2030 `1,133,012.2`) |
| **G3'** | **PASS** (zero LP) |
| **G4'** | **PASS** — 0 FAIL / 0 WARN, so no row can have flipped |
| **G5'** | **FIRES** — 2030 converts 1.786 GW; Addendum C wrote "STOP if the cap does NOT bind in a year" |
| **G6'** | **PASS** — 10.6 min, 3.30 GB |

**THE STOP IS REPORTED AS FIRED. This session does not reinterpret it to pass** — a STOP a session
may edit on seeing the number is not a STOP (D65-B §6.6; rules 1 `[R-STRUCT]` / 29).

**But the gate as I transcribed it contradicts the document it cites, verbatim.** D64 §2.3, the
same section Addendum C reads NEISO's "cap-bound" expectation out of, says in terms:

> *"Expectation for the A/B (§4): the cap stays bound in NEISO and NYISO and the composition
> re-ranks toward efficient hosts; **a year converting materially below the cap would be the
> informative surprise, not a STOP.**"*

So D64 pre-registered **this exact outcome** and pre-registered it as **not a STOP**. Addendum C
turned an expectation into a gate — which is the **same defect class the director adjudicated
against his own charter at r#48 §3(a)**, and it is mine: I quoted §2.4's "cap-bound" cell without
reading §2.3's sentence governing what a below-cap year means.

**Routed to the director, not resolved here.** This session may not repair a STOP it wrote by
declaring it void after seeing the number, even when the source says the gate should never have
existed. What is needed is an adjudication on the gate, not more solving.

**And the mechanism reading is favourable and is reported at full magnitude.** The unbinding is the
seam doing exactly what it was built to do, visible in the `k` column: 2028 clears at MW-wtd
`k` = 0.9952 (sub-reference hosts, cap bound), and by 2030 the remaining pool is `k` = 1.3032 —
hosts charged **1.30× per captured tonne** — and only 1.79 GW of them still clear. The efficient
hosts are consumed first (D64 §2.3's "composition re-ranks toward efficient hosts") and the
expensive tail cannot carry the accurate per-tonne cost. That is the D50/D64 seam's whole thesis.

**D64 §2.3's own conditional is now triggered.** *"The GOLDEN-3 horizon … is not expected to move
in kind; **it is only re-solved if the NEISO t1f arm shows the cap unbinding.**"* It does. So the
`neiso-t3` GOLDEN-3 leg is now **positively indicated by the source document** rather than merely
scheduled — and it is the leg that says whether the unbinding persists once RGGI reaches $67/t by
2040 with §45Q eligibility ending 2032.

**Per Addendum C's "STOP-only, per leg", the NEISO leg is stopped; the remaining legs proceed.**
NEISO is **not registered** pending adjudication.

### 5.3 `nyiso-t1f` — **G5' FIRES TWICE**, and NEISO's signature REPEATS

Solve key **`f62431376dd9df03`** = the pre-declaration exactly. Solve-path guard clean. **5/5 years,
14.2 min, 3.15 GB, 0 FAIL / 0 WARN on all 14 invariants.**

| year | rows | MW | % of cap | MW-wtd `er` | MW-wtd `hr` | MW-wtd `k` |
|---|---:|---:|---:|---:|---:|---:|
| 2028 | 13 | 2,984.4 | 99.5 % | 0.3786 | 7.057 | 1.0544 |
| **2029** | 19 | **2,271.5** | **75.7 %** | 0.4394 | 8.094 | 1.2235 |
| **2030** | 1 | **1,000.0** | **33.3 %** | 0.3600 | 6.300 | 1.0025 |

| gate | verdict |
|---|---|
| **G0' / G2' / G3' / G6'** | **PASS** — G2' on all 33 rows, `capex/k` host-invariant within every year (2028 `1,323,595.6`; 2029 `1,200,860.1`; 2030 `1,141,276.9`) |
| **G1'** | **NOT GATED** — no published NYISO band. Reported: `er/phys` 0.8419–1.4801 over 33 rows |
| **G4'** | **PASS** — 0 FAIL / 0 WARN, so nothing can have flipped |
| **G5'** | **FIRES on 2029 AND 2030** |

**Reported as fired, not reinterpreted.** Same routing as §5.2, and the same conflict with D64
§2.3, which names **NEISO and NYISO together** in the sentence that calls a below-cap year *"the
informative surprise, not a STOP."*

**THE SIGNATURE REPEATS ACROSS BOTH RGGI ISOs, AND THAT IS THE FINDING.** Two independent markets,
same construction, same shape:

| | 2028 | 2029 | 2030 |
|---|---|---|---|
| NEISO | 98.8 % of cap, `k` 0.9952 | 98.0 %, `k` 1.3347 | **59.5 %**, `k` 1.3032 |
| NYISO | 99.5 % of cap, `k` 1.0544 | **75.7 %**, `k` 1.2235 | **33.3 %**, `k` 1.0025 |

Both start cap-bound at a MW-weighted `k` ≈ 1.0 — the sub-reference and reference hosts — and both
unbind as the surviving pool moves to `k` > 1.2, i.e. hosts charged **>20 % more per captured
tonne** under the correctly-sized island. **The efficient hosts are consumed first and the
expensive tail cannot carry the accurate per-tonne cost.** A single ISO doing this is an anecdote;
both doing it, at different carbon prices and different fleets, is the seam's thesis reproduced.

It also sharpens what the gate got wrong. D64 §2.4's "cap-bound" cell was computed **at the hour
ceiling on the SHIPPED shape**; §2.3's expectation sentence is about the A/B. Addendum C promoted a
ceiling-census cell into a floor on a *solved* quantity — the same "a band is a window, not a floor"
error Addendum C itself warns about for ERCOT's G1', committed one paragraph later in its own table.

**NYISO is not registered pending the same adjudication.** Legs proceed.

### 5.4 `caiso-t1f` — ALL GATES CLEARED, and it is the CONTROL CASE that confirms the mechanism

Solve key **`17770cdad3230938`** = the pre-declaration exactly. Solve-path guard clean. **5/5 years,
35.5 min, 4.53 GB.**

| year | rows | MW | % of cap | MW-wtd `er` | MW-wtd `hr` | MW-wtd `k` |
|---|---:|---:|---:|---:|---:|---:|
| 2028 | 10 | 2,996.6 | 99.9 % | 0.3707 | 6.822 | 1.0324 |
| 2029 | 8 | 2,996.9 | 99.9 % | 0.3868 | 7.287 | 1.0772 |
| 2030 | 4 | 2,892.2 | 96.4 % | 0.3742 | 6.650 | 1.0422 |

| gate | verdict |
|---|---|
| **G0' / G2' / G3' / G6'** | **PASS** — G2' on all 22 rows; `capex/k` host-invariant within every year |
| **G1'** | **NOT GATED** — no published CAISO band. Reported: `er/phys` 0.8633–1.4151 over 22 rows |
| **G4'** | **PASS** — invariants **identical** to the committed `caiso-t1f`: `changed: none`. I7 and I12 were already FAIL pre-D65-B; **zero flips** |
| **G5'** | **PASS** — cap-bound in all three years, as D64 §2.4 predicts |

**This leg is the one that turns §5.2/§5.3 from a correlation into a mechanism.** CAISO is the third
carbon-priced ISO and the only one whose cap does **not** unbind — and the reason is visible in a
single column, the one step 0 made readable:

| ISO | MW-wtd `k` 2028 → 2030 | cap in 2030 |
|---|---|---|
| NEISO | 0.9952 → **1.3032** | **59.5 %** (unbinds) |
| NYISO | 1.0544 → **1.2235** (2029) | **33.3 %** (unbinds) |
| **CAISO** | 1.0324 → **1.0422** | **96.4 %** (stays bound) |

**CAISO's surviving host pool never leaves `k` ≈ 1.03–1.08.** It is not that CAISO is exempt from
the seam — the seam is armed identically — it is that CAISO's eligible fleet still has ~3 GW/yr of
**near-reference** hosts to convert in every year, so the screen never has to reach the `k` > 1.2
tail. NEISO and NYISO exhaust theirs and are pushed into that tail.

So the unbinding is not a level effect and not an ISO quirk: **it is a fleet-composition effect,
predicted by `k` and by nothing else.** That is the D50/D64 seam behaving as constructed, and it is
the strongest structural evidence this lane produces. Stated here because it also means the two
fired G5' STOPs are measuring *host exhaustion*, which is a real market fact, not a defect in the
arm.

### 5.5 `pjm-t1f` — ALL GATES CLEARED, and G1' EMPIRICALLY VINDICATES THE ADJUDICATION

Solve key **`542eeedadab83ee1`** = **Addendum E's re-declaration** exactly (the D67-ARM move was
correctly anticipated). Solve-path guard clean. **5/5 years, 55.6 min, 8.69 GB.**

| year | rows | MW | D64 §2.4 ceiling | MW-wtd `er` | MW-wtd `hr` | MW-wtd `k` |
|---|---:|---:|---:|---:|---:|---:|
| 2028 | 1 | **408.2** | **0.41 GW** | 0.6071 | 7.155 | 1.6907 |
| 2029 | 5 | 1,840.5 | 2.48 GW | 0.5603 | 7.121 | 1.5602 |
| 2030 | 0 | 0.0 | 2.48 GW | — | — | — |

| gate | verdict |
|---|---|
| **G0' / G2' / G3' / G6'** | **PASS** — G2' on all 6 rows; 55.6 min is inside 2× the ~36 min estimate, 8.69 GB < 14 GB |
| **G1'** | **PASS** — all 6 rows inside **PJM's** D64 band **1.27–1.49**, measured **1.2668–1.4886** |
| **G4'** | **PASS** — invariants **identical** to the committed `pjm-t1f`: `changed: none`; I7/I12 already FAIL; **zero flips** |
| **G5'** | **PASS** — 0.408 / 1.840 / 0.000 GW, every year under its ceiling |

**G1' IS THE EMPIRICAL VINDICATION OF THE DIRECTOR'S ADJUDICATION.** D65-B's charter applied
`er/phys ≥ 1.27` to an **ERCOT** screen and it fired; the director ruled at r#48 §3(a) that 1.27 is
**PJM/MISO's** host band, transcribed onto the wrong ISO. That ruling was made on documentary
grounds. It is now **measured**: PJM's clearing rows land at **1.2668–1.4886**, inside the band to
the digit, while ERCOT's land at 0.9672–1.0456 inside *its* row's 0.95–1.05. Two ISOs, two bands,
each ISO in its own — which is what "a gate names its ISO" means, demonstrated rather than argued.

**And G5' 2028 is the batch's sharpest number.** The solved value is **408.2 MW against D64 §2.4's
0.41 GW hour-ceiling census — 99.6 % of a prediction computed with ZERO LP**, months earlier, from
the ceiling arithmetic alone. A zero-solve census and a full 8760 dispatch agreeing to four parts in
a thousand is a strong statement that the seam's cost side is right.

**The two live hunks are disclosed, not netted (Addendum D.3 / E.3).** This leg carries D81 and
D67-ARM as well as the two acts, so its FC-map delta has three causes. **The gate table is
unaffected**, exactly as Addendum E predicted: G0'–G5' read only `ccs_retrofits`, and G4' comes back
`changed: none` — so neither live hunk moved a single invariant here, and the retrofit set is a
clean two-act reading. The disclosure stands for the *board row*, not for the gates.

### 5.6 `miso-t1f` — the retrofit gates CLEAR; **G4' FIRES**, and the flip is provably not the acts'

Solve key **`74359fedbf2eadd6`** = the pre-declaration exactly. Solve-path guard clean. **5/5 years,
53.9 min, 9.63 GB.**

| year | rows | MW | D64 §2.4 ceiling | MW-wtd `er` | MW-wtd `hr` | MW-wtd `k` |
|---|---:|---:|---:|---:|---:|---:|
| 2028 | 1 | 334.5 | 0.48 GW | 0.5761 | 7.256 | 1.6044 |
| 2029 | 2 | 283.7 | 0.72 GW | 0.5771 | 7.646 | 1.6071 |
| 2030 | 0 | 0.0 | 0.72 GW | — | — | — |

| gate | verdict |
|---|---|
| **G0' / G2' / G3' / G6'** | **PASS** |
| **G1'** | **PASS** — all 3 rows inside **MISO's** D64 band **1.26–1.39**, measured **1.2898–1.3930** |
| **G5'** | **PASS** — 0.334 / 0.284 / 0.000 GW, every year under its ceiling |
| **G4'** | **FIRES** — **I3 unserved/dump PASS → FAIL** (I14 also PASS → WARN) |

**Reported as fired. This session does not declare it passed.**

**But the flip is provably not the two acts', on the arm's own arithmetic.** I3 fails **starting in
2026** — `2026: slack 0.02 % of load (19 h, 111.6 GWh)`, `2027: 0.03 %` — and **the mechanism is
inert before 2028**: `apply_ccs_retrofit` returns at `if year < config.ccs_retrofit_available_year`
(2028) before reading either field, and G0' independently measured **0 retrofit rows in 2026 and
2027**. A mechanism that does not execute cannot have caused a failure in the years it does not
execute in.

**The cause is the demand vintage, pre-registered as a confound before this batch ran.** MISO's
prior (`ff-t1f-d60/miso`) was solved at **`2ef4326e`**, which D65-B §5's G-DRIFT table names
explicitly as **PRE-hunk on SCN-LOAD `d14a7ed0`** (`DEMAND_GROWTH_RATES`, all six ISOs). Higher
demand growth ⇒ more unserved energy ⇒ I3 fails and the load-weighted price rises out of I14's band.
D65-B §5 consequence 2 stated exactly this in advance: *"the batch's board-level before/after is
confounded by the demand vintage for the four pre-hunk ISOs … reported at full magnitude and
attributed, never netted"* — and named `2ef4326e (miso)` as one of the four.

So G4' as written fires on a **cross-vintage** comparison, because the only prior available for MISO
is on the old demand table. **Routed with §5.2/§5.3, not resolved here.** The three fired gates share
one root: Addendum C's gates compare a HEAD solve against a prior that predates HEAD, and two of the
three firings are measuring that gap rather than the arm.

**The retrofit seam itself is clean on this leg** — G1' inside MISO's own band, G5' under every
ceiling, G2' exact — which is the part of the leg the two acts actually reach.

### 5.7 `neiso-t3` GOLDEN-3 — the leg D64 §2.3 POSITIVELY INDICATED, and the horizon that answers whether the unbinding persists

Solve key **`0fc42cb56c24d544`** = Addendum C §C.1c's pre-declaration exactly, re-verified at four
successive HEADs (Addenda C, G, **H**, and — against a `main` that moved 49 commits *during* the
solve — **I**). HEAD guard clean at `f37121bd`.

**Why this leg exists, and why it is not merely the seventh item on a list.** D64 §2.3 wrote a
conditional: *"The GOLDEN-3 horizon … is not expected to move in kind; **it is only re-solved if the
NEISO t1f arm shows the cap unbinding.**"* Leg 2 showed exactly that (2030 converts 1.786 GW, 59.5 %
of the cap), so the source document **triggered its own condition** — this leg was positively
indicated rather than scheduled, and §5.2 said so before it ran. **That is an expectation to test,
never a target to hit**, and the measurement below is reported whichever way it falls.

**What this leg carries that the t1f legs' 2026–2030 window cannot reach.** The GOLDEN-3 horizon
runs to **2050**, so it passes two dates the five-year legs never see: **§45Q eligibility ends 2032**
(`ira_45q_credit_window_years` off `ccs_retrofit_available_year`) and the **RGGI ladder reaches
$67/t by 2040**. If the §5.2/§5.3 unbinding is host exhaustion — the efficient hosts consumed first,
the `k` > 1.2 tail unable to carry the accurate per-tonne cost — then a rising carbon price should
eventually re-open the tail, and the loss of §45Q should shut it. This leg is where those two
opposing forces are visible.

**25 / 25 years, 30.1 min, 3.56 GB.** Registered as `neiso-2026-2050-t3-golden3-d65br`.

| year | rows | MW | % of cap | MW-wtd `er` | MW-wtd `hr` | MW-wtd `k` | `capex/k` | `er/phys` span |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2026 / 2027 | 0 | 0.0 | — | — | — | — | — | — |
| 2028 | 12 | 2,965.4 | 98.8 % | 0.3574 | 7.103 | 0.9952 | 1,323,595.554 | 0.8074–0.9243 |
| 2029 | 9 | 2,939.8 | 98.0 % | 0.4793 | 7.259 | 1.3347 | 1,201,226.450 | 0.8457–1.4964 |
| **2030** | 7 | **1,786.1** | **59.5 %** | 0.4680 | 7.617 | 1.3032 | 1,133,012.155 | 0.8230–1.3534 |
| **2031** | 1 | **1,000.0** | **33.3 %** | 0.3600 | 6.300 | 1.0025 | 1,097,059.911 | 1.0025 |
| **2032 – 2050** | **0** | **0.0** | — | — | — | — | — | — |

| gate | verdict |
|---|---|
| **G0'** inert below 2028 | **PASS** — no row in 2026 or 2027 |
| **G1'** host band | **NOT GATED** — D64 §2.4 publishes no NEISO band. Reported: `er/phys` **0.8074–1.4964** over 29 rows |
| **G2'** the identity, on step 0's persisted fields | **PASS** — `fixed_cost_scale == capex_scale` on all 29 rows; `capex/k` host-invariant **to three decimals** within every year |
| **G3'** Act-A `k = 1` invariance | **PASS** — discharged at zero LP by `test_reference_host_is_invariant_on_and_off` |
| **G4'** no non-target load-bearing PASS → FAIL | **PASS** — the invariant set `{I3 FAIL, I13 WARN}` is **identical to the prior's**, and identical in *detail*, not merely in ident; **zero flips** |
| **G5'** the **in-kind** form (the only form Addendum C states for this leg) | **PASS** — the converted set gains **no** `from_fuel` class and **no** unit class the incumbent lacked; all 29 rows `gas_cc → gas_cc_ccs` |
| **G6'** wall / RSS | **PASS** — 30.1 min against the ~33 min estimate (2× bound 66 min); 3.56 GB against 14 GB |

**ALL GATES CLEARED. No gate fired on this leg**, so §0.2's basis disclosure has nothing to add
here — which is itself informative: the leg whose comparator is a *same-vintage* prior is the leg
with nothing to disclose.

### 5.7a The answer to D64 §2.3's conditional: the unbinding PERSISTS, DEEPENS, and then conversion STOPS

**2030 unbinds to 59.5 % of the cap, 2031 to 33.3 %, and there is not one retrofit row in
2032–2050.** Nineteen further years, across which the RGGI ladder climbs to **$67/t by 2040**, and
the screen never re-opens.

Two readings follow, and both are stronger than the t1f window could support:

1. **The rising carbon price does not reclaim the `k` > 1.2 tail.** If the §5.2/§5.3 unbinding were
   a *level* effect — hosts merely priced out at 2030's carbon — then a carbon price roughly
   doubling by 2040 would bring them back. It does not. The eligible host pool is **exhausted**, not
   priced out, which is exactly what §5.4's CAISO control predicted from composition alone.
2. **§45Q is not the binding constraint.** Eligibility ends 2032, and conversion stops in **2031** —
   the year *before* the window closes. So the horizon's shutdown cannot be attributed to the credit
   expiring; the host side runs out first. (The incumbent also ends in 2031, so this is reproduced
   across both arms rather than being a property of the acts.)

**And D64 §2.3's own prediction for this leg is CONFIRMED as measured.** It said GOLDEN-3 is
*"per-tonne-dominant on both sides and NOT expected to move in kind"*, and Addendum C wrote the STOP
accordingly. Measured: **29 rows, every one `gas_cc → gas_cc_ccs`**, unit classes `CC_REGULAR` (28)
and `gas_cc_h_class_Central` (1) — the identical class set the incumbent converted, with nothing
gained in either direction. **The prediction was an expectation to test, and it survives its test.**

### 5.7b The check nobody asked for: this leg reproduces leg 2 BYTE-FOR-BYTE on every overlapping year

| year | leg 2 `neiso-t1f` (2026–2030) | leg 7 `neiso-t3` (2026–2050) |
|---|---|---|
| 2028 | 12 rows / 2,965.4 MW · `k` 0.9952 · `capex/k` 1,323,595.554 | **identical** |
| 2029 | 9 / 2,939.8 · `k` 1.3347 · 1,201,226.450 | **identical** |
| 2030 | 7 / 1,786.1 · `k` 1.3032 · 1,133,012.155 | **identical** |

Two independent solves, same ISO and same recipe, different horizons (5 years vs 25) and different
cache keys — landing on the same retrofit ledger to every digit, including the MW-weighted `er`,
`hr` and `k` columns and the `er/phys` spans. **The screen is horizon-independent inside its own
window, shown rather than assumed**, and it means §5.2's unbinding is not an artefact of where the
t1f window happened to stop.

### 5.7c THE THREE-CAUSE DISCLOSURE — stated at the gate, not netted (the leg-5 pattern)

Against its incumbent `bau-d60` (`f04fd06348e1623d`, solved **2026-09-06T03:46:25Z**) this leg
carries **three** causes, not two: Act A, Act B, and **capx D77's CCS emission-rate seam repair**,
whose commit `ae8dd2a0` is dated **05:17:42Z the same day — 91 minutes after the incumbent was
solved.** D77 §8.1 lists this very bundle among the 45 it mis-states, and PRECOMMIT §7 made D77 a
precondition of the whole batch (*"Screen cleared AND D77 merged (both required)"*), so **all seven
legs carry it**; it is a batch-level property, not this leg's peculiarity.

**What that voids and what it does not.** The retrofit-*ledger* difference — arm **29 rows /
8,691.3 MW** vs incumbent **39 / 10,423.6 MW** over 2028–2031 — is **not** a two-act reading, because
D77's own NEISO A/B measured that the repair alone moves the retrofit set. It is reported and left
attributed. What *is* clean is **every gate above**: G0'/G2'/G3'/G5'/G6' are absolute properties of
the arm's own rows and need no comparator at all, and G4' compares invariant **status**, which is
identical. **The demand vintage is NOT a confound here** — unlike MISO's leg 6, both this leg and its
incumbent are POST-hunk on SCN-LOAD `d14a7ed0` (`FINDING-capx-d60-2026-09-05.md` §5.5's own
correction records `bau-d60` as the post-hunk side).

### 5.7d What this leg supplies to the routed FC-5 re-authoring

D77 §8.2 measured that of 14 FF-2D verdicts keyed to a CCS-carrying run, **three** carry a *scored*
FC-5/FC-6 row — all three NEISO T3 — and that the repair makes their `co2@2030/2035/2040` corridor
rows mis-stated in a way needing **re-authoring, not re-scoring**. This lane does not re-author them
(§6.3, §7). What it supplies is the post-repair, post-D65-B bundle they must be re-authored
*against*:

| corridor row | D25 table | `bau-d46` | `bau-d60` (incumbent) | **this leg** |
|---|---:|---:|---:|---:|
| `co2@2030` | — | — | 13.368 Mt | **6.1058 Mt** |
| `co2@2035` | — | — | 8.9119 | **3.0808** |
| `co2@2040` | **4.4883** | 9.5792 (+113.4 %) | 8.5587 (+90.7 %) | **2.7746 (−38.2 %)** |

**The sign of the corridor gap FLIPS.** `bau-d46` and `bau-d60` both sat *above* the carried table on
`co2@2040`; this arm sits **38.2 % below** it. Still past the corridor memo's 15 % explanation
threshold — so still an `EXPLAINED DIVERGENCE` that must be re-authored — but now on the **other side
of the table**, which is precisely why D77 refused to let a re-score stand in for a re-authoring, and
why `FINDING-capx-d60-2026-09-05.md` §5.5 routed it rather than absorbing it.

---

## 6. Governance

### 6.1 Rule 27 `[R-PUSH]` — blob verification

Every push in this batch that touched a file ≥ 300 lines was followed immediately by a blob
fetch-back and a line-count + content-hash comparison against the local bytes, before the next
commit. The files that qualify, and the transport each went over:

| file | lines (local) | transport | verified |
|---|---:|---|---|
| `docs/handoffs/FINDING-capx-d65br-2026-09-06.md` | 860 | `git push` (small pack) | line count + sha256 equal |
| `docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md` | 964 | `git push` (small pack) | line count + sha256 equal |
| `docs/codebase-site/data/mechanism-matrix.js` | 2,663 | `git push` (small pack) | line count + sha256 equal |
| `docs/codebase-site/data/mechanism-matrix/CAISO.js` | 654 | `git push` (small pack) | line count + sha256 equal |
| `docs/codebase-site/data/mechanism-matrix/ERCOT.js` | 499 | `git push` (small pack) | line count + sha256 equal |
| `docs/codebase-site/data/mechanism-matrix/MISO.js` | 515 | `git push` (small pack) | line count + sha256 equal |
| `docs/codebase-site/data/mechanism-matrix/NEISO.js` | 438 | `git push` (small pack) | line count + sha256 equal |
| `docs/codebase-site/data/mechanism-matrix/NYISO.js` | 931 | `git push` (small pack) | line count + sha256 equal |
| `docs/codebase-site/data/mechanism-matrix/PJM.js` | 365 | `git push` (small pack) | line count + sha256 equal |
| `frontend/data/hindcast/invariant-failures.json` | 310 | `git push` (small pack) | line count + sha256 equal |
| `frontend/data/hindcast/neiso-2026-2050-t3-golden3-d65br.json` | 635 (new file) | `git push` (small pack) | line count + sha256 equal |
| `scripts/register_forecast_run.py` | 1,320 | **not modified by this lane** | n/a |

**`docs/codebase-site/data/mechanism-matrix/SPP.js` is NOT in this table and was NOT touched.** The
SPP shard landed inside this session's own rebase window (Addendum H) and already carries the
`ccs_retrofit_fixed_cost_co2_scaling` cell at `fc: "U"`. Rule 25 `[R-ISO-SCOPE]` and rule 28(d) both
say the same thing: **a verdict transfers to nobody.** SPP holds no leg in this batch and therefore
no measured verdict, so its cell correctly stays `U` — re-stamping it to `K` off six other ISOs'
evidence is exactly the transfer those rules forbid. The six shards this lane edited are the six
ISOs it solved.

No file ≥ 300 lines was rewritten from regenerated response content at any point in the batch; every
push carried the exact on-disk bytes (rule 27's push-integrity half). The model-assignment half is
satisfied by construction: this lane is **Opus** throughout, and its scope reaches
`src/market_sim/` (step 0's ledger fields) and `docs/`.

### 6.2 Rule 21 `[R-DOF]` — the D8 curated DOF rows for the flipped default

`scripts/build_forecast_dof_ledger.py` enumerates **non-default** solve-affecting fields and emits
the literal token `unattested` for any that has no curated identification row — a token
`forecast_verdict._dof_ledger_row` scores exactly as a MISSING ledger (CAVEAT at t1, FAIL at t3).
So the question a (b′-1) declared default flip has to answer is whether it *degrades FC-7 by
arithmetic*, and the answer is measured on leg 7's own `run_config.json`, not asserted.

**MEASURED on leg 7's own bundle** (`build_forecast_dof_ledger.py results/ff-t3-neiso-golden/bau-d65br
--stdout`, committed artifacts only, zero LP): **7 entries — 1 `design-decision`, 6 `published`,
0 UNIDENTIFIED, 0 `unattested`, and NO CCS entry of any kind.** FC-7's DOF-ledger row is therefore
not degraded by the flip, and it is not degraded by luck either:

**Neither act appears in the ledger, and that is the flip's own mechanic rather than an omission.**
Act A (`ccs_retrofit_fixed_cost_co2_scaling` `False → True`) and Act B
(`ccs_retrofit_vom_adder` `8.0 → 2.95`) both moved the **dataclass default**, and the builder
enumerates departures *from* the default — so a config sitting at the armed default carries no
entry for either field. The measurement above reproduces, entry for entry, the same reading capx D60 recorded for Q42's flip of
`ccs_retrofit_capex_co2_scaling` (`FINDING-capx-d60-2026-09-05.md` §5.5, P20: *"7 entries, 7
IDENTIFIED, 0 UNIDENTIFIED, 0 unattested, and **no CCS entry** — Q42 made the field the dataclass
default and the ledger enumerates non-default fields"*), and it is why the D8 curated row that
already exists for `ccs_retrofit_capex_co2_scaling` (`build_forecast_dof_ledger.py`, key
`("*", "ccs_retrofit_capex_co2_scaling")`, `identification: design-decision`) is dormant rather
than wrong.

**The identification is nonetheless committed, which is what rule 21 actually asks for.** Act A's
is `PRECOMMIT-capx-d65b-2026-09-06.md` §1 + `FINDING-capx-d64-2026-09-05.md` §§1.2–1.3 (ATB 2024
v4.0.0 + NETL Rev 4a: both fixed-cost legs are TPC fractions, so under seam 1 both scale with
`k = captured / captured_ref`) — **zero free parameters**, no new constant and no new reference
host. Act B's is the derivation pinned in
`tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py::TestRetrofitVomBasis`
(`(4.8 − 2.1) × 1.090947 = 2.9456 → 2.95`), read off the same pinned ATB bytes as the other two
cost legs. **Neither is a tuned value**, so neither opens a rule-21 root-cause issue, and the
authorized-price-tuning channel of rules 1/13 is not engaged at all — this is a forecast-mode
capacity screen, not an offer curve.

### 6.3 D77 §8 blast-radius reconciliation

`FINDING-capx-d77-2026-09-06.md` §8 measured the radius of the CCS emission-rate seam repair and
handed it to this batch: **45 committed forecast bundles carry a non-empty CCS retrofit ledger**
(CAISO 2 · ERCOT 3 · MISO 2 · NEISO 30 · NYISO 4 · PJM 4), **every one at an unmoved cache key**,
so a post-fix run of the same config would CACHE-HIT the pre-fix bundle. D77 re-solved none of
them and named the remedy in terms: *"Purge-or-re-solve is D65-B's batch, at one HEAD, carrying
this fix."*

**What this batch discharges.** Seven legs solved at one post-D77 HEAD, each at a key that moved
(Act B re-keys unconditionally), so none of them can cache-hit a pre-fix bundle: the seven bare
recipes — the six t1f and GOLDEN-3 — now have a post-repair measurement on the board.

**What it does NOT discharge, stated rather than left to be discovered.** D77 §8.2 measured that
of 14 FF-2D verdicts keyed to a CCS-carrying run, only **three** carry a *scored* FC-5/FC-6 row on
such a run, and all three are NEISO T3: `neiso-t3`, `neiso-t3-pre-d60`, `neiso-t3-pre-d47`. Their
FC-5 corridor rows (`co2@2030`, `co2@2035`, `co2@2040`) and the FC-6 `paired P1` cumulative-CO2
operands are mis-stated — and D77 is explicit that *"the repair moves the model value, so the
explanation must be **re-authored, not merely re-scored**."* Re-authoring the FC-5 corridor table
is a dedicated lane's work (D25 authored it; D46/D47/D60 each carried it unre-authored, and
`FINDING-capx-d60-2026-09-05.md` §5.5 routed the re-authoring rather than absorbing it, measuring
the carried table already stale on **6 of 42** computable rows). **This lane does not re-author it
and writes no `ff-verdicts.json` byte** (§6.6). What leg 7 supplies is the missing precondition:
those three rows now have a post-repair, post-D65-B GOLDEN-3 bundle to be re-authored *against*.

The other 11 verdicts read FC-4 `n/a`, FC-5 `SKIPPED` and FC-6 `SKIPPED`, so no scored cell of
theirs moves; D77's own warning not to mistake `SKIPPED` for "unaffected" is carried here rather
than repeated as a claim.

### 6.4 D50 §6.2 radius

`FINDING-capx-d50-2026-09-04.md` §6.2 censused **153 committed forecast-mode `run_config.json`** at
its HEAD and split them by what a declared default flip on this family would do: 3 carry the field
explicitly, 150 re-key, of which 108 end ≤ 2027 and are **byte-identical** (the screen is gated
2028 — a cache-key formality, never a re-measure on the merits), 42 reach ≥ 2028, and **31 bundles
/ 25 distinct keys** carry a decided CCS retrofit and can move on behaviour.

Its partition of those 31 is what makes this batch's scope exactly right, and it is quoted rather
than restated: **7 BARE keys — `ercot-t1f`, `neiso-t1f`, `pjm-t1f`, `miso-t1f`, `nyiso-t1f`,
`caiso-t1f`, and `neiso-t3` (GOLDEN-3)**. That is this batch's seven legs, one for one, and no
other bundle in the census is touched:

* the **6 historical / suffixed keys** are frozen records of a superseded posture — they re-key but
  are never re-solved, because re-solving one destroys the thing it preserves;
* the **12 unregistered keys** (the CAISO `ffr3p`/`ffr4d`/`ffr4e`/`ffr4f`/`ffrsc` family, the
  GOLDEN-3 FC-6 arms, `arm3arm/miso-2031-2035-armed-default`) hold no live verdict row and are
  reported, not re-solved.

Act A's own flip mechanic is D44's **(b′-1)**, verified at HEAD by PRECOMMIT §3.1: the frozen drop
value stays `"False"`, so an explicit `False` still selects the pre-flip construction and keeps its
key, and `Act A alone` leaves the explicit-`False` path on the pre-flip key `e5ecd4105ada3e58`
exactly. The unconditional movement at HEAD is **Act B's**, by construction — it is not a
`_CACHE_KEY_OPTIONAL_FIELDS` member and has no drop value to hide behind.

**Backcast behaviour is byte-identical** and so is every hindcast/crossover horizon ending before
2028: `ccs.py::apply_ccs_retrofit` returns at `if year < config.ccs_retrofit_available_year` before
any read of either field, and that call site is the only consumer of both. The backcast KEY moves
(a one-time cache MISS); **no keeper, sidecar, marker, freeze, determination or dashboard row
does** — committed artifacts are files, not cache lookups. No backcast keeper was re-solved by this
lane, and rule 22 `[R-HOLDOUT]` is untouched: every leg is `mode="forecast"` spanning 2026+, so no
held-out year was solved, scored or registered.

### 6.5 The D72-prehunk `neiso-t1f` residue key is DISCHARGED

`FINDING-capx-d72-prehunk-2026-09-06.md` §6 item 2 left three of D60-R3's seven residue keys
undischarged — `neiso-t1f`, `miso-t1h`, `neiso-t1h` — because the reference moved out from under
the campaign: its leg 1 solved `18515067bf4d2fbe` clean at HEAD (5/5 years, 0 FAIL / 0 WARN,
realized key exactly as pre-declared) and its **pre-declared STOP 3 fired**, bisected to SCN-LOAD
`ad45b0e4`'s `DEMAND_GROWTH_RATES["NEISO"]["low"]["near"]` `0.007 → 0.004009`. Its own remedy
sentence is the discharge condition: those keys *"need a **re-based charter** with a
pre-declaration written against the SCN-LOAD side."* The director assigned the t1f one to this
batch at r#48 (`capx-director-ledger-2026-08.md`, D65-B-R charter row: *"Also discharges the
D72-prehunk `neiso-t1f` residue key"*) and re-stated the split at r#49 (*"t1f one inside D65-B-R's
batch; the two t1h behind D76 phase 0"*).

**It is discharged, and here is exactly what discharges it.** PRECOMMIT **Addendum C** is the
re-based pre-declaration, written 2026-09-06 — after the SCN-LOAD hunk — and committed and pushed
(`5c82c9d7`) before any leg solved. Leg 2 (`neiso-t1f`) then solved on it at a post-hunk HEAD:
realized key `c3519b861f920bbe` = the pre-declaration to the digit, 5/5 years, **0 FAIL / 0 WARN on
all 14 invariants** — the cleanest leg on the board — and registered as
`neiso-2026-2030-d65br-arm`. Addendum C §C.1c and Addendum G §G.4 close the loop from the other
side: undoing exactly the two acts on leg 2's HEAD-resolved config reproduces **`18515067bf4d2fbe`**
— D72-prehunk's own pin — to the digit, measured twice (at `2485e611` and again at `29a76482`), and
re-measured a fifth time at this session's HEAD in **Addendum H**. So the key D72-prehunk could not
finish is now solved, gated and registered on a basis fixed after the hunk that stranded it.

**What the discharge does NOT include, so nothing is over-claimed.** The bare `neiso-t1f` FF-2D
verdict key still points at `neiso-2026-2030-d50-ccscapex`, a PRE-hunk bundle; this batch took no
bare verdict key and wrote no `ff-verdicts.json` byte (§6.6). The residue key's requirement was a
re-based charter and solve, and that is what is discharged — not a re-pointing of the board's
verdict pointer. **The two `t1h` residue keys (`miso-t1h`, `neiso-t1h`) are untouched by this lane**
and remain queued behind D76 phase 0, exactly as r#49 placed them.

### 6.6 What this lane deliberately did not write

No `frontend/data/forecast/ff-verdicts.json` byte, no `program-status.json` byte, no re-score of
any FF-2D verdict, no keeper, no marker, no freeze, no calibration registry row, no backcast
sidecar, no ISO shard this lane's own evidence does not cover, and nothing armed beyond the two
acts already on `main`. The reasoning, with the code-path evidence, is §7.

---

## 7. THE `ff-verdicts.json` QUESTION, answered from the code path

**The question, and whose it is.** At r#52 the director proved the batch had "written no board byte"
by citing `frontend/data/forecast/ff-verdicts.json`, and recorded against interest at r#53 §2(a) that
this was **the wrong instrument**: the registration artifact is the per-run **hindcast sidecar** under
`frontend/data/hindcast/` (7 files in `c36a3fe7`, zero under `frontend/data/forecast/`), while
`ff-verdicts.json` is the FF-2D **verdict snapshot**, a different object that moves only when a
verdict moves. The conclusion held; the proof did not. He routed the genuinely open question here,
asserting it neither way: **do any of the seven legs require an `ff-verdicts.json` update?**

### 7.1 The answer

**NO — not one of the seven, leg 7 included.** And the reason is not that the file happens not to
have moved; it is that **a registration and a verdict are two different acts, and this batch
performed only the first.**

### 7.2 The code path, measured rather than read

**(a) The registrar never writes the file.** `scripts/register_forecast_run.py` reaches
`ff-verdicts.json` at exactly one place — `_load_verdicts()` (:648–653), which *reads* the committed
snapshot and falls back to `docs/handoffs/ff-t1-gate-verdicts.json`. Every other reference in the
module is a docstring. The file's **sole writer** in the tree is
`scripts/rescore_forecast_verdicts.py --apply` (:69, :299), whose scope is stated in its own header:
verdicts whose `VERDICT_MAP`-mapped run has a **tracked score artifact under `results/hindcast/`** —
`score.json` for t1h, `crossover_score.json` for t1x. A t1f 2026–2030 or a t3 2026–2050 forecast run
has neither, so no leg of this batch is even in that script's domain.

**(b) A run only touches the snapshot if it takes a verdict key, and none of these does.**
`_verdict_key(run_id, meta)` (:636–641) resolves `meta["verdict_key"]` first, else
`VERDICT_MAP.get(run_id)`, else `None`; `build_sidecar` then does `verdicts.get(vkey) if vkey else
None`, so a `None` key means the run renders **score-only, no verdict** and consumes no snapshot
entry at all. Measured through the registrar's own resolver over all **127** committed sidecars:

| run | `_verdict_key` | renders a verdict |
|---|---|---|
| `ercot-2026-2030-d65br-arm` | `None` | no |
| `neiso-2026-2030-d65br-arm` | `None` | no |
| `nyiso-2026-2030-d65br-arm` | `None` | no |
| `caiso-2026-2030-d65br-arm` | `None` | no |
| `pjm-2026-2030-d65br-arm` | `None` | no |
| `miso-2026-2030-d65br-arm` | `None` | no |
| `neiso-2026-2050-t3-golden3-d65br` (leg 7) | `None` | no |

None carries a `meta.verdict_key`; none is in `VERDICT_MAP`. **This is not an oversight of this
lane's — it is the posture the immediately preceding lane used for the same act**: capx D60's own
t1f arms (`caiso-/miso-/nyiso-/pjm-2026-2030-d60-arm`) each produced a `forecast_verdict.json` in
their bundle *and* were given a `VERDICT_MAP` entry, which is what made an `ff-verdicts.json` write
owed there. This batch's legs carry **no `forecast_verdict.json` and no `dof_ledger.json` in any
bundle** — measured: `results/ff-t1f-d65br/<iso>/` holds exactly `run_config.json`,
`full_horizon_summary.json` and the key dir, against `results/ff-t1f-d60/<iso>/` which holds both
extra files. **No FF-2D verdict was produced by this batch, so there was none to write.**

**(c) Rule 15 `[R-DASHBOARD]` names the same split.** The forecast namespace is generated and
gitignored, "fully derived from the COMMITTED inputs: the hindcast sidecars + the FF-2D verdict
snapshot `ff-verdicts.json` + the board seed `program-status.json`." A registration writes the
**first**; the second moves only when a verdict is re-scored. `scripts/check_forecast_staleness.py`
states the same thing from the staleness side, and its comment is the sharpest statement of the
distinction the director's r#52 proof missed: *"a hindcast sidecar is an INPUT to a future verdict,
never a substitute for one, so re-registering a hindcast run must not make the gate evidence look
re-scored."*

### 7.3 What WOULD have moved it

**Taking a bare verdict key** — and leg 7 is the only leg where that was ever a live option, because
it is the only one whose incumbent holds one. `neiso-2026-2050-t3-golden3-d60` carries
`meta.verdict_key = "neiso-t3"`, and the D60-R3 lane discharged the consequent duty exactly as the
convention requires: it wrote its own verdict as the new `neiso-t3` (provenance `run_id`
`neiso-2026-2050-t3-golden3-d60`, session `capx-D60-R3`, sha `7ed062ba9a68`) and preserved the
predecessor as **`neiso-t3-pre-d60`**. So the mechanism is not hypothetical; it is the pattern that
would have bound leg 7.

**Why leg 7 does not take it, on three independent grounds:**

1. **This batch produced no verdict to write.** §7.2(b). Registering leg 7 under `neiso-t3` without
   writing a new verdict would make it render the **D60 run's** HOLD — a run displaying a
   determination scored on a different run at a different configuration, which is precisely the
   mis-attachment every `VERDICT_MAP` comment block in the registrar exists to forbid (*"a run must
   never render a verdict its own score contradicts"*). It would also invert the FR-21 provenance
   stamp: `_run_provenance` (:717–746) ranks *"the rubric verdict's own stamp > the canonical
   hindcast sidecar's stamp"*, so leg 7's board entry would carry D60's `scored_at_sha` /
   `scored_at_date` instead of its own.
2. **Writing one is out of this lane's charter and would be dishonest arithmetic.** Addendum C's
   gates are **STOP-only and contribute to no determination** (rule 29 `[R-SCREEN]`). An FF-2D t3
   verdict needs FC-3 (T1-H) and FC-4 (T1-X) scores plus the FC-5 corridor and FC-6 driver battery —
   and `FINDING-capx-d77-2026-09-06.md` §8.2 measured that the D77 repair leg 7 carries makes exactly
   `neiso-t3`'s FC-5 `co2@2030/2035/2040` rows and FC-6 `paired P1` operands mis-stated, requiring
   the explanation to be **"re-authored, not merely re-scored."** `FINDING-capx-d60-2026-09-05.md`
   §5.5 already routed that re-authoring rather than absorbing it, measuring the carried table
   **already stale on 6 of 42 computable rows**. A verdict written here would be a re-score standing
   in for a re-authoring.
3. **It is not the posture the six landed legs took**, and the director graded that posture at r#53
   (*"incumbents preserved — a new label is a new run_id; nothing overwritten"*). Leg 7 taking a bare
   key while its six siblings do not would make the batch internally inconsistent for no measured
   reason.

### 7.4 Two things this measurement surfaced, reported and routed, not acted on

* **Three registered runs already render a `neiso-t3` verdict scored on a different run.**
  `neiso-2026-2050-t3-golden-bau`, `-golden2-bau` and `-golden3-bau` each carry
  `meta.verdict_key = "neiso-t3"`, and that pointer now resolves to the D60 verdict — so all three
  display D60's determination *and* inherit its provenance stamp over their own. It is pre-existing
  (the bare key is a moving pointer and these runs were pinned to it before it moved), it is not
  this lane's to repair, and **it is a fourth reason leg 7 should not join them.** The same shape
  exists on `miso-2026-2030-s123-verify` → `miso-t1f`, `neiso-2026-2030-s4hydro` → `neiso-t1f` and
  `pjm-2021-2025-realized-t1h-d67arm` → `pjm-t1h`; those belong to other desks and are named here
  only so the class is on the record. Everything else round-trips: of the verdicts whose provenance
  `run_id` is a registered run, **28 resolve back to their own run**, and all seven bare t1f/t3 keys
  are correctly held by the run that scored them.
* **A docstring/code drift in the registrar.** `register_forecast_run.py`:111 says *"``--verdict-key``
  sets it"*, but `main()` defines no such flag; the only routes are `meta["verdict_key"]` (reachable
  via `--extra-meta`) and `VERDICT_MAP`. Reported under CLAUDE.md's "fix the docs" rule and **routed**
  — a 1,320-line core script is not this lane's to edit for a comment, and the forecast-registrar
  owner should take it.
