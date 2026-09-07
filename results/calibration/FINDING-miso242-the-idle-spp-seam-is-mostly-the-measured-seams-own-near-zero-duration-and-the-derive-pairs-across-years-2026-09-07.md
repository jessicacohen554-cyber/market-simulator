# FINDING miso-242 — **84 / 88 / 77 % of the model's idle SPP seam is the MEASURED seam's own near-zero duration**, transmitted by a Q-Q ladder working as designed (`Z_target` **0.3501 / 0.3580 / 0.3698** against a model **0.4175 / 0.4066 / 0.4810**) — and the residual is fully decomposed, because the committed per-year SPP ladder's derive **PAIRS EACH YEAR'S MISO ROWS AGAINST ALL THREE YEARS OF SPP HUB PRICES**

**Zero LP. No arm, no screen, no bundle, no registration, no field, no cell verdict, no re-derive,
no repair.**
**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and **no out-of-training year was
solved, scored or registered**. MISO still carries exactly **one** registered run (rule 15).

**Pre-registration: `PREREG-miso242-why-the-spp-seam-is-idle-2026-09-07.md`, pushed together with
its probe and BEFORE either was run.** Three addenda, each pushed **before the numbers it governs**:
`ADDENDUM-miso242-the-dead-band-predicate-was-a-rearrangement-2026-09-07.md` (this session's own
gate failure and its repair), `ADDENDUM-miso242-the-edge-decomposition-2026-09-07.md` (the decided
Q-A…Q-E results, published **before** D-EDGE ran), and
`ADDENDUM-miso242-the-derive-pairs-across-years-2026-09-07.md` (V-1…V-5 with its bars). **Every
decision rule applied below was fixed in one of those four documents; none was written after seeing
a number.**

Probes: `scripts/probes/_miso242_spp_idle_seam_phase0.py` → `_miso242_spp_idle_seam_phase0.json`;
`_miso242_edge_decomposition_addendum.py` → `_miso242_edge_decomposition_addendum.json`;
`_miso242_derive_pairing_addendum.py` → `_miso242_derive_pairing_addendum.json`.

**Queue item taken (rule 28(a)): item 1 — the handoff's RECOMMENDED item**, *"why the model's SPP
seam is at exactly zero in 42/41/48 % of hours"*.

**Basis (PREREG §0b).** The Indiana-hub **RT** series builds the finite-hour `ok` mask
byte-identically to miso-235…241. Every **spread** is the Indiana-hub **DA**; the SPP anchor is the
measured SPP **NORTH** hub DA; `p_bus` is the keeper's committed `MISO_external` P1 price. They
correlate only +0.402 / +0.424 / +0.553 and are never interchanged. miso-232's measured decile
column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

---

## 0. STATED FIRST, AGAINST INTEREST — four disclosures, and the first three cost this session something

### 0a. THIS SESSION'S OWN G-DB GATE FAILED, and the failure was published before it was repaired

Five of six provenance legs passed exactly on the first run. **G-DB — this session's own falsifiable
identity leg — FAILED on 16 / 1 / 26 SPP hours** against a bar of zero (PJM: 0 / 0 / 0). Every one
of the 43 hours is an **exact tie**: `p_bus − (spp_hub + δ_1^export) == 0.0` to the bit.

The cause was a defect in **the PREREG's own §0 F3**, not in the instrument. `build_recons` uses
**two** operand forms — the import leg tests a **spread** (a subtraction), the export leg tests a
**level** (an addition) — and F3 rearranged the export edge into the spread form. That is exact in
real arithmetic and **not** exact in IEEE double arithmetic at ties.

The repair was declared in a **pushed addendum before the repaired numbers existed**, **no bar was
moved**, and the repair is **stricter**: each edge is now evaluated in its own leg's operand form,
so G-DB tests the predicate the code evaluates rather than a rearrangement of it. The addendum also
fixed the **bound** in advance — at most 16 / 1 / 26 of 8,741 / 8,760 / 8,712 hours can move, i.e.
**≤ 0.0030**, which is 6.7× below Q-A's bar and 16.7× below Q-B's, so the repair **could not flip
any verdict**. On the re-run G-DB reads **0 / 0 / 0** on both seams and the other five legs are
unchanged at |Δ| = 0.0000.

