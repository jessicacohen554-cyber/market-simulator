# FINDING — PJM's C3a-2025 residual is a monotone price-DISPERSION compression, not a level miss and not a discrete tail truncation (pjm-120, 2026-07-25)

> **STATUS — COMPLETE (2026-07-25).** All sections measured. **No keeper change
> is proposed and no lever is promoted**: this session diagnoses, refutes two
> candidate causes, and hands off. The keeper stays
> `2026-07-24-pjm-119-overlay-restore`.
>
> **Self-correction.** An earlier draft of this finding (commit `6b3dc33`)
> argued the residual was concentrated in ~14 extreme hours the model
> structurally cannot reach. The 2025 replay's own stratified decomposition
> (§3) **partly refutes that**: the >$376 stratum is only 31 % of the negative
> side, smaller than the 50–100 $/MWh band. The refutation is recorded here
> rather than quietly rewritten, and the measured decomposition governs.

**Charter:** close PJM's last open gate — C3a mean LMP 2025, `−10.7 %` against a
`±10 %` band, the single NOT-YET criterion on keeper
`2026-07-24-pjm-119-overlay-restore` (9/10 scored PASS).

**Verdict — a clean split, both halves measured:**

1. The handoff's strongest named lead — *"2025 gas is above the anchor, so the
   fixed margin compresses offers in exactly the year that fails"* — is
   **REFUTED**. In the months that actually miss, delivered gas is *below* the
   anchor, so `gas_offer_net_revenue_margin` **raises** those offers. It
   compresses only in the months that already score well.
2. The residual is a **monotone compression of the price distribution**, not a
   level offset and not a discrete ceiling. Measured on the keeper's own 2025
   replay: the model runs **too HIGH** in the 6,771 cheapest hours (+$4.01
   load-weighted) and **too LOW** in every expensive stratum (−$8.90), with
   the undershoot growing steadily with the actual price — −$17.5/h at
   50–100, −$64.8 at 100–200, −$166 at 200–376, −$635 above $376.
3. Therefore **no level knob can fix this.** Anything that lifts the whole
   curve makes the 6,771 cheap hours (77 % of hours) worse. What is missing is
   *dispersion*: the model's supply is too abundant and too cheap in tight
   hours and too expensive in slack ones.
4. Reserve-product coverage (§5) is a real structural gap but is **not** the
   operative cause, and this is now **measured, not inferred**: the keeper's
   own reserve dual is nonzero in only **22 of 8,759 hours** and reaches
   **$300 in zero hours** — it never touches even the second ORDC step, let
   alone the $850 penalty. A second demand curve over a balance with ~10×
   slack cannot bind either, so `pjm_reserve_pergen_sync` cannot close C3a
   (§6). This re-derives the owner's 2026-07-11 hold on fresh evidence.

---

## 1. The gap is small and the arithmetic is unforgiving

C3a gates on the load-weighted RT actual (`rt_lw`, `calibration_verdict.py`
:1112) — 2025 `rt_lw = $45.80/MWh`. At `−10.7 %` the model is `≈ $40.90`; the
band edge (`−10.0 %`) is `$41.22`. **The whole gate is $0.32/MWh of annual
load-weighted price.**

That matters because it sets the bar for what counts as an explanation: any
mechanism worth more than ~$0.3/MWh annually is a candidate, and any mechanism
that also moves 2023/2024 by that much breaks a passing year.

## 2. The anchor/margin lead is refuted by the delivered-gas series

The handoff proposed that 2025 fails because gas ($3.52 HH) sits above the
`gas_offer_margin_anchor` ($3.3483), compressing offers via
`apply_gas_offer_margin`: `mc += markup_hr × (anchor − fuel)`.

The sign of that adjustment is set by the **delivered** series
(`data.fuel.trajectories._gas_series`, the keeper's own
`--gas-monthly-actuals` + daily-shape overlay), not by the annual Henry Hub
scalar. Measured, PJM 2025 monthly delivered $/MMBtu:

| Jan | Feb | Mar | Apr | May | **Jun** | **Jul** | Aug | **Sep** | **Oct** | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 6.79 | 4.99 | 4.07 | 4.03 | 3.41 | **2.99** | **3.26** | 2.89 | **2.66** | **3.12** | 3.94 | 5.09 |

