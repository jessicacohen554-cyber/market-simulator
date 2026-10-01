# RESULT — SPP-71 (2026-09-22), card R-bc: the charter's channel is refused on a proof, and the object relocates to a floor SPP already had in the wrong place

**Keeper 15 promoted**: `2026-09-22-spp-71-ensemble-syncfloor` (CALIBRATED), rung
`2026-09-22-spp-71-rung-ensemble` (NOT-YET) stamped to it. `audit_keepers --iso SPP`: **PASS, 0
failures** — the two standing SPP-68 E13 failures cleared in this session.
PRECOMMIT: `docs/handoffs/PRECOMMIT-spp-71-ensemble-sync-floor-2026-09-22.md`, pushed at
`6edc996d1051296b6fb62185df7b304adbc7f3d1` **before any shard was launched**.

---

## 0. Headline

**R-bc as chartered is impossible, and the proof is two lines.** The card asked for a reduced-form
curtailment entering as an LP row whose dual reaches the zonal price. Let that row be any upper
limit on wind delivery, `Σ_w W_w(t) ≤ D(t)`:

> If it binds, wind sits at `D(t)` with its own CF bound slack, so the marginal MWh of zonal load
> **cannot** be served by wind — the row forbids it — and the energy-balance dual is the marginal
> cost of the next unit in the stack, a positive thermal offer. **Wind is not marginal and the price
> cannot reach its offer.** ∎

This holds for a variable bound (what `spp_curtailment_ceiling` does) *and* for an LP row.
`FINDING-spp-64` §3 diagnosed the bound and prescribed the row; **the row has the same defect,
because the defect is the DIRECTION OF THE INEQUALITY, not the object it attaches to.**

**What can take a zonal price to the wind offer is supply pushed UP from below** — and SPP's keeper
already carried that mechanism, in the wrong place. The lane therefore relocated R-bc to the coal
synchronization floor's **placement rule**, armed it, and promoted it.

**It works structurally and it is small on the gates. Both halves are reported at full magnitude.**

---

## 1. What was armed

