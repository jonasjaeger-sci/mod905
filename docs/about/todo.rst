.. _todo-notes:

#####
Todo
#####

There is still a lot of simple things that should be included in pytismol:

- Move from pyplot to (for example)

.. code-block:: python

  from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
  from matplotlib.figure import Figure

- Include option for storing/loading binary files

- Update analysis tools so that we do not pass through the same data
  in many independent loops. Much of the analysis can be done in a one-pass
  way.

- Consider more carefully the reversing of paths: Will we need to recalculate
  order parameters here?

- Investigate where we should write c/fortran code. The block error analysis
  is one example where we perhaps can speed up things?
