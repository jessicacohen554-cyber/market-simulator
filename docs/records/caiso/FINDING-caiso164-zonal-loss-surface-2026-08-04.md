# FINDING — caiso-164: CAISO zonal marginal-loss surface

**Session** caiso-164 · **Date** 2026-08-04 · **Branch**
`claude/caiso-ns-basis-root-cause-b3f9qo` · **Base** `6040f28c`

**Mechanism** `ScenarioConfig.caiso_zonal_loss_surface` · matrix row
`zonal_loss_surface` (CAISO cell `U` → **`K`**) · **Prereg**
`PRECHECK-caiso164-zonal-loss-surface-2026-08-04.md`, pushed at `eda8ebe8`
**before either arm solved**.

**Outcome: KEPT and PROMOTED.** New CAISO keeper
`2026-08-04-caiso164-zonal-loss-surface`; A/B control
`2026-08-04-control-flagoff-lossless-baseline`. Determination
**CALIBRATED-WITH-CAVEATS**, carried over unchanged (2 ledgered, 0 FAILs,
protective 3/3 PASS, **zero criterion flips**).

---

## 0. Headline

**CAISO's north–south basis now carries the correct sign for the first time.**
Mean NP15 − ZP26 goes **−0.077 / −0.109 / −0.084 → +0.236 / +0.126 / +0.111
$/MWh** against a same-HEAD control, and the zones separate **in the measured
direction** (NP15 dearer) in **3,082 / 2,120 / 2,108 hours** where the control
managed **3 / 0 / 1**.

It gets there with **zero free parameters**, by replacing the model's implicit
*estimate* that transmission losses are zero with CAISO's **own published
marginal delivery-factor surface**.

The session's more useful contribution is the measurement that chose it. The
handoff said the successor must come from a decomposition, not from caiso-163's
named hypothesis — and the decomposition says the hypothesis was **not where the
recoverable component was**. §1.

---

## 1. §0 — THE DIAGNOSIS, AND WHY IT OVERTURNED THE LEADING HYPOTHESIS

No LP. Committed artifacts only: the caiso-163 keeper's `hourly/system_<y>`
sidecars and `data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv`
(`scripts/probes/caiso164_ns_basis_decomp.py`, `caiso164_zonal_surplus.py`).

### 1.1 CAISO publishes the congestion/loss split directly

A CAISO LMP is `MCE + MCC + MCL`, and MCE is the single system reference —
**identical at every node**, measured here to `0.00e+00` in all three years. So
any hub-to-hub basis is **exactly `dMCC + dMCL`**; no estimation is involved.

| year | pair | total | dMCE | **dMCC** | **dMCL** | cong % | loss % |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | NP15−ZP26 | 5.947 | 0.0000 | **4.771** | **1.176** | 80.2 % | 19.8 % |
| 2024 | NP15−ZP26 | 8.576 | 0.0000 | **7.475** | **1.102** | 87.2 % | 12.8 % |
| 2025 | NP15−ZP26 | 5.727 | 0.0000 | **4.677** | **1.049** | 81.7 % | 18.3 % |
| 2023 | NP15−SP15 | 2.337 | 0.0000 | 2.101 | 0.235 | 89.9 % | 10.1 % |
| 2024 | NP15−SP15 | 7.992 | 0.0000 | 7.148 | 0.844 | 89.4 % | 10.6 % |
| 2025 | NP15−SP15 | 6.009 | 0.0000 | 4.991 | 1.018 | 83.1 % | 16.9 % |

The LP is **lossless**, so it had *no representation whatsoever* of the `dMCL`
column. Not a calibration gap — a missing mechanism, whose current treatment is
the **estimate** "losses are zero" (rule 14 `[R-ACCURATE]`).

### 1.2 The congestion majority is a FREQUENCY-and-DIRECTION miss

Scored like-for-like (model price basis vs measured `dMCC`, since the model can
only produce the congestion component). `mean = sep_share × conditional_mean`,
so the two ratios multiply:

| year | measured sep % | model sep % | **FREQ ×** | measured \|cond\| | model \|cond\| | **MAG ×** | net × |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 68.87 % | 2.71 % | **0.039** | 7.196 | 2.859 | 0.397 | 0.0156 |
| 2024 | 87.70 % | 4.73 % | **0.054** | 9.014 | 2.299 | 0.255 | 0.0137 |
| 2025 | 93.11 % | 3.24 % | **0.035** | 5.927 | 2.625 | 0.443 | 0.0154 |

