# PRECOMMIT caiso-287 — splitting the 270.3 MW between the `startup_aware` gap-merge and the surplus decommit screen, with both attributions named before the shard is launched

**Lane:** CAISO calibration · **Date:** 2026-09-19 · **Keeper UNCHANGED**
`2026-09-12-caiso-275-gascoupling` · **LP spent so far: ZERO.** Predecessors:
`docs/RESULT-caiso286-cc-start-cost-2026-09-19.md` (which re-opened the object) and
`docs/RESULT-caiso285-bridge-candidacy-2026-09-17.md` (which built the partition).

This document exists to fix **the metric, the four verdict words and the cut before the
instrumented replay is solved**. §4 states the measurement. §5 states the gates. §6 names every
outcome, including the two this lane is instructed to be willing to report. Nothing below is
computed yet.

---

## 1. The object, inherited and NOT re-derived (rule 28 `[R-MECH-MATRIX]` (a))

caiso-286 §7 measured, on the code's own per-gap basis rather than caiso-285's uniform-price one,
that **270.279 mean-belly-MW passes the restart inequality at the incumbent $50/MW** and that the
committed `floors/2024_P1.npz` shows those gen-hours floored by **nothing** (0.000 MW by any other
mechanism). The inequality does not fail first. Two screens can remove them and caiso-286 could
not tell which did:

* **(A) the `startup_aware` run screen's GAP-MERGING side effect** — `model/commitment.py:1114`
  rebinds `runs = kept_runs`, so a dropped run *between* two kept runs fuses two short gaps into
  one long one, which raises `hold_cost` linearly in `gap` and, past
  `DA_COMMITMENT_HORIZON_HOURS = 24`, excludes the gap outright at line 1221.
* **(B) the surplus DECOMMIT screen** — `_apply_economic_bridges` (`commitment.py:639-698`)
  reprices gap energy to `surplus_floor_value` in hours where the candidate floors exceed the
  system's dispatchable absorption, then decommits cheapest-startup-first.

caiso-285's `S4 = 0.0 MW` measured that the screen never *zeroes a unit outright* — a different
claim, which caiso-285 itself flagged. The merging channel has never been measured.

## 2. STEP 1 — the artifact audit, done at ZERO LP, with three things CONFIRMED and one CORRECTED

**(a) `--persist-p0-commitment` has no MW sibling. Confirmed.** It writes the bit-packed on/off
pattern only (`run_calibration_full._write_p0_commitment_sidecar`). The pattern recovers the
detector's `runs` at its own `0.05 x pmax` threshold — which is why caiso-285/286 could scan gaps
— but neither screen can be replayed from it: the run screen scores
`sum((price - mc) x dispatch) / pmax` (line 1067) and the decommit screen derives absorption from
the interchange rows' dispatch (line 655-663). **Both read MW.**

**(b) No committed artifact anywhere carries the P0 dispatch. Confirmed by tree read, not
assumed.** `git ls-tree -r 203124e310f7be4f806ad968d6cf5755f96bbc00` over the caiso-285 bundle
returns 17 files whose only dispatch payloads are `dispatch/2024_P1.parquet` and
`dispatch/2024_P1_fleet.parquet`. There is no `_P0`.

**(c) A CORRECTION to a premise caiso-286 did not state.** The screens are fed the **P0 duals**
(`build_caiso_ra_p1_prep` passes `r0.prices`, `pipeline/commitment.py:203-216`). caiso-286's probe
read `hourly/system_2024.parquet` filtered to `df["pass"] == "P1"` — i.e. it priced every gap at
the **P1** dual. The committed sidecars carry P1 only, so no better array was available to it. The
270.279 MW is therefore an upper bound **on a price array the screens never saw**, and this session
persists `r0.prices` so the replay stops approximating it.

