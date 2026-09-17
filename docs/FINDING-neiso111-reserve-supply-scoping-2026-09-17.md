# FINDING — neiso-111: why NEISO's reserve co-opt is dormant, and what the C3c tail actually needs

**Session:** neiso-111 (NEISO calibration lane, ORCHESTRATOR — **zero LP spent**).
**Keeper at this head:** `2026-09-16-neiso110-dualfuel-derate-scope`
(`results/calibration/neiso110_dualfuel_span`, years 2020-2025, CALIBRATED with a single
ledgered C3c caveat) — verified from `frontend/data/backcast/registry/` and
`frontend/data/backcast/keepers/NEISO.json` at HEAD `73281357`.
**Predecessors:** `docs/FINDING-neiso110-winter-oil-driver-2026-09-16.md`,
`docs/RESULT-neiso110-coldsnap-dualfuel-screen-2026-09-16.md`.

---

## 0. HEADLINE

The reserve co-opt is dormant because **98.95 % of the model's reserve capability at Winter
Storm Elliott is cold iron**. At the Elliott minimum-headroom hour (2022-12-26 17:00, model
hour 8633) the 6,959.1 MW of class-0 headroom decomposes as **73.3 MW online** and
**6,885.8 MW offline** — including **2,855.2 MW of oil-fired STEAM BOILERS that the model
counts as TEN-MINUTE reserve**, because NEISO reserve eligibility is a fuel-type membership
test (`oil ∈ QUICK_START_FUEL_TYPES`) with no start-time, ramp, or online gate of any kind.

**All three charter directions are answered with numbers, and none of them is the fix.**
Direction 1 is a definitional boundary and closing it naively would manufacture a shortage.
Direction 2 is structurally blocked and inert. Direction 3 is **unblocked on data** (its stated
blocker is falsified here) but moves **partly the wrong way** and cannot bind alone.

The one construction that reaches a binding hour at the right event is **supply-side response
scoping combined with the measured requirement** — and it crosses by only ~83 MW under the
*strictest* admissible scoping, so it is reported as sizing, not as a prediction.

---

## 1. G-DRIFT — form 4 VALID, no control LP spent (rule 29 `[R-SCREEN]` (b))

The keeper records `basis_sha c0916408bf1d69a8c8b249a76c6716ab024b1b29`. The audit:

```
git diff c0916408bf1d69a8c8b249a76c6716ab024b1b29 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
```

**Two files, two hunks, both INERT for NEISO:**

| file | hunk | classification |
|---|---|---|
| `scripts/run_calibration_full.py` | `_eia930_frame_generic`: pool-region benchmark dispatch (lane NWPP-40) | **INERT** — gated on `_is_pool_region(iso)`; NEISO is a 1:1 region and takes `load_eia_hourly_benchmark` on the unchanged path |
| `src/market_sim/model/interchange/spec.py` | single hunk at `MISO_PJM_BORDER_HR_BY_YEAR` — MISO 2020/2021 seam-ladder rows (lane miso-260) | **INERT** — another ISO's branch; no NEISO path reads the MISO seam ladders |

**All hunks INERT ⇒ form 4 is valid and the keeper's committed bundle is the control.**

---

## 2. DIRECTION 1 — THE DEMAND BOUNDARY. **CLOSED: it is a definition, not a miss.**

### 2.1 What the boundary is, measured

`scripts/run_calibration_full.py:5773` passes `include_interchange = not priced_interchange`, and
the keeper ran `priced_interchange=False`. So NEISO's LP demand is

> **EIA-930 ISNE demand − the measured EIA-930 net-interchange schedule = the INTERNAL
> GENERATION REQUIREMENT.**

Verified against the keeper's own committed sidecar, not inferred:

| 2022 | TWh | system peak |
|---|---:|---:|
| `load_demand(include_interchange=True)` | 100.2057 | 22,933 MW |
| keeper `hourly/system_2022.parquet`, summed over zones | **100.2057** | **22,933 MW** |
| `load_demand(include_interchange=False)` (raw ISNE demand) | 116.9243 | 24,233 MW |
| net-import wedge | 16.7187 | — |
| **ratio net / raw** | **0.8570** | — |

`np.allclose(sidecar, netted, atol=1.0)` → **True**. The 0.856 ratio neiso-110 reported is
**exactly** this wedge, to three decimals.

Across the span the wedge is large and strongly trending:

| year | model (netted) TWh | raw TWh | wedge TWh | ratio |
|---|---:|---:|---:|---:|
| 2020 | 92.096 | 115.294 | 23.198 | 0.7988 |
| 2021 | 98.551 | 117.117 | 18.566 | 0.8415 |
| 2022 | 100.206 | 116.924 | 16.719 | 0.8570 |
| 2023 | 96.863 | 112.003 | 15.140 | 0.8648 |
| 2024 | 103.810 | 114.107 | 10.297 | 0.9098 |
| 2025 | 107.155 | 115.281 | 8.126 | 0.9295 |

At Elliott (Dec 23-26 2022, 96 h): model 1.1747 TWh / peak **15,596 MW**; raw 1.3891 TWh /
peak **17,382 MW**; wedge mean 2,233.2 MW. Both reproduce neiso-110's figures.

### 2.2 Is the oil fleet inside the boundary? **Yes** — the netting removes only external
imports; every internal unit, oil included, serves the netted load.

### 2.3 Would carrying the measured load change the headroom? **Not admissibly.**

The imports are **already served** — as a netted wedge. Handing the internal fleet the raw
116.9 TWh without also giving it the import supply would force it to generate 16.7 TWh it never
generated; that is manufacturing a shortage, and rule 13 `[R-MEASURED]` forbids it. The
admissible alternative — `priced_interchange`, imports as supply on the `HQ_import` node — is
**headroom-neutral by construction**: if the priced tranches clear at the measured MW, internal
thermal output is identical and unloaded headroom is identical. neiso-110's lead
("carrying the real load would cut headroom to ~5,059 MW") holds only for the inadmissible
version.

**Closed. This is a real result and it is negative.** It also removes the largest remaining
suspicion about NEISO's demand construction.

### 2.4 One data-quality flag, recorded not pursued

The 2021 net-interchange wedge peaks at **12,307 MW** — roughly 2.8× ISO-NE's entire external
tie capability (~4.4 GW). Later years' maxima (4,206 / 4,386 / 4,637 / 4,788 MW) sit at the
physical envelope; 2021 does not. One or more EIA-930 ISNE `TI` hours are corrupt. Not this
lane's target, not acted on, recorded so the next lane does not rediscover it.

---

## 3. DIRECTION 2 — `neiso_rcpf_enabled`. **INERT, and structurally blocked.**

The charter asked for the obvious objection to be answered before proposing. It is worse than
inert:

1. **Hard-blocked.** `reserve_config._neiso_design` raises `ValueError` when
   `neiso_rcpf_enabled=True` under `energy_reserve_coopt` (`model/reserves/spec.py:3817`) —
   one mechanism per phenomenon, rule 19 `[R-ONE-MECH]`. The keeper has
   `energy_reserve_coopt=True`. The overlay is the **co-opt-OFF comparator**, nothing else.
2. **Nothing to price.** RCPF prices a reserve shortage. §5 measures the class-1 (ten-minute)
   supply at **no fewer than 1,494.9 MW in any of 2022's 8,760 hours**, against a 1,200 MW
   requirement — and that is under the *strictest* scoping, which is far more binding than the
   keeper's actual construction (5,494.7 MW mean, 3,764.5 MW annual minimum). There is no
   shortage anywhere in the year for the overlay to find.

**Verdict: `G` (governance-refused/closed by the rule-19 guard)** — the same verdict
`nyiso_rcpf_postsolve_overlay` carries in NYISO, for the same structural reason.

**Rule 28(c) hygiene gap CONFIRMED:** `grep neiso_rcpf docs/codebase-site/data/mechanism-matrix.js`
returns **zero** — a solve-affecting `ScenarioConfig` field with no matrix row. The row is owed.

---

## 4. DIRECTION 3 — `neiso_dynamic_reserve_requirements`. **Blocker (a) FALSIFIED; the
mechanism moves partly the WRONG WAY.**

### 4.1 Blocker (a) — the coverage limit is spent, and the data is reachable. **MEASURED.**

`data/raw/NEISO-AS/requirements/` holds **only a README** at this head; the 75 window CSVs are
gitignored and absent from disk. The README's stated policy is *"Coverage policy: train years
2023-2025 only (CLAUDE.md rule 22 — no out-of-training intake without explicit owner
authorization)."*

**Rule 22 `[R-HOLDOUT]` was REMOVED on 2026-09-09.** *"Any year may now be solved, scored and
registered with no authorization, no marker and no one-shot."* The policy sentence is a dead
citation; nothing governs the coverage any more.

And the data is reachable **from this container, for the years that matter**. Probed directly
through `scripts/data/fetch_neiso_reserve_requirements.py` (a bare `curl` 403s — the script
bootstraps the `isox_token` session itself, which is why the 403 is not the blocker it looks
like):

