# FINDING — miso-141: the flat summer derate IS the nameplate→net-summer gap, re-applied to a base that already is net-summer — a ~5.8 GW double count confirmed on measured evidence, with NO existing mechanism that can repair it

**Session:** miso-141, 2026-08-07, branch `claude/miso-141-summer-derate-qeynwi`.
Charter lane: §5.4 **QUEUE ITEM 2** (queue head since miso-140) — the flat summer
capacity haircut vs the net-summer `pmax` basis, rule 14 `[R-ACCURATE]`.

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER SET. NOTHING WRITTEN UNDER
`data/raw/`.** MISO keeper unchanged at **`2026-08-05-miso-132b-cc-committed`**
(bundle `results/calibration/miso132_ccmin_B`).

**PREREG** `results/calibration/PREREG-miso141-summer-derate-basis-2026-08-07.md`,
pushed at **`15de62ea`** BEFORE any adjudicating statistic, with a two-sided
prior carrying **seven falsifiable numeric predictions**, five look-alike traps
each with a pre-committed counter-measurement, and the decisive test (G-3b)
specified so that it does **not depend on provenance at all**.

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level miss.
No C7 lane chartered, no C7 ledger sought.

**NOT A LEVER, and nothing here is offered as one.** No C3a number appears in
this finding as evidence for or against the repair, in either direction.

---

## 1. Headline

**The double count is CONFIRMED, and it is bigger than the charter's framing
implied — but the repair does not exist.** Three results:

1. **The object is identified and the basis is measured.** MISO's gas `pmax`
   **is** the EIA-860 net-summer rating — **100.0 %** of matched class capacity
   for CT_PEAKER, CT_CHP and CC_CHP, and 83.6 % for CC_REGULAR (the residual
   being EIA-860's own invalid filings, §4). On top of it the model removes a
   further flat **10 % (CC) / 12.5 % (CT)**, which is **the same size as the
   nameplate→summer gap already embedded in that base**: measured clean, CC_REGULAR
   **11.40 %**, CC_CHP **14.34 %**, CT_PEAKER **16.35 %**, CT_CHP **15.25 %**.
2. **The alternative reading is refuted without appeal to provenance.** If the
   flat derate were an *incremental* loss below the net-summer rating point, its
   honest magnitude at MISO's **own** measured slopes is **−1.9 to −2.0 % (CC)**
   and **−3.6 to −3.8 % (CT)** — **negative, i.e. an UPRATE**, because in
   **18 of 18** zone-years the mean summer hour sits **8.3–11.9 °C BELOW** the
   summer-peak condition the rating is set at. The flat derate is **3.3–5.2×**
   too large **and points the wrong way**.
3. **No existing mechanism repairs it.** `cc_nameplate_summer_derate` reaches
   only the CC half — **~52 %** of the affected MW — and it is **not a basis
   swap**: on a `outage_source="historic"` keeper it *also* drops the
   statistical POF and the age/performance derate for CC, and MISO's
   `wefor_residual` is `None`, so arming it changes **four** things at once
   (rule 19 `[R-ONE-MECH]`). The CT half — **2,824–2,841 MW/yr** — has **no
   mechanism at all**.

**Scale:** the flat derate removes **5,933 / 5,853 / 5,686 MW** of summer
h12–17 capability (2023 / 2024 / 2025). Against miso-139 §7's own cushion
(13,720–18,828 MW) that is **2.4–3.2×** inside — so it still cannot reach the
marginal unit, and the "not a lever" verdict **holds**. But it is **~12×** the
ambient-derate family's 456–497 MW reach, i.e. an order of magnitude closer to
consequential than the family miso-139 closed. *That margin is 2.4×, not 30×,
and the next session should not treat it as the same kind of "safely inside".*

**MISO is the only ISO in this position.** Measured across every committed
bundle: `plant_level_fleet=True` **and** `cc_nameplate_summer_derate=False` is
**MISO alone (34/34 bundles)**. CAISO (20/20), NYISO (18/18), NEISO (9/9) and
PJM (6/6) all run the flag ON; ERCOT is off but is **not** in the same class —
its fleet is not plant-level (CAMPD-bin `Nameplate_MW` basis), so its flat
derate sits on nameplate and is not a double count.

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **G-1** provenance (gating for interpretation) | **P-A *and* P-C jointly.** No derivation artifact exists; the committed record identifies the object as the **nameplate→net-summer gap** in three independent places. Instrument limit disclosed (§3). |
| **G-2** basis, per unit (GATING) | **CONFIRMED net-summer.** 100.0 % for CT_PEAKER / CT_CHP / CC_CHP (bar ≥95 %); CC_REGULAR 83.6 %, below the bar for a **measured and explained** reason. The nameplate counter-branch did **not** fire. §4 |
| **G-3** magnitude (GATING for size) | **MATERIAL**, far above the 2 % bar: **11.11 % (CC) / 14.29 % (CT)** of the class's own summer capability. §5 |
| **G-3b** the decisive test | **P-B REFUTED ON BOTH LEGS** — magnitude 3.3–5.2× over the 3× bar, and the sign is inverted in 18/18 zone-years. §6 |
| **G-4** reach (diagnostic) | **5.7–5.9 GW** restored vs a **13.7–18.8 GW** cushion = **2.4–3.2×**. Still inside; still not a lever. §7 |
| **G-5** treatment consistency (diagnostic) | **MISO is the sole plant-level ISO with the flag off**, 34/34 bundles. §8 |

**Stop rules honoured as written.** PREREG §6: *"P6 confirmed (no single field
covers all four classes) ⇒ NO ARM, NO SOLVE."* P6 **is** confirmed (§9), so no
arm was built and no solve was spent. The G-2 counter-branch (basis is
nameplate), which would have killed the charter outright, was checked **first**
and did not fire.

