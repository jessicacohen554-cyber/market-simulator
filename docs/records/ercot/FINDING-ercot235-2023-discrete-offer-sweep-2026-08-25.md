# FINDING — ercot-235: the 2023-discrete-config campaign — 11 kill-gated solves; the winner (k_peak 24) is the FIRST ERCOT config to PASS C3b-2023 and C3c-2023, leaving C3a-2023 (−13.5 %) the sole failing criterion

**Date:** 2026-08-25 · **ISO:** ERCOT · **Authorization:** the owner's
2023-discrete-config order (verbatim in the ercot-235 log entry: solve 2023
for its own ECRS-era conditions; rule 16 waived; Q-B/R-A superseded by the
owner) · **Charter:**
`docs/PRECOMMIT-ercot235-2023-discrete-offer-sweep-2026-08-25.md` (grid,
kills and selection fixed before each round's solves; amendments 1–3 record
each round's result before the next round's grid) · **Registered winner:**
`2026-08-25-235-2023-discrete-k24`
(bundle `results/calibration/ercot235_r10`; grid points R1–R9, R11 are local
W-2 probe bundles whose `ercot235_point_score.json` records this table).

**What this is:** rule-1-sanctioned offer-curve TUNING on a discrete 2023
config — structure frozen at the `2026-08-25-234-eastex-identity` keeper
recipe (EASTEX identity repair included); ONE added residual-identified
scalar, declared in the DOF ledger (n_residual 6 → 7). Not a structural
claim: the tuned level stands in for the adjudicated 2023 conduct object
(ECRS-era scarcity equilibrium an LP with competitive offers cannot form —
ercot-209/211/216 lineage), carried as an explicit parameter instead of an
unexplained residual.

## 1. The campaign table (official 2023 basis; kills per precommit)

| pt | k_peak | k_eh | C3a-2023 | C3b | C3c (/181) | kills |
|---|---|---|---|---|---|---|
| keeper | 1 | 1 | −39.7 % | 0.730 | 72 | — |
| R1 | 3 | 1 | −34.5 % | 0.622 | 155 | clean |
| R2 | 3 | 1.75 | −27.6 % | 0.580 | 156 | **coal +6.04 TWh** |
| R3 | 5 | 2.5 | −16.8 % | 0.465 | 175 | **coal +8.38 TWh; off-season** |
| R4 | 6 | 1 | −30.0 % | 0.526 | 173 | clean |
| R5 | 10 | 1 | −25.6 % | 0.434 | 173 | clean |
| R6 | 14 | 1 | −21.3 % | 0.344 | 180 | clean |
| R7 | 20 | 1 | −16.6 % | 0.246 | 180 | clean |
| **R10** | **24** | **1** | **−13.5 %** | **0.186 PASS** | **180 PASS** | **clean — WINNER** |
| R11 | 27 | 1 | −11.4 % | 0.149 | 180 | **new shed h4097 (grows with k)** |
| R8 | 30 | 1 | −9.3 % | 0.119 | 180 | **new shed h4097 (35.9 MWh)** |
| R9 | 45 | 1 | +0.8 % | 0.189 | 180 | new shed h4097 (310.9 MWh) |

Three measured structure lessons, all precommit-recorded before the next
round ran:
1. **`econ_high` is the corrupt lever** — it buys level by re-ordering the
   merit stack (coal over-runs measured generation 6–8 TWh). Excluded from
   round 2 onward.
2. **The peak-band lever is structurally free through k=24**: coal flat
   (+0.10 TWh at every point), zero shed, the calibrated off-season months
   untouched (the band targeting localizes the lift to the scarcity windows
   through the merit order itself — no time window is coded), and the spur
   cost saturates at 68 banded hours (keeper 11) from R4 onward.
3. **The clean frontier ends between k=24 and k=27**: past it, the
   reshaped price path manufactures a single June-20 17:00 shed hour
   (h4097), growing with k — the ercot-221 G-SHED pattern. The band-reaching
   R8 (−9.3 %) and R9 (+0.8 %) are therefore killed as precommitted; their
   existence shows C3a-2023 is REACHABLE on this surface if the h4097 object
   is ever repaired, and is ~2 pp away at the frontier without it.

## 2. The winner, and what it means

`2026-08-25-235-2023-discrete-k24`: **C3a-2023 −13.5 %** (keeper −39.7 %),
**C3b-2023 0.186 — the first PASS of the 2023 shape criterion in the ERCOT
program**, **C3c-2023 180/181 = 0.994× — PASS** (no C3c ledger entry needed
for 2023; 2024/2025 are not scored in this bundle). Registered
determination: **NOT-YET on C3a-2023 ALONE** — the first single-criterion
ERCOT fail set since ercot-213. August lands $196 vs actual $220 (keeper
$93); the deep tail fills to 56 h ≥ $1,000 vs actual 59.

The selected k is not an arbitrary landing: at k_peak = 24 the gas
peak-tranche offers sit at ~$1.7–4.4k — inside the MEASURED 2023 evening
ask range (ercot-161/162: submitted SCED asks $3.4–5k), i.e. the tuned
level converges toward the documented 2023 conduct rather than past it.

**Honest costs, at full magnitude:** one residual-identified scalar
(DOF-ledgered; identified in-sample on 2023 only, no held-out validation);
68 banded spurious mid-band hours vs the keeper's 11 (the blunt-instrument
price of the lift — hours the model now prices $150–500 where the market
stayed low); and the remaining −13.5 % C3a gap, whose next ~4 pp are
blocked by the h4097 shed object, not by the surface.

## 3. Open to the owner

1. **Keeper structure:** does the ERCOT lane now carry a PAIR — the
   cross-year `2026-08-25-234-eastex-identity` (2024/2025) plus this
   2023-discrete run — or does the 2023-discrete run become the designated
   keeper for 2023 reporting? Registered and reported; not self-adjudicated.
2. **Round 5, if wanted:** the h4097 shed object (a storage/commitment
   state interaction the reshaped price path exposes at k > 24) is the one
   thing between the clean frontier and the C3a band; it is a bounded,
   diagnosable single-hour object.

## Hygiene

Years = {2023} only (owner rule-16 waiver, recorded; rule 22 satisfied);
ERCOT-only (rule 25); every solve precommitted before its grid ran, kills
direction-blind, rejected points reported (rule 15: the winner registered;
grid points are W-2 local probe bundles with committed JSON records quoted
here); no mechanism cell edited (rule 28(b) — no matrix mechanism tested;
the tuning surface is the standing DOF-ledgered one); no CI jobs. The
3-year keeper and its records are untouched.
