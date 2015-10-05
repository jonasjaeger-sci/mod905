# -*- coding: utf-8 -*-
"""This file contains classes to represent order parameters"""
from __future__ import division  # for StringFunctionParser
import numpy as np
import warnings
# imports for StringFunctionParser:
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group,
                       Optional, ZeroOrMore, Forward, nums, alphas, oneOf)
import operator


__all__ = ['OrderParameter', 'OrderParameterPosition', 'OrderParameterParse']


class OrderParameter(object):
    """
    OrderParameter(object)

    This class represents an order parameter. The order parameter
    is assumed to be a function that can uniquely be determined by
    the system object and its attributes.

    The order parameter implements __call__ so it can be calculated
    using OrderParameter(System)

    Attributes
    ----------
    desc : string
        This is a short description of the order parameter
    name : string
        A name for the order parameter (useful for output)
    """
    def __init__(self, name, desc='General order parameter'):
        """
        Initialize the OrderParameter object

        Parameters
        ----------
        name : string
            The name for the order parameter
        desc : string
            Short description of the order parameter
        """
        self.name = name
        self.desc = desc

    def calculate(self, system):
        """
        This function calculates the order parameter

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation, typically only
            system.particles.pos and/or system.particles.vel will be used.
            In some cases system.forcefield can also be used to include
            specific energies for the order parameter

        Returns
        -------
        out : float
            The order parameter
        """
        pass

    def calculate_velocity(self, system):
        """
        This function calculates the time derivative of the order parameter.

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation.

        Returns
        -------
        out : float
            The velocity of the order parameter
        """
        pass

    def __call__(self, system):
        """
        Method to conveniently call calculate and calculate_velocity.

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation.

        Returns
        -------
        out[0] : float
            The order parameter
        out[1] : float
            The velocity of the order parameter
        """
        orderp = self.calculate(system)
        orderv = self.calculate_velocity(system)
        return orderp, orderv

    def __str__(self):
        """Return a simple string representation of the order parameter."""
        msg = ['Order parameter {}'.format(self.name)]
        msg += ['{}'.format(self.desc)]
        return '\n'.join(msg)


