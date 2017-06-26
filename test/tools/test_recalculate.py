# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Test the tools in pyretis.tools."""
import logging
import os
import tarfile
from tempfile import NamedTemporaryFile
import unittest
import numpy as np
from pyretis.tools.recalculate_order import recalculate_order
from pyretis.orderparameter import OrderParameter
logging.disable(logging.CRITICAL)


CORRECT_TRI = [
    [1.2000000476837158, 1.100000023841858, 0.9526299834251404,
     0.0, 0.0, 0.0, 0.0, 0.550000011920929, 0.0],
    [1.3190346956253052, 1.1973484754562378, 1.0101481676101685,
     0.0, 0.0, 0.0, 0.0, 0.6045578122138977, 0.0],
    [1.445665717124939, 1.2725739479064941, 1.043269157409668,
     0.0, 0.0, 0.0, 0.0, 0.6625972390174866, 0.0],
    [1.549871802330017, 1.3433609008789062, 1.0741169452667236,
     0.0, 0.0, 0.0, 0.0, 0.7103575468063354, 0.0],
    [1.6492804288864136, 1.3989951610565186, 1.0993438959121704,
     0.0, 0.0, 0.0, 0.0, 0.7559200525283813, 0.0],
    [1.7235912084579468, 1.4501303434371948, 1.1253700256347656,
     0.0, 0.0, 0.0, 0.0, 0.7899801731109619, 0.0],
    [1.8234614133834839, 1.5086286067962646, 1.1493875980377197,
     0.0, 0.0, 0.0, 0.0, 0.8357531428337097, 0.0],
    [1.9387280941009521, 1.5735180377960205, 1.1708111763000488,
     0.0, 0.0, 0.0, 0.0, 0.888584315776825, 0.0],
    [2.0414657592773438, 1.6291977167129517, 1.1705245971679688,
     0.0, 0.0, 0.0, 0.0, 0.9356740117073059, 0.0],
    [2.138443946838379, 1.6822302341461182, 1.191916584968567,
     0.0, 0.0, 0.0, 0.0, 0.9801228642463684, 0.0],
    [2.234323024749756, 1.7414289712905884, 1.219726800918579,
     0.0, 0.0, 0.0, 0.0, 1.0240683555603027, 0.0],
]


class OrderBox(OrderParameter):
    """This order parameter is just the box."""

    def __init__(self):
        super().__init__(description='Box order parameter')

    def calculate(self, system):
        return system.box.cell


class RecalculateOrder(unittest.TestCase):
    """Test the calculation of order parameters from trajectory files."""

    def test_rectangular_box(self):
        """Test that we can generate all lattices."""
        orderf = OrderBox()
        box = np.array([2.7200000286102295]*3)
        here = os.path.abspath(os.path.dirname(__file__))
        trr = os.path.join(here, '4water.trr')
        for i in recalculate_order(orderf, trr):
            self.assertTrue(np.allclose(i, box))

    def test_tri_box(self):
        """Test that we can generate all lattices."""
        orderf = OrderBox()
        here = os.path.abspath(os.path.dirname(__file__))
        trr = os.path.join(here, '4water_tri_dyn.trr')
        for i, j in enumerate(recalculate_order(orderf, trr)):
            self.assertTrue(np.allclose(j, CORRECT_TRI[i]))

    def test_recalculate_gro(self):
        """Recalculate from .gro file"""
        orderf = OrderBox()
        here = os.path.abspath(os.path.dirname(__file__))
        tarf = os.path.join(here, '4water_tri_dyn.gro.tgz')
        tar = tarfile.open(tarf, 'r:gz')
        members = sorted([i.name for i in tar.getmembers()])
        i = 0
        for member in members:
            gro = tar.extractfile(member)
            if gro is not None:
                grofile = NamedTemporaryFile(suffix='.gro')
                path = grofile.name
                with open(path, 'wb') as output:
                    output.write(gro.read())
                box = recalculate_order(orderf, path)
                for a, b in zip(box[0], CORRECT_TRI[i]):
                    self.assertAlmostEqual(a, b, places=5)
                i += 1

    def test_recalculate_g96(self):
        """Recalculate from .g96."""
        orderf = OrderBox()
        here = os.path.abspath(os.path.dirname(__file__))
        tarf = os.path.join(here, '4water_tri_dyn.g96.tgz')
        tar = tarfile.open(tarf, 'r:gz')
        members = sorted([i.name for i in tar.getmembers()])
        i = 0
        for member in members:
            g96 = tar.extractfile(member)
            if g96 is not None:
                g96file = NamedTemporaryFile(suffix='.g96')
                path = g96file.name
                with open(path, 'wb') as output:
                    output.write(g96.read())
                box = recalculate_order(orderf, path)
                for a, b in zip(box[0], CORRECT_TRI[i]):
                    self.assertAlmostEqual(a, b, places=5)
                i += 1


if __name__ == '__main__':
    unittest.main()
