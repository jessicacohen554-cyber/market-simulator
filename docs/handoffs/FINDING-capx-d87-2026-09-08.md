# FINDING — capx D87: the CCS retrofit screen consumes the clean-tier seam

**Lane:** capx D87 · **Branch:** `claude/capx-d87-ccs-clean-tier-seam` · **Date:** 2026-09-08 ·
**Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `nyiso` + `code`
**Charter:** capx ledger §0bf ← `DESIGN-capx-d87-d88-s19-read-2026-09-08.md` §1.6 ← SCN ruling
S19 (D-15). **Pre-registration:** `PRECOMMIT-capx-d87-2026-09-08.md` + its ADDENDUM (gate G7),
both pushed **before** the edit and **before** any solve.

---

## 0. RESULT

**The seam is real, it is repaired, and the screen's identity gate passes to the cent.** Six of
the seven pre-registered gates PASS. **G2 fails by the letter on one year, by 0.338 MW, and the
cause is my own rounding in transcribing the bound** (§4.2) — reported, not re-derived.

Three things the screen established that no committed artifact could:

1. **The repair does exactly what its arithmetic says.** `attr_post` in the arm's 2028 and 2029
   retrofit ledgers is **47.50 $/MWh** — the ACP 50.00 × `federal_ces_ccs_capture_fraction` 0.95,
   exactly — against **0.0** in the control, and `attr_unabated` is 0.0 in every year of both.
2. **The 2029 endogenous dual is $7.5636/MWh**, read off the arm's own 2030 ledger
   (`attr_post` 7.18544 / 0.95). The PRECOMMIT could only bound it as "endogenous ∈ (0, 50]".
3. **The control solve that rule 29(b) earned was a no-op**: it reproduces the committed campaign
   in all three retrofit years to 0.04 MW, so the one LIVE G-DRIFT hunk moved the decision by
   **0.000 MW** (§3).

**My own pre-solve bracket prediction MISSED, for a reason that is the most interesting thing in
this document** (§5): a target row is *not* a constant premium, because its dual **collapses when
the standard starts binding**.

---

## 1. THE DEFECT IN ONE TABLE, FROM THE COMMITTED RECORD ALONE

NYISO, cumulative `gas_cc_ccs` MW, `scn-campaign-policy-2026-09-06`:

| leg | what the retrofit screen saw (`attr_post`, $/MWh) | 2028 | 2029 | 2030 |
|---|---|---:|---:|---:|
| `REF` — no CES at all | 0 (correctly none) | 2,984.4 | 5,255.9 | 6,255.9 |
| **`CES-T80` — a $50/MWh ACP target row** | **0 (the defect)** | **2,984.4** | **5,255.9** | **6,255.9** |
| `CES-P20` — a $20/MWh premium | 19.00 | 2,999.7 | 5,999.7 | 7,731.7 |
| `CES-P60` — a $60/MWh premium | 57.00 | 2,999.5 | 5,999.3 | 7,890.3 |

**A $50/MWh target row bought exactly what no policy at all bought — identical to `REF` to 0.1 MW
in all five years — while a $20/MWh premium bought +1,475.8 MW by 2030.** A stronger instrument at
a higher price produced a smaller response than a weaker one, entirely because of which code path
carried it.

**The repair, one seam** (`ccs.py:475-476` + the `evolve.py:664` threading): fold
`clean_credit_for_zone(by_fuel, fuel, zone_idx)` into BOTH continuations through the existing
`max()` — the composition `retirements.py:3634` (step 3) and `new_entry.py:1202` (step 5) already
use. A `None`-default keyword, no `ScenarioConfig` field, no constant, no RPS leg, zero cache keys
(rules 19 / 21 / 24 / 25). `None` ⇒ credit 0.0 ⇒ `max(x, 0.0) == x` ⇒ byte-identical.

---

## 2. THE SCREEN — the measured A/B

