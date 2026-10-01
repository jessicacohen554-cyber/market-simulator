# FFR-5E-H — PRE-REGISTRATION of the hindcast-arm measurement

**Committed BEFORE either arm was solved.** Session `ffr-5e-hindcast-arm`, 2026-08-09, branch
`claude/ffr-5e-hindcast-arm-k679kt` off `origin/main` **`e9f99e6`**. Lane: measurement (owner
decision **D-18(a)** lineage; manager dispatch Addendum AF.4).

**Scope, stated first.** This is a MEASUREMENT of
`vre_procurement_additions_enabled` on its hindcast arm. The channel stays **GATED default-OFF**;
nothing is armed beyond the treatment arm; no keeper is touched; no backcast-registry artifact is
written. Whether the channel becomes a FORECAST default is a future owner card, not this
session's.

---

## 1. The two arms

Both at THIS head, i.e. at/after the FFR-3V-FIX epoch — **condition 2** of
`docs/handoffs/ffr-3v-fix-2026-08-08.md` §6: no pre-epoch cached bundle may serve as either
side, because the arms hash to the same key as their pre-epoch predecessors while producing
different output.

```
control: --iso MISO --vintage 2020 --start-year 2021 --end-year 2025 \
         --forward-from-base --arm realized \
         --out-dir results/hindcast/miso-2021-2025-t1ff-armr-ffr5eh-control

armed:   --iso MISO --vintage 2020 --start-year 2021 --end-year 2025 \
         --forward-from-base --arm realized --vre-procurement-additions \
         --out-dir results/hindcast/miso-2021-2025-t1ff-armr-ffr5eh-armed
```

### 1.1 The flag surface had to be added, and what that cost

