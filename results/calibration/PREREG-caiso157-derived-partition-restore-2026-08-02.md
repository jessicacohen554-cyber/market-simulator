# PREREG — caiso-157: the two silently-absent derived CLEAN partitions re-arm a RETIRED fitted import scalar in the CAISO keeper

**Written and committed BEFORE any arm is solved** (house rule; caiso-139..156
precedent). Everything below — the defect statement, the arms, the predicted
directions, the gates, the promotion rule and the kill conditions — is fixed at
this commit. No gate is added, dropped or re-thresholded after a solve.

* **Session:** caiso-157 (CAISO calibration).
  **Branch:** `claude/caiso-backcast-calibration-t2aume`.
* **Class: INPUT-INTEGRITY DEFECT FIX (the caiso-152/153/155 class), NOT a
  mechanism cell and NOT a price lever.** No matrix cell is re-tested, no new
  `ScenarioConfig` field exists, and **no config value changes in either arm** —
  the delta is whether two DERIVED-NOT-COMMITTED `data/clean` partitions that
  the keeper's own armed flags require are PRESENT on disk.
* **Rule 14 `[R-ACCURATE]` + rule 20 `[R-DOF]` + rule 24 `[R-REGISTRY]`** are the
  grounds. The lever was selected from a **provenance audit**, not from a
  residual: the defect was found by diffing `meta.shared_inputs` across the
  CAISO bundle lineage before any price statistic was read.
* **Rule 22:** solve years are **2023 2024 2025 ONLY**. CAISO holds NO
  `complete` and NO `final` marker; the holdout spend freeze is ACTIVE;
  `--holdout-authorized` is not passed; no out-of-training year is solved,
  scored or registered; no marker is written.
* **Rule 25 `[R-ISO-SCOPE]`:** CAISO-only. The audit's cross-ISO sweep (§1.4) is
  reported as an exposure statement for other lanes; **no other ISO is solved,
  scored, promoted or re-registered by this session.**
* **Disclosure (house honesty rule):** before this pre-registration existed, this
  session started ONE `replay_keeper` invocation of the keeper recipe to
  measure the environment, killed it ~45 s in during input loading (it is what
  surfaced the two degradation warnings), and **deleted its output directory**.
  No solve completed, no LP was scored, and nothing from it is quoted anywhere.

---

## 1. The defect — measured, on the committed keeper's own bytes

### 1.1 What is absent

`data/clean/` is DERIVED-and-disposable (gitignored) and dies with the
container, so every session must regenerate the partitions its recipe consumes.
Two partitions the CAISO keeper's armed flags require were absent at solve time:

| clean partition | consumed by | behaviour when absent |
|---|---|---|
| `hydro-plant-modes/CAISO` | `hydro_ror_split=True` | `data/hydro.py` logs `hydro_ror_split armed but no hydro-plant-modes classifier partition — fleet left fully shapeable` and **the RoR split does not happen** |
| `capacity-deliverability/CAISO` | `capacity_deliverability_limits=True` | `interchange/spec.py` Part A silently **no-ops** (`_seam_mw` is None), so the published branch-group **MIC** seam cap is never applied |

### 1.2 It is provable per bundle, and it dates the regression

`meta.shared_inputs` pins exactly the derived-not-committed inputs a bundle
solved on — `bundle_io.write_derived_solve_inputs`, whose own docstring calls
this "the silent-degrade trap" and records that *"an absent partition records
nothing, exactly the state the solve degraded to."* Auditing every CAISO bundle
on disk (`capacity_deliverability` / `hydro_plant_modes` keys present?):

