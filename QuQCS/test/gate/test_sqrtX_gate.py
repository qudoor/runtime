import numpy as np
from runtime.QuQCS.qucuQuantum.cuQuantumSim import cuQuantumSimulator
import cupy as cp
class TestSqrtXGate:
    def test_sqrtx_gate(self):
        nIndexBits = 1
        simulator = cuQuantumSimulator()
        simulator.create_qureg(nIndexBits)
        # initialize to |0> state
        simulator.init_zero_state()

        ureal = np.array([[0.5, 0.5], [0.5, 0.5]])
        uimag = np.array([[0.5, -0.5], [-0.5, 0.5]])

        target = 0
        simulator.sqrtx(target, ureal, uimag)

        amps_list = []
        for i in range(simulator.total_num_amps):
            amps_list.append(simulator.real[i] + 1j * simulator.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        expected = np.asarray([
            0.5 + 0.50j, 0.5 - 0.5j
        ], dtype=np.complex64)

        # check result

        if not cp.allclose(expected, d_sv):
            raise ValueError("results mismatch")

