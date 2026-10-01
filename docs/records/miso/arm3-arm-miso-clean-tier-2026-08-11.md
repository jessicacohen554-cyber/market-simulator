# ARM-3-ARM — the corrected MISO clean-tier rows, armed as the shipped forecast default

**Owner card D-29 (sitting Addendum AK.8, signed 2026-08-11) EXECUTED.** This lane
implements a signed decision; it did not re-decide it. Nothing measured here contradicts
the signed evidence, so the escalation clause never fired.

**Branch:** `claude/arm-miso-clean-tier-default-jqwfpc` off a freshly fetched
`origin/main` (`e346cfb`).
**Pre-registration:** `docs/handoffs/PREREG-arm3-arm-miso-clean-tier-2026-08-11.md`,
pushed (`0b7ff76`) **before** the arming edit and **before** any solve.
**Arming commit:** `90bbacf`.

**Scope discharged:** MISO only (rule 25). Forecast mode only, 2031–2035 (rule 22 —
the holdout freeze is ACTIVE and MISO holds no marker; no out-of-training backcast year
was solved, scored or registered). Forecast namespace only (rule 15). No keeper contact.
No backcast-registry touch. No new `ScenarioConfig` field, no new tunable, no CI workflow.

---

## 1. Headline

> **`miso_clean_tier_rows` is now the MISO forecast default**, armed through
> `ISOConfig.default_scenario_overrides` — the same seam D-26 used for Arm 2 — with the
> `ScenarioConfig` field default deliberately held at `False`. **The stop-the-line
> pre-flight guard PASSES: the Arm-2 RPS duals are bit-stable at `[0, 30, 0, 30, 0]` in
> every year of the armed-default solve.** The armed default resolves to cache key
> `9337e00504e1e72a` — **byte-identical to the signed ARM3-FIX armed leg** — so what now
> ships is exactly the scenario the signed evidence measured, and the solve reproduces its
> behaviour: **MI's clean row is exactly 0.0000 in 2031–2034 and BINDS in 2035, its first
> statutory obligation year, pinned at the $30 ACP ceiling; MN slack in all five years.**
> The arming is a declared **cache epoch for the MISO forecast lane**
> (`cd2403cc031515db` → `9337e00504e1e72a`); the global pinned default key
> `603c2498bf71d21d` is **unmoved**. Registered
> `miso-2031-2035-arm3arm-clean-armed-default` (forecast namespace only).

## 2. The arming: which seam, and why it is forced

The `ScenarioConfig` field default stays `False`. The arming is one line in
`config/iso_configs.py::_miso_config`:

```python
default_scenario_overrides={
    "entry_vre_capacity_revenue": True,
    "miso_rps_compliance_regions": True,
    "miso_clean_tier_rows": True,      # <- D-29
},
```

That choice is forced by two independent constraints, not a style preference:

* **Rule 25 `[R-ISO-SCOPE]`.** The field default is ISO-agnostic. `True` there would arm
  the family for all six ISOs, and `MISO_CLEAN_TIER_REGIONS` has no member outside MISO.
  It would also trip the strict, one-directional Arm-2 dependency — `runner.py` refuses
  `miso_clean_tier_rows` without `miso_rps_compliance_regions` — for the five ISOs that
  never carry the K-row grain.
* **Cache identity (rule 24 `[R-REGISTRY]`).** `cache_key()` drops an
  `_CACHE_KEY_OPTIONAL_FIELDS` member when it equals the **live field default**. Holding
  that default at `False` is precisely what makes an armed run differ from it and so
  **enter** the digest. Flipping the ledger line to `"True"` would do the *opposite* of
  arming: every armed run would drop the field and silently re-use its pre-arm bundle.
  The ledger line now carries a comment saying so.

**Forecast scoping is at CONSUMPTION, and Arm 3 grows no gate of its own.**
`runner.run_scenario_iso` builds `clean_region_arrays` only *inside* the
`_rps_region_grain_active(config, iso)` branch, so Arm 3 inherits Arm 2's MISO-only +
`mode == "forecast"` gate wholesale (rule 19 `[R-ONE-MECH]` — one gate, not two). The
backcast lane is doubly insulated: `run_calibration_full.py` never applies
`default_scenario_overrides` at all, and `rps_enabled` is `False` in every backcast.
Both legs are proven by test, not asserted.

## 3. THE CACHE EPOCH — declared and measured

Measured by `scripts/probes/_arm3arm_cache_epoch.py` (committed with the prereg), which
computes keys off the live config and solves nothing — run **before** the arming commit
and again **after**:

| key | pre-arm | post-arm |
|---|---|---|
| GLOBAL pinned default `ScenarioConfig()` | `603c2498bf71d21d` | `603c2498bf71d21d` — **unmoved** |
| MISO forecast lane **resolved** default | `cd2403cc031515db` | **`9337e00504e1e72a`** |
| resolved `miso_clean_tier_rows` | `false` | **`true`** |

**`cd2403cc031515db` → `9337e00504e1e72a` IS the cache epoch for the MISO forecast lane.**
Every MISO forecast bundle addressed under the pre-arm key is superseded, and **none is
silently re-used** — the armed value differs from the registered field default and
therefore enters the digest. The epoch is scoped to the *forecast* lane: no MISO backcast
key shifts, so `2026-08-09-miso-148-basis-aware` and every other MISO backcast bundle key
exactly as before (pinned by test).

**Both poles reproduce the signed ARM3-FIX pair byte-exactly at HEAD** — pre-arm equals
its control key, post-arm equals its armed key. The armed default therefore resolves to
*the very scenario the signed evidence measured*, not a lookalike.

**Reproduction trap, recorded because it cost this lane a false start.** The ARM3-FIX pair
ran `--golden-posture` with the **scalar** `capacity_market_clearing` left `False`; the
golden posture supplies the per-ISO `capacity_market_clearing_by_iso` seam instead. The
sidecars' `capacity_market_clearing: true` is MISO's *resolved* per-ISO value, not the
scalar. Reproducing with `cmc=True` yields different keys, which on first measurement
looked like HEAD drift and was **not** — verified by re-measuring against the ARM3-FIX-era
config, which produced the same mismatched keys. The probe's docstring carries the note.

## 4. THE BINDING PRE-FLIGHT GUARD — **PASS**

**The Arm-2 RPS duals are `[0, 30, 0, 30, 0]` (MN, MI, WI, IL, MO) in EVERY year
2031–2035 of the armed-default solve.** The stop-the-line condition did not fire; no
escalation was required.

| year | LP status | **Arm-2 RPS duals** | guard |
|---|---|---|---|
| 2031 | Optimal | `[0, 30, 0, 30, 0]` | PASS |
| 2032 | Optimal | `[0, 30, 0, 30, 0]` | PASS |
| 2033 | Optimal | `[0, 30, 0, 30, 0]` | PASS |
| 2034 | Optimal | `[0, 30, 0, 30, 0]` | PASS |
| 2035 | Optimal | `[0, 30, 0, 30, 0]` | PASS |

**2035 is the year that carries the guard**, and it is worth saying why the other four
are near-free. Arm 3 can only disturb Arm 2 where Arm 3 is *doing* something, and MI's
clean row is at RHS 0 until 2035. So 2031–2034 test that arming is inert while the rows
are slack; **2035 tests that a clean row can bind at its $30 ACP ceiling without moving
the RPS grain it rides on**. That is the case that passed.

**Reported precisely, not normalised:** the LP returns IEEE **negative zero** (`-0.0`)
for a slack row's dual. `-0.0 == 0.0` is `True` but the sign bit differs, so "bit-stable"
is asserted here on **numeric equality**, which is the correct standard for a dual, and
the raw values are printed in the reader's output rather than rounded away.

**Instrument.** The committed ARM3-MEASURE probe
(`scripts/probes/_arm3_clean_row_horizon.py`) requires an armed/control **pair** for its
R4 delta table, and this lane has only the armed leg (§6). Its own extractors —
`run_key_dir`, `duals_from_parquet` — were therefore imported and used **byte-identical**
(the committed-prereg discipline: reuse, do not re-derive); no dual is re-computed here.

## 5. The armed-default solve

```
uv run python scripts/run_full_horizon.py --iso MISO --start-year 2031 --end-year 2035 \
    --golden-posture --out-dir results/arm3arm/miso-2031-2035-armed-default
```

**No clean-tier flag was passed** — that is the whole point of the demonstration. 5 years
sequential, 1 concurrent, 3,727.5 s wall, peak RSS 9,877.4 MB, all five year-solves
`Optimal`, exit 0. Registered `miso-2031-2035-arm3arm-clean-armed-default` (forecast
namespace only).

### 5.1 E2 — the leg armed itself, and the record proves it three ways

* The run's **own** `config.yaml` records `miso_clean_tier_rows: true` and
  `miso_rps_compliance_regions: true`, `mode: forecast`.
