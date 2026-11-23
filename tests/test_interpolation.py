import numpy as np
import pytest

from yieldcurve import METHODS, ZeroCurve, bootstrap
from test_bootstrap import MARKET


@pytest.mark.parametrize("method", METHODS)
def test_every_method_reprices_the_market(method):
    curve = bootstrap(MARKET, method=method)
    for inst in MARKET:
        assert inst.pv(curve) == pytest.approx(1.0, abs=1e-10)


@pytest.mark.parametrize("method", METHODS)
def test_curve_passes_through_nodes(method):
    t, z = [1, 2, 5, 10], [0.03, 0.035, 0.04, 0.042]
    assert np.allclose(ZeroCurve(t, z, method).zero_rate(t), z, atol=1e-14)


def test_log_linear_df_has_constant_forwards_between_nodes():
    curve = ZeroCurve([1, 2, 5], [0.03, 0.035, 0.04], "log_linear_df")
    f = curve.instantaneous_forward(np.linspace(2.1, 4.9, 15))
    assert np.allclose(f, curve.forward_rate(2, 5), atol=1e-8)


def test_forward_rate_consistent_with_discount_factors():
    curve = bootstrap(MARKET, "cubic_spline")
    t1, t2 = 3.0, 7.0
    f = curve.forward_rate(t1, t2)
    assert curve.discount(t2) == pytest.approx(curve.discount(t1) * np.exp(-f * (t2 - t1)), rel=1e-12)


def test_spline_forwards_continuous_linear_forwards_jump():
    t, z = [1, 2, 5, 10], [0.03, 0.036, 0.039, 0.041]
    eps = 1e-3

    def jump(method):
        c = ZeroCurve(t, z, method)
        return abs(c.instantaneous_forward(5 + eps, 1e-6) - c.instantaneous_forward(5 - eps, 1e-6))

    assert jump("cubic_spline") < 1e-4
    assert jump("linear_zero") > 1e-3
