# FINDING — SPP-51b **session B**: an INDEPENDENT second run of the same charter. Same refusal, different axis — the C3a residual is a **ROTATION** on the load axis, and the model's own base-cost merit order already reproduces the measured mid-load price. **The primary lane's object naming SUPERSEDES this one; the two are complementary, not competing.** ZERO LP.

> **READ THIS FIRST — a lane collision, disclosed rather than papered over.**
> The desk issued the **SPP-51b charter to two sessions**, which ran it independently and
> concurrently without knowledge of each other. The other session (Opus 5, branch
> `claude/spp-c3a-c3b-price-1i4bgi`, PR #5679) **landed first** and its record is the canonical
> `docs/handoffs/FINDING-spp-51b-2026-09-09.md`. This document is the second session's, renamed to
> `-session-b` (the precedent is `FINDING-spp-14-2026-09-06-session-b.md`); it does not overwrite
> or contest the primary record.
>
> **What the primary lane established, and this lane defers to:** the C3a residual is a **missing
> BOTTOM tail** — the market prints **992 / 1,172 / 1,018** hours below \$0 per year and the model
> prints **4 / 7 / 0**; those hours alone carry **109 % / 222 % / 192 %** of the whole load-weighted
> C3a error. The named object is the **flat wind gross-up rule**, which spreads SPP's measured
> curtailment energy uniformly across 8,760 hours instead of onto the hours it actually occurred, so
> the LP has nothing to curtail and cannot go long. **That naming is sharper than this lane's and
> supersedes it.**
>
> **What this lane adds that the primary record does not carry**, and why it is worth keeping:
> (1) the decomposition on the **system-load axis** rather than the price-sign axis, which shows the
> residual is a rotation (+26 to +40 % in percentiles 10–75, −2 to −30 % above the 90th) and that the
> steepening deficit **widened** with the SPP-49/48 repairs; (2) the **base-cost merit-order
> identity** — the model's own arrays, cleared on merit at its own thermal residual, reproduce the
> measured mid-load price to **+1.4 / +6.8 / −2.1 %** while the LP's dual sits **\$5.61–6.45 above**
> — which is the same defect seen from the cost side and is the most direct evidence that the offer
> curve is not the surface at fault; (3) the **SPP-49 R-5 Permian arithmetic ceiling**, a third
> independent refusal of the fuel channel; (4) the **P1 startup-markup attribution**.
>
> **Where this lane was less right:** §0.5 below routes an "unattributed remainder" of the mid-load
> wedge and names the zonal split as its leading candidate. On the primary lane's evidence that is
> **probably wrong** — the remainder is most likely the wind-allocation defect itself, since the LP
> is running 10.3–11.5 GW of thermal in exactly the hours the market was curtailing wind. **R-1
> below should be read as subordinate to the primary lane's §5 routing, not beside it.**

---

## 0. Owner report

### 0.1 The one-line result

**The +12 to +15 % C3a miss is not a level residual at all.** Decomposed against system load it is
**+26 to +40 % in load percentiles 10–75** and **−2 to −30 % above the 90th percentile**, in every
year. The load-weighted mean reads "uniformly ~13 % rich" only because the middle carries the
weight. **The available levers — a fuel level, a band multiplier — are LEVEL levers, and the
residual reverses sign across load.** Neither can fix it, and phase 0 says so with numbers rather
than with a solve.

### 0.2 Phase 0.1 — the decomposition (the table the charter asked for first)

Each run's hourly ISO price recovered from its **own** committed payload (`lmpDeltaHr`, validated
against keeper-3's committed sidecar to the int16 quantization floor: `max|Δ| 0.500`,
`mean|Δ| 0.249`). Load-weighted, against SPP's own hourly RT LMP.

