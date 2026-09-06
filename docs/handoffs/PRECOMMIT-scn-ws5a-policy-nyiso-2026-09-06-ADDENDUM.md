# ADDENDUM to PRECOMMIT — SCN-WS5A-POLICY-NYISO: the slot, the fan-out, and a budget correction

**Pushed BEFORE the first LP.** Rule 29 `[R-SCREEN]` forbids revising a PRECOMMIT after a
solve; nothing has solved. The eleven legs dispatched at 22:26 UTC each aborted in **≈2
seconds** at fleet build, before any LP was constructed, on the missing `data/clean`
prerequisite (§1) — so **zero solve-years have been spent** and the parent PRECOMMIT stands
unrevised. **No gate, no prediction, no level, no case verdict and no cache key in the parent
document is changed by this addendum.** It records three things that happened after it was
pushed: an owner decision on two open items, a measured budget correction, and a change to
*where* the legs run.

---

## 1. A budget item the parent PRECOMMIT missed, measured

`§8`'s budget said "≈3.5 h of LP total" and was silent on `data/clean`. It is a **HARD
prerequisite for every forecast leg and it is gitignored**, so a fresh container has none of
it. The confirmed-exits loader refuses rather than degrading:

```
RuntimeError: confirmed-retirements: clean partition for NYISO is absent while
confirmed_exits_enabled is on in forecast mode … refusing to silently degrade to
the economic screen
```

This is documented — forecast plan §2.4's boxed prerequisite, measured by FFR-3A at ≈55 min /
50 datatypes / ≈1.6 GB — and the parent §8 simply did not carry it into the budget. Measured
here: **56 datatypes**, `PYTHONPATH=. uv run python scripts/regenerate_clean.py`, with
`lmp` alone taking ≈13 min. The corrected budget for this lane is **data/clean (~45–60 min,
one time per container) + the LP**, and the failure mode is loud and cheap (2 s per leg), not
silent. Recorded so the four remaining program-ISO policy lanes carry it in their own §8.

**Nothing was contaminated.** The eleven aborted legs wrote an error-only
`full_horizon_summary.json` into their out-dirs; the whole
`results/scn-campaign-policy-2026-09-06/` tree was deleted before anything else ran, and
`results/NYISO/` still held **0 cache entries** at the point the real legs were dispatched.

## 2. Owner decisions on the two items the parent PRECOMMIT left open

Both were put to the owner with the parent document pushed, before any LP.

| item | parent §  | decision |
|---|---|---|
| **The rule-12 slot (precondition P4)**, which the parent recorded as *NOT ESTABLISHED — first solve HELD* | §1 P4, §8 | **GO.** The slot is free; the legs are authorized to run. |
| **The `REF` / `LOAD-HI` rematerialization**, the parent's one declared deviation from charter P2 | §8, gate G13 | **Rematerialize both, as declared.** The answer is never re-derived; gate **G13** stands exactly as written, and a mismatch is still a STOP that becomes this lane's headline. |

## 3. THE FAN-OUT — the nine legs are split across four containers, by owner instruction

**Owner instruction, verbatim:** *"Give me prompts to run multiple scenarios in parallel in
other sessions so that you don't burn 15 hr compute here I have unlimited compute to run lps
in other sessions."*