**Frequency dominates** — and it is worse than "too few hours". In the **top
decile of measured |dMCC|** (864 / 879 / 876 h, measured mean **+34.0 / +43.5 /
+30.3 $/MWh**, **100 % / 100 % / 99.9 % of them S→N**), the pre-arm model
separated in **0 hours**; swept over lags −3…+3 h the count never exceeded 30 of
~875. Its rare separations ran **99–100 % N→S**, the *opposite* direction.

### 1.3 The north was roughly right — **the south never got cheap**

2024, Pacific local hour, $/MWh:

| h | meas NP15 | meas ZP26 | meas Δ | mdl NP15 | mdl ZP26 | mdl Δ |
|---:|---:|---:|---:|---:|---:|---:|
| 09 | 31.54 | 9.77 | **+21.78** | 25.19 | 25.19 | 0.00 |
| 12 | 26.10 | 5.26 | **+20.83** | 19.40 | 19.40 | 0.00 |
| 14 | 28.58 | 7.06 | **+21.52** | 21.58 | 21.58 | 0.00 |

The model's NP15 tracked measured NP15 to a few $/MWh; its **ZP26 was
$14–19/MWh too expensive** midday. All five CAISO zones priced as one
copperplate — identical minima (−$20.00), identical p01/p05, identical sub-$0
counts (610/610/610 in 2024) — while the real south goes sub-$0 in **1,151 h
(ZP26) / 1,169 h (SP15)** against the north's 271 h.

### 1.4 Why — the part this lane cannot fix

Renewable **siting is correct**: ZP26 and SP15_rest run belly renewable/load
ratios of **2.1–3.5** and are in local surplus in ~2,850 of 2,920 belly hours.
But the **southern block as a whole is a net renewable IMPORTER** in the belly
(mean net **−3,679 / −2,494 / −834 MW**), because `LA_BASIN` carries **77–83
TWh** of load at a **0.11–0.12** belly ratio and absorbs the entire
ZP26 + SP15_rest surplus through a **12,008 MW one-way link that never binds**.
No surplus reaches Path 15, so Path 15 never binds S→N with a positive dual, so
the basis cannot form.

**→ DATA BLOCKER, FILED (§6).** Reproducing that needs the **intra-SP15**
corridor to congest — CAISO nodal / intra-zonal congestion data, which is **not
in `data/raw`**. Per the handoff and rules 1/13 it is filed with the measurement
that establishes it, **not approximated with a fitted proxy**.

---

## 2. What changed

`dev_z,m = Σ MCL_z,t / Σ MCE_t` over the month — the **same frozen estimator**
as `derive_miso_loss_surface.py` and `derive_pjm_loss_surface.py`, re-derived on
CAISO's own data by `scripts/data/derive_caiso_loss_surface.py` →
`data/raw/iso-specific-transmission/CAISO_loss_surface.csv` (240 rows).

Annual-mean `df_deviation`:

| zone | 2023 | 2024 | 2025 | source |
|---|---:|---:|---:|---|
| NP15 | −0.02660 | −0.01792 | −0.01450 | `TH_NP15_GEN-APND` |
| ZP26 | −0.04558 | −0.04274 | −0.04068 | `TH_ZP26_GEN-APND` |
| SP15_rest | −0.03039 | −0.03667 | −0.04080 | `TH_SP15_GEN-APND` |
| LA_BASIN | −0.03039 | −0.03667 | −0.04080 | `TH_SP15` — **interpolated** |
| SDGE | −0.03039 | −0.03667 | −0.04080 | `TH_SP15` — **interpolated** |

Each internal link splits into a one-way pair whose receiving-end
energy-balance coefficient is `1 − ε(month)`,
`ε = max(0, (dev_to − dev_from)/(1 + dev_to))`. `NP15` is the least-negative
deviation, so **the lossy direction is S→N** — the same direction the measured
congestion binds in. That is a property of CAISO's measured data, not a choice.

**Zero free parameters.** Nothing swept, blended or tuned; no residual
consulted. The only non-measured device is the `1e-3 $/MWh` loss-pair flow
tiebreaker (rule 9 `[R-EPSILON]`, storage-ε class). DOF ledger carried
**verbatim** at 11 entries / 9 residual, asserted by
`scripts/gen_caiso164_attestation.py`.

---

## 3. Pre-solve checks — run and passed BEFORE solving

The caiso-162/163 standing lesson applied ex ante: a `run_config.json` recording
a flag as armed is not evidence the LP saw it, and **liveness is verified on a
physical observable, never on prices**.

**Derive acceptance** (`--acceptance`, miso-76 B1 band `[0.5×, 1.5×]` on CAISO's
own quantities): **6/6 pair-years in band at 1.04–1.06×**.

