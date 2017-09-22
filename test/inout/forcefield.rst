Forcefield
----------
description = My force field mix

Potential
---------
class = PairLennardJonesCutnp
shift = True
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}

Potential
---------
class = DoubleWellWCA
parameter types = [(0, 0)]
parameter rzero = 1.122462048309373
parameter height = 6.0
parameter width = 0.25

Potential
---------
class = FooPotential
module = foopotential.py
parameter a = 10.0
