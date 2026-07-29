# FINDING — caiso-137 (⚠ PARTLY CORRECTED, see the banner below): ask **A2 CLOSES as a no-defect** — the CAISO overlay's reserve measure is ALREADY plant-level online, and options (a)/(b)/(c) are each refuted against the code. **That result stands.** The storage-tier "defect" this document went on to file, and the D2 E1/E2 gate table built on it, are **WITHDRAWN by caiso-137b**: the overlay never runs in a CAISO backcast, and its storage argument was never the flat nameplate. **No solve was run and nothing was armed.**


> ## ⚠ CORRECTED 2026-07-29 (caiso-137b) — READ THIS FIRST
>
> **§1 STANDS in full: ask A2 closes as a no-defect.** That is this document's
> primary result and it is re-verified by the correction instrument.
>
> **§2–§5 are WITHDRAWN.** Two secondary claims were wrong, both because this
> session reconstructed the overlay through
> `scripts/run_calibration.py::run_year(fleet_only=True)` instead of tracing the
> call site:
>
> 1. **The overlay never runs in a CAISO backcast.** `caiso_scarcity_overlay` is
>    called in exactly one place — `src/market_sim/runner.py:2085`, the FORECAST
>    path. The calibration path never imports `market_sim.runner`, and its only
>    price writer (`_system_frame`) builds `total_overlay` from **ERCOT terms
>    alone**. A CAISO keeper's persisted price is the **energy-only LP dual**, the
>    realised adder is **exactly $0.00 in every hour**, and
>    `caiso_scarcity_pricing=True` is a **stored no-op** in that lane. The
>    "realised overlay adder $0.1399 / $0.0158 / $0.0004" is withdrawn — it
>    described a counterfactual, and with it the entire §4 D2 E1/E2 gate table.
> 2. **There is no flat-nameplate defect.** `runner.py:993-999` REPLACES
>    `storage.power_cap` with the COD-ramped 2-D array before any solve, so the
>    overlay's third argument is already the hourly in-service cap. The 1-D
>    nameplate measured in §3 is a property of the `fleet_only` reconstruction
>    helper (which assigns the ramped cap to a separate local, line 3741), **not
>    of the overlay**. The "phantom 3,049 / 3,567 / 4,317 MW" is withdrawn.
>
> **Net effect: there is no defect and no keeper candidate.** What the correction
> leaves standing is sharper than what it removes — CAISO has **no
> scarcity-pricing mechanism in the backcast at all**, which is the honest reason
> its C3c is 0 / 0 / 0.
>
> Correction record and instrument:
> `FINDING-caiso137b-overlay-reachability-2026-07-29.md`,
> `scripts/probes/_caiso137b_overlay_reachability.py`. The §2 `r_online`
> decomposition and the §5 dump-floor method remain valid as *technique*; their
> numbers characterise the forecast-path overlay evaluated on backcast inputs,
> never a realised backcast price.

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED**, determination NOT-YET,
fail set {C3a-2025, C3c}. No LP was built, no solver called, no `ScenarioConfig`
field added, no flag flipped, no bundle produced. Every number below is read from
the keeper's committed sidecars plus a `run_year(fleet_only=True)`
reconstruction.

Instrument (committed): `scripts/probes/_caiso137_lolp_reserve_measure.py`
(sections A–F), which reproduces this document end-to-end in ~10 minutes with no
solve.

---

## §1 — STEP 1: A2 as written, adjudicated against the code

The brief required A2 to be **re-specified before being gated**, because
`FINDING-caiso133` §7 had already flagged that the ask's premise did not match
the code. It does not, and the correction runs deeper than caiso-133 stated: not
one of the ask's live readings survives.

`results/scarcity.py:2002-2024` — the whole of `caiso_scarcity_overlay`:

```python
r_online, r_offline = reserve_headroom(...)          # plant-level online split
reserves_total = r_online + r_offline                # + import_headroom if supplied
return ordc_adder(reserves_total, lam, ..., reserves_online_mw=r_online)
```

