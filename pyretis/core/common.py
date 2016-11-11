# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definition of some common methods that might be useful.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

inspect_function (:py:func:`pyretis.core.common.inspect_function`)
    A method to obtain information about arguments, keyword arguments
    for functions.

initiate_instance
    Method to initiate a class with optional arguments.

generic_factory
    Create instances of classes based on settings.
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


def _pick_out_arg_kwargs(klass, settings):
    """Method to pick out arguments for a class from settings.

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
            # used.add(arg)
    # add special keys as used:
    # used.add('class')
    # used.add('parameter')
    # used.add('module')
    # for key in settings:
    #     if key not in used:
    #        msg = 'Superfluous setting "{}" ignored for "{}"!'.format(key,
    #                                                                  klass)
    #        logger.warning(msg)
    return args, kwargs


def initiate_instance(klass, settings):
    """Method to initiate a class with optional arguments.

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
    # Ready to initiate!
    msg = 'Initiated "{}" from "{}" {{}}'.format(klass.__name__,
                                                 klass.__module__)
    if len(args) == 0:
        if len(kwargs) == 0:
            msgtxt = msg.format('without arguments.')
            logger.debug(msgtxt)
            return klass()
        else:
            msgtxt = msg.format('with keyword arguments.')
            logger.debug(msgtxt)
            return klass(**kwargs)
    else:
        if len(kwargs) == 0:
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
    cls = object_map[klass]['cls']
    return initiate_instance(cls, settings)