---

## 3. G-1 — provenance, and the limit of the instrument

**No derivation artifact exists at HEAD**, by search rather than by assumption
(*an absence claim is a measurement*, miso-136): no derive script produces the
pair (the nine `.py` files naming it are all **consumers** — six `*_tempderate_ab`
A/B probes, `_miso139_derate_gates.py`, and `derive_ercot_rtolcap_forward.py`),
and `docs/parameter-citations.md:895-896` carries it tagged
**`needs-citation, modeled`**.

**And the record identifies the OBJECT, in three independent places:**

* `config/fuel_trajectories.py:934-949` — *"The SPECIFIC magnitudes 0.10 / 0.125
  are an **UNCITED FLAT APPROXIMATION** … consistent with, but not derived from,
  the 10-30 % typical CT summer derate the repo's own capacity audit records
  **against EIA-860 net-summer ratings**."*
* `docs/capacity-audit-860-923-campd.md:134` — frames it as the model's handling
  of *"105 plants where the CT/ST summer capacity is **below nameplate**"*.
* `docs/cc-high-cf-investigation.md:267-275` (2026-06-24) — names the defect in
  terms: *"`_SUMMER_CLASS_DERATE` (a flat 10 %) again in the summer months — **a
  second summer derate on a number that was *already* the summer rating**"*.
* `docs/handoffs/miso-94-…-charter-2026-07.md` §1 — *"`SUMMER_WEFOR_SHARE` /
  `SUMMER_CLASS_DERATE` — **no derivation of any kind exists**; nothing to cite."*

So **G-1 returns P-A** (the object is the nameplate→summer gap) **and P-C** (no
derivation) together. Under the pre-registered map, applying it to a net-summer
base is a double count **on provenance**.

**MISO's exclusion is a recorded deferral, not an oversight, and not a finding
that its treatment is right.** Commit `4fb54b53` (2026-07-14, *"Unify CC capacity
into one measured-capability stack (cross-ISO)"*) states: *"A.4.2 coverage:
derive CAISO/NYISO/NEISO tables so every ISO is on the same measured stack;
ERCOT (CAMPD-bin basis) and **MISO (cap-only static keeper) left as-is**."*

**THE INSTRUMENT'S LIMIT, DISCLOSED RATHER THAN PAPERED OVER.** The git-history
leg of G-1 is **not fully measurable here**: this clone is **SHALLOW** (12
grafts; `git rev-list --count` returns **1** at the boundary commit), so
`git log -S` reports every file as "added" at the graft and can see nothing
earlier — a null result from it would be an artifact, not evidence. The GitHub
API path reaches back only to **2026-06-27** within one 100-commit page, and the
constant predates that. **So this finding does NOT claim "no commit ever derived
it."** What is certified is: no derivation artifact exists on disk at HEAD, and
the repo's own governance audit (miso-94) independently recorded the same. *A
correction is not verified by the commit that makes it, and the instrument that
checks it needs checking too* (miso-140b).

---

## 4. G-2 — the basis, measured per unit

Built through the model's own loader (`load_fleet_from_csv` →
`generators_to_fleet_arrays` → `_availability_matrix`, the miso-139
construction), joined unit-by-unit to the committed EIA-860 Generator_Y Operable
sheet. Share of each class's **matched** LP capacity lying within 1 % of each
basis (identical in all three years):

