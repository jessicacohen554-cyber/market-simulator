# ASSESSMENT (pjm-159): PJM is **NOT** ready for a `final` declaration. Recommend **HOLD**.

**Session:** pjm-159 (task A — final-declaration assessment)
**Date:** 2026-08-06
**Branch:** `claude/pjm-final-assessment-nak29a`
**Scope:** NO LP. No solve, no score of any out-of-training year, no registration,
no mechanism tested, no keeper touched, no marker edited, no freeze touched.
Every number below is either a read of a committed artifact, a re-run of a
committed-artifacts-only scorer on the **in-sample** years, or a read of source
code at HEAD.
**Standing:** `final` is an OWNER action. This document **recommends**; it
declares nothing and lifts nothing.

---

## §0 — the recommendation in one table

**HOLD. Do not declare PJM `final`.** Four blockers, each sufficient on its own,
and two of them are *newly measured in this session*.

| # | blocker | status | sufficient alone? |
|---|---|---|---|
| **B1** | **Neither locked-test year can be solved today.** 2019 has no demand driver (`eia_demand_profiles.parquet` starts at 2021 for every ISO — the cross-ISO F3 gap), no `calibration_reference.json` block and no `PJM_2019_renewable_capacity.csv`. H1-2026 is publication-horizon blocked by construction. | **VERIFIED ON DISK** this session | **YES** — a `final` grant would be *unspendable*, so declaring it buys nothing and risks a premature spend later |
| **B2** | **The frozen keeper recipe does not reproduce on 2019.** `pjm_seam_measured_ladder` is armed but `PJM_SEAM_LADDER_BY_YEAR` carries **2023/2024/2025 only**; outside those years the ladder silently no-ops **and the firm scheduled-export floor it displaces under rule 19 fires in its place**. A different seam mechanism = not the keeper's model. Two further overlays (`measured_ramp_capability`, `measured_ct_heat_rates`) are pooled on the training window by construction. | **NEW, measured this session** | **YES** — a touch-once test of "the frozen keeper config" that silently runs a different mechanism is not a test of the keeper |
| **B3** | **The locked-test C3a would be scored on a different statistic than every in-sample number.** The rubric-v2.4 basis ladder is `rt_lw > da_lw > rt > da`; PJM's bench carries `rt_lw` for 2023–2025 **only**. Load-weighting raises PJM's RT actual by **+3.9 / +6.0 / +6.8 %** — 40–70 % of C3a's entire ±10 % band, from the basis alone. And `rt_lw` for 2019 **cannot be built**: `lw_retrofit` calls `load_demand`, which is the same F3 gap as B1. | **NEW, measured this session** | **YES** on a tier that cannot be re-scored |
| **B4** | **The pjm-158 DA/RT basis defect is disqualifying for the touch-once tier** (not for the keeper, and not for the validation tier). The layer's C1 contribution on any year is `−(DA−RT basis) × gain`, and **PJM's DA−RT spread flips sign outside the training window**: +0.89/+0.25/+0.82 in-sample vs **+0.10 in 2019** and −0.03/−0.25/−0.27/−1.49 in 2018/2020/2021/2022. The in-sample near-cancellation is regime-specific, so a 2019 result is uninterpretable in either direction. | **NEW quantification** this session | **YES** for the locked tier |

Two further open items are **not** independently disqualifying but belong in the
decision: the pjm-135 **M4 net-interchange defect** (§6 — an unbounded export
side that demonstrably absorbs perturbations) and the **CAMPD economic-layup
residual** (§7 — which the owner **re-adjudicated on 2026-08-06**, declining the
charter's own recommendation to close with cause and lift fully; the freeze's
basis is therefore a live owner choice, not a stale leftover).

**The precedent that should settle it (§8):** NEISO's locked test was spent
2026-07-07 on `2026-07-07-neiso53-winter-fuelsec-coldsnap`. NEISO's keeper today
is `2026-08-05-neiso-83-ca1-reclass` — **thirty keeper generations later**. Its
certified out-of-sample number belongs to a model that no longer exists, and it
is never re-grantable. That is the exact failure a PJM `final` declaration today
would repeat, with three known-open defects instead of none.

---

