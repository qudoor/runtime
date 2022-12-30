
## 安装依赖
### 算法库
☐ 1. sklearn:: https://pypi.org/project/scikit-learn/

​pip install scikit-learn  (装qiskit时候会自动装)

☐ 2. pytorch: You need to have either PyTorch or LibTorch installed based on if you are using Python or C++ and you must have CUDA, cuDNN and TensorRT installed. https://pytorch.org/TensorRT/tutorials/installation.html

​根据您使用的是 Python 还是 C++，您需要安装 PyTorch 或 LibTorch，并且必须安装 CUDA、cuDNN 和 TensorRT。


☐ 3. tensorflow (支持 GPU 和  仅支持 CPU )
 https://www.tensorflow.org/install?hl=zh-cn

​​# Current stable release for CPU and GPU

​ pip install tensorflow


☐ 4. VQE变分量子特征值求解算法(Variational-Quantum-Eigensolver，简称VQE)[ :  https://pypi.org/project/qiskit-aqua/  

pip install qiskit-aqua​

​from qiskit.aqua.algorithms import VQE, QAOA,

☐ 5. QAOA：量子近似优化算法(Quantum Approximate Optimization Algorithm, QAOA)   

from qiskit.aqua.algorithms import VQE, QAOA,

☐ 6.  : SciPy 是一个开源的 Python 算法库和数学工具包。

python3 -m pip install -U scipy

☐ 7. HHL(Harrow, Hassidim 和 Lloyd（HHL）提出了一种求解线性系统 Ax=b (其中A是算子，x，b是向量)中x信息的量子线性系统分析):  qiskit

https://qrunes-tutorial.readthedocs.io/en/latest/chapters/algorithms/HHL_Algorithm.html

​https://qiskit.org/textbook/ch-applications/hhl_tutorial.html#3.-Example:-4-qubit-HHL

​from qiskit.algorithms.linear_solvers.hhl import HHL

#### 总结
只需要安装三个算法库支持
1. 只需要安装 qiskit-aqua(Algorithms for QUantum Applications) 就会依赖安装：sklearn、VQE、QAOA、SciPy、HHL
```shell
pip install qiskit-aqua
```
2. 安装 pytorch：
3. 安装 TensorFlow： 通过
### arm 上测试算法库

1. 安装 pip
```shell
# 需要 update 否则无法安装 pip 
$ sudo apt-get update
# For Python 3.3+
$ sudo apt-get install python3-pip
```

2. 安装 qiskit-aqua
```shell
pip install qiskit-aqua

暗转Python 遇到问题

```
 Failed to build these modules: _ctypes
```

https://techglimpse.com/install-python-openssl-support-tutorial/

```pip3 install tensorflow==2.11.0
WARNING: pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError("Can't connect to HTTPS URL because the SSL module is not available.")': /simple/tensorflow/
WARNING: Retrying (Retry(total=3, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError("Can't connect to HTTPS URL because the SSL module is not available.")': /simple/tensorflow/
WARNING: Retrying (Retry(total=2, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError("Can't connect to HTTPS URL because the SSL module is not available.")': /simple/tensorflow/
WARNING: Retrying (Retry(total=1, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError("Can't connect to HTTPS URL because the SSL module is not available.")': /simple/tensorflow/
WARNING: Retrying (Retry(total=0, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError("Can't connect to HTTPS URL because the SSL module is not available.")': /simple/tensorflow/
Could not fetch URL https://pypi.org/simple/tensorflow/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /simple/tensorflow/ (Caused by SSLError("Can't connect to HTTPS URL because the SSL module is not available.")) - skipping
ERROR: Could not find a version that satisfies the requirement tensorflow==2.11.0 (from versions: none)
ERROR: No matching distribution found for tensorflow==2.11.0
WARNING: pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
Could not fetch URL https://pypi.org/simple/pip/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /simple/pip/ (Caused by SSLError("Can't connect to HTTPS URL because the SSL module is not available.")) - skipping
```

https://blog.csdn.net/YMY_mine/article/details/103804365


https://bugs.python.org/issue30090

https://blog.csdn.net/zsl10/article/details/52315319

手动安装 Python3.8.15

https://blog.csdn.net/u010786653/article/details/122690588


### 安装 qusprout 到 arm centos 中

- 安装 qusprout 前安装基本的工具：gcc g++ make unzip


### 问题
```
unexpected character "[" in variable name near "[DEFAULT]\nRT_BASE
```

fix:
[Settings -> General -> Use Docker Compose V2](https://github.com/laradock/laradock/issues/3076#issuecomment-1017484349)

### 打包流程
在192.168.170.205上
cd /home/gitlab-runner/builds/-yE6PDuQ/0/qudoor/runtime/
git pull




amd64:
生成docker
docker build -t registry.queco.cn/qudoor/runtime:ansible-2.10.6-amd64 .

arm64:
生成docker
docker build -t registry.queco.cn/qudoor/runtime:ansible-2.10.6-arm64 .

Nexus 密码：runtime123
