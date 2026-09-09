# FINDING — SPP-51c: the oversupply allocation instrument was BUILT, SCREENED and **KILLED on its own pre-registered structural gate** — and, found while validating it, **SPP's committed actual-LMP sidecar is on UTC while the model runs on local time**

**Lane** SPP-51c · **Model** Opus 5 (`claude-opus-5`) · **Date** 2026-09-09 ·
**Branch** `claude/spp-51c-curtailment-allocation-izd5x2` · **Base** `b849a51b` ·
**Data profile** `spp` · **Charter** `FINDING-spp-51b-2026-09-09.md` §5 **R-1** ·
**Pre-registration** `PRECOMMIT-spp-51c-2026-09-09.md` (pushed before any instrument number was
read) + `PRECOMMIT-spp-51c-ADDENDUM-2026-09-09.md` (pushed before the screen ran).

**LP SPENT: ONE screen year (SPP 2025).** No control solve (rule 29(b) form 4 holds — see §6).
The remaining two years were **never spent** (rule 29). Nothing registered, nothing promoted,
`keepers/SPP.json` untouched, keeper-3 stands.

**Outcome partition: 3 — SCREEN STOP.**

---

## 0. Owner report

### 0.1 Two results, and the second one is the bigger

**(A) A defect in a committed scoring input, found while validating the instrument.**
`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet` — the series C3a, C3b and C3c all score
SPP against — **is indexed on UTC while the model's EIA-930 frame is Central prevailing time**
(6 h in CST months, 5 h in CDT). Rubric v2.4 scores C3a against `rt_lw`, *the committed hourly
actual weighted by the same measured demand the model dispatches*, which is an **hour-matched**
pairing, so the offset lands directly on a load-bearing criterion. Corrected, SPP's actual rises
**+0.740 / +0.966 / +0.692 \$/MWh** and SPP-50's C3a moves **+15.0 / +12.1 / +14.2 % → ≈ +11.6 /
+7.9 / +11.4 %**, with **2024 flipping FAIL → PASS**. A six-ISO control census isolates the defect
to **SPP alone**. This lane does **not** land the repair and §4 says exactly why. **No owner card is
opened.**

**(B) The instrument works and is not enough.** The oversupply water-fill allocates the frozen
annual curtailment energy far better than anything before it — it reaches **91.2 %** of SPP's
measured-negative hours against the availability shape's **67.8 %** — and it creates SPP's
negative-price regime for the first time (**177** interior-wind hours, **159** system-LW hours
below \$0, against a control of essentially zero), pricing at **exactly −\$26.00** where it binds.
It still **missed every pre-registered band**, so the screen **STOPped** and the arm is rejected.

### 0.2 Why it missed, which is the transferable result

**The LP absorbs 98.2 % of the concentrated headroom by turning thermal down instead of spilling
wind.** In the 2,848 allocated hours where wind did *not* go interior, thermal averaged 8,454 MW and
**still had 8,200 MW of turn-down available** above its own annual minimum — 2,624 of them with over
2 GW spare. The model's thermal **annual minimum is 254.3 MW across a ~40 GW fleet**, because SPP
carries **zero commitment floors and zero bridges**. Wind can only become marginal once thermal is
already at ~1,316 MW.

**This is direct measured evidence against SPP-51b's own sizing note**, which argued the deficit sat
on the wind side because measured SPP non-wind non-nuclear output in those hours was ~12 GW, "close
to the model's". The model *reaches* that level only by decommitting a fleet the real market cannot
decommit. **The binding limb is R-2, the thermal-commitment floor**, and rule 19 `[R-ONE-MECH]`
applies to any successor: an R-2 floor must be **reconciled with** this allocation, never stacked on
the un-diagnosed residual of the flat rule.

---

## 1. THE CLOCK DEFECT (result A)

Full evidence and the six-ISO census: **ADDENDUM §A**. The load-bearing points:

- Direction and magnitude were fixed by **clock-independent physical markers, before any scored
  number was computed** — EIA-930 SPP solar peaks at hour-index **12 / 13 / 13** (solar noon) and
  load at **17**; the sidecar's RT LMP peaks at **23 / 22 / 23**; SPP's own explicitly GMT-stamped
  GenMix load peaks at **UTC hour 22**, the same index the sidecar peaks at. A −12…+12 lag scan is
  single-peaked at **+5**, and splits **6 h in Jan/Feb + Nov/Dec** vs **4–5 h in Apr–Sep**: CST/CDT.
