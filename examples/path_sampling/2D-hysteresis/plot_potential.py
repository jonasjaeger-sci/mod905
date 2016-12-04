# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation
"""
# pylint: disable=C0103
import numpy as np
from pyretis.core import System, Box
from pyretis.core.units import CONVERT, create_conversion_factors
from pyretis.inout.settings import create_force_field, create_orderparameter
# imports for the plotting:
from matplotlib import pyplot as plt
settings = {}
settings['potential'] = [{'class': 'Hyst2D',
                          'module': 'potential.py',
                          'dim': 2,
                          'parameter': {'gamma1': 1, 'gamma2': -10,
                                        'gamma3': -10, 'alpha1': -30,
                                        'alpha2': -3, 'beta1': -30,
                                        'beta2': -3, 'x0': 0.2, 'y0': 0.4}}]
settings['orderparameter'] = {'class': 'OrderXY',
                              'module': 'retis-xy/orderp.py',
                              'name': 'order',
                              'index': 0}
forcefield = create_force_field(settings)
print(forcefield)
orderp = create_orderparameter(settings)
box = Box(periodic=[False, False])
fakesys = System(units='reduced', box=box)
fakesys.add_particle(name='B', pos=np.zeros(2), ptype=1)
x = np.linspace(-0.5, 0.5, 100)
y = np.linspace(-0.5, 0.5, 100)
X, Y = np.meshgrid(x, y, indexing='ij')
Z = np.zeros_like(X)
O = np.zeros_like(X)
fig = plt.figure()
ax1 = fig.add_subplot(111)
OXY = []
for i, xi in enumerate(x):
    for j, yj in enumerate(y):
        fakesys.particles.pos[0, 0] = xi
        fakesys.particles.pos[0, 1] = yj
        Z[i, j] = forcefield.evaluate_potential(fakesys)
        O[i, j] = orderp.calculate(fakesys)
        point = orderp.origin + orderp.vec * O[i, j]
        OXY.append(point)       
OXY = np.array(OXY)
ax1.contourf(X, Y, Z, 10, cmap=plt.cm.viridis)
ax1.scatter(OXY[:,0], OXY[:, 1], color='k')
fig.savefig('pot.png')
#plt.show()
