# FINDING — miso-119/120: `gas_offer_margin_zonal_anchor` at MISO is **DISPATCH-LIVE, PRICE-INERT** → cell `U` → **`I`**

**Session:** miso-120 (completing the Phase-1 A/B that miso-119 pre-registered
and left unrun), branch `claude/miso-120-backcast-calibration-jbnzh2`, off
`origin/main` at `01b6a6a`. **Keeper under test and UNCHANGED:**
`2026-08-03-miso-117b-ct-heat` (`results/calibration/miso117_ctheatrate_B`,
determination NOT-YET, sole FAIL C7 `COAL_PRB` ×3y, ledgered caveats 2/3
`{C3a, C3c}`).

**Pre-registration:** `PREREG-miso119-zonal-anchor-screen-2026-08-03.md`,
written, committed and pushed *before* the Phase-0 screen and *before* either
arm solved. Its §5 fixed every construction gate, every kill, and the
disposition rule in advance. **Nothing in §5 was re-designed here.**

**Registered runs (rule 15):**

| arm | run id | bundle |
|---|---|---|
| A (control) | `2026-08-03-miso-119a-control` | `results/calibration/miso119_control_A` |
| B (treatment) | `2026-08-03-miso-119b-zonal-anchor` | `results/calibration/miso119_zonalanchor_B` |

---

## 1 — The verdict, and the rule that produced it

| gate | result |
|---|---|
| **K1** flag fidelity | **PASS** — arm B records `gas_offer_margin_zonal_anchor=True` and the full six-zone map equal to `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["MISO"]`; control records `False`/`None`; both record `gas_offer_net_revenue_margin=True` at anchor 3.0492 |
| **K2** control integrity | **PASS** — on the scorecard basis (same determination, all nine criterion statuses) **and** on the reported strict-byte basis: **max \|Δ MW\| = 0.000000 on every class-hour, all three years**, against the committed miso-117b sidecars |
| **K3** liveness | **FAIL** — dispatch leg passes (912.5 / 912.5 / 912.5 MW vs the 50 MW bar); **zonal price leg fails in every year: max zonal \|Δλ\| 0.027 / 0.030 / 0.050 $/MWh vs the 0.10 bar** |
| **K4** single delta | **PASS** — the two scenario blocks differ in exactly the two zonal-anchor keys |
| **K5** year span | **PASS** — both bundles `[2023, 2024, 2025]` (rules 16 / 22) |
| **P1–P5** kills | **ALL PASS** — no kill fires |

**Disposition, by §5's pre-committed rule verbatim — *"K3 fails → `I`,
registered, keeper unchanged"*:** the MISO
`gas_offer_margin_zonal_anchor` cell moves **`U` → `I`**. Arm B is **not
promoted**. The owner's standing "structural integrity improves but gates
regress" instruction is **not** invoked and does not apply: no gate regressed
and nothing was measurably corrected at the grain the rubric scores.

Every criterion is identical across keeper, control and arm:
`fuelmix PASS · sysvol PASS · price_mean CAVEAT · price_shape PASS ·
price_tail CAVEAT · dispatch_corr PASS · governance PASS · shape FAIL ·
forced_share PASS`; determination NOT-YET in all three; C1 all 16/16, free
12/12 in all three.

---

## 2 — What the Phase-0 screen got right, and the one thing it got wrong

Phase 0 (miso-119, no LP) returned **LIVE** because neither pre-declared
inertness route fired:

* **Route A** (anchor grain): `max_z |anchor_z − 3.0492| = 0.1799 $/MMBtu`
  against a 0.10 bar — did not fire, correctly.
* **Route B** (price-side unreachability): `max_g |Δoffer_g| = 11.54 $/MWh`
  against a 0.10 bar — did not fire.

**Route B's bound was valid and useless, and that is the transferable lesson.**
Its argument was that a zonal dual is set within the span of the perturbed
offers, so a perturbation bounded by δ cannot move a zonal annual mean by more
than δ. That is true. But δ = 11.54 $/MWh over-bounds the realized effect by
**two orders of magnitude** (0.027–0.050 $/MWh), because the tranches carrying
the large per-tranche deltas are peaking tranches (`markup_hr` up to 75.8 —
St Clair peak, Northeast (MI) peak, New Orleans Power peak) that are marginal
in very few hours. The capacity-weighted p50 |Δoffer| was 0.384 $/MWh and the
p95 was 0.977; those, not the max, are the statistics that predicted the
outcome.

