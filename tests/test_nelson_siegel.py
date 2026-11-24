import numpy as np
import pytest

from yieldcurve import ParametricCurve, fit_nelson_siegel, fit_svensson

T = np.array([0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])


def test_limits_short_and_long_end():
    c = ParametricCurve(np.array([0.045, -0.015, 0.01]), (2.0,))
    assert c.zero_rate(1e-12)[0] == pytest.approx(0.045 - 0.015)
    assert c.zero_rate(1e6)[0] == pytest.approx(0.045, abs=1e-5)


def test_recovers_true_nelson_siegel_parameters():
    true = ParametricCurve(np.array([0.042, -0.012, 0.018]), (1.7,))
    fit = fit_nelson_siegel(T, true.zero_rate(T))
    assert fit.taus[0] == pytest.approx(1.7, rel=1e-5)
    assert np.allclose(fit.betas, true.betas, atol=1e-7)


def test_svensson_fits_at_least_as_well_and_captures_double_hump():
    true = ParametricCurve(np.array([0.04, -0.01, 0.03, -0.02]), (0.8, 6.0))
    y = true.zero_rate(T)
    ns, sv = fit_nelson_siegel(T, y), fit_svensson(T, y)
    rmse = lambda c: np.sqrt(np.mean((c.zero_rate(T) - y) ** 2))
    assert rmse(sv) < 1e-7 < rmse(ns)


def test_fit_to_bootstrapped_curve():
    from test_bootstrap import MARKET
    from yieldcurve import bootstrap

    curve = bootstrap(MARKET, "log_linear_df")
    fit = fit_nelson_siegel(curve.times, curve.rates)
    # a 3-factor curve should explain the bootstrapped zeros to within a few bp
    assert np.max(np.abs(fit.zero_rate(curve.times) - curve.rates)) < 5e-4
