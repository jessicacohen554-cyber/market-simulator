# DIAGNOSIS — ERCOT-124: the coal offer-curve upper tail is REAL, but two-thirds of it is one jointly-owned plant's second-owner share; the class-representative residual is 1.6 pp and licenses no class mechanism

**Date** 2026-07-27 · **ISO** ERCOT · **Lane** ercot124-coal-offer-uppertail ·
**Keeper under audit** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) — **unchanged by this session** ·
**Chartered by** `docs/DIAGNOSIS-ercot123-coal-sced-reach-2026-07-27.md` §5/§7.2
(which CLOSED the coal offer-REACH question and named the upper tail as the one
surviving residual the RT instrument exposes) ·
**Method** Phase 1 only — raw-direct derivation from the 60-Day SCED disclosure
(`scripts/data/derive_sced_coal_uppertail.py` →
`data/raw/_validation-source/offer_curve_sced_coal_uppertail.json`), plus one
cross-instrument check on the 60-Day DAM disclosure.
**No LP was built. No year was solved. No arm was registered. No keeper file was
touched.**

**Outcome: Phase 1 does NOT license a mechanism, and Phase 2 was not run.** The
tail ERCOT-123 §5 measured reproduces exactly (5.0–5.3 pp of HASL above \$35,
stable across both measured years). Decomposed, **68–71 % of it is two resource
registrations** — `FPPYD1_FPP_G1_J02` / `FPPYD1_FPP_G2_J02`, the *second owner's
registered share* of two jointly-owned Fayette units whose *first* owner's share
of the same physical machines offers at \$18.41/\$18.74 against their \$150.10.
Set that owner-share conduct aside and the measured curve saturates at **\$35,
not \$500**: the model's coal offer curve is already right to within **1.6 pp of
capability**. §5 states the recommendation; §6 records what would reopen this.

---

## 1. Headline — the tail, decomposed

Measured share of telemetered `HASL` carrying a submitted RT offer at or below
each price edge (ERCOT-117 §1.1 convention, curve-carrying units floored at
`LSL`), pooled per delivery year over all 82 probe days. `all` is the whole
CLLIG fleet; `ex_owner_split` drops the two Fayette second-owner registrations.

| year | variant | ≤\$20 | ≤\$25 | ≤\$35 | ≤\$60 | ≤\$100 | ≤\$150 | ≤\$500 |
|---|---|---|---|---|---|---|---|---|
| 2024 | all | 0.689 | 0.918 | 0.948 | 0.954 | 0.964 | 0.990 | **0.998** |
| 2024 | **ex_owner_split** | 0.710 | 0.950 | **0.982** | 0.989 | **0.998** | 0.998 | 0.998 |
| 2025 | all | 0.651 | 0.914 | 0.945 | 0.955 | 0.961 | 0.997 | **0.998** |
| 2025 | **ex_owner_split** | 0.671 | 0.949 | **0.983** | 0.993 | **0.997** | 0.998 | 0.998 |

The `all` rows reproduce ERCOT-123 §5 (which reported per day-family; this is the
per-year pooling of the same intervals) and confirm its reading: the measured
curve needs \$500 to reach 1.00 while the model's coal stack is fully offered at
**mult 1.562 ≈ \$32.3** (§3). The tail above \$35 is **0.0504 / 0.0531** — and it
is the *only* year-stable statistic in this measurement.

**Dropping two of twenty-six resources moves the saturation point from \$500 to
\$35.** Ex-owner-split, the residual over-offering is **1.8 pp at \$35, 1.1 pp at
\$60, 0.17 pp at \$100** — against 5.2 pp / 4.6 pp / 3.6 pp with them in.

## 2. Why those two resources are not a class behaviour — the coverage receipts

Per-band shares with the artifact's `coverage` (share of fleet `HSL` held by
resources contributing any MW to the band) and top-1 concentration:

| year | band | share of HASL | **coverage** | n res | top-1 |
|---|---|---|---|---|---|
| 2024 | (\$35,\$60] | 0.0062 | **0.106** | 3 | 0.50 |
| 2024 | (\$60,\$100] | 0.0094 | **0.646** | 16 | 0.24 |
| 2024 | (\$100,\$150] | **0.0262** | **0.045** | 2 | 0.59 |
| 2024 | (\$150,\$500] | **0.0086** | **0.045** | 2 | 0.66 |
| 2025 | (\$35,\$60] | 0.0096 | **0.055** | 3 | 0.83 |
| 2025 | (\$60,\$100] | 0.0060 | **0.669** | 13 | 0.46 |
| 2025 | (\$100,\$150] | **0.0363** | **0.108** | 3 | 0.49 |
| 2025 | (\$150,\$500] | 0.0012 | 0.047 | 2 | 0.56 |

