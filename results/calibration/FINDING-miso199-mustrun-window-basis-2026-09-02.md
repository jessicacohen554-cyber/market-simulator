# FINDING miso-199 — the per-plant must-run floor's WINDOW BASIS is REFUSED on its own frozen line: the window is already well-placed, and the whole commitment-floor family is closed for this phenomenon (2026-09-02)

**Session:** miso-199 (2026-09-02). **Keeper at open AND at close: `2026-09-01-miso-198-oomlevel`**
(bundle `results/calibration/miso198_oom_B`) — **UNCHANGED. Nothing was solved, nothing
promoted, nothing registered** (rule 15: no run was produced). **Charter:** the
FINDING-miso198 §7 item-1 named successor — repair the WINDOW BASIS of the
`st_gas_mustrun_*` per-plant must-run floor.

**THE CHARTER'S LEVER IS REFUSED, on the line this session froze and published before
it computed a single adjudicating number.** The refusal is not a failure to build: it
is the pre-declared outcome of a test the charter's premise did not survive.

---

## 1. The answer, in one paragraph

The charter inherited FINDING-miso198 §4's inference that the floor's window basis is
the binding defect — that "a level honest inside its own sample becomes dishonest once
placed in the floor's window", because the window is the top-`online_frac` fraction of
hours ranked by SYSTEM LOAD while the conduct's own hour set is the plant's COMMITMENT
STATE. **That inference is measurably wrong.** The keeper's own over-assertion
partitions EXACTLY (identity residual 0.0e+00) into MISPLACEMENT and LEVEL as
**0.110 / 0.568 / 0.197** against **0.890 / 0.432 / 0.803**, so the dominant channel is
**LEVEL in 2 of 3 years** and the pre-registered L-2b line REFUSES the window family
without solving. The reason is structural and is this session's real result: **the
incumbent window is already well-placed — 7 of 7 plants clear the 0.80 hit line in all
three years, energy-weighted hit 0.991 / 0.962 / 0.986** — because **57–60 % of the
entire floor assertion sits on ONE continuously-synchronized plant (1403, 688.0 MW ×
8,602 h, MISO-South) whose window cannot be misplaced.** The floor's window ranking was
never the problem. And the refusal generalizes: the third channel, `W`, is **80–85 %
attributable to the window being too SMALL (k < m in 20 of 21 plant-years), not
mis-placed**, so a *basis* change at fixed `k` cannot reach it either — and the *size*
lever is already `R` at MISO. **With the level family exhausted (miso-198 §4), the
window family refused here, and `L` unreachable by construction, the entire
commitment-floor family is closed for the out-of-merit steam phenomenon.** The residual
is a bid-side / economics object, and the successor is re-pointed accordingly (§6).

## 2. What was frozen, and when

Two zero-solve instruments, each with its rule frozen in its own docstring and **pushed
+ blob-verified BEFORE any adjudicating quantity was computed** (the standing session
pattern; miso-198 §2, miso-197 §10, miso-196 §7):

| instrument | frozen + pushed | blob-verified |
|---|---|---|
| `scripts/probes/_miso199_mustrun_window_basis_phase0.py` (the census, N-1..N-3) | `ca9681a8` | ✓ against a fresh fetch |
| `scripts/probes/_miso199_overassertion_attribution.py` (the extension, X-1/X-2) | `ca9763dc` | ✓ against a fresh fetch |

**Neither weighed anything against a price residual (rule 1 `[R-STRUCT]`). C3a does not
appear in this session at all** — not as a criterion, not as a face, not as a
direction. The window question was posed and settled entirely on conduct reproduction,
which is why nothing here can be read as having been steered by the keeper's open
C3a-2025 miss.

**The census was written to be refutable, and it refuted.** L-2b was declared verbatim
before any number: *"If it is `O_lvl`, the premise is REFUTED: the over-assertion is a
residual level effect inside correctly-placed hours, the window family is REFUSED, and
the session escalates WITHOUT SOLVING. This line is declared before any number is
computed and is not revisited."* It is not revisited.

