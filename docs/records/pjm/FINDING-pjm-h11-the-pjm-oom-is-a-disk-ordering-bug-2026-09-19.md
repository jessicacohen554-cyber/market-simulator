# FINDING — the PJM shard OOM is a DISK-ORDERING bug, not a memory bug. MISO's fix is sound; PJM runs it too late. (pjm-h11, 2026-09-19)

**Session:** pjm-h11 · **Branch:** `claude/pjm-h11-calibration-tuning-mwod34` · **ZERO LP MINUTES**
(rule 32 `[R-SHARD]` (a)) — this is a code-and-arithmetic reading, no solve.
**Owner ask:** *"If they keep OOM then we should figure out a fix.. check what's done for miso."*

---

## 1. Answer, up front

**MISO's fix works and is already wired into the PJM path. PJM defeats it by spending the disk the
fix needs, before the fix runs.**

The swapfile that makes a per-plant ISO-year LP survivable is **sized from free disk at the moment
it is provisioned**, and the runner provisions it **at solve time** — *after* a PJM shard has
hydrated 6.5 GiB of `data/raw`, built `data/clean`, and fetched the DA-virtuals corpus. MISO's
working lane provisioned it **first**, when the disk was still free, and got **10 GiB** of swap.
pjm-h10's shard provisioned it last and got **5.0 GiB**, which is **6.9 GiB short of what the
target needs** — and it was OOM-killed.

**The fix needs no code change: run `scripts/prepare_solve_container.py` as the FIRST step of a PJM
shard, before hydration.** It is idempotent, so the runner's own later call then keeps it.

---

## 2. What is done for MISO, and that it is sound

`scripts/lib/solve_container.py::ensure_solve_container`, called automatically by
`run_calibration_full.solve_and_persist` (hence `replay_keeper.py`) and `run_calibration.main`
since miso-254 (2026-09-12). It (a) reads the **binding** nested-cgroup ceiling rather than `free`
or `MemTotal`, (b) provisions a swapfile at `/swapfile-marketsim` up to a **24 GiB ceiling+swap
target**, and (c) pins `MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1`.
None of it touches the LP optimum, so it is correctly not a `ScenarioConfig` tunable (rule 24).

miso-254 proved the mechanism with a pre-registered A/B on one SHA:

| shard | preflight | swap provisioned | outcome |
|---|---|---|---|
| A | ON (as shipped) | 0 → **10 GiB** → ceiling+swap **23.3 GiB** (of the 24 target) | **finished** |
| B | `--no-container-preflight` | 0 | **OOM-killed** ~85 s in, `CONSTRAINT_MEMCG` |

So the MISO answer is not in doubt, and the "13.30 GiB peak" figure everyone quotes is **the
ceiling, not the demand** — a swapped run and an OOM-killed run both report it.

**Independently re-verified here, and it kills the obvious rival explanation.** pjm-h10 suspected
the cgroup was forbidden to swap (`memory.memsw.limit_in_bytes` "unreadable"). Read directly in this
container's own binding cgroup, `/sys/fs/cgroup/memory/process_api/<id>/claude-code-bash`:

```
memory.limit_in_bytes      = 14345912320   (13.36 GiB — the binding ceiling)
memory.memsw.limit_in_bytes = 9223372036854771712   (UNLIMITED)
memory.swappiness          = 60
```

**memsw is unlimited and swappiness is normal**, so the cgroup may swap freely. Swap accounting is
not the blocker, and nobody should re-hunt it.

---

## 3. The actual mechanism, from the code

`solve_container.provision_swap`, the sizing line:

```python
add_gib = int(min(deficit_gib, max(0.0, free_gib - disk_reserve_gib)))   # DISK_RESERVE_GIB = 6
```

Two properties decide everything:

1. **The swapfile is bounded by free disk minus a 6 GiB reserve, measured when it runs.**
2. **It is idempotent in the one direction that hurts** — an already-active swapfile is *kept as it
   is*, never grown:
   ```python
   if _swapfile_active(swapfile, proc):
       warnings.append("... already active ... leaving it as it is")
       return 0, warnings
   ```
   So a swapfile made too small early is never topped up later.

