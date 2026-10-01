# PRECOMMIT — SPP-43: the 2019–2022 CAMPD unit-outage intake

**Lane** SPP-43 · **Date** 2026-09-16 · **Base** `a9599d150d2c97bed523944297d19074acda7cc5`
**Keeper** 12, `2026-09-16-spp-42-commitment-feasibility`, bundle `results/calibration/spp42_span_a`
**Held-out control** `2026-09-13-spp-40-holdout-span`, bundle `results/calibration/spp40_holdout` (COMMITTED)
**DATA PROFILE** `spp`

---

## 1. The object

SPP's CAMPD unit-outage extracts covered **2023–2025 only**. In the held-out
years availability was therefore the **flat EFOR baseline**, and every
outage-conditioned mechanism was inert there. Two open defects root-cause to
that single gap:

1. Keeper 12's `mustrun_commitment_feasibility_clip` is **provably inert** on
   2019–2022 — the engine's own line, *"21 floored plant-groups tested, 0
   infeasible plant-hours, 0.0 MWh of commitment floor released"* — so
   `spp42_span_b` came back byte-identical to the stamped holdout run.
2. SPP-40's held-out **C8 ST_GAS `forced_share` breach** (0.504 / 0.556 in
   2021/2022 against a 0.30 cap) is still open: the floor forces plants in hours
   the meter says they were out, with no overlay to relax it.

This lane closes the data gap. It is a **data intake, not a mechanism**: no
`ScenarioConfig` field is added or changed, no gate is armed, no `--set` is
passed, and `offer_curve_by_group` is replayed byte-identically.

## 2. Phase 0 — the source survey, done BEFORE anything was proposed

`scripts/probes/_spp43_source_survey.py` (committed). Rule 29 `[R-SCREEN]` step 0.

**State panel.** 13 of SPP's 14 CAMPD detection states carry a complete
`{STATE}_{YEAR}.parquet` in **every** year 2019–2025. The 14th (**CO**) is
absent in **every** year *including 2023–2025*, so the committed block was
itself derived on the same 13-state panel. **The gap is purely temporal, never
spatial.**

**Corpus completeness.** Every 2019–2022 year spans Jan 1 → Dec 31 with
8.58–8.69 M rows, against 8.74–8.81 M in 2023–2025.

**Fleet CEMS coverage — 2019–2022 equals or exceeds the in-sample years:**

| year | model plants | ST_GAS | COAL |
|---|---|---|---|
| 2019 | 112 / 213 | 19 / 23 | 26 / 29 |
| 2020 | 109 / 213 | 18 / 23 | 25 / 29 |
| 2021 | 107 / 213 | 17 / 23 | 24 / 29 |
| 2022 | 107 / 213 | 17 / 23 | 24 / 29 |
| *2023* | *107 / 213* | *17 / 23* | *24 / 29* |
| *2024* | *105 / 213* | *17 / 23* | *23 / 29* |
| *2025* | *106 / 213* | *17 / 23* | *23 / 29* |

All four plants carrying SPP-42's residual D-4 failures — **1230, 1235, 1271,
3008** — file CEMS in all seven years.

**Verdict: the source data fully supports the intake.**

## 3. What was derived, and why it is a FIRST derivation

Rule 23 `[R-FROZEN-DERIVE]`: **extending an extract's YEAR RANGE on unchanged
source data is a first derivation for those years, not a re-derivation against
a residual.** No detector threshold, constant or setting was touched — the
intake invocation differs from the committed one in `--years` and nothing else
— and the derived years were never compared against a residual before being
kept.

```
derive_campd_unit_outages.py --iso SPP --years 2019 2020 2021 2022
derive_campd_unit_outages.py --iso SPP --years 2019 2020 2021 2022 \
    --short-windows --min-outage-days 1.0 --min-inmerit-hours 6
```

| extract | 2019 | 2020 | 2021 | 2022 | (2023 | 2024 | 2025) |
|---|---|---|---|---|---|---|---|
| standard | 943 | 932 | 982 | 946 | *880* | *905* | *936* |
| short | 181 | 239 | 379 | 270 | *163* | *211* | *246* |

Class composition matches the in-sample years (ST_GAS 429/385/402/401 against
344/390/407; COAL 219/239/207/216 against 268/272/212).

## 4. Additivity — proven, not asserted

* diff committed → extended: **3,803 additions / 0 removals** (short: 1,069 / 0);
* the committed block's bytes are unchanged **including line positions**
  (`sha256` over the original byte length is equal: `735d27fe37047a3b…`,
  short `b5a0a63ee7879e34…`);
* **no new row has `outage_end >= 2023-01-01`** (max is 2022-12-31 in both);
* and the statement that actually matters — **the LP's own 2023–2025
  availability multiplier arrays are byte-identical before and after**, all six
  of them (std/short × 2023/2024/2025, `sha256` over the sorted
  `(plant_code, plant_group) → float64` arrays).

**The keeper's scored years therefore cannot move, and are deliberately not
re-solved.** That is a zero-LP kill of a ~10-minute shard, not an assumption.

## 5. Does it reach the LP? — `scripts/probes/_spp43_overlay_reach.py`

