# PREREG — miso-137: decomposition of the MISO 2024/2025 mean-LMP gap into its actual-spike-hour and BODY components

**Session:** miso-137, 2026-08-06, branch `claude/miso-137-calibration-2uc53h`,
off `origin/main` at `3b671bf5`. Charter lane **(a)** — *DECOMPOSE THE GAP
FIRST*.

**Committed and pushed BEFORE any adjudicating statistic is computed.** No LP
will be solved in this lane: every number comes from the **committed keeper
bundle sidecars** and the **committed measured actual series**. Nothing will be
written under `data/raw/`. No mechanism will be built, sized, tuned or armed.
No parameter will be derived. MISO keeper unchanged at
`2026-08-05-miso-132b-cc-committed`.

**Owner directive (2026-08-06, miso-136 chat) governing this session:** the
target is the **2024/2025 mean-LMP level miss**. C7 `COAL_PRB` is
DEPRIORITIZED by owner order — no C7 lane is chartered here and no C7 ledger is
sought. This satisfies the rule-28(a) off-target statement.

---

## §0 — Everything already in hand (disclosed before the adjudicating statistic)

All re-verified this session from committed artifacts only
(`scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`,
no solve), so §0 is measurement, not recollection.

**Keeper determination:** `NOT-YET`. Sole FAIL: C7 diurnal shape, 2025
`COAL_PRB` (profile r 0.971, off-peak cv_ratio 0.338) — **out of scope by owner
order**. Ledgered caveats {C3a, C3c}. C1 16/16, C2 PASS, C3b PASS, C4 PASS,
C6 PASS, C8 PASS.

**C3a — the target (gated basis: RT, load-weighted `rt_lw`):**

| year | model $/MWh | actual `rt_lw` $/MWh | gap $/MWh | % | status |
|---|---:|---:|---:|---:|---|
| 2023 | — | 32.87 | — | **−2.2 %** | PASS |
| 2024 | — | 32.27 | — | **−8.0 %** | PASS |
| 2025 | 38.66 | 45.39 | **−6.73** | **−14.0 %** | CAVEAT (ledgered) |

**C3a DA diagnostic (never gated):** 2023 **−4.4 %**, 2024 **−8.3 %**, 2025
**−15.6 %**. Committed DA−RT premia: **+1.37 / +0.86 / +0.90** $/MWh. Committed
`da_lw`: 34.24 / 33.13 / 46.29.

**C3c — the actual scarcity tail (RT hourly, >$200):** actual **30 / 37 / 88**
hours; model (energy-only LMP) **0 / 6 / 0**. DA companion: actual DA>$200
**1 / 24 / 38** hours.

**The claim under test (the 2025 C3a ledger, verbatim):** *"The 2025
annual-mean miss is the arithmetic tail of the C3c residual, NOT an independent
level error … Those 88 Indiana-Hub spike hours (actual up to $1,783; model ~$50
median) contribute the bulk of the $6.73/MWh gap."*

**Why the charter calls that under-evidenced (disclosed as the motivating prior,
not as evidence):** the DA-side gap is −8.3 % / −15.6 % while DA actual carries
only 24 / 38 hours above $200 — a much thinner tail than RT's 37 / 88 — so the
DA gap cannot be the same spike arithmetic. **This is a prior. It is not the
result, and §4's decision rule is written so it can be refuted.**

**C3c is FRONTIER-DESIGNATED (2026-07-20)** and closed to tuned adders. The
admissible object of this session is therefore the **BODY** price formation, and
the honest possible outcome that the body is *small* is pre-committed as a
first-class result (§4).

**Named prior lanes, read before this PREREG:**
`FINDING-miso87-c3b-summer-2025-body-2026-07.md` (2025 summer body),
`FINDING-miso130-c7-night-regime-2026-08-05.md` (July-night regime / wave
compression), `FINDING-miso134-ct-night-order-binding-not-licensing-2026-08-05.md`
(hour-invariant flat CT margin), `FINDING-miso133-overnight-identity-basis-2026-08-05.md`
(the ONE-BASIS bar).

**Committed 2025 `rt_lw_mon`** (disclosed, since it is already in the bench and
would otherwise look like a result): `[51.23, 46.29, 37.91, 37.70, 33.94, 57.37,
59.47, 40.44, 46.37, 38.66, 40.47, 47.25]`.

---

## §1 — The basis, fixed in advance (miso-133 ONE-BASIS bar)

Read out of the code before writing this PREREG, so no basis is chosen after
seeing a number.