**Wiring probe** (`scripts/probes/caiso164_wiring_probe.py`, exit 0):

| check | result |
|---|---|
| **W1** call site fires on the calibration lane | links **6 → 8**, all years |
| **W2** the flag is the gate | True, all years |
| **W3** builder REFUSES an unsplit topology | True (a signed lossy link would create energy) |
| **W3** loss oriented **S→N** | Path 15 S→N ε **0.01936 / 0.02516 / 0.02645**; N→S **clamped to None** |
| **W4** caiso-163 ratings survive the split | `NP15_ZP26` cap 3265 / rev 5400, `ZP26_SP15_rest` cap 4000 / rev 3000 — **2 links, signs [−1, +1]**, all years |
| **W5** WECC seam untouched | identical link set, **zero** lossy seam links |

W4 was the one real composition risk — the split doubles the link count on
exactly the two corridors caiso-163 bounds — and it is clean.

---

## 4. The A/B — every pre-registered gate

Both arms `--year 2023 2024 2025`, **one invocation and one bundle each**
(rule 16), years sequential (rule 12), in-session (never a CI runner), via
`replay_keeper.py --set caiso_zonal_loss_surface=<bool>`.

### Liveness (L1 / L3), on FLOWS

| path · year | control max N→S | control max S→N | control S→N h | control S→N TWh | arm h over ANY published cap |
|---|---:|---:|---:|---:|---:|
| Path 15 · 2023 | 3,265.0 | 5,400.0 | 3,277 | **6.079** | **0** |
| Path 15 · 2024 | 3,265.0 | 5,400.0 | 2,834 | **4.352** | **0** |
| Path 15 · 2025 | 3,265.0 | 5,400.0 | 2,733 | **3.820** | **0** |
| Path 26 · 2023–25 | 4,000.0 | ≤3,000.0 | 1,222 / 543 / 180 | 1.116 / 0.422 / 0.118 | **0** |

- **L1 PASS.** The control carries **6.08 / 4.35 / 3.82 TWh** of real S→N energy
  on Path 15 over 3,277 / 2,834 / 2,733 h — the corridor the surface makes lossy
  genuinely runs in the lossy direction, so the mechanism is **not inert**.
- **L3 PASS.** **Zero** treatment hours over any caiso-163 published directional
  cap, all paths, all years. The split did not loosen the ratings it composes
  with.

### Structural (S1–S4)

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **S1** mean NP15−ZP26, control → arm | −0.0768 → **+0.2362** | −0.1086 → **+0.1258** | −0.0841 → **+0.1113** |
| S1 — ACTUAL | +5.947 | +8.576 | +5.727 |
| **S1 verdict** | **PASS** | **PASS** | **PASS** |
| **S2** ceiling = measured dMCL | 1.176, **26.6 % used** | 1.102, **21.3 % used** | 1.049, **18.6 % used** |
| **S2 verdict** | **PASS** | **PASS** | **PASS** |
| **S3** hours NP15 ≠ ZP26 | 237 (2.7 %) → **3,332 (38.0 %)** | 414 (4.7 %) → **2,522 (28.8 %)** | 284 (3.2 %) → **2,388 (27.3 %)** |
| hours NP15 **DEARER** (measured direction) | 3 → **3,082** | 0 → **2,120** | 1 → **2,108** |
| **S3 verdict** | **PASS** | **PASS** | **PASS** |
| **S4** mean NP15−SP15_rest | −1.2265 → **−1.5665** | −0.9834 → **−0.9571** | −0.8221 → **−0.7427** |
| **S4 verdict** | **MISS** | **PASS** | **PASS** |
| recovered % of measured LOSS component | **26.6 %** | **21.3 %** | **18.6 %** |
| recovered % of total measured basis | 5.26 % | 2.73 % | 3.41 % |
| load-weighted λ | 55.9512 → 56.1596 (**+0.372 %**) | 37.7610 → 37.8801 (**+0.315 %**) | 38.5209 → 38.5613 (**+0.105 %**) |

λ rises slightly in every year — the expected direction, because **losses
consume energy**.

### Guards (G1–G6) — ZERO flips

| criterion | keeper | arm |
|---|---|---|
| C1 fuel-mix | PASS | PASS |
| C2 system volume | PASS | PASS |
| C3a mean LMP | CAVEAT (ledgered) | CAVEAT (ledgered) |
| C3b price shape | PASS | PASS |
| C3c price tail | CAVEAT (ledgered) | CAVEAT (ledgered) |
| C4 dispatch corr | PASS | PASS |
| C6 governance | PASS | PASS |
| C7 diurnal shape | PASS | PASS |
| C8 forced share | PASS | PASS |