**Reported, never gated:** an exact tie at `p_bus = spp_hub + δ_1^export` is the signature of the
**SPP export band 1 being exactly marginal at the external bus**. 16 / 1 / 26 such hours is a fact
about the keeper's dispatch; no verdict is attached to it.

### 0b. THE SESSION'S HEADLINE HYPOTHESIS WAS POST-HOC, and it is labelled as such

The cross-year pairing defect (§5) was **not** anticipated by the PREREG. It was formed **after**
reading D-EDGE's `quantile_recheck` column — a column that *was* pre-declared and pushed before it
ran, but whose interpretation was not. That is why it is not asserted anywhere on the strength of
that column: it was **pre-registered as V-1…V-5 with its bars, in a pushed addendum, before the
confirming test ran**, and with **three independently refuting legs** (V-1, V-2 and V-3 can each
kill it) plus a control on the seam whose derive takes no join.

### 0c. THIS SESSION'S OWN "corroboration" WAS CORROBORATING THE DEFECT

The phase-0 probe carried a *read-only derive verification* — re-running
`derive_spp_neighbour_hourly` and comparing to the committed table — which returned
`band1_import_delta_vs_committed = 0.0` and `band1_export_delta_vs_committed = 0.0` in all three
years, and which this session initially read as evidence that the committed ladder was sound. **It
was not.** It invokes `derive_spp_neighbour_hourly(g_all.loc[year])` — the *same* call the defect
lives in — so it reproduces the mispaired ladder and agrees with it exactly. The column is correct
and its interpretation was wrong; it is re-labelled here as **a consistency check that cannot detect
this class of defect**, which is precisely §7's point about the rule-23 pin test.

### 0d. THE BRANCH THAT WOULD HAVE LET THIS SESSION WRITE "ITEM 1 CLOSES" DID NOT OCCUR

PREREG §4's decision table licenses *"item 1 CLOSES"* only on `IDENTITY HOLDS + TRANSMITTED`. Q-A
**FAILS** in 2023 (0.0395 against a 0.020 bar) and Q-B reads **DISPLACED** in 2025 (0.1017 against
0.050), so the pre-registered verdict is **TABLE-INTERNAL** and **this session does not claim the
closure it would have preferred.** The question is *answered and fully decomposed* below; the queue
item is **handed forward with a named, quantified successor**, not closed.

---

## 1. THE PROVENANCE GATE — **ALL SIX LEGS PASS**

| leg | what it reproduces, in the predecessor's own metric | bar | **measured** |
|---|---|---:|---:|
| **G-T** | the committed SPP + PJM hourly ladder tuples = PREREG §0 F2; import non-decreasing / export non-increasing in `k`, both seams, all years | exact / 0 | **exact, 0 violations** |
| **G-Z** | miso-241 §3's SPP zero-flow share **0.4175 / 0.4066 / 0.4810** and `env_i`=0 share 0.0106 / 0.0035 / 0.0034 | ≤ 0.002 | **0.0000** (all six) |
| **G-L** | miso-241 §3's `ceiling_active_share` **0.2572 / 0.2952 / 0.2474** and mean import bands in merit **0.5035 / 0.4880 / 0.3311** | ≤ 0.002 / 0.01 | **0.0000** (all six) |
| **G-ID** | miso-241's prefix identity `flow ≡ min(env^eff, n·w)`, both legs of both export variants, four seams | ≤ 1e-6 MW, 0 | **0.0 MW, 0** |
| **G-B** | miso-241 Q-0's **REPAIRED** harness `corr` **0.9917 / 0.9935 / 0.9935** and level **8.9 / 1.8 / 5.8 MW** | ≤ 0.002 / 0.5 MW | **0.0000 / 0.02–0.05 MW** |
| **G-DB** | the dead-band identity: `{n_i = 0 ∧ n_e = 0}` ≡ the dead band, SPP **and** PJM | 0 hours | **0 / 0 / 0**, both seams |