**What this spends, said plainly.** Charter P4 / ruling **S14** caps the SCN track at *"≤ 2
SCN-track solves at once … only on different ISOs"*. Four concurrent NYISO containers is
beyond what that clause contemplates. The clause's stated rationale is **memory on one shared
box** (the charter's own sizing note: *"pair a heavy ISO with a light one, never two heavy
ones"*, on a 15 GB box), and these are **separate containers with separate 15 GB allowances**,
so the rationale does not transfer — but the *letter* of the cap does, and the owner
instruction above is what authorizes exceeding it. It is recorded as an owner decision, not
read into S14. Inside every container the rule-12 half that still binds is honoured without
exception: **years sequential within a leg, legs sequential within a container, never two LPs
at once anywhere.**

### 3.1 The partition

| container | legs | LP |
|---|---|---|
| **this session (D)** | `REF`, `LOAD-HI`, **`CAP-STATE-TIGHT`** | ~55 min |
| **group A** (`claude/scn-ws5a-policy-nyiso-leg-a`) | `REF`, `CES-P10`, `CES-P20`, `CES-P30` | ~75 min |
| **group B** (`claude/scn-ws5a-policy-nyiso-leg-b`) | `REF`, `CES-T80`, `ALL-CLEAN` | ~55 min |
| **group C** (`claude/scn-ws5a-policy-nyiso-leg-c`) | `REF`, `VOL-MID`, `VOL-HI`, `CES-P20+VOL-HI` | ~75 min |

Every group branches from **`de06bcd6`** — THE PIN plus this lane's two doc-only commits,
verified to carry a **zero solve-path diff** against `bdfb3095` — so all four containers solve
the identical code at the identical pin, and every leg's HEAD guard is the diff itself
(`git diff --name-only <PIN> HEAD -- src/market_sim scripts configs data/raw` must be empty)
rather than an exact sha, which survives each container's own artifact commits.

The grouping is by **mechanism**, not by cost: the CES premium ladder, the two target-row
legs, the voluntary legs, and the cap case. Each group therefore reports one coherent block,
and each is scored by the **same committed instrument**
(`docs/handoffs/scn-ws5a-policy-nyiso/score_gates_2026-09-06.py`, pushed at `de06bcd6`
*before* the first leg precisely so no group scores its own legs its own way).

### 3.2 Why every group also solves `REF` — and what it buys

`report_scenario_deltas.py` reads each case's **cached bundle**, not its slim summary, and a
bundle lives only in the container that produced it. A group without `REF` in its own cache
cannot produce the charter's per-case delta set at all — no `import_co2_mt_reported` leakage
line, no by-fuel, no by-zone, no curtailment table. So each group rematerializes `REF` at its
own committed key `f10cc93084b4c0db` and reports against it locally.

**This strengthens gate G13 rather than diluting it.** The parent §6.2 registered P-1 as a
single-container determinism identity. It is now a **four-container replication**: four
independent solves, in four fresh containers, each with its own independently rebuilt
`data/clean`, must all reproduce the committed trajectory (`co2_mt` 23.6923 / 24.5911 /
17.1630 / 13.7082 / 10.9030; `lw_price` 50.193 / 49.18 / 50.92 / 49.28 / 54.95; 14/14 PASS;
`unserved_mwh` 0.0 throughout) **exactly**. A disagreement *between containers* would be a
finding about the pin's reproducibility that no single-container run could ever surface, and
it outranks every other result in this lane. Each group is instructed to check `REF` **first**
and to stop before its other legs if it misses.

### 3.3 What the groups may not do

They solve, report and push slim artifacts. They do **not** register runs on the dashboard,
touch `frontend/`, `docs/codebase-site/`, the mechanism matrix, `invariant-failures.json`, or
any FINDING; they do not rebase onto a newer `main`, move a default, add a `ScenarioConfig`
field, or interpret a result against a residual. This session fetches their branches and does
the registration, the combined report, the FINDING and the matrix stamp — so the registration
seam (rule 15 / §7.5) and the Y-24 invariant-declaration ratchet stay under one writer.

## 4. Unchanged

The pin; the four phase-0 kills and their proofs; the nine surviving cases and their cache
keys; the voluntary regime table and the per-arm WTP ceilings; the cap budget table; G-DRIFT
on both windows; every prediction P-1 … P-19; every gate G1 … G13; the DOF ledger (**zero**
free parameters); and every duty in §10. Rule 29(c) still binds trivially — this lane produces
no screen bundle and no control bundle.