Now the arithmetic, on the measured numbers:

| | free disk when provisioned | `free − 6` | deficit to the 24 GiB target | swap actually added | ceiling+swap |
|---|---|---|---|---|---|
| **MISO, provisioned FIRST** | ~19–20 GiB | ~13–14 GiB | 10.64 GiB | **10 GiB** (deficit-bound) | **23.3 GiB** ✅ |
| **pjm-h10, provisioned LAST** | ~11 GiB | ~5 GiB | 10.64 GiB | **5 GiB** (disk-bound) | **18.4 GiB** ❌ |

A PJM shard's hydration footprint is what moves it from the first row to the second — measured in
this container, `data/raw` at the `pjm` profile is **6.5 GiB**, plus `data/clean` and the
licensing-gitignored DA-virtuals corpus on top.

**This reproduces pjm-h10's observations exactly, including the two that looked paradoxical:**

* preflight **printed its own warning and ran anyway** — *"ceiling+swap 18.4 GiB is below the 24 GiB
  target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here"*. That is the disk-bound
  branch firing, correctly, and the run proceeding on a container the code had already judged
  inadequate;
* **5.0 GiB of swap sat with `/proc/swaps` Used = 0 at the kill.** With only 5 GiB of headroom over a
  13.36 GiB ceiling, the HiGHS allocation burst in the P0→P1 seam outruns reclaim: the kernel
  SIGKILLs under `CONSTRAINT_MEMCG` rather than paging out in time. Swap that is too small is not a
  gentler failure — it is the same failure.

---

## 4. The fix

**Run the preflight FIRST, before any hydration**, so it sizes against a full disk:

```
sudo python3 scripts/prepare_solve_container.py      # or: eval "$(... --emit-exports)"
# ...only then: uv sync, hydrate_data.py --profile pjm, curates, fetch_pjm_da_virtuals.py
```

At that point `free ≈ 19–20 GiB`, so `free − 6 ≈ 13–14 GiB` exceeds the 10.64 GiB deficit and the
**full** amount is provisioned — MISO's working configuration, reached on PJM. Being idempotent, the
runner's own later `ensure_solve_container` call then finds it active and keeps it.

**This is exactly what the MISO fuelvintage lane did** (its prompt pack cited
`prepare_solve_container.py` as an explicit setup step) and exactly what the PJM shard prompts did
not — **mine included**, which is recorded here as this session's own error, not someone else's.

### 4.1 Why the prompts stopped doing it — a rule that is subtly wrong for a heavy-hydration ISO

Rule 32 `[R-SHARD]` (c)(8) currently tells a lane the opposite, in as many words:

> *"The runners now do it themselves … A shard prompt therefore names NO memory recipe of its own
> beyond: run the runner unmodified, never pass `--no-container-preflight`, and REPORT the
> `container preflight:` and `memory peak:` log lines."*

That is right about **whether** the container gets provisioned and wrong about **when**. For an ISO
whose setup spends ~7+ GiB of disk before the first loader, "the runner does it itself" means "the
runner does it after the disk is gone".

**PROPOSED AMENDMENT — for the owner, not self-applied** (rule 32 is governance):

> **(c)(8) addendum.** On an ISO whose `DATA PROFILE` hydration plus clean-tree build exceeds ~4 GiB
> — PJM and MISO at least — the shard prompt's FIRST action after the SHA check is
> `sudo python3 scripts/prepare_solve_container.py`, **before** hydration. The swapfile is sized
> from free disk (`free − 6 GiB`) at the moment it is created and is never grown afterwards, so
> provisioning it after hydration silently caps it several GiB below the target and the runner's
> own warning becomes unactionable.

A code-side alternative, which the owner may prefer because it cannot be forgotten: have
`provision_swap` **grow** an active-but-undersized swapfile (add a second swapfile rather than
returning early), so the ordering stops mattering. That is a real change to a solve-path module and
is not made here.

---