**G-B is the leg that matters for provenance**: it pins this session to miso-241's **repaired**
export pricing rather than miso-235's superseded one, and it reads |Δcorr| = **0.0000**.
**G-DB is falsifiable and it did fail once** (§0a) — which is the point of writing it.

Three predecessors' published columns reproduce on this code path (miso-241's zero-flow, ceiling and
identity legs; its repaired harness), and an **unplanned fourth** in §6: the derive script's own
docstring statistic `corr(measured SPP seam flow, MISO DA − SPP hub DA)` = +0.041 / −0.020 / +0.050
recomputes to **+0.0409 / −0.0200 / +0.0502**.

## 2. THE ANSWER TO ITEM 1 — the model's idle seam is **mostly the measured seam's own near-zero duration**

`Z_target` = `P(|measured SPP net flow| ≤ 250 MW)`, the quantity the Q-Q estimator's dead band is
constructed to reproduce (PREREG §0 F5), measured on the derive's own row set:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **`Z_target`** — the MEASURED seam within ±250 MW of zero | **0.3501** | **0.3580** | **0.3698** |
| `Z_model` — the model's seam at EXACTLY zero (miso-241 §3) | 0.4175 | 0.4066 | 0.4810 |
| **share of the model's idle hours that `Z_target` accounts for** | **83.9 %** | **88.0 %** | **76.9 %** |
| measured SPP flow mean / σ (MW) | +109.9 / 577.5 | −42.7 / 687.4 | +109.8 / 615.3 |

**The 42 / 41 / 48 % is not, in the main, a model artifact.** The real MISO–SPP seam sits within
±250 MW of zero in **35–37 % of hours**; the model's 500 MW band granularity renders every such hour
as *exactly* zero, and the Q-Q ladder is constructed to reproduce that duration. miso-241's σ
statistic (577 / 687 / 615 MW) is a **dispersion** measure and says nothing about near-zero
duration — a seam can have large σ and still be near zero much of the time, and this one is.

**The remainder decomposes exactly** (arithmetic on the pre-registered columns; no new statistic):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| gap `Z_model − Z_target` | 0.0674 | 0.0486 | 0.1112 |
| ├ **Q-A**, the committed table's own miss (§5: the pairing defect) | **0.0395** | 0.0144 | 0.0089 |
| ├ **Q-B**, the model bus-price displacement | 0.0274 | 0.0344 | **0.1017** |
| └ row-set residual (R_D vs R_K) | +0.0005 | −0.0002 | +0.0006 |

## 3. Q-A — **IDENTITY FAILS** (2023). PJM is EXACT

| `|Z_derive − Z_target|` | 2023 | 2024 | 2025 | bar |
|---|---:|---:|---:|---:|
| **SPP** | **0.0395** | 0.0144 | 0.0089 | ≤ 0.020, all years |
| **PJM** | **0.0000** | **0.0000** | **0.0000** | — |

The pre-registered rule requires all three years, so **SPP reads IDENTITY FAILS on 2023 alone**;
2024 and 2025 hold comfortably. **PJM's identity is exact in every year**, which is what makes the
SPP miss a signal rather than an estimator tolerance — and §5 identifies its cause.

## 4. Q-B — **DISPLACED** (2025), and the diagnostics say *compression*, not shift

| SPP, on the single common row set R_K | 2023 | 2024 | 2025 | bar |
|---|---:|---:|---:|---:|
| **`|Z_model − Z_derive^K|`** | 0.0274 | 0.0344 | **0.1017** | ≤ 0.050 |
| signed | +0.0274 | +0.0344 | +0.1017 | — |
| mean `s_model` / `s_derive` | 10.11 / 8.74 | 10.86 / 10.07 | 13.21 / 15.65 | — |
| **σ `s_model` / σ `s_derive`** | **18.59 / 22.11** | 24.11 / 23.97 | **21.21 / 29.16** | — |

