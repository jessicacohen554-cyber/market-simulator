# FFR-2E — Validating the SHIPPED capacity-price posture (audit FR-14)

**Session:** FFR-2E, Wave 2 of the forecast-readiness remediation program.
**Date:** 2026-08-02. **Base:** `origin/main` @ `a900c67`.
**Charter:** `docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-2E;
audit `docs/forecast-readiness-audit-2026-07.md` §3.2 FR-14; peer review
`docs/forecast-readiness-peer-review-2026-07.md` §3.1 ("validate the
configuration you ship").

**Nothing here tunes anything** (rules 1 / 14). No `ScenarioConfig` default
moved (rule 24) — the posture flips remain the owner's, executed at FFR-3A
step 0. No rubric threshold, band or scorer logic was touched.

---

## 0. Headline

The capacity-hindcast instrument now runs the posture the forecast ships, and
the posture question turns out **not** to be a second-order calibration detail:

1. **For PJM, NEISO and MISO the two arms are not a perturbation of each other
   — at the model's own reserve position the shipped curve arm pays ZERO
   capacity revenue in the 2021–2025 window where the fixed arm pays the full
   net-CONE.** The T1-H "curve-ON over-fire" FC-3 FAILs are the direct
   arithmetic consequence of removing $77–109 k/firm-MW-yr of going-forward
   revenue from the retirement screen, not a separate defect.
2. **CAISO's curve-ON posture is provably inert** — not asserted, proved: the
   registry carries no published CAISO demand curve, so the shared pricing seam
   returns the identical float in both arms at every reserve position and every
   solve year. FF-2C's "pricing no-op" verdict is confirmed at HEAD.
3. **NYISO's shipped posture IS the fixed arm** (production ships it curve-OFF),
   so `nyiso-2021-2025-{curve,fixed}` are a force-ON probe pair, not a
   shipped-vs-fixed pair. The `--golden-posture` used by the full-horizon runner
   disagrees with the shipped default on exactly this ISO.
4. **PJM's new FFR-2C floor reaches the screens and reverses the sign of the
   posture gap from 2028**: at a long position the curve arm goes from paying
   $0 (2021–2027 vintages) to paying $63,875/firm-MW-yr (2028/29 vintage),
   i.e. from 100 % below the fixed arm to 17.5 % below it. **This is measured at
   the pricing seam only — its fleet-level effect remains UNMEASURED (§4).**

> **⚠ COMPLETION STATE.** Charter items 1 (instrument), 3 (arm recommendation)
> and the rule-28 matrix duty are DONE. Item 2 (re-run the T1-H legs) and item 4
> (the PJM T0 leg) are **NOT DONE — no LP was solved and no run was registered**;
> the container had no `data/clean/` tree and rebuilding it did not finish in
> session. §3.1 and §4 carry the exact commands. Every quantitative claim below
> is either exact seam arithmetic (§2) or committed pre-epoch evidence explicitly
> labelled as prior (§3.0) — none of it is a fresh solve.

---

## 1. What was wrong (FR-14) and what changed

`scripts/run_capacity_hindcast.py` passed
`capacity_market_clearing_by_iso={iso: True} if --capacity-market-clearing else None`.
The default arm was therefore `None` — the flat net-CONE stub — while the
production `ScenarioConfig` ships
`{"PJM": True, "MISO": True, "CAISO": True, "NEISO": True}`. Every FC-3 verdict
produced without the flag scored a price formation the forecast never runs.

**The change** (commit 1, `scripts/run_capacity_hindcast.py`):

| posture | how selected | `capacity_market_clearing_by_iso` |
|---|---|---|
| **shipped** (new default) | no flag | the live `ScenarioConfig` default, read off the dataclass field |
| **fixed net-CONE** | `--fixed-net-cone` | `None` — byte-identical to the pre-FFR-2E default |
| **forced curve** (RC-1B probe) | `--capacity-market-clearing` | `{iso: True}` — for an ISO production ships OFF |

The two flags are mutually exclusive and refuse *before* the solve. The
shipped posture is **read from the dataclass field, never mirrored**, so an
owner flip at FFR-3A step 0 is followed with no edit here — a hardcoded copy
would be a second, silently-diverging tuning channel (rule 24).

**One correctness fix rides with it.** `meta["capacity_market_clearing"]` now
records the **resolved per-ISO gate** instead of the raw flag.
`scripts/forecast_verdict.py::_curve_on` reads that key to classify a leg
curve-ON/curve-OFF; with a flag-sourced value every shipped-posture leg would
have been classified curve-OFF by the rubric — FR-14 in another costume. This
is backward-compatible on **every** committed sidecar: before FFR-2E the
resolved gate always equalled the flag (default `None` ⇒ `False`). A new
`capacity_clearing_posture` key (`shipped` / `fixed_net_cone` / `forced_curve`)
is the FC-3 evidence-row discriminator.

**Old evidence is untouched.** No committed sidecar is rewritten and no
committed verdict is re-interpreted; the `--fixed-net-cone` arm reproduces the
posture those legs ran, so each stands as scored. New runs are new rows.

Contract tests: `tests/scoring/test_capacity_clearing_posture.py` (14 tests,
LP-free) — default provenance, the three postures and their refusal, the
resolved gate per ISO, `__post_init__` non-coercion on a hindcast leg, and the
two price-identity results below.

---

## 2. The input-side measurement (LP-free, exact)

All three capacity screens price adequacy through one seam
(`MarketDesign.capacity_price_per_firm_mw_yr`, rule 19), so a price identity at
that seam **is** a screen identity. `scripts/probes/_ffr2e_posture_price_sweep.py`
sweeps it under both arms across the reserve-position domain and 2021–2028.
Published registry parameters only (rule 13).

$/firm-MW-yr, **shipped vs fixed**, at four reserve positions:

| ISO | year (DY) | 0.95 | 1.00 | 1.045 | 1.10 |
|---|---|---|---|---|---|
| **CAISO** | any | 88,080 vs 88,080 | 88,080 vs 88,080 | 88,080 vs 88,080 | 88,080 vs 88,080 |
| **NYISO** | any | 110,000 vs 110,000 | 110,000 vs 110,000 | 110,000 vs 110,000 | 110,000 vs 110,000 |
| **ERCOT** | any | 0 vs 0 | 0 vs 0 | 0 vs 0 | 0 vs 0 |
| **PJM** | 2023 (2023/24) | 150,541 vs 77,431 | 121,404 vs 77,431 | 30,868 vs 77,431 | **0 vs 77,431** |
| **PJM** | 2025 (2025/26) | 164,838 vs 77,431 | 123,200 vs 77,431 | 27,112 vs 77,431 | **0 vs 77,431** |
| **PJM** | 2027 (2027/28) | 121,706 vs 77,431 | 108,431 vs 77,431 | 0 vs 77,431 | **0 vs 77,431** |
| **PJM** | **2028 (2028/29)** | 118,625 vs 77,431 | 118,625 vs 77,431 | **63,875 vs 77,431** | **63,875 vs 77,431** |
| **NEISO** | 2023 (2023-24) | 157,188 vs 108,940 | 98,244 vs 108,940 | 44,979 vs 108,940 | **0 vs 108,940** |
| **NEISO** | 2025 (2025-26) | 148,800 vs 108,940 | 89,616 vs 108,940 | 41,029 vs 108,940 | **0 vs 108,940** |
| **MISO** | 2023 (2023-24) | 103,040 vs 79,800 | 103,040 vs 79,800 | 0 vs 79,800 | **0 vs 79,800** |
| **MISO** | 2025 (2025-26) | **509,446** vs 79,800 | 79,800 vs 79,800 | 7,980 vs 79,800 | **0 vs 79,800** |

Three structural readings:

* **CAISO is inert by construction, not by coincidence.** `MARKET_DESIGN["CAISO"]`
  carries `demand_curve=()` and `seasonal_rbdc=None` (its RA construction is
  bilateral, not an auction), so the curve branch's own guard is false and the
  seam falls through to the flat anchor **in both arms**. The clearing gate
  resolves `True` for CAISO and changes nothing. This is a proof, not a sample.
* **NYISO is absent from the shipped mapping**, so its gate resolves off the
  scalar (`False`). Its shipped posture *is* the fixed arm.
* **MISO's seasonal RBDC makes it the most posture-sensitive ISO on the short
  side** — the four-season RBDC sum reaches 6.4× net-CONE, so at position 0.95
  the shipped arm pays 6.4× the fixed arm. On the long side it pays zero. MISO's
  posture gap is a factor of ~6 in one direction and −100 % in the other.

### 2.1 Why this matters more than a price table

FFR-2C records the model's own PJM hindcast positions at **1.100–1.196**
(`validate_capacity_prices` Pass 2). Those positions sit in the flat-extrapolated
tail. So for the 2021–2025 window the shipped PJM posture pays **exactly zero**
capacity revenue into the step-3 economic-retirement screen, where the fixed arm
pays $77,431 × (1 − EFORd) per firm MW. The same holds for NEISO and MISO
wherever their positions clear their zero-crosses (1.083 / 1.05).

That is the arithmetic behind the T1-H "curve-ON over-fire" FC-3 FAILs recorded
in `ff-t1-gate-2026-07.md` §4.1 — **the curve arm is not a mild re-pricing, it
removes the entire RA revenue stream at a long position.** It is also why the
*fixed* arm is the unrepresentative one: it pays full net-CONE to a fleet the
market itself would pay nothing for.

---

## 3. The fleet-level measurement (paired T1-H legs)

### 3.0 What the ALREADY-COMMITTED evidence says (prior, not this session's)

Before any new solve, the committed sidecars already contain both arms for all
four curve-capable ISOs. Total thermal retirements 2021–2025, GW:

| ISO | curve arm (run) | model GW | err | fixed arm (run) | model GW | err | actual GW |
|---|---|--:|--:|---|--:|--:|--:|
| **PJM** | `pjm-2021-2025-curve-ff2c` | 18.157 | **+63 %** | `pjm-2021-2025-realized` | 4.106 | **−63 %** | 11.121 |
| **MISO** | `miso-2021-2025-curve-ff2c` | 10.814 | **−29 %** | `miso-2021-2025-realized` | 0.784 | **−95 %** | 15.227 |
| **NEISO** | `neiso-2021-2025-curve` | 9.325 | **+880 %** | `neiso-2021-2025-fixed` | 0.002 | **−99.8 %** | 0.951 |
| **NYISO**\* | `nyiso-2021-2025-curve` | 3.318 | +123 % | `nyiso-2021-2025-fixed` | 1.036 | −30 % | 1.488 |

\* NYISO's "curve" leg is a **force-ON probe**, not its shipped posture (§2).

**The posture is the single largest lever on the T1-H retirement result — larger
than the retirement rule itself.** NEISO moves 0.002 → 9.325 GW (a factor of
~4,600) on nothing but the capacity-price posture. Every one of the eight legs
FAILs its retirement band, but the two arms fail in **opposite directions**: the
shipped arm over-retires (it pays $0 at a long position, so the screen sees no
RA revenue at all), the fixed arm under-retires to ~nothing (it pays full
net-CONE to every MW regardless of how long the fleet is). That is the §2
arithmetic reproduced at fleet level.

**These legs are all PRE-cache-epoch** (2026-07-18 → 2026-07-20), so under the
Wave-1 epoch they are invalid as current evidence and are cited here as *prior*
only. FFR-2B's post-epoch cold re-solve of the same curve-ON posture shows how
much that matters: PJM 18.157 → **29.373 GW** (`pjm-2021-2025-cmc-legacy-ffr2b`,
2026-08-02) and MISO 10.814 → **15.202 GW** (vs actual 15.227, −0.2 %) with no
posture or rule change at all.

### 3.1 This session's post-epoch paired legs

The container was cloned fresh, so `data/clean/` — the derived, gitignored
curation layer every solve reads — had to be rebuilt from `data/raw/` first
(`scripts/regenerate_clean.py`, 50 datatypes). The cache-epoch purge was verified
a **no-op** on this checkout beforehand: zero `year_*.parquet` anywhere under
`results/`, every committed parquet being a backcast keeper hourly, which the
epoch does not invalidate. So every leg below is a **cold post-epoch solve**.

#### NEISO — `neiso-2021-2025-shipped-ffr2e` / `neiso-2021-2025-fixed-ffr2e`

Cache keys `da53a89d26323710` (shipped) / `aaf627fc634d0012` (fixed); solved
[2021, 2023, 2024, 2025], 2022 bridged; zero leakage-guard violations.

**Economic retirements, MW, by year** (`_ffr2e_arm_diff.py`):

| year | shipped | fixed | Δ |
|--:|--:|--:|--:|
| 2023 | 3,833.1 | **0.0** | +3,833.1 |
| 2024 | 6,630.5 | **0.0** | +6,630.5 |
| 2025 | 0.0 | 0.0 | 0 |
| **total** | **10,464.6** | **0.0** | **+10,464.6** |

The pre-epoch split (9.325 vs 0.002 GW) **survives the epoch and widens**:
10.465 vs 0.000 GW. The fixed arm economically retires **nothing at all** across
the whole window.

It is not only retirements — the whole fleet path forks. By 2025 the shipped arm
has taken gas_ct, gas_st and coal to **zero** and cut gas_cc 17,485 → 10,646 MW,
reserve margin 0.538 → 0.025 in 2024, and then *compensates* with entry the fixed
arm never builds: +1,500 MW economic thermal and +720 MW storage in 2025.

**FC-3 scores — the arms fail in instructive, opposite ways:**

| metric | shipped (curve) | fixed net-CONE | actual |
|---|--:|--:|--:|
| retire total GW | 10.465 (+10.0×) **FAIL** | 0.002 (−99.8 %) **FAIL** | 0.951 |
| `unit_recall_gt300` | 1.00 **PASS** | 0.00 **FAIL** | — |
| `false_retire` | 9.573 GW (91.5 % of model) **FAIL** | 0.0 **PASS** | — |
| additions GW | 14.72 | 15.00 | 2.981 |
| `add.by_tech` FAIL | wind, solar, gas_ct | wind, solar, gas_ct, **storage** | — |

**Read the fixed arm's two PASSes carefully — both are vacuous.** It "passes"
`false_retire` only because a model that retires nothing cannot false-retire, and
it pays for that by **failing recall outright (0.00)**: it misses the one real
>300 MW retirement entirely. The shipped arm finds it (recall 1.00) and over-fires
around it. The shipped arm additionally **passes storage additions where the fixed
arm fails** — the curve is what gives storage an RA value to enter on, exactly the
mechanism FF-2C credited for MISO's first storage entry.

So on NEISO the shipped posture is not merely the one production runs; it is the
only arm that detects the real event at all. **Both still FAIL overall — no
determination flips.**

#### CAISO — `caiso-2021-2025-shipped-ffr2e` / `caiso-2021-2025-fixed-ffr2e`

**The §2 inertness proof is confirmed at fleet level.** Cache keys
`831634d4252ceed0` (shipped) / `42927055c50f4df0` (fixed) — genuinely different
configs, two independent cold solves — and `_ffr2e_arm_diff.py` reports:

```
(no metric differs — the two arms produced the same fleet path)
ARMS DIVERGE: False
```

Identical across **every** metric in **every** solve year: retirements by reason,
additions by channel (thermal/renewable/storage, incl. the thermal source split),
reserve margin, peak demand, firm-clean MW, storage/wind/solar capacity, and the
end-of-year fleet by fuel. This is the empirical confirmation of the analytic
claim — CAISO's clearing gate resolves **on**, computes a reserve position, feeds
it to the seam, and the seam returns the same flat $88,080/firm-MW-yr either way,
so nothing downstream can move.

It also validates the proof *method* used throughout §2: seam identity ⇒ screen
identity ⇒ fleet identity. That chain is what lets the rest of this document
reason from exact seam arithmetic rather than from solves.

Neither leg carries an FC-3 score — `capacity_actuals_caiso.csv` does not exist
(blocker B4), so `score_capacity_hindcast.py` refuses both arms. They are
registered as unscored evidence rows; **no CAISO FC-3 verdict is claimed.**

#### PJM / MISO T1-H — **NOT RUN** (window coordination)

Deferred under the rule-12 split: FFR-2A owns the PJM and MISO windows first, and
at session end it had **not** yet registered its heavy legs (checked repeatedly
against `origin/main`'s `frontend/data/hindcast/`). Rather than co-run, these are
left for a successor. Note that FFR-2B's `{pjm,miso}-2021-2025-cmc-legacy-ffr2b`
(2026-08-02) are already **post-epoch curve-ON legs whose `{iso: True}` posture
resolves identically to the shipped default for those ISOs** — so a successor
needs only the *fixed* arm for each, provided it verifies no solve-affecting
change landed in between (otherwise run both, one tree, as was done for NEISO).

The commands are:

```bash
python scripts/run_capacity_hindcast.py --iso <ISO> --fuel-variant realized \
    --vintage 2020 --start-year 2021 --end-year 2025 [--fixed-net-cone] \
    --out-dir results/hindcast/<iso>-2021-2025-{shipped,fixed}-ffr2e
