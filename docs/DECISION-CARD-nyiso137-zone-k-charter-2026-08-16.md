# DECISION CARD nyiso-137 — CHARTER REQUEST: the JOINT Zone-K reconciliation

**Session nyiso-137, 2026-08-16.** Requested under rule 19 `[R-ONE-MECH]`. No
solve has been spent and none will be until this card is answered — the arm is
not written and no pre-registration is filed.

> **STATUS (nyiso-138, 2026-08-16, main `e1760bb`): D1 · D2 · D3 REMAIN OPEN and
> unanswered — no owner ruling has been received on any of them, and no solve has
> been spent. D4 is WITHDRAWN: another lane resolved it at HEAD (see D4 below);
> it needs no ruling and its recommended edit must not be made.** nyiso-138 spent
> no solve, wrote no mechanism, and made no edit to `src/`.

---

## THE ASK, IN ONE SENTENCE

Authorize a **joint** local-security representation for Zone K — the
mainland→Zone-K transfer bound **and** the downstate ST_GAS `min_gen`
reliability floor reconciled as **ONE** mechanism — as the named successor
nyiso-130 left open, with its own pre-registration to follow before any LP runs.

## WHY IT NEEDS A CHARTER RATHER THAN JUST A PRE-REGISTRATION

nyiso-130 established that Zone-K reliability is carried in this model by **two**
proxies, and that relieving one **loads the other**: arming the published 940 MW
transfer limit alone collapsed the tail to 2 / 0 / 5 h and fired kill gate K6,
the downstate ST_GAS floor taking up the slack at +0.22 / +0.42 / +0.23 TWh. So
the successor necessarily touches **two** existing armed representations at once,
which is precisely the case rule 19 reserves for an owner charter rather than a
session decision.

## WHAT IS ALREADY SETTLED, AND NEEDS NO RE-LITIGATION

* **The identification is published and stands** (nyiso-130 §1–§2, untouched by
  its own rejection). NYISO's Zone-K "Locality Limit" is the N-1-1 transfer limit
  **minus** a 660 MW generation loss-of-source, stated in TABLE 1 note 2 of the
  Locality Bulk Power Transmission Capability Reports identically across the
  2024-25, 2025-26 and 2026-27 editions. The model already carries that
  contingency **twice** elsewhere. Zero free parameters.
* **The bare number swap is dead.** `nyiso_li_tsl_n11_security` is `R`, killed on
  K6. It is not proposed again.
* **The RTD-clock disclosure is GRADED and does not block this lever** —
  nyiso-137, `FINDING-nyiso137-rtd-clock-graded-against-zone-k-gates-2026-08-16.md`.
  All six kill gates K1–K6 are computed from the arms' own output bundles and
  read no actual-price series; the promote criteria that do (C3a, C3b) move by
  −0.0353 % pooled against a nearest band margin of 1.2 pp.

## THE THREE DECISIONS REQUESTED

**D1 — Grant or refuse the charter.** If granted, nyiso-138 writes the joint
mechanism and its pre-registration, and solves 2023 / 2024 / 2025 in one bundle
(rule 16). If refused, the NYISO lever queue reduces to item (2), the VRE
availability object, which nyiso-136 sized and argued against on its own merits.

**D2 — The C3c reporting condition.** nyiso-137 measured that the C3c **actual**
count is verdict-fragile under the known interval mis-binning: 2023 flips
FAIL → PASS on **one** actual-hour, 2025 flips PASS → FAIL on **seven**. The
arm-vs-control **delta** is invariant (both arms score against the same actual);
absolute band membership is not. Requested ruling: **any C3c-turning claim from
this lever is reported as CONDITIONAL on the clock repair, and the promote
decision rests on K1–K6 plus C1/C2/C3a/C3b/C4/C6/C8 as nyiso-130 §8 already
fixed — "whatever C3c does".**

**D3 — Does the clock repair go first?** The repair is a one-line change to
`derive_actual_lmp._nyiso_wide` plus a re-derivation of
`actual_lmp_hourly_NYISO.parquet`, and it is **data-blocked**: only 21 monthly RT
zips are staged against a 2018-2026 series, and 2022's twelve are inside the
active holdout freeze. Three options:

| | option | cost |
|---|---|---|
| **a** | Charter the lever now, repair later | The C3c ledger keeps a caveat whose 2023 entry is one hour from vacating. Cheapest; D2 contains the risk. |
| **b** | Re-stage the NYISO RT archive, repair first, then charter | Correct order, but blocked on staging ~8 years of monthly zips and on the freeze for 2022. |
| **c** | Repair on partial coverage | **Not recommended and not offered as equal** — the standing disclosure forbids re-deriving the parquet on partial coverage. |