**The band carrying most of the tail's MW carries the least of the fleet.** The
\$100+ layer is 3.48 pp (2024) / 3.75 pp (2025) of HASL on **4.5 % / 10.8 % of
fleet capacity**. Adopting it class-wide — giving Martin Lake, Limestone, Oak
Grove, W A Parish, Coleto Creek, J K Spruce and Sandy Creek a \$114–150 rung when
their measured median-day top-of-curve is \$19–27 — is **precisely the
substitution ERCOT-122 §1 refuted** in the pooled `COAL_LIGNITE econ_high` 2.856
(a 21–47 %-coverage subsample imported as if it described the class). This lane
was chartered with the explicit warning "your tail must not become that mistake";
on the numbers, a class-wide adoption would be a *worse* instance of it.

**What the two resources are.** The per-resource capacities are internally
decisive without any external source: `FPPYD1_FPP_G1_J01` 300.5 MW +
`FPPYD1_FPP_G1_J02` 308.0 MW ≈ 608 MW; `FPPYD1_FPP_G2_J01` 297.7 MW +
`FPPYD1_FPP_G2_J02` 308.0 MW ≈ 606 MW; `FPPYD2_FPP_G3` 435 MW — summing to
1,649 MW against the model's single Fayette Power Project plant (code 6179) at
**1,690 MW**. The `_J01` / `_J02` pairs are two registered ownership shares of
**the same two physical units**, and units 1–2 are the jointly-owned pair while
unit 3 is single-owner. Their measured median-day top-of-curve, 2024 → 2025:

| resource | 2024 | 2025 |
|---|---|---|
| `FPPYD1_FPP_G1_J01` | \$18.74 | \$17.35 |
| `FPPYD1_FPP_G2_J01` | \$18.41 | \$16.24 |
| `FPPYD2_FPP_G3` | \$19.66 | \$17.52 |
| **`FPPYD1_FPP_G1_J02`** | **\$150.10** | **\$116.00** |
| **`FPPYD1_FPP_G2_J02`** | **\$150.10** | **\$113.15** |

An 8× offer spread between two shares of one machine is not a heat rate, a fuel
cost or a class conduct — it is one owner's disposition of its share, persistent
on the typical day and corroborated on a second instrument in a third year
(ERCOT-122 §1 measured `FPPYD1_FPP_G1_J02` at \$114.00 in the 2023 **DAM**
disclosure). *(That the joint owners of Fayette 1–2 are known to hold divergent
positions on running the plant is consistent with this and is the obvious
explanation; the disclosure carries no ownership field, so the attribution is an
inference from the capacity arithmetic and the offer split, not a measured
fact.)* **The model fleet has no owner-share dimension at all** — Fayette is one
1,690 MW plant — so there is nothing in the model's coal representation for this
conduct to re-shape.

## 3. Rule 19 `[R-ONE-MECH]` enumeration — what already shapes or caps coal

Read from the keeper's `run_config.json`, `legitimacy_diagnostics.json` and
`data/raw/reference/custom-bin-assignments.csv`:

