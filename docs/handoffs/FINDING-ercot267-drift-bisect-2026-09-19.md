# FINDING — the ERCOT engine drift is **SOCO-15's COD-ramp regrain** (`9398000db`, merged `a0bcb04f93`, PR #6123). **HEAD IS CORRECT. NOTHING IS OWED.**

**Session:** ercot-267 (parent/orchestrator), 2026-09-19. Branch
`claude/ercot-engine-drift-bisect-2z2z1a`.
**Predecessor:** `docs/handoffs/RESULT-ercot-mer-keeper-resolve-2026-09-19.md` — the run that
found the drift and correctly stopped at "report and stop" (its sealed prediction P4).
**ZERO LP SOLVED.** Every number below comes from `run_year(fleet_only=True)` rebuilds
(~90 s each) and from git. No shard was launched (rule 32 `[R-SHARD]` (a) never had to bind).

---

## Headline

1. **The commit is named and bisected, not guessed.** `9398000db` *"SOCO-15: resolve the COD
   ramp at the LP unit's own grain (owner card S12)"*, merged as `a0bcb04f93` (PR #6123,
   2026-09-13 11:11:36 -0700). The immediately preceding merge `6d8dd509b2` (11:06:34, five
   minutes earlier) is clean. One commit, one clean step, two distinct hashes across the whole
   window.
2. **What it moves is `availability` and `min_gen` — NOT the plant→class map.** The
   RESULT doc's reading ("a plant→class MAPPING change, not the LP dispatching differently")
   is **REFUTED by direct measurement**: the `unit_id → plant_group` map is **bit-identical at
   both shas in all five years, zero units re-classed**. The class-energy swaps it saw are the
   LP re-dispatching around a changed availability envelope, which is what those aggregates
   look like either way.
3. **The leading candidate in the handoff is EXONERATED, by measurement.** `760012f7` (EIA-860
   vintage cache keying) is inert for ERCOT twice over: the keeper carries
   `eia860_vintage_tracks_solve_year = False`, under which that commit is a strict no-op by its
   own construction; and it is an **ancestor of bisect index 72, which was probed and is GOOD**,
   so it demonstrably moves nothing. The same holds for every other candidate the handoff named.
4. **2025 is explained, and it is the proof.** SOCO-15 moves ERCOT 2025's availability by
   **max |Δ| = 4.44e-16 — one ULP — with the array sum changing by exactly 0.0**, which is why
   the one year the re-solve reproduced byte-exactly on all 61,320 zone-hours is that one. One
   cause accounts for all five years, including the null.
5. **HEAD is correct and the keeper is already on it, so NO RE-SOLVE IS OWED.** The repair
   replaces an *estimate* (a plant-collapsed capacity-weighted mean COD) with a *measurement*
   (each unit's own EIA-860 Operating Year/Month; for a CAMPD bin, its constituents' measured
   monthly online-capacity fraction). That is rule 14 `[R-ACCURATE]` on its own terms, and the
   accuracy moved the right way in 3 of the 4 affected years. **The drift is closed.**
6. **Two defects found on the way in, both outside this lane to fix, both stated here rather
   than buried**: the superseded keeper's recorded solve sha is **false** (§6), and a
   cross-ISO, deliberately results-moving change landed with **every cache key byte-identical
   and no solve epoch** (§7) — which is the mechanism by which this became invisible.
7. **And one live consequence for other lanes: PJM's and CAISO's designated keepers were both
   solved BEFORE this commit** and carry the superseded construction, so form 4 differencing is
   suspect for them in exactly the way it was for ERCOT (§8). Unmeasured there, not assumed.

---

## 1. The mechanism, in one paragraph

`cod_ramp.effective_cod` let the **plant-collapsed capacity-weighted mean COD** win a
generator's ONLINE date; the per-unit preference existed only for retirement. SOCO-15 replaced
it with `generator_online_mask`, under which (a) a raw EIA-860 unit keeps its own
`Operating Year`/`Operating Month`, and (b) **a plant-level CAMPD bin — which is what every
ERCOT LP thermal unit is, since the ERCOT default is `use_campd_bins=True` — takes the
nameplate-weighted monthly online *fraction* of its `(plant, group)` constituents.** Two
consequences fall straight out of that and are exactly what was measured: the online mask stops
being all-year-or-nothing and becomes **fractional**, so the change is not confined to a unit's
COD year; and `min_gen` is now **scaled by the same mask** where it was previously **zeroed in
offline months**, which is why both arrays moved together.

