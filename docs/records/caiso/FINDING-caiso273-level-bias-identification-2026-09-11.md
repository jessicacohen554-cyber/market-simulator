# FINDING — caiso-273: the CAISO price bias is a YEAR-INVARIANT ADDITIVE LEVEL OFFSET that lives in the LOW-THERMAL hours, and it is NOT an offer-curve object

**Session caiso-273, 2026-09-11. CAISO only (rule 25 `[R-ISO-SCOPE]`). ZERO LP SPENT.**
Every number below is measured from COMMITTED artifacts — the keeper bundle
`caiso271_egrid_family_span`, the 2022 rung `caiso271_egrid_family_2022`, the committed
`bench/CAISO/<year>.json.gz` parts, and `data/raw/_validation-source/caiso_offer_curve_measured.json`.
**KEEPER UNCHANGED at `2026-09-10-caiso-271-egrid-family`. Nothing armed, nothing proposed as a
fix here — this doc establishes WHAT the object is and rules out three candidate causes.**

---

## §0 — Why this exists

caiso-270/271/272 each closed a candidate for **"the 2022 failure"**, treating it as a year-scoped
object. The owner's observation on 2026-09-11 reframes it, and the reframing is correct:

> *"There's a level issue across all four years it's running hot on price."*

C3a is **+4.4 / +8.7 / +7.9 / +13.0 %** for 2023 / 2024 / 2025 / 2022 — **positive in every year.**
2022 is not a separate phenomenon that happens to fail; it is the year where a persistent bias
crosses the band. **caiso-272 decomposed 2022 only**, so the all-year object has never been measured.
This doc measures it.

## §1 — THE BIAS IS ADDITIVE AND YEAR-INVARIANT

Model load-weighted price against the committed RT load-weighted actual:

| year | model lw | RT lw | DA lw | gap $/MWh | gap % | DA−RT |
|---|--:|--:|--:|--:|--:|--:|
| 2022 | 95.47 | 84.49 | 92.14 | **+10.98** | +13.0 % | +7.65 |
| 2023 | 56.54 | 54.17 | 61.68 | **+2.37** | +4.4 % | +7.51 |
| 2024 | 37.65 | 34.65 | 37.97 | **+3.00** | +8.7 % | +3.32 |
| 2025 | 37.13 | 34.42 | 35.40 | **+2.71** | +7.9 % | +0.98 |

**Excluding 2022 the gap is an almost perfectly constant ADDER: 2.37 / 3.00 / 2.71 $/MWh,
mean +2.70, sd 0.26, CV 0.095** — across years whose price level ranges 34.4 → 54.2 $/MWh, i.e.
a 58 % swing in the base. The percentage form is **less** stable (CV 0.267). **The object is an
additive offset, not a multiplicative one.** That distinction is load-bearing: a band multiplier
is multiplicative by construction and therefore cannot be the matching instrument even in
principle.

**2022 carries +8.29 $/MWh ON TOP of that constant adder**, and that excess is a separate object
(§2).

## §2 — 2022 IS MOSTLY ONE MONTH

Monthly contribution to the 2022 annual gap (reconstructed total +11.78 $/MWh):

| month | contributes $/MWh | share of the annual gap |
|---|--:|--:|
| **December** | **+5.28** | **44.8 %** |
| February | +0.92 | 7.8 % |
| July | +0.91 | 7.8 % |
| January | +0.90 | 7.6 % |

**December 2022 alone is 44.8 % of the year's failure** — the western gas crisis month, where the
market itself cleared 238.53 $/MWh and the model cleared ~305. The monthly gap table reads
**+66.6 $/MWh for Dec-2022** against +1.4 to +12.1 for every other month of that year.

Stated against any easy reading: the fuel chain for that month is **already fully measured and
armed** — `gas_daily_shape`, `gas_hub_basis_overlay`, `gas_monthly_actuals`,
`gas_plant_monthly_fuel_pricing` are all `true` on the keeper. **Dec-2022 is not a missing-daily-gas
defect**, and a lever that only reaches December would be year-scoped, which rule 1 `[R-STRUCT]`
condition (b) refuses.

## §3 — THE BIAS LIVES IN THE LOW-THERMAL HOURS (the decisive measurement)

Per month, the price gap against CC_REGULAR's own total output and its band composition:

| 2024 month | gap $/MWh | CC_REGULAR (GWh) | deep-band share | peak-band share |
|---|--:|--:|--:|--:|
| **May** | **+10.2** | **948** (year low) | 14.7 % | 0.06 % |
| **April** | **+7.0** | **1,486** | 16.2 % | 0.25 % |
| **June** | **+7.1** | **2,516** | 16.4 % | 0.04 % |
| **March** | **+4.1** | **1,920** | 15.2 % | 0.03 % |
| July | −1.6 | **6,267** (year high) | 16.0 % | 0.02 % |
| January | −1.5 | 5,248 | 17.1 % | 0.09 % |