**0 flips**, determination **CALIBRATED-WITH-CAVEATS** unchanged, 4 caveat
entries unchanged, **no new caveat slot spent**. G3–G6 are asserted by the
attestation generator (§5).

---

## 5. Governance

- **Config drift is EXACTLY ONE FIELD** against the same-HEAD control:
  `caiso_zonal_loss_surface` `False → True`, with **zero schema drift either
  way** (0 `arm_only`, 0 `other_only`). Computed with a present/absent-aware
  diff, never `dict.get`.
- Against the **incumbent** — an older HEAD — the field appears as `arm_only`
  because it did not exist, alongside three fields other sessions merged since
  (`exit_rate_limits`, `nyiso_seny_rcpf_increment_step`,
  `pjm_seam_envelope_by_neighbor`). That is a real hole, so it is **closed
  rather than waived**: the generator ASSERTS every inherited field holds its
  `ScenarioConfig` **default** in the arm. An inherited non-default would be an
  undeclared config change, and the generator fails on it.
- **Owner-decision default flips** (`retirement_rule → pipeline`,
  `entry_rate_limits` + `entry_commissioning_lag`,
  `net_cone_forward_escalation → reindex_gross`; D-1/D-2/D-3a) are **merged
  owner decisions, not this session's choices and not tuning**. Asserted on both
  grounds: forecast-gated capacity-evolution machinery unreachable at
  `mode="backcast"`, and identical across both arms.
- `gen_caiso164_attestation.py` **FAILS** if: an undeclared config delta appears
  against either comparator; schema drift exists against the same-HEAD control;
  an inherited field is off its default; the intended delta is absent; the owner
  flips differ between arms; `mode != "backcast"`; the DOF ledger moves off
  11/9; a solve year or surface year falls outside 2023–2025; a non-CAISO row
  appears in the surface; **the control carries zero S→N Path-15 hours** (the
  mechanism would be INERT and promotion forbidden); any treatment hour exceeds
  a published cap; **or the arm moves the basis by MORE than the measured
  dMCL** (§5 gate S2 — a loss mechanism cannot legitimately produce more
  separation than the losses it represents).
- **Rule 22.** CAISO holds **no** `complete` marker → no `calibration-complete`
  re-key (D-5(b) is for `complete` ISOs only) and no marker was written. The
  **holdout spend freeze is ACTIVE**: 2023/2024/2025 only, nothing outside it
  solved, scored or registered — asserted on both bundles *and* on the derived
  surface. LOYO reduces to the no-held-out-degradation check; this session fits
  nothing and moves no free parameter, and all three years show the same
  structural direction with no criterion flip in any year.
- **Rule 15.** Both arms registered. **Rule 16.** Three years, one bundle each.

### 5.1 Process note — the first control run was OOM-killed

Recorded rather than buried. The first control arm was killed by the kernel
(`Out of memory: Killed process 8145 (python)`, `anon-rss 8,846,836 kB`) while
finalizing 2025 with both arms resident on a 15 GB box; it wrote no bundle. The
treatment had already completed cleanly and is unaffected. The control was
**re-solved alone** and is the bundle reported here.

It remains a genuine same-HEAD control: the only commit between the two solves
(`5f02556e`) touched `scripts/gen_caiso164_attestation.py` and
`scripts/probes/caiso164_ab_gates.py`, **neither of which the LP imports**, so
the solve path is byte-identical across both runs.

*(Operational note for later sessions: rule 12 permits ~2 concurrent per-plant
multi-zone runs, but two full CAISO 2023–2025 replays overlap at their 2025
peaks on a 15 GB box. Stagger them or run CAISO pairs sequentially.)*

---

## 6. DATA BLOCKER FILED — CAISO intra-zonal congestion

**New blocker, established by measurement, not asserted.** The ~80–87 %
congestion majority of CAISO's N–S basis cannot be reached by any mechanism
available in `data/raw`.

**The measurement that establishes it** (§1.2–§1.4): the miss is
frequency-and-direction, not magnitude; in the top decile of measured
congestion — 100 % of it S→N — the model separated in **0 of 864/879/876
hours**; and the cause is that the southern block never reaches surplus because
`LA_BASIN`'s 77–83 TWh of load absorbs it behind a never-binding 12,008 MW
one-way link.

