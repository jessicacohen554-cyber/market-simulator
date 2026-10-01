# SHARD REPORT — SPP-62 SPAN (2023 · 2024 · 2025)

**Charter** `docs/handoffs/PRECOMMIT-spp-62-2026-09-10.md` §9–§10 ·
**Protocol** `docs/handoffs/shard-launcher-protocol-2026-09-09.md` §3, §6, §7 ·
**Role** §3 SPAN shard — the only registerable one · **DATA PROFILE** `spp`.

**RUN_ID `2026-09-10-spp-62-vintage-census`** · bundle `results/calibration/spp62_span`.

---

## 1. HARD STOP 1 — the pin

```
git rev-parse HEAD = 67feede7403240374091cc73a536d836ba6d08c4   ✓ matches
```

No `git pull` / `rebase` / `merge` / `fetch` was run at any point before the final push.

## 2. HARD STOP 2 — the config signature (control `spp52a_fossil93`)

```
vintage_arm_before = False                       ✓
CC_REGULAR   [0.93, 0.93, 0.93, 0.93]            ✓
CC_CHP       [0.93, 0.93, 0.93, 0.93]            ✓
CT_CHP       [0.93, 0.93, 0.93, 0.93]            ✓
CT_PEAKER    [0.93, 0.93, 0.93, 0.93]            ✓
ST_GAS       [0.93, 0.93, 0.93, 0.93]            ✓
COAL         [0.93, 0.93, 0.93, 0.93]            ✓
COAL_BIT     [0.93, 0.93, 0.93, 0.93]            ✓
COAL_LIGNITE [0.93, 0.93, 0.93, 0.93]            ✓
COAL_PRB     [0.93, 0.93, 0.93, 0.93]            ✓
COAL_WC      [0.93, 0.93, 0.93, 0.93]            ✓
wc -l data/raw/_processed-legacy/coal_supply_SPP.csv   = 32   ✓
grep -c "^6193,prb,"                                   =  1   ✓
```

## 3. The solve — ONE invocation, three years, sequential (rules 12 / 16)

```
.venv/bin/python scripts/replay_keeper.py results/calibration/spp52a_fossil93 \
  --years 2023 2024 2025 \
  --out-dir results/calibration/spp62_span \
  --set eia860_vintage_tracks_solve_year=true \
  --note "SPP-62: eia860_vintage_tracks_solve_year over the R-ay coal supply-class census
          repair (--census-vintage 2023 2024 2025). Full span, rule 16 [R-ALLYEARS],
          one input snapshot."
```

**Wall clock 440 s = 7.3 minutes** (LP through the last diagnostic write), inside the rule-32
20-minute shard budget. ONE input snapshot; the span was never split into per-year bundles.

## 4. HARD STOP 3 — armed, all three years present

```
armed = True
years = [2023, 2024, 2025]
hourly/ = class_band_hourly_{2023,2024,2025}.parquet, class_hourly_{…}, network_{…},
          storage_{…}, system_{…}, unit_hourly_{…}                        (18 files, 3 years)
```

## 5. MEASUREMENT — verbatim

```json
{
 "2023": {
  "class_twh": {
   "CC_CHP": 1.8535, "CC_REGULAR": 42.4877, "COAL_LIGNITE": 7.2935, "COAL_PRB": 66.8769,
   "CT_CHP": 1.2108, "CT_PEAKER": 16.2967, "OTHER": 0.5072, "ST_CHP": 0.3027,
   "ST_GAS": 7.0867, "biomass": 1.1014, "hydro": 8.3441, "nuclear": 16.927, "oil": 0.0,
   "solar": 0.5876, "wind": 113.7572
  },
  "bare_COAL_twh": 0.0, "total_gen_twh": 284.633, "system_demand_twh": 284.5182,
  "C3a": 25.6527, "C3b": 0.1723
 },
 "2024": {
  "class_twh": {
   "CC_CHP": 1.8882, "CC_REGULAR": 42.2992, "COAL_LIGNITE": 6.6375, "COAL_PRB": 61.7175,
   "CT_CHP": 1.2419, "CT_PEAKER": 18.7383, "OTHER": 0.5987, "ST_CHP": 0.4101,
   "ST_GAS": 10.3858, "biomass": 1.1803, "hydro": 8.9666, "nuclear": 15.0157, "oil": 0.003,
   "solar": 1.1942, "wind": 120.7235
  },
  "bare_COAL_twh": 0.0, "total_gen_twh": 291.0005, "system_demand_twh": 290.8868,
  "C3a": 25.7858, "C3b": 0.1725
 },
 "2025": {
  "class_twh": {
   "CC_CHP": 1.9439, "CC_REGULAR": 35.8242, "COAL_LIGNITE": 6.9856, "COAL_PRB": 81.4384,
   "CT_CHP": 1.1544, "CT_PEAKER": 14.8826, "OTHER": 0.4891, "ST_CHP": 0.1823,
   "ST_GAS": 9.2059, "biomass": 0.949, "hydro": 8.8207, "nuclear": 15.7804, "oil": 0.0,
   "solar": 2.3258, "wind": 122.043
  },
  "bare_COAL_twh": 0.0, "total_gen_twh": 302.0253, "system_demand_twh": 301.8402,
  "C3a": 29.2249, "C3b": 0.1669
 }
}
```