## §1 — what IS in good order (stated first, because it is most of the picture)

PJM genuinely is the ISO closest to `final`. Nothing below is hedged.

**The keeper re-verifies clean, from committed artifacts, at HEAD.**
`scripts/calibration_verdict.py --run-id 2026-08-04-pjm-152-collapse` (no solve):

```
CALIBRATION DETERMINATION: CALIBRATED     scorable years 2023, 2024, 2025
C1 fuel-mix PASS · C2 system volume PASS · C3a mean LMP PASS · C3b shape PASS
C3c price tail PASS · C4 dispatch corr PASS · C6 governance PASS
C7 diurnal shape PASS · C8 forced-energy PASS
D-10 free-class C1: all 16/16 · free 12/12      ZERO fails, ZERO caveats
```

Four C8 report notes (CT_PEAKER 2023/24/25 at 16.2/16.4/16.7 %, ST_GAS 2025 at
39.9 %) are **clean grounded PASSes** under rule 21's grounded-pass clause — all
binding mechanisms clear D-4, profile *r* 0.927/0.962/0.974/0.896, off-peak CV
ratio 0.719/1.075/0.836/2.242. They are notes, not caveats.

**Governance is clean.** `scripts/audit_keepers.py --iso PJM` → **0 failures, 0
warnings** across the keeper, holdout, marker and status shards. The `complete`
marker's `keeper` field is correctly re-keyed to the current keeper with the
D-5(b) determination re-verification recorded.

**The lever queue is genuinely empty and the frontier is genuinely declared.**
Queue cleared at pjm-153 (item 8 → `I` provably inert, item 10 → `R` premise
refuted, item 15b → collapsed into the frontier limitation, item 4 → blocked on a
measured sub-zonal load basis that does not exist). Frontier owner-declared at
pjm-142. The three watch-list items (W1 CT_PEAKER forced share, W2 C3c margin,
W3 ST_GAS 2025) are monitored, not actionable. Per rule 28 I checked the matrix
(`docs/codebase-site/data/mechanism-matrix.js`) and PJM's lever queue
(`docs/mechanism-testing-matrix.md` §5) before writing: **PJM's queue is still
clear, and this session proposes no lever, so no cell moves.**

**The 2022 validation touchpoint is spent and honestly recorded** —
`2026-08-05-pjm-2022-touchpoint`, NOT-YET, degraded on C1 (`CC_REGULAR`
+18.28 TWh) and C3b (NRMSE 0.206), seven criteria held, availability-envelope
parity verified, no re-tune performed in response.

So the objection is **not** that PJM's calibration is unfinished. It is that the
locked tier cannot presently be spent, cannot presently be spent *on the
keeper's own model*, cannot presently be scored on the keeper's own price
statistic, and carries one open mechanism whose contribution is regime-dependent
in exactly the way a touch-once test cannot absorb.

---

## §2 — B1: neither locked-test year is solvable today

This is the plainest blocker and it is verifiable in two commands.

**2019.** Three model/scoring inputs required for any PJM solve are absent for
2019 on disk right now:

| input | on-disk PJM coverage | consequence |
|---|---|---|
| `data/raw/_validation-source/calibration_reference.json` `isos.PJM` | **2021, 2022, 2023, 2024, 2025** | no 2019 block; `build_calibration_reference._demand_totals` cannot produce one |
| `data/raw/_validation-source/PJM_<y>_renewable_capacity.csv` | **2021–2025 only** | no 2019 renewable capacity |
| `data/raw/eia-930/eia_demand_profiles.parquet` (what `load_demand` reads) | 2021–2025 for **every** ISO | **the primary demand driver.** `load_demand('PJM', 2019)` raises |

The demand-profile gap is the cross-ISO **F3** blocker, recorded independently in
`docs/holdout-data-equivalency-register-2026-07.md` for PJM (§PJM, line 518:
*"the 2018-2020 demand-profile gap is a hard blocker for every ISO — no dispatch
is possible without it"*), NEISO (confirmed by a direct `load_demand_meta`
failure), CAISO and MISO. There is **no in-repo builder** for the artifact — it
is hand-uploaded — so this is not a fetch away.

