"""Interest-rate risk measures for a fixed-coupon bond priced from a flat yield.

Conventions: yield y compounded `freq` times per year, cash flow times t_i in years,
discount factor (1 + y/freq)^(-freq * t_i).
"""

import numpy as np

from .bonds import cash_flows, price_from_yield


def macaulay_duration(face, coupon_rate, maturity, ytm, freq=2):
    """Present-value-weighted average time to cash flows, in years."""
    t, cf = cash_flows(face, coupon_rate, maturity, freq)
    pv = cf * (1 + ytm / freq) ** (-freq * t)
    return float((t * pv).sum() / pv.sum())


def modified_duration(face, coupon_rate, maturity, ytm, freq=2):
    """-(1/P) dP/dy = Macaulay duration / (1 + y/freq)."""
    return macaulay_duration(face, coupon_rate, maturity, ytm, freq) / (1 + ytm / freq)


def convexity(face, coupon_rate, maturity, ytm, freq=2):
    """(1/P) d^2P/dy^2, computed analytically."""
    t, cf = cash_flows(face, coupon_rate, maturity, freq)
    n = freq * t  # number of periods to each cash flow
    pv = cf * (1 + ytm / freq) ** (-n)
    d2 = (pv * n * (n + 1)).sum() / (freq**2 * (1 + ytm / freq) ** 2)
    return float(d2 / pv.sum())


def dv01(face, coupon_rate, maturity, ytm, freq=2):
    """Price fall for a 1bp rise in yield, by central difference (positive for a long bond)."""
    h = 1e-4
    up = price_from_yield(face, coupon_rate, maturity, ytm + h, freq)
    down = price_from_yield(face, coupon_rate, maturity, ytm - h, freq)
    return float((down - up) / 2)


def price_change_approx(face, coupon_rate, maturity, ytm, dy, freq=2):
    """Second-order Taylor estimate of the price change for a yield move dy."""
    p = price_from_yield(face, coupon_rate, maturity, ytm, freq)
    d = modified_duration(face, coupon_rate, maturity, ytm, freq)
    c = convexity(face, coupon_rate, maturity, ytm, freq)
    return float(p * (-d * dy + 0.5 * c * dy**2))