Both arms solved at HEAD, concurrently, NYISO `CES-T80` 2026-2030, key `eb1b0e1df942db47` in both;
the control is the arm's **exact parent commit** in a code-only git worktree with its own results
cache. 14/14 invariants PASS and 5/5 years solved in both (arm 74.9 min, control 62.6 min wall).

### 2.1 Retrofit MW — annual adds recorded by the ledger

| year | CONTROL | ARM | Δ | pre-registered G2 bound | cap headroom (from the control) |
|---:|---:|---:|---:|---|---:|
| 2026 | 0.000 | 0.000 | +0.000 | (inert) | — |
| 2027 | 0.000 | 0.000 | +0.000 | (inert) | — |
| **2028** | 2,984.397 | 2,999.463 | **+15.065** | ≤ +16 ✓ | 15.603 |
| **2029** | 2,271.542 | 2,999.880 | **+728.338** | ≤ +728 ✗ **by 0.338** | 728.458 |
| **2030** | 1,000.000 | 1,384.227 | **+384.227** | ≤ +2,000 ✓ | 2,000.000 |

Cumulative `gas_cc_ccs`: control **6,255.940** MW at 2030, arm **7,383.569** MW — **+1,127.6 MW**
of capture capacity that the target row had been paying for and not getting.

### 2.2 The identity — G1, the screen's centrepiece

| year | CONTROL `attr_post` | ARM `attr_post` | ARM `attr_unabated` | what it means |
|---:|---:|---:|---:|---|
| 2028 | 0.0 | **47.50** | 0.0 | = ACP 50.00 × 0.95 (2027 row escaping at the ACP) |
| 2029 | 0.0 | **47.50** | 0.0 | = ACP 50.00 × 0.95 (2028 row escaping) |
| 2030 | 0.0 | **7.18544** | 0.0 | ⇒ **the 2029 endogenous dual is $7.5636/MWh** |

The 2028/2029 values are the PRECOMMIT §2.3 reconstruction confirmed by the model itself: I derived
the 2027 and 2028 duals as "ACP $50 exactly" from the row's feasibility state alone, with no NYISO
`duals.json` committed, and the arm's ledger prints 47.50 = 50 × 0.95. `attr_unabated` is 0.0
everywhere, as `gas_cc`'s absence from `federal_ces_eligible_fuels` requires.

---

## 3. G-DRIFT — and the control solve it earned, which turned out to be a no-op

