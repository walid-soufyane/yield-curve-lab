# Yield Curve Lab

Fixed-income toolkit in Python: bond pricing, risk measures, and building a zero-coupon yield curve from market instruments.

## Current features
- Cash flows of fixed-coupon bullet bonds
- Pricing from a flat yield (any compounding frequency)
- Yield to maturity via Brent root-finding
- Tests: par bonds price at face, zero-coupon closed form, premium/discount, YTM round trip

## Quick start
```python
from yieldcurve import price_from_yield, yield_to_maturity

p = price_from_yield(face=100, coupon_rate=0.045, maturity=7, ytm=0.04)
print(p, yield_to_maturity(p, 100, 0.045, 7))
```

Run tests: `pip install -r requirements.txt && pytest`

## Roadmap
- [x] Bond cash flows, pricing and YTM
- [ ] Macaulay/modified duration, convexity, DV01
- [ ] Bootstrapping a zero curve from deposits, swaps and par bonds
- [ ] Interpolation: linear zero rates, log-linear discount factors, cubic spline
- [ ] Forward rates
- [ ] Nelson-Siegel / Svensson curve fitting
- [ ] Key-rate durations and parallel / twist scenario P&L
- [ ] Example notebook with real curve data