**Every year's displacement has the same sign** — the model's bus-price spread puts *more* mass in
the dead band than the derive's spread does — and the 2025 magnitude is driven by **compression**:
σ falls 29.16 → 21.21 (−27 %) while the mean falls 15.65 → 13.21, and the 2025 dead band sits at
`[+1.04, +21.85]`, so a lower, narrower spread distribution lands squarely inside it. The underlying
price statistic is in §6: **σ(`p_bus`) is 6.09 / 16.51 / 15.22 against σ(MISO DA) 12.81 / 19.89 /
26.12** — the model's external bus price is materially less volatile than the measured Indiana hub
in every year, by 2.1× in 2023 and 1.7× in 2025. PJM's displacement is 0.0021 / 0.0212 / 0.0562 on
the same construction.

## 5. **THE DEFECT — CONFIRMED ON ALL THREE REFUTING LEGS.** The per-year SPP ladder's derive pairs each year's MISO rows against ALL THREE hub years

`derive_spp_neighbour_hourly(g)` does `work = g.join(load_spp_hub_da(), how="left")`. Both the CLI
(`_print_ladder(df.loc[year])`) and the rule-23 pin test (`derive_spp_neighbour_hourly(joined.loc[year])`)
pass `df.loc[year]`, whose index is **`hour` alone**, while `load_spp_hub_da()` is
**`(year, hour)`**-MultiIndexed. pandas partial-joins on the shared level name, so each of the
year's 8,760 MISO rows is replicated against **all three years'** SPP hub price for that hour.
`derive_pjm_neighbour_hourly` performs **no join** (`pjm_border` is already a column of `g`) — that
asymmetry is the signature, and V-3 is built on it.

| leg | bar | **measured** | |
|---|---|---|---|
| **V-1** | join = 3 × 8,760 rows; `da` and SPP flow identical across the three hub-year blocks | **26,280 rows**, blocks {2023: 8,760, 2024: 8,760, 2025: 8,760}, deviations **0.0 / 0.0** | **PASS** |
| **V-2** | the **mispaired** frame reproduces the **COMMITTED** per-year table, all 48 entries, atol 0.005 | **0.0000** | **PASS** |
| **V-3** *(CONTROL)* | PJM's **no-join** derive reproduces its committed table, all 48 entries | **0.0000** | **PASS** |
| **V-5** | the **POOLED** forward ladder — `df.loc[a:b]` keeps the MultiIndex, so its join should be proper | **26,280 rows, correctly paired**; reproduces the committed pooled tuple at **0.0000** | **PASS** |

**HYPOTHESIS CONFIRMED.** What is contaminated is precisely one thing, and it is worth stating
exactly: the 3× replication leaves every **flow** exceedance share untouched (replicating a sample
three times does not change a share), so the estimator's **targets** `P(flow > mid_k)` and
`P(flow < −mid_k)` are **correct**. The **quantile is drawn from a three-year mixture of the spread**
instead of the year's own spread.

### 5a. **V-4 — REPORTED, GATED NOWHERE, AND EXPLICITLY NOT ADOPTED.** What the correctly paired frame would produce

| band 1 | committed (mispaired) | **correctly paired** |
|---|---|---|
| 2023 import / export | 14.10 / −4.20 | **13.44 / −2.39** |
| 2024 import / export | 14.49 / −2.15 | **17.26 / +1.44** |
| 2025 import / export | 21.85 / +1.04 | **18.58 / −2.37** |
| dead-band width | 18.30 / 16.64 / 20.81 | **15.83 / 15.82 / 20.95** |

**And this is what closes §3:** with the correctly paired ladder, `|Z_derive − Z_target|` becomes
**0.0003 / 0.0000 / 0.0001**, against the committed table's **0.0395 / 0.0144 / 0.0089**.
**Q-A's failure is fully attributed** — the Q-Q identity is essentially exact once the pairing is
right, and 2023 was the year the mixture displaced most.

