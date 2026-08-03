# FINDING — caiso-162: CAISO per-year LCT pocket import caps

**Session** caiso-162 · **Date** 2026-08-03 · **ISO** CAISO · **Mechanism**
`caiso_per_year_import_caps` (matrix row `lcr_tsl_published`, CAISO cell
`U` → `O`) · **Incumbent keeper** `2026-08-03-caiso156-meter-screen-b`
(unchanged by this session)

**Registered runs**

| run id | bundle | arm |
|---|---|---|
| `2026-08-03-caiso162-control` | `caiso162_control_A` | A — control, flag **off** |
| `2026-08-03-caiso162-per-year-import` | `caiso162_peryear_import_caps_v2` | B v2 — treatment, flag **on** |

---

## 1. HEADLINE — the mechanism was unreachable from the backcast lane

The handoff framed task 0 as "there is no CLI flag." The flag was the smaller
half. **`apply_caiso_local_import_limits` had no call site in the calibration
lane at all.** Its only invocation was `runner.py:1627`, inside
`run_scenario_iso` — the **forecast/scenario** path. A backcast solve reaches
the LP through `scripts/run_calibration.py::run_year` →
`market_sim.pipeline.solve.run_energy_solve`, which never called it. Confirmed
by absence: the symbol appeared **nowhere** in `scripts/` or
`src/market_sim/pipeline/`.

So `caiso_per_year_import_caps` was structurally unreachable from **every**
backcast — whether set via the new CLI flag, `replay_keeper --set`, or the
`ScenarioConfig` field directly. That last route is precisely what the caiso-161
census assumed worked when it minted this cell `U`.

### 1a. How it was caught — flows, not prices

Arm B v1 recorded `caiso_per_year_import_caps=true` **in its own
`run_config.json`** (so the CLI threading was correct) and came back
**byte-identical to the flag-off control in all three years**.

**Read on prices alone, that is a clean `INERT` verdict.** It would have written
a **false `I`** onto the matrix for a mechanism that had never once executed —
and `I` is a DO-NOT-REDO code, so the error would have been self-sealing.

The flows falsified it:

| | 2024 LA_BASIN | 2024 SDGE | 2025 LA_BASIN | 2025 SDGE |
|---|---:|---:|---:|---:|
| arm B v1 max flow | **12008.00** | **1436.00** | **12008.00** | **1436.00** |
| published cap it should have used | 15224 | 2074 | 15174 | 2071 |

Topping out at *exactly* the static caps is unambiguous.

### 1b. The generalised lesson

caiso-161's lesson (a) — *check a field's **gate** before asserting a mechanism
is live* — generalises:

> **A `run_config.json` recording a mechanism as armed is not evidence the LP
> saw it. Also confirm a CALL SITE EXISTS ON THE LANE BEING SOLVED.**

A CAISO run config overstates what is armed in a second, previously
undocumented way: caiso-161 found six fields armed-but-gated-off; this adds
*armed, ungated, and unreachable because the lane has no call site*. The
instrument that discriminates them is the **flow/observable**, not the config
and not the price.

### 1c. The fix

Applied in `run_calibration.py` immediately after `_apply_iso_year_ttc` and
**before the import node joins**, so corrected links flow through incidence,
interface groups and the TTC array alike — the same placement rationale the
adjacent year-varying-interface-limits call already documents. Gated
**flag-first** (`iso == "CAISO" and getattr(config, ...)`), so it is a
byte-identical no-op for every existing run and for the flag-off control arm
(which therefore did **not** need re-solving at the new head).

---

## 2. A second self-inflicted defect: the prereg's control assertion

Prereg §7 asserted "2023 must come back byte-identical **to the keeper**." That
assumed the committed keeper bundle was a same-HEAD baseline. It is not — keeper
sha `69e0e30` vs this session's basis `de504ad`, **13 `src/market_sim` commits
apart**, several solve-affecting (lazy reserve balance-row materialization,
`retirement_rule` default legacy→pipeline, `entry_rate_limits` +
`entry_commissioning_lag` armed, net-CONE → `reindex_gross`).

Withdrawn in ADDENDUM A and replaced by arm A, a same-HEAD flag-off control.
Corroboration that the drift is real and material at the scale being measured:
**arm A scores C3a-2025 at +12.1% where the committed keeper scores +12.2%** —
a 0.1 pp gap from drift alone, comparable to the effect under test. Without arm
A the lever's entire signal would have been inside the drift.

"2023 is a built-in control" removes the need for a separate control **year**,
never the need for a same-HEAD control **run**.

---

## 3. MEASURED RESULT (arm A vs arm B v2, same head, single flag delta)

**Flows — the mechanism now reaches the LP:**

| year | pocket | A max | B v2 max | published cap |
|---|---|---:|---:|---:|
| 2023 | LA_BASIN | 9423.57 | 9423.57 | 12008 |
| 2023 | SDGE | 1436.00 | 1436.00 | 1436 |
| 2024 | LA_BASIN | 12008.00 | 13318.60 | 15224 |
| 2024 | SDGE | 1436.00 | **2074.00** | 2074 (binding) |
| 2025 | LA_BASIN | 12008.00 | 14404.78 | 15174 |
| 2025 | SDGE | 1436.00 | **2071.00** | 2071 (binding) |

**Prices — load-weighted mean LMP:**

| year | A | B v2 | delta | % of level |
|---|---:|---:|---:|---:|
| 2023 | 55.9532 | 55.9532 | +0.0000 | **BYTE-IDENTICAL** |
| 2024 | 37.8297 | 37.7665 | −0.0632 | **−0.1670%** |
| 2025 | 38.5646 | 38.5169 | −0.0477 | **−0.1236%** |