Anchor = **3.3483**. Every month of the failing summer/autumn block
(Jun −20.1, Jul −9.0, Aug −4.6, Sep −8.5, Oct −6.7 $/MWh model−actual) is
**below** the anchor, so `anchor − fuel > 0` and the mechanism **lifts** those
offers. The months where it genuinely compresses — Jan 6.79, Feb 4.99,
Dec 5.09 — are the months that score best (Jan −0.9, Feb −2.0).

**The mechanism's sign is opposite to the residual it was proposed to explain.**
Lowering the anchor (e.g. to a pooled p50, $2.9449) would *reduce* the summer
lift and make 2025 worse. This lead is closed; `gas_offer_net_revenue_margin`
and its anchor are exonerated as the C3a-2025 driver, independently of the
owner's 2026-07-24 decision to keep the mechanism.

> **Incidental doc/code inconsistency, flagged not fixed.** The pjm-117 log
> entry and the pjm-119 handoff both describe the anchor as *"a measured p50 of
> the keeper's own delivered-gas overlay 2023-25"*. It is not a p50. Both
> `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO` and
> `scripts/data/derive_gas_offer_margin_anchor.py` define it as the **mean of
> the annual delivered means** — and the registered 3.3483 reproduces exactly
> as `mean(3.2551, 2.8556, 3.9341)`, whereas the pooled hourly p50 is 2.9449.
> The code is self-consistent and correctly cited; only the prose is wrong.
> Left for `/sync-docs` rather than edited here, since rule 23 makes any touch
> of a frozen derive a data-provenance event.

## 3. Where the residual actually lives — the measured decomposition

The keeper recipe was replayed byte-faithfully for 2025 with the overlays live
(`results/probes/pjm120_c3a_2025`; the run logged
`measured EAST interface cut on 2 link(s) … mean 8149 MW`, so this reproduces
the keeper, not a degraded variant). Model $41.19 vs actual $46.07
load-weighted, **gap −$4.89/MWh**. Decomposed by ACTUAL-price stratum, each
row's contribution to that gap:

| actual stratum | hours | model $/MWh | actual $/MWh | **contribution to gap** |
|---|---|---|---|---|
| 0–25 | 1,922 | 30.8 | 20.4 | **+1.965** |
| 25–50 | 4,849 | 39.1 | 35.4 | **+2.045** |
| 50–100 | 1,655 | 48.5 | 66.0 | **−3.736** |
| 100–200 | 274 | 64.6 | 129.4 | **−2.499** |
| 200–376 | 45 | 86.0 | 252.5 | **−1.127** |
| > 376 | 14 | 181.2 | 815.7 | **−1.534** |

**This refutes the extreme-tail reading.** The >$376 stratum contributes
−$1.53 of a −$8.90 negative side — **31 %**, and *less* than the 50–100 band's
−$3.74. The gate is not lost in fourteen hours.

What the table actually shows is a **monotone dispersion compression**. The
model's error is a smooth, sign-flipping function of the actual price:

| actual band | model − actual, per hour |
|---|---|
| 0–25 | **+10.4** |
| 25–50 | **+3.7** |
| 50–100 | −17.5 |
| 100–200 | −64.8 |
| 200–376 | −166.5 |
| > 376 | −634.5 |

The model is **too expensive when the system is slack and too cheap when it is
tight**, monotonically, across the whole range. Its price distribution is
squeezed toward the middle: 77 % of hours (the two cheap strata) are over-priced
by a combined **+$4.01**, and the tight 23 % are under-priced by **−$8.90**.

**The operational consequence is a hard guard on any candidate fix.** A lever
that raises the price level — a higher anchor, a firmer offer curve, a scarcity
adder — necessarily worsens the 6,771 cheap hours, which are already $4–10/MWh
too high. Only a mechanism that increases *dispersion* (cheaper when slack,
dearer when tight) can close C3a-2025 without breaking the rest of the year, and
2023 (+4.7 %, already over) makes that constraint binding across the window too.