## 5. Status of this lane's 12 shards, and what it does NOT change

The 12 single-year shards now running were launched **before** this was diagnosed, so **none of them
runs the preflight first** — they carry the rule-32(c)(8) wording. They are therefore in pjm-h10's
configuration and some may be OOM-killed. At the time of writing they are past setup and solving
(CTL 2020 polling solve progress; ARM 2020 reading its preflight and seam lines), so the outcome is
open rather than lost. Two things make this survivable that the span attempt did not have: a kill now
costs **one year** rather than a whole span, and a relaunch of that one year can carry the corrected
ordering.

**There is no way to correct a running shard** — there is no messaging route from a CCR parent to a
CCR shard (pjm-h10 ADDENDUM §3), so the prompt is the only channel and it is already spent. The
remedy is applied on relaunch.

---

## 5b. UPDATE, ~25 MINUTES LATER — THE LIVE SHARDS CONFIRM §3 AND DE-CONFOUND Q3

Both halves of §3 are now **measured on this lane's own containers**, not inferred:

**(i) The disk bound is real and it is biting every shard.** CTL 2022 reports *"5 GiB swap
provisioned (18.4 target)"* and CTL 2024 *"~5 GiB swap"* — **5 GiB, not the 10 GiB MISO's working
shard got**, and a `ceiling+swap` of **18.4 GiB**, reproducing pjm-h10's number exactly. §3's
arithmetic predicted this before any shard reported it.

**(ii) The LP itself FITS. What does not fit is the post-solve window.** **CTL 2020 COMPLETED** on a
13.36 GiB ceiling with a 13.36 GiB peak — so a PJM per-plant year is survivable here even
under-provisioned. **CTL 2021 was OOM-killed, and its own report localises the kill:**

> *"PJM control 2021 solve failed on OOM during post-solve `marginal_emission_rate` extraction; no
> bundle written; container ceiling 13.36 GiB insufficient"* — recommending *"re-launch with larger
> container ceiling (>18.36 GiB) OR escalate code fix to ungated `h.run()` at `model.py:1660`."*

**The solve finished and the process died afterwards, inside the MER dual.** That is the phase
localisation pjm-h10 could not get, and it changes Q3's status: the dual is no longer merely a
*candidate* contributor, it is where the kill lands when the kill happens.

**Stated carefully, because I primed this shard.** Its prompt told it the dual was new, ungated, and
in the window a previous shard died in, so its *attribution* is not independent. What is independent
is the **phase**, which it read from its own log: solve complete, then killed in MER extraction.
Treat the phase as evidence and the blame as corroboration.

**So the two explanations are not rivals — they compose, and the order matters:**
the LP fits at 13.36 GiB; the MER dual then demands more on top of a completed solve; and the
under-provisioned 5 GiB swap removes the headroom that would have absorbed it. That predicts the
observed split — CTL 2020 finishes, CTL 2021 dies — because how far the dual pushes past the ceiling
varies by year, and 18.4 GiB of ceiling+swap sits right at the boundary. It also says **both**
remedies work and they are independent: restore the swap (§4, free), or gate the dual (Q3, a code
change and the owner's call).

**Action taken:** CTL 2021 relaunched as `session_01553U34CaoGg7uKj6JgBCHn` with §4's fix — the
**only** change is `sudo python3 scripts/prepare_solve_container.py` moved to STEP 0, before
hydration. It is instructed to report `cat /proc/swaps` **after** the solve, because *swap actually
USED* — not merely present — is the one number that would settle whether a bigger swapfile is
sufficient on its own. The dead shard is archived (rule 33); it wrote no bundle and no branch, so
its `post_turn_summary`, quoted above, is the whole of its record.

**Status at this update: 11 of 12 shards alive, 1 dead and relaunched.**

---

## 6. Ledger

Nothing armed, no `ScenarioConfig` field, no default flipped, no mechanism-matrix cell moved, no run
registered, no keeper touched, no code changed. Zero LP minutes. Rule 31 `[R-RETAIN]`: nothing
deleted.
