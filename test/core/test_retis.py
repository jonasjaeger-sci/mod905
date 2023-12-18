# -*- coding: utf-8 -*-
# Copyright (c) 2023, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the RETIS method(s)."""
import copy
import logging
import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch
from pyretis.core.common import (relative_shoots_select,
                                 null_move, soft_partial_exit,
                                 compute_weight)
from pyretis.core.pathensemble import PathEnsemble
from pyretis.core.random_gen import MockRandomGenerator
from pyretis.core.retis import (high_acc_swap,
                                make_retis_step,
                                repptis_swap,
                                retis_moves,
                                retis_swap,
                                retis_swap_wrapper,
                                retis_swap_zero)
from pyretis.inout.common import make_dirs
from pyretis.initiation import initiate_path_simulation
from pyretis.inout.settings import fill_up_tis_and_retis_settings
from .help import (
    create_ensembles_and_paths,
    make_internal_path,
    MockEngine,
    MockOrder,
    prepare_test_simulation,
)

logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))


def compare_path_skip_generated(path1, path2):
    """Compare two paths, but skip the generated attribute."""
    gen1 = copy.deepcopy(path1.generated)
    gen2 = copy.deepcopy(path2.generated)
    del path1.generated
    del path2.generated
    equal = path1 == path2
    path1.generated = gen1
    path2.generated = gen2
    return equal


