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

crossing_counter (:py:func`.crossing_counter`)
    Function to count the crossing of a path on an interface.

crossing_finder (:py:func`.crossing_finder`)
    Function to get the shooting points of the crossing of a path
    on an interface.

select_and_trim_a_segment (:py:func`.select_and_trim_a_segment`)
    Function to trim a path between interfaces plus the two external points.

trim_path_between_interfaces (:py:func`.trim_path_between_interfaces`)
    Function to trim a path between interfaces.

"""
import logging
import inspect
import numpy as np

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


__all__ = ['inspect_function', 'initiate_instance', 'generic_factory',
           'crossing_counter', 'crossing_finder',
           'select_and_trim_a_segment', 'trim_path_between_interfaces',
           'big_fat_comparer']


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


def big_fat_comparer(any1, any2, hard=False):
    """Check if two dictionary are the same, regardless their complexity.

    Parameters
    ----------
    any1 : anything
    any2 : anything
    hard : boolean, optional
        Raise ValueError if any1 and any2 are different

    Returns
    -------
    out : boolean
        True if any1 = any2, false otherwise

    """
    if type(any1) is not type(any2):
        if hard:
            raise ValueError('Fail type', any1, any2)
        return False

    if isinstance(any1, (list, tuple)):
        if len(any1) != len(any2):
            if hard:
                raise ValueError('Fail list length', any1, any2)
            return False

        for key1, key2 in zip(any1, any2):
            if not big_fat_comparer(key1, key2, hard):
                if hard:
                    raise ValueError('Fail item in list',
                                     any1, any2)  # pragma: no cover
                return False

    elif isinstance(any1, np.ndarray):
        if any1.shape != any2.shape:
            if hard:
                raise ValueError('Fail np array shape', any1, any2)
            return False

        for key1, key2 in zip(np.nditer(any1), np.nditer(any2)):
            if not (key1 == key2).all():
                if hard:
                    raise ValueError('Fail np array item', any1, any2)
                return False

    elif isinstance(any1, dict):
        for key in any1:
            if key not in any2:
                if hard:
                    raise ValueError('Fail dict', any1, any2)
                return False

            if not isinstance(any1[key], type(any2[key])):
                if hard:
                    raise ValueError('Fail types', any1[key], any2[key])
                return False

            if isinstance(any1[key], (dict, list, tuple, np.ndarray)):
                if not big_fat_comparer(any1[key], any2[key], hard):
                    if hard:
                        raise ValueError('Fail item',
                                         any1[key],
                                         any2[key])  # pragma: no cover
                    return False

            else:
                if any1[key] != any2[key]:
                    if hard:
                        raise ValueError('Fail item', any1[key], any2[key])
                    return False

        for key in any2:
            if key not in any1:
                if hard:
                    raise ValueError('Fail item', any1, any2)
                return False

    else:
        if any1 != any2:
            if hard:
                raise ValueError('Fail item', any1, any2)
            return False

    return True


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
    :py:function:`.numpy_allclose` defined in this module.

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


def segments_counter(path, interface_l, interface_r):
    """Count the directional segment between interfaces.

    Method to count the number of the directional segments of the path,
    along the orderp, that connect FROM interface_l TO interface_r.

    Parameters
    -----------
    path : object like :py:class:`.PathBase`
        This is the input path which segments will be counted.
    interface_r : float
        This is the position of the RIGHT interface.
    interface_l : float
        This is the position of the LEFT interface.

    Returns
    -------
    n_segments : integer
        Segment counter

    """
    icros, n_segments = -1, 0
    for i in range(len(path.phasepoints[:-1])):
        op1 = path.phasepoints[i].order[0]
        op2 = path.phasepoints[i+1].order[0]
        if op2 > interface_l >= op1:
            icros = i
        if op2 > interface_r >= op1:
            if icros != -1:
                icros = -1
                n_segments += 1
    return n_segments


def crossing_counter(path, interface):
    """Count the crossing to an interfaces.

    Method to count the crosses of a path over an interface.

    Parameters
    -----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be trimmed.
    interface : float
        This is the position of the interface.

    Returns
    -------
    cnt : integer
        Number of crossing of the given interface.

    """
    cnt = 0
    for i in range(len(path.phasepoints[:-1])):
        op1 = path.phasepoints[i].order[0]
        op2 = path.phasepoints[i+1].order[0]
        if op2 >= interface > op1 or op1 >= interface > op2:
            cnt += 1
    return cnt


def crossing_finder(path, interface):
    """Find the crossing to an interfaces.

    Method to select the crosses of a path over an interface.

    Parameters
    -----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be trimmed.
    interface : float
        This is the position of the interface.

    Returns
    -------
    ph1, ph2 : lists of snapshots
        It is a list of snapshots to define the crossing,
        one right before and one right after the interface.

    """
    ph1, ph2 = [], []
    for i in range(len(path.phasepoints[:-1])):
        op1 = path.phasepoints[i].order[0]
        op2 = path.phasepoints[i+1].order[0]
        if op2 >= interface > op1 or op1 >= interface > op2:
            ph1.append(path.phasepoints[i])
            ph2.append(path.phasepoints[i+1])
    return ph1, ph2


def trim_path_between_interfaces(path, interface_l, interface_r):
    """Cut a path between the two interfaces.

    The method cut a path and keeps only what is within the range
    (interface_l interface_r).
    -Be careful, it can provide multiple discontinuous segments-
    =Be carefull2 consider if you need to make this check left inclusive
    (as the ensemble should be left inclusive)

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be trimmed.
    interface_r : float
        This is the position of the RIGHT interface.
    interface_l : float
        This is the position of the LEFT interface.

    Returns
    -------
    new_path : object like :py:class:`.PathBase`
        This is the output trimmed path.

    """
    new_path = path.empty_path()
    for phasepoint in path.phasepoints:
        orderp = phasepoint.order[0]
        if interface_r > orderp > interface_l:
            new_path.append(phasepoint)
    new_path.maxlen = path.maxlen
    new_path.status = path.status
    new_path.time_origin = path.time_origin
    new_path.generated = 'ct'
    new_path.rgen = path.rgen
    return new_path


def select_and_trim_a_segment(path, interface_l, interface_r,
                              segment_to_pick=None):
    """Cut a directional segment from interface_l to interface_r.

    It keeps what is within the range [interface_l interface_r)
    AND the snapshots just after/before the interface.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be trimmed.
    interface_r : float
        This is the position of the RIGHT interface.
    interface_l : float
        This is the position of the LEFT interface.
    segment_to_pick : integer (n.b. it starts from 0)
        This is the segment to be selected, None = random

    Returns
    -------
    segment : a path segment composed only the snapshots for which
        orderp is between interface_r and interface_l and the
        ones right after/before the interfaces

    """
    key = False
    segment = path.empty_path()
    segment_i = -1
    if segment_to_pick is None:
        segment_number = segments_counter(path, interface_l, interface_r)
        segment_to_pick = path.rgen.random_integers(0, segment_number)

    for i, phasepoint in enumerate(path.phasepoints[:-1]):
        op1 = path.phasepoints[i].order[0]
        op2 = path.phasepoints[i+1].order[0]
        # NB: these are directional crossing
        if op2 >= interface_l > op1:
            # We are in the good region, segment_i
            if not key:
                segment_i += 1
            key = True
        if key:
            if segment_i == segment_to_pick:
                segment.append(phasepoint)
        if op2 >= interface_r > op1:
            if key and segment_i == segment_to_pick:
                segment.append(path.phasepoints[i+1])
            key = False

    segment.maxlen = path.maxlen
    segment.status = path.status
    segment.time_origin = path.time_origin
    segment.generated = 'sg'
    segment.rgen = path.rgen
    return segment
