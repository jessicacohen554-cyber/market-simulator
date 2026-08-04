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

**Candidate 2, and the mechanism is storage ACCREDITATION, not build volume — candidate 1 is
provably inert (ΔRM = 0.0000 pp, all three years), and candidate 3 moves the wrong way.**

The +18.04 pp overshoot at the corrected ceiling decomposes **exactly** (closes to the digit):

| term | pp | what it is |
|---|--:|---|
| **Already in the vintage-2023 fleet** | **+4.69** | present at 2023 *before the model evolves anything* — a **fourth term nobody named** |
| **Storage economic entry** | **+11.34** | 96.4 % of all firm-capacity growth |
| Peak decline (84,617 → 83,573 MW) | +1.58 | |
| Planned thermal (356 MW, EIA-860 exogenous) | +0.43 | not economic entry |
| **Candidate 1 — retirement rule** | **0.00** | measured inert on a 677-field-clean pair |
| **Candidate 3 — band basis** | **−6.60** | why the ceiling is 22.15 %, not 28.75 % |

And the storage term is **not an over-build in MW**. The model adds 5.0 GW/yr of storage
against ERCOT's actual 4.1/5.6 GW — comparable nameplate. It is a **duration/accreditation**
divergence: the entry screen builds 100-hour iron-air and 8-hour CAES accrediting at **94.8 %**,
while ERCOT's real storage fleet is **14,114 MW at a capacity-weighted 1.54 h** (median 1.00,
p90 2.06, **zero MW above 4.5 h** — EIA-860, measured), which accredits at **≤ 40 %** on the
model's *own* ELCC curve.

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

**Posture:** ERCOT, `--forward-from-base --vintage 2023 --start-year 2023 --end-year 2025
--arm realized` — the FH-1 §3.3 gate posture exactly, re-solved COLD at this session's HEAD.

| arm | `--retirement-rule` | cache key |
|---|---|---|
| **A — shipped default** | omitted (inherits `pipeline`) | `d9a630ade1c48216` |
| **B — legacy control** | `legacy` | `d24d0c24213e07d4` |

Cache keys verified **distinct before either arm was read**. The two logged config dicts were
diffed mechanically: **677 fields each, exactly ONE differing** — `retirement_rule`. Arm A
reproduces the target number, **40.1939 %** in 2025 (FFR-3F: 40.2 %), so the phenomenon is
confirmed at this HEAD and not an artifact of a stale run.

### 3.1 Candidate 1 — REFUTED, and the pre-registered prediction held

| year | ΔRM (pipeline − legacy) | exits, pipeline | exits, legacy |
|---|--:|--:|--:|
| 2023 | **+0.0000 pp** | 0.0 MW | 0.0 MW |
| 2024 | **+0.0000 pp** | 0.0 MW | 0.0 MW |
| 2025 | **+0.0000 pp** | 0.0 MW | 0.0 MW |

Every ledger field is identical between arms. `pipeline_events` is **empty in every year** —
not just no `executed` rows but no `decided` rows either, and `decided` fires on the *first*
failing year under D = 0. **Zero units failed the screen's bar in any year**, which is exactly
what §3 of the pre-registration predicted from the code: both rules consume the same `margins`
list and apply the identical `net_revenue < going_forward_cost` bar
(`retirements.py:1425` / `:2029`), differing only in post-failure calendar. With no failures
there is nothing for the calendar to act on.

**The retirement rule cannot be the cause of the inversion at this posture, and swapping it
back would not move the margin by one basis point.** FFR-3F's `L_coal` observation (a 2024
decision executes in 2027, outside the window) is true but not load-bearing: nothing is
decided in the first place.

> **What this does NOT license.** The rule is inert *here*, not in general. FFR-3F §10.1
> already established that a 3-year window is the wrong instrument for an exit mechanism. This
> result is evidence about **this posture**, and the matrix cell stays `O` (§5) rather than
> flipping to `I`, so a successor is not blocked from testing the rule where exits execute.

### 3.2 Candidate 2 — CONFIRMED, and the mechanism is accreditation, not volume