**(d) The keeper has BOTH screens armed — verified from its own recorded config, not inferred.**
`scenario_config.caiso_ra_bridge_startup_aware = True` and
`caiso_ra_bridge_decommit = True` in the bundle's `run_config.json`. (Checked because
`caiso_ra_bridge_startup_aware` is **absent from `meta.json`**, where its NYISO counterpart is
present — had the CAISO screen been off, candidate (A) would have been inert by construction and
this session would have ended at zero LP. It is not off.) Also armed:
`caiso_ra_startup_trajectory = True` (so `startup_lead_hours` writes floors the probe must
reproduce); `caiso_ra_min_load_frac = 0.26`; and **off**:
`caiso_ra_mustoffer_quantity_gate`, `caiso_ra_bridge_curtailment_release` (so `release_hours` is
`None`), `negative_renewable_offers` (so `surplus_floor_value = 0.0`).

## 3. THE PERSISTENCE CHANGE — scripts-only, opt-in, write-only, and PROVED byte-identical

`--persist-p0-dispatch`, the MW-valued sibling of `--persist-p0-commitment`, on the same
`persist_p2_state` precedent. It writes `hourly/p0_dispatch_<year>.parquet` (the `(n_gen, T)` P0
dispatch, **float64**, packed per generator) and `hourly/p0_prices_<year>.parquet` (the P0 zonal
duals, carrying their zone **names**).

**Design choices, and why each is the conservative one:**

* **The INPUTS, not a decision ledger.** Instrumenting the two screens to emit verdicts would fix
  ex ante which questions can be asked and would put diagnostic code inside
  `model/commitment.py`. Persisting the two arrays the prep hook actually passes keeps `src/`
  untouched and lets the parent replay the **production** detector offline, unmodified.
* **float64, not float32.** The point is an exact replay, so the reproduction gate (§5 G-R2) is an
  *equality*. Narrowing would buy ~60 MB at the cost of the only property the file has.
* **`hourly/`, not `dispatch/`.** `scripts/regression_gate.py:70` globs
  `(iso_dir / "dispatch").glob("*.parquet")` — a `dispatch/<year>_P0.parquet` would be swept into
  a gate that means P1. `hourly/` is the sibling's own home and nothing globs it for dispatch.
* **The zone NAMES are written, not left to be recomputed.** This is the inherited trap: on a
  `fleet_only` rebuild `config.zones` is `None` and a consumer falls through to `sorted(unique)`,
  reading every price from the wrong zone. The names come from the solve's own
  `iso_config.zone_names`.

**BYTE-IDENTITY, proved rather than asserted — four independent legs:**

1. **No `src/` file is touched, and no `ScenarioConfig` field is added.** `git diff --name-only --
   src/` is empty, so `cache_key()` cannot see the flag and no cached bundle re-keys.
2. **Every added executable line in the solve path is inside an `if persist_p0_dispatch` guard** —
   two `... if persist_p0_dispatch else None` bindings and one guarded dict-merge into
   `p2_state`. At the `False` default the keys are absent and the writer returns `[]`.
3. **The capture is after both LPs have run** (immediately beside the existing
   `_p0_commitment_bits`, before `fleet_arrays` is rebound) and is consumed by nothing downstream.
   The flag is added to `_REUSE_KWARG_EXEMPT`, so `_solve_kwargs_snapshot` excludes it and
   `plan_reuse_solved` is unaffected.
4. **`meta.json` cannot change — measured on a bundle that used the sibling flag.** caiso-285 was
   solved *with* `--persist-p0-commitment`, and the string `persist_p0_commitment` does not occur
   anywhere in its committed `meta.json`. Persistence flags do not reach meta at all, so the only
   difference an armed run carries is **two added files**; no existing file changes.

