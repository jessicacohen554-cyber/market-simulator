# FINDING — pjm-125: constraining commitment halves PJM's reserve supply and still cannot make it bind (2026-07-26)

**Verdict: framing 1 lands PARTIAL — NO SOLVE SPENT.** The second and last
candidate named in `docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md` §7
("whether perfect-foresight all-online commitment should be constrained before
the reserve bound is read") **does** bite, and bites hardest exactly where PJM's
residual lives — and still leaves the reserve balance **5.0–5.6× oversupplied**
in all three keeper years.

This is materially different from pjm-124. Framing 2 was **inert**; framing 1 is
**effective but insufficient**. That distinction is the point: it is the
frontier evidence the charter said a negative result would produce — *the supply
side cannot be closed within the no-MIP mandate*, demonstrated rather than
asserted.

Kill criteria were committed before the probe ran (`4860cf7`,
`scripts/probes/pjm125_commitment_constraint_precheck.py`); per-year JSON in
`results/calibration/pjm125_precheck_{2023,2024,2025}.json`.

---

## 1. Why this is not pjm-124 again

The per-gen co-opt imposes **two** constraint families per pool-hour:

| family | bound | attacked by |
|---|---|---|
| ramp | `R[r] ≤ Σ ramp10 × availability` | **framing 2** (pjm-124, closed) |
| joint capacity | `Σ P + R ≤ Σ cap` — counts every member, committed or not | **framing 1** (this finding) |

`docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.4 states framing 1's
premise: "pjm-81/82 proved the perfect-foresight LP holds ~2.7–3.1× the real
online reserve at near-zero cost". A 2.7–3.1× surplus is a far better prospect
than framing 2's measured ~10×, so the two were measured separately rather than
assumed to share a verdict (rule 19).

## 2. What actually bounds the keeper's reserve today (new measurement)

| GW, annual mean | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured Primary requirement **R** | 3.09 | 3.42 | 3.35 |
| ramp bound | 38.74 | 38.67 | 38.95 |
| joint capacity headroom | 45.91 | 42.53 | 40.18 |
| **effective bound = min(both)** | **37.12** | **35.78** | **34.80** |
| effective ÷ R | **12.0×** | **10.5×** | **10.4×** |
| share of hours where the **ramp** family binds | 81 % | 70 % | **60 %** |

Two things worth recording independently of the verdict:

* The **ramp family binds most hours, but its share is falling** — 81 % → 70 %
  → 60 % across 2023–2025. The joint capacity row is progressively becoming the
  binding family as the fleet tightens. Framing 1 was therefore aimed at a
  genuinely live constraint, not a slack one.
* On the quantity that actually bounds the co-opt, the surplus is **10.4–12.0×
  the requirement** (and 10.5–12.4× the measured SR+REG target) — *larger* than
  the 2.7–3.1× premise figure. These are **not the same quantity**: pjm-82
  measured unloaded headroom on committed units under a posture-constrained arm;
  this is the co-opt's own aggregate supply bound. No claim is made here about
  pjm-82's number. The relevant point is only that on the binding quantity the
  surplus is larger, which makes framing 1's task **harder**, not easier.

## 3. The commitment-invariant floor

Whatever a commitment constraint does — a posture screen, a no-foresight
commitment, a decommitment pass — it **cannot remove offline fast-start
capacity** from a Primary balance: Primary = Synchronized + **Non-Synchronized**,
and Non-Sync reserve *is* offline 10-min-startable iron (Manual 11 §4.2, the
pjm-124 result). Fast-start members therefore supply reserve in either
commitment state, bounded by both families at once:

```
F_ramp(t) = Σ FAST ramp10 × availability(t)                      [ramp family]
F_head(t) = Σ FAST cap × availability(t)  −  D_fast(t)           [joint family]
S_floor(t) = max(0, min(F_ramp, F_head))   ≤  reserve supply, ALWAYS
```

`D_fast` comes from the keeper's own committed P1 class-hourly sidecar and is
deliberately **over**-attributed (a class's whole production charged to its fast
members, capped at their capacity), which biases `S_floor` *down* — in the
mechanism's favour.

| GW, annual mean | 2023 | 2024 | 2025 |
|---|---|---|---|
| F_ramp (fast, ramp family) | 17.54 | 17.57 | 17.57 |
| F_head (fast, joint family) | 22.95 | 22.91 | 22.03 |
| **S_floor** | **17.34** | **17.18** | **16.99** |
| **S_floor ÷ R** | **5.6×** | **5.0×** | **5.1×** |
| reduction vs the keeper's effective bound | **53.3 %** | **52.0 %** | **51.2 %** |
| tight-quartile hours with S_floor ≤ 2×R | 5 / 2,191 | 52 / 2,190 | 69 / 2,190 |

## 4. Verdict against the pre-registered criteria

| criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| **K1 MAGNITUDE** | **PARTIAL** 5.6×R | **PARTIAL** 5.0×R | **PARTIAL** 5.1×R |
| **K2 TIGHT-BIN BITE** (≥ 10 pp) | **PASS** 42.7 pp | **PASS** 40.6 pp | **PASS** 40.0 pp |
| **K3 ADMISSIBILITY** | PASS | PASS | PASS |
| verdict | NO SOLVE | NO SOLVE | NO SOLVE |

**K2 passes decisively, and that is the substantive result.** Framing 1 bites
*hardest in the tightest net-load quartile* — the exact inverse of framing 2:

| bite, slack → tight quartile | bin0 | bin1 | bin2 | bin3 (tight) |
|---|---|---|---|---|
| framing 1 (this finding, 2025) | 32.5 % | 36.3 % | 38.5 % | **40.0 %** |
| framing 2 (pjm-124, 2025) | 18.4 % | 14.6 % | 13.7 % | **8.6 %** |

Framing 1 is a real commitment-state mechanism operating on the right hours.
It halves the reserve supply bound. **It still does not make the balance bind**
— the floor stays at 5×R, and even in the best year only 69 of 2,190 tight hours
reach 2×R (the PASS band needed the *annual mean* at ≤ 3×R).

**K3 passes**: every arm is fleet physics plus the model's own dispatch. The
measured PJM series enters as the requirement only; the SR+REG target is
reported as a diagnostic comparison and is not an input to any arm.

## 5. What this closes, and what it means

**Lane 1 is now complete.** Both framings pjm-120 §7 named are on record:

| framing | mechanism | result |
|---|---|---|
| 2 (pjm-124) | scope `ramp10` to committed-and-online | **inert** — 13.6–15.9 % reduction, *least* bite in tight hours, floor ~10×R |
| 1 (pjm-125) | constrain commitment before the reserve bound | **effective but insufficient** — 51–53 % reduction, *most* bite in tight hours, floor ~5×R |

Together they bound the whole reserve **supply** side, because the floor they
share is not a modelling choice:

1. **Offline fast-start capacity is tariff-protected.** 17.5 GW of it — 45 % of
   the deliverable ramp — is Non-Synchronized Primary reserve by Manual 11 §4.2.
   No commitment mechanism may remove it, and removing it anyway is the closed
   product mismatch (pjm-124 §4).
2. **That floor alone is 5.0–5.6× the requirement.** So even a *maximally*
   aggressive, perfectly-informed commitment constraint leaves the balance five
   times oversupplied, and no ORDC step can fire.

**This sharpens, and partly qualifies, pjm-82's LP-vs-MIP attribution.** pjm-82
placed the residual on the continuous-`U` representation boundary. That reading
is right that commitment is where the surplus comes from — framing 1's 51–53 %
bite confirms it — but **a MIP would still not close this gate**, because the
5×R floor survives any commitment representation whatsoever. The binding
constraint is not LP-vs-MIP. It is that **PJM's reserve requirement (~3.4 GW) is
small relative to the fast-ramping fleet that can serve it (~30.6 GW nameplate,
17.5 GW of 10-minute deliverable ramp)** — a real property of the system, not an
artifact of how the model represents commitment.

Which means the >$200 residual is **not** on the reserve supply side at all.
What PJM printed at h4193 — $1,722, against a model dual of $210.99 and a model
any-zone energy price of $675.3 — is being set by something a Primary-reserve
shortage the model could reproduce by tightening supply does not explain.

**Frontier readiness is flagged, not declared** (frontier is owner-declared).
Every named admissible mechanism in Lane 1 has now been tried on record, with
what remains either inadmissible (the product mismatch, rule 26) or shown
structurally incapable. Lane 2 (the pjm-123 derive-conditioning question,
owner-gated) is independent and remains open.

## 6. Guardrail review, including one disclosure

* **Rule 1** — framing 1 is *not* rejected for failing to move a residual; it is
  recorded as a real mechanism that bites correctly, and declined only because
  its own invariant floor cannot reach the binding regime. Nothing was tuned.
* **Rule 13** — all arms are fleet physics plus own-dispatch; no measured
  outcome is pinned.
* **Rule 16** — all three keeper years measured. No dashboard registration: **no
  solve was run**, so there is no bundle to register (the pjm-123/124 precedent).
* **Rule 19** — framings 1 and 2 were adjudicated in separate probes with
  separate criteria and separate findings, and **neither was ever armed in a
  solve**, so there is zero attribution contamination between them. (This
  session ran both at the owner's explicit direction after 124 closed; the
  charter's separability requirement is about not arming both and reading one
  number, which did not occur.)
* **Rule 22** — 2023–2025 only; PJM has no calibration-complete marker and no
  out-of-training year was touched.
* **Falsifiability, with a disclosure.** The pre-registered PARTIAL and KILL
  bands as worded **overlap**: a floor can both "stay above 3×R" and "fall ≥ 50 %
  below the keeper's effective bound". The first implementation checked only the
  3×R clause and printed **KILL**; the measured reduction is 51–53 %, so the
  pre-registered PARTIAL band applies. **The code was corrected to match the
  pre-registered prose — the prose was not changed to match the code** — with
  PARTIAL taking precedence as the more specific band. The NO-SOLVE decision is
  identical under either label, so the correction changes only how much the
  result reports. pjm-124's classifier carries the same overlap, but its measured
  reduction (13.6–15.9 %) is far below the 50 % PARTIAL threshold, so **its
  reported KILL stands unchanged** and was not revisited.

## 7. Reproduction

Environment as pjm-124 (§8 there); ~4 min per year, no LP:

```
for y in 2023 2024 2025; do
  python scripts/probes/pjm125_commitment_constraint_precheck.py \
    results/calibration/pjm121_ccbelt --year $y \
    --json-out results/calibration/pjm125_precheck_$y.json
done
```

## Pointers

* Charter and ledger: `docs/handoffs/pjm-frontier-path-2026-07.md` §2–§4.
* The framing this closes: `docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md`
  §7, framing 1.
* Its sibling: `docs/FINDING-pjm124-ramp10-scoping-precheck-2026-07.md` (framing 2).
* The attribution this qualifies: pjm-82, and
  `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3–B.4.
