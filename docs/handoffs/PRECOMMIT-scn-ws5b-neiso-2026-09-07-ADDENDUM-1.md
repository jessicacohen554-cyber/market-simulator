# ADDENDUM 1 to PRECOMMIT-scn-ws5b-neiso-2026-09-07 — S21, a G-DRIFT REFRESH that moved every key, the run ids, and the artifact route

**Written and pushed BEFORE THE FIRST SOLVE.** Nothing here is revised by a result; every number
below is derived at zero LP from committed files at HEAD. It records five things the parent
PRECOMMIT could not: owner ruling **S21** and CARB-HI's key; a **G-DRIFT REFRESH** at the new HEAD
that found and fully attributed a **cache-key mismatch against §4**; the **revised GATE-I
prediction** that refresh forces; two **new pre-registrations** the Stage-C memo asks for; and the
**run ids + artifact route**.

**Lane:** SCN-WS5B-NEISO · **ISO:** NEISO · **Campaign:** `scn-campaign-stageb-2026-09-07`
**PRECOMMIT HEAD:** `a667073f` · **THIS SESSION'S HEAD:** `b849a51b` (**170 commits later**)
**Authorization:** owner ruling **S18** (2026-09-07, card D-5), as amended by **S21** (2026-09-08).

---

## 1. RULING S21 — CARB-HI replaces CARB-MID. The liveness condition is MET.

S21 (owner, 2026-09-08): *"Substitute CARB-HI, per-lane liveness proof required."*

**The proof already exists and is committed** — parent PRECOMMIT §5, whose exhaustive
identification of `carbon_price_path`'s single solve-affecting consumer
(`policy/carbon.py:187`, `resolved_base_trajectory_price = max(program, rff_path_price(path, year))`)
established both halves in one arithmetic: **RGGI strictly dominates the RFF `mid` path in 25 of
25 years, so CARB-MID is inert; RGGI does NOT dominate the RFF `high` path, which clears the floor
in 10 of 25 years (2033–2043, peak Δ +3.32 $/t at 2038), so CARB-HI is LIVE.** The condition S21
attaches is therefore met for NEISO by this lane's own committed §5, not by a new argument.

**The CARB-MID kill STANDS and is a campaign result, not an omission:** *the RFF mid carbon path is
entirely masked by RGGI on NEISO across 2026–2050 — NEISO's reference carbon signal is already
above the federal mid path in every year of the horizon.* CARB-MID is **not solved**.

The six S18 cases now read **REF · CAP-STATE-TIGHT · CES-P60 · CES-T80 · CARB-HI · ALL-CLEAN** — a
replacement for a proven-dead leg, **still six, not a seventh**; §2.1b(3) still forbids riders and
none is added.

---

## 2. G-DRIFT REFRESH at HEAD `b849a51b` — the §4 keys MOVED, and the cause is exactly one field

The parent PRECOMMIT's G-DRIFT was pinned to `a667073f`. `main` has since moved **170 commits**,
touching **26 files / +2,063 / −112** inside the audited scope. The charter's standing instruction
is *"STOP on any cache-key mismatch against your §4 table and change nothing."* **A mismatch was
found on all five previously-derived legs.** It was stopped on, diagnosed at zero LP, and is
reported here in full. **Nothing was changed to make it match.**

### 2.1 The mismatch, and its complete attribution

Re-derived at HEAD through the runner's own resolution (`resolve_policy_bundle` →
`set_caiso_fsno_partition` → `apply_iso_scenario_defaults` → `cache_key()`, `runner.py:1386-1425`):

| Case | **HEAD key (what this lane solves on)** | PRECOMMIT §4 key | HEAD key **minus one field** |
|---|---|---|---|
| REF | `1b452c457ca786a6` | `09b7e61d88f83579` | `09b7e61d88f83579` **MATCH** |
| CAP-STATE-TIGHT | `9bceb08bc291fced` | `31e7090a388d7da7` | `31e7090a388d7da7` **MATCH** |
| CES-P60 | `bd7de61415f5d950` | `859b3ca99d187974` | `859b3ca99d187974` **MATCH** |
| CES-T80 | `e4286b070d08cdcb` | `5d22c3d99d9e8d2e` | `5d22c3d99d9e8d2e` **MATCH** |
| **CARB-HI** | **`0e65d419ef104c54`** | *(new leg — S21)* | `3b6a4671622d909a` |
| ALL-CLEAN | `1c5c40a4fd011b6b` | `aaecf1bb07355400` | `aaecf1bb07355400` **MATCH** |
| CARB-MID *(killed, not solved)* | `5c70a3370360b1a5` | `5a9e78535e28bbbf` | `5a9e78535e28bbbf` **MATCH** |

