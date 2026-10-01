# FINDING — SPP-37 card A: the span/single-year divergence is an **EIA-860 vintage cache leak**. Years 2+ of every SPP span solve on a STALE fleet snapshot.

**VERDICT (one line): SPP-36's divergence is not run-to-run variation and not a
single-year artifact — years 2 and 3 of an SPP span run compute their unit-outage
denominator and their CC duct-peaking offer band from YEAR 1's EIA-860 vintage,
because those loaders are `lru_cache`d on keys that omit the vintage; the
SINGLE-YEAR leg is the correct one and the SPAN — which is what every SPP keeper
is — is wrong for 2024 and 2025.**

Lane SPP-37 · base `origin/main` @ **`9ae27cd7fca1e401c3a977eb0f86383242ad2090`** ·
branch `claude/spp-37-order-sensitivity-0am7xy` · **parent LP: ZERO. Shards launched: ZERO.**
Card A closed at phase 0, with no solve spent and none needed.

Probe (re-runnable, read-only): `scripts/probes/_spp37_vintage_cache_census.py`.

---

## 1. WHAT SPP-36 OBSERVED, AND WHY THE PROPOSED SOLVE WOULD HAVE MISSED IT

`docs/RESULT-spp-36-shortwindow-span-2026-09-12.md` §4 and
`docs/handoffs/SHARDREPORT-spp36-span.md` §5 recorded that a 3-year span invocation
does not reproduce three single-year invocations of the same recipe: **2023 matched
to 4 dp, 2024 and 2025 did not.** Warm-start, fleet evolution, config partition,
the derate input and the offer curve were all correctly ruled out there.

This lane's charter proposed, if phase 0 found a live candidate, one shard
re-solving keeper 10's recipe and checking byte-identity against the committed
bundle. **That test would have PASSED and been misleading.** The span path is
perfectly deterministic — it reproduces itself exactly — and it is *also* wrong.
The defect is not non-determinism; it is **order-dependence**, and byte-identity
against a bundle produced in the same order cannot see it. The zero-LP
enumeration the charter asked for first is what found it.

## 2. THE MECHANISM

SPP keeper 10 carries **`eia860_vintage_tracks_solve_year = True`**
(`results/calibration/spp36_span/run_config.json`). `run_calibration.run_year`
therefore calls `paths.set_eia860_vintage(year)` on **every** year, and the
process-global `_ACTIVE_EIA_860_DIR` moves across the span:

| solve year | active EIA-860 directory |
|---|---|
| 2023 | `data/raw/eia-860/vintage_2023/` |
| 2024 | `data/raw/eia-860/vintage_2024/` |
| 2025 | `data/raw/eia-860/` (no `vintage_2025/` is committed — falls through to canonical) |

The LP's own fleet follows that correctly: `load_fleet_from_csv` is **not** cached,
so each year builds from its own vintage.

Several `lru_cache`d loaders read the same global but **do not carry it in their
cache key**. The first year of a span pins its vintage's value for every later
year. Numerator and denominator then sit on different EIA-860 vintages — the exact
defect `outages._iso_plant_capacity`'s own docstring says must never happen:

> *"this denominator has to be THE SAME capacity the derate multiplier is applied
> to in the LP."*

**Year 1 is always correct (cold cache); years 2+ are not.** That is precisely the
observed signature, and it is why 2023 reproduced and 2024/2025 did not.

The repo already knows this hazard and has the correct pattern in four places —
`cod_ramp._load_cod_map(eia860_dir)`, `chp._chp_by_plant(eia860_dir, year)`,
`eia860._cc_steam_part_generators(eia860_dir)`, `eia860._eia860_plant_sectors(eia860_dir)`
all key on the directory. The leaking loaders simply do not.

## 3. THE CENSUS — eleven vintage-blind caches, two live on SPP's keeper path

Measured across SPP's three vintages (probe §2). "LEAKS" means the value actually
moves, so the stale entry is a wrong answer rather than a harmless re-use.

