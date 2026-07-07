# FINDING — ERCOT storage-AS duration gate 0.54–0.61× (G-37) is a dispatch-choice LIMITATION, not a coupling bug — 2026-07-07

**Branch:** `claude/ercot-storage-as-gap-gzvo6m`
**Register row:** `G-37` (`docs/gap-register-2026-07.md`).
**Reads first:** `docs/handoffs/ercot-storage-as-duration-gate-2026-07.md` (the WS-B build),
CLAUDE.md rules **1** (structure-first), **9** (storage ε), **11**/**12** (measured-data admissibility).
**Bundle reproduced:** `results/calibration/166/storage_as.parquet` (run 166 = run 164 + duration gate,
the one-delta probe; `ercot_storage_as_endogenous` + `ercot_storage_as_duration_gate` on).

---

## 1. Metric reproduced (exact, not the min() upper bound)

`python scripts/probes/storage_as_split.py results/calibration/166`

| year | measured AS (60-Day DAM battery award) | modeled AS | mod/meas |
|---|---|---|---|
| 2023 | 1,249 MW | 678 MW | **0.54×** |
| 2024 | 2,045 MW | 1,132 MW | **0.55×** |
| 2025 | 2,824 MW | 1,715 MW | **0.61×** |

Matches G-37's cited 0.54–0.61×. With the gate on, `modeled_as_mw` is the **exact** RS decision
variable (`DispatchResult.storage_reserve_dispatch` = `Σ_c RS[c,z]`, `run_calibration_full.py:772-774`),
**not** the storage-first `min()` upper bound — so the shortfall is a real cleared-quantity gap, not an
attribution artifact. (The probe's printed footnote still described the old `min()` bound; corrected in
this branch.) Comparison is apples-to-apples: measured is battery RegUp/RRS/ECRS up-AS
(`scarcity.py::ercot_storage_as_reserve_mw`); the model clears the same up-classes
(`ERCOT_AS_PRODUCTS`, all up).

## 2. Diagnosis: the coupling is CORRECT — the shortfall is an intraday dispatch choice

The storage↔AS coupling is three LP-linear row families in `dispatch._build_reserve_rows`
(`src/market_sim/model/dispatch.py`):

- **Power-competition** (`dispatch.py:1441-1471`): `Σ_c RS[c,z] + Σ_{s∈z}(Dis−Chg) ≤ Σ cap`.
- **Duration gate** (`dispatch.py:1473-1494`, SOC coupling at `:1481-1483`):
  `Σ_c dur_c·RS[c,z] − Σ_{s∈z} SOC[s] ≤ 0`, gating on the **same-hour (end-of-hour) SOC**.

Both are structurally faithful to ERCOT's ESR State-of-Charge rule (Nodal Protocols §3.17.3) and are
working exactly as designed. The proof is the **intraday shape**, from the hourly parquet
(mean MW by hour-of-day, 2024; every year is the same shape):

```
 hod  measAS  modAS  ratio  battery-discharge(energy)
 h12   2389   1903   0.80     36     <- midday: battery CHARGING/idle, SOC rising
 h13   2549   1862   0.73     56         -> up to 2×cap up-headroom (curtail-charge + discharge)
 h14   2630   2020   0.77     62            and high SOC -> AS ~full
 h15   2783   2068   0.74     68
 h16   2988   2093   0.70     97
 h17   3047   1818   0.60    980     <- evening ramp: discharge spikes
 h18   2844   1174   0.41   2189     <- evening PEAK: battery dumps energy for arbitrage,
 h19   2502    526   0.21   1955        SOC drawn down -> duration gate forecloses AS
 h20   2284    309   0.14    546
 h21   1938    256   0.13     92     <- ratio floor 0.13 exactly where discharge is largest
```

The modeled AS ratio **collapses precisely where battery discharge spikes** (evening net-load peak
h17–22) and is **near-full where the battery charges** (midday h11–16). This is the correct coupling:
a charging battery has up to 2×`cap` upward-reserve room (stop charging + discharge) and a rising SOC,
so it can back near its full measured award; a discharging battery has little power room left (`RS ≤
cap − Dis`) **and** a drawn-down SOC, so the duration gate caps its AS. Nothing in the coupling is
mis-signed, mis-scaled, or double-counting — the units check (`dur_c[h]·RS[MW] = MWh ≤ SOC[MWh]`), and
the flag-off path is byte-identical (`n_storage_reserve = 0`).

**The residual is therefore an energy-vs-AS dispatch choice, not a coupling defect.** In the deterministic
P1 co-optimization the battery discharges its stored energy into the evening peak (where the realized
energy dual is highest), and the resulting SOC depletion — via the *correct* duration gate — leaves it
unable to hold AS in exactly the hours (h17–22) where the measured fleet holds its **largest** awards.
The measured battery instead reserves SOC across those hours to honor its Day-Ahead AS commitment.

### 2a. The previously-recorded diagnosis was backwards

The WS-B handoff attributed the shortfall to *"idle thermal reserve free in loose hours … the endogenous
LP gives storage its **tight-hour share**, netting 0.55×."* The hourly evidence is the **opposite**:
storage keeps its share in the **loose midday hours** (h11–16, ratio ~0.8) and **loses** it in the
**tight evening peak** (h17–22, ratio 0.13–0.41). Free idle thermal in loose hours is not the binding
mechanism; evening SOC depletion from energy arbitrage is. (Corrected in the handoff's Open follow-ups.)

## 3. The missing mechanism (why no fitted fix — rule 11)

Two real, forward-reproducible structures are absent; neither is closable by a tuned adder, so per
CLAUDE.md #1/#11 the structurally-faithful gate stays as-is and the shortfall stays a documented residual:

1. **Forward AS commitment under uncertainty.** ERCOT's Day-Ahead co-optimization awards AS and the ESR
   then *self-manages SOC in real time to honor the award* — it will not renege to chase a high RT energy
   price. Our single deterministic **perfect-foresight** P1 solve has no such commitment: it sees exactly
   which evening hours pay most for energy and greedily arbitrages, whereas a real battery hedges by
   holding AS against uncertain deployment. A perfect-foresight LP **structurally** under-provides standby
   reserve from a flexible, energy-substitutable asset. Closing this needs a forward-commitment /
   stochastic layer (a two-settlement or scenario-robust AS award), not a knob.

2. **Evening fast-AS scarcity price formation.** Qualified fast up-AS supply (batteries + the limited
   online thermal that can respond in seconds) is scarcest in the evening peak, so ERCOT RRS/ECRS/RegUp
   clearing prices co-move up with energy scarcity. If our reserve requirement is met at a modest evening
   dual, the co-opt has no price reason to retain the battery in AS over marginal energy. A **grounded**
   fast-AS supply separation (e.g. a ramp/response-qualified thermal reserve limit from
   `data/ramp_capability.py`, which responds to fleet changes) would raise the evening AS dual and pull
   storage back — this is the "grounded cost separation, not a tuned adder" the WS-B handoff flagged as
   open follow-up #1. It is out of scope for the storage↔AS coupling (it lives on the **thermal** AS
   supply side) and needs its own validated build + LOYO scoring before it could touch a keeper.

## 4. Keeper impact / regression posture

`ercot_storage_as_duration_gate` is **default-off** and is **not enabled in the ERCOT keeper**
(`2026-07-06-ercot34-stage4-overlay-off`; the flag is absent from its `run_config.json`, i.e. off).
The gate is validated only on the run-166 probe. This finding changes **no LP-construction code** — only
this doc, the WS-B handoff's follow-up wording, the register row, and the probe's stale printed footnote —
so the ERCOT keeper solve and all other AS metrics are **byte-identical** (verified by the unchanged
dispatch/reserve/storage/scarcity test suite; the coupling's flag-off byte-identity is already covered by
`tests/test_ercot_storage_as_duration_gate.py`).

## 5. Disposition

**LIMITATION — documented, not fixed.** The storage↔AS duration-gate coupling is structurally correct
(`dispatch.py:1441-1494`); the 0.54–0.61× residual is a deterministic-dispatch/AS-valuation limitation
whose two missing mechanisms (§3) require their own builds and cannot be closed by an adder. G-37 stays
open as debt with a sharpened root cause; the coupling itself is **not** the defect.
