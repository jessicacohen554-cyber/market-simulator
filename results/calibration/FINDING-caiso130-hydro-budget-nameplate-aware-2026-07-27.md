# FINDING — caiso-130: `hydro_budget_nameplate_aware` delivers exactly the energy it promises (P2 PASS, 93–98 % of it, all three years) and is **KILLED as armed** by K2-2024 — because the LP spreads the freed water almost FLAT and puts 26–47 % of it in the overnight against 11–32 % in the evening. This is a rule-14 result, not a rule-1 one: the accurate input made the fit worse, which localizes the real defect rather than condemning the input.

> **PROMOTED 2026-07-27 (owner, in-session).** The owner set the criterion
> explicitly — *"if structural integrity improves but gates regress that may
> still be a keeper"* — and arm B meets it: the **rubric is identical to the
> same-HEAD control** (C1/C2/C3b/C4/C7/C8 PASS, C3a/C3c/C5a FAIL, NOT-YET in
> both), so no scored criterion regresses, while the delta closes a real
> physical defect with zero DOF. **CAISO keeper is now
> `2026-07-27-caiso-130-nameplate-aware`.** The as-armed REJECTED verdict below
> stands as recorded — it is not erased by the promotion, and §5's rule-14
> reading is the promotion's basis: the exposed overnight regression is an OPEN
> ROOT-CAUSE ITEM (the caiso-127 evening λ pin), never a ledgered exception and
> never bought by a tuned value. Precedent is exact — the superseded keeper
> `caiso-126-ror-split` was itself promoted from a REJECTED probe on the same
> rule 1/14 grounds. DOF ledger (11 entries) + governance attestation carried
> forward and re-attested; `audit_keepers.py --iso CAISO` PASSES clean.

**Superseded keeper `2026-07-27-caiso-126-ror-split`.** Arm B registered as a
REJECTED probe (`2026-07-27-caiso-130-nameplate-aware`) and arm A as its
control (`2026-07-27-caiso-130-control`), both on the dashboard (rule 15). One
pre-registered kill fired, so the delta is REJECTED **as armed**; promotion was
not pre-granted and came later in-session as a separate owner act on the
structural-integrity criterion (banner above).

Gates: `results/calibration/PREREG-caiso130-hydro-budget-nameplate-aware-2026-07-27.md`,
committed at `26259a2` **before arm B solved** (scorer read-key fix `ab44dcc`,
also pre-solve, changed no threshold). Scorer:
`scripts/probes/_caiso130_nameplate_ab.py`. Derives:
`_caiso130_nameplate_blast_radius.py`, `_caiso130_nameplate_precheck.py` (both
no-LP). Arms: `caiso130_control_A` / `caiso130_nameplate_B`, both 3-year single
invocations at the same HEAD, years sequential (rules 12/16).

**Basis is clean.** Arm A reproduces the committed keeper **digit-for-digit** —
max hourly delta 0.000000 MW on the hydro class AND on all 14 classes, all three
years — so the `2a01de8..HEAD` window is CAISO-inert and this A/B carries no
basis caveat.

---

## §1 — cross-ISO blast radius (the owner grant's own precondition)

Answered BEFORE any solve, by code reading plus a no-LP derive over every ISO
keeper's own hydro settings. **The flag is NOT CAISO-scoped by construction**
— it lives in the shared `data.hydro.load_hydro_budget` level-pinning path,
inside the `if monthly_target_mwh is not None` branch, so its reach is exactly
"the ISOs whose run pins a monthly hydro level".

| ISO (keeper) | pins a level? | 2023 | 2024 | 2025 | forecast 2026 |
|---|---|---|---|---|---|
| **PJM** `pjm121_ccbelt` | yes | **5.51 %** | **3.62 %** | **6.72 %** | 4.13 % |
| **MISO** `miso88_egrid_hr` | yes | 1.30 % | 2.12 % | 0.87 % | 1.10 % |
| **CAISO** `caiso126_rorsplit_B` | yes | 0.53 % | 1.50 % | 0.12 % | 0.79 % |
| **NEISO** `neiso61_netrev_margin` | yes | 0.81 % | 0.91 % | 0.28 % | 0.28 % |
| **ERCOT** `ercot115_coal_floor_only` | **no** | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL |
| **NYISO** `nyiso87_cmeas_minrun` | **no** | IDENTICAL | IDENTICAL | IDENTICAL | 0.01 % |