| cached loader | key | moves? | reached by SPP keeper 10? |
|---|---|---|---|
| `outages._iso_plant_capacity` | `(iso, 2 bools)` | **LEAKS** | **YES — both outage overlays** |
| `campd_bins.cc_duct_peaking_pct` | `(row_scoped)` | **LEAKS** | **YES — `cc_duct_peaking=True`** |
| `outages._iso_plant_unit_capacity` | `(iso, bool)` | LEAKS | no (`unit_outage_st_capacity_basis=False`) |
| `outages._fleet_status_index` | `(iso)` | LEAKS | no (`unit_outage_fleet_status_scope=False`) |
| `campd_bins.cc_summer_capacity` | *none* | LEAKS | no (`cc_nameplate_summer_derate=False`) |
| `campd_bins.cc_winter_capacity` | *none* | LEAKS | no |
| `campd_bins.coal_summer_capacity` | *none* | LEAKS | no |
| `eia860._eia860_plant_sector` | *none* | LEAKS | no (forecast/retirement path) |
| `eia860.eia860_plant_states` | *none* | LEAKS | no |
| `eia860.eia860_regulated_plants` | *none* | LEAKS | no (`retirement_sector_gate=False`) |
| `eia860.eia860_costofservice_majority_plants` | *none* | LEAKS | no |
| `eia860.eia860_selfcommit_scope_plants` | *none* | stable | — |

The nine unreached rows are the **same defect class, currently latent**: each becomes
live the moment an ISO arms its gate together with a moving vintage. They are reported
here rather than fixed silently.

*(Method note: an earlier pass of this census wrongly read `_iso_plant_capacity` as
"stable" because a `json.dumps` digest raises on a tuple-keyed dict and the exception
was swallowed. The committed probe uses `pprint.pformat`. Any future census of this
family must not key on `json.dumps`.)*

## 4. THE EVIDENCE — how big, and in which direction

### 4a. The outage-derate denominator (probe §3–§4)

| year | bins | total MW | vs the stale 2023 map a span actually uses |
|---|---|---|---|
| 2023 | 224 | 51,319.20 | — (correct: it *is* year 1) |
| 2024 | 229 | 50,905.65 | 63 bins wrong, **+413.55 MW** stale |
| 2025 | 238 | 54,059.64 | 92 bins wrong, **−2,740.44 MW** stale |

Worse than a wrong *value*: `_unit_outage_factors_from_events` skips any event whose
bin is absent from the map (`if tgt is None or tgt not in cap: continue`). The stale
map misses **12 bins / 526.1 MW in 2024** and **26 bins / 3,692.3 MW in 2025** — those
plants' outages **never reach the LP at all** in a span run.

The single largest term is legible and physical: plant **6193** appears in the stale
2023 map as `(6193, 'COAL')` 1,018.0 MW and in the true 2025 fleet as
`(6193, 'ST_GAS')` 1,018.0 MW — **a coal-to-gas conversion between the vintages.** A
span run routes its 2025 outage events to `ST_GAS`, finds no such bin in the 2023 map,
and drops every one of them.

### 4b. The LP's own availability input for 2025 (probe §5)

`availability[g_idx, :] *= f` (`data/fleet/arrays.py`) — these factors are a direct LP
generator bound, so this is the input, not a diagnostic.

| overlay | span | single-year | delta |
|---|---|---|---|
| ≥ 5-day | 114,314,440 MWh removed | 120,131,613 MWh | **−5,817,173 MWh** (18 bins) |
| < 5-day | 9,833,720 MWh removed | 9,691,423 MWh | **+142,296 MWh** (5 bins) |

### 4c. The direction check — all four observations, one mechanism

Both legs of the divergent 2025 pair are committed and were differenced with no solve
(`results/calibration/spp36_2025` single-year arm vs `results/calibration/spp36_span`
year 2025 arm — same config, same `git_sha` `706aa547`, differing only in year
construction). This reproduces SPP-36's table exactly:

| 2025 P1 | single-year | span | span − single |
|---|---|---|---|
| LW mean price | 30.0737 | 29.5377 | −0.5360 |
| slack MWh | 240.5966 | 0.0000 | −240.5966 |
| hours > $200 | 2 | 0 | −2 |
| COAL_PRB TWh | 78.0526 | 77.4872 | −0.5654 |
| COAL_LIGNITE TWh | 6.5890 | 6.5483 | −0.0407 |
| CT_PEAKER TWh | 15.9916 | 15.5101 | −0.4815 |
| CC_REGULAR TWh | 36.3783 | 36.1986 | −0.1797 |
| **ST_GAS TWh** | **11.3395** | **12.6132** | **+1.2737** |

Every sign follows from §4b, and nothing was adjusted toward it:

- The span removes **5.82 TWh less** gas-side capability (dominated by the dropped
  `(6193,'ST_GAS')` events) → **ST_GAS +1.27 TWh** in the span.
- The span removes **more** coal capability (+142 GWh short-window, +365 GWh on
  `(6068,'COAL')` long) → **coal lower** in the span.
- Less total derate → less scarcity → **slack 240.6 → 0**, **hours>200 2 → 0**,
  **LW price −0.54**.

Four independent observations, one mechanism, correct sign on each.

## 5. WHICH LEG IS RIGHT — and what that costs

**The single-year leg is correct.** It reads each year's own vintage for the
denominator, matching the LP fleet built from that same vintage. The span reads year
1's vintage for years 2 and 3 while the LP fleet correctly advances — internally
inconsistent by construction.

Consequences, stated at full magnitude:

- **Keeper 10 `2026-09-12-spp-36-shortwindow-span`, keeper 9
  `2026-09-10-spp-27-commitment-grain`, and every prior SPP span bundle carry wrong
  outage derates and wrong CC duct-peaking bands for 2024 and 2025.** 2023 is sound in
  all of them. The runs are self-reproducible; they are not right.
- **The SPP-36 A/B itself survives.** Arm and control were both 3-year invocations at
  the same `git_sha` and shared the identical stale state, so the *difference* it
  measured is real. What is not sound is the *level* of either leg in 2024/2025 — which
  is what C3a/C3b/C1 are scored on.
- **Rule 14 `[R-ACCURATE]` is the basis, not the residual.** One of the two
  constructions is simply wrong about which fleet existed in 2025. No gate, residual or
  band was consulted in reaching that conclusion, and none should be.
- **This contaminates the evidence base for the live queue.** Cards R-be (ST_GAS
  must-run day selection) and R-ba (merit inversion) both reason off per-plant ST_GAS
  and thermal behaviour in 2024/2025 — the years the leak moves, and `ST_GAS` is the
  class it moves most (+1.27 TWh). **That is why card A outranks the queue, and why
  this session did not proceed to queue item 1.**

## 6. THE PROPOSED REPAIR — NOT LANDED; the owner's call

Idiomatic and already used four times in this codebase: **key the cache on the active
directory.** For each leaking loader, keep the public name as a thin uncached shim and
move the body into a cached core that takes `str(active_eia860_dir())` as its first
key argument — the `cod_ramp._load_cod_map(eia860_dir)` pattern.

- **Zero free parameters, zero new `ScenarioConfig` fields** (rules 21 `[R-DOF]` /
  24 `[R-REGISTRY]`). It is a cache-key repair, not a mechanism — no matrix row.
- **Blast radius is measured, not asserted (probe §6).** With
  `eia860_vintage_tracks_solve_year` **off** the directory is constant across a span,
  so a directory-keyed cache is a **strict no-op**. Of all 93 committed bundles,
  **only SPP's two arm it** — every CAISO bundle carrying the field has it `False`.
  So the repair is byte-inert for **every other ISO**, for **every SPP single-year
  run**, and for **year 1 of every SPP span**. It changes exactly the years it repairs.