| class | n units | LP `pmax` MW | matched | **= net-summer** | = nameplate |
|---|---:|---:|---:|---:|---:|
| **CT_PEAKER** | 516 | 22,289 | 100.0 % | **100.0 %** | 7.2 % |
| **CT_CHP** | 96 | 2,626 | 100.0 % | **100.0 %** | 5.8 % |
| **CC_CHP** | 86 | 7,286 | 100.0 % | **100.0 %** | 14.7 % |
| **CC_REGULAR** | 160 | 27,410 | 89.4 % | **83.6 %** | 21.2 % |
| *ST_GAS / ST_CHP / COAL (controls)* | 39 / 98 / 109 | 10,991 / 1,932 / 42,800 | 100.0 % | 100.0 % | 3.0 / 23.6 / 3.9 % |

*(The two columns overlap because a flat-rated unit satisfies both.)*

**Three of four classes clear the pre-registered ≥95 % bar outright.
CC_REGULAR does not, and the reason is measured, not assumed.** Its aggregate
`net_summer / nameplate` reads **1.0138** — the registered SUMMER rating **above
nameplate**, which EIA-860's own schema forbids. That is the component/total
double-filing pattern `2541f647` (pjm-110 leg A) already diagnosed and which
`fleet.cc_summer_capacity` clamps (`ns_sum = min(ns_sum, np_sum)`); the loader
prints its own reconciliation for 7 plants at build time.

**A contaminated aggregate is not a measurement, and the pre-registered
instrument check is what caught it.** Split into CLEAN (`ns ≤ np`) and CORRUPT
(`ns > np`) rows:

| class | rows | corrupt | corrupt % | all `ns/np` | **CLEAN `ns/np`** | **CLEAN gap %** | unit-p50 gap % |
|---|---:|---:|---:|---:|---:|---:|---:|
| CC_REGULAR | 139 | 20 | 14.4 % | *1.0138* | **0.8860** | **11.40** | 12.19 |
| CC_CHP | 86 | 16 | 18.6 % | 0.8934 | **0.8566** | **14.34** | 13.22 |
| CT_PEAKER | 516 | 21 | 4.1 % | 0.8459 | **0.8365** | **16.35** | 8.88 |
| CT_CHP | 96 | 2 | 2.1 % | 0.8495 | **0.8475** | **15.25** | 8.82 |

The 20 corrupt CC_REGULAR rows (12 plants, incl. 55380, 55467, 55620) file
**3,962 MW of nameplate against 6,814 MW of net-summer**. **Recorded against
interest:** on the contaminated aggregate I would have reported *"MISO CC has no
nameplate→summer gap at all"* — a striking claim, and **wrong**. The clean
subset puts CC_REGULAR's gap at **11.40 %**, in line with every other class.

---

## 5. G-3 — the magnitude, and Trap 3 discharged

Trap 3 (rule 19 `[R-ONE-MECH]`) required separating the flat derate from every
other summer term before attributing anything to it. The summer capability stack
was rebuilt with `SUMMER_CLASS_DERATE` zeroed **in place** (the private alias in
`arrays.py` is the same object, so this reaches the real read site; restored in a
`finally`), leaving `THERMAL_AVAILABILITY`, `SUMMER_WEFOR_SHARE = 0.30`, the
mean-anchored `temp_dependent_derate` overlay, the CAMPD outage overlay and
`BIN_FORCED_DERATE_BY_YEAR` all live and unchanged:

| yr | class | flat | summer avail | no-flat | **stack / net-summer** | **stack / nameplate** | **excess %** | **h12–17 removal MW** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | CT_PEAKER | 0.125 | 0.7974 | 0.9113 | 0.7974 | **0.6745** | **14.29** | **2,538** |
| 2024 | CT_PEAKER | 0.125 | 0.7968 | 0.9107 | 0.7968 | **0.6741** | 14.29 | 2,536 |
| 2025 | CT_PEAKER | 0.125 | 0.7923 | 0.9055 | 0.7923 | **0.6703** | 14.29 | 2,522 |
| 2023 | CC_REGULAR | 0.100 | 0.7949 | 0.8833 | 0.8314 | 0.8429 | **11.11** | **2,420** |
| 2024 | CC_REGULAR | 0.100 | 0.7657 | 0.8508 | 0.8009 | 0.8119 | 11.11 | 2,331 |
| 2025 | CC_REGULAR | 0.100 | 0.7275 | 0.8083 | 0.7609 | 0.7714 | 11.11 | 2,215 |
| 2023–25 | CC_CHP | 0.100 | 0.80–0.84 | 0.89–0.94 | 0.80–0.84 | 0.71–0.75 | 11.11 | 647–683 |
| 2023–25 | CT_CHP | 0.125 | 0.81 | 0.93 | 0.81 | 0.69 | 14.29 | 302–304 |

**The excess is exactly `d/(1−d)`** — 11.11 % and 14.29 % of the class's own
summer capability, an order of magnitude above the 2 % materiality bar. **P4
confirmed.**

**The clearest single number is CT_PEAKER against nameplate.** EIA-860 rates the
clean fleet's summer capability at **83.65 %** of nameplate. The model's stacked
summer availability sits at **67.0–67.5 %**. It removes the registered
**16.35 %** ambient gap *inside the base*, and then **12.5 %** more on top.

---

## 6. G-3b — the decisive test, and it needs no provenance

**(ii) SIGN — 18 of 18 zone-years.** The mean summer hour is **cooler** than the
p99 summer-peak condition an EIA net-summer rating is set at, by **−8.34 to
−11.85 °C** (measured on the same `iso_zone_hourly_drybulb` series the LP
consumes; year means −10.58 / −10.04 / −10.14 °C). **P7 confirmed — predicted
≥90 %, measured 100 %.**

**(i) MAGNITUDE.** At MISO's **own** committed slopes (miso-139 G-1: CT
0.00363/°C, CC 0.00192/°C — read, not re-derived), the implied incremental
below the rating point is:

| class | slope /°C | **implied incremental** | flat derate | **\|ratio\|** |
|---|---:|---:|---:|---:|
| CT_PEAKER / CT_CHP | 0.00363 | **−0.0364 … −0.0384** (an **uprate**) | 0.125 | **3.25–3.43×** |
| CC_REGULAR / CC_CHP | 0.00192 | **−0.0193 … −0.0203** (an **uprate**) | 0.100 | **4.92–5.19×** |

**Both legs refute P-B.** The magnitude clears the pre-registered 3× bar in every
class-year, *and* the sign is inverted: an honest incremental-below-net-summer
treatment for MISO would **add** ~2 % (CC) / ~3.7 % (CT) of capability in the
average summer hour, not remove 10–12.5 %.

**This is the load-bearing result**, because it is independent of what the git
history can or cannot show. Even if a derivation for 0.10/0.125 were found
tomorrow describing them as an incremental ambient loss, the numbers refuse that
reading on MISO's own fleet and MISO's own weather.

---

## 7. G-4 — reach, and an honest correction to my own prior

**Restored summer h12–17 capability (mean MW):**

| year | CC (REGULAR+CHP) | CT (PEAKER+CHP) | **total** | **cushion (miso-139 basis)** | **ratio** |
|---|---:|---:|---:|---:|---:|
| 2023 | 3,092 | 2,841 | **5,933** | **17,544** | **2.96×** |
| 2024 | 3,014 | 2,839 | **5,853** | **18,828** | **3.22×** |
| 2025 | 2,862 | 2,824 | **5,686** | **13,720** | **2.41×** |

