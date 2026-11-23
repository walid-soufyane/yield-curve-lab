"""Zero-coupon curve and bootstrapping from deposits and par swaps/bonds.

The curve stores continuously compounded zero rates z(t) at node maturities. Discount factors
are P(t) = exp(-z(t) t). Between nodes z is interpolated linearly; before the first node it is
held flat.
"""

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq


class ZeroCurve:
    def __init__(self, times, zero_rates):
        t = np.asarray(times, dtype=float)
        z = np.asarray(zero_rates, dtype=float)
        if t.ndim != 1 or t.shape != z.shape or np.any(np.diff(t) <= 0) or t[0] <= 0:
            raise ValueError("times must be positive and strictly increasing, same length as rates")
        self.times, self.rates = t, z

    def zero_rate(self, t):
        return np.interp(np.asarray(t, dtype=float), self.times, self.rates)

    def discount(self, t):
        t = np.asarray(t, dtype=float)
        return np.exp(-self.zero_rate(t) * t)


@dataclass
class Deposit:
    """Money-market deposit: simple rate, single payment at maturity. P(T) = 1 / (1 + rate * T)."""
    maturity: float
    rate: float

    def pv(self, curve):
        return float(curve.discount(self.maturity) * (1 + self.rate * self.maturity))


@dataclass
class ParSwap:
    """Fixed leg of a par swap (or a par bond): coupons rate/freq, notional 1 repaid at maturity.

    At par:  sum_i (rate / freq) P(t_i) + P(T) = 1.
    """
    maturity: float
    rate: float
    freq: int = field(default=2)

    def pv(self, curve):
        n = int(round(self.maturity * self.freq))
        t = np.arange(1, n + 1) / self.freq
        return float(self.rate / self.freq * curve.discount(t).sum() + curve.discount(self.maturity))


def bootstrap(instruments):
    """Build a ZeroCurve that reprices every instrument to par (PV = 1), one node per maturity.

    Instruments are processed in order of maturity; for each one the zero rate at its maturity is
    solved with Brent's method, keeping the earlier nodes fixed. Coupons that fall between nodes
    use the interpolated curve, so the problem stays one-dimensional at each step.
    """
    instruments = sorted(instruments, key=lambda x: x.maturity)
    times, rates = [], []
    for inst in instruments:
        if times and inst.maturity <= times[-1]:
            raise ValueError("instrument maturities must be distinct")

        def err(z):
            return inst.pv(ZeroCurve(times + [inst.maturity], rates + [z])) - 1.0

        rates.append(brentq(err, -0.5, 1.0, xtol=1e-15))
        times.append(inst.maturity)
    return ZeroCurve(times, rates)
