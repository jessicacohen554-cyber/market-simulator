# FFR-5E-H — the procurement channel's HINDCAST arm, measured

**Session:** `ffr-5e-hindcast-arm`, 2026-08-09. **Measurement lane** (owner decision **D-18(a)**
lineage; manager dispatch Addendum AF.4). Branch `claude/ffr-5e-hindcast-arm-k679kt` off
`origin/main` **`e9f99e6`**. Pre-registration: `ffr-5e-hindcast-arm-prereg-2026-08-09.md`,
committed as `bdfd46b` **before either arm was solved**.

**Scope discharged as dispatched.** The channel remains **GATED default-OFF**; nothing was armed
beyond the measurement arm; no keeper, marker, `calibration-complete.json` or backcast-registry
artifact was touched. Both arms register in the **hindcast** namespace only.

---

## 0. THE SENTENCE THE MANAGER IS WAITING ON

> **The procurement channel's hindcast behaviour DEFERS its forecast-default arming question.
> It neither supports nor refutes it, because this hindcast has no power to discriminate — and
> the reason is arithmetic that was pre-registered before the solves, not a result read
> after them.**

The channel did exactly what it is specified to do, cleanly and auditably (R1 exact, R3
coherent, zero invariant flips, byte-clean control). But the **one property whose failure would
actually matter in a forecast — the netting against the economic screen's budgets — is
VACUOUS here**: `entry_decided_mw_by_tech` is **empty in every year of both arms**, so the
screen decided nothing for the channel's netting to net against. The netting was therefore
*not exercised*, not *validated*. Anyone reading this run as evidence that the channel composes
safely in a forecast would be reading a test that did not run.

**This is a DEFER, and it is emphatically NOT a finding of inertness.** Marking the cell `I`
would be wrong for the same reason FFR-SA's PJM electrification cell must not be marked `I`:
the mechanism fired correctly and its effect propagated: what is absent is the *pipeline* at
this vintage and the *contrast* in the screens, not the mechanism.

---

## 1. What was solved

| | control | armed |
|---|---|---|
| run id | `miso-2021-2025-t1ff-armr-ffr5eh-control` | `miso-2021-2025-t1ff-armr-ffr5eh-armed` |
| gate (`meta`, read from the SOLVED config) | `False` | `True` |
| runtime `cache_key` | `42985ca815282871` | `0dc92a27d0782dbc` |
| exit / `leakage_violations` | 0 / `[]` | 0 / `[]` |
| solved / bridged | `[2021, 2023, 2024, 2025]` / `[2022]` | identical |
| invariants | **13/14 PASS** | **13/14 PASS** |

MISO, vintage 2020, 2021–2025, `--forward-from-base --arm realized`. Years sequential within
each invocation; the two invocations **sequential** (rule 12 permits ≤2 concurrent, but only
~10 GB was available and each arm peaked at ~5.9 GB RSS). Both solved **at this head**, i.e.
at/after the FFR-3V-FIX epoch — **condition 2** discharged, no pre-epoch bundle on either side.

**The single non-PASS invariant is I12 (reserve-margin band), WARN in BOTH arms on the same
year (2021, 26.0 % against a [10 %, 25 %] band). ZERO invariant flips between arms.** It is the
same pre-existing WARN FFR-3V-FIX §5.2 reported; it is not this measurement's.

### 1.1 The flag surface, and the cache-key-pin verdict

FFR-5E landed the channel with **no CLI surface** (its measurement was a scratchpad harness over
`evolve_fleet`, no LP solve; its §3.3 recorded the hindcast arm BLOCKED). `--vre-procurement-additions`
was added here under the dispatch's scope guard. **No `ScenarioConfig` field was added** — the
field exists and was already registered by FFR-5E. The flag rides `build_config`'s None-drop
dict (OMIT inherits the shipped default rather than mirroring it as a literal) and is declared
`FromConfig` in `META_RECORD_SPEC`, so the record reads the solved gate and cannot claim an
arming the solve did not carry (the FFR-3R defect).

**CACHE-KEY-PIN VERDICT — PASS, measured before solving:**

| config | `cache_key()` | |
|---|---|---|
| control (flag omitted), this head | `8062ab39ad904049` | |
| control, `origin/main` `build_config` | `8062ab39ad904049` | **identical — the control IS the shipped path** |
| `--no-vre-procurement-additions` | `8062ab39ad904049` | collapses onto the control |
| `--vre-procurement-additions` | `b6fca9a6c67407b0` | **distinct** |
| `ScenarioConfig().cache_key()` | `603c2498bf71d21d` | unmoved (the pinned value) |

