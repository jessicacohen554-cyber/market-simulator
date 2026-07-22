# FINDING — CAISO body overprice + evening-merit gap are one seam-shape defect (2026-07-07)

> **SUPERSEDED IN PART (2026-07-07, same day, W3a lane) — §2 and §5 are wrong; do not
> build on them.** §2's "measured actual" hod table was bucketed on the **UTC hour** of
> the EIA-930 `period` timestamp (reproduced to the MW in the correction), so the
> model-vs-actual comparison was 7–8 hours out of phase: the "evening collapse /
> +2–3.2 GW evening over-import / midday under-import" attribution inverts on the true
> clock (real residual: midday **over**-import at the envelope, overnight/evening
> **under**-import, no evening suppressor), and §5's pre-registered prediction points
> the wrong way in both segments. §1 (hod-λ table), §3's reserve-scarcity/offer-band
> adjudications, and §4's firm-block observations survive. Full forensics, the corrected
> tables, a second (in-LP) clock defect in the corridor envelope and its fix + A/B, and
> the reattribution of the C3a body to belly gas commitment:
> **`FINDING-caiso-seam-tz-correction-2026-07-07.md`**.

**Thread:** G-20d (`docs/g20-scarcity-price-formation-diagnosis-2026-07.md`) folded into G-15;
work-order item 3 of the caiso-calibration-burndown lane ("diagnose why the evening merit
order clears low — offer bands vs RA commitment vs import pricing").
**Basis:** `caiso61_lolp_tail` — a byte-faithful HEAD replay of the caiso-60 keeper recipe
(P1-native, drag ON, per-hub intertie + firm base + measured corridor p95 envelopes ON per
`meta.json`; the run_config `caiso_corridor_flow_limit: false` is the known O-2 serialization
gap, `docs/caiso-c5-wecc-cap-closeout-2026-07-03.md`) — all three years, plus the measured
EIA-930 CISO series (`data/raw/CISO_region.parquet`, TI) and the LOLP-overlay deriver
diagnostic. Supersedes nothing; extends `FINDING-caiso-evening-merit-2026-07-04.md` to the
current keeper lineage and attributes the C3a/C3b/C4 residual across hours.

## 1. Where the +20–42 % C3a overshoot lives (hour-of-day, model load-weighted λ vs actual hub)

| bucket | 2023 Δ | 2024 Δ | 2025 Δ | actual level |
|---|---|---|---|---|
| midday h9–15 | **+$27…34** | **+$17…23** | **+$20…24** | $13–33 (duck belly) |
| overnight h0–3 | +$22…25 | +$8…10 | +$11…12 | $37–50 |
| evening peak h19 | **+3.0** | **−0.6** | **+8.1** | $46–73 |
| evening shoulder h20–21 | +$11…13 | +$4 | +$9…10 | $45–65 |

The evening **peak level is essentially right**; the **body is inflated** — worst at midday.
The model's diurnal swing (2023: 57→76 ≈ 1.33×) is ~3× too flat vs actual (23→73 ≈ 3.2×).
That flatness, not the peak level, is what C3b (NRMSE ≈ 0.29) and C4 (fleet dispatch corr
r ≈ 0) score. "Evening merit clears low" is therefore precisely: **the evening premium over
the model's own body is missing**, because the body is high and the peak is capped from
above by cheap evening imports (§2).

## 2. The load-bearing object: the WECC seam's diurnal delivery is near-flat vs a 5:1 measured swing

Model net corridor import (caiso-61, WECC_PNW→NP15 + WECC_DSW→SP15, hour-of-day means) vs
measured EIA-930 CISO net imports (−TI):

| hod | 2023 model | 2023 actual | 2024 model | 2024 actual | 2025 model | 2025 actual |
|---|---|---|---|---|---|---|
| 0 | 4,730 | 955 | 3,755 | 1,439 | 4,419 | 1,654 |
| 6 | 3,659 | 5,444 | 3,216 | 5,432 | 3,681 | 5,928 |
| 9 | 4,084 | 5,311 | 4,344 | 5,589 | 5,130 | 6,255 |
| 12 | 3,462 | 5,131 | 3,537 | 5,290 | 4,178 | 5,957 |
| 15 | 2,790 | 3,906 | 2,429 | 4,220 | 3,301 | 4,749 |
| 19 | **3,893** | **669** | **2,984** | **1,380** | **3,560** | **1,884** |
| 21 | **4,172** | **200** | **3,131** | **887** | **3,810** | **1,308** |

Annual net TWh is roughly right (34.5/29.8/35.3 model vs 28.5/30.8/35.9 actual) — the
**shape** is wrong in all three segments:

- **Evening h19–21: +2.0–3.2 GW over-import.** The real seam collapses to 0.2–1.9 GW as the
  whole West peaks (neighbors withdraw); the model keeps importing 3–4.2 GW at measured hub
  prices. This is the direct suppressor of the evening premium: ~3 GW of external supply at
  the ramp is why evening CT cannot clear on merit and why the `ct_netload_drag` has to carry
  the class (G-15). The 07-04 finding's evening *export* artifact is gone (0 net-export
  hours — per-hub firm base + export-direction envelope fixed it); the residual defect is
  over-*import*.