`ScenarioConfig.coal_sync_ensemble_level` (SHARED, GATED, default off, registered in
`_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit).

```
floor_p(t) = coal_sync_pmin_mw_p × online_frac_p        in EVERY hour          (arm)
floor_p(t) = coal_sync_pmin_mw_p  on the top round(frac × 8760) load hours,
             0 everywhere else                                                  (shipped)
```

`online_frac` is a measured **marginal probability** — the CAMPD share of hours the plant is
synchronized. The shipped code spends it as a **degenerate** distribution (P(sync | top-k load
hour) = 1, P(sync | else) = 0), which is false on the unit's own physics: a coal unit's min-down is
12–48 h and its start cost five figures, so its online hours are multi-day runs that span load
troughs. The arm is the **continuous-relaxation image** of the same commitment — what a Bernoulli
variable relaxes to in a pure-LP dispatch model with no integrality — and it is the answer the
repo's own rule-17 declaration already gave: `legitimacy_diagnostics.py`,
`(MECH_COAL_MUSTRUN, None): (0, 24)`, *"the driver-justified window is ALL 24 hours BY DRIVER … there
is no hour-of-day the driver says it is off."*

**Zero new free parameters, zero new data.** DOF ledger **5 entries / 3 residual**, the same five
names as keeper 14. `offer_curve_by_group` byte-identical (SHA-256 `090abd793b5fa5a7`).
Rule 19 `[R-ONE-MECH]`: it **replaces** the placement in place — the armed branch short-circuits
before the force-all branch, the `load_rank` branch **and** pjm-h16's day-grain window — and it
replaces `spp_curtailment_ceiling` as R-bc's answer; the two are never co-armed.

---

## 2. How it was solved

**Seven shards, one per year 2019–2025** (rule 36 `[R-YEAR-ISOLATION]`), all at pinned HEAD
`6edc996d`, **each solving CONTROL AND ARM in its own container**. The differencing is therefore
exact by construction and rule 29(b) form 4 is **not relied on** — which matters, because G-DRIFT
found 14 changed files on the audited solve path since keeper 14's basis sha, including the very
block this arm edits. The parent ran **no LP**.

**Single-delta verified**: `coal_sync_ensemble_level` is the **only** differing `scenario_config`
key in all seven years.

Rule 25 `[R-ISO-SCOPE]`, proven by construction **and** by census: all 51 committed run configs
re-key byte-identically and the field appears in none.

---

## 3. THE STRUCTURAL RESULT — the reason for the verdict

Fleet coal hourly minimum against the measured EIA-930 SWPP COL minimum:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| control, MW | 1,816.2 | 464.8 | 388.8 | 113.5 | 280.1 | 168.8 | **27.5** |
| **arm, MW** | **2,433.4** | **1,499.5** | **1,378.3** | **1,381.8** | **945.9** | **1,262.3** | **1,057.9** |
| measured, MW | 3,817.0 | 2,259.0 | 1,711.0 | 2,203.0 | 1,565.0 | 2,384.0 | 2,128.0 |
| control / measured | 0.476 | 0.206 | 0.227 | **0.052** | 0.179 | 0.071 | **0.013** |
| **arm / measured** | **0.638** | **0.664** | **0.806** | **0.627** | **0.604** | **0.530** | **0.497** |

**K-1 (the pre-registered over-forcing limb) PASSES in all seven years** — the arm never exceeds the
measured minimum. The two placements spend the **same** measured annual synchronized MWh
(ensemble/window **0.985–0.994**, the residual being the per-plant `pmax × availability` clip), so
only the placement moved.

The floor reimplementation used to design this was **validated against the bundle's own realised
`min_gen`** before any counterfactual was quoted: max |Δ| **0.0 MW**, r **+1.0000**, all seven years
(`scripts/probes/_spp71_floor_delta.py`).

---

## 4. THE GATE RESULT — small, and said so in advance

**P-1, hours at the wind offer (−26.000):**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| control | 0 | 169 | 505 | 511 | 393 | 461 | 435 |
| **arm** | **8** | **280** | **578** | **580** | **440** | **532** | **513** |
| measured negative | 547 | 936 | 1,108 | 995 | 992 | 1,172 | 1,018 |
| **gap closed** | 1.5 % | 14.5 % | 12.1 % | 14.3 % | 7.8 % | 10.0 % | 13.4 % |

Up in **all seven years**. Closing **1.5–14.5 %** of the gap.

**P-2, wind volume — the weakest leg, and the PRECOMMIT said so before the solve.** Wind falls
0.004 / 0.163 / 0.262 / 0.310 / 0.140 / 0.264 / 0.263 TWh against an excess of 1.2 / 8.3 / 9.0 / 9.9
/ 8.9 / 11.7 / 11.6 TWh — **about 2 %**. **R-bc does not close SPP's wind volume defect.**

**P-3, price.** Mean falls $0.028 / 0.406 / 0.275 / 0.260 / 0.183 / 0.199 / 0.180. Price CV rises in
every year toward the actual.

**P-4, congestion rent — success condition (3) is NOT met.** Mean |N−S| moves 0.035→0.035,
0.086→0.089, 1.521→1.553, 4.312→4.340, 0.640→0.664. Up in six of seven years, **by hundredths of a
dollar**, against a measured $12–17. Reported as a null result, not dressed up.

**P-5, coal volume** rises 0.071 / 0.285 / 0.270 / 0.325 / 0.196 / 0.315 / 0.262 TWh. The declared
risk (COAL_PRB already long in 2021/2022/2025) materialised at that magnitude and moved no C1 row.

Slack and dump are **unchanged in every year** (2022's 274.6 MWh is identical in both legs).

---

## 5. SCORED AGAINST THE PRE-REGISTERED TABLE

| leg | predicted | realised | verdict |
|---|---|---|---|
| P-1 offer hours | +9 / +85 / +61 / +61 / +46 / +56 / +56 | +8 / +111 / +73 / +69 / +47 / +71 / +78 | **BEAT in 6 of 7** — the first-order estimate held the LP's dispatch fixed and could not see it re-optimise |
| P-2 wind TWh | −0.005 / −0.129 / −0.237 / −0.269 / −0.119 / −0.196 / −0.202 | −0.004 / −0.163 / −0.262 / −0.310 / −0.140 / −0.264 / −0.263 | slightly **larger** in 6 of 7 |
| P-3 mean $ | −0.03 / −0.29 / −0.22 / −0.22 / −0.16 / −0.20 / −0.18 | −0.03 / −0.41 / −0.28 / −0.26 / −0.18 / −0.20 / −0.18 | slightly **larger**, same sign |
| P-5 coal TWh | +0.006 / +0.197 / +0.269 / +0.303 / +0.154 / +0.265 / +0.255 | +0.071 / +0.285 / +0.270 / +0.325 / +0.196 / +0.315 / +0.262 | larger, same sign |

**Direction correct on every leg in every year; no prediction wrong-signed.** The one honest miss is
that the PRECOMMIT's headline framing (§5.1) understated the price leg by ~25 % because the
zero-LP instrument cannot re-optimise; it flagged itself as a lower bound and was.

**All five kill limbs held**: K-1 PASS ×7; K-2 no C3a/C3b flip in 2023–2025; K-3 negative hours rose
in 7 of 7 (bar was 5); K-4 C8 PASS; K-5 no C1 row moved status.

---

## 6. DETERMINATION

| criterion | arm span | keeper 14 span | arm rung | keeper 14 rung |
|---|---|---|---|---|
| C1 fuel-mix | PASS | PASS | PASS | PASS |
| C2 system volume | PASS | PASS | PASS | PASS |
| C3a mean LMP | PASS | PASS | FAIL | FAIL |
| C3b price shape | PASS | PASS | FAIL | FAIL |
| C3c price tail | CAVEAT | CAVEAT | CAVEAT | CAVEAT |
| C4 dispatch corr | PASS | PASS | **PASS** | **FAIL** |
| C6 governance | PASS | PASS | PASS | PASS |
| C8 forced share | PASS | PASS | PASS | PASS |
| **determination** | **CALIBRATED** | CALIBRATED | NOT-YET | NOT-YET |

**No criterion regresses in either direction in any of the seven years, and the rung's C4 flips
FAIL → PASS** — the only status move anywhere.

---

## 7. GOVERNANCE

- **Rule 35 `[R-PROMOTE]`** — year union enumerated **before** the prune (2019–2025, unchanged);
  keeper written, rung stamped (rule 30(a)), `build_status.py --iso SPP` rebuilt,
  `audit_keepers --iso SPP` run **between** the promotion and the prune (E1 clean), then four
  superseded runs pruned with `--force-uncite` and `--keep` for the rung. Final audit: **PASS**.
  `calibration-complete.json` re-keyed with the determination re-verified.
- **Rule 31 `[R-RETAIN]`** — nothing was deleted before the owner ruled. The per-year shard bundles
  are gitignored (rule 32(d)), never `rm`'d.
- **Rule 34 `[R-SHARD-PROMOTABLE]` (e) — retrievability.** The registered keeper and rung bundles
  are on `main` inside this lane's commit. The 14 per-year shard bundles are on their shard
  branches, which are **transport, not storage** (rule 33(f)) — treat any leg not in the registered
  composite as a **re-solve** (~5 min/year).
- **Rule 28 `[R-MECH-MATRIX]`** — base row added with the field, a cell line in **every** ISO shard
  (all `U` but SPP), SPP's cell moved **O → K** with keeper/gates re-stamped.
- **Rule 1 `[R-STRUCT]`** — no tuning channel was touched. The band multipliers stay at keeper 14's
  uniform 0.93, byte-identical. Nothing was swept.

---

## 8. WHAT THIS DOES NOT ESTABLISH — and where SPP goes next

- It does **not** close C1. Wind moves ~2 % of its excess.
- It does **not** reach C3c, and it does **not** produce congestion rent.
- **SPP's remaining levers, in the order the evidence now supports.**

  > **CORRECTION, entered after this lane's solves and before its RESULT was final.** An earlier
  > draft of this section read *"the offer-curve family is now unblocked in principle — this card
  > was the thing it was sequenced behind."* **That is wrong, and a stronger cross-ISO result
  > refutes it.** `docs/RESULT-xiso-stack-climb-attribution-2026-09-22.md` (merged to `main` at
  > `919e674d` while this lane's shards were solving, zero LP, 44 `fleet_only` rebuilds) measures
  > the same idle-thermal signature in **nine ISOs of nine** and concludes that **the offer-curve
  > family is refused everywhere BY CONSTRUCTION**, because adding vertical extent above a
  > clearing price that never reaches it is inert. SPP-70 §4 was not measuring an SPP quirk. The
  > family is **closed**, not merely sequenced, and a successor must not re-open it on this
  > lane's evidence.

  1. **DEMAND — untested here and untested by anyone.** The xiso lane's own corrected ranking puts
     it second only to commitment reach and notes it is *"cheap to measure at zero LP"*: whether
     the model's own load is tight in the market's top-1 % hours has never been measured in any
     ISO. For SPP this bears directly on the live rubric failures (§below).
  2. **COMMITMENT REACH** — the xiso lane's new first-ranked lever: the idle capacity concentrates
     in exactly the classes a no-MIP LP commits worst (CT 13–46 %, oil 1–5 %). SPP's fossil fleet
     carries `min_down_hours = min_run_hours = startup_cost_per_mw = 0` on every unit.
     > **CORRECTION (SPP-73, 2026-09-22, measured on a `fleet_only` rebuild of rung 2020):** not every unit. 135 `_committed` tranches (103 gas, 32 coal) carry generic start-up costs (CT $20, ST_GAS/ST_CHP $35, CC $50, coal $100 per MW) and the 32 coal `_committed` tranches carry min-run 36 h / min-down 16 h. What is zero is every gas econ/peak tranche's start-up cost and every gas row's min-run/min-down. `docs/handoffs/RESULT-spp-73-commitment-reach-2026-09-22.md` §5.
  3. **R-ba** (the ST_GAS / CT_PEAKER inversion) is untouched and is still the most persistent C1
     error (ST_GAS short 4.41–9.40 TWh in all seven years) — but note C1 **PASSES**, so it is not
     a rubric failure.
  4. **R-be** (the −26.000 price floor is a clamp, not a distribution) is untouched.

- **SPP's LIVE rubric failures are four rows, all on the rung:** C3a 2020 **+17.3 %** (band ±10 %),
  C3b 2020 / 2021 / 2022 **0.267 / 0.243 / 0.208** (band 0.20). The span is clean. 2022 is 0.008
  over its band. `SPP-69` §5 characterised 2020: the whole year's price lives in a **$13.35** band
  and never exceeds **$36.21**, against an actual with **23 hours above $200**.
- Every number here is model-**SELECTION** evidence. `[R-HOLDOUT]` was removed 2026-09-09, so no
  year is out-of-sample and none of this is a certified skill claim.
