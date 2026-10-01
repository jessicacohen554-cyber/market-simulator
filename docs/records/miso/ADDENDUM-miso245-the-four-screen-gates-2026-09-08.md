# ADDENDUM miso-245 (second) — **THE FOUR STRUCTURAL STOP-ONLY SCREEN GATES, and the G-DRIFT audit that earns form 4.** Pushed BEFORE the screen runs

**Governs:** `PREREG-miso245-attribute-the-incumbent-ladder-drift-2026-09-08.md` §4 steps 2–4.
**Pushed BEFORE the screen solve is launched and before any of its numbers exist. NO BAR DECLARED
HERE MAY BE MOVED AFTERWARDS.** The first addendum
(`ADDENDUM-miso245-the-test-passed-with-low-power-and-one-more-leg-can-still-kill-it-2026-09-08.md`)
governs the verdict and the citation; this one governs only the screen.

---

## 0. `G-CLAMP-N` PASSED, and the reconciliation is committed

`G-CLAMP-N` (addendum 1 §0c) was declared before its numbers existed and **passes at every entry**:
each reaching value is the **unclamped** quantile, at margins of **23.29 / 34.08 $/MWh** below the
same-seam no-wash limit, and no value in `Δ ∈ {−1, 0, +1}` is clamped anywhere
(`results/calibration/_miso245_gclamp_n.json`). **It removes a way `A-CONFIRMED` could have been
false; it adds no evidence, and it is not read as if it did.** The mechanism it exposes is exact:

| entry | at `Δ = 0` | **at the reaching `Δ`** | committed |
|---|---:|---:|---:|
| 2023 South export 4 | 27.6962804 → **27.70** | `Δ = −1` → 27.6900005 → **27.69** | 27.69 ✓ |
| 2024 South export 5 | 23.7600002 → **23.76** | `Δ = +1` → 23.7730485 → **23.77** | 23.77 ✓ |

The reconciliation is committed at `663f5967`: three entries moved to `derive()`'s own output, **189
byte-identical** (checked), `_MISO244_KNOWN_LADDER_DIVERGENCES` **deleted** (rule 26 `[R-DELETE]`),
the reproduction pin now holding all 192 at `atol=0.005` with **no exceptions** and falsified twice
before it was kept.

## 0b. `G-DRIFT` `a667073f..HEAD` — **ZERO HUNKS ON THE BACKCAST SOLVE PATH**

