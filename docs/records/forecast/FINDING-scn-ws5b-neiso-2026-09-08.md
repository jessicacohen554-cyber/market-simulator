# FINDING — SCN-WS5B-NEISO, Stage-B full-horizon scenario campaign (NEISO, 2026–2050)

**Lane:** SCN-WS5B-NEISO · **ISO:** NEISO · **Campaign:** `scn-campaign-stageb-2026-09-07`
**HEAD:** `b849a51b` · **Authorization:** owner ruling **S18** (2026-09-07, card D-5), amended by **S21** (2026-09-08)
**Pre-registration:** `PRECOMMIT-scn-ws5b-neiso-2026-09-07.md` + `…-ADDENDUM-1.md`, both pushed **before the first solve**.

Every number here is scored against a prediction that was on `main` before the LP that produced it ran.
Where a prediction was wrong, it is marked wrong and the measurement stands.

---

## 0. Headline

**A federal carbon price is not an active instrument on NEISO, and an 80 %-glide mass cap that
*replaces* the state price is far worse than the price it replaces — it permits 2.6× the cumulative
emissions and then sheds up to 13 % of load.** The CES premium, whose NEISO elasticity Stage A could
not identify, **is real and was masked by the 3 GW/yr retrofit cap**; the cap releases in 2031 and
the premium then sustains +2.0–3.5 GW of CCS above reference for two decades. And the Stage-C memo's
flagship zero — **a $50 CES target ACP buying +0.0 MW of CCS retrofit** — **was a code seam, not a
level**: capx D87 closed it, and the same leg at HEAD buys **+858.3 MW at 2030 and +6,047.8 MW by
2050**.

| leg | key | wall | cum CO₂ 2026–50 | CO₂ 2050 | `gas_cc_ccs` 2050 | price 2050 |
|---|---|---|---|---|---|---|
| REF | `1b452c457ca786a6` | 15.2 min | **122.81 Mt** | 5.5319 | 4,271.4 | 74.68 |
| CARB-HI | `0e65d419ef104c54` | 16.0 min | 122.14 | 5.5319 | 4,271.4 | 74.68 |
| CES-P60 | `bd7de61415f5d950` | 21.7 min | **92.91** | 1.7236 | 7,788.7 | 8.63 |
| ALL-CLEAN | `1c5c40a4fd011b6b` | 301.0 min | 117.23 | 4.3238 | **14,286.2** | 34.77 |
| CAP-STATE-TIGHT | `9bceb08bc291fced` | 237.2 min | **313.72** | 4.1000 | **0.0** | **1,601.18** |
| CES-T80 | `e4286b070d08cdcb` | 336.2 min | **95.84** | 2.4065 | 10,319.2 | 33.82 |

Every key matches the value pre-declared in ADDENDUM 1 §5 before the solve.

---

## 1. Scope delivered — six legs, one killed at zero LP and replaced under S21

S18 granted **REF · CAP-STATE-TIGHT · CES-P60 · CES-T80 · CARB-MID · ALL-CLEAN**. The parent
PRECOMMIT §5 killed **CARB-MID** at phase 0 on a proven LP-input identity and routed the
substitution rather than taking it; **S21 substituted CARB-HI**, and the liveness condition it
attached was met by this lane's own committed §5. **Six legs, not seven; no rider was added.**

**The CARB-MID kill is a campaign result, not an omission:** *the RFF mid carbon path is entirely
masked by RGGI on NEISO in 25 of 25 years.* It cost zero LP to establish and ~30 min of LP to avoid.

---

## 2. THE G-DRIFT REFRESH — the charter's STOP fired, and it was right to

The charter said *"STOP on any cache-key mismatch against your §4 table and change nothing."*
**It fired.** All five previously-derived keys had moved between the parent PRECOMMIT's HEAD
(`a667073f`) and this session's (`b849a51b`, 170 commits later). The lane stopped, diagnosed at zero
LP, changed nothing, and recorded the result in ADDENDUM 1 §2 before solving.

