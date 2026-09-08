# PRECOMMIT — SCN-WS5B-NYISO: Stage B, full horizon 2026–2050, under owner ruling S18

**Lane:** `SCN-WS5B-NYISO` (coordinator form, ruling S16) · **Model:** Opus (`claude-opus-5`) ·
**Branch:** `claude/scn-ws5b-nyiso-stageb-igxw5v` · **DATA PROFILE:** `nyiso`
**Campaign id:** `scn-campaign-stageb-2026-09-07` (NEW — never `scn-campaign-policy-2026-09-06`)
**THE PIN:** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **HEAD at writing:** `4e4ad90d`
**Written and pushed BEFORE the first solve** (rule 29 `[R-SCREEN]`). Every number below is
derived from committed artifacts or from the resolver at HEAD; **nothing here is revised by a
result**, and every prediction in §7 is scored as written in the FINDING.

---

## 0. Bottom line, before any LP

1. **All four §2.1b legs verified live, from the files, not from board prose.** (a) `complete`
   marker present; (b) the **bare** `nyiso-t1f` key reads **PROMOTE, caveats `[]`**, FC-1 fail set
   empty; (c) `nyiso-t1x` registered and FC-4 measured-and-reported; (d) **S18**. §1.
2. **G-DRIFT is ALL-INERT for a NYISO forecast leg — form 4 valid, NO control solve earned**, on
   74 files / 37 non-merge commits, with a **machine check stronger than the hunk audit**: all
   **14/14** committed Stage-A NYISO cache keys reproduce byte-identically at HEAD through the
   runner's own resolution chain, which since capx D79 carries the ISO-projected solve-surface
   fingerprint. §2.
3. **THE ONE HUNK THAT REACHES NYISO DATA IS MEASURED, NOT ASSUMED.** SPP-41's new
   `_screen_fuel_spike_columns` is a shared seam on every ISO's EIA-930 frame. Measured on NYISO:
   it fires in **1 of 7 years (2024)**, on **1 of 8** `NG:` columns (`NG: OTH`), for **1 of 8,760
   hours**; `NG: OTH`'s only reader in the codebase is ERCOT-only, and the two columns a NYISO
   forecast reads (`NG: WND` / `NG: SUN`) are unchanged in all seven years. §2.4.
4. **CARB-MID IS KILLED AT PHASE 0 ON A PROVEN 25-YEAR LP-INPUT IDENTITY — 25 solve-years never
   spent.** Its single resolved field delta is `carbon_price_path: zero → mid`, whose only
   LP-affecting consumer returns **Δ = 0.000000000000 $/t in ALL 25 YEARS** against REF. The
   Stage-A kill was a T1-F fact; **this is the horizon fact, and it holds.** The live carbon arm
   on NYISO at full horizon is **CARB-HI** (crossing 2031–2047, peak +$9.05/t at 2040), which S18
   does not name. **ROUTED to SCN-DESK as a scope question — not substituted, not added.** §3.
5. **Five legs are solved:** `REF` · `CAP-STATE-TIGHT` · `CES-P60` · `CES-T80` · `ALL-CLEAN`.
   Keys pre-declared in §4, budget ≈ 15–17 h in §6.
6. **Rule 29's one-year screen does not apply and is not skipped** — it governs a NEW MECHANISM.
   Stage B is the SAME five configs on a LONGER horizon: no new field, no new default, no new
   mechanism. §5.

---

## 1. The four §2.1b legs, read from the live files

| leg | requirement | reading | source, verbatim field |
|---|---|---|---|
| **(a)** | keeper + `complete` marker | **PASS** | `frontend/data/backcast/calibration-complete.json` → `complete.NYISO`: `declared` **2026-09-06**, `keeper` **`2026-09-07-nyiso-213-summer-seam`**, determination **CALIBRATED** (rubric v3.6, grade 7 of 8, fails 0, single ledgered C3c). `withdrawn` block is **EMPTY**. |
| **(b)** | a **T1-F PROMOTE** | **PASS** | `frontend/data/forecast/ff-verdicts.json` → **bare `nyiso-t1f`**: `determination` **`PROMOTE`**, `reasons` `[]`, **`caveats` `[]`**; FC-1 **PASS**, FC-2 PASS, FC-7 PASS, FC-8 PASS; FC-3/FC-4 `n/a`, FC-5/FC-6 SKIPPED. Provenance `run_id` `nyiso-2026-2030-d60-arm`, `scored_at_sha` `7ed062ba9a68`, session `capx-D60-R3`. |
| **(c)** | T1-X crossover gap MEASURED and REPORTED | **PASS** | `ff-verdicts.json` → `nyiso-t1x` present; `program-status.json` → `isos.NYISO.gate.c_crossover_gap` **`pass`**, `c_readiness` **`green`**. FC-4 **FAIL** at full magnitude (price 2023 +29.9 % / 2025 −24.0 %; gas_twh 21.0 / 19.8 %; co2 10.1 / 10.3 % CAVEAT) — **the leg closes on MEASUREMENT, not on a pass**, per the owner-signed card-A reading. |
| **(d)** | per-campaign owner authorization | **GRANTED — S18** | `docs/handoffs/scenario-desk-ledger-2026-09.md` r#21, card D-5 → **S18 (2026-09-07): "Narrow: 6 legs × NEISO+NYISO."** Second leg-(d) grant in program history; **per-campaign by its own terms**. |

