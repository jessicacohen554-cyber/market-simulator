# PRECOMMIT — caiso-265: the 2022 winter over-pricing object. Is it identifiable IN-SAMPLE, or is it an out-of-sample regime rule 22 forbids fitting?

**Pushed BEFORE any measurement.** Session caiso-265, 2026-09-08, branch
`claude/caiso-backcast-2022-hvh9xz`. Keeper **`2026-09-06-caiso-260-b1-demand`**
(CALIBRATED, rubric v3.6) — **UNCHANGED by this session whatever the numbers
say**. Touchpoint `2026-09-07-caiso-262-2022-touchpoint` (NOT-YET on 2022,
rule 30(c): it moves no determination).

Owner instruction, this session: take `FINDING-caiso262-2022-touchpoint`
**§8 QUEUE item 1** — diagnose the high-gas passthrough regime.

---

## §0 — What this session IS and IS NOT

**IS:** a **DIAGNOSIS**, zero-LP in its primary phase, run off already-committed
artifacts (the keeper's and the touchpoint's `hourly/` sidecars, the committed
measured actuals, the committed citygate series).

**IS NOT** — declared now, so none of it can be reached for later:

* **NO `ScenarioConfig` field** is added, and no default is flipped.
* **NO offer-curve band multiplier** is touched. The rule 1 `[R-STRUCT]` /
  rule 13 `[R-MEASURED]` authorized price-tuning channel is **NOT USED**; the
  keeper's `authorized_price_tuning` block stays absent.
* **NO gas haircut, adder, offset, or contract-discount of any kind.** I record
  now that `ercot_gas_contract_haircut` exists as a default-off field and that
  reaching for a CAISO analogue would be the fitted mechanism rules 1/13
  forbid. It is out of bounds for this session **and** as a proposal.
* **NO keeper change, no promotion, no re-registration.**
* **NOTHING IS FITTED TO 2022.** Rule 22: 2022 is validation tier — iterable
  selection evidence, never a training target. Any repair this lane eventually
  proposes must be *identified on 2023–2025* and only then re-tested on 2022.

## §1 — The object

`FINDING-caiso262` §2: on the touchpoint, CAISO 2022 misses C3a by **+21.1 %**
(hub basis), and the miss is **seasonal, not a level shift** — Jan **+28.5 %**,
Feb **+31.4 %**, Dec **+27.7 %** against Jun/Aug/Sep/Nov at **+4.5 % … +8.6 %**,
i.e. the summer sits in the same band the model holds in 2023–2025. The run log
records the hub-basis overlay repricing 1,443 gas generators at measured
citygate spot with a **winter maximum of $54.05/MMBtu**.

§2's stated hypothesis — **full measured gas passthrough into a price regime the
training window never contained** — is explicitly labelled there as a hypothesis,
not a conclusion, and is not isolated against import depth, hydro or storage.

## §2 — The question this session answers FIRST, before any mechanism talk

Rule 22 makes one question logically prior to every other one:

> **Is this defect visible and identifiable inside the training window
> (2023–2025), or does it exist only at 2022's extreme?**

If it is *only* at 2022's extreme, then **no repair may be built at all** —
identifying one would mean fitting to a validation year, which rule 22 forbids
outright. That is a real and permitted outcome of this session, and I commit to
reporting it as the result rather than working around it.

## §3 — M1, the pre-registered primary measurement

**M1 — monthly price error against monthly gas price, 48 months, 2022–2025.**

For each month of 2022 (touchpoint bundle) and 2023/2024/2025 (keeper bundle):

* `model(m)` = model RT price, aggregated on the **`CAISO_HUB_WEIGHTS` basis the
  scorer uses** (`derive_actual_lmp.CAISO_HUB_WEIGHTS`: NP15 0.3969 / ZP26
  0.0646 / SP15 0.5385), from the committed `system_<year>.parquet`.
  *Declared now:* `FINDING-caiso262` §7 disclosure 2 records that a zone-demand
  weighting reads +16.2 % where the scorer reads +21.1 %. **The hub basis is the
  one that counts**, and M1 uses it; any zone-demand figure is labelled as a
  shape diagnostic, never quoted as the scored number.
* `actual(m)` = measured RT on the same hub basis, from the committed
  `actual_lmp_hourly_CAISO.parquet`.
* `err(m)` = `model(m)/actual(m) − 1`.
* `gas(m)` = measured CA composite citygate, monthly mean of
  `data/raw/gas-prices/caiso_citygate_daily.csv` — **the same series the run
  consumed** (`caiso_citygate_spot_level=True`, `caiso_citygate_flow_date=True`,
  `caiso_citygate_spot_coverage=True`, `gas_hub_basis_overlay=True`).

**M2 — the implied market heat rate.** `IMHR(m) = price(m)/gas(m)`, computed for
model and actual. Reported because it is the physical statement of the
hypothesis: near-linear passthrough means a flat `IMHR_model` against gas, and
"the market clears below full passthrough" means `IMHR_actual` **falls** as gas
rises. *(Noted now so it cannot be presented as an independent confirmation
later: `IMHR_model/IMHR_actual ≡ model/actual`, so M2's ratio is algebraically
M1's error. M2's content is the LEVEL and SLOPE of each curve separately, not
the ratio.)*

## §4 — DECISION RULES, fixed before the numbers

Let **T** = the 36 training months (2023–2025), **V** = the 12 months of 2022.

* **D-1 — IN-SAMPLE IDENTIFIABLE.** If, within **T alone**, `err(m)` rises with
  `gas(m)` (positive slope, and the highest-gas training months already carry
  visibly positive error), the defect is present in the training window. Rule 22
  is then satisfiable and the lane may proceed to attribute the mechanism on T.
  **This is the only branch in which any repair may ever be identified.**
* **D-2 — OUT-OF-SAMPLE-ONLY ⇒ STOP.** If **T** shows no such relationship and
  the error appears only in **V**'s extreme, then the object is identifiable
  only against a validation year. **The lane STOPS.** I state the finding, name
  what evidence would be needed, and build nothing. No parameter, no mechanism,
  no field. **I commit to this branch now** so that a null result cannot be
  converted into a licence to tune.
* **D-3 — attribution, only if D-1 fires.** Enumerate the candidate structures
  that get cheaper *relative to gas* as gas rises and that the model may under-
  carry — imports priced off a different basin, hydro, storage, DR — and test
  them on **T** using committed artifacts. Rule 19 `[R-ONE-MECH]`: before any
  new mechanism is proposed, enumerate what already prices the same hours.
* **D-4 — the honest-null clause.** A month-level relationship that is visible
  but explains only part of the winter gap is reported at its measured
  magnitude, not rounded up into a mechanism.

## §5 — What I will report either way

The monthly table (model, actual, error, gas, both IMHRs) for all 48 months, the
D-1/D-2 verdict, and — whichever branch fires — the disclosures against interest.
No number in the finding will be my own re-derivation standing in place of the
scorer's where the scorer has one (`FINDING-caiso262` §7 disclosure 6 is the
precedent: the scorer's figure is authoritative).

**No keeper change. No `ScenarioConfig` field. No mechanism-matrix verdict move
unless a mechanism is actually tested (none is planned). Next number: caiso-266.**
