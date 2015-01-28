# Welcome to pyretis!

pyretis is a molecular simulation toolkit 
for rare events with emphasis on
[transition interface sampling](http://en.wikipedia.org/wiki/Transition_path_sampling#Transition_interface_sampling)
and [replica exchange transition interface sampling](http://www.van-erp.org).

pyretis is open source, licenced under
the <a href="LICENSE.txt">MIT license</a>, written 
in [python](https://www.python.org) and simulations are
defined, set up and run using a high-level python script.

## Introductionary example
To give you a flavor on the usage of pyretis,
the following python script defines a transition
path simulation for a particle in a double well
potential and calculates the rate constant for
the transition between the two wells:
```python 
from retis.core import Simulation, System
from retis.core import Tis
mysystem = System() # create empty system
```

## Learning pyretis
    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
    examples/     # Example simulations
        index.md
    retis/        # The retis toolkit
        core/     # Core functions for the retis toolkit