**Read against the charter's own warning.** I read the **bare, un-suffixed** `nyiso-t1f` key. The
four suffixed NYISO T1-F keys present in the file — `nyiso-t1f-pre-d60`, `nyiso-t1f-ff2d`,
`nyiso-t1f-ffr3a2`, `nyiso-t1f-pre-d45r` — are PRESERVED SUPERSEDED baselines and none was quoted.
NYISO's `complete` marker has been declared/withdrawn/re-declared three times; the reading above is
**the live file at HEAD `4e4ad90d`**, not the board narrative.

**One stale board cell, FLAGGED not edited** (`program-status.json` is outside this lane's write
scope): `isos.NYISO.gate.d_owner_auth` reads **`none` — "no authorization exists"**. That predates
S18 by one refresh. The authorization is the ledger's r#21 ruling, and this lane does not edit the
board. Routed to SCN-DESK.

---

## 2. G-DRIFT (rule 29 clause (b)) — the audit, before the first solve

`git diff bdfb3095 → origin/main (4e4ad90d)` over `src/market_sim`, `scripts/lib`,
`scripts/run_full_horizon.py`, `scripts/run_ces_leg.py`, `scripts/run_calibration*.py`,
`data/raw/reference`: **74 files, 37 non-merge commits, +43,397 / −26,442.**

### 2.1 The machine check that outranks the hunk audit — 14/14 keys reproduce

Every committed Stage-A NYISO leg key was **recomputed at HEAD** through the runner's own chain
(`matrix_configs` → `resolve_policy_bundle` → `apply_iso_scenario_defaults` → `cache_key()`), which
is the chain `run_ces_leg.assemble_bundle`'s docstring names as the only one that reproduces a real
key. Result — **14 matched, 0 moved**:

```
ALL-CLEAN e13b0d801b1ffce1 · CAP-STATE-TIGHT 76c60ac152400146 · CES-P10 3c96d694c18e5547
CES-P20 9da7c76372c98406 · CES-P20+VOL-HI 566335c8ca37dc17 · CES-P30 89a70dd1140c6731
CES-P60 c3013cc6087bd2aa · CES-T80 eb1b0e1df942db47 · VOL-HI 893acae55a1a898f
VOL-MID 9528d708b81b5074 · REF f10cc93084b4c0db (both trees) · LOAD-HI c2ceaefa4afafcda (both
trees) · LOAD-HI-ORGANIC 27f19f22105ab6cb
```

**Why this is stronger than "files changed, therefore void."** Since capx **D79** (owner ruling
Q54) `cache_key()` carries a **per-name, per-ISO value hash of the seven `config/solve_surface.py`
`SURFACE_MODULES`**, dropped at each name's frozen declaration — so a name enters the key **only**
when its live hash differs from its declaration. An unmoved key therefore proves three things at
once: (i) no cache-key-registered field's resolved value moved; (ii) **NYISO's own `ISOConfig` and
its `default_scenario_overrides` are unmoved** (`apply_iso_scenario_defaults` is inside the chain);
and (iii) the **NYISO projection of `constants` / `capacity_market` / `fuel_trajectories` /
`ercot_envelopes` / `plant_taxonomy` / `entry_config` / `offer_curve_base.generic` has not moved**,
which is what covers the +218 / +267 / +61 lines those three registry modules gained.

**Reconciled, not assumed — "twelve summaries for ten registered legs."** The policy tree carries
its own `REF` and `LOAD-HI` copies. Both are **the unregistered Stage-A controls**, and their keys
are **identical** to the `-r2` load tree's (`f10cc93084b4c0db` / `c2ceaefa4afafcda`) — the same
config rematerialized, not a second leg. 12 policy dirs = 10 registered + 2 controls; NYISO's
registered total is 10 policy + 3 load = **13 sidecars**, which is what `frontend/data/hindcast/`
holds.

### 2.2 The eleven new `ScenarioConfig` fields, resolved on the actual Stage-B legs

Eleven solve-affecting fields landed since the pin. Resolved on **all six** Stage-B configs:
**11/11 `False` on every leg**, `mode=forecast`, `hindcast=False`.

| field | lane | why INERT here |
|---|---|---|
| `capacity_screen_peak_measured_hindcast` | capx D76 | **the only one whose dataclass default is `True`.** Its `__post_init__` coerces back to the frozen declaration whenever `not config.hindcast`, and the LP branch predicate is `config.hindcast and not is_crossover_forward_year` — measured `False` on all six legs, and the 14/14 key check is the independent second proof. |
| `netload_drag_layup_window_mask` | ercot-256 | `_resolve_drag_layup_shares` is **backcast-only by its own gate** (rule 13); a forecast run gets an empty dict and the drag floors are byte-identical. |
| `cc_summer_derate_reconciled_basis` | nyiso-212 | **NYISO's own new field** — default-off and NOT in NYISO's `default_scenario_overrides`; it is the backcast keeper's field, and a registered key field, so the unmoved keys prove it. |
| `spp_gas_commitment_bridge` | SPP-44 | ISO-exclusive to SPP; `build_spp_gas_bridge_p1_prep` returns `None` for every non-SPP run. |
| `pjm_thermal_accreditation_vintage` | capx D84 | PJM registry-gated (`THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO`, PJM alone) + requires the D48 predicate; armed only through PJM's `_pjm_config`. |
| `pjm_interface_feed_admissibility_gate` | pjm-interface | PJM-scoped; the new `interface_series_admissibility` has no NYISO call site. |
| `miso_seam_neighbour_hourly_ladder`, `miso_seam_neighbour_hourly_spp` | miso-231/233 | MISO seam pricing; `_inject_seam_ladder`'s new `hourly_anchor` defaults `None` → `mc[row,:] = prices[k]`, the pre-change line. |
| `ercot_ep_gas_basis_monthly`, `ercot_zonal_spread_ep_referenced`, `gas_offer_margin_anchor_vintage` | ercot-253/254 | ERCOT basis path. |

