# RESULT — SPP-42: the commitment-feasibility clip (card R-be, open half)

**Lane** SPP-42 · **Charter** `docs/handoffs/PRECOMMIT-spp-42-commitment-feasibility-2026-09-14.md`
**Mechanism base** `78d7c0345d29cef0f45ee3e8721ceecdff577870` (auto-merged to `main`)
**Screen base / span base** `1f586ed75b20db7085eddf70c5c3926687861c69`
**Control** keeper 11 `2026-09-13-spp-38-vintage-cache`, recipe replayed at the SAME base.

---

## 0. Headline

The rule-29 `[R-SCREEN]` screen on **2023** — the year named in the PRECOMMIT on the
mechanism's own largest measured footprint, before it ran — **CLEARS its pre-registered
structural gates**, and the target moves: **D-4 conduct failures 4 → 1** on the screen year.
Plants 1230, 1235 and 1271 all pass; **3008 remains**, which is the one outcome phase 0 flagged
as at risk and is reported rather than absorbed.

**One pre-registered gate clause fails as literally written and is reported, not rewritten**
(§3, G2c). The property it was written to test is proven by a strictly stronger check.

Full span (7 years) solved on that basis. **PROMOTED 2026-09-16 by owner ruling — SPP keeper 12
is `2026-09-16-spp-42-commitment-feasibility`, CALIBRATED, D-4 conduct failures 10 → 2 across
2023-2025. See §7.** The held-out years are covered and the arm is provably INERT there; §7 says
why, and flags one number that must not be read as this arm's.

---

## 1. Phase 0 — what selects the floor's hours, and the re-diagnosis

Established exactly from `run_year(..., fleet_only=True)` rebuilds of keeper 11's own recipe
through the sanctioned `replay_keeper.run_year_kwargs` path. **The selection is the top
`round(online_frac × 8760 / 24)` whole operating days ranked by day-mean SYSTEM LOAD, the
identical ranking for every plant** — verified: the placed day set is a subset of the top-N
day-mean-load days for **all 21 floored plants**, N matching `round(online_frac × 8760 / 24)`,
shortfalls being the availability clip. The plant's own record enters ONLY through the count
and the level.

The confusion matrix (§1b of the PRECOMMIT) splits the four failures in two: 1230 / 1235 /
1271 are a **day**-selection miss (day precision 0.483 / 0.500 / 0.500, within-day 0.855 /
0.907 / 0.847, flat hour-of-day profile); 3008 is a **within-day** miss (day precision 0.812,
within-day 0.601, daytime-cycling 0.22 → 0.80 → 0.27).

**But the day-selection reading is largely wrong.** About half of each failing plant's floored
hours carry a dated ≥5-day CAMPD full-stop outage, and the floor survives it as a fraction of
the plant's own minimum online level — single-unit **Cimarron River (1230, 50 MW) floored at a
median 1.33 MW, 6.2 % of its own 21.6 MW level, across 845 hours its meter reads zero**
(1235 4.00/24.0, 1271 1.68/17.0, 3008 16.91/41.9; passing plants sit at 73–92 %). Because a
committed tranche's `cc_mustrun_pmin_mw` **is** its own `pmax`, the global clip reduces to
exactly `pmax × availability`: the asserted **commitment** inherits the derate **linearly**,
and `np.minimum` substitutes a smaller, equally infeasible commitment instead of none.

**Two sibling routes killed at zero LP** (do not re-reach for them):

1. **`mustrun_layup_window_mask` (miso-173) alone is a rule-19 double-subtraction on SPP.**
   The gate presumes the merit-order guard has removed lay-up windows from availability.
   Keeper 11 runs `campd_outage_merit_order_guard = False`, no
   `campd-unit-outages-perunitmerit-SPP.csv` exists, and **1089 of 1089** rows of
   `campd-unit-outages-layup-SPP.csv` are already present in the `campd-unit-outages-SPP.csv`
   the keeper reads. Availability inside those windows is already 0.040 / 0.182 / 0.108 /
   0.297 on the four plants, and **zero** lay-up hours are left underated.
2. **"Zero the floor wherever any dated outage is present"** removes 1.15 TWh fleet-wide and
   destroys *correct* floors on multi-unit plants (2964: 4,326 of its 4,560 zeroed hours are
   hours the meter says it **was** running).

## 2. The mechanism