**Bare `COAL` = 0.0000 TWh in ALL THREE YEARS** — the identity limb that killed SPP-61 holds
across the span, not just in the screen year.

**2023 reproduces the screen to four decimals**: C3a 25.6527, C3b 0.1723, ΔCOAL_PRB +3.4118.

## 6. Control differencing — rule 29(b) form 4, the committed keeper IS the control

Against `results/calibration/spp52a_fossil93/hourly/` (no control solve was spent). TWh, P1:

| year | COAL_PRB | COAL_LIGNITE | ST_GAS | CT_PEAKER | CC_REGULAR | bare COAL | Σ class |
|---|---|---|---|---|---|---|---|
| 2023 | 63.4651 → **66.8769** (+3.4118) | 7.8875 → 7.2935 (−0.5940) | 8.3546 → **7.0867** (−1.2678) | 17.8622 → 16.2967 (−1.5655) | 42.4753 → 42.4877 (+0.0124) | absent → **absent** | +0.0054 |
| 2024 | 59.4628 → **61.7175** (+2.2547) | 6.5031 → 6.6375 (+0.1343) | 11.9700 → **10.3858** (−1.5842) | 19.7797 → 18.7383 (−1.0414) | 42.1065 → 42.2992 (+0.1927) | absent → **absent** | +0.0061 |
| 2025 | 81.8127 → 81.4384 (−0.3743) | 7.0252 → 6.9856 (−0.0396) | 8.4024 → **9.2059** (+0.8035) | 15.2290 → 14.8826 (−0.3463) | 35.8740 → 35.8242 (−0.0497) | absent → **absent** | −0.0029 |

Conservation holds in every year (|Σ Δclass| ≤ 0.0061 TWh; model total tracks system demand
to ≤ 0.19 TWh, the dump/slack residual).

C3, arm vs the control's own committed sidecars:

| year | C3a control → arm | C3b control → arm |
|---|---|---|
| 2023 | 25.4689 → 25.6527 | 0.1647 → 0.1723 |
| 2024 | 25.2967 → 25.7858 | 0.1761 → **0.1725** |
| 2025 | 29.6357 → 29.2249 | 0.1755 → **0.1669** |

C3b **improves** in 2024 and 2025 and gives back 0.0076 in 2023; every year stays far inside
the 0.20 band. C3a stays within +1.3 % to +2.2 % of actual in all three years.

## 7. VERDICT — full dump