| bundle | timestamp | `cdl` armed | cdl PIN | `ror` armed | ror PIN |
|---|---|---|---|---|---|
| `caiso138_envclip_B` | 2026-07-29T02:53 | True | **yes** | True | **yes** |
| `caiso139_control_A` / `_dumpguard_B` | 2026-07-29T04:51 / 05:18 | True | **yes** | True | **yes** |
| `caiso142_control_A` / `_seam_B` | 2026-07-30T04:26 / 04:48 | True | **yes** | True | **yes** |
| `caiso153_control_A` / **`caiso153_reid_B` (KEEPER)** | 2026-07-31T04:21 / 04:43 | True | **NO** | True | **NO** |
| `caiso146_control_A` / `_ctheatrate_B` | 2026-07-31T06:57 / 07:01 | True | **NO** | True | **NO** |
| `caiso147_control_A` / `_chp_B` | 2026-07-31T17:19 | True | **NO** | True | **NO** |
| `caiso148_control_A` / `_nucavail_B` | 2026-07-31T18:42 | True | **NO** | True | **NO** |
| `caiso151_control_A` / `_clip_B` | 2026-07-31T22:51 / 22:52 | True | **NO** | True | **NO** |

**The regression window is between caiso-142 (2026-07-30) and caiso-146
(2026-07-31)**, and every CAISO keeper promoted since — caiso-146, -147, -148,
-151, -153 — was solved with both mechanisms silently inert. No caiso-146..155
log entry mentions it; it was undetected.

### 1.3 The consequence that makes this a governance defect, not housekeeping

With Part A a no-op, the CAISO import node falls back to the hard-coded
`WECC_import_simultaneous` interface limit, **`cap_mw = 7,500 MW`**. That value
is a **residual-identified fitted scalar**. The keeper's OWN committed
`calibration_attestation.json` DOF ledger carries it and states, verbatim:

> `"name": "WECC_import_simultaneous.cap_mw"`,
> `"where": "iso_configs.py CAISO interface_limits (fallback; capacity_deliverability_limits OFF only)"`,
> `"identification": "residual"`, `"value": 7500.0`,
> `"source": "fitted aggregate WECC import cap — SUPERSEDED in the caiso-51 keeper by the published branch-group MIC sum (16,055/16,452/16,148 MW 2023/24/25) + measured p95 corridor envelopes … `**`Not in the keeper binding path`**`; governs the forecast / non-deliverability path only."`

and `iso_configs.py` (lines 414–428) says the scalar is carried "as a
fallback-only DOF-ledger row (scalar-remediation B-CAI-1, 2026-07-05) **so this
fallback cannot silently re-become the binding import limit**."

**Measured on the keeper's own committed `hourly/class_hourly_<year>.parquet`
(P1, `klass == "import"`, at-cap tolerance 0.5 MW) — the attestation is false:**

| year | hours pinned at 7,500 MW | share of year | mean import MW | binding hours concentrate at |
|---|---|---|---|---|
| 2023 | **757** | 8.6 % | 4,130 | hours 0–2 & 23; Jan/May/Feb/Mar |
| 2024 | **472** | 5.4 % | 4,514 | hours 0–4; Jun/Nov/Dec/May |
| 2025 | **864** | 9.9 % | 4,692 | hours 0–4; Dec/Nov/Jun/Oct |

and, decisively for the ledgered caveat, **Sep–Dec 2025: 528 of 2,928 hours
(18.0 %) are pinned at the fitted cap.** The keeper's p95, p99 and max import
are all *exactly* 7,500.000 MW in all three years.

So a **residual-identified DOF the attestation declares retired and non-binding
is in fact the binding import constraint in 5–10 % of every keeper year**, and
in nearly one Sep–Dec 2025 hour in five. Restoring the partition hands the
binding limit back to the MEASURED instruments the keeper intends: the published
MIC seam (**16,055 / 16,452 / 16,148 MW**, resolved this session from the
regenerated partition, 36/36/33 branch-group areas) and the measured p95
corridor envelopes (`caiso_corridor_flow_limit`, armed).

### 1.4 The hydro half, and the cross-ISO exposure