- **Instrument validated first:** re-computing the *misaligned* `rt_lw` reproduces the committed
  bench exactly — **24.438 / 24.531 / 27.957**.
- **The other six ISOs are clean.** Best lag of corr(load, RT LMP), 2024: CAISO 0, PJM 0, MISO 0,
  NEISO 0, NYISO −1, ERCOT +2, **SPP +5**. The six go through
  `scripts/data/derive_actual_lmp.py`'s `_STD_TZ` registry; **SPP's sidecar bypasses it**, staged
  pre-built by `scripts/data/build_spp_lmp_reference.py`, whose docstring asserts the SPP monthly
  wide files are "already hourly on the local clock". The measurement says they are not.
- **Consequence carried through, not hidden:** the measured-negative-hour sets before and after
  correction overlap by only **41.2 / 36.6 / 43.0 %**, so SPP-51b §2's bucket decomposition and its
  *which-hours* pairing are misaligned (its *counts* — 992 / 1,172 / 1,018 measured, 4 / 7 / 0 model
  — are each computed on one series and stand). Every hour-matched number in this lane is computed
  on the **corrected** alignment, and SPP-51b's availability arm was **re-measured here** rather
  than quoted.

**The repair makes SPP's C3a better.** That is exactly why the ordering is disclosed rather than
asserted: it was found by a pairing that looked wrong, and its direction was set by solar noon.

---

## 2. THE INSTRUMENT (result B) — what it is and what it does at zero LP

`vre_curtailment_oversupply_allocation`, a gated `ScenarioConfig` bool, **default off**,
**ISO-agnostic**, replacing (never stacking on) the flat reference-rate gross-up at the one seam
that builds the renewable bound. With `NL(t) = load − delivered wind − delivered solar`,
`H(t)` the fleet's online-capacity headroom and `C` the **frozen** annual curtailment energy:
`curt(t) = min(max(0, λ − NL(t)), H(t))`, λ the **unique root** of `Σ_t curt(t) = C`.

**Zero new free parameters** (λ is determined by the annual identity and is reported, never set;
the cap is measured EIA-860 capacity; every input is a series the LP already consumes).
**Forward-native** on every leg (rule 13). The annual potential is **identical** to the flat rule's
in every year, so the measured reference rate is untouched (rule 23).

Phase 0, all three allocation rules like-for-like on the corrected clock (annual potential
114.0552 / 120.9925 / 122.2552 TWh for **all three arms** in all three years):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| share of `C` landing in the measured-negative hours — flat rule | 17.01 % | 18.72 % | 16.91 % |
| — availability shape (SPP-51b §3, re-measured) | 32.91 % | 34.33 % | 43.49 % |
| — **oversupply water-fill** | **40.75 %** | **42.68 %** | **43.71 %** |
| mean lift of the bound there — availability | +1,764 MW | +1,553 MW | +3,081 MW |
| — **oversupply** | **+2,634 MW** | **+2,385 MW** | **+3,106 MW** |
| negative-hour **coverage** — availability | 62.9 % | 58.7 % | 67.8 % |
| — **oversupply** | **93.1 %** | **86.0 %** | **91.2 %** |

**Two declared bands MISSED at phase 0 and are reported in the words they were written in.**
F-2's bar was "**≥ 45 %**" and the best year reached **43.71 %** — a miss, not "≈ 45 %". F-4's band
was "**+3.0 to +8.0 GW**" and 2023/2024 came in at **+2.63 / +2.38 GW**, below it. F-1 (identity, no
root), F-3 (breadth 3,090 / 3,173 / 3,025 h) and F-5 (λ 16.15 / 16.48 / 17.58 GW) passed. Neither
miss is partition branch 2, which fires at **F-2 < 20 %** on the stated ground of being "no better
than the availability key" — so the declared partition sent the arm to a screen and **it was
honored rather than the threshold re-cut**.

---

## 3. THE SCREEN — 2025, graded against the pre-registered STRUCTURAL STOP GATE

