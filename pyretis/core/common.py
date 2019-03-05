# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Definition of some common methods that might be useful.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

inspect_function (:py:func:`.inspect_function`)
    A method to obtain information about arguments, keyword arguments
    for functions.

initiate_instance (:py:func:`.initiate_instance`)
    Method to initiate a class with optional arguments.

generic_factory (:py:func:`.generic_factory`)
    Create instances of classes based on settings.

compare_objects (:py:func`.compare_objects`)
    Method to compare two PyRETIS objects.
"""
import logging
import inspect
import numpy as np


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


__all__ = ['inspect_function', 'initiate_instance', 'generic_factory']


def _arg_kind(arg):
    """Determine kind for a given argument.

    This method will help :py:func:`.inspect_function` to determine
    the correct kind for arguments.

    Parameters
    ----------
    arg : object like :py:class:`inspect.Parameter`
        The argument we will determine the type of.

    Returns
    -------
    out : string
        A string we use for determine the kind.

    """
    kind = None
    if arg.kind == arg.POSITIONAL_OR_KEYWORD:
        if arg.default is arg.empty:
            kind = 'args'
        else:
            kind = 'kwargs'
    elif arg.kind == arg.POSITIONAL_ONLY:
        kind = 'args'
    elif arg.kind == arg.VAR_POSITIONAL:
        kind = 'varargs'
    elif arg.kind == arg.VAR_KEYWORD:
        kind = 'keywords'
    elif arg.kind == arg.KEYWORD_ONLY:
        # We treat these as keyword arguments:
        kind = 'kwargs'
    return kind


def inspect_function(function):
    """Return arguments/kwargs of a given function.

    This method is intended for use where we are checking that we can
    call a certain function. This method will return arguments and
    keyword arguments a function expects. This method may be fragile -
    we assume here that we are not really interested in args and
    kwargs and we do not look for more information about these here.

    Parameters
    ----------
    function : callable
        The function to inspect.

    Returns
    -------
    out : dict
        A dict with the arguments, the following keys are defined:

        * `args` : list of the positional arguments
        * `kwargs` : list of keyword arguments
        * `varargs` : list of arguments
        * `keywords` : list of keyword arguments

    """
    out = {'args': [], 'kwargs': [],
           'varargs': [], 'keywords': []}
    arguments = inspect.signature(function)  # pylint: disable=no-member
    for arg in arguments.parameters.values():
        kind = _arg_kind(arg)
        if kind is not None:
            out[kind].append(arg.name)
        else:  # pragma: no cover
            logger.critical('Unknown variable kind "%s" for "%s"',
                            arg.kind, arg.name)
    return out


def _pick_out_arg_kwargs(klass, settings):
    """Pick out arguments for a class from settings.

    Parameters
    ----------
    klass : class
        The class to initiate.
    settings : dict
        Positional and keyword arguments to pass to `klass.__init__()`.

    Returns
    -------
    out[0] : list
        A list of the positional arguments.
    out[1] : dict
        The keyword arguments.

    """
    info = inspect_function(klass.__init__)
    used, args, kwargs = set(), [], {}
    for arg in info['args']:
        if arg == 'self':
            continue
        try:
            args.append(settings[arg])
            used.add(arg)
        except KeyError:
            msg = 'Required argument "{}" for "{}" not found!'.format(arg,
                                                                      klass)
            raise ValueError(msg)
    for arg in info['kwargs']:
        if arg == 'self':
            continue
        if arg in settings:
            kwargs[arg] = settings[arg]
    return args, kwargs


def initiate_instance(klass, settings):
    """Initialise a class with optional arguments.

    Parameters
    ----------
    klass : class
        The class to initiate.
    settings : dict
        Positional and keyword arguments to pass to `klass.__init__()`.

    Returns
    -------
    out : instance of `klass`
        Here, we just return the initiated instance of the given class.

    """
    args, kwargs = _pick_out_arg_kwargs(klass, settings)
    # Ready to initiate:
    msg = 'Initiated "%s" from "%s" %s'
    name = klass.__name__
    mod = klass.__module__
    if not args:
        if not kwargs:
            logger.debug(msg, name, mod, 'without arguments.')
            return klass()
        logger.debug(msg, name, mod, 'with keyword arguments.')
        return klass(**kwargs)
    if not kwargs:
        logger.debug(msg, name, mod, 'with positional arguments.')
        return klass(*args)
    logger.debug(msg, name, mod,
                 'with positional and keyword arguments.')
    return klass(*args, **kwargs)


def generic_factory(settings, object_map, name='generic'):
    """Create instances of classes based on settings.

    This method is intended as a semi-generic factory for creating
    instances of different objects based on simulation input settings.
    The input settings define what classes should be created and
    the object_map defines a mapping between settings and the
    class.

    Parameters
    ----------
    settings : dict
        This defines how we set up and select the order parameter.
    object_map : dict
        Definitions on how to initiate the different classes.
    name : string, optional
        Short name for the object type. Only used for error messages.

    Returns
    -------
    out : instance of a class
        The created object, in case we were successful. Otherwise we
        return none.

    """
    try:
        klass = settings['class'].lower()
    except KeyError:
        msg = 'No class given for %s -- could not create object!'
        logger.critical(msg, name)
        return None
    if klass not in object_map:
        logger.critical('Could not create unknown class "%s" for %s',
                        settings['class'], name)
        return None
    cls = object_map[klass]['cls']
    return initiate_instance(cls, settings)


def numpy_allclose(val1, val2):
    """Compare two values with allclose from numpy.

    Here, we allow for one, or both, of the values to be None.
    Note that if val1 == val2 but are not of a type known to
    numpy, the returned value will be False.

    Parameters
    ----------
    val1 : np.array
        The variable in the comparison.
    val2 : np.array
        The second variable in the comparison.

    Returns
    -------
    out : boolean
        True if the values are equal, False otherwise.

    """
    if val1 is None and val2 is None:
        return True
    if val1 is None and val2 is not None:
        return False
    if val1 is not None and val2 is None:
        return False
    try:
        return np.allclose(val1, val2)
    except TypeError:
        return False


def compare_objects(obj1, obj2, attrs, numpy_attrs=None):
    """Compare two PyRETIS objects.

    This method will compare two PyRETIS objects by checking
    the equality of the attributes. Some of these attributes
    might be numpy arrays in which case we use the
    :py:funtion:`.numpy_allclose` defined in this module.

    Parameters
    ----------
    obj1 : object
        The first object for the comparison.
    obj2 : object
        The second object for the comparison.
    attrs : iterable of strings
        The attributes to check.
    numpy_attrs : iterable of strings, optional
        The subset of attributes which are numpy arrays.

    Returns
    -------
    out : boolean
        True if the objects are equal, False otherwise.

    """
    if not obj1.__class__ == obj2.__class__:
        logger.debug(
            'The classes are different %s != %s',
            obj1.__class__, obj2.__class__
        )
        return False
    if not len(obj1.__dict__) == len(obj2.__dict__):
        logger.debug('Number of attributes differ.')
        return False
    # Compare the requested attributes:
    for key in attrs:
        try:
            val1 = getattr(obj1, key)
            val2 = getattr(obj2, key)
        except AttributeError:
            logger.debug('Failed to compare attribute "%s"', key)
            return False
        if numpy_attrs and key in numpy_attrs:
            if not numpy_allclose(val1, val2):
                logger.debug('Attribute "%s" differ.', key)
                return False
        else:
            if not val1 == val2:
                logger.debug('Attribute "%s" differ.', key)
                return False
    return True
