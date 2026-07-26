# HANDOFF — the path from PJM CALIBRATED to PJM FRONTIER (2026-07-26)

**Status going in:** PJM keeper `2026-07-25-pjm-121-cc-belt` is **CALIBRATED,
10/10** — PJM's first all-pass determination. It carries **no frontier block**
(`frontend/data/backcast/keepers/PJM.json` has `keeper` / `promotion_note` /
`note` only). Frontier holders today: **NEISO** and **NYISO** (both 2026-07-11).
ERCOT's stale block was removed 2026-07-26 (declared and withdrawn the same day
by the ERCOT-79 audit; lineage preserved in its `promotion_note`).

**Frontier is owner-declared and purely declarative.** No session may set it.
`build_status.py:494–501` attaches `verdict["frontier"]` *after* `determine()`
runs, for a badge and note on the Calibration Status page — it never gates and
never touches the verdict.

---

## 1. The bar, stated exactly

From `docs/codebase-site/calibration-rubric.html` §frontier:

> Every named admissible mechanism for the ISO's residual caveat family has
> been tried **on record**, and what remains is either **inadmissible to close**
> (residual-fitting, rule 26) or **blocked on data that does not exist
> publicly**.

Both current holders earned it the same way: every hard and volume criterion in
band, the entire remaining residual is the C3c price scarcity tail, and the
tail is gated by reserve dynamics the real ISO either has not implemented or
that would need new measured identification.

* **NEISO** — four named mechanisms tried on record; the real tail forms while
  the model still carries GW of cheaper non-fast-start headroom, so no
  repricing of the fast-start band reaches it.
* **NYISO** — the deep >$300 tail's two candidate reserve levers chased to
  ground; the sole remaining gap (IMM Rec. 2021-1 net-load forecast-uncertainty
  reserve) has no published formula, so adding it would be residual-fitting.

PJM clears the first half of that bar already (10/10). What frontier needs is
the **ledger**: the enumeration, tried on record, of what owns the remaining
residual.

## 2. PJM's ledger — what is already closed

