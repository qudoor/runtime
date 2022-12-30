import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
import math
class TestZ1Gate:
    def test_z1_gate(self):
        nIndexBits = 1
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |0> state
        simulator.init_zero_state()

        rotation = np.pi / 4.0
        ureal = np.array([[math.cos(-rotation), 0], [0, math.cos(rotation)]])
        uimag = np.array([[math.sin(-rotation), 0], [0, math.sin(rotation)]])

        target = 0
        simulator.z1(target, ureal, uimag)

        amps_list = []
        for i in range(simulator.total_num_amps):
            amps_list.append(simulator.real[i] + 1j * simulator.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        expected = np.asarray([
            1/math.sqrt(2) - 1j * 1/math.sqrt(2), 0.0 + 0.0j
        ], dtype=np.complex64)

        # check result

        if not cp.allclose(expected, d_sv):
            raise ValueError("results mismatch")