class RetisTestSwap(unittest.TestCase):
    """The RETIS specific methods, for Internal simulations."""

    def test_swap_internal(self):
        """Test swapping of paths."""
        settings, ensembles = create_ensembles_and_paths()
        # 1) Try [0^+] with [1^+]:
        # This move should be rejected, we here check that
        # the currently accepted paths are not modified.
        path1 = ensembles[1]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[2]['path_ensemble'].last_path
        path2c = path2.copy()

        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '001'))
            make_dirs(os.path.join(tempdir, '002'))
            settings['ensemble'][1]['simulation']['exe_path'] = tempdir
            settings['ensemble'][2]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=1, settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'NCR')
        # Check that the return trial paths are identical
        # to the accepted paths, with the exception of the move:
        self.assertTrue(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertTrue(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated == trial1.generated)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

        # 2) Try [3^+] with [4^+]
        # This move should be accepted:
        path1 = ensembles[3]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[4]['path_ensemble'].last_path
        path2c = path2.copy()

        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '003'))
            make_dirs(os.path.join(tempdir, '004'))
            settings['ensemble'][3]['simulation']['exe_path'] = tempdir
            settings['ensemble'][4]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=3, settings=settings, cycle=0)
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Here, path1 and trial2 should be identical:
        self.assertTrue(path1 is trial2)
        self.assertTrue(path1 is ensembles[4]['path_ensemble'].last_path)
        # Here, path2 and trial1 should be identical:
        self.assertTrue(path2 is trial1)
        self.assertTrue(path2 is ensembles[3]['path_ensemble'].last_path)
        # Copies should be identical with the exception of the
        # generated attribute and status.
        path1c.status = 'ACC'
        path2c.status = 'ACC'
        self.assertTrue(compare_path_skip_generated(path1, path1c))
        self.assertFalse(path1.generated[0] == path1c.generated[0])
        self.assertTrue(compare_path_skip_generated(path2, path2c))
        self.assertFalse(path2.generated[0] == path2c.generated[0])

    def test_swap_internal_wf(self):
        """Test swapping of paths with the wf move."""
        settings, ensembles = create_ensembles_and_paths()
        settings['tis']['high_accept'] = True

        with tempfile.TemporaryDirectory() as tempdir:
            # Test retis_swap_zero() that will perform sh in both 000 and 001,
            # but we define 001 to be a WF HA ensemble, hence high_acc_swap
            # has to be called.
            settings['ensemble'][1]['tis']['shooting_move'] = 'wf'
            settings['ensemble'][1]['tis']['high_accept'] = True
            make_dirs(os.path.join(tempdir, '000'))
            make_dirs(os.path.join(tempdir, '001'))
            settings['ensemble'][0]['simulation']['exe_path'] = tempdir
            settings['ensemble'][1]['simulation']['exe_path'] = tempdir
            ensembles[1]['engine'].time = 10
            accept, (_, _), status = retis_swap_zero(
                ensembles, settings=settings, cycle=0)
            self.assertFalse(accept)
            self.assertEqual(status, 'HAS')
            accept, (trial1, trial2), status = retis_swap_zero(
                ensembles, settings=settings, cycle=0)
            self.assertTrue(accept)
            self.assertEqual(status, 'ACC')
            self.assertEqual(trial1.weight, 1)
            self.assertEqual(trial2.weight, 5)

            # We test retis_swap() with WF HA in both 003 and 004 ensembles
            for i in [3, 4]:
                settings['ensemble'][i]['tis']['shooting_move'] = 'wf'
                settings['ensemble'][i]['tis']['high_accept'] = True
                make_dirs(os.path.join(tempdir, f'00{i}'))
                settings['ensemble'][i]['simulation']['exe_path'] = tempdir
            settings['ensemble'][4]['tis']['interface_cap'] = 5.0
            accept, (trial1, trial2), status = retis_swap(
                ensembles, idx=3, settings=settings, cycle=0)
            self.assertTrue(accept)
            self.assertEqual(status, 'ACC')
            self.assertEqual(trial1.weight, 120)
            self.assertEqual(trial2.weight, 37)

    def test_swap_internal_repptis_SWD(self):
        """Test swapping of paths with repptis
        1) Try [0^+-'] <--> [1^+-]:
        1) Try    LML  <-->   LMR
        This move should fail due to incompatible swap directions (SWD)
        """
        settings, ensembles = create_ensembles_and_paths(task='repptis')

        path1 = ensembles[1]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[2]['path_ensemble'].last_path
        path2c = path2.copy()
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '001'))
            make_dirs(os.path.join(tempdir, '002'))
            settings['ensemble'][1]['simulation']['exe_path'] = tempdir
            settings['ensemble'][2]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=1, settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'SWD')
        # Check that the return trial paths are identical
        # to the accepted paths, with the exception of the move:
        self.assertTrue(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertTrue(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated == trial1.generated)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

    def test_swap_internal_repptis_0minus_fail(self):
        """Test swapping [0-] and [0+-'] in repptis.
        A RML path in [0+-'] cannot be swapped with [0-] (at least not for
        the current implementation.

        """
        settings, ensembles = create_ensembles_and_paths(task='repptis',
                                                         number=1)
        ensembles[0]['rgen'].seed = 5
        path1 = ensembles[0]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[1]['path_ensemble'].last_path
        path2c = path2.copy()
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '000'))
            make_dirs(os.path.join(tempdir, '001'))
            settings['ensemble'][0]['simulation']['exe_path'] = tempdir
            settings['ensemble'][1]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=0, settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'SWD')
        # Check that the return trial paths have changed.
        self.assertTrue(compare_path_skip_generated(path1, trial2))
        self.assertTrue(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertFalse(path2.generated == trial1.generated)
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

    def test_swap_internal_repptis_SWH(self):
        """Test swapping of paths with repptis
        2) Try [1^+] with [2^+]
        2) Try   LMR <--> LML
        Depending on the seed for ens 0, this move is accepted or not.
        Yes, ensemble 0, as the prop_dir draw depends on that (there are
        issues with seed coupling in the random generator. To avoid coupling,
        both ensembles in the swap move drew from the same generator.)

        2A) Good prop direction, but first path propagation exceeds maxlen.
        """
        settings, ensembles = create_ensembles_and_paths(task='repptis')
        ensembles[0]['rgen'].seed = 5
        path1 = ensembles[2]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[3]['path_ensemble'].last_path
        path2c = path2.copy()
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '002'))
            make_dirs(os.path.join(tempdir, '003'))
            settings['ensemble'][2]['simulation']['exe_path'] = tempdir
            settings['ensemble'][3]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=2, settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'SWH')
        # Check that the return trial path [i+-] has changed, while the
        # trial1 path is identical to the last accepted path of[i+-].
        self.assertTrue(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertFalse(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated == trial1.generated)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

    def test_swap_internal_repptis_ACC0(self):
        """Test swapping of paths with repptis
        2) Try [1^+] with [2^+]
        2) Try   LMR <--> LML
        Depending on the seed for ens 0, this move is accepted or not.
        Yes, ensemble 0, as the prop_dir draw depends on that (there are
        issues with seed coupling in the random generator. To avoid coupling,
        both ensembles in the swap move drew from the same generator.)

        2B) Good prop direction, and it works
        """
        settings, ensembles = create_ensembles_and_paths(task='repptis',
                                                         total_eclipse=10000)
        ensembles[0]['rgen'].seed = 4
        path1 = ensembles[2]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[3]['path_ensemble'].last_path
        path2c = path2.copy()
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '002'))
            make_dirs(os.path.join(tempdir, '003'))
            settings['ensemble'][2]['simulation']['exe_path'] = tempdir
            settings['ensemble'][3]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=2, settings=settings, cycle=0)
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Check that the return trial path [i+-] has changed, while the
        # trial1 path is identical to the last accepted path of[i+-].
        self.assertFalse(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertFalse(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated == trial1.generated)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

    def test_swap_internal_repptis_ACC1(self):
        """Test swapping of paths with repptis
        3) Swap [3^+] <--> [4^+]
        3) Swap   RMR <--> LML: always acceptable propdirs
        3) We change total_eclipse to a very large number to force
           This move to be accepted.
        """
        settings, ensembles = create_ensembles_and_paths(task='repptis',
                                                         total_eclipse=10000)
        path1 = ensembles[4]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[5]['path_ensemble'].last_path
        path2c = path2.copy()
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '004'))
            make_dirs(os.path.join(tempdir, '005'))
            settings['ensemble'][4]['simulation']['exe_path'] = tempdir
            settings['ensemble'][5]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=4, settings=settings, cycle=0)
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Check that the return trial paths are identical
        # to the accepted paths, with the exception of the move:
        self.assertFalse(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertFalse(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated == trial1.generated)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

    def test_swap_internal_repptis_ACC2(self):
        """Test swapping of paths with repptis
        3) Swap [3^+] <--> [4^+]
        3) Swap   RMR <--> LML: always acceptable propdirs
        3) We change total_eclipse to a very large number to force
           This move to be accepted.
        """
        settings, ensembles = create_ensembles_and_paths(task='repptis',
                                                         total_eclipse=10000)
        ensembles[0]['rgen'].seed = 1
        path1 = ensembles[4]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[5]['path_ensemble'].last_path
        path2c = path2.copy()
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '004'))
            make_dirs(os.path.join(tempdir, '005'))
            settings['ensemble'][4]['simulation']['exe_path'] = tempdir
            settings['ensemble'][5]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=4, settings=settings, cycle=0)
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Check that the return trial paths are identical
        # to the accepted paths, with the exception of the move:
        self.assertFalse(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertFalse(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated == trial1.generated)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

    def test_swap_internal_repptis_FTX(self):
        """Test swapping of paths with repptis
        4) Swap [3^+] <--> [4^+]
        4) Swap   RMR <--> LML: always acceptable propdirs
        4) We total_eclipse to a very large number to force
        4A) but we decrease maxlen to force BTX/FTX in first extension
        4B) but we decrease maxlen to force BTX/FTX in second extension

        4A) too long in first extension
        """
        settings, ensembles = create_ensembles_and_paths(task='repptis',
                                                         total_eclipse=10000)
        path1 = ensembles[4]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[5]['path_ensemble'].last_path
        path2c = path2.copy()
        # decrease maxlen in ensemble 4
        settings['ensemble'][4]['tis']['maxlength'] = 200
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '004'))
            make_dirs(os.path.join(tempdir, '005'))
            settings['ensemble'][4]['simulation']['exe_path'] = tempdir
            settings['ensemble'][5]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=4, settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'SWH')
        # Check that the return trial paths are identical
        # to the accepted paths, with the exception of the move:
        self.assertTrue(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertFalse(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated == trial1.generated)
        # Check that trial1 reached the maximum length:
        self.assertEqual(len(trial1.phasepoints), 200)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

        # 4B) too long in second extension
        settings, ensembles = create_ensembles_and_paths(task='repptis',
                                                         total_eclipse=10000)
        path1 = ensembles[4]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[5]['path_ensemble'].last_path
        path2c = path2.copy()
        # decrease maxlen in ensemble 5
        settings['ensemble'][5]['tis']['maxlength'] = 200
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '004'))
            make_dirs(os.path.join(tempdir, '005'))
            settings['ensemble'][4]['simulation']['exe_path'] = tempdir
            settings['ensemble'][5]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap_wrapper(
                ensembles, idx=4, settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'FTX')
        # Check that the return trial paths are identical
        # to the accepted paths, with the exception of the move:
        self.assertFalse(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated == trial2.generated)
        self.assertFalse(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated == trial1.generated)
        # Check that trial2 reached the maximum length:
        self.assertEqual(len(trial2.phasepoints), 200)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

        # Testing for BTS and FTS makes no sense for REPPTIS swap, as it is
        # impossible by definition.

    def test_high_acc_ss_wt_swap(self):
        """Test weights and high_acc_swap method for the ss and wt move."""
        settings, ensembles = create_ensembles_and_paths()
        rgen = MockRandomGenerator(seed=3)
        interfaces = [-1., 0., 1., 2., 10]
        # 1) Try [0^+] with [1^+]:
        # This move should be reject, we here check that
        # the currently accepted paths are not modified.
        path1 = ensembles[2]['path_ensemble'].last_path.copy()
        path2 = ensembles[4]['path_ensemble'].last_path.copy()
        intf0 = [interfaces[0], interfaces[1], interfaces[-1]]
        intf1 = [interfaces[0], interfaces[2], interfaces[-1]]

        success, status = high_acc_swap([path1, path2], rgen,
                                        intf0,
                                        intf1,
                                        ['ss', 'ss'])
        self.assertFalse(success)
        self.assertEqual(status, 'HAS')

        path1 = ensembles[3]['path_ensemble'].last_path.copy()
        path2 = ensembles[4]['path_ensemble'].last_path.copy()
        success, status = high_acc_swap([path1, path2], rgen,
                                        intf0,
                                        intf1,
                                        ['ss', 'ss'])
        self.assertTrue(success)
        self.assertEqual(status, 'ACC')

        # Now let's check with ss only in path1
        success, status = high_acc_swap([path1, path2], rgen,
                                        intf0,
                                        intf1,
                                        ['ss', 'wt'])
        self.assertTrue(success)
        self.assertEqual(status, 'ACC')

        path1 = ensembles[4]['path_ensemble'].last_path.copy()
        path2 = ensembles[4]['path_ensemble'].last_path.copy()
        success, status = high_acc_swap([path1, path2], rgen,
                                        intf0,
                                        intf1,
                                        ['ss', 'wt'])
        self.assertTrue(success)
        self.assertEqual(status, 'ACC')

        # Now let's check with ss only in path2
        success, status = high_acc_swap([path1, path2], rgen,
                                        intf0,
                                        intf1,
                                        ['wt', 'ss'])
        self.assertTrue(success)
        self.assertEqual(status, 'ACC')

        path1 = ensembles[4]['path_ensemble'].last_path.copy()
        path2 = ensembles[4]['path_ensemble'].last_path.copy()
        success, status = high_acc_swap([path1, path2], rgen,
                                        intf0,
                                        intf1,
                                        ['wt', 'ss'])
        self.assertTrue(success)
        self.assertEqual(status, 'ACC')

        path1 = ensembles[3]['path_ensemble'].last_path.copy()
        success, status = high_acc_swap([path1, path2], rgen,
                                        intf0,
                                        intf1,
                                        ['wt', 'ss'])
        self.assertTrue(success)
        self.assertEqual(status, 'ACC')

        settings['tis']['high_accept'] = True
        fill_up_tis_and_retis_settings(settings)
        accept, (_, _), status = retis_swap(ensembles,
                                            idx=3,
                                            settings=settings,
                                            cycle=1)
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')

        # Check that we can use the ss weights:
        ensembles[3]['path_ensemble'].last_path.set_move('ss')
        ensembles[4]['path_ensemble'].last_path.set_move('ss')
        settings['ensemble'][4]['tis']['shooting_move'] = 'ss'
        accept, (_, _), status = retis_swap(ensembles, idx=3,
                                            settings=settings,
                                            cycle=1)
        self.assertEqual(ensembles[4]['path_ensemble'].last_path.weight, 2)

    def test_high_acc_wf_swap(self):
        """Test weights and high_acc_swap method for the wf move."""
        _, ensembles = create_ensembles_and_paths()
        rgen = MockRandomGenerator(seed=3)
        interfaces = [-1., 0., 1., 2., 10]
        # 1) Try [0^+] with [1^+]:
        path1 = ensembles[2]['path_ensemble'].last_path.copy()
        path2 = ensembles[4]['path_ensemble'].last_path.copy()
        intf1 = [interfaces[0], interfaces[1], interfaces[-1]]
        intf2 = [interfaces[0], interfaces[2], interfaces[-1]]

        c1_old = compute_weight(path1, intf1, 'wf')
        c2_old = compute_weight(path2, intf2, 'wf')
        c1_new = compute_weight(path1, intf2, 'wf')
        c2_new = compute_weight(path2, intf1, 'wf')
        self.assertEqual([c1_old, c2_old, c1_new, c2_new], [54, 120, 0, 120])
        success, status = high_acc_swap([path1, path2], rgen, intf1,
                                        intf2, ['wf', 'wf'])
        self.assertFalse(success)
        self.assertEqual(status, 'HAS')

        success, status = high_acc_swap([path1, path2], rgen, intf2,
                                        intf1, ['wf', 'wf'])
        self.assertTrue(success)
        self.assertEqual(status, 'ACC')

    def test_nullmove_internal(self):
        """Test the null move."""
        _, ensembles = create_ensembles_and_paths()
        for ens in ensembles:
            path0 = ens['path_ensemble'].last_path
            before = ens['path_ensemble'].last_path.copy()
            accept, trial, status = null_move(ens, 1)
            self.assertTrue(accept)
            self.assertTrue(path0 is trial)
            self.assertTrue(status == 'ACC')
            self.assertTrue(path0.generated[0] == '00')
            after = ens['path_ensemble'].last_path
            self.assertTrue(compare_path_skip_generated(before, after))

    def test_swap_zero_internal_repptis(self):
        """Test the repptis swap zero move."""
        settings, ensembles = create_ensembles_and_paths()
        settings['simulation']['task'] = 'repptis'

        path1 = ensembles[0]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[1]['path_ensemble'].last_path
        path2c = path2.copy()
        ensembles[1]['engine'].time = 6
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '000'))
            make_dirs(os.path.join(tempdir, '001'))
            settings['ensemble'][0]['simulation']['exe_path'] = tempdir
            settings['ensemble'][1]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = repptis_swap(ensembles,
                                                            idx=0,
                                                            settings=settings,
                                                            cycle=0)
        # This should be accepted:
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)
        # Last point in trial 1 is second in path 2:
        self.assertEqual(trial1.phasepoints[-1], path2.phasepoints[1])
        # Second last point in trial 1 is first in path 2:
        self.assertEqual(trial1.phasepoints[-2], path2.phasepoints[0])
        # First point in trial 2 is second last in path 1:
        self.assertEqual(trial2.phasepoints[0], path1.phasepoints[-2])
        # Second point in trial 2 is last point in path 1:
        self.assertEqual(trial2.phasepoints[1], path1.phasepoints[-1])

    def test_swap_zero_internal(self):
        """Test the retis swap zero move."""
        settings, ensembles = create_ensembles_and_paths()

        path1 = ensembles[0]['path_ensemble'].last_path
        path1c = path1.copy()
        path2 = ensembles[1]['path_ensemble'].last_path
        path2c = path2.copy()
        ensembles[1]['engine'].time = 6
        with tempfile.TemporaryDirectory() as tempdir:
            make_dirs(os.path.join(tempdir, '000'))
            make_dirs(os.path.join(tempdir, '001'))
            settings['ensemble'][0]['simulation']['exe_path'] = tempdir
            settings['ensemble'][1]['simulation']['exe_path'] = tempdir
            accept, (trial1, trial2), status = retis_swap(ensembles,
                                                          idx=0,
                                                          settings=settings,
                                                          cycle=0)
        # This should be accepted:
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)
        # Last point in trial 1 is second in path 2:
        self.assertEqual(trial1.phasepoints[-1], path2.phasepoints[1])
        # Second last point in trial 1 is first in path 2:
        self.assertEqual(trial1.phasepoints[-2], path2.phasepoints[0])
        # First point in trial 2 is second last in path 1:
        self.assertEqual(trial2.phasepoints[0], path1.phasepoints[-2])
        # Second point in trial 2 is last point in path 1:
        self.assertEqual(trial2.phasepoints[1], path1.phasepoints[-1])

    def test_swap_zero_internal_0L(self):
        ens0 = PathEnsemble(ensemble_number=0, interfaces=(0, 2, 2))
        ens1 = PathEnsemble(ensemble_number=1, interfaces=(2, 2.5, 3))
        path0 = make_internal_path((0, 2.1), (100, 2.2), (50, -1),
                                   ens0.interfaces[1])
        path1 = make_internal_path((0, 1.9), (100, 1.8), (50, 2.5),
                                   ens1.interfaces[1])

        ens0.add_path_data(path0, status='ACC')
        ens1.add_path_data(path1, status='ACC')
        ens0.last_path = path0
        ens1.last_path = path1

        order_f = MockOrder()
        engine = MockEngine(10, turn_around=15)
        engine.delta_v *= -1
        ensemble0 = {'path_ensemble': ens0, 'engine': engine,
                     'order_function': order_f, 'interfaces': [0, 2, 2]}
        ensemble1 = {'path_ensemble': ens1, 'engine': engine,
                     'order_function': order_f, 'interfaces': [2, 2.5, 3]}
        with tempfile.TemporaryDirectory() as tpdr:
            make_dirs(os.path.join(tpdr, '000'))
            make_dirs(os.path.join(tpdr, '001'))
            out = retis_swap_zero(
                ensembles=[ensemble0, ensemble1],
                settings={'ensemble': [{'tis': {'maxlength': 1000},
                                        'simulation': {'exe_path': tpdr}}]*2},
                cycle=1)
        self.assertFalse(out[0])
        self.assertEqual(out[1][0].status, "0-L")
        self.assertEqual(out[1][1].status, "0-L")
        self.assertEqual(out[1][0].check_interfaces(ens0.interfaces)[:2],
                         ('L', 'R'))

    def test_swap_zero_internal_0L_acc(self):
        ens0 = PathEnsemble(ensemble_number=0, interfaces=(0, 2, 2))
        ens1 = PathEnsemble(ensemble_number=1, interfaces=(2, 2.5, 3))
        path0 = make_internal_path((0, 2.1), (100, 2.2), (50, -1),
                                   ens0.interfaces[1])
        path1 = make_internal_path((0, 1.9), (100, 1.8), (50, 2.5),
                                   ens1.interfaces[1])

        ens0.add_path_data(path0, status='ACC')
        ens1.add_path_data(path1, status='ACC')
        ens0.last_path = path0
        ens1.last_path = path1

        order_f = MockOrder()
        engine = MockEngine(5, turn_around=100)
        ensemble0 = {'path_ensemble': ens0, 'engine': engine,
                     'order_function': order_f, 'interfaces': [0, 2, 2]}
        ensemble1 = {'path_ensemble': ens1, 'engine': engine,
                     'order_function': order_f, 'interfaces': [2, 2.5, 3]}
        with tempfile.TemporaryDirectory() as tpdr:
            make_dirs(os.path.join(tpdr, '000'))
            make_dirs(os.path.join(tpdr, '001'))
            out = retis_swap_zero(
                ensembles=[ensemble0, ensemble1],
                settings={'ensemble': [{'tis': {'maxlength': 1000},
                                        'simulation': {'exe_path': tpdr}}]*2,
                          'tis': {'high_accept': False}},
                cycle=1)
        self.assertTrue(out[0])
        self.assertEqual(out[1][0].status, "ACC")
        self.assertEqual(out[1][1].status, "ACC")
        self.assertEqual(out[1][0].check_interfaces(ens0.interfaces)[:2],
                         ('R', 'R'))

    def test_swap_zero_internal_ftx(self):
        """Test the swap zero when we force a FTX"""
        settings, ensembles = create_ensembles_and_paths()
        with tempfile.TemporaryDirectory() as tempdir:
            ensembles[0]['engine'] = MockEngine(timestep=1.0, turn_around=500)
            settings['ensemble'][0]['tis']['maxlength'] = 100
            settings['ensemble'][0]['simulation']['exe_path'] = tempdir
            settings['ensemble'][1]['simulation']['exe_path'] = tempdir
            make_dirs(os.path.join(tempdir, '000'))
            make_dirs(os.path.join(tempdir, '001'))
            accept, _, status = retis_swap(ensembles, idx=0,
                                           settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'FTX')

    def test_swap_zero_internal_btx(self):
        """Test the swap zero when we force a BTX"""
        settings, ensembles = create_ensembles_and_paths()
        for i_ens, ens in enumerate(ensembles):
            ens['engine'] = MockEngine(timestep=1.0, turn_around=500)
            settings['ensemble'][i_ens]['tis']['maxlength'] = 3
            with tempfile.TemporaryDirectory() as tempdir:
                settings['ensemble'][0]['simulation']['exe_path'] = tempdir
                settings['ensemble'][1]['simulation']['exe_path'] = tempdir
                make_dirs(os.path.join(tempdir, '000'))
                make_dirs(os.path.join(tempdir, '001'))
                accept, _, status = retis_swap(ensembles, idx=0,
                                               settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'BTX')

    def test_swap_zero_internal_bts(self):
        """Test the swap zero when we force a BTS"""
        settings, ensembles = create_ensembles_and_paths()
        for ens in ensembles:
            ens['engine'] = MockEngine(timestep=200.0)
        # We set up for BTS by making a faulty initial path:
        path = make_internal_path((0, -0.9), (100, -1.2), (50, -0.2), None)
        ensembles[1]['path_ensemble'].add_path_data(path, 'ACC')
        accept, _, status = retis_swap(ensembles, idx=0,
                                       settings=settings, cycle=1)
        self.assertFalse(accept)
        self.assertEqual(status, 'BTS')

    def test_swap_zero_internal_non_accept(self):
        """Test the swap zero when we force a FTS"""
        settings, ensembles = create_ensembles_and_paths()
        # We set up for FTS by making a faulty initial path:
        with tempfile.TemporaryDirectory() as tempdir:
            settings['ensemble'][0]['simulation']['exe_path'] = tempdir
            settings['ensemble'][1]['simulation']['exe_path'] = tempdir
            make_dirs(os.path.join(tempdir, '000'))
            make_dirs(os.path.join(tempdir, '001'))
            path = make_internal_path((0, -0.9), (100, -1.2), (50, -5), None)
            ensembles[0]['path_ensemble'].add_path_data(path, 'ACC')
            accept, _, status = retis_swap(ensembles, idx=0,
                                           settings=settings, cycle=0)
        self.assertFalse(accept)
        self.assertEqual(status, 'BTS')

    def test_retis_moves(self):
        """Test the retis moves function."""
        settings, ensembles = create_ensembles_and_paths()
        rgen = MockRandomGenerator(seed=0)
        settings['retis']['swapsimul'] = False
        settings['retis']['nullmoves'] = True
        path1 = ensembles[3]['path_ensemble'].last_path
        path2 = ensembles[4]['path_ensemble'].last_path
        results = retis_moves(ensembles, rgen, settings, cycle=1)
        # We should have done swapping for [2^+] and [3^+] and nullmoves
        # for the rest:
        for resi in results:
            idx = resi['ensemble_number']
            if idx not in (3, 4):
                self.assertEqual(resi['mc-move'], 'nullmove')
            else:
                self.assertEqual(resi['mc-move'], 'swap')
                if idx == 3:
                    self.assertEqual(resi['swap-with'], 4)
                    self.assertTrue(path2 is resi['trial'])
                elif idx == 4:
                    self.assertEqual(resi['swap-with'], 3)
                    self.assertTrue(path1 is resi['trial'])
            self.assertEqual(resi['status'], 'ACC')
            self.assertTrue(resi['accept'])

    def test_repptis_moves(self):
        """Test the repptis moves function, NO swapsimul.
        We have 6 ensembles, with the following acceptable paths:
            [0^-]---RMR
            [0^+-']-LML
            [1^+-]--LMR
            [2^+-]--LML
            [3^+-]--RMR
            [4^+-]--LML
        Ensembles 2^+- and 3^+- are swapped, the others do nullmoves
        """
        settings, ensembles = create_ensembles_and_paths(task='repptis')
        rgen = MockRandomGenerator(seed=0)
        settings['retis']['swapsimul'] = False
        settings['retis']['nullmoves'] = True
        results = retis_moves(ensembles, rgen, settings, cycle=1)
        # for the rest:
        statuses = ['SWD', 'SWD', 'ACC', 'ACC', 'ACC', 'ACC']
        mc_moves = ['swap', 'swap', 'nullmove', 'nullmove', 'nullmove',
                    'nullmove']
        ens_names = ['[2^+]', '[3^+]', '[0^-]', '[0^+]', '[1^+]', '[4^+]']
        for i, resi in enumerate(results):
            idx = resi['ensemble_number']
            if idx == 3:
                self.assertEqual(resi['swap-with'], 4)
            elif idx == 4:
                self.assertEqual(resi['swap-with'], 3)
            self.assertTrue(resi['mc-move'] in ['nullmove', 'swap'])
            self.assertEqual(ensembles[idx]['path_ensemble'].ensemble_name,
                             ens_names[i])
            self.assertEqual((idx, resi['status']), (idx, statuses[i]))
            self.assertEqual(resi['mc-move'], mc_moves[i])

    def test_repptis_moves_simul(self):
        """Test the repptis moves function.
        We have 6 ensembles, with the following acceptable paths:
            [0^-]---RMR
            [0^+-']-LML
            [1^+-]--LMR
            [2^+-]--LML
            [3^+-]--RMR
            [4^+-]--LML
        """
        settings, ensembles = create_ensembles_and_paths(task='repptis')
        rgen = MockRandomGenerator(seed=0)
        settings['retis']['swapsimul'] = True
        settings['retis']['nullmoves'] = True
        results = retis_moves(ensembles, rgen, settings, cycle=1)
        # for the rest:
        statuses = ['SWD', 'SWD', 'SWD', 'SWD', 'ACC', 'ACC']
        mc_moves = ['swap', 'swap', 'swap', 'swap', 'nullmove', 'nullmove']
        ens_names = ['[0^+]', '[1^+]', '[2^+]', '[3^+]', '[4^+]', '[0^-]']
        for i, resi in enumerate(results):
            idx = resi['ensemble_number']
            if idx == 3:
                self.assertEqual(resi['swap-with'], 4)
            elif idx == 4:
                self.assertEqual(resi['swap-with'], 3)
            self.assertTrue(resi['mc-move'] in ['nullmove', 'swap'])
            self.assertEqual(ensembles[idx]['path_ensemble'].ensemble_name,
                             ens_names[i])
            self.assertEqual((idx, resi['status']), (idx, statuses[i]))
            self.assertEqual(resi['mc-move'], mc_moves[i])

    def test_retis_moves_simul(self):
        """Test the retis moves function with swaps."""
        settings, ensembles = create_ensembles_and_paths()
        rgen = MockRandomGenerator(seed=0)
        settings['retis']['swapsimul'] = True
        settings['retis']['nullmoves'] = True
        results = retis_moves(ensembles, rgen, settings, cycle=1)
        # We expect a nullmove for the first and swapping for the rest:
        moves = ('nullmove', 'swap', 'swap', 'swap', 'swap')
        for resi in results:
            self.assertEqual(resi['mc-move'],
                             moves[resi['ensemble_number']])
        # Try with an even number of ensembles. This should trigger
        # the ``if len(ensembles) % 2`` for a particular scheme, we
        # enforce this scheme by resetting the seed:
        ensembles = ensembles[:-1]
        ensembles[0]['path_ensemble'].last_path.set_move('ld')
        rgen = MockRandomGenerator(seed=0)
        results = retis_moves(ensembles, rgen, settings, cycle=1)
        moves = ('nullmove', 'swap', 'swap', 'nullmove')
        for resi in results:
            self.assertEqual(resi['mc-move'],
                             moves[resi['ensemble_number']])
        self.assertEqual(ensembles[0]['path_ensemble'].last_path.get_move(),
                         'ld')
        # Finally, try with just 2 ensembles:
        ensembles = ensembles[0:2]
        results = retis_moves(ensembles, rgen, settings, cycle=1)
        for resi in results:
            self.assertEqual(resi['mc-move'], 'swap')

    def test_relative_shoots(self):
        """Test the relative shoots selection."""
        _, ensembles = create_ensembles_and_paths()
        rgen = MockRandomGenerator(seed=0)
        relative = [0.1, 0.1, 0.1, 0.1, 0.6]
        idx, ensemble = relative_shoots_select(ensembles, rgen, relative)
        self.assertEqual(idx, 4)
        self.assertEqual(ensemble, ensembles[idx])
        relative = [1.0, 0.0, 0.0, 0.0, 0.0]
        idx, ensemble = relative_shoots_select(ensembles, rgen, relative)
        self.assertEqual(idx, 0)
        self.assertEqual(ensemble, ensembles[idx])
        relative = [0.0, 0.0, 0.0, 0.0, 0.0]
        with self.assertRaises(ValueError):
            relative_shoots_select(ensembles, rgen, relative)

    def test_make_retis_step(self):
        """Test that we can do the RETIS steps."""
        settings, ensembles = create_ensembles_and_paths()
        rgen = MockRandomGenerator(seed=0)
        for setting in settings['ensemble']:
            setting['tis']['freq'] = 1.0
        # Check that we can do RETIS:
        settings['retis']['swapfreq'] = 1.0
        settings['retis']['swapsimul'] = True
        settings['retis']['nullmoves'] = True
        ensembles[1]['path_ensemble'].last_path.set_move('ld')
        results = make_retis_step(ensembles, rgen, settings, cycle=1)
        self.assertTrue(ensembles[1]['path_ensemble'].last_path.get_move() ==
                        'ld')
        moves = ('swap', 'swap', 'swap', 'swap', 'nullmove')
        for resi in results:
            self.assertEqual(resi['mc-move'],
                             moves[resi['ensemble_number']])
        # Check that we can select TIS moves:
        settings['retis']['swapfreq'] = 0.0
        results = make_retis_step(ensembles, rgen, settings, cycle=1)

        moves = ('tr', 'ld', 'tr', 'tr', 'tr')
        for resi in results:
            self.assertEqual(
                resi['mc-move'], moves[resi['ensemble_number']])

        # Check that we can do relative shoots:
        settings['retis']['relative_shoots'] = [0.1, 0.1, 0.1, 0.1, 0.6]

        with tempfile.TemporaryDirectory() as tempdir:
            settings['engine']['exe_path'] = tempdir
            settings['simulation']['exe_path'] = tempdir
            for ens in settings['ensemble']:
                ens['engine']['exe_path'] = tempdir
                ens['simulation']['exe_path'] = tempdir
            for fd in {'000', '001', '002', '003', '004'}:
                make_dirs(os.path.join(tempdir, fd))
            results2 = make_retis_step(ensembles, rgen, settings, cycle=0)
            moves = ('nullmove', 'nullmove', 'nullmove', 'nullmove', 'tr')
            for resi in results2:
                self.assertEqual(
                    resi['mc-move'], moves[resi['ensemble_number']])

        # Check that we can do priority shooting:
        settings['retis']['relative_shoots'] = None
        settings['simulation']['priority_shooting'] = True
        results2 = make_retis_step(ensembles, rgen, settings, cycle=2)
        ensembles[1]['path_ensemble'].nstats['npath'] = 1
        moves = (None, 'ld', None, None, None)
        for i, resi in enumerate(results2):
            if i != 1:
                self.assertEqual(resi, moves[i])
            else:
                self.assertEqual(resi['mc-move'],
                                 moves[resi['ensemble_number']])

    def test_make_repptis_step(self):
        """Test that we can do REPPTIS steps."""
        settings, ensembles = create_ensembles_and_paths(task='repptis')
        rgen = MockRandomGenerator(seed=1)
        for setting in settings['ensemble']:
            setting['tis']['freq'] = 1.0
        # Check that we can do REPPTIS:
        settings['retis']['swapfreq'] = 1.0
        settings['retis']['swapsimul'] = True
        settings['retis']['nullmoves'] = True
        ensembles[1]['path_ensemble'].last_path.set_move('ld')
        results = make_retis_step(ensembles, rgen, settings, cycle=1)
        self.assertTrue(ensembles[1]['path_ensemble'].last_path.get_move() ==
                        'ld')
        moves = ('nullmove', 'swap', 'swap', 'swap', 'swap', 'nullmove')
        for resi in results:
            self.assertEqual(resi['mc-move'],
                             moves[resi['ensemble_number']])

        # Check that we can select TIS moves:
        settings['retis']['swapfreq'] = 0.0
        results = make_retis_step(ensembles, rgen, settings, cycle=1)

        moves = ('tr', 'ld', 'tr', 'tr', 'tr', 'tr')
        for resi in results:
            self.assertEqual(
                resi['mc-move'], moves[resi['ensemble_number']])

        # Check that we can do relative shoots:
        settings['retis']['relative_shoots'] = [0.1, 0.1, 0.1, 0.1, 0.6, 0.0]

        with tempfile.TemporaryDirectory() as tempdir:
            settings['engine']['exe_path'] = tempdir
            settings['simulation']['exe_path'] = tempdir
            for ens in settings['ensemble']:
                ens['engine']['exe_path'] = tempdir
                ens['simulation']['exe_path'] = tempdir
            for fd in {'000', '001', '002', '003', '004', '005'}:
                make_dirs(os.path.join(tempdir, fd))
            results2 = make_retis_step(ensembles, rgen, settings, cycle=0)
            moves = ('nullmove', 'nullmove', 'nullmove', 'nullmove', 'tr',
                     'nullmove')
            for resi in results2:
                self.assertEqual(
                    resi['mc-move'], moves[resi['ensemble_number']])

        # Check that we can do priority shooting:
        settings['retis']['relative_shoots'] = None
        settings['simulation']['priority_shooting'] = True
        results2 = make_retis_step(ensembles, rgen, settings, cycle=2)
        ensembles[1]['path_ensemble'].nstats['npath'] = 1
        moves = (None, 'ld', None, None, None, None)
        for i, resi in enumerate(results2):
            if i != 1:
                self.assertEqual(resi, moves[i])
            else:
                self.assertEqual(resi['mc-move'],
                                 moves[resi['ensemble_number']])

    def test_partial_exit_retis(self):
        """Test that we can quit from the RETIS steps."""
        sim, settings = prepare_test_simulation()
        with tempfile.TemporaryDirectory() as tempdir:
            # Run a healthy simulation
            sim.settings['simulation']['exe_path'] = tempdir
            sim.settings['ensemble'][0]['simulation']['exe_path'] = tempdir
            with patch('sys.stdout', new=StringIO()):
                for _ in initiate_path_simulation(sim, settings):
                    logging.debug('Running initialisation')
            make_dirs(os.path.join(tempdir, '002'))
            for _ in sim.run():
                pass
            self.assertEqual(
                sim.ensembles[0]['path_ensemble'].paths[-1:][0]['cycle'], 10)

        del sim
        sim, settings = prepare_test_simulation()
        with tempfile.TemporaryDirectory() as tempdir:
            sim.settings['simulation']['exe_path'] = tempdir
            sim.settings['ensemble'][0]['simulation']['exe_path'] = tempdir
            with patch('sys.stdout', new=StringIO()):
                for _ in initiate_path_simulation(sim, settings):
                    logging.debug('Running initialisation')
            make_dirs(os.path.join(tempdir, '002'))

            self.assertEqual(
                sim.ensembles[0]['path_ensemble'].paths[-1:][0]['cycle'], 0)
            sim.step()
            self.assertEqual(
                sim.ensembles[0]['path_ensemble'].paths[-1:][0]['cycle'], 1)

            # Insert Covid19 and check its presence
            os.mknod(os.path.join(tempdir, "EXIT"))
            with patch('sys.stdout', new=StringIO()):
                self.assertTrue(soft_partial_exit(tempdir))

            # Run a zombie simulation
            with patch('sys.stdout', new=StringIO()):
                for _ in sim.run():
                    logging.info('Try to walk')
            self.assertEqual(
                sim.ensembles[0]['path_ensemble'].paths[-1:][0]['cycle'], 2)


if __name__ == '__main__':
    unittest.main()
