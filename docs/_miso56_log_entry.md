## 2026-07-11 — Owner decisions: miso-56 PROMOTED to MISO keeper (supersedes miso-54); PJM G-20b hold CONFIRMED — pjm-87/pjm-88 stay held, keeper stays pjm-97

**Decision 1 — MISO keeper.** Owner promoted `2026-07-11-miso-56-measured-scarcity`
to MISO keeper (owner authorization, this session, 2026-07-11), superseding
`2026-07-10-miso-54-som-restored`, per the recommendation in the miso-56 entry
above: FAIL set identical to miso-55/miso-54-lineage with every class-year delta
flat-to-better, and strictly stronger structural grounding (both new mechanisms
measured — rule-13 AS power reservation + CAMPD-measured conditional commitment
blocks; zero fitted scalars). No re-solve. Executed: `keepers.json` MISO →
miso-56, keeper sidecar marked, `status.js` rebuilt (`build_status.py`), top-15
retention pruned MISO to 15 mains — `2026-07-03-miso-statmode-d-7` and
`2026-07-06-miso-42-coal-econ` (+ twin) displaced (oldest mains; bundles under
`results/calibration/` kept, dashboard registration only).

**Decision 2 — PJM G-20b hold CONFIRMED (owner-decision brief
`docs/handoffs/owner-decision-briefs-2026-07-08.md` Decision 2).** Owner
confirmed 2026-07-11 that `pjm-87` (`pjm_reserve_pergen_sync`) and `pjm-88`
(`pjm_reserve_pergen_size_split`) STAY HELD: the per-gen reserve dual fires in
the correct opportunity-cost regime (sub-$32, never the $300 penalty step) but
at $0–10 vs the $75–200 afternoon residual C3c needs — reserve-supply scoping
cannot price PJM's residual (LP-tightness class, same as ERCOT G-22). `pjm-87`
stays the documented default-off structure (rule 26 — real mechanism, kept, not
re-tuned or deleted); `pjm-88` stays rejected (adds frequency at a real 2025
dispatch-distortion cost, no magnitude gain). Keeper stays
`2026-07-10-pjm-97-measured-interfaces`. This question is CLOSED — do not
re-open reserve-supply probes for PJM C3c; the honest next lever remains
demand-side/commitment tightness (the ERCOT-G-22 route) or accepting C3c as a
disclosed limitation.