* It landed in cache-key directory **`9337e00504e1e72a`** — the post-arm pole of the
  declared epoch (§3), now confirmed by a solve rather than only by config arithmetic,
  and byte-identical to the signed ARM3-FIX armed leg's key.
* The sidecar's `miso_clean_tier_rows: true` is **machine-verified, not asserted**:
  `register_forecast_baseline._extra_meta_spec` auto-declares config-named `--extra-meta`
  keys as `FromConfig`, so the registrar refuses a record that disagrees with the solved
  config. **Falsifier run:** re-registering with `{"miso_clean_tier_rows": false}` is
  REFUSED — *"record says False but config.miso_clean_tier_rows is True"* — and writes
  nothing. The check bites, so the `true` in the committed sidecar means something.

### 5.2 E1 / E3 — the clean duals reproduce the signed evidence exactly

| year | MI obligation | **MN clean dual** | **MI clean dual** |
|---|---|---|---|
| 2031–2034 | .0000 | 0.00 | **0.00** (RHS-0 arithmetic certainty) |
| **2035** | **.4560** | 0.00 — SLACK | **30.00 — BINDS @ the $30 ACP ceiling** |

Every pre-registered expectation hit: MI's onset is **2035, its first statutory
obligation year**, pinned at the ACP ceiling; MI is exactly 0.0000 in the four
zero-obligation years; **MN is slack in all five** under the shipped 5-zone delivery mask.

### 5.3 E4/E5 — and in fact the whole trajectory reproduces

Compared against the committed signed armed leg
(`miso-2031-2035-arm3fix-clean-armed`) at that sidecar's own stored precision:
**every comparable field is identical in every year** — `retire_mw`,
`builds_thermal_mw`, `builds_renew_mw`, `builds_storage_mw`, `reserve_margin`,
`lw_price`, `co2_mt`, `max_hourly_price`, `hours_ge_500`. So E4 holds in its strong
form — **capacity events identical to the digit in every year**, the behavioural check
that E-1 acquires no build limb — and E5's price-only discipline with it.

*(Method note, against interest: a first comparison reported spurious diffs because it
compared this leg's RAW trajectory against the sidecar's ROUNDED values —
`1426.1999999999996` vs `1426.2`, `8714.055974661725` vs `8714.1`. Re-run at the
sidecar's own precision, nothing differs. The artifact was in the comparison, not the
solve.)*

**All 14 forecast invariants are identical to the signed leg in status AND detail text**,
including the three failures: **I3 / I7 / I12** (unserved-slack, reliability floor,
reserve-margin band) fail in 2031–2034 in both. That is the known **cold-2031 seeding**
limitation the ARM3-MEASURE prereg §0.2 declared in advance, not an arming effect — and
its pre-stated bias direction still holds: understated qualifying supply biases the rows
toward binding MORE and EARLIER, so MN's slack is strong evidence, while MI's bind rests
on a ~38 TWh structural gap far beyond what seeding could manufacture.

## 6. The control leg: unreachable by construction, and why that is a finding

**Arming Arm 3 removes the arm-off pole from the CLI.** `apply_iso_scenario_defaults`
applies an ISO override to any field whose value still **equals** the `ScenarioConfig`
default; `miso_clean_tier_rows` is a bool defaulting to `False`, and
`--miso-clean-tier-rows` is `store_true` with **no negative form**. So after D-29 there is
no CLI invocation that reaches a clean-tier-off MISO forecast leg — an explicit "off"
lands on the default and is re-armed.

This was **stated in the pre-registration before the arming commit**, so it is a declared
consequence rather than an omission discovered afterwards. It is the same caveat
`iso_configs.py` already records for `entry_vre_capacity_revenue` and for D-26's Arm 2,
now extended to Arm 3, and the `--miso-clean-tier-rows` help text is updated to say the
flag is redundant for MISO and has no off switch.

**Consequence for the guard's arm-off pole:** it is permanently the **committed** ARM3-FIX
control bundle (`miso-2031-2035-arm3fix-clean-ctrl`, key `cd2403cc031515db`), whose RPS
duals are `[0,30,0,30,0]` in all five years — and whose key this lane reproduced
byte-exactly at HEAD, so it names the same scenario. It is not a re-solve and cannot be
one. Any future session needing a genuine arm-off leg must revert the override on a
branch; that is a code change, not a flag.

## 7. Rule-28 `[R-MECH-MATRIX]` discharge

`docs/codebase-site/data/mechanism-matrix/MISO.js` only (rule 25 — no other ISO's shard
touched). `miso_clean_tier_rows`: **`fc: "O"` → `fc: "K"`**, with the existing ARM3-MEASURE
and ARM3-FIX citation preserved verbatim and the D-29 arming, the cache-epoch declaration
and the control-reachability consequence appended.

