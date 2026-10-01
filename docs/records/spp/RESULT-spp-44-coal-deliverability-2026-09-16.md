# RESULT — SPP-44 (2026-09-16): the coal-deliverability lever, adjudicated at ZERO LP

**Lane-name collision, stated up front.** An earlier lane also carried the label
SPP-44 (`FINDING-spp-44-2026-09-07.md`, the P0-anchored `spp_gas_commitment_bridge`,
killed at its STOP gate). That lane is unrelated to this one and is untouched. This
document is the 2026-09-16 lane; cite it by date.

**Base:** `d54cd9c571359b85cb1a8e1cd5cab68c080a6b0c`.
**Keeper:** `2026-09-16-spp-42-commitment-feasibility` (`spp42_span_a`) — **UNCHANGED**.
**2019–2022 rung:** `2026-09-16-spp-43-outage-intake` (`spp43_holdout_span`) — **UNCHANGED**.
**LP spent: none. Bundles produced: none. Runs registered: none. Cells armed: none.**

---

## 0. Headline

SPP's **named structural successor** — *"a coal offer markup keyed to coal
deliverability / stockpile days"*, entered as `U` by SPP-41 and recorded there as
**blocked on an EIA-923 Schedule-5 coal receipts-and-stocks intake that does not
exist on disk** — is **DEAD on measurement**.

1. **The blocker is stale.** Both datatypes landed **2026-09-14** (`data/raw/coal-receipts`
   + `data/raw/coal-stocks`, 2018–2024, with schemas, curation scripts, and readers whose
   own docstrings carry the rule-13 discipline). The *data* question is closed.
2. **The identification fails anyway.** Across six legs — lagged and same-year, fleet and
   per-plant, tonnage and sub-annual timing — **no statistic puts 2022 outside the other
   years' range**, while the MMU target has 2022 at **3.07× the maximum of every other
   year**. 2022 is in fact the **smoothest, most reliably-supplied delivery year in the
   2018–2024 record**, and the two genuinely stressed years (2020, 2024) carry the
   **lowest** markups.
3. **A second cell falls out of the same measurement.** The existing
   `coal_fuel_inventory` mechanism **would bind on SPP in 2021/2022** — but the
   physically correct cumulative constraint **never binds in any of the seven years**.
   The binding is an artifact of the row's flat `/12` form, so arming it would move the
   residual through a constraint that **is not real**. Cell moves `U` → **`R`**.

Killing a lever cleanly is a result. This one dies against the very intake it was
blocked on, which is the strongest available form of that result — and it dies **before**
a future lane spends a span arming either object.

---

## 1. The stale blocker, corrected

SPP-41 §2.6 point 4 (2026-09-14):

> *"The MMU's own named driver — coal deliverability — **would be forecast-admissible**,
> but nothing on disk reaches it: there is no coal receipts/stocks (EIA-923 Schedule-5
> tonnage) intake … That is a data-intake decision, not a modelling one."*

That was true when written and is false now. Landed 2026-09-14 (MISO lane, `miso-258`/`miso-259`):

| | |
|---|---|
| `data/raw/coal-receipts/` | EIA-923 Page 5, 2018–2024, national, with `SHA256SUMS.txt` + re-fetch recovery |
| `data/raw/coal-stocks/` | EIA-923 Page 2, 2018–2024, national |
| schemas | `data/dictionary/schema/coal-{receipts,stocks}.schema.yaml` |
| readers | `coal_receipts.prior_years_delivery_rate`, `coal_stocks.opening_stock_tons` |
| curation | `scripts/data/curate_coal_{receipts,stocks}.py` |

Both readers are **built for this question**: the curation note states that transport mode
survives "so a rail/logistics construction does too", and `coal_stocks`' module docstring
states the rule-13 trap verbatim and exists "to make the admissible read the easy one."

**Coverage of SPP's own model coal fleet is complete** — 30 of the model's 32 coal plants in
receipts and 29–30 in stocks, in **every** year 2018–2024. The data does not block this lever.
The identification does.

---

## 2. Rule 13 `[R-MEASURED]`, applied before anything was measured

Every candidate statistic is built **only from years ≤ Y-1**. That is not a formality here:
`ending[m] = ending[m-1] + receipts[m] - burn[m]` means a year's own stock path embeds the
very burn a backcast is asked to reproduce. The admissible reads are the opening stock
(the prior December's state — for a forecast year, the model's own carried-forward
inventory, the role a storage SOC boundary plays) and a delivery rate from years ≤ Y-1.

The same-year legs are computed and reported **as the forbidden comparator**, to show what
the admissible construction is giving up. They are never a candidate.

---

## 3. The target, and what the candidates do against it