**Guarded by test** (`tests/iso/caiso/test_caiso287_p0_dispatch_sidecar.py`, 5 cases): the writer
is a no-op without the record; the payload round-trips bit-for-bit; the prices carry their zone
names in the solve's order (fixture deliberately defeats `sorted()`); row-count mismatches raise
rather than pad; and — the load-bearing case — the **real** `caiso_ra_mustoffer_min_gen`, both
screens armed, returns an **identical** floor from the round-tripped arrays as from the originals,
behind a `want.any()` vacuity guard that already caught one inert fixture.

### 3.1 THE SHA SPLIT — stated explicitly, because the handoff forbids leaving it implicit

The intended resolution of handoff §10 was to land this change on `main` first and pin all three
shards to one clean post-merge SHA. **That is not available here:**
`claude/caiso-287-startup-decommit-split-qwdxfc` is this session's designated deliverable branch,
it does not auto-merge, and opening a PR to force it is not authorized. So the handoff's own
stated fallback is taken, and recorded here rather than left implicit:

| shard | pinned SHA | why |
|---|---|---|
| 1, the probe | **`92b8e4dbf6017a8571026c3f58fb20914e590875`** (this branch) | it is the only SHA carrying `--persist-p0-dispatch`, which is the whole point of the probe |
| 2 and 3, the MER controls | **`4583e70b864a7d5c99a206b06eddf3c36af495bf`** (clean `origin/main`) | a control must be a keeper replay with **no** lane-local code in it |

This is **better** for the controls than the merged-first plan, not a compromise: pinned to clean
`main`, they carry zero caiso-287 code, so their G-DRIFT form-4 confirmation is unambiguous and
cannot be explained by anything this session wrote. The probe's extra commit is proved write-only
by the four legs above, and the probe is a throwaway that is never registered in any case.

**Both SHAs were checked to contain the marginal-emission-rate commit**
`2ec096633f5624585eb9db1728ebc7c8ca5ccbdf` (`git merge-base --is-ancestor`), as the append
requires, so no shard can produce a bundle without `marginal_emission_rate`.

## 4. THE MEASUREMENT — a 2x2 over the two screens, at zero further LP

The instrumented replay produces the arrays; **every number below is then computed in the parent**
by calling the production detector offline with the §2(d) recipe.

**The metric.** `M(config)` = the mean, over the **frozen 876-hour belly**, of the total RA-bridge
floor written on `CC_REGULAR` rows:

```
M = (1/876) * sum_{h in belly} sum_{g in CC_REGULAR} floor[g, h]
```

where `floor` is the array `caiso_ra_mustoffer_min_gen` returns. The belly set is caiso-285's,
re-verified by its own `sha256_int32_le[:16] == c5948fb0d43620a1` recipe.

**The four configurations**, every other argument held at the keeper's:

| | `startup_aware` | `bridge_decommit` | |
|---|---|---|---|
| `M_both` | True | True | **the keeper** |
| `M_sa` | True | False | only the run screen acts |
| `M_dc` | False | True | only the decommit screen acts |
| `M_none` | False | False | neither |

**The removals:**

* `R_SA = M_none - M_sa` — what the run screen removes on its own.
* `R_DC = M_none - M_dc` — what the decommit screen removes on its own.
* `R_total = M_none - M_both` — what they remove together.

These need not sum to `R_total`: both screens can remove the same MW, and that overlap is the
reason the outcome set in §6 has four members rather than three.

## 5. PRE-REGISTERED GATES

**G-R — REPRODUCTION. A failure STOPS THE SESSION and is reported as a defect** (the caiso-286
G-C discipline), never worked around.

* **G-R1** — the rebuild re-asserts caiso-286's published census: fleet rows **1,705**; belly sha
  **`c5948fb0d43620a1`**; bridge-eligible rows **74**; econ-eligible `CC_REGULAR` **30**; and the
  `p0_dispatch` / `p0_commitment` / `floors` unit-id vectors **identical** to the rebuilt fleet's.
