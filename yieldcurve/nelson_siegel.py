"""Nelson-Siegel and Svensson parametric yield curves, fitted by least squares.

    NS:  y(t) = b0 + b1 L(t/tau) + b2 [L(t/tau) - e^{-t/tau}],   L(x) = (1 - e^{-x}) / x
    Svensson adds a second hump: + b3 [L(t/tau2) - e^{-t/tau2}]

b0 = long-run level (y -> b0 as t -> inf), b0 + b1 = short rate (t -> 0), b2/b3 = curvature.
For fixed decay parameters the model is linear in the betas, so we solve the betas by ordinary
least squares and search only over tau (1-D) or (tau1, tau2) (2-D grid + local refinement).
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize, minimize_scalar


def _L(x):
    return np.where(x > 1e-10, (1 - np.exp(-x)) / np.where(x > 1e-10, x, 1.0), 1.0 - x / 2)


def _loadings(t, taus):
    t = np.asarray(t, dtype=float)
    cols = [np.ones_like(t)]
    for i, tau in enumerate(taus):
        x = t / tau
        if i == 0:
            cols.append(_L(x))
        cols.append(_L(x) - np.exp(-x))
    return np.column_stack(cols)


@dataclass
class ParametricCurve:
    betas: np.ndarray
    taus: tuple

    def zero_rate(self, t):
        return _loadings(np.atleast_1d(t), self.taus) @ self.betas

    @property
    def name(self):
        return "Nelson-Siegel" if len(self.taus) == 1 else "Svensson"


def _ols(t, y, taus):
    X = _loadings(t, taus)
    betas, *_ = np.linalg.lstsq(X, y, rcond=None)
    return betas, float(np.sum((X @ betas - y) ** 2))


def fit_nelson_siegel(t, y, tau_bounds=(0.05, 15.0)):
    t, y = np.asarray(t, float), np.asarray(y, float)
    res = minimize_scalar(lambda tau: _ols(t, y, (tau,))[1], bounds=tau_bounds, method="bounded",
                          options={"xatol": 1e-10})
    # guard against a local minimum: compare with a coarse grid
    grid = np.geomspace(*tau_bounds, 60)
    best = min([res.x, *grid], key=lambda tau: _ols(t, y, (tau,))[1])
    return ParametricCurve(_ols(t, y, (best,))[0], (float(best),))


def fit_svensson(t, y, tau_bounds=(0.05, 15.0)):
    t, y = np.asarray(t, float), np.asarray(y, float)
    grid = np.geomspace(*tau_bounds, 30)
    sse = lambda taus: _ols(t, y, tuple(taus))[1]
    start = min(((a, b) for a in grid for b in grid if b > a), key=sse)
    res = minimize(lambda p: sse(np.exp(p)), np.log(start), method="Nelder-Mead",
                   options={"xatol": 1e-10, "fatol": 1e-16, "maxiter": 4000})
    taus = tuple(float(v) for v in np.clip(np.exp(res.x), *tau_bounds))
    if sse(taus) > sse(start):
        taus = tuple(float(v) for v in start)
    return ParametricCurve(_ols(t, y, taus)[0], taus)