Screen year selected by the declared rule (largest reallocated energy, **13.587 TWh**), which is
**not** the worst-C3a year. One invocation, keeper recipe plus exactly this one flag. P0 123.6 s
cold (79,905 it.), P1 43.9 s warm (15,477 it.).

| gate | requirement (declared ex ante) | measured | verdict |
|---|---|---|---|
| **G-1a** interior-wind hours | 871 predicted, band **[348, 2178]** | **177** | **STOP** |
| **G-1b** system-LW hours < \$0 | 592 predicted, band **[237, 1480]** | **159** | **STOP** |
| **G-2** footprint confinement | ≥ 90 % | **53.67 %** | **FAIL — but the gate was MIS-SPECIFIED by me; see below** |
| **G-3** wind identity | move toward 1.0, land in **[1.02, 1.09]**, never < 1.00 | **1.10681 → 1.10489** | **STOP** |
| **G-4** C1 non-regression | no passing row may fail; Σ\|err\| not up > 20 % | only wind/solar evaluable in 2025 (preliminary EIA-923 vintage skips the thermal rows); wind 10.68 → **10.49 %**, solar −0.04 → **−0.94 %**, Σ\|err\| 11.799 → **11.607 TWh** | **no regression on what is evaluable** |
| **G-5** C2 / C4 / C6 / C8 | no PASS → FAIL flip | **NOT EVALUATED** — see §5 | **not claimed** |

**G-2 was my specification error and I am not converting it into a pass.** As written it measured
the change against the **flat** bound, which this mechanism moves in *every* hour by construction
(up in allocated hours, down in the rest), so the gate could never have passed. The property it was
meant to test — that the LP's endogenous curtailment is confined to the hours the instrument names
— measures **100.0 %**: all **212,240 MWh** of re-curtailment falls inside the 3,025 allocated hours
and **zero** outside. That is reported as a diagnostic, **never as a gate pass**, and the verdict
does not rest on it: G-1a, G-1b and G-3 each STOP the arm on their own.

**Reconstruction validated before grading:** the bound I rebuild offline matches the LP's to
**0.002 MW** at its maximum, so every gate above is measured against the bound the LP actually got.

### 3.1 Reported at FULL MAGNITUDE and **NOT GATED ON**, in either direction

| | control (SPP-50) | **arm** | actual |
|---|---|---|---|
| C3a (as scored) | +14.2 % | **+12.81 %** | 27.957 LW |
| C3a (on the §1 clock-corrected actual) | ≈ +11.4 % | **+10.08 %** | 28.649 LW |
| C3b monthly NRMSE | 0.253 | **0.2094** | — |
| C3c hours > \$200 | 1 (keeper-3 basis) | **2** | 68 |
| min zonal price | — | **−\$26.00** | — |
| slack / dump | — | 240.6 MWh / 0.0 | — |

**X-2 CONFIRMED:** C3a still FAILS in the screen year on both bases. **X-1 CONFIRMED and then
some:** I predicted the arm would not create the regime, "below 700" system-LW negative hours — it
produced **159**, so I *over*-predicted my own arm by a factor of ~3.7. **X-3 is NOT meaningfully
confirmed:** I predicted at least one reported band would get worse, and the only evaluable band
that did is the **report-only** solar VRE row, by **0.021 TWh** (−0.04 → −0.94 %). Every other
evaluable band moved slightly toward the actual. I am not dressing a 0.021 TWh move up as my
prediction landing.

### 3.2 The absorption diagnostic — why the gate failed, measured on the arm's own sidecars

| hour class | hours | thermal mean | turn-down still available | wind bound | wind spilled |
|---|---|---|---|---|---|
| allocated **and** wind interior | 177 | 1,316.5 MW | 1,062.2 MW | 26,257.7 MW | 1,199.1 MW |
| allocated, wind **not** interior | **2,848** | 8,454.4 MW | **8,200.0 MW** | 20,922.1 MW | **0.0 MW** |
| not allocated | 5,735 | 22,449.5 MW | 22,195.1 MW | 10,117.1 MW | 0.0 MW |

Headroom offered **11.7978 TWh**; actually spilled **0.2122 TWh**; **absorbed by thermal
displacement 98.2 %**. Thermal annual minimum **254.3 MW**.

---

## 4. The clock repair is ROUTED, not landed — SPP-51c R-1

