import math

import pytest

from yieldcurve import cash_flows, price_from_yield, yield_to_maturity


def test_cash_flows_shape():
    t, cf = cash_flows(100, 0.05, 2, freq=2)
    assert list(t) == [0.5, 1.0, 1.5, 2.0]
    assert list(cf) == [2.5, 2.5, 2.5, 102.5]


def test_par_bond_prices_at_face():
    # Coupon = yield  =>  price = face
    assert math.isclose(price_from_yield(100, 0.04, 10, 0.04), 100.0, rel_tol=1e-12)


def test_zero_coupon_closed_form():
    p = price_from_yield(100, 0.0, 5, 0.03, freq=1)
    assert math.isclose(p, 100 / 1.03**5, rel_tol=1e-12)


def test_premium_and_discount():
    assert price_from_yield(100, 0.06, 10, 0.04) > 100
    assert price_from_yield(100, 0.02, 10, 0.04) < 100


@pytest.mark.parametrize("y", [0.001, 0.035, 0.08])
def test_ytm_round_trip(y):
    p = price_from_yield(100, 0.045, 7, y)
    assert math.isclose(yield_to_maturity(p, 100, 0.045, 7), y, abs_tol=1e-10)