Note also that the model never approaches its own structural ceiling: in the
single worst hour the system price reaches $375.7 (any-zone $675.3) against an
actual $1,722, while §5 shows the published mechanism could in principle carry
it to ~$994–$1,844. The ceiling is not what binds — §6.

## 4. Those hours are a real, published pricing mechanism — measured

They are not statistical noise. PJM's own RT reserve settlement
(`data/raw/PJM-AS/reserve_market_results_2025.parquet`) shows a deep
simultaneous shortage across **all three** nested products at 2025-06-24
18:50 EPT:

| product | requirement (MW) | cleared (MW) | shortfall | clearing price |
|---|---|---|---|---|
| Synchronized (SR) | 2,515 | 1,619 | **−896** | **$2,550** = 3 × $850 |
| Primary (PR) | 3,678 | 1,621 | **−2,057** | **$1,700** = 2 × $850 |
| 30-Minute (Secondary) | 3,678 | 1,831 | **−1,847** | **$850** = 1 × $850 |
| Regulation | 1,000 | 993 | −7 | $4,206 |

This is exactly the cascade documented in
`docs/multi-iso/pjm-reserve-curve-source.md`
(`SRMCP = SP_SR + SP_PR + SP_30`, Manual 11 sec 4.4.1), with all three
demand curves pinned at their Step-1 **$850** penalty factor. The $1,722
energy LMP is that reserve scarcity rent arriving in energy through
co-optimization — PJM's post-2022 Reserve Price Formation design working as
filed.

Shortage is rare and tightly bounded, which is why it cannot be mistaken for a
level effect — PJM 2025 hours with a positive hourly-mean RTO shortfall:
**SR 12 h, PR 29 h, 30-Min 4 h**.

## 5. The top strata specifically — one of three nested products

§3 shows the extreme tail is 31 % of the negative side, not the whole story.
This section is scoped to that 31 %: why the model cannot follow the top
strata even in principle. **It is not a cap that needs raising** — every
parameter in the ceiling chain is already correct and cited:

| element | value | site |
|---|---|---|
| Hard LP ceiling (load-shed slack at ISO VOLL) | **$2,000** | `config/iso_configs.py:763`, `model/lp/costs.py:124` |
| ORDC step-1 / step-2 penalty | **$850 / $300 (+190 MW)** | `data/raw/_validation-source/pjm_ordc_curve.csv`, Manual 11 §4.3.3 |
| Reserve families built in the LP | **Primary RTO + Primary MAD only** | `model/reserves/spec.py:1680-1729` |
| Top gas offer at June-2025 gas (CT_PEAKER peak ×4.0) | **≈ $144** | `pjm_campd_marginal_hr_summary.csv`, `assembly.py:506` |
| Post-solve scarcity adder | **none for PJM** (correctly skipped under co-opt) | `runner.py:1846-1852` |

So the model's *structural* June-2025 ceiling is `$144 + $850 = $994` in an
RTO-only zone and `$144 + $1,700 = $1,844` in a MAD zone — i.e. **the
published mechanism, if it bound, could reach the observed $1,722.** Nothing
here needs a bigger number.

What is missing is **product coverage**. PJM clears three nested reserve
products; the keeper's LP carries one:

* **Primary** (RTO + MAD) — live (`pjm_reserve_pergen=true`).
* **Synchronized** (RTO + MAD) — implemented but **default-off**
  (`pjm_reserve_pergen_sync=false`).
* **30-Minute / Secondary** — **not implemented in the LP at all**
  (`PJM_RESERVE_CASCADE` / `pjm_reserve_cascade_mcp` in `results/scarcity.py`
  exist only on the validation/overlay side).

In a shortage where reality stacks 3 × $850, the keeper can inherit at most
one layer. The count of scarcity hours is therefore reproducible (C3c passes:
39 of 59 hours > $200) while their **depth** is not — and C3c counts hours, so
it never registers the miss that lands squarely in C3a.

**Scope honestly.** Closing this gap perfectly would recover at most the
−$1.53 of the >$376 stratum, which alone would take C3a-2025 from −10.6 % to
about −7.3 % — a PASS. But it would leave −$7.4 of the compression untouched
and the cheap hours still over-priced, so it would buy the gate without fixing
the price formation. On rule-1 grounds that makes it a *partial* structural
repair, not a closure of the lane.