`ScenarioConfig.mustrun_commitment_feasibility_clip` (bool, default **False**), registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at that declared default in the same commit as the field. In
`_compose_min_gen_floors`, after the global clip and before `clear_where_unfloored`: the floor
is **zeroed** wherever the plant-group's own available capacity (`Σ pmax × availability`) is
below the committed level it asserts (`Σ cc_mustrun_pmin_mw`); every other hour keeps the
incumbent clip. Masked on the two per-plant commitment mechanism ids.

Rule 21 `[R-DOF]` **zero free parameters, zero new artifacts, loaders or CLI inputs**.
Rule 18 `[R-PHYSICS]` eligibility is unit physics, never a class tuple or plant list.
Rule 13 `[R-MEASURED]` nothing measured enters — both operands are arrays the LP already
holds, so it is **forward-native** and responds in a forecast year to that year's own
availability. Rule 19 `[R-ONE-MECH]` the ONE floor's clip is replaced, nothing stacked; the
committed D-2 confirms `st_gas_mustrun_per_plant` is the **sole** mechanism flooring SPP
ST_GAS. Rule 25 default off, every other ISO byte-identical; all nine matrix shards seeded.

## 3. The screen — 2023, control + arm in ONE shard, same construction

Shard `session_01F3EGvyQVJHkxbY6xE8uQXP`, commit
`48e6f7a5635e1c909ddbb817bcffdeb89faea0c6`, both bundles pushed (16 files each, incl.
`dispatch/2023_P1.parquet`).

**G-DRIFT: form 4 is VOID and the control solve was EARNED.** `git diff 760012f7 <base>` over
the solve path returns 49 files / +4,751 −146, and a **LIVE** hunk sits on the exact path under
test: `arrays.py`'s COD-ramp seam moved to `cod_ramp.generator_online_mask` (SOCO-15 card S12)
and its own comment records that **`min_gen` is now "scaled by the same mask" where it was
previously "zeroed in offline months"**. Not gated on any ISO, live for a backcast SPP run.

**The control is faithful — three independent reproductions of keeper 11's committed 2023:**
D-4 rows identical (1230 bind_h 1287 / med 0.0 / zero 0.6185; 1235 1124 / 0.5632; 1271 836 /
0.5921; 3008 2047 / 0.6087), **C3a +2.43 %** (committed +2.43), **C3b 0.1761** (committed
0.1760).

### Gate table

| id | gate | measured | verdict |
|----|------|----------|---------|
| **G1** | FIRING: placed floor falls by 0.1428 ± 0.005 TWh | placed `min_gen` 22.2420 → **22.0992 TWh**, delta **−0.1428** | **PASS** (hits the zero-LP prediction to 4 dp) |
| **G2a** | exactly one differing `scenario_config` key | `mustrun_commitment_feasibility_clip`: False → True. Only key. | **PASS** |
| **G2b** | `offer_curve_by_group` byte-identical | `090abd79…62f65` in both legs | **PASS** |
| **G2c** | no class other than ST_GAS changes its D-2 forced energy | CC_CHP 0.0533 → 0.0531, CT_CHP 0.0474 → 0.0472 (−0.0002 TWh each) | **FAILS AS WRITTEN — see below** |
| **G3** | ST_GAS gross falls, by ≤ 0.4284 TWh | ST_GAS **−0.1312 TWh**; CC_REGULAR +0.0422, CT_PEAKER +0.0391, COAL_PRB +0.0363, COAL_LIGNITE +0.0101; total +0.0002 on 284.64 TWh; wind +0.0026 | **PASS** |
| **G4** | slack and dump do not increase | slack 0.0000 → 0.0000, dump 0.0000 → 0.0000, hours > $200 0 → 0, price max 61.4221 byte-identical | **PASS** |
| **G5** | no load-bearing PASS → FAIL flip | C3a +2.43 → **+2.52 %** (±10 band); C3b 0.1761 → **0.1768** (≤ 0.20); C1 ST_GAS share_pp **−0.046** | **PASS** |

### G2c — reported, NOT re-read (the SPP-32 discipline)

