# ADDENDUM miso-240 (second) — THE PROVENANCE GATE REJECTED THIS SESSION'S OWN INSTRUMENT ON LEG G-ID2, AND THE REPAIR IS DECLARED HERE BEFORE THE REPAIRED NUMBERS ARE COMPUTED

Extends `PREREG-miso240-charter-or-refuse-the-external-bus-price-2026-09-07.md` (pushed
`5c503155`) and `ADDENDUM-miso240-two-decision-rules-fixed-before-the-numbers-2026-09-07.md`
(pushed `9316432b`). **This is the miso-238 §0 pattern**: that session's gate fired on its own
statistic at 457.126 MW/z against a 0.5 bar, its ADDENDUM declared the repair before the
repaired numbers existed, and it moved no bar. So does this one.

**NO BAR MOVES.** The `≤ 1e-9` MW identity bar, the five provenance legs, G-ID1, `τ = $0.01`
and its declared sensitivity, Q-A's ladder and readings, Q-B's `0.25` / `0.50` bars and its
`100 MW/z` floor on **both** denominators (first addendum §A), Q-C's coverage bar, Q-C2's
`0.99` / `0.50` bars and its **closed** candidate set, and Q-D's `0.10` / `0.02` bars all stand
exactly as pushed. Zero LP. Keeper unchanged at `2026-09-07-miso-233-spp-hourly` (CALIBRATED,
C3c the single ledgered caveat, DOF 41/2).

---

## 0 — THE FAILURE, AT FULL MAGNITUDE, STATED FIRST

The first run of `scripts/probes/_miso240_external_bus_price_charter_phase0.py` (pushed at
`9316432b` **before** it was run) returned:

| leg | bar | measured | verdict |
|---|---:|---:|---|
| G-P1 `γ_MERIT` (miso-239) | ≤ 0.5 MW/z | pass | PASS |
| G-P2 channel shares (miso-239) | ≤ 0.005 | pass | PASS |
| G-P3 both ventile columns (miso-239) | ≤ 0.5 MW/z | pass | PASS |
| G-P4 `γ_model` (miso-238) | ≤ 0.5 MW/z | pass | PASS |
| G-X0 PJM export leg identically zero | exact 0 | 0.0 | PASS |
| G-ID1 band-count identity | ≤ 1e-6 MW | 0.0 | PASS |
| **G-ID2 pure-bin support identity** | **≤ 1e-9 MW** | **869.6 MW** | **FAIL** |

**PREREG §1: "If any leg fails, the instrument is declared BROKEN, the failure is published,
and NOTHING in §3 is read."** It is published here, and it is published *first*.

**The failure is in ONE cell of six** — 2024, the `s`-ladder. The other five read
1.91e-11 / 9.44e-11 MW (`s`-ladder, 2023 / 2025) and 1.52e-11 / 1.48e-11 / 7.96e-12 MW
(`p1`-mirror, all three years), i.e. **the bar is not too tight; five of six cells clear it by
two orders of magnitude.**

## 1 — THE CAUSE: an interval-convention error in THIS SESSION'S OWN predicate, not in the object

`G-ID2` asks whether the residual of `MERIT` on ventile dummies of its own conditioning spread
is exactly zero on every ventile bin containing no crossed threshold `δ_k`. The probe assigned
bins to thresholds by interval arithmetic:

```python
lo = np.concatenate([[-np.inf], edges]); hi = np.concatenate([edges, [np.inf]])
impure = [any(lo[b] < d <= hi[b] for d in crossed) for b in range(VENTILES)]
```

That is the **wrong half-open interval** for the bin index the same probe builds with
`np.searchsorted(edges, x, side="right")`, whose bins are `[lo[b], hi[b])`. When a threshold
`δ_k` lands **exactly on a ventile edge** the predicate marks bin `b` (whose upper edge *is*
`δ_k`, and on which `1[s > δ_k]` is in fact constant at 0) impure, and marks bin `b+1` (which
contains the hours at and above `δ_k`, where the indicator actually changes) **pure** — so the
identity is evaluated over a genuinely mixed bin and reads 869.6 MW. The counts corroborate it
exactly: 2024 reports `n_impure = 8` against `n_crossed = 8`, i.e. the right *number* of bins
with one of them displaced by one position. **The defect is in this session's bookkeeping; no
predecessor quantity, no channel definition and no object is implicated.**