**Bases** are the miso-198 census's own (B1 `run_year`'s own chain, B2 raw CAMPD through
the frozen deriver's helpers, B3 the committed keeper sidecars), **imported rather than
restated** (rule 23 `[R-FROZEN-DERIVE]`) and re-pointed at this session's keeper. The
miso-198 §3 `load_shape` instrument defect has a **regression test** in this session's
satisfiability: the rebuilt floor is asserted against the keeper's own logged 2023
assertion and matches it to four decimals (**9.9319 TWh**), so the window channel is
measured against the floor the solve actually built, not a fallback all-hours floor.

## 3. N-2 — the over-assertion partition (the load-bearing identity)

`O = Σ max(0, flr − meas)` over floored plant-hours partitions exactly by whether the
hour is a measured commitment hour.

| year | raw assertion | O | O/raw | **O_mis (misplacement)** | **O_lvl (level)** | identity residual |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 9.9319 | 0.6951 | 0.0700 | 0.0763 (**0.110**) | 0.6188 (**0.890**) | 0.0e+00 |
| 2024 | 10.3857 | 0.6984 | 0.0672 | 0.3969 (**0.568**) | 0.3015 (**0.432**) | 0.0e+00 |
| 2025 | 10.4408 | 0.5901 | 0.0565 | 0.1162 (**0.197**) | 0.4739 (**0.803**) | 0.0e+00 |

**L-2a DOMINANT = LEVEL** (2 of 3 years over the 0.45 line; MIS clears in 2024 only).
**L-2b: PREMISE REFUTED — the window family is REFUSED.**

**The magnitude bound, stated so the refusal is not merely categorical.** A window
repair can address at most the MIS channel. Even a *perfect* repair — one that
eliminated every misplaced MWh and introduced none — would move the charter's own
acceptance metric `O/raw_assertion` from 0.0700 / 0.0672 / 0.0565 to
**0.0623 / 0.0290 / 0.0454**, i.e. by **0.8 / 3.8 / 1.1 pp of assertion**. That is the
entire upside available to the chartered lever, and it buys **none** of the
5.024 / 7.420 / 5.924 TWh `L` channel the charter actually wants closed.

## 4. N-1 — WHY: the window is already well-placed, and one plant carries it

`hit` is the share of floored hours the plant was measurably RUNNING; `chance` is the
hit rate an arbitrary window achieves by construction; `lift = hit / chance`.

| year | energy-weighted hit | energy-weighted lift | informative (lift>1) | **well-placed (hit ≥ 0.80)** |
|---|---:|---:|---:|---:|
| 2023 | 0.9906 | 1.0703 | 6/7 | **7/7** |
| 2024 | 0.9616 | 1.0621 | 5/7 | **7/7** |
| 2025 | 0.9860 | 1.0514 | 6/7 | **7/7** |

**Plant 1403 dominates and is structurally immune to a window defect.** Its floor is
**688.0 MW × 8,602 h = 5.9182 TWh — 57–60 % of the fleet assertion in every year** —
against 8,759 / 8,294 / 8,760 measured online hours, giving `hit` 0.9999 / 0.9458 /
1.0000. Its `k` is 98.2 % of the year, which is **exactly** the synchronization share
the mechanism's own D-4 declaration cites as its evidence base (*"Nine Mile synchronized
98.2 % of ALL hours 2023-2025"*, `legitimacy_diagnostics.py` `D4_WINDOWS`). A plant
synchronized essentially all year has no window to get wrong, and it carries the
majority of the quantity under test.

The plants whose windows *are* informative (1402 lift 4.18 / 1.48 / 1.46; 6035 lift
2.68 / 1.96 / 1.97) carry **0.05–0.18 TWh** each. The window basis is only decidable
where it barely matters.

**A correction to the mechanism's own D-4 language, reported because it is now
measurable.** `D4_WINDOWS` describes this floor as *"self-windowing by construction"*.
It is self-**sizing** by construction (`k` comes from the plant's measured
`online_frac`); it is **not** self-**placing** — the placement is a system-load ranking
that carries almost no information about which hours those are (lift 1.05–1.07). The
declaration's conclusion survives on this evidence, but its stated reason is imprecise.

## 5. N-3 — the misplacement HAS structure; the structure is not where the quantity is