| A2 option (brief STEP 1) | verdict | why |
|---|---|---|
| **(a)** `reserves_total` is the wrong argument to the FULL-HOUR term | **NO** | It is the published two-half-hour RTORPA form. `r_offline` is headroom on **offline quick-start** plants (`QUICK_START_FUEL_TYPES` = gas_ct/oil) — 30-minute non-spin capability, exactly what a full-hour reserve measure carries and what CAISO procures as Non-Spin. A cold slow-start unit already contributes to **neither** tier. |
| **(b)** `import_headroom` does not belong in any tier | **MOOT** | `caiso_scarcity_import_headroom` is **`False`** on this keeper, so `import_headroom is None` and enters **no tier at all**. There is nothing to remove. The caiso-85 design question is real but not live. |
| **(c)** `r_online` is understated — storage + curtailed VRE are missing | **NO** | The code **already** carries both (`reserve_headroom` adds storage headroom and `renewable_headroom`; `runner.py:2040-2045` builds the VRE term). `FINDING-caiso133` §7's "missing" was a statement about the **sidecar measurement**, not the code. §2 measures both for the first time. |
| **(d)** nothing — the measure is right | **YES, on the basis** | The measure basis is already plant-level online, via `_online_plant_mask`. **A2 as written closes as a no-defect.** |

**A2 is therefore CLOSED.** This is a rule-1 `[R-STRUCT]` judgement made against
the code, not against the residual — it would be the same answer whichever way
the residual moved.

## §2 — the decomposition A2's D1 was a lower bound on

`FINDING-caiso133` §7 could only measure the **thermal** leg and said so. With
the storage sidecar and the rebuilt caps, here is the whole of `r_online`:

| year | thermal ONLINE (p10) | storage headroom (p10) | curtailed VRE (med) | **r_online (p10)** | r_offline (p10) | reserves_total (p10) |
|---|---|---|---|---|---|---|
| 2023 | 1,201 | 6,845 | 0 | **8,748** | 5,924 | 14,442 |
| 2024 | 1,119 | 8,577 | 0 | **10,499** | 6,023 | 16,774 |
| 2025 | 1,021 | 11,480 | 0 | **13,124** | 6,184 | 19,512 |

Two things this settles:

* **Storage is the dominant term** — 5.7× to 11× the thermal leg. The caiso-133
  D1 number (1.0–1.2 GW) is a lower bound on `r_online` by roughly an order of
  magnitude, exactly as that FINDING warned.
* **Curtailed VRE is ~0 by construction**, in every hour, all three years. The LP
  carries a `Dump` column, so surplus renewables are *dumped* at the dump price
  rather than *curtailed* below potential. The overlay's renewable term is
  therefore inert in CAISO — not wrong, just empty. (Its min of −0.00 MW across
  26,280 hours also validates the rebuilt potential against the solved
  dispatch: the reconstruction never claims more output than potential.)

**A correction to `FINDING-caiso131` §4.** That FINDING recorded the overlay as
"armed and inert because R never approaches MCL = 1,400 MW". The premise is
right — reserves_total never falls below 8.2 GW — but the inference is not: with
σ = 2,500 MW the Gaussian tail still reaches out ~4σ, so the adder is small but
**not identically zero**. Reconstructed, it contributes a demand-weighted
**$0.14 / $0.016 / $0.0004 per MWh** and exceeds $10/MWh in 20 hours of 2023.
§5.1 bounds how tightly that level can be pinned without a solve; the
qualitative correction ("nearly inert, and not for the stated reason") is firm.

## §3 — the defect the decomposition exposes

`runner.py:2085-2094` calls

```python
caiso_adder = caiso_scarcity_overlay(fleet_arrays, result.dispatch,
                                     storage.power_cap,   # <-- flat NAMEPLATE
                                     ...)
```

`StorageArrays.power_cap` is the **per-unit nameplate** array
(`model/storage.py:109`), and each unit's `power_cap_mw` is set to
`float(monthly_p[-1])` (`storage.py:401`) — the **December** value. Handed a 1-D
array, `reserve_headroom` broadcasts it to a **constant** hourly series
(`np.full(shape, cap.sum())`). The LP itself bounds storage with the hourly
`storage_power_cap`, which carries the COD vintage ramp (`storage_vintage_ramp`,
**on** for this keeper).