**H1-2026.** Blocked by construction, not by neglect:

- the full-8760 demand contract is **unbuildable from a partial year** (the
  register's own words), so `load_demand('PJM', 2026)` cannot exist;
- `PJM-AS/pjm_2026_as_up_mw.parquet` — the series `pjm_reserve_pergen` actually
  reads — is **absent by design**: the builder refuses a partial year;
- `actual_lmp_hourly_PJM` 2026: raws landed (`..._partial.csv`, 52,116 rows),
  parquet block **deliberately not built**;
- CAMPD Q2-2026 unposted; EIA delivered gas May-2026+ unpublished.

**Therefore a `final` declaration issued today grants an authorization that
cannot be exercised.** That is worse than neutral: the grant is permanent, the
years are touch-once, and the standing pressure of an unspent grant is exactly
how a spend happens before the blockers close.

---

## §3 — B2: the frozen keeper recipe does not reproduce on 2019 *(new)*

A locked test is defined as *"scored EXACTLY ONCE per ISO with the frozen keeper
config."* The keeper carries **78 `True` ScenarioConfig flags**
(`results/calibration/pjm152_collapse_A/run_config.json`). Three of them do not
survive a move to 2019, and the first one changes the LP's structure silently.

### §3.1 — the seam ladder silently swaps to a different mechanism (decisive)

`pjm_seam_measured_ladder = True` in the keeper.
`PJM_SEAM_LADDER_BY_YEAR` (`src/market_sim/model/interchange/spec.py:1251`)
carries exactly **`{2023, 2024, 2025}`** — its own preamble says *"default off,
**backcast years below only**"*.

And `src/market_sim/model/interchange/import_nodes.py:971-981`:

```python
_pjm_ladder_active = (
    iso == "PJM"
    and getattr(config, "pjm_seam_measured_ladder", False)
    and year in PJM_SEAM_LADDER_BY_YEAR
)
if not _pjm_ladder_active and inject_reference_price_firm_export(...):
```

So on 2019, with the flag armed, **the ladder no-ops AND
`inject_reference_price_firm_export` fires** — the firm scheduled-export floor
that the ladder *displaces under rule 19* on the years it covers. The 2019 run
would not be the keeper's seam model; it would be the keeper's **rule-19
alternative**, chosen by a year key rather than by a decision.

This is not a peripheral flag. pjm-153's item 15b established that PJM's
net-export shortfall is governed by the model's own price-duration curve
*measured on the seam*, and that the ladder is what prices that structure. A
locked-test result on 2019 would be a result about a seam representation no
keeper has ever been scored on, in the exact channel that carries PJM's largest
single-signed volume error.

> Note the code is *correct as written* — the year gate is the honest way to
> express "measured on the years the measurement exists, formula elsewhere," and
> the same two-track design governs `hr_by_year`. The defect is not the code; it
> is that "spend the frozen keeper config on 2019" is not a well-defined
> operation while a load-bearing armed mechanism is year-keyed to the training
> window.

### §3.2 — two overlays are pooled on the training window by construction

- **`measured_ramp_capability`** — `scripts/lib/ramp_capability/__init__.py:54`:
  `POOLED_VINTAGES = (2023, 2024, 2025)`, with the module docstring stating
  *"2022 and 2026 are [the designated holdouts] … excluded by construction"* —
  an explicit rule-22 quarantine constant. A 2019 solve would apply
  2023–2025-derived ramp envelopes to a 2019 fleet. Separately, its clean
  partition is gitignored and `load_measured_ramp_capability` **raises** rather
  than degrading (pjm-119), so it must be rebuilt before any solve.
- **`measured_ct_heat_rates`** — the artifact carries one pooled row per
  `plant_code` with `years == "2023-2024-2025"`, keyed on plant code alone. The
  register already grades the vintage exposure **DEGRADED (accepted)** for
  out-of-training years (N-P3). On 2019 it applies training-window heat rates to
  a materially different fleet; any plant that ran in 2019 but not 2023–2025
  falls back to its eGRID rate.

Neither is fatal by itself, and both are honestly labelled. But on a
**touch-once** test, "accepted-degraded" inputs cannot be revisited after the
fact — the whole point of the tier is that the number stands.

### §3.3 — the DA-virtual corpus is not on disk and its loader refuses to degrade

`pjm_da_virtual_bids = True` in the keeper. `data/raw/pjm-da-virtuals/` in this
container contains **only its README** — the corpus is gitignored under PJM's
DataMiner redistribution restriction, and `fetch_pjm_da_virtuals.py` defaults to
`--years 2023 2024 2025`. The loader is deliberately strict
(`src/market_sim/data/virtual_bids.py:231, 336`): it **raises** on a missing
month, *"the mechanism never silently…"* degrades.

Retention is indefinite per the directory's own README, so 2019 is fetchable —
but fetching it is **rule-22 channel-1 data intake for a locked-test year** and
needs its own explicit, session-logged owner authorization. It is a step, not a
wall; I record it so it is not discovered mid-spend.

---

## §4 — B3: the locked-test price gate would use a different statistic *(new)*

`scripts/calibration_verdict.py::score_price_mean` (rubric v2.4) selects its
actual from a four-rung ladder:

```
rt_lw  >  da_lw  >  rt  >  da        # lines 1250-1257
```

PJM's committed bench parts carry `rt_lw`/`da_lw` for **2023, 2024, 2025 only**.
I checked all four committed parts directly:

| bench part | `da` | `rt` | `da_lw` | `rt_lw` | gated basis |
|---|---:|---:|---:|---:|---|
| PJM 2022 | 67.30 | 68.79 | — | — | **RT (LEGACY equal-hour)** |
| PJM 2023 | 29.33 | 28.44 | 30.51 | **29.55** | RT (load-weighted) |
| PJM 2024 | 29.78 | 29.53 | 31.60 | **31.31** | RT (load-weighted) |
| PJM 2025 | 43.71 | 42.89 | 46.58 | **45.80** | RT (load-weighted) |

**The basis shift is large against the band.** Load-weighting raises PJM's RT
actual by **+1.11 / +1.78 / +2.91 $/MWh = +3.9 % / +6.0 % / +6.8 %**. C3a's band
is `PRICE_MEAN_TOL = 0.10` (±10 %). Restating the keeper's own gated C3a on the
legacy basis it would be forced onto outside 2023–2025 (model levels 31.43 /
31.18 / 42.35 from the committed verdict):

| C3a | on `rt_lw` (as gated) | on `rt` (the fallback) | Δ |
|---|---:|---:|---:|
| 2023 | **+6.4 %** PASS | **+10.5 %** → would **FAIL** | +4.1 pp |
| 2024 | **−0.4 %** PASS | **+5.6 %** PASS | +6.0 pp |
| 2025 | **−7.5 %** PASS | **−1.3 %** PASS | +6.2 pp |

A basis change alone moves the keeper's own 2023 C3a **across the gate
boundary**. On an iterable tier that is a footnote. On a touch-once tier it means
the certified number is not comparable to any in-sample number, in either
direction, and cannot be re-scored once spent.

**And it cannot simply be fixed for 2019, because it has the same root as B1.**
`lw_retrofit` (`scripts/data/derive_actual_lmp.py:963-1071`) calls
`eia_loader.load_demand(iso, year, …)` to build the weights — the F3-blocked
artifact. The register records exactly this for NYISO 2026 (line 342: *"`lw_retrofit`
skips 2026: `load_demand` has no … series (the full-8760 demand contract — the
cross-ISO F3 blocker)"*). So **B1 and B3 close together or not at all.**

**Also recorded, retrospectively:** the already-spent 2022 touchpoint was scored
on the legacy equal-hour basis for C3a while every in-sample number is
load-weighted. Its `caveat` field carefully establishes availability-envelope
parity and correctly claims the in-sample→holdout *delta* is like-for-like on
that axis — but the **price-statistic basis is a separate non-parity that nobody
recorded.** 2022 is iterable, so this is a note to carry, not a defect to
repair; it should be stated when that touchpoint's C3a is quoted.

---

## §5 — B4: is the pjm-158 DA/RT basis defect disqualifying?

**For the keeper: no.** pjm-158's rule-14 disposition is right, and I am not
re-opening it. The layer is real measured DA depth, disarming it is worse on
every load-bearing and supporting gate, and rule 1 forbids rejecting real
structure to improve a residual just as firmly as it forbids keeping a fitted
one. The cell stays `K`.

**For the validation tier: no.** 2022 is iterable and re-runnable after any fix.

**For the touch-once locked tier: YES, disqualifying** — and the reason is
sharper than "there is an open defect." It is that **the defect's contribution
is regime-dependent, and 2019 is a different regime.**

The layer's C1 contribution is, to first order,
`ΔEnergy ≈ −(DA − RT) × dNet/dλ × 8760`, with the measured gain
`dNet/dλ = −440 / −463 / −340 MW per $/MWh`. So the whole exposure is set by the
year's DA−RT spread. Reading that spread straight off the committed bench —
**measured data only, no model output, no scoring** (the same class of read
pjm-157 and pjm-158 §1 performed):

| year | DA | RT | **DA − RT** | tier |
|---|---:|---:|---:|---|
| 2018 | 34.12 | 34.15 | **−0.03** | (outside grant) |
| **2019** | **25.54** | **25.44** | **+0.10** | **LOCKED TEST** |
| 2020 | 19.99 | 20.24 | **−0.25** | (outside grant) |
| 2021 | 36.87 | 37.14 | **−0.27** | (outside grant) |
| 2022 | 67.30 | 68.79 | **−1.49** | validation (SPENT) |
| 2023 | 29.33 | 28.44 | **+0.89** | train |
| 2024 | 29.78 | 29.53 | **+0.25** | train |
| 2025 | 43.71 | 42.89 | **+0.82** | train |

**The sign flips.** Every tuned year has DA **above** RT (+0.25 to +0.89, and
+0.29 to +0.96 on the load-weighted basis the scorer uses). Every year outside
the tuned window is at or below zero except 2019, which is **+0.10 — an order of
magnitude smaller than any training year.**

Three consequences for a locked-test spend:

1. **The in-sample near-cancellation is a property of the 2023–2025 regime, not
   of the mechanism.** pjm-158 already said the cancellation is *"a coincidence
   of two large opposing errors"* (basis +5.8/+4.6/+6.6 against model price error
   −12.5/−9.6/−5.9). This table shows the *first* term is regime-specific too.
   On a year where DA−RT ≈ 0, the basis term largely vanishes and the model's own
   price error stands alone and uncancelled.
2. **A 2019 result is uninterpretable in either direction.** A miss cannot be
   attributed between forecast error and a layer whose phantom energy changed
   regime; a pass cannot be trusted, because it may be the two terms failing to
   cancel *in a favourable direction*. That is the precise condition the freeze
   was declared to prevent — *"a MISS would be uninterpretable … and a PASS would
   be actively misleading, because the locked tier is touch-once and cannot be
   re-scored"* — applied to a second, independent input defect.
3. **It will get worse before it gets better.** The standing pjm-158 warning
   holds and I re-state it: improving C3b toward RT — the stated goal of PJM's
   price lane — *grows* this layer's phantom demand toward +5 to +7 TWh, toward
   the condemned pjm-102 clamp. Any PJM price-shape work must expect this
   mechanism's C1 contribution to move against it. Spending the locked test
   before that lane resolves means certifying a model whose known trajectory is
   to break the certified number.

**What would make it non-disqualifying** (either, not both): the architecture
question is resolved (the LP gains a DA/RT distinction, or the layer is
re-anchored to the price the model actually produces); **or** the owner accepts
the spend with the regime dependence explicitly recorded as a stated limitation
of the certified number, in the declaration itself. The second is a legitimate
owner choice — it is just not a choice a session may make silently by declaring
the number clean.

---

## §6 — the pjm-135 M4 net-interchange defect

**Status: open, no charter, and structurally asymmetric in the direction the
error actually runs.**

- **The error.** On the keeper's own attested net position (attestation
  free-parameter entry 14): model **30.41 / 23.66 / 27.53** TWh net export vs
  measured **39.98 / 32.83 / 32.93** — **one-signed in all three years at
  −9.57 / −9.17 / −5.40 TWh. The model always under-exports.**