```

then `score_capacity_hindcast.py --bundle …` → `forecast_verdict.py --tier t1h`
→ `register_forecast_run.py --bundle …`, plus `_ffr2e_arm_diff.py`. PJM and MISO
pairs run **sequentially** (~8.6 GB/leg) and never co-run with each other.
**`--fixed-net-cone` did not exist before this session**, so the fixed arm was
previously unreachable except by predating the flip.

---

## 4. PJM's 2028/29 floor — measured at the SEAM, **UNMEASURED at fleet level**

This is the one deliverable the session did not produce, stated plainly rather
than inferred.

**What IS measured** (§2, exact, no LP): the floor reaches the screens. All three
capacity screens thread `year` into `capacity_price_per_firm_mw_yr`
(`retirements.py:707`, `new_entry.py:1012`, `storage.py:1092`), so
`resolve_demand_curve_vintage` selects the 2028/29 vintage for any solve year
≥ 2028 and holds it forward. At a long position the shipped arm pays
**$63,875/firm-MW-yr** in 2028 where it paid **$0** under the held 2027/28
vintage — the posture gap flips from −100 % of the fixed arm to −17.5 %. That
confirms and quantifies FFR-2C §2.1 independently.

**What is NOT measured:** what that does to PJM's build/retire path. The named
acceptance step — a PJM T0 leg over 2026–2028, which is the only window that
reaches the new vintage (the T1-H window ends at 2025 by construction) — was
**not run**, for the §3.1 reason. It is verified schedulable (3 solve-years, under
the §2.1b cap, no `--full-solve-authorized` needed) and the arms are verified to
resolve correctly:

```bash
# shipped/curve arm — --golden-posture resolves IDENTICALLY to the shipped
# default for PJM (both True); they differ only on NYISO, see B2
python scripts/run_full_horizon.py --iso PJM --start-year 2026 --end-year 2028 \
    --golden-posture --out-dir results/ffr2e/pjm-t0-shipped