SPP's MMU publishes the quantity the model sets to zero by construction — offer minus
mitigated reference cost, cleared-MW-weighted (SPP-41 §2.5):

| year | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **MMU coal markup $/MWh** | 6.02 | **21.12** | 6.88 | 4.29 | 5.81 |
| model markup | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

The MMU names the driver (ASOM 2023 fn. 194): *"Several coal resources experienced **coal
deliverability issues as a result of rail limitations**."*

### 3a. Leg B — lagged (admissible) and same-year (forbidden)

| Y | MMU $ | L:openDays | L:rec/burn | L:rail % | S:rec/burn | S:deficit Mt |
|---|---|---|---|---|---|---|
| 2021 | 6.02 | 91.3 | 0.9990 | 86.4 | 1.0033 | +0.191 |
| **2022** | **21.12** | **92.1** | **0.9988** | **87.3** | **0.9835** | **−0.982** |
| 2023 | 6.88 | 79.2 | 0.9933 | 87.7 | 1.1877 | +8.651 |
| 2024 | 4.29 | 148.7 | 1.0728 | 91.2 | 0.9419 | −2.522 |
| 2025 | 5.81 | 154.6 | 1.0685 | 97.3 | — | — |

| statistic | Spearman ρ | 2022 | other years | verdict |
|---|---|---|---|---|
| L:openDays | −0.600 (n=5) | 92.15 | [79.16, 154.56] | **INSIDE** |
| L:rec/burn | −0.900 (n=5) | 0.9988 | [0.9933, 1.0728] | **INSIDE** |
| L:rail % | −0.600 (n=5) | 87.25 | [86.38, 97.35] | **INSIDE** |
| S:rec/burn | +0.400 (n=4) | 0.9835 | [0.9419, 1.1877] | **INSIDE** |
| S:deficit | +0.400 (n=4) | −0.982 | [−2.522, +8.651] | **INSIDE** |
| **MMU target** | — | **21.12** | **[4.29, 6.88]** | **OUTSIDE, 3.07×** |

**`L:rec/burn` does rank-correlate at ρ −0.900, in the expected direction, and that is
reported honestly — but it does not identify.** The rank agreement is carried entirely by
the two *loose* years (2024, 2025 at ≈1.07) having low markups. In the three years that
matter the statistic is flat and the target is not:

> **2021 and 2022 are indistinguishable on the admissible statistic — 0.9990 vs 0.9988,
> a 0.02 % difference — and differ by 3.51× in the target ($6.02 vs $21.12). 2023 is
> *tighter* than 2022 (0.9933 < 0.9988) on a markup of $6.88.**

Any smooth monotone map from a 0.02 % input difference to a 3.51× output difference is an
essentially vertical response whose steepness is a free parameter fitted to hit 2022. That
is precisely the fitted-mechanism selection rule 1 `[R-STRUCT]` (c) forbids, and rule 21
`[R-DOF]` would book it as a residual-identified parameter. **Refused.**

### 3b. Leg C — the aggregate is not hiding a concentrated event

The MMU says "several coal resources", so a fleet aggregate could wash one out. It does not:

| year | plants | n < 0.90 | n < 0.75 | p10 | median |
|---|---|---|---|---|---|
| 2020 | 28 | 6 | 1 | 0.836 | 0.982 |
| 2021 | 28 | 6 | 0 | 0.853 | 1.002 |
| **2022** | **28** | **2** | **0** | **0.908** | 0.978 |
| 2023 | 28 | 0 | 0 | 1.014 | 1.155 |
| **2024** | **27** | **10** | **3** | **0.651** | 0.946 |

**2022 is the second-least-stressed year in the record.** Two plants under 90 % coverage,
**none** under 75 %, and the highest p10 of any year but 2023. **2024** — ten plants under
90 %, three under 75 %, p10 0.651 — is by far the most stressed, and carries the record's
**lowest** markup ($4.29). The per-plant picture inverts the hypothesis rather than rescuing it.

### 3c. Leg D — the sub-annual timing signature, and its confound

Annual tonnage could miss a *timing* failure — deliveries arriving, but not when needed:

| year | mean zero-delivery months | mean CV | plants with a ≥2-month gap |
|---|---|---|---|
| 2020 | 1.00 | 0.492 | 7 |
| 2021 | 0.37 | 0.354 | 4 |
| **2022** | **0.20** | **0.326** | **1** |
| 2023 | 0.90 | 0.438 | 5 |
| 2024 | 1.62 | 0.589 | 9 |

2022 **is** outside the other years' range on all three — **in the wrong direction**, at
ρ −0.800 each. **2022 is the smoothest, most regularly-supplied year in the entire
2018–2024 record.** Deliveries were *more* reliable in the year of the rail event than in
any other year, by every timing measure available.

