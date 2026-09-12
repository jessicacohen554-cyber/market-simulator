# PRECOMMIT (miso-255): screen `miso_import_sil_measured_envelope` on 2021 and 2022

**Pushed BEFORE any LP is spent (rule 29 `[R-SCREEN]`).** Every gate, gate value, screen-year
choice, control basis and drift audit below is fixed at this commit and is not renegotiated after
a number comes back. Phase 0 that produced the arm:
`docs/FINDING-miso255-cc-cf-tracks-the-object-is-the-seam-2026-09-12.md`.

---

## 1. THE ARM

`ScenarioConfig.miso_import_sil_measured_envelope` (bool, **default `False`**, MISO-only,
byte-identical off; registered in `_CACHE_KEY_OPTIONAL_FIELDS` at its default in the same commit
as the field — the nyiso-119 discipline).

**What it does.** The aggregate `MISO_simultaneous_import` interface limit
(`EXTERNAL_SIMULTANEOUS_LIMITS["MISO"]`) caps total simultaneous flow across every `MISO_external`
border link at **8,700 MW in both directions**. The flag **REPLACES** that scalar with MISO's own
**measured coincident boundary transfer envelope, per direction**
(`data/eia930/envelopes.py::measured_boundary_transfer_envelope`), injected at the single
`runner.py` `build_interface_groups` seam by
`model/interchange/miso.py::apply_miso_measured_sil_envelope`. Per-link TTCs and the per-seam
envelopes (`miso_seam_flow_limit` / `miso_seam_export_limit`) are untouched and still bind below
it. It replaces; it never stacks (rule 19 `[R-ONE-MECH]`).

**Why (rule 14 `[R-ACCURATE]`, not the residual).** 8,700 MW is MISO's published **Capacity Import
Limit** — a PRA/LOLE resource-adequacy accreditation limit for a delivery year, by the constant's
own cited provenance ("MISO PRA clearing results; MISO LOLE Study Report; MTEP") — used as the
**hourly energy** bound in **both** directions. The meter falsifies it in that role both ways:

* metered net import **exceeds** 8,700 MW in **583 / 106 / 69 / 118 / 4 / 14** hours of 2020-2025
  (max 12,601 MW);
* metered net **export has never reached** 8,700 MW in any of those years (deepest **−5,415 MW**,
  2024) — MISO publishes a separate Capacity **Export** Limit and the code applies the **import**
  number symmetrically (`bidirectional=True`).

With the priced reference-price seam wanting import in nearly every hour, the scalar stops being a
bound and becomes the schedule: the model's net interchange sits **on** it for
**3,730 / 8,650 / 2,609 / 3 / 0 / 0** hours of 2020-2025, and 2021's hourly import takes **110
distinct values in 8,760 hours**.

