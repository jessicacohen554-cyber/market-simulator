# FINDING — caiso-197 (lane 3): `gas_st_wefor_base_override = 0.1591` at CAISO is **ACCEPTED on all pre-registered gates** — the ERCOT-fitted 0.21 stops governing CAISO's 2,858.8 MW of ST_GAS, replaced by a fully cited GADS-class EFORd derived from CAISO's own fleet census; ledger unchanged 11/8

**Pre-registration:** `PRECHECK-caiso197-stgas-wefor-2026-08-16.md`, committed and
pushed at `3a4d79db1` BEFORE the lane-3 solve, with the value FROZEN and the full
citation chain quoted. Gate spec applied as written:
`GATESPEC-caiso193-stgas-wefor-2026-08-11.md`. No band edited. Keeper UNCHANGED
this lane. 2023–2025 only; markers and freeze untouched. Registered run:
**`2026-08-16-caiso-197-l3-stgas`** (NOT-YET, C6 UNATTESTED — standard
non-keeper A/B posture). Control **shared with lane 2**
(`2026-08-16-caiso-197-l2-control`, BIT-ZERO vs the committed keeper, noise
floor 0.0) — the GATESPEC §6 sharing clause, disclosed in both FINDINGs.

## 0. Direction-hazard regime (verbatim from the GATESPEC, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

**Single-mechanism statement (required verbatim):** The A/B delta is
`gas_st_wefor_base_override` = 0.1591 at CAISO; no other input differs.

## 1. Gate tally — 5/5 PASS

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-FROZEN** | one value committed before any solve; no sweep, no second candidate; post-PRECHECK change voids | 0.1591 frozen at `3a4d79db1`; the census probe ran no LP and read no price; the value never moved. | **PASS** |
| **G-CITE** | full public chain, reproducible from the citations alone | EIA-860 census (six gas-ST units at plants 315/335/350, 2,858.8 MW — equal to the GATESPEC's own figure — through the SHIPPED fleet path) → NERC GADS "Generating Unit Statistical Brochure 3 — 2020-2024" FOSSIL Gas Primary EFORd rows by size class (committed corpus `data/raw/reference/nerc-gads-eford-2020-2024/` with recorded URL + retrieval) → capacity-weighted mean 15.9149 % → 0.1591. Record `_caiso197_stgas_census.json`; every link public and quoted in the PRECHECK. | **PASS** |
| **G-BAND** | value ∈ [0.03, 0.21] | 0.1591 — in band; the ceiling exception was never needed. | **PASS** |
| **G-POSITION** | position vs MISO's 0.10 explained by the census, never targeted | Written in the PRECHECK before the solve: CAISO's capacity is concentrated in the LARGEST published size classes (Ormond Beach's two 600-799 MW units = 52.2 % of the fleet at the near-highest published row, 19.31 %; Alamitos 5 at 400-599 = 15.22 %), where a mid-size fleet sits in the 10.35–11.26 % rows — the size mapping alone produces the position; no cross-ISO number entered the arithmetic. | **PASS** |
| **G-DOF** | ledger does not increase; field enters `measured` (cited); ERCOT 0.21 / MISO 0.10 byte-untouched | Built arm ledger **11/8 — unchanged** from the control (the cited override carries no free-parameter row, the committed MISO-keeper precedent: miso148 ledger has zero gas_st rows); `constants.THERMAL_AVAILABILITY` untouched, `backcast_config`'s MISO 0.10 untouched. | **PASS** |

Environment legs: seam caps 16055/16452/16148 logged in the arm solve;
`hydro_ror_split=false` disclosed; warm-start pinned off; arm solved after the
lane-2 arm completed (rule 12, arms sequential); highspy 1.14.0 / python
3.11.15 — the keeper's own stack.

## 2. Engagement and the criteria panel

**G-ONEMECH** (verified over the FULL config of both committed
`run_config.json`s): the diff is EXACTLY `gas_st_wefor_base_override`
None→0.1591 — the lane-2 fields sit at their CONTROL values (0.7/None/None)
in this arm, ST_GAS's question kept cleanly separate (rule 19). Record
`_caiso197_l3_gates.json`, `g_onemech.pass: true`.

**Engagement** (model artifacts only): prices change in **4,915 / 10,631 /
10,522 of 61,320 zone-hours** (2023/24/25; max single-hour |Δ| $82.2 / $481.9
/ $50.1), class-hour dispatch moves up to 629/587/222 MW. The base cut from
0.21×0.7=0.147 effective to 0.1591×0.7... — precisely: in this arm the
multiplier stays at the CONTROL's 0.7, so the effective statistical WEFOR base
falls 0.147 → 0.1114 before age escalation; ~3.6 pp of class availability
released, and the LP re-prices the margin in ~8–17 % of zone-hours. Not inert.

**Criteria panel** (registration-scored): C1 ST_GAS rows barely move and stay
PASS (2023 −0.77 → −0.77 TWh; 2024 +0.89 → +0.91 TWh) — the class's annual
energy is economics-limited, not availability-limited, so the released
capability expresses on prices rather than volume. The panel's only FAIL rows
are the control's own: C1-2023 CC_REGULAR −4.44 TWh (untouched by this arm —
lane 2's object) and C3a. **No pass→fail flip anywhere** (§5 silent); C3b
0.077/0.154/0.176 all PASS (control 0.077/0.155/0.176). C3a, reported per §0
and never consulted: +4.4/+11.5/+14.5 % vs control +4.4/+11.7/+14.5 %.

## 3. What the acceptance means

The last ERCOT-fitted availability parameter governing a CAISO class is
replaced by a value CAISO's own fleet census produces from a published class
table — rule-14/rule-25 provenance work exactly as chartered. The
identification is per-year-independent (a 5-year published pool + a static
census; no solve-year residual anywhere in the chain), so the LOYO discharge
at any later promotion is by construction. The field enters identified
`measured`; the incumbent 0.21 remains in `constants.THERMAL_AVAILABILITY`
for ERCOT untouched (rule 25).

## 4. Composition posture (Wave 2)

Lane 3's gates PASS ⇒ the arm enters the ladder at its fixed rung (control →
+L2 → +L3). The composed rung solves the lane-2 three-field move AND this
override together; expected composed ledger 10/7 (lane 2's move) + no lane-3
row = **10/7**, verified at composition per protocol §4.

## 5. Artifacts

Registered: `2026-08-16-caiso-197-l3-stgas` (bundle
`results/calibration/caiso197_l3_stgas`: `legitimacy_diagnostics.json`, built
attestation ledger 11/8, `metrics.json`, hourly sidecars per the A/B
precedent). Control shared: `2026-08-16-caiso-197-l2-control`. Records:
`_caiso197_stgas_census.json` (census + derivation + zero-coverage
re-verification), `_caiso197_l3_gates.json` (G-ONEMECH + engagement); probes
`scripts/probes/_caiso197_stgas_census.py`, `_caiso197_ab_gates.py`. Matrix
duty (b): the `wefor_statistical_stack` CAISO cell (the row that registers
`gas_st_wefor_base_override`) gains this acceptance's evidence citation
in-session. Calibration-log entry in `docs/calibration-log/caiso.md`.
