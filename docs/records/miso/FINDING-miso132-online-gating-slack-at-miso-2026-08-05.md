# FINDING miso-132(a) — SYNCHRONIZED-RESERVE ONLINE-GATING is IDENTIFIED but INERT at MISO: the model's own generating fleet already carries ~9× the published online requirement in free overnight headroom

Session miso-132, 2026-08-05, branch `claude/miso-132-backcast-calibration-d8gen8`,
off `origin/main` at `b4581c49`. **NO LP SOLVED IN THIS LANE. NO ARM BUILT. NO
`ScenarioConfig` FIELD ADDED. NO MECHANISM ARMED. NO RUN REGISTERED FOR THIS LANE.
KEEPER UNCHANGED** at `2026-08-04-miso-127-onlinepmin` (NOT-YET, sole FAIL C7
`COAL_PRB` 2025 `cv_ratio` 0.347 vs the 0.50 gate, ledgered caveats 2/3 {C3a, C3c}).

**Pre-registration**
`results/calibration/PREREG-miso132-synchronized-reserve-online-gating-2026-08-05.md`,
pushed at **`9a0033bb`** BEFORE the probe ran, with the two-sided prior declared (S-2
named in advance as the live kill risk) and §0 disclosing every previously-measured
number. **Probe** `scripts/probes/_miso132_online_gating_sizing.py`; **record**
`results/calibration/_miso132_online_gating_sizing.json`. Rule 22 `[R-HOLDOUT]`: MISO
holds no marker — 2023–2025 only; the probe hard-errors on any other year, and the
2022/2026 files present in `data/raw/MISO-AS/` were **not read**.

The lane is the miso-130 stamp (b) / miso-131 §3 **successor 1** — "the only
structural, hour-organizing, price-regime-immune candidate left".

---

## 1. Verdict

**P1 KILL on the pre-registered S-2 bar, with the identification (§1 of the prereg)
fully SUCCESSFUL. Zero solves.** The charter's step-1 prerequisite is discharged and
its premise is confirmed; the mechanism dies one step later, on whether the gate can
bind.

| screen | statistic | 2023 | 2024 | 2025 | BAR | verdict |
|---|---|---:|---:|---:|---|---|
| **S-1** | published online (`reg+spin`) requirement, July night (h0–5) mean, MW | **1,316** | **1,550** | **1,519** | ≥ 800 | **PASS** |
| **S-2** | `REQ_on / ONLINE_CAP`, July night | **0.100** | **0.113** | **0.110** | ≥ 0.25 | **FAIL** |
| **S-3a** | coal share of `ONLINE_CAP`, July night 2025 | 0.387 | 0.372 | **0.245** | ≥ 0.40 (2025) | **FAIL** |
| **S-3b** | `REQ_on ×` coal share, MW, 2025 | 509 | 576 | **371** | ≥ 500 (2025) | **FAIL** |

## 2. The identification SUCCEEDED — and it is definitional, not a fitted share

The charter's binding instruction was "published requirements only … if no citable
published basis exists, STOP and file the data ask". A citable basis exists, and it is
a **product-definition boundary**, not a share:

* **MISO BPM-002 §4.2.1.1.2** (Regulation, real-time eligibility): "**synchronized**
  Generation Resources; **synchronized** DRRs-Type II; and available External
  Asynchronous Resources".
* **MISO BPM-002 §4.2.1.2.2** (Spin, real-time eligibility): "**Synchronized**
  Generation Resources; Uncommitted DRRs-Type I with a Contingency Reserve Status of
  '**online**'; **Synchronized** DRRs-Type II …".
* Supplemental is the offline-capable product — PJM's public cross-RTO survey states
  it for MISO directly: "MISO does qualification testing to provide **offline
  supplemental reserve**, but not for synchronized reserves" (*Education on Reserve
  Practices across RTOs/ISOs*, PJM Reserve Certainty Senior Task Force, 2024-01-17).

**So the online portion of MISO's Market-Wide Operating Reserve is exactly
`reg + spin`.** In the backcast its MW require **no new intake**: the keeper already
runs `miso_measured_reserve_requirements`, whose loader reads MISO's real-time
cleared-offers report at (date, hour, region, **product**) grain and today sums
`reg+spin+supp`. Restricting to the report's own `reg`/`spin` labels is a `groupby`,
never a residual. Measured: the online portion is **55.0 / 56.9 / 58.7 %** of the total
OR requirement, i.e. **1,316 / 1,550 / 1,519 MW** at July night — the charter's
"~1–1.4 GW must be SYNCHRONIZED" claim confirmed within its own stated band.

