# pyretis

Rare event simulations with python

---

## Overview

pyretis is a molecular simulation toolkit 
for **rare events** with emphasis on
[transition interface sampling](http://en.wikipedia.org/wiki/Transition_path_sampling#Transition_interface_sampling)
and [replica exchange transition interface sampling](http://www.van-erp.org).

pyretis is open source, licenced under
the [MIT license](about/license.md), written 
in [python](https://www.python.org) and simulations are
defined, set up and run using a high-level python script.

---



## Easy to use

pyretis is easy to use and customize.
To give you a flavor,
the following python script defines a transition
interface simulation for a particle in a double well
potential and calculates the rate constant for
the transition between the two states:
```python
from retis.core import Simulation, System
from retis.core import Tis
mysystem = System() # create empty system
run_fancy_tis_calculation()
```
## Getting started

Getting started info, examples.