- **Midday h9–12: −1.0 to −1.8 GW under-import**, and the model essentially never reaches
  the curtailment margin (hours with dump > 1 MW: 0 / 28 / 8 per year vs routine real
  CAISO midday curtailment). Midday is therefore gas-CC-marginal at $36–59 where reality is
  import/solar-surplus-marginal at $13–33 — the single worst C3a bucket.
- **Overnight h0: +2.8–3.1 GW over-import**, with import tranches price-setting in 15–40 %
  of overnight hours (interior-solution fraction, 2023 h0–4) and the **DSW_solar_PV firm
  tranche running at 84 % of max at night** (`caiso_import_solar_shape` exists for exactly
  this and is off in the keeper lineage).

**Why the measured p95 envelope doesn't prevent this (no defect in the envelope itself):**
`eia_loader.measured_corridor_flow_envelope` caps each corridor at the per-(month ×
hour-of-day) **p95** of measured net import — a deliverability *ceiling* (rule-12-safe: the
LP clears below it). But evening buckets have a low median and a fat right tail (heat
events), so their p95 stays high and the *typical* evening thinness — the neighbors' own
evening scarcity — is not a capability fact the ceiling can carry. The model then imports to
hub-price merit every evening. Tightening the percentile toward the median would turn the
capability bound into an outcome pin tuned to the residual (rules 12/23) — **not** the fix.

## 3. Candidate adjudication (work-order item 3)

- **Reserve scarcity — RULED OUT (measured twice).** The published LOLP overlay
  (`caiso_scarcity_pricing`, #1556 params: VOLL $2,000, MCL 1,400 MW, σ 2,500 MW) derived
  post-solve on this exact bundle: 2023 mean +$0.54 (>$100 in 10 h; RT-basis tail 502→511 h
  vs 21 h actual — it *adds* to the over-tail); 2024 +$0.04, 2025 +$0.01, tail 0→0 in both
  (the deficit years). The in-LP co-opt was already inert (caiso-59, +$0.47). Confirms
  G-20d: the tail miss is not reserve-scarcity-shaped.
- **Offer bands — NOT the driver of this residual.** CC committed is already 1.00× at the
  keeper; econ_low 0.95× remains sub-SRMC (CAISO's own mitigation constructs cost-based
  Default Energy Bids at 110 % of fuel+VOM+GHG, so a systematic sub-1.0 econ band has no
  market-design basis) — but re-grounding it *raises* offers, i.e. raises the already-high
  body; it cannot produce the missing diurnal swing. Park under #1302 (per-ISO committed-band
  re-grounding) on its own merits; it is not the C3a/C4 root cause.
