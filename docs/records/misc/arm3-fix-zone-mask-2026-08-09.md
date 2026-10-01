# ARM3-FIX — the clean-tier generator-column zone mask, fixed and re-measured

**Owner decision D-28 option A, step 3 follow-through: fix the defect ARM3-MEASURE found,
then re-run the pre-registered 2031–2035 measurement so the Arm-3 arming card gets real
evidence.** FIX + MEASUREMENT ONLY. **No arming decision (`miso_clean_tier_rows` stays
default-OFF), no keeper contact, no backcast-registry touch.** The arming card is the
MANAGER's to put and the OWNER's to sign; this document is its evidence table.

**The finding this fixes:** `docs/handoffs/arm3-clean-row-horizon-2026-08-09.md` §3 —
`model/lp/rows.py::_build_rps_region_rows` zone-masks a clean row's WIND/SOLAR columns but
appended its `region_gen_idx` columns with no zone filter, because
`_resolve_clean_region_gen_idx` resolved by FUEL ALONE across the whole fleet. Michigan's
East-only row (MCL 460.1029, in-state systems only) was satisfied by MISO-South nuclear,
defeating its own cited statutory basis. Corrected offline, MI-2035 flipped SLACK → BINDS
(53.324 TWh in-mask supply vs a 95.771 TWh obligation; leak 85.788 TWh-yr MI /
49.056 TWh-yr MN).

**Branch:** `claude/arm3-fix-zone-mask-eqcghk` off fresh `origin/main` (`51d4e98`).

---

## 1. The fix (one seam, one commit)

### 1.1 What changed

`_resolve_clean_region_gen_idx(fleet, region_fuels)` →
`_resolve_clean_region_gen_idx(fleet, region_fuels, eligible_zone_mask)`:

```python
zone_idx = np.asarray(fleet.zone_idx, dtype=int)
mask = np.asarray(eligible_zone_mask, dtype=bool)
# (K, n_gen): generator g is zone-eligible for region r. One gather, no
# per-region zone loop.
gen_in_mask = mask[:, zone_idx]
...
gidx = np.flatnonzero(np.isin(fuel_idx, codes) & gen_in_mask[r])
```

The resolver now receives the SAME `(K, n_zones)` mask the row builder applies to each
region's wind/solar columns, and admits a generator into region `r`'s index set only when
its fuel qualifies AND its zone is in `mask[r]`. The one call site
(`rows.py::build_constraints`, the clean-family branch) passes `clean_region_zone_mask`
through. A mask/fuels region-axis mismatch is refused with a hard error, never a silent
broadcast.

### 1.2 What deliberately did NOT change

* **The row builder (`_build_rps_region_rows`) is structurally untouched** — it still
  appends whatever `region_gen_idx` it is given. Filtering happens at index construction
  (the resolver), so the builder stays a pure column-append: rule 2 [R-VECTOR] (no hour
  loops, no per-hour masking), rule 3 [R-RENEW-VAR] (wind/solar stay decision variables,
  their treatment byte-identical).
* **The Arm-2 RPS call passes no `region_gen_idx`** and never reaches the resolver —
  untouched by construction (finding §3.3), and pinned by test (§2 below).
* **No `ScenarioConfig` field added, no config value changed, no cache-key surface
  moved.** `miso_clean_tier_rows` remains a registered `_CACHE_KEY_OPTIONAL_FIELDS`
  member at default `False`.
* The credit-side consumer (`policy.clean_tiers.clean_credit_by_fuel`) already masked by
  zone (`eligible_zone_mask & admits`) — the LP row was the only leak. Fixing the row
  brings the row and its credit mapping into agreement.
* `scripts/probes/_arm3_clean_row_horizon.py` is reused BYTE-IDENTICAL (the committed
  prereg protocol — reuse, do not re-derive). Note for readers of its `mask_leak`
  section: post-fix, that read's "as_built" column describes the PRE-FIX construction (a
  counterfactual kept for continuity with the finding's §3.2 table) and "as_intended" IS
  the live row.

## 2. The three-way test evidence