Two axes clear their frozen lines, and both are reported because a refusal that hides
real structure is not honest:

* **SEASONAL** — worst-4-month concentration of the false-positive floor energy
  **0.8067**, and it is one month: **February carries 354.8 GWh of the 592.8 GWh
  three-year total (60 %)**.
* **FRAGMENTATION** — the floor's mean contiguous run is **76.7 h over 123.6 runs**
  against the measured commitment's **1,575.8 h over 13.8 runs**, ratio **0.0486**. The
  top-k-by-load hour set is not a commitment state: it switches on and off ~124 times a
  year *inside* a plant's continuous run.
* DIURNAL does not clear (0.3577); DRIVER does not clear — the best alternative ranking
  (zone load, mean point-biserial 0.179) beats system load (0.121) by **0.0585**,
  under the 0.10 line.

**Fragmentation is a real shape defect and it is handed on, not acted on.** It costs
almost no over-assertion (the floor switches off inside hours the plant is running, so
the omitted hours land in `W`, not `O`), which is precisely why it cannot rescue the
chartered lever — but it is the reason the floor's D-1 shape contribution is
structurally unlike the conduct it represents.

## 6. The third channel, and why the whole family closes

miso-198 §3 partitioned the gap into `P` (population) / `W` (window) / `L` (level).
This session closes `W` as well, by arithmetic on the census's own published N-1
counts (no new adjudication):

| year | Σk (floored hours) | Σm (measured online hours) | Σ(k−m) | uncovered `|H_meas \ H_floor|` | **share explained by k < m** |
|---|---:|---:|---:|---:|---:|
| 2023 | 39,739 | 45,217 | −5,478 | 6,450 | **84.9 %** |
| 2024 | 43,591 | 49,146 | −5,555 | 7,361 | **79.6 %** |
| 2025 | 43,680 | 50,284 | −6,604 | 7,971 | **82.9 %** |

`k < m` in **20 of 21 plant-years** (the sole exception is 1403 in 2024, +308 h — the
outage cell of §7). **The window is systematically too SMALL, not mis-placed**, so a
change of *basis* at fixed `k` cannot recover `W` either. Enlarging `k` is a different
object — the window SIZE — and that lever is **already `R` at MISO**
(`mustrun_online_frac_per_year`, miso-172, rejected on its own pre-registered
liveness band).

That closes the family:

| channel | 2023/24/25 share of the gap | reachable by | status |
|---|---|---|---|
| `P` population | .162 / .138 / .183 | a membership change | miso-198 L-3b: **not a clean identification defect** (5 of 10 plants demonstrably operated); out of this charter by constraint (a) |
| `W` window | .197 / .163 / .153 | window SIZE (80–85 %) / BASIS (15–20 %) | size lever **`R`** (miso-172); basis **REFUSED here** |
| `L` level | **.640 / .699 / .665** | raising the level | **unreachable by construction**: `L` is measured energy *above* the floor in hours it is already armed, so capturing it means pinning — miso-198 §4 refused exactly that on S-ii/S-iii |

**No commitment floor — at any level, in any window, over any membership — can close
this gap without pinning.** That is the session's substantive result, and it is
stronger than the refusal the charter anticipated.

## 7. X-1 / X-2 — where the misplacement actually is, and a correction to §4

The extension is **explicitly non-adjudicating**: L-2b had already spoken, and nothing
below re-opens the refused family. It exists because a refusal that does not say where
the quantity actually lives hands the successor nothing.

### 7a. X-1 — the misplacement is ONE EVENT, not a ranking property

| plant | year-month | O_mis | share of 3-yr O_mis |
|---|---|---:|---:|
| **1403** | **2024-02** | **320.5 GWh** | **0.5438** |
| 990 | 2025-03 | 38.5 GWh | 0.0653 |
| 3459 | 2025-12 | 12.4 GWh | 0.0210 |
| 990 | 2023-02 | 12.0 GWh | 0.0204 |
| 3457 | 2025-01 | 11.7 GWh | 0.0199 |

