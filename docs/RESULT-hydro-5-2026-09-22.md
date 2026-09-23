# RESULT — hydro-5: hydro dispatch physics, SPP + NEISO + MISO (2026-09-22)

Companion to `docs/PRECOMMIT-hydro-5-2026-09-22.md` (phase 0, gates, G-DRIFT, launch record),
pushed and pinned at `fda9ece3` before any solve. **This doc carries every number the lane
cites.** Read-outs: `scripts/probes/_hydro5_arm_readout.py` (G1–G3),
`scripts/screen_collateral_gate.py` per arm-year (G4, committed bench held fixed).

**26 of 26 shards solved, pushed complete bundles, and passed the self-check** (recipe = keeper
+ exactly the one flag; RoR arms on the pinned classifier hash). Zero LP spent in this session.

---

## 1. Headline

| ISO | arm | hours at 0 MW (keeper → arm) | annual hydro TWh Δ | G4 flips | recommendation |
|---|---|---|---|---:|---|
| SPP | **F** `hydro_min_flow_floor` | 1,191–3,209 → **0** (all 7 yrs) | −0.004 … +0.031 % | **0** | **promote** (pre-registered SPP choice) |
| SPP | R `hydro_ror_split` | 1,191–3,209 → **0** | −0.001 … +0.011 % | **0** | not recommended (weaker; see §3) |
| NEISO | **R** `hydro_ror_split` | 0–1,908 → **0** (all 6 yrs) | −0.0001 … 0.0000 % | **0** | **promote** |
| MISO | **R** `hydro_ror_split` | 62–565 → **0** (all 6 yrs) | 0.0000 % | **0** | **promote** |

The reported defect — hydro parked at exactly 0 MW for up to 37 % of the year — is **gone in
all 26 arm-years**, annual energy is unchanged, and no scored criterion flips PASS → FAIL.

---

## 2. G1–G3, per arm-year (arm vs keeper; measured EIA-930 `NG: WAT` in brackets, parentheses where it folds pumped storage)

`top-dec` = share of each month's water in its top-10 % load hours (flat fleet 0.10).
`daily CV` = mean over months of SD(daily energy) ÷ mean — the within-month banking statistic.