The commit's own message is unambiguous that this was intended:
> *"No ScenarioConfig field, no default flip, no cache.py edit: every registered keeper's cache
> key is byte-identical (gate G8) **and results move — that is the point.**"*

So this is not a regression that slipped in. It is a deliberate construction repair whose
blast radius on the other eight regions' committed keepers was not carried to those lanes.

## 2. How it was found (method, and why it cost no LP)

Four instruments, each narrower than the last, all in the parent:

1. **`scripts/probes/_ercot267_drift_bisect.py`** — two `run_year(fleet_only=True)` rebuilds
   per year of the keeper's own recipe, `market_sim` imported from a sparse worktree at each
   sha, `data/` shared by symlink so both arms read identical bytes off disk and any difference
   must come from code. Differenced by sha256 over the raw bytes of every LP-visible fleet
   array, **plus** the renewable/storage/fuel-price state arrays (renewables are decision
   variables, rule 3 `[R-RENEW-VAR]`, so their CF arrays are LP inputs), **plus** the
   `unit_id → plant_group` map and a per-class census. Adapted from the CAISO ancestor
   `_caiso255_gdrift_identity.py`, with the ERCOT three-config partition overlay applied per
   year (`replay_keeper.config_partition_overlay`) — without it a rebuild solves the forward
   config on a carve-out year, the ercot-259 defect.
2. **`scripts/probes/_ercot267_input_at_sha.py`** — the same measurement at ONE sha, cached by
   `(sha, year)`, with per-class attribution.
3. **`scripts/probes/_ercot267_bisect_driver.py`** — binary search on the `availability` hash
   over the 157 first-parent commits in `0ebfc2da0..5926ca52` that touch `src/` or `scripts/`
   (the only commits that CAN move a rebuild, since `data/` is shared). **Seven probes.**
4. **`scripts/probes/_ercot267_cod_unit_delta.py`** — the found commit's effect resolved to the
   individual LP unit and the calendar month, which is what turns "a number moved" into "these
   three plants, in these months, for this reason" (§4).

The search log, verbatim:

```
good 0ebfc2da0 availability=9787d8698d6b685f6259cbfb
bad  5926ca52 availability=33208ae82c6e0323827914be
157 code-touching first-parent commits in range
  [ 78/156] 39a1c9a182 BAD   | Merge pull request #6129 ...
  [ 39/156] 60b3aff6df GOOD  | Merge pull request #6003 ...
  [ 59/156] 8f1e9135e0 GOOD  | Merge pull request #6078 ...
  [ 69/156] 33a7c9615f GOOD  | Merge pull request #6106 ...
  [ 74/156] e028ce2309 BAD   | Merge pull request #6124 ...
  [ 72/156] 6d8dd509b2 GOOD  | Merge pull request #6117 ...
  [ 73/156] a0bcb04f93 BAD   | Merge pull request #6123 .../claude/soco-15-spp-arm
```

**Only two distinct availability hashes appear anywhere in the window**, and every probed sha at
or after index 73 carries the endpoint's hash, so the transition is a single commit and there is
no second mover to look for. The same search run on **2025** lands on **the same commit**.

That also settles the handoff's other named candidates **by measurement rather than argument**:
`760012f7`, `eaa9d6f1`, `ee40acd2`, `26f8508b8` (the `classify_plant` pumped-storage change) and
`6b82b833f` (the host-steam cogen partition) are all ancestors of index 72, which was probed and
is GOOD — none of them moves ERCOT's availability at all.

A note on the control the bisect used, because it is not the one the handoff names: the
superseded keeper's recorded sha `6bc43501` **cannot** build its own recorded recipe (§6), so
the "good" endpoint is `0ebfc2da0` — the earliest sha at which the keeper's declared recipe is
expressible at all — and the recipe is its own `meta.json` with the receipts-fallback key routed
through `prb_overrides`, the channel both shas understand.

