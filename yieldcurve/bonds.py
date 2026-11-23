"""Fixed-coupon bond cash flows, pricing from a flat yield, and yield to maturity."""

import numpy as np
from scipy.optimize import brentq


def cash_flows(face, coupon_rate, maturity, freq=2):
    """Times (in years) and amounts of a bullet bond's cash flows.

    Assumes maturity is a whole number of coupon periods.
    """
    n = int(round(maturity * freq))
    if n <= 0 or not np.isclose(n / freq, maturity):
        raise ValueError("maturity must be a positive multiple of 1/freq")
    times = np.arange(1, n + 1) / freq
    amounts = np.full(n, face * coupon_rate / freq)
    amounts[-1] += face
    return times, amounts


def price_from_yield(face, coupon_rate, maturity, ytm, freq=2):
    """Dirty price on a coupon date, discounting at yield ytm compounded freq times per year."""
    times, amounts = cash_flows(face, coupon_rate, maturity, freq)
    disc = (1 + ytm / freq) ** (-times * freq)
    return float(amounts @ disc)


def yield_to_maturity(price, face, coupon_rate, maturity, freq=2):
    """Solve price_from_yield(ytm) = price for ytm with Brent's method."""
    f = lambda y: price_from_yield(face, coupon_rate, maturity, y, freq) - price
    return float(brentq(f, -0.99 * freq, 10.0, xtol=1e-14))