---

## 2. R1 — pool reconciliation: EXACT, as pre-registered

The source side was measured and **committed before the solve**; the solve reproduced it to the
megawatt and to the generator id.

```
MISO procured VRE additions: 51 rows, 2414 MW (wind 1380 / solar 1034), 2021-2022
year 2022: procured VRE additions {'solar': 451.0} (451 MW total)
```

| year | ctl wind | ctl solar | arm wind | arm solar | procured | rows |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 26,050.0 | 2,048.0 | 26,050.0 | 2,048.0 | 0.0 | 0 |
| 2022 | *(bridge — pools not stamped)* | | | | **451.0** | **4** |
| 2023 | 26,050.0 | 2,048.0 | 26,050.0 | **2,499.0** | 0.0 | 0 |
| 2024 | 26,050.0 | 2,048.0 | 26,050.0 | **2,499.0** | 0.0 | 0 |
| 2025 | 26,050.0 | 2,048.0 | 26,050.0 | **2,499.0** | 0.0 | 0 |

**Additivity check — armed pool − control pool vs cumulative procured: OK in 2023, 2024, 2025
(+451.0 vs 451.0 each).** This is FFR-3V §6's promise made concrete: the base is the vintage
year-end fleet, so an injected row names capacity demonstrably absent from it.

Per-row provenance (rule 13 attribution, design §3.5) — all four as pre-registered:

| year | tech | MW | zone | plant | gen |
|---|---|---:|---|---|---|
| 2022 | solar | 150.0 | MISO-Illinois | 64393 | GEN2 |
| 2022 | solar | 100.0 | MISO-Illinois | 64738 | HCS |
| 2022 | solar | 200.0 | MISO-Illinois | 64856 | 65009 |
| 2022 | solar | 1.0 | MISO-Illinois | 64866 | USSWC |

**The 2021 cohort was correctly DROPPED** — 47 rows / 1,963.4 MW with effective year 2021, the
non-evolving base year. Pre-registered as required behaviour; observed.

**CONDITION 2, verified in the output rather than assumed:** the control pools seed at wind
**26,050.0** / solar **2,048.0** MW — the FFR-3V-FIX vintage-2020 measured values, **not** the
pre-epoch present-day constants (32,000 / 7,000). Had this run been solved before the 3V epoch,
the 451 MW would have landed on a pool already 3.4× the real fleet and double-counted invisibly.

### 2.1 A defect in my own probe, found and fixed

My first R1 read reported **0 procured rows against a +451.0 MW pool delta** — a mismatch. The
cause was mine, not the model's: the ledger carries **two** VRE keys, and I read the wrong one.
`renewable_additions` is the AGGREGATED pool delta (`zone`/`tech`/`mw` only); `vre_additions` is
the source-tagged per-generator record carrying `source: "procured"`, `eia860_id` and
`generator_id`. Reading the aggregate for provenance silently finds nothing. Fixed in
`scripts/probes/ffr5eh_arm_reads.py` with the distinction written into the docstring so the next
reader does not repeat it. **Recorded because a silent zero is exactly the shape of a false
"the mechanism didn't fire" conclusion.**

---

## 3. R2 — the base-year UNDER-COUNT, stated and NOT absorbed

**Condition 1** of FFR-3V-FIX §6. Capacity commissioned *during* 2021 is in neither the
vintage-2020 seed nor the injection, because 2021 does not evolve.

Measured independently here (vintage-2021 Dec minus vintage-2020 Dec, model zones):

| | vintage-2020 | vintage-2021 | commissioned during 2021 |
|---|---:|---:|---:|
| MISO wind | 26,025.9 | 28,711.2 | **2,685.3 MW** |
| MISO solar | 2,082.0 | 3,273.6 | **1,191.6 MW** |

FFR-3V-FIX §6 carried **2,945 MW wind / 1,160 MW solar**. Mine differ by **−259.7 MW wind
(−8.8 %)** and **+31.6 MW solar (+2.7 %)**. **Both are reported; neither is silently preferred.**
The gap is a zone-set / planned-retirement-off-ramp construction detail, not a disagreement on
direction or magnitude. (The seeded pool the run actually uses — 26,050.0 / 2,048.0 — differs
again by tens of MW from the raw sheet reads for the same reason.)

**The sharp form of R2, which the condition did not anticipate:** of that under-count the channel
can **see 1,963.4 MW in its own source data** (the 47 effective-year-2021 rows) and still cannot
inject it. The under-count is therefore **partly data the channel HOLDS AND DISCARDS**, not
merely data it lacks. It stays the SAFE direction and remains ~2–4× smaller than the over-count
FFR-3V-FIX removed (solar −1,191.6 against the old **+4,952**), but it is not zero and this score
states it rather than absorbing it.