### 2.3 Per-file classification — every changed hunk, with its reason

| file(s) | classification | cited reason |
|---|---|---|
| `config/iso_configs.py` (+369) | **INERT** | Two hunks only: PJM's `default_scenario_overrides` (D75-R arm) and a **new `_spp_config`** appended after `_neiso_config`. `_nyiso_config` is **untouched**; the only other change is a docstring "six ISOs → seven". |
| `config/constants.py`, `capacity_market.py`, `fuel_trajectories.py` | **INERT** | `SURFACE_MODULES` — covered by §2.1(iii); NYISO's projection is at its frozen declaration or the keys would have moved. |
| `config/scenarios.py` (+879) | **INERT** | The eleven fields of §2.2 plus their key registrations; every one resolves `False` on all six legs. |
| `config/solve_surface.py`, `solve_surface_declared.py` (new) | **INERT** | capx D79; landed at **zero key moves** and reproduced here as 14/14. |
| `config/paths.py` | **INERT** | `resolve_backcast_eia860_vintage` — reached only under `config.mode == "backcast"`. |
| `runner.py` (+28) | **INERT** | SPP bridge hook (`None` off-SPP) + the backcast-gated eia860 vintage resolution; a forecast leg passes `None` exactly as before. |
| `pipeline/year.py`, `pipeline/__init__.py`, `pipeline/kwargs.py` | **INERT** | SPP bridge hook / export / logging branch. |
| `pipeline/commitment.py` (+174) | **INERT** | **Pure insertion** (`@@ -1216,0 +1217,174 @@`, zero lines removed) of `build_spp_gas_bridge_p1_prep`; `build_nyiso_gas_bridge_p1_prep` is unmodified. |
| `pipeline/backcast_config.py` (+143) | **INERT** | `backcast_config()` is never entered by a `mode="forecast"` run. |
| `pipeline/persist.py`, `results/cache.py`, `results/export.py` | **INERT** | Recording only — the `solve_surface.json` sidecar, the `solve_surface` block in the exported JSON, and path roots in `environment_block()`, which "is not an input to any key". |
| `model/capacity_evolution/evolve.py` | **INERT** | Deletes `exempt_unit_ids=frozenset()`, a parameter capx D78-R2 removed because it **had no producer** — its only use was a skip that never fired. `exit_exempt_unit_ids=(…)` is byte-identical across the diff. |
| `model/capacity_evolution/retirements.py` (+174) | **INERT** | capx D84 thermal ELCC vintage: additive, default-off, PJM-registry-gated, and requires the D48 predicate. The unarmed ladder runs "BYTE-IDENTICALLY" by its own contract. |
| `model/reserves/spec.py` (+272) | **INERT** | Two deletions, **both inside `_ercot_multiproduct_design`** (ercot-253's plan→measured AS requirement swap); plus a new `_spp_design` and its `get_reserve_design` dispatch (`if iso == "SPP"`). |
| `model/interchange/*` | **INERT** | `hourly_anchor` defaults `None`; SPP registry entry; MISO-only seam work. NYISO's injection tuple untouched. |
| `results/scarcity.py` (+91) | **INERT** | New/edited functions are all `ercot_*`. |
| `data/renewables.py` (+167), `zone_assignment.py`, `fleet/models.py`, `campd.py`, `eia930/{frames,envelopes,__init__}.py`, `transmission_expansion.py`, `data/fuel/**` | **INERT** | SPP registry rows and new SPP/MISO/ERCOT readers. NYISO appears in **no** changed set: `_UNCURTAILED_FALLBACK_ISOS` and `_WIND_ZONE_SHAPE_ISOS` gained **SPP only**. |
| `data/fleet/arrays.py` (+88) | **INERT** | `_reconciled_summer_ratios` is reached only under `cc_summer_derate_reconciled_basis` (§2.2). |
| `data/fleet/floors.py` (+110), `floor_mechanisms.py` | **INERT** | `layup_removed` defaults `None` (byte-identical clip) and its resolver is backcast-only; the new mech id is append-only. |
| `data/eia930/actuals.py` (+194) | **INERT — MEASURED, see §2.4** | The one shared seam that reaches NYISO. |
| `data/eia930/demand.py` (+71) | **INERT** | New `_load_spp_hourly_demand`; `_screen_demand_spikes` itself is unchanged in behaviour and its one live case is SPP 2023. |
| `scripts/run_full_horizon.py` (+80) | **INERT — and it DISCHARGES this lane's §9 item 4** | `_policy_duals` is "a RECORDING SEAM ONLY … no solve, no threshold and no cache key moves". See §2.5. |
| `scripts/run_ces_leg.py` (+9) | **INERT** | Docstring only. |
| `scripts/lib/**` | **INERT** | SPP `_ISO_MODULES` rows, `ISO_ORDER` gaining SPP, `PROVENANCE_FIELDS` gaining `solve_surface`, and two new modules (`key_provenance.py`, `wind_shape.py`) with no NYISO caller. |
| `scripts/run_calibration.py` (+247), `run_calibration_full.py` (+194) | **INERT** | Backcast entry points; a Stage-B leg runs `run_ces_leg.py`. |
| `data/raw/reference/**` | **INERT** | CAISO supply-consistent demand + SPP seam tables. No NYISO artifact. |

### 2.4 The one hunk that reaches NYISO — measured to zero

SPP-41 routes **every** ISO's `<BA> hourly` frame through a new `_screen_fuel_spike_columns`
before any consumer sees it. That is shared code on the NYISO path, so it is **not** dischargeable
by an "another ISO's branch" reason. Measured directly, 2019–2025:

| year | `NG:` columns | cells changed |
|---|---|---|
| 2019–2023, 2025 | 8 | **NONE** |
| **2024** | 8 | **`NG: OTH` × 1 hour** (h6759; 16,117 MW vs p99.9 3,290 MW — a unit slip) |

**Why that is INERT for this campaign, by citation and not by assumption:** `NG: OTH` has exactly
one reader in the tree — `load_ercot_other_gen`, which draws from `_ercot_hourly_frame_screened`
and is ERCOT-only. The generic per-ISO renewable reader takes **`NG: WND` and `NG: SUN` alone**,
and both are byte-identical on NYISO in all seven years. A forecast leg additionally runs no C1/C4
benchmark, which is the only other consumer of the wider fuel map.

**Verdict: G-DRIFT ALL-INERT ⇒ rule 29(b) form 4 is VALID. The committed Stage-A artifacts ARE the
control. No control solve is spent by this lane or by any shard.**

### 2.5 One LIVE-for-the-better change, declared: this lane's own §9 item 4 is discharged

`FINDING-scn-ws5a-policy-nyiso-2026-09-07.md` §9 item 4 recorded that a policy campaign's duals are
unrecoverable from committed artifacts, so under S16 sharding the dual limbs of gates G4 and G7 die
with the container. **SCN-FIX3 landed the fix** (`1d683cd7`, "Record the clean-tier and mass-cap
duals in the full-horizon summary"): `run_full_horizon._policy_duals` now writes
`clean_region_duals` and `co2_cap_price` into every trajectory row beside `rps_dual`, `None` (never
`0.0` or `[]`) where nothing was measured.

**Consequences this PRECOMMIT commits to:**
- The G4/G7 dual limbs are scored **as the gates state them** in Stage B, from the committed
  summary — not by the identity substitute Stage A had to use. Stage A's substitute is not
  re-used and not quoted as if it were the dual.
- Stage-A legs carry **neither key**, which every reader treats as *not measured*. Any Stage-A ↔
  Stage-B comparison of a dual is therefore a comparison against an **absent** record, and is
  reported as such rather than as a change.
- **No shard edits `scripts/run_ces_leg.py` or `run_full_horizon.py`.** The repair is already on
  `main`; the charter's instruction to coordinate through SCN-DESK rather than touch the file is
  satisfied by taking the landed fix.

---

## 3. PHASE 0 — `CARB-MID` is killed on a proven 25-year LP-input identity

**Rule 29 clause (0): a zero-LP phase 0 first, wherever one exists. One exists here, it costs
seconds, and it kills a leg.**

`CARB-MID`'s resolved delta against `REF` is **exactly one field** —
`carbon_price_path: 'zero' → 'mid'` (verified by a full `dataclasses.fields` diff on the resolved
configs). At the pin and at HEAD that field has **one LP-affecting consumer**:
`policy/carbon.py::resolved_base_trajectory_price`'s `max(program, rff_path_price(...))` (`:187`).
Everything else is a docstring, a cache-key registration, or
`scenarios.py:17498`'s `carbon_path_below_program_warning` tripwire, **which only warns**.

Evaluated over the **full Stage-B horizon**, NYISO, through the same resolution chain:

| | 2026 | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|---|
| NYISO program trajectory (RGGI) $/t | 23.6363 | 30.9824 | 43.4544 | 60.9470 | 85.4813 | 119.8920 |
| RFF `mid` path $/t | 0.0000 | 15.0000 | 25.0000 | 35.0000 | 42.5000 | 50.0000 |
| **Δ resolved (`CARB-MID` − `REF`)** | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** |

- `Σ |Δ|` over 2026–2050 = **0.000000000000 $/t**; live years = **NONE (25/25 identical)**.
- Cross-checked at the top of the precedence chain too: `max |resolve_carbon_price(REF, y) −
  resolve_carbon_price(CARB-MID, y)|` = **0.000000000000 $/t**, and `resolve_carbon_program`
  returns an identical `price_adder` / `cap_spec` in all 25 years.
- `CARB-LO` is likewise inert 25/25 (not a Stage-B leg; recorded for completeness).

**So the LP inputs are identical and the solve is deterministic: `CARB-MID` would reproduce `REF`'s
trajectory exactly, at the cost of a full 25-year invocation (≈2–3 h), because
`carbon_price_path` is a registered cache-key field and the two configs key differently
(`4678fbbfc44b943a` vs `f1a2ef17634b0467`).** That is precisely the spend rule 29 clause (0)
exists to refuse.

**What this is NOT evidence of** (carried forward verbatim from the Stage-A kill, because it now
governs a full-horizon leg): it says a *federal RFF* `mid` price is a no-op where RGGI already
charges more. It says **nothing** about whether carbon pricing works in New York — NYISO is
carbon-priced above the `mid` path in **every one of the 25 years**, by 2.1× at 2030 rising to
2.4× at 2050.

### 3.1 ROUTED to SCN-DESK — the scope question, not executed

**`CARB-HI` is the live full-horizon carbon arm on NYISO and S18 does not name it.** Measured on
the same chain: `CARB-HI` crosses above the RGGI trajectory in **2031–2047**, `Σ|Δ| = 99.61 $/t`,
peak **+$9.0530/t at 2040**, returning to inert by 2048. This is the property
`configs/scenario_campaign_matrix.yaml` records as "**the inertness is a T1-F fact, not a horizon
fact**" — and this lane has now verified it independently rather than quoting the comment.

**This lane does not substitute it and does not add a seventh leg.** §2.1b(3) forbids riders by
name, and S18 is per-campaign and enumerated. The question the desk owns is:

> `CARB-MID` is provably byte-identical to `REF` at full horizon on NYISO, so the granted six
> reduce to five live legs. Does the desk (i) accept the kill and leave the carbon axis unmeasured
> at full horizon, (ii) rule that `CARB-MID` be solved anyway as a registered identity control, or
> (iii) substitute `CARB-HI`, the arm that is live in 17 of 25 years?

**Answer wanted before the campaign closes; nothing is blocked on it** — the five live legs do not
depend on it and are solved regardless. If the desk rules (ii) or (iii), the leg is one further
invocation on the same pin, PRECOMMIT addendum first.

---

## 4. The five solved legs — keys pre-declared, derived from mechanism

Derived through the runner's own chain, never copied from a prior prompt. **The derivation is
control-checked**: the same code reproduces the committed Stage-A `CES-P60` key
`c3013cc6087bd2aa` at the T1-F window exactly, including its `--set` override, so the chain below
is the one the solve will use. `tests/regression/test_persisted_identity.py::
PINNED_DEFAULT_CACHE_KEY` is the standing pin for the bare default; these are its campaign siblings.

| leg | **pre-declared key (2026–2050)** | resolved field delta vs `REF` | Stage-A sibling key (2026–2030) |
|---|---|---|---|
| **REF** | **`f1a2ef17634b0467`** | — (the reference; overrides nothing) | `f10cc93084b4c0db` |
| **CAP-STATE-TIGHT** | **`462d197ef1f9e023`** | `mass_cap_enabled` F→T · `mass_cap_program` None→`co2` · `mass_cap_tons_by_year` None→S12 schedule | `76c60ac152400146` |
| **CES-P60** | **`ddff74e2738eaf96`** | `federal_ces_enabled` F→T · `federal_ces_premium_usd_per_mwh` 0.0→**60.0** | `c3013cc6087bd2aa` |
| **CES-T80** | **`fc3ad07981d95d84`** | `federal_ces_enabled` F→T · `federal_ces_acp_usd_per_mwh` None→50.0 · `federal_ces_target_by_year` None→{2026: 0.55, 2035: 0.80, 2050: 1.00} | `eb1b0e1df942db47` |
| **ALL-CLEAN** | **`774db75da9f4d95a`** | 7 fields: the CES-T80 three · `carbon_price_path` zero→mid · `demand_growth_path` mid→high · `datacenter_load_path` mid→high · `voluntary_clean_demand_path` off→high | `e13b0d801b1ffce1` |
| *(killed §3)* CARB-MID | *(`4678fbbfc44b943a`)* | `carbon_price_path` zero→mid — **Δ = 0 in all 25 yr** | `91d435c848c57fb6` |

**A key that does not match its pre-declaration is a STOP**, not a note: the shard reports it and
solves nothing further until this lane has re-derived it.

**`CES-P60` is the committed `--set` channel**, unchanged from Stage A:
`--case CES-P30 --set federal_ces_premium_usd_per_mwh=60.0`. **$60 is one common level for every
ISO**, above the footprint's highest published ACP ($50), identified from `STATE_RPS_ACP`, declared
ex ante, and **never swept against a gate**. **DOF ledger: ZERO free parameters** in this lane —
no offer-curve multiplier, no `authorized_price_tuning` block (a backcast channel, untouched), no
new field, no default moved.

**Declared against interest — `ALL-CLEAN` carries an inert limb.** Its `carbon_price_path: mid` is
one of the seven fields and, by §3, contributes **exactly nothing** on NYISO in any of the 25
years. `ALL-CLEAN`'s live limbs are the CES target row, `demand_growth_path`, `datacenter_load_path`
and `voluntary_clean_demand_path`, and its correct comparator is `LOAD-HI`, not `REF` — the same
reading Stage A used. It is **not** re-labelled and **not** dropped; the limb is stated so no reader
attributes an `ALL-CLEAN` delta to carbon.

---

## 5. Rule 29's one-year screen — stated, not left to be inferred

**It does not apply.** Rule 29 `[R-SCREEN]` governs *"a new config"* whose mechanism has not been
measured — it asks whether the mechanism does what its arithmetic says before the full span is
spent. Stage B introduces **no new mechanism, no new `ScenarioConfig` field, no new default and no
new level**: it is the *same five configs already solved and registered at the T1-F window*, on a
longer horizon. There is nothing for a screen gate to kill that Stage A has not already screened.

What replaces it, and is stronger for this shape of work, is **§8's 2026–2030 identity gate**: the
first five years of each Stage-B leg must reproduce its own registered Stage-A leg. A screen asks
"does the mechanism do what it claims"; the identity gate asks "is this the same model on a longer
clock", which is the only question a horizon extension can get wrong.

**Where a phase-0 kill DID apply, it fired**: §3 killed `CARB-MID` at zero LP cost — clause (0)
working exactly as written.

---

## 6. Shard plan and LP budget (ruling S16 · rule 12 · ruling S14)

**One shard session per leg. A full-horizon leg CANNOT be sharded by year** — one-pass capacity
evolution chains the years and rule 12 `[R-PARALLEL]` makes them sequential inside an invocation.
No shard splits a leg.

| shard | leg | Stage-A min/solve-year | **25-yr projection** | notes |
|---|---|---|---|---|
| **S-1** | **`CAP-STATE-TIGHT`** | **12.87** | **≈5.4 h** | **THE DECLARED EXCEPTION** to S16's <60 min target, budgeted separately. Launched first because it is the long pole. |
| **S-2** | `REF` | 4.87 | ≈2.0–2.5 h | The basis for every delta; launched first alongside S-1. |
| **S-3** | `CES-P60` | 4.64 | ≈1.9–2.4 h | |
| **S-4** | `CES-T80` | 6.06 | ≈2.5–3.2 h | Stage A spiked to 668 s at 2029, the first year the row is interior; expect more such years. |
| **S-5** | `ALL-CLEAN` | 6.17 | ≈2.6–3.3 h | Same spike signature at 2029 (675 s). |
| | **TOTAL** | | **≈15–17 h** | `CARB-MID`'s ≈2–3 h is **not spent** (§3). |

**Concurrency:** at most **2 SCN-track solves at once** (S14), and none while the capx track is
mid-solve. Order: (S-1, S-2) → S-3 → S-4 → S-5, refilling as each returns.

**The projection is a projection and is labelled one.** Stage-A per-year cost on NYISO *rises*
within a 5-year window (REF 219 → 331 s), but the program's only measured 25-year run (GOLDEN-3,
NEISO) found years 21–25 **cheaper** than years 1–5 (0.68×) and came in 1.8 % above the flat-median
bound. The bracket above is flat-median × 25 with a +30 % allowance, not FF-3E's refuted 1.76×
uplift. Peak RSS on Stage A was 3.51–4.06 GB per leg; two concurrent legs is ≈8 GB, inside a 15 GB
container. **The measured 25-year wall and RSS are reported in the FINDING whatever they are** —
this campaign produces the program's second-ever 25-year NYISO cost measurement.

**Every shard is told, verbatim:** solve the one named case; verify the key against §4 before
proceeding; commit the slim `full_horizon_summary.json` + `run_config.json` into
`results/scn-campaign-stageb-2026-09-07/NYISO/<CASE>/` **before the container dies**; touch nothing
outside that directory; `--full-solve-authorized` is legitimate **only** under S18 and is cited as
such.

```
python3 scripts/run_ces_leg.py \
  --config configs/scenarios/nyiso_scenario_base_2026_2050.yaml \
  --matrix configs/scenario_campaign_matrix.yaml \
  --case <CASE> --out-dir results/scn-campaign-stageb-2026-09-07/NYISO/<CASE> \
  --campaign scn-campaign-stageb-2026-09-07 --full-solve-authorized
```

---

## 7. Predictions — every one scored as written in the FINDING, at full magnitude

**P-1 (identity).** Each leg's 2026–2030 sub-trajectory reproduces its registered Stage-A leg on
every scalar in §8's list. **PASS** at |rel| ≤ 1e-9; **WARN** at ≤ 1e-6 (float summation / simplex
degeneracy); anything beyond is a **FINDING about the horizon or a G-DRIFT miss**, never a licence
to re-pin.

