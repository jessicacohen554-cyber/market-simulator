# FINDING pjm-164 — C3c program Q1: PJM's reserve-dual channel is REAL, not the ercot-214 phantom

**Session:** pjm-164, 2026-09-01. **Charter:** `docs/CHARTER-c3c-scarcity-program-2026-08-31.md`
Q1. **Zero solve — committed artifacts + in-repo published data only.** Keeper audited:
`2026-08-15-pjm-162-inputclock` (bundle `results/calibration/pjm_debugb_inputclock_A`,
CALIBRATED, every criterion PASS — state re-verified this session with
`calibration_verdict.py --run-id` and `audit_keepers.py --iso PJM`, both clean).
**Artifact:** `results/calibration/_pjm164_c3c_overlap.json`. **No keeper, shard, marker,
matrix-cell or determination change** (nothing tested — this audits existing artifacts).

## Verdict: REAL — charter Q2 proceeds

The channel behaves like NYISO's timing (right hours), not CAISO's, in the only year it
materially fires; where it fires, PJM reality was pricing reserve scarcity through the same
mechanism (published DataMiner2 reserve MCPs); and reality's own >$200 tail is itself
reserve-scarcity-priced. The ercot-214 signature — a tail manufactured through a
price-formation channel the real market does not have, in hours the real market priced no
scarcity — is **absent**. Three honest caveats are recorded in §5; none is
determination-level.

## 1. What was audited, exactly

The C3c gate for PJM scores the **energy-only** basis: the registered payload carries no
`overlay` key, so `score_price_tail` reads `ordc.hoursGt200.model` — the render fallback's
count of hours where the **max-across-zones P1 energy-balance dual** exceeds $200
(`render_calibration_html.py::_tail_hours` over `system_<year>.parquet` `price`). The reserve
channel therefore enters the scored tail only **through** the energy dual (co-optimization
opportunity cost), never as an adder. This session replicated that construction from the
committed bundle bytes and matched the payload exactly: model 4/10/32 h vs actual 6/18/59 h
(2023/2024/2025).

Inputs: keeper `hourly/system_<year>.parquet` + `hourly/reserve_family_<year>.parquet` (P1),
`data/raw/_validation-source/actual_lmp_hourly_PJM.parquet` (rt, da-fallback), and — for T2 —
`data/raw/PJM-AS/reserve_market_results_<year>.parquet` (DataMiner2 RT reserve market
results, 5-minute grain, SR/PR/30MIN × PJM_RTO/MAD, requirement/held/MCP). Both sides on the
same hour index (k-th real UTC hour after EST midnight Jan 1). Hour labels below are EST.

## 2. T1 — overlap of model tail with reality's tail (the caiso-144 §D construction)

| year | model >$200 | actual >$200 | **overlap** | share of model tail | share of actual tail | model tail h with reserve dual>0 | overlap of that subset |
|---|---|---|---|---|---|---|---|
| 2023 | 4 | 6 | **0** | 0.00 | 0.00 | 0 | 0 |
| 2024 | 10 | 18 | **1** | 0.10 | 0.06 | 2 | 0 |
| 2025 | 32 | 59 | **14** | **0.44** | **0.24** | 27 | **13** |

Benchmarks: CAISO's overlay overlap was 1/47, 0/35, 0/8 (phantom-shaped, wrong hours);
NYISO's shortfall overlap was 5/20, 0/7, 20/24 (real-shaped, right hours). PJM 2025 is
NYISO-shaped; PJM 2023–24 have near-zero overlap — but with near-zero reserve involvement
(§3), so the mis-timing there is not the reserve channel's.

Hour-level anatomy (full table in the artifact JSON):

- **2023 (0/4):** all four model tail hours are one July-28 afternoon congestion episode.
  Actual RT there: $45–82. Reserve duals: **zero — the channel never fires in any hour of
  2023** (max family dual −0.0; held ≡ requirement at zero cost). Reality's 6 tail hours
  (Jan 10 morning, scattered summer/fall late-afternoons) are all missed.
