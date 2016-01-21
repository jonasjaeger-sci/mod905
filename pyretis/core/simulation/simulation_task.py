# -*- coding: utf-8 -*-
"""Definition of a class for tasks."""
from __future__ import print_function
import inspect
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


def _check_args(function, given_args=None, given_kwargs=None):
    """Check consistency for function and the given (keyword) arguments.

    Here we assume that the arguments are given in a list and that
    the keyword arguments are given as a dictionary. The function
    `inspect.getargspec` is used to check the input function.

    Parameters
    ----------
    function : function
        The function we will inspect.
    given_args : list
        A list of the arguments to pass to the function. 'self' will not
        be considered here since it passed implicitly.
    given_kwargs : dict
        A dictionary with keyword arguments.

    Returns
    -------
    out : boolean
        False if there is some inconsistencies, the calling of the function
        will probably fail. True otherwise.
    """
    arguments = inspect.getargspec(function)
    if not arguments.defaults:
        args = arguments.args
        defaults = None
    else:
        defaults = arguments.args[-len(arguments.defaults):]
        args = [arg for arg in arguments.args if arg not in defaults]
    # remove self from args, this is passed implicitly to objects
    args = [arg for arg in args if arg is not 'self']
    # first test, do we give correct number of required arguments?
    if given_args is not None:
        given = len(given_args)
    else:
        given = 0
    if len(args) != given:
        msgtxt = 'Wrong number of arguments given'
        logging.warning(msgtxt)
        return False
    # Check kwargs but only check in case some kwargs are given here.
    # If they are not given, we assume that the user knows what's happening
    # and that the default kwargs will be used.
    if given_kwargs is not None:
        if defaults:
            extra = [key for key in given_kwargs if key not in defaults]
            if extra:
                msg = ['Task Keyword arguments: {}'.format(defaults)]
                msg += ['Unexpected keyword argument: {}'.format(extra)]
                msgtxt = '\n'.join(msg)
                logging.warning(msgtxt)
                return False
        else:
            msgtxt = 'Unexpected keyword argument!'
            logging.warning(msgtxt)
            return False
    return True


def execute_now(step, when):
    """Determine if a task should be executed or not at this `step`.

    Parameters
    ----------
    step : dict of ints
        Keys are 'step' (current cycle number), 'start' cycle number at start
        'stepno' the number of cycles we have performed so far.
    when : dict
        This dict determines when the function should be executed.

    Returns
    -------
    out : boolean
        True of the task should be executed.
    """
    if when is None:
        return True
    else:
        exe = False
        if 'every' in when:
            exe = step['stepno'] % when['every'] == 0
        if not exe and 'at' in when:
            try:
                exe = step['step'] in when['at']
            except TypeError:
                exe = step['step'] == when['at']
        return exe


class SimulationTask(object):
    """Class SimulationTask(object) - Representation of simulation tasks.

    This class defines a task object. A task is executed at specific points,
    at regular intervals etc. in a simulation. A task will typically provide
    a result, but it does not need to. I can simply just alter the state of
    the passed argument(s).

    Attributes
    ----------
    function : function
        The function to execute.
    when : dict
        Determines if the task should be executed.
    args : list
        List of arguments to the function.
    kwargs : dict
        The keyword arguments to the function.
    first : boolean
        True if this task should be executed before the first
        step of the simulation.
    result : string
        This is a label for the result created by the task.
    """

    def __init__(self, function, args=None, kwargs=None, when=None,
                 result=None, first=False):
        """Initialize the task.

        Parameters
        ----------
        function : function
            The function to execute.
        args : list, optional
            List of arguments to the function.
        kwargs : dict, optional
            The keyword arguments to the function.
        when : dict
            Determines if the task should be executed.
        first : boolean
            True if this task should be executed before the first
            step of the simulation.
        result : string
            This is a label for the result created by the task.
        """
        if not callable(function):
            msg = 'The given function for the task is not callable!'
            raise AssertionError(msg)
        ok_to_add = _check_args(function, given_args=args, given_kwargs=kwargs)
        if not ok_to_add:
            msg = 'Wrong arguments or keyword arguments!'
            raise AssertionError(msg)
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.when = when
        self._result = result
        self.first = first

    def execute(self, step):
        """Execute the task.

        Parameters
        ----------
        step : dict of ints
            Keys are 'step' (current cycle number), 'start' cycle number at
            start and 'stepno' the number of cycles we have performed so far.

        Returns
        -------
        out : unknown type
            The result of running `self.function`.
        """
        args = self.args
        kwargs = self.kwargs
        if execute_now(step, self.when):
            if args is None:
                if kwargs is None:
                    return self.function()
                else:
                    return self.function(**kwargs)
            else:
                if kwargs is None:
                    return self.function(*args)
                else:
                    return self.function(*args, **kwargs)
        else:
            return None

    def update_when(self, when):
        """Update when to new value(s).

        It will only update `self.when` for the keys given in the
        input `when`.

        Parameters
        ----------
        when : dict
            This dict contains the settings to update.

        Returns
        -------
        out : None
            Returns `None` but modifies `self.when`.
        """
        if self.when is None:
            self.when = when
        else:
            for key in when:
                self.when[key] = when[key]

    @property
    def result(self):
        """Return the result label."""
        return self._result

    def run_first(self):
        """Return True if task should be executed before first step."""
        return self.first

    def __call__(self, step):
        """Execute the task.

        Parameters
        ----------
        step : dict of ints
            Keys are 'step' (current cycle number), 'start' cycle number at
            start and 'stepno' the number of cycles we have performed so far.

        Returns
        -------
        out : unknown type
            The result of `self.execute(step)`.
        """
        return self.execute(step)
