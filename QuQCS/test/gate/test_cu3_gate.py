import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
import math
class TestCU3Gate:
    def test_cu3_gate(self):
        nIndexBits = 2
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |00> state
        simulator.init_zero_state()

        theta = lam = phi = np.pi/2

        ureal = np.array(
            [
                [1, 0, 0, 0],
                [0, math.cos(theta / 2), 0, -math.cos(lam) * math.sin(theta / 2)],
                [0, 0, 1, 0],
                [
                    0,
                    math.cos(phi) * math.sin(theta / 2),
                    0,
                    math.cos(phi + lam) * math.cos(theta / 2),
                ],
            ]
        )
        uimag = np.array(
            [
                [0, 0, 0, 0],
                [0, 0, 0, -math.sin(lam) * math.sin(theta / 2)],
                [0, 0, 0, 0],
                [
                    0,
                    math.sin(phi) * math.sin(theta / 2),
                    0,
                    math.sin(phi + lam) * math.cos(theta / 2),
                ],
            ]
        )

        control = 0
        target = 1

        simulator.cu3(control, target, ureal, uimag)

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

