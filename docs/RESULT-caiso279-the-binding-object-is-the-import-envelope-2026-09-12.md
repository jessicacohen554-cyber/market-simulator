# RESULT — caiso-279: the arm is **REFUTED** (it moves C3a-2022 the WRONG WAY), and in refuting it the shards found the real object: **a MEASURED IMPORT ENVELOPE that binds 92–95 % of the hours carrying the miss, at a shadow price of −$169 to −$285/MWh, while the physical interties sit at 24–60 % utilisation.** The CAISO overshoot is **quantity-constrained, not price-constrained** — which is why eighteen sessions of price-side levers found nothing.

**Session caiso-279, 2026-09-12. CAISO only (rule 25 `[R-ISO-SCOPE]`). Two shards, one LP each;
the parent spent ZERO LP.** Charter:
`docs/PRECOMMIT-caiso279-dsw-import-gas-regional-basis-2026-09-12.md` (pushed at `0901c503`
before either solve). Control: keeper `2026-09-12-caiso-275-gascoupling`, G-CTRL **form 4**, no
control solve spent. **KEEPER UNCHANGED. NOTHING PROMOTED.**

---

## §1 — THE ARM FAILED ITS OWN PRE-REGISTERED GATE, IN THE WRONG DIRECTION

Arm A: `replay_keeper caiso275_B_gascoupling_2022 --years 2022 --set caiso_import_gas_coupling=false`.

| | control | arm | |
|---|--:|--:|---|
| **2022 load-weighted price** | 94.069 | **95.478** | **+1.409 $/MWh** |
| **C3a-2022 vs rt_lw 84.49** | +11.34 % | **+13.00 %** | gate ceiling 92.939 — **FAIL, further out** |
| December load-weighted | 291.708 | **305.818** | +14.11 |
| import TWh (annual) | 53.497 | 51.975 | **−1.522** |
| CC_REGULAR TWh | 53.214 | 54.506 | **+1.292** |
| slack / dump | 0 / 0 | 0 / 0 | no scarcity either side |

**G-DIR — pre-registered as "December Δλ is negative" — FAILED.** The charter required the
diagnostic to stop on exactly this, and it does. **The arm is refuted and is not promotable**;
the ablation is not re-run, and no second value is tried (rule 1 (c)).

**G-IDENT: 3 fields differ, of which ONE is behavioural.** `caiso_import_gas_coupling`
True → False; the other two (`unit_outage_window_hour_grain`, `miso_import_sil_measured_envelope`)
are **absent in the control and `False` in the arm** — new default-off fields added to
`ScenarioConfig` between the keeper's solve and HEAD `ab1267e9`, one of them another ISO's.
Reported rather than waved through. G-LIVE: 3,660 of 61,320 zone-hours move > $5, max $539.11.
D1/D2/D5/D9/D10 pass; **D4 fails in the arm and in the control alike** (pre-existing `chp_steam`
unit-conduct rows) — no flip.

## §2 — WHY IT FAILED, AND IT IS NOT A SIGN ERROR IN THE ARITHMETIC

The PRECOMMIT's §3 delta was computed for **December**, where the coupling's shift is strongly
positive (+74.3 / +110.5 $/MWh). Across the **year** the sign is mostly the other way, so removing
the coupling made imports dearer on net: −1.52 TWh of import replaced by +1.29 TWh of CC_REGULAR,
and the price rose. **The annual sign was never measured before the solve — only December's.**
That is this session's identification error and it is owned here.

**But the far more important finding is where the arm did NOTHING:**

| Dec 2022 day | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Δ price (arm − control) | **0.0** | +11.2 | +13.4 | **0.0** | **0.0** | +12.9 | **0.0** | **0.0** | **0.0** |
| Δ import MW | +0.2 | −1.7 | −120.6 | **0.0** | **0.0** | −261.5 | **0.0** | **0.0** | **0.0** |