**The one field is `pjm_seam_neighbour_hourly_ladder`** — a `ScenarioConfig` field that did not
exist at the pin (`git show a667073f:…/scenarios.py` contains the name **zero** times) and that
landed **WITHOUT cache-key registration**: it is absent from `_CACHE_KEY_OPTIONAL_FIELDS`, so
`cache_key_drop_defaults()` has no drop value for it and it enters the hash of **every config of
every ISO**, at its default. Dropping it — and nothing else — restores **all six** previously
derived keys byte-for-byte. The attribution is exact, not approximate.

**This is not a NEISO effect and not a Stage-B effect. It is program-wide, and it is measurable on
the program's own pin:** `PINNED_DEFAULT_CACHE_KEY = "547053bdfccd4264"`
(`tests/regression/test_persisted_identity.py:277`) is **unchanged** across the range, but a default
`ScenarioConfig`'s payload at HEAD hashes to `080aed989d20cbda` — and to **exactly
`547053bdfccd4264`** with `pjm_seam_neighbour_hourly_ladder` dropped. Every cached bundle of every
ISO re-keys.

**ROUTED TO SCN-DESK, NOT ACTED ON.** `src/market_sim/**` and `tests/**` are outside this lane's
declared regions and this lane does not touch them. The finding is reported; the desk or the
owning lane decides. Contrast with the two fields that landed correctly in the same window —
`hydro_budget_period_by_instrument` and `netload_drag_merit_allocation` are both registered with a
frozen `"False"` declaration and move no key — which is what makes this one a defect rather than a
design choice.

**The D79 solve surface is NOT the cause and is explicitly cleared.** NEISO's fingerprint did move,
`531e4805c9085734` (195 rows) → `9d35c270c69e9eee` (197 rows), from two names SPP-49 declared
(`EGRID_CT_HR_PHYSICAL_FLOOR`, `F923_GAS_PRICE_PLAUSIBILITY_BAND`). But `cache_key()` inserts
`__solve_surface__` only when `moved_rows(iso)` is non-empty, and **`moved_rows("NEISO") == {}`**
with `applicable_epochs == []`: no NEISO-projected value moved off its frozen declaration, so the
surface contributes nothing to any key here. The fingerprint moving while no key moves is the
mechanism working as designed.

### 2.2 THREE HUNKS ARE **LIVE** FOR A NEISO FORECAST LEG — named before the solve

The parent §3 concluded *"No hunk was classified LIVE."* **That verdict was true at `a667073f` and
is FALSE at `b849a51b`.** It is superseded here, in the direction that costs this lane more work,
not less. All three LIVE hunks are **repairs**, which under rule 14 `[R-ACCURATE]` is precisely why
this lane runs at HEAD rather than re-pinning — and the charter says so independently
(*"THE PIN `bdfb3095` is the CONTROL's sha — you run at HEAD"*).

1. **SPP-49 seam 2 — `data/fleet/eia860.py::_apply_simple_cycle_hr_floor`** (owner ruling P19,
   repo-wide). Its own docstring: *"A CONSTRUCTION, not a gate … Frame-level and unconditional."*
   It re-keys nothing and changes fleet heat rates in every mode, so it is LIVE for **every** leg.
   **NEISO footprint MEASURED at zero LP (`load_fleet_from_csv("NEISO", year=2026)`): exactly ONE
   plant** — 64378, whose single operating row is an `IC` prime mover — clamped **8.500 → 9.000
   MMBtu/MWh**, against a 431-unit / **24,209.6 MW** thermal fleet. NEISO's exposure is one
   sub-10 MW peaking row (the 35 units sitting at the 9.0 floor total 161.8 MW, mean 4.6 MW), i.e.
   **≲0.1 % of thermal capacity**. Bounded and near-negligible, but **not zero** — which is enough
   to void a strict identity claim, and is why GATE I is revised in §3.
