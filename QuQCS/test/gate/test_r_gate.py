import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
import math
class TestRGate:
    def test_r_gate(self):
        nIndexBits = 1
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |0> state
        simulator.init_zero_state()

        target = 0
        theta = phi = np.pi/2

        ureal = np.array(
            [
                [math.cos(theta / 2), math.sin(-phi) * math.sin(theta / 2)],
                [math.sin(phi) * math.sin(theta / 2), math.cos(theta / 2)],
            ]
        )

        # imaginary part of complex number
        uimag = np.array(
            [
                [0, -1 * math.cos(-phi) * math.sin(theta / 2)],
                [-1 * math.cos(phi) * math.sin(theta / 2), 0],
            ]
        )

        simulator.rotate(target, ureal, uimag)

        amps_list = []
        for i in range(simulator.total_num_amps):
            amps_list.append(simulator.real[i] + 1j * simulator.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        expected = np.asarray([
            1/math.sqrt(2) + 0.0j, 1/math.sqrt(2) + 0.0j,
        ], dtype=np.complex64)

        # check result

        if not cp.allclose(expected, d_sv):
            raise ValueError("results mismatch")