| load pct | hrs (2024) | **2023 err** | **2024 err** | **2025 err** |
|---|---:|---:|---:|---:|
| 0–10 | 874 | +8.5 % | +3.3 % | +8.6 % |
| **10–25** | 1,312 | **+27.8 %** | **+37.0 %** | **+26.2 %** |
| **25–50** | 2,187 | **+33.6 %** | **+39.5 %** | **+35.4 %** |
| **50–75** | 2,188 | **+27.3 %** | **+31.3 %** | **+15.1 %** |
| 75–90 | 1,312 | +7.3 % | −0.1 % | +13.1 % |
| 90–95 | 437 | −1.8 % | **−30.0 %** | −8.3 % |
| 95–98 | 263 | −5.9 % | −11.4 % | −9.5 % |
| 98–100 | 175 | **−24.3 %** | −11.5 % | −14.4 % |
| **LW mean (C3a)** | | **+15.05 %** | **+12.06 %** | **+14.21 %** |

**The rotation deficit got WORSE with the repairs, not better** — reported against interest. The
steepening ratio `MHR(>95 pct)/MHR(25–75 pct)` over SPP's own KS+OK delivered gas:

| | measured | keeper-3 | **SPP-50** |
|---|---|---|---|
| 2023 | 2.0816 | 1.3824 | **1.3611** |
| 2024 | 1.8949 | 1.3298 | **1.2450** |
| 2025 | 1.6765 | 1.2528 | **1.1972** |

### 0.3 Phase 0.1 — WHO is marginal in the rich hours, and what their cost is made of

Cap-weighted over every fleet row within ±$0.25 of the run's own clearing price — the merit-order
lane's own instrument, on the repaired surface (2024 shown; 2023/2025 in §2):

| load pct | model $ | actual $ | marginal physical HR | marginal fuel $/MMBtu | marginal classes (available-MW share) |
|---|---:|---:|---:|---:|---|
| 25–50 | 24.84 | 17.81 | 9.93 | 2.118 | COAL 36 %, CC_REGULAR 26 %, CT_PEAKER 25 %, ST_GAS 12 % |
| 50–75 | 29.12 | 22.18 | 10.09 | 2.276 | COAL 35 %, CT_PEAKER 26 %, CC_REGULAR 23 %, ST_GAS 15 % |
| ≥95 | 33.71 | 38.07 | 11.37 | 2.354 | ST_GAS 38–45 %, CT_PEAKER 26–31 %, COAL 25 % |

**The market's implied heat rate at mid load is 6.81 / 6.97 / 5.54** (actual price over SPP's own
delivered gas) **against the model's marginal physical heat rate of 9.66 / 10.01 / 9.36.** At the
top the signs reverse: market 14.16 / 13.20 / 9.28 against model 11.86 / 11.37 / 11.06.

**And the merit-order lane's structural reason SURVIVES the input repair**, which is the finding
that decides the cell. Its refusal rested on *"there is no regime to separate — CT_PEAKER is the
marginal class in 24–27 % of SPP's MEDIAN-load hours"*. On the repaired surface CT_PEAKER is
**20–23 % (2023) / 24–26 % (2024) / 16–18 % (2025)** of the mid-load near-price MW. Reduced in
2025, **not segregated** in any year.

### 0.4 Phase 0.2 — the fuel leg, tested against the record: **(A) REFUSED**

| test | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| model's marginal **gas** rows vs SPP's published state delivered reference (`N3045KS3`/`N3045OK3` ÷ 1.036), mid load | **−9.5 %** | **−14.0 %** | **−29.0 %** | already **BELOW** the reference |
| fuel multiplier that would close the **mid** gap alone | ×0.7375 | ×0.7520 | ×0.8265 | marginal gas → $2.02 / $1.86 / $2.64 against a $3.03 / $2.88 / $4.50 reference |
| fuel multiplier that would close the **top** gap alone | **×1.2054** | **×1.2779** | **×1.1703** | **opposite sign, same year** |
| SPP-49 **R-5 Permian cohort** (Elk 58835, Mustang 56326/55065, Jones 3482, Harrington 6193) share of the mid-load near-price MW | 13.57 % | 17.68 % | 11.58 % | |
| **arithmetic ceiling** — mid-load $/MWh removable if that cohort's ENTIRE fuel bill went to **zero** | **$3.17** | **$3.89** | **$3.04** | against a gap of **$6.21 / $6.98 / $5.93** |