**Confound ruled out, not assumed.** An annual-frequency filer fakes eleven zero-delivery
months and would manufacture this leg. The filer mix is **constant**: 28 M / 2 A in every
year (27 M / 2 A in the two 29-plant years). The signal is data.

### 3d. Why it is dead, physically

EIA-923 Schedule 5 measures **tonnage delivered and stock held**. The MMU's event was a
**delivery-reliability** constraint — whether a trainload can be counted on *this week* to
support running at full load *this hour*. A fleet facing that takes every load it can get
(smooth, gap-free receipts — exactly what 2022 shows) and **prices the risk into its offer**
to protect a stockpile it cannot rebuild on demand. The tonnage arrives; the *option* to
burn it freely does not. Annual and monthly tonnage cannot see that, which is also why 2024
— a genuine 5.8 % tonnage under-delivery — carries no markup: that was **demand-side decline**,
not a supply constraint.

**Reported for routing only, and proposing nothing:** the markup's rank correlation with
delivered gas is **ρ +0.700 (n=5)**, against −0.900-but-unidentifying on the best
deliverability statistic. SPP-41 §2.6 point 2 rejected the gas-keyed reading partly because
the monitor attributes 2022 to rail; this lane removes the *empirical* support for the rail
attribution being visible in tonnage, without supplying any for a gas-keyed form. **SPP-41's
kill of the gas-keyed sigmoid stands untouched** (weak identification, four parameters on five
points, and `derive_coal_sigmoid` destroys 2023: 39.5 → 97.3 %). Nothing here revives it, and
a gas-keyed proposal would need its own charter and still faces rule 1 condition (b).

---

## 4. `coal_fuel_inventory` for SPP — `U` → `R`, and why re-opening was legitimate

SPP-41's DO-NOT-REDO says *"Do NOT propose a coal energy/capacity ceiling."* Re-opening
needs **new evidence**, and there is some: (a) the `coal_fuel_inventory` field **did not
exist** when SPP-41 was written (row added 2026-09-16, `miso-259`); (b) the intake it reads
was believed absent; and (c) every number SPP-41 cites is about **LEVEL** — peak MW, max-24 h,
per-plant demonstrated maximum — while its own conclusion is that *"the excess is **DURATION**,
not LEVEL"*, which is what an **energy** budget constrains. SPP's cell was `U`, not `R`.

The mechanism caps each month independently at `(opening_stock + delivery_rate) × mmbtu_per_ton / 12`.

| Y | budget Mt | model Mt | headroom % | **flat** bind mo | flat worst % | **cum** bind mo | min stock, days |
|---|---|---|---|---|---|---|---|
| 2019 | 79.62 | 52.59 | +51.4 | 0 | −2.3 | **0** | 88.2 |
| 2020 | 76.18 | 41.96 | +81.5 | 0 | −6.0 | **0** | 137.8 |
| 2021 | 67.97 | 61.26 | +10.9 | **5** | **+45.6** | **0** | 31.6 |
| 2022 | 68.38 | 63.98 | +6.9 | **5** | **+50.1** | **0** | 16.9 |
| 2023 | 71.51 | 46.37 | +54.2 | 2 | +15.9 | **0** | 99.6 |
| 2024 | 78.01 | 39.95 | +95.3 | 0 | −11.3 | **0** | 186.5 |
| 2025 | 66.75 | 53.58 | +24.6 | 3 | +15.8 | **0** | 89.7 |

**The flat row binds in 2021 and 2022 — five months each, peak months 45–50 % over cap —
which are exactly SPP-41's two failing crossover years.** That alignment is **reported, and
is emphatically not the basis for anything**: rule 1 `[R-STRUCT]` forbids selecting a
mechanism because the residual moves.

**And it is an artifact.** The physically correct constraint — stock may never go negative —
**never binds in any of the seven years**, bottoming at 16.9 days of burn in the tightest
(2022) and 31.6 in 2021. The measured stockpile supports precisely the seasonal
drawdown-and-rebuild that the `/12` row forbids. So arming it would push coal down in
2021/2022 **through a flatness assumption the measured data contradicts** — rule 1's
"never reach the right number through a mechanism that isn't real", in one table.

**Verdict `R` for SPP.** This is a verdict on **SPP's own footprint** (rule 25
`[R-ISO-SCOPE]`): it fills no other ISO's cell, and MISO's chartering measurement is
untouched. The `/12` form may well be right for a genuinely inventory-tight fleet; SPP's
is not one.