**The cause is exactly one field.** `pjm_seam_neighbour_hourly_ladder` landed as a new
`ScenarioConfig` field **without cache-key registration**, so it enters the hash of every config of
every ISO. Dropping it — and nothing else — restores all six keys byte-for-byte, and restores a
default `ScenarioConfig` to the program's own unchanged `PINNED_DEFAULT_CACHE_KEY`
(`547053bdfccd4264`). **This is program-wide, not a NEISO or Stage-B effect. Routed to SCN-DESK
(§8.1); `src/` and `tests/` are outside this lane's regions and were not touched.**

The D79 solve surface is **cleared as a cause**: NEISO's fingerprint moved (195 → 197 rows, two
newly declared SPP-49 names) but `moved_rows("NEISO") == {}`, so it enters no key.

### 2.1 Three hunks were LIVE, and the parent's "no hunk is LIVE" verdict was superseded before solving

| repair | scope | measured NEISO footprint |
|---|---|---|
| **SPP-49** `_apply_simple_cycle_hr_floor` — unconditional fleet construction | every leg | **one plant** (64378, `IC`), clamped 8.500 → 9.000 MMBtu/MWh, of a 431-unit / **24,209.6 MW** fleet |
| **capx D87** — CCS retrofit reads `clean_attribute_price_by_fuel` (**the D-15/S19 seam the Stage-C memo sent this lane to report — REPAIRED at HEAD**) | target-row legs only | **ALL-CLEAN: +48.1 / +92.3 / +194.1 MW** of `gas_cc_ccs` in 2028/29/30 |
| **capx D88** — retrofit representative `unit_id` re-mint | any leg that converts a legacy `gas_cc` | no separable footprint at reported precision |

---

## 3. GATE I — scored, and the repairs' footprint is *smaller* than this lane predicted

ADDENDUM 1 §3 **withdrew** the parent's strict-identity prediction on the code audit, before any LP,
and re-purposed GATE I as a **repair-footprint measurement** whose falsifiable content is: *every
2026–2030 deviation is attributable to SPP-49, D87 or D88.*

| leg | worst rel. dev. 2026–2030 (6 metrics) | verdict |
|---|---|---|
| **CAP-STATE-TIGHT** | **0.00e+00 on all six** | **PASS — exact byte-identity** |
| **CES-P60** | **0.00e+00 on all six** | **PASS — exact byte-identity** |
| REF | `co2` 1.20e-04 … 7.14e-04 against the **2-dp-rounded sidecar**; **0.00e+00** against the parent §6.1 frozen 4-dp table | **PASS** (see below) |
| **ALL-CLEAN** | `co2_mt` **9.63e-02**, `lw_price` 1.97e-02 | **FAIL — as predicted, and attributed** |
| CARB-HI | no Stage-A twin; byte-identical to this campaign's REF in 2026–2032 | identity chain closed |

**REF's apparent miss is an artefact of comparator precision, not physics.** Stage-A NEISO has no
REF *bundle* on disk — its comparator is the sidecar `meta.year_summary`, which stores **two
decimals** (`15.83`, `2758.3`, `51.89`). Stage-B's full-precision values round to those exactly
(`15.8319`, `2758.32417`, `51.892`), and against the parent PRECOMMIT §6.1's frozen 4-dp table the
deviation is **0.00e+00 in all five years**. *Method note for later lanes: a sidecar `year_summary`
cannot score a 1e-6 identity gate; only the full-precision `full_horizon_summary.json` can.*

### 3.1 ALL-CLEAN's failure is the cleanest attribution in the campaign

Against the committed Stage-A (pre-D87) bundle:

| year | Δ `gas_cc_ccs` | Δ `co2_mt` |
|---|---|---|
| 2026 | **+0.0 MW** | **+0.0000 Mt** |
| 2027 | **+0.0 MW** | **+0.0000 Mt** |
| 2028 | +48.1 MW | +0.0133 Mt |
| 2029 | +92.3 MW | +0.5041 Mt |
| 2030 | +194.1 MW | −0.0180 Mt |

**Exactly zero in the two years before `ccs_retrofit_available_year = 2028`, non-zero in exactly the
three the retrofit screen executes.** A mechanism that does not execute cannot move a year it does
not execute in, so the deviation is D87's and nothing else's. **GATE I's falsifiable content holds.**