* **G-R2** — the keeper configuration reproduces the committed floor. Because
  `floors/2024_P1.npz` records **one winning mechanism id per gen-hour** (max-composition), the
  checkable form is stated here rather than after the fact:
  * on gen-hours with `mechanism == MECH_RA_MUSTOFFER`: `floor_mine == min_gen` **exactly**;
  * elsewhere: `floor_mine <= min_gen` (another mechanism wrote higher).
  This equality is only available because §3 persists float64.
* **G-R3** — `M_both` reproduces the published actual RA `min_gen` belly mean **670.470** to
  within **+/- 0.05 MW**.

**G-S — THE SPLIT.** Computed only if G-R passes. Cut fixed here at **70 %** of `R_total`:

| verdict | condition |
|---|---|
| **(A) GAP-MERGING DOMINANT** | `R_SA >= 0.70 * R_total` and `R_DC < 0.70 * R_total` |
| **(B) DECOMMIT DOMINANT** | `R_DC >= 0.70 * R_total` and `R_SA < 0.70 * R_total` |
| **BOTH-SUFFICIENT** | both `>= 0.70 * R_total` — each screen alone removes nearly all of it, so neither is *the* cause |
| **SPLIT** | both `< 0.70 * R_total` — the removal is genuinely joint, and neither dominates |

**G-0 — THE DEGENERATE GUARD, named because it must be reportable.** If
`R_total < 10 mean-belly-MW`, the verdict is **NO-OBJECT**: the two screens do *not* remove the
coverage, and caiso-286 §7's re-opening was itself an artifact of the gap-level upper bound rather
than a live mechanism. This session reports that outcome if it occurs.

## 6. THE OUTCOMES, ALL NAMED BEFORE THE ANSWER IS COMPUTED (rule 1 `[R-STRUCT]`)

**6.1 A verdict is not a proposal.** Whatever G-S returns, **this session arms nothing, changes no
default, adds no `ScenarioConfig` field and promotes nothing.** It produces an attribution and a
RESULT doc.

**6.2 THE TRAP, pre-registered as the handoff §4 requires.** If **(A)** fires, the fix is **NOT**
"disarm `startup_aware` to recover 270 MW". The screen is structurally motivated — a run whose
whole P0 margin cannot repay one startup is a phantom the continuous LP manufactured, and a real
UC would not have started the unit. **Disarming a real mechanism because it costs coverage is the
mirror image of the fitted adder**, and this lane refuses it.

The narrower question, and the **only** one an (A) verdict opens, is distinguished here **before
the numbers are seen**: the screen has two effects that nothing separates today.

* **The INTENDED effect** — a dropped (phantom) run must not *anchor* a bridge leg.
* **The SIDE EFFECT** — because `runs` is rebound, a dropped run also stops *delimiting* gaps, so
  two real gaps on either side of it FUSE into one longer gap that is priced as a single hold and
  may exceed the 24 h DA horizon.

To measure the second without conflating it with the first, the probe additionally computes
`M_sa_anchor`: `startup_aware` applied to **anchoring only** — a dropped run cannot anchor a leg,
but gaps are still measured between **all** detected P0 runs — with `bridge_decommit=False`. Then

```
R_merge = M_sa_anchor - M_sa
```

is the coverage attributable **purely to the fusing**, as distinct from the screen's intended
action. This requires a modified copy of the detector **in the probe script only**; it is a
DIAGNOSTIC, it is never armed, no `ScenarioConfig` field is added for it, and it is reported as a
measurement rather than as a proposal. Pre-registered reading: a large `R_merge` share of `R_SA`
means the *side effect*, not the mechanism, is doing the work — which is a defect in the gap
arithmetic rather than a reason to weaken the screen. A small share means the screen is simply
correct and the coverage was never real.