| # | mechanism | live value in the keeper | what it moves |
|---|---|---|---|
| 1 | `COAL_PRB` / `COAL_LIGNITE` class bands (`backcast_config` `_ERCOT`) | PRB {committed 0.95, econ_low 0.70, econ_high 0.94, **peak 1.48**, econ_low_share 0.556}; LIGNITE {0.95, 1.14, 1.15, **peak 1.55**, 0.556} | the whole curve height |
| 2 | keeper `offer_curve_deltas` | PRB {committed −0.04, econ_low −0.30, econ_high **+0.44**, **peak +0.082**}; LIGNITE {committed −0.07, econ_low +0.076, econ_high −0.037, **no peak delta**} | ⇒ live peaks **PRB 1.562**, **LIGNITE 1.55** |
| 3 | `coal_econ_marginal_hr_bound=True` | the ercot115 keeper delta | bounds the econ band's marginal HR |
| 4 | `Pct_Peaking` in the bin sheet | **5.0 % for every coal plant** (698 MW of 13,963.9 MW); no coal curve carries `pct_peaking`, so the sheet governs | the peak band's **capacity** |
| 5 | take-or-pay + passthrough sigmoids | `coal_take_or_pay_tranches` (0.30/0.25/0.45 fracs at 0.00/0.35/1.00 passthrough), `coal_prb_passthrough_sigmoid` floor 0.76, `coal_lignite_passthrough_sigmoid` floor 0.675 / ceil 1.0, `coal_prb_passthrough_tiered`, `coal_plant_monthly_pricing` | the **fuel term** every band multiplies |
| 6 | ERCOT-116 availability envelope | `ercot_thermal_dam_availability` + `_hourly` + `_plant` | how much coal is offered **at all** per hour |
| 7 | `coal_mustrun_per_plant=True`, `commitment_screen_coal=True`, `coal_drop_pof=True` | per-plant must-run tranche | the **bottom** of the curve (ERCOT-117 §5.3's lane, not this one) |
| 8 | **D-2 forced-energy attribution** | **no COAL row in any of 2023/2024/2025** | **the keeper forces ZERO coal energy** |

**The enumeration's verdict on mechanism *form* is a PASS.** #8 is the key
result: no floor, bridge or CHP limb touches coal, so a peak-band re-shape would
stack on nothing. And a clean re-shape channel already exists — `peak_ladder`
(`[[capacity_share, multiplier], …]`, `assembly.py:866-899`) splits the existing
peak band into rungs at fixed capacity without adding a limb or changing the
band's MW. Item #4 pins that MW at 5.0 % of nameplate.

**The lane fails on mechanism *content*, not form.** The channel is available and
would be legitimate; what cannot be put into it is a fleet-representative tail.

## 4. Direction, sizing and identification — checked ex ante, as the charter required

**Direction (charter task 3), stated before any solve and confirmed by
arithmetic.** A dearer top removes coal from merit in the \$35–\$500 clearing
band, so coal energy **falls**, the C8 forced share **falls or holds** (it forces
nothing — §3 #8), and prices in those hours **rise**. The re-shape is
capacity-preserving: it changes *when* the peak band clears, not how much of it
exists. The sign is the one the lane wants; there is no ERCOT-122-style inversion
here.

**Sizing of the class-representative residual, labelled a hand calculation.** The
ex-owner-split tail is **1.6–1.8 pp of online HASL** — ~150–170 MW at the
9.1–9.6 GW interval-mean online coal HASL this instrument measures, i.e. about a
**quarter of the existing 698 MW peak band**, to be lifted from mult 1.562 into
[1.692, 4.835] (\$35–\$100 on the 2024–2025 delivered-PRB basis). Over the
12.5 % (2024) / 25.5 % (2025) of full-year hours clearing in [\$35, \$100) that is
**0.18 / 0.36 TWh** — **0.31 % / 0.59 %** of the keeper's modelled coal
(57.3 / 60.3 TWh) and **1.4–5.3 %** of the ERCOT-116 envelope's
+6.8/+9.2/+12.9 TWh. *(With the owner-share block left in, the figure is
0.6–1.2 TWh, reproducing the charter's own 0.6–1.6 TWh order of magnitude — which
was computed before the block was isolated.)*

**Identification fails on both available tests.**

*Band-level LOYO, on the only two years the instrument covers* — every
constituent band swings ~2× while only the total is stable:

| band (ex_owner_split) | 2024 | 2025 | ratio |
|---|---|---|---|
| (\$35,\$60] | 0.0065 | 0.0101 | 1.55× |
| (\$60,\$100] | 0.0098 | 0.0046 | 2.13× |
| total > \$35 | 0.0163 | 0.0159 | 1.03× |

Only the aggregate is identified; its composition — which is what a ladder must
specify — is not. Per-resource it is worse: `LEG_LEG_G1` \$78.00 → \$23.44,
`WAP_WAP_G5` \$76.50 → \$25.39, and `CALAVERS_JKS1`/`JKS2` swap places
(\$47.73/\$20.02 → \$18.79/\$75.03) between adjacent years. The cap-weighted q90
of the per-resource typical top-of-curve moves \$76.65 → \$51.61 while q10–q70
move < \$0.7. Stability tracks coverage exactly, as ERCOT-122 §2 found.

*The 2023 extrapolation — the charter's named central risk — has no supporting
instrument and one contradicting one.* No 2023 SCED exists. The **DAM**
disclosure, the only instrument spanning 2023, gives a coal tail above \$35 of
**3.87 pp (2023) → 1.14 pp (2024) → 0.13 pp (2025)** of HSL — a 31× collapse,
directly contradicting the RT tail's 5.04 → 5.31 pp flatness (committed as
`_dam_cross_instrument` in the artifact, identical band construction). Both
readings cannot be right, and the DAM series is the low-coverage instrument
ERCOT-122 declined to adopt for exactly this reason. Either way the conclusion for a G6
LOYO gate is the same: **the 2023 leg would be unidentified before a single hour
was solved**, and a 2023-only LOYO failure is a FAIL by the charter's own terms.

**Two risks the charter flagged did NOT materialise, and are recorded as clean.**
*(i) Hour-of-day sampling.* Three of four subsets cover hours 11–22 only; measured
on the one all-24-hour subset the tail above \$35 is **0.0542 in h11–22 against
0.0583 in h23–h10** — larger overnight, so the daytime sampling does not inflate
it. *(ii) Probe-day representativeness.* ERCOT-123 §6(ii) bounded it at ≤ 0.010 on
the reach statistic over these same days.

## 5. Recommendation — recommend-and-STOP (keeper untouched; owner decides)

1. **Phase 2 is NOT run.** Three independent grounds, any one of which is
   sufficient: **(a)** 68–71 % of the tail's MW is one plant's second-owner share
   at 4.5–10.8 % capacity coverage — adopting it class-wide repeats the ERCOT-122
   `econ_high` error the charter forbade in its own text; **(b)** the conduct has
   no representation in the model to re-shape (Fayette is one plant, no
   owner-share dimension), so expressing it needs a **new per-plant offer-height
   channel**, which is a new mechanism, not a re-shape of the `COAL_PRB` `peak`
   band — the charter's stated stop condition; **(c)** the class-representative
   residual is 1.6–1.8 pp / 0.18–0.36 TWh (0.3–0.6 % of modelled coal), with
   band-level composition unidentified even in-sample and the 2023 leg
   unidentified entirely. Rule 21 `[R-DOF]`: a quantity that can only be fixed by
   choosing a value is an open root-cause issue, not a parameter.
2. **The model's coal offer curve is CORRECT to within 1.6 pp of capability, and
   this should be recorded as a positive result, not a deferred defect.** Read
   ex-owner-split, the measured class saturates at \$35 and the model saturates at
   \$32.3 — a 0.13 gap in hr-mult units. Together with ERCOT-123 (reach ≈ 100 %,
   correctly) and ERCOT-122 (level flat at \$20.5–21.8, matched below \$25), the
   coal **offer surface** is now measured on both instruments across every moment
   of its distribution and is not where the ERCOT-116 over-run lives. **The coal
   offer-curve lane as a whole should be closed**; the remaining coal lanes
   (ERCOT-117 §5.3's price-taking base, the ERCOT-116/121 availability envelope)
   are not offer-curve questions.
3. **If the owner wants the owner-share conduct represented, it is a new lane.**
   The honest form is a per-plant (strictly, per-registered-share) coal offer-height
   channel — a registered, ERCOT-scoped, default-off artifact in the sanctioned
   per-plant style (`thermal_tranches_<ISO>.csv`, `cc_duct_peaking_pct`), *not* a
   class band. It is worth ~0.4–0.8 TWh/yr, it is stable across three years and two
   instruments, and it would be the first mechanism in the model to represent
   ownership-driven withholding at a jointly-owned unit. That is a real market
   structure (rule 1 `[R-STRUCT]`) and a defensible successor charter — but it is
   **not** what ERCOT-124 was chartered to build, and it inherits a live question
   (whether a *forecast* year can regenerate an owner-specific disposition, rule
   13 `[R-MEASURED]`'s forward test) that must be settled before it is built.
4. **The derived artifact stands as the committed measured record.**
   `data/raw/_validation-source/offer_curve_sced_coal_uppertail.json` — nothing
   reads it; no `ScenarioConfig` field, cache-key surface or solve path was
   touched. Its `coverage` / `top1_concentration` fields are the receipts that
   made §2 possible and should be read before any future adoption.
5. **Three inherited owner decisions, surfaced once and NOT decided here.**
   (a) Whether to run the ERCOT-122 offer-**level** arm as a registered controlled
   refutation for the record — ERCOT-122 recommended against, ERCOT-123 §5
   strengthened that, and **this session strengthens it again from a third angle**:
   ex-owner-split the model already matches the measured curve to 1.6 pp over its
   *whole* range, not just below \$25. It remains one `replay_keeper` away, a
   separate bundle, with DIAGNOSIS-ercot122 §5.1 as its pre-commit.
   (b) The **committed-band data gap** — `Min Gen Cost` exists in the SCED
   disclosure (populated on 29–31 % of online coal resource-intervals) but is the
   RT instrument on 82 probe days, not the DAM committed band. Flagged as
   existing; **not** fetched, transformed or approximated here.
   (c) Whether the **December-2025 SCED schema revision** warrants a data-intake
   lane to re-fetch the affected days under the new layout, or whether dropping
   them stands. This session inherits the drop unchanged (§6).
6. **ERCOT-120 and ERCOT-117 §5.3 remain separate, un-renumbered lanes**,
   unaffected by this session.

## 6. Scope, closed items honoured, environment

No year solved, no run registered, no arm built;
`frontend/data/backcast/keepers/ERCOT.json` untouched. The session's diff against
`origin/main` is **three new files** — the derive script, its artifact, and this
diagnosis — plus the calibration-log entry. No `ScenarioConfig` field, cache-key
surface, solve path or existing artifact was touched, so no config pin moved and
no existing run can change. `scripts/data/derive_dam_offer_hrmults.py` is
**imported but not modified**, so the committed CC (`..._ep_yearly.json`) and coal
(`..._coal_yearly.json`) artifacts are byte-identical and no re-derivation was
needed.

Rule 23 `[R-FROZEN-DERIVE]` honoured: every quantity is read from the raw
disclosure against the charter's measurement question; the price edges were fixed
from the measured distribution's own plateaus and jump (docstring, "How the price
edges were chosen") **before** any model quantity was read; no residual entered
any derivation and no edge was chosen because it moved one. Rule 22
`[R-HOLDOUT]`: the SCED subsets are 2024–2025 and the DAM cross-check is
2023–2025 — all in-window; no 2022-or-earlier data was read and no LP ran. No
GitHub Actions workflow was added.

**Data contract.** The December-2025 SCED schema revision (ERCOT-123 §7.5) is
inherited unchanged: the reused `load_sced()` coalesces the two
`Telemetered Net Output` spellings and **explicitly drops** the intervals with no
`HASL` (15,146 of 85,694 and 17,387 of 87,792 online rows on the two affected
2025 subsets), recorded per subset in the artifact's `_provenance.load_coverage`.

Closed lists honoured: the coal offer-**REACH** question and all four ERCOT-123
buckets — reach is settled and the model's ~100 % coal reach is correct, and
nothing here reopens it; the coal offer-**LEVEL** lane and the pooled `econ_high`
2.856 (ERCOT-122 §1/§3) — §1 and §5.2 independently *confirm* that refutation
across the whole range; the EP-rebasis lane as a C3c fix and the
peak-p50/quantile-ladder legs (ERCOT-119); age/temp coal derates (ERCOT-121 §1a);
the pooled HH-0.50 artifacts; `ercot_zonal_gas_basis` ablations; the
West/Panhandle topology split. The wtx Panhandle stack and CC offer-dispersion
lanes were not touched.

**Sampling bound, carried on every number above.** 82 probe days, 2024–2025 only.
Nothing here is an annual statistic; the two TWh figures in §4 are explicitly
labelled hand calculations pairing a probe-day supply share with a full-year hour
count, and are not computed inside the derive script.

**Test state (reported, not chased, pins untouched):**
`tests/regression/test_persisted_identity.py` **passes 11/11** in this session's
container. The ERCOT-122/123 sessions recorded it failing 2/9 on clean
`origin/main`; that state no longer reproduces here. Either way this session
touches no `src/` code, config surface or cache key — its diff is one new script,
one new artifact and one new doc — so no test outcome is attributable to it.