**So the overlay credits, as online spinning reserve, battery power the LP's own
bounds hold at zero because the unit is not yet in service.**

| year | nameplate (Dec) | COD-ramped range | **phantom max** | phantom mean | hours > 500 MW | max % of `r_online` |
|---|---|---|---|---|---|---|
| 2023 | 9,570 MW | 6,521 → 9,570 | **3,049 MW** | 1,968 MW | 8,016 / 8,760 | 51.2 % |
| 2024 | 13,209 MW | 9,642 → 13,209 | **3,567 MW** | 1,854 MW | 7,296 / 8,760 | 44.3 % |
| 2025 | 17,526 MW | 13,209 → 17,526 | **4,317 MW** | 2,277 MW | 8,016 / 8,760 | 44.9 % |

**The corrected basis is unambiguous.** On this keeper the COD-ramped cap and the
LP's own hourly `storage_power_cap` are the **same array** —
`max |COD-ramped − LP cap| = 0.000000 MW` in all three years — so the caiso-99
shape anchor (`caiso_storage_shape_anchor`, on) does not reduce the fleet-summed
power cap and there is **no rule-19 `[R-ONE-MECH]` double-count to weigh**.

**Independent corroboration — the codebase already disagrees with itself.** The
offline derivers written to *reproduce* these overlays read the hourly cap:

* `scripts/data/derive_ordc_overlay.py:200-201` —
  `cap = state["storage_power_cap"]; cap_t = cap.sum(axis=0) if cap.ndim == 2 …`
* `scripts/data/derive_caiso_scarcity_overlay.py:119` —
  `cap_t = a["storage_power_cap_mw"]`, the hourly series

while `runner.py:2088` (CAISO) and `runner.py:1996` (ERCOT) pass the flat
nameplate. Two implementations of one overlay, disagreeing on the storage tier —
and the reference implementation uses the hourly cap. This is a rule-14
`[R-ACCURATE]` defect: the accurate input is already built, already consumed by
the LP, and already in scope at the call site.

**Scope (rule 25 `[R-ISO-SCOPE]`).** `runner.py:1996` is the **ERCOT** ORDC call
and carries the same argument. Any arming must be scoped to the CAISO call site
alone, or adjudicated per-ISO on ERCOT's own evidence. A CAISO session does not
change ERCOT's behaviour.

## §4 — D2 and D3

**D3 — no fitted parameter: PASS.** `CAISO_SCARCITY_VOLL` $2,000,
`CAISO_SCARCITY_MCL_MW` 1,400, `CAISO_SCARCITY_SIGMA_MW` 2,500 and
`CAISO_SCARCITY_SHIFT_SIGMA` 0.0 are unchanged at their published
CAISO-tariff-backed values (verified against `run_config.json`). The correction
adds **no** `ScenarioConfig` field, **no** threshold, **no** multiplier: it swaps
one already-built array for another at one call site. D3 passes by construction.

**D2 — the ask memo §2 E1/E2 spillover pre-check: FAILS on E1.**

| year | keeper adder | corrected adder | **Δ annual dw-mean LMP** | §2 gate | verdict |
|---|---|---|---|---|---|
| 2023 | $0.1399 | $2.6325 | **+$2.4926** | — (+$3.67 of room) | — |
| 2024 | $0.0158 | $0.5700 | **+$0.5542** | ≤ +$0.30 (E2) | **FAIL** |
| **2025** | **$0.0004** | **$0.0672** | **+$0.0668** | **≤ +$0.00 (E1)** | **FAIL** |

Prices are computed on the recovered **pre-adder** λ fixed point — `runner.py`
evaluates the overlay on the pre-overlay demand-weighted price and then adds the
adder to every zone, so the persisted series is `λ_pre + adder` and the fixed
point `a = f(R, λ_post − a)` recovers both exactly.

**E1 fails structurally, not on a magnitude.** The correction can only *shrink*
the reserve measure, and the adder is monotone decreasing in the measure, so
Δ > 0 in every hour where the overlay is not already identically zero. E1's gate
is exactly +$0.00. There is no reconstruction under which this passes — §5.2
confirms it across a 0–5,000 MW sensitivity sweep.