class OrderParameterPosition(OrderParameter):
    """
    OrderParameterPosition(OrderParameter)

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
        """
        Initialize the OrderParameterPosition object

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
            This determines if periodic boundary conditions should be applied
            to the position.
        """
        description = 'Position of particle {} (dim: {})'.format(index, dim)
        super(OrderParameterPosition, self).__init__(name, desc=description)
        self.periodic = periodic
        self.index = index
        dims = {'x': 0, 'y': 1, 'z': 2}
        try:
            self.dim = dims[dim]
        except KeyError:
            warnings.warn('Unknown dimension {} requested'.format(dim))
            raise

    def calculate(self, system):
        """
        This function calculates the order parameter. Here, the order
        parameter is just the coordinate of one of the particles.

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation, typically only
            system.particles.pos and/or system.particles.vel will be used.
            In some cases system.forcefield can also be used to include
            specific energies for the order parameter

        Returns
        -------
        out : float
            The order parameter
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
        """
        This function calculates the time derivative of the order parameter.
        For this order parameter we just return the velocity.

        Parameters
        ----------
        system : object of type retis.core.system
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
    """
    OrderParameterParse(OrderParameter)

    This class defines a simple order parameter that is
    parsed from a text string given by the user. The reason
    for putting this into a object rather than as a functionality
    to the OrderParameter function is just to limit the possibility
    of parsing to one object only.

    Attributes
    ----------
    name : string
        Human readable name for the order parameter.
    orderparser : object of type StringFunctionParser
        This is used for parsing a string to a order parameter.
    ordervelparser : object of type StringFunctionParser
        This is used for parsing a string to a velocity for the order
        parameter.
    """
    def __init__(self, name, orderstr, ordervelstr):
        """
        Initialize the OrderParameterParse object

        Parameters
        ----------
        name : string
            The name for the order parameter
        orderstr : string
            This is the string representing the order parameter
        ordervelstr : string
            This is the string representing the velocity of the order
            parameter
        """
        description = 'Parsed order parameter'
        super(OrderParameterParse, self).__init__(name, desc=description)
        self.orderparser = StringFunctionParser(string_function=orderstr)
        self.ordervelparser = StringFunctionParser(string_function=ordervelstr)

    def calculate(self, system):
        """
        This function calculates the order parameter

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation, typically only
            system.particles.pos and/or system.particles.vel will be used.
            In some cases system.forcefield can also be used to include
            specific energies for the order parameter

        Returns
        -------
        out : float
            The order parameter
        """
        return self.orderparser.evaluate(system=system)

    def calculate_velocity(self, system):
        """
        This function calculates the time derivative of the order parameter.

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation.

        Returns
        -------
        out : float
            The velocity of the order parameter
        """
        return self.ordervelparser.evaluate(system=system)


class StringFunctionParser(object):
    """
    This class defines a simple parser for user-defined order parameters.
    It is based on fourFn.py, see
    http://pyparsing.wikispaces.com/file/view/fourFn.py

    Attributes
    ----------
    pars :
        This is responsible for the actual parsing
    operators : dict
        This dict defines the different operators that can be used.
    functs : dict
        This dict defines the different scalar functions that can be used.
    system_functs : set
        This set defines the different functions that will make use of
        the system object
    system : object of type retis.core.system
        This object is used to access system properties, e.g. partilces
        and the box.
    string_function : string
        String representation of the function that we wish to evaluate.
    """
    def __init__(self, string_function=None):
        """
        Initialte the function

        Parameters
        ----------
        string_function : string, optional
            This is the string that defines the function we wish to use.
        """
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
        """
        This handles the calls that need to envoke system functions.

        Parameters
        ----------
        function : string
            This is the function that should be called. I will need
            to be one of the strings defined in self.system_functs
        args : string
            These are the arguments that should be passed to function.
        """
        # print('Calling with:',function, args)
        xyz = {'x': 0, 'y': 1, 'z': 2}
        particles = self.system.particles
        retval = None
        if function[:8] == 'distance':
            # print('Calculate dist between particles {} and {}'.format(i, j))
            i, j = int(args[0]), int(args[1])
            dist = particles.pos[i] - particles.pos[j]
            if function[-4:] == '_pbc':
                dist = self.system.box.pbc_dist_coordinate(dist)
            retval = dist
        elif function[:3] == 'pbc':
            # print('Apply pbc {} to: {}'.format(function,args))
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
        """
        This will append parsed string elements
        to the stack.

        Parameters
        ----------
        toks: list of strings
            Tokens, toks[0] is to be added

        Returns
        -------
        N/A but updates self.exprstack

        Note
        ----
        The function can also be defined as push_first(self, strg, loc, toks)
        where strg is the original string being parsed and loc is the location
        of the matching substring.
        """
        self.exprstack.append(toks[0])

    def push_uminus(self, toks):
        """
        This will push to the expression stack,
        similar to ``push_first``, however this function is needed for
        handling expressions like ``-x''

        Parameters
        ----------
        toks: list of strings
            Tokens, toks[0] is to be added

        Returns
        -------
        N/A but updates self.exprstack

        Note
        ----
        The function can also be defined as push_first(self, strg, loc, toks)
        where strg is the original string being parsed and loc is the location
        of the matching substring.
        """
        if toks and toks[0] == '-':
            self.exprstack.append('unary -')

    def evaluate_stack(self, stack):
        """
        The method evaluates the stack recursively.
        Here, we also might pass the system in case we need to
        use it for accessing positions, velocities etc.

        Parameters
        ----------
        stack : list
            This is the list of operations/expressions to execute
        system : object of type retis.core.system
            The system object is used to access particles and
            also the box.
        """
        oper = stack.pop()
        result = 0
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
                result = 0
            else:
                result = float(oper)
        return result

    def parse_function(self, string_function):
        """
        This method will parse the string and set up
        self.exprstack.
        """
        self.exprstack = []
        self.pars.parseString(string_function, True)
        self.string_function = string_function

    def evaluate(self, system=None):
        """
        Evaluate the expression, assuming that is has been parsed.

        Parameters
        ----------
        system : object of type retis.core.system
            The system object is used to access particles and
            also the box. Here we set self.system to point to this
            object as it is a convenient way of accessing the required
            paramters.
        """
        if self.string_function is None or len(self.exprstack) < 1:
            return None
        else:
            self.system = system
            return self.evaluate_stack(self.exprstack[:])

    def _initiate_parser(self):
        """
        Helper function to initiate the parser.
        """
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
