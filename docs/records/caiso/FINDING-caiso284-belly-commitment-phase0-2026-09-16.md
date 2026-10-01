# FINDING caiso-284 Job B phase 0 — the belly deficit is bridge COVERAGE, and the next step is blocked on an artifact, not on a hypothesis

**Lane:** CAISO calibration · **Date:** 2026-09-16 · **LP spent: ZERO** (rule 32 `[R-SHARD]` (a):
the parent never solves) · keeper unchanged `2026-09-12-caiso-275-gascoupling`. Nothing armed,
nothing registered, no `ScenarioConfig` field, no derive re-run, **no mechanism cell moved**
(rule 28 duty (b) is not owed — no mechanism was tested).

**Object inherited:** caiso-275 §1 / caiso-283 §3 — *"the successor object is CAISO COMMITMENT,
not the import offer."* Measured there: a belly gas deficit (model 1.5 GW vs actual 7.2 GW in the
2024 lowest net-load decile) and a reversed seam direction (model +2 GW import vs actual −1 GW
export).

---

## 0. What phase 0 settled, and what it did not

| | |
|---|---|
| **Settled** | The belly deficit is **entirely a commitment-coverage quantity.** In the belly CC_REGULAR runs **100 % out of its `committed` band and 0.0 MW out of every econ band**, and that band delivers only **16.5–19.6 %** of its own year-max. |
| **Settled** | Three candidate levers are **refused at phase 0** without a solve: the min-load fraction (rule 23), the export route (`R`/`R`/`G`), and the decommit screen (not binding). |
| **NOT settled** | *Why* so few units are bridge candidates. That reads the **P0 run pattern**, which no committed CAISO artifact carries. |
| **Consequence** | **No shard was launched.** There is no pre-registered mechanism to test yet, and spending a 4-year CAISO span to go looking for one is exploration, not a screen. |

---

## 1. The measurement — belly gas is 100 % floor, 0 % economic

Keeper's own committed P1 sidecars (`hourly/class_band_hourly_<y>.parquet`,
`class_hourly_<y>.parquet`, `system_<y>.parquet`). Belly = lowest decile of model net load
(demand − wind − solar), 876 h/yr. Mean MW.

| CC_REGULAR band | 2023 belly | 2024 belly | 2025 belly | 2024 peak decile |
|---|--:|--:|--:|--:|
| **`committed`** | **803.1** | **670.5** | **774.8** | 3,163.2 |
| `econc00…econc05` | 6.6 → 0.9 | **0.0** | 0.4 → 0.2 | 1,488 → 855 |
| `peak…peak4` | 0.0 | 0.0 | 0.0 | 8.4 → 0.2 |

**In 2024 every economic band is exactly 0.0 MW in all 876 belly hours.** The belly price is
−$6.71 (2024), +$3.76 (2023), +$1.50 (2025); no CC econ tranche is anywhere near marginal. So
**nothing about offer levels can move belly gas** — which independently re-confirms caiso-283's
RTM-FLAT closure from the dispatch side, and confirms caiso-275's naming of the successor.

The whole of the model's belly gas is floor:

| year | `committed` belly | `committed` year-max | **% of its own block held** | CHP belly | floors total | imports |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | 803.1 | 4,101.5 | **19.6 %** | 980.5 | 1,783.6 | 1,508.3 |
| 2024 | 670.5 | 4,063.1 | **16.5 %** | 821.7 | 1,492.2 | 2,000.9 |
| 2025 | 774.8 | 4,050.5 | **19.1 %** | 821.4 | 1,596.2 | 1,882.2 |

The `committed` year-max (~4.06 GW) is close to the CA CC fleet's own minimum-load block
(0.26 × 12.7 GW ≈ 3.3 GW, plus CHP). **The RA bridge therefore holds roughly one fifth of the
fleet's Pmin block through the belly.** That single ratio is the object.

CHP is flat to the hundred-kW across all three years (821.7 / 821.4 in 2024/2025) — a hard
steam-host must-run, correctly not a bridge decision and not a lever.

---

## 2. Three levers refused at phase 0, each on its own ground

### 2.1 `caiso_ra_min_load_frac` — REFUSED under rule 23 `[R-FROZEN-DERIVE]`