## 3. The measurement

`availability` and `min_gen` are `(n_gen, 8760)`; the sums below are MW-hours over the whole
array, at `6d8dd509b2` (PRE) and `a0bcb04f93` (POST) — the two sides of the bisected step.

| year | availability PRE | availability POST | Δ | Δ% | min_gen Δ | Δ% |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 14,561,459.1 | 14,476,262.0 | **−85,197.1** | −0.585 % | −258,603.6 | −0.294 % |
| 2022 | 15,580,033.2 | 15,513,478.8 | **−66,554.4** | −0.427 % | −267,594.8 | −0.299 % |
| 2023 | 16,135,889.9 | 16,095,614.7 | **−40,275.2** | −0.250 % | −78,760.0 | −0.085 % |
| 2024 | 16,039,805.3 | 16,000,425.5 | **−39,379.7** | −0.246 % | −8,089.2 | −0.009 % |
| 2025 | 15,652,808.2 | 15,652,808.2 | **0.0** (exactly; max cell Δ 4.4e-16, §5) | **0.000 %** | **0.0** | **0.000 %** |

**Every class that moves is a CHP class or CT_PEAKER; every other class moves by exactly zero
in every year** — COAL, CC_REGULAR, ST_GAS, ST_CHP, hydro and the unclassed remainder are
bit-identical throughout.

| year | classes that moved (availability Δ, % of class) |
|---|---|
| 2021 | CC_CHP −33,690.7 (−1.818 %); CT_CHP −47,322.0 (−3.869 %); CT_PEAKER −4,184.4 (−0.115 %) |
| 2022 | CC_CHP −33,690.7 (−1.890 %); CT_CHP −47,322.0 (−3.876 %); CT_PEAKER +14,458.2 (+0.341 %) |
| 2023 | CT_CHP −47,322.0 (−3.883 %); CT_PEAKER +7,046.8 (+0.144 %) |
| 2024 | CT_CHP −16,042.5 (−1.319 %); CT_PEAKER −23,337.2 (−0.471 %) |
| 2025 | *(none)* |

**This reproduces the drift's own class signature.** The RESULT doc's dominant energy moves were
2021/2022 `CC_CHP ↔ CC_REGULAR` with `CT_CHP` falling, and 2023/2024 `CT_CHP` and `CT_PEAKER`
falling into `CC_REGULAR`/`ST_GAS`. The classes losing *availability* here are precisely the
classes losing *energy* there, year for year, and the classes gaining energy are the ones whose
availability never moved — i.e. the LP re-dispatching onto unchanged capacity. That is the
mechanism, not a coincidence of sign.

**Direction and magnitude are consistent with the price move.** Availability falls 0.25–0.59 %,
concentrated in cheap CHP capacity that sits low in the ERCOT merit order, so the marginal unit
is more expensive more often and the load-weighted price rises — which is the sign the re-solve
measured (2021 +0.6332, 2022 +0.2855, 2023 +3.6060, 2024 +0.1296 $/MWh) and the reason 2023
moves most (−3.88 % of CT_CHP with no offsetting CC_CHP change).

## 4. WHY THE REPAIR IS A REPAIR — three real plants, named

In 2023 exactly **46 of 2,323 LP units move, and they belong to three plants**. Not a fleet-wide
derate wearing a COD costume: three multi-vintage Houston plants, each disagreeing with its own
plant-collapsed mean in the way the repair predicts.

| plant | EIA-860 constituents (own COD) | plant-mean COD (the OLD input) | measured Δ in 2023 |
|---|---|---|---|
| **57504 TECO CHP-1** (CT_CHP) | CHP1 48.0 MW **2010-09**; GTG2 50.0 MW **2024-05** | ≈2017 | **−3,943.5 per tranche, all 12 months** |
| **65373 Brotman Power Station** (CT_PEAKER) | CTG-1…6 60.5 MW **2023-05**; CTG-7/8 60.5 MW **2023-10** | ≈2023-06 | **−164.6 per tranche, months 5–9 ONLY** |
| **65372 Mark One Power Station** (CT_PEAKER) | CTG-1…6 60.5 MW **2022-11**; CTG-7/8 60.5 MW **2024-10** | ≈2023-05 | **+579.1 per tranche, all 12 months** |