FFR-5E landed the channel with **no CLI surface** — its own measurement was a scratchpad harness
over `evolve_fleet` with no LP solve (FFR-5E §3), and its §3.3 recorded the hindcast arm as
BLOCKED. So `--vre-procurement-additions` is added here, per the dispatch's scope guard
("if any solve-affecting flag surface must be added, matrix row + cache-key registration SAME
COMMIT and WAIT for the cache-key-pin verdict before merging").

* **No `ScenarioConfig` field is added.** The field exists and is already registered
  (`_CACHE_KEY_OPTIONAL_FIELDS`, the defaults registry, `TIER_TAGS`) — FFR-5E §6 defect 2.
* The flag rides the existing **None-drop dict** in `build_config`, so OMIT inherits the shipped
  GATED-OFF default rather than mirroring it as a literal (the FFR-3D / FFR-2E instrument
  pattern; a mirrored literal is how a signed default gets silently overridden).
* It is declared `FromConfig` in `META_RECORD_SPEC`, never `FromArgs`, so the run record reads
  the **solved** gate and cannot claim an arming the solve did not carry (the FFR-3R defect).

**CACHE-KEY-PIN VERDICT — PASS, measured before solving:**

| config | `cache_key()` | |
|---|---|---|
| control (flag omitted), THIS head | `8062ab39ad904049` | |
| control (flag omitted), `origin/main` `build_config` | `8062ab39ad904049` | **identical — the control IS the shipped path** |
| `--no-vre-procurement-additions` (explicit off) | `8062ab39ad904049` | collapses onto the control, as it must |
| `--vre-procurement-additions` (armed) | `b6fca9a6c67407b0` | **distinct — no FFR-4D collision** |
| `ScenarioConfig().cache_key()` default pin | `603c2498bf71d21d` | unmoved (the value `test_persisted_identity` pins) |

These are the pre-`ISOConfig.default_scenario_overrides` keys from a dry `build_config`; the
runtime `cache_key=` line is the recorded key and is reported in the results doc.

---

## 2. THE PRE-REGISTERED READS

### R1 — pool reconciliation (the FFR-3V §6 promise made concrete)

The armed run's per-year injected MW, named against EIA-860 rows with `online_year > 2020`,
**additive and auditable on the vintage seed**. Source side is measured from
`data/raw/eia-860/vintage_2020/` BEFORE the solve, so R1 is a falsifiable plumbing check with an
exact expected value, not a description of whatever comes out:

| effective year | rows | wind MW | solar MW | injected? |
|---|---:|---:|---:|---|
| 2021 | 47 | 1,380.0 | 583.4 | **NO** — base year does not evolve |
| 2022 | 4 | — | **451.0** | **YES** |
| 2023 / 2024 / 2025 | 0 | — | — | pipeline empty at a 2020 vintage |
| **total in sheet** | **51** | 1,380.0 | 1,034.4 | **451.0 MW injected** |

**PRE-REGISTERED EXPECTATION: the armed arm injects exactly 451.0 MW of solar into MISO-Illinois
in 2022 and NOTHING in any other year.** Four `source: "procured"` ledger rows, plants
64393/GEN2 (150.0), 64738/HCS (100.0), 64856/65009 (200.0), 64866/USSWC (1.0). Any other
injected total falsifies the plumbing.

**The treatment is therefore small and bounded, and I am stating that before I see the result
rather than after.** 81.3 % of the pipeline the channel can see (1,963.4 of 2,414.4 MW) lands in
the non-evolving base year. Against a vintage-2020 MISO base pool of 2,082.0 MW solar the 451.0
MW is ~21.7 % of the solar pool in the year it lands; against 26,025.9 MW of wind and MISO's
total load it is small. **A near-null R3/R4 is a plausible and reportable outcome, not a failed
measurement** — and it is a fact about the vintage-2020 pipeline, not about the mechanism.

### R2 — the base-year UNDER-COUNT, stated in the score and NOT absorbed

**Condition 1** of FFR-3V-FIX §6. Capacity commissioned *during* 2021 is in neither the
vintage-2020 seed nor the injection, because 2021 does not evolve.

Measured independently here (vintage-2021 year-end minus vintage-2020 year-end, model zones):

| | vintage-2020 Dec | vintage-2021 Dec | commissioned during 2021 |
|---|---:|---:|---:|
| MISO wind | 26,025.9 | 28,711.2 | **2,685.3 MW** |
| MISO solar | 2,082.0 | 3,273.6 | **1,191.6 MW** |

FFR-3V-FIX §6 carried **2,945 MW wind / 1,160 MW solar**. My figures differ by −259.7 MW wind
(−8.8 %) and +31.6 MW solar (+2.7 %). **Both are reported; neither is silently preferred.** The
difference is a zone-set / planned-retirement-off-ramp construction detail, not a disagreement
about the direction or the order of magnitude.

**The sharp form of R2, which the condition did not anticipate:** of that under-count, the
channel can *see* **1,963.4 MW** in its own source data (the 47 rows with effective year 2021)
and still cannot inject it, because the base year does not evolve. So the under-count is not
merely "data the channel lacks" — it is **partly data the channel holds and deliberately
discards**. This is the SAFE direction and it remains ~2–4× smaller than the over-count
FFR-3V-FIX removed (MISO solar −1,191.6 against the old **+4,952**), but it is not zero and the
score states it.

### R3 — the T1-FF posture, arm vs control

Renewable generation and curtailment by year, prices, and the capacity-evolution ledger deltas —
what the corrected near-term VRE supply changes downstream:

* `wind_twh` / `solar_twh` / total VRE TWh and VRE share of load, per solve year
* `dump_twh` (curtailment) — FFR-3V-FIX §5.1 measured `dump_twh = 0.0` in every MISO year of both
  its arms, so VRE entered the balance linearly there; whether 451 MW changes that is a read
* load-weighted and zone-mean price, per solve year
* the evolution ledgers at `<out-dir>/MISO/<runtime-key>/`

### R4 — in-window exit/entry deltas, REPORTED (never targeted)

FFR-3V-FIX §5.3 recorded R4 as a **failed pre-registered read**: its two-solve-year pair had no
power to test it, and it explicitly did not claim the answer. **This session is the first read.**
Per-year additions and retirements by fuel and by `source`, both arms, reported at full
magnitude whatever the sign — including "identical in both arms", which given R1's 451 MW is a
live possibility.

**R4 is reported, never targeted.** No parameter is identified against it and no arm is chosen
by it (rule 1 `[R-STRUCT]`, rule 13 `[R-MEASURED]`).

### R5 — key hygiene

Runtime `cache_key=` recorded for both arms; the two must be **distinct** (§1.1) and each arm has
its own `--out-dir` regardless. This is the FFR-4D hazard FFR-3V-FIX §5.1 reproduced.

---

## 3. Standing caveat carried in, not discovered late

`assign_zone_by_coords` is **incomplete for MISO** (FFR-5E §7): all 51 rows collapse to
MISO-Illinois (48) / MISO-South (3), while their true states are MN 15, IL 10, MI 8, WI 7, IA 6,
AR 2, IN 2, LA 1. All four **injecting** rows are WI/IA/MI/MN and all four are assigned
MISO-Illinois. This is a **pre-existing repo condition shared identically with the thermal
limb** — measured, not introduced here — and it bounds the channel's siting benefit in MISO.
Fixing the shared helper would move the shipped thermal channel and is out of this lane.

---

## 4. Registration and guards

* Both arms register in the **HINDCAST** namespace (`frontend/data/hindcast/`) with
  `meta.kind="full_forward"`, ids `miso-2021-2025-t1ff-armr-ffr5eh-{control,armed}`.
  **NEVER the backcast registry** — the backcast CI gates stay blind to this namespace.
* **Holdout:** solve years 2021–2025 are hindcast windows, the T1-FF carve-out. The freeze is
  ACTIVE and no out-of-training *backcast* year is touched; no marker is read or spent.
* **Rule 12:** years SEQUENTIAL within each invocation; the two invocations sequential or ≤2
  concurrent, both MISO, no PJM co-run.
* **Rule 28(b):** the `vre_procurement` matrix cell citation is updated with the hindcast verdict
  in THIS session.
* **Rule 27:** Opus; exact on-disk bytes pushed; blob verification after any push touching a
  ≥300-line file.

---

## 5. What would make this measurement say each thing

Stated in advance so the conclusion is not written to fit the number:

* **SUPPORTS** forecast-default arming: the injection reconciles exactly (R1), the downstream
  effect is coherent and in the direction the mechanism predicts (more near-term VRE energy,
  softer prices, entry displaced rather than double-counted), and R4 shows the netting working
  rather than a double-count.
* **REFUTES** it: the injection does not reconcile, the netting double-counts, or the arm moves
  capacity decisions in a way that is incoherent with 451 MW of solar.
* **DEFERS** it: the arm is inert or near-inert at this vintage, so the hindcast has **no power**
  to discriminate — which, given R1's pre-solve arithmetic, is the outcome I consider most
  likely. A no-power result is reported as no-power. It is **not** evidence for arming, and it is
  **not** evidence against the mechanism either.
