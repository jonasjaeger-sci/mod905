# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definition of some common methods that might be useful.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

inspect_function (:py:func:`pyretis.core.common.inspect_function`)
    A method to obtain information about arguments, keyword arguments
    for functions.
"""
import logging
import inspect
import sys
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


def _arg_kind(arg):
    """Helper function to determine kind for a given argument.

    This method will help `inspect_function` to determine the correct
    kind for arguments when using python3.

    Parameters
    ----------
    arg : object like inspect.Parameter
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
    elif arg.kind == arg.VAR_POSITIONAL:
        kind = 'varargs'
    elif arg.kind == arg.VAR_KEYWORD:
        kind = 'keywords'
    elif arg.kind == arg.KEYWORD_ONLY:
        # we treat these as keyword arguments:
        kind = 'kwargs'
    return kind


def inspect_function(function):
    """Method returning arguments/kwargs of a given function.

    This method is intended for usage where we are checking that we can
    call certain function. This method will return arguments and
    keyword arguments a function expects. This method may be fragile -
    we assume here that we are not really interested in *args and
    **kwargs and we do not look for more information about these here.

    Parameters
    ----------
    function : A callable function.
        The function to analyse.

    Returns
    -------
    out : dict
        A dict with the arguments, the following keys are defined:

        * `args` : list of the positional arguments
        * `kwargs` : list of keyword arguments
        * `varargs` : list of arguments on form *args
        * `keywords` : list of arguments on form **kwargs
    """
    out = {'args': [], 'kwargs': [],
           'varargs': [], 'keywords': []}
    if sys.version_info > (3, 3):
        arguments = inspect.signature(function)  # pylint: disable=no-member
        for arg in arguments.parameters.values():
            kind = _arg_kind(arg)
            if kind is not None:
                out[kind].append(arg.name)
            else:
                msg = 'Unknow variable kind "{}" for "{}"'.format(arg.kind,
                                                                  arg.name)
                logger.critical(msg)
        return out
    else:
        arguments = inspect.getargspec(function)
        if not arguments.defaults:
            out['args'] = [arg for arg in arguments.args]
        else:
            defaults = arguments.args[-len(arguments.defaults):]
            for arg in arguments.args:
                if arg not in defaults:
                    out['args'].append(arg)
                else:
                    out['kwargs'].append(arg)
        if arguments.varargs is not None:
            out['varargs'] = [arguments.varargs]
        if arguments.keywords is not None:
            out['keywords'] = [arguments.keywords]
        return out


def initiate_instance(klass, args=None, kwargs=None):
    """Function to initiate a class with optional arguments.

    Parameters
    ----------
    klass : class
        The class to initiate.
    args : list, optional
        Positional arguments to `klass.__init__()`.
    kwargs : dict, optional
        The keyword arguments to `klass.__init__()`

    Returns
    -------
    out : instance of `klass`
        Here, we just return the initiated instance of the given class.
    """
    msg = 'Initiated "{}" from "{}" {{}}'.format(klass.__name__,
                                                 klass.__module__)
    if args is None:
        if kwargs is None:
            msgtxt = msg.format('without arguments.')
            logger.debug(msgtxt)
            return klass()
        else:
            msgtxt = msg.format('with keyword arguments.')
            logger.debug(msgtxt)
            return klass(**kwargs)
    else:
        if kwargs is None:
            msgtxt = msg.format('with positional arguments.')
            logger.debug(msgtxt)
            return klass(*args)
        else:
            msgtxt = msg.format('with positional and keyword arguments.')
            logger.debug(msgtxt)
            return klass(*args, **kwargs)


def generic_factory(settings, object_map, name='generic'):
    """Create instances of classes based on settings.

    This method is intended as a semi-generic factory for creating
    instances of different objects based on simulation input settings.
    The input settings defines what classes should be created and
    the object_map defines a mapping between settings and the
    class.

    Parameters
    ----------
    settings : dict
        This defines how we set up and select the order parameter.
    object_map : dict
        Definitions on how to initiate the different classes.
    name : string
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
        msg = ('No class given for {}'
               ' -- could not create object!').format(name)
        logger.critical(msg)
        return None
    if klass not in object_map:
        msg = ('Could not create unknown class "{}"'
               ' for {}').format(settings['class'], name)
        logger.critical(msg)
        return None
    cls = object_map[klass].get('cls')
    args = object_map[klass].get('args', [])
    kwargs = object_map[klass].get('kwargs', {})

    input_args = []
    for arg in args:
        if arg not in settings:
            msg = 'Setting "{}" for "{}" not found. Aborting!'.format(arg,
                                                                      klass)
            logger.critical(msg)
            return None
        else:
            input_args.append(settings[arg])

    input_kwargs = {}
    for kwarg in kwargs:
        if kwarg in settings:
            input_kwargs[kwarg] = settings[kwarg]
        else:
            # Here we could do something, but we just assume that we
            # now should use the default defined by the class.
            pass

    if len(input_args) == 0:
        input_args = None
    if len(input_kwargs) == 0:
        input_kwargs = None
    return initiate_instance(cls, input_args, input_kwargs)