Read them in order, because together they are the whole argument:

* **TECO CHP-1** had 48 MW in 2023 and 98 MW from May 2024. The old construction put the
  **whole 98 MW** on the 2023 grid from the plant mean — capacity that did not exist. The
  reduction is flat across all twelve months because GTG2 is absent from *every* month of 2023.
  That is not a ramp; it is capacity that was never there.
* **Brotman** genuinely commissioned mid-year: six units in May 2023, two more in October. The
  delta is confined to **months 5–9** — precisely the window where "the whole plant from the
  plant mean" and "the constituents that had actually reached commercial operation" disagree.
  Before May both constructions say zero; from October both say 484 MW.
* **Mark One** moves the **other way, +579.1**: six units were running from November 2022, but
  the two 2024 units drag the capacity-weighted plant mean out to ~May 2023, so the old
  construction held 363 MW of real, operating capacity offline for four months of 2023. **A
  repair that raises availability at one plant and lowers it at another, each on that plant's
  own published vintages, is not something a fitted derate can do.**

This is the failure the commit's own message names (Vogtle 3: own COD 2023-07, plant mean
2005-05, read as online all twelve months of 2023), reproduced in ERCOT with ERCOT's plants.

## 5. Why 2025 is byte-exact — measured at full precision

Every ERCOT bin's constituents resolve to an online fraction of 1 in every month of 2025, so
there is nothing for the regrain to change. What remains is arithmetic: the new code multiplies
`availability` by a *computed* fraction where the old code multiplied by a literal mask, and a
fraction that equals 1 only to within a rounding error is not bit-identical to 1.

Measured on the raw `(2310, 8760)` float64 arrays at `6d8dd509b2` vs `a0bcb04f93`:

```
cells differing: 753,360 of 20,235,600
max abs delta:   4.440892098500626e-16      (one ULP)
max rel delta:   5.328704605033957e-16
sum delta:       0.0                        (exactly)
```

So the sha256 moves and the model does not. **This is the loose end the earlier five-year sweep
surfaced** — 2025's array hash differed across the full window — and it is closed rather than
waved through: there is no second mover, the same commit is responsible, and its 2025 effect is
one unit in the last place. A cause that did not also predict the null would not be the cause.

*(Worth knowing for the next lane, not a defect here: because ERCOT carries
`eia860_vintage_tracks_solve_year = False`, a 2023 solve reads the current EIA-860 directory,
which already knows GTG2 comes online in 2024. The repair uses that knowledge to EXCLUDE
not-yet-built capacity, which is the correct direction and regenerates forward from the
then-current 860 (rule 13 `[R-MEASURED]`). Whether a backcast year should read its own vintage
at all is the separate, registered `eia860_vintage_tracks_solve_year` mechanism, untouched here.)*

## 6. THE SUPERSEDED KEEPER'S RECORDED SOLVE SHA IS FALSE

Found while building the control, and it invalidates the window the predecessor bisected over.

All four `run_config*.json` in `results/calibration/ercot265_receipts_five_year` record
`git.sha = 6bc43501`, `basis_sha = 6bc4350111df…`, `dirty = false`, `changed_files = []` — **and**
`scenario_config.ercot_ep_gas_basis_receipts_fallback = true`. That field **does not exist
anywhere in `src/` or `scripts/` at `6bc43501`**: `git grep -c` returns zero hits at that sha
and four in `scenarios.py` at `0ebfc2da0`, the commit that introduced it
(*"ercot-265: receipts fallback for the corroboration filter"*, 2026-09-09 20:23 UTC), which is
**not an ancestor of `6bc43501`** (2026-09-09 04:09 UTC). A run cannot have armed a flag its
tree did not contain.