- **The bound is on the wrong side.** `pjm_external_net_position_cut` is armed,
  and `build_pjm_external_net_position_cut_groups`
  (`src/market_sim/model/interchange/pjm.py:293`) is explicitly
  **`bidirectional=False`**: *"the cap bounds how import-heavy the net position
  may be and never bounds net export."* So the model's only statement about its
  net position constrains the direction the error is **not** in.
- **It demonstrably absorbs perturbations.** pjm-158's A/B is the proof: removing
  the virtual layer sent **+1.00 / +0.67 / +0.37 TWh** of the withdrawn supply
  straight into the star node, which is why P1's point predictions missed. A free
  sink of that size, in a year nobody has solved, silently rebalances whatever a
  locked-test perturbation does.
- **And it has no charter, by design.** pjm-153 collapsed item 15b into the
  owner-declared-closed frontier: the binding side is the model's own price
  duration curve (deep export bands never clear because the model is too dear at
  the bottom — p5 +$7.32/+$7.57/+$7.36 above actual), i.e. the flat-stack
  amplitude defect measured on the seam. Chartering it *"would re-open the
  frontier under a new name."*

**Verdict on this item alone: NOT independently disqualifying.** It fails no
gate, it is fully disclosed, and its root cause is a declared representation
boundary. But it compounds B2 and B4: the seam is simultaneously (a) the channel
whose armed mechanism silently swaps on 2019 (§3.1), (b) bounded on only one
side, in the direction the error is not, and (c) the sink that absorbed pjm-158's
perturbation. A locked-test miss would partially leak into an unbounded node
whose mechanism differs from the keeper's.

