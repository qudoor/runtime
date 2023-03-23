#!/usr/bin/env bash

export red=31
export green=32
export yellow=33

export QU_BASE=/opt
export CWD=$(pwd)


export COMPOSE_HTTP_TIMEOUT=180
export CURRENT_QU_VERSION=`cat ${QU_BASE}/qupot/qupot.conf|grep QU_TAG|awk -F= '{print $2}'`
export OFFLINE_KO_VERSION=$(pwd|grep -Eo "v([0-9]{1,}\.)+[0-9]{1,}")
export KO_PORT=`cat ${QU_BASE}/qupot/qupot.conf |grep KO_PORT|awk -F= '{print $2}'`
export OS_ARCH=`cat ${QU_BASE}/qupot/qupot.conf |grep OS_ARCH|awk -F= '{print $2}'`
export KO_REPO_PORT=`cat ${QU_BASE}/qupot/qupot.conf |grep KO_REPO_PORT|awk -F= '{print $2}'`
export KO_REGISTRY_PORT=`cat ${QU_BASE}/qupot/qupot.conf |grep KO_REGISTRY_PORT|awk -F= '{print $2}'`
export KO_REGISTRY_HOSTED_PORT=`cat ${QU_BASE}/qupot/qupot.conf |grep KO_REGISTRY_HOSTED_PORT|awk -F= '{print $2}'`

function colorMsg() {
  echo -e "\033[$1m $2 \033[0m"
}