What actually happened is visible in the blobs. Comparing `ercot261_five_year_keeper` against
`ercot265_receipts_five_year` at `c79e89ef8`: of 38 files, **24 are byte-identical and the 14
that differ are the six 2021 sidecars plus every metadata file.** ercot-265 re-solved 2021
alone, carried the incumbent's 2022–2025 sidecars forward unchanged, and **rewrote all four
`run_config*.json` to assert `receipts_fallback = true` while keeping the incumbent's
`git_sha`.** So the committed record describes a code tree that solved none of its years under
the recipe it claims:

* for **2022–2025**, the flag is asserted of legs solved at `6bc43501` where it did not exist
  (harmless in effect — ercot-265 measured the fallback byte-identical outside 2021, and the
  2025 byte-exact reproduction confirms it independently — but false as a record);
* for **2021**, the sha is asserted of a leg solved at some later tree carrying `0ebfc2da0`.

**Consequence for the predecessor's work, stated plainly:** the "~25 commits in
`6bc43501..HEAD`" enumeration started ~16 h and at least one ERCOT-solve-path commit *before the
keeper existed*. The bisect above is unaffected — it uses `0ebfc2da0` as its good endpoint and
lands on a commit five days later — but any future lane differencing against that record should
know the sha is not usable.

**Not repaired here.** The bundle is pruned (rule 35 `[R-PROMOTE]` (a), executed at the
2026-09-19 promotion) and the current keeper's own record is clean: `5926ca52` genuinely
contains everything `ercot_mer20260919_five_year` records. What is owed is the *general* fix —
a composition that inherits another run's legs must not inherit its `git_state()` — and that
belongs with whoever owns `run_calibration_full`'s bundle composition, not this lane.

## 7. THE GOVERNANCE GAP THAT MADE IT INVISIBLE

SOCO-15 moved every region's results while leaving **every cache key byte-identical**, by
design and stated in its own message. Two safety nets exist for exactly this and neither caught
it:

* **`cache_key()`'s solve-surface fingerprint** (capx D79) covers the seven
  `config/solve_surface.py::SURFACE_MODULES` — the config registry modules. `data/cod_ramp.py`
  and `data/fleet/arrays.py` are **not** among them, and by construction cannot be: the seven
  "import nothing but each other and stdlib, and none reads a file at import", which is what
  makes the fingerprint reproducible from source alone. ERCOT's fingerprint is
  `5ab10cf3fa2f1447` in the superseded keeper and `5ab10cf3fa2f1447` in the new one — identical
  across the change, correctly and uselessly.
* **`SOLVE_EPOCHS`** is the ledger that module's own docstring introduces as *"a mechanical,
  SCOPED epoch ledger for the **code-level changes a value hash cannot see**"*. It is
  `SOLVE_EPOCHS: tuple[SolveEpoch, ...] = ()` — **empty**. It has never been used.

So a deliberately results-moving code change re-used every ISO's cached solves and left every
committed keeper silently unreproducible. **This is the first measured instance of the exact
failure `SOLVE_EPOCHS` was built for, and it is the recommendation this finding carries
forward**: SOCO-15 warranted an epoch entry, and the absence of one is why four ISO-years of
drift had to be found by a price residual ten days later instead of by a changed cache key on
the day.

## 8. CROSS-ISO EXPOSURE — **PJM AND CAISO ARE OWED THE SAME NOTICE**

SOCO-15 is not ERCOT-scoped; its own message says *"one shared seam, the same construction on
every fleet path (rule 25)"*. Every designated keeper's solve timestamp against the merge
(2026-09-13 18:11 UTC):

| ISO | keeper | solved | sha | side |
|---|---|---|---|---|
| **PJM** | `2026-09-11-pjm-d4-4-gasoutage` (+ its holdout touchpoint) | 2026-09-11 | `f09eddbe` | **PRE** |
| **CAISO** | `2026-09-12-caiso-275-gascoupling` (+ `-2022`) | 2026-09-12 | `b8ddf8bc` | **PRE** |
| NEISO | `2026-09-16-neiso110-dualfuel-derate-scope` | 2026-09-16 | `c0916408` | post |
| SPP | `2026-09-16-spp-42-commitment-feasibility` | 2026-09-16 | `1f586ed7` | post |
| NYISO | `2026-09-17-nyiso240-bench-attribution` | 2026-09-17 | `3edb8ad8` | post |
| ERCOT | `2026-09-19-ercot266-mer-five-year` | 2026-09-19 | `5926ca52` | post |
| MISO | `2026-09-19-miso-262-cold-year` | 2026-09-19 | `4583e70b` | post |
| NWPP | `2026-09-19-nwpp41-coal-taxonomy-own` | 2026-09-19 | `f932a881` | post |
| SOCO | `2026-09-19-soco53d-campaign-commitment` | 2026-09-19 | `0b3f2fdc` | post |

