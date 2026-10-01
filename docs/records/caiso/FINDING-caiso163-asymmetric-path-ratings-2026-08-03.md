# FINDING — caiso-163: CAISO asymmetric WECC path ratings

**Session** caiso-163 · **Date** 2026-08-03 · **Branch**
`claude/caiso-asymmetric-path-ratings-3qnzoh` · **Base** `98ad9c1`

**Mechanism** `ScenarioConfig.caiso_asymmetric_path_ratings` · matrix row
`measured_interface_limits` · **Prereg**
`PRECHECK-caiso163-asymmetric-path-ratings-2026-08-03.md`, pushed at `e709857`
**before either arm solved**.

**Outcome: KEPT and PROMOTED.** New CAISO keeper
`2026-08-03-caiso163-asym-path-ratings`; A/B control
`2026-08-03-caiso163-control-asymoff`. Determination **CALIBRATED-WITH-CAVEATS**,
carried over unchanged (2 ledgered, 0 FAILs, protective 0/1).

---

## 0. Headline

The model was moving power across CAISO's internal north–south paths **past
limits WECC does not grant**, in **1,141 path-hours** across 2023–2025. Both
paths shipped a single symmetric TTC that was only **one direction's** rating,
leaving the reverse direction up to **65 % too loose**. Installing the published
directional ratings takes that count to **zero in every hour of every year**,
makes Path 15 bind for the first time, and costs **nothing** on any gate —
all nine criteria are identical to the same-HEAD control.

It also **opens a root-cause issue rather than closing one**, and that is the
session's more useful finding: the published ratings are *not* what was
suppressing CAISO's north–south basis. §5.

---

## 1. What changed

`iso_configs.py:369-378` ships:

```
TransferLink(from_zone="NP15", to_zone="ZP26",      ttc_mw=5400.0)  # Path 15
TransferLink(from_zone="ZP26", to_zone="SP15_rest", ttc_mw=4000.0)  # Path 26
```

The published WECC Path Rating Catalog ratings
(`interchange/caiso.py:1850-1857`, `CAISO_PATH_DIRECTIONAL_RATINGS`):

| path | N→S | S→N | shipped | loose direction |
|---|---:|---:|---:|---|
| Path 15 (Midway–Los Banos) | **3,265** | **5,400** | 5,400 (its S→N rating) | N→S **+65.4 %** too loose |
| Path 26 (Midway–Vincent) | **4,000** | **3,000** | 4,000 (its N→S rating) | S→N **+33.3 %** too loose |

The mechanism appends one directional `InterfaceLimit` per path
(`cap_mw` = N→S, `reverse_cap_mw` = S→N, which overrides `bidirectional` and
bounds the signed group sum in `[-reverse, cap]`). Per-link `ttc_mw` is
untouched — it already equals the looser direction, so the effective bounds
become exactly the published ratings.

**Zero free parameters.** All four numbers were committed in
`CAISO_PATH_DIRECTIONAL_RATINGS` before this session opened. Nothing swept,
blended, interpolated or tuned; no residual consulted. DOF ledger carried
**verbatim** at 11 entries / 9 residual, asserted by
`scripts/gen_caiso163_attestation.py`.

---

## 2. Wiring — checked BEFORE solving, and the answer differed from caiso-162's

caiso-162 lost a solve to a mechanism with **no backcast call site at all**,
which read on prices as a clean INERT verdict and would have written a false
matrix `I` (a DO-NOT-REDO code). That check was run first here, as a no-LP probe
(`scripts/probes/caiso163_wiring_probe.py`).

**The call site exists.** `apply_caiso_asymmetric_path_limits` is invoked from
`interchange/spec.py:1988` inside `apply_interchange_topology`, which
`scripts/run_calibration.py:2037` calls in the `priced_interchange` branch the
CAISO keeper takes (`priced_interchange=true`, `caiso_per_hub_intertie=true`,
`caiso_endogenous_wecc_node=false`). The probe replayed the calibration lane's
exact topology sequence for each solve year and resolved the result through
`build_interface_groups`:

```
2023/2024/2025 OFF: directional limits = 0 | resolved-to-LP-groups = 0
2023/2024/2025 ON : directional limits = 2 | resolved-to-LP-groups = 2
                    CAISO_path_directional_NP15_ZP26       cap=3265.0 rev=5400.0
                    CAISO_path_directional_ZP26_SP15_rest  cap=4000.0 rev=3000.0
```

**What WAS missing was only the CLI/kwarg channel** — the flag could be reached
only through the generic `prb_overrides` dict. Wired across **seven** sites:
`run_calibration_full.py` (`solve_and_persist` signature, `recorded_cfg`
`with_overrides`, the `run_year` call, the `meta` dict, argparse
`--caiso-asymmetric-path-ratings`, `main()`) plus `run_calibration.py`
(`run_year` signature and its `with_overrides` block) — the two
`run_calibration.py` sites being exactly the ones caiso-162 lost a solve to.

**No zero-delta year exists** for this mechanism: the published ratings are
year-invariant, so every solve year is live. The prereg replaced the free
zero-delta control with a **pre-solve structural assertion**, run and passing
before either arm solved:

```
A. flag-off returns SAME OBJECT: True     # identity, not equality
B. flag-on  returns a NEW object: True
```

That is what licenses arm A as a clean control.

---

## 3. Liveness — on FLOWS, never on prices (gates L1/L2/L3)

Both arms solved 2023–2025 in **one invocation and one bundle** each (rule 16),
years sequential (rule 12), in-session (never a CI runner), both at the same
HEAD. Read from each bundle's own `flows.parquet` by
`scripts/probes/caiso163_ab_gates.py`.

| path · year | control max N→S | h over 3,265 | control max S→N | h over cap | arm max N→S | arm max S→N | arm h over ANY cap |
|---|---:|---:|---:|---:|---:|---:|---:|
| Path 15 · 2023 | **4,119.3** | **294** | 5,400.0 | 0 | 3,265.0 | 5,400.0 | **0** |
| Path 15 · 2024 | **4,443.3** | **450** | 5,400.0 | 0 | 3,265.0 | 5,400.0 | **0** |
| Path 15 · 2025 | **4,596.6** | **380** | 5,400.0 | 0 | 3,265.0 | 5,400.0 | **0** |
| Path 26 · 2023 | 4,000.0 | 0 | **3,514.1** | **6** | 4,000.0 | 3,000.0 | **0** |
| Path 26 · 2024 | 4,000.0 | 0 | **4,000.0** | **11** | 4,000.0 | 3,000.0 | **0** |
| Path 26 · 2025 | 4,000.0 | 0 | 2,945.8 | 0 | 4,000.0 | 3,000.0 | **0** |

- **L1 PASS.** The control exceeded a published directional rating in **1,141
  path-hours** (Path 15 N→S 1,124 h; Path 26 S→N 17 h). The symmetric TTCs were
  genuinely binding-and-wrong, not merely slack — so the mechanism is not inert.
- **L2 PASS.** **Zero** treatment-arm hours over any published cap, all paths,
  all years.
- **L3.** The paths now bind as real paths do: Path 15 N→S **307 / 489 / 411 h**,
  Path 26 N→S **1,656 / 1,987 / 2,213 h** (≈ a quarter of all hours — the
  midday solar belly), Path 26 S→N 9 / 9 / 3 h.

---

## 4. Structural gates (S1–S4) and the guards

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **S1** hours NP15 ≠ ZP26, control | 3 (0.034 %) | **0** | 1 (0.011 %) |
| **S1** hours NP15 ≠ ZP26, **arm** | **237 (2.705 %)** | **414 (4.726 %)** | **284 (3.242 %)** |
| S1 — ACTUAL (DAM hub prints) | 99.5 % | 99.9 % | 100.0 % |
| **S2** NP15 ≡ ZP26 byte-identical, control → arm | False → False | **True → False** | False → False |
| **S3** mean NP15 − ZP26, control → arm | +0.000 → **−0.077** | +0.000 → **−0.109** | +0.000 → **−0.084** |
| S3 — ACTUAL | **+5.947** | **+8.576** | **+5.727** |
| **S4** mean NP15 − SP15, control → arm | −1.168 → **−1.226** | −0.913 → **−0.983** | −0.770 → **−0.822** |
| S4 — ACTUAL | **+2.337** | **+7.992** | **+6.009** |
| load-weighted λ, control → arm | 55.9532 → 55.9512 | 37.7665 → 37.7610 | 38.5169 → 38.5209 |
| λ effect | **−0.0036 %** | **−0.0147 %** | **+0.0102 %** |

**Guards — ZERO flips.** All nine criteria identical between control and
treatment: C1 PASS, C2 PASS, C3a-2025 **+12.0 % in both**, C3b PASS, C3c
unchanged, C4 PASS, and protective C6/C7/C8 all PASS. Determination
**CALIBRATED-WITH-CAVEATS**, 2 ledgered / 0 FAILs — identical to the incumbent,
**no new caveat slot spent**.

*(The control arm registers `NOT-YET`. That is the control convention, not a
result: a control carries no `calibration_attestation.json`, so C6 is
UNATTESTED and the two owner-ledgered caveats score as raw FAILs. Same as
`caiso162_control_A`.)*

---

## 5. THE ROOT-CAUSE ISSUE THIS OPENS — the session's real finding

**S3/S4 move marginally the WRONG way, and the published ratings stay in
anyway.** The prereg (§4.4) pre-committed this disposition **before any arm
solved**, precisely so it could not be chosen after seeing the sign.

§3 of the prereg also registered, before solving, that the two legs push the ISO
mean in **opposite** directions and predicted **no** sign:

- tightening **Path 15 N→S** traps cheap northern energy in NP15 → NP15 falls
  relative to ZP26/SP15 (moves NP15 − ZP26 *further negative*);
- tightening **Path 26 S→N** confines the south's midday solar → SP15 falls
  (moves NP15 − SP15 *toward* the measured positive).

The solve resolves the ambiguity: **the Path-15 N→S leg dominates.**