**6.3 THE OUTCOME THIS LANE IS EXPLICITLY WILLING TO REPORT (handoff §4, §7).** If both screens
are doing exactly what they are designed to do — `R_merge` small, or verdict **BOTH-SUFFICIENT**
with each screen independently justified — then **the 270.3 MW should not be held**, the CAISO
belly has **no remaining identified mechanism**, and this lane says so and **STOPS** rather than
manufacturing one. The keeper stays `CALIBRATED` with its single ledgered C3c, and 2022's C3a miss
never downgrades it (rule 30 `[R-TOUCHPOINT-FOLD]` (c)). The honest successor is then the 2022 C3a
object on its own terms.

**6.4 WHAT THIS SESSION REFUSES, named so it can be checked.**
* **No sweep.** No threshold, margin, horizon or fraction is varied against G-S to find a value
  that moves the verdict. No response curve is selected from; if one is reported it is
  **CONTEXT ONLY**, as caiso-285 and caiso-286 both labelled theirs.
* **`BIN_STARTUP_COST_PER_MW` is not touched.** It is a shared cross-ISO constant
  (`eia860.py:3230`); changing it moves every CAMPD-binned ISO's keeper and re-keys their caches.
  Cross-ISO governance item (rules 25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`), not a CAISO-lane edit.
* **No re-opening of the caiso-286 §9 closed list** (the CC start cost, flat-vs-downtime-keyed,
  CAISO public bids, the CAMPD start-fuel derive) — closed with evidence, and nothing here is new
  evidence against them.
* **The S2 DA-horizon object stays closed**, for caiso-285's own reason.

## 7. THE SHARDS — three, all pinned to ONE clean post-merge SHA

**THE PARENT NEVER SOLVES** (rule 32 `[R-SHARD]` (a)). Every shard pushes its whole bundle to its
own branch by `.gitignore` NEGATION plus a **plain** `git add` (rule 34 `[R-SHARD-PROMOTABLE]`
(a), and the `-f` correction of 2026-09-12).

| # | purpose | bundle | years |
|---|---|---|---|
| 1 | **the instrumented probe** — `--persist-p0-commitment --persist-p0-dispatch` | `caiso275_B_gascoupling_span` | 2024 |
| 2 | **MER control** (append; handoff §10) | `caiso275_B_gascoupling_span` | 2023 2024 2025 |
| 3 | **MER control**, the stamped touchpoint | `caiso275_B_gascoupling_2022` | 2022 |

Shard 1 is a rule-29 `[R-SCREEN]` throwaway probe: **one year, never registered**, its numbers
live in this document and the RESULT. Shards 2 and 3 are keeper replays and are **not new runs** —
no dashboard id is minted, the keeper bundle is not overwritten, nothing is re-registered. Their
`metrics.json` is differenced against the committed keeper's: **identical** confirms G-DRIFT form 4
empirically (rule 29 (b)) *and* is the fourth, empirical leg of §3's byte-identity proof; **any
scored number moving is a finding**, reported, and the session stops.

`--years 2022` is a single invocation for shard 3 because 2022 is a separate stamped bundle, not
extra years on shard 2 (rule 32 (b): one registrable run = one shard = one bundle; folding them
would be the banned fan-out in reverse).

## 8. COST, stated before it is spent

Shard 1: one CAISO year (~10-20 min of LP). Shards 2 and 3: three years and one year of keeper
replay. **The parent spends zero LP**; the entire 2x2, the `R_merge` limb, the scoring and the
differencing are arithmetic over the returned arrays.

CAISO is per-plant multi-zone (1,705 LP rows at 2024), so the append's memory warning is live: each
shard runs the runner **unmodified**, never passes `--no-container-preflight`, and reports the
`container preflight:` and `memory peak:` lines (RSS and RSS+swap) from the **nested** cgroup —
never `free`, never MemTotal (rule 32 (c)(8)). An OOM on the marginal-emission dual is a **finding
about the dual**, not a model regression, and is reported as one.

**Nothing is deleted** (rule 31 `[R-RETAIN]`): the promotion question is surfaced in the RESULT
rather than pre-empted, and no bundle is removed on this session's own judgement.
