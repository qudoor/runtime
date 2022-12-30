import math
import random
from enum import Enum

import numpy as np
import cupy as cp
from cuquantum import custatevec as cusv
from cuquantum import cudaDataType as cudtype
from cuquantum import ComputeType as ctype
import time

REAL_EPS = 1e-13


if cp.cuda.runtime.runtimeGetVersion() < 11020:
    raise RuntimeError("memory_handler example WAIVED : This example uses CUDA's "
                       "built-in stream-ordered memory allocator, which requires "
                       "CUDA 11.2+.")
device = cp.cuda.Device()
if not device.attributes['MemoryPoolsSupported']:
    raise RuntimeError("memory handler example WAIVED: device does not support CUDA Memory pools")


class BitEncoding(Enum):
    """Bit Encoding"""

    UNSIGNED = 0
    TWOS_COMPLEMENT = 1


class PhaseFunc(Enum):
    """PhaseFunc"""

    NORM = 0
    SCALED_NORM = 1
    INVERSE_NORM = 2
    SCALED_INVERSE_NORM = 3
    SCALED_INVERSE_SHIFTED_NORM = 4
    PRODUCT = 5
    SCALED_PRODUCT = 6
    INVERSE_PRODUCT = 7
    SCALED_INVERSE_PRODUCT = 8
    DISTANCE = 9
    SCALED_DISTANCE = 10
    INVERSE_DISTANCE = 11
    SCALED_INVERSE_DISTANCE = 12
    SCALED_INVERSE_SHIFTED_DISTANCE = 13


class PauliOpType(Enum):
    """PauliOpType"""

    PAULI_I = 0
    PAULI_X = 1
    PAULI_Y = 2
    PAULI_Z = 3


