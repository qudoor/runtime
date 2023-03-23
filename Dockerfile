FROM python:3.9-slim-buster
MAINTAINER young <yangzhuohua@qudoor.cn>
ENV LANG=zh_CN.UTF-8

ARG BUILD_DEPENDENCIES="              \
    g++                               \
    make                              \
    gcc"

ARG DEPENDENCIES="                    \
    default-libmysqlclient-dev        \
    libxml2-dev                       \
    libxslt-dev                       \
    python3-dev                       \
    libffi-dev                        \
    libtool                           \
    libpq-dev                         \
    openssh-client                    \
    sshpass"

ARG TOOLS="                           \
    curl                              \
    default-mysql-client              \
    telnet                            \
    vim                               \
    unzip                             \
    locales                           \
    wget"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=core \
    sed -i 's@http://.*.debian.org@http://mirrors.ustc.edu.cn@g' /etc/apt/sources.list \
    && rm -f /etc/apt/apt.conf.d/docker-clean \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && apt-get update \
    && apt-get -y install --no-install-recommends ${BUILD_DEPENDENCIES} \
    && apt-get -y install --no-install-recommends ${DEPENDENCIES} \
    && apt-get -y install --no-install-recommends ${TOOLS} \
    && mkdir -p /root/.ssh/ \
    && echo "Host *\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile /dev/null" > /root/.ssh/config \
    && sed -i "s@# alias l@alias l@g" ~/.bashrc \
    && echo "set mouse-=a" > ~/.vimrc \
    && echo "no" | dpkg-reconfigure dash \
    && echo "zh_CN.UTF-8" | dpkg-reconfigure locales \
    && rm -rf /var/lib/apt/lists/* \
    && rm /usr/bin/python3 \
    && ln -s /usr/local/bin/python3 /usr/bin/python3


ENV HELM_VERSION=v3.10.1
ARG PYARCH

RUN curl -L x.x.x.195:8081/repository/qudoor-raw/helm/${HELM_VERSION}/${PYARCH}/helm-${HELM_VERSION}-linux-${PYARCH}.tar.gz | tar xz && mv linux-${PYARCH}/helm /usr/bin/helm && rm -rf linux-${PYARCH}
COPY . /QuPot
WORKDIR /QuPot

VOLUME /QuPot/data
VOLUME /QuPot/logs
VOLUME /QuPot/static


ARG PIP_MIRROR=https://pypi.douban.com/simple
ENV PIP_MIRROR=$PIP_MIRROR

RUN --mount=type=cache,target=/root/.cache/pip \
    set -ex \
    &&  pip config set global.index-url ${PIP_MIRROR} \
    && pip install --upgrade pip \
    && pip install --upgrade setuptools wheel \
    && pip install --no-cache-dir mysqlclient -i ${PIP_MIRROR} \
    && pip install --no-cache-dir -r /QuPot/requirements.txt  -i ${PIP_MIRROR}


EXPOSE 9001
ENTRYPOINT ["./entrypoint.sh"]