**The cushion reproduces miso-139 §7 to the megawatt in all three years**
(17,544 / 18,828 / 13,720), rebuilt independently from the keeper's own
committed `hourly/class_hourly_<year>.parquet` — a three-for-three verification
of the construction. On the wider basis that also counts the two CHP classes'
idle headroom (both carry the flat derate), the cushion is 22,152 / 23,582 /
18,364 MW and the ratio 3.2–4.0×.

**A construction bug caught by its own cross-check, reported.** The first cushion
run read **48.6–51.5 GW** because the sidecar splits coal into
`COAL_BIT`/`COAL_LIGNITE`/`COAL_PRB` while the model's `plant_group` is the bare
`COAL`: the unmapped lookup silently returned **zero dispatch** and handed coal's
entire ~32 GW capability back as phantom headroom. It was caught because the
number disagreed with miso-139's committed prior, and the fix is an explicit
alias map **plus an assertion** that fails loudly on any unmapped class. *A gate
that can fail for a reason outside the thing it is gating must be able to tell
the two apart before its verdict is quotable* (miso-140b).

**DIAGNOSTIC, NOT LICENSING, and the sign was disclosed in advance.** This repair
**adds** capability, so its price effect is **downward** — the wrong direction
for a model already −14.1 % low in 2025. No C3a claim attaches, and none is made.

---

## 8. G-5 — MISO is alone, measured

`cc_nameplate_summer_derate` × `plant_level_fleet` across **every** committed
bundle's `run_config.json` (a READ only; rule 25 `[R-ISO-SCOPE]` — no parameter
transferred into MISO, no other ISO's artifact written, no other ISO's cell
touched):

| ISO | `plant_level_fleet` | `cc_nameplate_summer_derate` | bundles |
|---|---|---|---:|
| CAISO | True | **True** | 20 / 20 |
| NYISO | True | **True** | 18 / 18 |
| NEISO | True | **True** | 9 / 9 |
| PJM | True | **True** | 6 / 6 |
| ERCOT | **False** | False | 19 / 19 |
| **MISO** | **True** | **False** | **34 / 34** |

**ERCOT is not a counter-example**: its fleet is the CAMPD-bin path carrying
`Nameplate_MW`, so its flat derate sits on a nameplate base and is not a double
count. **MISO is the only ISO running the EIA-860 per-plant net-summer basis with
the flat derate still on top.**

---

## 9. P6 — why nothing was armed, and why that is not timidity

**The existing flag cannot express the correction.**

* **Coverage.** `cc_nameplate_summer_derate` reaches CC_REGULAR + CC_CHP only —
  **3,092 / 3,014 / 2,862 MW of 5,933 / 5,853 / 5,686**, i.e. **50.3–52.1 %**.
  The CT half (**2,824–2,841 MW/yr**) has **no** mechanism: there is no
  `ct_nameplate_summer_derate`, and CT_PEAKER is the class with the **largest**
  measured gap (16.35 %) and the **largest** idle headroom (11.6–13.3 GW).
* **It is not a basis swap.** The MISO keeper runs `outage_source="historic"`, so
  `cc_np_derate_backcast` is True and the flag *additionally* drops the
  statistical POF and the age/performance derate for CC
  (`arrays.py:626-637`). With `wefor_residual = None` on this keeper, CC
  availability would become a bare `1 − wefor` at nameplate. That is **four
  changes in one flag** — rule 19 `[R-ONE-MECH]` forbids riding them in on a
  basis correction.
* **A half-fix is not obviously the accurate input.** Correcting CC while leaving
  CT on a doubled derate leaves two classes that compete on the same margin
  carrying **inconsistent** capacity bases. Rule 14 says keep the accurate
  input; it does not say keep half of one.
* **And the CC half interacts with §4's corrupt filings.** For the 12
  double-filed CC plants the measured ratio clamps to 1.0, so the flag's summer
  derate is inert there while its nameplate rescale is not — an interaction that
  needs its own measurement before anyone arms it.

**So the repair is a MECHANISM CHANGE (rules 19/24) and therefore an owner
decision** — the same discipline miso-139 §10(3) applied to the anchor-convention
successor. It is specified in §11 and **not built here**.

---

## 10. My prior, scored against interest