The regenerated `hydro-plant-modes/CAISO` partition classifies **195 plants —
84 non-shapeable (904.6 MW, 13.5 % of the 6,703 MW EHA conventional-hydro
fleet) and 111 shapeable**. With it absent the whole fleet is treated as
shapeable, which (a) removes the RoR flat-dispatch stamp
(`MECH_HYDRO_ROR_FLAT`, min == max at the plant's own monthly water) and (b)
**mis-allocates the armed `hydro_min_flow_floor`**, which `scenarios.py` (line
~1027) says is "RECONCILED" over the reservoir class only when `hydro_ror_split`
is armed. Both are D-2/D-4-visible floor mechanisms, so the keeper's committed
`legitimacy_diagnostics.json` describes a floor allocation the accurate input
would not produce.

**Cross-ISO sweep (audit only, no other ISO solved):** the pin-vs-armed audit
over all 131 bundles on disk shows **no other ISO arms either flag**, so the
degradation is CAISO-exclusive. MISO/NYISO bundles carry a
`capacity_deliverability` pin with the flag OFF (provenance capture is
unconditional) — not a defect. This is reported to the other lanes as an
exposure statement only.

## 2. Arms — zero config deltas; the delta is the presence of two files

Every arm replays the keeper's own `meta.json` at HEAD via
`scripts/replay_keeper.py`, years **sequential inside each invocation** (rules
12/16), **ONE solve at a time** on this 15 GB / 4-core box.

| arm | out-dir | `hydro-plant-modes/CAISO` | `capacity-deliverability/CAISO` |
|---|---|---|---|
| **A — control (degraded)** | `results/calibration/caiso157_control_A` | ABSENT | ABSENT |
| **B — both restored** | `results/calibration/caiso157_restore_B` | PRESENT | PRESENT |
| **C — seam only** (attribution) | `results/calibration/caiso157_capdel_C` | ABSENT | PRESENT |
| **D — hydro only** (attribution) | `results/calibration/caiso157_ror_D` | PRESENT | ABSENT |

* **Arm A is mandatory and is the honest baseline**, not the committed keeper:
  caiso-155 §D (D-13) established that committed CAISO bundles do NOT reproduce
  in a fresh container, so a committed-vs-B comparison would conflate
  vertex/stack drift with the lever. Arm A reproduces the keeper's *degraded
  input state* on this HEAD.
* All arms pass `--set nuclear_unit_availability=true` — **value-identical** to
  the keeper's own channel state (verified: the keeper's
  `coal_prb_sigmoid_overrides` carries `nuclear_unit_availability: True`), so
  the merged config is unchanged. The override exists solely so `replay_keeper`
  mints a fresh dated run id instead of restoring the keeper's date. **Config
  equality across all four arms is gate K3.**
* **Nothing under `src/` or `scripts/` changes between arms.** The partitions are
  moved in/out of `data/clean/` (gitignored) around each invocation; each arm's
  actual state is verified from its own written `meta.shared_inputs` (gate K1),
  never from what this session believes it staged.
* **Execution order, fixed: A → B → C → D.** A and B decide the keeper; C and D
  are attribution only. **Session-cut clause:** if the session ends before all
  four complete, every COMPLETED arm is registered and the FINDING states the
  cut explicitly; a promotion needs A and B only. C/D missing is a reported
  limitation, never silently omitted.
* `legitimacy_diagnostics.json` is generated IN-SESSION immediately after each
  arm's own solve, from that arm's own `floors/*_P?.npz` — never post-hoc, never
  from a rebuild, never from another bundle's replay (caiso-155 A1b/D-13).

## 3. Predicted directions — frozen before any solve

Stated so a matching result is a prediction and a non-matching one is a finding.

1. **Imports RISE in the ~5–10 % of hours the fitted cap pins** (A → B), by up
   to the 7,500 → corridor-envelope headroom. In the remaining ~90 % of hours
   the seam is slack in BOTH arms and the arms should be near-identical there.