```
session bootstrap: OK
2022 window 2022-12-16..2022-12-31: OK 54206 bytes
2020 window 2020-01-01..2020-01-15: OK 51185 bytes
```

**The rule-34(c) all-years blocker on this mechanism is removable by a plain download.** The
loader hard-errors on a missing year by design, so today a six-year armed span cannot solve at
all; after a `--years 2020 2021 2022` intake it can.

### 4.2 Blocker (b), and a correction to the charter's arithmetic

The charter sizes this as *"+500 MW of a 3,359 MW gap — material but not sufficient alone."*
The measured record says the sign is not uniform. ISO-NE ROS (location 7000), Dec 2022:

| product | measured mean (Dec 16-31) | measured mean at Elliott | measured max at Elliott | model static | Elliott delta |
|---|---:|---:|---:|---:|---:|
| Ten-Minute Spinning | 398.1 | 384.0 | 388.0 | **600** | **−212.0** |
| Ten-Minute (total) | 1,590.0 | 1,533.7 | 1,549.8 | **1,200** | +349.8 |
| TOTAL (30-minute) | 2,394.8 | 2,337.4 | 2,354.1 | **1,800** | +554.1 |

Two things the charter's framing misses:

1. **The spin requirement is LOWER than the static value the model enforces** (384 vs 600).
   Arming the measured series *loosens* that family.
2. **The published columns are NESTED, not additive** — `spin ⊆ ten-minute ⊆ TOTAL`
   (388 ≤ 1,549.8 ≤ 2,354.1). The model runs them as three separate balance rows whose static
   values sum to 3,600 MW, while ISO-NE's actual total operating-reserve requirement at Elliott
   peaked at **2,354.1 MW**. Measured against the model's *aggregate* posture the mechanism is a
   **1,246 MW LOOSENING**, not a +500 MW tightening.

Per family — the accounting that actually governs, since class-0 and class-1 draw separate `R`
pools — the increments are +349.8 and +554.1 MW against a class-0 supply of **6,959.1 MW** and a
class-1 supply of **5,217.5 MW** at Elliott. **It does not come close to binding alone**, which
confirms the charter's own warning while correcting its sizing.

### 4.3 Blocker (c), the summer-tail objection from neiso-57, is NOT retired here

Not measured this session (it needs the 2023-2025 intake regenerated). It stands as an open
objection against arming this mechanism on its own.

**Verdict: stays `R`, with NEW evidence against a DIFFERENT target than neiso-57's.** Not a
re-test of an adjudicated cell (rule 28(a)): neiso-57 tested it as a price-formation lever; this
is a sizing measurement against the C3c tail, and the sizing is negative on its own.

---

## 5. WHAT PHASE 0 ACTUALLY FOUND — THE RESERVE SUPPLY SIDE IS THE DEFECT

### 5.1 NEISO reserve eligibility is a fuel-name test with no physics in it

`model/reserves/spec.py::_neiso_design` closes with exactly two masks:

```python
full_elig  = _reserve_eligible(fleet_arrays)     # np.isin(fuel, {gas_cc,gas_ct,gas_st,coal,nuclear,oil})
quick_elig = _quick_start_eligible(fleet_arrays) # np.isin(fuel, {gas_ct, oil})
```

and the LP row (`model/lp/reserve_rows.py::_build_reserve_rows`) is

```
sum_{class-c eligible g in z} P[g,t] + R[c,z,t] <= sum_{class-c eligible g in z} cap[g,t]
```

with `cap[g,t] = pmax[g] × availability[g,t]`. **Every unloaded MW on any reserve-fuel unit
counts, regardless of whether the unit is online, how long it takes to start, or how fast it
ramps.** A cold combined-cycle with a 4-12 h start contributes its full nameplate to ISO-NE's
**thirty-minute** operating reserve; a cold oil boiler contributes its full nameplate to
ISO-NE's **ten-minute** reserve.

This violates the published product definitions ISO-NE actually enforces — TMSR is
*synchronized*, TMNSR is *offline fast-start fully loadable in ten minutes*, TMOR is
*reachable in thirty minutes* — and it is a rule 18 `[R-PHYSICS]` violation in form as well as
substance: the gate is a class/fuel tuple, not unit physics.

**The LP already carries the machinery, and NEISO passes none of it:** `_build_reserve_rows`
accepts `online_gated`, `online_rho`, `online_capacity_cap`, `reserve_supply_cap`,
`headroom_extra_cap`; `_build_reserve_rows_pergen` accepts `pergen_ramp10`. PJM
(`pjm_reserve_online_gated`, `pjm_reserve_online_rho`), MISO (`miso_reserve_online_gated`) and
CAISO (`caiso_reserve_online_scoped`, with a measured `ramp10`) all use them. NEISO has **no
member in that family at all**.