**Measurement caveat, stated rather than buried.** These are *screening* numbers, not the
mechanism's own arithmetic: tons are converted from the model's class-hourly coal MWh at
year Y-1's measured tons/TWh, where the builder would use per-unit heat rates and the
receipts' own `mmbtu_per_ton`. 2019 uses its own year's factor (no 2018 bench). The
conclusion is not close — `cum_bind` is 0 with 16.9–186.5 days of margin — so no plausible
refinement of the conversion reaches it.

---

## 5. Rules

* **13 `[R-MEASURED]`** — every candidate built from ≤ Y-1; same-year legs computed and
  labelled as the forbidden comparator, never as a candidate.
* **1 `[R-STRUCT]`** — both objects refused on structure. The deliverability markup would
  need a residual-fitted steepness (condition (c)); `coal_fuel_inventory` would move the
  residual through a non-physical flatness.
* **21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero free parameters proposed, zero fields added,
  zero tunables. Nothing armed.
* **25 `[R-ISO-SCOPE]`** — SPP's own fleet and SPP's own footprint throughout; no verdict
  transferred in or out.
* **28 `[R-MECH-MATRIX]` (b)** — `coal_fuel_inventory` cell moved in `SPP.js` this session;
  the deliverability successor has no field and no row, so its verdict is recorded in the
  §5.7 lever queue where SPP-41 entered it.
* **29 `[R-SCREEN]`** — zero-LP phase 0 only. **No screen year was named and none was owed:**
  the screen applies to a candidate *mechanism* competing against a correct one, and both
  objects died in phase 0 before any arm existed. **29(b) form 4 holds** — G-DRIFT from the
  keeper-12 promotion to base finds the solve path unchanged; irrelevant here since no LP ran.
* **31 `[R-RETAIN]`** — nothing deleted; no bundle produced. See §7.
* **32 `[R-SHARD]` (a)** — the parent never solved; no shard was launched because no
  mechanism survived phase 0 to screen.
* **15 `[R-DASHBOARD]`** — no completed calibration run, so nothing to register. The
  dashboard is unchanged and correct.

---

## 6. Reported, not folded in

1. **Parity gate: the same two pre-existing REDs, no new ones** —
   `caiso279_ablate_dswcouple_span` (CAISO) and `soco15_spp_arm`. This lane created no
   bundle and so added none. `soco15_spp_arm`'s `meta.json` reads `iso = SPP`, so it *is*
   in SPP's rule-35(a) scope, but it is cited as live evidence by ten-plus docs across the
   SOCO, NWPP, PJM, MISO and NYISO lanes and rule 31 reserves that call for the owner.
   **Still red; still not pruned.**
2. **`data/clean/coal-{receipts,stocks}` were curated in this container** to run the probe.
   That tree is gitignored, derived and disposable; the probe's docstring carries the two
   curation commands so any lane reproduces it in ~40 s.
3. **The four open objects the lane brief listed are otherwise untouched** — card R-be's
   within-day grain on plant 3008, SPP-43's two declared costs (2022 slack / 2020
   degradation), and the Ponca reproducibility defect in the frozen 2023–2025 extract block.
   None was in this lane's object.
4. **The lane-name collision** with the 2026-09-07 `spp_gas_commitment_bridge` SPP-44 is
   recorded at the head of this document. Neither lane's record is altered.

---

## 7. Promotion question (rule 31 `[R-RETAIN]`) — asked, not pre-empted

**There is nothing to promote, and that is the finding rather than an omission.** No LP was
spent, no bundle was produced, no run was registered, no keeper file was touched and no cell
was armed. Nothing is stranded on ephemeral disk; every number this lane will ever cite is
in this document, and the probe that produces them is committed and re-runnable.

**What the owner may want to rule on** is whether the two cells stay dead:

* the **deliverability-keyed coal offer markup** — this lane's recommendation is that it is
  **dead on measurement**, and that reviving it requires a *different dataset* (a delivery-
  reliability or rail-performance series), not a different statistic on this one;
* **`coal_fuel_inventory` for SPP** — recommended **`R`**, on the flat-`/12` artifact. A lane
  that wanted it would first have to change the row's **form** (a carryover/cumulative
  inventory constraint), which is a shared-machinery change and a different charter.

**SPP's open C1 / C3a / C3b / C4 held-out failures remain open, with no identified
forward-admissible instrument.** After this lane the object is the same as ERCOT's
daily-Waha block: an owner **data-procurement** decision, not a modelling one.

---

## 8. Probe committed (zero-LP, re-runnable)

| probe | what it establishes |
|---|---|
| `scripts/probes/_spp44_coal_deliverability_phase0.py` | all six legs A–F above, including the reporting-frequency confound check |