Reserve/scarcity lanes (`docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3):

| lane | result | disposition |
|---|---|---|
| Post-solve two-step ORDC overlay (arch. A) | fires 8/20/5 h, overshoots ($850-class vs the $75–200 need), cannot make the sub-shortage $50–105 component | retired to diagnostic; **inadmissible** in the keeper line (would stack on the live co-opt, rule 19) |
| Zone-aggregate co-opt scoping | reserve price $0 in all 26,280 h (deliverable cap ~50 GW ≫ 3.4 GW req) | empirically refuted |
| Per-gen class-tier co-opt, measured ramp (arch. B) | fires 1 h / 3 yr ($46.47) | **live in the keeper — the sole reserve-price owner** (rule 19) |
| SYNC product / size split | duals in the correct regime but $0–10 vs the $75–200 need | **owner-CLOSED 2026-07-11** |
| Commitment posture (Phase 1) | G-P1 FAIL all years, model online headroom 2.66–3.14× the measured target; tail unchanged | REJECTED — root cause is **LP-vs-MIP**, a representation boundary under the no-MIP mandate |
| DA demand depth + measured offer levels (G-22) | moved 2025 C3c 0 → 17 h, fixed C1/C3a/C3b/C7 | **in the keeper** |
| **`ramp10` scoped to committed-and-online (Lane 1 framing 2)** | **no-LP pre-check, all 3 years: rigorous lower bound stays 9.7–10.5× the requirement; reduction only 13.6–15.9 %, and smallest (8–10 %) in the TIGHTEST net-load quartile** | **CLOSED pjm-124 — no solve spent** (`docs/FINDING-pjm124-ramp10-scoping-precheck-2026-07.md`) |

Offer/energy-stack lanes:

* **`pjm_reserve_pergen_sync`** — settled on **direct evidence**, not by the
  A/B arm (which OOM-killed in the P1 warm-start at ~15 GB). pjm-120 §6.1 reads
  the keeper's own persisted reserve dual: **22 nonzero hours of 8,759, 0 hours
  ≥ $300, 0 ≥ $850, max $210.99**. At the worst hour (h4193, PJM printed
  $1,722, 896 MW short on Synchronized) the model's dual is $210.99. The
  balance never leaves the sub-shortage regime, so a second ORDC curve over
  ~10× slack cannot move C3a. **Closed on merit — the OOM is irrelevant.**
* **B.4 leg A (`gas_daily_shape`)** and **leg B (`CC_LIKE` mid-curve)** — both
  now **live in the keeper** (leg B is the pjm-121 promotion itself).
* **`gas_offer_margin_anchor`** — refuted, pjm-120 §1.
* **The entire measured-offer-surface family as a dispersion lever** — refuted
  pjm-123 (`docs/FINDING-pjm123-composite-precheck-2026-07.md`). Not just the
  three-leg composite: the frozen surface prices `CT_FAST`, `CC_LIKE` **and**
  `LONG_RUN` cheapest in the tightest net-load bin, so *any* mechanism handing
  a class its measured conditional level compresses top-end dispersion instead
  of widening it. Legs 1/2/3 and every recombination are closed.

**Read that list against the bar.** PJM's remaining residual is already
characterized the way NEISO's and NYISO's are: the >$200 tail is owned by the
reserve *supply* side, and pjm-82/B.4 name it a **disclosed representation
boundary under the no-MIP mandate** — a continuous `U` holds fractional online
capacity at near-zero cost, so the perfect-foresight LP carries 2.66–3.14× the
measured online reserve. That is a structural boundary, not a tuning gap.

## 3. What still blocks the declaration — two lanes, both admissible, neither tried

### Lane 1 (primary) — G-20b reserve SUPPLY side, the two unvalidated framings

> **UPDATE 2026-07-26 (pjm-124): framing 2 is CLOSED, no solve spent.**
> `docs/FINDING-pjm124-ramp10-scoping-precheck-2026-07.md`. Three results the
> rest of this section should be read against:
>
> 1. **45 % of the deliverable ramp is tariff-protected.** The keeper's balance
>    families are **Primary** = Synchronized + **Non-Synchronized**, and
>    Non-Sync reserve *is* offline 10-min-startable iron (Manual 11 §4.2). The
>    fast-start term — 1,411 members, 30.6 GW nameplate, **F = 17.6 GW mean, 45 %
>    of the 38.9 GW cap** — counts in either commitment state, so no
>    commitment-state scoping may remove it. F alone is **5.2× the requirement**.
> 2. **The rigorous lower bound stays 9.7–10.5× the requirement** in 2023/2024/
>    2025 (`F + max(MG, DISP)` = 32.6 / 33.2 / 33.6 GW). The mechanism does not
>    reach even the PARTIAL band. Its bite is *smallest* (8–10 %) in the tightest
>    net-load quartile — where the residual lives.
> 3. **The strict online-only variant is closed too**, on both grounds: it prices
>    Synchronized while calling it Primary (a product mismatch, rule 1), and its
>    own lower bound is still **4.6–4.9× the requirement**.
>
> **Consequence for the ledger — this qualifies pjm-82's LP-vs-MIP attribution.**
> Even with commitment state read exactly, and counting only iron the tariff
> permits, the balance stays ~10× slack. **A MIP would not close this gate
> either.** The slack is the size of PJM's reserve-eligible fast-ramping fleet
> against a ~3.4 GW requirement — a real fleet property, not a representation
> artifact. That is a strong prior that **framing 1 (pjm-125) will land the same
> way**, since it addresses the same online/offline distinction just measured to
> be worth 13.6–15.9 % of a 10× surplus. Framing 1 is still worth running for
> the record; it should not be expected to move the tail.
>
> Corroboration, free of any solve: the keeper's persisted reserve dual is now
> read across **all three** years — **0 hours ≥ $300 in 26,280**, and in 2023 and
> 2024 the dual is *identically zero all year* (2025's 22 nonzero hours, max
> $210.99, is the tightest of the three, not a representative one).

`docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md` §7 names two candidate
framings and explicitly marks them **"none validated here"**:

1. **Constrain perfect-foresight all-online commitment before the reserve bound
   is read.** The LP reads reserve headroom off a fleet it has already
   committed with perfect foresight; the question is whether that commitment
   should be constrained first.
2. **Scope `ramp10` deliverability to genuinely committed-and-online capacity**
   rather than the availability-scaled fleet.

The measurement that motivates both: **38.1 GW of deliverable 10-min ramp
against a ~3.7 GW requirement**, while PJM actually cleared 1.6 GW against 2.5
GW. Until that headroom is realistic no demand curve can price scarcity.

Until these two are on record — implemented and measured, or shown
inadmissible — PJM has a *named admissible mechanism not yet tried*, which is
exactly what the bar excludes. **This is the critical path.**

**Session charter.** Both framings are P1-native and read the model's own P0
run pattern, so neither needs new data and neither is residual-fitting; both
change *which capacity counts as deliverable reserve*, a structural question.
Precedent wiring exists: `build_pjm_reserve_p1_prep` (path B) already zeroes
non-fast-start reserve-eligible units' availability in their plant's P0-offline
hours and recomputes the supply cap on the masked fleet — framing 2 is a
tightening of that scope, framing 1 is its commitment-side analogue.

**Pre-register the kill criteria before solving** (the pjm-121 §5 / pjm-123
pattern, which has now killed two candidates without spending a solve):
* the deliverable-ramp aggregate must fall toward the ~3.7 GW requirement from
  38.1 GW — state the target band before the run;
* the reserve dual must cross **$300** in a nonzero number of hours (today: 0
  of 8,759, max $210.99) — this is the single most diagnostic number in the
  lane and it is readable from `hourly/system_<year>.parquet::reserve_price`
  **without a re-solve** on any bundle that has one;
* C1 fuel-mix must stay 16/16 — tightening reserve supply moves energy dispatch;
* rule 1: a framing that closes the tail by making reserve artificially scarce
  is not a repair. The headroom must be wrong *for a stated physical reason*.

**Honest expectation, stated up front.** pjm-82's finding is that the binding
constraint is LP-vs-MIP. Both framings may well land as *partial* — narrowing
the headroom without crossing $300 — which would itself be the frontier
evidence: it would demonstrate on record that the supply side cannot be closed
within the no-MIP mandate. **A negative result here advances the declaration
just as much as a positive one.** Do not chase the number.

### Lane 2 (secondary) — the pjm-123 derive-conditioning question

Is the tightest-bin inversion in `pjm_offer_midcurve_condbinned.json` a real
property of PJM offers, or an artifact of the derive's conditioning? Evidence
(2025 tables, × delivered gas, surface's own edges `[0.80, 0.90, 0.97]`):

| segment | bin0 | bin1 | bin2 | **bin3 (tightest)** |
|---|---|---|---|---|
| CT_FAST (s0.05–0.85) | 26.5–30.9 | 32.0–33.9 | 32.7–34.5 | **22.5–25.2** |
| CC_LIKE (body) | ~4.9–5.1 | 5.17–5.42 | 5.08–5.53 | **4.83–4.92** |
| LONG_RUN (top) | 8.57–8.97 | 8.28–8.62 | 8.18–8.62 | **8.07–8.47** |

Not a gas artifact: bin3's mean delivered gas is itself the lowest ($4.03 vs
$4.53 in bin1), so a constant dollar offer would read as a *higher* multiplier.

**Hypothesis to test (not a claim):** within-*year* net-load percentile puts
winter evening peaks and summer scarcity in the same bin3, and fast-start units
in those hours are largely already committed — so the offers *submitted* in
bin3 come from a different population than the offers that *set* the price.

**Constraint — read before touching anything.** This is a rule-20 review of
`scripts/data/derive_pjm_offer_midcurve.py`. Derive scripts are **frozen
against residuals**: a re-derivation commit must cite a **data or
conditioning-definition change**, never a residual movement. A season-split or
committed/uncommitted-split conditioning is a *definitional* change and is
admissible on that basis alone; re-deriving because C3a moved is not. Owner-gated.

If the inversion proves to be an artifact, the measured surface may re-enter as
a dispersion lever and pjm-123's §3 generalization narrows to "the surface *as
conditioned in the 2026-07 vintage*". If it proves real, §3 stands as written
and this lane closes — **either outcome is ledger progress.**

## 4. Suggested sequence

1. ~~**pjm-124 — Lane 1, framing 2**~~ — **DONE 2026-07-26, CLOSED on the no-LP
   pre-check, no solve spent.** See the Lane 1 update above and
   `docs/FINDING-pjm124-ramp10-scoping-precheck-2026-07.md`. The §5 housekeeping
   item is also done: `scripts/lib/bundle_fleet.py` is the shared widened
   reconstruction helper.
2. **pjm-125 — Lane 1, framing 1** (constrained commitment before the reserve
   bound). Run only after 124, so the two are separably attributable (rule 19 —
   do not arm both and read one number).
3. **pjm-126 — Lane 2**, owner-authorized, as a derive review with its own
   admissibility memo. Independent of 1–2; can run in parallel by a separate
   session (rule 12: separate invocations concurrent, years sequential within).
4. **Then, and only then, the owner decides frontier** on the completed ledger.

Rule 16 binds throughout: any registered bundle is `--year 2023 2024 2025` in
one invocation. Rule 22: PJM has **no calibration-complete marker**, so no
out-of-training year (2022, 2019, ≤2021, H1-2026) may be solved or scored.
Frontier and calibration-complete are independent — NYISO holds frontier with
no marker.

## 5. Two housekeeping items this session surfaced

* ~~**`derive_pjm_ordc_overlay._run_year_kwargs` drops 38 non-default `run_year`
  flags**~~ — **DONE (pjm-124)**: promoted to `scripts/lib/bundle_fleet.py`
  (`full_run_year_kwargs`, `reconstruct_bundle_fleet`, the year-chain gas-price
  fallback and a generalized fidelity guard covering the offer-path *and*
  reserve gates). `pjm123_composite_precheck.full_run_year_kwargs` now delegates
  to it. Original description follows.

  **`derive_pjm_ordc_overlay._run_year_kwargs` drops 38 non-default `run_year`
  flags** the pjm-121 keeper records — including all three `tranche_startup_*`
  gates, `ct_netload_drag` / `gas_st_netload_drag` and their overrides, and the
  `pjm_offer_midcurve_conditional` master gate. Every PJM no-LP probe that uses
  it measures a fleet the keeper never solved.
  `scripts/probes/pjm123_composite_precheck.py::full_run_year_kwargs` is the
  widened replacement, with fidelity guards that hard-fail on a dropped gate.
  **Promoting it to the shared helper is a small unblocked task** and should
  happen before Lane 1's pre-check, which will want the same reconstruction.
* **pjm-121 §5's level-form magnitudes** (−8.76 $/MWh MW-weighted; the CC econ
  spread table) were measured on the partial reconstruction. Its *conclusion*
  is unaffected and is independently reconfirmed by pjm-123 §2, but those
  specific numbers should not be quoted as the keeper fleet's.

## 6. Environment (container starts empty)

```
uv sync                                        # use .venv/bin/python throughout
python scripts/regenerate_clean.py transfer-interface-limits ramp-capability lmp
python scripts/data/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds hrl_da_incs_decs
```

The virtuals fetch is **required** (`pjm_da_virtual_bids` hard-fails without the
gitignored raw) and takes ~10 min/yr. Solves ~15 min/yr, peak ~14.8 GB on a
15 GB box — one solve process at a time, years sequential. The container
suspends between turns: `nohup` the solve and hold awake in bounded blocks.

Fidelity anchor, **no solve needed** (the keeper hourlies are committed):
`pjm120_c3a_stratum_readout.py results/calibration/pjm121_ccbelt --year 2025`
must read model_lw 41.53 / actual 46.07 / gap −4.54.

The reserve-dual readout that Lane 1 turns on is likewise no-solve:
`hourly/system_<year>.parquet::reserve_price` on any bundle carrying sidecars.

## Pointers

* `docs/FINDING-pjm123-composite-precheck-2026-07.md` — the offer-surface family closure
* `docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md` §6–§7 — the reserve-dual evidence and the two unvalidated framings
* `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3–B.4 — the lever ledger and the LP-vs-MIP boundary
* `docs/FINDING-pjm121-ccbelt-c3a-close-2026-07.md` §4 — the honest-scope caveat carried with the keeper
* `docs/codebase-site/calibration-rubric.html` §frontier — the bar, and how NEISO/NYISO met it
