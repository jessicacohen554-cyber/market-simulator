# CAISO — next-steps roadmap (2026-06-23 session pickup)

State at pickup: all prior session work is merged to `main`. Current keeper is
`caiso-import-cap-floor` (PR #788): two-mechanism priced import node (hub prices
+ gas-coupling + solar-shape) + aggregate WECC 8.3 GW simultaneous-import cap +
per-tranche delivered-cost basis + RA gas-commitment floor 0.80 + negative
renewable offers. 2024: neg-price hrs 815 (~800 actual), net interchange −30.4
TWh vs −32.4 actual. Residual: mean LMP ~$8 high, body +$6.

Parallel thread left un-merged: `caiso-20-bidir-intertie` replaced the
two-mechanism node with a single signed WECC intertie (both legs at the measured
hub) and **flipped the 2024 diurnal interchange correlation from −0.65 to
positive** — fixing the *shape* the keeper still gets wrong — but it never
adopted the keeper's level fixes (delivered-cost basis, gas floor 0.80). The two
import representations are mutually exclusive in code
(`run_calibration.py` ~1835: bidir supersedes the hub injectors).

## UNIFY attempt 1 — REJECTED (caiso 21 bidir+floor probe, 2026-06-23)

Ran the unify below (bidir + delivered-cost basis on the bidir import legs + RA
gas floor 0.80 + interchange shaping + neg offers, 3-yr). **Regressed the keeper
on every axis** — registered as a PROBE (`2026-06-23-caiso-21-bidir-floor`):

| metric (2024) | keeper import-cap-floor | unify probe | actual |
|---|---|---|---|
| neg-price hours | 815 | 194 | ~800 |
| net interchange | −30.4 TWh | −17.68 | −32.4 |
| p10 LMP | $1.40 | $33.63 | — |
| mean LMP | ~42 | 48.8 | 35.8 |
| diurnal corr | (poor) | +0.09 (2025 −0.12) | — |