**Three independent kills.** The model's marginal gas is already cheaper than the published state
blend, so a basis refinement would have to push it 35–40 % below a reference it already undercuts.
The residual demands opposite-signed fuel moves in the same year, which no single fuel level
supplies. And SPP-49 R-5's own cohort cannot close the mid-load gap even at the physically absurd
limit of free fuel — it reaches **at most 51–56 %** of it.

**R-5 is NOT killed by this — it is un-elected as the cause of this residual.** A Waha-referenced
screen for the Permian cohort remains a legitimate rule-14 refinement worth its own lane; it is
simply not what makes SPP's middle expensive, and it moves the top band the wrong way.

### 0.5 Phase 0.1b — the decisive structural measurement: **the offer curve is not where the error is**

The model's **own** base-cost arrays, cleared by pure merit order at the model's **own** hourly
thermal residual load, against what the market actually cleared at:

| mid load (25–75 pct) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| thermal residual, mean MW | 14,209 | 14,910 | 16,332 |
| **merit order on the model's own `mc_base`** | **$20.89** | **$21.46** | **$24.37** |
| **ACTUAL RT price** | **$20.60** | **$20.09** | **$24.90** |
| deviation | **+1.4 %** | **+6.8 %** | **−2.1 %** |
| **the LP's own P1 dual** | **$26.81** | **$27.07** | **$30.82** |
| **the wedge** | **+$5.92** | **+$5.61** | **+$6.45** |

**The cost surface is already right where the residual sits.** The +26 to +28 % over-pricing is
introduced **between the cost arrays and the LP's dual**, not in the arrays a band multiplier would
scale. Attribution of the wedge, each measured rather than asserted:

| candidate | measured | verdict |
|---|---|---|
| forced min-gen displacement | headroom clearing $20.89 / $21.46 / $24.37 vs gross $21.04 / $21.52 / $24.44; forced block 2,079 / 1,870 / 1,913 MW (11.7–14.6 % of the residual) | **−$0.06 to −$0.15** — not it |
| zonal congestion (2 zones, 3,400 MW seam) | keeper-3 mid-load mean spread **$0.91 / $1.06 / $1.10**, binding >$0.5 in 834–902 of ~4,380 hours | ~**$1** — not it |
| **P1 startup amortization** (`compute_monthly_markup`, `mc_bid = mc_base + markup`) | 98–100 eligible rows / **11,148–11,163 MW** — **coal 6,265 MW** at up to $100/MW, CC 3,601, CT 1,282–1,296 (`gas_st_startup_cost=False`, so ST_GAS is exempt). Re-clearing the stack with the markup, by average run length: **2 h → +$3.00 / +$3.67 / +$5.78; 6 h → +$2.46 / +$2.53 / +$3.92; 12 h → +$1.67 / +$1.63 / +$2.29; 24 h → +$0.99 / +$0.96 / +$1.23** | **+$0.96 to +$5.78** — the largest identified component, **but not the whole wedge at any run length** |
| **unattributed remainder** | 2023 **$2.92–4.93** · 2024 **$1.94–4.65** · 2025 **$0.67–5.22** | open — §5 R-1 |

And the LP is carrying this while **5,661 MW of capacity priced at or below its own clearing price
sits unused** at mid load, in **4,364 of 4,375 hours** (2024). The energy balance of the
reconstruction closes to **−20 MW** (storage/net-flow), so this is not an accounting artifact.

### 0.6 Phase 0.3 — **THE CHANNEL: (B). The band is NOT the answer, and I say so.**

**(C) is refused on two independent grounds, neither of them a residual.**

**First — the lever's own measured transfer function cannot produce the shape.** The price-family
lane measured the LP's actual response to a band quadruple as **flat in load**: arm/control price
ratio **0.9070–0.9151 across the entire load range, a 0.81 pp spread**. Applying that lever at the
strength that would zero the C3a mean:

| load pct | 2024 now | 2024 after ×0.8923 | 2025 now | 2025 after ×0.8756 |
|---|---:|---:|---:|---:|
| 10–25 | +37.0 % | **+22.3 %** | +26.2 % | **+10.5 %** |
| 25–50 | +39.5 % | **+24.5 %** | +35.4 % | **+18.6 %** |
| 90–95 | −30.0 % | **−37.6 %** | −8.3 % | **−19.7 %** |
| 98–100 | −11.5 % | **−21.0 %** | −14.4 % | **−25.0 %** |