* **Model price** — `results/calibration/miso132_ccmin_B/hourly/system_<year>.parquet`,
  rows `pass == "P1"` (P1 is the scored pass), columns `price` (energy-only
  LP dual) and `demand`, per model zone × hour.
  The scorer's C3a model scalar is
  `Σ_z (p_z · D_z) / Σ_z D_z` with `p_z = Σ_h (price_{z,h}·dem_{z,h}) / Σ_h dem_{z,h}`
  and `D_z = Σ_h dem_{z,h}` (`render_calibration_html.build_payload` →
  `calibration_verdict.score_price_mean`), which is algebraically the full
  zone-hour load-weighted mean `Σ_{z,h}(price·dem) / Σ_{z,h} dem`.
  **The energy-only `lmp` block is what C3a gates on** — never `lmpScar`
  (that is C3c's settlement series); the keeper bundle carries no
  `scarcity.parquet`, so no overlay can leak in.
* **Actual price** — `data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`,
  columns `rt` / `da`. Composition is `INDIANA.HUB`
  (`derive_miso_hub_lmp.SYSTEM_HUB`), on the model's **chronological non-leap
  CST 8760 calendar** — the same clock the model dispatches on (the 2026-07-15
  clock repair; the pre-repair prevailing-time indexing was one real hour off).
* **Actual scalar** — `frontend/data/backcast/bench/MISO/<year>.json.gz`
  → `bench.avgLMP.rt_lw` / `da_lw`, defined
  (`derive_actual_lmp._lw_stats`) as `Σ_h (a_h·W_h) / Σ_h W_h` over hours with a
  non-NaN actual and `W_h > 0`, where `W_h` is **total measured system demand**
  (`eia_loader.load_demand`) — the same measured series the model dispatches.

**The consequence that makes this decomposition exact.** Both sides carry the
same weights `W_h = Σ_z dem_{z,h}`. Writing the model's hourly system price
`p_h = Σ_z(price_{z,h}·dem_{z,h}) / W_h` and the actual `a_h`:

```
model_lw − actual_lw  =  Σ_h W_h · (p_h − a_h) / Σ_h W_h
```

so the contribution of ANY hour-set `S`, `C(S) = Σ_{h∈S} W_h (p_h − a_h) / Σ_h W_h`,
is **exactly additive** and every partition's parts sum to the total gap with
no residual term. **`C(·)` in $/MWh is the single reported currency of this
session.** No other decomposition (ratio-of-means, per-hour percentage,
unweighted means) will be quoted.

**Masking.** Hours are kept only where the actual is non-NaN and `W_h > 0`
(2025 has 8,759 of 8,760). Both sides are masked identically; the coverage
count is reported per year.

**Bases are never blended.** RT is the gated basis and is primary. DA is
reported as a **separate, complete, parallel** decomposition, never averaged
with RT, and never used to state a C3a verdict.

---

## §2 — Gates

* **G-0 (basis validation, must pass before any decomposition is read).**
  Reproduce, from the sidecars alone, (i) the committed `rt_lw`/`da_lw` scalars
  and (ii) the scorer's model C3a scalar and its `%` error, for all three years.
  **Tolerance ±$0.05 /MWh and ±0.2 pp** (the payload rounds `p` to 2 dp and `d`
  to 4 dp in millions). **If G-0 fails, the session reports the basis defect and
  stops** — a decomposition on an unvalidated basis is worthless, and a
  reproduction failure would itself be the finding.
* **G-1 (coverage).** Report kept-hours per year. No year with < 8,000 kept
  hours is decomposed.
* **G-2 (rule 22).** Only 2023, 2024, 2025. **2023 is included as a CONTROL** —
  it PASSES C3a at −2.2 %, so its body contribution is the natural null against
  which 2024/2025 are read. No out-of-training year is touched.

---

## §3 — The statistics, defined before they are computed

**Tail set** `T_RT(year)` = kept hours with **actual RT > $200/MWh** (the C3c
frontier component, out of admissible scope). On the DA basis the parallel set
`T_DA` uses **actual DA > $200**. The tail is defined by the **ACTUAL**, never
by the model — defining it by the model price would make the split circular.

**Body set** `B` = kept hours not in the tail set.

**Primary adjudicating statistic** — for each year and each basis:

```
body_share = C(B) / C(all kept hours)
```

the fraction of the total signed gap carried by the body. (`C(T) + C(B) =
C(all)` exactly, by §1.)

**Secondary — the pre-named look-alike trap (charter §a).** *The trap is:
attributing the body gap to "diffuse spike spillover" — adjacent-hour effects
must be MEASURED, not assumed.* Test: recompute `C(B)` on
`B_excl(k) = B \ {hours within ±k of any tail hour}`, for **k = 3** (primary)
and k = 1, 6 (reported). Statistic: `spill(k) = 1 − C(B_excl(k)) / C(B)`,
the fraction of the body gap sitting adjacent to a spike.

**Tertiary — the window map.** `C(B)` cut by **season × hour-of-day block**:
seasons Winter (Dec/Jan/Feb), Spring (Mar/Apr/May), Summer (Jun/Jul/Aug), Fall
(Sep/Oct/Nov); blocks **h0–5** (night), **h6–11** (morning), **h12–17**
(afternoon), **h18–23** (evening), with `hod = hour % 24` on the CST calendar.
The full **12 month × 24 hour** grid of `C(·)` is emitted alongside, so the
blocking cannot hide structure. A cell is **DOMINANT** if it carries
**≥ 25 %** of `C(B)`.

**Sensitivity (guards the $200 cut).** The whole tail/body split is repeated at
thresholds **$100** and **$500**. A verdict that flips across these is reported
as threshold-dependent and NOT asserted.

**DA basis extra line — the DART guard.** The model is an RT analogue and the
scorer explicitly holds that the DA−RT risk premium is not the model's to price.
The DA body gap is therefore reported **both raw and net of the committed
annual DA−RT premium** (+1.37 / +0.86 / +0.90). The net figure is the one read
as a *body-level* statement; the raw figure is reported so nothing is hidden.

---

## §4 — Two-sided decision rule, pre-committed

Read on the **RT (gated) basis**, on **2024 and 2025** (the owner's target
years); 2023 is the control and is reported but does not drive the verdict.

* **LEDGER HOLDS (tail-dominated).** `body_share ≤ 0.40` in **both** 2024 and
  2025. ⇒ The 2025 C3a ledger's tail-arithmetic claim is **SUPPORTED**; the
  mean-LMP target routes back to the C3c frontier and the honest next step is
  the owner-facing assessment, not a body lever. **This outcome is as valuable
  as its negation and WILL be recorded as the session's headline if it
  obtains** (charter §a).
* **LEDGER FAILS (body-dominated).** `body_share ≥ 0.60` in **both** 2024 and
  2025. ⇒ The gap is an **independent body-level error**; the window map names
  where, and lane (b)'s bridge / a class-free measured identification is aimed
  at that window.
* **MIXED / SPLIT.** Anything else, including a split between the two years.
  ⇒ **No single verdict is asserted.** Both years are reported at full
  magnitude with the window map, and the ledger is described as *partially*
  supported, naming exactly which year and how much.

**Trap-conditioned override, pre-committed:** if the verdict is LEDGER FAILS
but `spill(3) ≥ 0.50`, the body gap is **NOT** read as independent — the
look-alike fired, and the verdict is reported as **spillover-confounded**, not
as a body error. `spill(3) < 0.20` is recorded as spillover immaterial;
0.20–0.50 as ambiguous.

**Prior, declared two-sided.** I hold roughly even odds. The DA evidence in §0
points toward a real body component (LEDGER FAILS); the 2025 tail is large
enough (88 hours, actual to $1,783 against a ~$50 model) that a purely
arithmetic reading of the RT gap is entirely plausible (LEDGER HOLDS) — an
88-hour set at a several-hundred-dollar mean deviation is on the order of the
whole $6.73 gap before any body term is invoked. **I do not know which way this
goes, and the MIXED branch exists because a split across 2024/2025 looks at
least as likely as either clean outcome.**

---

## §5 — What this session will NOT do

* **No LP solve, no arm, no field, no `ScenarioConfig` change, no parameter
  derivation.** Whatever the window map says, sizing a lever to it is a separate
  session with its own PREREG and full kill stack (charter §c, rules 13/21/24).
* **No adder, offset or multiplier tuned to any residual reported here** —
  the C3a/C3c ledgers' own bar, and rules 1/21/24. A window map is a
  *localisation*, never a magnitude to fit.
* **No cell verdict minted** unless a mechanism is actually tested (rule 28(b));
  this lane tests none, so the expected matrix effect is a **§5.4 queue stamp
  only**.
* **No out-of-training year** touched (rule 22; MISO holds no
  `calibration-complete` marker).
* **No other ISO's cell or keeper touched** (rule 25).
* **No C7 work** (owner directive).

---

## §6 — Deliverables

Probe `scripts/probes/_miso137_c3a_gap_decomposition.py` (stdlib + pandas/numpy,
reads committed artifacts only), machine record
`results/calibration/_miso137_c3a_gap_decomposition.json`, FINDING
`results/calibration/FINDING-miso137-<outcome-slug>-2026-08-06.md`,
§5.4 queue stamp, `docs/calibration-log/miso.md` entry. **Rule 15: no LP is
solved in this lane, so there is no run to register** (the miso-131…136
precedent).
