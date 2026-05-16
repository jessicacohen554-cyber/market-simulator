# Decision Log

## 2026-05-16: Fleet Binning Required for LP Performance

**Decision:** Fleet builder must aggregate units into representative bins
(fuel type × efficiency class × zone). Target: ≤50 thermal generators per ISO.

**Rationale:** At 300 individual generators, HiGHS solves in ~47s (far above
5s target). At 36 representative generators, solve time is ~5-10s.

## 2026-05-16: Sigmoid Retirement Replaced with Fuel-Aware Economic Retirement

**Decision:** Replaced sigmoid-based thermal retirement with fuel-aware
economic retirement that evaluates each unit's net revenue vs going-forward cost.

**Rationale:** Sigmoid applied uniform retirement pressure across all thermal.
Fuel-aware approach retires least-efficient units first within each fuel class,
matching standard production cost model practice.