| prediction | stated | measured | verdict |
|---|---|---|---|
| **P1** G-1 returns P-C or P-A; no derivation artifact | 0.75 | **both**, P-A *and* P-C | **RIGHT** (git leg not certifiable, §3) |
| **P2** basis net-summer, ≥95 % of class capacity | 0.85 | 100.0 % in 3 of 4 classes; CC_REGULAR 83.6 % | **RIGHT in substance, MISSED the bar in one class** |
| **P3** `ns/np`: CC 0.92–0.97, CT 0.85–0.94 | 0.60 | CC **0.8860 / 0.8566**, CT **0.8365 / 0.8475** | **WRONG** — CC well below the band, CT just below it. The gap is **larger** than I predicted in every class |
| **P4** stack ≥9 % (CC) / ≥11 % (CT) below net-summer | 0.90 | **11.11 % / 14.29 %**, exactly `d/(1−d)` | **RIGHT** |
| **P5** 2.5–4.5 GW restored; 5–9× the ambient family; 3–7× inside the cushion | 0.55 | **5.69–5.93 GW**; **~12×** the family; **2.4–3.2×** inside | **WRONG in all three legs**, and consistently in the direction of **understating** it |
| **P6** no single field covers all four classes ⇒ no arm | 0.70 | confirmed, and worse than stated (§9) | **RIGHT, and under-stated** |
| **P7** sign inverted in ≥90 % of zone-years | 0.85 | **18/18** | **RIGHT** |
| net: P(arm licensed and solved) | 0.20 | no arm, no solve | **calibrated** |

**Where I was wrong, recorded.** (a) **P3 and P5 both under-shot the size of the
object** — I predicted a 3–8 % CC gap and 2.5–4.5 GW of reach; measured 11.4 %
and 5.7–5.9 GW. My prior was anchored on miso-139's summer↔winter spread, and
even while writing Trap 1 to warn against exactly that crossing I still let it
set my numeric band. **The trap caught the reporting; it did not catch the
prior.** (b) My "other side" #1 — that P-B might be right and my sign argument
too clever — lost decisively, 18/18 with a 3.3–5.2× magnitude margin. (c) My
"other side" #2 — that the CC fix might itself be a level move in disguise —
proved **right and then some**: §9 shows it is four changes, not one.

---

## 11. What this licenses — nothing armed, and one specified successor

1. **The double count is established** for all four flat-derate classes and is
   **not a lever** (2.4–3.2× inside the cushion). It must never be chartered as
   one. But the margin is **2.4×**, not miso-139's 30–39× — a materially
   different kind of "inside", and the next session should treat it as such.
2. **The successor mechanism, specified and NOT built** (rules 19/24 — an owner
   decision): a **class-agnostic net-summer basis switch** that (a) covers
   **CT_PEAKER and CT_CHP** as well as the CC classes, (b) is a **pure basis
   swap** — nameplate base + the per-plant measured `net_summer/nameplate`
   multiplier in summer — with the POF / age-derate drops kept behind their
   **own** flag rather than riding in on it, and (c) handles the §4 corrupt-filing
   plants explicitly rather than by silent clamp. `cc_nameplate_summer_derate`
   as it stands is **not** that mechanism.
3. **A data-quality item, bounded and reported**: **2.1–18.6 % of rows per class**
   file an EIA-860 summer capability **above** nameplate (CC_REGULAR: 20 rows,
   12 plants, 3,962 MW nameplate vs 6,814 MW net-summer). Already guarded at load
   (`2541f647`), so nothing is broken — but any successor that keys on
   `net_summer/nameplate` inherits it and must state its treatment.
4. **`SUMMER_CLASS_DERATE` remains uncited and is now measured to be the wrong
   object for MISO.** It stays untouched this session (rule 23
   `[R-FROZEN-DERIVE]`: it may not be re-derived against a residual, and nothing
   here is a residual). Its `docs/parameter-citations.md` row should gain this
   finding as its provenance note when the registry is next regenerated.
5. **The object still stands where miso-137 left it.** The compression is a
   PRICE defect; this is a CAPABILITY basis defect. Removing it moves capability
   the wrong way for C3a, which is precisely why it is filed as rule-14 hygiene
   and not as progress against the gap.

---

