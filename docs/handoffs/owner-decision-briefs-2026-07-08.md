# Owner decision briefs — 2026-07-08

Two build-exhausted owner decisions gating the in-flight CAISO and PJM work. Each is
a call the code can't make for you: the mechanism is built and probed, the metrics
are known, and the choice is a judgment about rule 1 (structure) vs a moved metric.

---

## Decision 1 — G-61(b): adopt the CAISO startup-aware RA bridge (`caiso-66`)?

> **RESOLVED — ADOPTED (owner decision, 2026-07-11).** Ship on the current keeper config
> (`2026-07-11-caiso-76-hydro-budget`), not the caiso-65 base. Executed by verification:
> the caiso-76 keeper already carries `caiso_ra_bridge_startup_aware=True` — it entered
> the line as caiso-70's pre-registered single delta (2026-07-10) and was carried through
> caiso-72 → 73 → 75 → 76, promoted to keeper 2026-07-11 (commit 295510c) with all three
> years and the zero-forcing ablation twin. The decision's requested replay is therefore
> config-identical to the keeper itself; no duplicate bundle was solved or registered.
> Mechanism engaged in the keeper (D-2 `ra_mustoffer_bridge` CC_REGULAR 2.38/2.26/1.73 TWh,
> C8 PASS). The predicted λ regression did not materialize on the shipped base (caiso-70 vs
> caiso-69 A/B: hub means ~unchanged, 2023 tail 530→540 h); the residual C3a body miss is
> attributed to the belly under-commitment gap (tz-correction FINDING §4.3 / G-15 lane) —
> the unconditional floor is not a fallback. Closure record: calibration-log 2026-07-11
> G-61(b) entry; gap-register G-61 row updated.

**The mechanism.** `caiso_ra_bridge_startup_aware` replaces the RA must-offer bridge's
unconditional floor. Today the bridge floors *every* eligible merchant CC across any gap
shorter than its min-down (6–8 h > the midday solar belly), so essentially the whole
merchant CC fleet rides the belly at 0.26×pmax — pre-positioned, non-physical. The new
branch anchors a unit only when the commitment is *real* (run margin ≥ published startup
cost).

**What it does (probe `2026-07-07-caiso-66-g61b-startup`, transplanted onto the caiso-65
seam-clock keeper base; held back from promotion):**
- RA phantom-anchored belly energy **−~40%**: CC_REGULAR 4.04/4.01/3.48 → 2.56/2.33/2.38 TWh.
  ~1.5–1.7 TWh/yr of belly min-load was phantom-anchored. CC returns mostly on merit.
- CT evening dispatch **unchanged** (drag-owned).
- λ **+$0.30–0.46**; 2023 tail 502→530 h. The phantom floors were price-suppressing.

**The tension.** More faithful UC physics + a ~40% smaller RA forcing budget — but λ moved
*away* from actual. The tz-correction FINDING §4.3 explains why: measured CAISO runs **3.1–5.2
GW MORE belly gas** than the model (reality *over*-commits the belly relative to the model).
So cutting the model's belly commitment is directionally correct as UC physics but moves the
price further from actual, because the model is *already* under-committing the belly.

**Recommendation: adopt — but bundle it with the G-15 belly-grounding fix, not standalone.**
- Rule 1 + rule 11 say keep the structurally-correct mechanism (phantom anchoring is a real
  defect) and fix the root cause rather than revert. Reverting to the unconditional floor to
  protect λ would be burying the error.
- But promoting `caiso-66` *alone* ships a keeper whose headline price metric regressed, for a
  reason (belly under-commitment) that the **in-flight G-15 belly-grounding work is actively
  fixing**. Sequencing them means the smaller forcing budget lands together with the measured
  belly commitment that justifies the price — the λ regression is absorbed, not shipped.
- **Action:** hold `caiso-66` for adoption in the same keeper swap as the belly-grounding
  outcome; if G-15 stalls, adopt `caiso-66` anyway and attribute the λ miss to the documented
  belly gap (do not revert to phantom anchoring).

---

## Decision 2 — G-20b: promote a PJM per-gen reserve co-opt (`pjm-87` / `pjm-88`), or hold?

> **Note:** you flagged midstream PJM fixes in progress. C3c is only one of PJM's two FAILs
> (the other is C1 fuel-mix). This brief covers the reserve-magnitude (C3c) call only; hold it
> against whatever your midstream fixes do to C1/dispatch before promoting anything.

**The candidates (both default-off probes; keeper stays `pjm-90`):**
- **`pjm-87` (`pjm_reserve_pergen_sync`)** — per-gen ramp limit + online/offline product
  scoping. Reserve dual **fires 133/44/50 h/yr** (2023–25), strictly **sub-$32**, never crosses
  the $300 penalty step → correctly prices the *opportunity-cost* regime, not shortage. But the
  magnitude sits mostly **$0–10**, below the **$75–200** afternoon residual C3c needs. Full
  C1–C8 verdict is **criterion-identical to the flag-off `pjm-86` baseline** — C3c still FAILs.
- **`pjm-88` (`pjm_reserve_pergen_size_split`)** — splits large plants into individual columns
  (91–95 pools vs 39). Fires ~50% more hours (205/54/70) but **does not sharpen magnitude**
  (still ≥90% in $0–10), and introduces a **real 2025 dispatch distortion** (CT_PEAKER −2.53
  TWh vs pjm-87; moves #1484 CT_PEAKER D-2 share 10.54→11.93%, still under the 15% cap).

**The finding.** Both reserve-supply-scoping paths were empirically closed: the *shortage*
requirement prices at **$0 in all 26,280 h** (fast-start ramp10 alone ≫ the ~3.4 GW Primary
requirement), and the opportunity-cost band that does form is real but **too small** to reach
C3c's $75–200. Reserve-supply scoping **cannot** price PJM's residual — it's an LP-tightness
problem (perfect foresight leaves the market not-short), the same class as ERCOT G-22.

**Recommendation: reject `pjm-88`, keep `pjm-87` as the documented default-off structure, do
NOT gate the PJM keeper on either — accept C3c as an open LP-tightness limitation.**
- `pjm-88` buys frequency at a dispatch-distortion cost with no magnitude gain → not a keeper.
- `pjm-87` is the structurally-correct opportunity-cost mechanism; keep it default-off/documented
  (rule 26: don't delete it, it's real), but it does not close C3c so it is not a promotion.
- C3c will not close via reserve supply. The honest next lever is demand-side / commitment
  tightness (the ERCOT-G-22 route), or accepting C3c as a disclosed limitation. Fold this into
  your midstream PJM work rather than spending another reserve probe.

---

*Both decisions are build-exhausted: the mechanisms exist, are probed, and are registered. What
remains is the judgment call above. Recommendations follow rule 1 (keep correct structure) /
rule 11 (fix the root cause, don't bury it) / rule 26 (deprecate by keeping default-off, not by
re-tuning).*