## 6. The supply side — why no reserve family can bind (pre-registered)

§5 establishes that the keeper prices one of three nested products. That is a
real structural gap. It is **not**, on this evidence, the operative cause — and
the keeper's own solve log says why:

```
PJM PER-GEN reserve co-opt ON: 39 R columns / 2405 member units
(eligible, ramp10>0; deliverable ramp mean 38.1 GW),
2 balance families (pjm_primary, pjm_primary_mad)
```

Two facts in one line. The families are **Primary RTO + Primary MAD only**
(§5 confirmed from the run itself, not inferred). And the model carries a
**mean deliverable 10-minute ramp of 38.1 GW** against a Primary requirement
of ~3.7 GW and a Synchronized requirement of ~2.5 GW — roughly **10× slack on
the reserve balance**.

Reality at the same moment is the opposite: at 2025-06-24 18:50 PJM *cleared*
only 1,619 MW of Synchronized reserve against a 2,515 MW requirement (§4). The
model's reserve supply exceeds PJM's realised cleared reserve by more than an
order of magnitude.

A demand curve only prices when the balance binds. With ~10× headroom, no
ORDC family — Primary, Synchronized, or a future Secondary — can reach its
Step-1 penalty. **Adding products cannot fix a supply-side surplus.**

> **Pre-registered prediction, fixed before any arm was read.** The A/B arm
> `results/probes/pjm120_syncarm_2025` (keeper recipe + `--set
> pjm_reserve_pergen_sync=true`, adding the measured Synchronized RTO+MAD
> families) will be **≈ inert on C3a-2025 (|Δ| < 0.2 pp)** and will not
> materially raise the 14 hours above $376. If instead C3a moves ≥ 0.5 pp, the
> product-coverage reading of §5 is the operative cause and this section is
> wrong.

### 6.1 The A/B arm is memory-infeasible — but the dual settles it directly

The arm built correctly (**78 R columns / 4 balance families**, versus 39/2 in
the keeper — the product split is live) and cleared P0 in 561 s, then was
**OOM-killed in the P1 warm-start** (`SYNC_EXIT=137`) on this 15 GB box. That
is the documented failure mode for PJM's finer reserve tiers, not a flake:
`model/reserves/spec.py` records the same P1-warm-start OOM for the
plant-in-MAD tier at ~15.1 GB. **So the arm did not return a C3a number.**

It does not need to. The keeper's own solve **persists the reserve clearing
price** (`hourly/system_2025.parquet::reserve_price`), which tests this
section's claim directly and more strongly than the arm would have — it reads
the binding state of the balance itself rather than inferring it from a price
delta:

| model 2025 reserve dual (max across zones per hour) | value |
|---|---|
| hours with any nonzero dual | **22 of 8,759** |
| hours ≥ $300 (ORDC **Step 2**) | **0** |
| hours ≥ $850 (ORDC **Step 1**) | **0** |
| max / mean | **$210.99** / $0.151 |

At the single worst hour — h4193, 2025-06-24 18:00, where PJM printed $1,722
and cleared 896 MW short on Synchronized — the model's reserve dual is
**$210.99** and its any-zone energy price $675.3. The balance is in the
**sub-shortage opportunity-cost regime and never reaches even the $300 second
step**, anywhere, all year.

