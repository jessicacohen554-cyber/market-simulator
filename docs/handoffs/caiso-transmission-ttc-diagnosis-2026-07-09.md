# CAISO transmission / TTC / zonal-topology diagnosis (2026-07-09)

**Scope.** Ground-up structural reassessment of CAISO calibration with transmission/TTC and
zonal topology as the primary suspects. Diagnosis-and-plan, not a re-tune (rule 1). Baseline is
the caiso-65 keeper (`2026-07-07-caiso65-seam-envelope-clock`) *with* `temp_dependent_derate`
adopted default-on (owner decision). Holdout discipline (rule 22): everything below uses the
2023–2025 train years and the already-committed keeper/probe bundles + `data/raw` only. No
2022/2019/H1-2026 solve, score, or intake was performed.

---

## TL;DR — the headline is locational, not the import cap

The dominant CAISO structural failure is **SP15 copperplate under-pricing**. SP15's *annual mean*
LMP is dramatically **under**-forecast — and the gap grows every year:

| Year | SP15 model | SP15 actual | miss | NP15 model | NP15 actual | miss |
|------|-----------:|------------:|-----:|-----------:|------------:|-----:|
| 2023 | $69.62 | $117.52 | **−$48** | $65.82 | $86.57 | −$21 |
| 2024 | $47.18 | $124.55 | **−$77** | $42.71 | $85.07 | −$42 |
| 2025 | $49.51 | $127.04 | **−$78** | $47.30 | $83.41 | −$36 |

(model vs DA-actual hub mean LMP; caiso-65 keeper run payload.) The real SP15↔NP15 spread is
**$31–44**; the keeper produces **~$4**. The LA-basin locational premium that sets real SP15
prices is essentially absent.

This single gap explains **six of the failing criteria** at once (C1 fuel-mix, C3a mean, C3b
shape, C3c tail, C4 correlation, C8 forced-energy). The transmission suspects the task flagged —
the WECC import cap and the internal Path-15/26/46/66 TTC seeds — are **not** the primary drivers;
the instrumentation below shows the import ceiling is *not binding below actual in the scarcity
hours*, and the internal path TTCs barely bind under the copperplate. The import representation is
a real but *secondary* (base/shape/volume) problem, addressed after the zone split.

---

## 1. The map of what can bind (and what actually does)

Import **supply** is only ~12.2 GW (`IMPORT_TRANCHES["CAISO"]` = 12,171 MW), so the ~16 GW MIC
seam cap (published, replaces the old fitted 7,500 via `capacity_deliverability_limits`) never
binds. In the keeper the tightest import-path limit is the **measured p95 corridor ATC envelope**
(`caiso_corridor_flow_limit`), DSW ≈ 3.6 GW / PNW ≈ 0.8 GW midday, per corridor
(`WECC_PNW`→NP15, `WECC_DSW`→SP15). Internal Path 15 (5,400) and Path 26 (4,000) are symmetric
catalog seeds; the asymmetric-rating flag (`caiso_asymmetric_path_ratings`, N→S 4,000 / S→N 3,000
for Path 26) is **off** in the keeper.

Provenance summary (full table in the session transcript / `iso_configs.py:280–338`,
`interchange_config.py`, `transmission.py`, `capacity_deliverability.py`):

- **Path 15/26/66/46 TTCs** — catalog-seed (WECC Path Rating Catalog), explicit "verify against
  OASIS" Tier-3 comment. Not re-grounded against OASIS branch-group ATC yet.
- **WECC_import_simultaneous 7,500 MW** — fitted scalar; superseded by published MIC when
  `capacity_deliverability_limits` is on (keeper), inert thereafter. Still governs the **forecast
  path** (flag default-off) → open parity item O-1 / issue #1373.
- **Corridor p95 envelope** — measured (EIA-930 CISO BA-to-BA interchange, p95 per month×hod).
  Binding import limit in the keeper. Seam-clock TZ fix (caiso-65) corrected a 1–2 h phase error
  in delivering it to the LP.
- **Firm import base** — `caiso_perhub_firm_base`: static PNW_hydro_base 1,566 + DSW_solar_PV
  1,805 = **3,371 MW** priced-flat; everything above is spot-priced at Malin/Palo-Verde hubs.

