# ADDENDUM miso-242 — the Q-A / Q-B / Q-D / Q-E results are published HERE, and ONE purely descriptive follow-up (**D-EDGE**) is declared **before it is computed**. It carries **no decision rule** and **cannot move any verdict**

**Governs:** `PREREG-miso242-why-the-spp-seam-is-idle-2026-09-07.md`, as already extended by
`ADDENDUM-miso242-the-dead-band-predicate-was-a-rearrangement-2026-09-07.md`. Pushed **before**
D-EDGE is computed. **No bar moves. No decision rule is added, changed or removed.**

---

## 1. The provenance gate now PASSES on all six legs, and the four questions are DECIDED

Re-run on the repaired predicate (the previous addendum's §3), **G-DB is 0 / 0 / 0 disagreeing hours
on both SPP and PJM**, and the other five legs are unchanged at |Δ| = 0.0000 on every share and
correlation column. The pre-registered verdicts, on the rules fixed in the PREREG:

| | 2023 | 2024 | 2025 | bar | pre-registered verdict |
|---|---:|---:|---:|---:|---|
| **Q-A** `|Z_derive − Z_target|`, SPP | **0.0395** | 0.0144 | 0.0089 | ≤ 0.020 all years | **IDENTITY FAILS** (2023) |
| Q-A, PJM | **0.0000** | **0.0000** | **0.0000** | — | exact |
| **Q-B** `|Z_model − Z_derive^K|`, SPP | 0.0274 | 0.0344 | **0.1017** | ≤ 0.050 all years | **DISPLACED** (2025) |
| **Q-D** `Z_target(PJM) < Z_target(SPP)` | 0.0022 < 0.3501 | 0.0142 < 0.3580 | 0.0314 < 0.3698 | all years | **YES** |
| **Q-E1** `corr(model net, s_model)` | +0.7946 | +0.6989 | +0.7434 | > 0 all years | **SIGN HYPOTHESIS REFUTED** |

On PREREG §4's decision table, `IDENTITY FAILS | any` ⇒ **TABLE-INTERNAL**, and that is this
session's verdict. It is recorded here **before** any further quantity is computed, so nothing below
can be read as having produced it.

**Stated against interest:** the branch that would have let this session write *"item 1 CLOSES"* was
`IDENTITY HOLDS + TRANSMITTED`, and it **did not occur**. This session does not claim the closure it
would have preferred; item 1 is handed forward with a quantified successor instead.

**Also recorded here, and it is the load-bearing measured number:** `Z_target(SPP)` =
**0.3501 / 0.3580 / 0.3698** — the **measured** SPP seam is within ±250 MW of zero in **35–37 % of
hours**, against PJM's **0.2 / 1.4 / 3.1 %**.

## 2. D-EDGE — declared here, BEFORE it is computed

**What it is.** The Q-Q identity has two edges and Q-A measures only their sum. D-EDGE splits it,
per seam per year on **R_D**, into the two exceedances the estimator actually equates:

```
import edge:   P( spread_derive >  δ_1^import )   against   P( flow > +mid_1 )
export edge:   P( spread_derive <  δ_1^export )   against   P( flow < −mid_1 )
```

plus a **tie census** on the derive spread: the count of R_D rows lying exactly on either threshold,
and the number of distinct spread values, since `np.quantile` cannot place a threshold at a nominal
exceedance when the underlying sample is heavily tied.

**Its status, fixed here.** D-EDGE is **REPORTED, GATED NOWHERE**. It carries **no bar, no decision
rule and no verdict**, in either direction. It is arithmetic *inside* a quantity whose verdict §1
has already published, so it **cannot change Q-A's verdict, Q-B's verdict, Q-C's decision-table row,
Q-D's gated comparison or Q-E's sign leg**, whatever it returns — including if it returns something
that would have been convenient. Its only purpose is to tell a successor *which* edge the 2023 miss
sits on.

**What it explicitly does NOT license.** Nothing. In particular it does **not** license a re-derive,
a damping factor, a change of K, a re-spacing of δ_k, a rounding change, an envelope or percentile
change, or any interface-limit change — PREREG §5.2 fixed that for **every** branch and fixed it
again for the IDENTITY-FAILS branch by name, which is the branch that occurred. Every number D-EDGE
produces is **UN-TARGETABLE** (PREREG §5.1).

Probe: `scripts/probes/_miso242_edge_decomposition_addendum.py` →
`results/calibration/_miso242_edge_decomposition_addendum.json`, pushed with this document and
**before it is run**.
