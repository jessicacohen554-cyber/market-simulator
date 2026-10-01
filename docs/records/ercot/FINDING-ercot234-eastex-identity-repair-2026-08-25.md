# FINDING — ercot-234 execution: the card Z-A `NE_LOB`→`EASTEX` identity repair — ALL P-6 GATES PASS, the ercot-231 G-SPUR artifact dissolves (21→11), and the 2023 officials give back the mis-attributed gain exactly as rule 14 predicts

**Date:** 2026-08-25 · **ISO:** ERCOT · **Authorization:** card Z signed
**(Z-A)** with the owner's advance promotion standard
(`docs/DECISION-CARD-ercot234-nelob-identity-repair-2026-08-24.md`
RESOLUTIONS) · **Charter:**
`docs/PRECOMMIT-ercot234-eastex-identity-repair-2026-08-25.md`, pushed +
blob-verified (blob `ddbcde2`) BEFORE any derivation or solve, including its
Amendment 1 (the P-1 firing record) and the phase-0 verdict.
· **Bundle:** `results/calibration/ercot234_eastex_identity` (3-year replay
of the ercot-231 keeper recipe at repaired HEAD; control = the committed
keeper bundle BY IDENTITY per P-5's drift audit — two changed files since
`c9a07b9`, both provably inert at the keeper's flags).
· **Gates artifact:** `results/calibration/ercot234_gates.json` ·
**Official scores:** `results/calibration/ercot234_official_score.json`
(scorer validated against the keeper's registered values exactly:
−38.0 % / 0.696 / 93 · +0.4 / 0.130 / 22 · −7.7 / 0.099 / 1).

**ZERO FITTED SCALARS.** The repair: `EASTEX` (ERCOT's East Texas GTC)
replaces the geographically mis-attributed `NE_LOB` (North Edinburg – Lobo,
Rio Grande Valley) on the `Northeast→North` link in
`constants.ERCOT_GTC_LINK_MAP`; the static export rating re-derives 1,300 →
**2,300 MW** (P-2: NP6-86 mean-limit-at-bind pooled 2023+2024, instrument
validated on WESTEX +0.20 % / PNHNDL +0.05 %); the import side (1,788 MW,
ERCOT-76) is untouched; the measured hourly overlay follows the corrected
map. Identity basis: FINDING-ercot234 (survey half) — ERCOT's own GTC
definitions and market notice #1557 ("around Tyler, Lufkin and
Nacogdoches").

## 1. The mechanical gate table (P-6) — every gate PASSES

| gate | class | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|---|
| G-SHED-NEW | **STOP** | none | none | none | **PASS** (no new shed hour; slack sets identical) |
| G-COAL148-GROSS (>2.0 TWh) | **STOP** | +0.066 | +0.210 | +0.203 | **PASS** — and all three under even the 0.5 TWh report bar: the feared Martin-Lake blowout did not materialize |
| G-SPUR banded (vs keeper 21·11·1) | report | 21→**11** | 11→11 | 1→1 | **IMPROVES** — lidless identical (11·12·1, top 0·1·0) |
| G-SPAN (>2 % named) | report | 0.071 % | 0.047 % | 0.043 % | PASS (max class move, ST_GAS/COAL_PRB) |
| G-DOF | report | — | — | — | PASS (zero parameters added; static is a rule-23 measured constant) |
| G-D2/D-4 | report | — | — | — | PASS (D-4 FAIL rows byte-identical keeper↔arm — inherited, none new) |

**The ercot-231 promotion's named cost dissolves.** The 21 spurious
in-season mid-band hours — the sole basis of ercot-231's pre-registered
REJECTED-AS-ARMED mechanical verdict, promoted over by the owner — drop to
**11** (the ercot-223-era set): the 10 extra hours were the mis-attributed
Valley-series congestion pricing the Northeast apart, exactly as ercot-232
measured ("the six non-Northeast zones price identically while Northeast
prices $24–126").

**The congestion object lands at the real scale.** Northeast|North price
separation collapses **2,155 / 1,128 / 1,354 → 29 / 45 / 45 hours** —
against a real EASTEX binding record of ~69 / ~16 / ~0.3 hour-equivalents,
the right order of magnitude where the keeper was 25–50× over.

## 2. The official side-effects (Q-B / R-A: reported at full magnitude, never the basis)

| year | C3a official | C3b NRMSE | C3c (of 181/53/31) |
|---|---|---|---|
| 2023 | −38.0 % → **−39.7 %** | 0.696 → **0.730** | 93 → **72** |
| 2024 | +0.4 % → **−0.2 %** (PASS) | 0.130 → 0.131 (PASS) | 22 → 22 |
| 2025 | −7.7 % → **−7.9 %** (PASS) | 0.099 → 0.101 (PASS) | 1 → 1 |

The 2023 arm lands almost exactly on the ercot-223-era officials
(−39.7 / 0.729 / 74): the ercot-231 keeper's 2023 gain was substantially the
mis-attributed congestion, and rule 14's instruction is exactly this case —
*keep the accurate input; the exposed residual is the real open object*. The
tie-zone attribution (the ercot-231 arm's other half) stays armed and keeps
its guard years: 2024 and 2025 hold PASS on C3a and C3b. C3c-2023 returns
below its band (72/181 = 0.40×) and re-enters the standing model-class
ledger (the C3c standing rule; ledgered ×3 as in the ercot-215/221/223
lineage). Determination: **NOT-YET on {C3a-2023, C3b-2023}, unchanged in
kind** — the misses report at full magnitude, now un-flattered.

## 3. Promotion

Per the precommit P-7: **no STOP leg fired**, so the arm is promoted on the
owner's in-advance signature (*"If structural integrity improves but gates
regress that may still be a keeper"*) — and in this case the mechanical
verdict itself is KEEPER-CANDIDATE: no gate regressed; only the reported
official 2023 side-effects moved, in the direction honesty demands. What the
keeper now claims is strictly more defensible: a measured series applied at
the boundary where ERCOT measures it, a sourced static, 10 fewer spurious
hours, and a congestion object at the real scale. Run id
**`2026-08-25-ercot234-eastex-identity`**; the superseded
`2026-08-24-231-tie-zone-measured` remains registered as the immediate-prior
comparison.

**Replay rule (updates the ercot-231 note):** this keeper's replays require
the gtc-limits clean partition AND the repaired crosswalk
(`EASTEX → Northeast→North`); ercot-231 replays additionally require the
pre-repair map (`NE_LOB → Northeast→North`) — replay from each bundle's own
HEAD.

## 4. Hygiene

Years ⊂ {2023, 2024, 2025} (rule 22); ERCOT-only (rule 25); years solved
sequentially in one invocation (rule 12); 3-year bundle (rule 16); no CI
job; Q-B/R-A honoured (this charter's basis is identity, never the
residual); the ercot-233 zonal-grain closure, `internal_congestion_split`
`G`, and the tie placement untouched; the ercot-225 gate card remains a
separate open signature (G-SPUR reported in both forms above). The P-1
Amendment-1 firing (the 1,300 seed was hand-rounded, not instrument-derived)
is carried here as required. The ercot-188/E2 P0 bit-identity forfeiture is
inherited unexpired.