---

## 2. Instrumenting the 2023 over-scarcity — it is a copperplate symptom, not the import cap

**Correction to the premise.** The 507 h of zonal-max LMP > $200 in 2023 is a property of the
**keeper itself** (temp-derate OFF: model 507 vs actual 21), not a temp-derate artifact —
temp-derate barely moves it (529 h). And the year signature is a **sign-flip**:

| Year | model hrs>$200 | actual hrs>$200 |
|------|---------------:|----------------:|
| 2023 | 507 | 21 |
| 2024 | 0 | 35 |
| 2025 | 0 | 8 |

Both sides are the **same** root cause. With no locational scarcity mechanism, the model's entire
price tail is set by the **system-wide supply-stack top** (gas + the WECC scarcity import
tranche), so it tracks the annual gas price instead of local congestion: high-gas 2023 ($2.54)
pushes evening peaks over $200 in ~507 h (spurious), low-gas 2024/25 ($2.19/$3.52 belly) keeps the
whole system under $200 so the model prints **zero** scarcity — while reality still had 35/8 h of
**local** SP15 scarcity the copperplate cannot form. A legacy copperplate probe confirms the
mechanism directly: all four zones price **identically** ($76.4 mean, 684 h>$200, all in the
evening ramp h16–21).

**Is the model hitting an import ceiling in hours the real system imported freely?** No — the
opposite. In summer-evening peak hours (JJAS h17–21, 2023) the model's p95 envelope *allows*
mean ≈ 5.3 GW of imports while CAISO actually imported only ≈ 2.1 GW (the WECC neighbours are
short in CA summer peaks too). The envelope caps below actual in only ~1 % of those hours; even in
the top-50 import hours of the year the model is short only ~150 MW. **The import ceiling is not
the scarcity driver.** Raising the corridor percentile (p95→p99) would *not* fix the tail — do not
spend a solve on it.

Where the corridor envelope *does* bite is a flat ~0.3 TWh/yr of clipped import spread evenly
across the day — a small contributor to CC backfill, not a scarcity mechanism.

---

## 3. The CC-over / CT-under split is a locational MIX, not a volume error

Gas as a **family** is roughly in band (C2 commercial-band): model 72.9/74.5/71.8 TWh vs actual
74.2/71.8/68.5 (2023/24/25). The failure is the **split within gas**:

- **CT_PEAKER** class total ≈ **1.4–2.1 TWh** (model) vs actual **3.1–5.2 TWh** — under by 2–3×.
- **CC_REGULAR** absorbs the difference (≈ 61–64 TWh), over-dispatched at the class level.

Mechanism: SP15 priced as system-marginal gas (~$47–70) never clears CT peakers (cheapest band
~$59 > evening LMP in ~70 % of hours), so the LA-basin peaker energy is served by cheaper
system CC instead. The `ct_netload_drag` floor is then bolted on to force the peakers back up —
and the D-2 diagnostics show it carrying **59.7 % / 55.8 % / 63.4 %** of CT class energy
(2023/24/25), a rule-20 C8 **FAIL** in 2023/24, and it is LOYO-unstable (+18 % train-vs-full slope
drift, G-15 open). Per the seam FINDING it "**is the class it floors**" and cannot be stabilised
by better regression — only by a structural mechanism taking load off it. **That is the signature
of a missing local congestion signal, and the drag is its scaffold (rule 12: a peaker floor
standing in for absent congestion has no forward story).**

Note the RA-must-offer bridge is a *different* mechanism and is **not** the culprit here: it
forces only ~3.2–3.8 TWh of CC (≈ 5–6 % of class, well under the 30 % cap), and the seam FINDING
established reality runs **3.1–5.2 GW *more* belly gas** than the model — so the bridge is
directionally right and, if anything, thin. The task's "RA bridge over-commits CC and crowds out
peakers" hypothesis is **not** supported; CC over-dispatch is locational substitution, not bridge
forcing.

---

## 4. Import base/shape — the secondary (volume) lever