- **Cost if accepted:** SPP's keeper must be re-solved to carry correct 2024/2025
  numbers — one shard, one `--years 2023 2024 2025` invocation, **~500 s of LP**
  (rule 32(b): one registrable run = one shard = one solve). The re-solve will move
  C3a/C3b/C1 in 2024 and 2025 by an amount nobody can predict from here, and per
  rule 1 `[R-STRUCT]` **that movement is not a reason to keep the defect** whichever
  way it goes.

**I did not land the repair.** It changes SPP's solve at HEAD, which would leave
keeper 10 non-reproducible with no replacement and break the next lane's rule-29(b)
form-4 control. This repo gates behavioural changes behind an owner ruling and a
declared flip even for pure construction repairs (D49/D50/D76), and card A's charter
is explicit that it "cannot move a keeper and must not try". The patch is described
above so a single shard can land it and re-solve in one pass on a yes.

## 7. TWO THINGS FLAGGED, NOT ACTED ON

- **`results/calibration/spp36_2025` is committed, unregistered, and turns the
  bundle-retention parity gate RED** (Class-E point 4) — inherited from SPP-36's banned
  fan-out. **It is also the only committed artifact showing the CORRECT 2025
  construction, and it is the evidence in §4c.** Rule 31 `[R-RETAIN]` forbids removing
  a result before the owner has ruled, so it stays. Recovery pin (full SHA, rule 33(d)):
  `git checkout 18ef91756ac84482a78ea719c2fc8d57ec7d5cf5 -- results/calibration/spp36_2025`.
  *The gate is already red at HEAD from four other lanes' bundles
  (`caiso275_B_gascoupling_{2023,2024,2025}`, `nyiso227_rebasis_span`), so removing
  SPP's would not turn it green.*
- **SPP-27 recorded `scripts/lib/bundle_fleet.reconstruct_bundle_fleet` as
  order-dependent across years for SPP — the same defect class, one layer over.** Its
  conclusion that "nothing scored is affected" is right that an arm/control pair sharing
  process order differences out, and wrong to infer the numbers are therefore correct.
  That reasoning is what let this sit. Not re-opened here; it is the same repair.

## 8. RULES

- **Rule 32(a) `[R-SHARD]`** — the parent ran no LP and launched no shard. Zero-LP work
  (census, differencing committed sidecars) stays in the parent, which is where it was done.
- **Rule 33 `[R-SHARD-ARCHIVE]`** — no shards launched, so nothing to archive or sweep.
- **Rule 29(b)** — no arm was solved, so no G-DRIFT audit was owed. The solve path was
  nonetheless verified live at HEAD: `tests/unit/pipeline/test_run_year_kwarg_binding.py`
  **4 passed**.
- **Rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — `offer_curve_by_group` was not read,
  re-cut, swept or examined. No adder, offset, haircut, proxy or rescaled input.
- **Rule 31 `[R-RETAIN]`** — nothing deleted; no `rm`. Both committed SPP bundles stand.
- **Rule 28 `[R-MECH-MATRIX]`** — no mechanism proposed, tested or added; a cache-key
  defect is not a tuning channel. **No matrix cell moves.**
- **Rule 15 `[R-DASHBOARD]`** — no run was produced, so nothing to register.
- **`[R-HOLDOUT]` removed 2026-09-09** — no SPP number here or elsewhere is a certified
  out-of-sample skill claim.

## 9. THE QUESTIONS FOR THE OWNER

1. **Land the cache-key repair?** It is byte-inert for every ISO but SPP and for SPP's
   2023, and it fixes a proven-wrong LP input for 2024/2025.
2. **If yes, re-solve SPP's keeper in the same pass?** One shard, ~500 s, one bundle,
   registered by that shard (rule 32(b)). Keeper 10's committed 2024/2025 numbers are
   superseded either way — the only choice is whether the dashboard says so.
3. **Repair the nine latent rows in §3 too, or only the two SPP reaches?** Fixing all
   eleven is the same one-line pattern per function and prevents the next ISO that arms
   vintage tracking from re-discovering this.

**Nothing is time-critical to this container:** no uncommitted bundle was produced, so
nothing is lost when the session ends. The committed evidence and this document carry
every number cited.

**Next shorthand: spp-38.**