But the magnitudes are what matter. The real Path 15 separates NP15 from ZP26 in
**~100 %** of hours with a mean basis of **+5.95 / +8.58 / +5.73 $/MWh**. This
keeper separates them in **2.7 / 4.7 / 3.2 %** of hours, by **−0.08 to −0.11
$/MWh**. So:

> **The published directional ratings are NOT the binding cause of the model's
> missing north–south basis.** The loose symmetric TTC was a real defect and is
> now fixed, but fixing it recovers ~1 % of the observed basis. Something else
> is suppressing CAISO's N–S price separation.

Per rule 14 `[R-ACCURATE]` and rule 1 `[R-STRUCT]`, a marginally worse residual
under a **published** limit is a **discovered bug**, not a reason to restore the
estimate — the symmetric TTC was silently absorbing a defect that lives
elsewhere. The most plausible location, stated as a hypothesis for a future
session and **not** tested here: the reduced **two-link N–S topology** and
**zonal aggregation** cannot reproduce hourly Path-15 congestion whatever the
ratings are — the real Path 15 congests against a nodal network with intra-zonal
constraints the reduced model collapses away. **No compensating adder, haircut
or offset was added to hide the gap** (rules 1/13), and the gap is **not**
claimed as closed.

**This is not a C3a arm and must not be reported as one.** C3a-2025 is unchanged
at +12.0 % and the level effect is nil.

---

## 6. Governance

- **Config drift is EXACTLY ONE FIELD** against **both** the incumbent
  (`caiso162_peryear_import_caps_v2`) and the same-HEAD control
  (`caiso163_control_A`): `caiso_asymmetric_path_ratings`, with **zero** schema
  drift on either side. Computed with a present/absent-aware diff, not
  `dict.get`.
- **Owner-decision default flips** (`retirement_rule → pipeline`,
  `entry_rate_limits` + `entry_commissioning_lag` armed,
  `net_cone_forward_escalation → reindex_gross`; D-1/D-2/D-3a) were **already
  carried by the incumbent**, so unlike caiso-162 they do not even appear as a
  drift here. Asserted anyway on both grounds: forecast-gated capacity-evolution
  machinery unreachable at `mode="backcast"`, and identical across both arms.
- `gen_caiso163_attestation.py` **FAILS** if: an undeclared config delta appears
  against either comparator; the intended delta is absent; the owner flips differ
  between arms; `mode != "backcast"`; the DOF ledger moves off 11/9; **the
  control never exceeded a published rating** (which would make the mechanism
  INERT and forbid promotion); **any** treatment hour exceeds a published cap; or
  NP15/ZP26 stay byte-identical in 2024 under the treatment.
- **Rule 22.** CAISO holds **no** `complete` marker, so there is no
  `calibration-complete` re-key (D-5(b) is for `complete` ISOs only) and no
  marker was written. The **holdout spend freeze is ACTIVE** and outranks every
  marker: 2023/2024/2025 only, nothing outside it solved, scored or registered.
  LOYO reduces to the no-held-out-degradation check — this session fits nothing
  and moves no free parameter; all three years show the same structural
  improvement and no criterion flips in any year.
- **Rule 16.** All three years in one invocation, one bundle, per arm.
- **Rule 15.** Both arms registered.

---

## 7. Correction to the handoff's framing, recorded not buried

The handoff stated NP15 ≡ ZP26 was "byte-identical in all years". Measured on
the incumbent's own committed sidecars, that is true only in **2024**; 2023 and
2025 differ in 3 and 1 hours (max |Δ| 1.14 and 4.29 $/MWh). The defect and the
direction of the claim are unchanged — Path 15 essentially never binds — but the
gates in the prereg were written against the measured 0.034 % / 0 % / 0.011 %
rather than against zero.

---

## 8. Artifacts

| | |
|---|---|
| keeper bundle | `results/calibration/caiso163_asym_path_ratings` |
| control bundle | `results/calibration/caiso163_control_A` |
| keeper run id | `2026-08-03-caiso163-asym-path-ratings` |
| control run id | `2026-08-03-caiso163-control-asymoff` |
| prereg | `results/calibration/PRECHECK-caiso163-asymmetric-path-ratings-2026-08-03.md` |
| wiring probe | `scripts/probes/caiso163_wiring_probe.py` |
| gate reader | `scripts/probes/caiso163_ab_gates.py` |
| attestation generator | `scripts/gen_caiso163_attestation.py` |

---

## 9. Standing lessons

1. **Check the call site on the lane you are solving, before you solve** —
   caiso-162's lesson, applied ex ante here. It cost one no-LP probe and would
   have cost a wasted solve pair.
2. **Verify liveness on a flow or other physical observable, never on price.**
   Here it was also what made the *positive* case: 1,141 hours of
   rating violations is a structural argument no price delta could have made
   (the price delta is −0.01 %).
3. **A structurally-correct mechanism whose residual moves the wrong way is a
   lead, not a failure.** The pre-committed rule-14 disposition turned what would
   otherwise have been a revert-or-rationalise decision into a bounded,
   quantified root-cause question.