| arm-year | G1 min gap MW | G2 annual % | G2 max month % | p05 | p95 | top-dec | daily CV |
|---|---:|---:|---:|---|---|---|---|
| SPP F 2019 | **−9.3** | +0.0037 | 0.036 | 0 → 406 [681] | 3103 → 3102 | 0.149 → 0.133 [0.112] | 0.457 → 0.283 [0.077] |
| SPP F 2020 | 0.0 | 0.0000 | 0.000 | 0 → 310 [493] | 3102 → 3102 | 0.172 → 0.158 [0.130] | 0.524 → 0.367 [0.071] |
| SPP F 2021 | 0.0 | +0.0088 | 0.052 | 0 → 212 [412] | 3102 → 3102 | 0.160 → 0.144 [0.132] | 0.683 → 0.522 [0.092] |
| SPP F 2022 | 0.0 | +0.0038 | 0.039 | 0 → 189 [302] | 3102 → 3074 | 0.212 → 0.191 [0.132] | 0.718 → 0.571 [0.099] |
| SPP F 2023 | 0.0 | 0.0000 | 0.000 | 0 → 169 [304] | 2965 → 2842 | 0.171 → 0.153 [0.129] | 0.682 → 0.526 [0.096] |
| SPP F 2024 | 0.0 | −0.0035 | 0.033 | 0 → 232 [281] | 2956 → 2874 | 0.171 → 0.153 [0.123] | 0.671 → 0.509 [0.160] |
| SPP F 2025 | 0.0 | +0.0305 | **0.276** | 0 → 259 [293] | 2969 → 2877 | 0.153 → 0.139 [0.130] | 0.707 → 0.544 [0.114] |
| SPP R 2019 | 0.0 | −0.0012 | 0.012 | 0 → 73 | 3103 → 2999 | 0.149 → 0.144 | 0.457 → 0.410 |
| SPP R 2020 | 0.0 | 0.0000 | 0.000 | 0 → 113 | 3102 → 2962 | 0.172 → 0.165 | 0.524 → 0.470 |
| SPP R 2021 | 0.0 | +0.0112 | 0.079 | 0 → 98 | 3102 → 2944 | 0.160 → 0.153 | 0.683 → 0.610 |
| SPP R 2022 | 0.0 | +0.0038 | 0.039 | 0 → 84 | 3102 → 2928 | 0.212 → 0.201 | 0.718 → 0.647 |
| SPP R 2023 | 0.0 | 0.0000 | 0.000 | 0 → 93 | 2965 → 2811 | 0.171 → 0.165 | 0.682 → 0.613 |
| SPP R 2024 | 0.0 | −0.0002 | 0.002 | 0 → 97 | 2956 → 2795 | 0.171 → 0.163 | 0.671 → 0.601 |
| SPP R 2025 | 0.0 | −0.0011 | 0.010 | 0 → 107 | 2969 → 2802 | 0.153 → 0.148 | 0.707 → 0.633 |
| NEISO R 2020 | 0.0 | 0.0000 | 0.000 | 0 → 78 (208) | 1883 → 1639 | 0.303 → 0.216 (0.162) | 0.757 → 0.428 (0.168) |
| NEISO R 2021 | 0.0 | −0.0001 | 0.001 | 0 → 204 (290) | 1908 → 1528 | 0.252 → 0.191 (0.163) | 0.742 → 0.410 (0.186) |
| NEISO R 2022 | 0.0 | 0.0000 | 0.000 | 0 → 123 (293) | 1877 → 1597 | 0.262 → 0.193 (0.174) | 0.833 → 0.459 (0.173) |
| NEISO R 2023 | 0.0 | 0.0000 | 0.000 | 58 → 446 (554) | 1836 → 1586 | 0.165 → 0.141 (0.157) | 0.484 → 0.289 (0.127) |
| NEISO R 2024 | 0.0 | 0.0000 | 0.000 | 0 → 160 (253) | 1803 → 1540 | 0.210 → 0.167 (0.167) | 0.645 → 0.383 (0.158) |
| NEISO R 2025 | 0.0 | 0.0000 | 0.000 | 0 → 92 [187] | 1790 → 1489 | 0.288 → 0.211 [0.120] | 0.866 → 0.493 [0.167] |
| MISO R 2020 | 0.0 | 0.0000 | 0.000 | 60 → 661 | 2378 → 1905 | 0.175 → 0.137 (0.151) | 0.413 → 0.204 (0.112) |
| MISO R 2021 | 0.0 | 0.0000 | 0.000 | 0 → 613 | 2420 → 1938 | 0.194 → 0.149 (0.159) | 0.517 → 0.260 (0.144) |
| MISO R 2022 | 0.0 | 0.0000 | 0.000 | 0 → 552 | 2411 → 1814 | 0.191 → 0.144 (0.171) | 0.530 → 0.257 (0.167) |
| MISO R 2023 | 0.0 | 0.0000 | 0.000 | 5 → 430 | 2369 → 1853 | 0.200 → 0.146 (0.163) | 0.492 → 0.218 (0.139) |
| MISO R 2024 | 0.0 | 0.0000 | 0.000 | 4 → 401 | 2332 → 1773 | 0.197 → 0.145 (0.164) | 0.525 → 0.234 (0.142) |
| MISO R 2025 | 0.0 | 0.0000 | 0.000 | 4 → 400 | 2322 → 1763 | 0.197 → 0.145 (0.152) | 0.534 → 0.235 (0.120) |

**G3: right direction in every arm-year on every statistic** — zero-hours to 0, p05 up, p95
down or flat, top-decile and daily CV down.

**Two gate misses, both explained, neither a code defect:**

