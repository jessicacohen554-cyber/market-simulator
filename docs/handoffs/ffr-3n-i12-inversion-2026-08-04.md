# FFR-3N — Attributing the FH-1 §3.3 gate's I12 inversion

**Session.** FFR Wave 3, attribution lane. Branch `claude/fh1-i12-inversion-3njgo4`, off
`origin/main` **`38a80266`** (the packet's stated HEAD `bc9e6dbf` was already ~30 merges stale
at session start; ERCOT keeper re-verified as `2026-08-03-ercot158-pool-arm` from the shard,
not the packet line).

**The deliverable is ATTRIBUTION, NOT A SMALLER NUMBER.** No `ScenarioConfig` default was
changed, no band widened, no damper unarmed, no parameter tuned, nothing promoted. The FH-4/FH-5
block is NOT lifted and owner decisions G.5 and D-9 are not pre-empted.

Pre-registration, committed and pushed **before either arm solved**:
`docs/PRECOMMIT-ffr3n-i12-inversion-2026-08-04.md` (commit `d962543e`).

---

## 0. One-line answer

*(filled after the arms — see §4)*

---

## 1. Candidate 3 — the band basis. Settled, no LP, and it moves the WRONG WAY

This was to be done first and netted out so the solve-based work measures the right residual.
It does not net out. **It enlarges the residual.**

### 1.1 The measurement

I12's energy-only branch (`check_forecast_invariants.py:594`) scores the ledger's
`reserve_margin` against the scalar `config.planning_reserve_margin`. Those are on different
denominators:

* the ledger's `reserve_margin` is `accredited_firm / **GROSS** peak − 1`
  (`runner.py:2698`, with `peak_demand = year_demand.sum(axis=0).max()` at `runner.py:992`);
* `planning_reserve_margin = 0.1375` is ERCOT's Board target stated on the CDR's **firm**
  (DR-netted) peak — and `resolve_adequacy_requirement_mw` applies it to
  `gross_peak × (1 − 0.058)`, ERCOT's own published Firm Peak Load construction.

Restating the requirement the model actually enforces as a margin over the gross peak:

```
0.942 × 1.1375 − 1 = 7.1525 %
```

| quantity | value |
|---|--:|
| Margin at which the model's own retirement floor is satisfied | **+7.1525 %** |
| Margin I12 scores ERCOT against | **+13.75 %** |
| **Basis gap** | **6.5975 pp** |

Reproduce: `uv run python scripts/probes/_ffr3n_i12_attribution.py --band-only`.

> **Correction to FFR-3C §2.1, small but worth having right.** That section reports the gap as
> **6.65 pp**, reading the floor as "13.80 %". The scalar is `0.1375`; `f"{0.1375:.1%}"`
> renders as `13.8%`, and the gap taken off the *rendered* value is 0.05 pp too large. The
> exact gap is **6.5975 pp**. Nothing in FFR-3C's conclusion depends on the difference — its
> FAIL-robustness argument holds unchanged — but the corrected figure is the one to carry.

### 1.2 The direction, which is the actual finding

FFR-3C met this defect in the **under**-supplied direction, where correcting it made the
breach *smaller* (the floor it moved was a floor). At the FH-1 gate posture the excursion is
**upward**, through the *ceiling* — and the ceiling is `floor + 15 pp`, so correcting the
floor moves the ceiling **down** by the same 6.5975 pp:

| band | floor | ceiling | 2025 margin | overshoot |
|---|--:|--:|--:|--:|
| **as I12 scores it** | 13.75 % | 28.75 % | 40.2 % | **+11.45 pp** |
| **on the model's own basis** | 7.1525 % | 22.1525 % | 40.2 % | **+18.05 pp** |

**Candidate 3 accounts for −6.5975 pp of the overshoot.** It is not an excuse for any part of
the inversion; it is the one candidate that could have made the number benign, and it does the
opposite. The residual that candidates 1 and 2 must jointly explain is **18.05 pp, not 11.45 pp**.

### 1.3 A consequence for the verdict label, flagged not acted on

I12 returns FAIL on `>= 3` consecutive out-of-band years and WARN otherwise. The gate posture
solves exactly three years. As scored, 2024 (32.3 %) and 2025 (40.2 %) are out and 2023 is in →
two consecutive → **WARN**. On the corrected 22.15 % ceiling, whether 2023 also exits decides
**WARN vs FAIL**. §3 reports 2023's margin against both ceilings.

This is reported as a property of the instrument. **Nothing here is a proposal to change the
band**, in either direction — under rule 14 `[R-ACCURATE]` the model's DR-netted basis is the
accurate one and I12's generic scalar is the estimate, which is a finding about the invariant's
definition for the owner (G.5), not a patch for this session to apply.

---

## 2. The evidence base is more confounded than the charter assumes

Before attributing the *difference* between FH-1's probe and FFR-3F's re-probe to any
mechanism, it is worth checking what actually differs between them. Both bundles' `meta.json`
are committed, so this is a no-LP read.

| field | FH-1 gate probe (`cc54eae9863ba180`, 2026-08-02T04:46Z) | FFR-3F capfix control (`5de5e8b320b525eb`, 2026-08-03T21:28Z) |
|---|---|---|
| `retirement_rule` | **legacy** | `null` → **pipeline** (D-1) |
| `correlated_forced_outage` | **False** | **True** |
| `entry_lookahead_reprice` | **False** | **True** |
| `entry_rate_limits` | not passed | **true** |
| `entry_commissioning_lag` | not passed | **true** |
| `exit_rate_limits` | not passed | false |

Plus a code delta (the FFR-3F cap-grain fix, and ~1 day of main).

**The two runs whose difference defines "the inversion" differ in at least five armed
mechanisms simultaneously**, three of them on the entry side. The FFR-3D instrument repair
(owner C.4(c), "UN-PIN — MATCH PRODUCTION") un-pinned `correlated_forced_outage` and
`entry_lookahead_reprice` on 2026-08-03 — *between* the two runs — and FFR-3D's own report says
so plainly: every T1-H verdict committed before it "are LEGACY EVIDENCE on a superseded
posture."

So the charter's three candidates are not an exhaustive partition of a one-factor change; they
are three hypotheses about a five-factor difference. This does not make the 40.2 % less real —
it is what the current shipped posture produces, measured — but it does mean **no single-arm
comparison against FH-1 can attribute it**, and it is why §3's arms are paired at a fixed HEAD
rather than compared to FH-1.

---

## 3. Candidates 1 and 2 — the paired arms

*(filled after the arms)*

---

## 4. What this evidence does NOT separate — stated plainly

*(filled after the arms)*