**P-2 (`CES-T80` is the case the horizon transforms).** In the T1-F window the target glide only
reached **0.6611**; at full horizon it reaches **0.80 at 2035 and 1.00 at 2050** — a 100 % clean
standard. I predict `CES-T80` separates from `REF` far more than Stage A's +156.6 MW of 2030 solar,
and that its **first interior year stays 2029** (Stage A, G4) with the row interior in every
subsequent year.

**P-3 (`CES-P60` vs `CES-T80` are NOT one instrument at two levels).** This lane's own Stage-A
§9 item 1 measured the seam: `ccs.py:475-476` prices the retrofit uplift with
`effective_eac_price_for_unit = max(legacy eac, premium × credit)` and **never reads
`clean_attribute_price_by_fuel`**, where a target-row dual lives. So the **premium reaches the CCS
retrofit screen and the target row does not**. Prediction: `CES-P60`'s CCS retrofit build **exceeds**
`CES-T80`'s in every year, and `CES-T80`'s incremental `gas_cc_ccs` over `REF` stays at or near
**0.0 MW** despite its larger attribute price by 2050. **Ruled D-15/S19 and routed to the capx
director — this lane REPORTS it and does not edit `ccs.py`.** The two legs are never presented as
one instrument at two levels without this stated first.

**P-4 (`CAP-STATE-TIGHT` crossing year).** Defined precisely, because two different crossings are
in play:

- **(a) Quantity axis — budget vs `REF` emissions.** The cap is a *loosening* while
  `budget(y) > REF co2_mt(y)` and a *tightening* once `budget(y) < REF co2_mt(y)`. Stage A
  measured `REF` falling 23.69 → 24.59 → 17.16 → 13.71 → **10.903** Mt (the CCS retrofit wave,
  6,255.9 MW by 2030) against a budget of 23.16 → 20.20, so the cap is **already a loosening from
  2028**. The S12 glide reaches 10.903 Mt between **2042 (11.16)** and **2043 (10.34)**.
  **PRE-REGISTERED: the crossing back to a tightening is 2044, band [2041, 2050], and "no crossing
  within the horizon" is an allowed outcome** — later if `REF` keeps abating under an RGGI adder
  rising to $119.89/t, earlier if DC load growth lifts `REF`. **The measured crossing is reported
  whatever it is.**
- **(b) Price axis — the cap dual vs the RGGI adder it REPLACES.** On NYISO this is **already
  crossed at 2026** and is the opposite of NEISO's reading: Stage A measured the dual
  26.98 → 4,130.35 $/t against an adder of 23.64 → 30.98, i.e. **above in every year** (NEISO:
  below in every year). Prediction: the dual stays above the adder in **every one of the 25 years**
  and grows super-linearly as the budget glides to 4.6 Mt.

