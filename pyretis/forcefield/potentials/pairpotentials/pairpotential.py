# -*- coding: utf-8 -*-
"""Convenience functions for pair potentials."""
import itertools
import logging
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['mixing_parameters', 'generate_pair_interactions']


def _check_pair_parameters(parameters):
    """This will just check that the required parameters are given.

    If the parameters are not given, we will just set them do default values.

    Parameters
    ----------
    parameters : dict
        The dict with the settings for the potential

    Note
    ----
    This function will not return anything, but it will update the input
    `parameters` with default values.
    """
    for pair in parameters:
        if pair == 'mixing':
            continue
        for key in ('epsilon', 'sigma'):
            if not key in parameters[pair]:
                msg = '{} for {} not given. Set to 0.0'.format(key, pair)
                logger.warning(msg)
                parameters[pair][key] = 0.0
        if not 'rcut' in parameters[pair]:
            factor = parameters[pair].get('factor', 0.0)
            rcut = factor * parameters[pair]['sigma']
            parameters[pair]['rcut'] = rcut
            msg = ('rcut for {} not given. Using factor to set it to:'
                   '{} * {} = {}')
            msg = msg.format(pair, parameters[pair]['sigma'], factor, rcut)
            logger.warning(msg)


def generate_pair_interactions(parameters):
    """Function to generate pair parameters from atom parameters.

    The parameters are given as a dictionary where the keys are
    either just string -- which defines atom parameters -- or tuples
    which define pair interactions.

    Parameters
    ----------
    parameters : dict
        This dict contain the atom parameters.
    """
    _check_pair_parameters(parameters)
    mixing = parameters.get('mixing', None)
    atoms = []
    pair_param = {}
    for key in parameters:
        if key == 'mixing' or isinstance(key, tuple):
            continue
        atoms.append(key)
    for (atmi, atmj) in itertools.product(atoms, atoms):
        pari = parameters[atmi]
        parj = parameters[atmj]
        if (atmi, atmj) in pair_param:
            if not (atmj, atmi) in pair_param:
                pair_param[atmj, atmi] = pair_param[atmi, atmj]
            continue
        if (atmi, atmj) in parameters:
            pair_param[atmi, atmj] = dict(parameters[atmi, atmj])
            pair_param[atmj, atmi] = pair_param[atmi, atmj]
            continue
        elif (atmj, atmi) in parameters:
            pair_param[atmj, atmi] = dict(parameters[atmj, atmi])
            pair_param[atmi, atmj] = pair_param[atmj, atmi]
            continue
        if atmi == atmj:
            eps_ij = pari['epsilon']
            sig_ij = pari['sigma']
            rcut_ij = pari['rcut']
        else:
            eps_ij, sig_ij, rcut_ij = mixing_parameters(pari['epsilon'],
                                                        pari['sigma'],
                                                        pari['rcut'],
                                                        parj['epsilon'],
                                                        parj['sigma'],
                                                        parj['rcut'], mixing)
        pair_param[atmi, atmj] = {'epsilon': eps_ij, 'sigma': sig_ij,
                                  'rcut': rcut_ij}
        if not (atmj, atmi) in pair_param:
            pair_param[atmj, atmi] = pair_param[atmi, atmj]
    return pair_param


def mixing_parameters(epsilon_i, sigma_i, rcut_i, epsilon_j, sigma_j, rcut_j,
                      mixing='geometric'):
    r"""Define the so-called mixing rules.

    These mixing rules are used for some force fields when generating cross
    interactions. The known mixing rules are:

    1. Geometric:

       * :math:`\epsilon_{ij} = \sqrt{\epsilon_{i} \times \epsilon_{j}}`

       * :math:`\sigma_{ij} = \sqrt{\sigma_{i} \times \sigma_{j}}`

       * :math:`r_{\text{cut},ij} = \sqrt{r_{\text{cut},i} \times r_{\text{cut},j}}`

    2. Arithmetic:

       * :math:`\epsilon_{ij} = \sqrt{\epsilon_{i} \times \epsilon_{j}}`

       * :math:`\sigma_{ij} = \frac{\sigma_{i} \times \sigma_{j}}{2}`

       * :math:`r_{\text{cut},ij} = \frac{r_{\text{cut},i} \times r_{\text{cut},j}}{2}`

    3. Sixthpower

       * :math:`\epsilon_{ij} = 2 \sqrt{\epsilon_{i} \times \epsilon_{j}} \frac{\sigma_i^3 \times \sigma_j^3}{\sigma_i^6 + \sigma_j^6}`

       * :math:`\sigma_{ij} = \left( \frac{\sigma_{i}^6 \times \sigma_{j}^6}{2} \right)^{1/6}`

       * :math:`r_{\text{cut},ij} = \left(\frac{r_{\text{cut},i}^6 \times r_{\text{cut},j}^6}{2}\right)^{1/6}`


    Parameters
    ----------
    epsilon_i and epsilon_j : floats
        For a Lennard-Jones potential, this corresponds to the epsilon
        parameters.
    sigma_i and sigma_j : floats
        For a Lennard-Jones potential, this corresponds to the
        sigma parameters.
    mixing :  string
        Represents what kind of mixing that should be done.

    Returns
    -------
    out[0] : float
        The mixed ``epsilon_ij`` parameter.
    out[1] : float
        The mixed ``sigma_ij`` parameter.
    out[2] : float
        The mixed ``rcut_ij`` parameter.
    """
    if mixing not in ('geometric', 'arithmetic', 'sixthpower'):
        epsilon_ij = 0.0
        sigma_ij = 0.0
        rcut_ij = 0.0
        logger.warning('No mixing requested. Cross interactions set to zero')
    if mixing == 'geometric':
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j)
        sigma_ij = np.sqrt(sigma_i * sigma_j)
        rcut_ij = np.sqrt(rcut_i * rcut_j)
    elif mixing == 'arithmetic':
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j)
        sigma_ij = 0.5 * (sigma_i + sigma_j)
        rcut_ij = 0.5 * (rcut_i + rcut_j)
    elif mixing == 'sixthpower':
        si3 = sigma_i**3
        si6 = si3**2
        sj3 = sigma_j**3
        sj6 = sj3**2
        avgs6 = 0.5 * (si6 + sj6)
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j) * si3 * sj3 / avgs6
        sigma_ij = avgs6**(1.0 / 6.0)
        rcut_ij = (0.5 * (rcut_i**6 + rcut_j**6))**(1.0 / 6.0)
    return epsilon_ij, sigma_ij, rcut_ij
