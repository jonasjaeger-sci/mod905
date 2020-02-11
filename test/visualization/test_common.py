# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the common methods in pyretis.visualization.common."""
from io import StringIO
import colorama
from unittest.mock import patch
import os
import logging
import unittest
import numpy as np
from pyretis.visualization.common import (
    get_min_max,
    get_startat,
    diff_matching,
    try_data_shift,
    hello_pyvisa
)
logging.disable(logging.CRITICAL)

HERE = os.path.abspath(os.path.dirname(__file__))
color = colorama.Fore.CYAN


def del_list_ind(l, d):
    """Function deleting indeces in list"""
    for i in reversed(d):
        del l[i]


class TestMethods(unittest.TestCase):
    """Test some of the methods from pyretis.visualization.common."""
    def test_hello_pyvisa(self):
        """Test of the hello-message of pathdensity module"""
        hello_pyvisa(noprint=True)
        # Does nothing but print, always ok!

    def test_hello_pyvisa_print(self):
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            hello_pyvisa(noprint=False)
            color = colorama.Fore.CYAN
            msgtxt = color+'Starting\n'
            msgtxt += color
            msgtxt += r"+------------------------------------------+"+"\n"
            msgtxt += color
            msgtxt += r"|   _______                                |"+"\n"
            msgtxt += color
            msgtxt += r"|  /   ___ \        _    ___         ___   |"+"\n"
            msgtxt += color
            msgtxt += r"| /_/\ \_/ /_  __  | |  / (_)____   /   |  |"+"\n"
            msgtxt += color
            msgtxt += r"|    /  __  / / /  | | / / / ___/  / /| |  |"+"\n"
            msgtxt += color
            msgtxt += r"|   / /   \ \/ /   | |/ / (__  )  / ___ |  |"+"\n"
            msgtxt += color
            msgtxt += r"|  /_/    _\  /    |___/_/____/  /_/  |_|  |"+"\n"
            msgtxt += color
            msgtxt += r"|        /___/                             |"+"\n"
            msgtxt += color
            msgtxt += r"|     ,       ,       ,       ,       ,    |"+"\n"
            msgtxt += color
            msgtxt += r"|   .'|     .'|     .'|     .'|     .'|    |"+"\n"
            msgtxt += color
            msgtxt += r"|   |*****  | :     | :     | :     | :    |"+"\n"
            msgtxt += color
            msgtxt += r"|   : '   **: '     : '     : '     : '    |"+"\n"
            msgtxt += color
            msgtxt += r"|   | |     |**  ***|****   | |     | |    |"+"\n"
            msgtxt += color
            msgtxt += r"|   ' :     ' :**   ' :  ***'*:     ' :    |"+"\n"
            msgtxt += color
            msgtxt += r"|   ; |     ; |     ; |     ; ***** ; |    |"+"\n"
            msgtxt += color
            msgtxt += r"|   | :     | :     | :     | :    *| :    |"+"\n"
            msgtxt += color
            msgtxt += r"|   : '     :*******: '     : ' *** : '    |"+"\n"
            msgtxt += color
            msgtxt += r"|   | |  ***| |     |*******|***    | |    |"+"\n"
            msgtxt += color
            msgtxt += r"|   :****   : ;     : ;     : ;     : ;    |"+"\n"
            msgtxt += color
            msgtxt += r"|   ,/      ,/      ,/      ,/      ,/     |"+"\n"
            msgtxt += color
            msgtxt += r"|   '       '       '       '       '      |"+"\n"
            msgtxt += color
            msgtxt += r"+------------------------------------------+"+"\n"
            msgtxt += color

            self.assertEqual(fakeOutput.getvalue().strip(), str(msgtxt))

    def test_get_min_max(self):
        """Test for getting correct indeces of min/max cycle from data."""
        my_mini = {'a': 0, 'r': 0}
        my_maxi = {'a': 0, 'r': 0}

        mydata = [j for j in range(10) for i in range(3)]
        get_min_max(mydata, [0, 9], my_mini, my_maxi, 'a')
        self.assertEqual(0, my_mini['a'])
        self.assertEqual(29, my_maxi['a'])

        mydata = [j for j in range(10) for i in range(3)]
        get_min_max(mydata, [3, 8], my_mini, my_maxi, 'r')
        self.assertEqual(9, my_mini['r'])
        self.assertEqual(26, my_maxi['r'])

        mydata = [j for j in range(3, 10) for i in range(3)]
        get_min_max(mydata, [0, 2], my_mini, my_maxi, 'r')
        self.assertEqual(my_mini['r'], my_maxi['r'])

    def test_get_startat(self):
        """Test that we can find latest start of a output file."""
        test_file = os.path.join(HERE, 'test_simulation_dir/000/energy.txt')
        self.assertEqual(get_startat(test_file, noprint=True), 1)
        test_file = os.path.join(HERE, 'test_simulation_dir/000/order.txt')
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertEqual(get_startat(test_file, noprint=False), 4)
            msgtxt = "- Found last restart of {} at line 3".format(test_file)
            self.assertEqual(fakeOutput.getvalue().strip(), str(msgtxt))

    def test_diff_matching(self):
        """Test that we can find the indeces where two similar lists
        do not match eachother"""
        # Case 0, No match:
        list1 = [i for i in range(0, 10)]
        list2 = [i for i in range(20, 30)]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))
        list1 = [i for i in range(20, 30)]
        list2 = [i for i in range(0, 10)]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))

        # Case 1, equal lists:
        list1 = [i for i in range(100)]
        list2 = [i for i in range(100)]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))

        # Case 2, varying lists:
        list1 = [i for i in range(205)]
        list2 = [i for i in range(200)]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))

        list1 = [i for i in range(100, 205) if i != 131 and i != 161]
        list2 = [i for i in range(200)]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))
        list1 = [i for i in range(100, 200) if i != 131 and i != 161]
        list2 = [i for i in range(205)]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))

        list1 = [i for i in range(200)]
        list2 = [i for i in range(100, 205) if i != 131 and i != 161]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))
        list1 = [i for i in range(205)]
        list2 = [i for i in range(100, 200) if i != 131 and i != 161]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))
        list1 = list(range(10))
        list2 = [i*2 for i in range(10)]
        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))
        list1 = [i*2 for i in range(10)]
        list2 = list(range(10))

        d1, d2 = diff_matching(list1, list2, [len(list1), len(list2)])
        self.assertEqual(del_list_ind(list1, d1),
                         del_list_ind(list2, d2))

        # Test empty lists
        list1 = list(range(10))
        d1, d2 = diff_matching(list1, [], (len(list1), 0))
        self.assertEqual(d1, list1)
        self.assertEqual(d2, [])

        d1, d2 = diff_matching([], list1, (0, len(list1)))
        self.assertEqual(d1, [])
        self.assertEqual(d2, list1)

    def test_try_data_shift(self):
        """Test to try_data_shift and shift_data functions"""
        n = 100  # number of data points
        # The Correct data, normal distr around origo
        # with a slope m=-1/3
        x, y = [], []
        np.random.seed(n)
        for i in range(n):
            r1 = np.random.normal()
            r2 = 3*np.random.normal()
            x.append(r1-r2)
            y.append(r1+r2)
        # The shifted data, to be corrected
        avx, avy = np.average(x), np.average(y)
        sx, sy = [], []
        for i in range(n):
            if x[i] > avx:
                sx.append(-90+x[i])
            else:
                sx.append(x[i])
            if y[i] > avy:
                sy.append(-90+y[i])
            else:
                sy.append(y[i])
        # Evaluate correct data, should do nothing:
        nx, ny = try_data_shift(x, y, 'opX')
        self.assertEqual(x, nx)
        self.assertEqual(y, ny)
        # Evaluate x-shifted data:
        nx, ny = try_data_shift(sx, y, 'opX')
        self.assertEqual(ny, y)
        self.assertFalse(np.average(sx) == np.average(nx))
        # Evaluate y-shifted data:
        nx, ny = try_data_shift(x, sy, 'opX')
        self.assertEqual(x, nx)
        self.assertFalse(np.average(sy) == np.average(ny))
        # Evaluate x&y-shifted data:
        nx, ny = try_data_shift(sx, sy, 'opX')
        self.assertFalse(np.average(sx) == np.average(nx))
        self.assertFalse(np.average(sy) == np.average(ny))
        # Evaluate x&y-shifted data, but with op1 flag to hold:
        nx, ny = try_data_shift(sx, sy, 'op1')
        self.assertEqual(sx, nx)
        self.assertFalse(np.average(sy) == np.average(ny))


if __name__ == '__main__':
    unittest.main()
