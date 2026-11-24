import pytest

from yieldcurve import (
    Position,
    bootstrap,
    butterfly,
    key_rate_durations,
    parallel,
    portfolio_value,
    price_from_curve,
    scenario_pnl,
    twist,
)
from test_bootstrap import MARKET

CURVE = bootstrap(MARKET, "log_linear_df")
BULLET = [Position(1_000_000, 0.04, 10)]


def _barbell():
    """2Y + 30Y mix with the same value and effective duration as the 10Y bullet."""
    import numpy as np

    def dv(p):
        price = price_from_curve(CURVE, 100, p.coupon_rate, p.maturity)
        return price, key_rate_durations(CURVE, 100, p.coupon_rate, p.maturity)[1]

    pb, db = dv(BULLET[0])
    p2, d2 = dv(Position(1, 0.04, 2))
    p30, d30 = dv(Position(1, 0.04, 30))
    target_v = pb * 1_000_000 / 100
    # solve value and dollar-duration matching for face amounts
    A = np.array([[p2, p30], [p2 * d2, p30 * d30]]) / 100
    f2, f30 = np.linalg.solve(A, [target_v, target_v * db])
    return [Position(f2, 0.04, 2), Position(f30, 0.04, 30)]


def test_parallel_shift_first_order():
    full, approx = scenario_pnl(CURVE, BULLET, parallel(10))
    assert full < 0
    assert approx == pytest.approx(full, rel=0.01)


def test_krd_approx_misses_only_convexity_for_large_moves():
    full_up, approx_up = scenario_pnl(CURVE, BULLET, parallel(100))
    full_dn, approx_dn = scenario_pnl(CURVE, BULLET, parallel(-100))
    # positive convexity: real P&L beats the linear estimate in both directions
    assert full_up > approx_up and full_dn > approx_dn


def test_barbell_vs_bullet_same_duration():
    barbell = _barbell()
    assert portfolio_value(CURVE, barbell) == pytest.approx(portfolio_value(CURVE, BULLET), rel=1e-9)
    # parallel move: nearly identical first-order P&L
    bb, _ = scenario_pnl(CURVE, barbell, parallel(10))
    bu, _ = scenario_pnl(CURVE, BULLET, parallel(10))
    assert bb == pytest.approx(bu, rel=0.02)
    # butterfly (wings up, belly down): barbell loses, bullet gains
    assert scenario_pnl(CURVE, barbell, butterfly(25))[0] < 0 < scenario_pnl(CURVE, BULLET, butterfly(25))[0]


def test_steepener_hurts_long_end_more():
    long_bond = [Position(1_000_000, 0.04, 30)]
    short_bond = [Position(1_000_000, 0.04, 2)]
    assert scenario_pnl(CURVE, long_bond, twist(50))[0] < 0 < scenario_pnl(CURVE, short_bond, twist(50))[0]
