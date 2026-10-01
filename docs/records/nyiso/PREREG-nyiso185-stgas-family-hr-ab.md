# PRE-REGISTRATION — nyiso-185 (`stgas-family-hr-ab` lane): ONE grounding bar that separates the loaded heat rate from the idle-load denominator, then the A/B the owner authorized

**Session:** nyiso-185, NYISO backcast-calibration track, 2026-09-04.
**Branch:** `claude/nyiso-185-stgas-family-hr-ab`, fresh off `origin/main` at
`4b24ad3c` (which carries every nyiso-184 commit: PR #4672 the pre-registration,
PR #4675 the code, artifact and docs).
**Keeper at entry:** `2026-09-02-nyiso-177-vintage-matched`
(`results/calibration/nyiso177_vintage_B1p`) — determination **NOT-YET**,
target grade 5, fail set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**.

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE FIRST
MEASUREMENT OF THIS SESSION.** Every bar, verdict rule and stop condition is
fixed here. No solve, no reconstruction and no probe output of this session's
own making exists at the time of writing.

---

## §0 — DISCLOSURE, including the one this session cannot avoid

**This session runs in the SAME container and the SAME model context as
nyiso-184.** The author therefore HOLDS, at writing time, every number
nyiso-184 produced — including the post-hoc `POSTHOC_r_decomposition` block
the handoff told a fresh successor not to read before its bar was pushed.
Specifically the author knows: Ravenswood's annual/loaded factor **1.029**
against the peers' **1.001–1.071**; the exact heat boundary (1.0000); the
gross→net factor **1.115** (net/gross 0.897) against peers' 1.043–1.083; the
per-unit net/gross **0.913 / 0.933 / 0.862**; the peers' plant net ÷ CAMPD
steam gross 0.923–0.959 (with 2517 / 2511 polluted by their GTs at 1.094 /
1.030); the per-vintage family record 11.47 → 12.57 → 12.29. **The bar
below cannot be blind. What it can be is PRINCIPLED**: it is stated as the
rule that would have been written by anyone who had read only nyiso-184 §3
("the heat side is what the join controls; the denominator is the published
convention every peer carries"), and the reader is told exactly which numbers
were known so the choice can be judged. The alternative — pretending
ignorance — would be worse.

Everything else held: the whole nyiso-184 record (finding, prereg, JSON,
probe, derive, artifact), nyiso-183 §7 / §12, the matrix §5.5 queue and the
three NYISO shard cells named in the brief, the owner's 2026-09-04 ruling
verbatim, `CLAUDE.md` rules 1, 5, 12–16, 19, 21–25, 27, 28. Not opened this
session: any bundle's `metrics.json` / `legitimacy_diagnostics.json`; no
score, price or residual of any run.

---

## §1 — THE OWNER'S RULING AND WHAT IT AUTHORIZES

Verbatim (2026-09-04): *"If structural integrity improves but gates regress
that may still be a keeper.."* — the standing nyiso-155 / -157 / -159 / -177
formula. Read here, before any measurement, as: **the A/B nyiso-184's S2
withheld is AUTHORIZED** — the construction's consequence is to be MEASURED,
not inferred — and **nothing is promoted in advance**. The verdict rule (§4)
decides candidate vs probe; the owner decides promotion.

---

## §2 — RULE 19 `[R-ONE-MECH]`, re-checked on the code (not re-derived)

nyiso-184 PREREG §1 / FINDING §2 is the record: mechanism 1 (plant-grain eGRID
join) owns Ravenswood's 8.80 and mechanism 5 (`MIXED_FACILITY_STEAM_HR`)
owns its 9.50; `measured_ct_heat_rates` (CT_PEAKER rows; 2500 absent from the
artifact), `measured_chp_heat_rates` (CHP; 2500 absent), `egrid_identity_heat_rates`
(7784 only) and the boundary repair (`gas_cc`, {55641}) do not reach
(2500, ST). Under `egrid_family_heat_rates=True`, `_apply_egrid_family_heat_rates`
runs at the eGRID-input seam and `_correct_mixed_facility_steam_hr` SKIPS the
covered plants — superseded, never stacked. **G3 below re-checks this on the
code and on the armed no-LP reconstruction; it is not re-derived.**

---

## §3 — THE GROUNDING BAR (step 1a): what the join controls, and only that

nyiso-184 G2c tested `r = eGRID rate ÷ CAMPD running-hour HR` and Ravenswood
missed the peers' band. `r` factorises exactly (nyiso-184 §3.1) into

```
r = F_H × F_B × F_D
F_H = CAMPD all-hours HR ÷ CAMPD running-hour HR      (annual vs loaded: the HEAT side)
F_B = eGRID family HTIAN ÷ CAMPD heat                  (heat boundary)
F_D = CAMPD gross ÷ EIA-923 net (eGRID GENNTAN)        (the DENOMINATOR convention)
```

**Principle, fixed now.** The family construction's claim is that eGRID at
family grain is the same BASIS every single-family peer carries. `F_H` and
`F_B` are what the construction controls: whether the family's heat input is
the right heat input and whether an annual rate stands in for a loaded one the
way it does at every peer. `F_D` is EIA-923's published net-generation
convention — it charges idle-period station service against output at every
plant — and it is IDENTICAL by construction between Ravenswood and each peer;
its LEVEL at a plant is a fact about that plant's station service and
capacity factor, not about the join. **A grounding bar on `F_D` would test
Ravenswood's auxiliaries, not the construction; nyiso-184 G2c conflated the
two.** So:

* **G1a — HEAT SIDE.** `F_H(2500)`, over the plant's `ST_GAS` CAMPD units
  (10 / 20 / 30), lies within `[min, max]` of `F_H` over nyiso-183's eight
  peers (2527, 2625, 2516, 2490, 2517, 2480, 8006, 2511), each over its own
  `ST_GAS` units on the keeper's crosswalk (`stgas_units`), CAMPD 2023.
* **G1b — HEAT BOUNDARY.** `F_B(2500, ST)` within `[0.99, 1.01]` — eGRID's
  family heat input IS the CEMS heat input (the construction reads no other
  heat); for the peers, `F_B` over their `ST` family (Σ`UNT23.HTIAN`, PRMVR
  ST) against their CAMPD steam heat, reported alongside.
* **G1c — PLANT-BOUNDARY RECONCILIATION (guards a broken EIA-923 row without
  gating station service).** Ravenswood's PLANT-level EIA-923 net ÷ CAMPD
  gross — `PLNGENAN(2500)` ÷ Σ CAMPD gross over EVERY unit of facility 2500
  (steam + `UCC001` + the GTs) — lies within `[min, max]` of the same
  plant-level statistic over the eight peers (`PLNGENAN` ÷ Σ CAMPD gross over
  every unit, GTs included on both sides). This is the nyiso-141 §2 external
  channel ("EIA-923 net over CAMPD gross … 0.92–0.96 at every genuine NY
  gas-steam peer"), applied at the boundary where EIA-923 and CAMPD are
  reconcilable.
* **G1d — REPORTED, NOT GATED:** `F_D` per family and per generator at 2500,
  each unit's 2023 capacity factor, and the peers' `F_D` — so the reader sees
  the idle-load effect at full magnitude and where it sits.

**G1 FIRES iff G1a ∧ G1b ∧ G1c.** Bars use the peers' own spread on the
identical statistic; the `[0.99, 1.01]` heat-boundary tolerance is the only
number chosen here and it is a tolerance on an identity, not a band on a
measurement.

**What a G1 failure means, fixed now:** the A/B is STILL RUN (§1, owner
authorization) but the arm **cannot be a KEEPER CANDIDATE**; it is registered
as a **PROBE** with the failed leg stated at full magnitude.

---

## §4 — THE A/B (steps 3–5)

* **Control:** `scripts/run_calibration_full.py --replay-bundle
  results/calibration/nyiso177_vintage_B1p --year 2023 2024 2025 --out-dir
  results/calibration/nyiso185_control` — the keeper's recorded recipe at
  HEAD. **G2 (instrument):** its hourly zonal prices against the committed
  keeper's `hourly/system_<year>.parquet`, all three years. Bit-identical
  (max |Δ| = 0.0) ⇒ the committed keeper IS the baseline and the control
  replay registers nothing. Non-identical ⇒ the control is registered as the
  baseline and the drift is named (count of hours moved, max |Δ|, per year).
* **Arm:** the identical replay plus **`--egrid-family-heat-rates`**, `--out-dir
  results/calibration/nyiso185_family_hr`. ONE invocation, years SEQUENTIAL
  (rules 16, 12). **G-DELTA:** the arm's `run_config.json` differs from the
  control's in exactly `egrid_family_heat_rates` (after normalizing
  registration-time defaults); anything else riding along is a stop (S4).
* **Verdict rule (step 1b), fixed now:** the arm is a **REJECTED PROBE** iff
  any of `C2`, `C3a`, `C3b` or `C8` flips PASS → FAIL against the baseline.
  Otherwise, with G1 fired, it is a **KEEPER CANDIDATE** put to the owner
  with the C1 movement in ALL THREE years, C3a in all three years, the DOF
  ledger (zero added), and every regression at full magnitude. With G1
  failed, it is a PROBE whatever the gates.
* **Pre-declared expectations (falsifiable, not bars):** (i) Ravenswood
  `ST_GAS` energy FALLS every year; (ii) C1-2023 `ST_GAS` moves toward zero;
  (iii) 2024 / 2025 `ST_GAS` DEEPEN (the other ten plants −6.776 / −7.957
  TWh short; nyiso-140 precedent, EXPECTED of a correct repair, never
  compensated); (iv) Ravenswood `CC_REGULAR` RISES (8.80 → 7.35); (v) NO
  price claim; C3a-2025 stays owner-court whatever it does.
* **LOYO:** the standard leave-one-year-out within 2023–2025 is scored from
  the arm's committed artifacts (`calibration_verdict.py`) before any
  promotion is proposed; in-sample gain with held-out degradation is
  reported as such.

## §5 — FORBIDDEN (nyiso-184 §5 F1–F10 carried verbatim, plus)

F11 — no second solve-affecting change in the arm; F12 — no re-derivation of
the artifact (vintage, families, window all as committed); F13 — the second
object (the merit-panel stack-duplicate defect) is its OWN pre-registration
and never rides in this arm; F14 — no edit of any bar after G1 is read.

## §6 — STOP CONDITIONS

S0 G0 fails (the no-LP reconstruction does not reproduce nyiso-184's bases
9.50 / 8.80 flag-off, or flag-on does not put (2500, ST) at 12.2918 × the
committed multipliers and (2500, CC) at 7.3499 × theirs with no plant outside
the nyiso-184 G4 footprint moving) ⇒ STOP, instrument failure. S1 G1 fails ⇒
the A/B runs, the arm is a PROBE, never a candidate. S2 memory: at most two
concurrent invocations, and the control is launched only after the arm's
first year is past LP build with headroom shown by `free -g`. S3 every
completed non-control solve is registered THIS session (rule 15). S4 G-DELTA
fails ⇒ the arm is re-solved, not registered. S5 2023–2025 only; no marker
requested; the freeze untouched.
