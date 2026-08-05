# PRECHECK — caiso-174: the FFR-4D epoch re-solve and re-gate

**Date:** 2026-08-05 · **Session:** caiso-174 · **Written and committed BEFORE the first arm
finishes.** Everything below is pre-registered. Any departure is recorded explicitly in the
finding (the caiso-172 §5.1 discipline), not silently taken.

**Incumbent keeper under re-solve:** `2026-08-04-caiso-172-measured-path15`
(bundle `results/calibration/caiso172_measured_path15_split`), determination
**CALIBRATED-WITH-CAVEATS**, 0 FAIL, 2 ledgered caveats (C3a mean LMP 2024+2025, C3c price
tail 2023+2024), D-10 free-class C1 12/12 · free 8/8.

---

## 1. Why this session exists, in one paragraph

`ASSESSMENT-caiso173-frontier-2026-08-04.md` re-assessed the CAISO frontier on the
post-caiso-172 ledger and found **every limb intact** — in-model lever queue empty, all
three standing walls re-verified on live bytes, evidence census 19/19, matrix column census
`0/0/0/0/0`, ISO-specific residual DOF down to 3. It recommended **NOT YET** on `complete`
for exactly one reason, and it is not a calibration reason: **FFR-4D merged (PR #3562)
carrying cache epoch `2026-08-04c`, and the designated keeper predates it.** This session is
that re-solve. Nothing else is owed.

**The frontier question is CLOSED and this session does not re-open it.** Its job is one
measurement and a promote-or-escalate call.

---

## 2. The pre-registered verdict rule — caiso-173 §6, BINDING

Fixed here before any number is read, so the decision cannot be steered by what the solve
returns:

| outcome | action |
|---|---|
| **CALIBRATED-WITH-CAVEATS, no NEW criterion FAIL, no new caveat slot spent** | **PROMOTE.** Recommend **YES** on `complete` on that record, citing caiso-173 §6. No further frontier work is required to support it. |
| **Determination DEGRADES** (a new FAIL, or a third non-protective caveat slot) | **DO NOT PROMOTE. DO NOT recommend.** Write the finding, register both arms, **ESCALATE TO THE OWNER.** Rule 22 D-5(b)'s posture applied prospectively: a worse determination is never silently written. |

Either way both arms are registered (rule 15 `[R-DASHBOARD]`) and **the marker is not
written** — `calibration-complete.json` and `holdout-freeze.json` are owner acts (rule 22)
and stay untouched under every outcome.

---

## 3. The design — a two-arm A/B at ONE post-epoch head

`scripts/replay_keeper.py` reconstructs `ScenarioConfig` from the recorded config, so a
field **absent** from the keeper's `run_config.json` takes the **current default**. That is
precisely the epoch effect, and it means the treated arm needs no edit at all.

| arm | out-dir | delta | purpose |
|---|---|---|---|
| **A — CONTROL** | `caiso174_control_flatfleet` | `--set storage_measured_base_fleet=false` | Isolates **incidental code drift** between caiso-172's head (`789e28b8`) and this one. Main has moved substantially (FFR-4C wind PTC, ercot-165, miso-127/129, nyiso-127, neiso-83, the entry ladder). Without this arm the delta is not attributable to the epoch. |
| **B — TREATED** | `caiso174_measured_fleet` | none — the default fires | The epoch: measured EIA-860 storage base fleet resolved as of the solve year. |

**Arms run SEQUENTIALLY, never concurrently** (rule 12 `[R-PARALLEL]`: one CAISO plant-level
multi-zone LP already needs several GB; this container is **15 GB / 4 cores** and two
concurrent arms would OOM). **Years 2023 2024 2025 in ONE invocation each** (rule 16
`[R-ALLYEARS]` + rule 12's sequential-years requirement). If a single process OOMs, the
fallback is `replay_keeper`'s `--years` + `--reuse-solved` per-year chain — a mechanical
memory workaround, not a scope change.

---

## 4. THE QUANTITY GATE — checked BEFORE any price is read

The caiso-162 standing lesson, which caiso-172 re-learned the hard way: **a `run_config`
recording a mechanism as armed is NOT evidence the LP saw it.** The separation is verified
on the **fleet**, first, and if it fails this is a wiring defect and the session STOPS
rather than reporting a price result.

Pre-registered expectations (FFR-4D §5, EIA-860 2025 Early Release):

| check | Arm A (control) | Arm B (treated) |
|---|---|---|
| battery MW at year-end 2023 | flat **8,000.0** | **7,492.4** |
| battery MW at year-end 2024 | flat **8,000.0** | **11,131.3** |
| battery MW at year-end 2025 | flat **8,000.0** | **15,448.4** |
| `power_cap` shape | 1-D (flat scalar) | **2-D `(6, 8760)`** |
| `storage_vintage_ramp` for batteries | dead (nothing to ramp) | **live for the first time** |

`storage_vintage_ramp` is armed on the keeper and has been a **DEAD FLAG for batteries** —
with the fleet a flat scalar there is no COD ramp to apply, so it was reaching pumped
storage only. Arm B is the first CAISO solve in which it is live for batteries, and the
2-D `power_cap` is that closing.

`caiso_storage_shape_caps` is a **per-MW-of-EIA-860-fleet** rate (EIA-930 NG:OTH ÷ EIA-860
monthly fleet) multiplied by `power_cap`. In Arm A its **denominator and multiplicand are on
different fleets**; in Arm B they are the same fleet. That basis reconciliation is confirmed
as part of this gate.

---

## 5. What is REPORTED and what GATES

**GATES the promotion:** the determination, and only the determination — per §2.

**REPORTED, never gated:**

- **C3a movement, in either direction.** FFR-4D §5 files a hypothesis it **explicitly does
  not claim**: that the C3a-2025 caveat (mean LMP **+14.4 %** hot) is partly this fleet
  defect, since 7.4 GW of missing evening-peak battery leaves that load to thermal. **It is
  untested and this run is its first test.** It is pre-registered here as a hypothesis that
  may be **confirmed or refuted**, never as an expected result. Whichever way it goes is
  stated as measured.
- **The sign reversal.** caiso-173 §1 is emphatic and it is carried here: the defect is
  **not uniformly "short"**. 2023 ran **6.8 % OVER** the measured fleet, 2024 **28.1 %
  short**, 2025 **48.2 % short**. FFR-4D's "48 % short" headline is the 2025 figure alone
  and must not be carried as a uniform direction. **Per-year effects may oppose each
  other**, and that is an anticipated outcome rather than an anomaly.
- **KNOWN-OPEN 1** (the N–S congestion majority) and the **SDGE limb inversion**, re-measured
  on the new keeper via caiso-173's instrument.

---

## 6. Rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]` — stated before the result, because that is
when it binds

**The measured EIA-860 fleet stays in EITHER WAY.** It is the accurate input; the flat
8,000 MW is a hand-rounded *forecast* base-year constant that was being fed to backcast
years. If the fit gets **worse**, rule 14 is explicit that this is a **discovered bug
elsewhere** — never grounds to revert to the estimate — and rule 1 forbids judging a
structurally-correct mechanism by whether it improves the backcast fit.

The only thing a degraded determination changes is **whether the run is promoted and whether
`complete` is recommended** (§2). It does not put the flat scalar back.

---

## 7. What will NOT be done — pre-committed

- **No parameter is re-picked in response to anything the solve returns** (rules 5
  `[R-NO-MAGIC]`, 13 `[R-MEASURED]`, 21 `[R-REGISTRY]`, 24 `[R-REGISTRY]`). A derive re-run
  "because the residual moved" is barred by rule 23 `[R-FROZEN-DERIVE]`; derives re-run only
  on a **source-data** change.
- **The Path-15 weights are not re-opened.** caiso-172 **measured** them; a re-pick against
  any residual is an outcome pin.
- **`STORAGE_BASE_FLEET_MW["CAISO"]` and `RENEWABLE_INSTALLED_MW["CAISO"]` are not
  re-derived.** FFR-4D measured them from the committed EIA-860 2025 Early Release under
  rule 23; the licence to move them is a source-data change.
- **ERCOT's parallel hand-entered storage row is not touched** (rule 25 `[R-ISO-SCOPE]` —
  routed as FFR-4D D-3, not open).
- **No N–S topology lever is chartered** (caiso-164 §0/§6 stands).
- **MWD-TAC is deliberately OUT OF SCOPE.** caiso-173 §2 C adjudicated it a recorded open
  item and **not a blocker** (it is a *misapportionment*, not missing load — `load_zonal_shares`
  normalises to 1.0 — worth **0.24–0.30 %** of ISO load across a model boundary). Closing it
  is a demand-input **intake** in its own session. Folding it in here would confound the one
  delta this re-gate must attribute (rule 19 `[R-ONE-MECH]` in spirit).
- **No lever from any closed cell is re-tested.** CAISO's in-model lever queue is empty and
  every `R`/`I`/`G` cell stays closed. This session **replays a recipe; it does not tune
  one.**

---

## 8. Holdout — 2023 / 2024 / 2025 only

CAISO holds **no** `complete` marker. No out-of-training year (2022, 2019, ≤2021, H1-2026)
may be solved, scored or registered — not even as a throwaway diagnostic. The CLI hard-fails
outside {2023, 2024, 2025}, and the **holdout spend freeze is ACTIVE** for all ISOs and both
tiers and outranks every marker.

**Rule 22 leave-one-year-out:** this session fits **nothing** and moves **no free
parameter** — the delta is a default-ON measured-input field with zero free parameters. LOYO
therefore reduces to the **no-held-out-degradation** check across 2023/2024/2025. If a single
year carries a verdict flip, that is a finding and it is stated.

**Rule 22 D-5(b) re-keying does NOT apply:** it binds only ISOs holding a `complete` entry,
and CAISO does not.

---

## 9. The DOF ledger — a pre-registered invariant

The epoch field carries **zero free parameters** and selects a **measured EIA-860 fleet**
over a hand-rounded scalar — a rule-14 identification, the same object class as caiso-172's
own closure. Pre-registered:

> **`n_entries` stays 11, `n_residual` stays 8, and CAISO's ISO-specific residual count
> stays 3.** If the attestation shows the epoch field incrementing any of them, **that is a
> defect in the attestation**, not a property of the mechanism, and it is fixed before the
> run is registered.

---

## 10. Matrix duty (rule 28 `[R-MECH-MATRIX]`, duty b)

`storage_measured_base_fleet` is CAISO **`O`**, and **this session is the only one that can
adjudicate it**: FFR-4D was a forecast-lane charter that ran no backcast, and only a CAISO
**backcast** can adjudicate a backcast-scoped field. The cell moves to its measured verdict
**in this session**, with its evidence citation.

FFR-4D's own evidence note is explicit and is honoured: its forecast FC-2 row-4 result
(65.48 % → 52.51 %) measures the two **re-vintaged constants**, **not** this field, which is
inert in a forecast leg by construction. It does **not** adjudicate the cell.

**KNOWN-OPEN 2** (the caiso-170 within-day storage placement pointer) was measured on the
**pre-epoch fleet** — statistics computed against a fleet up to 48 % short. It is **re-read**
after the solve rather than carried forward as measured. Its re-reading is reported; **no
successor is chartered off it.**

---

## 11. Closing check

`scripts/probes/caiso173_frontier_recheck.py` resolves the keeper from the registry, so it
follows any promotion automatically. Pre-registered expectations:

- **G0 must flip** to `KEEPER IS PRE-EPOCH: False`.
- **F2** must still show CAISO ISO-specific residual **3** (per §9).
- **F3 / F4** re-measure KNOWN-OPEN 1 and the SDGE limb on the new keeper.

Its output is quoted in the finding.