**PJM's and CAISO's committed keepers carry the superseded COD construction**, so rule 29
`[R-SCREEN]` (b) form 4 — "the incumbent keeper's committed bundle IS the control" — is
**suspect for those two ISOs** in exactly the way it was for ERCOT until this week's promotion.
The size of the effect is **unmeasured** outside ERCOT and is not assumed: PJM and CAISO are
EIA-860 per-plant fleets, so they are exposed through the *first* limb (a unit keeps its own
Operating Year/Month) rather than ERCOT's bin-fraction limb, and the magnitudes need not be
comparable. Each lane should run this finding's probe on its own keeper before spending a
control solve. **No ISO's keeper is invalidated by this finding** — the same posture rule 36
`[R-YEAR-ISOLATION]` (f) takes about its own artifact.

## 9. IS HEAD CORRECT? **YES — AND THE ANSWER DOES NOT REST ON THE RESIDUAL**

Rule 14 `[R-ACCURATE]` decides this and it decides it on construction, before any price is
looked at:

* **the old value is an estimate**: a plant-collapsed capacity-weighted mean COD, standing in
  for units that do not share a commissioning date;
* **the new value is a measurement**: each unit's own EIA-860 `Operating Year`/`Operating
  Month`, and for a CAMPD bin the nameplate-weighted online-capacity fraction of its own
  constituents, read from the same operable sheet at the same vintage;
* **the failure mode the repair names is real, and in ERCOT it is three named plants** (§4):
  TECO CHP-1 carrying 50 MW that would not exist until May 2024; Brotman's mid-year
  commissioning smeared onto the wrong months; Mark One's six operating units held offline for
  four months by two siblings that arrive in 2024. Each is checkable against the published
  EIA-860 operable sheet, and the correction runs in both directions.

The accuracy evidence is **corroboration, cited second and deliberately not as the reason**
(rule 1 `[R-STRUCT]`): C3a mean LMP moved toward actual in three of the four affected years
(2023 −6.5 % → −0.9 %, 2024 −0.3 % → +0.1 %, 2022 −8.1 % → −7.7 %) and slightly away in one
(2021 +5.6 % → +6.0 %). Had it moved the other way the verdict would be the same, and the right
response would be rule 14's own — keep the accurate input and open a root-cause investigation on
whatever the estimate had been silently compensating for.

**So the drift is not to be reverted, and there is nothing to fix.** The ERCOT keeper
`2026-09-19-ercot266-mer-five-year` was already solved at `5926ca52`, i.e. **on the repaired
construction**, so its published numbers are the correct ones and no re-solve is owed. Rule 29
`[R-SCREEN]` (b) form 4 is valid for ERCOT, which the promotion had already restored; this
finding says *why* it had stopped being valid, which is what the open item asked for.

## 10. What this finding does NOT claim

* **No re-score, and none needed.** The keeper's gates were scored at promotion
  (C1/C2/C3a/C3b/C4/C6/C8 PASS, C3c the lone ledgered caveat, CALIBRATED) and nothing here
  moves a number in that bundle.
* **No claim about the size of the effect in any ISO but ERCOT** (§8).
* **No claim that SOCO-15 is the only commit in the window that touches any ERCOT LP input** —
  only that it is the only one that moves `availability` or `min_gen`, which the
  two-distinct-hash result establishes for 2021–2025 alike. Every other LP-visible array the
  instrument covers (`pmax`, `pmin`, `mc_base`, `heat_rate`, `emission_rate`, `nox_rate`,
  `so2_rate`, `vom`, `zone_idx`, `fuel_type_idx`, `plant_code`, `plant_group`, `state`,
  `ramp10`, `efficiency_bin`, `unit_ids`) and every state array (`demand`, `wind_cf/cap/mc`,
  `solar_cf/cap/mc`, `storage_power_cap`, `fuel_prices`) is **bit-identical end to end**.
* **LP construction and solve are not covered by the instrument.** A `fleet_only` rebuild exits
  before them. That is not a gap here — the inputs *did* differ, and the difference fully
  accounts for the drift — but a future lane whose inputs come back identical must look there.

## 11. Settled by this finding, and closed

| open item | status |
|---|---|
| Bisect the drift; name the commit | **DONE — `9398000db` / `a0bcb04f93`, PR #6123** |
| Is HEAD correct? | **YES, rule 14. No re-solve owed; keeper already on it** |
| `760012f7` as leading candidate | **EXONERATED** — inert under `eia860_vintage_tracks_solve_year=False`, and on the wrong side of the transition |
| "plant→class mapping change" hypothesis | **REFUTED** — zero units re-classed in any year |
| `eaa9d6f1` / `ee40acd2` LP memory hygiene | **RULED OUT by measurement** — both are ancestors of the probed GOOD index 72 |
| 2023's magnitude "may be a second effect" | **NO** — one commit, one step; 2023 is largest because CT_CHP falls 3.88 % with no offsetting CC_CHP move |
| 2025's array hash differing over the full window | **CLOSED** — same commit, one-ULP arithmetic, sum delta exactly 0.0 (§5) |

## 12. Still open, NOT this lane's, and not blocking

* **The bundle-composition sha defect** (§6): a composed bundle inherits another run's
  `git_state()`. Owner: `run_calibration_full` composition.
* **`SOLVE_EPOCHS` is empty** (§7): the ledger for code-level solve changes has never been
  used, and this is the first measured case that needed it.
* **PJM and CAISO keeper reproducibility** (§8): unmeasured, one probe run each.
* Inherited from the predecessor and untouched here: the MER dual's memory headroom on
  per-plant MISO/PJM, 2024's −7.7000 tCO2/MWh MER minimum, and `tzdata` missing from the
  runtime deps (hit again in this session — `uv pip install tzdata` was required).

---

## Reproduce

```bash
uv sync --no-dev && uv pip install tzdata
python3 - <<'PY'   # the control recipe: the superseded keeper's meta, receipts key re-routed
import json
o = json.load(open("<superseded meta.json from git>"))
n = json.load(open("results/calibration/ercot_mer20260919_five_year/meta.json"))
o["gas_prices"] = n["gas_prices"]; o.pop("model_changes_note", None)
o["coal_prb_sigmoid_overrides"]["ercot_ep_gas_basis_receipts_fallback"] = o.pop(
    "ercot_ep_gas_basis_receipts_fallback")
json.dump(o, open("/tmp/control_meta.json", "w"), indent=1, sort_keys=True)
PY
PYTHONPATH=.:src uv run python scripts/probes/_ercot267_drift_bisect.py \
    --keeper-sha 0ebfc2da0 --head-sha 5926ca52 --meta /tmp/control_meta.json
PYTHONPATH=.:src uv run python scripts/probes/_ercot267_bisect_driver.py \
    --good 0ebfc2da0 --bad 5926ca52 --year 2023 --meta /tmp/control_meta.json
PYTHONPATH=.:src uv run python scripts/probes/_ercot267_cod_unit_delta.py \
    --pre 6d8dd509b2 --post a0bcb04f93 --year 2023 --meta /tmp/control_meta.json
```

`_ercot267_bisect_driver.py` caches every rebuild by `(sha, year)`, so re-running it or
re-pointing it at another year costs only the probes it has not already made. Run it on `--year
2025` to reproduce the null, and `_ercot267_cod_unit_delta.py --year 2025` to see zero of 2,310
units move.

The superseded keeper's `meta.json` is recoverable at
`git show b0639b758^:results/calibration/ercot265_receipts_five_year/meta.json`.