---

## 4. R3 — the T1-FF posture: coherent, small, exactly proportional

| year | metric | control | armed | Δ | % |
|---|---|---:|---:|---:|---:|
| 2021 | *every metric* | — | — | **0.0000** | **0.000 %** |
| 2023 | solar TWh | 3.946905 | 4.816073 | +0.869168 | **+22.021 %** |
| 2023 | VRE TWh | 81.534 | 82.403 | +0.8692 | +1.066 % |
| 2023 | price load-wtd $/MWh | 27.492 | 27.454 | **−0.0380** | −0.138 % |
| 2024 | solar TWh | 3.946113 | 4.815106 | +0.868993 | +22.021 % |
| 2024 | price load-wtd $/MWh | 26.081 | 26.058 | **−0.0226** | −0.087 % |
| 2025 | solar TWh | 3.946905 | 4.816073 | +0.869168 | +22.021 % |
| 2025 | price load-wtd $/MWh | 33.072 | 33.027 | **−0.0453** | −0.137 % |
| all | wind TWh | 77.587 | 77.587 | 0.0000 | 0.000 % |
| all | `dump_twh` (curtailment) | 0.000 | 0.000 | 0.0000 | — |

**2021 is byte-identical in both arms** — the injection is in 2022, so the pre-injection year
must not move, and it does not. That is a free control.

**The energy response is EXACTLY the pool ratio, to zero difference:** armed/control solar energy
= 1.220215 in all three years, against a pool ratio 2499.0/2048.0 = 1.220215, `diff = 0.00e+00`.
Because `dump_twh = 0.0` everywhere, MISO solar is never curtailment-bound and the pool enters
the energy balance linearly — the same proportionality FFR-3V-FIX §5.1 measured on the seed, now
measured on the injection. **The channel adds no curtailment and displaces no wind.**

Prices move **down** by 2–5 ¢/MWh (−0.09 % to −0.14 %) — the right sign for added zero-marginal-
cost energy, and small.

---

## 5. R4 — in-window exit/entry deltas: REPORTED, and they are ZERO

FFR-3V-FIX §5.3 recorded R4 as a **failed pre-registered read** and explicitly did not claim the
answer. **This session is the first read, over a full five-year window.** The answer:

| ledger | control | armed | Δ |
|---|---|---|---|
| 2022 thermal additions | gas_cc 1,146.0 | gas_cc 1,146.0 | **0** |
| 2022 retirements | nuclear 768.5 | nuclear 768.5 | **0** |
| 2023 retirements | biomass 16.0 | biomass 16.0 | **0** |
| 2024 retirements | coal 6,036.0 | coal 6,036.0 | **0** |
| storage additions | none | none | **0** |
| VRE additions | — | solar 451.0 (`procured`) | +451.0 |

**Every capacity decision in the window is identical between arms.** The only ledger delta is
the 451 MW itself. Reported, never targeted — no parameter was identified against R4 and no arm
was chosen by it.

**The one thing that DID move, and it reconciles exactly.** Reserve margin:

| year | control | armed | Δ observed | Δ predicted = 451.0 × 0.3875 / peak | residual |
|---|---:|---:|---:|---:|---:|
| 2023 | 0.194532 | 0.195978 | 0.001446 | 0.001447 | 9.4e-07 |
| 2024 | 0.141194 | 0.142632 | 0.001438 | 0.001438 | 3.4e-07 |
| 2025 | 0.169075 | 0.170547 | 0.001472 | 0.001473 | 7.9e-07 |

0.3875 is MISO's **published** solar ELCC (the PY2025-26 seasonal mean FFR-4B wired under owner
decision D-12). The accreditation chain is therefore verified end-to-end: procured MW → zonal
pool → accredited firm capacity → reserve margin, with **no unexplained residual**.

### 5.1 WHY R4 IS ZERO — and why that is the load-bearing result

Two structural facts, both measured in these bundles:

1. **`entry_decided_mw_by_tech` is EMPTY in every year of BOTH arms.** The economic entry screen
   decided nothing at all across 2021–2025.
2. **The control builds ZERO renewables in all five years** — `renewable_additions` empty in
   every control ledger, both pools flat at the vintage seed 2021→2025, against a real MISO that
   added ~2,685 MW wind + ~1,192 MW solar in 2021 alone.