The middle stays **+10 to +25 %** too dear and the top goes to **−20 to −38 %**. C3a's *mean* would
read zero while every band is wrong — the criterion satisfied by redistributing the error, which is
precisely what rule 1's condition (c) exists to refuse.

**Second, and decisively — the offer curve is not where the error is (§0.5).** The base-cost stack
already reproduces the measured mid-load price to +1.4 / +6.8 / −2.1 %. Scaling it down to offset a
wedge introduced elsewhere in the LP is the compensating error rule 14 `[R-ACCURATE]` names by
sentence — *"do not bury the error back inside an inaccurate input"* — and the mechanism rule 1
`[R-STRUCT]` forbids reaching a number through. **SPP-46 refused this same channel on an input
census; this lane refuses it on a COST-SURFACE census, and the two refusals are the same discipline
applied to the repaired surface.**

**The `R` verdict therefore STANDS, and the new evidence STRENGTHENS it.** The charter's re-opening
argument was sound and worth testing — the input defect that carried the old refusal is genuinely
gone. What the repaired surface shows is that the case against the band is now *stronger*, because
the cost arrays it would scale are demonstrably correct.

**(B), named.** *The mid-load wedge between SPP's own base-cost merit order and its own P1 clearing
dual — $5.61 to $6.45/MWh, of which the coal-dominated startup amortization accounts for $0.96–5.78
(by average run length) and congestion and min-gen for under $1 combined.* The top-of-stack half is a **separate,
already-adjudicated object**: SPP-55 measured scarcity and reserve shortage **INERT** on this
dispatch (the reserve row can bind in 0 / 1 / 0 hours of 8,760), so the −12 to −15 % top-band miss
and C3c are not this lane's and not the band's.

### 0.7 C3a and C3b at full magnitude — **REPORTED, NOT GATED ON**

Nothing was solved, so these are SPP-50's registered values, unchanged by this lane:
**C3a +15.05 / +12.06 / +14.21 %** (FAIL, all three years);
**C3b duration NRMSE 0.250 / 0.244 / 0.253** (FAIL, all three years);
**C3c 0 / 3 / 2 hours >$200** against 42 / 59 / 68 measured.
The determination is SPP-50's **NOT-YET** and keeper-3's **NOT-YET**; **neither moves**, because
this lane changed nothing.

**No gate in this lane was read against C3a or C3b.** Gating a channel on the criterion it targets
is the fitted-mechanism selection rule 1 forbids; every kill above is structural — a transfer
function, an arithmetic ceiling, a cost-surface identity — and each is stated with the number that
decided it.

### 0.8 Rule 31 `[R-RETAIN]` and the promotion question — asked in session, as r#15 clause 8 requires

**There is nothing to promote and nothing to retain.** No LP was spent, no bundle was written, no
run was registered, `keepers/SPP.json` is untouched and keeper-3 is not pruned. Rule 31 has no
object in this lane and no `.gitignore` entry is owed — the SPP-46 / SPP-55 / merit-order posture.

**The promotion question that IS open is not this lane's to answer and is not re-opened here:**
owner ruling P15 declined SPP-50's promotion, and SPP-50's 119 MB bundle did not survive its
session. Reproducing it costs **~13 minutes of LP** (its own §9 estimate) plus registration. This
lane neither asks for that nor spends it.

---

## 1. What ran, in order

| step | what | LP | result |
|---|---|---|---|
| 1 | payload price recovery for both registered runs, validated against keeper-3's own sidecar | none | §0.2, PRECOMMIT §2.3 |
| 2 | LP input arrays rebuilt at HEAD on keeper-3's recipe, 2023–2025 (`run_year(fleet_only=True)`) | none | PRECOMMIT §2.2 — the surface IS SPP-50's, proven three ways |
| 3 | marginal-class + cost decomposition by load band | none | §0.3, §2 |
| 4 | the fuel leg against the published state reference; the R-5 cohort's arithmetic ceiling | none | §0.4 |
| 5 | the model's own merit order at its own thermal residual; the wedge and its attribution | none | §0.5 |
| 6 | the band channel's measured transfer function applied at C3a-zeroing strength | none | §0.6 |