The clause names a **dispatch** measure (D-2 forced energy = MWh dispatched *at* a floor) to
test a **mechanism** property. It was written loosely, and the 0.0002 TWh CHP movement is
downstream re-dispatch after ST_GAS fell 0.13 TWh — not the mechanism reaching another class.
**I did not rewrite the gate after seeing its number.** The property it exists to test is
proven by a strictly stronger check, pre-registered in the PRECOMMIT's own prose ("every moved
cell carries mechanism id 16 and no other id appears") and re-run here on the **SOLVED** floor
arrays rather than a pre-solve rebuild:

- **6,720 moved `min_gen` cells. Control-leg mechanism stamp: id 16
  (`st_gas_mustrun_per_plant`) on 100 % of them. Arm-leg stamp: id 0 (unfloored) on 100 %.**
- `chp_steam` floor cells (**104,016**) and `nuclear_mustrun` floor cells (**17,520**) are
  **byte-identical across the two legs.**

The owner's call, stated plainly: the gate as drafted is wrong for its purpose, the underlying
confinement is established, and nothing about the arm changed to make it so.

### The target — not a gate, reported after the gates

**D-4 `verdict == "FAIL"` rows: 4 → 1** (23 rows both legs; `passed` stays False).

| plant | control bind_h / med / zero% | arm | verdict |
|------:|---|---|---|
| 1230 | 1287 / 0.000 / 0.6185 | — | **resolved** |
| 1235 | 1124 / 0.000 / 0.5632 | — | **resolved** |
| 1271 | 836 / 0.000 / 0.5921 | — | **resolved** |
| 3008 | 2047 / 0.000 / 0.6087 | 1836 / 0.000 / 0.5839 | **still FAILS** (improved, not crossed) |

D-2 ST_GAS forced energy 2.4998 → **2.4057 TWh**, share of class 0.1935 → **0.1881**.