- **2024 (1/10):** eight of ten model tail hours are July 14–15 afternoons (actual RT
  $72–282; the single hit is 07-15 16h at $282). The only two reserve-binding tail hours
  (Aug 27, duals ≤$8.5) land where actual RT was $84/$71. Reality's missed 17 include five
  January winter-morning/evening hours.
- **2025 (14/32):** the model tail sits on the real June 23–25 and July 28–29 heat events.
  The largest duals coincide with reality's extreme hours — 06-24 17h EST: family dual sum
  $258, actual RT **$1,722**; 06-24 15–18h duals $118–258 against actual $405–1,722. The 18
  non-overlap model tail hours are shoulder hours of the same events, actual RT p50 $122
  (12/18 above $100) — near-misses at the threshold, not cheap-reality phantom hours.

## 3. T2 — did PJM reality price reserve scarcity there? (data IS in-repo)

`reserve_market_results_<year>.parquet` gives the published RT reserve MCPs. Per-hour
measure: max over SR/PR/30MIN × RTO/MAD of the within-hour time-mean MCP (5-min grain
averaged to the hour — the settlement-aligned grain for an hourly-LMP tail comparison).

| year | hours published MCP >$25 | in model's reserve-binding hours: n, MCP p50 / max | in reality's >$200 LMP tail: MCP p50 / >$25 count |
|---|---|---|---|
| 2023 | 92 | 0 binding hours | $172 / 6 of 6 |
| 2024 | 235 | 2, $21 / $29 | $43 / 11 of 18 |
| 2025 | 391 | 29, **$88 / $1,614**; 20/29 >$25, 12/29 >$100 | $143 / 46 of 59 |

Two facts, cutting in opposite directions:

1. **The mechanism is the market's own.** PJM reality prices reserve scarcity frequently and
   at scale, and its >$200 LMP tail hours are overwhelmingly reserve-priced hours (2023: all
   six; 2025: 46 of 59). Where the model's channel fires (2025's 29 binding hours), published
   reserve MCPs were high in the same hours (p50 $88, max $1,614 on the same June-24/25 days).
   Contrast ercot-214: published settled RTORPA p50 was **$14.2** in the contaminated hours —
   ERCOT reality had no reserve scarcity to recover; the arm's channel was manufacturing one.
   PJM is the opposite case.
2. **The channel under-fires reality by an order of magnitude.** Reality priced hourly-mean
   reserve MCP >$25 in 92/235/391 hours; the model binds 0/2/29. The entire winter-morning
   reserve-scarcity face (Jan 2024, Jan 2025 — hours reality priced both reserves and >$200
   LMPs) is absent from the model's channel. Under-firing a real mechanism is a miss, not a
   phantom.

## 4. T3 — is the reserve channel load-bearing for the C3c PASS?

Two bracketing recounts (the true no-reserve counterfactual needs a solve, which this session
is forbidden): **strict** removes every model tail hour carrying any family dual >0 (a lower
bound — some would stay >$200 without the requirement); **dual-subtracted** re-thresholds
`max zonal price − Σ family duals` per hour (generous — subtracts the full stacked dual).

| year | gated model tail | strict removal | dual-subtracted | band vs actual | verdict without channel |
|---|---|---|---|---|---|
| 2023 | 4 | 4 | 4 | small-count: any 0–16 passes vs 6 | PASS — channel **irrelevant** |
| 2024 | 10 | 8 | 9 | [9, 36] vs 18 | strict FAILs (0.44×); subtracted exactly 0.50× boundary |
| 2025 | 32 | 5 | 30 | [29.5, 118] vs 59 | strict FAILs; subtracted 0.508× — passes by **one hour** |

