# FINDING — capx T16: the T1.6 driver adjudicated DELETE, executed, and the instrument routed

**Session:** T16 (capacity-expansion / Forecast Finalization track), branch
`claude/t16-driver-adjudication-rgcrmc`. **Date:** 2026-09-01. **HEAD at launch:**
`6eea67c7` (origin/main, D26's merge). **Charter:** adjudicate WIRE vs DELETE for
`renewable_buildout_pace` — the disconnected driver of NEISO's only pre-registered FC-6
battery ladder — execute the decided branch, and re-score FC-6 if the wire branch makes
the ladder non-vacuous.

**Headline: the adjudication is DELETE, and it is not close.** The phenomenon the field
names — VRE buildout pace — **already has a mechanism in this model**: the FF-2A entry
growth ladder (`entry_rate_limits`), a measured, cited, owner-armed constraint whose
EIA-860 throughput seed covers wind and solar explicitly. Wiring a second
slow/mid/aggressive channel onto that same constraint would be a rule-19 `[R-ONE-MECH]`
duplicate built out of uncited rungs (rule 5 `[R-NO-MAGIC]`), authored for no reason but
to give a gate a driver. The field is deleted under rule 26 `[R-DELETE]` with a
`_CACHE_KEY_RETIRED_FIELDS` entry; the **default cache key does not move** and neither
does the golden's own — both measured against an unmodified-`main` control (§4).

**FC-6 cannot clear CAVEAT in this lane, and no honest branch of this adjudication could
have made it.** T1.6 is marked OUT OF SERVICE — its pre-registration stands, it solves
nothing, and its gate rows are emitted `SKIP` + `vacuous`, which FC-6 reads as CAVEAT
(verified end-to-end, §5.2). Choosing a replacement lever is a plan-§2 instrument
decision the charter reserves to the owner; §6 recommends one, priced, with its
confounds ruled out.

---

## 1. Charter discipline (what this lane did NOT do)

No solve of any kind — the wire branch's battery re-run was never reached, so the lane's
solve budget is zero. No golden re-solve (§0v.6(a)/Q16 is owner-gated). No holdout year
touched; nothing in the backcast namespace; no keeper shard, `status/*.js`,
`calibration-complete.json`, or `bench/`. No new GitHub Actions workflow. No threshold,
band, or pre-registered **expectation** edited — T1.6a and T1.6b are byte-identical, and
deliberately so: **it is the instrument that failed, not the claim.** No plan-§2
pre-registration edited. No model parameter, mechanism, or economics moved: after this
lane every solve in the program produces byte-identical results, because the deleted
field reached no solve path to begin with — which is the whole finding.

Rule 28 duties do **not** fire, on the same reading D21 recorded: `renewable_buildout_pace`
has no mechanism-matrix row (it never was a mechanism), no cell moves, and no lever was
tested. The NEISO shard and the §5 lever queue were read at session start; the one
mechanism this finding *recommends* to the owner (`entry_rate_limits`) carries no NEISO
cell and no `R`/`I`/`G` adjudication anywhere, so the DO-NOT-REDO discipline is not
engaged by recommending it. The only matrix file touched is a **mechanical line-anchor
repair** (§7), which the guard itself prescribes and which my `scenarios.py` edit caused.

## 2. Phase 0 — the adjudication

### 2.1 The fact being adjudicated (D21's measurement, re-verified here)

`renewable_buildout_pace: str = "mid"` was declared in `ScenarioConfig`, tagged tier-1 in
`TIER_TAGS`, hashed into every cache key — and read by **no model code**, at `9e56f0f`
and at HEAD alike. D21 measured the consequence rather than inferring it: NEISO's T1.6
rungs `slow` and `aggressive` solved **metric-identically across all 18 extracted
values** (CO2 195.5868 Mt, renewable build 33.0 GW, `rps_dual_over_acp` 1.0, …),
replicated on two independent data vintages
(`FINDING-capx-d21-fc6-battery-2026-08-31.md` §5.1). The ladder solved the same model
twice under different labels.

One correction to the charter's premise, immaterial to the outcome but material to the
remedy: the field was **NOT** registered in `_CACHE_KEY_OPTIONAL_FIELDS` (it predates
that mechanism). It was a full member of the hash. That is *worse*, not better — it is
why the two rungs minted distinct cache keys and both solved — and it is why the
deletion needs the `_CACHE_KEY_RETIRED_FIELDS` route rather than a one-line removal.

### 2.2 Why not WIRE

Four independent reasons, in descending force:

1. **Rule 19 `[R-ONE-MECH]` — the phenomenon already has a mechanism.** VRE buildout
   pace is set by the FF-2A entry growth ladder (`entry_rate_limits`, armed by owner
   decision D-2, 2026-08-02): each tech's annual build is capped at
   `ENTRY_GROWTH_LIMIT_MULTIPLE` (2.0 — the ReEDS growth-constraint hard bound adopted
   verbatim) times its prior maximum annual build, seeded from the measured EIA-860
   record over a trailing 10-year window. `data/build_throughput.py` states in its own
   docstring that **"Wind/solar come from their EIA-860 technology sheets"** — the
   ladder is not thermal-only. Alongside it sit the per-tech queue caps, the ISO budget,
   `entry_commissioning_lag`, the tech availability years, and the economic entry screen
   itself. A `slow/mid/aggressive` scalar layered on that constraint would be a second
   registry channel controlling one physical quantity, and `aggressive` would be
   *definitionally* `entry_rate_limits=False` for VRE — the textbook duplicate.
2. **Rule 5 `[R-NO-MAGIC]` — the rungs have no citation the ladder does not already
   carry.** There is no orphaned constants table waiting for this field (searched:
   no `RENEWABLE_BUILDOUT_*`, no pace ladder, nothing analogous to
   `STORAGE_BASE_FLEET_MW`, which is how the sibling `storage_deployment` is grounded).
   The nearest citable construction — ReEDS's 130 % free-growth band for `slow`, its
   200 % hard bound for `mid`, uncapped for `aggressive` — is exactly reason 1 restated:
   every rung is a state `entry_rate_limits` already expresses. Anything *else* is a
   hand-set multiplier, which is a magic number.
3. **Rule 1 `[R-STRUCT]` — the ordering.** A mechanism enters this model because it is
   real market structure, never because a measurement needs it to move. "Author a lever
   so a gate row stops reading vacuous" inverts that, and would have been the first
   mechanism in the program whose sole justification was an instrument's convenience.
4. **Cost of proof, for a lever that probably cannot move the metric anyway.** WIRE owes
   a byte-neutrality control solve, a matrix row plus a cell line in all six ISO shards,
   parameter citations, spec text, and tests — against a metric (`rps_dual_over_acp`)
   that is **pinned at 1.0 in every year of both existing rungs with 33.0 GW of VRE
   already built**. The charter itself pre-registers that a correctly-wired driver may
   still not move it.

### 2.3 Why DELETE, positively

Rule 26 `[R-DELETE]` is on its face: *"deprecated fitted knobs are removed, not zeroed —
a deprecated parameter that still parses is a re-armable answer key."* The harm here is
not hypothetical and is the exact inverse of a rule-24 `[R-REGISTRY]` off-registry
channel — an **on-registry dead knob**:

- It **minted distinct cache keys for identical solves**. Two runs of the same model got
  two keys, two bundles, and a published two-rung "sensitivity".
- It carried a **fabricated citation** into the parameter registry and the tornado:
  `"NREL ATB entry (renewable_buildout_pace, scenarios.py:65)"` — a line that never
  contained it — attached to a tornado axis whose band could only ever be zero (§3.3).
- It **passed a test that looked like reachability and was not**:
  `test_cache_key_sensitive_to_every_tier1_param` asserted that changing the field
  changes the cache key, and it did, for as long as the field existed (§3.4).

**Routing.** The charter's issuance authorizes executing whichever branch the
adjudication names; it names DELETE, which is executed here in full. The one thing the
charter explicitly reserves — choosing T1.6's replacement lever, a plan-§2
pre-registration act — is **routed, not assumed** (§6).

## 3. What was executed

### 3.1 The deletion + the retired-fields entry (`src/market_sim/config/scenarios.py`)

The field declaration and its `TIER_TAGS` entry are removed, and
`_CACHE_KEY_RETIRED_FIELDS` gains `"renewable_buildout_pace": "mid"` with the citation
chain in its comment. `cache_key()` re-inserts retired names at the default they carried
before hashing, so **removing the knob does not move any key or orphan any cached run**.
A retired entry is hash-only: nothing can assign or read it, so it cannot be re-armed —
which is precisely the failure mode rule 26 targets. `from_yaml` already drops unknown
keys with a loud `RuntimeWarning` (the `pjm_seam_envelope_by_neighbor` precedent), so
every historical bundle config stays loadable; verified on the NEISO golden's own
`config.yaml` (§4).

### 3.2 T1.6 marked OUT OF SERVICE (`scripts/run_driver_battery.py`)

A new `Ladder.out_of_service: str` field. When set, `run_ladder` returns early: **zero
rungs solved**, and every expectation emitted `SKIP` + `vacuous: True` carrying the
reason. Deleting the ladder outright was rejected — it would have hidden a live
pre-registration; the ladder must stay visible and stay unscored. The rung list is
deliberately **empty**, not a pair of dead overrides: a stale override key would be a
landmine the day someone clears `out_of_service`. The retired rungs and the full
adjudication are recorded in the registry comment.

### 3.3 The tornado axis removed (`scripts/run_sensitivity_tornado.py`)

The "Renewable buildout pace" axis was **structurally zero**: low and high arms solved
the same model, so it published a band that could only ever be 0, under the fabricated
citation quoted in §2.3. Removed with the field. A replacement axis, if wanted, perturbs
`entry_rate_limits` and is a separate decision.

### 3.4 Tests, docs, registry

- `tests/regression/test_soundness.py` — the field drops out of `tier1_changes`, and the
  test gains a docstring recording what it does and does **not** establish: cache-key
  sensitivity is a hashing property, not reachability. This field passed it for its
  entire life while reaching nothing.
- `tests/unit/results/test_sensitivity_tornado.py` — the registry-coverage smoke floor
  moves 15 → 14, the count remaining after deleting an axis that measured nothing.
  Stated plainly because it is the one number in this lane that moved in the permissive
  direction: it is a coverage smoke test, not a model gate, and the alternative is a
  test that requires a fake axis to exist.
- `frontend/data/parameters.json` (entry removed surgically — the generator preserves
  rather than prunes retired ids, and re-running it whole would have swept in two other
  lanes' unregistered fields) and its rendered `docs/parameter-citations.md`.
- `docs/codebase/08-config-reference.md`, `model-methodology-spec.md` (its
  `sweep_demand_buildout.yaml` example used the dead field to illustrate sweeps — nine
  cache keys over three scenarios; now `storage_deployment`).
- `tests/golden/ercot_2026_2040.run_config.json` is **untouched by design**: it is a
  seeded historical record regenerated only under the D-7 owner authorization, and its
  staleness test passes unchanged (§4).

## 4. The control (the D26 base-arm pattern, discharged without a solve)

The charter's byte-neutrality requirement is met by measurement against an
unmodified-`main` control, taken by stashing the change and re-running each check:

| Check | origin/main (control) | this branch | Verdict |
|---|---|---|---|
| `ScenarioConfig().cache_key()` | `7a57fadff595ca83` | `7a57fadff595ca83` | **unmoved** |
| NEISO golden `config.yaml` re-hash | `500790494e360a2a` | `500790494e360a2a` | **unmoved** |
| `check_cache_key_registration.py` | ok, 767 fields | ok, 766 fields | pass both |
| `check_mechanism_matrix.py` | integrity OK | integrity OK | pass both |
| **`tests/unit` + `tests/regression`, FULL** | **33 failed / 4385 passed / 32 skipped / 1 xfailed** | **33 failed / 4385 passed / 32 skipped / 1 xfailed** | **identical set** |
| `test_golden_forecast_bands.py` | 2 passed, 1 skipped | 2 passed, 1 skipped | pass both |

The deletion introduces **no new test failure and fixes none** — the failing set is
name-for-name identical on both sides (verified by diffing the two `FAILED` lists; the
nine names the branch run's captured tail truncated were re-run individually on the
branch and fail there too). The **only** difference across the whole suite is the
subtest count, 298 → 296: exactly the two `low`/`high` subtests of the deleted tornado
axis, which is the change being made.

**Two pre-existing reds on `main`, surfaced by this control and NOT repaired here**
(they are another lane's object, and both are disclosed rather than absorbed):

1. **The pinned default cache key is stale.** `ScenarioConfig().cache_key()` is
   `7a57fadff595ca83` at HEAD, but `tests/unit/data/test_ramp_envelope_basis.py` and
   `tests/unit/pipeline/test_forecast_xyear_warmstart_flag.py` both pin
   `603c2498bf71d21d`, and both are red on unmodified `main`. The move is consistent
   with D24-R's own repair (`0ee0542a`, comparing against the FROZEN declared default
   instead of the LIVE one) meeting owner ruling R-A's default flips (`ecf9972f`) —
   i.e. it is the *intended* consequence of D24-R, with the pins simply not re-pinned in
   that PR. **Here re-pinning is the correct remedy** (the move is disclosed and
   deliberate), unlike the case `check_cache_key_registration.py`'s docstring warns
   about. **This is not two tests: 23 of `main`'s 33 failures are this one defect** —
   every `..._key_is_unmoved` / `..._is_byte_stable` / `..._not_the_pin` /
   `..._cache_key_is_pinned` test across `tests/unit/config`, `tests/unit/data`,
   `tests/unit/model`, `tests/unit/pipeline` and `tests/regression/test_persisted_identity.py`.
   A single re-pin sweep should clear all 23; it is a one-line-per-file change and it is
   **not this lane's** (it belongs with the D24-R/R-A pair that moved the key). Four
   `tests/unit/results/test_export.py` failures, six `test_soundness.py::TestEndToEnd`
   failures and `test_constants_facade.py::test_moved_surface_is_complete` are separate
   pre-existing reds, likewise unrelated to this change and untouched.
2. **`scripts/validate_parameters.py` FAILs on `main`** — 2 parameters missing a
   citation entry, identical before and after this change.

Neither is in this lane's scope, and neither is touched.

## 5. FC-6 consequence — stated honestly

### 5.1 The re-score was not reached, and could not have been

The charter's re-score clause is conditional: *"(wire branch, if the ladder becomes
non-vacuous)"*. The adjudication went the other way, so there was no battery run and no
new committed artifact. **`neiso-t3` is not re-scored and `ff-verdicts.json` /
`forecast_verdict.json` are not touched** — FC-6 continues to read **CAVEAT** from the
D26-committed record, exactly as it did at session start. Nothing in the published
verdict changed, so nothing needed preserving.

### 5.2 What a future battery run will now emit (verified, not asserted)

Exercised end-to-end in-process, no solve:

- `run_ladder` on T1.6 returns `rungs: []` and two `SKIP` rows carrying
  `vacuous: True` and the out-of-service reason; the markdown report renders.
- `forecast_verdict.score_fc6` on that ladder returns exactly one row:
  `FC-6 / battery gate rows / **CAVEAT** — "no gate FAIL but 2 vacuous row(s)"`,
  naming `T1.6/T1.6a` and `T1.6/T1.6b`.

So the FC-6 **status is unchanged** (CAVEAT before, CAVEAT after) while the **reason
becomes true**: today's committed record says two gate rows passed on constant series;
after a re-run it will say the model was never asked the question. That is a strictly
more honest artifact and a strictly worse-looking one, which is the right direction.

### 5.3 Can FC-6 clear CAVEAT? Not until the instrument decision lands

NEISO's entire pre-registered battery contribution is this one ladder (D21 finding 3).
With T1.6 out of service, FC-6's NEISO content is P1–P3 — all three PASS since D26 — plus
two vacuous gate rows. **FC-6 is structurally CAVEAT-at-best for NEISO until either a
replacement T1.6 lever is pre-registered and run, or additional NEISO ladders are
registered.** No re-solve, at any vintage, can change that.

## 6. THE ASK — the T1.6 instrument decision (owner, plan §2)

**What is being asked:** T1.6's pre-registration stands. Its implementation does not.
Authorize a replacement lever, or authorize registering additional NEISO ladders, or
accept FC-6 as a standing CAVEAT for NEISO.

**One observation that may narrow the ask, with the evidence for it.** Plan §2's Tier-1
table names a **config field** in the "Ladder" column of every row but one:

| Row | Plan §2 "Ladder" column | Names a field? |
|---|---|:--:|
| T1.1 | `carbon_price` ∈ {0, 25, 50, 100} $/t | yes |
| T1.2 | `mass_cap_enabled` with `mass_cap_tons` … | yes |
| T1.3 | `gas_price_factor` ∈ {0.5, 1.0, 1.5} | yes |
| T1.4 | `demand_growth_path` low/mid/high | yes |
| T1.5 | Build years straddling `ira_wind_solar_last_year` | yes |
| **T1.6** | **"NEISO or CAISO forecast, VRE fleet held short vs long"** | **NO** |
| T1.7 | PJM `net_cone_per_kw_yr` × {0, 1, 2} | yes |
| T1.8 | `tech_cost_path` low/mid/high | yes |
| T1.9 | Storage fleet seeded at {5, 15, 25} GW (ERCOT) | no (a quantity) |

T1.6 alone pre-registers an **economic condition**, not an implementation.
`renewable_buildout_pace` was the 2026-07-12 session's implementation choice made *under*
that pre-registration, not the pre-registration itself. On that reading, pointing T1.6 at
a different lever that genuinely holds the VRE fleet short vs long is an instrument
repair **within** the existing pre-registration rather than an edit to it — the same
relationship T1.9's `_storage_seed_gw` probe patch already has to its own "seeded at
{5, 15, 25} GW" row. This lane did **not** act on that reading; the charter reserves the
call. But it is the difference between a one-line sign-off and a re-registration, so it
is put to the owner explicitly.

**A third clause of T1.6's pre-registration has never been implemented at all**, noted
here because it is the same sitting's business: plan §2 line 99 also requires *"nuclear
does not move the dual (once the CX-6a row half lands)"*. No rung, expectation or
scoring path for it exists in `run_driver_battery.py`. Whatever is decided about the
VRE lever, T1.6 is a two-of-three implementation of its own pre-registration.

**Recommended lever: `entry_rate_limits`** (`vre_short` = `True`, the armed default and
the golden's own posture; `vre_long` = `False`, uncapped). Why this one:

- It is **real, cited, consumed and owner-armed** (D-2) — the model's actual VRE-pace
  mechanism, so the ladder would perturb the thing rather than a proxy for it.
- It is **not confounded with the metric**. The obvious alternative, `eac_price_wind` /
  `eac_price_solar`, must be **rejected**: `policy/eac.py` prices attribute revenue as
  `max(eac, rps_shadow)`, so moving an EAC price moves the very channel
  `rps_dual_over_acp` measures. That is a broken instrument, not a lever.
- `offshore_wind_available_year` must also be **rejected** for NEISO:
  `offshore_wind_eligible_isos` defaults to `["CAISO"]`, so it is inert in NEISO —
  the same defect being retired here.
- Disclosed cost: `entry_rate_limits` also gates thermal entry and the reserve backstop,
  so the arm is broader than VRE alone. It is a real confound and should be declared in
  the pre-registration, not hidden.

**Priced:** 2 rungs × 2026–2050, legacy bins ≈ **12 minutes** (D21 measured 696.5 s for
this exact ladder shape), plus the FC-6 re-score from committed artifacts. No golden
re-solve is implied.

**PRE-REGISTERED NOW, so the result cannot be chosen after the fact** (this text is also
committed in `run_driver_battery.py` beside the ladder): in both D21 rungs the REC dual
sits pinned **at** the $50 ACP ceiling in every year (`rps_dual_over_acp = 1.0`) with
33.0 GW of VRE already built. **A correctly-wired lever may still not move the 2050
dual.** If it does not, that is a REAL finding about the RPS/ACP stack — the dual
escaping to its cap, NEISO's target unreachable at any plausible VRE build — and it is
reported as the outcome. It is **not** grounds for trying a third lever until one moves
(rules 1/11/14). The scorer will label a constant series vacuous either way.

**Second-order note for the same sitting, out of this lane's scope:**
`retirement_aggressiveness` has the identical signature — declared in `ScenarioConfig`,
tier-1 in `TIER_TAGS`, and (by the same grep that found this one) read by no model code.
It is *not* adjudicated here and no claim is made about it beyond the grep; it deserves
D21's measured treatment before anyone acts.

## 7. The mechanism-matrix anchor repair

`check_mechanism_matrix.py` reported 0 anchor warnings on `main` and 236 after my
`scenarios.py` edit — line anchors into `scenarios.py`, shifted by the ~17-line net
insertion. Repaired with the tool's own `--fix-anchors` (digits only; the field NAME is
the durable identifier), landed as its own commit so it is trivially re-runnable if a
parallel `scenarios.py` lane rebases ahead of it. No cell verdict, `fc` posture,
evidence string or keeper stamp changed, and no ISO shard was touched.

## 8. Consequence for the golden re-solve card (D26 finding §8.3)

**D26 §8.3 item 3 is confirmed and now has a name, a route, and a price — but its
ceiling stands.** Item 3 read: *"What still caps a re-solved golden's FC-6 at CAVEAT is
the vacuous T1.6 battery leg … A re-solve cannot buy FC-6 PASS until that
wiring/registration decision is taken."* That is exactly right, and this lane resolves
only its first half:

1. **The wiring question is CLOSED: it is not wirable.** The wire branch is refused on
   the merits (§2.2), so "wire it" is off the table permanently — the model already
   contains the mechanism. What remains is purely a **registration** question.
2. **The ceiling is UNCHANGED.** A re-solved golden's FC-6 still cannot exceed CAVEAT,
   for the same reason and now for a permanent one: NEISO's whole battery is one ladder,
   and it is out of service until the owner authorizes a replacement lever (§6).
3. **The card gains a cheap unblocking option it did not have.** The §6 decision is a
   ~12-minute battery plus an artifact-only re-score — it does **not** need to be
   sequenced with a campaign, and it can be taken before, during, or after one. If the
   owner authorizes it and the ladder discriminates, FC-6 becomes PASS-eligible for the
   *existing* golden without any re-solve. If the ACP pin holds, FC-6 stays CAVEAT and
   the card's ceiling logic is unchanged — but the reason is then a measured RPS/ACP
   finding rather than an instrument defect, which is a materially better thing to
   publish.
4. **Nothing else on the card moves.** No solve was run, no vintage assumption touched,
   and D26's paired-arm pricing rider (§8.3 item 4) is unaffected.

## 9. Reproduction record

```
git fetch origin main && git checkout -B <branch> origin/main   # 6eea67c7
python3 -m venv .venv-t16 && .venv-t16/bin/pip install -r requirements.txt pytest

# cache-key control (run once on main, once on the branch)
PYTHONPATH=src .venv-t16/bin/python -c "
from market_sim.config.scenarios import ScenarioConfig
print(ScenarioConfig().cache_key())
print(ScenarioConfig.from_yaml(
    'results/ff-t3-neiso-golden/bau/NEISO/a4b11ef4aaa1be35/config.yaml').cache_key())"
#   main: 7a57fadff595ca83 / 500790494e360a2a
# branch: 7a57fadff595ca83 / 500790494e360a2a

# out-of-service ladder -> FC-6 CAVEAT, no solve
PYTHONPATH=src .venv-t16/bin/python -c "
import sys; sys.path.insert(0,'scripts')
import run_driver_battery as B, forecast_verdict as V
l=[x for x in B.build_ladders() if x.test_id=='T1.6'][0]
r=B.run_ladder(l,'NEISO',2026,2050,'/tmp/x','/tmp/y',1)
print(V.score_fc6({'driver_battery':{'ladders':[r]}},'t3','NEISO'))"

PYTHONPATH=src .venv-t16/bin/python scripts/check_cache_key_registration.py
PYTHONPATH=src .venv-t16/bin/python scripts/check_mechanism_matrix.py
.venv-t16/bin/python -m pytest tests/unit tests/regression -q
```

## 10. CROSS-LANE NOTE — D26-S (found on the r#26 refresh, after this lane's commits)

The director's r#26 sitting landed on `main` mid-lane and **issued D26-S**
(`claude/capx-d26s-arm-solves`, Opus, neiso): *"execute the D26 finding's committed
runbook (two paired 25-yr arms at the pinned vintage, paired-invariants scoring,
**neiso-t3 FC-6 re-score**, fill the TBD sections); cross-lane re-grade STOP rule."* That
lane and this one are the only two writing NEISO FC-6, so the interaction is stated here
explicitly rather than left to be discovered by its STOP rule:

- **No verdict conflict.** If D26-S re-runs `run_driver_battery.py` at a HEAD carrying
  this branch, T1.6 emits two `SKIP` + `vacuous` rows instead of the old constant-series
  `PASS` rows. `score_fc6` returns **CAVEAT either way** (measured, §5.2), FC-6 stays
  **CAVEAT**, and the determination stays **HOLD**. Nothing D26-S is chartered to move
  moves differently because of this lane.
- **One thing D26-S should expect.** Its control-first step reproduces the committed FC-6
  record. The battery row's **detail string** legitimately changes — from "two gate rows
  passed on constant series" to the out-of-service reason — while its **status** does not.
  That is this lane's intended effect, not a re-grade breach; the status is the thing the
  STOP rule protects.
- **Sequencing is free.** These branches share no file (D26-S writes `fc6/` artifacts and
  `ff-verdicts.json`; this one writes `scenarios.py`, the battery registry, the tornado,
  docs and `program-status.json`'s own new block). Either can land first. If D26-S lands
  first, its committed battery output simply carries the old T1.6 rows and the next run
  after this branch replaces them with the honest ones.
- **D26's charter clause is honoured, not contradicted.** D26 was told *"do not touch the
  vacuous-ladder CAVEAT (`renewable_buildout_pace`) — that is a separate, still-true
  finding."* It did not, and this lane is that separate finding being executed. The CAVEAT
  is not removed here either; only its cause is, and its reason made true.