Fact 2 reproduces FFR-3V §4.3 (the merchant screen is a **single point of failure** for all VRE)
and **extends it from FFR-3V-FIX's two solve years to a full five-year window**. It is the
strongest confirmation of that finding on the record, and it is exactly the defect FFR-5E's
channel exists to close.

Fact 1 is what disarms this measurement. **The netting — the channel's key composition property
(§2.3(b)), the thing FFR-5E demonstrated in a 2027 forecast where procured 2,510.7 MW pushed
economic wind 4,000.0 → 2,489.3 to land exactly on MISO's 5,000 MW queue budget — had NOTHING TO
NET AGAINST here.** It is **vacuously satisfied, not tested**. A hindcast in which the screen
never decides cannot tell you whether the channel double-counts against a screen that does.

---

## 6. The verdict, and what would change it

**DEFER.** Concretely, against the pre-registered §5 criteria:

* **SUPPORTS?** No. That required the downstream effect to show the netting working. The netting
  did not run.
* **REFUTES?** No, and nothing here is adverse. R1 exact, additivity OK, provenance complete,
  2021 byte-identical, zero invariant flips, energy exactly proportional, reserve margin
  reconciling to <1e-6, prices the right sign.
* **DEFERS?** Yes — and this was pre-registered as the most likely outcome, from arithmetic
  available before the solves: 81.3 % of the vintage-2020 pipeline (1,963.4 of 2,414.4 MW) lands
  in the non-evolving base year, leaving a 451 MW treatment, and the screen it must compose with
  is silent.

**What a discriminating test would need** (routed, not done here, and none of it is this
session's call):

1. **A vintage whose pipeline horizon reaches into the evolving years.** At vintage 2020 the
   committed MISO pipeline ends in 2022. A later vintage (or an ISO with a longer committed
   queue) puts real MW into years the screens actually decide.
2. **A posture where the economic screen decides something**, so the netting is exercised rather
   than vacuous. As long as MISO's screen builds zero VRE, no hindcast in this ISO can test the
   netting — which makes the FFR-3V §4.3 defect a *precondition* for testing its own fix.
3. The FFR-5E forecast measurement remains the only place the netting has been demonstrated, and
   it was a no-LP harness. **A forecast arm with an LP solve is the missing evidence**, not a
   longer hindcast.

**The arming decision is a future owner card and this session does not pre-empt it.** What this
run adds to that card is: the mechanism is correct and auditable where it fires, and the
hindcast cannot speak to the composition risk.

---

## 7. Findings routed to other owners

1. **The harness leakage guard has no VRE limb.** `assert_pipeline_from_vintage`
   (`scripts/run_capacity_hindcast.py`) iterates `thermal_additions` only and matches
   `source == "planned"`, so `source: "procured"` rows get **no automatic vintage trace** —
   `leakage_violations: []` on the armed arm is silence, not a clean bill. R1's additivity check
   covers it manually for this pair. Not patched here: the guard is shared with every hindcast
   and widening it mid-measurement was out of lane.
2. **Ledger key ambiguity** — `renewable_additions` (aggregate) vs `vre_additions` (source-tagged)
   in the same ledger, §2.1. It cost me one wrong read and will cost the next reader one too.
3. **MISO zone siting** — all 51 rows collapse to MISO-Illinois (48) / MISO-South (3) while their
   true states are MN 15, IL 10, MI 8, WI 7, IA 6, AR 2, IN 2, LA 1; all four injecting rows are
   WI/IA/MI/MN and all four land in MISO-Illinois. Pre-existing `assign_zone_by_coords` gap
   (FFR-5E §7), shared identically with the thermal limb. Carried in from the pre-registration,
   not discovered late.

## 8. What this session did NOT do

* **Did not arm the channel anywhere.** It ships GATED default-OFF; no `ISOConfig` override.
* **Did not add a `ScenarioConfig` field**, and did not move the default cache key.
* **Did not touch a keeper, a marker, `calibration-complete.json`, or the backcast registry.**
  Both arms are hindcast-namespace only.
* **Did not solve an out-of-training backcast year.** Solve years are 2021–2025 hindcast windows
  (the T1-FF carve-out); the holdout freeze was ACTIVE at launch and is recorded in both metas;
  no marker was read or spent.
* **Did not patch the leakage guard** (§7.1) or the zone helper (§7.3).
* **Did not re-run or re-score any committed leg**, and did not reinterpret FFR-3V-FIX's numbers
  — where mine differ (§3) both are shown.
* **Did not test the netting.** §5.1. Stated as untested rather than reported as passing, which
  is the single most important sentence in this document.