**P-5 (the reliability trajectory, and the mechanism I expect to own it).** Stage A already
measured `unserved_mwh` = **1,566,947.7 MWh at 2030** under the cap, with `lw_price` $1,687.46 and
`max_hourly_price` at the $2,000 cap. **PRE-REGISTERED: `unserved_mwh > 0` in every year from 2030
to 2050 and non-decreasing in trend; `gas_cc_ccs` stays 0.0 MW in every year of the capped case.**

**P-6 (the seam I expect P-5 to expose — pre-registered so it cannot be written after the fact).**
`runner.py:2337` computes `carbon_price_year = resolve_carbon_price(config, driver_year)` and
passes it to `evolve_fleet` (`:2354`). Under a mass-cap row `resolve_carbon_price` returns **0.0**
(the two-source invariant: a row resolution carries `price_adder is None`, and the allowance price
is the LP dual, which does not exist at config-resolution time). **So every capacity-evolution
screen — the CCS retrofit screen, the economic-retirement screen and the new-entry screen — sees a
carbon price of ZERO under `CAP-STATE-TIGHT`, while the LP's own dispatch pays the endogenous row
dual.** Prediction: this, and not the budget level, is what produces P-5 — a quantity instrument
prices *dispatch* but not *investment*, so the fleet never builds the abatement that would let it
meet the budget, and the model sheds load instead. **This is the carbon-axis sibling of §9 item 1's
CES coverage seam.** Reported and **routed**; `runner.py` is outside this lane's regions and is not
touched. If the measurement contradicts this, it is reported as a refuted prediction.

