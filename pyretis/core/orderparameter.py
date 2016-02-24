# -*- coding: utf-8 -*-
"""This file contains classes to represent order parameters.

The order parameters are assumed to all be completely determined
by the system properties and they will all return at least two
values - the order parameter and the rate of change in the order
parameter (i.e. its velocity).

Important classes defined here:

- OrderParameter: Base class for the order parameters.

- OrderParameterPosition: A class for a simple position dependent order
  parameter.

- OrderParameterParse: A class for order parameters which can be parsed
  from a input string.
"""
from __future__ import division  # for StringFunctionParser
import logging
import operator
import numpy as np
# imports for StringFunctionParser:
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group,
                       Optional, ZeroOrMore, Forward, nums, alphas, oneOf)
logging.getLogger(__name__).addHandler(logging.NullHandler())


__all__ = ['OrderParameter', 'OrderParameterPosition', 'OrderParameterParse']


class OrderParameter(object):
    """OrderParameter(object).

    This class represents an order parameter. The order parameter
    is assumed to be a function that can uniquely be determined by
    the system object and its attributes.

    The order parameter implements `__call__` so it can be calculated
    using `OrderParameter(System)`.

    Attributes
    ----------
    desc : string
        This is a short description of the order parameter.
    name : string
        A name for the order parameter (useful for output).
    extra : list of functions
        This is a list of extra order parameters to calculate.
        We will assume that this list contains functions that all
        accept an object like `System` from `pyretis.core.system`
        as input and returns a single float.
    """

    def __init__(self, name, desc='General order parameter'):
        """Initialize the OrderParameter object.

        Parameters
        ----------
        name : string
            The name for the order parameter.
        desc : string
            Short description of the order parameter.
        """
        self.name = name
        self.desc = desc
        self.extra = []

    def calculate(self, system):
        """Calculate the order parameter and return it.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation, typically
            only `system.particles.pos` and/or `system.particles.vel`
            will be used. In some cases system.forcefield can also be
            used to include specific energies for the order parameter.

        Returns
        -------
        out : float
            The order parameter.
        """
        pass

    def calculate_velocity(self, system):
        """Calculate the time derivative of the order parameter.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation, typically
            only `system.particles.pos` and/or `system.particles.vel`
            will be used. In some cases system.forcefield can also be
            used to include specific energies for the order parameter.

        Returns
        -------
        out : float
            The velocity of the order parameter.
        """
        pass

    def __call__(self, system):
        """Conveniently call `calculate` and `calculate_velocity`.

        It will also call the additional order parameters defined in
        `self.extra`, if any.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation.

        Returns
        -------
        out[0] : float
            The order parameter.
        out[1] : float
            The velocity of the order parameter.
        out[2, ...] : float(s)
            Additional order parameters, if any.
        """
        orderp = self.calculate(system)
        orderv = self.calculate_velocity(system)
        ret_val = [orderp, orderv]
        if self.extra is None:
            return ret_val
        else:
            for func in self.extra:
                try:
                    extra = func(system)
                except TypeError:
                    extra = float('nan')
                ret_val.append(extra)
            return ret_val

    def add_orderparameter(self, func):
        """Add an extra order parameter to calculate.

        The given function should accept an object like
        `pyretis.core.system.System` as parameter.

        Parameters
        ----------
        func : function
            Extra function for calculation of an extra order parameter.
            It is assumed to accept only a `pyretis.core.system.System`
            object as its parameter.
        """
        if not callable(func):
            msg = 'The given function is not callable, it will not be added!'
            logging.warning(msg)
            return False
        self.extra.append(func)

    def __str__(self):
        """Return a simple string representation of the order parameter."""
        msg = ['Order parameter {}'.format(self.name)]
        msg += ['{}'.format(self.desc)]
        return '\n'.join(msg)