### 5.2 The measured decomposition at Elliott

Source: the neiso-110 screen bundle's `hourly/unit_hourly_2022.parquet` (per-unit `mw` and
`cap_mw`), recovered from shard sha `7b82a4c08039c04f348884dfad894e196a9a16fb`. The screen arm
differs from the keeper by **+0.00154 TWh of oil across six years**, so it is a valid sizing
basis; it is not the keeper and is not quoted as one.

Elliott minimum-headroom hour = **2022-12-26 17:00 (model hour 8633)**, class-0 headroom
**6,959.1 MW** — reproducing neiso-110's number exactly.

| component | MW | share |
|---|---:|---:|
| total available capacity (reserve fuels) | 18,680.7 | |
| dispatched | 11,721.6 | |
| **class-0 headroom** | **6,959.1** | 100 % |
|  — ONLINE (mw > 0; 281 units) | **73.3** | **1.05 %** |
|  — OFFLINE (mw = 0; 329 units) | **6,885.8** | **98.95 %** |

Offline headroom by class:

| class | MW |
|---|---:|
| oil (all) | 4,696.6 |
| gas_cc CC_REGULAR | 1,379.7 |
| gas_ct CT_PEAKER | 492.2 |
| gas_cc CC_CHP | 279.9 |
| gas_st ST_GAS | 17.2 |
| gas_ct CT_CHP | 12.1 |
| gas_st ST_CHP | 8.2 |

And the oil fleet split by **EIA-860 generator prime mover** (`eia860_generator_operable`,
joined on `(Plant Code, Generator ID)`; **100 % of oil units matched**):

| prime mover | offline headroom MW | ten-minute capable? |
|---|---:|---|
| **ST (steam boiler)** | **2,855.2** | **NO** — multi-hour cold start |
| GT (combustion turbine) | 1,587.2 | yes |
| IC (internal combustion) | 106.8 | yes |

**2,855.2 MW of oil-fired steam boilers are counted as ISO-NE TEN-MINUTE reserve, in every
hour of the year** (annual mean 2,860.1 MW, max 2,861.5 MW). That single line is the largest
identified defect in NEISO's reserve construction.

### 5.3 Why the headroom is 99 % offline — the deeper reading

A pure LP with no unit-commitment state loads every economic unit to its cap and leaves the rest
completely off. Real systems carry reserve as **part-load on committed units**; this model
carries it as **cold iron**. The 3,359 MW that neiso-110 measured as "clear of binding" is not
spare capability on running machines — it is 281 online units at their cap plus 329 units that
are not running at all.