## §5 — how far these numbers can be trusted

The reconstruction is honest about being one. The rebuild is a
`run_year(fleet_only=True)` approximation of the keeper's fleet (it carries only
the `meta.json` flags that map onto `run_year`'s signature) and produces
1,800–1,808 LP units against the keeper's own 1,619, so `r_online` is
*reconstructed*, not read. Two checks bound it.

### 5.1 — the hard bound: the LP's own dump-price floor

The dump column's reduced cost gives `λ_z ≥ −dump_cost` in **every** zone-hour.
So wherever the persisted min-zonal price sits exactly on that floor
(−$26.001/MWh), the pre-adder price was also on the floor and the realised adder
in that hour is **exactly 0** — a hard, exact measurement of the truth in
thousands of hours per year.

| year | floor-pinned hours | of those, recon > $0.01 | provably-spurious $/MWh | % of recon dw-mean | implied missing `r_online` (median) |
|---|---|---|---|---|---|
| 2023 | 2,774 | 152 | $0.0091 | 6.5 % | 934 MW |
| 2024 | 4,251 | 133 | $0.0026 | 16.6 % | 696 MW |
| 2025 | 2,771 | 7 | $0.0001 | 22.9 % | 230 MW |

The reconstruction is exact in the overwhelming majority of pinned hours (19 of
2,774 exceed $1 in 2023) and biased **high** by a measured 6.5–23 % of the
level, consistent with `r_online` being understated by roughly 0.2–0.9 GW.

### 5.2 — the sensitivity sweep, and what survives it

Adding a uniform offset `δ` to `r_online` in **both** arms:

| δ (MW) | 2023 Δ$ | 2024 Δ$ | E2 | 2025 Δ$ | **E1** | C3c 2023 | C3c 2024 |
|---|---|---|---|---|---|---|---|
| 0 | +2.4926 | +0.5542 | FAIL | +0.0668 | **FAIL** | 16 h ✗ | 0 h ✗ |
| 500 | +1.3818 | +0.2740 | PASS | +0.0284 | **FAIL** | 0 h ✗ | 0 h ✗ |
| 1,000 | +0.7246 | +0.1276 | PASS | +0.0114 | **FAIL** | 0 h ✗ | 0 h ✗ |
| 2,000 | +0.1671 | +0.0229 | PASS | +0.0015 | **FAIL** | 0 h ✗ | 0 h ✗ |
| 3,000 | +0.0301 | +0.0032 | PASS | +0.0001 | **FAIL** | 0 h ✗ | 0 h ✗ |
| 5,000 | +0.0004 | +0.0000 | PASS | +0.0000 | **FAIL** | 0 h ✗ | 0 h ✗ |

Three conclusions, graded by how robust they are:

1. **E1 FAILS at every offset — robust, and structural.** D2 fails. **No solve is
   authorized.**
2. **E2 is INDETERMINATE at this fidelity.** It fails at δ = 0 and passes from
   δ = 500 MW, i.e. its verdict flips *inside* the reconstruction's own measured
   error band (median missing `r_online` 696 MW in 2024). Recorded as
   indeterminate rather than claimed as a fail.
3. **The correction cannot close C3c under any admissible reconstruction** —
   robust. C3c's basis is the scorer's own (`_tail_hours`: hours whose **max
   zonal** LMP exceeds $200; CAISO has no `scarcity.parquet`, so the fallback
   applies). At δ = 0, the *most generous* point of the sweep, the correction
   yields **16 hours in 2023** against a 24–94 h band and **0 in 2024** against
   18–70 h. Every correction to the reconstruction pushes `r_online` **up**,
   which pushes the count **down** — 0 h at every δ > 0. The band arithmetic
   `FINDING-caiso131` §5 predicted (12.6–12.8 GW deep) holds: this corrects the
   measure, it does not remove the band.

## §6 — disposition

