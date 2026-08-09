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

*(filled from the completed legs — see §4.1–§4.5)*

## 5. Registration

## 6. Scope guards discharged
