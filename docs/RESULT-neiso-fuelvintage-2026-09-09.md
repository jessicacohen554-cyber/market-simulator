# RESULT — NEISO: the 2019-2022 retiree window and the measured monthly gas LEVEL, both promoted

**Session:** `neiso-fuelvintage-1`, 2026-09-09. **Keeper:** `2026-09-09-neiso-108-fuelvintage`,
**DETERMINATION CALIBRATED**. **Touchpoints:** `2026-09-09-neiso-108-fuelvintage-touchpoints`
(2020/2021/2022), **CALIBRATED**, stamped to the keeper.
**Companion docs:** `PRECOMMIT-neiso-fuelvintage-2026-09-09.md` (written before any LP),
`FINDING-neiso-index-vs-delivered-gas-2026-09-09.md` (the headline).

---

## 1. THE HEADLINE IS THE ZERO-LP INVESTIGATION, NOT THE PROMOTION

The program's one unresolved cross-ISO discrepancy is **settled**, and the earlier reading —
*stated but explicitly not proven* in `FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09` §6a —
is now **proven by a physical falsification**, not by argument.

**The ISO-NE published Algonquin Citygate index is right. $15.34/MMBtu is not the New England
marginal generator's January-2023 gas cost.** It is a **measurement-basis gap** — an average delivered cost including transportation and contract (LNG) charges versus the marginal commodity price — not a level defect in the model: $15.35 is a real
measurement of the fleet's **average delivered cost**, and an offer prices the **marginal** MMBtu.

> **⚠ CORRECTION made before publication.** An earlier draft called this a *respondent-composition
> artifact* — that N3045's price rests on a thin panel. **That mechanism is withdrawn.** The
> parallel session `neiso-107` measured EIA's companion **volume** series `N3045<ST>2` and found New
> England's delivered volume matches the CAMPD-metered burn to 1.6 %; their metered leg reproduces
> **exactly** here (29,290,427 MMBtu, to the MMBtu). The verdict and every other line of evidence
> are unchanged; only the *reason* the two series differ is corrected. Full account:
> `FINDING-neiso-index-vs-delivered-gas-2026-09-09.md` §3c.

**The decisive test needs no view on which survey is better.** Monthly mean realised RT LMP ÷ the
candidate gas price is the **implied marginal heat rate**; NEISO's most efficient CC is
~6.3 MMBtu/MWh, so anything below that is not a disagreement but a violation of the second law.
Over **84 months** (2019-01…2025-12):

| gas series | median | p05 | **months below the 6.3 floor** |
|---|---|---|---|
| ISO-NE AGT index | 11.13 | **7.99** | **0 / 84** |
| EIA N3045 blend | 9.36 | **5.27** | **13 / 84** |

January 2023: LMP $50.51 ÷ index $4.73 = **10.68** (plausible); ÷ N3045 $15.35 = **3.29** — a
~104 %-efficient heat engine. Log-price correlation with realised LMP: index **0.9324**, N3045
**0.8452**. Four corroborations, each independent:

- **N3045 prices Jan-2023 and Jan-2025 identically** (15.346 vs 15.316) while the market priced
  them **$50.51 vs $135.08**/MWh — and gas ran **harder** in the cheap month (49.3 % vs 46.8 %
  share, also above Jan-2022's 44.4 %). Gas ran hard because it was cheap, which is what the index
  says and what N3045 denies.
- **The Algonquin daily prints** for Jan-2023: 4.04, 3.38, 3.24, 4.23, 3.22, then 13.49 on Jan-31.
  Four weeks at $3.22-4.23. There is no path from these to a $15.35 monthly *spot* cost.
- **WITHDRAWN (kept so it is not re-derived):** this repository's own EIA-923 receipt *extraction*
  holds one New England plant that month — 1660 Potter Station 2, a 58 MW peaker, 28,703 MMBtu.
  That is a property of the **extraction**, not of EIA's respondent set, and is **not** evidence
  that N3045 is thinly sampled; `neiso-107`'s volume measurement refutes that reading (above).
- **Cross-state dispersion, and it is positive evidence for the basis reading.** MA/CT — same
  pipeline, same month, same molecule — reads 2.69× (2023-01), 3.07× (2023-05), **4.13×** (2024-03).
  The *commodity* cannot differ 4× between adjacent states on one pipe; an **average delivered cost**
  can, because the states differ in firm-transport charges and in **LNG** — Massachusetts has the
  Everett Marine Terminal, and Massachusetts is the state that prints high. The wedge is also not
  one-signed (below the index in **10 of 84** months), which is what an average-of-contracts series
  does and a marginal price does not.

**Consequence.** Rule 14 `[R-ACCURATE]`'s misalignment exception is **earned** rather than invoked;
the FINDING §4 ordering (measured hub index supersedes the state-average seam) is confirmed on
evidence. **The 2.303 $/MMBtu "level gap" the cross-ISO table reports for NEISO 2023 is the distance
between two different quantities, not a model error** — it must not be quoted as a NEISO defect.

**Recommendation, not an action:** do **not** build a NEISO copy of ercot-261's corroborator. That
instrument checks one plausibly-marginal series against a second; here the second series measures a different quantity and
fails a physical test as a marginal price in 13 of 84 months, so blending it would corrupt the
series that is already correct. **The transferable part of this finding is the implied-heat-rate
test itself** — a cheap, ISO-agnostic instrument for deciding whether an N3045 state blend behaves
like a marginal price before trusting it as a monthly level — together with §3c's caution: check
EIA's companion volume series `N3045<ST>2`, never this repository's filtered EIA-923 extraction,
before concluding anything about coverage. That matters for MISO, whose keeper carries *no* measured
monthly gas level at all and for whom a second series is an upgrade; the NEISO verdict does **not**
transfer (rule 25 `[R-ISO-SCOPE]`), only the instrument does.

## 2. WHAT WAS PROMOTED, AND WHAT IT IS WORTH

Owner ruling 2026-09-09, verbatim: *"these should be promoted as keepers on both 860 and gas shape
counts regardless of inertness."* Both promoted. **Zero new free parameters** (rule 21 `[R-DOF]`);
the neiso-106 `authorized_price_tuning` scalar 0.95470 is carried forward **unchanged** — neither
re-sized nor re-swept, no new price-tuning channel.

**Both are provably inert on 2023-2025**, measured at zero LP *before* the solve (rule 29
clause (0)) and reported as a property of the result, never as a reason to withhold:

| | measured |
|---|---|
| gas seam, fuel cells written | **0 of 22,837,320** (2023+2024+2025) |
| gas seam, full-payload sweep | **38 arrays / 38,518,653 numeric cells — none differ** |
| retiree window, injected rows | 59 / 59 / 61, nameplate 1,696.374 / 1,696.374 / 1,697.490 MW |
| retiree window, injected effective MW-h | **0.0000000000** |
| retiree window, shared-row max abs Δ | `pmax` **0.0** · `availability` **0.0** · `mc_base` **0.0** |

The seam is inert because the solve's own log says so: *"hub-basis overlay (NEISO 2023, daily): 463
gas generators repriced at the measured hub spot in **12/12 months**"* — the hub index supersedes
it in every gas cell of every month, with `gas_plant_monthly_fuel_pricing` overwriting from F923
prints on top. **The scheduled LP screen was CANCELLED, not skipped**: an LP whose inputs are proven
bit-identical cannot produce a different output.

**Charter task 3 is discharged for NEISO — and it was at genuine risk.**
`FINDING-pjm-retiree-window-redistribution-2026-09-09.md` proved the "zero effect on 2023-2025 by
construction" claim **false** for PJM (720 MW of May-2020 coal redistributed onto live siblings at
W H Sammis) and tabulated **NEISO's exposure at 521.5 MW — Mystic**, warning each ISO to measure its
own. **NEISO's realised leak is 0.0 MW.** Separately verified (§A5 item 2): the whole-plant channel
and `partial_plant_exit_carry` share **zero** (plant, unit) keys and zero plants (69 vs 24 ISNE
rows), so no double-count is possible; the flag is off in the recipe regardless.

## 3. HEAD DRIFT — reported at full magnitude, and why no control solve was spent

**G-DRIFT cannot be run as specified.** The incumbent records `git_sha 70ee7fca`, which does not
resolve in this repository (the 2026-08-16 history rewrite; no mapping in
`citation-commit-map.txt`), and the bundle predates capx D79 so carries no `solve_surface.json`.
Same blocker the PJM lane hit. **Stated, not worked around.**

**No control solve was spent** (rule 29(b)), and none is informative: the arm-vs-control comparison
at HEAD is a proven identity across all 38 payload arrays, so a control would build the same LP.
Therefore **every** difference against the incumbent's committed numbers is HEAD drift from other
lanes' commits, and **none** of it is attributable to either promoted change — an attribution
established by measurement, not by inference. Measured:

| | 2023 | 2024 |
|---|---|---|
| max abs class-hour Δ | 426.95 MW | 371.44 MW |
| largest annual class energy Δ | +0.00067 TWh on 52.7 TWh (**13 ppm**) | −0.00035 TWh |
| mean abs price Δ | 0.0039 $/MWh (mean 36.72) | 0.0055 (mean 42.07) |
| slack / dump | 0.0 / 0.0 both sides | 0.0 / 0.0 both sides |

The movement sits in `CC_REGULAR` and **hydro** — the budget-constrained, flat-marginal-cost
variable whose intertemporal placement is a numerical tie. **The two solutions are alternate optima
of the same LP.** Charter task 3's literal gate ("max |class-hour delta| = 0.000000 MW vs the
committed keeper") is therefore **not met at the dispatch layer**, and that is reported as such
rather than waved through: it is met at the **input** layer, exactly, and the dispatch residual is
root-caused to HEAD/solver degeneracy rather than to the change under test.

## 4. TOUCHPOINTS — every criterion held

