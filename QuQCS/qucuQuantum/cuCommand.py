"""Command of qucuQuantum"""
from cuquantum import cudaDataType as cudtype
from cuquantum import custatevec as cusv


class cuCommand:

    def __init__(self, nIndexBits, matrix, nTargets, nControls, rotation, matrixDataType=cudtype.CUDA_C_64F, matrixLayout=cusv.MatrixLayout.ROW):
        self.nIndexBits = nIndexBits
        self.matrix = matrix
        self.nTargets = nTargets
        self.nControls = nControls
        self.theta = rotation
        self.matrixDataType = matrixDataType
        self.matrixLayout = matrixLayout