**L-X1a: CONCENTRATED** (0.5438 ≥ 0.40). A single (plant, year, month) cell carries
**54 % of the entire three-year misplacement**. That settles the category: a *ranking*
defect is diffuse by construction — the system-load rank carries no calendar structure —
so a misplacement that lives in one month of one plant is an **EVENT**, not a property
of the basis under charter.

**The cell itself (L-X1b):**

| quantity | value |
|---|---|
| plant / class / nameplate | 1403 · ST_GAS · 1,465.4 MW |
| mean floor asserted, Feb-2024 | **688.0 MW** |
| mean measured net, Feb-2024 | **167.3 MW** |
| measured online hours | **206 of 672** (0.307) |
| **mean outage-extract availability** | **1.0000** |

The outage extract reads the plant **fully available for the entire month** while its own
meter reads it off for 69 % of it, so the `pmax × availability` clip never relaxes and the
floor asserts 688 MW straight through.

**REPORTED EXACTLY AS THE FROZEN LINE RETURNED IT, not relabelled.** L-X1b required
availability ≥ 0.50 **and** an online share ≤ 0.25. The cell clears the first (1.0000)
and **misses the second by 5.7 pp** (0.307 against 0.25), so the mechanical verdict is
**"NOT the availability family on this cell's evidence"** and it stands unaltered in
`_miso199_overassertion_attribution.json`. The threshold was frozen before the number and
is not renegotiated (the miso-172 discipline: the mechanical verdict is not
reinterpreted). What the *evidence* shows — availability 1.0000 against a meter that is
off 69 % of the month — is the qualitative signature of the named miso-172 "laid up but
reads available at PART-YEAR grain" family, and is handed on as such under §8, **without
claiming the frozen test passed.**

### 7b. X-2 — FINDING-miso198 §4's stated mechanism is WRONG

§4 refused the C2 (p50-over-out-of-merit) level and explained the refusal thus: *"A
statistic that is non-pinning inside its own sample is placed, at runtime, in a
differently selected set of hours. That mismatch — window basis, not level — is the
binding defect."* That is falsifiable, and it fails.

| year | C2 raw assertion | O | O/raw | **MIS** | **LVL** |
|---|---:|---:|---:|---:|---:|
| 2023 | 13.975 | 2.019 | 0.144 | 0.117 (0.058) | 1.902 (**0.942**) |
| 2024 | 15.010 | 1.792 | 0.119 | 0.565 (0.315) | 1.227 (**0.685**) |
| 2025 | 15.185 | 2.101 | 0.138 | 0.182 (0.087) | 1.918 (**0.913**) |

**INDEPENDENT VALIDATION OF THE REPAIRED INSTRUMENT:** the raw assertions
(13.975 / 15.010 / 15.185) and over-assertions (2.019 / 1.792 / 2.101) reproduce
FINDING-miso198 §4's own published C2 figures — *"13.975 / 15.010 / 15.185"* and
*"2.02 / 1.79 / 2.10 TWh/yr"* — **exactly**, from a different session's independently
written harness.

**L-X2: §4's stated mechanism is WRONG.** C2's over-assertion is **94 % / 69 % / 91 %
LEVEL**. The median over-asserts because it exceeds what the plant makes **in hours it IS
running** — a property of the level against its own conditioning sample, with nothing to
do with the window. **C2 nonetheless STAYS REFUSED**: S-iii refused it on the *magnitude*
of its over-assertion, which this measurement does not change and does not re-score.

This matters beyond bookkeeping. §4's window explanation is what produced this session's
charter. The explanation was wrong, and correcting it is what turns a narrow refusal into
§6's general closure: **even the refused higher-level candidate's defect was level, not
window.**

### 7c. Instrument defect, disclosed and repaired

The first X-2 run patched `thermal_tranche_p25_measured_level` — the slot
`_miso198_level_selection` patches, correct against *that* session's keeper
(`miso191_bax_B`, `st_gas_mustrun_oom_level=False`) and **wrong against this one**. This
keeper arms `st_gas_mustrun_oom_level`, and the runtime then does
`_p25_measured = {**_p25_measured, **_oom_level}` (`arrays.py:2512`), so the out-of-merit
map overrides the patched one on every ST_GAS key and the swap is a **silent no-op**. The
symptom was unmistakable and is recorded rather than hidden: the "C2" partition came back
**byte-identical to the incumbent's**. The probe now patches `thermal_tranche_oom_level`
and **aborts** if the swap fails to move the raw assertion by > 1 % against the incumbent,
so a no-op can never again be reported as a partition. The defective record was committed
as the disclosed artifact before the repair. **X-1 is unaffected** — it reads the keeper's
own unpatched floor — and stands.

