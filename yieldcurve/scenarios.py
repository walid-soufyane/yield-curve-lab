"""Curve scenarios and portfolio P&L: full revaluation vs key-rate-duration approximation.

Scenarios are additive zero-rate shifts s(t), in decimal (0.01 = 100bp):
    parallel(bp)          s(t) = bp
    twist(bp, pivot)      s(t) = bp * (t - pivot) / (30 - pivot), capped at +/- bp
                          (bp > 0 steepens: short end down, long end up)
    butterfly(bp)         wings (2Y, 30Y) up, belly (10Y) down
"""

from dataclasses import dataclass

import numpy as np

from .key_rates import KEY_TENORS, ShiftedCurve, key_rate_durations, price_from_curve


def parallel(bp):
    return lambda t: np.full_like(np.asarray(t, dtype=float), bp * 1e-4)


def twist(bp, pivot=5.0):
    def s(t):
        t = np.asarray(t, dtype=float)
        lo = (t - pivot) / (pivot - 0.25)  # -1 at 3M
        hi = (t - pivot) / (30 - pivot)    # +1 at 30Y
        return bp * 1e-4 * np.clip(np.where(t < pivot, lo, hi), -1, 1)
    return s


def butterfly(bp):
    return lambda t: bp * 1e-4 * np.interp(np.asarray(t, dtype=float), [2, 10, 30], [1, -1, 1])


@dataclass
class Position:
    notional: float     # face amount held (negative = short)
    coupon_rate: float
    maturity: float
    freq: int = 2


def portfolio_value(curve, positions):
    return sum(p.notional / 100 * price_from_curve(curve, 100, p.coupon_rate, p.maturity, p.freq) for p in positions)


def scenario_pnl(curve, positions, shift, tenors=KEY_TENORS):
    """Return (full-revaluation P&L, KRD first-order estimate) for a shift function."""
    v0 = portfolio_value(curve, positions)
    full = portfolio_value(ShiftedCurve(curve, shift), positions) - v0
    approx = 0.0
    for p in positions:
        price = price_from_curve(curve, 100, p.coupon_rate, p.maturity, p.freq)
        krd, _ = key_rate_durations(curve, 100, p.coupon_rate, p.maturity, p.freq, tenors)
        dz = shift(np.asarray(tenors, dtype=float))
        approx += -p.notional / 100 * price * sum(krd[k] * d for k, d in zip(tenors, dz))
    return full, float(approx)
