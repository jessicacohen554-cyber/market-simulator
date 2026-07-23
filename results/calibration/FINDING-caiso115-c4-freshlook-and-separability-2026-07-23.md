# FINDING — caiso-115 FRESH-LOOK: C4 is NOT the intractable frontier — it is ~75 % sub-ceiling day-to-day scatter (a mild reduced-network limit) + ~25 % fixable diurnal structure that is the SAME belly-import (C5a) and evening-displacement (C3c) defect; the keeper already PASSES C4 in 2/3 years on the clean CEMS basis and its sole fail (2023) is a benchmark-basis artifact; C5a-fix and C3a-guard ARE separable (different hours, different mechanisms) (2026-07-23)

**Measurement-only, NO SOLVE, nothing registered.** Keeper
`2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}). This is
the caiso-114 handoff's fresh-look diagnosis charter: answer the two questions —
(A) can the C5a-fix and the C3a-guard coexist, and (B) what is C4 — with
measurement, not another offer-curve tweak. All numbers reproduce from committed
artifacts + raw EIA-930 via `scripts/probes/_caiso115_c4_freshlook.py` (no LP).
The keeper carries no `hourly/` sidecar, so the model hourly work uses the
same-machine keeper-proxy `caiso104_m1_B` (reproduces the keeper's C4 gas
digit-for-digit: 2023 r=0.837/nrmse=0.331 vs keeper 0.836/0.333).

---

## Headline

**C4 is not a wall and not the ballgame.** The handoff feared C4 was a genuine
representational limitation that "resisted every mechanism and has never been
decomposed." Decomposed, it is:

- **~75 % irreducible day-to-day scatter** — the reduced 3-zone import/hydro/
  storage model's floor is NRMSE ~0.20–0.25 (below the 0.30 ceiling), a *mild*
  limitation that sits right at the peer-worst boundary (NYISO 0.207).
- **~25 % fixable diurnal structure** — the SAME two defects as the load-bearing
  fails: belly/overnight CC under-dispatch (imports substitute = **C5a**) and an
  evening CT-peaker under-run (evening under-scarcity = **C3c**).

The keeper **already passes C4 in 2024 and 2025** on the clean CEMS basis; its
only C4 fail (2023) is scored on the corruption-prone EIA-930 NG cell and
**passes on the same CEMS basis used for 2024/25**. And the two load-bearing
lanes are **separable**: the belly-volume (C5a) lever and the evening-price
(C3a/C3c) lever act on different hours through different mechanisms — L1b broke
C3a only because the endogenous West coupled them.

---

## Inv 1a — cross-ISO C4 benchmark: CAISO's NRMSE is the sole outlier; its r is in-family; the gate is NOT mis-specified

Every ISO keeper's gas `dispatch_corr`, scored from its committed payload/bench
(gate: r ≥ 0.70, NRMSE ≤ 0.30):

| ISO | gas r | gas NRMSE | per-year |
|---|---|---|---|
| ERCOT | 0.981–0.989 | **0.069–0.078** | PASS/PASS/PASS |
| PJM | 0.932–0.940 | **0.100–0.111** | PASS/PASS/PASS |
| MISO | 0.926–0.945 | **0.146–0.200** | PASS/PASS/PASS |
| NEISO | 0.863–0.912 | **0.121–0.170** | PASS/PASS/PASS |
| NYISO | 0.804–0.888 | **0.170–0.207** | PASS/PASS/PASS |
| **CAISO** | **0.836–0.908** | **0.260–0.333** | **FAIL**/PASS/PASS |

- CAISO's **NRMSE is the sole outlier** — every other ISO clears ≤ 0.207, most
  ≤ 0.17. CAISO is 1.3–1.9× the next-worst (NYISO).
- CAISO's **r (0.836–0.908) is in-family** with the other single-fuel/import-
  heavy ISOs — better than NYISO's low end (0.804). The *shape* correlation is
  not anomalous; the *magnitude* of hourly error is.
- **The gate is not mis-specified.** The handoff's hypothesis ("if everyone
  hovers near the C4 line, the gate may be mis-specified for a reduced-network
  model → escalate") is **refuted**: nobody hovers. 5/6 ISOs pass comfortably,
  including the import-heavy / hydro-carrying NYISO and NEISO. The C4 threshold
  is ambitious but achievable, consistent with the field survey (caiso-111 R4).

Basis caveat (does not change the read): CAISO gas 2024/25 is scored on CEMS
(its 930 NG cell is documented corrupt from 2024-05), while the peers score on
their 930 NG cells. CAISO **2023** is scored on 930 — the same basis as the
peers — and is still the worst (0.333). CAISO is the outlier on both bases.

## Inv 1b — where the gas-hourly error lives: timing, not volume; ~75 % irreducible scatter; belly-CC + evening-CT

Reproducing the gate's exact CEMS-basis gas series and resolving the residual
(model − actual) by hour-of-day, gas class, and SSE component:

| year | NRMSE | flat-bias share | timing share | perfect-hod floor | perfect-hod×month floor |
|---|---|---|---|---|---|
| 2023 | 0.271 | 18 % | **82 %** | 0.237 | 0.202 |
| 2024 | 0.260 | 17 % | **83 %** | 0.221 | 0.203 |
| 2025 | 0.287 | 13 % | **87 %** | 0.251 | 0.225 |

1. **C4 is timing-dominated.** The flat annual volume bias (−895/−755/−617 MW
   ≈ the −8/−7/−5 TWh gas deficit that *is* C5a) is only **13–18 %** of the C4
   SSE. Removing the volume bias entirely would drop NRMSE only 0.27 → ~0.245.
   **Fixing C5a barely moves C4** — this directly refutes caiso-108's "C4 driven
   by C1/C5a, would move once those are fixed," and explains the caiso-114
   paradox (L1b fixed the volume yet C4 stayed bad). C4 and C5a are *different*
   defects.
2. **~75 % of C4 is day-to-day scatter.** Even a *perfect* hour-of-day
   correction leaves NRMSE 0.221–0.251; a perfect hod×month correction leaves
   0.202–0.225. This floor is the reduced-model signature — nodal congestion,
   unit-specific outages, and hydro/import day-specific decisions that a 3-zone
   model integrates over. It is **invariant to the cogen/BTM/fill flat
   approximations** (they shift the mean, not the within-hour variance), so it
   is a robust number. Note it sits right at the peer-worst (NYISO's *actual*
   0.207): CAISO's *best achievable* ≈ the hardest peer's *actual*.
3. **The removable diurnal structure is two real signatures:**
   - **CC_REGULAR under-dispatch, belly + overnight** (−1.0 to −1.3 GW belly,
     −0.65 to −1.1 GW overnight; annual −6.4/−5.6/−4.2 TWh). Imports substitute.
     = the C5a defect.
   - **CT_PEAKER under-run, evening 17–21** (model 0.2–0.9 TWh vs actual
     1.7–3.3 TWh — a **3.3–6.8× under-run**, concentrated in the evening ramp).
     = the C3c evening-scarcity defect.

**2023 benchmark-basis fragility (escalation item).** The CEMS-anchor onset for
CAISO is **2024** (`EIA930_NG_CORRUPT_ONSET`), so 2023 — the *only* C4-failing
year — is scored on the EIA-930 NG cell (0.333 FAIL). On the *same CEMS basis*
used for 2024/25 it is **0.271 → PASS**. The two bases differ by ~0.06 NRMSE,
**larger than the 0.033 margin by which 2023 fails.** The bench-basis FINDING
(2026-07-12 §5.2) kept 2023 on 930 "for continuity — the two agree there"; they
agree on the *annual level* but **not at the hourly-NRMSE grain**. Re-examining
whether 2023 should also move to CEMS is a scorer-only question that would make
the keeper pass C4 in all three years.

## Inv 1c + Inv 3 — the evening merit order: over-hydro + over-import cap the price below the peaker/scarcity rung

Model evening (17–21) merit, keeper-proxy sidecars:

| year | CA load-wtd price | CT_PEAKER | hydro | import | model CT annual max |
|---|---|---|---|---|---|
| 2023 | $65.2 | 511 MW | 4120 MW | 4064 MW | 4314 MW |
| 2024 | $42.5 | 279 MW | 3463 MW | 4322 MW | 4568 MW |
| 2025 | $43.4 | 130 MW | 3399 MW | 4389 MW | 3415 MW |

The evening ramp is filled by **maxed CC + hydro + imports**, capping the price
at $43–65 — below the scarcity tail (C3c FAIL) and below where the peaker fleet
clears en masse. The CT fleet has capacity (model annual max 3.4–4.6 GW), so the
evening under-run is **economic, not capacity-limited.**

Against raw EIA-930 (Inv 3), the over-supply that caps the evening is measured:

| year | hydro evening (model−actual) | hydro belly | import belly (C5a) | import evening |
|---|---|---|---|---|
| 2023 | **+499 MW** | −591 MW | **+2306 MW** | +765 MW |
| 2024 | **+508 MW** | −708 MW | **+2493 MW** | +840 MW |
| 2025 | **+655 MW** | −688 MW | **+1931 MW** | +502 MW |

- **Hydro:** annual energy matches (24.1/21.4/20.7 vs 24.5/22.8/21.3 TWh) but the
  model **over-concentrates it into the evening** (+0.5–0.65 GW) and under-runs
  the belly. The keeper's `hydro_dispatch_envelope` (p95) is **already ON** — it
  cut the over-hydro from ~1.5 GW (caiso-72 STEP-0, envelope-off) to ~0.5 GW, but
  p95 is a *loose* ceiling the perfect-foresight LP saturates every evening. The
  companion lever `caiso_firm_import_shape` (caiso-72 candidate #2) remains
  **off**.
- **Import:** the **belly over-import (+1.9–2.5 GW)** is the dominant C5a/C4-belly
  driver (confirms caiso-109); the evening over-import (+0.5–0.8 GW) is the
  secondary evening filler.

This is one coherent circle: **over-evening-hydro + over-evening-import → price
caps below the scarcity tail (C3c) → CT peakers stay idle (C4 evening residual).**
It is the same evening-displacement caiso-72 diagnosed from a P0 solve; this
session re-derives it independently from the committed C4 series.

## Suspects retired / promoted (Inv 3)

- **Reduced network — mostly RETIRED as the systematic lever, IS the scatter
  floor.** caiso-111 already showed the *systematic* residual is not locational
  (model dump = 0 in every CA zone; the defect is the tie sign/price). The ~75 %
  day-to-day *scatter* is plausibly the nodal-congestion signature a 3-zone model
  cannot resolve — but that part is *below* the ceiling and untestable without a
  nodal build (major; the field survey R4 showed even nodal WECC models publish
  no error bars this tight). Granularity is not a lever for the systematic
  failing part.
- **Hydro shape — PROMOTED to a live (refinement) lever.** The evening residual
  *does* track hydro over-dispatch (+0.5–0.65 GW evening, matched annual). The
  mechanism (`hydro_dispatch_envelope`) exists, is measured/forward-stable, and
  is on — but its p95 setting is loose. Tightening the intra-day shape (lower
  percentile, or a daily rather than monthly budget) is a real, measured,
  forward-reproducible lever, with the caiso-72 disclosed risk (removing ~1.5 GW
  of 2023 evening supply may worsen the 2023 tail — rule 1: keep the real limit,
  chase the root cause).
- **Storage — CHECKED, not the current driver.** The keeper runs
  `storage_vintage_ramp=True` + `caiso_storage_shape_anchor=True` (the caiso-98/99
  corrections). The 2023 storage-oversizing that caiso-98 measured on the old
  caiso-97 keeper (flat 8 GW) is already corrected; the residual evening
  displacement is now hydro + import, not storage fleet size.

---

## Decision framing — classifying CAISO's residual

Per the handoff's ask, each residual sorted into (i) fixable mechanism, (ii)
gate mis-specification, or (iii) genuine representational limitation:

**C5a (belly over-import → gas volume) — (i) FIXABLE MECHANISM.** The belly
over-import (+1.9–2.5 GW) is the dominant driver; L1b (endogenous West) already
proved it is fixable with a forward-stable endogenous structure. Specific
single-delta: a **belly-scoped** import-volume correction (endogenous West, or a
physical belly-import cap) — separable from the evening by construction (it acts
on hod 10–15).

**C3c + C4-evening-CT (evening under-scarcity) — (i) FIXABLE MECHANISM, hard
multi-lever refinement.** The evening over-supply is ~0.5 GW residual hydro
(p95 envelope loose) + ~0.5–0.8 GW import. Levers, both refinements of existing
mechanisms: (1) tighten the hydro intra-day shape (`hydro_dispatch_envelope`
percentile / daily budget); (2) adopt the shaped firm-import base
(`caiso_firm_import_shape`, off). Each tightens the evening → forms the tail →
fires domestic peakers → prices the evening *with the right resource*. **Disclosed
risk:** over-tightening over-prices the evening — this is exactly L1b's C3a break,
which used *expensive imports* (the West hub) to raise the evening instead of
*domestic peakers*.

**C4 bulk (day-to-day scatter) — (iii) MILD REPRESENTATIONAL LIMITATION.** The
reduced 3-zone import/hydro/storage model has an irreducible ~0.20–0.25 NRMSE
floor, near the peer-worst. It is *below* the 0.30 ceiling, so it does not fail
C4 on its own; a successful belly+evening fix moves C4 from ~0.27 to ~0.23
(the perfect-diurnal floor), passing with margin. Document the floor; do not
chase it below ~0.22.

**2023 C4 FAIL specifically — (ii) BENCHMARK-BASIS ARTIFACT (escalate).** On the
clean CEMS basis (2024/25's basis) 2023 passes (0.271). The 2023-on-930 choice
rested on an annual-level "they agree" that does not hold at the hourly grain.
Owner call: re-examine moving 2023 to CEMS (scorer-only, no re-solve) — it would
make the keeper pass C4 all three years and isolate the honest residual.

### Question A — can the C5a-fix and the C3a-guard coexist? **YES.**

The measurement supports separability: the belly-volume defect (C5a, hod 10–15)
and the evening-price defect (C3a/C3c, hod 17–21) are **different hours reached
by different mechanisms.** L1b broke C3a only because the endogenous West is a
*single* structure that fixed the belly volume *and* re-set the evening price to
the West's own internal evening-scarcity hub (over-pricing hours 18–21). Separate
the levers — a belly-scoped import-volume correction + an evening-scoped hydro/
import-shape refinement — and the C5a fix need not touch the C3a evening. The
evening itself *wants* more domestic peaker/scarcity (which raises C3c and prices
correctly), not more expensive imports.

### Question B — what is C4? Is it a model limitation?

C4 is a **mix**: ~75 % a *mild* representational limitation (the ~0.22
day-to-day scatter floor of a reduced-network model, sub-ceiling) + ~25 % a
*fixable* diurnal component that is the same import/evening defect as C5a/C3c.
It is **not** gate mis-specification (peers pass comfortably) and **not** the
intractable wall the handoff feared (the keeper passes 2/3 years on the clean
basis; the 2023 fail is a benchmark artifact). C4 is not the ballgame — it rides
on the belly-import and evening-displacement lanes already in flight.

---

## Recommended next single-delta (derive-first; owner to select a direction)

The measurement re-scopes the caiso-114 handoff's caiso-115 candidates. The
evening lever is **not** "the West's evening pricing" alone (the hydro envelope,
already on, is a bigger evening filler than the handoff assumed). Two clean,
separable, forward-stable A/B deltas, each pre-registerable vs a fresh
`caiso102_repro_A`, 3 years one bundle, in-session (~10 min/yr, strictly one
year at a time), rule-22 LOYO:

1. **Belly (C5a) — endogenous West or physical belly-import cap, belly-scoped.**
   Gate: C5a → 0 (no year > +7 %), belly import → measured, **C3a STAYS PASS**
   (the whole point — do not let the West set the evening price), C4 watched.
2. **Evening (C3c/C4) — tighten `hydro_dispatch_envelope` (percentile / daily
   budget) and/or arm `caiso_firm_import_shape`.** Gate: evening hydro/import →
   measured, CT_PEAKER evening up toward 1–2 GW, C3c tail up, **C3a STAYS PASS**
   (disclosed over-price risk), 2023 tail watched (rule 1).

Do NOT re-run: firm-rung offer reprice (pinned, byte-inert — caiso-109);
belly-depth on any CA-price / west-surplus-quantity observable (caiso-107/109);
a fixed-hub West fallback (caiso-114 charter KILL). Do NOT gate the evening delta
on the ±5 $/MWh belly/evening ladder (it lives inside passing C3a/C3b —
caiso-108).

Full reproduction: `scripts/probes/_caiso115_c4_freshlook.py`.