2. **capx D87 — `model/capacity_evolution/ccs.py`** now folds `clean_attribute_price_by_fuel` into
   both retrofit continuations through the existing `max()` doctrine. **This is the D-15 / S19 seam
   the Stage-C memo (§5) instructed this lane to report — and it is REPAIRED at HEAD.** LIVE for the
   **target-row** legs (**CES-T80**, **ALL-CLEAN**); byte-identical elsewhere by its own contract
   (`None` ⇒ `clean_credit_for_zone` returns 0.0 ⇒ `max(x, 0.0) == x`). It moves **zero** cache keys
   (a runtime prior-year value, not a config field), which is why it is invisible in §2.1.
3. **capx D88 — `model/capacity_evolution/evolve.py`** re-mints a converted legacy representative's
   `unit_id` (`_retrofit_renames`), with a duplicate-id guard added in `data/fleet/arrays.py`. The
   collision it repairs corrupted `retirements.idx_of` (last-write-wins), `exit_exempt_unit_ids`
   membership and the `loss_years` counter — i.e. it **changed retirement decisions**. LIVE for any
   leg that converts a legacy `gas_cc` representative, which on NEISO is **every leg** (REF alone
   reaches 7,691.3 MW of `gas_cc_ccs` by 2030). Its own lane measured it *"on all nine NEISO T3
   golden variants."*

