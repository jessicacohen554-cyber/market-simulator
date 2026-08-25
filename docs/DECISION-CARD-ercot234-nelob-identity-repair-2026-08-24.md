# OWNER DECISION CARD — ercot-234 (card Z): repair the `NE_LOB` geographic mis-attribution in the keeper's measured-GTC crosswalk?

**For the owner. Session ercot-234, 2026-08-24. Status: AWAITING OWNER
SIGNATURE — NOTHING IS REPAIRED, SOLVED, OR ARMED BY THIS CARD.** Evidence
basis: `docs/FINDING-ercot234-subzonal-survey-nelob-identity-2026-08-24.md`
(primary-source documentary facts + descriptive reads of the committed NP6-86
archives; no solve, no LP, no bar-bearing measurement, keeper untouched).

Scope: ERCOT only (rule 25). Years referenced ⊂ {2023, 2024, 2025} (rule 22).
Keeper at assembly: `2026-08-24-231-tie-zone-measured`, determination NOT-YET
on {C3a-2023 −38.0 %, C3b-2023 0.696}, C3c-2023 clean PASS, C3c ledgered ×2.

---

## 1. The fact being adjudicated

ERCOT's public GTC definitions identify **`NE_LOB` as "North Edinburg – Lobo"
— a South Texas / Rio Grande Valley stability corridor** ("a stability limit
associated with South Texas wind farms connecting along the North Edinburg –
Lobo 345 kV line", GTC Workshop definitions deck 2020-02-24; still grouped
under "Valley Area" in the July-2024 ROS GTC update). The model reads the
name as "**N**orth**e**ast **lob**e" and:

- carves its **Northeast zone** out of North expressly "to capture the NE_LOB
  GTC" (`iso_configs._ercot_config`);
- sets the Northeast→North static export rating to NE_LOB's measured
  limit-at-bind (**1,300 MW — the forecast topology's East-Texas interface
  rating, not just a backcast overlay**);
- overlays NE_LOB's measured hourly limits onto that link in every keeper
  year (`ercot_gtc_limits_measured` → `data/gtc.py` →
  `constants.ERCOT_GTC_LINK_MAP`);
- and dismisses **EASTEX — ERCOT's actual "flows out of the East Texas area"
  GTC, the model boundary's true counterpart — as "intra-zone,
  unrepresentable"**, while the model's own zone map places the Rio Grande
  Valley (NE_LOB's real location) inside its South zone, making NE_LOB the
  unrepresentable intra-South pocket (VALEXP's existing class).

Magnitude, from the committed record: the keeper caps its ~8 GW NE lobe at
the Valley's 1,245/1,260/1,549 MW (p50) series, binding-heavy in all three
years, where the real EASTEX bound 828 → 191 → 3 intervals at ~2× the limit
(2025 parked at ~43 GW — effectively unconstrained). The 21 spurious
in-season mid-band hours the ercot-231 promotion accepted (G-SPUR) are hours
where this manufactured NE congestion prices Northeast $24–126 apart
(ercot-232 §1).

This is new evidence in the rule-28 sense (primary source vs the crosswalk's
own citation, which never defines NE_LOB), touching a measured input the
keeper REQUIRES. It does NOT re-open Q-B/R-A, the ercot-233 zonal-grain
timing closure, `internal_congestion_split` `G`, or the tie placement — the
FINDING §II.4 walks each fence. Under rule 14 a knowingly mis-attributed
measured input cannot silently rest, and any repair changes keeper inputs in
all three years — hence this card.

## 2. The options

**(Z-A) CHARTER THE FULL IDENTITY REPAIR — RECOMMENDED.** One executing
session, in order:

1. **Phase 0, boundary reconciliation (zero-solve, precommitted):** establish
   from public materials (workshop element slides, Constraints-and-Needs
   reports, SOM congestion tables) that EASTEX's monitored boundary
   corresponds to the model's EAST-weather-zone carve within rule 14's
   misalignment clause. If it cannot be reconciled, fall back to Z-B.
2. **Crosswalk repair (zero fitted scalars):** remove `NE_LOB` from
   `ERCOT_GTC_LINK_MAP` (it joins VALEXP/NELRIO/RV_RH as an intra-South
   pocket, per the topology's existing caveat class); map `EASTEX` to
   `(Northeast, North)` 1:1. Sweep every consumer of the old mapping
   (`iso_configs`, `constants`, `data/gtc.py`, `derive_ttc_limits`,
   `transmission_expansion`, `zone_assignment`/`zonal_shares`/`scenarios`
   comments) so no "NE_LOB = NE Texas" gloss survives (rule 26 spirit).
3. **Static rating re-derivation (rule 23, source-data-cited):** re-run
   `derive_ttc_limits.py` for the Northeast→North export rating from
   EASTEX's measured record, handling its sparse 2024/2025 honestly
   (limit-at-bind where populated; the reconciled Constraints-and-Needs
   interface capability otherwise — documented, never tuned). Import side
   unchanged (the ERCOT-76 measured envelope is genuinely NE-Texas data).
4. **Full rule-16 3-year re-solve** under a pushed, blob-verified precommit
   with the standing mechanical gates (G-SPUR incl. band-top report, G-SHED,
   G-C3c, G-SPAN, G-DOF, G-D2, G-OWNER), registered whatever it shows
   (rule 15), all C3a/C3b movement **side-effect-reported under Q-B/R-A** —
   this charter's basis is identity, never the residual. Promotion is
   adjudicated separately on that record, by you, as every promotion in this
   lane has been.

**(Z-B) ATTRIBUTION REMOVAL ONLY.** Steps 2–4 with no EASTEX hourly overlay:
NE_LOB leaves the crosswalk, the static rating is re-derived per step 3, the
link keeps a static-only cap. Smaller and safe against a failed boundary
reconciliation, but discards measured hourly variation rule 14 says to
prefer where the boundary DOES reconcile.

**(Z-C) REST AS-IS.** Record the defect; keeper and forecast topology keep
the mis-attributed series and the "NE Texas export ~1,300 MW" gloss.
Stated for completeness — this is the option rule 14 exists to refuse, and
it leaves a known-wrong measured input armed in a keeper and a known-wrong
static rating in the forecast product.

**Recommendation: Z-A**, with Z-B as its own named fallback. Zero fitted
scalars either way; every number in the repair traces to a published or
committed measured source.

## 3. What a signature does and does not do

- Z-A/Z-B license exactly the numbered steps — no other cell re-test, no
  admissibility beyond this object, Q-B/R-A untouched.
- The ercot-231 promotion record stands unrewritten; the repair is its
  successor on the same measured-input lane (tie placement kept, gtc-limits
  partition kept — re-pointed to the constraint that is actually there).
- The ercot-232/233 records stand as measured; their physical narrative is
  superseded by the FINDING's identity reading, recorded, not rewritten.
- **Independent and still pending: the ercot-225 G-SPUR band-top gate card**
  (`results/calibration/DECISION-ercot225-gspur-bandtop-gate-2026-08-21.md`,
  Option A recommended, AWAITING SIGN-OFF since 2026-08-21, scorer-only).
  Signing it is worthwhile BEFORE the Z-A re-solve gates run, so the
  repair's G-SPUR reading is lidless from the start — but it is a separate
  signature and stays as put.

*Fences honoured in the session that wrote this card: no solve, no LP, no
mechanism tested, no matrix cell verdict, no gate-file edit, no keeper
change, no holdout marker touched, no C3a/C3b-2023 spend. The ercot-188/E2
P0 bit-identity forfeiture is inherited unexpired and untouched.*