The reserve channel **is load-bearing for the 2025 PASS** (and marginal for 2024): without
it the strict count collapses to 5/59. Since §2–§3 establish the channel is real, this is a
legitimate dependence — the criterion is passing on real structure. But it means the phantom
question was NOT moot, and the audit was worth running: had the channel been phantom, the
CALIBRATED determination would indeed have been resting on it.

## 5. Caveats — recorded unrewritten, none determination-level

1. **The 2023 PASS is not evidence of scarcity-tail formation.** The channel fires zero
   hours in 2023; the 4-hour model tail is one mis-timed July congestion episode (reality
   $45–82, published reserve MCP ≈ $0 in those hours, overlap 0/4); the criterion passes
   because actual = 6 falls under the small-count guard, where |4−6| ≤ 10 passes at any
   model count from 0 to 16. When the program cites PJM as "the existence proof", the
   citation is **2025** (and weakly 2024's level), not 2023.
2. **The channel under-fires reality's reserve pricing ~10× and misses the winter face
   entirely** (§3.2). The C3c magnitudes (0.54–0.67×) sit at the band's lower edge for the
   same reason. Whether the winter-morning face is reachable in this LP class is exactly
   charter Q2/Q3 territory — it is a measured gap, not proposed work.
3. **2024's tail is congestion-formed, mostly mis-timed** (overlap 1/10; published reserve
   MCP p50 $0 in the model's tail hours). Like 2023, the mis-timed component rides a real
   market mechanism (congestion) firing on the wrong day — a shape miss the C3b/C3c bands
   already tolerate, not a channel the market lacks.

## 6. What PJM has that the other ISOs do not (the census question, answered)

From the census (charter §2) plus this audit: PJM's co-opt carries requirements at published
scale that actually collide with the merit order in heat events — RTO primary ~3.7–3.9 GW
(1.5× LSC) plus the ~2.5–2.9 GW MAD subzone requirement, held exactly at requirement in
most hours (p50 headroom 0) so that a demand/outage swing prices opportunity cost, never
shortfall (0 shortfall hours in all three years; duals to $187.90). NYISO's binding families
are capped at $25/$40 with the $750–775 NYCA products never binding; NEISO's requirements
never touch its fleet (0 binding hours, all years); CAISO arms no reserve co-opt in the
keeper. And PJM's real market is the one whose reserve product prices frequently and at
scale (§3) — so the same LP structure has something real to express there. The existence
proof stands: this LP class can form a genuine reserve-scarcity tail **where the ISO's
requirement geometry actually bites**, which is a statement about PJM's market, not a
transferable mechanism (rule 25 — any transfer enters other shards as `U`).

## 7. Disposition

- **Verdict REAL → charter Q2 (NYISO product-level shortage question) proceeds.**
- No keeper/shard/marker/determination action; no fix proposed or made (charter Q1 is a
  measurement). No matrix cell moves — `energy_reserve_coopt` PJM stays **K**,
  `ordc_scarcity_overlay` PJM stays **G**; this session tested nothing, it audited the
  committed record of what is already armed.
- The under-firing gap (§5.2) and the 2023 small-count weakness (§5.1) belong to the
  program's synthesis step, not to this lane — recorded here and in the artifact JSON only
  (the cross-ISO governance log is deliberately untouched; nyiso-164 may be running in
  parallel).

*Evidence: `results/calibration/_pjm164_c3c_overlap.json` (per-year counts, shares, hour
lists, T2/T3 tables) · keeper sidecars `pjm_debugb_inputclock_A/hourly/` ·
`data/raw/PJM-AS/reserve_market_results_{2023,2024,2025}.parquet` ·
`actual_lmp_hourly_PJM.parquet` · construction: `render_calibration_html.py::_tail_hours`
fallback + `calibration_verdict.py::score_price_tail` (G-20a settled-basis check: no overlay
key in the PJM payload) · benchmarks: FINDING-caiso144 §C/§D, nyiso-163b census
(`_nyiso163b_c3c_reserve_timing.json`), ercot-214/215 phantom record.*
