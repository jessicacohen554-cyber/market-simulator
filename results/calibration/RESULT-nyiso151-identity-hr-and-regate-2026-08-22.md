# RESULT nyiso-151 — the identity heat-rate repair is PROVEN INERT (bit-identical), the re-gate fails on Allegany at the SAME energy to the decimal, and the residual is re-typed: RESERVE-PROVISION dispatch, not energy merit

Session nyiso-151, 2026-08-22. Prereg
`PREREG-nyiso151-egrid-identity-hr-and-regate-2026-08-22.md` (+ Amendment 1)
committed and pushed before any arm solved. Control `nyiso151_control` = the
keeper recipe at the post-merge HEAD; **IDENT PASS — max |Δprice| = 0.0** over
every zone-hour of all three years (the mid-session merge of PRs
#4190/#4193/#4194 is thereby PROVEN NYISO-inert, discharging Amendment 1).
Gates record `_nyiso151_ab_gates.json`. Holdout freeze ACTIVE; every year
solved, scored or read is 2023–2025.

## 1. ARM H (`egrid_identity_heat_rates`) — MEASURED INERT BY LP GEOMETRY; the rule-14 case is intact and free

* H-K1 PASS (exact single delta); H-K2 PASS (the apply line fires every
  year: "applied to 2 generator(s) across 1 plant(s)"); the bins frame
  provably carries the repair (hr_weighted 7.5 → **8.4209**, hr_peak
  11.625 → 13.052 — verified in-process at HEAD).
* **The solve is BIT-IDENTICAL to the control** — total plant-level dispatch
  delta 0.0 MWh; max |Δprice| = 0.0 in all three years. **H-K3/H-K6 FAIL on
  the direction leg** (Allegany's energy does not fall — it does not move at
  all), and that inertness is the finding: Allegany runs ~96 % CF at the
  base offer, so a +0.92 MMBtu/MWh (≈ +$2.3/MWh) cost move leaves it deeply
  inframarginal in every hour — no LP vertex crosses, so dispatch AND prices
  are unchanged exactly (the ercot-202 class, in its purest form).
* H-K4 PASS trivially (bit-identity ⇒ zero new D-rows); every criterion is
  unmoved BY IDENTITY. The accurate input therefore costs nothing anywhere:
  arming it is a pure fleet-truthfulness gain with provably zero fit
  consequence at the current recipe.

## 2. ARM HC (repair + `cc_reserve_duty_split`) — REJECTED on HC-K2/HC-K6, and the rejection is a bit-identity

* HC-K1 PASS both ways (two fields vs control; one vs ARM H); HC-K3 PASS;
  HC-K4 PASS; Sterling / Massena / Batavia reproduce their collapses
  (−93/−94/−96 % and −93/−95/−98 % in the gated years).
* **Allegany lands at 148.2 / 203.2 GWh (70 % / 60 % falls vs the ≥80 %
  bar) — the EXACT nyiso-150 armC values to the decimal — and the whole run
  is BIT-IDENTICAL to `2026-08-22-nyiso-150-reserve-rearm` in every
  zone-hour of all three years**, across a hr_peak 11.625 → 13.052 armed
  offer shift. Two independent offer levels, one armed outcome, proven at
  machine precision: the residual is OFFER-INSENSITIVE.
* HC-K5 by identity: criteria equal the registered nyiso-150 run's
  (C1/C2/C3a/C3b/C4/C8 PASS; C6 unattested-probe; C3c reported).

## 2b′. AMENDED BY OWNER RULING (same day): ARM H REGISTERED AND PROMOTED

The owner, answering the disposition question in-session, chose **promote**
(the arm-on-legitimacy standard, the ercot-202 class). ARM H is therefore
registered after all — `2026-08-22-nyiso-151-identity-hr`, DETERMINATION
CALIBRATED on its own registration verdict (bit-identical artifacts + a
fresh attestation carrying the identity artifact as DOF entry 9, n_scalars
0) — and PROMOTED TO KEEPER with the full workflow (shard swap, D-5(b)
re-key with the identity making a worse determination impossible by
construction, status rebuild, audit 0/0, matrix cell I → K with the I
record preserved, §5.5 header re-stamp). The mechanical
REJECTED-AS-ARMED on the H-K3 direction leg stands unrewritten in
`_nyiso151_ab_gates.json` — both records stand. ARM HC's non-registration
stands as below (bit-identical to `2026-08-22-nyiso-150-reserve-rearm`).
The same sitting also ruled the RHO_CLIP card (option A — floor deleted)
and chartered the RAMP10 seams session.

## 2b. REGISTRATION DISPOSITION (rule 15, the nyiso-149 convention)

Neither arm is separately registered, because each reproduces an
already-registered run bit-exactly: **ARM H ≡ the designated keeper**
(`2026-08-22-nyiso-149-duty-curve`, via IDENT + the H bit-identity) and
**ARM HC ≡ `2026-08-22-nyiso-150-reserve-rearm`**. A second registration of
identical bytes would be a double entry; the identity proofs + this gates
record ARE the dashboard-visible record (both cited runs are live on the Run
Explorer). The bundles are committed for the replication record.

## 3. THE RE-TYPE — the residual is reserve-provision dispatch

The offer-insensitivity has a mechanism, measured on the armHC hourlies:
under the split Allegany runs **3,524 h (40 %) with HALF of its on-hours at
27–34 MW** — mid-load on a 64.7 MW plant, carrying ~30+ MW of 10-minute
headroom — against a control posture of ~8,733 h at 57.6 MW. A plant held at
mid-load half the time it is on is in **reserve posture**: the co-opt values
its quick-start headroom, and its energy is a by-product the energy offer
cannot price away (bit-equal across two offer levels is exactly what
reserve-coupled dispatch looks like; an energy-merit dispatch at full load
would shed the hours between the two offers).

**Why this closes the loop with the standing queue:** the model's 10-minute
reserve supply is missing its real cheapest provider — **NY hydro, ~5.69 GW
(96.1 % of nameplate) flagged 10-minute-capable in EIA-860 Sch. 3.1** —
because `withholding.py::_ramp10_capability` reconciles measured caps only
`if frac > 0.0` and hydro's class frac is 0.0, and
`scripts/lib/ramp_capability/` has no NYISO module (both re-verified at HEAD,
nyiso-150 assessment §4 item 5). With hydro's capability zeroed, the co-opt
leans on small gas CCs to hold headroom online. The last leg of the
merit-order-inversion object and the hydro RAMP10 seams are therefore **ONE
chain, in that order**: land the RAMP10 seams (with the AS-certification
admissibility question that item carries), and re-measure Allegany's reserve
posture on the corrected supply mix — never another offer-side lever (two are
now proven insensitive; a third would be tuning against a mechanism that
is not the binding one, rule 1 `[R-STRUCT]`).

## 4. DISPOSITIONS

* Per the prereg's mechanical rule, ARM H's H-K3/H-K6 failure registers it
  REJECTED-AS-ARMED-ON-ITS-OWN-GATES; the prereg's promote enumeration did
  not anticipate the (H inert, HC self-contained) case, so any promotion is
  an OWNER decision, put to the owner with this record — options: (i) arm
  the inert accurate input (zero measured cost, fleet more truthful), (ii)
  leave it default-off as a registered, proven-inert measured input.
* ARM HC registers per its own gates ([FINAL]); its HC-K2 failure is
  expected to stand on Allegany's reserve-typed residual, which no
  offer-side bar can reach.
* Matrix: `egrid_identity_heat_rates` NYISO cell stamped from this record;
  the `offer_curve_by_group` NYISO record gains the re-type (the reserve
  chain), closing the offer-side lane for this object.

## 5. REPRODUCTION

```
python3 scripts/data/derive_egrid_identity_heat_rates.py --iso NYISO --check
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso151_armH_recipe  --out-dir results/calibration/nyiso151_armH
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso151_armHC_recipe --out-dir results/calibration/nyiso151_armHC
python3 scripts/probes/_nyiso151_ab_gates.py --arm-h-log <log> --arm-hc-log <log>
```