# fixed net-CONE arm — the runner's own default pins by_iso=None (see B1)
python scripts/run_full_horizon.py --iso PJM --start-year 2026 --end-year 2028 \
    --out-dir results/ffr2e/pjm-t0-fixed
```

Run them **sequentially** (rule 12). Until then, FFR-2C's statement stands
verbatim: *the fleet-level consequence of the floor is UNMEASURED*. Nothing in
this document should be read as having closed it.

---

## 5. Per-ISO recommendation — which arm the T1 gate should cite

**Recommendation only.** The rubric-text change, if any, is FFR-3A/3B's; nothing
in `scripts/forecast_verdict.py` or the rubric was touched here.

The principle is the peer-review row itself: a forecast-readiness gate must cite
the arm the forecast **ships**. That resolves per ISO from
`ScenarioConfig.capacity_market_clearing_by_iso`, not from which leg happens to
exist.

| ISO | shipped posture | arm the T1 gate should cite | currently cited (`ff-t1-gate` §4.1) | action |
|---|---|---|---|---|
| **PJM** | curve-ON | **curve** | `pjm-2021-2025-curve-ff2c` (curve) | ✔ correct arm — **re-point to a post-epoch leg** (§3.1) |
| **MISO** | curve-ON | **curve** | `miso-2021-2025-curve-ff2c` (curve) | ✔ correct arm — **re-point to a post-epoch leg** (§3.1) |
| **NEISO** | curve-ON | **curve** | `neiso-2021-2025-curve` (curve) | ✔ correct arm — **re-point to a post-epoch leg** (§3.1) |
| **NYISO** | **curve-OFF** | **fixed** | `nyiso-2021-2025-curve` (**force-ON probe**) | ✘ **WRONG ARM — change the citation** |
| **CAISO** | curve-ON, provably inert | either (the distinction is void) | not scored — no curve leg | ✔ correct as written; add the §2 proof as the reason |
| **ERCOT** | n/a (energy-only) | n/a | n/a | ✔ |

**The one substantive correction is NYISO.** `ff-t1-gate-2026-07.md` §4.1 lists
`nyiso-2021-2025-curve` as NYISO's FC-3 evidence, but production ships NYISO
**curve-OFF** (it is deliberately absent from the clearing mapping — "excluded
pending re-calibration"). That leg is a `--capacity-market-clearing` force-ON
probe, so NYISO's FC-3 verdict currently describes a configuration the forecast
does not run — the exact FR-14 failure, one level up in the evidence chain. Its
shipped-posture twin `nyiso-2021-2025-fixed` exists and is already committed
(retire 1.036 GW, −30 % vs +123 % on the probe arm; **both still FAIL**, so no
determination flips — only the number and the claim it supports change).

**The second correction is uniform: every FC-3 citation in §4.1 is a
pre-cache-epoch leg** (2026-07-18 → 2026-07-20) and the epoch invalidates all of
them. §3.1's post-epoch legs are the replacements. FFR-2B's cold re-solve
already showed the magnitude at stake (PJM 18.157 → 29.373 GW on no posture or
rule change), so this is not a bookkeeping refresh.

**No FC-3 determination changes.** Every leg in every arm FAILs its retirement
band; the recommendation changes *which measurement the FAIL is attributed to*,
not the HOLD. The T1 board's per-ISO determinations are unaffected.

---

## 6. Open blockers (not fixed here)

**B1 — `scripts/run_full_horizon.py` carries the same FR-14 shape, and it is
the T0 / T1-F runner.** `reference_config()` (`:153`) pins
`cmc_by_iso = None` unless `--golden-posture` is passed, so a T0 or T1-F leg
launched with no flag prices adequacy on the flat stub while production clears
the curve. Its own docstring calls that the deliberate "P-2A probe posture", so
this is a **default-posture decision, not an oversight** — it belongs with the
D-1/D-3 batch at FFR-3A step 0, not to this session (rule 24). Flagged, not
fixed. *(This does not affect the §4 measurement: `--golden-posture` and the
shipped default agree on PJM.)*

**B2 — `GOLDEN_CMC_BY_ISO` and the shipped `ScenarioConfig` default disagree on
NYISO.** Golden = `{PJM, MISO, NYISO, NEISO, CAISO}`; shipped =
`{PJM, MISO, CAISO, NEISO}`. Two "the posture we ship" answers exist in the
tree simultaneously, and which one a run took depends on which runner launched
it. The mechanism-matrix note already records the NYISO discrepancy; what is
new here is that it makes "the shipped posture" ambiguous as a *harness
default*. The hindcast harness now follows `ScenarioConfig` (the config the
forecast object actually carries); reconciling the two encodings is FFR-3A/3B's.

**B3 — the capacity price cannot reach PJM/NEISO/MISO's retirement screen in
the T1-H window at all.** At the model's own reserve positions (PJM ~1.10–1.36
depending on basis; FF-2C §2.2, FFR-2C §2.1) every ISO with a published curve
sits past its zero-cross, so the shipped arm pays exactly $0. That is not a
posture defect — it is the **position/requirement basis** (BLK-3 R2/R3), and it
means the shipped posture's *quantitative* retirement effect stays gated on that
lane. Recorded as an open blocker, not closed by any parameter (rules 1 / 14).

**B5 — FR-14 is not only about the capacity curve: the hindcast harness still
pins TWO more mechanisms OFF that production ships ON.** Comparing
`build_config("PJM", 2021, 2025, …)` field-by-field against
`ScenarioConfig(iso="PJM", mode="forecast")` at HEAD, after this session's fix:

| field | production default | hindcast harness | status |
|---|---|---|---|
| `capacity_market_clearing_by_iso` | `{PJM,MISO,CAISO,NEISO: True}` | same | **FIXED here** |
| `correlated_forced_outage` | `True` | `False` | **still pinned off** |
| `entry_lookahead_reprice` | `True` | `False` | **still pinned off** |
| `datacenter_load_path` | `"mid"` | `"off"` | legitimate — `__post_init__` coerces it for any hindcast (`scenarios.py:9445`), and a 2021–2025 window has no forward datacenter path to take |
| `scarcity_pricing_enabled` | `False` | `True` | deliberate and documented — the harness adopts each ISO's *production scarcity footing* via `ISOConfig.default_scenario_overrides` (`build_config` docstring, the s2 root cause); this moves the harness **toward** production, not away |

`correlated_forced_outage` and `entry_lookahead_reprice` are **not** coerced —
`build_config` passes its own `False` defaults over the production `True`. That
is the FR-14 pattern on two more fields and it is **not fixed here**, for three
reasons: it changes what every T1-H leg means (the brief forbids silently
re-interpreting committed verdicts), it would confound this session's posture
A/B, and it is a harness-default decision of the same class as B1 — the owner
batch's, at FFR-3A step 0. Routed there.

Two consequences worth stating plainly: **(a)** FFR-2B's D-1 retirement-rule
evidence (`{pjm,miso}-2021-2025-cmc-{legacy,pipeline}-ffr2b`, 2026-08-02) also
ran with both pinned off, so it carries the same caveat; **(b)** this session's
arms are **unconfounded**, because both pin the two fields identically — the
only difference between a shipped leg and its fixed twin is the capacity-price
posture.

**B4 — CAISO cannot be FC-3 scored at all.** There is no
`data/raw/_validation-source/capacity_actuals_caiso.csv`, so no CAISO T1-H leg
can produce an FC-3 verdict in either arm. Since CAISO's posture divergence is
provably zero (§2), this costs nothing today — but any future CAISO capacity
evidence needs the actuals built first.

---

## 7. Standing disclosures (peer review §4)

> This forecast is produced by a chronological full-8760 LP dispatch model with a
> one-pass annual capacity-evolution loop. It does not include: MIP unit
> commitment; intertemporal capacity optimization or within-year entry/exit
> convergence; inter-hour ramp constraints; intra-ISO hurdle rates;
> demand-responsive fuel pricing. Unless produced by the weather ensemble,
> results are conditional on a single pinned weather year (stated in the run
> config). Uncertainty bands are dispatch-conditional: the fleet-path
> (capacity-expansion) component of structural error is unmeasured and excluded.
> Deterministic scenario cases are a range, not a probability distribution.