Session recommendation: **(a) with D2 attached.** The lever's licence is the
published number and the removed double count, not the tail count (rule 1
`[R-STRUCT]`), so it does not depend on the repair landing first.

**D4 — WITHDRAWN 2026-08-16 (nyiso-138): RESOLVED AT HEAD BY ANOTHER LANE. No
owner ruling is required; do not grant one.** The requested `_IGNORE` edit must
**not** now be made — it would double-handle a key already dispositioned.

Between nyiso-137 writing this card (main `ce779f9`) and nyiso-138 opening
(main `e1760bb`), commit `a964e23` — the DEBUG-manager lane, pushed by the
pjm-163 promotion, which made `2026-08-15-pjm-162-inputclock` the first *keeper*
meta to carry the deleted key — fixed this. The disposition chosen is **not**
the `_IGNORE` table this card asked for but a **new, narrower ledger**,
`replay_keeper._RULE26_DELETED_UNCONDITIONAL`, keyed
`field -> (owning_iso, unconditional_value)`. That is the **better** home and
supersedes this card's recommendation on the merits: `_IGNORE` would have
dropped the key silently in *every* ISO, whereas the ledger keeps the recorded
value as provenance, skips it as inert outside the owning ISO (rule 25
`[R-ISO-SCOPE]`, where the mechanism was never reachable), and **hard-errors
inside** the owning ISO for a bundle recording the dead polarity — honouring the
cache epoch note's own "read, never replayed" rather than silently replaying a
different mechanism.

Verified by nyiso-138 at `e1760bb`: `test_replay_keeper_strict.py` **8 passed**;
the designated keeper `2026-08-08-nyiso-133-cod-arm` records
`nyiso_solar_registry_cod_dates: true`, which **is** the unconditional value, so
it replays cleanly; and it is the **only** NYISO bundle on disk carrying the key,
so the ledger's hard-error branch is unreachable in this lane. Nine bundles
across five ISOs carry the key in total. **The stale baseline this card and the
nyiso-138 handoff both inherited — "1 pre-existing failure in
tests/scoring/test_replay_keeper_strict.py" — is therefore no longer true and
must not be carried forward as a known-failure allowance.**

*Superseded text follows, retained for the record:*

~~**D4 — NEW, and independent of D1–D3: the designated keeper is UNREPLAYABLE at
HEAD.**~~ Found while running this session's gates, **confirmed pre-existing on a
pristine tree**, and *not* among the costs nyiso-136 declared.
`tests/scoring/test_replay_keeper_strict.py::...::test_all_keeper_metas_build`
fails because `2026-08-08-nyiso-133-cod-arm`'s committed `meta.json` still
carries `nyiso_solar_registry_cod_dates`, which nyiso-136 deleted from
`ScenarioConfig`; `replay_keeper.build_kwargs` is strict by design and refuses
the unmapped key rather than dropping it (the miso-50..53 regression class).

Requested ruling: **add the name to `replay_keeper._IGNORE`.** That is the
semantically correct home — it governs recipe *reconstruction*, not hashing, and
its meaning is "not a solve kwarg", which is now true because the collapse made
the flag's behaviour unconditional in both lanes. This is deliberately **not**
the `_CACHE_KEY_RETIRED_FIELDS` situation nyiso-136 warned about, where
retirement would have re-inserted the name and moved the pinned key. This
session did not make the edit because it is a governance assertion about keeper
reproducibility, not part of the assigned lever.

## STANDING BLOCKERS, UNCHANGED — flagged, not actioned

* The **holdout spend freeze is ACTIVE**, re-confirmed HELD 2026-08-15. The 2022
  touchpoint is data-ready (nyiso-134) and blocked only on an owner lift. Its
  disclosures: import-tranche 719 MW duration RMSE (**ungraded**), Transco
  Dec-2022 Elliott hole (**ungraded, unfixable from the free archive**), and the
  RTD-clock mis-binning — **graded for 2023-2025 by nyiso-137, still ungraded for
  2022**, which is the year it was quantified on.
* Cross-lane, flag-don't-action: the NYISO **forecast** lane's 11 committed
  hindcast sidecars are stale after nyiso-136's gate collapse (rule 15's separate
  namespace); NEISO's 2022 touchpoint is stale w.r.t. HEAD; CAISO's 2018-2022
  CARB block is still absent.