## 12. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, so there is **no run to register**
(the miso-131…140b precedent). Keeper unchanged.
**Rule 28(b) `[R-MECH-MATRIX]`** — `cc_nameplate_summer_derate` MISO **stays
`U`**: it was adjudicated as a *candidate repair* and **refused as insufficient**
(covers 52 %, bundles four changes), but **no solve was spent**, so no tested
verdict is licensed. The cell's note and `ev.M` citation record this session's
measurement, and a §5.4 queue stamp is written. **No other ISO's cell moved**
(rule 28(d)); no new `ScenarioConfig` field, so 28(c) does not fire.
**Rule 22 `[R-HOLDOUT]`** — 2023 / 2024 / 2025 only, in one pass; MISO holds no
`calibration-complete` marker in either block. No out-of-training year was read,
solved, scored or registered.
**Rule 14 `[R-ACCURATE]`** — engaged and honoured: the accurate input is named
(the per-plant measured net-summer basis), the inaccurate one is **not** reverted
to protect a number, and nothing was reverted at all because nothing was armed.
**Rule 13 `[R-MEASURED]`** — every input is a physical or registration quantity
(EIA-860 ratings, zone dry-bulb, the model's own availability matrix, the
keeper's committed dispatch sidecar), forward-reproducible; **no price, no
benchmark and no model price output entered any estimator**.
**Rules 1 / 19 / 21 / 23 / 24 / 25** — nothing sized to any residual; the
existing summer-capability treatments enumerated and reconciled, not stacked
(§5); no free parameter added; no derive script re-run; no tuning channel
created; no non-MISO parameter armed for MISO and no other ISO's artifact
written.
**Rule 27 `[R-PUSH]`** — pushed blobs verified; no existing file ≥300 lines was
rewritten from regenerated content.
**Probe hygiene (miso-140b §6)** — both probes insert the **repo root** on
`sys.path` and **assert `load_zonal_shares(...) is not None`**, even though
neither consumes per-zone demand, so the assertion cannot rot.
**Owner directive** — no C7 work.

---

## 13. The generalisable lesson — **A DERATE IS A DELTA; NAME ITS BASE OR IT IS NOT A NUMBER**

`SUMMER_CLASS_DERATE = 0.125` looks like a parameter. It is not: it is a
**difference against an unstated reference**, and the whole question of whether
it is right is the question of what that reference is. Measured against
nameplate it is roughly correct (CT's true gap is 16.35 %). Measured against the
net-summer rating it sits on, it is 3.3–5.2× too big **and inverted in sign**.
The same literal is defensible and indefensible depending on a base that appears
nowhere in its own declaration — and the declaration's "UNCITED FLAT
APPROXIMATION" note names the magnitude's source while never naming what it is a
fraction *of*.

That is also why it survived: three separate audits looked at the **value**
(is 12.5 % a plausible CT summer derate? yes) and none looked at the **base**.
The defect became visible only when the base was measured per unit — and it was
settled, finally, by a test that ignored the number's history entirely and asked
what magnitude and **sign** the physics could support on this fleet in these
hours.

*A derate, a haircut, an adder, a multiplier — every one of them is a delta.
Measure the base before arguing about the size, and check the sign before either.*

Family: miso-129 *a signature is not a cause* → miso-131 *a plant-grain signature
is not a class-grain defect* → miso-132(a) *a missing rule is not a binding one*
→ miso-133 *measure the slack, on one basis* → miso-134 *binding is not
licensing* → miso-135 *the right quantity at the wrong grain is the wrong source*
→ miso-136 *an absence claim is a measurement, not a premise* → miso-137 *a
threshold is a hypothesis, not a definition* → miso-138 *measure an
identification's ceiling where the answer is known* → miso-139 *a mechanism's
anchor is part of the mechanism; bound its reach before debating its parameter*
→ miso-140/140b *a correction is not verified by the commit that makes it, and
the instrument that checks it needs checking too* → **miso-141 *a derate is a
delta; name its base or it is not a number***.

---

**Probes** `scripts/probes/_miso141_summer_derate_basis.py`,
`scripts/probes/_miso141_cc_rows_and_cushion.py` ·
**Records** `results/calibration/_miso141_summer_derate_basis.json`,
`results/calibration/_miso141_cc_rows_and_cushion.json` ·
**PREREG** `results/calibration/PREREG-miso141-summer-derate-basis-2026-08-07.md`
@ `15de62ea`.