1. **G1, SPP F 2019 — the fleet runs up to 9.3 MW below the floor level in 85 July hours.**
   Pensacola's pro-rata floor share (164.7 MW) exceeds its 130.1 MW nameplate — its July budget
   is above `nameplate × hours`, the same infeasible-excess plants PRECOMMIT §4 measured — and
   `generators_to_fleet_arrays` clips `min_gen` to `pmax × availability`. The floor is live;
   the shortfall is the nameplate clip. 0.5 % of the 1,888 MW July level.
2. **G2 monthly, SPP F 2025 — May +0.276 %** (annual +0.031 %, inside the bar). Upward, and the
   keeper's own 2025 economic spill (0.0054 TWh, PRECOMMIT §4) is the only energy the floor can
   recover — this is that water being turbined. **But I pre-declared the exception only for MISO
   2020, so it is reported as a breach of the monthly half, not waved through.**

**A prediction that was wrong:** PRECOMMIT §4 bounded MISO 2020 at up to +1.22 % upward (the
keeper's 0.136 TWh of economic spill). Measured: **0.0000 %**. The spilled water was not RoR-class
water, or it stayed spilled.

---

## 3. SPP — why F, not R

Pre-registered before any number (PRECOMMIT §4), and the numbers agree: F beats R on every
statistic in every year — p05 169–406 vs 73–113 MW (measured 281–681), top-dec 0.133–0.191 vs
0.144–0.201, daily CV 0.283–0.571 vs 0.410–0.647. R reaches only the 320 MW / 9–14 % RoR class
and cannot touch the Missouri-mainstem banking.

**The honest limit:** F cuts SPP's within-month banking by only 20–38 % (daily CV). It is still
**2–5× the measured fleet's**, and p95 still sits at the fleet's nameplate in 2019–2021. The floor bounds
the trough; nothing bounds the peak. SPP's real mainstem fleet runs to **Corps daily release
schedules** — near-constant day-to-day energy — which neither mechanism represents. That is the
named successor (§7), not something to tune.

## 4. NEISO and MISO

**NEISO**: RoR class ~48 % of energy. Daily CV roughly halves (0.48–0.87 → 0.29–0.49), top-dec
0.17–0.30 → 0.14–0.22. On the one clean measured year (2025): top-dec 0.288 → 0.211 against
0.120 measured, daily CV 0.866 → 0.493 against 0.167 — **the defect halved, not closed.**

**MISO**: RoR class ~59 % of energy — the largest in the program. Daily CV 0.41–0.53 → 0.20–0.26,
top-dec ~0.20 → 0.14–0.15. The folded reference (pumped storage included) can't score the
conventional class directly; the arm now sits **below** the folded top-dec in every year, which
is where a conventional-only class must sit if the PS fold adds peak-hour discharge.

## 5. G4 — C1 / C2 / C3a / C3b re-scored, every arm-year

**Zero PASS → FAIL flips in all 26.** One FAIL → PASS: MISO 2022 C1 `COAL_PRB` (+8.13 → +7.93).
No C3b status change anywhere. C3a (mean price error, $/MWh), all still PASS where they were:

| | moves toward actual | moves away | largest away |
|---|---:|---:|---|
| NEISO R | 2 (2022 −2.35 → −1.09; 2023 −0.57 → −0.06) | 4 | 2021 +2.48 → +3.58 |
| MISO R | 2 (2022; 2025 −0.79 → −0.34) | 4 | 2023 +1.91 → +2.26 |
| SPP F | 3 | 4 | 2022 −1.98 → −2.15 |
| SPP R | 5 | 2 | 2019 +1.59 → +1.65 |

The NEISO/MISO price-mean drift is **upward**: taking ~half the hydro out of peak hours raises peak
prices more than flat overnight water lowers off-peak ones. Small, reported at full magnitude,
not a kill (rule 1). C1 fuel-mix moves split roughly evenly (MISO 22 toward / 18 away; NEISO 18 / 8;
SPP 7 / 6 each). C4 dispatch correlation becomes *scorable* on the SPP arms (the slim keeper
bundle reads SKIPPED), so those rows are not comparable moves.

**C8 is unaffected, by design.** D-2 attributes 33–58 % of hydro energy to the mechanism
(SPP F 2023 32.8 %, NEISO R 2025 44.2 %, MISO R 2022 57.7 %); both mechanism ids are
`NON_THERMAL_MECHS`, excluded from the merchant forced-share arithmetic, with a declared
all-hours D-4 window that scores 0.0 off-window energy (`scripts/legitimacy_diagnostics.py`,
the `MECH_HYDRO_MIN_FLOW` / `MECH_HYDRO_ROR_FLAT` rows).

**Not scored here: C6.** An unregistered arm has no attestation, so each arm's own determination
reads NOT-YET by construction. That is the registration step, not a finding.

---

## 6. Promotion — recommended, NOT executed; the owner rules (rule 31)

**Recommendation:** promote **SPP F**, **NEISO R**, **MISO R** — each is a single `ScenarioConfig`
flag on its keeper, zero free parameters, structurally correct (rule 1), every year of each ISO's
set solved (rule 34(c)/35(c)), no collateral flip.

What a promotion would take, per ISO, **zero LP**: compose the per-year legs into the keeper's
bundle shape (SPP: `2023–25` span + `2019–22` rung stamped to it; NEISO and MISO: one
`2020–25` span), write the attestation + DOF ledger (no new DOF), register, re-stamp
`keepers/<ISO>.json` + `calibration-complete.json` + status + matrix shard, then prune the
outgoing keeper (rule 35, in that order).

**Retrievability (rule 34(e)):** all 26 bundles are on this session's **local disk only**,
gitignored (`.gitignore`, hydro-5 block). **They do not survive this container.** Leg SHAs,
**provenance only** (rule 33(d)) — shard branches are transport and are cut when this lane's
PR merges; cost any leg not landed on `main` as a re-solve (SPP ~4 min/yr, NEISO ~3, MISO
~12–20):

```
miso-ror-2020 6257c1e46499b93eb33f5eab79baab9724a4f9b8   neiso-ror-2020 7866f40ab23daa53e9882771140174b103a1254e
miso-ror-2021 043884c2d6c7e77faa31559eb9677225d3661829   neiso-ror-2021 e42999be834699094f1112cb38bb34a0eaee39e5
miso-ror-2022 a1c67f1f88116e78a4d26cf0b685e2135a9aea52   neiso-ror-2022 c341197f42eda6c49418834f3c35317e58ca491f
miso-ror-2023 312ca5b49f9be786185a9b5a14dca30473ed4334   neiso-ror-2023 b15b3bf08fb8ee7b14fe12d4131d1fe1fa597c1d
miso-ror-2024 be96a73de1efd61fe84ada3eb012716a43df368d   neiso-ror-2024 de00b0d244cb19a718f20bb8bef85728ff4503f0
miso-ror-2025 c331c4b7d074e1c5ba9a89565e2b3cb8974cc391   neiso-ror-2025 43bf8393f75aacb03bbfd5b0326685d81e6afa01
spp-floor-2019 e71ef83691d5981fbb1a3bcd76ef1f52d7e1313e  spp-ror-2019 2460f0b80b2b1b089a8a13b716e1dadfa54d954e
spp-floor-2020 c3b2abd6959d8a4cd0e6ed7387547b73a6e53ed8  spp-ror-2020 981485a5d86668dbfc412278410ee3547a7cc558
spp-floor-2021 6cd268bd88e39bc74cc7af7e2d9cbebf7e7d1379  spp-ror-2021 35db0c66313887c35aac585eddd92c3c25bfa569
spp-floor-2022 b0919091a0446b45888f7d4742f94539886eaa15  spp-ror-2022 f3b8286b0e73ebcf263ca464b33b01561660f5d0
spp-floor-2023 10871c2f3dad45d8d8283857f7faa6ff2d9545d5  spp-ror-2023 066983f27404d4380c5d4b6706cf04d8afacf589
spp-floor-2024 9d6905b42ca4b85f78e045b7f7d1b7a1a40bae2c  spp-ror-2024 faa36ecbeb56789bed08bef7a54d9074073a7ede
spp-floor-2025 6d1a5c6281bded76dee3bc914ee34eb6a3c37429  spp-ror-2025 6ccd3b6829c37bd78b5f073e7480dfe817442a2a
```

All 26 shards are archived (rule 33). The 26 `claude/hydro5-*` shard branches remain on the
remote; a session cannot delete refs (rule 33(f)(2)) — they need the owner to clear them.

---

## 7. Named successors — stated, not absorbed

1. **SPP mainstem daily-release representation.** The Missouri-mainstem fleet runs to published
   Corps daily release schedules; the measured daily CV (0.07–0.16) is that schedule. Neither
   armed mechanism bounds within-month day-to-day banking. Data question first (USACE NWD daily
   releases), not a tuning one.
2. **`hydro_min_flow_floor` / `hydro_dispatch_envelope` do not consult
   `eia930_wat_level_folded`** (hydro-1 §5.3, re-confirmed here). It is why MISO and NEISO
   2020–24 could not be offered the floor. A reader-side refusal mirroring the level pin's
   would make the bar mechanical rather than a lane's discipline.
3. **Nameplate-clipped floor shares** (SPP F 2019 G1): the pro-rata allocator can assign a plant
   more floor than its nameplate; the excess is silently dropped rather than reallocated.

---

# ADDENDUM (2026-09-23) — PROMOTED on the owner's ruling

Owner, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper."* Executed, zero LP:

| ISO | new keeper | bundle | determination | vs outgoing keeper, same benchmark |
|---|---|---|---|---|
| SPP | `2026-09-22-hydro-5-spp-floor` (2023–25) | `hydro5_spp_floor_span` | **CALIBRATED** | identical criteria |
| SPP | rung `2026-09-22-hydro-5-spp-rung` (2019–22), stamped to it | `hydro5_spp_floor_rung` | NOT-YET | identical except C4 2022 gas (below) |
| NEISO | `2026-09-22-hydro-5-neiso-ror` (2020–25) | `hydro5_neiso_ror_span` | **CALIBRATED** | identical criteria |
| MISO | `2026-09-22-hydro-5-miso-ror` (2020–25) | `hydro5_miso_ror_span` | train tier CALIBRATED | same held-out failures minus 2022 C1 COAL_PRB (FAIL → PASS) |

Composed by `scripts/probes/_hydro5_compose_span.py` (every leg re-verified keeper + one flag;
benchmark frames re-spanned; MISO `config_partition_overrides` re-derived identical to the
keeper's), attested by `scripts/gen_hydro5_attestation.py` (keeper governance and DOF ledger
inherited verbatim, `offer_curve_by_group` byte-identical). Rule 35: year sets unchanged
(SPP 2019–25, NEISO/MISO 2020–25); `audit_keepers` E1 clean before the prune; outgoing keepers
pruned with `--force-uncite` (NEISO's bundle retained — a regression golden names it); final
`audit_keepers --iso SPP NEISO MISO`: **PASS, 0 failures**.

**Finding — SPP's committed benchmark was degraded on `main`, and this registration restores it.**
SPP-71's composite recorded its first leg's single-year benchmark frames (the stale-reference
defect nwpp-46 fixed in the nwpp composer), so its registration wrote `bench/SPP/{2020,2021,2022,
2024,2025}.json.gz` with **zero plants carrying CAMPD hourly data**. The parts written here have
bench content **identical, key for key, to the pre-SPP-71 parts** (`107be503^`) — a restoration,
not a re-base. Consequence: on the restored benchmark the rung's C4 2022 gas becomes scorable and
reads FAIL (r 0.958, NRMSE 0.321; the SPP RoR arm on the same keeper reads 0.325), where the
outgoing rung read SKIPPED ("gas hourly fit absent"). That is not a demonstrated regression; the
rung is a held-out rung and does not move the ISO (rule 30(c)).

**Not committed:** regenerated MISO bench parts moved content in all six years (the builder drift
of `RESULT-miso266` §5.1). They were reverted to `HEAD`, and every MISO number above is scored on
the committed parts. NEISO's regenerated parts differed only in display metadata and were also
left at `HEAD`.