Derated `(bin, hour)` cells in the availability multipliers, **before** the
intake the 2019–2022 overlays were **empty (0 bins)**:

| year | std bins | std cells | ST_GAS cells | short bins | short cells |
|---|---|---|---|---|---|
| 2019 | 81 | 383,784 | 208,968 | 25 | 14,424 |
| 2020 | 79 | 403,176 | 212,040 | 23 | 18,072 |
| 2021 | 78 | 390,360 | 210,216 | 24 | 24,576 |
| 2022 | 77 | 362,856 | 201,000 | 22 | 17,688 |
| *2023* | *77* | *358,488* | *166,728* | *20* | *12,624* |
| *2024* | *74* | *336,888* | *153,504* | *18* | *16,632* |
| *2025* | *79* | *369,672* | *169,080* | *23* | *19,008* |

The overlay is now non-empty and **larger** than in the in-sample years. The
flat-EFOR condition is gone.

## 6. Rules and their disposition

* **13 `[R-MEASURED]` — PASSES.** A unit outage window is the rule's own named
  example of an admissible physical availability event, entering as a formulaic
  input. Nothing is pinned to observed generation; no offset, haircut or adder;
  nothing rescaled so an output lands on an actual. The identical construction
  regenerates for a forward year from that year's own EFOR/maintenance envelope.
* **14 `[R-ACCURATE]` IS THE BASIS AND THE RESIDUAL IS NOT.** A flat EFOR
  baseline is an estimate standing in for measured availability that exists on
  disk. **Whatever this does to the fit is a RESULT, never the reason** — a
  degraded criterion is a discovered root cause to route, not grounds to revert.
* **29 `[R-SCREEN]` — NO screen gate and NO residual gate**, on the precedent
  SPP-38's vintage repair set and keeper 12's promotion note records verbatim:
  the screen applies to a candidate *mechanism* competing against a correct one,
  and **a missing measured input is not a candidate mechanism**. Phase 0 was
  done in full regardless and is what set the scope.
* **29(b) form 4 HOLDS — no control solve.** Control = the **committed**
  `spp40_holdout` bundle, differenced. **G-DRIFT:**
  `git diff 520d9fc0 HEAD -- src/market_sim scripts/run_calibration.py
  scripts/run_calibration_full.py scripts/replay_keeper.py scripts/lib
  data/raw/_validation-source data/raw/reference` returns **ZERO changed
  hunks**. The older gap from that bundle's own `git_sha` (`3117f06a`) was
  already closed by an **actual re-solve**: SPP-42 solved these same four years
  at its base and reproduced the bundle byte-identically.
* **21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero free parameters added, zero
  re-cut, no new tunable. `offer_curve_by_group` SHA-256
  `090abd79…62f65`, unchanged.
* **25 `[R-ISO-SCOPE]`** — SPP's own extract files only.
* **16 `[R-ALLYEARS]` / 32(b) `[R-SHARD]` / 34 `[R-SHARD-PROMOTABLE]`** — ONE
  shard, ONE `--years 2019 2020 2021 2022` invocation, ONE bundle, pushed with
  `dispatch/<year>_P1.parquet` and the `_shared/SPP` inputs. SPP's registered
  year set stays at SEVEN: 2023–2025 from the keeper bundle (unchanged, proven
  above), 2019–2022 from this run.

## 7. Reported at the gate, not discovered later

1. **A reproducibility defect in the frozen 2023–2025 block**, found by deriving
   it at HEAD as a control and **deliberately not folded in**: HEAD emits **103
   rows the committed block does not carry — all plant 762 (Ponca) units 3–4,
   ST_GAS — with ZERO removals**. Ponca reaches the deriver only through
   `load_retired_within_window`, so the frozen block predates that scope.
   Changing it would move the keeper's **scored** years and is a separate lane's
   object. The 2019–2022 block **is** derived at HEAD scope and therefore **does**
   carry Ponca, because rule 14 forbids degrading an accurate input to match a
   stale one. **The short extract reproduces byte-identically at HEAD** (coal-only
   scope, which Ponca is not in). → routed as its own item.
2. **The `unit_outages` shared-input hash moves** for any newly captured bundle,
   because the file changed even though its 2023–2025 rows did not. The block is
   provenance only and `replay` ignores it by design; nothing gates on it.
3. **The C8 denominator caution stands and binds this lane.** Held-out ST_GAS
   `forced_share` read 0.3423 / 0.3014 / 0.5041 / 0.5556 in the SPP-40 control
   and 0.2497 / 0.2844 / 0.4559 / 0.4995 on today's base **before this intake** —
   `forced_twh` byte-identical, only `class_total_twh` moved between bases.
   **Every C8 claim this lane makes separates numerator from denominator first.**

## 8. What is measured after the solve (reporting, NOT a gate)

Against the committed `spp40_holdout` control, per year: D-4 off-window binding
rows and their plants; C8 ST_GAS `forced_twh` **and** `class_total_twh`
separately; the C1/C2/C3a/C3b/C4 movement at full magnitude; slack, dump and
energy conservation. **None of these is a promotion condition** — rule 14
decides, and the numbers are the result.

## 9. Promotion question

Asked explicitly in the RESULT, per rule 31 `[R-RETAIN]`. Nothing is deleted
until the owner rules.