**Recorded as a DO-NOT-REDO for this row:** no future ex-ante screen may treat
`max |Δoffer|` as a *lower* bound on the price-side effect. It is only an
upper bound, and at these markup distributions it is a very loose one. A
sharper future screen would price the perturbation on the *marginal* tranches
— the ones the P0 run actually sets price with — not on the capacity census.

---

## 3 — MISO is inert for a **different reason than PJM**, and the two must not be conflated

PJM (pjm-144) reached `I` on the stated mechanism that its **price-coupled
zones absorb the mean-zero redistribution**. That mechanism is **not** MISO's,
and the prereg already knew it: the "coupled topology" prior carried into this
row from pjm-144 §7 was **falsified at Phase 0** on the keeper's own committed
sidecars — MISO's zones decouple by more than $1/MWh in **21.3 / 24.4 / 50.1 %**
of hours in 2023 / 2024 / 2025 (and by more than $5/MWh in 6.7 / 9.0 / 31.8 %).
MISO is a genuinely decoupled topology and it is *still* inert.

The measured reason is different and is threefold:

1. **The applier convention removes the level.** `apply_miso_zonal_gas_basis`
   delegates to the capacity-weighted **mean-zero** core
   (`data/fuel/basis/meanzero.py`) — like PJM, unlike ERCOT, which carries a
   flat measured EP **level** term and is precisely why ERCOT's cell is `K`.
   Verified at Phase 0 to 4.4×10⁻¹⁶ $/MMBtu: the fleet-aggregate offer level
   cannot move by construction.
2. **The surviving spread is small.** Max |zone anchor − ISO anchor| is
   0.1799 $/MMBtu, against PJM's 1.483 raw window spread — MISO's zone anchors
   are South 3.2291 / West+Plains 2.9641 / Illinois+Indiana+East 2.8971 around
   the unchanged ISO anchor 3.0492.
3. **The repositioned tranches are not the price-setting ones** (§2).

**Rule 25 `[R-ISO-SCOPE]` in both directions:** PJM's `I` did not predict
MISO's `I` — its stated mechanism is absent here — and MISO's `I` does not
strengthen PJM's. Two ISOs, the same applier convention, two *different*
routes to the same verdict. Neither is evidence for the other.

---

## 4 — What moved (REPORTED; none of it is banked)

**The direction is exactly as pre-registered** (§6's two-sided geometry:
premium-basis zones under-marked today rise, discount zones fall) — **sign
agreement 6/6 in all three years**:

| year | premium-zone mean Δλ | discount-zone mean Δλ | system load-wtd Δλ |
|---|---|---|---|
| 2023 | +0.0137 | −0.0275 | −0.0163 $/MWh |
| 2024 | +0.0051 | −0.0302 | −0.0205 $/MWh |
| 2025 | +0.0117 | −0.0504 | −0.0347 $/MWh |

A correct sign at an inert magnitude is a correct sign at an inert magnitude.
The system move is about −0.06 %; it is **not** a C3a result and is not quoted
as one.

Dispatch moves coherently and trivially in energy terms — `CT_PEAKER`
+0.277 / +0.293 / +0.243 TWh against small offsetting reductions in `ST_GAS`,
`COAL_PRB`, `import`, `CC_REGULAR` and `CC_CHP`. No class-accuracy row changes
verdict.

**C7 `COAL_PRB` is untouched, exactly as pre-declared** (§6 explicitly
disclaimed any C7 claim in either direction). Off-peak cv_ratio moves
0.462 → 0.462, 0.474 → 0.474, 0.309 → 0.310 against the 0.50 bound; `profile_r`
0.988 / 0.979 / 0.971 unchanged. It FAILs in both arms in every year. **This
lever was never a C7 instrument and did not become one.** The C7 residual
stays where miso-113 routed it: the overnight dispatch *distribution* needs
widening, via the data-blocked miso-78/79 congestion + sub-hourly-RT lane.