---

## §7 — the CAMPD economic-layup residual: the freeze's `lifts_when`

**Freeze state at this session's HEAD (`305688a4`), stated precisely.** The file
reads `active: false` — but that is a **transient, NEISO-only lift** granted
2026-08-06 (session neiso-86) for exactly one spend: re-solving **NEISO** 2022 on
the corrected gas-basis input. Its own `lift_scope` says *"Nothing else is
authorized and nothing else may be spent — … NOT 2019 or H1-2026 … and NOT any
other ISO,"* and it is re-armed in the same session by design, so *"the file's
steady state remains FROZEN."* **PJM is authorized nothing by it.** Every
governance statement in this assessment holds unchanged.

**And the discrepancy an earlier draft of this section flagged is now RESOLVED on
the record — in favour of the freeze.** `holdout-freeze.json`'s `lifts_when`
requires that the merit-order-guard charter *"reaches a decision — either the
corrected detector is adopted and each affected ISO's keeper is re-audited on the
corrected envelope, or the charter is closed with cause."* The charter says that
condition is met on its *explained* branch (evidence below) and **recommends
closing with cause and lifting fully.** The 2026-08-06 owner entry shows that
recommendation was **put to the owner and declined**:

> *"charter section 9 records the investigation CLOSED ON EVIDENCE across four
> lanes … with a recommendation to close with cause and lift FULLY — **but the
> owner deliberately did NOT take that broader step here**, so every other
> out-of-training year for every ISO stays preserved."*

