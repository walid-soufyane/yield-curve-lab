"""Pricing off a zero curve, curve shifts, and key-rate durations.

A key-rate shift moves the zero curve by 1bp at one key tenor k, tapering linearly to zero at
the neighbouring key tenors (a "tent"). The tents sum to a parallel shift, so the key-rate
durations sum to the bond's effective duration and show *where* on the curve its risk sits.
"""

import numpy as np

from .bonds import cash_flows

KEY_TENORS = (0.25, 1, 2, 3, 5, 7, 10, 20, 30)


class ShiftedCurve:
    """A curve plus an additive zero-rate shift function s(t)."""

    def __init__(self, base, shift):
        self.base, self.shift = base, shift

    def zero_rate(self, t):
        t = np.asarray(t, dtype=float)
        return self.base.zero_rate(t) + self.shift(t)

    def discount(self, t):
        t = np.asarray(t, dtype=float)
        return np.exp(-self.zero_rate(t) * t)


def price_from_curve(curve, face, coupon_rate, maturity, freq=2):
    """Price a bullet bond by discounting each cash flow on the zero curve."""
    t, cf = cash_flows(face, coupon_rate, maturity, freq)
    return float(cf @ curve.discount(t))


def tent(k_index, tenors=KEY_TENORS):
    """Shift function equal to 1 at tenors[k_index], linear to 0 at its neighbours, flat beyond the ends."""
    y = np.zeros(len(tenors))
    y[k_index] = 1.0
    return lambda t: np.interp(np.asarray(t, dtype=float), tenors, y)


def key_rate_durations(curve, face, coupon_rate, maturity, freq=2, tenors=KEY_TENORS, bp=1e-4):
    """Key-rate durations  KRD_k = -(P(+bp tent_k) - P(-bp tent_k)) / (2 bp P).

    Returns (dict tenor -> KRD, effective duration from a parallel shift).
    """
    p0 = price_from_curve(curve, face, coupon_rate, maturity, freq)

    def dur(shape):
        up = price_from_curve(ShiftedCurve(curve, lambda t: bp * shape(t)), face, coupon_rate, maturity, freq)
        dn = price_from_curve(ShiftedCurve(curve, lambda t: -bp * shape(t)), face, coupon_rate, maturity, freq)
        return -(up - dn) / (2 * bp * p0)

    krd = {k: dur(tent(i, tenors)) for i, k in enumerate(tenors)}
    effective = dur(lambda t: np.ones_like(np.asarray(t, dtype=float)))
    return krd, effective