**The prediction is therefore confirmed on direct evidence**: a second ORDC
curve laid over a balance carrying ~10× slack would clear in the same
sub-shortage regime, so `pjm_reserve_pergen_sync` cannot move C3a. This also
reproduces the pjm-87 measurement ("fires in the correct opportunity-cost
regime, never crosses $300") on the *current*, east-cut-restored model — the
2026-07-11 hold was not an artifact of the degraded-overlay era.

**Conclusion.** PJM's C3a-2025 gate **cannot be closed by reserve-product
coverage.** The operative root cause is the reserve *supply* side — the
perfect-foresight, all-online dispatch carrying far more deliverable ramp than
PJM actually holds — which is the same LP-tightness class the owner identified
as G-20b (and ERCOT G-22). This **independently re-derives the owner's
2026-07-11 hold on `pjm_reserve_pergen_sync`** from a different criterion (C3a
rather than C3c) and on fresh evidence: it strengthens that decision rather
than re-opening it.

## 7. Guardrail review

* **Rule 1** — this relocates the residual onto a market-structure question
  (reserve/LP tightness), not onto a level knob, and §3 states explicitly that
  the one lever which *would* pass the gate would leave the mechanism unfixed.
  No mechanism is judged by whether it improves the fit, and nothing was
  promoted because a number moved.
* **Rule 11** — the anchor refutation *keeps* the accurate measured input and
  declines the estimate-shaped "retune the anchor" move; the anchor's basis
  question is answered by measurement, not by the residual.
* **Rule 13** — every quantity used here is a measured market input or a
  published tariff parameter with a forward analogue (reserve requirements
  regenerate from Manual 11's LSC rule; penalty factors are filed constants).
  No outcome is pinned.
* **Rule 16** — both 2025-only solves (`pjm120_c3a_2025`, `pjm120_syncarm_2025`)
  are explicitly diagnostic probes, never registerable as keepers. No dashboard
  registration is claimed for either, and the OOM'd arm is reported as a
  non-result rather than quietly dropped.
* **Rule 22** — 2023–2025 only; no holdout year touched.
* **Falsifiability** — §6's prediction was pre-registered before any arm was
  read, and §3's own decomposition refuted this finding's earlier draft. Both
  the refutation and the failed arm are recorded in place.

## 8. What this leaves for the next session

**Closed by this session — do not re-open as framed:**

* The `gas_offer_margin_anchor` / `gas_offer_net_revenue_margin` lead (§2 —
  refuted on sign, by the delivered series).
* Reserve-product coverage as the C3a lever, i.e. `pjm_reserve_pergen_sync`
  and any Secondary/30-Minute build motivated by C3a (§6 — the balance never
  binds; the dual reaches $300 in zero hours). Building the 30-Minute product
  remains defensible as *structure* under rule 1, but it will not move C3a and
  must not be sold as the gate's fix.
* Any level-shifting lever (§3 — the cheap 77 % of hours are already over-priced
  by $4–10/MWh; raising the level breaks them and breaks 2023's +4.7 %).

**The live question is reserve/LP tightness — the supply side.** The model
carries **38.1 GW of deliverable 10-min ramp against a ~3.7 GW requirement**
while PJM cleared 1.6 GW against 2.5 GW. Until that headroom is realistic,
no demand curve can price scarcity and the upper strata stay compressed. This
is the G-20b / ERCOT-G-22 class the owner has already named. Candidate framings
(none validated here): whether perfect-foresight all-online commitment should
be constrained before the reserve bound is read, and whether `ramp10`
deliverability should be scoped to genuinely committed-and-online capacity
rather than the availability-scaled fleet.

**A caution for whoever scopes that work.** Closing only the >$376 stratum
would pass C3a-2025 (≈ −7.3 %) while leaving −$7.4 of the compression and the
over-priced cheap hours intact. Per rule 1 the objective is the mechanism, not
the band — a fix that buys the gate without moving the dispersion should be
recorded as a partial repair, not a closure.

**Reproduction.** `scripts/regenerate_clean.py transfer-interface-limits
ramp-capability` (seconds — the full sweep is not needed) then
`scripts/data/fetch_pjm_da_virtuals.py --years 2025` (the keeper's
`pjm_da_virtual_bids` hard-fails without it), then `replay_keeper.py
results/calibration/pjm119_overlay_restore --years 2025`. Read out with
`scripts/probes/pjm120_c3a_stratum_readout.py`. Note the container suspends
between turns, so a solve advances only while a command is actively running.

## Pointers

* Superseded framing: the pjm-119 handoff's "summer SHOULDER-hour price LEVEL
  miss" and its `gas_offer_margin_anchor` lead (§2 refutes both).
* Prior adjudication of `pjm_reserve_pergen_sync`: owner hold 2026-07-11
  (`docs/calibration-log.md`), scoped to **C3c's $75–200 afternoon band** —
  a different question from C3a's extreme-tail depth. See §6.
* Mechanism provenance: `docs/multi-iso/pjm-reserve-curve-source.md`.