Rule 12 `[R-PARALLEL]`: no solve was launched, so the ≤2-concurrent-SPP-solve cap was never
approached and SPP-DESK had nothing to be asked about.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only; no holdout year was solved, scored or registered.

## 2. The full marginal-class tables (2023 and 2025)

**2023**

| load pct | model $ | actual $ | err | marg HR | marg fuel | marginal classes (available-MW share) |
|---|---:|---:|---:|---:|---:|---|
| 10–25 | 24.89 | 19.47 | +27.8 % | 9.67 | 2.251 | COAL 35 %, CC_REGULAR 35 %, CT_PEAKER 23 %, ST_GAS 6 % |
| 25–50 | 26.02 | 19.48 | +33.6 % | 9.58 | 2.376 | CC_REGULAR 36 %, COAL 35 %, CT_PEAKER 20 %, ST_GAS 9 % |
| 50–75 | 27.53 | 21.64 | +27.3 % | 9.74 | 2.462 | COAL 34 %, CC_REGULAR 33 %, CT_PEAKER 21 %, ST_GAS 11 % |
| 95–98 | 35.54 | 37.75 | −5.9 % | 11.72 | 2.685 | ST_GAS 53 %, CT_PEAKER 31 %, COAL 10 % |
| 98–100 | 37.80 | 49.92 | −24.3 % | 12.07 | 2.801 | ST_GAS 67 %, CT_PEAKER 29 %, COAL 2 % |

**2025**

| load pct | model $ | actual $ | err | marg HR | marg fuel | marginal classes (available-MW share) |
|---|---:|---:|---:|---:|---:|---|
| 10–25 | 28.57 | 22.65 | +26.2 % | 9.40 | 2.671 | CC_REGULAR 40 %, COAL 39 %, CT_PEAKER 16 %, ST_GAS 5 % |
| 25–50 | 30.32 | 22.39 | +35.4 % | 9.42 | 2.789 | CC_REGULAR 42 %, COAL 33 %, CT_PEAKER 18 %, ST_GAS 6 % |
| 50–75 | 31.27 | 27.17 | +15.1 % | 9.30 | 2.818 | CC_REGULAR 44 %, COAL 30 %, CT_PEAKER 16 %, ST_GAS 9 % |
| 95–98 | 36.02 | 39.81 | −9.5 % | 10.98 | 2.912 | CT_PEAKER 36 %, ST_GAS 33 %, COAL 21 % |
| 98–100 | 38.21 | 44.62 | −14.4 % | 11.19 | 2.977 | ST_GAS 46 %, CT_PEAKER 40 %, COAL 8 % |

## 3. Honest disclosures

1. **Phase 0 ran before the PRECOMMIT was written**, and PRECOMMIT §0 says so in terms. Nothing in
   this lane is a selection: no arm was declared, no multiplier derived, no criterion consulted as
   a gate, and the result is a refusal. The one condition pre-registration would have bound —
   rule 1 carve-out (c) — is never reached.
2. **The merit-order clearing in §0.5 is a POOLED reconstruction**: single stack, no zonal
   separation, no ramping, no storage co-optimization, and `mc_base` rather than `mc_bid`. It is
   therefore a **lower** bound on the LP's dual, and §0.5's own attribution table treats it as one
   — which is why the markup is measured separately and the remainder is reported as
   **unattributed** rather than claimed. What the leg establishes is narrow and holds regardless of
   the remainder: **the base-cost arrays reproduce the measured mid-load price**, so the surface a
   band multiplier would scale is not the surface carrying the error.
3. **The startup-markup figure is a BOUND, not the realised markup.** `compute_monthly_markup`
   needs the P0 dispatch, which no committed artifact carries, so it is reported across a range of
   average run lengths (2–24 h) rather than at one value, and the bracket is wide — it does not close the wedge at any run
   length in any year, but at 2 h in 2025 it reaches $5.78 of a $6.45 wedge. The eligible set and
   each row's startup cost are exact (read through `commitment._startup_cost` on the rebuilt fleet).
