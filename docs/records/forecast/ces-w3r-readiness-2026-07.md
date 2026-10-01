# CES W3-R readiness verification — GO / NO-GO (FF-3B)

**Session:** FF-3B (Opus). **Evaluated at HEAD:** `57ed9fc` (session-start main; the branch
`claude/ces-w3r-readiness-poc-x4s903` is rebased onto the current remote main `415df68`,
which force-advanced mid-session with a capacity-cost/reserve intake that touches **neither**
the registered `-ff2a` hindcast bundles, the CES path, nor the `scenarios.py` defaults this
verdict rests on — so the verdict is unaffected; a fresh re-solve at `415df68` is a lane
re-measure, out of scope for a §2.1b committed-evidence readiness read). **Deliverable:** the
explicit W3-R go/no-go the CES plan §8 specifies
(`docs/handoffs/national-ces-eac-premium-plan-2026-07.md` §7 R1–R4, §8 W3-R).

## Verdict: **NO-GO** for the W4 premium-ladder campaign

R1 and R2 are **clear blockers**; R3 is **met**; R4 is **partial** (its named PJM-I7
prerequisite landed, but a new multi-year I4 leak and the frozen/unverified golden keep
final sign-off open). W4 (2026–2050, both ISOs) is in any case **deferred behind the
forecast program's §2.1b full-solve authorization gate** — so this verdict does not itself
"block" anything schedulable today; it is the readiness record that routes the open items
to their lanes, and the §2.1b(b/c) evidence a future gate-open ask will cite.

**The T1-scale CES POC (this session's other deliverable) proceeds regardless of this
verdict** — see §"Relationship to the POC". The POC is a machinery/plumbing proof at ≤5
solve-years and draws **no** capacity-expansion or premium-ladder conclusions; it is
decoupled from the R1–R4 screen-fitness gate by construction (§0 Phase A: "every forecast
parameter a golden run would lean on … exercised end-to-end in a T0/T1 solve", independent
of whether the screens are yet fit for *conclusions*).

| Criterion | Verdict | One-line basis |
|---|---|---|
| **R1** VRE entry (ERCOT+PJM solar materially nonzero vs lane acceptance) | **NOT MET** | ERCOT solar **0.0 GW vs 25.08 actual** (exact zero); PJM builds solar but overshoots (19.32 vs 13.07). R1 needs *both*. |
| **R2** ERCOT exits (over-fire corrected; false-retire collapses from 96%) | **NOT MET** | Armed probe fixes the *magnitude* (1.87 vs 1.53 GW) but composition **inverts 100% onto gas_st** (unit-recall 0.0, LOYO recall_pass=False); the named revenue-basis fix is explicitly **open**. |
| **R3** PJM exits (fossil economic exit arithmetically possible) | **MET** | PJM coal economic exit **11.54 GW, unit-recall 76.5 % (band PASS)**, T-R10/LOYO ≥2/3; BLK-9 broken. |
| **R4** Regression (golden green; I1–I14 on fresh BAU) | **PARTIAL** | W2-D landed → PJM I7 passes; ERCOT 14/14 single-year; F923 forecast-leak fixed. But a new I4 multi-year leak (A1) is open and the golden band-test is frozen/unverified vs HEAD. |

---

## Scope & method (why this is not a fresh 2026–2050 re-run)

The CES plan's original W3-R prompt (§8) said "re-run ERCOT + PJM BAU forecasts
(2026–2050)". That instruction predates the **2026-07-19 owner §2.1b amendment**, which caps
every schedulable invocation at **5 solve-years** and defers all 2026–2050 (T2/T3/W4)
solves behind a per-ISO authorization gate. A 25-year ERCOT+PJM re-run is exactly the
W4-scale compute §2.1b withdraws. Readiness is therefore evaluated the quarantine-legal way
now available:

1. **Committed capacity-hindcast bundles** (`frontend/data/hindcast/…-ff2a*.json`) — the
   T1-H instrument is "the primary capacity instrument" (plan §2.1). R1/R2/R3 are read
   directly from each bundle's `score.json` (`additions.by_tech`, `retirements.per_fuel`,
   `retirements.unit_recall_gt300`, `loyo`).
2. **Lane findings docs** — FF-2A entry stack, FF-1B ERCOT availability, FF-1A retirement
   rule, FF-2B adequacy, the retirement-calibration plan.
3. **Source defaults** — the `ScenarioConfig` HEAD defaults that decide whether a
   correction is *live* in a fresh BAU or only demonstrated in an armed probe.