2. **λ FALLS in those hours**, because the marginal displaced resource is
   thermal above the import tranche price. **Direction on the ledgered C3a-2025
   caveat is FAVOURABLE (the model is +9.92 % HIGH).** Magnitude is NOT
   predicted. **This does not make the arm a C3a lever and a favourable move is
   NOT its justification** (rule 1 `[R-STRUCT]`): the restoration ships because
   the input is the accurate one and the alternative is a residual-identified
   scalar the ledger says is retired. **An ADVERSE C3a move does not revert it
   either** (rule 14) — it would be a discovered-bug signal for a root-cause lane.
3. **The binding hours are OVERNIGHT** (hours 0–4, 23) in every year, so the
   arms should separate most in the overnight/belly bands and least at the
   evening peak. A separation concentrated at the evening peak instead would
   contradict the mechanism and is reported as such.
4. **C3c tail counts essentially unchanged.** Relaxing an import cap cannot
   manufacture $200+ hours and can only remove them; the ledgered C3c-2023/24
   caveat is NOT re-litigated by this session and is not quoted as closed.
5. **Hydro (arm D):** the RoR split FIXES 904.6 MW at flat monthly dispatch,
   so overnight hydro RISES and evening-peak hydro FALLS relative to arm A,
   with the annual water budget unchanged (the split re-allocates within the
   monthly budget, it does not add or remove energy). Net λ effect is NOT
   predicted — it lowers evening λ headroom while raising overnight supply.
6. **D-2 / C8 mechanism attribution CHANGES in arms B and D by construction:**
   `MECH_HYDRO_ROR_FLAT` rows appear and `MECH_HYDRO_MIN_FLOW` shrinks to the
   reservoir class. This is the accurate attribution, not a regression. Hydro is
   a non-thermal exempt class for C7/C8, so no gated verdict should move from it.
7. **B ≈ C + D at the system level** (the two mechanisms touch different
   constraints). A large interaction term is a finding and is reported.

## 4. Gates

**Construction gates — all must pass or the arms are not comparable:**

* **K1 — input-state fidelity, verified from the written bundles.** Each arm's
  own `meta.shared_inputs` must carry exactly the pins its row in §2 declares
  (`capacity_deliverability` / `hydro_plant_modes` present or absent). An arm
  whose pins disagree with its intended state is discarded and re-solved.
* **K2 — control integrity.** Arm A reproduces the committed keeper's
  determination and per-criterion statuses (values may drift — D-13 says
  vertices do). A status flip in the CONTROL is a stop-the-lane event: reported,
  never scored against the lever.
* **K3 — config equality.** All arms' `run_config.json` differ only in
  provenance (timestamp, git_sha, note, basis_sha). Any ScenarioConfig-field
  diff fails the pair.
* **K4 — year span.** Every bundle carries exactly [2023, 2024, 2025].
* **K5 — the seam actually re-arms.** Arm B's and arm C's solve logs must record
  `capacity_deliverability_limits — seam import cap set to 16055/16452/16148 MW`
  for 2023/24/25, and arm B's and arm D's must NOT emit the
  `hydro_ror_split armed but no hydro-plant-modes` warning. If arm B does not
  re-arm, the lane stops and the FINDING reports a wiring defect instead.
* **K6 — liveness, reported not gated.** `max |Δ import MW|` and
  `max |Δ zonal λ|` between A and B per year. An input correction ships
  regardless; a score-inert result is stated plainly, not oversold.

**Determination gates, per arm** (baseline: the committed keeper's scorecard +
its committed `legitimacy_diagnostics.json`):

* **Protective:** C7 `profile_r ≥ 0.80` / `cv_ratio ≥ 0.50` where gated; C8
  forced share ≤ 0.30 (0.15 peaker cap) on gated classes; **D-4 off-window
  binding 0.000 on every non-exempt mechanism.**
* **Scored:** C1, C2, C3a, C3b, C3c, C4 + determination, per arm per year,
  movement reported in BOTH directions.

## 5. Promotion rule, LOYO, and the kill conditions

