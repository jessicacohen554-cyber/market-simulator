# PRE-REGISTRATION — nyiso-116: the C3c unit/network layer, and what the 2024 pin actually needs

**Date:** 2026-08-03 · **Scope:** NYISO 2023–2025 ·
**Keeper:** `2026-08-02-nyiso-113-li-locational` — this session proposes **no
promotion, no demotion, no re-key** · **Pushed before any solve.**

---

## §0 — what is already settled NO-LP, before this arm runs

Three measurements were made from **committed artifacts only** (the keeper
bundle `nyiso113_lilocational_B` and the nyiso-114 recipe re-solve
`nyiso114_lilocational_confirm`), with no LP spent. They are recorded here
*before* the arm so the arm cannot be read as having produced them.

1. **The settlement basis is INERT for C3c, all three years.** Adding the
   co-opt's own locational reserve duals to the zonal energy LMP — the
   `RCPF-into-LBMP` settlement basis `calibration_verdict.py`'s own G-20a
   comment names for NYISO — leaves the C3c count at **3 / 0 / 14**, unchanged
   in every year. Cause, measured: the locational adder is nonzero **only in
   hours whose energy price already exceeds $300**, and is **exactly $0.00 in
   all three 2024 pinned hours**; every one of 2024's 7 family-binding hours has
   max-zonal ≤ $250. The reserve families never arrive before the energy price.
   **The NYC-pair lane is therefore measured dead for C3c** — on the very
   instrument (nyiso-114's `reserve_family` sidecar) built to see it.
2. **The knife-edge is a red herring.** C3c gates on ratio ∈ [0.5×, 2×] of the
   RT actual (`TAIL_LO/TAIL_HI`), and 2024's actual is 12 ≥ `TAIL_SMALL_COUNT`,
   so the model needs **≥ 6 hours** > $300. The keeper's **6th-highest**
   max-zonal hour of 2024 is **$201.694** — it needs **+$98.31 (+48.7 %)**.
   Lifting the celebrated $2.46 pin yields 3 hours = **0.25×**, which **still
   FAILS**. The "$2.46 knife-edge" describes hours 1–3; the gate is decided by
   hour 6.
3. **The G1 replay divergence does not reach the C3c tail.** Keeper vs. recipe:
   all zone-hours differ by up to $10.50/$10.56/$9.04, but the **top-20 tail
   hours** differ by **$0.000000 (2023)**, $1.79 (2024), $4.74 (2025), and the
   C3c count is **3/0/14 in both**. A globally-failing replay can still be a
   faithful instrument for a specific gate; that has to be shown per gate, and
   it is shown here for C3c.

## §1 — the gap this arm exists to close

nyiso-114 §6 attributed the 2024 pin to a named unit, a named offer rung and two
named transmission limits. **None of it is reproducible from any committed
artifact.** `hourly/unit_hourly_*.parquet` and `hourly/network_*.parquet` are
excluded by `.gitignore:325–330`, on the stated ground that they are
"**regenerable by a replay**" — and nyiso-114 §2 *measured* that a replay does
**not** reproduce a keeper arming a P0-run-pattern bridge once main has moved.
The two statements cannot both be true. For this keeper the unit/network layer
is therefore **permanently unrecoverable**, and it is exactly the layer C3c
attribution needs.

This arm emits that layer, verifies §6's four claims against it, and commits it.

## §2 — the arm

`nyiso116_c3c_unitlayer` — a **zero-delta** replay of the nyiso-113 keeper
recipe across **2023, 2024, 2025 in one bundle** (rule 16). No `--set`, no
config field touched.

```
PYTHONPATH=.:src python scripts/replay_keeper.py \
  results/calibration/nyiso113_lilocational_B \
  --out-dir results/calibration/nyiso116_c3c_unitlayer \
  --years 2023 2024 2025 \
  --note "nyiso-116 zero-delta: emit + commit the unit/network layer for C3c attribution"
```

### Known risk, named in advance

**G1 will fail** — the replay will not reproduce the keeper bundle globally
(nyiso-114 §2, caiso-155 vertex dependence). This is pre-registered as a
**labelling** gate exactly as nyiso-114 pre-registered it: its outcome decides
whether results are reported as "measured on the keeper" or "measured on the
recipe", never whether they are reported at all.

## §3 — construction gates

| id | gate | instrument it is read on | fail ⇒ |
|---|---|---|---|
| **G1** | replay reproduces the keeper globally | `hourly/system_<y>.parquet`, both bundles, all zone-hours | labels flip to "recipe", nothing suppressed |
| **G2** | **replay is faithful *for C3c*** — max-zonal count = keeper's 3/0/14 **and** top-8 max-zonal values within $5.00 | `hourly/system_<y>.parquet`, both bundles | **K-A fires** |
| **G3** | sidecars well-formed — `unit_hourly` + `network` present for all 3 years, no NaN, `mw ≤ cap_mw + 1e-6` everywhere | the new `hourly/*.parquet` | instrument unusable; report and stop |
| **G4** | **§6 verified** — its four claims re-measured on 2024 h4528–4530, each scored CONFIRMED/REFUTED individually | `unit_hourly_2024`, `network_2024`, `reserve_family_2024` | see K-B |
| **G5** | span — 2023–2025 in one bundle, no year outside | `meta.json` | rule 16/22 breach; stop |

**Every gate names the artifact it is read on, and every named artifact carries
the column the gate needs.** G2 reads `price` per zone (present). G3 reads
`mw`/`cap_mw` (present, `_unit_hourly_frame`) and the network frame's flow/limit
columns — **verified present in the writer before this prereg was written**
(`run_calibration_full._network_frame`), which is the check nyiso-113's K3/K4
skipped and nyiso-114's G3 passed only because `held_mw` had been added.
G4's reserve leg reads `dual` per family (present since nyiso-114).

## §4 — kills

* **K-A — if G2 fails, no unit-level C3c attribution may be claimed from this
  bundle at all.** Report the instrument as unavailable for this keeper and
  stop. Attribution must be *measured*, not asserted, and a bundle that does not
  reproduce the gate cannot attribute it.
* **K-B — a REFUTED §6 claim is reported as refuted.** No lever may be proposed
  from, or repaired onto, a refuted attribution. nyiso-114 §3 refuted its own
  predecessor's P5 and said so; that is the standard.
* **K-C — no-tuning clause (binding).** This session introduces, changes and
  fits **nothing**. Specifically forbidden: the LI oil offer rung, the LI import
  limits (`measured_interface_limits` is cell **G**), the LI/NYC reserve
  requirements, their $25/MW value or the On-Peak calendar (nyiso-113 binding
  clause), the 227-3 compliance file, and the ramp envelope. **No mechanism
  sized to the $2.46 pin may be proposed** — §0(2) shows such a mechanism would
  not even pass the gate it targets.
* **K-D — DO-NOT-REDO.** No NYISO cell marked `R`/`I`/`G` is re-tested:
  `nyiso_east_reserve_families` (I), `measured_ramp_capability` (I),
  `nyiso_spin_reserve_online` (I), `nyiso_rcpf_postsolve_overlay` (G),
  `measured_interface_limits` (G), and the rest of the G list stand.

## §5 — predictions, to be scored

| id | prediction |
|---|---|
| **P1** | G1 **FAILS** — the replay diverges from the keeper globally |
| **P2** | G2 **PASSES** — C3c count 3/0/14 (already measured NO-LP on the recipe bundle) |
| **P3** | §6 transmission claim **CONFIRMED** — `NYC>Long_Island` and `NYISO_external>Long_Island` both at their limits in h4528–4530 |
| **P4** | §6 marginal-unit claim **CONFIRMED** — exactly one part-loaded LI generator, an OIL tranche, at a rung ≈ $297.539 |
| **P5** | §6 idle-capacity claim **CONFIRMED to ±5 MW** — ≈ 596.9 MW idle on Long Island at h4528 |

## §6 — governance

* **Keeper UNCHANGED.** No promotion, demotion or re-key; the arm is registered
  as a **diagnostic**, never as a keeper candidate (G1 is expected to fail).
* **Rule 16** — all three years in one bundle. **Rule 22** — the holdout spend
  freeze is ACTIVE; no year outside 2023–2025 is solved, scored or read.
* **Rule 24 / 21** — no `ScenarioConfig` field, no CLI flag, no free parameter:
  the arm is an emission of already-solved primal/dual values. Zero DOF.
* **Rule 28(b)** — the matrix cell(s) this session adjudicates are updated in
  this same session, rejection/inertness included.
* **Rule 15** — the completed run is registered on the backcast dashboard in
  this session.