Accredited firm capacity decomposes exactly (ERCOT accredits thermal at `seasonal_rating`
= 1.0, so the thermal leg is exact; reconstruction residual 817 MW = 0.7 %, consistent with
storage firm MW being recorded pre-dilution):

| leg (MW) | 2023 | 2024 | 2025 | Δ |
|---|--:|--:|--:|--:|
| thermal | 78,171 | 78,527 | 78,527 | **+356** |
| wind | 8,400 | 8,400 | 8,400 | **0** |
| solar | 7,980 | 7,980 | 7,980 | **0** |
| **storage** | 11,688 | 16,428 | 21,168 | **+9,480** |
| hydro | 276 | 273 | 273 | −3 |
| **firm total** | 107,328 | 112,424 | 117,164 | **+9,836** |

**Storage is 96.4 % of all firm-capacity growth.** Wind and solar contribute *nothing* — the
screen builds zero of both.

The storage the screen selects, per year (identical 2024 and 2025):

* **3,000 MW iron-air at `duration_h = 100.0`** → ELCC **1.00** (curve tops out at 24 h)
* **2,000 MW compressed-air at `duration_h = 8.0`** → ELCC **0.87**
* ⇒ 4,740 MW firm from 5,000 MW nameplate = **94.8 % accreditation**

Against ERCOT's measured reality (`eia860_energy_storage_operable`, TX, 207 units with both
MW and MWh):

| | model's build | ERCOT actual fleet |
|---|---|---|
| nameplate added 2024 / 2025 | 5,000 / 5,000 MW | 4,120 / 5,615 MW |
| duration | 100 h and 8 h | **cap-wt 1.54 h**, median 1.00, p90 2.06 |
| MW above 4.5 h | 5,000 MW/yr | **0 MW, of 14,114 MW total** |
| accreditation on the model's own curve | **94.8 %** | **≤ 40 %** |

So the volume is roughly right and the **technology is not**. This is a rule 14 `[R-ACCURATE]`
finding: the entry screen's technology selection does not reproduce the observed build, and the
margin error is the accreditation consequence. Had the same 5 GW/yr been built at ERCOT's
actual ~1.5 h duration, the storage term would contribute roughly 2 GW/yr of firm capacity
instead of 4.74 GW/yr — most of the +11.34 pp would not exist.