* **The partitions are restored regardless of arm outcomes** (rule 14): they are
  the accurate inputs and their absence re-arms a retired fitted DOF. A degraded
  score is a discovered-bug signal for a root-cause lane, never a revert.
* **Arm B is promoted keeper iff:** K1–K5 pass, arm B carries no protective
  FAIL, no load-bearing criterion flips PASS → FAIL vs arm A, and the
  determination is no worse than the committed keeper's. Otherwise the committed
  keeper STANDS, the degradation is disclosed on its dashboard note, and the
  mismatch is filed as CAISO's next lane item.
* **LOYO (rule 22): this session fits nothing** — zero free parameters are
  introduced or moved, and both restored inputs are external published data
  (ORNL EHA/HILARRI; CAISO MIC/LCR postings). Leave-one-year-out therefore
  reduces to the no-held-out-degradation check: promotion of arm B when any
  |ΔC3a| ≥ 1.0 pp requires the three per-year deltas to agree in sign with the
  pooled delta, computed from the registered bundles — no extra solve.
* **The two ledgered caveats are NOT re-litigated.** C3c-2023/24 (caiso-131 A4)
  and C3a-2025 (caiso-141 A2 wall) remain the owner's act of caiso-145. This
  session claims **no closure of either**. What it does claim, and what the
  owner may later weigh, is **new evidence against a named cell**: caiso-140's
  D3 walk-down attributed the Sep–Dec 2025 belly λ to a "2.7–3.0 GW economic
  import-parity plateau"; §1.3 shows that in 18.0 % of those hours the plateau
  is not economic at all but a **hard fitted cap**. Any re-disposition of C3a is
  an OWNER act on that evidence, never this session's.
* **KILL conditions** (stop, report, promote nothing): (i) arm A fails K2;
  (ii) arm B fails K5 (the mechanisms do not re-arm); (iii) any arm fails K3;
  (iv) arm B shows a protective FAIL — in which case the partitions still ship
  as inputs but the keeper does not move, and the protective failure becomes the
  named successor item.

## 6. The root-cause fix that must land with the finding

A defect that silently disarmed two mechanisms across five keeper promotions and
went unnoticed for six sessions is a **missing guard**, not a one-off. This
session ships, alongside the arms, a **pre-solve input-completeness check**:
when a gated mechanism is armed and the clean partition it requires is absent,
the solve **raises** instead of logging a warning and degrading. It carries no
`ScenarioConfig` field, no threshold and no tunable (rule 24), and it is
ISO-generic. Scope is fixed here to the two mechanisms this session proves:
`capacity_deliverability_limits` (for ISOs that publish a seam `import_limit`)
and `hydro_ror_split`. Unit tests pin both the raise and the
flag-off no-op. Widening the check to other armed-flag/partition pairs is filed,
not absorbed.

## 7. Deliverables (rules 15 / 28b), regardless of verdict

* Every COMPLETED arm registered on the backcast dashboard
  (`scripts/dashboard_add_run.py`), sidecars + `runs/<id>.js` payloads +
  changed `bench/` committed; payload commits over `git push` after a fresh
  rebase on origin/main; blob verification after any ≥300-line push (rule 27).
  Labels: `caiso157 partition control A`, `caiso157 partition restore B`,
  `caiso157 seam only C`, `caiso157 ror only D`.
* `legitimacy_diagnostics.json` per arm, generated in-session (§2).
* FINDING doc + `docs/calibration-log/caiso.md` entry with a DO-NOT-REDO
  section; matrix (`mechanism-matrix.js`) note/evidence updates on the
  `capacity_deliverability` and `hydro_ror_split` rows — **cells only move if a
  verdict actually moves**; keeper shard edit + `build_status.py --iso CAISO` +
  the keeper-auditor agent **only if arm B is promoted**.
* If arm B is promoted, its `calibration_attestation.json` DOF row for
  `WECC_import_simultaneous.cap_mw` is **re-verified true** on the new bundle
  (the scalar must no longer bind), and the FINDING states the measured
  binding-hour count on the promoted arm.