```
DETERMINATION: NOT-YET
GRADE: {'scored': 7, 'target_grade': 5, 'commercial_grade': 0, 'ledgered': 0, 'fails': 2}
CAVEATS: {'protective': [], 'ledgered': [], 'commercial_band': [],
          'budget': {'protective_max': 0, 'ledgered_max': 1}}
REASONS: ['governance gate UNATTESTED: no governance attestation in bundle']

### fuelmix status=FAIL
    CC_REGULAR   2023 PASS    model= 42.125 actual= 45.694 | -3.57 TWh, share -1.3pp
    CC_CHP       2023 PASS    model= 1.853  actual= 1.737  | +0.12 TWh, share +0.0pp
    CT_PEAKER    2023 PASS    model= 15.621 actual= 13.214 | +2.41 TWh, share +0.8pp
    ST_GAS       2023 FAIL    model= 6.64   actual= 15.02  | -8.38 TWh, share -2.9pp (volume out of band)
    ST_CHP       2023 PASS    model= 0.303  actual= 0.533  | -0.23 TWh, share -0.1pp
    COAL_PRB     2023 PASS    model= 66.877 actual= 65.279 | +1.60 TWh, share +0.6pp
    COAL_LIGNITE 2023 PASS    model= 7.293  actual= 9.396  | -2.10 TWh, share -0.7pp
    COAL_BIT     2023 PASS    model= 0.0    actual= 0.035  | -0.03 TWh, share -0.0pp
    CC_REGULAR   2024 PASS    model= 41.908 actual= 45.894 | -3.99 TWh, share -1.4pp
    CC_CHP       2024 PASS    model= 1.888  actual= 1.869  | +0.02 TWh, share +0.0pp
    CT_PEAKER    2024 PASS    model= 18.633 actual= 15.908 | +2.72 TWh, share +0.9pp
    ST_GAS       2024 FAIL    model= 10.386 actual= 20.098 | -9.71 TWh, share -3.3pp (volume/share out of band)
    ST_CHP       2024 PASS    model= 0.175  actual= 0.525  | -0.35 TWh, share -0.1pp
    COAL_PRB     2024 PASS    model= 61.718 actual= 59.953 | +1.76 TWh, share +0.6pp
    COAL_LIGNITE 2024 PASS    model= 6.638  actual= 8.669  | -2.03 TWh, share -0.7pp
    COAL_BIT     2024 PASS    model= 0.0    actual= 0.035  | -0.04 TWh, share -0.0pp
    CC_REGULAR   2025 SKIPPED model= 35.824 actual= 42.762 | preliminary EIA-923 vintage: incomplete plant data (5/22 prior plants missing (77% reporting)); not gated — C2 family grid reconcile covers this class
    CC_CHP       2025 SKIPPED model= 1.944  actual= 1.831  | preliminary EIA-923 vintage: complete plant data (no per-class actual); not gated — C2 family grid reconcile covers this class
    CT_PEAKER    2025 SKIPPED model= 14.267 actual= 11.284 | preliminary EIA-923 vintage: incomplete plant data (46/62 prior plants missing (26% reporting)); not gated — C2 family grid reconcile covers this class
    ST_GAS       2025 SKIPPED model= 8.767  actual= 20.104 | preliminary EIA-923 vintage: incomplete plant data (16/36 prior plants missing (56% reporting); plant-months 96% present); not gated — C2 family grid reconcile covers this class
    ST_CHP       2025 SKIPPED model= 0.152  actual= 0.341  | preliminary EIA-923 vintage: immaterial plant data (no per-class actual); not gated — C2 family grid reconcile covers this class
    COAL_PRB     2025 SKIPPED model= 81.438 actual= 74.572 | preliminary EIA-923 vintage: incomplete plant data (3/29 prior plants missing (90% reporting)); not gated — C2 family grid reconcile covers this class
    COAL_LIGNITE 2025 SKIPPED model= 6.986  actual= 8.86   | preliminary EIA-923 vintage: complete plant data (no per-class actual); not gated — C2 family grid reconcile covers this class
    COAL_BIT     2025 SKIPPED model= 0.0    actual= 0.039  | preliminary EIA-923 vintage: immaterial plant data (no per-class actual); not gated — C2 family grid reconcile covers this class
### sysvol status=PASS
    gas  2023 PASS    model= 66.54 actual= 76.2  | C1 flags: ST_GAS
    coal 2023 PASS    model= 74.17 actual= 74.71 | all classes in band (C1)
    gas  2024 PASS    model= 72.99 actual= 84.29 | C1 flags: ST_GAS
    coal 2024 PASS    model= 68.36 actual= 68.66 | all classes in band (C1)
    gas  2025 SKIPPED model= 63.19 actual= 80.7  | -21.7%
    coal 2025 SKIPPED model= 88.42 actual= 82.1  | +7.7%
### price_mean status=PASS
    None           2023 PASS    model= 25.65 actual= 25.13 | +2.1%
    da_diagnostic  2023 SKIPPED model= 25.65 actual= 27.55 | -6.9% vs DA (DA−RT premium $+2.42)
    None           2024 PASS    model= 25.79 actual= 25.45 | +1.3%
    da_diagnostic  2024 SKIPPED model= 25.79 actual= 28.29 | -8.9% vs DA (DA−RT premium $+2.84)
    None           2025 PASS    model= 29.23 actual= 28.6  | +2.2%
    da_diagnostic  2025 SKIPPED model= 29.23 actual= 30.2  | -3.2% vs DA (DA−RT premium $+1.60)
### price_shape status=PASS
    None 2023 PASS model= 0.172 actual= None | NRMSE 0.172
    None 2024 PASS model= 0.172 actual= None | NRMSE 0.172
    None 2025 PASS model= 0.167 actual= None | NRMSE 0.167
### price_tail status=FAIL
    None          2023 FAIL    model= 0.0 actual= 42.0 | model 0h [energy-only LMP] vs RT actual 42h (0.00×, >$200)
    da_diagnostic 2023 SKIPPED model= 0.0 actual= 6.0  | model 0h vs DA actual 6h (out-of-representation companion)
    None          2024 FAIL    model= 5.0 actual= 59.0 | model 5h [energy-only LMP] vs RT actual 59h (0.08×, >$200)
    da_diagnostic 2024 SKIPPED model= 5.0 actual= 35.0 | model 5h vs DA actual 35h (out-of-representation companion)
    None          2025 FAIL    model= 0.0 actual= 68.0 | model 0h [energy-only LMP] vs RT actual 68h (0.00×, >$200)
    da_diagnostic 2025 SKIPPED model= 0.0 actual= 0.0  | model 0h vs DA actual 0h (out-of-representation companion)
```