The charter named the committed bundle as the control under a G-DRIFT audit, *never* a control
solve. The audit's PRIMARY basis passed — the recipe re-keys to its recorded `eb1b0e1df942db47`
at HEAD, proved twice (from the committed 813-field config dict, and from the live ladder recipe
once NYISO's own `ISOConfig.default_scenario_overrides` are applied). But a key is necessary, not
sufficient: behaviour outside the seven `SURFACE_MODULES` does not re-key. So every changed hunk on
a NYISO forecast path was classified — **34 commits, 62 files, 3,576 non-comment added lines** —
and exactly **one was LIVE**: `eia860.py::_apply_simple_cycle_hr_floor` (SPP-49), documented in its
own source as *"a CONSTRUCTION, not a gate: frame-level and unconditional"*. NYISO footprint,
measured before the solve: **3 plants / 10 rows / 19.0 MW net summer**, none of them `gas_cc`.

Two other ungated repo-wide seams were **measured rather than assumed inert**:
`eia930.actuals._screen_fuel_spike_columns` repairs exactly one NYIS hour in 2019-2025 and it is in
`NG: OTH`, a benchmark-only series (`NG: WND` / `SUN` / `WAT` untouched in every year); and
`neighbor_price._measured_henry_hub_annual` fires only below a trajectory's first knot, all of
which are ≤ 2023.

**The control solve settled it empirically.** Against the committed campaign:

| year | committed `CES-T80` | CONTROL solve | difference |
|---:|---:|---:|---:|
| 2028 | 2,984.4 | 2,984.397 | 0.003 (rounding) |
| 2029 | 5,255.9 | 5,255.940 | 0.040 (rounding) |
| 2030 | 6,255.9 | 6,255.940 | 0.040 (rounding) |

**The LIVE hunk moved the decision by 0.000 MW.** Worth stating in both directions: the audit's
classification was right, *and* spending the solve was still correct, because "19 MW of small units
probably does not matter" is an argument, not a measurement. Rule 29(b) is vindicated on both
halves — the audit is cheap and usually sufficient, and the one case it flags is worth paying for.

---

## 4. THE GATES

| gate | verdict | evidence |
|---|---|---|
| **G1** identity | **PASS** | §2.2 — control 0.0 everywhere; arm 47.50 in 2028/2029; arm 2030 in (0, 47.50]; `attr_unabated` 0.0 in every year of both arms |
| **G2** direction & order | **FAIL by the letter** | 2028 +15.065 ≤ 16 ✓; **2029 +728.338 vs ≤ 728 ✗ by 0.338**; 2030 +384.227 ≤ 2,000 ✓. §4.2 |
| **G3** the cap | **PASS** | max annual retrofit 2,999.880 MW (arm 2029) ≤ 3,000.000 |
| **G4** 2026-2027 inertness | **PASS** | both years' ledgers **byte-identical** between arms, every key |
| **G5** no invariant flip | **PASS** | 14/14 PASS in both arms, 5/5 years, nothing flipped |
| **G6** byte-identity off the target row | **PASS** | by construction + 7 seam tests; **no LP spent** |
| **G7** duplicate-`unit_id` census | **PASS** | §4.3 |

### 4.2 The G2 miss, and why I am not re-deriving the bound

The bound is not an independent quantity. PRECOMMIT §2.3 derived it **as the cap headroom** ("up to
+728 MW (to the 3 GW cap)"), computed from the **rounded** committed value 2.272 GW
(3.000 − 2.272 = 0.728). The true control add is 2,271.542 MW, so the true headroom is
**728.458 MW**, and the measured delta **728.338 sits inside it**. The arm is cap-saturated at
2,999.880 ≤ 3,000.000, so **G3 — the physical constraint the bound was a proxy for — passes**.

So the excess is a transcription artifact, not a mechanism surprise. That is **stated, not used.**
A screen gate is STOP-ONLY and pre-registered; re-deriving a bound after seeing the result is
exactly the selection rule 1 `[R-STRUCT]` forbids, and the fact that this particular re-derivation
would be arithmetically innocent does not make performing it unilaterally acceptable. **The miss
stands on the record and the judgement is the owner's.** Recorded before the 2030 ledgers existed
(the session's scratch note `g2-2029-bound-miss.md`, written at the time).

### 4.3 G7 — the D88 census, and why it passes structurally

No `unit_id` appears twice in any year's fleet in either arm; no id is retrofitted in two different
years (the impossibility signature D88's census found on all nine NEISO T3 variants); no
legacy-form id is re-minted by a later economic `gas_cc` entry. The arm carries **53** distinct
retrofitted ids across 2026-2030 against the control's **33** — i.e. the arm retrofits 20 more
units and still collides with nothing.

**The structural reason, which is D88's own:** NYISO's retrofit ids are **CAMPD per-plant** form
(`CC_REGULAR_Capital_Hudson_p55405_econ`), not the legacy `gas_cc_<bin>_<zone>` representative form,
and CAMPD per-plant tranches never re-mint (`is_campd_bin` passthrough, the G-28 fix). D88's census
over 496 committed ledgers likewise found no collision in any NYISO bundle. **This is a NYISO-scoped
result and transfers to no other ISO (rule 25 `[R-ISO-SCOPE]`); D88's guard remains owed** — it
fires at `generators_to_fleet_arrays` on every future run and on collision sources a ledger cannot
record, which a post-hoc census cannot replace. Reported to D88
(`claude/capx-d88-fleet-id-uniqueness-x31hi6`) with these ledgers.

**A real observation the census surfaced:** the arm and control retrofit **different tranches of the
same plants** (`_committed` vs `_econ`), because a uniform +$47.50/MWh enters every candidate's
uplift and re-ranks the payback ordering. The PRECOMMIT predicted this ("the identity of retrofitted
units may change").

---

## 5. THE PRE-SOLVE BRACKET PREDICTION MISSED — AND THAT IS THE FINDING'S REAL RESULT

Before the arm ran (scratch note `d87-presolve-prediction.md`, written while both solves were still
in 2026) I predicted from the committed premium ladder that the arm's 2030 cumulative would land in
**(7,731.7, 7,890.3) MW** — between `CES-P20`'s $19.00 and `CES-P60`'s $57.00, since the arm's
`attr_post` of $47.50 sits between them.

**It landed at 7,383.569 MW — BELOW the bracket.** The arm's own ledger says why, and it is not a
defect:

| year | the row's state | the dual the NEXT year's screen reads | arm `attr_post` |
|---|---|---|---|
| 2027 | short by 19.0 pts → **escapes at the ACP** | $50.00 | 2028: 47.50 |
| 2028 | short by 8.4 pts → **escapes at the ACP** | $50.00 | 2029: 47.50 |
| 2029 | **binds exactly at target** (gap ±0.000000) | **$7.5636** | 2030: **7.185** |

**A federal CES target row is NOT a constant premium.** Its dual is the LP's own marginal cost of
the last credit: while the standard cannot be met the ACP escape caps it at $50, and **the moment
the standard starts binding the dual collapses to the marginal abatement cost** — here $7.56/MWh, an
85 % fall in one year. A premium is exogenous and constant; a target row's price is endogenous and
self-extinguishing. My bracket assumed the former and was wrong for exactly that reason.

**This changes what SCN should carry.** The NYISO shard's `federal_ces_target` cell concludes *"a
target case and a premium case are NOT the same instrument at different levels"*. **That conclusion
SURVIVES — but its stated reason does not.** Before this repair it rested on a wiring defect (the
retrofit screen could not see the row at all). After it, the claim is true for a real and much more
interesting reason: the two instruments differ in the **time path of the attribute price**, because
one is capped-and-constant and the other is endogenous and collapses at the binding point. The
screen's own numbers show both regimes in a single five-year run.

---

## 6. REPORTED AT FULL MAGNITUDE — the CO2 line does NOT move monotonically

No gate is on CO2, and a screen is never read against a residual. Reported because it would be
misleading to lead with "+1.1 GW of capture" and omit it:

| year | in-ISO CO2 control (Mt) | arm (Mt) | Δ |
|---:|---:|---:|---:|
| 2028 | 17.1342 | 17.2520 | **+0.1178** |
| 2029 | 11.3278 | 11.2938 | −0.0340 |
| 2030 | 9.2995 | 9.3323 | **+0.0328** |

**The mechanism, from the generation decomposition:** the arm displaces **imports** (−0.051 TWh in
2028, −0.159 TWh in 2030) with in-ISO generation, and **the LP holds import emission rates at ZERO
by design** — the campaign's own standing leakage disclosure (`REF`'s import line runs 44 % of
in-ISO CO2 at 2026 rising to 101.6 % at 2030). Displacing a zero-rated import with in-ISO gas raises
the in-ISO line whatever the true emissions do. The retrofit heat-rate penalty (+12 %) works the
same way.

A second observation, stated rather than explained away: at 2030 the arm holds **+1,127.6 MW** more
`gas_cc_ccs` capacity but generates **exactly the same** `gas_cc_ccs` energy (43.6988 TWh in both).
The consistent reading is that by 2030 the arm is converting the **marginal, low-CF hosts** the
control never reached — the best hosts having converted in 2028-2029 under the payback ordering —
so the extra MW are capacity, not energy. That reading is not independently verified at unit grain
here and is **routed, not asserted**.

---

## 7. ROUTED TO THE SCN DESK — re-statement, not performed here

The charter is explicit: **route, do not re-state.** The six ISO policy FINDINGs and the Stage C
memo (`FINDING-scenario-campaign-2026-09-07.md` §5) quote `CES-T80` / `ALL-CLEAN` numbers computed
on the defective screen, and **all twelve target-row bundles are cache-epoch-invalidated**
(`results/cache.py`, Epoch 2026-09-08 — a same-key invalidation, so a stale bundle will be SERVED to
a post-fix run unless purged). What SCN owes:

1. Purge or re-solve the twelve legs before re-quoting any `CES-T80` / `ALL-CLEAN` number. Their
   per-year duals and each leg's cap-bounded correction are tabulated in PRECOMMIT §2.5.
2. **Keep** the "not one instrument at two levels" conclusion and **replace its reason** with §5's.
3. Re-check pre-registered prediction **P-9** (*"CES-T80 gives the largest deployment response"*),
   recorded as MISSED on exactly this seam.

**Two corrections to the D87/D88 READ**, so the next reader is not misled:

- **"The measured 0.0 MW in every year of every `CES-T80` leg" reads as an absolute zero and is
  not one.** Traced to its source — the NYISO shard's `federal_ces_target` cell — the claim is that
  the row moves the retrofit ledger **BY** 0.0 MW, i.e. Δ against `REF`. The absolute set is
  2,984.4 / 5,255.9 / 6,255.9 MW cumulative, driven by §45Q and fuel economics. The distinction
  matters: the defect's magnitude is the **difference from the premium legs**, not the whole set.
- **"NYISO is the one ISO with headroom" is incomplete.** 2030 cap headroom under `CES-T80`: MISO
  3.000 GW and PJM 3.000 GW (neither retrofits at all that year), NYISO 2.000, NEISO 1.214, CAISO
  0.108, ERCOT 0.002. The screen year is unchanged — 2030 is where this mechanism's footprint is
  largest **for the screened ISO**, and re-choosing the venue on expected effect is the selection
  rule 1 `[R-STRUCT]` forbids.

---

## 8. A PRE-EXISTING RED ON `main`, REPORTED AGAINST INTEREST

`tests/unit/model/test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none` **fails on
`origin/main`**, verified in a clean unmodified worktree at `cbf9be9f`. It asserts
`get_rps_target("SPP", 2030) is None` on the stale premise *"SPP is not modeled"*; SPP now carries
a registered RPS floor and it returns `0.0`. **Not this lane's**, not fixed here, routed to the SPP
desk.

---

## 9. WHAT THIS LANE DID NOT DO

- Did not touch `ccs.py`'s conversion block (`:590-591`), `arrays.py:3651`, or `evolve.py`'s
  `_retrofitted_ids` / exempt-set lines — **capx D88** owns those. Its branch appeared on origin
  during this session and had not merged; gate **G7** was pre-registered as the substitute for its
  guard (ADDENDUM §3), under an explicit owner ruling to proceed.
- Did not touch the evolution-ledger adequacy-block writer (**D83**).
- Did not re-solve the other eleven invalidated bundles, re-state any ISO FINDING's numbers, or
  register anything on a dashboard (a screen bundle is never registered — rule 29 `[R-SCREEN]`).
- Did not touch D77's routed parasitic-uplift item, the level of `ccs_retrofit_vom_adder`, or
  anything under `_AGGREGATABLE_FUELS`.

## 10. RULE 31 `[R-RETAIN]` — THE BUNDLES, AND THE PROMOTION QUESTION

`results/capx-d87-screen/**` and both `results/NYISO/eb1b0e1df942db47/` trees are **gitignored, not
deleted** — which discharges rule 29 `[R-SCREEN]`(c) in full, because the parity gate only ever sees
committed directories. **Nothing has been removed from disk.**

**This container is ephemeral: the two solved bundles (≈137 min of LP) will not survive the
session.** The promotion question is therefore asked explicitly here rather than left implicit —
see the session's closing report.
