import math

import numpy as np
import pytest

from yieldcurve import Deposit, ParSwap, ZeroCurve, bootstrap

MARKET = [
    Deposit(0.25, 0.0420),
    Deposit(0.5, 0.0415),
    Deposit(1.0, 0.0405),
    ParSwap(2, 0.0390),
    ParSwap(3, 0.0382),
    ParSwap(5, 0.0378),
    ParSwap(7, 0.0381),
    ParSwap(10, 0.0390),
    ParSwap(30, 0.0410),
]


def test_reprices_every_input_instrument():
    curve = bootstrap(MARKET)
    for inst in MARKET:
        assert inst.pv(curve) == pytest.approx(1.0, abs=1e-12)


def test_deposit_node_closed_form():
    curve = bootstrap([Deposit(0.5, 0.05)])
    assert curve.zero_rate(0.5) == pytest.approx(math.log(1 + 0.05 * 0.5) / 0.5, rel=1e-12)


def test_flat_par_curve_gives_flat_zero_curve():
    y = 0.04
    curve = bootstrap([ParSwap(m, y) for m in (1, 2, 3, 5, 10)])
    # semi-annual par yield y on a flat curve <=> continuous zero rate 2 ln(1 + y/2)
    assert np.allclose(curve.rates, 2 * math.log(1 + y / 2), atol=1e-12)


def test_discount_factors_decrease():
    curve = bootstrap(MARKET)
    assert np.all(np.diff(curve.discount(np.linspace(0.25, 30, 200))) < 0)


def test_invalid_curve_inputs():
    with pytest.raises(ValueError):
        ZeroCurve([1, 1], [0.03, 0.03])
    with pytest.raises(ValueError):
        bootstrap([ParSwap(2, 0.04), ParSwap(2, 0.05)])