**Six of the nine days that carry the entire miss are byte-identical.** On Dec 23/26/27/29/30/31
the import sits at exactly **7,482.8 MW in both arms.** Repricing a block changes nothing when the
block is already **at its bound**.

## §3 — THE REAL OBJECT, MEASURED FROM THE ARM'S OWN `network_2022.parquet`

Dec 29–31, all 72 hours:

| constraint | flow MW | limit MW | utilisation | **dual $/MWh** | hours at bound |
|---|--:|--:|--:|--:|--:|
| **`grp:+WECC_PNW>NP15`** | 1,157.58 | 1,157.58 | **1.000** | **−285.41** | **72 / 72** |
| **`grp:+WECC_DSW>SP15_rest`** | 6,325.21 | 6,325.21 | **1.000** | **−261.94** | **72 / 72** |
| `WECC_DSW>SP15_rest` (physical link) | 6,325.21 | 10,623 | 0.595 | 0.000 | 0 |
| `WECC_PNW>NP15` (physical link) | 1,157.58 | 4,800 | 0.241 | 0.000 | 0 |

**The physical interties are not the constraint — a measured ENVELOPE sitting far below them is.**
Those group limits are **time-varying with 286 distinct daily values** (range 2,380–7,741 and
301–3,961 MW) against physical TTCs that are single constants — i.e. an hourly/daily measured
import envelope, the `caiso_firm_envelope_clip` family, applied as an interface-group limit.

**How often it binds, over the whole year:**

| envelope | all 8,760 h | December | **Dec 23–31** | mean dual when binding (Dec 23–31) |
|---|--:|--:|--:|--:|
| `grp:+WECC_DSW>SP15_rest` | **43.4 %** | 47.7 % | **92.1 %** | **−169.39 $/MWh** |
| `grp:+WECC_PNW>NP15` | **40.1 %** | 81.2 % | **95.4 %** | **−193.63 $/MWh** |

**It reconciles exactly with the price spread §1 of the closure measured independently**: the
import nodes clear $137–151 while internal CAISO clears $409–423 on those days — a $258–270
wedge, which is the congestion rent these duals report. Two measurements, taken different ways,
agreeing to a few dollars.

## §4 — THIS CORRECTS caiso-276 §5b, AND EXPLAINS EIGHTEEN SESSIONS

caiso-276 §5b concluded *"the seam is not binding, in any window — **hours ≥ 99 %: 0**"* and that
kill has been carried forward ever since, including into caiso-278's charter. **It measured the
PHYSICAL LINK utilisation** (0.595 DSW / 0.241 PNW, and the combined
`grp:+WECC_PNW>NP15+WECC_DSW>SP15_rest` at 0.474) — **not the per-corridor group envelope, which
is at 1.000 for 72 of 72 hours.** The conclusion is false for the object that actually binds. It
is a measurement-target error, not a data error, and every number in §5b is individually correct.

**That single error is the best available explanation of why this lane has run dry for eighteen
sessions.** On the hours that carry the miss the solution is **quantity-constrained**: λ is set by
an envelope's shadow price, not by any generator's offer. A price-side lever cannot move a
quantity-constrained solution — which is precisely what was measured, each time, one lever at a
time:

* the CHP/ST_GAS offer surface — ~1 % of the object (caiso-231's own solved A/B);
* the flat ×0.92 fossil cut — closes C3a and breaks C4-2025 (caiso-267/268);
* the CC bands the authorized channel can reach — already 0.05 **below** the market's own implied
  heat rate (caiso-272, LP-row grain);
* wider RA must-offer reach — only 2.9 % idle-in-the-money to act on (caiso-276 §5a);
* and now the desert-SW import gas coupling — **inert on six of the nine days that matter**.

## §5 — WHAT IS AND IS NOT ESTABLISHED

**Established, by measurement:** the envelope binds, where, how often, and at what shadow price;
that the physical interties have 4.3 GW (DSW) and 3.6 GW (PNW) of unused headroom in those hours;
and that the arm tested here is refuted.

**NOT established, and not to be assumed:** that the envelope is *wrong*. A cap that binds is not
by itself a defect — CAISO's real interties are scheduled, not free. What makes it a live question
is its own matrix note, carried on `caiso_firm_selfsched_floor` since caiso-150: *"the floor's
shape basis is still EIA-930 **realised net** corridor interchange — **the wrong object in kind**,
with NO admissible measured replacement … any successor needs a new direction-splitting source,
adjudicated unreachable from the public feed at caiso-150 §H."* A **net**-interchange envelope
understates **gross** import capability in any hour with simultaneous exports, and it is an
*outcome* series being used as a *capability* cap. Whether the measured actual import on
Dec 29–31 2022 exceeded 7,482.8 MW is **the next measurement**, and it is zero-LP: the EIA-930
CISO interchange record is already committed.

**Rule 1 `[R-STRUCT]`:** nothing is selected here. §5 names the open question; it does not propose
relaxing a cap to close a residual, and a cap must never be widened because the residual wants it.

## §6 — RETENTION, AND ONE HONEST LOSS

* **Arm A is retrievable with zero re-solve.** Bundle `caiso279_ablate_dswcouple_2022`, 16 files
  incl. the per-plant `dispatch/` layer, at immutable SHA
  **`b17ac9d0f8b505d542f279356d5300888c69a70f`** (rule 33(d)):
  `git checkout b17ac9d0f8b505d542f279356d5300888c69a70f -- results/calibration/caiso279_ablate_dswcouple_2022`.
  Gitignored locally so it never reaches `main` (rule 29(c)); **not deleted** (rule 31).
* **Arm B's bundle is LOST unless its container is used.** The 2023–2025 span solved, but its
  272 MB push **did not land** — `claude/caiso279-arm-span` does not exist on the remote, and
  `36ce217` does not resolve. CLAUDE.md's Git & Pushing section says exactly this: `git push` is
  not licensed for a full bundle directory; the remote rejects large **packs**. The shard reported
  success because it did not verify the ref afterwards. **Its container is deliberately left
  ALIVE** (rule 33(a)/(b)) — it is the only thing that can re-push — but this session has **no
  messaging path to a cloud shard** (no `send_message` tool in its toolset and `ListAgents` shows
  no reachable peer), so it could not be instructed. Cost if the owner wants those years:
  ~35–55 min of LP. The arm is refuted, so nothing in the verdict depends on it.
* **Shard-prompt defect to carry forward:** a shard prompt must require
  `git ls-remote --heads origin | grep <branch>` **after** the push, and must instruct the slim
  set (exclude `dispatch/`, `floors/`, `*.npz`, `unit_hourly_*`) for any multi-year bundle.

## §7 — RULE LEDGER

| rule | discharge |
|---|---|
| 1 `[R-STRUCT]` | Arm refuted on its own pre-registered G-DIR, not on the residual; factor not resized; no lever selected in §5. |
| 12 / 32 `[R-SHARD]` | Parent spent zero LP; two shards, one invocation each, years sequential. |
| 15 `[R-DASHBOARD]` | A refuted screen bundle is never registered (rule 29(2)); every number it will ever be cited for is in this document. |
| 25 `[R-ISO-SCOPE]` | CAISO only. |
| 28(b) | `caiso_import_gas_coupling` CAISO cell takes this session's evidence; **verdict unchanged at K** — the mechanism stays armed, only the ablation is refuted. |
| 29 `[R-SCREEN]` | Screen year pre-registered on the operand footprint; the screen KILLED the arm and the remaining years were not spent on it. |
| 31 `[R-RETAIN]` | Nothing deleted. Arm A pinned by SHA; arm B's loss and its cost stated rather than tidied away. |
| 33 `[R-SHARD-ARCHIVE]` | Arm A fetched, checked out, verified, then archived. Arm B left alive, and §6 says why. |
| 34 `[R-SHARD-PROMOTABLE]` | Arm A's bundle is pushed and promotable; arm B's is not, and §6 states that at the time of discovery with its re-solve cost. |
