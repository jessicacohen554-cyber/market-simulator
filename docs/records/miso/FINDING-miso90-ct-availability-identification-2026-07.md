# FINDING (miso-90, 2026-07-26) — the MISO CT "coverage hole" is a deliberate IDENTIFICATION exclusion, not a data gap; every output-derived instrument inherits the defect by construction

**Lane.** LANE B' of the miso-89 handoff, taken **on its own merits** (rule 11),
explicitly *not* as a C3b fix — miso-89 already sized its C3b effect at ~$4–6 of
a $16.3 gap and the owner's 2026-07-26 decision ledgered C3b separately.

**Method.** Static reading of the live data path plus direct measurement of the
committed outage extracts. **No LP re-solve.**

**Bottom line: NO-BUILD, on identification grounds.** The 0 % CT measured-derate
coverage is not an oversight, a fetch failure, or an unfilled TODO. It is a
**deliberate, documented, and correct exclusion**, and the reason it exists also
proves that no *output-derived* source — CAMPD CEMS, EIA-923, or any successor of
the same family — can ever fill it. Closing it needs a **capability-declaring**
source, which is precisely the standing data ask
(`docs/handoffs/miso-outage-grain-data-ask-2026-07.md`).

---

## 1. First, a correction to the inbound framing

The miso-89 handoff carried the hole as "**CT_PEAKER + CT_CHP = 25.02 GW at
0.0 % CAMPD derate coverage**". Measured directly, that number is right about
the *derate map* but conflates two different classes at two different stages:

| | rows in `campd-unit-outages-MISO.csv`, 2023–2025 | plants | reaches the derate map |
|---|---|---|---|
| CT_PEAKER | **0** | 0 | no |
| CT_CHP | **115** | 27 | no |

CT_CHP **is** in `QUALIFYING_PLANT_GROUPS`, and the detector **does** write 115
CT_CHP outage windows across 27 MISO plants. They are then discarded one stage
later, by `outages._unit_outage_target`, which returns `None` for both CT groups.
So the two classes are at 0 % coverage for **two different reasons** — CT_PEAKER
is never detected, CT_CHP is detected and then dropped — and only the second is
even arguably recoverable. The aggregate "25.02 GW at 0.0 %" is true of the
derate map and should not be read as 25 GW of uniformly missing data.

## 2. The exclusion is deliberate, and its stated reason is an identification argument

`src/market_sim/data/outages.py`, module docstring:

> Combustion turbines (`CT_PEAKER` / `CT_CHP`) carry no derate — they dispatch
> economically, and **a CT down-window cannot be certified a forced outage vs
> out-of-merit-at-peak** (unlike baseload coal/CC, where down-at-peak reliably
> implies an outage).

Enforced at `outages.py:260` and `:298` (`_unit_outage_target` → `None`) and
restated at `:240`. The same judgement is made independently for the spiky
`ST_GAS_PEAKER_PLANTS` set (`outages.py:139-160`), where the comment is blunter:
the event-based rule *"would flood them with economic-idleness windows."*

This is not a data-availability claim. It is an **identification** claim, and it
is correct. An event-based outage detector infers *unavailability* from *absence
of output*. That inference is valid only when running is the unit's default
state. For a peaker, **not running is the default state** — so absence of output
carries no information about availability, and any window the detector emits is
unfalsifiable.

## 3. Therefore every output-derived instrument inherits the defect — verified, not assumed

The obvious candidate substitute is the EIA-923 monthly fallback landed
2026-07-24 (`data/raw/campd-unit-outages-e923-MISO.csv`, default-off), which
exists specifically to cover **non-CAMPD** plants. It does not help, and it
declines for the same reason rather than by accident —
`scripts/data/derive_campd_unit_outages.py::derive_eia923_noncampd_fallback`:

> Only plants in a `QUALIFYING_PLANT_GROUPS` bin (**peakers excluded, matching
> the overlay**) that are ABSENT from `campd_codes` are considered.

Measured contents of the MISO file, all years:

| plant_group | rows | plants | MW |
|---|---|---|---|
| CC_CHP | 14 | 5 | 2,282.1 |
| CC_REGULAR | 14 | 2 | 2,117.6 |
| CT_CHP | 37 | 7 | 1,244.3 |
| ST_CHP | 70 | 14 | 1,185.5 |
| COAL | 35 | 7 | 235.9 |
| **CT_PEAKER** | **0** | **0** | **0** |