The same shape holds in 2023 (May: CC 941 GWh → **+10.4**; July: CC 5,933 GWh → **−3.8**) and in
2025 (April/May/June +5.6 / +4.9 / +4.7 against the year's lowest CC months).

**The model runs hot precisely where thermal generation is LIGHTEST** — the spring high-solar,
low-net-load belly. The correlation is strongly negative against CC output and it reproduces in
all three training years independently.

## §4 — THREE CANDIDATE CAUSES, RULED OUT BY MEASUREMENT

### (a) It is NOT the offer ladder's depth or its peak bands

`peak`-band share of CC_REGULAR dispatch is **≤ 0.6 % in every month of every year** (typically
0.00–0.13 %), and the deep-band (`econc04`+`econc05`) share is **flat at 14.7–19.1 % across hot and
cold months alike**. The hot months are not months in which the ladder is pushed deeper or into
its peak blocks. Whatever sets the hot-hour price, it is not the CC ladder running out of cheap
blocks.

### (b) It is NOT an offer-LEVEL object — and this extends caiso-272's refusal to a class it never measured

`data/raw/_validation-source/caiso_offer_curve_measured.json` (derived from CAISO's own OASIS
Public Bid Data, trade years 2023-2025) carries a measured band set for **CC_REGULAR and
CT_PEAKER**. Against the armed keeper config:

| class | band | measured | **armed** |
|---|---|--:|--:|
| CC_REGULAR | econ_low / econ_high / peak | 1.066 / 1.072 / 1.386 | **1.066 / 1.072 / 1.386** |
| CT_PEAKER | econ_low / econ_high / peak | 1.103 / 1.146 / 1.154 | **1.103 / 1.146 / 1.154** |

**Both classes sit EXACTLY on the measured surface.** caiso-272 refused the offer-curve channel on
CC grounds and dismissed the non-CC families on *weight* rather than measuring them; this closes
that gap — **CT_PEAKER is on its measured surface too**, so the rule-1 `[R-STRUCT]` authorized
channel is spent for both classes that have a measured basis, and resizing either would move it
*away* from CAISO's own bid data (rule 14 `[R-ACCURATE]`).

**One genuine unmeasured assumption is recorded here rather than hidden:** the armed config applies
the **CT_PEAKER** ladder (1.103 / 1.146 / 1.154) verbatim to **CT_CHP and ST_GAS**, which have no
measured band set of their own. Their marginal weight is small (caiso-272 §3: ST_GAS 0.79 % of
matched weight) so this is unlikely to carry a 2.70 $/MWh level offset, but it is an open,
untested transfer and it should be stated whenever the CT/ST tail is discussed.

> **ANNOTATION 2026-09-12 (caiso-276) — THE CONCLUSION STANDS; THIS PARAGRAPH'S *REASON* IS
> SUPERSEDED, AND ITS "open, untested transfer" IS CLOSED FOR `CT_CHP`.**
> The dismissal above is on **weight**, and it cites the wrong class: caiso-276 §5c measures
> **`CT_CHP` at 28.8 %** of the marginal load-weight in the window that carries 2022's residual
> (16.6 % over all 8,760 h), not ST_GAS's 0.79 %. Examined on the merits, the answer is
> **stronger** than the dismissal. `caiso_offer_curve_measured.json`'s
> `_provenance.classifier.contamination_note` states the CT bucket "may include the 2.9 GW OTC/RMR
> ST_GAS steamers and **priced CT_CHP**" and that "**masked ids preclude per-plant mapping**". So
> **`CT_CHP` is already inside the measured CT bucket**: applying the CT ladder to it is applying a
> measured surface to a class it was measured over — the **correct** treatment, not an ungrounded
> extrapolation — and a separate CT_CHP ladder is **structurally un-derivable** from this source,
> not merely un-derived. `caiso_offer_surface_measured_ungrounded`, which performs the merge, is
> armed on the keeper and is the correct posture.
> **ST_GAS is a different matter and also not a lever:** its own measured ladder **is** derived
> (`classifier.classes` includes it) but **not consumed**, and consuming it would make ST_GAS
> offers **more expensive** (econ_low 1.849 / 1.294 / 1.523 against the armed 1.103 / 1.102 /
> 1.140) — it **raises** price. Its `committed` band is **NaN in 2024 and 2025**, so it cannot be
> the "ONE config across EVERY scored year" rule 1 condition (b) requires. A rules-14/23 fidelity
> item for a future session, to be chartered **on the data** and never on a price residual.
> `docs/FINDING-caiso276-c3a-2022-no-admissible-lever-2026-09-12.md` §6/§8.

### (c) It is NOT the D-4 floor family

The keeper's D-4 off-window-binding diagnostic reads **21 FAIL of 39 rows**, which looks alarming
and is not the cause. Every failing row is a `chp_steam` floor on a small CHP plant, and the
totals are decisive: **0.440 TWh floored across all three years, of which 0.000 TWh is
off-window** — about 0.1 % of CAISO annual load. The rows fail on the measured-zero-share test (the
metered unit is zero ~90 % of hours while the model floors it), which is a real but trivially small
defect, not a 2.70 $/MWh price offset. *(These same rows are present in the superseded caiso-269
keeper at 20 FAIL of 29, so they are pre-existing and not attributable to the eGRID family arm.)*

## §5 — WHAT THE OBJECT THEREFORE IS

A year-invariant **additive** price offset, concentrated in **low-net-load / high-solar hours**,
that is **not** produced by the offer ladder's level, depth, peak blocks, or the floor family.

That is the same structure caiso-266 §4 identified from the other direction and left open —
1,001 / 1,222 / 1,020 hours (h6-h15, Mar-Jun weighted) in which the model is **thermal-marginal at
$29.28 / $26.04 / $26.45 with dump 0.000 MW, against a market clearing $9.40 / $6.81 / $10.39** —
and the same structure caiso-272 §3.1 found from a third direction, that λ sits **in a GAP in the
thermal offer stack in 97.4 %** of the weight its price-match instrument could not name.

**Three independent instruments, three sessions, one object: in the solar belly the model's
cheapest available marginal resource is a gas unit at ~$27, and the real market's is not a CAISO
gas unit at all.** A model whose belly floor is a thermal offer, in a market whose belly is priced
by something else, carries exactly the year-invariant additive offset §1 measures.

**No cause is asserted here and nothing is armed.** What is established is the object's shape, its
location in the clock and the calendar, and that the three cheapest explanations are refuted by
measurement. The candidate ladder, the pre-registered kill conditions and the shard plan are the
next session's charter.

## §6 — Disclosures against interest

1. **§5 is a characterisation, not a diagnosis.** It says where the bias lives and what it is not.
   It does not name the missing supply, and a session that treats it as if it had would be
   selecting a mechanism on a hunch.
2. **The DA basis does not rescue it.** Model−DA reads +3.33 / −5.14 / −0.32 / +1.73 for
   2022-2025 — it **flips sign**, so it is *less* stable than the RT gap, not more. This is
   counter-evidence to any DA-rebase reading and is consistent with caiso-272 §5.1, which must be
   carried at full magnitude wherever the DA-RT premium is quoted.
3. **2022 is two objects, not one.** The constant adder (§1) plus a Dec-2022 excess (§2). A lever
   that closes one will not close the other, and the 2022 band will not clear on the adder alone.

   > **ANNOTATION 2026-09-12 (caiso-276) — THIS DISCLOSURE IS FALSIFIED BY MEASUREMENT. 2022 IS
   > *ONE* OBJECT.** Measured on 2022's own 12 months, the implied marginal heat-rate bias
   > (load-weighted price ÷ the model's own delivered gas price, model minus the committed monthly
   > actual) is **mean +1.024 MMBtu/MWh, sd 0.642** — reproducing caiso-270 §4's cross-ISO **+1.01**
   > from a new direction — and **December's +1.337 RANKS 3 OF 12, only +0.51 sd above the
   > ex-December mean of +0.996**. The **+$49.51** December gap is that **ordinary** bias ×
   > **$37.02** gas, to the dollar. Normalising by gas halves the dispersion (raw monthly gap CV
   > **1.26** → gas-normalised CV **0.627**), so the residual scales **with** gas and cannot be a
   > non-fuel adder. §2's own reading ("Dec-2022 is not a missing-daily-gas defect", and a
   > December-only lever would be year-scoped) was right; what is withdrawn is the **two-objects**
   > framing, and with it the premise that a separate December mechanism exists to be found.
   > `docs/FINDING-caiso276-c3a-2022-no-admissible-lever-2026-09-12.md` §3/§8.
4. **The monthly gap uses a 730-hour month approximation** (`hour // 730`) against the bench's
   calendar-month actuals. That is accurate enough for a several-dollar monthly signal and the
   ranking is unambiguous, but it is not an exact calendar alignment and should not be quoted to
   the cent.