class cuQuantumSimulator:
    """Simulator implement"""

    def __init__(self):
        self.real = []  # real
        self.imag = []  # imag
        self.qureg = None
        self.qubits = 0
        self.total_num_amps = 0  # numAmpsPerChunk

        # avoid shrinking the pool
        self.mempool = cp.cuda.runtime.deviceGetDefaultMemPool(device.id)
        if int(cp.__version__.split('.')[0]) >= 10:
            # this API is exposed since CuPy v10
            cp.cuda.runtime.memPoolSetAttribute(
                self.mempool, cp.cuda.runtime.cudaMemPoolAttrReleaseThreshold, 0xffffffffffffffff)  # = UINT64_MAX
        self.handle = cusv.create()
        self.stream = cp.cuda.Stream()
        cusv.set_stream(self.handle, self.stream.ptr)

        self.handler = (self.__malloc, self.__free, "memory_handler python for qucuQuantum sim")
        cusv.set_device_mem_handler(self.handle, self.handler)

        self.adjoint = 0
        self.layout = cusv.MatrixLayout.ROW
        self.svDataType = cudtype.CUDA_C_64F
        self.computeType = ctype.COMPUTE_64F



    def __malloc(size, stream):
        return cp.cuda.runtime.mallocAsync(size, stream)

    def __free(ptr, size, stream):
        cp.cuda.runtime.freeAsync(ptr, stream)

    def create_qureg(self, num_qubits):
        """
        Allocate resource

        Args:
            num_qubits: number of qubits
        """
        self.qubits = num_qubits
        num_amps = 2**num_qubits
        self.total_num_amps = num_amps
        self.real = [0] * num_amps
        self.imag = [0] * num_amps

    def init_blank_state(self):
        """Init blank state"""
        for i in range(self.total_num_amps):
            self.real[i] = 0.0
            self.imag[i] = 0.0

    def init_zero_state(self):
        """Init zero state"""
        self.init_blank_state()
        self.real[0] = 1.0

    def init_plus_state(self):
        """Init plus state"""
        # dimension of the state vector
        chunk_size = self.total_num_amps
        state_vec_size = chunk_size
        normFactor = 1.0 / math.sqrt(state_vec_size)

        # initialise the state to |+++..+++> = 1/normFactor {1, 1, 1, ...}
        for this_task in range(chunk_size):
            self.real[this_task] = normFactor
            self.imag[this_task] = 0.0

    def init_classical_state(self):
        """Init classical state"""

        # initialise the state to vector to all zeros
        self.init_blank_state()

        # give the specified classical state prob 1
        self.real[0] = 1.0
        self.imag[0] = 0.0

    # TODO:need to improve.
    def hadamard(self, target):
        """
        Apply hadamard gate.

        Args:
            target: target qubit.
        """
        targets = (target,)

        hGate = cp.asarray([
            1 / np.sqrt(2) + 1j * 0.0, 1 / np.sqrt(2) + 1j * 0.0,
            1 / np.sqrt(2) + 1j * 0.0, -1 / np.sqrt(2) + 1j * 0.0
            ], dtype=cp.complex128)

        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        # start_time = time.time()
        # apply matrix
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            hGate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType ,
            0, 0)
        #end_time = time.time()
        #print("time clap 1= %.14f" % (end_time - start_time))

        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j+1]

    def ch(self, control_bit, target_bit, ureal, uimage):
        self.controlled_unitary(control_bit, target_bit, ureal, uimage)

    def phase_shift(self, target, angle):
        """Shift the phase between |0> and |1> of a single qubit by a given angle.

        Args:
            target: qubit to undergo a phase shift.
            angle:  amount by which to shift the phase in radians.
        """
        real = angle
        imag = math.sin(angle)
        self.phase_shift_by_term(self.real, self.imag, target, real, imag)

    def controlled_phase_shift(self, ctrl, target, angle):
        """
        Controlled-Phase gate.

        Args:
            ctrl: control qubit
            target: target qubit
            angle: amount by which to shift the phase in radians.
        """
        control_phase_gate = cp.asarray([
            np.exp(angle) + 1j * 0.0, 0.0 + 1j * 0.0,
            0.0 + 1j * 0.0, np.exp(angle) + 1j * 0.0
        ], dtype=cp.complex128)
        targets = (target,)
        controls = (ctrl,)
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            control_phase_gate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), controls, 0, len(controls), self.computeType ,
            0, 0)
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def rotate(self, target, ureal, uimag):
        """Rotate gate."""
        self.apply_matrix2(target, ureal, uimag)

    def rotate_x(self, target, angle):
        """rx gate."""
        rotation_axis = cusv.Pauli.X
        self.rotate_around_axis(target, angle, rotation_axis)

    def rotate_y(self, target, angle):
        """ry gate."""
        '''
        control_phase_gate = cp.asarray([
            math.cos(angle/2) + 1j * 0.0, -math.sin(angle/2) + 1j * 0.0,
            math.sin(angle/2) + 1j * 0.0, math.cos(angle/2) + 1j * 0.0
        ], dtype=cp.complex128)
        targets = (target,)

        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j*self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            control_phase_gate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType ,
            0, 0)
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]
        '''
        rotation_axis = cusv.Pauli.Y
        self.rotate_around_axis(target, angle, rotation_axis)

    def rotate_z(self, target, angle):
        """rz gate."""
        rotation_axis = cusv.Pauli.Z
        self.rotate_around_axis(target, angle, rotation_axis)

    def pauli_x(self, target):
        """The single-qubit Pauli-X gate."""
        xGate = cp.asarray([[0.0, 0.0], [1.0, 0.0],
                            [1.0, 0.0], [0.0, 0.0]], dtype=np.float64)
        self._pauli_gate(target, xGate)

    def pauli_y(self, target):
        """The single-qubit Pauli-Y gate."""
        yGate = cp.asarray([[0.0, 0.0], [0.0, -1.0],
                            [0.0, 1.0], [0.0, 0.0]], dtype=np.float64)
        self._pauli_gate(target, yGate)


    def pauli_z(self, target):
        """The single-qubit Pauli-Z gate."""
        zGate = cp.asarray([[1.0, 0.0], [0.0, 0.0],
                            [0.0, 0.0], [-1.0, 0.0]], dtype=np.float64)
        self._pauli_gate(target, zGate)

    def s_gate(self, target):
        """The single-qubit S gate."""
        state_vec_size = self.total_num_amps
        hTargets = (target,)
        hNTargets = 1
        amps_list = []
        for index in range(state_vec_size):
            amps_list.append(self.real[index] + 1j* self.imag[index])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        s_gate = cp.asarray([
            1 + 1j * 0.0, 0 + 1j * 0.0,
            0 + 1j * 0.0, 0 + 1j * 1.0
        ], dtype=cp.complex128)

        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            s_gate.data.ptr, self.svDataType, self.layout, self.adjoint,
            hTargets, hNTargets, 0, 0, 0, self.computeType ,
            0, 0)

        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def t_gate(self, target):
        """The single-qubit T gate."""
        targets = (target,)
        amps_list = []
        for index in range(self.total_num_amps):
            amps_list.append(self.real[index] + 1j * self.imag[index])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        s_gate = cp.asarray([
            1 + 1j * 0.0, 0 + 1j * 0.0,
            0 + 1j * 0.0, np.exp(np.pi/4) + 1j * 0.0
        ], dtype=cp.complex128)

        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            s_gate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType,
            0, 0)

        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def control_not(self, ctrl, target):
        # CNOT gate
        targets = (target,)
        controls = (ctrl,)
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)
        cnotGate = cp.asarray([[0.0, 0.0], [1.0, 0.0],
                              [1.0, 0.0], [0.0, 0.0]], dtype=np.float64)

        # apply CNOT gate
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            cnotGate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), controls, 0, len(controls), self.computeType ,
            0, 0)

        #copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j+1]

    def sdg(self, target_bit, ureal, uimag):
        self.apply_matrix2(target_bit, ureal, uimag)

    def tdg(self, target_bit, ureal, uimag):
        self.apply_matrix2(target_bit, ureal, uimag)

    def sqrtswap(self, target0, target1, ureal, uimag):
        #self.apply_matrix4(target_bit0, target_bit1, ureal, uimag)
        matrix = ureal + uimag*1j
        gate = cp.asarray(matrix, dtype=cp.complex128)
        targets = (target0, target1)
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            gate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType,
            0, 0)
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]


    def swap(self, target_bit0, target_bit1):
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        nBitSwaps = 1
        bitSwaps = [(target_bit0, target_bit1)]
        
        # swap the state vector elements only if 1st qubit is 1
        maskLen = 0
        maskBitString = []
        maskOrdering = []

        # bit swap
        cusv.swap_index_bits(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            bitSwaps, nBitSwaps,
            maskBitString, maskOrdering, maskLen)

        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def cswap(self, control_bit, target_bit0, targetbi_bit1, ureal, uimage):
        # control-SWAP gate
        self.controlled_two_qubit_unitary(
            control_bit, target_bit0, targetbi_bit1, ureal, uimage
        )

    def cy(self, control_bit, target_bit):
        yGate = cp.asarray([
            0.0 + 1j * 0.0, 0.0 - 1j * 1.0,
            0.0 + 1j * 1.0, 0.0 + 1j * 0.0,
        ], dtype=cp.complex128)
        controls = (control_bit,)
        self._control_pauli_gate(controls, target_bit, yGate)

    def cz(self, control_bits, num_control_bits):
        amps_list = []
        zGate = cp.asarray([[1.0, 0.0], [0.0, 0.0],
                            [0.0, 0.0], [-1.0, 0.0]], dtype=np.float64)

        targets = (control_bits[-1],)
        controls = tuple(control_bits[0:-1])
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)
        # apply Pauli operator
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            zGate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), controls, 0, len(controls), self.computeType,
            0, 0)
        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def u3(self, target_bit, ureal, uimag):
        self._unitary_gate(target_bit, ureal, uimag)

    def u2(self, target_bit, ureal, uimag):
        self._unitary_gate(target_bit, ureal, uimag)

    def u1(self, target_bit, ureal, uimag):
        self._unitary_gate(target_bit, ureal, uimag)
        #self.unitary(target_bit, ureal, uimag)

    def crx(self, control_bit, target_bit, angle):
        rotation_axis = cusv.Pauli.X
        self.controlled_rotate_around_axis(control_bit, target_bit, angle, rotation_axis)

    def cry(self, control_bit, target_bit, angle):
        rotation_axis = cusv.Pauli.Y
        self.controlled_rotate_around_axis(control_bit, target_bit, angle, rotation_axis)

    def crz(self, control_bit, target_bit, angle):
        rotation_axis = cusv.Pauli.Z
        self.controlled_rotate_around_axis(control_bit, target_bit, angle, rotation_axis)

    def controlled_rotate_around_axis(self, control_bit, target_bit, angle, pauli_axis):
        targets = np.asarray([target_bit], dtype=np.int32)
        controls = np.asarray([control_bit], dtype=np.int32)
        controlBitValues = np.asarray([1], dtype=np.int32)
        paulis = np.asarray([pauli_axis], dtype=np.int32)

        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        cusv.apply_pauli_rotation(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            -angle / 2, paulis,
            targets.ctypes.data, len(targets),
            controls.ctypes.data, controlBitValues.ctypes.data, len(controls))

        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def rotate_around_axis(self, target_bit, angle, pauli_axis):
        targets = (target_bit,)
        targets_len = len(targets)

        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)
        paulis = [pauli_axis]
        controls = []
        controls_len = len(controls)
        control_values = 1
        cusv.apply_pauli_rotation(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            -angle / 2, paulis,
            targets, targets_len,
            controls, control_values, controls_len)

        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def x1(self, target, ureal, uimag):
        self.apply_matrix2(target, ureal, uimag)

    def y1(self, target, ureal, uimag):
        self.apply_matrix2(target, ureal, uimag)

    def z1(self, target, ureal, uimag):
        self.apply_matrix2(target, ureal, uimag)

    def sqrtx(self, target, ureal, uimag):
        self.apply_matrix2(target, ureal, uimag)

    def sqrtxdg(self, target, ureal, uimag):
        self.apply_matrix2(target, ureal, uimag)

    def csqrtx(self, control_bit, target_bit, ureal, uimage):
        self.controlled_unitary(control_bit, target_bit, ureal, uimage)

    def cu1(self, target_bit0, target_bit1, ureal, uimag):
        self.apply_matrix4(target_bit0, target_bit1, ureal, uimag)

    def cu3(self, target_bit0, target_bit1, ureal, uimag):
        self.apply_matrix4(target_bit0, target_bit1, ureal, uimag)

    def cu(self, target_bit0, target_bit1, ureal, uimag):
        self.apply_matrix4(target_bit0, target_bit1, ureal, uimag)

    def cr(self, target_bit0, target_bit1, ureal, uimag):
        self.apply_matrix4(target_bit0, target_bit1, ureal, uimag)

    def iswap(self, target_bit0, target_bit1, ureal, uimag):
        self.apply_matrix4(target_bit0, target_bit1, ureal, uimag)

    def get_qubit_bit_mask(self, qubits, numqubit):
        mask = 0
        for index in range(numqubit):
            mask = mask | (1 << qubits[index])

        return mask

    def apply_matrix2(self, target, ureal, uimag):
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)


        gate_matrix = cp.asarray([
                                    ureal[0][0] + 1j * uimag[0][0],  ureal[0][1] + 1j * uimag[0][1],
                                    ureal[1][0] + 1j * uimag[1][0],  ureal[1][1] + 1j * uimag[1][1]
                                ])

        targets = (target,)
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            gate_matrix.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType ,
            0, 0)

        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def apply_matrix4(self, target0, target1, ureal, uimag):
        matrix = ureal + uimag * 1j
        gate = cp.asarray(matrix, dtype=cp.complex128)
        targets = (target0, target1)
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            gate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType,
            0, 0)
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def controlled_unitary(self, control_bit, target_bit, ureal, uimag):
        gate = cp.asarray([
            ureal[0][0] + 1j * uimag[0][0], ureal[0][1] + 1j * uimag[0][1],
            ureal[1][0] + 1j * uimag[1][0], ureal[1][1] + 1j * uimag[1][1]
        ],  dtype=cp.complex128)

        targets = (target_bit,)
        controls = (control_bit,)
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            gate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), controls, 0, len(controls), self.computeType ,
            0, 0)
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]


    def insert_two_zero_bits(self, number, bit1, bit2):
        small = bit1 if bit1 < bit2 else bit2
        big = bit2 if bit1 < bit2 else bit1
        return self.insert_zero_bit(self.insert_zero_bit(number, small), big)

    def insert_zero_bit(self, number, index):
        left = (number >> index) << index
        right = number - left
        return (left << 1) ^ right

    def flip_bit(self, number, bit_ind):
        return number ^ (1 << bit_ind)

    def extract_bit(self, ctrl, index):
        return (index & (2**ctrl)) // (2**ctrl)

    def multi_controlled_multi_qubit_not(
        self, control_bits, num_control_bits, target_bits, num_target_bits
    ):
        targets = tuple(target_bits)
        controls = tuple(control_bits)

        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)
        cnotGate = cp.asarray([[0.0, 0.0], [1.0, 0.0],
                               [1.0, 0.0], [0.0, 0.0]], dtype=np.float64)

        # apply CNOT gate
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            cnotGate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, num_target_bits, controls, 0, num_control_bits, self.computeType,
            0, 0)

        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]


    def controlled_two_qubit_unitary(
        self, control_bit, target_bit0, targetbi_bit1, ureal, uimage
    ):
        # control-SWAP gate
        swapTargets = (target_bit0, targetbi_bit1)
        swapControls = (control_bit,)

        swapGate = np.asarray(
            [ureal[0][0] + 1j * uimage[0][0], ureal[0][1] + 1j * uimage[0][1], ureal[0][2] + 1j * uimage[0][2],
             ureal[0][3] + 1j * uimage[0][3],
             ureal[1][0] + 1j * uimage[1][0], ureal[1][1] + 1j * uimage[1][1], ureal[1][2] + 1j * uimage[1][2],
             ureal[1][3] + 1j * uimage[1][3],
             ureal[2][0] + 1j * uimage[2][0], ureal[2][1] + 1j * uimage[2][1], ureal[2][2] + 1j * uimage[2][2],
             ureal[2][3] + 1j * uimage[2][3],
             ureal[3][0] + 1j * uimage[3][0], ureal[3][1] + 1j * uimage[3][1], ureal[3][2] + 1j * uimage[3][2],
             ureal[3][3] + 1j * uimage[3][3]],
            dtype=np.complex128)

        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        # apply control swap gate
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            swapGate.ctypes.data, self.svDataType, self.layout, self.adjoint,
            swapTargets, len(swapTargets), swapControls, 0, len(swapControls), self.computeType,
            0, 0)

        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def measure(self, target):
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        rand = random.random()
        collapse = cusv.Collapse.NORMALIZE_AND_ZERO

        bitstring = np.empty(self.qubits, dtype=np.int32)
        bit_ordering = list(range(self.qubits))

        cusv.batch_measure(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            bitstring.ctypes.data, bit_ordering, bitstring.size,
            rand, collapse)

        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

        if bitstring.sum() == 0:
            # collapse to |0>
            outcome = 0
        else:
            # collapse to |1>
            outcome = 1

        '''
        # <--qucuQuantum end

        zero_prob = self.calc_prob_of_outcome(target, 0)
        outcome, outcome_prob = self.generate_measure_outcome(zero_prob)
        self.collapse_to_know_prob_outcome(target, outcome, outcome_prob)
        '''
        return outcome


    def generate_measure_outcome(self, zero_prob):
        if zero_prob < REAL_EPS:
            outcome = 1
        elif (1 - zero_prob) < REAL_EPS:
            outcome = 0
        else:
            outcome = 1 if random.random() > zero_prob else 0

        outcome_prob = zero_prob if outcome == 0 else 1 - zero_prob
        return outcome, outcome_prob

    def calc_prob_of_outcome(self, target, outcome):
        outcome_prob = self.find_prob_of_zero(target)
        if outcome == 1:
            outcome_prob = 1.0 - outcome_prob
        return outcome_prob

    def find_prob_of_zero(self, target):
        num_task = self.total_num_amps // 2
        size_half_block = 2**target
        size_block = size_half_block * 2
        total_prob = 0.0

        for this_task in range(num_task):
            this_block = this_task // size_half_block
            index = this_block * size_block + this_task % size_half_block

            total_prob += (
                self.real[index] * self.real[index]
                + self.imag[index] * self.imag[index]
            )

        return total_prob

    def get_prob(self, index):
        """
        Get the probability of a state-vector at an index in the full state vector.

        Args:
            index: index in state vector of probability amplitudes

        Returns:
            the probability of target index
        """
        if index < 0 or index >= self.total_num_amps:
            raise ValueError(f"{index} is illegal parameter.")

        real = self.real[index]
        imag = self.imag[index]
        return real * real + imag * imag

    def get_prob_outcome(self, qubit, outcome):
        """
        Get the probability of a specified qubit being measured in the given outcome (0 or 1)

        Args:
            qubit: the specified qubit to be measured
            outcome: the qubit measure result(0 or 1)

        Returns:
            the probability of target qubit
        """
        outcome_prob = self.find_prob_of_zero(qubit)
        if outcome == 1:
            outcome_prob = 1.0 - outcome_prob
        return outcome_prob

    def get_probs(self, qubits):
        """
        Get outcomeProbs with the probabilities of every outcome of the sub-register contained in qureg

        Args:
            qubits: the sub-register contained in qureg

        Returns:
            An array contains probability of target qubits
        """
        num_outcome_probs = len(qubits)
        outcome_probs = [0] * (2**num_outcome_probs)
        for i in range(self.total_num_amps):
            outcome_ind = 0
            for q in range(num_outcome_probs):
                outcome_ind += self.extract_bit(qubits[q], i) * (2**q)

            real = self.real[i]
            imag = self.imag[i]
            prob = real * real + imag * imag
            outcome_probs[outcome_ind] += prob

        return outcome_probs

    def get_all_state(self):
        """
        Get the current state vector of probability amplitudes for a set of qubits
        """
        # todo better in float or ndarray
        state_list = []
        for i in range(self.total_num_amps):
            real = "%.14f" % self.real[i]
            imag = "%.14f" % self.imag[i]
            state = real + ", " + imag
            state_list.append(state)
        return state_list

    def apply_param_named_phase(
        self,
        qubits,
        num_qubits_per_reg,
        num_regs,
        encoding,
        phase_func_name,
        params,
        override_inds,
        override_phases,
        num_overrides,
        conj,
    ):
        i = 0
        max_num_regs_apply_arbitrary_phase = 100
        phase_inds = [0] * max_num_regs_apply_arbitrary_phase
        for index in range(self.total_num_amps):
            flat_ind = 0
            for r in range(num_regs):
                phase_inds[r] = 0
                if encoding == BitEncoding.UNSIGNED:
                    for q in range(num_qubits_per_reg[r]):
                        phase_inds[r] += (2**q) * self.extract_bit(
                            qubits[flat_ind], index
                        )
                        flat_ind += 1
                elif encoding == BitEncoding.TWOS_COMPLEMENT:
                    for q in range(num_qubits_per_reg[r] - 1):
                        phase_inds[r] += (2**q) * self.extract_bit(
                            qubits[flat_ind], index
                        )
                        flat_ind += 1
                    if self.extract_bit(qubits[flat_ind], index) == 1:
                        phase_inds[r] -= 2 ** (num_qubits_per_reg[r] - 1)
                    flat_ind += 1

            for i in range(num_overrides):
                found = 1
                for r in range(num_regs):
                    if phase_inds[r] != override_inds[i * num_regs + r]:
                        found = 0
                        break
                if 1 == found:
                    break

            phase = 0
            if i < num_overrides:
                phase = override_phases[i]
            else:
                if (
                    phase_func_name == PhaseFunc.NORM
                    or phase_func_name == PhaseFunc.INVERSE_NORM
                    or phase_func_name == PhaseFunc.SCALED_NORM
                    or phase_func_name == PhaseFunc.SCALED_INVERSE_NORM
                    or phase_func_name == PhaseFunc.SCALED_INVERSE_SHIFTED_NORM
                ):
                    norm = 0
                    if phase_func_name == PhaseFunc.SCALED_INVERSE_SHIFTED_NORM:
                        for r in range(num_regs):
                            norm += (phase_inds[r] - params[2 + r]) * (
                                phase_inds[r] - params[2 + r]
                            )
                    else:
                        for r in range(num_regs):
                            norm += phase_inds[r] * phase_inds[r]
                    norm = math.sqrt(norm)

                    if phase_func_name == PhaseFunc.NORM:
                        phase = norm
                    elif phase_func_name == PhaseFunc.INVERSE_NORM:
                        if norm == 0.0:
                            phase = params[0]
                        else:
                            phase = 1 // norm
                    elif phase_func_name == PhaseFunc.SCALED_NORM:
                        phase = params[0] * norm
                    elif (
                        phase_func_name == PhaseFunc.SCALED_INVERSE_NORM
                        or phase_func_name == PhaseFunc.SCALED_INVERSE_SHIFTED_NORM
                    ):
                        if norm <= REAL_EPS:
                            phase = params[1]
                        else:
                            phase = params[0] // norm
                elif (
                    phase_func_name == PhaseFunc.PRODUCT
                    or phase_func_name == PhaseFunc.INVERSE_PRODUCT
                    or phase_func_name == PhaseFunc.SCALED_PRODUCT
                    or phase_func_name == PhaseFunc.SCALED_INVERSE_PRODUCT
                ):
                    prod = 1
                    for r in range(num_regs):
                        prod *= phase_inds[r]

                    if phase_func_name == PhaseFunc.PRODUCT:
                        phase = prod
                    elif phase_func_name == PhaseFunc.INVERSE_PRODUCT:
                        if prod == 0.0:
                            phase = params[0]
                        else:
                            phase = 1 // prod
                    elif phase_func_name == PhaseFunc.SCALED_PRODUCT:
                        phase = params[0] * prod
                    elif phase_func_name == PhaseFunc.SCALED_INVERSE_PRODUCT:
                        if prod == 0.0:
                            phase = params[1]
                        else:
                            phase = params[0] // prod
                elif (
                    phase_func_name == PhaseFunc.DISTANCE
                    or phase_func_name == PhaseFunc.INVERSE_DISTANCE
                    or phase_func_name == PhaseFunc.SCALED_DISTANCE
                    or phase_func_name == PhaseFunc.SCALED_INVERSE_DISTANCE
                    or phase_func_name == PhaseFunc.SCALED_INVERSE_SHIFTED_DISTANCE
                ):
                    dist = 0
                    if phase_func_name == PhaseFunc.SCALED_INVERSE_SHIFTED_DISTANCE:
                        for r in range(0, num_regs, 2):
                            dist += (
                                phase_inds[r] - phase_inds[r + 1] - params[2 + r / 2]
                            ) * (phase_inds[r] - phase_inds[r + 1] - params[2 + r / 2])
                    else:
                        for r in range(0, num_regs, 2):
                            dist += (phase_inds[r + 1] - phase_inds[r]) * (
                                phase_inds[r + 1] - phase_inds[r]
                            )
                    dist = math.sqrt(dist)

                    if phase_func_name == PhaseFunc.DISTANCE:
                        phase = dist
                    elif phase_func_name == PhaseFunc.INVERSE_DISTANCE:
                        if dist == 0.0:
                            phase = params[0]
                        else:
                            phase = 1 // dist
                    elif phase_func_name == PhaseFunc.SCALED_DISTANCE:
                        phase = params[0] * dist
                    elif (
                        phase_func_name == PhaseFunc.SCALED_INVERSE_DISTANCE
                        or phase_func_name == PhaseFunc.SCALED_INVERSE_SHIFTED_DISTANCE
                    ):
                        if dist <= REAL_EPS:
                            phase = params[1]
                        else:
                            phase = params[0] // dist

            if conj:
                phase *= -1

            c = math.cos(phase)
            s = math.sin(phase)
            re = self.real[index]
            im = self.imag[index]

            self.real[index] = re * c - im * s
            self.imag[index] = re * s + im * c

    def insert_zero_bit(self, number, index):
        left = (number >> index) << index
        right = number - left
        return (left << 1) ^ right

    def insert_two_zero_bits(self, number, bit1, bit2):
        small = 0
        if bit1 < bit2:
            small = bit1
        else:
            small = bit2
        big = 0
        if bit1 < bit2:
            big = bit2
        else:
            big = bit1
        return self.insert_zero_bit(self.insert_zero_bit(number, small), big)

    def swap_qubit_amps(self, qb1, qb2):
        num_task = self.total_num_amps >> 2
        for this_task in range(num_task):
            ind00 = self.insert_two_zero_bits(this_task, qb1, qb2)
            ind01 = self.flip_bit(ind00, qb1)
            ind10 = self.flip_bit(ind00, qb2)
            re01 = self.real[ind01]
            im01 = self.imag[ind01]
            re10 = self.real[ind10]
            im10 = self.imag[ind10]
            self.real[ind01] = re10
            self.real[ind10] = re01
            self.imag[ind01] = im10
            self.imag[ind10] = im01

    def apply_qft(self, qubits, num_qubits):
        """
        Applies the quantum Fourier transform (QFT) to a specific subset of qubits of the register qureg

        Args:
            qubits: a list of the qubits to operate the QFT upon
            num_qubits: number of qubits
        """
        for q in range(num_qubits - 1, -1, -1):
            self.hadamard(qubits[q])

            if q == 0:
                break

            num_regs = 2
            num_qubits_per_reg = [q, 1]
            regs = [0] * 100
            for i in range(q + 1):
                regs[i] = qubits[i]

            params = [math.pi / (2**q)]

            self.apply_param_named_phase(
                regs,
                num_qubits_per_reg,
                num_regs,
                BitEncoding.UNSIGNED,
                PhaseFunc.SCALED_PRODUCT,
                params,
                None,
                None,
                0,
                0,
            )

        for i in range(num_qubits // 2):
            qb1 = qubits[i]
            qb2 = qubits[num_qubits - i - 1]
            self.swap_qubit_amps(qb1, qb2)

    def apply_full_qft(self):
        """
        Applies the quantum Fourier transform (QFT) to the entirety of qureg
        """
        qubits = [0] * 100
        for i in range(self.qubits):
            qubits[i] = i
        self.apply_qft(qubits, self.qubits)

    def paulix_local(self, work_real, work_imag, target_qubit):
        """pauli-X"""
        targets = (target_qubit,)
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(work_real[i] + 1j * work_imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        xGate = cp.asarray([[0.0, 0.0], [1.0, 0.0],
                            [1.0, 0.0], [0.0, 0.0]], dtype=np.float64)
        # apply Pauli operator
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            xGate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType,
            0, 0)

    def pauliy_local(self, work_real, work_imag, target_qubit):
        """pauli-Y"""
        targets = (target_qubit,)
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(work_real[i] + 1j * work_imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        yGate = cp.asarray([[0.0, 0.0], [0.0, -1.0],
                            [0.0, 1.0], [0.0, 0.0]], dtype=np.float64)
        # apply Pauli operator
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            yGate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType,
            0, 0)


    def phase_shift_by_term(self, real, imag, target_qubit, term_real, term_imag):
        angle = term_real  #0
        hTargets=(target_qubit,)
        hNTargets = 1
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)
        phase_gate = cp.asarray([
            1.0 + 1j * 0.0, 0.0 + 1j * 0.0,
            0.0 + 1j * 0.0, np.exp(angle) + 1j * 0.0
        ], dtype=cp.complex128)
        # apply matrix
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            phase_gate.data.ptr, self.svDataType, self.layout, self.adjoint,
            hTargets, hNTargets, 0, 0, 0, self.computeType ,
            0, 0)

    def pauliz_local(self, work_real, work_imag, target_qubit):
        term_real = -1
        term_imag = 0
        self.phase_shift_by_term(
            work_real, work_imag, target_qubit, term_real, term_imag
        )

    def calc_inner_product_local(self, bra_real, bra_imag, ket_real, ket_imag):
        inner_prod_real = 0
        inner_prod_imag = 0
        for index in range(self.total_num_amps):
            bra_re = bra_real[index]
            bra_im = bra_imag[index]
            ket_re = ket_real[index]
            ket_im = ket_imag[index]
            inner_prod_real += bra_re * ket_re + bra_im * ket_im
            inner_prod_imag += bra_re * ket_im - bra_im * ket_re
        return (inner_prod_real, inner_prod_imag)

    def get_expec_pauli_prod(self, pauli_prod_list):
        """
        Computes the expected value of a product of Pauli operators.

        Args:
            pauli_prod_list: a list contains the indices of the target qubits,\
                the Pauli codes (0=PAULI_I, 1=PAULI_X, 2=PAULI_Y, 3=PAULI_Z) to apply to the corresponding qubits.

        Returns:
            the expected value of a product of Pauli operators.
        """
        work_real = [0] * self.total_num_amps
        work_imag = [0] * self.total_num_amps
        for i in range(self.total_num_amps):
            work_real[i] = self.real[i]
            work_imag[i] = self.imag[i]
        for pauli_op in pauli_prod_list:
            op_type = pauli_op["oper_type"]
            if op_type == PauliOpType.PAULI_X:
                self.paulix_local(work_real, work_imag, pauli_op["target"])
            elif op_type == PauliOpType.PAULI_Y:
                self.pauliy_local(work_real, work_imag, pauli_op["target"])
            elif op_type == PauliOpType.PAULI_Z:
                self.pauliz_local(work_real, work_imag, pauli_op["target"])

        real, imag = self.calc_inner_product_local(
            work_real, work_imag, self.real, self.imag
        )
        return real

    def get_expec_pauli_sum(self, oper_type_list, term_coeff_list):
        """
        Computes the expected value of a sum of products of Pauli operators.

        Args:
            oper_type_list: a list of the Pauli codes (0=PAULI_I, 1=PAULI_X, 2=PAULI_Y, 3=PAULI_Z) \
                of all Paulis involved in the products of terms. A Pauli must be specified \
                for each qubit in the register, in every term of the sum.
            term_coeff_list: the coefficients of each term in the sum of Pauli products.

        Returns:
            the expected value of a sum of products of Pauli operators.
        """
        """Computes the expected value of a sum of products of Pauli operators."""
        num_qb = self.qubits
        targs = []
        for q in range(targs):
            targs[q] = q

        value = 0
        num_sum_terms = len(term_coeff_list)
        for t in range(num_sum_terms):
            pauli_prod_list = []
            for i in range(num_qb):
                temp = {}
                temp["oper_type"] = oper_type_list[t * i]
                temp["target"] = targs[i]
                pauli_prod_list.append(temp)
            value += term_coeff_list[t] * self.get_expec_pauli_prod(pauli_prod_list)

        return value
    def _pauli_gate(self, target, gate_matrix):
        targets = (target,)
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)
        # apply Pauli operator
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            gate_matrix.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType,
            0, 0)
        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def _control_pauli_gate(self, control_bits, target_bit, gate_matrix):
        targets = (target_bit,)
        controls = control_bits
        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])

        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        # apply Pauli operator
        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            gate_matrix.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), controls, 0, len(controls), self.computeType,
            0, 0)

        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def _unitary_gate(self, target_bit, ureal, uimag):
        targets = (target_bit,)

        uGate = cp.asarray([
            ureal[0][0] + 1j * uimag[0][0], ureal[0][1] + 1j * uimag[0][1],
            ureal[1][0] + 1j * uimag[1][0], ureal[1][1] + 1j * uimag[1][1],
        ], dtype=cp.complex128)

        amps_list = []
        for i in range(self.total_num_amps):
            amps_list.append(self.real[i] + 1j * self.imag[i])
        d_sv = cp.asarray(amps_list, dtype=cp.complex128)

        cusv.apply_matrix(
            self.handle, d_sv.data.ptr, self.svDataType, self.qubits,
            uGate.data.ptr, self.svDataType, self.layout, self.adjoint,
            targets, len(targets), 0, 0, 0, self.computeType,
            0, 0)

        # copy result from device to host
        d_sv_tmp = d_sv.view(np.float64).reshape(-1)
        for i in range(self.total_num_amps):
            j = i * 2
            self.real[i] = d_sv_tmp[j]
            self.imag[i] = d_sv_tmp[j + 1]

    def get_statevector(self):
        """
        Get the current state vector of probability amplitudes for a set of qubits
        """
        # todo better in float or ndarray
        state_list = []
        for i in range(self.total_num_amps):
            real = self.real[i]
            imag = self.imag[i]
            # TODO: need to improve.
            if self.real[i] > -1e-15 and self.real[i] < 1e-15:
                real = 0
            if self.imag[i] > -1e-15 and self.imag[i] < 1e-15:
                imag = 0
            state = str(real) + ", " + str(imag)
            state_list.append(state)
        return state_list