Actual CAISO net imports are strongly shaped — overnight **5.2–6.1 GW**, midday **0.7–1.8 GW**,
evening **4.0–4.5 GW** — but the model's firm base is **3.4 GW flat**. The revealed
contracted/self-scheduled overnight base is ~5–6 GW (DMM-grounded), so the model is **~1.9–2.7 GW
short overnight** and backfills with domestic CC. This is a genuine, rule-11/14 structural gap
(prefer the measured firm-block volumes), but it drives **volume/shape** (CC overnight backfill),
not the price tail. It compounds — it does not replace — the locational fix.

---

## 5. Ranked structural plan (topology → import → TTC → offer curves)

**Tier 1 — Topology (the dominant lever).**

1. **Split SP15 into its local capacity areas.** Minimum viable: SP15 → {`LA_BASIN`
   (SCE LA-basin + Big-Creek/Ventura LCR), `SDGE` (SDG&E / Path-44 pocket), `SP15_rest`}, each with
   (a) measured TAC load shares (SCE 44.3 % / SDGE 9.2 % of component-TAC already known; needs the
   LA-basin sub-share of SCE), (b) a **local import limit** into each pocket from the published
   CAISO Local Capacity Technical (LCT) study LCR/effective-limit (or OASIS nomogram), (c) Path 44
   as a first-class link. This lets a local energy balance call LA-basin peakers, form the real
   SP15 congestion premium ($117–127), and — critically — **enables deleting `ct_netload_drag`**
   (rule 12: the drag is the scaffold for exactly this signal). *Pre-registered A/B (vs caiso-65,
   both temp-derate on, all 3 years):* SP15/LA mean LMP → toward $117–127; CT_PEAKER dispatch →
   toward 3–5 TWh; CC_REGULAR ↓; C8 drag-forcing retired; register main + zero-forcing ablation
   twin as **probes**; score leave-one-year-out before proposing promotion. This is a build (new
   zones, crosswalk, fleet zone-assignment, local limits) and likely needs an **authorized LCT/LCR
   data intake** — scope it first.

2. **Promote the two WECC corridors (`WECC_PNW`/`WECC_DSW`) to first-class** (already half-done via
   `caiso_per_hub_intertie`). Low marginal risk; clean topology; do alongside Tier 1.

**Tier 2 — Import representation (volume/base).**

3. **Enlarge & shape the firm/contracted import base** from 3.4 GW flat to the measured ~5–6 GW
   overnight/evening shape (DMM RA-import + EIM transfer + CARB specified-source blocks). Reduces
   overnight CC backfill (C1/C2/C5a volume). Rule-11/14 measured-input; **do not** re-tune to the
   residual.

**Tier 3 — TTC provenance (verify; do *after* the split so effects are observable).**

4. **Re-ground Path 15/26/66/46 against CAISO OASIS branch-group ATC / nomogram limits**; enable
   the already-coded asymmetric Path-26 ratings (N→S 4,000 / S→N 3,000). Rule 11: keep the measured
   value even if the fit worsens, then chase the root cause. These barely bind under the copperplate
   but will matter once the SP15 split creates real intra-CAISO N–S stress.

**Tier 4 — Offer-curve / commitment posture (only after structure).**

5. Belly-gas commitment grounding (RA-bridge, G-61) and level calibration — last, once Tier 1–2
   are in. Never judged by MAE movement alone (rule 1).

**Explicitly NOT fixes** (evidence-backed dead-ends): raising the corridor p95 percentile (envelope
not binding in peaks); re-tuning temp-derate to kill the 507 h (the 507 h is a copperplate symptom,
temp-derate stays on per owner and is not the cause); pinning imports or peakers to actuals (rule
11).

---

## 6. Why no solve was launched in this pass

The highest-value change (SP15 split) is a multi-step build requiring an authorized local-capacity
data intake, not a one-line probe; and the instrumentation above shows the *cheap* prototypes
(corridor percentile, temp-derate re-tune) would not move the core failure. Per rule 1 this pass
delivers the diagnosis that redirects effort and a pre-registered plan; the SP15-split prototype is
the recommended first build, run across all three train years with an ablation twin and registered
as a probe per rule 16.
