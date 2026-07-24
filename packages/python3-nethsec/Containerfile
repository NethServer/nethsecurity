FROM python:3.13.9
RUN apt-get update \
    && apt-get install -y \
        cmake \
        liblua5.1-0-dev \
        lua5.1 \
        libjson-c-dev

RUN mkdir /tmp/requirements \
    && git clone https://github.com/openwrt/libubox.git /tmp/requirements/libubox \
    && cd /tmp/requirements/libubox \
    && git checkout 815633847cd32ffe6da28943cbeb37edc88265c8 \
    && cmake CMakeLists.txt \
    && make install \
    && git clone https://github.com/openwrt/ubus.git /tmp/requirements/ubus \
    && cd /tmp/requirements/ubus \
    && git checkout 3cc98db1a422dcf560f2d6347fd410f17565a89d \
    && cmake CMakeLists.txt \
    && make install \
    && git clone https://github.com/openwrt/uci.git /tmp/requirements/uci \
    && cd /tmp/requirements/uci \
    && git checkout 66127cd76c5d0bd46d5a90302cc6110f53a4e2f8 \
    && cmake CMakeLists.txt \
    && make install \
    && rm -rf /tmp/requirements \
    && echo "/usr/local/lib" >> /etc/ld.so.conf.d/local.conf \
    && ldconfig

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt
WORKDIR /app
CMD ["python3", "-m", "pytest"]
