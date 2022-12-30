## qucuQUantum

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](http://developer.queco.cn)
[![License](https://img.shields.io/badge/license-Apache%202-blue.svg)](LICENSE)
[![Download Code](https://img.shields.io/badge/download-zip-green.svg)](https://github.com/qudoor/runtime)

### **概述**
---
* quqcs 是基于 NVIDIA GPU 开发的量子线路模拟器，可与启科量子编程框架QuTrunk集成，实现基于本地GPU服务器的量子线路模拟计算加速。
* quqcs 目前只支持 State Vector 的量子线路模拟
* quqcs 基于 Python 语言，提供门级别的 API， 包括H, CH, P, CP, R, CR, Rx, Ry, Rz, Rxx, Ryy, Rzz, X, Y, Z, S, T, Sdg, Tdg, SqrtX, CSqrtX, SqrtSwap, Swap, CSwap, CNot, MCX, CY, MCZ, U1, U2, U3, U, CU, ISwap, SqrtXdg, PH等量子门
* quqcs 目前只支持与QuTrunk本地集成，需要与QuTrunk部署在同一台 NVIDIA GPU 服务器上。

### **下载和安装**
---
* quqcs 作为独立的库，与 runtime 集成，由 runtime 完成部署安装。

### **使用方法**
1. quqcs 库引入QuTrunk代码中
```import
from qucuQuantum.cuQuantum import BackendcuQuantum
```

2. 在QuTrunk代码中，构造QCircuit对象时，指定backend为BackendcuQuantum, 
```initialize
circuit = QCircuit(backend=BackendcuQuantum())
```
### **示例代码**

以下示例展示了利用 QuTrunk 运行 bell-pair 量子算法：

  ```python
  # import package
  from qutrunk.circuit import QCircuit
  from qutrunk.circuit.gates import H, CNOT, Measure, All
  from qucuQuantum.cuQuantum import BackendcuQuantum

  # allocate resource
  qc = QCircuit(backend=BackendcuQuantum())
  qr = qc.allocate(2) 

  # apply quantum gates
  H * qr[0]   
  CNOT * (qr[0], qr[1])
  All(Measure) * qr

  # print circuit
  qc.print()   
  # run circuit
  res = qc.run(shots=1024) 
  # print result
  print(res.get_counts()) 
  # draw circuit
  qc.draw()
  ```
运行结果：
<div>
<img src="http://developer.queco.cn/media/images/bell_pairYunXingJieGuo.original.png"/>
</div>

### ** 依赖 **
| 内容                            | 要求                                 |
|-------------------------------|------------------------------------|
| GPU 架构                        | Volta, Turing, Ampere, Ada, Hopper |
| NVIDIA GPU Compute Capability | 7.0+                               |
| CUDA                          | 11.x    (需要支持CUDA Memory Pools)    |
| CPU 架构                        | x86_64, ppc64Ie, ARM64             |
| 操作系统                          | Linux                              |
| GPU 驱动                        | 450.80.02+ (Linux)                 |

