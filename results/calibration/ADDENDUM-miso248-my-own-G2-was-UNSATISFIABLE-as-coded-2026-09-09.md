# ADDENDUM miso-248 (second) — **MY OWN `G-2` FAILED, AND THE FAILURE IS AN UNSATISFIABLE BAR IN MY OWN CODE, NOT A RESULT.** Published first, at full magnitude, with the repair and its decision rule declared **BEFORE** the repaired number is computed

**Governs:** `G-2` only. Nothing else in the session moves; no other bar is touched; the arm solve
running while this is written is untouched by it. First-run record preserved verbatim at
`results/calibration/_miso248_g2_first_run_UNSATISFIABLE.json`.

---

## 1. THE FAILURE, AT FULL MAGNITUDE

`G-2` as coded returned **`PASS: false`**, `n_non_spp_rows_moved: 5`:

```
n_rows_total 48 · n_rows_moved 16 · n_non_spp_rows_moved 5
all_moves_exact_and_hour_constant  false
MISO_external_refimp_SPP#1: want -2.8200000000000003, got -2.8200000000000003  std 2.56e-16
MISO_external_refexp_SPP#1: want  2.63,                got  2.629999999999999   std 1.36e-15
MISO_external_refimp_SPP#2: want -4.57,                got -4.569999999999993   std 5.13e-16
MISO_external_refimp_SPP#3: want -7.75,                got -7.75                std 3.28e-15
MISO_external_refimp_SPP#5: want -39.349999999999994,  got -39.34999999999998   std 7.67e-15
```

## 2. **WHY THIS IS A BROKEN GATE AND NOT A RESULT — the distinction this lane fixed at miso-246, applied against myself**

The rule this lane carries is: *a gate that was **satisfiable** and simply failed is a RESULT; do not
repair it.* miso-247 left `G-1` standing at 3.279× on exactly that ground. **`G-2` as coded was NOT
satisfiable**, and the proof is arithmetic rather than a judgement call:

* the field the gate reads is `mc = hub(t) + δ_k`, computed in float64;
* the gate's operand is `d(t) = (hub(t) + δ_new) − (hub(t) + δ_old)`;
* `hub(t)` varies hour to hour over roughly `[−, 200]` $/MWh, so the rounding of each addition
  varies with `hub(t)`, and `d(t)` therefore carries a per-hour error of order `1e-14`;
* the gate demanded **`float(d.std()) == 0.0` exactly**. No correct implementation of
  `hub(t) + δ` can satisfy that. **The bar was unmeetable by construction.**

**The label `n_non_spp_rows_moved: 5` is my code's own mislabelling** and I state it plainly: the
five rows it lists are **all SPP rows**, appended to the same list the non-SPP rows would go in. **No
non-SPP row moved at all.**

## 3. **WHAT ACTUALLY HELD, reported before the repair rather than after it**

The substantive confinement claim is already measured and it is clean:

* **16 rows moved of 48** — exactly the 8 import + 8 export SPP bands;
* **ZERO non-SPP rows moved** (every listed row is `…_SPP#k`);
* every moved row's delta equals `δ_new,k − δ_old,k` to **≤ 8e-15 $/MWh**, and its within-row
  spread is **≤ 8e-15 $/MWh**.

**So the mechanism is confined exactly where the PREREG said it must be**, and the only thing that
failed is the numeral I chose to express "exactly" with.

## 4. THE REPAIR, DECLARED BEFORE THE REPAIRED NUMBER IS COMPUTED — and it is **STRICTER**, not looser

The unsatisfiable literal `std == 0.0` is **DELETED, not widened** (rule 26 `[R-DELETE]` — a bar that
cannot be met is not a bar), and replaced by a **quantified, satisfiable, and tighter-than-necessary**
pair, both of which must hold for every moved row:

1. **hour-constancy:** `max_t d(t) − min_t d(t) ≤ 1e-9 $/MWh`;
2. **value identity:** `max_t |d(t) − (δ_new,k − δ_old,k)| ≤ 1e-9 $/MWh`.

plus the two structural clauses, **unchanged**: exactly **16** rows move, and **zero** of them is a
non-SPP row. `1e-9 $/MWh` is six orders of magnitude below any economically meaningful quantity in
this model and five orders above the observed float error, so it discriminates a real leak from
float64 rounding and nothing else.

**What is NOT done.** The gate is not re-scoped, no row is dropped, the 16-row and zero-non-SPP
clauses are not relaxed, and the repair is not chosen after seeing which form would pass — the
observed errors are `~1e-14` and **any** bar between `1e-13` and `1e-9` would pass identically, so
the choice cannot be doing work. **`G-2`'s verdict is recomputed under this form and reported
whatever it is.**

**Also disclosed:** the gate probe's provenance block reads `dirty: true`. That is this session's own
`spec.py` re-derive edit, which is the arm — expected, and named here so no reader has to infer it.

## 5. Non-claims

1. **The first-run failure is not withdrawn or hidden**; its record is preserved verbatim.
2. **No other gate's bar is touched**, and `G-1`'s `[1/3, 3]` band and `G-3`'s `atol = 0.01` are
   untouched by this document.
3. **The repair is declared before the repaired number exists**, and it makes the gate stricter in
   substance (a quantified bound where there was an unmeetable literal), not weaker.
4. **Nothing about the arm, the control, the re-derive or the screen year moves because of this.**
