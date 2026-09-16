# RESULT — neiso-110 screen: the dual-fuel exemption is real, unearned, and NOT load-bearing

**Session** neiso-110 · **ISO** NEISO · **PRECOMMIT**
`docs/PRECOMMIT-neiso110-coldsnap-dualfuel-2026-09-16.md` (written and pushed before the solve).
**Phase-0 evidence** `docs/FINDING-neiso110-winter-oil-driver-2026-09-16.md`.

**VERDICT: the screen KILLS the arm as a fix for oil.** Gate G5 fails its pre-registered
non-triviality threshold by two orders of magnitude. **The remaining five years are NOT
spent** (rule 29 `[R-SCREEN]`). The keeper is UNCHANGED.

**One LP solved** (2022, one shard, ~6 min). No control solve (G-DRIFT form 4; the keeper's
committed bundle is the control).

---

## 1. GATE TABLE — SCORED AGAINST THE PRECOMMIT, NOT REWRITTEN AFTER THE FACT

| gate | criterion | measured | verdict |
|---|---|---|---|
| **G1** | footprint identity, ±2 % | dual-fuel in-window/out-window capacity ratio **0.82074** vs predicted **0.81775** — **0.37 % off** | **PASS** |
| **G2** | window confinement | out-of-window `frac` is identically 0 by construction (`np.where(window, frac, 0.0)`); guarded by `test_partial_mask_derates_exactly_the_unswitched_hours` | **PASS (by construction + test)** — see §5 for what was *not* measurable |
| **G3** | exemption purity | `test_switch_always_active_is_byte_identical_to_legacy` | **PASS (by construction + test)** |
| **G4** | non-dual invariance | `test_non_dual_rows_are_untouched_by_the_gate` | **PASS (by construction + test)** |
| **G5** | **oil rises AND gas falls, both > 10 % of own control value** | oil **+1.32 %**, gas **−0.00 %** | **FAIL** |
| **G6** | no load-bearing criterion flips PASS→FAIL | largest class move **0.00237 %** of ISO load; C3a −6.205 % → **−6.120 %** (*toward* the bench) | **PASS** |
| **G7** | slack/dump do not increase vs control | slack 0.000000 → 0.000000; dump 0.000000 → 0.000000 | **PASS** |

**G1 is the important PASS.** The mechanism did *exactly* what its arithmetic said it would:
on the coldest derated day (doy 16, `frac` = 0.18225) dual-fuel capacity inside the cold-snap
window is 4,230.2 MW against 5,154.2 MW outside it. The derate fired, on the right units, at
the right magnitude. **The arm is not broken — it is immaterial.**

## 2. WHAT MOVED