The base `docs/codebase-site/data/mechanism-matrix.js` change is **anchor digits only**
(`scripts/check_mechanism_matrix.py --fix-anchors`), rebasing the line numbers this
commit's +36 net lines in `scenarios.py` shifted. No row, verdict or keeper stamp touched
— the frozen pre-2026-08-11 stamp log is intact. `check_mechanism_matrix.py` passes,
including the `--base` diff gate.

## 8. Verification run at HEAD

| check | result |
|---|---|
| `tests/regression/test_persisted_identity.py` + `test_cache_key_default_flip_guard.py` (**the exact `cache-key-pin` CI command**) | 22 passed |
| `tests/unit/config/test_miso_rps_region_arming.py` | passed (see §9) |
| `tests/unit/config` + `tests/unit/policy` + `tests/unit/pipeline` | 886 passed, 27 subtests |
| `tests/unit/model/test_dispatch.py` | 96 passed |
| `scripts/check_cache_key_registration.py` (HEAD + `--base origin/main`) | ok — no new fields; 165 declared defaults match HEAD |
| `scripts/check_mechanism_matrix.py` (integrity, anchors, stamps, `--base`) | all OK |
| `ruff check` on every touched source file | All checks passed |

**On the CI verdict (card step 3).** The `cache-key-pin` job is `pull_request`-triggered
only, so it does not run on a branch push and no PR was opened (none was requested). Its
verdict is therefore recorded here as the **identical command run at HEAD: 22 passed.**
Whoever opens the PR must still see `Pinned default cache key` green before merging — the
card's "do not merge on a pending check" stands unchanged.

## 9. The test that had to be inverted

`TestD26Arming::test_clean_tier_rows_stays_unarmed_everywhere` asserted the D-22/X.2
blocker — "Arm 3 stays unarmed everywhere". D-29 makes that assertion false, so it is
**replaced by its inverse** rather than deleted, plus four new pins:

* the arming is present for MISO and **absent for every other ISO** (rule 25);
* the seam is the ISO override, with the field default held at `False` and the field
  registered `_CACHE_KEY_OPTIONAL_FIELDS` — the docstring states both reasons a future
  session must not "sync" the ledger line to the override;
* the epoch **moves the MISO forecast key** and **leaves the global pin at
  `603c2498bf71d21d`**;
* rule-22 insulation: an armed *backcast* config still resolves the legacy row, and no
  MISO backcast key shifts.

## 10. What this lane deliberately did NOT do

* **The MISO backcast keeper is untouched.** `2026-08-09-miso-148-basis-aware` scores
  NOT-YET at HEAD (fail set: C3a 2025 −15.6 %, C3b 2025 NRMSE 0.212). That is the
  promotion's **own declared result**, not re-scoring drift (Addendum AK.4). This lane is
  forecast-side and never contacted it.
* **The MN eligibility-mask reading stays open** and is unchanged by arming — the owner's
  statutory call, and decisive for MN. Under the shipped 5-zone delivery mask MN is slack
  in every ramp year; under an in-state (West-only) reading it would be short
  27.1–41.9 TWh and pin at $30 in **all five** years. Arming ships the 5-zone reading, so
  a later flip to in-state would be a materially different MN result, not a refinement.
* **No PJM work** (MISO and PJM never co-run). No other ISO's shard, verdicts or defaults.
* **No P2**, no legacy commitment pass, no new mechanism.

## 11. Successor questions named, not chartered

1. **The MN mask reading** (above) — owner's, and the single largest open item on this
   family.
2. **A reachable arm-off control for ISO-override-armed flags.** Three MISO forecast
   defaults are now unreachable-off from the CLI (`entry_vre_capacity_revenue`,
   `miso_rps_compliance_regions`, `miso_clean_tier_rows`). Every future A/B against a
   MISO forecast default must revert code on a branch. A `--no-iso-scenario-defaults`
   escape hatch would fix all three at once — but it is a new tuning channel in spirit
   (rule 24) and needs its own charter, so it is **named and not built here**.
3. **The 2036+ capacity-screen consequence.** Within 2031–2035 the binding MI dual reaches
   no capacity screen — the 2035 evolution step runs before its dispatch, so the dual
   first reaches a screen in **2036**, outside the measured window. The first year in
   which arming can move a MISO capacity decision is therefore **unmeasured**. Any lane
   extending the horizon past 2035 should expect that to be where E-1's price-only
   behaviour is first genuinely tested.