The keeper runs **0.26** where NYISO's measured CC value is 0.523 and ERCOT's is 0.574, which
looks like a free parameter set low. **It is not.** `pipeline/backcast_config.py:1647` grounds it
in the CAMPD/CEMS-measured CAISO combined-cycle minimum stable load — **P5 of net CF over online
hours**, capacity-weighted **0.259** over a 23-plant / 12.7 GW CA CC fleet (range 0.10–0.63,
median 0.25), producer `scripts/data/derive_thermal_tranches.py`, artifact
`data/raw/_processed-legacy/thermal_tranches_CAISO.csv`. It already *supersedes* the generic 0.40
NREL/Master-File turn-down.

The cross-ISO gap is a **statistic** difference, not a grounding difference: ERCOT's 0.574 is a
registered LSL/HSL ratio and CAISO's 0.259 is a realized-P5 proxy for the same Pmin. A CA 2×1 CC
running one train at minimum sits near 0.26, so the value is physically ordinary.

Rule 23 is explicit that min-stable loads *"re-derive only when their source data updates — never
because a residual moved."* There is no new source. **Refused, and it should stay refused.**
Recorded so the next lane does not re-open it on the cross-ISO comparison alone.

### 2.2 The export route — already `R` / `R` / `G`, DO-NOT-REDO

The real CAISO belly is a **net exporter** while the model imports ~2 GW, so "let the surplus
out" is the obvious reading of the seam. The whole family is adjudicated:

| cell | verdict | evidence |
|---|---|---|
| `caiso_p1_export_sink_seam` | **R** | caiso-142 |
| `caiso_corridor_export_path` | **R** | caiso-132 → 138 → 142 → 143 |
| `caiso_node_export_constraint` | **G** (governance-refused) | caiso-143 |

Checked before proposing, per rule 28 (a). Not re-opened.

### 2.3 The bridge's decommit screen — measured NOT binding

`_write_economic_bridges` (`model/commitment.py:615`) decommits a bridge when the candidate floors
exceed hourly absorption, `absorb = Σ import dispatch + unused export-sink headroom`, repricing
held energy to `surplus_floor_value`. The keeper arms it (`caiso_ra_bridge_decommit = True`), so
it was the natural suspect.

**It is at most marginal.** Total floors in the belly are 1.49–1.78 GW against an import term
alone of 1.51–2.00 GW, with export headroom on top. The surplus condition
`floor_total > absorb` is therefore not clearly reached in the mean belly hour, so surviving
bridges are priced at the real LMP and the screen is **not** what caps belly gas at one fifth of
the Pmin block. The cap is **upstream, in candidacy**.

Stated honestly: this is a mean-hour comparison, not an hour-by-hour reconstruction of the
screen, and export headroom is not separately measurable from the committed sidecars. It is
enough to move the screen off the top of the suspect list; it is not enough to exonerate it.

---

## 3. What blocks the next step — an artifact gap, named precisely

The remaining question is **why so few CC units become bridge candidates**, and every route to it
reads state the committed bundle does not carry:

1. **The P0 run pattern.** `caiso_ra_mustoffer_min_gen` detects bridges from the **P0** dispatch.
   Every committed CAISO sidecar holds **P1 only** (`class_hourly`, `class_band_hourly`,
   `system` all report `passes: ['P1']`). Candidacy cannot be reconstructed.

   > **CORRECTED 2026-09-17 — THIS NEEDS NO CODE CHANGE, ONLY A FLAG.** An earlier revision of
   > this finding (and the session's own report) said persisting P0 was a change to write. **That
   > was wrong.** `scripts/run_calibration_full.py --persist-p0-commitment` already exists, is a
   > plain CLI flag with **no** `--enable-legacy-p2` gate, and writes
   > `hourly/p0_commitment_<year>.parquet` — the bit-packed P0 on/off pattern from
   > `p0_commitment_pattern(energy_solve.r0.dispatch, fleet_arrays.pmax)`, which is *exactly* the
   > run pattern the bridge detector keys on — plus
   > `hourly/startup_run_ratio_<year>.parquet`. The CAISO keeper simply did not pass it. **The
   > next CAISO solve passes `--persist-p0-commitment` and the P0 gap closes with zero code.**
2. **Per-unit storage SOC.** The screen excludes storage-charge headroom from `absorb` on an
   explicit **energy**-capacity premise (*"the fleet already fills by the belly in P1"*). The
   keeper's sidecars show **1,477 / 1,945 / 2,391 MW of unused charge POWER** in the mean belly
   hour, with the fleet above 95 % of its own annual max charge in only 18 / 55 / 43 of 876 belly
   hours — so the *power* half of the premise does not hold. The *energy* half is the one the
   comment actually asserts, and it is **not testable from committed artifacts**: the storage
   sidecar carries `charge_mw` / `discharge_mw` aggregated by tech, with no SOC column, and
   integrating the tech-aggregate fails its own physical check (reconstructed SOC span came out
   at **420–4,121 % of implied capacity**, because each unit carries its own cyclic SOC and the
   aggregation destroys it). **That reconstruction is reported as failed and no number from it is
   quoted or used.**

**The unblock — LANDED 2026-09-17 on the owner's instruction ("Yes make the change").** Both
halves are now in place and neither costs LP time of its own:

* **P0 — no code needed.** `--persist-p0-commitment` already existed (see the correction above).
  The next CAISO solve passes it.
* **SOC — landed.** `scripts/run_calibration_full.py::_storage_frame` now emits `soc_mwh` and
  `energy_cap_mwh` per storage unit-hour, and `_write_storage_hourly_sidecar` sums both into the
  committed per-tech sidecar. `DispatchResult.storage_soc` was already solved on every path — the
  SOC recursion is a core LP constraint — so this persists an existing variable rather than
  computing anything new. Because stored energy is extensive, `Σ cap − Σ soc` at tech grain is the
  tech's true absorption headroom, which is precisely the quantity the decommit screen's premise
  is about and precisely what a reconstruction cannot recover. WRITE-ONLY, read after both LPs
  have run, no `ScenarioConfig` field (rule 24 `[R-REGISTRY]` scopes to tunables that can change a
  solve). `soc_mwh` is NaN — never 0.0 — where a solve carried no SOC block, since 0.0 would read
  as "the reservoir is empty", a real and very wrong claim about headroom. Guard:
  `tests/scoring/test_storage_soc_sidecar.py` (7 tests, incl. that the charge/discharge
  aggregation is byte-unchanged).

**Already-committed bundles do not gain the columns** — they are written at solve time. The next
CAISO solve carries both, after which candidacy and the energy premise are answerable at zero LP.
Doing it the other way round — solving a span now to see what happens — is the exploration
rule 29's phase-0 practice exists to avoid.

---

## 4. Why no shard was launched

Rule 1 `[R-STRUCT]`: a mechanism is never selected because the residual moved. I have an object
(bridge coverage) but **no identified mechanism** — the three named candidates are refused above,
and the fourth (counting storage headroom in `absorb`) rests on a premise phase 0 could not test.
Arming it anyway would be arming on an untested premise and selecting it afterwards on the
residual.

Rule 34 `[R-SHARD-PROMOTABLE]` (c) makes the cost concrete: a promotable CAISO batch is **four**
year-shards (2022–2025, the ISO's full registered set), each pushing its bundle. That is the right
price for testing a pre-registered hypothesis and the wrong price for finding one.

**So the session stops here and asks.** Nothing is deleted; nothing was solved, so rule 31
`[R-RETAIN]` has nothing to protect and no bundle is at risk from this container's reclamation.

---

## 5. Successor, ranked

1. ~~**Persist P0 + per-unit SOC in the bundle sidecars**~~ — **DONE 2026-09-17.** SOC landed
   (`_storage_frame` / `_write_storage_hourly_sidecar`); P0 needed no change, only
   `--persist-p0-commitment`. **Both must be on the next CAISO solve**, which is a one-year
   instrumented probe, not a span.
2. **Then** identify the coverage mechanism from the P0 pattern: is the shortfall in
   `RA_BRIDGE_ECON_MIN_DOWN_HOURS` eligibility, in the `DA_COMMITMENT_HORIZON_HOURS` multi-day cap,
   or in the restart inequality's `mc_gap` term? Each is separately measurable once P0 is on disk.
3. **Only then** a pre-registered one-year screen and, if it clears, the four-year span.

**Do-not-redo, added (rule 28 a):** re-deriving `caiso_ra_min_load_frac` on the cross-ISO
comparison with NYISO/ERCOT. The value is measured, the gap is a statistic difference, and rule 23
refuses re-derivation without new source data.