**Classified INERT at HEAD, each with its reason** — `hydro.py` / `pipeline/kwargs.py` /
`model/lp/rows.py` (all gated `hydro_budget_period_by_instrument`, default off, early-return
`UNSET`/`None`); `data/fleet/floors.py` (gated `netload_drag_merit_allocation`, default off);
`data/fuel/plant_prices.py` + `f923_gas_price_plausibility_screen` (a `__post_init__` coercion
returns it to its frozen `False` unless `(mode == "backcast" or hindcast) and
gas_plant_monthly_fuel_pricing` — a forecast leg is neither, verified resolved `False`);
`runner.py` (capx D83 — bridge-year **ledger recording** only, explicitly *"a statement about the
LP, NEVER about the fleet"*); `model/interchange/*` (PJM/MISO seams);
`pjm_seam_neighbour_hourly_ladder` itself (PJM-gated, resolves `False` for NEISO — it re-keys
without changing a single number, which is the whole of §2.1's cost).

**Consequence, stated plainly:** the LP results of a NEISO Stage-B leg differ from Stage A's for
reasons **other than the horizon**, and the parent PRECOMMIT §4's line *"the Stage-B and Stage-A
keys differ only because `end_year` is a keyed field"* no longer holds at HEAD. No control solve is
spent on this: G-DRIFT answers a code question with code, and it answered it.

---

## 3. GATE I — REVISED BEFORE ANY SOLVE, and re-purposed

The parent §6.1 pre-registered *"identity holds iff, for every year 2026–2030 and every leg,
`|HEAD − StageA| / max(1, |StageA|) ≤ 1e-6`"* and predicted **PASS for all five legs**. **That
prediction is WITHDRAWN, on the §2.2 code audit, before a single LP has run** — not adjusted after
seeing a result. Its premise (that `end_year` is the only thing separating the two runs) was
established correctly at `a667073f` and was falsified by three repairs landing since.

**Revised, and it is a stricter commitment, not a looser one** — a bare "expect differences" would
be unfalsifiable, so each leg carries a named channel and a direction:

| leg | LIVE channels | **pre-registered expectation for 2026–2030 vs Stage A** |
|---|---|---|
| REF · CAP-STATE-TIGHT · CARB-HI | SPP-49, D88 | deviation **> 1e-6** admitted; attributable to D88's retirement bookkeeping, with SPP-49 bounded by one ≲10 MW `IC` row |
| CES-P60 | SPP-49, D88 | as above; **D87 must be a no-op** here (a premium leg mints no clean-tier vector) |
| **CES-T80 · ALL-CLEAN** | SPP-49, D88, **D87** | deviation expected to be **MATERIAL and DIRECTIONAL** — see P-3 |

**GATE I is therefore re-purposed from an identity check to a REPAIR-FOOTPRINT MEASUREMENT**, and
its falsifiable content is now: *every 2026–2030 deviation is attributable to SPP-49, D87 or D88.*
**A deviation that none of the three explains is a finding and is reported as one** — it would mean
something reads the horizon, or drifted, that this audit did not find. The Stage-A comparator
values frozen in parent §6.1 stand unchanged as the baseline; they are not re-stated here.

**GATE II (the CAP-STATE-TIGHT crossing year) is UNCHANGED** — point estimate **2049**, band
**2048–2050**, "no crossing within the horizon" explicitly admitted, crossing defined as the first
year `cap(y) < REF_CO2(y)`. It is scored exactly as the parent wrote it. **GATE III is UNCHANGED**,
and is strengthened by SCN-FIX3: `co2_cap_price` and `clean_region_duals` are now recorded in
`full_horizon_summary.json`, so CAP-STATE-TIGHT's binding limbs (emissions = budget with
`co2_cap_price` > 0 in a binding year; exactly 0 in a slack year) are read **from the committed
summary** rather than scored by identity. This lane will say which limbs it read that way.

---

## 4. Two NEW pre-registrations the Stage-C memo asks this lane for

`docs/handoffs/FINDING-scenario-campaign-2026-09-07.md` §5–§6 routes two questions to the 25-year
horizon. Both are answered from committed inputs at zero LP, so the predictions are falsifiable.

**The arithmetic.** `ccs_retrofit_available_year = 2028` and `ccs_retrofit_max_gw_per_year = 3.0`
per ISO ⇒ cumulative cap `= 3,000 × (year − 2027)` MW: 3,000 / 6,000 / 9,000 at 2028/29/30 — and
**12,000 at 2031, 15,000 at 2032**. NEISO's retrofit-eligible fleet, measured at zero LP, is
**12,886.0 MW of `gas_cc` across 97 units** (Boston 2,512.4 · Central 3,997.7 · Connecticut
3,869.2 · North 2,506.7). Stage A put NEISO's REF at **7,691.3 MW = 85.5 %** of the 2030 cap.

> **P-1 — THE CAP RELEASES, AND IT RELEASES EARLY.** The cumulative 3 GW/yr cap **stops binding on
> NEISO in 2031 or 2032**, because from 2032 the cap (15,000 MW) exceeds the **entire** eligible
> `gas_cc` fleet (12,886.0 MW) and cannot bind again at any later year. Point estimate **2031**.
> The release year is reported whatever it is.

> **P-2 — AND RELEASE DOES NOT BUY AN ELASTICITY.** After release the binding constraint **hands
> off from the cap to fleet exhaustion**, so `gas_cc_ccs` plateaus at a fleet-limited ceiling
> strictly **below 12,886.0 MW** and the CES-premium ladder still shows **no NEISO elasticity**.
> Stage A could not distinguish "cap-bound" from "inelastic"; Stage B can, and this lane predicts
> the constraint changes **identity, not existence**. The explicitly admitted alternative — a real,
> monotone premium response opening in 2031–2035 once headroom exceeds the annual cap — is what
> would falsify it.

> **P-3 — CES-T80's ZERO IS A SEAM, NOT A LEVEL, AND HEAD REPAIRS IT.** Stage A measured
> `CES-T80`'s $50 ACP buying **+0.0 MW** of `gas_cc_ccs` on five of six ISOs, NEISO included, while
> `CES-P10`'s $10 bought **+1,220.1 MW**. With capx D87 landed (§2.2), **CES-T80's `gas_cc_ccs` Δ
> vs REF turns strictly positive at HEAD.** This lane's CES-T80 leg is the first NEISO measurement
> of the repaired seam.

**Standing constraint on how this lane may report:** even at HEAD, **`CES-T80` and `CES-P60` are
not one instrument at two levels**, and no table of this lane's will rank them on one axis without
saying so in place — a premium enters `apply_eac_to_mc` → dispatch marginal cost **and** the
retrofit screen; a target row's dual enters entry, retirement and (only since D87) the retrofit
screen. This lane **does not edit `ccs.py`** and did not ask for it to be edited.

---

## 5. Run ids, registration, and the artifact route

`register_forecast_baseline.build_sidecar:184` builds `run_id = f"{iso.lower()}-{start}-{end}-{label}"`.
Pre-declared, so registration cannot drift:

| leg | **pre-declared run id** | HEAD cache key (§2.1) |
|---|---|---|
| REF | `neiso-2026-2050-scn-campaign-stageb-2026-09-07-ref` | `1b452c457ca786a6` |
| CAP-STATE-TIGHT | `neiso-2026-2050-scn-campaign-stageb-2026-09-07-cap-state-tight` | `9bceb08bc291fced` |
| CES-P60 | `neiso-2026-2050-scn-campaign-stageb-2026-09-07-ces-p60` | `bd7de61415f5d950` |
| CES-T80 | `neiso-2026-2050-scn-campaign-stageb-2026-09-07-ces-t80` | `e4286b070d08cdcb` |
| **CARB-HI** | `neiso-2026-2050-scn-campaign-stageb-2026-09-07-carb-hi` | `0e65d419ef104c54` |
| ALL-CLEAN | `neiso-2026-2050-scn-campaign-stageb-2026-09-07-all-clean` | `1c5c40a4fd011b6b` |

```
python3 scripts/register_forecast_run.py \
  --summary <summary path> \
  --label scn-campaign-stageb-2026-09-07-<slug> --kind scenario
```

**REGISTRATION IS THE DELIVERABLE AND IT SHARES THE LEG'S COMMIT.** Each leg's invariant FAILs are
declared in `frontend/data/hindcast/invariant-failures.json` in the **same commit** as its sidecar;
`scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` is then run and **this
lane quotes its own exit code**. A leg that solved and did not register did not happen — the PJM
Stage-A precedent (ten legs solved, none registered across three desk refreshes) is what this
clause exists to prevent.

**Artifact route — the S20 narrowing is NOT on `main` yet.** Verified at this session's HEAD
`b849a51b`: `.gitignore:1450` still ignores the whole `results/scn-campaign-stageb-2026-09-07/`
tree. **SCN-WS5B-NYISO owns that one-line change and this lane does not make it**; this lane
**never** runs `git add -f` and **never** edits `.gitignore`. So each leg mirrors exactly two slim
files — `full_horizon_summary.json` and `run_config.json`, a few KB — to

```
docs/handoffs/scn-ws5b-neiso/<CASE>/
```

matching NYISO's ADDENDUM 1 §1 resolution and Stage A's layout. **`git fetch origin main` is re-run
before every registration commit; the moment the narrowing lands, the remaining legs commit their
slim files under `results/scn-campaign-stageb-2026-09-07/NEISO/<CASE>/` and the already-mirrored
ones are re-homed there.** Which route each leg actually took is reported in the FINDING. The heavy
bundle stays on local disk, gitignored and undeleted, per rule 31 `[R-RETAIN]`.

---

## 6. Shard plan — unchanged, plus CARB-HI

Parent §7's budget stands, with CARB-HI entering as a REF-class arm (its resolved-config diff
against REF is **exactly one field**, `carbon_price_path` `'zero'` → `'high'`, verified at HEAD):