**Route check (candidate 2's "through which route").** Confirmed independently before solving:
`resolve_reserve_margin_build_enabled(ERCOT) = False` (ON for all five other ISOs), so the
step-6 administrative backstop is **not** the channel — consistent with FFR-3H. The ledger
agrees: zero `reserve_backstop` rows. The thermal additions that do occur are **`planned`**
(356 MW, EIA-860 exogenous pipeline), not economic entry. Because `load_planned_additions`
skips wind/solar/hydro/storage by construction, **every storage MW here is step-5 economic
entry** — the split is exact from the ledger alone, no reconstruction needed.

### 3.3 The fourth term nobody named

At 2023 — the **first** solve year, before the model evolves anything — the margin is already
**26.84 %**, which is **+4.69 pp above the corrected ceiling** of 22.15 %. A quarter of the
2025 overshoot is a property of the **vintage-2023 initial fleet and its accreditation**, not
of any evolution mechanism. No candidate in the charter covers this, and none of the three
could have explained it.

It also decides the verdict label. Against the two ceilings:

| basis | 2023 | 2024 | 2025 | consecutive out | I12 |
|---|:--:|:--:|:--:|:--:|:--:|
| as I12 scores it (28.75 %) | in (26.84) | out (32.26) | out (40.19) | 2 | **WARN** |
| model's own basis (22.15 %) | **out** | out | out | **3** | **FAIL** |

`reserve_margin_consecutive_fail = 3`, so **correcting the basis flips I12 from WARN to FAIL.**
Reported, **not acted on** — the band is not touched in either direction (§1.3).

---

## 4. What this evidence does NOT separate — stated plainly

Mirrors FFR-3C §5 and FFR-3F §7. A partial attribution honestly bounded is worth more than a
complete one that overreaches.

1. **It does not separate the five-way confound between FH-1's probe and FFR-3F's re-probe
   (§2).** The arms isolate `retirement_rule` at a **fixed HEAD**, which is what makes the
   candidate-1 refutation clean — but it says nothing about how much of the *swing* from
   FH-1's 21.05 GW over-retirement to today's 0.000 GW is owed to
   `correlated_forced_outage`, `entry_lookahead_reprice`, `entry_rate_limits`,
   `entry_commissioning_lag`, or the cap-grain fix. **That decomposition is still open**, and
   it needs a 2×2 (or 2⁵) at a fixed HEAD, not a comparison against FH-1.
2. **It does not explain WHY the entry screen picks 100-hour iron-air over the 1–2 h lithium
   ERCOT actually builds.** This lane measured *that* it does and what it costs in accredited
   MW. The root cause lives in the storage value stack (arbitrage + RA capacity value,
   `STORAGE_TECH_BUILD_SHARE_CAP`, the duration-ELCC curve that rewards long duration) and
   needs its own charter. **No parameter was touched here, and none should be moved to close
   this residual** (rules 11/23) until that lane identifies the cause.
3. **It does not explain the zero wind and zero solar build.** ERCOT actually added 4.9 GW
   wind and 18.6 GW solar across 2023–2025; the screen builds none. That is a *second*
   entry-side defect, plausibly the same root cause, and it is **not** separated from the
   storage finding here.
4. **It does not explain the +4.69 pp already present in the vintage-2023 fleet (§3.3).**
   Measured, decomposed out, unattributed. It could be the initial fleet, the accreditation
   bases, or the peak — this lane did not test which.
5. **It does not establish that 40.2 % is "wrong" in absolute terms.** No ERCOT-published CDR
   reserve-margin series is in the repo, and the model's gross-peak basis is not ERCOT's
   published firm-peak basis anyway. What is measured is narrower and firmer: the model's
   storage **duration mix does not match ERCOT's actual fleet**, and that divergence is worth
   +11.34 pp of margin. The 817 MW (0.7 %) reconstruction residual is likewise reported, not
   absorbed.
6. **Rule 25 `[R-ISO-SCOPE]` — this is ERCOT only.** Nothing transfers to another ISO. ERCOT
   is also the *only* ISO exposed to the §1 band defect (I12's scalar branch fires only for
   energy-only ISOs) and the only one with the step-6 backstop off.
7. **It does not validate the retirement rule anywhere.** §3.1 is inertness at one posture on
   one ISO, not evidence about the rule's correctness.

---

## 5. Mechanism matrix (rule 28)

`economic_retirement_screen`, ERCOT cell: **stays `O`** with the evidence note extended.
Deliberately **not** flipped to `I`: the rule is measured inert *at the FH-1 3-year gate
posture*, and FFR-3F §10.1 established that window is the wrong instrument for an exit
mechanism. Flipping to `I` would invoke the DO-NOT-REDO discipline and wrongly block a
successor from testing the rule at a posture where exits execute.

No `ScenarioConfig` field was added, so duty (c) is not engaged. Nothing was armed, so no
other cell moves.

---

## 6. Open blockers

* **B-1 — the storage entry technology selection.** 100-hour iron-air at 94.8 % accreditation
  vs a measured 1.54 h real fleet. Worth +11.34 pp of reserve margin. Needs its own lane;
  **do not tune the ELCC curve or the tech-share cap to close it** — identify the cause first.
* **B-2 — zero VRE entry** against 23.4 GW actually built. Possibly the same screen defect.
* **B-3 — the +4.69 pp vintage-fleet term.** Present before any evolution; unattributed.
* **B-4 — the five-way confound (§2)** between the two runs whose difference defined "the
  inversion".
* **B-5 — I12's ERCOT basis defect (§1).** A finding about the invariant's definition, for
  owner decision G.5. It flips the verdict WARN → FAIL. There is no test asserting the
  energy-only branch's basis; the capacity-market branch is tested, the scalar branch is not.

**FH-4/FH-5 remain BLOCKED** (Addendum G.2). Nothing here lifts them and this report does not
claim to. G.5 and D-9 are untouched.
