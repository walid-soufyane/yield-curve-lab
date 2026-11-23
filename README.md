# Yield Curve Lab

Fixed-income toolkit in Python: bond pricing, risk measures, and building a zero-coupon yield curve from market instruments.

## Current features
- Cash flows of fixed-coupon bullet bonds
- Pricing from a flat yield (any compounding frequency)
- Yield to maturity via Brent root-finding
- Risk measures: Macaulay and modified duration, convexity (analytic), DV01, duration-convexity price-change approximation
- Tests: par bonds price at face, zero-coupon closed form, premium/discount, YTM round trip

## Quick start
```python
from yieldcurve import price_from_yield, yield_to_maturity

p = price_from_yield(face=100, coupon_rate=0.045, maturity=7, ytm=0.04)
print(p, yield_to_maturity(p, 100, 0.045, 7))
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

## Roadmap
- [x] Bond cash flows, pricing and YTM
- [x] Macaulay/modified duration, convexity, DV01
- [ ] Bootstrapping a zero curve from deposits, swaps and par bonds
- [ ] Interpolation: linear zero rates, log-linear discount factors, cubic spline
- [ ] Forward rates
- [ ] Nelson-Siegel / Svensson curve fitting
- [ ] Key-rate durations and parallel / twist scenario P&L
- [ ] Example notebook with real curve data
