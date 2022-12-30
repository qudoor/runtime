import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
import math
class TestX1Gate:
    def test_x1_gate(self):
        nIndexBits = 1
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |0> state
        simulator.init_zero_state()


        factor = 1 / math.sqrt(2)
        ureal = np.array([[1 * factor, 0], [0, 1 * factor]])
        uimag = np.array([[0, -1 * factor], [-1 * factor, 0]])

        target = 0
        simulator.x1(target, ureal, uimag)

        amps_list = []
        for i in range(simulator.total_num_amps):
            amps_list.append(simulator.real[i] + 1j * simulator.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        expected = np.asarray([
            1/math.sqrt(2)+ 0.0j, 0.0 - 1j * 1/math.sqrt(2)
        ], dtype=np.complex64)

        # check result

        if not cp.allclose(expected, d_sv):
            raise ValueError("results mismatch")