Baseline `a667073f`, the sha miso-244 audited to and an ancestor of `origin/main` (re-verified with
`git merge-base --is-ancestor`; the keeper's own `git.sha = 710d4dad` is re-confirmed **ORPHANED**).

> `git diff a667073f origin/main -- src/market_sim scripts/run_calibration.py`
> `scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
> → **EMPTY.**

35 files moved in the range and **not one of them is on the audited solve path** — they are docs,
handoff ledgers, forecast scripts (`run_full_horizon.py`, `run_ces_leg.py`,
`register_forecast_run.py`), scoring tests, PJM's matrix shard, a scenario-campaign rollup, and one
new NYISO-keyed data corpus (`data/raw/nid/`), which sits outside every audited root. **There is
nothing to classify, so there is no LIVE hunk and no control solve is earned: form 4 holds and the
KEEPER'S COMMITTED BUNDLE IS THE CONTROL.** Corroborated as the handoff requires:
`surface_stamp("MISO", keeper_config)` reproduces **`8ee657ee4c7c49b0`**, **rows 208**, **`moved: {}`**,
**`epochs: []`** — miso-244's published fingerprint, and **disclosed as EXPECTED** (a deterministic
stamp over an unchanged surface), not as independent corroboration.

## 0c. THE FOOTPRINT IS RE-MEASURED IN THIS SESSION, NOT QUOTED

`scripts/probes/_miso244_liveness_gate.py` re-run **before** the table was edited (after the edit the
two ladders are the same object and the gate has nothing to measure):

| bus | 2023 | **2024** | 2025 |
|---|---:|---:|---:|
| **`MISO_external_South`** *(the bands' own bus)* `L` | 0.00000 (0 h) | **0.00981735 (86 h)** | 0.00000 (0 h) |
| `MISO_external` `L` | 0.00011416 (1 h) | 0.00422374 (37 h) | 0.00000 (0 h) |
| **`max_L`** | | **0.00981735** | |
| **`max abs Δq̂`** | | **3.681507 MW** | |
| **`SCREEN_YEAR`** | | **2024** | |

The re-run reproduces miso-244's published JSON **byte-for-byte** (`git status` clean on that
artifact). **DISCLOSED AGAINST INTEREST AND AS PRE-DECLARED (addendum 1 §0d): this agreement is
EXPECTED — a deterministic estimator on the same series and the same committed sidecars — and is NOT
presented as independent corroboration.** Its only job is that the screen year is named by a
measurement taken here: **`argmax_year L` ⇒ 2024**, which is also the year of the mechanism's own
largest measured footprint, **never the year of any residual**.

## 0d. THE PRE-SOLVE ARITHMETIC THE GATES TEST AGAINST

Only the **2024 South export band 5** correction is live in the screen year: `23.77 → 23.76` lowers
the price at which that 375 MW band (South's own step, `3000/8`) is willing to export, so it clears in
**fewer** hours. `Δn̄_i ≡ 0` (no import band moves), `Δn̄_e = −86/8760 = −0.0098174`, and

> **`Δq̂ = −375 MW × Δn̄_e = +3.681507 MW`** — the seam's mean net flow moves **UP** (less export).

**Every bar below is set from that arithmetic and from nothing else. No scored criterion, no residual
and no band comparison enters any of them, and none of them is a target.**

---

## 1. **THE FOUR GATES — STRUCTURAL, STOP-ONLY, and each able to kill the arm**

Control = the keeper's **committed** 2024 artifacts (form 4, §0b). Arm = the 2024 screen bundle.
Rule 29: *"It may kill an arm; it may never promote one."* **None of these is the target residual —
this correction has no target residual; it is a correctness repair, and S-4 is purely protective.**

**A REAL CONSTRAINT, STATED BEFORE THE GATES RATHER THAN DISCOVERED AFTER** (the trap miso-243 hit):
the committed `hourly/` sidecars carry **no per-seam split** — only an aggregate net `import` class in
`class_hourly_<year>.parquet` (`klass == "import"`, `pass == "P1"`, 8,760 rows). **A gate written on
per-seam flow is NOT measurable from committed artifacts**, so S-1 and S-2 are written on the
aggregate, which is, and the pre-solve prediction is carried onto it explicitly.

### **S-1 — DIRECTION AND ORDER OF MAGNITUDE**

`Δ = mean_hourly(arm net import) − mean_hourly(control net import)`, MW, over 8,760 hours of 2024.

> **PASS iff `Δ ≥ 0` AND `Δ ≤ 40 MW`.**

`≥ 0`: the only band that moved makes export **harder**, and nothing else changed, so the LP cannot
gain a cheaper export at the margin — a strictly negative aggregate response says the correction is
not doing what its own arithmetic says. `≤ 40 MW`: ten times `|Δq̂| = 3.6815 MW`, so a one-cent band
move producing an order-of-magnitude-larger dispatch response **STOPS** the arm. The band is measured
by miso-244 §0e to be the marginal price-setter in **82 of its 86 hours**, so the LP's response may be
**smaller** than `Δq̂` — which is why the lower bound is `0` and not `Δq̂` itself. That looseness is
declared here, not discovered later.

### **S-2 — FOOTPRINT CONFINEMENT**

`H = #{hours in 2024 : |arm net import − control net import| > 1 MW}`.

> **PASS iff `H ≤ 860`** (ten times the 86-hour pre-solve footprint, i.e. ≤ 9.8 % of the year).

A one-cent move on one band of one seam must not repaint the year. If the response is spread across
the calendar, the arm is not confined to the rows the correction touches and **STOPS**.

### **S-3 — THE IDENTITY THE CORRECTION ASSERTS, AND THE CLEANLINESS OF THE A/B**

> **PASS iff (a)** re-running `derive()` on the source data reproduces the solved
> `MISO_SEAM_LADDER_BY_YEAR` at **exactly 0.00 on all 192 entries**, **AND (b)** the screen bundle's
> `run_config.json` `scenario_config` is **identical to the keeper's on every field**.

(a) is the correction's own claim — the table *is* the frozen estimator's output on current data.
(b) proves the **only** delta between control and arm is that constant: not a flag, not a CLI option,
not a config drift. A failure on either **STOPS** the arm.

### **S-4 — NO COLLATERAL FLIP** (rule 29's G-4)

> **PASS iff no load-bearing criterion that PASSES on the keeper's 2024 FAILS on the arm**, scored by
> `scripts/screen_collateral_gate.py --bundle <screen> --keeper-run-id 2026-09-07-miso-243-spp-pairing
> --years 2024`, with the bench held fixed at the keeper's committed parts.

C3c is excluded by construction (the ledgered caveat, rubric v3.3). C6 reads UNATTESTED on a screen
bundle by construction and **is reported as "not scorable at a screen", never as a flip**. Every other
status move, toward or away, is **REPORTED at full magnitude and gated in neither direction**.

---

## 2. DISPOSITION

* **ANY gate STOPS ⇒ the arm is killed, that is the session's result, the remaining years are never
  spent, and the reconciliation commit is reported with the screen that refused it.** Whether the
  committed table is then left reconciled or reverted is an owner question this session would surface,
  not decide.
* **ALL FOUR CLEAR ⇒ the full span** in **ONE** `--year 2023 2024 2025` invocation and **ONE** bundle
  (rules 12 / 16 / 29), years sequential, via `replay_keeper.py` off the keeper's own bundle, with the
  keeper's attestation carried forward and re-stamped so C6 does not read `UNATTESTED`.
* **Rule 31 `[R-RETAIN]`**: every bundle produced stays on local disk, is `.gitignore`d and kept
  **outside** `results/calibration/` so the parity sweep stays green, is **never deleted**, and **the
  promotion question is surfaced explicitly in the final report** with the statement that the bundles
  will not survive this container.

## 3. Non-claims

1. **No bar in this document may move**, and none of the four gates is the target residual.
2. **The screen cannot promote anything.** A cleared screen authorises the full span and nothing else;
   the determination comes from the scorer on a full-span bundle, never from a screen.
3. **DOF stays 41/2** and no `ScenarioConfig` field is created or changed in either branch.
4. **No out-of-training year is solved, scored or registered**; MISO holds no `complete` marker and
   none is sought.
5. **MISO has no failing gate**, this session does not invent one, and C3c is untouched.
6. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage**; no 2025 C1 pass is read as evidence.