4. **A first pass under-counted the markup** by reading a `Generator.startup_cost` attribute that
   does not exist on this path and reporting $0.00/MW on every row, which would have made the
   markup look irrelevant. Corrected by routing through `_startup_cost`, which returns
   `startup_cost_per_mw` for a CAMPD bin — and the correction **changed the answer**: coal is
   6,265 of the 11,148 eligible MW and the markup went from "immaterial" to the wedge's largest
   identified component. Recorded rather than quietly fixed.
5. **The zonal-spread bound is keeper-3's**, not SPP-50's, and is labelled as such wherever it
   appears. SPP-50 wrote no `hourly/` sidecar, so its own spread is unmeasurable; the bound is used
   only to establish an order of magnitude (~$1 against a ~$6 wedge).
6. **The 2024 90–95 pct cell (−30.0 %)** sits beside a 95–98 cell of −11.4 %, i.e. the measured
   surface is not monotone there. It is reported as measured; nothing in the lane's conclusion
   turns on that one cell.
7. **`hydrate_data.py --profile spp` was a no-op** — this container carries a full clone, so every
   blob was already local.

## 4. The mechanism-matrix cell

`offer_curve_by_group` stays **`R`** for SPP. This lane appends its evidence to the existing cell
in `docs/codebase-site/data/mechanism-matrix/SPP.js` (rule 28(b): the session that tests a
mechanism updates its own ISO's cell in the same session, rejections included). No other cell
moves; no `ScenarioConfig` field was added, so rule 28(c) is not engaged. The keeper/gates stamp is
**untouched** (r#11 collision rule 2 — this lane promotes nothing).

## 5. Routed (not absorbed) — cite as `SPP-51b R-nn`

| # | item | owner | what it needs |
|---|---|---|---|
| **R-1** | **SUBORDINATE TO THE PRIMARY LANE'S §5 — the mid-load wedge between SPP's base-cost merit order and its own P1 dual** — $5.61–6.45/MWh, of which the coal-dominated startup amortization is $0.96–5.78 (bracketed by average run length) and congestion + min-gen under $1. The remainder is **unattributed by a pooled zero-LP reconstruction** and is most likely the PRIMARY LANE'S OBJECT (the flat wind gross-up), not the zonal split this lane first suspected: the LP runs 10.3-11.5 GW of thermal in exactly the hours the market was curtailing wind. A successor should test that attribution before anything else | SPP-DESK | a lane with the keeper's own `hourly/` sidecars, or one P0/P1 pair whose markup array is persisted |
| **R-2** | **The coal startup amortization is the largest identified single component** — 6,265 MW of coal bins at up to $100/MW carrying a markup into the *clearing price*, in an ISO that recovers starts through make-whole uplift. `coal_warm_committed` is **`False`** in SPP's recipe and is the registered gate that exempts a must-run coal bin from it (34 SPP rows carry `must_run_pct > 0`). Its own docstring records the ERCOT inversion it was written for. **Untested for SPP** — a rule-19 `[R-ONE-MECH]` question about which mechanism owns coal's committed band, not a band multiplier | SPP-DESK | its own PRECOMMIT; screen year by the mechanism's own footprint (rule 29) |
| **R-3** | **The rotation deficit WIDENED with the repairs** — steepening 1.3824/1.3298/1.2528 → 1.3611/1.2450/1.1972 against measured 2.0816/1.8949/1.6765. Reported against interest, and it bears on P15: SPP-50 is the more structurally faithful run **and** its stack is flatter. Both facts are true and the desk should hold them together | SPP-DESK | note only |
| **R-4** | **SPP-49 R-5 (Waha / Permian reference) is UN-ELECTED as this residual's cause, not killed.** Its cohort reaches at most 51–56 % of the mid-load gap at the absurd limit of free fuel, and moves the top band the wrong way. It remains a legitimate rule-14 refinement | SPP-DESK / ERCOT-DESK | unchanged from SPP-49 R-5 |
| **R-5** | **The top-of-stack half (−12 to −15 %, and C3c) is SPP-55's adjudicated object** — scarcity and reserve shortage measured **INERT** on this dispatch. This lane confirms the two halves are separate objects and that no offer-curve lever touches either | SPP-DESK | note only |

---

## Log entry

```
## spp-51b — 2026-09-09 — the C3a residual is a ROTATION, not a level; the offer curve is NOT where the error is; channels (A) and (C) both REFUSED at phase 0; ZERO LP
Charter (desk r#15) re-opened the offer_curve_by_group cell on NEW EVIDENCE -- the input defect that
carried SPP-46's refusal is repaired (SPP-49, owner ruling P19) and SPP-50 left a price residual
standing in the open. The re-opening argument was sound and was tested; the answer is that the
repaired surface makes the case AGAINST the band STRONGER. DECOMPOSITION (zero LP, each run's hourly
ISO price recovered from its OWN committed payload via lmpDeltaHr, validated against keeper-3's
committed sidecar to the int16 floor: max|d| 0.500, mean|d| 0.249): the +15.05/+12.06/+14.21 % C3a
miss is NOT uniform -- it is +26 to +40 % in load percentiles 10-75 and -2 to -30 % above the 90th,
in every year, and the steepening ratio WIDENED with the repairs (keeper-3 1.3824/1.3298/1.2528 ->
SPP-50 1.3611/1.2450/1.1972 against measured 2.0816/1.8949/1.6765). (A) FUEL-BASIS REFUSED on three
independent measurements: the model's marginal gas rows already price 9.5/14.0/29.0 % BELOW SPP's
published state delivered reference; the mid gap needs fuel x0.74-0.83 while the top needs x1.17-1.28
in the SAME year; and the SPP-49 R-5 Permian cohort's ARITHMETIC CEILING -- its entire fuel bill to
zero -- closes $3.17/$3.89/$3.04 of a $6.21/$6.98/$5.93 gap (51-56 %). R-5 is un-elected as the cause,
not killed. (C) CARVE-OUT BAND REFUSED on two grounds, neither a residual: the lever's own measured
transfer function is FLAT in load (price-family lane, 0.9070-0.9151, 0.81 pp spread), so at the
strength that zeroes the C3a mean the middle stays +10 to +25 % dear and the top goes to -20 to -38 %;
and DECISIVELY, the offer curve is not where the error is -- the model's OWN base-cost arrays, cleared
by pure merit order at its OWN hourly thermal residual, give $20.89/$21.46/$24.37 against measured
$20.60/$20.09/$24.90 (+1.4/+6.8/-2.1 %), while its P1 dual sits $5.92/$5.61/$6.45 ABOVE that, with
5,661 MW priced at or below its own clearing price unused in 4,364 of 4,375 mid-load hours (2024).
Scaling a correct cost surface to offset a wedge introduced elsewhere is the compensating error rule
14 forbids by sentence. The merit-order lane's structural reason SURVIVES the repair: CT_PEAKER is
still 16-26 % of the mid-load near-price MW (24-27 % pre-repair) -- reduced, not segregated. WEDGE
ATTRIBUTION, each measured: min-gen -$0.06 to -$0.15 (forced block 11.7-14.6 % of the residual); zonal
congestion ~$1 (keeper-3 mid-load spread $0.91/$1.06/$1.10); P1 STARTUP AMORTIZATION +$0.96 to +$5.78
by average run length (98-100 eligible rows / ~11,150 MW, COAL 6,265 MW at up to $100/MW, CC 3,601,
CT ~1,290; ST_GAS exempt at gas_st_startup_cost=False) -- the largest identified component but not
the whole wedge at any run length; the remainder is UNATTRIBUTED by a pooled reconstruction and
routed as R-1. offer_curve_by_group STAYS R. C3a/C3b
reported at full magnitude and NOT GATED ON; no gate in this lane was read against either. NOTHING
SOLVED, no bundle, nothing registered, keepers/SPP.json untouched, keeper-3 not pruned, no
ScenarioConfig field or constant added; rule 31 has no object. Phase 0 ran before the PRECOMMIT was
written and PRECOMMIT §0 discloses it -- nothing here is a selection.
FINDING: docs/handoffs/FINDING-spp-51b-2026-09-09.md
```