## 8. Handed on

1. **THE SUCCESSOR IS BID-SIDE, NOT A FLOOR.** §6 closes the commitment-floor family.
   The measured conduct — a 10-HR steamer running while 7-HR CC capability sits idle —
   is a *cost/offer* phenomenon, and miso-198's own M-4 already enumerated the form:
   **(c) BID-SIDE SELF-SCHEDULE COST-INSENSITIVITY**, in which the measured
   self-scheduled block is OFFERED price-insensitively so the LP clears it *in merit*
   rather than forcing it. It carries **zero forced energy, hence zero C8 exposure** —
   which matters, because the class is over-budget with a grounded pass today. Note the
   governance position honestly: MISO's offer-level family carries `R`/`I` verdicts
   (miso-179 `R`, miso-180 `I`, miso-178 lever 1 `R`), so a successor needs the
   DO-NOT-REDO discipline's **new evidence** — which §3/§6 of this finding supply, and
   which is the reason they are stated as quantities rather than as a narrative.
2. **The `W` size lever is NOT re-opened by this session.** `mustrun_online_frac_per_year`
   stays `R`. §6 says only that `W` is a size object; it does not re-litigate miso-172's
   liveness-band rejection, and a successor must clear that band on its own.
3. **FRAGMENTATION (§5)** — the floor's 76.7 h / 123.6-run shape against a 1,575.8 h /
   13.8-run commitment state. A real shape defect, measured, costless in `O`, unacted.
4. **PLANT 1403, FEBRUARY 2024 (§7a)** — availability 1.0000 against a meter off 69 % of
   the month, worth 320.5 GWh, i.e. **54 % of the entire three-year misplacement in one
   cell**. The frozen L-X1b test did NOT classify it (it missed the online-share leg by
   5.7 pp) and no claim is made that it did; but on the evidence it is the miso-172 "laid
   up but reads available" family at part-year grain, and it is by far the largest single
   defect this session measured. A successor should take it as an **availability /
   outage-extract** question, which is a different mechanism under a different charter
   (rule 19 `[R-ONE-MECH]`) — **not** a floor question.
4. Unchanged from miso-198 §7: the lay-up census's cycler/mothball boundary; `CT_CHP`
   as the visible half of the steam-host family; `ST_CHP`'s CEMS invisibility; the
   standing wind +5 TWh/yr over EIA-930; the 2023 import +2.0 TWh face; the
   `_CC_PMAX_RECONCILED_PLANTS` last-writer-wins order dependence.
5. **Not this lane's, but blocking others:** the 11 `tests/unit/config` cache-key pin
   tests that fail on clean `main` (the capx-d24 repair moved the default key
   `603c2498bf71d21d` → `7a57fadff595ca83` without updating its literal pins).
   Untouched here.

## 9. Governance

Rule 22: 2023–2025 only; MISO holds no `complete`/`final` marker; the holdout freeze
untouched; **no marker read or written**. Rule 12: no solve was run at all, and none was
offloaded to CI. Rule 15: **no run was produced, so there is nothing to register** — the
deliverable is the two committed probe records plus this finding. Rule 25: only MISO's
shard is edited. Rule 27: every push touching a ≥300-line file was blob-verified against
a fresh fetch. Rule 28(b): the `st_gas_mustrun_p25` cell carries this adjudication;
**no new `ScenarioConfig` field was added**, so rule 28(c) does not apply.

## 10. Reproduction

```
python3 scripts/probes/_miso199_mustrun_window_basis_phase0.py --satisfiability
python3 scripts/probes/_miso199_mustrun_window_basis_phase0.py
python3 scripts/probes/_miso199_overassertion_attribution.py --satisfiability
python3 scripts/probes/_miso199_overassertion_attribution.py
```