4. **A fresh ERCOT T1 smoke** — ERCOT 2026 BAU at HEAD defaults solved clean in-session
   (2.7 min, 3.22 GB, **I1–I14 0 FAIL / 0 WARN**), confirming the golden posture resolves
   and the invariant harness is green on the reference ISO.

**Evaluation basis caveat (load-bearing — see Nuance 2):** R2's magnitude fix and R3's
whole mechanism are demonstrated in **armed probes** (`retirement_rule="pipeline"`,
`capacity_market_clearing` ON), not at HEAD defaults (`retirement_rule="legacy"`,
`capacity_market_clearing=False`). The readiness criteria (§7) are written against "the
lane's hindcast acceptance", i.e. the armed probes — so R1–R4 are graded there. The
default-posture flips that would make them live are the owner-gated **FF-2C** decision,
not yet executed.

---

## R1 — VRE entry (blocks everything): **NOT MET**

R1 requires the BAU forecast to build **materially nonzero solar (and wind) in *both* ERCOT
and PJM**, validated against the lane's hindcast acceptance (~25 GW-class ERCOT, ~13
GW-class PJM through the window).

- **ERCOT solar = exactly 0.0 GW vs 25.08 actual** (band FAIL) — a *pure zero*, not a
  small miss (`frontend/data/hindcast/ercot-2021-2025-realized-comp-ff2a.json` →
  `score.additions.by_tech.solar`). ERCOT wind builds 20.0 vs 12.66 (over, FAIL).
- **PJM solar = 19.32 vs 13.07 actual** (band FAIL but **recall > 0** — solar entry is
  alive, it over-builds) (`pjm-2021-2025-realized-cmc-ff2a.json`).
- FF-2A's own verdict is explicit: **"R1 verdict: PJM ✓ (recall > 0, over-build
  tightening), ERCOT ✗ (still 0)"** (`docs/handoffs/ff-entry-stack-completion-2026-07.md:77`).
  ERCOT solar zero is measured as a pure term-(a) **price-signal residual** — the screen's
  best-year entry margin for solar is ≈ **−$9.7k/MW-yr** below the entry hurdle (`:270`,
  `:84`), i.e. the ERCOT energy-only price signal alone never clears solar's screen.

**Why R1 fails:** the criterion is conjunctive across ISOs, and ERCOT's exact zero is the
hardest possible miss. PJM half-satisfies it (solar builds, over-tuned). This is the same
root as R2 (the ERCOT screen forms too little scarcity/energy revenue).

## R2 — ERCOT exits: **NOT MET** (magnitude reduced, composition + revenue-basis open)

R2 requires the ERCOT economic-retirement over-fire (was ~15× / 22.8 vs 1.5 GW, 96%
false-retire) corrected to lane acceptance, **with the screen scarcity/AS revenue basis
fixed**.

- The R-NEW rule collapses the *gross magnitude*: ERCOT thermal false-retire **22.8 → 1.87
  GW**, near the 1.53 GW actual (`ercot-…-comp-ff2a.json` → `retirements.total_gw`
  model 1.87 / actual 1.534).
- **But the composition is 100 % wrong.** The model retires **1.87 GW of gas_st (actual
  0.0)** while missing every real exit — coal 0.932, gas_ct 0.502, gas_cc 0.08 GW all
  model 0.0 (`retirements.per_fuel`). `unit_recall_gt300.recall = 0.0`;
  `false_retire.frac_of_model = 1.0`; LOYO `holds_2of3.recall_pass = False`, `tr10a/b FAIL`
  in every fold with first-mover fuel `gas_st`. The false-retire rate did **not** collapse —
  it is 100 % of a smaller number.
- **The named fix is explicitly unclosed.** FF-1B landed only the *availability half*
  (`correlated_forced_outage`, now default-True): in-year scarcity forms only on thin
  fleets (2024 Heather, mean $0.87/MWh), and the CT screen residual to the SOM anchor is
  still **≈56 $/kW-yr (event-year) / ≈66 (event-free)** —
  `docs/handoffs/ff-1b-correlated-availability-2026-07-17.md` §3. The revenue-*level* half
  is carried forward as G-20/G-22, not yet re-chartered.

**Why R2 fails:** "false-retire collapses from 96 %" and "screen revenue basis fixed" are
both unmet — the screen still retires the wrong units and under-forms scarcity revenue.

## R3 — PJM exits: **MET**

R3 requires PJM capacity-market clearing calibration (RC-1A → position basis) landed so
fossil economic exit is *arithmetically possible* in capacity-market designs.