**NOTHING HERE IS ADOPTED, COMMITTED OR TARGETED.** PREREG §5.2 refused a re-derive **in advance,
for every branch, and named the IDENTITY-FAILS branch** — the branch that occurred — as the one
where the temptation would be largest. The frozen committed table is **unchanged**; no δ_k moved, no
K changed, no spacing changed, no damping factor exists, and the envelope, its percentile and every
interface limit are untouched (rules 14 / 23). **Every number in this section is UN-TARGETABLE**
(PREREG §5.1): no successor may size, scale, tune or select anything to land on it.

## 6. Q-D and Q-E — the contrast is confirmed and the sign hypothesis is REFUTED

**Q-D, the one gated question: `Z_target(PJM) < Z_target(SPP)` — YES, in all three years.**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **`Z_target` PJM** | **0.0022** | **0.0142** | **0.0314** |
| **`Z_target` SPP** | **0.3501** | **0.3580** | **0.3698** |
| ratio | **159×** | **25×** | **11.8×** |

**The two seams' idle behaviour differs in the MEASURED record, before any model object touches
it.** Reported, never gated: model import-leg zero share PJM 0.0055 / 0.0467 / 0.0988 against SPP
0.5718 / 0.5788 / 0.7052; dead-band width PJM 64.81 / 21.16 / 44.70 against SPP 18.30 / 16.64 /
20.81 — PJM's band is *wider* but sits **entirely at negative spreads** (upper edge −29.17 / −13.87
/ −15.79) while realized spreads average +4.12 / +2.81 / +2.29, so PJM's seam clears almost always.
**Width was the wrong intuition; position is the operative property**, and the position is set by
the measured flow duration the Q-Q map reads.

**Q-E1, gated: `corr(model SPP net flow, s_model)` = +0.7946 / +0.6989 / +0.7434 > 0 in all three
years ⇒ the SIGN HYPOTHESIS IS REFUTED.** The merit test's sign and basis are right.

**Reported, never gated, and it is the structural fact of the session beside §2:**
`corr(measured SPP net flow, s_derive)` = **+0.0409 / −0.0200 / +0.0502** — reproducing the derive
script's own docstring figure (+0.041 / −0.020 / +0.050) to the digit. **The model's SPP seam is
0.70–0.79 correlated with the hub-pair spread; the real one is 0.04.** The seam being idle is not
the anomaly — it is that the model's seam is *spread-driven at all*. That corroborates miso-235 §4's
`PRICE_RESPONSE_OVERSHOOT` + `MISSING_NON_PRICE_VARIATION` verdict on an entirely independent
statistic, and it is the handoff's own stopping condition — *"the ladder is correct and the real
seam's flow is simply not spread-driven"* — met on this session's numbers. Also reported:
`corr(p_bus, MISO DA)` 0.6925 / 0.5863 / 0.7833, means 34.35 / 32.16 / 41.30 against 32.98 / 31.37 /
43.73, and mean SPP hub 24.24 / 21.30 / 28.08.

## 7. The rule-23 pin test, recorded and NOT scored

`tests/iso/miso/test_miso_seam_ladder.py::test_registry_reproduces_the_frozen_derivation` invokes
`dm.derive_spp_neighbour_hourly(joined.loc[year])` — **the same call** — so it compares the committed
table against the same mispaired output and passes, as it did throughout and will keep doing.
**That is not a failure of the test.** It pins *consistency* (the table IS the derive's output, so a
hand-edited or silently re-tuned offset fails there rather than reaching a solve), which is exactly
what rule 23 `[R-FROZEN-DERIVE]` asks of it. It is simply not a *correctness* pin, and nothing
suggests it was meant to be. **This observation is recorded, not scored, and it names no defect in
the test.** §0c records that this session's own verification column had the identical blind spot.

## 8. Rule 19 `[R-ONE-MECH]` — the enumeration, written whatever the verdict