**What is needed:** CAISO nodal or DLAP-level LMP components and/or published
intra-SP15 (desert/Kern → LA basin) transfer limits. `data/raw/lmp-data/CAISO/`
carries only the three `TH_*_GEN-APND` hubs hourly; the 22 nodal
`DAM_LMP_GRP` zips cover individual days only (they were fetched to patch a
2023 hole), not a scoreable span.

**Not closable by an adder, haircut or residual-tuned value** (rules 1/13). It
joins the standing CAISO blockers: C3a-2025 (non-public hourly pumped-storage
data) and C3c-2023/24 (the SoCalGas OFO declaration record).

**Secondary, same root:** it is also what would let `LA_BASIN` and `SDGE` carry
their own measured loss deviations instead of the SP15 hub's (§2).

---

## 7. Carried caveats — recorded, not buried

1. **S4 misses in 2023.** Mean NP15 − SP15_rest goes −1.2265 → −1.5665, *away*
   from the measured +2.337, while 2024 and 2025 move toward it. Prereg §5
   disposition 4 pre-committed that **S1–S4 are measurements, not promotion
   criteria** — only S2's *ceiling* can fail the arm, and it passes with room.
   Rules 1/14 keep a structurally-correct measured mechanism whatever the
   residual does.
2. **2 of 5 zones are interpolated.** `LA_BASIN` and `SDGE` carry
   `interpolated=True`: CAISO's DLAP component record is not in `data/raw`, so
   they inherit the SP15 generation hub's measured deviation under rule 14's
   "reconciled version of the real data" clause rather than an invented scalar
   (rule 5). The three zones carrying **the quantity under test** — NP15, ZP26,
   SP15_rest — each have their **own measured hub**. PJM's analogue carries no
   interpolated zone; CAISO's does, and says so.
3. **The basis is not closed.** The arm recovers 26.6 / 21.3 / 18.6 % of the
   measured *loss* component and 5.26 / 2.73 / 3.41 % of the *total* basis.
   Measured sep % is 68.9 / 87.7 / 93.1 against the arm's 38.0 / 28.8 / 27.3.
   **No compensating adder, haircut or offset was added.**
4. **Not a C3a arm.** C3a-2025 is unchanged and remains the owner's ledgered
   caveat on the caiso-141 A2 data wall. λ moves +0.1 to +0.4 %.

---

## 8. Artifacts

| | |
|---|---|
| keeper bundle | `results/calibration/caiso164_zonal_loss_surface` |
| control bundle | `results/calibration/caiso164_control_lossless` |
| keeper run id | `2026-08-04-caiso164-zonal-loss-surface` |
| control run id | `2026-08-04-control-flagoff-lossless-baseline` |
| prereg | `results/calibration/PRECHECK-caiso164-zonal-loss-surface-2026-08-04.md` (`eda8ebe8`) |
| §0 decomposition probe | `scripts/probes/caiso164_ns_basis_decomp.py` |
| §0 surplus probe | `scripts/probes/caiso164_zonal_surplus.py` |
| pre-solve wiring probe | `scripts/probes/caiso164_wiring_probe.py` |
| gate reader | `scripts/probes/caiso164_ab_gates.py` (+ `_caiso164_ab_gates.json`) |
| attestation generator | `scripts/gen_caiso164_attestation.py` |
| derive | `scripts/data/derive_caiso_loss_surface.py` |
| surface | `data/raw/iso-specific-transmission/CAISO_loss_surface.csv` |
| LP mechanism | `interchange/caiso.py::apply_caiso_zonal_loss_links` + `build_caiso_link_loss` |

---

## 9. Standing lessons

1. **When the market publishes the decomposition, decompose before you
   hypothesise.** caiso-163 named reduced topology as the leading suspect. One
   no-LP probe over CAISO's own `MCE/MCC/MCL` split showed a fifth of the basis
   was a component the model *could not represent at all*, and that the
   remaining majority was a **direction** failure — not the magnitude failure
   the topology story implied. The successor was chosen from the measurement.
2. **"Too small" and "never, in the wrong direction" are different diagnoses.**
   Splitting the miss into frequency × conditional magnitude, then checking the
   *sign* in the widest measured hours, turned "the model under-separates" into
   "the model separates in 0 of 876 hours and backwards" — which pointed at a
   different mechanism entirely.
3. **Pre-register a ceiling, not just a floor.** Gate S2 made the arm fail if it
   *over*-performed. A loss mechanism that moved the basis further than the
   measured losses would have been a defect wearing a good result; the ceiling
   is what makes the realised +0.31/+0.23/+0.20 evidence rather than luck.
4. **A negative result is a filing, not a silence.** The congestion majority got
   a data blocker with the measurement attached, so the next session inherits a
   quantified boundary instead of re-deriving it.