class OrderParameterPosition(OrderParameter):
    """OrderParameterPosition(OrderParameter).

    This class defines a very simple order parameter which is just
    the position of a given particle.

    Attributes
    ----------
    name : string
        A human readable name for the order parameter
    index : integer
        This is the index of the atom which will be used, i.e.
        system.particles.pos[index] will be used.
    dim : integer
        This is the dimension of the coordinate to use.
        0, 1 or 2 for 'x', 'y' or 'z'.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the position or not.
    """

    def __init__(self, name, index, dim='x', periodic=False):
        """Initialize `OrderParameterPosition`.

        Parameters
        ----------
        name : string
            The name for the order parameter
        index : int
            This is the index of the atom we will use the position of.
        dim : string
            This select what dimension we should consider,
            it should equal 'x', 'y' or 'z'.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.
        """
        description = 'Position of particle {} (dim: {})'.format(index, dim)
        super(OrderParameterPosition, self).__init__(name, desc=description)
        self.periodic = periodic
        self.index = index
        dims = {'x': 0, 'y': 1, 'z': 2}
        try:
            self.dim = dims[dim]
        except KeyError:
            msg = 'Unknown dimension {} requested'.format(dim)
            logging.critical(msg)
            raise

    def calculate(self, system):
        """Calculate the order parameter.

        Here, the order parameter is just the coordinate of one of the
        particles.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation, typically
            only `system.particles.pos` and/or `system.particles.vel`
            will be used. In some cases `system.forcefield` can also be
            used to include specific energies for the order parameter.

        Returns
        -------
        out : float
            The order parameter.
        """
        pos = system.particles.pos[self.index]
        if self.periodic:
            box = system.box
            pos = box.pbc_wrap(pos)
        if system.get_dim() == 1:
            return pos
        else:
            return pos[self.dim]

    def calculate_velocity(self, system):
        """Calculate the time derivative of the order parameter.

        For this order parameter we just return the velocity.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation.

        Returns
        -------
        out : float
            The velocity of the order parameter
        """
        vel = system.particles.vel[self.index]
        if system.get_dim() == 1:
            return vel
        else:
            return vel[self.dim]


class OrderParameterParse(OrderParameter):
    """OrderParameterParse(OrderParameter).

    This class defines a simple order parameter that is
    parsed from a text string given by the user. The reason
    for putting this into a object rather than as a functionality
    to the OrderParameter function is just to limit the possibility
    of parsing to one object only.

    Attributes
    ----------
    name : string
        Human readable name for the order parameter.
    orderparser : object of type `StringFunctionParser`
        This is used for parsing a string to a order parameter.
    ordervelparser : object of type `StringFunctionParser`
        This is used for parsing a string to a velocity for the order
        parameter.
    """

    def __init__(self, name, orderstr, ordervelstr):
        """Initialize `OrderParameterParse`.

        Parameters
        ----------
        name : string
            The name for the order parameter.
        orderstr : string
            This is the string representing the order parameter.
        ordervelstr : string
            This is the string representing the velocity of the order
            parameter.
        """
        description = 'Parsed order parameter'
        super(OrderParameterParse, self).__init__(name, desc=description)
        self.orderparser = StringFunctionParser(string_function=orderstr)
        self.ordervelparser = StringFunctionParser(string_function=ordervelstr)

    def calculate(self, system):
        """Calculate the order parameter.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation, typically
            only `system.particles.pos` and/or `system.particles.vel`
            will be used. In some cases `system.forcefield` can also be
            used to include specific energies for the order parameter.

        Returns
        -------
        out : float
            The order parameter.
        """
        return self.orderparser.evaluate(system=system)

    def calculate_velocity(self, system):
        """Calculate the time derivative of the order parameter.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation.

        Returns
        -------
        out : float
            The velocity of the order parameter.
        """
        return self.ordervelparser.evaluate(system=system)

    def add_orderparameter(self, strfunc):
        """Add an extra order parameter to calculate.

        Here, we assume that the function is given as a string, which we
        will parse.

        Parameters
        ----------
        strfunc : string
            Extra function for calculation of an extra order parameter.
            It is assumed to accept a `pyretis.core.system.System`
            object as its parameter.
        """
        func = StringFunctionParser(string_function=strfunc)
        if not callable(func):
            msg = 'The given function is not callable, it will not be added!'
            logging.warning(msg)
            return False
        self.extra.append(func)