**The zero-delta control PASSED** (restated §7): 2023 byte-identical, as required
by the mechanism being a provable no-op there.

**C3a-2025: +12.1% (A) → +12.0% (B v2).**

**Guards: ZERO flips A → B v2** on all nine criteria (C1, C2, C3a, C3b, C3c, C4,
C6, C7, C8). C3a/C3c read FAIL on **both** arms only because a replay probe
bundle carries no `calibration_attestation.json`, so the keeper's ledgered
caveats degrade to MODEL MISS — identical on both sides, so the A/B is
unaffected. Import volume: the WECC seam cap is untouched by this arm (§4), and
the zonal signature (§3a) shows redistribution *inside* SP15, not extra
importing.

### 3a. Zonal signature — the mechanism's own, not a level shift

| zone | 2024 Δ | 2025 Δ |
|---|---:|---:|
| SDGE | **−0.958** | **−0.626** |
| LA_BASIN | +0.013 | −0.023 |
| SP15_rest | +0.045 | +0.037 |
| NP15 / ZP26 | +0.023 | +0.033 |

SDGE — the pocket whose cap actually binds (11.5% of hours) — carries the whole
effect. LA_BASIN barely moves **despite carrying 83% of the MW loosening**
(3,166 of 3,801 MW in 2025), because it binds in only 0.7% of hours. The rest
of the system ticks *up* slightly as energy is pulled toward the pocket. This
reproduces the pre-registered §2 binding pre-check exactly.

### 3b. The ceiling held

Prereg §3 pre-committed, before the solve, that removing the pocket premium
*entirely* moves 2025 by at most **$0.084/MWh (0.22% of level)** against the
**$0.76/MWh** needed to reach the ±10% band. Realised: **−$0.0477/MWh, 57% of
that ceiling.** The arm behaved inside its own ex-ante bound.

**Verdict against the pre-registered bars:** **PARTIAL CREDIT** (C3a-2025 moves
down ≥0.05 pp of level, no guard breach). The **PASS** bar was pre-registered as
unattainable by this arm and was not attained.

---

## 4. Rule 19 `[R-ONE-MECH]` — no double-count with the deliverability seam

The keeper runs `capacity_deliverability_limits=True` /
`local_capacity_constraints=False`. Disjoint objects:
`apply_deliverability_seam_limit` rewrites the `InterfaceLimit` whose links all
originate at `WECC_import` (the **external** seam);
`apply_caiso_local_import_limits` rewrites `links[].ttc_mw` on two **internal**
pocket links originating at `SP15_rest` that carry no `InterfaceLimit`. Total
WECC import capability is unchanged — only its distribution past the pocket
boundary moves.

---

## 5. Governance note (the question the owner posed)

The caiso-141 **A2 pumped-storage data wall** underpinning the C3a-2025 ledger
slot was **not reopened** and is **not challenged**. The narrow question — could
this lever, invisible to the matrix when the ledger entry was adopted at
caiso-145, own part of the residual charged to A2?

**Measured bound: ≤0.22 pp of a 12.2 pp residual — under 2% of it**, and that is
a ceiling, not an estimate (§3b). **The A2 attribution is not materially
undermined.** Recorded so the owner holds the number before any
`calibration-complete` marker is considered.

---

## 6. DISPOSITION — rule 14 `[R-ACCURATE]`, pre-committed before the result

The published per-year LCT capability is measured, same-convention,
forward-reproducible and responsive to changed conditions. It **beats the frozen
2023 estimate regardless of fit**. It is **not reverted and not parked**. Zero
free parameters; no new caveat; no ledger slot spent; the DOF ledger is
unchanged.

**The cell is `O`, not `K`, only because promotion is a separate governance act
this session stopped short of.** A replay probe bundle carries no
`calibration_attestation.json`, so promoting requires carrying the keeper's
ledger forward, updating `keepers/CAISO.json`, re-running the
`calibration-keeper-auditor` and `build_status.py --iso CAISO`.

**RECOMMENDED FOR PROMOTION** on the evidence: structurally correct, strictly
more accurate input, fit improves in both non-degenerate years, zero guard
flips, and **LOYO-clean by construction** — 2023 is a provable no-op and 2024
and 2025 both improve, so no year carries the result.

---

## 7. DO-NOT-REDO

- **Do not re-test whether the mechanism "works."** It is wired and measured.
  Its size is bounded by §3b and that bound is a property of the keeper's own
  dispatch, not of this arm.
- **Do not propose this lever for C3a-2025.** The ceiling is ~11% of the gap;
  it was pre-registered as unable to clear the gate and did not.
- **Do not reopen** the caiso-141 A2 wall, the caiso-131/144 C3c routes, or the
  caiso-104 charge-allocation family.
- **`caiso_asymmetric_path_ratings` remains untested** and is the other
  caiso-161 queue item — its own single-delta arm, not bundled here.

## 8. Filed for the owner (not acted on)

- `caiso_gas_floor_frac` = 0.80 remains the rule-26 `[R-DELETE]` deletion
  candidate caiso-161 filed (provably inert; gated on
  `caiso_gas_commitment_floor`, which is False).
- **A pre-existing tree-wide lint break** (F841 in
  `scripts/gen_nyiso115_attestation.py` from `6f102b1`) was failing the
  "Ruff lint + format" CI job on **every** PR. Fixed here in its own commit,
  labelled as out-of-lane. Two CI jobs remain red on main and were left alone:
  "Forecast-invariant artifact audit" and "Fast test tier".