What already sets the MISO–SPP seam on the keeper: the armed **hourly SPP neighbour anchor**
(`miso_seam_neighbour_hourly_spp`, band `k` at `spp_hub(t) + δ_k`, import and export alike); the
**frozen Q-Q `δ_k` ladders** (`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR`); the **incumbent
MISO-hub Q-Q ladder** it displaces (`MISO_SEAM_LADDER_BY_YEAR["SPP"]`, an alternative, never
stacked); the **measured `(month × hod)` deliverability envelope** in both directions under the
merit-order waterfall; the seam's **4,000 MW** interface limit and its eight **500 MW** bands; the
`MISO_external` border-link TTCs; the **8,700 MW** `MISO_simultaneous_import` SIL; and the published
**CIL/CEL** deliverability groups. **Nothing is added, so nothing replaces and nothing reconciles.**

## 9. What is handed forward

1. **ITEM 1 IS ANSWERED AND FULLY DECOMPOSED, BUT NOT CLOSED** (§0d). **84 / 88 / 77 %** of the
   model's idle SPP hours are the measured seam's own ±250 MW duration, transmitted by a Q-Q ladder
   working as designed; the remainder is **0.0395 / 0.0144 / 0.0089** of committed-table miss plus
   **0.0274 / 0.0344 / 0.1017** of model bus-price displacement. A successor does **not** need to
   re-measure any of this.
2. **THE NAMED SUCCESSOR, AND IT IS A REPAIR SOMEONE MUST DECIDE ON.** The per-year SPP hourly
   ladder's derive pairs across years (§5), confirmed on three refuting legs with a control. **This
   session did not repair it, on its own pre-registered refusal**, and a repair is **not** a lane's
   unilateral act: it moves `δ_k`, therefore the keeper's solve, so it is a mechanism change owing a
   rule-29 `[R-SCREEN]` phase 0 + one-year screen on the mechanism's own footprint, a G-DRIFT audit,
   and a promotion decision. **The magnitudes it would move are in §5a and are UN-TARGETABLE**; a
   successor derives its own, and must not select the pairing by which arm scores better — the case
   for correct pairing is **rule 14 `[R-ACCURATE]` and rule 23's own construction**, never a
   residual.
3. **THE FORWARD LADDER IS NOT AFFECTED** (V-5): `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED` is
   correctly paired and reproduces at **0.0000**. Rule 13's forward story is intact; only the
   per-year backcast table is implicated.
4. **PJM IS CLEAN ON EVERY LEG THIS SESSION RAN** — Q-A exact, V-3 exact, G-DB 0/0/0, and its
   `quantile_recheck` reproduces its committed δ to four decimals. No PJM object is implicated and
   none should be re-tested.
5. **THE SIGN AND BASIS OF THE MERIT TEST ARE RIGHT** (Q-E1, +0.79 / +0.70 / +0.74). That hypothesis
   is **REFUTED** and should not be re-opened.
6. **THE DEEPER STRUCTURAL FACT, reported and chartering nothing:** the model's SPP seam is 0.70–0.79
   spread-correlated and the measured one is 0.04. Any future SPP work should start from *that*,
   not from the idle share — and miso-241 §5 already refused the quantity-side charter for want of a
   DOF-free form. **The SPP quantity-side charter stays REFUSED** and is not re-opened here.
7. **UNCHANGED AND NOT RE-TESTED:** queue item 1's *external-bus price* half stays **CLOSED**; the
   per-seam external-node split **REFUSED at zero LP**; the saturation hypothesis **REFUTED**;
   miso-239's Q-A **MIXED** and Q-C **SURVIVES**; miso-240's Q-B **UNRESOLVED**; the `(month × hod)`
   template hypothesis **REMOVED**; the PJM import/export asymmetry **CLOSED FOR PJM**; South's
   neighbour-state route **CLOSED**; `miso_manitoba_seam` **CLOSED as already-armed**;
   `internal_congestion_split` **G**; `vre_reference_rate_curtailment_grossup` **K**;
   `measured_interface_limits` **R**; `miso_rdt_measured_limit` **R**; `m2m_seam_entitlement_cap`
   **G**; `miso_south_firm_export_block` **G**; `miso_south_export_ladder_rt_tail` **R**;
   `miso_south_gas_delivered_cost_basis` **R**.