So the freeze's basis is a **live owner decision made today**, not an unnoticed
contradiction. That strengthens the HOLD: the standing instrument protecting the
locked tier was affirmed on the same date as this assessment.

**The charter's evidence, for completeness.**
`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §9 (*"Residual
over-count investigation — CLOSED on evidence; the freeze-lift decision is now
the owner's"*) records all three steps done, no LP solve used:

- step 1 **DONE, PASSED** — the residual tracks ISO-NE's published
  `uncommitted_available_gen_nonfast_mw` at +0.70…+0.85 and is *anti*-correlated
  with published outages (−0.85/−0.86);
- step 2 **DONE, NEGATIVE** — the commitment-economics mechanism has no
  discriminating power (per-unit AUC 0.47–0.57, below the marginal test in every
  one of 18 configuration-years; sign inverts on the seam population);
- LANE B (day-grain replacement) **closed on a negative** — 82 of 180 cells, a
  coin flip, median gain −0.0003;
- the LP-side closure **closed on a negative** (neiso-68).

Its own conclusion: the over-count is a **definitional seam** (published series
measure *unavailability*, the CEMS detector measures *non-operation*), *"explained,
quantified, bounded … and shown not to be closable by a detector change. That is
a cause, not a stall"* — i.e. the §7 **"Closed with cause"** leg fits, and
*"its stated condition … is now met on the explained branch."*

**And the owner's 2026-08-06 answer to that recommendation was HOLD** (quoted
above). The `holdout-freeze.json` `reason` and the `complete.PJM` marker's
`freeze_interaction` field both continue to carry the residual as the freeze's
standing basis, which is now consistent with that decision rather than in tension
with it.

**In any case, lifting the freeze would not make PJM ready.** B1–B4 are all
independent of it, and B1 and B3 are data-availability facts no governance act can
change.

---

## §8 — the precedent: what spending `final` early actually costs

NEISO is the only ISO to have spent its locked test, and the record is
unambiguous (`calibration-complete.json` `complete.NEISO`):

```
locked_test:            "SPENT, NOT RE-GRANTABLE. … scored ONCE with the
                         frozen neiso-53 config on 2026-07-07 and STANDS"
