import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
import math
class TestU3Gate:
    def test_u3_gate(self):
        nIndexBits = 1
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |0> state
        simulator.init_zero_state()

        theta = np.pi
        phi = 0
        lam = np.pi

        ureal = np.array(
            [
                [math.cos(theta / 2), -1 * math.cos(lam) * math.sin(theta / 2)],
                [
                    math.cos(phi) * math.sin(theta / 2),
                    math.cos(phi + lam) * math.cos(theta / 2),
                ],
            ]
        )
        uimag = np.array(
            [
                [0, -1 * math.sin(lam) * math.sin(theta / 2)],
                [
                    math.sin(phi) * math.sin(theta / 2),
                    math.sin(phi + lam) * math.cos(theta / 2),
                ],
            ]
        )

        target = 0
        simulator.u3(target, ureal, uimag)

        amps_list = []
        for i in range(simulator.total_num_amps):
            amps_list.append(simulator.real[i] + 1j * simulator.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        expected = np.asarray([
            0.0+ 0.0j, 1.0 + 0.0j
        ], dtype=np.complex64)

        # check result

        if not cp.allclose(expected, d_sv):
            raise ValueError("results mismatch")