The forward generator is equally published (`MISO_REGULATING_RESERVE_MW + 0.50 × MSSC`;
BPM-002 §3.2 sets the Contingency requirement at ≥ MSSC and the Spin requirement as
"a percent of Contingency Reserve", and the PJM survey records MISO's percent as 50).
**It was used by no number here.**

## 3. Why the lane dies: the gate is SLACK, because idle capacity was never the binding provider overnight

`ONLINE_CAP(t) = Σ_pools min(ρ·P_pool, ramp10_pool, cap_pool − P_pool)` — the reserve
capability that survives the gate, at fuel grain, on the keeper's own dispatch and the
fleet assembled at HEAD under the keeper's committed config.

| July night (h0–5), MW | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| published online requirement `REQ_on` | 1,316 | 1,550 | 1,519 |
| **`ONLINE_CAP`** (gated capability) | **13,213** | **13,732** | **13,774** |
| un-gated capability (idle capacity included) | 32,493 | 30,191 | 30,045 |
| share of the un-gated pool that SURVIVES gating | 0.407 | 0.455 | 0.458 |

**Both halves of the finding are in that table.** The gate does exactly what miso-130
said it would to the *supply stack* — it deletes **~55 %** of the overnight reserve
pool, and the deleted block is precisely the idle one (`gas_ct` 17.9 → 1.6 GW,
`oil` 3.0 → 0.0 GW in 2025). **And it changes nothing**, because what remains —
13.8 GW on generating pools — is still **~9×** the 1.5 GW it has to cover. A
constraint with 9× slack has a zero dual, displaces no energy, and organises no hours.
The keeper's own solve log states the un-gated version of the same fact: the pergen
reserve pool's availability-scaled 10-minute deliverable cap averages **36.7 GW**
against a ~2.5 GW total requirement.

**The zone-pooling bias did not manufacture the kill.** Pooling zones inflates
`ONLINE_CAP`, so it was the one declared bias that could. Resolved on the published
Midwest (North+Central) / South boundary the measured series itself carries, with each
fuel's dispatch allocated pro rata to regional capacity:

| July night 2025 | requirement MW | `ONLINE_CAP` MW | tightness |
|---|---:|---:|---:|
| Midwest | 950 | 9,054 | **0.105** |
| South | 569 | 4,720 | **0.120** |

Both regions are 8–10× oversupplied. The 2023/2024 region splits are the same shape
(0.122/0.055 and 0.112/0.115). Nothing in the zonal structure rescues the lane.

## 4. Two construction facts recorded honestly

**(a) The pre-registered `ρ` construction is DEGENERATE at MISO, and was replaced with
disclosure.** PREREG §2 specified `ρ` as the capacity-weighted plant-level
`(pmax − pmin)/pmin`. Measured: **0 of 504** plants in the pergen member set have a
positive `pmin` (0.0 % of capacity) — `generators_to_fleet_arrays`' own docstring says
so ("Coal carries no Pmin floor: each coal bin is split into take-or-pay tranches …
each with `pmin_mw = 0`"), and the tranche-binned MISO fleet carries the min-load level
in `min_gen`, not `pmin`. The same physical quantity was therefore taken through the
fleet's **CEMS-measured min-stable-when-online fraction** — the identical source
`_posture_pool_params` reads (`thermal_tranche_overrides` `committed_pct`, WWSIS-2
class gap-fill): cap-weighted `mlf` **0.352** over **87.5 %** CEMS-covered capacity ⇒
`ρ = (1 − mlf)/mlf = **1.839**`, inside the same physical `[0.5, 4.0]` band the NYISO
path clips to. Still a fleet property, still measured, still zero free parameters —
but it is **not** the construction the prereg named, and saying so is the point.

**(b) S-3's 2025 legs are construction-contaminated and are NOT relied on.** The
probe's availability basis reproduces the solve's outage overlay well (thermal
reserve-eligible capacity 76.6 GW annual mean / 89.0 GW July night against 112.0 GW
nameplate) but not exactly: the keeper's coal dispatch exceeds the probe's coal
available capacity in **36.8 %** of 2025 hours (0.8 % in 2023, 5.9 % in 2024), which
zeroes coal's headroom term in those hours and **understates** coal's share of
`ONLINE_CAP`. So S-3a's 2025 miss (0.245 vs 0.40) is partly an artifact.
**This does not touch the kill**, and the direction is what makes that safe: any
correction that ADDS capability makes `ONLINE_CAP` **larger** and S-2 tightness
**smaller** — the S-2 kill can only get stronger. The verdict rests on S-2 alone.

## 5. The generalisable lesson: A MISSING MARKET RULE IS NOT AUTOMATICALLY A BINDING ONE

miso-130 identified a real, citable gap — MISO's design genuinely never sets
`online_gated`, and ~2.5–2.7 GW of a published requirement genuinely could be backed by
idle capacity. Every word of that stands. What did **not** follow is the inference that
closing the gap would move dispatch. **A constraint changes an optimum only where it
binds**, and this one is 9× slack in exactly the hours it was recruited to fix. The
check costs one fleet assembly and no LP — the same price as miso-131's grain check,
and it inverted this lane the same way.

Stated as the reusable rule: **before building a mechanism that adds or tightens a
constraint, measure the SLACK of that constraint in the target hours on the incumbent's
own dispatch.** "The real market has this rule and we don't" establishes admissibility
(rules 1/14); it does not establish reach. This joins miso-129 §2 ("a signature is not
a cause") and miso-131 §2 ("a plant-grain signature is not a class-grain defect") as
the third member of the same family.

## 6. What this closes and what it does not

* **CLOSED (verdict-grade): synchronized-reserve online-gating as a MISO C7 lever.**
  Adjudicated **`R`** on a pre-registered bar. **DO NOT re-open it at MISO without new
  evidence that the overnight ONLINE reserve capability is SCARCE** — the pre-check to
  beat is §3's table, and a per-plant or per-zone statistic is not such evidence
  (miso-131 §2's lesson applies: the binding grain is the pool the requirement is
  drawn against). Rule 25 `[R-ISO-SCOPE]`: this verdict is MISO's alone — it rests on
  MISO's fleet size and overnight headroom, and transfers to **no** other ISO. PJM's
  `pjm_reserve_online_gated` and NYISO's three online-gated arms are untouched.
* **NOT closed — the identification is banked, and it is reusable.** The published
  `reg+spin` online split (§2) is now measured, cited and reproducible. Any future MISO
  mechanism that needs the synchronized portion of the OR requirement — a commitment
  posture, a scarcity representation, a forecast-lane reserve product — should take it
  from there rather than re-deriving it, and the forward generator
  (`REG + 0.50 × MSSC`) is registered with it.
* **NOT touched:** the miso-130 §3 price-regime attribution (the 2025 July night floor
  sits above the cheap-PRB majority) stands unchanged — this lane never reached it.
  `gas_commitment_bridge` stays `U` with its empty-pool census intact.
* **NOT chartered off this finding:** nothing. Successor 2 (the CC committed-band
  re-grounding) is opened in this session under **its own** pre-registration
  (`PREREG-miso132b-cc-committed-band-regrounding-2026-08-05.md`), not licensed by
  anything measured here.

## 7. Rule duties

* **Rule 15 `[R-DASHBOARD]`** — this lane produced no run, so there is nothing to
  register (this statement). The session's registered runs belong to lane (b).
* **Rule 16** — all three training years measured together throughout.
* **Rule 19 / 24** — nothing armed, nothing stacked, no field added, no knob created.
* **Rule 21 `[R-DOF]`** — no parameter was introduced, so none is owed an
  identification; the `ρ` question is moot with the lane.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive was re-run; every measured artifact was
  read as committed.
* **Rule 25 `[R-ISO-SCOPE]`** — MISO-scoped, explicitly non-transferable (§6).
* **Rule 28(b)** — the `reserve_online_gated` MISO cell is stamped **`R`** with this
  citation in the same session, and §5.4 carries the queue stamp.
* **Contamination** — declared in the prereg §0. The adjudicating statistic
  (`ONLINE_CAP` and its tightness) had never been computed before this session.
* Next number: **miso-133**.

## 8. Reproduce

```
uv run python scripts/probes/_miso132_online_gating_sizing.py
```

No LP, no network; reads the MISO ASM cleared-offers parquets (2023–2025), the keeper
bundle's class-hourly sidecars, and assembles the dispatch fleet at HEAD under the
keeper's committed config. ~8 min.
