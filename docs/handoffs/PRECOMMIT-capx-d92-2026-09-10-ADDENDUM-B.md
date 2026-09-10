# ADDENDUM B to `PRECOMMIT-capx-d92-2026-09-10.md`

**The FC-6 assembler is BUILT AND PROVEN before any of this lane's arms exist.** Still no LP in the
parent; the four shards are solving.

---

## B.1 The end-to-end control: the committed d46 file, re-assembled from ITS OWN slim artifacts

`docs/handoffs/d92/assemble_paired_invariants.py` is pointed at
`results/ff-t3-neiso-golden/bau-d46/fc6/arms` — four committed arms that carry **summaries,
run_configs and `evolution_*.json` and NO dispatch parquets**, i.e. exactly the artifact set this
lane's shards will hand back. Output versus the committed
`bau-d46/fc6/paired_invariants.json`:

| row | status | detail |
|---|---|---|
| **P1** | PASS = PASS | `cumulative CO2 base 284.42 Mt vs high 273.92 Mt` — **EXACT** |
| **P1.premise** | PASS = PASS | `strictly positive delta in all 25 years (min +25.00, max +25.00 $/t)` — **EXACT** |
| **P2** | PASS = PASS | **EXACT up to the one disclosed clause** `[not scored at this grain: objective↑]` (ADDENDUM A §A.3) |
| **P3** | PASS = PASS | `cumulative builds moved 0.0% (base 42337 MW, pert 42319 MW)` — **EXACT** |

Same four idents, same order, same statuses. **Three of four detail strings are byte-identical to a
file produced from the full dispatch cache, and the fourth differs only by the sub-check the summary
grain provably cannot carry.**

**What this control does and does not establish.** It establishes that the assembly path is not
introducing error: given the same arms, it emits the same file. It does **not** establish that the
summary grain equals the cache grain in general — that claim rests on the two-point operand match in
ADDENDUM A §A.2.1 and is not upgraded here.

## B.2 The three switches now fixed, so nothing about them can be chosen after seeing a number

1. **P1's status rule** is the instrument's: `PASS iff high < base`, no tolerance, no band.
2. **P2 keeps its `not_scored` clause in the emitted file.** It is not stripped to make the new row
   look like the old one.
3. **Row order is `P1, P1.premise, P2, P3`**, matching the committed file, so a diff against d46 is
   readable.

## B.3 What is still open, and will be decided by L0's numbers alone

The FC-5 explanations for the six-plus-one rows named in ADDENDUM A §A.4. The **mechanical** half
(model values, divergences, which rows change class) is already computed by
`rebase_disposition.py` and cannot be influenced by a verdict; the **authored** half is written
against L0 and is reported at full magnitude whether it leaves FC-5 at CAVEAT (prediction **D13**)
or takes it to FAIL. **A row will not be talked into corridor to protect D13.**