**P4 on the delta:** slack+dump identical between arms — 0.0 / 19,059.283 / 0.0
MWh in both — so the arm costs nothing at the scarcity edge.

---

## 5 — Governance

* **Rule 15** — both arms registered on the dashboard in this session,
  top-15 MISO retention honoured (pruned `2026-07-28-miso-102a-control` and
  `2026-07-28-miso-99a-chp-hr`).
* **Rule 16** — one bundle each, `[2023, 2024, 2025]`, one invocation, years
  sequential inside it.
* **Rule 19 `[R-ONE-MECH]`** — nothing stacked: the zonal anchor *resolves*
  `gas_offer_net_revenue_margin`'s identification point; that mechanism is
  armed and unchanged in both arms. The band-scoped `offer_margin_anchor`
  channel keeps precedence and the MISO census finds **0** band-scoped
  tranches, so the two channels never met.
* **Rule 21 `[R-DOF]`** — both arms carry a DOF ledger; arm B's one new entry
  (`gas_offer_margin_anchor_by_zone (MISO)`) is `measured/published` with
  `free_parameters_added: 0`. `n_residual` unchanged.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the zone anchor table is the derive
  script's own output, was never swept, and is **expressly not re-derived
  against this arm's inert outcome** (P5 holds).
* **Rule 25 `[R-ISO-SCOPE]`** — MISO's anchors from MISO's own basis data and
  MISO's own keeper fleet weights. Nothing imported from NYISO/PJM/ERCOT.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only, in every phase. MISO holds no
  `calibration-complete` marker; no out-of-training year was solved, scored or
  read.
* **Rule 28 duty (b)** — the matrix cell is stamped in this session.
* **Contamination declared** — this session is not blind: it read the miso-119
  prereg and probe transcript, the MISO log, and the matrix row before acting.
  What protects the result is that the *decision rule* was fixed by a
  pre-registration written before any of the measured quantities existed, and
  it was applied verbatim.

---

## 6 — Disposition and DO-NOT-REDO

**Cell:** `gas_offer_margin_zonal_anchor` × MISO: **`U` → `I`**.
**Keeper:** unchanged (`2026-08-03-miso-117b-ct-heat`).
**Table:** stays registered in `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE`;
the flag stays default-off, one CLI switch away.

**Do not re-test this cell without NEW evidence.** Admissible new evidence is
narrow and named: a zone-grain *scored* criterion (the rubric has none today —
C3a/C3b/C3c are all ISO-level); a zone-decoupling mechanism arriving under its
own charter that changes which tranches set zonal price; or an owner override
of the prereg's K3 rule. **Not** admissible: re-running the same arm, sweeping
the anchor table, or arguing from the 6/6 sign agreement — the direction was
already correct and it did not make the mechanism live.

**Every standing MISO bar carries forward unchanged:** the h14-21 `CT_PEAKER`
floor limb is not relaxed and `min_stable_pct` is not re-derived
(rules 1/14/23/25); `CC_CHP` volume and heat-rate questions stay closed
(miso-116/118); the trough-quantity question stays closed (miso-115/116);
`CT_CHP`/`ST_CHP` ratios stay VOID; `miso_cc_coal_rebalance`,
`miso_firm_import_floor` and `miso_pjm_lmp_import_pricing` stay refused; the
seam hod mis-shape stays unchartered; miso-89 stays ledgered; the regulated-PRB
family stays SPENT.

**Live queue head after this:** item 5 `dual_fuel_switching` (cell `U`) — whose
Phase 0 is the measured *identification* (does MISO's own data identify
dual-fuel capability, switch price and event windows?), not a solve, and needs
its own pre-registration before any arm — then the 55088 Dearborn hybrid-cogen
scope gate (miso-118 §5, named not chartered).

**Artifacts:** `_miso119_zonal_anchor_ab.json` (the scored gates),
`PROBE-miso119-zonal-anchor-screen-2026-08-03.txt` (Phase 0),
`PREREG-miso119-zonal-anchor-screen-2026-08-03.md`,
`scripts/probes/_miso119_zonal_anchor_ab.py`,
`scripts/gen_miso119_attestation.py`.