Stated rather than left implied. **(a)** It is a **scoring-basis** change: it re-scores every
registered SPP run and both keepers' determinations, which needs its own pre-registration and is
outside this PRECOMMIT's declared file scope. **(b)** It **cannot be verified end-to-end here** —
the SPP raw monthly settlement-location exports are not staged (`data/raw/spp-lmp-alt/` carries only
`README.md` / `SOURCES.md`) and `portal.spp.org` is blocked to an anonymous caller
(`FINDING-spp-12-2026-09-06.md`), so the sidecar cannot be regenerated from source and a permutation
of the committed file cannot be proved against the publisher's own product. **(c)** `data/raw` is
immutable, so the locus is the builder or the `derive_actual_lmp._STD_TZ` seam, not the file.
The measured effect is in §1 and ADDENDUM §A so the desk can act on it immediately.

**Incidental, not fixed and not mine:** `scripts/run_calibration_full.py --help` raises
`ValueError: unsupported format character ')' at index 1002` from an unescaped `%` in some
argument's help text. **Verified pre-existing on `main`** (stashed this branch and reproduced), so
it is reported rather than folded into this diff.

---

## 5. Honest disclosures

1. **The screen's post-solve report stage died** (no traceback, the log ends mid-report — the same
   OOM-in-report class the SPP price-family lane recorded). **The LP itself completed and wrote
   every hourly sidecar**, so G-1/G-2/G-3 and §3.1/§3.2 are graded from `system_2025.parquet` and
   `class_hourly_2025.parquet`, the same artifacts the scorer reads. **`metrics.json`,
   `calibration_attestation.json` and `legitimacy_diagnostics.json` were never written, so G-5
   (C2/C4/C6/C8) was NOT evaluated and this finding does not claim it.** It does not change the
   verdict: G-1a, G-1b and G-3 are STOPs on their own.
2. **G-4 is only partially evaluable in 2025.** SPP-50's committed payload carries system-level C1
   rows for wind and solar only in 2025 — the thermal classes are skipped on the preliminary
   EIA-923 vintage — so the PRECOMMIT's 2024-specific `CC_REGULAR` / `CT_PEAKER` clause never
   applied (the screen year is 2025) and the thermal rows are simply not scoreable here.
3. **A monitoring error, repeated from a predecessor lane and corrected in the open.** My
   `pgrep -f "run_calibration_full.py --iso SPP"` matched my own polling wrapper shells, so several
   readings reported "RUNNING" after the python process had already died; and one cleanup
   `pkill -f` matched the shell issuing it and killed my own command. Both are the trap the session
   prompt names. Processes were finally identified and terminated **by PID**.
4. **F-2 and F-4 missed their declared bands** (§2) and G-2 was **mis-specified by me** (§3). All
   three are recorded as written, not re-described.
5. **Phase-0 ordering.** The PRECOMMIT was pushed before any instrument number existed; the ADDENDUM
   (footprint, screen year, frozen G-1 predictions) before the screen ran. The clock defect was
   found *between* them and its correction direction was fixed by physics before `rt_lw` was
   computed on either basis.

---

## 6. Rule postures

- **Rule 29 `[R-SCREEN]`.** Phase 0 first and it did most of the work; the screen was ONE year named
  by the mechanism's own largest reallocated energy, not by residual; the gate was structural and
  STOP-only, and it stopped the arm. **The remaining two years were never spent.**
- **Rule 29(b).** **No control solve.** G-DRIFT at code level between SPP-50's registration commit
  `08e486f2` and HEAD is 17 files / 9 commits and **every hunk classifies INERT for an SPP
  backcast** (capx D88's `unit_id` guard, silent on all seven keepers and an evolved-fleet-only
  event; `hydro_budget_period_by_instrument` and `netload_drag_merit_allocation`, both new bools at
  default `False` and absent from SPP's recipe; capx D87's CCS/cache work, on the capacity-evolution
  path a `mode="backcast"` run never enters). Form 4 holds and SPP-50's committed numbers are the
  control. Its missing `hourly/` sidecars are a stated limitation: the control's hourly negative
  census is taken as **structurally zero** (SPP-50 re-curtails 0.00030 % of its 2025 wind, and a
  negative LMP in this LP requires an interior wind column), and **no hour-level control
  differencing is claimed**. Keeper-3 is not the control for anything on the input surface.