8. **Manitoba determinism**, **the export-leg asymmetry**, **CC_REGULAR 2024→2025 shape emergence**,
   **Q-B's successor** and **C3c** (the designated frontier) are untouched and stay where they are
   filed. C3c still needs a new admissible measured identification **and** an owner ruling; no LP is
   authorized there and none was sought.

## 10. Non-claims

1. **This session solved nothing.** No screen ran, nothing went through a structural gate, no number
   is a solve result, and **there is no keeper candidate**.
2. **Nothing was repaired.** The committed ladder, the envelope, its percentile and every interface
   limit are byte-identical to what this session found. **No re-derive was run into the registry**;
   the derive was executed read-only, as an instrument.
3. **§5a's correctly-paired values are NOT a proposal and NOT a target.** They are the magnitude a
   successor needs in order to scope a screen, and they are un-targetable like every other number
   here.
4. **The model side is a RECONSTRUCTION** (harness `corr` 0.9917 / 0.9935 / 0.9935 — close, not 1).
   Every model-side share inherits that.
5. **Q-A's 2023 failure is EXPLAINED, not CANCELLED.** The verdict on the pre-registered decision
   table is **TABLE-INTERNAL** and stands.
6. **No verdict moves anywhere in the matrix**, in either direction; evidence only.
7. **MISO has no failing gate.** There is no rubric failure anywhere in the program, this session
   did not invent one, and nothing here trades a passing gate for anything.
8. **A measured near-zero duration is not a licence and not a defect.** It is a duration.

## 11. Governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; every gate was structural, every number
was declared un-targetable before it was computed, and §5's defect is named on **construction**
(a mis-specified join), never on a residual. Rule 12 `[R-PARALLEL]`: no LP; nothing ran on CI.
Rule 13 `[R-MEASURED]`: measurement only; no input changed and no measured outcome entered any
solve. Rule 14 `[R-ACCURATE]`: no input changed; the measured envelope, its percentile and every
interface limit are untouched — and §9.2 names rule 14 as the *basis* on which a successor would
argue the repair, never the residual. Rule 15 `[R-DASHBOARD]`: no run produced, so nothing registered
or pruned; MISO keeps exactly one registered run and the keeper's `hourly/` sidecars stay committed.
Rule 17 `[R-FLOOR-WINDOW]`: no floor added. Rule 19 `[R-ONE-MECH]`: no mechanism added; §8 writes the
enumeration anyway. Rule 21 `[R-DOF]`: **41/2, unchanged**; every instrument here carries zero free
parameters beyond the decision bars fixed ex ante and the ±250 / ±456.25 MW midpoints, which are
`interface_limit_mw / SEAM_FLOW_TRANCHES / 2` — an identity. Rule 22 `[R-HOLDOUT]`: 2023–2025 only;
MISO holds no `complete` marker and no out-of-training year was solved, scored or registered.
Rule 23 `[R-FROZEN-DERIVE]`: **no derive re-run into the registry**; the frozen table is unchanged
and §7 records why its pin test cannot see this defect. Rule 24 `[R-REGISTRY]`: no field created.
Rule 25 `[R-ISO-SCOPE]`: MISO's shard, section and lane only — SPP's own shard, keeper and lane are
untouched, and the SPP hub series is read as a measured *price input*, never as SPP's calibration.
Rule 26 `[R-DELETE]`: the defective dead-band predicate is **replaced** in this session's instrument,
not left behind a flag. Rule 27 `[R-PUSH]`: on-disk edits only; every pushed blob ≥ 300 lines
verified against local after push. Rule 28(a): queue item 1 taken; every standing adjudication
touched is corroborated or untouched, never re-tested. Rule 28(b): **no verdict moves**; evidence
appended in MISO's shard in-session. Rule 29 `[R-SCREEN]`: clause 0 in full — a zero-LP phase 0 that
**answered the recommended queue item, decomposed it exactly, and found a construction defect in a
committed derive, before a single LP minute was spent**.
