# -*- coding: utf-8 -*-

"""
constants.py
This module defines some natural constants, in different units
"""

kB = {'eV/K':8.6173324e-05, 'J/K': 1.3806488e-23, 'lj': 1.0}
NA = 6.02214129e23

# define some conversions of units
# note that we here base the conversion from lennard jones
# units on the parameters for Argon given by 
# Rowley et al., Journal of Computational Physics, vol. 17, pp. 401-414, 1975
# doi: http://dx.doi.org/10.1016/0021-9991(75)90042-X
# lj units:
# real units:
# distance in Å
# mass in u
# energy Kcal/mol
# time in fs
convert = {'length': {}, 'mass': {}, 'energy': {}}
convert['length']['nm', 'Å'] = 10.0
convert['length']['lj', 'Å'] = 3.405
convert['mass']['lj', 'kg'] = 6.690e-26
convert['mass']['lj', 'g/mol'] = 39.948
convert['energy']['lj', 'J'] = 119.8*kB['J/K']
convert['energy']['kcal', 'J'] = 4184.
convert['energy']['kcal', 'kcal/mol'] = NA
convert['energy']['lj', 'kcal/mol'] = convert['energy']['lj', 'J']*convert['energy']['kcal', 'kcal/mol']/convert['energy']['kcal', 'J']


# time: length * (mass/energy)**(0.5)

#convert['time']['lj', 'ps'] = 1e12*(convert['length']['lj','Å']
#convert['lj-time', 'ps'] = 1e12*(
#                          (convert['lj-mass' ,'kg']/(119.8*kB['J/K']))**(0.5))