## 2 — THE REPAIR, DECLARED HERE, BEFORE THE REPAIRED NUMBERS EXIST

Two changes, both to the impurity predicate only:

1. **Impurity becomes EMPIRICAL and convention-free.** A ventile bin is **impure** iff `MERIT`
   is not constant on it — `max(MERIT) − min(MERIT) > 1e-9` MW over the bin's hours. This
   removes the half-open-interval question from the instrument entirely rather than fixing one
   side of it, and it carries **no free parameter**: `1e-9` MW is the same identity tolerance
   the leg already gates on.
2. **The falsifiable content the empirical predicate would otherwise lose is RESTORED AS A NEW
   GATED LEG, `G-ID2b`, fixed here before it is computed.** With impurity read off the data,
   "the residual is zero on pure bins" becomes true by construction, so on its own it would test
   nothing. The claim that actually carries §3b's mechanism is the *arithmetic* one — a monotone
   `K`-step function of `x` can make **at most one** ventile bin of `x` impure per threshold —
   and it is now gated directly:

   > **G-ID2b:** `n_impure ≤ n_crossed_thresholds`, in **all three years and on BOTH ladders**
   > (the `s`-ladder and the `p1`-mirror), six cells. A violation falsifies the mechanism claim
   > and declares §3b BROKEN.

   This is **stricter** than what the PREREG had: the original leg could pass on a mis-assigned
   bin set, and this one cannot.

`G-ID2` keeps its `≤ 1e-9` MW bar and its gating role; `G-ID2b` joins it as a gating leg. **No
other line of the probe is touched.**

## 3 — DISCLOSED AGAINST INTEREST: THE §3 VALUES WERE PRODUCED IN THE SAME RUN AND HAVE BEEN SEEN

The probe computes the whole report in one pass and prints it, so the failing run **also emitted
every §3 quantity, and this session has seen them.** PREREG §1 says nothing in §3 is read when a
leg fails; that instruction was violated by the instrument's own structure, not by a decision,
and the honest remedy is not to pretend otherwise. It is stated here, before the repaired run,
together with the reason it cannot rescue anything:

**The repair touches ONLY the impurity predicate, which feeds no verdict.** `n_impure`,
`share_hours_impure` and `max_abs_resid_on_pure_bins_mw` are REPORTED columns; not one of Q-A,
Q-B, Q-C, Q-C2 or Q-D reads any of them, and none of their decision rules or bars is altered
here. **Therefore the repaired run's §3 values must be BYTE-IDENTICAL to the failing run's.**
That is declared here as a prediction, and the repaired run **verifies it and publishes the
comparison** (`s3_values_unchanged_after_repair`, an exact equality check over the whole §3
block of the report). If any §3 value moves, the repair is not what this addendum says it is,
the instrument is declared BROKEN a second time, and nothing is read.

**No decision rule is being written after seeing a number.** Every Q-A / Q-B / Q-C / Q-C2 / Q-D
bar, ladder and reading was fixed in the PREREG or the first addendum, both pushed before the
probe ran; this addendum changes a bookkeeping predicate and adds a leg that can only make the
gate harder to pass.

## 4 — Governance

Rule 1 `[R-STRUCT]`: no bar moved; the one change makes the gate **stricter**, and the failure
is published at full magnitude before anything else. Rule 12: no LP. Rule 13: measurement only.
Rule 14 / 23: no input changed, no derive re-run; PREREG §5.2's freeze on the `δ_k` ladders and
the measured envelope binds unchanged. Rule 15: no run produced, registered or pruned. Rule 21
`[R-DOF]`: 41/2 unchanged; the repaired predicate carries **zero** free parameters. Rule 22:
2023–2025 only. Rule 24: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO only. Rule 26
`[R-DELETE]`: the defective predicate is **replaced**, not left in place behind a flag. Rule 27:
blobs verified after push. Rule 28(b): evidence-append form only. Rule 29: clause 0, zero LP.