| shard | leg | estimate |
|---|---|---|
| **S5 (long, started first)** | **CAP-STATE-TIGHT** | **≈ 364 min ≈ 6.1 h** |
| S1 | REF | ≈ 27 min |
| S2 | CES-P60 | ≈ 42 min |
| S3 | CES-T80 | ≈ 68 min |
| S4 | ALL-CLEAN | ≈ 77 min |
| S6 | **CARB-HI** | ≈ 27–30 min |
| | | **≈ 10.1 h** |

**CAP-STATE-TIGHT is the declared exception to S16's <60 min shard target** and is **not** sharded
by year — one-pass capacity evolution (rule 10) chains the years and rule 12 makes them sequential
inside an invocation. At most **2** SCN-track solves at once (ruling S14), never while the capx
track is mid-solve. `--full-solve-authorized` is legitimate **only under S18** and is cited in every
invocation. Invocation form is parent §7's, unchanged, with `--case CES-P20 --set
federal_ces_premium_usd_per_mwh=60.0` for CES-P60 (parent §2.1) and `--case CARB-HI` for the S21 leg.

---

## 7. Routed to SCN-DESK — this lane reports, does not act

1. **`pjm_seam_neighbour_hourly_ladder` is an UNREGISTERED cache-key field (§2.1)** — it re-keys
   every config of every ISO, and a default `ScenarioConfig` at HEAD no longer hashes to the
   program's own `PINNED_DEFAULT_CACHE_KEY`. Attribution is exact and reproducible. `src/` and
   `tests/` are outside this lane's regions.
2. **The parent PRECOMMIT §3's "no hunk is LIVE" verdict is pin-scoped and is superseded at
   `b849a51b` (§2.2)** — any other lane inheriting a G-DRIFT written against `a667073f` should
   re-run it rather than inherit the verdict.
3. **The Stage-C memo §5's headline (CES-T80 buys +0.0 MW of retrofit on five of six ISOs) is
   REPAIRED at HEAD by capx D87** and is now a historical measurement of the pre-D87 code. The memo
   is a committed campaign record and this lane does not edit it.