`2026-09-09-neiso-108-fuelvintage-touchpoints`, 2020/2021/2022, `--holdout-authorized` under
NEISO's `complete` marker. **CALIBRATED.** Per-year ladder: **2020 CALIBRATED · 2021 CALIBRATED ·
2022 CALIBRATED.** Criterion-by-criterion, in-sample → holdout: C1/C2/C3a/C3b/C4/C6/C8 **PASS →
PASS**; C3c **CAVEAT → CAVEAT** (rubric v3.6's holdout auto-ledger). Nothing degraded.

The retiree window is **live** in these years (+956.0 MW in 2020, +949.0 MW in 2021, +201.3 MW in
2022) — and the pre-registered "a large 2022 move is a BUG, not a win" did not fire.

Stamped to the keeper under rule 30 `[R-TOUCHPOINT-FOLD]`, so it renders as ordinary year columns
of the keeper's report rather than a second card for the same config. **Rule 30(c) binds
regardless**: a held-out year never downgrades NEISO, and rule 22 makes these iterable
model-SELECTION evidence that must never be quoted as a certified out-of-sample skill number.

## 5. THE 2019 CASE — closed as far as it can be, without touching 2019

**Charter task 4 discharged.** The standing `constants.py` caveat on
`NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` — *"a 2019 solve is short ~2.18 TWh of nuclear regardless of
this overlay"* — is **retired, its premise now false**:

| Jan-May 2019 nuclear energy | TWh |
|---|---|
| **actual** (EIA-923, three plants) | **13.002** |
| pre-fix: 3,355.4 MW fleet × the committed CF row | 10.862 (**−2.140**) |
| **post-fix: restored 4,029.0 MW fleet × the same row** | **13.042 (+0.040)** |

The fleet repair alone closes **98.1 %** of the gap, leaving a **+0.3 %** over-injection well inside
NEISO 2019's ±2.366 TWh C1 band. `monthly_online_mask(1972, 12, 2019, 5, y)` gives Pilgrim exactly
**5** online months in 2019 and **0** in every year 2020+. **The CF row is left unchanged and needs
no re-derivation** — checked, not assumed: it reproduces exactly as the two-plant numerator over the
3,355.4 MW denominator, and the exact re-derived row (`[0.98, 1.00, 0.99, 0.73, 0.76, …]`, landing
on 13.002 TWh) is recorded in the constants comment for whoever eventually spends 2019, rather than
applied here — that would be a rule 23 `[R-FROZEN-DERIVE]` change to a frozen table for 0.040 TWh in
a year nobody can solve.

**No 2019 solve, score or registration was performed.** 2019 is locked-test tier, `final` empty,
freeze ACTIVE. Every number above is EIA-923 / EIA-860 data inspection plus the COD-ramp mask, which
rule 22 leaves unrestricted. **Nothing here is evidence about 2019's out-of-sample skill.**

## 6. GOVERNANCE LEDGER

- **Rule 15 / 16:** two runs registered, each **one bundle** covering its full span. The four solve
  shards were composed by **re-solving each span in a single invocation** rather than stitching
  bundles — a fragment is never registered.
- **Rule 22 D-5(b):** `complete.NEISO` re-keyed with its determination re-verification on committed
  artifacts (CALIBRATED, **not worse**). `final` untouched.
- **R-T / Q34:** the forecast gate-(a) stamp re-keyed **in this same session**, so the row was never
  stale. Verdict unaffected (PASS → PASS; identity and text only).
- **Rule 15 retention:** swept to the keeper + its folded twin; 5 runs pruned. `neiso99_joint_B`
  retained by the regression-golden carve-out.
- **Rule 28:** only `mechanism-matrix/NEISO.js` written — `gas_electric_power_monthly_level`
  **O → K**, and the retiree-window outcome recorded on `retiree_vintage_status_scope` (the
  closest-owning cell; the window adds no `ScenarioConfig` field, so charter §7's duty (c) is not
  engaged).
- **Rule 12:** the four solve shards ran two-at-a-time in this container, years sequential within
  each invocation. Declared deviation from the handoff's child-session sharding, on NEISO's measured
  4.0 GB peak against 23.7 GiB — the cap does not bind at two, and keeping the bundles on this
  session's disk serves rule 31.
- **INHERITED AND NAMED, NOT BURIED:** NEISO's `perfb-stage0` regression golden captures
  `neiso99_joint_B` and was **already stale** against the neiso-106 keeper before this promotion; it
  is staler now. The **R-AI re-capture obligation applies to this lane and is NOT discharged here**
  — it needs its own capture procedure and solves.

## 7. WHAT THIS SESSION DID NOT DO

- **2019 / H1-2026:** not attempted, not designed around, no result is evidence about them.
- **No NEISO corroborator built** — recommended against, with the reason measured (§1).
- **The N3045-vs-index question is adjudicated.** Do not re-open it without new *measured* evidence;
  there is a physical falsification behind the verdict.
- **The PJM redistribution defect is not repaired here.** It does not bite NEISO (0.0 MW realised),
  and the fix lives in the shared plant-binning path — an owner-level call about the whole program's
  frozen recipe, as that finding routed it.
