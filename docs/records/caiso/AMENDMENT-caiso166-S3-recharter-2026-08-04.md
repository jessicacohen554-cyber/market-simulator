# AMENDMENT — caiso-166 gate S3 re-charter (OWNER DECISION)

**Date** 2026-08-04 · **Session** caiso-167 (continuation of caiso-166) ·
**Amends** `results/calibration/PRECHECK-caiso166-measured-loss-zones-2026-08-04.md` §6
· **Decided by** the OWNER, on the standing clause *"if structural integrity
improves but gates regress that may still be a keeper"*, reaffirmed 2026-08-04
after caiso-166 recommended against promotion.

> **This document is pushed BEFORE the attestation generator is re-run.** The
> re-chartered rule is stated here, with its provenance, so it cannot be chosen
> after the number it produces. caiso-166's original S3 result stands on the
> record unaltered in `FINDING-caiso166-measured-loss-zones-2026-08-04.md` §3.

---

## 1. What is being amended, and by whom

caiso-166 pre-registered gate **S3** as: the arm may not move a zonal basis by
more than **1.00 ×** that pair-year's measured `dMCL`. It fired — 2025
`LA_BASIN−SP15_rest` at **105.4 %** — and caiso-166 **declined to promote** and
**refused to re-cut the gate itself**, because re-cutting a gate after seeing
the number it produced is precisely what pre-registration exists to prevent.

That refusal was correct and is not withdrawn. What changes is **who decides**:
the owner, holding the promotion authority, has re-chartered the ceiling. This
amendment records that decision explicitly rather than letting it happen
silently inside a re-run.

## 2. The defect in the original ceiling — measured, not asserted

The `1.00 ×` ceiling is **internally inconsistent with the derive it sits beside**.
The surface the LP consumes is itself only held to the **miso-76 B1 band
`[0.5×, 1.5×]`** against measured `dMCL` (`derive_caiso_loss_surface.py
--acceptance`, 12/12 pair-years in band at 0.94–1.06×). The MCE-weighted
estimator carries a known **positive bias**: on the two re-sourced pockets the
surface implies **1.038–1.042 ×** the measured `dMCL`.

An LP that reproduced its input **perfectly** would therefore land at ~1.04 ×
measured `dMCL` and **fail a 1.00 × ceiling** — the gate was unsatisfiable by a
correct implementation. Measured decomposition:

| year | zone | measured `dMCL` | surface-implied | LP delta | **LP ÷ implied** | LP ÷ measured |
|---|---|---|---|---|---|---|
| 2024 | `LA_BASIN` | +0.9242 | +0.9597 (1.038×) | +0.9213 | **0.960×** | 0.997× |
| 2024 | `SDGE` | +1.2107 | +1.2566 (1.038×) | +1.1483 | **0.914×** | 0.948× |
| 2025 | `LA_BASIN` | +0.9686 | +1.0096 (1.042×) | +1.0205 | **1.011×** | 1.054× |
| 2025 | `SDGE` | +1.3101 | +1.3656 (1.042×) | +1.2523 | **0.917×** | 0.956× |

`105.4 % = 1.042 (estimator) × 1.011 (LP tracking)`. **The LP tracks the surface
it was given to within 1.1 %.** The breach measured the *estimator's* bias, not
the mechanism's behaviour.

## 3. THE RE-CHARTERED RULE — zero new parameters

> **S3′.** Per pair-year, `|Δ mean(basis)| ÷ |measured dMCL|` must lie inside the
> **miso-76 B1 band `[0.5×, 1.5×]`** — the SAME band the derive's own
> `--acceptance` gate applies to the SAME measured quantity.

**Rule 5 `[R-NO-MAGIC]` / rule 23 `[R-FROZEN-DERIVE]`: this introduces no new
number.** `[0.5×, 1.5×]` is the existing frozen band, already in
`derive_caiso_loss_surface.ACCEPT_BAND`; the amendment stops holding the LP to a
*tighter* standard than the surface it consumes. The adversarial character is
**retained** — the arm still FAILS for over-performing, now at 1.5× instead of
1.0×, and the generator still exits non-zero on breach.

`LP ÷ measured` ∈ **[0.948, 1.054]** ⊂ `[0.5, 1.5]` → S3′ PASSES on all four
pocket pair-years. The finer `LP ÷ implied` ratio is additionally reported as a
diagnostic, but is **not** the gate.

## 4. The 2024 `price_mean` ledger entry

caiso-166's second promotion blocker was C3a `price_mean` regressing 2024
**PASS → FAIL** (+9.5 % → +11.5 %, ±10 % band), *undocumented* because the
incumbent's ledgered exception covers **2025 only**. The owner ledgers 2024
alongside it. Grounds, all measured and none of them this mechanism's doing:

* losses **consume MWh**, so representing them **must** raise the delivered
  price level — λ +1.82 % (2024) / +2.06 % (2025) is the physically obligatory
  direction, not a tuning artifact;
* CAISO's mean LMP was **already** +9.5 % / +12.1 % hot against RT with the
  control sitting only 0.5 pp inside the band — the arm pushed a **pre-existing**
  bias across a line it was already touching;
* against CAISO's own **day-ahead** basis — the basis the surface is *derived
  on* — the arm sits **+1.8 %** (2024) and +11.3 % (2025), i.e. the 2024 arm is
  closer to DA than the control is to RT. DA−RT premium +$3.30 / +$0.98.

Root cause is the standing owner caveat on the **caiso-141 A2 non-public hourly
pumped-storage** data wall. Ledger budget: `ledgered_max` 3; this takes the
count to 2. **No compensating adder, haircut or offset is added anywhere.**

## 5. What is NOT amended

* **Rule 14 `[R-ACCURATE]` is untouched** — the measured surface was kept
  regardless of the backcast, and that disposition was pre-committed before any
  number was seen. This amendment changes only the *promotion* decision.
* **S1, S2, S4 stand exactly as pre-registered** and all PASSED on their
  original terms: the 2023 placebo reproduces to **exactly 0.0** on price, class
  dispatch and flows; the control carries 48.2–59.4 TWh on the newly-lossy
  corridors with **zero** hours over any published cap and identical link counts;
  zero `ScenarioConfig` drift of any kind against the same-HEAD control.
* **No re-solve.** Both bundles are committed and unchanged; only the gate's
  threshold and the exception ledger move. The dispatch being promoted is
  byte-identical to the dispatch caiso-166 measured.
* **Arm B stays BLOCKED** and the intra-SP15 prohibition is unchanged (rule 13
  `[R-MEASURED]` — no published limit in `data/raw`, and knowing the target
  numbers precisely makes a fitted limit *more* forbidden, not less).
