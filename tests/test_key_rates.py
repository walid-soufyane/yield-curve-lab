import math

import numpy as np
import pytest

from yieldcurve import (
    KEY_TENORS,
    ZeroCurve,
    bootstrap,
    key_rate_durations,
    price_from_curve,
    price_from_yield,
)
from test_bootstrap import MARKET

CURVE = bootstrap(MARKET, "log_linear_df")


def test_flat_curve_matches_yield_pricing():
    # flat continuous zero z <=> semi-annual yield 2(e^{z/2} - 1)
    z = 0.04
    flat = ZeroCurve([0.5, 30], [z, z])
    y = 2 * (math.exp(z / 2) - 1)
    assert price_from_curve(flat, 100, 0.05, 10) == pytest.approx(price_from_yield(100, 0.05, 10, y), rel=1e-12)


@pytest.mark.parametrize("maturity", [2, 5, 10, 30])
def test_krds_sum_to_effective_duration(maturity):
    krd, eff = key_rate_durations(CURVE, 100, 0.04, maturity)
    assert sum(krd.values()) == pytest.approx(eff, rel=1e-6)


def test_zero_coupon_risk_sits_at_its_maturity():
    krd, eff = key_rate_durations(CURVE, 100, 0.0, 7, freq=1)
    assert krd[7] == pytest.approx(7.0, rel=1e-6)  # continuous-compounding duration of a 7y zero
    assert all(abs(v) < 1e-9 for k, v in krd.items() if k != 7)


def test_coupon_bond_has_no_risk_beyond_maturity():
    krd, _ = key_rate_durations(CURVE, 100, 0.05, 5)
    assert all(abs(krd[k]) < 1e-12 for k in KEY_TENORS if k > 5)
    assert max(krd, key=krd.get) == 5