**This lane's own prediction was too pessimistic and is marked so.** ADDENDUM 1 admitted deviation
`> 1e-6` for REF, CAP-STATE-TIGHT, CARB-HI and CES-P60 on SPP-49 + D88. Measured, **two of those are
exactly zero on all six metrics** and the other two show none. The code audit correctly found the
repairs *can* move results; the measurement shows that on NEISO, in this window, **they do not** —
D87 on a target row is the only one that bites. The prediction that *was* exactly right is the one
that mattered: **D87 must be a no-op on CES-P60 (a premium leg mints no clean-tier vector) — measured
0.00e+00.** The two CES legs bracket the repair's footprint from both sides.

---

## 4. GATE II — the crossing year is **2049**, exactly the pre-registered point estimate

The parent §6.2 fixed the definition before the solve: *the first year `y` in which
`cap(y) < REF_CO2(y)`*, point estimate **2049**, band 2048–2050, "no crossing" admitted.

**Measured: 2049** (cap 4.830 Mt < REF 5.2000 Mt; 2048 is 5.560 vs 3.6561, not crossed).

But the pre-registered metric is the *less* important half of what CAP-STATE-TIGHT returned.

### 4.1 The price-vs-quantity answer S17 sent this leg to get

**GATE III's binding limbs are read directly from the committed summary** — SCN-FIX3 now records
`co2_cap_price` per year, so this lane did not have to score them by identity, and both halves hold
exactly: the cap **binds in 23 of 25 years** with emissions equal to the budget, and is slack in
**exactly two** (2032: 16.3734 vs 16.680; 2033: 15.8264 vs 16.020) where **`co2_cap_price` is `0.0`
exactly**.

The dual's path is the finding: **12.23 → 2.75 (2031) → 38.00 (2040) → 95.87 (2041) → 5,337.55
(2042)**, holding near 5,400 to 2050, with the load-weighted price stepping **$78 → $1,688** in the
same year. From 2042 the cap is met only by **shedding load** — I3 records unserved energy at 1.88 %
(1,199 h) in 2042 rising monotonically to **13.29 % by 2049**.

**The mechanism is in the fleet, and it is a policy-design result, not a solver artefact.**
CAP-STATE-TIGHT builds **863.2 MW** of `gas_cc_ccs` in 2029–2030 and **zero in every other year**,
against REF's 7,691.3 MW at 2030. Because the case **replaces** the RGGI adder with the mass row
(`carbon_price_path: zero`), there is no marginal carbon signal to make a retrofit economic, so the
fleet that arrives at the tightening years has nothing to comply with.

> **Over 2026–2050 the mass cap permits 313.72 Mt against the price case's 122.81 Mt — 2.6× — and
> then collapses into load-shedding, while REF, driven by the RGGI price alone, emits 2.8–3.6 Mt
> through the 2030s and 40s, three to five times *below* the same budget, and never sheds a MWh.**

Stage A saw the first five years of this and called it a *loosening*. The 25-year horizon shows the
loosening is not the end state: it is what **builds the fleet that cannot comply later**. Ruling
S12's 80 % slope and `mass_cap_tons_by_year` are **not re-levelled by this lane**; the finding is
about the instrument's *form* (a quantity row replacing a price), not its level.

---

## 5. P-1 / P-2 — the retrofit cap releases in 2031, and the CES premium was masked, not absent

ADDENDUM 1 §4 pre-registered both from committed inputs at zero LP.

**P-1 — EXACT HIT.** Point estimate: the cumulative 3 GW/yr cap stops binding on NEISO in **2031**.
Measured on CES-P60: **100.0 % of the cumulative cap in 2028, 2029 and 2030** (3,000.0 / 5,998.5 /
8,998.3 MW), then **81.4 % in 2031** and falling every year after.

**P-2 — half right, and the wrong half is the campaign result.** Its first clause holds: the
constraint hands off from the cap to **economics and retirement**, and `gas_cc_ccs` plateaus at
**10,190.9 MW (2032) = 79.1 %** of NEISO's **12,886.0 MW** eligible `gas_cc` fleet, never
approaching exhaustion. Its second clause — that release would still show **no** premium elasticity
— is **FALSIFIED**:

| year | 2028 | 2029 | 2030 | 2031 | 2032 | 2040 | 2049–50 |
|---|---|---|---|---|---|---|---|
| **CES-P60 − REF `gas_cc_ccs` (MW)** | +34.6 | +93.3 | +1,307.0 | **+2,063.5** | **+2,483.0** | +3,151.8 | **+3,517.3** |

The $60 premium sustains **+2.0 to +3.5 GW of CCS above REF for two decades** and cuts cumulative
CO₂ from 122.81 to **92.91 Mt (−24 %)**.

> **The Stage-C memo's §6 reading — that NEISO's CES-premium numbers measure what the fleet can
> absorb under a 3 GW/yr cap rather than what a credit buys — is CORRECT FOR THE WINDOW STAGE A
> COULD SEE, and stops being correct in 2031.** Stage A's five-year window ended inside the
> cap-bound region, where the P60−REF gap is +34.6 and +93.3 MW *because both arms are pinned at the
> cap*. **NEISO's CES-premium effect was masked by the cap, not absent**, and the 25-year horizon is
> the instrument that discriminates. If the elasticity is the question, the cap is still the
> parameter to vary — but the horizon alone already answers whether one exists.

---

## 6. CES-T80 — the repaired-seam leg, and the campaign's most consequential single number

Solved at HEAD on `e4286b070d08cdcb` (matching the pre-declaration), 25/25 years, **336.2 min**,
peak RSS 3.82 GB. Cumulative CO2 **95.84 Mt** against REF's 122.81 (**-22 %**).

**P-3 IS CONFIRMED.** ADDENDUM 1 predicted, before the solve, that `CES-T80`'s `gas_cc_ccs` delta
against REF would turn **strictly positive** at HEAD, against Stage A's `+0.0 MW`, because capx D87
repaired the seam. Measured, against the committed Stage-A (pre-D87) bundle:

| year | Stage-A `gas_cc_ccs` | Stage-B | **D87 delta** | REF | **T80 - REF** |
|---|---|---|---|---|---|
| 2026 | 0.0 | 0.0 | **+0.0** | 0.0 | **+0.0** |
| 2027 | 0.0 | 0.0 | **+0.0** | 0.0 | **+0.0** |
| 2028 | 2,965.4 | 2,998.5 | +33.1 | 2,965.4 | +33.1 |
| 2029 | 5,905.2 | 5,997.5 | +92.3 | 5,905.2 | +92.3 |
| 2030 | **7,691.3** | **8,549.6** | **+858.3** | 7,691.3 | **+858.3** |

**At Stage A this leg's `gas_cc_ccs` was 7,691.3 MW — byte-identical to REF, i.e. the `+0.0 MW` the
Stage-C memo made its headline. At HEAD the same leg, same config, buys +858.3 MW at 2030, rising to
+6,047.8 MW by 2050.** The `$50` target ACP was never worth nothing on NEISO; it could not reach the
retrofit screen. **The memo's five-of-six-ISO zero was a code seam, and D87 closed it.**

The attribution is again exact by the mechanism's own gate year: the D87 delta is **0.0 in 2026 and
2027** — before `ccs_retrofit_available_year = 2028` — and non-zero in exactly the three years the
screen runs. GATE I accordingly **FAILS** on the 1e-6 identity (`co2_mt` 9.36e-02, `lw_price`
2.07e-02, `total_gen_mwh` 1.42e-04) and every part of that failure is D87's, as §3 requires.

Over the horizon `CES-T80` holds **+1,582 MW** (2031-35), **+3,754 MW** (2040-46) and **+6,048 MW**
(2049-50) of CCS above REF, cutting CO2 from REF's 3.0-5.5 Mt to 1.9-2.4 Mt while the load-weighted
price falls 51.89 -> 33.82 $/MWh.

