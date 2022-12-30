import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
import math
class TestTDGGate:
    def test_tdg_gate(self):
        nIndexBits = 1
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |0> state
        simulator.init_zero_state()

        ureal = np.array([[1, 0], [0, 1 / math.sqrt(2)]])
        uimag = np.array([[0, 0], [0, -1 / math.sqrt(2)]])

        target = 0
        simulator.tdg(target, ureal, uimag)

        amps_list = []
        for i in range(simulator.total_num_amps):
            amps_list.append(simulator.real[i] + 1j * simulator.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        expected = np.asarray([
            1.0 + 0.0j, 0.0 + 0.0j
        ], dtype=np.complex64)

        # check result

        if not cp.allclose(expected, d_sv):
            raise ValueError("results mismatch")