locked_test_scored_on:  "2026-07-07-neiso53-winter-fuelsec-coldsnap"
keeper (today):         "2026-08-05-neiso-83-ca1-reclass"
keeper_at_declaration:  "2026-07-08-neiso-54-steamgas-ct"
```

The one-shot was scored on `neiso-53`. The keeper moved to `neiso-54` **the next
day**, and stands at `neiso-83` a month later. NEISO's honest out-of-sample
number describes a model thirty generations stale, and the policy correctly
refuses to re-grant it.

PJM today is in a *better* position than NEISO was — a cleared queue, a declared
frontier, zero caveats — but it also carries **three defects NEISO's declaration
did not know about** (§3, §4, §5), two of which were found in the last 48 hours
by sessions specifically looking. pjm-157 found one on 2026-08-05, pjm-158 found
a bigger one on 2026-08-06, and this session found two more. **A lane still
producing material findings at that rate is not a lane at rest.** That is the
strongest single argument for HOLD, and it is an argument about *rate of
discovery*, not about any individual defect's severity.

---

## §9 — what would make PJM ready (ordered; each item is verifiable)

1. **Close the F3 demand-profile gap for 2019** (cross-ISO, benefits every ISO):
   `eia_demand_profiles{,_meta}.parquet` extended below 2021, then
   `calibration_reference.json` `isos.PJM.2019` + `PJM_2019_renewable_capacity.csv`
   rebuilt by their own committed builders. **Fixes B1 and — via `lw_retrofit` —
   B3 in one step.** No LP required.
2. **Build PJM 2019 `rt_lw`/`da_lw`** (`derive_actual_lmp.py --lw-retrofit`,
   unblocked by step 1) so the locked-test C3a is on the same statistic as every
   in-sample number. Verify the committed 2023–2025 rows re-derive byte-identically.
3. **Resolve the year-keyed-recipe question (B2)** — an owner decision, not a
   session's. Either (a) derive `PJM_SEAM_LADDER_BY_YEAR[2019]` from the 2019 tie
   file + 2019 DA LMP with the frozen formula (rule 23: the derive script
   re-derives when the *source data extends*, which is exactly this case — and
   the 2019 tie file is already landed EQUIVALENT at 192,708 rows); or (b) declare
   explicitly that the locked test runs the rule-19 alternative on 2019 and
   record that in the declaration. Silence is the one unacceptable option.
   Same decision for `measured_ramp_capability` / `measured_ct_heat_rates`
   pooled vintages.
4. **Authorize the `pjm-da-virtuals` 2019 intake** (channel-1, no-LP; retention
   is indefinite) — or accept that the keeper's armed layer raises on 2019.
5. **Dispose of B4** — either the DA/RT architecture question is chartered and
   resolved (task B, which needs its own explicit owner authorization because it
   sits inside the pjm-142 frontier), or the declaration records the regime
   dependence as a stated limitation of the certified number.
6. **Lift the freeze for PJM** (owner act). Note the owner declined a full lift
   on 2026-08-06 despite the charter recommending it (§7), so this is a live
   decision to revisit, not a formality — and the current `active: false` state
   is a NEISO-only transient that authorizes PJM nothing.
7. **Then** declare `final`, and spend once: `--year 2019 --holdout-authorized`,
   frozen keeper recipe, result recorded whatever it is, `locked_test_scored_on`
   frozen and never re-keyed (rule 22).

**H1-2026 is a separate question** and will stay publication-blocked for some
time (CAMPD Q2-2026, EIA gas May-2026+, and a half-year that cannot satisfy the
8760 demand contract). Note that `final` as written grants **both** locked years
at once; the owner may want to grant 2019 alone, or to designate the H1-2026
window's handling explicitly, rather than issuing a two-year grant of which one
year is structurally unspendable.

---

## §10 — recorded in passing (no action taken, nothing re-opened)

- **The pjm-158 §5.3 C3a row is not on the C3a gate's basis.** That table reports
  *"+8.8 % → +9.7 %, +2.1 % → +3.5 %, −5.0 % → −6.3 %"*. Re-running the committed
  scorer on both registered arms gives, on the gated `rt_lw` basis:
  control **+6.4 / −0.4 / −7.5 %**, treatment **+6.5 / +0.5 / −9.7 %** (control
  identical to the keeper, as byte-identical dispatch requires).
  **The A/B's conclusion is unaffected and in fact strengthened:** C3a still
  degrades in all three years, and the treatment's 2025 error is **−9.7 %,
  0.3 pp inside the ±10 % band** — it very nearly fails C3a as well as C3c. Both
  arms score `NOT-YET` on C6-unattested alone, exactly as pjm-158 §5.4 reported.
- **C3c, gate basis, both arms:** control 3 / 10 / 32 h vs RT actual 6 / 18 / 59 h
  (PASS, PASS, PASS at 0.56× and 0.54×); treatment 2 / 24 / 22 h → **2025 FAIL at
  0.37×**. Confirms §5.4 and keeper watch-item W2 (model 3/10/32 h) exactly.
- **The three-bases trap generalizes past coal and CC_REGULAR.** pjm-158 §1/§5.2
  documented it for those two classes; §4 above is the same failure mode on the
  *price* side (`rt_lw` vs `rt`). **Before sizing anything against an inherited
  PJM number, check which of the available bases it is on** — for prices that now
  means four (`rt_lw`, `da_lw`, `rt`, `da`), and only 2023–2025 have all four.
- **The cross-ISO bench `npl = 1 MW` defect (task C) is confirmed still open** at
  HEAD and unfixed; pjm-158's inventory stands (PJM 2022: 4 plants / 9.87 TWh;
  also MISO, NEISO, CAISO). Not fixed here — this session's charter is the
  assessment, and the fix touches a shared data builder. It remains the cheapest
  available cross-ISO win and is unaffected by the freeze.

---

## §11 — governance statement

- **Rule 22 (holdout):** freeze respected absolutely. No out-of-training year was
  solved, scored or registered. This session rebased onto `origin/main`
  **`305688a4`** mid-way and re-verified the freeze at that HEAD: it reads
  `active: false` under a **NEISO-2022-only transient lift** (2026-08-06, session
  neiso-86) that authorizes PJM nothing and is re-armed by design — see §7. The
  2019 and 2018–2022 numbers in §4 and §5 are
  reads of **measured committed bench artifacts** with **no model output on
  either side** — the same class of read pjm-157 and pjm-158 §1 performed, and
  the reason they are here is precisely to size a governance risk *without*
  spending the year. The freeze was not lifted, edited, or interpreted as lifted.
- **Rule 16 / rule 12:** no bundle registered, no solve run, so neither applies.
- **Rule 28:** matrix and PJM lever queue checked before writing (§1). No
  mechanism was proposed or tested, so no cell moves and no matrix edit is owed.
- **Rule 15:** no run was produced, so nothing is owed to either dashboard.
- **Rule 27 (`[R-PUSH]`):** Opus, per the model-assignment half. No source file
  ≥300 lines was rewritten; this session adds two new documents and appends one
  log entry.
- **`final` is not declared and cannot be by this session.** The recommendation
  is **HOLD**, and the decision is the owner's.

**Next shorthand: pjm-160.**