- **Rule 31 `[R-RETAIN]`.** `results/calibration/_spp51c_screen_ARM` (41 MB) is **on local disk and
  gitignored** — `.gitignore:1495` covers `results/calibration/_spp51c_*`, which discharges rule
  29(c) in full without an `rm`. **Nothing was deleted.** The promotion question is put explicitly
  in §7.
- **Rule 15 `[R-DASHBOARD]`.** A screen bundle is **never registered** (rule 29 clause 2). Every
  number this lane cites lives in this document and its ADDENDUM.
- **Rule 28 `[R-MECH-MATRIX]`.** New base row `vre_curtailment_oversupply_allocation` **plus a cell
  line in every one of the seven shards, in this PR** (duty (c), CI-verified: "1 new field(s) all
  registered"). SPP's cell is stamped **`R`** in this session (duty (b)). Every other ISO enters at
  its own posture and **no verdict transfers** (duty (d) / rule 25): ERCOT / CAISO / MISO `U` — MISO
  is the most directly applicable, since the flat gross-up is live and unconditional there — and
  PJM / NYISO / NEISO `.` (not in `_UNCURTAILED_FALLBACK_ISOS`). Cells already adjudicated for SPP
  (`offer_curve_by_group` R, `negative_renewable_offers` I, `wind_ptc_vintage_offers` I) were **not
  re-tested**.
- **Rules 21 / 24 / 25.** Zero new free parameters; the field is registered in `ScenarioConfig` and
  in both cache-key structures in the same commit as the field; ISO-agnostic with no SPP constant in
  shared code. Default off, so all six existing keepers replay byte-identical and keep their keys.
- **Rule 27 `[R-PUSH]`.** Every edit local; all four ≥300-line files blob-verified against the
  remote after push (sha and line count identical).
- **Out of scope and not absorbed:** R-2 (thermal commitment), R-3 (zonal spread), C3c / SPP-55, the
  C1-2024 `ST_GAS` Harrington fuel-vintage row. **No owner card opened.**

---

## 7. The promotion question, asked while the bundle is alive (rule 31)

**This session recommends NOT promoting the arm** — it failed its own pre-registered structural
gate, and promoting it on an improved C3a would be exactly the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids. **That recommendation is not a decision and this lane has destroyed nothing.**

The owner may reasonably disagree, because the mechanism is a **rule 14 `[R-ACCURATE]` input
repair** whose case does not depend on the gate: it puts measured energy in the hours it actually
belonged to, at zero DOF, with the annual level frozen, and every evaluable band moved toward the
actual. If the owner wants it promoted, the honest path is a **full-span 2023–2025 bundle** (rule
16) — the screen bundle can never be a keeper.

- **On local disk now:** `results/calibration/_spp51c_screen_ARM`, 41 MB, 2025 only, gitignored.
  **This container is ephemeral: it will not survive the session.**
- **LP cost to reproduce it:** ~3 min of solve for the screen year (P0 123.6 s + P1 43.9 s, plus
  ~2 min of fleet/report overhead).
- **LP cost of the full-span keeper-candidate bundle:** ~10–15 min for `--year 2023 2024 2025` in
  one invocation, years sequential.

Neither cost is large. Nothing is lost if the answer comes later — it just has to be re-solved.

---

## Log entry

```
## 2026-09-09 — spp-19: SPP-51c the oversupply curtailment ALLOCATION — BUILT, SCREENED, KILLED ON ITS OWN GATE; and SPP's actual-LMP sidecar is on UTC while the model is on LOCAL
R-1 executed. ONE screen year spent (2025), remaining two years NEVER spent (rule 29), nothing
registered, keeper-3 unchanged. Outcome partition 3 (SCREEN STOP). RESULT A, found while validating
the instrument and the bigger of the two: data/raw/_validation-source/actual_lmp_hourly_SPP.parquet
-- the series C3a/C3b/C3c score SPP against -- is indexed on UTC while the model's EIA-930 frame is
Central PREVAILING time (6 h CST / 5 h CDT). Direction fixed by clock-independent physical markers
BEFORE any scored number: EIA-930 solar peaks at index 12/13 (solar noon) and load at 17, the
sidecar's RT peaks at 22/23, SPP's own GMT-stamped GenMix load peaks at UTC hour 22, the lag scan is
single-peaked at +5 and splits 6 h in CST months vs 4-5 in CDT. Instrument validated: the misaligned
rt_lw reproduces the committed bench exactly (24.438/24.531/27.957). Rubric v2.4 scores C3a against
rt_lw, an HOUR-MATCHED pairing of the actual price with the model's own demand, so the offset lands
on a load-bearing criterion: corrected actual 25.178/25.497/28.649 (+0.740/+0.966/+0.692) and
SPP-50's C3a +15.0/+12.1/+14.2 -> approx +11.6/+7.9/+11.4 %, 2024 flipping FAIL -> PASS. A six-ISO
census ISOLATES the defect to SPP (best lag CAISO/PJM/MISO/NEISO 0, NYISO -1, ERCOT +2, SPP +5): the
six go through derive_actual_lmp._STD_TZ, SPP's sidecar is staged pre-built by
build_spp_lmp_reference.py and bypasses it. NOT LANDED -- scoring-basis change needing its own
prereg, unverifiable end-to-end (SPP raw exports unstaged, portal blocked), data/raw immutable;
routed as SPP-51c R-1, NO owner card. SPP-51b section 2's hour-matched decomposition is misaligned
(its counts stand); the negative-hour sets overlap only 41.2/36.6/43.0 %, so its availability arm
was RE-MEASURED here rather than quoted. RESULT B: vre_curtailment_oversupply_allocation added
(gated, default off, ISO-agnostic, zero new free parameters, forward-native, annual potential
identical to the flat rule's in every year so rule 23 untouched; lambda is the unique root of that
identity, reported never set). Phase 0 like-for-like on the corrected clock, share of the frozen
energy landing in the measured-negative hours: flat 17.01/18.72/16.91 %, availability 32.91/34.33/
43.49 %, oversupply 40.75/42.68/43.71 %, at 93.1/86.0/91.2 % negative-hour coverage vs 62.9/58.7/
67.8 %. TWO DECLARED BANDS MISSED and are reported as written: F-2's bar was ">= 45 %" and the best
year reached 43.71 %; F-4's was "+3.0 to +8.0 GW" and 2023/2024 came in at +2.63/+2.38. Neither is
branch 2 (< 20 %), so the declared partition sent it to a screen and that was honored rather than the
threshold re-cut. THE SCREEN CREATED THE REGIME AND STILL FAILED: 177 interior-wind hours (predicted
871, band 348-2178) and 159 system-LW hours < $0 (predicted 592, band 237-1480) against a control of
essentially zero, min zonal price EXACTLY -$26.00, but G-1a/G-1b/G-3 all STOP (wind identity moved
only 1.10681 -> 1.10489, re-curtailment 0.1736 % against a measured 9.65 %). G-2 also failed (53.67
vs 90 %) but THAT GATE WAS MIS-SPECIFIED BY THIS LANE -- it measured against the FLAT bound, which
the mechanism moves in every hour by construction; the property it meant to test reads 100.0 % (all
212,240 MWh of re-curtailment inside the 3,025 named hours, zero outside) and is reported as a
diagnostic, never a gate pass. ROOT CAUSE, MEASURED, AND IT RE-POINTS THE OBJECT: the LP absorbs
98.2 % of the concentrated headroom by displacing thermal. In the 2,848 allocated hours where wind
did NOT go interior, thermal averaged 8,454 MW and still had 8,200 MW of turn-down available (2,624
with over 2 GW spare); thermal's ANNUAL MINIMUM is 254.3 MW across a ~40 GW fleet because SPP carries
ZERO floors and ZERO bridges. That is direct evidence AGAINST SPP-51b's own sizing note, which put
the deficit on the wind side -- the model reaches ~12 GW only by decommitting a fleet the real market
cannot. The binding limb is R-2, and rule 19 says a floor must be RECONCILED with this allocation,
never stacked on it. NOT GATED ON, reported at full magnitude: C3a +14.2 -> +12.81 % as scored
(+10.08 % on the corrected actual), C3b 0.253 -> 0.2094, C3c 1 -> 2 h vs 68 actual, C1 wind
10.68 -> 10.49 %, sum|class err| 11.799 -> 11.607 TWh. X-1 and X-2 CONFIRMED (I over-predicted my own
arm 592 -> 159); X-3 NOT meaningfully confirmed -- the only evaluable band that worsened is the
report-only solar row by 0.021 TWh, and I am not calling that my prediction landing. DISCLOSED: the
post-solve report stage died before metrics.json (LP completed, hourly sidecars intact), so G-5
(C2/C4/C6/C8) was NOT EVALUATED and is not claimed, and G-4 is only partly evaluable in 2025
(preliminary EIA-923 vintage skips the thermal C1 rows); a pgrep/pkill pattern matched my own shells,
corrected by killing by PID. Matrix: base row minted with the field + a cell in ALL SEVEN shards in
this PR (rule 28c, CI-verified), SPP stamped R, ERCOT/CAISO/MISO U, PJM/NYISO/NEISO '.'. Rule 31: the
41 MB screen bundle is GITIGNORED and was NOT deleted; the promotion question is asked in the FINDING
section 7 with reproduction costs (~3 min screen, ~10-15 min full span). Incidental, pre-existing on
main and not fixed here: run_calibration_full.py --help raises ValueError on an unescaped % in some
argument's help text.
FINDING: docs/handoffs/FINDING-spp-51c-2026-09-09.md
```

---

# ADDENDUM 2 (2026-09-09, same session) — the owner ruled: PROMOTED, and the clock is REPAIRED

Two owner instructions, both executed in-session:

> *"Just fix it so it's not on utc anymore and then fix so results are local time."*
> *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but
> gates regress that may still be a keeper."*

## A2.1 A CORRECTION TO THIS DOCUMENT'S OWN ADDENDUM: the offset is a CONSTANT +6, not 6/5

§1 and the ADDENDUM read the offset as "**6 h in CST months and 5 h in CDT**", inferred from a
price-vs-load lag scan. **That is wrong on the DST detail and it changes the fix, so it is corrected
here rather than left to stand.** The model's 8760 calendar is **fixed Central Standard Time all
year** — `derive_actual_lmp._STD_TZ`'s `Etc/GMT+N` convention, the clock
`eia_loader._eia_hourly_frame` produces by sorting rows by UTC from local **standard** midnight —
so the correction is a constant **+6**.

Settled empirically, not by reading the convention: measured against SPP's own GMT-stamped GenMix
load **restricted to the DST months, the only hours where the two hypotheses differ**, fixed CST
beats prevailing time in all three years — corr **0.9913 / 0.9391 / 0.9652** vs 0.9815 / 0.9309 /
0.9588, MAPE **2.499 / 5.316 / 3.878 %** vs 3.314 / 5.564 / 4.208 %. The summer peak of the original
lag scan is flat to within 0.015 correlation across lags 4–6, which is why it could not resolve this
and should not have been read as if it could.

**The defect itself is unchanged and unaffected**: the sidecar was on SPP's GMT market interval.
Only the magnitude of the shift moves.

## A2.2 The repair, and how it is verified

`build_spp_lmp_reference.py` asserted SPP's monthly wide files were "already hourly on the local
clock". They are GMT. Fixed at the source (`gmt_dense_to_model_clock`, the **single** definition of
the conversion) for any future fetch, plus a `--repair-clock` mode that re-indexes the
already-emitted sidecars — required because the SPP portal is blocked and the raw monthly exports
are not committed, so the affected files cannot be re-fetched.