- PJM coal **economic exit = 11.54 GW** (vs 6.885 actual), **unit-recall 76.5 % (band
  PASS)**, `tr10`/`loyo` present and ≥2/3 (`pjm-…-cmc-ff2a.json`
  `retirements.per_fuel.coal`, `.unit_recall_gt300`). Exit is not merely possible — the
  screen fires it at hindcast-acceptable recall. This breaks **BLK-9** (fixed payment
  cleared 1.26–4.92× FOM → exit impossible) via the CR-1 sloped curve + P-2B position
  basis + R-NEW.
- **Caveats (do not un-meet R3, routed elsewhere):** (a) PJM over-*depth* — coal model
  11.54 vs 6.885 actual (+68 %) — is a revenue-lane item (RD-4), not a "can't-retire"
  blocker; (b) the flip that makes `capacity_market_clearing` a default (**FF-2C**) is
  owner-gated and **not executed** (`ScenarioConfig().capacity_market_clearing == False`).
  R3 is graded on the armed probe per §7's "lane hindcast acceptance" basis.

## R4 — Regression: **PARTIAL**

R4 requires the golden green and I1–I14 passing on fresh ERCOT+PJM BAU. W1-B flagged R4 as
structurally needing G10/W2-D for PJM's I7.

- **W2-D landed and PJM I7 passes.** `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"] =
  5795/146105` and `ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"] = 1281.7`, both **2026/27 BRA
  Report Table 6/7 cited** (`constants.py:3879, 3962`) — published parameters, not tuned to
  clear I7 (rules 5/13). The T1-F 6-ISO baseline confirms PJM passes I7 (and I12) every year
  at HEAD. ERCOT was 14/14 on the W1-B smoke and re-confirmed 0 FAIL/0 WARN on this
  session's 2026 smoke.
- **B2 F923 forecast-leak fixed (W2-E):** `apply_plant_monthly_fuel_prices` is a no-op
  outside backcast mode — the ERCOT golden forecast is no longer contaminated by measured
  H1-2026 delivered fuel (rule 22).
- **Open — golden not actively verified green:** `test_golden_bands_hold` is gated
  `RUN_GOLDEN_FORECAST=1` (weekly tier, not per-PR) and seeded stale vs HEAD; the golden
  freeze is HELD and the FF-4A regen prompt withdrawn. No fresh green band-check exists.
- **Open — NEW multi-year I4 leak (A1):** the T1-F baseline surfaced an I4
  capacity-accounting leak affecting 4/6 ISOs (e.g. PJM coal 2029 −743 MW) with no fix
  landed. This is a *multi-year* regression the single-year smokes cannot see.

**Why R4 is partial, not met:** the PJM-I7 prerequisite is closed and the reference ISO is
green, but "I1–I14 on fresh *multi-year* BAU" is not established (open I4/A1) and the golden
is unverified against HEAD. Final R4 sign-off belongs to **FF-3E** (full-solve readiness
battery), which owns the multi-year input-resolution + invariant sweep.

---

## Blocking list → lane routing

| # | Blocker | Criterion | Routes to |
|---|---|---|---|
| B-1 | ERCOT solar entry = 0 (energy-only price signal never clears the screen; best-year margin −$9.7k/MW-yr) | R1 | **G-20/G-22 ERCOT screen-revenue-level lane** (frontier §1.2 item 3; FF-2A term-(a) residual). Not yet re-chartered as a discrete FF prompt. |
| B-2 | ERCOT retirement composition inverts onto gas_st (unit-recall 0.0); revenue-*level* basis unclosed (CT residual ≈56–66 $/kW-yr) | R2 | **Same G-20/G-22 lane** (FF-1B landed availability; level residual open). B-1 and B-2 share the ERCOT scarcity/AS-revenue root. |
| B-3 | New I4 multi-year capacity-accounting leak (4/6 ISOs, PJM coal 2029 −743 MW) | R4 | **FF-3E** full-solve readiness battery (input-resolution + invariant sweep, plan §2.1b/§6). |
| B-4 | Golden band-test frozen/unverified vs HEAD | R4 | **FF-3E / owner** (golden regen is a withdrawn FF-4A prompt; re-authored at gate-open). |

**Not blockers (met / owner-gated, recorded for completeness):** R3 mechanism (met);
FF-2C capacity-market + retirement-rule default flips (owner-gated, decision-ready, per-ISO);
PJM coal over-depth +68 % (RD-4 revenue lane).

---

## Two nuances the readiness picture depends on

