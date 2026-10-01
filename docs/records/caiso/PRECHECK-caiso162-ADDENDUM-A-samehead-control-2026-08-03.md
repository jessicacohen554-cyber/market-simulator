# ADDENDUM A to PRECHECK-caiso162 — the control arm, and a correction to §7

**Session** caiso-162 · **Date** 2026-08-03 · written **after** arm B solved,
**before** any A/B result was read.

## 1. What went wrong in the prereg

Prereg §7 ("BUILT-IN ZERO-DELTA CONTROL — 2023") asserted:

> **2023 MUST come back byte-identical to the keeper.**

**That assertion was wrong as written, and it is withdrawn.** It silently
assumed the committed keeper bundle `caiso156_meter_screen_B` was solved at the
same HEAD as this session. It was not:

| | git sha | basis sha |
|---|---|---|
| keeper `caiso156_meter_screen_B` | `69e0e30` | `0d49cc4` |
| arm B `caiso162_peryear_import_caps` | `c4ca927` | `de504ad` |

**13 commits touching `src/market_sim/` landed in between**, several plainly
solve-affecting:

- `9a54412` materialize the reserve balance-row activity lazily, inside the co-opt branch
- `24b1602` D-1: flip `retirement_rule` default legacy → pipeline
- `3e33f15` D-2: arm `entry_rate_limits` + `entry_commissioning_lag`
- `e6f0cdb` owner decision D-3a: net-CONE forward mode → `reindex_gross`
- `9df32c2` persist per-family reserve duals
- (+8 more)

So a treatment-vs-keeper diff measures **HEAD drift + arm**, never the arm.

## 2. What was actually observed, and why it is not a wiring failure

Arm B vs the committed keeper, P1, load-weighted:

| year | zone-hours changed | mean LMP delta | % of level |
|---|---:|---:|---:|
| 2023 | 16,128 | +0.0059 $/MWh | +0.0106% |
| 2024 | 16,474 | +0.0027 $/MWh | +0.0072% |
| 2025 | 18,010 | −0.0017 $/MWh | −0.0044% |

2023 moved, which by §7 as written is a stop-the-line event. It is **not** one,
because the arm **cannot** touch 2023's LP inputs. This was verified
**structurally, before the solve**, with no LP:

```
apply_caiso_local_import_limits, no LP:
  2023: returned SAME OBJECT (no-op)    LA_BASIN=12008  SDGE=1436
  2024: returned NEW CONFIG             LA_BASIN=15224  SDGE=2074
  2025: returned NEW CONFIG             LA_BASIN=15174  SDGE=2071
```

For 2023 the function finds `cap == link.ttc_mw` on both links, sets
`changed = False`, and returns `iso_config` itself
(`interchange/caiso.py:1831-1837`). `runner.py:1630` then skips the branch
entirely, leaving `year_ttc = ttc` untouched. 2023's LP is bit-for-bit the same
LP in both arms. The observed 2023 delta therefore has exactly one possible
source: **HEAD drift**.

**The three deltas in the table above are confounded and are NOT the arm's
effect. They are withdrawn as evidence and are superseded by the A/B in §3.**

## 3. The correction — arm A, a same-HEAD control

`results/calibration/caiso162_control_A` — the caiso156 keeper recipe replayed
at **this** HEAD with **no `--set`**, i.e. a structurally zero ScenarioConfig
delta rather than an asserted one. This is the caiso-158 ADDENDUM B /
caiso-160 pattern (control arm and treatment arm at the same head), which the
handoff carried forward as lesson (c) and which this prereg mis-applied: "2023
is built in" removes the need for a separate control **year**, not the need for
a same-HEAD control **run**.

**§7 is restated in its corrected form:**

> **2023 must be BYTE-IDENTICAL between arm A and arm B.** The arm is a provable
> no-op there (§2), so any 2023 difference between the two arms is a wiring
> failure — stop and fix before reading 2024 or 2025. HEAD drift cancels in an
> A/B at one head, so this test is now sound.

## 4. What is unaffected

- **The §3 ceiling stands.** It was computed from the *keeper's own* committed
  hourlies as an upper bound on the pocket-premium channel ($0.084/MWh in 2025
  against the $0.76/MWh needed to reach the ±10% band). It is a property of the
  keeper's dispatch and its zonal price separation, not of any A/B, and HEAD
  drift does not enter it. The observed magnitudes are consistent with it.
- **The §2 pre-check stands** for the same reason (measured on keeper bytes).
- **The §3b governance answer stands** — the bound on what this lever could take
  from the caiso-141 A2 attribution is ≤0.22 pp of a 12.2 pp residual.
- **The §5 rule-14 disposition stands, unchanged and still pre-committed:** the
  published input stays whatever the A/B shows; a worse fit is a discovered bug
  opening a root-cause investigation, never a revert to the frozen estimate.
- **The no-tuning clause stands** — this addendum adds no parameter and sweeps
  nothing. It adds a control **run**, which is evidence hygiene, not a knob.

## 5. Scoring note

Both arms are scored with `scripts/calibration_verdict.py`. The **incumbent
keeper's** determination remains the promotion bar, but the **mechanism's**
effect is read A vs B at one head. Where the two disagree, the A/B is the
mechanism evidence and the keeper comparison is reported as HEAD drift, labelled
as such.