That is why no derate can reach it (neiso-110's finding, now explained), and why the fix is on
the **eligibility** side rather than the **capacity** side.

---

## 6. SIZING THE CANDIDATE — HONESTLY, INCLUDING WHERE IT OVERSHOOTS

Define a **strictest-admissible** response scoping, zero free parameters, every input measured
or published: an offline unit contributes reserve only if it is fast-start (gas `CT_PEAKER` /
`CT_CHP` classes, or oil whose EIA-860 prime mover is `GT`/`IC`); online units contribute their
unloaded headroom. Applied to all 8,760 hours of 2022:

| class-0 (30-min) supply | mean MW | min MW | Elliott min MW |
|---|---:|---:|---:|
| as modelled | 9,736.2 | 3,764.5 | 6,959.1 |
| **response-scoped** | **2,520.3** | **1,494.9** | **2,271.6** |
| excluded (offline slow-start) | 7,216.0 | — | 4,687.5 |

| class-1 (10-min) supply | mean MW | min MW | Elliott min MW | hours < 1,200 |
|---|---:|---:|---:|---:|
| as modelled | 5,494.7 | 3,764.5 | 5,217.5 | **0** |
| **response-scoped** | **2,465.1** | **1,494.9** | **2,214.9** | **0** |

**Three things this says, and the third is the one that matters:**

1. **Scoping alone does not bind the ten-minute families.** Even at maximum strictness the
   class-1 supply never falls below 1,494.9 MW against a 1,200 MW requirement — zero short hours
   in 8,760. Removing 2,855 MW of oil boilers from the ten-minute class is a **correct rule-14
   `[R-ACCURATE]` repair that produces no scarcity hour by itself.** Same shape as neiso-110's
   result for the derate family, and it must be said plainly.
2. **Against the STATIC 1,800 MW the 30-minute family goes short in 27 hours of 2022 — none of
   them at Elliott** (Elliott scoped min 2,271.6 > 1,800).
3. **Against the MEASURED requirement it crosses at Elliott.** Scoped class-0 supply
   **2,271.6 MW** vs the measured 30-minute TOTAL requirement **2,354.1 MW** →
   **short by 82.5 MW** at the right hour of the right event. Neither half reaches it alone:
   scoping alone leaves +471.6 MW of slack, the measured requirement alone leaves +4,605.0 MW.

**The overshoot, stated rather than buried.** An earlier cut of this measurement compared the
scoped supply against a 3,600 MW "total requirement" and found the model short in **8,760 of
8,760 hours**. That comparator was **wrong** — the three families draw separate `R` pools and
ISO-NE's published columns are nested, not additive — and the corrected per-family accounting is
what §6 reports. It is recorded because it is exactly the trap the charter warned about, and
because the strictest scoping remains *stricter than ISO-NE*: the real TMOR product does credit
some offline resources reachable inside thirty minutes, so a properly designed mechanism will be
**looser than this measurement and may not cross the 82.5 MW margin.**

**This is sizing. It is not a prediction, and it is not a gate.**

---

## 7. WHAT I RECOMMEND, AND WHAT I DID NOT DO

**No mechanism was built and no LP was spent.** The candidate is off the charter's queue and
materially different from all three named directions, so the direction decision is the owner's
before any build (rule 1 `[R-STRUCT]` favours it; rule 28(a) permits going off-queue with a
stated reason, which §5 is).

The proposed lane, in order:

1. **Widen the measured requirement intake to 2020-2025** — `fetch_neiso_reserve_requirements.py
   --years 2020 2021 2022`, then `curate_reserve_requirements.py --isos NEISO`, and repair the
   README's dead rule-22 citation. Zero LP, proven reachable (§4.1), and it permanently removes
   the rule-34(c) blocker on direction 3.
2. **Build `neiso_reserve_response_scoping`** — a start-time / ramp gate on reserve supply keyed
   on unit physics (rule 18), never on fuel names: offline units contribute to a product only
   within their start time, online units at most their ramp over the product's response window.
   Default **off**, new `ScenarioConfig` field, new matrix row in the same PR (rule 28(c)).
3. **One shard, six years, one `--years 2020 2021 2022 2023 2024 2025` invocation**, pushing its
   full bundle including `dispatch/<year>_P1.parquet` (rules 32(b) / 34(a)). Budget ~15 min.

**A correction to the charter's discipline section, flagged rather than silently followed.** It
instructs *"Rule 29 `[R-SCREEN]`: zero-LP phase 0 → ONE-YEAR screen … → full span only if it
clears."* **That regime was REMOVED on 2026-09-16** (CLAUDE.md rule 29: *"THE SCREEN-YEAR REGIME
IS REMOVED. A new config goes STRAIGHT TO THE FULL SPAN"*), and rule 32(b) now bans the per-year
fan-out outright. The plan above follows CLAUDE.md at HEAD, not the charter's stale text. What
survives of rule 29 and is honoured here: clause (b) (no control solves — §1's G-DRIFT) and
clause (c) (nothing reaches `main` that should not).

---

## 8. WHAT THIS SESSION DOES NOT CLAIM

* It does **not** claim the scoping mechanism will produce a scarcity hour. §6's 82.5 MW crossing
  is under a scoping stricter than ISO-NE's own product definitions, and a correct design will be
  looser.
* It does **not** re-adjudicate `dynamic_reserve_requirements` as promotable. §4 measures it as
  insufficient alone and partly loosening; the neiso-57 summer-tail objection is untouched.
* It does **not** measure the 2023-2025 requirement series (not regenerated this session), so
  the seasonality of the measured requirement is unquantified here.
* The Elliott decomposition rests on the neiso-110 **screen arm**, not the keeper. The two differ
  by +0.00154 TWh of oil over six years; that is stated at every use rather than glossed.

---

## 9. ARTIFACTS, RETRIEVABILITY, AND THE PROMOTION QUESTION (rules 31 / 34)

**Nothing was solved, so there is nothing to promote and nothing to retain.** No bundle was
produced, no registration is owed, and rule 31 `[R-RETAIN]` has nothing to protect. No shard was
launched, so rule 33 `[R-SHARD-ARCHIVE]` has nothing to sweep.

The keeper `2026-09-16-neiso110-dualfuel-derate-scope` is **unchanged** and remains NEISO's
designated keeper across all six years {2020, 2021, 2022, 2023, 2024, 2025}.

**The open question for the owner is a DIRECTION question, not a promotion question:** build the
reserve response scoping of §5-§7, or stay on the charter's queue.
