import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
import math
class TestRXGate:
    def test_rx_gate(self):
        nIndexBits = 1
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |0> state
        simulator.init_zero_state()

        target = 0
        angle = np.pi/2
        simulator.rotate_x(target, angle)

        amps_list = []
        for i in range(simulator.total_num_amps):
            amps_list.append(simulator.real[i] + 1j * simulator.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        expected = np.asarray([
            1/math.sqrt(2) + 0.0j, 0.0 - 1j * (1/math.sqrt(2))
        ], dtype=np.complex64)

        # check result

        if not cp.allclose(expected, d_sv):
            raise ValueError("results mismatch")