**Nuance 1 — the frontier's #1 "blocker" row is stale.**
`docs/forecast-development-plan-2026-07.md` §1.2 item 1 still lists the "retirement
decision-rule inversion" (RC-1A-D1) as the top blocker routing to "FF-0C then FF-1A ⛔".
Both **FF-0C (R-NEW memo) and FF-1A (implement + LOYO) merged and verified-pass**; the
inversion is closed (T-R10 PASS, LOYO-robust). This session independently verified the **PJM**
half — coal economic-exit recall is back to **76.5 % (band PASS)** in the R-NEW
(`retirement_rule="pipeline"`) probe, reversing the "recall 76 %→0" elimination the row
describes — and confirmed the `retirement_rule` field + FF-1A implementation doc are on
HEAD. What actually remains is the signal-*level* residual (the revenue lane), not the
decision-rule inversion. Per §7.8 this session **flags** the stale row for the retirement
lane / wave manager to correct; it does not itself rewrite another lane's frontier row,
having verified only the PJM half (not the MISO gas_st half) of the closure.

**Nuance 2 — the R2/R3 corrections live behind default-OFF gates.**
At true HEAD defaults a fresh BAU still runs the **legacy** retirement screen
(`retirement_rule="legacy"`) with `capacity_market_clearing=False`. R2's magnitude fix and
R3's entire mechanism are demonstrated only in the lane's **armed** hindcast probes. The
readiness criteria are graded against that armed acceptance (per §7's wording), but a reader
must not infer that a default-posture 2026–2050 BAU would exhibit R3's clean PJM exits or
R2's reduced magnitude — it would not, until the owner-gated **FF-2C** flip lands. (The
FF-1F/FF-2A posture flips that *did* land are live: `correlated_forced_outage=True`,
`datacenter_load_path="mid"`, `entry_lookahead_reprice=True`.)

---

## Relationship to the CES POC (decoupled from this verdict)

This NO-GO gates the **W4 premium-ladder campaign** — the run that would draw
clean-share-vs-premium and revenue-decomposition conclusions. It does **not** gate the
**T1-scale CES POC**, which this session runs in parallel (ERCOT 2026–2030, `clean_capture`,
BAU + CES-20 + CES-40, registered `kind="ces-poc"`). Rationale:

- The POC's purpose is to prove the campaign **configs, seams and reporting execute
  bug-free at POC cost** (FF-3B item 2) — a plumbing proof, not a conclusion. It explicitly
  draws **no premium-ladder conclusions from a 5-year window**.
- §0 Phase A makes POC-exercising the CES resolver + premium configs a definition-of-done
  item **independent of screen fitness** — indeed the moment you most want a cheap machinery
  proof is *before* the screens are fixed and someone launches a 10-hour run.
- FF-3E's wall/RSS projection (§2.1b(c)) consumes FF-3B's per-year CES ledger — the program
  design assumes FF-3B produces it.
- The owner re-scope note scopes FF-3B to "W3-R readiness **+** a T1-scale CES POC" — both,
  unconditionally; the "On GO" phrasing in the prompt contrasts POC-vs-W4, it does not make
  the POC conditional on a GO.

The premium moves the **full** reporting surface in the POC (clean-share, negative-price
hours, captured-price cannibalization, VRE entry, premium-capture) — exercised without R1–R4
met, which is the point. **Correction (measured in the POC, updating an earlier prediction
here):** the *forward* POC does **not** show ~0 VRE entry — the forward BAU builds **9 GW
solar** (→ 19–20 GW under the premium). This *strengthens* R1 rather than softening it: the
forward entry mechanism builds solar only because forward DC-load/demand-growth/fuel inflate
the price signal, whereas the R1 **hindcast** — the *validation* instrument — shows the same
mechanism yields **0** against realized 2021–2025 prices. The forward solar is therefore
exactly the *unvalidated* forward entry R1 flags; a forward run building it is not evidence
the mechanism works. (Nuance 2's `retirement_rule=legacy` point stands — it governs
retirements, not entry.) POC results, the wall/RSS ledger, and the three findings are in the
companion doc `docs/handoffs/ff-3b-ces-poc-2026-07.md`.

---

## Owner-decision box

1. **W4 launch remains closed** on two counts: this **NO-GO** (R1/R2) *and* the standing
   §2.1b deferral. Opening it needs the ERCOT screen-revenue lane (B-1/B-2) closed **and**
   the §2.1b per-ISO gate conditions + a fresh per-campaign authorization.
2. **B-1/B-2 need a discrete charter.** The ERCOT scarcity/AS-revenue-*level* residual
   (G-20/G-22) is the single root under both R1 and R2 and is not yet a numbered FF prompt.
   Recommend the wave manager charter it before any CES-campaign gate ask.
3. **R4 closes under FF-3E**, not here — the I4/A1 leak and the golden regen are its scope.
4. **The CES machinery is POC-proven** (companion doc) regardless of the above — the CES
   layer is not on the readiness critical path; the *ERCOT screens under it* are.
