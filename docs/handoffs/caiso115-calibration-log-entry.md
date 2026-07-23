# caiso-115 calibration-log entry (append to docs/calibration-log/caiso.md)

> Delivered as a handoff doc: `docs/calibration-log/caiso.md` is 44 KB and parallel
> CAISO sessions append to it, so a full-file API push would risk clobbering their
> entries (the caiso-114 precedent). This entry IS committed to caiso.md in this
> branch's local history; merge it into caiso.md on integration. On main the log
> runs 111 → 115 (caiso-112/113/114 live on their own branches, not main).

## caiso-115 (2026-07-23) — FRESH-LOOK DIAGNOSIS: C4 is NOT the intractable frontier — decomposed, it is ~75 % sub-ceiling day-to-day scatter (a mild reduced-network limit) + ~25 % fixable diurnal structure that is the SAME belly-import (C5a) + evening-displacement (C3c) defect; the keeper already PASSES C4 in 2/3 years on the clean CEMS basis and its sole fail (2023) is a benchmark-basis artifact; C5a-fix and C3a-guard ARE separable; keeper UNCHANGED

**Measurement-only, NO SOLVE, nothing registered.** Keeper
`2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}). The
caiso-114 handoff's fresh-look charter: answer (A) can C5a-fix + C3a-guard
coexist, and (B) what is C4, with measurement not another tweak. All from
committed artifacts + raw EIA-930 via `scripts/probes/_caiso115_c4_freshlook.py`
(no LP; keeper-proxy `caiso104_m1_B` for the model hourly, reproduces the keeper
C4 gas digit-for-digit). Full record:
`results/calibration/FINDING-caiso115-c4-freshlook-and-separability-2026-07-23.md`.

**Inv 1a — cross-ISO C4 benchmark: the gate is NOT mis-specified, CAISO is a
marginal-NRMSE outlier, not a broken one.** Scoring every ISO keeper's gas
`dispatch_corr` (r≥0.70, NRMSE≤0.30): ERCOT 0.07–0.08, PJM 0.10–0.11,
MISO 0.15–0.20, NEISO 0.12–0.17, NYISO 0.17–0.21 — all PASS comfortably;
**CAISO 0.26–0.33 is the sole outlier**, FAIL 2023 only. But CAISO's gas **r
(0.836–0.908) is in-family** with the import/hydro peers (NYISO 0.804–0.888) —
the *shape* is fine, the *magnitude* is high. The handoff's "maybe the gate is
mis-specified for a reduced-network model" is REFUTED: nobody hovers near the
line, including import-heavy NYISO/NEISO.

**Inv 1b — C4 is TIMING, not volume; ~75 % is irreducible scatter.** Reproducing
the gate's CEMS-basis gas series and decomposing the residual: the flat annual
volume bias (the −8/−7/−5 TWh gas deficit that *is* C5a) is only **13–18 %** of
the C4 SSE — so **fixing C5a barely moves C4** (refutes caiso-108's "C4 moves
once C1/C5a are fixed"; explains the caiso-114 paradox where L1b fixed the volume
yet C4 stayed bad). A *perfect* hour-of-day fix leaves NRMSE 0.221–0.251; a
perfect hod×month fix leaves 0.202–0.225 — **~75 % of C4 is day-to-day scatter**,
the reduced-model floor (invariant to the cogen/fill approximations; sits right
at the peer-worst NYISO 0.207). The removable ~25 % is two real signatures:
**CC_REGULAR under-dispatch belly+overnight** (−1.0 to −1.3 GW belly; imports
substitute = C5a) and **CT_PEAKER evening under-run** (0.2–0.9 vs 1.7–3.3 TWh, a
3.3–6.8× under-run = C3c).

**2023 fail is a BENCHMARK-BASIS artifact (escalation).** CEMS-anchor onset is
2024, so 2023 — the only C4-failing year — is scored on the EIA-930 NG cell
(0.333 FAIL). On the *same CEMS basis as 2024/25* it is **0.271 → PASS**. The two
bases differ ~0.06 NRMSE > the 0.033 fail margin; 2023 was kept on 930 "for
continuity — the two agree there" (bench-basis FINDING 2026-07-12 §5.2), true at
the annual level but NOT at the hourly grain. Moving 2023 to CEMS (scorer-only,
no re-solve) would make the keeper pass C4 all three years.

**Inv 1c + Inv 3 — the evening circle.** The model fills the evening ramp (17–21)
with maxed CC + over-hydro + over-import, capping the CA price at $43–65 (below
the scarcity tail → C3c FAIL) so the CT peaker fleet stays idle despite available
capacity (model annual max 3.4–4.6 GW) — the under-run is ECONOMIC. Against raw
EIA-930: hydro annual matches but the model **over-concentrates it into the
evening (+0.5–0.65 GW)** and under-runs the belly; the **belly over-import
(+1.9–2.5 GW)** is the dominant C5a/C4-belly driver (confirms caiso-109). The
keeper's `hydro_dispatch_envelope` (p95) is **already ON** — it cut the
over-hydro from ~1.5 GW (caiso-72 STEP-0) to ~0.5 GW, but p95 is a loose ceiling
the perfect-foresight LP saturates every evening; `caiso_firm_import_shape`
(caiso-72 #2) is off. Storage is NOT the current driver (keeper runs
`storage_vintage_ramp` + `caiso_storage_shape_anchor`; the caiso-98 flat-8-GW
oversizing is already corrected). Network granularity is not the systematic lever
(caiso-111; dump=0 in every CA zone) — it may underlie the scatter floor but that
part is sub-ceiling and untestable without a nodal build.

**DECISION FRAMING (the handoff's ask).** C5a (belly over-import) = **(i) fixable
mechanism** — belly-scoped import-volume correction, separable from the evening.
C3c + C4-evening-CT = **(i) fixable mechanism, hard multi-lever refinement** —
tighten `hydro_dispatch_envelope` and/or arm `caiso_firm_import_shape`; disclosed
risk = over-tightening over-prices the evening (exactly L1b's C3a break, which
raised the evening with *expensive imports* instead of *domestic peakers*).
C4 bulk (day-to-day scatter) = **(iii) mild representational limitation** (~0.22
floor, sub-ceiling; a belly+evening fix moves C4 ~0.27 → ~0.23, passing).
2023 C4 fail = **(ii) benchmark-basis artifact** — escalate the CEMS-vs-930 2023
basis. **Question A: YES, separable** — belly-volume (hod 10–15) and evening-price
(hod 17–21) are different hours/mechanisms; L1b broke C3a only because the
endogenous West coupled them (fixed belly volume AND re-set the evening price to
the West hub). **Question B: C4 is not the ballgame** — ~75 % a mild reduced-net
limit + ~25 % the same import/evening defect as C5a/C3c; keeper passes 2/3 years
on the clean basis.

**Recommended next single-delta (owner to select; derive-first).** Two separable
forward-stable A/B deltas vs a fresh `caiso102_repro_A`, 3 yr one bundle, LOYO:
(1) **belly** — endogenous West or physical belly-import cap, gated C5a→0 with
**C3a STAYS PASS**; (2) **evening** — tighten the hydro envelope / arm the shaped
firm-import base, gated C3c-tail-up + CT-evening-up with **C3a STAYS PASS** (2023
tail watched, rule 1). DO-NOT-REDO carried: firm-rung reprice (pinned, caiso-109);
belly-depth on CA-price/west-surplus observables (caiso-107/109); fixed-hub West
fallback (caiso-114 KILL); gating the evening on the ±5 $/MWh ladder inside
passing C3a/C3b (caiso-108).

Next number: caiso-116.
