# Yield Curve Lab

[![tests](https://github.com/walid-soufyane/yield-curve-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/walid-soufyane/yield-curve-lab/actions/workflows/tests.yml)

Fixed-income toolkit in Python: bond pricing, risk measures, and building a zero-coupon yield curve from market instruments.

## Current features
- Cash flows of fixed-coupon bullet bonds
- Pricing from a flat yield (any compounding frequency)
- Yield to maturity via Brent root-finding
- Risk measures: Macaulay and modified duration, convexity (analytic), DV01, duration-convexity price-change approximation
- Zero-curve bootstrapping from deposits and par swaps (each input reprices to par to 1e-12)
- Interpolation: linear zero rates, log-linear discount factors (piecewise-flat forwards), natural cubic spline (solved globally, since a spline is non-local)
- Forward rates: term forwards F(t1, t2) and instantaneous forwards f(t)
- Tests: par bonds at face, closed forms, YTM round trip, numerical derivatives, repricing of every input instrument, forward/discount consistency. Run on every push by GitHub Actions

## Quick start
```python
from yieldcurve import price_from_yield, yield_to_maturity

p = price_from_yield(face=100, coupon_rate=0.045, maturity=7, ytm=0.04)
print(p, yield_to_maturity(p, 100, 0.045, 7))
```

```python
from yieldcurve import Deposit, ParSwap, bootstrap

market = [Deposit(0.25, 0.042), Deposit(1.0, 0.0405), ParSwap(2, 0.039), ParSwap(5, 0.0378),
          ParSwap(10, 0.039), ParSwap(30, 0.041)]
curve = bootstrap(market, method="cubic_spline")
print(curve.zero_rate(7), curve.forward_rate(5, 10))  # 7y zero, 5y5y forward
```

Run tests: `pip install -r requirements.txt && pytest`

## Risk example
10-year 5% semi-annual bond at a 4.5% yield:

| Measure | Value |
|---|---|
| Price | 103.99 |
| Macaulay duration | 8.04 years |
| Modified duration | 7.86 |
| Convexity | 74.55 |
| DV01 (per 100 face) | 0.0817 |

## Bootstrapping example
Deposits (3M–1Y) and semi-annual par swaps (2Y–30Y), zero rates in % (continuous compounding):

| Interpolation | 2Y | 5Y | 10Y | 30Y | 5y5y fwd |
|---|---|---|---|---|---|
| Linear zero | 3.859 | 3.739 | 3.876 | 4.140 | 4.012 |
| Log-linear DF | 3.860 | 3.740 | 3.875 | 4.116 | 4.011 |
| Cubic spline | 3.860 | 3.740 | 3.877 | 4.107 | 4.013 |

All three reprice the inputs exactly. They differ between nodes, most at the long end where nodes are sparse, and in how smooth the forward curve is.

## Roadmap
- [x] Bond cash flows, pricing and YTM
- [x] Macaulay/modified duration, convexity, DV01
- [x] Bootstrapping a zero curve from deposits, swaps and par bonds
- [x] Interpolation: linear zero rates, log-linear discount factors, cubic spline
- [x] Forward rates
- [ ] Nelson-Siegel / Svensson curve fitting
- [ ] Key-rate durations and parallel / twist scenario P&L
- [ ] Example notebook with real curve data