**It is a pure re-indexing, verified rather than asserted:** the sorted value set is identical on
every common observation in all three years, the equal-hour annual mean is unchanged to four
decimals (23.4732 / 23.3135 / 27.1112), and non-null counts are preserved.

**Verified against the markers that found the defect:** the sidecar's RT hour-of-day peak moves
**23 / 22 / 23 → 17 / 16 / 17**, matching EIA-930 load's own peak at 17, and the load-vs-price lag
scan moves **+5 → −1**, into the same range as the other six ISOs. Independent corroboration from a
statistic nothing here targets: `actual_amplitude.json`'s SPP `rt_peak_hour` moves 23/22/23 →
**17/16/17** and `rt_trough_hour` **7 → 1** — an overnight trough and an evening peak — while
`rt_range` barely moves (29.53→29.48, 37.37→37.29, 47.12→47.28), as a permutation must.

Downstream, each verified **SPP-only**: `actual_lmp.json` `rt_lw` **24.438 / 24.531 / 27.957 →
25.133 / 25.450 / 28.598**; `actual_tail.json` regenerated with a **zero diff** (C3c's 42/59/68 are
clock-invariant counts, which also proves no other ISO moved); `actual_amplitude.json` as above.

**Stale and deliberately NOT regenerated (rule 25 `[R-ISO-SCOPE]`):** the SPP sidecar is also a
neighbour anchor for `derive_miso_seam_ladders.py` and `derive_neighbor_hr_by_year.py`. Those
committed artifacts and MISO's/PJM's keepers are unchanged by this lane, but are now stale against
their source. Re-deriving them is those desks' call.

