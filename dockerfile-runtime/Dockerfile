FROM python:3.9-alpine

ENV ANSIBLE_VER=2.10.6

RUN set -x \
       # Build dependencies
    && apk --no-cache add --virtual build-dependencies \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev \
        openssl-dev \
        cargo \
        build-base \
       # Useful tools
    && apk --no-cache add \
        bash \
        openssh-client \
        rsync \
        sshpass \
    && pip install pip --upgrade \
    && pip install --no-cache-dir \
        ansible=="$ANSIBLE_VER" \
       # Some module need '/usr/bin/python' exist
    && ln -s -f /usr/local/bin/python3 /usr/bin/python \
    && ln -s -f /usr/local/bin/python3 /usr/bin/python3 \
       # Cleaning
    && apk del build-dependencies \
    && rm -rf /var/cache/apk/* \
    && rm -rf /root/.cache \
    && rm -rf /root/.cargo

CMD [ "sleep", "360000000" ]