**The standing constraint ADDENDUM 1 imposed on this comparison is honoured here rather than
footnoted.** `CES-T80` and `CES-P60` are **not one instrument at two levels**, even at HEAD: a
premium enters `apply_eac_to_mc` -> dispatch marginal cost **and** the retrofit screen, while a
target row's dual enters entry, retirement and — only since D87 — the retrofit screen. They are
reported side by side and never ranked on one axis. With that said, the two now land close on the
quantity that matters — cumulative CO2 **95.84** (T80) vs **92.91 Mt** (P60) against REF's 122.81 —
where before D87 the target row reached the retrofit channel not at all.

**Invariant I3 declared and diagnosed, not absolved (rules 1/11):** dump 2.89 % (2043) rising
through 4.67 % (2045), the same late-horizon curtailment signature every other leg carries, arriving
in the same window. I13 records a WARN (cobweb: gas_cc 5, gas_ct 4); the ledger declares FAILs only.

---

## 7. Invariants and registration — the deliverable

**All six legs are registered in the `frontend/data/forecast/` namespace, each in the same commit as
its leg and its invariant declaration**, via the single `scripts/register_forecast_run.py --summary
… --kind scenario` path. The PJM Stage-A precedent — ten legs solved, none registered across three
desk refreshes — is what that discipline exists to prevent.

| leg | run id | declared FAILs | WARNs |
|---|---|---|---|
| REF | `neiso-2026-2050-scn-campaign-stageb-2026-09-07-ref` | I3 | I13 |
| CAP-STATE-TIGHT | `…-cap-state-tight` | I3 | I13, I14 |
| ALL-CLEAN | `…-all-clean` | I3 | I13 |
| CES-P60 | `…-ces-p60` | I3, I9 | I13, I14 |
| CARB-HI | `…-carb-hi` | I3 | I13 |
| CES-T80 | `…-ces-t80` | I3 | I13 |

**I3 is declared on every leg and diagnosed rather than absolved (rules 1/11).** On five legs it is
late-horizon **curtailment** (dump > 2 % of renewable potential, first crossing 2043–2045) — the
25-year horizon's own signature, which NEISO's committed T3 goldens (`neiso-2026-2050-t3-golden-bau`
and four siblings) already carry, and which Stage A's five-year legs could never reach. On
**CAP-STATE-TIGHT alone** it is **unserved load**, which is that leg's result (§4.1). **I9** on
CES-P60 is the storage-tiebreaker miss the Stage-A NEISO lane diagnosed, whose 2030 value here is
**byte-identical at 9.41 %**; this lane extends the measurement to 2031–2050 and does **not** repair
it — rule 9 fixes ε at 0.001 $/MWh and a lane that raised it to buy a PASS would be fitting the
diagnostic.

**`scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` was run after every
registration. This lane's own exit code, quoted verbatim, was `0` every time** ("forecast-invariant
artifact audit OK"; 182 sidecars / 2,548 records / 223 FAILs declared at the CARB-HI registration).

**Artifact route.** The S20 `.gitignore` narrowing was **re-checked against `origin/main`
immediately before every registration commit and had not landed**, so each leg's two slim files
(`full_horizon_summary.json`, `run_config.json`) are mirrored to
`docs/handoffs/scn-ws5b-neiso/<CASE>/`, as ADDENDUM 1 §5 declared and as the NYISO lane did. **No
`git add -f`, no `.gitignore` edit.** They should be re-homed to
`results/scn-campaign-stageb-2026-09-07/NEISO/<CASE>/` once SCN-WS5B-NYISO's one-line change lands.

---

## 8. Routed to SCN-DESK — reported, not acted on

1. **`pjm_seam_neighbour_hourly_ladder` is an unregistered cache-key field.** It re-keys every
   config of every ISO — every keeper, every cached bundle — and a default `ScenarioConfig` at HEAD
   no longer hashes to the program's own `PINNED_DEFAULT_CACHE_KEY`. Attribution is exact and
   reproducible at zero LP (§2). Contrast the two fields that landed correctly in the same window,
   `hydro_budget_period_by_instrument` and `netload_drag_merit_allocation`, both registered with a
   frozen `"False"` declaration and moving no key.
