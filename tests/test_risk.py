import math

import pytest

from yieldcurve import (
    convexity,
    dv01,
    macaulay_duration,
    modified_duration,
    price_change_approx,
    price_from_yield,
)

BOND = dict(face=100, coupon_rate=0.05, maturity=10, ytm=0.045)


def test_zero_coupon_macaulay_equals_maturity():
    assert math.isclose(macaulay_duration(100, 0.0, 7, 0.03), 7.0, rel_tol=1e-12)


def test_coupon_bond_duration_below_maturity():
    assert macaulay_duration(**BOND) < BOND["maturity"]


def test_modified_duration_matches_numerical_derivative():
    h = 1e-6
    p = price_from_yield(**BOND)
    up = price_from_yield(100, 0.05, 10, BOND["ytm"] + h)
    down = price_from_yield(100, 0.05, 10, BOND["ytm"] - h)
    numeric = -(up - down) / (2 * h) / p
    assert math.isclose(modified_duration(**BOND), numeric, rel_tol=1e-6)


def test_convexity_matches_numerical_second_derivative():
    h = 1e-4
    y = BOND["ytm"]
    p = price_from_yield(**BOND)
    up = price_from_yield(100, 0.05, 10, y + h)
    down = price_from_yield(100, 0.05, 10, y - h)
    numeric = (up - 2 * p + down) / h**2 / p
    assert math.isclose(convexity(**BOND), numeric, rel_tol=1e-5)


def test_dv01_close_to_duration_times_price():
    p = price_from_yield(**BOND)
    assert math.isclose(dv01(**BOND), modified_duration(**BOND) * p * 1e-4, rel_tol=1e-6)


@pytest.mark.parametrize("dy", [-0.01, 0.01, 0.02])
def test_duration_convexity_approximation(dy):
    p0 = price_from_yield(**BOND)
    actual = price_from_yield(100, 0.05, 10, BOND["ytm"] + dy) - p0
    approx = price_change_approx(**BOND, dy=dy)
    # Second-order error is O(dy^3): within 1% of the move for shocks up to 200bp
    assert abs(approx - actual) < 0.01 * abs(actual)