- **RA commitment — the coupled INTERNAL half (G-61).** The same-day D-8 closure §7
  re-verification found the P1-native RA bridge floors the ENTIRE merchant CC fleet
  through the solar belly (no RA-quantity gate; CC min-down > belly length), spun out as
  **G-61** — internal supply at the wrong hours, where the seam defect here is external
  supply at the wrong hours; both flatten the diurnal profile and pre-position CC to eat
  the evening ramp. The two are coupled through price formation: G-61 §7's price-based
  release mechanism was inert because "the model's midday LMP never reaches the
  curtailment floor ($56–58 through the belly)" — this finding's §2 shows *why*: the
  midday −1 to −1.8 GW import under-delivery keeps midday gas-marginal, so any
  curtailment-price-triggered release (or G-61 path (c)'s curtailed-VRE signal) is starved
  by the seam defect. Fixing the seam shape is a precondition for G-61's release signals
  to fire, and together they are the D-8/G-15 drag-retirement path.
- **Import pricing/delivery — CONFIRMED root cause** (§2). One structural object — the
  hourly WECC seam supply — owns the midday overshoot, the overnight overshoot, the missing
  evening premium, and through it the CT-merit gap the drag papers over.

## 4. Admissible fix directions (filed, not built here — each is measured-data-first, rule 14)

1. **Measured specified-import volumes by corridor (#1373's real content).** The firm/
   contracted tranche MW (PNW_hydro_base, DSW_solar_PV, …) are estimates; the 07-04 finding
   already flagged PNW_hydro_base at 86 % evening utilisation as undersized, and the DSW
   solar block's flat-at-night delivery is unphysical. The measured objects: CAISO
   specified-source import schedules / EIM base schedules by corridor, or at minimum the
   EIA-930 by-DIBA hourly history shaping each firm block's **delivery profile** (a
   contract/product shape — physics of the product, not an outcome pin).
2. **`caiso_import_solar_shape` (built, default off):** a solar-named firm product delivering
   84 % of max at night is indefensible on product physics; the flag's net-load-conditioned
   shape is the existing lever. Single-delta probe candidate on the keeper recipe.
3. **Neighbor-scarcity evening withdrawal:** the evening thinness is the neighbors' own
   net-load peak. Structural forms: (a) hub-price-coupled tranche supply already prices the
   energy leg — verify the delivered-cost stack (hub + wheel + border carbon) hour-by-hour
   against the measured intertie LMP series; if evening delivered cost is genuinely below
   the CAISO LMP while real flows are ~0, the binding real object is **scheduled quantity**
   (→ item 1), not price; (b) a measured net-load-conditioned availability shape on the
   spot tranches (the `wefor`-style conditioning, derived from the same EIA-930 history —
   forward-regenerating).
4. **Not admissible:** corridor-percentile tuning (p95 → p50) or any tranche-MW rescale
   chosen against the price residual (rules 12/23); re-flooring CT (rules 17–19); rejecting
   the co-opt/overlay for inertness (rule 1 — they stay, default-off/probe-scored).

## 5. Falsifiable prediction (pre-registered for the fix probe)

Shaping the seam to the measured diurnal pattern (items 1/2) should, with **no** offer-band
or floor change: lower midday λ toward the curtailment margin (C3a's worst bucket), raise
h19–21 λ by pricing out 2–3 GW of external supply, steepen the model's diurnal swing toward
the actual ~3×, move C3b/C4 materially, and shrink the D-2 share the drag must carry
(G-15/D-8). If it does all that, the drag's scarcity-pricing half retires with the seam fix
rather than with any scarcity overlay — closing G-20d and most of G-15 with one measured
mechanism.

## Files
- `results/calibration/caiso61_lolp_tail/` — HEAD replay bundle (this finding's basis; also
  the caiso-62 A/B base arm and the LOLP-overlay probe vehicle).
- `results/calibration/caiso61_overlay_diag.log` — deriver diagnostic (§3 numbers).
- `FINDING-caiso-evening-merit-2026-07-04.md` — the prior evening-merit adjudication this
  extends (its Lever-A evening-export artifact is fixed at HEAD; its Lever-B under-import
  reading updates to the three-segment shape defect above).
