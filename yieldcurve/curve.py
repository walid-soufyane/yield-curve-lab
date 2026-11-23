"""Zero-coupon curve and bootstrapping from deposits and par swaps/bonds.

The curve stores continuously compounded zero rates z(t) at node maturities. Discount factors
are P(t) = exp(-z(t) t). Interpolation between nodes:

    "linear_zero"    z(t) linear between nodes (simple, but forward curve has a sawtooth)
    "log_linear_df"  ln P(t) linear, i.e. piecewise-constant instantaneous forwards
    "cubic_spline"   natural cubic spline on z(t): smooth zero and forward curves

Outside the node range the zero rate is held flat.
"""

from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq, root

METHODS = ("linear_zero", "log_linear_df", "cubic_spline")


class ZeroCurve:
    def __init__(self, times, zero_rates, method="linear_zero"):
        t = np.asarray(times, dtype=float)
        z = np.asarray(zero_rates, dtype=float)
        if t.ndim != 1 or t.shape != z.shape or np.any(np.diff(t) <= 0) or t[0] <= 0:
            raise ValueError("times must be positive and strictly increasing, same length as rates")
        if method not in METHODS:
            raise ValueError(f"method must be one of {METHODS}")
        self.times, self.rates, self.method = t, z, method
        if method == "cubic_spline" and len(t) >= 3:
            self._spline = CubicSpline(t, z, bc_type="natural")
        elif method == "cubic_spline":
            self.method = "linear_zero"  # a spline needs at least 3 nodes

    def zero_rate(self, t):
        t = np.asarray(t, dtype=float)
        inside = np.clip(t, self.times[0], self.times[-1])
        if self.method == "linear_zero":
            return np.interp(inside, self.times, self.rates)
        if self.method == "cubic_spline":
            return self._spline(inside)
        # log-linear discount factors through (0, 0) and the nodes; flat zero beyond the last node
        log_p = np.interp(np.minimum(t, self.times[-1]), np.r_[0.0, self.times], np.r_[0.0, -self.rates * self.times])
        z = -log_p / np.where(t > 0, np.minimum(t, self.times[-1]), 1.0)
        return np.where(t > self.times[-1], self.rates[-1], z)

    def forward_rate(self, t1, t2):
        """Continuously compounded forward rate for borrowing from t1 to t2: ln(P(t1)/P(t2)) / (t2 - t1)."""
        t1, t2 = np.asarray(t1, dtype=float), np.asarray(t2, dtype=float)
        return (np.log(self.discount(t1)) - np.log(self.discount(t2))) / (t2 - t1)

    def instantaneous_forward(self, t, h=1e-5):
        """f(t) = d/dt [z(t) t], by central difference."""
        t = np.asarray(t, dtype=float)
        return self.forward_rate(t - h, t + h)

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


def bootstrap(instruments, method="linear_zero"):
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
            return inst.pv(ZeroCurve(times + [inst.maturity], rates + [z], method)) - 1.0

        rates.append(brentq(err, -0.5, 1.0, xtol=1e-15))
        times.append(inst.maturity)

    if method == "cubic_spline" and len(times) >= 3:
        # A spline is non-local: adding a node moves the curve before it, so the sequential pass
        # only gives a starting point. Solve all nodes jointly so every instrument reprices.
        def residuals(z):
            c = ZeroCurve(times, z, method)
            return [inst.pv(c) - 1.0 for inst in instruments]

        sol = root(residuals, rates, method="hybr", tol=1e-14)
        if not sol.success:
            raise RuntimeError(f"global spline bootstrap failed: {sol.message}")
        rates = list(sol.x)
    return ZeroCurve(times, rates, method)