**P-7 (`ALL-CLEAN` vs `LOAD-HI`).** `ALL-CLEAN`'s correct comparator is `LOAD-HI`, whose Stage-B
leg S18 does not grant — so its netting is reported against the **committed Stage-A `LOAD-HI`** at
the T1-F window only, and the 2031–2050 tail is reported against `REF` **with the load limb named
as an unnetted confound**. No implicit netting.

**P-8 (cost).** ≈15–17 h total, `CAP-STATE-TIGHT` ≈5.4 h. Reported measured, per leg and per year.

**P-9 (`rps_dual`).** Stage A measured `rps_dual` = **40.0000 at the `STATE_RPS_ACP["NYISO"]`
escape in all five years of all ten legs**. Prediction: it stays 40.0000 in every year of every
Stage-B leg — no arm moves the RPS row's dual — **unless** the `CES-T80`/`ALL-CLEAN` target row
reaching 1.00 at 2050 drives the clean fleet past the RPS requirement, which would make the row
interior. A year in which it moves is reported as the first RPS-row response the campaign has
measured.

---

## 8. The 2026–2030 identity gate — the control, with its tolerance

**G-CTRL form 4.** The control is the **committed Stage-A artifacts**, never a control solve
(§2 establishes form 4's validity):

```
results/scn-campaign-load-2026-09-06-r2/NYISO/REF/full_horizon_summary.json      f10cc93084b4c0db
results/scn-campaign-policy-2026-09-06/NYISO/<CASE>/full_horizon_summary.json
frontend/data/hindcast/nyiso-2026-2030-scn-campaign-policy-2026-09-06-*.json
```

**Scored scalars — every one in the summary's own trajectory row:** `lw_price`,
`max_hourly_price`, `neg_price_hour_frac`, `hours_ge_{100,500,1000,2000}`, `co2_mt`,
`peak_demand_mw`, `reserve_margin`, `rps_dual`, `thermal_mw`, `firm_clean_mw`, `vre_mw`,
`total_cap_mw`, `storage_mw`, `storage_power_mw`, `builds_{thermal,thermal_backstop,renew,storage}_mw`,
`retire_mw`, `total_gen_mwh`, `storage_{charge,discharge}_mwh`, and every member of
`capacity_by_fuel_mw` / `generation_by_fuel_mwh` / `builds_by_source`.

**The reference rows, quoted now so they cannot be chosen later** (`REF`, `f10cc93084b4c0db`):

| year | `lw_price` | `max_hourly_price` | `co2_mt` | `peak_demand_mw` | `reserve_margin` | `vre_mw` | `total_cap_mw` | `total_gen_mwh` | `builds_renew_mw` | `retire_mw` |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 50.193 | 64.5 | 23.6923 | 29393.444 | 0.185113 | 3900.0 | 45205.1 | 154123651.1 | 0.0 | 0.0 |
| 2027 | 49.184 | 63.1 | 24.5911 | 29564.922 | 0.177361 | 3900.0 | 45177.3 | 155943434.4 | 0.0 | 27.8 |
| 2028 | 50.921 | 65.7 | 17.1630 | 29740.544 | 0.170408 | 3900.0 | 45177.3 | 157780426.5 | 0.0 | 0.0 |
| 2029 | 49.276 | 65.8 | 13.7082 | 29920.357 | 0.208295 | 6743.4 | 49020.7 | 159665229.9 | 2843.4 | 0.0 |
| 2030 | 54.953 | 73.0 | 10.9030 | 30104.412 | 0.200907 | 6743.4 | 49020.7 | 161553427.6 | 0.0 | 0.0 |

The four other legs' reference rows are in the committed summaries at the keys of §4 and are
scored identically; `CAP-STATE-TIGHT`'s 2030 row (`lw_price` 1687.46, `max_hourly_price` 2000.0,
`co2_mt` 20.2, `total_gen_mwh` 159958364.3) is the one this lane expects to be most informative,
since its 1.59 TWh generation shortfall against `REF` **is** the unserved energy.