Single-delta verified: for 2022 the arm's only `ScenarioConfig` difference from the keeper is
`neiso_coldsnap_derate_dualfuel_unswitched`. (`gas_price_override` 2.03→6.45 and
`weather_year` 2020→2022 are the keeper's own *per-year* values — its `calibration_flags`
table gives 2022 → 6.45 — and the control's `run_config.json` records its span's first year.
`coal_fuel_inventory` / `hydro_cascade_coupling` read `<absent>` vs `False`: fields that did
not exist at the keeper's basis, both default-off.)

| class | control | arm | Δ TWh |
|---|---:|---:|---:|
| oil | 0.1307 | 0.1324 | **+0.00172** |
| CC_REGULAR | 51.0758 | 51.0773 | +0.00148 |
| CC_CHP | 0.4760 | 0.4772 | +0.00123 |
| ST_GAS | 0.2225 | 0.2231 | +0.00064 |
| CT_CHP | 0.4484 | 0.4473 | −0.00110 |
| CT_PEAKER | 1.9190 | 1.9166 | −0.00238 |

Price: mean 85.550 → 85.628 (**+0.09 %**), **max unchanged at 249.47**, hours > $300 **still
zero**, hours > $200 114 → 123. 1,423 hours saw some price change.

**Every direction is right and every magnitude is ~2 orders of magnitude too small.** Oil
moves **+0.0017 TWh against a 1.72 TWh gap — it closes 0.1 %.**

## 3. WHY IT DOESN'T WORK — MEASURED, NOT INFERRED

**The reserve co-opt stayed completely dormant.** In the arm, exactly as in the control:
**0 nonzero reserve duals in 26,280 family-hours**, zero shortfall, `held_mw` still sitting
exactly on the requirement. Removing ~779 MW of unearned exemption at the Elliott derate was
absorbed with **zero slack and zero dump**.

So the documented chain — *derate → reserve shortage → RCPF co-opt prices scarcity → >$300
tail → the oil fleet clears* — is broken, and now we know **where**: at the first link, and
by a margin no version of this mechanism can cross.

### THE NUMBER THE NEXT LANE NEEDS

At Elliott the model's **minimum thermal headroom is 6,959 MW** against a total reserve
requirement of **3,600 MW** (1,800 + 1,200 + 600). The system is **3,359 MW clear of binding
at its tightest Elliott hour.**

| | MW removed at the Elliott derate |
|---|---:|
| this screen (dual-fuel exemption removed) | ~779 |
| **required to make reserve bind** | **3,359** |
| derating **100 % of all NEISO gas** (17,565 MW) | **1,985** |

**Even the physically maximal version of this entire mechanism falls ~40 % short of
producing a single reserve-short hour at Elliott.** The cold-snap derate channel cannot be
the explanation for the missing tail, at any admissible magnitude. That is a stronger and
more useful result than the screen's own verdict, and it retires a whole family of candidate
levers rather than one.

## 4. WHAT THIS DOES AND DOES NOT ADJUDICATE

**STANDS — the exemption is genuinely unearned.** The parent derate exempts 6,896 MW (39.3 %
of NEISO gas capacity) on the stated premise that `apply_dual_fuel_pricing` has switched
those units to oil. That premise is `mc = min(gas, oil)`, and at Elliott gas ran
$12.54–15.08/MMBtu against an oil parity of $20.985 — the switch was $5.9–8.4/MMBtu from
firing. The phase-0 finding is unaffected by this screen, and the correction is structurally
right.

**REFUTED — it is not the fix for ISO-NE's winter oil burn.** The capacity the exemption
protected is not what keeps the oil fleet out of merit. That was the hypothesis; it is now
measured false.

**A decision for the owner, not for this session** (§7): the code is correct, gated,
default-off and tested. Rule 1 `[R-STRUCT]` says a structurally-correct mechanism is not
judged by the residual — but it also does not oblige arming an immaterial one. Arming it buys
**correctness, not accuracy**: +0.0017 TWh of oil and a C3a that moves 0.085 pp toward the
bench.

## 5. WHAT I COULD NOT MEASURE, STATED RATHER THAN GLOSSED

**G2/G3/G4 were verified by construction and unit test, not by bundle differencing.** The
keeper's committed bundle is *slim* and carries **no `unit_hourly` parquet**, so there is no
control unit-level array to difference the arm against. The code path is a single
`np.where(window, frac, 0.0)` and the three properties are covered by
`tests/iso/neiso/test_neiso_coldsnap_dualfuel_exemption.py`, but a reader should know these
three are argued from code plus test rather than from two bundles. G1, G5, G6 and G7 are
measured from the bundles.

**The screen's own out-of-window dual-fuel capacity varies across 253 distinct values** —
driven by the CAMPD outage overlay and commitment, not by this mechanism. That is why a naive
"did anything change outside the window" gate on the *bundle* would have been meaningless
here, and why G2 was written against the availability construction instead.

**What the bundle *does* show, measured and reported at full magnitude.** Of 43,800 zone-hour
price rows, **35,605 (81.29 %) are BIT-IDENTICAL** to the control. Two things follow:

1. **There is no dependency-version drift.** The shard flagged pandas/pyarrow/pydantic
   versions differing from the control's solve environment. Had that perturbed the solve
   numerically, essentially *no* row would be bit-identical; 81 % identical says the solver
   path is reproducible and every change is the mechanism's own. The concern is answered.
2. **Prices propagate outside the derate window, and the propagation is not trivial.**

| | rows | changed | mean abs Δ | max abs Δ | total abs Δ |
|---|---:|---:|---:|---:|---:|
| in-window | 1,680 | 1,525 (90.8 %) | $1.7576 | $9.1877 | $2,680.41 |
| out-of-window | 42,120 | 6,670 (15.8 %) | $0.1757 | $3.1465 | $1,172.03 |

**30.42 % of total absolute price movement lands outside the derate window.** That is an
order of magnitude more than the ~0.13 % cyclic-storage coupling neiso-109 documented, and it
should be stated rather than filed under the same precedent: neiso-109 changed a *fuel price*,
whereas this arm removes *capacity*, which changes commitment and run patterns and therefore
propagates much further through an 8760-hour LP with cyclic storage. **It is not a window
violation** — the availability array this mechanism writes is confined to the window by
construction (`np.where(window, frac, 0.0)`), and total generation moves +0.00161 %
(100.367599 → 100.369217 TWh), i.e. the solve is essentially energy-conserving. But a price
confinement gate would have fired on it, which is exactly why G2 was not written as one.

## 6. A LEAD THE NEXT LANE SHOULD TAKE SERIOUSLY

The 3,359 MW shortfall says the model simply carries **too much available capacity** at
Elliott. The largest single candidate, found in phase 0 and deliberately set aside there:
**the model serves 1,483.6 GWh across Elliott against a measured ISO-NE 1,711.6 GWh** — about
**1,900 MW of load the model does not carry**, peak 15,596 MW vs 17,297 MW actual.

Handle with care: that gap is **systematic, not Elliott-specific** (annual model/actual
demand ratio 0.856 vs 0.867 across Elliott), so it is very likely a definitional boundary —
imports and losses — rather than a miss. But it is the right size to matter: carrying the real
load would cut headroom to ~5,059 MW, and *combined* with a full-gas derate (1,985 MW) that
would cross 3,600 MW and bind. **Establishing what the model's demand boundary actually is,
and whether the oil fleet sits inside or outside it, is worth more than any further derate
work.**

## 6b. TEST BASELINE — ZERO REGRESSIONS, MEASURED NOT ASSUMED

The code change is additive and default-off, but that was verified rather than asserted.
`tests/unit tests/scoring tests/regression` was run in full on this branch and the failing
set compared, test-by-test, against a clean `origin/main` checkout of the same 20 files:

| | failures |
|---|---:|
| this branch | **64** |
| clean `origin/main` | **64** |
| only on this branch (regressions introduced) | **0** |
| only on `origin/main` (silently fixed) | **0** |

The two sets are **identical member-for-member** (`comm -23` and `comm -13` both empty). All
64 are pre-existing infrastructure/golden drift owned by other lanes — notably 2 NYISO
keeper-stamp failures (`2026-09-13-nyiso-232-st-gas` in the matrix vs
`2026-09-14-nyiso-235-gas-repair` in the keeper shard) and 1 NYISO solve-surface pin, both of
which the matrix guard already flagged at this session's start and neither of which is this
lane's to fix (rule 25 `[R-ISO-SCOPE]`).

One test *was* legitimately changed by this work and is fixed here, not suppressed:
`test_fleet_unification.py::test_coldsnap_wrapper_threads_config_fields` asserted the exact
call signature of `inject_neiso_gas_coldsnap_derate`, which now takes
`dual_switch_active=None` on the legacy path. The baseline count is 65 → 64 accordingly.

The cache-key pin is separately guarded and passes: `test_caiso_ra_mpb_anchor.py`
(`547053bdfccd4264` unmoved) and `test_persisted_identity.py[NEISO]`
(`9d35c270c69e9eee`, 197 rows, `moved {}`).

## 7. ARTIFACTS, RETRIEVABILITY, AND THE PROMOTION QUESTION (rules 31 / 34)

* **Screen bundle**: `results/calibration/neiso110_dualfuel_screen_2022` — **pushed and
  retrievable**, 17 files including `dispatch/2022_P1.parquet`, on shard branch
  `claude/neiso110-screen-2022` at full SHA
  **`7b82a4c08039c04f348884dfad894e196a9a16fb`**. Recover with
  `git archive 7b82a4c08039c04f348884dfad894e196a9a16fb results/calibration/neiso110_dualfuel_screen_2022 | tar -x`
  (never `git checkout <sha> -- <path>`, which stages the bundle).
* **Nothing has been deleted** (rule 31 `[R-RETAIN]`). The working-tree copy does not survive
  this container; the shard branch does.
* **THE PROMOTION QUESTION, ASKED EXPLICITLY:** there is **nothing to promote as a keeper** —
  this is a one-year screen, never registrable (rule 29), and it does not improve the model
  materially. What *is* an open owner decision is **whether to merge the code** (gated,
  default-off, byte-identical off) as a standing structural correction, and if so whether to
  arm it on the NEISO keeper. My recommendation: **merge the code, do not arm it** — the
  exemption is genuinely unearned and the correction should exist, but arming it changes
  nothing worth a re-solve of six years, and it would spend a DOF-ledger line for +0.1 % of
  the gap.
