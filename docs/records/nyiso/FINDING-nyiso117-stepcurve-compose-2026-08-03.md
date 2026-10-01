# FINDING — nyiso-117: the composition solved clean, and the supersession it was ordered to repair never happened

**Date:** 2026-08-03 · **Scope:** NYISO 2023–2025 · **Keeper:**
`2026-08-03-nyiso160-ctmeter-screen-b` → **`2026-08-03-nyiso-117-nyc-rcpf`** ·
**Pre-registration:** `PREREG-nyiso117-nyc-stepcurve-compose-2026-08-03.md`
(committed and pushed before either solve).

---

## §1 — the headline, stated before the gates

The session was ordered to compose two orthogonal rule-14 `[R-ACCURATE]`
corrections — the CT heat-rate meter-artifact **input** fix (on the designated
keeper) and the NYC locational RCPF demand-curve **shape** mechanism
(`nyiso_nyc_rcpf_step_curve`) — because nyiso-115 solved the mechanism against
what was believed to be the **pre-fix** CT artifact and therefore yielded its
keeper to caiso-160.

**Every gate passes and the mechanism is re-promoted.** But the more important
result is the one the same-HEAD control was built to measure and nobody had
measured:

> **nyiso-115's arms were ALREADY on the post-fix CT artifact.** This session's
> control is **bit-identical** to nyiso-115's control *and* to the designated
> keeper, and this session's treatment is **bit-identical** to nyiso-115's
> treatment — `max |ΔMW| = 0.000000` and `max |Δprice| = 0.000000` on every
> class-hour and every zone-hour of all three years.

The supersession was therefore unnecessary. It was not unreasonable — the
artifact vintage was *assumed* from commit ordering rather than measured, and
assuming it the other way would have risked promoting a genuinely stale bundle.
But the record should say what is true: **nyiso-115's keeper was never stale**,
and this session's contribution is the measurement that proves it, not a new
result.

## §2 — the null is real, and it is NOT "the CT fix does nothing"

The obvious alternative explanation for §1 — that the CT heat-rate correction is
simply inert on NYISO — is **refuted by caiso-160's own two arms**, which are
still on disk and differ substantially:

| comparison | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| **caiso-160 pre-fix `control_A` vs post-fix `screen_B`** — the CT fix itself | max \|ΔMW\| **508.19** · max \|Δp\| **$10.50** | **628.89** · **$10.56** | **387.23** · **$9.04** |
| nyiso-115 control vs nyiso-117 control | **0.000000** · **$0.000000** | **0.000000** · **$0.000000** | **0.000000** · **$0.000000** |
| designated keeper vs nyiso-117 control | **0.000000** · **$0.000000** | **0.000000** · **$0.000000** | **0.000000** · **$0.000000** |
| nyiso-115 treatment vs nyiso-117 treatment | **0.000000** · **$0.000000** | **0.000000** · **$0.000000** | **0.000000** · **$0.000000** |