**3008 is the pre-registered risk landing.** Phase 0 predicted its *placed* median would move
0.0 → 13.8 MW, and the rider scores *binding* hours, where it stays at 0.0. That is exactly the
placed-vs-binding bound §3a of the PRECOMMIT declared and SPP-39 was caught by — **it bit on
one plant of four**. 3008 is also the only multi-unit plant of the four and the one measured
two-shifter in the fleet; its defect is the within-day grain (SPP-27's finding), not the
feasibility clip, so the clip was never the mechanism for it.

**Expectations held.** C1 ST_GAS worsens as declared at the gate: error −6.362 → **−6.494 TWh**
(share_pp −0.046), because the arm removes floor from a class already under-produced. Two
classes improve slightly (COAL_PRB −0.036, COAL_LIGNITE −0.010 on |error|), two worsen slightly
(CC_REGULAR +0.042, CT_PEAKER +0.039). Load-weighted price 25.7440 → 25.7672 (+2.3 ¢/MWh).
**Nothing here is a criterion in either direction** — it is reported at full magnitude.

## 4. Span — launched, seven years, two registrable bundles

Rule 35(b): SPP's registered year set enumerated from `frontend/data/backcast/registry/*.json`
**before** anything is pruned —

- `2026-09-13-spp-38-vintage-cache` → 2023, 2024, 2025 (keeper 11)
- `2026-09-13-spp-40-holdout-span` → 2019, 2020, 2021, 2022 (stamped `holdout.keeper`)

**Seven years; a promotion re-keys all seven** (rule 34(c)). No year is deliberately omitted.

- **Span A** `session_01NE4AXjzKi6ovbRF8KACCDN` — `--years 2023 2024 2025`, one bundle
  `spp42_span_a`, branch `claude/spp42-span-a`.
- **Span B** `session_012XynfrPcZEXDXVXLshcUfR` — `--years 2019 2020 2021 2022`, one bundle
  `spp42_span_b`, branch `claude/spp42-span-b`.

Both pinned to `1f586ed75b20db7085eddf70c5c3926687861c69`, both push their own bundle including
every `dispatch/<year>_P1.parquet` (rule 34(a)).

**Span B carries a headline number this lane owes.** SPP-40 decomposed the held-out C8
`forced_share` breach — ST_GAS **0.504 / 0.556** in 2021/2022 against a 0.30 cap — into a
larger floor plus a collapsing denominator, and named the floor half as the actionable one.
This arm attacks the floor half directly. Whether it moves that number is measured, not
predicted.

## 5. Retrievability (rule 34(e))

| bundle | where | cost to promote from here |
|---|---|---|
| `spp42_screen_ctl`, `spp42_screen_arm` | pushed, recover with `git checkout 48e6f7a5635e1c909ddbb817bcffdeb89faea0c6 -- <path>`; on local disk, `.gitignore`d per rules 29(c)+31 | n/a — a screen is never registered |
| `spp42_span_a`, `spp42_span_b` | each shard pushes its own branch; SHAs recorded on arrival | **zero re-solve** once fetched |

## 6. Rules

Rule 1 `[R-STRUCT]` structure first; no gate reads the target, and the offer curve was not
touched · 12 years sequential within each invocation · 13 `[R-MEASURED]` forward-native,
nothing measured enters · 16 `[R-ALLYEARS]` one bundle per span · 17 `[R-FLOOR-WINDOW]` the
defect is a rule-17 bug by definition and no residual justified the lane · 18 `[R-PHYSICS]`
· 19 `[R-ONE-MECH]` machine-verified on solved arrays · 21 `[R-DOF]` zero free parameters,
ledger unchanged · 23 no derive touched · 24 `[R-REGISTRY]` registered in `ScenarioConfig` +
cache key + `run_config.json` · 25 `[R-ISO-SCOPE]` default off, no number to transfer ·
28 `[R-MECH-MATRIX]` row + nine shard cells added in the mechanism's own commit ·
29 `[R-SCREEN]` phase 0 first, screen year named ex ante on footprint, gates stop-only ·
31 `[R-RETAIN]` nothing deleted, keeper shard untouched, promotion question open ·
32 `[R-SHARD]` the parent solved nothing · 34 `[R-SHARD-PROMOTABLE]` every bundle pushed ·
35 `[R-PROMOTE]` year union enumerated before any prune.

**Housekeeping.** The parity gate is still RED on exactly the two pre-existing non-SPP bundles
`caiso279_ablate_dswcouple_span` and `soco15_spp_arm` (the latter carries "spp" in its name but
is a SOCO bundle). Rule 35(a) is per-ISO — **not pruned by this lane**.

SPP's determination is **UNCHANGED**: `CALIBRATED` on the 2023–2025 train-tier verdict.
`[R-HOLDOUT]` was removed 2026-09-09, so no year is protected from having been iterated
against: that is a **rubric determination, not a certified out-of-sample skill claim**.

---

## 7. PROMOTED — SPP keeper 12 (owner ruling, in-session)

**Owner ruling, verbatim: "Promote it when they land."** The lane had not acted;
`frontend/data/backcast/keepers/SPP.json` was untouched until the ruling (rule 31 `[R-RETAIN]`).

**New keeper: `2026-09-16-spp-42-commitment-feasibility`** (bundle
`results/calibration/spp42_span_a`, committed slim per rule 15). **DETERMINATION CALIBRATED**
(rubric v3.7) — 0 FAILS, 1 ledgered C3c caveat, 0 protective, free-class C1 16/16 all / 12/12
free; C1 / C2 / C3a / C3b / C4 / C6 / C8 all PASS. The same shape as keeper 11 on every scored
criterion.

### Span A — the registered result

| | keeper 11 | keeper 12 |
|---|---|---|
| D-4 conduct FAIL rows | 10 | **2** |
| 2023 | 1230, 1235, 1271, 3008 | 3008 |
| 2024 | 1235, 1271, 3008 | 3008 |
| 2025 | 1235, 1271, 3008 | **clean** |
| C8 ST_GAS forced share (cap 0.30) | .2001 / .1873 / .1535 | **.1881 / .1769 / .1423** |

3008 improves in both remaining years (bind_h 2047 → 1836 and 2427 → 1997; zero share
0.6087 → 0.5839 and 0.5777 → 0.5108) without crossing — the pre-registered placed-vs-binding
risk, on the only multi-unit plant of the four and the fleet's one measured two-shifter, whose
defect SPP-27 already identified as the within-day grain.

### Span B — RE-SOLVED, AND THE ARM IS PROVABLY INERT THERE

**This is the lane's second finding and it would have been easy to misreport.** SPP-42 did
re-solve 2019–2022 with the gate armed (`results/calibration/spp42_span_b`, pushed, recoverable
at `be5123c29d82c74f464ebc0f3bc5061be94975d7`). Its **dispatch is byte-identical** to
`2026-09-13-spp-40-holdout-span` in every class and year (271.8128 / 262.6208 / 269.7705 /
288.1893 TWh), its **D-4 rows are byte-identical** (33 FAIL rows, same plants, same binding
hours, same zero shares) and its **D-2 forced energy is byte-identical** (5.0294 / 4.7849 /
5.4248 / 5.4898 TWh).

**Root cause, measured not assumed: SPP's CAMPD unit-outage extracts cover 2023–2025 ONLY.**
`campd-unit-outages-SPP.csv` holds 880 / 905 / 936 windows in 2023/2024/2025 and **zero rows in
2019–2022**; likewise the short and lay-up companions. So availability in the held-out years is
the flat EFOR baseline — verified directly, `min availcap == p05 availcap` for all 21 floored
ST_GAS plant-groups in 2019 — and the clip's predicate can never fire. The engine says so
itself: *"mustrun_commitment_feasibility_clip ARMED (SPP 2019): 21 floored plant-groups tested,
**0 infeasible plant-hours**, 0.0 MWh of commitment floor released"*.

The held-out run was therefore **re-stamped** to keeper 12 (rules 30(a) / 34(c) / 35(c)) rather
than replaced by a numerically identical twin, and SPP's registered year set stays at **seven**.

> **CAUTION, recorded because the obvious reading is wrong.** Held-out C8 ST_GAS forced share
> reads 0.3423 / 0.3014 / 0.5041 / 0.5556 in the SPP-40 control and 0.2497 / 0.2844 / 0.4559 /
> 0.4995 on this base. That looks like a large improvement and **is not this arm**: `forced_twh`
> is byte-identical and only the **denominator** (`class_total_twh`, the benchmark-side actual)
> moved between bases. **SPP-40's held-out C8 breach is NOT addressed by this lane and stays
> open.** Its root cause is the same missing 2019–2022 outage extract — routed as SPP's next
> **data-intake** item, not a modelling lane.

### Promotion mechanics (rule 35 `[R-PROMOTE]`, in order)

1. **(b) Year union enumerated FIRST**, before any prune: 2019–2025, seven years, from
   `frontend/data/backcast/registry/*.json`. **(c)** covered — 2023–2025 in the keeper bundle,
   2019–2022 in the stamped run.
2. Both spans attested (`scripts/gen_spp42_attestation.py`; the shared
   `gen_touchpoint_attestation.py` still refuses a multi-tier span on a stale `tier_for_year`
   guard, and `replay_keeper --out-dir` still does not propagate the attestation — both
   **reported, not patched**, rule 25). DOF ledger machine-checked: **5 entries / 3 residual on
   both bundles, byte-identical to keeper 11's** — the gate adds zero free parameters.
3. Registered; holdout re-stamped; SPP's corrected caveat text re-applied (a re-stamp resets it —
   the known `stamp_touchpoint_holdout.py` defect, reported not patched).
