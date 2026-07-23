"""NYISO 2023 off-peak marginal-unit FULL mc decomposition.

mc_base = hr*gas + vom + emission_rate*carbon.  Back out the effective gas
price of the off-peak marginal units and compare to actual Transco Z6 NY
($1.39 shoulder) / ISO-avg ($1.77). Settles whether the driver is gas basis,
heat rate, or VOM.
"""
import numpy as np

NPZ = "/tmp/nyiso_2023_markup_decomp.npz"
HPM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
CARBON = 13.49  # RGGI 2023 $/short ton


def main():
    d = np.load(NPZ, allow_pickle=True)
    p0 = d["p0_prices"]
    if p0.shape[0] > p0.shape[1]:
        p0 = p0.T
    T = p0.shape[1]
    pg = d["pg"]
    mc = d["mc_base_gen"]
    disp = d["p0_disp"]
    pmax = d["pmax"]
    avail = d["availability"]
    hr = d["heat_rate"]
    vom = d["vom"]
    emis = d["emission_rate"]
    uids = d["unit_ids"]
    moh = np.repeat(np.arange(1, 13), [h * 24 for h in HPM])[:T]
    hod = np.tile(np.arange(24), T // 24 + 1)[:T]
    eff_cap = pmax[:, None] * avail
    mask = np.isin(moh, [5, 6, 8]) & (hod <= 6)
    ref = p0[3]  # NYC price (downstate, where marginal lives)

    # effective gas per gen per hour = (mc - vom - emis*carbon) / hr
    with np.errstate(divide="ignore", invalid="ignore"):
        eff_gas = (mc - vom[:, None] - emis[:, None] * CARBON) / hr[:, None]

    running = (disp > 0.05 * eff_cap) & (disp < 0.98 * eff_cap)
    print("=== Off-peak shoulder marginal units: full MC decomposition ===")
    print(f"  (actual Transco Z6 NY shoulder gas = $1.39; ISO-avg = $1.77)")
    rows = {}
    for t in np.where(mask)[0]:
        cand = np.where(running[:, t])[0]
        if len(cand) == 0:
            continue
        g = cand[np.argmin(np.abs(mc[cand, t] - ref[t]))]
        c = str(pg[g])
        rows.setdefault(c, []).append(
            (mc[g, t], hr[g], vom[g], emis[g] * CARBON, eff_gas[g, t], str(uids[g]))
        )
    print(f"{'class':>12} {'n':>4} {'mc':>7} {'hr':>6} {'gas':>6} {'fuel$':>7} "
          f"{'vom':>5} {'carbon':>6}")
    for c, lst in sorted(rows.items(), key=lambda r: -len(r[1])):
        a = np.array([(r[0], r[1], r[2], r[3], r[4]) for r in lst], dtype=float)
        n = len(a)
        gas = a[:, 4]
        print(f"{c:>12} {n:>4} {a[:, 0].mean():>7.2f} {a[:, 1].mean():>6.2f} "
              f"{gas[np.isfinite(gas)].mean():>6.2f} {(a[:, 1] * gas)[np.isfinite(gas)].mean():>7.2f} "
              f"{a[:, 2].mean():>5.2f} {a[:, 3].mean():>6.2f}")

    # sample the actual marginal ST_GAS units (names)
    print("\n=== sample marginal ST_GAS unit-hours (uid, mc, hr, eff_gas) ===")
    st = [r for c, lst in rows.items() if c == "ST_GAS" for r in lst]
    seen = set()
    for mcv, h, v, cb, g, uid in sorted(st, key=lambda r: -r[0])[:12]:
        base = uid.rsplit("_", 1)[0]
        if base in seen:
            continue
        seen.add(base)
        print(f"  {uid:>34} mc {mcv:6.2f} hr {h:5.2f} gas {g:5.2f}")


if __name__ == "__main__":
    main()