## 8. What the shard observed, stated plainly — no verdict is the shard's to give

- **The §10 prediction landed, in both limbs, before any number was read.** 2023 `ST_GAS` was
  predicted to break its ±8.00 TWh band at "roughly −8.2 TWh"; it broke it at **−8.38 TWh**.
  2024 `ST_GAS` was predicted to move the wrong way from −8.13 TWh; it moved to **−9.71 TWh**.
  Neither is a surprise and neither was chased.
- **The identity limb holds across the span**: bare `COAL` carries 0.0000 TWh in 2023, 2024 and
  2025 — the SPP-61 failure mode does not recur outside the screen year.
- **Two failing criteria, so the C3c standing rule (rule 22 `[R-C3C]`) cannot fire**: it needs a
  LONE failure and a PASSING governance gate, and this run has neither.
- **Governance reads UNATTESTED because the arm bundle carries no
  `calibration_attestation.json`.** The control `spp52a_fossil93` **does** carry one;
  `replay_keeper.py` did not propagate it into `--out-dir`. Reported, **not fixed** — writing a
  governance attestation is the parent's act, and this shard makes no edit under `src/` or
  `scripts/`.
- **Rule 31 `[R-RETAIN]`: the bundle is on local disk and was NOT deleted.** It does not survive
  container reclamation. The promotion question is the owner's and the parent's.

## 9. Push verification (rule 27 `[R-PUSH]`)

Recorded at the end of the session — see the commit on `claude/spp62-span`. The run payload
`frontend/data/backcast/runs/2026-09-10-spp-62-vintage-census.js` is **768,863 bytes**, above
`push_files`' ~457 KB cap, so it went over `git push` per Git & Pushing §2.

**VERIFIED, on branch `claude/spp62-span`, commit `54e0c30c`:**

| file | local | remote (`origin/claude/spp62-span`) | match |
|---|---|---|---|
| `frontend/data/backcast/runs/2026-09-10-spp-62-vintage-census.js` | 768,863 B · sha256 `4fb4ecac71eaf662…` | 768,863 B · sha256 `4fb4ecac71eaf662…` | ✓ |
| `docs/handoffs/SHARD-spp62-span.md` | 210 lines · sha256 `b769f04212ad5ce5…` | 210 lines · sha256 `b769f04212ad5ce5…` | ✓ |

`git push` succeeded on the first attempt — no HTTP 408/500, no HTTP/1.1 fallback needed.
Nothing under `dispatch/`, `floors/`, or any top-level `*.parquet` was staged; nothing under
`src/` or `scripts/`; no `keepers/`, `status/` or `calibration-complete.json` was touched;
no PR was opened; no result was deleted.