2. **A G-DRIFT verdict is pin-scoped.** The parent PRECOMMIT §3's "no hunk is LIVE" was true at
   `a667073f` and false at `b849a51b`. Any lane inheriting a G-DRIFT should re-run it, not inherit it.
3. **The Stage-C memo §5's headline is now historical, and this lane measured by how much.**
   `CES-T80` buying +0.0 MW of retrofit on five of six ISOs was a measurement of the **pre-D87**
   code. On NEISO the same config at HEAD buys **+858.3 MW at 2030** and **+6,047.8 MW by 2050**
   (§6). The other four affected ISOs (MISO, PJM, NYISO, CAISO) carry the same pre-D87 zero and
   **their Stage-A CES-T80 numbers should be treated as superseded rather than re-quoted**; only a
   re-solve at HEAD can say by how much. The memo is a committed campaign record and this lane did
   not edit it.
4. **CES-P60's I9 storage-tiebreaker miss** extends across 2031–2050 at up to 19.34 % of throughput.
   Unrepaired here by design; the structural question (does the rule-9 ε need to scale with the
   negative-price regime a high clean-attribute price creates) is the Stage-A NEISO lane's, re-raised.
5. **LP budget error, for future planning.** ADDENDUM 1 §6's per-leg estimates, scaled from Stage-A
   five-year rates, were wrong by up to **3.9×** on the heavy arms (ALL-CLEAN 301 min actual vs 77
   estimated) and **too pessimistic** on CAP-STATE-TIGHT (237 vs 364). **25-year legs do not scale
   linearly from a five-year leg**, in either direction. Measured min/solve-year: REF 0.61,
   CARB-HI 0.64, CES-P60 0.87, CAP-STATE-TIGHT 9.49, ALL-CLEAN 12.04, CES-T80 13.45 —
   a **22x spread** across six legs of one ISO.
6. **A `data/clean` partition was missing on a fresh checkout** and hard-failed both opening legs in
   ~90 s (`confirmed-retirements`, absent for NEISO with `confirmed_exits_enabled` on). The error
   names its own fix and `scripts/data/curate_confirmed_retirements.py` regenerated all six
   partitions; noted only because it is a standing first-solve cost for any lane on a fresh
   container.

**Not touched, per the charter:** `.gitignore` · `src/market_sim/**` · `scripts/**` · `configs/**` ·
`tests/**` · other ISOs' shards and results trees · the backcast namespace · `program-status.json` ·
`ff-verdicts.json` · the desk ledger · the plan's §5.1.

---

## 9. Mechanism matrix (rule 28(b)) — four cells, not one

The lane brief anticipated "one appended cell line". This campaign materially tested **four**
mechanisms on NEISO, and rule 28(b) binds per mechanism, so **four cells** in
`docs/codebase-site/data/mechanism-matrix/NEISO.js` carry new evidence and citations — no other
ISO's shard was touched, and no verdict letter moved:

| cell | what Stage B added | `fc` |
|---|---|---|
| `federal_ces` | the cap releases in 2031; the premium then separates from REF by +2.0–3.5 GW of CCS for two decades (P-1 hit, P-2 half-falsified) | **stays O** |
| `federal_ces_target` | the target row's `+0.0 MW` was a code seam; D87 closed it, +858.3 MW at 2030 → +6,047.8 MW at 2050 | **stays O** |
| `mass_cap_schedule` | the longer horizon this cell was explicitly waiting for; binds 23/25, dual → 5,337.55, load-shedding from 2042, 2.6× REF's cumulative CO₂ | **stays O** |
| `carbon_price_path` | the post-2030 RGGI crossing this cell named as untested: CARB-MID masked 25/25 (killed at zero LP), CARB-HI live in exactly 10 years but marginal | **stays O** |

**No `fc` letter moves**, and that is deliberate: all four are **scenario levers with default-off
fields**. Arming any of them as a forecast posture would be a policy assertion the model must not
make. What the campaign establishes is that each lever *works*, and on what horizon — which is what
`O`-with-evidence means. `scripts/check_mechanism_matrix.py` exits **0** after the edit (the
remaining warnings are pre-existing `scenarios.py` line-anchor drifts in the shared base-row file,
which this lane does not own).