Zero CT_PEAKER rows, in nine years of data. And its detector rule makes the
reason explicit: a month is "out" when net generation `<= ratio × reference`,
where `reference` is *the plant's own median positive-month output*
(`_eia923_month_windows`). For a unit whose median month is near zero by design,
that test is degenerate — it either never fires or fires on ordinary economic
idleness. **The EIA-923 layer cannot substitute for CT availability, and it was
built already knowing that.**

Both candidate instruments are output-derived; both fail identically; the failure
is structural to the family, not to either implementation.

## 4. What IS a live defect: the statistical substitute rests on an uncited, undeclared parameter

With no measured overlay, all 22.39 GW of MISO CT_PEAKER availability comes from
the statistical model in `data/fleet/arrays.py::_availability_matrix`, whose
seasonal design is (code-verified, `arrays.py:374-385`):

* **POF (planned outages): shoulder months ONLY** — none in summer or winter.
* **WEFOR (forced outages):** only `_SUMMER_WEFOR_SHARE` applies in summer; the
  remaining `(1 − share)` is redistributed into the shoulder. Winter keeps flat
  WEFOR.
* A flat weather/performance derate, plus `_SUMMER_CLASS_DERATE` = 0.125 for
  CT_PEAKER/CT_CHP.

The annual outage *energy* is conserved; only its seasonal *shape* moves. For
planned outages this is well-founded — operators genuinely schedule maintenance
away from peaks. For **forced** outages it is a much stronger claim, and it runs
the opposite way to the physics: forced outages correlate *positively* with heat
and high load, not negatively.

The parameter carrying that claim is:

```python
# src/market_sim/data/fleet/arrays.py:164-167
# Fraction of a unit's WEFOR (forced-outage rate) that applies during the
# summer peak; the remaining (1 - share) is redistributed into the shoulder
# months. Winter keeps the flat WEFOR.
_SUMMER_WEFOR_SHARE: float = 0.30
```

**It carries no citation comment, appears nowhere in
`docs/parameter-citations.md`, and is absent from the keeper's DOF ledger** (26
entries, verified — `calibration_attestation.json.free_parameters`). Under rule 5
`[R-NO-MAGIC]` it needs a source; under rule 20 `[R-REGISTRY]` and rule 21
`[R-DOF]` it needs to be declared. It governs the summer availability of the
single largest measured-blind block in the MISO fleet.

**This finding does not change its value.** Re-tuning 0.30 against a residual is
exactly the answer-key move rule 24 forbids, and doing it in the same session
that ledgered C3b would be indistinguishable from tuning to the ledgered miss.
The correct dispositions are (a) declare it in the DOF ledger as
residual/unidentified, and (b) name it as a target of the data ask, which is
where a measured seasonal forced-outage shape would come from.

## 5. Pre-registered expectations, recorded for the record

The handoff asked Lane B' to pre-register its effects before building. No build
happened, so nothing is claimed — but the pre-registration stands as written and
should bind any future attempt:

* Effect on C3b: **~$4–6 of the $16.3 peak-hour gap at most** (miso-89 §5) — a
  ~3.4 GW derate against 31.9 GW of idle fossil headroom, leaving the reserve
  constraint slack by ~10×. **Not a C3b remedy.**
* Effect on C1: expected to **worsen** CT_PEAKER volume.

## 6. Disposition

**NO-BUILD.** Not because the data was not fetched, but because the quantity is
**not identified** by any source of the type available. Per rule 24, the honest
outcome is to report that and stop rather than manufacture a number.

Two follow-ons, neither of which is a C3b lane:

1. **DOF-ledger `_SUMMER_WEFOR_SHARE`** (and audit the sibling
   `_SUMMER_CLASS_DERATE` literals for citations) — a governance defect that is
   real, cheap, and independent of any residual.
2. **The standing data ask** — `docs/handoffs/miso-outage-grain-data-ask-2026-07.md`.
   §2–§3 above sharpen its acceptance test: the required source must declare
   **capability**, not output. That single criterion rejects CAMPD, EIA-923, and
   every derivative of either, and it is the reason the ask is genuinely
   blocking rather than merely unattempted.
