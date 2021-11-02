import numpy as np

from pyretis.analysis import block_error


class TestAnalysis(object):
    def test_block_error_weights(self):
        data = np.random.random(100)
        weights = np.ones(data.shape)*(np.random.random() + 0.001)  # catch 0.0
        r1 = block_error(data)
        r2 = block_error(data, weights=weights)
        for i, j in zip(r1, r2):
            assert np.allclose(i, j)

    def test_block_error_zero_weights(self):
        # This has to be even to not alter the the number of blocks
        data = np.random.random(100)
        weights = np.ones(data.shape)

        # add a giant data point that should not matter
        data2 = np.array([i for i in data]+[1e10])
        weights2 = np.array([i for i in weights]+[0])
        r1 = block_error(data, weights=weights)
        r2 = block_error(data2, weights=weights2)
        for i, j in zip(r1, r2):
            assert np.allclose(i, j)

    def test_block_error_zero_weights_start(self):
        data = np.random.random(100)
        weights = np.ones(data.shape)
        weights[0] = 0  # this would lead to nan's
        r1 = block_error(data, weights=weights)
        assert not np.isnan(r1[1][0])