**Tolerance, pre-registered:** **PASS** |rel| ≤ **1e-9** on every scalar; **WARN** 1e-9 < |rel| ≤
**1e-6**, recorded with the field named; **FAIL** beyond, and a FAIL is a **finding**, investigated
as a horizon effect or a missed G-DRIFT hunk. **A miss is never a licence to re-pin.** The gate is
expected to pass exactly: G-DRIFT is all-INERT, the two base YAMLs differ **only** in `end_year`
(verified by diff), and nothing in the solve path reads `end_year` as a per-year input — the
`mass_cap_tons_by_year` knots, the CES target glide and the demand paths are all interpolated on
**absolute year**, not on horizon fraction.

**Why the gate can pass at all despite different keys:** `start_year`/`end_year` are cache-key
fields, so every Stage-B leg is a genuine re-solve into a new bundle, not a cache hit. The identity
is therefore a real test of the model, not of the cache.

---

## 9. Duties, scope and retention

**Files this lane writes:** `results/scn-campaign-stageb-2026-09-07/NYISO/**` · the NYISO Stage-B
sidecars and their `frontend/data/hindcast/invariant-failures.json` rows · this PRECOMMIT ·
`docs/handoffs/FINDING-scn-ws5b-nyiso-2026-09-07.md` ·
`docs/codebase-site/data/mechanism-matrix/NYISO.js` (**LAST commit, after rebase, appended cell
lines only** — rule 28(b)).

**Files this lane does NOT touch:** `src/market_sim/**`, `scripts/**`, `configs/**`, `tests/**`,
any other ISO's matrix shard or results tree, the whole backcast namespace, `program-status.json`,
`ff-verdicts.json`, the desk ledger, and the plan's §5.1 — **§5.1 rows are routed to SCN-DESK**,
because `SCN-WS5A-POLICY-SYNTH` is writing that table in the same window.

**Registration is the deliverable** (the PJM Stage-A failure this charter names). Each leg is
registered via `scripts/register_forecast_run.py` into `frontend/data/forecast/`, with its
invariant FAILs declared in `frontend/data/hindcast/invariant-failures.json` **in the same
commit**, then `scripts/check_forecast_invariants.py --sidecar-dir` is run and **this lane quotes
its own EXIT code**. While registering, this lane checks whether `meta.set_overrides` lands as
`null` on the `--set`-constructed `CES-P60` leg (Stage-A §9 item 5 reported that it does) and
**reports what it observes**; `SCN-FIX3` owns the repair.

**Rule 31 `[R-RETAIN]` — no bundle is deleted on this lane's judgement of promotability.** Every
solved bundle stays on local disk; `.gitignore`, not `rm`, discharges rule 29(c) and rule 15's
retention. The container is ephemeral, so **the FINDING asks the promotion question explicitly**
and states what is on disk that will not survive the session.

**Rule 27 `[R-PUSH]`:** no existing source file ≥300 lines is rewritten; every push touching one is
verified by fetch-back. **No CI workflow is created.** **No default is moved.** **No solve is run
that is not named in §4 of this document or in a pushed addendum to it.**

---

*Written before the first solve. `git log --oneline -1` at writing: `4e4ad90d`.*