(% = share of that ISO-year's in-LP conventional-hydro budget that is
undeliverable under the uniform scale. "IDENTICAL" = budget array bit-equal
with the flag off and on, `max |Δ| < 1e-6` MWh — verified, not asserted.)

**Arming it in this A/B still changes no other keeper**: it is a per-run
`ScenarioConfig` field defaulting `False`, read via `getattr` in
`data/fleet/assembly.py:1489`, with no shared derived artifact and no on-disk
regeneration — the flag only changes an in-memory budget array. **Rule 25
`[R-ISO-SCOPE]` is satisfied without scoping work**: the mechanism carries no
ISO-fitted constant at all; its bound is the plant's own EIA-860 nameplate ×
the calendar.

**Reported, NOT acted on** (the session's DO-NOT-REDO forbids bundling): the
defect is an order of magnitude larger on **PJM** (3.6–6.7 %) than on CAISO.
That is a separate per-ISO A/B and a separate owner act. Also recorded: the
forward path pins through the same branch on **every** hydro ISO, so NYISO
changes by 0.01 % on a 2026 forecast where its backcast is a strict no-op.

**Disclosed, not fixed:** NYISO 2023/24 carries 20.0/25.1 GWh above
nameplate-hours over 34 plant-months *in the raw EIA-923 rows themselves*. With
no level pin there is no target to re-allocate against, so this flag cannot
touch it (`moved_mwh = 0`, undeliverable unchanged). Separate defect, separate
lane.

## §2 — the mechanism does exactly what it claims (P2 PASS, all three years)

The flag's own identity check is the one gate it passes cleanly. Solve logs
confirm the re-allocation fired and the month total was met exactly:
**130.2 / 352.7 / 26.3 GWh re-allocated over 70 / 52 / 27 clipped plant-months,
0.0 GWh physically unattainable** in every year. (The log counter accumulates
across water-fill iterations, so it reads slightly above the pre-solve net
|Δ|/2 of 130.2/340.6/26.3 GWh — same operation, different accounting.)

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| annual hydro A → B (MW) | 2 762.9 → **2 777.4** | 2 506.2 → **2 543.6** | 2 412.9 → **2 415.7** |
| rise | **+14.5** | **+37.5** | **+2.8** |
| predicted (full delivery) | +14.8 | +38.9 | +3.0 |
| **delivered share** | **98 %** | **96 %** | **93 %** |
| P2 gate (≥ 60 % of predicted) | PASS | PASS | PASS |

The fleet now delivers its own measured level target. Under the uniform scale it
could not: the budget was being pushed above a physical ceiling and silently
clipped. **That defect is closed** (P4: 0 MWh / 0 plant-months above the bound,
all three years). Zero new free parameters; the bound is nameplate × calendar.

## §3 — why it is KILLED anyway: the freed water goes almost everywhere EXCEPT the evening

The pre-registered kill K2 fired in 2024 — overnight |gap| 92 → 152 MW, a
+60 MW worsening against a +50 MW bound. The attribution shows why, and it is
the load-bearing result of this session.

**Where the re-allocated water actually lands** (B − A hydro, mean MW by window,
share of the annual rise):

| window | 2023 | 2024 | 2025 |
|---|---|---|---|
| **overnight** (h0-6) | +17.6 MW / **35.5 %** | +59.8 MW / **46.5 %** | +2.5 MW / **25.9 %** |
| belly (h9-15) | +12.7 / 25.7 % | +31.2 / 24.3 % | +2.1 / 21.9 % |
| **evening** (h17-21) | +10.9 / **15.7 %** | +20.4 / **11.3 %** | +4.3 / **31.9 %** |
| late (h22-23) | +16.7 / 9.6 % | +29.2 / 6.5 % | +3.2 / 9.5 % |

The 2024 hour-of-day profile is nearly **flat with an overnight tilt** —
+59/+62/+63/+56/+59/+60/+60 across h0-6, falling to +25/+16/+13/+14 across
h18-21. The LP does not concentrate the freed water where the price is highest;
it spreads it and tilts it *away* from the evening.

**Two mechanisms, both structural, both already on record:**

1. **The recipients have headroom in the wrong hours.** By construction the
   water-fill routes the overflow to the plant-months *with nameplate headroom
   left*. Those are precisely the plants the LP was not already running flat
   out in the peak; adding to their budget extends them into progressively
   lower-λ hours, which are the overnight and the belly. The tilt is a property
   of *which plants can physically take the energy*, not of the mechanism's
   intent.
2. **The evening premium is too compressed to attract it.** This is
   FINDING-caiso127 §1's fixed point, now confirmed from a completely
   independent direction: the model's evening−overnight premium is compressed
   ~2× by the storage arbitrage pin, so the LP's own λ surface does not reward
   concentrating water in h17-21. A mechanism that hands the LP free deliverable
   energy with **zero degrees of freedom** still cannot route it to the evening.

**Measured against the pre-solve ceiling:** the evening moved +10.9 / +20.4 /
+4.3 MW against a no-feedback ceiling of +64.8 / +172.5 / +13.2 MW — feedback
ratios of **0.17× / 0.12× / 0.33×**. Contrast caiso-126, where the water-value
feedback *exceeded* the fixed-λ proxy by 1.2–3×. Here the feedback runs the
other way: the LP takes the energy and declines to put it in the window the
energy argument pointed at.

## §4 — the pre-registered scorecard, in full

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| **P1** evening moves toward 0 by ≥ 25 % of ceiling | +10.9 (need +16.2) | +20.4 (need +43.1) | +4.3 (need +3.3) | **FAIL 2023/24**, PASS 2025 |
| **P2** annual hydro rise ≥ 60 % of predicted | +14.5 | +37.5 | +2.8 | **PASS all** |
| **P3** D-2 share move ≤ 2 pp; D-4 off-window = 0 | ✓ | ✓ | ✓ | **PASS all** |
| **P4** undeliverable energy closed | 0 MWh | 0 MWh | 0 MWh | **PASS all** |
| **K1** C3a guard (≤ +0.25 pp worsening) | 3.73 → 3.63 % | 7.70 → 7.56 % | 8.50 → 8.49 % | **ok — improves every year** |
| **K2** overnight ≤ +50 MW worsening | +159.7 → +177.4 | **+91.7 → +151.7** | +211.1 → +213.6 | **KILL 2024** |
| **K3** \|belly\| ≤ 150 MW | −91.8 → −79.0 | −57.8 → −26.5 | −83.3 → −81.1 | **ok — improves every year** |
| **K4** rubric non-regression | identical | identical | identical | **ok** |
| **K5** plant/class set unchanged | ✓ | ✓ | ✓ | **ok** |

D-2 forced shares move ≤ 0.41 pp (`hydro_ror_flat` 0.1198/0.1110/0.0998,
`hydro_min_flow` 0.1617→0.1596 / 0.1659→0.1618 / 0.1446→0.1444); D-4
off-window is `0.0000` for both mechanisms in all three years. Rubric identical
in both arms: C1/C2/C3b/C4/C7/C8 PASS, C3a/C3c/C5a FAIL, C6 UNATTESTED,
determination **NOT-YET** in both.

**Side effects, reported not gated:** belly improves in all three years
(−91.8 → −79.0, −57.8 → −26.5, −83.3 → −81.1) and C3a improves *toward* actual
in all three (−0.10/−0.14/−0.01 pp). Gas falls −0.080/−0.266/−0.022 TWh, which
moves **C5a the wrong way** (CAISO's C5a is a −11 to −13.5 % CO2 *deficit*, so
displacing gas with hydro widens it) — second-order against a 6–8 TWh gap, but
it is a real cost of this delta and is recorded as such.

## §5 — the disposition is a rule-14 call, and it matters which way it is read

Rule 14 `[R-ACCURATE]` is explicit about exactly this situation: *if swapping a
hand estimate for real data makes the backcast worse, that is a signal that
something else in the model is miscalibrated and the estimate was silently
compensating for it.* That is precisely what happened here, and it can be
stated mechanically:

- The uniform scale's silent nameplate clip was **removing 0.13–0.35 TWh/yr of
  hydro energy** the model's own level target said should exist.
- The model has a **known, year-stable overnight hydro excess** (+160/+92/+211
  MW in the keeper). The clip was quietly offsetting part of it.
- Restoring the accurate input restores the energy — and the LP, judging by its
  own compressed λ surface, puts a plurality of it back into the overnight,
  making the excess visible again.

So the K2 kill is a **discovered defect elsewhere**, not evidence against the
nameplate bound. Reverting to the uniform scale to "fix" the overnight would be
burying the error back inside an inaccurate input, which rule 14 forbids in
terms. Accordingly:

1. **Keeper PROMOTED to arm B** (owner, in-session, on the stated
   structural-integrity criterion). The as-armed REJECTED verdict stands as
   recorded. The flag itself stays **default-off in `ScenarioConfig`** — the
   keeper arms it explicitly through its own run config, exactly as
   `hydro_ror_split` and `hydro_min_flow_floor` are armed; nothing about the
   promotion changes another ISO's default (§1).
2. **The flag is NOT refuted as physics.** It is refuted *as armed on this
   keeper, today*, by a kill whose cause is the evening λ-formation defect the
   caiso-126 K1 and caiso-127 diagnoses already identified as the blocker for
   the entire hydro family. It is a one-flag re-test once that lane lands — the
   same standing as the RoR family itself.
3. **Do not re-arm it against this residual.** Any attempt to make it pass by
   scoping *where* the water is re-allocated would be tuning an allocation
   against the overnight residual (rules 13/21) — and the water-fill has no
   free parameter to scope with, which is a feature.
4. **The PJM exposure is now the most valuable open item this session
   produced** (§1): 3.6–6.7 % of PJM's hydro budget is undeliverable, ~10×
   CAISO's, and PJM's keeper carries none of CAISO's evening-λ pin. Filed as an
   ask, not built.

## §6 — rule-22 LOYO record

**Zero fitted parameters** (bound = EIA-860 nameplate × calendar; no threshold,
no percentile, nothing derived from a residual), so LOYO reduces to per-year
gate consistency exactly as in FINDING-caiso126 §5. Nothing was re-tuned
against any year, and there is nothing to re-tune.

- **P2 is same-signed and consistent in all three years** (98/96/93 % delivery).
  The mechanism's own claim holds leave-one-year-out.
- **The evening under-delivery is same-signed in all three years** — the
  movement is positive everywhere but lands at 0.17/0.12/0.33× of its own
  ceiling. P1's 2025 "PASS" is an artifact of that year's ceiling being tiny
  (+13.2 MW): +4.3 MW clears a 25 % bar it would fail at any other year's
  scale. **Scored honestly, P1 fails as a three-year property**, and the 2025
  pass must not be quoted as a partial win.
- **The overnight worsens in all three years** (+17.7 / +60.0 / +2.5 MW). The
  K2 breach is confined to 2024 only because 2024 carries 2.6× the
  re-allocation of 2023 and 13× that of 2025. **The kill is a systematic
  mechanism property scaled by the delta's own size, not a single-year
  artifact** — the same structure as caiso-126's K1.

No promotion is requested and none is granted; promotion remains a separate
owner act (rule 1).

## §7 — DO-NOT-REDO (new, binding)

Re-arming `hydro_budget_nameplate_aware` on the CAISO keeper against this
residual, in any scoped form (per-window, per-class, or per-plant restriction of
where the overflow is re-allocated) — §3 shows the destination is set by which
plant-months have physical headroom, and §5 shows scoping it would be tuning an
allocation against the overnight residual; re-measuring the cross-ISO blast
radius or the per-ISO undeliverable shares (§1 carries them, with the forecast
path); re-measuring the delta's energy budget, its destination split, or the
no-feedback evening ceiling (§2/§3 and the committed precheck carry them);
re-solving the A/B to "confirm" the direction — arm A is byte-identical to the
keeper, so both arms are reproducible from the committed bundles; reverting to
the uniform fleet-wide scale as an improvement (rule 14 — that is the silent
compensation this session identified, not a fix).

Carried forward unchanged: everything in FINDING-caiso129 §6, FINDING-caiso127
§7 and FINDING-caiso128's DO-NOT-REDO. Notably still binding: the CT
offer-heat-rate lane is CLOSED; the allocation-floor family is CLOSED against
the storage pin; S2 (the DA/RT two-settlement separation) must be chartered
separately and was not opened here; pumped storage remains flagged-not-built.

## §8 — status of the caiso-127 grant

**The grant is now fully spent.** Item 1 (S1) was executed and killed at the
derive gates (caiso-129). Item 3 (this session) was executed as its own single
delta with the cross-ISO blast radius checked first, and is killed at the
pre-registered A/B gates. Item 2 (the caiso-114 refinement) remains **unfunded
as a first delta** and is unchanged by this session — it stays gated behind the
storage pin, which is still not fixed. Item 4 (pumped storage: no shape
restraint of any kind, +58/+85/+89 MW of the overnight excess) remains
**flagged, not built** — this session did not open it.

Every hydro-side candidate the lane has tried now converges on the same
blocker: **the evening λ-formation defect (the storage arbitrage pin) is the
prerequisite for the entire hydro family**, and this session adds the sharpest
evidence yet for it — a zero-DOF mechanism that hands the LP free, physically
deliverable evening-capable energy, and the LP puts a plurality of it in the
overnight instead.

Next number: caiso-131.