**A2 is closed and its replacement is filed, not armed.** Stated plainly, in the
terms the ask memo §4 itself set ("judge it on whether the measure is right … do
not fund it as a C3c fix and then judge it on the tail count"):

* The **measure basis** is right. A2 as written is a no-defect (§1).
* The **storage tier** is wrong, on rule 14 `[R-ACCURATE]` grounds, with zero new
  free parameters and an independent corroboration from the repo's own derivers
  (§3). That judgement does **not** depend on any residual and is not withdrawn
  by anything below it.
* Arming it **fails D2's E1** structurally (§4, §5.2), and it does **not** buy
  C3c (§5.2). Under the brief's gate structure — "IF AND ONLY IF STEP 1 + D2 +
  D3 PASS" — **no solve is authorized and none was run.**

Arming the storage-tier fix is therefore a **separate owner act**. Per rule 1
`[R-STRUCT]` it must be decided on whether the measure is right — **not** on the
residual in either direction: neither armed because it might buy 16 tail hours,
nor refused because it costs +$0.07/MWh in 2025. If it is armed, it needs (i)
CAISO-scoped call-site handling so ERCOT is byte-identical (rule 25), (ii) the
full three-year A/B with both arms registered (rules 15/16), and (iii) a rerun of
the §5 bounds against the arm's *own* solved reserves, which removes the
reconstruction uncertainty §5.1 could only bound.

**What this does NOT change:** keeper unchanged; determination NOT-YET; fail set
{C3a-2025, C3c}; no gate re-scored; rule 22 `[R-HOLDOUT]` respected (2023–2025
only — no 2022/2019/H1-2026 solve, score or probe).

## §7 — DO-NOT-REDO (new, binding)

* **Re-specifying A2 as options (a), (b) or (c).** §1 adjudicates all three
  against the code: the full-hour argument is the published RTORPA form,
  `caiso_scarcity_import_headroom` is off so `import_headroom` enters no tier at
  all, and storage + curtailed VRE are already in `r_online`. A2 as written is
  closed as a no-defect and does not need re-opening.
* **Re-measuring the CAISO overlay's `r_online` decomposition.** §2 carries it
  for all three years from committed bytes; the instrument re-runs it with no
  solve. Storage is 5.7–11× the thermal leg and the curtailed-VRE term is
  identically ~0 because the LP dumps rather than curtails.
* **Proposing the flat-nameplate storage tier as a C3c candidate.** §5.2: 16 h in
  2023 at the most generous reconstruction against a 24 h floor, 0 h at every
  other point of the sweep, 0 h in 2024 throughout. It cannot close C3c, and a
  proposal that says otherwise must first overturn the sweep's monotonicity.
* **Re-running the E1 pre-check for any measure-SHRINKING correction to this
  overlay.** E1's gate is exactly +$0.00 and a smaller reserve measure can only
  raise the adder, so E1 fails for the whole family by construction — not for
  this candidate in particular. Any future member of it is pre-refused on E1
  unless E1 itself is re-specified by the owner.
* **Re-deriving which storage cap the overlay should use.** §3: the COD-ramped
  cap and the LP's hourly `storage_power_cap` are byte-identical on this keeper
  (`max |Δ| = 0.000000 MW`), and both derivers already use the hourly cap. There
  is no third basis to weigh and no shape-anchor double-count to adjudicate.

Carried forward unchanged: everything in `FINDING-caiso136` §5,
`FINDING-caiso135` §10, `FINDING-caiso134` §9, `FINDING-caiso133` §9,
`FINDING-caiso132` §10, `FINDING-caiso131` §10, `FINDING-caiso130` §7,
`FINDING-caiso129` §6 and `FINDING-caiso127` §7. Notably still binding: the
entire committed-gas lane is CLOSED; the unit-availability window family is
CLOSED for CAISO (matrix cell `I`); the corridor lane is CLOSED for C3a-2025 in
both directions; `caiso_endogenous_wecc_node` is not re-armable; and C3a-2025 is
a guard, never a tuning target.

**Still open and untouched by this session:** the caiso-134 §2 observation (the
70 → 161 → 307 MW of self-scheduled firm PNW hydro dumped at WECC_PNW, the
interaction between `caiso_firm_import_selfschedule` and
`caiso_corridor_flow_limit`). It remains filed with no charter; this session did
not reach it.

Next number: caiso-138.