**Zero free parameters (rules 21/24).** Same estimator, same registered percentile
(`miso_seam_flow_percentile` → `MISO_SEAM_FLOW_PERCENTILE`, p90) and same miso-175 hour-ending key
as the per-seam envelopes already armed. The **only** difference is aggregation **order**:
coincident (sum the seams' DIBAs at each timestamp, then take the percentile) rather than per-seam
percentiles summed afterward, because the seams do not co-peak — the summed per-seam p90 is
**64.87 TWh** in 2021 against a coincident **49.62 TWh**.

**Not a re-test of an `R` cell.** `miso_seam_coincident_envelope` (**R**, miso-181) conditioned the
**per-seam** envelope on the **neighbour's own load state** and died because the conditional
percentile was flat in its declared driver. This adds **no conditioning variable and no driver**;
it swaps one unsourced scalar for the unconditional estimator the **K** cell already uses, at the
boundary the scalar itself governs.

**Rule 13 `[R-MEASURED]` admissibility, measured rather than asserted.** It is a ceiling the LP
clears below, not a pin: measured flow **exceeds** the envelope in **11.8-15.4 %** of the hours of
every year 2020-2025, with **1.5-2.1 GW** of mean headroom over the measured mean. It regenerates
for a forward year from the then-current directed-flow record and responds to changed conditions.
Guarded by `tests/iso/miso/test_miso_measured_sil_envelope.py::test_envelope_is_a_ceiling_not_a_pin`.

---

## 2. SCREEN YEARS: **2021 AND 2022**, chosen on FOOTPRINT — both metrics disclosed

Rule 29 names the screen year as the one where the **mechanism's own measured footprint is
largest**, never the biggest residual. The pre-solve footprint (hours in which the model's own
solved flow violates the new envelope, and the MWh by which it does):

| yr | h over import env | h over export env | **total bound-hours** | **excess TWh** |
|---|---:|---:|---:|---:|
| 2020 | 3,493 | 1,101 | 4,594 | 7.82 |
| **2021** | **8,476** | 3 | **8,479** | 26.48 |
| **2022** | 713 | 5,723 | **6,436** | **33.81** |
| 2023 | 2,141 | 10 | 2,151 | 1.28 |
| 2024 | 1,928 | 209 | 2,137 | 1.35 |
| 2025 | 1,619 | 414 | 2,033 | 1.64 |

**The two metrics rank them differently** — 2021 leads on bound-hours (the mechanism's own unit: it
is an hourly capability bound), 2022 leads on TWh. **Choosing one metric after seeing the table
would be metric selection, so BOTH are screened.** They are also the mechanism's two legs: 2021 is
almost purely the import leg, 2022 almost purely the export leg. Two ~16-minute shards is still far
cheaper than a 3-year span, and it removes the selection problem rather than arguing it away.

**Stated at the gate, before any result:** the training years 2023-2025 carry a **1.28 / 1.35 /
1.64 TWh** pre-solve delta, so this arm is **not** inert there. The keeper is untouched (the flag
is default-off and absent from its recipe), but any promotion re-solves the full span in one
invocation and one bundle (rule 16 `[R-ALLYEARS]`).

---

## 3. THE GATES — **STOP-ONLY, STRUCTURAL, AND NOT KEYED TO THE TARGET RESIDUAL**

A screen may kill an arm; it may never promote one. **No gate below reads C1 `CC_REGULAR`, C3a, or
the gas volume** — gating on the target residual is the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids, done one year at a time. Values are fixed here, before the solves.

* **G-1 — LIVENESS.** The solve log must carry the line
  `aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope`
  with `declared scalar 8700 MW`. **Absent ⇒ the arm did not fire; the shard STOPS and pushes
  nothing.**
* **G-2 — FOOTPRINT CONFINEMENT.** The armed solve's hourly net interchange must satisfy the new
  bounds to within 1 MW in **every** hour (`−export_env ≤ flow ≤ import_env`), and **no other
  interface group's flow may move outside** what the changed interchange implies. A violation means
  the injected row is not the row I think it is. **STOP.**
* **G-3 — THE RAIL MUST BREAK.** Hours at the ±8,700 scalar must fall from **8,650 → 0** (2021) and
  **2,609 → 0** (2022): the scalar is gone, so *by construction* nothing can sit on it. Any nonzero
  count means a second, unaudited path is setting the aggregate flow. **STOP.**
* **G-4 — NOT A PIN (the load-bearing legitimacy gate).** The armed solve must **not** simply rail
  the new envelope in place of the old scalar. Pre-registered line: hours at ≥ 99 % of the import
  envelope must be **< 80 % of the year** in the screened year. At or above 80 % the mechanism has
  merely relocated the rail, the LP is still not clearing imports on merit, and the arm is **not
  promotable as a price-formation repair** however the volumes read. **STOP-on-report** — this one
  does not kill the code (the provenance repair stands on rule 14 regardless), it kills the claim
  that the arm resolves the object, and the session says so.
* **G-5 — NO NON-TARGET LOAD-BEARING FLIP.** No load-bearing criterion **other than** the fuel-mix
  and dispatch-correlation rows the interchange change necessarily moves may flip PASS → FAIL.
  Specifically C2 (system volume), C6 (governance) and C8 (forced share) must hold. **STOP.**
* **G-6 — REPORTED, NEVER A KILL AND NEVER A PROMOTION.** The import/export TWh, the C1 and C4
  rows, and the per-year determination are **recorded at full magnitude** and contribute to no
  gate in either direction.

**What the mechanism's own arithmetic predicts, written down before the solves so it can be
wrong:** 2021 net import falls from 75.93 TWh toward a **49.62 TWh ceiling** (so at most ~26.3 TWh
of the +40.41 TWh import error is removed — **the arm cannot close the 2021 miss and is not claimed
to**); 2022 net export is clipped toward the ~2.0 TWh export ceiling from −22.58 TWh, a much larger
move than 2021's. If 2021 moves more than 2022 in absolute MWh, the mechanism is not doing what its
own envelope says. **STOP.**

---

## 4. CONTROL — rule 29(b) form 4, **NO CONTROL SOLVE IS SPENT**

The controls are the **committed** bundles `results/calibration/miso251_tp2021` (2021) and
`results/calibration/miso251_screen2022` (2022), both keeper-recipe replays carrying the identical
seam configuration (verified field-by-field against `miso_fuelvintage_A`). The arm is a single
`--set` delta on top of the same recipe.

### G-DRIFT (code-level, zero LP)

`git diff 4d498369 origin/main -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` →
25 files, +4,066/−47. **Every hunk classified INERT for MISO 2021/2022:**

| file(s) | classification |
|---|---|
| `model/lp/model.py` | **The only changed file whose diff names MISO** — miso-253's memory-lifetime fix, documented in the hunk itself as "the LP, its optimum and every extracted dual are bit-identical". Allocation lifetime only. INERT. |
| `fleet/arrays.py`, `data/outages.py`, `data/renewables.py`, `pipeline/ttc.py`, `runner.py`, `fuel/hubs.py` | New behaviour is behind `unit_outage_short_windows_gas`, `mustrun_window_commitment_grain`, `spp_curtailment_ceiling`, `vre_curtailment_oversupply_allocation`, `nyiso_total_east_cutset_ttc`, `nyiso_hub_gap_month_level` — **every one default `False` AND absent from all three MISO recipes** (verified against each `run_config.json`). INERT. |
| `interchange/caiso.py`, `interchange/spec.py`, `data/curtailment_share.py`, `scripts/lib/spp63_g5.py`, `scripts/lib/forecast_parity_registry.py` | Another ISO's branch (CAISO / SPP) or the forecast namespace, which a `mode="backcast"` MISO run never enters. INERT. |
| `constants.py`, `scenarios.py`, `solve_surface_declared.py` | Additive field/constant registration; the cache-key gate confirms 297/297 declared defaults match HEAD and no MISO key moves. INERT. |
| `scripts/lib/solve_container.py` (new), `run_calibration*.py` | miso-254's container preflight — swap and thread pins. Memory, not dispatch. INERT. |
| `data/raw/reference/reliability_floor_coeffs_NYISO.csv`, `spp_curtailment_share.csv`, `_validation-source/*SPP*`, `actual_lmp.json` | Another ISO's artifact, or a scoring comparator that is not a solve input. INERT. |

**Empirical anchor, stronger than the hunk audit and already paid for:** miso-254 shard A replayed
the committed MISO keeper on **2023** at SHA `0101b4ce` (≈ HEAD) and reproduced the committed P1
price sidecar **exactly — 0 of 490,560 cells differ** (`docs/SHARD-misooom-A-2023.md`). The MISO
backcast solve path has measured zero drift at HEAD.

**This session's own hunks** (the new field, estimator, injector and runner call) are gated
default-off and inert off-gate by construction and by test
(`test_default_is_off_and_registered`, `test_non_miso_iso_is_a_noop`,
`test_unresolvable_year_keeps_the_declared_scalar`).

**Verdict: all hunks INERT ⇒ form 4 is valid, the committed bundles are the controls, and NO
control solve is spent.**

---

## 5. EXECUTION — rule 32 `[R-SHARD]`

**The parent runs no LP.** Two shards, one per screen year, each pinned to the full 40-character
SHA of the commit carrying this PRECOMMIT, each with its own `--out-dir` and branch, each
committing only its own bundle path. Neither registers anything, edits `src/` or `scripts/`, opens
a PR, or deletes any result (rule 31 `[R-RETAIN]`).

Command per shard (2021 shown):

```
uv run python scripts/replay_keeper.py results/calibration/miso251_tp2021 \
  --years 2021 --out-dir results/calibration/miso255_sil_2021 \
  --set miso_import_sil_measured_envelope=true \
  --note "miso-255 SIL measured-envelope screen"
```

Budget: MISO 2023 solved in **937.6 s** with the shipped container preflight (P0 525.8 s,
P1 269.0 s), peak `cgroup_peak_rss_plus_swap_gib=18.91` against a 13.34 GiB ceiling + 10 GiB of
self-provisioned swap — inside the 20-minute cap. Shards run the runner **unmodified** and never
pass `--no-container-preflight`.

**Retention (rule 31 `[R-RETAIN]`):** the `results/calibration/miso255_sil_*` family is gitignored
in this commit, which is what discharges rule 29(c) — nothing is `rm`'d, the bundles stay on disk,
and the promotion question is put to the owner before the session ends.