**Root cause:** the gas floor (forces gas online) and the delivery basis (raises
import cost) BOTH suppress imports. On the single-flow bidir node the model
badly under-imports, and the bidir export leg sells the midday surplus at the
*positive* hub instead of crashing to negative — so the negative tail the keeper
relies on disappears, and the floor even drags the bidir diurnal win back toward
zero. The level levers are **antagonistic with the bidir representation, not
additive.** The delivery-basis CODE change (transmission.py) is structurally
sound and stays in (rule #1 — it is a real physical input); it is the *stacking*
that fails, not the basis itself.

### Refined next step for UNIFY (decompose)
Isolate which lever is bidir-compatible, one change at a time off the standalone
bidir keeper (which DID flip the diurnal corr positive without these levers):
1. **bidir + gas floor only** (no delivery basis) — does the floor alone keep the
   negative tail under the export-leg competition?
2. **bidir + delivery basis only** (no gas floor) — does the basis restore the
   merit order without collapsing imports?
If neither composes, the honest conclusion is that the diurnal fix (bidir) and
the level fix (keeper's two-mechanism node) are mutually exclusive *by design*
and the keeper stays as-is until measured WECC hub diurnal prices land (option B).

## DECOMPOSE step 2 — DONE: basis-only is the suppressor (2026-06-23)

Ran item 2 (`bidir + delivery basis only`, **floor explicitly off** via
`--no-caiso-gas-commitment-floor` — the flag DEFAULTS ON for CAISO, so omitting
it does *not* disable the floor). Registered PROBE
`2026-06-23-caiso-23-bidir-basis` (`caiso 23 bidir+basis-only`):

| metric (2024) | keeper import-cap-floor | caiso-21 basis+floor | **basis-only** | actual |
|---|---|---|---|---|
| neg-price hours | 815 | 194 | **194** | ~800 |
| net interchange | −30.4 TWh | −17.68 | **−19.09** | −32.38 |
| p10 LMP | $1.40 | $33.63 | **$33.63** | — |
| mean LMP | ~42 | 48.8 | **48.79** | 35.8 |
| import hours | — | — | **81.8%** | 89.0% |
| diurnal corr | (poor) | +0.09 | **−0.04** | — |

(2025 net −25.70 vs keeper −38.6 / actual −36.16, corr −0.12; 2023 corr +0.94 but
the basis is **inactive** in 2023 — no measured hub, the tie keeps its
static-ladder placeholder — so 2023 is not informative about the basis.)

**Verdict:** basis-only is nearly byte-identical to caiso-21 (basis+floor) on
every 2024 axis (neg 194=194, mean 48.79≈48.8, p10 33.63=33.63). Dropping the
floor barely moved anything → **the delivery BASIS, not the gas floor, is the
import suppressor** on the single-flow bidir node. The multiplicative line-loss
markup over-prices imports on the already-capped (8.3 GW) bidir leg: it collapses
the negative tail and net-import magnitude and drags the diurnal correlation the
standalone bidir keeper (`caiso-20`) flipped positive back to negative.

**Next (grounded, rule #12):** the line-loss markup is multiplicative
(`hub + max(hub,0)·loss + wheel`); on the capped single-flow node that loss term
is too aggressive. Try **wheel-only (additive) delivery** or a **smaller, source-
grounded loss factor** on the bidir import legs — a physical input, NOT a residual
tune. If even a minimal additive wheel still over-suppresses, the diurnal-shape
fix (bidir) and the merit-order-restoring basis are mutually exclusive *by design*
on the capped single-flow node, and the keeper stays as-is until measured WECC hub
diurnal prices land (option B).

## DECOMPOSE — BOTH halves done; combined verdict (2026-06-23, two parallel sessions)

The parallel session ran step 1 (`bidir + gas floor only`, basis reverted in
`transmission.py` commit 28574a6 — now main) and registered PROBE
`2026-06-23-caiso-22-bidir-floor`. Side-by-side, both off the standalone bidir
keeper (`caiso-20`, which flipped 2024 corr positive with neither lever):

| 2024 | keeper | caiso-21 basis+floor | caiso-22 **floor-only** | caiso-23 **basis-only** | actual |
|---|---|---|---|---|---|
| neg-price hrs | 815 | 194 | **221** | 194 | ~800 |
| net interchange | −30.4 | −17.68 | **−22.36** | −19.09 | −32.38 |
| mean LMP | ~42 | 48.8 | **46.81** | 48.79 | 35.8 |
| p10 LMP | $1.40 | 33.63 | **32.24** | 33.63 | — |
| diurnal corr | poor | +0.09 | **+0.22** | −0.04 | — |

corr by year: floor-only **+0.95/+0.22/+0.11** (positive every year) vs basis-only
**+0.94/−0.04/−0.12** (negative once the basis is active, i.e. 2024–25).

**Combined conclusion.** Both levers under-import and collapse the negative tail
on the single-flow node (neither beats the keeper), but they differ on *shape*:

* the **gas floor is diurnal-COMPATIBLE** — the bidir corr survives it positive
  every year (+0.22 2024); it is only level-antagonistic (forces gas online →
  fewer imports); and
* the **delivery basis is the STRONGER suppressor AND diurnal-INCOMPATIBLE** —
  it imports the least (−19.09), recovers the smallest tail, and its
  *multiplicative* `loss·max(hub,0)` markup drags corr negative (−0.04). Dropping
  the basis (floor-only) recovered net −19.09→−22.36, neg 194→221, corr −0.04→+0.22.

So the basis's **multiplicative loss** is the term to fix, and the **floor** is
the level lever to keep. The unified-keeper hypothesis (next run): **bidir + floor
0.80 + a WHEEL-ONLY (additive) delivery basis** — apply only the per-tranche
`wheel` ($2–6/MWh, real OATT PTP charges) and DROP the `loss·max(hub,0)` markup
(the multiplicative loss double-counts the congestion the 8.3 GW cap already
prices; physical justification, rule #12, not a residual tune). The additive wheel
still separates the flat ~$38 MCE into a rising delivered-import merit order
(PNW_hydro +2, DSW_solar +4, PNW_midC +5, WECC_scarcity +6) without the
price-scaling explosion that crushes imports midday. If even wheel-only still
under-imports / loses the tail, the diurnal fix (bidir) and the level fix are
mutually exclusive by design on the capped node and the keeper stays until
measured WECC hub diurnal prices land (option B).

## UNIFY attempt 2 — REJECTED (caiso 24 bidir+wheel-only PROBE, 2026-06-23)

Ran the wheel-only unify: bidir + RA gas floor 0.80 + the ADDITIVE per-tranche
OATT `wheel` term of `CAISO_IMPORT_DELIVERY_BASIS` on the bidir import legs, but
DROPPING the multiplicative `loss·max(hub,0)` markup (transmission.py
`inject_caiso_bidir_intertie_prices`). Registered PROBE
`2026-06-23-caiso-24-bidir-wheel` (`caiso 24 bidir+wheel-only`):

| 2024 | keeper | caiso-22 floor-only | **caiso-24 wheel-only** | caiso-23 basis-only | actual |
|---|---|---|---|---|---|
| neg-price hrs | 815 | 221 | **194** | 194 | ~800 |
| net interchange | −30.4 | −22.36 | **−18.66** | −19.09 | −32.38 |
| mean LMP | ~42 | 46.81 | **48.34** | 48.79 | 35.8 |
| p10 LMP | $1.40 | 32.24 | **33.36** | 33.63 | — |
| diurnal corr | poor | +0.22 | **+0.14** | −0.04 | — |

corr by year wheel-only: **+0.95 / +0.14 / −0.07** (2023 informative-free — basis
inactive; 2025 negative). 2023 net −19.41, neg 48; 2025 net −26.73, neg 9.

**Verdict — FAILS the keeper gate on every axis, and is mutual-exclusivity
confirmation, not a level fix.** The minimal additive wheel ($2–6/MWh) still
over-suppresses: wheel-only lands essentially on **basis-only** (neg 194 = 194,
net −18.66 ≈ −19.09, mean 48.34 ≈ 48.79, p10 33.36 ≈ 33.63), i.e. dropping the
multiplicative loss recovered almost nothing — the *wheel itself* is the
suppressor on the capped single-flow node, not (only) the loss markup. And it is
**worse than floor-only** on both level (net −22.36, neg 221, mean 46.81) and
shape (2024 corr +0.14 < +0.22; 2025 −0.07, not positive every year). Any delivery
adder that separates the flat MCE into a rising delivered-import merit order also
prices the tie out of the imports that build the negative tail and the positive
diurnal correlation.

**Conclusion (decompose thread closed).** The bidir diurnal-shape fix and any
merit-order-restoring delivery basis (multiplicative OR additive) are **mutually
exclusive by design on the capped 8.3 GW single-flow node**: the cap already
prices the binding congestion, so any extra delivered-cost adder double-suppresses
imports. The keeper (`caiso-import-cap-floor` / dashboard `caiso-19-local-band`)
stays as-is until measured WECC hub *diurnal* prices land (option B) — that is the
only remaining lever that can fix the shape without an import-suppressing adder.
The wheel-only transmission.py code change stays in (it is the structurally
correct additive form, rule #1/#12); only the config stacking is rejected.

## Original chosen path: UNIFY (superseded by the attempt above)

Bring the bidir-intertie mechanism to keeper parity so ONE keeper has both the
diurnal-shape fix and the price-level fix:

1. **Code:** add the per-tranche `CAISO_IMPORT_DELIVERY_BASIS` (line-loss +
   OATT wheeling markup over the hub MCE) to the import legs in
   `inject_caiso_bidir_intertie_prices` — mirroring
   `inject_caiso_import_hub_prices` (transmission.py ~575). The bidir export leg
   owes none (CAISO delivers to the neighbor at the bare hub). Arbitrage-free
   property preserved (import = hub·(1+loss)+wheel+carbon+ε ≥ export = hub−ε).
   The 8.3 GW import cap is already baked into the bidir leg
   (`CAISO_BIDIR_IMPORT_CAP_MW`).
2. **Config:** run bidir + `--caiso-gas-commitment-floor` (0.80) +
   `--negative-renewable-offers` + `--gas-hub-basis-overlay` (bidir run had the
   gas floor OFF; the keeper validated it at 0.80). gas-coupling / solar-shape
   are intentionally NOT used — bidir supersedes them (single unified hub).
3. **Solve** 3 years (2023 2024 2025), register as a keeper, compare to
   `caiso-import-cap-floor` on: mean LMP, body, neg-price precision/recall, net
   interchange, AND the diurnal interchange correlation.

Risk to watch: 2023 has no measured WECC hub series (OASIS Jan–Feb aged out), so
the bidir tie falls back to its static-ladder placeholder for 2023 — same
limitation the keeper has.

## Logged alternates (not chosen this session)

### B. Diurnal import price shape (the body-overprice diagnosis's recommended build)
`DIAGNOSIS-caiso-body-overprice-2026-06-21.md`: the residual +$6 body is a
flat-import diurnal artifact — over-import midday → $28 PNW_hydro_base floor
(reality is long → ~$14), under-import overnight → gas-CC $48 (reality $42). The
fix is a measured diurnal import *price* vector (cheap-but-positive midday,
cheap overnight). **Blocked** on OASIS measured WECC hub hourly prices (Mid-C /
Palo Verde) — not fetchable in this environment. Before committing here, check
whether the bidir hub series already supplies enough diurnal signal (it may
subsume this item) or whether any in-repo proxy exists. An availability cap is
NOT the instrument (caiso-16 regressed; band-only is a no-op; the
PNW_hydro_base −$20 collapse hit an ~85% precision wall — all ruled out).

### C. Evening-ramp residual
The evening ramp (h18–21) is *under*-priced (−21%, model flat $50 vs $66 peak)
and is currently offsetting the mean. Lifting it needs a non-AS mechanism:
the CAISO summary explicitly rejects an ORDC / AS-stream overlay (RA-backed,
$2,000 cap, no scarcity tail; the model already over-prices the body). Higher
risk of a dead end; revisit only after UNIFY settles the body/shape.