4. `keepers/SPP.json` promoted; `calibration-complete.json` re-keyed (audit M1a).
5. **(e) `audit_keepers.py --iso SPP` run BETWEEN the promotion and the prune: PASS, 0 failures,
   0 warnings** (E1 and E13 clean).
6. **(a)/(d) `prune_iso_runs.py --iso SPP --force-uncite`** — keeper 11's three stores removed.
   `--force-uncite` is the rule-35(d) **intended** route here, used only after checking where the
   citations are: both are historical prose (`keeper_at_declaration` and the re-key note) and
   **stay**, exactly as rule 35(d) requires. SPP only.
7. Matrix cell **O → K**, shard keeper stamp and §5.7 prose header re-stamped (rule 28).

**One incident, recorded rather than smoothed over.** The first span-B registration attempt
collapsed to the same run id as span A and **overwrote span A's sidecar** (bundle pointer and
years) before dying on the missing shared inputs, which made the keeper briefly re-score
`NOT-YET` with `governance FAIL`. Caught by re-scoring instead of trusting the earlier
`CALIBRATED`, and repaired by re-registering span A. The determination above is the repaired,
re-verified one.

### Housekeeping

`check_registry_payload_parity.py` is RED on exactly the two **pre-existing, committed, non-SPP**
bundles `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` — rule 35(a) is per-ISO, **not
pruned by this lane**. This lane's screen and span-B bundles are **untracked and gitignored** (0
tracked files each), so they cannot exist in a CI checkout; they stay on local disk under rule 31
with their immutable recovery SHAs recorded in `.gitignore`.