class StringFunctionParser(object):
    """Class StringFunctionParser(object).

    This class defines a simple parser for user-defined order
    parameters.

    It is based on fourFn.py, see:
    http://pyparsing.wikispaces.com/file/view/fourFn.py

    Attributes
    ----------
    pars : object of type `Forward` from `pyparsing`
        `Forward` is a subclass of `ParseElementEnhance` and is used
        here for the actual parsing.
    operators : dict
        This dict defines the different operators that can be used.
    functs : dict
        This dict defines the different scalar functions that can be
        used.
    system_functs : set
        This set defines the different functions that will make use of
        the system object.
    system : object like `System` from `pyretis.core.system`
        This object is used to access system properties, e.g. particles
        and the box.
    string_function : string
        String representation of the function that we wish to evaluate.
    """

    def __init__(self, string_function=None):
        """Initiate `StringFunctionParser`.

        Parameters
        ----------
        string_function : string, optional
            This is the string that defines the function we wish to use.
        """
        self.exprstack = []
        self.pars = self._initiate_parser()

        self.operators = {'+': operator.add,
                          '-': operator.sub,
                          '*': operator.mul,
                          '/': operator.truediv,
                          '^': operator.pow,
                          ',': lambda x, y: (x, y)}

        self.functs = {'sin': np.sin,
                       'cos': np.cos,
                       'tan': np.tan,
                       'abs': np.abs,
                       'sign': np.sign,
                       'sqrt': np.sqrt}

        self.system_functs = ['x', 'y', 'z', 'vx', 'vy', 'vz', 'distance',
                              'distance_pbc', 'pbc_x', 'pbc_y', 'pbc_z']

        self.system = None

        if string_function is not None:
            self.parse_function(string_function)
        else:
            self.string_function = None

    def system_function(self, function, args):
        """Handle calls that need to invoke 'system' functions.

        Parameters
        ----------
        function : string
            This is the function that should be called. It will need
            to be one of the strings defined in `self.system_functs`.
        args : string
            These are the arguments that should be passed to function.
        """
        xyz = {'x': 0, 'y': 1, 'z': 2}
        particles = self.system.particles
        retval = None
        if function[:8] == 'distance':
            i, j = int(args[0]), int(args[1])
            dist = particles.pos[i] - particles.pos[j]
            if function[-4:] == '_pbc':
                dist = self.system.box.pbc_dist_coordinate(dist)
            retval = dist
        elif function[:3] == 'pbc':
            dim = xyz[function[-1]]
            retval = self.system.box.pbc_coordinate_dim(args, dim)
        else:
            # simple look-up of velocity or position
            idx = int(args)
            if function[0] == 'v':
                dim = xyz[function[1]]
                coord = particles.vel[idx]
            else:
                dim = xyz[function[0]]
                coord = particles.pos[idx]
            if self.system.get_dim() == 1:
                retval = coord
            else:
                retval = coord[dim]
        return retval

    def push_first(self, toks):
        """Append parsed string elements to the stack.

        Parameters
        ----------
        toks: list of strings
            Tokens, toks[0] is to be added.

        Returns
        -------
        out : None
            Returns `None`, but updates `self.exprstack`.

        Note
        ----
        The function can also be defined as
        `push_first(self, strg, loc, toks)` where `strg` is the original
        string being parsed and `loc` is the location of the matching
        substring.
        """
        self.exprstack.append(toks[0])

    def push_uminus(self, toks):
        """Push to the expression stack.

        `push_uminus` is similar to `push_first`, however `push_uminus`
        is needed for handling expressions like `-x`.

        Parameters
        ----------
        toks: list of strings
            The tokens, `toks[0]` is to be added.

        Returns
        -------
        out : None
            Returns `None`, but updates `self.exprstack`.

        Note
        ----
        The function can also be defined as
        `push_first(self, strg, loc, toks)` where `strg` is the original
        string being parsed and `loc` is the location of the matching
        substring.
        """
        if toks and toks[0] == '-':
            self.exprstack.append('unary -')

    def evaluate_stack(self, stack):
        """Evaluate the expression stack recursively.

        Here, we also might pass the system in case we need to
        use it for accessing positions, velocities etc.

        Parameters
        ----------
        stack : list
            This is the list of operations/expressions to execute
        """
        oper = stack.pop()
        result = 0.0
        if oper == 'unary -':
            result = -self.evaluate_stack(stack)
        else:
            if oper in "+-*/^,":
                op2 = self.evaluate_stack(stack)
                op1 = self.evaluate_stack(stack)
                result = self.operators[oper](op1, op2)
            elif oper == "PI":
                result = np.pi  # 3.1415926535
            elif oper == "E":
                result = np.e  # 2.718281828
            elif oper in self.functs:
                result = self.functs[oper](self.evaluate_stack(stack))
            elif oper in self.system_functs:
                result = self.system_function(oper, self.evaluate_stack(stack))
            elif oper[0].isalpha():
                result = 0  # TODO: Check if this can be made into 0.0
            else:
                result = float(oper)
        return result

    def parse_function(self, string_function):
        """Parse the string and set up the expression stack.

        Parameters
        ----------
        string_function : string, optional
            This is the string that defines the function we wish to use.
        """
        self.exprstack = []
        self.pars.parseString(string_function, True)
        self.string_function = string_function

    def evaluate(self, system=None):
        """Evaluate the expression, assuming that is has been parsed.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system object is used to access particles and
            also the box. Here we set `self.system` to point to this
            object as it is a convenient way of accessing the required
            parameters.
        """
        if self.string_function is None or len(self.exprstack) < 1:
            return None
        else:
            self.system = system
            return self.evaluate_stack(self.exprstack[:])

    def __call__(self, system=None):
        """Function to call `self.evaluate`."""
        return self.evaluate(system=system)

    def _initiate_parser(self):
        """Helper function to initiate the parser."""
        point = Literal('.')
        exp = CaselessLiteral('E')
        fnumber = Combine(Word('+-' + nums, nums) +
                          Optional(point + Optional(Word(nums))) +
                          Optional(exp + Word('+-' + nums, nums)))
        ident = Word(alphas, alphas + nums + "_$")
        plus = Literal('+')
        minus = Literal('-')
        mult = Literal('*')
        div = Literal('/')
        comma = Literal(',')
        lpar = Literal('(').suppress()
        rpar = Literal(')').suppress()
        lbra = Literal('[').suppress()
        rbra = Literal(']').suppress()
        addop = plus | minus | comma
        multop = mult | div
        expop = Literal('^')
        # pylint: disable=C0103
        pi = CaselessLiteral('PI')
        # pylint: enable=C0103
        expr = Forward()
        atom = ((Optional(oneOf('- +')) +
                 (pi | exp | fnumber | ident +
                  ((lpar + expr + rpar) |
                   (lbra + expr + rbra))).setParseAction(self.push_first))
                | Optional(oneOf('- +')) +
                Group(lpar + expr + rpar)).setParseAction(self.push_uminus)

        factor = Forward()
        # Forward implements __lshift__ so that x << y will update x
        # therefore we here disable pylint warnings:
        # pylint: disable=W0106
        factor << atom + ZeroOrMore((expop +
                                     factor).setParseAction(self.push_first))
        term = factor + ZeroOrMore((multop +
                                    factor).setParseAction(self.push_first))
        expr << term + ZeroOrMore((addop +
                                   term).setParseAction(self.push_first))
        # pylint: enable=W0106
        return expr

    def __str__(self):
        """Return a simple string representation of the parser."""
        msg = ['{}:'.format(self.__class__.__name__)]
        msg += ['Function: {}'.format(self.string_function)]
        msg += ['Expression stack:']
        msg += ['{}'.format(self.exprstack)]
        return '\n'.join(msg)