All in `tests/unit/model/test_dispatch.py::TestCleanTierRegionRows` unless noted; the
whole dispatch module (96 tests), `tests/unit/config` (474), `tests/unit/policy` +
`tests/unit/pipeline` (387) and `tests/regression/test_persisted_identity.py` (13) pass
on the fix commit.

**(a) The corrected-offline semantics pin (the finding's §3.2 flip).**

* `test_clean_row_generator_columns_are_zone_masked` — on a two-zone [E, S] system with a
  reactor in each and an E-only clean mask, the clean row carries `+1` on the E reactor's
  `P` columns and NOTHING on the S reactor's, in every hour, while the VRE treatment is
  unchanged (E wind counted, S wind not).
* `test_out_of_mask_nuclear_cannot_satisfy_clean_row` — the MI-2035 flip in miniature: an
  East-only clean row whose only qualifying reactor sits in the other zone is
  certificate-short and escapes at its $30 ACP (dual pins at the ceiling); relocate the
  reactor in-mask and the same row is covered (dual 0). Under pre-fix fuel-only
  resolution both variants read dual 0 — exactly the defect.
* The finding's literal MI-2035 numbers are re-measured on the fixed rows in §4 below
  (they are properties of a solve, not of a unit test).

**(b) Arm-2 non-regression (the stop-the-line guard).**

* `test_arming_clean_family_only_appends_rows` — on ONE layout, the build WITH the clean
  family equals the build WITHOUT it in every shared row, matrix and bounds, with the
  clean rows purely appended; the RPS family block is byte-identical across the two.
* The D-26 armed MISO forecast default's RPS duals are re-measured in §4: [0, 30, 0, 30, 0]
  in every year, both legs — bit-stable through the fix.
* The existing Arm-2 suites pass unchanged: `TestRpsComplianceRegionRows` (the K=1
  legacy-row byte-identity contract), `tests/unit/policy/test_rps.py`,
  `tests/unit/config/test_miso_rps_region_arming.py` (D-26 arming + backcast insulation).

**(c) Default path byte-inert.**

* `test_default_path_never_reaches_the_resolver` — with the clean family OFF (the shipped
  default), constraint assembly never calls the changed resolver on either RPS grain
  (sentinel-patched to raise; and the same sentinel DOES fire when the family is armed,
  so the probe is proven able to detect the call).
* `tests/regression/test_persisted_identity.py::test_default_scenario_config_cache_key_is_pinned`
  — the pinned default cache key `603c2498bf71d21d` is UNMOVED (13/13 pass). The fix adds
  no config field and changes only row construction reached when
  `miso_clean_tier_rows=True`.

## 3. The re-measurement protocol (reused, not re-derived)

The committed ARM3-MEASURE prereg IS the protocol: window 2031–2035 (§0.1 — MI's first
statutory knot at the window's last year, MN's +6.2 pp ramp), cold-2031 seeding with the
pre-stated bias direction (§0.2 — understated qualifying supply biases the rows toward
binding MORE/EARLIER, so a slack row is a strong result and a binding row a weak one),
two legs one flag apart on the `--golden-posture` shipped posture (§0.3, Arm-2 armed in
BOTH via the D-26 ISO default), reads R1–R5 (§0.4), serial legs, armed first (rule 12
memory cap). Probe: `scripts/probes/_arm3_clean_row_horizon.py`, byte-identical.

Pre-stated expectations ON THE FIXED ROWS, written before the solves (this session):

* **R1:** MI dual EXACTLY 0 in 2031–2034 (zero obligation ⇒ RHS 0 — arithmetic
  certainty, unchanged). **MI-2035 expected to BIND, most likely pinned at the $30 ACP
  ceiling** (the finding's corrected accounting: 53.3 TWh in-mask vs 95.8 TWh obligation
  on the defective leg's dispatch; the fixed row now also *pulls* in-mask clean dispatch,
  so the measured shortfall may be smaller, but a ~42 TWh gap is far beyond what
  redispatch can close). **MN expected SLACK through 2035** under the shipped 5-zone
  mask (finding §4: covered 161–174 TWh vs 73–87 TWh targets).
* **R4:** no longer expected to be identically zero a priori — a binding MI row prices
  East clean energy ($30 dual → capacity-screen revenue via `clean_credit_for_zone`) and
  buys ~$1.3 bn of ACP in 2035, so ledger/cost deltas are a REAL read now, not a
  formality. E-1 (R5) still requires: no build limb — any delta must arrive through
  price-taking screens, never a forced build.

## 4. R1–R5 on the fixed rows

Both legs solved on this branch's fix commit against a freshly regenerated
`data/clean` (50/50 datatypes, 0 errors; completeness verified by
`test_resolve_report_no_hard_fail_full_horizon`, not `ls`). **ARMED** key
`9337e00504e1e72a` (75.2 min, peak RSS 9.8 GB), **CTRL** `cd2403cc031515db`
(70.3 min, 9.7 GB) — both cache keys IDENTICAL to the ARM3-MEASURE pair, as the
byte-inertness evidence predicts (code fixed, config untouched). All ten
year-solves `Optimal`, both exits 0. Legs ran serially, armed first.

### 4.1 R1 — the duals: MI's row now binds exactly where the statute says

| year | MN oblig. | MI oblig. | **MN clean dual** | **MI clean dual** | RPS duals (MN,MI,WI,IL,MO) |
|---|---|---|---|---|---|
| 2031 | .6314 | .0000 | 0.00 | 0.00 | 0, **30**, 0, **30**, 0 |
| 2032 | .6468 | .0000 | 0.00 | 0.00 | 0, **30**, 0, **30**, 0 |
| 2033 | .6622 | .0000 | 0.00 | 0.00 | 0, **30**, 0, **30**, 0 |
| 2034 | .6776 | .0000 | 0.00 | 0.00 | 0, **30**, 0, **30**, 0 |
| **2035** | .6930 | **.4560** | 0.00 | **30.00 — BINDS @ ACP** | 0, **30**, 0, **30**, 0 |

Every §3 pre-stated expectation hit: **MI onset = 2035, pinned at the $30 ACP
ceiling** — the row FFR-6B §2.2 sized as materially binding now prices in its first
obligated year; MI 2031–2034 exactly 0 (the RHS-0 arithmetic certainty); **MN slack in
all five years** under the shipped 5-zone mask. **The stop-the-line guard passes: the
Arm-2 RPS duals are bit-stable at [0, 30, 0, 30, 0] in every year of BOTH legs** —
the D-26 armed forecast default is untouched by the fix, in solves, not just in tests.

### 4.2 R2 — composition-independence CONFIRMED at the measured dual

MI's dual sits exactly at the $30 ACP ceiling, where D-28 §2.3 / F-2 §0(3) measured
all defensible §45U compositions coinciding to the cent — and §45U is dead after 2032
(26 U.S.C. §45U(e)) while MI cannot bind before 2035, so **the arming question is
composition-independent under every reading, now confirmed on a binding row** (the
finding could only show it on a slack one). The F-2 seam is consumed, not modified.

Fleet (armed run's own FleetContext, 2031): 13 nuclear units / 11,519.3 MW. MN's
footprint mask pays 8 units / 6,260.4 MW — including the cross-state WI/IL/MO
reactors the charter flags — MI's East-only mask pays 3 units / 2,330.5 MW
(1729_2, 4046_1, 4046_2); the 5 MISO-South reactors (5,258.9 MW) now correctly earn
NEITHER row.

### 4.3 R3 — qualifying supply vs target, and the corrected-number pin

| year | row | target (TWh) | in-mask qualifying (TWh) | slack (TWh) | verdict |
|---|---|---:|---:|---:|---|
| 2031 | MN | 73.336 | 165.156 | +91.820 | SLACK |
| 2032 | MN | 76.629 | 161.227 | +84.598 | SLACK |
| 2033 | MN | 80.025 | 161.270 | +81.244 | SLACK |
| 2034 | MN | 83.527 | 161.207 | +77.681 | SLACK |
| 2035 | MN | 87.136 | 173.584 | +86.449 | SLACK |
| **2035** | **MI** | **95.771** | **57.351** | **−38.420** | **BINDS @ $30** |

* **The finding's corrected-offline number REPRODUCES on the control leg:** CTRL-2035
  in-mask MI supply = **53.327 TWh** vs the finding's offline 53.324 (Δ 0.006%, a fresh
  container's data rebuild). That is the (a) evidence leg landing in a solve.
* **The armed leg's binding row PULLS +4.02 TWh of clean energy in-mask** (53.327 →
  57.351): the $30 incentive produces a real redispatch response — and the remaining
  38.42 TWh gap is structural (East clean capacity), exactly why the row escapes at its
  ceiling. Pre-stated in §3: "the measured shortfall may be smaller, but a ~42 TWh gap
  is far beyond what redispatch can close."
* The `mask_leak` continuity read on armed-2035: as-built-counterfactual (pre-fix
  construction) 143.100 TWh vs live row 57.351 TWh — an 85.749 TWh leak that NO LONGER
  EXISTS in the LP; the table's role is now purely historical continuity with finding
  §3.2.
* **The MN mask question stays decisive and open** (owner's): in-state (West-only)
  counterfactual SHORT 27.1–41.9 TWh in all five years → would pin at $30 every year;
  shipped 5-zone mask → covered every year. Unchanged by the fix, still not this
  session's call.

### 4.4 R4 — what arming changes NOW: nothing until the row binds, everything real when it does

| year | retire MW A/C | thermal add MW A/C | renew add MW A/C | objective Δ (A−C) |
|---|---|---|---|---|
| 2031 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | +150,066 (+0.0007%) |
| 2032 | 633.0 / 633.0 | 0.0 / 0.0 | 0.0 / 0.0 | +88,537 (+0.0004%) |
| 2033 | 1426.2 / 1426.2 | 1306.0 / 1306.0 | 0.0 / 0.0 | +11,566 (+0.0000%) |
| 2034 | 0.0 / 0.0 | 7384.2 / 7384.2 | 5921.8 / 5921.8 | −38,244 (−0.0002%) |
| **2035** | 0.0 / 0.0 | 8714.1 / 8714.1 | 4078.2 / 4078.2 | **+1,174,608,980 (+4.84%)** |

* **Capacity events are identical to the digit in every year** — including 2035, whose
  evolution step runs before its dispatch and whose binding dual can first reach a
  screen in 2036, outside this window. The E-1 charter holds behaviourally: the row's
  only output is a price.
* **2031–2034 objective deltas reproduce the DEFECTIVE pair's alternate-optima noise
  byte-identically** (+150,066 / +88,537 / +11,566 / −38,244 — finding §6's exact
  values): on slack rows the fix is provably a no-op in the solve, not just in the
  matrix.
* **2035 is a real economic event now:** +$1.1746 bn (+4.84% of a $24.3 bn objective) =
  38.420 TWh ACP shortfall × $30 = $1.1526 bn of compliance payments, plus ~$22 M of
  true redispatch cost. Load-weighted price −$0.39/MWh (62.941 → 62.551 — in-mask clean
  displaces marginal fossil in the East), CO2 +0.77 Mt (425.43 vs 424.66 — the
  displaced-elsewhere counterpart), reserve margin / max price / hours≥500 identical.
* Both legs' I3/I7/I12 invariant failures (cold-fleet slack/reserve-margin, 2031–2034)
  are IDENTICAL across the pair and identical to the ARM3-MEASURE pair — the known
  §0.2 cold-seed limitation, not fix-induced.

### 4.5 R5 — E-1 discipline: PASSES

`policy/clean_tiers.py` still exposes exactly four entry points (a target, the row
builder's arrays, two price resolvers); consumers remain `retirements.py` /
`new_entry.py` on the existing revenue seam. No build limb, structurally or
behaviourally (§4.4's identical addition columns).

## 5. Registration

Forecast namespace ONLY (rule 15's forecast clause); the backcast registry untouched.
NEW run ids — the ARM3-MEASURE pair's sidecars are the finding's record and stay
intact:

| leg | run id | cache key | committed sidecar |
|---|---|---|---|
| ARMED | `miso-2031-2035-arm3fix-clean-armed` | `9337e00504e1e72a` | `frontend/data/hindcast/miso-2031-2035-arm3fix-clean-armed.json` |
| CONTROL | `miso-2031-2035-arm3fix-clean-ctrl` | `cd2403cc031515db` | `frontend/data/hindcast/miso-2031-2035-arm3fix-clean-ctrl.json` |

Both sidecars machine-verify `miso_rps_compliance_regions: true` and the per-leg
`miso_clean_tier_rows` against each run's resolved `run_config.json`
(`register_forecast_baseline._extra_meta_spec` auto-declares config-named extra-meta
keys `FromConfig`). `registry/`, `runs/`, `manifest.js`, `program-status.js` are
GENERATED (gitignored; the Pages deploy is their single writer). Out-dir bundles stay
gitignored under `/results/arm3/`.

## 5a. Card-ready summary

> **The Arm-3 blocker ARM3-MEASURE found is FIXED, and the re-measured evidence is
> arming-grade.** The clean-tier rows' generator columns now obey each region's
> eligible-zone mask exactly as their wind/solar columns always did, and on the fixed
> LP the pre-registered 2031–2035 pair shows: **MI's row binds in 2035 — its first
> statutory obligation year — pinned at its $30 ACP ceiling** (in-mask supply 57.4 TWh
> vs a 95.8 TWh obligation), which is precisely the behaviour FFR-6B §2.2 sized the
> row to have and MCL 460.1029 requires; **MN stays slack every year** under the
> shipped 5-zone mask; **the Arm-2 RPS default is bit-untouched** ([0,30,0,30,0] in
> every year, both legs, keys unmoved); and **arming changes no capacity event in the
> window** — the binding row's only output is a price (+$1.17 bn of 2035 compliance
> cost, −$0.39/MWh load-weighted, +4.0 TWh of clean redispatch into Michigan).
>
> **Left open for the card, deliberately:** (1) the **MN eligibility-mask reading** —
> in-state (West-only) would flip MN to binding at $30 in ALL five years (short
> 27.1–41.9 TWh); the shipped delivery-based mask leaves it inert. One line of data,
> owner's statutory call, decisive for MN. (2) The **cold-2031 seeding caveat** carries
> unchanged (§0.2, direction pre-stated: it biases toward binding, so MN's slack is
> strong evidence; MI's bind rests on a 38 TWh structural gap, ~10× the measured
> redispatch response, so seeding alone cannot plausibly explain it). (3) §45U
> composition: measured moot — MI's dual and a live credit can never coexist, and at
> $30 all compositions coincide to the cent.

## 6. Scope guards discharged

* `miso_clean_tier_rows` remains **DEFAULT-OFF**; the armed run IS the measurement. No
  `ScenarioConfig` field added, no RPS/ACP value changed, no cache-key surface moved —
  both legs' keys are byte-identical to the ARM3-MEASURE pair's.
* **No arming decision, no keeper contact, no backcast-registry touch.** The card is
  the manager's to put and the owner's to sign.
* Rule 22: every solve forecast-mode 2031+, the 2026+ clause; no measured actual read
  or scored.
* Rule 28(b): the `miso_clean_tier_rows` cell's `ev.M` citation gains the fix + this
  re-measurement in THIS session. **The verdict stays `O`** — the mechanism is now
  validly testable and tested-by-measurement, but arming is an owner decision this
  session does not take (and rule 25 keeps the verdict per-ISO regardless).
* The F-2 composition seam: consumed, not modified.

## 7. Instrument and operational notes

1. **Probe compatibility repair (one call site).** The committed probe's R2 section
   passed the runtime-key DIRECTORY to `fleet_context`, whose documented contract is
   ONE year parquet; the ARM3-MEASURE container's pyarrow tolerated the directory,
   this one's does not. Fixed to pass the first year parquet (R3 already reads its
   context per year). Protocol, reads and math untouched — recorded per the finding
   §10's own instrument-defect discipline.
2. **The container-pause hazard is real and cost this session ~55 min.** The first
   regen+solve chain was silently killed by a container pause between turns (regen
   died mid-`emissions`, nothing after it launched, zero output). The rerun resumed
   from the completed datatypes and was kept alive by a monitor emitting 15-minute
   heartbeats. Sessions running multi-hour background chains should arm such a
   heartbeat from the start.
3. `regenerate_clean.py`: first pass 6 datatypes + partial emissions before the kill;
   resumed pass completed the remaining 44 with 0 errors. Readiness verified by the
   FF battery (1 passed), not by `ls`.