## A2.3 The promotion — SPP keeper 4, `2026-09-09-spp-51c-oversupply-curtailment`

Full span `--year 2023 2024 2025`, one invocation, years sequential (rules 12 / 16); keeper-3's
recipe plus **exactly one** field. Reproducibility check: the full-span 2025 P0 objective is
**188,653,999.5344**, identical to the screen's to the cent.

**All three runs re-scored on the same repaired bench**, so this is like-for-like and not a basis
artifact:

| | keeper-3 | SPP-50 (the control) | **this run** |
|---|---|---|---|
| C1 failing rows | **2** (2024 CC_REGULAR −8.60, CT_PEAKER +9.94) | 1 (2024 ST_GAS −8.71) | **1** (2024 ST_GAS −8.23) |
| C3a failing years | 1 (2023 +11.0 %) | **2** (2023 +11.9, 2025 +11.6) | **1** (2025 +10.3 %) |
| C3b failing years | 2 (0.225, 0.233) | **3** (0.235, 0.239, 0.248) | **1** (2025 0.204) |
| C3c | 0/3/1 h vs 42/59/68 | 0/3/2 h | 0/4/2 h |
| C2 / C4 / C6 / C8 | PASS | PASS | **PASS** |

**Against its own control it is better on every criterion and worse on none.** C5a CO2 −2.4 / −1.8 /
+3.1 %; D-10 free-class C1 11/12, all-class 15/16. **Determination NOT-YET**, unchanged from
keeper-3 — C3c fails in all three years (SPP has no scarcity mechanism at all; SPP-55's object) and
C3a/C3b-2025 are marginal misses of a ±10 % and a ≤0.20 band.

**The failed gate is not withdrawn.** §3 stands exactly as recorded: the mechanism failed G-1a,
G-1b and G-3, and the session recommended against promotion. The owner overrode that, on the
standing rule that a structural improvement can be a keeper even when gates do not clear. What the
promotion does **not** do is make the mechanism sufficient: it still reaches only ~15–23 % of the
measured negative hours, and §3.2's root cause — the LP absorbing 98.2 % of the headroom by turning
thermal down to a **254.3 MW annual minimum across a ~40 GW fleet** — is now the SPP desk's leading
lever (SPP-51b **R-2**), with rule 19 `[R-ONE-MECH]` requiring any successor floor to be
**reconciled with** this allocation rather than stacked on it.

**Retention, rules 15 / 31.** The registered bundle is slimmed to exactly keeper-3's committed shape
(4 JSONs + `hourly/{class_band_hourly,class_hourly,storage,system}_<year>`, 3.1 MB). The 121 MB of
`dispatch/`, `floors/` and the extra hourly parts were **moved to a gitignored sibling, not
deleted**. SPP is now at **keeper-only retention** — one registered run — which required converting
this lane's own predecessor citations from run ids to lane/FINDING form, the convention keeper-3's
note had itself recorded.

**DOF ledger unchanged at 3 entries / 1 residual.** The two `identification` labels the builder
defaults to `residual` were carried forward from keeper-3's committed ledger, where the same two
entries with the same values read `measured-physical`; the builder-vs-committed discrepancy is **not
resolved here** and remains SPP-50 R-3.

**Disclosed:** the post-solve report stage was killed again (~4.8 GB, no traceback) after the 2025
price-duration block. The LP completed and wrote every hourly sidecar for all three years, which are
the artifacts the scorer reads; `metrics.json` is written by the **registration** step, not the
solve, so the bundle was never incomplete.
