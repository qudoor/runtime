import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
import math

class TestCRGate:
    def test_cr_gate(self):
        nIndexBits = 2
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |00> state
        simulator.init_zero_state()

        control = 0
        target = 1
        angle = np.pi/2
        ureal = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, math.cos(angle)]]
        )
        uimag = np.array(
            [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, math.sin(angle)]]
        )

        simulator.cr(control, target, ureal, uimag)

        amps_list = []
        for i in range(simulator.total_num_amps):
            amps_list.append(simulator.real[i] + 1j * simulator.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        expected = np.asarray([
            1.0 + 0.0j, 0.0 + 0.0j,
            0.0 + 0.0j, 0.0 + 0.0j
        ], dtype=np.complex64)

        # check result

        if not cp.allclose(expected, d_sv):
            raise ValueError("results mismatch")

