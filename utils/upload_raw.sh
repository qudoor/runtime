

### 需要在x.x.x.195上执行，上传到x.x.x.212服务器上


curl -X 'POST' \
  'http://x.x.x.212:8081/service/rest/v1/components?repository=qudoor-raw' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'raw.directory=cuda/11.7.1/amd64/' \
  -F 'raw.asset1=@/data/download/qudoor-raw/cuda-archive-keyring.gpg;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document' \
  -F 'raw.asset1.filename=cuda-archive-keyring.gpg' \
  -u admin:123456


curl -X 'POST' \
  'http://x.x.x.212:8081/service/rest/v1/components?repository=qudoor-raw' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'raw.directory=/cuda/11.7.1/amd64' \
  -F 'raw.asset1=@/data/download/qudoor-raw/cuda_11.7.1_515.65.01_linux.run;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document' \
  -F 'raw.asset1.filename=cuda_11.7.1_515.65.01_linux.run' \
  -u admin:123456

curl -X 'POST' \
  'http://x.x.x.212:8081/service/rest/v1/components?repository=qudoor-raw' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'raw.directory=/nvidia/515.65.01/amd64' \
  -F 'raw.asset1=@/data/download/qudoor-raw/NVIDIA-Linux-x86_64-515.65.01.run;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document' \
  -F 'raw.asset1.filename=NVIDIA-Linux-x86_64-515.65.01.run' \
  -u admin:123456

curl -X 'POST' \
  'http://x.x.x.212:8081/service/rest/v1/components?repository=qudoor-raw' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'raw.directory=python/3.8.16/amd64/' \
  -F 'raw.asset1=@/data/download/qudoor-raw/Python-3.8.16.tgz;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document' \
  -F 'raw.asset1.filename=Python-3.8.16.tgz' \
  -u admin:123456

curl -X 'POST' \
  'http://x.x.x.212:8081/service/rest/v1/components?repository=qudoor-raw' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'raw.directory=/python/3.9.14/amd64' \
  -F 'raw.asset1=@/data/download/qudoor-raw/Python-3.9.14.tar.xz;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document' \
  -F 'raw.asset1.filename=Python-3.9.14.tar.xz' \
  -u admin:123456