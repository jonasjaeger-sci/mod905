# -*- coding: utf-8 -*-
"""The Langevin integrator implemented in FORTRAN."""
import numpy as np
from matplotlib import pyplot as plt

try:
    from vvintegrator import vvintegrator
except ImportError:
    MSG = ('Could not import external Fortran library.'
           '\nPlease compile with "make"!')
    logger.critical(MSG)
    raise ImportError(MSG)

def test_rangaussian(sigma, numbers=10000, bins=100):
    """Test the gaussian generator"""
    rndf = np.array([vvintegrator.rangaussian(sigma) for _ in range(numbers)])
    rnd = np.random.normal(loc=0.0, scale=sigma, size=numbers)

    mini = min(rndf.min(), rnd.min())
    maxi = max(rndf.max(), rnd.max())

    fig = plt.figure()
    ax1 = fig.add_subplot(111)

    histf, edgesf = np.histogram(rndf, bins=bins, range=(mini, maxi))
    midf = 0.5 * (edgesf[1:] + edgesf[:-1])
    hist, edges = np.histogram(rnd, bins=bins, range=(mini, maxi))
    mid = 0.5 * (edges[1:] + edges[:-1])
    ax1.plot(midf, histf, 'bo-', label='FORTRAN', lw=2, alpha=0.5)
    ax1.plot(mid, hist, 'gs-', label='numpy', lw=2, alpha=0.5)
    ax1.legend()
    plt.show()

def test_gssbivar(s12os11, sqrts11, sqrtsos11, numbers=10000, bins=100):
    rndf = np.array([vvintegrator.gssbivar(s12os11, sqrts11, sqrtsos11) for _ in range(numbers)])
    histf, xedges, yedges = np.histogram2d(rndf[:, 0], rndf[:, 1], bins=bins, range=None)
    xvarf, yvarf = np.meshgrid(xedges, yedges)
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.pcolormesh(xvarf, yvarf, histf)
    plt.show()

if __name__ == '__main__':
    seed = 1000
    size = vvintegrator.get_seed_size()
    print(size)
    seeds = [seed + i for i in range(size)]
    seeds = np.array(seeds, dtype=np.int32)
    vvintegrator.seed_random_generator(seeds)
    for sigma in [1.0, 0.5, 2.0, 10.0]:
        test_rangaussian(sigma, numbers=10**6)
    test_gssbivar(1.0, 2.0, 1.0)