The fix moves NYISO by up to **629 MW** of class dispatch and **$10.56/MWh**
where it applies. nyiso-115's arms show **exactly zero** difference from the
post-fix side. Those two facts together identify the artifact vintage: nyiso-115
solved **after** `f6238a5` ("caiso-156 fix: apply the CT heat-rate physical band
at the HOUR, not only the plant aggregate", committed 2026-08-03 00:05:32), which
is the only commit that has ever changed
`data/raw/_processed-legacy/campd_ct_heat_rates_NYISO.csv`.

**A caution against the tempting shortcut, stated precisely.** The test that
looks like it would answer this from git alone —
`git merge-base --is-ancestor f6238a5 <sha>` — reports "not an ancestor" for
*every* other session's HEAD in a fresh container, because those branch commits
are **not fetched locally**. **Git itself does distinguish the two cases**: a
missing object exits **128** with `fatal: Not a valid object name`, while a
genuine negative exits **1**. What collapses them is the *caller* — the ordinary
`cmd && echo yes || echo no` idiom (and a `2>/dev/null`) maps every non-zero exit
to "no", turning "I cannot see that commit" into "the fix is absent". So the
shortcut is not unsound in git; it is unsound as usually invoked, and that is the
same failure mode as reading a pipeline's exit status instead of the process's.
The dispatch comparison above needs no such care, and that is why it is the
evidence quoted.

## §3 — a standing caution that did NOT fire, and was measured rather than assumed

FINDING-nyiso114 §2 established that a keeper arming a P0-run-pattern commitment
bridge does **not** re-solve to byte-identity once main moves (max |Δprice|
$9.0–10.6 there). That is why the pre-registration made a same-HEAD control
**mandatory**, and the caution was live: the keeper solved at `b8d5e04` on
caiso-160's branch and this session's HEAD is `722f5ca`.

Between those two HEADs the drift measured **exactly zero** — kill **K-A**
reports `control_vs_keeper_max_abs_ddual_DRIFT = 0.0` for both NYC families in
all three years. The same-HEAD design was still the right call (the drift is not
knowable in advance), and its value here is precisely that it turned an
assumption into a number. Had the control been skipped, §1 and §2 would have
been unavailable and the bit-identity would have gone unnoticed.

## §4 — gates

| gate | result |
|---|---|
| **G1** curve armed | **PASS** — the NYC families reach exactly $25.00 in **14/6/19** (10-min) and **2/6/8** (30-min) hours, and sit on an interior ramp rung in **zero** hours of all three years |
| **G2a** scope, CONSTRUCTION (the kill) | **PASS** — all **seven** non-NYC families' `requirement_mw` **float32-exactly identical** to control (Δ = 0.0), all three years |
| **G2b** scope, independent corroboration | **PASS** — solve-log ORDC steps **73 → 59** in *each* of the three years, a drop of exactly **14 = 2 families × 7 rungs**, with the family count unchanged at **9 → 9** |
| **G2c** scope, reported not a kill | non-NYC `shortfall_mw` Δ = 0 everywhere; `dual`/`held_mw` reported and deliberately **not** gated |
| **G3** LP row identity | **PASS** — `held + shortfall ≥ requirement` everywhere, tight exactly where the family prices |
| **G4** feasibility | **PASS** — zero unserved-energy slack and zero dump in **both** arms, all three years |
| **G5** span | **PASS** — 2023–2025 in one bundle per arm; holdout freeze ACTIVE and untouched |
| **G6** scoring | **PASS** — both arms scored; determinations identical |
| **K-A** drift | **does not fire** — drift 0.0 against a treatment effect of $12.50–$21.875 on the NYC duals |
| **K-B/K-C/K-D** | do not fire |
| **K-E** composition additivity | **does not fire** — see §5 |

### §4.1 — G2 was written on construction, and that is why it is informative

nyiso-115's G2 demanded byte-identity of `dual`, `requirement_mw`, `held_mw` and
`shortfall_mw` for every non-NYC family. Three of those four are **solved outputs
of a co-optimization**, so the gate could only pass when the mechanism did
nothing; it failed uninformatively and had to be decomposed after the fact.

This session pre-registered the decomposition instead: the kill (**G2a**) is
`requirement_mw` alone — the balance-row RHS, the one **pure input** in the
sidecar — corroborated by an instrument that never touches the parquet at all
(**G2b**, the solve log's ORDC step count). `dual` and `held_mw` are reported and
**explicitly not gated**, and `shortfall_mw` is demoted to a reported quantity
(**G2c**) because it too is a solved LP variable, zero on the non-NYC families
only because they are slack. Gating a kill on it would have repeated the same
category error at one remove.

**Two dtype/instrument lessons were also inherited rather than re-learned.**
Byte-identity is asserted as float32 **exact** equality (`np.array_equal`), not
against a `1e-6` MW tolerance the dtype's spacing (7.6e-06 – 6.1e-05 MW) cannot
represent — the nyiso-116 G3/P4 failure. And every reserve gate reads
`hourly/reserve_family_<year>.parquet`, never `system.parquet`'s `reserve_price`,
which is the cross-family SUM broadcast identically to every zone.

## §5 — effect, and the null that was pre-registered

Measured treatment-vs-control at one HEAD:

| year | mean zonal price Δ | NYC max ($/MWh) | **LI hours >$300 (C3c)** |
|---|--:|---|--:|
| 2023 | +0.0111 % | 185.61 → **207.49** | 3 → **3** |
| 2024 | +0.0062 % | 199.13 → 199.13 | 0 → **0** |
| 2025 | +0.0213 % | 253.51 → **293.33** | 14 → **14** |

**C3c is unchanged at 3/0/14, and §5 of the pre-registration said so in
advance.** A step and a ramp are *both* $0 at or above the requirement, so this
moves the **level** of the reserve price in hours a family already binds and
**cannot add binding hours**. It therefore does **not** reach nyiso-110's
everyday-reserve-formation gap and **is not reported as closing it**.

**K-E measures the null directly rather than inferring it.** Binding hours
**gained: zero**, in every family, every year. The 30-minute family *loses* 5
hours (2023) and 1 hour (2025) — which the pre-registration also anticipated in
advance ("a steeper curve makes shortfall more expensive to incur, so binding
hours may fall"), and which is a shortfall crossing zero, not a scope leak.

## §6 — TASK 2: SENY screened ex ante, no solve spent — **S-OVER**, recorded not acted on

Pre-registered in §6 of the pre-registration as a **separate mechanism with its
own kill set** (`nyiso_ordc_measured_step_span`, cell `U`), because rule 19
`[R-ONE-MECH]` forbids folding it into the NYC flag. Screened on the same
instrument as NYC, before any conclusion was drawn.

**MEASURED.** The isolated SENY-only 30-minute adder (`DUNWOD − CAPITL`, i.e. a
SENY zone minus a zone in East but not SENY) caps at **$23.92 / $30.37 / $40.00**
in 2023/24/25, with **52 hours of 2025 at exactly $40.00** and **zero hours above
it in any year** — an atom at the published ASM items-2/12 increment over a
smooth continuum (272/133/510 material hours; 143/104/334 distinct sub-ceiling
values). All three SENY references agree exactly. **The modelled $500 base is
never reached in 26,301 hours.**

**MODEL.** The SENY family prices in **2/0/8** hours at **$62.50–$125.00**. Its
very first ramp rung — $500/8 = **$62.50** — already sits **above the entire
measured envelope**, so **9 of 10** binding hours are over-priced. **The
direction is the opposite of NYC's under-pricing.**

**SPAN.** The construction defect the flag exists to fix is confirmed
independently: the balance-row RHS carries the measured hourly requirement (mean
**1,602/1,594/1,613 MW**, max **1,800**) while the ORDC step widths are built off
the static published **1,300 MW** — mis-spanned in **69 %** of hours, ratio up to
**1.385×**.

**Action: RECORD ONLY.** No parameter was introduced, changed or fitted; no solve
was spent; no lever is proposed. A SENY curve change is
`nyiso_ordc_measured_step_span`'s mechanism and needs its own pre-registration
and its own arm.

### §6.1 — an instrument that could not observe its claim, disclosed

The screen's intended **negative control** — differencing against a zone outside
East, which should pick up the East component and therefore *disagree* with the
in-East reference — **degenerates on the 30-minute product**: the East 30-minute
adder is **identically $0.00 in every hour of all three years**, so both
references give the same answer and the control has no power to discriminate.
Reporting "the control agreed" would have claimed a pass the instrument never
had the power to give.

It is reported as **uninformative**, and the reference pair is instead validated
where it *can* be — on the **10-minute** product, where `east_10min_total` does
bind and the same `CAPITL`-vs-`WEST` pair separates in **4,603/6,993/6,611
hours** (max **$27.00/$36.05/$46.22**). That demonstrates live that the pair
detects an East component whenever one exists, which is what makes its silence on
`op_30` a *measurement of East* rather than a blind spot. (It also independently
corroborates nyiso-115's "East's $775 is never approached".)

## §7 — TASK 3: the cross-ISO queue

NYISO's transfer queue is **empty** and nothing on it was re-tested. The shared-
field ratchet was re-run and still reports **0** for NYISO
(`mechanism_matrix_gap_sweep.py --iso NYISO`: 40 family fields, **0** absent,
**0** prose-only, **0** armed-no-cell, **0** shared-gap; the single
"live-but-invisible" row is `weather_year`, the declared
`SHARED_CENSUS_EXCLUSIONS` false positive). `check_mechanism_matrix.py` passes
integrity and keeper-stamp checks.

The ERCOT (14), PJM (18), MISO (17) and CAISO (5) shared-field backlogs are
**their lanes' work** (rule 25 / 28(d) — a census can mint a `U` and nothing
more) and were not adjudicated here.

## §8 — governance

* **Rule 15** — both arms registered on the dashboard in this session.
* **Rule 16** — 2023, 2024, 2025 in one bundle per arm.
* **Rule 22** — the holdout spend freeze is **ACTIVE** and untouched; no year
  outside 2023–2025 solved, scored or read.
* **Rule 19** — SENY reported, not acted on; no mechanism stacked on the NYC flag.
* **Rule 23** — the $25/MW RCPF and the NYC-pair scope were **not** re-derived,
  re-levelled or re-scoped; this was a re-solve on a corrected input.
* **Rule 28(b)** — `nyiso_nyc_rcpf_step_curve` `O` → `K` and
  `nyiso_ordc_measured_step_span`'s note extended, in this session.
* **Rule 27** — every push touching a file ≥ 300 lines blob-verified.

## §9 — what a later session should NOT redo

* **Do not re-open the NYC curve.** Level ($25/MW, ASM §6.8) and scope (the NYC
  pair) are frozen under rule 23 and confirmed twice on measurement.
* **Do not re-run this composition.** It is now solved twice, bit-identically,
  at two HEADs.
* **Do not infer a bundle's artifact vintage from commit ordering.** In a fresh
  container `git merge-base --is-ancestor` cannot see other branches' commits; it
  says so (exit 128, `fatal: Not a valid object name`), but the usual
  `&&`/`||` idiom discards that and reports a plain negative (§2). Compare the
  dispatch instead — and if you do use the ancestry test, check the exit code.
* **SENY is open** (`nyiso_ordc_measured_step_span`, `U`), with its measurement
  already done and recorded in
  `results/calibration/nyiso117_seny_rcpf_curve_screen.json`. It needs a
  pre-registration and an arm, not another screen.
