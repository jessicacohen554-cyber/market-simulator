# FINDING — capx D83 **VERIFICATION ADDENDUM**: the (i) verdict holds, and the lane was already discharged

**Lane:** capx D83 re-emission, under owner ruling **Q60**. Branch
`claude/capx-d83-adequacy-diagnosis-5wqbwp`. **DATA PROFILE: pjm.** MODEL: Opus.

**This is an addendum, not a second finding.** `FINDING-capx-d83-2026-09-07.md` is the diagnosis and
stays the record; nothing in it is restated here. This document carries only what re-verification at
a later HEAD adds, and one status correction the re-emitted charter could not have known.

---

## 0. The two headlines

**(1) The charter's premise is stale — D83 was dispatched and has landed.** The re-emitted charter
states the lane was "NEVER DISPATCHED (no branch, no commit, no document, confirmed on a second
fetch)." That was true at the director's fetch and is no longer true. The work exists under a
**different branch name than the charter anticipated**, which is why the fetch missed it:

| | |
|---|---|
| branch | `claude/capx-evolution-2022-adequacy-hghzvv` (charter anticipated `claude/capx-d83-evolution-2022-adequacy`) |
| commit | `815a0066` — 2026-09-08 05:49:18 UTC |
| merged by | PR [#5641](https://github.com/jessicacohen554-cyber/market-simulator/pull/5641), merge commit `32f83c2f` |
| in my HEAD | yes — `d1b8d1bf` == `origin/main`, 0 ahead / 0 behind |

So no diagnosis was re-run and no repair re-written. What this lane did instead is **verify the
landed result independently**, at a HEAD five merges later than the one it was produced on.

**(2) The verdict is (i) — a RECORDING defect — and it survives independent verification.** More
than that: the corpus-wide test below is a **stronger** affirmative proof than the original, which
established (i) on one reproduced bundle. **No counterexample exists anywhere in the committed
corpus.**

---

## 1. Verification results

| # | claim in the 09-07 finding | how I re-tested it | result |
|---|---|---|---|
| 1 | the named line — `runner.py:2554` `if is_bridge:`, gated by `HINDCAST_BRIDGE_YEARS` at `:237` | read the ordering at HEAD | **holds** — `is_bridge` at `:1988` → D76 predicate `:2110` → screen `:2213` → bridge writer `:2554` |
| 2 | the screen runs above the branch and consumes the pools | read `runner.py:2213–2233` | **holds** — unconditional; `wind_cap_mw` / `solar_cap_mw` / `storage_firm_mw` threaded into `accredited_firm_capacity_mw` |
| 3 | 72 committed bridge-year ledgers, 46 carry / 26 missing, missing ⟺ `bridge=True` | recomputed from `git ls-tree` over HEAD | **exact** — 26/26 missing are bridge; 0/46 carriers are bridge; identical missing field-set in all 26 |
| 4 | by ISO: PJM 11, MISO 7, NEISO 3, NYISO 3, CAISO 1, ERCOT 1 | same | **reproduced digit-for-digit** |
| 5 | the recurrence guard has teeth | ran it against `815a0066^`'s runner, then HEAD's | **3 failed / 1 passed → 4 passed**, as claimed |
| 6 | zero key moves | ran the census myself, pre-repair vs HEAD, in one environment | **byte-identical over 230 payloads** |

`src/market_sim/runner.py` was restored byte-identically after each swap
(`md5 c4d188db4502a36be5899c67d653ed1a`), and the working tree is clean.

---

## 2. What this adds — the (i) proof, generalized from one bundle to the whole corpus

The charter names the (i) direction as **the expensive error**: repairing a writer that was
faithfully recording a real absence would paper over a substantive defect. The 09-07 finding proved
the operand existed at screen time on **one** reproduced PJM bundle (§2.2). That is a sound proof
about that bundle. It is not, on its own, a proof about the other 25.

So I asked the same question of all 26 — **does the bridge year's own ledger record a non-`None`
screen operand?** The capx D52 `screen_ledger_fields` block is what carries that evidence, and the
answer partitions perfectly:

| | ledgers | `screen_entering_firm_mw` | reading |
|---|---:|---|---|
| D52 key **PRESENT** | **10** | **non-`None` in 10/10** | screen ran **with the pools inside it** |
| D52 key **ABSENT** | **16** | n/a — no D52 block at all | silent, and the silence is uninformative (below) |
| D52 key present **but `None`** | **0** | — | **this is the (ii) signature, and it does not occur** |

The middle row is the load-bearing one. `screen_entering_firm_mw` is `None` exactly when the guard
`fleet is not None and prior_results is not None and peak_demand > 0.0` fails — i.e. when the
accreditation call genuinely did not run. **That case appears zero times in 26 ledgers.**

The 10 that carry affirmative evidence span **three ISOs** — PJM 7, MISO 2, NYISO 1 — not one:

```
PJM   a9c66d8e fb16fda2 b9fa47de f0e050e8 b98060898 81ad0918 bb6a6023   firm 185264.2 / 130958.8-class reqs, position 1.13-1.26
MISO  6ea92547 c306ddc6                                                 firm 130958.8 / 125424.9,  position 1.137 / 1.089
NYISO 911371a8                                                          firm  36163.6,             position 1.055
```

**And the 16 silent ones are a pre-D52 bundle vintage, not a bridge-specific gap.** Decisive test:
in every one of the 16, the bundle's own **solved** years lack the D52 block too — **0 of 4 solved
siblings carry it, in 16 of 16 bundles**. A bundle that never recorded the block anywhere cannot be
evidence that a bridge year failed to compute it.

> **Verdict: (i), affirmatively, corpus-wide.** The operand existed, was consumed, and drove
> decisions; the writer stayed silent. There is no bundle in the repository whose 2022 capacity
> screen ran on a different basis than its neighbours, so the (ii) escalation is **not** owed.

---

## 3. Zero key moves — re-measured at a later HEAD, and one delta explained

My own before/after census, both legs run in **one environment** (the only valid differencing):

```
pre-repair runner  ->  230 payloads hashed, 123 reproduced, 107 mismatch, 0 unbuildable
HEAD runner        ->  230 payloads hashed, 123 reproduced, 107 mismatch, 0 unbuildable
diff               ->  IDENTICAL   ==>  ZERO KEY MOVES
```

**One thing to state rather than leave for a later reader to trip over:** my HEAD census is *not*
byte-identical to the committed `docs/handoffs/d83/key-census-after.json`. **18 keys differ, and
none of them is D83's.** All 18 are `results/calibration/*` payloads, and the cause is a lane that
landed *after* D83:

- `203c031e` (**spp-49**) changed `config/constants.py`, `config/scenarios.py` and
  `config/solve_surface_declared.py` — three of the seven `SURFACE_MODULES`.
- That is the capx **D79 solve-surface fingerprint re-keying by design**, with the declaration
  updated in the same commit (`solve_surface_declared.py`, +2 lines), which is the correct discipline.
- No `results/calibration/**/run_config.json` changed between `815a0066` and HEAD, so the payloads
  are identical and the move is entirely the fingerprint's.

The committed census remains valid as the record of what D83 did. The 18-key delta is spp-49's, is
already declared, and is **not this lane's to act on** — recorded here only so the next reader who
re-runs the probe is not surprised by it.

---

## 4. Still open, still routed, still not mine — and now confirmed live at HEAD

The 09-07 finding's §7 routed one item to the owner. **It is unaddressed at `d1b8d1bf`**, and I
re-verified it rather than assuming:

**A bridge year reads that year's measured data, while the code says it does not.**

```
runner.py:249  (docstring, THE single definition of a bridge year)
    "the fleet evolves across it, but its LP is never solved and its measured data never read"

runner.py:2110-2113  (capx D76 predicate, default ON since owner ruling Q58)
    if (config.capacity_screen_peak_measured_hindcast
        and config.hindcast
        and not config.is_crossover_forward_year(year)):        # <-- no `is_bridge` term
            screen_measured_demand = _hindcast_measured_demand(...)
```

`is_bridge` is computed at `:1988`, **122 lines above** the predicate that ignores it. The operand it
changes is decision-bearing — the seam peak feeds the reliability floor, the entry screen and the
reserve-margin backstop — and the 09-07 reproduction measured the gap at **~13.4 GW** for PJM 2022
(148,528.0 MW armed vs 135,090.6 MW in the pre-D76 bundle).

This is **not a rule-22 breach** — rule 22 gates the *spend* (solve / score / register), and a bridge
year is none of those. What is certain is narrower and still worth a decision: **an invariant the
code states in terms is false.** The two candidate resolutions the prior lane named are unchanged —
add `not is_bridge` to the D76 predicate (a mechanism change, owner's call), or correct the docstring
and banner to state what a bridge year actually reads (a record change). D76 is armed and owner-ruled
(Q58); **neither charter authorizes touching it**, so it stays routed.

---

## 5. Boundaries, and what this lane changed

**Code changed: none.** No mechanism, no arm, no default, no registration, no re-solve — and none was
needed, because the repair had already landed and verified clean. The only new file is this document.

Boundary respected in full: `ccs.py`, `arrays.py:3651`, `evolve.py`'s `_retrofitted_ids` / exempt-set
lines, `ccs.py:475-476`, `evolve.py:664`, `test_d62_published_going_forward_bar.py` and
`test_d74_no_default_cap_convention.py` are **untouched** — the verification never reached them.

**G-DRIFT:** the charter's correction is right and I confirmed it independently —
`git cat-file -t 457ae04` → `fatal: Not a valid object name`, so the PJM keeper's recorded sha is
dead to the 2026-08-16 rewrite. Drift between the D83 commit and my HEAD is **6 source files**, named
in §3; three are solve-surface modules and account for the 18-key delta. None touches the bridge
writer, which is byte-identical at both revisions.

**Rule 31 `[R-RETAIN]`:** **this lane solved nothing — there is no bundle on local disk and no
promotion question outstanding.** Every result above is from committed artifacts, source reading, and
two zero-LP instruments (the AST parity test and the key census). Nothing is awaiting a decision from
this lane; the only decision outstanding on the D83 object is §4's, which belongs to the owner and was
already routed on 2026-09-07.
