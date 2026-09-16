FROM ubuntu:24.04@sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254 AS build
ARG C2POOL_REF=v0.2.0
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git g++ cmake make python3 python3-pip pkg-config \
    libleveldb-dev libsecp256k1-dev libssl-dev libzmq3-dev && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install --break-system-packages "conan>=2.0,<3.0"
WORKDIR /src
COPY patches/solo-explicit-merged-payout.py /tmp/solo-explicit-merged-payout.py
RUN git clone --depth 1 --branch "${C2POOL_REF}" https://github.com/frstrtr/c2pool.git .
RUN python3 /tmp/solo-explicit-merged-payout.py /src
RUN sed -i '/add_library(core_util STATIC core_util.cpp)/a target_link_libraries(core_util PUBLIC Boost::headers)' src/core/CMakeLists.txt
RUN conan profile detect --force && mkdir -p build && cd build && \
    conan install .. --build=missing --output-folder=. --settings=build_type=Release && \
    cmake .. --preset conan-release && \
    cmake --build . --target c2pool-ltc -j2

FROM ubuntu:24.04@sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget libleveldb1d libsecp256k1-1 libssl3 libzmq5 && \
    rm -rf /var/lib/apt/lists/* && \
    groupmod -n mergeforge ubuntu && \
    usermod -l mergeforge -d /home/mergeforge -m ubuntu && \
    usermod -G mergeforge mergeforge
COPY --from=build /src/build/src/c2pool/c2pool-ltc /usr/local/bin/c2pool-ltc
RUN mkdir -p /data && chown -R mergeforge:mergeforge /data
USER mergeforge
EXPOSE 3333 8080
ENTRYPOINT []
