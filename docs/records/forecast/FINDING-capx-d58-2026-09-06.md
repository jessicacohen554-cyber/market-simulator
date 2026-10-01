# FINDING — capx D58: the sector gate on PJM — the DISCRIMINATING claim is CONFIRMED (sector 1 is 11.7 % of PJM's failing pool against MISO's 76.8 %), the partition is exact to the row, and the rule-29 SCREEN KILLED THE ARM on a SECOND SEAM D53 did not build for: on a clearing-armed ISO a gated unit stops offering into the capacity auction, 34.2 GW moves to $0 price-taker supply, PJM's clearing price falls 9.67 %, and the gate INCREASES economic exits instead of reducing them

**Lane:** capx D58 — the PJM leg of D53's retirement-screen sector gate, the discriminating test
D53 §7 item 1 named. Pre-declared in `PREDECL-capx-d58-2026-09-06.md`, **pushed before any LP**
(`cdea18cd`); instruments pushed before the solves (`99c75b3d`).
**Branch:** `claude/capx-d58-pjm-sectorgate-v0b9fa`, off `origin/main` `6887484f`.
**Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.

**NOTHING ARMS. NO MECHANISM CODE WAS WRITTEN.** No keeper, no marker, no default flip, no
parameter value, no `src/` edit. PJM's matrix cell moves `U` → **`O`** on PJM's own measured
evidence (rule 25 — MISO's `K` never filled it). The full span was **never spent** and the two
screen bundles are **deleted before merge** (rule 29(c)).

---

## 0. Verdict (one paragraph)

**The partition is exactly what D53 says it is, the discriminating claim is confirmed, and the
arm is nonetheless killed by the screen — on a seam, not on a residual.** On the same-HEAD
control the 2022 screen fails 677 rows / 29,727.9 MW of which **3,476.5 MW (11.70 %) is sector 1**;
the arm removes **226 rows / 3,476.5 MW, every one of them sector-1 and nothing else**, and the
451 rows both arms share carry **identical MW to the decimal (26,251.4)**. That is the
discriminating result the charter asked for: PJM's failing pool is **11.7 % utility-owned where
MISO's is 76.8 %**, on a fleet that is 23.8 % sector-1 where MISO's is 80.2 %, and a real coal
exit cohort that is 10 % utility-owned where MISO's is 88 % — the gate behaves as an ownership
attribute should, removing a MINORITY here and a supermajority there. **But the arm's failing
pool does not shrink by 3,476.5 MW; it shrinks by 566.3.** The missing 2,910.2 MW is 41 *merchant*
rows that fail in the arm and not in the control, and the cause is proven at the line: PJM's
capacity-supply clearing (D57, armed for PJM) builds its sell-offer stack by iterating the
retirement screen's own `margins` list (`retirements.py:2856`), which the `exempt_unit_ids` filter
empties (`:3199`), and `price_takers_mw` is computed as the residual `accredited_total_mw −
offered_mw` (`:2872`). **So a sector-gated unit stops submitting a net-ACR sell offer and becomes
$0 price-taker supply**: 34,172.4 MW moves out of the stack, `n_offers` 1,370 → 1,000, and PJM's
2022 clearing price falls **67.76 → 61.21 $/MW-day (−9.67 %)**, which pushes marginal merchant
units below the bar. The consequence is a **sign inversion of the mechanism's own logic**: a gate
can only remove screen candidates and so can only reduce economic exits, which is what
PREDECL §3 P5 declared before the solve — yet 2022 economic exits rise **7,333.7 → 7,790.9 MW
(+457.2)** and 2023's **3,105.5 → 3,310.9 (+205.4)**. This is a second seam that D53's design
§1.8 explicitly claimed the gate does not touch, and D53 was right *for MISO*, which arms no
capacity clearing — the seam exists only where D57 is armed, i.e. on PJM alone today. Per the
charter (*"if PJM needs a seam D53 did not build, STOP and route — do not extend the gate in this
lane"*) and PREDECL §7(a)/K-c, the recommendation is **HOLD-and-route, not DECLINE**: the
partition's fidelity limb (b) is MET and the composition question is simply not answerable while
limb (a) fails. Rule 29's screen did its job — it killed the arm for **~22 minutes of LP instead
of the ~30 the full span would have cost**, and the kill is the session's result.

---

## 1. What was solved

| leg | out-dir | key (pre-declared → realized) | wall | order |
|---|---|---|---:|---|
| screen **control** (same-HEAD) | `pjm-2021-2023-realized-t1h-d58-screen-control` | `e47fee08f5f37d6f` → **match** | 11.3 min | first, solo |
| screen **arm** (`--retirement-sector-gate`) | `pjm-2021-2023-realized-t1h-d58-screen-arm` | `0265ce2b262ad37f` → **match** | 10.7 min | after, solo |

Both: `--iso PJM --start-year 2021 --end-year 2023 --vintage 2020 --fuel-variant realized
--entry-screen-diagnostics`. Solve years **{2021, 2023}**, 2022 **bridged**, asserted by the run
banner; the holdout freeze asserted active and unspent; no out-of-training year solved, scored or
registered. Sequential, PJM solo (rule 12). **HEAD guard held across both solves**
(`99c75b3d…`, unchanged, checked after each). `data/clean` was absent at session start and was
rebuilt in full (`regenerate_clean.py`, 56 datatypes, exit 0, zero failures) so both legs solved
on one input surface. **K-a did not fire:** both keys realized exactly as pre-declared, no
collision.

**The full span was never spent** — rule 29 clause (2). The screen bundles are throwaway probes:
never registered, never a keeper, deleted before merge (§7).

---

## 2. The discriminating result — CONFIRMED

### 2.1 The partition is exact to the row (2022 screen, control vs arm)

| set | rows | MW | sectors |
|---|---:|---:|---|
| only in **control** (what the gate removed) | 226 | **3,476.5** | **sector 1 ×226 — nothing else** |
| in **both** | 451 | ctl **26,251.4** = arm **26,251.4** | unchanged to the decimal |
| only in **arm** (the second seam, §3) | 41 | 2,910.2 | 2 ×24 · 3 ×9 · 5 ×5 · 7 ×2 · 4 ×1 — **zero sector-1** |

The gate removed **every** sector-1 row and **only** sector-1 rows, and left the shared rows'
screen economics untouched. Zero sector-1 rows and zero unknown-sector rows survive anywhere in
the arm (2021–2023). The `sector_gated` ledger block reads **384 units / 41,221.6 GW** in 2022 —
inside the pre-declared 36–46 GW — with **zero** unknown-sector fail-open MW.

### 2.2 The minority claim, in the numbers it was declared in

| quantity | MISO (D53) | **PJM (measured here)** | pre-declared |
|---|---:|---:|---|
| thermal fleet, sector-1 share | 80.2 % | **23.8 %** | 23.8 % (census) |
| 2022 failing pool, sector-1 share | **76.8 %** | **11.70 %** | 12.88 %, band 11–15 % — **HIT** |
| 2023 failing pool, sector-1 share | 76.6 % | **10.74 %** | 14.20 % — near-miss, see §5 |
| real coal exits, sector-1 share | 0.88 | **0.102** | 0.102 (census) |

**PJM's screen fails a minority of utility capacity where MISO's fails a supermajority**, which
is the behaviour an ownership attribute should have and the question this leg existed to answer.
It is answered, and it is answered on PJM's own record.

---

## 3. Why the screen killed the arm — the second seam, proven at the line

### 3.1 The mechanism

`clear_capacity_supply_stack`'s offer list is built from the retirement screen's candidate set:

```
retirements.py:2856   for g, eas, gfc in margins:      # the screen's own candidate list
retirements.py:2861       offer = max(0.0, gfc - eas) / (a_mw * 365.0)
retirements.py:2871   offered_mw     = sum(o[3] for o in offers)
retirements.py:2872   price_takers_mw = max(0.0, accredited_total_mw - offered_mw)   # a RESIDUAL
retirements.py:3199   if g.unit_id in exempt_unit_ids:  continue    # what fills `margins`
```

A sector-gated unit never enters `margins`, so it never enters `offers`, so its accredited MW
falls automatically into `price_takers_mw` — **$0 supply that always clears**. The gate was
designed as a partition of *who faces an exit decision*; on a clearing-armed ISO it is also,
silently, a partition of *who submits a capacity sell offer*.

### 3.2 The magnitude

| | 2022 ctl → arm | 2023 ctl → arm |
|---|---|---|
| `n_offers` | 1,370 → **1,000** (−370) | 907 → **659** (−248) |
| `offered_mw` | 150,857.2 → **116,684.8** (**−34,172.4**) | 138,942.4 → **104,697.8** (−34,244.6) |
| `price_takers_mw` | 30,577.9 → **64,750.2** (**+34,172.4**) | 36,375.1 → **70,194.6** (+33,819.4) |
| `price_usd_per_mw_day` | 67.760 → **61.207** (**−9.67 %**) | 67.760 → 67.760 (**0.00 %**) |
| `price_per_firm_mw_yr` | 24,732.5 → 22,340.4 (−2,392.0) | unchanged |
| `requirement_mw` / `census_mw` | **identical** | identical / −425.2 |

**The seam is present in both years; its price consequence is not.** 34.2 GW moves in each, but
2023 sits on a flat segment of the VRR curve and the price does not move. Reading the seam off
2023 alone would have missed it entirely — which is one more reason the unit-level diff, not a
headline comparison, is what caught it.

### 3.3 The consequence: the mechanism's own sign inverts

PREDECL §3 P5, written before the solve: *"A gate can only REDUCE the set of units the economic
screen may retire. It removes candidates; it never adds one. So economic exits can only fall or
stay."* Measured:

| screen year | control economic exits | **arm** | Δ |
|---|---:|---:|---:|
| 2022 | 7,333.7 MW | **7,790.9** | **+457.2** |
| 2023 | 3,105.5 MW | **3,310.9** | **+205.4** |

The gate **increases** economic exits, because the capacity price it depresses pushes marginal
merchant units below the bar faster than removing utility candidates removes exits. That is not a
band reading and it is not a rule-14 matter: it is the mechanism doing the arithmetic opposite of
what its own definition permits, which is only possible through a seam outside the definition.

---

## 4. The screen gate (PREDECL §4), graded

| gate | condition | reading |
|---|---|---|
| **S1** | zero sector-1 rows and zero unknown-sector rows in 2021–2023 | **PASS** — 0 and 0 |
| **S2** | 2022 failing pool falls 5–30 % | **FAIL** — falls 1.91 % (the seam backfills 2,910.2 MW; see §5 on the band's calibration) |
| **S3** | 2023 failing pool falls 5–30 % | **FAIL** — **rises** 19.07 % |
| **S3b** | 2023 admitted drops 400–850 MW, capped stays 0 | **FAIL** — admitted **rises** 205.4 MW; capped 3,589.3, not 0 |
| **S4** | 2022 admitted ≥ 10,500 MW (the cap re-fills) | **PASS** — 12,635.5 |
| **S5** | no non-target footprint row moves | **FAIL** — `capacity_clearing` differs in both years |

**ALL_PASS = False → the arm is killed and the remaining years are never spent** (rule 29).

**S5 initially read PASS, and that was my instrument's defect, not the arm's.** `FOOTPRINT_KEYS`
in `ab_compare.py` omitted `capacity_clearing`, so the check that exists precisely to catch a
second seam did not look at the ledger block the second seam lives in. The unit-level set diff
(§2.1) is what surfaced it. The key has been added and the gate re-run (it now fails as it
should); the omission is graded as a miss in §5 and `capacity_clearing` is flagged in the source
as **the first key any future sector-gate leg on a clearing-armed ISO must read**.

---

## 5. The pre-declaration, graded at full magnitude

| # | prediction | outcome |
|---|---|---|
| **census** | PJM fleet 23.8 % sector-1; failing pool 12.88 % (2022) / 14.20 % (2023); cohort coal 0.102 | **HIT on the fleet and the cohort** (read from the same committed source). Failing-pool share measured **11.70 % / 10.74 %** at HEAD vs 12.88 / 14.20 from the pre-hunk bundle — **2022 inside the declared 11–15 % band, 2023 below it** |
| **P1** minority claim: pool falls 11–15 % (2022), 11–17 % (2023) | **MISS as a NET-SHRINKAGE band; HIT as the ownership claim.** The *gated* fraction is 11.70 % (2022), inside the band — but the *net* pool falls 1.91 % (2022) and **rises** 19.07 % (2023) because of the seam. Falsifier "fall > 30 % or < 5 %" **FIRED** |
| **P1** zero sector-1 rows; zero unknown-sector rows | **HIT** — 0 and 0 |
| **P1** gated set 36–46 GW in 2022 | **HIT** — 41,221.6 GW / 384 units |
| **P2** 2022 admitted 11.5–14.5 GW, all non-sector-1 | **HIT** — 12,635.5 GW, zero sector-1 |
| **P2** 2023 admitted 3,650–3,900, capped stays 0 | **MISS** — 3,310.9 and capped 3,589.3 |
| **P3** composition / release precision | **NOT ADJUDICABLE** — the screen span carries no `score.json`, and limb (a) fails, so composition is not the question any more |
| **P4** footprint identical | **MISS** — `capacity_clearing` moves in both years. This is the finding |
| **P5** rule-14 sign line: exits can only fall | **MISS, and the most informative one** — exits **rise** +457.2 / +205.4 MW (§3.3) |
| **keys** both realized as declared, no collision | **HIT** — `e47fee08f5f37d6f`, `0265ce2b262ad37f` |
| **G-DRIFT** form 4 void; #5033 INERT | **HIT** — the HEAD control key ≠ the committed `f0e050e820c1159a`, confirming the void independently of the SCN-LOAD hunk itself |
| **instrumentation** | **MISS (mine)** — `FOOTPRINT_KEYS` omitted `capacity_clearing`, so S5 read PASS on a run whose second seam was moving 34.2 GW (§4) |

**Tally: 6 hits, 5 misses, 1 not adjudicable.** Two of the misses are the finding (P4, P5); one is
my own instrument (S5's key list); two are bands (P1 net-shrinkage, P2 2023) whose calibration
problem is stated next.

**Why the bands were mis-calibrated, disclosed rather than explained away.** The PREDECL's bands
were derived from the census of the **committed D57 arm A bundle** — the only PJM ledger that
existed — and PREDECL §6 had already established that this bundle is **pre-hunk** on SCN-LOAD
`d14a7ed0` and therefore that form 4 is void. The same-HEAD control confirms the drift is large:
its 2022 failing pool is **29,727.9 MW against the committed bundle's 20,788.5**, and its 2023
screen carries 2,689.7 MW of capped rows where the committed bundle had none. So the bands were
built on a surface I had already declared unfit for differencing. **The honest reading is that
the census was right about ownership shares — which is what it was for and which is what the
control confirms (11.70 % vs 12.88 %) — and wrong about MW levels, which it was never entitled
to predict.** A future leg should band shares, not levels, whenever its census predates its
control.

---

## 6. Routed to the director — the seam, stated as a question, not a patch

**No code was written and none is proposed here** (charter; rule 29). The seam needs an owner
decision because both readings are defensible and they differ in market fact:

1. **The seam is a defect.** PJM's Reliability Pricing Model has a **must-offer requirement** for
   existing generation capacity: a rate-based unit is not exempt from offering into the BRA — it
   offers at a cost-based (net-ACR) price, but it *is* in the supply stack. Modelling 34.2 GW of
   it as $0 price-taker supply misstates PJM's actual supply curve and depresses the clearing
   price 9.67 %, and D66/D57 already measure this model's clearing price against PJM's published
   BRA record. On this reading the fix is to decouple the **offer stack** from the **screen
   candidate set** — a gated unit still offers, it just does not face an exit decision — which is
   a change to `retirements.py`'s clearing path, not to the gate.
2. **The seam is correct as built.** If a unit's exit is not a merchant decision, arguably its
   *offer* is not a merchant offer either, and a cost-based must-offer unit is closer to a price
   taker than to an economic withholder.

**Reading 1 is the one this lane would argue**, on the ground that the must-offer requirement is a
published PJM market rule and rule 14 `[R-ACCURATE]` prefers the measured market design; but the
charter forbids this lane from building it, and it is a D53-family design question with its own
census and its own A/B. **Named, not built.**

Also routed:

3. **The seam is not PJM-specific in the code — it is clearing-specific.** `capacity_market_supply_clearing_by_iso`
   is armed for PJM alone today, so PJM is the only ISO where the sector gate reaches it. Any
   future ISO that arms D57 inherits this interaction, and **D53's design §1.8 claim that the
   gate "touches no second seam" should be amended to say "on an ISO with no capacity-supply
   clearing armed"** — it was true for MISO and is not true in general.
4. **The dated-plant exemption rides the same seam.** `dated_plant_unit_ids` unions into the same
   `exempt_unit_ids`, so dated plants have always been dropped from the offer stack too. The
   control already carries 30,577.9 MW of price takers. This is pre-existing behaviour that the
   sector gate does not introduce but amplifies by ~1.1× the entire pre-existing price-taker pool;
   whichever way the owner decides item 1, it applies to both declarations.
5. **A band-calibration process note** (§5): a census taken from a bundle already declared unfit
   for differencing may band *shares*, never *levels*.

---

## 7. Matrix (rule 28) and bundle retention (rule 29(c))

- PJM's `retirement_sector_gate` cell moves **`U` → `O`** (measured, not adjudicated — the owner
  decides on §6) with this finding cited, in **PJM's shard only**. MISO's `K` did not fill it and
  no other shard is touched (rule 25).
- PJM's `economic_retirement_screen` cell gains the D58 evidence.
- **Both screen bundles are deleted from `results/hindcast/` before this PR merges.** Every number
  this lane will ever cite is in this document and in the committed instruments
  (`docs/handoffs/d58/census_probe.json`, `keys_probe.json`, `screen_compare.json`); git history is
  the record for the bytes (rule 15's delete-not-archive discipline, rule 29(c)).
- **Nothing is registered on either dashboard.** Rule 29 clause (2) forbids registering a screen
  bundle, and the full span — the only thing that would have been registered — was never solved.
  This is a stated deviation from the charter's EXIT line ("the suffixed arm registered"), which
  presumed the screen would clear; rule 29 governs when it does not.

---

## 8. Governance attestation

**Rule 1 `[R-STRUCT]`:** the arm is killed on a structural seam — the mechanism's own arithmetic
inverting — and on nothing about a residual; no gate reads a band, and the kill would stand
whichever way `retire.total_gw` had moved. **Rule 12 `[R-PARALLEL]`:** PJM solo, the two legs
sequential, years sequential within each. **Rule 13 `[R-MEASURED]`:** `Sector` is an owner
attribute read at the run's active vintage; the real cohort measured the partition's consequence
and identified nothing. **Rule 14 `[R-ACCURATE]`:** the sign line was stated before the solve, in
both directions, and its violation is reported as the finding rather than absorbed. **Rule 19
`[R-ONE-MECH]`:** the seam of §3 is precisely a one-mechanism violation discovered — one filter
(`exempt_unit_ids`) is doing two jobs (exit candidacy and capacity offering) — and it is routed,
not reconciled in this lane. **Rule 21 `[R-DOF]`:** zero free parameters; a partition on one
published boolean. **Rule 22 `[R-HOLDOUT]`:** solve years {2021, 2023}, 2022 bridged and never
scored, nothing outside the training window solved, scored or registered; the freeze asserted by
both run banners. **Rule 24 `[R-REGISTRY]`:** the existing gated field and its harness flag; no
env knob, no literal, no dict. **Rule 25 `[R-ISO-SCOPE]`:** PJM's cell carries PJM's own measured
letter; no verdict crossed an ISO boundary in either direction. **Rule 27 `[R-PUSH]`:** no
≥300-line source file was rewritten from response content; no `src/` file was edited at all.
**Rule 28d `[R-MECH-MATRIX]`:** only PJM's shard is edited. **Rule 29 `[R-SCREEN]`:** phase 0 was
zero-LP; the screen year was named from the mechanism's own footprint before the screen ran; the
gate was structural and STOP-only; the arm was killed and the remaining years were never spent;
both bundles are deleted before merge. **No mechanism code, no keeper, no marker, no default flip,
no parameter value.**

## 9. Reproduction

```
uv run python scripts/regenerate_clean.py
bash docs/handoffs/d58/run_screen.sh          # both legs, HEAD-guarded, ~22 min
uv run python docs/handoffs/d58/ab_compare.py \
    results/hindcast/pjm-2021-2023-realized-t1h-d58-screen-control \
    results/hindcast/pjm-2021-2023-realized-t1h-d58-screen-arm \
    docs/handoffs/d58/screen_compare.json
uv run python docs/handoffs/d58/census_probe.py    # the pre-solve census
uv run python docs/handoffs/d58/keys_probe.py      # the keys, at HEAD
```
