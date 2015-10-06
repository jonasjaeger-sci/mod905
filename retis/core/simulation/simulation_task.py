# -*- coding: utf-8 -*-
"""Definition of a class for tasks."""
import inspect
import warnings

def _check_args(function, given_args=None, given_kwargs=None):
    """
    Will check if the given args match the given function
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

    # first test the required arguments:
    if given_args is not None:
        given = len(given_args)
    else:
        given = 0
    if not len(args) == given:
        msg = 'Wrong number of arguments given'
        warnings.warn(msg)
        return False
    # Check kwargs, only check in case some kwargs are given
    # If they are not given, we assume that the user knows what's happening
    # and that the default kwargs will be used.
    if given_kwargs is not None:
        if defaults:
            extra = [key for key in given_kwargs if key not in defaults]
            if extra:
                msg = ['Task Keyword arguments: {}'.format(defaults)]
                msg += ['Unexpected keyword argument: {}'.format(extra)]
                msg = '\n'.join(msg)
                warnings.warn(msg)
                return False
        else:
            msg = 'Unexpected keyword argument!'
            warnings.warn(msg)
            return False
    return True


class Task(object):
    """
    This class defines a task object. A task is executed at specific points,
    regular interval etc. in a simulation. A task will also produce a result.

    Attributes
    ----------
    function : function
        The function to execute
    when : dict
        Determines if the task should be executed.
    args : list
        List of arguments to the function
    kwargs : dict
        The keyword arguments to the function
    """
    def __init__(self, function, args=None, kwargs=None, when=None):
        """
        Parameters
        ----------
        function : function
            The function to execute
        args : list, optional
            List of arguments to the function
        kwargs : dict, optional
            The keyword arguments to the function
        when : dict
            Determines if the task should be executed.
        """
        # 1) make sure function is callable
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

    def _execute_now(self, step):
        """
        Should a task be executed now?

        Parameters
        ----------
        step : dict of ints
            Keys are 'step' (current cycle number), 'start' cycle number at start
            'stepno' the number of cycles we have performed so far.

        Returns
        -------
        out : boolean
            True of the task should be executed
        """
        if self.when is None:
            return True
        else:
            exe = False
            if 'every' in self.when:
                exe = step['stepno'] % self.when['every'] == 0
            if 'at' in self.when:
                try:
                    exe = step['step'] in self.when['at']
                except TypeError:
                    exe = step['step'] == self.when['at']
            return exe

    def execute(self, step):
        """
        This will execute the task.

        Parameters
        ----------
        step : dict of ints
            Keys are 'step' (current cycle number), 'start' cycle number at start
            'stepno' the number of cycles we have performed so far.
        args : list
            These are the arguments to the function. Can be used to override
            self.args
        kwargs : dict
            These are keyword arguments to the function.
            Can be used to override self.kwargs
        """
        args = self.args
        kwargs = self.kwargs
        if self._execute_now(step):
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

    def __call__(self, step):
        """
        This will execute the task.

        Parameters
        ----------
        step : dict of ints
            Keys are 'step' (current cycle number), 'start' cycle number at start
            'stepno' the number of cycles we have performed so far.
        """
        return self.execute(step)
